"""
Prometheus Metrics Configuration

Comprehensive metrics for:
- API endpoint latency histograms
- Request rate counters
- Error rate by endpoint
- Credit balance gauges
- Subscription status metrics
- Database connection pool metrics
- LLM usage metrics
- Business metrics
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import FastAPI, Request, Response
from fastapi.responses import Response as FastAPIResponse
from typing import Callable
import time


class MetricsCollector:
    """Central metrics collector for Ops-Center."""

    def __init__(self):
        # HTTP Metrics
        self.http_requests_total = Counter(
            'ops_center_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )

        self.http_request_duration_seconds = Histogram(
            'ops_center_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )

        self.http_request_size_bytes = Histogram(
            'ops_center_http_request_size_bytes',
            'HTTP request size in bytes',
            ['method', 'endpoint']
        )

        self.http_response_size_bytes = Histogram(
            'ops_center_http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint']
        )

        # Error Metrics
        self.http_errors_total = Counter(
            'ops_center_http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'status', 'error_type']
        )

        # Credit System Metrics
        self.credit_balance = Gauge(
            'ops_center_credit_balance',
            'Current credit balance',
            ['user_id', 'organization_id', 'tier']
        )

        self.credit_transactions_total = Counter(
            'ops_center_credit_transactions_total',
            'Total credit transactions',
            ['transaction_type', 'user_id', 'organization_id']
        )

        self.credit_usage_total = Counter(
            'ops_center_credit_usage_total',
            'Total credits used',
            ['service', 'model', 'user_id', 'organization_id']
        )

        # Subscription Metrics
        self.subscription_status = Gauge(
            'ops_center_subscription_status',
            'Current subscription status (1=active, 0=inactive)',
            ['user_id', 'tier', 'status']
        )

        self.subscription_tier_distribution = Gauge(
            'ops_center_subscription_tier_distribution',
            'Number of users per subscription tier',
            ['tier']
        )

        self.subscription_changes_total = Counter(
            'ops_center_subscription_changes_total',
            'Total subscription changes',
            ['from_tier', 'to_tier', 'change_type']
        )

        # Database Metrics
        self.db_connections_active = Gauge(
            'ops_center_db_connections_active',
            'Active database connections',
            ['database']
        )

        self.db_connections_idle = Gauge(
            'ops_center_db_connections_idle',
            'Idle database connections in pool',
            ['database']
        )

        self.db_query_duration_seconds = Histogram(
            'ops_center_db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type', 'table'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )

        self.db_errors_total = Counter(
            'ops_center_db_errors_total',
            'Total database errors',
            ['database', 'error_type']
        )

        # LLM Usage Metrics
        self.llm_requests_total = Counter(
            'ops_center_llm_requests_total',
            'Total LLM requests',
            ['model', 'provider', 'user_id', 'status']
        )

        self.llm_tokens_total = Counter(
            'ops_center_llm_tokens_total',
            'Total LLM tokens processed',
            ['model', 'provider', 'token_type']  # token_type: prompt, completion
        )

        self.llm_request_duration_seconds = Histogram(
            'ops_center_llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['model', 'provider'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )

        self.llm_cost_total = Counter(
            'ops_center_llm_cost_total',
            'Total LLM cost in credits',
            ['model', 'provider', 'user_id', 'organization_id']
        )

        # Business Metrics
        self.user_registrations_total = Counter(
            'ops_center_user_registrations_total',
            'Total user registrations',
            ['tier', 'source']  # source: direct, sso_google, sso_github, etc.
        )

        self.user_logins_total = Counter(
            'ops_center_user_logins_total',
            'Total user logins',
            ['method']  # method: password, sso_google, sso_github, etc.
        )

        self.payment_transactions_total = Counter(
            'ops_center_payment_transactions_total',
            'Total payment transactions',
            ['status', 'payment_method', 'tier']
        )

        self.revenue_total = Counter(
            'ops_center_revenue_total',
            'Total revenue in cents',
            ['tier', 'payment_method']
        )

        # Organization Metrics
        self.organizations_total = Gauge(
            'ops_center_organizations_total',
            'Total number of organizations'
        )

        self.organization_members = Gauge(
            'ops_center_organization_members',
            'Number of members per organization',
            ['organization_id', 'organization_name']
        )

        # Feature Access Metrics
        self.feature_access_total = Counter(
            'ops_center_feature_access_total',
            'Total feature access attempts',
            ['feature', 'tier', 'allowed']  # allowed: true, false
        )

        # Security Metrics
        self.auth_failures_total = Counter(
            'ops_center_auth_failures_total',
            'Total authentication failures',
            ['reason', 'method']
        )

        self.rate_limit_exceeded_total = Counter(
            'ops_center_rate_limit_exceeded_total',
            'Total rate limit violations',
            ['endpoint', 'user_id']
        )

        # System Info
        self.build_info = Info(
            'ops_center_build',
            'Ops-Center build information'
        )

        # API Key Metrics
        self.api_key_usage_total = Counter(
            'ops_center_api_key_usage_total',
            'Total API key usage',
            ['key_id', 'user_id', 'endpoint']
        )

        # Webhook Metrics
        self.webhook_deliveries_total = Counter(
            'ops_center_webhook_deliveries_total',
            'Total webhook deliveries',
            ['event_type', 'status']
        )

    def set_build_info(self, version: str, commit: str, build_date: str):
        """Set build information."""
        self.build_info.info({
            'version': version,
            'commit': commit,
            'build_date': build_date
        })


# Global metrics instance
metrics = MetricsCollector()


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance
    """

    # Add /metrics endpoint
    @app.get("/metrics")
    async def metrics_endpoint():
        """Expose Prometheus metrics."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    # Add middleware for automatic HTTP metrics
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        """Middleware to collect HTTP metrics."""
        start_time = time.time()

        # Get request size
        request_size = len(await request.body())

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Get endpoint path (remove query params)
            endpoint = request.url.path

            # Record metrics
            metrics.http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()

            metrics.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)

            metrics.http_request_size_bytes.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(request_size)

            # Get response size if available
            if hasattr(response, 'body'):
                response_size = len(response.body)
                metrics.http_response_size_bytes.labels(
                    method=request.method,
                    endpoint=endpoint
                ).observe(response_size)

            # Record errors
            if response.status_code >= 400:
                error_type = "client_error" if response.status_code < 500 else "server_error"
                metrics.http_errors_total.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code,
                    error_type=error_type
                ).inc()

            return response

        except Exception as e:
            # Record exception
            duration = time.time() - start_time

            metrics.http_errors_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500,
                error_type=type(e).__name__
            ).inc()

            raise


def record_credit_transaction(
    transaction_type: str,
    user_id: str,
    organization_id: str,
    amount: float
):
    """
    Record credit transaction metric.

    Args:
        transaction_type: Type of transaction (purchase, usage, refund, etc.)
        user_id: User ID
        organization_id: Organization ID
        amount: Transaction amount (positive or negative)
    """
    metrics.credit_transactions_total.labels(
        transaction_type=transaction_type,
        user_id=user_id,
        organization_id=organization_id
    ).inc()


def record_llm_usage(
    model: str,
    provider: str,
    user_id: str,
    organization_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_seconds: float,
    cost_credits: float,
    status: str = "success"
):
    """
    Record LLM usage metrics.

    Args:
        model: Model name
        provider: Provider name (openai, anthropic, etc.)
        user_id: User ID
        organization_id: Organization ID
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        duration_seconds: Request duration in seconds
        cost_credits: Cost in credits
        status: Request status (success, error)
    """
    metrics.llm_requests_total.labels(
        model=model,
        provider=provider,
        user_id=user_id,
        status=status
    ).inc()

    metrics.llm_tokens_total.labels(
        model=model,
        provider=provider,
        token_type="prompt"
    ).inc(prompt_tokens)

    metrics.llm_tokens_total.labels(
        model=model,
        provider=provider,
        token_type="completion"
    ).inc(completion_tokens)

    metrics.llm_request_duration_seconds.labels(
        model=model,
        provider=provider
    ).observe(duration_seconds)

    metrics.llm_cost_total.labels(
        model=model,
        provider=provider,
        user_id=user_id,
        organization_id=organization_id
    ).inc(cost_credits)
