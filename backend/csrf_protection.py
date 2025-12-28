"""
CSRF Protection Middleware for UC-1 Pro Ops Center
Implements double-submit cookie pattern with session integration
"""

import secrets
import hashlib
import time
from typing import Optional, Callable, Set
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """CSRF token generation and validation"""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_length: int = 32,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_httponly: bool = False,
        cookie_samesite: str = "lax",
        cookie_secure: bool = False,
        max_age: int = 3600 * 24  # 24 hours
    ):
        """
        Initialize CSRF protection

        Args:
            secret_key: Secret key for token generation (optional, generates random if not provided)
            token_length: Length of CSRF tokens in bytes
            cookie_name: Name of the CSRF cookie
            header_name: Name of the CSRF header
            cookie_httponly: Whether to set HttpOnly flag on cookie
            cookie_samesite: SameSite attribute for cookie (lax, strict, or none)
            cookie_secure: Whether to set Secure flag on cookie
            max_age: Cookie max age in seconds
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.token_length = token_length
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.cookie_secure = cookie_secure
        self.max_age = max_age

    def generate_token(self) -> str:
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(self.token_length)

    def generate_token_hash(self, token: str) -> str:
        """Generate a hash of the token for server-side validation"""
        combined = f"{token}{self.secret_key}".encode()
        return hashlib.sha256(combined).hexdigest()

    def validate_token(self, token: str, expected_token: str) -> bool:
        """
        Validate CSRF token using constant-time comparison

        Args:
            token: Token from request header/form
            expected_token: Expected token from cookie/session

        Returns:
            True if tokens match, False otherwise
        """
        if not token or not expected_token:
            return False
        return secrets.compare_digest(token, expected_token)


class CSRFMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for CSRF protection"""

    # Methods that require CSRF protection
    PROTECTED_METHODS: Set[str] = {"POST", "PUT", "DELETE", "PATCH"}

    # Safe methods that don't require CSRF protection
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def __init__(
        self,
        app,
        csrf_protect: CSRFProtection,
        exempt_urls: Optional[Set[str]] = None,
        enabled: bool = True,
        sessions_store: Optional[dict] = None
    ):
        """
        Initialize CSRF middleware

        Args:
            app: FastAPI application
            csrf_protect: CSRFProtection instance
            exempt_urls: Set of URL paths to exempt from CSRF validation
            enabled: Whether CSRF protection is enabled
            sessions_store: Reference to the sessions dictionary for token storage
        """
        super().__init__(app)
        self.csrf_protect = csrf_protect
        self.exempt_urls = exempt_urls or {
            "/auth/callback",
            "/auth/login",
            "/auth/logout",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/byok/",  # BYOK API endpoints (Bring Your Own Key)
            "/api/v1/llm/",  # LLM API endpoints (used by Brigade, Open-WebUI, etc.)
            "/api/v1/email-provider/",  # Email provider API (used for testing providers)
            "/api/v1/platform/",  # Platform settings API (credential management)
            "/api/v1/monitoring/grafana/",  # Grafana integration API (monitoring)
            "/api/v1/admin/users/",  # User management and API key endpoints
            "/api/v1/org/",  # Organization management API
            "/api/v1/org"    # Organization management API (without trailing slash)
        }
        self.enabled = enabled
        self.sessions_store = sessions_store or {}

    def is_exempt(self, path: str) -> bool:
        """Check if a URL path is exempt from CSRF protection"""
        logger.info(f"CSRF exemption check for path: {path}")
        logger.info(f"Exempt URLs: {self.exempt_urls}")

        # Check exact matches
        if path in self.exempt_urls:
            logger.info(f"Path {path} matched exact exempt URL")
            return True

        # Check prefix matches for OAuth callbacks
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                logger.info(f"Path {path} matched exempt URL prefix: {exempt_url}")
                return True

        logger.warning(f"Path {path} NOT EXEMPT. Exempt URLs: {self.exempt_urls}")
        return False

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract CSRF token from request
        Checks in order: header, form data, query params
        """
        # Check header first (preferred method)
        token = request.headers.get(self.csrf_protect.header_name)
        if token:
            return token

        # For form submissions, check form data
        # Note: This requires the request body to be already read
        # In production, you might want to use a different approach
        return None

    def get_session_token(self, request: Request) -> Optional[str]:
        """Get CSRF token from session"""
        session_token = request.cookies.get("session_token")
        if not session_token or session_token not in self.sessions_store:
            return None

        session = self.sessions_store[session_token]
        return session.get("csrf_token")

    def set_csrf_cookie(self, response: Response, token: str):
        """Set CSRF token cookie on response"""
        response.set_cookie(
            key=self.csrf_protect.cookie_name,
            value=token,
            max_age=self.csrf_protect.max_age,
            httponly=self.csrf_protect.cookie_httponly,
            samesite=self.csrf_protect.cookie_samesite,
            secure=self.csrf_protect.cookie_secure,
            path="/"
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and validate CSRF token if required"""

        # Skip if CSRF protection is disabled
        if not self.enabled:
            return await call_next(request)

        # Skip for safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)

            # Generate and set CSRF token for authenticated users
            session_token = request.cookies.get("session_token")
            if session_token and session_token in self.sessions_store:
                session = self.sessions_store[session_token]

                # Generate new token if not exists
                if "csrf_token" not in session:
                    csrf_token = self.csrf_protect.generate_token()
                    session["csrf_token"] = csrf_token
                    self.sessions_store[session_token] = session  # Save back to Redis
                    logger.info(f"Generated new CSRF token for session: {session_token[:8]}...")
                else:
                    csrf_token = session["csrf_token"]

                # Set CSRF cookie on response
                self.set_csrf_cookie(response, csrf_token)

            return response

        # Check if URL is exempt
        if self.is_exempt(request.url.path):
            logger.info(f"CSRF check skipped for exempt URL: {request.url.path}")
            return await call_next(request)

        # For protected methods, validate CSRF token
        if request.method in self.PROTECTED_METHODS:
            # Get token from request
            request_token = self.get_token_from_request(request)

            # Also check cookie as fallback (double-submit pattern)
            cookie_token = request.cookies.get(self.csrf_protect.cookie_name)

            # Get expected token from session
            session_token = self.get_session_token(request)

            # Validate token
            valid = False

            # Primary validation: header/form token matches session token
            if request_token and session_token:
                valid = self.csrf_protect.validate_token(request_token, session_token)
                if valid:
                    logger.debug(f"CSRF validation passed (header) for {request.url.path}")

            # Fallback validation: cookie token matches session token (double-submit)
            if not valid and cookie_token and session_token:
                valid = self.csrf_protect.validate_token(cookie_token, session_token)
                if valid:
                    logger.debug(f"CSRF validation passed (cookie) for {request.url.path}")

            if not valid:
                logger.warning(
                    f"CSRF validation failed for {request.method} {request.url.path} - "
                    f"Request token: {'present' if request_token else 'missing'}, "
                    f"Cookie token: {'present' if cookie_token else 'missing'}, "
                    f"Session token: {'present' if session_token else 'missing'}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed. Invalid or missing CSRF token."
                )

        # Process request
        response = await call_next(request)

        # Refresh CSRF token in cookie on successful requests
        session_token = request.cookies.get("session_token")
        if session_token and session_token in self.sessions_store:
            session = self.sessions_store[session_token]
            if "csrf_token" in session:
                self.set_csrf_cookie(response, session["csrf_token"])

        return response


def get_csrf_token(request: Request, sessions_store: dict) -> Optional[str]:
    """
    Helper function to get CSRF token for current session
    Can be used in route handlers to provide CSRF token to frontend

    Args:
        request: FastAPI request object
        sessions_store: Reference to sessions dictionary

    Returns:
        CSRF token if session exists, None otherwise
    """
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions_store:
        return None

    session = sessions_store[session_token]
    return session.get("csrf_token")


def create_csrf_protection(
    enabled: bool = True,
    secret_key: Optional[str] = None,
    exempt_urls: Optional[Set[str]] = None,
    sessions_store: Optional[dict] = None,
    cookie_secure: bool = False
) -> tuple[CSRFProtection, CSRFMiddleware]:
    """
    Factory function to create CSRF protection components

    Args:
        enabled: Whether CSRF protection is enabled
        secret_key: Secret key for token generation
        exempt_urls: Set of URLs to exempt from CSRF protection
        sessions_store: Reference to sessions dictionary
        cookie_secure: Whether to set Secure flag on cookies (True for HTTPS)

    Returns:
        Tuple of (CSRFProtection, CSRFMiddleware)
    """
    csrf_protect = CSRFProtection(
        secret_key=secret_key,
        cookie_secure=cookie_secure,
        cookie_samesite="lax",
        cookie_httponly=False  # Frontend needs to read this
    )

    csrf_middleware = lambda app: CSRFMiddleware(
        app=app,
        csrf_protect=csrf_protect,
        exempt_urls=exempt_urls,
        enabled=enabled,
        sessions_store=sessions_store
    )

    return csrf_protect, csrf_middleware
