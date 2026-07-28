"""
Colonel Configuration - Database-backed with environment defaults.
"""

import os
import json
import logging
from typing import Optional

import asyncpg

from colonel.models import ColonelConfig, ColonelPersonality

logger = logging.getLogger("colonel.config")

# Database connection settings (same as rest of ops-center)
DB_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "unicorn")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "unicorn")
DB_NAME = os.getenv("POSTGRES_DB", "unicorn_db")

# LLM settings
LITELLM_URL = os.getenv(
    "COLONEL_LLM_URL",
    "http://ops-center-direct:8084/api/v1/llm/chat/completions"
)
DEFAULT_MODEL = os.getenv("COLONEL_MODEL", "anthropic/claude-sonnet-4-5-20250929")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "unicorn-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Session settings
SESSION_TTL = int(os.getenv("COLONEL_SESSION_TTL", "86400"))  # 24 hours


_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _db_pool
    if _db_pool is None or _db_pool._closed:
        _db_pool = await asyncpg.create_pool(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            database=DB_NAME,
            min_size=1, max_size=5,
            command_timeout=10,
        )
    return _db_pool


async def get_colonel_config(colonel_id: str = "default") -> ColonelConfig:
    """Load colonel config from database, falling back to defaults."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT config_json, created_at, updated_at FROM colonels WHERE id = $1",
                colonel_id,
            )
            if row:
                data = json.loads(row["config_json"])
                data["id"] = colonel_id
                data["created_at"] = row["created_at"].isoformat() if row["created_at"] else None
                data["updated_at"] = row["updated_at"].isoformat() if row["updated_at"] else None
                return ColonelConfig(**data)
    except Exception as e:
        logger.warning(f"Could not load colonel config from DB: {e}")

    # Return defaults
    return ColonelConfig(id=colonel_id, model=DEFAULT_MODEL)


async def save_colonel_config(config: ColonelConfig) -> ColonelConfig:
    """Save colonel config to database (upsert)."""
    pool = await get_db_pool()
    data = config.model_dump(exclude={"id", "created_at", "updated_at"})
    config_json = json.dumps(data, default=str)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO colonels (id, config_json, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (id)
            DO UPDATE SET config_json = $2, updated_at = NOW()
            """,
            config.id, config_json,
        )

    logger.info(f"Saved colonel config: {config.name} ({config.id})")
    return await get_colonel_config(config.id)


async def list_colonels() -> list:
    """
    List every Colonel registered in the database.

    Returns a list of dicts: [{"id": ..., "name": ..., "server_name": ..., "mission": ...}, ...]
    Always includes the "default" Colonel synthetically if no row exists,
    so single-Colonel deployments behave as they did pre-multi-Colonel.
    """
    colonels = []
    seen_default = False
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, config_json FROM colonels ORDER BY id"
            )
            for row in rows:
                try:
                    data = json.loads(row["config_json"])
                except Exception:
                    data = {}
                cid = row["id"]
                if cid == "default":
                    seen_default = True
                colonels.append({
                    "id": cid,
                    "name": data.get("name") or "The Colonel",
                    "server_name": data.get("server_name"),
                    "mission": data.get("mission"),
                })
    except Exception as e:
        logger.warning(f"Could not list colonels from DB: {e}")

    if not seen_default:
        # Synthesize a default entry so /.well-known/agent.json keeps working
        # for fresh installs that haven't run colonel onboarding yet.
        try:
            default_cfg = await get_colonel_config("default")
            colonels.insert(0, {
                "id": "default",
                "name": default_cfg.name or "The Colonel",
                "server_name": default_cfg.server_name,
                "mission": default_cfg.mission,
            })
        except Exception as e:
            logger.warning(f"Could not synthesize default colonel entry: {e}")

    return colonels
