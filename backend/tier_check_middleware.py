"""
Tier Check ForwardAuth Endpoint for Traefik

This module provides a ForwardAuth endpoint that Traefik can use to enforce
tier-based access control. It checks if the authenticated user has the required
subscription tier to access a resource.

Usage:
    - Traefik calls this endpoint before forwarding to protected service
    - Returns 200 OK if user has required tier
    - Returns 403 Forbidden if user doesn't have required tier
    - Returns 401 Unauthorized if user is not authenticated
"""

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
import os
import logging
from typing import Optional

# Import Keycloak integration
try:
    from keycloak_integration import get_user_by_email
    KEYCLOAK_AVAILABLE = True
except ImportError:
    KEYCLOAK_AVAILABLE = False

router = APIRouter(prefix="/api/v1/tier-check", tags=["Tier Enforcement"])

logger = logging.getLogger(__name__)

# Tier hierarchy (lower value = higher tier)
TIER_HIERARCHY = {
    "enterprise": 1,
    "professional": 2,
    "starter": 3,
    "trial": 4,
    "free": 5
}

# Default tier requirements for different services
SERVICE_TIER_REQUIREMENTS = {
    "billing": "professional",  # Lago billing requires Professional+
    "admin": "enterprise",      # Admin features require Enterprise
    "byok": "starter",          # BYOK requires Starter+
    "default": "trial"          # Default access for any authenticated user
}


def tier_meets_requirement(user_tier: str, required_tier: str) -> bool:
    """
    Check if user's tier meets the requirement.

    Args:
        user_tier: User's current subscription tier
        required_tier: Minimum required tier

    Returns:
        True if user tier meets or exceeds requirement
    """
    user_level = TIER_HIERARCHY.get(user_tier.lower(), 999)
    required_level = TIER_HIERARCHY.get(required_tier.lower(), 999)

    return user_level <= required_level


async def get_user_tier(email: str) -> Optional[str]:
    """
    Get user's subscription tier from Keycloak.

    Args:
        email: User's email address

    Returns:
        Subscription tier string or None if not found
    """
    if not KEYCLOAK_AVAILABLE:
        logger.warning("Keycloak integration not available, allowing access")
        return "enterprise"  # Fail open in development

    try:
        user = await get_user_by_email(email)
        if not user:
            return None

        # Keycloak stores attributes as arrays
        attributes = user.get("attributes", {})
        tier_list = attributes.get("subscription_tier", ["trial"])
        tier = tier_list[0] if tier_list else "trial"

        logger.info(f"User {email} has tier: {tier}")
        return tier

    except Exception as e:
        logger.error(f"Error fetching user tier for {email}: {e}")
        return None


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "tier-check",
        "keycloak_available": KEYCLOAK_AVAILABLE
    }


@router.get("/check")
@router.post("/check")
async def check_tier_access(
    request: Request,
    required_tier: str = "trial"
):
    """
    ForwardAuth endpoint for Traefik to check tier-based access.

    Headers expected from OAuth2 Proxy:
        X-Auth-Request-User: Username
        X-Auth-Request-Email: User's email
        X-Forwarded-Uri: Original request URI

    Query parameters:
        required_tier: Minimum tier required (default: trial)

    Returns:
        200 OK: User has required tier, allow access
        403 Forbidden: User doesn't have required tier
        401 Unauthorized: User not authenticated
    """
    # Extract user email from OAuth2 Proxy headers
    user_email = request.headers.get("X-Auth-Request-Email")
    user_name = request.headers.get("X-Auth-Request-User")
    original_uri = request.headers.get("X-Forwarded-Uri", "/")

    # Check if user is authenticated
    if not user_email:
        logger.warning(f"Tier check failed: No authenticated user for {original_uri}")
        return Response(
            content="Authentication required",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Determine required tier (can be overridden via query param)
    tier_requirement = request.query_params.get("tier", required_tier)

    # Special handling: infer tier from URI path if not explicitly provided
    if tier_requirement == "trial":
        if "/billing" in original_uri or "billing." in request.headers.get("Host", ""):
            tier_requirement = SERVICE_TIER_REQUIREMENTS.get("billing", "professional")
        elif "/admin" in original_uri:
            tier_requirement = SERVICE_TIER_REQUIREMENTS.get("admin", "enterprise")

    # Get user's current tier
    user_tier = await get_user_tier(user_email)

    if not user_tier:
        logger.error(f"Could not determine tier for user {user_email}")
        return Response(
            content="Could not verify subscription tier",
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Check if user's tier meets requirement
    if tier_meets_requirement(user_tier, tier_requirement):
        logger.info(
            f"Tier check PASSED: {user_email} ({user_tier}) accessing "
            f"{original_uri} (requires {tier_requirement})"
        )

        # Return 200 OK with user info headers
        return Response(
            status_code=status.HTTP_200_OK,
            headers={
                "X-User-Email": user_email,
                "X-User-Tier": user_tier,
                "X-Tier-Required": tier_requirement
            }
        )
    else:
        logger.warning(
            f"Tier check FAILED: {user_email} ({user_tier}) attempted to access "
            f"{original_uri} (requires {tier_requirement})"
        )

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "insufficient_tier",
                "message": f"This feature requires {tier_requirement.title()} tier or higher",
                "current_tier": user_tier,
                "required_tier": tier_requirement,
                "upgrade_url": "https://unicorncommander.ai/subscription"
            }
        )


@router.get("/billing")
async def check_billing_access(request: Request):
    """
    Dedicated endpoint for checking Lago billing access.
    Requires Professional tier or higher.
    """
    return await check_tier_access(request, required_tier="professional")


@router.get("/admin")
async def check_admin_access(request: Request):
    """
    Dedicated endpoint for checking admin access.
    Requires Enterprise tier.
    """
    return await check_tier_access(request, required_tier="enterprise")


@router.get("/byok")
async def check_byok_access(request: Request):
    """
    Dedicated endpoint for checking BYOK access.
    Requires Starter tier or higher.
    """
    return await check_tier_access(request, required_tier="starter")
