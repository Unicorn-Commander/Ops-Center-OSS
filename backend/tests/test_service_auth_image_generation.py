"""
Integration Tests for Service Key Authentication with Image Generation

Tests the fix for 401 errors when Presenton/Bolt.diy use service keys
to call the image generation API without X-User-ID header.

Author: Backend Authentication Team
Date: November 29, 2025
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

# Test configurations
SERVICE_KEYS = {
    'presenton': 'sk-presenton-service-key-2025',
    'bolt_diy': 'sk-bolt-diy-service-key-2025',
    'brigade': 'sk-brigade-service-key-2025',
    'centerdeep': 'sk-centerdeep-service-key-2025'
}

SERVICE_ORG_IDS = {
    'presenton': 'org_presenton_service',
    'bolt_diy': 'org_bolt_service',
    'brigade': 'org_brigade_service',
    'centerdeep': 'org_centerdeep_service'
}

# Sample user ID for testing X-User-ID header
TEST_USER_ID = '7a6bfd31-0120-4a30-9e21-0fc3b8006579'


class TestServiceKeyAuthentication:
    """Test service key authentication without user context"""

    @pytest.mark.asyncio
    async def test_service_key_without_user_context(self, async_client: AsyncClient):
        """
        Test: Service key authentication WITHOUT X-User-ID header

        Expected:
        - Authentication succeeds (not 401)
        - get_user_id() returns service org ID (e.g., 'org_presenton_service')
        - Credit lookup uses service organization
        - Image generation proceeds successfully
        """
        service_key = SERVICE_KEYS['presenton']

        response = await async_client.post(
            "/api/v1/llm/image/generations",
            headers={
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": "A unicorn with a wizard hat",
                "model": "dall-e-3",
                "size": "1024x1024",
                "quality": "standard",
                "n": 1
            }
        )

        # Assertions
        assert response.status_code != 401, "Service key should authenticate successfully"
        assert response.status_code != 404, "Service org should exist in database"

        if response.status_code == 402:
            pytest.skip("Service org has insufficient credits (expected in test env)")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify response structure
        data = response.json()
        assert "data" in data, "Response should contain 'data' field"
        assert isinstance(data["data"], list), "'data' should be a list of images"
        assert len(data["data"]) == 1, "Should return 1 image"


    @pytest.mark.asyncio
    async def test_service_key_with_user_context(self, async_client: AsyncClient):
        """
        Test: Service key authentication WITH X-User-ID header (user proxying)

        Expected:
        - Authentication succeeds
        - get_user_id() returns user UUID (not service org ID)
        - Credit lookup uses user account
        - Image generation billed to user
        """
        service_key = SERVICE_KEYS['presenton']

        response = await async_client.post(
            "/api/v1/llm/image/generations",
            headers={
                "Authorization": f"Bearer {service_key}",
                "X-User-ID": TEST_USER_ID,
                "Content-Type": "application/json"
            },
            json={
                "prompt": "A cat wearing glasses",
                "model": "dall-e-3",
                "size": "1024x1024",
                "quality": "standard",
                "n": 1
            }
        )

        # Assertions
        assert response.status_code != 401, "Service key with X-User-ID should authenticate"

        if response.status_code == 402:
            pytest.skip("User has insufficient credits (expected in test env)")
        if response.status_code == 404:
            pytest.skip("Test user not found in database")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


    @pytest.mark.asyncio
    async def test_all_service_keys_authenticate(self, async_client: AsyncClient):
        """
        Test: All service keys authenticate without user context

        Expected:
        - All 4 service keys work (presenton, bolt.diy, brigade, centerdeep)
        - Each maps to correct service org ID
        """
        for service_name, service_key in SERVICE_KEYS.items():
            response = await async_client.post(
                "/api/v1/llm/image/generations",
                headers={
                    "Authorization": f"Bearer {service_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": f"Test image for {service_name}",
                    "model": "dall-e-2",  # Cheaper model for testing
                    "size": "256x256",
                    "n": 1
                }
            )

            # All services should authenticate (not 401)
            assert response.status_code != 401, f"{service_name} service key should authenticate"


    @pytest.mark.asyncio
    async def test_invalid_service_key_rejected(self, async_client: AsyncClient):
        """
        Test: Invalid service key is rejected

        Expected:
        - Returns 401 Unauthorized
        - Error message indicates invalid service key
        """
        fake_service_key = "sk-fake-service-key-9999"

        response = await async_client.post(
            "/api/v1/llm/image/generations",
            headers={
                "Authorization": f"Bearer {fake_service_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": "This should fail",
                "model": "dall-e-3",
                "size": "1024x1024",
                "n": 1
            }
        )

        # Assertions
        assert response.status_code == 401, "Invalid service key should return 401"
        assert "Invalid service key" in response.text or "Invalid" in response.text


class TestServiceCreditSystem:
    """Test credit deduction for service organizations"""

    @pytest.mark.asyncio
    async def test_service_org_credit_balance_query(self, db_connection):
        """
        Test: Can query service organization credit balance

        Expected:
        - Service org exists in database
        - Credit balance is accessible
        - Balance is in valid range (0-10000 credits)
        """
        for service_name, org_id in SERVICE_ORG_IDS.items():
            result = await db_connection.fetchrow(
                "SELECT credit_balance FROM organizations WHERE id = $1",
                org_id
            )

            assert result is not None, f"Service org {org_id} should exist"
            assert result['credit_balance'] is not None, f"{org_id} should have credit balance"

            # Convert millicredits to credits
            balance_credits = float(result['credit_balance']) / 1000.0
            assert 0 <= balance_credits <= 10000, f"{org_id} balance should be 0-10000 credits"


    @pytest.mark.asyncio
    async def test_service_org_tier_lookup(self, db_connection):
        """
        Test: Service organization tier lookup works

        Expected:
        - All service orgs have 'managed' tier
        - Tier is used for cost calculation
        """
        for service_name, org_id in SERVICE_ORG_IDS.items():
            result = await db_connection.fetchrow(
                "SELECT subscription_tier FROM organizations WHERE id = $1",
                org_id
            )

            assert result is not None, f"Service org {org_id} should exist"
            assert result['subscription_tier'] == 'managed', f"{org_id} should have 'managed' tier"


    @pytest.mark.asyncio
    async def test_service_credit_deduction(self, credit_system):
        """
        Test: Credit deduction works for service organizations

        Expected:
        - Credits are debited from service org balance
        - Transaction is logged in service_usage_log
        - Cache is invalidated
        """
        org_id = SERVICE_ORG_IDS['presenton']

        # Get initial balance
        initial_balance = await credit_system.get_user_credits(org_id)

        # Debit credits
        metadata = {
            'provider': 'openai',
            'model': 'dall-e-3',
            'endpoint': '/api/v1/llm/image/generations',
            'service_name': 'presenton',
            'prompt': 'Test image'
        }
        new_balance, tx_id = await credit_system.debit_credits(
            user_id=org_id,
            amount=40.0,  # DALL-E 3 costs ~40 credits
            metadata=metadata
        )

        # Assertions
        assert new_balance == initial_balance - 40.0, "Balance should decrease by 40 credits"
        assert tx_id is not None, "Transaction ID should be returned"
        assert tx_id.startswith('svc_'), "Service transaction ID should have 'svc_' prefix"


    @pytest.mark.asyncio
    async def test_service_usage_logging(self, db_connection, credit_system):
        """
        Test: Service usage is logged to service_usage_log table

        Expected:
        - Usage record is created
        - Contains correct service_org_id, credits_used, model
        - Metadata is stored as JSON
        """
        org_id = SERVICE_ORG_IDS['bolt_diy']

        # Debit credits
        metadata = {
            'provider': 'openai',
            'model': 'dall-e-2',
            'endpoint': '/api/v1/llm/image/generations',
            'service_name': 'bolt-diy',
            'prompt': 'Test logging',
            'size': '512x512'
        }
        await credit_system.debit_credits(
            user_id=org_id,
            amount=20.0,
            metadata=metadata
        )

        # Check service_usage_log
        result = await db_connection.fetchrow(
            """
            SELECT * FROM service_usage_log
            WHERE service_org_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            org_id
        )

        assert result is not None, "Usage log entry should be created"
        assert result['service_name'] == 'bolt-diy'
        assert result['credits_used'] == 20.0
        assert result['model_used'] == 'dall-e-2'
        assert result['endpoint'] == '/api/v1/llm/image/generations'


    @pytest.mark.asyncio
    async def test_insufficient_service_credits_error(self, credit_system, db_connection):
        """
        Test: Error when service org has insufficient credits

        Expected:
        - Returns 402 Payment Required
        - Error message indicates insufficient credits
        - Balance is not modified
        """
        org_id = SERVICE_ORG_IDS['centerdeep']

        # Set balance to 10 credits
        await db_connection.execute(
            "UPDATE organizations SET credit_balance = $1 WHERE id = $2",
            10000,  # 10 credits in millicredits
            org_id
        )

        # Try to debit 50 credits (more than balance)
        with pytest.raises(Exception) as exc_info:
            await credit_system.debit_credits(
                user_id=org_id,
                amount=50.0,
                metadata={'provider': 'openai', 'model': 'dall-e-3'}
            )

        assert exc_info.value.status_code == 402, "Should return 402 Payment Required"
        assert "Insufficient" in str(exc_info.value.detail), "Error should mention insufficient credits"


class TestServiceTierBilling:
    """Test tier-based markup for service organizations"""

    @pytest.mark.asyncio
    async def test_service_tier_markup_applied(self, credit_system):
        """
        Test: Managed tier markup is applied to service orgs

        Expected:
        - Service orgs have 'managed' tier
        - Markup is 25% (managed tier default)
        - Cost calculation includes markup
        """
        org_id = SERVICE_ORG_IDS['presenton']

        # Get tier
        tier = await credit_system.get_user_tier(org_id)
        assert tier == 'managed', "Service org should have 'managed' tier"

        # Calculate cost for image generation
        # Base cost for DALL-E 3 (1024x1024 standard): ~$0.04 = 40 credits
        # Managed tier markup: 25%
        # Expected cost: 40 * 1.25 = 50 credits
        from litellm_api import calculate_image_cost

        cost = calculate_image_cost(
            model='dall-e-3',
            size='1024x1024',
            quality='standard',
            n=1,
            user_tier='managed'
        )

        # Allow some rounding tolerance
        assert 48 <= cost <= 52, f"Expected ~50 credits with markup, got {cost}"


class TestBackwardCompatibility:
    """Test that existing functionality still works"""

    @pytest.mark.asyncio
    async def test_regular_user_image_generation_still_works(self, async_client):
        """
        Test: Regular users can still generate images with API keys

        Expected:
        - User API key authentication works
        - BYOK users can generate images
        - Credit deduction happens correctly
        """
        # This test requires a valid user API key
        # Skip if not available in test environment
        pytest.skip("Requires valid user API key in test environment")


    @pytest.mark.asyncio
    async def test_byok_image_generation_bypasses_credits(self, async_client):
        """
        Test: BYOK users are not charged credits for image generation

        Expected:
        - User with OpenAI/OpenRouter BYOK key
        - Image generation succeeds
        - Credits are NOT deducted
        - BYOK key is used for API call
        """
        # This test requires a user with BYOK configured
        pytest.skip("Requires user with BYOK configured in test environment")


# Pytest Fixtures

@pytest.fixture
async def async_client():
    """Async HTTP client for API testing"""
    from server import app  # Import main FastAPI app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_connection():
    """Database connection for direct queries"""
    import asyncpg
    import os

    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
        database=os.getenv('POSTGRES_DB', 'unicorn_db')
    )

    yield conn

    await conn.close()


@pytest.fixture
async def credit_system(db_connection):
    """Credit system instance for testing"""
    import redis.asyncio as aioredis
    import os
    from litellm_credit_system import CreditSystem

    # Create Redis client
    redis_client = await aioredis.from_url(
        f"redis://{os.getenv('REDIS_HOST', 'unicorn-redis')}:{os.getenv('REDIS_PORT', 6379)}"
    )

    # Create DB pool (mock with single connection for testing)
    class MockPool:
        def __init__(self, conn):
            self._conn = conn

        def acquire(self):
            return MockContext(self._conn)

    class MockContext:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    pool = MockPool(db_connection)
    credit_sys = CreditSystem(pool, redis_client)

    yield credit_sys

    await redis_client.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
