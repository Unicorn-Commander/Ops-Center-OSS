"""
Epic 1.8: Credit & Usage Metering System
Module: coupon_system.py

Purpose: Promotional coupon code management with validation,
         redemption tracking, and automatic credit allocation.

Author: Backend Team Lead
Date: October 23, 2025
"""

import asyncpg
import secrets
import string
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os
from audit_logger import audit_logger
from credit_system import credit_manager

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CouponError(Exception):
    """Base exception for coupon system errors"""
    pass


class CouponExpiredError(CouponError):
    """Raised when coupon has expired"""
    pass


class CouponLimitReachedError(CouponError):
    """Raised when coupon redemption limit is reached"""
    pass


class CouponAlreadyRedeemedError(CouponError):
    """Raised when user already redeemed this coupon"""
    pass


class CouponManager:
    """
    Manages promotional coupon codes with validation and redemption tracking.

    Coupon Types:
    - free_month: Waive subscription fee for 30 days
    - credit_bonus: Add bonus credits to user account
    - percentage_discount: Percentage off subscription (e.g., 20% off)
    - fixed_discount: Fixed dollar amount off subscription

    Features:
    - Automatic code generation
    - Expiration date validation
    - Max redemption limits
    - Per-user redemption tracking
    - Automatic credit allocation on redemption
    """

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
            logger.info("CouponManager database pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
            logger.info("CouponManager database pool closed")

    def generate_code(self, prefix: str = "UC", length: int = 8) -> str:
        """
        Generate a random coupon code.

        Args:
            prefix: Code prefix (default: UC)
            length: Length of random part (default: 8)

        Returns:
            Generated code (e.g., UC-ABCD1234)
        """
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(length))
        return f"{prefix}-{random_part}"

    async def create_coupon(
        self,
        coupon_type: str,
        value: Decimal,
        code: Optional[str] = None,
        description: Optional[str] = None,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new coupon code.

        Args:
            coupon_type: Type (free_month, credit_bonus, percentage_discount, fixed_discount)
            value: Coupon value (credits, percentage, or dollar amount)
            code: Custom code (optional, will be generated if not provided)
            description: Human-readable description
            max_uses: Maximum redemptions allowed (None = unlimited)
            expires_at: Expiration date (None = never expires)
            created_by: User ID of creator (admin)

        Returns:
            Created coupon information
        """
        if not self.db_pool:
            await self.initialize()

        # Validate coupon type
        valid_types = ["free_month", "credit_bonus", "percentage_discount", "fixed_discount"]
        if coupon_type not in valid_types:
            raise ValueError(f"Invalid coupon type. Must be one of: {valid_types}")

        # Generate code if not provided
        if not code:
            code = self.generate_code()

        # Ensure code is uppercase
        code = code.upper()

        async with self.db_pool.acquire() as conn:
            # Check if code already exists
            existing = await conn.fetchval(
                "SELECT COUNT(*) FROM coupon_codes WHERE code = $1",
                code
            )

            if existing > 0:
                raise CouponError(f"Coupon code '{code}' already exists")

            # Create coupon
            await conn.execute(
                """
                INSERT INTO coupon_codes (
                    code, coupon_type, value, description,
                    max_uses, expires_at, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                code, coupon_type, value, description,
                max_uses, expires_at, created_by
            )

            # Audit log
            await audit_logger.log(
                action="coupon.create",
                user_id=created_by,
                resource_type="coupon_code",
                resource_id=code,
                details={
                    "coupon_type": coupon_type,
                    "value": float(value),
                    "max_uses": max_uses,
                    "expires_at": expires_at.isoformat() if expires_at else None
                },
                status="success"
            )

        logger.info(f"Created coupon code: {code} ({coupon_type}, value: {value})")

        return await self.get_coupon(code)

    async def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get coupon information.

        Args:
            code: Coupon code

        Returns:
            Coupon information or None if not found
        """
        if not self.db_pool:
            await self.initialize()

        code = code.upper()

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT code, coupon_type, value, description,
                       max_uses, used_count, expires_at, is_active,
                       created_by, created_at, updated_at
                FROM coupon_codes
                WHERE code = $1
                """,
                code
            )

            if not row:
                return None

            return {
                "code": row["code"],
                "coupon_type": row["coupon_type"],
                "value": row["value"],
                "description": row["description"],
                "max_uses": row["max_uses"],
                "used_count": row["used_count"],
                "remaining_uses": row["max_uses"] - row["used_count"] if row["max_uses"] else None,
                "expires_at": row["expires_at"],
                "is_active": row["is_active"],
                "is_expired": row["expires_at"] and row["expires_at"] < datetime.utcnow(),
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    async def validate_coupon(self, code: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a coupon code.

        Args:
            code: Coupon code
            user_id: User ID (to check if already redeemed)

        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "coupon": dict (if valid)
            }
        """
        if not self.db_pool:
            await self.initialize()

        code = code.upper()

        # Get coupon
        coupon = await self.get_coupon(code)

        if not coupon:
            return {
                "valid": False,
                "reason": "Coupon code not found"
            }

        # Check if active
        if not coupon["is_active"]:
            return {
                "valid": False,
                "reason": "Coupon code is inactive"
            }

        # Check if expired
        if coupon["is_expired"]:
            return {
                "valid": False,
                "reason": "Coupon code has expired"
            }

        # Check if max uses reached
        if coupon["max_uses"] and coupon["used_count"] >= coupon["max_uses"]:
            return {
                "valid": False,
                "reason": "Coupon redemption limit reached"
            }

        # Check if user already redeemed
        if user_id:
            async with self.db_pool.acquire() as conn:
                already_redeemed = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM coupon_redemptions
                    WHERE coupon_code = $1 AND user_id = $2
                    """,
                    code, user_id
                )

                if already_redeemed > 0:
                    return {
                        "valid": False,
                        "reason": "You have already redeemed this coupon"
                    }

        return {
            "valid": True,
            "coupon": coupon
        }

    async def redeem_coupon(
        self,
        code: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Redeem a coupon code.

        Args:
            code: Coupon code
            user_id: Keycloak user ID
            metadata: Additional metadata

        Returns:
            Redemption information with credits awarded

        Raises:
            CouponError: If coupon is invalid or already redeemed
        """
        if not self.db_pool:
            await self.initialize()

        code = code.upper()

        # Validate coupon
        validation = await self.validate_coupon(code, user_id)

        if not validation["valid"]:
            raise CouponError(validation["reason"])

        coupon = validation["coupon"]

        # Calculate credits to award
        if coupon["coupon_type"] == "credit_bonus":
            credits_awarded = coupon["value"]
        elif coupon["coupon_type"] == "free_month":
            # Approximate credit value of a month's subscription
            credits_awarded = Decimal("50.00")  # Average tier value
        else:
            # Percentage or fixed discount - doesn't grant credits directly
            credits_awarded = Decimal("0.00")

        import json

        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Record redemption
                await conn.execute(
                    """
                    INSERT INTO coupon_redemptions (
                        coupon_code, user_id, credits_awarded, metadata
                    )
                    VALUES ($1, $2, $3, $4)
                    """,
                    code, user_id, credits_awarded,
                    json.dumps(metadata) if metadata else None
                )

                # Update used_count (handled by trigger, but we'll update updated_at)
                await conn.execute(
                    """
                    UPDATE coupon_codes
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE code = $1
                    """,
                    code
                )

        # Award credits if applicable
        if credits_awarded > 0:
            await credit_manager.add_bonus_credits(
                user_id=user_id,
                amount=credits_awarded,
                reason=f"coupon_redemption:{code}",
                metadata={
                    "coupon_code": code,
                    "coupon_type": coupon["coupon_type"]
                }
            )

        # Audit log
        await audit_logger.log(
            action="coupon.redeem",
            user_id=user_id,
            resource_type="coupon_code",
            resource_id=code,
            details={
                "coupon_type": coupon["coupon_type"],
                "value": float(coupon["value"]),
                "credits_awarded": float(credits_awarded)
            },
            status="success"
        )

        logger.info(f"User {user_id} redeemed coupon {code} - awarded {credits_awarded} credits")

        return {
            "code": code,
            "coupon_type": coupon["coupon_type"],
            "value": coupon["value"],
            "credits_awarded": credits_awarded,
            "redeemed_at": datetime.utcnow()
        }

    async def list_coupons(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all coupon codes.

        Args:
            active_only: Only return active, non-expired coupons
            limit: Maximum number of coupons to return
            offset: Pagination offset

        Returns:
            List of coupon information
        """
        if not self.db_pool:
            await self.initialize()

        if active_only:
            query = """
                SELECT code, coupon_type, value, description,
                       max_uses, used_count, expires_at, is_active,
                       created_by, created_at, updated_at
                FROM coupon_codes
                WHERE is_active = true
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                  AND (max_uses IS NULL OR used_count < max_uses)
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            params = [limit, offset]
        else:
            query = """
                SELECT code, coupon_type, value, description,
                       max_uses, used_count, expires_at, is_active,
                       created_by, created_at, updated_at
                FROM coupon_codes
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            params = [limit, offset]

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            return [
                {
                    "code": row["code"],
                    "coupon_type": row["coupon_type"],
                    "value": row["value"],
                    "description": row["description"],
                    "max_uses": row["max_uses"],
                    "used_count": row["used_count"],
                    "remaining_uses": row["max_uses"] - row["used_count"] if row["max_uses"] else None,
                    "expires_at": row["expires_at"],
                    "is_active": row["is_active"],
                    "is_expired": row["expires_at"] and row["expires_at"] < datetime.utcnow(),
                    "created_by": row["created_by"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in rows
            ]

    async def deactivate_coupon(
        self,
        code: str,
        deactivated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate a coupon code.

        Args:
            code: Coupon code
            deactivated_by: User ID of admin deactivating

        Returns:
            Updated coupon information
        """
        if not self.db_pool:
            await self.initialize()

        code = code.upper()

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE coupon_codes
                SET is_active = false,
                    updated_at = CURRENT_TIMESTAMP
                WHERE code = $1
                """,
                code
            )

            if result == "UPDATE 0":
                raise CouponError(f"Coupon code '{code}' not found")

        # Audit log
        await audit_logger.log(
            action="coupon.deactivate",
            user_id=deactivated_by,
            resource_type="coupon_code",
            resource_id=code,
            status="success"
        )

        logger.info(f"Deactivated coupon code: {code}")

        return await self.get_coupon(code)

    async def get_usage_stats(self, code: str) -> Dict[str, Any]:
        """
        Get usage statistics for a coupon.

        Args:
            code: Coupon code

        Returns:
            Usage statistics
        """
        if not self.db_pool:
            await self.initialize()

        code = code.upper()

        async with self.db_pool.acquire() as conn:
            # Overall stats
            coupon = await self.get_coupon(code)

            if not coupon:
                raise CouponError(f"Coupon code '{code}' not found")

            # Redemption stats
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_redemptions,
                    SUM(credits_awarded) as total_credits_awarded,
                    MIN(redeemed_at) as first_redemption,
                    MAX(redeemed_at) as last_redemption
                FROM coupon_redemptions
                WHERE coupon_code = $1
                """,
                code
            )

            # Recent redemptions
            recent = await conn.fetch(
                """
                SELECT user_id, credits_awarded, redeemed_at
                FROM coupon_redemptions
                WHERE coupon_code = $1
                ORDER BY redeemed_at DESC
                LIMIT 10
                """,
                code
            )

        return {
            "code": code,
            "coupon_type": coupon["coupon_type"],
            "value": coupon["value"],
            "max_uses": coupon["max_uses"],
            "used_count": coupon["used_count"],
            "remaining_uses": coupon["remaining_uses"],
            "total_redemptions": stats["total_redemptions"],
            "total_credits_awarded": stats["total_credits_awarded"],
            "first_redemption": stats["first_redemption"],
            "last_redemption": stats["last_redemption"],
            "recent_redemptions": [
                {
                    "user_id": row["user_id"],
                    "credits_awarded": row["credits_awarded"],
                    "redeemed_at": row["redeemed_at"]
                }
                for row in recent
            ]
        }


# Global instance
coupon_manager = CouponManager()
