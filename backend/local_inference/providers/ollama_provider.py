"""
Ollama Provider Implementation

Implements the LocalInferenceProvider interface for Ollama.
Supports Ollama's REST API for model management and inference.

Features:
- Model pulling/downloading from Ollama library
- Model loading via generate endpoint
- Idle timeout via OLLAMA_KEEP_ALIVE
- Running model monitoring

API Endpoints Used:
- GET /api/tags - List local models
- POST /api/pull - Pull/download model
- POST /api/generate - Generate (loads model if not loaded)
- DELETE /api/delete - Delete model
- GET /api/ps - List running models
- GET /api/show - Show model info

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import logging
import time
import asyncio
from typing import List, Dict, Optional, Any, AsyncIterator

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


@register_provider("ollama")
class OllamaProvider(LocalInferenceProvider):
    """
    Ollama provider implementation.

    Provides integration with Ollama's API for local LLM inference.
    Supports pulling models from Ollama's library and managing
    model lifecycle with keep_alive timeout.

    Attributes:
        provider_name: "ollama"
        display_name: "Ollama"
        supports_idle_unload: True (via keep_alive)
        supports_model_pull: True (can download models)
    """

    provider_name = "ollama"
    display_name = "Ollama"
    description = "Easy-to-use local LLM runner with built-in model library"

    # Capability flags
    supports_idle_unload = True
    supports_multi_gpu = False
    supports_model_hot_swap = True
    supports_quantization = True
    supports_embeddings = True
    supports_vision = True
    supports_model_pull = True
    supports_metrics = False

    def __init__(self, settings: ProviderSettings):
        """Initialize Ollama provider"""
        super().__init__(settings)
        self._keep_alive: Optional[str] = None

    # =========================================================================
    # Abstract Method Implementations
    # =========================================================================

    async def health_check(self) -> HealthCheckResult:
        """
        Check Ollama server health.

        Uses / endpoint or /api/version to verify server is running.
        """
        start_time = time.time()

        try:
            # Try the version endpoint
            client = self._get_http_client()
            url = f"{self.settings.url.rstrip('/')}/api/version"

            response = await client.get(url)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                version = data.get("version", None)

                # Get model counts
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
                    status=ProviderStatus.ONLINE,
                    provider=self.provider_name,
                    version=version,
                    message="Ollama is running",
                    latency_ms=round(latency_ms, 2),
                    supports_loading=True,
                    supports_gpu=True,
                    supports_streaming=True,
                    supports_embeddings=True,
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
            raise ProviderNotAvailableError(f"Cannot connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheckResult(
                status=ProviderStatus.OFFLINE,
                provider=self.provider_name,
                message=str(e),
            )

    async def list_models(self) -> List[ModelInfo]:
        """
        List all local models.

        Uses /api/tags to get available models and /api/ps for running models.
        """
        try:
            # Get all local models
            response = await self._make_request("GET", "/api/tags")
            models_data = response.get("models", [])

            # Get running models
            try:
                running = await self._get_running_models()
                running_names = {r.get("name") for r in running}
            except Exception:
                running_names = set()

            models = []
            for model in models_data:
                name = model.get("name", "unknown")

                # Parse model name for family and parameter count
                family = None
                parameter_count = None
                if ":" in name:
                    base_name = name.split(":")[0]
                    tag = name.split(":")[1] if len(name.split(":")) > 1 else None
                    family = base_name.split("-")[0] if "-" in base_name else base_name
                else:
                    family = name.split("-")[0] if "-" in name else name

                # Check for parameter count in name (e.g., "7b", "13b")
                for part in name.lower().replace("-", ":").replace("_", ":").split(":"):
                    if part.endswith("b") and part[:-1].isdigit():
                        parameter_count = part.upper()
                        break

                # Determine status
                if name in running_names:
                    status = ModelStatus.LOADED
                else:
                    status = ModelStatus.UNLOADED

                # Parse quantization from model details
                details = model.get("details", {})
                quantization = details.get("quantization_level")

                model_info = ModelInfo(
                    id=name,
                    name=name,
                    provider=self.provider_name,
                    status=status,
                    size_bytes=model.get("size"),
                    quantization=quantization,
                    family=family,
                    parameter_count=parameter_count,
                    format=details.get("format", "GGUF"),
                    modified_at=model.get("modified_at"),
                    digest=model.get("digest"),
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

        # Model might exist on Ollama library but not locally
        # Return as unloaded/not found
        raise ModelNotFoundError(f"Model {model_id} not found locally")

    async def load_model(
        self,
        model_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a model into memory.

        Ollama loads models automatically when generating. We use a
        dummy generate request with no prompt to force loading.

        Args:
            model_id: Model name (e.g., "llama2:7b")
            options: Loading options:
                - keep_alive: How long to keep model loaded (e.g., "5m", "1h")

        Returns:
            Dictionary with loading result
        """
        start_time = time.time()
        options = options or {}

        # Prepare generate request to trigger loading
        generate_request: Dict[str, Any] = {
            "model": model_id,
            "prompt": "",  # Empty prompt just loads the model
            "stream": False,
        }

        # Set keep_alive for idle timeout
        keep_alive = options.get("keep_alive", self._keep_alive)
        if keep_alive:
            generate_request["keep_alive"] = keep_alive
        elif self.settings.idle_timeout_seconds:
            generate_request["keep_alive"] = f"{self.settings.idle_timeout_seconds}s"

        # Options that can be passed to Ollama
        if "num_gpu" in options:
            generate_request.setdefault("options", {})["num_gpu"] = options["num_gpu"]
        if "num_ctx" in options:
            generate_request.setdefault("options", {})["num_ctx"] = options["num_ctx"]

        logger.info(f"Loading Ollama model {model_id}")

        try:
            response = await self._make_request(
                "POST",
                "/api/generate",
                json=generate_request
            )

            load_time = time.time() - start_time

            logger.info(f"Model {model_id} loaded in {load_time:.2f}s")

            return {
                "success": True,
                "model_id": model_id,
                "load_time_seconds": round(load_time, 2),
                "response": response,
            }

        except ProviderError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise ModelNotFoundError(f"Model {model_id} not found. Try pulling it first.")
            raise ModelLoadError(f"Failed to load {model_id}: {e}")

    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """
        Unload a model from memory.

        Ollama unloads models by setting keep_alive to 0 in a generate request.

        Args:
            model_id: Model name to unload

        Returns:
            Dictionary with unload result
        """
        logger.info(f"Unloading Ollama model {model_id}")

        try:
            # Send generate request with keep_alive: "0" to unload
            response = await self._make_request(
                "POST",
                "/api/generate",
                json={
                    "model": model_id,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": "0",
                }
            )

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

        logger.info(f"Updated Ollama provider settings: {settings}")
        return self.settings

    # =========================================================================
    # Optional Method Implementations
    # =========================================================================

    async def pull_model(
        self,
        model_name: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Pull/download a model from Ollama library.

        Args:
            model_name: Model to pull (e.g., "llama2:7b", "mistral:latest")
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with pull result
        """
        logger.info(f"Pulling Ollama model: {model_name}")
        start_time = time.time()

        try:
            # Ollama pull streams progress updates
            client = self._get_http_client()
            url = f"{self.settings.url.rstrip('/')}/api/pull"

            # Use longer timeout for pulls
            timeout = httpx.Timeout(
                connect=10.0,
                read=300.0,  # 5 minutes for large models
                write=10.0,
                pool=10.0,
            )

            async with client.stream(
                "POST",
                url,
                json={"name": model_name},
                timeout=timeout
            ) as response:
                response.raise_for_status()

                last_status = None
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        import json
                        data = json.loads(line)

                        status = data.get("status", "")

                        # Call progress callback if provided
                        if progress_callback and status != last_status:
                            progress_callback(data)
                            last_status = status

                        # Log significant progress
                        if "completed" in data or "total" in data:
                            completed = data.get("completed", 0)
                            total = data.get("total", 1)
                            if total > 0:
                                pct = (completed / total) * 100
                                logger.debug(f"Pull progress: {pct:.1f}%")

                    except json.JSONDecodeError:
                        continue

            elapsed = time.time() - start_time
            logger.info(f"Model {model_name} pulled in {elapsed:.1f}s")

            return {
                "success": True,
                "model": model_name,
                "elapsed_seconds": round(elapsed, 2),
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"Pull failed: {e.response.status_code}"
            logger.error(error_msg)
            raise ProviderError(error_msg)
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            raise ProviderError(f"Failed to pull {model_name}: {e}")

    async def delete_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete a model from local storage.

        Args:
            model_id: Model name to delete

        Returns:
            Dictionary with deletion result
        """
        logger.info(f"Deleting Ollama model: {model_id}")

        try:
            # First unload if running
            try:
                await self.unload_model(model_id)
            except Exception:
                pass  # Model might not be loaded

            # Delete the model
            response = await self._make_request(
                "DELETE",
                "/api/delete",
                json={"name": model_id}
            )

            logger.info(f"Model {model_id} deleted")

            return {
                "success": True,
                "model_id": model_id,
                "response": response,
            }

        except ProviderError as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            raise

    async def generate(
        self,
        model_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text completion.

        Args:
            model_id: Model to use
            prompt: Text prompt
            options: Generation options (temperature, max_tokens, etc.)
            stream: Whether to stream response

        Returns:
            Generation result
        """
        options = options or {}

        generate_request: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "stream": stream,
        }

        # Map common option names
        if "max_tokens" in options:
            generate_request.setdefault("options", {})["num_predict"] = options["max_tokens"]
        if "temperature" in options:
            generate_request.setdefault("options", {})["temperature"] = options["temperature"]
        if "top_p" in options:
            generate_request.setdefault("options", {})["top_p"] = options["top_p"]
        if "top_k" in options:
            generate_request.setdefault("options", {})["top_k"] = options["top_k"]

        try:
            response = await self._make_request(
                "POST",
                "/api/generate",
                json=generate_request
            )

            return {
                "success": True,
                "model": model_id,
                "response": response.get("response", ""),
                "eval_count": response.get("eval_count"),
                "eval_duration": response.get("eval_duration"),
            }

        except ProviderError as e:
            logger.error(f"Generate failed: {e}")
            raise

    # =========================================================================
    # Ollama Specific Methods
    # =========================================================================

    async def _get_running_models(self) -> List[Dict[str, Any]]:
        """
        Get list of currently running models.

        Uses /api/ps endpoint.
        """
        try:
            response = await self._make_request("GET", "/api/ps")
            return response.get("models", [])
        except Exception as e:
            logger.warning(f"Failed to get running models: {e}")
            return []

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed model information.

        Uses /api/show endpoint.

        Args:
            model_id: Model name

        Returns:
            Detailed model information
        """
        try:
            response = await self._make_request(
                "POST",
                "/api/show",
                json={"name": model_id}
            )
            return response
        except ProviderError as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            raise ModelNotFoundError(f"Model {model_id} not found")

    async def set_keep_alive(self, duration: str) -> Dict[str, Any]:
        """
        Set default keep_alive duration for model loading.

        Args:
            duration: Duration string (e.g., "5m", "1h", "0" for immediate unload)

        Returns:
            Configuration result
        """
        self._keep_alive = duration

        # Also update settings
        if duration == "0":
            self.settings.idle_timeout_seconds = 0
        else:
            # Try to parse duration to seconds
            try:
                if duration.endswith("s"):
                    seconds = int(duration[:-1])
                elif duration.endswith("m"):
                    seconds = int(duration[:-1]) * 60
                elif duration.endswith("h"):
                    seconds = int(duration[:-1]) * 3600
                else:
                    seconds = int(duration)
                self.settings.idle_timeout_seconds = seconds
            except ValueError:
                pass

        return {
            "success": True,
            "keep_alive": duration,
            "message": "Keep-alive duration updated",
        }

    async def copy_model(
        self,
        source: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Copy a model to a new name.

        Args:
            source: Source model name
            destination: Destination model name

        Returns:
            Copy result
        """
        logger.info(f"Copying Ollama model {source} to {destination}")

        try:
            response = await self._make_request(
                "POST",
                "/api/copy",
                json={"source": source, "destination": destination}
            )

            return {
                "success": True,
                "source": source,
                "destination": destination,
                "response": response,
            }

        except ProviderError as e:
            logger.error(f"Failed to copy model: {e}")
            raise

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get comprehensive server information.
        """
        try:
            health = await self.health_check()
            health_status = health.status.value
            version = health.version
        except Exception:
            health_status = "unknown"
            version = None

        try:
            running = await self._get_running_models()
        except Exception:
            running = []

        try:
            models = await self.list_models()
            total_models = len(models)
        except Exception:
            total_models = 0

        return {
            "provider": self.provider_name,
            "display_name": self.display_name,
            "url": self.settings.url,
            "status": health_status,
            "version": version,
            "running_models": len(running),
            "total_models": total_models,
            "keep_alive": self._keep_alive,
            "capabilities": {
                "supports_idle_unload": self.supports_idle_unload,
                "supports_model_pull": self.supports_model_pull,
                "supports_embeddings": self.supports_embeddings,
                "supports_vision": self.supports_vision,
            },
        }
