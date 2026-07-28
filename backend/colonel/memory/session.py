"""
Redis + PostgreSQL Session Manager for Colonel chat sessions.

Redis is the PRIMARY store for active sessions (fast reads, TTL-based expiry).
PostgreSQL is the DURABLE store for permanent history (survives restarts).

Dual-write: saves go to both Redis and PostgreSQL.
Fallback:   loads try Redis first, then PostgreSQL if Redis misses.
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import redis.asyncio as aioredis

from colonel.config import REDIS_HOST, REDIS_PORT, SESSION_TTL
from colonel import persistence

logger = logging.getLogger("colonel.memory.session")

SESSION_PREFIX = "colonel:session:"


class ColonelSessionManager:
    """Manages Colonel chat sessions in Redis with PostgreSQL persistence."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
            )
        return self._redis

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID. Tries Redis first, falls back to PostgreSQL."""
        # Try Redis first (fast path)
        r = await self._get_redis()
        data = await r.get(f"{SESSION_PREFIX}{session_id}")
        if data:
            # Extend TTL on access
            await r.expire(f"{SESSION_PREFIX}{session_id}", SESSION_TTL)
            return json.loads(data)

        # Redis miss -- fall back to PostgreSQL
        logger.debug(f"Redis miss for session {session_id}, trying PostgreSQL")
        pg_data = await persistence.load_conversation(session_id)
        if pg_data:
            # Re-hydrate into Redis so subsequent reads are fast
            try:
                pg_data["updated_at"] = pg_data.get("updated_at") or datetime.utcnow().isoformat()
                await r.set(
                    f"{SESSION_PREFIX}{session_id}",
                    json.dumps(pg_data, default=str),
                    ex=SESSION_TTL,
                )
                logger.info(f"Re-hydrated session {session_id} from PostgreSQL into Redis")
            except Exception as e:
                logger.warning(f"Failed to re-hydrate session {session_id} into Redis: {e}")
            return pg_data

        return None

    async def save(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data to Redis, and persist to PostgreSQL (fire-and-forget)."""
        # 1. Write to Redis (primary, blocking)
        r = await self._get_redis()
        session_data["updated_at"] = datetime.utcnow().isoformat()
        await r.set(
            f"{SESSION_PREFIX}{session_id}",
            json.dumps(session_data, default=str),
            ex=SESSION_TTL,
        )

        # 2. Write to PostgreSQL (secondary, fire-and-forget)
        asyncio.create_task(
            self._persist_to_pg(session_id, session_data)
        )

    async def _persist_to_pg(self, session_id: str, session_data: Dict[str, Any]):
        """Background task: persist session to PostgreSQL. Never raises."""
        try:
            await persistence.save_conversation(
                session_id=session_id,
                user_id=session_data.get("user_id", "unknown"),
                title=session_data.get("title"),
                messages=session_data.get("messages", []),
                metadata={
                    k: v for k, v in session_data.items()
                    if k not in ("id", "user_id", "title", "messages",
                                 "created_at", "updated_at")
                },
                colonel_name=session_data.get("colonel_name", "The Colonel"),
            )
        except Exception as e:
            logger.warning(f"Background persist failed for {session_id}: {e}")

    async def delete(self, session_id: str) -> bool:
        """Delete a session from both Redis and PostgreSQL."""
        # Delete from Redis
        r = await self._get_redis()
        deleted = await r.delete(f"{SESSION_PREFIX}{session_id}")

        # Also delete from PostgreSQL (fire-and-forget)
        asyncio.create_task(
            self._delete_from_pg(session_id)
        )

        return deleted > 0

    async def _delete_from_pg(self, session_id: str):
        """Background task: delete from PostgreSQL. Never raises."""
        try:
            await persistence.delete_conversation(session_id)
        except Exception as e:
            logger.warning(f"Background delete failed for {session_id}: {e}")

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all sessions for a user, merging Redis and PostgreSQL.

        Redis sessions are returned first (most current). PostgreSQL
        sessions that are not in Redis are appended (older / expired).
        The combined list is deduplicated by session id and sorted by
        most recent update.
        """
        # Gather Redis sessions
        r = await self._get_redis()
        redis_sessions: Dict[str, Dict[str, Any]] = {}

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
                        sid = session.get("id", key.replace(SESSION_PREFIX, ""))
                        redis_sessions[sid] = {
                            "id": sid,
                            "title": title or "New Session",
                            "created_at": session.get("created_at"),
                            "updated_at": session.get("updated_at"),
                            "message_count": msg_count,
                        }
            except Exception as e:
                logger.warning(f"Error reading session {key}: {e}")
                continue

        # Gather PostgreSQL sessions (includes expired Redis sessions)
        pg_sessions = await persistence.list_conversations(user_id, limit=100)

        # Merge: Redis wins for duplicates, PG fills in the rest
        merged: Dict[str, Dict[str, Any]] = {}
        for s in pg_sessions:
            merged[s["id"]] = s
        for sid, s in redis_sessions.items():
            merged[sid] = s  # Redis overwrites PG for same id

        sessions = list(merged.values())
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    async def count_active(self) -> int:
        """Count total active sessions (Redis only -- these are the live ones)."""
        r = await self._get_redis()
        count = 0
        async for _ in r.scan_iter(match=f"{SESSION_PREFIX}*", count=100):
            count += 1
        return count


# Singleton
colonel_session_manager = ColonelSessionManager()
