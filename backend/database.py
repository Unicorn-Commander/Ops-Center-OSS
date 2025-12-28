"""
Database Connection Helper

Provides async PostgreSQL connection management for Ops-Center backend.

Author: Backend API Developer Agent
Created: 2025-11-26
"""

import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "unicorn")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
DB_NAME = os.getenv("POSTGRES_DB", "unicorn_db")


async def get_db_connection() -> asyncpg.Connection:
    """
    Get an async PostgreSQL database connection.

    Returns:
        asyncpg.Connection: Database connection

    Raises:
        Exception: If connection fails

    Usage:
        conn = await get_db_connection()
        try:
            result = await conn.fetch("SELECT * FROM users")
            # ... process result
        finally:
            await conn.close()
    """
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def execute_query(query: str, *args):
    """
    Execute a query and return results.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        List of records

    Usage:
        results = await execute_query("SELECT * FROM users WHERE id = $1", user_id)
    """
    conn = await get_db_connection()
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()


async def execute_one(query: str, *args):
    """
    Execute a query and return a single record.

    Args:
        query: SQL query string
        *args: Query parameters

    Returns:
        Single record or None

    Usage:
        user = await execute_one("SELECT * FROM users WHERE id = $1", user_id)
    """
    conn = await get_db_connection()
    try:
        return await conn.fetchrow(query, *args)
    finally:
        await conn.close()
