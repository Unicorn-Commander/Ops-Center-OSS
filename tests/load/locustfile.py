"""
Locust Load Testing Suite for Ops-Center Billing System
========================================================

Simulates realistic user behavior patterns for billing endpoints.

Usage:
    locust -f locustfile.py --host=http://localhost:8084
    locust -f locustfile.py --host=http://localhost:8084 --users=100 --spawn-rate=10

Features:
- Realistic user workflows
- Different user personas (admin, org admin, end user)
- Weighted task distribution
- Authentication handling
- Performance metrics collection
"""

from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import RescheduleTask
import json
import random
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BillingWorkflow(SequentialTaskSet):
    """Sequential workflow simulating a user checking billing"""

    def on_start(self):
        """Setup before tasks"""
        self.org_id = None
        self.subscription_id = None

    @task
    def view_credit_balance(self):
        """Check credit balance"""
        response = self.client.get(
            "/api/v1/credits/balance",
            headers=self.get_auth_headers(),
            name="GET /credits/balance"
        )
        if response.status_code == 200:
            logger.info(f"Credit balance: {response.json().get('balance')}")

    @task
    def view_usage_summary(self):
        """Check usage summary"""
        response = self.client.get(
            "/api/v1/credits/usage/summary",
            headers=self.get_auth_headers(),
            name="GET /credits/usage/summary"
        )
        if response.status_code == 200:
            logger.info(f"API calls: {response.json().get('api_calls')}")

    @task
    def view_transactions(self):
        """View credit transactions"""
        response = self.client.get(
            "/api/v1/credits/transactions?limit=10",
            headers=self.get_auth_headers(),
            name="GET /credits/transactions"
        )
        if response.status_code == 200:
            logger.info(f"Transactions: {len(response.json().get('transactions', []))}")

    def get_auth_headers(self):
        """Get authentication headers"""
        # In real scenario, would use actual session token
        return {
            "Authorization": f"Bearer test_token_{self.user.user_id}",
            "Cookie": f"session_token=test_session_{self.user.user_id}"
        }


class OrgBillingWorkflow(SequentialTaskSet):
    """Organization admin checking org billing"""

    def on_start(self):
        """Setup org context"""
        self.org_id = f"org_{random.randint(1000, 9999)}"
        self.subscription_id = None

    @task
    def get_org_subscription(self):
        """Check organization subscription"""
        response = self.client.get(
            f"/api/v1/org-billing/organizations/{self.org_id}/subscription",
            headers=self.get_auth_headers(),
            name="GET /org-billing/subscription"
        )
        if response.status_code == 200:
            data = response.json()
            self.subscription_id = data.get('id')
            logger.info(f"Subscription plan: {data.get('subscription_plan')}")

    @task
    def get_credit_pool(self):
        """Check credit pool"""
        if not self.org_id:
            return

        response = self.client.get(
            f"/api/v1/org-billing/organizations/{self.org_id}/credit-pool",
            headers=self.get_auth_headers(),
            name="GET /org-billing/credit-pool"
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Available credits: {data.get('available_credits')}")

    @task
    def list_members(self):
        """List organization members"""
        response = self.client.get(
            f"/api/v1/org-billing/organizations/{self.org_id}/members",
            headers=self.get_auth_headers(),
            name="GET /org-billing/members"
        )
        if response.status_code == 200:
            members = response.json().get('members', [])
            logger.info(f"Organization members: {len(members)}")

    @task
    def get_usage_by_user(self):
        """Get usage breakdown by user"""
        response = self.client.get(
            f"/api/v1/org-billing/organizations/{self.org_id}/usage/users",
            headers=self.get_auth_headers(),
            name="GET /org-billing/usage/users"
        )
        if response.status_code == 200:
            usage = response.json().get('usage', [])
            logger.info(f"Users with usage: {len(usage)}")

    def get_auth_headers(self):
        """Get authentication headers with org admin role"""
        return {
            "Authorization": f"Bearer test_token_{self.user.user_id}",
            "Cookie": f"session_token=test_session_{self.user.user_id}",
            "X-Org-ID": self.org_id
        }


class AdminBillingWorkflow(SequentialTaskSet):
    """System admin checking all billing data"""

    @task
    def list_all_subscriptions(self):
        """List all organization subscriptions"""
        response = self.client.get(
            "/api/v1/org-billing/subscriptions",
            headers=self.get_auth_headers(),
            name="GET /org-billing/subscriptions (admin)"
        )
        if response.status_code == 200:
            subs = response.json().get('subscriptions', [])
            logger.info(f"Total subscriptions: {len(subs)}")

    @task
    def get_platform_analytics(self):
        """Get platform-wide analytics"""
        response = self.client.get(
            "/api/v1/org-billing/analytics/platform",
            headers=self.get_auth_headers(),
            name="GET /org-billing/analytics/platform"
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Total revenue: ${data.get('total_revenue', 0)}")

    @task
    def get_revenue_trends(self):
        """Get revenue trends"""
        response = self.client.get(
            "/api/v1/org-billing/analytics/revenue-trends?period=30d",
            headers=self.get_auth_headers(),
            name="GET /org-billing/analytics/revenue-trends"
        )
        if response.status_code == 200:
            trends = response.json().get('trends', [])
            logger.info(f"Revenue data points: {len(trends)}")

    def get_auth_headers(self):
        """Get admin authentication headers"""
        return {
            "Authorization": f"Bearer admin_token_{self.user.user_id}",
            "Cookie": f"session_token=admin_session_{self.user.user_id}",
            "X-Admin": "true"
        }


class EndUser(HttpUser):
    """End user persona - checks credits and usage"""
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    weight = 10  # 10x more end users than other types

    def on_start(self):
        """Initialize user"""
        self.user_id = f"user_{random.randint(10000, 99999)}"
        logger.info(f"End user started: {self.user_id}")

    @task(5)
    def check_balance(self):
        """Check credit balance (most common action)"""
        self.client.get(
            "/api/v1/credits/balance",
            headers={"Authorization": f"Bearer token_{self.user_id}"},
            name="GET /credits/balance (end user)"
        )

    @task(3)
    def check_usage(self):
        """Check usage statistics"""
        self.client.get(
            "/api/v1/credits/usage/summary",
            headers={"Authorization": f"Bearer token_{self.user_id}"},
            name="GET /credits/usage/summary (end user)"
        )

    @task(2)
    def view_transactions(self):
        """View transaction history"""
        self.client.get(
            "/api/v1/credits/transactions?limit=20",
            headers={"Authorization": f"Bearer token_{self.user_id}"},
            name="GET /credits/transactions (end user)"
        )

    @task(1)
    def purchase_credits(self):
        """Simulate credit purchase"""
        self.client.post(
            "/api/v1/credits/purchase",
            headers={"Authorization": f"Bearer token_{self.user_id}"},
            json={
                "amount": random.choice([1000, 5000, 10000]),
                "payment_method": "stripe"
            },
            name="POST /credits/purchase"
        )


class OrgAdmin(HttpUser):
    """Organization admin persona"""
    wait_time = between(5, 10)  # Slower pace
    weight = 2  # Fewer org admins

    tasks = [OrgBillingWorkflow]

    def on_start(self):
        """Initialize org admin"""
        self.user_id = f"org_admin_{random.randint(1000, 9999)}"
        logger.info(f"Org admin started: {self.user_id}")


class SystemAdmin(HttpUser):
    """System admin persona"""
    wait_time = between(10, 20)  # Even slower, more analysis
    weight = 1  # Very few system admins

    tasks = [AdminBillingWorkflow]

    def on_start(self):
        """Initialize system admin"""
        self.user_id = f"admin_{random.randint(100, 999)}"
        logger.info(f"System admin started: {self.user_id}")


# ============================================================================
# Custom Test Scenarios
# ============================================================================

class SpikeTest(HttpUser):
    """Spike test - sudden load increase"""
    wait_time = between(0.1, 0.5)  # Very fast requests

    @task
    def spike_read(self):
        """Rapid read operations"""
        self.client.get(
            "/api/v1/credits/balance",
            name="Spike test - balance check"
        )


class StressTest(HttpUser):
    """Stress test - sustained high load"""
    wait_time = between(0.5, 1)  # Fast but sustainable

    @task(5)
    def stress_read(self):
        """High-frequency reads"""
        self.client.get(
            "/api/v1/credits/balance",
            name="Stress test - reads"
        )

    @task(1)
    def stress_write(self):
        """Some writes mixed in"""
        self.client.post(
            "/api/v1/credits/usage/track",
            json={
                "operation": "api_call",
                "credits_used": random.randint(1, 10)
            },
            name="Stress test - writes"
        )


if __name__ == "__main__":
    # Can be run directly for local testing
    import os
    os.system("locust -f locustfile.py --host=http://localhost:8084")
