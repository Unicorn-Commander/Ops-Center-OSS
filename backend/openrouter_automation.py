"""
Epic 1.8: Credit & Usage Metering System
Module: openrouter_automation.py

Purpose: OpenRouter BYOK (Bring Your Own Key) account management with
         automatic free model detection and platform markup calculation.

Author: Backend Team Lead
Date: October 23, 2025
"""

import asyncpg
import httpx
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from cryptography.fernet import Fernet
import base64
from audit_logger import audit_logger
from openrouter_client import OpenRouterClient, OpenRouterAPIError, OpenRouterAuthError

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenRouterError(Exception):
    """Base exception for OpenRouter operations"""
    pass


class OpenRouterManager:
    """
    Manages OpenRouter BYOK accounts with encrypted key storage,
    free model detection, and cost calculation with platform markup.

    Features:
    - Secure key encryption using Fernet
    - Automatic free model detection (40+ models with :free suffix)
    - Platform markup calculation (0% for free, 5-10% for paid)
    - Free credit sync from OpenRouter API
    - Request routing with cost tracking
    """

    # Free tier model patterns (OpenRouter models with :free suffix)
    FREE_MODEL_PATTERNS = [
        "free",  # Any model with :free suffix
        "llama",  # Many Llama models are free
        "mistral-7b",  # Mistral 7B variants
        "mythomax",
        "toppy",
        "cinematika"
    ]

    # Markup rates by model tier
    MARKUP_RATES = {
        "free": Decimal("0.00"),      # 0% markup on free models
        "budget": Decimal("0.05"),    # 5% markup on budget models
        "standard": Decimal("0.10"),  # 10% markup on standard models
        "premium": Decimal("0.15")    # 15% markup on premium models
    }

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.api_client: Optional[OpenRouterClient] = None
        self._encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self._encryption_key)
        self._models_cache: Optional[Dict[str, Any]] = None
        self._models_cache_time: Optional[datetime] = None
        self._models_cache_ttl = timedelta(hours=1)  # Cache models for 1 hour

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create Fernet encryption key"""
        key_path = "/app/data/openrouter_encryption.key"

        # Try to load existing key
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()

        # Generate new key
        key = Fernet.generate_key()

        # Save to file
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, "wb") as f:
            f.write(key)

        logger.info("Generated new OpenRouter encryption key")
        return key

    async def initialize(self):
        """Initialize database connection pool and OpenRouter API client"""
        if not self.db_pool:
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
                logger.info("OpenRouterManager database pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise

        if not self.api_client:
            self.api_client = OpenRouterClient()
            await self.api_client.initialize()
            logger.info("OpenRouter API client initialized")

    async def close(self):
        """Close database connection pool and API client"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None

        if self.api_client:
            await self.api_client.close()
            self.api_client = None

        logger.info("OpenRouterManager closed")

    def encrypt_key(self, api_key: str) -> str:
        """Encrypt OpenRouter API key"""
        return self.fernet.encrypt(api_key.encode()).decode()

    def decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt OpenRouter API key"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()

    async def create_account(
        self,
        user_id: str,
        api_key: str,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create OpenRouter BYOK account for user.

        Args:
            user_id: Keycloak user ID
            api_key: User's OpenRouter API key
            user_email: User's email (optional)

        Returns:
            Account information
        """
        if not self.db_pool:
            await self.initialize()

        # Encrypt API key
        encrypted_key = self.encrypt_key(api_key)

        # Verify API key is valid
        try:
            account_info = await self._verify_api_key(api_key)
        except Exception as e:
            raise OpenRouterError(f"Invalid OpenRouter API key: {e}")

        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Create or update account
                await conn.execute(
                    """
                    INSERT INTO openrouter_accounts (
                        user_id, openrouter_api_key_encrypted,
                        openrouter_account_id, free_credits
                    )
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE
                    SET openrouter_api_key_encrypted = EXCLUDED.openrouter_api_key_encrypted,
                        openrouter_account_id = EXCLUDED.openrouter_account_id,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id, encrypted_key,
                    account_info.get("label", user_email), Decimal("0.00")
                )

                # Audit log
                await audit_logger.log(
                    action="openrouter.account_create",
                    user_id=user_id,
                    resource_type="openrouter_account",
                    resource_id=user_id,
                    details={
                        "email": user_email or account_info.get("email"),
                        "account_id": account_info.get("id")
                    },
                    status="success"
                )

        # Sync free credits
        await self.sync_free_credits(user_id)

        return await self.get_account(user_id)

    async def get_account(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get OpenRouter account for user.

        Args:
            user_id: Keycloak user ID

        Returns:
            Account information (with key redacted) or None
        """
        if not self.db_pool:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, openrouter_account_id,
                       free_credits,
                       last_synced, created_at, updated_at
                FROM openrouter_accounts
                WHERE user_id = $1
                """,
                user_id
            )

            if not row:
                return None

            return {
                "user_id": row["user_id"],
                "account_id": row["openrouter_account_id"],
                "free_credits": float(row["free_credits"]) if row["free_credits"] else 0.0,
                "last_synced": row["last_synced"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    async def sync_free_credits(self, user_id: str) -> Decimal:
        """
        Sync free credits from OpenRouter API.

        Args:
            user_id: Keycloak user ID

        Returns:
            Updated free credits balance
        """
        if not self.db_pool:
            await self.initialize()

        # Get API key
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT openrouter_api_key_encrypted FROM openrouter_accounts WHERE user_id = $1",
                user_id
            )

        if not row:
            raise OpenRouterError(f"No OpenRouter account for user {user_id}")

        api_key = self.decrypt_key(row["openrouter_api_key_encrypted"])

        # Query OpenRouter API for credit balance
        try:
            if not self.api_client:
                await self.initialize()

            key_info = await self.api_client.get_key_info(api_key)

            # Extract credit information
            limit = key_info.get("limit")  # Can be null for unlimited
            limit_remaining = key_info.get("limit_remaining", 0)

            # Convert to Decimal
            free_credits = Decimal(str(limit_remaining)) if limit_remaining else Decimal("0.00")

            logger.info(f"OpenRouter key info for {user_id}: limit={limit}, remaining={limit_remaining}")

        except OpenRouterAuthError as e:
            logger.error(f"Authentication failed for {user_id}: {e}")
            raise OpenRouterError(f"Invalid OpenRouter API key: {e}")
        except Exception as e:
            logger.error(f"Failed to sync free credits for {user_id}: {e}")
            raise OpenRouterError(f"Failed to sync credits: {e}")

        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE openrouter_accounts
                SET free_credits = $1,
                    last_synced = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                free_credits, user_id
            )

        logger.info(f"Synced {free_credits} free credits for user {user_id}")
        return free_credits

    async def route_request(
        self,
        user_id: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route LLM request through OpenRouter with user's BYOK key.

        Args:
            user_id: Keycloak user ID
            model: Model name
            messages: Chat messages
            **kwargs: Additional OpenRouter parameters

        Returns:
            OpenRouter API response
        """
        if not self.db_pool:
            await self.initialize()

        # Get API key
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT openrouter_api_key_encrypted
                FROM openrouter_accounts
                WHERE user_id = $1
                """,
                user_id
            )

        if not row:
            raise OpenRouterError(f"No OpenRouter account for user {user_id}")

        api_key = self.decrypt_key(row["openrouter_api_key_encrypted"])

        # Make request using OpenRouter API client
        if not self.api_client:
            await self.initialize()

        try:
            return await self.api_client.chat_completion(
                model=model,
                messages=messages,
                api_key=api_key,
                **kwargs
            )
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            raise OpenRouterError(f"OpenRouter API error: {e}")

    async def detect_free_models(self) -> List[str]:
        """
        Get list of free models from OpenRouter API.

        Returns:
            List of free model IDs (with :free suffix)

        Note:
            Results are cached for 1 hour to reduce API calls
        """
        # Check cache
        if self._models_cache and self._models_cache_time:
            if datetime.now() - self._models_cache_time < self._models_cache_ttl:
                logger.debug("Returning cached free models")
                return self._models_cache.get("free_models", [])

        # Fetch fresh data from API
        if not self.api_client:
            await self.initialize()

        try:
            # Use a system API key if available, or skip auth check
            # (OpenRouter's /models endpoint may be public)
            system_key = os.getenv("OPENROUTER_SYSTEM_KEY")
            models = await self.api_client.get_models(api_key=system_key)

            # Filter for free models (pricing.prompt == "0")
            free_models = []
            for model in models:
                model_id = model.get("id", "")
                pricing = model.get("pricing", {})

                # Check if prompt and completion costs are both 0
                prompt_cost = float(pricing.get("prompt", 1))
                completion_cost = float(pricing.get("completion", 1))

                if prompt_cost == 0 and completion_cost == 0:
                    free_models.append(model_id)

            # Update cache
            self._models_cache = {
                "free_models": free_models,
                "all_models": models
            }
            self._models_cache_time = datetime.now()

            logger.info(f"Discovered {len(free_models)} free models from OpenRouter")
            return free_models

        except Exception as e:
            logger.error(f"Failed to fetch free models: {e}")
            # Return empty list on error (fail gracefully)
            return []

    def detect_free_model(self, model: str) -> bool:
        """
        Detect if a model is on the free tier (synchronous check).

        Args:
            model: Model name (e.g., "meta-llama/llama-3.1-8b-instruct:free")

        Returns:
            True if model is free tier

        Note:
            This is a pattern-based check. For authoritative results,
            use detect_free_models() which queries the API.
        """
        model_lower = model.lower()

        # Check for :free suffix (most reliable indicator)
        if ":free" in model_lower:
            return True

        # Check for known free model patterns
        for pattern in self.FREE_MODEL_PATTERNS:
            if pattern in model_lower:
                return True

        return False

    async def calculate_markup(
        self,
        user_id: str,
        model: str,
        provider_cost: Decimal
    ) -> Tuple[Decimal, Decimal, str]:
        """
        Calculate platform markup for a model based on user's subscription tier.

        Args:
            user_id: Keycloak user ID
            model: Model name
            provider_cost: Cost from OpenRouter provider

        Returns:
            (markup_amount, total_cost, markup_reason)

        Markup Strategy:
        - Free models: 0% markup (always)
        - Paid models:
          - Trial: 15% markup
          - Starter: 10% markup
          - Professional: 5% markup
          - Enterprise: 0% markup
        """
        # Free models have no markup
        if self.detect_free_model(model):
            return (Decimal("0.00"), Decimal("0.00"), "free_model")

        # Get user's subscription tier from Keycloak
        try:
            if not self.db_pool:
                await self.initialize()

            # Query Keycloak integration for user subscription
            # (This assumes keycloak_integration.py has get_user_attributes method)
            from keycloak_integration import keycloak_service

            user_attrs = await keycloak_service.get_user_attributes(user_id)
            subscription_tier = user_attrs.get("subscription_tier", "trial").lower()

        except Exception as e:
            logger.warning(f"Failed to get subscription tier for {user_id}: {e}. Using 'trial'")
            subscription_tier = "trial"

        # Determine markup rate by subscription tier
        tier_markup_rates = {
            "trial": Decimal("0.15"),         # 15% markup
            "starter": Decimal("0.10"),       # 10% markup
            "professional": Decimal("0.05"),  # 5% markup
            "enterprise": Decimal("0.00")     # 0% markup
        }

        markup_rate = tier_markup_rates.get(subscription_tier, Decimal("0.15"))
        markup_amount = provider_cost * markup_rate
        total_cost = provider_cost + markup_amount

        markup_reason = f"{subscription_tier}_tier_{int(markup_rate * 100)}pct"

        logger.debug(
            f"Markup calculation for {user_id}: "
            f"tier={subscription_tier}, model={model}, "
            f"provider_cost={provider_cost}, markup={markup_amount}, total={total_cost}"
        )

        return (markup_amount, total_cost, markup_reason)

    async def delete_account(self, user_id: str):
        """
        Delete OpenRouter account for user.

        Args:
            user_id: Keycloak user ID
        """
        if not self.db_pool:
            await self.initialize()

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM openrouter_accounts WHERE user_id = $1",
                user_id
            )

        await audit_logger.log(
            action="openrouter.account_delete",
            user_id=user_id,
            resource_type="openrouter_account",
            resource_id=user_id,
            status="success"
        )

        logger.info(f"Deleted OpenRouter account for user {user_id}")

    async def _verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify OpenRouter API key and get account info"""
        if not self.api_client:
            await self.initialize()

        try:
            key_info = await self.api_client.get_key_info(api_key)
            return key_info
        except OpenRouterAuthError as e:
            raise OpenRouterError(f"API key verification failed: {e}")


# Global instance
openrouter_manager = OpenRouterManager()
