"""
LLM Provider Integration Layer

Integrates LLMConfigManager with LLM inference routing.
Fetches active provider from database and returns configuration for LiteLLM/WilmerRouter.

This module bridges the gap between:
- Provider management (llm_config_manager.py)
- Intelligent routing (wilmer_router.py)
- Actual inference (litellm_api.py)

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from llm_config_manager import LLMConfigManager, Purpose, ProviderType

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfiguration:
    """
    Active provider configuration for LLM inference.

    This is returned by get_active_llm_provider() and used by:
    - litellm_api.py for routing requests
    - wilmer_router.py for intelligent provider selection
    """
    provider_type: str  # "ai_server" or "api_key"
    provider_id: int

    # For AI Server providers
    base_url: Optional[str] = None
    server_type: Optional[str] = None  # "vllm", "ollama", "llamacpp", "openai-compatible"
    model_path: Optional[str] = None

    # For API Key providers
    provider_name: Optional[str] = None  # "openrouter", "openai", "anthropic", etc.
    api_key: Optional[str] = None  # Decrypted API key (SENSITIVE - use carefully)

    # Common fields
    enabled: bool = True
    purpose: str = "chat"  # "chat", "embeddings", "reranking"

    # Fallback configuration
    fallback_provider_type: Optional[str] = None
    fallback_provider_id: Optional[int] = None

    # Metadata
    health_status: Optional[str] = None
    last_health_check: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_litellm_config(self) -> Dict[str, Any]:
        """
        Convert to LiteLLM configuration format.

        Returns:
            Dict with keys: api_base, api_key, model, etc.
        """
        if self.provider_type == ProviderType.AI_SERVER.value:
            # AI Server configuration (local vLLM, Ollama, etc.)
            return {
                "api_base": self.base_url,
                "api_key": self.api_key or "dummy",  # Some servers don't need key
                "model": self.model_path or "default",
                "custom_llm_provider": self.server_type,
                "metadata": {
                    "provider_id": self.provider_id,
                    "provider_type": "ai_server",
                    "server_type": self.server_type
                }
            }
        else:
            # API Key configuration (OpenRouter, OpenAI, Anthropic, etc.)
            return {
                "api_key": self.api_key,
                "custom_llm_provider": self.provider_name,
                "metadata": {
                    "provider_id": self.provider_id,
                    "provider_type": "api_key",
                    "provider_name": self.provider_name
                }
            }

    def to_wilmer_config(self) -> Dict[str, Any]:
        """
        Convert to WilmerRouter configuration format.

        Returns:
            Dict with provider info for intelligent routing
        """
        return {
            "provider_type": self.provider_type,
            "provider_id": self.provider_id,
            "provider_name": self.provider_name if self.provider_type == "api_key" else self.server_type,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "is_local": self.provider_type == "ai_server" and self.server_type in ["vllm", "ollama", "llamacpp"],
            "supports_streaming": True,  # Most providers support streaming
            "metadata": self.metadata
        }


class LLMProviderIntegration:
    """
    Integration layer for LLM provider management and inference routing.

    This class provides a simple interface for:
    1. Getting active provider for a purpose (chat/embeddings/reranking)
    2. Converting provider config to LiteLLM format
    3. Handling fallback providers
    4. Caching provider configs for performance
    """

    def __init__(self, llm_manager: LLMConfigManager):
        """
        Initialize provider integration.

        Args:
            llm_manager: LLMConfigManager instance
        """
        self.llm_manager = llm_manager
        self._config_cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes

    async def get_active_llm_provider(self, purpose: str = "chat") -> Optional[ProviderConfiguration]:
        """
        Get active LLM provider configuration for specified purpose.

        This is the main integration point. It:
        1. Queries active_providers table for the purpose (chat/embeddings/reranking)
        2. Fetches the provider details (AI server or API key)
        3. Decrypts API key if provider_type="api_key"
        4. Returns ProviderConfiguration ready for use

        Args:
            purpose: "chat", "embeddings", or "reranking"

        Returns:
            ProviderConfiguration with all needed info, or None if no active provider

        Example:
            >>> integration = LLMProviderIntegration(llm_manager)
            >>> config = await integration.get_active_llm_provider("chat")
            >>> if config:
            >>>     litellm_config = config.to_litellm_config()
            >>>     # Use litellm_config for inference
        """
        try:
            # Validate purpose
            valid_purposes = [Purpose.CHAT.value, Purpose.EMBEDDINGS.value, Purpose.RERANKING.value]
            if purpose not in valid_purposes:
                logger.error(f"Invalid purpose: {purpose}. Must be one of: {valid_purposes}")
                return None

            # Check cache first
            cache_key = f"active_provider:{purpose}"
            if cache_key in self._config_cache:
                logger.debug(f"Returning cached provider config for {purpose}")
                return self._config_cache[cache_key]

            # Fetch active provider from database
            logger.info(f"Fetching active provider for purpose: {purpose}")
            active_provider = await self.llm_manager.get_active_provider(purpose)

            if not active_provider:
                logger.warning(f"No active provider configured for {purpose}")
                return None

            provider_type = active_provider['provider_type']
            provider_id = active_provider['provider_id']
            provider_data = active_provider['provider']

            logger.info(f"Active provider for {purpose}: {provider_type}/{provider_id}")

            # Build ProviderConfiguration based on type
            if provider_type == ProviderType.AI_SERVER.value:
                # AI Server provider
                config = ProviderConfiguration(
                    provider_type=provider_type,
                    provider_id=provider_id,
                    base_url=provider_data.get('base_url'),
                    server_type=provider_data.get('server_type'),
                    model_path=provider_data.get('model_path'),
                    api_key=provider_data.get('api_key'),
                    enabled=provider_data.get('enabled', True),
                    purpose=purpose,
                    fallback_provider_type=active_provider.get('fallback_provider_type'),
                    fallback_provider_id=active_provider.get('fallback_provider_id'),
                    health_status=provider_data.get('health_status'),
                    last_health_check=str(provider_data.get('last_health_check')) if provider_data.get('last_health_check') else None,
                    metadata=provider_data.get('metadata', {})
                )

                logger.info(
                    f"AI Server provider: {config.server_type} at {config.base_url}"
                )

            elif provider_type == ProviderType.API_KEY.value:
                # API Key provider - need to decrypt the key
                # WARNING: This exposes the decrypted API key - use carefully!
                # Only call this in trusted code paths (not in API responses)

                # Get API key with decryption
                key_data = await self.llm_manager.get_api_key(provider_id, decrypt=True)

                if not key_data:
                    logger.error(f"API key {provider_id} not found")
                    return None

                if not key_data.get('enabled', True):
                    logger.error(f"API key {provider_id} is disabled")
                    return None

                config = ProviderConfiguration(
                    provider_type=provider_type,
                    provider_id=provider_id,
                    provider_name=key_data.get('provider'),  # "openrouter", "openai", etc.
                    api_key=key_data.get('api_key'),  # DECRYPTED KEY - SENSITIVE!
                    enabled=key_data.get('enabled', True),
                    purpose=purpose,
                    fallback_provider_type=active_provider.get('fallback_provider_type'),
                    fallback_provider_id=active_provider.get('fallback_provider_id'),
                    metadata=key_data.get('metadata', {})
                )

                logger.info(
                    f"API Key provider: {config.provider_name} (key_id={provider_id})"
                )

            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None

            # Cache the config
            self._config_cache[cache_key] = config

            return config

        except Exception as e:
            logger.error(f"Failed to get active LLM provider for {purpose}: {e}")
            return None

    async def get_fallback_provider(self, primary_config: ProviderConfiguration) -> Optional[ProviderConfiguration]:
        """
        Get fallback provider if primary is configured.

        Args:
            primary_config: Primary provider configuration

        Returns:
            ProviderConfiguration for fallback, or None if no fallback configured
        """
        if not primary_config.fallback_provider_type or not primary_config.fallback_provider_id:
            logger.debug("No fallback provider configured")
            return None

        try:
            # Fetch fallback provider
            if primary_config.fallback_provider_type == ProviderType.AI_SERVER.value:
                provider_data = await self.llm_manager.get_ai_server(primary_config.fallback_provider_id)

                if not provider_data:
                    logger.error(f"Fallback AI server {primary_config.fallback_provider_id} not found")
                    return None

                return ProviderConfiguration(
                    provider_type=primary_config.fallback_provider_type,
                    provider_id=primary_config.fallback_provider_id,
                    base_url=provider_data.base_url,
                    server_type=provider_data.server_type,
                    model_path=provider_data.model_path,
                    api_key=provider_data.api_key,
                    enabled=provider_data.enabled,
                    purpose=primary_config.purpose,
                    metadata=provider_data.metadata or {}
                )

            elif primary_config.fallback_provider_type == ProviderType.API_KEY.value:
                key_data = await self.llm_manager.get_api_key(primary_config.fallback_provider_id, decrypt=True)

                if not key_data:
                    logger.error(f"Fallback API key {primary_config.fallback_provider_id} not found")
                    return None

                return ProviderConfiguration(
                    provider_type=primary_config.fallback_provider_type,
                    provider_id=primary_config.fallback_provider_id,
                    provider_name=key_data.get('provider'),
                    api_key=key_data.get('api_key'),
                    enabled=key_data.get('enabled', True),
                    purpose=primary_config.purpose,
                    metadata=key_data.get('metadata', {})
                )

        except Exception as e:
            logger.error(f"Failed to get fallback provider: {e}")
            return None

    def clear_cache(self):
        """Clear provider configuration cache."""
        self._config_cache = {}
        logger.info("Provider config cache cleared")

    async def test_provider(self, config: ProviderConfiguration) -> tuple[bool, str]:
        """
        Test if provider is accessible and working.

        Args:
            config: Provider configuration to test

        Returns:
            Tuple of (success, message)
        """
        try:
            if config.provider_type == ProviderType.AI_SERVER.value:
                # Test AI server
                health_status, message = await self.llm_manager.test_ai_server(config.provider_id)
                success = health_status.value == "healthy"
                return success, message

            elif config.provider_type == ProviderType.API_KEY.value:
                # Test API key
                success, message = await self.llm_manager.test_api_key(config.provider_id)
                return success, message

            else:
                return False, f"Unknown provider type: {config.provider_type}"

        except Exception as e:
            logger.error(f"Failed to test provider: {e}")
            return False, str(e)


# ============================================================================
# Usage Example
# ============================================================================

async def example_usage(llm_manager: LLMConfigManager):
    """
    Example: How to use LLMProviderIntegration in your code.

    This shows the typical workflow:
    1. Initialize integration with LLMConfigManager
    2. Get active provider for "chat"
    3. Convert to LiteLLM config
    4. Use for inference
    5. Handle fallback if primary fails
    """
    # 1. Initialize
    integration = LLMProviderIntegration(llm_manager)

    # 2. Get active provider
    provider_config = await integration.get_active_llm_provider("chat")

    if not provider_config:
        logger.error("No active provider configured for chat")
        return

    # 3. Convert to LiteLLM config
    litellm_config = provider_config.to_litellm_config()

    logger.info(f"Using provider: {provider_config.provider_name or provider_config.server_type}")
    logger.info(f"LiteLLM config: {litellm_config}")

    # 4. Test provider
    success, message = await integration.test_provider(provider_config)

    if not success:
        logger.warning(f"Provider test failed: {message}")

        # 5. Try fallback
        fallback = await integration.get_fallback_provider(provider_config)
        if fallback:
            logger.info("Switching to fallback provider")
            provider_config = fallback
            litellm_config = provider_config.to_litellm_config()
        else:
            logger.error("No fallback provider available")
            return

    # 6. Use for inference
    # import litellm
    # response = litellm.completion(
    #     model=litellm_config.get('model', 'gpt-3.5-turbo'),
    #     messages=[{"role": "user", "content": "Hello"}],
    #     api_base=litellm_config.get('api_base'),
    #     api_key=litellm_config.get('api_key')
    # )

    logger.info("Inference successful")
