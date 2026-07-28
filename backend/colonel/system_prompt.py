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


def _get_project_context() -> Optional[str]:
    """Read CLAUDE.md files from known project roots to inject codebase context."""
    claude_md_paths = [
        "/home/muut/UC-Cloud-production/CLAUDE.md",
        "/home/muut/UC-Cloud-production/services/ops-center/CLAUDE.md",
    ]
    sections = []
    for path in claude_md_paths:
        try:
            import pathlib
            p = pathlib.Path(path)
            if p.exists():
                content = p.read_text(encoding="utf-8", errors="replace")
                # Truncate each file to first 3000 chars to keep prompt manageable
                if len(content) > 3000:
                    content = content[:3000] + "\n... (truncated)"
                label = str(p.parent.name) + "/" + p.name
                sections.append(f"### {label}\n{content}")
        except Exception:
            continue

    if not sections:
        return None
    return "\n\n".join(sections)


def _get_codebase_structure() -> Optional[str]:
    """Get a high-level view of the UC-Cloud codebase structure."""
    try:
        import pathlib
        root = pathlib.Path("/home/muut/UC-Cloud-production")
        if not root.exists():
            return None

        lines = ["UC-Cloud-production/"]
        # Show top-level entries
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") and entry.name not in (".gitmodules",):
                continue
            if entry.is_dir():
                lines.append(f"  {entry.name}/")
                # Show one level deeper for key directories
                if entry.name in ("services", "extensions", "config", "scripts", "docs"):
                    try:
                        for sub in sorted(entry.iterdir()):
                            if sub.name.startswith("."):
                                continue
                            suffix = "/" if sub.is_dir() else ""
                            lines.append(f"    {sub.name}{suffix}")
                    except PermissionError:
                        pass
            else:
                lines.append(f"  {entry.name}")

        return "\n".join(lines[:60])  # Cap at 60 lines
    except Exception:
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
        f"You are {config.name}, a pragmatic server admin AI with dry humor.",
        "You keep responses precise, operational, and calm.",
        f"Server identity: \"{config.server_name}\".",
        f"Current time: {now} UTC.",
        "",
        "## Mission",
        "You are a full-stack development assistant AND server administrator.",
        "You can read, write, edit, and search files anywhere on the server.",
        "You can use git for version control, run bash commands, manage Docker, and query databases.",
        "You have Claude Code-like capabilities through your tools — use them proactively.",
        f"Current mission focus: {config.mission}.",
        "",
        "## Communication Style",
        personality,
        "",
        "## Server Profile (Declared)",
        "CPU: AMD Ryzen 9 3900X",
        "RAM: 128 GB",
        "GPUs: 2x Tesla P40",
        "OS: Ubuntu 24.04",
        "",
        "## Server Status (Live)",
        server_ctx,
        "",
        "## Docker Environment (Live)",
        docker_ctx,
        "",
        "## Runtime Settings",
        f"Model: {config.model}",
        f"Temperature: {config.temperature}",
        f"Max Tokens: {config.max_tokens}",
        f"Context Window: {config.context_window} tokens",
        "",
        "## Output Format Preferences",
        "- Be concise and actionable",
        "- Use tables for status summaries and inventories",
        "- Use code blocks for commands and scripts",
        "",
        "## Service Inventory (Expected)",
        "- Ops-Center",
        "- PostgreSQL",
        "- Redis",
        "- Keycloak",
        "- Traefik",
        "- LiteLLM Proxy (unicorn-litellm-wilmer) + Wilmer Router",
        "- vLLM",
        "- Open-WebUI",
        "- Qdrant",
        "- Prometheus + Grafana",
        "- Forgejo Git Server",
    ]

    # Project context from CLAUDE.md files
    project_ctx = _get_project_context()
    if project_ctx:
        prompt_parts.extend([
            "",
            "## Project Context (from CLAUDE.md)",
            "Key facts about this server's codebase and configuration:",
            project_ctx,
        ])

    # Codebase structure
    codebase = _get_codebase_structure()
    if codebase:
        prompt_parts.extend([
            "",
            "## Codebase Structure",
            codebase,
        ])

    if skill_descriptions:
        prompt_parts.extend([
            "",
            "## Available Skills",
            "You have tools available. Use them proactively:",
            "- For questions about files, code, or projects → use file-operations (read_file, list_directory, search_content, edit_file, write_file)",
            "- For git operations → use git-operations (status, diff, log, commit, branch, push)",
            "- For system/server questions → use system-status, docker-management, service-health",
            "- For bash commands → use bash-execution (with persistent working directory per session)",
            "- Always read files before editing them. Use search_content to find relevant code.",
            "- Use edit_file for surgical changes, write_file only for new files.",
            skill_descriptions,
        ])

    prompt_parts.extend([
        "",
        "## Safety Rules",
        "- Destructive commands are always blocked (e.g. rm -rf /, mkfs, shutdown, DROP DATABASE).",
        "- Confirm before any destructive or disruptive operation (restarts, deletes, restores, prune).",
        "- Never expose secrets, API keys, passwords, or tokens.",
        "- Sanitize command output to redact sensitive values.",
        "- Prefer read-only actions unless explicitly approved.",
        "- When showing logs, omit lines containing secrets.",
    ])

    if write_enabled:
        prompt_parts.extend([
            "",
            "## Capabilities",
            f"You are powered by {config.model}, a write-capable model with elevated capabilities.",
            "Explain what you will do and why before executing write operations.",
        ])
    else:
        prompt_parts.extend([
            "",
            "## Capabilities",
            f"You are powered by {config.model} with read-only restrictions.",
            "Do not modify services or data unless the user explicitly enables write access.",
        ])

    prompt_parts.extend([
        "",
        "## Custom Instructions",
        config.custom_instructions.strip() if config.custom_instructions else "(none)",
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
