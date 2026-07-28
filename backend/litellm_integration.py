"""
LiteLLM Integration with BYOK Support

This module provides a wrapper around LiteLLM that automatically uses
user's BYOK configuration or falls back to system defaults.
"""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx
import json
from datetime import datetime

from byok_service import get_byok_service

logger = logging.getLogger(__name__)

# LiteLLM server URL (assuming LiteLLM is running as a proxy server)
LITELLM_PROXY_URL = "http://localhost:4000"


class LiteLLMClient:
    """Client for LiteLLM with BYOK support"""

    def __init__(self):
        self.byok_service = get_byok_service()

    async def chat_completion(
        self,
        user: Dict[str, Any],
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using user's BYOK or system default.

        Args:
            user: User object from Keycloak
            messages: List of message dicts
            model: Specific model to use (optional)
            provider: Specific provider to use (optional)
            stream: Whether to stream response
            **kwargs: Additional parameters for completion

        Returns:
            Completion response dict
        """
        # Get provider config (BYOK or default)
        config = await self.byok_service.get_user_provider_config(user, provider, model)

        logger.info(
            f"User {user.get('email')} using {'BYOK' if config['is_byok'] else 'system default'} "
            f"provider: {config['provider']}, model: {config['model']}"
        )

        # Build request
        request_data = {
            "model": config["model"],
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        # Call LiteLLM based on format
        if config["format"] == "anthropic":
            return await self._call_anthropic(config, request_data)
        else:
            return await self._call_openai_format(config, request_data)

    async def _call_openai_format(
        self,
        config: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call LiteLLM with OpenAI-compatible format"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{config['base_url']}/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {config['api_key']}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"LiteLLM call failed: {e}")
                raise

    async def _call_anthropic(
        self,
        config: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call Anthropic API directly"""
        # Convert OpenAI format to Anthropic format
        anthropic_request = {
            "model": request_data["model"],
            "messages": request_data["messages"],
            "max_tokens": request_data.get("max_tokens", 4096),
            "stream": request_data.get("stream", False)
        }

        if "temperature" in request_data:
            anthropic_request["temperature"] = request_data["temperature"]
        if "top_p" in request_data:
            anthropic_request["top_p"] = request_data["top_p"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{config['base_url']}/messages",
                    json=anthropic_request,
                    headers={
                        "x-api-key": config['api_key'],
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Anthropic API call failed: {e}")
                raise

    async def stream_completion(
        self,
        user: Dict[str, Any],
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a chat completion using user's BYOK or system default.

        Args:
            user: User object from Keycloak
            messages: List of message dicts
            model: Specific model to use (optional)
            provider: Specific provider to use (optional)
            **kwargs: Additional parameters for completion

        Yields:
            Completion chunk dicts
        """
        # Get provider config (BYOK or default)
        config = await self.byok_service.get_user_provider_config(user, provider, model)

        logger.info(
            f"User {user.get('email')} streaming with {'BYOK' if config['is_byok'] else 'system default'} "
            f"provider: {config['provider']}, model: {config['model']}"
        )

        # Build request
        request_data = {
            "model": config["model"],
            "messages": messages,
            "stream": True,
            **kwargs
        }

        # Stream based on format
        if config["format"] == "anthropic":
            async for chunk in self._stream_anthropic(config, request_data):
                yield chunk
        else:
            async for chunk in self._stream_openai_format(config, request_data):
                yield chunk

    async def _stream_openai_format(
        self,
        config: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream OpenAI-compatible response"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{config['base_url']}/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {config['api_key']}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
            except httpx.HTTPError as e:
                logger.error(f"Streaming failed: {e}")
                raise

    async def _stream_anthropic(
        self,
        config: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream Anthropic response"""
        # Convert to Anthropic format
        anthropic_request = {
            "model": request_data["model"],
            "messages": request_data["messages"],
            "max_tokens": request_data.get("max_tokens", 4096),
            "stream": True
        }

        if "temperature" in request_data:
            anthropic_request["temperature"] = request_data["temperature"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{config['base_url']}/messages",
                    json=anthropic_request,
                    headers={
                        "x-api-key": config['api_key'],
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
            except httpx.HTTPError as e:
                logger.error(f"Anthropic streaming failed: {e}")
                raise

    async def get_available_models(
        self,
        user: Dict[str, Any],
        provider: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get list of available models for user.

        Returns models from user's BYOK providers or system defaults.
        """
        from byok_service import PROVIDER_CONFIGS

        user_attributes = user.get("attributes", {})
        byok_service = get_byok_service()
        byok_providers = byok_service._get_user_byok_providers(user_attributes)

        models = []

        # Add models from BYOK providers
        for provider_id, byok_data in byok_providers.items():
            provider_config = PROVIDER_CONFIGS.get(provider_id, {})
            for model_name in provider_config.get("models", []):
                models.append({
                    "id": f"{provider_id}/{model_name}",
                    "name": model_name,
                    "provider": provider_id,
                    "source": "byok"
                })

        # Add system default models if no BYOK configured
        if not models:
            from byok_service import DEFAULT_PROVIDER
            default_config = PROVIDER_CONFIGS.get(DEFAULT_PROVIDER, {})
            for model_name in default_config.get("models", []):
                models.append({
                    "id": f"{DEFAULT_PROVIDER}/{model_name}",
                    "name": model_name,
                    "provider": DEFAULT_PROVIDER,
                    "source": "system"
                })

        return models


# Singleton instance
_litellm_client: Optional[LiteLLMClient] = None


def get_litellm_client() -> LiteLLMClient:
    """Get or create singleton LiteLLM client instance"""
    global _litellm_client
    if _litellm_client is None:
        _litellm_client = LiteLLMClient()
    return _litellm_client
