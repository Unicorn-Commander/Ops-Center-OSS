"""
Paid-org provisioning — the single, idempotent path that turns an existing org
into a correctly-provisioned PAID org.
=====================================================================

Used by BOTH manual admin onboarding (the endpoint below) and the Stripe
subscription webhook (self-serve). Org-scoped — an individual is just a personal
org-of-one (signup already creates the org), so the same path serves both.

Closes the paying-org readiness gaps, in order, each failure-isolated:
  1. set organizations.plan_tier  (so the tier is non-exempt → it bills)
  2. Lago subscription on the tier's REAL plan, external_id == org_id (so the
     gateway's per-org ai_api_call events attach and actually bill)
  3. gateway key WITH max_budget = tier.max_monthly_llm_budget  — the cloud
     HARD CAP (the #1 money risk: a paid org must never run uncapped on
     third-party cloud). Local stays $0, so the cap only bites cloud overflow.
  4. (optional) fund the inline-path org credit wallet to the included allowance.

Numbers are READ from subscription_tiers (never hardcoded here), so tuning a
tier's cap/markup/plan is a DB change, not a code change. Returns a status dict;
never raises into the caller.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth_dependencies import require_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/billing", tags=["Paid Org Provisioning"])


async def _load_tier(tier_code: str):
    from database import get_db_connection
    async with await get_db_connection() as conn:
        return await conn.fetchrow(
            """
            SELECT tier_code,
                   COALESCE(lago_plan_code, tier_code) AS lago_plan_code,
                   max_monthly_llm_budget AS cloud_cap
            FROM subscription_tiers WHERE tier_code = $1
            """,
            tier_code,
        )


async def _org_name(org_id: str) -> str:
    from database import get_db_connection
    try:
        async with await get_db_connection() as conn:
            row = await conn.fetchrow("SELECT name FROM organizations WHERE id = $1", org_id)
            return (row["name"] if row and row["name"] else org_id)
    except Exception:
        return org_id


async def provision_paid_org(
    org_id: str,
    tier_code: str,
    *,
    email: str = "",
    included_credits: Optional[int] = None,
    source: str = "manual",
) -> Dict[str, Any]:
    """Upgrade an existing org to a correctly-provisioned paid org. Idempotent."""
    out: Dict[str, Any] = {
        "org_id": org_id, "tier": tier_code, "source": source,
        "tier_set": False, "lago_sub": False, "key_capped": False,
        "cloud_cap": None, "wallet_funded": False,
    }
    if not org_id or not tier_code:
        out["error"] = "org_id and tier_code required"
        return out

    tier = await _load_tier(tier_code)
    if not tier:
        out["error"] = f"unknown tier_code '{tier_code}'"
        return out
    cloud_cap = float(tier["cloud_cap"]) if tier["cloud_cap"] is not None else None
    lago_plan = tier["lago_plan_code"]
    out["cloud_cap"] = cloud_cap

    # ID forms differ by subsystem: organizations.id is a bare UUID, while the
    # gateway key (litellm user_id) and Lago external_id use the "org_<uuid>"
    # form (so metered ai_api_call events attach). Normalize to both.
    s = str(org_id)
    bare_id = s[4:] if s.startswith("org_") else s
    org_key = "org_" + bare_id
    out["bare_id"], out["org_key"] = bare_id, org_key

    # 1. Set the org's tier (non-exempt paid tier → billing engages).
    try:
        from database import get_db_connection
        async with await get_db_connection() as conn:
            await conn.execute("UPDATE organizations SET plan_tier = $1 WHERE id = $2", tier_code, bare_id)
        out["tier_set"] = True
    except Exception as e:
        out["tier_error"] = str(e)
        logger.warning("[provision_paid_org] tier set failed org=%s: %s", bare_id, e)

    # 2. Lago subscription on the tier's real plan (external_id == org_key, to
    #    match the gateway's per-org metering identity).
    try:
        from lago_integration import subscribe_org_to_plan
        sub = await subscribe_org_to_plan(
            org_id=org_key, plan_code=lago_plan, org_name=await _org_name(bare_id), email=email,
        )
        out["lago_sub"] = bool(sub and sub.get("lago_id"))
        out["lago_plan"] = lago_plan
    except Exception as e:
        out["lago_error"] = str(e)
        logger.warning("[provision_paid_org] lago sub failed org=%s plan=%s: %s", org_key, lago_plan, e)

    # 3. Gateway key WITH the cloud hard cap (create-with-budget, then ensure on
    #    a pre-existing key — provision is create-only idempotent).
    try:
        from gateway_key_provisioning import provision_org_gateway_key, update_org_gateway_key_budget
        await provision_org_gateway_key(org_id=org_key, plan_code=tier_code, max_budget=cloud_cap)
        if cloud_cap is not None:
            out["key_capped"] = bool(await update_org_gateway_key_budget(org_key, cloud_cap, plan_code=tier_code))
    except Exception as e:
        out["key_error"] = str(e)
        logger.warning("[provision_paid_org] key cap failed org=%s: %s", org_key, e)

    # 4. Optionally fund the inline-path credit wallet.
    if included_credits is not None:
        try:
            from database import get_db_connection
            async with await get_db_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO organization_credit_pools (org_id, total_credits)
                    VALUES ($1, $2)
                    ON CONFLICT (org_id) DO UPDATE
                      SET total_credits = GREATEST(organization_credit_pools.total_credits, EXCLUDED.total_credits)
                    """,
                    bare_id, int(included_credits),
                )
            out["wallet_funded"] = True
        except Exception as e:
            out["wallet_error"] = str(e)
            logger.warning("[provision_paid_org] wallet fund failed org=%s: %s", bare_id, e)

    logger.info("[provision_paid_org] %s", out)
    return out


async def downgrade_org(org_id: str, *, to_tier: str = "free", source: str = "stripe") -> Dict[str, Any]:
    """Downgrade an org when its subscription is canceled / payment fails.

    Reuses provision_paid_org with the lower tier — which immediately RE-CAPS the
    gateway key to that tier's budget (e.g. free = $0.10), the critical effect:
    stop the org's third-party cloud spend the moment they stop paying. Sets the
    tier and (best-effort) the lower Lago plan too. Never raises.
    """
    logger.info("[downgrade_org] org=%s -> %s (%s)", org_id, to_tier, source)
    return await provision_paid_org(org_id, to_tier, source=f"downgrade:{source}")


class ProvisionRequest(BaseModel):
    org_id: str
    tier_code: str
    email: Optional[str] = ""
    included_credits: Optional[int] = None


@router.post("/provision-paid-org")
async def provision_paid_org_endpoint(req: ProvisionRequest, user: Dict[str, Any] = Depends(require_admin_user)):
    """Admin: provision/upgrade an org to a paid tier (capped + subscribed + billed)."""
    result = await provision_paid_org(
        req.org_id, req.tier_code, email=req.email or "",
        included_credits=req.included_credits, source="admin",
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
