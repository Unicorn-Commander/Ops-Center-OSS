"""
Ops-Center Observability Module

Comprehensive observability system providing:
- Structured logging with correlation IDs
- Prometheus metrics for monitoring
- Health checks (liveness, readiness, detailed)
- Distributed tracing with OpenTelemetry
- Alerting rule definitions

Usage:
    from observability import setup_observability, get_logger, metrics

    # Setup during app initialization
    setup_observability(app)

    # Use structured logger
    logger = get_logger(__name__)
    logger.info("User action", user_id="123", action="login")

    # Record metrics
    metrics.http_requests.inc()
    metrics.http_request_duration.observe(0.5)
"""

from .logging_config import setup_logging, get_logger, log_context
from .metrics import metrics, setup_metrics
from .health import router as health_router, HealthChecker
from .tracing import setup_tracing, trace_request
from .alerting import AlertingRules

__all__ = [
    "setup_logging",
    "get_logger",
    "log_context",
    "metrics",
    "setup_metrics",
    "health_router",
    "HealthChecker",
    "setup_tracing",
    "trace_request",
    "AlertingRules",
    "setup_observability",
]

def setup_observability(app):
    """
    Setup all observability components for the FastAPI application.

    Args:
        app: FastAPI application instance

    Returns:
        dict: Configuration details of setup components
    """
    # 1. Setup structured logging
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Initializing Ops-Center observability system")

    # 2. Setup Prometheus metrics
    setup_metrics(app)
    logger.info("Prometheus metrics endpoint configured at /metrics")

    # 3. Add health check routes
    app.include_router(health_router, prefix="/health", tags=["health"])
    logger.info("Health check endpoints configured at /health/*")

    # 4. Setup distributed tracing
    setup_tracing(app)
    logger.info("OpenTelemetry distributed tracing configured")

    logger.info("Observability system initialized successfully")

    return {
        "logging": "configured",
        "metrics": "/metrics",
        "health": {
            "liveness": "/health",
            "readiness": "/health/ready",
            "detailed": "/health/detailed"
        },
        "tracing": "enabled"
    }
