"""
Federation node agent daemon for self-registration, heartbeat emission,
and local service discovery.

Runs as a background asyncio task within Ops-Center. On startup it detects
hardware, discovers local services via health checks, and registers with
configured peer nodes. A heartbeat loop then reports GPU memory, load,
and service status every 30 seconds.
"""


import asyncio
import logging
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx

from federation.auth import get_federation_auth
from federation.hardware_detector import HardwareDetector

logger = logging.getLogger(__name__)

# Default service definitions per deployment profile
# Each entry: (name, docker_host, docker_port, host_port, service_type, health_path, models_path)
#
# Set FEDERATION_SERVICE_PROFILE env var to select which services to discover:
#   "home"       — your-gpu-server.example.com (GPU inference server)
#   "vps"        — your-ops-center.example.com (gateway, LiteLLM, Brigade)
#   "centerdeep" — centerdeep.online (search, extraction)
#   "custom"     — uses FEDERATION_CUSTOM_SERVICES JSON env var
#
# Default: "home" (backward compatible)

SERVICE_PROFILES = {
    "home": [
        ("llama-router", "unicorn-llama-router", 8080, 8085, "llm", "/health", "/v1/models"),
        ("whisperx", "whisperx-dev", 9000, 9000, "stt", "/health", None),
        ("kokoro-tts", "kokoro-tts", 8880, 8880, "tts", "/health", None),
        ("infinity-embeddings", "unicorn-infinity-proxy", 8080, 8086, "embeddings", "/health", None),
        ("infinity-reranker", "unicorn-infinity-proxy", 8080, 8086, "reranker", "/health", None),
        ("artwork-studio", "unicorn-artwork-api", 8095, 8095, "image_gen", "/health", None),
        ("majiks-studio", "unicorn-majiks-api", 8090, 8091, "music_gen", "/health", None),
        ("granite-proxy", "unicorn-granite-proxy", 8080, 8089, "extraction", "/health", None),
        ("brigade", "unicorn-brigade", 8100, 8101, "agents", "/", "/api/agents"),
    ],
    "vps": [
        ("litellm", "uchub-litellm", 4000, 4000, "llm", "/health", "/v1/models"),
        ("brigade", "unicorn-brigade", 8100, 8101, "agents", "/", "/api/agents"),
    ],
    "centerdeep": [
        ("search-web", "center-deep-tool-search", 8001, 11001, "search", "/health", None),
        ("search-deep", "center-deep-tool-deep-search", 8002, 11002, "search", "/health", None),
        ("search-report", "center-deep-tool-report", 8003, 11003, "search", "/health", None),
        ("search-academic", "center-deep-tool-academic", 8004, 11004, "search", "/health", None),
        ("tika", "unicorn-tika", 9998, 9998, "extraction", "/tika", None),
    ],
}


def _get_local_services():
    """Get the service discovery list for this node's profile."""
    profile = os.getenv("FEDERATION_SERVICE_PROFILE", "home")
    if profile == "custom":
        custom = os.getenv("FEDERATION_CUSTOM_SERVICES", "[]")
        try:
            return [tuple(s) for s in json.loads(custom)]
        except Exception:
            logger.warning("Failed to parse FEDERATION_CUSTOM_SERVICES, using empty list")
            return []
    return SERVICE_PROFILES.get(profile, SERVICE_PROFILES["home"])


LOCAL_SERVICES = _get_local_services()

class NodeAgent:
    """Federation node agent that handles registration, heartbeats,
    and local service discovery.

    All configuration is via environment variables:
        FEDERATION_NODE_ID          - Unique node identifier
        FEDERATION_NODE_NAME        - Human-readable display name
        FEDERATION_ENDPOINT_URL     - This node's externally reachable URL
        FEDERATION_KEY              - Shared secret for peer authentication
        FEDERATION_PEERS            - Comma-separated list of peer URLs
        FEDERATION_ROLES            - Comma-separated roles (default: gateway,inference)
        FEDERATION_REGION           - Geographic region identifier
        FEDERATION_HEARTBEAT_INTERVAL - Seconds between heartbeats (default: 30)
    """

    def __init__(
        self,
        *,
        node_id: str,
        display_name: str,
        endpoint_url: str,
        peers: Iterable[str],
        auth_token: Optional[str] = None,
        roles: Optional[List[str]] = None,
        region: Optional[str] = None,
        heartbeat_interval: int = 30,
    ):
        self.node_id = node_id
        self.display_name = display_name
        self.endpoint_url = endpoint_url.rstrip("/")
        self.peers = [peer.rstrip("/") for peer in peers if peer]
        self.auth_token = auth_token or os.getenv("FEDERATION_KEY")
        self.roles = roles or self._parse_roles()
        self.region = region or os.getenv("FEDERATION_REGION")
        self.heartbeat_interval = heartbeat_interval
        self.hardware_detector = HardwareDetector()
        self._task: Optional[asyncio.Task] = None
        self._shutdown = asyncio.Event()
        self._discovered_services: List[Dict[str, Any]] = []
        self._last_hardware: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the agent: detect hardware, discover services, register, begin heartbeats."""
        if not self.peers:
            logger.info("Federation agent: no peers configured, running in standalone mode")

        try:
            # Initial hardware detection
            self._last_hardware = self.hardware_detector.detect()
            logger.info(
                "Hardware detected: %d GPUs, %d CPU cores, %.1f GB RAM",
                len(self._last_hardware.get("gpus", [])),
                self._last_hardware.get("cpu", {}).get("logical_cores", 0),
                self._last_hardware.get("memory", {}).get("total_gb", 0),
            )

            # Discover local services
            self._discovered_services = await self._discover_local_services()
            logger.info(
                "Discovered %d local services: %s",
                len(self._discovered_services),
                ", ".join(s["service_type"] for s in self._discovered_services),
            )

            # Register with peers
            if self.peers:
                await self._register_with_peers()

        except Exception as exc:
            logger.error("Federation agent startup error (non-fatal): %s", exc)

        # Start heartbeat loop
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Federation agent started (node_id=%s)", self.node_id)

    async def stop(self) -> None:
        """Stop the agent and deregister from peers."""
        self._shutdown.set()

        # Graceful deregistration
        if self.peers:
            try:
                await self._deregister_from_peers()
            except Exception as exc:
                logger.warning("Deregistration failed (non-fatal): %s", exc)

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        logger.info("Federation agent stopped (node_id=%s)", self.node_id)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def _register_with_peers(self) -> Dict[str, Any]:
        """Register this node with all configured peers."""
        payload = self._build_registration_payload()
        results = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for peer in self.peers:
                try:
                    url = f"{peer}/api/v1/federation/register"
                    response = await client.post(
                        url, json=payload, headers=self._headers()
                    )
                    response.raise_for_status()
                    results.append({"peer": peer, "status": "ok", "response": response.json()})
                    logger.info("Registered with peer %s", peer)
                except Exception as exc:
                    results.append({"peer": peer, "status": "error", "error": str(exc)})
                    logger.warning("Failed to register with peer %s: %s", peer, exc)
        return {"registered_with": len([r for r in results if r["status"] == "ok"]), "results": results}

    async def _deregister_from_peers(self) -> None:
        """Notify peers that this node is going offline."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for peer in self.peers:
                try:
                    url = f"{peer}/api/v1/federation/deregister"
                    await client.post(
                        url,
                        json={"node_id": self.node_id},
                        headers=self._headers(),
                    )
                    logger.info("Deregistered from peer %s", peer)
                except Exception as exc:
                    logger.debug("Deregistration from %s failed: %s", peer, exc)

    def _build_registration_payload(self) -> Dict[str, Any]:
        """Build the full registration payload."""
        return {
            "node_id": self.node_id,
            "display_name": self.display_name,
            "endpoint_url": self.endpoint_url,
            "auth_method": "jwt",
            "hardware_profile": self._last_hardware,
            "roles": self.roles,
            "region": self.region,
            "services": self._discovered_services,
            "is_self": True,
        }

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        """Background loop that sends heartbeats at the configured interval."""
        while not self._shutdown.is_set():
            try:
                await self._send_heartbeat()
            except Exception as exc:
                logger.warning("Heartbeat failed: %s", exc)

            try:
                await asyncio.wait_for(
                    self._shutdown.wait(), timeout=self.heartbeat_interval
                )
            except asyncio.TimeoutError:
                continue

    async def _send_heartbeat(self) -> None:
        """Send a single heartbeat to all peers."""
        # Refresh hardware and services periodically
        self._last_hardware = self.hardware_detector.detect()
        self._discovered_services = await self._discover_local_services()

        payload = {
            "node_id": self.node_id,
            "load": self._build_load_report(),
            "hardware_profile": self._last_hardware,
            "services": self._discovered_services,
        }

        # Self-heartbeat to keep our own node fresh in the local registry
        try:
            async with httpx.AsyncClient(timeout=5.0) as local_client:
                await local_client.post(
                    "http://localhost:8084/api/v1/federation/heartbeat",
                    json=payload,
                    headers=self._headers(),
                )
        except Exception:
            pass  # Local heartbeat failure is non-fatal

        if not self.peers:
            return

        async with httpx.AsyncClient(timeout=20.0) as client:
            for peer in self.peers:
                try:
                    url = f"{peer}/api/v1/federation/heartbeat"
                    response = await client.post(
                        url, json=payload, headers=self._headers()
                    )
                    response.raise_for_status()
                except Exception as exc:
                    logger.debug("Heartbeat to %s failed: %s", peer, exc)

    def _build_load_report(self) -> Dict[str, Any]:
        """Build current load metrics."""
        cpu = self._last_hardware.get("cpu", {})
        mem = self._last_hardware.get("memory", {})
        gpus = self._last_hardware.get("gpus", [])

        gpu_load = []
        for gpu in gpus:
            gpu_load.append({
                "index": gpu.get("index"),
                "name": gpu.get("name"),
                "utilization_percent": gpu.get("utilization_percent", 0),
                "memory_used_mb": gpu.get("memory_used_mb", 0),
                "memory_total_mb": gpu.get("memory_total_mb", 0),
                "memory_free_mb": gpu.get("memory_free_mb", 0),
            })

        return {
            "cpu_percent": cpu.get("usage_percent", 0),
            "memory_total_gb": mem.get("total_gb", 0),
            "memory_available_gb": mem.get("available_gb", 0),
            "gpu_load": gpu_load,
        }

    # ------------------------------------------------------------------
    # Service discovery
    # ------------------------------------------------------------------

    async def _discover_local_services(self) -> List[Dict[str, Any]]:
        """Check local service endpoints for availability via health checks."""
        services = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            tasks = [
                self._check_service(client, name, docker_host, docker_port, host_port, svc_type, health_path, models_path)
                for name, docker_host, docker_port, host_port, svc_type, health_path, models_path in LOCAL_SERVICES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict):
                services.append(result)
            # Exceptions are silently ignored (service not available)

        if services:
            logger.info("Discovered %d local services: %s", len(services),
                       ", ".join(s["service_type"] for s in services))

        return services

    async def _check_service(
        self,
        client: httpx.AsyncClient,
        name: str,
        docker_host: str,
        docker_port: int,
        host_port: int,
        service_type: str,
        health_path: str,
        models_path: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Check if a single local service is healthy and optionally fetch its models.
        Tries Docker container name first, then falls back to localhost with host-mapped port."""
        # Try Docker container name first (container-to-container)
        urls_to_try = [
            f"http://{docker_host}:{docker_port}{health_path}",
            f"http://localhost:{host_port}{health_path}",
        ]
        url = None
        for try_url in urls_to_try:
            try:
                response = await client.get(try_url)
                # < 500 means the service is running — 401/403 just means auth-protected
                if response.status_code < 500:
                    url = try_url
                    break
            except Exception:
                continue

        if url is None:
            return None

        # Service is healthy — extract base URL for model fetching
        base_url = url.rsplit(health_path, 1)[0]

        models = []
        if models_path:
            models = await self._fetch_models(client, base_url, models_path)

        endpoint_path = self._service_endpoint_path(service_type)

        return {
            "service_type": service_type,
            "name": name,
            "port": host_port,
            "models": models,
            "endpoint_path": endpoint_path,
            "status": "running",
            "capabilities": {
                "hardware_accelerated": len(self._last_hardware.get("gpus", [])) > 0,
            },
            "cold_start_seconds": 5 if service_type in {"embeddings", "reranker"} else 20,
            "avg_latency_ms": 150 if service_type in {"embeddings", "reranker"} else 800,
            "cost_usd": 0.0,
        }

    async def _fetch_models(
        self, client: httpx.AsyncClient, base_url: str, models_path: str
    ) -> List[str]:
        """Fetch the model list from a service's /v1/models endpoint."""
        url = f"{base_url}{models_path}"
        try:
            response = await client.get(url)
            if response.status_code >= 400:
                return []
            data = response.json()
            # OpenAI-compatible format: {"data": [{"id": "model-name"}, ...]}
            if isinstance(data, dict) and "data" in data:
                return [m.get("id", "") for m in data["data"] if m.get("id")]
            # Brigade agents format: {"agents": [{"id": "agent-id"}, ...]}
            if isinstance(data, dict) and "agents" in data:
                return [m.get("id", "") for m in data["agents"] if m.get("id")]
            # Simple list format
            if isinstance(data, list):
                return [str(m) for m in data]
            return []
        except Exception:
            return []

    @staticmethod
    def _service_endpoint_path(service_type: str) -> str:
        """Return the default API path for a service type."""
        mapping = {
            "llm": "/v1/chat/completions",
            "tts": "/v1/audio/speech",
            "stt": "/v1/audio/transcriptions",
            "embeddings": "/v1/embeddings",
            "reranker": "/v1/rerank",
            "image_gen": "/v1/images/generate",
            "music_gen": "/v1/music/generate",
            "agents": "/api/v1/a2a/agents/{id}/invoke",
        }
        return mapping.get(service_type, "/v1/inference")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        """Build authentication headers for peer requests.

        Uses per-node signed JWTs via FederationAuth. Falls back to raw
        Bearer token if FederationAuth is not configured (backward compat).
        """
        try:
            fed_auth = get_federation_auth()
            if fed_auth.shared_key or fed_auth.auth_mode == "node_keys":
                return fed_auth.get_auth_headers()
        except Exception:
            pass
        # Fallback: raw shared key (backward compatible)
        headers: Dict[str, str] = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    @staticmethod
    def _parse_roles() -> List[str]:
        """Parse roles from environment variable."""
        roles_str = os.getenv("FEDERATION_ROLES", "gateway,inference")
        return [r.strip() for r in roles_str.split(",") if r.strip()]


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_agent_instance: Optional[NodeAgent] = None


def get_node_agent() -> NodeAgent:
    """Get or create the module-level NodeAgent singleton.

    Configuration is read from environment variables. If federation is not
    configured, a minimal agent is returned that will run in standalone mode.
    """
    global _agent_instance
    if _agent_instance is None:
        hostname = socket.gethostname().split(".")[0]
        peers_str = os.getenv("FEDERATION_PEERS", "")
        _agent_instance = NodeAgent(
            node_id=os.getenv("FEDERATION_NODE_ID", f"uc-{hostname}"),
            display_name=os.getenv("FEDERATION_NODE_NAME", hostname),
            endpoint_url=os.getenv("FEDERATION_ENDPOINT_URL", "http://localhost:8084"),
            peers=[p.strip() for p in peers_str.split(",") if p.strip()],
            auth_token=os.getenv("FEDERATION_KEY") or os.getenv("FEDERATION_SHARED_SECRET"),
            heartbeat_interval=int(os.getenv("FEDERATION_HEARTBEAT_INTERVAL", "30")),
        )
    return _agent_instance
