"""
Integration Tests for OpenRouter API

Tests the OpenRouter client and automation manager with mocked API responses.

Author: Integration Team Lead
Date: October 24, 2025
Epic: 2.2 - OpenRouter Integration
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import httpx

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from openrouter_client import (
    OpenRouterClient,
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError
)
from openrouter_automation import OpenRouterManager, OpenRouterError


class TestOpenRouterClient:
    """Test OpenRouter API client functionality"""

    @pytest.mark.asyncio
    async def test_get_models_success(self):
        """Test successful model retrieval"""
        mock_response = {
            "data": [
                {
                    "id": "meta-llama/llama-3.1-8b-instruct:free",
                    "name": "Llama 3.1 8B Instruct (free)",
                    "pricing": {"prompt": "0", "completion": "0"}
                },
                {
                    "id": "openai/gpt-4",
                    "name": "GPT-4",
                    "pricing": {"prompt": "0.03", "completion": "0.06"}
                }
            ]
        }

        async with OpenRouterClient("test-key") as client:
            with patch.object(client, '_make_request', return_value=mock_response):
                models = await client.get_models()

                assert len(models) == 2
                assert models[0]["id"] == "meta-llama/llama-3.1-8b-instruct:free"
                assert models[1]["id"] == "openai/gpt-4"

    @pytest.mark.asyncio
    async def test_get_key_info_success(self):
        """Test successful API key info retrieval"""
        mock_response = {
            "data": {
                "label": "Test Key",
                "limit": 10.0,
                "usage": 3.5,
                "limit_remaining": 6.5,
                "rate_limit": {
                    "requests": 20,
                    "interval": "minute"
                }
            }
        }

        async with OpenRouterClient("test-key") as client:
            with patch.object(client, '_make_request', return_value=mock_response):
                key_info = await client.get_key_info()

                assert key_info["label"] == "Test Key"
                assert key_info["limit"] == 10.0
                assert key_info["limit_remaining"] == 6.5

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test authentication error handling"""
        async with OpenRouterClient("invalid-key") as client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": {"message": "Invalid API key"}
            }
            mock_response.content = b'{"error": {"message": "Invalid API key"}}'

            with patch.object(client._client, 'request', side_effect=httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_response
            )):
                with pytest.raises(OpenRouterAuthError):
                    await client._make_request("GET", "/models")

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate limit error handling with retry"""
        async with OpenRouterClient("test-key") as client:
            # First call returns 429, second call succeeds
            call_count = 0

            async def mock_request(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    mock_response = MagicMock()
                    mock_response.status_code = 429
                    mock_response.headers = {"Retry-After": "1"}
                    mock_response.content = b'{"error": "Rate limit exceeded"}'
                    raise httpx.HTTPStatusError(
                        "429 Too Many Requests",
                        request=MagicMock(),
                        response=mock_response
                    )
                else:
                    # Return success on retry
                    return {"data": []}

            with patch.object(client._client, 'request', side_effect=mock_request):
                # Should succeed after retry
                result = await client._make_request("GET", "/models")
                assert result == {"data": []}
                assert call_count == 2

    @pytest.mark.asyncio
    async def test_chat_completion(self):
        """Test chat completion request"""
        mock_response = {
            "id": "gen-123",
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }

        async with OpenRouterClient("test-key") as client:
            with patch.object(client, '_make_request', return_value=mock_response):
                response = await client.chat_completion(
                    model="meta-llama/llama-3.1-8b-instruct:free",
                    messages=[{"role": "user", "content": "Hello"}]
                )

                assert response["id"] == "gen-123"
                assert response["choices"][0]["message"]["content"] == "Hello! How can I help you?"
                assert response["usage"]["total_tokens"] == 18


class TestOpenRouterManager:
    """Test OpenRouter automation manager"""

    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        pool.acquire = AsyncMock()
        return pool

    @pytest.fixture
    def mock_api_client(self):
        """Mock OpenRouter API client"""
        client = AsyncMock(spec=OpenRouterClient)
        return client

    @pytest.mark.asyncio
    async def test_detect_free_models(self, mock_api_client):
        """Test free model detection from API"""
        mock_models = [
            {
                "id": "meta-llama/llama-3.1-8b-instruct:free",
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "deepseek/deepseek-r1:free",
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "openai/gpt-4",
                "pricing": {"prompt": "0.03", "completion": "0.06"}
            }
        ]

        manager = OpenRouterManager()
        manager.api_client = mock_api_client
        mock_api_client.get_models.return_value = mock_models

        free_models = await manager.detect_free_models()

        assert len(free_models) == 2
        assert "meta-llama/llama-3.1-8b-instruct:free" in free_models
        assert "deepseek/deepseek-r1:free" in free_models
        assert "openai/gpt-4" not in free_models

    @pytest.mark.asyncio
    async def test_detect_free_model_pattern(self):
        """Test pattern-based free model detection"""
        manager = OpenRouterManager()

        # Should detect :free suffix
        assert manager.detect_free_model("meta-llama/llama-3.1-8b-instruct:free") is True

        # Should detect known patterns
        assert manager.detect_free_model("llama-2-7b") is True
        assert manager.detect_free_model("mistral-7b-instruct") is True

        # Should not detect paid models
        assert manager.detect_free_model("openai/gpt-4") is False
        assert manager.detect_free_model("anthropic/claude-3") is False

    @pytest.mark.asyncio
    async def test_calculate_markup_free_model(self):
        """Test markup calculation for free models"""
        manager = OpenRouterManager()

        # Mock Keycloak service
        with patch('openrouter_automation.keycloak_service') as mock_keycloak:
            mock_keycloak.get_user_attributes.return_value = {
                "subscription_tier": "professional"
            }

            markup, total, reason = await manager.calculate_markup(
                user_id="user-123",
                model="meta-llama/llama-3.1-8b-instruct:free",
                provider_cost=Decimal("0.00")
            )

            # Free models should have 0% markup
            assert markup == Decimal("0.00")
            assert total == Decimal("0.00")
            assert reason == "free_model"

    @pytest.mark.asyncio
    async def test_calculate_markup_trial_tier(self):
        """Test markup calculation for trial tier"""
        manager = OpenRouterManager()

        # Mock Keycloak service
        with patch('openrouter_automation.keycloak_service') as mock_keycloak:
            mock_keycloak.get_user_attributes.return_value = {
                "subscription_tier": "trial"
            }

            provider_cost = Decimal("1.00")
            markup, total, reason = await manager.calculate_markup(
                user_id="user-123",
                model="openai/gpt-4",
                provider_cost=provider_cost
            )

            # Trial tier should have 15% markup
            expected_markup = Decimal("0.15")
            expected_total = Decimal("1.15")

            assert markup == expected_markup
            assert total == expected_total
            assert reason == "trial_tier_15pct"

    @pytest.mark.asyncio
    async def test_calculate_markup_professional_tier(self):
        """Test markup calculation for professional tier"""
        manager = OpenRouterManager()

        # Mock Keycloak service
        with patch('openrouter_automation.keycloak_service') as mock_keycloak:
            mock_keycloak.get_user_attributes.return_value = {
                "subscription_tier": "professional"
            }

            provider_cost = Decimal("1.00")
            markup, total, reason = await manager.calculate_markup(
                user_id="user-123",
                model="openai/gpt-4",
                provider_cost=provider_cost
            )

            # Professional tier should have 5% markup
            expected_markup = Decimal("0.05")
            expected_total = Decimal("1.05")

            assert markup == expected_markup
            assert total == expected_total
            assert reason == "professional_tier_5pct"

    @pytest.mark.asyncio
    async def test_calculate_markup_enterprise_tier(self):
        """Test markup calculation for enterprise tier"""
        manager = OpenRouterManager()

        # Mock Keycloak service
        with patch('openrouter_automation.keycloak_service') as mock_keycloak:
            mock_keycloak.get_user_attributes.return_value = {
                "subscription_tier": "enterprise"
            }

            provider_cost = Decimal("1.00")
            markup, total, reason = await manager.calculate_markup(
                user_id="user-123",
                model="openai/gpt-4",
                provider_cost=provider_cost
            )

            # Enterprise tier should have 0% markup
            expected_markup = Decimal("0.00")
            expected_total = Decimal("1.00")

            assert markup == expected_markup
            assert total == expected_total
            assert reason == "enterprise_tier_0pct"

    @pytest.mark.asyncio
    async def test_sync_free_credits_success(self, mock_db_pool, mock_api_client):
        """Test successful credit sync"""
        manager = OpenRouterManager()
        manager.db_pool = mock_db_pool
        manager.api_client = mock_api_client

        # Mock database response
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            "openrouter_api_key_encrypted": manager.encrypt_key("test-key")
        }
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Mock API response
        mock_api_client.get_key_info.return_value = {
            "limit": 10.0,
            "limit_remaining": 6.5
        }

        credits = await manager.sync_free_credits("user-123")

        assert credits == Decimal("6.5")
        mock_conn.execute.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
