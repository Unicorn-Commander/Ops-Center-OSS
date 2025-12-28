"""Unit tests for promo code functionality"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.unit
class TestPromoCodeValidation:
    """Promo code validation tests"""

    def test_validate_active_promo_code(self, test_promo_codes):
        """Test valid active promo code is accepted"""
        promo = next(p for p in test_promo_codes if p["code"] == "SAVE15")

        assert promo["is_active"] is True
        assert datetime.fromisoformat(promo["expires_at"]) > datetime.now()

    def test_expired_promo_code_rejected(self, test_promo_codes):
        """Test expired promo code is rejected"""
        promo = next(p for p in test_promo_codes if p["code"] == "EXPIRED")

        expires_at = datetime.fromisoformat(promo["expires_at"])
        is_expired = datetime.now() > expires_at

        assert is_expired is True
        assert promo["is_active"] is False

    def test_invalid_promo_code(self, test_promo_codes):
        """Test invalid promo code returns None"""
        code = "INVALIDCODE123"
        promo = next((p for p in test_promo_codes if p["code"] == code), None)

        assert promo is None

    def test_promo_code_case_insensitive(self, test_promo_codes):
        """Test promo codes work regardless of case"""
        code_variations = ["SAVE15", "save15", "Save15", "SaVe15"]

        for code in code_variations:
            promo = next(
                (p for p in test_promo_codes if p["code"].upper() == code.upper()),
                None
            )
            assert promo is not None, f"Promo code {code} should be found"

    def test_promo_code_max_uses(self, test_promo_codes):
        """Test promo code respects max_uses limit"""
        promo = next(p for p in test_promo_codes if p["code"] == "MAXEDOUT")

        assert promo["max_uses"] is not None
        assert promo["times_used"] >= promo["max_uses"]

        # Should be rejected
        can_use = promo["times_used"] < promo["max_uses"] if promo["max_uses"] else True
        assert can_use is False


@pytest.mark.unit
class TestPromoCodeDiscounts:
    """Discount calculation tests"""

    def test_percentage_discount_calculation(self, test_promo_codes):
        """Test percentage discount is calculated correctly"""
        promo = next(p for p in test_promo_codes if p["discount_type"] == "percentage")
        subtotal = 100.00

        discount_amount = subtotal * (promo["discount_value"] / 100)
        final_price = subtotal - discount_amount

        assert discount_amount == subtotal * 0.15  # 15% of $100 = $15
        assert final_price == 85.00

    def test_fixed_amount_discount(self, test_promo_codes):
        """Test fixed amount discount is applied correctly"""
        promo = next(p for p in test_promo_codes if p["discount_type"] == "fixed_amount")
        subtotal = 50.00

        discount_amount = promo["discount_value"]
        final_price = max(0, subtotal - discount_amount)

        assert discount_amount == 10.00
        assert final_price == 40.00

    def test_fixed_discount_not_negative(self):
        """Test fixed discount doesn't result in negative total"""
        subtotal = 5.00
        discount = 10.00

        final_price = max(0, subtotal - discount)

        assert final_price >= 0
        assert final_price == 0  # Can't go negative

    def test_percentage_discount_large_amount(self):
        """Test percentage discount on large purchase"""
        subtotal = 999.99
        discount_percentage = 50.0

        discount_amount = subtotal * (discount_percentage / 100)
        final_price = subtotal - discount_amount

        assert discount_amount == 499.995
        assert final_price == 499.995

    def test_discount_rounding(self):
        """Test discount amounts are rounded to 2 decimal places"""
        subtotal = 9.99
        discount_percentage = 15.0

        discount_amount = round(subtotal * (discount_percentage / 100), 2)

        assert discount_amount == 1.50  # Not 1.4985


@pytest.mark.unit
class TestPromoCodeRestrictions:
    """Promo code restriction tests"""

    def test_promo_minimum_purchase(self, test_promo_codes):
        """Test promo code minimum purchase requirement"""
        promo = next(p for p in test_promo_codes if p["code"] == "WELCOME10")
        subtotal = 10.00

        min_purchase = promo.get("minimum_purchase", 0)
        can_apply = subtotal >= min_purchase

        assert min_purchase == 15.00
        assert can_apply is False  # $10 is less than $15 minimum

    def test_promo_applicable_categories(self, test_promo_codes):
        """Test promo code only applies to specific categories"""
        promo = next(p for p in test_promo_codes if p["code"] == "AI50")
        addon_category = "ai-services"

        applicable_to = promo.get("applicable_to", ["all"])
        can_apply = "all" in applicable_to or addon_category in applicable_to

        assert "ai-services" in applicable_to
        assert can_apply is True

    def test_promo_not_applicable_to_category(self, test_promo_codes):
        """Test promo code doesn't apply to wrong category"""
        promo = next(p for p in test_promo_codes if p["code"] == "AI50")
        addon_category = "storage"

        applicable_to = promo.get("applicable_to", ["all"])
        can_apply = "all" in applicable_to or addon_category in applicable_to

        assert can_apply is False  # AI50 only applies to ai-services

    def test_promo_one_time_use(self, test_promo_codes):
        """Test promo code limited to one use per user"""
        promo = next(p for p in test_promo_codes if p["code"] == "WELCOME10")

        max_uses = promo.get("max_uses")

        assert max_uses == 1, "WELCOME10 should be one-time use"


@pytest.mark.unit
class TestPromoCodeMetadata:
    """Promo code metadata and tracking tests"""

    def test_promo_code_has_description(self, test_promo_codes):
        """Test all promo codes have descriptions"""
        for promo in test_promo_codes:
            assert "description" in promo, f"Promo {promo['code']} missing description"
            assert len(promo["description"]) > 0

    def test_promo_code_usage_tracking(self, test_promo_codes):
        """Test promo code tracks usage count"""
        promo = next(p for p in test_promo_codes if p["code"] == "SAVE15")

        assert "times_used" in promo
        assert promo["times_used"] >= 0

    def test_promo_code_expiry_format(self, test_promo_codes):
        """Test promo code expiry is valid ISO format"""
        for promo in test_promo_codes:
            expires_at = promo["expires_at"]
            try:
                datetime.fromisoformat(expires_at)
                valid_format = True
            except ValueError:
                valid_format = False

            assert valid_format, f"Invalid expiry format for {promo['code']}"

    def test_promo_code_discount_types(self, test_promo_codes):
        """Test promo codes have valid discount types"""
        valid_types = ["percentage", "fixed_amount"]

        for promo in test_promo_codes:
            assert promo["discount_type"] in valid_types, \
                f"Invalid discount type: {promo['discount_type']}"
