"""
Enhanced Redis Cache Manager

Provides intelligent caching for API responses with:
- Automatic cache key generation
- TTL management
- Cache invalidation strategies
- Hit/miss metrics tracking
- Compression for large payloads
- Cache warming
"""

import redis
import json
import hashlib
import gzip
from typing import Optional, Any, Callable
from functools import wraps
import time
from datetime import datetime, timedelta


class RedisCacheManager:
    """
    Advanced Redis cache manager with intelligent caching strategies
    """

    def __init__(self, redis_url: str = "redis://unicorn-redis:6379/0"):
        """
        Initialize Redis cache manager

        Args:
            redis_url: Redis connection URL
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'compressions': 0
        }

        # Cache key prefixes
        self.KEY_PREFIX = "opscenter:"
        self.API_PREFIX = f"{self.KEY_PREFIX}api:"
        self.USER_PREFIX = f"{self.KEY_PREFIX}user:"
        self.ORG_PREFIX = f"{self.KEY_PREFIX}org:"
        self.METRICS_PREFIX = f"{self.KEY_PREFIX}metrics:"

        # Default TTLs (in seconds)
        self.DEFAULT_TTL = 60  # 1 minute
        self.SHORT_TTL = 30  # 30 seconds
        self.MEDIUM_TTL = 300  # 5 minutes
        self.LONG_TTL = 3600  # 1 hour
        self.VERY_LONG_TTL = 86400  # 24 hours

        # Compression threshold (bytes)
        self.COMPRESSION_THRESHOLD = 1024  # 1 KB

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic string from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_str = ":".join(key_parts)

        # Hash if too long
        if len(key_str) > 200:
            key_str = hashlib.md5(key_str.encode()).hexdigest()

        return f"{prefix}{key_str}"

    def _serialize(self, data: Any) -> bytes:
        """
        Serialize data to bytes with optional compression

        Args:
            data: Data to serialize

        Returns:
            Serialized bytes
        """
        # Serialize to JSON
        json_str = json.dumps(data, default=str)
        json_bytes = json_str.encode('utf-8')

        # Compress if large enough
        if len(json_bytes) > self.COMPRESSION_THRESHOLD:
            compressed = gzip.compress(json_bytes)
            self.metrics['compressions'] += 1
            # Prepend marker for compressed data
            return b'GZIP:' + compressed

        return json_bytes

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize bytes to Python object

        Args:
            data: Serialized bytes

        Returns:
            Deserialized object
        """
        # Check if compressed
        if data.startswith(b'GZIP:'):
            data = gzip.decompress(data[5:])

        # Deserialize from JSON
        return json.loads(data.decode('utf-8'))

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            data = self.redis_client.get(key)
            if data:
                self.metrics['hits'] += 1
                return self._deserialize(data)
            else:
                self.metrics['misses'] += 1
                return None
        except Exception as e:
            print(f"Redis get error: {e}")
            self.metrics['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: DEFAULT_TTL)

        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.DEFAULT_TTL
            data = self._serialize(value)
            self.redis_client.setex(key, ttl, data)
            self.metrics['sets'] += 1
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            self.redis_client.delete(key)
            self.metrics['invalidations'] += 1
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "opscenter:api:users:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                count = self.redis_client.delete(*keys)
                self.metrics['invalidations'] += count
                return count
            return 0
        except Exception as e:
            print(f"Redis invalidate pattern error: {e}")
            return 0

    def cache_api_response(self, endpoint: str, params: dict = None, ttl: int = None):
        """
        Decorator to cache API responses

        Args:
            endpoint: API endpoint name
            params: Additional parameters for cache key
            ttl: Time to live in seconds

        Usage:
            @cache.cache_api_response("users.list", ttl=300)
            async def get_users():
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_params = params or {}
                cache_params.update(kwargs)
                cache_key = self._generate_key(self.API_PREFIX + endpoint + ":", *args, **cache_params)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                self.set(cache_key, result, ttl)

                return result

            return wrapper
        return decorator

    def cache_user_data(self, user_id: str, data_type: str, ttl: int = None):
        """
        Decorator to cache user-specific data

        Args:
            user_id: User identifier
            data_type: Type of data (e.g., "profile", "settings")
            ttl: Time to live in seconds
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(self.USER_PREFIX, user_id, data_type)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                self.set(cache_key, result, ttl or self.SHORT_TTL)

                return result

            return wrapper
        return decorator

    def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all cached data for a user

        Args:
            user_id: User identifier

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.USER_PREFIX}{user_id}:*"
        return self.invalidate_pattern(pattern)

    def invalidate_org_cache(self, org_id: str) -> int:
        """
        Invalidate all cached data for an organization

        Args:
            org_id: Organization identifier

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.ORG_PREFIX}{org_id}:*"
        return self.invalidate_pattern(pattern)

    def warm_cache(self, warm_func: Callable, cache_key: str, ttl: int = None):
        """
        Warm cache by pre-loading data

        Args:
            warm_func: Function to execute to get data
            cache_key: Cache key to use
            ttl: Time to live in seconds
        """
        try:
            data = warm_func()
            self.set(cache_key, data, ttl)
            return True
        except Exception as e:
            print(f"Cache warming error: {e}")
            return False

    def get_metrics(self) -> dict:
        """
        Get cache performance metrics

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self.metrics['hits'] + self.metrics['misses']
        hit_rate = (self.metrics['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.metrics['hits'],
            'misses': self.metrics['misses'],
            'sets': self.metrics['sets'],
            'invalidations': self.metrics['invalidations'],
            'compressions': self.metrics['compressions'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'compression_savings_percent': round(
                (self.metrics['compressions'] / self.metrics['sets'] * 100) if self.metrics['sets'] > 0 else 0, 2
            )
        }

    def reset_metrics(self):
        """Reset cache metrics"""
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'compressions': 0
        }

    def get_cache_info(self) -> dict:
        """
        Get Redis cache information

        Returns:
            Dictionary with cache info
        """
        try:
            info = self.redis_client.info('memory')
            stats = self.redis_client.info('stats')

            return {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
                'connected_clients': stats.get('connected_clients', 0),
                'total_commands_processed': stats.get('total_commands_processed', 0),
                'keyspace_hits': stats.get('keyspace_hits', 0),
                'keyspace_misses': stats.get('keyspace_misses', 0),
                'evicted_keys': stats.get('evicted_keys', 0)
            }
        except Exception as e:
            print(f"Failed to get cache info: {e}")
            return {}


# Global cache instance
cache = RedisCacheManager()


# Convenience decorators
def cache_api(endpoint: str, ttl: int = 60):
    """
    Quick decorator for caching API responses

    Usage:
        @cache_api("users.list", ttl=300)
        async def get_users():
            ...
    """
    return cache.cache_api_response(endpoint, ttl=ttl)


def cache_user(user_id: str, data_type: str, ttl: int = 30):
    """
    Quick decorator for caching user data

    Usage:
        @cache_user(user_id, "profile", ttl=60)
        async def get_user_profile():
            ...
    """
    return cache.cache_user_data(user_id, data_type, ttl=ttl)
