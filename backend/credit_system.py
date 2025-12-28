"""
Epic 1.8: Credit & Usage Metering System
Module: credit_system.py

Purpose: Core credit management system with atomic transactions, audit logging,
         and comprehensive credits_remaining management.

Author: Backend Team Lead
Date: October 23, 2025
"""

import asyncpg
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import os
from contextlib import asynccontextmanager
from audit_logger import audit_logger
from email_notifications import EmailNotificationService

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Email notification service
email_service = EmailNotificationService()


class CreditError(Exception):
    """Base exception for credit system errors"""
    pass


class InsufficientCreditsError(CreditError):
    """Raised when user has insufficient credits"""
    pass


class CreditManager:
    """
    Manages user credit balances with atomic transactions and audit logging.

    Features:
    - Atomic credit operations (ACID-compliant)
    - Monthly credit allocations based on subscription tier
    - Bonus credit management
    - Free tier usage tracking
    - Comprehensive audit trail
    - Transaction rollback on errors
    """

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self._tier_allocations = {
            "trial": Decimal("5.00"),        # $1/week ≈ $4/month → $5 credits
            "starter": Decimal("20.00"),     # $19/month → $20 credits
            "professional": Decimal("60.00"), # $49/month → $60 credits
            "enterprise": Decimal("999999.99")  # $99/month → unlimited
        }

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
            logger.info("CreditManager database pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
            logger.info("CreditManager database pool closed")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions with automatic rollback"""
        if not self.db_pool:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        """
        Get current credit balance for a user.
        Auto-provisions credit account if user doesn't have one (first-request pattern).

        Args:
            user_id: Keycloak user ID

        Returns:
            {
                "user_id": str,
                "credits_remaining": Decimal,
                "credits_allocated": Decimal,
                "bonus_credits": Decimal,
                "free_tier_used": Decimal,
                "last_reset": datetime,
                "updated_at": datetime,
                "created_at": datetime
            }
        """
        if not self.db_pool:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, credits_remaining, credits_allocated, tier,
                        last_reset, updated_at, created_at
                FROM user_credits
                WHERE user_id = $1
                """,
                user_id
            )

            if not row:
                # AUTO-PROVISION: User doesn't exist yet, create with default trial tier
                logger.info(f"Auto-provisioning credit account for new user: {user_id}")
                return await self.create_user_credits(user_id, tier="trial")

            # Map database columns to API response fields
            return {
                "user_id": row["user_id"],
                "balance": row["credits_remaining"],  # DB column: credits_remaining
                "allocated_monthly": row["credits_allocated"],  # DB column: credits_allocated
                "bonus_credits": Decimal("0.00"),  # Not stored in DB
                "free_tier_used": Decimal("0.00"),  # Calculated: allocated - remaining
                "reset_date": row["last_reset"],  # DB column: last_reset
                "last_updated": row["updated_at"],  # DB column: updated_at
                "tier": row["tier"],
                "created_at": row["created_at"]
            }

    async def create_user_credits(
        self,
        user_id: str,
        tier: str = "trial"
    ) -> Dict[str, Any]:
        """
        Create initial credit record for a new user.

        Args:
            user_id: Keycloak user ID
            tier: Subscription tier (trial, starter, professional, enterprise)

        Returns:
            Created credit record
        """
        allocated = self._tier_allocations.get(tier, Decimal("0.00"))
        last_reset = datetime.utcnow() + timedelta(days=30)

        async with self.transaction() as conn:
            # Create user credits record
            await conn.execute(
                """
                INSERT INTO user_credits (
                    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id, allocated, allocated, tier, allocated, last_reset
            )

            # Log allocation transaction (use 'purchase' type for initial allocation)
            await self._log_transaction(
                conn, user_id, allocated, allocated,
                "purchase", metadata={
                    "tier": tier,
                    "reason": "initial_allocation",
                    "source": "trial_signup"
                }
            )

            # Audit log
            await audit_logger.log(
                action="credit.create",
                result="success",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                metadata={
                    "tier": tier,
                    "allocated": float(allocated),
                    "last_reset": last_reset.isoformat()
                }
            )

        # Send welcome email (don't fail transaction if email fails)
        try:
            await email_service.send_welcome_email(user_id, tier)
            logger.info(f"Welcome email sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to user {user_id}: {e}")

        return await self.get_balance(user_id)

    async def allocate_credits(
        self,
        user_id: str,
        amount: Decimal,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Allocate credits to a user (admin operation).

        Args:
            user_id: Keycloak user ID
            amount: Credit amount to allocate
            source: Source of allocation (tier_upgrade, manual, bonus, etc.)
            metadata: Additional context

        Returns:
            Updated credits_remaining information
        """
        if amount <= 0:
            raise ValueError("Allocation amount must be positive")

        async with self.transaction() as conn:
            # Get current balance
            current = await conn.fetchrow(
                "SELECT credits_remaining FROM user_credits WHERE user_id = $1",
                user_id
            )

            if not current:
                # Create user first
                await self.create_user_credits(user_id)
                current_credits_remaining = Decimal("0.00")
            else:
                current_credits_remaining = current["credits_remaining"]

            new_credits_remaining = current_credits_remaining + amount

            # Update balance
            await conn.execute(
                """
                UPDATE user_credits
                SET credits_remaining = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                new_credits_remaining, user_id
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_credits_remaining,
                "allocation", metadata={
                    "source": source,
                    **(metadata or {})
                }
            )

            # Audit log
            await audit_logger.log(
                action="credit.allocate",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                details={
                    "amount": float(amount),
                    "source": source,
                    "new_balance": float(new_credits_remaining),
                    "metadata": metadata
                },
                status="success"
            )

        return await self.get_balance(user_id)

    async def deduct_credits(
        self,
        user_id: str,
        amount: Decimal,
        service: str,
        model: Optional[str] = None,
        cost_breakdown: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deduct credits from user credits_remaining (atomic operation).

        Args:
            user_id: Keycloak user ID
            amount: Credit amount to deduct
            service: Service name (openrouter, embedding, tts, etc.)
            model: Model name (optional)
            cost_breakdown: {provider_cost, markup, total}
            metadata: Additional context

        Returns:
            Updated credits_remaining information

        Raises:
            InsufficientCreditsError: If user has insufficient credits
        """
        if amount <= 0:
            raise ValueError("Deduction amount must be positive")

        async with self.transaction() as conn:
            # Check current credits_remaining with row lock
            current = await conn.fetchrow(
                """
                SELECT credits_remaining FROM user_credits
                WHERE user_id = $1
                FOR UPDATE
                """,
                user_id
            )

            if not current:
                raise CreditError(f"User {user_id} does not have a credit account")

            current_credits_remaining = current["credits_remaining"]

            # Check sufficient balance
            if current_credits_remaining < amount:
                await audit_logger.log(
                    action="credit.deduct_failed",
                    user_id=user_id,
                    resource_type="user_credits",
                    resource_id=user_id,
                    details={
                        "amount": float(amount),
                        "current_balance": float(current_credits_remaining),
                        "reason": "insufficient_credits"
                    },
                    status="failure"
                )
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: {amount}, Available: {current_credits_remaining}"
                )

            new_credits_remaining = current_credits_remaining - amount

            # Update balance
            await conn.execute(
                """
                UPDATE user_credits
                SET credits_remaining = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                new_credits_remaining, user_id
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, -amount, new_credits_remaining,
                "usage", service=service, model=model,
                cost_breakdown=cost_breakdown, metadata=metadata
            )

            # Audit log
            await audit_logger.log(
                action="credit.deduct",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                details={
                    "amount": float(amount),
                    "service": service,
                    "model": model,
                    "new_balance": float(new_credits_remaining),
                    "cost_breakdown": cost_breakdown
                },
                status="success"
            )

        # Send low balance alert if credits are running low (don't fail transaction if email fails)
        if new_credits_remaining < Decimal("100.00") and new_credits_remaining > Decimal("0.00"):
            try:
                await email_service.send_low_balance_alert(user_id, new_credits_remaining)
                logger.info(f"Low balance alert sent to user {user_id} (balance: {new_credits_remaining})")
            except Exception as e:
                logger.error(f"Failed to send low balance alert to user {user_id}: {e}")

        return await self.get_balance(user_id)

    async def add_bonus_credits(
        self,
        user_id: str,
        amount: Decimal,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add bonus credits to user account.

        Args:
            user_id: Keycloak user ID
            amount: Bonus credit amount
            reason: Reason for bonus (referral, promotion, compensation, etc.)
            metadata: Additional context

        Returns:
            Updated credits_remaining information
        """
        if amount <= 0:
            raise ValueError("Bonus amount must be positive")

        async with self.transaction() as conn:
            # Update credits_remaining (note: bonus_credits column doesn't exist in DB)
            result = await conn.fetchrow(
                """
                UPDATE user_credits
                SET credits_remaining = credits_remaining + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                RETURNING credits_remaining
                """,
                amount, user_id
            )

            if not result:
                raise CreditError(f"User {user_id} does not have a credit account")

            new_credits_remaining = result["credits_remaining"]

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_credits_remaining,
                "bonus", metadata={
                    "reason": reason,
                    **(metadata or {})
                }
            )

            # Audit log
            await audit_logger.log(
                action="credit.bonus",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                details={
                    "amount": float(amount),
                    "reason": reason,
                    "new_balance": float(new_credits_remaining),
                    "metadata": metadata
                },
                status="success"
            )

        return await self.get_balance(user_id)

    async def refund_credits(
        self,
        user_id: str,
        amount: Decimal,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refund credits to user account.

        Args:
            user_id: Keycloak user ID
            amount: Refund amount
            reason: Reason for refund
            metadata: Additional context (e.g., original transaction ID)

        Returns:
            Updated credits_remaining information
        """
        if amount <= 0:
            raise ValueError("Refund amount must be positive")

        async with self.transaction() as conn:
            # Update balance
            result = await conn.fetchrow(
                """
                UPDATE user_credits
                SET credits_remaining = credits_remaining + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                RETURNING credits_remaining
                """,
                amount, user_id
            )

            if not result:
                raise CreditError(f"User {user_id} does not have a credit account")

            new_credits_remaining = result["credits_remaining"]

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_credits_remaining,
                "refund", metadata={
                    "reason": reason,
                    **(metadata or {})
                }
            )

            # Audit log
            await audit_logger.log(
                action="credit.refund",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                details={
                    "amount": float(amount),
                    "reason": reason,
                    "new_balance": float(new_credits_remaining),
                    "metadata": metadata
                },
                status="success"
            )

        return await self.get_balance(user_id)

    async def reset_monthly_credits(
        self,
        user_id: str,
        new_tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reset monthly credits based on subscription tier.

        Args:
            user_id: Keycloak user ID
            new_tier: New subscription tier (if changed)

        Returns:
            Updated credits_remaining information
        """
        async with self.transaction() as conn:
            # Get current allocation
            current = await conn.fetchrow(
                """
                SELECT credits_allocated, credits_remaining
                FROM user_credits
                WHERE user_id = $1
                """,
                user_id
            )

            if not current:
                raise CreditError(f"User {user_id} does not have a credit account")

            # Determine new allocation
            if new_tier:
                new_allocation = self._tier_allocations.get(new_tier, Decimal("0.00"))
            else:
                new_allocation = current["credits_allocated"]

            # Calculate new credits_remaining (add new allocation)
            new_credits_remaining = current["credits_remaining"] + new_allocation
            next_reset = datetime.utcnow() + timedelta(days=30)

            # Update credits
            await conn.execute(
                """
                UPDATE user_credits
                SET credits_remaining = $1,
                    credits_allocated = $2,
                    last_reset = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
                """,
                new_credits_remaining, new_allocation, next_reset, user_id
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, new_allocation, new_credits_remaining,
                "monthly_reset", metadata={
                    "tier": new_tier,
                    "allocation": float(new_allocation),
                    "next_reset": next_reset.isoformat()
                }
            )

            # Audit log
            await audit_logger.log(
                action="credit.monthly_reset",
                user_id=user_id,
                resource_type="user_credits",
                resource_id=user_id,
                details={
                    "new_allocation": float(new_allocation),
                    "new_balance": float(new_credits_remaining),
                    "tier": new_tier,
                    "next_reset": next_reset.isoformat()
                },
                status="success"
            )

        # Send monthly reset notification (don't fail transaction if email fails)
        try:
            await email_service.send_monthly_reset_notification(user_id, new_credits_remaining)
            logger.info(f"Monthly reset notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send monthly reset notification to user {user_id}: {e}")

        return await self.get_balance(user_id)

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get credit transaction history for a user.

        Args:
            user_id: Keycloak user ID
            limit: Maximum number of transactions to return
            offset: Pagination offset
            transaction_type: Filter by transaction type (optional)

        Returns:
            List of transaction records
        """
        if not self.db_pool:
            await self.initialize()

        if transaction_type:
            query = """
                SELECT id, user_id, amount, balance_after, transaction_type,
                       provider as service, model, cost as cost_breakdown, metadata, created_at
                FROM credit_transactions
                WHERE user_id = $1 AND transaction_type = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
            """
            params = [user_id, transaction_type, limit, offset]
        else:
            query = """
                SELECT id, user_id, amount, balance_after, transaction_type,
                       provider as service, model, cost as cost_breakdown, metadata, created_at
                FROM credit_transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            params = [user_id, limit, offset]

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            import json

            return [
                {
                    "id": str(row["id"]),  # Convert UUID to string
                    "user_id": row["user_id"],
                    "amount": row["amount"],
                    "balance_after": row["balance_after"],
                    "transaction_type": row["transaction_type"],
                    "service": row["service"],
                    "model": row["model"],
                    "cost_breakdown": row["cost_breakdown"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] and isinstance(row["metadata"], str) else row["metadata"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

    async def check_sufficient_balance(
        self,
        user_id: str,
        amount: Decimal
    ) -> Tuple[bool, Decimal]:
        """
        Check if user has sufficient credits.

        Args:
            user_id: Keycloak user ID
            amount: Required credit amount

        Returns:
            (has_sufficient, current_balance)
        """
        balance_info = await self.get_balance(user_id)
        current_balance = balance_info["balance"]  # Use the mapped field name
        return (current_balance >= amount, current_balance)

    async def _log_transaction(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        amount: Decimal,
        balance_after: Decimal,
        transaction_type: str,
        service: Optional[str] = None,
        model: Optional[str] = None,
        cost_breakdown: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Internal method to log a credit transaction"""
        import json

        await conn.execute(
            """
            INSERT INTO credit_transactions (
                user_id, amount, balance_after, transaction_type,
                provider, model, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_id, amount, balance_after, transaction_type,
            service,  # Maps to 'provider' column
            model,
            json.dumps(metadata) if metadata else None
        )


# Global instance
credit_manager = CreditManager()
