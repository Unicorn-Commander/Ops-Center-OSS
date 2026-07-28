"""
Unit tests for the core-table schema-drift check + versioned migration runner.

No live DB: the comparison core (`schema_drift.evaluate`) is a pure function, and
the async paths use tiny asyncpg-style fakes (matching the FakePool/FakeConn style
used elsewhere in tests/). Also guards the shipped canonical contract.
"""
import os

import pytest

import schema_drift
import core_migrations


# --------------------------------------------------------------------------- #
# type_class
# --------------------------------------------------------------------------- #
def test_type_class_core_mappings():
    assert schema_drift.type_class("uuid") == "uuid"
    assert schema_drift.type_class("int4") == "int"
    assert schema_drift.type_class("int8") == "int"
    assert schema_drift.type_class("numeric") == "numeric"
    assert schema_drift.type_class("bool") == "bool"
    assert schema_drift.type_class("jsonb") == "json"


def test_type_class_collapses_benign_pairs():
    # varchar<->text and timestamp<->timestamptz are benign (same class)
    assert schema_drift.type_class("varchar") == schema_drift.type_class("text") == "string"
    assert schema_drift.type_class("timestamp") == schema_drift.type_class("timestamptz") == "ts"


def test_type_class_enum_only_matches_itself():
    assert schema_drift.type_class("federation_node_status") == "federation_node_status"
    assert schema_drift.type_class("uuid") != schema_drift.type_class("federation_node_status")


# --------------------------------------------------------------------------- #
# evaluate() — pure comparison
# --------------------------------------------------------------------------- #
def _contract(cols):
    return {"tables": {"t": cols}}


def test_evaluate_ok_when_live_matches():
    contract = _contract({"id": {"class": "uuid"}, "name": {"class": "string"}})
    live = {"t": {"id": "uuid", "name": "varchar"}}  # varchar matches class 'string'
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "ok"
    assert rep["summary"] == {"error": 0, "danger": 0, "info": 0}


def test_evaluate_missing_required_is_error():
    contract = _contract({"id": {"class": "uuid"}, "slug": {"class": "string"}})
    live = {"t": {"id": "uuid"}}
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "drift"
    assert rep["summary"]["error"] == 1
    assert rep["tables"]["t"]["status"] == "drift"


def test_evaluate_missing_optional_is_info_not_drift():
    contract = _contract({"id": {"class": "uuid"}, "legacy": {"class": "string", "optional": True}})
    live = {"t": {"id": "uuid"}}
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "ok"
    assert rep["summary"]["info"] == 1


def test_evaluate_cross_class_signoff_is_danger():
    contract = _contract({"id": {"class": "uuid", "signoff": "int->uuid needs sign-off"}})
    live = {"t": {"id": "int4"}}
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "drift"
    assert rep["summary"]["danger"] == 1
    assert rep["summary"]["error"] == 0
    assert any("int->uuid" in s for s in rep["signoff_pending"])


def test_evaluate_cross_class_without_signoff_is_error():
    contract = _contract({"user_id": {"class": "uuid"}})
    live = {"t": {"user_id": "varchar"}}  # string vs uuid, no signoff flag
    rep = schema_drift.evaluate(contract, live)
    assert rep["summary"]["error"] == 1
    assert rep["summary"]["danger"] == 0


def test_evaluate_benign_same_class_is_ok():
    contract = _contract({"created_at": {"class": "ts"}})
    live = {"t": {"created_at": "timestamp"}}  # canonical timestamptz-class, live timestamp -> same class
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "ok"


def test_evaluate_extra_column_is_info():
    contract = _contract({"id": {"class": "uuid"}})
    live = {"t": {"id": "uuid", "extra": "varchar"}}
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "ok"
    assert rep["summary"]["info"] == 1


def test_evaluate_missing_table_is_error():
    contract = _contract({"id": {"class": "uuid"}})
    rep = schema_drift.evaluate(contract, live={})
    assert rep["status"] == "drift"
    assert rep["tables"]["t"]["status"] == "missing"
    assert rep["summary"]["error"] == 1


# --------------------------------------------------------------------------- #
# async check_drift() with an asyncpg-style fake pool
# --------------------------------------------------------------------------- #
class _Acquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self.applied = {}  # version -> checksum for schema_migrations

    async def fetch(self, query, *args):
        if "information_schema.columns" in query:
            return self.rows
        if "schema_migrations" in query:
            return [{"version": v, "checksum": c} for v, c in self.applied.items()]
        return []

    async def execute(self, query, *args):
        self.executed.append((query, args))
        if "INSERT INTO" in query and "schema_migrations" in query and len(args) >= 2:
            self.applied[args[0]] = args[1]
        return "OK"


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


@pytest.mark.asyncio
async def test_check_drift_end_to_end_with_fake_pool():
    contract = _contract({"id": {"class": "uuid"}, "user_id": {"class": "string"}})
    rows = [
        {"table_name": "t", "column_name": "id", "udt_name": "uuid"},
        {"table_name": "t", "column_name": "user_id", "udt_name": "int4"},  # cross-class -> error
    ]
    pool = FakePool(FakeConn(rows))
    rep = await schema_drift.check_drift(pool, contract)
    assert rep["status"] == "drift"
    assert rep["summary"]["error"] == 1


# --------------------------------------------------------------------------- #
# split_sql_statements
# --------------------------------------------------------------------------- #
def test_split_sql_respects_dollar_quoted_body():
    sql = (
        "ALTER TABLE x ADD COLUMN IF NOT EXISTS a int;\n"
        "DO $$ BEGIN\n  RAISE NOTICE 'hi; still in body';\nEND $$;\n"
        "CREATE INDEX IF NOT EXISTS i ON x(a);\n"
    )
    stmts = core_migrations.split_sql_statements(sql)
    assert len(stmts) == 3
    assert "RAISE NOTICE 'hi; still in body'" in stmts[1]


# --------------------------------------------------------------------------- #
# run_core_migrations — applies once, skips on unchanged checksum
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_run_core_migrations_applies_then_skips(tmp_path, monkeypatch):
    core = tmp_path / "core"
    core.mkdir()
    (core / "0001_demo.sql").write_text(
        "ALTER TABLE demo ADD COLUMN IF NOT EXISTS a int;\n"
        "ALTER TABLE demo ADD COLUMN IF NOT EXISTS b text;\n"
    )
    monkeypatch.setattr(core_migrations, "CORE_DIR", str(core))

    conn = FakeConn()
    pool = FakePool(conn)

    summary1 = await core_migrations.run_core_migrations(pool)
    assert [a["version"] for a in summary1["applied"]] == ["0001_demo"]
    assert conn.applied.get("0001_demo")  # recorded

    # second run: checksum unchanged -> skipped, no re-apply
    summary2 = await core_migrations.run_core_migrations(pool)
    assert summary2["applied"] == []
    assert summary2["skipped_already"] == ["0001_demo"]


@pytest.mark.asyncio
async def test_run_core_migrations_noop_without_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(core_migrations, "CORE_DIR", str(tmp_path / "does_not_exist"))
    summary = await core_migrations.run_core_migrations(FakePool(FakeConn()))
    assert summary["applied"] == []


# --------------------------------------------------------------------------- #
# the SHIPPED canonical contract
# --------------------------------------------------------------------------- #
def test_shipped_contract_is_valid_and_flags_known_signoff_columns():
    contract = schema_drift.load_contract()
    tables = contract["tables"]
    assert len(tables) == 16
    signoff = {f"{t}.{c}" for t, cols in tables.items() for c, s in cols.items() if "signoff" in s}
    # signoff flags mark the PK/identity type changes; each is cleared once signed
    # off + applied, so the remaining set must always be a subset of the known three.
    known = {"credit_packages.id", "user_credits.user_id", "user_provider_keys.user_id"}
    assert signoff <= known
    # credit_packages.id was signed off + applied (both nodes uuid) -> resolved.
    assert "credit_packages.id" not in signoff


def test_shipped_contract_reports_ok_against_itself():
    # A node whose live schema == canonical (one representative udt per class)
    # must report OK — proves the contract isn't self-contradictory.
    contract = schema_drift.load_contract()
    rep_udt = {"uuid": "uuid", "int": "int4", "numeric": "numeric", "bool": "bool",
               "json": "jsonb", "string": "varchar", "ts": "timestamptz"}
    live = {}
    for t, cols in contract["tables"].items():
        live[t] = {}
        for c, spec in cols.items():
            if spec.get("optional"):
                continue
            cls = spec["class"]
            live[t][c] = rep_udt.get(cls, cls)  # enums map to themselves
    rep = schema_drift.evaluate(contract, live)
    assert rep["status"] == "ok", rep["summary"]
