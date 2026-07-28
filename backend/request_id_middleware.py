"""
Request ID Tracking Middleware
===============================

Adds unique request IDs to all HTTP requests for audit trail and debugging.

Each request gets:
- Unique UUID in X-Request-ID header
- Request ID logged with every log message
- Request ID included in error responses

Author: Ops-Center Security Team
Created: 2025-11-12
"""

import uuid
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds unique request IDs to all HTTP requests.

    Features:
    - Generates UUID for each request
    - Adds X-Request-ID to response headers
    - Logs request ID with request method and path
    - Tracks request duration
    - Available in request.state for use in endpoints
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add request ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response with X-Request-ID header
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Log request start
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {client_ip} - Request started"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"completed with status {response.status_code} "
                f"in {duration_ms:.2f}ms"
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"failed after {duration_ms:.2f}ms: {str(e)}"
            )

            # Re-raise exception to be handled by FastAPI
            raise


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.

    Usage in endpoints:
        from request_id_middleware import get_request_id

        @router.get("/endpoint")
        async def my_endpoint(request: Request):
            request_id = get_request_id(request)
            logger.info(f"[{request_id}] Processing endpoint")

    Args:
        request: FastAPI request object

    Returns:
        Request ID string (UUID)
    """
    return getattr(request.state, "request_id", "unknown")
