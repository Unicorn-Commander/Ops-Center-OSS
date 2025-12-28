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
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login to access this resource."
        )

    # Get Redis connection
    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)
    user_data = sessions.get(session_token)

    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please login again."
        )

    # Ensure user_id field exists (map from Keycloak 'sub' if needed)
    if "user_id" not in user_data:
        user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

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

    # Check admin role
    user_roles = user.get("roles", [])
    is_admin = "admin" in user_roles or "system_admin" in user_roles

    if not is_admin:
        logger.warning(f"Non-admin user {user.get('email')} attempted admin access")
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
    user_roles = user.get("roles", [])
    is_system_admin = "admin" in user_roles or "system_admin" in user_roles

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
