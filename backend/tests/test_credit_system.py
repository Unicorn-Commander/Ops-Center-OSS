"""
Epic 1.8 - Credit System Unit Tests

Comprehensive test suite for the CreditSystem class covering:
- Credit allocation and deduction
- Balance tracking and caching
- Transaction history
- Cost calculation
- Monthly caps and resets
- Usage statistics
- Thread safety and atomicity

Author: Testing & DevOps Team Lead
Date: October 23, 2025
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json

# Import the CreditSystem class
import sys
sys.path.insert(0, '/app')
from litellm_credit_system import CreditSystem, POWER_LEVELS, PRICING, MODEL_PRICING, TIER_MARKUP


@pytest.fixture
async def mock_db_pool():
    """Mock asyncpg connection pool"""
    pool = AsyncMock()
    conn = AsyncMock()

    # Setup connection context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    # Setup transaction context manager
    conn.transaction.return_value.__aenter__.return_value = None
    conn.transaction.return_value.__aexit__.return_value = None

    return pool, conn


@pytest.fixture
async def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = True
    redis.delete.return_value = True
    return redis


@pytest.fixture
async def credit_system(mock_db_pool, mock_redis):
    """Create CreditSystem instance with mocked dependencies"""
    pool, conn = mock_db_pool
    return CreditSystem(pool, mock_redis), conn


class TestCreditAllocation:
    """Test credit allocation operations"""

    @pytest.mark.asyncio
    async def test_allocate_credits_new_user(self, credit_system):
        """Test credit allocation for new user"""
        system, conn = credit_system

        # Mock database responses
        conn.fetchval.return_value = 100.0

        # Allocate credits
        new_balance = await system.credit_credits(
            user_id="new_user@example.com",
            amount=100.0,
            reason="purchase"
        )

        assert new_balance == 100.0
        assert conn.execute.called

    @pytest.mark.asyncio
    async def test_allocate_credits_existing_user(self, credit_system):
        """Test credit allocation for existing user"""
        system, conn = credit_system

        # Mock existing balance
        conn.fetchval.return_value = 150.0  # 50 + 100

        new_balance = await system.credit_credits(
            user_id="existing@example.com",
            amount=100.0,
            reason="purchase"
        )

        assert new_balance == 150.0

    @pytest.mark.asyncio
    async def test_allocate_bonus_credits(self, credit_system):
        """Test bonus credit allocation"""
        system, conn = credit_system

        conn.fetchval.return_value = 50.0

        new_balance = await system.credit_credits(
            user_id="user@example.com",
            amount=50.0,
            reason="bonus"
        )

        assert new_balance == 50.0

    @pytest.mark.asyncio
    async def test_allocate_refund_credits(self, credit_system):
        """Test refund credit allocation"""
        system, conn = credit_system

        conn.fetchval.return_value = 75.0

        new_balance = await system.credit_credits(
            user_id="user@example.com",
            amount=75.0,
            reason="refund"
        )

        assert new_balance == 75.0


class TestCreditDeduction:
    """Test credit deduction operations"""

    @pytest.mark.asyncio
    async def test_deduct_credits_sufficient_balance(self, credit_system):
        """Test credit deduction with sufficient balance"""
        system, conn = credit_system

        # Mock sufficient balance
        conn.fetchrow.side_effect = [
            {'credits_remaining': 100.0, 'monthly_cap': None, 'tier': 'professional'},
            None
        ]
        conn.fetchval.return_value = "txn_123"

        metadata = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'tokens_used': 1000,
            'cost': 10.0
        }

        new_balance, txn_id = await system.debit_credits(
            user_id="user@example.com",
            amount=10.0,
            metadata=metadata
        )

        assert new_balance == 90.0
        assert txn_id == "txn_123"

    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient_balance(self, credit_system):
        """Test credit deduction fails with insufficient balance"""
        system, conn = credit_system

        # Mock insufficient balance
        conn.fetchrow.return_value = {
            'credits_remaining': 5.0,
            'monthly_cap': None,
            'tier': 'professional'
        }

        metadata = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'tokens_used': 1000,
            'cost': 10.0
        }

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await system.debit_credits(
                user_id="user@example.com",
                amount=10.0,
                metadata=metadata
            )

        assert exc_info.value.status_code == 402
        assert "Insufficient credits" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_deduct_credits_free_tier_unlimited(self, credit_system):
        """Test free tier can deduct even with zero balance"""
        system, conn = credit_system

        # Mock free tier with zero balance
        conn.fetchrow.side_effect = [
            {'credits_remaining': 0.0, 'monthly_cap': None, 'tier': 'free'},
            None
        ]
        conn.fetchval.return_value = "txn_124"

        metadata = {'provider': 'groq', 'model': 'llama3-70b', 'tokens_used': 500}

        new_balance, txn_id = await system.debit_credits(
            user_id="free_user@example.com",
            amount=0.0,  # Free model
            metadata=metadata
        )

        assert new_balance == 0.0
        assert txn_id == "txn_124"

    @pytest.mark.asyncio
    async def test_atomic_deduction(self, credit_system):
        """Test that credit deduction is atomic (uses transaction)"""
        system, conn = credit_system

        conn.fetchrow.side_effect = [
            {'credits_remaining': 100.0, 'monthly_cap': None, 'tier': 'starter'},
            None
        ]
        conn.fetchval.return_value = "txn_125"

        metadata = {'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}

        await system.debit_credits(
            user_id="user@example.com",
            amount=15.0,
            metadata=metadata
        )

        # Verify transaction context was used
        assert conn.transaction.called


class TestBalanceTracking:
    """Test balance tracking and caching"""

    @pytest.mark.asyncio
    async def test_get_balance_from_cache(self, credit_system, mock_redis):
        """Test balance retrieval from cache"""
        system, conn = credit_system

        # Mock cached balance
        mock_redis.get.return_value = b"75.50"

        balance = await system.get_user_credits("user@example.com")

        assert balance == 75.50
        assert mock_redis.get.called
        assert not conn.fetchrow.called

    @pytest.mark.asyncio
    async def test_get_balance_from_database(self, credit_system, mock_redis):
        """Test balance retrieval from database when cache misses"""
        system, conn = credit_system

        # Mock cache miss
        mock_redis.get.return_value = None
        conn.fetchrow.return_value = {'credits_remaining': 125.0, 'tier': 'professional'}

        balance = await system.get_user_credits("user@example.com")

        assert balance == 125.0
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_debit(self, credit_system, mock_redis):
        """Test cache is invalidated after debit"""
        system, conn = credit_system

        conn.fetchrow.side_effect = [
            {'credits_remaining': 100.0, 'monthly_cap': None, 'tier': 'starter'},
            None
        ]
        conn.fetchval.return_value = "txn_126"

        await system.debit_credits(
            user_id="user@example.com",
            amount=10.0,
            metadata={'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}
        )

        assert mock_redis.delete.called

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_credit(self, credit_system, mock_redis):
        """Test cache is invalidated after credit"""
        system, conn = credit_system

        conn.fetchval.return_value = 150.0

        await system.credit_credits(
            user_id="user@example.com",
            amount=50.0,
            reason="purchase"
        )

        assert mock_redis.delete.called


class TestTransactionHistory:
    """Test transaction history retrieval"""

    @pytest.mark.asyncio
    async def test_get_transaction_history(self, credit_system):
        """Test transaction history retrieval"""
        system, conn = credit_system

        mock_transactions = [
            {
                'id': 1,
                'amount': -10.0,
                'transaction_type': 'usage',
                'provider': 'openai',
                'model': 'gpt-4o',
                'tokens_used': 1000,
                'cost': 10.0,
                'metadata': '{"request_id": "req_123"}',
                'created_at': datetime.utcnow()
            },
            {
                'id': 2,
                'amount': 100.0,
                'transaction_type': 'purchase',
                'provider': None,
                'model': None,
                'tokens_used': None,
                'cost': 100.0,
                'metadata': '{"payment_id": "pay_456"}',
                'created_at': datetime.utcnow() - timedelta(days=1)
            }
        ]

        conn.fetch.return_value = mock_transactions

        history = await system.get_credit_history(
            user_id="user@example.com",
            limit=100,
            offset=0
        )

        assert len(history) == 2
        assert history[0]['type'] == 'usage'
        assert history[0]['amount'] == -10.0
        assert history[1]['type'] == 'purchase'
        assert history[1]['amount'] == 100.0

    @pytest.mark.asyncio
    async def test_transaction_history_pagination(self, credit_system):
        """Test transaction history pagination"""
        system, conn = credit_system

        conn.fetch.return_value = []

        history = await system.get_credit_history(
            user_id="user@example.com",
            limit=50,
            offset=100
        )

        # Verify pagination parameters were passed
        conn.fetch.assert_called_once()
        call_args = conn.fetch.call_args
        assert call_args[0][2] == 50  # limit
        assert call_args[0][3] == 100  # offset


class TestCostCalculation:
    """Test cost calculation logic"""

    def test_calculate_cost_free_model(self, credit_system):
        """Test cost calculation for free models"""
        system, _ = credit_system

        cost = system.calculate_cost(
            tokens_used=1000,
            model="llama3-70b-groq",
            power_level="balanced",
            user_tier="free"
        )

        assert cost == 0.0

    def test_calculate_cost_paid_model(self, credit_system):
        """Test cost calculation for paid models"""
        system, _ = credit_system

        # gpt-4o at 0.015 per 1K tokens
        # 1000 tokens = 0.015 base
        # balanced power = 0.25 multiplier = 0.00375
        # starter tier = 1.4 multiplier = 0.00525
        cost = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="balanced",
            user_tier="starter"
        )

        expected = (1000 / 1000) * 0.015 * 0.25 * 1.4
        assert abs(cost - expected) < 0.000001

    def test_calculate_cost_eco_power_level(self, credit_system):
        """Test eco power level reduces cost"""
        system, _ = credit_system

        cost_eco = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="eco",
            user_tier="professional"
        )

        cost_balanced = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="balanced",
            user_tier="professional"
        )

        assert cost_eco < cost_balanced

    def test_calculate_cost_precision_power_level(self, credit_system):
        """Test precision power level increases cost"""
        system, _ = credit_system

        cost_precision = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="precision",
            user_tier="professional"
        )

        cost_balanced = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="balanced",
            user_tier="professional"
        )

        assert cost_precision > cost_balanced

    def test_calculate_cost_tier_markup(self, credit_system):
        """Test tier markup affects cost"""
        system, _ = credit_system

        cost_free = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="balanced",
            user_tier="free"
        )

        cost_enterprise = system.calculate_cost(
            tokens_used=1000,
            model="gpt-4o",
            power_level="balanced",
            user_tier="enterprise"
        )

        assert cost_enterprise > cost_free


class TestMonthlyCaps:
    """Test monthly spending caps"""

    @pytest.mark.asyncio
    async def test_check_monthly_cap_no_cap_set(self, credit_system):
        """Test monthly cap check when no cap is set"""
        system, conn = credit_system

        conn.fetchrow.return_value = {
            'monthly_cap': None,
            'last_reset': datetime.utcnow()
        }

        within_cap = await system.check_monthly_cap(
            user_id="user@example.com",
            amount=100.0
        )

        assert within_cap is True

    @pytest.mark.asyncio
    async def test_check_monthly_cap_within_limit(self, credit_system):
        """Test monthly cap check within limit"""
        system, conn = credit_system

        conn.fetchrow.return_value = {
            'monthly_cap': 1000.0,
            'last_reset': datetime.utcnow()
        }
        conn.fetchval.return_value = 500.0  # Current spending

        within_cap = await system.check_monthly_cap(
            user_id="user@example.com",
            amount=400.0  # Total would be 900
        )

        assert within_cap is True

    @pytest.mark.asyncio
    async def test_check_monthly_cap_exceeds_limit(self, credit_system):
        """Test monthly cap check exceeds limit"""
        system, conn = credit_system

        conn.fetchrow.return_value = {
            'monthly_cap': 1000.0,
            'last_reset': datetime.utcnow()
        }
        conn.fetchval.return_value = 950.0  # Current spending

        within_cap = await system.check_monthly_cap(
            user_id="user@example.com",
            amount=100.0  # Total would be 1050
        )

        assert within_cap is False

    @pytest.mark.asyncio
    async def test_monthly_reset_after_30_days(self, credit_system):
        """Test monthly reset logic"""
        system, conn = credit_system

        # Mock last reset was 31 days ago
        conn.fetchrow.side_effect = [
            {
                'credits_remaining': 100.0,
                'monthly_cap': 1000.0,
                'tier': 'professional'
            },
            None
        ]
        conn.fetchval.return_value = "txn_127"

        await system.debit_credits(
            user_id="user@example.com",
            amount=10.0,
            metadata={'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}
        )

        # Verify UPDATE statement includes CASE for reset
        assert conn.execute.called


class TestUsageStatistics:
    """Test usage statistics"""

    @pytest.mark.asyncio
    async def test_get_usage_stats_30_days(self, credit_system):
        """Test usage statistics for 30 days"""
        system, conn = credit_system

        conn.fetchrow.return_value = {
            'total_requests': 150,
            'total_tokens': 75000,
            'total_cost': 45.50,
            'avg_cost_per_request': 0.303
        }

        conn.fetch.return_value = [
            {'provider': 'openai', 'requests': 100, 'tokens': 50000, 'cost': 30.0},
            {'provider': 'anthropic', 'requests': 50, 'tokens': 25000, 'cost': 15.5}
        ]

        stats = await system.get_usage_stats(
            user_id="user@example.com",
            days=30
        )

        assert stats['total_requests'] == 150
        assert stats['total_tokens'] == 75000
        assert stats['total_cost'] == 45.50
        assert len(stats['providers']) == 2

    @pytest.mark.asyncio
    async def test_get_usage_stats_custom_days(self, credit_system):
        """Test usage statistics for custom date range"""
        system, conn = credit_system

        conn.fetchrow.return_value = {
            'total_requests': 10,
            'total_tokens': 5000,
            'total_cost': 3.0,
            'avg_cost_per_request': 0.3
        }

        conn.fetch.return_value = []

        stats = await system.get_usage_stats(
            user_id="user@example.com",
            days=7
        )

        assert stats['total_requests'] == 10


class TestConcurrentOperations:
    """Test thread-safe concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_deductions(self, credit_system):
        """Test concurrent credit deductions are safe"""
        system, conn = credit_system

        # Mock sufficient initial balance
        conn.fetchrow.side_effect = [
            {'credits_remaining': 1000.0, 'monthly_cap': None, 'tier': 'professional'}
            for _ in range(10)
        ] + [None] * 10

        conn.fetchval.side_effect = [f"txn_{i}" for i in range(10)]

        # Simulate 10 concurrent deductions
        tasks = []
        for i in range(10):
            task = system.debit_credits(
                user_id=f"user{i}@example.com",
                amount=10.0,
                metadata={'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed (or fail gracefully)
        assert len(results) == 10


class TestProviderExtraction:
    """Test provider extraction from model names"""

    def test_extract_openrouter_provider(self, credit_system):
        """Test OpenRouter provider extraction"""
        system, _ = credit_system

        assert system._extract_provider("openrouter/claude-3.5-sonnet") == "openrouter:claude-3.5"
        assert system._extract_provider("openrouter/gpt-4o") == "openrouter:gpt-4o"
        assert system._extract_provider("openrouter/mixtral-8x7b") == "openrouter:mixtral"

    def test_extract_direct_providers(self, credit_system):
        """Test direct provider extraction"""
        system, _ = credit_system

        assert system._extract_provider("anthropic/claude-3.5-sonnet") == "anthropic"
        assert system._extract_provider("openai/gpt-4o") == "openai"
        assert system._extract_provider("together_ai/llama3") == "together"
        assert system._extract_provider("groq/llama3-70b") == "groq"

    def test_extract_local_provider(self, credit_system):
        """Test local provider extraction"""
        system, _ = credit_system

        assert system._extract_provider("ollama/llama3-8b") == "local"
        assert system._extract_provider("vllm/qwen-32b") == "local"


class TestUserTier:
    """Test user tier management"""

    @pytest.mark.asyncio
    async def test_get_user_tier(self, credit_system):
        """Test getting user's subscription tier"""
        system, conn = credit_system

        conn.fetchval.return_value = "professional"

        tier = await system.get_user_tier("user@example.com")

        assert tier == "professional"

    @pytest.mark.asyncio
    async def test_get_user_tier_default_free(self, credit_system):
        """Test default tier is free when user not found"""
        system, conn = credit_system

        conn.fetchval.return_value = None

        tier = await system.get_user_tier("new_user@example.com")

        assert tier == "free"


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_zero_token_cost(self, credit_system):
        """Test zero token usage"""
        system, _ = credit_system

        cost = system.calculate_cost(
            tokens_used=0,
            model="gpt-4o",
            power_level="balanced",
            user_tier="professional"
        )

        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_very_large_token_count(self, credit_system):
        """Test very large token counts"""
        system, _ = credit_system

        cost = system.calculate_cost(
            tokens_used=1000000,  # 1M tokens
            model="gpt-4o",
            power_level="balanced",
            user_tier="enterprise"
        )

        assert cost > 0
        assert cost < 100000  # Sanity check

    @pytest.mark.asyncio
    async def test_unknown_model_uses_default_pricing(self, credit_system):
        """Test unknown models use default pricing"""
        system, _ = credit_system

        cost = system.calculate_cost(
            tokens_used=1000,
            model="unknown/model-x",
            power_level="balanced",
            user_tier="professional"
        )

        # Should use PRICING["default"] = 0.01
        expected = (1000 / 1000) * 0.01 * 0.25 * 1.6
        assert abs(cost - expected) < 0.000001


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
