"""
System Settings Manager

Manages system configuration settings stored in database with encryption.
Provides secure storage for environment variables that can be managed via GUI.

Features:
- Encrypted storage of sensitive values (API keys, passwords)
- Redis caching with 2-minute TTL for performance
- Event emission for hot-reload when settings change
- Audit logging for all changes
- Category-based organization
- Type validation

Author: Backend API Developer
Date: October 20, 2025
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timedelta
from enum import Enum

import asyncpg
import aioredis
from cryptography.fernet import Fernet
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# Enums for type safety
class SettingCategory(str, Enum):
    """Setting categories for organization"""
    SECURITY = "security"
    LLM = "llm"
    BILLING = "billing"
    EMAIL = "email"
    STORAGE = "storage"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    SYSTEM = "system"


class ValueType(str, Enum):
    """Value types for validation"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    JSON = "json"


# Pydantic models
class SystemSetting(BaseModel):
    """System setting model"""
    key: str
    value: Optional[str] = None  # Decrypted value (only if user has permission)
    encrypted_value: Optional[str] = None  # Encrypted value (admin only)
    category: SettingCategory
    description: Optional[str] = None
    is_sensitive: bool = False
    value_type: ValueType = ValueType.STRING
    is_required: bool = False
    is_editable: bool = True
    default_value: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        use_enum_values = True


class SettingCreate(BaseModel):
    """Create new setting"""
    key: str = Field(..., min_length=1, max_length=255)
    value: str
    category: SettingCategory
    description: Optional[str] = None
    is_sensitive: bool = False
    value_type: ValueType = ValueType.STRING
    is_required: bool = False
    is_editable: bool = True
    default_value: Optional[str] = None


class SettingUpdate(BaseModel):
    """Update existing setting"""
    value: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None
    value_type: Optional[ValueType] = None
    is_required: Optional[bool] = None
    is_editable: Optional[bool] = None
    default_value: Optional[str] = None


class SettingAuditLog(BaseModel):
    """Audit log entry for setting changes"""
    id: int
    setting_key: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: str
    changed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SystemSettingsManager:
    """Manage system settings with encryption and caching"""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: aioredis.Redis,
        encryption_key: Optional[str] = None
    ):
        """
        Initialize System Settings Manager

        Args:
            db_pool: PostgreSQL connection pool
            redis_client: Redis client for caching
            encryption_key: Base64-encoded Fernet key (generated if not provided)
        """
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.cache_ttl = 120  # 2 minutes

        # Get or generate encryption key
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # Try to get from environment
            env_key = os.getenv('SYSTEM_SETTINGS_ENCRYPTION_KEY')
            if env_key:
                self.encryption_key = env_key.encode()
            else:
                # Try BYOK key as fallback
                byok_key = os.getenv('BYOK_ENCRYPTION_KEY')
                if byok_key:
                    logger.info("Using BYOK_ENCRYPTION_KEY for system settings")
                    self.encryption_key = byok_key.encode()
                else:
                    # Generate new key (WARNING: will lose access to existing settings!)
                    logger.warning("No encryption key found, generating new key")
                    self.encryption_key = Fernet.generate_key()
                    logger.warning(f"Generated encryption key: {self.encryption_key.decode()}")
                    logger.warning("Add this to .env.auth as SYSTEM_SETTINGS_ENCRYPTION_KEY to persist")

        # Initialize Fernet cipher
        try:
            self.cipher = Fernet(self.encryption_key)
            logger.info("System Settings Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key")

    def _encrypt_value(self, value: str) -> str:
        """Encrypt setting value"""
        try:
            encrypted = self.cipher.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to encrypt value")

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt setting value"""
        try:
            if not encrypted_value:
                return ""
            decrypted = self.cipher.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to decrypt value")

    def _get_cache_key(self, key: str) -> str:
        """Get Redis cache key for setting"""
        return f"system_setting:{key}"

    def _get_list_cache_key(self, category: Optional[str] = None) -> str:
        """Get Redis cache key for settings list"""
        if category:
            return f"system_settings:category:{category}"
        return "system_settings:all"

    async def _invalidate_cache(self, key: Optional[str] = None):
        """Invalidate cache for setting or all settings"""
        try:
            if key:
                # Invalidate specific setting
                await self.redis_client.delete(self._get_cache_key(key))

            # Invalidate all list caches
            await self.redis_client.delete(self._get_list_cache_key())
            for category in SettingCategory:
                await self.redis_client.delete(self._get_list_cache_key(category.value))

            logger.info(f"Cache invalidated for: {key or 'all settings'}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

    async def _emit_change_event(self, key: str, action: str):
        """Emit event when setting changes (for hot-reload)"""
        try:
            event = {
                "type": "setting_changed",
                "key": key,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
            # Publish to Redis pub/sub for real-time updates
            await self.redis_client.publish("system_settings_changes", json.dumps(event))
            logger.info(f"Emitted change event for {key}: {action}")
        except Exception as e:
            logger.warning(f"Failed to emit change event: {e}")

    async def _log_audit(
        self,
        key: str,
        action: str,
        old_value: Optional[str],
        new_value: Optional[str],
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log setting change to audit table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO system_settings_audit (
                        setting_key, action, old_value, new_value,
                        changed_by, ip_address, user_agent
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    key, action, old_value, new_value,
                    user_id, ip_address, user_agent
                )
            logger.info(f"Audit logged: {action} on {key} by {user_id}")
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")

    def _mask_sensitive_value(self, value: str, show_chars: int = 8) -> str:
        """Mask sensitive value, showing only last N characters"""
        if len(value) <= show_chars:
            return "*" * len(value)
        return "*" * (len(value) - show_chars) + value[-show_chars:]

    async def get_setting(
        self,
        key: str,
        decrypt: bool = True,
        mask_sensitive: bool = False
    ) -> Optional[SystemSetting]:
        """
        Get setting by key

        Args:
            key: Setting key
            decrypt: Whether to decrypt the value
            mask_sensitive: Whether to mask sensitive values (only last 8 chars shown)

        Returns:
            SystemSetting or None if not found
        """
        # Try cache first
        cache_key = self._get_cache_key(key)
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return SystemSetting(**data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        # Query database
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT key, encrypted_value, category, description,
                           is_sensitive, value_type, is_required, is_editable,
                           default_value, created_at, updated_at, updated_by
                    FROM system_settings
                    WHERE key = $1
                    """,
                    key
                )

                if not row:
                    return None

                # Decrypt value if requested
                value = None
                if decrypt:
                    value = self._decrypt_value(row['encrypted_value'])

                    # Mask sensitive values if requested
                    if mask_sensitive and row['is_sensitive']:
                        value = self._mask_sensitive_value(value)

                setting = SystemSetting(
                    key=row['key'],
                    value=value,
                    encrypted_value=row['encrypted_value'] if not decrypt else None,
                    category=row['category'],
                    description=row['description'],
                    is_sensitive=row['is_sensitive'],
                    value_type=row['value_type'],
                    is_required=row['is_required'],
                    is_editable=row['is_editable'],
                    default_value=row['default_value'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    updated_by=row['updated_by']
                )

                # Cache the result
                try:
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(setting.dict(), default=str)
                    )
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

                return setting

        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve setting: {str(e)}")

    async def list_settings(
        self,
        category: Optional[SettingCategory] = None,
        include_sensitive: bool = True,
        decrypt: bool = True,
        mask_sensitive: bool = True
    ) -> List[SystemSetting]:
        """
        List all settings, optionally filtered by category

        Args:
            category: Filter by category (optional)
            include_sensitive: Whether to include sensitive settings
            decrypt: Whether to decrypt values
            mask_sensitive: Whether to mask sensitive values

        Returns:
            List of SystemSetting objects
        """
        # Try cache first
        cache_key = self._get_list_cache_key(category.value if category else None)
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return [SystemSetting(**item) for item in data]
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        # Query database
        try:
            async with self.db_pool.acquire() as conn:
                if category:
                    query = """
                        SELECT key, encrypted_value, category, description,
                               is_sensitive, value_type, is_required, is_editable,
                               default_value, created_at, updated_at, updated_by
                        FROM system_settings
                        WHERE category = $1
                        ORDER BY key
                    """
                    rows = await conn.fetch(query, category.value)
                else:
                    query = """
                        SELECT key, encrypted_value, category, description,
                               is_sensitive, value_type, is_required, is_editable,
                               default_value, created_at, updated_at, updated_by
                        FROM system_settings
                        ORDER BY category, key
                    """
                    rows = await conn.fetch(query)

                settings = []
                for row in rows:
                    # Skip sensitive settings if not requested
                    if not include_sensitive and row['is_sensitive']:
                        continue

                    # Decrypt value if requested
                    value = None
                    if decrypt:
                        value = self._decrypt_value(row['encrypted_value'])

                        # Mask sensitive values if requested
                        if mask_sensitive and row['is_sensitive']:
                            value = self._mask_sensitive_value(value)

                    setting = SystemSetting(
                        key=row['key'],
                        value=value,
                        encrypted_value=row['encrypted_value'] if not decrypt else None,
                        category=row['category'],
                        description=row['description'],
                        is_sensitive=row['is_sensitive'],
                        value_type=row['value_type'],
                        is_required=row['is_required'],
                        is_editable=row['is_editable'],
                        default_value=row['default_value'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        updated_by=row['updated_by']
                    )
                    settings.append(setting)

                # Cache the result
                try:
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps([s.dict() for s in settings], default=str)
                    )
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

                return settings

        except Exception as e:
            logger.error(f"Failed to list settings: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list settings: {str(e)}")

    async def set_setting(
        self,
        key: str,
        value: str,
        user_id: str,
        category: Optional[SettingCategory] = None,
        description: Optional[str] = None,
        is_sensitive: bool = False,
        value_type: ValueType = ValueType.STRING,
        is_required: bool = False,
        is_editable: bool = True,
        default_value: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemSetting:
        """
        Create or update a setting

        Args:
            key: Setting key
            value: Setting value (will be encrypted)
            user_id: User making the change
            category: Setting category (required for new settings)
            description: Human-readable description
            is_sensitive: Whether this is a sensitive value
            value_type: Value type for validation
            is_required: Whether this setting is required
            is_editable: Whether this setting is editable
            default_value: Default value for documentation
            ip_address: IP address of user
            user_agent: User agent of user

        Returns:
            Created/updated SystemSetting
        """
        try:
            # Encrypt the value
            encrypted_value = self._encrypt_value(value)

            async with self.db_pool.acquire() as conn:
                # Check if setting exists
                existing = await conn.fetchrow(
                    "SELECT encrypted_value, is_editable FROM system_settings WHERE key = $1",
                    key
                )

                if existing:
                    # Check if editable
                    if not existing['is_editable']:
                        raise HTTPException(
                            status_code=403,
                            detail=f"Setting '{key}' is read-only and cannot be modified"
                        )

                    # Update existing setting
                    old_value = existing['encrypted_value']

                    row = await conn.fetchrow(
                        """
                        UPDATE system_settings
                        SET encrypted_value = $1,
                            description = COALESCE($2, description),
                            is_sensitive = COALESCE($3, is_sensitive),
                            value_type = COALESCE($4, value_type),
                            is_required = COALESCE($5, is_required),
                            default_value = COALESCE($6, default_value),
                            updated_by = $7,
                            updated_at = NOW()
                        WHERE key = $8
                        RETURNING key, encrypted_value, category, description,
                                  is_sensitive, value_type, is_required, is_editable,
                                  default_value, created_at, updated_at, updated_by
                        """,
                        encrypted_value, description, is_sensitive, value_type.value if value_type else None,
                        is_required, default_value, user_id, key
                    )

                    # Log audit
                    await self._log_audit(
                        key, "UPDATE", old_value, encrypted_value,
                        user_id, ip_address, user_agent
                    )

                    action = "updated"

                else:
                    # Insert new setting
                    if not category:
                        raise HTTPException(
                            status_code=400,
                            detail="Category is required for new settings"
                        )

                    row = await conn.fetchrow(
                        """
                        INSERT INTO system_settings (
                            key, encrypted_value, category, description,
                            is_sensitive, value_type, is_required, is_editable,
                            default_value, updated_by
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING key, encrypted_value, category, description,
                                  is_sensitive, value_type, is_required, is_editable,
                                  default_value, created_at, updated_at, updated_by
                        """,
                        key, encrypted_value, category.value, description,
                        is_sensitive, value_type.value, is_required, is_editable,
                        default_value, user_id
                    )

                    # Log audit
                    await self._log_audit(
                        key, "CREATE", None, encrypted_value,
                        user_id, ip_address, user_agent
                    )

                    action = "created"

                # Invalidate cache
                await self._invalidate_cache(key)

                # Emit change event
                await self._emit_change_event(key, action)

                # Return decrypted setting
                setting = SystemSetting(
                    key=row['key'],
                    value=value,  # Return decrypted value
                    category=row['category'],
                    description=row['description'],
                    is_sensitive=row['is_sensitive'],
                    value_type=row['value_type'],
                    is_required=row['is_required'],
                    is_editable=row['is_editable'],
                    default_value=row['default_value'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    updated_by=row['updated_by']
                )

                logger.info(f"Setting {key} {action} by {user_id}")
                return setting

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to set setting: {str(e)}")

    async def delete_setting(
        self,
        key: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Delete a setting

        Args:
            key: Setting key
            user_id: User making the change
            ip_address: IP address of user
            user_agent: User agent of user

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check if setting exists and is editable
                existing = await conn.fetchrow(
                    "SELECT encrypted_value, is_editable, is_required FROM system_settings WHERE key = $1",
                    key
                )

                if not existing:
                    return False

                if not existing['is_editable']:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Setting '{key}' is read-only and cannot be deleted"
                    )

                if existing['is_required']:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Setting '{key}' is required and cannot be deleted"
                    )

                # Delete the setting
                await conn.execute(
                    "DELETE FROM system_settings WHERE key = $1",
                    key
                )

                # Log audit
                await self._log_audit(
                    key, "DELETE", existing['encrypted_value'], None,
                    user_id, ip_address, user_agent
                )

                # Invalidate cache
                await self._invalidate_cache(key)

                # Emit change event
                await self._emit_change_event(key, "deleted")

                logger.info(f"Setting {key} deleted by {user_id}")
                return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete setting {key}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete setting: {str(e)}")

    async def get_audit_log(
        self,
        key: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SettingAuditLog]:
        """
        Get audit log for settings changes

        Args:
            key: Filter by setting key (optional)
            limit: Maximum number of entries to return
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        try:
            async with self.db_pool.acquire() as conn:
                if key:
                    query = """
                        SELECT id, setting_key, action, old_value, new_value,
                               changed_by, changed_at, ip_address, user_agent
                        FROM system_settings_audit
                        WHERE setting_key = $1
                        ORDER BY changed_at DESC
                        LIMIT $2 OFFSET $3
                    """
                    rows = await conn.fetch(query, key, limit, offset)
                else:
                    query = """
                        SELECT id, setting_key, action, old_value, new_value,
                               changed_by, changed_at, ip_address, user_agent
                        FROM system_settings_audit
                        ORDER BY changed_at DESC
                        LIMIT $1 OFFSET $2
                    """
                    rows = await conn.fetch(query, limit, offset)

                return [SettingAuditLog(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")
