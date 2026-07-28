"""
LLM Configuration API
FastAPI endpoints for managing AI servers and 3rd party API keys

Endpoints:
- AI Server Management (list, add, update, delete, test, get models)
- API Key Management (list, add, update, delete, test)
- Active Provider Configuration (get, set)
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field, validator
import asyncpg

from llm_config_manager import (
    LLMConfigManager, AIServer, ServerType, HealthStatus,
    ProviderType, Purpose
)

logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

# AI Server Models
class AIServerCreate(BaseModel):
    """Request model for creating AI server"""
    name: str = Field(..., min_length=1, max_length=255)
    server_type: str = Field(..., description="vllm, ollama, llamacpp, openai-compatible")
    base_url: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    enabled: bool = True
    use_for_chat: bool = False
    use_for_embeddings: bool = False
    use_for_reranking: bool = False
    metadata: Optional[Dict[str, Any]] = None

    @validator('server_type')
    def validate_server_type(cls, v):
        valid_types = [st.value for st in ServerType]
        if v not in valid_types:
            raise ValueError(f"server_type must be one of: {', '.join(valid_types)}")
        return v

    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v


class AIServerUpdate(BaseModel):
    """Request model for updating AI server"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    server_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    enabled: Optional[bool] = None
    use_for_chat: Optional[bool] = None
    use_for_embeddings: Optional[bool] = None
    use_for_reranking: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('server_type')
    def validate_server_type(cls, v):
        if v is not None:
            valid_types = [st.value for st in ServerType]
            if v not in valid_types:
                raise ValueError(f"server_type must be one of: {', '.join(valid_types)}")
        return v

    @validator('base_url')
    def validate_base_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v


class AIServerResponse(BaseModel):
    """Response model for AI server"""
    id: int
    name: str
    server_type: str
    base_url: str
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    enabled: bool
    use_for_chat: bool
    use_for_embeddings: bool
    use_for_reranking: bool
    last_health_check: Optional[datetime] = None
    health_status: str
    metadata: Dict[str, Any] = {}
    created_by: str
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    server_id: int
    status: str
    message: str
    timestamp: datetime


# API Key Models
class APIKeyCreate(BaseModel):
    """Request model for creating API key"""
    provider: str = Field(..., min_length=1, description="openrouter, openai, anthropic, etc.")
    key_name: str = Field(..., min_length=1, max_length=255)
    api_key: str = Field(..., min_length=1)
    use_for_ops_center: bool = False
    metadata: Optional[Dict[str, Any]] = None

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ['openrouter', 'openai', 'anthropic', 'google', 'cohere', 'together', 'fireworks']
        if v not in valid_providers:
            raise ValueError(f"provider must be one of: {', '.join(valid_providers)}")
        return v


class APIKeyUpdate(BaseModel):
    """Request model for updating API key"""
    key_name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = Field(None, min_length=1, description="New API key to re-encrypt")
    enabled: Optional[bool] = None
    use_for_ops_center: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class APIKeyResponse(BaseModel):
    """Response model for API key (MASKED)"""
    id: int
    provider: str
    key_name: str
    masked_key: str
    enabled: bool
    use_for_ops_center: bool
    last_used: Optional[datetime] = None
    requests_count: int
    tokens_used: int
    cost_usd: float
    metadata: Dict[str, Any] = {}
    created_by: str
    created_at: datetime
    updated_at: datetime


class APIKeyTestResponse(BaseModel):
    """Response model for API key test"""
    key_id: int
    success: bool
    message: str
    timestamp: datetime


# Active Provider Models
class ActiveProviderSet(BaseModel):
    """Request model for setting active provider"""
    purpose: str = Field(..., description="chat, embeddings, or reranking")
    provider_type: str = Field(..., description="ai_server or api_key")
    provider_id: int
    fallback_provider_type: Optional[str] = None
    fallback_provider_id: Optional[int] = None

    @validator('purpose')
    def validate_purpose(cls, v):
        valid_purposes = [p.value for p in Purpose]
        if v not in valid_purposes:
            raise ValueError(f"purpose must be one of: {', '.join(valid_purposes)}")
        return v

    @validator('provider_type')
    def validate_provider_type(cls, v):
        valid_types = [pt.value for pt in ProviderType]
        if v not in valid_types:
            raise ValueError(f"provider_type must be one of: {', '.join(valid_types)}")
        return v


class ActiveProviderResponse(BaseModel):
    """Response model for active provider"""
    purpose: str
    provider_type: str
    provider_id: int
    provider: Dict[str, Any]
    fallback_provider_type: Optional[str] = None
    fallback_provider_id: Optional[int] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/llm-config", tags=["LLM Configuration"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_llm_manager(request: Request) -> LLMConfigManager:
    """Get LLM config manager from app state"""
    if not hasattr(request.app.state, 'llm_manager'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM configuration manager not initialized"
        )
    return request.app.state.llm_manager


async def get_current_user(request: Request) -> str:
    """
    Get current user from session

    For now, returns 'admin' - integrate with Keycloak later
    """
    # TODO: Integrate with Keycloak SSO to get real user
    # session_token = request.cookies.get('session_token')
    # user = await validate_session(session_token)
    # return user['keycloak_id']

    return "admin"


async def require_admin(user_id: str = Depends(get_current_user)):
    """Require admin role (all LLM config endpoints need admin)"""
    # TODO: Check if user has admin role via Keycloak
    # For now, allow all authenticated users
    return user_id


# ============================================================================
# AI Server Endpoints
# ============================================================================

@router.get("/servers", response_model=List[AIServerResponse])
async def list_ai_servers(
    enabled_only: bool = False,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    List all AI servers

    Query Parameters:
    - enabled_only: Only return enabled servers
    """
    try:
        servers = await manager.list_ai_servers(enabled_only=enabled_only)
        return servers
    except Exception as e:
        logger.error(f"Failed to list AI servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}", response_model=AIServerResponse)
async def get_ai_server(
    server_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """Get specific AI server by ID"""
    try:
        server = await manager.get_ai_server(server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
        return server
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers", response_model=AIServerResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_server(
    server: AIServerCreate,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Create new AI server configuration

    Request Body:
    - name: Friendly name
    - server_type: vllm, ollama, llamacpp, openai-compatible
    - base_url: Server URL (e.g., http://localhost:8000)
    - api_key: Optional API key for protected endpoints
    - model_path: Optional model path (for vLLM/llama.cpp)
    - enabled: Enable immediately (default: true)
    - use_for_chat/embeddings/reranking: Purpose flags
    - metadata: Additional config (JSON)
    """
    try:
        # Convert Pydantic model to AIServer dataclass
        ai_server = AIServer(
            name=server.name,
            server_type=server.server_type,
            base_url=server.base_url,
            api_key=server.api_key,
            model_path=server.model_path,
            enabled=server.enabled,
            use_for_chat=server.use_for_chat,
            use_for_embeddings=server.use_for_embeddings,
            use_for_reranking=server.use_for_reranking,
            metadata=server.metadata or {},
            created_by=user_id
        )

        created = await manager.add_ai_server(ai_server, user_id)
        return created
    except Exception as e:
        logger.error(f"Failed to create AI server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/servers/{server_id}", response_model=AIServerResponse)
async def update_ai_server(
    server_id: int,
    updates: AIServerUpdate,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Update AI server configuration

    Path Parameters:
    - server_id: Server ID to update

    Request Body: (all fields optional)
    - name, server_type, base_url, api_key, model_path
    - enabled, use_for_chat, use_for_embeddings, use_for_reranking
    - metadata
    """
    try:
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated = await manager.update_ai_server(server_id, update_dict, user_id)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update AI server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_server(
    server_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Delete AI server configuration

    Returns 400 if server is currently in use as active provider
    """
    try:
        await manager.delete_ai_server(server_id, user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete AI server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_id}/test", response_model=HealthCheckResponse)
async def test_ai_server(
    server_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Test connection to AI server

    Attempts to connect to the server and verify it's working.
    Updates health_status and last_health_check in database.

    Returns:
    - status: healthy, degraded, down, unknown
    - message: Details about the health check
    """
    try:
        health_status, message = await manager.test_ai_server(server_id)

        return HealthCheckResponse(
            server_id=server_id,
            status=health_status.value,
            message=message,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to test AI server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/models", response_model=List[str])
async def get_ai_server_models(
    server_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Get list of available models from AI server

    Queries the server's /v1/models endpoint (or /api/tags for Ollama)
    and returns available model names.
    """
    try:
        models = await manager.get_ai_server_models(server_id)
        return models
    except Exception as e:
        logger.error(f"Failed to get models from server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API Key Endpoints
# ============================================================================

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    enabled_only: bool = False,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    List all API keys (MASKED - never returns plaintext keys)

    Query Parameters:
    - enabled_only: Only return enabled keys
    """
    try:
        keys = await manager.list_api_keys(enabled_only=enabled_only)
        return keys
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """Get specific API key by ID (MASKED)"""
    try:
        key = await manager.get_api_key(key_id, decrypt=False)
        if not key:
            raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
        return key
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key: APIKeyCreate,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Create new API key (encrypted storage)

    Request Body:
    - provider: openrouter, openai, anthropic, google, cohere, together, fireworks
    - key_name: Friendly name for UI
    - api_key: Plaintext API key (will be encrypted)
    - use_for_ops_center: Use for ops-center services
    - metadata: Optional metadata (rate limits, etc.)

    Security: API key is encrypted with Fernet before storage
    """
    try:
        created = await manager.add_api_key(
            provider=key.provider,
            key_name=key.key_name,
            api_key=key.api_key,
            use_for_ops_center=key.use_for_ops_center,
            user_id=user_id,
            metadata=key.metadata
        )
        return created
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    updates: APIKeyUpdate,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Update API key

    Path Parameters:
    - key_id: Key ID to update

    Request Body: (all fields optional)
    - key_name: Update friendly name
    - api_key: New API key to re-encrypt
    - enabled: Enable/disable key
    - use_for_ops_center: Toggle ops-center usage
    - metadata: Update metadata
    """
    try:
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated = await manager.update_api_key(key_id, update_dict, user_id)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Delete API key

    Returns 400 if key is currently in use as active provider
    """
    try:
        await manager.delete_api_key(key_id, user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys/{key_id}/test", response_model=APIKeyTestResponse)
async def test_api_key(
    key_id: int,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Test API key validity

    Makes a minimal request to the provider's API to verify the key works.
    Does NOT update usage statistics (tokens_used, requests_count, etc.)

    Returns:
    - success: True if key is valid
    - message: Details about the test result
    """
    try:
        success, message = await manager.test_api_key(key_id)

        return APIKeyTestResponse(
            key_id=key_id,
            success=success,
            message=message,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to test API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Active Provider Endpoints
# ============================================================================

@router.get("/active", response_model=Dict[str, ActiveProviderResponse])
async def get_all_active_providers(
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Get all active providers for all purposes

    Returns a dictionary:
    {
        "chat": {...},
        "embeddings": {...},
        "reranking": {...}
    }
    """
    try:
        providers = await manager.get_all_active_providers()
        return providers
    except Exception as e:
        logger.error(f"Failed to get active providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/{purpose}", response_model=ActiveProviderResponse)
async def get_active_provider(
    purpose: str,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Get active provider for specific purpose

    Path Parameters:
    - purpose: chat, embeddings, or reranking
    """
    try:
        # Validate purpose
        valid_purposes = [p.value for p in Purpose]
        if purpose not in valid_purposes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid purpose. Must be one of: {', '.join(valid_purposes)}"
            )

        provider = await manager.get_active_provider(purpose)
        if not provider:
            raise HTTPException(status_code=404, detail=f"No active provider for {purpose}")

        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active provider for {purpose}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/active", status_code=status.HTTP_200_OK)
async def set_active_provider(
    config: ActiveProviderSet,
    manager: LLMConfigManager = Depends(get_llm_manager),
    user_id: str = Depends(require_admin)
):
    """
    Set active provider for a purpose

    Request Body:
    - purpose: chat, embeddings, or reranking
    - provider_type: ai_server or api_key
    - provider_id: ID of the provider
    - fallback_provider_type: Optional fallback type
    - fallback_provider_id: Optional fallback ID

    Example:
    {
        "purpose": "chat",
        "provider_type": "ai_server",
        "provider_id": 1,
        "fallback_provider_type": "api_key",
        "fallback_provider_id": 2
    }
    """
    try:
        await manager.set_active_provider(
            purpose=config.purpose,
            provider_type=config.provider_type,
            provider_id=config.provider_id,
            user_id=user_id,
            fallback_provider_type=config.fallback_provider_type,
            fallback_provider_id=config.fallback_provider_id
        )

        return {"message": f"Active provider set for {config.purpose}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set active provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LLM Configuration API"}
