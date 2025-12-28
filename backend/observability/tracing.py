"""
Distributed Tracing with OpenTelemetry

Provides end-to-end request tracing across:
- HTTP endpoints
- Database queries
- External service calls
- Business operations

Integrates with Jaeger, Zipkin, or OTLP-compatible backends.
"""

from typing import Optional, Callable, Any
from functools import wraps
import time
import os

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

from .logging_config import get_logger

logger = get_logger(__name__)


class TracingManager:
    """Manager for distributed tracing configuration."""

    def __init__(self):
        self.tracer: Optional[Any] = None
        self.enabled = False

    def setup(self, app, service_name: str = "ops-center"):
        """
        Setup distributed tracing for the application.

        Args:
            app: FastAPI application instance
            service_name: Service name for tracing
        """
        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry not available - tracing disabled",
                reason="missing_dependencies"
            )
            return

        try:
            # Create resource
            resource = Resource(attributes={
                SERVICE_NAME: service_name,
                "service.version": os.getenv("OPS_CENTER_VERSION", "2.3.0"),
                "deployment.environment": os.getenv("ENVIRONMENT", "production")
            })

            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)

            # Configure exporter based on environment
            exporter = self._get_exporter()
            if exporter:
                span_processor = BatchSpanProcessor(exporter)
                tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(app)

            # Instrument HTTP clients
            HTTPXClientInstrumentor().instrument()

            # Instrument database
            try:
                AsyncPGInstrumentor().instrument()
            except Exception as e:
                logger.warning("Failed to instrument AsyncPG", error=str(e))

            # Instrument Redis
            try:
                RedisInstrumentor().instrument()
            except Exception as e:
                logger.warning("Failed to instrument Redis", error=str(e))

            self.enabled = True
            logger.info(
                "Distributed tracing configured",
                service_name=service_name,
                exporter=type(exporter).__name__ if exporter else "none"
            )

        except Exception as e:
            logger.error(
                "Failed to setup distributed tracing",
                error=str(e)
            )

    def _get_exporter(self):
        """
        Get trace exporter based on configuration.

        Supports:
        - OTLP (OpenTelemetry Protocol)
        - Jaeger
        - Console (for development)

        Returns:
            Span exporter instance
        """
        exporter_type = os.getenv("OTEL_EXPORTER_TYPE", "console").lower()

        if exporter_type == "otlp":
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            return OTLPSpanExporter(endpoint=endpoint)

        elif exporter_type == "jaeger":
            agent_host = os.getenv("JAEGER_AGENT_HOST", "localhost")
            agent_port = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
            return JaegerExporter(
                agent_host_name=agent_host,
                agent_port=agent_port
            )

        elif exporter_type == "console":
            # Console exporter for development
            return ConsoleSpanExporter()

        else:
            logger.warning(
                f"Unknown exporter type: {exporter_type}, using console",
                exporter_type=exporter_type
            )
            return ConsoleSpanExporter()


# Global tracing manager
tracing_manager = TracingManager()


def setup_tracing(app, service_name: str = "ops-center"):
    """
    Setup distributed tracing for the application.

    Args:
        app: FastAPI application instance
        service_name: Service name for tracing
    """
    tracing_manager.setup(app, service_name)


def trace_request(operation_name: str):
    """
    Decorator to trace a request or operation.

    Usage:
        @trace_request("process_payment")
        async def process_payment(user_id: str, amount: float):
            pass

    Args:
        operation_name: Name of the operation being traced
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not tracing_manager.enabled or not tracing_manager.tracer:
                return await func(*args, **kwargs)

            with tracing_manager.tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                span.set_attribute("operation.name", operation_name)
                span.set_attribute("function.name", func.__name__)

                # Add arguments as attributes (be careful with PII)
                for i, arg in enumerate(args):
                    if isinstance(arg, (str, int, float, bool)):
                        span.set_attribute(f"arg.{i}", str(arg))

                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"kwarg.{key}", str(value))

                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    span.set_attribute("duration_ms", duration_ms)
                    span.set_attribute("status", "success")

                    return result

                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not tracing_manager.enabled or not tracing_manager.tracer:
                return func(*args, **kwargs)

            with tracing_manager.tracer.start_as_current_span(operation_name) as span:
                # Add attributes
                span.set_attribute("operation.name", operation_name)
                span.set_attribute("function.name", func.__name__)

                # Add arguments as attributes
                for i, arg in enumerate(args):
                    if isinstance(arg, (str, int, float, bool)):
                        span.set_attribute(f"arg.{i}", str(arg))

                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"kwarg.{key}", str(value))

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    span.set_attribute("duration_ms", duration_ms)
                    span.set_attribute("status", "success")

                    return result

                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attribute(key: str, value: Any):
    """
    Add attribute to current span.

    Usage:
        add_span_attribute("user_id", "123")
        add_span_attribute("credits_used", 100)

    Args:
        key: Attribute key
        value: Attribute value
    """
    if not OTEL_AVAILABLE or not tracing_manager.enabled:
        return

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute(key, str(value))
    except Exception:
        pass


def add_span_event(name: str, attributes: Optional[dict] = None):
    """
    Add event to current span.

    Usage:
        add_span_event("payment_processed", {"amount": 100, "method": "stripe"})

    Args:
        name: Event name
        attributes: Event attributes
    """
    if not OTEL_AVAILABLE or not tracing_manager.enabled:
        return

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(name, attributes or {})
    except Exception:
        pass


def get_current_trace_id() -> Optional[str]:
    """
    Get current trace ID.

    Returns:
        Trace ID as hex string or None
    """
    if not OTEL_AVAILABLE or not tracing_manager.enabled:
        return None

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            trace_id = span.get_span_context().trace_id
            return format(trace_id, '032x')
    except Exception:
        pass

    return None


def get_current_span_id() -> Optional[str]:
    """
    Get current span ID.

    Returns:
        Span ID as hex string or None
    """
    if not OTEL_AVAILABLE or not tracing_manager.enabled:
        return None

    try:
        span = trace.get_current_span()
        if span and span.is_recording():
            span_id = span.get_span_context().span_id
            return format(span_id, '016x')
    except Exception:
        pass

    return None


# Convenience function for tracing database queries
def trace_db_query(query_type: str, table: str):
    """
    Decorator specifically for database queries.

    Usage:
        @trace_db_query("SELECT", "users")
        async def get_user(user_id: str):
            pass

    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
    """
    def decorator(func: Callable):
        @trace_request(f"db.{query_type}.{table}")
        @wraps(func)
        async def wrapper(*args, **kwargs):
            add_span_attribute("db.operation", query_type)
            add_span_attribute("db.table", table)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience function for tracing external API calls
def trace_external_call(service: str, operation: str):
    """
    Decorator for external service calls.

    Usage:
        @trace_external_call("stripe", "create_payment")
        async def create_stripe_payment(amount: float):
            pass

    Args:
        service: External service name
        operation: Operation being performed
    """
    def decorator(func: Callable):
        @trace_request(f"external.{service}.{operation}")
        @wraps(func)
        async def wrapper(*args, **kwargs):
            add_span_attribute("external.service", service)
            add_span_attribute("external.operation", operation)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
