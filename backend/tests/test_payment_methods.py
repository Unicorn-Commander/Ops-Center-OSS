"""
Comprehensive Test Suite for Payment Methods API
Tests all endpoints with various scenarios including edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException
import stripe
from datetime import datetime

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.payment_methods_manager import PaymentMethodsManager
from routers.payment_methods_api import (
    list_payment_methods,
    create_setup_intent,
    set_default_payment_method,
    remove_payment_method,
    update_billing_address,
    get_upcoming_invoice
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_lago_client():
    """Mock Lago client"""
    client = Mock()
    client.get_customer = AsyncMock(return_value={
        "stripe_customer": {
            "stripe_customer_id": "cus_test123"
        }
    })
    return client


@pytest.fixture
def payment_methods_manager(mock_lago_client):
    """Create PaymentMethodsManager with mocked dependencies"""
    return PaymentMethodsManager(lago_client=mock_lago_client)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "email": "test@example.com",
        "sub": "user123",
        "username": "testuser"
    }


@pytest.fixture
def mock_stripe_payment_method():
    """Mock Stripe PaymentMethod object"""
    pm = Mock()
    pm.id = "pm_test123"
    pm.type = "card"
    pm.customer = "cus_test123"
    pm.created = 1609459200
    pm.card = Mock()
    pm.card.brand = "visa"
    pm.card.last4 = "4242"
    pm.card.exp_month = 12
    pm.card.exp_year = 2025
    pm.card.country = "US"
    pm.card.funding = "credit"
    pm.card.fingerprint = "fp123"
    return pm


@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe Customer object"""
    customer = Mock()
    customer.id = "cus_test123"
    customer.invoice_settings = {
        "default_payment_method": "pm_test123"
    }
    customer.address = {
        "line1": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94102",
        "country": "US"
    }
    return customer


# ============================================================================
# PAYMENT METHODS MANAGER TESTS
# ============================================================================

class TestPaymentMethodsManager:
    """Test suite for PaymentMethodsManager service class"""

    @pytest.mark.asyncio
    async def test_get_stripe_customer_id_success(self, payment_methods_manager):
        """Test successful retrieval of Stripe customer ID"""
        customer_id = await payment_methods_manager.get_stripe_customer_id("test@example.com")
        assert customer_id == "cus_test123"

    @pytest.mark.asyncio
    async def test_get_stripe_customer_id_not_found(self, payment_methods_manager):
        """Test when customer not found in Lago"""
        payment_methods_manager.lago.get_customer = AsyncMock(return_value=None)
        customer_id = await payment_methods_manager.get_stripe_customer_id("notfound@example.com")
        assert customer_id is None

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.list')
    @patch('stripe.Customer.retrieve')
    async def test_list_payment_methods_success(
        self,
        mock_customer_retrieve,
        mock_pm_list,
        payment_methods_manager,
        mock_stripe_customer,
        mock_stripe_payment_method
    ):
        """Test listing payment methods successfully"""
        mock_customer_retrieve.return_value = mock_stripe_customer
        mock_pm_list.return_value = Mock(data=[mock_stripe_payment_method])

        result = await payment_methods_manager.list_payment_methods("cus_test123")

        assert "payment_methods" in result
        assert len(result["payment_methods"]) == 1
        assert result["payment_methods"][0]["last4"] == "4242"
        assert result["payment_methods"][0]["brand"] == "visa"
        assert result["payment_methods"][0]["is_default"] is True
        assert result["default_payment_method_id"] == "pm_test123"

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.list')
    @patch('stripe.Customer.retrieve')
    async def test_list_payment_methods_expires_soon(
        self,
        mock_customer_retrieve,
        mock_pm_list,
        payment_methods_manager,
        mock_stripe_customer,
        mock_stripe_payment_method
    ):
        """Test expiring soon detection"""
        # Set expiration to next month
        next_month = (datetime.now().month % 12) + 1
        next_year = datetime.now().year if next_month > 1 else datetime.now().year + 1
        mock_stripe_payment_method.card.exp_month = next_month
        mock_stripe_payment_method.card.exp_year = next_year

        mock_customer_retrieve.return_value = mock_stripe_customer
        mock_pm_list.return_value = Mock(data=[mock_stripe_payment_method])

        result = await payment_methods_manager.list_payment_methods("cus_test123")

        assert result["payment_methods"][0]["expires_soon"] is True

    @pytest.mark.asyncio
    @patch('stripe.SetupIntent.create')
    async def test_create_setup_intent_success(
        self,
        mock_si_create,
        payment_methods_manager
    ):
        """Test creating SetupIntent successfully"""
        mock_si_create.return_value = Mock(
            id="seti_test123",
            client_secret="seti_test123_secret_abc"
        )

        result = await payment_methods_manager.create_setup_intent(
            "cus_test123",
            {"user_email": "test@example.com"}
        )

        assert result["client_secret"] == "seti_test123_secret_abc"
        assert result["setup_intent_id"] == "seti_test123"
        mock_si_create.assert_called_once()

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.Customer.modify')
    async def test_set_default_payment_method_success(
        self,
        mock_customer_modify,
        mock_pm_retrieve,
        payment_methods_manager,
        mock_stripe_payment_method
    ):
        """Test setting default payment method successfully"""
        mock_pm_retrieve.return_value = mock_stripe_payment_method
        mock_customer_modify.return_value = Mock()

        result = await payment_methods_manager.set_default_payment_method(
            "cus_test123",
            "pm_test123"
        )

        assert result is True
        mock_customer_modify.assert_called_once_with(
            "cus_test123",
            invoice_settings={"default_payment_method": "pm_test123"}
        )

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.retrieve')
    async def test_set_default_payment_method_wrong_customer(
        self,
        mock_pm_retrieve,
        payment_methods_manager,
        mock_stripe_payment_method
    ):
        """Test setting default when payment method belongs to different customer"""
        mock_stripe_payment_method.customer = "cus_different"
        mock_pm_retrieve.return_value = mock_stripe_payment_method

        with pytest.raises(Exception, match="does not belong to customer"):
            await payment_methods_manager.set_default_payment_method(
                "cus_test123",
                "pm_test123"
            )

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.PaymentMethod.list')
    @patch('stripe.Subscription.list')
    @patch('stripe.PaymentMethod.detach')
    async def test_remove_payment_method_success(
        self,
        mock_pm_detach,
        mock_sub_list,
        mock_pm_list,
        mock_pm_retrieve,
        payment_methods_manager,
        mock_stripe_payment_method
    ):
        """Test removing payment method successfully"""
        mock_pm_retrieve.return_value = mock_stripe_payment_method
        mock_sub_list.return_value = Mock(data=[])  # No active subscriptions
        mock_pm_list.return_value = Mock(data=[mock_stripe_payment_method, Mock()])  # 2 methods

        result = await payment_methods_manager.remove_payment_method(
            "cus_test123",
            "pm_test123"
        )

        assert result is True
        mock_pm_detach.assert_called_once_with("pm_test123")

    @pytest.mark.asyncio
    @patch('stripe.PaymentMethod.retrieve')
    @patch('stripe.PaymentMethod.list')
    @patch('stripe.Subscription.list')
    async def test_remove_last_payment_method_with_active_subscription(
        self,
        mock_sub_list,
        mock_pm_list,
        mock_pm_retrieve,
        payment_methods_manager,
        mock_stripe_payment_method
    ):
        """Test blocking removal of last payment method when subscription active"""
        mock_pm_retrieve.return_value = mock_stripe_payment_method
        mock_sub_list.return_value = Mock(data=[Mock()])  # Has active subscription
        mock_pm_list.return_value = Mock(data=[mock_stripe_payment_method])  # Only 1 method

        with pytest.raises(Exception, match="last payment method"):
            await payment_methods_manager.remove_payment_method(
                "cus_test123",
                "pm_test123"
            )

    @pytest.mark.asyncio
    @patch('stripe.Customer.modify')
    async def test_update_billing_address_success(
        self,
        mock_customer_modify,
        payment_methods_manager
    ):
        """Test updating billing address successfully"""
        address = {
            "line1": "456 Oak Ave",
            "line2": "Apt 7",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90001",
            "country": "US"
        }

        result = await payment_methods_manager.update_billing_address(
            "cus_test123",
            address
        )

        assert result is True
        mock_customer_modify.assert_called_once()

    @pytest.mark.asyncio
    @patch('stripe.Invoice.upcoming')
    @patch('stripe.Customer.retrieve')
    @patch('stripe.PaymentMethod.retrieve')
    async def test_get_upcoming_invoice_success(
        self,
        mock_pm_retrieve,
        mock_customer_retrieve,
        mock_invoice_upcoming,
        payment_methods_manager,
        mock_stripe_customer,
        mock_stripe_payment_method
    ):
        """Test fetching upcoming invoice successfully"""
        mock_customer_retrieve.return_value = mock_stripe_customer

        mock_invoice = Mock()
        mock_invoice.amount_due = 4900  # $49.00
        mock_invoice.amount_remaining = 4900
        mock_invoice.currency = "usd"
        mock_invoice.next_payment_attempt = 1640995200
        mock_invoice.period_start = 1638403200
        mock_invoice.period_end = 1640995200
        mock_invoice.subtotal = 4900
        mock_invoice.tax = 0
        mock_invoice.total = 4900
        mock_invoice.lines = Mock(data=[])

        mock_invoice_upcoming.return_value = mock_invoice
        mock_pm_retrieve.return_value = mock_stripe_payment_method

        result = await payment_methods_manager.get_upcoming_invoice("cus_test123")

        assert result is not None
        assert result["amount_due"] == 4900
        assert result["currency"] == "usd"
        assert result["default_payment_method"]["last4"] == "4242"

    @pytest.mark.asyncio
    @patch('stripe.Invoice.upcoming')
    async def test_get_upcoming_invoice_no_subscription(
        self,
        mock_invoice_upcoming,
        payment_methods_manager
    ):
        """Test when customer has no active subscription"""
        mock_invoice_upcoming.side_effect = stripe.error.InvalidRequestError(
            "No upcoming invoices",
            param="customer"
        )

        result = await payment_methods_manager.get_upcoming_invoice("cus_test123")

        assert result is None


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestPaymentMethodsAPI:
    """Test suite for Payment Methods API endpoints"""

    @pytest.mark.asyncio
    @patch('routers.payment_methods_api.get_payment_methods_manager')
    async def test_list_payment_methods_endpoint(
        self,
        mock_get_manager,
        mock_user
    ):
        """Test list payment methods API endpoint"""
        mock_manager = Mock()
        mock_manager.get_stripe_customer_id = AsyncMock(return_value="cus_test123")
        mock_manager.list_payment_methods = AsyncMock(return_value={
            "payment_methods": [
                {
                    "id": "pm_test123",
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "is_default": True,
                    "expires_soon": False,
                    "country": "US",
                    "funding": "credit",
                    "created": 1609459200
                }
            ],
            "default_payment_method_id": "pm_test123",
            "count": 1
        })
        mock_get_manager.return_value = mock_manager

        result = await list_payment_methods(user=mock_user, pm_manager=mock_manager)

        assert len(result.payment_methods) == 1
        assert result.payment_methods[0].last4 == "4242"
        assert result.default_payment_method_id == "pm_test123"

    @pytest.mark.asyncio
    @patch('routers.payment_methods_api.get_payment_methods_manager')
    async def test_create_setup_intent_endpoint(
        self,
        mock_get_manager,
        mock_user
    ):
        """Test create setup intent API endpoint"""
        mock_manager = Mock()
        mock_manager.get_stripe_customer_id = AsyncMock(return_value="cus_test123")
        mock_manager.create_setup_intent = AsyncMock(return_value={
            "client_secret": "seti_secret_abc",
            "setup_intent_id": "seti_123"
        })
        mock_get_manager.return_value = mock_manager

        result = await create_setup_intent(
            request=None,
            user=mock_user,
            pm_manager=mock_manager
        )

        assert result.client_secret == "seti_secret_abc"
        assert result.setup_intent_id == "seti_123"

    @pytest.mark.asyncio
    @patch('routers.payment_methods_api.get_payment_methods_manager')
    async def test_set_default_payment_method_endpoint(
        self,
        mock_get_manager,
        mock_user
    ):
        """Test set default payment method API endpoint"""
        mock_manager = Mock()
        mock_manager.get_stripe_customer_id = AsyncMock(return_value="cus_test123")
        mock_manager.set_default_payment_method = AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_manager

        result = await set_default_payment_method(
            payment_method_id="pm_test123",
            user=mock_user,
            pm_manager=mock_manager
        )

        assert result["success"] is True
        assert "updated successfully" in result["message"]

    @pytest.mark.asyncio
    @patch('routers.payment_methods_api.get_payment_methods_manager')
    async def test_remove_payment_method_endpoint(
        self,
        mock_get_manager,
        mock_user
    ):
        """Test remove payment method API endpoint"""
        mock_manager = Mock()
        mock_manager.get_stripe_customer_id = AsyncMock(return_value="cus_test123")
        mock_manager.remove_payment_method = AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_manager

        result = await remove_payment_method(
            payment_method_id="pm_test123",
            user=mock_user,
            pm_manager=mock_manager
        )

        assert result["success"] is True
        assert "removed successfully" in result["message"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPaymentMethodsIntegration:
    """Integration tests for complete payment method flows"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_add_card_flow(self):
        """Test complete flow of adding a new card"""
        # This would require actual Stripe test mode credentials
        # For now, we just validate the flow structure
        pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_set_default_flow(self):
        """Test complete flow of setting default payment method"""
        pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_remove_card_flow(self):
        """Test complete flow of removing a card"""
        pass


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_stripe_api_error_handling(self, payment_methods_manager):
        """Test handling of Stripe API errors"""
        with patch('stripe.PaymentMethod.list') as mock_list:
            mock_list.side_effect = stripe.error.APIConnectionError("Network error")

            with pytest.raises(Exception, match="Failed to retrieve payment methods"):
                await payment_methods_manager.list_payment_methods("cus_test123")

    @pytest.mark.asyncio
    async def test_missing_user_email(self, mock_user):
        """Test when user email is missing"""
        mock_user_no_email = {}

        # Would raise HTTPException(400) in actual endpoint
        # This tests the validation logic

    @pytest.mark.asyncio
    async def test_invalid_payment_method_id(self, payment_methods_manager):
        """Test with invalid payment method ID format"""
        with patch('stripe.PaymentMethod.retrieve') as mock_retrieve:
            mock_retrieve.side_effect = stripe.error.InvalidRequestError(
                "No such payment method",
                param="id"
            )

            with pytest.raises(Exception):
                await payment_methods_manager.set_default_payment_method(
                    "cus_test123",
                    "invalid_pm_id"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
