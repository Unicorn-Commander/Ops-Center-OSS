"""
PostgreSQL Audit Logger for Colonel.

Writes immutable audit log entries for all Colonel actions.
Uses asyncpg for non-blocking database writes.
"""

import json
import logging
from typing import Optional, Dict, Any

from colonel.config import get_db_pool

logger = logging.getLogger("colonel.memory.audit")


async def log_action(
    colonel_id: str = "default",
    session_id: Optional[str] = None,
    user_id: str = "unknown",
    action_type: str = "chat",
    skill_name: Optional[str] = None,
    action_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result_summary: Optional[str] = None,
    success: bool = True,
    duration_ms: Optional[int] = None,
):
    """Write an audit log entry. Fails silently if DB is unavailable."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO colonel_audit_log
                    (colonel_id, session_id, user_id, action_type,
                     skill_name, action_name, parameters, result_summary,
                     success, duration_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                colonel_id, session_id, user_id, action_type,
                skill_name, action_name,
                json.dumps(parameters, default=str) if parameters else None,
                result_summary[:500] if result_summary else None,
                success, duration_ms,
            )
    except Exception as e:
        logger.warning(f"Failed to write audit log: {e}")


async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    action_type: Optional[str] = None,
    skill_name: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list:
    """Query the audit log with optional filters."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conditions = []
            params = []
            param_idx = 1

            if action_type:
                conditions.append(f"action_type = ${param_idx}")
                params.append(action_type)
                param_idx += 1
            if skill_name:
                conditions.append(f"skill_name = ${param_idx}")
                params.append(skill_name)
                param_idx += 1
            if user_id:
                conditions.append(f"user_id = ${param_idx}")
                params.append(user_id)
                param_idx += 1

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            params.extend([limit, offset])
            query = f"""
                SELECT id, colonel_id, session_id, user_id, action_type,
                       skill_name, action_name, parameters, result_summary,
                       success, duration_ms, created_at
                FROM colonel_audit_log
                {where}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """

            rows = await conn.fetch(query, *params)
            return [
                {
                    "id": row["id"],
                    "colonel_id": row["colonel_id"],
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "action_type": row["action_type"],
                    "skill_name": row["skill_name"],
                    "action_name": row["action_name"],
                    "parameters": json.loads(row["parameters"]) if row["parameters"] else None,
                    "result_summary": row["result_summary"],
                    "success": row["success"],
                    "duration_ms": row["duration_ms"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                }
                for row in rows
            ]
    except Exception as e:
        logger.warning(f"Failed to query audit log: {e}")
        return []
