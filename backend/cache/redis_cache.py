"""
Redis Caching Layer for High-Performance Billing System
=======================================================

Intelligent caching with:
- TTL-based invalidation
- Cache warming
- Hit rate metrics
- Automatic fallback
- Cache-aside pattern

Author: Performance Excellence Team
Created: 2025-11-12
"""

import redis.asyncio as aioredis
import json
import logging
import hashlib
from typing import Any, Optional, Dict, List, Callable
from datetime import timedelta
from functools import wraps
import asyncio
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 2),
            "total_requests": self.hits + self.misses,
        }


class RedisCache:
    """High-performance Redis caching layer"""

    def __init__(self, redis_url: str = "redis://unicorn-redis:6379/1"):
        """Initialize Redis connection"""
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.stats = CacheStats()

        # Default TTLs for different data types
        self.default_ttls = {
            "credit_balance": 60,  # 1 minute
            "subscription": 300,  # 5 minutes
            "pricing_rules": 1800,  # 30 minutes
            "user_tier": 300,  # 5 minutes
            "org_data": 600,  # 10 minutes
            "analytics": 120,  # 2 minutes
        }

    async def connect(self):
        """Establish Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=100,  # Connection pooling
            )
            logger.info(f"✓ Redis cache connected: {self.redis_url}")
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            self.redis = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis cache disconnected")

    def _make_key(self, namespace: str, identifier: str) -> str:
        """Generate cache key with namespace"""
        # Hash long identifiers to keep keys short
        if len(identifier) > 50:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"ops_center:{namespace}:{identifier}"

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage"""
        # Handle Decimal types
        if isinstance(value, Decimal):
            return json.dumps({"__decimal__": str(value)})
        elif isinstance(value, dict):
            # Convert Decimals in dict
            return json.dumps(value, default=str)
        return json.dumps(value)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage"""
        try:
            data = json.loads(value)
            if isinstance(data, dict) and "__decimal__" in data:
                return Decimal(data["__decimal__"])
            return data
        except json.JSONDecodeError:
            return value

    async def get(self, namespace: str, identifier: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None

        key = self._make_key(namespace, identifier)

        try:
            value = await self.redis.get(key)
            if value:
                self.stats.hits += 1
                logger.debug(f"✓ Cache HIT: {key}")
                return self._deserialize(value)
            else:
                self.stats.misses += 1
                logger.debug(f"✗ Cache MISS: {key}")
                return None
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self,
        namespace: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis:
            return False

        key = self._make_key(namespace, identifier)

        # Use default TTL if not specified
        if ttl is None:
            ttl = self.default_ttls.get(namespace, 300)

        try:
            serialized = self._serialize(value)
            await self.redis.setex(key, ttl, serialized)
            self.stats.sets += 1
            logger.debug(f"✓ Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, namespace: str, identifier: str) -> bool:
        """Delete value from cache"""
        if not self.redis:
            return False

        key = self._make_key(namespace, identifier)

        try:
            await self.redis.delete(key)
            self.stats.deletes += 1
            logger.debug(f"✓ Cache DELETE: {key}")
            return True
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis:
            return 0

        full_pattern = f"ops_center:{pattern}"

        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=full_pattern, count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break

            logger.info(f"✓ Deleted {deleted} keys matching {full_pattern}")
            return deleted
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
            return 0

    async def get_or_set(
        self,
        namespace: str,
        identifier: str,
        fetch_func: Callable,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get value from cache or fetch and store if missing.

        Cache-aside pattern implementation.
        """
        # Try cache first
        cached = await self.get(namespace, identifier)
        if cached is not None:
            return cached

        # Cache miss - fetch from source
        try:
            value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()

            if value is not None:
                await self.set(namespace, identifier, value, ttl)

            return value
        except Exception as e:
            logger.error(f"Fetch function error: {e}")
            return None

    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        patterns = [
            f"credit_balance:{user_id}*",
            f"subscription:{user_id}*",
            f"user_tier:{user_id}*",
        ]

        for pattern in patterns:
            await self.delete_pattern(pattern)

        logger.info(f"Invalidated cache for user {user_id}")

    async def invalidate_org_cache(self, org_id: str):
        """Invalidate all cache entries for an organization"""
        patterns = [
            f"org_data:{org_id}*",
            f"credit_pool:{org_id}*",
            f"org_subscription:{org_id}*",
        ]

        for pattern in patterns:
            await self.delete_pattern(pattern)

        logger.info(f"Invalidated cache for org {org_id}")

    async def warm_cache(self, namespace: str, items: List[Dict]):
        """Pre-warm cache with frequently accessed data"""
        logger.info(f"Warming cache for {namespace} with {len(items)} items")

        tasks = []
        for item in items:
            identifier = item.get("id") or item.get("user_id") or item.get("org_id")
            if identifier:
                task = self.set(namespace, identifier, item)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)

        logger.info(f"✓ Cache warmed: {success_count}/{len(items)} items")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return self.stats.to_dict()

    async def health_check(self) -> Dict:
        """Check Redis health"""
        if not self.redis:
            return {"status": "disconnected", "healthy": False}

        try:
            await self.redis.ping()
            info = await self.redis.info("stats")

            return {
                "status": "connected",
                "healthy": True,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients", 0),
                "stats": self.get_stats(),
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }


# Global cache instance
cache = RedisCache()


# Decorator for automatic caching
def cached(namespace: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator to automatically cache function results.

    Usage:
        @cached("credit_balance", ttl=60)
        async def get_user_balance(user_id: str):
            # Expensive database query
            return balance

    Args:
        namespace: Cache namespace
        ttl: Time-to-live in seconds
        key_func: Function to generate cache key from args
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                # Use first argument as identifier (common pattern)
                identifier = str(args[0]) if args else str(kwargs.get('id', 'default'))

            # Get or set cache
            return await cache.get_or_set(
                namespace,
                identifier,
                lambda: func(*args, **kwargs),
                ttl
            )
        return wrapper
    return decorator
