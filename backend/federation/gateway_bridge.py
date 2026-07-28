"""
Federation gateway bridge — carry the per-org gateway key across the hop.

The per-org LiteLLM virtual key (gateway_key_provisioning.py, user_id ==
org_id) is the proven inference-billing contract: the gateway runs with
LITELLM_SUCCESS_CALLBACK=lago and charge_by=user_id, so a call made with
that key fires exactly one Lago `ai_api_call` event (response_cost ×
markup) keyed to the org's subscription on UC-1 Hub.

Until now that contract broke at the federation boundary: the inference
router proxied to peers with the shared federation credential, so the
publisher's gateway had no org identity to meter under. This module is
the PUBLISHER side of the fix:

    consumer node                         publisher node (this code)
    -------------                         --------------------------
    proxy_to_node(..., org_id=X) ───────▶ POST /api/v1/federation/inference
      X-Federation-Org-Id: X                1. federation auth (peer JWT)
                                            2. trust gate: peer_may_call()
                                            3. provision_org_gateway_key(X)
                                               on the LOCAL gateway (reuse,
                                               never a second key system)
                                            4. forward payload to the local
                                               gateway with the org's key
                                            5. gateway fires the ONE Lago
                                               event keyed to org X

Because the publisher's own gateway meters the call, the response is
marked gateway_metered=True so FederationMeter never double-fires Lago
for it (see federation/metering.py).
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("federation.gateway_bridge")

# Same service-type → gateway path mapping the router uses for cloud routing.
GATEWAY_PATHS = {
    "llm": "/v1/chat/completions",
    "embeddings": "/v1/embeddings",
    "reranker": "/v1/rerank",
    "image_gen": "/v1/images/generations",
    "tts": "/v1/audio/speech",
    "stt": "/v1/audio/transcriptions",
}

ORG_HEADER = "X-Federation-Org-Id"

# The federation catalog advertises the RAW model names the GPU backend
# reports (e.g. "Qwen_Qwen3.5-27B-Q4_K_M") while the local gateway serves
# ALIASES (e.g. "qwen3.5-27b" → openai/Qwen_Qwen3.5-27B-Q4_K_M). Consumers
# route by catalog name, so the publisher translates raw→alias using the
# gateway's /model/info. Cached; fail-soft (unknown names pass through and
# the gateway's own 400 surfaces).
_ALIAS_CACHE_TTL = 300.0
_alias_cache: Dict[str, Any] = {"ts": 0.0, "aliases": set(), "raw_to_alias": {}}


async def _resolve_gateway_model(
    model: str, gateway_url: str, master_key: str, http_client: Any = None
) -> str:
    import time as _time
    now = _time.monotonic()
    if now - _alias_cache["ts"] > _ALIAS_CACHE_TTL:
        try:
            own = False
            if http_client is None:
                http_client = httpx.AsyncClient(timeout=10.0)
                own = True
            try:
                resp = await http_client.get(
                    f"{gateway_url}/model/info",
                    headers={"Authorization": f"Bearer {master_key}"},
                )
            finally:
                if own:
                    await http_client.aclose()
            if resp.status_code == 200:
                aliases, raw_map = set(), {}
                for entry in resp.json().get("data", []):
                    alias = entry.get("model_name")
                    upstream = (entry.get("litellm_params") or {}).get("model") or ""
                    if not alias:
                        continue
                    aliases.add(alias)
                    if "/" in upstream:
                        raw_map.setdefault(upstream.split("/", 1)[1], alias)
                _alias_cache.update(
                    {"aliases": aliases, "raw_to_alias": raw_map, "ts": now}
                )
        except Exception as exc:
            logger.debug("Gateway model-info refresh failed: %s", exc)
            _alias_cache["ts"] = now
    if model in _alias_cache["aliases"]:
        return model
    resolved = _alias_cache["raw_to_alias"].get(model)
    if resolved:
        logger.debug("Resolved catalog model %s -> gateway alias %s", model, resolved)
        return resolved
    return model


class FederatedInferenceError(Exception):
    """Base error; http_status tells the API layer what to return."""
    http_status = 500


class TrustDenied(FederatedInferenceError):
    http_status = 403


class BadFederatedRequest(FederatedInferenceError):
    http_status = 400


class GatewayKeyUnavailable(FederatedInferenceError):
    http_status = 503


class GatewayUpstreamError(FederatedInferenceError):
    http_status = 504


async def _prepare_gateway_forward(
    *,
    peer_node_id: str,
    org_id: Optional[str],
    service_type: str,
    payload: Dict[str, Any],
    db_pool=None,
    local_node_id: Optional[str] = None,
    trust_enforcer: Any = None,
    key_provisioner: Any = None,
    gateway_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Trust-gate, provision the org key, resolve the gateway URL + model alias.

    Shared by the buffered and streaming serve paths so both go through the
    SAME trust + per-org-key + metering contract. Raises the explicit
    FederatedInferenceError subclasses; on success returns the ready-to-send
    forward plan {url, headers, payload, key_info, service_type}.
    """
    if not org_id:
        raise BadFederatedRequest(
            f"Federated inference requires the consuming org identity "
            f"({ORG_HEADER} header or org_id field)"
        )
    path = GATEWAY_PATHS.get(service_type)
    if not path:
        raise BadFederatedRequest(
            f"Service type '{service_type}' is not gateway-servable "
            f"(supported: {sorted(GATEWAY_PATHS)})"
        )

    # 1. Trust gate — the peer must be allowed to CALL this service on us.
    if trust_enforcer is None:
        from federation.trust import get_trust_enforcer
        trust_enforcer = get_trust_enforcer(db_pool, local_node_id=local_node_id)
    allowed, reason = await trust_enforcer.peer_may_call(peer_node_id, service_type)
    if not allowed:
        raise TrustDenied(
            f"Trust mode denies peer '{peer_node_id}' calling "
            f"'{service_type}': {reason}"
        )

    # 2. Per-org key on OUR gateway (idempotent; the one key system).
    if key_provisioner is None:
        from gateway_key_provisioning import provision_org_gateway_key
        key_provisioner = provision_org_gateway_key
    key_info = await key_provisioner(org_id=org_id)
    if not key_info:
        raise GatewayKeyUnavailable(
            f"Gateway key provisioning unavailable for org {org_id} "
            f"(gateway unreachable or LITELLM_MASTER_KEY unset)"
        )
    org_key = key_info.get("key")
    if not org_key:
        # Key exists on the gateway but its secret isn't retrievable on this
        # node (created without ENCRYPTION_KEY at-rest storage). Without the
        # raw value we cannot attribute the call — fail explicitly rather
        # than fall back to an unmetered credential.
        raise GatewayKeyUnavailable(
            f"Org {org_id} has gateway key {key_info.get('key_id', '?')[:12]} "
            f"but its secret is not retrievable on this node; re-key or set "
            f"ENCRYPTION_KEY so the value persists"
        )

    # 3. Resolve the LOCAL gateway URL (DB-first, same as provisioning).
    master_key = ""
    if gateway_url is None:
        from gateway_key_provisioning import _resolve_gateway_creds
        gateway_url, master_key = await _resolve_gateway_creds()
    gateway_url = (gateway_url or "").rstrip("/")
    if not gateway_url:
        raise GatewayKeyUnavailable("No gateway URL configured on this node")

    # 3b. Translate catalog (raw backend) model names to gateway aliases.
    if master_key and payload.get("model"):
        try:
            payload = dict(payload)
            payload["model"] = await _resolve_gateway_model(
                payload["model"], gateway_url, master_key
            )
        except Exception as exc:
            logger.debug("Model alias resolution skipped: %s", exc)

    return {
        "url": f"{gateway_url}{path}",
        "headers": {
            "Authorization": f"Bearer {org_key}",
            "Content-Type": "application/json",
        },
        "payload": payload,
        "key_info": key_info,
        "service_type": service_type,
    }


async def serve_federated_inference(
    *,
    peer_node_id: str,
    org_id: Optional[str],
    service_type: str,
    payload: Dict[str, Any],
    db_pool=None,
    local_node_id: Optional[str] = None,
    trust_enforcer: Any = None,
    key_provisioner: Any = None,
    gateway_url: Optional[str] = None,
    http_client: Any = None,
) -> Dict[str, Any]:
    """Serve an inbound federated inference call under the org's gateway key
    (BUFFERED — one request/response). See serve_federated_inference_stream
    for the token-by-token SSE path.

    Returns:
        {data, status_code, org_id, key_id, gateway_metered: True}

    Raises:
        TrustDenied / BadFederatedRequest / GatewayKeyUnavailable.
    """
    plan = await _prepare_gateway_forward(
        peer_node_id=peer_node_id, org_id=org_id, service_type=service_type,
        payload=payload, db_pool=db_pool, local_node_id=local_node_id,
        trust_enforcer=trust_enforcer, key_provisioner=key_provisioner,
        gateway_url=gateway_url,
    )

    # Forward under the org's key — the gateway meters this call to Lago keyed
    # user_id == org_id with the configured markup. Exactly one billable event,
    # fired by the gateway, not by us.
    timeout = float(os.getenv("FEDERATION_PROXY_TIMEOUT", "120"))
    own_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=timeout)
        own_client = True
    try:
        response = await http_client.post(
            plan["url"], json=plan["payload"], headers=plan["headers"]
        )
    except httpx.TimeoutException as exc:
        raise GatewayUpstreamError(
            f"Gateway timed out serving {service_type} for org {org_id} "
            f"after {timeout:.0f}s (model may be cold-loading): {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        raise GatewayUpstreamError(
            f"Gateway unreachable serving {service_type} for org {org_id}: {exc}"
        ) from exc
    finally:
        if own_client:
            await http_client.aclose()

    logger.info(
        "Federated inference: peer=%s org=%s %s -> %s [%d]",
        peer_node_id, org_id, service_type, plan["url"], response.status_code,
    )
    return {
        "data": response.json(),
        "status_code": response.status_code,
        "org_id": org_id,
        "key_id": plan["key_info"].get("key_id"),
        "gateway_metered": response.status_code < 400,
    }


def _sse_error_chunk(message: str) -> bytes:
    """An in-band OpenAI-style SSE error event + terminator.

    Streaming responses have already committed a 200 status to the client by
    the time the gateway is reached, so a gateway-level failure is surfaced
    in-band (the standard streaming-proxy contract) rather than as an HTTP code.
    """
    import json as _json
    err = _json.dumps({"error": {"message": message, "type": "federation_error"}})
    return f"data: {err}\n\ndata: [DONE]\n\n".encode()


async def serve_federated_inference_stream(
    *,
    peer_node_id: str,
    org_id: Optional[str],
    service_type: str,
    payload: Dict[str, Any],
    db_pool=None,
    local_node_id: Optional[str] = None,
    trust_enforcer: Any = None,
    key_provisioner: Any = None,
    gateway_url: Optional[str] = None,
    http_client: Any = None,
):
    """Serve a STREAMING federated inference call under the org's gateway key.

    Two-phase so pre-stream failures map to a real HTTP status: this coroutine
    runs the trust/key/url prep eagerly (raising TrustDenied / BadFederatedRequest
    / GatewayKeyUnavailable BEFORE any bytes are committed), then returns an async
    byte iterator that opens a streaming POST to the local gateway and relays its
    SSE chunks verbatim. The gateway meters the call on stream completion exactly
    as for the buffered path (LITELLM_SUCCESS_CALLBACK=lago, charge_by=user_id) —
    still the single billable event, keyed to the org.

    Usage:
        agen = await serve_federated_inference_stream(...)   # may raise
        return StreamingResponse(agen, media_type="text/event-stream")
    """
    plan = await _prepare_gateway_forward(
        peer_node_id=peer_node_id, org_id=org_id, service_type=service_type,
        payload=payload, db_pool=db_pool, local_node_id=local_node_id,
        trust_enforcer=trust_enforcer, key_provisioner=key_provisioner,
        gateway_url=gateway_url,
    )

    async def _byte_stream():
        timeout = float(os.getenv("FEDERATION_PROXY_TIMEOUT", "120"))
        own_client = False
        client = http_client
        if client is None:
            client = httpx.AsyncClient(timeout=timeout)
            own_client = True
        try:
            async with client.stream(
                "POST", plan["url"], json=plan["payload"], headers=plan["headers"]
            ) as response:
                if response.status_code >= 400:
                    detail = (await response.aread()).decode(errors="replace")[:300]
                    logger.warning(
                        "Federated stream: gateway %d for org %s: %s",
                        response.status_code, org_id, detail,
                    )
                    yield _sse_error_chunk(
                        f"gateway returned {response.status_code}"
                    )
                    return
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
        except httpx.HTTPError as exc:
            logger.warning("Federated stream transport error for org %s: %s", org_id, exc)
            yield _sse_error_chunk(f"gateway unreachable: {exc}")
        finally:
            if own_client:
                await client.aclose()
        logger.info(
            "Federated stream done: peer=%s org=%s %s -> %s",
            peer_node_id, org_id, service_type, plan["url"],
        )

    return _byte_stream()
