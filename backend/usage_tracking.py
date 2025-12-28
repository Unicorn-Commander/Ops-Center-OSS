"""
API Call Usage Tracking System
===============================

Complete metering system for tracking API usage per user and enforcing subscription limits.

Features:
- Real-time usage tracking with Redis (fast)
- Persistent storage in PostgreSQL (historical)
- Automatic quota enforcement
- Billing cycle management
- Per-tier limit enforcement
- Usage analytics

Author: Usage Tracking Team Lead
Date: November 12, 2025
"""

import asyncpg
import redis.asyncio as aioredis
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os
import json

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks API usage and enforces subscription tier limits.

    Architecture:
    - Redis: Fast counters with TTL (for current period)
    - PostgreSQL: Persistent historical data
    - Dual-write: Increment both Redis and PostgreSQL

    Subscription Tiers:
    - trial: 100 calls/day (700 total over 7 days)
    - starter: 1,000 calls/month
    - professional: 10,000 calls/month
    - enterprise: Unlimited
    """

    # Tier limits configuration
    TIER_LIMITS = {
        "trial": {
            "daily_limit": 100,
            "monthly_limit": 700,  # 7 days * 100/day
            "reset_period": "daily"
        },
        "starter": {
            "daily_limit": 34,  # ~1000/30 days
            "monthly_limit": 1000,
            "reset_period": "monthly"
        },
        "professional": {
            "daily_limit": 334,  # ~10000/30 days
            "monthly_limit": 10000,
            "reset_period": "monthly"
        },
        "enterprise": {
            "daily_limit": -1,  # Unlimited
            "monthly_limit": -1,  # Unlimited
            "reset_period": "monthly"
        },
        "vip_founder": {
            "daily_limit": -1,  # Unlimited
            "monthly_limit": -1,  # Unlimited
            "reset_period": "monthly"
        },
        "byok": {
            "daily_limit": -1,  # Unlimited (user pays their own API costs)
            "monthly_limit": -1,
            "reset_period": "monthly"
        }
    }

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None

    async def initialize(self):
        """Initialize database and Redis connections"""
        if self.db_pool and self.redis:
            return

        try:
            # PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "uchub-postgres"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "unicorn"),
                password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
                database=os.getenv("POSTGRES_DB", "unicorn_db"),
                min_size=5,
                max_size=20
            )

            # Redis connection
            self.redis = await aioredis.from_url(
                f"redis://{os.getenv('REDIS_HOST', 'unicorn-lago-redis')}:{os.getenv('REDIS_PORT', 6379)}",
                encoding="utf-8",
                decode_responses=True
            )

            logger.info("UsageTracker initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize UsageTracker: {e}")
            raise

    async def close(self):
        """Close connections"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None

        if self.redis:
            await self.redis.close()
            self.redis = None

        logger.info("UsageTracker connections closed")

    async def increment_api_usage(
        self,
        user_id: str,
        org_id: Optional[str] = None,
        endpoint: str = "/api/v1/llm/chat/completions",
        method: str = "POST",
        response_status: int = 200,
        tokens_used: int = 0,
        cost_credits: Decimal = Decimal("0.00")
    ) -> Dict[str, Any]:
        """
        Track an API call and enforce limits.

        Args:
            user_id: Keycloak user ID
            org_id: Organization ID (optional)
            endpoint: API endpoint called
            method: HTTP method
            response_status: HTTP response status
            tokens_used: Number of tokens consumed
            cost_credits: Cost in credits

        Returns:
            {
                "allowed": bool,
                "used": int,
                "limit": int,
                "remaining": int,
                "reset_date": str,
                "tier": str,
                "message": str
            }

        Raises:
            HTTPException: 429 if limit exceeded
        """
        if not self.db_pool or not self.redis:
            await self.initialize()

        # Get user's subscription tier
        tier_info = await self._get_user_tier(user_id)
        tier = tier_info.get("tier", "trial")
        tier_limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["trial"])

        # Get current usage
        current_usage = await self._get_current_usage(user_id, tier_limits["reset_period"])

        # Check if within limits
        monthly_limit = tier_limits["monthly_limit"]
        daily_limit = tier_limits["daily_limit"]

        # Check monthly limit
        if monthly_limit > 0 and current_usage["monthly"] >= monthly_limit:
            return {
                "allowed": False,
                "used": current_usage["monthly"],
                "limit": monthly_limit,
                "remaining": 0,
                "reset_date": current_usage["reset_date"],
                "tier": tier,
                "message": f"Monthly API call limit ({monthly_limit}) exceeded. Upgrade your plan or wait until {current_usage['reset_date']}."
            }

        # Check daily limit
        if daily_limit > 0 and current_usage["daily"] >= daily_limit:
            return {
                "allowed": False,
                "used": current_usage["daily"],
                "limit": daily_limit,
                "remaining": 0,
                "reset_date": (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
                "tier": tier,
                "message": f"Daily API call limit ({daily_limit}) exceeded. Upgrade your plan or try again tomorrow."
            }

        # Increment usage counters (dual-write to Redis and PostgreSQL)
        await self._increment_counters(
            user_id=user_id,
            org_id=org_id,
            endpoint=endpoint,
            method=method,
            response_status=response_status,
            tokens_used=tokens_used,
            cost_credits=cost_credits,
            reset_period=tier_limits["reset_period"]
        )

        # Calculate remaining
        remaining = monthly_limit - (current_usage["monthly"] + 1) if monthly_limit > 0 else -1

        return {
            "allowed": True,
            "used": current_usage["monthly"] + 1,
            "limit": monthly_limit if monthly_limit > 0 else -1,
            "remaining": remaining,
            "reset_date": current_usage["reset_date"],
            "tier": tier,
            "message": "API call tracked successfully"
        }

    async def _get_user_tier(self, user_id: str) -> Dict[str, Any]:
        """Get user's subscription tier from database"""
        async with self.db_pool.acquire() as conn:
            # Check PostgreSQL first (Keycloak attributes synced to PostgreSQL)
            row = await conn.fetchrow(
                """
                SELECT subscription_tier, subscription_status
                FROM usage_quotas
                WHERE user_id = $1
                """,
                user_id
            )

            if row:
                return {
                    "tier": row["subscription_tier"] or "trial",
                    "status": row["subscription_status"] or "active"
                }

            # Fallback: Create entry with trial tier
            await conn.execute(
                """
                INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, reset_date)
                VALUES ($1, 'trial', 100, CURRENT_DATE + INTERVAL '1 day')
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id
            )

            return {"tier": "trial", "status": "active"}

    async def _get_current_usage(self, user_id: str, reset_period: str) -> Dict[str, Any]:
        """Get current usage counts from Redis (with PostgreSQL fallback)"""
        now = datetime.utcnow()

        # Calculate reset dates
        if reset_period == "daily":
            reset_date = (now + timedelta(days=1)).date().isoformat()
            monthly_key = f"usage:{user_id}:current:calls"
            daily_key = f"usage:{user_id}:{now.date().isoformat()}:calls"
        else:  # monthly
            # First day of next month
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            reset_date = next_month.date().isoformat()
            monthly_key = f"usage:{user_id}:{now.strftime('%Y-%m')}:calls"
            daily_key = f"usage:{user_id}:{now.date().isoformat()}:calls"

        # Try Redis first (fast)
        try:
            monthly_usage = await self.redis.get(monthly_key) or "0"
            daily_usage = await self.redis.get(daily_key) or "0"

            return {
                "monthly": int(monthly_usage),
                "daily": int(daily_usage),
                "reset_date": reset_date
            }
        except Exception as e:
            logger.warning(f"Redis error, falling back to PostgreSQL: {e}")

        # Fallback to PostgreSQL (slower but reliable)
        async with self.db_pool.acquire() as conn:
            # Monthly usage
            if reset_period == "monthly":
                billing_period = now.strftime("%Y-%m")
            else:
                billing_period = now.date().isoformat()

            monthly_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as count
                FROM api_usage
                WHERE user_id = $1 AND billing_period = $2
                """,
                user_id, billing_period
            )

            # Daily usage
            daily_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as count
                FROM api_usage
                WHERE user_id = $1 AND DATE(timestamp) = CURRENT_DATE
                """,
                user_id
            )

            return {
                "monthly": monthly_row["count"] if monthly_row else 0,
                "daily": daily_row["count"] if daily_row else 0,
                "reset_date": reset_date
            }

    async def _increment_counters(
        self,
        user_id: str,
        org_id: Optional[str],
        endpoint: str,
        method: str,
        response_status: int,
        tokens_used: int,
        cost_credits: Decimal,
        reset_period: str
    ):
        """Increment usage counters in both Redis and PostgreSQL"""
        now = datetime.utcnow()

        # Calculate Redis keys and TTLs
        if reset_period == "daily":
            monthly_key = f"usage:{user_id}:current:calls"
            monthly_ttl = 86400  # 24 hours
            billing_period = now.date().isoformat()
        else:  # monthly
            monthly_key = f"usage:{user_id}:{now.strftime('%Y-%m')}:calls"
            # TTL until end of month
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            monthly_ttl = int((next_month - now).total_seconds())
            billing_period = now.strftime("%Y-%m")

        daily_key = f"usage:{user_id}:{now.date().isoformat()}:calls"
        daily_ttl = 86400  # 24 hours

        # Organization keys (if applicable)
        if org_id:
            org_key = f"usage:org:{org_id}:current:calls"
            org_ttl = monthly_ttl

        # Redis increment (fast, atomic)
        try:
            pipe = self.redis.pipeline()
            pipe.incr(monthly_key)
            pipe.expire(monthly_key, monthly_ttl)
            pipe.incr(daily_key)
            pipe.expire(daily_key, daily_ttl)

            if org_id:
                pipe.incr(org_key)
                pipe.expire(org_key, org_ttl)

            await pipe.execute()
        except Exception as e:
            logger.error(f"Redis increment error: {e}")

        # PostgreSQL insert (persistent, historical)
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO api_usage (
                        user_id, org_id, endpoint, method, response_status,
                        tokens_used, cost_credits, billing_period
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    user_id, org_id, endpoint, method, response_status,
                    tokens_used, float(cost_credits), billing_period
                )

                # Update usage_quotas table
                await conn.execute(
                    """
                    UPDATE usage_quotas
                    SET api_calls_used = api_calls_used + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                    """,
                    user_id
                )
        except Exception as e:
            logger.error(f"PostgreSQL insert error: {e}")

    async def get_usage_stats(
        self,
        user_id: str,
        period: str = "current"
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Args:
            user_id: Keycloak user ID
            period: "current" (current billing cycle), "daily", "weekly", "monthly"

        Returns:
            {
                "user_id": str,
                "tier": str,
                "period": str,
                "used": int,
                "limit": int,
                "remaining": int,
                "reset_date": str,
                "daily_usage": int,
                "monthly_usage": int,
                "history": [...] (if requested)
            }
        """
        if not self.db_pool:
            await self.initialize()

        # Get user tier
        tier_info = await self._get_user_tier(user_id)
        tier = tier_info["tier"]
        tier_limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["trial"])

        # Get current usage
        current_usage = await self._get_current_usage(user_id, tier_limits["reset_period"])

        # Calculate remaining
        monthly_limit = tier_limits["monthly_limit"]
        remaining = monthly_limit - current_usage["monthly"] if monthly_limit > 0 else -1

        result = {
            "user_id": user_id,
            "tier": tier,
            "status": tier_info["status"],
            "period": period,
            "used": current_usage["monthly"],
            "limit": monthly_limit if monthly_limit > 0 else -1,
            "remaining": remaining,
            "reset_date": current_usage["reset_date"],
            "daily_usage": current_usage["daily"],
            "monthly_usage": current_usage["monthly"],
            "daily_limit": tier_limits["daily_limit"] if tier_limits["daily_limit"] > 0 else -1
        }

        # Add historical data if requested
        if period in ["daily", "weekly", "monthly"]:
            result["history"] = await self._get_usage_history(user_id, period)

        return result

    async def _get_usage_history(
        self,
        user_id: str,
        period: str
    ) -> List[Dict[str, Any]]:
        """Get historical usage data"""
        if period == "daily":
            days = 1
        elif period == "weekly":
            days = 7
        elif period == "monthly":
            days = 30
        else:
            days = 7

        start_date = datetime.utcnow() - timedelta(days=days)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as calls,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_credits) as total_cost
                FROM api_usage
                WHERE user_id = $1 AND timestamp >= $2
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                """,
                user_id, start_date
            )

            return [
                {
                    "date": row["date"].isoformat(),
                    "calls": row["calls"],
                    "tokens": row["total_tokens"] or 0,
                    "cost": float(row["total_cost"] or 0)
                }
                for row in rows
            ]

    async def reset_quota(self, user_id: str) -> bool:
        """
        Reset usage quota for a user (called on billing cycle reset).

        Args:
            user_id: Keycloak user ID

        Returns:
            True if successful
        """
        if not self.db_pool or not self.redis:
            await self.initialize()

        try:
            # Clear Redis counters
            now = datetime.utcnow()
            keys_to_delete = [
                f"usage:{user_id}:current:calls",
                f"usage:{user_id}:{now.strftime('%Y-%m')}:calls"
            ]
            await self.redis.delete(*keys_to_delete)

            # Update PostgreSQL
            next_reset = (now.replace(day=1) + timedelta(days=32)).replace(day=1)

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE usage_quotas
                    SET api_calls_used = 0,
                        reset_date = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                    """,
                    user_id, next_reset.date()
                )

            logger.info(f"Reset quota for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset quota for {user_id}: {e}")
            return False

    def get_tier_limits(self, tier: str) -> Dict[str, Any]:
        """
        Get API call limits for a subscription tier.

        Args:
            tier: Tier code (trial, starter, professional, enterprise)

        Returns:
            {
                "daily_limit": int,
                "monthly_limit": int,
                "reset_period": str
            }
        """
        return self.TIER_LIMITS.get(tier, self.TIER_LIMITS["trial"])


# Global singleton instance
usage_tracker = UsageTracker()
