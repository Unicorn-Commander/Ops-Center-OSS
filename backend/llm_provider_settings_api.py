"""
LLM Provider Settings API

This module provides endpoints for managing LLM provider configurations,
including OpenAI, Anthropic, Google, Cohere, Together AI, Replicate,
and custom/local endpoints.

Author: Magic Unicorn Unconventional Technology & Stuff Inc
License: MIT
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Literal
import httpx
import asyncio
import time
import json
import logging
from datetime import datetime
from cryptography.fernet import Fernet
import os
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/llm/providers", tags=["LLM Providers"])

# Encryption key for API keys (in production, load from secure vault)
ENCRYPTION_KEY = os.getenv("LLM_ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)


# ============================================================================
# Pydantic Models
# ============================================================================

class ProviderSettings(BaseModel):
    """Provider-specific settings"""
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1)
    timeout: Optional[int] = Field(default=60, ge=1, le=300)
    retry_attempts: Optional[int] = Field(default=3, ge=0, le=10)
    custom_headers: Optional[Dict[str, str]] = {}
    extra_params: Optional[Dict[str, Any]] = {}


class ProviderConfig(BaseModel):
    """LLM Provider Configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal[
        "openai",
        "anthropic",
        "google",
        "cohere",
        "together",
        "replicate",
        "vllm",
        "ollama",
        "custom"
    ]
    api_key: Optional[str] = Field(default=None, description="API key (will be encrypted)")
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")
    models: List[str] = Field(default_factory=list, description="Available models")
    enabled: bool = Field(default=True)
    settings: ProviderSettings = Field(default_factory=ProviderSettings)
    description: Optional[str] = Field(default=None, max_length=500)

    @validator('api_base')
    def validate_api_base(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('API base must start with http:// or https://')
        return v


class ProviderUpdate(BaseModel):
    """Update provider configuration (all fields optional)"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    models: Optional[List[str]] = None
    enabled: Optional[bool] = None
    settings: Optional[ProviderSettings] = None
    description: Optional[str] = Field(default=None, max_length=500)


class ProviderResponse(BaseModel):
    """Provider response with masked API key"""
    id: str
    name: str
    type: str
    api_base: Optional[str]
    models: List[str]
    enabled: bool
    settings: ProviderSettings
    description: Optional[str]
    api_key_configured: bool
    created_at: str
    updated_at: str
    last_test_status: Optional[str] = None
    last_test_time: Optional[str] = None


class TestResult(BaseModel):
    """Provider test result"""
    success: bool
    latency_ms: Optional[int] = None
    model_tested: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AvailableProvider(BaseModel):
    """Available provider type"""
    id: str
    name: str
    description: str
    default_models: List[str]
    requires_api_key: bool
    default_api_base: Optional[str]
    documentation_url: str


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "openai-1": {
        "id": "openai-1",
        "name": "OpenAI",
        "type": "openai",
        "api_key_encrypted": None,
        "api_base": None,
        "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"],
        "enabled": True,
        "settings": ProviderSettings().dict(),
        "description": "OpenAI GPT models",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_test_status": None,
        "last_test_time": None,
    },
    "anthropic-1": {
        "id": "anthropic-1",
        "name": "Anthropic",
        "type": "anthropic",
        "api_key_encrypted": None,
        "api_base": None,
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "enabled": True,
        "settings": ProviderSettings().dict(),
        "description": "Anthropic Claude models",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_test_status": None,
        "last_test_time": None,
    },
    "vllm-local": {
        "id": "vllm-local",
        "name": "vLLM Local",
        "type": "vllm",
        "api_key_encrypted": None,
        "api_base": "http://unicorn-vllm:8000",
        "models": ["Qwen/Qwen2.5-32B-Instruct-AWQ"],
        "enabled": True,
        "settings": ProviderSettings().dict(),
        "description": "Local vLLM inference",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_test_status": "healthy",
        "last_test_time": datetime.utcnow().isoformat(),
    },
}

# Available provider types
AVAILABLE_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "description": "OpenAI GPT models (GPT-4, GPT-3.5, etc.)",
        "default_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"],
        "requires_api_key": True,
        "default_api_base": "https://api.openai.com/v1",
        "documentation_url": "https://platform.openai.com/docs/api-reference",
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "description": "Anthropic Claude models",
        "default_models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "requires_api_key": True,
        "default_api_base": "https://api.anthropic.com",
        "documentation_url": "https://docs.anthropic.com/claude/reference",
    },
    {
        "id": "google",
        "name": "Google AI",
        "description": "Google Gemini models",
        "default_models": ["gemini-pro", "gemini-pro-vision", "gemini-ultra"],
        "requires_api_key": True,
        "default_api_base": "https://generativelanguage.googleapis.com/v1",
        "documentation_url": "https://ai.google.dev/docs",
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "description": "Cohere Command models",
        "default_models": ["command", "command-light", "command-nightly"],
        "requires_api_key": True,
        "default_api_base": "https://api.cohere.ai/v1",
        "documentation_url": "https://docs.cohere.com/reference/about",
    },
    {
        "id": "together",
        "name": "Together AI",
        "description": "Together AI hosted models",
        "default_models": ["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-2-70b-chat-hf"],
        "requires_api_key": True,
        "default_api_base": "https://api.together.xyz/v1",
        "documentation_url": "https://docs.together.ai/reference",
    },
    {
        "id": "replicate",
        "name": "Replicate",
        "description": "Replicate hosted models",
        "default_models": ["meta/llama-2-70b-chat", "mistralai/mixtral-8x7b-instruct-v0.1"],
        "requires_api_key": True,
        "default_api_base": "https://api.replicate.com/v1",
        "documentation_url": "https://replicate.com/docs/reference/http",
    },
    {
        "id": "vllm",
        "name": "vLLM (Local)",
        "description": "Local vLLM inference server",
        "default_models": ["custom"],
        "requires_api_key": False,
        "default_api_base": "http://localhost:8000",
        "documentation_url": "https://docs.vllm.ai/en/latest/",
    },
    {
        "id": "ollama",
        "name": "Ollama (Local)",
        "description": "Local Ollama inference server",
        "default_models": ["llama2", "mistral", "codellama"],
        "requires_api_key": False,
        "default_api_base": "http://localhost:11434",
        "documentation_url": "https://github.com/ollama/ollama/blob/main/docs/api.md",
    },
    {
        "id": "custom",
        "name": "Custom Endpoint",
        "description": "Custom OpenAI-compatible API endpoint",
        "default_models": ["custom"],
        "requires_api_key": False,
        "default_api_base": "http://localhost:8000",
        "documentation_url": "https://platform.openai.com/docs/api-reference",
    },
]


# ============================================================================
# Helper Functions
# ============================================================================

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()


def mask_api_key(api_key: Optional[str]) -> Optional[str]:
    """Mask API key for display"""
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


def generate_provider_id(name: str, provider_type: str) -> str:
    """Generate unique provider ID"""
    timestamp = str(time.time())
    hash_input = f"{name}-{provider_type}-{timestamp}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:12]


def provider_to_response(provider_data: Dict[str, Any]) -> ProviderResponse:
    """Convert internal provider data to response model"""
    return ProviderResponse(
        id=provider_data["id"],
        name=provider_data["name"],
        type=provider_data["type"],
        api_base=provider_data.get("api_base"),
        models=provider_data["models"],
        enabled=provider_data["enabled"],
        settings=ProviderSettings(**provider_data["settings"]),
        description=provider_data.get("description"),
        api_key_configured=provider_data.get("api_key_encrypted") is not None,
        created_at=provider_data["created_at"],
        updated_at=provider_data["updated_at"],
        last_test_status=provider_data.get("last_test_status"),
        last_test_time=provider_data.get("last_test_time"),
    )


async def test_openai_provider(api_key: str, api_base: Optional[str], model: str) -> TestResult:
    """Test OpenAI-compatible provider"""
    start_time = time.time()
    base_url = api_base or "https://api.openai.com/v1"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5,
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return TestResult(
                    success=True,
                    latency_ms=latency_ms,
                    model_tested=model,
                    details={"status_code": 200}
                )
            else:
                return TestResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    details={"status_code": response.status_code}
                )

    except Exception as e:
        return TestResult(
            success=False,
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


async def test_anthropic_provider(api_key: str, api_base: Optional[str], model: str) -> TestResult:
    """Test Anthropic provider"""
    start_time = time.time()
    base_url = api_base or "https://api.anthropic.com"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5,
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return TestResult(
                    success=True,
                    latency_ms=latency_ms,
                    model_tested=model,
                    details={"status_code": 200}
                )
            else:
                return TestResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    details={"status_code": response.status_code}
                )

    except Exception as e:
        return TestResult(
            success=False,
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


async def test_google_provider(api_key: str, api_base: Optional[str], model: str) -> TestResult:
    """Test Google AI provider"""
    start_time = time.time()
    base_url = api_base or "https://generativelanguage.googleapis.com/v1"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": "Hello"}]}],
                    "generationConfig": {"maxOutputTokens": 5}
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return TestResult(
                    success=True,
                    latency_ms=latency_ms,
                    model_tested=model,
                    details={"status_code": 200}
                )
            else:
                return TestResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    details={"status_code": response.status_code}
                )

    except Exception as e:
        return TestResult(
            success=False,
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


async def test_vllm_provider(api_base: str, model: str) -> TestResult:
    """Test vLLM local provider"""
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test health endpoint first
            health_response = await client.get(f"{api_base}/health")
            if health_response.status_code != 200:
                return TestResult(
                    success=False,
                    error="vLLM health check failed",
                    details={"status_code": health_response.status_code}
                )

            # Test inference
            response = await client.post(
                f"{api_base}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5,
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return TestResult(
                    success=True,
                    latency_ms=latency_ms,
                    model_tested=model,
                    details={"status_code": 200}
                )
            else:
                return TestResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    details={"status_code": response.status_code}
                )

    except Exception as e:
        return TestResult(
            success=False,
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=Dict[str, List[ProviderResponse]])
async def list_providers():
    """
    List all configured LLM providers.

    Returns:
        Dictionary with 'providers' key containing list of provider configurations
    """
    providers = [provider_to_response(p) for p in PROVIDERS.values()]
    return {"providers": providers}


@router.get("/available", response_model=Dict[str, List[AvailableProvider]])
async def list_available_provider_types():
    """
    List all available LLM provider types that can be configured.

    Returns:
        Dictionary with 'providers' key containing available provider types
    """
    return {"providers": [AvailableProvider(**p) for p in AVAILABLE_PROVIDERS]}


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(config: ProviderConfig):
    """
    Add a new LLM provider configuration.

    Args:
        config: Provider configuration

    Returns:
        Created provider configuration

    Raises:
        HTTPException: If provider creation fails
    """
    # Generate unique ID
    provider_id = generate_provider_id(config.name, config.type)

    # Check if provider with same name exists
    for provider in PROVIDERS.values():
        if provider["name"].lower() == config.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider with name '{config.name}' already exists"
            )

    # Encrypt API key if provided
    api_key_encrypted = None
    if config.api_key:
        api_key_encrypted = encrypt_api_key(config.api_key)

    # Create provider
    now = datetime.utcnow().isoformat()
    provider_data = {
        "id": provider_id,
        "name": config.name,
        "type": config.type,
        "api_key_encrypted": api_key_encrypted,
        "api_base": config.api_base,
        "models": config.models,
        "enabled": config.enabled,
        "settings": config.settings.dict(),
        "description": config.description,
        "created_at": now,
        "updated_at": now,
        "last_test_status": None,
        "last_test_time": None,
    }

    PROVIDERS[provider_id] = provider_data

    logger.info(f"Created LLM provider: {provider_id} ({config.name})")

    return provider_to_response(provider_data)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: str, update: ProviderUpdate):
    """
    Update an existing LLM provider configuration.

    Args:
        provider_id: Provider ID
        update: Fields to update

    Returns:
        Updated provider configuration

    Raises:
        HTTPException: If provider not found
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found"
        )

    provider = PROVIDERS[provider_id]

    # Update fields
    if update.name is not None:
        provider["name"] = update.name
    if update.api_key is not None:
        provider["api_key_encrypted"] = encrypt_api_key(update.api_key)
    if update.api_base is not None:
        provider["api_base"] = update.api_base
    if update.models is not None:
        provider["models"] = update.models
    if update.enabled is not None:
        provider["enabled"] = update.enabled
    if update.settings is not None:
        provider["settings"] = update.settings.dict()
    if update.description is not None:
        provider["description"] = update.description

    provider["updated_at"] = datetime.utcnow().isoformat()

    logger.info(f"Updated LLM provider: {provider_id}")

    return provider_to_response(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: str):
    """
    Remove an LLM provider configuration.

    Args:
        provider_id: Provider ID to delete

    Raises:
        HTTPException: If provider not found
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found"
        )

    provider_name = PROVIDERS[provider_id]["name"]
    del PROVIDERS[provider_id]

    logger.info(f"Deleted LLM provider: {provider_id} ({provider_name})")

    return None


@router.post("/{provider_id}/test", response_model=TestResult)
async def test_provider_connection(provider_id: str):
    """
    Test connection to an LLM provider.

    Sends a minimal request to the provider to verify:
    - API key is valid
    - Endpoint is accessible
    - Model is available

    Args:
        provider_id: Provider ID to test

    Returns:
        Test result with success status, latency, and error details

    Raises:
        HTTPException: If provider not found or not enabled
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found"
        )

    provider = PROVIDERS[provider_id]

    if not provider["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider['name']}' is disabled"
        )

    # Get API key if encrypted
    api_key = None
    if provider.get("api_key_encrypted"):
        api_key = decrypt_api_key(provider["api_key_encrypted"])

    # Get first model for testing
    if not provider["models"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider['name']}' has no models configured"
        )

    test_model = provider["models"][0]
    provider_type = provider["type"]
    api_base = provider.get("api_base")

    # Test based on provider type
    try:
        if provider_type == "openai":
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OpenAI provider requires API key"
                )
            result = await test_openai_provider(api_key, api_base, test_model)

        elif provider_type == "anthropic":
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Anthropic provider requires API key"
                )
            result = await test_anthropic_provider(api_key, api_base, test_model)

        elif provider_type == "google":
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google AI provider requires API key"
                )
            result = await test_google_provider(api_key, api_base, test_model)

        elif provider_type in ["vllm", "ollama", "custom"]:
            if not api_base:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{provider_type} provider requires API base URL"
                )
            result = await test_vllm_provider(api_base, test_model)

        elif provider_type in ["cohere", "together", "replicate"]:
            # These use OpenAI-compatible API
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{provider_type} provider requires API key"
                )
            result = await test_openai_provider(api_key, api_base, test_model)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Testing not implemented for provider type: {provider_type}"
            )

        # Update test status
        provider["last_test_status"] = "healthy" if result.success else "unhealthy"
        provider["last_test_time"] = datetime.utcnow().isoformat()

        logger.info(f"Tested provider {provider_id}: {result.success}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider {provider_id}: {e}")
        return TestResult(
            success=False,
            error=str(e),
            details={"exception_type": type(e).__name__}
        )


# ============================================================================
# Additional Utility Endpoints
# ============================================================================

@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str):
    """
    Get details of a specific LLM provider.

    Args:
        provider_id: Provider ID

    Returns:
        Provider configuration

    Raises:
        HTTPException: If provider not found
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found"
        )

    return provider_to_response(PROVIDERS[provider_id])


@router.post("/{provider_id}/toggle", response_model=ProviderResponse)
async def toggle_provider(provider_id: str):
    """
    Toggle provider enabled/disabled status.

    Args:
        provider_id: Provider ID

    Returns:
        Updated provider configuration

    Raises:
        HTTPException: If provider not found
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_id}' not found"
        )

    provider = PROVIDERS[provider_id]
    provider["enabled"] = not provider["enabled"]
    provider["updated_at"] = datetime.utcnow().isoformat()

    status_str = "enabled" if provider["enabled"] else "disabled"
    logger.info(f"Provider {provider_id} {status_str}")

    return provider_to_response(provider)
