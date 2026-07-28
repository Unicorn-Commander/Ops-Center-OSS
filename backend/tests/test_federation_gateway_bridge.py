"""
Unit tests for the federation gateway bridge (federation/gateway_bridge.py)
and the consumer-side org propagation in proxy_to_node.

The contract under test: a federated inference call is served under the
CONSUMING org's per-org gateway key (user_id == org_id), provisioned via
the existing gateway_key_provisioning path — so the publisher's gateway
fires the single billable Lago event keyed to the org. Failure modes are
explicit, never silently unmetered.
"""

import pytest

from federation.gateway_bridge import (
    BadFederatedRequest,
    GatewayKeyUnavailable,
    TrustDenied,
    serve_federated_inference,
)
from federation.trust import TrustModeEnforcer


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"choices": [{"message": {"content": "hi"}}]}

    def json(self):
        return self._payload


class FakeHttpClient:
    def __init__(self, response=None):
        self.response = response or FakeResponse()
        self.calls = []

    async def post(self, url, json=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


def full_trust_enforcer():
    e = TrustModeEnforcer(None, local_node_id="self-node")
    e.set_policy_for_tests("peer-1", {"trust_mode": "full"})
    return e


def make_provisioner(result):
    calls = []

    async def provision(org_id=None, **kwargs):
        calls.append(org_id)
        return result

    provision.calls = calls
    return provision


@pytest.mark.asyncio
async def test_happy_path_forwards_under_org_key():
    """The forwarded gateway call must carry the ORG's virtual key — the
    metering identity (user_id == org_id) that keys the Lago event."""
    client = FakeHttpClient()
    provision = make_provisioner(
        {"key_id": "tok-abc", "key": "sk-org-secret", "org_id": "org_123"}
    )
    result = await serve_federated_inference(
        peer_node_id="peer-1",
        org_id="org_123",
        service_type="llm",
        payload={"model": "qwen3.5-27b", "messages": [{"role": "user", "content": "hi"}]},
        trust_enforcer=full_trust_enforcer(),
        key_provisioner=provision,
        gateway_url="http://gateway:4000",
        http_client=client,
    )
    # Key provisioned for the consuming org (idempotent, one key system)
    assert provision.calls == ["org_123"]
    # Forwarded to the gateway's chat path under the org's key
    call = client.calls[0]
    assert call["url"] == "http://gateway:4000/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer sk-org-secret"
    assert call["json"]["model"] == "qwen3.5-27b"
    # The gateway fired the billable event — mark it so meters don't double-fire
    assert result["gateway_metered"] is True
    assert result["org_id"] == "org_123"
    assert result["key_id"] == "tok-abc"
    assert result["status_code"] == 200


@pytest.mark.asyncio
async def test_missing_org_identity_is_rejected():
    with pytest.raises(BadFederatedRequest):
        await serve_federated_inference(
            peer_node_id="peer-1", org_id=None, service_type="llm",
            payload={}, trust_enforcer=full_trust_enforcer(),
            key_provisioner=make_provisioner({"key": "x"}),
            gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
        )


@pytest.mark.asyncio
async def test_unsupported_service_type_is_rejected():
    with pytest.raises(BadFederatedRequest):
        await serve_federated_inference(
            peer_node_id="peer-1", org_id="org_123", service_type="agents",
            payload={}, trust_enforcer=full_trust_enforcer(),
            key_provisioner=make_provisioner({"key": "x"}),
            gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
        )


@pytest.mark.asyncio
async def test_trust_mode_gates_federated_inference():
    e = TrustModeEnforcer(None, local_node_id="self-node")
    e.set_policy_for_tests("peer-1", {"trust_mode": "scoped", "consume": ["embeddings"]})
    with pytest.raises(TrustDenied):
        await serve_federated_inference(
            peer_node_id="peer-1", org_id="org_123", service_type="llm",
            payload={}, trust_enforcer=e,
            key_provisioner=make_provisioner({"key": "x"}),
            gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
        )
    # The allowed service type goes through
    result = await serve_federated_inference(
        peer_node_id="peer-1", org_id="org_123", service_type="embeddings",
        payload={"input": "hello"}, trust_enforcer=e,
        key_provisioner=make_provisioner({"key_id": "t", "key": "sk-1"}),
        gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
    )
    assert result["gateway_metered"] is True


@pytest.mark.asyncio
async def test_provisioning_failure_is_503_never_unmetered():
    with pytest.raises(GatewayKeyUnavailable):
        await serve_federated_inference(
            peer_node_id="peer-1", org_id="org_123", service_type="llm",
            payload={}, trust_enforcer=full_trust_enforcer(),
            key_provisioner=make_provisioner(None),
            gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
        )


@pytest.mark.asyncio
async def test_unretrievable_key_secret_is_503_never_unmetered():
    """A key id without its secret must NOT silently fall back to the
    federation credential — that would unmeter the call."""
    with pytest.raises(GatewayKeyUnavailable):
        await serve_federated_inference(
            peer_node_id="peer-1", org_id="org_123", service_type="llm",
            payload={}, trust_enforcer=full_trust_enforcer(),
            key_provisioner=make_provisioner({"key_id": "tok-abc", "key": None}),
            gateway_url="http://gateway:4000", http_client=FakeHttpClient(),
        )


@pytest.mark.asyncio
async def test_gateway_error_status_is_not_marked_metered():
    client = FakeHttpClient(FakeResponse(status_code=429, payload={"error": "budget"}))
    result = await serve_federated_inference(
        peer_node_id="peer-1", org_id="org_123", service_type="llm",
        payload={}, trust_enforcer=full_trust_enforcer(),
        key_provisioner=make_provisioner({"key_id": "t", "key": "sk-1"}),
        gateway_url="http://gateway:4000", http_client=client,
    )
    assert result["status_code"] == 429
    assert result["gateway_metered"] is False


# ---------------------------------------------------------------------------
# Consumer side — proxy_to_node carries the org identity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_to_node_sends_org_header(monkeypatch):
    from federation.inference_router import InferenceRouter
    from federation.node_registry import NodeRegistry
    from tests.test_federation import FakeRedis

    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)
    await registry.register_node({
        "node_id": "publisher-node",
        "display_name": "Publisher",
        "endpoint_url": "https://publisher.example.com",
        "services": [],
    })

    captured = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"ok": True}

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None, headers=None):
            captured.update({"url": url, "headers": headers})
            return _Resp()

    import federation.inference_router as ir_mod
    monkeypatch.setattr(ir_mod.httpx, "AsyncClient", _Client)

    router = InferenceRouter(registry, local_node_id="self-node")
    result = await router.proxy_to_node(
        "publisher-node", "/api/v1/federation/inference",
        {"service_type": "llm"}, org_id="org_123",
    )
    assert captured["headers"]["X-Federation-Org-Id"] == "org_123"
    assert result["status_code"] == 200
