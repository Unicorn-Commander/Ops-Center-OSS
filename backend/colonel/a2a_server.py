"""
A2A (Agent-to-Agent) Server for The Colonel.

Implements the Google/Linux Foundation A2A protocol:
- GET /.well-known/agent.json → Agent Card
- POST /a2a → JSON-RPC 2.0 task execution

Supported JSON-RPC methods:
- skills/list     → List available skills and their actions
- skills/invoke   → Execute a specific skill action
- agent/status    → Return Colonel status information
- tasks/send      → Legacy A2A task execution (keyword-based routing)

This allows Brigade (The General) and other agents to discover and
invoke The Colonel's skills programmatically.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Optional, Dict, Any, List

import httpx
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from colonel.config import get_colonel_config, list_colonels
from colonel.skill_router import SkillRouter
from colonel.skill_executor import EXECUTOR_MAP
from colonel.memory.audit import log_action

logger = logging.getLogger("colonel.a2a")

# Brigade connection settings
BRIGADE_API_URL = os.getenv("BRIGADE_API_URL", "http://unicorn-brigade:8100")
BRIGADE_SERVICE_KEY = os.getenv("BRIGADE_SERVICE_KEY", "")
A2A_SHARED_SECRET = os.getenv("A2A_SHARED_SECRET", "")

# Provider info — env-overridable so each white-label deployment can identify
# its own brand (Magic Unicorn / Majik's Studio / Genesis Flow Labs / etc.)
# rather than hardcoding the platform vendor on every Colonel everywhere.
COLONEL_PROVIDER_ORG = os.getenv(
    "COLONEL_PROVIDER_ORG",
    "Magic Unicorn Unconventional Technology & Stuff Inc",
)
COLONEL_PROVIDER_URL = os.getenv(
    "COLONEL_PROVIDER_URL",
    "https://unicorncommander.com",
)

# Public-facing base URL override. When set (e.g.
# COLONEL_PUBLIC_URL=https://ops.majiks.studio) it forces every agent
# card / api-catalog url to use this scheme+host instead of whatever
# Starlette derived from the inbound request. Useful behind reverse
# proxies that don't forward X-Forwarded-Proto correctly.
COLONEL_PUBLIC_URL = os.getenv("COLONEL_PUBLIC_URL", "").rstrip("/")


def _public_base_url(request) -> str:
    """Derive the canonical public base URL for this request.

    Resolution order:
      1. COLONEL_PUBLIC_URL env (explicit override, wins always).
      2. X-Forwarded-Proto + X-Forwarded-Host headers (Traefik / nginx /
         any RFC 7239-aware reverse proxy).
      3. Starlette's request.base_url (fallback for direct hits).

    The result never has a trailing slash so callers can safely append
    paths like "/a2a" or "/.well-known/agent.json".
    """
    if COLONEL_PUBLIC_URL:
        return COLONEL_PUBLIC_URL

    # Honour reverse-proxy hints. We only trust X-Forwarded-Proto here
    # because production deploys live behind Traefik/nginx that strip
    # client-supplied versions of these headers.
    fwd_proto = request.headers.get("x-forwarded-proto")
    fwd_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if fwd_proto and fwd_host:
        # Strip any port-from-host duplication and trailing slashes.
        return f"{fwd_proto}://{fwd_host}".rstrip("/")

    return str(request.base_url).rstrip("/")


# ─── Agent Card ──────────────────────────────────────────────────────────

def build_agent_card(config, skills: List[Dict], base_url: str) -> Dict[str, Any]:
    """Build an A2A-compliant Agent Card."""
    name = config.name or "The Colonel"
    server = config.server_name or "this server"
    mission = config.mission or "general"
    return {
        "name": name,
        "description": f"{name}, AI command agent for {server}. Mission: {mission}.",
        "url": f"{base_url}/a2a",
        "version": "1.0.0",
        "provider": {
            "organization": COLONEL_PROVIDER_ORG,
            "url": COLONEL_PROVIDER_URL,
        },
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "skillInvocation": True,
        },
        "authentication": {
            "schemes": ["bearer"],
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "tags": [config.mission or "general", "server-management"],
                "actions": s.get("actions", []),
            }
            for s in skills
        ],
    }


# ─── JSON-RPC Models ────────────────────────────────────────────────────

class A2ARequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class TaskSendParams(BaseModel):
    id: Optional[str] = None
    message: Optional[Dict[str, Any]] = None


# ─── Authentication ──────────────────────────────────────────────────────

def _validate_a2a_auth(request: Request) -> bool:
    """
    Validate A2A request authentication.

    Checks for a shared secret in the Authorization header if one is configured
    via A2A_SHARED_SECRET or BRIGADE_SERVICE_KEY environment variables.
    If no secret is configured, all requests are allowed (open mode).
    """
    secret = A2A_SHARED_SECRET or BRIGADE_SERVICE_KEY
    if not secret:
        # No secret configured — open mode
        return True

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == secret

    # Also accept X-Service-Key header
    service_key = request.headers.get("x-service-key", "")
    if service_key:
        return service_key == secret

    return False


# ─── Router ─────────────────────────────────────────────────────────────

router = APIRouter(tags=["a2a"])


def _resolve_colonel_id(params: Dict[str, Any], default: str = "default") -> str:
    """
    Resolve a colonel_id from JSON-RPC params.

    Accepts either top-level 'colonel' or nested 'colonel_id' for clarity.
    Falls back to 'default' so existing single-Colonel callers keep working.
    """
    if not isinstance(params, dict):
        return default
    return params.get("colonel") or params.get("colonel_id") or default


async def _build_card_for(colonel_id: str, base_url: str) -> Dict[str, Any]:
    """Build the agent card for a given colonel_id."""
    config = await get_colonel_config(colonel_id)

    skills = []
    try:
        sr = SkillRouter()
        skills = sr.list_skills()
    except Exception as e:
        logger.warning(f"Could not load skills for agent card ({colonel_id}): {e}")

    return build_agent_card(config, skills, base_url)


@router.get("/.well-known/agent.json")
async def agent_card(request: Request):
    """
    Publish the default Agent Card for discovery (backwards-compatible).

    This always serves the colonel with id='default'. For per-Colonel
    discovery on multi-Colonel servers, use /.well-known/agent-{colonel_id}.json
    or query the /.well-known/api-catalog index.
    """
    base_url = _public_base_url(request)
    return await _build_card_for("default", base_url)


@router.get("/.well-known/agent-{colonel_id}.json")
async def agent_card_named(colonel_id: str, request: Request):
    """
    Publish the Agent Card for a specific Colonel by id.

    Enables multi-Colonel-per-server deployments (e.g. platform 'corelli'
    plus per-server scoped colonels like 'carmine', 'calderon', ...).
    """
    # Reject the special 'default' alias here so callers use the canonical
    # path /.well-known/agent.json — keeps responses cache-coherent.
    if colonel_id == "default":
        raise HTTPException(
            status_code=404,
            detail="Use /.well-known/agent.json for the default Colonel.",
        )

    # Verify the colonel exists before building the card so callers get a
    # clean 404 instead of a synthetic empty card.
    known = {c["id"] for c in await list_colonels()}
    if colonel_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown colonel_id: {colonel_id}")

    base_url = _public_base_url(request)
    return await _build_card_for(colonel_id, base_url)


@router.get("/.well-known/api-catalog")
async def api_catalog(request: Request):
    """
    RFC 9264-style catalog of every Colonel hosted on this server.

    This is the forward-compatible discovery endpoint for multi-Colonel
    deployments — clients walk this list to find every accessible agent
    card without having to guess colonel ids.

    Cf. https://github.com/a2aproject/A2A/issues/641 for the emerging
    A2A multi-agent-per-origin proposal.
    """
    base_url = _public_base_url(request)
    colonels = await list_colonels()

    links = []
    for c in colonels:
        cid = c["id"]
        href = f"{base_url}/.well-known/agent.json" if cid == "default" \
            else f"{base_url}/.well-known/agent-{cid}.json"
        links.append({
            "href": href,
            "rel": "agent-card",
            "title": c.get("name") or cid,
            "colonel_id": cid,
            "server_name": c.get("server_name"),
            "mission": c.get("mission"),
        })

    return {
        "linkset": [
            {
                "anchor": base_url,
                "links": links,
            }
        ],
        "colonels": colonels,
    }


@router.post("/a2a")
async def a2a_endpoint(request: Request):
    """
    A2A JSON-RPC 2.0 endpoint.

    Supported methods:
      - skills/list:   List available skills and their actions
      - skills/invoke: Execute a skill action directly
      - agent/status:  Return Colonel status information
      - tasks/send:    Legacy A2A task execution (keyword-based routing)
      - tasks/get:     Get task status (not implemented yet)

    All methods accept an optional 'colonel' param to scope the call to
    a specific Colonel; absent it, the 'default' Colonel is used so single-
    Colonel deployments continue to work unchanged.
    """
    # Authenticate
    if not _validate_a2a_auth(request):
        return _jsonrpc_error(None, -32000, "Authentication failed: invalid or missing service key")

    try:
        body = await request.json()
    except Exception:
        return _jsonrpc_error(None, -32700, "Parse error")

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if not method:
        return _jsonrpc_error(req_id, -32600, "Invalid Request: missing method")

    # Route to handler
    if method == "skills/list":
        return await _handle_skills_list(req_id, params)
    elif method == "skills/invoke":
        return await _handle_skills_invoke(req_id, params)
    elif method == "agent/status":
        return await _handle_agent_status(req_id, params)
    elif method == "tasks/send":
        return await _handle_tasks_send(req_id, params)
    elif method == "tasks/get":
        return _jsonrpc_error(req_id, -32601, "tasks/get not yet implemented")
    elif method == "colonels/list":
        return await _handle_colonels_list(req_id, params)
    else:
        return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")


# ─── skills/list handler ────────────────────────────────────────────────

async def _handle_skills_list(req_id: Optional[str], params: Dict[str, Any]) -> Dict:
    """
    Handle skills/list: return all available skills and their actions.

    Returns a list of skills, each with an id, name, description, and a list
    of actions. Each action includes its name, description, parameters, and
    whether it requires confirmation.
    """
    try:
        sr = SkillRouter()
        skills = sr.list_skills()

        # Also include the executor map keys for reference
        executor_keys = sorted(EXECUTOR_MAP.keys())

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "status": "success",
                "data": {
                    "skills": skills,
                    "executor_count": len(executor_keys),
                    "executors": executor_keys,
                },
            },
        }
    except Exception as e:
        logger.error(f"skills/list error: {e}", exc_info=True)
        return _jsonrpc_error(req_id, -32603, f"Internal error listing skills: {e}")


# ─── skills/invoke handler ──────────────────────────────────────────────

async def _handle_skills_invoke(req_id: Optional[str], params: Dict[str, Any]) -> Dict:
    """
    Handle skills/invoke: execute a specific skill action.

    Expected params:
      - skill: str       — The skill name (e.g., "docker-management")
      - action: str      — The action name (e.g., "list_containers")
      - parameters: dict  — Parameters to pass to the executor (optional)

    The executor key is constructed as "{skill}__{action}".
    """
    skill_name = params.get("skill", "")
    action_name = params.get("action", "")
    action_params = params.get("parameters", {})

    if not skill_name:
        return _jsonrpc_error(req_id, -32602, "Missing required param: 'skill'")
    if not action_name:
        return _jsonrpc_error(req_id, -32602, "Missing required param: 'action'")

    # Build the executor key: "skill-name__action_name"
    executor_key = f"{skill_name}__{action_name}"

    executor = EXECUTOR_MAP.get(executor_key)
    if not executor:
        # Provide helpful error with available executors for this skill
        available = [k for k in EXECUTOR_MAP.keys() if k.startswith(f"{skill_name}__")]
        hint = f" Available actions for '{skill_name}': {available}" if available else f" Skill '{skill_name}' not found."
        return _jsonrpc_error(
            req_id, -32602,
            f"Unknown executor: '{executor_key}'.{hint}"
        )

    start_time = time.monotonic()
    success = True
    result_text = ""

    try:
        result_text = await executor(**action_params)
    except TypeError as e:
        # Parameter mismatch — provide a clear message
        result_text = f"Parameter error for {executor_key}: {e}"
        success = False
        logger.warning(f"A2A skills/invoke parameter error: {executor_key} — {e}")
    except Exception as e:
        result_text = f"Execution error: {e}"
        success = False
        logger.error(f"A2A skills/invoke execution error: {executor_key}", exc_info=True)

    duration_ms = int((time.monotonic() - start_time) * 1000)

    # Audit log (best effort) — scope by selected colonel for multi-Colonel deployments
    try:
        await log_action(
            colonel_id=_resolve_colonel_id(params),
            action_type="a2a_skill_invoke",
            skill_name=skill_name,
            action_name=action_name,
            parameters=action_params,
            result_summary=result_text[:500] if result_text else None,
            success=success,
            duration_ms=duration_ms,
        )
    except Exception:
        pass

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "status": "success" if success else "error",
            "data": {
                "output": result_text,
                "skill": skill_name,
                "action": action_name,
                "duration_ms": duration_ms,
            },
        },
    }


# ─── agent/status handler ──────────────────────────────────────────────

async def _handle_agent_status(req_id: Optional[str], params: Dict[str, Any]) -> Dict:
    """
    Handle agent/status: return Colonel status information.

    Returns the Colonel configuration, loaded skill count, and whether
    Brigade registration has been attempted. Honors an optional 'colonel'
    param to scope the response to a specific Colonel.
    """
    try:
        config = await get_colonel_config(_resolve_colonel_id(params))

        skill_count = 0
        executor_count = len(EXECUTOR_MAP)
        try:
            sr = SkillRouter()
            skill_count = len(sr.list_skills())
        except Exception:
            pass

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "status": "success",
                "data": {
                    "online": True,
                    "name": config.name,
                    "server_name": config.server_name,
                    "mission": config.mission,
                    "model": config.model,
                    "skills_loaded": skill_count,
                    "executors_loaded": executor_count,
                    "enabled_skills": config.enabled_skills,
                    "brigade_registered": _brigade_registered,
                },
            },
        }
    except Exception as e:
        logger.error(f"agent/status error: {e}", exc_info=True)
        return _jsonrpc_error(req_id, -32603, f"Internal error: {e}")


# ─── tasks/send handler (legacy) ───────────────────────────────────────

async def _handle_tasks_send(req_id: Optional[str], params: Dict[str, Any]) -> Dict:
    """Handle tasks/send: extract user message and route through skill system."""
    task_id = params.get("id") or str(uuid.uuid4())
    message = params.get("message", {})

    # Extract text from A2A message format
    parts = message.get("parts", [])
    text_content = ""
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            text_content += part.get("text", "")
        elif isinstance(part, str):
            text_content += part

    if not text_content:
        # Fallback: try direct content field
        text_content = message.get("content", "")

    if not text_content:
        return _jsonrpc_error(req_id, -32602, "No text content in message")

    # Execute through keyword-based routing
    result_text = ""

    try:
        tool_name, tool_args = _extract_skill_call(text_content)
        if tool_name:
            executor = EXECUTOR_MAP.get(tool_name)
            if executor:
                result_text = await executor(**tool_args)
            else:
                result_text = f"Skill '{tool_name}' found in keyword map but has no executor."
        else:
            result_text = (
                f"Received: {text_content}. "
                "No keyword match found. Use 'skills/invoke' method for direct skill execution, "
                "or the chat interface for conversational access."
            )
    except Exception as e:
        logger.error(f"A2A task execution error: {e}", exc_info=True)
        result_text = f"Error: {str(e)}"

    # Log to audit — scope by selected colonel for multi-Colonel deployments
    try:
        await log_action(
            colonel_id=_resolve_colonel_id(params),
            action_type="a2a_task",
            action_name="tasks/send",
            parameters={"text": text_content[:200]},
            result_summary=result_text[:200],
            success=True,
        )
    except Exception:
        pass

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "parts": [{"type": "text", "text": result_text}],
                }
            ],
        },
    }


# ─── colonels/list handler ─────────────────────────────────────────────

async def _handle_colonels_list(req_id: Optional[str], params: Dict[str, Any]) -> Dict:
    """
    Handle colonels/list: enumerate every Colonel registered on this server.

    Lets A2A clients discover all available Colonels in a multi-Colonel
    deployment via JSON-RPC, mirroring the HTTP /.well-known/api-catalog
    endpoint for callers that prefer to stay on the JSON-RPC channel.
    """
    try:
        colonels = await list_colonels()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "status": "success",
                "data": {
                    "colonels": colonels,
                    "count": len(colonels),
                },
            },
        }
    except Exception as e:
        logger.error(f"colonels/list error: {e}", exc_info=True)
        return _jsonrpc_error(req_id, -32603, f"Internal error listing colonels: {e}")


def _extract_skill_call(text: str) -> tuple:
    """
    Simple keyword-based skill extraction for A2A tasks/send requests.
    Returns (tool_name, args) or (None, None).
    """
    text_lower = text.lower()

    # Map common A2A requests to skill calls
    mappings = [
        (["list containers", "running containers", "docker ps"], "docker-management__list_containers", {}),
        (["system status", "server status"], "system-status__full_status", {}),
        (["cpu status", "cpu usage"], "system-status__cpu", {}),
        (["memory status", "ram usage"], "system-status__memory", {}),
        (["disk status", "disk usage"], "system-status__disk", {}),
        (["gpu status", "gpu memory"], "system-status__gpu", {}),
        (["health check", "service health"], "service-health__check_all", {}),
        (["top processes"], "system-status__processes", {"count": 10}),
        (["list databases", "show databases"], "postgresql-ops__list_databases", {}),
        (["gpu summary"], "gpu-monitoring__summary", {}),
        (["gpu temperatures", "gpu temp"], "gpu-monitoring__temperatures", {}),
        (["docker networks"], "network-diagnostics__list_docker_networks", {}),
        (["traefik routers", "list routers"], "traefik-management__list_routers", {}),
        (["traefik services"], "traefik-management__list_services", {}),
        (["litellm health", "llm health"], "litellm-management__health_check", {}),
        (["litellm models", "list models"], "litellm-management__list_models", {}),
    ]

    for keywords, tool_name, args in mappings:
        if any(kw in text_lower for kw in keywords):
            return (tool_name, args)

    return (None, None)


# ─── Brigade Registration ──────────────────────────────────────────────

_brigade_registered = False


async def register_with_brigade(base_url: str = ""):
    """
    Register Colonel as an agent with Brigade's A2A agent catalog.

    POSTs the Agent Card to Brigade's agent creation endpoint so that
    The General and other Brigade agents can discover and invoke Colonel.

    This function is fire-and-forget: it logs warnings on failure but never
    raises exceptions. If the first attempt fails, it retries once after
    30 seconds.

    Args:
        base_url: The external URL of this Ops-Center instance. If not
                  provided, falls back to EXTERNAL_HOST env var or localhost.
    """
    global _brigade_registered

    if not base_url:
        host = os.getenv("EXTERNAL_HOST", "localhost")
        protocol = os.getenv("EXTERNAL_PROTOCOL", "http")
        port = os.getenv("OPS_CENTER_PORT", "8084")
        base_url = f"{protocol}://{host}:{port}"

    logger.info(f"Attempting Colonel registration with Brigade at {BRIGADE_API_URL}...")

    for attempt in range(2):  # Try twice
        if attempt == 1:
            logger.info("Retrying Brigade registration in 30 seconds...")
            await asyncio.sleep(30)

        try:
            # Build the agent card
            config = await get_colonel_config()

            skills = []
            try:
                sr = SkillRouter()
                skills = sr.list_skills()
            except Exception as e:
                logger.warning(f"Could not load skills for registration: {e}")

            card = build_agent_card(config, skills, base_url)

            # Build the registration payload for Brigade's POST /api/v1/agents
            registration_payload = {
                "id": f"colonel-{config.id}",
                "name": config.name or "The Colonel",
                "displayName": f"{config.name or 'The Colonel'} ({config.server_name or 'Server'})",
                "bio": card["description"],
                "persona": (
                    f"I am {config.name or 'The Colonel'}, an AI command agent managing "
                    f"{config.server_name or 'this server'}. My mission is {config.mission or 'general'} "
                    f"server management. I can manage Docker containers, monitor system health, "
                    f"query databases, manage Traefik routing, and more."
                ),
                "domain": config.mission or "devops",
                "subdomain": "server-management",
                "status": "active",
                "capabilities": [
                    "docker-management",
                    "system-monitoring",
                    "service-health",
                    "database-ops",
                    "log-analysis",
                    "backup-management",
                ],
                "tools": [s.get("id", s.get("name", "")) for s in skills],
                "model": config.model,
                "temperature": config.temperature,
                "maxTokens": config.max_tokens,
                "requiresAuth": bool(A2A_SHARED_SECRET or BRIGADE_SERVICE_KEY),
                "pricingModel": "free",
                "metadata": {
                    "a2a_url": f"{base_url}/a2a",
                    "agent_card_url": f"{base_url}/.well-known/agent.json",
                    "source": "ops-center-colonel",
                    "server_name": config.server_name,
                    "version": "1.0.0",
                },
            }

            # Build request headers
            headers = {"Content-Type": "application/json"}
            if BRIGADE_SERVICE_KEY:
                headers["X-API-Key"] = BRIGADE_SERVICE_KEY

            async with httpx.AsyncClient(timeout=15.0) as client:
                # First, try to check if agent already exists
                agent_id = f"colonel-{config.id}"
                check_url = f"{BRIGADE_API_URL}/api/v1/agents/{agent_id}"

                try:
                    check_resp = await client.get(check_url, headers=headers)
                    if check_resp.status_code == 200:
                        # Agent exists — update it
                        update_url = f"{BRIGADE_API_URL}/api/v1/agents/{agent_id}"
                        resp = await client.put(
                            update_url,
                            json=registration_payload,
                            headers=headers,
                        )
                        if resp.status_code in (200, 201):
                            _brigade_registered = True
                            logger.info(
                                f"Colonel '{config.name}' updated in Brigade "
                                f"(agent_id={agent_id}, skills={len(skills)})"
                            )
                            return
                        else:
                            logger.warning(
                                f"Brigade agent update failed: {resp.status_code} — {resp.text[:200]}"
                            )
                except httpx.HTTPError:
                    pass  # Agent doesn't exist or Brigade unreachable — try create

                # Create agent in Brigade
                create_url = f"{BRIGADE_API_URL}/api/v1/agents"
                resp = await client.post(
                    create_url,
                    json=registration_payload,
                    headers=headers,
                )

                if resp.status_code in (200, 201):
                    _brigade_registered = True
                    logger.info(
                        f"Colonel '{config.name}' registered with Brigade "
                        f"(agent_id={agent_id}, skills={len(skills)})"
                    )
                    return
                elif resp.status_code == 409:
                    # Conflict — agent already exists (race condition)
                    _brigade_registered = True
                    logger.info(
                        f"Colonel '{config.name}' already registered in Brigade (409 Conflict)"
                    )
                    return
                else:
                    logger.warning(
                        f"Brigade registration attempt {attempt + 1} failed: "
                        f"{resp.status_code} — {resp.text[:200]}"
                    )

        except httpx.ConnectError:
            logger.warning(
                f"Brigade not reachable at {BRIGADE_API_URL} (attempt {attempt + 1}/2). "
                "Colonel will operate standalone."
            )
        except httpx.TimeoutException:
            logger.warning(
                f"Brigade registration timed out (attempt {attempt + 1}/2)."
            )
        except Exception as e:
            logger.warning(
                f"Brigade registration error (attempt {attempt + 1}/2): {e}"
            )

    logger.warning(
        "Brigade registration failed after 2 attempts. "
        "Colonel will operate standalone. A2A endpoint is still available."
    )


# ─── Helpers ────────────────────────────────────────────────────────────

def _jsonrpc_error(req_id: Optional[str], code: int, message: str) -> Dict:
    """Build a JSON-RPC 2.0 error response."""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
