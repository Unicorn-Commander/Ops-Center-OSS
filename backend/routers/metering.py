"""
Metering & Billing API Router
Provides usage metering, billing analytics, and LLM cost tracking endpoints.

STATUS OF DATA (all REAL or honestly zeroed — the random/hardcoded mock data
this module used to return is gone; never regress to that):

- /api/v1/billing/analytics/summary — REAL revenue/subscription figures from
  routers.analytics.compute_billing_summary_core, i.e. the exact same
  organization_subscriptions queries as /api/v1/billing/analytics/dashboard.
  Cost/profitability/payment sections are not tracked anywhere and stay zeroed.

- /api/v1/llm/usage/summary and /api/v1/llm/costs — REAL, aggregated from
  credit_transactions rows with transaction_type='usage' (the rows
  litellm_credit_system.debit_credits writes for every metered LLM /
  inference call: model, tokens_used, cost-in-credits). This is the same
  table the billing usage summary and /api/v1/analytics/metrics/* use, so
  the numbers agree across dashboards. Input/output token split is NOT
  stored (only tokens_used) so those keys stay 0 with a note.

- /api/v1/metering/summary, /api/v1/metering/usage/by-service and
  /api/v1/metering/service/{name} — REAL, aggregated from usage_events
  (usage_metering.UsageMeter.track_usage; services observed in code:
  'litellm', 'inference_proxy', 'image_generation', plus anything callers
  register). usage_events is used as the single source for per-service
  splits because metered LLM calls are recorded in BOTH usage_events AND
  credit_transactions — mixing the two inside one breakdown would double
  count. DB service labels are mapped onto the UI's service keys
  (litellm→llm_inference, center-deep→search_queries, brigade→
  agent_invocations); unmapped labels pass through unchanged, nothing is
  invented into a bucket.

- /api/v1/llm/cache-stats — zeroed with no_data:true. No LLM response-cache
  metrics are collected anywhere yet; inventing hit rates would violate the
  honest-data rule.

Every endpoint keeps its legacy JSON keys, carries "no_data" (false only when
real rows backed the numbers), and fail-softs to the zeroed shape if the
database is unreachable — same pattern as routers/analytics.py.
"""

import logging
from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

from auth_dependencies import require_admin_user  # admin gate (these live under the m2m-allowlisted /api/v1/llm prefix)
from database.connection import get_db_pool
from routers.analytics import compute_billing_summary_core  # shared real revenue core (billing-dashboard definitions)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Metering"])


# ============================================================================
# SHARED HELPERS
# ============================================================================

def _f(value: Any, digits: int = 2) -> float:
    """Coerce asyncpg Decimal/None to a rounded float."""
    return round(float(value or 0), digits)


def _pct_change(current: float, previous: float) -> float:
    """% change vs previous; previous<=0 -> 0.0 (never claims growth off a zero base)."""
    if previous > 0:
        return round((current - previous) / previous * 100, 2)
    return 0.0


# Hard cap for user-supplied trailing windows (10 years). Without it a huge
# "Nd" period (e.g. 9999999999d) overflowed timedelta arithmetic BEFORE the
# handlers' fail-soft try blocks and returned a 500.
_MAX_WINDOW_DAYS = 3650


def normalize_period(period: str) -> str:
    """
    Convert various period formats to days format (Nd).

    Args:
        period: Time period (this_month, 30d, this_week, etc.)

    Returns:
        Normalized period in Nd format, clamped to [1, _MAX_WINDOW_DAYS] days
        so downstream timedelta arithmetic can never overflow.
    """
    mappings = {
        "this_month": "30d",
        "last_month": "30d",
        "this_week": "7d",
        "last_week": "7d",
        "today": "1d",
        "yesterday": "1d",
        "this_quarter": "90d",
        "last_quarter": "90d",
        "last_3_months": "90d",
        "last_6_months": "180d"
    }

    # If already in Nd format, clamp and return
    if period.endswith('d') and period[:-1].isdigit():
        return f"{min(max(int(period[:-1]), 1), _MAX_WINDOW_DAYS)}d"

    # Otherwise, use mapping or default to 30d
    return mappings.get(period.lower(), "30d")


def _period_bounds(period: str) -> Tuple[datetime, datetime]:
    """
    Resolve a period name to [start, end) naive-UTC datetimes.

    Calendar periods (this_month/last_month/this_quarter/last_quarter) use
    real calendar boundaries; last_3_months/last_6_months/Nd are trailing
    windows. Naive datetime.utcnow() params against TIMESTAMPTZ columns is
    the established asyncpg pattern in this codebase (billing_analytics_api).
    """
    now = datetime.utcnow()
    p = (period or "").lower()
    if p == "this_month":
        return datetime(now.year, now.month, 1), now
    if p == "last_month":
        first_this = datetime(now.year, now.month, 1)
        first_last = (first_this - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return first_last, first_this
    if p == "this_quarter":
        q_month = ((now.month - 1) // 3) * 3 + 1
        return datetime(now.year, q_month, 1), now
    if p == "last_quarter":
        q_month = ((now.month - 1) // 3) * 3 + 1
        this_q_start = datetime(now.year, q_month, 1)
        prev_day = this_q_start - timedelta(days=1)
        prev_q_month = ((prev_day.month - 1) // 3) * 3 + 1
        return datetime(prev_day.year, prev_q_month, 1), this_q_start
    # Trailing windows (last_3_months, last_6_months, Nd, unknown -> 30d)
    days = int(normalize_period(p or "30d").rstrip("d"))
    return now - timedelta(days=days), now


def _previous_window(start: datetime, end: datetime) -> Tuple[datetime, datetime]:
    """Equal-length window immediately before [start, end)."""
    length = end - start
    return start - length, start


# UI service keys (src/pages/UsageMetrics.jsx SERVICE_CONFIG) <-> usage_events
# service labels actually written by backend code. Only literal, documented
# label matches are mapped; unknown labels pass through under their own name.
_SERVICE_KEY_ALIASES = {
    "litellm": "llm_inference",
    "openrouter": "llm_inference",
    "llm": "llm_inference",
    "center-deep": "search_queries",
    "center_deep": "search_queries",
    "search": "search_queries",
    "brigade": "agent_invocations",
    "agent": "agent_invocations",
}

_SERVICE_DB_NAMES = {
    "llm_inference": ["litellm", "openrouter", "llm"],
    "search_queries": ["center-deep", "center_deep", "search"],
    "agent_invocations": ["brigade", "agent"],
    "tts": ["tts"],
    "stt": ["stt"],
    "image_generation": ["image_generation"],
    "storage": ["storage"],
    "bandwidth": ["bandwidth"],
}


def _ui_service_key(db_service: Optional[str]) -> str:
    s = (db_service or "unknown").lower()
    return _SERVICE_KEY_ALIASES.get(s, s)


async def _llm_usage_totals(conn, start: datetime, end: datetime) -> Dict[str, Any]:
    """Metered LLM totals from credit_transactions (transaction_type='usage')."""
    row = await conn.fetchrow(
        """
        SELECT COUNT(*) AS calls,
               COALESCE(SUM(tokens_used), 0) AS tokens,
               COALESCE(SUM(COALESCE(cost, -amount, 0)), 0) AS credits
        FROM credit_transactions
        WHERE transaction_type = 'usage'
          AND created_at >= $1 AND created_at < $2
        """,
        start, end,
    )
    return {
        "calls": int(row["calls"] or 0),
        "tokens": int(row["tokens"] or 0),
        "credits": _f(row["credits"], 4),
    }


async def _llm_usage_by_model(conn, start: datetime, end: datetime, limit: int = 10) -> List[Dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT COALESCE(model, 'unknown') AS model,
               COUNT(*) AS calls,
               COALESCE(SUM(tokens_used), 0) AS tokens,
               COALESCE(SUM(COALESCE(cost, -amount, 0)), 0) AS credits
        FROM credit_transactions
        WHERE transaction_type = 'usage'
          AND created_at >= $1 AND created_at < $2
        GROUP BY COALESCE(model, 'unknown')
        ORDER BY credits DESC, calls DESC
        LIMIT $3
        """,
        start, end, limit,
    )
    return [
        {
            "model": r["model"],
            "calls": int(r["calls"] or 0),
            "tokens": int(r["tokens"] or 0),
            "cost_credits": _f(r["credits"], 4),
        }
        for r in rows
    ]


async def _llm_daily_series(conn, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """Zero-filled per-day calls/tokens/credits from credit_transactions."""
    rows = await conn.fetch(
        """
        WITH days AS (
            SELECT generate_series(
                date_trunc('day', $1::timestamptz),
                date_trunc('day', $2::timestamptz),
                INTERVAL '1 day'
            ) AS day
        )
        SELECT to_char(d.day, 'YYYY-MM-DD') AS date,
               COALESCE(COUNT(t.id), 0) AS calls,
               COALESCE(SUM(t.tokens_used), 0) AS tokens,
               COALESCE(SUM(COALESCE(t.cost, -t.amount, 0)), 0) AS credits
        FROM days d
        LEFT JOIN credit_transactions t
               ON t.transaction_type = 'usage'
              AND t.created_at >= d.day
              AND t.created_at < d.day + INTERVAL '1 day'
              AND t.created_at >= $1 AND t.created_at < $2
        GROUP BY d.day
        ORDER BY d.day
        """,
        start, end,
    )
    return [
        {
            "date": r["date"],
            "calls": int(r["calls"] or 0),
            "tokens": int(r["tokens"] or 0),
            "cost_credits": _f(r["credits"], 4),
        }
        for r in rows
    ]


async def _events_by_service(conn, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    """Per-service aggregates from usage_events over a window."""
    rows = await conn.fetch(
        """
        SELECT service,
               COUNT(*) AS events,
               COALESCE(SUM(tokens_used), 0) AS tokens,
               COALESCE(SUM(cost), 0) AS credits,
               COUNT(DISTINCT user_id) AS unique_users
        FROM usage_events
        WHERE created_at >= $1 AND created_at < $2
        GROUP BY service
        ORDER BY credits DESC, events DESC
        """,
        start, end,
    )
    return [
        {
            "service": r["service"],
            "events": int(r["events"] or 0),
            "tokens": int(r["tokens"] or 0),
            "credits": _f(r["credits"], 4),
            "unique_users": int(r["unique_users"] or 0),
        }
        for r in rows
    ]


def _merge_service_rows(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Fold usage_events service labels into UI service keys (summing aliases)."""
    merged: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        key = _ui_service_key(r["service"])
        slot = merged.setdefault(
            key, {"events": 0, "tokens": 0, "credits": 0.0, "unique_users": 0}
        )
        slot["events"] += r["events"]
        slot["tokens"] += r["tokens"]
        slot["credits"] = _f(slot["credits"] + r["credits"], 4)
        # unique_users can't be summed across labels without double counting;
        # keep the max as a lower bound rather than inventing a union count.
        slot["unique_users"] = max(slot["unique_users"], r["unique_users"])
    return merged


async def _events_service_detail(
    conn, db_names: List[str], start: datetime, end: datetime
) -> Dict[str, Any]:
    """Totals + top users + zero-filled daily series for one UI service key."""
    totals = await conn.fetchrow(
        """
        SELECT COUNT(*) AS events,
               COALESCE(SUM(tokens_used), 0) AS tokens,
               COALESCE(SUM(cost), 0) AS credits
        FROM usage_events
        WHERE service = ANY($1::text[])
          AND created_at >= $2 AND created_at < $3
        """,
        db_names, start, end,
    )
    top_users = await conn.fetch(
        """
        SELECT user_id,
               COUNT(*) AS events,
               COALESCE(SUM(cost), 0) AS credits
        FROM usage_events
        WHERE service = ANY($1::text[])
          AND created_at >= $2 AND created_at < $3
        GROUP BY user_id
        ORDER BY credits DESC, events DESC
        LIMIT 5
        """,
        db_names, start, end,
    )
    daily = await conn.fetch(
        """
        WITH days AS (
            SELECT generate_series(
                date_trunc('day', $2::timestamptz),
                date_trunc('day', $3::timestamptz),
                INTERVAL '1 day'
            ) AS day
        )
        SELECT to_char(d.day, 'YYYY-MM-DD') AS date,
               COALESCE(COUNT(e.id), 0) AS events,
               COALESCE(SUM(e.tokens_used), 0) AS tokens,
               COALESCE(SUM(e.cost), 0) AS credits
        FROM days d
        LEFT JOIN usage_events e
               ON e.service = ANY($1::text[])
              AND e.created_at >= d.day
              AND e.created_at < d.day + INTERVAL '1 day'
              AND e.created_at >= $2 AND e.created_at < $3
        GROUP BY d.day
        ORDER BY d.day
        """,
        db_names, start, end,
    )
    return {
        "events": int(totals["events"] or 0),
        "tokens": int(totals["tokens"] or 0),
        "credits": _f(totals["credits"], 4),
        "top_users": [
            {
                "user_id": r["user_id"],
                "api_calls": int(r["events"] or 0),
                "cost_credits": _f(r["credits"], 4),
            }
            for r in top_users
        ],
        "daily": [
            {
                "date": r["date"],
                "events": int(r["events"] or 0),
                "tokens": int(r["tokens"] or 0),
                "credits": _f(r["credits"], 4),
            }
            for r in daily
        ],
    }


# ============================================================================
# LLM USAGE & COSTS (3 endpoints)
# ============================================================================

@router.get("/llm/usage/summary")
async def get_llm_usage_summary(range: Literal["day", "week", "month", "year"] = "month", _admin: Dict[str, Any] = Depends(require_admin_user)):
    """
    Get LLM usage summary for specified time range.

    **Query Parameters**:
    - `range`: Time range (day, week, month, year) - default: month

    **Returns**:
    - REAL metered LLM usage from credit_transactions (transaction_type
      ='usage'): total calls, tokens_used sums, per-model breakdown and cost
      in credits — the same rows the billing/credit system writes per call.
    - `tokens.input_tokens` / `tokens.output_tokens` stay 0: only the total
      tokens_used per call is stored, and splitting it would be invented.
    - `no_data: true` with a zeroed shape when no usage rows exist in range.
    """
    days = {"day": 1, "week": 7, "month": 30, "year": 365}[range]
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    payload = {
        "time_range": range,
        "total_api_calls": 0,
        "tokens": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        },
        "top_models": [],
        "total_cost_credits": 0,
        "average_cost_per_call": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "metered LLM calls from credit_transactions; input/output token split is not tracked (only totals)"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            totals = await _llm_usage_totals(conn, start, now)
            if totals["calls"] == 0:
                return payload
            models = await _llm_usage_by_model(conn, start, now)
        payload.update({
            "total_api_calls": totals["calls"],
            "tokens": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": totals["tokens"],
            },
            "top_models": models,
            "total_cost_credits": totals["credits"],
            "average_cost_per_call": _f(totals["credits"] / totals["calls"], 4) if totals["calls"] > 0 else 0,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001 - fail soft to honest zeros
        logger.warning("llm/usage/summary fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@router.get("/llm/costs")
async def get_llm_costs(period: str = Query("30d", description="Time period (e.g., '30d', 'this_month', 'this_week')"), _admin: Dict[str, Any] = Depends(require_admin_user)):
    """
    Get LLM costs breakdown for specified period.

    **Query Parameters**:
    - `period`: Time period - accepts "Nd" format (e.g., "7d", "30d", "90d") or
                named periods (this_month, last_month, this_week, today)

    **Returns**:
    - REAL costs in credits from credit_transactions usage rows: zero-filled
      daily trend, per-model breakdown, and per-tier breakdown via the
      user_credits.tier of the spending user.
    - `by_model` mirrors `cost_by_model` as a {model: credits} map for
      LLMManagement.jsx. `no_data: true` when no usage rows exist in range.
    """
    normalized_period = normalize_period(period)
    days = int(normalized_period.rstrip('d'))
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    payload = {
        "period": period,
        "normalized_period": normalized_period,
        "days": days,
        "total_cost_credits": 0,
        "average_daily_cost": 0,
        "cost_by_model": [],
        "by_model": {},
        "cost_by_tier": [],
        "daily_trend": [],
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "credits metered per LLM call in credit_transactions; empty until usage rows exist"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            totals = await _llm_usage_totals(conn, start, now)
            if totals["calls"] == 0:
                return payload
            models = await _llm_usage_by_model(conn, start, now, limit=15)
            daily = await _llm_daily_series(conn, start, now)
            tier_rows = await conn.fetch(
                """
                SELECT COALESCE(uc.tier, 'unknown') AS tier,
                       COALESCE(SUM(COALESCE(t.cost, -t.amount, 0)), 0) AS credits
                FROM credit_transactions t
                LEFT JOIN user_credits uc ON uc.user_id = t.user_id
                WHERE t.transaction_type = 'usage'
                  AND t.created_at >= $1 AND t.created_at < $2
                GROUP BY COALESCE(uc.tier, 'unknown')
                ORDER BY credits DESC
                """,
                start, now,
            )
        cost_by_model = [
            {"model": m["model"], "cost_credits": m["cost_credits"]} for m in models
        ]
        payload.update({
            "total_cost_credits": totals["credits"],
            "average_daily_cost": _f(totals["credits"] / days, 4) if days > 0 else 0,
            "cost_by_model": cost_by_model,
            "by_model": {m["model"]: m["cost_credits"] for m in models},
            "cost_by_tier": [
                {"tier": r["tier"], "cost_credits": _f(r["credits"], 4)} for r in tier_rows
            ],
            "daily_trend": [
                {"date": d["date"], "cost_credits": d["cost_credits"]} for d in daily
            ],
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("llm/costs fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@router.get("/llm/cache-stats")
async def get_cache_stats(_admin: Dict[str, Any] = Depends(require_admin_user)):
    """
    Get LLM cache statistics and hit rates.

    **Returns**:
    - Zeroed shape with `no_data: true`. No LLM response-cache metrics are
      collected anywhere in the stack yet (this endpoint used to return
      hardcoded fake hit rates — never regress to that).
    """
    return {
        "cache_hit_rate": 0,
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "cache_size_mb": 0,
        "cache_entries": 0,
        "estimated_cost_saved_credits": 0,
        "average_response_time_ms": {
            "cache_hit": 0,
            "cache_miss": 0
        },
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "LLM response caching metrics are not collected yet"
    }


# ============================================================================
# METERING (3 endpoints)
# ============================================================================

@router.get("/metering/service/{service_name}")
async def get_service_metering(
    service_name: str,
    period: str = Query("this_month", description="this_month, last_month, this_quarter, last_quarter, last_3_months, last_6_months, or Nd"),
    _admin: Dict[str, Any] = Depends(require_admin_user),
):
    """
    Get metering data for a specific service.

    **Path Parameters**:
    - `service_name`: Service identifier (llm_inference, tts, stt, storage, etc.)

    **Query Parameters**:
    - `period`: Time period (calendar or trailing window)

    **Returns**:
    - REAL per-service usage from usage_events: event counts, tokens where
      recorded, credits, top users and a zero-filled `daily_usage` series
      ({date, usage} points for the UsageMetrics chart; `usage_by_day`
      mirrors it with the legacy key). UI service keys map onto the labels
      backend code actually writes (llm_inference<-litellm etc.); unknown
      names are looked up literally. `no_data: true` when nothing is
      recorded for the service in the window (e.g. storage, which has no
      metering source yet — its `total_gb` stays 0 rather than being faked).
    """
    start, end = _period_bounds(period)
    payload = {
        "service": service_name,
        "period": period,
        "total_units": 0,
        "unit_type": "events",
        "total_api_calls": 0,
        "total_tokens": 0,
        "total_cost_credits": 0,
        "top_users": [],
        "usage_by_day": [],
        "daily_usage": [],
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "usage_events has no rows for this service in the selected period"
    }
    if service_name == "storage":
        payload["total_gb"] = 0  # legacy key; no storage metering source exists
    try:
        db_names = _SERVICE_DB_NAMES.get(service_name, [service_name])
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            detail = await _events_service_detail(conn, db_names, start, end)
        if detail["events"] == 0:
            return payload
        # llm_inference charts token volume (SERVICE_CONFIG unit: tokens);
        # other services chart event counts — their per-unit volumes
        # (minutes/GB/queries) are not recorded, only occurrences.
        use_tokens = service_name == "llm_inference" and detail["tokens"] > 0
        daily_usage = [
            {
                "date": d["date"],
                "usage": d["tokens"] if use_tokens else d["events"],
                "events": d["events"],
                "cost_credits": d["credits"],
            }
            for d in detail["daily"]
        ]
        payload.update({
            "total_units": detail["events"],
            "unit_type": "tokens" if use_tokens else "events",
            "total_api_calls": detail["events"],
            "total_tokens": detail["tokens"],
            "total_cost_credits": detail["credits"],
            "top_users": detail["top_users"],
            "usage_by_day": [
                {"date": d["date"], "api_calls": d["events"]} for d in detail["daily"]
            ],
            "daily_usage": daily_usage,
            "no_data": False,
            "note": f"aggregated from usage_events service labels {db_names}",
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("metering/service/%s fell back to no_data: %s: %s", service_name, type(e).__name__, e)
        return payload


@router.get("/metering/summary")
async def get_metering_summary(
    period: str = Query("this_month", description="this_month, last_month, this_quarter, last_quarter, last_3_months, last_6_months, or Nd"),
    _admin: Dict[str, Any] = Depends(require_admin_user),
):
    """
    Get overall metering summary across all services.

    **Query Parameters**:
    - `period`: Time period (calendar or trailing window)

    **Returns**:
    - REAL per-service usage from usage_events, keyed by UI service key
      (`services` is a map — the shape UsageMetrics.jsx consumes: count /
      last_period_count / change_percentage / cost per service, plus the
      legacy units/unit_type/cost_credits/percentage_of_total fields).
    - `total_revenue` is the REAL subscription MRR (same
      organization_subscriptions source as the billing dashboard).
    - `gross_margin` stays 0: usage costs are credit-denominated and revenue
      is dollar-denominated — subtracting them (as the old mock did) would
      be fabricated. `usage_percentage` stays 0: no per-service quotas exist.
    - `no_data: true` when neither usage events nor subscriptions exist.
    """
    start, end = _period_bounds(period)
    prev_start, prev_end = _previous_window(start, end)
    payload = {
        "period": period,
        "services": {},
        "total_cost_credits": 0,
        "total_revenue": 0,
        "gross_margin": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "per-service usage from usage_events; revenue = subscription MRR; gross margin not computed (credit costs are not dollar-denominated)"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            current_rows = await _events_by_service(conn, start, end)
            previous_rows = await _events_by_service(conn, prev_start, prev_end)
        current = _merge_service_rows(current_rows)
        previous = _merge_service_rows(previous_rows)

        core = await compute_billing_summary_core()
        mrr = core["mrr"] if core and core.get("has_subscription_rows") else 0

        if not current and not mrr:
            return payload

        total_credits = _f(sum(s["credits"] for s in current.values()), 4)
        services: Dict[str, Any] = {}
        for key, cur in current.items():
            prev = previous.get(key, {"events": 0, "credits": 0.0})
            services[key] = {
                # Keys UsageMetrics.jsx consumes:
                "count": cur["events"],
                "last_period_count": prev["events"],
                "change_percentage": _pct_change(cur["events"], prev["events"]),
                "cost": cur["credits"],
                "usage_percentage": 0,  # no per-service quotas tracked
                # Legacy keys (same meanings as the old list entries):
                "units": cur["events"],
                "unit_type": "events",
                "cost_credits": cur["credits"],
                "percentage_of_total": _f(cur["credits"] / total_credits * 100) if total_credits > 0 else 0.0,
                "tokens": cur["tokens"],
                "unique_users": cur["unique_users"],
            }

        payload.update({
            "services": services,
            "total_cost_credits": total_credits,
            "total_revenue": mrr,
            "gross_margin": 0,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("metering/summary fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


@router.get("/metering/usage/by-service")
async def get_usage_by_service(
    period: str = Query("this_month", description="Time period"),
    _admin: Dict[str, Any] = Depends(require_admin_user),
):
    """
    Get usage breakdown by service.

    **Query Parameters**:
    - `period`: Time period (this_month, last_month, this_week, today, or Nd format like 7d, 30d)

    **Returns**:
    - REAL usage and credit costs per service from usage_events (same keys
      per service as before: calls / credits / percentage). Only services
      with recorded events appear — nothing is invented into a bucket.
    - `no_data: true` when no usage events exist in the window.
    """
    start, end = _period_bounds(period)
    payload = {
        "period": period,
        "services": {},
        "total_calls": 0,
        "total_credits": 0,
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "aggregated from usage_events; empty until services record usage"
    }
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await _events_by_service(conn, start, end)
        merged = _merge_service_rows(rows)
        if not merged:
            return payload
        total_calls = sum(s["events"] for s in merged.values())
        total_credits = _f(sum(s["credits"] for s in merged.values()), 4)
        payload.update({
            "services": {
                key: {
                    "calls": s["events"],
                    "credits": s["credits"],
                    "percentage": _f(s["credits"] / total_credits * 100) if total_credits > 0
                    else (_f(s["events"] / total_calls * 100) if total_calls > 0 else 0.0),
                }
                for key, s in merged.items()
            },
            "total_calls": total_calls,
            "total_credits": total_credits,
            "no_data": False,
        })
        return payload
    except Exception as e:  # noqa: BLE001
        logger.warning("metering/usage/by-service fell back to no_data: %s: %s", type(e).__name__, e)
        return payload


# ============================================================================
# BILLING ANALYTICS (1 endpoint)
# ============================================================================

@router.get("/billing/analytics/summary")
async def get_billing_analytics_summary(_admin: Dict[str, Any] = Depends(require_admin_user)):
    """
    Get billing analytics summary.

    **Returns**:
    - REAL revenue + subscription metrics from organization_subscriptions —
      identical definitions to /api/v1/billing/analytics/dashboard
      (MRR = sum of active monthly_price, ARR = MRR*12, 30-day growth rate).
    - Cost / profitability / payment sections are NOT tracked anywhere yet:
      they stay zeroed and the payload says so instead of inventing figures
      (this route used to return hardcoded mock numbers, e.g. MRR 15000).
    - `no_data: true` with all-zero values when there are no subscription
      rows or the database is unreachable.
    """
    payload = {
        "revenue": {
            "mrr": 0,
            "arr": 0,
            "total_this_month": 0,
            "growth_rate": 0
        },
        "costs": {
            "infrastructure": 0,
            "llm_api_costs": 0,
            "other_services": 0,
            "total": 0,
            "percentage_of_revenue": 0
        },
        "profitability": {
            "gross_profit": 0,
            "gross_margin_percentage": 0,
            "net_profit": 0,
            "net_margin_percentage": 0
        },
        "payments": {
            "total_invoices": 0,
            "paid_invoices": 0,
            "failed_invoices": 0,
            "success_rate": 0,
            "total_amount_collected": 0,
            "failed_amount": 0
        },
        "subscriptions": {
            "total_active": 0,
            "new_this_month": 0,
            "cancelled_this_month": 0,
            "net_growth": 0
        },
        "calculated_at": datetime.now().isoformat(),
        "no_data": True,
        "note": "costs, profitability, payments and collected revenue are not tracked yet and stay zeroed"
    }

    core = await compute_billing_summary_core()
    if not core or not core.get("has_subscription_rows"):
        return payload

    payload["revenue"].update({
        "mrr": core["mrr"],
        "arr": core["arr"],
        # Collected revenue is not tracked (no payments source) — stays 0.
        "growth_rate": core["growth_rate"],
    })
    payload["subscriptions"].update({
        "total_active": core["total_active_orgs"],
        "new_this_month": core["new_this_month"],
        "cancelled_this_month": core["cancelled_this_month"],
        "net_growth": core["new_this_month"] - core["cancelled_this_month"],
    })
    payload["no_data"] = False
    return payload

# Export router for server.py registration
__all__ = ["router"]
