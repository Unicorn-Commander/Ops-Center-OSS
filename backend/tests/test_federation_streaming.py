"""
True SSE stream-through for federated inference.

Publisher side (gateway_bridge.serve_federated_inference_stream): runs the
trust/key/url prep eagerly (pre-stream failures map to HTTP status), then
relays the gateway's SSE bytes verbatim; a gateway-level error degrades to an
in-band SSE error event.

Consumer side (federation_llm_bridge.stream_llm_via_federation): forwards
stream=true under the org identity with a signed federation JWT and relays the
publisher's bytes to the customer.
"""

import pytest

import federation.gateway_bridge as gw
import federation_llm_bridge as bridge
from federation.gateway_bridge import TrustDenied, serve_federated_inference_stream
from federation.trust import TrustModeEnforcer


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeStreamResponse:
    def __init__(self, status_code=200, chunks=None, err_body=b"boom"):
        self.status_code = status_code
        self._chunks = chunks or [b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n',
                                  b"data: [DONE]\n\n"]
        self._err_body = err_body

    async def aiter_bytes(self):
        for c in self._chunks:
            yield c

    async def aread(self):
        return self._err_body


class FakeStreamCtx:
    def __init__(self, response, sink):
        self.response = response
        self.sink = sink

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, *a):
        return False


class FakeStreamClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def stream(self, method, url, json=None, headers=None):
        self.calls.append({"method": method, "url": url, "json": json, "headers": headers})
        return FakeStreamCtx(self.response, self.calls)


def full_trust_enforcer():
    e = TrustModeEnforcer(None, local_node_id="self-node")
    e.set_policy_for_tests("peer-1", {"trust_mode": "full"})
    return e


def isolated_enforcer():
    e = TrustModeEnforcer(None, local_node_id="self-node")
    e.set_policy_for_tests("peer-1", {"trust_mode": "isolated"})
    return e


def make_provisioner(key="sk-org-key"):
    async def provision(org_id=None, **kw):
        return {"key": key, "key_id": "key_abc123"}
    return provision


# ---------------------------------------------------------------------------
# Publisher side
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stream_prep_denies_before_any_bytes():
    """A trust-denied peer must raise during prep, not mid-stream."""
    with pytest.raises(TrustDenied):
        await serve_federated_inference_stream(
            peer_node_id="peer-1", org_id="org_1", service_type="llm",
            payload={"model": "m", "messages": [], "stream": True},
            trust_enforcer=isolated_enforcer(),
            key_provisioner=make_provisioner(),
            gateway_url="http://gw:4000",
            http_client=FakeStreamClient(FakeStreamResponse()),
        )


@pytest.mark.asyncio
async def test_stream_relays_gateway_chunks_under_org_key():
    client = FakeStreamClient(FakeStreamResponse())
    agen = await serve_federated_inference_stream(
        peer_node_id="peer-1", org_id="org_1", service_type="llm",
        payload={"model": "m", "messages": [], "stream": True},
        trust_enforcer=full_trust_enforcer(),
        key_provisioner=make_provisioner(),
        gateway_url="http://gw:4000",
        http_client=client,
    )
    out = b"".join([c async for c in agen])
    assert b"[DONE]" in out and b'"content":"hi"' in out
    # Forwarded under the org's gateway key, to the chat path.
    call = client.calls[0]
    assert call["url"] == "http://gw:4000/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer sk-org-key"
    assert call["json"]["stream"] is True


@pytest.mark.asyncio
async def test_stream_gateway_error_becomes_inband_sse():
    client = FakeStreamClient(FakeStreamResponse(status_code=500))
    agen = await serve_federated_inference_stream(
        peer_node_id="peer-1", org_id="org_1", service_type="llm",
        payload={"model": "m", "messages": [], "stream": True},
        trust_enforcer=full_trust_enforcer(),
        key_provisioner=make_provisioner(),
        gateway_url="http://gw:4000",
        http_client=client,
    )
    out = b"".join([c async for c in agen])
    assert b"gateway returned 500" in out
    assert b"[DONE]" in out


# ---------------------------------------------------------------------------
# Consumer side
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_consumer_streams_with_stream_flag_and_signed_auth(monkeypatch):
    monkeypatch.setenv("FEDERATION_NODE_ID", "uc-unicorncommander")
    captured = {}

    class FakeRouter:
        def __init__(self, registry, **kw):
            pass

        async def proxy_to_node_stream(self, node_id, path, body, *, org_id=None, headers=None):
            captured.update({"node_id": node_id, "path": path, "body": body,
                             "org_id": org_id, "headers": headers})
            for c in [b"data: a\n\n", b"data: [DONE]\n\n"]:
                yield c

    async def _get():
        class R:  # minimal registry stand-in
            db_pool = None
        return R()
    monkeypatch.setattr(bridge, "_get_registry", _get)
    import federation.inference_router as ir_mod
    monkeypatch.setattr(ir_mod, "InferenceRouter", FakeRouter)
    monkeypatch.setattr(bridge, "InferenceRouter", FakeRouter, raising=False)

    chunks = []
    async for c in bridge.stream_llm_via_federation(
        model="qwen3.5-27b", node_id="uc-magicunicorn",
        payload={"model": "qwen3.5-27b", "messages": [{"role": "user", "content": "hi"}]},
        org_id="org_123",
    ):
        chunks.append(c)

    assert b"".join(chunks) == b"data: a\n\ndata: [DONE]\n\n"
    assert captured["path"] == "/api/v1/federation/inference"
    assert captured["org_id"] == "org_123"
    inner = captured["body"]["payload"]
    assert inner["stream"] is True
    assert inner["stream_options"] == {"include_usage": True}
    assert captured["headers"]["Authorization"].startswith("Bearer ")
