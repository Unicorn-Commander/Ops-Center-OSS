"""
Unit tests for billing-on-signup (plan_provisioning.py).

Contract: when a plan activates for an org, the org ends up with a gateway
key carrying the plan's budget — and NOTHING in this path may ever raise
into the subscribe flow.
"""

import pytest

import plan_provisioning
from plan_provisioning import _norm, budget_for_plan, on_plan_activated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self, tier_budget=None, settings=None):
        self.tier_budget = tier_budget
        self.settings = settings or {}
        self.closed = False

    async def fetchrow(self, query, *params):
        if "subscription_tiers" in query and self.tier_budget is not None:
            return {"max_monthly_llm_budget": self.tier_budget}
        return None

    async def fetchval(self, query, *params):
        if "platform_settings" in query:
            return self.settings.get(params[0]) or self.settings.get(params[0].lower())
        return None

    async def close(self):
        self.closed = True


def patch_conn(monkeypatch, conn):
    async def _get():
        return conn
    monkeypatch.setattr(plan_provisioning, "_get_conn", _get)


def make_provisioner(result=None, fail=False):
    calls = []

    async def provision(org_id=None, plan_code=None, **kw):
        calls.append({"org_id": org_id, "plan_code": plan_code})
        if fail:
            raise RuntimeError("gateway down")
        return result if result is not None else {"key_id": "tok", "key": "sk-1"}

    provision.calls = calls
    return provision


def make_budget_updater(ok=True):
    calls = []

    async def update(org_id, max_budget, plan_code=None):
        calls.append({"org_id": org_id, "max_budget": max_budget, "plan_code": plan_code})
        return ok

    update.calls = calls
    return update


async def fixed_budget(value):
    async def resolver(plan_code):
        return value
    return resolver


# ---------------------------------------------------------------------------
# Code normalization + budget resolution
# ---------------------------------------------------------------------------

def test_norm_strips_intervals_and_unifies_separators():
    assert _norm("professional_monthly") == "professional"
    assert _norm("Starter_Yearly") == "starter"
    assert _norm("founder-friend") == "founder_friend"
    assert _norm("vip_founder") == "vip_founder"


@pytest.mark.asyncio
async def test_budget_from_tier_column(monkeypatch):
    patch_conn(monkeypatch, FakeConn(tier_budget=35.00))
    assert await budget_for_plan("professional_monthly") == 35.0


@pytest.mark.asyncio
async def test_budget_falls_back_to_platform_settings(monkeypatch):
    patch_conn(monkeypatch, FakeConn(settings={"LLM_BUDGET_starter": "10.5"}))
    assert await budget_for_plan("starter_monthly") == 10.5


@pytest.mark.asyncio
async def test_budget_defaults_to_unlimited(monkeypatch):
    patch_conn(monkeypatch, FakeConn())
    assert await budget_for_plan("vip_founder") is None


@pytest.mark.asyncio
async def test_budget_resolution_never_raises(monkeypatch):
    async def boom():
        raise RuntimeError("db down")
    monkeypatch.setattr(plan_provisioning, "_get_conn", boom)
    assert await budget_for_plan("starter") is None


# ---------------------------------------------------------------------------
# on_plan_activated — the hook every activation path calls
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activation_provisions_key_and_applies_budget(monkeypatch):
    monkeypatch.setattr(plan_provisioning, "_update_org_plan_tier", lambda *a: None)
    provision = make_provisioner()
    update = make_budget_updater()

    async def resolver(plan_code):
        return 35.0

    out = await on_plan_activated(
        "org_abc", "professional_monthly", source="test",
        key_provisioner=provision, budget_updater=update, budget_resolver=resolver,
    )
    assert provision.calls == [{"org_id": "org_abc", "plan_code": "professional_monthly"}]
    assert update.calls == [{"org_id": "org_abc", "max_budget": 35.0,
                             "plan_code": "professional_monthly"}]
    assert out["key"] is True and out["budget_applied"] is True


@pytest.mark.asyncio
async def test_signup_path_does_not_apply_a_tier_budget(monkeypatch):
    """Gap 3 decouple: with no resolver/updater (the real signup/webhook path),
    the key is provisioned but NO budget is sourced from the plan tier — the
    credit wallet is the spend guard, not a per-plan cap."""
    monkeypatch.setattr(plan_provisioning, "_update_org_plan_tier", lambda *a: None)
    provision = make_provisioner()
    # Guard: budget_for_plan must NOT be consulted by the default path.
    async def _boom_resolver(_):
        raise AssertionError("budget_for_plan should not be called by signup path")
    monkeypatch.setattr(plan_provisioning, "budget_for_plan", _boom_resolver)

    out = await on_plan_activated(
        "org_abc", "professional_monthly", source="create_subscription",
        key_provisioner=provision,
    )
    assert provision.calls == [{"org_id": "org_abc", "plan_code": "professional_monthly"}]
    assert out["key"] is True
    assert out["budget_applied"] is False
    assert out["budget"] is None


@pytest.mark.asyncio
async def test_unlimited_plan_skips_budget_update(monkeypatch):
    monkeypatch.setattr(plan_provisioning, "_update_org_plan_tier", lambda *a: None)
    update = make_budget_updater()

    async def resolver(plan_code):
        return None

    out = await on_plan_activated(
        "org_abc", "vip_founder", key_provisioner=make_provisioner(),
        budget_updater=update, budget_resolver=resolver,
    )
    assert update.calls == []
    assert out["budget"] is None and out["budget_applied"] is False


@pytest.mark.asyncio
async def test_non_org_identities_are_skipped():
    out = await on_plan_activated("someone@example.com", "starter")
    assert out["skipped"] == "not org-keyed"
    out2 = await on_plan_activated("", "starter")
    assert out2["skipped"] == "not org-keyed"


@pytest.mark.asyncio
async def test_activation_never_raises_on_failures(monkeypatch):
    monkeypatch.setattr(plan_provisioning, "_update_org_plan_tier", lambda *a: None)

    async def resolver(plan_code):
        return 10.0

    # Provisioner exploding must be swallowed
    out = await on_plan_activated(
        "org_abc", "starter", key_provisioner=make_provisioner(fail=True),
        budget_updater=make_budget_updater(), budget_resolver=resolver,
    )
    assert "error" in out  # captured, not raised
