import pytest

from federation.hardware_detector import HardwareDetector
from federation.inference_router import InferenceRouter
from federation.metering_aggregator import MeteringAggregator
from federation.node_registry import NodeRegistry


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.values = {}
        self.sorted_sets = {}

    async def hset(self, key, mapping=None, *args):
        bucket = self.hashes.setdefault(key, {})
        if mapping:
            bucket.update(mapping)
        elif len(args) == 2:
            bucket[args[0]] = args[1]

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def set(self, key, value, ex=None):
        self.values[key] = value

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.hashes.pop(key, None)
        self.values.pop(key, None)

    async def zadd(self, key, mapping):
        bucket = self.sorted_sets.setdefault(key, {})
        bucket.update(mapping)

    async def zrange(self, key, start, end):
        return list(self.sorted_sets.get(key, {}).keys())

    async def zrem(self, key, member):
        self.sorted_sets.get(key, {}).pop(member, None)

    async def scan_iter(self, match=None):
        prefix = (match or "").replace("*", "")
        for key in list(self.hashes.keys()):
            if key.startswith(prefix):
                yield key


@pytest.mark.asyncio
async def test_registry_registers_nodes_and_services():
    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)

    result = await registry.register_node(
        {
            "node_id": "local-1",
            "display_name": "Local Node",
            "endpoint_url": "https://local.example.com",
            "roles": ["gateway", "inference"],
            "hardware_profile": {"gpus": []},
            "services": [
                {
                    "service_type": "llm",
                    "models": ["qwen"],
                    "endpoint_path": "/v1/chat/completions",
                    "status": "running",
                    "capabilities": {"total_vram_mb": 0},
                    "avg_latency_ms": 120,
                    "cost_usd": 0.0,
                }
            ],
        }
    )

    assert result["node_id"] == "local-1"
    nodes = await registry.get_nodes()
    assert len(nodes) == 1
    assert nodes[0]["status"] == "online"

    catalog = await registry.get_service_catalog("llm")
    assert len(catalog) == 1
    assert catalog[0]["node_id"] == "local-1"


@pytest.mark.asyncio
async def test_inference_router_prefers_local_then_remote_then_cloud():
    registry = NodeRegistry(redis_client=FakeRedis(), db_pool=None)
    await registry.register_node(
        {
            "node_id": "local-node",
            "display_name": "Local",
            "endpoint_url": "https://local.example.com",
            "services": [
                {
                    "service_type": "llm",
                    "models": ["qwen-local"],
                    "endpoint_path": "/llm",
                    "status": "running",
                    "capabilities": {"total_vram_mb": 8192},
                    "avg_latency_ms": 80,
                    "cost_usd": 0.0,
                }
            ],
        }
    )
    await registry.register_node(
        {
            "node_id": "remote-node",
            "display_name": "Remote",
            "endpoint_url": "https://remote.example.com",
            "services": [
                {
                    "service_type": "llm",
                    "models": ["qwen-remote"],
                    "endpoint_path": "/llm",
                    "status": "running",
                    "capabilities": {"total_vram_mb": 24576},
                    "avg_latency_ms": 220,
                    "cost_usd": 0.02,
                }
            ],
        }
    )

    router = InferenceRouter(registry, local_node_id="local-node")
    local = await router.route({"service_type": "llm", "model": "qwen-local"})
    assert local["route_type"] == "local"

    remote = await router.route({"service_type": "llm", "model": "qwen-remote"})
    assert remote["route_type"] == "federated"
    assert remote["target_node_id"] == "remote-node"

    cloud = await router.route({"service_type": "tts", "model": "missing"})
    assert cloud["route_type"] == "cloud"


def test_hardware_detector_builds_default_inventory():
    detector = HardwareDetector()
    profile = {
        "cpu": {"physical_cores": 8, "logical_cores": 16, "usage_percent": 10},
        "memory": {"total_gb": 64, "available_gb": 32},
        "gpus": [{"memory_total_mb": 16384, "memory_free_mb": 12000}],
    }
    services = detector.build_service_inventory(profile)
    service_types = {service["service_type"] for service in services}
    assert {"llm", "embeddings", "reranker", "tts", "stt", "image_gen", "music_gen"} <= service_types


@pytest.mark.asyncio
async def test_metering_summary_without_db_is_empty():
    aggregator = MeteringAggregator(db_pool=None)
    summary = await aggregator.summarize_usage(hours=12)
    assert summary["window_hours"] == 12
    assert summary["total_requests"] == 0
