"""
Abstract Base Provider for Local Inference

Defines the interface that all local inference providers must implement.
Supports Ollama, llama.cpp, vLLM, and other local inference engines.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class ProviderNotAvailableError(ProviderError):
    """Raised when provider is not running or unreachable"""
    pass


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not found"""
    pass


class ModelLoadError(ProviderError):
    """Raised when model fails to load"""
    pass


class ModelUnloadError(ProviderError):
    """Raised when model fails to unload"""
    pass


# =============================================================================
# Enums
# =============================================================================

class ModelStatus(str, Enum):
    """Model loading status"""
    LOADED = "loaded"
    LOADING = "loading"
    UNLOADED = "unloaded"
    ERROR = "error"
    UNKNOWN = "unknown"


class ProviderStatus(str, Enum):
    """Provider health status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


# =============================================================================
# Pydantic Models
# =============================================================================

class ModelInfo(BaseModel):
    """Information about a model"""
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Display name for the model")
    size_bytes: Optional[int] = Field(None, description="Model size in bytes")
    quantization: Optional[str] = Field(None, description="Quantization type (e.g., Q4_K_M, Q8_0)")
    status: ModelStatus = Field(ModelStatus.UNLOADED, description="Current model status")
    provider: str = Field(..., description="Provider name (e.g., ollama, llama-cpp)")
    gpu_layers: Optional[int] = Field(None, description="Number of GPU layers loaded")
    context_size: Optional[int] = Field(None, description="Maximum context size in tokens")

    # Additional metadata
    family: Optional[str] = Field(None, description="Model family (e.g., llama, mistral)")
    parameter_count: Optional[str] = Field(None, description="Parameter count (e.g., 7B, 13B)")
    format: Optional[str] = Field(None, description="Model format (e.g., GGUF, safetensors)")
    modified_at: Optional[str] = Field(None, description="Last modification timestamp")
    digest: Optional[str] = Field(None, description="Model digest/hash")

    # Runtime info (populated when model is loaded)
    memory_used_mb: Optional[int] = Field(None, description="Memory used by model in MB")
    gpu_memory_used_mb: Optional[int] = Field(None, description="GPU memory used in MB")

    class Config:
        use_enum_values = True


class GPUInfo(BaseModel):
    """GPU hardware information"""
    index: int = Field(..., description="GPU device index")
    name: str = Field(..., description="GPU model name")
    memory_used_mb: int = Field(..., description="Memory used in MB")
    memory_total_mb: int = Field(..., description="Total memory in MB")
    utilization_percent: float = Field(..., description="GPU utilization percentage")
    temperature_c: Optional[int] = Field(None, description="Temperature in Celsius")
    power_draw_w: Optional[float] = Field(None, description="Power draw in Watts")
    power_limit_w: Optional[float] = Field(None, description="Power limit in Watts")

    # Additional metrics
    memory_free_mb: Optional[int] = Field(None, description="Free memory in MB")
    fan_speed_percent: Optional[int] = Field(None, description="Fan speed percentage")
    compute_capability: Optional[str] = Field(None, description="CUDA compute capability")
    driver_version: Optional[str] = Field(None, description="GPU driver version")
    cuda_version: Optional[str] = Field(None, description="CUDA version")

    @property
    def memory_used_percent(self) -> float:
        """Calculate memory usage percentage"""
        if self.memory_total_mb > 0:
            return (self.memory_used_mb / self.memory_total_mb) * 100
        return 0.0


class ProviderSettings(BaseModel):
    """Configuration settings for a provider"""
    url: str = Field(..., description="Provider API URL")
    enabled: bool = Field(True, description="Whether provider is enabled")
    idle_timeout_seconds: Optional[int] = Field(
        None,
        description="Seconds of inactivity before unloading models"
    )
    max_loaded_models: Optional[int] = Field(
        None,
        description="Maximum number of models to keep loaded"
    )

    # Additional settings
    api_key: Optional[str] = Field(None, description="API key if required")
    timeout_seconds: int = Field(30, description="HTTP request timeout")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    gpu_layers: Optional[int] = Field(
        None,
        description="Default GPU layers for loading models"
    )
    context_size: Optional[int] = Field(
        None,
        description="Default context size for models"
    )

    # Extra provider-specific settings
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific settings"
    )


class HealthCheckResult(BaseModel):
    """Result of a health check"""
    status: ProviderStatus = Field(..., description="Overall health status")
    provider: str = Field(..., description="Provider name")
    version: Optional[str] = Field(None, description="Provider version")
    message: Optional[str] = Field(None, description="Status message")
    latency_ms: Optional[float] = Field(None, description="Health check latency")

    # Capabilities
    supports_loading: bool = Field(True, description="Supports model loading/unloading")
    supports_gpu: bool = Field(True, description="Supports GPU acceleration")
    supports_streaming: bool = Field(True, description="Supports streaming responses")
    supports_embeddings: bool = Field(False, description="Supports embedding generation")

    # Resource info
    loaded_models: int = Field(0, description="Number of currently loaded models")
    available_models: int = Field(0, description="Number of available models")
    gpu_count: int = Field(0, description="Number of available GPUs")

    class Config:
        use_enum_values = True


# =============================================================================
# Abstract Base Class
# =============================================================================

class LocalInferenceProvider(ABC):
    """
    Abstract base class for local inference providers.

    All provider implementations must inherit from this class and implement
    the abstract methods. This ensures a consistent interface across
    different inference backends (Ollama, llama.cpp, vLLM, etc.).

    Example Implementation:

        class OllamaProvider(LocalInferenceProvider):
            provider_name = "ollama"
            display_name = "Ollama"
            supports_idle_unload = True
            supports_multi_gpu = True

            async def health_check(self) -> HealthCheckResult:
                # Implementation...
                pass
    """

    # Class-level attributes (override in subclasses)
    provider_name: str = "base"
    display_name: str = "Base Provider"
    description: str = "Abstract base provider"

    # Capability flags
    supports_idle_unload: bool = False
    supports_multi_gpu: bool = False
    supports_model_hot_swap: bool = False
    supports_quantization: bool = False
    supports_embeddings: bool = False
    supports_vision: bool = False

    def __init__(self, settings: ProviderSettings):
        """
        Initialize the provider with settings.

        Args:
            settings: Provider configuration settings
        """
        self.settings = settings
        self._http_client = None
        self._initialized = False

        logger.info(
            f"Initializing {self.display_name} provider at {settings.url}"
        )

    async def initialize(self) -> None:
        """
        Perform async initialization.

        Called after __init__ to set up async resources like HTTP clients.
        Override this method for custom initialization logic.
        """
        import httpx

        self._http_client = httpx.AsyncClient(
            timeout=self.settings.timeout_seconds,
            follow_redirects=True,
        )
        self._initialized = True
        logger.debug(f"{self.display_name} provider initialized")

    async def cleanup(self) -> None:
        """
        Clean up resources when shutting down.

        Called when the provider is being removed or the application is
        shutting down. Override for custom cleanup logic.
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._initialized = False
        logger.debug(f"{self.display_name} provider cleaned up")

    @property
    def is_initialized(self) -> bool:
        """Check if provider has been initialized"""
        return self._initialized

    # =========================================================================
    # Abstract Methods (MUST be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Check if provider is running and healthy.

        Returns:
            HealthCheckResult with status and provider information

        Raises:
            ProviderNotAvailableError: If provider is unreachable
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """
        List all available models (loaded and unloaded).

        Returns:
            List of ModelInfo objects for all known models

        Note:
            This should include both currently loaded models and
            models that are available to load (e.g., on disk).
        """
        pass

    @abstractmethod
    async def get_model_status(self, model_id: str) -> ModelInfo:
        """
        Get status of a specific model.

        Args:
            model_id: Model identifier

        Returns:
            ModelInfo with current status

        Raises:
            ModelNotFoundError: If model does not exist
        """
        pass

    @abstractmethod
    async def load_model(
        self,
        model_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a model into memory.

        Args:
            model_id: Model identifier to load
            options: Optional loading options (gpu_layers, context_size, etc.)

        Returns:
            Dictionary with loading result and timing info

        Raises:
            ModelNotFoundError: If model does not exist
            ModelLoadError: If model fails to load
        """
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """
        Unload a model from memory.

        Args:
            model_id: Model identifier to unload

        Returns:
            Dictionary with unload result

        Raises:
            ModelNotFoundError: If model is not loaded
            ModelUnloadError: If model fails to unload
        """
        pass

    @abstractmethod
    async def get_gpu_status(self) -> List[GPUInfo]:
        """
        Get GPU utilization information.

        Returns:
            List of GPUInfo for each available GPU

        Note:
            Returns empty list if no GPUs available or if provider
            does not support GPU monitoring.
        """
        pass

    @abstractmethod
    async def get_settings(self) -> ProviderSettings:
        """
        Get current provider settings.

        Returns:
            Current ProviderSettings (may include runtime values)
        """
        pass

    @abstractmethod
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

        Note:
            Some settings may require provider restart to take effect.
        """
        pass

    # =========================================================================
    # Optional Methods (override if supported)
    # =========================================================================

    async def get_metrics(self) -> Optional[str]:
        """
        Get Prometheus metrics if supported.

        Returns:
            Prometheus metrics in text format, or None if not supported
        """
        return None

    async def get_loaded_models(self) -> List[ModelInfo]:
        """
        Get list of currently loaded models.

        Default implementation filters list_models() for loaded status.
        Override for more efficient implementation.
        """
        all_models = await self.list_models()
        return [m for m in all_models if m.status == ModelStatus.LOADED]

    async def pull_model(
        self,
        model_name: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Pull/download a model from a registry.

        Args:
            model_name: Model name to pull
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with pull result

        Note:
            Not all providers support pulling models. Override if supported.
        """
        raise NotImplementedError(
            f"{self.display_name} does not support model pulling"
        )

    async def delete_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete a model from the system.

        Args:
            model_id: Model identifier to delete

        Returns:
            Dictionary with deletion result

        Note:
            Not all providers support model deletion. Override if supported.
        """
        raise NotImplementedError(
            f"{self.display_name} does not support model deletion"
        )

    async def generate(
        self,
        model_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text completion (for testing purposes).

        Args:
            model_id: Model to use
            prompt: Text prompt
            options: Generation options (temperature, max_tokens, etc.)
            stream: Whether to stream response

        Returns:
            Generation result

        Note:
            Override if provider supports generation testing.
        """
        raise NotImplementedError(
            f"{self.display_name} does not support direct generation"
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_http_client(self):
        """Get HTTP client, initializing if needed"""
        if not self._http_client:
            import httpx
            self._http_client = httpx.AsyncClient(
                timeout=self.settings.timeout_seconds,
            )
        return self._http_client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to provider.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (appended to base URL)
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON as dictionary

        Raises:
            ProviderNotAvailableError: If request fails
        """
        import httpx

        client = self._get_http_client()
        url = f"{self.settings.url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Add API key if configured
        if self.settings.api_key:
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
            kwargs["headers"] = headers

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise ProviderNotAvailableError(
                f"Cannot connect to {self.display_name} at {url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise ProviderNotAvailableError(
                f"Timeout connecting to {self.display_name}: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"HTTP error from {self.display_name}: {e.response.status_code}"
            )
        except Exception as e:
            raise ProviderError(
                f"Unexpected error from {self.display_name}: {e}"
            )

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name={self.provider_name} "
            f"url={self.settings.url} "
            f"enabled={self.settings.enabled}>"
        )
