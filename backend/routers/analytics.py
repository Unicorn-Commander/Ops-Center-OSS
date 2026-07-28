"""
Analytics API Router - Supplementary Endpoints
Provides additional analytics endpoints that complement existing analytics routers.

This router adds endpoints requested specifically with these paths:
- /api/v1/analytics/revenue/mrr
- /api/v1/analytics/revenue/arr
- /api/v1/analytics/revenue/growth
- /api/v1/analytics/revenue/by-tier (alias for /by-plan)
- /api/v1/analytics/users/ltv (alias for existing /ltv)
- /api/v1/analytics/users/churn
- /api/v1/analytics/users/acquisition
- /api/v1/analytics/services/*
- /api/v1/analytics/metrics/*

Existing analytics routers:
- revenue_analytics.py: /api/v1/analytics/revenue/*
- user_analytics.py: /api/v1/analytics/users/*
- usage_analytics.py: /api/v1/analytics/usage/*

DATA SOURCES (real, DB-backed — same definitions as the Revenue Dashboard):
- Revenue: organization_subscriptions.monthly_price — identical to
  /api/v1/billing/analytics/dashboard (billing_analytics_api.py):
  MRR = SUM(COALESCE(monthly_price,0)) of status='active' rows, ARR = MRR*12.
  Historical months are reconstructed from created_at / canceled_at
  (falling back to updated_at for canceled rows, like churn/analysis does).
- Users: organization_members.joined_at histograms (first join per user_id).
  The headline user total prefers the same Keycloak user list that
  /api/v1/admin/users/analytics/summary counts (cached ~5 min); when Keycloak
  is unreachable it falls back to the distinct org-member count and says so
  in a "basis" field.
- Services uptime/latency/errors/performance/alerts: monitored_websites +
  website_checks (routers/website_monitor.py scheduler output).
- Services popularity/adoption: api_usage (migrations/usage_tracking_schema.sql).
- API-call volume: credit_transactions rows with transaction_type='usage'
  (the same table /api/v1/billing/analytics/usage/summary aggregates).

HONESTY CONTRACT: these endpoints once returned randomly generated mock data
— never regress to that. Every payload keeps its exact legacy JSON shape
(same keys) and carries "no_data": it is false only when the value(s) came
from real rows; when a source table is empty/missing or the DB is down the
endpoint fail-softs to the zeroed shape with "no_data": true (the same
pattern usage_tracking_api.py uses) instead of erroring or inventing numbers.
Metrics that still have no backing source (LTV/CAC, cloud costs, forecasts,
signup channels, retention tracking) STAY zeroed with a note — no fabrication.

A few list/alias keys consumed by src/pages/AdvancedAnalytics.jsx are filled
in addition to the legacy keys (documented per-endpoint below); aliases only
ever duplicate real values already present in the payload.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query

# Shared asyncpg pool (same pattern as billing_analytics_api.py / routers/billing_events.py)
from database.connection import get_db_pool

# Admin gate — matches sibling revenue endpoints (billing_analytics_api.py and
# the /api/v1/llm/* handlers in routers/metering.py). The default-deny auth
# middleware already requires a session; this additionally requires admin,
# because these payloads now contain real revenue/customer data.
from auth_dependencies import require_admin_user

logger = logging.getLogger(__name__)

# Create sub-routers for different analytics categories
revenue_router = APIRouter(prefix="/api/v1/analytics/revenue", tags=["Analytics - Revenue"])
users_router = APIRouter(prefix="/api/v1/analytics/users", tags=["Analytics - Users"])
services_router = APIRouter(prefix="/api/v1/analytics/services", tags=["Analytics - Services"])
metrics_router = APIRouter(prefix="/api/v1/analytics/metrics", tags=["Analytics - Metrics"])
performance_router = APIRouter(prefix="/api/v1/analytics/performance", tags=["Analytics - Performance"])
main_router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics - Main"])


# ============================================================================
# SHARED QUERY HELPERS
# ============================================================================

# Fixed tier keys that several legacy payload shapes require. Real
# subscription_plan values only land in these buckets when the names match;
# unmatched plans are still counted in the totals (never invented into a bucket).
FIXED_TIER_KEYS = ("trial", "starter", "professional", "enterprise")


def _f(value: Any, digits: int = 2) -> float:
    """Coerce asyncpg Decimal/None to a rounded float."""
    return round(float(value or 0), digits)


async def _subscription_month_series(conn, months: int) -> List[Dict[str, Any]]:
    """
    Reconstruct per-month recurring-revenue state from organization_subscriptions.

    A subscription counts toward a month when it was created before the month's
    end and either is still active or was canceled after the month's end
    (COALESCE(canceled_at, updated_at), matching billing_analytics churn logic).
    The current month therefore equals the dashboard MRR exactly.
    """
    rows = await conn.fetch(
        """
        WITH months AS (
            SELECT date_trunc('month', NOW()) - (INTERVAL '1 month' * gs) AS month_start
            FROM generate_series(0, $1 - 1) AS gs
        )
        SELECT
            to_char(m.month_start, 'YYYY-MM') AS month,
            COALESCE(SUM(s.monthly_price) FILTER (
                WHERE s.created_at < m.month_start + INTERVAL '1 month'
                  AND (s.status = 'active'
                       OR (s.status IN ('canceled', 'expired')
                           AND COALESCE(s.canceled_at, s.updated_at) >= m.month_start + INTERVAL '1 month'))
            ), 0) AS mrr,
            COALESCE(COUNT(s.id) FILTER (
                WHERE s.created_at < m.month_start + INTERVAL '1 month'
                  AND (s.status = 'active'
                       OR (s.status IN ('canceled', 'expired')
                           AND COALESCE(s.canceled_at, s.updated_at) >= m.month_start + INTERVAL '1 month'))
            ), 0) AS active_subscriptions,
            COALESCE(SUM(s.monthly_price) FILTER (
                WHERE s.created_at >= m.month_start
                  AND s.created_at < m.month_start + INTERVAL '1 month'
            ), 0) AS new_mrr,
            COALESCE(COUNT(s.id) FILTER (
                WHERE s.status IN ('canceled', 'expired')
                  AND COALESCE(s.canceled_at, s.updated_at) >= m.month_start
                  AND COALESCE(s.canceled_at, s.updated_at) < m.month_start + INTERVAL '1 month'
            ), 0) AS churned_count,
            COALESCE(SUM(s.monthly_price) FILTER (
                WHERE s.status IN ('canceled', 'expired')
                  AND COALESCE(s.canceled_at, s.updated_at) >= m.month_start
                  AND COALESCE(s.canceled_at, s.updated_at) < m.month_start + INTERVAL '1 month'
            ), 0) AS churned_mrr
        FROM months m
        LEFT JOIN organization_subscriptions s ON TRUE
        GROUP BY m.month_start
        ORDER BY m.month_start
        """,
        months,
    )
    return [
        {
            "month": r["month"],
            "mrr": _f(r["mrr"]),
            "active_subscriptions": int(r["active_subscriptions"] or 0),
            "new_mrr": _f(r["new_mrr"]),
            "churned_count": int(r["churned_count"] or 0),
            "churned_mrr": _f(r["churned_mrr"]),
        }
        for r in rows
    ]


async def _has_subscription_rows(conn) -> bool:
    return bool(await conn.fetchval("SELECT EXISTS (SELECT 1 FROM organization_subscriptions)"))


async def _dashboard_core(conn) -> Dict[str, Any]:
    """
    Same headline numbers as /api/v1/billing/analytics/dashboard
    (billing_analytics_api.get_billing_dashboard, 30-day window).
    """
    mrr = _f(await conn.fetchval(
        "SELECT SUM(COALESCE(monthly_price, 0)) FROM organization_subscriptions WHERE status = 'active'"
    ))
    total_orgs = int(await conn.fetchval(
        "SELECT COUNT(DISTINCT org_id) FROM organization_subscriptions WHERE status = 'active'"
    ) or 0)

    prev_subs = int(await conn.fetchval(
        """
        SELECT COUNT(DISTINCT org_id) FROM organization_subscriptions
        WHERE created_at >= NOW() - INTERVAL '60 days' AND created_at < NOW() - INTERVAL '30 days'
        """
    ) or 0)
    current_subs = int(await conn.fetchval(
        """
        SELECT COUNT(DISTINCT org_id) FROM organization_subscriptions
        WHERE created_at >= NOW() - INTERVAL '30 days'
        """
    ) or 0)
    growth_rate = _f(((current_subs - prev_subs) / prev_subs) * 100) if prev_subs > 0 else 0.0

    churned_orgs = int(await conn.fetchval(
        """
        SELECT COUNT(DISTINCT org_id) FROM organization_subscriptions
        WHERE status IN ('canceled', 'expired') AND updated_at >= NOW() - INTERVAL '30 days'
        """
    ) or 0)
    churn_rate = _f(churned_orgs / total_orgs * 100) if total_orgs > 0 else 0.0

    return {
        "mrr": mrr,
        "arr": _f(mrr * 12),
        "total_active_orgs": total_orgs,
        "arpu": _f(mrr / total_orgs) if total_orgs > 0 else 0.0,
        "growth_rate": growth_rate,
        "churn_rate": churn_rate,
        "churned_orgs_30d": churned_orgs,
    }


async def _plan_breakdown(conn) -> List[Dict[str, Any]]:
    """Active MRR grouped by subscription_plan (real plan names, no remapping)."""
    rows = await conn.fetch(
        """
        SELECT s.subscription_plan AS plan,
               COALESCE(SUM(s.monthly_price), 0) AS mrr,
               COUNT(DISTINCT s.org_id) AS customers
        FROM organization_subscriptions s
        WHERE s.status = 'active'
        GROUP BY s.subscription_plan
        ORDER BY mrr DESC
        """
    )
    return [
        {"plan": r["plan"], "mrr": _f(r["mrr"]), "customers": int(r["customers"] or 0)}
        for r in rows
    ]


async def _subscription_month_counts(conn) -> Dict[str, int]:
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE created_at >= date_trunc('month', NOW())) AS new_this_month,
            COUNT(*) FILTER (
                WHERE status IN ('canceled', 'expired')
                  AND COALESCE(canceled_at, updated_at) >= date_trunc('month', NOW())
            ) AS cancelled_this_month
        FROM organization_subscriptions
        """
    )
    return {
        "new_this_month": int(row["new_this_month"] or 0),
        "cancelled_this_month": int(row["cancelled_this_month"] or 0),
    }


async def _member_month_series(conn, months: int) -> List[Dict[str, Any]]:
    """New/cumulative distinct users per month from organization_members first-join."""
    rows = await conn.fetch(
        """
        WITH months AS (
            SELECT date_trunc('month', NOW()) - (INTERVAL '1 month' * gs) AS month_start
            FROM generate_series(0, $1 - 1) AS gs
        ),
        firsts AS (
            SELECT user_id, MIN(joined_at) AS first_joined
            FROM organization_members
            GROUP BY user_id
        )
        SELECT
            to_char(m.month_start, 'YYYY-MM') AS month,
            COALESCE(COUNT(f.user_id) FILTER (
                WHERE f.first_joined >= m.month_start
                  AND f.first_joined < m.month_start + INTERVAL '1 month'
            ), 0) AS new_users,
            COALESCE(COUNT(f.user_id) FILTER (
                WHERE f.first_joined < m.month_start + INTERVAL '1 month'
            ), 0) AS total_users
        FROM months m
        LEFT JOIN firsts f ON TRUE
        GROUP BY m.month_start
        ORDER BY m.month_start
        """,
        months,
    )
    return [
        {
            "month": r["month"],
            "new_users": int(r["new_users"] or 0),
            "total_users": int(r["total_users"] or 0),
        }
        for r in rows
    ]


async def _distinct_member_count(conn) -> int:
    return int(await conn.fetchval(
        "SELECT COUNT(DISTINCT user_id) FROM organization_members"
    ) or 0)


# Keycloak user counts — the same list /api/v1/admin/users/analytics/summary
# counts (keycloak_integration.get_all_users). Cached briefly so dashboard
# fan-out doesn't hammer Keycloak.
_KC_COUNT_CACHE: Dict[str, Any] = {"ts": 0.0, "total": None, "active": None}
_KC_COUNT_TTL_SECONDS = 300


async def _keycloak_user_counts() -> Tuple[Optional[int], Optional[int]]:
    """Return (total_users, active_users) from Keycloak, or (None, None) if unavailable."""
    now = time.time()
    if _KC_COUNT_CACHE["total"] is not None and (now - _KC_COUNT_CACHE["ts"]) < _KC_COUNT_TTL_SECONDS:
        return _KC_COUNT_CACHE["total"], _KC_COUNT_CACHE["active"]
    try:
        from keycloak_integration import get_all_users  # lazy: heavy httpx module
        users = await get_all_users()
        if users:
            total = len(users)
            active = sum(1 for u in users if u.get("enabled", True))
            _KC_COUNT_CACHE.update({"ts": now, "total": total, "active": active})
            return total, active
    except Exception as e:  # noqa: BLE001 - availability probe, never fatal
        logger.debug("Keycloak user count unavailable for analytics: %s", e)
    return None, None


async def _user_headline_counts(conn) -> Tuple[int, int, str]:
    """(total, active, basis) — Keycloak preferred, org-members fallback."""
    kc_total, kc_active = await _keycloak_user_counts()
    if kc_total is not None:
        return kc_total, int(kc_active or 0), "keycloak_users"
    member_count = await _distinct_member_count(conn)
    return member_count, member_count, "organization_members_distinct"


async def _site_window_stats(conn, hours: int) -> List[Dict[str, Any]]:
    """Per-site uptime/latency/error aggregates from website_checks over a window."""
    rows = await conn.fetch(
        """
        SELECT w.name,
               COUNT(c.id) AS total_checks,
               COUNT(c.id) FILTER (WHERE c.status = 'up') AS up_checks,
               COUNT(c.id) FILTER (WHERE c.status = 'down') AS down_checks,
               COALESCE(AVG(c.response_time_ms), 0) AS avg_ms,
               (ARRAY_AGG(c.status ORDER BY c.checked_at DESC))[1] AS last_status,
               (ARRAY_AGG(c.error ORDER BY c.checked_at DESC) FILTER (WHERE c.error IS NOT NULL))[1] AS last_error,
               MAX(c.checked_at) AS last_check
        FROM monitored_websites w
        JOIN website_checks c ON c.website_id = w.id
        WHERE w.is_active = TRUE
          AND c.checked_at > NOW() - make_interval(hours => $1)
        GROUP BY w.name
        ORDER BY w.name
        """,
        hours,
    )
    out = []
    for r in rows:
        total = int(r["total_checks"] or 0)
        up = int(r["up_checks"] or 0)
        out.append({
            "name": r["name"],
            "total_checks": total,
            "up_checks": up,
            "down_checks": int(r["down_checks"] or 0),
            "uptime_percent": _f(up / total * 100) if total > 0 else 0.0,
            "avg_ms": _f(r["avg_ms"], 1),
            "last_status": r["last_status"],
            "last_error": r["last_error"],
            "last_check": r["last_check"].isoformat() if r["last_check"] else None,
        })
    return out


async def _usage_by_service(conn, days: int = 30) -> List[Dict[str, Any]]:
    """Call counts per service path prefix from api_usage (usage_tracking_schema.sql)."""
    rows = await conn.fetch(
        """
        SELECT COALESCE(substring(a.endpoint FROM '^(/api/v1/[^/?]+)'),
                        split_part(a.endpoint, '?', 1)) AS service_path,
               COUNT(*) AS total_calls,
               COUNT(DISTINCT a.user_id) AS unique_users,
               COALESCE(AVG(a.request_duration_ms), 0) AS avg_ms,
               COUNT(*) FILTER (WHERE a.response_status >= 500) AS server_errors
        FROM api_usage a
        WHERE a."timestamp" > NOW() - make_interval(days => $1)
        GROUP BY service_path
        ORDER BY total_calls DESC
        LIMIT 25
        """,
        days,
    )
    out = []
    for r in rows:
        path = r["service_path"] or "unknown"
        total = int(r["total_calls"] or 0)
        errors = int(r["server_errors"] or 0)
        pretty = path.replace("/api/v1/", "").replace("-", " ").replace("_", " ").strip("/").title() or path
        out.append({
            "service_path": path,
            "service_name": pretty,
            "total_calls": total,
            "unique_users": int(r["unique_users"] or 0),
            "avg_response_time": int(_f(r["avg_ms"], 0)),
            "error_rate": _f(errors / total * 100) if total > 0 else 0.0,
        })
    return out


async def _usage_distinct_users(conn, days: int = 30) -> int:
    return int(await conn.fetchval(
        'SELECT COUNT(DISTINCT user_id) FROM api_usage WHERE "timestamp" > NOW() - make_interval(days => $1)',
        days,
    ) or 0)


async def _llm_call_counts(conn) -> Dict[str, int]:
    """Metered LLM API-call counts from credit_transactions (transaction_type='usage')."""
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE created_at >= date_trunc('month', NOW())) AS this_month,
            COUNT(*) FILTER (
                WHERE created_at >= date_trunc('month', NOW()) - INTERVAL '1 month'
                  AND created_at < date_trunc('month', NOW())
            ) AS last_month,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') AS last_30_days
        FROM credit_transactions
        WHERE transaction_type = 'usage'
        """
    )
    return {
        "this_month": int(row["this_month"] or 0),
        "last_month": int(row["last_month"] or 0),
        "last_30_days": int(row["last_30_days"] or 0),
    }


def _pct_change(current: float, previous: float) -> float:
    """% change vs previous. previous<=0 -> 0.0, matching the billing
    dashboard's growth_rate convention (never claims growth off a zero base)."""
    if previous > 0:
        return _f((current - previous) / previous * 100)
    return 0.0


async def compute_billing_summary_core() -> Optional[Dict[str, Any]]:
    """
    Shared real revenue core (used by routers/metering.py
    /api/v1/billing/analytics/summary so it reports the SAME numbers as the
    /api/v1/analytics/revenue/* endpoints and the billing dashboard).

    Returns None when the database is unreachable.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            has_rows = await _has_subscription_rows(conn)
            core = await _dashboard_core(conn)
            month_counts = await _subscription_month_counts(conn)
            return {
                "has_subscription_rows": has_rows,
                **core,
                **month_counts,
            }
    except Exception as e:  # noqa: BLE001 - callers fail soft to no_data zeros
        logger.warning("compute_billing_summary_core unavailable: %s: %s", type(e).__name__, e)
        return None


# ============================================================================
# REVENUE ANALYTICS (6 endpoints)
# ============================================================================

@revenue_router.get("/mrr")
async def get_monthly_recurring_revenue(
    months: int = Query(12, ge=1, le=24),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get Monthly Recurring Revenue (MRR) for last N months.

    **Query Parameters**:
    - `months`: Number of months to retrieve (1-24, default: 12)

    **Returns**:
    - Real MRR series reconstructed from organization_subscriptions
      (monthly_price + created_at/canceled_at). Current month matches
      /api/v1/billing/analytics/dashboard exactly. `no_data: true` with a
      zeroed shape when no subscription rows exist.
    - `mrr_trend` mirrors `mrr_data` for the AdvancedAnalytics chart.
    """
    payload = {
        "mrr_data": [],
        "mrr_trend": [],
        "current_mrr": 0,
        "previous_mrr": 0,
        "total_months": months,
        "no_data": True,
        "note": "insufficient data - no subscription rows yet"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if not await _has_subscription_rows(conn):
                return payload
            series = await _subscription_month_series(conn, months)
        mrr_data = [
            {"month": s["month"], "mrr": s["mrr"], "new_mrr": s["new_mrr"],
             "churned_mrr": s["churned_mrr"], "active_subscriptions": s["active_subscriptions"]}
            for s in series
        ]
        payload.update({
            "mrr_data": mrr_data,
            "mrr_trend": mrr_data,
            "current_mrr": series[-1]["mrr"] if series else 0,
            "previous_mrr": series[-2]["mrr"] if len(series) >= 2 else 0,
            "no_data": False,
            "note": "reconstructed from organization_subscriptions monthly_price (matches billing dashboard MRR)",
        })
        return payload
    except Exception as e:  # noqa: BLE001 - fail soft to honest zeros
        logger.warning("analytics revenue/mrr fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@revenue_router.get("/arr")
async def get_annual_recurring_revenue(_admin: Dict = Depends(require_admin_user)):
    """
    Get Annual Recurring Revenue (ARR) metrics.

    **Returns**:
    - Real ARR (= dashboard MRR x 12) plus YoY growth from the reconstructed
      monthly series. `arr_by_tier` keeps its fixed keys; a plan's ARR lands
      in a bucket only when subscription_plan literally matches that key
      (unmatched plans are still inside the total, never guessed into a bucket).
    """
    payload = {
        "arr": 0,
        "arr_by_tier": {k: 0 for k in FIXED_TIER_KEYS},
        "yoy_growth": 0,
        "mrr": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if not await _has_subscription_rows(conn):
                return payload
            core = await _dashboard_core(conn)
            plans = await _plan_breakdown(conn)
            series = await _subscription_month_series(conn, 13)
        arr_by_tier = {k: 0 for k in FIXED_TIER_KEYS}
        for p in plans:
            if p["plan"] in arr_by_tier:
                arr_by_tier[p["plan"]] = _f(p["mrr"] * 12)
        yoy = _pct_change(series[-1]["mrr"], series[0]["mrr"]) if len(series) >= 13 else 0.0
        payload.update({
            "arr": core["arr"],
            "arr_by_tier": arr_by_tier,
            "yoy_growth": yoy,
            "mrr": core["mrr"],
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics revenue/arr fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@revenue_router.get("/by-tier")
async def get_revenue_by_tier(_admin: Dict = Depends(require_admin_user)):
    """
    Get revenue breakdown by subscription tier.

    **Returns**:
    - Real active-subscription MRR grouped by subscription_plan
      (same monthly_price source as the billing dashboard).
    - `tier_breakdown` mirrors `tiers` for the AdvancedAnalytics chart
      (keys: tier / mrr / avg_revenue_per_user).
    """
    payload = {
        "tiers": [],
        "tier_breakdown": [],
        "total_revenue": 0,
        "total_customers": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            plans = await _plan_breakdown(conn)
        if not plans:
            return payload
        total_mrr = _f(sum(p["mrr"] for p in plans))
        total_customers = sum(p["customers"] for p in plans)
        tiers = [
            {
                "tier": p["plan"],
                "mrr": p["mrr"],
                "arr": _f(p["mrr"] * 12),
                "customers": p["customers"],
                "avg_revenue_per_user": _f(p["mrr"] / p["customers"]) if p["customers"] > 0 else 0.0,
                "percentage_of_total": _f(p["mrr"] / total_mrr * 100) if total_mrr > 0 else 0.0,
            }
            for p in plans
        ]
        payload.update({
            "tiers": tiers,
            "tier_breakdown": tiers,
            "total_revenue": total_mrr,
            "total_customers": total_customers,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics revenue/by-tier fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@revenue_router.get("/growth")
async def get_revenue_growth(_admin: Dict = Depends(require_admin_user)):
    """
    Get revenue growth metrics and trends.

    **Returns**:
    - Real MoM/QoQ/YoY growth of recurring revenue, from the same
      organization_subscriptions reconstruction the /mrr endpoint uses.
      Monthly "revenue" figures are the recurring-revenue level (MRR) at
      each month's end.
    """
    payload = {
        "mom_growth": 0,
        "qoq_growth": 0,
        "yoy_growth": 0,
        "growth_trend": "insufficient_data",
        "current_month_revenue": 0,
        "previous_month_revenue": 0,
        "same_month_last_year": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if not await _has_subscription_rows(conn):
                return payload
            series = await _subscription_month_series(conn, 13)
        if not series:
            return payload
        current = series[-1]["mrr"]
        prev = series[-2]["mrr"] if len(series) >= 2 else 0.0
        quarter_ago = series[-4]["mrr"] if len(series) >= 4 else 0.0
        year_ago = series[0]["mrr"] if len(series) >= 13 else 0.0
        mom = _pct_change(current, prev) if len(series) >= 2 else 0.0
        if mom > 0:
            trend = "increasing"
        elif mom < 0:
            trend = "decreasing"
        else:
            trend = "flat"
        payload.update({
            "mom_growth": mom,
            "qoq_growth": _pct_change(current, quarter_ago) if len(series) >= 4 else 0.0,
            "yoy_growth": _pct_change(current, year_ago) if len(series) >= 13 else 0.0,
            "growth_trend": trend,
            "current_month_revenue": current,
            "previous_month_revenue": prev,
            "same_month_last_year": year_ago,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics revenue/growth fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@revenue_router.get("/forecast")
async def get_revenue_forecast(
    months_ahead: int = Query(6, ge=1, le=12),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get revenue forecast for next N months.

    **Returns**:
    - Empty forecast with `no_data: true` — there is NO forecasting model
      wired, and inventing projections would violate the honest-data rule.
    """
    return {
        "forecast": [],
        "model": "insufficient_data",
        "growth_rate": 0,
        "generated_at": datetime.now().isoformat(),
        "no_data": True
    }


@revenue_router.get("/churn")
async def get_revenue_churn(
    months: int = Query(12, ge=1, le=24),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get revenue churn for last N months.

    **Returns**:
    - Real monthly canceled/expired subscription counts + lost MRR from
      organization_subscriptions (COALESCE(canceled_at, updated_at) bucketing,
      matching /api/v1/billing/analytics/churn/analysis). `churn_by_tier`
      keeps its fixed keys and only fills literal plan-name matches;
      cancellation reasons are not tracked, so `top_churn_reasons` stays empty.
    """
    payload = {
        "churn_data": [],
        "current_churn_rate": 0,
        "average_churn_rate": 0,
        "churn_by_tier": {k: 0 for k in FIXED_TIER_KEYS},
        "top_churn_reasons": [],
        "total_months": months,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if not await _has_subscription_rows(conn):
                return payload
            series = await _subscription_month_series(conn, months)
            core = await _dashboard_core(conn)
            churned_by_plan = await conn.fetch(
                """
                SELECT subscription_plan AS plan, COUNT(*) AS churned
                FROM organization_subscriptions
                WHERE status IN ('canceled', 'expired')
                  AND COALESCE(canceled_at, updated_at) >= NOW() - make_interval(months => $1)
                GROUP BY subscription_plan
                """,
                months,
            )
        churn_data = []
        monthly_rates = []
        for s in series:
            rate = _f(s["churned_count"] / s["active_subscriptions"] * 100) if s["active_subscriptions"] > 0 else 0.0
            churn_data.append({
                "month": s["month"],
                "churned_count": s["churned_count"],
                "churned_mrr": s["churned_mrr"],
                "churn_rate": rate,
            })
            if s["active_subscriptions"] > 0:
                monthly_rates.append(rate)
        churn_by_tier = {k: 0 for k in FIXED_TIER_KEYS}
        for r in churned_by_plan:
            if r["plan"] in churn_by_tier:
                churn_by_tier[r["plan"]] = int(r["churned"] or 0)
        payload.update({
            "churn_data": churn_data,
            "current_churn_rate": core["churn_rate"],
            "average_churn_rate": _f(sum(monthly_rates) / len(monthly_rates)) if monthly_rates else 0.0,
            "churn_by_tier": churn_by_tier,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics revenue/churn fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# ============================================================================
# USER ANALYTICS (5 endpoints)
# ============================================================================

@users_router.get("/ltv")
async def get_lifetime_value(_admin: Dict = Depends(require_admin_user)):
    """
    Get customer lifetime value (LTV) metrics.

    **Returns**:
    - Zeroed LTV payload with `no_data: true`. LTV/CAC require acquisition
      cost + lifespan history that is not tracked; computing it from the
      little we have would fabricate a metric.
    """
    return {
        "average_ltv": 0,
        "ltv_by_tier": {k: 0 for k in FIXED_TIER_KEYS},
        "ltv_cac_ratio": 0,
        "average_customer_lifespan_months": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }


@users_router.get("/churn")
async def get_user_churn(_admin: Dict = Depends(require_admin_user)):
    """
    Get user churn rate metrics.

    **Returns**:
    - Real subscription churn from organization_subscriptions — the same
      30-day churn rate as /api/v1/billing/analytics/dashboard, plus this
      calendar month's cancellations. `churn_rate` / `churned_users` mirror
      the real values for the AdvancedAnalytics Users section.
    """
    payload = {
        "monthly_churn_rate": 0,
        "churn_rate": 0,
        "churn_by_tier": {k: 0 for k in FIXED_TIER_KEYS},
        "retention_rate": 0,
        "churned_this_month": 0,
        "churned_users": 0,
        "total_customers": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if not await _has_subscription_rows(conn):
                return payload
            core = await _dashboard_core(conn)
            month_counts = await _subscription_month_counts(conn)
            churned_by_plan = await conn.fetch(
                """
                SELECT subscription_plan AS plan, COUNT(*) AS churned
                FROM organization_subscriptions
                WHERE status IN ('canceled', 'expired')
                  AND COALESCE(canceled_at, updated_at) >= date_trunc('month', NOW())
                GROUP BY subscription_plan
                """
            )
        churn_by_tier = {k: 0 for k in FIXED_TIER_KEYS}
        for r in churned_by_plan:
            if r["plan"] in churn_by_tier:
                churn_by_tier[r["plan"]] = int(r["churned"] or 0)
        payload.update({
            "monthly_churn_rate": core["churn_rate"],
            "churn_rate": core["churn_rate"],
            "churn_by_tier": churn_by_tier,
            "retention_rate": _f(100 - core["churn_rate"]),
            "churned_this_month": month_counts["cancelled_this_month"],
            "churned_users": month_counts["cancelled_this_month"],
            "total_customers": core["total_active_orgs"],
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics users/churn fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@users_router.get("/acquisition")
async def get_user_acquisition(_admin: Dict = Depends(require_admin_user)):
    """
    Get user acquisition metrics.

    **Returns**:
    - Real new-user counts (first organization_members.joined_at per user)
      for this and last calendar month. Signup channels / CPA are NOT
      tracked, so `acquisition_channels` stays empty and `average_cpa` 0.
    """
    payload = {
        "new_users_this_month": 0,
        "new_users_last_month": 0,
        "growth_rate": 0,
        "acquisition_channels": [],
        "average_cpa": 0,
        "basis": "organization_members_first_join",
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "channel attribution and CPA are not tracked; counts come from organization membership"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH firsts AS (
                    SELECT user_id, MIN(joined_at) AS first_joined
                    FROM organization_members
                    GROUP BY user_id
                )
                SELECT
                    COUNT(*) AS total_users,
                    COUNT(*) FILTER (WHERE first_joined >= date_trunc('month', NOW())) AS this_month,
                    COUNT(*) FILTER (
                        WHERE first_joined >= date_trunc('month', NOW()) - INTERVAL '1 month'
                          AND first_joined < date_trunc('month', NOW())
                    ) AS last_month
                FROM firsts
                """
            )
        total = int(row["total_users"] or 0)
        if total == 0:
            return payload
        this_month = int(row["this_month"] or 0)
        last_month = int(row["last_month"] or 0)
        payload.update({
            "new_users_this_month": this_month,
            "new_users_last_month": last_month,
            "growth_rate": _pct_change(this_month, last_month),
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics users/acquisition fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@users_router.get("/cohorts")
async def get_user_cohorts(
    months: int = Query(6, ge=1, le=12),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get user cohort sizes for last N months.

    **Returns**:
    - Real cohort SIZES (users grouped by month of first org membership).
      Per-user monthly activity is not tracked, so `retention_rates` is an
      empty list on every cohort and `average_retention_month_1` stays 0
      rather than inventing retention percentages.
    """
    payload = {
        "cohorts": [],
        "average_retention_month_1": 0,
        "total_cohorts": 0,
        "basis": "organization_members_first_join",
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "cohort sizes are real; retention tracking is not wired yet"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            series = await _member_month_series(conn, months)
        cohorts = [
            {"cohort": s["month"], "size": s["new_users"], "retention_rates": []}
            for s in series
        ]
        if not any(c["size"] for c in cohorts):
            return payload
        payload.update({
            "cohorts": cohorts,
            "total_cohorts": len(cohorts),
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics users/cohorts fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@users_router.get("/growth")
async def get_user_growth(
    months: int = Query(12, ge=1, le=24),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get user growth for last N months.

    **Returns**:
    - Real monthly series from organization_members first-join dates.
      `current_users` prefers the Keycloak user count (what
      /api/v1/admin/users/analytics/summary reports, cached ~5 min) and
      falls back to the distinct org-member count — `basis` says which.
    """
    payload = {
        "growth_data": [],
        "current_users": 0,
        "total_growth": 0,
        "average_monthly_growth": 0,
        "basis": "organization_members_first_join",
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            series = await _member_month_series(conn, months)
            total, _active, basis = await _user_headline_counts(conn)
        if not series or series[-1]["total_users"] == 0:
            # No membership rows yet; a bare Keycloak count alone is still real.
            if total > 0:
                payload.update({"current_users": total, "basis": basis, "no_data": False})
            return payload
        monthly_growth_pcts = []
        for prev_row, cur_row in zip(series, series[1:]):
            if prev_row["total_users"] > 0:
                monthly_growth_pcts.append(
                    _pct_change(cur_row["total_users"], prev_row["total_users"])
                )
        payload.update({
            "growth_data": series,
            "current_users": total if total > 0 else series[-1]["total_users"],
            "total_growth": sum(s["new_users"] for s in series),
            "average_monthly_growth": _f(sum(monthly_growth_pcts) / len(monthly_growth_pcts)) if monthly_growth_pcts else 0.0,
            "basis": basis,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics users/growth fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# ============================================================================
# SERVICE ANALYTICS (7 endpoints)
# ============================================================================

@services_router.get("/popularity")
async def get_service_popularity(_admin: Dict = Depends(require_admin_user)):
    """
    Get most popular services by usage (api_usage, last 30 days).

    **Returns**:
    - Real per-service call counts / unique users / avg duration / 5xx rate
      grouped by endpoint prefix. `no_data: true` while the api_usage table
      is empty (request tracking middleware not enabled) or missing.
    """
    payload = {
        "services": [],
        "total_services": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await _usage_by_service(conn, 30)
        if not rows:
            return payload
        services = [
            {
                "popularity_rank": i + 1,
                "service_name": r["service_name"],
                "service_path": r["service_path"],
                "total_calls": r["total_calls"],
                "unique_users": r["unique_users"],
                "avg_response_time": r["avg_response_time"],
                "error_rate": r["error_rate"],
            }
            for i, r in enumerate(rows)
        ]
        payload.update({
            "services": services,
            "total_services": len(services),
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/popularity fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@services_router.get("/cost-per-user")
async def get_cost_per_user(_admin: Dict = Depends(require_admin_user)):
    """
    Get infrastructure cost per active user.

    **Returns**:
    - Zeroed cost payload with `no_data: true` — cloud bills are not wired,
      and inventing infra costs would violate the honest-data rule.
      (`services` is an empty list for the AdvancedAnalytics cost table.)
    """
    return {
        "total_cost": 0,
        "active_users": 0,
        "cost_per_user": 0,
        "cost_breakdown": [],
        "services": [],
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }


@services_router.get("/adoption")
async def get_service_adoption(_admin: Dict = Depends(require_admin_user)):
    """
    Get service adoption rates (api_usage, last 30 days).

    **Returns**:
    - Real share of tracked users who used each service. `no_data: true`
      while api_usage is empty/missing.
    """
    payload = {
        "services": [],
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await _usage_by_service(conn, 30)
            total_users = await _usage_distinct_users(conn, 30)
        if not rows or total_users == 0:
            return payload
        payload.update({
            "services": [
                {
                    "service": r["service_name"],
                    "service_path": r["service_path"],
                    "users": r["unique_users"],
                    "adoption_rate": _f(r["unique_users"] / total_users * 100),
                }
                for r in rows
            ],
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/adoption fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@services_router.get("/performance")
async def get_service_performance(_admin: Dict = Depends(require_admin_user)):
    """
    Get monitored-service performance (website_checks, last 24 hours).

    **Returns**:
    - Real per-site uptime %, average latency and failed-check rate from the
      uptime monitor. `health_score` IS the 24h uptime percentage (no
      synthetic scoring model).
    """
    payload = {
        "services": [],
        "overall_uptime": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            sites = await _site_window_stats(conn, 24)
        if not sites:
            return payload
        services = [
            {
                "service": s["name"],
                "health_score": s["uptime_percent"],
                "uptime": s["uptime_percent"],
                "avg_latency": s["avg_ms"],
                "error_rate": _f(s["down_checks"] / s["total_checks"] * 100) if s["total_checks"] > 0 else 0.0,
                "status": s["last_status"],
                "last_check": s["last_check"],
            }
            for s in sites
        ]
        payload.update({
            "services": services,
            "overall_uptime": _f(sum(s["uptime"] for s in services) / len(services)),
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/performance fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@services_router.get("/uptime")
async def get_service_uptime(
    days: int = Query(30, ge=1, le=90),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get uptime history for last N days (website_checks).

    **Returns**:
    - Real per-site uptime percentages over the window, keyed by site name.
    """
    payload = {
        "services": {},
        "overall_average": 0,
        "days_analyzed": days,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            sites = await _site_window_stats(conn, days * 24)
        if not sites:
            return payload
        services = {
            s["name"]: {
                "uptime_percent": s["uptime_percent"],
                "total_checks": s["total_checks"],
                "failed_checks": s["down_checks"],
                "avg_response_time_ms": s["avg_ms"],
            }
            for s in sites
        }
        payload.update({
            "services": services,
            "overall_average": _f(sum(s["uptime_percent"] for s in sites) / len(sites)),
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/uptime fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@services_router.get("/latency")
async def get_service_latency(
    hours: int = Query(24, ge=1, le=168),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get response-time metrics for last N hours (website_checks.response_time_ms).

    **Returns**:
    - Real avg / p50 / p95 / max latency per monitored site.
    """
    payload = {
        "services": {},
        "hours_analyzed": hours,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT w.name,
                       COUNT(c.response_time_ms) AS samples,
                       COALESCE(AVG(c.response_time_ms), 0) AS avg_ms,
                       COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_time_ms), 0) AS p50_ms,
                       COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY c.response_time_ms), 0) AS p95_ms,
                       COALESCE(MAX(c.response_time_ms), 0) AS max_ms
                FROM monitored_websites w
                JOIN website_checks c ON c.website_id = w.id
                WHERE w.is_active = TRUE
                  AND c.response_time_ms IS NOT NULL
                  AND c.checked_at > NOW() - make_interval(hours => $1)
                GROUP BY w.name
                ORDER BY w.name
                """,
                hours,
            )
        if not rows:
            return payload
        payload.update({
            "services": {
                r["name"]: {
                    "avg_ms": _f(r["avg_ms"], 1),
                    "p50_ms": _f(r["p50_ms"], 1),
                    "p95_ms": _f(r["p95_ms"], 1),
                    "max_ms": int(r["max_ms"] or 0),
                    "samples": int(r["samples"] or 0),
                }
                for r in rows
            },
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/latency fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@services_router.get("/errors")
async def get_service_errors(
    hours: int = Query(24, ge=1, le=168),
    _admin: Dict = Depends(require_admin_user),
):
    """
    Get failed-check rates for last N hours (website_checks).

    **Returns**:
    - Real down-check counts, rates and the most recent recorded error per site.
    """
    payload = {
        "services": {},
        "hours_analyzed": hours,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            sites = await _site_window_stats(conn, hours)
        if not sites:
            return payload
        payload.update({
            "services": {
                s["name"]: {
                    "failed_checks": s["down_checks"],
                    "total_checks": s["total_checks"],
                    "error_rate": _f(s["down_checks"] / s["total_checks"] * 100) if s["total_checks"] > 0 else 0.0,
                    "last_error": s["last_error"],
                }
                for s in sites
            },
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics services/errors fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# ============================================================================
# METRICS & KPIs (3 endpoints)
# ============================================================================

@metrics_router.get("/summary")
async def get_metrics_summary(_admin: Dict = Depends(require_admin_user)):
    """
    Get high-level metrics summary dashboard.

    **Returns**:
    - Real aggregates: MRR/ARR (billing dashboard definition), user counts
      (Keycloak with org-member fallback), metered LLM API calls
      (credit_transactions) and monitored-site uptime. The flat keys
      (mrr/arr/total_users/...) duplicate the nested values for the
      AdvancedAnalytics overview cards.
    """
    payload = {
        "revenue": {"mrr": 0, "change": 0},
        "users": {"total": 0, "active": 0, "change": 0},
        "api_calls": {"this_month": 0, "change": 0},
        "churn_rate": {"percentage": 0, "change": 0},
        "mrr": 0,
        "arr": 0,
        "growth_rate": 0,
        "total_users": 0,
        "active_users": 0,
        "average_revenue_per_user": 0,
        "platform_uptime": 0,
        "total_api_calls_month": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            has_subs = await _has_subscription_rows(conn)
            core = await _dashboard_core(conn) if has_subs else None
            rev_series = await _subscription_month_series(conn, 2) if has_subs else []
            total_users, active_users, _basis = await _user_headline_counts(conn)
            member_series = await _member_month_series(conn, 2)
            try:
                calls = await _llm_call_counts(conn)
            except Exception as e:  # noqa: BLE001 - table may not exist on this node
                logger.debug("credit_transactions unavailable for metrics summary: %s", e)
                calls = {"this_month": 0, "last_month": 0, "last_30_days": 0}
            try:
                sites = await _site_window_stats(conn, 24)
            except Exception as e:  # noqa: BLE001
                logger.debug("website_checks unavailable for metrics summary: %s", e)
                sites = []

        has_any = bool(core) or total_users > 0 or calls["this_month"] > 0 or calls["last_month"] > 0 or bool(sites)
        if not has_any:
            return payload

        mrr = core["mrr"] if core else 0.0
        arr = core["arr"] if core else 0.0
        churn_pct = core["churn_rate"] if core else 0.0
        arpu = core["arpu"] if core else 0.0
        growth_rate = core["growth_rate"] if core else 0.0
        revenue_change = (
            _pct_change(rev_series[-1]["mrr"], rev_series[0]["mrr"]) if len(rev_series) >= 2 else 0.0
        )
        users_change = (
            _pct_change(member_series[-1]["total_users"], member_series[0]["total_users"])
            if len(member_series) >= 2 else 0.0
        )
        total_checks = sum(s["total_checks"] for s in sites)
        up_checks = sum(s["up_checks"] for s in sites)
        platform_uptime = _f(up_checks / total_checks * 100) if total_checks > 0 else 0.0

        payload.update({
            "revenue": {"mrr": mrr, "change": revenue_change},
            "users": {"total": total_users, "active": active_users, "change": users_change},
            "api_calls": {
                "this_month": calls["this_month"],
                "change": _pct_change(calls["this_month"], calls["last_month"]),
            },
            "churn_rate": {"percentage": churn_pct, "change": 0},
            "mrr": mrr,
            "arr": arr,
            "growth_rate": growth_rate,
            "total_users": total_users,
            "active_users": active_users,
            "average_revenue_per_user": arpu,
            "platform_uptime": platform_uptime,
            "total_api_calls_month": calls["this_month"],
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics metrics/summary fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@metrics_router.get("/kpis")
async def get_kpis(_admin: Dict = Depends(require_admin_user)):
    """
    Get key performance indicators.

    **Returns**:
    - Real values where a source exists (MRR/ARR, user counts, subscription
      churn/retention, uptime + latency from website_checks, metered LLM
      calls/day from credit_transactions). LTV/CAC remain 0 — not tracked.
    """
    payload = {
        "revenue_kpis": {"mrr": 0, "arr": 0, "ltv": 0, "ltv_cac_ratio": 0},
        "user_kpis": {"total_users": 0, "active_users": 0, "churn_rate": 0, "retention_rate": 0},
        "service_kpis": {"uptime": 0, "avg_response_time_ms": 0, "api_calls_per_day": 0, "error_rate": 0},
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "ltv / ltv_cac_ratio are not tracked and stay 0"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            has_subs = await _has_subscription_rows(conn)
            core = await _dashboard_core(conn) if has_subs else None
            total_users, active_users, _basis = await _user_headline_counts(conn)
            try:
                calls = await _llm_call_counts(conn)
            except Exception:  # noqa: BLE001
                calls = {"this_month": 0, "last_month": 0, "last_30_days": 0}
            try:
                sites = await _site_window_stats(conn, 30 * 24)
            except Exception:  # noqa: BLE001
                sites = []

        has_any = bool(core) or total_users > 0 or calls["last_30_days"] > 0 or bool(sites)
        if not has_any:
            return payload

        total_checks = sum(s["total_checks"] for s in sites)
        up_checks = sum(s["up_checks"] for s in sites)
        down_checks = sum(s["down_checks"] for s in sites)
        weighted_ms = sum(s["avg_ms"] * s["total_checks"] for s in sites)

        payload.update({
            "revenue_kpis": {
                "mrr": core["mrr"] if core else 0,
                "arr": core["arr"] if core else 0,
                "ltv": 0,
                "ltv_cac_ratio": 0,
            },
            "user_kpis": {
                "total_users": total_users,
                "active_users": active_users,
                "churn_rate": core["churn_rate"] if core else 0,
                "retention_rate": _f(100 - core["churn_rate"]) if core else 0,
            },
            "service_kpis": {
                "uptime": _f(up_checks / total_checks * 100) if total_checks > 0 else 0,
                "avg_response_time_ms": _f(weighted_ms / total_checks, 1) if total_checks > 0 else 0,
                "api_calls_per_day": _f(calls["last_30_days"] / 30, 1),
                "error_rate": _f(down_checks / total_checks * 100) if total_checks > 0 else 0,
            },
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics metrics/kpis fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@metrics_router.get("/alerts")
async def get_metric_alerts(_admin: Dict = Depends(require_admin_user)):
    """
    Get active operational alerts derived from the uptime monitor.

    **Returns**:
    - Real alerts: sites whose LATEST check is down (critical) and SSL
      certificates expiring within 14 days (warning). `no_data: true` when
      no monitoring checks exist yet; empty lists with `no_data: false`
      genuinely mean "no active alerts".
    """
    payload = {
        "critical_alerts": [],
        "warning_alerts": [],
        "info_alerts": [],
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT w.name, w.url,
                       c.status, c.error, c.checked_at, c.ssl_valid, c.ssl_expiry
                FROM monitored_websites w
                JOIN LATERAL (
                    SELECT status, error, checked_at, ssl_valid, ssl_expiry
                    FROM website_checks
                    WHERE website_id = w.id
                    ORDER BY checked_at DESC
                    LIMIT 1
                ) c ON TRUE
                WHERE w.is_active = TRUE
                """
            )
        if not rows:
            return payload
        critical = []
        warning = []
        now = datetime.now()
        for r in rows:
            if r["status"] == "down":
                critical.append({
                    "type": "website_down",
                    "severity": "critical",
                    "service": r["name"],
                    "url": r["url"],
                    "error": r["error"],
                    "detected_at": r["checked_at"].isoformat() if r["checked_at"] else None,
                })
            expiry = r["ssl_expiry"]
            if expiry is not None:
                days_left = (expiry - now).days
                if days_left <= 14:
                    warning.append({
                        "type": "ssl_expiring",
                        "severity": "warning",
                        "service": r["name"],
                        "url": r["url"],
                        "ssl_expiry": expiry.isoformat(),
                        "days_until_expiry": days_left,
                    })
        payload.update({
            "critical_alerts": critical,
            "warning_alerts": warning,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics metrics/alerts fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# ============================================================================
# PERFORMANCE ANALYTICS (1 endpoint)
# ============================================================================

@performance_router.get("/metrics")
async def get_performance_metrics(_admin: Dict = Depends(require_admin_user)):
    """
    Get system-wide performance metrics.

    **Returns**:
    - Zeroed metrics payload with `no_data: true` (host/DB/Redis/APM
      aggregation not wired here). Use /api/v1/system/status for real host
      metrics — duplicating a partial guess here would be dishonest.
    """
    return {
        "system": {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_rx_mbps": 0,
            "network_tx_mbps": 0
        },
        "database": {
            "connections_active": 0,
            "connections_max": 0,
            "query_avg_time_ms": 0,
            "slow_queries": 0
        },
        "cache": {
            "redis_hit_rate": 0,
            "redis_memory_used_mb": 0,
            "redis_memory_max_mb": 0,
            "keys_total": 0
        },
        "api": {
            "requests_per_second": 0,
            "avg_response_time_ms": 0,
            "p95_response_time_ms": 0,
            "error_rate": 0
        },
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }


# ============================================================================
# MAIN ANALYTICS (1 endpoint - Top-level summary)
# ============================================================================

@main_router.get("/summary")
async def get_analytics_summary(_admin: Dict = Depends(require_admin_user)):
    """
    Get comprehensive analytics summary across all categories.

    **Returns**:
    - Real aggregates from the same sources as the category endpoints
      (subscriptions, org members/Keycloak, credit_transactions,
      website_checks). LTV/CAC/NPS are not tracked and stay 0.
    """
    payload = {
        "revenue": {"mrr": 0, "arr": 0, "mom_growth": 0, "churn_rate": 0},
        "users": {"total": 0, "active": 0, "new_this_month": 0, "churn_this_month": 0, "growth_rate": 0},
        "services": {
            "total_services": 0,
            "average_uptime": 0,
            "total_api_calls": 0,
            "average_response_time_ms": 0
        },
        "kpis": {"ltv": 0, "cac": 0, "ltv_cac_ratio": 0, "retention_rate": 0, "nps_score": 0},
        "top_performing_tier": None,
        "top_performing_service": None,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            has_subs = await _has_subscription_rows(conn)
            core = await _dashboard_core(conn) if has_subs else None
            rev_series = await _subscription_month_series(conn, 2) if has_subs else []
            plans = await _plan_breakdown(conn) if has_subs else []
            month_counts = await _subscription_month_counts(conn) if has_subs else {"cancelled_this_month": 0}
            total_users, active_users, _basis = await _user_headline_counts(conn)
            new_members = await conn.fetchval(
                """
                WITH firsts AS (
                    SELECT user_id, MIN(joined_at) AS first_joined
                    FROM organization_members GROUP BY user_id
                )
                SELECT COUNT(*) FROM firsts WHERE first_joined >= date_trunc('month', NOW())
                """
            )
            try:
                calls = await _llm_call_counts(conn)
            except Exception:  # noqa: BLE001
                calls = {"this_month": 0, "last_month": 0, "last_30_days": 0}
            try:
                sites = await _site_window_stats(conn, 24)
            except Exception:  # noqa: BLE001
                sites = []

        has_any = bool(core) or total_users > 0 or calls["this_month"] > 0 or bool(sites)
        if not has_any:
            return payload

        total_checks = sum(s["total_checks"] for s in sites)
        up_checks = sum(s["up_checks"] for s in sites)
        weighted_ms = sum(s["avg_ms"] * s["total_checks"] for s in sites)
        best_site = max(sites, key=lambda s: (s["uptime_percent"], -s["avg_ms"]))["name"] if sites else None

        payload.update({
            "revenue": {
                "mrr": core["mrr"] if core else 0,
                "arr": core["arr"] if core else 0,
                "mom_growth": _pct_change(rev_series[-1]["mrr"], rev_series[0]["mrr"]) if len(rev_series) >= 2 else 0,
                "churn_rate": core["churn_rate"] if core else 0,
            },
            "users": {
                "total": total_users,
                "active": active_users,
                "new_this_month": int(new_members or 0),
                "churn_this_month": month_counts["cancelled_this_month"],
                "growth_rate": core["growth_rate"] if core else 0,
            },
            "services": {
                "total_services": len(sites),
                "average_uptime": _f(up_checks / total_checks * 100) if total_checks > 0 else 0,
                "total_api_calls": calls["this_month"],
                "average_response_time_ms": _f(weighted_ms / total_checks, 1) if total_checks > 0 else 0,
            },
            "kpis": {
                "ltv": 0,
                "cac": 0,
                "ltv_cac_ratio": 0,
                "retention_rate": _f(100 - core["churn_rate"]) if core else 0,
                "nps_score": 0,
            },
            "top_performing_tier": plans[0]["plan"] if plans else None,
            "top_performing_service": best_site,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("analytics main/summary fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# Export all routers for server.py registration
__all__ = [
    "revenue_router", "users_router", "services_router", "metrics_router",
    "performance_router", "main_router", "compute_billing_summary_core",
]
