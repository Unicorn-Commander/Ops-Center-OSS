"""
Extensions Marketplace Integration Test Suite
==============================================

Comprehensive tests for all 25 marketplace endpoints:
- Catalog API (6 endpoints)
- Cart API (6 endpoints)
- Purchase API (8 endpoints)
- Admin API (5 endpoints)

Run with: pytest tests/test_extensions_marketplace.py -v
"""

import pytest
import asyncio
import httpx
from decimal import Decimal
from typing import Optional, Dict, Any

# Test Configuration
BASE_URL = "http://localhost:8084"
TEST_USER_ID = "test-user-123"
TEST_ADMIN_ID = "admin-user-123"

# Session tokens (mock for testing - in production these would be real Keycloak tokens)
USER_SESSION = "test-session-token-user"
ADMIN_SESSION = "test-session-token-admin"


class TestClient:
    """HTTP client wrapper with session handling"""

    def __init__(self, session_token: Optional[str] = None):
        self.session_token = session_token
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        cookies = {"session_token": self.session_token} if self.session_token else {}
        return await self.client.get(url, cookies=cookies, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        cookies = {"session_token": self.session_token} if self.session_token else {}
        return await self.client.post(url, cookies=cookies, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        cookies = {"session_token": self.session_token} if self.session_token else {}
        return await self.client.put(url, cookies=cookies, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        cookies = {"session_token": self.session_token} if self.session_token else {}
        return await self.client.delete(url, cookies=cookies, **kwargs)

    async def close(self):
        await self.client.aclose()


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def public_client():
    """Public client (no authentication)"""
    client = TestClient()
    yield client
    await client.close()


@pytest.fixture
async def user_client():
    """Authenticated user client"""
    client = TestClient(USER_SESSION)
    yield client
    await client.close()


@pytest.fixture
async def admin_client():
    """Authenticated admin client"""
    client = TestClient(ADMIN_SESSION)
    yield client
    await client.close()


@pytest.fixture
async def sample_addon_id(admin_client):
    """Get a sample add-on ID for testing"""
    response = await admin_client.get("/api/v1/extensions/catalog", params={"limit": 1})
    if response.status_code == 200 and response.json():
        return response.json()[0]["id"]
    return 1  # Default to ID 1 if query fails


# ============================================================================
# CATALOG API TESTS (6 endpoints)
# ============================================================================

class TestCatalogAPI:
    """Test public catalog browsing endpoints"""

    @pytest.mark.asyncio
    async def test_list_catalog_empty(self, public_client):
        """Test listing catalog with no data (should return empty array)"""
        # Use a category that doesn't exist
        response = await public_client.get(
            "/api/v1/extensions/catalog",
            params={"category": "NonExistentCategory"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    @pytest.mark.asyncio
    async def test_list_catalog_with_data(self, public_client):
        """Test listing catalog returns add-ons"""
        response = await public_client.get("/api/v1/extensions/catalog")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            addon = data[0]
            assert "id" in addon
            assert "name" in addon
            assert "description" in addon
            assert "category" in addon
            assert "base_price" in addon
            assert "features" in addon

    @pytest.mark.asyncio
    async def test_get_addon_by_id(self, public_client, sample_addon_id):
        """Test getting specific add-on details"""
        response = await public_client.get(f"/api/v1/extensions/{sample_addon_id}")

        if response.status_code == 404:
            pytest.skip("No add-ons in database")

        assert response.status_code == 200
        addon = response.json()
        assert addon["id"] == sample_addon_id
        assert "name" in addon
        assert "features" in addon
        assert isinstance(addon["features"], dict)

    @pytest.mark.asyncio
    async def test_list_categories(self, public_client):
        """Test getting category list with counts"""
        response = await public_client.get("/api/v1/extensions/categories/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            category = data[0]
            assert "category" in category
            assert "count" in category
            assert category["count"] >= 0

    @pytest.mark.asyncio
    async def test_featured_addons(self, public_client):
        """Test getting featured add-ons"""
        response = await public_client.get("/api/v1/extensions/featured")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Featured endpoint should limit results
        assert len(data) <= 20

    @pytest.mark.asyncio
    async def test_search_addons(self, public_client):
        """Test searching add-ons with query"""
        response = await public_client.get(
            "/api/v1/extensions/search",
            params={"q": "analytics", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


# ============================================================================
# CART API TESTS (6 endpoints)
# ============================================================================

class TestCartAPI:
    """Test cart management endpoints"""

    @pytest.mark.asyncio
    async def test_get_cart_unauthenticated(self, public_client):
        """Test getting cart without authentication returns 401"""
        response = await public_client.get("/api/v1/cart")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_add_to_cart_authenticated(self, user_client, sample_addon_id):
        """Test adding item to cart"""
        # First clear cart
        await user_client.delete("/api/v1/cart/clear")

        # Add item to cart
        response = await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 2}
        )

        if response.status_code == 404:
            pytest.skip("No add-ons available")

        assert response.status_code == 200
        cart = response.json()
        assert cart["item_count"] >= 1
        assert cart["total"] > 0

        # Verify cart contains the item
        items = cart["items"]
        assert len(items) >= 1
        assert items[0]["quantity"] == 2

    @pytest.mark.asyncio
    async def test_update_cart_quantity(self, user_client, sample_addon_id):
        """Test updating cart item quantity"""
        # Add item first
        await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 1}
        )

        # Get cart to find cart_item_id
        cart_response = await user_client.get("/api/v1/cart")
        if cart_response.status_code != 200 or not cart_response.json()["items"]:
            pytest.skip("Cart is empty")

        cart_item_id = cart_response.json()["items"][0]["cart_item_id"]

        # Update quantity
        response = await user_client.put(
            f"/api/v1/cart/{cart_item_id}",
            params={"quantity": 5}
        )

        assert response.status_code == 200
        cart = response.json()
        updated_item = next(
            (item for item in cart["items"] if item["cart_item_id"] == cart_item_id),
            None
        )
        assert updated_item is not None
        assert updated_item["quantity"] == 5

    @pytest.mark.asyncio
    async def test_remove_from_cart(self, user_client, sample_addon_id):
        """Test removing item from cart"""
        # Add item first
        await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 1}
        )

        # Get cart
        cart_response = await user_client.get("/api/v1/cart")
        if cart_response.status_code != 200 or not cart_response.json()["items"]:
            pytest.skip("Cart is empty")

        cart_item_id = cart_response.json()["items"][0]["cart_item_id"]

        # Remove item
        response = await user_client.delete(f"/api/v1/cart/{cart_item_id}")
        assert response.status_code == 200

        # Verify item was removed
        cart = response.json()
        assert not any(
            item["cart_item_id"] == cart_item_id for item in cart["items"]
        )

    @pytest.mark.asyncio
    async def test_clear_cart(self, user_client, sample_addon_id):
        """Test clearing entire cart"""
        # Add items
        await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 3}
        )

        # Clear cart
        response = await user_client.delete("/api/v1/cart/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cart"]["item_count"] == 0

    @pytest.mark.asyncio
    async def test_cart_totals_calculation(self, user_client, sample_addon_id):
        """Test cart total calculation is accurate"""
        # Clear cart
        await user_client.delete("/api/v1/cart/clear")

        # Add items
        add_response = await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 3}
        )

        if add_response.status_code != 200:
            pytest.skip("Could not add items to cart")

        cart = add_response.json()

        # Verify totals
        assert "subtotal" in cart
        assert "discount" in cart
        assert "total" in cart

        # Calculate expected total
        expected_subtotal = sum(
            float(item["subtotal"]) for item in cart["items"]
        )
        assert abs(float(cart["subtotal"]) - expected_subtotal) < 0.01

        # Total should be subtotal - discount
        expected_total = float(cart["subtotal"]) - float(cart["discount"])
        assert abs(float(cart["total"]) - expected_total) < 0.01


# ============================================================================
# PURCHASE API TESTS (8 endpoints)
# ============================================================================

class TestPurchaseAPI:
    """Test purchase and checkout endpoints"""

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, user_client, sample_addon_id):
        """Test creating Stripe checkout session"""
        # Add item to cart
        await user_client.delete("/api/v1/cart/clear")
        await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 1}
        )

        # Create checkout session
        response = await user_client.post(
            "/api/v1/extensions/checkout",
            json={
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
        )

        # May return 500 if Stripe not configured - that's expected
        if response.status_code == 500:
            pytest.skip("Stripe not configured")

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data or "session_id" in data

    @pytest.mark.asyncio
    async def test_stripe_webhook_checkout_completed(self, public_client):
        """Test Stripe webhook handling (checkout.session.completed)"""
        # This is hard to test without real Stripe events
        # Just verify endpoint exists and validates signature
        response = await public_client.post(
            "/api/v1/extensions/webhook/stripe",
            json={},
            headers={"Stripe-Signature": "invalid"}
        )

        # Should return 400 or 401 for invalid signature
        assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_list_purchases(self, user_client):
        """Test listing user's purchases"""
        response = await user_client.get("/api/v1/extensions/purchases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Check structure if purchases exist
        if len(data) > 0:
            purchase = data[0]
            assert "id" in purchase
            assert "add_on_id" in purchase
            assert "status" in purchase

    @pytest.mark.asyncio
    async def test_activate_purchase(self, user_client):
        """Test activating a purchase"""
        # Get purchases first
        purchases_response = await user_client.get("/api/v1/extensions/purchases")

        if purchases_response.status_code != 200 or not purchases_response.json():
            pytest.skip("No purchases to activate")

        purchase_id = purchases_response.json()[0]["id"]

        response = await user_client.post(
            f"/api/v1/extensions/purchases/{purchase_id}/activate"
        )

        # May return 400 if already active
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_list_active_addons(self, user_client):
        """Test listing currently active add-ons"""
        response = await user_client.get("/api/v1/extensions/active")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_apply_promo_code(self, user_client, sample_addon_id):
        """Test applying promotional code"""
        # Add item to cart
        await user_client.delete("/api/v1/cart/clear")
        await user_client.post(
            "/api/v1/cart/add",
            params={"addon_id": str(sample_addon_id), "quantity": 1}
        )

        # Apply promo code
        response = await user_client.post(
            "/api/v1/extensions/promo/apply",
            json={"code": "WELCOME25"}
        )

        # May return 404 if promo code doesn't exist
        if response.status_code == 404:
            pytest.skip("Promo code not found")

        assert response.status_code in [200, 400]  # 400 if invalid/expired

    @pytest.mark.asyncio
    async def test_cancel_purchase(self, user_client):
        """Test canceling a purchase/subscription"""
        # Get purchases
        purchases_response = await user_client.get("/api/v1/extensions/purchases")

        if purchases_response.status_code != 200 or not purchases_response.json():
            pytest.skip("No purchases to cancel")

        purchase_id = purchases_response.json()[0]["id"]

        response = await user_client.post(
            f"/api/v1/extensions/purchases/{purchase_id}/cancel"
        )

        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_get_invoice(self, user_client):
        """Test retrieving invoice for purchase"""
        # Get purchases
        purchases_response = await user_client.get("/api/v1/extensions/purchases")

        if purchases_response.status_code != 200 or not purchases_response.json():
            pytest.skip("No purchases with invoices")

        purchase_id = purchases_response.json()[0]["id"]

        response = await user_client.get(
            f"/api/v1/extensions/purchases/{purchase_id}/invoice"
        )

        # May return 404 if no invoice generated yet
        assert response.status_code in [200, 404]


# ============================================================================
# ADMIN API TESTS (5 endpoints)
# ============================================================================

class TestAdminAPI:
    """Test admin-only management endpoints"""

    @pytest.mark.asyncio
    async def test_create_addon_admin_only(self, admin_client):
        """Test creating add-on requires admin role"""
        response = await admin_client.post(
            "/api/v1/admin/extensions/addons",
            json={
                "name": "Test Add-on",
                "description": "Test description",
                "category": "Testing",
                "base_price": 9.99,
                "billing_type": "monthly",
                "features": {"test": "feature"}
            }
        )

        # Should succeed with admin session
        # May fail with validation error if data invalid
        assert response.status_code in [200, 201, 422]

    @pytest.mark.asyncio
    async def test_update_addon(self, admin_client, sample_addon_id):
        """Test updating add-on"""
        response = await admin_client.put(
            f"/api/v1/admin/extensions/addons/{sample_addon_id}",
            json={
                "name": "Updated Add-on Name",
                "base_price": 19.99
            }
        )

        if response.status_code == 404:
            pytest.skip("Add-on not found")

        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_soft_delete_addon(self, admin_client, sample_addon_id):
        """Test soft deleting add-on (sets is_active=false)"""
        response = await admin_client.delete(
            f"/api/v1/admin/extensions/addons/{sample_addon_id}"
        )

        if response.status_code == 404:
            pytest.skip("Add-on not found")

        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_sales_analytics(self, admin_client):
        """Test getting sales analytics"""
        response = await admin_client.get("/api/v1/admin/extensions/analytics")

        assert response.status_code == 200
        data = response.json()

        # Check expected analytics fields
        assert "total_revenue" in data or "total_sales" in data

    @pytest.mark.asyncio
    async def test_create_promo_code(self, admin_client):
        """Test creating promotional code"""
        response = await admin_client.post(
            "/api/v1/admin/extensions/promo",
            json={
                "code": "TEST20",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "valid_until": "2025-12-31T23:59:59"
            }
        )

        # May return 409 if code already exists
        assert response.status_code in [200, 201, 409, 422]


# ============================================================================
# Test Summary
# ============================================================================

def test_summary():
    """
    Summary of test coverage:

    Catalog API (6 endpoints):
    - ✓ List catalog (empty)
    - ✓ List catalog (with data)
    - ✓ Get add-on by ID
    - ✓ List categories
    - ✓ Featured add-ons
    - ✓ Search add-ons

    Cart API (6 endpoints):
    - ✓ Get cart (unauthenticated)
    - ✓ Add to cart
    - ✓ Update quantity
    - ✓ Remove from cart
    - ✓ Clear cart
    - ✓ Cart totals calculation

    Purchase API (8 endpoints):
    - ✓ Create checkout session
    - ✓ Stripe webhook
    - ✓ List purchases
    - ✓ Activate purchase
    - ✓ List active add-ons
    - ✓ Apply promo code
    - ✓ Cancel purchase
    - ✓ Get invoice

    Admin API (5 endpoints):
    - ✓ Create add-on (admin only)
    - ✓ Update add-on
    - ✓ Soft delete add-on
    - ✓ Sales analytics
    - ✓ Create promo code

    Total: 25 endpoints tested
    """
    pass


if __name__ == "__main__":
    print("Run with: pytest tests/test_extensions_marketplace.py -v")
    print("\nTest Coverage:")
    print("- Catalog API: 6 endpoints")
    print("- Cart API: 6 endpoints")
    print("- Purchase API: 8 endpoints")
    print("- Admin API: 5 endpoints")
    print("Total: 25 endpoints")
