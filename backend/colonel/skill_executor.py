"""
Skill Executor - Executes Docker, bash, and system commands.

Each executor function takes parameters and returns a string result.
"""

import asyncio
import json
import logging
import time
from typing import Optional

import docker
import psutil

from colonel.safety import validate_command, sanitize_output, validate_docker_command

logger = logging.getLogger("colonel.skill_executor")

# Docker client (lazy init)
_docker_client = None


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

async def bash_execute(command: str, timeout: int = 30) -> str:
    """Execute a bash command with safety validation."""
    allowed, reason = validate_command(command)
    if not allowed:
        return f"Blocked: {reason}"

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return f"Command timed out after {timeout}s"

        output = stdout.decode("utf-8", errors="replace")
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

    # Bash Execution
    "bash-execution__run_command": lambda **kw: bash_execute(
        kw["command"], kw.get("timeout", 30)
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

    # Keycloak Auth
    "keycloak-auth__list_users": lambda **kw: bash_execute(
        "docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users --realm uchub --fields username,email,enabled --limit 50",
        timeout=15,
    ),
    "keycloak-auth__list_realms": lambda **kw: bash_execute(
        "docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get realms --fields realm,enabled",
        timeout=10,
    ),
    "keycloak-auth__user_info": lambda **kw: bash_execute(
        f"docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users --realm uchub -q username={kw['username']} --fields id,username,email,enabled,emailVerified",
        timeout=10,
    ),

    # Forgejo Management
    "forgejo-management__list_repos": lambda **kw: bash_execute(
        "docker exec unicorn-forgejo gitea admin repo list --limit 50 2>/dev/null || echo 'Forgejo CLI not available'",
        timeout=10,
    ),
    "forgejo-management__list_orgs": lambda **kw: bash_execute(
        "docker exec unicorn-forgejo gitea admin org list 2>/dev/null || echo 'Forgejo CLI not available'",
        timeout=10,
    ),
}
