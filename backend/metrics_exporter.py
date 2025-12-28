"""
Prometheus Metrics Exporter for Ops-Center
Provides custom application metrics for monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client import CollectorRegistry, multiprocess, generate_latest as generate_latest_multiproc
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import logging
import psutil
import os

logger = logging.getLogger(__name__)

# ======================
# Metric Definitions
# ======================

# API Request Metrics
api_requests_total = Counter(
    'ops_center_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'ops_center_api_request_duration_seconds',
    'API request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

api_errors_total = Counter(
    'ops_center_api_errors_total',
    'Total API errors',
    ['method', 'endpoint', 'status_code', 'error_type']
)

# Database Metrics
db_queries_total = Counter(
    'ops_center_db_queries_total',
    'Total database queries',
    ['query_type', 'table']
)

db_query_duration_seconds = Histogram(
    'ops_center_db_query_duration_seconds',
    'Database query latency in seconds',
    ['query_type', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# External API Metrics
cloudflare_api_calls_total = Counter(
    'ops_center_cloudflare_api_calls_total',
    'Total Cloudflare API calls',
    ['operation', 'status']
)

namecheap_api_calls_total = Counter(
    'ops_center_namecheap_api_calls_total',
    'Total NameCheap API calls',
    ['operation', 'status']
)

# Authentication Metrics
keycloak_logins_total = Counter(
    'ops_center_keycloak_logins_total',
    'Total Keycloak login attempts',
    ['status', 'provider']
)

keycloak_active_sessions = Gauge(
    'ops_center_keycloak_active_sessions',
    'Current number of active Keycloak sessions'
)

# Billing Metrics
lago_invoices_total = Counter(
    'ops_center_lago_invoices_total',
    'Total Lago invoices',
    ['status', 'plan']
)

lago_subscriptions_total = Gauge(
    'ops_center_lago_subscriptions_total',
    'Current number of active subscriptions',
    ['plan']
)

# User Metrics
active_users = Gauge(
    'ops_center_active_users',
    'Current number of active users',
    ['tier']
)

user_api_usage = Counter(
    'ops_center_user_api_usage',
    'User API call usage',
    ['user_id', 'endpoint']
)

# System Metrics
system_cpu_percent = Gauge(
    'ops_center_system_cpu_percent',
    'System CPU usage percentage'
)

system_memory_percent = Gauge(
    'ops_center_system_memory_percent',
    'System memory usage percentage'
)

system_disk_percent = Gauge(
    'ops_center_system_disk_percent',
    'System disk usage percentage',
    ['mountpoint']
)

# Business Metrics
total_revenue = Gauge(
    'ops_center_total_revenue_dollars',
    'Total revenue in dollars'
)

subscription_churn_rate = Gauge(
    'ops_center_subscription_churn_rate',
    'Subscription churn rate percentage'
)

# ======================
# Metrics Collection
# ======================

class MetricsCollector:
    """Collect and expose application metrics"""

    def __init__(self):
        self.start_time = time.time()

    async def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_percent.set(cpu_percent)

            # Memory
            mem = psutil.virtual_memory()
            system_memory_percent.set(mem.percent)

            # Disk
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    system_disk_percent.labels(mountpoint=partition.mountpoint).set(usage.percent)
                except PermissionError:
                    continue

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def track_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Track API request metrics"""
        api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

        # Track errors
        if status_code >= 400:
            error_type = "client_error" if status_code < 500 else "server_error"
            api_errors_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                error_type=error_type
            ).inc()

    def track_db_query(self, query_type: str, table: str, duration: float):
        """Track database query metrics"""
        db_queries_total.labels(query_type=query_type, table=table).inc()
        db_query_duration_seconds.labels(query_type=query_type, table=table).observe(duration)

    def track_cloudflare_api_call(self, operation: str, status: str):
        """Track Cloudflare API call"""
        cloudflare_api_calls_total.labels(operation=operation, status=status).inc()

    def track_namecheap_api_call(self, operation: str, status: str):
        """Track NameCheap API call"""
        namecheap_api_calls_total.labels(operation=operation, status=status).inc()

    def track_keycloak_login(self, status: str, provider: str = "keycloak"):
        """Track Keycloak login attempt"""
        keycloak_logins_total.labels(status=status, provider=provider).inc()

    def update_active_sessions(self, count: int):
        """Update active sessions gauge"""
        keycloak_active_sessions.set(count)

    def track_lago_invoice(self, status: str, plan: str):
        """Track Lago invoice"""
        lago_invoices_total.labels(status=status, plan=plan).inc()

    def update_active_subscriptions(self, plan: str, count: int):
        """Update active subscriptions gauge"""
        lago_subscriptions_total.labels(plan=plan).set(count)

    def update_active_users(self, tier: str, count: int):
        """Update active users gauge"""
        active_users.labels(tier=tier).set(count)

    def track_user_api_call(self, user_id: str, endpoint: str):
        """Track user API usage"""
        user_api_usage.labels(user_id=user_id, endpoint=endpoint).inc()

# Global metrics collector instance
metrics_collector = MetricsCollector()

# ======================
# Middleware
# ======================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API requests"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Track metrics
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code

        metrics_collector.track_api_request(method, endpoint, status_code, duration)

        return response

# ======================
# Metrics Endpoint
# ======================

async def metrics_endpoint():
    """Expose Prometheus metrics"""
    try:
        # Collect latest system metrics
        await metrics_collector.collect_system_metrics()

        # Generate metrics
        metrics = generate_latest(REGISTRY)

        return Response(content=metrics, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )

# ======================
# Helper Functions
# ======================

async def update_business_metrics_periodically():
    """Background task to update business metrics periodically"""
    import asyncio

    while True:
        try:
            # Update user counts by tier
            # This should query Keycloak/database for actual counts
            # Example: metrics_collector.update_active_users("trial", trial_count)

            # Update subscription counts
            # Example: metrics_collector.update_active_subscriptions("professional", pro_count)

            # Update revenue metrics
            # Example: total_revenue.set(calculated_revenue)

            await asyncio.sleep(60)  # Update every minute

        except Exception as e:
            logger.error(f"Error updating business metrics: {e}")
            await asyncio.sleep(60)

# Export for use in server.py
__all__ = [
    'metrics_collector',
    'PrometheusMiddleware',
    'metrics_endpoint',
    'update_business_metrics_periodically'
]
