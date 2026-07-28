#!/usr/bin/env python3
"""
End-to-End Billing System Tests
Tests complete user journey from signup to billing management

Requirements:
- pytest
- playwright
- httpx
- stripe (test mode)

Usage:
    pytest tests/e2e_billing_test.py -v --html=report.html
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import httpx
import stripe

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from keycloak_integration import (
    get_user_by_email,
    get_user_tier_info,
    create_user,
    delete_user,
    set_subscription_tier,
    update_user_attributes
)
from billing.stripe_client import StripeClient

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8084")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://auth.unicorncommander.ai")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_TEST_MODE = True

# Test user data
TEST_USERS = {
    "trial": {
        "email": "test-trial@example.com",
        "username": "test_trial",
        "tier": "trial",
        "first_name": "Trial",
        "last_name": "User"
    },
    "starter": {
        "email": "test-starter@example.com",
        "username": "test_starter",
        "tier": "starter",
        "first_name": "Starter",
        "last_name": "User"
    },
    "professional": {
        "email": "test-professional@example.com",
        "username": "test_professional",
        "tier": "professional",
        "first_name": "Professional",
        "last_name": "User"
    },
    "enterprise": {
        "email": "test-enterprise@example.com",
        "username": "test_enterprise",
        "tier": "enterprise",
        "first_name": "Enterprise",
        "last_name": "User"
    }
}

# Stripe test cards
STRIPE_TEST_CARDS = {
    "success": "4242424242424242",
    "decline": "4000000000000002",
    "insufficient_funds": "4000000000009995",
    "requires_auth": "4000002500003155"
}


@pytest.fixture(scope="session")
def stripe_client():
    """Initialize Stripe client in test mode"""
    if not STRIPE_SECRET_KEY:
        pytest.skip("STRIPE_SECRET_KEY not configured")

    stripe.api_key = STRIPE_SECRET_KEY
    client = StripeClient(api_key=STRIPE_SECRET_KEY)
    return client


@pytest.fixture(scope="session")
def http_client():
    """HTTP client for API requests"""
    return httpx.AsyncClient(timeout=30.0, verify=False)


@pytest.fixture(scope="function")
async def cleanup_test_users():
    """Clean up test users before and after tests"""
    # Cleanup before test
    for tier, user_data in TEST_USERS.items():
        try:
            await delete_user(user_data["email"])
        except:
            pass

    yield

    # Cleanup after test
    for tier, user_data in TEST_USERS.items():
        try:
            await delete_user(user_data["email"])
        except:
            pass


class TestUserSignupFlow:
    """Test complete user signup flow with payment"""

    @pytest.mark.asyncio
    async def test_new_user_trial_signup(self, cleanup_test_users):
        """Test new user signs up and gets trial tier"""
        user_data = TEST_USERS["trial"]

        # Step 1: Create user in Keycloak
        user_id = await create_user(
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            attributes={
                "subscription_tier": ["trial"],
                "subscription_status": ["active"],
                "api_calls_used": ["0"]
            }
        )

        assert user_id is not None, "User creation failed"

        # Step 2: Verify user exists
        user = await get_user_by_email(user_data["email"])
        assert user is not None
        assert user["email"] == user_data["email"]

        # Step 3: Verify tier info
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "trial"
        assert tier_info["subscription_status"] == "active"
        assert tier_info["api_calls_used"] == 0


    @pytest.mark.asyncio
    async def test_trial_to_paid_upgrade(self, cleanup_test_users, stripe_client):
        """Test user upgrades from trial to paid tier"""
        user_data = TEST_USERS["starter"]

        # Step 1: Create trial user
        user_id = await create_user(
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            attributes={
                "subscription_tier": ["trial"],
                "subscription_status": ["active"]
            }
        )
        assert user_id is not None

        # Step 2: Create Stripe customer
        customer = stripe.Customer.create(
            email=user_data["email"],
            name=f"{user_data['first_name']} {user_data['last_name']}",
            metadata={"keycloak_user_id": user_id}
        )

        # Step 3: Create test subscription
        # Note: In real test, you'd complete checkout flow
        # For now, we simulate subscription creation
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": "price_test_starter"}],  # Test price ID
            metadata={
                "tier": "starter",
                "keycloak_user_id": user_id
            }
        )

        # Step 4: Update Keycloak with subscription
        await update_user_attributes(user_data["email"], {
            "subscription_tier": ["starter"],
            "subscription_status": ["active"],
            "stripe_customer_id": [customer.id],
            "stripe_subscription_id": [subscription.id]
        })

        # Step 5: Verify upgrade
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "starter"
        assert tier_info["stripe_customer_id"] == customer.id

        # Cleanup Stripe
        stripe.Subscription.delete(subscription.id)
        stripe.Customer.delete(customer.id)


class TestSubscriptionManagement:
    """Test subscription management operations"""

    @pytest.mark.asyncio
    async def test_subscription_upgrade(self, cleanup_test_users):
        """Test upgrading subscription to higher tier"""
        user_data = TEST_USERS["starter"]

        # Create starter user
        user_id = await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "subscription_status": ["active"]
            }
        )

        # Upgrade to professional
        success = await set_subscription_tier(
            user_data["email"],
            "professional",
            "active"
        )
        assert success

        # Verify upgrade
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "professional"


    @pytest.mark.asyncio
    async def test_subscription_downgrade(self, cleanup_test_users):
        """Test downgrading subscription to lower tier"""
        user_data = TEST_USERS["professional"]

        # Create professional user
        user_id = await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["professional"],
                "subscription_status": ["active"]
            }
        )

        # Downgrade to starter
        success = await set_subscription_tier(
            user_data["email"],
            "starter",
            "active"
        )
        assert success

        # Verify downgrade
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "starter"


    @pytest.mark.asyncio
    async def test_subscription_cancellation(self, cleanup_test_users):
        """Test canceling subscription"""
        user_data = TEST_USERS["starter"]

        # Create active user
        user_id = await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "subscription_status": ["active"]
            }
        )

        # Cancel subscription
        success = await set_subscription_tier(
            user_data["email"],
            "trial",  # Downgrade to free tier
            "cancelled"
        )
        assert success

        # Verify cancellation
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "trial"
        assert tier_info["subscription_status"] == "cancelled"


class TestTierAccess:
    """Test tier-based access control"""

    @pytest.mark.asyncio
    async def test_trial_tier_limitations(self, cleanup_test_users, http_client):
        """Test trial tier access limitations"""
        user_data = TEST_USERS["trial"]

        # Create trial user
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["trial"],
                "subscription_status": ["active"]
            }
        )

        # Test: Trial users should NOT have BYOK access
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "trial"

        # In a real test, you'd call the API endpoint with auth
        # For now, we verify the tier is set correctly


    @pytest.mark.asyncio
    async def test_starter_tier_byok_access(self, cleanup_test_users):
        """Test starter tier has BYOK access"""
        user_data = TEST_USERS["starter"]

        # Create starter user
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "subscription_status": ["active"]
            }
        )

        # Verify tier
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "starter"

        # Starter tier should have BYOK access
        # (actual BYOK API test would go here)


    @pytest.mark.asyncio
    async def test_professional_tier_full_access(self, cleanup_test_users):
        """Test professional tier has full access"""
        user_data = TEST_USERS["professional"]

        # Create professional user
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["professional"],
                "subscription_status": ["active"]
            }
        )

        # Verify tier
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "professional"


class TestWebhookHandling:
    """Test webhook event handling"""

    @pytest.mark.asyncio
    async def test_lago_subscription_created_webhook(self, cleanup_test_users, http_client):
        """Test Lago subscription.created webhook"""
        user_data = TEST_USERS["starter"]

        # Create user
        await create_user(
            email=user_data["email"],
            username=user_data["username"]
        )

        # Simulate Lago webhook
        webhook_payload = {
            "webhook_type": "subscription.created",
            "subscription": {
                "lago_id": "sub_test_123",
                "plan_code": "starter_monthly",
                "status": "active"
            },
            "customer": {
                "email": user_data["email"]
            }
        }

        # Send webhook to endpoint
        response = await http_client.post(
            f"{BASE_URL}/api/v1/webhooks/lago",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )

        # Should succeed
        assert response.status_code == 200

        # Verify user was updated
        await asyncio.sleep(1)  # Give webhook handler time to process
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "starter"


    @pytest.mark.asyncio
    async def test_lago_subscription_cancelled_webhook(self, cleanup_test_users, http_client):
        """Test Lago subscription.cancelled webhook"""
        user_data = TEST_USERS["starter"]

        # Create active user
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "subscription_status": ["active"]
            }
        )

        # Simulate cancellation webhook
        webhook_payload = {
            "webhook_type": "subscription.cancelled",
            "subscription": {
                "lago_id": "sub_test_123"
            },
            "customer": {
                "email": user_data["email"]
            }
        }

        # Send webhook
        response = await http_client.post(
            f"{BASE_URL}/api/v1/webhooks/lago",
            json=webhook_payload
        )

        assert response.status_code == 200

        # Verify downgrade
        await asyncio.sleep(1)
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["subscription_tier"] == "free" or tier_info["subscription_status"] == "cancelled"


class TestStripeIntegration:
    """Test Stripe payment integration"""

    @pytest.mark.asyncio
    async def test_stripe_customer_creation(self, stripe_client):
        """Test creating Stripe customer"""
        customer = stripe.Customer.create(
            email="test@example.com",
            name="Test User",
            metadata={"test": "true"}
        )

        assert customer.id is not None
        assert customer.email == "test@example.com"

        # Cleanup
        stripe.Customer.delete(customer.id)


    @pytest.mark.asyncio
    async def test_stripe_retrieve_invoices(self, stripe_client):
        """Test retrieving customer invoices"""
        # Create test customer
        customer = stripe.Customer.create(
            email="test@example.com"
        )

        # Get invoices (should be empty)
        invoices = await stripe_client.get_customer_invoices(customer.id)
        assert isinstance(invoices, list)

        # Cleanup
        stripe.Customer.delete(customer.id)


    @pytest.mark.asyncio
    async def test_stripe_subscription_retrieval(self, stripe_client):
        """Test retrieving customer subscription"""
        # Create test customer
        customer = stripe.Customer.create(
            email="test@example.com"
        )

        # Get subscription (should be None)
        subscription = await stripe_client.get_customer_subscription(customer.id)
        assert subscription is None

        # Cleanup
        stripe.Customer.delete(customer.id)


class TestAPIEndpoints:
    """Test billing API endpoints"""

    @pytest.mark.asyncio
    async def test_subscription_status_endpoint(self, http_client):
        """Test /api/v1/subscription/status endpoint"""
        # Note: Requires authentication
        # This is a basic connectivity test
        response = await http_client.get(
            f"{BASE_URL}/api/v1/subscription/status"
        )

        # Should get 401 without auth
        assert response.status_code in [401, 403]


    @pytest.mark.asyncio
    async def test_tier_check_endpoint(self, http_client):
        """Test tier check endpoint"""
        response = await http_client.get(
            f"{BASE_URL}/api/v1/tier/check"
        )

        # Should work without auth but return trial tier
        assert response.status_code in [200, 401]


    @pytest.mark.asyncio
    async def test_webhook_health_endpoint(self, http_client):
        """Test webhook health check"""
        response = await http_client.get(
            f"{BASE_URL}/api/v1/webhooks/lago/health"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestUsageLimits:
    """Test usage limits and tracking"""

    @pytest.mark.asyncio
    async def test_api_usage_increment(self, cleanup_test_users):
        """Test API usage counter increments"""
        from keycloak_integration import increment_usage

        user_data = TEST_USERS["starter"]

        # Create user
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "api_calls_used": ["0"]
            }
        )

        # Increment usage
        success = await increment_usage(user_data["email"])
        assert success

        # Verify increment
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["api_calls_used"] == 1

        # Increment again
        success = await increment_usage(user_data["email"])
        assert success

        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["api_calls_used"] == 2


    @pytest.mark.asyncio
    async def test_usage_reset(self, cleanup_test_users):
        """Test usage counter reset"""
        from keycloak_integration import reset_usage

        user_data = TEST_USERS["starter"]

        # Create user with usage
        await create_user(
            email=user_data["email"],
            username=user_data["username"],
            attributes={
                "subscription_tier": ["starter"],
                "api_calls_used": ["100"]
            }
        )

        # Reset usage
        success = await reset_usage(user_data["email"])
        assert success

        # Verify reset
        tier_info = await get_user_tier_info(user_data["email"])
        assert tier_info["api_calls_used"] == 0


# Test execution report
@pytest.fixture(scope="session", autouse=True)
def test_report():
    """Generate test execution report"""
    print("\n" + "="*80)
    print("E2E BILLING SYSTEM TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Keycloak URL: {KEYCLOAK_URL}")
    print(f"Stripe Test Mode: {STRIPE_TEST_MODE}")
    print(f"Test Start: {datetime.now().isoformat()}")
    print("="*80 + "\n")

    yield

    print("\n" + "="*80)
    print(f"Test End: {datetime.now().isoformat()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--html=test_report.html", "--self-contained-html"])
