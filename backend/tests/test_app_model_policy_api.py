"""
Unit tests for the app_model_policy admin CRUD API (app_model_policy_api.py).

Contract under test:
  - default-safe: empty table lists cleanly (no 500), changes nothing
  - create + list round-trip
  - validation: bad policy / bad model / empty app are rejected (422), not 500'd
  - duplicate (app, model) -> 409
  - update policy and/or note (404 when missing, 400 when nothing provided)
  - delete (404 when missing)
  - 503 when no DB pool

Follows the federation-test style: an in-memory FakePool stands in for asyncpg,
and the route handlers are called directly (the require_admin dependency is
bypassed by passing admin_user= explicitly, exactly as FastAPI would inject it).
"""

import asyncpg
import pytest
from pydantic import ValidationError

import app_model_policy_api as api
from app_model_policy_api import (
    PolicyCreate,
    PolicyUpdate,
    create_policy,
    delete_policy,
    list_policies,
    update_policy,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakePool:
    """In-memory stand-in for an asyncpg pool backing app_model_policy.

    Implements just the calls the router makes: fetch / fetchrow / execute,
    with an enforced UNIQUE(app, model) so the 409 path is exercised.
    """

    def __init__(self):
        self.rows = []
        self._next_id = 1

    def _insert(self, app, model, policy, note):
        for r in self.rows:
            if r["app"] == app and r["model"] == model:
                raise asyncpg.UniqueViolationError(
                    "duplicate key value violates unique constraint"
                )
        row = {
            "id": self._next_id,
            "app": app,
            "model": model,
            "policy": policy,
            "note": note,
            "created_at": None,
        }
        self._next_id += 1
        self.rows.append(row)
        return row

    async def fetch(self, query, *params):
        # Only query is the ordered SELECT all
        return sorted(self.rows, key=lambda r: (r["app"], r["model"]))

    async def fetchrow(self, query, *params):
        q = " ".join(query.split())
        if q.startswith("INSERT INTO app_model_policy"):
            app, model, policy, note = params
            return self._insert(app, model, policy, note)
        if q.startswith("SELECT") and "WHERE id =" in q:
            (pid,) = params
            for r in self.rows:
                if r["id"] == pid:
                    return r
            return None
        if q.startswith("UPDATE app_model_policy"):
            policy, note, pid = params
            for r in self.rows:
                if r["id"] == pid:
                    r["policy"] = policy
                    r["note"] = note
                    return r
            return None
        raise AssertionError(f"unexpected fetchrow query: {q}")

    async def execute(self, query, *params):
        q = " ".join(query.split())
        if q.startswith("DELETE FROM app_model_policy"):
            (pid,) = params
            before = len(self.rows)
            self.rows = [r for r in self.rows if r["id"] != pid]
            return f"DELETE {before - len(self.rows)}"
        raise AssertionError(f"unexpected execute query: {q}")


class _State:
    def __init__(self, pool):
        self.db_pool = pool


class _App:
    def __init__(self, pool):
        self.state = _State(pool)


class FakeRequest:
    def __init__(self, pool):
        self.app = _App(pool)


ADMIN = {"id": "admin-1", "username": "admin@example.com", "role": "admin"}


@pytest.fixture(autouse=True)
def _no_real_audit(monkeypatch):
    """Stub the audit hook so tests don't touch the SQLite audit DB / filesystem."""
    async def _fake_audit(*args, **kwargs):
        return None
    monkeypatch.setattr(api, "_audit", _fake_audit)


# ---------------------------------------------------------------------------
# Validation (Pydantic models) — bad input rejected, not 500'd
# ---------------------------------------------------------------------------

def test_bad_policy_rejected():
    with pytest.raises(ValidationError):
        PolicyCreate(app="meeting-ops-service", model="gpt-4o", policy="free")


def test_empty_app_rejected():
    with pytest.raises(ValidationError):
        PolicyCreate(app="   ", model="gpt-4o", policy="included")


def test_empty_model_rejected():
    with pytest.raises(ValidationError):
        PolicyCreate(app="meeting-ops-service", model="", policy="included")


def test_bad_model_wildcard_rejected():
    # '*' is only valid as a trailing prefix or the bare wildcard
    with pytest.raises(ValidationError):
        PolicyCreate(app="mo", model="Qwen*3.6", policy="included")
    with pytest.raises(ValidationError):
        PolicyCreate(app="mo", model="*-vision", policy="included")


def test_valid_model_forms_accepted():
    assert PolicyCreate(app="mo", model="gpt-4o", policy="included").model == "gpt-4o"
    assert PolicyCreate(app="mo", model="Qwen3.6-*", policy="included").model == "Qwen3.6-*"
    assert PolicyCreate(app="mo", model="*", policy="included").model == "*"


def test_policy_normalized_lowercase():
    assert PolicyCreate(app="mo", model="gpt-4o", policy="INCLUDED").policy == "included"


def test_update_requires_valid_policy():
    with pytest.raises(ValidationError):
        PolicyUpdate(policy="bogus")
    assert PolicyUpdate(policy="metered").policy == "metered"
    assert PolicyUpdate(note="just a note").note == "just a note"


# ---------------------------------------------------------------------------
# CRUD round-trips
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_list_is_clean():
    req = FakeRequest(FakePool())
    rows = await list_policies(req, admin_user=ADMIN)
    assert rows == []


@pytest.mark.asyncio
async def test_create_then_list_round_trip():
    req = FakeRequest(FakePool())
    created = await create_policy(
        PolicyCreate(app="meeting-ops-service", model="Qwen3.6-*", policy="included", note="bundled summaries"),
        req,
        admin_user=ADMIN,
    )
    assert created["id"] == 1
    assert created["app"] == "meeting-ops-service"
    assert created["model"] == "Qwen3.6-*"
    assert created["policy"] == "included"
    assert created["note"] == "bundled summaries"

    rows = await list_policies(req, admin_user=ADMIN)
    assert len(rows) == 1
    assert rows[0]["model"] == "Qwen3.6-*"


@pytest.mark.asyncio
async def test_list_is_ordered_by_app_then_model():
    req = FakeRequest(FakePool())
    await create_policy(PolicyCreate(app="brand-ops", model="gpt-4o", policy="metered"), req, admin_user=ADMIN)
    await create_policy(PolicyCreate(app="meeting-ops-service", model="*", policy="included"), req, admin_user=ADMIN)
    await create_policy(PolicyCreate(app="brand-ops", model="*", policy="included"), req, admin_user=ADMIN)
    rows = await list_policies(req, admin_user=ADMIN)
    assert [(r["app"], r["model"]) for r in rows] == [
        ("brand-ops", "*"),
        ("brand-ops", "gpt-4o"),
        ("meeting-ops-service", "*"),
    ]


@pytest.mark.asyncio
async def test_duplicate_returns_409():
    req = FakeRequest(FakePool())
    await create_policy(PolicyCreate(app="mo", model="gpt-4o", policy="included"), req, admin_user=ADMIN)
    with pytest.raises(api.HTTPException) as exc:
        await create_policy(PolicyCreate(app="mo", model="gpt-4o", policy="metered"), req, admin_user=ADMIN)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_policy_and_note():
    req = FakeRequest(FakePool())
    created = await create_policy(
        PolicyCreate(app="mo", model="gpt-4o", policy="metered"), req, admin_user=ADMIN
    )
    updated = await update_policy(
        created["id"], PolicyUpdate(policy="included", note="now bundled"), req, admin_user=ADMIN
    )
    assert updated["policy"] == "included"
    assert updated["note"] == "now bundled"

    # partial update: note only, policy preserved
    updated2 = await update_policy(
        created["id"], PolicyUpdate(note="changed reason"), req, admin_user=ADMIN
    )
    assert updated2["policy"] == "included"
    assert updated2["note"] == "changed reason"


@pytest.mark.asyncio
async def test_update_missing_returns_404():
    req = FakeRequest(FakePool())
    with pytest.raises(api.HTTPException) as exc:
        await update_policy(999, PolicyUpdate(policy="included"), req, admin_user=ADMIN)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_with_nothing_returns_400():
    req = FakeRequest(FakePool())
    created = await create_policy(
        PolicyCreate(app="mo", model="gpt-4o", policy="metered"), req, admin_user=ADMIN
    )
    with pytest.raises(api.HTTPException) as exc:
        await update_policy(created["id"], PolicyUpdate(), req, admin_user=ADMIN)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_then_gone():
    req = FakeRequest(FakePool())
    created = await create_policy(
        PolicyCreate(app="mo", model="gpt-4o", policy="included"), req, admin_user=ADMIN
    )
    result = await delete_policy(created["id"], req, admin_user=ADMIN)
    assert result is None
    rows = await list_policies(req, admin_user=ADMIN)
    assert rows == []


@pytest.mark.asyncio
async def test_delete_missing_returns_404():
    req = FakeRequest(FakePool())
    with pytest.raises(api.HTTPException) as exc:
        await delete_policy(12345, req, admin_user=ADMIN)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_no_pool_returns_503():
    class NoPoolState:
        db_pool = None

    class NoPoolApp:
        state = NoPoolState()

    class NoPoolRequest:
        app = NoPoolApp()

    with pytest.raises(api.HTTPException) as exc:
        await list_policies(NoPoolRequest(), admin_user=ADMIN)
    assert exc.value.status_code == 503
