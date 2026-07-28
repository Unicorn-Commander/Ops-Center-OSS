import importlib.util
import io
import json
import os
import sys
import types
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


BACKEND_DIR = Path("/home/muut/UC-Cloud-production/services/ops-center/backend")


def load_module(module_name: str, file_path: Path, stubs: dict | None = None):
    original = {}
    for name, module in (stubs or {}).items():
        original[name] = sys.modules.get(name)
        sys.modules[name] = module

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        for name in (stubs or {}):
            if original[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original[name]


class FakePool:
    def __init__(self):
        self.config = None
        self.peers = []
        self.peer_counter = 0

    async def fetchrow(self, query, *args):
        if "SELECT * FROM federation_config LIMIT 1" in query:
            return self.config
        if "SELECT id FROM federation_configured_peers WHERE peer_url" in query:
            peer_url = args[0]
            return next(({"id": p["id"]} for p in self.peers if p["peer_url"] == peer_url), None)
        if "INSERT INTO federation_configured_peers" in query:
            self.peer_counter += 1
            peer = {
                "id": f"peer-{self.peer_counter}",
                "peer_url": args[0],
                "display_name": args[1],
                "federation_key_override": args[2],
                "trust_level": args[3],
                "auto_connect": args[4],
                "last_test_at": args[5],
                "last_test_result": args[6],
                "created_at": args[5],
                "updated_at": args[5],
            }
            self.peers.append(peer)
            return peer
        if "SELECT * FROM federation_configured_peers WHERE id" in query:
            peer_id = args[0]
            return next((peer for peer in self.peers if peer["id"] == peer_id), None)
        return None

    async def fetch(self, query, *args):
        if "SELECT * FROM federation_configured_peers ORDER BY created_at" in query:
            return list(self.peers)
        return []

    async def execute(self, query, *args):
        if "INSERT INTO federation_config (" in query:
            self.config = {
                "id": "cfg-1",
                "enabled": args[0],
                "node_id": args[1],
                "display_name": args[2],
                "endpoint_url": args[3],
                "region": args[4],
                "roles": args[5],
                "is_billing_node": args[6],
                "routing_priority": args[7],
                "branding": args[8],
                "heartbeat_interval": args[9],
                "auto_discover_services": args[10],
                "advertised_services": {},
                "federation_key_hash": None,
                "federation_key_prefix": None,
            }
            return "INSERT 0 1"
        if "UPDATE federation_config SET" in query and self.config:
            if "federation_key_hash" in query:
                self.config["federation_key_hash"] = args[0]
                self.config["federation_key_prefix"] = args[1]
                return "UPDATE 1"

            if "advertised_services" in query and "WHERE id" in query:
                self.config["advertised_services"] = args[0]
                return "UPDATE 1"

            keys = [
                "enabled",
                "node_id",
                "display_name",
                "endpoint_url",
                "region",
                "is_billing_node",
                "routing_priority",
                "roles",
                "branding",
                "heartbeat_interval",
                "auto_discover_services",
            ]
            values = list(args[:-1])
            for key, value in zip(keys, values):
                if value is not None:
                    self.config[key] = value
            return "UPDATE 1"
        if "INSERT INTO federation_config (federation_key_hash, federation_key_prefix)" in query:
            self.config = {
                "id": "cfg-1",
                "enabled": False,
                "node_id": None,
                "display_name": None,
                "endpoint_url": None,
                "region": None,
                "roles": '["inference"]',
                "is_billing_node": False,
                "routing_priority": "cost",
                "branding": "{}",
                "heartbeat_interval": 30,
                "auto_discover_services": True,
                "advertised_services": {},
                "federation_key_hash": args[0],
                "federation_key_prefix": args[1],
            }
            return "INSERT 0 1"
        if "DELETE FROM federation_configured_peers WHERE id" in query:
            peer_id = args[0]
            before = len(self.peers)
            self.peers = [peer for peer in self.peers if peer["id"] != peer_id]
            return "DELETE 1" if len(self.peers) != before else "DELETE 0"
        if "UPDATE federation_configured_peers" in query:
            peer_id = args[-1]
            for peer in self.peers:
                if peer["id"] == peer_id:
                    peer["last_test_at"] = args[0]
                    peer["last_test_result"] = args[1]
                    peer["updated_at"] = args[2]
                    return "UPDATE 1"
        return "OK"


@pytest.fixture
def federation_settings_module():
    admin_stub = types.ModuleType("admin_subscriptions_api")

    async def require_admin():
        return {"email": "admin@example.com", "is_admin": True}

    admin_stub.require_admin = require_admin
    asyncpg_stub = types.ModuleType("asyncpg")
    asyncpg_stub.Pool = object
    asyncpg_stub.Record = dict
    return load_module(
        "test_federation_settings_api",
        BACKEND_DIR / "federation_settings_api.py",
        stubs={
            "admin_subscriptions_api": admin_stub,
            "asyncpg": asyncpg_stub,
        },
    )


@pytest.fixture
def federation_app(federation_settings_module):
    pool = FakePool()
    app = FastAPI()
    app.state.db_pool = pool
    app.include_router(federation_settings_module.router)
    return app, pool, federation_settings_module


def test_get_settings_returns_defaults_when_db_missing(federation_app, monkeypatch):
    app, _, _ = federation_app
    monkeypatch.setenv("FEDERATION_ENABLED", "true")
    monkeypatch.setenv("FEDERATION_HEARTBEAT_INTERVAL", "45")
    client = TestClient(app)

    response = client.get("/api/v1/admin/federation/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["heartbeat_interval"] == 45
    assert body["identity"] is None


def test_put_settings_persists_identity_and_branding(federation_app):
    app, pool, _ = federation_app
    client = TestClient(app)

    payload = {
        "enabled": True,
        "identity": {
            "node_id": "ops-east",
            "display_name": "Ops East",
            "endpoint_url": "https://east.example.com",
            "region": "us-east",
            "roles": ["gateway", "inference"],
            "is_billing_node": True,
            "routing_priority": "latency",
        },
        "branding": {
            "theme_id": "sunrise",
            "company_name": "Magic Unicorn",
            "accent_color": "#ffaa00",
        },
        "heartbeat_interval": 60,
        "auto_discover_services": False,
    }
    response = client.put("/api/v1/admin/federation/settings", json=payload)
    assert response.status_code == 200
    assert pool.config["node_id"] == "ops-east"
    assert json.loads(pool.config["branding"])["theme_id"] == "sunrise"


def test_rotate_key_generates_and_returns_once(federation_app):
    app, pool, _ = federation_app
    client = TestClient(app)

    response = client.post("/api/v1/admin/federation/key/rotate")
    assert response.status_code == 200
    body = response.json()
    assert body["federation_key"].startswith("fk-")
    assert body["federation_key_preview"].startswith("fk-")
    assert pool.config["federation_key_hash"] != body["federation_key"]


def test_add_and_remove_peer_with_connectivity_test(federation_app):
    app, pool, module = federation_app
    client = TestClient(app)

    with patch.object(module, "_test_peer_connectivity", AsyncMock(return_value={
        "reachable": True,
        "latency_ms": 22,
        "node_info": {"node_id": "peer-west"},
        "error": None,
    })):
        create_response = client.post(
            "/api/v1/admin/federation/peers",
            json={
                "peer_url": "https://peer.example.com",
                "display_name": "Peer West",
                "federation_key": "secret",
                "trust_level": "full",
                "auto_connect": True,
            },
        )
        assert create_response.status_code == 201
        peer_id = create_response.json()["id"]
        assert len(pool.peers) == 1

        delete_response = client.delete(f"/api/v1/admin/federation/peers/{peer_id}")
        assert delete_response.status_code == 204
        assert pool.peers == []


def test_test_peer_returns_latency_and_node_info(federation_app):
    app, pool, module = federation_app
    client = TestClient(app)
    pool.peers.append({
        "id": "peer-1",
        "peer_url": "https://peer.example.com",
        "display_name": "Peer",
        "federation_key_override": "token",
        "trust_level": "full",
        "auto_connect": True,
        "last_test_at": None,
        "last_test_result": None,
        "created_at": None,
        "updated_at": None,
    })

    with patch.object(module, "_test_peer_connectivity", AsyncMock(return_value={
        "reachable": True,
        "latency_ms": 18,
        "node_info": {"node_id": "peer-1", "display_name": "Peer"},
        "error": None,
    })):
        response = client.post("/api/v1/admin/federation/peers/peer-1/test")
        assert response.status_code == 200
        body = response.json()
        assert body["latency_ms"] == 18
        assert body["node_info"]["node_id"] == "peer-1"
        assert json.loads(pool.peers[0]["last_test_result"])["reachable"] is True


@pytest.fixture
def pipelines_module():
    return load_module("test_federation_pipelines", BACKEND_DIR / "federation" / "pipelines.py")


class RecordingRouter:
    def __init__(self, fail_once_for=None, always_fail_for=None):
        self.calls = []
        self.fail_once_for = set(fail_once_for or [])
        self.always_fail_for = set(always_fail_for or [])

    async def route(self, request):
        name = request["service_type"]
        self.calls.append(name)
        if name in self.always_fail_for:
            raise RuntimeError(f"{name} failed")
        if name in self.fail_once_for:
            self.fail_once_for.remove(name)
            raise RuntimeError(f"{name} retry")
        return {"target": "self", "endpoint_url": "http://localhost", "node_id": "self"}


@pytest.mark.asyncio
async def test_pipeline_variable_resolution_and_dependency_order(pipelines_module):
    step_a = pipelines_module.PipelineStep(
        name="lyrics",
        service_type="llm",
        input_template={"prompt": "Write about {topic}"},
        output_key="lyrics_result",
    )
    step_b = pipelines_module.PipelineStep(
        name="art",
        service_type="image_gen",
        input_template={"prompt": "{topic}"},
        depends_on=["lyrics"],
    )
    execution = pipelines_module.PipelineExecution(
        pipelines_module.Pipeline(name="demo", steps=[step_a, step_b], variables={"topic": "dragons"}),
        RecordingRouter(),
    )
    assert execution._resolve_input(step_a) == {"prompt": "Write about dragons"}
    await execution.execute()
    assert execution.router.calls == ["llm", "image_gen"]


def test_pipeline_parallel_grouping_and_builtin_template(pipelines_module):
    step_a = pipelines_module.PipelineStep(name="music", service_type="music_gen")
    step_b = pipelines_module.PipelineStep(name="art", service_type="image_gen", parallel_with="music")
    execution = pipelines_module.PipelineExecution(
        pipelines_module.Pipeline(name="parallel", steps=[step_a, step_b]),
        RecordingRouter(),
    )
    groups = execution._group_parallel([step_a, step_b])
    assert len(groups) == 1
    assert {step.name for step in groups[0]} == {"music", "art"}

    registry = pipelines_module.PipelineRegistry()
    built_in = registry.get_pipeline("music-production")
    assert built_in is not None
    assert built_in.name == "music-production"
    assert len(built_in.steps) == 3


@pytest.mark.asyncio
async def test_pipeline_failure_skip_stop_and_retry_logic(pipelines_module):
    skip_pipeline = pipelines_module.Pipeline(
        name="skip-pipeline",
        steps=[
            pipelines_module.PipelineStep(name="bad", service_type="llm", on_failure="skip", max_retries=0),
            pipelines_module.PipelineStep(name="good", service_type="tts", depends_on=["bad"]),
        ],
    )
    skip_exec = pipelines_module.PipelineExecution(skip_pipeline, RecordingRouter(always_fail_for={"llm"}))
    skip_result = await skip_exec.execute()
    assert skip_result["status"] == "completed"
    assert skip_result["steps"]["bad"]["status"] == "skipped"
    assert skip_exec.router.calls == ["llm", "tts"]

    stop_pipeline = pipelines_module.Pipeline(
        name="stop-pipeline",
        steps=[pipelines_module.PipelineStep(name="bad", service_type="llm", on_failure="stop", max_retries=0)],
    )
    stop_exec = pipelines_module.PipelineExecution(stop_pipeline, RecordingRouter(always_fail_for={"llm"}))
    stop_result = await stop_exec.execute()
    assert stop_result["status"] == "failed"

    retry_pipeline = pipelines_module.Pipeline(
        name="retry-pipeline",
        steps=[pipelines_module.PipelineStep(name="retry-step", service_type="llm", max_retries=1)],
    )
    retry_router = RecordingRouter(fail_once_for={"llm"})
    retry_exec = pipelines_module.PipelineExecution(retry_pipeline, retry_router)
    retry_result = await retry_exec.execute()
    assert retry_result["status"] == "completed"
    assert retry_router.calls == ["llm", "llm"]


@pytest.fixture
def inference_router_module():
    federation_pkg = types.ModuleType("federation")
    federation_pkg.__path__ = []
    node_registry_stub = types.ModuleType("federation.node_registry")
    node_registry_stub.NodeRegistry = object
    return load_module(
        "test_federation_inference_router",
        BACKEND_DIR / "federation" / "inference_router.py",
        stubs={
            "federation": federation_pkg,
            "federation.node_registry": node_registry_stub,
        },
    )


def test_constraint_routing_filters_and_boosts(inference_router_module):
    router = inference_router_module.InferenceRouter(Mock(), local_node_id="self")
    candidates = [
        {"node_id": "self", "_target": "self", "cost_usd": 0.0, "capabilities": {"total_vram_mb": 4096, "compute_capability": 7.5}},
        {"node_id": "peer-a", "_target": "peer", "cost_usd": 0.5, "capabilities": {"total_vram_mb": 24576, "compute_capability": 8.0}},
        {"node_id": "peer-b", "_target": "peer", "cost_usd": 2.0, "capabilities": {"total_vram_mb": 8192, "compute_capability": 7.0}},
    ]

    assert [c["node_id"] for c in router._apply_constraints(candidates, {"locality": "local_only"})] == ["self"]
    assert [c["node_id"] for c in router._apply_constraints(candidates, {"min_vram_gb": 16})] == ["peer-a"]
    assert [c["node_id"] for c in router._apply_constraints(candidates, {"exclude_nodes": ["peer-a"]})] == ["self", "peer-b"]
    assert [c["node_id"] for c in router._apply_constraints(candidates, {"max_cost_usd": 0.75})] == ["self", "peer-a"]
    assert [c["node_id"] for c in router._apply_constraints(candidates, {"required_gpu": "ampere+"})] == ["peer-a"]

    boosted = router._apply_constraints(candidates, {"preferred_node": "peer-a"})
    peer_a = next(c for c in boosted if c["node_id"] == "peer-a")
    score = router._calculate_routing_score(peer_a, {}, "balanced")
    no_boost = router._calculate_routing_score({**peer_a, "_preferred_boost": 0.0}, {}, "balanced")
    assert score == no_boost + 50.0


@pytest.fixture
def cli_module():
    httpx_stub = types.ModuleType("httpx")
    httpx_stub.get = Mock()
    httpx_stub.post = Mock()
    psutil_stub = types.ModuleType("psutil")
    psutil_stub.cpu_count = lambda logical=False: 16 if logical else 8
    psutil_stub.cpu_percent = lambda interval=0.3: 12.5
    psutil_stub.virtual_memory = lambda: types.SimpleNamespace(total=64 * 1024**3, available=32 * 1024**3)
    return load_module(
        "test_federation_cli",
        BACKEND_DIR / "federation" / "cli.py",
        stubs={"httpx": httpx_stub, "psutil": psutil_stub},
    )


def test_cli_register_sends_correct_payload(cli_module):
    response = Mock()
    response.raise_for_status = Mock()
    cli_module.httpx.post = Mock(return_value=response)
    with patch.object(cli_module, "detect_hardware", return_value={"gpus": [{"name": "RTX"}]}), \
         patch.object(cli_module, "discover_services", return_value=[{"service_type": "llm"}]):
        code = cli_module.cmd_register(Namespace(
            peer="https://peer.example.com",
            key="secret",
            node_id="node-1",
            name="Node One",
            url="https://self.example.com",
            region="us-east",
            roles="gateway,inference",
        ))
    assert code == 0
    sent = cli_module.httpx.post.call_args.kwargs["json"]
    assert sent["node_id"] == "node-1"
    assert sent["services"] == [{"service_type": "llm"}]
    assert sent["hardware_profile"]["gpus"][0]["name"] == "RTX"


def test_cli_services_checks_all_eight_endpoints(cli_module):
    with patch.object(cli_module, "_check_service", side_effect=lambda *args: {"name": args[0], "status": "running", "port": args[1], "service_type": args[2], "models": []}) as check:
        services = cli_module.discover_services()
    assert len(services) == 8
    assert check.call_count == 8


def test_cli_hardware_parses_nvidia_smi_output(cli_module):
    run_result = types.SimpleNamespace(
        returncode=0,
        stdout="0, NVIDIA RTX 5090, 32768, 16384, 42\n",
    )
    with patch.object(cli_module.shutil, "which", return_value="/usr/bin/nvidia-smi"), \
         patch.object(cli_module.subprocess, "run", return_value=run_result):
        hardware = cli_module.detect_hardware()
    assert hardware["gpus"][0]["name"] == "NVIDIA RTX 5090"
    assert hardware["gpus"][0]["memory_used_mb"] == 16384


def test_cli_status_reads_env_vars_correctly(cli_module, monkeypatch):
    monkeypatch.setenv("FEDERATION_NODE_ID", "env-node")
    monkeypatch.setenv("FEDERATION_NODE_NAME", "Env Node")
    monkeypatch.setenv("FEDERATION_ENDPOINT_URL", "https://env.example.com")
    monkeypatch.setenv("FEDERATION_SHARED_SECRET", "supersecret")
    monkeypatch.setenv("FEDERATION_REGION", "eu-west")
    monkeypatch.setenv("FEDERATION_ROLES", "gateway,inference")
    monkeypatch.setenv("FEDERATION_PEERS", "https://peer-a,https://peer-b")
    monkeypatch.setenv("FEDERATION_HEARTBEAT_INTERVAL", "33")

    stream = io.StringIO()
    with redirect_stdout(stream):
        code = cli_module.cmd_status(Namespace())
    output = stream.getvalue()
    assert code == 0
    assert "env-node" in output
    assert "Env Node" in output
    assert "https://peer-a" in output and "https://peer-b" in output
    assert "33s" in output
