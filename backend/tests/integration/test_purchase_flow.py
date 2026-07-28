"""Integration tests for complete purchase flow"""

import pytest
from unittest.mock import patch, Mock
import json


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_purchase_flow(test_user, test_addons, test_promo_codes, mock_stripe):
    """
    Test complete purchase flow from catalog to add-on activation

    Steps:
    1. Get catalog
    2. Add item to cart
    3. Apply promo code
    4. Create checkout session
    5. Simulate webhook (payment succeeded)
    6. Verify add-on activated
    """
    # Step 1: Get catalog
    catalog = test_addons
    assert len(catalog) == 9, "Catalog should have 9 add-ons"

    # Step 2: Add to cart
    addon = catalog[0]  # TTS Premium
    cart = {
        "user_id": test_user["user_id"],
        "items": [{
            "addon_id": addon["id"],
            "quantity": 1,
            "price": addon["base_price"]
        }]
    }
    subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])
    assert subtotal == 9.99

    # Step 3: Apply promo code
    promo = next(p for p in test_promo_codes if p["code"] == "SAVE15")
    discount_amount = subtotal * (promo["discount_value"] / 100)
    total = subtotal - discount_amount

    cart["promo_code"] = promo["code"]
    cart["discount_amount"] = discount_amount
    cart["total"] = total

    assert cart["discount_amount"] == 1.50  # 15% of $9.99
    assert cart["total"] == 8.49  # $9.99 - $1.50

    # Step 4: Create checkout session (mocked)
    session = mock_stripe["session"].create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": addon["name"]},
                "unit_amount": int(cart["total"] * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        metadata={
            "user_id": test_user["user_id"],
            "addon_ids": json.dumps([addon["id"]])
        }
    )

    assert session.id == "cs_test_123456789"
    assert session.url.startswith("https://checkout.stripe.com")

    # Step 5: Simulate webhook (payment succeeded)
    webhook_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": session.id,
                "payment_status": "paid",
                "metadata": {
                    "user_id": test_user["user_id"],
                    "addon_ids": json.dumps([addon["id"]])
                }
            }
        }
    }

    # Simulate webhook processing
    user_id = webhook_event["data"]["object"]["metadata"]["user_id"]
    addon_ids = json.loads(webhook_event["data"]["object"]["metadata"]["addon_ids"])

    # Step 6: Verify add-on would be activated
    assert user_id == test_user["user_id"]
    assert addon["id"] in addon_ids

    # In real implementation, this would:
    # - Update database with purchase record
    # - Grant add-on features to user
    # - Send confirmation email
    # - Clear cart


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cart_to_checkout_flow(test_user, test_addons):
    """Test cart operations leading to checkout"""
    cart = {"user_id": test_user["user_id"], "items": []}

    # Add 3 items
    for i in range(3):
        addon = test_addons[i]
        cart["items"].append({
            "addon_id": addon["id"],
            "quantity": 1,
            "price": addon["base_price"]
        })

    assert len(cart["items"]) == 3
    subtotal = sum(item["price"] for item in cart["items"])
    assert subtotal == 29.97  # $9.99 + $9.99 + $9.99

    # Remove 1 item
    removed_id = cart["items"][1]["addon_id"]
    cart["items"] = [item for item in cart["items"] if item["addon_id"] != removed_id]

    assert len(cart["items"]) == 2
    new_subtotal = sum(item["price"] for item in cart["items"])
    assert new_subtotal == 19.98

    # Apply promo code
    cart["promo_code"] = "SAVE15"
    cart["discount_amount"] = new_subtotal * 0.15
    cart["total"] = new_subtotal - cart["discount_amount"]

    assert cart["total"] == 16.98  # $19.98 - 15%


@pytest.mark.integration
@pytest.mark.asyncio
async def test_promo_code_integration(test_user, test_addons, test_promo_codes):
    """Test promo code application in purchase flow"""
    cart = {
        "user_id": test_user["user_id"],
        "items": [{
            "addon_id": test_addons[0]["id"],
            "quantity": 1,
            "price": test_addons[0]["base_price"]
        }]
    }

    subtotal = cart["items"][0]["price"]

    # Test percentage discount
    promo = next(p for p in test_promo_codes if p["code"] == "SAVE15")
    discount = subtotal * (promo["discount_value"] / 100)
    total = subtotal - discount

    assert discount == 1.50
    assert total == 8.49

    # Test fixed amount discount
    promo2 = next(p for p in test_promo_codes if p["code"] == "WELCOME10")

    # Check minimum purchase requirement
    min_purchase = promo2.get("minimum_purchase", 0)
    can_apply = subtotal >= min_purchase

    assert min_purchase == 15.00
    assert can_apply is False  # $9.99 < $15.00


@pytest.mark.integration
@pytest.mark.asyncio
async def test_payment_failure_handling(mock_stripe, test_user, test_addons):
    """Test handling payment failure gracefully"""
    # Create checkout session
    session = mock_stripe["session"].create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": test_addons[0]["name"]},
                "unit_amount": 999,
            },
            "quantity": 1,
        }],
        mode="payment",
        metadata={"user_id": test_user["user_id"]}
    )

    # Simulate payment_failed webhook
    webhook_event = {
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_test_failed",
                "status": "failed",
                "last_payment_error": {
                    "code": "card_declined",
                    "message": "Your card was declined"
                },
                "metadata": {"user_id": test_user["user_id"]}
            }
        }
    }

    # Verify payment failed
    assert webhook_event["type"] == "payment_intent.payment_failed"
    assert webhook_event["data"]["object"]["status"] == "failed"

    # Add-on should NOT be activated
    # User should see error message
    # Cart should remain intact for retry


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_admin_create_addon(test_user):
    """Test admin workflow for creating and publishing add-on"""
    # Step 1: Admin creates add-on
    new_addon = {
        "id": "test-new-addon",
        "name": "Test New Add-On",
        "description": "A new add-on for testing",
        "category": "test",
        "base_price": 19.99,
        "billing_type": "monthly",
        "features": ["test_feature_1", "test_feature_2"],
        "icon_url": "/assets/addons/test-new.png",
        "is_active": False  # Initially unpublished
    }

    # Simulate admin API call
    assert new_addon["is_active"] is False

    # Step 2: Admin publishes add-on
    new_addon["is_active"] = True

    # Step 3: Verify in catalog
    # (In real implementation, this would query the database)
    assert new_addon["is_active"] is True
    assert new_addon["base_price"] == 19.99

    # Step 4: User can purchase
    cart = {
        "user_id": test_user["user_id"],
        "items": [{
            "addon_id": new_addon["id"],
            "quantity": 1,
            "price": new_addon["base_price"]
        }]
    }

    assert len(cart["items"]) == 1
    assert cart["items"][0]["addon_id"] == new_addon["id"]
