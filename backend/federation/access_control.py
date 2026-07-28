"""
Federation Access Control

Controls which users and tiers can access which services via the federation.
This is checked by the inference router BEFORE routing a request.

Configuration stored in database (federation_service_acl table) and cached in Redis.
Falls back to default "allow all" if no ACL is configured.

Examples:
- music_gen: only managed/professional tiers and above
- llm: all tiers except trial
- embeddings: all tiers (utility service)
- image_gen: only managed tier and above
"""

import os
import json
import logging
from typing import Optional, Dict, List, Set

logger = logging.getLogger("federation.access_control")

# Default ACL — which tiers can access which service types
# If a service type is not listed, it's open to all tiers
DEFAULT_SERVICE_ACL = {
    "llm": {
        "allowed_tiers": ["vip_founder", "founder_friend", "byok", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "tts": {
        "allowed_tiers": ["vip_founder", "founder_friend", "byok", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "stt": {
        "allowed_tiers": ["vip_founder", "founder_friend", "byok", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "embeddings": {
        "allowed_tiers": None,  # None = all tiers allowed
        "blocked_tiers": [],
        "require_credits": False,  # utility service, usually free
        "free_tiers": None,  # None = free for everyone
    },
    "reranker": {
        "allowed_tiers": None,
        "blocked_tiers": [],
        "require_credits": False,
        "free_tiers": None,
    },
    "image_gen": {
        "allowed_tiers": ["vip_founder", "founder_friend", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial", "byok"],  # BYOK doesn't cover image gen
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "music_gen": {
        "allowed_tiers": ["vip_founder", "founder_friend", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial", "byok"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "search": {
        "allowed_tiers": ["vip_founder", "founder_friend", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
    "extraction": {
        "allowed_tiers": ["vip_founder", "founder_friend", "byok", "managed", "professional", "enterprise"],
        "blocked_tiers": ["trial"],
        "require_credits": True,
        "free_tiers": ["vip_founder", "founder_friend", "admin", "internal"],
    },
}


class ServiceAccessControl:
    """Checks if a user/tier can access a specific service type."""

    def __init__(self, redis_client=None, db_pool=None):
        self.redis = redis_client
        self.db_pool = db_pool
        self._acl_cache: Optional[Dict] = None
        self._cache_ttl = 300  # 5 minutes
        self._cache_time = 0

    async def check_access(
        self,
        service_type: str,
        user_tier: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """Check if a user can access a service type.

        Returns: {
            "allowed": bool,
            "reason": str,
            "requires_credits": bool,
            "is_free": bool,
        }
        """
        acl = await self._get_acl()
        service_acl = acl.get(service_type, {})

        # No ACL configured = allow all
        if not service_acl:
            return {"allowed": True, "reason": "no_acl_configured", "requires_credits": False, "is_free": True}

        # No tier info = allow (unauthenticated federation requests)
        if user_tier is None:
            return {"allowed": True, "reason": "no_tier_info", "requires_credits": False, "is_free": True}

        # Check blocked tiers first
        blocked = service_acl.get("blocked_tiers", [])
        if blocked and user_tier in blocked:
            return {
                "allowed": False,
                "reason": f"tier '{user_tier}' is blocked from {service_type}",
                "requires_credits": False,
                "is_free": False,
            }

        # Check allowed tiers
        allowed = service_acl.get("allowed_tiers")
        if allowed is not None and user_tier not in allowed:
            return {
                "allowed": False,
                "reason": f"tier '{user_tier}' not in allowed list for {service_type}",
                "requires_credits": False,
                "is_free": False,
            }

        # Check if free for this tier
        free_tiers = service_acl.get("free_tiers")
        is_free = free_tiers is None or (free_tiers and user_tier in free_tiers)

        return {
            "allowed": True,
            "reason": "acl_passed",
            "requires_credits": service_acl.get("require_credits", False) and not is_free,
            "is_free": is_free,
        }

    async def _get_acl(self) -> Dict:
        """Get ACL config — from cache, Redis, DB, or defaults."""
        import time
        now = time.time()

        if self._acl_cache and now - self._cache_time < self._cache_ttl:
            return self._acl_cache

        # Try Redis cache
        if self.redis:
            try:
                cached = await self.redis.get("federation:service_acl")
                if cached:
                    self._acl_cache = json.loads(cached)
                    self._cache_time = now
                    return self._acl_cache
            except Exception:
                pass

        # Try database
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT advertised_services FROM federation_config LIMIT 1"
                    )
                    if row and row["advertised_services"]:
                        acl_data = row["advertised_services"]
                        if isinstance(acl_data, str):
                            acl_data = json.loads(acl_data)
                        if "acl" in acl_data:
                            self._acl_cache = acl_data["acl"]
                            self._cache_time = now
                            # Cache in Redis
                            if self.redis:
                                await self.redis.set(
                                    "federation:service_acl",
                                    json.dumps(self._acl_cache),
                                    ex=self._cache_ttl
                                )
                            return self._acl_cache
            except Exception:
                pass

        # Fall back to defaults
        self._acl_cache = DEFAULT_SERVICE_ACL
        self._cache_time = now
        return self._acl_cache

    def get_default_acl(self) -> Dict:
        """Return the default ACL for reference/editing."""
        return DEFAULT_SERVICE_ACL.copy()


# Module singleton
_access_control: Optional[ServiceAccessControl] = None

def get_service_access_control(redis_client=None, db_pool=None) -> ServiceAccessControl:
    global _access_control
    if _access_control is None:
        _access_control = ServiceAccessControl(redis_client, db_pool)
    return _access_control
