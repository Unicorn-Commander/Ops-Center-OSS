"""
Consumer-side federated LLM serving — local models over the federation.

This node (e.g. commander, no GPUs) serves customer requests for models that
a trusted federation peer (e.g. bigboy) publishes, by forwarding through the
federation runtime:

    customer → /api/v1/llm/chat/completions
             → (model is in a peer's published llm catalog?)
             → InferenceRouter.proxy_to_node(peer, "/api/v1/federation/inference",
                                             org_id=<caller's org>)
             → publisher trust-gates, serves via ITS gateway under the org's
               per-org key, fires the single Lago ai_api_call event

Because the publisher meters the call (gateway_metered), the consumer must
NOT charge local credits for it — litellm_api's federated branch reports
cost 0 and stamps _metadata.gateway_metered for the credit middleware.

Catalog matching is fail-soft and cached (60s): registry errors keep the
stale cache; an empty cache simply means no federated branch is taken.
"""

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_CACHE_TTL = 60.0
_catalog: Dict[str, Any] = {"ts": 0.0, "models": {}}

_redis_client = None


def _local_node_id() -> Optional[str]:
    return os.getenv("FEDERATION_LOCAL_NODE_ID") or os.getenv("FEDERATION_NODE_ID")


async def _get_registry():
    """Build a NodeRegistry like routers/federation.get_registry does."""
    global _redis_client
    import redis.asyncio as aioredis
    from database.connection import get_db_pool
    from federation.node_registry import NodeRegistry

    if _redis_client is None:
        _redis_client = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://unicorn-redis:6379/0"),
            decode_responses=True,
        )
    return NodeRegistry(redis_client=_redis_client, db_pool=await get_db_pool())


async def _refresh_catalog() -> None:
    registry = await _get_registry()
    services = await registry.get_service_catalog(service_type="llm")
    self_id = _local_node_id()
    models: Dict[str, str] = {}
    for svc in services:
        node_id = svc.get("node_id")
        if not node_id or node_id == self_id:
            continue
        if svc.get("node_status") not in {None, "online", "degraded"}:
            continue
        if svc.get("status") not in {"running", "healthy", "loaded", "idle"}:
            continue
        for model in svc.get("models") or []:
            models.setdefault(model, node_id)
    _catalog["models"] = models
    _catalog["ts"] = time.monotonic()


async def _catalog_models() -> Dict[str, str]:
    """Current {model -> publishing node_id} map, refreshing if stale.

    Fail-soft: registry errors keep the stale cache; an empty map simply
    means no peer publishes a model right now.
    """
    now = time.monotonic()
    if now - _catalog["ts"] > _CACHE_TTL:
        try:
            await _refresh_catalog()
        except Exception as exc:
            # Keep serving the stale cache; never break the LLM path.
            logger.debug("Federated catalog refresh failed: %s", exc)
            _catalog["ts"] = now
    return _catalog["models"]


async def federated_node_for_model(model: Optional[str]) -> Optional[str]:
    """Which peer publishes this model? None if nobody does (or on error)."""
    if not model:
        return None
    return (await _catalog_models()).get(model)


async def federated_models() -> Dict[str, str]:
    """All peer-published models available over federation: {model -> node_id}.

    For listing endpoints (/models, /models/categorized) so customers can
    browse the local models a trusted peer publishes. Never raises — returns
    {} on any error.
    """
    try:
        return dict(await _catalog_models())
    except Exception as exc:
        logger.debug("federated_models() unavailable: %s", exc)
        return {}


async def serve_llm_via_federation(
    *,
    model: str,
    node_id: str,
    payload: Dict[str, Any],
    org_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Forward an OpenAI-style chat payload to the publishing peer.

    Returns (gateway_response_json, meta) where meta carries node/latency/
    gateway_metered. Raises on transport errors — the caller maps them.
    """
    from federation.auth import get_federation_auth
    from federation.inference_router import InferenceRouter

    registry = await _get_registry()
    router = InferenceRouter(registry, local_node_id=_local_node_id())

    body = dict(payload)
    # Streaming cannot transit the JSON envelope; the caller synthesizes
    # SSE for streaming clients from the buffered response.
    body.pop("stream", None)

    result = await router.proxy_to_node(
        node_id,
        "/api/v1/federation/inference",
        {"service_type": "llm", "model": model, "org_id": org_id, "payload": body},
        org_id=org_id,
        # Signed federation JWT — peers' stored auth_credential rows are not
        # uniformly populated, so always send our own credential.
        headers=get_federation_auth().get_auth_headers(node_id),
    )
    envelope = result.get("data") or {}
    response_json = envelope.get("data") or {}
    meta = {
        "federated_node": node_id,
        "gateway_metered": bool(envelope.get("gateway_metered")),
        "publisher_status": envelope.get("status_code"),
        "latency_ms": result.get("latency_ms"),
    }
    return response_json, meta


async def stream_llm_via_federation(
    *,
    model: str,
    node_id: str,
    payload: Dict[str, Any],
    org_id: str,
):
    """Stream an OpenAI-style chat completion from the publishing peer.

    Yields the publisher's SSE bytes verbatim (which are the gateway's SSE
    chunks) so the customer gets true token-by-token streaming. The publisher
    forwards stream=true to ITS gateway under the org's per-org key, and the
    gateway fires the single Lago ai_api_call event on stream completion — so,
    as with the buffered path, no local credit is charged (the consumer returns
    a text/event-stream response, which the credit middleware skips).
    """
    from federation.auth import get_federation_auth
    from federation.inference_router import InferenceRouter

    registry = await _get_registry()
    router = InferenceRouter(registry, local_node_id=_local_node_id())

    body = dict(payload)
    body["stream"] = True
    # Ask the gateway to emit a final usage chunk so cost is captured for
    # metering and the client sees token counts.
    body.setdefault("stream_options", {"include_usage": True})

    async for chunk in router.proxy_to_node_stream(
        node_id,
        "/api/v1/federation/inference",
        {"service_type": "llm", "model": model, "org_id": org_id, "payload": body},
        org_id=org_id,
        # Signed federation JWT — peers' stored auth_credential rows are not
        # uniformly populated, so always send our own credential.
        headers=get_federation_auth().get_auth_headers(node_id),
    ):
        yield chunk
