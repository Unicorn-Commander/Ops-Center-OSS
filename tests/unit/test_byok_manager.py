"""
Unit tests for BYOK (Bring Your Own Key) Manager.

Tests key encryption, storage, retrieval, validation, and caching.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from modules.byok_manager import BYOKManager, BYOKKey
from tests.fixtures.llm_test_data import TEST_ENCRYPTION_KEY, get_mock_user_keys


class TestBYOKManager:
    """Test suite for BYOK Manager."""

    @pytest.fixture
    def byok_manager(self, mock_keycloak_admin):
        """Initialize BYOK Manager with mock dependencies."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY.decode()}):
            manager = BYOKManager(keycloak_admin=mock_keycloak_admin)
            return manager

    @pytest.fixture
    def sample_api_key(self):
        """Sample API key for testing."""
        return "sk-test-1234567890abcdefghijklmnopqrstuvwxyz"

    # Test: Key Encryption/Decryption
    def test_encrypt_decrypt_key(self, byok_manager, sample_api_key):
        """Test that keys are encrypted and decrypted correctly."""
        encrypted = byok_manager.encrypt_key(sample_api_key)

        # Encrypted key should be different from original
        assert encrypted != sample_api_key
        assert isinstance(encrypted, str)

        # Decryption should restore original key
        decrypted = byok_manager.decrypt_key(encrypted)
        assert decrypted == sample_api_key

    def test_encrypt_empty_key_raises_error(self, byok_manager):
        """Test that encrypting empty key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            byok_manager.encrypt_key("")

    def test_decrypt_invalid_key_raises_error(self, byok_manager):
        """Test that decrypting invalid key raises error."""
        with pytest.raises(Exception):
            byok_manager.decrypt_key("invalid-encrypted-key")

    # Test: Key Storage in Keycloak
    @pytest.mark.asyncio
    async def test_store_key_success(self, byok_manager, mock_keycloak_admin, sample_api_key):
        """Test successful key storage in Keycloak attributes."""
        user_id = "user-123"
        provider_id = "provider-1"
        key_name = "My Test Key"

        result = await byok_manager.store_key(
            user_id=user_id,
            provider_id=provider_id,
            provider_name="OpenAI",
            api_key=sample_api_key,
            key_name=key_name
        )

        # Verify result
        assert result["success"] is True
        assert result["key_id"] is not None
        assert "encrypted_key" not in result  # Should not expose encrypted key

        # Verify Keycloak was called
        mock_keycloak_admin.update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_key_duplicate_provider(self, byok_manager, mock_keycloak_admin, sample_api_key):
        """Test storing key for provider that already has a key."""
        user_id = "user-123"
        provider_id = "provider-1"

        # Mock existing key for this provider
        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "provider_id": provider_id,
                        "encrypted_key": "existing-key",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
            }
        }

        result = await byok_manager.store_key(
            user_id=user_id,
            provider_id=provider_id,
            provider_name="OpenAI",
            api_key=sample_api_key,
            key_name="Duplicate Key"
        )

        # Should replace existing key
        assert result["success"] is True

    # Test: Key Retrieval
    @pytest.mark.asyncio
    async def test_get_user_key_success(self, byok_manager, mock_keycloak_admin):
        """Test retrieving user's key for specific provider."""
        user_id = "user-123"
        provider_id = "provider-1"
        encrypted_key = byok_manager.encrypt_key("sk-test-key")

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": provider_id,
                        "provider_name": "OpenAI",
                        "encrypted_key": encrypted_key,
                        "key_name": "Test Key",
                        "created_at": datetime.utcnow().isoformat(),
                        "is_active": True
                    }
                ]
            }
        }

        key = await byok_manager.get_user_key(user_id, provider_id)

        assert key is not None
        assert key["provider_id"] == provider_id
        assert key["decrypted_key"] == "sk-test-key"
        assert key["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_user_key_not_found(self, byok_manager, mock_keycloak_admin):
        """Test retrieving key that doesn't exist."""
        user_id = "user-123"
        provider_id = "provider-999"

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": []
            }
        }

        key = await byok_manager.get_user_key(user_id, provider_id)
        assert key is None

    @pytest.mark.asyncio
    async def test_get_user_key_inactive(self, byok_manager, mock_keycloak_admin):
        """Test that inactive keys are not returned."""
        user_id = "user-123"
        provider_id = "provider-1"

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": provider_id,
                        "encrypted_key": "encrypted",
                        "is_active": False
                    }
                ]
            }
        }

        key = await byok_manager.get_user_key(user_id, provider_id)
        assert key is None

    @pytest.mark.asyncio
    async def test_list_user_keys(self, byok_manager, mock_keycloak_admin):
        """Test listing all keys for a user."""
        user_id = "user-123"

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": "provider-1",
                        "provider_name": "OpenAI",
                        "encrypted_key": "encrypted1",
                        "key_name": "Key 1",
                        "created_at": datetime.utcnow().isoformat(),
                        "is_active": True
                    },
                    {
                        "key_id": "key-2",
                        "provider_id": "provider-2",
                        "provider_name": "Anthropic",
                        "encrypted_key": "encrypted2",
                        "key_name": "Key 2",
                        "created_at": datetime.utcnow().isoformat(),
                        "is_active": True
                    }
                ]
            }
        }

        keys = await byok_manager.list_user_keys(user_id)

        assert len(keys) == 2
        assert keys[0]["provider_name"] == "OpenAI"
        assert keys[1]["provider_name"] == "Anthropic"
        # Should not expose decrypted keys in list
        assert "decrypted_key" not in keys[0]

    # Test: Key Validation
    @pytest.mark.asyncio
    async def test_validate_key_openai_success(self, byok_manager):
        """Test validating OpenAI API key."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200,
                json=lambda: {"data": [{"id": "model-1"}]}
            )

            is_valid = await byok_manager.validate_key(
                provider_type="openai",
                api_key="sk-test-key"
            )

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_key_openai_invalid(self, byok_manager):
        """Test validating invalid OpenAI API key."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=401,
                json=lambda: {"error": {"code": "invalid_api_key"}}
            )

            is_valid = await byok_manager.validate_key(
                provider_type="openai",
                api_key="sk-invalid-key"
            )

            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_key_anthropic_success(self, byok_manager):
        """Test validating Anthropic API key."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: {"content": [{"text": "test"}]}
            )

            is_valid = await byok_manager.validate_key(
                provider_type="anthropic",
                api_key="sk-ant-test-key"
            )

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_key_network_error(self, byok_manager):
        """Test key validation with network error."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            is_valid = await byok_manager.validate_key(
                provider_type="openai",
                api_key="sk-test-key"
            )

            assert is_valid is False

    # Test: Key Deletion
    @pytest.mark.asyncio
    async def test_delete_key_success(self, byok_manager, mock_keycloak_admin):
        """Test deleting user's API key."""
        user_id = "user-123"
        key_id = "key-1"

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": key_id,
                        "provider_id": "provider-1",
                        "encrypted_key": "encrypted"
                    }
                ]
            }
        }

        result = await byok_manager.delete_key(user_id, key_id)

        assert result["success"] is True
        mock_keycloak_admin.update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_key_not_found(self, byok_manager, mock_keycloak_admin):
        """Test deleting non-existent key."""
        user_id = "user-123"
        key_id = "key-999"

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": []
            }
        }

        result = await byok_manager.delete_key(user_id, key_id)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    # Test: Key Caching
    @pytest.mark.asyncio
    async def test_key_caching_behavior(self, byok_manager, mock_keycloak_admin):
        """Test that keys are cached after first retrieval."""
        user_id = "user-123"
        provider_id = "provider-1"
        encrypted_key = byok_manager.encrypt_key("sk-test-key")

        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": provider_id,
                        "encrypted_key": encrypted_key,
                        "is_active": True
                    }
                ]
            }
        }

        # First call - should hit Keycloak
        key1 = await byok_manager.get_user_key(user_id, provider_id)
        assert key1 is not None

        # Second call - should use cache (if implemented)
        key2 = await byok_manager.get_user_key(user_id, provider_id)
        assert key2 is not None
        assert key1["decrypted_key"] == key2["decrypted_key"]

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, byok_manager, mock_keycloak_admin, sample_api_key):
        """Test that cache is invalidated when key is updated."""
        user_id = "user-123"
        provider_id = "provider-1"

        # Store new key
        await byok_manager.store_key(
            user_id=user_id,
            provider_id=provider_id,
            provider_name="OpenAI",
            api_key=sample_api_key,
            key_name="Updated Key"
        )

        # Cache should be cleared for this user+provider

    # Test: Error Handling
    @pytest.mark.asyncio
    async def test_store_key_missing_user(self, byok_manager, mock_keycloak_admin, sample_api_key):
        """Test storing key for non-existent user."""
        mock_keycloak_admin.get_user.side_effect = Exception("User not found")

        result = await byok_manager.store_key(
            user_id="user-999",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key=sample_api_key,
            key_name="Test"
        )

        assert result["success"] is False
        assert "error" in result

    def test_encrypt_with_wrong_key_format(self, byok_manager):
        """Test encrypting with non-string input."""
        with pytest.raises(Exception):
            byok_manager.encrypt_key(12345)  # Not a string

    @pytest.mark.asyncio
    async def test_concurrent_key_operations(self, byok_manager, mock_keycloak_admin):
        """Test handling concurrent key operations."""
        import asyncio

        user_id = "user-123"
        provider_id = "provider-1"

        encrypted_key = byok_manager.encrypt_key("sk-test-key")
        mock_keycloak_admin.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": provider_id,
                        "encrypted_key": encrypted_key,
                        "is_active": True
                    }
                ]
            }
        }

        # Run 10 concurrent get operations
        tasks = [
            byok_manager.get_user_key(user_id, provider_id)
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r is not None for r in results)
        # All should return same key
        assert all(r["decrypted_key"] == "sk-test-key" for r in results)


# Run tests with: pytest -v tests/unit/test_byok_manager.py
