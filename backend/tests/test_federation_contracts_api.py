import json
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

audit_logger_stub = types.ModuleType("audit_logger")
audit_logger_stub.audit_logger = None
sys.modules.setdefault("audit_logger", audit_logger_stub)

audit_helpers_stub = types.ModuleType("audit_helpers")
audit_helpers_stub.get_client_ip = lambda request: "testclient"
audit_helpers_stub.get_session_id = lambda request: None
audit_helpers_stub.get_user_agent = lambda request: "pytest"
sys.modules.setdefault("audit_helpers", audit_helpers_stub)

import federation_contracts_api as contracts_api
from federation_contracts_api import require_admin, router


class _AcquireCtx:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, pool):
        self.pool = pool

    async def fetchval(self, query, *params):
        if "FROM federation_config" in query:
            return self.pool.local_node_id
        if "platform_settings" in query:
            key = params[0] if params else "FEDERATION_DEFAULT_TRUST_MODE"
            return self.pool.settings.get(key)
        return None

    async def fetchrow(self, query, *params):
        if "FROM federation_peers" not in query:
            return None
        peer_row_id = params[0]
        if peer_row_id != self.pool.contract["id"]:
            return None
        return dict(self.pool.contract)

    async def fetch(self, query, *params):
        if "FROM federation_services" in query:
            return [{"models": '["sql-analyst", "finance.ops"]'}]
        if "FROM federation_peers" in query:
            contract = self.pool.contract
            return [
                {
                    "peer_row_id": contract["id"],
                    "remote_node_id": contract["remote_node_id"],
                    "display_name": "Peer Node",
                    "status": "online",
                    "last_heartbeat": None,
                    "trust_mode": contract["trust_mode"],
                    "publish": contract["publish"],
                    "consume": contract["consume"],
                    "is_active": contract["is_active"],
                    "capability_token": "secret-token",
                    "authority_for": '["billing"]',
                    "consumer_of": [],
                }
            ]
        return []

    async def execute(self, query, *params):
        if "INSERT INTO platform_settings" in query:
            key, value = params[0], params[1]
            self.pool.settings[key] = value
            self.pool.executed.append(("platform_settings", key, value))
            return "INSERT 0 1"

        if "UPDATE federation_peers SET" in query:
            values = list(params[:-1])
            for clause in query.split("SET", 1)[1].split("WHERE", 1)[0].split(","):
                name = clause.strip().split("=", 1)[0].strip()
                value = values.pop(0)
                if name in {"trust_mode", "publish", "consume", "is_active"}:
                    self.pool.contract[name] = value
            self.pool.executed.append(("federation_peers", params[-1], query))
            return "UPDATE 1"

        self.pool.executed.append(("other", query, params))
        return "OK"


class FakePool:
    def __init__(self):
        self.local_node_id = "self-node"
        self.settings = {}
        self.executed = []
        self.contract = {
            "id": "peer-row-1",
            "local_node_id": "self-node",
            "remote_node_id": "peer-node",
            "trust_mode": "full",
            "publish": "[]",
            "consume": "[]",
            "is_active": True,
        }

    def acquire(self):
        return _AcquireCtx(FakeConn(self))

    async def fetchval(self, query, *params):
        return await FakeConn(self).fetchval(query, *params)

    async def fetchrow(self, query, *params):
        return await FakeConn(self).fetchrow(query, *params)

    async def fetch(self, query, *params):
        return await FakeConn(self).fetch(query, *params)

    async def execute(self, query, *params):
        return await FakeConn(self).execute(query, *params)


class FakeAuditLogger:
    def __init__(self):
        self.entries = []

    async def log(self, **kwargs):
        self.entries.append(kwargs)
        return len(self.entries)


def _make_client(monkeypatch):
    pool = FakePool()
    audit = FakeAuditLogger()
    monkeypatch.setenv("FEDERATION_LOCAL_NODE_ID", "self-node")
    # Isolate from ambient / other-test env pollution: the platform_settings PUT
    # handler sets os.environ[FEDERATION_DEFAULT_TRUST_MODE] in-process (by design,
    # for immediate effect), which leaks across tests in one pytest process. Clear
    # it so the default resolves from the (empty) FakePool platform_settings -> "full".
    monkeypatch.delenv("FEDERATION_DEFAULT_TRUST_MODE", raising=False)
    monkeypatch.setattr(contracts_api, "audit_logger", audit)

    app = FastAPI()
    app.state.db_pool = pool
    app.dependency_overrides[require_admin] = lambda: {
        "id": "admin-1",
        "email": "admin@example.com",
        "is_admin": True,
    }
    app.include_router(router)
    return TestClient(app), pool, audit


def test_bad_trust_mode_returns_422(monkeypatch):
    client, pool, _ = _make_client(monkeypatch)

    response = client.put(
        "/api/v1/admin/federation/contracts/peer-row-1",
        json={"trust_mode": "frenemy"},
    )

    assert response.status_code == 422
    assert pool.contract["trust_mode"] == "full"


def test_malformed_agent_grant_returns_422(monkeypatch):
    client, pool, _ = _make_client(monkeypatch)

    response = client.put(
        "/api/v1/admin/federation/contracts/peer-row-1",
        json={"trust_mode": "scoped", "consume": ["agents/"]},
    )

    assert response.status_code == 422
    assert "Invalid consume entry" in response.json()["detail"]
    assert pool.contract["consume"] == "[]"


def test_scoped_update_persists_jsonb_acl_and_audits(monkeypatch):
    client, pool, audit = _make_client(monkeypatch)

    response = client.put(
        "/api/v1/admin/federation/contracts/peer-row-1",
        json={
            "trust_mode": "scoped",
            "publish": ["agents/sql-analyst"],
            "consume": ["llm"],
            "is_active": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trust_mode"] == "scoped"
    assert body["publish"] == ["agents/sql-analyst"]
    assert body["consume"] == ["llm"]
    assert pool.contract["trust_mode"] == "scoped"
    assert json.loads(pool.contract["publish"]) == ["agents/sql-analyst"]
    assert json.loads(pool.contract["consume"]) == ["llm"]
    assert audit.entries[0]["action"] == "federation.contract.update"
    assert audit.entries[0]["metadata"]["peer_node_id"] == "peer-node"
    assert audit.entries[0]["metadata"]["before"]["trust_mode"] == "full"
    assert audit.entries[0]["metadata"]["after"]["trust_mode"] == "scoped"


def test_default_trust_mode_upsert_writes_platform_settings_key(monkeypatch):
    client, pool, audit = _make_client(monkeypatch)

    response = client.put(
        "/api/v1/admin/federation/contracts/default-trust-mode",
        json={"trust_mode": "isolated"},
    )

    assert response.status_code == 200
    assert response.json()["trust_mode"] == "isolated"
    assert pool.settings["FEDERATION_DEFAULT_TRUST_MODE"] == "isolated"
    assert ("platform_settings", "FEDERATION_DEFAULT_TRUST_MODE", "isolated") in pool.executed
    assert audit.entries[0]["action"] == "federation.default_trust_mode.update"


def test_list_contracts_normalizes_json_and_hides_token(monkeypatch):
    client, _, _ = _make_client(monkeypatch)

    response = client.get("/api/v1/admin/federation/contracts")

    assert response.status_code == 200
    body = response.json()
    assert body["local_node_id"] == "self-node"
    assert body["default_trust_mode"] == "full"
    assert body["contracts"][0]["capability_token"] is True
    assert body["contracts"][0]["authority_for"] == ["billing"]
