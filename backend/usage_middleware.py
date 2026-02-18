"""
Usage Tracking Middleware
==========================

FastAPI middleware to automatically track API usage and enforce subscription limits.

This middleware intercepts all /api/v1/llm/* requests and:
1. Extracts user_id from session
2. Checks usage limits before processing request
3. Returns 429 Too Many Requests if limit exceeded
4. Adds rate limit headers to responses
5. Tracks successful API calls

Headers added to responses:
- X-RateLimit-Limit: Total limit for current period
- X-RateLimit-Remaining: Calls remaining
- X-RateLimit-Reset: Unix timestamp when quota resets

Author: Usage Tracking Team Lead
Date: November 12, 2025
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from datetime import datetime
from typing import Optional
import re

from usage_tracking import usage_tracker

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage and enforce subscription limits.

    Applies to endpoints matching:
    - /api/v1/llm/chat/completions (primary LLM endpoint)
    - /api/v1/llm/image/generations (image generation)
    - /api/v1/llm/* (any other LLM endpoints)
    """

    # Endpoints to track (regex patterns)
    TRACKED_ENDPOINTS = [
        r"^/api/v1/llm/chat/completions",
        r"^/api/v1/llm/image/generations",
        r"^/api/v1/llm/completions",
        r"^/api/v1/llm/embeddings"
    ]

    # Endpoints to exclude from tracking
    EXCLUDED_ENDPOINTS = [
        r"^/api/v1/llm/models",  # Model list endpoint (doesn't consume credits)
        r"^/api/v1/llm/health",  # Health check
        r"^/api/v1/usage/",      # Usage tracking endpoints themselves
        r"^/api/v1/admin/",      # Admin endpoints
        r"^/api/v1/billing/"     # Billing endpoints
    ]

    def __init__(self, app):
        super().__init__(app)
        self.initialized = False

    async def _ensure_initialized(self):
        """Ensure usage tracker is initialized"""
        if not self.initialized:
            await usage_tracker.initialize()
            self.initialized = True

    async def _should_track_endpoint(self, path: str) -> bool:
        """Check if endpoint should be tracked"""
        # Check exclusions first
        for pattern in self.EXCLUDED_ENDPOINTS:
            if re.match(pattern, path):
                return False

        # Check if matches tracked patterns
        for pattern in self.TRACKED_ENDPOINTS:
            if re.match(pattern, path):
                return True

        return False

    async def _get_user_from_session(self, request: Request) -> Optional[dict]:
        """Extract user data from session cookie"""
        try:
            # Add /app to path for imports
            import sys
            import os
            if '/app' not in sys.path:
                sys.path.insert(0, '/app')

            from redis_session import RedisSessionManager

            session_token = request.cookies.get("session_token")
            if not session_token:
                return None

            redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            sessions = RedisSessionManager(host=redis_host, port=redis_port)
            user_data = sessions.get(session_token)

            if not user_data:
                return None

            # Ensure user_id field exists
            if "user_id" not in user_data:
                user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

            return user_data

        except Exception as e:
            logger.error(f"Error extracting user from session: {e}")
            return None

    async def _extract_request_metadata(self, request: Request, response: Optional[Response] = None) -> dict:
        """Extract metadata from request for tracking"""
        metadata = {
            "endpoint": request.url.path,
            "method": request.method,
            "response_status": response.status_code if response else 0,
            "tokens_used": 0,
            "cost_credits": 0.0
        }

        # Try to extract token usage from response body (if available)
        if response and hasattr(response, "body"):
            try:
                import json
                body = json.loads(response.body)
                if "usage" in body:
                    metadata["tokens_used"] = body["usage"].get("total_tokens", 0)
                if "cost" in body:
                    metadata["cost_credits"] = float(body.get("cost", 0.0))
            except:
                pass

        return metadata

    async def dispatch(self, request: Request, call_next):
        """
        Main middleware logic.

        Flow:
        1. Check if endpoint should be tracked
        2. If yes, check user authentication
        3. Check usage limits BEFORE processing request
        4. If limit exceeded, return 429
        5. If within limits, process request
        6. Track usage after successful response
        7. Add rate limit headers to response
        """
        path = request.url.path

        # Check if we should track this endpoint
        should_track = await self._should_track_endpoint(path)

        if not should_track:
            # Not a tracked endpoint, pass through normally
            return await call_next(request)

        # Initialize tracker if needed
        await self._ensure_initialized()

        # Get user from session
        user = await self._get_user_from_session(request)

        if not user:
            # No user session - return 401
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Authentication required to access this endpoint. Please login."
                }
            )

        user_id = user.get("user_id")
        org_id = user.get("org_id")

        # Check usage limits BEFORE processing request
        try:
            # Get current usage stats
            stats = await usage_tracker.get_usage_stats(user_id, period="current")

            # Check if user is at or over limit
            if stats["limit"] > 0 and stats["used"] >= stats["limit"]:
                # Limit exceeded - return 429
                reset_date = stats["reset_date"]
                reset_timestamp = int(datetime.fromisoformat(reset_date).timestamp())

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate Limit Exceeded",
                        "message": f"You have exceeded your {stats['tier']} tier API call limit ({stats['limit']} calls per month). Your quota resets on {reset_date}.",
                        "tier": stats["tier"],
                        "used": stats["used"],
                        "limit": stats["limit"],
                        "remaining": 0,
                        "reset_date": reset_date,
                        "upgrade_url": "/admin/subscription/plan"
                    },
                    headers={
                        "X-RateLimit-Limit": str(stats["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_timestamp),
                        "Retry-After": str(reset_timestamp - int(datetime.utcnow().timestamp()))
                    }
                )

            # Process the request
            response = await call_next(request)

            # Track the API call (only if response was successful)
            if response.status_code < 400:
                try:
                    metadata = await self._extract_request_metadata(request, response)

                    result = await usage_tracker.increment_api_usage(
                        user_id=user_id,
                        org_id=org_id,
                        endpoint=metadata["endpoint"],
                        method=metadata["method"],
                        response_status=metadata["response_status"],
                        tokens_used=metadata["tokens_used"],
                        cost_credits=metadata["cost_credits"]
                    )

                    # Add rate limit headers
                    reset_date = result["reset_date"]
                    reset_timestamp = int(datetime.fromisoformat(reset_date).timestamp())

                    response.headers["X-RateLimit-Limit"] = str(result["limit"]) if result["limit"] > 0 else "unlimited"
                    response.headers["X-RateLimit-Remaining"] = str(result["remaining"]) if result["remaining"] >= 0 else "unlimited"
                    response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
                    response.headers["X-RateLimit-Tier"] = result["tier"]

                except Exception as e:
                    logger.error(f"Error tracking API usage: {e}", exc_info=True)
                    # Don't fail the request if tracking fails

            return response

        except Exception as e:
            logger.error(f"Error in usage tracking middleware: {e}", exc_info=True)
            # On error, allow request to proceed (fail open)
            return await call_next(request)


# Backward compatibility: export as function for older code
def create_usage_tracking_middleware():
    """Factory function to create middleware instance"""
    return UsageTrackingMiddleware
