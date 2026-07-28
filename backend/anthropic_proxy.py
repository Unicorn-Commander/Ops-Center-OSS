"""
Anthropic API Proxy for Ops-Center

This module implements a proxy endpoint that mimics the Anthropic API format,
allowing Claude Code to communicate with Ops-Center, which then routes requests
through Brigade for agent orchestration and LiteLLM for LLM inference.

Architecture:
1. Accept requests in Anthropic API format
2. Extract user message and context
3. Route to Brigade for agent orchestration
4. Brigade calls LiteLLM via Ops-Center for inference
5. Brigade may call back to user's local MCP servers for tool execution
6. Return response in Anthropic API format
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Literal
from datetime import datetime
import httpx
import json
import uuid
import logging
import os
import asyncio
from auth_manager import auth_manager

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Router for Anthropic API proxy
router = APIRouter(prefix="/v1", tags=["anthropic-proxy"])

# Configuration
BRIGADE_URL = os.environ.get("BRIGADE_URL", "http://unicorn-brigade:8112")
LITELLM_URL = os.environ.get("LITELLM_URL", "http://localhost:4000")
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "https://auth.unicorncommander.ai")

# ===================================================================
# Anthropic API Models (Request/Response Schemas)
# ===================================================================

class ToolInputSchema(BaseModel):
    """Schema for tool input parameters"""
    type: str = "object"
    properties: Dict[str, Any]
    required: Optional[List[str]] = None

class AnthropicTool(BaseModel):
    """Tool definition in Anthropic format"""
    name: str
    description: str
    input_schema: ToolInputSchema

class MessageContent(BaseModel):
    """Content block in message"""
    type: Literal["text", "tool_use", "tool_result", "image"]
    text: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    tool_use_id: Optional[str] = None
    content: Optional[Union[str, List[Dict[str, Any]]]] = None
    source: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    """Message in conversation"""
    role: Literal["user", "assistant"]
    content: Union[str, List[MessageContent]]

class AnthropicRequest(BaseModel):
    """Anthropic API request format"""
    model: str = Field(..., description="Model name (e.g., claude-3-5-sonnet-20241022)")
    messages: List[Message] = Field(..., description="Conversation messages")
    max_tokens: int = Field(4096, description="Maximum tokens to generate")
    system: Optional[str] = Field(None, description="System prompt")
    temperature: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=0)
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = Field(False, description="Stream response")
    tools: Optional[List[AnthropicTool]] = Field(None, description="Available tools")
    metadata: Optional[Dict[str, Any]] = None

class UsageInfo(BaseModel):
    """Token usage information"""
    input_tokens: int
    output_tokens: int

class AnthropicResponse(BaseModel):
    """Anthropic API response format"""
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: List[MessageContent]
    model: str
    stop_reason: Optional[Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"]] = None
    stop_sequence: Optional[str] = None
    usage: UsageInfo

# ===================================================================
# Authentication & User Context
# ===================================================================

async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extract and validate user from JWT token or API key.

    Returns user context including:
    - user_id: Unique user identifier
    - email: User email
    - mcp_servers: List of user's MCP server endpoints for callbacks
    - subscription_tier: User's subscription level
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Extract token
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    try:
        # Validate with Keycloak or check API key
        if token.startswith("sk-ant-"):
            # This is an Anthropic-style API key
            # For now, we'll validate against user's BYOK keys
            # In production, implement proper API key validation
            user_info = await validate_api_key(token)
        else:
            # JWT token validation
            user_info = await validate_jwt_token(token)

        return user_info
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def validate_api_key(api_key: str) -> Dict[str, Any]:
    """Validate API key and return user context"""
    # TODO: Implement proper API key validation
    # For now, return mock user data
    return {
        "user_id": "user_123",
        "email": "user@example.com",
        "subscription_tier": "pro",
        "mcp_servers": []
    }

async def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate JWT token with Keycloak"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KEYCLOAK_URL}/realms/uchub/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            user_data = response.json()

            return {
                "user_id": user_data.get("sub"),
                "email": user_data.get("email"),
                "username": user_data.get("preferred_username"),
                "subscription_tier": user_data.get("subscription_tier", "free"),
                "mcp_servers": user_data.get("mcp_servers", [])
            }
        except httpx.HTTPError as e:
            logger.error(f"Keycloak validation failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

# ===================================================================
# Main Proxy Endpoint
# ===================================================================

@router.post("/messages", response_model=AnthropicResponse)
async def create_message(
    request: AnthropicRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Main endpoint that mimics Anthropic's /v1/messages API.

    This endpoint:
    1. Accepts requests in Anthropic API format
    2. Checks user's BYOK configuration
    3. Converts to Brigade task format (including BYOK and execution server config)
    4. Routes to Brigade for orchestration
    5. Brigade calls LiteLLM with user's API key or system default
    6. Brigade may call user's MCP servers for tool execution
    7. Returns response in Anthropic API format
    """
    try:
        logger.info(f"Received request from user {user['user_id']}")
        logger.info(f"Model: {request.model}, Messages: {len(request.messages)}, Tools: {len(request.tools or [])}")

        # Get user's BYOK configuration
        from byok_service import get_byok_service
        byok_service = get_byok_service()

        # Get provider config (will use BYOK if configured, otherwise system default)
        provider_config = await byok_service.get_user_provider_config(user, None, request.model)

        logger.info(
            f"User {user.get('email')} request routing: "
            f"provider={provider_config['provider']}, "
            f"model={provider_config['model']}, "
            f"byok={provider_config['is_byok']}"
        )

        # Get execution server config if configured
        execution_server = await byok_service.get_execution_server_config(user.get('user_id'))
        if execution_server:
            logger.info(f"User has execution server configured: {execution_server['name']}")

        # Convert Anthropic request to Brigade format
        from brigade_adapter import convert_anthropic_to_brigade
        brigade_request = convert_anthropic_to_brigade(request, user, provider_config, execution_server)

        # Send to Brigade
        async with httpx.AsyncClient(timeout=300.0) as client:
            brigade_response = await client.post(
                f"{BRIGADE_URL}/api/tasks",
                json=brigade_request,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {user.get('token', '')}"
                }
            )
            brigade_response.raise_for_status()
            brigade_data = brigade_response.json()

        # Convert Brigade response back to Anthropic format
        from brigade_adapter import convert_brigade_to_anthropic
        anthropic_response = convert_brigade_to_anthropic(
            brigade_data,
            request.model,
            user
        )

        logger.info(f"Successfully processed request for user {user['user_id']}")
        return anthropic_response

    except httpx.HTTPError as e:
        logger.error(f"Brigade request failed: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Brigade orchestration failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/messages/stream")
async def create_message_stream(
    request: AnthropicRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Streaming endpoint for Anthropic API.

    Returns Server-Sent Events (SSE) format with incremental responses.
    Uses user's BYOK if configured, otherwise system default.
    """
    try:
        logger.info(f"Streaming request from user {user['user_id']}")

        # Get user's BYOK configuration
        from byok_service import get_byok_service
        byok_service = get_byok_service()
        provider_config = await byok_service.get_user_provider_config(user, None, request.model)
        execution_server = await byok_service.get_execution_server_config(user.get('user_id'))

        # Convert to Brigade format
        from brigade_adapter import convert_anthropic_to_brigade
        brigade_request = convert_anthropic_to_brigade(request, user, provider_config, execution_server)
        brigade_request["stream"] = True

        async def event_generator():
            """Generate SSE events from Brigade streaming response"""
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{BRIGADE_URL}/api/tasks/stream",
                    json=brigade_request,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {user.get('token', '')}"
                    }
                ) as response:
                    async for chunk in response.aiter_lines():
                        if chunk:
                            # Convert Brigade SSE to Anthropic SSE format
                            anthropic_event = convert_sse_event(chunk, request.model)
                            yield f"data: {json.dumps(anthropic_event)}\n\n"

            # Send final event
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def convert_sse_event(brigade_event: str, model: str) -> Dict[str, Any]:
    """Convert Brigade SSE event to Anthropic format"""
    try:
        data = json.loads(brigade_event.replace("data: ", ""))

        # Map Brigade event types to Anthropic format
        if data.get("type") == "content_block_start":
            return {
                "type": "content_block_start",
                "index": data.get("index", 0),
                "content_block": {
                    "type": "text",
                    "text": ""
                }
            }
        elif data.get("type") == "content_block_delta":
            return {
                "type": "content_block_delta",
                "index": data.get("index", 0),
                "delta": {
                    "type": "text_delta",
                    "text": data.get("text", "")
                }
            }
        elif data.get("type") == "message_stop":
            return {
                "type": "message_stop"
            }
        else:
            return data
    except json.JSONDecodeError:
        return {"type": "error", "error": "Invalid JSON in stream"}

# ===================================================================
# Health & Status Endpoints
# ===================================================================

@router.get("/health")
async def health_check():
    """Health check for the proxy service"""
    try:
        # Check Brigade connectivity
        async with httpx.AsyncClient(timeout=5.0) as client:
            brigade_health = await client.get(f"{BRIGADE_URL}/health")
            brigade_status = brigade_health.status_code == 200
    except:
        brigade_status = False

    return {
        "status": "healthy" if brigade_status else "degraded",
        "brigade_connected": brigade_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/models")
async def list_models(user: Dict[str, Any] = Depends(get_current_user)):
    """
    List available models (mimics Anthropic's model list endpoint).

    Returns models available through LiteLLM based on user's BYOK configuration.
    """
    return {
        "data": [
            {
                "id": "claude-3-5-sonnet-20241022",
                "type": "model",
                "display_name": "Claude 3.5 Sonnet"
            },
            {
                "id": "claude-3-opus-20240229",
                "type": "model",
                "display_name": "Claude 3 Opus"
            },
            {
                "id": "gpt-4",
                "type": "model",
                "display_name": "GPT-4"
            },
            {
                "id": "gpt-3.5-turbo",
                "type": "model",
                "display_name": "GPT-3.5 Turbo"
            }
        ]
    }
