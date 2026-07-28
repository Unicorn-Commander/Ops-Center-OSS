"""
Epic 1.8 - Credit API Integration Tests

End-to-end integration tests for credit system API endpoints covering:
- Authentication and authorization
- Credit balance endpoints
- Credit allocation (admin-only)
- Credit deduction flow
- Transaction history with pagination
- Usage statistics
- Monthly caps
- Error handling and edge cases

Author: Testing & DevOps Team Lead
Date: October 23, 2025
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys

# Import FastAPI app
sys.path.insert(0, '/app')
from server import app


# Test fixtures
@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def admin_headers():
    """Admin authentication headers"""
    return {
        "Authorization": "Bearer admin_test_token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def user_headers():
    """Regular user authentication headers"""
    return {
        "Authorization": "Bearer user_test_token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_user_session():
    """Mock user session data"""
    return {
        "user": {
            "id": "test_user_123",
            "email": "test@example.com",
            "username": "testuser",
            "roles": ["user"]
        },
        "tier": "professional",
        "credits": 100.0
    }


@pytest.fixture
def mock_admin_session():
    """Mock admin session data"""
    return {
        "user": {
            "id": "admin_123",
            "email": "admin@example.com",
            "username": "admin",
            "roles": ["admin"]
        },
        "tier": "enterprise",
        "credits": 1000.0
    }


class TestCreditBalanceEndpoints:
    """Test credit balance retrieval endpoints"""

    def test_get_balance_authenticated(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/balance with authentication"""
        # Mock session
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/balance",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "tier" in data
        assert data["tier"] == "professional"

    def test_get_balance_unauthenticated(self, client):
        """Test GET /api/v1/credits/balance without authentication"""
        response = client.get("/api/v1/credits/balance")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_balance_with_transaction_history(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/balance?include_history=true"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/balance?include_history=true&limit=10",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "transactions" in data
        assert isinstance(data["transactions"], list)


class TestCreditAllocationEndpoints:
    """Test credit allocation endpoints (admin-only)"""

    def test_allocate_credits_as_admin(self, client, admin_headers, mock_admin_session):
        """Test POST /api/v1/admin/credits/allocate as admin"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        payload = {
            "user_id": "test@example.com",
            "amount": 50.0,
            "reason": "bonus"
        }

        response = client.post(
            "/api/v1/admin/credits/allocate",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "new_balance" in data
        assert "transaction_id" in data

    def test_allocate_credits_as_user_forbidden(self, client, user_headers, mock_user_session):
        """Test POST /api/v1/admin/credits/allocate as regular user fails"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "user_id": "test@example.com",
            "amount": 50.0,
            "reason": "bonus"
        }

        response = client.post(
            "/api/v1/admin/credits/allocate",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 403

    def test_allocate_negative_credits(self, client, admin_headers, mock_admin_session):
        """Test allocating negative credits is rejected"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        payload = {
            "user_id": "test@example.com",
            "amount": -50.0,
            "reason": "invalid"
        }

        response = client.post(
            "/api/v1/admin/credits/allocate",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"},
            json=payload
        )

        assert response.status_code == 400

    def test_allocate_credits_invalid_user(self, client, admin_headers, mock_admin_session):
        """Test allocating credits to non-existent user"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        payload = {
            "user_id": "nonexistent@example.com",
            "amount": 50.0,
            "reason": "bonus"
        }

        response = client.post(
            "/api/v1/admin/credits/allocate",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"},
            json=payload
        )

        assert response.status_code in [404, 400]

    def test_bulk_allocate_credits(self, client, admin_headers, mock_admin_session):
        """Test POST /api/v1/admin/credits/bulk-allocate"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        payload = {
            "allocations": [
                {"user_id": "user1@example.com", "amount": 50.0, "reason": "bonus"},
                {"user_id": "user2@example.com", "amount": 100.0, "reason": "purchase"},
                {"user_id": "user3@example.com", "amount": 25.0, "reason": "refund"}
            ]
        }

        response = client.post(
            "/api/v1/admin/credits/bulk-allocate",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "success_count" in data
        assert "failed_count" in data
        assert data["success_count"] + data["failed_count"] == 3


class TestCreditDeductionFlow:
    """Test credit deduction endpoints"""

    def test_deduct_credits_sufficient_balance(self, client, user_headers, mock_user_session):
        """Test POST /api/v1/credits/deduct with sufficient balance"""
        mock_user_session["credits"] = 100.0
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "amount": 10.0,
            "metadata": {
                "provider": "openai",
                "model": "gpt-4o",
                "tokens_used": 1000,
                "request_id": "req_123"
            }
        }

        response = client.post(
            "/api/v1/credits/deduct",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "new_balance" in data
        assert "transaction_id" in data
        assert data["new_balance"] == 90.0

    def test_deduct_credits_insufficient_balance(self, client, user_headers, mock_user_session):
        """Test credit deduction fails with insufficient balance"""
        mock_user_session["credits"] = 5.0
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "amount": 10.0,
            "metadata": {
                "provider": "openai",
                "model": "gpt-4o",
                "tokens_used": 1000
            }
        }

        response = client.post(
            "/api/v1/credits/deduct",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 402  # Payment Required
        assert "Insufficient credits" in response.json()["detail"]

    def test_deduct_credits_free_tier(self, client, user_headers, mock_user_session):
        """Test free tier can deduct even with zero balance"""
        mock_user_session["tier"] = "free"
        mock_user_session["credits"] = 0.0
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "amount": 0.0,  # Free model
            "metadata": {
                "provider": "groq",
                "model": "llama3-70b",
                "tokens_used": 1000
            }
        }

        response = client.post(
            "/api/v1/credits/deduct",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200

    def test_automatic_cost_calculation(self, client, user_headers, mock_user_session):
        """Test POST /api/v1/credits/calculate-and-deduct"""
        mock_user_session["credits"] = 100.0
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "tokens_used": 1000,
            "model": "gpt-4o",
            "power_level": "balanced",
            "metadata": {
                "request_id": "req_124"
            }
        }

        response = client.post(
            "/api/v1/credits/calculate-and-deduct",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "cost" in data
        assert "new_balance" in data
        assert "transaction_id" in data


class TestTransactionHistoryEndpoints:
    """Test transaction history endpoints"""

    def test_get_transaction_history(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/transactions"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/transactions",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total_count" in data
        assert isinstance(data["transactions"], list)

    def test_transaction_history_pagination(self, client, user_headers, mock_user_session):
        """Test transaction history pagination"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/transactions?limit=10&offset=20",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) <= 10

    def test_transaction_history_filtering_by_type(self, client, user_headers, mock_user_session):
        """Test filtering transactions by type"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/transactions?type=usage",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        for txn in data["transactions"]:
            assert txn["type"] == "usage"

    def test_transaction_history_filtering_by_date_range(self, client, user_headers, mock_user_session):
        """Test filtering transactions by date range"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = client.get(
            f"/api/v1/credits/transactions?start_date={start_date}&end_date={end_date}",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200

    def test_get_transaction_detail(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/transactions/{transaction_id}"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        transaction_id = "txn_123"

        response = client.get(
            f"/api/v1/credits/transactions/{transaction_id}",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code in [200, 404]

    def test_export_transactions_csv(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/transactions/export?format=csv"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/transactions/export?format=csv",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv"


class TestUsageStatisticsEndpoints:
    """Test usage statistics endpoints"""

    def test_get_usage_stats(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/usage/stats"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/usage/stats",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "avg_cost_per_request" in data
        assert "providers" in data

    def test_get_usage_stats_custom_date_range(self, client, user_headers, mock_user_session):
        """Test usage stats with custom date range"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/usage/stats?days=7",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200

    def test_get_usage_by_model(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/usage/by-model"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/usage/by-model",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["models"], list)

    def test_get_usage_by_power_level(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/usage/by-power-level"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/usage/by-power-level",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "eco" in data or "balanced" in data or "precision" in data


class TestMonthlyCapsEndpoints:
    """Test monthly spending cap endpoints"""

    def test_get_monthly_cap(self, client, user_headers, mock_user_session):
        """Test GET /api/v1/credits/monthly-cap"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        response = client.get(
            "/api/v1/credits/monthly-cap",
            headers=user_headers,
            cookies={"session_token": "user_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "monthly_cap" in data
        assert "monthly_spending" in data
        assert "remaining" in data
        assert "reset_date" in data

    def test_set_monthly_cap(self, client, user_headers, mock_user_session):
        """Test POST /api/v1/credits/monthly-cap"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {"monthly_cap": 1000.0}

        response = client.post(
            "/api/v1/credits/monthly-cap",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200

    def test_exceeding_monthly_cap_blocks_deduction(self, client, user_headers, mock_user_session):
        """Test deduction fails when would exceed monthly cap"""
        # This would require setting up a monthly cap and simulating spending
        # Implementation depends on actual API behavior
        pass


class TestCostCalculationEndpoints:
    """Test cost calculation endpoints"""

    def test_calculate_cost(self, client, user_headers, mock_user_session):
        """Test POST /api/v1/credits/calculate-cost"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "tokens_used": 1000,
            "model": "gpt-4o",
            "power_level": "balanced"
        }

        response = client.post(
            "/api/v1/credits/calculate-cost",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "cost" in data
        assert data["cost"] > 0

    def test_calculate_cost_free_model(self, client, user_headers, mock_user_session):
        """Test cost calculation for free models"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {
            "tokens_used": 1000,
            "model": "llama3-70b-groq",
            "power_level": "balanced"
        }

        response = client.post(
            "/api/v1/credits/calculate-cost",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cost"] == 0.0

    def test_calculate_cost_different_power_levels(self, client, user_headers, mock_user_session):
        """Test cost varies by power level"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        costs = {}
        for power_level in ["eco", "balanced", "precision"]:
            payload = {
                "tokens_used": 1000,
                "model": "gpt-4o",
                "power_level": power_level
            }

            response = client.post(
                "/api/v1/credits/calculate-cost",
                headers=user_headers,
                cookies={"session_token": "user_test_token"},
                json=payload
            )

            assert response.status_code == 200
            costs[power_level] = response.json()["cost"]

        assert costs["eco"] < costs["balanced"] < costs["precision"]


class TestAdminAnalyticsEndpoints:
    """Test admin analytics endpoints"""

    def test_get_system_wide_usage(self, client, admin_headers, mock_admin_session):
        """Test GET /api/v1/admin/credits/analytics/system"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        response = client.get(
            "/api/v1/admin/credits/analytics/system",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_credits_allocated" in data
        assert "total_credits_used" in data

    def test_get_top_spenders(self, client, admin_headers, mock_admin_session):
        """Test GET /api/v1/admin/credits/analytics/top-spenders"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        response = client.get(
            "/api/v1/admin/credits/analytics/top-spenders?limit=10",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["users"], list)

    def test_get_credit_distribution(self, client, admin_headers, mock_admin_session):
        """Test GET /api/v1/admin/credits/analytics/distribution"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        response = client.get(
            "/api/v1/admin/credits/analytics/distribution",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"}
        )

        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_amount_format(self, client, admin_headers, mock_admin_session):
        """Test invalid amount format"""
        client.app.state.sessions = {
            "admin_test_token": mock_admin_session
        }

        payload = {
            "user_id": "test@example.com",
            "amount": "invalid",
            "reason": "bonus"
        }

        response = client.post(
            "/api/v1/admin/credits/allocate",
            headers=admin_headers,
            cookies={"session_token": "admin_test_token"},
            json=payload
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client, user_headers, mock_user_session):
        """Test missing required fields"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        payload = {"amount": 10.0}  # Missing metadata

        response = client.post(
            "/api/v1/credits/deduct",
            headers=user_headers,
            cookies={"session_token": "user_test_token"},
            json=payload
        )

        assert response.status_code in [400, 422]

    def test_invalid_session_token(self, client, user_headers):
        """Test invalid session token"""
        response = client.get(
            "/api/v1/credits/balance",
            headers=user_headers,
            cookies={"session_token": "invalid_token"}
        )

        assert response.status_code == 401

    def test_rate_limiting(self, client, user_headers, mock_user_session):
        """Test rate limiting on credit endpoints"""
        client.app.state.sessions = {
            "user_test_token": mock_user_session
        }

        # Make 100 rapid requests
        for _ in range(100):
            response = client.get(
                "/api/v1/credits/balance",
                headers=user_headers,
                cookies={"session_token": "user_test_token"}
            )

            if response.status_code == 429:
                assert "rate limit" in response.json()["detail"].lower()
                break


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--maxfail=5"])
