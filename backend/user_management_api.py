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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Request, UploadFile, File, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import bcrypt
import secrets
import string

# Import Keycloak integration functions
from keycloak_integration import (
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    create_user as keycloak_create_user,
    update_user_attributes as keycloak_update_user,
    delete_user as keycloak_delete_user,
    set_subscription_tier,
    set_user_password,
    _get_attr_value
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
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

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

    return True

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

        return {
            "users": paginated_users,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    """Reset user password (generates temporary password)"""
    try:
        # Generate temporary password
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

        # Set password in Keycloak
        success = await set_user_password(user_id, temp_password, temporary=True)

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        # TODO: Implement email sending
        # For now, log securely and return message
        logger.info(f"Password reset for user {user_id} (temp password generated but not returned for security)")
        return {
            "message": "Password reset successfully. A new temporary password has been set.",
            "note": "The user will need to contact admin to receive the password securely, or implement email notification."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
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
    """Assign a role to user"""
    try:
        # TODO: Implement role assignment in Keycloak
        return {"message": f"Role '{role}' assigned successfully (not yet implemented)"}
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
    """Remove a role from user"""
    try:
        # TODO: Implement role removal in Keycloak
        return {"message": f"Role '{role}' removed successfully (not yet implemented)"}
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
                # Create user in Keycloak
                user_data = {
                    "username": row.get("username"),
                    "email": row.get("email"),
                    "firstName": row.get("firstName", ""),
                    "lastName": row.get("lastName", ""),
                    "enabled": row.get("enabled", "true").lower() == "true",
                    "emailVerified": row.get("emailVerified", "false").lower() == "true",
                    "attributes": {
                        "subscription_tier": [row.get("subscription_tier", "trial")],
                        "subscription_status": [row.get("subscription_status", "active")],
                        "api_calls_limit": [row.get("api_calls_limit", "1000")],
                        "api_calls_used": ["0"]
                    }
                }

                user_id = await keycloak_create_user(user_data)
                if user_id:
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
