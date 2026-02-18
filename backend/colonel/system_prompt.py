"""
Build the system prompt for The Colonel based on config and live server context.
"""

import logging
import platform
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

import psutil

from colonel.models import ColonelConfig

logger = logging.getLogger("colonel.system_prompt")


def _get_server_context() -> str:
    """Gather live server metrics for the system prompt."""
    try:
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        lines = [
            f"Hostname: {platform.node()}",
            f"OS: {platform.system()} {platform.release()}",
            f"CPU: {psutil.cpu_count()} cores, {cpu_pct:.1f}% used",
            f"RAM: {mem.total / (1024**3):.1f} GB total, {mem.percent:.1f}% used ({mem.available / (1024**3):.1f} GB free)",
            f"Disk: {disk.total / (1024**3):.1f} GB total, {disk.percent:.1f}% used ({disk.free / (1024**3):.1f} GB free)",
            f"Uptime: {_format_uptime()}",
        ]

        # GPU info via nvidia-smi (best effort)
        gpu_info = _get_gpu_info()
        if gpu_info:
            lines.append(f"GPUs: {gpu_info}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Error gathering server context: {e}")
        return f"Hostname: {platform.node()}\n(Detailed metrics unavailable)"


def _format_uptime() -> str:
    """Format system uptime."""
    try:
        boot = psutil.boot_time()
        delta = datetime.now().timestamp() - boot
        days = int(delta // 86400)
        hours = int((delta % 86400) // 3600)
        return f"{days}d {hours}h"
    except Exception:
        return "unknown"


def _get_gpu_info() -> Optional[str]:
    """Get GPU info from nvidia-smi (best effort)."""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append(f"{parts[0]} ({parts[2]}MB/{parts[1]}MB, {parts[3]}°C)")
            return "; ".join(gpus) if gpus else None
    except Exception:
        pass
    return None


def _get_docker_context() -> str:
    """Get running Docker containers summary."""
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list()
        if not containers:
            return "No running containers"
        lines = []
        for c in sorted(containers, key=lambda x: x.name):
            status = c.status
            lines.append(f"  - {c.name} ({status})")
        return f"{len(containers)} running containers:\n" + "\n".join(lines)
    except Exception as e:
        logger.warning(f"Error getting Docker context: {e}")
        return "Docker context unavailable"


def _personality_instruction(config: ColonelConfig) -> str:
    """Generate personality instruction from config."""
    p = config.personality
    style_parts = []

    if p.formality >= 7:
        style_parts.append("Use formal, professional language")
    elif p.formality <= 3:
        style_parts.append("Use casual, conversational language")

    if p.verbosity >= 7:
        style_parts.append("provide detailed explanations")
    elif p.verbosity <= 3:
        style_parts.append("be concise and brief")

    if p.humor >= 7:
        style_parts.append("use wit and dry humor when appropriate")
    elif p.humor <= 3:
        style_parts.append("stay serious and factual")

    if not style_parts:
        return "Communicate in a balanced professional tone."

    return ". ".join(style_parts) + "."


def build_system_prompt(
    config: ColonelConfig,
    memories: Optional[List[str]] = None,
    graph_context: Optional[str] = None,
    skill_descriptions: Optional[str] = None,
    write_enabled: bool = False,
) -> str:
    """Build the full system prompt for the LLM."""

    server_ctx = _get_server_context()
    docker_ctx = _get_docker_context()
    personality = _personality_instruction(config)
    now = datetime.utcnow().isoformat()

    prompt_parts = [
        f"You are {config.name}, The Colonel — an AI command agent managing the server \"{config.server_name}\".",
        f"Your mission focus is: {config.mission}.",
        f"Current time: {now} UTC.",
        "",
        f"## Communication Style",
        personality,
        "",
        f"## Server Status",
        server_ctx,
        "",
        f"## Docker Environment",
        docker_ctx,
    ]

    if skill_descriptions:
        prompt_parts.extend([
            "",
            "## Available Skills",
            "You have tools available. Use them to answer questions about the server, containers, and services.",
            "When the user asks about system status, containers, logs, etc., call the appropriate tool rather than guessing.",
            skill_descriptions,
        ])

    if write_enabled:
        prompt_parts.extend([
            "",
            "## Capabilities",
            f"You are powered by {config.model}, a write-capable model with FULL system access.",
            "You can:",
            "- Execute any bash command (within safety limits)",
            "- Start, stop, restart Docker containers (user will be asked to confirm)",
            "- Run INSERT, UPDATE, DELETE SQL queries (user will be asked to confirm)",
            "- Modify files, settings, and configurations",
            "- Manage services, users, and deployments",
            "",
            "## Safety Rules",
            "- Destructive commands (rm -rf /, DROP DATABASE, shutdown, etc.) are always blocked",
            "- NEVER expose secrets, API keys, passwords, or tokens in your responses",
            "- ALWAYS sanitize command output to redact sensitive values",
            "- For write operations, explain what you'll do and why — the user will be asked to confirm",
            "- When showing logs, omit lines containing passwords or tokens",
        ])
    else:
        prompt_parts.extend([
            "",
            "## Safety Rules",
            "- NEVER execute destructive commands (rm -rf /, drop database, etc.)",
            "- NEVER expose secrets, API keys, passwords, or tokens in your responses",
            "- ALWAYS sanitize command output to redact sensitive values",
            "- Do not modify Docker compose files or configuration files directly",
            "- Prefer read-only operations (inspect, logs, stats) over write operations (restart, stop)",
            "- SQL queries are limited to SELECT only",
            "- When showing logs, omit lines containing passwords or tokens",
        ])

    if memories:
        prompt_parts.extend([
            "",
            "## Relevant Memories",
            "These are facts you've previously remembered about this server and user:",
        ])
        for mem in memories:
            prompt_parts.append(f"- {mem}")

    if graph_context:
        prompt_parts.extend([
            "",
            "## Server Knowledge Graph",
            graph_context,
        ])

    return "\n".join(prompt_parts)
