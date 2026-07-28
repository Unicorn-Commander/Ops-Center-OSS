"""
User Management API - Comprehensive Keycloak user management

Provides admin endpoints for managing Keycloak users with advanced features:
- User listing with filtering and pagination
- Bulk operations (import, export, delete, suspend, role assignment)
- Role management with hierarchy
- API key management
- Session management
- User impersonation
- Activity tracking
- Analytics

Endpoints: /api/v1/admin/users/*
"""

import asyncio
import csv
import io
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Request, UploadFile, File, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import bcrypt
import secrets
import string

# Import Keycloak integration functions
import httpx
from keycloak_integration import (
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    create_user as keycloak_create_user,
    update_user_attributes as keycloak_update_user,
    delete_user as keycloak_delete_user,
    set_subscription_tier,
    set_user_password,
    send_account_action_email,
    get_admin_token,
    _get_attr_value,
    KEYCLOAK_URL,
    KEYCLOAK_REALM,
)

from audit_logger import audit_logger
from audit_helpers import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/admin/users", tags=["User Management"])

# ============================================================================
# MODELS
# ============================================================================

class UserFilters(BaseModel):
    """Query parameters for filtering users"""
    search: Optional[str] = None
    tier: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    org_id: Optional[str] = None
    created_from: Optional[str] = None
    created_to: Optional[str] = None
    last_login_from: Optional[str] = None
    last_login_to: Optional[str] = None
    email_verified: Optional[bool] = None
    byok_enabled: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class BulkRoleAssignment(BaseModel):
    """Bulk role assignment request"""
    user_ids: List[str]
    role: str

class BulkTierChange(BaseModel):
    """Bulk tier change request"""
    user_ids: List[str]
    tier: str

class BulkOperationRequest(BaseModel):
    """Bulk operation request"""
    user_ids: List[str]

class APIKeyCreate(BaseModel):
    """API key creation request"""
    name: str
    expires_days: Optional[int] = None

class ImpersonationRequest(BaseModel):
    """User impersonation request"""
    duration_hours: int = Field(default=24, ge=1, le=72)

class UserCreateRequest(BaseModel):
    """Basic single-user creation request (POST /api/v1/admin/users)"""
    email: str
    username: Optional[str] = None          # defaults to email when omitted
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    password: Optional[str] = None          # optional; omit to provision without password
    temporary_password: bool = False        # True => Keycloak forces UPDATE_PASSWORD on first login
    enabled: bool = True
    emailVerified: bool = False
    subscription_tier: str = "trial"
    send_onboarding_email: bool = False     # email a set-password/verify link instead of a password

class ComprehensiveUserCreate(BaseModel):
    """Payload sent by the admin CreateUserModal (POST /api/v1/admin/users/comprehensive).

    Field names intentionally mirror the frontend modal's formData keys
    (camelCase). Unknown extra keys (e.g. confirmPassword) are ignored.
    """
    # Tab 1: Basic information
    email: str
    username: Optional[str] = None
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    password: Optional[str] = None
    enabled: bool = True
    emailVerified: bool = False
    sendWelcomeEmail: bool = True
    # Tab 2: Organization & roles
    organizationId: Optional[str] = ""
    brigadeRoles: List[Any] = []
    keycloakRoles: List[Any] = []
    # Tab 3: Subscription & billing
    subscriptionTier: str = "free"
    billingStartDate: Optional[str] = None
    paymentMethod: Optional[str] = "skip"
    apiCallLimitOverride: Optional[int] = None
    initialCredits: Optional[int] = 0
    # Tab 4: Access & permissions
    serviceAccess: Dict[str, Any] = {}
    featureFlags: Dict[str, Any] = {}
    rateLimits: Dict[str, Any] = {}
    # Tab 5: Metadata
    tags: List[str] = []
    internalNotes: Optional[str] = ""
    accountSource: Optional[str] = "admin-created"

# Default daily API-call limits per tier (mirrors the CreateUserModal tier table)
TIER_API_CALL_LIMITS = {
    "free": 100,
    "trial": 700,
    "starter": 1000,
    "professional": 10000,
    "enterprise": 999999,
}

# ============================================================================
# DEPENDENCY: REQUIRE ADMIN
# ============================================================================

async def require_admin(request: Request):
    """Verify user is authenticated and has admin role (uses Redis session manager)"""
    import sys
    import os

    # Add parent directory to path if needed
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))

    # Get session data
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Check if user has admin role
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Return the session user dict (truthy, so existing `admin: bool = Depends(...)`
    # call sites keep working) so newer endpoints can audit the acting admin.
    return user

# ============================================================================
# ROLE HELPERS
# ============================================================================

async def _fetch_realm_roles(user_id: str) -> List[str]:
    """
    Fetch a user's realm role names via the Keycloak admin REST API.

    The /users list endpoint does not include role mappings, so the REST path
    must fetch them per-user from /users/{id}/role-mappings/realm. Returns an
    empty list on any failure (best-effort enrichment, never blocks the list).
    """
    try:
        token = await get_admin_token()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return [r.get("name") for r in response.json() if r.get("name")]
            logger.warning(f"Failed to fetch realm roles for {user_id}: {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching realm roles for {user_id}: {e}")
    return []


async def _set_user_enabled(user_id: str, enabled: bool) -> bool:
    """Set the Keycloak `enabled` flag on a user (admin REST PUT /users/{id})."""
    try:
        token = await get_admin_token()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"enabled": enabled},
                timeout=10.0,
            )
            if response.status_code == 204:
                return True
            logger.error(f"Failed to set enabled={enabled} for {user_id}: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error setting enabled flag for {user_id}: {e}")
    return False


async def _get_realm_role(role_name: str) -> Optional[Dict[str, Any]]:
    """Fetch a realm role representation by name (None if it doesn't exist)."""
    try:
        token = await get_admin_token()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles/{role_name}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            if response.status_code != 404:
                logger.warning(f"Failed to fetch realm role '{role_name}': {response.status_code}")
    except Exception as e:
        logger.warning(f"Error fetching realm role '{role_name}': {e}")
    return None


def _normalize_role_names(values: List[Any]) -> List[str]:
    """Accept role names as plain strings or {name: ...} objects (frontend sends either)."""
    names = []
    for v in values or []:
        if isinstance(v, str) and v.strip():
            names.append(v.strip())
        elif isinstance(v, dict) and v.get("name"):
            names.append(str(v["name"]).strip())
    # De-dupe, preserve order
    seen = set()
    return [n for n in names if not (n in seen or seen.add(n))]


async def _assign_realm_roles(user_id: str, role_names: List[str]) -> Dict[str, List]:
    """
    Assign realm roles to a user via the Keycloak admin REST API.

    Returns {"assigned": [names], "failed": [{"role", "error"}]} — unknown roles
    are reported per-role instead of failing the whole call.
    """
    results = {"assigned": [], "failed": []}
    if not role_names:
        return results

    role_reps = []
    for name in role_names:
        rep = await _get_realm_role(name)
        if rep:
            role_reps.append(rep)
        else:
            results["failed"].append({"role": name, "error": "Realm role not found"})

    if not role_reps:
        return results

    try:
        token = await get_admin_token()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=role_reps,
                timeout=10.0,
            )
            if response.status_code == 204:
                results["assigned"] = [r.get("name") for r in role_reps]
            else:
                logger.error(f"Failed to assign roles to {user_id}: {response.status_code} - {response.text}")
                for r in role_reps:
                    results["failed"].append({"role": r.get("name"), "error": f"Keycloak returned {response.status_code}"})
    except Exception as e:
        logger.error(f"Error assigning roles to {user_id}: {e}")
        for r in role_reps:
            results["failed"].append({"role": r.get("name"), "error": str(e)})

    return results


async def _remove_realm_role(user_id: str, role_name: str) -> bool:
    """Remove a realm role mapping from a user."""
    rep = await _get_realm_role(role_name)
    if not rep:
        return False
    try:
        token = await get_admin_token()
        async with httpx.AsyncClient(verify=False) as client:
            # httpx .delete() does not accept a JSON body; use .request()
            response = await client.request(
                "DELETE",
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=[rep],
                timeout=10.0,
            )
            return response.status_code == 204
    except Exception as e:
        logger.error(f"Error removing role '{role_name}' from {user_id}: {e}")
        return False


async def _add_user_to_organization(user_id: str, org_id: str, role: str = "member") -> Dict[str, Any]:
    """
    Add a user to an organization in Postgres (same organization_members insert
    used by org_api.add_organization_member). Returns org info on success;
    raises ValueError with a human-readable reason on failure.
    """
    import asyncpg  # lazy import: only needed on the org path

    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db"),
    )
    try:
        org = await conn.fetchrow(
            "SELECT id::text AS id, name FROM organizations WHERE id::text = $1",
            org_id,
        )
        if not org:
            raise ValueError(f"Organization {org_id} not found")

        existing = await conn.fetchrow(
            "SELECT 1 FROM organization_members WHERE org_id::text = $1 AND user_id = $2",
            org_id,
            user_id,
        )
        if not existing:
            await conn.execute(
                """
                INSERT INTO organization_members (org_id, user_id, role)
                VALUES ($1::uuid, $2, $3)
                """,
                org_id,
                user_id,
                role,
            )
        return {"id": org["id"], "name": org["name"], "role": role}
    finally:
        await conn.close()


def _shape_user_response(user: Dict[str, Any], roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Shape a Keycloak user record like the items returned by GET /api/v1/admin/users."""
    attrs = user.get("attributes", {}) or {}
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "firstName": user.get("firstName", ""),
        "lastName": user.get("lastName", ""),
        "enabled": user.get("enabled", True),
        "emailVerified": user.get("emailVerified", False),
        "createdTimestamp": user.get("createdTimestamp"),
        "roles": roles if roles is not None else (user.get("realmRoles") or []),
        "subscription_tier": _get_attr_value(attrs, "subscription_tier", "trial"),
        "subscription_status": _get_attr_value(attrs, "subscription_status", "active"),
        "api_calls_limit": _get_attr_value(attrs, "api_calls_limit", "1000"),
        "api_calls_used": _get_attr_value(attrs, "api_calls_used", "0"),
        "org_id": _get_attr_value(attrs, "org_id"),
        "org_name": _get_attr_value(attrs, "org_name"),
        "byok_enabled": _get_attr_value(attrs, "byok_enabled", "false") == "true",
    }


async def _reject_duplicate_user(email: str, username: str):
    """Raise 409 when the email or username is already taken in Keycloak."""
    existing = await get_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A user with email '{email}' already exists",
        )
    if username and username.lower() != email.lower():
        existing = await get_user_by_username(username)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"A user with username '{username}' already exists",
            )


# ============================================================================
# USER LISTING & FILTERING
# ============================================================================

@router.get("")
async def list_users(
    search: Optional[str] = None,
    tier: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    org_id: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
    last_login_from: Optional[str] = None,
    last_login_to: Optional[str] = None,
    email_verified: Optional[bool] = None,
    byok_enabled: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    admin: bool = Depends(require_admin)
):
    """
    List users with advanced filtering and pagination

    Query Parameters:
    - search: Search by email/username
    - tier: Filter by subscription tier
    - role: Filter by role
    - status: Filter by account status
    - org_id: Filter by organization
    - created_from/to: Registration date range
    - last_login_from/to: Last login date range
    - email_verified: Filter by email verification status
    - byok_enabled: Filter by BYOK status
    - limit/offset: Pagination
    """
    try:
        # Get all users from Keycloak
        all_users = await get_all_users()

        # Apply filters
        filtered_users = []
        for user in all_users:
            # Search filter
            if search:
                email = user.get("email", "").lower()
                username = user.get("username", "").lower()
                if search.lower() not in email and search.lower() not in username:
                    continue

            # Get user attributes
            attrs = user.get("attributes", {})

            # Tier filter
            if tier:
                user_tier = _get_attr_value(attrs, "subscription_tier", "trial")
                if user_tier != tier:
                    continue

            # Status filter
            if status:
                if status == "enabled" and not user.get("enabled", True):
                    continue
                if status == "disabled" and user.get("enabled", True):
                    continue

            # Email verified filter
            if email_verified is not None:
                if user.get("emailVerified", False) != email_verified:
                    continue

            # BYOK filter
            if byok_enabled is not None:
                has_byok = bool(_get_attr_value(attrs, "byok_enabled"))
                if has_byok != byok_enabled:
                    continue

            # Organization filter
            if org_id:
                user_org = _get_attr_value(attrs, "org_id")
                if user_org != org_id:
                    continue

            # Realm roles. The DB-fallback path already provides these as
            # `realmRoles`; the REST path omits them (backfilled post-pagination
            # for the page slice below, to avoid an N+1 over every user).
            user_roles = user.get("realmRoles")

            # Role filter. When a role filter is active we must know the user's
            # roles to decide inclusion; on the REST path (no `realmRoles`) fetch
            # them now so filtering is correct rather than silently empty.
            if role:
                if user_roles is None:
                    user_roles = await _fetch_realm_roles(user.get("id"))
                if role not in user_roles:
                    continue

            user_roles = user_roles or []

            # Add to filtered list
            filtered_users.append({
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "enabled": user.get("enabled", True),
                "emailVerified": user.get("emailVerified", False),
                "createdTimestamp": user.get("createdTimestamp"),
                "roles": user_roles,
                "subscription_tier": _get_attr_value(attrs, "subscription_tier", "trial"),
                "subscription_status": _get_attr_value(attrs, "subscription_status", "active"),
                "api_calls_limit": _get_attr_value(attrs, "api_calls_limit", "1000"),
                "api_calls_used": _get_attr_value(attrs, "api_calls_used", "0"),
                "org_id": _get_attr_value(attrs, "org_id"),
                "org_name": _get_attr_value(attrs, "org_name"),
                "byok_enabled": _get_attr_value(attrs, "byok_enabled", "false") == "true"
            })

        # Apply pagination
        total = len(filtered_users)
        paginated_users = filtered_users[offset:offset+limit]

        # Backfill realm roles for the paginated slice when the REST path was
        # used (no `realmRoles` present). Bounded to the page size, not all users.
        for u in paginated_users:
            if not u["roles"] and u.get("id"):
                u["roles"] = await _fetch_realm_roles(u["id"])

        return {
            "users": paginated_users,
            "total": total,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# USER CREATION
# ============================================================================

@router.post("", status_code=201)
async def create_user_basic(
    payload: UserCreateRequest,
    request: Request,
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Create a single Keycloak user (basic).

    - Duplicate email/username -> 409.
    - Optional password; `temporary_password=true` forces a password reset at
      first login (Keycloak UPDATE_PASSWORD required action).
    - `send_onboarding_email=true` (when no password is set) emails the user a
      secure set-password + verify-email link instead.
    - Sets subscription_tier/status attributes so the user renders correctly
      in the admin list immediately.
    """
    email = payload.email.strip().lower()
    username = (payload.username or email).strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")

    await _reject_duplicate_user(email, username)

    tier = payload.subscription_tier or "trial"
    api_calls_limit = TIER_API_CALL_LIMITS.get(tier, 1000)
    attributes = {
        "subscription_tier": [tier],
        "subscription_status": ["active"],
        "api_calls_limit": [str(api_calls_limit)],
        "api_calls_used": ["0"],
    }

    user_id = await keycloak_create_user(
        email=email,
        username=username,
        first_name=payload.firstName or "",
        last_name=payload.lastName or "",
        attributes=attributes,
        email_verified=payload.emailVerified,
    )
    if not user_id:
        raise HTTPException(status_code=502, detail="Keycloak rejected the user creation request")

    warnings = []

    if not payload.enabled:
        if not await _set_user_enabled(user_id, False):
            warnings.append("Failed to disable the account after creation")

    if payload.password:
        if not await set_user_password(user_id, payload.password, temporary=payload.temporary_password):
            warnings.append("User created but setting the password failed")
    elif payload.send_onboarding_email:
        result = await send_account_action_email(
            user_id, ["UPDATE_PASSWORD", "VERIFY_EMAIL"], lifespan=604800
        )
        if not result.get("success"):
            warnings.append(f"Onboarding email failed: {result.get('message', 'unknown error')}")

    # Best-effort audit (never blocks the response)
    try:
        await audit_logger.log(
            action="admin.user.create",
            result="success",
            user_id=admin.get("user_id") or admin.get("sub") if isinstance(admin, dict) else None,
            username=admin.get("email") if isinstance(admin, dict) else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            resource_type="user",
            resource_id=user_id,
            metadata={"email": email, "username": username, "tier": tier},
        )
    except Exception as e:
        logger.warning(f"Audit log failed for user create: {e}")

    created = await get_user_by_id(user_id)
    response = _shape_user_response(created or {"id": user_id, "email": email, "username": username})
    if warnings:
        response["warnings"] = warnings
    logger.info(f"Admin created user {email} ({user_id})")
    return response


@router.post("/comprehensive", status_code=201)
async def create_user_comprehensive(
    payload: ComprehensiveUserCreate,
    request: Request,
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Create a user from the admin Create User modal (all tabs).

    Creates the Keycloak user, sets the password, assigns realm roles
    (Keycloak + Brigade role names), sets tier/limit/feature attributes,
    optionally adds the user to an organization, and optionally sends the
    onboarding/welcome email. Returns the created user shaped like the
    GET /api/v1/admin/users list items (plus provisioning details).
    """
    email = payload.email.strip().lower()
    username = (payload.username or email).strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")

    await _reject_duplicate_user(email, username)

    tier = payload.subscriptionTier or "free"
    api_calls_limit = payload.apiCallLimitOverride or TIER_API_CALL_LIMITS.get(tier, 1000)

    attributes = {
        "subscription_tier": [tier],
        "subscription_status": ["active"],
        "api_calls_limit": [str(api_calls_limit)],
        "api_calls_used": ["0"],
        "byok_enabled": ["true" if (payload.featureFlags or {}).get("byokEnabled") else "false"],
        "account_source": [payload.accountSource or "admin-created"],
    }
    if payload.billingStartDate:
        attributes["billing_start_date"] = [payload.billingStartDate]
    if payload.tags:
        attributes["tags"] = [str(t) for t in payload.tags if str(t).strip()]
    if payload.internalNotes:
        attributes["internal_notes"] = [payload.internalNotes]

    user_id = await keycloak_create_user(
        email=email,
        username=username,
        first_name=payload.firstName or "",
        last_name=payload.lastName or "",
        attributes=attributes,
        email_verified=payload.emailVerified,
    )
    if not user_id:
        raise HTTPException(status_code=502, detail="Keycloak rejected the user creation request")

    warnings = []

    # Enabled flag (create_user always creates enabled=True)
    if not payload.enabled:
        if not await _set_user_enabled(user_id, False):
            warnings.append("Failed to disable the account after creation")

    # Password (the modal always collects one; API callers may omit it)
    if payload.password:
        if not await set_user_password(user_id, payload.password, temporary=False):
            warnings.append("User created but setting the password failed")

    # Realm roles: Keycloak roles + Brigade roles are both realm-role names
    role_names = _normalize_role_names(list(payload.keycloakRoles or []) + list(payload.brigadeRoles or []))
    role_result = await _assign_realm_roles(user_id, role_names) if role_names else {"assigned": [], "failed": []}

    # Organization membership (same organization_members insert as org_api)
    organization = None
    if payload.organizationId:
        try:
            organization = await _add_user_to_organization(user_id, payload.organizationId, role="member")
            # Mirror org onto Keycloak attributes so the users list shows it
            await keycloak_update_user(email, {
                "org_id": [organization["id"]],
                "org_name": [organization["name"]],
            })
        except ValueError as e:
            warnings.append(str(e))
        except Exception as e:
            logger.error(f"Failed to add user {user_id} to org {payload.organizationId}: {e}")
            warnings.append(f"Failed to add user to organization: {e}")

    # Welcome / onboarding email (best-effort)
    welcome_email_sent = False
    if payload.sendWelcomeEmail:
        actions = []
        if not payload.password:
            actions.append("UPDATE_PASSWORD")
        if not payload.emailVerified:
            actions.append("VERIFY_EMAIL")
        if actions:
            result = await send_account_action_email(user_id, actions, lifespan=604800)
            welcome_email_sent = bool(result.get("success"))
            if not welcome_email_sent:
                warnings.append(f"Welcome email failed: {result.get('message', 'unknown error')}")
        else:
            # Nothing for Keycloak to ask of the user (password set + email verified)
            warnings.append("Welcome email skipped: no pending account actions (password set and email already verified)")

    # Best-effort audit (never blocks the response)
    try:
        await audit_logger.log(
            action="admin.user.create_comprehensive",
            result="success",
            user_id=admin.get("user_id") or admin.get("sub") if isinstance(admin, dict) else None,
            username=admin.get("email") if isinstance(admin, dict) else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            resource_type="user",
            resource_id=user_id,
            metadata={
                "email": email,
                "username": username,
                "tier": tier,
                "roles": role_result.get("assigned", []),
                "org_id": payload.organizationId or None,
            },
        )
    except Exception as e:
        logger.warning(f"Audit log failed for comprehensive user create: {e}")

    created = await get_user_by_id(user_id)
    response = _shape_user_response(
        created or {"id": user_id, "email": email, "username": username},
        roles=role_result.get("assigned", []),
    )
    response.update({
        "roles_assigned": role_result.get("assigned", []),
        "roles_failed": role_result.get("failed", []),
        "organization": organization,
        "welcome_email_sent": welcome_email_sent,
    })
    if warnings:
        response["warnings"] = warnings

    logger.info(
        f"Admin created user {email} ({user_id}) via comprehensive create "
        f"(tier={tier}, roles={role_result.get('assigned', [])}, org={payload.organizationId or None})"
    )
    return response

# ============================================================================
# USER ANALYTICS
# ============================================================================

@router.get("/analytics/summary")
async def get_user_analytics_summary(admin: bool = Depends(require_admin)):
    """Get user analytics summary (total users, active, tiers, roles)"""
    try:
        users = await get_all_users()

        total_users = len(users)
        active_users = sum(1 for u in users if u.get("enabled", True))
        # Suspended = accounts that are disabled (cannot sign in).
        suspended_users = sum(1 for u in users if not u.get("enabled", True))

        # Tier distribution
        tiers = {"trial": 0, "starter": 0, "professional": 0, "enterprise": 0}
        for user in users:
            attrs = user.get("attributes", {})
            tier = _get_attr_value(attrs, "subscription_tier", "trial")
            if tier in tiers:
                tiers[tier] += 1

        # Count email verified users
        email_verified = sum(1 for u in users if u.get("emailVerified", False))

        return {
            "total_users": total_users,
            "active_users": active_users,
            "suspended_users": suspended_users,
            "email_verified": email_verified,
            "tier_distribution": tiers,
            "growth_this_month": 0,  # TODO: Calculate from creation timestamps
            "churn_rate": 0.0  # TODO: Calculate from subscription status changes
        }

    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roles/available")
async def get_available_roles(admin: bool = Depends(require_admin)):
    """Get list of available roles"""
    return {
        "roles": [
            {"name": "admin", "description": "Full system access", "level": 1},
            {"name": "moderator", "description": "User & content management", "level": 2},
            {"name": "developer", "description": "Service access & API keys", "level": 3},
            {"name": "analyst", "description": "Read-only analytics", "level": 4},
            {"name": "viewer", "description": "Basic read access", "level": 5}
        ]
    }

# ============================================================================
# INDIVIDUAL USER OPERATIONS
# ============================================================================

@router.get("/{user_id}")
async def get_user_details(user_id: str, admin: bool = Depends(require_admin)):
    """Get detailed information about a specific user"""
    try:
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        attrs = user.get("attributes", {})

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "enabled": user.get("enabled", True),
            "emailVerified": user.get("emailVerified", False),
            "createdTimestamp": user.get("createdTimestamp"),
            "subscription_tier": _get_attr_value(attrs, "subscription_tier", "trial"),
            "subscription_status": _get_attr_value(attrs, "subscription_status", "active"),
            "api_calls_limit": _get_attr_value(attrs, "api_calls_limit", "1000"),
            "api_calls_used": _get_attr_value(attrs, "api_calls_used", "0"),
            "api_calls_reset_date": _get_attr_value(attrs, "api_calls_reset_date"),
            "org_id": _get_attr_value(attrs, "org_id"),
            "org_name": _get_attr_value(attrs, "org_name"),
            "org_role": _get_attr_value(attrs, "org_role", "member"),
            "byok_enabled": _get_attr_value(attrs, "byok_enabled", "false") == "true",
            "last_login": _get_attr_value(attrs, "last_login"),
            "attributes": attrs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    updates: Dict[str, Any],
    admin: bool = Depends(require_admin)
):
    """Update user details"""
    try:
        # Update user in Keycloak
        success = await keycloak_update_user(user_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        # Get updated user
        updated_user = await get_user_by_id(user_id)
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(user_id: str, admin: bool = Depends(require_admin)):
    """Delete a user"""
    try:
        success = await keycloak_delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    admin: bool = Depends(require_admin)
):
    """Reset a user's password by emailing them a secure Keycloak set-password link.

    Uses the realm's SMTP (Postmark) + UPDATE_PASSWORD required-action email — no
    password is ever generated, stored, or transmitted by us. The user clicks the
    link and chooses their own password. Link valid 12h.
    """
    try:
        result = await send_account_action_email(user_id, ["UPDATE_PASSWORD"], lifespan=43200)
        if not result.get("success"):
            # 404 if the user_id is unknown; otherwise surface the SMTP/KC reason.
            code = result.get("status_code")
            raise HTTPException(
                status_code=404 if code == 404 else 502,
                detail=result.get("message", "Failed to send reset email"),
            )
        return {
            "message": "Password reset email sent. The user can set a new password via the secure link.",
            "delivery": "keycloak-email",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/send-onboarding-email")
async def send_onboarding_email(
    user_id: str,
    admin: bool = Depends(require_admin)
):
    """Send a new user the onboarding email: set-password + verify-email links.

    The self-service alternative to manually setting a password via kcadm. Lets an
    admin provision an account (no password) and have Keycloak email the user a
    secure link to choose their own password and verify their address. Link valid 7d.
    """
    try:
        result = await send_account_action_email(
            user_id, ["UPDATE_PASSWORD", "VERIFY_EMAIL"], lifespan=604800
        )
        if not result.get("success"):
            code = result.get("status_code")
            raise HTTPException(
                status_code=404 if code == 404 else 502,
                detail=result.get("message", "Failed to send onboarding email"),
            )
        return {
            "message": "Onboarding email sent (set password + verify email).",
            "actions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
            "delivery": "keycloak-email",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending onboarding email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

@router.get("/{user_id}/roles")
async def get_user_roles_endpoint(user_id: str, admin: bool = Depends(require_admin)):
    """Get user's current roles"""
    try:
        # TODO: Implement role retrieval from Keycloak
        # For now, return empty list
        return {"roles": []}
    except Exception as e:
        logger.error(f"Error getting user roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/roles/assign")
async def assign_role(
    user_id: str,
    role: str,
    admin: bool = Depends(require_admin)
):
    """Assign a realm role to a user (Keycloak role-mappings API)"""
    try:
        result = await _assign_realm_roles(user_id, [role])
        if result["assigned"]:
            return {"message": f"Role '{role}' assigned successfully", "assigned": result["assigned"]}
        error = (result["failed"][0].get("error") if result["failed"] else "Unknown error")
        status = 404 if "not found" in str(error).lower() else 502
        raise HTTPException(status_code=status, detail=f"Failed to assign role '{role}': {error}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/roles/{role}")
async def remove_role(
    user_id: str,
    role: str,
    admin: bool = Depends(require_admin)
):
    """Remove a realm role from a user (Keycloak role-mappings API)"""
    try:
        removed = await _remove_realm_role(user_id, role)
        if not removed:
            raise HTTPException(status_code=404, detail=f"Role '{role}' not found or not removable")
        return {"message": f"Role '{role}' removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@router.get("/{user_id}/sessions")
async def get_user_sessions_endpoint(user_id: str, admin: bool = Depends(require_admin)):
    """Get user's active sessions"""
    try:
        # TODO: Implement session retrieval from Keycloak
        return {"sessions": []}
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/sessions/{session_id}")
async def revoke_session(
    user_id: str,
    session_id: str,
    admin: bool = Depends(require_admin)
):
    """Revoke a specific user session"""
    try:
        # TODO: Implement session revocation in Keycloak
        return {"message": "Session revoked successfully (not yet implemented)"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/sessions")
async def revoke_all_sessions(user_id: str, admin: bool = Depends(require_admin)):
    """Revoke all user sessions"""
    try:
        # TODO: Implement session revocation in Keycloak
        return {"message": "All sessions revoked successfully (not yet implemented)"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk/delete")
async def bulk_delete_users(
    request: BulkOperationRequest,
    admin: bool = Depends(require_admin)
):
    """Delete multiple users"""
    try:
        results = {"success": [], "failed": []}

        for user_id in request.user_ids:
            try:
                success = await keycloak_delete_user(user_id)
                if success:
                    results["success"].append(user_id)
                else:
                    results["failed"].append({"user_id": user_id, "error": "User not found"})
            except Exception as e:
                results["failed"].append({"user_id": user_id, "error": str(e)})

        return results

    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/assign-roles")
async def bulk_assign_roles(
    request: BulkRoleAssignment,
    admin: bool = Depends(require_admin)
):
    """Assign role to multiple users"""
    try:
        results = {"success": [], "failed": []}

        # TODO: Implement bulk role assignment
        for user_id in request.user_ids:
            results["failed"].append({"user_id": user_id, "error": "Bulk role assignment not yet implemented"})

        return results

    except Exception as e:
        logger.error(f"Error in bulk role assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/set-tier")
async def bulk_set_tier(
    request: BulkTierChange,
    admin: bool = Depends(require_admin)
):
    """Change subscription tier for multiple users"""
    try:
        results = {"success": [], "failed": []}

        for user_id in request.user_ids:
            try:
                success = await set_subscription_tier(user_id, request.tier)
                if success:
                    results["success"].append(user_id)
                else:
                    results["failed"].append({"user_id": user_id, "error": "Failed to update tier"})
            except Exception as e:
                results["failed"].append({"user_id": user_id, "error": str(e)})

        return results

    except Exception as e:
        logger.error(f"Error in bulk tier change: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_users_csv(admin: bool = Depends(require_admin)):
    """Export all users to CSV"""
    try:
        users = await get_all_users()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id", "username", "email", "firstName", "lastName",
            "enabled", "emailVerified", "subscription_tier", "subscription_status",
            "api_calls_limit", "api_calls_used", "org_id", "org_name"
        ])
        writer.writeheader()

        for user in users:
            attrs = user.get("attributes", {})
            writer.writerow({
                "id": user.get("id", ""),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "enabled": user.get("enabled", True),
                "emailVerified": user.get("emailVerified", False),
                "subscription_tier": _get_attr_value(attrs, "subscription_tier", "trial"),
                "subscription_status": _get_attr_value(attrs, "subscription_status", "active"),
                "api_calls_limit": _get_attr_value(attrs, "api_calls_limit", "1000"),
                "api_calls_used": _get_attr_value(attrs, "api_calls_used", "0"),
                "org_id": _get_attr_value(attrs, "org_id", ""),
                "org_name": _get_attr_value(attrs, "org_name", "")
            })

        # Return CSV file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/import")
async def import_users_csv(
    file: UploadFile = File(...),
    admin: bool = Depends(require_admin)
):
    """Import users from CSV file"""
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)

        results = {"success": [], "failed": []}

        for row in reader:
            try:
                # Create user in Keycloak (create_user takes kwargs, not a dict)
                user_id = await keycloak_create_user(
                    email=row.get("email"),
                    username=row.get("username") or row.get("email"),
                    first_name=row.get("firstName", ""),
                    last_name=row.get("lastName", ""),
                    attributes={
                        "subscription_tier": [row.get("subscription_tier", "trial")],
                        "subscription_status": [row.get("subscription_status", "active")],
                        "api_calls_limit": [row.get("api_calls_limit", "1000")],
                        "api_calls_used": ["0"],
                    },
                    email_verified=(row.get("emailVerified", "false") or "false").lower() == "true",
                )
                if user_id:
                    if (row.get("enabled", "true") or "true").lower() != "true":
                        await _set_user_enabled(user_id, False)
                    results["success"].append(row.get("email"))
                else:
                    results["failed"].append({"email": row.get("email"), "error": "Failed to create user"})

            except Exception as e:
                results["failed"].append({"email": row.get("email"), "error": str(e)})

        return results

    except Exception as e:
        logger.error(f"Error importing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PLACEHOLDER ENDPOINTS (To be implemented)
# ============================================================================

@router.get("/{user_id}/activity")
async def get_user_activity(user_id: str, admin: bool = Depends(require_admin)):
    """Get user activity timeline"""
    # TODO: Implement activity tracking
    return {"activities": [], "message": "Activity tracking not yet implemented"}

@router.post("/{user_id}/api-keys")
async def generate_api_key(
    user_id: str,
    request: APIKeyCreate,
    admin: bool = Depends(require_admin),
    app_state: Any = Depends(lambda: None)
):
    """
    Generate API key for user

    Creates a secure API key for external application authentication.
    The key is shown ONCE and cannot be retrieved again.
    """
    from api_key_manager import get_api_key_manager

    try:
        manager = get_api_key_manager()

        # Create API key
        result = await manager.create_api_key(
            user_id=user_id,
            key_name=request.name,
            expires_in_days=request.expires_in_days,
            permissions=request.permissions or ["llm:inference", "llm:models"]
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to generate API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

@router.get("/{user_id}/api-keys")
async def list_api_keys(user_id: str, admin: bool = Depends(require_admin)):
    """
    List user's API keys

    Returns all API keys for the user (masked - actual keys are never shown again)
    """
    from api_key_manager import get_api_key_manager

    try:
        manager = get_api_key_manager()
        keys = await manager.list_user_keys(user_id)

        return {
            "success": True,
            "api_keys": keys,
            "total": len(keys)
        }
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@router.delete("/{user_id}/api-keys/{key_id}")
async def revoke_api_key(
    user_id: str,
    key_id: str,
    admin: bool = Depends(require_admin)
):
    """
    Revoke user's API key

    Permanently disables the specified API key. This action cannot be undone.
    """
    from api_key_manager import get_api_key_manager

    try:
        manager = get_api_key_manager()
        success = await manager.revoke_key(user_id, key_id)

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        return {
            "success": True,
            "message": f"API key {key_id} revoked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

@router.post("/{user_id}/impersonate/start")
async def start_impersonation(
    user_id: str,
    request: ImpersonationRequest,
    admin: bool = Depends(require_admin)
):
    """Start impersonating user"""
    # TODO: Implement user impersonation
    return {"message": "User impersonation not yet implemented"}

@router.post("/{user_id}/impersonate/stop")
async def stop_impersonation(user_id: str, admin: bool = Depends(require_admin)):
    """Stop impersonating user"""
    # TODO: Implement impersonation stop
    return {"message": "User impersonation not yet implemented"}
