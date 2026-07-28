"""
Organization Credit Integration for LLM API

This module provides integration between the LLM API and organizational billing system.
It allows LLM credit charges to be deducted from organization credit pools instead of
individual user balances.

Author: Integration Team
Date: November 12, 2025
"""

import logging
from typing import Optional, Dict, Tuple
import asyncpg
import os

logger = logging.getLogger(__name__)


class OrgCreditIntegration:
    """
    Integrates LLM API with organizational billing system
    """

    def __init__(self, db_pool: asyncpg.Pool = None):
        """
        Initialize integration

        Args:
            db_pool: PostgreSQL connection pool (optional, will create if not provided)
        """
        self.db_pool = db_pool

    async def _get_db_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        if self.db_pool:
            return await self.db_pool.acquire()

        # Create one-off connection if no pool provided
        return await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )

    async def get_user_org_id(self, user_id: str, request_state: Optional[Dict] = None) -> Optional[str]:
        """
        Get user's active organization ID

        Strategy:
        1. Check request state for active_org_id (user-selected org)
        2. Check for default organization
        3. Get first organization user belongs to

        Args:
            user_id: User's ID (from Keycloak sub)
            request_state: Optional request state dict with active_org_id

        Returns:
            Organization ID or None if user doesn't belong to any org
        """
        try:
            # Option 1: From request state (user explicitly selected)
            if request_state and hasattr(request_state, 'active_org_id'):
                org_id = request_state.active_org_id
                if org_id:
                    logger.info(f"Using active org from request state: {org_id}")
                    return org_id

            # Option 2: From database (default org or first org)
            conn = await self._get_db_connection()
            try:
                # Check for default organization first
                org_id = await conn.fetchval(
                    """
                    SELECT org_id FROM organization_members
                    WHERE user_id = $1 AND is_default = true
                    LIMIT 1
                    """,
                    user_id
                )

                if org_id:
                    logger.info(f"Using default org for user {user_id}: {org_id}")
                    return org_id

                # Get first organization user belongs to
                org_id = await conn.fetchval(
                    """
                    SELECT org_id FROM organization_members
                    WHERE user_id = $1
                    ORDER BY joined_at DESC
                    LIMIT 1
                    """,
                    user_id
                )

                if org_id:
                    logger.info(f"Using first org for user {user_id}: {org_id}")
                    return org_id

                logger.warning(f"User {user_id} does not belong to any organization")
                return None

            finally:
                if not self.db_pool:
                    await conn.close()

        except Exception as e:
            logger.error(f"Error getting user org ID: {e}", exc_info=True)
            return None

    async def has_sufficient_org_credits(
        self,
        user_id: str,
        credits_needed: float,
        request_state: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if user has sufficient organizational credits

        Args:
            user_id: User's ID
            credits_needed: Number of credits needed
            request_state: Optional request state with active_org_id

        Returns:
            Tuple of (has_credits: bool, org_id: str, message: str)
        """
        try:
            # Get user's organization
            org_id = await self.get_user_org_id(user_id, request_state)

            if not org_id:
                return False, None, "User does not belong to any organization"

            # Check if org has sufficient credits
            conn = await self._get_db_connection()
            try:
                # Convert float credits to integer (credits are stored as bigint)
                credits_needed_int = int(credits_needed * 1000)  # Convert to milicredits

                has_credits = await conn.fetchval(
                    "SELECT has_sufficient_credits($1, $2, $3)",
                    org_id,
                    user_id,
                    credits_needed_int
                )

                if has_credits:
                    return True, org_id, "Sufficient credits available"
                else:
                    # Get current allocation for better error message
                    allocation = await conn.fetchrow(
                        """
                        SELECT allocated_credits, used_credits,
                               (allocated_credits - used_credits) as remaining
                        FROM user_credit_allocations
                        WHERE org_id = $1 AND user_id = $2
                        """,
                        org_id,
                        user_id
                    )

                    if allocation:
                        remaining = allocation['remaining']
                        return False, org_id, f"Insufficient credits. Available: {remaining/1000:.3f}, needed: {credits_needed:.3f}"
                    else:
                        return False, org_id, "No credit allocation found for user in organization"

            finally:
                if not self.db_pool:
                    await conn.close()

        except Exception as e:
            logger.error(f"Error checking org credits: {e}", exc_info=True)
            return False, None, f"Error checking credits: {str(e)}"

    async def deduct_org_credits(
        self,
        user_id: str,
        credits_used: float,
        service_name: str,
        provider: str,
        model: str,
        tokens_used: int,
        power_level: str,
        task_type: Optional[str],
        request_id: Optional[str],
        org_id: Optional[str] = None,
        request_state: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Deduct credits from organization credit pool

        Args:
            user_id: User's ID
            credits_used: Number of credits to deduct
            service_name: Name of the service (model name)
            provider: Provider used (openai, anthropic, etc.)
            model: Model name
            tokens_used: Number of tokens used
            power_level: Power level (eco, balanced, precision)
            task_type: Type of task
            request_id: Request ID for tracking
            org_id: Optional organization ID (will be fetched if not provided)
            request_state: Optional request state

        Returns:
            Tuple of (success: bool, org_id: str, remaining_credits: int)
        """
        try:
            # Get organization ID if not provided
            if not org_id:
                org_id = await self.get_user_org_id(user_id, request_state)

            if not org_id:
                logger.error(f"Cannot deduct credits: user {user_id} has no organization")
                return False, None, None

            # Convert float credits to integer milicredits
            credits_used_int = int(credits_used * 1000)

            # Build metadata
            metadata = {
                'provider': provider,
                'model': model,
                'tokens_used': tokens_used,
                'power_level': power_level,
                'task_type': task_type,
                'cost': credits_used
            }

            # Deduct credits using stored function
            conn = await self._get_db_connection()
            try:
                success = await conn.fetchval(
                    "SELECT deduct_credits($1, $2, $3, $4, $5, $6, $7)",
                    org_id,
                    user_id,
                    credits_used_int,
                    "llm_inference",  # service_type
                    service_name,     # service_name (model)
                    request_id,
                    metadata
                )

                if success:
                    # Get remaining credits
                    remaining = await conn.fetchval(
                        """
                        SELECT (allocated_credits - used_credits) as remaining
                        FROM user_credit_allocations
                        WHERE org_id = $1 AND user_id = $2
                        """,
                        org_id,
                        user_id
                    )

                    logger.info(
                        f"Deducted {credits_used:.3f} credits from org {org_id} "
                        f"for user {user_id}. Remaining: {remaining/1000:.3f}"
                    )

                    return True, org_id, remaining
                else:
                    logger.error(f"Failed to deduct credits for user {user_id} in org {org_id}")
                    return False, org_id, None

            finally:
                if not self.db_pool:
                    await conn.close()

        except Exception as e:
            logger.error(f"Error deducting org credits: {e}", exc_info=True)
            return False, org_id, None

    async def get_user_org_credits(
        self,
        user_id: str,
        request_state: Optional[Dict] = None
    ) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Get user's organizational credit allocation

        Args:
            user_id: User's ID
            request_state: Optional request state

        Returns:
            Tuple of (org_id: str, allocated_credits: int, remaining_credits: int)
        """
        try:
            org_id = await self.get_user_org_id(user_id, request_state)

            if not org_id:
                return None, None, None

            conn = await self._get_db_connection()
            try:
                allocation = await conn.fetchrow(
                    """
                    SELECT allocated_credits, used_credits,
                           (allocated_credits - used_credits) as remaining
                    FROM user_credit_allocations
                    WHERE org_id = $1 AND user_id = $2
                    """,
                    org_id,
                    user_id
                )

                if allocation:
                    return (
                        org_id,
                        allocation['allocated_credits'],
                        allocation['remaining']
                    )
                else:
                    # User has no allocation yet
                    return org_id, 0, 0

            finally:
                if not self.db_pool:
                    await conn.close()

        except Exception as e:
            logger.error(f"Error getting user org credits: {e}", exc_info=True)
            return None, None, None


# Singleton instance
_org_credit_integration = None


def get_org_credit_integration() -> OrgCreditIntegration:
    """
    Get singleton instance of OrgCreditIntegration

    Returns:
        OrgCreditIntegration instance
    """
    global _org_credit_integration
    if _org_credit_integration is None:
        _org_credit_integration = OrgCreditIntegration()
    return _org_credit_integration
