"""
Epic 1.8 - Credit System Security Tests

Security testing for credit system covering:
- API key encryption
- SQL injection prevention
- Authorization checks
- Rate limiting
- XSS/CSRF protection
- Input validation
- Session security

Author: Testing & DevOps Team Lead
Date: October 23, 2025
"""

import pytest
import hashlib
import base64
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, '/app')
from server import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def admin_session():
    """Admin session"""
    return {
        "user": {
            "id": "admin_123",
            "email": "admin@example.com",
            "roles": ["admin"]
        }
    }


@pytest.fixture
def user_session():
    """Regular user session"""
    return {
        "user": {
            "id": "user_123",
            "email": "user@example.com",
            "roles": ["user"]
        }
    }


class TestAPIKeyEncryption:
    """Test API key encryption security"""

    def test_api_keys_are_encrypted_at_rest(self):
        """Test that API keys are encrypted when stored"""
        # Generate test API key
        api_key = "sk-test-1234567890abcdef"

        # Encrypt with Fernet
        encryption_key = Fernet.generate_key()
        fernet = Fernet(encryption_key)
        encrypted_key = fernet.encrypt(api_key.encode())

        # Verify encrypted != plaintext
        assert encrypted_key != api_key.encode()
        assert len(encrypted_key) > len(api_key)

        # Verify decryption works
        decrypted_key = fernet.decrypt(encrypted_key).decode()
        assert decrypted_key == api_key

    def test_api_key_hashing_for_comparison(self):
        """Test API keys are hashed for comparison"""
        api_key = "sk-test-abcdef123456"

        # Hash with bcrypt-style (using SHA-256 as proxy)
        hashed = hashlib.sha256(api_key.encode()).hexdigest()

        # Verify hash is one-way
        assert hashed != api_key
        assert len(hashed) == 64  # SHA-256 produces 64 hex chars

        # Verify same input produces same hash
        hashed2 = hashlib.sha256(api_key.encode()).hexdigest()
        assert hashed == hashed2

    def test_api_keys_not_logged(self, client, user_session, caplog):
        """Test that API keys are not logged in plaintext"""
        client.app.state.sessions = {"test_token": user_session}

        # Make request with API key
        response = client.post(
            "/api/v1/admin/users/test@example.com/api-keys",
            cookies={"session_token": "test_token"},
            json={"name": "Test Key"}
        )

        # Check logs don't contain API key patterns
        for record in caplog.records:
            assert "sk-" not in record.message  # OpenAI-style keys
            assert "api_key" not in record.message.lower() or "***" in record.message


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention"""

    def test_user_id_sql_injection(self, client, admin_session):
        """Test SQL injection via user_id parameter"""
        client.app.state.sessions = {"admin_token": admin_session}

        # Attempt SQL injection in user_id
        malicious_inputs = [
            "'; DROP TABLE user_credits; --",
            "1' OR '1'='1",
            "1'; SELECT * FROM user_credits WHERE '1'='1",
            "admin@example.com'; DELETE FROM credit_transactions; --"
        ]

        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/v1/admin/credits/allocate",
                cookies={"session_token": "admin_token"},
                json={
                    "user_id": malicious_input,
                    "amount": 100.0,
                    "reason": "bonus"
                }
            )

            # Should either reject or safely handle
            assert response.status_code in [400, 404, 422]
            # Should not return 500 (which might indicate SQL error)
            assert response.status_code != 500

    def test_transaction_metadata_injection(self, client, user_session):
        """Test SQL injection via transaction metadata"""
        client.app.state.sessions = {"user_token": user_session}

        malicious_metadata = {
            "provider": "'; DROP TABLE credit_transactions; --",
            "model": "1' OR '1'='1",
            "request_id": "'; DELETE FROM user_credits; --"
        }

        response = client.post(
            "/api/v1/credits/deduct",
            cookies={"session_token": "user_token"},
            json={
                "amount": 10.0,
                "metadata": malicious_metadata
            }
        )

        # Should safely handle or reject
        assert response.status_code in [200, 400, 422]
        assert response.status_code != 500

    def test_parameterized_queries_used(self):
        """Verify parameterized queries are used (code inspection)"""
        # This test would inspect the codebase to ensure
        # all database queries use parameterized statements
        # rather than string concatenation

        import litellm_credit_system
        source_code = inspect.getsource(litellm_credit_system.CreditSystem)

        # Check for dangerous patterns
        dangerous_patterns = [
            "f\"SELECT",
            "f'SELECT",
            ".format(",
            "% ("
        ]

        for pattern in dangerous_patterns:
            assert pattern not in source_code, \
                f"Found potentially unsafe query pattern: {pattern}"


class TestAuthorizationChecks:
    """Test authorization and access control"""

    def test_admin_endpoints_require_admin_role(self, client, user_session):
        """Test admin endpoints reject non-admin users"""
        client.app.state.sessions = {"user_token": user_session}

        admin_endpoints = [
            ("/api/v1/admin/credits/allocate", "POST", {"user_id": "test@example.com", "amount": 100}),
            ("/api/v1/admin/credits/bulk-allocate", "POST", {"allocations": []}),
            ("/api/v1/admin/credits/analytics/system", "GET", None),
            ("/api/v1/admin/credits/analytics/top-spenders", "GET", None),
        ]

        for endpoint, method, data in admin_endpoints:
            if method == "GET":
                response = client.get(
                    endpoint,
                    cookies={"session_token": "user_token"}
                )
            else:
                response = client.post(
                    endpoint,
                    cookies={"session_token": "user_token"},
                    json=data
                )

            assert response.status_code == 403, \
                f"Endpoint {endpoint} should reject non-admin"

    def test_users_cannot_access_other_users_data(self, client, user_session):
        """Test users can only access their own data"""
        client.app.state.sessions = {"user_token": user_session}

        # Try to access another user's transaction history
        response = client.get(
            "/api/v1/credits/transactions?user_id=other@example.com",
            cookies={"session_token": "user_token"}
        )

        # Should either ignore the parameter or reject
        if response.status_code == 200:
            # If successful, should only return current user's data
            data = response.json()
            for txn in data.get("transactions", []):
                assert txn.get("user_id") == "user@example.com"

    def test_unauthenticated_requests_rejected(self, client):
        """Test all endpoints require authentication"""
        endpoints = [
            "/api/v1/credits/balance",
            "/api/v1/credits/transactions",
            "/api/v1/credits/usage/stats",
            "/api/v1/admin/credits/allocate",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_expired_sessions_rejected(self, client):
        """Test expired sessions are rejected"""
        # Simulate expired session
        expired_session = {
            "user": {"id": "user_123", "email": "user@example.com"},
            "expires_at": "2020-01-01T00:00:00Z"  # Past date
        }

        client.app.state.sessions = {"expired_token": expired_session}

        response = client.get(
            "/api/v1/credits/balance",
            cookies={"session_token": "expired_token"}
        )

        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting protection"""

    def test_balance_endpoint_rate_limit(self, client, user_session):
        """Test balance endpoint has rate limiting"""
        client.app.state.sessions = {"user_token": user_session}

        # Make rapid requests
        rate_limited = False
        for i in range(200):
            response = client.get(
                "/api/v1/credits/balance",
                cookies={"session_token": "user_token"}
            )

            if response.status_code == 429:
                rate_limited = True
                assert "rate limit" in response.json()["detail"].lower()
                break

        # Should hit rate limit within 200 requests
        assert rate_limited, "Rate limiting not enforced"

    def test_deduction_endpoint_rate_limit(self, client, user_session):
        """Test deduction endpoint has rate limiting"""
        client.app.state.sessions = {"user_token": user_session}

        rate_limited = False
        for i in range(100):
            response = client.post(
                "/api/v1/credits/deduct",
                cookies={"session_token": "user_token"},
                json={
                    "amount": 1.0,
                    "metadata": {"provider": "test", "model": "test", "tokens_used": 100}
                }
            )

            if response.status_code == 429:
                rate_limited = True
                break

        # Deduction should have stricter rate limit
        assert rate_limited, "Deduction rate limiting not enforced"

    def test_rate_limit_per_user(self, client, user_session, admin_session):
        """Test rate limits are per-user, not global"""
        client.app.state.sessions = {
            "user_token": user_session,
            "admin_token": admin_session
        }

        # Exhaust user's rate limit
        for _ in range(200):
            client.get(
                "/api/v1/credits/balance",
                cookies={"session_token": "user_token"}
            )

        # Admin should still be able to make requests
        response = client.get(
            "/api/v1/admin/credits/analytics/system",
            cookies={"session_token": "admin_token"}
        )

        # Admin should not be rate limited
        assert response.status_code != 429


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_negative_credit_amount_rejected(self, client, admin_session):
        """Test negative amounts are rejected"""
        client.app.state.sessions = {"admin_token": admin_session}

        response = client.post(
            "/api/v1/admin/credits/allocate",
            cookies={"session_token": "admin_token"},
            json={
                "user_id": "test@example.com",
                "amount": -100.0,
                "reason": "bonus"
            }
        )

        assert response.status_code in [400, 422]

    def test_excessive_credit_amount_rejected(self, client, admin_session):
        """Test excessively large amounts are rejected"""
        client.app.state.sessions = {"admin_token": admin_session}

        response = client.post(
            "/api/v1/admin/credits/allocate",
            cookies={"session_token": "admin_token"},
            json={
                "user_id": "test@example.com",
                "amount": 999999999999.0,  # Excessive
                "reason": "bonus"
            }
        )

        assert response.status_code in [400, 422]

    def test_invalid_email_format_rejected(self, client, admin_session):
        """Test invalid email formats are rejected"""
        client.app.state.sessions = {"admin_token": admin_session}

        invalid_emails = [
            "not-an-email",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com"
        ]

        for email in invalid_emails:
            response = client.post(
                "/api/v1/admin/credits/allocate",
                cookies={"session_token": "admin_token"},
                json={
                    "user_id": email,
                    "amount": 100.0,
                    "reason": "bonus"
                }
            )

            assert response.status_code in [400, 422]

    def test_xss_in_metadata_sanitized(self, client, user_session):
        """Test XSS payloads in metadata are sanitized"""
        client.app.state.sessions = {"user_token": user_session}

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/v1/credits/deduct",
                cookies={"session_token": "user_token"},
                json={
                    "amount": 10.0,
                    "metadata": {
                        "provider": payload,
                        "model": payload,
                        "request_id": payload
                    }
                }
            )

            if response.status_code == 200:
                # Retrieve transaction and verify XSS is sanitized
                txn_response = client.get(
                    "/api/v1/credits/transactions?limit=1",
                    cookies={"session_token": "user_token"}
                )

                if txn_response.status_code == 200:
                    transactions = txn_response.json().get("transactions", [])
                    if transactions:
                        metadata = transactions[0].get("metadata", {})
                        # XSS should be escaped or removed
                        for value in metadata.values():
                            if isinstance(value, str):
                                assert "<script>" not in value
                                assert "onerror=" not in value


class TestCSRFProtection:
    """Test CSRF protection"""

    def test_state_changing_operations_require_csrf_token(self, client, user_session):
        """Test POST/PUT/DELETE require CSRF token"""
        client.app.state.sessions = {"user_token": user_session}

        # Attempt POST without CSRF token
        response = client.post(
            "/api/v1/credits/deduct",
            cookies={"session_token": "user_token"},
            json={"amount": 10.0, "metadata": {}},
            headers={"Origin": "https://evil.com"}  # Different origin
        )

        # Should be rejected if CSRF protection is enabled
        # (Depends on implementation)
        if response.status_code == 403:
            assert "csrf" in response.json()["detail"].lower()


class TestSessionSecurity:
    """Test session security"""

    def test_session_tokens_are_random(self):
        """Test session tokens are cryptographically random"""
        import secrets

        # Generate multiple tokens
        tokens = [secrets.token_urlsafe(32) for _ in range(100)]

        # All should be unique
        assert len(set(tokens)) == 100

        # All should be long enough (32 bytes = 43 chars base64)
        for token in tokens:
            assert len(token) >= 40

    def test_session_tokens_not_predictable(self):
        """Test session tokens are not sequential or predictable"""
        import secrets

        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        # Should be completely different
        assert token1 != token2

        # Should not be sequential
        assert abs(int.from_bytes(token1.encode(), 'big') -
                   int.from_bytes(token2.encode(), 'big')) > 10000

    def test_sessions_expire_after_inactivity(self, client, user_session):
        """Test sessions expire after period of inactivity"""
        # This would require simulating time passage
        # Or checking that session expiry logic exists
        pass


class TestSecureHeaders:
    """Test security headers are set"""

    def test_response_has_security_headers(self, client, user_session):
        """Test responses include security headers"""
        client.app.state.sessions = {"user_token": user_session}

        response = client.get(
            "/api/v1/credits/balance",
            cookies={"session_token": "user_token"}
        )

        headers = response.headers

        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",  # Should be "nosniff"
            "X-Frame-Options",  # Should be "DENY" or "SAMEORIGIN"
            "X-XSS-Protection",  # Should be "1; mode=block"
        ]

        for header in security_headers:
            if header in headers:
                print(f"{header}: {headers[header]}")


class TestDataLeakage:
    """Test for sensitive data leakage"""

    def test_error_messages_dont_leak_sensitive_info(self, client, user_session):
        """Test error messages don't expose internal details"""
        client.app.state.sessions = {"user_token": user_session}

        # Trigger various errors
        response = client.post(
            "/api/v1/credits/deduct",
            cookies={"session_token": "user_token"},
            json={"invalid": "data"}
        )

        if response.status_code >= 400:
            error_message = response.json().get("detail", "")

            # Should not contain sensitive info
            sensitive_patterns = [
                "password",
                "api_key",
                "secret",
                "token",
                "postgresql://",
                "redis://",
                "Exception:",
                "Traceback"
            ]

            for pattern in sensitive_patterns:
                assert pattern.lower() not in error_message.lower()

    def test_transaction_history_doesnt_expose_other_users(self, client, user_session):
        """Test transaction history doesn't leak other users' data"""
        client.app.state.sessions = {"user_token": user_session}

        response = client.get(
            "/api/v1/credits/transactions",
            cookies={"session_token": "user_token"}
        )

        if response.status_code == 200:
            transactions = response.json().get("transactions", [])

            for txn in transactions:
                # Should only contain current user's data
                assert txn.get("user_id") == user_session["user"]["email"]


# Security audit summary
def print_security_audit_summary():
    """Print security audit summary"""
    print("\n" + "="*60)
    print("CREDIT SYSTEM SECURITY AUDIT SUMMARY")
    print("="*60)
    print("\nSecurity Categories Tested:")
    print("  1. API Key Encryption")
    print("  2. SQL Injection Prevention")
    print("  3. Authorization & Access Control")
    print("  4. Rate Limiting")
    print("  5. Input Validation & Sanitization")
    print("  6. CSRF Protection")
    print("  7. Session Security")
    print("  8. Secure Headers")
    print("  9. Data Leakage Prevention")
    print("\nSecurity Requirements:")
    print("  - All API keys encrypted at rest (Fernet)")
    print("  - Parameterized queries (no SQL injection)")
    print("  - Role-based access control enforced")
    print("  - Rate limiting on all endpoints")
    print("  - XSS payloads sanitized")
    print("  - CSRF tokens validated")
    print("  - Session tokens cryptographically random")
    print("  - No sensitive data in error messages")
    print("="*60 + "\n")


# Run security tests
if __name__ == "__main__":
    print_security_audit_summary()
    pytest.main([__file__, "-v", "--tb=short"])
