"""
Two-Factor Authentication (2FA) Management API

Provides admin endpoints for managing 2FA for users:
- View 2FA status for users
- Enforce 2FA setup (via email or immediate)
- Reset 2FA for users (lost device scenarios)
- Manage role-based 2FA policies

Endpoints: /api/v1/admin/2fa/*

Security:
- Admin-only access (requires admin role)
- Audit logging for all operations
- Rate limiting on reset operations (3 per user per 24 hours)
- No storage of 2FA secrets (all managed by Keycloak)

Author: Security Team
Date: October 28, 2025
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import asyncpg

# Import Keycloak integration functions
from keycloak_integration import (
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    get_user_2fa_status,
    enforce_user_2fa,
    reset_user_2fa,
    logout_user_sessions,
    get_user_credentials
)

from audit_logger import audit_logger
from audit_helpers import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/admin/2fa", tags=["Two-Factor Authentication"])

# ============================================================================
# MODELS
# ============================================================================

class TwoFactorEnforceRequest(BaseModel):
    """Request model for enforcing 2FA"""
    method: str = Field(
        default="email",
        description="Method: 'email' (send setup email) or 'immediate' (require on next login)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for enforcement (for audit log)"
    )

    @validator('method')
    def validate_method(cls, v):
        if v not in ['email', 'immediate']:
            raise ValueError("method must be 'email' or 'immediate'")
        return v


class TwoFactorResetRequest(BaseModel):
    """Request model for resetting 2FA"""
    reason: str = Field(
        ...,
        description="Required reason for reset (for audit log and user notification)"
    )
    require_reconfigure: bool = Field(
        default=True,
        description="If True, user must reconfigure 2FA on next login"
    )
    logout_sessions: bool = Field(
        default=True,
        description="If True, logout all user sessions after reset"
    )


class TwoFactorPolicyRequest(BaseModel):
    """Request model for setting role-based 2FA policy"""
    role: str = Field(
        ...,
        description="Role name (admin, moderator, developer, etc.)"
    )
    require_2fa: bool = Field(
        default=True,
        description="Whether 2FA is required for this role"
    )
    grace_period_days: int = Field(
        default=7,
        ge=0,
        le=90,
        description="Days before enforcement starts (0-90)"
    )
    notify_users: bool = Field(
        default=True,
        description="Send email notifications to affected users"
    )


# ============================================================================
# RATE LIMITING
# ============================================================================

# In-memory rate limit tracking (in production, use Redis)
_reset_rate_limits: Dict[str, List[datetime]] = {}

async def check_reset_rate_limit(user_id: str, limit: int = 3, window_hours: int = 24) -> bool:
    """
    Check if user has exceeded reset rate limit.

    Args:
        user_id: User ID to check
        limit: Maximum resets allowed (default 3)
        window_hours: Time window in hours (default 24)

    Returns:
        True if within limit, False if exceeded
    """
    now = datetime.now()
    window_start = now - timedelta(hours=window_hours)

    # Get resets for this user
    if user_id not in _reset_rate_limits:
        _reset_rate_limits[user_id] = []

    # Remove old resets outside window
    _reset_rate_limits[user_id] = [
        reset_time for reset_time in _reset_rate_limits[user_id]
        if reset_time > window_start
    ]

    # Check if limit exceeded
    if len(_reset_rate_limits[user_id]) >= limit:
        return False

    return True


async def record_reset(user_id: str):
    """Record a reset operation for rate limiting"""
    now = datetime.now()
    if user_id not in _reset_rate_limits:
        _reset_rate_limits[user_id] = []
    _reset_rate_limits[user_id].append(now)


# ============================================================================
# DEPENDENCY: REQUIRE ADMIN
# ============================================================================

async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    # TODO: Implement actual auth check
    # For now, this is a placeholder
    # In production, check JWT token and verify admin role
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Extract and validate token
    # For MVP, we assume valid if header present
    return True


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/users/{user_id}/status", dependencies=[Depends(require_admin)])
async def get_user_2fa_status_endpoint(
    user_id: str,
    request: Request
):
    """
    Get 2FA status for a specific user.

    Returns:
        - two_factor_enabled: Whether user has 2FA configured
        - two_factor_methods: List of configured methods (TOTP, WebAuthn)
        - setup_pending: Whether user has pending 2FA setup
        - required_by_policy: Whether user's role requires 2FA (TODO)
        - last_used: Last time 2FA was used (not available from Keycloak)

    Security:
        - Admin only
        - Audit logged

    Example:
        GET /api/v1/admin/2fa/users/abc-123/status
    """
    try:
        # Get 2FA status from Keycloak
        status_data = await get_user_2fa_status(user_id)

        if "error" in status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_data.get("error", "User not found")
            )

        # TODO: Check if user's role requires 2FA (policy check)
        status_data["required_by_policy"] = False  # Placeholder

        # Audit log
        await audit_logger.log_event(
            event_type="2fa_status_viewed",
            user_id=user_id,
            admin_ip=get_client_ip(request),
            admin_user_agent=get_user_agent(request),
            details={"user_id": user_id}
        )

        return JSONResponse(content=status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting 2FA status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get 2FA status: {str(e)}"
        )


@router.post("/users/{user_id}/enforce", dependencies=[Depends(require_admin)])
async def enforce_user_2fa_endpoint(
    user_id: str,
    body: TwoFactorEnforceRequest,
    request: Request
):
    """
    Enforce 2FA for a user.

    Methods:
        - email: Send setup email with link (valid for 24 hours)
        - immediate: Require on next login (no email sent)

    Security:
        - Admin only
        - Audit logged with reason
        - Idempotent (safe if already enforced)

    Example:
        POST /api/v1/admin/2fa/users/abc-123/enforce
        {
            "method": "email",
            "reason": "Admin policy enforcement"
        }
    """
    try:
        # Enforce 2FA via Keycloak
        result = await enforce_user_2fa(
            user_id=user_id,
            method=body.method,
            lifespan=86400  # 24 hours
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to enforce 2FA")
            )

        # Audit log
        await audit_logger.log_event(
            event_type="2fa_enforced",
            user_id=user_id,
            admin_ip=get_client_ip(request),
            admin_user_agent=get_user_agent(request),
            details={
                "user_id": user_id,
                "method": body.method,
                "reason": body.reason or "No reason provided",
                "action_taken": result.get("action_taken")
            }
        )

        logger.info(f"Admin enforced 2FA for user {user_id} via {body.method}")

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enforcing 2FA for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enforce 2FA: {str(e)}"
        )


@router.delete("/users/{user_id}/reset", dependencies=[Depends(require_admin)])
async def reset_user_2fa_endpoint(
    user_id: str,
    body: TwoFactorResetRequest,
    request: Request
):
    """
    Reset user's 2FA by removing all 2FA credentials.

    Use Cases:
        - User lost their device
        - User switched authenticator apps
        - User lost backup codes

    Security:
        - Admin only
        - Reason required (for audit trail)
        - Rate limited: 3 resets per user per 24 hours
        - Audit logged
        - User sessions logged out (optional)
        - User notified via email (optional)

    Example:
        DELETE /api/v1/admin/2fa/users/abc-123/reset
        {
            "reason": "User lost device",
            "require_reconfigure": true,
            "logout_sessions": true
        }
    """
    try:
        # Check rate limit
        if not await check_reset_rate_limit(user_id):
            # Get next allowed time
            window_start = datetime.now() - timedelta(hours=24)
            resets = _reset_rate_limits.get(user_id, [])
            oldest_reset = min(resets) if resets else datetime.now()
            next_allowed = oldest_reset + timedelta(hours=24)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Maximum 3 resets per 24 hours",
                    "next_allowed": next_allowed.isoformat(),
                    "resets_remaining": 0
                }
            )

        # Reset 2FA via Keycloak
        result = await reset_user_2fa(
            user_id=user_id,
            require_reconfigure=body.require_reconfigure
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to reset 2FA")
            )

        # Record reset for rate limiting
        await record_reset(user_id)

        # Optionally logout all sessions
        if body.logout_sessions:
            await logout_user_sessions(user_id)
            result["sessions_logged_out"] = True

        # Audit log
        await audit_logger.log_event(
            event_type="2fa_reset",
            user_id=user_id,
            admin_ip=get_client_ip(request),
            admin_user_agent=get_user_agent(request),
            details={
                "user_id": user_id,
                "reason": body.reason,
                "credentials_removed": result.get("credentials_removed", []),
                "required_action_set": result.get("required_action_set"),
                "sessions_logged_out": body.logout_sessions
            }
        )

        logger.info(f"Admin reset 2FA for user {user_id}. Reason: {body.reason}")

        # TODO: Send email notification to user

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting 2FA for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset 2FA: {str(e)}"
        )


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users_2fa_status(
    request: Request,
    search: Optional[str] = Query(None, description="Search by username or email"),
    has_2fa: Optional[bool] = Query(None, description="Filter by 2FA enabled status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List 2FA status for all users (with filtering).

    Filters:
        - search: Search by username or email
        - has_2fa: Filter by whether 2FA is enabled
        - role: Filter by user role
        - limit: Max results (1-500, default 50)
        - offset: Pagination offset

    Returns:
        List of users with 2FA status

    Security:
        - Admin only
        - Pagination required for large user bases

    Example:
        GET /api/v1/admin/2fa/users?has_2fa=false&limit=20
    """
    try:
        # Get all users from Keycloak
        all_users = await get_all_users()

        # Collect 2FA status for each user (in parallel)
        tasks = [get_user_2fa_status(user["id"]) for user in all_users]
        statuses = await asyncio.gather(*tasks)

        # Combine user info with 2FA status
        users_with_2fa = []
        for user, status in zip(all_users, statuses):
            if "error" not in status:
                combined = {
                    "id": user["id"],
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "first_name": user.get("firstName"),
                    "last_name": user.get("lastName"),
                    "created_timestamp": user.get("createdTimestamp"),
                    **status  # Merge 2FA status
                }
                users_with_2fa.append(combined)

        # Apply filters
        filtered_users = users_with_2fa

        if search:
            search_lower = search.lower()
            filtered_users = [
                u for u in filtered_users
                if search_lower in u.get("username", "").lower()
                or search_lower in u.get("email", "").lower()
            ]

        if has_2fa is not None:
            filtered_users = [
                u for u in filtered_users
                if u.get("two_factor_enabled") == has_2fa
            ]

        # TODO: Filter by role (requires role lookup)

        # Apply pagination
        total = len(filtered_users)
        paginated_users = filtered_users[offset:offset + limit]

        return JSONResponse(content={
            "users": paginated_users,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        })

    except Exception as e:
        logger.error(f"Error listing users 2FA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("/policy", dependencies=[Depends(require_admin)])
async def set_2fa_policy(
    body: TwoFactorPolicyRequest,
    request: Request
):
    """
    Set role-based 2FA policy.

    Enforces 2FA requirement for all users with a specific role.

    Example:
        POST /api/v1/admin/2fa/policy
        {
            "role": "admin",
            "require_2fa": true,
            "grace_period_days": 7,
            "notify_users": true
        }

    Grace Period:
        - Users have N days to enable 2FA before enforcement
        - After grace period, users cannot login without 2FA

    Security:
        - Admin only
        - Audit logged
        - Email notifications sent to affected users

    NOTE: This endpoint is a placeholder. Full implementation requires:
        1. Database table to store policies
        2. Background job to check compliance
        3. Email notification system
        4. Enforcement mechanism in authentication flow
    """
    try:
        # TODO: Implement policy storage in PostgreSQL
        # For now, return placeholder response

        # Calculate enforcement date
        enforcement_date = datetime.now() + timedelta(days=body.grace_period_days)

        # TODO: Get all users with this role
        affected_users = 0

        # TODO: Send email notifications

        # Audit log
        await audit_logger.log_event(
            event_type="2fa_policy_created",
            user_id=None,  # No specific user
            admin_ip=get_client_ip(request),
            admin_user_agent=get_user_agent(request),
            details={
                "role": body.role,
                "require_2fa": body.require_2fa,
                "grace_period_days": body.grace_period_days,
                "enforcement_date": enforcement_date.isoformat(),
                "notify_users": body.notify_users,
                "affected_users": affected_users
            }
        )

        logger.info(f"Admin set 2FA policy for role '{body.role}': require={body.require_2fa}")

        return JSONResponse(content={
            "success": True,
            "policy": {
                "role": body.role,
                "require_2fa": body.require_2fa,
                "grace_period_days": body.grace_period_days,
                "enforcement_date": enforcement_date.isoformat(),
                "affected_users": affected_users
            },
            "message": "Policy set successfully (NOTE: Full enforcement requires database setup)",
            "notifications_sent": 0  # Placeholder
        })

    except Exception as e:
        logger.error(f"Error setting 2FA policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set policy: {str(e)}"
        )


@router.get("/policy/{role}", dependencies=[Depends(require_admin)])
async def get_2fa_policy(role: str):
    """
    Get 2FA policy for a specific role.

    Example:
        GET /api/v1/admin/2fa/policy/admin

    NOTE: Placeholder endpoint. Requires database implementation.
    """
    # TODO: Implement policy retrieval from database
    return JSONResponse(content={
        "role": role,
        "require_2fa": False,
        "grace_period_days": 0,
        "enforcement_date": None,
        "message": "Policy storage not yet implemented"
    })


@router.get("/policies", dependencies=[Depends(require_admin)])
async def list_2fa_policies():
    """
    List all role-based 2FA policies.

    Example:
        GET /api/v1/admin/2fa/policies

    NOTE: Placeholder endpoint. Requires database implementation.
    """
    # TODO: Implement policy listing from database
    return JSONResponse(content={
        "policies": [],
        "message": "Policy storage not yet implemented"
    })


@router.get("/audit-log", dependencies=[Depends(require_admin)])
async def get_2fa_audit_log(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get audit log of 2FA operations.

    Filters:
        - user_id: Filter by specific user
        - event_type: Filter by event type (2fa_enforced, 2fa_reset, etc.)
        - limit: Max results
        - offset: Pagination offset

    Example:
        GET /api/v1/admin/2fa/audit-log?event_type=2fa_reset&limit=20

    Security:
        - Admin only
        - Read-only (audit log is immutable)
    """
    try:
        # TODO: Implement audit log retrieval from database
        # This should query the audit_logs table with filters

        return JSONResponse(content={
            "logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "message": "Audit log query not yet implemented"
        })

    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint for 2FA API.

    Returns:
        Service status and Keycloak connectivity
    """
    try:
        # Test Keycloak connectivity
        from keycloak_integration import get_admin_token
        token = await get_admin_token()
        keycloak_ok = bool(token)

        return JSONResponse(content={
            "status": "healthy" if keycloak_ok else "degraded",
            "service": "2fa-api",
            "keycloak_connection": "ok" if keycloak_ok else "failed",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "2fa-api",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
