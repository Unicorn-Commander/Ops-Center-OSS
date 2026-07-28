"""
Unit tests for the Layer-2 agent contract (federation/agent_bridge.py)
and per-agent (resource-scoped) trust ACLs.

Contract: a federated agent invocation is trust-gated PER AGENT, runs under
the consuming org's identity, and a COMPLETED invocation fires exactly one
agent_invocation Lago event keyed to the org with the agent's outcome price
in units. Failed invocations are not billed.
"""

import pytest

from federation.agent_bridge import serve_federated_agent_invoke
from federation.gateway_bridge import (
    BadFederatedRequest,
    TrustDenied,
)
from federation.trust import TrustModeEnforcer

from tests.test_federation_trust_modes import FakePool


class FakeBrigadeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {
            "status": "completed", "result": "AGENT-OK",
            "model_used": "local/gemma", "error": None,
        }

    def json(self):
        return self._payload


class FakeBrigadeClient:
    def __init__(self, response=None):
        self.response = response or FakeBrigadeResponse()
        self.calls = []

    async def post(self, url, json=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


class LagoCapture:
    def __init__(self):
        self.events = []

    async def __call__(self, **kwargs):
        self.events.append(kwargs)


def enforcer_with(policy):
    e = TrustModeEnforcer(None, local_node_id="self-node")
    e.set_policy_for_tests("peer-1", policy)
    return e


async def invoke(*, enforcer, client=None, lago=None, org_id="org_123",
                 agent_id="sql-analyst", task="do it", db_pool=None):
    return await serve_federated_agent_invoke(
        peer_node_id="peer-1", org_id=org_id, agent_id=agent_id, task=task,
        trust_enforcer=enforcer, brigade_url="http://brigade:8100",
        brigade_key="bk-test", http_client=client or FakeBrigadeClient(),
        lago_reporter=lago or LagoCapture(), db_pool=db_pool,
    )


# ---------------------------------------------------------------------------
# Per-agent ACL semantics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resource_scoped_acl_gates_individual_agents():
    e = enforcer_with({"trust_mode": "scoped", "consume": ["agents/sql-analyst"]})
    # The granted agent works
    result = await invoke(enforcer=e, agent_id="sql-analyst")
    assert result["status"] == "completed"
    # A different agent on the same node is denied
    with pytest.raises(TrustDenied):
        await invoke(enforcer=e, agent_id="col-finance")


@pytest.mark.asyncio
async def test_bare_type_grant_covers_all_agents():
    e = enforcer_with({"trust_mode": "scoped", "consume": ["agents"]})
    assert (await invoke(enforcer=e, agent_id="sql-analyst"))["status"] == "completed"
    assert (await invoke(enforcer=e, agent_id="col-finance"))["status"] == "completed"


@pytest.mark.asyncio
async def test_visible_resources_narrows_discovery():
    e = enforcer_with({"trust_mode": "scoped", "publish": ["agents/sql-analyst", "llm"]})
    # Catalog still shows the agents TYPE...
    assert "agents" in await e.visible_service_types("peer-1")
    # ...but only the granted agent id is listable
    assert await e.visible_resources("peer-1", "agents") == {"sql-analyst"}
    # Bare-type publish → all resources (None)
    e2 = enforcer_with({"trust_mode": "scoped", "publish": ["agents"]})
    assert await e2.visible_resources("peer-1", "agents") is None
    # Isolated → nothing
    e3 = enforcer_with({"trust_mode": "isolated"})
    assert await e3.visible_resources("peer-1", "agents") == set()


# ---------------------------------------------------------------------------
# Invocation + outcome metering
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completed_invocation_fires_one_org_keyed_event():
    lago = LagoCapture()
    client = FakeBrigadeClient()
    result = await invoke(
        enforcer=enforcer_with({"trust_mode": "full"}), client=client, lago=lago,
    )
    # Forwarded to the local Brigade A2A path with our credential
    call = client.calls[0]
    assert call["url"].endswith("/api/v1/a2a/agents/sql-analyst/invoke")
    assert call["headers"]["X-API-Key"] == "bk-test"
    assert call["json"] == {"task": "do it"}
    # Exactly one outcome event keyed to the consuming org
    assert len(lago.events) == 1
    ev = lago.events[0]
    assert ev["org_id"] == "org_123"
    assert ev["agent_id"] == "sql-analyst"
    assert ev["units"] == 1.0  # default price
    assert result["agent_metered"] is True
    assert result["result"] == "AGENT-OK"


@pytest.mark.asyncio
async def test_failed_invocation_is_not_billed():
    lago = LagoCapture()
    client = FakeBrigadeClient(FakeBrigadeResponse(payload={
        "status": "failed", "result": None, "error": "boom",
    }))
    result = await invoke(
        enforcer=enforcer_with({"trust_mode": "full"}), client=client, lago=lago,
    )
    assert result["status"] == "failed"
    assert result["agent_metered"] is False
    assert result["units"] == 0.0
    assert lago.events == []  # no billable event for failures


@pytest.mark.asyncio
async def test_per_agent_pricing_from_platform_settings():
    rows = []  # no peer rows; default full
    pool = FakePool(rows)

    # Extend the FakeConn to answer the pricing query
    class PricedConn:
        async def fetch(self, q, *p):
            return rows
        async def fetchval(self, q, *p):
            if "FEDERATION_AGENT_PRICING" in q:
                return '{"deep-research": 50, "default": 2}'
            return None

    class PricedPool:
        def acquire(self):
            class _Ctx:
                async def __aenter__(self_inner):
                    return PricedConn()
                async def __aexit__(self_inner, *exc):
                    return False
            return _Ctx()

    lago = LagoCapture()
    result = await invoke(
        enforcer=enforcer_with({"trust_mode": "full"}),
        agent_id="deep-research", lago=lago, db_pool=PricedPool(),
    )
    assert result["units"] == 50.0
    assert lago.events[0]["units"] == 50.0
    # Unlisted agent gets the configured default
    lago2 = LagoCapture()
    result2 = await invoke(
        enforcer=enforcer_with({"trust_mode": "full"}),
        agent_id="sql-analyst", lago=lago2, db_pool=PricedPool(),
    )
    assert result2["units"] == 2.0


@pytest.mark.asyncio
async def test_missing_org_or_task_rejected():
    e = enforcer_with({"trust_mode": "full"})
    with pytest.raises(BadFederatedRequest):
        await invoke(enforcer=e, org_id=None)
    with pytest.raises(BadFederatedRequest):
        await invoke(enforcer=e, task="")


@pytest.mark.asyncio
async def test_unknown_agent_404s_cleanly():
    client = FakeBrigadeClient(FakeBrigadeResponse(status_code=404, payload={}))
    with pytest.raises(BadFederatedRequest):
        await invoke(enforcer=enforcer_with({"trust_mode": "full"}), client=client)
