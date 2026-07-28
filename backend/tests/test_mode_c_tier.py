"""
Gap 1: direct-API (`uc_`) keys must bill the key OWNER's real tier, not a
blanket vip_founder exempt (which made all direct-API inference free = we eat
the cost). Internal/founder owners stay exempt naturally; real customers bill.
Lookup errors fail-open to "free" (exempt) — never wrongly charge.
"""

import types

import pytest

import api_key_manager as akm_mod
from credit_deduction_middleware import CreditDeductionMiddleware


class FakeManager:
    def __init__(self, user_id):
        self._uid = user_id

    async def validate_api_key(self, token):
        return {"user_id": self._uid, "permissions": []}


class FakeCreditSystem:
    def __init__(self, tier=None, raise_exc=False):
        self._tier = tier
        self._raise = raise_exc

    async def get_user_tier(self, user_id):
        if self._raise:
            raise RuntimeError("db down")
        return self._tier


class FakeHeaders(dict):
    def get(self, k, default=None):
        return super().get(k, default)


class FakeRequest:
    def __init__(self, auth):
        self.headers = FakeHeaders({"Authorization": auth})
        self.cookies = {}


def mw_with(monkeypatch, owner_uid, tier=None, raise_exc=False):
    monkeypatch.setattr(akm_mod, "get_api_key_manager", lambda: FakeManager(owner_uid))
    mw = CreditDeductionMiddleware(app=None)
    mw.credit_system = FakeCreditSystem(tier=tier, raise_exc=raise_exc)
    return mw


@pytest.mark.asyncio
async def test_uc_key_bills_owner_real_tier(monkeypatch):
    mw = mw_with(monkeypatch, "cust-1", tier="managed")
    user = await mw._get_user_from_session(FakeRequest("Bearer uc_deadbeef"))
    assert user["user_id"] == "cust-1"
    assert user["subscription_tier"] == "managed"  # real tier → will be charged


@pytest.mark.asyncio
async def test_uc_key_internal_owner_stays_exempt(monkeypatch):
    mw = mw_with(monkeypatch, "aaron", tier="vip_founder")
    user = await mw._get_user_from_session(FakeRequest("Bearer uc_aaaa"))
    assert user["subscription_tier"] == "vip_founder"  # exempt naturally


@pytest.mark.asyncio
async def test_uc_key_tier_lookup_error_fails_open_to_exempt(monkeypatch):
    mw = mw_with(monkeypatch, "cust-2", raise_exc=True)
    user = await mw._get_user_from_session(FakeRequest("Bearer uc_bbbb"))
    assert user["subscription_tier"] == "free"  # fail-open: never wrongly charge
