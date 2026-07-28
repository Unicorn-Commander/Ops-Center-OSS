"""
Input Validation Middleware
Validates and sanitizes input to prevent XSS and SQL injection attacks
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize input"""

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>',  # XSS
        r'javascript:',     # XSS
        r'on\w+\s*=',       # Event handlers
        r'union\s+select',  # SQL injection
        r';\s*drop\s+',     # SQL injection
        r'--\s*$',          # SQL comment
    ]

    async def dispatch(self, request: Request, call_next):
        # Check query parameters
        for key, value in request.query_params.items():
            if self._is_dangerous(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Invalid input in parameter: {key}"}
                )

        return await call_next(request)

    def _is_dangerous(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        value_lower = value.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
