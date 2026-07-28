"""
UC local-pricing gateway hook (LiteLLM CustomLogger)
====================================================

Mounted into the public LiteLLM gateway (`uchub-litellm`) and registered via
`litellm_settings.callbacks: ["uc_pricing_hook.proxy_handler_instance"]`.

Because the gateway is network-isolated from the credit wallet + the monthly
local-token counter, this hook does NOT decide pricing itself — it asks
ops-center (reachable at OPS_CENTER_URL on uchub-network) via the internal
preflight endpoint, then:
  * decision "deny"     -> reject the call (HTTP 429),
  * decision "overflow" -> rewrite data["model"] to the paid overflow model,
  * decision "allow"    -> pass through unchanged.
On the success event it reports the served token count back so local usage
counts toward the org's monthly quota (ops-center filters cloud out).

FAIL-OPEN: any error talking to ops-center serves the request unchanged — a
transient ops-center blip must never block paid gateway traffic. The hook is
also effectively inert until LOCAL_PRICING_ENABLED is on in ops-center
(preflight returns "allow" while disabled).

Deploy: copy to commander:/home/muut/UC-1-Hub/config/uc_pricing_hook.py,
ensure that dir is importable by litellm, add to litellm_settings.callbacks,
and set OPS_CENTER_URL + INTERNAL_LLM_KEY in the uchub-litellm compose
environment block (litellm only sees env listed there), then recreate the
container.
"""

import os
import logging

import httpx
from litellm.integrations.custom_logger import CustomLogger
from litellm.proxy._types import UserAPIKeyAuth
from fastapi import HTTPException

logger = logging.getLogger(__name__)

OPS_CENTER_URL = os.getenv("OPS_CENTER_URL", "http://ops-center-direct:8084").rstrip("/")
INTERNAL_LLM_KEY = os.getenv("INTERNAL_LLM_KEY", "") or os.getenv("FEDERATION_KEY", "")
PREFLIGHT_TIMEOUT = float(os.getenv("UC_PREFLIGHT_TIMEOUT", "2.0"))

_COMPLETION_CALLS = {"completion", "acompletion", "chat_completion", "text_completion"}


def _estimate_tokens(data: dict) -> int:
    """Cheap prompt-size estimate (words * 1.5), matching the inline path."""
    try:
        msgs = data.get("messages") or []
        words = sum(len(str(m.get("content") or "").split()) for m in msgs)
        if not words and data.get("prompt"):
            words = len(str(data["prompt"]).split())
        return int(words * 1.5)
    except Exception:
        return 0


class UCPricingHook(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache, data: dict, call_type: str):
        if call_type not in _COMPLETION_CALLS:
            return data
        org_id = getattr(user_api_key_dict, "user_id", None)  # per-org key: user_id == org_id
        model = data.get("model")
        if not org_id or not model or not INTERNAL_LLM_KEY:
            return data
        try:
            async with httpx.AsyncClient(timeout=PREFLIGHT_TIMEOUT) as client:
                resp = await client.post(
                    f"{OPS_CENTER_URL}/api/v1/internal/llm/preflight",
                    json={"org_id": org_id, "model": model, "est_tokens": _estimate_tokens(data)},
                    headers={"X-Internal-Key": INTERNAL_LLM_KEY},
                )
            d = resp.json()
            decision = d.get("decision")
            if decision == "deny":
                raise HTTPException(
                    status_code=429,
                    detail="Local AI usage limit reached for your plan. Upgrade or wait for the monthly reset.",
                )
            if decision == "overflow" and d.get("model"):
                logger.info("[uc_pricing] org=%s overflow %s -> %s", org_id, model, d["model"])
                data["model"] = d["model"]
        except HTTPException:
            raise
        except Exception as exc:  # fail-open
            logger.warning("[uc_pricing] preflight failed (fail-open serve): %s", exc)
        return data

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            key_obj = (kwargs.get("litellm_params", {}) or {}).get("metadata", {}) or {}
            org_id = key_obj.get("user_api_key_user_id")
            model = kwargs.get("model")
            usage = getattr(response_obj, "usage", None) or {}
            total = int(getattr(usage, "total_tokens", 0) or (usage.get("total_tokens", 0) if isinstance(usage, dict) else 0) or 0)
            if not org_id or not model or total <= 0 or not INTERNAL_LLM_KEY:
                return
            async with httpx.AsyncClient(timeout=PREFLIGHT_TIMEOUT) as client:
                await client.post(
                    f"{OPS_CENTER_URL}/api/v1/internal/llm/record-local-tokens",
                    json={"org_id": org_id, "tokens": total, "model": model},
                    headers={"X-Internal-Key": INTERNAL_LLM_KEY},
                )
        except Exception as exc:
            logger.debug("[uc_pricing] usage record skipped: %s", exc)


proxy_handler_instance = UCPricingHook()
