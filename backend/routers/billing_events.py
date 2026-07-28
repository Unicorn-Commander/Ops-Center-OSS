"""
Cross-Property Billing Events API
===================================
Provides REST endpoints for recording, querying, and reconciling
billing events across all UC-Cloud properties.

Supports both machine-to-machine auth (X-Agent-Key) and session auth.

Author: Billing Events Team
Created: 2026-04-09
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from database.connection import get_db_pool

# Import auth dependencies — same pattern as compute_api.py.
# NOTE: `from server import ...` ALWAYS raises ImportError here (server.py imports this
# router -> circular), so the except branch is the LIVE path. It previously returned a
# fake admin unconditionally, which made verify_agent_or_admin's session fallback INERT —
# a keyless caller (no X-Agent-Key) was treated as admin, so the metering INGEST accepted
# unauthenticated/fake billing events. Map to the standalone auth_dependencies module,
# which enforces real session auth and has no circular-import problem.
try:
    from server import get_current_user, require_admin, get_current_user_optional
except ImportError:
    from auth_dependencies import require_authenticated_user as get_current_user
    from auth_dependencies import require_admin_user as require_admin
    async def get_current_user_optional(request: Request):
        return None

logger = logging.getLogger(__name__)

# Shared secret for service-to-service auth (same key as compute fabric)
GPU_AGENT_KEY = os.environ.get("GPU_AGENT_KEY", "")

# Lago configuration
LAGO_API_KEY = os.environ.get("LAGO_API_KEY", "")
LAGO_API_URL = os.environ.get("LAGO_API_URL", "http://unicorn-lago-api:3000")


async def verify_agent_or_admin(request: Request):
    """Allow access via X-Agent-Key header OR admin session."""
    # Check agent key first
    agent_key = request.headers.get("X-Agent-Key", "")
    if GPU_AGENT_KEY and agent_key == GPU_AGENT_KEY:
        return {"user_id": "agent", "role": "agent"}

    # Fall back to admin session auth (the dashboards read org-wide billing analytics;
    # the ingest's normal caller is the agent-key path above).
    try:
        user = await require_admin(request)
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")


router = APIRouter(
    prefix="/api/v1/billing/events",
    tags=["billing-events"],
    responses={
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)


# =============================================================================
# Pydantic Models
# =============================================================================

class BillingEvent(BaseModel):
    event_type: str
    origin_property: str
    origin_user_id: Optional[str] = None
    origin_org_id: Optional[str] = None
    executed_on_property: Optional[str] = None
    executed_on_node_id: Optional[str] = None
    service_type: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    gpu_seconds: Optional[float] = None
    cost_internal_usd: Optional[float] = None
    cost_provider_usd: Optional[float] = None
    cost_billed_usd: Optional[float] = None
    markup_percent: Optional[float] = None
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BillingEventBatch(BaseModel):
    events: List[BillingEvent]


class BillingEventInput(BaseModel):
    """Accepts either a single event or a batch."""
    event: Optional[BillingEvent] = None
    events: Optional[List[BillingEvent]] = None


# =============================================================================
# Table Setup
# =============================================================================

_tables_ensured = False


async def _ensure_tables(pool):
    """Create billing_events table if it doesn't exist (idempotent)."""
    global _tables_ensured
    if _tables_ensured:
        return
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_events (
                event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                origin_property TEXT NOT NULL,
                origin_user_id UUID,
                origin_org_id UUID,
                executed_on_property TEXT,
                executed_on_node_id TEXT,
                service_type TEXT,
                model TEXT,
                provider TEXT,
                duration_ms INTEGER,
                tokens_in INTEGER,
                tokens_out INTEGER,
                gpu_seconds NUMERIC(12, 4),
                cost_internal_usd NUMERIC(12, 6),
                cost_provider_usd NUMERIC(12, 6),
                cost_billed_usd NUMERIC(12, 6),
                markup_percent NUMERIC(5, 2),
                payload JSONB DEFAULT '{}',
                lago_event_id TEXT,
                lago_status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_events_org ON billing_events(origin_org_id, timestamp)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_events_property ON billing_events(origin_property, timestamp)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_events_type ON billing_events(event_type, timestamp)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_events_lago ON billing_events(lago_status) WHERE lago_status != 'sent'")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_billing_events_executed ON billing_events(executed_on_property, timestamp)")
    _tables_ensured = True
    logger.info("billing_events table ensured")


# =============================================================================
# Lago Integration Helpers
# =============================================================================

# Map event_type to Lago billable metric codes
LAGO_METRIC_MAP = {
    "compute_used": "compute_seconds",
    "external_api_call": "api_calls",
    "storage_billed": "storage_gb_hours",
    "agent_invocation": "agent_runs",
    "app_subscription": "app_subscription_events",
    "llm_inference": "llm_tokens",
    "image_gen": "image_gen_calls",
    "music_gen": "music_gen_calls",
    "embedding": "embedding_tokens",
    "search": "search_queries",
}


async def _send_to_lago(event_id: str, event_type: str, org_id: str, properties: Dict[str, Any]) -> Optional[str]:
    """
    Forward a billing event to Lago's events API.
    Returns the Lago event ID on success, None on failure.
    """
    if not LAGO_API_KEY:
        logger.debug("LAGO_API_KEY not set, skipping Lago forwarding")
        return None

    metric_code = LAGO_METRIC_MAP.get(event_type, event_type)

    lago_payload = {
        "event": {
            "transaction_id": event_id,
            "external_subscription_id": org_id,
            "code": metric_code,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "properties": properties,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LAGO_API_URL}/api/v1/events",
                json=lago_payload,
                headers={
                    "Authorization": f"Bearer {LAGO_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code in (200, 201):
                logger.info("Sent billing event %s to Lago (metric=%s)", event_id, metric_code)
                return event_id
            else:
                logger.warning("Lago returned %d for event %s: %s", resp.status_code, event_id, resp.text[:200])
                return None
    except Exception as e:
        logger.error("Failed to send event %s to Lago: %s", event_id, e)
        return None


# =============================================================================
# Helper: Insert billing event
# =============================================================================

async def emit_billing_event(pool, event_type: str, origin_property: str, origin_org_id: Optional[str] = None, **kwargs) -> str:
    """
    Insert a billing event into the billing_events table.
    Returns the event_id.
    Can be called from other modules (e.g., compute_api) for direct DB insert.
    """
    await _ensure_tables(pool)
    event_id = str(uuid4())

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO billing_events (
                event_id, event_type, origin_property, origin_user_id, origin_org_id,
                executed_on_property, executed_on_node_id, service_type, model, provider,
                duration_ms, tokens_in, tokens_out, gpu_seconds,
                cost_internal_usd, cost_provider_usd, cost_billed_usd, markup_percent,
                payload
            ) VALUES (
                $1::uuid, $2, $3, $4::uuid, $5::uuid,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16, $17, $18,
                $19::jsonb
            )
        """,
            event_id,
            event_type,
            origin_property,
            kwargs.get("origin_user_id"),
            origin_org_id,
            kwargs.get("executed_on_property"),
            kwargs.get("executed_on_node_id"),
            kwargs.get("service_type"),
            kwargs.get("model"),
            kwargs.get("provider"),
            kwargs.get("duration_ms"),
            kwargs.get("tokens_in"),
            kwargs.get("tokens_out"),
            kwargs.get("gpu_seconds"),
            kwargs.get("cost_internal_usd"),
            kwargs.get("cost_provider_usd"),
            kwargs.get("cost_billed_usd"),
            kwargs.get("markup_percent"),
            json.dumps(kwargs.get("payload", {})),
        )

    logger.info("Billing event %s recorded: type=%s property=%s", event_id, event_type, origin_property)
    return event_id


# =============================================================================
# Endpoints
# =============================================================================

@router.post("")
async def create_billing_events(request: Request, auth_user: dict = Depends(verify_agent_or_admin)):
    """
    Record one or more billing events.
    Accepts JSON body with either:
      - {"event": {...}} for a single event
      - {"events": [{...}, ...]} for a batch
    """
    pool = await get_db_pool()
    await _ensure_tables(pool)

    body = await request.json()

    # Normalize to list of events
    events_data = []
    if "events" in body and isinstance(body["events"], list):
        events_data = body["events"]
    elif "event" in body and isinstance(body["event"], dict):
        events_data = [body["event"]]
    elif "event_type" in body:
        # Direct event object at top level
        events_data = [body]
    else:
        raise HTTPException(status_code=400, detail="Provide 'event' or 'events' in request body")

    results = []
    for evt in events_data:
        try:
            event_id = await emit_billing_event(
                pool,
                event_type=evt.get("event_type", "unknown"),
                origin_property=evt.get("origin_property", "unknown"),
                origin_org_id=evt.get("origin_org_id"),
                origin_user_id=evt.get("origin_user_id"),
                executed_on_property=evt.get("executed_on_property"),
                executed_on_node_id=evt.get("executed_on_node_id"),
                service_type=evt.get("service_type"),
                model=evt.get("model"),
                provider=evt.get("provider"),
                duration_ms=evt.get("duration_ms"),
                tokens_in=evt.get("tokens_in"),
                tokens_out=evt.get("tokens_out"),
                gpu_seconds=evt.get("gpu_seconds"),
                cost_internal_usd=evt.get("cost_internal_usd"),
                cost_provider_usd=evt.get("cost_provider_usd"),
                cost_billed_usd=evt.get("cost_billed_usd"),
                markup_percent=evt.get("markup_percent"),
                payload=evt.get("payload", {}),
            )
            results.append({"event_id": event_id, "status": "recorded"})
        except Exception as e:
            logger.error("Failed to record billing event: %s", e)
            results.append({"error": str(e), "status": "failed"})

    return {"recorded": len([r for r in results if r.get("status") == "recorded"]), "results": results}


@router.get("/summary")
async def billing_summary(
    request: Request,
    property: Optional[str] = None,
    org_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_user: dict = Depends(verify_agent_or_admin),
):
    """Aggregated billing summary grouped by property, event_type, service_type."""
    pool = await get_db_pool()
    await _ensure_tables(pool)

    conditions = []
    params = []
    idx = 1

    if property:
        conditions.append(f"origin_property = ${idx}")
        params.append(property)
        idx += 1
    if org_id:
        conditions.append(f"origin_org_id = ${idx}::uuid")
        params.append(org_id)
        idx += 1
    if event_type:
        conditions.append(f"event_type = ${idx}")
        params.append(event_type)
        idx += 1
    if start_date:
        conditions.append(f"timestamp >= ${idx}::timestamptz")
        params.append(start_date)
        idx += 1
    if end_date:
        conditions.append(f"timestamp <= ${idx}::timestamptz")
        params.append(end_date)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            origin_property,
            event_type,
            service_type,
            COUNT(*) as event_count,
            COALESCE(SUM(cost_internal_usd), 0) as total_cost_internal,
            COALESCE(SUM(cost_billed_usd), 0) as total_cost_billed,
            COALESCE(SUM(cost_provider_usd), 0) as total_cost_provider
        FROM billing_events
        {where}
        GROUP BY origin_property, event_type, service_type
        ORDER BY total_cost_billed DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return {
        "groups": [
            {
                "property": r["origin_property"],
                "event_type": r["event_type"],
                "service_type": r["service_type"],
                "event_count": r["event_count"],
                "total_cost_internal": float(r["total_cost_internal"]),
                "total_cost_billed": float(r["total_cost_billed"]),
                "total_cost_provider": float(r["total_cost_provider"]),
            }
            for r in rows
        ],
        "total_groups": len(rows),
    }


@router.get("/by-property")
async def billing_by_property(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_user: dict = Depends(verify_agent_or_admin),
):
    """Per-property breakdown for a date range."""
    pool = await get_db_pool()
    await _ensure_tables(pool)

    conditions = []
    params = []
    idx = 1

    if start_date:
        conditions.append(f"timestamp >= ${idx}::timestamptz")
        params.append(start_date)
        idx += 1
    if end_date:
        conditions.append(f"timestamp <= ${idx}::timestamptz")
        params.append(end_date)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            origin_property,
            COUNT(*) as total_events,
            COALESCE(SUM(cost_internal_usd), 0) as total_cost_internal,
            COALESCE(SUM(cost_billed_usd), 0) as total_cost_billed,
            COALESCE(SUM(gpu_seconds), 0) as total_gpu_seconds,
            COALESCE(SUM(tokens_in), 0) + COALESCE(SUM(tokens_out), 0) as total_tokens
        FROM billing_events
        {where}
        GROUP BY origin_property
        ORDER BY total_cost_billed DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return {
        "properties": [
            {
                "property": r["origin_property"],
                "total_events": r["total_events"],
                "total_cost_internal": float(r["total_cost_internal"]),
                "total_cost_billed": float(r["total_cost_billed"]),
                "total_gpu_seconds": float(r["total_gpu_seconds"]),
                "total_tokens": int(r["total_tokens"]),
            }
            for r in rows
        ],
    }


@router.get("/by-org/{org_id}")
async def billing_by_org(
    org_id: str,
    request: Request,
    auth_user: dict = Depends(verify_agent_or_admin),
):
    """Usage breakdown for a specific organization, grouped by event_type and service_type."""
    pool = await get_db_pool()
    await _ensure_tables(pool)

    query = """
        SELECT
            event_type,
            service_type,
            COUNT(*) as event_count,
            COALESCE(SUM(cost_internal_usd), 0) as total_cost_internal,
            COALESCE(SUM(cost_billed_usd), 0) as total_cost_billed,
            COALESCE(SUM(cost_provider_usd), 0) as total_cost_provider,
            COALESCE(SUM(tokens_in), 0) as total_tokens_in,
            COALESCE(SUM(tokens_out), 0) as total_tokens_out,
            COALESCE(SUM(gpu_seconds), 0) as total_gpu_seconds,
            COALESCE(SUM(duration_ms), 0) as total_duration_ms
        FROM billing_events
        WHERE origin_org_id = $1::uuid
        GROUP BY event_type, service_type
        ORDER BY total_cost_billed DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, org_id)

    return {
        "org_id": org_id,
        "breakdown": [
            {
                "event_type": r["event_type"],
                "service_type": r["service_type"],
                "event_count": r["event_count"],
                "total_cost_internal": float(r["total_cost_internal"]),
                "total_cost_billed": float(r["total_cost_billed"]),
                "total_cost_provider": float(r["total_cost_provider"]),
                "total_tokens_in": int(r["total_tokens_in"]),
                "total_tokens_out": int(r["total_tokens_out"]),
                "total_gpu_seconds": float(r["total_gpu_seconds"]),
                "total_duration_ms": int(r["total_duration_ms"]),
            }
            for r in rows
        ],
    }


@router.get("/markup-revenue")
async def markup_revenue(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auth_user: dict = Depends(verify_agent_or_admin),
):
    """Markup revenue collected from external API calls, grouped by provider."""
    pool = await get_db_pool()
    await _ensure_tables(pool)

    conditions = ["cost_provider_usd IS NOT NULL", "cost_billed_usd IS NOT NULL"]
    params = []
    idx = 1

    if start_date:
        conditions.append(f"timestamp >= ${idx}::timestamptz")
        params.append(start_date)
        idx += 1
    if end_date:
        conditions.append(f"timestamp <= ${idx}::timestamptz")
        params.append(end_date)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}"

    query = f"""
        SELECT
            provider,
            COUNT(*) as event_count,
            COALESCE(SUM(cost_provider_usd), 0) as total_cost_provider,
            COALESCE(SUM(cost_billed_usd), 0) as total_cost_billed,
            COALESCE(SUM(cost_billed_usd), 0) - COALESCE(SUM(cost_provider_usd), 0) as markup_collected
        FROM billing_events
        {where}
        GROUP BY provider
        ORDER BY markup_collected DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return {
        "providers": [
            {
                "provider": r["provider"],
                "event_count": r["event_count"],
                "cost_provider_usd": float(r["total_cost_provider"]),
                "cost_billed_usd": float(r["total_cost_billed"]),
                "markup_collected": float(r["markup_collected"]),
            }
            for r in rows
        ],
    }


@router.post("/reconcile")
async def reconcile_lago(
    request: Request,
    auth_user: dict = Depends(verify_agent_or_admin),
):
    """
    Admin endpoint: find all events with lago_status='pending' and forward them to Lago.
    Returns count of sent/failed.
    """
    # Only allow admin users (not just agent key)
    if auth_user.get("role") not in ("admin", "agent"):
        raise HTTPException(status_code=403, detail="Admin access required")

    pool = await get_db_pool()
    await _ensure_tables(pool)

    async with pool.acquire() as conn:
        pending = await conn.fetch("""
            SELECT event_id, event_type, origin_org_id, service_type, model, provider,
                   tokens_in, tokens_out, gpu_seconds, cost_billed_usd, duration_ms
            FROM billing_events
            WHERE lago_status = 'pending'
            ORDER BY timestamp ASC
            LIMIT 500
        """)

    sent = 0
    failed = 0

    for row in pending:
        event_id = str(row["event_id"])
        org_id = str(row["origin_org_id"]) if row["origin_org_id"] else None

        if not org_id:
            # Can't send to Lago without an org/subscription ID
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE billing_events SET lago_status = 'skipped' WHERE event_id = $1::uuid",
                    event_id,
                )
            continue

        properties = {
            "service_type": row["service_type"] or "",
            "model": row["model"] or "",
            "provider": row["provider"] or "",
            "tokens_in": row["tokens_in"] or 0,
            "tokens_out": row["tokens_out"] or 0,
            "gpu_seconds": float(row["gpu_seconds"]) if row["gpu_seconds"] else 0,
            "cost_billed_usd": float(row["cost_billed_usd"]) if row["cost_billed_usd"] else 0,
            "duration_ms": row["duration_ms"] or 0,
        }

        lago_id = await _send_to_lago(event_id, row["event_type"], org_id, properties)

        async with pool.acquire() as conn:
            if lago_id:
                await conn.execute("""
                    UPDATE billing_events
                    SET lago_status = 'sent', lago_event_id = $2
                    WHERE event_id = $1::uuid
                """, event_id, lago_id)
                sent += 1
            else:
                await conn.execute("""
                    UPDATE billing_events
                    SET lago_status = 'failed', retry_count = retry_count + 1
                    WHERE event_id = $1::uuid
                """, event_id)
                failed += 1

    return {"sent": sent, "failed": failed, "skipped": len(pending) - sent - failed, "total_pending": len(pending)}
