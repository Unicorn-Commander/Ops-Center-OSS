"""
Testing Lab API - Interactive Model Testing with Streaming

This module provides comprehensive model testing capabilities:
- Streaming chat completions for any configured model
- Real-time cost and latency tracking
- Test history and analytics
- Pre-built test templates
- Access control based on user subscription tier
- Support for all providers (OpenRouter, OpenAI, Anthropic, local)

Author: Backend API Developer
Date: October 27, 2025
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
import httpx
import asyncpg
import redis.asyncio as aioredis
from cryptography.fernet import Fernet

from database.connection import get_db_pool

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/v1/llm/test", tags=["Testing Lab"])

# Environment
REDIS_HOST = os.getenv("REDIS_HOST", "unicorn-lago-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://unicorn-litellm:4000")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

# Encryption
cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Redis client (lazy initialization)
_redis_client: Optional[aioredis.Redis] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ModelTestRequest(BaseModel):
    model_id: str = Field(..., description="Model identifier (e.g., openrouter/anthropic/claude-3.5-sonnet)")
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    stream: bool = Field(True, description="Stream response chunks")

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('top_p')
    def validate_top_p(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Top_p must be between 0.0 and 1.0')
        return v


class TestTemplate(BaseModel):
    id: str
    name: str
    prompt: str
    category: str
    description: Optional[str] = None
    suggested_models: Optional[List[str]] = None


class TestHistoryEntry(BaseModel):
    id: str
    model_id: str
    prompt: str
    response: str
    tokens_used: int
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    created_at: datetime
    parameters: Dict[str, Any]


class TestStats(BaseModel):
    total_tests: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    models_tested: List[str]
    last_test_at: Optional[datetime]


# ============================================================================
# Authentication & Access Control
# ============================================================================

async def get_current_user_from_session(request: Request) -> Dict:
    """
    Get current user from session cookie

    Returns:
        User dict with id, email, role, subscription_tier

    Raises:
        HTTPException 401 if not authenticated
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no session token")

    # Get sessions from app state
    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session - please login again")

    user = session_data.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    return user


async def check_model_access(user: Dict, model_id: str) -> Dict[str, Any]:
    """
    Check if user has access to test this model

    Args:
        user: User dict with subscription_tier
        model_id: Model identifier

    Returns:
        {
            "allowed": bool,
            "reason": str,
            "tier_required": str (if not allowed)
        }
    """
    user_tier = user.get("subscription_tier", "trial").lower()

    # Tier-based model access rules
    tier_access = {
        "trial": ["openrouter/free", "local"],
        "starter": ["openrouter/", "groq/", "together/", "local"],
        "professional": ["openrouter/", "openai/gpt-3.5", "openai/gpt-4o-mini", "anthropic/claude-3-haiku", "groq/", "together/", "local"],
        "enterprise": ["*"]  # All models
    }

    # Check if model is allowed for this tier
    allowed_prefixes = tier_access.get(user_tier, tier_access["trial"])

    if "*" in allowed_prefixes:
        return {"allowed": True, "reason": "Enterprise tier - all models available"}

    # Check if model matches any allowed prefix
    for prefix in allowed_prefixes:
        if prefix.endswith("/") and model_id.startswith(prefix):
            return {"allowed": True, "reason": f"Model allowed for {user_tier} tier"}
        elif model_id == prefix:
            return {"allowed": True, "reason": f"Model allowed for {user_tier} tier"}

    # Premium models require upgrade
    if model_id.startswith("openai/gpt-4") or model_id.startswith("anthropic/claude-3-opus"):
        return {
            "allowed": False,
            "reason": "Premium models require Professional or Enterprise tier",
            "tier_required": "professional"
        }

    return {
        "allowed": False,
        "reason": f"Model not available for {user_tier} tier. Upgrade to access more models.",
        "tier_required": "professional"
    }


# ============================================================================
# Database Helpers
# ============================================================================

async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client"""
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = await aioredis.from_url(
                f"redis://{REDIS_HOST}:{REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise HTTPException(status_code=503, detail="Cache service unavailable")

    return _redis_client


async def log_test_usage(
    user_id: str,
    model_id: str,
    messages: List[Dict],
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    latency_ms: int,
    parameters: Dict[str, Any]
):
    """
    Log test run to database

    Args:
        user_id: User identifier
        model_id: Model identifier
        messages: Input messages
        response_text: Model response
        input_tokens: Input token count
        output_tokens: Output token count
        cost: Cost in USD
        latency_ms: Latency in milliseconds
        parameters: Test parameters (temperature, max_tokens, etc.)
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Store in llm_usage_logs
        await conn.execute("""
            INSERT INTO llm_usage_logs (
                user_id, model_name, input_tokens, output_tokens, total_tokens,
                cost, latency_ms, success, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, true, $8, NOW())
        """,
            user_id,
            model_id,
            input_tokens,
            output_tokens,
            input_tokens + output_tokens,
            cost,
            latency_ms,
            json.dumps({
                "prompt": messages[-1]["content"] if messages else "",
                "response": response_text[:500],  # Truncate for storage
                "parameters": parameters,
                "source": "testing_lab"
            })
        )


async def get_provider_key(provider: str, user_byok: Optional[Dict] = None) -> Optional[str]:
    """
    Get API key for provider (BYOK if available, otherwise system key)

    Args:
        provider: Provider name (openrouter, openai, anthropic, etc.)
        user_byok: User's BYOK settings (encrypted keys)

    Returns:
        Decrypted API key or None
    """
    # Check BYOK first
    if user_byok and provider in user_byok:
        encrypted_key = user_byok[provider]
        try:
            return cipher_suite.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt BYOK key for {provider}: {e}")

    # Fall back to system key
    env_key_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "together": "TOGETHER_API_KEY",
        "groq": "GROQ_API_KEY"
    }

    env_var = env_key_map.get(provider)
    if env_var:
        return os.getenv(env_var)

    return None


async def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost based on model pricing

    Args:
        model_id: Model identifier
        input_tokens: Input token count
        output_tokens: Output token count

    Returns:
        Cost in USD (rounded to 6 decimals)
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Try to get pricing from database
        pricing = await conn.fetchrow("""
            SELECT cost_per_1m_input_tokens, cost_per_1m_output_tokens
            FROM llm_models
            WHERE name = $1 OR display_name = $1
            LIMIT 1
        """, model_id)

        if pricing:
            input_cost = (input_tokens / 1_000_000) * float(pricing['cost_per_1m_input_tokens'] or 0)
            output_cost = (output_tokens / 1_000_000) * float(pricing['cost_per_1m_output_tokens'] or 0)
            return round(input_cost + output_cost, 6)

    # Fallback: estimate based on provider
    # Default pricing: $0.50 per 1M input, $1.50 per 1M output
    input_cost = (input_tokens / 1_000_000) * 0.50
    output_cost = (output_tokens / 1_000_000) * 1.50
    return round(input_cost + output_cost, 6)


# ============================================================================
# Streaming Implementations
# ============================================================================

async def test_openrouter_model(request: ModelTestRequest, user_id: str, api_key: str) -> AsyncIterator[str]:
    """
    Stream response from OpenRouter

    Yields:
        SSE-formatted chunks: data: {"content": "...", "tokens": N}\n\n
    """
    start_time = time.time()
    total_input_tokens = 0
    total_output_tokens = 0
    response_text = ""

    # Prepare request
    model_name = request.model_id.replace("openrouter/", "")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://your-domain.com",
                    "X-Title": "UC-1 Pro Testing Lab"
                },
                json={
                    "model": model_name,
                    "messages": [msg.dict() for msg in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"data: {json.dumps({'error': f'OpenRouter error: {response.status_code} - {error_text.decode()}'})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)

                            # Extract usage info if available
                            if "usage" in chunk:
                                usage = chunk["usage"]
                                total_input_tokens = usage.get("prompt_tokens", 0)
                                total_output_tokens = usage.get("completion_tokens", 0)

                            # Extract content
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                response_text += content
                                yield f"data: {json.dumps({'content': content, 'tokens': len(response_text.split())})}\n\n"

                        except json.JSONDecodeError:
                            continue

        # Calculate final metrics
        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate tokens if not provided
        if total_input_tokens == 0:
            total_input_tokens = sum(len(msg.content.split()) for msg in request.messages)
        if total_output_tokens == 0:
            total_output_tokens = len(response_text.split())

        cost = await calculate_cost(request.model_id, total_input_tokens, total_output_tokens)

        # Send final metrics
        yield f"data: {json.dumps({'done': True, 'input_tokens': total_input_tokens, 'output_tokens': total_output_tokens, 'total_tokens': total_input_tokens + total_output_tokens, 'cost': cost, 'latency_ms': latency_ms})}\n\n"

        # Log usage
        await log_test_usage(
            user_id=user_id,
            model_id=request.model_id,
            messages=[msg.dict() for msg in request.messages],
            response_text=response_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            parameters={
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p
            }
        )

    except httpx.TimeoutException:
        yield f"data: {json.dumps({'error': 'Request timeout (60s limit)'})}\n\n"
    except Exception as e:
        logger.error(f"OpenRouter streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"


async def test_openai_model(request: ModelTestRequest, user_id: str, api_key: str) -> AsyncIterator[str]:
    """Stream response from OpenAI"""
    start_time = time.time()
    total_input_tokens = 0
    total_output_tokens = 0
    response_text = ""

    model_name = request.model_id.replace("openai/", "")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [msg.dict() for msg in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "top_p": request.top_p,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"data: {json.dumps({'error': f'OpenAI error: {response.status_code} - {error_text.decode()}'})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)

                            # Extract usage
                            if "usage" in chunk:
                                usage = chunk["usage"]
                                total_input_tokens = usage.get("prompt_tokens", 0)
                                total_output_tokens = usage.get("completion_tokens", 0)

                            # Extract content
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                response_text += content
                                yield f"data: {json.dumps({'content': content, 'tokens': len(response_text.split())})}\n\n"

                        except json.JSONDecodeError:
                            continue

        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate tokens if not provided
        if total_input_tokens == 0:
            total_input_tokens = sum(len(msg.content.split()) for msg in request.messages)
        if total_output_tokens == 0:
            total_output_tokens = len(response_text.split())

        cost = await calculate_cost(request.model_id, total_input_tokens, total_output_tokens)

        yield f"data: {json.dumps({'done': True, 'input_tokens': total_input_tokens, 'output_tokens': total_output_tokens, 'total_tokens': total_input_tokens + total_output_tokens, 'cost': cost, 'latency_ms': latency_ms})}\n\n"

        await log_test_usage(
            user_id=user_id,
            model_id=request.model_id,
            messages=[msg.dict() for msg in request.messages],
            response_text=response_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            parameters={
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p
            }
        )

    except httpx.TimeoutException:
        yield f"data: {json.dumps({'error': 'Request timeout (60s limit)'})}\n\n"
    except Exception as e:
        logger.error(f"OpenAI streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"


async def test_anthropic_model(request: ModelTestRequest, user_id: str, api_key: str) -> AsyncIterator[str]:
    """Stream response from Anthropic"""
    start_time = time.time()
    total_input_tokens = 0
    total_output_tokens = 0
    response_text = ""

    model_name = request.model_id.replace("anthropic/", "")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [msg.dict() for msg in request.messages if msg.role != "system"],
                    "system": next((msg.content for msg in request.messages if msg.role == "system"), None),
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens or 4096,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"data: {json.dumps({'error': f'Anthropic error: {response.status_code} - {error_text.decode()}'})}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]

                        try:
                            chunk = json.loads(data)
                            event_type = chunk.get("type")

                            if event_type == "content_block_delta":
                                content = chunk.get("delta", {}).get("text", "")
                                if content:
                                    response_text += content
                                    yield f"data: {json.dumps({'content': content, 'tokens': len(response_text.split())})}\n\n"

                            elif event_type == "message_start":
                                usage = chunk.get("message", {}).get("usage", {})
                                total_input_tokens = usage.get("input_tokens", 0)

                            elif event_type == "message_delta":
                                usage = chunk.get("usage", {})
                                total_output_tokens = usage.get("output_tokens", 0)

                        except json.JSONDecodeError:
                            continue

        latency_ms = int((time.time() - start_time) * 1000)

        # Estimate tokens if not provided
        if total_input_tokens == 0:
            total_input_tokens = sum(len(msg.content.split()) for msg in request.messages)
        if total_output_tokens == 0:
            total_output_tokens = len(response_text.split())

        cost = await calculate_cost(request.model_id, total_input_tokens, total_output_tokens)

        yield f"data: {json.dumps({'done': True, 'input_tokens': total_input_tokens, 'output_tokens': total_output_tokens, 'total_tokens': total_input_tokens + total_output_tokens, 'cost': cost, 'latency_ms': latency_ms})}\n\n"

        await log_test_usage(
            user_id=user_id,
            model_id=request.model_id,
            messages=[msg.dict() for msg in request.messages],
            response_text=response_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            parameters={
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p
            }
        )

    except httpx.TimeoutException:
        yield f"data: {json.dumps({'error': 'Request timeout (60s limit)'})}\n\n"
    except Exception as e:
        logger.error(f"Anthropic streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("")
async def test_model(
    request_body: ModelTestRequest,
    req: Request,
    current_user: Dict = Depends(get_current_user_from_session)
):
    """
    Test any configured model with streaming response

    **Request Body:**
    ```json
    {
      "model_id": "openrouter/anthropic/claude-3.5-sonnet",
      "messages": [{"role": "user", "content": "Hello"}],
      "temperature": 0.7,
      "max_tokens": 1000,
      "top_p": 1.0,
      "stream": true
    }
    ```

    **Response:** SSE (Server-Sent Events) stream
    ```
    data: {"content": "Hello", "tokens": 1}
    data: {"content": " there", "tokens": 2}
    data: {"done": true, "input_tokens": 10, "output_tokens": 150, "total_tokens": 160, "cost": 0.0045, "latency_ms": 2340}
    ```
    """
    user_id = current_user.get("id") or current_user.get("email")

    # Check access control
    access = await check_model_access(current_user, request_body.model_id)
    if not access["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": access["reason"],
                "tier_required": access.get("tier_required"),
                "current_tier": current_user.get("subscription_tier", "trial")
            }
        )

    # Detect provider
    if request_body.model_id.startswith("openrouter/"):
        provider = "openrouter"
    elif request_body.model_id.startswith("openai/"):
        provider = "openai"
    elif request_body.model_id.startswith("anthropic/"):
        provider = "anthropic"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model provider: {request_body.model_id}")

    # Get API key (BYOK or system)
    # TODO: Fetch user BYOK settings from database
    user_byok = None  # Placeholder
    api_key = await get_provider_key(provider, user_byok)

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=f"{provider.title()} API key not configured. Please configure in LLM Settings or provide your own key (BYOK)."
        )

    # Route to appropriate provider
    if provider == "openrouter":
        return StreamingResponse(
            test_openrouter_model(request_body, user_id, api_key),
            media_type="text/event-stream"
        )
    elif provider == "openai":
        return StreamingResponse(
            test_openai_model(request_body, user_id, api_key),
            media_type="text/event-stream"
        )
    elif provider == "anthropic":
        return StreamingResponse(
            test_anthropic_model(request_body, user_id, api_key),
            media_type="text/event-stream"
        )


@router.get("/history")
async def get_test_history(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user_from_session)
):
    """
    Get user's recent test runs

    **Query Parameters:**
    - `limit`: Number of records to return (default 20, max 100)
    - `offset`: Pagination offset (default 0)

    **Returns:**
    ```json
    {
      "total": 45,
      "tests": [
        {
          "id": "uuid",
          "model_id": "openrouter/anthropic/claude-3.5-sonnet",
          "prompt": "Explain quantum physics",
          "response": "Quantum physics is...",
          "tokens_used": 250,
          "input_tokens": 10,
          "output_tokens": 240,
          "cost": 0.0045,
          "latency_ms": 2340,
          "created_at": "2025-10-27T12:00:00Z",
          "parameters": {"temperature": 0.7, "max_tokens": 1000}
        }
      ]
    }
    ```
    """
    user_id = current_user.get("id") or current_user.get("email")

    # Clamp limit
    limit = min(limit, 100)

    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM llm_usage_logs
            WHERE user_id = $1 AND metadata->>'source' = 'testing_lab'
        """, user_id)

        # Get records
        rows = await conn.fetch("""
            SELECT
                id::text,
                model_name,
                input_tokens,
                output_tokens,
                total_tokens,
                cost,
                latency_ms,
                created_at,
                metadata
            FROM llm_usage_logs
            WHERE user_id = $1 AND metadata->>'source' = 'testing_lab'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)

        tests = []
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            tests.append({
                "id": row['id'],
                "model_id": row['model_name'],
                "prompt": metadata.get("prompt", ""),
                "response": metadata.get("response", ""),
                "tokens_used": row['total_tokens'],
                "input_tokens": row['input_tokens'],
                "output_tokens": row['output_tokens'],
                "cost": float(row['cost']),
                "latency_ms": row['latency_ms'],
                "created_at": row['created_at'].isoformat(),
                "parameters": metadata.get("parameters", {})
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tests": tests
        }


@router.get("/templates")
async def get_test_templates():
    """
    Get pre-built test prompts

    **Returns:**
    ```json
    [
      {
        "id": "explain-quantum",
        "name": "Explain Quantum Physics",
        "prompt": "Explain quantum physics in simple terms",
        "category": "explanation",
        "description": "Test model's ability to explain complex concepts",
        "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o"]
      }
    ]
    ```
    """
    templates = [
        {
            "id": "explain-quantum",
            "name": "Explain Quantum Physics",
            "prompt": "Explain quantum physics in simple terms that a high school student could understand.",
            "category": "explanation",
            "description": "Test model's ability to explain complex scientific concepts",
            "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o", "openrouter/google/gemini-pro"]
        },
        {
            "id": "write-poem",
            "name": "Write a Poem",
            "prompt": "Write a haiku about artificial intelligence and its impact on humanity.",
            "category": "creative",
            "description": "Test creative writing and poetry generation",
            "suggested_models": ["openrouter/anthropic/claude-3-opus", "openai/gpt-4", "openrouter/meta-llama/llama-3.1-70b"]
        },
        {
            "id": "code-function",
            "name": "Code a Function",
            "prompt": "Write a Python function to check if a number is prime. Include docstring and unit tests.",
            "category": "coding",
            "description": "Test coding ability and best practices",
            "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o", "openrouter/qwen/qwen-2.5-coder-32b"]
        },
        {
            "id": "analyze-sentiment",
            "name": "Sentiment Analysis",
            "prompt": "Analyze the sentiment of this text: 'I absolutely love this product! It exceeded all my expectations and the customer service was phenomenal.' Provide a score from -1 (very negative) to +1 (very positive) and explain your reasoning.",
            "category": "analysis",
            "description": "Test analytical reasoning and sentiment detection",
            "suggested_models": ["openrouter/anthropic/claude-3-haiku", "openai/gpt-3.5-turbo", "openrouter/meta-llama/llama-3.1-8b"]
        },
        {
            "id": "logic-puzzle",
            "name": "Logic Puzzle",
            "prompt": "Solve this logic puzzle: Three people (Alice, Bob, Charlie) are standing in a line. Alice is not at the front. Bob is not at the back. Charlie is not in the middle. What is the order from front to back?",
            "category": "reasoning",
            "description": "Test logical reasoning and problem-solving",
            "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/o1-preview", "openrouter/google/gemini-pro"]
        },
        {
            "id": "summarize-text",
            "name": "Text Summarization",
            "prompt": "Summarize the following text in 2-3 sentences: 'Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves. The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future.'",
            "category": "summarization",
            "description": "Test summarization and comprehension",
            "suggested_models": ["openrouter/anthropic/claude-3-haiku", "openai/gpt-4o-mini", "openrouter/meta-llama/llama-3.1-8b"]
        },
        {
            "id": "translate-language",
            "name": "Language Translation",
            "prompt": "Translate the following English text to French: 'The quick brown fox jumps over the lazy dog.' Then explain any cultural nuances or idioms that don't translate directly.",
            "category": "translation",
            "description": "Test multilingual capabilities",
            "suggested_models": ["openrouter/anthropic/claude-3-opus", "openai/gpt-4", "openrouter/google/gemini-pro"]
        },
        {
            "id": "math-problem",
            "name": "Math Problem",
            "prompt": "Solve this math problem step by step: If a train travels 120 km in 2 hours, and then 180 km in 3 hours, what is its average speed for the entire journey?",
            "category": "mathematics",
            "description": "Test mathematical reasoning and explanation",
            "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o", "openrouter/qwen/qwen-2.5-math-72b"]
        },
        {
            "id": "role-play",
            "name": "Role-Playing",
            "prompt": "You are a customer service representative for a tech company. A customer is frustrated because their new laptop won't turn on. Help them troubleshoot the issue with empathy and clear instructions.",
            "category": "conversation",
            "description": "Test conversational ability and empathy",
            "suggested_models": ["openrouter/anthropic/claude-3-opus", "openai/gpt-4", "openrouter/meta-llama/llama-3.1-70b"]
        },
        {
            "id": "brainstorm-ideas",
            "name": "Brainstorming",
            "prompt": "Brainstorm 5 innovative product ideas for reducing plastic waste in urban environments. For each idea, provide a brief description and potential challenges.",
            "category": "creative",
            "description": "Test creative thinking and ideation",
            "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o", "openrouter/google/gemini-pro"]
        }
    ]

    return templates


@router.get("/stats")
async def get_test_stats(
    current_user: Dict = Depends(get_current_user_from_session)
):
    """
    Get user's testing statistics

    **Returns:**
    ```json
    {
      "total_tests": 45,
      "total_tokens": 125000,
      "total_cost": 2.45,
      "avg_latency_ms": 1850,
      "models_tested": [
        "openrouter/anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openrouter/meta-llama/llama-3.1-70b"
      ],
      "last_test_at": "2025-10-27T12:00:00Z"
    }
    ```
    """
    user_id = current_user.get("id") or current_user.get("email")

    pool = await get_db_pool()

    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_tests,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost), 0) as total_cost,
                COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
                MAX(created_at) as last_test_at
            FROM llm_usage_logs
            WHERE user_id = $1 AND metadata->>'source' = 'testing_lab'
        """, user_id)

        # Get unique models tested
        models = await conn.fetch("""
            SELECT DISTINCT model_name
            FROM llm_usage_logs
            WHERE user_id = $1 AND metadata->>'source' = 'testing_lab'
            ORDER BY model_name
        """, user_id)

        return {
            "total_tests": stats['total_tests'],
            "total_tokens": int(stats['total_tokens']),
            "total_cost": round(float(stats['total_cost']), 2),
            "avg_latency_ms": int(stats['avg_latency_ms']),
            "models_tested": [row['model_name'] for row in models],
            "last_test_at": stats['last_test_at'].isoformat() if stats['last_test_at'] else None
        }
