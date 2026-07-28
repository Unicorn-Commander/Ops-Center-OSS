"""
Plan activation → metered-inference provisioning (billing-on-signup).

When an org's plan becomes active or changes — via the live subscribe/
upgrade/change API paths or a Lago webhook — the org must automatically end
up with:

  1. its per-org LiteLLM gateway key (the metering/billing contract,
     user_id == org_id; created idempotently if missing), and
  2. organizations.plan_tier tracking reality (it was previously only
     written at org creation).

NOTE — inference budget is DECOUPLED from the subscription tier. Subscription
(app access) and credits (a metered inference wallet) are orthogonal: a solo
founder can need far more inference than an enterprise. Inference spend is
guarded by the credit WALLET (has_sufficient_org_credits in the credit
middleware), NOT by a per-plan gateway-key cap. on_plan_activated therefore
does not source a max_budget from the plan tier; budget_for_plan /
update_org_gateway_key_budget are retained as helpers for admin use and for the
future credit-wallet sync that will guard the FEDERATED path (where the local
credit middleware isn't in the request loop).

Budget resolution order for a plan code:
  a. subscription_tiers.max_monthly_llm_budget where lago_plan_code or
     tier_code matches (codes normalized: lowercase, '-'/'_' equivalent,
     trailing _monthly/_yearly stripped) — admin-editable via the existing
     tiers CRUD;
  b. platform_settings key 'LLM_BUDGET_<plan_code>' (same normalization);
  c. None → unlimited (today's behavior, e.g. vip_founder).

EVERYTHING here is failure-isolated: a Lago outage, missing table, or
gateway error must never break a signup or plan change. on_plan_activated()
never raises.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def _get_conn():
    # Same double-await shim as gateway_key_provisioning.py — the package
    # helper returns a PoolAcquireContext, not a live connection. Imported
    # lazily so this module stays importable without DB deps (tests).
    from database import get_db_connection as _pkg_get_db_connection
    return await (await _pkg_get_db_connection())


def _norm(code: str) -> str:
    code = (code or "").strip().lower().replace("-", "_")
    for suffix in ("_monthly", "_yearly", "_weekly", "_annual"):
        if code.endswith(suffix):
            code = code[: -len(suffix)]
    return code


async def budget_for_plan(plan_code: str) -> Optional[float]:
    """Resolve the monthly inference budget (USD) for a plan code, or None
    for unlimited. Never raises."""
    if not plan_code:
        return None
    base = _norm(plan_code)

    conn = None
    try:
        conn = await _get_conn()
        # a) subscription_tiers column (matches lago_plan_code or tier_code,
        #    normalized on both sides)
        try:
            row = await conn.fetchrow(
                """
                SELECT max_monthly_llm_budget FROM subscription_tiers
                WHERE replace(lower(COALESCE(lago_plan_code, '')), '-', '_') IN ($1, $2)
                   OR replace(lower(tier_code), '-', '_') = $2
                LIMIT 1
                """,
                plan_code.lower().replace("-", "_"),
                base,
            )
            if row and row["max_monthly_llm_budget"] is not None:
                return float(row["max_monthly_llm_budget"])
        except Exception as e:
            logger.debug("Tier budget lookup failed for %s: %s", plan_code, e)

        # b) platform_settings fallback
        try:
            for key in (f"LLM_BUDGET_{plan_code}", f"LLM_BUDGET_{base}"):
                val = await conn.fetchval(
                    "SELECT value FROM platform_settings WHERE lower(key) = lower($1)",
                    key,
                )
                if val not in (None, ""):
                    return float(val)
        except Exception as e:
            logger.debug("platform_settings budget lookup failed for %s: %s", plan_code, e)
    except Exception as e:
        logger.warning("Budget resolution unavailable for plan %s: %s", plan_code, e)
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass
    return None


def _update_org_plan_tier(org_id: str, plan_code: str) -> None:
    """Best-effort: keep the OrgManager record's plan_tier in sync."""
    try:
        from org_manager import org_manager
        org_manager.update_org_plan(org_id, _norm(plan_code))
    except Exception as e:
        logger.debug("plan_tier sync skipped for %s: %s", org_id, e)


async def on_plan_activated(
    org_id: str,
    plan_code: str,
    *,
    source: str = "unknown",
    key_provisioner: Any = None,
    budget_updater: Any = None,
    budget_resolver: Any = None,
) -> Dict[str, Any]:
    """The single hook every plan-activation path calls.

    Idempotent and failure-isolated — safe to call repeatedly (webhook
    retries, upgrade+webhook double-fire). Returns a small status dict for
    logging/tests; NEVER raises.
    """
    out: Dict[str, Any] = {"org_id": org_id, "plan_code": plan_code,
                           "key": False, "budget": None, "budget_applied": False}
    budget = None  # referenced in the summary log even when no budget_resolver is passed
    if not org_id or not str(org_id).startswith("org_"):
        # Email-keyed legacy customers and service accounts are not org
        # contracts — nothing to provision.
        out["skipped"] = "not org-keyed"
        return out
    try:
        if key_provisioner is None:
            from gateway_key_provisioning import provision_org_gateway_key
            key_provisioner = provision_org_gateway_key

        # 1. Ensure the org key exists (create-only idempotent) — the org's
        #    metering identity on the gateway.
        key_info = await key_provisioner(org_id=org_id, plan_code=plan_code)
        out["key"] = bool(key_info)

        # 2. Budget is DECOUPLED from the subscription tier. The two axes are
        #    orthogonal: subscription = app access; credits = a metered inference
        #    wallet. A solo founder can need more inference than an enterprise —
        #    so inference spend is guarded by the credit WALLET
        #    (has_sufficient_org_credits), NOT by a per-plan cap. We therefore do
        #    NOT source a gateway-key max_budget from the plan tier. A budget is
        #    applied ONLY when a caller explicitly supplies a resolver (reserved
        #    for the future credit-wallet sync that guards the federated path,
        #    where the local credit middleware isn't in the loop); the
        #    signup/upgrade/webhook path supplies none → key left uncapped.
        if budget_resolver is not None and budget_updater is not None:
            budget = await budget_resolver(plan_code)
            out["budget"] = budget
            if budget is not None:
                out["budget_applied"] = bool(await budget_updater(
                    org_id, budget, plan_code=plan_code
                ))

        # 3. Track the plan on the org record.
        _update_org_plan_tier(org_id, plan_code)

        logger.info(
            "Plan activated (%s): org=%s plan=%s key=%s budget=%s applied=%s",
            source, org_id, plan_code, out["key"], budget, out["budget_applied"],
        )
    except Exception as e:
        # Absolute backstop — plan provisioning must never break the caller.
        logger.warning("on_plan_activated failed for org %s plan %s: %s",
                       org_id, plan_code, e)
        out["error"] = str(e)
    return out
