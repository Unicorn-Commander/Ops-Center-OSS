"""
Tier Check API Endpoints

FastAPI routes for tier checking and access control.
Used by Traefik ForwardAuth and other services.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
from tier_middleware import (
    check_service_access,
    get_user_tier,
    get_rate_limit,
    get_concurrent_search_limit,
    SERVICE_ACCESS,
    TIER_LEVELS,
    RATE_LIMITS,
    CONCURRENT_SEARCH_LIMITS
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tier-check"])


@router.get("/check-tier")
async def check_tier_access(
    service: str = Query(..., description="Service name to check"),
    min_tier: str = Query(None, description="Minimum tier required"),
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Check if user has access to a service based on their subscription tier.

    Used by Traefik ForwardAuth middleware.

    Returns:
        200: Access granted
        401: Authentication required
        403: Upgrade required (tier too low)
    """
    # Get user info
    if not user_email and not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication required",
                "message": "Please log in to access this service"
            }
        )

    user_info = get_user_tier(user_id=user_id, email=user_email)

    if not user_info:
        return JSONResponse(
            status_code=401,
            content={
                "error": "User not found",
                "message": "Invalid user credentials"
            }
        )

    user_tier = user_info.get('subscription_tier', 'free')

    # Check service access
    has_access, required_tier, message = check_service_access(user_tier, service)

    if not has_access:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Upgrade required",
                "message": message,
                "current_tier": user_tier,
                "required_tier": required_tier,
                "upgrade_url": f"/billing#upgrade-{required_tier}",
                "service": service
            }
        )

    # Access granted
    return JSONResponse(
        status_code=200,
        content={
            "access": "granted",
            "user_tier": user_tier,
            "service": service,
            "message": "Access allowed"
        }
    )


@router.get("/user/tier")
async def get_user_tier_info(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    user_id: Optional[str] = Query(None)
):
    """
    Get user's subscription tier information.
    """
    if not user_email and not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_info = get_user_tier(user_id=user_id, email=user_email)

    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    user_tier = user_info.get('subscription_tier', 'free')

    return {
        "user_id": user_info.get('user_id'),
        "email": user_info.get('email'),
        "subscription_tier": user_tier,
        "tier_level": TIER_LEVELS.get(user_tier.lower(), 0),
        "rate_limit": get_rate_limit(user_tier),
        "concurrent_searches": get_concurrent_search_limit(user_tier),
        "services_available": [
            service for service, config in SERVICE_ACCESS.items()
            if check_service_access(user_tier, service)[0]
        ]
    }


@router.get("/services/access-matrix")
async def get_access_matrix(
    user_tier: Optional[str] = Query('free', description="User's subscription tier")
):
    """
    Get complete service access matrix for a given tier.

    Useful for frontend to display available services.
    """
    tier_level = TIER_LEVELS.get(user_tier.lower(), 0)

    services = {}
    for service_name, service_config in SERVICE_ACCESS.items():
        required_level = TIER_LEVELS.get(service_config['min_tier'].lower(), 0)
        has_access = tier_level >= required_level

        services[service_name] = {
            "name": service_name,
            "description": service_config['description'],
            "min_tier": service_config['min_tier'],
            "has_access": has_access,
            "requires_upgrade": not has_access,
            "upgrade_tier": service_config['min_tier'] if not has_access else None
        }

    return {
        "user_tier": user_tier,
        "tier_level": tier_level,
        "services": services,
        "rate_limit": get_rate_limit(user_tier),
        "concurrent_searches": get_concurrent_search_limit(user_tier)
    }


@router.get("/tiers/info")
async def get_tiers_info():
    """
    Get information about all subscription tiers.
    """
    return {
        "tiers": [
            {
                "name": "free",
                "level": TIER_LEVELS["free"],
                "rate_limit": RATE_LIMITS["free"],
                "concurrent_searches": CONCURRENT_SEARCH_LIMITS["free"],
                "price": 0,
                "description": "Basic access to core services"
            },
            {
                "name": "starter",
                "level": TIER_LEVELS["starter"],
                "rate_limit": RATE_LIMITS["starter"],
                "concurrent_searches": CONCURRENT_SEARCH_LIMITS["starter"],
                "price": 19,
                "description": "Access to search and BYOK"
            },
            {
                "name": "professional",
                "level": TIER_LEVELS["professional"],
                "rate_limit": RATE_LIMITS["professional"],
                "concurrent_searches": CONCURRENT_SEARCH_LIMITS["professional"],
                "price": 49,
                "description": "All premium features included"
            },
            {
                "name": "enterprise",
                "level": TIER_LEVELS["enterprise"],
                "rate_limit": RATE_LIMITS["enterprise"],
                "concurrent_searches": CONCURRENT_SEARCH_LIMITS["enterprise"],
                "price": 99,
                "description": "Unlimited access with team features"
            }
        ],
        "services": SERVICE_ACCESS
    }


@router.post("/usage/track")
async def track_usage(
    service: str,
    action: str,
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    user_id: Optional[str] = Query(None)
):
    """
    Track service usage for billing and rate limiting.

    This endpoint is called by services to log usage events.
    """
    if not user_email and not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_info = get_user_tier(user_id=user_id, email=user_email)

    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    # Log usage (could send to Lago, Redis, etc.)
    logger.info(f"Usage tracked: {user_info.get('email')} - {service} - {action}")

    return {
        "status": "tracked",
        "service": service,
        "action": action,
        "user": user_info.get('email')
    }


@router.get("/rate-limit/check")
async def check_rate_limit(
    user_email: Optional[str] = Header(None, alias="X-User-Email"),
    user_id: Optional[str] = Query(None)
):
    """
    Check current rate limit status for user.
    """
    if not user_email and not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_info = get_user_tier(user_id=user_id, email=user_email)

    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    user_tier = user_info.get('subscription_tier', 'free')
    limit = get_rate_limit(user_tier)

    # TODO: Implement actual rate limit checking with Redis
    # For now, return the limit info

    return {
        "user_tier": user_tier,
        "rate_limit": limit,
        "rate_limit_per": "minute",
        "current_usage": 0,  # TODO: Get from Redis
        "remaining": limit if limit != -1 else "unlimited",
        "reset_at": None  # TODO: Calculate reset time
    }
