"""
Local Inference API Router for Ops-Center

Provides REST endpoints for managing local inference providers (Ollama, llama.cpp, vLLM, etc.).
Supports provider management, model loading/unloading, GPU monitoring, and auto-detection.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import logging
import sys
import os
from datetime import datetime

# Import local inference modules
from local_inference.base_provider import (
    LocalInferenceProvider,
    ProviderSettings,
    ProviderStatus,
    ModelStatus,
    ModelInfo,
    GPUInfo,
    HealthCheckResult,
    ProviderError,
    ProviderNotAvailableError,
    ModelNotFoundError,
    ModelLoadError,
    ModelUnloadError,
)
from local_inference.registry import (
    get_registry,
    initialize_registry,
    ProviderRegistry,
)
from local_inference.config import (
    get_config,
    save_config,
    LocalInferenceConfig,
    ProviderConfig,
    ProviderConfigStatus,
    GlobalConfig,
    get_provider_config,
    update_provider_config,
    set_provider_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/local-inference",
    tags=["local-inference"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    },
)


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(request: Request):
    """Verify user is authenticated (uses Redis session manager)"""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    return user


async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    user = await get_current_user(request)

    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# =============================================================================
# Request/Response Models
# =============================================================================

class ModuleStatusResponse(BaseModel):
    """Response model for module status"""
    enabled: bool = Field(..., description="Whether the local inference module is enabled")
    active_providers: List[str] = Field(..., description="List of active provider names")
    detected_providers: List[str] = Field(..., description="List of detected provider names")
    total_providers: int = Field(..., description="Total number of registered providers")
    gpu_available: bool = Field(..., description="Whether GPU is available")
    last_detection: Optional[datetime] = Field(None, description="Last auto-detection timestamp")


class ModuleEnableRequest(BaseModel):
    """Request model for enabling the module"""
    auto_detect: bool = Field(True, description="Whether to run auto-detection on enable")


class ModuleEnableResponse(BaseModel):
    """Response model for enabling the module"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    detected_providers: List[str] = Field(default_factory=list, description="Providers detected")


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration"""
    global_config: Optional[GlobalConfig] = Field(None, description="Global settings to update")
    providers: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Provider configurations to update"
    )


class ProviderListResponse(BaseModel):
    """Response model for provider list"""
    providers: List[Dict[str, Any]] = Field(..., description="List of provider information")
    total: int = Field(..., description="Total number of providers")


class ProviderDetailResponse(BaseModel):
    """Response model for provider details"""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Provider description")
    status: ProviderStatus = Field(..., description="Current status")
    enabled: bool = Field(..., description="Whether provider is enabled")
    url: str = Field(..., description="Provider API URL")
    capabilities: Dict[str, bool] = Field(..., description="Provider capabilities")
    settings: ProviderSettings = Field(..., description="Provider settings")
    health: Optional[HealthCheckResult] = Field(None, description="Latest health check result")


class ProviderEnableResponse(BaseModel):
    """Response model for provider enable/disable"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    provider: str = Field(..., description="Provider name")
    enabled: bool = Field(..., description="Current enabled status")


class ProviderSettingsUpdateRequest(BaseModel):
    """Request model for updating provider settings"""
    url: Optional[str] = Field(None, description="Provider API URL")
    enabled: Optional[bool] = Field(None, description="Whether provider is enabled")
    idle_timeout_seconds: Optional[int] = Field(None, description="Idle timeout in seconds")
    max_loaded_models: Optional[int] = Field(None, description="Maximum loaded models")
    api_key: Optional[str] = Field(None, description="API key if required")
    timeout_seconds: Optional[int] = Field(None, description="HTTP request timeout")
    gpu_layers: Optional[int] = Field(None, description="Default GPU layers")
    context_size: Optional[int] = Field(None, description="Default context size")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra provider-specific settings")


class ModelListResponse(BaseModel):
    """Response model for model list"""
    models: List[ModelInfo] = Field(..., description="List of models")
    total: int = Field(..., description="Total number of models")
    loaded_count: int = Field(..., description="Number of loaded models")


class ModelLoadRequest(BaseModel):
    """Request model for loading a model"""
    gpu_layers: Optional[int] = Field(None, description="Number of GPU layers to use")
    context_size: Optional[int] = Field(None, description="Context window size")
    batch_size: Optional[int] = Field(None, description="Batch size for inference")
    extra_options: Optional[Dict[str, Any]] = Field(None, description="Extra loading options")


class ModelOperationResponse(BaseModel):
    """Response model for model load/unload operations"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    model_id: str = Field(..., description="Model identifier")
    operation: str = Field(..., description="Operation performed (load/unload)")
    duration_ms: Optional[float] = Field(None, description="Operation duration in milliseconds")


class GPUStatusResponse(BaseModel):
    """Response model for GPU status"""
    devices: List[GPUInfo] = Field(..., description="List of GPU devices")
    total_count: int = Field(..., description="Total number of GPUs")
    total_memory_mb: int = Field(..., description="Total GPU memory in MB")
    used_memory_mb: int = Field(..., description="Used GPU memory in MB")
    utilization_average: float = Field(..., description="Average GPU utilization percentage")


class AutoDetectRequest(BaseModel):
    """Request model for auto-detection"""
    timeout: float = Field(2.0, description="Timeout for health checks in seconds")
    providers: Optional[List[str]] = Field(None, description="Specific providers to check")


class AutoDetectResponse(BaseModel):
    """Response model for auto-detection"""
    success: bool = Field(..., description="Whether detection completed")
    detected: Dict[str, bool] = Field(..., description="Provider detection results")
    message: str = Field(..., description="Status message")


# =============================================================================
# Module Status Endpoints
# =============================================================================

@router.get(
    "/status",
    response_model=ModuleStatusResponse,
    summary="Get module status",
    description="Get the current status of the local inference module including active providers and GPU availability.",
)
async def get_module_status(current_user: dict = Depends(get_current_user)):
    """
    Get the current status of the local inference module.

    Returns:
        ModuleStatusResponse with module status information
    """
    try:
        registry = get_registry()
        config = await get_config()

        # Get all providers
        all_providers = registry.get_all_providers()

        # Get active providers
        active_providers = await registry.get_active_providers()
        active_names = [p.provider_name for p in active_providers]

        # Check GPU availability
        gpu_available = False
        for provider in active_providers:
            try:
                gpus = await provider.get_gpu_status()
                if gpus:
                    gpu_available = True
                    break
            except Exception:
                pass

        return ModuleStatusResponse(
            enabled=config.global_config.auto_detect_on_startup,
            active_providers=active_names,
            detected_providers=list(all_providers.keys()),
            total_providers=len(all_providers),
            gpu_available=gpu_available,
            last_detection=config.updated_at,
        )

    except Exception as e:
        logger.error(f"Failed to get module status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/enable",
    response_model=ModuleEnableResponse,
    summary="Enable local inference module",
    description="Enable the local inference module and optionally run auto-detection.",
)
async def enable_module(
    request: ModuleEnableRequest = ModuleEnableRequest(),
    admin: dict = Depends(require_admin),
):
    """
    Enable the local inference module.

    Args:
        request: Enable request with optional auto-detection flag

    Returns:
        ModuleEnableResponse with operation result
    """
    try:
        registry = get_registry()
        await registry.initialize()

        detected_providers = []

        if request.auto_detect:
            detection_results = await registry.auto_detect()
            detected_providers = [
                name for name, detected in detection_results.items() if detected
            ]

        # Update config
        config = await get_config()
        config.global_config.auto_detect_on_startup = True
        await save_config(config, updated_by=admin.get("email", "admin"))

        return ModuleEnableResponse(
            success=True,
            message="Local inference module enabled successfully",
            detected_providers=detected_providers,
        )

    except Exception as e:
        logger.error(f"Failed to enable module: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/disable",
    response_model=ModuleEnableResponse,
    summary="Disable local inference module",
    description="Disable the local inference module and shut down all providers.",
)
async def disable_module(admin: dict = Depends(require_admin)):
    """
    Disable the local inference module.

    Returns:
        ModuleEnableResponse with operation result
    """
    try:
        registry = get_registry()
        await registry.shutdown()

        # Update config
        config = await get_config()
        config.global_config.auto_detect_on_startup = False
        await save_config(config, updated_by=admin.get("email", "admin"))

        return ModuleEnableResponse(
            success=True,
            message="Local inference module disabled successfully",
            detected_providers=[],
        )

    except Exception as e:
        logger.error(f"Failed to disable module: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/config",
    response_model=LocalInferenceConfig,
    summary="Get full configuration",
    description="Get the complete local inference configuration including global settings and all providers.",
)
async def get_full_config(current_user: dict = Depends(get_current_user)):
    """
    Get the complete local inference configuration.

    Returns:
        LocalInferenceConfig with all settings
    """
    try:
        config = await get_config()
        return config

    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/config",
    response_model=LocalInferenceConfig,
    summary="Update configuration",
    description="Update the local inference configuration. Only provided fields are updated.",
)
async def update_full_config(
    request: ConfigUpdateRequest,
    admin: dict = Depends(require_admin),
):
    """
    Update the local inference configuration.

    Args:
        request: Configuration updates

    Returns:
        Updated LocalInferenceConfig
    """
    try:
        config = await get_config()

        # Update global config if provided
        if request.global_config:
            for field, value in request.global_config.dict(exclude_unset=True).items():
                setattr(config.global_config, field, value)

        # Update provider configs if provided
        if request.providers:
            for provider_name, updates in request.providers.items():
                if provider_name in config.providers:
                    provider = config.providers[provider_name]
                    for field, value in updates.items():
                        if hasattr(provider, field):
                            setattr(provider, field, value)

        # Save updated config
        await save_config(config, updated_by=admin.get("email", "admin"))

        # Apply changes to running registry
        registry = get_registry()
        for provider_name, updates in (request.providers or {}).items():
            registry.update_provider_settings(provider_name, updates)

        return config

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Provider Management Endpoints
# =============================================================================

@router.get(
    "/providers",
    response_model=ProviderListResponse,
    summary="List all providers",
    description="List all registered local inference providers with their current status.",
)
async def list_providers(current_user: dict = Depends(get_current_user)):
    """
    List all registered providers with their status.

    Returns:
        ProviderListResponse with provider information
    """
    try:
        registry = get_registry()
        all_providers = registry.get_all_providers()
        health_results = await registry.check_all_health()

        providers_list = []
        for name, provider in all_providers.items():
            health = health_results.get(name)
            providers_list.append({
                "name": provider.provider_name,
                "display_name": provider.display_name,
                "description": provider.description,
                "enabled": provider.settings.enabled,
                "url": provider.settings.url,
                "status": health.status if health else ProviderStatus.UNKNOWN,
                "loaded_models": health.loaded_models if health else 0,
                "available_models": health.available_models if health else 0,
                "capabilities": {
                    "idle_unload": provider.supports_idle_unload,
                    "multi_gpu": provider.supports_multi_gpu,
                    "model_hot_swap": provider.supports_model_hot_swap,
                    "quantization": provider.supports_quantization,
                    "embeddings": provider.supports_embeddings,
                    "vision": provider.supports_vision,
                },
            })

        return ProviderListResponse(
            providers=providers_list,
            total=len(providers_list),
        )

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/providers/{provider}",
    response_model=ProviderDetailResponse,
    summary="Get provider details",
    description="Get detailed information about a specific provider.",
)
async def get_provider_detail(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific provider.

    Args:
        provider: Provider name

    Returns:
        ProviderDetailResponse with provider details
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        health = await registry.check_health(provider)

        return ProviderDetailResponse(
            name=prov.provider_name,
            display_name=prov.display_name,
            description=prov.description,
            status=health.status,
            enabled=prov.settings.enabled,
            url=prov.settings.url,
            capabilities={
                "idle_unload": prov.supports_idle_unload,
                "multi_gpu": prov.supports_multi_gpu,
                "model_hot_swap": prov.supports_model_hot_swap,
                "quantization": prov.supports_quantization,
                "embeddings": prov.supports_embeddings,
                "vision": prov.supports_vision,
            },
            settings=prov.settings,
            health=health,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/providers/{provider}/enable",
    response_model=ProviderEnableResponse,
    summary="Enable provider",
    description="Enable a specific provider.",
)
async def enable_provider(
    provider: str,
    admin: dict = Depends(require_admin),
):
    """
    Enable a specific provider.

    Args:
        provider: Provider name

    Returns:
        ProviderEnableResponse with operation result
    """
    try:
        registry = get_registry()

        if not registry.get_provider(provider):
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        success = registry.enable_provider(provider)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to enable provider")

        # Update config
        await set_provider_status(
            provider,
            ProviderConfigStatus.ENABLED,
            updated_by=admin.get("email", "admin"),
        )

        return ProviderEnableResponse(
            success=True,
            message=f"Provider '{provider}' enabled successfully",
            provider=provider,
            enabled=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/providers/{provider}/disable",
    response_model=ProviderEnableResponse,
    summary="Disable provider",
    description="Disable a specific provider.",
)
async def disable_provider(
    provider: str,
    admin: dict = Depends(require_admin),
):
    """
    Disable a specific provider.

    Args:
        provider: Provider name

    Returns:
        ProviderEnableResponse with operation result
    """
    try:
        registry = get_registry()

        if not registry.get_provider(provider):
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        success = registry.disable_provider(provider)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to disable provider")

        # Update config
        await set_provider_status(
            provider,
            ProviderConfigStatus.DISABLED,
            updated_by=admin.get("email", "admin"),
        )

        return ProviderEnableResponse(
            success=True,
            message=f"Provider '{provider}' disabled successfully",
            provider=provider,
            enabled=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/providers/{provider}/health",
    response_model=HealthCheckResult,
    summary="Check provider health",
    description="Perform a health check on a specific provider.",
)
async def check_provider_health(
    provider: str,
    force_refresh: bool = Query(False, description="Force a fresh health check"),
    current_user: dict = Depends(get_current_user),
):
    """
    Perform a health check on a specific provider.

    Args:
        provider: Provider name
        force_refresh: Whether to force a fresh check

    Returns:
        HealthCheckResult with health status
    """
    try:
        registry = get_registry()

        if not registry.get_provider(provider):
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        health = await registry.check_health(provider, force_refresh=force_refresh)
        return health

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check provider health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/providers/{provider}/settings",
    response_model=ProviderSettings,
    summary="Get provider settings",
    description="Get the current settings for a specific provider.",
)
async def get_provider_settings(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current settings for a specific provider.

    Args:
        provider: Provider name

    Returns:
        ProviderSettings with current settings
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        return await prov.get_settings()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/providers/{provider}/settings",
    response_model=ProviderSettings,
    summary="Update provider settings",
    description="Update the settings for a specific provider.",
)
async def update_provider_settings(
    provider: str,
    request: ProviderSettingsUpdateRequest,
    admin: dict = Depends(require_admin),
):
    """
    Update the settings for a specific provider.

    Args:
        provider: Provider name
        request: Settings to update

    Returns:
        Updated ProviderSettings
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        # Convert request to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        # Update provider settings
        updated = await prov.update_settings(updates)

        # Also update config
        await update_provider_config(
            provider,
            updates,
            updated_by=admin.get("email", "admin"),
        )

        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update provider settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Model Management Endpoints (Unified)
# =============================================================================

@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="List all models",
    description="List all models from all active providers.",
)
async def list_all_models(
    status: Optional[ModelStatus] = Query(None, description="Filter by model status"),
    provider: Optional[str] = Query(None, description="Filter by provider name"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all models from all active providers.

    Args:
        status: Optional filter by model status
        provider: Optional filter by provider name

    Returns:
        ModelListResponse with all models
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        all_models = []
        loaded_count = 0

        for prov in active_providers:
            # Skip if filtering by provider and this isn't the one
            if provider and prov.provider_name != provider:
                continue

            try:
                models = await prov.list_models()

                for model in models:
                    # Filter by status if specified
                    if status and model.status != status:
                        continue

                    all_models.append(model)

                    if model.status == ModelStatus.LOADED:
                        loaded_count += 1

            except Exception as e:
                logger.warning(f"Failed to list models from {prov.provider_name}: {e}")

        return ModelListResponse(
            models=all_models,
            total=len(all_models),
            loaded_count=loaded_count,
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/models/{model_id:path}",
    response_model=ModelInfo,
    summary="Get model details",
    description="Get detailed information about a specific model.",
)
async def get_model_detail(
    model_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific model.

    Args:
        model_id: Model identifier (may include provider prefix)

    Returns:
        ModelInfo with model details
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        # Try to find the model in active providers
        for prov in active_providers:
            try:
                model = await prov.get_model_status(model_id)
                if model:
                    return model
            except ModelNotFoundError:
                continue
            except Exception as e:
                logger.warning(f"Error getting model from {prov.provider_name}: {e}")

        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/models/{model_id:path}/load",
    response_model=ModelOperationResponse,
    summary="Load model",
    description="Load a model into memory across active providers.",
)
async def load_model(
    model_id: str,
    request: ModelLoadRequest = ModelLoadRequest(),
    admin: dict = Depends(require_admin),
):
    """
    Load a model into memory.

    Args:
        model_id: Model identifier
        request: Loading options

    Returns:
        ModelOperationResponse with operation result
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        # Build options dict
        options = {}
        if request.gpu_layers is not None:
            options["gpu_layers"] = request.gpu_layers
        if request.context_size is not None:
            options["context_size"] = request.context_size
        if request.batch_size is not None:
            options["batch_size"] = request.batch_size
        if request.extra_options:
            options.update(request.extra_options)

        # Try to load the model from first provider that has it
        for prov in active_providers:
            try:
                start_time = datetime.now()
                result = await prov.load_model(model_id, options if options else None)
                duration = (datetime.now() - start_time).total_seconds() * 1000

                return ModelOperationResponse(
                    success=True,
                    message=f"Model '{model_id}' loaded successfully via {prov.display_name}",
                    model_id=model_id,
                    operation="load",
                    duration_ms=duration,
                )

            except ModelNotFoundError:
                continue
            except ModelLoadError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.warning(f"Failed to load model via {prov.provider_name}: {e}")

        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in any provider")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/models/{model_id:path}/unload",
    response_model=ModelOperationResponse,
    summary="Unload model",
    description="Unload a model from memory.",
)
async def unload_model(
    model_id: str,
    admin: dict = Depends(require_admin),
):
    """
    Unload a model from memory.

    Args:
        model_id: Model identifier

    Returns:
        ModelOperationResponse with operation result
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        # Try to unload the model from first provider that has it loaded
        for prov in active_providers:
            try:
                start_time = datetime.now()
                result = await prov.unload_model(model_id)
                duration = (datetime.now() - start_time).total_seconds() * 1000

                return ModelOperationResponse(
                    success=True,
                    message=f"Model '{model_id}' unloaded successfully via {prov.display_name}",
                    model_id=model_id,
                    operation="unload",
                    duration_ms=duration,
                )

            except ModelNotFoundError:
                continue
            except ModelUnloadError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.warning(f"Failed to unload model via {prov.provider_name}: {e}")

        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found or not loaded")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Provider-Specific Model Endpoints
# =============================================================================

@router.get(
    "/providers/{provider}/models",
    response_model=ModelListResponse,
    summary="List provider models",
    description="List all models for a specific provider.",
)
async def list_provider_models(
    provider: str,
    status: Optional[ModelStatus] = Query(None, description="Filter by model status"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all models for a specific provider.

    Args:
        provider: Provider name
        status: Optional filter by model status

    Returns:
        ModelListResponse with provider's models
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        models = await prov.list_models()
        loaded_count = 0

        # Filter by status if specified
        if status:
            models = [m for m in models if m.status == status]

        loaded_count = sum(1 for m in models if m.status == ModelStatus.LOADED)

        return ModelListResponse(
            models=models,
            total=len(models),
            loaded_count=loaded_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list provider models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/providers/{provider}/models/{model_id:path}/load",
    response_model=ModelOperationResponse,
    summary="Load model on provider",
    description="Load a model on a specific provider.",
)
async def load_model_on_provider(
    provider: str,
    model_id: str,
    request: ModelLoadRequest = ModelLoadRequest(),
    admin: dict = Depends(require_admin),
):
    """
    Load a model on a specific provider.

    Args:
        provider: Provider name
        model_id: Model identifier
        request: Loading options

    Returns:
        ModelOperationResponse with operation result
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        # Build options dict
        options = {}
        if request.gpu_layers is not None:
            options["gpu_layers"] = request.gpu_layers
        if request.context_size is not None:
            options["context_size"] = request.context_size
        if request.batch_size is not None:
            options["batch_size"] = request.batch_size
        if request.extra_options:
            options.update(request.extra_options)

        start_time = datetime.now()
        result = await prov.load_model(model_id, options if options else None)
        duration = (datetime.now() - start_time).total_seconds() * 1000

        return ModelOperationResponse(
            success=True,
            message=f"Model '{model_id}' loaded successfully on {prov.display_name}",
            model_id=model_id,
            operation="load",
            duration_ms=duration,
        )

    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModelLoadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model on provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/providers/{provider}/models/{model_id:path}/unload",
    response_model=ModelOperationResponse,
    summary="Unload model from provider",
    description="Unload a model from a specific provider.",
)
async def unload_model_from_provider(
    provider: str,
    model_id: str,
    admin: dict = Depends(require_admin),
):
    """
    Unload a model from a specific provider.

    Args:
        provider: Provider name
        model_id: Model identifier

    Returns:
        ModelOperationResponse with operation result
    """
    try:
        registry = get_registry()
        prov = registry.get_provider(provider)

        if not prov:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

        start_time = datetime.now()
        result = await prov.unload_model(model_id)
        duration = (datetime.now() - start_time).total_seconds() * 1000

        return ModelOperationResponse(
            success=True,
            message=f"Model '{model_id}' unloaded successfully from {prov.display_name}",
            model_id=model_id,
            operation="unload",
            duration_ms=duration,
        )

    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModelUnloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model from provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GPU Monitoring Endpoints
# =============================================================================

@router.get(
    "/gpu/status",
    response_model=GPUStatusResponse,
    summary="Get GPU status",
    description="Get GPU status from all active providers.",
)
async def get_gpu_status(current_user: dict = Depends(get_current_user)):
    """
    Get GPU status from all active providers.

    Returns:
        GPUStatusResponse with GPU information
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        all_gpus = []
        seen_indices = set()

        # Collect GPU info from all providers
        for prov in active_providers:
            try:
                gpus = await prov.get_gpu_status()
                for gpu in gpus:
                    # Avoid duplicates based on index
                    if gpu.index not in seen_indices:
                        all_gpus.append(gpu)
                        seen_indices.add(gpu.index)
            except Exception as e:
                logger.warning(f"Failed to get GPU status from {prov.provider_name}: {e}")

        # Calculate totals
        total_memory = sum(g.memory_total_mb for g in all_gpus)
        used_memory = sum(g.memory_used_mb for g in all_gpus)
        avg_utilization = (
            sum(g.utilization_percent for g in all_gpus) / len(all_gpus)
            if all_gpus else 0.0
        )

        return GPUStatusResponse(
            devices=all_gpus,
            total_count=len(all_gpus),
            total_memory_mb=total_memory,
            used_memory_mb=used_memory,
            utilization_average=avg_utilization,
        )

    except Exception as e:
        logger.error(f"Failed to get GPU status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/gpu/devices",
    response_model=List[GPUInfo],
    summary="List GPU devices",
    description="List all GPU devices with detailed information.",
)
async def list_gpu_devices(current_user: dict = Depends(get_current_user)):
    """
    List all GPU devices with detailed information.

    Returns:
        List of GPUInfo for each device
    """
    try:
        registry = get_registry()
        active_providers = await registry.get_active_providers()

        all_gpus = []
        seen_indices = set()

        for prov in active_providers:
            try:
                gpus = await prov.get_gpu_status()
                for gpu in gpus:
                    if gpu.index not in seen_indices:
                        all_gpus.append(gpu)
                        seen_indices.add(gpu.index)
            except Exception as e:
                logger.warning(f"Failed to get GPU info from {prov.provider_name}: {e}")

        return all_gpus

    except Exception as e:
        logger.error(f"Failed to list GPU devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Auto-Detection Endpoints
# =============================================================================

@router.post(
    "/detect",
    response_model=AutoDetectResponse,
    summary="Run auto-detection",
    description="Run auto-detection to find and register running providers.",
)
async def run_auto_detect(
    request: AutoDetectRequest = AutoDetectRequest(),
    admin: dict = Depends(require_admin),
):
    """
    Run auto-detection to find and register running providers.

    Args:
        request: Detection options

    Returns:
        AutoDetectResponse with detection results
    """
    try:
        registry = get_registry()

        # Ensure registry is initialized
        await registry.initialize()

        # Run detection
        results = await registry.auto_detect(
            timeout=request.timeout,
            provider_names=request.providers,
        )

        detected_count = sum(1 for v in results.values() if v)

        return AutoDetectResponse(
            success=True,
            detected=results,
            message=f"Auto-detection complete. Found {detected_count} active provider(s).",
        )

    except Exception as e:
        logger.error(f"Failed to run auto-detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
