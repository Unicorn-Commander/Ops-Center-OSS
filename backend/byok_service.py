"""
BYOK Service - Business Logic for Bring Your Own Key

Handles retrieval and management of user's BYOK configurations,
including fallback to system defaults when user hasn't configured their own keys.
"""

import logging
from typing import Dict, Any, Optional, List
from key_encryption import get_encryption
import os

logger = logging.getLogger(__name__)

# System default provider configuration
DEFAULT_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openrouter")
DEFAULT_API_KEY = os.getenv("DEFAULT_LLM_API_KEY", "")
DEFAULT_BASE_URL = os.getenv("DEFAULT_LLM_BASE_URL", "https://openrouter.ai/api/v1")

# Provider configurations
PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
        "supports_streaming": True,
        "format": "openai"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "supports_streaming": True,
        "format": "anthropic"
    },
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co/models",
        "models": ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
        "supports_streaming": False,
        "format": "huggingface"
    },
    "cohere": {
        "base_url": "https://api.cohere.ai/v1",
        "models": ["command-r-plus", "command-r", "command"],
        "supports_streaming": True,
        "format": "cohere"
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "models": ["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-2-70b-chat-hf"],
        "supports_streaming": True,
        "format": "openai"
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "models": ["pplx-70b-online", "pplx-7b-chat"],
        "supports_streaming": True,
        "format": "openai"
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
        "supports_streaming": True,
        "format": "openai"
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo", "meta-llama/llama-3-70b-instruct"],
        "supports_streaming": True,
        "format": "openai"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "models": ["llama2", "mistral", "codellama"],
        "supports_streaming": True,
        "format": "openai"
    },
    "custom": {
        "base_url": None,  # User-provided
        "models": [],
        "supports_streaming": True,
        "format": "openai"
    }
}


class BYOKService:
    """Service for managing BYOK configurations"""

    def __init__(self):
        self.encryption = get_encryption()

    async def get_user_provider_config(
        self,
        user: Dict[str, Any],
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get LLM provider configuration for user.

        Priority:
        1. User's preferred provider if specified
        2. User's BYOK configuration
        3. System default provider

        Args:
            user: User object from Keycloak
            preferred_provider: Specific provider requested
            preferred_model: Specific model requested

        Returns:
            Configuration dict with:
            - provider: Provider name
            - api_key: API key (decrypted)
            - base_url: Base URL for API
            - model: Model to use
            - format: API format (openai, anthropic, etc.)
            - is_byok: Whether this is user's own key
        """
        user_attributes = user.get("attributes", {})

        # Helper to extract from Keycloak array format
        def get_attr(key, default=None):
            val = user_attributes.get(key, [default])
            return val[0] if isinstance(val, list) and val else default

        # Check if user has BYOK configured
        byok_providers = self._get_user_byok_providers(user_attributes)

        # If preferred provider specified and user has it configured
        if preferred_provider and preferred_provider in byok_providers:
            return await self._build_provider_config(
                preferred_provider,
                byok_providers[preferred_provider],
                preferred_model,
                is_byok=True
            )

        # If user has any BYOK configured, use first available
        if byok_providers:
            provider = list(byok_providers.keys())[0]
            return await self._build_provider_config(
                provider,
                byok_providers[provider],
                preferred_model,
                is_byok=True
            )

        # Fall back to system default
        logger.info(f"User {user.get('email')} has no BYOK configured, using system default")
        return self._get_default_provider_config(preferred_model)

    def _get_user_byok_providers(self, attributes: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract all configured BYOK providers from user attributes"""
        providers = {}

        for provider_id in PROVIDER_CONFIGS.keys():
            key_attr = f"byok_{provider_id}_key"

            # Check if attribute exists and has value
            if key_attr in attributes:
                key_val = attributes.get(key_attr, [])
                if isinstance(key_val, list) and len(key_val) > 0 and key_val[0]:
                    # Extract all related attributes
                    def get_attr(suffix, default=None):
                        val = attributes.get(f"byok_{provider_id}_{suffix}", [default])
                        return val[0] if isinstance(val, list) and val else default

                    providers[provider_id] = {
                        "encrypted_key": key_val[0],
                        "label": get_attr("label"),
                        "endpoint": get_attr("endpoint"),
                        "added_date": get_attr("added_date"),
                        "last_tested": get_attr("last_tested"),
                        "test_status": get_attr("test_status")
                    }

        return providers

    async def _build_provider_config(
        self,
        provider: str,
        byok_data: Dict[str, Any],
        preferred_model: Optional[str] = None,
        is_byok: bool = True
    ) -> Dict[str, Any]:
        """Build provider configuration from BYOK data"""
        # Decrypt API key
        try:
            api_key = self.encryption.decrypt_key(byok_data["encrypted_key"])
        except Exception as e:
            logger.error(f"Failed to decrypt BYOK key for {provider}: {e}")
            # Fall back to default
            return self._get_default_provider_config(preferred_model)

        provider_config = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["custom"])

        # Determine base URL
        base_url = byok_data.get("endpoint") or provider_config.get("base_url")

        # Determine model
        model = preferred_model
        if not model:
            # Use first available model for provider
            models = provider_config.get("models", [])
            model = models[0] if models else "default"

        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "format": provider_config.get("format", "openai"),
            "supports_streaming": provider_config.get("supports_streaming", True),
            "is_byok": is_byok,
            "label": byok_data.get("label"),
            "last_tested": byok_data.get("last_tested"),
            "test_status": byok_data.get("test_status")
        }

    def _get_default_provider_config(self, preferred_model: Optional[str] = None) -> Dict[str, Any]:
        """Get system default provider configuration"""
        provider_config = PROVIDER_CONFIGS.get(DEFAULT_PROVIDER, PROVIDER_CONFIGS["openrouter"])

        # Determine model
        model = preferred_model
        if not model:
            models = provider_config.get("models", [])
            model = models[0] if models else "default"

        return {
            "provider": DEFAULT_PROVIDER,
            "api_key": DEFAULT_API_KEY,
            "base_url": DEFAULT_BASE_URL,
            "model": model,
            "format": provider_config.get("format", "openai"),
            "supports_streaming": provider_config.get("supports_streaming", True),
            "is_byok": False
        }

    async def get_litellm_config(
        self,
        user: Dict[str, Any],
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get LiteLLM-compatible configuration.

        Returns configuration in format expected by LiteLLM:
        {
            "model": "provider/model-name",
            "api_key": "...",
            "api_base": "...",
            "custom_llm_provider": "..."
        }
        """
        config = await self.get_user_provider_config(user, provider, model)

        # Build LiteLLM config
        litellm_config = {
            "api_key": config["api_key"],
            "api_base": config["base_url"]
        }

        # Format model name for LiteLLM
        if config["provider"] == "ollama":
            litellm_config["model"] = f"ollama/{config['model']}"
            litellm_config["custom_llm_provider"] = "ollama"
        elif config["provider"] == "anthropic":
            litellm_config["model"] = config["model"]
            litellm_config["custom_llm_provider"] = "anthropic"
        elif config["format"] == "openai":
            litellm_config["model"] = config["model"]
            litellm_config["custom_llm_provider"] = config["provider"]
        else:
            litellm_config["model"] = config["model"]

        return litellm_config

    async def get_execution_server_config(
        self,
        user_id: str,
        server_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get execution server configuration for Brigade.

        Args:
            user_id: User ID from Keycloak
            server_id: Specific server ID, or None for default

        Returns:
            Execution server config or None if not configured
        """
        import asyncpg
        import os
        import json
        import uuid

        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ops_center")

        try:
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                if server_id:
                    # Get specific server
                    row = await conn.fetchrow("""
                        SELECT id, name, server_type, connection_config, workspace_path
                        FROM user_execution_servers
                        WHERE id = $1 AND user_id = $2 AND is_active = true
                    """, uuid.UUID(server_id), user_id)
                else:
                    # Get default server
                    row = await conn.fetchrow("""
                        SELECT id, name, server_type, connection_config, workspace_path
                        FROM user_execution_servers
                        WHERE user_id = $1 AND is_default = true AND is_active = true
                    """, user_id)

                if not row:
                    return None

                config = json.loads(row['connection_config']) if isinstance(row['connection_config'], str) else row['connection_config']

                # Decrypt sensitive fields
                from execution_servers_api import decrypt_sensitive_fields
                decrypted_config = decrypt_sensitive_fields(config, row['server_type'])

                return {
                    "id": str(row['id']),
                    "name": row['name'],
                    "type": row['server_type'],
                    "connection": decrypted_config,
                    "workspace": row['workspace_path']
                }
            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Failed to get execution server config: {e}")
            return None


# Singleton instance
_byok_service: Optional[BYOKService] = None


def get_byok_service() -> BYOKService:
    """Get or create singleton BYOK service instance"""
    global _byok_service
    if _byok_service is None:
        _byok_service = BYOKService()
    return _byok_service
