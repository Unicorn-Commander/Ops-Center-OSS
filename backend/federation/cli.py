#!/usr/bin/env python3
"""
Federation CLI - Headless node registration and management.

Standalone CLI for registering a node with the federation, checking status,
discovering local services, and sending heartbeats -- all without needing
the full Ops-Center stack running.

Usage:
    python -m federation.cli register --peer https://peer.example.com --key sk-xxx --name "My Server"
    python -m federation.cli status
    python -m federation.cli services
    python -m federation.cli heartbeat --peer https://peer.example.com
    python -m federation.cli deregister --peer https://peer.example.com
    python -m federation.cli hardware
"""


import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
from typing import Any, Dict, List, Optional

import httpx
import psutil

# ---------------------------------------------------------------------------
# Local service definitions (mirrors node_agent.LOCAL_SERVICES)
# ---------------------------------------------------------------------------

LOCAL_SERVICES = [
    ("llama-router",        8085, "llm",        "/health", "/v1/models"),
    ("whisperx",            9000, "stt",        "/health", None),
    ("kokoro-tts",          8880, "tts",        "/health", None),
    ("infinity-embeddings", 8082, "embeddings", "/health", None),
    ("infinity-reranker",   8083, "reranker",   "/health", None),
    ("artwork-studio",      8095, "image_gen",  "/health", None),
    ("majiks-studio",       8091, "music_gen",  "/health", None),
    ("granite-proxy",       8089, "llm",        "/health", None),
]


# ---------------------------------------------------------------------------
# Hardware detection (synchronous, adapted from hardware_detector.py)
# ---------------------------------------------------------------------------

def detect_hardware() -> Dict[str, Any]:
    """Detect local hardware: CPU, memory, GPUs."""
    profile: Dict[str, Any] = {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False) or 0,
            "logical_cores": psutil.cpu_count(logical=True) or 0,
            "usage_percent": psutil.cpu_percent(interval=0.3),
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
        },
        "gpus": _detect_gpus(),
        "accelerators": [],
    }
    return profile


def _detect_gpus() -> List[Dict[str, Any]]:
    """Detect NVIDIA GPUs via nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return []
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []

    if result.returncode != 0:
        return []

    gpus = []
    for line in result.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        total_mb = int(parts[2])
        free_mb = int(parts[3])
        gpus.append({
            "index": int(parts[0]),
            "name": parts[1],
            "memory_total_mb": total_mb,
            "memory_free_mb": free_mb,
            "memory_used_mb": total_mb - free_mb,
            "utilization_percent": int(parts[4]),
        })
    return gpus


# ---------------------------------------------------------------------------
# Service discovery (synchronous)
# ---------------------------------------------------------------------------

def discover_services() -> List[Dict[str, Any]]:
    """Check local service health endpoints synchronously."""
    services: List[Dict[str, Any]] = []
    for name, port, svc_type, health_path, models_path in LOCAL_SERVICES:
        svc = _check_service(name, port, svc_type, health_path, models_path)
        if svc is not None:
            services.append(svc)
    return services


def _check_service(
    name: str,
    port: int,
    service_type: str,
    health_path: str,
    models_path: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Check a single local service via its health endpoint."""
    url = f"http://localhost:{port}{health_path}"
    try:
        resp = httpx.get(url, timeout=3.0)
        if resp.status_code >= 400:
            return None
    except Exception:
        return None

    models: List[str] = []
    if models_path:
        models = _fetch_models(port, models_path)

    return {
        "service_type": service_type,
        "name": name,
        "port": port,
        "models": models,
        "status": "running",
    }


def _fetch_models(port: int, models_path: str) -> List[str]:
    """Fetch model list from an OpenAI-compatible /v1/models endpoint."""
    url = f"http://localhost:{port}{models_path}"
    try:
        resp = httpx.get(url, timeout=5.0)
        if resp.status_code >= 400:
            return []
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return [m.get("id", "") for m in data["data"] if m.get("id")]
        if isinstance(data, list):
            return [str(m) for m in data]
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# Node config helpers
# ---------------------------------------------------------------------------

def _node_id() -> str:
    hostname = socket.gethostname().split(".")[0]
    return os.getenv("FEDERATION_NODE_ID", f"uc-{hostname}")


def _node_name() -> str:
    return os.getenv("FEDERATION_NODE_NAME", socket.gethostname())


def _endpoint_url() -> str:
    return os.getenv("FEDERATION_ENDPOINT_URL", "http://localhost:8084")


def _auth_token() -> Optional[str]:
    return os.getenv("FEDERATION_KEY") or os.getenv("FEDERATION_SHARED_SECRET")


def _auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Build auth headers — uses per-node signed JWTs when available,
    falls back to raw Bearer token for backward compatibility."""
    try:
        from federation.auth import get_federation_auth

        fed_auth = get_federation_auth()
        if fed_auth.shared_key or fed_auth.auth_mode == "node_keys":
            return fed_auth.get_auth_headers()
    except Exception:
        pass
    # Fallback: raw shared key (backward compatible)
    key = token or _auth_token()
    if key:
        return {"Authorization": f"Bearer {key}"}
    return {}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_register(args: argparse.Namespace) -> int:
    """Register this node with a peer."""
    peer = args.peer.rstrip("/")
    token = args.key or _auth_token()
    node_id = args.node_id or _node_id()
    name = args.name or _node_name()
    url = args.url or _endpoint_url()
    region = args.region or os.getenv("FEDERATION_REGION")
    roles_str = args.roles or os.getenv("FEDERATION_ROLES", "gateway,inference")
    roles = [r.strip() for r in roles_str.split(",") if r.strip()]

    print(f"Detecting hardware...")
    hw = detect_hardware()

    print(f"Discovering local services...")
    services = discover_services()

    payload = {
        "node_id": node_id,
        "display_name": name,
        "endpoint_url": url,
        "auth_method": "jwt",
        "hardware_profile": hw,
        "roles": roles,
        "region": region,
        "services": services,
        "is_self": True,
    }

    register_url = f"{peer}/api/v1/federation/register"
    print(f"Registering with {peer}...")

    try:
        resp = httpx.post(
            register_url,
            json=payload,
            headers=_auth_headers(token),
            timeout=20.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"Registration failed: HTTP {exc.response.status_code}")
        print(f"  Response: {exc.response.text[:500]}")
        return 1
    except Exception as exc:
        print(f"Registration failed: {exc}")
        return 1

    print(f"Registered successfully.")
    print(f"  Node ID:  {node_id}")
    print(f"  Name:     {name}")
    print(f"  Endpoint: {url}")
    print(f"  Region:   {region or '(not set)'}")
    print(f"  Roles:    {', '.join(roles)}")
    print(f"  GPUs:     {len(hw.get('gpus', []))}")
    print(f"  Services: {len(services)}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show current node configuration from env vars."""
    node_id = _node_id()
    name = _node_name()
    url = _endpoint_url()
    token = _auth_token()
    region = os.getenv("FEDERATION_REGION", "(not set)")
    roles = os.getenv("FEDERATION_ROLES", "gateway,inference")
    peers = os.getenv("FEDERATION_PEERS", "")
    interval = os.getenv("FEDERATION_HEARTBEAT_INTERVAL", "30")

    print("Federation Node Status")
    print("=" * 40)
    print(f"  Node ID:            {node_id}")
    print(f"  Display Name:       {name}")
    print(f"  Endpoint URL:       {url}")
    print(f"  Region:             {region}")
    print(f"  Roles:              {roles}")
    print(f"  Auth Token:         {'***' + token[-4:] if token and len(token) > 4 else '(not set)'}")
    print(f"  Heartbeat Interval: {interval}s")
    if peers:
        print(f"  Peers:")
        for p in peers.split(","):
            p = p.strip()
            if p:
                print(f"    - {p}")
    else:
        print(f"  Peers:              (none configured)")
    return 0


def cmd_services(args: argparse.Namespace) -> int:
    """Discover and list locally running services."""
    print("Discovering local services...")
    services = discover_services()

    if not services:
        print("No services detected.")
        return 0

    print(f"\nFound {len(services)} service(s):\n")
    for svc in services:
        models_str = ""
        if svc.get("models"):
            models_str = f"  models: {', '.join(svc['models'])}"
        print(f"  [{svc['status'].upper():>7}]  {svc['name']:<25} port {svc['port']:<6} type={svc['service_type']}")
        if models_str:
            print(f"           {models_str}")
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    """Send a single heartbeat to a peer."""
    peer = args.peer.rstrip("/")
    token = args.key or _auth_token()
    node_id = args.node_id or _node_id()

    hw = detect_hardware()
    services = discover_services()

    cpu = hw.get("cpu", {})
    mem = hw.get("memory", {})
    gpus = hw.get("gpus", [])
    gpu_load = [
        {
            "index": g.get("index"),
            "name": g.get("name"),
            "utilization_percent": g.get("utilization_percent", 0),
            "memory_used_mb": g.get("memory_used_mb", 0),
            "memory_total_mb": g.get("memory_total_mb", 0),
            "memory_free_mb": g.get("memory_free_mb", 0),
        }
        for g in gpus
    ]

    payload = {
        "node_id": node_id,
        "load": {
            "cpu_percent": cpu.get("usage_percent", 0),
            "memory_total_gb": mem.get("total_gb", 0),
            "memory_available_gb": mem.get("available_gb", 0),
            "gpu_load": gpu_load,
        },
        "hardware_profile": hw,
        "services": services,
    }

    heartbeat_url = f"{peer}/api/v1/federation/heartbeat"
    print(f"Sending heartbeat to {peer}...")

    try:
        resp = httpx.post(
            heartbeat_url,
            json=payload,
            headers=_auth_headers(token),
            timeout=20.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"Heartbeat failed: HTTP {exc.response.status_code}")
        return 1
    except Exception as exc:
        print(f"Heartbeat failed: {exc}")
        return 1

    print(f"Heartbeat sent successfully.")
    print(f"  CPU:      {cpu.get('usage_percent', 0):.1f}%")
    print(f"  Memory:   {mem.get('available_gb', 0):.1f} / {mem.get('total_gb', 0):.1f} GB available")
    print(f"  GPUs:     {len(gpus)}")
    print(f"  Services: {len(services)}")
    return 0


def cmd_deregister(args: argparse.Namespace) -> int:
    """Deregister this node from a peer."""
    peer = args.peer.rstrip("/")
    token = args.key or _auth_token()
    node_id = args.node_id or _node_id()

    deregister_url = f"{peer}/api/v1/federation/deregister"
    print(f"Deregistering from {peer}...")

    try:
        resp = httpx.post(
            deregister_url,
            json={"node_id": node_id},
            headers=_auth_headers(token),
            timeout=10.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"Deregistration failed: HTTP {exc.response.status_code}")
        return 1
    except Exception as exc:
        print(f"Deregistration failed: {exc}")
        return 1

    print(f"Deregistered successfully (node_id={node_id}).")
    return 0


def cmd_hardware(args: argparse.Namespace) -> int:
    """Detect and display local hardware."""
    print("Detecting hardware...\n")
    hw = detect_hardware()

    print(f"Hostname:  {hw['hostname']}")
    print(f"Platform:  {hw['platform']}")

    cpu = hw["cpu"]
    print(f"\nCPU:")
    print(f"  Physical cores: {cpu['physical_cores']}")
    print(f"  Logical cores:  {cpu['logical_cores']}")
    print(f"  Usage:          {cpu['usage_percent']:.1f}%")

    mem = hw["memory"]
    used_gb = mem["total_gb"] - mem["available_gb"]
    print(f"\nMemory:")
    print(f"  Total:     {mem['total_gb']:.1f} GB")
    print(f"  Available: {mem['available_gb']:.1f} GB")
    print(f"  Used:      {used_gb:.1f} GB")

    gpus = hw["gpus"]
    if gpus:
        print(f"\nGPUs ({len(gpus)}):")
        for gpu in gpus:
            used_pct = (gpu["memory_used_mb"] / gpu["memory_total_mb"] * 100) if gpu["memory_total_mb"] > 0 else 0
            print(f"  [{gpu['index']}] {gpu['name']}")
            print(f"      VRAM:        {gpu['memory_used_mb']} / {gpu['memory_total_mb']} MB ({used_pct:.0f}% used)")
            print(f"      Utilization: {gpu['utilization_percent']}%")
    else:
        print("\nGPUs: none detected")

    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="federation-cli",
        description="Federation node CLI for headless registration and management.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- register --
    p_reg = sub.add_parser("register", help="Register this node with a peer")
    p_reg.add_argument("--peer", required=True, help="Peer URL (e.g. https://your-ops-center.example.com)")
    p_reg.add_argument("--key", help="Federation shared secret (or set FEDERATION_KEY)")
    p_reg.add_argument("--name", help="Display name for this node")
    p_reg.add_argument("--url", help="This node's externally reachable URL")
    p_reg.add_argument("--region", help="Geographic region identifier")
    p_reg.add_argument("--roles", help="Comma-separated roles (default: gateway,inference)")
    p_reg.add_argument("--node-id", help="Unique node identifier (default: auto-generated)")

    # -- status --
    sub.add_parser("status", help="Show current node configuration")

    # -- services --
    sub.add_parser("services", help="Discover locally running services")

    # -- heartbeat --
    p_hb = sub.add_parser("heartbeat", help="Send a single heartbeat to a peer")
    p_hb.add_argument("--peer", required=True, help="Peer URL")
    p_hb.add_argument("--key", help="Federation shared secret")
    p_hb.add_argument("--node-id", help="Node identifier")

    # -- deregister --
    p_dereg = sub.add_parser("deregister", help="Deregister from a peer")
    p_dereg.add_argument("--peer", required=True, help="Peer URL")
    p_dereg.add_argument("--key", help="Federation shared secret")
    p_dereg.add_argument("--node-id", help="Node identifier")

    # -- hardware --
    sub.add_parser("hardware", help="Detect and display local hardware")

    return parser


COMMANDS = {
    "register": cmd_register,
    "status": cmd_status,
    "services": cmd_services,
    "heartbeat": cmd_heartbeat,
    "deregister": cmd_deregister,
    "hardware": cmd_hardware,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
