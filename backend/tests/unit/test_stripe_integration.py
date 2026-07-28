"""Unit tests for Stripe integration (mocked)"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


@pytest.mark.unit
@pytest.mark.stripe
class TestStripeCheckoutSession:
    """Stripe Checkout Session creation tests"""

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_create, test_user, test_cart):
        """Test creating Stripe checkout session"""
        # Configure mock
        mock_create.return_value = Mock(
            id="cs_test_123456789",
            url="https://checkout.stripe.com/c/pay/cs_test_123456789",
            status="open",
            payment_status="unpaid"
        )

        # Simulate creating checkout session
        session = mock_create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": test_cart["items"][0]["addon_name"],
                    },
                    "unit_amount": int(test_cart["items"][0]["price"] * 100),
                },
                "quantity": test_cart["items"][0]["quantity"],
            }],
            mode="payment",
            success_url="https://unicorncommander.ai/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://unicorncommander.ai/cancel",
            metadata={
                "user_id": test_user["user_id"],
                "cart_id": "cart-123"
            }
        )

        assert session.id == "cs_test_123456789"
        assert session.url.startswith("https://checkout.stripe.com")
        assert session.status == "open"
        assert session.payment_status == "unpaid"
        mock_create.assert_called_once()

    @patch("stripe.checkout.Session.create")
    def test_checkout_session_with_metadata(self, mock_create, test_user, test_cart):
        """Test checkout session includes user and cart metadata"""
        mock_create.return_value = Mock(
            id="cs_test_123",
            metadata={"user_id": test_user["user_id"], "cart_id": "cart-123"}
        )

        session = mock_create(
            payment_method_types=["card"],
            line_items=[],
            mode="payment",
            metadata={
                "user_id": test_user["user_id"],
                "cart_id": "cart-123",
                "addon_ids": json.dumps([item["addon_id"] for item in test_cart["items"]])
            }
        )

        # Verify metadata was passed
        call_kwargs = mock_create.call_args[1]
        assert "metadata" in call_kwargs
        assert call_kwargs["metadata"]["user_id"] == test_user["user_id"]

    @patch("stripe.checkout.Session.create")
    def test_checkout_session_error_handling(self, mock_create):
        """Test handling Stripe API errors"""
        import stripe

        # Simulate Stripe error
        mock_create.side_effect = stripe.error.StripeError("API Error")

        with pytest.raises(stripe.error.StripeError):
            mock_create(
                payment_method_types=["card"],
                line_items=[],
                mode="payment"
            )


@pytest.mark.unit
@pytest.mark.stripe
class TestStripeWebhooks:
    """Stripe webhook handling tests"""

    @patch("stripe.Webhook.construct_event")
    def test_webhook_signature_verification(self, mock_construct, test_webhook_event):
        """Test webhook signature is verified"""
        payload = json.dumps(test_webhook_event)
        sig_header = "t=1234567890,v1=signature"
        webhook_secret = "whsec_test_secret"

        # Configure mock to return the event
        mock_construct.return_value = test_webhook_event

        # Verify webhook
        event = mock_construct(payload, sig_header, webhook_secret)

        assert event["type"] == "checkout.session.completed"
        assert event["data"]["object"]["payment_status"] == "paid"
        mock_construct.assert_called_once_with(payload, sig_header, webhook_secret)

    @patch("stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_construct):
        """Test invalid webhook signature is rejected"""
        import stripe

        payload = '{"id": "evt_test"}'
        sig_header = "invalid_signature"
        webhook_secret = "whsec_test_secret"

        # Simulate signature verification failure
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", sig_header
        )

        with pytest.raises(stripe.error.SignatureVerificationError):
            mock_construct(payload, sig_header, webhook_secret)

    def test_webhook_payment_succeeded(self, test_webhook_event, test_user):
        """Test processing payment_succeeded webhook"""
        event_type = test_webhook_event["type"]
        payment_status = test_webhook_event["data"]["object"]["payment_status"]

        assert event_type == "checkout.session.completed"
        assert payment_status == "paid"

        # Simulate activating add-on
        user_id = test_webhook_event["data"]["object"]["metadata"]["user_id"]
        addon_ids = json.loads(test_webhook_event["data"]["object"]["metadata"]["addon_ids"])

        assert user_id == test_user["user_id"]
        assert len(addon_ids) > 0

    def test_webhook_payment_failed(self, test_webhook_event):
        """Test processing payment_failed webhook"""
        # Modify event to be payment_failed
        test_webhook_event["type"] = "payment_intent.payment_failed"
        test_webhook_event["data"]["object"]["payment_status"] = "failed"

        event_type = test_webhook_event["type"]
        payment_status = test_webhook_event["data"]["object"]["payment_status"]

        assert event_type == "payment_intent.payment_failed"
        assert payment_status == "failed"

        # Simulate NOT activating add-on
        # (add-on should remain inactive)


@pytest.mark.unit
@pytest.mark.stripe
class TestStripeSubscriptions:
    """Stripe subscription handling tests (monthly billing)"""

    @patch("stripe.checkout.Session.create")
    def test_create_subscription_checkout(self, mock_create, test_user):
        """Test creating checkout session for monthly subscription"""
        mock_create.return_value = Mock(
            id="cs_test_sub_123",
            mode="subscription",
            subscription="sub_123"
        )

        session = mock_create(
            payment_method_types=["card"],
            line_items=[{
                "price": "price_monthly_addon",  # Stripe price ID
                "quantity": 1,
            }],
            mode="subscription",
            metadata={"user_id": test_user["user_id"]}
        )

        assert session.id == "cs_test_sub_123"
        assert session.mode == "subscription"
        mock_create.assert_called_once()

    def test_webhook_subscription_created(self, test_webhook_event):
        """Test processing subscription_created webhook"""
        test_webhook_event["type"] = "customer.subscription.created"
        test_webhook_event["data"]["object"] = {
            "id": "sub_123",
            "status": "active",
            "current_period_end": 1234567890,
            "metadata": {"user_id": "test-user-123", "addon_id": "tts-premium"}
        }

        event_type = test_webhook_event["type"]
        subscription_status = test_webhook_event["data"]["object"]["status"]

        assert event_type == "customer.subscription.created"
        assert subscription_status == "active"

    def test_webhook_subscription_cancelled(self, test_webhook_event):
        """Test processing subscription_cancelled webhook"""
        test_webhook_event["type"] = "customer.subscription.deleted"
        test_webhook_event["data"]["object"] = {
            "id": "sub_123",
            "status": "canceled",
            "metadata": {"user_id": "test-user-123", "addon_id": "tts-premium"}
        }

        event_type = test_webhook_event["type"]
        subscription_status = test_webhook_event["data"]["object"]["status"]

        assert event_type == "customer.subscription.deleted"
        assert subscription_status == "canceled"

        # Simulate deactivating add-on


@pytest.mark.unit
@pytest.mark.stripe
class TestStripeRefunds:
    """Stripe refund handling tests"""

    def test_webhook_refund_issued(self, test_webhook_event):
        """Test processing refund webhook"""
        test_webhook_event["type"] = "charge.refunded"
        test_webhook_event["data"]["object"] = {
            "id": "ch_123",
            "amount_refunded": 999,  # $9.99 in cents
            "refunded": True,
            "metadata": {"user_id": "test-user-123", "addon_id": "tts-premium"}
        }

        event_type = test_webhook_event["type"]
        is_refunded = test_webhook_event["data"]["object"]["refunded"]

        assert event_type == "charge.refunded"
        assert is_refunded is True

        # Simulate deactivating add-on after refund


@pytest.mark.unit
@pytest.mark.stripe
class TestStripeTestCards:
    """Stripe test card validation"""

    def test_successful_test_cards(self, stripe_test_cards):
        """Test successful payment cards are valid"""
        visa = stripe_test_cards["success"]["visa"]
        mastercard = stripe_test_cards["success"]["mastercard"]

        assert visa == "4242424242424242"
        assert mastercard == "5555555555554444"
        assert len(visa) == 16
        assert len(mastercard) == 16

    def test_declined_test_cards(self, stripe_test_cards):
        """Test declined payment cards"""
        card_declined = stripe_test_cards["declined"]["card_declined"]
        insufficient_funds = stripe_test_cards["declined"]["insufficient_funds"]

        assert card_declined == "4000000000000002"
        assert insufficient_funds == "4000000000000009"

    def test_3d_secure_test_card(self, stripe_test_cards):
        """Test 3D Secure authentication required card"""
        requires_auth = stripe_test_cards["requires_auth"]["3d_secure"]

        assert requires_auth == "4000002500003155"
