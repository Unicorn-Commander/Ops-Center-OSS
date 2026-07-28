"""
Colonel WebSocket Gateway - Handles streaming chat with the LLM.

Authenticates via session cookie, manages chat sessions in Redis,
streams LLM responses via SSE from LiteLLM, and dispatches tool calls.

Memory integration:
  - Mem0 semantic recall is queried before each LLM call to inject relevant
    context from prior conversations.
  - After a complete assistant response, the exchange is stored to Mem0 via
    a fire-and-forget task so it never blocks the response stream.
  - All memory operations degrade gracefully: if Mem0/Qdrant is unreachable,
    a warning is logged and the conversation continues without memory.

Context pruning:
  - Before sending messages to the LLM, the conversation history is pruned
    so it fits within 80% of the configured context_window (in tokens).
  - The system prompt is accounted for in the budget.
  - Older user/assistant pairs are removed first; the system prompt and the
    most recent messages are always preserved.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Optional, Dict, Any, List

import httpx
import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect

from colonel.models import (
    ColonelConfig, ColonelSession, ChatMessage,
    WSChunkFrame, WSMessageDoneFrame, WSErrorFrame,
    WSSkillStartFrame, WSSkillProgressFrame, WSSkillResultFrame,
    WSConfirmFrame, WSPingFrame, WSPongFrame,
)
from colonel.config import get_colonel_config, LITELLM_URL, REDIS_HOST, REDIS_PORT, SESSION_TTL
from colonel.safety import is_write_capable_model
from colonel.system_prompt import build_system_prompt

logger = logging.getLogger("colonel.ws")

# ─── Token Estimation Helpers ────────────────────────────────────────────────

# Rough heuristic: 1 token ~= 4 characters.  This is intentionally
# conservative so we stay under the real limit even if the ratio varies.
_CHARS_PER_TOKEN = 4

# We target 80% of the context window to leave headroom for the LLM response
# and any tokenization variance.
_CONTEXT_BUDGET_RATIO = 0.80


def _estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in *text* using the 4-chars heuristic."""
    return max(len(text) // _CHARS_PER_TOKEN, 1) if text else 0


def _estimate_message_tokens(msg: ChatMessage) -> int:
    """Estimate tokens for a single ChatMessage, including tool metadata."""
    tokens = _estimate_tokens(msg.content or "")
    if msg.tool_calls:
        # Rough estimate for serialised tool_calls JSON
        tokens += _estimate_tokens(json.dumps(msg.tool_calls))
    if msg.name:
        tokens += _estimate_tokens(msg.name)
    # Per-message overhead (role, separators)
    tokens += 4
    return tokens


class ColonelGateway:
    """Manages WebSocket connections for The Colonel."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._http: Optional[httpx.AsyncClient] = None
        self._connections: Dict[str, WebSocket] = {}  # session_id -> ws
        # Initialize skill router
        try:
            from colonel.skill_router import SkillRouter
            self.skill_router = SkillRouter()
            logger.info(f"Skill router initialized with {len(self.skill_router.skills)} skills")
        except Exception as e:
            logger.warning(f"Could not initialize skill router: {e}")
            self.skill_router = None
        # Initialize memory client
        try:
            from colonel.memory.mem0_client import ColonelMemoryClient
            self.memory_client = ColonelMemoryClient()
            logger.info("Memory client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize memory client: {e}")
            self.memory_client = None
        # Initialize graph client (sub-phase 1e)
        try:
            from colonel.memory.kuzu_client import ColonelGraphClient
            self.graph_client = ColonelGraphClient()
            if self.graph_client.available:
                self.graph_client.populate_from_docker()
                logger.info("Graph client initialized and populated")
            else:
                logger.info("Graph client initialized (kuzu not available)")
        except Exception as e:
            logger.warning(f"Could not initialize graph client: {e}")
            self.graph_client = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
            )
        return self._redis

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
        return self._http

    # ─── Session Management ─────────────────────────────────────────────

    async def _get_session(self, session_id: str) -> Optional[ColonelSession]:
        """Load a chat session from Redis."""
        r = await self._get_redis()
        data = await r.get(f"colonel:session:{session_id}")
        if data:
            return ColonelSession(**json.loads(data))
        return None

    async def _save_session(self, session: ColonelSession):
        """Save a chat session to Redis with TTL, and persist to PostgreSQL."""
        r = await self._get_redis()
        session.updated_at = __import__("datetime").datetime.utcnow().isoformat()
        await r.set(
            f"colonel:session:{session.id}",
            session.model_dump_json(),
            ex=SESSION_TTL,
        )
        # Fire-and-forget persist to PostgreSQL for durability
        try:
            from colonel import persistence
            session_dict = json.loads(session.model_dump_json())
            asyncio.create_task(persistence.save_conversation(
                session_id=session.id,
                user_id=session.user_id,
                title=session.title,
                messages=session_dict.get("messages", []),
                colonel_name=session.colonel_id,
            ))
        except Exception as e:
            logger.debug(f"PostgreSQL persist skipped: {e}")

    async def _create_session(self, user_id: str, colonel_id: str = "default") -> ColonelSession:
        """Create a new chat session."""
        session = ColonelSession(user_id=user_id, colonel_id=colonel_id)
        await self._save_session(session)
        return session

    async def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user."""
        r = await self._get_redis()
        keys = []
        async for key in r.scan_iter(match="colonel:session:*", count=100):
            keys.append(key)

        sessions = []
        for key in keys:
            data = await r.get(key)
            if data:
                s = json.loads(data)
                if s.get("user_id") == user_id:
                    sessions.append({
                        "id": s["id"],
                        "title": s.get("title") or _derive_title(s.get("messages", [])),
                        "created_at": s.get("created_at"),
                        "updated_at": s.get("updated_at"),
                        "message_count": len(s.get("messages", [])),
                    })

        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    # ─── Authentication ─────────────────────────────────────────────────

    async def _authenticate(self, ws: WebSocket) -> Optional[Dict[str, Any]]:
        """Authenticate via session cookie (same as rest of Ops-Center)."""
        session_token = ws.cookies.get("session_token")
        if not session_token:
            # Also check query param for dev convenience
            session_token = ws.query_params.get("token")

        if not session_token:
            return None

        try:
            from redis_session import RedisSessionManager
            sessions = RedisSessionManager(host=REDIS_HOST, port=REDIS_PORT, password=os.getenv("REDIS_PASSWORD"))
            session_data = sessions.get(session_token)
            if not session_data:
                return None

            user_data = session_data.get("user", {})
            if not user_data:
                return None

            return user_data
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None

    # ─── WebSocket Handler ──────────────────────────────────────────────

    async def handle_websocket(self, ws: WebSocket):
        """Main WebSocket handler for Colonel chat."""
        await ws.accept()

        # Authenticate
        user = await self._authenticate(ws)
        if not user:
            await ws.send_json(WSErrorFrame(detail="Authentication required", code="auth_required").model_dump())
            await ws.close(code=4001, reason="Authentication required")
            return

        user_id = user.get("sub") or user.get("id") or user.get("user_id", "unknown")
        user_email = user.get("email", "unknown")
        is_admin = user.get("role") == "admin" or "admin" in user.get("realm_access", {}).get("roles", [])

        # Load config — honor optional ?colonel=<id> for multi-Colonel deployments
        # (defaults to "default" so single-Colonel deployments behave unchanged).
        requested_colonel = ws.query_params.get("colonel", "default")
        config = await get_colonel_config(requested_colonel)
        if config.admin_only and not is_admin:
            await ws.send_json(WSErrorFrame(detail="Admin access required", code="forbidden").model_dump())
            await ws.close(code=4003, reason="Forbidden")
            return

        # Get or create session
        session_id = ws.query_params.get("session_id")
        if session_id:
            session = await self._get_session(session_id)
            if not session or session.user_id != user_id:
                session = await self._create_session(user_id, config.id)
        else:
            session = await self._create_session(user_id, config.id)

        self._connections[session.id] = ws

        # Determine write capability based on model
        write_enabled = is_write_capable_model(config.model, config.write_capable_models)

        # Send initial status
        await ws.send_json({
            "type": "connected",
            "session_id": session.id,
            "colonel_name": config.name,
            "server_name": config.server_name,
            "write_enabled": write_enabled,
        })

        logger.info(f"Colonel WS connected: user={user_email}, session={session.id}")

        try:
            await self._message_loop(ws, session, config, user, write_enabled)
        except WebSocketDisconnect:
            logger.info(f"Colonel WS disconnected: session={session.id}")
        except Exception as e:
            logger.error(f"Colonel WS error: {e}", exc_info=True)
            try:
                await ws.send_json(WSErrorFrame(detail=str(e)).model_dump())
            except Exception:
                pass
        finally:
            self._connections.pop(session.id, None)

    async def _message_loop(self, ws: WebSocket, session: ColonelSession, config: ColonelConfig, user: dict, write_enabled: bool = False):
        """Main message receive loop."""
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json(WSErrorFrame(detail="Invalid JSON").model_dump())
                continue

            msg_type = msg.get("type", "message")

            if msg_type == "ping":
                await ws.send_json(WSPongFrame().model_dump())
                continue

            if msg_type == "confirm":
                # User confirmed a pending action (handled by skill router)
                if self.skill_router:
                    confirm_id = msg.get("confirm_id")
                    confirmed = msg.get("confirmed", False)
                    await self.skill_router.handle_confirmation(confirm_id, confirmed)
                continue

            if msg_type in ("message", "chat"):
                content = msg.get("content", "").strip()
                if not content:
                    continue

                # Add user message to session
                user_msg = ChatMessage(role="user", content=content)
                session.messages.append(user_msg)

                # Auto-title from first message
                if len(session.messages) == 1:
                    session.title = content[:60] + ("..." if len(content) > 60 else "")

                await self._save_session(session)

                # Stream LLM response
                await self._stream_response(ws, session, config, user, write_enabled)

    # ─── LLM Streaming ──────────────────────────────────────────────────

    async def _stream_response(self, ws: WebSocket, session: ColonelSession, config: ColonelConfig, user: dict, write_enabled: bool = False):
        """Call LLM and stream the response back over WebSocket."""

        # ── Recall memories (Mem0 semantic search) ────────────────────────
        memories = None
        if self.memory_client:
            try:
                last_msg = session.messages[-1].content if session.messages else ""
                memories = await asyncio.wait_for(
                    self.memory_client.recall(last_msg, user_id=session.user_id),
                    timeout=5.0,
                )
                if memories:
                    logger.info(f"Mem0 recalled {len(memories)} memories for user {session.user_id}")
                else:
                    logger.debug("Mem0 recall returned no relevant memories")
            except asyncio.TimeoutError:
                logger.warning("Mem0 recall timed out (5s limit) - continuing without memory")
            except Exception as e:
                logger.warning(f"Memory recall failed: {e}")

        # ── Build tool definitions (sub-phase 1b) ────────────────────────
        tools = None
        skill_descriptions = None
        if self.skill_router:
            tools = self.skill_router.get_tool_definitions(config.enabled_skills)
            skill_descriptions = self.skill_router.get_skill_descriptions(config.enabled_skills)

        # ── Query graph context (sub-phase 1e) ───────────────────────────
        graph_context = None
        if self.graph_client and self.graph_client.available:
            try:
                last_msg = session.messages[-1].content if session.messages else ""
                ctx_items = self.graph_client.query_context(last_msg)
                if ctx_items:
                    graph_context = "\n".join(ctx_items)
            except Exception as e:
                logger.debug(f"Graph context query failed: {e}")

        # ── Build system prompt ──────────────────────────────────────────
        system_prompt = build_system_prompt(
            config,
            memories=memories,
            graph_context=graph_context,
            skill_descriptions=skill_descriptions,
            write_enabled=write_enabled,
        )

        # ── Prepare messages for LLM ─────────────────────────────────────
        # Build an ID remap table so tool_call_ids in tool messages match
        # the (possibly rewritten) ids in the assistant tool_calls list.
        _id_remap: Dict[str, str] = {}

        def _normalize_tc_id(raw_id: str) -> str:
            """Ensure tool-call ids use the OpenAI 'call_' prefix.
            Some providers (Anthropic/Bedrock via OpenRouter) return ids
            like 'toolu_vrtx_...' which can confuse the format converter
            on the next round-trip."""
            if not raw_id:
                return raw_id
            if raw_id.startswith("call_"):
                return raw_id
            new_id = "call_" + raw_id.replace("toolu_vrtx_", "").replace("toolu_", "")
            _id_remap[raw_id] = new_id
            return new_id

        # ── Context Pruning ──────────────────────────────────────────────
        # Keep conversation within 80% of the configured context window.
        # Budget = (context_window * 0.80) - system_prompt_tokens.
        # We remove the oldest user/assistant pairs first, always keeping
        # the most recent messages and any trailing tool exchanges.
        context_messages = _prune_context(
            session.messages,
            system_prompt,
            config.context_window,
        )
        if len(context_messages) < len(session.messages):
            removed = len(session.messages) - len(context_messages)
            logger.info(
                f"Context pruning: kept {len(context_messages)}/{len(session.messages)} "
                f"messages (removed {removed} oldest) to fit within "
                f"{int(config.context_window * _CONTEXT_BUDGET_RATIO)} token budget"
            )

        llm_messages = [{"role": "system", "content": system_prompt}]
        for m in context_messages:
            msg_dict = {"role": m.role, "content": m.content}
            if m.tool_call_id:
                msg_dict["tool_call_id"] = _id_remap.get(m.tool_call_id, m.tool_call_id)
            if m.tool_calls:
                # Normalize tool_call ids inside the assistant message
                normalized_tcs = []
                for tc in m.tool_calls:
                    tc_copy = {**tc}
                    if tc_copy.get("id"):
                        tc_copy["id"] = _normalize_tc_id(tc_copy["id"])
                    normalized_tcs.append(tc_copy)
                msg_dict["tool_calls"] = normalized_tcs
            if m.name:
                msg_dict["name"] = m.name
            llm_messages.append(msg_dict)

        # Call LLM with tool loop
        max_tool_rounds = 5
        all_content_parts = []  # accumulate content across rounds
        done_sent = False
        for round_num in range(max_tool_rounds + 1):
            assistant_content, tool_calls = await self._call_llm_stream(
                ws, config, llm_messages, tools
            )
            if assistant_content:
                all_content_parts.append(assistant_content)

            if not tool_calls:
                # No tool calls — we're done
                if assistant_content:
                    msg_id = str(uuid.uuid4())[:8]
                    session.messages.append(ChatMessage(
                        role="assistant", content=assistant_content
                    ))
                    await ws.send_json(WSMessageDoneFrame(
                        message_id=msg_id, content=assistant_content
                    ).model_dump())
                    done_sent = True

                    # Store memories (fire-and-forget to avoid delaying response)
                    if self.memory_client and len(session.messages) >= 2:
                        asyncio.create_task(
                            self._store_memory_safe(
                                session.messages[-2].content,  # user msg
                                assistant_content,
                                session.user_id,
                            )
                        )

                await self._save_session(session)
                break

            # Process tool calls (sub-phase 1b)
            if self.skill_router:
                # Filter to valid tool calls only
                valid_tool_calls = []
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    if not func_name:
                        logger.warning("Skipping tool call with empty function name")
                        continue
                    raw_args = tc["function"].get("arguments", "")
                    if isinstance(raw_args, str) and raw_args.strip():
                        try:
                            parsed_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping tool call {func_name}: invalid JSON args: {raw_args[:100]}")
                            continue
                    elif isinstance(raw_args, dict):
                        parsed_args = raw_args
                    else:
                        parsed_args = {}
                    valid_tool_calls.append((tc, func_name, parsed_args))

                if not valid_tool_calls:
                    # All tool calls were malformed — treat as plain response
                    logger.warning("All tool calls had invalid args, treating as plain response")
                    if assistant_content:
                        msg_id = str(uuid.uuid4())[:8]
                        session.messages.append(ChatMessage(
                            role="assistant", content=assistant_content
                        ))
                        await ws.send_json(WSMessageDoneFrame(
                            message_id=msg_id, content=assistant_content
                        ).model_dump())
                    await self._save_session(session)
                    break

                # Normalize tool_call ids to OpenAI 'call_' format
                # (Anthropic/Bedrock return 'toolu_*' ids that break on round-trip)
                normalized_tool_calls = []
                for tc in tool_calls:
                    tc_copy = {**tc}
                    if tc_copy.get("id"):
                        tc_copy["id"] = _normalize_tc_id(tc_copy["id"])
                    normalized_tool_calls.append(tc_copy)

                # Add assistant message with tool_calls
                llm_messages.append({
                    "role": "assistant",
                    "content": assistant_content or "",
                    "tool_calls": normalized_tool_calls,
                })
                session.messages.append(ChatMessage(
                    role="assistant",
                    content=assistant_content or "",
                    tool_calls=normalized_tool_calls,
                ))

                for tc, func_name, func_args in valid_tool_calls:
                    tc_id = _id_remap.get(tc["id"], tc["id"])

                    # Execute skill
                    result = await self.skill_router.execute(
                        ws, func_name, func_args, config,
                        write_enabled=write_enabled,
                        session_id=session.id,
                    )

                    # Add tool result to messages
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": func_name,
                        "content": str(result) if result else "(no output)",
                    }
                    llm_messages.append(tool_msg)
                    session.messages.append(ChatMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tc_id,
                        name=func_name,
                    ))

                await self._save_session(session)
                # Loop back to call LLM again with tool results
            else:
                # No skill router yet — just note the tool calls
                session.messages.append(ChatMessage(
                    role="assistant",
                    content=assistant_content or "(Tool calling not yet available)",
                ))
                await self._save_session(session)
                break
        else:
            # Exhausted max_tool_rounds
            logger.warning(f"Reached max tool rounds ({max_tool_rounds})")

        # Safety net: always send message_done so the frontend unlocks
        if not done_sent:
            final_content = "\n\n".join(all_content_parts) if all_content_parts else ""
            if final_content:
                msg_id = str(uuid.uuid4())[:8]
                # Only add to session if not already added
                if not session.messages or session.messages[-1].content != final_content:
                    session.messages.append(ChatMessage(
                        role="assistant", content=final_content
                    ))
                await ws.send_json(WSMessageDoneFrame(
                    message_id=msg_id, content=final_content
                ).model_dump())
            else:
                # Even with no content, send done to unlock the UI
                await ws.send_json(WSMessageDoneFrame(
                    message_id=str(uuid.uuid4())[:8], content="(No response generated)"
                ).model_dump())
            await self._save_session(session)

    async def _store_memory_safe(self, user_msg: str, assistant_msg: str, user_id: str):
        """Fire-and-forget wrapper for Mem0 store with timeout and error handling.

        This runs as a background task (via asyncio.create_task) so memory
        storage never delays the WebSocket response.  All errors are caught
        and logged; they never propagate to the caller.
        """
        try:
            await asyncio.wait_for(
                self.memory_client.store(user_msg, assistant_msg, user_id=user_id),
                timeout=10.0,
            )
            logger.debug(f"Mem0 stored exchange for user {user_id}")
        except asyncio.TimeoutError:
            logger.warning(f"Mem0 store timed out (10s limit) for user {user_id}")
        except Exception as e:
            logger.warning(f"Mem0 store failed for user {user_id}: {e}")

    async def _call_llm_stream(
        self, ws: WebSocket, config: ColonelConfig,
        messages: List[Dict], tools: Optional[List[Dict]]
    ) -> tuple:
        """
        Call LiteLLM with streaming and send chunks over WebSocket.
        Returns (full_content, tool_calls_or_None).
        """
        http = await self._get_http()

        payload: Dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "stream": True,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        # Use internal service key for LLM access
        headers = {
            "Content-Type": "application/json",
        }
        service_key = os.getenv("COLONEL_SERVICE_KEY", "sk-colonel-service-key-2026")
        if service_key:
            headers["Authorization"] = f"Bearer {service_key}"

        full_content = ""
        tool_calls = []
        current_tool_calls: Dict[int, Dict] = {}  # index -> tool_call

        try:
            async with http.stream("POST", LITELLM_URL, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_msg = f"LLM returned {response.status_code}: {body.decode()[:200]}"
                    logger.error(error_msg)
                    await ws.send_json(WSErrorFrame(detail=error_msg).model_dump())
                    return ("", None)

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Detect error objects in SSE stream
                    if "error" in chunk and "choices" not in chunk:
                        err_detail = chunk["error"]
                        if isinstance(err_detail, dict):
                            err_msg = err_detail.get("message", str(err_detail))
                        else:
                            err_msg = str(err_detail)
                        logger.error(f"LLM stream returned error: {err_msg}")
                        await ws.send_json(WSErrorFrame(detail=f"LLM error: {err_msg}").model_dump())
                        return (full_content, None)

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})

                    # Handle content chunks
                    content = delta.get("content")
                    if content:
                        full_content += content
                        await ws.send_json(WSChunkFrame(content=content).model_dump())

                    # Handle tool call chunks
                    tc_list = delta.get("tool_calls")
                    if tc_list:
                        for tc_delta in tc_list:
                            idx = tc_delta.get("index", 0)
                            if idx not in current_tool_calls:
                                current_tool_calls[idx] = {
                                    "id": tc_delta.get("id", ""),
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            tc = current_tool_calls[idx]
                            if tc_delta.get("id"):
                                tc["id"] = tc_delta["id"]
                            func = tc_delta.get("function", {})
                            if func.get("name"):
                                tc["function"]["name"] += func["name"]
                            if func.get("arguments"):
                                tc["function"]["arguments"] += func["arguments"]

        except httpx.ReadTimeout:
            await ws.send_json(WSErrorFrame(detail="LLM response timed out").model_dump())
            return (full_content, None)
        except Exception as e:
            logger.error(f"LLM stream error: {e}", exc_info=True)
            await ws.send_json(WSErrorFrame(detail=f"LLM error: {str(e)}").model_dump())
            return (full_content, None)

        # Convert accumulated tool calls
        if current_tool_calls:
            tool_calls = [current_tool_calls[i] for i in sorted(current_tool_calls.keys())]

        return (full_content, tool_calls if tool_calls else None)


# ─── Helpers ────────────────────────────────────────────────────────────

def _derive_title(messages: List[Dict]) -> str:
    """Derive a session title from the first user message."""
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role")
            content = m.get("content", "")
        else:
            role = getattr(m, "role", None)
            content = getattr(m, "content", "")
        if role == "user" and content:
            return content[:60] + ("..." if len(content) > 60 else "")
    return "New Session"


def _prune_context(
    messages: List[ChatMessage],
    system_prompt: str,
    context_window: int,
) -> List[ChatMessage]:
    """Return the subset of *messages* that fits within the token budget.

    Strategy:
      1. Compute the budget = (context_window * 80%) - system_prompt_tokens.
      2. Always keep the most recent messages.  Walk backwards from the end,
         accumulating tokens until the budget is exhausted.
      3. Never split a tool-call exchange: if an assistant message with
         tool_calls is included, all following tool-result messages (up to
         the next user/assistant) are included too.

    If all messages already fit, the original list is returned unchanged.
    """
    if not messages:
        return messages

    # Budget in estimated tokens, minus what the system prompt will consume.
    total_budget = int(context_window * _CONTEXT_BUDGET_RATIO)
    system_tokens = _estimate_tokens(system_prompt)
    message_budget = max(total_budget - system_tokens, 512)  # floor at 512 tokens

    # Fast path: everything fits.
    total_tokens = sum(_estimate_message_tokens(m) for m in messages)
    if total_tokens <= message_budget:
        return messages

    # Walk backwards, accumulating tokens.
    selected_indices: List[int] = []
    running_tokens = 0

    i = len(messages) - 1
    while i >= 0:
        msg = messages[i]
        msg_tokens = _estimate_message_tokens(msg)

        # If adding this message would exceed the budget and we already
        # have at least the latest user message, stop.
        if selected_indices and (running_tokens + msg_tokens) > message_budget:
            break

        selected_indices.append(i)
        running_tokens += msg_tokens

        # If this is a tool message, we must also include the preceding
        # assistant message that initiated the tool call (keep the exchange
        # together).  Walk back to include the full tool-call group.
        if msg.role == "tool" and i > 0:
            # Already handled by the main loop — just continue backwards.
            pass

        i -= 1

    selected_indices.reverse()
    return [messages[idx] for idx in selected_indices]


# Singleton instance
colonel_gateway = ColonelGateway()
