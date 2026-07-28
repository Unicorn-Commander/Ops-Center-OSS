"""
Cloud GPU Auto-Provisioner

Manages the lifecycle of on-demand cloud GPU instances:
1. Provision — Spin up a RunPod/Lambda instance with federation bootstrap
2. Wait — Poll until instance is running and registered with federation
3. Route — Return the instance as a routing target
4. Monitor — Track active instances, costs, idle timeouts
5. Terminate — Shut down idle instances (handled by the instance itself via federation-idle-monitor)

Supports:
- RunPod (primary) — GraphQL API for pod management
- Lambda Labs — REST API for instance management
- Extensible for Vast.ai, etc.

Configuration via environment variables:
- RUNPOD_API_KEY — RunPod API key
- LAMBDA_API_KEY — Lambda Labs API key
- CLOUD_GPU_ENABLED — Enable/disable auto-provisioning (default: false)
- CLOUD_GPU_PROVIDER — Default provider: runpod, lambda (default: runpod)
- CLOUD_GPU_MAX_INSTANCES — Maximum concurrent cloud instances (default: 3)
- CLOUD_GPU_BUDGET_HOURLY — Max hourly spend in USD (default: 5.0)
"""

import os
import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import httpx

from federation.resilience import DistributedLock

logger = logging.getLogger("federation.cloud_provisioner")


class CloudProvider(Enum):
    RUNPOD = "runpod"
    LAMBDA = "lambda"


class InstanceStatus(Enum):
    REQUESTING = "requesting"
    BOOTING = "booting"
    REGISTERING = "registering"  # waiting for federation registration
    READY = "ready"
    DRAINING = "draining"
    TERMINATED = "terminated"
    FAILED = "failed"


@dataclass
class CloudInstance:
    """Tracks a provisioned cloud GPU instance."""
    id: str  # our internal ID
    provider: CloudProvider
    provider_instance_id: str  # RunPod pod ID or Lambda instance ID
    gpu_type: str  # e.g. "A10G", "A100"
    gpu_count: int
    vram_gb: int
    service_profile: str  # music, image, stt, llm, embeddings, all
    status: InstanceStatus
    cost_per_hour: float
    federation_node_id: Optional[str] = None  # once registered
    created_at: float = field(default_factory=time.time)
    ready_at: Optional[float] = None
    terminated_at: Optional[float] = None
    total_cost: float = 0.0
    requests_served: int = 0
    last_request_at: Optional[float] = None


# GPU type to specs mapping for cost estimation and selection
GPU_SPECS = {
    # RunPod pricing (approximate, per hour)
    "NVIDIA RTX A4000": {"vram_gb": 16, "cost_hr": 0.20, "provider": "runpod"},
    "NVIDIA RTX A4500": {"vram_gb": 20, "cost_hr": 0.25, "provider": "runpod"},
    "NVIDIA RTX A5000": {"vram_gb": 24, "cost_hr": 0.30, "provider": "runpod"},
    "NVIDIA A10G": {"vram_gb": 24, "cost_hr": 0.50, "provider": "runpod"},
    "NVIDIA RTX A6000": {"vram_gb": 48, "cost_hr": 0.65, "provider": "runpod"},
    "NVIDIA A40": {"vram_gb": 48, "cost_hr": 0.55, "provider": "runpod"},
    "NVIDIA A100 40GB": {"vram_gb": 40, "cost_hr": 1.10, "provider": "runpod"},
    "NVIDIA A100 80GB": {"vram_gb": 80, "cost_hr": 1.60, "provider": "runpod"},
    "NVIDIA H100 80GB": {"vram_gb": 80, "cost_hr": 3.50, "provider": "runpod"},
    # Lambda pricing (live as of March 2026)
    "gpu_1x_a10": {"vram_gb": 24, "cost_hr": 0.86, "provider": "lambda"},
    "gpu_1x_a100_sxm4": {"vram_gb": 40, "cost_hr": 1.48, "provider": "lambda"},
    "gpu_1x_gh200": {"vram_gb": 96, "cost_hr": 1.99, "provider": "lambda"},
    "gpu_1x_h100_pcie": {"vram_gb": 80, "cost_hr": 2.86, "provider": "lambda"},
    "gpu_1x_h100_sxm5": {"vram_gb": 80, "cost_hr": 3.78, "provider": "lambda"},
    "gpu_1x_b200_sxm6": {"vram_gb": 192, "cost_hr": 6.08, "provider": "lambda"},
}

# Service profile VRAM requirements (from service-profiles.yml)
SERVICE_VRAM_REQUIREMENTS = {
    "embeddings": 4,
    "stt": 2,
    "tts": 1,
    "llm": 8,
    "image": 12,
    "image_gen": 12,
    "music": 14,
    "music_gen": 14,
    "reranker": 4,
    "all": 24,  # minimum for a useful "all" deployment
}


class CloudProvisioner:
    """Manages on-demand cloud GPU instances for the federation."""

    def __init__(self):
        self.enabled = os.getenv("CLOUD_GPU_ENABLED", "false").lower() == "true"
        self.default_provider = os.getenv("CLOUD_GPU_PROVIDER", "lambda")
        self.max_instances = int(os.getenv("CLOUD_GPU_MAX_INSTANCES", "3"))
        self.budget_hourly = float(os.getenv("CLOUD_GPU_BUDGET_HOURLY", "5.0"))
        self.runpod_api_key = os.getenv("RUNPOD_API_KEY", "")
        self.lambda_api_key = os.getenv("LAMBDA_API_KEY", "")
        self.federation_key = os.getenv("FEDERATION_KEY", "")
        self.federation_endpoint = os.getenv("FEDERATION_ENDPOINT_URL", "")

        # Docker image to deploy on cloud instances
        # This should be your pre-built image with inference services + federation CLI
        self.docker_image = os.getenv("CLOUD_GPU_DOCKER_IMAGE", "")

        # Active instances tracker
        self.instances: Dict[str, CloudInstance] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._distributed_lock: Optional[DistributedLock] = None

    def set_redis(self, redis_client) -> None:
        """Set the Redis client for distributed locking."""
        if redis_client:
            self._distributed_lock = DistributedLock(redis_client)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def provision_for_service(
        self,
        service_type: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        gpu_type: Optional[str] = None,
        user_tier: Optional[str] = None,
    ) -> Optional[CloudInstance]:
        """
        Provision a cloud GPU instance for a specific service type.

        Called by the federation router when no local/peer capacity exists.
        Uses a distributed lock to prevent duplicate provisioning.

        Returns CloudInstance once it's ready, or None if provisioning failed.
        """
        if not self.enabled:
            logger.debug("Cloud GPU provisioning is disabled")
            return None

        lock_name = f"provision:{service_type}"
        holder_id = uuid.uuid4().hex[:8]
        lock_acquired = False

        # Try to acquire distributed lock to prevent duplicate provisioning
        if self._distributed_lock:
            lock_acquired = await self._distributed_lock.acquire(lock_name, holder_id)
            if not lock_acquired:
                # Another process is already provisioning for this service type.
                # Wait up to 30 seconds for it to finish, then check for a ready instance.
                logger.info(
                    f"Provisioning lock held for {service_type}, waiting for existing provision"
                )
                for _ in range(6):
                    await asyncio.sleep(5)
                    existing = self.find_ready_instance(service_type)
                    if existing:
                        logger.info(
                            f"Instance appeared while waiting for lock: {existing.id}"
                        )
                        return existing
                    if not await self._distributed_lock.is_locked(lock_name):
                        # Lock released but no instance appeared — try again
                        lock_acquired = await self._distributed_lock.acquire(
                            lock_name, holder_id
                        )
                        if lock_acquired:
                            break
                if not lock_acquired:
                    logger.warning(
                        f"Could not acquire provisioning lock for {service_type} after waiting"
                    )
                    return None

        try:
            return await self._do_provision(
                service_type, model, provider, gpu_type, user_tier
            )
        finally:
            if lock_acquired and self._distributed_lock:
                await self._distributed_lock.release(lock_name, holder_id)

    async def _do_provision(
        self,
        service_type: str,
        model: Optional[str],
        provider: Optional[str],
        gpu_type: Optional[str],
        user_tier: Optional[str],
    ) -> Optional[CloudInstance]:
        """Internal provisioning logic (called under distributed lock)."""
        # Check limits
        active = [
            i for i in self.instances.values()
            if i.status in (
                InstanceStatus.REQUESTING,
                InstanceStatus.BOOTING,
                InstanceStatus.REGISTERING,
                InstanceStatus.READY,
            )
        ]
        if len(active) >= self.max_instances:
            logger.warning(f"Max cloud instances reached ({self.max_instances})")
            return None

        # Check budget
        hourly_cost = sum(i.cost_per_hour for i in active)
        if hourly_cost >= self.budget_hourly:
            logger.warning(
                f"Hourly budget exceeded (${hourly_cost:.2f} >= ${self.budget_hourly:.2f})"
            )
            return None

        # Select optimal GPU for this service
        provider = provider or self.default_provider
        profile = service_type
        min_vram = SERVICE_VRAM_REQUIREMENTS.get(profile, 8)

        if gpu_type is None:
            gpu_type = await self._select_gpu_with_availability(min_vram, provider)
            if gpu_type is None:
                logger.error(f"No suitable GPU found for {profile} (needs {min_vram}GB)")
                return None

        gpu_spec = GPU_SPECS.get(gpu_type, {})

        # Create instance record
        instance = CloudInstance(
            id=f"cloud-{uuid.uuid4().hex[:8]}",
            provider=CloudProvider(provider),
            provider_instance_id="",  # set after API call
            gpu_type=gpu_type,
            gpu_count=1,
            vram_gb=gpu_spec.get("vram_gb", 24),
            service_profile=profile,
            status=InstanceStatus.REQUESTING,
            cost_per_hour=gpu_spec.get("cost_hr", 0.50),
        )
        self.instances[instance.id] = instance

        try:
            # Provision via provider API
            if provider == "runpod":
                provider_id = await self._provision_runpod(instance, profile)
            elif provider == "lambda":
                provider_id = await self._provision_lambda(instance, profile)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            instance.provider_instance_id = provider_id
            instance.status = InstanceStatus.BOOTING
            logger.info(
                f"Cloud instance {instance.id} provisioned: {gpu_type} on {provider} "
                f"(pod={provider_id})"
            )

            # Wait for federation registration
            instance.federation_node_id = await self._wait_for_registration(
                instance, timeout=180
            )

            if instance.federation_node_id:
                instance.status = InstanceStatus.READY
                instance.ready_at = time.time()
                boot_time = int(instance.ready_at - instance.created_at)
                logger.info(
                    f"Cloud instance {instance.id} ready in {boot_time}s, "
                    f"federation node: {instance.federation_node_id}"
                )
                return instance
            else:
                instance.status = InstanceStatus.FAILED
                logger.error(
                    f"Cloud instance {instance.id} failed to register with "
                    f"federation within timeout"
                )
                await self._terminate_instance(instance)
                return None

        except Exception as e:
            instance.status = InstanceStatus.FAILED
            logger.error(f"Cloud provisioning failed: {e}")
            return None

    def _select_gpu(self, min_vram: int, provider: str) -> Optional[str]:
        """Select the cheapest GPU that meets VRAM requirements."""
        candidates = []
        for gpu_name, spec in GPU_SPECS.items():
            if spec.get("provider") == provider and spec["vram_gb"] >= min_vram:
                candidates.append((gpu_name, spec["cost_hr"]))

        if not candidates:
            return None

        # Sort by cost (cheapest first)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    async def _find_lambda_region(self, instance_type: str) -> Optional[str]:
        """Query Lambda API for a region with capacity for this instance type."""
        client = await self._get_client()
        try:
            resp = await client.get(
                "https://cloud.lambdalabs.com/api/v1/instance-types",
                headers={"Authorization": f"Bearer {self.lambda_api_key}"}
            )
            data = resp.json()
            type_info = data.get("data", {}).get(instance_type, {})
            regions = type_info.get("regions_with_capacity_available", [])
            if regions:
                return regions[0]["name"]
        except Exception as e:
            logger.warning(f"Failed to query Lambda regions: {e}")
        return None

    async def _select_gpu_with_availability(self, min_vram: int, provider: str) -> Optional[str]:
        """Select cheapest GPU that meets VRAM requirements AND has availability."""
        if provider != "lambda":
            return self._select_gpu(min_vram, provider)

        # For Lambda, check live availability
        client = await self._get_client()
        try:
            resp = await client.get(
                "https://cloud.lambdalabs.com/api/v1/instance-types",
                headers={"Authorization": f"Bearer {self.lambda_api_key}"}
            )
            data = resp.json()
            candidates = []
            for type_name, info in data.get("data", {}).items():
                regions = info.get("regions_with_capacity_available", [])
                if not regions:
                    continue
                specs = info.get("instance_type", {}).get("specs", {})
                vram = specs.get("gpu_ram_gb", 0)
                if isinstance(vram, (int, float)) and vram >= min_vram:
                    price = info.get("instance_type", {}).get("price_cents_per_hour", 9999) / 100
                    candidates.append((type_name, price, vram))

            if candidates:
                candidates.sort(key=lambda x: x[1])  # cheapest first
                chosen = candidates[0]
                logger.info(f"Lambda GPU selected: {chosen[0]} ({chosen[2]}GB, ${chosen[1]:.2f}/hr)")
                return chosen[0]
        except Exception as e:
            logger.warning(f"Failed to query Lambda availability: {e}")

        # Fall back to static selection
        return self._select_gpu(min_vram, provider)

    async def _provision_runpod(self, instance: CloudInstance, profile: str) -> str:
        """Provision a RunPod pod via GraphQL API."""
        client = await self._get_client()

        # Environment variables for the federation bootstrap
        env_vars = {
            "FEDERATION_PEERS": self.federation_endpoint,
            "FEDERATION_KEY": self.federation_key,
            "FEDERATION_NODE_ID": instance.id,
            "FEDERATION_NODE_NAME": f"Cloud {instance.gpu_type}",
            "FEDERATION_ROLES": "inference",
            "FEDERATION_REGION": "cloud-runpod",
            "SERVICE_PROFILE": profile,
            "IDLE_TIMEOUT_MINUTES": "5",
            "GPU_PROVIDER": "runpod",
        }

        env_str = ", ".join(
            [f'{{key: "{k}", value: "{v}"}}' for k, v in env_vars.items()]
        )

        # Map our GPU name to RunPod GPU ID
        gpu_id_map = {
            "NVIDIA A10G": "NVIDIA A10G",
            "NVIDIA RTX A4000": "NVIDIA RTX A4000",
            "NVIDIA RTX A4500": "NVIDIA RTX A4500",
            "NVIDIA RTX A5000": "NVIDIA RTX A5000",
            "NVIDIA RTX A6000": "NVIDIA RTX A6000",
            "NVIDIA A40": "NVIDIA A40",
            "NVIDIA A100 40GB": "NVIDIA A100",
            "NVIDIA A100 80GB": "NVIDIA A100 80GB SXM",
            "NVIDIA H100 80GB": "NVIDIA H100 80GB HBM3",
        }
        runpod_gpu = gpu_id_map.get(instance.gpu_type, instance.gpu_type)

        docker_image = (
            self.docker_image
            or "runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel-ubuntu22.04"
        )

        query = """
        mutation {
            podFindAndDeployOnDemand(input: {
                name: "uc-federation-%s"
                imageName: "%s"
                gpuTypeId: "%s"
                gpuCount: %d
                volumeInGb: 50
                containerDiskInGb: 20
                minVcpuCount: 4
                minMemoryInGb: 16
                env: [%s]
                dockerArgs: "bash /workspace/bootstrap.sh"
            }) {
                id
                desiredStatus
                imageName
                machine { gpuDisplayName }
            }
        }
        """ % (
            instance.id,
            docker_image,
            runpod_gpu,
            instance.gpu_count,
            env_str,
        )

        resp = await client.post(
            "https://api.runpod.io/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {self.runpod_api_key}"},
        )

        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"RunPod API error: {data['errors']}")

        pod = data.get("data", {}).get("podFindAndDeployOnDemand", {})
        pod_id = pod.get("id", "")
        if not pod_id:
            raise RuntimeError(f"RunPod returned no pod ID: {data}")
        return pod_id

    async def _provision_lambda(self, instance: CloudInstance, profile: str) -> str:
        """Provision a Lambda Labs instance via REST API."""
        client = await self._get_client()

        # GPU type names in GPU_SPECS already match Lambda's instance type names
        instance_type = instance.gpu_type

        # Find a region with capacity for this instance type
        region = await self._find_lambda_region(instance_type)
        if not region:
            raise RuntimeError(f"No Lambda regions have capacity for {instance_type}")

        # Attach persistent filesystem for pre-cached models
        lambda_fs_name = os.getenv("LAMBDA_FILESYSTEM_NAME", "")
        launch_payload = {
            "region_name": region,
            "instance_type_name": instance_type,
            "ssh_key_names": [],
            "quantity": 1,
            "name": f"uc-federation-{instance.id}",
        }
        if lambda_fs_name:
            launch_payload["file_system_names"] = [lambda_fs_name]

        resp = await client.post(
            "https://cloud.lambdalabs.com/api/v1/instance-operations/launch",
            json=launch_payload,
            headers={"Authorization": f"Bearer {self.lambda_api_key}"},
        )

        data = resp.json()
        instances = data.get("data", {}).get("instance_ids", [])
        if not instances:
            raise RuntimeError(f"Lambda API error: {data}")

        return instances[0]

    async def _wait_for_registration(
        self, instance: CloudInstance, timeout: int = 180
    ) -> Optional[str]:
        """Wait for the cloud instance to register with federation."""
        instance.status = InstanceStatus.REGISTERING
        client = await self._get_client()

        start = time.time()
        while time.time() - start < timeout:
            try:
                # Query federation nodes for our instance
                nodes_resp = await client.get(
                    "http://localhost:8084/api/v1/federation/nodes",
                    headers={"Cookie": ""},  # internal call, no auth needed
                )
                if nodes_resp.status_code == 200:
                    data = nodes_resp.json()
                    nodes = data.get("nodes", data) if isinstance(data, dict) else data
                    for node in nodes:
                        if node.get("node_id") == instance.id:
                            return instance.id
            except Exception:
                pass

            await asyncio.sleep(5)

        return None

    async def _terminate_instance(self, instance: CloudInstance):
        """Terminate a cloud instance."""
        client = await self._get_client()
        instance.status = InstanceStatus.DRAINING

        try:
            if instance.provider == CloudProvider.RUNPOD:
                # Use podTerminate to fully remove the pod (not just stop)
                query = (
                    'mutation { podTerminate(input: {podId: "%s"}) }'
                    % instance.provider_instance_id
                )
                await client.post(
                    "https://api.runpod.io/graphql",
                    json={"query": query},
                    headers={"Authorization": f"Bearer {self.runpod_api_key}"},
                )
            elif instance.provider == CloudProvider.LAMBDA:
                await client.post(
                    "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate",
                    json={"instance_ids": [instance.provider_instance_id]},
                    headers={"Authorization": f"Bearer {self.lambda_api_key}"},
                )

            instance.status = InstanceStatus.TERMINATED
            instance.terminated_at = time.time()

            # Calculate total cost
            runtime_hours = (instance.terminated_at - instance.created_at) / 3600
            instance.total_cost = runtime_hours * instance.cost_per_hour

            logger.info(
                f"Cloud instance {instance.id} terminated. "
                f"Runtime: {runtime_hours:.2f}h, Cost: ${instance.total_cost:.2f}"
            )

        except Exception as e:
            logger.error(f"Failed to terminate {instance.id}: {e}")

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def find_ready_instance(self, service_type: str) -> Optional[CloudInstance]:
        """Find an existing READY cloud instance that serves the given service type."""
        for inst in self.instances.values():
            if (
                inst.service_profile == service_type
                and inst.status == InstanceStatus.READY
            ):
                return inst
        return None

    def record_request(self, instance_id: str):
        """Record that a request was served by a cloud instance."""
        inst = self.instances.get(instance_id)
        if inst:
            inst.requests_served += 1
            inst.last_request_at = time.time()

    def get_active_instances(self) -> List[Dict[str, Any]]:
        """Get all active cloud instances."""
        return [
            {
                "id": inst.id,
                "provider": inst.provider.value,
                "provider_instance_id": inst.provider_instance_id,
                "gpu_type": inst.gpu_type,
                "vram_gb": inst.vram_gb,
                "service_profile": inst.service_profile,
                "status": inst.status.value,
                "cost_per_hour": inst.cost_per_hour,
                "federation_node_id": inst.federation_node_id,
                "uptime_minutes": int((time.time() - inst.created_at) / 60),
                "total_cost": round(
                    ((time.time() - inst.created_at) / 3600) * inst.cost_per_hour, 4
                ),
                "requests_served": inst.requests_served,
            }
            for inst in self.instances.values()
            if inst.status not in (InstanceStatus.TERMINATED, InstanceStatus.FAILED)
        ]

    def get_current_hourly_cost(self) -> float:
        """Get current hourly cost of all active instances."""
        return sum(
            inst.cost_per_hour
            for inst in self.instances.values()
            if inst.status
            in (InstanceStatus.BOOTING, InstanceStatus.REGISTERING, InstanceStatus.READY)
        )

    async def cleanup_stale(self):
        """Clean up instances that have been in REQUESTING/BOOTING too long."""
        now = time.time()
        for inst in list(self.instances.values()):
            if (
                inst.status in (InstanceStatus.REQUESTING, InstanceStatus.BOOTING)
                and now - inst.created_at > 300
            ):
                logger.warning(
                    f"Instance {inst.id} stuck in {inst.status.value} for 5+ minutes, "
                    f"terminating"
                )
                await self._terminate_instance(inst)


# Module-level singleton
_provisioner: Optional[CloudProvisioner] = None


def get_cloud_provisioner() -> CloudProvisioner:
    global _provisioner
    if _provisioner is None:
        _provisioner = CloudProvisioner()
    return _provisioner
