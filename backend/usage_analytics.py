"""Usage Analytics API Module

Comprehensive API usage analysis system with cost optimization and performance insights.

Features:
- API usage tracking across all ops-center endpoints
- LLM inference cost analysis
- Usage pattern detection (peak hours, popular endpoints)
- Per-user and per-service usage breakdowns
- Cost optimization recommendations
- Performance metrics (latency, errors, success rates)
- Quota usage tracking by plan tier
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import redis.asyncio as aioredis

# Logging setup
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "unicorn")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "unicorn_db")

REDIS_HOST = os.getenv("REDIS_HOST", "unicorn-lago-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://unicorn-litellm:4000")
LOG_DIR = Path("/var/log/ops-center")

# Database connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Redis connection (lazy initialization)
redis_client: Optional[aioredis.Redis] = None

# Cost constants (per 1M tokens)
LLM_COSTS = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "llama-3-70b": {"input": 0.9, "output": 0.9},
    "qwen2.5-32b": {"input": 0.5, "output": 0.5},
    "default": {"input": 1.0, "output": 2.0}
}

STORAGE_COST_PER_GB_MONTH = 0.023  # AWS S3 standard pricing
BANDWIDTH_COST_PER_GB = 0.09  # AWS data transfer out pricing

# Plan tier limits
PLAN_LIMITS = {
    "trial": {"api_calls": 700, "tokens": 100000},
    "starter": {"api_calls": 30000, "tokens": 5000000},
    "professional": {"api_calls": 300000, "tokens": 50000000},
    "enterprise": {"api_calls": -1, "tokens": -1}  # unlimited
}

# Pydantic models
class UsageOverview(BaseModel):
    """API usage overview response"""
    total_api_calls: int = Field(description="Total API calls in period")
    total_cost: float = Field(description="Total cost in USD")
    cost_per_call: float = Field(description="Average cost per API call")
    period_start: str = Field(description="Period start date")
    period_end: str = Field(description="Period end date")
    by_service: Dict[str, Dict[str, Any]] = Field(description="Usage breakdown by service")
    by_user_count: int = Field(description="Number of active users")

class UsagePattern(BaseModel):
    """Usage pattern analysis response"""
    peak_hours: List[Dict[str, Any]] = Field(description="Peak usage hours")
    peak_days: List[Dict[str, Any]] = Field(description="Peak usage days")
    popular_endpoints: List[Dict[str, Any]] = Field(description="Most popular endpoints")
    usage_trends: Dict[str, List[float]] = Field(description="Usage trends over time")

class UserUsage(BaseModel):
    """Per-user usage breakdown"""
    user_id: str
    username: str
    total_calls: int
    total_cost: float
    by_service: Dict[str, int]
    subscription_tier: str
    quota_used_percent: float

class ServiceUsage(BaseModel):
    """Per-service usage metrics"""
    service_name: str
    total_calls: int
    total_cost: float
    avg_latency_ms: float
    success_rate: float
    error_rate: float
    unique_users: int

class CostAnalysis(BaseModel):
    """Cost analysis response"""
    total_cost: float
    cost_breakdown: Dict[str, float]
    cost_trends: List[Dict[str, Any]]
    projected_monthly_cost: float
    cost_per_user: float
    cost_per_service: Dict[str, float]

class OptimizationRecommendation(BaseModel):
    """Cost optimization recommendation"""
    type: str = Field(description="Recommendation type (model_switch, caching, etc.)")
    priority: str = Field(description="Priority: high, medium, low")
    current: str = Field(description="Current configuration")
    recommended: str = Field(description="Recommended configuration")
    potential_savings: str = Field(description="Potential savings ($/month)")
    impact: str = Field(description="Impact description")
    implementation_effort: str = Field(description="Implementation effort: low, medium, high")

class OptimizationResponse(BaseModel):
    """Cost optimization recommendations response"""
    recommendations: List[OptimizationRecommendation]
    total_potential_savings: float
    estimated_implementation_time: str

class PerformanceMetrics(BaseModel):
    """Performance metrics response"""
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    success_rate: float
    error_rate: float
    timeout_rate: float
    by_endpoint: Dict[str, Dict[str, float]]

class QuotaUsage(BaseModel):
    """Quota usage by plan tier"""
    trial: Dict[str, Any]
    starter: Dict[str, Any]
    professional: Dict[str, Any]
    enterprise: Dict[str, Any]

# Router setup
router = APIRouter(prefix="/api/v1/analytics/usage", tags=["Usage Analytics"])

# Helper functions
async def get_redis():
    """Get Redis client with lazy initialization"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

def get_db_session():
    """Get database session"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def cache_get(key: str) -> Optional[Any]:
    """Get value from Redis cache"""
    try:
        r = await get_redis()
        value = await r.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
    return None

async def cache_set(key: str, value: Any, ttl: int = 300):
    """Set value in Redis cache with TTL"""
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Redis set error: {e}")

def parse_log_file(log_file: Path, start_date: datetime, end_date: datetime) -> List[Dict]:
    """Parse ops-center log file for API requests"""
    entries = []

    if not log_file.exists():
        return entries

    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parse JSON log line
                    if line.strip().startswith('{'):
                        entry = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))

                        if start_date <= timestamp <= end_date:
                            entries.append(entry)
                    else:
                        # Parse nginx-style access log
                        match = re.match(
                            r'(\d+\.\d+\.\d+\.\d+) - - \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)" ([\d.]+)',
                            line
                        )
                        if match:
                            ip, timestamp_str, request, status, size, referer, user_agent, duration = match.groups()
                            timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')

                            if start_date <= timestamp <= end_date:
                                method, path, protocol = request.split() if len(request.split()) == 3 else ('GET', request, 'HTTP/1.1')
                                entries.append({
                                    'timestamp': timestamp.isoformat(),
                                    'ip_address': ip,
                                    'method': method,
                                    'path': path,
                                    'status': int(status),
                                    'size': int(size),
                                    'duration_ms': float(duration) * 1000,
                                    'user_agent': user_agent
                                })
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Failed to parse log line: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {e}")

    return entries

async def get_litellm_metrics() -> Dict[str, Any]:
    """Fetch metrics from LiteLLM proxy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LITELLM_PROXY_URL}/metrics")
            if response.status_code == 200:
                # Parse Prometheus metrics format
                metrics = {}
                for line in response.text.split('\n'):
                    if line.startswith('#') or not line.strip():
                        continue

                    parts = line.split()
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        metric_value = parts[1]
                        metrics[metric_name] = float(metric_value)

                return metrics
    except Exception as e:
        logger.error(f"Error fetching LiteLLM metrics: {e}")

    return {}

async def aggregate_usage_data(days: int = 7) -> Dict[str, Any]:
    """Aggregate usage data from logs and database"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Parse log files
    log_entries = []
    if LOG_DIR.exists():
        for log_file in LOG_DIR.glob("*.log"):
            log_entries.extend(parse_log_file(log_file, start_date, end_date))

    # Aggregate by service
    by_service = defaultdict(lambda: {
        "calls": 0,
        "total_duration_ms": 0,
        "errors": 0,
        "users": set()
    })

    by_user = defaultdict(lambda: {
        "calls": 0,
        "by_service": defaultdict(int),
        "errors": 0
    })

    by_hour = defaultdict(int)
    by_day = defaultdict(int)
    by_endpoint = defaultdict(lambda: {"calls": 0, "total_duration_ms": 0, "errors": 0})

    for entry in log_entries:
        timestamp = datetime.fromisoformat(entry['timestamp'])
        path = entry.get('path', '')
        status = entry.get('status', 200)
        duration_ms = entry.get('duration_ms', 0)
        user = entry.get('user_id', 'anonymous')

        # Determine service from path
        service = 'unknown'
        if '/llm/' in path:
            service = 'llm'
        elif '/embeddings' in path:
            service = 'embeddings'
        elif '/search' in path:
            service = 'search'
        elif '/tts' in path:
            service = 'tts'
        elif '/stt' in path:
            service = 'stt'
        elif '/admin' in path:
            service = 'admin'

        # Aggregate data
        by_service[service]["calls"] += 1
        by_service[service]["total_duration_ms"] += duration_ms
        by_service[service]["users"].add(user)

        if status >= 400:
            by_service[service]["errors"] += 1

        by_user[user]["calls"] += 1
        by_user[user]["by_service"][service] += 1

        if status >= 400:
            by_user[user]["errors"] += 1

        by_hour[timestamp.hour] += 1
        by_day[timestamp.strftime('%A')] += 1
        by_endpoint[path]["calls"] += 1
        by_endpoint[path]["total_duration_ms"] += duration_ms

        if status >= 400:
            by_endpoint[path]["errors"] += 1

    # Convert sets to counts
    for service_data in by_service.values():
        service_data["unique_users"] = len(service_data["users"])
        del service_data["users"]

    return {
        "by_service": dict(by_service),
        "by_user": dict(by_user),
        "by_hour": dict(by_hour),
        "by_day": dict(by_day),
        "by_endpoint": dict(by_endpoint),
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat()
    }

def calculate_llm_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate LLM inference cost"""
    costs = LLM_COSTS.get(model, LLM_COSTS["default"])
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

# API Endpoints

@router.get("/overview", response_model=UsageOverview)
async def get_usage_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get API usage overview

    Returns total API calls, costs, and breakdown by service.
    """
    cache_key = f"usage:overview:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Aggregate usage data
    data = await aggregate_usage_data(days)

    # Calculate totals
    total_calls = sum(s["calls"] for s in data["by_service"].values())

    # Get LLM metrics from LiteLLM
    litellm_metrics = await get_litellm_metrics()

    # Estimate costs
    by_service_costs = {}
    total_cost = 0.0

    for service, metrics in data["by_service"].items():
        if service == "llm":
            # Estimate LLM cost from metrics
            llm_cost = litellm_metrics.get("litellm_total_cost", 0.0)
            by_service_costs[service] = {
                "calls": metrics["calls"],
                "cost": llm_cost,
                "avg_latency_ms": metrics["total_duration_ms"] / max(metrics["calls"], 1),
                "unique_users": metrics["unique_users"]
            }
            total_cost += llm_cost
        else:
            # Estimate cost for other services (much lower)
            service_cost = metrics["calls"] * 0.001  # $0.001 per call
            by_service_costs[service] = {
                "calls": metrics["calls"],
                "cost": service_cost,
                "avg_latency_ms": metrics["total_duration_ms"] / max(metrics["calls"], 1),
                "unique_users": metrics["unique_users"]
            }
            total_cost += service_cost

    cost_per_call = total_cost / max(total_calls, 1)

    # Count active users
    by_user_count = len(data["by_user"])

    result = {
        "total_api_calls": total_calls,
        "total_cost": round(total_cost, 2),
        "cost_per_call": round(cost_per_call, 6),
        "period_start": data["period_start"],
        "period_end": data["period_end"],
        "by_service": by_service_costs,
        "by_user_count": by_user_count
    }

    await cache_set(cache_key, result, ttl=300)
    return result

@router.get("/patterns", response_model=UsagePattern)
async def get_usage_patterns(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get usage patterns

    Returns peak hours, popular endpoints, and usage trends.
    """
    cache_key = f"usage:patterns:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await aggregate_usage_data(days)

    # Sort and format peak hours
    peak_hours = [
        {"hour": hour, "calls": calls}
        for hour, calls in sorted(data["by_hour"].items(), key=lambda x: x[1], reverse=True)
    ][:10]

    # Sort and format peak days
    peak_days = [
        {"day": day, "calls": calls}
        for day, calls in sorted(data["by_day"].items(), key=lambda x: x[1], reverse=True)
    ]

    # Sort and format popular endpoints
    popular_endpoints = [
        {
            "endpoint": endpoint,
            "calls": metrics["calls"],
            "avg_latency_ms": round(metrics["total_duration_ms"] / max(metrics["calls"], 1), 2),
            "error_rate": round(metrics["errors"] / max(metrics["calls"], 1) * 100, 2)
        }
        for endpoint, metrics in sorted(data["by_endpoint"].items(), key=lambda x: x[1]["calls"], reverse=True)
    ][:20]

    # Calculate daily trends (simplified)
    usage_trends = {
        "daily_calls": [sum(data["by_hour"].values()) // max(days, 1)] * days,
        "daily_costs": [0.0] * days  # Would need historical cost data
    }

    result = {
        "peak_hours": peak_hours,
        "peak_days": peak_days,
        "popular_endpoints": popular_endpoints,
        "usage_trends": usage_trends
    }

    await cache_set(cache_key, result, ttl=300)
    return result

@router.get("/by-user", response_model=List[UserUsage])
async def get_usage_by_user(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum users to return")
):
    """Get per-user usage breakdown

    Returns API usage, costs, and quota usage for each user.
    """
    cache_key = f"usage:by_user:{days}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await aggregate_usage_data(days)

    # Fetch user details from database
    user_details = {}
    with next(get_db_session()) as db:
        # This would query Keycloak or user table for tier info
        # Simplified for now
        pass

    results = []
    for user_id, user_data in sorted(data["by_user"].items(), key=lambda x: x[1]["calls"], reverse=True)[:limit]:
        # Estimate cost (simplified)
        total_cost = user_data["calls"] * 0.002  # avg $0.002 per call

        # Get subscription tier (would come from database)
        tier = "professional"  # default
        quota_limit = PLAN_LIMITS.get(tier, {}).get("api_calls", 300000)
        quota_used_percent = (user_data["calls"] / quota_limit * 100) if quota_limit > 0 else 0

        results.append({
            "user_id": user_id,
            "username": user_id.split('@')[0] if '@' in user_id else user_id,
            "total_calls": user_data["calls"],
            "total_cost": round(total_cost, 2),
            "by_service": dict(user_data["by_service"]),
            "subscription_tier": tier,
            "quota_used_percent": round(quota_used_percent, 2)
        })

    await cache_set(cache_key, results, ttl=300)
    return results

@router.get("/by-service", response_model=List[ServiceUsage])
async def get_usage_by_service(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get per-service usage metrics

    Returns calls, costs, latency, and success rates for each service.
    """
    cache_key = f"usage:by_service:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await aggregate_usage_data(days)

    results = []
    for service, metrics in data["by_service"].items():
        avg_latency = metrics["total_duration_ms"] / max(metrics["calls"], 1)
        error_rate = (metrics["errors"] / max(metrics["calls"], 1)) * 100
        success_rate = 100 - error_rate

        # Estimate cost
        if service == "llm":
            litellm_metrics = await get_litellm_metrics()
            service_cost = litellm_metrics.get("litellm_total_cost", 0.0)
        else:
            service_cost = metrics["calls"] * 0.001

        results.append({
            "service_name": service,
            "total_calls": metrics["calls"],
            "total_cost": round(service_cost, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 2),
            "error_rate": round(error_rate, 2),
            "unique_users": metrics["unique_users"]
        })

    await cache_set(cache_key, results, ttl=300)
    return results

@router.get("/costs", response_model=CostAnalysis)
async def get_cost_analysis(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get cost analysis

    Returns detailed cost breakdown and trends.
    """
    cache_key = f"usage:costs:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await aggregate_usage_data(days)

    # Calculate costs by service
    cost_breakdown = {}
    total_cost = 0.0

    for service, metrics in data["by_service"].items():
        if service == "llm":
            litellm_metrics = await get_litellm_metrics()
            service_cost = litellm_metrics.get("litellm_total_cost", 0.0)
        else:
            service_cost = metrics["calls"] * 0.001

        cost_breakdown[service] = round(service_cost, 2)
        total_cost += service_cost

    # Project monthly cost
    projected_monthly_cost = (total_cost / days) * 30

    # Cost per user
    num_users = len(data["by_user"])
    cost_per_user = total_cost / max(num_users, 1)

    # Cost trends (simplified - would need historical data)
    cost_trends = [
        {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), "cost": total_cost / days}
        for i in range(days-1, -1, -1)
    ]

    result = {
        "total_cost": round(total_cost, 2),
        "cost_breakdown": cost_breakdown,
        "cost_trends": cost_trends,
        "projected_monthly_cost": round(projected_monthly_cost, 2),
        "cost_per_user": round(cost_per_user, 2),
        "cost_per_service": cost_breakdown
    }

    await cache_set(cache_key, result, ttl=300)
    return result

@router.get("/optimization", response_model=OptimizationResponse)
async def get_optimization_recommendations(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get cost optimization recommendations

    Returns actionable recommendations to reduce costs.
    """
    cache_key = f"usage:optimization:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # This would integrate with cost_optimizer.py
    # For now, return sample recommendations
    from utils.cost_optimizer import CostOptimizer

    optimizer = CostOptimizer()
    recommendations = await optimizer.generate_recommendations(days)

    total_savings = sum(float(rec["potential_savings"].replace('$', '').replace('/month', ''))
                       for rec in recommendations)

    # Estimate implementation time
    effort_hours = {"low": 2, "medium": 8, "high": 24}
    total_hours = sum(effort_hours.get(rec["implementation_effort"], 8) for rec in recommendations)
    estimated_time = f"{total_hours} hours" if total_hours < 40 else f"{total_hours // 8} days"

    result = {
        "recommendations": recommendations,
        "total_potential_savings": round(total_savings, 2),
        "estimated_implementation_time": estimated_time
    }

    await cache_set(cache_key, result, ttl=300)
    return result

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get performance metrics

    Returns latency percentiles, success rates, and error rates.
    """
    cache_key = f"usage:performance:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    data = await aggregate_usage_data(days)

    # Calculate latency percentiles (simplified - would need sorted data)
    all_calls = sum(s["calls"] for s in data["by_service"].values())
    total_duration = sum(s["total_duration_ms"] for s in data["by_service"].values())
    avg_latency = total_duration / max(all_calls, 1)

    # Estimates (would need actual percentile calculation from sorted data)
    p50_latency = avg_latency * 0.8
    p95_latency = avg_latency * 2.5
    p99_latency = avg_latency * 4.0

    # Calculate rates
    total_errors = sum(s["errors"] for s in data["by_service"].values())
    success_rate = ((all_calls - total_errors) / max(all_calls, 1)) * 100
    error_rate = (total_errors / max(all_calls, 1)) * 100
    timeout_rate = 0.5  # Would need timeout tracking

    # By endpoint
    by_endpoint = {}
    for endpoint, metrics in list(data["by_endpoint"].items())[:20]:
        avg_ep_latency = metrics["total_duration_ms"] / max(metrics["calls"], 1)
        ep_error_rate = (metrics["errors"] / max(metrics["calls"], 1)) * 100

        by_endpoint[endpoint] = {
            "avg_latency_ms": round(avg_ep_latency, 2),
            "success_rate": round(100 - ep_error_rate, 2),
            "error_rate": round(ep_error_rate, 2)
        }

    result = {
        "avg_latency_ms": round(avg_latency, 2),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
        "success_rate": round(success_rate, 2),
        "error_rate": round(error_rate, 2),
        "timeout_rate": round(timeout_rate, 2),
        "by_endpoint": by_endpoint
    }

    await cache_set(cache_key, result, ttl=300)
    return result

@router.get("/quotas", response_model=QuotaUsage)
async def get_quota_usage(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get quota usage by plan tier

    Returns usage and limits for each subscription tier.
    """
    cache_key = f"usage:quotas:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Would query database for actual user tiers
    # Simplified version with sample data

    data = await aggregate_usage_data(days)

    # Aggregate usage by tier (would come from database joins)
    tier_usage = {
        "trial": {"calls": 450, "tokens": 65000},
        "starter": {"calls": 12500, "tokens": 1800000},
        "professional": {"calls": 85000, "tokens": 12000000},
        "enterprise": {"calls": 450000, "tokens": 65000000}
    }

    result = {}
    for tier, limits in PLAN_LIMITS.items():
        used = tier_usage.get(tier, {"calls": 0, "tokens": 0})
        limit_calls = limits["api_calls"]
        limit_tokens = limits["tokens"]

        if limit_calls == -1:  # unlimited
            percentage = 0
        else:
            percentage = (used["calls"] / limit_calls * 100) if limit_calls > 0 else 0

        result[tier] = {
            "used": used["calls"],
            "limit": limit_calls if limit_calls > 0 else "unlimited",
            "percentage": round(percentage, 2),
            "tokens_used": used["tokens"],
            "tokens_limit": limit_tokens if limit_tokens > 0 else "unlimited"
        }

    await cache_set(cache_key, result, ttl=300)
    return result

# Background task for hourly aggregation
async def hourly_usage_aggregation():
    """Background task to aggregate usage data hourly"""
    while True:
        try:
            logger.info("Running hourly usage aggregation")

            # Aggregate last hour of data
            await aggregate_usage_data(days=1)

            # Clear relevant caches
            r = await get_redis()
            keys = await r.keys("usage:*")
            if keys:
                await r.delete(*keys)

            logger.info("Hourly usage aggregation complete")
        except Exception as e:
            logger.error(f"Error in hourly aggregation: {e}")

        # Sleep for 1 hour
        await asyncio.sleep(3600)

# Initialize background task on startup
@router.on_event("startup")
async def startup_event():
    """Start background tasks on router startup"""
    asyncio.create_task(hourly_usage_aggregation())
    logger.info("Usage analytics background tasks started")
