"""
Cache Module
============

High-performance caching layer for Ops-Center billing system.
"""

from .redis_cache import cache, cached, RedisCache

__all__ = ["cache", "cached", "RedisCache"]
