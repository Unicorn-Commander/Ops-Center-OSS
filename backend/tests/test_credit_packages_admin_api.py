"""
Unit tests for credit_packages_admin_api.py

Uses a FastAPI app with the router mounted, the admin dependency overridden,
and a hand-rolled async mock pool injected into app.state.db_pool. No live
DB/Redis required.

Run: pytest backend/tests/test_credit_packages_admin_api.py -v
(If local imports of audit_logger/models fail in your env, Claude runs the
full suite on the node where the package layout resolves.)
"""

import sys
import os
import types
import uuid
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

# The real audit_logger module imports aiofiles, which is a runtime-only dep not
# always present in a bare local test env. We only need a no-op `audit_logger`
# object, so install a lightweight stub BEFORE importing the API module. On the
# node (where aiofiles exists) this stub is harmless — the API module imports
# `audit_logger` from whatever is in sys.modules, and the autouse fixture below
# patches `.log` either way.
if "audit_logger" not in sys.modules:
    try:
        import aiofiles  # noqa: F401  (present on the node -> use the real module)
    except ImportError:
        _stub = types.ModuleType("audit_logger")
        _stub.audit_logger = types.SimpleNamespace(log=AsyncMock(return_value=1))
        sys.modules["audit_logger"] = _stub

import credit_packages_admin_api as cpa  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def _make_row(**overrides):
    """Build a dict that behaves like an asyncpg.Record for our helper."""
    row = {
        "id": overrides.get("id", str(uuid.uuid4())),
        "package_code": overrides.get("package_code", "starter"),
        "package_name": overrides.get("package_name", "Starter Pack"),
        "description": overrides.get("description", "A starter pack"),
        "credits": overrides.get("credits", 1000),
        "price_usd": overrides.get("price_usd", 10.00),
        "discount_percentage": overrides.get("discount_percentage", 0),
        "stripe_price_id": overrides.get("stripe_price_id", None),
        "stripe_product_id": overrides.get("stripe_product_id", None),
        "is_active": overrides.get("is_active", True),
        "display_order": overrides.get("display_order", 0),
        "created_at": overrides.get("created_at", datetime(2026, 6, 13, 12, 0, 0)),
        "updated_at": overrides.get("updated_at", datetime(2026, 6, 13, 12, 0, 0)),
    }
    return row


class FakePool:
    """Minimal async stand-in for asyncpg.Pool with programmable return values."""

    def __init__(self):
        self.fetch = AsyncMock(return_value=[])
        self.fetchrow = AsyncMock(return_value=None)
        self.fetchval = AsyncMock(return_value=None)
        self.execute = AsyncMock(return_value="UPDATE 1")


@pytest.fixture(autouse=True)
def _silence_audit(monkeypatch):
    """Replace the real audit logger with a no-op async mock for all tests."""
    monkeypatch.setattr(cpa.audit_logger, "log", AsyncMock(return_value=1))


@pytest.fixture
def pool():
    return FakePool()


@pytest.fixture
def client(pool):
    app = FastAPI()
    app.include_router(cpa.router)
    app.state.db_pool = pool
    # Bypass the Redis-session admin check.
    app.dependency_overrides[cpa.require_admin] = lambda: {
        "user_id": "admin-1",
        "username": "admin@example.com",
        "role": "admin",
    }
    return TestClient(app)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_list_returns_all_packages(client, pool):
    pool.fetch.return_value = [
        _make_row(package_code="starter", display_order=0),
        _make_row(package_code="pro", package_name="Pro Pack", credits=5000, price_usd=45.0, display_order=1),
    ]
    res = client.get("/api/v1/admin/credit-packages/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["package_code"] == "starter"
    assert data[1]["credits"] == 5000


def test_list_empty_when_table_missing(client, pool):
    pool.fetch.side_effect = asyncpg.UndefinedTableError("no table")
    res = client.get("/api/v1/admin/credit-packages/")
    assert res.status_code == 200
    assert res.json() == []


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_success(client, pool):
    pool.fetchrow.side_effect = [
        None,  # duplicate check -> not found
        _make_row(package_code="bigpack", package_name="Big Pack", credits=20000, price_usd=150.0),  # INSERT RETURNING
    ]
    payload = {
        "package_code": "bigpack",
        "package_name": "Big Pack",
        "credits": 20000,
        "price_usd": 150.0,
        "discount_percentage": 10,
    }
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["package_code"] == "bigpack"
    assert body["credits"] == 20000
    # Audit was invoked.
    cpa.audit_logger.log.assert_awaited()


def test_create_duplicate_code_409(client, pool):
    pool.fetchrow.return_value = _make_row()  # duplicate check finds an existing row
    payload = {"package_code": "starter", "package_name": "Dupe", "credits": 100, "price_usd": 5.0}
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 409


def test_create_zero_credits_422(client, pool):
    payload = {"package_code": "zero", "package_name": "Zero", "credits": 0, "price_usd": 5.0}
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 422
    assert "credits" in res.json()["detail"].lower()


def test_create_negative_price_422(client, pool):
    payload = {"package_code": "neg", "package_name": "Neg", "credits": 100, "price_usd": -1.0}
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 422
    assert "price_usd" in res.json()["detail"].lower()


def test_create_discount_out_of_range_422(client, pool):
    payload = {
        "package_code": "disc",
        "package_name": "Disc",
        "credits": 100,
        "price_usd": 5.0,
        "discount_percentage": 150,
    }
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 422
    assert "discount" in res.json()["detail"].lower()


def test_create_unique_violation_maps_to_409(client, pool):
    # Passes the pre-check (None) but the INSERT races and raises UniqueViolation.
    pool.fetchrow.side_effect = [None, asyncpg.UniqueViolationError("dup")]
    payload = {"package_code": "race", "package_name": "Race", "credits": 100, "price_usd": 5.0}
    res = client.post("/api/v1/admin/credit-packages/", json=payload)
    assert res.status_code == 409


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_success(client, pool):
    pid = str(uuid.uuid4())
    pool.fetchrow.side_effect = [
        _make_row(id=pid, package_code="starter", price_usd=10.0),  # existing
        _make_row(id=pid, package_code="starter", package_name="Renamed", price_usd=12.0),  # RETURNING
    ]
    res = client.put(f"/api/v1/admin/credit-packages/{pid}", json={"package_name": "Renamed", "price_usd": 12.0})
    assert res.status_code == 200, res.text
    assert res.json()["package_name"] == "Renamed"
    assert res.json()["price_usd"] == 12.0


def test_update_not_found_404(client, pool):
    pool.fetchrow.return_value = None
    pid = str(uuid.uuid4())
    res = client.put(f"/api/v1/admin/credit-packages/{pid}", json={"package_name": "Nope"})
    assert res.status_code == 404


def test_update_empty_body_422(client, pool):
    pid = str(uuid.uuid4())
    pool.fetchrow.return_value = _make_row(id=pid)
    res = client.put(f"/api/v1/admin/credit-packages/{pid}", json={})
    assert res.status_code == 422


def test_update_invalid_credits_422(client, pool):
    pid = str(uuid.uuid4())
    pool.fetchrow.return_value = _make_row(id=pid)
    res = client.put(f"/api/v1/admin/credit-packages/{pid}", json={"credits": 0})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------

def test_soft_delete_success(client, pool):
    pid = str(uuid.uuid4())
    pool.fetchrow.return_value = {"id": pid, "package_code": "starter", "is_active": True}
    res = client.delete(f"/api/v1/admin/credit-packages/{pid}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    # The UPDATE ... SET is_active = FALSE was issued, not a DELETE.
    pool.execute.assert_awaited()
    args = pool.execute.await_args.args
    assert "is_active = FALSE" in args[0].upper().replace("  ", " ") or "IS_ACTIVE = FALSE" in args[0].upper()
    assert args[1] == pid


def test_soft_delete_not_found_404(client, pool):
    pool.fetchrow.return_value = None
    pid = str(uuid.uuid4())
    res = client.delete(f"/api/v1/admin/credit-packages/{pid}")
    assert res.status_code == 404


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
