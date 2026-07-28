"""
Unit tests for the metering-sink reconciliation (federation/metering.py).

Invariant under test: EXACTLY ONE billable Lago event per federated call.

- gateway-metered events (served under a per-org gateway key — the
  publisher's gateway already fired Lago) must NOT fire Lago again.
- org-attributed events that were NOT gateway-metered fire the canonical
  `ai_api_call` metric keyed external_subscription_id == org_id with
  response_cost = cost × 1.32 — the same contract as the gateway.
- events with no org identity keep the legacy `federation_<service>`
  node-visibility code (not the billable metric).
"""

import pytest

import federation.metering as metering_mod
from federation.metering import FederationMeter


class _FakeLagoResponse:
    status_code = 200
    text = "ok"


class FakeLagoClient:
    """Captures Lago POSTs made by FederationMeter._report_to_lago."""

    posts = []  # class-level so the test can read after the meter's client closes

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        FakeLagoClient.posts.append({"url": url, "json": json, "headers": headers})
        return _FakeLagoResponse()


@pytest.fixture(autouse=True)
def lago_capture(monkeypatch):
    FakeLagoClient.posts = []
    monkeypatch.setattr(metering_mod.httpx, "AsyncClient", FakeLagoClient)
    yield FakeLagoClient.posts


def make_meter():
    return FederationMeter(
        db_pool=None, lago_url="http://lago:3000", lago_api_key="lago-key"
    )


@pytest.mark.asyncio
async def test_gateway_metered_event_never_fires_lago(lago_capture):
    """The publisher's gateway already billed this call — zero Lago posts."""
    meter = make_meter()
    result = await meter.record_usage({
        "source_node_id": "uc-commander",
        "target_node_id": "uc-magicunicorn",
        "service_type": "llm",
        "model": "qwen3.5-27b",
        "org_id": "org_123",
        "gateway_metered": True,
        "cost_usd": 0.01,
    })
    assert result["status"] == "recorded"
    assert lago_capture == []  # exactly one billable event: the gateway's


@pytest.mark.asyncio
async def test_org_event_fires_canonical_metric(lago_capture):
    """Non-gateway org-attributed usage fires ai_api_call keyed to the org
    with RAW response_cost — the gateway's exact contract (verified live:
    the ×1.32 markup is applied at the Lago plan level, not in the event)."""
    meter = make_meter()
    await meter.record_usage({
        "source_node_id": "uc-commander",
        "target_node_id": "uc-magicunicorn",
        "service_type": "llm",
        "model": "qwen3.5-27b",
        "org_id": "org_123",
        "cost_usd": 0.10,
    })
    assert len(lago_capture) == 1  # exactly one
    ev = lago_capture[0]["json"]["event"]
    assert ev["code"] == "ai_api_call"
    assert ev["external_subscription_id"] == "org_123"  # org, NOT node slug
    assert ev["properties"]["response_cost"] == pytest.approx(0.10)  # raw
    assert ev["properties"]["via"] == "federation_meter"


@pytest.mark.asyncio
async def test_node_event_keeps_legacy_visibility_code(lago_capture):
    """No org identity → legacy federation_<service> keyed by node slug.
    This is settlement visibility, not the billable ai_api_call metric."""
    meter = make_meter()
    await meter.record_usage({
        "source_node_id": "uc-commander",
        "target_node_id": "uc-magicunicorn",
        "service_type": "llm",
        "cost_usd": 0.05,
    })
    assert len(lago_capture) == 1
    ev = lago_capture[0]["json"]["event"]
    assert ev["code"] == "federation_llm"
    assert ev["external_subscription_id"] == "uc-commander"


@pytest.mark.asyncio
async def test_markup_and_code_are_configurable(monkeypatch, lago_capture):
    monkeypatch.setenv("FEDERATION_LAGO_MARKUP", "2.0")
    monkeypatch.setenv("FEDERATION_LAGO_EVENT_CODE", "custom_call")
    meter = make_meter()
    await meter.record_usage({
        "source_node_id": "n1", "target_node_id": "n2",
        "service_type": "llm", "org_id": "org_9", "cost_usd": 0.5,
    })
    ev = lago_capture[0]["json"]["event"]
    assert ev["code"] == "custom_call"
    assert ev["properties"]["response_cost"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_proxy_with_org_marks_gateway_metered(monkeypatch, lago_capture):
    """End-to-end consumer side: proxy_to_node(org_id=...) → the meter
    records the hop as gateway_metered → no Lago fire from the consumer."""
    from federation.inference_router import InferenceRouter
    from federation.node_registry import NodeRegistry
    from tests.test_federation import FakeRedis
    import federation.inference_router as ir_mod

    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)
    await registry.register_node({
        "node_id": "publisher-node", "display_name": "Pub",
        "endpoint_url": "https://pub.example.com", "services": [],
    })

    calls = []

    class _Resp:
        status_code = 200
        text = "ok"
        def json(self):
            return {"ok": True}
        def raise_for_status(self):
            return None

    # Shared httpx module: this one patched client sees both the proxy POST
    # and any Lago POST the meter would make.
    class _Client:
        def __init__(self, *a, **kw):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def post(self, url, json=None, headers=None):
            calls.append({"url": url, "json": json})
            return _Resp()

    monkeypatch.setattr(ir_mod.httpx, "AsyncClient", _Client)

    meter = make_meter()
    router = InferenceRouter(registry, local_node_id="consumer-node", meter=meter)
    await router.proxy_to_node(
        "publisher-node", "/api/v1/federation/inference",
        {"service_type": "llm", "model": "qwen3.5-27b"}, org_id="org_123",
    )
    # The proxy call itself went out...
    assert any("/api/v1/federation/inference" in c["url"] for c in calls)
    # ...but the consumer fired ZERO Lago events — the publisher's gateway
    # owns the one billable event.
    assert [c for c in calls if "/api/v1/events" in c["url"]] == []


@pytest.mark.asyncio
async def test_proxy_without_org_still_fires_legacy_visibility(monkeypatch, lago_capture):
    from federation.inference_router import InferenceRouter
    from federation.node_registry import NodeRegistry
    from tests.test_federation import FakeRedis
    import federation.inference_router as ir_mod

    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)
    await registry.register_node({
        "node_id": "publisher-node", "display_name": "Pub",
        "endpoint_url": "https://pub.example.com", "services": [],
    })

    calls = []

    class _Resp:
        status_code = 200
        text = "ok"
        def json(self):
            return {"ok": True}
        def raise_for_status(self):
            return None

    # federation.inference_router and federation.metering share the same
    # httpx module object, so one patched client sees BOTH the proxy POST
    # and the meter's Lago POST.
    class _Client:
        def __init__(self, *a, **kw):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def post(self, url, json=None, headers=None):
            calls.append({"url": url, "json": json})
            return _Resp()

    monkeypatch.setattr(ir_mod.httpx, "AsyncClient", _Client)

    meter = make_meter()
    router = InferenceRouter(registry, local_node_id="consumer-node", meter=meter)
    await router.proxy_to_node(
        "publisher-node", "/v1/chat/completions", {"service_type": "llm"},
    )
    lago_posts = [c for c in calls if "/api/v1/events" in c["url"]]
    assert len(lago_posts) == 1
    assert lago_posts[0]["json"]["event"]["code"] == "federation_llm"
