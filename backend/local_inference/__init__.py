"""
Local Inference Provider Abstraction Layer

Provides a unified interface for managing local LLM inference providers
such as Ollama, llama.cpp, vLLM, and others.

Supports:
- Multiple provider backends
- Automatic provider detection
- Model loading/unloading management
- GPU resource monitoring
- Configuration persistence

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

from .base_provider import (
    LocalInferenceProvider,
    ModelInfo,
    GPUInfo,
    ProviderSettings,
    ProviderError,
    ProviderNotAvailableError,
    ModelNotFoundError,
    ModelLoadError,
)
from .registry import (
    ProviderRegistry,
    get_registry,
)
from .config import (
    LocalInferenceConfig,
    get_config,
    save_config,
    load_config_from_env,
)

__all__ = [
    # Base classes
    "LocalInferenceProvider",
    "ModelInfo",
    "GPUInfo",
    "ProviderSettings",
    # Exceptions
    "ProviderError",
    "ProviderNotAvailableError",
    "ModelNotFoundError",
    "ModelLoadError",
    # Registry
    "ProviderRegistry",
    "get_registry",
    # Config
    "LocalInferenceConfig",
    "get_config",
    "save_config",
    "load_config_from_env",
]

__version__ = "1.0.0"
