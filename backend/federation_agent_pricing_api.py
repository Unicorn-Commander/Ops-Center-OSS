"""
Federation Agent Pricing API — admin editor for FEDERATION_AGENT_PRICING.

The federated agent-invoke path (federation/agent_bridge.py) prices each
``agent_invocation`` Lago event from the platform_settings key
``FEDERATION_AGENT_PRICING`` — a JSON object of the shape::

    {"default": <units>, "<agent-id>": <units>, ...}

``default`` applies to any agent without an explicit price; absent/empty/
unparseable config falls back to ``{"default": 1}``. A "unit" is priced by
the Lago plan charge on the metric (same philosophy as ai_api_call: raw
usage in the event, money decided at the plan). This module is the admin
*writer* for that key — it does not change the read shape or key name.

Endpoints (prefix /api/v1/admin/agent-pricing):
  GET  /                -> current pricing dict (default {"default": 1})
  PUT  /                -> validate + upsert the pricing dict (audited)
  GET  /agent-choices   -> best-effort local agent ids for UI suggestions

Security:
  All endpoints require admin authentication (same Redis/browser session
  used by the other admin pages — copied from federation_settings_api.py).

Author: Backend Development Team
Date: June 2026
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/agent-pricing",
    tags=["Federation Agent Pricing"],
)

# The platform_settings key consumed by federation/agent_bridge.py — do NOT
# rename. The matching read lives in agent_bridge._agent_unit_price().
PRICING_KEY = "FEDERATION_AGENT_PRICING"
PRICING_CATEGORY = "federation"
DEFAULT_PRICING: Dict[str, float] = {"default": 1}


# ============================================================================
# Admin auth (copied from federation_settings_api.require_admin)
# ============================================================================

async def require_admin(request: Request):
    """Verify admin access using the same Redis/browser session used by admin pages."""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    user = getattr(request, "session", {}).get("user", {}) if hasattr(request, "session") else {}
    session_token = request.cookies.get("session_token")

    if not user and session_token:
        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        sessions = RedisSessionManager(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
        if session_token in sessions:
            user = sessions[session_token].get("user", {})

    is_admin = (
        user.get("role") == "admin"
        or user.get("is_admin") is True
        or user.get("is_superuser") is True
        or "admin" in user.get("groups", [])
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state."""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Pydantic models
# ============================================================================

class AgentPricingResponse(BaseModel):
    """Current agent pricing map."""
    pricing: Dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_PRICING))


class AgentPricingUpdate(BaseModel):
    """Replacement pricing map: {"default": n, "<agent-id>": n, ...}.

    Accepts an arbitrary set of agent-id keys; values are validated in the
    handler (every value a number >= 0; ``default`` filled to 1 if omitted).
    """
    pricing: Dict[str, Any]


class AgentChoice(BaseModel):
    agent_id: str
    node_id: str = ""
    node_name: str = ""


# ============================================================================
# Helpers
# ============================================================================

async def _read_pricing(pool: asyncpg.Pool) -> Dict[str, float]:
    """Read + parse the stored pricing map, defaulting safely.

    Mirrors federation/agent_bridge._agent_unit_price(): a missing row,
    empty value, or unparseable JSON yields the default map. Non-numeric
    stored values are coerced/dropped defensively so a hand-edited row
    can never break the editor.
    """
    raw = None
    try:
        raw = await pool.fetchval(
            "SELECT value FROM platform_settings WHERE key = $1", PRICING_KEY
        )
    except Exception as exc:  # table may not exist yet on a fresh node
        logger.warning("platform_settings read failed for %s (using default): %s", PRICING_KEY, exc)
        return dict(DEFAULT_PRICING)

    if not raw:
        return dict(DEFAULT_PRICING)

    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        logger.warning("%s is not valid JSON (using default)", PRICING_KEY)
        return dict(DEFAULT_PRICING)

    if not isinstance(parsed, dict):
        return dict(DEFAULT_PRICING)

    cleaned: Dict[str, float] = {}
    for key, val in parsed.items():
        try:
            cleaned[str(key)] = float(val)
        except (TypeError, ValueError):
            continue  # drop a malformed entry rather than 500

    cleaned.setdefault("default", 1.0)
    return cleaned


def _validate_pricing(pricing: Dict[str, Any]) -> Dict[str, float]:
    """Validate + normalize an incoming pricing map.

    Rules: every value must be a real number >= 0; ``default`` is required
    (filled to 1 if omitted); empty/whitespace agent-id keys are rejected.
    Raises HTTP 422 on any violation.
    """
    if not isinstance(pricing, dict):
        raise HTTPException(status_code=422, detail="pricing must be a JSON object")

    cleaned: Dict[str, float] = {}
    for key, val in pricing.items():
        agent_id = str(key).strip()
        if not agent_id:
            raise HTTPException(status_code=422, detail="Empty agent id is not allowed")
        # Reject bools (bool is an int subclass) and non-numeric values.
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise HTTPException(
                status_code=422,
                detail=f"Price for '{agent_id}' must be a number (got {type(val).__name__})",
            )
        fval = float(val)
        if fval < 0:
            raise HTTPException(
                status_code=422,
                detail=f"Price for '{agent_id}' must be >= 0 (got {fval})",
            )
        cleaned[agent_id] = fval

    # default is required by the consumer; default it to 1 if not supplied.
    cleaned.setdefault("default", 1.0)
    return cleaned


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=AgentPricingResponse)
async def get_agent_pricing(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Return the current FEDERATION_AGENT_PRICING map (default {"default": 1})."""
    pool = await get_db_pool(request)
    pricing = await _read_pricing(pool)
    return AgentPricingResponse(pricing=pricing)


@router.put("/", response_model=AgentPricingResponse)
async def update_agent_pricing(
    body: AgentPricingUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Validate and persist the agent pricing map (stored as a JSON string).

    Upserts platform_settings on key FEDERATION_AGENT_PRICING. Audited
    before/after.
    """
    pool = await get_db_pool(request)

    before = await _read_pricing(pool)
    new_pricing = _validate_pricing(body.pricing)

    try:
        await pool.execute(
            """
            INSERT INTO platform_settings (key, value, category, is_secret, updated_at)
            VALUES ($1, $2, $3, FALSE, $4)
            ON CONFLICT (key) DO UPDATE
              SET value = EXCLUDED.value,
                  category = EXCLUDED.category,
                  is_secret = EXCLUDED.is_secret,
                  updated_at = EXCLUDED.updated_at
            """,
            PRICING_KEY,
            json.dumps(new_pricing),
            PRICING_CATEGORY,
            datetime.utcnow(),
        )
    except Exception as exc:
        logger.error("Failed to persist %s: %s", PRICING_KEY, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save agent pricing: {exc}")

    # Audit the change (before/after) — every write is audited.
    try:
        from audit_logger import audit_logger
        await audit_logger.log(
            action="federation.agent_pricing.update",
            result="success",
            user_id=admin_user.get("id") or admin_user.get("sub"),
            username=admin_user.get("username") or admin_user.get("email"),
            resource_type="platform_setting",
            resource_id=PRICING_KEY,
            metadata={"before": before, "after": new_pricing},
        )
    except Exception as exc:  # auditing must never fail the write
        logger.warning("Audit log for agent pricing update failed: %s", exc)

    logger.info(
        "Agent pricing updated by %s: %s",
        admin_user.get("email") or admin_user.get("username") or "unknown",
        new_pricing,
    )
    return AgentPricingResponse(pricing=new_pricing)


@router.get("/agent-choices", response_model=List[AgentChoice])
async def get_agent_choices(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Best-effort list of local agent ids for UI suggestions.

    Tries the federation service catalog (local node's Brigade agents). The
    UI accepts free-form ids, so any failure here returns [] rather than
    erroring — never block the editor on agent discovery.
    """
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return []

    try:
        from federation.node_registry import NodeRegistry  # type: ignore

        registry = NodeRegistry(db_pool=pool)
        catalog = await registry.get_service_catalog(service_type="agents")
    except Exception as exc:
        logger.debug("Agent-choices catalog lookup unavailable: %s", exc)
        return []

    choices: List[AgentChoice] = []
    seen = set()
    for service in (catalog or []):
        if service.get("service_type") != "agents":
            continue
        node_id = service.get("node_id", "")
        node_name = service.get("node_name", "")
        for agent_id in service.get("models", []) or []:
            if agent_id in seen:
                continue
            seen.add(agent_id)
            choices.append(AgentChoice(agent_id=agent_id, node_id=node_id, node_name=node_name))

    return choices
