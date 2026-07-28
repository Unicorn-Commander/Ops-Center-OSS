"""
FastAPI Tier Enforcement Middleware

Enforces subscription tier limits on API endpoints by:
1. Reading user's subscription tier from Keycloak user attributes
2. Checking API call limits based on tier
3. Incrementing usage counters
4. Returning appropriate error responses when limits exceeded

Integrates with Keycloak for user data and session management.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from typing import Optional, Dict
import os
from datetime import datetime
import json
import asyncio

# Import Keycloak integration
from keycloak_integration import get_user_tier_info, increment_usage

logger = logging.getLogger(__name__)

class TierEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce subscription tier limits.
    Reads tier from Keycloak user attributes.
    """

    # Paths that don't require tier checking
    EXEMPT_PATHS = [
        "/",
        "/index.html",
        "/auth/",
        "/api/v1/auth/",
        "/api/v1/webhooks/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static/",
        "/favicon.ico",
        "/api/v1/csrf-token",
        "/api/v1/subscription/",  # Allow access to subscription management
        "/api/v1/usage/",  # Allow access to usage info
    ]

    # Tier limits (daily API calls)
    # Note: These are daily limits. Monthly limits divided by 30.
    TIER_LIMITS = {
        "trial": 100,           # 100 calls/day
        "free": 33,             # ~1000 calls/month
        "starter": 33,          # ~1000 calls/month
        "professional": 333,    # ~10000 calls/month
        "enterprise": -1        # Unlimited
    }

    # Feature access by tier
    SERVICE_ACCESS = {
        "search": ["professional", "enterprise"],
        "litellm": ["professional", "enterprise"],
        "billing": ["professional", "enterprise"],
        "team-management": ["enterprise"],
        "audit-logs": ["enterprise"],
    }

    def __init__(self, app):
        super().__init__(app)
        logger.info("TierEnforcementMiddleware initialized with Keycloak backend")

    async def dispatch(self, request: Request, call_next):
        """Main middleware handler"""

        # Skip exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Get user from session
        user_info = self._get_user_from_request(request)

        if not user_info:
            # Not authenticated - let auth middleware handle it
            return await call_next(request)

        user_email = user_info.get("email")
        if not user_email:
            logger.warning("User session exists but no email found")
            return await call_next(request)

        # Get user's subscription tier from Keycloak
        try:
            tier_info = await get_user_tier_info(user_email)
        except Exception as e:
            logger.error(f"Error fetching tier info from Keycloak: {e}")
            # Allow request to proceed on error
            return await call_next(request)

        if not tier_info:
            # Could not fetch tier info - log warning but allow request
            logger.warning(f"Could not fetch tier for {user_email} - allowing request")
            return await call_next(request)

        tier = tier_info.get("subscription_tier", "trial")
        status = tier_info.get("subscription_status", "active")
        api_calls_used = tier_info.get("api_calls_used", 0)

        # Check if subscription is active
        if status not in ["active", "trialing", "trial"]:
            return self._create_error_response(
                status_code=403,
                error="subscription_inactive",
                message="Your subscription is not active. Please update your payment method or contact support.",
                extra={
                    "tier": tier,
                    "status": status,
                    "upgrade_url": "/subscription"
                }
            )

        # Check API call limits
        tier_limit = self.TIER_LIMITS.get(tier, 100)

        if tier_limit > 0 and api_calls_used >= tier_limit:
            return self._create_error_response(
                status_code=429,
                error="rate_limit_exceeded",
                message=f"Daily API limit reached ({tier_limit} calls). Upgrade for higher limits.",
                extra={
                    "tier": tier,
                    "used": api_calls_used,
                    "limit": tier_limit,
                    "upgrade_url": "/subscription"
                }
            )

        # Increment usage counter (fire and forget)
        asyncio.create_task(increment_usage(user_email, api_calls_used))

        # Add tier info to request state for use in endpoints
        request.state.tier = tier
        request.state.tier_status = status
        request.state.tier_usage = api_calls_used
        request.state.tier_limit = tier_limit

        # Process request
        response = await call_next(request)

        # Add usage headers to response
        response.headers["X-Tier"] = tier
        response.headers["X-Tier-Status"] = status
        response.headers["X-API-Calls-Used"] = str(api_calls_used + 1)

        if tier_limit > 0:
            response.headers["X-API-Calls-Limit"] = str(tier_limit)
            response.headers["X-API-Calls-Remaining"] = str(max(0, tier_limit - api_calls_used - 1))
        else:
            response.headers["X-API-Calls-Limit"] = "unlimited"

        return response

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tier checking"""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)

    def _get_user_from_request(self, request: Request) -> Optional[Dict]:
        """Extract user info from request session or headers"""

        # Try to get from session cookie
        session_token = request.cookies.get("session_token")

        if session_token:
            # Get sessions from app state (set by main app)
            sessions = getattr(request.app.state, "sessions", {})
            session_data = sessions.get(session_token)

            if session_data:
                return session_data.get("user")

        # Try to get from X-User-Email header (for API key auth)
        user_email = request.headers.get("X-User-Email")
        if user_email:
            return {"email": user_email}

        return None

    def _create_error_response(self, status_code: int, error: str, message: str, extra: Dict = None):
        """Create JSON error response"""

        content = {
            "error": error,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        if extra:
            content.update(extra)

        return Response(
            content=json.dumps(content),
            status_code=status_code,
            media_type="application/json"
        )


def check_service_access(user_tier: str, service_name: str) -> tuple[bool, str]:
    """
    Check if user tier has access to a service.

    Args:
        user_tier: User's subscription tier
        service_name: Service identifier

    Returns:
        (has_access: bool, message: str)
    """

    if service_name not in TierEnforcementMiddleware.SERVICE_ACCESS:
        # Service not restricted
        return True, "Access granted"

    required_tiers = TierEnforcementMiddleware.SERVICE_ACCESS[service_name]

    if user_tier.lower() in [t.lower() for t in required_tiers]:
        return True, "Access granted"

    return False, f"This service requires {' or '.join(required_tiers)} tier"


def get_tier_limit(user_tier: str) -> int:
    """Get API call limit for user tier"""
    return TierEnforcementMiddleware.TIER_LIMITS.get(user_tier.lower(), 100)
