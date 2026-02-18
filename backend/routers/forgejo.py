"""
Forgejo API Router for Ops-Center

Provides REST endpoints for Forgejo integration.

Author: Ops-Center AI
Created: November 8, 2025
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional, Dict, Any, List
import logging
import sys
import os

from services.forgejo_client import ForgejoClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/forgejo", tags=["forgejo"])

# Initialize Forgejo client
forgejo = ForgejoClient()


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(request: Request):
    """Verify user is authenticated (uses Redis session manager)"""
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

    return user


async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    user = await get_current_user(request)

    # Check if user has admin role
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return True


@router.get("/health")
async def get_forgejo_health(current_user: dict = Depends(get_current_user)):
    """
    Check Forgejo service health

    Returns:
        dict: Health status including online status and version
    """
    try:
        health = await forgejo.health_check()
        return {
            "service": "Forgejo",
            "url": forgejo.base_url,
            **health
        }
    except Exception as e:
        logger.error(f"Forgejo health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_forgejo_stats(current_user: dict = Depends(get_current_user)):
    """
    Get Forgejo instance statistics

    Returns:
        dict: Statistics including org count, repo count
    """
    try:
        stats = await forgejo.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to fetch Forgejo stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orgs")
async def get_all_organizations(admin: bool = Depends(require_admin)):
    """
    Get all Forgejo organizations (admin only)

    Returns:
        list: All organizations
    """
    try:
        orgs = await forgejo.get_all_orgs()
        return {"organizations": orgs, "count": len(orgs)}
    except Exception as e:
        logger.error(f"Failed to fetch organizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orgs/{org_name}/repos")
async def get_organization_repos(org_name: str, admin: bool = Depends(require_admin)):
    """
    Get repositories for specific organization

    Args:
        org_name: Organization name

    Returns:
        list: Organization's repositories
    """
    try:
        repos = await forgejo.get_org_repos(org_name)
        return {
            "organization": org_name,
            "repositories": repos,
            "count": len(repos)
        }
    except Exception as e:
        logger.error(f"Failed to fetch repos for {org_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# User endpoints (require user token in future)
@router.get("/user/repos")
async def get_user_repos(
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's repositories

    Note: Currently returns empty list. Will be implemented when
    user token management is added (Phase 2).

    Args:
        authorization: Bearer token (optional for now)

    Returns:
        list: User's repositories
    """
    # TODO: Extract user token from Keycloak session
    # TODO: Store/retrieve user's Forgejo token from database
    return {
        "repositories": [],
        "message": "User token integration coming in Phase 2"
    }


@router.get("/info")
async def get_forgejo_info(current_user: dict = Depends(get_current_user)):
    """
    Get Forgejo instance information

    Returns:
        dict: Instance info including URL, API base, status
    """
    try:
        health = await forgejo.health_check()
        stats = await forgejo.get_stats()

        return {
            "instance_url": forgejo.base_url,
            "api_base": f"{forgejo.base_url}/api/v1",
            "admin_url": f"{forgejo.base_url}/admin",
            "status": health.get("status", "unknown"),
            "online": health.get("online", False),
            "version": health.get("version", "unknown"),
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to fetch Forgejo info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
