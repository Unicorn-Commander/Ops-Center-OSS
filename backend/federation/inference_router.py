"""
Inference routing engine for local, federated, and cloud execution.

Routes inference requests to the best available backend using a priority-based
scoring system that considers cost, latency, and quality. Supports local services,
peer federation nodes, and cloud API fallback via LiteLLM.
"""


import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from federation.node_registry import NodeRegistry
from federation.resilience import get_circuit_breaker, get_routing_audit_log

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency — resolved at first use.
_cloud_provisioner_factory = None


def _get_cloud_provisioner():
    """Lazy accessor for the cloud provisioner singleton."""
    global _cloud_provisioner_factory
    if _cloud_provisioner_factory is None:
        try:
            from federation.cloud_provisioner import get_cloud_provisioner
            _cloud_provisioner_factory = get_cloud_provisioner
        except ImportError:
            return None
    return _cloud_provisioner_factory()

# Default scoring weights by priority mode
SCORING_WEIGHTS = {
    "cost": {"cost": 0.6, "latency": 0.2, "quality": 0.2},
    "latency": {"cost": 0.1, "latency": 0.7, "quality": 0.2},
    "quality": {"cost": 0.1, "latency": 0.2, "quality": 0.7},
    "balanced": {"cost": 0.34, "latency": 0.33, "quality": 0.33},
}

# Latency history for peer nodes (node_id -> list of recent latency samples in ms)
_latency_history: Dict[str, List[float]] = {}
MAX_LATENCY_SAMPLES = 50


class InferenceRouter:
    """Routes inference requests to the optimal backend.

    Priority order:
      1. Local services (free, lowest latency)
      2. Peer federation nodes (sorted by latency, load, capability)
      3. Cloud APIs via LiteLLM (paid)
    """

    def __init__(
        self,
        registry: NodeRegistry,
        *,
        local_node_id: Optional[str] = None,
        litellm_url: Optional[str] = None,
        meter: Any = None,
    ):
        self.registry = registry
        self.local_node_id = local_node_id
        self.litellm_url = litellm_url or os.getenv(
            "LITELLM_PROXY_URL", "http://unicorn-litellm:4000"
        )
        self.meter = meter
        self._http_timeout = float(os.getenv("FEDERATION_PROXY_TIMEOUT", "120"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # Tiers that get free routing to self-hosted infrastructure
    FREE_TIERS = {"vip_founder", "founder_friend", "admin", "internal"}

    async def route(self, request: Dict[str, Any], *, user_tier: Optional[str] = None) -> Dict[str, Any]:
        """Route an inference request to the best available target.

        Args:
            request: Dict with keys:
                - service_type (str): e.g. "llm", "tts", "stt", "embeddings"
                - model (str, optional): specific model identifier
                - priority (str, optional): "cost" | "latency" | "quality" | "balanced"
                - min_vram_mb (float, optional): minimum VRAM requirement
            user_tier: Optional subscription tier for tier-aware routing.
                If provided, free tiers route to local/peer first while
                paying tiers route to cloud GPU for guaranteed capacity.

        Returns:
            Dict with routing decision including endpoint_url, estimated cost/latency.
        """
        service_type = request["service_type"]
        model = request.get("model")
        priority = request.get("priority", "balanced")
        require_model = bool(model)
        request_id = str(uuid.uuid4())
        circuit_breaker = get_circuit_breaker()
        audit_log = get_routing_audit_log()

        logger.debug(
            "Routing request: service_type=%s model=%s priority=%s user_tier=%s",
            service_type,
            model,
            priority,
            user_tier,
        )

        constraints = request.get("constraints")

        # 1. Gather all candidates from local, peer, and cloud sources
        candidates: List[Dict[str, Any]] = []

        local = await self._find_local_service(service_type, model)
        if local:
            local["_target"] = "self"
            candidates.append(local)

        peers = await self._find_peer_services(service_type, model)
        for peer in peers:
            peer["_target"] = "peer"
            candidates.append(peer)

        cloud = await self._find_cloud_service(service_type, model)
        if cloud:
            cloud["_target"] = "cloud"
            candidates.append(cloud)

        total_candidates = len(candidates)

        # 2. Apply constraint filtering
        if constraints:
            candidates = self._apply_constraints(candidates, constraints)

        candidates_after_constraints = len(candidates)

        # 3. Determine search order based on user tier
        if user_tier and user_tier in self.FREE_TIERS:
            # Free tiers: route to self-hosted first (free), then peers, then cloud as last resort
            search_order = ["local", "peer", "cloud"]
        elif user_tier:
            # Paying users: route to cloud GPU for guaranteed capacity
            # But still allow local/peer if user explicitly chooses via constraints
            if constraints and constraints.get("preferred_node"):
                search_order = ["local", "peer", "cloud"]
            else:
                search_order = ["cloud_gpu", "cloud", "local", "peer"]
        else:
            # No tier specified: preserve original behavior (local → peer → cloud)
            search_order = ["local", "peer", "cloud"]

        # 4. Route using tier-aware search order
        for target in search_order:
            if target == "local":
                local_candidates = [c for c in candidates if c.get("_target") == "self"]
                if local_candidates:
                    result = self._build_result("local", local_candidates[0], request)
                    result["request_id"] = request_id
                    logger.info(
                        "Routed %s to local service (model=%s, tier=%s)", service_type, model, user_tier
                    )
                    await audit_log.log_decision(
                        request_id=request_id, service_type=service_type, model=model,
                        user_id=request.get("user_id"), user_tier=user_tier,
                        candidates_found=total_candidates,
                        candidates_after_constraints=candidates_after_constraints,
                        constraints_applied=constraints,
                        selected_target="local", selected_node_id=self.local_node_id,
                        selected_reason="Local service available", outcome="routed",
                    )
                    return result
            elif target == "peer":
                peer_candidates = [c for c in candidates if c.get("_target") == "peer"]
                # Filter out peers with open circuits
                peer_candidates = [
                    c for c in peer_candidates
                    if circuit_breaker.can_request(c.get("node_id", ""))
                ]
                if peer_candidates:
                    scored = self._rank_candidates(peer_candidates, request, priority)
                    if scored:
                        best = scored[0][1]
                        result = self._build_result("federated", best, request)
                        result["request_id"] = request_id
                        logger.info(
                            "Routed %s to peer node %s (model=%s, score=%.1f, tier=%s)",
                            service_type,
                            best.get("node_id"),
                            model,
                            scored[0][0],
                            user_tier,
                        )
                        await audit_log.log_decision(
                            request_id=request_id, service_type=service_type, model=model,
                            user_id=request.get("user_id"), user_tier=user_tier,
                            candidates_found=total_candidates,
                            candidates_after_constraints=candidates_after_constraints,
                            constraints_applied=constraints,
                            selected_target="peer", selected_node_id=best.get("node_id"),
                            selected_reason=f"Best peer (score={scored[0][0]:.1f})",
                            routing_score=scored[0][0], outcome="routed",
                        )
                        return result
            elif target == "cloud_gpu":
                # Auto-provision a cloud GPU instance via RunPod/Lambda
                provisioner = _get_cloud_provisioner()
                if provisioner and provisioner.enabled:
                    # Check for an already-running instance that serves this service
                    existing = provisioner.find_ready_instance(service_type)
                    if existing and existing.federation_node_id:
                        provisioner.record_request(existing.id)
                        result = self._build_cloud_gpu_result(existing, request)
                        result["request_id"] = request_id
                        logger.info(
                            "Routed %s to existing cloud GPU %s (node=%s, tier=%s)",
                            service_type,
                            existing.gpu_type,
                            existing.federation_node_id,
                            user_tier,
                        )
                        await audit_log.log_decision(
                            request_id=request_id, service_type=service_type, model=model,
                            user_id=request.get("user_id"), user_tier=user_tier,
                            candidates_found=total_candidates,
                            candidates_after_constraints=candidates_after_constraints,
                            constraints_applied=constraints,
                            selected_target="cloud_gpu",
                            selected_node_id=existing.federation_node_id,
                            selected_reason=f"Existing cloud GPU ({existing.gpu_type})",
                            outcome="routed",
                        )
                        return result

                    # No existing instance — provision a new one
                    logger.info(
                        "No local/peer capacity for %s, provisioning cloud GPU (tier=%s)",
                        service_type,
                        user_tier,
                    )
                    instance = await provisioner.provision_for_service(
                        service_type, model, user_tier=user_tier
                    )
                    if instance and instance.federation_node_id:
                        provisioner.record_request(instance.id)
                        result = self._build_cloud_gpu_result(instance, request)
                        result["request_id"] = request_id
                        logger.info(
                            "Routed %s to new cloud GPU %s (node=%s, tier=%s)",
                            service_type,
                            instance.gpu_type,
                            instance.federation_node_id,
                            user_tier,
                        )
                        await audit_log.log_decision(
                            request_id=request_id, service_type=service_type, model=model,
                            user_id=request.get("user_id"), user_tier=user_tier,
                            candidates_found=total_candidates,
                            candidates_after_constraints=candidates_after_constraints,
                            constraints_applied=constraints,
                            selected_target="cloud_gpu",
                            selected_node_id=instance.federation_node_id,
                            selected_reason=f"Provisioned new cloud GPU ({instance.gpu_type})",
                            outcome="provisioning",
                        )
                        return result
            elif target == "cloud":
                cloud_candidates = [c for c in candidates if c.get("_target") == "cloud"]
                if cloud_candidates:
                    result = self._build_result("cloud", cloud_candidates[0], request)
                    result["request_id"] = request_id
                    logger.info(
                        "Routed %s to cloud via LiteLLM (model=%s, tier=%s)", service_type, model, user_tier
                    )
                    await audit_log.log_decision(
                        request_id=request_id, service_type=service_type, model=model,
                        user_id=request.get("user_id"), user_tier=user_tier,
                        candidates_found=total_candidates,
                        candidates_after_constraints=candidates_after_constraints,
                        constraints_applied=constraints,
                        selected_target="cloud", selected_node_id="cloud",
                        selected_reason="Cloud fallback via LiteLLM", outcome="routed",
                    )
                    return result

        # 5. No target found
        await audit_log.log_decision(
            request_id=request_id, service_type=service_type, model=model,
            user_id=request.get("user_id"), user_tier=user_tier,
            candidates_found=total_candidates,
            candidates_after_constraints=candidates_after_constraints,
            constraints_applied=constraints,
            selected_target="none", outcome="no_capacity",
            selected_reason="No local, federated, or cloud backend could satisfy the request",
        )
        return {
            "route_type": "none",
            "reason": "No local, federated, or cloud backend could satisfy the request",
            "service_type": service_type,
            "model": model,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def proxy_to_node(
        self,
        node_id: str,
        endpoint_path: str,
        request_data: Dict[str, Any],
        *,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Forward a request to a peer federation node and track latency.

        Args:
            node_id: Target node identifier.
            endpoint_path: API path on the remote node (e.g. "/v1/chat/completions").
            request_data: JSON body to send.
            method: HTTP method (default POST).
            headers: Additional headers.

        Returns:
            Dict with response data and metadata (latency_ms, status_code).
        """
        circuit_breaker = get_circuit_breaker()

        # Check circuit breaker before attempting the request
        if not circuit_breaker.can_request(node_id):
            raise ConnectionError(
                f"Circuit breaker OPEN for node {node_id} — peer is unreachable"
            )

        node = await self.registry.get_node(node_id)
        if not node:
            raise ValueError(f"Unknown federation node: {node_id}")

        endpoint_url = node.get("endpoint_url", "").rstrip("/")
        if not endpoint_url:
            raise ValueError(f"Node {node_id} has no endpoint URL configured")

        url = f"{endpoint_url}{endpoint_path}"
        request_headers = {"Content-Type": "application/json"}

        # Add authentication if the node has credentials
        auth_credential = node.get("auth_credential")
        if auth_credential:
            request_headers["Authorization"] = f"Bearer {auth_credential}"

        if headers:
            request_headers.update(headers)

        start_time = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                else:
                    response = await client.post(
                        url, json=request_data, headers=request_headers
                    )

            latency_ms = (time.monotonic() - start_time) * 1000
            self._record_latency(node_id, latency_ms)

            response.raise_for_status()
            response_data = response.json()

            # Proxy succeeded — record success in circuit breaker
            circuit_breaker.record_success(node_id)

            # Record usage if metering is available
            if self.meter:
                try:
                    await self.meter.record_usage({
                        "event_type": "proxy_request",
                        "source_node_id": self.local_node_id,
                        "target_node_id": node_id,
                        "service_type": request_data.get("service_type", "unknown"),
                        "model": request_data.get("model"),
                        "latency_ms": latency_ms,
                        "status": "success",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as meter_exc:
                    logger.warning("Failed to record usage: %s", meter_exc)

            return {
                "data": response_data,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "node_id": node_id,
                "endpoint_url": url,
            }

        except httpx.TimeoutException:
            latency_ms = (time.monotonic() - start_time) * 1000
            self._record_latency(node_id, latency_ms)
            circuit_breaker.record_failure(node_id)
            logger.error("Proxy request to %s timed out after %.0fms", node_id, latency_ms)
            raise
        except httpx.HTTPStatusError as exc:
            latency_ms = (time.monotonic() - start_time) * 1000
            self._record_latency(node_id, latency_ms)
            # Only trip the circuit breaker for server errors (5xx), not client errors (4xx)
            if exc.response.status_code >= 500:
                circuit_breaker.record_failure(node_id)
            logger.error(
                "Proxy request to %s failed: HTTP %d", node_id, exc.response.status_code
            )
            raise
        except Exception as exc:
            circuit_breaker.record_failure(node_id)
            logger.error("Proxy request to %s failed: %s", node_id, exc)
            raise

    # ------------------------------------------------------------------
    # Service discovery
    # ------------------------------------------------------------------

    async def _find_local_service(
        self, service_type: str, model: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Check if the local node can handle this request."""
        if not self.local_node_id:
            return None

        services = await self.registry.get_service_catalog(
            service_type=service_type, node_id=self.local_node_id
        )
        for svc in services:
            if svc.get("status") not in {"running", "healthy", "loaded", "idle"}:
                continue
            if model and model not in (svc.get("models") or []):
                continue
            # Local services are free
            svc["cost_usd"] = 0.0
            svc["is_local"] = True
            return svc
        return None

    async def _find_peer_services(
        self, service_type: str, model: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Query registry for matching peer node services."""
        all_services = await self.registry.get_service_catalog(
            service_type=service_type
        )
        candidates = []
        for svc in all_services:
            # Skip local node
            if svc.get("node_id") == self.local_node_id:
                continue
            # Skip offline or unhealthy
            if svc.get("node_status") not in {None, "online", "degraded"}:
                continue
            if svc.get("status") not in {"running", "healthy", "loaded", "idle"}:
                continue
            # Check model availability
            if model and model not in (svc.get("models") or []):
                continue
            # Peer services are self-hosted (free between nodes)
            svc.setdefault("cost_usd", 0.0)
            svc["is_local"] = False
            candidates.append(svc)
        return candidates

    async def _find_cloud_service(
        self, service_type: str, model: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Build a cloud API fallback target via LiteLLM."""
        # Only LLM and embedding services can fall back to cloud
        cloud_service_types = {"llm", "embeddings", "reranker", "image_gen", "tts", "stt"}
        if service_type not in cloud_service_types:
            return None

        return {
            "node_id": "cloud",
            "display_name": "LiteLLM Cloud Proxy",
            "endpoint_url": self.litellm_url,
            "endpoint_path": self._cloud_endpoint_path(service_type),
            "service_type": service_type,
            "models": [model] if model else [],
            "status": "running",
            "cost_usd": self._estimate_cloud_cost(service_type, model),
            "avg_latency_ms": 500.0,
            "cold_start_seconds": 0,
            "is_local": False,
            "provider": "litellm",
            "capabilities": {},
        }

    # ------------------------------------------------------------------
    # Scoring and ranking
    # ------------------------------------------------------------------

    def _rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        request: Dict[str, Any],
        priority: str = "balanced",
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Score and rank candidates by configurable priority."""
        scored = []
        for candidate in candidates:
            score = self._calculate_routing_score(candidate, request, priority)
            scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored

    def _calculate_routing_score(
        self,
        candidate: Dict[str, Any],
        request: Dict[str, Any],
        priority: str = "balanced",
    ) -> float:
        """Calculate a composite routing score for a candidate.

        Scoring dimensions:
          - cost_score: self-hosted (100) > peer (90) > cloud (70 - cost_factor)
          - latency_score: local (100) > low-latency peer (90 - penalty) > cloud (50)
          - quality_score: model match (100), partial match (70), no models listed (50)
        """
        weights = SCORING_WEIGHTS.get(priority, SCORING_WEIGHTS["balanced"])

        # --- Cost score ---
        cost_usd = float(candidate.get("cost_usd") or 0.0)
        if candidate.get("is_local"):
            cost_score = 100.0
        elif candidate.get("provider") == "litellm":
            cost_score = max(70.0 - cost_usd * 100.0, 0.0)
        else:
            cost_score = max(90.0 - cost_usd * 50.0, 0.0)

        # --- Latency score ---
        node_id = candidate.get("node_id", "")
        avg_latency = self._get_avg_latency(node_id)
        if avg_latency is None:
            avg_latency = float(candidate.get("avg_latency_ms") or 500.0)

        cold_start = float(candidate.get("cold_start_seconds") or 0.0)

        if candidate.get("is_local"):
            latency_score = 100.0
        else:
            # Penalize for latency: every 100ms costs 5 points
            latency_penalty = avg_latency / 20.0
            cold_penalty = cold_start * 2.0
            latency_score = max(90.0 - latency_penalty - cold_penalty, 0.0)

        # --- Quality score ---
        requested_model = request.get("model")
        available_models = candidate.get("models") or []

        if not requested_model:
            quality_score = 80.0
        elif requested_model in available_models:
            quality_score = 100.0
        elif any(requested_model.lower() in m.lower() for m in available_models):
            quality_score = 70.0
        elif available_models:
            quality_score = 40.0
        else:
            quality_score = 50.0  # No model list published

        # --- VRAM bonus ---
        hardware = candidate.get("capabilities") or {}
        free_vram = float(
            hardware.get("free_vram_mb", hardware.get("total_vram_mb", 0.0)) or 0.0
        )
        requested_vram = float(request.get("min_vram_mb") or 0.0)
        vram_bonus = min(max(free_vram - requested_vram, 0.0), 48000.0) / 2000.0

        # --- Preferred node boost (from constraint filtering) ---
        preferred_boost = float(candidate.get("_preferred_boost", 0.0))

        # --- Composite score ---
        composite = (
            weights["cost"] * cost_score
            + weights["latency"] * latency_score
            + weights["quality"] * quality_score
            + vram_bonus
            + preferred_boost
        )

        return round(composite, 2)

    # ------------------------------------------------------------------
    # Constraint filtering
    # ------------------------------------------------------------------

    def _apply_constraints(
        self,
        candidates: List[Dict[str, Any]],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Filter and adjust candidates based on routing constraints.

        Supported constraints:
          - locality: "local_only" | "lan_only" | "any"
          - data_region: keep only nodes matching the specified region
          - required_gpu: "ampere+" (compute >= 8.0), "turing+" (>= 7.5), "any"
          - min_vram_gb: minimum GPU VRAM in GB
          - max_cost_usd: budget cap per request
          - preferred_node: boost score by 50 points
          - exclude_nodes: remove specific nodes
          - compliance: informational filter on node compliance tags
        """
        filtered = list(candidates)

        # --- locality ---
        locality = constraints.get("locality")
        if locality == "local_only":
            filtered = [c for c in filtered if c.get("_target") == "self"]
        elif locality == "lan_only":
            request_region = constraints.get("data_region")
            filtered = [
                c for c in filtered
                if c.get("_target") == "self"
                or (
                    c.get("_target") == "peer"
                    and (not request_region or c.get("region") == request_region)
                )
            ]

        # --- data_region ---
        data_region = constraints.get("data_region")
        if data_region:
            filtered = [
                c for c in filtered
                if c.get("_target") == "self"  # local always qualifies
                or c.get("region") == data_region
            ]

        # --- required_gpu ---
        gpu_min_compute = {
            "ampere+": 8.0,
            "turing+": 7.5,
        }
        required_gpu = constraints.get("required_gpu")
        if required_gpu and required_gpu != "any":
            min_compute = gpu_min_compute.get(required_gpu, 0.0)
            kept = []
            for c in filtered:
                hw = c.get("capabilities") or {}
                compute_cap = float(hw.get("compute_capability", 0.0) or 0.0)
                # If compute capability is unknown, keep the candidate (don't exclude)
                if compute_cap == 0.0 or compute_cap >= min_compute:
                    kept.append(c)
            filtered = kept

        # --- min_vram_gb ---
        min_vram_gb = constraints.get("min_vram_gb")
        if min_vram_gb is not None:
            min_vram_mb = min_vram_gb * 1024.0
            kept = []
            for c in filtered:
                hw = c.get("capabilities") or {}
                total_vram = float(hw.get("total_vram_mb", 0.0) or 0.0)
                # If VRAM info is unknown, keep the candidate
                if total_vram == 0.0 or total_vram >= min_vram_mb:
                    kept.append(c)
            filtered = kept

        # --- max_cost_usd ---
        max_cost = constraints.get("max_cost_usd")
        if max_cost is not None:
            filtered = [
                c for c in filtered
                if float(c.get("cost_usd") or 0.0) <= max_cost
            ]

        # --- exclude_nodes ---
        exclude_nodes = constraints.get("exclude_nodes")
        if exclude_nodes:
            exclude_set = set(exclude_nodes)
            filtered = [
                c for c in filtered
                if c.get("node_id") not in exclude_set
            ]

        # --- preferred_node (score boost, applied later during ranking) ---
        preferred_node = constraints.get("preferred_node")
        if preferred_node:
            for c in filtered:
                if c.get("node_id") == preferred_node:
                    c["_preferred_boost"] = 50.0

        # --- compliance (filter nodes missing required compliance tags) ---
        compliance = constraints.get("compliance")
        if compliance:
            required = set(compliance)
            kept = []
            for c in filtered:
                hw = c.get("capabilities") or {}
                node_compliance = set(hw.get("compliance", []) or [])
                # Local node or cloud: keep (assume compliant unless proven otherwise)
                if c.get("_target") in ("self", "cloud"):
                    kept.append(c)
                elif required.issubset(node_compliance):
                    kept.append(c)
                elif not node_compliance:
                    # No compliance info published — keep with a warning
                    kept.append(c)
            filtered = kept

        logger.debug(
            "Constraint filtering: %d candidates → %d after constraints %s",
            len(candidates),
            len(filtered),
            {k: v for k, v in constraints.items() if v is not None},
        )

        return filtered

    # ------------------------------------------------------------------
    # Latency tracking
    # ------------------------------------------------------------------

    def _record_latency(self, node_id: str, latency_ms: float) -> None:
        """Record a latency sample for a peer node."""
        if node_id not in _latency_history:
            _latency_history[node_id] = []
        samples = _latency_history[node_id]
        samples.append(latency_ms)
        if len(samples) > MAX_LATENCY_SAMPLES:
            _latency_history[node_id] = samples[-MAX_LATENCY_SAMPLES:]

    def _get_avg_latency(self, node_id: str) -> Optional[float]:
        """Get average latency for a node from recorded samples."""
        samples = _latency_history.get(node_id)
        if not samples:
            return None
        return sum(samples) / len(samples)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        route_type: str, candidate: Dict[str, Any], request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a standardized routing result."""
        return {
            "route_type": route_type,
            "service_type": request["service_type"],
            "model": request.get("model"),
            "target_node_id": candidate.get("node_id"),
            "target_display_name": candidate.get("display_name"),
            "target_endpoint_url": candidate.get("endpoint_url"),
            "target_endpoint_path": candidate.get("endpoint_path"),
            "avg_latency_ms": candidate.get("avg_latency_ms"),
            "cold_start_seconds": candidate.get("cold_start_seconds"),
            "cost_usd": candidate.get("cost_usd", 0.0),
            "provider": candidate.get("provider"),
            "capabilities": candidate.get("capabilities", {}),
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": f"Selected best {route_type} candidate based on scoring",
        }

    @staticmethod
    def _build_cloud_gpu_result(instance: Any, request: Dict[str, Any]) -> Dict[str, Any]:
        """Build a routing result for a cloud GPU instance."""
        return {
            "route_type": "cloud_gpu",
            "service_type": request["service_type"],
            "model": request.get("model"),
            "target_node_id": instance.federation_node_id,
            "target_display_name": f"Cloud {instance.gpu_type}",
            "target_endpoint_url": None,  # resolved via federation node registry
            "target_endpoint_path": None,
            "avg_latency_ms": None,
            "cold_start_seconds": int(
                (instance.ready_at - instance.created_at)
                if instance.ready_at
                else 0
            ),
            "cost_usd": instance.cost_per_hour / 3600,  # per-second cost approximation
            "provider": instance.provider.value,
            "cloud_instance_id": instance.id,
            "gpu_type": instance.gpu_type,
            "vram_gb": instance.vram_gb,
            "capabilities": {},
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": (
                f"Provisioned cloud GPU ({instance.gpu_type}) via {instance.provider.value}"
            ),
        }

    @staticmethod
    def _cloud_endpoint_path(service_type: str) -> str:
        """Return the LiteLLM endpoint path for a service type."""
        mapping = {
            "llm": "/v1/chat/completions",
            "embeddings": "/v1/embeddings",
            "reranker": "/v1/rerank",
            "image_gen": "/v1/images/generations",
            "tts": "/v1/audio/speech",
            "stt": "/v1/audio/transcriptions",
        }
        return mapping.get(service_type, "/v1/chat/completions")

    @staticmethod
    def _estimate_cloud_cost(service_type: str, model: Optional[str]) -> float:
        """Rough cost estimate for cloud API usage per request (USD)."""
        # Base cost estimates per request
        base_costs = {
            "llm": 0.005,
            "embeddings": 0.0001,
            "reranker": 0.0002,
            "image_gen": 0.04,
            "tts": 0.015,
            "stt": 0.006,
        }
        base = base_costs.get(service_type, 0.01)
        # Premium models cost more
        if model and any(
            tag in (model or "").lower()
            for tag in ["gpt-4", "claude-3", "opus", "sonnet"]
        ):
            base *= 3.0
        return round(base, 6)
