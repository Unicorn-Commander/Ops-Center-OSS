"""
Database Connection Pool Management

Provides shared asyncpg connection pool for all API modules.
This module ensures efficient database connection reuse and proper resource management.

Author: Integration Testing & Deployment Lead
Date: October 23, 2025
"""

import os
import logging
import asyncpg
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton connection pool
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool.

    Returns a singleton connection pool that's shared across all API modules.
    The pool is created on first call and reused on subsequent calls.

    Returns:
        asyncpg.Pool: Database connection pool

    Raises:
        RuntimeError: If database connection fails

    Example:
        ```python
        # In your API endpoint
        from database.connection import get_db_pool

        async def my_endpoint():
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        ```
    """
    global _db_pool

    if _db_pool is None:
        # Get database connection from environment
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://ops_user:change-me@localhost:5432/ops_center_db"
        )

        try:
            logger.info("Creating database connection pool...")
            _db_pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
                timeout=10
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise RuntimeError(f"Database connection failed: {e}")

    return _db_pool


async def close_db_pool():
    """
    Close the database connection pool.

    Should be called during application shutdown to properly close all connections.

    Example:
        ```python
        # In server.py shutdown handler
        from database.connection import close_db_pool

        @app.on_event("shutdown")
        async def shutdown():
            await close_db_pool()
        ```
    """
    global _db_pool

    if _db_pool is not None:
        logger.info("Closing database connection pool...")
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed")


async def get_db_connection():
    """
    Convenience function to get a single database connection from the pool.

    Returns:
        asyncpg.Connection: Database connection (context manager)

    Example:
        ```python
        # Alternative usage pattern
        from database.connection import get_db_connection

        async def my_endpoint():
            async with await get_db_connection() as conn:
                result = await conn.fetchrow("SELECT * FROM users")
        ```
    """
    pool = await get_db_pool()
    return pool.acquire()
