"""
Metered Compute API — Lago billing for non-LLM local models
============================================================

Meters non-LLM local compute that does NOT transit ops-center — currently
STT and TTS (the voice plane on another box) — through the EXISTING federation
metering rail (`FederationMeter.record_usage` → `_report_to_lago`, keyed
`external_subscription_id = org_id`, with the `gateway_metered` double-bill
guard), with unit-based billable metrics:

    STT         → metric `stt_audio_seconds`     (unit: audio_seconds)
    TTS         → metric `tts_characters`        (unit: characters)

Entry: a service reports unit counts via POST /api/v1/metered/report with a
service key (audio/text never transits ops-center).

NOTE: embeddings + reranking are metered the other way — they ride the public
litellm gateway (`llm.unicorncommander.ai`) and bill as `ai_api_call` via the
litellm cost map + the plan markup. The earlier embeddings/rerank proxy routes
here were retired 2026-06-19 (redundant with the gateway path).

Exempt tiers (free / on-device / vip / internal — see CREDIT_EXEMPT_TIERS)
are not metered. Collect-don't-gate: we meter usage but never block the call.

Register the Lago billable metrics once with
`scripts/register_metering_metrics.py`.

Created: 2026-06-18
"""

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metered", tags=["Metered Compute"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Service-to-service key for the /report bridge. Reuse the federation key by
# default so the voice plane can authenticate without a new secret.
METERING_SERVICE_KEY = os.getenv("METERING_SERVICE_KEY", "") or os.getenv("FEDERATION_KEY", "")

LAGO_API_URL = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")

BILLING_ENABLED = os.getenv("BILLING_ENABLED", "true").lower() == "true"
CREDIT_EXEMPT_TIERS = set(
    t.strip()
    for t in os.getenv(
        "CREDIT_EXEMPT_TIERS",
        "free,vip_founder,vip,founder,founder_friend,admin,unlimited,internal",
    ).split(",")
    if t.strip()
)

_LOCAL_NODE_ID = os.getenv("FEDERATION_NODE_ID", "ops-center")

# service_type -> (metric_code, unit_name, cost_per_unit_usd)
# Cost basis from the scoping handoff (2026-06-17). The Lago plan charge is
# the source of truth for price; cost_usd here feeds cost dashboards only.
_METRICS: Dict[str, Dict[str, Any]] = {
    "stt":        {"metric": "stt_audio_seconds", "unit": "audio_seconds", "cost_per_unit": 0.004 / 60.0},
    "tts":        {"metric": "tts_characters",    "unit": "characters", "cost_per_unit": 15.0 / 1_000_000},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_exempt(tier: Optional[str]) -> bool:
    if not BILLING_ENABLED:
        return True
    if "*" in CREDIT_EXEMPT_TIERS:
        return True
    return (tier or "unknown") in CREDIT_EXEMPT_TIERS


async def _get_meter():
    """Build a FederationMeter pointed at the canonical Lago target.

    Uses the same `FEDERATION_LAGO_API_URL/KEY` platform_settings override the
    rest of the federation rail uses, so a node whose local LAGO_* env points
    at a local Lago (e.g. bigboy, whose local key 401s) relays billing to the
    UC-1 Hub instead of failing.
    """
    from database.connection import get_db_pool
    from federation.metering import FederationMeter
    try:
        pool = await get_db_pool()
    except Exception:
        pool = None
    try:
        from federation.agent_bridge import _resolve_lago_creds
        lago_url, lago_key = await _resolve_lago_creds(pool)
    except Exception:
        lago_url, lago_key = LAGO_API_URL, os.getenv("LAGO_API_KEY", "")
    return FederationMeter(pool, lago_url=lago_url, lago_api_key=lago_key)


async def _resolve_org(user_id: str) -> tuple[Optional[str], Optional[str]]:
    """Resolve (org_id, plan_tier) for a user via their active org membership."""
    from database.connection import get_db_pool
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT o.id::text AS org_id, o.plan_tier
                FROM organizations o
                JOIN organization_members om ON om.org_id = o.id
                WHERE om.user_id = $1 AND COALESCE(o.status, 'active') = 'active'
                ORDER BY (o.plan_tier IS NOT NULL) DESC
                LIMIT 1
                """,
                user_id,
            )
            if row:
                return row["org_id"], row["plan_tier"]
    except Exception as exc:
        logger.warning("[metered] org resolution failed for %s: %s", user_id, exc)
    return None, None


async def _tier_for_org(org_id: str) -> Optional[str]:
    from database.connection import get_db_pool
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT plan_tier FROM organizations WHERE id = $1", org_id)
            if row:
                return row["plan_tier"]
    except Exception as exc:
        logger.warning("[metered] tier lookup failed for org %s: %s", org_id, exc)
    return None


async def _meter(service_type: str, org_id: str, quantity: float, metadata: Dict[str, Any]) -> Optional[str]:
    """Emit one Lago billable event for a non-LLM compute unit. Returns event_id."""
    spec = _METRICS[service_type]
    cost = float(quantity) * spec["cost_per_unit"]
    meter = await _get_meter()
    result = await meter.record_usage({
        "source_node_id": _LOCAL_NODE_ID,
        "target_node_id": _LOCAL_NODE_ID,
        "service_type": service_type,
        "event_type": "inference",
        "org_id": org_id,
        "cost_usd": cost,
        "gateway_metered": False,
        "billing_metric": spec["metric"],
        "billing_quantity": quantity,
        "billing_unit": spec["unit"],
        "metadata": metadata,
    })
    return result.get("event_id")


# ---------------------------------------------------------------------------
# Report bridge — STT / TTS (and any service) report unit counts
# ---------------------------------------------------------------------------

class MeterReport(BaseModel):
    service_type: str            # "stt" | "tts" | "embeddings" | "rerank"
    quantity: float              # audio_seconds | characters | tokens | searches
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/report")
async def report_usage(report: MeterReport, request: Request):
    """
    Service-to-service usage report for compute that doesn't transit ops-center
    (e.g. STT/TTS on the voice box). Authenticated with the metering service key.
    """
    key = request.headers.get("X-Metering-Key", "")
    if not METERING_SERVICE_KEY or key != METERING_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing metering service key")

    st = report.service_type.strip().lower()
    if st not in _METRICS:
        raise HTTPException(status_code=422, detail=f"service_type must be one of {sorted(_METRICS)}")
    if report.quantity is None or report.quantity < 0:
        raise HTTPException(status_code=422, detail="quantity must be >= 0")

    org_id = report.org_id
    if not org_id and report.user_id:
        org_id, _ = await _resolve_org(report.user_id)
    if not org_id:
        raise HTTPException(status_code=422, detail="org_id (or a resolvable user_id) is required")

    tier = await _tier_for_org(org_id)
    if _is_exempt(tier):
        logger.debug("[metered] exempt tier '%s' (org=%s) — %s report not metered", tier, org_id, st)
        return {"status": "skipped_exempt", "org_id": org_id, "tier": tier}

    meta = dict(report.metadata or {})
    meta.update({"model": report.model or "", "user_id": report.user_id, "via": "report_bridge"})
    event_id = await _meter(st, org_id, report.quantity, meta)
    return {"status": "recorded", "event_id": event_id, "metric": _METRICS[st]["metric"],
            "quantity": report.quantity, "unit": _METRICS[st]["unit"], "org_id": org_id}


@router.get("/health")
async def metered_health():
    return {
        "status": "healthy",
        "metrics": {k: v["metric"] for k, v in _METRICS.items()},
        "billing_enabled": BILLING_ENABLED,
        "report_bridge_key_configured": bool(METERING_SERVICE_KEY),
    }
