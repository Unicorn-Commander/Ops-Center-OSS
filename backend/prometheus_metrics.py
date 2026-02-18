"""
Prometheus Metrics Exporter
Exposes metrics at /metrics endpoint for Prometheus scraping
"""

import time
import asyncio
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from fastapi import APIRouter, Response, Request
from typing import Dict
import psutil
import docker

router = APIRouter()

# Create custom registry to avoid conflicts
ops_center_registry = CollectorRegistry()

# HTTP Metrics
http_requests_total = Counter(
    'ops_center_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=ops_center_registry
)

http_request_duration_seconds = Histogram(
    'ops_center_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=ops_center_registry
)

http_requests_in_progress = Gauge(
    'ops_center_http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    registry=ops_center_registry
)

# User Metrics
active_users = Gauge(
    'ops_center_active_users_total',
    'Number of active users with sessions',
    registry=ops_center_registry
)

total_users = Gauge(
    'ops_center_total_users',
    'Total number of registered users',
    registry=ops_center_registry
)

users_by_tier = Gauge(
    'ops_center_users_by_tier',
    'Number of users per subscription tier',
    ['tier'],
    registry=ops_center_registry
)

# LLM API Metrics
llm_api_calls_total = Counter(
    'ops_center_llm_api_calls_total',
    'Total LLM API calls',
    ['model', 'provider', 'user_tier'],
    registry=ops_center_registry
)

llm_tokens_processed = Counter(
    'ops_center_llm_tokens_processed_total',
    'Total tokens processed',
    ['model', 'token_type'],  # token_type: input or output
    registry=ops_center_registry
)

llm_credits_spent = Counter(
    'ops_center_llm_credits_spent_total',
    'Total credits spent on LLM calls',
    ['user_id', 'model', 'tier'],
    registry=ops_center_registry
)

llm_request_duration = Histogram(
    'ops_center_llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model', 'provider'],
    registry=ops_center_registry
)

llm_errors_total = Counter(
    'ops_center_llm_errors_total',
    'Total LLM API errors',
    ['model', 'error_type'],
    registry=ops_center_registry
)

# Organization Metrics
organizations_total = Gauge(
    'ops_center_organizations_total',
    'Total number of organizations',
    registry=ops_center_registry
)

organization_members = Gauge(
    'ops_center_organization_members',
    'Number of members per organization',
    ['org_id', 'org_name'],
    registry=ops_center_registry
)

# Credit Balance Metrics
credit_balance = Gauge(
    'ops_center_credit_balance',
    'Credit balance by organization',
    ['org_id', 'tier'],
    registry=ops_center_registry
)

credit_transactions_total = Counter(
    'ops_center_credit_transactions_total',
    'Total credit transactions',
    ['org_id', 'transaction_type'],  # transaction_type: purchase, usage, refund
    registry=ops_center_registry
)

# System Resource Metrics
system_cpu_percent = Gauge(
    'ops_center_system_cpu_percent',
    'System CPU usage percentage',
    registry=ops_center_registry
)

system_memory_percent = Gauge(
    'ops_center_system_memory_percent',
    'System memory usage percentage',
    registry=ops_center_registry
)

system_disk_percent = Gauge(
    'ops_center_system_disk_percent',
    'System disk usage percentage',
    ['mount_point'],
    registry=ops_center_registry
)

# Docker Container Metrics
docker_containers_running = Gauge(
    'ops_center_docker_containers_running',
    'Number of running Docker containers',
    registry=ops_center_registry
)

docker_container_status = Gauge(
    'ops_center_docker_container_status',
    'Docker container status (1=running, 0=stopped)',
    ['container_name', 'image'],
    registry=ops_center_registry
)

# Database Metrics
database_connections = Gauge(
    'ops_center_database_connections',
    'Number of active database connections',
    ['database'],
    registry=ops_center_registry
)

database_query_duration = Histogram(
    'ops_center_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    registry=ops_center_registry
)

# Cache Metrics (Redis)
cache_hits_total = Counter(
    'ops_center_cache_hits_total',
    'Total cache hits',
    ['cache_key_prefix'],
    registry=ops_center_registry
)

cache_misses_total = Counter(
    'ops_center_cache_misses_total',
    'Total cache misses',
    ['cache_key_prefix'],
    registry=ops_center_registry
)

# Subscription Metrics
subscriptions_active = Gauge(
    'ops_center_subscriptions_active',
    'Number of active subscriptions',
    ['tier'],
    registry=ops_center_registry
)

subscription_mrr = Gauge(
    'ops_center_subscription_mrr',
    'Monthly Recurring Revenue (MRR) in cents',
    ['tier'],
    registry=ops_center_registry
)

# API Usage Metrics
api_usage_quota_remaining = Gauge(
    'ops_center_api_usage_quota_remaining',
    'Remaining API call quota',
    ['user_id', 'tier'],
    registry=ops_center_registry
)

api_usage_reset_timestamp = Gauge(
    'ops_center_api_usage_reset_timestamp',
    'Unix timestamp of next quota reset',
    ['user_id'],
    registry=ops_center_registry
)

# Application Info
app_info = Info(
    'ops_center_build',
    'Ops-Center application build information',
    registry=ops_center_registry
)

app_info.info({
    'version': '2.5.0',
    'build_date': '2026-02-18',
    'python_version': '3.10'
})

# Background task to update system metrics
async def update_system_metrics():
    """Background task to periodically update system metrics"""
    while True:
        try:
            # CPU and Memory
            system_cpu_percent.set(psutil.cpu_percent(interval=1))
            system_memory_percent.set(psutil.virtual_memory().percent)

            # Disk usage for all mount points
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    system_disk_percent.labels(mount_point=partition.mountpoint).set(usage.percent)
                except:
                    pass

            # Docker container status
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                docker_containers_running.set(len([c for c in containers if c.status == 'running']))

                for container in containers:
                    status = 1 if container.status == 'running' else 0
                    docker_container_status.labels(
                        container_name=container.name,
                        image=container.image.tags[0] if container.image.tags else 'unknown'
                    ).set(status)
            except:
                pass

        except Exception as e:
            print(f"Error updating system metrics: {e}")

        await asyncio.sleep(15)  # Update every 15 seconds

@router.on_event("startup")
async def start_metrics_updater():
    """Start background metrics updater on app startup"""
    asyncio.create_task(update_system_metrics())

@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics in OpenMetrics format"""
    return Response(
        content=generate_latest(ops_center_registry),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/metrics/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {
        "status": "healthy",
        "metrics_enabled": True,
        "registry": "ops_center_registry"
    }

# Helper functions for recording metrics (to be used by other modules)
def record_http_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

def record_llm_call(model: str, provider: str, user_tier: str, tokens_in: int, tokens_out: int, credits: float, duration: float):
    """Record LLM API call metrics"""
    llm_api_calls_total.labels(model=model, provider=provider, user_tier=user_tier).inc()
    llm_tokens_processed.labels(model=model, token_type='input').inc(tokens_in)
    llm_tokens_processed.labels(model=model, token_type='output').inc(tokens_out)
    llm_credits_spent.labels(user_id='aggregate', model=model, tier=user_tier).inc(credits)
    llm_request_duration.labels(model=model, provider=provider).observe(duration)

def record_llm_error(model: str, error_type: str):
    """Record LLM API error"""
    llm_errors_total.labels(model=model, error_type=error_type).inc()

def update_user_metrics(total: int, active: int, by_tier: Dict[str, int]):
    """Update user count metrics"""
    total_users.set(total)
    active_users.set(active)
    for tier, count in by_tier.items():
        users_by_tier.labels(tier=tier).set(count)

def update_credit_balance(org_id: str, tier: str, balance: float):
    """Update credit balance metric"""
    credit_balance.labels(org_id=org_id, tier=tier).set(balance)

def record_cache_hit(key_prefix: str):
    """Record cache hit"""
    cache_hits_total.labels(cache_key_prefix=key_prefix).inc()

def record_cache_miss(key_prefix: str):
    """Record cache miss"""
    cache_misses_total.labels(cache_key_prefix=key_prefix).inc()
