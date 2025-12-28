"""
Rate Limiting Module for UC-1 Pro Ops-Center Backend

This module provides Redis-based rate limiting with support for:
- Multiple rate limit strategies (sliding window, token bucket)
- Different limits per endpoint category
- IP + User ID based rate limiting
- Admin bypass functionality
- Graceful Redis failure handling
- Proper HTTP 429 responses with Retry-After headers

Author: UC-1 Pro Team
License: MIT
"""

import os
import time
import logging
from typing import Optional, Callable, Dict, Any, Tuple
from functools import wraps
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

# Redis imports with fallback
try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    AsyncRedis = None

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for rate limiting"""

    def __init__(self):
        # Enable/disable rate limiting
        self.enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"

        # Redis connection
        self.redis_url = os.environ.get("REDIS_URL", "redis://unicorn-lago-redis:6379/0")

        # Rate limit configurations (format: "count/period")
        self.limits = {
            "auth": self._parse_limit(os.environ.get("RATE_LIMIT_AUTH", "5/minute")),
            "admin": self._parse_limit(os.environ.get("RATE_LIMIT_ADMIN", "100/minute")),
            "read": self._parse_limit(os.environ.get("RATE_LIMIT_READ", "200/minute")),
            "write": self._parse_limit(os.environ.get("RATE_LIMIT_WRITE", "50/minute")),
            "health": None,  # No limit for health checks
        }

        # Admin bypass
        self.admin_bypass = os.environ.get("RATE_LIMIT_ADMIN_BYPASS", "true").lower() == "true"

        # Graceful degradation
        self.fail_open = os.environ.get("RATE_LIMIT_FAIL_OPEN", "true").lower() == "true"

        # Key prefix
        self.key_prefix = os.environ.get("RATE_LIMIT_KEY_PREFIX", "ratelimit:")

        # Strategy: sliding_window or token_bucket
        self.strategy = os.environ.get("RATE_LIMIT_STRATEGY", "sliding_window")

    @staticmethod
    def _parse_limit(limit_str: str) -> Tuple[int, int]:
        """
        Parse rate limit string like "5/minute" into (count, seconds)

        Args:
            limit_str: Rate limit string (e.g., "5/minute", "100/hour")

        Returns:
            Tuple of (count, seconds)
        """
        try:
            count, period = limit_str.split("/")
            count = int(count.strip())
            period = period.strip().lower()

            period_map = {
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400,
            }

            seconds = period_map.get(period, 60)
            return (count, seconds)
        except Exception as e:
            logger.error(f"Error parsing rate limit '{limit_str}': {e}")
            return (100, 60)  # Default: 100/minute


class RateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.redis_client: Optional[AsyncRedis] = None
        self._initialized = False

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - rate limiting will be disabled")
            self.config.enabled = False

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.config.enabled or self._initialized:
            return

        try:
            self.redis_client = AsyncRedis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Rate limiter initialized with Redis backend")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for rate limiting: {e}")
            if not self.config.fail_open:
                raise
            logger.warning("Rate limiting will fail open (allow requests)")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False

    def _get_key(self, identifier: str, category: str) -> str:
        """Generate Redis key for rate limit"""
        return f"{self.config.key_prefix}{category}:{identifier}"

    async def _check_sliding_window(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window algorithm

        Args:
            key: Redis key
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, current_count, retry_after_seconds)
        """
        if not self.redis_client:
            return (True, 0, 0)

        try:
            now = time.time()
            window_start = now - window_seconds

            # Use Redis transaction
            pipe = self.redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Add current request with score = timestamp
            pipe.zadd(key, {str(now): now})

            # Set expiry
            pipe.expire(key, window_seconds + 1)

            results = await pipe.execute()
            current_count = results[1]

            # Check if limit exceeded
            if current_count >= max_requests:
                # Calculate retry after
                oldest_scores = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_scores:
                    oldest_timestamp = oldest_scores[0][1]
                    retry_after = int(window_start + window_seconds - oldest_timestamp + 1)
                else:
                    retry_after = window_seconds

                return (False, current_count, max(retry_after, 1))

            return (True, current_count + 1, 0)

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            if self.config.fail_open:
                return (True, 0, 0)
            raise

    async def _check_token_bucket(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using token bucket algorithm

        Args:
            key: Redis key
            max_requests: Maximum requests allowed (bucket capacity)
            window_seconds: Refill period in seconds

        Returns:
            Tuple of (allowed, current_tokens, retry_after_seconds)
        """
        if not self.redis_client:
            return (True, 0, 0)

        try:
            now = time.time()

            # Get current bucket state
            bucket_data = await self.redis_client.hgetall(key)

            if bucket_data:
                tokens = float(bucket_data.get("tokens", max_requests))
                last_refill = float(bucket_data.get("last_refill", now))
            else:
                tokens = max_requests
                last_refill = now

            # Calculate refill
            time_passed = now - last_refill
            refill_rate = max_requests / window_seconds
            tokens_to_add = time_passed * refill_rate
            tokens = min(max_requests, tokens + tokens_to_add)

            # Try to consume a token
            if tokens >= 1:
                tokens -= 1

                # Update bucket
                pipe = self.redis_client.pipeline()
                pipe.hset(key, mapping={"tokens": tokens, "last_refill": now})
                pipe.expire(key, window_seconds * 2)
                await pipe.execute()

                return (True, int(tokens), 0)
            else:
                # Calculate retry after
                tokens_needed = 1 - tokens
                retry_after = int(tokens_needed / refill_rate) + 1
                return (False, 0, retry_after)

        except Exception as e:
            logger.error(f"Error checking token bucket: {e}")
            if self.config.fail_open:
                return (True, 0, 0)
            raise

    async def check_rate_limit(
        self,
        identifier: str,
        category: str,
        is_admin: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited

        Args:
            identifier: Unique identifier (IP + user ID)
            category: Rate limit category (auth, admin, read, write, health)
            is_admin: Whether user is admin

        Returns:
            Tuple of (allowed, metadata dict with headers info)
        """
        # Check if rate limiting is enabled
        if not self.config.enabled:
            return (True, {})

        # Admin bypass
        if is_admin and self.config.admin_bypass:
            return (True, {"bypassed": True})

        # Get limit for category
        limit_config = self.config.limits.get(category)
        if limit_config is None:
            # No limit for this category
            return (True, {})

        max_requests, window_seconds = limit_config
        key = self._get_key(identifier, category)

        # Check rate limit based on strategy
        if self.config.strategy == "token_bucket":
            allowed, current, retry_after = await self._check_token_bucket(
                key, max_requests, window_seconds
            )
        else:
            allowed, current, retry_after = await self._check_sliding_window(
                key, max_requests, window_seconds
            )

        metadata = {
            "limit": max_requests,
            "window": window_seconds,
            "current": current,
            "remaining": max(0, max_requests - current),
            "reset": int(time.time() + window_seconds),
        }

        if not allowed:
            metadata["retry_after"] = retry_after

        return (allowed, metadata)

    def get_identifier(self, request: Request, user_id: Optional[str] = None) -> str:
        """
        Get unique identifier for rate limiting

        Args:
            request: FastAPI request
            user_id: Optional user ID

        Returns:
            Unique identifier string
        """
        # Get client IP
        ip = request.client.host if request.client else "unknown"

        # Check for proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()

        # Combine IP and user ID
        if user_id:
            return f"{ip}:{user_id}"
        return ip


# Global rate limiter instance
rate_limiter_config = RateLimitConfig()
rate_limiter = RateLimiter(rate_limiter_config)


def rate_limit(category: str = "read"):
    """
    Decorator for rate limiting FastAPI endpoints

    Args:
        category: Rate limit category (auth, admin, read, write, health)

    Usage:
        @app.get("/api/v1/data")
        @rate_limit("read")
        async def get_data(request: Request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get("request")

            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)

            # Get user info (you may need to adjust this based on your auth)
            user_id = None
            is_admin = False

            # Try to get from Authorization header or session
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Extract user info from token (implement based on your auth system)
                pass

            # Get identifier
            identifier = rate_limiter.get_identifier(request, user_id)

            # Check rate limit
            allowed, metadata = await rate_limiter.check_rate_limit(
                identifier, category, is_admin
            )

            if not allowed:
                # Return 429 with headers
                retry_after = metadata.get("retry_after", 60)

                headers = {
                    "X-RateLimit-Limit": str(metadata.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(metadata.get("reset", 0)),
                    "Retry-After": str(retry_after),
                }

                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                    },
                    headers=headers,
                )

            # Add rate limit headers to response
            response = await func(*args, **kwargs)

            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(metadata.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(metadata.get("reset", 0))

            return response

        return wrapper
    return decorator


class RateLimitMiddleware:
    """
    Middleware for global rate limiting

    This can be used as alternative to decorators for applying
    rate limits to all endpoints automatically.
    """

    def __init__(self, app, limiter: RateLimiter):
        self.app = app
        self.limiter = limiter

        # Endpoint category mapping (regex patterns)
        self.category_patterns = [
            (r"^/api/v1/auth/", "auth"),
            (r"^/api/v1/(users|sso|api-keys)/", "admin"),
            (r"^/api/v1/(services|models|logs|storage|backup|extensions)/[^/]+", "write"),
            (r"^/api/v1/", "read"),
            (r"^/health", "health"),
            (r"^/api/v1/system/status", "health"),
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Get path
        path = scope.get("path", "")

        # Determine category
        category = "read"  # default
        for pattern, cat in self.category_patterns:
            if re.match(pattern, path):
                category = cat
                break

        # Skip rate limiting for health checks
        if category == "health":
            return await self.app(scope, receive, send)

        # Create request object (simplified)
        from starlette.requests import Request as StarletteRequest
        request = StarletteRequest(scope, receive)

        # Get identifier
        identifier = self.limiter.get_identifier(request)

        # Check rate limit
        allowed, metadata = await self.limiter.check_rate_limit(identifier, category)

        if not allowed:
            # Return 429 response
            retry_after = metadata.get("retry_after", 60)

            response = JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(metadata.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(metadata.get("reset", 0)),
                    "Retry-After": str(retry_after),
                },
            )

            await response(scope, receive, send)
            return

        # Continue with request
        await self.app(scope, receive, send)


# Utility functions for manual rate limit checks
async def check_rate_limit_manual(
    request: Request,
    category: str = "read",
    user_id: Optional[str] = None,
    is_admin: bool = False
) -> None:
    """
    Manually check rate limit and raise HTTPException if exceeded

    Args:
        request: FastAPI request
        category: Rate limit category
        user_id: Optional user ID
        is_admin: Whether user is admin

    Raises:
        HTTPException: If rate limit exceeded
    """
    identifier = rate_limiter.get_identifier(request, user_id)
    allowed, metadata = await rate_limiter.check_rate_limit(identifier, category, is_admin)

    if not allowed:
        retry_after = metadata.get("retry_after", 60)

        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "retry_after": retry_after,
            },
            headers={
                "X-RateLimit-Limit": str(metadata.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(metadata.get("reset", 0)),
                "Retry-After": str(retry_after),
            },
        )
