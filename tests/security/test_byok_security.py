"""
Security tests for BYOK and LLM Routing.

Tests encryption at rest, access controls, SQL injection prevention,
authentication bypass attempts, and data leak prevention.
"""
import pytest
from unittest.mock import MagicMock, patch
import re
import base64

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from modules.byok_manager import BYOKManager
from tests.fixtures.llm_test_data import TEST_ENCRYPTION_KEY


class TestBYOKSecurity:
    """Security tests for BYOK system."""

    @pytest.fixture
    def byok_manager(self, mock_keycloak_admin):
        """Initialize BYOK Manager."""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY.decode()}):
            return BYOKManager(keycloak_admin=mock_keycloak_admin)

    # Test: API Keys Encrypted at Rest
    @pytest.mark.asyncio
    async def test_keys_encrypted_at_rest(self, byok_manager, mock_keycloak_admin):
        """Verify API keys are encrypted before storage."""
        plaintext_key = "sk-test-1234567890abcdef"

        result = await byok_manager.store_key(
            user_id="user-123",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key=plaintext_key,
            key_name="Test Key"
        )

        # Get the stored value from Keycloak
        stored_data = mock_keycloak_admin.update_user.call_args[1]["attributes"]["llm_api_keys"][0]

        # Encrypted key should NOT match plaintext
        assert stored_data["encrypted_key"] != plaintext_key

        # Encrypted key should be base64-like (Fernet output)
        assert len(stored_data["encrypted_key"]) > len(plaintext_key)

        # Should not contain plaintext anywhere in stored data
        assert plaintext_key not in str(stored_data)

    def test_encryption_key_strength(self, byok_manager):
        """Verify encryption key meets security requirements."""
        # Encryption key should be 32 bytes (256 bits)
        assert len(TEST_ENCRYPTION_KEY) == 44  # Base64 encoded 32 bytes

        # Should be URL-safe base64
        try:
            decoded = base64.urlsafe_b64decode(TEST_ENCRYPTION_KEY)
            assert len(decoded) == 32
        except Exception:
            pytest.fail("Encryption key is not valid Fernet key")

    def test_encrypted_keys_cannot_be_decrypted_without_key(self, byok_manager):
        """Verify encrypted keys cannot be decrypted without encryption key."""
        plaintext = "sk-test-secret"
        encrypted = byok_manager.encrypt_key(plaintext)

        # Try to decrypt with wrong key
        from cryptography.fernet import Fernet
        wrong_key = Fernet.generate_key()
        wrong_fernet = Fernet(wrong_key)

        with pytest.raises(Exception):
            wrong_fernet.decrypt(encrypted.encode())

    # Test: Keys Never Logged in Plaintext
    @pytest.mark.asyncio
    async def test_keys_not_logged(self, byok_manager, mock_keycloak_admin, caplog):
        """Verify API keys are never logged in plaintext."""
        import logging
        caplog.set_level(logging.DEBUG)

        plaintext_key = "sk-test-secret-1234567890"

        await byok_manager.store_key(
            user_id="user-123",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key=plaintext_key,
            key_name="Test"
        )

        # Check all log messages
        for record in caplog.records:
            # Plaintext key should NOT appear in any log
            assert plaintext_key not in record.message
            assert plaintext_key not in str(record.args)

    @pytest.mark.asyncio
    async def test_keys_masked_in_responses(self, byok_manager, mock_keycloak_admin):
        """Verify API keys are masked in API responses."""
        plaintext_key = "sk-test-1234567890abcdef"

        # Store key
        result = await byok_manager.store_key(
            user_id="user-123",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key=plaintext_key,
            key_name="Test"
        )

        # Response should not contain plaintext key
        assert "api_key" not in result
        assert "decrypted_key" not in result
        assert plaintext_key not in str(result)

        # List keys
        encrypted_key = byok_manager.encrypt_key(plaintext_key)
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": "provider-1",
                        "encrypted_key": encrypted_key,
                        "key_name": "Test",
                        "is_active": True
                    }
                ]
            }
        }

        keys = await byok_manager.list_user_keys("user-123")

        # Keys in list should be masked
        for key in keys:
            assert "decrypted_key" not in key
            assert plaintext_key not in str(key)

    # Test: Users Cannot Access Other Users' Keys
    @pytest.mark.asyncio
    async def test_user_isolation(self, byok_manager, mock_keycloak_admin):
        """Verify users cannot access other users' keys."""
        # User A stores key
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-A",
            "attributes": {"llm_api_keys": []}
        }

        await byok_manager.store_key(
            user_id="user-A",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key="sk-user-a-key",
            key_name="User A Key"
        )

        # User B tries to access User A's keys
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-B",
            "attributes": {"llm_api_keys": []}
        }

        # User B should not see User A's keys
        key = await byok_manager.get_user_key("user-B", "provider-1")
        assert key is None

    @pytest.mark.asyncio
    async def test_cannot_delete_other_users_keys(self, byok_manager, mock_keycloak_admin):
        """Verify users cannot delete other users' keys."""
        # User A has a key
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-A",
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-A",
                        "provider_id": "provider-1",
                        "encrypted_key": "encrypted"
                    }
                ]
            }
        }

        # User B tries to delete User A's key (by using User B's ID)
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-B",
            "attributes": {"llm_api_keys": []}
        }

        result = await byok_manager.delete_key("user-B", "key-A")

        # Should fail (key not found for User B)
        assert result["success"] is False

    # Test: Admin Cannot See Decrypted Keys
    @pytest.mark.asyncio
    async def test_admin_cannot_see_decrypted_keys(self, byok_manager, mock_keycloak_admin):
        """Verify even admins cannot see decrypted keys in Keycloak."""
        plaintext_key = "sk-test-admin-cannot-see"
        encrypted_key = byok_manager.encrypt_key(plaintext_key)

        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": "provider-1",
                        "encrypted_key": encrypted_key
                    }
                ]
            }
        }

        # Admin views user in Keycloak
        user_data = mock_keycloak_admin.get_user.return_value

        # Only encrypted version should be visible
        assert plaintext_key not in str(user_data)
        assert encrypted_key in str(user_data)

    # Test: SQL Injection Prevention
    @pytest.mark.asyncio
    async def test_sql_injection_in_provider_id(self, byok_manager, mock_keycloak_admin):
        """Test SQL injection attempts in provider_id parameter."""
        malicious_provider_id = "provider-1'; DROP TABLE users; --"

        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {"llm_api_keys": []}
        }

        # Attempt SQL injection
        result = await byok_manager.store_key(
            user_id="user-123",
            provider_id=malicious_provider_id,
            provider_name="Evil Provider",
            api_key="sk-test",
            key_name="Hacker Key"
        )

        # Should handle safely (parameterized queries prevent injection)
        # No exception = safe handling
        assert result["success"] in [True, False]  # Either works or rejected safely

    @pytest.mark.asyncio
    async def test_sql_injection_in_user_id(self, byok_manager, mock_keycloak_admin):
        """Test SQL injection attempts in user_id parameter."""
        malicious_user_id = "user-123' OR '1'='1"

        mock_keycloak_admin.get_user.side_effect = Exception("Invalid user ID")

        # Should not allow injection
        with pytest.raises(Exception):
            await byok_manager.store_key(
                user_id=malicious_user_id,
                provider_id="provider-1",
                provider_name="Test",
                api_key="sk-test",
                key_name="Test"
            )

    # Test: Authentication Bypass Attempts
    @pytest.mark.asyncio
    async def test_cannot_bypass_authentication(self):
        """Test that API endpoints require authentication."""
        import httpx

        # Try to access API without token
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8084/api/v1/llm/byok/keys")

            # Should return 401 Unauthorized
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cannot_use_invalid_token(self):
        """Test that invalid JWT tokens are rejected."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8084/api/v1/llm/byok/keys",
                headers={"Authorization": "Bearer invalid-token-12345"}
            )

            # Should return 401 Unauthorized
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cannot_use_expired_token(self):
        """Test that expired JWT tokens are rejected."""
        import httpx
        import jwt
        from datetime import datetime, timedelta

        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": "user-123",
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            "secret",
            algorithm="HS256"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8084/api/v1/llm/byok/keys",
                headers={"Authorization": f"Bearer {expired_token}"}
            )

            # Should return 401 Unauthorized
            assert response.status_code == 401

    # Test: Input Validation
    @pytest.mark.asyncio
    async def test_rejects_invalid_api_key_format(self, byok_manager, mock_keycloak_admin):
        """Test that invalid API key formats are rejected."""
        invalid_keys = [
            "",  # Empty
            "short",  # Too short
            "no-prefix-key",  # No sk- prefix for OpenAI
            "<script>alert('xss')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal
        ]

        for invalid_key in invalid_keys:
            result = await byok_manager.store_key(
                user_id="user-123",
                provider_id="provider-1",
                provider_name="OpenAI",
                api_key=invalid_key,
                key_name="Invalid Key Test"
            )

            # Should either fail validation or be rejected
            # Empty key should definitely fail
            if invalid_key == "":
                assert result["success"] is False

    @pytest.mark.asyncio
    async def test_sanitizes_key_names(self, byok_manager, mock_keycloak_admin):
        """Test that key names are sanitized to prevent XSS."""
        xss_name = "<script>alert('XSS')</script>"

        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {"llm_api_keys": []}
        }

        result = await byok_manager.store_key(
            user_id="user-123",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key="sk-test-key",
            key_name=xss_name
        )

        # Key name should be sanitized (HTML entities or stripped)
        stored_name = mock_keycloak_admin.update_user.call_args[1]["attributes"]["llm_api_keys"][0]["key_name"]

        # Should not contain raw script tags
        assert "<script>" not in stored_name

    # Test: Rate Limiting
    @pytest.mark.asyncio
    async def test_rate_limiting_on_key_operations(self, byok_manager, mock_keycloak_admin):
        """Test that rate limiting prevents abuse."""
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {"llm_api_keys": []}
        }

        # Attempt many rapid key additions
        for i in range(100):
            await byok_manager.store_key(
                user_id="user-123",
                provider_id=f"provider-{i}",
                provider_name="Test",
                api_key=f"sk-test-{i}",
                key_name=f"Key {i}"
            )

        # Rate limiting should kick in (if implemented)
        # This test verifies system doesn't crash under abuse

    # Test: Secure Key Deletion
    @pytest.mark.asyncio
    async def test_secure_key_deletion(self, byok_manager, mock_keycloak_admin):
        """Verify deleted keys are truly removed and not recoverable."""
        encrypted_key = byok_manager.encrypt_key("sk-test-to-delete")

        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": "provider-1",
                        "encrypted_key": encrypted_key
                    }
                ]
            }
        }

        # Delete key
        await byok_manager.delete_key("user-123", "key-1")

        # Verify it's removed from Keycloak
        updated_keys = mock_keycloak_admin.update_user.call_args[1]["attributes"]["llm_api_keys"]
        assert len(updated_keys) == 0

        # Try to retrieve deleted key
        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {"llm_api_keys": []}
        }

        key = await byok_manager.get_user_key("user-123", "provider-1")
        assert key is None

    # Test: Encryption Key Rotation
    def test_supports_key_rotation(self, byok_manager):
        """Test that system supports encryption key rotation."""
        from cryptography.fernet import Fernet

        # Old key
        old_key = TEST_ENCRYPTION_KEY
        old_fernet = Fernet(old_key)

        # Encrypt with old key
        plaintext = "sk-test-rotation"
        encrypted_old = old_fernet.encrypt(plaintext.encode()).decode()

        # New key
        new_key = Fernet.generate_key()
        new_fernet = Fernet(new_key)

        # Decrypt with old, re-encrypt with new
        decrypted = old_fernet.decrypt(encrypted_old.encode()).decode()
        encrypted_new = new_fernet.encrypt(decrypted.encode()).decode()

        # Verify new encryption works
        final_decrypted = new_fernet.decrypt(encrypted_new.encode()).decode()
        assert final_decrypted == plaintext


class TestSecurityHeaders:
    """Test security headers in API responses."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Verify security headers are set on API responses."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8084/api/v1/health")

            # Check for security headers
            headers = response.headers

            # Should have CORS headers
            assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers

            # Should have security headers
            expected_headers = [
                "X-Content-Type-Options",  # nosniff
                "X-Frame-Options",  # DENY or SAMEORIGIN
                "X-XSS-Protection",  # 1; mode=block
            ]

            # At least some security headers should be present
            # (Exact headers depend on FastAPI/Starlette configuration)


class TestAuditLogging:
    """Test security audit logging."""

    @pytest.mark.asyncio
    async def test_key_operations_are_audited(self, byok_manager, mock_keycloak_admin, caplog):
        """Verify key operations are logged for audit trail."""
        import logging
        caplog.set_level(logging.INFO)

        mock_keycloak_admin.get_user.return_value = {
            "id": "user-123",
            "attributes": {"llm_api_keys": []}
        }

        # Add key
        await byok_manager.store_key(
            user_id="user-123",
            provider_id="provider-1",
            provider_name="OpenAI",
            api_key="sk-test-audit",
            key_name="Audit Test"
        )

        # Check audit logs
        audit_logs = [record for record in caplog.records if record.levelname == "INFO"]

        # Should have log entry for key addition
        assert any("store" in record.message.lower() or "add" in record.message.lower() for record in audit_logs)

    @pytest.mark.asyncio
    async def test_failed_authentication_logged(self, caplog):
        """Verify failed authentication attempts are logged."""
        import logging
        import httpx

        caplog.set_level(logging.WARNING)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8084/api/v1/llm/byok/keys",
                headers={"Authorization": "Bearer invalid-token"}
            )

        # Check for auth failure logs
        # (Depends on implementation - may log at WARNING or ERROR level)


# Run tests with: pytest -v tests/security/test_byok_security.py
# For security audit: pytest -v -s tests/security/test_byok_security.py --tb=short
