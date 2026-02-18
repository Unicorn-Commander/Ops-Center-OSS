"""
Local Inference Provider Implementations

This module contains implementations of the LocalInferenceProvider
interface for various local inference backends:

- llama_cpp: llama.cpp server with model hot-swap and multi-GPU
- ollama: Ollama with model pulling and keep_alive timeout
- vllm: vLLM high-throughput inference engine

All providers are automatically registered using the @register_provider
decorator and can be discovered via the registry.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

# Import providers to trigger registration
from .llama_cpp_provider import LlamaCppProvider
from .ollama_provider import OllamaProvider
from .vllm_provider import VLLMProvider

# Import GPU monitor utilities
from .gpu_monitor import (
    get_gpu_info,
    get_gpu_count,
    get_total_gpu_memory_mb,
    get_available_gpu_memory_mb,
    get_gpu_summary,
    clear_gpu_cache,
    is_nvidia_available,
)

# Import registry functions for convenience
from ..registry import (
    register_provider,
    get_registered_providers,
    get_registry,
)

__all__ = [
    # Provider classes
    "LlamaCppProvider",
    "OllamaProvider",
    "VLLMProvider",

    # GPU monitoring
    "get_gpu_info",
    "get_gpu_count",
    "get_total_gpu_memory_mb",
    "get_available_gpu_memory_mb",
    "get_gpu_summary",
    "clear_gpu_cache",
    "is_nvidia_available",

    # Registry
    "register_provider",
    "get_registered_providers",
    "get_registry",
]

# Provider metadata for discovery
PROVIDER_INFO = {
    "llama_cpp": {
        "class": LlamaCppProvider,
        "display_name": "llama.cpp Router",
        "description": "High-performance C++ LLM inference with GGUF support",
        "default_url": "http://localhost:8080",
        "capabilities": {
            "supports_idle_unload": True,
            "supports_multi_gpu": True,
            "supports_metrics": True,
            "supports_model_hot_swap": True,
        },
    },
    "ollama": {
        "class": OllamaProvider,
        "display_name": "Ollama",
        "description": "Easy-to-use LLM runner with built-in model library",
        "default_url": "http://localhost:11434",
        "capabilities": {
            "supports_idle_unload": True,
            "supports_model_pull": True,
            "supports_embeddings": True,
            "supports_vision": True,
        },
    },
    "vllm": {
        "class": VLLMProvider,
        "display_name": "vLLM",
        "description": "High-throughput serving with tensor parallelism",
        "default_url": "http://localhost:8000",
        "capabilities": {
            "supports_multi_gpu": True,
            "supports_metrics": True,
            "supports_model_hot_swap": False,
        },
    },
}


def get_provider_info(provider_name: str) -> dict:
    """
    Get metadata for a specific provider.

    Args:
        provider_name: Provider identifier

    Returns:
        Dictionary with provider metadata
    """
    return PROVIDER_INFO.get(provider_name, {})


def get_all_provider_info() -> dict:
    """
    Get metadata for all available providers.

    Returns:
        Dictionary mapping provider names to their metadata
    """
    return PROVIDER_INFO.copy()


def list_providers() -> list:
    """
    Get list of available provider names.

    Returns:
        List of provider name strings
    """
    return list(PROVIDER_INFO.keys())
