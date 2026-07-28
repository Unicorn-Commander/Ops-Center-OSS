"""
Unit tests for LLM Routing Engine.

Tests power level selection, BYOK preference, fallback mechanisms,
cost calculation, usage logging, and load balancing.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from modules.llm_routing_engine import LLMRoutingEngine, RoutingDecision
from tests.fixtures.llm_test_data import MOCK_PROVIDERS, MOCK_ROUTING_RULES


class TestLLMRoutingEngine:
    """Test suite for LLM Routing Engine."""

    @pytest.fixture
    def routing_engine(self, mock_db_session):
        """Initialize routing engine with mock dependencies."""
        engine = LLMRoutingEngine(db_session=mock_db_session)
        return engine

    @pytest.fixture
    def mock_providers_db(self, mock_db_session):
        """Mock database provider queries."""
        mock_db_session.query().filter().all.return_value = MOCK_PROVIDERS
        return mock_db_session

    # Test: Power Level to Model Selection
    @pytest.mark.asyncio
    async def test_select_model_eco_power_level(self, routing_engine, mock_providers_db):
        """Test model selection for eco power level."""
        decision = await routing_engine.select_model(
            power_level="eco",
            user_id="user-123",
            providers=MOCK_PROVIDERS
        )

        assert decision is not None
        assert decision.power_level == "eco"
        # Should select cheapest model
        assert decision.cost_per_1k_tokens <= 0.001
        # Should prefer platform vLLM (free) or Gemini Flash
        assert decision.provider_type in ["vllm", "google"]

    @pytest.mark.asyncio
    async def test_select_model_balanced_power_level(self, routing_engine, mock_providers_db):
        """Test model selection for balanced power level."""
        decision = await routing_engine.select_model(
            power_level="balanced",
            user_id="user-123",
            providers=MOCK_PROVIDERS
        )

        assert decision is not None
        assert decision.power_level == "balanced"
        # Should select mid-tier model
        assert 0.0001 < decision.cost_per_1k_tokens < 0.01
        # Should prefer Claude Haiku, GPT-4o Mini, or Gemini Flash
        assert decision.model_id in [
            "claude-3-5-haiku-20241022",
            "gpt-4o-mini",
            "gemini-2.0-flash-exp"
        ]

    @pytest.mark.asyncio
    async def test_select_model_precision_power_level(self, routing_engine, mock_providers_db):
        """Test model selection for precision power level."""
        decision = await routing_engine.select_model(
            power_level="precision",
            user_id="user-123",
            providers=MOCK_PROVIDERS
        )

        assert decision is not None
        assert decision.power_level == "precision"
        # Should select premium model
        assert decision.cost_per_1k_tokens >= 0.01
        # Should prefer GPT-4o or Claude 3.5 Sonnet
        assert decision.model_id in [
            "gpt-4o",
            "claude-3-5-sonnet-20241022"
        ]

    @pytest.mark.asyncio
    async def test_select_model_invalid_power_level(self, routing_engine, mock_providers_db):
        """Test handling of invalid power level."""
        with pytest.raises(ValueError, match="Invalid power level"):
            await routing_engine.select_model(
                power_level="ultra-mega",
                user_id="user-123",
                providers=MOCK_PROVIDERS
            )

    # Test: BYOK Preference Logic
    @pytest.mark.asyncio
    async def test_prefer_byok_when_available(self, routing_engine, mock_providers_db):
        """Test that user's BYOK key is preferred over platform key."""
        with patch('modules.byok_manager.BYOKManager.get_user_key') as mock_get_key:
            # Mock user has OpenAI key
            mock_get_key.return_value = {
                "provider_id": "provider-1",
                "decrypted_key": "sk-user-openai-key",
                "is_active": True
            }

            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=MOCK_PROVIDERS,
                prefer_byok=True
            )

            assert decision.used_byok is True
            assert decision.provider_id == "provider-1"
            # Should use user's key, not platform key

    @pytest.mark.asyncio
    async def test_fallback_to_platform_key_when_no_byok(self, routing_engine, mock_providers_db):
        """Test fallback to platform key when user has no BYOK."""
        with patch('modules.byok_manager.BYOKManager.get_user_key') as mock_get_key:
            mock_get_key.return_value = None  # No BYOK key

            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=MOCK_PROVIDERS,
                prefer_byok=True
            )

            assert decision.used_byok is False
            # Should still select a model using platform key

    @pytest.mark.asyncio
    async def test_respect_byok_disabled_flag(self, routing_engine, mock_providers_db):
        """Test that BYOK is not used when prefer_byok=False."""
        with patch('modules.byok_manager.BYOKManager.get_user_key') as mock_get_key:
            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=MOCK_PROVIDERS,
                prefer_byok=False
            )

            # Should not even check for BYOK key
            mock_get_key.assert_not_called()
            assert decision.used_byok is False

    # Test: Fallback Mechanisms
    @pytest.mark.asyncio
    async def test_fallback_when_primary_provider_down(self, routing_engine, mock_providers_db):
        """Test fallback to secondary provider when primary is unhealthy."""
        # Mark OpenAI as unhealthy
        unhealthy_providers = MOCK_PROVIDERS.copy()
        unhealthy_providers[0]["health_status"] = "unhealthy"
        unhealthy_providers[0]["enabled"] = False

        decision = await routing_engine.select_model(
            power_level="precision",
            user_id="user-123",
            providers=unhealthy_providers
        )

        # Should fallback to Anthropic (next best for precision)
        assert decision.provider_id == "provider-2"
        assert decision.provider_name == "Anthropic"

    @pytest.mark.asyncio
    async def test_fallback_chain(self, routing_engine):
        """Test complete fallback chain when multiple providers fail."""
        # All commercial providers down
        limited_providers = [
            p for p in MOCK_PROVIDERS if p["provider_type"] == "vllm"
        ]

        decision = await routing_engine.select_model(
            power_level="precision",
            user_id="user-123",
            providers=limited_providers
        )

        # Should fallback to vLLM even though it's not ideal for precision
        assert decision.provider_type == "vllm"

    @pytest.mark.asyncio
    async def test_no_available_providers(self, routing_engine):
        """Test error handling when no providers available."""
        with pytest.raises(Exception, match="No available providers"):
            await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=[]
            )

    # Test: Cost Calculation
    def test_calculate_cost_accurate(self, routing_engine):
        """Test accurate cost calculation."""
        cost = routing_engine.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            cost_per_1k_tokens=0.015
        )

        expected_cost = (1000 + 500) * 0.015 / 1000
        assert abs(cost - expected_cost) < 0.0001

    def test_calculate_cost_zero_tokens(self, routing_engine):
        """Test cost calculation with zero tokens."""
        cost = routing_engine.calculate_cost(
            prompt_tokens=0,
            completion_tokens=0,
            cost_per_1k_tokens=0.015
        )

        assert cost == 0.0

    def test_calculate_cost_free_model(self, routing_engine):
        """Test cost calculation for free model (vLLM)."""
        cost = routing_engine.calculate_cost(
            prompt_tokens=5000,
            completion_tokens=2000,
            cost_per_1k_tokens=0.0
        )

        assert cost == 0.0

    # Test: Usage Logging
    @pytest.mark.asyncio
    async def test_log_usage_success(self, routing_engine, mock_db_session):
        """Test successful usage logging."""
        decision = RoutingDecision(
            provider_id="provider-1",
            provider_name="OpenAI",
            provider_type="openai",
            model_id="gpt-4o",
            power_level="precision",
            cost_per_1k_tokens=0.015,
            used_byok=False
        )

        await routing_engine.log_usage(
            user_id="user-123",
            decision=decision,
            prompt_tokens=100,
            completion_tokens=200,
            latency_ms=500,
            status="success"
        )

        # Verify database insert called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_usage_with_error_status(self, routing_engine, mock_db_session):
        """Test usage logging with error status."""
        decision = RoutingDecision(
            provider_id="provider-1",
            provider_name="OpenAI",
            provider_type="openai",
            model_id="gpt-4o",
            power_level="precision",
            cost_per_1k_tokens=0.015,
            used_byok=False
        )

        await routing_engine.log_usage(
            user_id="user-123",
            decision=decision,
            prompt_tokens=100,
            completion_tokens=0,
            latency_ms=100,
            status="error",
            error_message="Rate limit exceeded"
        )

        # Should still log even for errors
        mock_db_session.add.assert_called_once()

    # Test: Load Balancing
    @pytest.mark.asyncio
    async def test_load_balance_across_providers(self, routing_engine, mock_providers_db):
        """Test load balancing distributes requests across providers."""
        decisions = []

        # Make 100 requests
        for i in range(100):
            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id=f"user-{i}",
                providers=MOCK_PROVIDERS,
                enable_load_balancing=True
            )
            decisions.append(decision)

        # Should use multiple providers, not just one
        unique_providers = set(d.provider_id for d in decisions)
        assert len(unique_providers) > 1

    @pytest.mark.asyncio
    async def test_weighted_load_balancing(self, routing_engine, mock_providers_db):
        """Test that load balancing respects provider priorities."""
        decisions = []

        for i in range(100):
            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id=f"user-{i}",
                providers=MOCK_PROVIDERS,
                enable_load_balancing=True
            )
            decisions.append(decision)

        # Higher priority providers should get more requests
        provider_counts = {}
        for d in decisions:
            provider_counts[d.provider_id] = provider_counts.get(d.provider_id, 0) + 1

        # Provider-1 (priority 1) should get more than Provider-3 (priority 3)
        if "provider-1" in provider_counts and "provider-3" in provider_counts:
            assert provider_counts["provider-1"] >= provider_counts["provider-3"]

    # Test: Context Window Handling
    @pytest.mark.asyncio
    async def test_select_model_respects_context_window(self, routing_engine, mock_providers_db):
        """Test that model selection respects required context window."""
        decision = await routing_engine.select_model(
            power_level="balanced",
            user_id="user-123",
            providers=MOCK_PROVIDERS,
            min_context_window=100000
        )

        # Should select model with sufficient context window
        assert decision.context_window >= 100000
        # Should prefer Gemini or Claude (large context)
        assert decision.provider_type in ["google", "anthropic"]

    @pytest.mark.asyncio
    async def test_no_model_with_sufficient_context(self, routing_engine, mock_providers_db):
        """Test error when no model has required context window."""
        with pytest.raises(Exception, match="No model with sufficient context"):
            await routing_engine.select_model(
                power_level="eco",
                user_id="user-123",
                providers=MOCK_PROVIDERS,
                min_context_window=2000000  # 2M tokens - no model supports this
            )

    # Test: Provider Health Monitoring
    @pytest.mark.asyncio
    async def test_update_provider_health(self, routing_engine, mock_db_session):
        """Test updating provider health status."""
        await routing_engine.update_provider_health(
            provider_id="provider-1",
            is_healthy=False,
            error_message="Connection timeout"
        )

        # Should update database
        mock_db_session.query().filter().update.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_auto_recovery_after_health_check(self, routing_engine, mock_db_session):
        """Test provider auto-recovery after successful health check."""
        # Mark as unhealthy
        await routing_engine.update_provider_health(
            provider_id="provider-1",
            is_healthy=False
        )

        # Successful request should restore health
        await routing_engine.update_provider_health(
            provider_id="provider-1",
            is_healthy=True
        )

        # Health should be restored

    # Test: Concurrent Routing Decisions
    @pytest.mark.asyncio
    async def test_concurrent_routing_decisions(self, routing_engine, mock_providers_db):
        """Test handling multiple concurrent routing decisions."""
        tasks = [
            routing_engine.select_model(
                power_level="balanced",
                user_id=f"user-{i}",
                providers=MOCK_PROVIDERS
            )
            for i in range(50)
        ]

        decisions = await asyncio.gather(*tasks)

        # All should succeed
        assert len(decisions) == 50
        assert all(d is not None for d in decisions)

    # Test: Edge Cases
    @pytest.mark.asyncio
    async def test_handle_provider_with_no_models(self, routing_engine):
        """Test handling provider with empty model list."""
        broken_providers = MOCK_PROVIDERS.copy()
        broken_providers[0]["models"] = []

        decision = await routing_engine.select_model(
            power_level="balanced",
            user_id="user-123",
            providers=broken_providers
        )

        # Should skip provider with no models
        assert decision.provider_id != broken_providers[0]["id"]

    @pytest.mark.asyncio
    async def test_handle_malformed_provider_data(self, routing_engine):
        """Test handling malformed provider configuration."""
        malformed_providers = [
            {
                "id": "bad-provider",
                "name": "Bad Provider"
                # Missing required fields
            }
        ]

        with pytest.raises(Exception):
            await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=malformed_providers
            )


# Run tests with: pytest -v tests/unit/test_llm_routing_engine.py
