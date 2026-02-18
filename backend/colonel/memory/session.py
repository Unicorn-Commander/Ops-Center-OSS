"""
Redis Session Manager for Colonel chat sessions.

Sessions are stored as JSON in Redis with a configurable TTL.
The TTL is extended on each activity to keep active sessions alive.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import redis.asyncio as aioredis

from colonel.config import REDIS_HOST, REDIS_PORT, SESSION_TTL

logger = logging.getLogger("colonel.memory.session")

SESSION_PREFIX = "colonel:session:"


class ColonelSessionManager:
    """Manages Colonel chat sessions in Redis."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
            )
        return self._redis

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        r = await self._get_redis()
        data = await r.get(f"{SESSION_PREFIX}{session_id}")
        if data:
            # Extend TTL on access
            await r.expire(f"{SESSION_PREFIX}{session_id}", SESSION_TTL)
            return json.loads(data)
        return None

    async def save(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data."""
        r = await self._get_redis()
        session_data["updated_at"] = datetime.utcnow().isoformat()
        await r.set(
            f"{SESSION_PREFIX}{session_id}",
            json.dumps(session_data, default=str),
            ex=SESSION_TTL,
        )

    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        r = await self._get_redis()
        deleted = await r.delete(f"{SESSION_PREFIX}{session_id}")
        return deleted > 0

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user, sorted by most recent."""
        r = await self._get_redis()
        sessions = []

        async for key in r.scan_iter(match=f"{SESSION_PREFIX}*", count=100):
            try:
                data = await r.get(key)
                if data:
                    session = json.loads(data)
                    if session.get("user_id") == user_id:
                        msg_count = len(session.get("messages", []))
                        # Derive title from first user message
                        title = session.get("title", "")
                        if not title:
                            for m in session.get("messages", []):
                                if m.get("role") == "user":
                                    content = m.get("content", "")
                                    title = content[:60] + ("..." if len(content) > 60 else "")
                                    break
                        sessions.append({
                            "id": session.get("id", key.replace(SESSION_PREFIX, "")),
                            "title": title or "New Session",
                            "created_at": session.get("created_at"),
                            "updated_at": session.get("updated_at"),
                            "message_count": msg_count,
                        })
            except Exception as e:
                logger.warning(f"Error reading session {key}: {e}")
                continue

        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    async def count_active(self) -> int:
        """Count total active sessions."""
        r = await self._get_redis()
        count = 0
        async for _ in r.scan_iter(match=f"{SESSION_PREFIX}*", count=100):
            count += 1
        return count


# Singleton
colonel_session_manager = ColonelSessionManager()
