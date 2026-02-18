"""
Skill Router - Maps LLM tool_calls to executor functions,
handles multi-step tool use loops and confirmation flow.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional

from fastapi import WebSocket

from colonel.models import (
    ColonelConfig,
    WSSkillStartFrame, WSSkillProgressFrame, WSSkillResultFrame,
    WSConfirmFrame,
)
from colonel.skill_loader import (
    load_all_skills, get_tool_definitions_for_skills,
    get_skill_descriptions as _get_skill_descriptions,
    get_confirmation_required,
)
from colonel.skill_executor import EXECUTOR_MAP
from colonel.safety import requires_confirmation

logger = logging.getLogger("colonel.skill_router")


class SkillRouter:
    """Routes tool calls from the LLM to skill executors."""

    def __init__(self):
        self.skills = load_all_skills()
        self._pending_confirmations: Dict[str, asyncio.Event] = {}
        self._confirmation_results: Dict[str, bool] = {}

    def get_tool_definitions(self, enabled_skills: List[str]) -> List[Dict[str, Any]]:
        """Get OpenAI function-calling tool definitions for enabled skills."""
        return get_tool_definitions_for_skills(self.skills, enabled_skills)

    def get_skill_descriptions(self, enabled_skills: List[str]) -> str:
        """Get human-readable skill descriptions for the system prompt."""
        return _get_skill_descriptions(self.skills, enabled_skills)

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills with their metadata."""
        result = []
        for skill_id, skill in self.skills.items():
            result.append({
                "id": skill_id,
                "name": skill.get("name", skill_id),
                "description": skill.get("description", ""),
                "actions": [
                    {
                        "name": a["name"],
                        "description": a.get("description", ""),
                        "confirmation_required": a.get("confirmation_required", False),
                    }
                    for a in skill.get("actions", [])
                ],
            })
        return result

    async def execute(
        self, ws: WebSocket, func_name: str, params: Dict[str, Any], config: ColonelConfig,
        write_enabled: bool = False,
    ) -> str:
        """
        Execute a skill action and return the result string.
        Sends progress frames over WebSocket.
        """
        # Parse skill and action name
        parts = func_name.split("__", 1)
        skill_name = parts[0] if parts else func_name
        action_name = parts[1] if len(parts) > 1 else func_name

        logger.info(f"Executing skill: {func_name} with params: {params}")

        # Check if confirmation is required by SKILL.md definition
        needs_confirm = get_confirmation_required(self.skills, func_name)

        # Also check safety patterns for bash commands
        confirm_reason = None
        if func_name == "bash-execution__run_command" and "command" in params:
            confirm_reason = requires_confirmation(params["command"])
            if confirm_reason:
                needs_confirm = True

        # ─── Confirmation flow ───────────────────────────────────────────
        if needs_confirm:
            confirm_id = str(uuid.uuid4())[:8]
            if not confirm_reason:
                confirm_reason = f"Execute {action_name} on {skill_name}?"

            await ws.send_json(WSConfirmFrame(
                id=confirm_id,
                skill_name=skill_name,
                action=action_name,
                description=confirm_reason,
                params=params,
            ).model_dump())

            event = asyncio.Event()
            self._pending_confirmations[confirm_id] = event
            try:
                await asyncio.wait_for(event.wait(), timeout=60.0)
                confirmed = self._confirmation_results.pop(confirm_id, False)
            except asyncio.TimeoutError:
                confirmed = False
                await ws.send_json(WSSkillResultFrame(
                    skill_name=skill_name, action=action_name,
                    success=False, output="Confirmation timed out (60s)",
                ).model_dump())
            finally:
                self._pending_confirmations.pop(confirm_id, None)
                self._confirmation_results.pop(confirm_id, None)

            if not confirmed:
                return "Action cancelled by user."

        # Send skill_start frame
        try:
            await ws.send_json(WSSkillStartFrame(
                skill_name=skill_name,
                action=action_name,
                params=params,
            ).model_dump())
        except Exception:
            pass

        # Inject _write_enabled for executors that need it
        exec_params = {**params}
        if write_enabled:
            exec_params["_write_enabled"] = True

        # Execute
        start_time = time.monotonic()
        try:
            executor = EXECUTOR_MAP.get(func_name)
            if not executor:
                result = f"Unknown skill action: {func_name}"
                success = False
            else:
                result = await executor(**exec_params)
                success = True
        except Exception as e:
            result = f"Skill execution error: {e}"
            success = False
            logger.error(f"Skill execution failed: {func_name}", exc_info=True)

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Send skill_result frame
        try:
            await ws.send_json(WSSkillResultFrame(
                skill_name=skill_name,
                action=action_name,
                success=success,
                output=result[:500],  # Truncate for WS frame (full result goes to LLM)
                duration_ms=duration_ms,
            ).model_dump())
        except Exception:
            pass

        # Audit log (best effort)
        try:
            from colonel.config import get_db_pool
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO colonel_audit_log
                        (colonel_id, action_type, skill_name, action_name, parameters, result_summary, success, duration_ms, user_id)
                    VALUES
                        ($1, 'skill_exec', $2, $3, $4, $5, $6, $7, $8)
                    """,
                    config.id, skill_name, action_name,
                    json.dumps(params, default=str),
                    result[:500],
                    success, duration_ms,
                    "system",  # user_id filled by gateway in production
                )
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

        return result

    async def handle_confirmation(self, confirm_id: str, confirmed: bool):
        """Handle user confirmation response."""
        self._confirmation_results[confirm_id] = confirmed
        event = self._pending_confirmations.get(confirm_id)
        if event:
            event.set()
