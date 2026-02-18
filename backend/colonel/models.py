"""
Pydantic models for The Colonel WebSocket frames, chat messages, and sessions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid


# ─── WebSocket Frame Types ─────────────────────────────────────────────────

class WSFrame(BaseModel):
    """Base WebSocket frame sent between client and server."""
    type: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WSChunkFrame(WSFrame):
    """Streamed text chunk from the LLM."""
    type: Literal["chunk"] = "chunk"
    content: str


class WSMessageDoneFrame(WSFrame):
    """Signals the end of a complete message."""
    type: Literal["message_done"] = "message_done"
    message_id: str
    content: str  # full assembled message


class WSErrorFrame(WSFrame):
    """Error frame."""
    type: Literal["error"] = "error"
    detail: str
    code: Optional[str] = None


class WSSkillStartFrame(WSFrame):
    """Skill execution has started."""
    type: Literal["skill_start"] = "skill_start"
    skill_name: str
    action: str
    params: Dict[str, Any] = {}


class WSSkillProgressFrame(WSFrame):
    """Streaming output from a skill execution."""
    type: Literal["skill_progress"] = "skill_progress"
    skill_name: str
    output: str


class WSSkillResultFrame(WSFrame):
    """Skill execution completed."""
    type: Literal["skill_result"] = "skill_result"
    skill_name: str
    action: str
    success: bool
    output: str
    duration_ms: Optional[int] = None


class WSConfirmFrame(WSFrame):
    """Request user confirmation before executing a dangerous action."""
    type: Literal["confirm_required"] = "confirm_required"
    skill_name: str
    action: str
    description: str
    params: Dict[str, Any] = {}


class WSPingFrame(WSFrame):
    """Keepalive ping."""
    type: Literal["ping"] = "ping"


class WSPongFrame(WSFrame):
    """Keepalive pong response."""
    type: Literal["pong"] = "pong"


# ─── Chat Message Models ───────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single chat message in a session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    name: Optional[str] = None  # for tool messages


class ColonelSession(BaseModel):
    """A chat session with The Colonel."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    colonel_id: str = "default"
    messages: List[ChatMessage] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    title: Optional[str] = None


# ─── Colonel Configuration ─────────────────────────────────────────────────

class ColonelPersonality(BaseModel):
    """Personality configuration for The Colonel."""
    formality: int = Field(default=7, ge=1, le=10, description="1=casual, 10=very formal")
    verbosity: int = Field(default=5, ge=1, le=10, description="1=terse, 10=verbose")
    humor: int = Field(default=4, ge=1, le=10, description="1=serious, 10=playful")


class ColonelConfig(BaseModel):
    """Configuration for a Colonel instance."""
    id: str = Field(default="default")
    name: str = Field(default="Col. Corelli")
    server_name: str = Field(default_factory=lambda: __import__('os').getenv("COLONEL_SERVER_NAME", __import__('os').getenv("EXTERNAL_HOST", "My Server")))
    mission: Literal["devops", "monitoring", "security", "general"] = "devops"
    personality: ColonelPersonality = Field(default_factory=ColonelPersonality)
    model: str = Field(default="claude-opus-4-6")
    enabled_skills: List[str] = Field(default_factory=lambda: [
        "docker-management", "bash-execution", "system-status",
        "service-health", "log-viewer"
    ])
    write_capable_models: List[str] = Field(default_factory=lambda: [
        "anthropic/claude-opus-4*",
        "anthropic/claude-sonnet-4-5*",
        "claude-opus-4*",
        "claude-sonnet-4-5*",
        "openai/gpt-5*",
        "openai/gpt-4o*",
        "openai/o1*",
        "openai/o3*",
        "google/gemini-2*-pro*",
        "google/gemini-2.5-flash*",
    ])
    admin_only: bool = True
    onboarded: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ─── REST API Models ───────────────────────────────────────────────────────

class ColonelStatusResponse(BaseModel):
    """Response for GET /api/v1/colonel/status."""
    online: bool
    config: ColonelConfig
    active_sessions: int = 0
    skills_loaded: int = 0
    memory_entries: int = 0
    graph_stats: Optional[Dict[str, Any]] = None


class ColonelConfigUpdate(BaseModel):
    """Request body for PUT /api/v1/colonel/config."""
    name: Optional[str] = None
    server_name: Optional[str] = None
    mission: Optional[Literal["devops", "monitoring", "security", "general"]] = None
    personality: Optional[ColonelPersonality] = None
    model: Optional[str] = None
    enabled_skills: Optional[List[str]] = None
    write_capable_models: Optional[List[str]] = None
    admin_only: Optional[bool] = None
