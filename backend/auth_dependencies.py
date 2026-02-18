"""
Authentication Dependencies for FastAPI
========================================

Provides reusable FastAPI dependencies for authentication that run BEFORE
request body validation, preventing information disclosure through validation errors.

Author: Ops-Center Security Team
Created: 2025-11-12
"""

from fastapi import Request, HTTPException, Depends
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def require_authenticated_user(request: Request) -> Dict[str, Any]:
    """
    Dependency that requires authentication BEFORE body validation.

    This runs before FastAPI/Pydantic validates the request body,
    preventing information disclosure through validation errors.

    Usage:
        @router.post("/endpoint")
        async def my_endpoint(
            user: Dict = Depends(require_authenticated_user),
            data: MyModel  # ← Validation happens AFTER auth check
        ):
            # user is already authenticated here

    Returns:
        Dict: User data from session (includes user_id, email, roles, etc.)

    Raises:
        HTTPException(401): If not authenticated
    """
    import sys
    import os

    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Check for session token in cookie
    session_token = request.cookies.get("session_token")
    logger.info(f"[AUTH-DEBUG] Session token from cookie: {session_token[:20] if session_token else 'None'}...")
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login to access this resource."
        )

    # Get Redis connection
    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please login again."
        )

    # Debug: Log session structure
    logger.info(f"Session data keys: {list(session_data.keys()) if isinstance(session_data, dict) else type(session_data)}")

    # Session structure: {"user": {user_info}, "access_token": ..., "org_id": ..., ...}
    # Extract user info from the nested "user" key
    user_data = session_data.get("user", {})

    # Debug: Log user data
    logger.info(f"User data from session: email={user_data.get('email') if user_data else 'None'}, role={user_data.get('role') if user_data else 'None'}")

    logger.info(f"[AUTH-DEBUG] User data type: {type(user_data)}, empty: {not user_data}")
    if not user_data:
        logger.warning(f"[AUTH-DEBUG] Empty user_data. Session keys: {list(session_data.keys()) if session_data else 'None'}")
        raise HTTPException(
            status_code=401,
            detail="Session missing user data. Please login again."
        )

    # Ensure user_id field exists (map from Keycloak 'sub' if needed)
    if "user_id" not in user_data:
        user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

    # Copy org context from session to user data for convenience
    user_data["org_id"] = session_data.get("org_id")
    user_data["org_name"] = session_data.get("org_name")
    user_data["org_role"] = session_data.get("org_role")

    logger.debug(f"Authenticated user: {user_data.get('email', 'unknown')}")
    return user_data


async def require_admin_user(request: Request) -> Dict[str, Any]:
    """
    Dependency that requires admin authentication BEFORE body validation.

    This checks both authentication AND admin role before request processing.

    Usage:
        @router.post("/admin-endpoint")
        async def admin_endpoint(
            user: Dict = Depends(require_admin_user),
            data: MyModel
        ):
            # user is already authenticated AND verified as admin

    Returns:
        Dict: User data from session

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If not admin
    """
    # First check authentication
    user = await require_authenticated_user(request)

    # Check admin role - session stores singular "role", not plural "roles"
    user_role = user.get("role", "")
    user_roles = user.get("roles", [])  # Fallback for legacy sessions

    # Check both singular role and roles array for compatibility
    is_admin = (
        user_role == "admin" or
        user_role == "system_admin" or
        "admin" in user_roles or
        "system_admin" in user_roles
    )

    if not is_admin:
        logger.warning(f"Non-admin user {user.get('email')} (role: {user_role}) attempted admin access")
        raise HTTPException(
            status_code=403,
            detail="Admin access required. You do not have permission to access this resource."
        )

    return user


async def require_org_admin(request: Request, org_id: str) -> Dict[str, Any]:
    """
    Dependency that requires org admin authentication BEFORE body validation.

    Checks if user is either:
    1. System admin (can access any org)
    2. Organization admin for the specified org

    Usage:
        @router.post("/orgs/{org_id}/endpoint")
        async def org_endpoint(
            org_id: str,
            user: Dict = Depends(lambda r: require_org_admin(r, org_id)),
            data: MyModel
        ):
            # user is already verified as org admin

    Args:
        request: FastAPI request object
        org_id: Organization UUID to check membership

    Returns:
        Dict: User data from session

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If not authorized for this org
    """
    import asyncpg
    from database import get_db_connection

    # First check authentication
    user = await require_authenticated_user(request)

    # Check if system admin (can access any org)
    user_role = user.get("role", "")
    user_roles = user.get("roles", [])  # Fallback for legacy sessions
    is_system_admin = (
        user_role == "admin" or
        user_role == "system_admin" or
        "admin" in user_roles or
        "system_admin" in user_roles
    )

    if is_system_admin:
        return user

    # Check org membership and role
    conn = await get_db_connection()
    try:
        member = await conn.fetchrow(
            """
            SELECT role FROM organization_members
            WHERE org_id = $1 AND user_id = $2
            """,
            org_id, user["user_id"]
        )

        if not member:
            logger.warning(
                f"User {user.get('email')} attempted access to org {org_id} without membership"
            )
            raise HTTPException(
                status_code=403,
                detail="Not a member of this organization"
            )

        # Check if user has admin role in org
        if member["role"] not in ["admin", "owner"]:
            logger.warning(
                f"User {user.get('email')} attempted admin action in org {org_id} with role {member['role']}"
            )
            raise HTTPException(
                status_code=403,
                detail="Organization admin access required"
            )

        return user

    finally:
        await conn.close()
