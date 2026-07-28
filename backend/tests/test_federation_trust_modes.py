"""
Unit tests for federation trust-mode enforcement (federation/trust.py)
and its wiring into the inference router.

Covers every trust_mode × publish/consume combination from
FEDERATION_TRUST_MODES.md: full, scoped (allowed + denied subsets),
consumer, publisher, isolated, unknown-peer defaults, inactive rows,
and unknown modes in the DB (fail closed).
"""

import pytest

from federation.inference_router import InferenceRouter
from federation.node_registry import NodeRegistry
from federation.trust import TrustModeEnforcer

from tests.test_federation import FakeRedis


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeAcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, rows, settings=None):
        self.rows = rows
        self.settings = settings or {}

    async def fetch(self, query, *params):
        return self.rows

    async def fetchval(self, query, *params):
        if "platform_settings" in query:
            return self.settings.get("FEDERATION_DEFAULT_TRUST_MODE")
        return None


class FakePool:
    """Minimal asyncpg-pool stand-in returning canned federation_peers rows."""

    def __init__(self, rows, settings=None):
        self.rows = rows
        self.settings = settings

    def acquire(self):
        return _FakeAcquireCtx(FakeConn(self.rows, self.settings))


def make_enforcer(policies=None, *, default_mode="full"):
    enforcer = TrustModeEnforcer(None, local_node_id="self-node", default_mode=default_mode)
    for peer, policy in (policies or {}).items():
        enforcer.set_policy_for_tests(peer, policy)
    return enforcer


# ---------------------------------------------------------------------------
# Mode semantics — inbound visibility (publish), inbound calls (consume),
# outbound consumption
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_mode_allows_everything():
    e = make_enforcer({"peer": {"trust_mode": "full"}})
    assert await e.visible_service_types("peer") is None  # None = all
    assert (await e.peer_may_call("peer", "llm"))[0] is True
    assert (await e.we_may_consume("peer", "llm"))[0] is True


@pytest.mark.asyncio
async def test_scoped_mode_enforces_publish_and_consume_acls():
    e = make_enforcer({
        "peer": {"trust_mode": "scoped", "publish": ["llm"], "consume": ["embeddings"]}
    })
    # Peer SEES only publish[]
    assert await e.visible_service_types("peer") == {"llm"}
    # Peer CALLS only consume[]
    assert (await e.peer_may_call("peer", "embeddings"))[0] is True
    assert (await e.peer_may_call("peer", "llm"))[0] is False
    assert (await e.peer_may_call("peer", "music_gen"))[0] is False  # fail-closed
    # We call out only consume[]
    assert (await e.we_may_consume("peer", "embeddings"))[0] is True
    assert (await e.we_may_consume("peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_scoped_empty_acls_deny_everything():
    e = make_enforcer({"peer": {"trust_mode": "scoped"}})
    assert await e.visible_service_types("peer") == set()
    assert (await e.peer_may_call("peer", "llm"))[0] is False
    assert (await e.we_may_consume("peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_consumer_mode_is_outbound_only():
    e = make_enforcer({"peer": {"trust_mode": "consumer"}})
    # We may call the peer...
    assert (await e.we_may_consume("peer", "llm"))[0] is True
    # ...but the peer sees and calls nothing on us.
    assert await e.visible_service_types("peer") == set()
    assert (await e.peer_may_call("peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_publisher_mode_is_inbound_only():
    e = make_enforcer({"peer": {"trust_mode": "publisher"}})
    # Peer sees and may call everything on us...
    assert await e.visible_service_types("peer") is None
    assert (await e.peer_may_call("peer", "llm"))[0] is True
    # ...but we never call out to it.
    assert (await e.we_may_consume("peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_isolated_mode_exposes_nothing():
    e = make_enforcer({"peer": {"trust_mode": "isolated"}})
    assert await e.visible_service_types("peer") == set()
    assert (await e.peer_may_call("peer", "llm"))[0] is False
    assert (await e.we_may_consume("peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_unknown_peer_uses_default_mode():
    # Backward-compatible default (full) — unknown peers unrestricted
    e_full = make_enforcer()
    assert (await e_full.peer_may_call("stranger", "llm"))[0] is True
    # Hardened default — unknown peers denied everything
    e_iso = make_enforcer(default_mode="isolated")
    assert (await e_iso.peer_may_call("stranger", "llm"))[0] is False
    assert (await e_iso.we_may_consume("stranger", "llm"))[0] is False
    assert await e_iso.visible_service_types("stranger") == set()


# ---------------------------------------------------------------------------
# DB loading and normalization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_loads_rows_and_fails_closed_on_bad_data():
    rows = [
        # publish/consume arrive as JSON strings from JSONB sometimes
        {"peer_node_id": "scoped-peer", "trust_mode": "scoped",
         "publish": '["llm"]', "consume": '["embeddings"]', "is_active": True},
        # inactive rows are treated as isolated
        {"peer_node_id": "inactive-peer", "trust_mode": "full",
         "publish": [], "consume": [], "is_active": False},
        # unknown trust_mode value fails closed to isolated
        {"peer_node_id": "weird-peer", "trust_mode": "frenemy",
         "publish": [], "consume": [], "is_active": True},
    ]
    e = TrustModeEnforcer(FakePool(rows), local_node_id="self-node")
    await e.refresh()

    assert await e.visible_service_types("scoped-peer") == {"llm"}
    assert (await e.peer_may_call("scoped-peer", "embeddings"))[0] is True
    assert (await e.peer_may_call("inactive-peer", "llm"))[0] is False
    assert (await e.we_may_consume("weird-peer", "llm"))[0] is False


@pytest.mark.asyncio
async def test_default_mode_flippable_via_platform_settings():
    """Deny-by-default can be enabled with a SQL UPDATE — no container
    recreate. platform_settings overrides the env default at refresh."""
    pool = FakePool([], settings={"FEDERATION_DEFAULT_TRUST_MODE": "isolated"})
    e = TrustModeEnforcer(pool, local_node_id="self-node", default_mode="full")
    await e.refresh()
    assert e.default_mode == "isolated"
    assert (await e.peer_may_call("stranger", "llm"))[0] is False
    # Invalid DB values are ignored (env/constructor default stands)
    pool2 = FakePool([], settings={"FEDERATION_DEFAULT_TRUST_MODE": "frenemy"})
    e2 = TrustModeEnforcer(pool2, local_node_id="self-node", default_mode="full")
    await e2.refresh()
    assert e2.default_mode == "full"


@pytest.mark.asyncio
async def test_filter_catalog_for_peer():
    e = make_enforcer({
        "scoped-peer": {"trust_mode": "scoped", "publish": ["embeddings"]},
        "full-peer": {"trust_mode": "full"},
        "iso-peer": {"trust_mode": "isolated"},
    })
    catalog = [
        {"service_type": "llm", "node_id": "self-node"},
        {"service_type": "embeddings", "node_id": "self-node"},
        {"service_type": "agents", "node_id": "self-node"},
    ]
    assert await e.filter_catalog_for_peer(catalog, "full-peer") == catalog
    scoped = await e.filter_catalog_for_peer(catalog, "scoped-peer")
    assert [s["service_type"] for s in scoped] == ["embeddings"]
    assert await e.filter_catalog_for_peer(catalog, "iso-peer") == []


# ---------------------------------------------------------------------------
# Inference router integration — outbound candidate filtering
# ---------------------------------------------------------------------------

async def _registry_with_two_peers():
    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)
    for node_id in ("peer-allowed", "peer-blocked"):
        await registry.register_node({
            "node_id": node_id,
            "display_name": node_id,
            "endpoint_url": f"https://{node_id}.example.com",
            "services": [{
                "service_type": "llm",
                "models": ["qwen-fed"],
                "endpoint_path": "/llm",
                "status": "running",
                "capabilities": {},
                "avg_latency_ms": 100,
                "cost_usd": 0.0,
            }],
        })
    return registry


@pytest.mark.asyncio
async def test_router_skips_trust_blocked_peers():
    registry = await _registry_with_two_peers()
    enforcer = make_enforcer({
        "peer-allowed": {"trust_mode": "full"},
        "peer-blocked": {"trust_mode": "isolated"},
    })
    router = InferenceRouter(registry, local_node_id="self-node", trust_enforcer=enforcer)

    route = await router.route({"service_type": "llm", "model": "qwen-fed"})
    assert route["route_type"] == "federated"
    assert route["target_node_id"] == "peer-allowed"


@pytest.mark.asyncio
async def test_router_scoped_acl_gates_outbound_service_types():
    registry = await _registry_with_two_peers()
    enforcer = make_enforcer({
        # llm NOT in consume[] → both peers unroutable for llm
        "peer-allowed": {"trust_mode": "scoped", "consume": ["embeddings"]},
        "peer-blocked": {"trust_mode": "publisher"},
    })
    router = InferenceRouter(registry, local_node_id="self-node", trust_enforcer=enforcer)

    route = await router.route({"service_type": "llm", "model": "qwen-fed"})
    # No peer candidate may serve llm; llm falls back to cloud (model unknown there,
    # but the cloud candidate is synthesized unconditionally for llm).
    assert route["route_type"] != "federated"


@pytest.mark.asyncio
async def test_router_all_peers_allowed_under_default_full():
    registry = await _registry_with_two_peers()
    enforcer = make_enforcer()  # no rows; default full
    router = InferenceRouter(registry, local_node_id="self-node", trust_enforcer=enforcer)
    route = await router.route({"service_type": "llm", "model": "qwen-fed"})
    assert route["route_type"] == "federated"
    assert route["target_node_id"] in {"peer-allowed", "peer-blocked"}
