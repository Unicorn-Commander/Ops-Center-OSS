"""
vLLM Provider Implementation

Implements the LocalInferenceProvider interface for vLLM.
vLLM is a high-performance LLM serving engine that supports
tensor parallelism and continuous batching.

Features:
- OpenAI-compatible API
- Prometheus metrics support
- Multi-GPU tensor parallelism
- High-throughput batching

Note: vLLM typically runs a single model. Loading/unloading
requires server restart, so these operations return information
about the currently loaded model.

API Endpoints Used:
- GET /v1/models - List models
- GET /health - Health check
- GET /metrics - Prometheus metrics

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import logging
import time
from typing import List, Dict, Optional, Any

import httpx

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


@register_provider("vllm")
class VLLMProvider(LocalInferenceProvider):
    """
    vLLM provider implementation.

    Provides integration with vLLM's OpenAI-compatible API.
    Note that vLLM runs a single model specified at startup,
    so dynamic model loading/unloading is limited.

    Attributes:
        provider_name: "vllm"
        display_name: "vLLM"
        supports_metrics: True (Prometheus endpoint)
        supports_multi_gpu: True (tensor parallelism)
    """

    provider_name = "vllm"
    display_name = "vLLM"
    description = "High-throughput LLM serving engine with tensor parallelism"

    # Capability flags
    supports_idle_unload = False  # vLLM doesn't support dynamic unloading
    supports_multi_gpu = True
    supports_model_hot_swap = False  # Requires restart
    supports_quantization = True
    supports_embeddings = False  # Depends on model
    supports_vision = False  # Depends on model
    supports_metrics = True

    def __init__(self, settings: ProviderSettings):
        """Initialize vLLM provider"""
        super().__init__(settings)
        self._model_info: Optional[Dict[str, Any]] = None

    # =========================================================================
    # Abstract Method Implementations
    # =========================================================================

    async def health_check(self) -> HealthCheckResult:
        """
        Check vLLM server health.

        Uses /health endpoint to verify server is running.
        """
        start_time = time.time()

        try:
            client = self._get_http_client()
            url = f"{self.settings.url.rstrip('/')}/health"

            response = await client.get(url)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Get model info
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

                # Try to get version from model endpoint
                version = None
                try:
                    model_resp = await self._make_request("GET", "/v1/models")
                    # vLLM doesn't expose version in standard response
                except Exception:
                    pass

                return HealthCheckResult(
                    status=ProviderStatus.ONLINE,
                    provider=self.provider_name,
                    version=version,
                    message="vLLM is running",
                    latency_ms=round(latency_ms, 2),
                    supports_loading=False,  # vLLM doesn't support dynamic loading
                    supports_gpu=True,
                    supports_streaming=True,
                    supports_embeddings=False,
                    loaded_models=loaded_models,
                    available_models=available_models,
                    gpu_count=gpu_count,
                )
            else:
                return HealthCheckResult(
                    status=ProviderStatus.DEGRADED,
                    provider=self.provider_name,
                    message=f"Unexpected status: {response.status_code}",
                    latency_ms=round(latency_ms, 2),
                )

        except httpx.ConnectError as e:
            raise ProviderNotAvailableError(f"Cannot connect to vLLM: {e}")
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

        vLLM typically runs a single model, which is always loaded.
        Uses /v1/models endpoint (OpenAI-compatible).
        """
        try:
            response = await self._make_request("GET", "/v1/models")
            models_data = response.get("data", [])

            models = []
            for model in models_data:
                model_id = model.get("id", "unknown")

                # Parse model name for metadata
                family = None
                parameter_count = None

                if "/" in model_id:
                    # HuggingFace model format
                    parts = model_id.split("/")
                    base_name = parts[-1] if parts else model_id
                    family = base_name.split("-")[0] if "-" in base_name else base_name
                else:
                    family = model_id.split("-")[0] if "-" in model_id else model_id

                # Check for parameter count
                for part in model_id.lower().replace("-", "_").replace("/", "_").split("_"):
                    if part.endswith("b") and part[:-1].replace(".", "").isdigit():
                        parameter_count = part.upper()
                        break

                # vLLM models are always loaded
                model_info = ModelInfo(
                    id=model_id,
                    name=model_id.split("/")[-1] if "/" in model_id else model_id,
                    provider=self.provider_name,
                    status=ModelStatus.LOADED,
                    family=family,
                    parameter_count=parameter_count,
                    context_size=model.get("context_length") or model.get("max_model_len"),
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
        Load a model.

        Note: vLLM doesn't support dynamic model loading.
        The model is specified at server startup.

        This method returns information about loading limitations.
        """
        logger.warning(
            f"vLLM does not support dynamic model loading. "
            f"Model {model_id} cannot be loaded at runtime."
        )

        # Check if this is the already-loaded model
        try:
            models = await self.list_models()
            for model in models:
                if model.id == model_id or model.name == model_id:
                    return {
                        "success": True,
                        "model_id": model_id,
                        "message": "Model is already loaded",
                        "already_loaded": True,
                    }
        except Exception:
            pass

        raise ModelLoadError(
            f"vLLM does not support dynamic model loading. "
            f"To load {model_id}, restart vLLM with the new model."
        )

    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """
        Unload a model.

        Note: vLLM doesn't support dynamic model unloading.
        The server must be stopped to unload the model.
        """
        logger.warning(
            f"vLLM does not support dynamic model unloading. "
            f"Model {model_id} cannot be unloaded at runtime."
        )

        raise ModelUnloadError(
            f"vLLM does not support dynamic model unloading. "
            f"Stop the vLLM server to unload {model_id}."
        )

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

        logger.info(f"Updated vLLM provider settings: {settings}")
        return self.settings

    # =========================================================================
    # Optional Method Implementations
    # =========================================================================

    async def get_metrics(self) -> Optional[str]:
        """
        Get Prometheus metrics.

        vLLM exposes metrics at /metrics endpoint.
        Returns raw Prometheus text format.
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
        """Get currently loaded models (all models in vLLM)"""
        return await self.list_models()

    async def generate(
        self,
        model_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text completion using OpenAI-compatible API.

        Args:
            model_id: Model to use
            prompt: Text prompt
            options: Generation options
            stream: Whether to stream response

        Returns:
            Generation result
        """
        options = options or {}

        request_body: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "stream": stream,
        }

        # Map options to OpenAI format
        if "max_tokens" in options:
            request_body["max_tokens"] = options["max_tokens"]
        if "temperature" in options:
            request_body["temperature"] = options["temperature"]
        if "top_p" in options:
            request_body["top_p"] = options["top_p"]
        if "stop" in options:
            request_body["stop"] = options["stop"]

        try:
            response = await self._make_request(
                "POST",
                "/v1/completions",
                json=request_body
            )

            # Extract text from response
            choices = response.get("choices", [])
            text = choices[0].get("text", "") if choices else ""

            return {
                "success": True,
                "model": model_id,
                "response": text,
                "usage": response.get("usage"),
                "id": response.get("id"),
            }

        except ProviderError as e:
            logger.error(f"Generate failed: {e}")
            raise

    # =========================================================================
    # vLLM Specific Methods
    # =========================================================================

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get comprehensive server information.
        """
        try:
            health = await self.health_check()
            health_status = health.status.value
        except Exception:
            health_status = "unknown"

        try:
            models = await self.list_models()
            loaded_models = [m.id for m in models]
        except Exception:
            loaded_models = []

        try:
            gpus = await self.get_gpu_status()
            gpu_info = [
                {
                    "index": gpu.index,
                    "name": gpu.name,
                    "memory_used_mb": gpu.memory_used_mb,
                    "memory_total_mb": gpu.memory_total_mb,
                    "utilization_percent": gpu.utilization_percent,
                }
                for gpu in gpus
            ]
        except Exception:
            gpu_info = []

        return {
            "provider": self.provider_name,
            "display_name": self.display_name,
            "url": self.settings.url,
            "status": health_status,
            "loaded_models": loaded_models,
            "model_count": len(loaded_models),
            "gpus": gpu_info,
            "gpu_count": len(gpu_info),
            "capabilities": {
                "supports_idle_unload": self.supports_idle_unload,
                "supports_multi_gpu": self.supports_multi_gpu,
                "supports_model_hot_swap": self.supports_model_hot_swap,
                "supports_metrics": self.supports_metrics,
            },
            "notes": [
                "vLLM runs a single model specified at startup",
                "Dynamic model loading/unloading requires server restart",
                "Supports tensor parallelism for multi-GPU inference",
            ],
        }

    async def get_metrics_parsed(self) -> Dict[str, Any]:
        """
        Get Prometheus metrics parsed into structured format.

        Returns:
            Dictionary with parsed metrics
        """
        raw_metrics = await self.get_metrics()

        if not raw_metrics:
            return {"error": "Metrics not available"}

        metrics = {}
        current_metric = None

        for line in raw_metrics.split("\n"):
            line = line.strip()

            if not line or line.startswith("#"):
                # Skip empty lines and comments, but extract metric names
                if line.startswith("# HELP"):
                    parts = line.split(" ", 3)
                    if len(parts) >= 3:
                        current_metric = parts[2]
                continue

            # Parse metric line: metric_name{labels} value
            try:
                if "{" in line:
                    name_part, rest = line.split("{", 1)
                    labels_part, value = rest.rsplit("}", 1)
                    name = name_part.strip()
                    value = float(value.strip())

                    # Parse labels
                    labels = {}
                    for label in labels_part.split(","):
                        if "=" in label:
                            k, v = label.split("=", 1)
                            labels[k.strip()] = v.strip().strip('"')

                    if name not in metrics:
                        metrics[name] = []
                    metrics[name].append({"labels": labels, "value": value})
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        value = float(parts[1])
                        metrics[name] = value

            except (ValueError, IndexError):
                continue

        return metrics

    async def get_model_config(self) -> Dict[str, Any]:
        """
        Get the configuration of the currently loaded model.

        Attempts to infer configuration from metrics and model info.
        """
        try:
            models = await self.list_models()
            if not models:
                return {"error": "No models loaded"}

            model = models[0]

            # Try to get more info from metrics
            metrics = await self.get_metrics_parsed()

            config = {
                "model_id": model.id,
                "model_name": model.name,
                "context_size": model.context_size,
                "status": model.status.value,
            }

            # Add GPU info if available
            try:
                gpus = await self.get_gpu_status()
                config["gpu_count"] = len(gpus)
                config["total_gpu_memory_mb"] = sum(g.memory_total_mb for g in gpus)
                config["used_gpu_memory_mb"] = sum(g.memory_used_mb for g in gpus)
            except Exception:
                pass

            # Add relevant metrics
            if isinstance(metrics, dict) and "error" not in metrics:
                for key in ["vllm_num_requests_running", "vllm_num_requests_waiting",
                           "vllm_gpu_cache_usage_perc", "vllm_cpu_cache_usage_perc"]:
                    if key in metrics:
                        config[key] = metrics[key]

            return config

        except Exception as e:
            logger.error(f"Failed to get model config: {e}")
            return {"error": str(e)}
