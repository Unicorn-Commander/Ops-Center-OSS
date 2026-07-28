"""
Per-tier local-LLM pricing decision (system of record)
======================================================

ONE function — `resolve_local_pricing` — decides, for a given org + requested model,
how a LOCAL inference request should be priced/routed. Both inference paths use it:

  * the inline ops-center path (backend/litellm_api.py) calls it in-process, and
  * the public LiteLLM gateway calls it via the internal preflight endpoint
    (backend/internal_llm_preflight_api.py) — because the gateway is network-isolated
    from the wallet + the counter, ops-center is the only place that can decide.

Three modes (per subscription_tiers.local_pricing_mode, migration core/0008):
  free_unlimited       -> serve local, free (today's behavior; the default)
  free_quota_overflow  -> free local up to local_monthly_token_quota tokens this month,
                          then route to local_overflow_model (billed as cloud). If no
                          overflow model is configured it DEGRADES to free (never denies
                          — denying a paying customer is the cardinal sin; Risk table).
  metered              -> serve local, priced at local_token_rate_per_1k (counts against
                          the credit wallet via calculate_cost(local_rate_per_1k=...)).

SAFETY:
  * Hard-gated by env LOCAL_PRICING_ENABLED (default "false"): when off, ALWAYS passthrough
    (exactly today's behavior) — so this module is inert until an operator opts in.
  * is_local is AUTHORITATIVE and supplied by the caller from the resolved provider record
    (never inferred from the model string — see Risk B in litellm_credit_system.py).
  * FAIL-OPEN: any error resolving tier/quota returns a passthrough ALLOW. We never block
    or overflow a request because of an internal lookup failure.
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Decision constants
ALLOW = "allow"        # serve the requested (local) model as-is
OVERFLOW = "overflow"  # serve the configured paid model instead (bill as cloud)
DENY = "deny"          # reject (429) — only reachable in modes that explicitly opt in


def _enabled() -> bool:
    return os.getenv("LOCAL_PRICING_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")


def _passthrough(model: str, *, is_local: bool, reason: str) -> Dict[str, Any]:
    """The today's-behavior result: serve the requested model, free if local."""
    return {
        "decision": ALLOW,
        "model": model,
        "is_local": is_local,
        "local_rate_per_1k": None,
        "meter": False,
        "reason": reason,
    }


async def _load_tier_pricing(tier_code: str) -> Optional[Dict[str, Any]]:
    from database import get_db_connection
    async with await get_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT COALESCE(local_pricing_mode, 'free_unlimited') AS mode,
                   local_monthly_token_quota AS quota,
                   local_overflow_model       AS overflow_model,
                   COALESCE(local_token_rate_per_1k, 0.0) AS rate
            FROM subscription_tiers
            WHERE tier_code = $1
            """,
            tier_code,
        )
        return dict(row) if row else None


async def resolve_local_pricing(
    org_id: Optional[str],
    requested_model: str,
    est_tokens: int,
    *,
    tier_code: str,
    is_local: bool,
) -> Dict[str, Any]:
    """Decide how to price/route a (possibly local) inference request.

    Returns a dict: {decision, model, is_local, local_rate_per_1k, meter, reason}.
      - decision == ALLOW: serve `model`; if `meter` and `local_rate_per_1k` is set,
        the caller prices it via calculate_cost(is_local=True, local_rate_per_1k=...).
      - decision == OVERFLOW: serve `model` (the paid overflow model); `is_local` is
        False so the caller bills it at the normal cloud rate.
      - decision == DENY: reject with 429.
    """
    # Cloud requests are never affected by local pricing.
    if not is_local:
        return _passthrough(requested_model, is_local=False, reason="cloud")

    # Inert unless explicitly enabled.
    if not _enabled():
        return _passthrough(requested_model, is_local=True, reason="disabled")

    try:
        tier = await _load_tier_pricing(tier_code) if tier_code else None
        if not tier:
            return _passthrough(requested_model, is_local=True, reason="no_tier")

        mode = tier["mode"]

        if mode == "free_unlimited":
            return _passthrough(requested_model, is_local=True, reason="free_unlimited")

        if mode == "metered":
            rate = float(tier["rate"] or 0.0)
            return {
                "decision": ALLOW,
                "model": requested_model,
                "is_local": True,
                "local_rate_per_1k": rate,
                "meter": rate > 0.0,
                "reason": "metered",
            }

        if mode == "free_quota_overflow":
            quota = tier["quota"]
            if quota is None:  # unlimited despite the mode
                return _passthrough(requested_model, is_local=True, reason="quota_unlimited")
            from local_quota import get_local_tokens
            used = await get_local_tokens(org_id) if org_id else 0
            if used + max(int(est_tokens or 0), 0) <= int(quota):
                return _passthrough(requested_model, is_local=True, reason="within_quota")
            overflow_model = tier["overflow_model"]
            if overflow_model:
                return {
                    "decision": OVERFLOW,
                    "model": overflow_model,
                    "is_local": False,  # served by the paid model -> bill as cloud
                    "local_rate_per_1k": None,
                    "meter": False,
                    "reason": "quota_exceeded_overflow",
                }
            # No overflow configured -> degrade to free rather than deny a customer.
            logger.info("[local_pricing] org=%s over quota but no overflow model; serving free", org_id)
            return _passthrough(requested_model, is_local=True, reason="quota_exceeded_no_overflow_degrade")

        # Unknown mode -> safe passthrough.
        return _passthrough(requested_model, is_local=True, reason=f"unknown_mode:{mode}")

    except Exception as exc:  # fail-open
        logger.warning("[local_pricing] resolve failed for org=%s (fail-open allow): %s", org_id, exc)
        return _passthrough(requested_model, is_local=True, reason="error_failopen")
