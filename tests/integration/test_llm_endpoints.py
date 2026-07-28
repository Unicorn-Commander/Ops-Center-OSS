"""
Integration tests for LLM API endpoints.

Tests complete API flows including provider CRUD, BYOK management,
chat completions, usage analytics, and health monitoring.
"""
import pytest
import httpx
import asyncio
from datetime import datetime, timedelta
import json

# Test Configuration
BASE_URL = "http://localhost:8084"
API_BASE = f"{BASE_URL}/api/v1"
TEST_USER_TOKEN = None  # Will be set during authentication


@pytest.fixture(scope="module")
async def auth_token():
    """Authenticate and get JWT token for tests."""
    global TEST_USER_TOKEN

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        TEST_USER_TOKEN = data["access_token"]
        return TEST_USER_TOKEN


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers with token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestProviderEndpoints:
    """Test provider CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_providers(self, auth_headers):
        """Test listing all LLM providers."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/providers",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "providers" in data
            assert isinstance(data["providers"], list)
            assert len(data["providers"]) > 0

            # Verify provider structure
            provider = data["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "provider_type" in provider
            assert "enabled" in provider
            assert "models" in provider

    @pytest.mark.asyncio
    async def test_get_provider_details(self, auth_headers):
        """Test getting specific provider details."""
        async with httpx.AsyncClient() as client:
            # First get list to find a provider ID
            list_response = await client.get(
                f"{API_BASE}/llm/providers",
                headers=auth_headers
            )
            provider_id = list_response.json()["providers"][0]["id"]

            # Get provider details
            response = await client.get(
                f"{API_BASE}/llm/providers/{provider_id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == provider_id
            assert "health_status" in data
            assert "last_health_check" in data

    @pytest.mark.asyncio
    async def test_create_provider_admin_only(self, auth_headers):
        """Test creating new provider (admin only)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/llm/providers",
                headers=auth_headers,
                json={
                    "name": "Test Provider",
                    "provider_type": "openai",
                    "api_endpoint": "https://api.openai.com/v1",
                    "enabled": True,
                    "priority": 5
                }
            )

            # Should succeed for admin, fail for regular user
            assert response.status_code in [201, 403]

            if response.status_code == 201:
                data = response.json()
                assert data["name"] == "Test Provider"
                assert data["provider_type"] == "openai"

    @pytest.mark.asyncio
    async def test_update_provider(self, auth_headers):
        """Test updating provider configuration."""
        async with httpx.AsyncClient() as client:
            # Get existing provider
            list_response = await client.get(
                f"{API_BASE}/llm/providers",
                headers=auth_headers
            )
            provider_id = list_response.json()["providers"][0]["id"]

            # Update provider
            response = await client.put(
                f"{API_BASE}/llm/providers/{provider_id}",
                headers=auth_headers,
                json={
                    "enabled": True,
                    "priority": 1
                }
            )

            assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_delete_provider(self, auth_headers):
        """Test deleting provider (admin only)."""
        async with httpx.AsyncClient() as client:
            # Create test provider first
            create_response = await client.post(
                f"{API_BASE}/llm/providers",
                headers=auth_headers,
                json={
                    "name": "To Delete",
                    "provider_type": "openai",
                    "api_endpoint": "https://api.openai.com/v1"
                }
            )

            if create_response.status_code == 201:
                provider_id = create_response.json()["id"]

                # Delete it
                response = await client.delete(
                    f"{API_BASE}/llm/providers/{provider_id}",
                    headers=auth_headers
                )

                assert response.status_code in [200, 204, 403]


class TestBYOKEndpoints:
    """Test BYOK (Bring Your Own Key) management."""

    @pytest.mark.asyncio
    async def test_add_byok_key(self, auth_headers):
        """Test adding user's API key."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/llm/byok/keys",
                headers=auth_headers,
                json={
                    "provider_id": "provider-1",
                    "provider_name": "OpenAI",
                    "api_key": "sk-test-1234567890abcdef",
                    "key_name": "My Test Key"
                }
            )

            assert response.status_code in [200, 201]
            data = response.json()

            assert data["success"] is True
            assert "key_id" in data
            # Should not expose API key
            assert "api_key" not in data

    @pytest.mark.asyncio
    async def test_list_byok_keys(self, auth_headers):
        """Test listing user's BYOK keys."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/byok/keys",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "keys" in data
            assert isinstance(data["keys"], list)

            # Keys should be masked
            for key in data["keys"]:
                assert "key_id" in key
                assert "provider_name" in key
                assert "key_name" in key
                assert "created_at" in key
                # Should NOT expose actual API key
                assert "decrypted_key" not in key

    @pytest.mark.asyncio
    async def test_test_byok_key(self, auth_headers):
        """Test validating BYOK key with provider."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/llm/byok/test",
                headers=auth_headers,
                json={
                    "provider_type": "openai",
                    "api_key": "sk-test-valid-key"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "is_valid" in data
            # Will be False for test key, True for real key

    @pytest.mark.asyncio
    async def test_delete_byok_key(self, auth_headers):
        """Test deleting user's BYOK key."""
        async with httpx.AsyncClient() as client:
            # First add a key
            add_response = await client.post(
                f"{API_BASE}/llm/byok/keys",
                headers=auth_headers,
                json={
                    "provider_id": "provider-1",
                    "api_key": "sk-test-to-delete",
                    "key_name": "To Delete"
                }
            )

            if add_response.status_code in [200, 201]:
                key_id = add_response.json()["key_id"]

                # Delete it
                response = await client.delete(
                    f"{API_BASE}/llm/byok/keys/{key_id}",
                    headers=auth_headers
                )

                assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_keys(self, auth_headers):
        """Test that users cannot access other users' keys."""
        async with httpx.AsyncClient() as client:
            # Try to delete a non-existent or other user's key
            response = await client.delete(
                f"{API_BASE}/llm/byok/keys/other-user-key-id",
                headers=auth_headers
            )

            assert response.status_code in [404, 403]


class TestChatCompletionEndpoints:
    """Test LLM chat completion with power levels."""

    @pytest.mark.asyncio
    async def test_chat_completion_eco(self, auth_headers):
        """Test chat completion with eco power level."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Say hello in one word"}
                    ],
                    "power_level": "eco",
                    "max_tokens": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
            assert "content" in data["choices"][0]["message"]

            # Verify routing info
            assert "routing_info" in data
            assert data["routing_info"]["power_level"] == "eco"
            assert "provider_name" in data["routing_info"]
            assert "model_id" in data["routing_info"]

    @pytest.mark.asyncio
    async def test_chat_completion_balanced(self, auth_headers):
        """Test chat completion with balanced power level."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Explain quantum computing briefly"}
                    ],
                    "power_level": "balanced",
                    "max_tokens": 100
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["routing_info"]["power_level"] == "balanced"
            # Should use mid-tier model
            assert data["routing_info"]["cost_per_1k_tokens"] > 0.0001

    @pytest.mark.asyncio
    async def test_chat_completion_precision(self, auth_headers):
        """Test chat completion with precision power level."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Write a haiku about AI"}
                    ],
                    "power_level": "precision",
                    "max_tokens": 50
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["routing_info"]["power_level"] == "precision"
            # Should use premium model
            assert data["routing_info"]["cost_per_1k_tokens"] >= 0.01

    @pytest.mark.asyncio
    async def test_chat_completion_with_byok(self, auth_headers):
        """Test chat completion using BYOK key."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First add BYOK key
            await client.post(
                f"{API_BASE}/llm/byok/keys",
                headers=auth_headers,
                json={
                    "provider_id": "provider-1",
                    "api_key": "sk-test-byok-key",
                    "key_name": "Test BYOK"
                }
            )

            # Make request with BYOK preference
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Test"}
                    ],
                    "power_level": "balanced",
                    "prefer_byok": True,
                    "max_tokens": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check if BYOK was used
            if "routing_info" in data:
                # used_byok flag indicates if user's key was used
                assert "used_byok" in data["routing_info"]

    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, auth_headers):
        """Test streaming chat completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Count to 5"}
                    ],
                    "power_level": "eco",
                    "stream": True,
                    "max_tokens": 20
                }
            )

            assert response.status_code == 200
            # Should return streaming response
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_completion_error_handling(self, auth_headers):
        """Test error handling in chat completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Invalid request (missing messages)
            response = await client.post(
                f"{API_BASE}/llm/chat/completions",
                headers=auth_headers,
                json={
                    "power_level": "eco"
                }
            )

            assert response.status_code == 422  # Validation error


class TestUsageAnalyticsEndpoints:
    """Test usage analytics and reporting."""

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, auth_headers):
        """Test getting usage statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/usage/stats",
                headers=auth_headers,
                params={
                    "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_requests" in data
            assert "total_tokens" in data
            assert "total_cost" in data
            assert "by_provider" in data
            assert "by_power_level" in data

    @pytest.mark.asyncio
    async def test_get_usage_by_date(self, auth_headers):
        """Test getting usage breakdown by date."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/usage/by-date",
                headers=auth_headers,
                params={
                    "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "daily_usage" in data
            assert isinstance(data["daily_usage"], list)

    @pytest.mark.asyncio
    async def test_export_usage_csv(self, auth_headers):
        """Test exporting usage data as CSV."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/usage/export",
                headers=auth_headers,
                params={
                    "format": "csv",
                    "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat()
                }
            )

            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_get_cost_breakdown(self, auth_headers):
        """Test getting cost breakdown by provider/model."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/usage/costs",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "total_cost" in data
            assert "by_provider" in data
            assert "by_model" in data


class TestHealthMonitoringEndpoints:
    """Test health monitoring and status endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_provider_health(self, auth_headers):
        """Test getting health status of all providers."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/llm/health",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "providers" in data
            for provider in data["providers"]:
                assert "id" in provider
                assert "name" in provider
                assert "health_status" in provider
                assert "last_check" in provider

    @pytest.mark.asyncio
    async def test_trigger_health_check(self, auth_headers):
        """Test triggering health check for specific provider."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get provider ID
            list_response = await client.get(
                f"{API_BASE}/llm/providers",
                headers=auth_headers
            )
            provider_id = list_response.json()["providers"][0]["id"]

            # Trigger health check
            response = await client.post(
                f"{API_BASE}/llm/health/check/{provider_id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()

            assert "is_healthy" in data
            assert "response_time_ms" in data


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, auth_headers):
        """Test that rate limits are enforced."""
        async with httpx.AsyncClient() as client:
            # Make many rapid requests
            responses = []
            for i in range(100):
                response = await client.post(
                    f"{API_BASE}/llm/chat/completions",
                    headers=auth_headers,
                    json={
                        "messages": [{"role": "user", "content": "test"}],
                        "power_level": "eco",
                        "max_tokens": 5
                    }
                )
                responses.append(response.status_code)

                if response.status_code == 429:  # Rate limited
                    break

            # Should eventually hit rate limit
            assert 429 in responses


# Run tests with: pytest -v tests/integration/test_llm_endpoints.py
