"""
Epic 1.8: Credit & Usage Metering System
Module: usage_metering.py

Purpose: Detailed usage tracking and analytics for all UC-Cloud services
         (LLMs, embeddings, TTS, STT, Center-Deep search, etc.)

Author: Backend Team Lead
Date: October 23, 2025
"""

import asyncpg
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os
from audit_logger import audit_logger

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UsageMeter:
    """
    Tracks and analyzes usage events across all UC-Cloud services.

    Services tracked:
    - openrouter: LLM chat completions
    - embedding: Text embeddings
    - tts: Text-to-speech (Unicorn Orator)
    - stt: Speech-to-text (Unicorn Amanuensis)
    - center-deep: AI metasearch queries
    - reranker: Document reranking
    - brigade: Agent executions

    Features:
    - Real-time usage tracking
    - Cost calculation with markup
    - Free tier detection and tracking
    - Per-model, per-service analytics
    - Time-series aggregations
    """

    # Cost per token for different model tiers (in dollars)
    MODEL_COSTS = {
        # OpenRouter models (examples, actual costs from provider)
        "gpt-4": {"input": Decimal("0.00003"), "output": Decimal("0.00006")},
        "gpt-3.5-turbo": {"input": Decimal("0.000001"), "output": Decimal("0.000002")},
        "claude-3-opus": {"input": Decimal("0.000015"), "output": Decimal("0.000075")},
        "claude-3-sonnet": {"input": Decimal("0.000003"), "output": Decimal("0.000015")},

        # Embedding models
        "bge-base-en-v1.5": {"per_token": Decimal("0.0000001")},
        "text-embedding-ada-002": {"per_token": Decimal("0.0000001")},

        # TTS (per character)
        "unicorn-orator": {"per_char": Decimal("0.000015")},

        # STT (per second)
        "whisperx": {"per_second": Decimal("0.0001")},

        # Center-Deep search (per query)
        "center-deep": {"per_query": Decimal("0.001")}
    }

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool"""
        if self.db_pool:
            return

        try:
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "unicorn"),
                password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
                database=os.getenv("POSTGRES_DB", "unicorn_db"),
                min_size=5,
                max_size=20
            )
            logger.info("UsageMeter database pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
            logger.info("UsageMeter database pool closed")

    async def track_usage(
        self,
        user_id: str,
        service: str,
        model: Optional[str] = None,
        tokens: Optional[int] = None,
        cost: Optional[Decimal] = None,
        is_free: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a usage event.

        Args:
            user_id: Keycloak user ID
            service: Service name (openrouter, embedding, tts, stt, center-deep)
            model: Model name (optional)
            tokens: Tokens used (for LLM/embedding)
            cost: Total cost in credits (optional, will be calculated if not provided)
            is_free: Whether this is free tier usage
            metadata: Additional metadata (request_id, ip, endpoint, etc.)

        Returns:
            Created usage event record
        """
        if not self.db_pool:
            await self.initialize()

        # Calculate cost if not provided
        if cost is None and not is_free:
            cost = self.calculate_cost(tokens, model, is_free)

        # Calculate platform markup
        if cost and not is_free:
            markup = cost * Decimal("0.10")  # 10% platform markup
            provider_cost = cost - markup
        else:
            provider_cost = Decimal("0.00")
            markup = Decimal("0.00")
            cost = Decimal("0.00")

        import json

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO usage_events (
                    user_id, service, model, tokens_used,
                    cost, is_free, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, created_at
                """,
                user_id, service, model, tokens,
                cost, is_free, json.dumps(metadata) if metadata else None
            )

        logger.debug(f"Tracked usage for {user_id}: {service}/{model} - {cost} credits")

        return {
            "id": row["id"],
            "user_id": user_id,
            "service": service,
            "model": model,
            "tokens_used": tokens,
            "provider_cost": provider_cost,
            "platform_markup": markup,
            "total_cost": cost,
            "is_free_tier": is_free,
            "created_at": row["created_at"]
        }

    async def get_usage_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated usage summary for a user.

        Args:
            user_id: Keycloak user ID
            start_date: Start date (optional, defaults to 30 days ago)
            end_date: End date (optional, defaults to now)

        Returns:
            {
                "total_events": int,
                "total_tokens": int,
                "total_cost": Decimal,
                "free_tier_events": int,
                "paid_tier_events": int,
                "services": {...},
                "period": {...}
            }
        """
        if not self.db_pool:
            await self.initialize()

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            # Overall summary
            summary = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_events,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(CASE WHEN is_free THEN 1 ELSE 0 END), 0) as free_tier_events,
                    COALESCE(SUM(CASE WHEN NOT is_free THEN 1 ELSE 0 END), 0) as paid_tier_events
                FROM usage_events
                WHERE user_id = $1
                  AND created_at >= $2
                  AND created_at <= $3
                """,
                user_id, start_date, end_date
            )

            # Per-service breakdown
            services = await conn.fetch(
                """
                SELECT
                    service,
                    COUNT(*) as event_count,
                    COALESCE(SUM(tokens_used), 0) as tokens,
                    COALESCE(SUM(cost), 0) as cost
                FROM usage_events
                WHERE user_id = $1
                  AND created_at >= $2
                  AND created_at <= $3
                GROUP BY service
                ORDER BY cost DESC
                """,
                user_id, start_date, end_date
            )

        return {
            "total_events": summary["total_events"],
            "total_tokens": int(summary["total_tokens"]),
            "total_cost": summary["total_cost"],
            "free_tier_events": summary["free_tier_events"],
            "paid_tier_events": summary["paid_tier_events"],
            "services": {
                row["service"]: {
                    "event_count": row["event_count"],
                    "tokens": int(row["tokens"]),
                    "cost": row["cost"]
                }
                for row in services
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def get_usage_by_model(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage breakdown by model.

        Args:
            user_id: Keycloak user ID
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            List of model usage statistics
        """
        if not self.db_pool:
            await self.initialize()

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    service,
                    model,
                    COUNT(*) as event_count,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(AVG(tokens_used), 0) as avg_tokens,
                    COALESCE(SUM(CASE WHEN is_free THEN 1 ELSE 0 END), 0) as free_events
                FROM usage_events
                WHERE user_id = $1
                  AND created_at >= $2
                  AND created_at <= $3
                  AND model IS NOT NULL
                GROUP BY service, model
                ORDER BY cost DESC
                """,
                user_id, start_date, end_date
            )

        return [
            {
                "service": row["service"],
                "model": row["model"],
                "event_count": row["event_count"],
                "total_tokens": int(row["total_tokens"]),
                "total_cost": row["total_cost"],
                "avg_tokens": float(row["avg_tokens"]) if row["avg_tokens"] else 0,
                "free_events": row["free_events"]
            }
            for row in rows
        ]

    async def get_usage_by_service(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage breakdown by service.

        Args:
            user_id: Keycloak user ID
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            List of service usage statistics
        """
        if not self.db_pool:
            await self.initialize()

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    service,
                    COUNT(*) as event_count,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COUNT(DISTINCT model) as unique_models,
                    COALESCE(SUM(CASE WHEN is_free THEN 1 ELSE 0 END), 0) as free_events
                FROM usage_events
                WHERE user_id = $1
                  AND created_at >= $2
                  AND created_at <= $3
                GROUP BY service
                ORDER BY cost DESC
                """,
                user_id, start_date, end_date
            )

        return [
            {
                "service": row["service"],
                "event_count": row["event_count"],
                "total_tokens": int(row["total_tokens"]),
                "total_cost": row["total_cost"],
                "unique_models": row["unique_models"],
                "free_events": row["free_events"]
            }
            for row in rows
        ]

    async def get_free_tier_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get free tier usage statistics.

        Args:
            user_id: Keycloak user ID
            start_date: Start date (optional, defaults to current month)

        Returns:
            Free tier usage summary
        """
        if not self.db_pool:
            await self.initialize()

        if not start_date:
            # Current month
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)

        end_date = datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            summary = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as free_events,
                    COALESCE(SUM(tokens_used), 0) as free_tokens,
                    COUNT(DISTINCT model) as free_models_used
                FROM usage_events
                WHERE user_id = $1
                  AND is_free = true
                  AND created_at >= $2
                  AND created_at <= $3
                """,
                user_id, start_date, end_date
            )

            # Per-model breakdown
            models = await conn.fetch(
                """
                SELECT
                    model,
                    COUNT(*) as event_count,
                    COALESCE(SUM(tokens_used), 0) as tokens
                FROM usage_events
                WHERE user_id = $1
                  AND is_free = true
                  AND created_at >= $2
                  AND created_at <= $3
                  AND model IS NOT NULL
                GROUP BY model
                ORDER BY event_count DESC
                """,
                user_id, start_date, end_date
            )

        return {
            "total_free_events": summary["free_events"],
            "total_free_tokens": int(summary["free_tokens"]),
            "unique_free_models": summary["free_models_used"],
            "models": [
                {
                    "model": row["model"],
                    "event_count": row["event_count"],
                    "tokens": int(row["tokens"])
                }
                for row in models
            ],
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def get_daily_usage(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get today's usage statistics.

        Args:
            user_id: Keycloak user ID

        Returns:
            Today's usage summary
        """
        if not self.db_pool:
            await self.initialize()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        async with self.db_pool.acquire() as conn:
            summary = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_events,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(SUM(cost), 0) as total_cost,
                    COALESCE(SUM(CASE WHEN is_free THEN 1 ELSE 0 END), 0) as free_events
                FROM usage_events
                WHERE user_id = $1
                  AND created_at >= $2
                  AND created_at < $3
                """,
                user_id, today, tomorrow
            )

        return {
            "date": today.date().isoformat(),
            "total_events": summary["total_events"],
            "total_tokens": int(summary["total_tokens"]),
            "total_cost": summary["total_cost"],
            "free_events": summary["free_events"]
        }

    def calculate_cost(
        self,
        tokens: Optional[int],
        model: Optional[str],
        is_free: bool
    ) -> Decimal:
        """
        Calculate cost for a usage event.

        Args:
            tokens: Number of tokens used
            model: Model name
            is_free: Whether this is free tier

        Returns:
            Cost in credits
        """
        if is_free or not tokens or not model:
            return Decimal("0.00")

        # Get model cost
        model_key = model.split("/")[-1].lower()  # Extract model name
        for key in self.MODEL_COSTS:
            if key in model_key:
                cost_info = self.MODEL_COSTS[key]

                # LLM models (input/output tokens)
                if "input" in cost_info:
                    # Assume 50/50 split for simplicity
                    cost = (cost_info["input"] + cost_info["output"]) / 2 * tokens
                    return cost

                # Other services (per token/char/second)
                elif "per_token" in cost_info:
                    return cost_info["per_token"] * tokens

        # Default fallback (GPT-3.5 turbo pricing)
        return Decimal("0.000001") * tokens


# Global instance
usage_meter = UsageMeter()
