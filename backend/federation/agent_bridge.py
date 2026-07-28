"""
Federation agent bridge — Layer 2: agent invocations as federation contracts.

The inference bridge (gateway_bridge.py) made the per-org gateway key the
billing contract for raw tokens. Agents are different: the unit of value is
the INVOCATION (the outcome), tokens are COGS. This module is the publisher
side of the agent contract:

    consumer node                          publisher node (this code)
    -------------                          --------------------------
    POST /federation/agents/{id}/invoke ─▶  1. federation auth (peer)
      X-Federation-Org-Id: X                2. trust gate: peer_may_call(
                                               "agents", resource=agent_id)
                                               — per-agent ACLs supported:
                                               consume ["agents/sql-analyst"]
                                            3. forward task to the LOCAL
                                               Brigade (A2A) under our own
                                               Brigade credential
                                            4. meter ONE Lago event
                                               code=agent_invocation keyed
                                               external_subscription_id=X
                                               (units = the agent's credit
                                               price; $0 until plans price
                                               the metric)

Pricing: outcome-based, per agent. The per-agent unit price comes from
platform_settings key FEDERATION_AGENT_PRICING (JSON: {"agent-id": units,
"default": units}); absent → default 1 unit per invocation. What a "unit"
bills is decided by the Lago plan charge on the agent_invocation metric —
same philosophy as ai_api_call (raw usage in the event, pricing at the plan).
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("federation.agent_bridge")

AGENT_EVENT_CODE = os.getenv("FEDERATION_AGENT_EVENT_CODE", "agent_invocation")
ORG_HEADER = "X-Federation-Org-Id"

# Reuse the inference bridge's error hierarchy so the API layer maps both.
from federation.gateway_bridge import (  # noqa: E402
    BadFederatedRequest,
    FederatedInferenceError,
    GatewayUpstreamError,
    TrustDenied,
)


class AgentBackendUnavailable(FederatedInferenceError):
    http_status = 503


async def _agent_unit_price(agent_id: str, db_pool) -> float:
    """Outcome price in metric units for one invocation of this agent."""
    pricing: Dict[str, Any] = {}
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                raw = await conn.fetchval(
                    "SELECT value FROM platform_settings "
                    "WHERE key = 'FEDERATION_AGENT_PRICING'"
                )
            if raw:
                pricing = json.loads(raw)
        except Exception as exc:
            logger.debug("Agent pricing lookup failed (using default): %s", exc)
    try:
        return float(pricing.get(agent_id, pricing.get("default", 1)))
    except (TypeError, ValueError):
        return 1.0


async def _resolve_lago_creds(db_pool) -> tuple:
    """Canonical Lago target for federation agent billing.

    platform_settings FEDERATION_LAGO_API_URL/KEY override the node env —
    a publisher whose own LAGO_* env points at a local Lago (e.g. bigboy)
    can aim federation billing at UC-1 Hub with a SQL UPDATE, no recreate.
    """
    url = (os.getenv("LAGO_API_URL") or os.getenv("LAGO_API_BASE") or "").rstrip("/")
    key = os.getenv("LAGO_API_KEY", "")
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                for setting, current in (("FEDERATION_LAGO_API_URL", "url"),
                                         ("FEDERATION_LAGO_API_KEY", "key")):
                    val = await conn.fetchval(
                        "SELECT value FROM platform_settings WHERE key = $1", setting
                    )
                    if val:
                        if current == "url":
                            url = val.rstrip("/")
                        else:
                            key = val
        except Exception as exc:
            logger.debug("Federation Lago override lookup failed: %s", exc)
    return url, key


async def _report_invocation_to_lago(
    *,
    org_id: str,
    agent_id: str,
    units: float,
    duration_s: float,
    status: str,
    peer_node_id: str,
    db_pool=None,
) -> None:
    """Fire the single billable agent event to the canonical Lago.

    Best-effort: metering failure must never fail the invocation that
    already ran.
    """
    lago_url, lago_key = await _resolve_lago_creds(db_pool)
    if not lago_url or not lago_key:
        logger.debug("Lago not configured on this node; agent event not reported")
        return
    event = {
        "event": {
            "transaction_id": str(uuid.uuid4()),
            "external_subscription_id": org_id,
            "code": AGENT_EVENT_CODE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "properties": {
                "agent_id": agent_id,
                "units": units,
                "duration_s": round(duration_s, 3),
                "status": status,
                "consumer_node": peer_node_id,
            },
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{lago_url}/api/v1/events",
                json=event,
                headers={"Authorization": f"Bearer {lago_key}"},
            )
        if resp.status_code >= 400:
            logger.warning(
                "Agent Lago event failed: HTTP %d %s",
                resp.status_code, resp.text[:200],
            )
    except Exception as exc:
        logger.warning("Agent Lago event failed: %s", exc)


async def serve_federated_agent_invoke(
    *,
    peer_node_id: str,
    org_id: Optional[str],
    agent_id: str,
    task: str,
    context: Optional[str] = None,
    db_pool=None,
    local_node_id: Optional[str] = None,
    trust_enforcer: Any = None,
    brigade_url: Optional[str] = None,
    brigade_key: Optional[str] = None,
    http_client: Any = None,
    lago_reporter: Any = None,
) -> Dict[str, Any]:
    """Serve an inbound federated agent invocation under the org's identity.

    Returns {result, status, agent_id, org_id, units, duration_s,
    agent_metered: True} — agent_metered means THIS layer fired the billable
    agent_invocation event (the outcome price; any LLM tokens the agent
    burned are publisher COGS, not separately billed to the consumer).
    """
    if not org_id:
        raise BadFederatedRequest(
            f"Federated agent invocation requires the consuming org identity "
            f"({ORG_HEADER} header or org_id field)"
        )
    if not task:
        raise BadFederatedRequest("Field 'task' is required")

    # 1. Trust gate — per-agent: scoped peers may carry "agents" (all) or
    #    "agents/<id>" grants in consume[].
    if trust_enforcer is None:
        from federation.trust import get_trust_enforcer
        trust_enforcer = get_trust_enforcer(db_pool, local_node_id=local_node_id)
    allowed, reason = await trust_enforcer.peer_may_call(
        peer_node_id, "agents", resource=agent_id
    )
    if not allowed:
        raise TrustDenied(
            f"Trust mode denies peer '{peer_node_id}' invoking agent "
            f"'{agent_id}': {reason}"
        )

    # 2. Forward to the local Brigade (A2A protocol).
    brigade_url = (
        brigade_url
        or os.getenv("BRIGADE_API_URL")
        or "http://unicorn-brigade:8100"
    ).rstrip("/")
    brigade_key = brigade_key or os.getenv("BRIGADE_API_KEY") or os.getenv("BRIGADE_ADMIN_KEY")
    if not brigade_key:
        raise AgentBackendUnavailable("No Brigade credential configured on this node")

    payload: Dict[str, Any] = {"task": task}
    if context:
        payload["context"] = context
    timeout = float(os.getenv("FEDERATION_AGENT_TIMEOUT", "300"))
    url = f"{brigade_url}/api/v1/a2a/agents/{agent_id}/invoke"

    start = time.monotonic()
    own_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=timeout)
        own_client = True
    try:
        response = await http_client.post(
            url, json=payload,
            headers={"X-API-Key": brigade_key, "Content-Type": "application/json"},
        )
    except httpx.TimeoutException as exc:
        raise GatewayUpstreamError(
            f"Brigade timed out invoking agent '{agent_id}' after {timeout:.0f}s"
        ) from exc
    except httpx.HTTPError as exc:
        raise AgentBackendUnavailable(f"Brigade unreachable: {exc}") from exc
    finally:
        if own_client:
            await http_client.aclose()
    duration_s = time.monotonic() - start

    if response.status_code == 404:
        raise BadFederatedRequest(f"Agent '{agent_id}' not found on this node")
    if response.status_code >= 400:
        raise AgentBackendUnavailable(
            f"Brigade returned HTTP {response.status_code} for agent '{agent_id}'"
        )
    data = response.json()
    invoke_status = data.get("status", "unknown")

    # 3. Meter the OUTCOME — exactly one billable event, only for completed
    #    invocations (failed runs are not billed).
    units = 0.0
    if invoke_status == "completed":
        units = await _agent_unit_price(agent_id, db_pool)
        try:
            if lago_reporter is not None:
                await lago_reporter(
                    org_id=org_id, agent_id=agent_id, units=units,
                    duration_s=duration_s, status=invoke_status,
                    peer_node_id=peer_node_id,
                )
            else:
                await _report_invocation_to_lago(
                    org_id=org_id, agent_id=agent_id, units=units,
                    duration_s=duration_s, status=invoke_status,
                    peer_node_id=peer_node_id, db_pool=db_pool,
                )
        except Exception as exc:  # metering must never fail a served result
            logger.warning("Agent invocation metering failed: %s", exc)

    logger.info(
        "Federated agent invoke: peer=%s org=%s agent=%s status=%s units=%s %.1fs",
        peer_node_id, org_id, agent_id, invoke_status, units, duration_s,
    )
    return {
        "result": data.get("result"),
        "status": invoke_status,
        "error": data.get("error"),
        "agent_id": agent_id,
        "org_id": org_id,
        "model_used": data.get("model_used"),
        "units": units,
        "duration_s": round(duration_s, 3),
        "agent_metered": invoke_status == "completed",
    }
