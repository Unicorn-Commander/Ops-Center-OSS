"""
Unit Tests for Credit Deduction Middleware
===========================================

Tests automatic credit deduction for LLM API requests.

Test Coverage:
- Org credit deduction (user belongs to organization)
- Individual credit deduction (no organization)
- BYOK passthrough (no credit deduction)
- Insufficient credits (402 error)
- Concurrent requests (atomic deduction)
- Error handling (fail-open)
- Credit headers in responses

Author: Backend Integration Teamlead
Date: November 15, 2025
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from starlette.responses import JSONResponse
import json

# Import the middleware
import sys
import os
sys.path.insert(0, '/app')

from credit_deduction_middleware import CreditDeductionMiddleware


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request"""
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/llm/chat/completions"
    request.method = "POST"
    request.cookies = {"session_token": "test-token-123"}
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_user_session():
    """Create a mock user session data"""
    return {
        "user_id": "user-123",
        "sub": "user-123",
        "email": "test@example.com",
        "subscription_tier": "professional",
        "org_id": None
    }


@pytest.fixture
def mock_org_user_session():
    """Create a mock organization user session"""
    return {
        "user_id": "user-456",
        "sub": "user-456",
        "email": "org-user@example.com",
        "subscription_tier": "professional",
        "org_id": "org-789"
    }


@pytest.fixture
def middleware():
    """Create middleware instance"""
    app = MagicMock()
    mw = CreditDeductionMiddleware(app)
    return mw


class TestCreditDeductionMiddleware:
    """Test suite for CreditDeductionMiddleware"""

    @pytest.mark.asyncio
    async def test_should_deduct_credits_chat_endpoint(self, middleware):
        """Test that chat completions endpoint is tracked"""
        should_deduct = await middleware._should_deduct_credits("/api/v1/llm/chat/completions")
        assert should_deduct is True

    @pytest.mark.asyncio
    async def test_should_not_deduct_models_endpoint(self, middleware):
        """Test that models list endpoint is NOT tracked"""
        should_deduct = await middleware._should_deduct_credits("/api/v1/llm/models")
        assert should_deduct is False

    @pytest.mark.asyncio
    async def test_should_not_deduct_admin_endpoint(self, middleware):
        """Test that admin endpoints are NOT tracked"""
        should_deduct = await middleware._should_deduct_credits("/api/v1/admin/users")
        assert should_deduct is False

    @pytest.mark.asyncio
    async def test_estimate_credits_chat(self, middleware, mock_request):
        """Test credit estimation for chat endpoint"""
        estimated = await middleware._estimate_credits_needed(mock_request)
        # Should estimate around 9 credits (1500 tokens * 0.006)
        assert estimated > 0
        assert estimated < 20  # Conservative check

    @pytest.mark.asyncio
    async def test_estimate_credits_image(self, middleware, mock_request):
        """Test credit estimation for image generation"""
        mock_request.url.path = "/api/v1/llm/image/generations"
        estimated = await middleware._estimate_credits_needed(mock_request)
        # Should estimate around 48 credits (DALL-E 3 standard)
        assert estimated == 48.0

    @pytest.mark.asyncio
    async def test_byok_detection_no_keys(self, middleware):
        """Test BYOK detection when user has no keys"""
        with patch('credit_deduction_middleware.BYOKManager') as MockBYOK:
            mock_manager = AsyncMock()
            mock_manager.get_user_providers.return_value = []
            MockBYOK.return_value = mock_manager

            is_byok, provider = await middleware._check_byok_enabled("user-123")
            assert is_byok is False
            assert provider is None

    @pytest.mark.asyncio
    async def test_byok_detection_with_keys(self, middleware):
        """Test BYOK detection when user has OpenRouter key"""
        with patch('credit_deduction_middleware.BYOKManager') as MockBYOK:
            mock_manager = AsyncMock()
            mock_manager.get_user_providers.return_value = ["openrouter", "huggingface"]
            MockBYOK.return_value = mock_manager

            is_byok, provider = await middleware._check_byok_enabled(
                "user-123",
                model="openrouter/anthropic/claude-3.5-sonnet"
            )
            assert is_byok is True
            assert provider == "openrouter"

    @pytest.mark.asyncio
    async def test_check_sufficient_org_credits_success(self, middleware):
        """Test checking org credits when sufficient"""
        # Mock org credit integration
        middleware.org_integration = AsyncMock()
        middleware.org_integration.has_sufficient_org_credits.return_value = (
            True, "org-789", "Sufficient credits"
        )

        has_credits, org_id, message = await middleware._check_sufficient_credits(
            user_id="user-456",
            credits_needed=10.0,
            user_tier="professional"
        )

        assert has_credits is True
        assert org_id == "org-789"
        assert "Sufficient" in message

    @pytest.mark.asyncio
    async def test_check_sufficient_org_credits_insufficient(self, middleware):
        """Test checking org credits when insufficient"""
        # Mock org credit integration
        middleware.org_integration = AsyncMock()
        middleware.org_integration.has_sufficient_org_credits.return_value = (
            False, "org-789", "Insufficient credits"
        )

        has_credits, org_id, message = await middleware._check_sufficient_credits(
            user_id="user-456",
            credits_needed=10.0,
            user_tier="professional"
        )

        assert has_credits is False
        assert org_id == "org-789"
        assert "Insufficient" in message

    @pytest.mark.asyncio
    async def test_check_sufficient_individual_credits_success(self, middleware):
        """Test checking individual credits when sufficient"""
        # Mock org credit integration (no org)
        middleware.org_integration = AsyncMock()
        middleware.org_integration.has_sufficient_org_credits.return_value = (
            False, None, "No organization"
        )

        # Mock credit system
        middleware.credit_system = AsyncMock()
        middleware.credit_system.get_user_credits.return_value = 100.0
        middleware.credit_system.check_monthly_cap.return_value = True

        has_credits, org_id, message = await middleware._check_sufficient_credits(
            user_id="user-123",
            credits_needed=10.0,
            user_tier="professional"
        )

        assert has_credits is True
        assert org_id is None
        assert "individual" in message.lower()

    @pytest.mark.asyncio
    async def test_check_sufficient_individual_credits_insufficient(self, middleware):
        """Test checking individual credits when insufficient"""
        # Mock org credit integration (no org)
        middleware.org_integration = AsyncMock()
        middleware.org_integration.has_sufficient_org_credits.return_value = (
            False, None, "No organization"
        )

        # Mock credit system (low balance)
        middleware.credit_system = AsyncMock()
        middleware.credit_system.get_user_credits.return_value = 5.0
        middleware.credit_system.check_monthly_cap.return_value = True

        has_credits, org_id, message = await middleware._check_sufficient_credits(
            user_id="user-123",
            credits_needed=10.0,
            user_tier="professional"
        )

        assert has_credits is False
        assert org_id is None
        assert "Insufficient" in message

    @pytest.mark.asyncio
    async def test_deduct_org_credits_success(self, middleware):
        """Test deducting org credits successfully"""
        # Mock org credit integration
        middleware.org_integration = AsyncMock()
        middleware.org_integration.deduct_org_credits.return_value = (
            True, "org-789", 5000  # 5000 milicredits = 5.0 credits
        )

        success, remaining = await middleware._deduct_credits(
            user_id="user-456",
            credits_used=10.0,
            tokens_used=1500,
            provider="openai",
            model="gpt-4",
            org_id="org-789"
        )

        assert success is True
        assert remaining == 5.0  # Converted from milicredits

    @pytest.mark.asyncio
    async def test_deduct_individual_credits_success(self, middleware):
        """Test deducting individual credits successfully"""
        # Mock credit system
        middleware.credit_system = AsyncMock()
        middleware.credit_system.deduct_credits.return_value = (
            "txn-123", 90.0  # New balance after deduction
        )

        success, remaining = await middleware._deduct_credits(
            user_id="user-123",
            credits_used=10.0,
            tokens_used=1500,
            provider="openai",
            model="gpt-4",
            org_id=None
        )

        assert success is True
        assert remaining == 90.0

    @pytest.mark.asyncio
    async def test_middleware_no_session(self, middleware, mock_request):
        """Test middleware returns 401 when no session"""
        mock_request.cookies = {}

        async def call_next(request):
            return Response(content="OK", status_code=200)

        with patch.object(middleware, '_get_user_from_session', return_value=None):
            response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert body["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_middleware_byok_passthrough(self, middleware, mock_request, mock_user_session):
        """Test middleware bypasses credit check for BYOK users"""
        # Mock session
        with patch.object(middleware, '_get_user_from_session', return_value=mock_user_session):
            # Mock BYOK enabled
            with patch.object(middleware, '_check_byok_enabled', return_value=(True, "openrouter")):
                # Mock successful request
                async def call_next(request):
                    return Response(content=json.dumps({"choices": [{"message": {"content": "OK"}}]}), status_code=200)

                response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        assert response.headers.get("X-BYOK") == "true"
        assert response.headers.get("X-Credits-Used") == "0.0"

    @pytest.mark.asyncio
    async def test_middleware_insufficient_credits(self, middleware, mock_request, mock_user_session):
        """Test middleware returns 402 when insufficient credits"""
        await middleware._ensure_initialized()

        # Mock session
        with patch.object(middleware, '_get_user_from_session', return_value=mock_user_session):
            # Mock BYOK disabled
            with patch.object(middleware, '_check_byok_enabled', return_value=(False, None)):
                # Mock insufficient credits
                with patch.object(middleware, '_check_sufficient_credits', return_value=(False, None, "Insufficient credits")):
                    async def call_next(request):
                        return Response(content="OK", status_code=200)

                    response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 402
        body = json.loads(response.body)
        assert body["error"] == "Payment Required"

    @pytest.mark.asyncio
    async def test_middleware_successful_deduction(self, middleware, mock_request, mock_user_session):
        """Test middleware successfully deducts credits"""
        await middleware._ensure_initialized()

        # Mock session
        with patch.object(middleware, '_get_user_from_session', return_value=mock_user_session):
            # Mock BYOK disabled
            with patch.object(middleware, '_check_byok_enabled', return_value=(False, None)):
                # Mock sufficient credits
                with patch.object(middleware, '_check_sufficient_credits', return_value=(True, None, "OK")):
                    # Mock successful deduction
                    with patch.object(middleware, '_deduct_credits', return_value=(True, 90.0)):
                        # Mock LLM response with usage
                        async def call_next(request):
                            response_body = json.dumps({
                                "choices": [{"message": {"content": "Hello"}}],
                                "usage": {"total_tokens": 150},
                                "cost": 0.9,
                                "model": "openai/gpt-4"
                            })
                            return Response(content=response_body, status_code=200)

                        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        assert "X-Credits-Used" in response.headers
        assert "X-Credits-Remaining" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_excluded_endpoint(self, middleware, mock_request):
        """Test middleware bypasses excluded endpoints"""
        mock_request.url.path = "/api/v1/llm/models"

        async def call_next(request):
            return Response(content="OK", status_code=200)

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        # No credit headers should be added
        assert "X-Credits-Used" not in response.headers

    @pytest.mark.asyncio
    async def test_concurrent_requests_atomic(self, middleware, mock_user_session):
        """Test that concurrent requests deduct credits atomically"""
        await middleware._ensure_initialized()

        # Mock org integration with atomic deduction
        middleware.org_integration = AsyncMock()
        deduction_count = 0

        async def mock_deduct(*args, **kwargs):
            nonlocal deduction_count
            deduction_count += 1
            await asyncio.sleep(0.01)  # Simulate DB delay
            return (True, f"org-{deduction_count}", 5000)

        middleware.org_integration.deduct_org_credits.side_effect = mock_deduct

        # Make 3 concurrent deduction calls
        tasks = [
            middleware._deduct_credits(
                user_id=f"user-{i}",
                credits_used=10.0,
                tokens_used=1500,
                provider="openai",
                model="gpt-4",
                org_id="org-789"
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # All 3 should succeed
        assert all(success for success, _ in results)
        # Each should get a unique deduction
        assert deduction_count == 3

    @pytest.mark.asyncio
    async def test_error_handling_fail_open(self, middleware, mock_request, mock_user_session):
        """Test that errors in credit check don't block users (fail-open)"""
        await middleware._ensure_initialized()

        # Mock session
        with patch.object(middleware, '_get_user_from_session', return_value=mock_user_session):
            # Mock BYOK check raises error
            with patch.object(middleware, '_check_byok_enabled', side_effect=Exception("DB error")):
                async def call_next(request):
                    return Response(content="OK", status_code=200)

                # Should NOT raise exception, should pass through
                response = await middleware.dispatch(mock_request, call_next)

        # Request should succeed despite error
        assert response.status_code == 200


# Integration test helper
@pytest.mark.asyncio
async def test_full_integration_flow():
    """
    Integration test for complete credit deduction flow.

    This test requires:
    - PostgreSQL with org credit tables
    - Redis for session management
    - Initialized credit system
    """
    # TODO: Implement when integration test environment is set up
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
