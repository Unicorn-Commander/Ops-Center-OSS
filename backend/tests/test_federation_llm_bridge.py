"""
Unit tests for consumer-side federated LLM serving (federation_llm_bridge)
and the publisher-side catalog-name → gateway-alias resolution.
"""

import pytest

import federation_llm_bridge as bridge
import federation.gateway_bridge as gw


# ---------------------------------------------------------------------------
# Catalog matching (consumer side)
# ---------------------------------------------------------------------------

class FakeRegistry:
    def __init__(self, services):
        self.services = services
        self.db_pool = None

    async def get_service_catalog(self, service_type=None, **kw):
        return self.services


def use_registry(monkeypatch, services):
    async def _get():
        return FakeRegistry(services)
    monkeypatch.setattr(bridge, "_get_registry", _get)
    bridge._catalog["ts"] = 0.0  # force refresh
    bridge._catalog["models"] = {}


@pytest.mark.asyncio
async def test_catalog_maps_models_to_publishing_nodes(monkeypatch):
    monkeypatch.setenv("FEDERATION_NODE_ID", "uc-unicorncommander")
    use_registry(monkeypatch, [
        {"node_id": "uc-magicunicorn", "node_status": "online", "status": "running",
         "models": ["qwen3.5-27b", "Qwen3-30B-Q4_K_M"]},
        # self node must be excluded
        {"node_id": "uc-unicorncommander", "node_status": "online", "status": "running",
         "models": ["cloud-proxy-model"]},
        # offline peers must be excluded
        {"node_id": "uc-centerdeep", "node_status": "offline", "status": "running",
         "models": ["dead-model"]},
    ])
    assert await bridge.federated_node_for_model("qwen3.5-27b") == "uc-magicunicorn"
    assert await bridge.federated_node_for_model("cloud-proxy-model") is None
    assert await bridge.federated_node_for_model("dead-model") is None
    assert await bridge.federated_node_for_model("gpt-4o") is None
    assert await bridge.federated_node_for_model(None) is None


@pytest.mark.asyncio
async def test_federated_models_lists_all_peer_models(monkeypatch):
    """federated_models() returns the full {model -> node} map for listings."""
    monkeypatch.setenv("FEDERATION_NODE_ID", "uc-unicorncommander")
    use_registry(monkeypatch, [
        {"node_id": "uc-magicunicorn", "node_status": "online", "status": "running",
         "models": ["qwen3.5-27b", "Qwen3-30B-Q4_K_M"]},
        {"node_id": "uc-unicorncommander", "node_status": "online", "status": "running",
         "models": ["cloud-proxy-model"]},  # self excluded
    ])
    catalog = await bridge.federated_models()
    assert catalog == {"qwen3.5-27b": "uc-magicunicorn",
                       "Qwen3-30B-Q4_K_M": "uc-magicunicorn"}


@pytest.mark.asyncio
async def test_federated_models_never_raises(monkeypatch):
    """Listing helper must be fail-soft — returns {} on registry failure."""
    async def boom():
        raise RuntimeError("registry down")
    monkeypatch.setattr(bridge, "_get_registry", boom)
    bridge._catalog["ts"] = 0.0
    bridge._catalog["models"] = {}
    assert await bridge.federated_models() == {}


@pytest.mark.asyncio
async def test_catalog_refresh_failure_keeps_stale_cache(monkeypatch):
    monkeypatch.setenv("FEDERATION_NODE_ID", "uc-unicorncommander")
    use_registry(monkeypatch, [
        {"node_id": "peer", "node_status": "online", "status": "running",
         "models": ["m1"]},
    ])
    assert await bridge.federated_node_for_model("m1") == "peer"

    async def boom():
        raise RuntimeError("registry down")
    monkeypatch.setattr(bridge, "_get_registry", boom)
    bridge._catalog["ts"] = 0.0  # force a (failing) refresh attempt
    # Stale cache still answers — never breaks the LLM path
    assert await bridge.federated_node_for_model("m1") == "peer"


# ---------------------------------------------------------------------------
# Forwarding (consumer side)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_serve_unwraps_envelope_and_sends_signed_auth(monkeypatch):
    monkeypatch.setenv("FEDERATION_NODE_ID", "uc-unicorncommander")
    captured = {}

    class FakeRouter:
        def __init__(self, registry, **kw):
            pass

        async def proxy_to_node(self, node_id, path, body, *, org_id=None, headers=None):
            captured.update({"node_id": node_id, "path": path, "body": body,
                             "org_id": org_id, "headers": headers})
            return {
                "data": {"data": {"choices": [{"message": {"content": "hi"}}]},
                         "status_code": 200, "gateway_metered": True},
                "latency_ms": 42.0,
            }

    async def _get():
        return FakeRegistry([])
    monkeypatch.setattr(bridge, "_get_registry", _get)
    import federation.inference_router as ir_mod
    monkeypatch.setattr(ir_mod, "InferenceRouter", FakeRouter)
    monkeypatch.setattr(bridge, "InferenceRouter", FakeRouter, raising=False)

    response, meta = await bridge.serve_llm_via_federation(
        model="qwen3.5-27b", node_id="uc-magicunicorn",
        payload={"model": "qwen3.5-27b", "stream": True,
                 "messages": [{"role": "user", "content": "hi"}]},
        org_id="org_123",
    )
    assert captured["node_id"] == "uc-magicunicorn"
    assert captured["path"] == "/api/v1/federation/inference"
    assert captured["org_id"] == "org_123"
    # stream flag must not transit (JSON envelope only)
    assert "stream" not in captured["body"]["payload"]
    # signed federation JWT present
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert response["choices"][0]["message"]["content"] == "hi"
    assert meta["gateway_metered"] is True
    assert meta["federated_node"] == "uc-magicunicorn"


# ---------------------------------------------------------------------------
# Publisher-side alias resolution
# ---------------------------------------------------------------------------

class FakeInfoClient:
    def __init__(self, entries):
        self.entries = entries

    async def get(self, url, headers=None):
        class _R:
            status_code = 200
            def __init__(self, entries):
                self._entries = entries
            def json(self):
                return {"data": self._entries}
        return _R(self.entries)


@pytest.mark.asyncio
async def test_raw_catalog_names_resolve_to_gateway_aliases():
    gw._alias_cache.update({"ts": 0.0, "aliases": set(), "raw_to_alias": {}})
    client = FakeInfoClient([
        {"model_name": "qwen3.5-27b",
         "litellm_params": {"model": "openai/Qwen_Qwen3.5-27B-Q4_K_M"}},
        {"model_name": "gpt-4o", "litellm_params": {"model": "openai/gpt-4o"}},
    ])
    # Raw backend name → alias
    assert await gw._resolve_gateway_model(
        "Qwen_Qwen3.5-27B-Q4_K_M", "http://gw:4000", "mk", http_client=client
    ) == "qwen3.5-27b"
    # Alias passes through
    assert await gw._resolve_gateway_model(
        "qwen3.5-27b", "http://gw:4000", "mk", http_client=client
    ) == "qwen3.5-27b"
    # Unknown passes through (gateway surfaces its own 400)
    assert await gw._resolve_gateway_model(
        "no-such-model", "http://gw:4000", "mk", http_client=client
    ) == "no-such-model"
