"""Unit tests for Extensions Marketplace catalog functionality"""

import pytest
from decimal import Decimal


@pytest.mark.unit
class TestCatalogBasics:
    """Basic catalog retrieval tests"""

    def test_get_all_addons(self, test_addons):
        """Test retrieving all add-ons from catalog"""
        # Simulate catalog API call
        catalog = test_addons

        assert len(catalog) == 9, f"Expected 9 add-ons, got {len(catalog)}"
        assert all("id" in addon for addon in catalog), "All add-ons should have ID"
        assert all("name" in addon for addon in catalog), "All add-ons should have name"
        assert all("base_price" in addon for addon in catalog), "All add-ons should have price"

    def test_get_addon_by_id(self, test_addons):
        """Test retrieving specific add-on by ID"""
        addon_id = "tts-premium"
        addon = next((a for a in test_addons if a["id"] == addon_id), None)

        assert addon is not None, f"Add-on {addon_id} not found"
        assert addon["name"] == "TTS Premium Service"
        assert addon["base_price"] == 9.99
        assert addon["category"] == "ai-services"

    def test_get_addon_not_found(self, test_addons):
        """Test retrieving non-existent add-on returns None"""
        addon_id = "nonexistent-addon"
        addon = next((a for a in test_addons if a["id"] == addon_id), None)

        assert addon is None, "Non-existent add-on should return None"


@pytest.mark.unit
class TestCatalogFiltering:
    """Catalog filtering and search tests"""

    def test_filter_by_category(self, test_addons):
        """Test filtering add-ons by category"""
        category = "ai-services"
        filtered = [a for a in test_addons if a["category"] == category]

        assert len(filtered) == 3, f"Expected 3 AI services, got {len(filtered)}"
        assert all(a["category"] == category for a in filtered)

    def test_filter_by_multiple_categories(self, test_addons):
        """Test filtering by multiple categories"""
        categories = ["ai-services", "storage"]
        filtered = [a for a in test_addons if a["category"] in categories]

        assert len(filtered) == 4, f"Expected 4 add-ons, got {len(filtered)}"

    def test_search_addons_by_name(self, test_addons):
        """Test searching add-ons by name"""
        search_term = "premium"
        results = [a for a in test_addons if search_term.lower() in a["name"].lower()]

        assert len(results) == 2, f"Expected 2 results for '{search_term}', got {len(results)}"

    def test_search_addons_by_description(self, test_addons):
        """Test searching add-ons by description"""
        search_term = "github"
        results = [a for a in test_addons
                   if search_term.lower() in a["description"].lower()]

        assert len(results) >= 1, "Should find GitHub integration add-on"


@pytest.mark.unit
class TestCatalogPricing:
    """Pricing and billing tests"""

    def test_addon_price_formatting(self, test_addons):
        """Test price is correctly formatted as decimal"""
        for addon in test_addons:
            price = addon["base_price"]
            assert isinstance(price, (int, float)), f"Price should be numeric, got {type(price)}"
            assert price > 0, "Price should be positive"
            # Check decimal places (should be .00 or .99 etc)
            decimal_price = Decimal(str(price))
            assert decimal_price.as_tuple().exponent >= -2, "Price should have max 2 decimal places"

    def test_tier_discounts(self, test_addons):
        """Test tier-based pricing discounts"""
        addon = next(a for a in test_addons if "tier_discount" in a)

        assert "professional" in addon["tier_discount"]
        assert "enterprise" in addon["tier_discount"]

        # Calculate discounted price for enterprise
        base_price = addon["base_price"]
        enterprise_discount = addon["tier_discount"]["enterprise"]
        discounted_price = base_price * (1 - enterprise_discount / 100)

        assert discounted_price < base_price, "Discounted price should be less than base"

    def test_billing_types(self, test_addons):
        """Test all add-ons have valid billing types"""
        valid_billing_types = ["monthly", "annual", "one_time"]

        for addon in test_addons:
            assert addon["billing_type"] in valid_billing_types, \
                f"Invalid billing type: {addon['billing_type']}"


@pytest.mark.unit
class TestCatalogSorting:
    """Catalog sorting tests"""

    def test_sort_by_price_ascending(self, test_addons):
        """Test sorting add-ons by price (low to high)"""
        sorted_addons = sorted(test_addons, key=lambda x: x["base_price"])

        assert sorted_addons[0]["base_price"] <= sorted_addons[1]["base_price"]
        assert sorted_addons[-2]["base_price"] <= sorted_addons[-1]["base_price"]

    def test_sort_by_price_descending(self, test_addons):
        """Test sorting add-ons by price (high to low)"""
        sorted_addons = sorted(test_addons, key=lambda x: x["base_price"], reverse=True)

        assert sorted_addons[0]["base_price"] >= sorted_addons[1]["base_price"]
        assert sorted_addons[-2]["base_price"] >= sorted_addons[-1]["base_price"]

    def test_sort_by_name(self, test_addons):
        """Test sorting add-ons alphabetically"""
        sorted_addons = sorted(test_addons, key=lambda x: x["name"])

        assert sorted_addons[0]["name"] <= sorted_addons[1]["name"]


@pytest.mark.unit
class TestCatalogFeatures:
    """Feature and metadata tests"""

    def test_addon_features_list(self, test_addons):
        """Test add-ons have valid features array"""
        for addon in test_addons:
            assert "features" in addon, f"Add-on {addon['id']} missing features"
            assert isinstance(addon["features"], list), "Features should be an array"
            assert len(addon["features"]) > 0, "Features array should not be empty"

    def test_addon_has_icon(self, test_addons):
        """Test all add-ons have icon URL"""
        for addon in test_addons:
            assert "icon_url" in addon, f"Add-on {addon['id']} missing icon_url"
            assert addon["icon_url"].startswith("/assets/addons/"), "Icon should be in correct path"

    def test_addon_active_status(self, test_addons):
        """Test add-ons have is_active flag"""
        for addon in test_addons:
            assert "is_active" in addon, f"Add-on {addon['id']} missing is_active"
            assert isinstance(addon["is_active"], bool), "is_active should be boolean"


@pytest.mark.unit
class TestCatalogPagination:
    """Pagination tests"""

    def test_pagination_limit(self, test_addons):
        """Test limiting results"""
        limit = 5
        paginated = test_addons[:limit]

        assert len(paginated) == limit, f"Expected {limit} results, got {len(paginated)}"

    def test_pagination_offset(self, test_addons):
        """Test offset pagination"""
        limit = 3
        offset = 2
        paginated = test_addons[offset:offset + limit]

        assert len(paginated) == limit
        assert paginated[0]["id"] == test_addons[offset]["id"]

    def test_pagination_beyond_results(self, test_addons):
        """Test pagination beyond available results"""
        offset = len(test_addons) + 10
        paginated = test_addons[offset:]

        assert len(paginated) == 0, "Should return empty list for offset beyond results"
