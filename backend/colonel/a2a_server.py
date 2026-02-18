"""
A2A (Agent-to-Agent) Server for The Colonel.

Implements the Google/Linux Foundation A2A protocol:
- GET /.well-known/agent.json → Agent Card
- POST /a2a → JSON-RPC 2.0 task execution

This allows Brigade (The General) and other agents to discover and
invoke The Colonel's skills programmatically.
"""

import json
import logging
import uuid
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from colonel.config import get_colonel_config
from colonel.skill_router import SkillRouter
from colonel.memory.audit import log_action

logger = logging.getLogger("colonel.a2a")


# ─── Agent Card ──────────────────────────────────────────────────────────

def build_agent_card(config, skills: List[Dict], base_url: str) -> Dict[str, Any]:
    """Build an A2A-compliant Agent Card."""
    return {
        "name": config.name or "The Colonel",
        "description": f"{config.name or 'The Colonel'} — AI command agent for {config.server_name or 'this server'}. Mission: {config.mission or 'general'}.",
        "url": f"{base_url}/a2a",
        "version": "1.0.0",
        "provider": {
            "organization": "Magic Unicorn Unconventional Technology & Stuff Inc",
            "url": "https://unicorncommander.com",
        },
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
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


# ─── Router ─────────────────────────────────────────────────────────────

router = APIRouter(tags=["a2a"])


@router.get("/.well-known/agent.json")
async def agent_card(request: Request):
    """Publish the Agent Card for discovery."""
    config = await get_colonel_config()

    skills = []
    try:
        sr = SkillRouter()
        skills = sr.list_skills()
    except Exception as e:
        logger.warning(f"Could not load skills for agent card: {e}")

    base_url = str(request.base_url).rstrip("/")
    card = build_agent_card(config, skills, base_url)
    return card


@router.post("/a2a")
async def a2a_endpoint(request: Request):
    """
    A2A JSON-RPC 2.0 endpoint.

    Supported methods:
      - tasks/send: Execute a task (skill invocation or chat)
      - tasks/get: Get task status (not implemented yet)
    """
    try:
        body = await request.json()
    except Exception:
        return _jsonrpc_error(None, -32700, "Parse error")

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if not method:
        return _jsonrpc_error(req_id, -32600, "Invalid Request: missing method")

    if method == "tasks/send":
        return await _handle_tasks_send(req_id, params)
    elif method == "tasks/get":
        return _jsonrpc_error(req_id, -32601, "tasks/get not yet implemented")
    else:
        return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")


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

    # Execute through skill router
    config = await get_colonel_config()
    result_text = ""

    try:
        sr = SkillRouter()
        # Try to match a skill directly from the text
        # For A2A, we do a simple keyword-based routing
        tool_name, tool_args = _extract_skill_call(text_content, sr, config)
        if tool_name:
            result_text = await sr.executors.get(tool_name, lambda **kw: "Unknown skill")(
                **tool_args
            ) if sr.executors.get(tool_name) else f"Skill {tool_name} not found"
        else:
            result_text = f"Received: {text_content}. Direct skill execution requires specific tool invocation. Use the chat interface for conversational access."
    except Exception as e:
        logger.error(f"A2A task execution error: {e}", exc_info=True)
        result_text = f"Error: {str(e)}"

    # Log to audit
    try:
        await log_action(
            colonel_id="default",
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


def _extract_skill_call(text: str, sr, config) -> tuple:
    """
    Simple keyword-based skill extraction for A2A requests.
    Returns (tool_name, args) or (None, None).
    """
    text_lower = text.lower()

    # Map common A2A requests to skill calls
    mappings = [
        (["list containers", "running containers", "docker ps"], "docker-management__list_containers", {}),
        (["system status", "server status"], "system-status__full_status", {}),
        (["cpu status", "cpu usage"], "system-status__cpu_status", {}),
        (["memory status", "ram usage"], "system-status__memory_status", {}),
        (["disk status", "disk usage"], "system-status__disk_status", {}),
        (["gpu status", "gpu memory"], "system-status__gpu_status", {}),
        (["health check", "service health"], "service-health__check_all", {}),
        (["top processes"], "system-status__top_processes", {"count": 10}),
    ]

    for keywords, tool_name, args in mappings:
        if any(kw in text_lower for kw in keywords):
            return (tool_name, args)

    return (None, None)


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
