"""
Dynamic Pricing Engine - Core pricing calculation for BYOK and Platform usage

This module handles:
- BYOK credit calculation with provider-specific markups
- Platform key credit calculation with tier-based pricing
- Free monthly BYOK credit allocation and tracking
- Cost calculation and preview
- Integration with PostgreSQL pricing_rules table

Author: System Architecture Designer
Date: January 12, 2025
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import json

import asyncpg
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class PricingEngine:
    """
    Dynamic pricing engine for BYOK and Platform usage.

    Features:
    - Provider-specific BYOK markups (5-15%)
    - Tier-based Platform markups (0-80%)
    - Free monthly BYOK credits
    - Real-time cost calculation
    - Audit trail integration
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize pricing engine with database pool.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        self._cache = {}  # Simple in-memory cache for pricing rules
        self._cache_ttl = 300  # 5 minutes

    async def calculate_byok_cost(
        self,
        provider: str,
        base_cost: Decimal,
        user_tier: str,
        user_id: str,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate cost for BYOK request.

        Args:
            provider: Provider name (e.g., 'openrouter', 'openai')
            base_cost: Provider's base cost in credits
            user_tier: User's subscription tier
            user_id: User identifier
            model: Model name (optional, for metadata)
            tokens_used: Tokens consumed (optional, for metadata)

        Returns:
            {
                'base_cost': float,
                'markup': float,
                'final_cost': float,
                'credits_charged': float,
                'free_credits_used': float,
                'paid_credits_used': float,
                'rule_applied': dict,
                'metadata': dict
            }
        """
        async with self.db_pool.acquire() as conn:
            # Get pricing rule (provider-specific or global)
            rule = await conn.fetchrow(
                """
                SELECT * FROM pricing_rules
                WHERE rule_type = 'byok'
                  AND (provider = $1 OR provider = '*')
                  AND is_active = TRUE
                  AND $2 = ANY(applies_to_tiers)
                ORDER BY
                    CASE WHEN provider = $1 THEN 1 ELSE 0 END DESC,
                    priority DESC
                LIMIT 1
                """,
                provider, user_tier
            )

            if not rule:
                # Fallback to 10% markup
                logger.warning(f"No BYOK pricing rule found for {provider}/{user_tier}, using 10% default")
                markup_value = Decimal('0.10')
                markup_type = 'percentage'
                min_charge = Decimal('0.001')
                rule_name = 'Default 10% Markup'
                rule_id = None
            else:
                markup_value = rule['markup_value']
                markup_type = rule['markup_type']
                min_charge = rule['min_charge']
                rule_name = rule['rule_name']
                rule_id = str(rule['id'])

            # Calculate markup
            if markup_type == 'percentage':
                markup = base_cost * markup_value
            elif markup_type == 'fixed':
                markup = markup_value
            else:  # 'none'
                markup = Decimal('0')

            # Apply minimum charge
            final_cost = max(base_cost + markup, min_charge)

            # Check if user has free BYOK credits
            free_credits = await self._get_user_byok_credits(conn, user_id, user_tier)

            if free_credits >= final_cost:
                # Deduct from free credits
                free_credits_used = final_cost
                paid_credits_used = Decimal('0')
                await self._deduct_byok_credits(conn, user_id, free_credits_used)
            elif free_credits > 0:
                # Use remaining free credits, charge rest
                free_credits_used = free_credits
                paid_credits_used = final_cost - free_credits
                await self._deduct_byok_credits(conn, user_id, free_credits_used)
            else:
                # Charge full amount
                free_credits_used = Decimal('0')
                paid_credits_used = final_cost

            return {
                'base_cost': float(base_cost),
                'markup': float(markup),
                'final_cost': float(final_cost),
                'credits_charged': float(final_cost),
                'free_credits_used': float(free_credits_used),
                'paid_credits_used': float(paid_credits_used),
                'rule_applied': {
                    'rule_id': rule_id,
                    'rule_name': rule_name,
                    'provider': provider,
                    'markup_type': markup_type,
                    'markup_percentage': float(markup_value * 100) if markup_type == 'percentage' else None
                },
                'metadata': {
                    'model': model,
                    'tokens_used': tokens_used,
                    'user_tier': user_tier,
                    'calculation_time': datetime.utcnow().isoformat()
                }
            }

    async def calculate_platform_cost(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        user_tier: str,
        base_cost: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate cost for Platform key request.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            model: Model name (e.g., 'gpt-4', 'claude-3.5-sonnet')
            tokens_used: Number of tokens consumed
            user_tier: User's subscription tier
            base_cost: Optional base cost (if pre-calculated)

        Returns:
            {
                'base_cost': float,
                'markup': float,
                'final_cost': float,
                'credits_charged': float,
                'rule_applied': dict,
                'metadata': dict
            }
        """
        async with self.db_pool.acquire() as conn:
            # Get platform pricing rule for tier
            rule = await conn.fetchrow(
                """
                SELECT * FROM pricing_rules
                WHERE rule_type = 'platform'
                  AND tier_code = $1
                  AND is_active = TRUE
                LIMIT 1
                """,
                user_tier
            )

            if not rule:
                logger.warning(f"No platform pricing rule for {user_tier}, using 0% default")
                markup_value = Decimal('0')
                markup_type = 'percentage'
                provider_overrides = {}
                rule_name = 'Default 0% Markup'
                rule_id = None
            else:
                markup_value = rule['markup_value']
                markup_type = rule['markup_type']
                provider_overrides = rule['provider_overrides'] or {}
                rule_name = rule['rule_name']
                rule_id = str(rule['id'])

            # Check for provider-specific override
            provider_override_applied = False
            if provider in provider_overrides:
                override = provider_overrides[provider]
                if 'markup' in override:
                    markup_value = Decimal(str(override['markup']))
                    provider_override_applied = True
                    logger.debug(f"Using provider override for {provider}: {markup_value}")

            # Calculate base cost if not provided
            if base_cost is None:
                base_cost = await self._get_model_base_cost(conn, provider, model, tokens_used)

            # Calculate markup
            if markup_type == 'percentage':
                markup = base_cost * markup_value
            elif markup_type == 'multiplier':
                markup = base_cost * (markup_value - 1)  # e.g., 1.5x multiplier = 50% markup
            elif markup_type == 'fixed':
                markup = markup_value
            else:
                markup = Decimal('0')

            final_cost = base_cost + markup

            return {
                'base_cost': float(base_cost),
                'markup': float(markup),
                'final_cost': float(final_cost),
                'credits_charged': float(final_cost),
                'rule_applied': {
                    'rule_id': rule_id,
                    'rule_name': rule_name,
                    'tier_code': user_tier,
                    'markup_type': markup_type,
                    'markup_percentage': float(markup_value * 100) if markup_type == 'percentage' else None,
                    'provider_override': provider_override_applied,
                    'provider': provider
                },
                'metadata': {
                    'model': model,
                    'tokens_used': tokens_used,
                    'user_tier': user_tier,
                    'calculation_time': datetime.utcnow().isoformat()
                }
            }

    async def _get_user_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        tier_code: str
    ) -> Decimal:
        """Get user's remaining free BYOK credits."""
        result = await conn.fetchrow(
            """
            SELECT credits_remaining FROM user_byok_credits
            WHERE user_id = $1 AND tier_code = $2
            """,
            user_id, tier_code
        )

        if not result:
            # Auto-provision BYOK credits if user doesn't have entry
            return await self._provision_byok_credits(conn, user_id, tier_code)

        return result['credits_remaining']

    async def _provision_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        tier_code: str
    ) -> Decimal:
        """Provision monthly BYOK credits for new user."""
        # Get tier's monthly allowance
        rule = await conn.fetchrow(
            """
            SELECT free_credits_monthly FROM pricing_rules
            WHERE rule_type = 'byok'
              AND $1 = ANY(applies_to_tiers)
              AND is_active = TRUE
              AND free_credits_monthly > 0
            ORDER BY free_credits_monthly DESC
            LIMIT 1
            """,
            tier_code
        )

        allowance = rule['free_credits_monthly'] if rule else Decimal('0')

        if allowance > 0:
            await conn.execute(
                """
                INSERT INTO user_byok_credits (
                    user_id, tier_code, monthly_allowance, credits_remaining
                )
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (user_id, tier_code) DO NOTHING
                """,
                user_id, tier_code, allowance
            )

            logger.info(f"Provisioned {allowance} BYOK credits for {user_id}/{tier_code}")

        return allowance

    async def _deduct_byok_credits(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        amount: Decimal
    ):
        """Deduct from user's free BYOK credits."""
        await conn.execute(
            """
            UPDATE user_byok_credits
            SET credits_used = credits_used + $1,
                credits_remaining = credits_remaining - $1,
                updated_at = NOW()
            WHERE user_id = $2
            """,
            amount, user_id
        )

    async def _get_model_base_cost(
        self,
        conn: asyncpg.Connection,
        provider: str,
        model: str,
        tokens_used: int
    ) -> Decimal:
        """
        Get base cost from model pricing table or hardcoded pricing.

        This would query your existing MODEL_PRICING or fetch from LiteLLM.
        For now, using hardcoded fallback values.
        """
        # Import hardcoded pricing from litellm_credit_system.py
        # In production, this should query a database table

        # Simplified pricing lookup (replace with actual database query)
        MODEL_PRICING_DEFAULTS = {
            # OpenAI
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0015,

            # Anthropic
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025,
            "claude-3.5-sonnet": 0.003,

            # Default
            "default": 0.01
        }

        # Try to get model-specific pricing
        cost_per_1k = MODEL_PRICING_DEFAULTS.get(model, MODEL_PRICING_DEFAULTS["default"])

        base_cost = Decimal(str(cost_per_1k)) * (tokens_used / 1000)
        return base_cost

    async def get_byok_balance(self, user_id: str, tier_code: str) -> Dict[str, Any]:
        """
        Get user's BYOK credit balance.

        Returns:
            {
                'monthly_allowance': float,
                'credits_used': float,
                'credits_remaining': float,
                'last_reset': str (ISO datetime),
                'next_reset': str (ISO datetime),
                'days_until_reset': int
            }
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT * FROM user_byok_credits
                WHERE user_id = $1 AND tier_code = $2
                """,
                user_id, tier_code
            )

            if not result:
                # Provision if doesn't exist
                await self._provision_byok_credits(conn, user_id, tier_code)
                result = await conn.fetchrow(
                    """
                    SELECT * FROM user_byok_credits
                    WHERE user_id = $1 AND tier_code = $2
                    """,
                    user_id, tier_code
                )

            if result:
                next_reset = result['next_reset']
                days_until_reset = (next_reset - datetime.utcnow()).days

                return {
                    'monthly_allowance': float(result['monthly_allowance']),
                    'credits_used': float(result['credits_used']),
                    'credits_remaining': float(result['credits_remaining']),
                    'last_reset': result['last_reset'].isoformat(),
                    'next_reset': next_reset.isoformat(),
                    'days_until_reset': days_until_reset
                }
            else:
                return {
                    'monthly_allowance': 0.0,
                    'credits_used': 0.0,
                    'credits_remaining': 0.0,
                    'last_reset': None,
                    'next_reset': None,
                    'days_until_reset': 0
                }

    async def calculate_cost_comparison(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        user_tier: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate side-by-side cost comparison: BYOK vs Platform.

        Useful for showing users potential savings with BYOK.

        Returns:
            {
                'byok': dict (from calculate_byok_cost),
                'platform': dict (from calculate_platform_cost),
                'savings': {
                    'credits': float,
                    'percentage': float,
                    'message': str
                }
            }
        """
        # Calculate base cost (use same for both)
        async with self.db_pool.acquire() as conn:
            base_cost = await self._get_model_base_cost(conn, provider, model, tokens_used)

        # Calculate BYOK cost
        byok_cost = await self.calculate_byok_cost(
            provider, base_cost, user_tier, user_id, model, tokens_used
        )

        # Calculate Platform cost
        platform_cost = await self.calculate_platform_cost(
            provider, model, tokens_used, user_tier, base_cost
        )

        # Calculate savings
        savings_credits = platform_cost['final_cost'] - byok_cost['final_cost']
        savings_percentage = (savings_credits / platform_cost['final_cost'] * 100) if platform_cost['final_cost'] > 0 else 0

        return {
            'byok': byok_cost,
            'platform': platform_cost,
            'savings': {
                'credits': savings_credits,
                'percentage': savings_percentage,
                'message': f"Save {savings_credits:.4f} credits ({savings_percentage:.1f}%) with BYOK"
            }
        }


# Singleton instance
_pricing_engine: Optional[PricingEngine] = None


async def get_pricing_engine(db_pool: asyncpg.Pool) -> PricingEngine:
    """Get or create singleton pricing engine instance."""
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = PricingEngine(db_pool)
    return _pricing_engine
