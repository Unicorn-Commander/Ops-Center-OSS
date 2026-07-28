"""
Structured Logging Configuration

Provides JSON-formatted logging with:
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request/response logging with timing
- Business event logging
- PII redaction
- Contextual logging with metadata
"""

import logging
import json
import sys
import re
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from functools import wraps
import traceback

# Context variables for correlation IDs
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# PII patterns for redaction
PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN_REDACTED]'),
    (re.compile(r'\b\d{16}\b'), '[CARD_REDACTED]'),
    (re.compile(r'password["\s:=]+[^\s,}]+', re.IGNORECASE), 'password: [REDACTED]'),
    (re.compile(r'api[_-]?key["\s:=]+[^\s,}]+', re.IGNORECASE), 'api_key: [REDACTED]'),
    (re.compile(r'token["\s:=]+[^\s,}]+', re.IGNORECASE), 'token: [REDACTED]'),
]


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter with PII redaction and correlation IDs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with metadata."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": self._redact_pii(record.getMessage()),
            "correlation_id": correlation_id_var.get(),
            "user_id": user_id_var.get(),
        }

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self._redact_pii(traceback.format_exception(*record.exc_info))
            }

        # Add file location
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }

        return json.dumps(log_data)

    def _redact_pii(self, text: Any) -> str:
        """Redact PII from log messages."""
        if not isinstance(text, str):
            text = str(text)

        for pattern, replacement in PII_PATTERNS:
            text = pattern.sub(replacement, text)

        return text


class StructuredLogger:
    """Wrapper for standard logger that adds structured logging capabilities."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured fields."""
        extra_fields = {k: v for k, v in kwargs.items() if v is not None}

        # Create log record
        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.extra_fields = extra_fields

        self._logger.handle(record)

    def debug(self, message: str, **kwargs):
        """Log debug message with structured fields."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with structured fields."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured fields."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with structured fields."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with structured fields."""
        self._log(logging.CRITICAL, message, **kwargs)

    def business_event(self, event_type: str, **kwargs):
        """
        Log business event with structured data.

        Business events include:
        - Credit usage/purchase
        - Tier changes
        - Payment events
        - User registration
        - Feature access
        """
        self.info(
            f"Business event: {event_type}",
            event_type=event_type,
            event_category="business",
            **kwargs
        )

    def request_log(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log HTTP request with timing."""
        self.info(
            f"{method} {path} {status_code}",
            request_method=method,
            request_path=path,
            response_status=status_code,
            duration_ms=duration_ms,
            log_type="http_request",
            **kwargs
        )


def setup_logging(log_level: str = "INFO"):
    """
    Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(JSONFormatter())

    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(logging.getLogger(name))


class log_context:
    """
    Context manager for setting correlation ID and user ID in logs.

    Usage:
        with log_context(correlation_id="abc123", user_id="user456"):
            logger.info("This log will include correlation_id and user_id")
    """

    def __init__(self, correlation_id: Optional[str] = None, user_id: Optional[str] = None):
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.correlation_token = None
        self.user_token = None

    def __enter__(self):
        if self.correlation_id:
            self.correlation_token = correlation_id_var.set(self.correlation_id)
        if self.user_id:
            self.user_token = user_id_var.set(self.user_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.correlation_token:
            correlation_id_var.reset(self.correlation_token)
        if self.user_token:
            user_id_var.reset(self.user_token)


def log_function_call(logger: StructuredLogger):
    """
    Decorator to log function calls with arguments and execution time.

    Usage:
        @log_function_call(logger)
        def my_function(arg1, arg2):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(
                    f"Function call completed: {func.__name__}",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="success"
                )
                return result
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Function call failed: {func.__name__}",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="error",
                    error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(
                    f"Function call completed: {func.__name__}",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="success"
                )
                return result
            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Function call failed: {func.__name__}",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    status="error",
                    error=str(e)
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
