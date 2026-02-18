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
                SELECT user_id, balance, tier, lifetime_credits, monthly_cap,
                        monthly_usage, monthly_reset_at, last_updated, created_at
                FROM user_credits
                WHERE user_id::text = $1
                """,
                user_id
            )

            if not row:
                # AUTO-PROVISION: User doesn't exist yet, create with default trial tier
                logger.info(f"Auto-provisioning credit account for new user: {user_id}")
                return await self.create_user_credits(user_id, tier="trial")

            # Map database columns to API response fields
            return {
                "user_id": str(row["user_id"]) if row["user_id"] else user_id,
                "balance": row["balance"] or Decimal("0.00"),  # DB column: balance
                "allocated_monthly": row["monthly_cap"] or Decimal("0.00"),  # DB column: monthly_cap
                "bonus_credits": Decimal("0.00"),  # Not stored in DB
                "free_tier_used": row["monthly_usage"] or Decimal("0.00"),  # DB column: monthly_usage
                "reset_date": row["monthly_reset_at"],  # DB column: monthly_reset_at
                "last_updated": row["last_updated"],  # DB column: last_updated
                "tier": row["tier"] or "free",
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
        next_reset = datetime.utcnow() + timedelta(days=30)

        # Check if user exists in users table first
        async with self.db_pool.acquire() as conn:
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1::uuid)",
                user_id
            )

        if not user_exists:
            # User not in users table (Keycloak user not synced yet)
            # Return a default balance object instead of trying to create a record
            logger.warning(f"User {user_id} not in users table, returning default trial balance")
            return {
                "user_id": user_id,
                "balance": Decimal("0.00"),
                "allocated_monthly": Decimal("0.00"),
                "bonus_credits": Decimal("0.00"),
                "free_tier_used": Decimal("0.00"),
                "reset_date": next_reset,
                "last_updated": datetime.utcnow(),
                "tier": "trial",
                "created_at": datetime.utcnow(),
                "note": "User not synced - contact support to activate credits"
            }

        async with self.transaction() as conn:
            # Create user credits record (uses actual DB column names)
            result = await conn.execute(
                """
                INSERT INTO user_credits (
                    user_id, balance, tier, monthly_cap, monthly_reset_at
                )
                VALUES ($1::uuid, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id, allocated, tier, allocated, next_reset
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
                    "next_reset": next_reset.isoformat()
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
            # Get current balance (uses actual DB column name: balance)
            current = await conn.fetchrow(
                "SELECT balance FROM user_credits WHERE user_id::text = $1",
                user_id
            )

            if not current:
                # Create user first
                await self.create_user_credits(user_id)
                current_balance = Decimal("0.00")
            else:
                current_balance = current["balance"] or Decimal("0.00")

            new_balance = current_balance + amount

            # Update balance (uses actual DB column names)
            await conn.execute(
                """
                UPDATE user_credits
                SET balance = $1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id::text = $2
                """,
                new_balance, user_id
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_balance,
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
                    "new_balance": float(new_balance),
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
            # Check current balance with row lock (uses actual DB column name: balance)
            current = await conn.fetchrow(
                """
                SELECT balance FROM user_credits
                WHERE user_id::text = $1
                FOR UPDATE
                """,
                user_id
            )

            if not current:
                raise CreditError(f"User {user_id} does not have a credit account")

            current_balance = current["balance"] or Decimal("0.00")

            # Check sufficient balance
            if current_balance < amount:
                await audit_logger.log(
                    action="credit.deduct_failed",
                    user_id=user_id,
                    resource_type="user_credits",
                    resource_id=user_id,
                    details={
                        "amount": float(amount),
                        "current_balance": float(current_balance),
                        "reason": "insufficient_credits"
                    },
                    status="failure"
                )
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: {amount}, Available: {current_balance}"
                )

            new_balance = current_balance - amount

            # Update balance (uses actual DB column names)
            await conn.execute(
                """
                UPDATE user_credits
                SET balance = $1,
                    monthly_usage = COALESCE(monthly_usage, 0) + $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id::text = $2
                """,
                new_balance, user_id, amount
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, -amount, new_balance,
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
                    "new_balance": float(new_balance),
                    "cost_breakdown": cost_breakdown
                },
                status="success"
            )

        # Send low balance alert if credits are running low (don't fail transaction if email fails)
        if new_balance < Decimal("100.00") and new_balance > Decimal("0.00"):
            try:
                await email_service.send_low_balance_alert(user_id, new_balance)
                logger.info(f"Low balance alert sent to user {user_id} (balance: {new_balance})")
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
            # Update balance (uses actual DB column name: balance)
            result = await conn.fetchrow(
                """
                UPDATE user_credits
                SET balance = COALESCE(balance, 0) + $1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id::text = $2
                RETURNING balance
                """,
                amount, user_id
            )

            if not result:
                raise CreditError(f"User {user_id} does not have a credit account")

            new_balance = result["balance"]

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_balance,
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
                    "new_balance": float(new_balance),
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
            # Update balance (uses actual DB column name: balance)
            result = await conn.fetchrow(
                """
                UPDATE user_credits
                SET balance = COALESCE(balance, 0) + $1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id::text = $2
                RETURNING balance
                """,
                amount, user_id
            )

            if not result:
                raise CreditError(f"User {user_id} does not have a credit account")

            new_balance = result["balance"]

            # Log transaction
            await self._log_transaction(
                conn, user_id, amount, new_balance,
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
                    "new_balance": float(new_balance),
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
            # Get current allocation (uses actual DB column names)
            current = await conn.fetchrow(
                """
                SELECT monthly_cap, balance
                FROM user_credits
                WHERE user_id::text = $1
                """,
                user_id
            )

            if not current:
                raise CreditError(f"User {user_id} does not have a credit account")

            # Determine new allocation
            if new_tier:
                new_allocation = self._tier_allocations.get(new_tier, Decimal("0.00"))
            else:
                new_allocation = current["monthly_cap"] or Decimal("0.00")

            # Calculate new balance (add new allocation)
            current_balance = current["balance"] or Decimal("0.00")
            new_balance = current_balance + new_allocation
            next_reset = datetime.utcnow() + timedelta(days=30)

            # Update credits (uses actual DB column names)
            await conn.execute(
                """
                UPDATE user_credits
                SET balance = $1,
                    monthly_cap = $2,
                    monthly_usage = 0,
                    monthly_reset_at = $3,
                    tier = COALESCE($5, tier),
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id::text = $4
                """,
                new_balance, new_allocation, next_reset, user_id, new_tier
            )

            # Log transaction
            await self._log_transaction(
                conn, user_id, new_allocation, new_balance,
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
                    "new_balance": float(new_balance),
                    "tier": new_tier,
                    "next_reset": next_reset.isoformat()
                },
                status="success"
            )

        # Send monthly reset notification (don't fail transaction if email fails)
        try:
            await email_service.send_monthly_reset_notification(user_id, new_balance)
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

        # Query the 'transactions' table with actual DB schema
        if transaction_type:
            query = """
                SELECT id, user_id, type, amount_cents, balance_after_cents,
                       description, metadata, created_at
                FROM transactions
                WHERE user_id::text = $1 AND type = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
            """
            params = [user_id, transaction_type, limit, offset]
        else:
            query = """
                SELECT id, user_id, type, amount_cents, balance_after_cents,
                       description, metadata, created_at
                FROM transactions
                WHERE user_id::text = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            params = [user_id, limit, offset]

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            return [
                {
                    "id": str(row["id"]),  # Convert UUID to string
                    "user_id": str(row["user_id"]) if row["user_id"] else user_id,
                    "amount": Decimal(row["amount_cents"]) / 100,  # Convert cents to decimal
                    "balance_after": Decimal(row["balance_after_cents"]) / 100,
                    "transaction_type": row["type"],
                    "service": row["metadata"].get("service") if row["metadata"] else None,
                    "model": row["metadata"].get("model") if row["metadata"] else None,
                    "cost_breakdown": row["metadata"].get("cost_breakdown") if row["metadata"] else None,
                    "metadata": row["metadata"],
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
        """Internal method to log a credit transaction using the 'transactions' table"""
        import json

        # Build description from service/model if provided
        description_parts = [transaction_type]
        if service:
            description_parts.append(f"service={service}")
        if model:
            description_parts.append(f"model={model}")
        description = " | ".join(description_parts)

        # Merge service/model/cost into metadata
        full_metadata = metadata or {}
        if service:
            full_metadata["service"] = service
        if model:
            full_metadata["model"] = model
        if cost_breakdown:
            full_metadata["cost_breakdown"] = cost_breakdown

        # Convert to cents for the transactions table (which stores cents as bigint)
        amount_cents = int(amount * 100)
        balance_after_cents = int(balance_after * 100)

        # Insert into transactions table (uses actual DB schema)
        await conn.execute(
            """
            INSERT INTO transactions (
                user_id, type, amount_cents, balance_after_cents,
                description, metadata
            )
            SELECT $1::uuid, $2, $3, $4, $5, $6::jsonb
            WHERE EXISTS (SELECT 1 FROM users WHERE id = $1::uuid)
            """,
            user_id, transaction_type, amount_cents, balance_after_cents,
            description, json.dumps(full_metadata) if full_metadata else '{}'
        )


# Global instance
credit_manager = CreditManager()
