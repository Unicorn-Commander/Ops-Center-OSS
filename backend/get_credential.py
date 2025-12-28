"""
Universal credential helper - reads from database first, falls back to environment.

This module provides a unified way for all APIs to retrieve credentials,
checking the platform_settings database first before falling back to environment variables.
"""

import os
import asyncpg
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "unicorn")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
DB_NAME = os.getenv("POSTGRES_DB", "unicorn_db")

# Cache for credentials (to avoid DB queries on every request)
_credential_cache = {}


async def get_credential_from_db(key: str) -> Optional[str]:
    """
    Get credential from platform_settings database.

    Args:
        key: Setting key (e.g., 'CLOUDFLARE_API_TOKEN', 'STRIPE_SECRET_KEY')

    Returns:
        Credential value if found, None otherwise
    """
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        # Query platform_settings table
        result = await conn.fetchval(
            "SELECT value FROM platform_settings WHERE key = $1",
            key
        )

        await conn.close()
        return result

    except Exception as e:
        logger.warning(f"Failed to get credential '{key}' from database: {e}")
        return None


def get_credential(key: str, default: str = "") -> str:
    """
    Get credential from database first, then environment variable, then default.

    This function tries to retrieve credentials in the following order:
    1. Cache (if previously fetched)
    2. platform_settings database
    3. Environment variable
    4. Default value

    Args:
        key: Setting key (e.g., 'CLOUDFLARE_API_TOKEN')
        default: Default value if not found anywhere

    Returns:
        Credential value

    Example:
        >>> token = get_credential("CLOUDFLARE_API_TOKEN")
        >>> stripe_key = get_credential("STRIPE_SECRET_KEY", "")
    """
    # Check cache first
    if key in _credential_cache:
        return _credential_cache[key]

    # Try database (synchronously wrapped)
    try:
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Fetch from database
        if loop.is_running():
            # If loop is already running, create a task
            future = asyncio.ensure_future(get_credential_from_db(key))
            # We can't await here, so fall back to env
            logger.info(f"Event loop running, falling back to env for '{key}'")
            value = os.getenv(key, "").strip()
        else:
            # Run async function synchronously
            value = loop.run_until_complete(get_credential_from_db(key))

    except Exception as e:
        logger.warning(f"Error fetching '{key}' from database: {e}")
        value = None

    # If not in database, check environment variable
    if not value:
        value = os.getenv(key, "").strip()
        if value:
            logger.info(f"Credential '{key}' loaded from environment variable")
    else:
        logger.info(f"Credential '{key}' loaded from database")

    # If still not found, use default
    if not value:
        value = default
        if default:
            logger.info(f"Credential '{key}' using default value")
        else:
            logger.warning(f"Credential '{key}' not found in database or environment")

    # Cache the result
    if value:
        _credential_cache[key] = value

    return value


async def get_credential_async(key: str, default: str = "") -> str:
    """
    Async version of get_credential.

    Args:
        key: Setting key
        default: Default value if not found

    Returns:
        Credential value
    """
    # Check cache first
    if key in _credential_cache:
        return _credential_cache[key]

    # Try database
    value = await get_credential_from_db(key)

    # If not in database, check environment
    if not value:
        value = os.getenv(key, "").strip()
        if value:
            logger.info(f"Credential '{key}' loaded from environment variable")
    else:
        logger.info(f"Credential '{key}' loaded from database")

    # If still not found, use default
    if not value:
        value = default
        if default:
            logger.info(f"Credential '{key}' using default value")
        else:
            logger.warning(f"Credential '{key}' not found in database or environment")

    # Cache the result
    if value:
        _credential_cache[key] = value

    return value


def clear_credential_cache():
    """Clear the credential cache. Call this when settings are updated."""
    global _credential_cache
    _credential_cache = {}
    logger.info("Credential cache cleared")


# For backward compatibility, keep the old function names
def get_setting(key: str, default: str = "") -> str:
    """Alias for get_credential."""
    return get_credential(key, default)


async def get_setting_async(key: str, default: str = "") -> str:
    """Alias for get_credential_async."""
    return await get_credential_async(key, default)
