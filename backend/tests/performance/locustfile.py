"""
Load testing for Extensions Marketplace using Locust

Run with:
    locust -f backend/tests/performance/locustfile.py --host http://localhost:8084

Web UI will be available at: http://localhost:8089
"""

from locust import HttpUser, task, between
import random
import json


class MarketplaceUser(HttpUser):
    """Simulated user browsing and purchasing from marketplace"""

    # Wait 1-5 seconds between tasks
    wait_time = between(1, 5)

    # Test data
    addon_ids = [
        "tts-premium",
        "stt-professional",
        "image-gen-plus",
        "storage-100gb",
        "premium-compute",
        "github-integration",
        "slack-notifications",
        "advanced-analytics",
        "custom-branding"
    ]

    promo_codes = ["SAVE15", "WELCOME10", "AI50"]

    def on_start(self):
        """Called when user starts - simulate login"""
        self.user_id = f"load-test-user-{random.randint(1000, 9999)}"
        self.cart_items = []

        # Simulate authentication
        self.auth_token = "test-auth-token-12345"
        self.client.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    @task(10)
    def browse_catalog(self):
        """
        Browse marketplace catalog (highest weight)

        Expected: <200ms response time
        """
        response = self.client.get(
            "/api/v1/marketplace/catalog",
            name="GET /catalog"
        )

        if response.status_code == 200:
            catalog = response.json()
            # Optionally validate response
            assert isinstance(catalog, list), "Catalog should be an array"

    @task(5)
    def search_catalog(self):
        """
        Search for specific add-ons

        Expected: <300ms response time
        """
        search_terms = ["tts", "storage", "analytics", "github", "premium"]
        search_term = random.choice(search_terms)

        self.client.get(
            f"/api/v1/marketplace/catalog?search={search_term}",
            name="GET /catalog (search)"
        )

    @task(3)
    def filter_by_category(self):
        """
        Filter add-ons by category

        Expected: <250ms response time
        """
        categories = ["ai-services", "storage", "integrations", "analytics"]
        category = random.choice(categories)

        self.client.get(
            f"/api/v1/marketplace/catalog?category={category}",
            name="GET /catalog (filter)"
        )

    @task(8)
    def add_to_cart(self):
        """
        Add item to shopping cart

        Expected: <150ms response time
        """
        addon_id = random.choice(self.addon_ids)

        response = self.client.post(
            "/api/v1/marketplace/cart/add",
            json={
                "addon_id": addon_id,
                "quantity": 1
            },
            name="POST /cart/add"
        )

        if response.status_code == 200:
            self.cart_items.append(addon_id)

    @task(2)
    def view_cart(self):
        """
        View cart contents

        Expected: <100ms response time
        """
        self.client.get(
            "/api/v1/marketplace/cart",
            name="GET /cart"
        )

    @task(1)
    def remove_from_cart(self):
        """
        Remove item from cart

        Expected: <150ms response time
        """
        if self.cart_items:
            addon_id = random.choice(self.cart_items)

            response = self.client.delete(
                f"/api/v1/marketplace/cart/{addon_id}",
                name="DELETE /cart/:id"
            )

            if response.status_code == 200:
                self.cart_items.remove(addon_id)

    @task(2)
    def apply_promo_code(self):
        """
        Apply promo code to cart

        Expected: <200ms response time
        """
        promo_code = random.choice(self.promo_codes)

        self.client.post(
            "/api/v1/marketplace/cart/promo",
            json={"promo_code": promo_code},
            name="POST /cart/promo"
        )

    @task(1)
    def create_checkout(self):
        """
        Create Stripe checkout session

        Expected: <500ms response time (includes Stripe API call)
        """
        if self.cart_items:
            self.client.post(
                "/api/v1/marketplace/checkout/create",
                json={"user_id": self.user_id},
                name="POST /checkout/create"
            )

    @task(1)
    def view_purchase_history(self):
        """
        View user's purchase history

        Expected: <300ms response time
        """
        self.client.get(
            f"/api/v1/marketplace/purchases?user_id={self.user_id}",
            name="GET /purchases"
        )


class AdminUser(HttpUser):
    """Simulated admin managing add-ons"""

    wait_time = between(2, 8)

    def on_start(self):
        """Admin authentication"""
        self.admin_token = "admin-auth-token-12345"
        self.client.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

    @task(5)
    def list_all_addons(self):
        """
        Admin views all add-ons (including inactive)

        Expected: <250ms response time
        """
        self.client.get(
            "/api/v1/admin/marketplace/addons",
            name="GET /admin/addons"
        )

    @task(1)
    def create_addon(self):
        """
        Admin creates new add-on

        Expected: <400ms response time
        """
        addon_data = {
            "name": f"Load Test Add-On {random.randint(1, 1000)}",
            "description": "Add-on created during load testing",
            "category": "test",
            "base_price": random.choice([4.99, 9.99, 19.99]),
            "billing_type": "monthly",
            "features": ["test_feature"],
            "is_active": False
        }

        self.client.post(
            "/api/v1/admin/marketplace/addons",
            json=addon_data,
            name="POST /admin/addons"
        )

    @task(2)
    def view_sales_analytics(self):
        """
        Admin views sales analytics

        Expected: <500ms response time
        """
        self.client.get(
            "/api/v1/admin/marketplace/analytics",
            name="GET /admin/analytics"
        )


class WebhookSimulator(HttpUser):
    """Simulated Stripe webhooks"""

    wait_time = between(10, 30)

    @task
    def send_payment_webhook(self):
        """
        Simulate Stripe webhook

        Expected: <300ms response time
        """
        webhook_event = {
            "id": f"evt_test_{random.randint(100000, 999999)}",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": f"cs_test_{random.randint(100000, 999999)}",
                    "payment_status": "paid",
                    "metadata": {
                        "user_id": f"user-{random.randint(1, 1000)}",
                        "addon_ids": '["tts-premium"]'
                    }
                }
            }
        }

        self.client.post(
            "/api/v1/marketplace/webhooks/stripe",
            json=webhook_event,
            headers={
                "Stripe-Signature": "test-signature-12345"
            },
            name="POST /webhooks/stripe"
        )


# Performance test scenarios

class LowLoadScenario(HttpUser):
    """Low load: 10 concurrent users"""
    tasks = [MarketplaceUser]
    weight = 10


class MediumLoadScenario(HttpUser):
    """Medium load: 50 concurrent users"""
    tasks = [MarketplaceUser]
    weight = 50


class HighLoadScenario(HttpUser):
    """High load: 100 concurrent users"""
    tasks = [MarketplaceUser]
    weight = 100


# Run configuration

"""
Performance Test Plan:

1. **Smoke Test** (sanity check):
   - Users: 5
   - Duration: 1 minute
   - Goal: Verify endpoints are functional

2. **Load Test** (normal traffic):
   - Users: 50
   - Duration: 5 minutes
   - Goal: Establish baseline performance

3. **Stress Test** (peak traffic):
   - Users: 100-200
   - Duration: 10 minutes
   - Goal: Identify breaking point

4. **Spike Test** (sudden traffic burst):
   - Start: 10 users
   - Spike to: 200 users in 30 seconds
   - Duration: 2 minutes
   - Goal: Test auto-scaling

5. **Soak Test** (sustained load):
   - Users: 50
   - Duration: 1 hour
   - Goal: Identify memory leaks

Success Criteria:
- 95th percentile response time < 500ms
- Error rate < 1%
- No memory leaks over 1 hour
- Database connections properly pooled
- Redis cache hit rate > 70%
"""
