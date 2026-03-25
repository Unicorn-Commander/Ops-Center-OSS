"""
PostgreSQL Persistence Layer for Colonel Conversations.

Provides durable storage for Colonel chat sessions. Redis remains the
primary fast store; this module is the fallback and permanent archive.

All operations degrade gracefully -- if PostgreSQL is unavailable the
caller gets None / empty results and a log warning, never an exception.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from colonel.config import get_db_pool

logger = logging.getLogger("colonel.persistence")


# ─── Public API ───────────────────────────────────────────────────────────────


async def save_conversation(
    session_id: str,
    user_id: str,
    title: Optional[str],
    messages: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    colonel_name: str = "Col. Corelli",
) -> bool:
    """
    Upsert a conversation and its messages into PostgreSQL.

    This is designed to be called fire-and-forget via asyncio.create_task()
    so it never blocks the chat flow.

    Returns True on success, False on failure.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Upsert the conversation row
                row = await conn.fetchrow(
                    """
                    INSERT INTO colonel_conversations
                        (session_id, user_id, title, colonel_name,
                         message_count, metadata, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        title = COALESCE(EXCLUDED.title, colonel_conversations.title),
                        message_count = EXCLUDED.message_count,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING id
                    """,
                    session_id,
                    user_id,
                    title,
                    colonel_name,
                    len(messages),
                    json.dumps(metadata or {}, default=str),
                )
                conversation_id = row["id"]

                # Delete existing messages and re-insert (simplest upsert
                # strategy for an ordered list that may have grown).
                await conn.execute(
                    "DELETE FROM colonel_messages WHERE conversation_id = $1",
                    conversation_id,
                )

                if messages:
                    # Build batch insert values
                    records = []
                    for idx, msg in enumerate(messages):
                        msg_metadata = {}
                        if msg.get("tool_call_id"):
                            msg_metadata["tool_call_id"] = msg["tool_call_id"]
                        if msg.get("tool_calls"):
                            msg_metadata["tool_calls"] = msg["tool_calls"]
                        if msg.get("name"):
                            msg_metadata["name"] = msg["name"]
                        if msg.get("id"):
                            msg_metadata["msg_id"] = msg["id"]
                        if msg.get("timestamp"):
                            msg_metadata["timestamp"] = msg["timestamp"]

                        records.append((
                            conversation_id,
                            msg.get("role", "user"),
                            msg.get("content", ""),
                            idx,
                            json.dumps(msg_metadata, default=str),
                        ))

                    await conn.executemany(
                        """
                        INSERT INTO colonel_messages
                            (conversation_id, role, content, message_index, metadata)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        records,
                    )

        logger.debug(
            f"Persisted conversation {session_id}: "
            f"{len(messages)} messages"
        )
        return True

    except Exception as e:
        logger.warning(f"Failed to persist conversation {session_id}: {e}")
        return False


async def load_conversation(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation and its messages from PostgreSQL.

    Returns a dict compatible with the Redis session format, or None.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conv = await conn.fetchrow(
                """
                SELECT id, session_id, user_id, title, colonel_name,
                       created_at, updated_at, message_count, metadata
                FROM colonel_conversations
                WHERE session_id = $1
                """,
                session_id,
            )
            if not conv:
                return None

            rows = await conn.fetch(
                """
                SELECT role, content, message_index, metadata, created_at
                FROM colonel_messages
                WHERE conversation_id = $1
                ORDER BY message_index ASC
                """,
                conv["id"],
            )

            messages = []
            for r in rows:
                msg: Dict[str, Any] = {
                    "role": r["role"],
                    "content": r["content"],
                }
                if r["metadata"]:
                    try:
                        meta = json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"]
                    except (json.JSONDecodeError, TypeError):
                        meta = {}
                    if meta.get("tool_call_id"):
                        msg["tool_call_id"] = meta["tool_call_id"]
                    if meta.get("tool_calls"):
                        msg["tool_calls"] = meta["tool_calls"]
                    if meta.get("name"):
                        msg["name"] = meta["name"]
                    if meta.get("msg_id"):
                        msg["id"] = meta["msg_id"]
                    if meta.get("timestamp"):
                        msg["timestamp"] = meta["timestamp"]
                messages.append(msg)

            conv_metadata = {}
            if conv["metadata"]:
                try:
                    conv_metadata = json.loads(conv["metadata"]) if isinstance(conv["metadata"], str) else conv["metadata"]
                except (json.JSONDecodeError, TypeError):
                    conv_metadata = {}

            return {
                "id": session_id,
                "user_id": conv["user_id"],
                "title": conv["title"],
                "colonel_name": conv["colonel_name"],
                "messages": messages,
                "created_at": conv["created_at"].isoformat() if conv["created_at"] else None,
                "updated_at": conv["updated_at"].isoformat() if conv["updated_at"] else None,
                "message_count": conv["message_count"],
                "metadata": conv_metadata,
            }

    except Exception as e:
        logger.warning(f"Failed to load conversation {session_id} from PostgreSQL: {e}")
        return None


async def list_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List a user's conversations (metadata only, no messages).

    Returns a list of dicts with id, title, created_at, updated_at,
    message_count -- matching the format from Redis list_for_user().
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT session_id, title, created_at, updated_at, message_count
                FROM colonel_conversations
                WHERE user_id = $1
                ORDER BY updated_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )

            return [
                {
                    "id": r["session_id"],
                    "title": r["title"] or "New Session",
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                    "message_count": r["message_count"] or 0,
                }
                for r in rows
            ]

    except Exception as e:
        logger.warning(f"Failed to list conversations for user {user_id}: {e}")
        return []


async def delete_conversation(session_id: str) -> bool:
    """
    Delete a conversation and its messages from PostgreSQL.

    Returns True if a row was deleted, False otherwise.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM colonel_conversations WHERE session_id = $1",
                session_id,
            )
            deleted = result.endswith("1")  # "DELETE 1" or "DELETE 0"
            if deleted:
                logger.debug(f"Deleted conversation {session_id} from PostgreSQL")
            return deleted

    except Exception as e:
        logger.warning(f"Failed to delete conversation {session_id} from PostgreSQL: {e}")
        return False
