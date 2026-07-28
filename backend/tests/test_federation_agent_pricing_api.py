"""
Unit tests for federation_agent_pricing_api.py

Uses a FastAPI app with the router mounted, the admin dependency overridden,
and a hand-rolled async mock pool injected into app.state.db_pool. No live
DB/Redis required.

Run: pytest backend/tests/test_federation_agent_pricing_api.py -v
(If local imports of audit_logger/models fail in your env, Claude runs the
full suite on the node where the package layout resolves.)
"""

import json
import os
import sys
import types
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import asyncpg
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Make backend modules importable whether tests run from repo root or backend/.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# The real audit_logger module imports aiofiles, a runtime-only dep not always
# present in a bare local test env. The API module imports `audit_logger`
# lazily inside the PUT handler and wraps the call in try/except, but install a
# lightweight stub BEFORE importing the API module so the import resolves on a
# bare env too. On the node (where aiofiles exists) this stub is skipped.
if "audit_logger" not in sys.modules:
    try:
        import aiofiles  # noqa: F401  (present on the node -> use the real module)
    except ImportError:
        _stub = types.ModuleType("audit_logger")
        _stub.audit_logger = types.SimpleNamespace(log=AsyncMock(return_value=1))
        sys.modules["audit_logger"] = _stub

import federation_agent_pricing_api as fap  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakePool:
    """Minimal async stand-in for asyncpg.Pool with programmable return values."""

    def __init__(self):
        self.fetch = AsyncMock(return_value=[])
        self.fetchrow = AsyncMock(return_value=None)
        self.fetchval = AsyncMock(return_value=None)
        self.execute = AsyncMock(return_value="INSERT 0 1")


@pytest.fixture
def pool():
    return FakePool()


@pytest.fixture
def client(pool):
    app = FastAPI()
    app.include_router(fap.router)
    app.state.db_pool = pool
    # Bypass the Redis-session admin check.
    app.dependency_overrides[fap.require_admin] = lambda: {
        "user_id": "admin-1",
        "username": "admin@example.com",
        "role": "admin",
    }
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET — default-safe behavior
# ---------------------------------------------------------------------------

def test_get_returns_default_when_absent(client, pool):
    # fetchval -> None (no stored row)
    res = client.get("/api/v1/admin/agent-pricing/")
    assert res.status_code == 200, res.text
    assert res.json() == {"pricing": {"default": 1.0}}


def test_get_returns_default_when_empty_string(client, pool):
    pool.fetchval.return_value = ""
    res = client.get("/api/v1/admin/agent-pricing/")
    assert res.status_code == 200
    assert res.json()["pricing"] == {"default": 1.0}


def test_get_returns_default_when_unparseable(client, pool):
    pool.fetchval.return_value = "{not valid json"
    res = client.get("/api/v1/admin/agent-pricing/")
    assert res.status_code == 200
    assert res.json()["pricing"] == {"default": 1.0}


def test_get_returns_stored_pricing(client, pool):
    pool.fetchval.return_value = json.dumps({"default": 2, "deep-research": 50})
    res = client.get("/api/v1/admin/agent-pricing/")
    assert res.status_code == 200
    pricing = res.json()["pricing"]
    assert pricing == {"default": 2.0, "deep-research": 50.0}


def test_get_default_when_table_missing(client, pool):
    pool.fetchval.side_effect = asyncpg.UndefinedTableError("no table")
    res = client.get("/api/v1/admin/agent-pricing/")
    assert res.status_code == 200
    assert res.json()["pricing"] == {"default": 1.0}


# ---------------------------------------------------------------------------
# PUT — valid round-trip
# ---------------------------------------------------------------------------

def test_put_valid_round_trip(client, pool):
    payload = {"pricing": {"default": 2, "deep-research": 50, "sql-analyst": 3.5}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 200, res.text
    assert res.json()["pricing"] == {
        "default": 2.0,
        "deep-research": 50.0,
        "sql-analyst": 3.5,
    }
    # The upsert persisted a JSON string under the exact consumer key.
    pool.execute.assert_awaited()
    args = pool.execute.await_args.args
    assert fap.PRICING_KEY in args  # key is the second positional ($1)
    stored = next(a for a in args if isinstance(a, str) and a.lstrip().startswith("{"))
    assert json.loads(stored) == {"default": 2.0, "deep-research": 50.0, "sql-analyst": 3.5}


def test_put_defaults_missing_default_to_one(client, pool):
    # No "default" key supplied -> handler fills it to 1.0.
    payload = {"pricing": {"deep-research": 10}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 200, res.text
    assert res.json()["pricing"] == {"deep-research": 10.0, "default": 1.0}


def test_put_zero_is_allowed(client, pool):
    payload = {"pricing": {"default": 0, "freebie-agent": 0}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 200, res.text
    assert res.json()["pricing"] == {"default": 0.0, "freebie-agent": 0.0}


# ---------------------------------------------------------------------------
# PUT — validation failures (422)
# ---------------------------------------------------------------------------

def test_put_non_numeric_value_422(client, pool):
    payload = {"pricing": {"default": 1, "bad-agent": "free"}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 422, res.text
    assert "number" in res.json()["detail"].lower()
    pool.execute.assert_not_awaited()


def test_put_negative_value_422(client, pool):
    payload = {"pricing": {"default": 1, "neg-agent": -5}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 422, res.text
    assert ">=" in res.json()["detail"] or "0" in res.json()["detail"]
    pool.execute.assert_not_awaited()


def test_put_bool_value_rejected_422(client, pool):
    # bool is an int subclass; it must NOT be accepted as a price.
    payload = {"pricing": {"default": True}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 422, res.text


def test_put_empty_agent_id_422(client, pool):
    payload = {"pricing": {"default": 1, "  ": 2}}
    res = client.put("/api/v1/admin/agent-pricing/", json=payload)
    assert res.status_code == 422, res.text
    pool.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# agent-choices — best-effort, never blocks
# ---------------------------------------------------------------------------

def test_agent_choices_returns_empty_when_unavailable(client, pool):
    # No federation.node_registry importable / catalog errors -> [].
    res = client.get("/api/v1/admin/agent-pricing/agent-choices")
    assert res.status_code == 200
    assert res.json() == []
