"""
BYOK (Bring Your Own Key) Manager

Securely store and retrieve user-provided API keys for LLM providers.
Keys are encrypted with Fernet symmetric encryption.

Author: Backend Developer #1
Date: October 20, 2025
"""

import logging
import os
from typing import Dict, List, Optional
import json

import asyncpg
from cryptography.fernet import Fernet
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class BYOKManager:
    """Manage user-provided API keys with encryption"""

    def __init__(self, db_pool: asyncpg.Pool, encryption_key: Optional[str] = None):
        """
        Initialize BYOK Manager

        Args:
            db_pool: PostgreSQL connection pool
            encryption_key: Base64-encoded Fernet key (generated if not provided)
        """
        self.db_pool = db_pool

        # Get or generate encryption key
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # Try to get from environment
            env_key = os.getenv('BYOK_ENCRYPTION_KEY')
            if env_key:
                self.encryption_key = env_key.encode()
            else:
                # Generate new key (WARNING: will lose access to existing keys!)
                logger.warning("No BYOK_ENCRYPTION_KEY found, generating new key")
                self.encryption_key = Fernet.generate_key()
                logger.warning(f"Generated encryption key: {self.encryption_key.decode()}")
                logger.warning("Add this to .env.auth as BYOK_ENCRYPTION_KEY to persist")

        # Initialize Fernet cipher
        try:
            self.cipher = Fernet(self.encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key")

    def _encrypt_key(self, api_key: str) -> str:
        """Encrypt API key"""
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to encrypt API key")

    def _decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        try:
            decrypted = self.cipher.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to decrypt API key")

    async def store_user_api_key(
        self,
        user_id: str,
        provider: str,
        api_key: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store user's API key for a provider

        Args:
            user_id: User identifier
            provider: Provider name (e.g., "openai", "anthropic")
            api_key: Plain text API key to store
            metadata: Optional metadata (model preferences, etc.)

        Returns:
            Key ID (UUID)

        Raises:
            HTTPException: If storage fails
        """
        try:
            # Encrypt the API key
            encrypted_key = self._encrypt_key(api_key)

            async with self.db_pool.acquire() as conn:
                # Check if key already exists for this provider
                existing = await conn.fetchrow(
                    """
                    SELECT id FROM user_provider_keys
                    WHERE user_id = $1 AND provider = $2
                    """,
                    user_id, provider
                )

                if existing:
                    # Update existing key
                    key_id = await conn.fetchval(
                        """
                        UPDATE user_provider_keys
                        SET api_key_encrypted = $1,
                            metadata = $2,
                            updated_at = NOW()
                        WHERE user_id = $3 AND provider = $4
                        RETURNING id
                        """,
                        encrypted_key,
                        json.dumps(metadata or {}),
                        user_id,
                        provider
                    )
                    logger.info(f"Updated BYOK for {user_id}/{provider}")
                else:
                    # Insert new key
                    key_id = await conn.fetchval(
                        """
                        INSERT INTO user_provider_keys (
                            user_id, provider, api_key_encrypted, metadata, enabled
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                        """,
                        user_id,
                        provider,
                        encrypted_key,
                        json.dumps(metadata or {}),
                        True
                    )
                    logger.info(f"Stored new BYOK for {user_id}/{provider}")

                return str(key_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error storing API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to store API key")

    async def get_user_api_key(
        self,
        user_id: str,
        provider: str
    ) -> Optional[str]:
        """
        Retrieve and decrypt user's API key for a provider

        Args:
            user_id: User identifier
            provider: Provider name

        Returns:
            Decrypted API key or None if not found/disabled

        Raises:
            HTTPException: If decryption fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT api_key_encrypted, enabled
                    FROM user_provider_keys
                    WHERE user_id = $1 AND provider = $2
                    """,
                    user_id, provider
                )

                if not result:
                    return None

                if not result['enabled']:
                    logger.warning(f"BYOK for {user_id}/{provider} is disabled")
                    return None

                # Decrypt and return
                return self._decrypt_key(result['api_key_encrypted'])

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving API key: {e}")
            return None

    async def delete_user_api_key(
        self,
        user_id: str,
        provider: str
    ) -> bool:
        """
        Delete user's API key for a provider

        Args:
            user_id: User identifier
            provider: Provider name

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM user_provider_keys
                    WHERE user_id = $1 AND provider = $2
                    """,
                    user_id, provider
                )

                deleted = result.split()[-1] == '1'
                if deleted:
                    logger.info(f"Deleted BYOK for {user_id}/{provider}")
                return deleted

        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key")

    async def list_user_providers(self, user_id: str) -> List[Dict]:
        """
        List all providers with stored API keys for user

        Args:
            user_id: User identifier

        Returns:
            List of provider info dicts (without API keys)
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        id, provider, enabled, metadata, created_at, updated_at
                    FROM user_provider_keys
                    WHERE user_id = $1
                    ORDER BY provider
                    """,
                    user_id
                )

                return [
                    {
                        'id': str(row['id']),
                        'provider': row['provider'],
                        'enabled': row['enabled'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'created_at': row['created_at'].isoformat(),
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                        'masked_key': self._mask_key(row['provider'])  # Show that key exists
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error listing providers: {e}")
            return []

    async def toggle_provider(
        self,
        user_id: str,
        provider: str,
        enabled: bool
    ) -> bool:
        """
        Enable or disable a provider's API key

        Args:
            user_id: User identifier
            provider: Provider name
            enabled: True to enable, False to disable

        Returns:
            True if updated
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE user_provider_keys
                    SET enabled = $1, updated_at = NOW()
                    WHERE user_id = $2 AND provider = $3
                    """,
                    enabled, user_id, provider
                )

                updated = result.split()[-1] == '1'
                if updated:
                    action = "enabled" if enabled else "disabled"
                    logger.info(f"{action.capitalize()} BYOK for {user_id}/{provider}")
                return updated

        except Exception as e:
            logger.error(f"Error toggling provider: {e}")
            raise HTTPException(status_code=500, detail="Failed to toggle provider")

    async def get_all_user_keys(self, user_id: str) -> Dict[str, str]:
        """
        Get all enabled API keys for user (for routing logic)

        Args:
            user_id: User identifier

        Returns:
            Dict mapping provider -> decrypted API key
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT provider, api_key_encrypted
                    FROM user_provider_keys
                    WHERE user_id = $1 AND enabled = TRUE
                    """,
                    user_id
                )

                keys = {}
                for row in rows:
                    try:
                        keys[row['provider']] = self._decrypt_key(row['api_key_encrypted'])
                    except Exception as e:
                        logger.error(f"Failed to decrypt key for {row['provider']}: {e}")

                return keys

        except Exception as e:
            logger.error(f"Error getting all user keys: {e}")
            return {}

    def _mask_key(self, provider: str) -> str:
        """Return masked key display (e.g., 'sk-...abcd')"""
        return f"***...{provider[:4]}"

    async def validate_api_key(
        self,
        user_id: str,
        provider: str,
        api_key: str
    ) -> bool:
        """
        Validate API key format (basic checks)

        Args:
            user_id: User identifier
            provider: Provider name
            api_key: API key to validate

        Returns:
            True if key appears valid
        """
        # Basic format validation
        if not api_key or len(api_key) < 10:
            return False

        # Provider-specific validation
        validation_rules = {
            'openai': lambda k: k.startswith('sk-') and len(k) > 40,
            'anthropic': lambda k: k.startswith('sk-ant-') and len(k) > 50,
            'openrouter': lambda k: k.startswith('sk-or-') and len(k) > 40,
            'together': lambda k: len(k) > 30,
            'fireworks': lambda k: len(k) > 30,
            'deepinfra': lambda k: len(k) > 30,
            'groq': lambda k: k.startswith('gsk_') and len(k) > 50,
            'huggingface': lambda k: k.startswith('hf_') and len(k) > 30,
        }

        validator = validation_rules.get(provider, lambda k: len(k) > 20)
        return validator(api_key)


# Generate encryption key utility
def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Generate new encryption key
    print("Generated BYOK encryption key:")
    print(generate_encryption_key())
    print("\nAdd this to .env.auth as:")
    print("BYOK_ENCRYPTION_KEY=<key>")
