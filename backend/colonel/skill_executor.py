"""
Skill Executor - Executes Docker, bash, and system commands.

Each executor function takes parameters and returns a string result.
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict
from pathlib import Path

import docker
import psutil

from colonel.safety import validate_command, sanitize_output, validate_docker_command

logger = logging.getLogger("colonel.skill_executor")

# Docker client (lazy init)
_docker_client = None
OPS_CENTER_DIR = Path(__file__).resolve().parents[2]
OPS_CENTER_BACKUPS = OPS_CENTER_DIR / "backups"


def _get_docker():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


# ─── Docker Management ──────────────────────────────────────────────────

async def docker_list_containers(status: str = "running") -> str:
    """List Docker containers."""
    try:
        client = _get_docker()
        filters = {}
        if status != "all":
            filters["status"] = status

        containers = client.containers.list(all=(status == "all"), filters=filters)
        if not containers:
            return f"No {status} containers found."

        lines = [f"{'NAME':<35} {'STATUS':<20} {'IMAGE':<40}"]
        lines.append("-" * 95)
        for c in sorted(containers, key=lambda x: x.name):
            image = c.image.tags[0] if c.image.tags else c.image.short_id
            lines.append(f"{c.name:<35} {c.status:<20} {image:<40}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing containers: {e}"


async def docker_inspect_container(container_name: str) -> str:
    """Get detailed info about a container."""
    try:
        client = _get_docker()
        c = client.containers.get(container_name)
        info = {
            "name": c.name,
            "id": c.short_id,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            "created": c.attrs.get("Created", ""),
            "ports": c.ports,
            "networks": list(c.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()),
            "labels": {k: v for k, v in c.labels.items() if not k.startswith("com.docker")},
        }
        # Memory/CPU stats
        try:
            stats = c.stats(stream=False)
            mem_usage = stats.get("memory_stats", {}).get("usage", 0)
            mem_limit = stats.get("memory_stats", {}).get("limit", 1)
            info["memory_mb"] = round(mem_usage / (1024 * 1024), 1)
            info["memory_pct"] = round(mem_usage / mem_limit * 100, 1) if mem_limit else 0
        except Exception:
            pass

        return json.dumps(info, indent=2, default=str)
    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except Exception as e:
        return f"Error inspecting container: {e}"


async def docker_container_logs(container_name: str, lines: int = 50, since: str = "") -> str:
    """Get container logs."""
    try:
        client = _get_docker()
        c = client.containers.get(container_name)
        kwargs = {"tail": lines, "timestamps": True}
        if since:
            kwargs["since"] = since

        raw = c.logs(**kwargs)
        output = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        return sanitize_output(output)
    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except Exception as e:
        return f"Error getting logs: {e}"


async def docker_container_stats(container_name: str) -> str:
    """Get real-time container resource usage."""
    try:
        client = _get_docker()
        c = client.containers.get(container_name)
        stats = c.stats(stream=False)

        mem_usage = stats.get("memory_stats", {}).get("usage", 0)
        mem_limit = stats.get("memory_stats", {}).get("limit", 1)

        # CPU calculation
        cpu_delta = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) - \
                    stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
        system_delta = stats.get("cpu_stats", {}).get("system_cpu_usage", 0) - \
                       stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
        cpu_pct = (cpu_delta / system_delta * 100) if system_delta > 0 else 0

        # Network I/O
        net = stats.get("networks", {})
        rx_bytes = sum(v.get("rx_bytes", 0) for v in net.values())
        tx_bytes = sum(v.get("tx_bytes", 0) for v in net.values())

        return (
            f"Container: {container_name}\n"
            f"CPU: {cpu_pct:.1f}%\n"
            f"Memory: {mem_usage / (1024 * 1024):.1f} MB / {mem_limit / (1024 * 1024):.0f} MB ({mem_usage / mem_limit * 100:.1f}%)\n"
            f"Network: RX {rx_bytes / 1024:.1f} KB, TX {tx_bytes / 1024:.1f} KB"
        )
    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except Exception as e:
        return f"Error getting stats: {e}"


async def docker_manage_container(container_name: str, action: str) -> str:
    """Start, stop, restart, or remove a container."""
    allowed, reason = validate_docker_command(container_name, action)
    if not allowed:
        return f"Blocked: {reason}"

    try:
        client = _get_docker()
        c = client.containers.get(container_name)

        if action == "start":
            c.start()
            return f"Container '{container_name}' started."
        elif action == "stop":
            c.stop(timeout=30)
            return f"Container '{container_name}' stopped."
        elif action == "restart":
            c.restart(timeout=30)
            return f"Container '{container_name}' restarted."
        elif action == "kill":
            c.kill()
            return f"Container '{container_name}' killed."
        else:
            return f"Unknown action: {action}"

    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except docker.errors.APIError as e:
        return f"Docker API error: {e}"


# ─── Bash Execution ─────────────────────────────────────────────────────

# ─── Persistent Working Directory ─────────────────────────────────────
# Keyed by session_id → cwd path. Updated when 'cd' is detected in commands.
_session_cwd: Dict[str, str] = {}

DEFAULT_CWD = "/home/muut/UC-Cloud-production"


def get_session_cwd(session_id: str = None) -> str:
    """Get the current working directory for a session."""
    if session_id and session_id in _session_cwd:
        cwd = _session_cwd[session_id]
        # Verify the directory still exists
        if Path(cwd).is_dir():
            return cwd
    return DEFAULT_CWD


def set_session_cwd(session_id: str, cwd: str):
    """Set the working directory for a session."""
    if session_id and Path(cwd).is_dir():
        _session_cwd[session_id] = cwd


async def bash_execute(command: str, timeout: int = 30, session_id: str = None) -> str:
    """Execute a bash command with safety validation and persistent working directory."""
    allowed, reason = validate_command(command)
    if not allowed:
        return f"Blocked: {reason}"

    cwd = get_session_cwd(session_id)

    try:
        # Wrap command to capture the final CWD after execution
        # This allows 'cd' commands to persist across calls
        wrapped = f'cd "{cwd}" 2>/dev/null; {command}; echo "___CWD___:$(pwd)"'

        process = await asyncio.create_subprocess_shell(
            wrapped,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return f"Command timed out after {timeout}s"

        output = stdout.decode("utf-8", errors="replace")

        # Extract and save the final CWD
        if "___CWD___:" in output:
            parts = output.rsplit("___CWD___:", 1)
            output = parts[0]
            new_cwd = parts[1].strip()
            if new_cwd and session_id:
                set_session_cwd(session_id, new_cwd)

        if stderr:
            err = stderr.decode("utf-8", errors="replace")
            if err.strip():
                output += f"\n[STDERR]\n{err}"

        return sanitize_output(output) if output.strip() else "(no output)"

    except Exception as e:
        return f"Error executing command: {e}"


# ─── System Status ──────────────────────────────────────────────────────

async def system_cpu_status() -> str:
    """Get CPU usage details."""
    try:
        cpu_pct = psutil.cpu_percent(interval=0.5, percpu=True)
        avg = sum(cpu_pct) / len(cpu_pct) if cpu_pct else 0
        freq = psutil.cpu_freq()
        load = psutil.getloadavg()

        lines = [
            f"CPU Cores: {psutil.cpu_count()} ({psutil.cpu_count(logical=False)} physical)",
            f"Average Usage: {avg:.1f}%",
            f"Per-Core: {', '.join(f'{p:.0f}%' for p in cpu_pct)}",
            f"Load Average: {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f} (1/5/15 min)",
        ]
        if freq:
            lines.append(f"Frequency: {freq.current:.0f} MHz (max: {freq.max:.0f} MHz)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


async def system_memory_status() -> str:
    """Get memory usage details."""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return (
            f"RAM: {mem.total / (1024**3):.1f} GB total\n"
            f"  Used: {mem.used / (1024**3):.1f} GB ({mem.percent:.1f}%)\n"
            f"  Available: {mem.available / (1024**3):.1f} GB\n"
            f"  Buffers/Cache: {(mem.buffers + mem.cached) / (1024**3):.1f} GB\n"
            f"Swap: {swap.total / (1024**3):.1f} GB total, {swap.used / (1024**3):.1f} GB used ({swap.percent:.1f}%)"
        )
    except Exception as e:
        return f"Error: {e}"


async def system_disk_status() -> str:
    """Get disk usage for all mounted partitions."""
    try:
        lines = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                lines.append(
                    f"{part.mountpoint}: {usage.total / (1024**3):.1f} GB total, "
                    f"{usage.used / (1024**3):.1f} GB used ({usage.percent:.1f}%), "
                    f"{usage.free / (1024**3):.1f} GB free"
                )
            except PermissionError:
                continue
        return "\n".join(lines) if lines else "No disk info available."
    except Exception as e:
        return f"Error: {e}"


async def system_gpu_status() -> str:
    """Get GPU status via nvidia-smi."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
            "--format=csv,noheader",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        output = stdout.decode().strip()
        if not output:
            return "No GPUs detected."

        lines = ["GPU Status:"]
        for i, line in enumerate(output.split("\n")):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                lines.append(
                    f"  GPU {i}: {parts[0]}\n"
                    f"    Memory: {parts[2]} / {parts[1]} ({parts[3]} free)\n"
                    f"    Temp: {parts[4]}°C, Utilization: {parts[5]}"
                )
        return "\n".join(lines)
    except FileNotFoundError:
        return "nvidia-smi not found — no NVIDIA GPUs available."
    except Exception as e:
        return f"Error: {e}"


async def system_top_processes(count: int = 10) -> str:
    """Get top processes by CPU usage."""
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
        top = procs[:count]

        lines = [f"{'PID':<8} {'CPU%':<8} {'MEM%':<8} {'NAME'}"]
        lines.append("-" * 50)
        for p in top:
            lines.append(f"{p['pid']:<8} {(p.get('cpu_percent') or 0):<8.1f} {(p.get('memory_percent') or 0):<8.1f} {p.get('name', '?')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


async def system_full_status() -> str:
    """Get comprehensive system status."""
    parts = []
    parts.append(await system_cpu_status())
    parts.append("")
    parts.append(await system_memory_status())
    parts.append("")
    parts.append(await system_disk_status())
    parts.append("")
    parts.append(await system_gpu_status())
    return "\n".join(parts)


# ─── Service Health ─────────────────────────────────────────────────────

async def service_health_check_all() -> str:
    """Check health of all running containers."""
    try:
        client = _get_docker()
        containers = client.containers.list()

        lines = [f"{'SERVICE':<35} {'STATUS':<12} {'HEALTH'}"]
        lines.append("-" * 65)

        for c in sorted(containers, key=lambda x: x.name):
            health = c.attrs.get("State", {}).get("Health", {}).get("Status", "n/a")
            status_icon = "✓" if c.status == "running" else "✗"
            health_icon = "✓" if health == "healthy" else "?" if health == "n/a" else "✗"
            lines.append(f"{c.name:<35} {status_icon} {c.status:<10} {health_icon} {health}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


async def service_health_check_one(service_name: str) -> str:
    """Check health of a specific service."""
    try:
        client = _get_docker()
        c = client.containers.get(service_name)

        health = c.attrs.get("State", {}).get("Health", {})
        started = c.attrs.get("State", {}).get("StartedAt", "")

        lines = [
            f"Service: {c.name}",
            f"Status: {c.status}",
            f"Health: {health.get('Status', 'n/a')}",
            f"Started: {started}",
        ]

        # Recent health check logs
        if health.get("Log"):
            lines.append("Recent health checks:")
            for log in health["Log"][-3:]:
                exit_code = log.get("ExitCode", "?")
                output = log.get("Output", "").strip()[:100]
                lines.append(f"  Exit {exit_code}: {output}")

        return "\n".join(lines)
    except docker.errors.NotFound:
        return f"Service '{service_name}' not found."
    except Exception as e:
        return f"Error: {e}"


# ─── Log Search ─────────────────────────────────────────────────────────

async def log_search(container_name: str, pattern: str, lines: int = 50) -> str:
    """Search container logs for a pattern."""
    try:
        client = _get_docker()
        c = client.containers.get(container_name)
        raw = c.logs(tail=500, timestamps=True)
        log_text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw

        matching = []
        for line in log_text.split("\n"):
            if pattern.lower() in line.lower():
                matching.append(line)

        if not matching:
            return f"No matches for '{pattern}' in last 500 lines of {container_name}."

        result = matching[-lines:]  # Last N matches
        return sanitize_output("\n".join(result))

    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except Exception as e:
        return f"Error: {e}"


# ─── PostgreSQL Operations ──────────────────────────────────────────────

async def postgresql_list_databases() -> str:
    """List PostgreSQL databases."""
    return await bash_execute(
        "docker exec unicorn-postgresql psql -U unicorn -c '\\l'",
        timeout=10,
    )


async def postgresql_list_tables(database: str = "unicorn_db") -> str:
    """List tables in a database."""
    return await bash_execute(
        f"docker exec unicorn-postgresql psql -U unicorn -d {database} -c '\\dt+'",
        timeout=10,
    )


async def postgresql_query(query: str, database: str = "unicorn_db", write_enabled: bool = False) -> str:
    """Run a SQL query. Write ops (INSERT/UPDATE/DELETE) allowed for write-capable models."""
    q_upper = query.strip().upper()

    # Always allowed
    read_prefixes = ("SELECT", "\\D", "EXPLAIN", "WITH")
    # Allowed only when write-capable
    write_prefixes = ("INSERT", "UPDATE", "DELETE")

    if any(q_upper.startswith(p) for p in read_prefixes):
        pass  # always OK
    elif write_enabled and any(q_upper.startswith(p) for p in write_prefixes):
        pass  # write-capable model — allowed
    else:
        if write_enabled:
            return "Only SELECT, INSERT, UPDATE, DELETE, WITH, \\d, and EXPLAIN are allowed. DROP/ALTER/TRUNCATE are always blocked."
        return "Only SELECT, \\d, and EXPLAIN queries are allowed. (Write operations require a write-capable model.)"

    return await bash_execute(
        f"docker exec unicorn-postgresql psql -U unicorn -d {database} -c \"{query}\"",
        timeout=15,
    )


async def postgresql_stats() -> str:
    """Get PostgreSQL database statistics."""
    return await bash_execute(
        "docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
        "\"SELECT datname, pg_size_pretty(pg_database_size(datname)), numbackends, "
        "xact_commit, xact_rollback FROM pg_stat_database WHERE datname NOT LIKE 'template%' ORDER BY pg_database_size(datname) DESC;\"",
        timeout=10,
    )


# ─── Traefik Management ────────────────────────────────────────────────

async def traefik_list_routers() -> str:
    return await bash_execute("curl -sS http://traefik:8080/api/http/routers", timeout=10)


async def traefik_list_services() -> str:
    return await bash_execute("curl -sS http://traefik:8080/api/http/services", timeout=10)


async def traefik_list_middlewares() -> str:
    return await bash_execute("curl -sS http://traefik:8080/api/http/middlewares", timeout=10)


async def traefik_list_tls_certs() -> str:
    return await bash_execute("curl -sS http://traefik:8080/api/tls/certificates", timeout=10)


async def traefik_restart() -> str:
    return await bash_execute("docker restart traefik", timeout=30)


# ─── Backup Management ────────────────────────────────────────────────

async def backup_trigger(backup_dir: Optional[str] = None, dry_run: bool = False) -> str:
    script = OPS_CENTER_DIR / "scripts" / "automated-backup.sh"
    cmd = f"bash {script}"
    if dry_run:
        cmd += " --dry-run"
    env_parts = []
    if backup_dir:
        env_parts.append(f"BACKUP_DIR={backup_dir}")
    else:
        env_parts.append(f"BACKUP_DIR={OPS_CENTER_BACKUPS}")
    env_parts.append("LOG_FILE=/tmp/uc-cloud-backup.log")
    env_prefix = " ".join(env_parts) + " " if env_parts else ""
    return await bash_execute(env_prefix + cmd, timeout=120)


async def backup_list(backup_dir: Optional[str] = None, limit: int = 10) -> str:
    target_dir = backup_dir or str(OPS_CENTER_BACKUPS)
    cmd = f"ls -1t {target_dir} 2>/dev/null | head -n {int(limit)}"
    return await bash_execute(cmd, timeout=10)


async def backup_restore_database(backup_file: str) -> str:
    cmd = (
        "set -e; "
        f"test -f '{backup_file}'; "
        "SAFETY_BACKUP=/home/muut/backups/database/unicorn_db_before_restore_$(date +%Y%m%d_%H%M%S).sql; "
        "docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db --format=plain --no-owner --no-acl > \"$SAFETY_BACKUP\"; "
        f"cat '{backup_file}' | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db > /dev/null 2>&1; "
        "echo \"Restore complete. Safety backup: $SAFETY_BACKUP\""
    )
    return await bash_execute(cmd, timeout=120)


async def backup_cleanup_old(days: int = 7, keep: int = 3, backup_dir: Optional[str] = None) -> str:
    env_parts = ["LOG_FILE=/tmp/uc-cloud-backup-cleanup.log"]
    if backup_dir:
        env_parts.append(f"BACKUP_DIR={backup_dir}")
    else:
        env_parts.append(f"BACKUP_DIR={OPS_CENTER_BACKUPS}")
    env_prefix = " ".join(env_parts) + " " if env_parts else ""
    script = OPS_CENTER_DIR / "scripts" / "cleanup-old-backups.sh"
    cmd = (
        f"bash {script} "
        f"--days {int(days)} --keep {int(keep)} --force"
    )
    return await bash_execute(env_prefix + cmd, timeout=120)


# ─── GPU Monitoring ───────────────────────────────────────────────────

async def gpu_summary() -> str:
    return await bash_execute(
        "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu "
        "--format=csv,noheader,nounits",
        timeout=10,
    )


async def gpu_vram_usage() -> str:
    return await bash_execute(
        "nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total "
        "--format=csv,noheader,nounits",
        timeout=10,
    )


async def gpu_temperatures() -> str:
    return await bash_execute(
        "nvidia-smi --query-gpu=index,name,temperature.gpu "
        "--format=csv,noheader,nounits",
        timeout=10,
    )


async def gpu_process_list() -> str:
    return await bash_execute(
        "nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory "
        "--format=csv,noheader,nounits",
        timeout=10,
    )


# ─── Network Diagnostics ──────────────────────────────────────────────

async def net_port_check(host: str, port: int, timeout: int = 3) -> str:
    cmd = (
        f"timeout {int(timeout)} bash -c '</dev/tcp/{host}/{int(port)}' "
        "&& echo 'open' || echo 'closed'"
    )
    return await bash_execute(cmd, timeout=10)


async def net_dns_lookup(hostname: str) -> str:
    cmd = f"getent hosts {hostname} || nslookup {hostname}"
    return await bash_execute(cmd, timeout=10)


async def net_list_docker_networks() -> str:
    return await bash_execute("docker network ls", timeout=10)


async def net_inspect_docker_network(network_name: str) -> str:
    return await bash_execute(f"docker network inspect {network_name}", timeout=10)


# ─── Resource Cleanup ────────────────────────────────────────────────

async def cleanup_disk_usage() -> str:
    return await bash_execute("df -h", timeout=10)


async def cleanup_docker_prune(include_volumes: bool = False) -> str:
    cmd = "docker system prune -f"
    if include_volumes:
        cmd += " --volumes"
    return await bash_execute(cmd, timeout=60)


async def cleanup_logs(max_size_mb: int = 50) -> str:
    max_mb = int(max_size_mb)
    cmd = (
        f"find {OPS_CENTER_DIR} -path '*logs*' -type f "
        f"-size +{max_mb}M -print -exec truncate -s 0 {{}} \\;"
    )
    return await bash_execute(cmd, timeout=60)


# ─── LiteLLM Management ──────────────────────────────────────────────

async def litellm_health_check() -> str:
    return await bash_execute("curl -sS http://localhost:4000/health", timeout=10)


async def litellm_list_models() -> str:
    import os
    key = os.getenv("LITELLM_MASTER_KEY", "")
    header = f"-H 'Authorization: Bearer {key}'" if key else ""
    cmd = f"curl -sS {header} http://localhost:4000/v1/models"
    return await bash_execute(cmd, timeout=15)


async def litellm_generate_master_key() -> str:
    import secrets
    key = f"sk-litellm-{secrets.token_hex(24)}"
    return (
        f"Generated key: {key}\n"
        "Next steps: update LITELLM_MASTER_KEY in environment and restart unicorn-litellm-wilmer."
    )


# ─── Keycloak Helper ──────────────────────────────────────────────────

import os
import re as _re
import fnmatch as _fnmatch


# ─── File Operations ─────────────────────────────────────────────────────

# Paths that are always blocked from reading/writing
_BLOCKED_PATH_PATTERNS = [
    "/etc/shadow", "/etc/gshadow", "/etc/sudoers",
    "*.pem", "*.key", "*id_rsa*", "*id_ed25519*",
]
_BLOCKED_PATH_CONTAINS = [
    "/.ssh/", "/acme.json",
]
# Filenames that should never be read/written by the Colonel
_BLOCKED_FILENAMES = [".env", ".env.auth", ".env.billing", ".env.local", ".env.production"]


def _validate_file_path(path: str, for_write: bool = False) -> tuple:
    """Validate a file path for safety. Returns (allowed, reason)."""
    from pathlib import Path as _P
    try:
        resolved = _P(path).resolve()
        path_str = str(resolved)
    except Exception as e:
        return (False, f"Invalid path: {e}")

    # Block path traversal attempts
    if ".." in path:
        return (False, "Path traversal (..) not allowed")

    # Block sensitive files
    for pattern in _BLOCKED_PATH_PATTERNS:
        if _fnmatch.fnmatch(path_str, pattern) or _fnmatch.fnmatch(resolved.name, pattern):
            return (False, f"Access denied: matches blocked pattern")

    for segment in _BLOCKED_PATH_CONTAINS:
        if segment in path_str:
            return (False, f"Access denied: path contains blocked segment")

    if resolved.name in _BLOCKED_FILENAMES:
        return (False, f"Access denied: {resolved.name} files contain secrets")

    # For writes, additional restrictions
    if for_write:
        # Never write to /etc, /boot, /proc, /sys
        system_dirs = ["/etc/", "/boot/", "/proc/", "/sys/", "/dev/"]
        for d in system_dirs:
            if path_str.startswith(d):
                return (False, f"Cannot write to system directory: {d}")

    return (True, None)


async def file_read(path: str, offset: int = 1, limit: int = 200) -> str:
    """Read a file and return its contents with line numbers."""
    allowed, reason = _validate_file_path(path)
    if not allowed:
        return f"Blocked: {reason}"

    from pathlib import Path as _P
    target = _P(path)

    if not target.exists():
        return f"File not found: {path}"
    if target.is_dir():
        return f"Path is a directory: {path}. Use list_directory instead."
    if target.stat().st_size > 2_000_000:  # 2MB limit
        return f"File too large ({target.stat().st_size:,} bytes). Use offset/limit or read sections."

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        total = len(lines)

        # Apply offset (1-based) and limit
        start = max(0, offset - 1)
        end = start + limit
        selected = lines[start:end]

        # Format with line numbers
        numbered = []
        for i, line in enumerate(selected, start=start + 1):
            # Truncate very long lines
            display = line[:500] + "..." if len(line) > 500 else line
            numbered.append(f"{i:>6}\t{display}")

        header = f"File: {path} ({total} lines total)"
        if start > 0 or end < total:
            header += f" [showing lines {start + 1}-{min(end, total)}]"

        return header + "\n" + "\n".join(numbered)
    except Exception as e:
        return f"Error reading {path}: {e}"


async def file_write(path: str, content: str) -> str:
    """Write content to a file."""
    allowed, reason = _validate_file_path(path, for_write=True)
    if not allowed:
        return f"Blocked: {reason}"

    from pathlib import Path as _P
    target = _P(path)

    try:
        # Create parent directories if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content):,} chars to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


async def file_edit(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by exact string replacement."""
    allowed, reason = _validate_file_path(path, for_write=True)
    if not allowed:
        return f"Blocked: {reason}"

    from pathlib import Path as _P
    target = _P(path)

    if not target.exists():
        return f"File not found: {path}"

    try:
        content = target.read_text(encoding="utf-8")
        count = content.count(old_text)

        if count == 0:
            return f"old_text not found in {path}. Make sure the text matches exactly (including whitespace and indentation)."
        if count > 1:
            return f"old_text found {count} times in {path}. Provide more surrounding context to make it unique."

        new_content = content.replace(old_text, new_text, 1)
        target.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {path}. Replaced {len(old_text)} chars with {len(new_text)} chars."
    except Exception as e:
        return f"Error editing {path}: {e}"


async def file_list_directory(path: str, pattern: str = None) -> str:
    """List directory contents or find files matching a glob pattern."""
    from pathlib import Path as _P
    import glob as _glob_mod

    # Check if the path itself is a glob pattern
    if any(c in path for c in ["*", "?", "["]):
        try:
            matches = sorted(_glob_mod.glob(path, recursive=True))
            if not matches:
                return f"No files matching pattern: {path}"
            lines = []
            for m in matches[:200]:  # cap at 200 results
                p = _P(m)
                suffix = "/" if p.is_dir() else f"  ({p.stat().st_size:,} bytes)"
                lines.append(f"  {m}{suffix}")
            result = f"Found {len(matches)} matches"
            if len(matches) > 200:
                result += f" (showing first 200)"
            return result + ":\n" + "\n".join(lines)
        except Exception as e:
            return f"Error with glob pattern: {e}"

    target = _P(path)
    if not target.exists():
        return f"Path not found: {path}"
    if not target.is_dir():
        return f"Not a directory: {path}. Use read_file to read file contents."

    try:
        if pattern:
            matches = sorted(target.glob(pattern))
        else:
            matches = sorted(target.iterdir())

        if not matches:
            if pattern:
                return f"No files matching '{pattern}' in {path}"
            return f"Directory is empty: {path}"

        lines = []
        for entry in matches[:200]:
            rel = str(entry.relative_to(target)) if not pattern or "**" not in pattern else str(entry)
            if entry.is_dir():
                lines.append(f"  {rel}/")
            else:
                size = entry.stat().st_size
                lines.append(f"  {rel}  ({size:,} bytes)")

        header = f"Directory: {path}"
        if pattern:
            header += f" (pattern: {pattern})"
        header += f"\n{len(matches)} entries"
        if len(matches) > 200:
            header += " (showing first 200)"
        return header + ":\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing {path}: {e}"


async def file_search_content(pattern: str, path: str, file_pattern: str = None, max_results: int = 50) -> str:
    """Search file contents using grep. Returns matching lines with file paths and line numbers."""
    max_r = int(max_results)

    # Use grep (universally available in the container)
    cmd_parts = ["grep", "-rn", "--color=never", f"-m {max_r}"]
    if file_pattern:
        cmd_parts.append(f"--include='{file_pattern}'")
    # Escape single quotes in pattern for shell safety
    safe_pattern = pattern.replace("'", "'\\''")
    cmd_parts.append(f"'{safe_pattern}'")
    cmd_parts.append(f"'{path}'")

    cmd = " ".join(cmd_parts)
    result = await bash_execute(cmd, timeout=15)

    if not result.strip() or result == "(no output)":
        return f"No matches for pattern '{pattern}' in {path}"

    # Count matches
    lines = [l for l in result.strip().split("\n") if l.strip()]
    header = f"Found {len(lines)} matches for '{pattern}' in {path}"
    if file_pattern:
        header += f" (files: {file_pattern})"
    return header + ":\n" + result


# ─── Git Operations ──────────────────────────────────────────────────────

_ALLOWED_GIT_DIRS = [
    "/home/muut/UC-Cloud-production",
    "/home/muut/UC-Cloud-production/services/ops-center",
    "/home/muut/UC-Cloud-production/Unicorn-Brigade",
    "/home/muut/UC-Cloud-production/Center-Deep-Pro",
    "/home/muut/",
]


def _validate_git_repo(repo_path: str) -> tuple:
    """Validate that a path is an allowed git repo. Returns (allowed, reason)."""
    from pathlib import Path as _P
    resolved = str(_P(repo_path).resolve())

    for allowed in _ALLOWED_GIT_DIRS:
        if resolved.startswith(allowed.rstrip("/")):
            return (True, None)

    return (False, f"Git operations only allowed in: {', '.join(_ALLOWED_GIT_DIRS)}")


def _git_safe_cmd(repo_path: str, git_args: str) -> str:
    """Build a git command with safe.directory workaround for container ownership."""
    return f"git -C {repo_path} -c safe.directory={repo_path} {git_args}"


async def git_status(repo_path: str) -> str:
    """Show git status."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"
    return await bash_execute(_git_safe_cmd(repo_path, "status"), timeout=10)


async def git_diff(repo_path: str, target: str = "unstaged", file_path: str = None) -> str:
    """Show git diff."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"

    args = "diff"
    if target == "staged":
        args += " --cached"
    elif target != "unstaged":
        args += f" {target}"

    if file_path:
        args += f" -- {file_path}"

    return await bash_execute(_git_safe_cmd(repo_path, args), timeout=15)


async def git_log(repo_path: str, count: int = 10, oneline: bool = True) -> str:
    """Show git log."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"

    fmt = "--oneline" if oneline else '--format=%h %an %ai %s'
    return await bash_execute(
        _git_safe_cmd(repo_path, f"log {fmt} -n {int(count)}"),
        timeout=10,
    )


async def git_commit(repo_path: str, message: str, files: str) -> str:
    """Stage files and commit."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"

    # Stage files
    stage_result = await bash_execute(
        _git_safe_cmd(repo_path, f"add {files}"), timeout=10
    )
    if "Blocked:" in stage_result or "Error" in stage_result:
        return f"Stage failed: {stage_result}"

    # Commit — use heredoc for message to handle special chars
    commit_cmd = f"""{_git_safe_cmd(repo_path, 'commit -m')} "$(cat <<'COLONEL_EOF'
{message}

Co-Authored-By: The Colonel <colonel@unicorncommander.ai>
COLONEL_EOF
)"
"""
    return await bash_execute(commit_cmd, timeout=15)


async def git_branch(repo_path: str, action: str = "list", branch_name: str = None) -> str:
    """List, create, or switch branches."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"

    if action == "list":
        return await bash_execute(_git_safe_cmd(repo_path, "branch -a"), timeout=10)
    elif action == "current":
        return await bash_execute(_git_safe_cmd(repo_path, "branch --show-current"), timeout=5)
    elif action == "create":
        if not branch_name:
            return "branch_name is required for 'create' action"
        return await bash_execute(_git_safe_cmd(repo_path, f"checkout -b {branch_name}"), timeout=10)
    elif action == "checkout":
        if not branch_name:
            return "branch_name is required for 'checkout' action"
        return await bash_execute(_git_safe_cmd(repo_path, f"checkout {branch_name}"), timeout=10)
    else:
        return f"Unknown branch action: {action}"


async def git_push(repo_path: str, remote: str = "origin", branch: str = None) -> str:
    """Push commits to remote."""
    allowed, reason = _validate_git_repo(repo_path)
    if not allowed:
        return f"Blocked: {reason}"

    args = f"push {remote}"
    if branch:
        args += f" {branch}"

    return await bash_execute(_git_safe_cmd(repo_path, args), timeout=30)


# ─── Keycloak Helper ──────────────────────────────────────────────────

_KC_CONTAINER = os.getenv("KEYCLOAK_CONTAINER", "unicorn-keycloak")
_KC_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
_KC_ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "MagicUnicorn2025!")


async def _keycloak_exec(kcadm_args: str, timeout: int = 15) -> str:
    """Run kcadm.sh command after authenticating."""
    auth_cmd = (
        f"docker exec {_KC_CONTAINER} /opt/keycloak/bin/kcadm.sh config credentials "
        f"--server http://localhost:8080 --realm master "
        f"--user {_KC_ADMIN_USER} --password {_KC_ADMIN_PASS} 2>/dev/null"
    )
    run_cmd = f"docker exec {_KC_CONTAINER} /opt/keycloak/bin/kcadm.sh {kcadm_args}"
    return await bash_execute(f"{auth_cmd} && {run_cmd}", timeout=timeout)


# ─── Brigade Delegation ─────────────────────────────────────────────────

import httpx as _httpx

_BRIGADE_URL = os.getenv("BRIGADE_API_URL", "http://brigade-api:8100")
_BRIGADE_KEY = os.getenv("BRIGADE_API_KEY", "")


async def brigade_delegate_task(agent_id: str, task: str, context: str = "") -> str:
    """Delegate a task to a Unicorn Brigade agent via A2A protocol."""
    if not _BRIGADE_KEY:
        return "ERROR: BRIGADE_API_KEY not configured. Cannot communicate with Brigade."

    message = task
    if context:
        message = f"Context: {context}\n\nTask: {task}"

    url = f"{_BRIGADE_URL}/api/v1/a2a/agents/{agent_id}/invoke"
    payload = {
        "task": message,
        "context": {
            "requesting_agent_id": "colonel-corelli",
            "requesting_agent_name": "The Colonel (Ops-Center)",
        },
        "conversation_history": [],
    }
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": _BRIGADE_KEY,
    }

    try:
        async with _httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 404:
                return f"Agent '{agent_id}' not found in Brigade. Use list_agents to see available agents."
            if resp.status_code == 401:
                return "Authentication failed. BRIGADE_API_KEY may be invalid."
            resp.raise_for_status()
            data = resp.json()
            # A2A response: 'result' has text, 'output_data' has tool_calls
            result_text = data.get("result", "") or ""
            if isinstance(result_text, dict):
                result_text = result_text.get("content", str(result_text))
            # If no text result, summarize tool call results
            if not result_text.strip():
                output = data.get("output_data", {}) or {}
                tool_calls = output.get("tool_calls", [])
                if tool_calls:
                    parts = [f"Agent used {len(tool_calls)} tool(s):"]
                    for tc in tool_calls[:5]:  # Show max 5
                        name = tc.get("name", "?")
                        res = tc.get("result", {})
                        parts.append(f"  - {name}: {json.dumps(res)[:150]}")
                    result_text = "\n".join(parts)
                else:
                    result_text = "(No response from agent)"
            status = data.get("status", "unknown")
            duration = data.get("duration_seconds", 0)
            model = data.get("model_used", "unknown")
            return (
                f"Brigade agent '{agent_id}' responded (status={status}, "
                f"model={model}, {duration:.1f}s):\n{result_text}"
            )
    except _httpx.TimeoutException:
        return f"Timeout waiting for Brigade agent '{agent_id}' (120s limit)."
    except _httpx.HTTPStatusError as e:
        return f"Brigade API error: {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return f"Failed to contact Brigade: {str(e)}"


async def brigade_list_agents() -> str:
    """List available Brigade agents via A2A discovery (public endpoint)."""
    url = f"{_BRIGADE_URL}/api/v1/a2a/agents"
    try:
        async with _httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            agents = data.get("agents", [])
            if not agents:
                return "No agents available in Brigade."
            lines = ["Available Brigade agents:\n"]
            for a in agents:
                aid = a.get("id", "?")
                name = a.get("name", "?")
                desc = a.get("description", "")[:80]
                lines.append(f"  {aid}: {name} — {desc}")
            return "\n".join(lines)
    except Exception as e:
        return f"Failed to query Brigade agents: {str(e)}"


# ─── Executor Dispatch Map ──────────────────────────────────────────────

EXECUTOR_MAP = {
    # Docker Management
    "docker-management__list_containers": lambda **kw: docker_list_containers(kw.get("status", "running")),
    "docker-management__inspect_container": lambda **kw: docker_inspect_container(kw["container_name"]),
    "docker-management__container_logs": lambda **kw: docker_container_logs(
        kw["container_name"], kw.get("lines", 50), kw.get("since", "")
    ),
    "docker-management__container_stats": lambda **kw: docker_container_stats(kw["container_name"]),
    "docker-management__manage_container": lambda **kw: docker_manage_container(
        kw["container_name"], kw["action"]
    ),

    # Bash Execution (with persistent CWD per session)
    "bash-execution__run_command": lambda **kw: bash_execute(
        kw["command"], kw.get("timeout", 30), session_id=kw.get("_session_id")
    ),

    # System Status
    "system-status__cpu": lambda **kw: system_cpu_status(),
    "system-status__memory": lambda **kw: system_memory_status(),
    "system-status__disk": lambda **kw: system_disk_status(),
    "system-status__gpu": lambda **kw: system_gpu_status(),
    "system-status__processes": lambda **kw: system_top_processes(kw.get("count", 10)),
    "system-status__full_status": lambda **kw: system_full_status(),

    # Service Health
    "service-health__check_all": lambda **kw: service_health_check_all(),
    "service-health__check_one": lambda **kw: service_health_check_one(kw["service_name"]),

    # Log Viewer
    "log-viewer__get_logs": lambda **kw: docker_container_logs(
        kw["container_name"], kw.get("lines", 50)
    ),
    "log-viewer__search_logs": lambda **kw: log_search(
        kw["container_name"], kw["pattern"], kw.get("lines", 50)
    ),

    # PostgreSQL Operations
    "postgresql-ops__list_databases": lambda **kw: postgresql_list_databases(),
    "postgresql-ops__list_tables": lambda **kw: postgresql_list_tables(kw.get("database", "unicorn_db")),
    "postgresql-ops__query": lambda **kw: postgresql_query(
        kw["query"], kw.get("database", "unicorn_db"),
        write_enabled=kw.pop("_write_enabled", False),
    ),
    "postgresql-ops__stats": lambda **kw: postgresql_stats(),

    # Traefik Management
    "traefik-management__list_routers": lambda **kw: traefik_list_routers(),
    "traefik-management__list_services": lambda **kw: traefik_list_services(),
    "traefik-management__list_middlewares": lambda **kw: traefik_list_middlewares(),
    "traefik-management__list_tls_certs": lambda **kw: traefik_list_tls_certs(),
    "traefik-management__restart_traefik": lambda **kw: traefik_restart(),

    # Backup Management
    "backup-management__trigger_backup": lambda **kw: backup_trigger(
        kw.get("backup_dir"), kw.get("dry_run", False)
    ),
    "backup-management__list_backups": lambda **kw: backup_list(
        kw.get("backup_dir"), kw.get("limit", 10)
    ),
    "backup-management__restore_database": lambda **kw: backup_restore_database(
        kw["backup_file"]
    ),
    "backup-management__cleanup_old_backups": lambda **kw: backup_cleanup_old(
        kw.get("days", 7), kw.get("keep", 3), kw.get("backup_dir")
    ),

    # GPU Monitoring
    "gpu-monitoring__summary": lambda **kw: gpu_summary(),
    "gpu-monitoring__vram_usage": lambda **kw: gpu_vram_usage(),
    "gpu-monitoring__temperatures": lambda **kw: gpu_temperatures(),
    "gpu-monitoring__process_list": lambda **kw: gpu_process_list(),

    # Network Diagnostics
    "network-diagnostics__port_check": lambda **kw: net_port_check(
        kw["host"], kw["port"], kw.get("timeout", 3)
    ),
    "network-diagnostics__dns_lookup": lambda **kw: net_dns_lookup(
        kw["hostname"]
    ),
    "network-diagnostics__list_docker_networks": lambda **kw: net_list_docker_networks(),
    "network-diagnostics__inspect_docker_network": lambda **kw: net_inspect_docker_network(
        kw["network_name"]
    ),

    # Resource Cleanup
    "resource-cleanup__disk_usage": lambda **kw: cleanup_disk_usage(),
    "resource-cleanup__docker_prune": lambda **kw: cleanup_docker_prune(
        kw.get("include_volumes", False)
    ),
    "resource-cleanup__cleanup_logs": lambda **kw: cleanup_logs(
        kw.get("max_size_mb", 50)
    ),

    # LiteLLM Management
    "litellm-management__health_check": lambda **kw: litellm_health_check(),
    "litellm-management__list_models": lambda **kw: litellm_list_models(),
    "litellm-management__generate_master_key": lambda **kw: litellm_generate_master_key(),

    # Keycloak Auth
    "keycloak-auth__list_users": lambda **kw: _keycloak_exec(
        "get users --realm uchub --fields username,email,enabled --limit 50",
        timeout=15,
    ),
    "keycloak-auth__list_realms": lambda **kw: _keycloak_exec(
        "get realms --fields realm,enabled",
        timeout=10,
    ),
    "keycloak-auth__user_info": lambda **kw: _keycloak_exec(
        f"get users --realm uchub -q username={kw['username']} --fields id,username,email,enabled,emailVerified",
        timeout=10,
    ),

    # Forgejo Management (uses CLI inside container)
    "forgejo-management__list_repos": lambda **kw: bash_execute(
        "docker exec unicorn-forgejo gitea admin repo list --limit 50 2>/dev/null || echo 'Forgejo CLI not available'",
        timeout=10,
    ),
    "forgejo-management__list_orgs": lambda **kw: bash_execute(
        "docker exec unicorn-forgejo gitea admin org list 2>/dev/null || echo 'Forgejo CLI not available'",
        timeout=10,
    ),

    # File Operations
    "file-operations__read_file": lambda **kw: file_read(
        kw["path"], kw.get("offset", 1), kw.get("limit", 200)
    ),
    "file-operations__write_file": lambda **kw: file_write(kw["path"], kw["content"]),
    "file-operations__edit_file": lambda **kw: file_edit(
        kw["path"], kw["old_text"], kw["new_text"]
    ),
    "file-operations__list_directory": lambda **kw: file_list_directory(
        kw["path"], kw.get("pattern")
    ),
    "file-operations__search_content": lambda **kw: file_search_content(
        kw["pattern"], kw["path"], kw.get("file_pattern"), kw.get("max_results", 50)
    ),

    # Git Operations
    "git-operations__status": lambda **kw: git_status(kw["repo_path"]),
    "git-operations__diff": lambda **kw: git_diff(
        kw["repo_path"], kw.get("target", "unstaged"), kw.get("file_path")
    ),
    "git-operations__log": lambda **kw: git_log(
        kw["repo_path"], kw.get("count", 10), kw.get("oneline", True)
    ),
    "git-operations__commit": lambda **kw: git_commit(
        kw["repo_path"], kw["message"], kw["files"]
    ),
    "git-operations__branch": lambda **kw: git_branch(
        kw["repo_path"], kw.get("action", "list"), kw.get("branch_name")
    ),
    "git-operations__push": lambda **kw: git_push(
        kw["repo_path"], kw.get("remote", "origin"), kw.get("branch")
    ),

    # Frontend Management
    "frontend-management__read_source": lambda **kw: frontend_read_source(kw["path"]),
    "frontend-management__list_files": lambda **kw: frontend_list_files(kw.get("path", "src")),
    "frontend-management__edit_source": lambda **kw: frontend_edit_source(
        kw["path"], kw["old_text"], kw["new_text"]
    ),
    "frontend-management__build_frontend": lambda **kw: frontend_build(),
    "frontend-management__deploy_frontend": lambda **kw: frontend_deploy(),
    "frontend-management__get_build_status": lambda **kw: frontend_build_status(),

    # Brigade Delegation
    "brigade-delegation__delegate_task": lambda **kw: brigade_delegate_task(
        kw["agent_id"], kw["task"], kw.get("context", "")
    ),
    "brigade-delegation__list_agents": lambda **kw: brigade_list_agents(),
}


# ─── Frontend Management Executors ────────────────────────────────────

import pathlib as _pathlib

# Resolve ops-center root (works both in container at /app and on host)
_OPS_ROOT = _pathlib.Path(os.getenv("OPS_CENTER_ROOT", "/app"))
_SRC_ROOT = _OPS_ROOT


def _safe_frontend_path(rel_path: str) -> _pathlib.Path:
    """Validate and resolve a relative path within the ops-center tree.
    Only allows access to src/, public/, package.json, vite.config.*, tailwind.config.*"""
    clean = rel_path.lstrip("/").replace("\\", "/")
    # Block path traversal
    if ".." in clean:
        raise ValueError("Path traversal not allowed")
    resolved = (_SRC_ROOT / clean).resolve()
    # Must stay within ops-center root
    if not str(resolved).startswith(str(_SRC_ROOT.resolve())):
        raise ValueError("Path outside ops-center root")
    # Only allow specific directories/files
    allowed_prefixes = ("src/", "public/logos/", "public/index.html", "package.json",
                        "vite.config", "tailwind.config", "postcss.config", "index.html")
    if not any(clean.startswith(p) or clean == p for p in allowed_prefixes):
        raise ValueError(f"Access restricted to src/, public/logos/, and config files. Got: {clean}")
    return resolved


async def frontend_read_source(path: str) -> str:
    """Read a frontend source file."""
    try:
        resolved = _safe_frontend_path(path)
        if not resolved.exists():
            return f"File not found: {path}"
        if resolved.stat().st_size > 100_000:
            return f"File too large ({resolved.stat().st_size} bytes). Read a smaller file or use a specific section."
        return resolved.read_text(encoding="utf-8")
    except ValueError as e:
        return f"Access denied: {e}"
    except Exception as e:
        return f"Error reading {path}: {e}"


async def frontend_list_files(path: str = "src") -> str:
    """List files in a frontend directory."""
    try:
        resolved = _safe_frontend_path(path)
        if not resolved.is_dir():
            return f"Not a directory: {path}"
        entries = sorted(resolved.iterdir())
        lines = []
        for entry in entries[:100]:  # limit to 100 entries
            rel = str(entry.relative_to(_SRC_ROOT))
            suffix = "/" if entry.is_dir() else f"  ({entry.stat().st_size} bytes)"
            lines.append(f"  {rel}{suffix}")
        return f"Directory: {path}\n" + "\n".join(lines)
    except ValueError as e:
        return f"Access denied: {e}"
    except Exception as e:
        return f"Error listing {path}: {e}"


async def frontend_edit_source(path: str, old_text: str, new_text: str) -> str:
    """Edit a frontend file by string replacement."""
    try:
        resolved = _safe_frontend_path(path)
        if not resolved.exists():
            return f"File not found: {path}"
        content = resolved.read_text(encoding="utf-8")
        count = content.count(old_text)
        if count == 0:
            return f"old_text not found in {path}. Make sure the text matches exactly (including whitespace)."
        if count > 1:
            return f"old_text found {count} times in {path}. Provide more context to make it unique."
        new_content = content.replace(old_text, new_text, 1)
        resolved.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {path}. Changed {len(old_text)} chars to {len(new_text)} chars.\nRemember to build and deploy for changes to take effect."
    except ValueError as e:
        return f"Access denied: {e}"
    except Exception as e:
        return f"Error editing {path}: {e}"


async def frontend_build() -> str:
    """Run npm build."""
    try:
        result = await bash_execute(
            f"cd {_SRC_ROOT} && npm run build 2>&1 | tail -30",
            timeout=60,
        )
        return f"Build output:\n{result}"
    except Exception as e:
        return f"Build failed: {e}"


async def frontend_deploy() -> str:
    """Copy dist/ to public/ to make changes live."""
    try:
        dist = _SRC_ROOT / "dist"
        public = _SRC_ROOT / "public"
        if not dist.exists():
            return "No dist/ directory found. Run build first."
        result = await bash_execute(
            f"cp -r {dist}/* {public}/ && echo 'Deployed successfully'",
            timeout=15,
        )
        return result
    except Exception as e:
        return f"Deploy failed: {e}"


async def frontend_build_status() -> str:
    """Check the last build status."""
    try:
        dist = _SRC_ROOT / "dist"
        if not dist.exists():
            return "No dist/ directory. Frontend has not been built yet."
        index = dist / "index.html"
        if not index.exists():
            return "dist/ exists but no index.html. Build may have failed."
        import time
        mtime = index.stat().st_mtime
        age = int(time.time() - mtime)
        if age < 60:
            age_str = f"{age}s ago"
        elif age < 3600:
            age_str = f"{age // 60}m ago"
        elif age < 86400:
            age_str = f"{age // 3600}h ago"
        else:
            age_str = f"{age // 86400}d ago"
        assets = list((dist / "assets").glob("*.js")) if (dist / "assets").exists() else []
        total_size = sum(f.stat().st_size for f in assets)
        return (
            f"Last build: {age_str}\n"
            f"Assets: {len(assets)} JS files, {total_size // 1024}KB total\n"
            f"Status: Ready to deploy"
        )
    except Exception as e:
        return f"Error checking build: {e}"
