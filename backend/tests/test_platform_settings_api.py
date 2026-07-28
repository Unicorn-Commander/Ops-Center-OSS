"""
Unit tests for platform_settings_api.py — focused on the four scalar config
keys added for the admin GUI:
    FEDERATION_DEFAULT_TRUST_MODE, FEDERATION_SERVICE_PROFILE,
    BILLING_ENABLED, CREDIT_EXEMPT_TIERS

These verify:
  * the four keys are registered in PLATFORM_SETTINGS
  * GET /api/v1/platform/settings includes them (with options/default metadata)
  * PUT /api/v1/platform/settings persists FEDERATION_DEFAULT_TRUST_MODE to the
    `platform_settings` TABLE under the exact key (the consumer contract for
    backend/federation/trust.py refresh()) — proved by a fake psycopg2 backend
    that honors INSERT ... ON CONFLICT and SELECT
  * an invalid trust-mode value is rejected (400) and never written

The DB is a hand-rolled in-memory fake standing in for psycopg2 — no live
Postgres required. The admin dependency is overridden. audit_logger is imported
defensively by the module under test (it is None when aiofiles is absent), so
these tests do not depend on it.

Run: pytest backend/tests/test_platform_settings_api.py -v
(If local imports fail in your env, Claude runs the full suite on the node
where the package layout / deps resolve.)
"""

import sys
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Make backend modules importable whether tests run from repo root or backend/.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import platform_settings_api as psa  # noqa: E402


SCALAR_KEYS = [
    "FEDERATION_DEFAULT_TRUST_MODE",
    "FEDERATION_SERVICE_PROFILE",
    "BILLING_ENABLED",
    "CREDIT_EXEMPT_TIERS",
]


# ---------------------------------------------------------------------------
# In-memory fake psycopg2 backed by a shared dict ("the platform_settings
# table"). It understands just enough SQL for this module: CREATE TABLE,
# the SELECT-by-key, and the INSERT ... ON CONFLICT (key) DO UPDATE upsert.
# ---------------------------------------------------------------------------

class FakeCursor:
    def __init__(self, store):
        self.store = store
        self._result = None

    def execute(self, query, params=None):
        q = " ".join(query.split()).lower()
        params = params or ()
        if q.startswith("create table"):
            self._result = None
        elif q.startswith("select value from platform_settings where key"):
            key = params[0]
            self._result = {"value": self.store[key]} if key in self.store else None
        elif q.startswith("insert into platform_settings"):
            # Columns: (key, value, category, is_secret, updated_at)
            key, value = params[0], params[1]
            self.store[key] = value  # upsert
            self._result = None
        else:
            self._result = None

    def fetchone(self):
        return self._result

    def close(self):
        pass


class FakeConn:
    def __init__(self, store):
        self.store = store

    def cursor(self, cursor_factory=None):
        return FakeCursor(self.store)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def db_store():
    """Shared dict acting as the platform_settings table contents."""
    return {}


@pytest.fixture(autouse=True)
def _patch_psycopg2(monkeypatch, db_store):
    """Route every psycopg2.connect in the module to our in-memory fake."""
    import psycopg2

    monkeypatch.setattr(psycopg2, "connect", lambda **kwargs: FakeConn(db_store))
    # Module reads os env for some keys; clear the scalar ones so the table /
    # registry-default path is exercised deterministically.
    for k in SCALAR_KEYS:
        monkeypatch.delenv(k, raising=False)
    yield


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(psa.router)
    app.dependency_overrides[psa.require_admin] = lambda: True
    return TestClient(app)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", SCALAR_KEYS)
def test_scalar_key_is_registered(key):
    assert key in psa.PLATFORM_SETTINGS
    cfg = psa.PLATFORM_SETTINGS[key]
    assert cfg["is_secret"] is False
    assert cfg["description"]  # non-empty


def test_federation_keys_categorized_federation():
    assert psa.PLATFORM_SETTINGS["FEDERATION_DEFAULT_TRUST_MODE"]["category"] == "federation"
    assert psa.PLATFORM_SETTINGS["FEDERATION_SERVICE_PROFILE"]["category"] == "federation"


def test_billing_keys_categorized_billing():
    assert psa.PLATFORM_SETTINGS["BILLING_ENABLED"]["category"] == "billing"
    assert psa.PLATFORM_SETTINGS["CREDIT_EXEMPT_TIERS"]["category"] == "billing"


def test_trust_mode_options_are_the_five_modes():
    opts = psa.PLATFORM_SETTINGS["FEDERATION_DEFAULT_TRUST_MODE"]["options"]
    assert set(opts) == {"full", "scoped", "consumer", "publisher", "isolated"}


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

def test_get_settings_includes_scalar_keys(client):
    res = client.get("/api/v1/platform/settings")
    assert res.status_code == 200
    data = res.json()
    keys = {s["key"] for s in data["settings"]}
    for k in SCALAR_KEYS:
        assert k in keys


def test_get_surfaces_registry_default_when_unset(client, db_store):
    """No table row + no env var -> GET shows the registry default."""
    assert "FEDERATION_DEFAULT_TRUST_MODE" not in db_store
    res = client.get("/api/v1/platform/settings/FEDERATION_DEFAULT_TRUST_MODE")
    assert res.status_code == 200
    body = res.json()
    assert body["value"] == "full"          # registry default
    assert body["default"] == "full"
    assert body["options"] == ["full", "scoped", "consumer", "publisher", "isolated"]


def test_get_grouped_has_federation_and_billing(client):
    res = client.get("/api/v1/platform/settings")
    grouped = res.json()["grouped"]
    assert "federation" in grouped
    assert "billing" in grouped


# ---------------------------------------------------------------------------
# PUT — the load-bearing storage contract
# ---------------------------------------------------------------------------

def test_put_trust_mode_persists_to_table_under_exact_key(client, db_store):
    res = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"FEDERATION_DEFAULT_TRUST_MODE": "isolated"}},
    )
    assert res.status_code == 200, res.text
    # Lands in the platform_settings table under EXACTLY this key — this is what
    # trust.py refresh() reads (SELECT value ... WHERE key='FEDERATION_DEFAULT_TRUST_MODE').
    assert db_store.get("FEDERATION_DEFAULT_TRUST_MODE") == "isolated"


def test_put_value_round_trips_via_get(client):
    put = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"FEDERATION_DEFAULT_TRUST_MODE": "scoped"}},
    )
    assert put.status_code == 200
    got = client.get("/api/v1/platform/settings/FEDERATION_DEFAULT_TRUST_MODE")
    assert got.json()["value"] == "scoped"


def test_put_billing_and_exempt_tiers_persist(client, db_store):
    res = client.put(
        "/api/v1/platform/settings",
        json={
            "settings": {
                "BILLING_ENABLED": "false",
                "CREDIT_EXEMPT_TIERS": "free,vip_founder,internal",
            }
        },
    )
    assert res.status_code == 200, res.text
    assert db_store["BILLING_ENABLED"] == "false"
    assert db_store["CREDIT_EXEMPT_TIERS"] == "free,vip_founder,internal"


# ---------------------------------------------------------------------------
# PUT — validation (fail closed)
# ---------------------------------------------------------------------------

def test_put_invalid_trust_mode_rejected_and_not_written(client, db_store):
    res = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"FEDERATION_DEFAULT_TRUST_MODE": "bogus"}},
    )
    assert res.status_code == 400
    # Must NOT have written a garbage value the enforcer would have to fail
    # closed on.
    assert "FEDERATION_DEFAULT_TRUST_MODE" not in db_store


def test_put_invalid_billing_enabled_rejected(client, db_store):
    res = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"BILLING_ENABLED": "yes"}},  # not in options
    )
    assert res.status_code == 400
    assert "BILLING_ENABLED" not in db_store


def test_put_unknown_key_rejected(client):
    res = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"NOT_A_REAL_KEY": "x"}},
    )
    assert res.status_code == 400


def test_put_csv_tiers_no_options_accepts_freeform(client, db_store):
    """CREDIT_EXEMPT_TIERS has no options list, so arbitrary CSV is accepted."""
    res = client.put(
        "/api/v1/platform/settings",
        json={"settings": {"CREDIT_EXEMPT_TIERS": "*"}},
    )
    assert res.status_code == 200
    assert db_store["CREDIT_EXEMPT_TIERS"] == "*"
