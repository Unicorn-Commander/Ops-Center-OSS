"""
Internal LLM preflight API — gateway-callable local-pricing decision
====================================================================

The public LiteLLM gateway (`uchub-litellm`) is network-isolated from the
credit wallet + the local-token counter, so it cannot decide local pricing on
its own. It calls THIS endpoint (reachable at ops-center-direct:8084 on
uchub-network) from a CustomLogger.async_pre_call_hook to get a decision:

  POST /api/v1/internal/llm/preflight
      {org_id, model, est_tokens}  ->  {decision, model, is_local, reason}
        decision: allow    -> serve `model`
                  overflow -> serve `model` (the paid overflow model) instead
                  deny     -> reject (429)

  POST /api/v1/internal/llm/record-local-tokens
      {org_id, tokens}     ->  records served LOCAL tokens to the monthly quota

Auth: a shared service key (X-Internal-Key == INTERNAL_LLM_KEY, falling back to
FEDERATION_KEY so no new secret is required). The gateway is the only caller.

Everything FAILS OPEN: on any internal error the preflight returns an `allow`
for the requested model, so a transient ops-center blip never blocks paid
gateway traffic. Inert in practice until LOCAL_PRICING_ENABLED is turned on
(resolve_local_pricing passes through when disabled).
"""

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/internal/llm", tags=["Internal LLM"])

INTERNAL_LLM_KEY = os.getenv("INTERNAL_LLM_KEY", "") or os.getenv("FEDERATION_KEY", "")

# Gateway models that run on OUR OWN infrastructure (org-local) but are reached
# THROUGH the gateway, so the host node (e.g. commander, a VPS) has no local
# llm_models row for them. "local" = org-owned compute, NOT physical co-location:
# uc/chat-default -> bigboy 3090, uc/chat-local-p40 -> midboy P40. Third-party
# cloud rungs (deepseek-*, or/*) are NOT matched, so they bill as cloud.
LOCAL_GATEWAY_PREFIXES = tuple(
    p.strip() for p in os.getenv("LOCAL_GATEWAY_MODEL_PREFIXES", "uc/").split(",") if p.strip()
)
LOCAL_GATEWAY_MODELS = set(
    m.strip() for m in os.getenv("LOCAL_GATEWAY_MODELS", "").split(",") if m.strip()
)


def _check_key(request: Request) -> None:
    key = request.headers.get("X-Internal-Key", "")
    if not INTERNAL_LLM_KEY or key != INTERNAL_LLM_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing internal service key")


async def _tier_for_org(org_id: str) -> Optional[str]:
    from database import get_db_connection
    try:
        async with await get_db_connection() as conn:
            row = await conn.fetchrow("SELECT plan_tier FROM organizations WHERE id = $1", org_id)
            return row["plan_tier"] if row else None
    except Exception as exc:
        logger.warning("[preflight] tier lookup failed for org %s: %s", org_id, exc)
        return None


async def _is_local_model(model: str) -> bool:
    """Authoritative local check. Two sources:
    1. Declared org-local gateway models (uc/* etc.) — own GPUs reached via the
       gateway, with no local llm_models row on a VPS host like commander.
    2. The model's provider record (same logic as the inline chat path) — for
       nodes that DO have local-provider models (e.g. bigboy's Qwen3-30B)."""
    if model in LOCAL_GATEWAY_MODELS or (LOCAL_GATEWAY_PREFIXES and model.startswith(LOCAL_GATEWAY_PREFIXES)):
        return True
    from database import get_db_connection
    try:
        async with await get_db_connection() as conn:
            prov = await conn.fetchrow(
                """
                SELECT p.type, p.api_base_url
                FROM llm_models m JOIN llm_providers p ON m.provider_id = p.id
                WHERE m.name = $1 AND m.enabled = true AND p.enabled = true
                """,
                model,
            )
            if not prov:
                return False
            base = prov["api_base_url"] or ""
            return prov["type"] in ("openai_compatible", "local") and (
                base.startswith("http://") or "localhost" in base or "unicorn-" in base
            )
    except Exception as exc:
        logger.warning("[preflight] is_local lookup failed for %s: %s", model, exc)
        return False


class PreflightRequest(BaseModel):
    org_id: str
    model: str
    est_tokens: int = 0


@router.post("/preflight")
async def preflight(req: PreflightRequest, request: Request):
    _check_key(request)
    # Fail-open default: serve the requested model unchanged.
    fallback = {"decision": "allow", "model": req.model, "is_local": False, "reason": "failopen"}
    try:
        is_local = await _is_local_model(req.model)
        if not is_local:
            return {"decision": "allow", "model": req.model, "is_local": False, "reason": "cloud"}
        tier = await _tier_for_org(req.org_id)
        from local_pricing import resolve_local_pricing
        decision = await resolve_local_pricing(
            req.org_id, req.model, req.est_tokens,
            tier_code=tier or "", is_local=True,
        )
        return {
            "decision": decision["decision"],
            "model": decision["model"],
            "is_local": decision["is_local"],
            "reason": decision["reason"],
        }
    except Exception as exc:
        logger.warning("[preflight] error (fail-open allow) org=%s model=%s: %s", req.org_id, req.model, exc)
        return fallback


class RecordRequest(BaseModel):
    org_id: str
    tokens: int
    model: Optional[str] = None   # if given, only count when the model is local


@router.post("/record-local-tokens")
async def record_local_tokens(req: RecordRequest, request: Request):
    _check_key(request)
    try:
        # The gateway can't tell local from cloud, so it passes the served model
        # and we filter here — only LOCAL usage counts against the local quota.
        if req.model is not None and not await _is_local_model(req.model):
            return {"status": "skipped_cloud", "org_id": req.org_id, "model": req.model}
        from local_quota import add_local_tokens
        await add_local_tokens(req.org_id, req.tokens)
        return {"status": "recorded", "org_id": req.org_id, "tokens": req.tokens}
    except Exception as exc:
        logger.warning("[preflight] record failed org=%s: %s", req.org_id, exc)
        return {"status": "skipped", "reason": str(exc)}


@router.get("/preflight/health")
async def preflight_health():
    return {
        "status": "healthy",
        "service_key_configured": bool(INTERNAL_LLM_KEY),
        "local_pricing_enabled": os.getenv("LOCAL_PRICING_ENABLED", "false"),
    }
