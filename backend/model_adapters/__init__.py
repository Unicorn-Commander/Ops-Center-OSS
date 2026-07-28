"""
Model Server Adapters Module
Provides unified interface for managing different types of model servers
"""

from .base import ServerAdapter, ModelInfo, ServerMetrics
from .vllm_adapter import VLLMAdapter
from .ollama_adapter import OllamaAdapter
from .embedding_adapter import EmbeddingAdapter
from .reranking_adapter import RerankingAdapter

# Factory function to create appropriate adapter
def create_adapter(server_type: str, base_url: str, api_key: str = None) -> ServerAdapter:
    """
    Create appropriate adapter based on server type

    Args:
        server_type: Type of server ('vllm', 'ollama', 'embedding', 'reranking')
        base_url: Base URL of the server
        api_key: Optional API key for authentication

    Returns:
        ServerAdapter instance

    Raises:
        ValueError: If server_type is not recognized
    """
    adapters = {
        'vllm': VLLMAdapter,
        'ollama': OllamaAdapter,
        'embedding': EmbeddingAdapter,
        'reranking': RerankingAdapter
    }

    adapter_class = adapters.get(server_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown server type: {server_type}")

    return adapter_class(base_url, api_key)

__all__ = [
    'ServerAdapter',
    'ModelInfo',
    'ServerMetrics',
    'VLLMAdapter',
    'OllamaAdapter',
    'EmbeddingAdapter',
    'RerankingAdapter',
    'create_adapter'
]