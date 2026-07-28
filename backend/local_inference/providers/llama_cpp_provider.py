"""
llama.cpp Router Provider Implementation

Implements the LocalInferenceProvider interface for llama.cpp server.
Supports the llama.cpp HTTP API endpoints for model management.

Features:
- Model loading/unloading with GPU layer control
- Multi-GPU tensor splitting
- Idle timeout with automatic unloading
- Prometheus metrics support
- Slot status monitoring

API Endpoints Used:
- GET /v1/models - List models
- POST /models/load - Load model
- POST /models/unload - Unload model
- GET /health - Health check
- GET /metrics - Prometheus metrics
- GET /props - Server properties
- GET /slots - Slot status

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import logging
import time
from typing import List, Dict, Optional, Any

from ..base_provider import (
    LocalInferenceProvider,
    ModelInfo,
    GPUInfo,
    ProviderSettings,
    HealthCheckResult,
    ProviderStatus,
    ModelStatus,
    ProviderError,
    ProviderNotAvailableError,
    ModelNotFoundError,
    ModelLoadError,
    ModelUnloadError,
)
from ..registry import register_provider
from .gpu_monitor import get_gpu_info

logger = logging.getLogger(__name__)


@register_provider("llama_cpp")
class LlamaCppProvider(LocalInferenceProvider):
    """
    llama.cpp server provider implementation.

    Provides integration with llama.cpp's HTTP server for local
    LLM inference. Supports advanced features like multi-GPU
    tensor splitting and idle timeout configuration.

    Attributes:
        provider_name: "llama_cpp"
        display_name: "llama.cpp Router"
        supports_idle_unload: True (via --sleep-idle-seconds)
        supports_multi_gpu: True (via tensor splitting)
        supports_metrics: True (Prometheus endpoint)
    """

    provider_name = "llama_cpp"
    display_name = "llama.cpp Router"
    description = "High-performance C++ LLM inference engine with GGUF model support"

    # Capability flags
    supports_idle_unload = True
    supports_multi_gpu = True
    supports_model_hot_swap = True
    supports_quantization = True
    supports_embeddings = True
    supports_vision = False
    supports_metrics = True

    def __init__(self, settings: ProviderSettings):
        """Initialize llama.cpp provider"""
        super().__init__(settings)
        self._server_props: Optional[Dict[str, Any]] = None
        self._current_model: Optional[str] = None

    # =========================================================================
    # Abstract Method Implementations
    # =========================================================================

    async def health_check(self) -> HealthCheckResult:
        """
        Check llama.cpp server health.

        Uses /health endpoint to verify server is running and ready.
        """
        start_time = time.time()

        try:
            response = await self._make_request("GET", "/health")
            latency_ms = (time.time() - start_time) * 1000

            # Get server properties for version info
            try:
                props = await self._get_server_props()
                version = props.get("version", None)
            except Exception:
                props = {}
                version = None

            # Determine status from health response
            status_str = response.get("status", "unknown")
            if status_str in ("ok", "ready"):
                status = ProviderStatus.ONLINE
            elif status_str == "loading":
                status = ProviderStatus.DEGRADED
            else:
                status = ProviderStatus.UNKNOWN

            # Get model count
            try:
                models = await self.list_models()
                available_models = len(models)
                loaded_models = sum(1 for m in models if m.status == ModelStatus.LOADED)
            except Exception:
                available_models = 0
                loaded_models = 0

            # Get GPU count
            try:
                gpus = await self.get_gpu_status()
                gpu_count = len(gpus)
            except Exception:
                gpu_count = 0

            return HealthCheckResult(
                status=status,
                provider=self.provider_name,
                version=version,
                message=f"Server {status_str}",
                latency_ms=round(latency_ms, 2),
                supports_loading=True,
                supports_gpu=True,
                supports_streaming=True,
                supports_embeddings=props.get("embedding", False),
                loaded_models=loaded_models,
                available_models=available_models,
                gpu_count=gpu_count,
            )

        except ProviderNotAvailableError:
            raise
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheckResult(
                status=ProviderStatus.OFFLINE,
                provider=self.provider_name,
                message=str(e),
            )

    async def list_models(self) -> List[ModelInfo]:
        """
        List available models.

        Uses /v1/models endpoint (OpenAI-compatible).
        """
        try:
            response = await self._make_request("GET", "/v1/models")
            models_data = response.get("data", [])

            models = []
            for model in models_data:
                model_id = model.get("id", "unknown")

                # Determine status based on whether model is currently loaded
                if self._current_model and model_id == self._current_model:
                    status = ModelStatus.LOADED
                else:
                    status = ModelStatus.UNLOADED

                model_info = ModelInfo(
                    id=model_id,
                    name=model.get("id", model_id).split("/")[-1],
                    provider=self.provider_name,
                    status=status,
                    format="GGUF",
                    context_size=model.get("context_length"),
                )
                models.append(model_info)

            return models

        except ProviderNotAvailableError:
            raise
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def get_model_status(self, model_id: str) -> ModelInfo:
        """
        Get status of a specific model.

        Args:
            model_id: Model identifier

        Returns:
            ModelInfo with current status
        """
        models = await self.list_models()

        for model in models:
            if model.id == model_id or model.name == model_id:
                return model

        raise ModelNotFoundError(f"Model {model_id} not found")

    async def load_model(
        self,
        model_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a model into memory.

        Uses POST /models/load endpoint.

        Args:
            model_id: Model identifier or path
            options: Loading options:
                - n_gpu_layers: Number of GPU layers
                - n_ctx: Context size
                - tensor_split: GPU tensor split ratios
                - main_gpu: Main GPU index

        Returns:
            Dictionary with loading result
        """
        start_time = time.time()
        options = options or {}

        # Build load request
        load_request: Dict[str, Any] = {
            "model": model_id,
        }

        # GPU layers
        n_gpu_layers = options.get(
            "n_gpu_layers",
            options.get("gpu_layers", self.settings.gpu_layers)
        )
        if n_gpu_layers is not None:
            load_request["n_gpu_layers"] = n_gpu_layers

        # Context size
        n_ctx = options.get(
            "n_ctx",
            options.get("context_size", self.settings.context_size)
        )
        if n_ctx is not None:
            load_request["n_ctx"] = n_ctx

        # Multi-GPU tensor splitting
        tensor_split = options.get("tensor_split")
        if tensor_split:
            load_request["tensor_split"] = tensor_split

        main_gpu = options.get("main_gpu")
        if main_gpu is not None:
            load_request["main_gpu"] = main_gpu

        # Additional options
        for key in ["use_mmap", "use_mlock", "rope_scaling_type", "rope_freq_base"]:
            if key in options:
                load_request[key] = options[key]

        logger.info(f"Loading model {model_id} with options: {load_request}")

        try:
            response = await self._make_request(
                "POST",
                "/models/load",
                json=load_request
            )

            load_time = time.time() - start_time
            self._current_model = model_id

            logger.info(f"Model {model_id} loaded in {load_time:.2f}s")

            return {
                "success": True,
                "model_id": model_id,
                "load_time_seconds": round(load_time, 2),
                "response": response,
            }

        except ProviderError as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise ModelLoadError(f"Failed to load {model_id}: {e}")

    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """
        Unload a model from memory.

        Uses POST /models/unload endpoint.

        Args:
            model_id: Model identifier to unload

        Returns:
            Dictionary with unload result
        """
        logger.info(f"Unloading model {model_id}")

        try:
            response = await self._make_request(
                "POST",
                "/models/unload",
                json={"model": model_id}
            )

            if self._current_model == model_id:
                self._current_model = None

            logger.info(f"Model {model_id} unloaded")

            return {
                "success": True,
                "model_id": model_id,
                "response": response,
            }

        except ProviderError as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            raise ModelUnloadError(f"Failed to unload {model_id}: {e}")

    async def get_gpu_status(self) -> List[GPUInfo]:
        """
        Get GPU utilization information.

        Uses the shared GPU monitor utility.
        """
        return await get_gpu_info()

    async def get_settings(self) -> ProviderSettings:
        """Get current provider settings"""
        return self.settings

    async def update_settings(
        self,
        settings: Dict[str, Any]
    ) -> ProviderSettings:
        """
        Update provider settings.

        Args:
            settings: Dictionary of settings to update

        Returns:
            Updated ProviderSettings
        """
        for key, value in settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

        logger.info(f"Updated llama.cpp provider settings: {settings}")
        return self.settings

    # =========================================================================
    # Optional Method Implementations
    # =========================================================================

    async def get_metrics(self) -> Optional[str]:
        """
        Get Prometheus metrics.

        Returns raw Prometheus text format metrics.
        """
        try:
            client = self._get_http_client()
            url = f"{self.settings.url.rstrip('/')}/metrics"

            response = await client.get(url)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.warning(f"Failed to get metrics: {e}")
            return None

    async def get_loaded_models(self) -> List[ModelInfo]:
        """Get currently loaded models"""
        models = await self.list_models()
        return [m for m in models if m.status == ModelStatus.LOADED]

    # =========================================================================
    # llama.cpp Specific Methods
    # =========================================================================

    async def _get_server_props(self) -> Dict[str, Any]:
        """
        Get server properties.

        Caches properties for efficiency.
        """
        if self._server_props is not None:
            return self._server_props

        try:
            self._server_props = await self._make_request("GET", "/props")
            return self._server_props
        except Exception as e:
            logger.warning(f"Failed to get server props: {e}")
            return {}

    async def get_slots(self) -> List[Dict[str, Any]]:
        """
        Get slot status.

        Returns information about server slots (concurrent request handling).
        """
        try:
            response = await self._make_request("GET", "/slots")
            return response if isinstance(response, list) else response.get("slots", [])
        except Exception as e:
            logger.warning(f"Failed to get slots: {e}")
            return []

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get comprehensive server information.

        Combines props, slots, and health information.
        """
        props = await self._get_server_props()

        try:
            slots = await self.get_slots()
        except Exception:
            slots = []

        try:
            health = await self.health_check()
            health_status = health.status.value
        except Exception:
            health_status = "unknown"

        return {
            "provider": self.provider_name,
            "display_name": self.display_name,
            "url": self.settings.url,
            "status": health_status,
            "props": props,
            "slots": slots,
            "slot_count": len(slots),
            "current_model": self._current_model,
            "capabilities": {
                "supports_idle_unload": self.supports_idle_unload,
                "supports_multi_gpu": self.supports_multi_gpu,
                "supports_metrics": self.supports_metrics,
                "supports_embeddings": self.supports_embeddings,
            },
        }

    async def set_idle_timeout(self, seconds: int) -> Dict[str, Any]:
        """
        Configure idle timeout for automatic model unloading.

        Note: This requires the server to be started with --sleep-idle-seconds.
        This method updates the provider settings only; the server must be
        restarted with the new configuration to apply.

        Args:
            seconds: Idle timeout in seconds (0 to disable)

        Returns:
            Configuration result
        """
        self.settings.idle_timeout_seconds = seconds if seconds > 0 else None

        return {
            "success": True,
            "message": f"Idle timeout set to {seconds}s (requires server restart)",
            "idle_timeout_seconds": seconds,
        }

    async def configure_tensor_split(
        self,
        gpu_ratios: List[float]
    ) -> Dict[str, Any]:
        """
        Configure tensor splitting for multi-GPU setups.

        Args:
            gpu_ratios: List of ratios for each GPU (e.g., [0.5, 0.5] for even split)

        Returns:
            Configuration stored (applied on next model load)
        """
        # Store in extra settings for next model load
        if "tensor_split" not in self.settings.extra:
            self.settings.extra["tensor_split"] = []

        self.settings.extra["tensor_split"] = gpu_ratios

        return {
            "success": True,
            "message": "Tensor split configured (will apply on next model load)",
            "tensor_split": gpu_ratios,
        }
