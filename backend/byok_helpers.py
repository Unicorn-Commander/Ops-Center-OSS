"""
BYOK Helper Functions
Utilities for retrieving and using user API keys in services
"""

import os
import httpx
from typing import Optional, Dict, Any
import logging

from key_encryption import get_encryption

logger = logging.getLogger(__name__)

# Cache for user keys (reduces Authentik API calls)
_user_keys_cache: Dict[str, Dict[str, Any]] = {}

async def get_user_from_keycloak(email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user data from Keycloak

    Args:
        email: User email address

    Returns:
        User data dict or None if not found
    """
    from keycloak_integration import get_user_by_email as kc_get_user

    try:
        user = await kc_get_user(email)
        if not user:
            logger.warning(f"User not found in Keycloak: {email}")
        return user
    except Exception as e:
        logger.error(f"Error fetching user from Keycloak: {e}")
        return None


async def get_user_api_key(user_email: str, provider: str, use_cache: bool = True) -> Optional[str]:
    """
    Get user's decrypted API key for a specific provider

    Args:
        user_email: User's email address
        provider: Provider name (openai, anthropic, etc.)
        use_cache: Whether to use cached keys (default: True)

    Returns:
        Decrypted API key or None if not found
    """
    cache_key = f"{user_email}:{provider}"

    # Check cache first
    if use_cache and cache_key in _user_keys_cache:
        cached = _user_keys_cache[cache_key]
        # Simple cache expiry (5 minutes)
        import time
        if time.time() - cached["timestamp"] < 300:
            return cached["key"]

    # Fetch from Keycloak
    user = await get_user_from_keycloak(user_email)
    if not user:
        return None

    attributes = user.get("attributes", {})

    # Keycloak stores attributes as arrays, extract first value
    encrypted_key_list = attributes.get(f"byok_{provider}_key", [])
    encrypted_key = encrypted_key_list[0] if isinstance(encrypted_key_list, list) and encrypted_key_list else None

    if not encrypted_key:
        return None

    try:
        encryption = get_encryption()
        decrypted_key = encryption.decrypt_key(encrypted_key)

        # Cache it
        import time
        _user_keys_cache[cache_key] = {
            "key": decrypted_key,
            "timestamp": time.time()
        }

        return decrypted_key

    except Exception as e:
        logger.error(f"Error decrypting key for {user_email}/{provider}: {e}")
        return None


async def get_user_api_key_or_default(user_email: str, provider: str, fallback_env_var: str) -> str:
    """
    Get user's API key or fallback to system default

    Args:
        user_email: User's email address
        provider: Provider name (openai, anthropic, etc.)
        fallback_env_var: Environment variable name for system key

    Returns:
        User's key if configured, otherwise system default key

    Raises:
        ValueError: If neither user key nor system key is available
    """
    # Try to get user's BYOK key
    user_key = await get_user_api_key(user_email, provider)

    if user_key:
        logger.info(f"Using BYOK key for {user_email}/{provider}")
        return user_key

    # Fallback to system key
    system_key = os.getenv(fallback_env_var)

    if system_key:
        logger.info(f"Using system key for {user_email}/{provider}")
        return system_key

    raise ValueError(f"No API key available for {provider}. User has no BYOK key and system key not configured.")


async def get_user_custom_endpoint(user_email: str, provider: str) -> Optional[str]:
    """
    Get user's custom endpoint URL for a provider

    Args:
        user_email: User's email address
        provider: Provider name

    Returns:
        Custom endpoint URL or None
    """
    user = await get_user_from_keycloak(user_email)
    if not user:
        return None

    attributes = user.get("attributes", {})

    # Keycloak stores as arrays
    endpoint_list = attributes.get(f"byok_{provider}_endpoint", [])
    return endpoint_list[0] if isinstance(endpoint_list, list) and endpoint_list else None


def clear_user_key_cache(user_email: Optional[str] = None, provider: Optional[str] = None):
    """
    Clear cached API keys

    Args:
        user_email: If provided, only clear this user's cache
        provider: If provided, only clear this provider's cache
    """
    if user_email and provider:
        cache_key = f"{user_email}:{provider}"
        _user_keys_cache.pop(cache_key, None)
    elif user_email:
        # Clear all keys for this user
        keys_to_remove = [k for k in _user_keys_cache if k.startswith(f"{user_email}:")]
        for key in keys_to_remove:
            _user_keys_cache.pop(key, None)
    else:
        # Clear entire cache
        _user_keys_cache.clear()


# Service-specific helpers

async def get_openai_key_for_user(user_email: str) -> str:
    """Get OpenAI API key for user (BYOK or system default)"""
    return await get_user_api_key_or_default(
        user_email,
        "openai",
        "OPENAI_API_KEY"
    )


async def get_anthropic_key_for_user(user_email: str) -> str:
    """Get Anthropic API key for user (BYOK or system default)"""
    return await get_user_api_key_or_default(
        user_email,
        "anthropic",
        "ANTHROPIC_API_KEY"
    )


async def get_huggingface_token_for_user(user_email: str) -> str:
    """Get HuggingFace token for user (BYOK or system default)"""
    return await get_user_api_key_or_default(
        user_email,
        "huggingface",
        "HUGGINGFACE_TOKEN"
    )


async def get_llm_config_for_user(user_email: str, preferred_provider: str = "openai") -> Dict[str, Any]:
    """
    Get complete LLM configuration for user

    Args:
        user_email: User's email address
        preferred_provider: Preferred LLM provider

    Returns:
        Dict with api_key, provider, endpoint (if custom)
    """
    api_key = await get_user_api_key(user_email, preferred_provider)

    if not api_key:
        # Try fallback providers
        fallback_order = ["openai", "anthropic", "together", "groq"]
        for fallback in fallback_order:
            if fallback != preferred_provider:
                api_key = await get_user_api_key(user_email, fallback)
                if api_key:
                    preferred_provider = fallback
                    break

    if not api_key:
        # Use system defaults
        system_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "together": os.getenv("TOGETHER_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY")
        }

        for provider, key in system_keys.items():
            if key:
                api_key = key
                preferred_provider = provider
                break

    if not api_key:
        raise ValueError("No LLM API key available (BYOK or system)")

    # Get custom endpoint if exists
    endpoint = await get_user_custom_endpoint(user_email, preferred_provider)

    return {
        "api_key": api_key,
        "provider": preferred_provider,
        "endpoint": endpoint,
        "is_byok": bool(await get_user_api_key(user_email, preferred_provider))
    }


# Usage tracking helpers (for future billing integration)

async def record_api_usage(
    user_email: str,
    provider: str,
    tokens_used: int,
    cost_usd: float = 0.0
):
    """
    Record API usage for billing purposes

    Args:
        user_email: User's email
        provider: Provider name
        tokens_used: Number of tokens used
        cost_usd: Estimated cost in USD
    """
    # TODO: Implement usage tracking in database
    # For now, just log it
    logger.info(
        f"API usage: user={user_email}, provider={provider}, "
        f"tokens={tokens_used}, cost=${cost_usd:.6f}"
    )


# Example integration for OpenWebUI

async def proxy_openai_request_with_byok(
    user_email: str,
    model: str,
    messages: list,
    **kwargs
) -> Dict[str, Any]:
    """
    Example: Proxy OpenAI-compatible request using user's BYOK key

    Args:
        user_email: User's email
        model: Model name
        messages: Chat messages
        **kwargs: Additional parameters

    Returns:
        API response
    """
    # Get user's API key
    config = await get_llm_config_for_user(user_email, "openai")

    # Determine endpoint
    base_url = config.get("endpoint") or "https://api.openai.com/v1"

    # Make request with user's key
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                **kwargs
            }
        )

        response.raise_for_status()
        result = response.json()

        # Track usage
        if "usage" in result:
            tokens = result["usage"].get("total_tokens", 0)
            await record_api_usage(user_email, config["provider"], tokens)

        return result
