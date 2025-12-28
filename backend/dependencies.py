"""
Centralized Dependency Injection Module
========================================

This module provides FastAPI dependency injection functions to avoid circular imports.
All dependencies that access app.state should be defined here.

Author: Backend Fix Team
Date: January 12, 2025
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional
import asyncpg
import sys
import os


# ============================================================================
# Database Dependencies
# ============================================================================

async def get_db_pool(request: Request) -> asyncpg.Pool:
    """
    Get database connection pool from app state.

    Usage:
        @router.get("/endpoint")
        async def endpoint(db_pool: asyncpg.Pool = Depends(get_db_pool)):
            async with db_pool.acquire() as conn:
                # Use connection
                pass
    """
    if not hasattr(request.app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database pool not initialized")

    return request.app.state.db_pool


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def require_admin(request: Request) -> bool:
    """
    Verify user is authenticated and has admin role.

    Returns:
        True if user is admin

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    # Add /app to path if not already present
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)
    user_data = sessions.get(session_token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Check if user has admin role
    user_roles = user_data.get("roles", [])
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    return True


async def get_current_user(request: Request) -> dict:
    """
    Get current authenticated user data from session.

    Returns:
        dict: User data including user_id, email, roles, etc.

    Raises:
        HTTPException: 401 if not authenticated
    """
    # Add /app to path if not already present
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)
    user_data = sessions.get(session_token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user_data


async def get_optional_user(request: Request) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.

    Returns:
        Optional[dict]: User data if authenticated, None otherwise
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


# ============================================================================
# Request Context Dependencies
# ============================================================================

async def get_request_context(request: Request) -> dict:
    """
    Get common request context including user, IP, user-agent, etc.

    Returns:
        dict: Request context including:
            - user: User data (if authenticated)
            - ip_address: Client IP
            - user_agent: User agent string
            - request_id: Unique request ID
    """
    user = await get_optional_user(request)

    # Get client IP (check for proxy headers first)
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or request.client.host if request.client else "unknown"
    )

    # Get user agent
    user_agent = request.headers.get("User-Agent", "unknown")

    # Generate request ID if not present
    request_id = request.headers.get("X-Request-ID", f"req_{int(request.state._start_time * 1000)}")

    return {
        "user": user,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id
    }


# ============================================================================
# Service Dependencies
# ============================================================================

async def get_redis_client(request: Request):
    """
    Get Redis client from app state.

    Returns:
        Redis: Redis client instance

    Raises:
        HTTPException: 500 if Redis not initialized
    """
    if not hasattr(request.app.state, 'redis'):
        raise HTTPException(status_code=500, detail="Redis not initialized")

    return request.app.state.redis


async def get_credit_system(request: Request):
    """
    Get CreditSystem instance from app state.

    Returns:
        CreditSystem: Credit system instance

    Raises:
        HTTPException: 500 if CreditSystem not initialized
    """
    if not hasattr(request.app.state, 'credit_system'):
        raise HTTPException(status_code=500, detail="Credit system not initialized")

    return request.app.state.credit_system


async def get_byok_manager(request: Request):
    """
    Get BYOKManager instance from app state.

    Returns:
        BYOKManager: BYOK manager instance

    Raises:
        HTTPException: 500 if BYOKManager not initialized
    """
    if not hasattr(request.app.state, 'byok_manager'):
        raise HTTPException(status_code=500, detail="BYOK manager not initialized")

    return request.app.state.byok_manager
