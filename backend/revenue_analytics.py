"""
Revenue Analytics Module for UC-Cloud Ops Center
Epic 2.6: Advanced Analytics - Revenue Analytics Lead

Provides comprehensive revenue analytics including MRR, ARR, forecasts,
and billing trends with integration to Lago billing system.

Author: Revenue Analytics Lead
Created: October 24, 2025
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio
import httpx
import numpy as np
from scipy import stats
import redis.asyncio as redis
import json
import os

# Import universal credential helper
from get_credential import get_credential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/analytics/revenue", tags=["Revenue Analytics"])

# Lago API configuration - read credentials from database first, then environment
LAGO_API_URL = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")
LAGO_API_KEY = get_credential("LAGO_API_KEY")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://unicorn-redis:6379/0")
CACHE_TTL = 300  # 5 minutes


# Pydantic models
class RevenueOverview(BaseModel):
    """Revenue overview metrics"""
    mrr: float = Field(..., description="Monthly Recurring Revenue")
    arr: float = Field(..., description="Annual Recurring Revenue")
    growth_rate: float = Field(..., description="Month-over-month growth rate (%)")
    churn_rate: float = Field(..., description="Monthly churn rate (%)")
    active_subscriptions: int = Field(..., description="Number of active subscriptions")
    total_customers: int = Field(..., description="Total active customers")
    average_revenue_per_user: float = Field(..., description="ARPU")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RevenueTrend(BaseModel):
    """Historical revenue trend data"""
    period: str = Field(..., description="Time period (daily/weekly/monthly)")
    data: List[Dict[str, Any]] = Field(..., description="Time series data")
    total_revenue: float = Field(..., description="Total revenue for period")
    average_revenue: float = Field(..., description="Average revenue per period")


class RevenueByPlan(BaseModel):
    """Revenue breakdown by subscription plan"""
    plan_code: str
    plan_name: str
    mrr: float
    subscriber_count: int
    percentage: float
    average_revenue_per_subscriber: float


class RevenueForecast(BaseModel):
    """Revenue forecast model"""
    forecast_3_months: float
    forecast_6_months: float
    forecast_12_months: float
    confidence_interval_low: float
    confidence_interval_high: float
    forecast_method: str = "linear_regression"
    accuracy_score: float


class ChurnImpact(BaseModel):
    """Churn impact on revenue"""
    churned_mrr: float
    churned_subscribers: int
    churn_rate: float
    revenue_impact: float
    period: str


class LifetimeValue(BaseModel):
    """Customer lifetime value metrics"""
    average_ltv: float
    ltv_by_plan: Dict[str, float]
    average_customer_lifetime_months: float
    ltv_to_cac_ratio: Optional[float] = None


class CohortRevenue(BaseModel):
    """Revenue by customer cohort"""
    cohort: str
    customer_count: int
    total_revenue: float
    average_revenue_per_customer: float
    retention_rate: float


# Dependency for HTTP client
async def get_http_client():
    """Get HTTP client for Lago API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


# Dependency for Redis connection
async def get_redis():
    """Get Redis connection"""
    r = await redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close()


# Helper functions
async def cache_get(redis_client: redis.Redis, key: str) -> Optional[Any]:
    """Get data from cache"""
    try:
        data = await redis_client.get(f"revenue:{key}")
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    return None


async def cache_set(redis_client: redis.Redis, key: str, data: Any, ttl: int = CACHE_TTL):
    """Set data in cache"""
    try:
        await redis_client.setex(
            f"revenue:{key}",
            ttl,
            json.dumps(data, default=str)
        )
    except Exception as e:
        logger.warning(f"Cache set error: {e}")


async def lago_api_call(client: httpx.AsyncClient, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """
    Make API call to Lago

    Args:
        client: HTTP client
        endpoint: API endpoint (e.g., /api/v1/customers)
        method: HTTP method
        data: Request body for POST/PUT

    Returns:
        API response data
    """
    if not LAGO_API_KEY:
        raise HTTPException(status_code=500, detail="Lago API key not configured")

    url = f"{LAGO_API_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {LAGO_API_KEY}"}

    try:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Lago API error ({e.response.status_code}): {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Lago API error: {e.response.text}")
    except Exception as e:
        logger.error(f"Lago API request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Lago API: {str(e)}")


async def calculate_mrr(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Calculate Monthly Recurring Revenue using Lago API"""
    try:
        # Get active subscriptions
        subscriptions_data = await lago_api_call(client, "/api/v1/subscriptions?status=active")
        subscriptions = subscriptions_data.get("subscriptions", [])

        # Get plans
        plans_data = await lago_api_call(client, "/api/v1/plans")
        plans_list = plans_data.get("plans", [])

        # Create plan lookup
        plans_by_id = {plan["lago_id"]: plan for plan in plans_list}

        mrr = 0.0
        active_subscriptions = len(subscriptions)
        customer_ids = set()

        for sub in subscriptions:
            customer_ids.add(sub.get("customer_id"))
            plan_id = sub.get("plan_code")

            # Find plan by code
            plan = None
            for p in plans_list:
                if p.get("code") == plan_id:
                    plan = p
                    break

            if plan:
                amount_cents = plan.get("amount_cents", 0)
                interval = plan.get("interval", "monthly")

                if interval == "monthly":
                    mrr += amount_cents / 100.0
                elif interval == "yearly":
                    mrr += (amount_cents / 100.0) / 12.0
                elif interval == "weekly":
                    mrr += (amount_cents / 100.0) * 4.33

        total_customers = len(customer_ids)
        arr = mrr * 12
        arpu = mrr / total_customers if total_customers > 0 else 0

        return {
            "mrr": mrr,
            "arr": arr,
            "active_subscriptions": active_subscriptions,
            "total_customers": total_customers,
            "arpu": arpu
        }
    except Exception as e:
        logger.error(f"Error calculating MRR: {e}")
        # Return default values on error
        return {
            "mrr": 0.0,
            "arr": 0.0,
            "active_subscriptions": 0,
            "total_customers": 0,
            "arpu": 0.0
        }


async def calculate_growth_rate(client: httpx.AsyncClient) -> float:
    """Calculate month-over-month growth rate using Lago API"""
    try:
        # Get invoices for last 2 months
        invoices_data = await lago_api_call(client, "/api/v1/invoices")
        invoices = invoices_data.get("invoices", [])

        # Group by month
        from collections import defaultdict
        monthly_revenue = defaultdict(float)

        for invoice in invoices:
            if invoice.get("status") in ["finalized", "succeeded"]:
                created_at = datetime.fromisoformat(invoice["issuing_date"].replace("Z", "+00:00"))
                month_key = created_at.strftime("%Y-%m")
                amount_cents = invoice.get("amount_cents", 0)
                monthly_revenue[month_key] += amount_cents / 100.0

        # Get last 2 months
        sorted_months = sorted(monthly_revenue.keys(), reverse=True)[:2]

        if len(sorted_months) < 2:
            return 0.0

        current_month_revenue = monthly_revenue[sorted_months[0]]
        previous_month_revenue = monthly_revenue[sorted_months[1]]

        if previous_month_revenue == 0:
            return 0.0

        growth_rate = ((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100
        return float(growth_rate)

    except Exception as e:
        logger.error(f"Error calculating growth rate: {e}")
        return 0.0


async def calculate_churn_rate(client: httpx.AsyncClient) -> float:
    """Calculate monthly churn rate using Lago API"""
    try:
        # Get all subscriptions
        all_subs_data = await lago_api_call(client, "/api/v1/subscriptions")
        all_subscriptions = all_subs_data.get("subscriptions", [])

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        churned = 0
        total = 0

        for sub in all_subscriptions:
            status = sub.get("status")

            # Count churned subscriptions in last 30 days
            if status == "terminated" and sub.get("terminated_at"):
                terminated_at = datetime.fromisoformat(sub["terminated_at"].replace("Z", "+00:00"))
                if terminated_at >= thirty_days_ago:
                    churned += 1
                    total += 1

            # Count active subscriptions
            elif status == "active":
                total += 1

        if total == 0:
            return 0.0

        churn_rate = (churned / total) * 100
        return float(churn_rate)

    except Exception as e:
        logger.error(f"Error calculating churn rate: {e}")
        return 0.0


async def get_revenue_trends(client: httpx.AsyncClient, period: str = "monthly", days: int = 365) -> List[Dict[str, Any]]:
    """Get historical revenue trends using Lago API"""
    try:
        from collections import defaultdict
        from datetime import timedelta

        # Get invoices
        invoices_data = await lago_api_call(client, "/api/v1/invoices")
        invoices = invoices_data.get("invoices", [])

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        period_data = defaultdict(lambda: {"revenue": 0.0, "customers": set()})

        for invoice in invoices:
            if invoice.get("status") not in ["finalized", "succeeded"]:
                continue

            issued_date = datetime.fromisoformat(invoice["issuing_date"].replace("Z", "+00:00"))
            if issued_date < cutoff_date:
                continue

            # Group by period
            if period == "daily":
                period_key = issued_date.strftime("%Y-%m-%d")
            elif period == "weekly":
                # Get Monday of the week
                monday = issued_date - timedelta(days=issued_date.weekday())
                period_key = monday.strftime("%Y-%m-%d")
            else:  # monthly
                period_key = issued_date.strftime("%Y-%m")

            amount_cents = invoice.get("amount_cents", 0)
            customer_id = invoice.get("customer", {}).get("lago_id")

            period_data[period_key]["revenue"] += amount_cents / 100.0
            if customer_id:
                period_data[period_key]["customers"].add(customer_id)

        # Convert to list format
        trends = []
        for date_key in sorted(period_data.keys()):
            trends.append({
                "date": date_key,
                "revenue": float(period_data[date_key]["revenue"]),
                "customers": len(period_data[date_key]["customers"])
            })

        return trends

    except Exception as e:
        logger.error(f"Error getting revenue trends: {e}")
        return []


async def get_revenue_by_plan(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Get revenue breakdown by subscription plan using Lago API"""
    try:
        from collections import defaultdict

        # Get active subscriptions
        subscriptions_data = await lago_api_call(client, "/api/v1/subscriptions?status=active")
        subscriptions = subscriptions_data.get("subscriptions", [])

        # Get plans
        plans_data = await lago_api_call(client, "/api/v1/plans")
        plans_list = plans_data.get("plans", [])

        # Create plan lookup
        plans_by_code = {plan["code"]: plan for plan in plans_list}

        # Group by plan
        plan_metrics = defaultdict(lambda: {"mrr": 0.0, "count": 0})

        for sub in subscriptions:
            plan_code = sub.get("plan_code")
            if plan_code and plan_code in plans_by_code:
                plan = plans_by_code[plan_code]
                amount_cents = plan.get("amount_cents", 0)
                interval = plan.get("interval", "monthly")

                # Calculate MRR contribution
                if interval == "monthly":
                    mrr = amount_cents / 100.0
                elif interval == "yearly":
                    mrr = (amount_cents / 100.0) / 12.0
                elif interval == "weekly":
                    mrr = (amount_cents / 100.0) * 4.33
                else:
                    mrr = 0.0

                plan_metrics[plan_code]["mrr"] += mrr
                plan_metrics[plan_code]["count"] += 1

        # Calculate total MRR
        total_mrr = sum(metrics["mrr"] for metrics in plan_metrics.values())

        # Build response
        plan_data = []
        for plan_code, metrics in plan_metrics.items():
            plan = plans_by_code.get(plan_code, {})
            mrr = metrics["mrr"]
            count = metrics["count"]

            plan_data.append({
                "plan_code": plan_code,
                "plan_name": plan.get("name", plan_code),
                "mrr": mrr,
                "subscriber_count": count,
                "percentage": (mrr / total_mrr * 100) if total_mrr > 0 else 0,
                "average_revenue_per_subscriber": mrr / count if count > 0 else 0
            })

        # Sort by MRR descending
        plan_data.sort(key=lambda x: x["mrr"], reverse=True)

        return plan_data

    except Exception as e:
        logger.error(f"Error getting revenue by plan: {e}")
        return []


async def forecast_revenue(client: httpx.AsyncClient, months: int) -> Dict[str, float]:
    """Forecast revenue using linear regression with Lago API data"""
    try:
        from collections import defaultdict

        # Get historical invoices (last 12 months)
        invoices_data = await lago_api_call(client, "/api/v1/invoices")
        invoices = invoices_data.get("invoices", [])

        cutoff_date = datetime.utcnow() - timedelta(days=365)
        monthly_revenue = defaultdict(float)

        for invoice in invoices:
            if invoice.get("status") not in ["finalized", "succeeded"]:
                continue

            issued_date = datetime.fromisoformat(invoice["issuing_date"].replace("Z", "+00:00"))
            if issued_date < cutoff_date:
                continue

            month_key = issued_date.strftime("%Y-%m")
            amount_cents = invoice.get("amount_cents", 0)
            monthly_revenue[month_key] += amount_cents / 100.0

        if len(monthly_revenue) < 3:
            # Not enough data for forecasting
            return {
                "forecast": 0.0,
                "confidence_low": 0.0,
                "confidence_high": 0.0,
                "accuracy": 0.0
            }

        # Prepare data for linear regression
        sorted_months = sorted(monthly_revenue.keys())
        x = np.array(list(range(len(sorted_months))))
        y = np.array([monthly_revenue[month] for month in sorted_months])

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Calculate forecast
        forecast_x = len(sorted_months) - 1 + months
        forecast = slope * forecast_x + intercept

        # Calculate confidence interval (95%)
        confidence_interval = 1.96 * std_err * np.sqrt(
            1 + 1/len(x) + (forecast_x - np.mean(x))**2 / np.sum((x - np.mean(x))**2)
        )

        return {
            "forecast": max(0.0, float(forecast)),
            "confidence_low": max(0.0, float(forecast - confidence_interval)),
            "confidence_high": max(0.0, float(forecast + confidence_interval)),
            "accuracy": float(r_value ** 2)  # R-squared
        }

    except Exception as e:
        logger.error(f"Error forecasting revenue: {e}")
        return {
            "forecast": 0.0,
            "confidence_low": 0.0,
            "confidence_high": 0.0,
            "accuracy": 0.0
        }


async def calculate_churn_impact(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Calculate churn impact on revenue using Lago API"""
    try:
        # Get subscriptions
        subscriptions_data = await lago_api_call(client, "/api/v1/subscriptions")
        subscriptions = subscriptions_data.get("subscriptions", [])

        # Get plans
        plans_data = await lago_api_call(client, "/api/v1/plans")
        plans_list = plans_data.get("plans", [])
        plans_by_code = {plan["code"]: plan for plan in plans_list}

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        churned_mrr = 0.0
        churned_count = 0
        total_subs = 0

        for sub in subscriptions:
            status = sub.get("status")
            plan_code = sub.get("plan_code")

            # Count churned subscriptions in last 30 days
            if status == "terminated" and sub.get("terminated_at"):
                terminated_at = datetime.fromisoformat(sub["terminated_at"].replace("Z", "+00:00"))
                if terminated_at >= thirty_days_ago:
                    churned_count += 1
                    total_subs += 1

                    # Calculate churned MRR
                    if plan_code and plan_code in plans_by_code:
                        plan = plans_by_code[plan_code]
                        amount_cents = plan.get("amount_cents", 0)
                        interval = plan.get("interval", "monthly")

                        if interval == "monthly":
                            churned_mrr += amount_cents / 100.0
                        elif interval == "yearly":
                            churned_mrr += (amount_cents / 100.0) / 12.0
                        elif interval == "weekly":
                            churned_mrr += (amount_cents / 100.0) * 4.33

            # Count active subscriptions
            elif status == "active":
                total_subs += 1

        churn_rate = (churned_count / total_subs * 100) if total_subs > 0 else 0
        revenue_impact = churned_mrr * 12

        return {
            "churned_mrr": churned_mrr,
            "churned_subscribers": churned_count,
            "churn_rate": churn_rate,
            "revenue_impact": revenue_impact,
            "period": "last_30_days"
        }

    except Exception as e:
        logger.error(f"Error calculating churn impact: {e}")
        return {
            "churned_mrr": 0.0,
            "churned_subscribers": 0,
            "churn_rate": 0.0,
            "revenue_impact": 0.0,
            "period": "last_30_days"
        }


async def calculate_lifetime_value(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Calculate customer lifetime value using Lago API"""
    try:
        # Get subscriptions
        subscriptions_data = await lago_api_call(client, "/api/v1/subscriptions")
        subscriptions = subscriptions_data.get("subscriptions", [])

        # Get plans
        plans_data = await lago_api_call(client, "/api/v1/plans")
        plans_list = plans_data.get("plans", [])
        plans_by_code = {plan["code"]: plan for plan in plans_list}

        # Calculate average lifetime
        total_lifetime_months = 0
        lifetime_count = 0
        plan_mrr = {}

        for sub in subscriptions:
            status = sub.get("status")
            created_at = datetime.fromisoformat(sub["created_at"].replace("Z", "+00:00"))

            # Calculate lifetime
            if status == "terminated" and sub.get("terminated_at"):
                terminated_at = datetime.fromisoformat(sub["terminated_at"].replace("Z", "+00:00"))
            else:
                terminated_at = datetime.utcnow()

            lifetime_months = (terminated_at - created_at).days / 30.44
            total_lifetime_months += lifetime_months
            lifetime_count += 1

            # Calculate MRR by plan
            if status == "active":
                plan_code = sub.get("plan_code")
                if plan_code and plan_code in plans_by_code:
                    plan = plans_by_code[plan_code]
                    amount_cents = plan.get("amount_cents", 0)
                    interval = plan.get("interval", "monthly")

                    if interval == "monthly":
                        mrr = amount_cents / 100.0
                    elif interval == "yearly":
                        mrr = (amount_cents / 100.0) / 12.0
                    elif interval == "weekly":
                        mrr = (amount_cents / 100.0) * 4.33
                    else:
                        mrr = 0.0

                    if plan_code not in plan_mrr:
                        plan_mrr[plan_code] = {"total_mrr": 0.0, "count": 0}
                    plan_mrr[plan_code]["total_mrr"] += mrr
                    plan_mrr[plan_code]["count"] += 1

        avg_lifetime_months = total_lifetime_months / lifetime_count if lifetime_count > 0 else 0

        # Calculate LTV by plan
        ltv_by_plan = {}
        total_ltv = 0.0
        plan_count = 0

        for plan_code, metrics in plan_mrr.items():
            avg_mrr = metrics["total_mrr"] / metrics["count"] if metrics["count"] > 0 else 0
            ltv = avg_mrr * avg_lifetime_months
            ltv_by_plan[plan_code] = ltv
            total_ltv += ltv
            plan_count += 1

        avg_ltv = total_ltv / plan_count if plan_count > 0 else 0

        return {
            "average_ltv": avg_ltv,
            "ltv_by_plan": ltv_by_plan,
            "average_customer_lifetime_months": avg_lifetime_months,
            "ltv_to_cac_ratio": None  # CAC data not available
        }

    except Exception as e:
        logger.error(f"Error calculating LTV: {e}")
        return {
            "average_ltv": 0.0,
            "ltv_by_plan": {},
            "average_customer_lifetime_months": 0.0,
            "ltv_to_cac_ratio": None
        }


async def get_cohort_revenue(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Get revenue by customer cohort using Lago API"""
    try:
        from collections import defaultdict

        # Get customers
        customers_data = await lago_api_call(client, "/api/v1/customers")
        customers = customers_data.get("customers", [])

        # Get invoices
        invoices_data = await lago_api_call(client, "/api/v1/invoices")
        invoices = invoices_data.get("invoices", [])

        # Get subscriptions
        subscriptions_data = await lago_api_call(client, "/api/v1/subscriptions")
        subscriptions = subscriptions_data.get("subscriptions", [])

        # Group customers by cohort
        customer_cohorts = {}
        for customer in customers:
            customer_id = customer.get("lago_id")
            created_at = datetime.fromisoformat(customer["created_at"].replace("Z", "+00:00"))
            cohort_month = created_at.strftime("%Y-%m")
            customer_cohorts[customer_id] = cohort_month

        # Calculate cohort metrics
        cohort_metrics = defaultdict(lambda: {
            "customer_count": set(),
            "total_revenue": 0.0,
            "active_customers": set()
        })

        # Add revenue from invoices
        for invoice in invoices:
            if invoice.get("status") not in ["finalized", "succeeded"]:
                continue

            customer_id = invoice.get("customer", {}).get("lago_id")
            if customer_id and customer_id in customer_cohorts:
                cohort = customer_cohorts[customer_id]
                amount_cents = invoice.get("amount_cents", 0)
                cohort_metrics[cohort]["total_revenue"] += amount_cents / 100.0
                cohort_metrics[cohort]["customer_count"].add(customer_id)

        # Add active customers
        for sub in subscriptions:
            if sub.get("status") == "active":
                customer_id = sub.get("customer", {}).get("lago_id")
                if customer_id and customer_id in customer_cohorts:
                    cohort = customer_cohorts[customer_id]
                    cohort_metrics[cohort]["active_customers"].add(customer_id)

        # Build response
        cohorts = []
        sorted_cohorts = sorted(cohort_metrics.keys(), reverse=True)[:12]

        for cohort in sorted_cohorts:
            metrics = cohort_metrics[cohort]
            customer_count = len(metrics["customer_count"])
            total_revenue = metrics["total_revenue"]
            retention_rate = (len(metrics["active_customers"]) / customer_count * 100) if customer_count > 0 else 0

            cohorts.append({
                "cohort": cohort,
                "customer_count": customer_count,
                "total_revenue": total_revenue,
                "average_revenue_per_customer": total_revenue / customer_count if customer_count > 0 else 0,
                "retention_rate": retention_rate
            })

        return cohorts

    except Exception as e:
        logger.error(f"Error getting cohort revenue: {e}")
        return []


# API Endpoints
@router.get("/overview", response_model=RevenueOverview)
async def get_revenue_overview(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get revenue overview including MRR, ARR, and key metrics
    """
    try:
        # Check cache
        cached = await cache_get(redis_client, "overview")
        if cached:
            logger.info("Returning cached revenue overview")
            return RevenueOverview(**cached)

        # Calculate metrics using Lago API
        mrr_data = await calculate_mrr(client)
        growth_rate = await calculate_growth_rate(client)
        churn_rate = await calculate_churn_rate(client)

        overview = RevenueOverview(
            mrr=mrr_data["mrr"],
            arr=mrr_data["arr"],
            growth_rate=growth_rate,
            churn_rate=churn_rate,
            active_subscriptions=mrr_data["active_subscriptions"],
            total_customers=mrr_data["total_customers"],
            average_revenue_per_user=mrr_data["arpu"]
        )

        # Cache result
        await cache_set(redis_client, "overview", overview.dict())

        logger.info(f"Revenue overview: MRR=${overview.mrr:.2f}, ARR=${overview.arr:.2f}")
        return overview

    except Exception as e:
        logger.error(f"Error getting revenue overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    period: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    days: int = Query(365, ge=30, le=730),
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get historical revenue trends

    Args:
        period: Time period aggregation (daily, weekly, monthly)
        days: Number of days to look back (30-730)
    """
    try:
        cache_key = f"trends:{period}:{days}"
        cached = await cache_get(redis_client, cache_key)
        if cached:
            logger.info(f"Returning cached revenue trends: {period}")
            return cached

        trends = await get_revenue_trends(client, period, days)

        total_revenue = sum(t["revenue"] for t in trends)
        average_revenue = total_revenue / len(trends) if trends else 0

        result = {
            "period": period,
            "data": trends,
            "total_revenue": total_revenue,
            "average_revenue": average_revenue
        }

        await cache_set(redis_client, cache_key, result)

        logger.info(f"Revenue trends: {len(trends)} periods, total=${total_revenue:.2f}")
        return result

    except Exception as e:
        logger.error(f"Error getting revenue trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-plan", response_model=List[RevenueByPlan])
async def get_revenue_by_plan_endpoint(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get revenue breakdown by subscription plan
    """
    try:
        cached = await cache_get(redis_client, "by_plan")
        if cached:
            logger.info("Returning cached revenue by plan")
            return [RevenueByPlan(**item) for item in cached]

        plan_data = await get_revenue_by_plan(client)

        result = [RevenueByPlan(**item) for item in plan_data]

        await cache_set(redis_client, "by_plan", [item.dict() for item in result])

        logger.info(f"Revenue by plan: {len(result)} plans")
        return result

    except Exception as e:
        logger.error(f"Error getting revenue by plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecasts", response_model=RevenueForecast)
async def get_revenue_forecasts(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get revenue forecasts for 3, 6, and 12 months
    """
    try:
        cached = await cache_get(redis_client, "forecasts")
        if cached:
            logger.info("Returning cached revenue forecasts")
            return RevenueForecast(**cached)

        forecast_3m = await forecast_revenue(client, 3)
        forecast_6m = await forecast_revenue(client, 6)
        forecast_12m = await forecast_revenue(client, 12)

        result = RevenueForecast(
            forecast_3_months=forecast_3m["forecast"],
            forecast_6_months=forecast_6m["forecast"],
            forecast_12_months=forecast_12m["forecast"],
            confidence_interval_low=forecast_3m["confidence_low"],
            confidence_interval_high=forecast_12m["confidence_high"],
            accuracy_score=forecast_6m["accuracy"]
        )

        await cache_set(redis_client, "forecasts", result.dict())

        logger.info(f"Revenue forecasts: 3m=${result.forecast_3_months:.2f}, 12m=${result.forecast_12_months:.2f}")
        return result

    except Exception as e:
        logger.error(f"Error getting revenue forecasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/churn-impact", response_model=ChurnImpact)
async def get_churn_impact_endpoint(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get churn impact on revenue
    """
    try:
        cached = await cache_get(redis_client, "churn_impact")
        if cached:
            logger.info("Returning cached churn impact")
            return ChurnImpact(**cached)

        impact = await calculate_churn_impact(client)

        result = ChurnImpact(**impact)

        await cache_set(redis_client, "churn_impact", result.dict())

        logger.info(f"Churn impact: ${result.churned_mrr:.2f} MRR, {result.churned_subscribers} subscribers")
        return result

    except Exception as e:
        logger.error(f"Error getting churn impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ltv", response_model=LifetimeValue)
async def get_lifetime_value_endpoint(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get customer lifetime value metrics
    """
    try:
        cached = await cache_get(redis_client, "ltv")
        if cached:
            logger.info("Returning cached LTV")
            return LifetimeValue(**cached)

        ltv = await calculate_lifetime_value(client)

        result = LifetimeValue(**ltv)

        await cache_set(redis_client, "ltv", result.dict())

        logger.info(f"LTV: avg=${result.average_ltv:.2f}, lifetime={result.average_customer_lifetime_months:.1f} months")
        return result

    except Exception as e:
        logger.error(f"Error getting LTV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohorts/revenue", response_model=List[CohortRevenue])
async def get_cohort_revenue_endpoint(
    client: httpx.AsyncClient = Depends(get_http_client),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get revenue by customer cohort
    """
    try:
        cached = await cache_get(redis_client, "cohorts")
        if cached:
            logger.info("Returning cached cohort revenue")
            return [CohortRevenue(**item) for item in cached]

        cohorts = await get_cohort_revenue(client)

        result = [CohortRevenue(**item) for item in cohorts]

        await cache_set(redis_client, "cohorts", [item.dict() for item in result])

        logger.info(f"Cohort revenue: {len(result)} cohorts")
        return result

    except Exception as e:
        logger.error(f"Error getting cohort revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "revenue_analytics",
        "timestamp": datetime.utcnow().isoformat()
    }
