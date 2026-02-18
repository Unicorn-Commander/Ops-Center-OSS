"""
Security Middleware for UC-Cloud Ops-Center

FastAPI middleware to add security headers and protections:
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

Security Epic: 1.7 High-Priority Issue #5 - Security Headers
Author: Security Team Lead
Date: October 22, 2025
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses

    Headers Added:
    - Strict-Transport-Security: Force HTTPS for 1 year
    - Content-Security-Policy: Restrict content sources
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Referrer-Policy: Control referer information
    - Permissions-Policy: Control browser features

    Usage:
        from fastapi import FastAPI
        from security_middleware import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 year
        include_subdomains: bool = True,
        enable_csp: bool = True,
        csp_policy: str = None
    ):
        """
        Initialize security headers middleware

        Args:
            app: ASGI application
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            include_subdomains: Include subdomains in HSTS
            enable_csp: Enable Content-Security-Policy header
            csp_policy: Custom CSP policy (default: strict policy)
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.include_subdomains = include_subdomains
        self.enable_csp = enable_csp

        # Default CSP policy (strict, but allows same-origin)
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # TODO: Remove unsafe-inline/eval
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        logger.info("SecurityHeadersMiddleware initialized")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Add security headers to response

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with security headers
        """
        # Process request
        response = await call_next(request)

        # Add security headers
        headers = self._get_security_headers(request)

        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response

    def _get_security_headers(self, request: Request) -> dict:
        """
        Get security headers based on configuration

        Args:
            request: HTTP request (to check if HTTPS)

        Returns:
            Dictionary of security headers
        """
        headers = {}

        # 1. Strict-Transport-Security (HSTS)
        # Force HTTPS for future requests (prevents SSL stripping attacks)
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.include_subdomains:
                hsts_value += "; includeSubDomains"
            hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        # 2. Content-Security-Policy (CSP)
        # Restrict content sources to prevent XSS attacks
        if self.enable_csp:
            headers["Content-Security-Policy"] = self.csp_policy

        # 3. X-Frame-Options
        # Prevent clickjacking attacks (prevents page from being framed)
        headers["X-Frame-Options"] = "DENY"

        # 4. X-Content-Type-Options
        # Prevent MIME sniffing (forces browser to respect declared content type)
        headers["X-Content-Type-Options"] = "nosniff"

        # 5. X-XSS-Protection
        # Enable XSS filter in legacy browsers (modern browsers use CSP)
        headers["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer-Policy
        # Control referer information sent to other sites
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy (formerly Feature-Policy)
        # Control browser features (microphone, camera, geolocation, etc.)
        headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # 8. X-Permitted-Cross-Domain-Policies
        # Restrict Adobe Flash and PDF cross-domain policies
        headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. Cache-Control (for sensitive endpoints)
        if request.url.path.startswith("/api/v1/admin") or "auth" in request.url.path:
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            headers["Pragma"] = "no-cache"

        return headers


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all HTTP requests with timing and status codes

    Logs:
    - Request method and path
    - Request timing
    - Response status code
    - Client IP address
    - User agent

    Excludes:
    - Health check endpoints
    - Static file requests
    """

    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        """
        Initialize request logging middleware

        Args:
            app: ASGI application
            exclude_paths: List of paths to exclude from logging
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/favicon.ico", "/static"]
        logger.info("RequestLoggingMiddleware initialized")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Log request and response

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log request
            logger.info(
                f"{request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Time: {process_time:.3f}s "
                f"- Client: {client_ip} "
                f"- UA: {user_agent[:50]}"
            )

            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} "
                f"- Error: {str(e)} "
                f"- Time: {process_time:.3f}s "
                f"- Client: {client_ip}"
            )
            raise


# ============================================================================
# CORS Security Middleware (Restrictive)
# ============================================================================

class SecureCORSMiddleware(BaseHTTPMiddleware):
    """
    Secure CORS middleware with whitelist-based origin validation

    Security Features:
    - Whitelist-only origins (no wildcards)
    - Restricted methods and headers
    - Credentials support with origin validation
    - Preflight caching

    Usage:
        app.add_middleware(
            SecureCORSMiddleware,
            allowed_origins=["https://unicorncommander.ai"],
            allow_credentials=True
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: list = None,
        allowed_methods: list = None,
        allowed_headers: list = None,
        allow_credentials: bool = True,
        max_age: int = 600  # 10 minutes preflight cache
    ):
        """
        Initialize CORS middleware

        Args:
            app: ASGI application
            allowed_origins: Whitelist of allowed origins (no wildcards)
            allowed_methods: Allowed HTTP methods
            allowed_headers: Allowed request headers
            allow_credentials: Allow credentials (cookies, auth headers)
            max_age: Preflight cache duration in seconds
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["https://unicorncommander.ai"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["Content-Type", "Authorization"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

        logger.info(f"SecureCORSMiddleware initialized with {len(self.allowed_origins)} allowed origins")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Handle CORS requests

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response with CORS headers
        """
        origin = request.headers.get("origin")

        # Preflight request (OPTIONS)
        if request.method == "OPTIONS":
            return self._handle_preflight(origin)

        # Regular request
        response = await call_next(request)

        # Add CORS headers if origin is allowed
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

    def _handle_preflight(self, origin: str) -> Response:
        """
        Handle CORS preflight request

        Args:
            origin: Request origin

        Returns:
            Preflight response with CORS headers
        """
        headers = {}

        # Only allow whitelisted origins (no wildcards for security)
        if origin in self.allowed_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            headers["Access-Control-Max-Age"] = str(self.max_age)

            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"

            return Response(status_code=200, headers=headers)

        # Origin not allowed
        return Response(status_code=403, content="Origin not allowed")


# ============================================================================
# Rate Limiting Middleware (Basic - See rate_limiter.py for Redis version)
# ============================================================================

class BasicRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic in-memory rate limiting middleware

    NOTE: This is a simple in-memory implementation.
    For production, use Redis-backed rate limiting (see rate_limiter.py)

    Limits:
    - 100 requests per minute per IP
    - Returns 429 Too Many Requests if exceeded
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 100
    ):
        """
        Initialize rate limiting middleware

        Args:
            app: ASGI application
            requests_per_minute: Max requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # IP -> [(timestamp, count)]
        logger.info(f"BasicRateLimitMiddleware initialized ({requests_per_minute} req/min)")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Check rate limit before processing request

        Args:
            request: HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response (or 429 if rate limit exceeded)
        """
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Check rate limit
        current_time = time.time()
        minute_ago = current_time - 60

        # Get request history for this IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Remove old requests (older than 1 minute)
        self.request_counts[client_ip] = [
            (timestamp, count)
            for timestamp, count in self.request_counts[client_ip]
            if timestamp > minute_ago
        ]

        # Count requests in last minute
        recent_count = sum(count for _, count in self.request_counts[client_ip])

        if recent_count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}: {recent_count}/{self.requests_per_minute}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add this request
        self.request_counts[client_ip].append((current_time, 1))

        # Process request
        return await call_next(request)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Security Middleware Module - Test Mode")
    print("=" * 70)

    print("\n1. Available Middleware:")
    print("   - SecurityHeadersMiddleware: Adds security headers (HSTS, CSP, etc.)")
    print("   - RequestLoggingMiddleware: Logs all HTTP requests")
    print("   - SecureCORSMiddleware: Whitelist-based CORS")
    print("   - BasicRateLimitMiddleware: In-memory rate limiting")

    print("\n2. Integration with FastAPI:")
    print("""
    from fastapi import FastAPI
    from security_middleware import (
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
        SecureCORSMiddleware,
        BasicRateLimitMiddleware
    )

    app = FastAPI()

    # Add middleware (order matters - last added = first executed)
    app.add_middleware(SecurityHeadersMiddleware, hsts_max_age=31536000)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        SecureCORSMiddleware,
        allowed_origins=["https://unicorncommander.ai"]
    )
    app.add_middleware(BasicRateLimitMiddleware, requests_per_minute=100)
    """)

    print("\n3. Security Headers Added:")
    print("   ✅ Strict-Transport-Security: max-age=31536000; includeSubDomains; preload")
    print("   ✅ Content-Security-Policy: default-src 'self'; ...")
    print("   ✅ X-Frame-Options: DENY")
    print("   ✅ X-Content-Type-Options: nosniff")
    print("   ✅ X-XSS-Protection: 1; mode=block")
    print("   ✅ Referrer-Policy: strict-origin-when-cross-origin")
    print("   ✅ Permissions-Policy: geolocation=(), microphone=(), ...")

    print("\n✅ Security middleware loaded successfully")
