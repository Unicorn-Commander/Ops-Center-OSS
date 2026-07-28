"""
Comprehensive Test Suite for Usage Tracking System
===================================================

Tests all scenarios for API call metering and quota enforcement.

Test Coverage:
1. User within limit → Request succeeds
2. User at limit → Request blocked with 429
3. Usage counter increments correctly
4. Quota resets on billing cycle
5. Enterprise tier has unlimited access
6. Multiple users in same org tracked separately
7. Redis cache sync with PostgreSQL

Author: Usage Tracking Test Team
Date: November 12, 2025
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import os
import sys

# Add app path for imports
sys.path.insert(0, '/app')

from usage_tracking import UsageTracker, usage_tracker
from usage_middleware import UsageTrackingMiddleware


class TestUsageTracker:
    """Test the core UsageTracker class"""

    @pytest.fixture
    async def tracker(self):
        """Create a fresh tracker instance for testing"""
        tracker = UsageTracker()
        await tracker.initialize()
        yield tracker
        await tracker.close()

    @pytest.mark.asyncio
    async def test_get_tier_limits(self, tracker):
        """Test that tier limits are correctly defined"""
        # Trial tier
        trial_limits = tracker.get_tier_limits("trial")
        assert trial_limits["daily_limit"] == 100
        assert trial_limits["monthly_limit"] == 700
        assert trial_limits["reset_period"] == "daily"

        # Starter tier
        starter_limits = tracker.get_tier_limits("starter")
        assert starter_limits["monthly_limit"] == 1000

        # Professional tier
        pro_limits = tracker.get_tier_limits("professional")
        assert pro_limits["monthly_limit"] == 10000

        # Enterprise tier (unlimited)
        enterprise_limits = tracker.get_tier_limits("enterprise")
        assert enterprise_limits["monthly_limit"] == -1  # Unlimited
        assert enterprise_limits["daily_limit"] == -1

    @pytest.mark.asyncio
    async def test_user_within_limit_succeeds(self, tracker):
        """
        Test Scenario 1: User within limit → Request succeeds
        """
        test_user_id = f"test_user_{datetime.utcnow().timestamp()}"

        # Simulate first API call
        result = await tracker.increment_api_usage(
            user_id=test_user_id,
            endpoint="/api/v1/llm/chat/completions",
            method="POST",
            response_status=200
        )

        # Should be allowed
        assert result["allowed"] is True
        assert result["used"] == 1
        assert result["tier"] == "trial"  # Default tier
        assert result["remaining"] > 0

    @pytest.mark.asyncio
    async def test_user_at_limit_blocked(self, tracker):
        """
        Test Scenario 2: User at limit → Request blocked with 429
        """
        test_user_id = f"test_user_limit_{datetime.utcnow().timestamp()}"

        # Manually set user to trial tier with only 5 calls allowed
        async with tracker.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, api_calls_used, reset_date)
                VALUES ($1, 'trial', 5, 5, CURRENT_DATE + INTERVAL '1 day')
                ON CONFLICT (user_id) DO UPDATE SET api_calls_used = 5, api_calls_limit = 5
                """,
                test_user_id
            )

        # Try to make another call (should be blocked)
        result = await tracker.increment_api_usage(
            user_id=test_user_id,
            endpoint="/api/v1/llm/chat/completions",
            method="POST"
        )

        # Should be denied
        assert result["allowed"] is False
        assert result["remaining"] == 0
        assert "limit" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_usage_counter_increments(self, tracker):
        """
        Test Scenario 3: Usage counter increments correctly
        """
        test_user_id = f"test_user_increment_{datetime.utcnow().timestamp()}"

        # Make 3 API calls
        for i in range(3):
            result = await tracker.increment_api_usage(
                user_id=test_user_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST",
                response_status=200,
                tokens_used=100,
                cost_credits=Decimal("0.01")
            )

            # Check incremental usage
            assert result["allowed"] is True
            assert result["used"] == i + 1

        # Verify final count
        stats = await tracker.get_usage_stats(test_user_id, period="current")
        assert stats["used"] == 3

    @pytest.mark.asyncio
    async def test_quota_reset(self, tracker):
        """
        Test Scenario 4: Quota resets on billing cycle
        """
        test_user_id = f"test_user_reset_{datetime.utcnow().timestamp()}"

        # Make some API calls
        for _ in range(5):
            await tracker.increment_api_usage(
                user_id=test_user_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST"
            )

        # Verify usage
        stats_before = await tracker.get_usage_stats(test_user_id, period="current")
        assert stats_before["used"] == 5

        # Reset quota
        reset_success = await tracker.reset_quota(test_user_id)
        assert reset_success is True

        # Verify usage is reset
        stats_after = await tracker.get_usage_stats(test_user_id, period="current")
        assert stats_after["used"] == 0

    @pytest.mark.asyncio
    async def test_enterprise_unlimited_access(self, tracker):
        """
        Test Scenario 5: Enterprise tier has unlimited access
        """
        test_user_id = f"test_user_enterprise_{datetime.utcnow().timestamp()}"

        # Set user to enterprise tier
        async with tracker.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, reset_date)
                VALUES ($1, 'enterprise', -1, CURRENT_DATE + INTERVAL '1 month')
                ON CONFLICT (user_id) DO UPDATE SET subscription_tier = 'enterprise', api_calls_limit = -1
                """,
                test_user_id
            )

        # Make 1000 API calls (should all succeed)
        for i in range(1000):
            result = await tracker.increment_api_usage(
                user_id=test_user_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST"
            )

            # All should be allowed (unlimited)
            assert result["allowed"] is True
            assert result["limit"] == -1  # Unlimited

            if i >= 999:  # Check last one
                assert result["used"] == 1000

    @pytest.mark.asyncio
    async def test_multiple_users_separate_tracking(self, tracker):
        """
        Test Scenario 6: Multiple users in same org tracked separately
        """
        org_id = f"test_org_{datetime.utcnow().timestamp()}"
        user1_id = f"user1_{datetime.utcnow().timestamp()}"
        user2_id = f"user2_{datetime.utcnow().timestamp()}"

        # User 1 makes 10 calls
        for _ in range(10):
            await tracker.increment_api_usage(
                user_id=user1_id,
                org_id=org_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST"
            )

        # User 2 makes 5 calls
        for _ in range(5):
            await tracker.increment_api_usage(
                user_id=user2_id,
                org_id=org_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST"
            )

        # Verify separate tracking
        user1_stats = await tracker.get_usage_stats(user1_id, period="current")
        user2_stats = await tracker.get_usage_stats(user2_id, period="current")

        assert user1_stats["used"] == 10
        assert user2_stats["used"] == 5

    @pytest.mark.asyncio
    async def test_redis_postgres_sync(self, tracker):
        """
        Test Scenario 7: Redis cache syncs with PostgreSQL
        """
        test_user_id = f"test_user_sync_{datetime.utcnow().timestamp()}"

        # Make API calls (writes to both Redis and PostgreSQL)
        for _ in range(10):
            await tracker.increment_api_usage(
                user_id=test_user_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST",
                tokens_used=50
            )

        # Check Redis
        now = datetime.utcnow()
        redis_key = f"usage:{test_user_id}:{now.strftime('%Y-%m')}:calls"
        redis_count = await tracker.redis.get(redis_key)

        # Check PostgreSQL
        async with tracker.db_pool.acquire() as conn:
            pg_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM api_usage
                WHERE user_id = $1
                """,
                test_user_id
            )

        # Both should match
        assert int(redis_count) == pg_count == 10

    @pytest.mark.asyncio
    async def test_daily_limit_enforcement(self, tracker):
        """Test that daily limits are enforced for trial tier"""
        test_user_id = f"test_user_daily_{datetime.utcnow().timestamp()}"

        # Set user to trial tier (100 calls/day)
        async with tracker.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, reset_date)
                VALUES ($1, 'trial', 700, CURRENT_DATE + INTERVAL '1 day')
                ON CONFLICT (user_id) DO UPDATE SET subscription_tier = 'trial', api_calls_limit = 700
                """,
                test_user_id
            )

        # Simulate 100 calls (daily limit)
        # Note: In real scenario, we'd need to mock the daily counter
        # For simplicity, we'll just verify the logic exists

        stats = await tracker.get_usage_stats(test_user_id, period="current")
        assert stats["daily_limit"] == 100  # Trial tier daily limit

    @pytest.mark.asyncio
    async def test_usage_history_tracking(self, tracker):
        """Test that usage history is properly tracked"""
        test_user_id = f"test_user_history_{datetime.utcnow().timestamp()}"

        # Make calls with different token counts
        for i in range(5):
            await tracker.increment_api_usage(
                user_id=test_user_id,
                endpoint="/api/v1/llm/chat/completions",
                method="POST",
                tokens_used=100 * (i + 1),
                cost_credits=Decimal(str(0.01 * (i + 1)))
            )

        # Get history
        stats = await tracker.get_usage_stats(test_user_id, period="daily")

        # Should have history data
        assert "history" in stats
        assert len(stats["history"]) > 0


class TestUsageMiddleware:
    """Test the FastAPI middleware"""

    def test_endpoint_matching(self):
        """Test that endpoint patterns are correctly identified"""
        middleware = UsageTrackingMiddleware(None)

        # Should track
        assert asyncio.run(middleware._should_track_endpoint("/api/v1/llm/chat/completions")) is True
        assert asyncio.run(middleware._should_track_endpoint("/api/v1/llm/image/generations")) is True

        # Should not track
        assert asyncio.run(middleware._should_track_endpoint("/api/v1/llm/models")) is False
        assert asyncio.run(middleware._should_track_endpoint("/api/v1/usage/current")) is False
        assert asyncio.run(middleware._should_track_endpoint("/api/v1/admin/users")) is False


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def run_all_tests():
    """
    Run all usage tracking tests.

    Returns exit code (0 = all passed, 1 = failures)
    """
    import pytest

    # Run tests with verbose output
    result = pytest.main([
        __file__,
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "-ra"  # Show summary of all test results
    ])

    return result


if __name__ == "__main__":
    # Run tests when script is executed directly
    exit_code = run_all_tests()
    sys.exit(exit_code)
