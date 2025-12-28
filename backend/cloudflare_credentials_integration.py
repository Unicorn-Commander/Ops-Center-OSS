"""
Cloudflare API Token Integration with CredentialManager

This module provides helper functions to integrate the new CredentialManager
with the existing cloudflare_api.py endpoints.

Usage:
    from cloudflare_credentials_integration import get_cloudflare_token

    # In your endpoint
    token = await get_cloudflare_token(user_id, db_connection)
    cloudflare_manager = CloudflareManager(api_token=token)

Epic 1.6: Cloudflare Integration with Credential Management
Author: Backend Development Team Lead
Date: October 23, 2025
"""

import os
import logging
from typing import Optional
from fastapi import HTTPException

# Import credential manager
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
from credential_manager import CredentialManager, CredentialNotFoundError

logger = logging.getLogger(__name__)


async def get_cloudflare_token(
    user_id: str,
    db_connection,
    fallback_to_env: bool = True
) -> str:
    """
    Get Cloudflare API token for user from database or environment

    This function retrieves the Cloudflare API token using the following priority:
    1. User's stored credential in database (encrypted)
    2. Environment variable CLOUDFLARE_API_TOKEN (if fallback_to_env=True)

    Args:
        user_id: Keycloak user ID
        db_connection: PostgreSQL database connection
        fallback_to_env: If True, fallback to CLOUDFLARE_API_TOKEN env var

    Returns:
        Decrypted Cloudflare API token (plaintext)

    Raises:
        HTTPException(400): No Cloudflare credentials configured

    Example:
        ```python
        # In cloudflare_api.py endpoint
        from cloudflare_credentials_integration import get_cloudflare_token
        from database.connection import get_db_pool

        async def my_endpoint(request: Request):
            admin = await require_admin(request)
            user_id = admin.get("user_id")

            db_pool = await get_db_pool()
            async with db_pool.acquire() as conn:
                token = await get_cloudflare_token(user_id, conn)

            # Use token with CloudflareManager
            manager = CloudflareManager(api_token=token)
            ...
        ```
    """
    try:
        # Try to get from database first
        credential_manager = CredentialManager(db_connection=db_connection)

        token = await credential_manager.get_credential_for_api(
            user_id=user_id,
            service="cloudflare",
            credential_type="api_token"
        )

        if token:
            logger.debug(f"Retrieved Cloudflare token from database for user={user_id}")
            return token

        # Fallback to environment variable
        if fallback_to_env:
            env_token = os.getenv("CLOUDFLARE_API_TOKEN")
            if env_token:
                logger.info(f"Using CLOUDFLARE_API_TOKEN environment variable for user={user_id}")
                return env_token

        # No token found
        raise HTTPException(
            status_code=400,
            detail=(
                "No Cloudflare API token configured. "
                "Please add your Cloudflare API token in Settings > Credentials."
            )
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve Cloudflare token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve Cloudflare credentials"
        )


async def get_namecheap_credentials(
    user_id: str,
    db_connection,
    fallback_to_env: bool = True
) -> dict:
    """
    Get NameCheap API credentials for user from database or environment

    NameCheap requires both API key and username. This function retrieves both.

    Args:
        user_id: Keycloak user ID
        db_connection: PostgreSQL database connection
        fallback_to_env: If True, fallback to environment variables

    Returns:
        Dictionary with:
        - api_key: NameCheap API key
        - api_user: NameCheap username

    Raises:
        HTTPException(400): No NameCheap credentials configured

    Example:
        ```python
        # In migration_api.py endpoint
        from cloudflare_credentials_integration import get_namecheap_credentials

        async def my_endpoint(request: Request):
            admin = await require_admin(request)
            user_id = admin.get("user_id")

            db_pool = await get_db_pool()
            async with db_pool.acquire() as conn:
                credentials = await get_namecheap_credentials(user_id, conn)

            api_key = credentials["api_key"]
            api_user = credentials["api_user"]
            ...
        ```
    """
    try:
        credential_manager = CredentialManager(db_connection=db_connection)

        # Get API key
        api_key = await credential_manager.get_credential_for_api(
            user_id=user_id,
            service="namecheap",
            credential_type="api_key"
        )

        # Get username
        api_user = await credential_manager.get_credential_for_api(
            user_id=user_id,
            service="namecheap",
            credential_type="api_user"
        )

        # If both found in database, return them
        if api_key and api_user:
            logger.debug(f"Retrieved NameCheap credentials from database for user={user_id}")
            return {
                "api_key": api_key,
                "api_user": api_user
            }

        # Fallback to environment variables
        if fallback_to_env:
            env_api_key = os.getenv("NAMECHEAP_API_KEY")
            env_api_user = os.getenv("NAMECHEAP_API_USER")

            if env_api_key and env_api_user:
                logger.info(f"Using NAMECHEAP_* environment variables for user={user_id}")
                return {
                    "api_key": env_api_key,
                    "api_user": env_api_user
                }

        # No credentials found
        raise HTTPException(
            status_code=400,
            detail=(
                "No NameCheap API credentials configured. "
                "Please add your NameCheap API key and username in Settings > Credentials."
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve NameCheap credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve NameCheap credentials"
        )


async def get_github_token(
    user_id: str,
    db_connection,
    fallback_to_env: bool = True
) -> str:
    """
    Get GitHub API token for user from database or environment

    Args:
        user_id: Keycloak user ID
        db_connection: PostgreSQL database connection
        fallback_to_env: If True, fallback to GITHUB_API_TOKEN env var

    Returns:
        GitHub API token (plaintext)

    Raises:
        HTTPException(400): No GitHub credentials configured
    """
    try:
        credential_manager = CredentialManager(db_connection=db_connection)

        token = await credential_manager.get_credential_for_api(
            user_id=user_id,
            service="github",
            credential_type="api_token"
        )

        if token:
            return token

        if fallback_to_env:
            env_token = os.getenv("GITHUB_API_TOKEN")
            if env_token:
                logger.info(f"Using GITHUB_API_TOKEN environment variable for user={user_id}")
                return env_token

        raise HTTPException(
            status_code=400,
            detail="No GitHub API token configured"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve GitHub credentials"
        )


async def get_stripe_secret_key(
    user_id: str,
    db_connection,
    fallback_to_env: bool = True
) -> str:
    """
    Get Stripe secret key for user from database or environment

    Args:
        user_id: Keycloak user ID
        db_connection: PostgreSQL database connection
        fallback_to_env: If True, fallback to STRIPE_SECRET_KEY env var

    Returns:
        Stripe secret key (plaintext)

    Raises:
        HTTPException(400): No Stripe credentials configured
    """
    try:
        credential_manager = CredentialManager(db_connection=db_connection)

        secret_key = await credential_manager.get_credential_for_api(
            user_id=user_id,
            service="stripe",
            credential_type="secret_key"
        )

        if secret_key:
            return secret_key

        if fallback_to_env:
            env_key = os.getenv("STRIPE_SECRET_KEY")
            if env_key:
                logger.info(f"Using STRIPE_SECRET_KEY environment variable for user={user_id}")
                return env_key

        raise HTTPException(
            status_code=400,
            detail="No Stripe secret key configured"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve Stripe secret key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve Stripe credentials"
        )
