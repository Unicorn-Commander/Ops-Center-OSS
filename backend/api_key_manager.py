"""
API Key Management for External Application Authentication

This module integrates auth_manager.py with Ops-Center's PostgreSQL database
to provide API key authentication for external applications accessing LLM endpoints.

Author: Claude Code
Date: October 28, 2025
"""

import os
import asyncio
import secrets
import bcrypt
import jwt
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncpg
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """
    Manages API keys for external application authentication.

    Features:
    - Generate secure API keys (Bearer tokens)
    - Store hashed keys in PostgreSQL
    - Validate API keys for requests
    - Support key expiration
    - Track key usage
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", self._generate_secret())
        self.jwt_algorithm = "HS256"
        self.default_expiry_days = 90  # API keys expire after 90 days

    def _generate_secret(self) -> str:
        """Generate a secure random secret for JWT signing"""
        return secrets.token_urlsafe(64)

    async def initialize_table(self):
        """Create user_api_keys table if it doesn't exist"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    key_name VARCHAR(255) NOT NULL,
                    key_hash TEXT NOT NULL,
                    key_prefix VARCHAR(20) NOT NULL,
                    permissions JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}'::jsonb
                );

                CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id
                    ON user_api_keys(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_api_keys_prefix
                    ON user_api_keys(key_prefix);
                CREATE INDEX IF NOT EXISTS idx_user_api_keys_active
                    ON user_api_keys(is_active, expires_at);
            """)
            logger.info("user_api_keys table initialized")

    def _generate_api_key(self) -> Tuple[str, str]:
        """
        Generate a secure API key and its prefix

        Returns:
            Tuple of (full_key, prefix)
            Example: ("uc_1234567890abcdef...", "uc_1234")
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(32)
        key_hex = random_bytes.hex()

        # Format: uc_<64-char-hex>
        full_key = f"uc_{key_hex}"
        prefix = full_key[:7]  # "uc_1234"

        return full_key, prefix

    def _hash_key(self, api_key: str) -> str:
        """Hash API key with bcrypt"""
        return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

    def _verify_key(self, api_key: str, key_hash: str) -> bool:
        """Verify API key against stored hash"""
        try:
            return bcrypt.checkpw(api_key.encode(), key_hash.encode())
        except Exception as e:
            logger.error(f"Key verification error: {e}")
            return False

    async def create_api_key(
        self,
        user_id: str,
        key_name: str,
        expires_in_days: Optional[int] = None,
        permissions: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new API key for a user

        Args:
            user_id: User identifier (email or Keycloak ID)
            key_name: Descriptive name for the key
            expires_in_days: Days until expiration (default: 90)
            permissions: List of permissions (default: all)

        Returns:
            Dict with 'api_key' (show once), 'key_id', 'key_prefix', 'expires_at'
        """
        # Generate key
        api_key, prefix = self._generate_api_key()
        key_hash = self._hash_key(api_key)

        # Calculate expiration
        expires_in_days = expires_in_days or self.default_expiry_days
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Default permissions
        if permissions is None:
            permissions = ["llm:inference", "llm:models"]

        # Store in database (convert permissions list to JSON)
        import json as json_lib
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO user_api_keys (
                    user_id, key_name, key_hash, key_prefix,
                    permissions, expires_at
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                RETURNING id, created_at
            """, user_id, key_name, key_hash, prefix, json_lib.dumps(permissions), expires_at)

        logger.info(f"Created API key '{key_name}' for user {user_id}")

        return {
            "api_key": api_key,  # Show ONLY ONCE
            "key_id": str(result['id']),
            "key_name": key_name,
            "key_prefix": prefix,
            "permissions": permissions,
            "created_at": result['created_at'].isoformat(),
            "expires_at": expires_at.isoformat(),
            "warning": "Save this API key now. You won't be able to see it again."
        }

    async def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate an API key and return user information

        Args:
            api_key: API key to validate

        Returns:
            User dict with 'user_id', 'permissions' if valid, None otherwise
        """
        if not api_key or not api_key.startswith("uc_"):
            return None

        # Get prefix for faster lookup
        prefix = api_key[:7]

        async with self.db_pool.acquire() as conn:
            # Find active keys with matching prefix
            keys = await conn.fetch("""
                SELECT id, user_id, key_hash, permissions, expires_at
                FROM user_api_keys
                WHERE key_prefix = $1
                  AND is_active = TRUE
                  AND (expires_at IS NULL OR expires_at > NOW())
            """, prefix)

            # Try to match hash (bcrypt is slow, so we limit candidates by prefix)
            for key_record in keys:
                if self._verify_key(api_key, key_record['key_hash']):
                    # Update last_used
                    await conn.execute("""
                        UPDATE user_api_keys
                        SET last_used = NOW()
                        WHERE id = $1
                    """, key_record['id'])

                    logger.debug(f"API key validated for user {key_record['user_id']}")

                    return {
                        "user_id": key_record['user_id'],
                        "permissions": key_record['permissions'],
                        "key_id": str(key_record['id'])
                    }

        logger.warning(f"Invalid API key attempt: {prefix}...")
        return None

    async def list_user_keys(self, user_id: str) -> List[Dict]:
        """
        List all API keys for a user (without showing the actual keys)

        Args:
            user_id: User identifier

        Returns:
            List of key info dicts
        """
        async with self.db_pool.acquire() as conn:
            keys = await conn.fetch("""
                SELECT id, key_name, key_prefix, permissions,
                       created_at, last_used, expires_at, is_active
                FROM user_api_keys
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, user_id)

            return [
                {
                    "key_id": str(k['id']),
                    "key_name": k['key_name'],
                    "key_prefix": k['key_prefix'],
                    "permissions": k['permissions'],
                    "created_at": k['created_at'].isoformat(),
                    "last_used": k['last_used'].isoformat() if k['last_used'] else None,
                    "expires_at": k['expires_at'].isoformat() if k['expires_at'] else None,
                    "is_active": k['is_active'],
                    "status": self._get_key_status(k)
                }
                for k in keys
            ]

    def _get_key_status(self, key_record) -> str:
        """Determine key status"""
        if not key_record['is_active']:
            return "revoked"
        if key_record['expires_at'] and key_record['expires_at'] < datetime.utcnow():
            return "expired"
        return "active"

    async def revoke_key(self, user_id: str, key_id: str) -> bool:
        """
        Revoke an API key

        Args:
            user_id: User identifier (for authorization)
            key_id: Key UUID to revoke

        Returns:
            True if revoked, False if not found
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE user_api_keys
                SET is_active = FALSE
                WHERE id = $1 AND user_id = $2
            """, key_id, user_id)

            if result == "UPDATE 1":
                logger.info(f"Revoked API key {key_id} for user {user_id}")
                return True
            return False

    async def revoke_all_user_keys(self, user_id: str) -> int:
        """
        Revoke all API keys for a user

        Args:
            user_id: User identifier

        Returns:
            Number of keys revoked
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE user_api_keys
                SET is_active = FALSE
                WHERE user_id = $1 AND is_active = TRUE
            """, user_id)

            count = int(result.split()[-1])
            logger.info(f"Revoked {count} API keys for user {user_id}")
            return count

    def create_jwt_token(self, user_id: str, permissions: List[str]) -> str:
        """
        Create a JWT token for API key authentication

        Args:
            user_id: User identifier
            permissions: List of permissions

        Returns:
            JWT token string
        """
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "api_key"
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Validate a JWT token

        Args:
            token: JWT token string

        Returns:
            Payload dict if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.warning(f"JWT validation error: {e}")
            return None


# Global instance (initialized by server.py)
api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance"""
    global api_key_manager
    if api_key_manager is None:
        raise RuntimeError("APIKeyManager not initialized. Call initialize_api_key_manager() first.")
    return api_key_manager


async def initialize_api_key_manager(db_pool: asyncpg.Pool):
    """Initialize global API key manager"""
    global api_key_manager
    api_key_manager = APIKeyManager(db_pool)
    await api_key_manager.initialize_table()
    logger.info("API Key Manager initialized")
