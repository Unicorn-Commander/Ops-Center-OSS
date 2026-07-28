"""
BILLING_ENABLED / CREDIT_EXEMPT_TIERS are DB-backed (platform_settings) so an
admin-GUI change survives a container restart instead of resetting to the env
baseline. Fail-soft to env defaults when the DB is unavailable.
"""

import pytest

import credit_deduction_middleware as mw


class FakeConn:
    def __init__(self, rows):
        self._rows = rows

    async def fetch(self, query, keys):
        return [r for r in self._rows if r["key"] in keys]


class FakeAcquire:
    def __init__(self, rows):
        self._rows = rows

    async def __aenter__(self):
        return FakeConn(self._rows)

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self, rows):
        self.rows = rows

    def acquire(self):
        return FakeAcquire(self.rows)


def reset():
    mw._billing_cfg.update({"ts": 0.0, "enabled": None, "exempt": None})


@pytest.mark.asyncio
async def test_db_values_override_env():
    reset()
    pool = FakePool([
        {"key": "BILLING_ENABLED", "value": "true"},
        {"key": "CREDIT_EXEMPT_TIERS", "value": "free,staff"},
    ])
    await mw.refresh_billing_config(pool)
    assert mw.is_credit_exempt("staff") is True       # from DB
    assert mw.is_credit_exempt("managed") is False     # not in DB exempt set
    # vip_founder is in the ENV default but NOT the DB set → DB wins
    assert mw.is_credit_exempt("vip_founder") is False


@pytest.mark.asyncio
async def test_db_billing_disabled_exempts_all():
    reset()
    pool = FakePool([{"key": "BILLING_ENABLED", "value": "false"}])
    await mw.refresh_billing_config(pool)
    assert mw.is_credit_exempt("managed") is True


@pytest.mark.asyncio
async def test_failsoft_to_env_when_no_db():
    reset()
    await mw.refresh_billing_config(None)  # no pool
    # env default exempt set includes vip_founder, excludes managed
    assert mw.is_credit_exempt("vip_founder") is True
    assert mw.is_credit_exempt("managed") is False


@pytest.mark.asyncio
async def test_cold_start_before_refresh_uses_env():
    reset()  # never refreshed
    assert mw.is_credit_exempt("vip_founder") is True
    assert mw.is_credit_exempt("managed") is False
