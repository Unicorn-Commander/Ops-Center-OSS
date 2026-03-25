"""
Federation API router for Ops-Center.
"""


import os
import sys
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

from database.connection import get_db_pool
from federation.auth import verify_federation_request
from federation.hardware_detector import HardwareDetector
from federation.inference_router import InferenceRouter
from federation.metering_aggregator import MeteringAggregator
from federation.node_registry import NodeRegistry
from rate_limiter import rate_limit

router = APIRouter(
    prefix="/api/v1/federation",
    tags=["federation"],
)


class FederationServicePayload(BaseModel):
    service_type: Literal["llm", "tts", "stt", "embeddings", "image_gen", "music_gen", "reranker", "agents", "search", "extraction"]
    models: List[str] = Field(default_factory=list)
    endpoint_path: Optional[str] = None
    status: str = "running"
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    cold_start_seconds: Optional[int] = None
    avg_latency_ms: Optional[int] = None
    cost_usd: float = 0.0


class NodeRegistrationPayload(BaseModel):
    node_id: str
    display_name: str
    endpoint_url: str
    auth_method: Literal["jwt", "mtls", "api_key"] = "jwt"
    auth_credential: Optional[str] = None
    hardware_profile: Dict[str, Any] = Field(default_factory=dict)
    status: str = "online"
    roles: List[str] = Field(default_factory=lambda: ["inference"])
    region: Optional[str] = None
    is_self: bool = False
    services: List[FederationServicePayload] = Field(default_factory=list)


class HeartbeatPayload(BaseModel):
    node_id: str
    load: Dict[str, Any] = Field(default_factory=dict)
    hardware_profile: Dict[str, Any] = Field(default_factory=dict)
    services: List[FederationServicePayload] = Field(default_factory=list)


class RoutingConstraints(BaseModel):
    """Constraints that filter which nodes can handle a request."""
    locality: Optional[str] = None  # "local_only", "lan_only", "any"
    compliance: Optional[List[str]] = None  # ["hipaa", "gdpr", "sox"]
    data_region: Optional[str] = None  # "us", "eu", "asia"
    required_gpu: Optional[str] = None  # "ampere+", "turing+", "any"
    min_vram_gb: Optional[float] = None  # minimum GPU VRAM needed
    max_cost_usd: Optional[float] = None  # budget cap per request
    preferred_node: Optional[str] = None  # prefer specific node if available
    exclude_nodes: Optional[List[str]] = None  # never route to these nodes


class RouteRequest(BaseModel):
    service_type: Literal["llm", "tts", "stt", "embeddings", "image_gen", "music_gen", "reranker", "agents", "search", "extraction"]
    model: Optional[str] = None
    min_vram_mb: Optional[int] = None
    latency_sensitive: bool = True
    constraints: Optional[RoutingConstraints] = None
    user_tier: Optional[str] = None  # subscription tier: vip_founder, founder_friend, managed, trial, etc.
    user_id: Optional[str] = None  # for usage tracking


class UsagePayload(BaseModel):
    source_node_id: str
    target_node_id: str
    service_type: Literal["llm", "tts", "stt", "embeddings", "image_gen", "music_gen", "reranker", "agents", "search", "extraction"]
    model: Optional[str] = None
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: Optional[int] = None
    cost_usd: float = 0.0


async def get_current_user(request: Request):
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = RedisSessionManager(
        host=os.getenv("REDIS_HOST", "unicorn-redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session_data = sessions[session_token]
    user = session_data.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")
    return user


async def require_admin(request: Request):
    user = await get_current_user(request)
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _federation_secret_ok(request: Request) -> bool:
    """Verify federation request auth — JWT (preferred) or legacy shared key.

    Uses verify_federation_request() from federation.auth which supports:
    - Per-node signed JWTs (new, zero-trust)
    - Raw Bearer shared-key tokens (backward compatible)
    - X-Federation-Key / X-Federation-Secret headers (backward compatible)
    - Open mode when no key is configured (development)
    """
    is_valid, node_id, error = verify_federation_request(request)
    if is_valid:
        # Stash the authenticated node_id on the request state for downstream use
        request.state.federation_node_id = node_id
        return True
    return False


async def get_registry(request: Request) -> NodeRegistry:
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is None:
        redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://unicorn-redis:6379/0"), decode_responses=True)
        request.app.state.redis_client = redis_client
    db_pool = await get_db_pool()
    return NodeRegistry(redis_client=redis_client, db_pool=db_pool)


@router.post("/register")
@rate_limit("federation_register")
async def register_node(
    payload: NodeRegistrationPayload,
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    if not _federation_secret_ok(request):
        raise HTTPException(status_code=401, detail="Federation authentication failed")
    return await registry.register_node(payload.model_dump())


@router.post("/heartbeat")
@rate_limit("federation_heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    if not _federation_secret_ok(request):
        raise HTTPException(status_code=401, detail="Federation authentication failed")
    try:
        return await registry.heartbeat(payload.node_id, payload.model_dump(exclude={"node_id"}))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/nodes/{node_id}")
async def deregister_node(
    node_id: str,
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    await registry.deregister_node(node_id)
    return {"deleted": True, "node_id": node_id}


@router.get("/nodes")
async def list_nodes(
    include_offline: bool = Query(True),
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    return {"nodes": await registry.get_nodes(include_offline=include_offline)}


@router.get("/services")
async def list_services(
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    return {"services": await registry.get_service_catalog()}


@router.get("/services/{service_type}")
async def list_services_by_type(
    service_type: str,
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    return {"services": await registry.get_service_catalog(service_type=service_type)}


@router.get("/agents")
async def list_federation_agents(
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    """List all agents available across the federation.

    Returns agents from all online nodes that have Brigade running,
    including which node hosts each agent.
    """
    catalog = await registry.get_service_catalog()
    agents = []
    for service in catalog:
        if service.get("service_type") == "agents":
            node_id = service.get("node_id", "unknown")
            node_name = service.get("node_name", "unknown")
            for agent_id in service.get("models", []):
                agents.append({
                    "agent_id": agent_id,
                    "node_id": node_id,
                    "node_name": node_name,
                    "endpoint": service.get("endpoint_path", "/api/v1/a2a/agents/{id}/invoke"),
                    "status": service.get("status", "unknown"),
                })
    return {"agents": agents, "total": len(agents)}


@router.post("/route")
@rate_limit("federation_route")
async def route_inference(
    payload: RouteRequest,
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    from federation.credit_estimator import estimate_credits
    from federation.access_control import get_service_access_control

    # Check service ACL before routing
    acl = get_service_access_control()
    access = await acl.check_access(
        service_type=payload.service_type,
        user_tier=payload.user_tier,
        user_id=payload.user_id,
    )
    if not access["allowed"]:
        raise HTTPException(403, f"Access denied: {access['reason']}")

    local_node_id = request.headers.get("x-local-node-id") or os.getenv("FEDERATION_LOCAL_NODE_ID")
    router_service = InferenceRouter(registry, local_node_id=local_node_id)
    route = await router_service.route(payload.model_dump(), user_tier=payload.user_tier)

    # Attach credit estimation to the route response
    credit_info = estimate_credits(
        service_type=payload.service_type,
        route_target=route.get("route_type", "cloud"),
        cloud_cost_per_hour=route.get("cost_per_hour", 0.0),
        tier_markup_percentage=25.0,  # TODO: look up from DB based on user_tier
    )
    route["credits"] = credit_info

    # Attach access control info so callers know about credit requirements
    route["access"] = {
        "requires_credits": access["requires_credits"],
        "is_free": access["is_free"],
    }

    return route


@router.get("/topology")
async def topology(
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    return await registry.get_topology()


@router.post("/usage")
async def record_usage(
    payload: UsagePayload,
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    if not _federation_secret_ok(request):
        raise HTTPException(status_code=401, detail="Federation authentication failed")
    meter = MeteringAggregator(registry.db_pool)
    return await meter.record_usage(**payload.model_dump())


@router.get("/usage")
async def usage_summary(
    hours: int = Query(24, ge=1, le=24 * 30),
    _admin=Depends(require_admin),
    registry: NodeRegistry = Depends(get_registry),
):
    meter = MeteringAggregator(registry.db_pool)
    return await meter.summarize_usage(hours=hours)


@router.get("/health")
@rate_limit("federation_health")
async def federation_health(
    request: Request,
    registry: NodeRegistry = Depends(get_registry),
):
    nodes = await registry.get_nodes(include_offline=True)
    healthy = len([node for node in nodes if node["status"] == "online"])
    degraded = len([node for node in nodes if node["status"] == "degraded"])
    offline = len([node for node in nodes if node["status"] == "offline"])
    return {
        "status": "healthy" if offline == 0 else "degraded",
        "nodes_total": len(nodes),
        "nodes_online": healthy,
        "nodes_degraded": degraded,
        "nodes_offline": offline,
        "services_total": len(await registry.get_service_catalog(include_offline=True)),
    }


@router.get("/self/advertisement")
async def local_advertisement(_admin=Depends(require_admin)):
    detector = HardwareDetector()
    profile = detector.detect()
    return {
        "hardware_profile": profile,
        "services": detector.build_service_inventory(profile),
    }


# ---------------------------------------------------------------------------
# Cloud GPU Management
# ---------------------------------------------------------------------------

from federation.cloud_provisioner import get_cloud_provisioner


@router.get("/cloud/instances")
async def list_cloud_instances(
    request: Request,
    _admin=Depends(require_admin),
):
    """List active cloud GPU instances."""
    provisioner = get_cloud_provisioner()
    return {
        "instances": provisioner.get_active_instances(),
        "hourly_cost": provisioner.get_current_hourly_cost(),
        "max_instances": provisioner.max_instances,
        "budget_hourly": provisioner.budget_hourly,
        "enabled": provisioner.enabled,
    }


@router.post("/cloud/provision")
@rate_limit("federation_provision")
async def provision_cloud_instance(
    request: Request,
    body: dict,
    _admin=Depends(require_admin),
):
    """Manually provision a cloud GPU instance.

    Request body::

        {
            "service_profile": "music",
            "provider": "runpod",
            "gpu_type": "NVIDIA A10G"
        }
    """
    provisioner = get_cloud_provisioner()
    if not provisioner.enabled:
        raise HTTPException(
            status_code=400,
            detail="Cloud GPU provisioning is disabled. Set CLOUD_GPU_ENABLED=true.",
        )

    instance = await provisioner.provision_for_service(
        service_type=body.get("service_profile", "all"),
        provider=body.get("provider"),
        gpu_type=body.get("gpu_type"),
    )
    if instance:
        active = provisioner.get_active_instances()
        return {"instance": active[-1] if active else None}
    raise HTTPException(status_code=500, detail="Provisioning failed")


@router.post("/cloud/instances/{instance_id}/terminate")
async def terminate_cloud_instance(
    instance_id: str,
    request: Request,
    _admin=Depends(require_admin),
):
    """Manually terminate a cloud GPU instance."""
    provisioner = get_cloud_provisioner()
    instance = provisioner.instances.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    await provisioner._terminate_instance(instance)
    return {"status": "terminated", "total_cost": instance.total_cost}


@router.post("/cloud/cleanup")
async def cleanup_stale_instances(
    request: Request,
    _admin=Depends(require_admin),
):
    """Clean up stale cloud instances stuck in REQUESTING/BOOTING."""
    provisioner = get_cloud_provisioner()
    await provisioner.cleanup_stale()
    return {"status": "ok", "active_instances": len(provisioner.get_active_instances())}


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------

from federation.pipelines import (
    Pipeline,
    PipelineExecution,
    get_pipeline_registry,
)


@router.get("/pipelines")
async def list_pipelines(request: Request, _admin=Depends(require_admin)):
    """List available pipeline templates."""
    registry = get_pipeline_registry()
    return {"pipelines": registry.list_pipelines()}


@router.post("/pipelines/execute")
async def execute_pipeline(
    request: Request,
    body: dict,
    registry_dep: NodeRegistry = Depends(get_registry),
):
    """Execute a pipeline with given variables.

    Request body::

        {
            "pipeline": "music-production",
            "variables": {"topic": "love", "genre": "pop"}
        }

    If ``pipeline`` is a string it must match a registered template name.
    Alternatively pass a full pipeline definition dict under ``pipeline_def``.
    """
    pipeline_registry = get_pipeline_registry()

    # Resolve pipeline template ------------------------------------------------
    pipeline_name = body.get("pipeline")
    pipeline_def = body.get("pipeline_def")

    if pipeline_def:
        pipeline = Pipeline.from_dict(pipeline_def)
    elif pipeline_name:
        pipeline = pipeline_registry.get_pipeline(pipeline_name)
        if pipeline is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline '{pipeline_name}' not found",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide 'pipeline' (template name) or 'pipeline_def' (full definition)",
        )

    # Build router and execute -------------------------------------------------
    local_node_id = (
        request.headers.get("x-local-node-id")
        or os.getenv("FEDERATION_LOCAL_NODE_ID")
    )
    inference_router = InferenceRouter(registry_dep, local_node_id=local_node_id)

    variables = body.get("variables", {})
    execution = PipelineExecution(pipeline, inference_router, variables=variables)

    # Track the execution so its status can be queried later.
    pipeline_registry.track_execution(execution)

    # Run the pipeline (awaited — caller gets the full result).
    result = await execution.execute()
    return result


@router.get("/pipelines/executions")
async def list_pipeline_executions(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    _admin=Depends(require_admin),
):
    """List recent pipeline executions."""
    registry = get_pipeline_registry()
    return {"executions": registry.list_executions(limit=limit)}


@router.get("/pipelines/executions/{execution_id}")
async def get_pipeline_execution(
    execution_id: str,
    request: Request,
    _admin=Depends(require_admin),
):
    """Get status of a pipeline execution."""
    registry = get_pipeline_registry()
    execution = registry.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.get_status()


# ---------------------------------------------------------------------------
# Audit & Circuit Breakers
# ---------------------------------------------------------------------------

@router.get("/audit")
async def routing_audit(
    service_type: Optional[str] = None,
    outcome: Optional[str] = None,
    user_tier: Optional[str] = None,
    limit: int = 100,
    _admin=Depends(require_admin),
):
    """Query the routing decision audit log."""
    from federation.resilience import get_routing_audit_log
    audit = get_routing_audit_log()
    return await audit.query(service_type=service_type, outcome=outcome, user_tier=user_tier, limit=limit)


@router.get("/circuits")
async def circuit_status(_admin=Depends(require_admin)):
    """Get circuit breaker status for all peers."""
    from federation.resilience import get_circuit_breaker
    cb = get_circuit_breaker()
    return cb.get_status()
