"""
Colonel REST API Router - Configuration, status, and session management.
"""

import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from colonel.models import ColonelConfig, ColonelConfigUpdate, ColonelStatusResponse
from colonel.config import get_colonel_config, save_colonel_config
from colonel.websocket_gateway import colonel_gateway

logger = logging.getLogger("colonel.router")

router = APIRouter(
    prefix="/api/v1/colonel",
    tags=["colonel"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Forbidden - admin only"},
    },
)


# ─── Auth Dependencies ──────────────────────────────────────────────────

async def _get_user(request: Request) -> dict:
    """Get authenticated user from session cookie."""
    import os
    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    sessions = RedisSessionManager(host=redis_host, port=redis_port)
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="No user in session")

    return user


async def _require_admin(request: Request) -> dict:
    """Require admin role."""
    user = await _get_user(request)
    is_admin = (
        user.get("role") == "admin"
        or "admin" in user.get("realm_access", {}).get("roles", [])
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ─── Status ─────────────────────────────────────────────────────────────

@router.get("/status", response_model=ColonelStatusResponse)
async def get_status(admin: dict = Depends(_require_admin)):
    """Get Colonel status and configuration."""
    config = await get_colonel_config()

    skills_loaded = 0
    if colonel_gateway.skill_router:
        skills_loaded = len(colonel_gateway.skill_router.get_tool_definitions(config.enabled_skills))

    memory_entries = 0
    if colonel_gateway.memory_client:
        try:
            memory_entries = await colonel_gateway.memory_client.count()
        except Exception:
            pass

    graph_stats = None
    if colonel_gateway.graph_client and colonel_gateway.graph_client.available:
        try:
            graph_stats = colonel_gateway.graph_client.get_stats()
        except Exception:
            pass

    return ColonelStatusResponse(
        online=True,
        config=config,
        active_sessions=len(colonel_gateway._connections),
        skills_loaded=skills_loaded,
        memory_entries=memory_entries,
        graph_stats=graph_stats,
    )


# ─── Configuration ──────────────────────────────────────────────────────

@router.get("/config")
async def get_config(admin: dict = Depends(_require_admin)):
    """Get Colonel configuration."""
    config = await get_colonel_config()
    return config.model_dump()


@router.put("/config")
async def update_config(update: ColonelConfigUpdate, admin: dict = Depends(_require_admin)):
    """Update Colonel configuration."""
    config = await get_colonel_config()

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if key == "personality":
                config.personality = config.personality.model_copy(update=value if isinstance(value, dict) else value.model_dump())
            else:
                setattr(config, key, value)

    config = await save_colonel_config(config)
    logger.info(f"Colonel config updated by {admin.get('email', 'unknown')}")
    return config.model_dump()


# ─── Sessions ───────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(admin: dict = Depends(_require_admin)):
    """List all Colonel chat sessions for the current user."""
    user_id = admin.get("sub") or admin.get("id") or admin.get("user_id", "unknown")
    sessions = await colonel_gateway.list_sessions(user_id)
    return {"sessions": sessions}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, admin: dict = Depends(_require_admin)):
    """Delete a specific chat session."""
    import redis.asyncio as aioredis
    import os

    r = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "unicorn-redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
    try:
        deleted = await r.delete(f"colonel:session:{session_id}")
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"detail": "Session deleted"}
    finally:
        await r.aclose()


# ─── Onboarding ─────────────────────────────────────────────────────────

@router.get("/onboarded")
async def check_onboarded(admin: dict = Depends(_require_admin)):
    """Check if The Colonel has been set up."""
    config = await get_colonel_config()
    return {"onboarded": config.onboarded}


@router.post("/onboard")
async def complete_onboarding(config_data: dict, admin: dict = Depends(_require_admin)):
    """Complete The Colonel onboarding with provided configuration."""
    config = await get_colonel_config()

    # Apply onboarding data
    if "name" in config_data:
        config.name = config_data["name"]
    if "server_name" in config_data:
        config.server_name = config_data["server_name"]
    if "mission" in config_data:
        config.mission = config_data["mission"]
    if "personality" in config_data:
        from colonel.models import ColonelPersonality
        config.personality = ColonelPersonality(**config_data["personality"])
    if "model" in config_data:
        config.model = config_data["model"]
    if "enabled_skills" in config_data:
        config.enabled_skills = config_data["enabled_skills"]
    if "admin_only" in config_data:
        config.admin_only = config_data["admin_only"]

    config.onboarded = True
    config = await save_colonel_config(config)

    logger.info(f"Colonel onboarding completed: {config.name} by {admin.get('email', 'unknown')}")
    return config.model_dump()


# ─── Detection ──────────────────────────────────────────────────────────

@router.get("/detect")
async def detect_environment(admin: dict = Depends(_require_admin)):
    """Auto-detect available services and hardware for Colonel setup."""
    import psutil
    import platform

    result = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_cores": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "containers": [],
        "gpus": [],
        "available_skills": [],
    }

    # Detect containers
    try:
        import docker
        client = docker.from_env()
        for c in client.containers.list():
            result["containers"].append({
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                "status": c.status,
            })
    except Exception as e:
        logger.warning(f"Docker detection failed: {e}")

    # Detect GPUs
    try:
        import subprocess
        gpu_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if gpu_result.returncode == 0:
            for line in gpu_result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    result["gpus"].append({"name": parts[0], "memory_mb": int(parts[1])})
    except Exception:
        pass

    # Determine available skills based on detected environment
    result["available_skills"] = [
        {"id": "docker-management", "name": "Docker Management", "detected": len(result["containers"]) > 0},
        {"id": "bash-execution", "name": "Bash Execution", "detected": True},
        {"id": "system-status", "name": "System Status", "detected": True},
        {"id": "service-health", "name": "Service Health", "detected": len(result["containers"]) > 0},
        {"id": "log-viewer", "name": "Log Viewer", "detected": len(result["containers"]) > 0},
    ]

    # Auto-detect optional skills
    container_names = [c["name"] for c in result["containers"]]
    if any("postgresql" in n for n in container_names):
        result["available_skills"].append(
            {"id": "postgresql-ops", "name": "PostgreSQL Operations", "detected": True}
        )
    if any("keycloak" in n for n in container_names):
        result["available_skills"].append(
            {"id": "keycloak-auth", "name": "Keycloak Auth", "detected": True}
        )
    if any("forgejo" in n or "gitea" in n for n in container_names):
        result["available_skills"].append(
            {"id": "forgejo-management", "name": "Forgejo Git", "detected": True}
        )

    return result


# ─── Skills ─────────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills(admin: dict = Depends(_require_admin)):
    """List all available skills and their status."""
    config = await get_colonel_config()

    if colonel_gateway.skill_router:
        all_skills = colonel_gateway.skill_router.list_skills()
        for skill in all_skills:
            skill["enabled"] = skill["id"] in config.enabled_skills
        return {"skills": all_skills}

    return {"skills": []}


@router.put("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, admin: dict = Depends(_require_admin)):
    """Enable or disable a skill."""
    config = await get_colonel_config()

    if skill_id in config.enabled_skills:
        config.enabled_skills.remove(skill_id)
        enabled = False
    else:
        config.enabled_skills.append(skill_id)
        enabled = True

    await save_colonel_config(config)
    return {"skill_id": skill_id, "enabled": enabled}


# ─── Memory ─────────────────────────────────────────────────────────────

@router.get("/memory/search")
async def search_memory(q: str, limit: int = 10, admin: dict = Depends(_require_admin)):
    """Search Colonel's semantic memory."""
    if not colonel_gateway.memory_client:
        return {"results": [], "detail": "Memory system not initialized"}

    results = await colonel_gateway.memory_client.search(q, limit=limit)
    return {"results": results}


# ─── Audit Log ──────────────────────────────────────────────────────────

@router.get("/audit")
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    action_type: Optional[str] = None,
    skill_name: Optional[str] = None,
    admin: dict = Depends(_require_admin),
):
    """Get Colonel audit log entries."""
    from colonel.memory.audit import get_audit_log as _get_audit_log

    user_id = admin.get("sub") or admin.get("id") or admin.get("user_id")
    entries = await _get_audit_log(
        limit=limit, offset=offset,
        action_type=action_type, skill_name=skill_name,
    )
    return {"entries": entries, "total": len(entries)}
