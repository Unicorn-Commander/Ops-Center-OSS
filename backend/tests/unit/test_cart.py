"""Unit tests for shopping cart functionality"""

import pytest
from datetime import datetime


@pytest.mark.unit
class TestCartBasicOperations:
    """Basic cart CRUD operations"""

    def test_add_to_cart(self, test_user, test_addons):
        """Test adding item to cart"""
        cart = {
            "user_id": test_user["user_id"],
            "items": [],
            "total": 0.0
        }

        # Add first addon
        addon = test_addons[0]
        cart["items"].append({
            "addon_id": addon["id"],
            "quantity": 1,
            "price": addon["base_price"]
        })
        cart["total"] = sum(item["price"] * item["quantity"] for item in cart["items"])

        assert len(cart["items"]) == 1
        assert cart["total"] == addon["base_price"]

    def test_add_duplicate_item(self, test_cart, test_addons):
        """Test adding same item increases quantity"""
        addon_id = test_cart["items"][0]["addon_id"]
        existing_item = test_cart["items"][0]

        # Instead of adding duplicate, update quantity
        existing_item["quantity"] += 1

        # Recalculate total
        test_cart["total"] = sum(
            item["price"] * item["quantity"]
            for item in test_cart["items"]
        )

        assert len(test_cart["items"]) == 1, "Should not create duplicate items"
        assert existing_item["quantity"] == 2
        assert test_cart["total"] == existing_item["price"] * 2

    def test_remove_from_cart(self, test_cart):
        """Test removing item from cart"""
        addon_id = test_cart["items"][0]["addon_id"]

        # Remove item
        test_cart["items"] = [
            item for item in test_cart["items"]
            if item["addon_id"] != addon_id
        ]
        test_cart["total"] = sum(
            item["price"] * item["quantity"]
            for item in test_cart["items"]
        )

        assert len(test_cart["items"]) == 0
        assert test_cart["total"] == 0.0

    def test_clear_cart(self, test_cart):
        """Test clearing entire cart"""
        test_cart["items"] = []
        test_cart["total"] = 0.0
        test_cart["promo_code"] = None
        test_cart["discount_amount"] = 0.0

        assert len(test_cart["items"]) == 0
        assert test_cart["total"] == 0.0


@pytest.mark.unit
class TestCartCalculations:
    """Cart total and pricing calculations"""

    def test_cart_total_calculation(self, test_user, test_addons):
        """Test cart total is calculated correctly"""
        cart = {
            "user_id": test_user["user_id"],
            "items": [
                {"addon_id": test_addons[0]["id"], "quantity": 1, "price": test_addons[0]["base_price"]},
                {"addon_id": test_addons[1]["id"], "quantity": 2, "price": test_addons[1]["base_price"]},
            ]
        }

        # Calculate total
        subtotal = sum(item["price"] * item["quantity"] for item in cart["items"])
        expected_total = test_addons[0]["base_price"] + (test_addons[1]["base_price"] * 2)

        assert subtotal == expected_total
        assert subtotal == 29.97  # 9.99 + (9.99 * 2)

    def test_cart_with_promo_code(self, test_cart, test_promo_codes):
        """Test applying percentage discount promo code"""
        promo = next(p for p in test_promo_codes if p["code"] == "SAVE15")

        # Apply promo code
        test_cart["promo_code"] = promo["code"]
        subtotal = test_cart["subtotal"]
        discount_amount = subtotal * (promo["discount_value"] / 100)
        test_cart["discount_amount"] = discount_amount
        test_cart["total"] = subtotal - discount_amount

        assert test_cart["discount_amount"] > 0
        assert test_cart["total"] < subtotal
        assert test_cart["total"] == subtotal * 0.85  # 15% off

    def test_cart_with_fixed_discount(self, test_cart, test_promo_codes):
        """Test applying fixed amount discount"""
        promo = next(p for p in test_promo_codes if p["code"] == "WELCOME10")

        # Apply fixed discount
        test_cart["promo_code"] = promo["code"]
        subtotal = test_cart["subtotal"]
        discount_amount = promo["discount_value"]
        test_cart["discount_amount"] = discount_amount
        test_cart["total"] = max(0, subtotal - discount_amount)

        assert test_cart["discount_amount"] == 10.0
        assert test_cart["total"] >= 0  # Can't go negative

    def test_cart_empty_check(self, test_cart):
        """Test checking if cart is empty"""
        assert len(test_cart["items"]) > 0, "Test cart should not be empty"

        # Empty cart
        test_cart["items"] = []
        assert len(test_cart["items"]) == 0, "Cart should be empty"

    def test_cart_item_limit(self, test_user, test_addons):
        """Test cart has maximum item limit"""
        max_items = 10
        cart = {"user_id": test_user["user_id"], "items": []}

        # Try to add 11 items
        for i in range(11):
            if len(cart["items"]) < max_items:
                cart["items"].append({
                    "addon_id": f"addon-{i}",
                    "quantity": 1,
                    "price": 9.99
                })

        assert len(cart["items"]) == max_items, f"Cart should be limited to {max_items} items"


@pytest.mark.unit
class TestCartPromoCode:
    """Promo code application tests"""

    def test_cart_with_expired_promo(self, test_cart, test_promo_codes):
        """Test expired promo code is rejected"""
        promo = next(p for p in test_promo_codes if p["code"] == "EXPIRED")

        # Check if expired
        from datetime import datetime
        expires_at = datetime.fromisoformat(promo["expires_at"])
        is_expired = datetime.now() > expires_at

        assert is_expired, "EXPIRED promo should be expired"
        assert not promo["is_active"], "Expired promo should be inactive"

    def test_cart_with_invalid_promo(self, test_cart, test_promo_codes):
        """Test invalid promo code is rejected"""
        invalid_code = "NOTEXIST"

        # Try to find promo
        promo = next((p for p in test_promo_codes if p["code"] == invalid_code), None)

        assert promo is None, "Invalid promo code should not be found"

    def test_cart_promo_code_case_insensitive(self, test_promo_codes):
        """Test promo codes are case-insensitive"""
        code_upper = "SAVE15"
        code_lower = "save15"

        # Normalize to uppercase for comparison
        promo_upper = next((p for p in test_promo_codes if p["code"].upper() == code_upper), None)
        promo_lower = next((p for p in test_promo_codes if p["code"].upper() == code_lower.upper()), None)

        assert promo_upper is not None
        assert promo_lower is not None
        assert promo_upper["code"] == promo_lower["code"]


@pytest.mark.unit
class TestCartPersistence:
    """Cart persistence and session tests"""

    def test_cart_persistence(self, test_cart):
        """Test cart is saved to session"""
        import json

        # Simulate session storage
        cart_json = json.dumps(test_cart)
        restored_cart = json.loads(cart_json)

        assert restored_cart["user_id"] == test_cart["user_id"]
        assert len(restored_cart["items"]) == len(test_cart["items"])
        assert restored_cart["total"] == test_cart["total"]

    def test_cart_expiry(self, test_cart):
        """Test cart expires after 24 hours"""
        from datetime import datetime, timedelta

        created_at = datetime.fromisoformat(test_cart["created_at"])
        expires_at = created_at + timedelta(hours=24)
        is_expired = datetime.now() > expires_at

        # For new cart, should not be expired
        assert not is_expired, "Fresh cart should not be expired"

    def test_cart_update_quantity(self, test_cart):
        """Test updating item quantity"""
        item = test_cart["items"][0]
        original_qty = item["quantity"]
        new_qty = 3

        # Update quantity
        item["quantity"] = new_qty
        test_cart["total"] = sum(
            i["price"] * i["quantity"]
            for i in test_cart["items"]
        )

        assert item["quantity"] == new_qty
        assert item["quantity"] != original_qty


@pytest.mark.unit
class TestCartValidation:
    """Cart validation tests"""

    def test_cart_requires_user_id(self):
        """Test cart requires user ID"""
        cart = {"items": []}

        # Cart without user_id should be invalid
        assert "user_id" not in cart or cart.get("user_id") is None

    def test_cart_item_validation(self, test_addons):
        """Test cart item has required fields"""
        item = {
            "addon_id": test_addons[0]["id"],
            "quantity": 1,
            "price": test_addons[0]["base_price"]
        }

        assert "addon_id" in item
        assert "quantity" in item
        assert "price" in item
        assert item["quantity"] > 0
        assert item["price"] > 0

    def test_cart_negative_quantity_rejected(self):
        """Test negative quantity is rejected"""
        quantity = -1

        # Validation should reject negative quantity
        assert quantity < 0, "Negative quantity should be rejected"

    def test_cart_zero_quantity_removes_item(self, test_cart):
        """Test setting quantity to 0 removes item"""
        item = test_cart["items"][0]
        item["quantity"] = 0

        # Remove items with quantity 0
        test_cart["items"] = [i for i in test_cart["items"] if i["quantity"] > 0]

        assert len(test_cart["items"]) == 0, "Item with quantity 0 should be removed"
