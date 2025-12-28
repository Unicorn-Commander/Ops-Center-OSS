"""
Unit Tests for Lago Org-Based Billing Integration
Run with: pytest test_lago_org_integration.py
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Import the functions we're testing
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lago_integration import (
    create_org_customer,
    get_customer,
    get_or_create_customer,
    create_subscription,
    subscribe_org_to_plan,
    get_subscription,
    terminate_subscription,
    record_usage,
    record_api_call,
    get_invoices,
    get_current_usage,
    migrate_user_to_org,
    is_org_customer,
    check_lago_health,
    LagoIntegrationError
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for API calls"""
    with patch("lago_integration.httpx.AsyncClient") as mock:
        yield mock


@pytest.fixture
def sample_org_data():
    """Sample organization data for testing"""
    return {
        "org_id": f"org_test_{uuid4().hex[:8]}",
        "org_name": "Test Organization",
        "email": "billing@test.org",
        "user_id": f"user_test_{uuid4().hex[:8]}"
    }


@pytest.fixture
def sample_customer_response():
    """Sample Lago customer response"""
    return {
        "customer": {
            "lago_id": "lago_cust_123",
            "external_id": "org_test_123",
            "name": "Test Organization",
            "email": "billing@test.org",
            "metadata": {
                "created_by_user_id": "user_test_456",
                "billing_type": "organization"
            }
        }
    }


@pytest.fixture
def sample_subscription_response():
    """Sample Lago subscription response"""
    return {
        "subscription": {
            "lago_id": "lago_sub_123",
            "external_customer_id": "org_test_123",
            "plan_code": "professional_monthly",
            "status": "active",
            "started_at": "2025-01-01T00:00:00Z"
        }
    }


# ============================================
# Customer Management Tests
# ============================================

@pytest.mark.asyncio
async def test_create_org_customer_success(mock_httpx_client, sample_org_data, sample_customer_response):
    """Test successful organization customer creation"""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = sample_customer_response

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    # Test customer creation
    customer = await create_org_customer(
        org_id=sample_org_data["org_id"],
        org_name=sample_org_data["org_name"],
        email=sample_org_data["email"],
        user_id=sample_org_data["user_id"]
    )

    # Assertions
    assert customer is not None
    assert customer.get("external_id") == "org_test_123"
    assert customer.get("metadata", {}).get("billing_type") == "organization"


@pytest.mark.asyncio
async def test_create_org_customer_already_exists(mock_httpx_client, sample_org_data):
    """Test customer creation when customer already exists"""
    # Mock 422 response (customer exists)
    mock_response_422 = MagicMock()
    mock_response_422.status_code = 422

    # Mock successful GET response
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"customer": {"external_id": sample_org_data["org_id"]}}

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response_422
    mock_client_instance.get.return_value = mock_response_200

    mock_httpx_client.return_value = mock_client_instance

    # Should not raise error, should return existing customer
    customer = await create_org_customer(
        org_id=sample_org_data["org_id"],
        org_name=sample_org_data["org_name"],
        email=sample_org_data["email"]
    )

    assert customer is not None


@pytest.mark.asyncio
async def test_get_customer_not_found(mock_httpx_client):
    """Test getting a customer that doesn't exist"""
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    customer = await get_customer("org_nonexistent")
    assert customer is None


# ============================================
# Subscription Management Tests
# ============================================

@pytest.mark.asyncio
async def test_create_subscription_success(mock_httpx_client, sample_org_data, sample_subscription_response):
    """Test successful subscription creation"""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = sample_subscription_response

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    subscription = await create_subscription(
        org_id=sample_org_data["org_id"],
        plan_code="professional_monthly"
    )

    assert subscription is not None
    assert subscription.get("plan_code") == "professional_monthly"
    assert subscription.get("status") == "active"


@pytest.mark.asyncio
async def test_subscribe_org_to_plan(mock_httpx_client, sample_org_data, sample_customer_response, sample_subscription_response):
    """Test full subscription flow (customer + subscription)"""
    # Mock GET customer (doesn't exist)
    mock_response_404 = MagicMock()
    mock_response_404.status_code = 404

    # Mock POST customer (create)
    mock_response_201_customer = MagicMock()
    mock_response_201_customer.status_code = 201
    mock_response_201_customer.json.return_value = sample_customer_response

    # Mock POST subscription
    mock_response_201_sub = MagicMock()
    mock_response_201_sub.status_code = 201
    mock_response_201_sub.json.return_value = sample_subscription_response

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    # Set up side effects for multiple calls
    mock_client_instance.get.return_value = mock_response_404
    mock_client_instance.post.side_effect = [mock_response_201_customer, mock_response_201_sub]

    mock_httpx_client.return_value = mock_client_instance

    subscription = await subscribe_org_to_plan(
        org_id=sample_org_data["org_id"],
        plan_code="professional_monthly",
        org_name=sample_org_data["org_name"],
        email=sample_org_data["email"],
        user_id=sample_org_data["user_id"]
    )

    assert subscription is not None
    assert subscription.get("status") == "active"


# ============================================
# Usage Tracking Tests
# ============================================

@pytest.mark.asyncio
async def test_record_usage_success(mock_httpx_client, sample_org_data):
    """Test recording a usage event"""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    success = await record_usage(
        org_id=sample_org_data["org_id"],
        event_code="api_call",
        transaction_id=f"tx_{uuid4()}",
        properties={"tokens": 1500}
    )

    assert success is True


@pytest.mark.asyncio
async def test_record_api_call_success(mock_httpx_client, sample_org_data):
    """Test recording an API call with convenience function"""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    success = await record_api_call(
        org_id=sample_org_data["org_id"],
        transaction_id=f"tx_{uuid4()}",
        endpoint="/api/v1/chat/completions",
        user_id=sample_org_data["user_id"],
        tokens=1500,
        model="gpt-4"
    )

    assert success is True


# ============================================
# ID Detection Tests
# ============================================

def test_is_org_customer_org_prefix():
    """Test org customer detection with org_ prefix"""
    assert is_org_customer("org_123abc") is True


def test_is_org_customer_user_prefix():
    """Test org customer detection with user_ prefix"""
    assert is_org_customer("user_123abc") is False


def test_is_org_customer_ambiguous():
    """Test org customer detection with ambiguous ID"""
    # This should use heuristic (length-based in current implementation)
    long_id = "a" * 25
    result = is_org_customer(long_id)
    assert isinstance(result, bool)


# ============================================
# Health Check Tests
# ============================================

@pytest.mark.asyncio
async def test_check_lago_health_healthy(mock_httpx_client):
    """Test health check when Lago is healthy"""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    health = await check_lago_health()

    assert health.get("status") == "healthy"
    assert "api_url" in health


@pytest.mark.asyncio
async def test_check_lago_health_unhealthy(mock_httpx_client):
    """Test health check when Lago is unhealthy"""
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    health = await check_lago_health()

    assert health.get("status") == "unhealthy"


# ============================================
# Error Handling Tests
# ============================================

@pytest.mark.asyncio
async def test_create_customer_no_api_key():
    """Test error when LAGO_API_KEY is not configured"""
    with patch("lago_integration.LAGO_API_KEY", ""):
        with pytest.raises(LagoIntegrationError, match="LAGO_API_KEY not configured"):
            await create_org_customer(
                org_id="org_test",
                org_name="Test",
                email="test@test.com"
            )


@pytest.mark.asyncio
async def test_create_customer_api_error(mock_httpx_client):
    """Test error handling when API returns error"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.get.return_value = mock_response

    mock_httpx_client.return_value = mock_client_instance

    with pytest.raises(LagoIntegrationError, match="Failed to create customer"):
        await create_org_customer(
            org_id="org_test",
            org_name="Test",
            email="test@test.com"
        )


# ============================================
# Integration Tests (require real Lago instance)
# ============================================

@pytest.mark.skip(reason="Requires real Lago instance")
@pytest.mark.asyncio
async def test_full_flow_integration():
    """
    Integration test - requires real Lago instance.
    Remove skip marker and configure LAGO_API_KEY to run.
    """
    org_id = f"org_integration_test_{uuid4().hex[:8]}"
    org_name = "Integration Test Org"
    email = "integration@test.com"

    # Create customer and subscription
    subscription = await subscribe_org_to_plan(
        org_id=org_id,
        plan_code="starter_monthly",
        org_name=org_name,
        email=email,
        user_id="integration_test_user"
    )

    assert subscription is not None

    # Record usage
    success = await record_api_call(
        org_id=org_id,
        transaction_id=f"tx_{uuid4()}",
        endpoint="/api/test",
        user_id="integration_test_user",
        tokens=100
    )

    assert success is True

    # Get subscription
    retrieved_sub = await get_subscription(org_id)
    assert retrieved_sub is not None
    assert retrieved_sub.get("status") == "active"

    # Terminate subscription
    terminated = await terminate_subscription(org_id)
    assert terminated is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
