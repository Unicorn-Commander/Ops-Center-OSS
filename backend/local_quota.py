"""
Local-LLM monthly usage quota counter (per-org)
================================================

System of record for "how many LOCAL tokens has this org used this month" — the
input to the `free_quota_overflow` local-pricing mode (see backend/local_pricing.py).

Design:
  * Durable counter of record = Postgres `org_local_token_usage (org_id, billing_month,
    tokens_used)` (migration core/0008). Survives restarts.
  * Redis (`local_tokens:{org_id}:{YYYY-MM}`) is a fast-path cache for the hot read on
    the request gate. On a Redis miss we fall back to Postgres and re-seed the cache.
  * FAIL-OPEN everywhere: a Redis or Postgres error must NEVER raise into the request
    path. Gating reads return a best-effort number; recording errors are logged. The
    worst case is a small boundary under-count (one request's tokens), never a blocked
    paying request and never a hard failure.

Org-scoped (not per-user) to match the credit wallet's scope: the quota is the org's.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_redis = None  # lazy singleton


def current_billing_month() -> str:
    """UTC 'YYYY-MM' — the bucket key for the monthly quota."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _redis_key(org_id: str, month: str) -> str:
    return f"local_tokens:{org_id}:{month}"


async def _get_redis():
    """Lazily build a shared redis client. Returns None if unavailable (fail-open)."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(
            f"redis://{os.getenv('REDIS_HOST', 'unicorn-redis')}:{os.getenv('REDIS_PORT', 6379)}",
            encoding="utf-8",
            decode_responses=True,
        )
        return _redis
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("[local_quota] redis unavailable, falling back to Postgres only: %s", exc)
        return None


async def _pg_get(org_id: str, month: str) -> int:
    from database import get_db_connection
    async with await get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT tokens_used FROM org_local_token_usage WHERE org_id = $1 AND billing_month = $2",
            org_id, month,
        )
        return int(row["tokens_used"]) if row else 0


async def get_local_tokens(org_id: str) -> int:
    """Best-effort monthly local-token count for the org. Never raises."""
    if not org_id:
        return 0
    month = current_billing_month()
    # Fast path: Redis
    try:
        r = await _get_redis()
        if r is not None:
            val = await r.get(_redis_key(org_id, month))
            if val is not None:
                return int(val)
    except Exception as exc:
        logger.debug("[local_quota] redis read miss/err for %s: %s", org_id, exc)
    # Durable fallback: Postgres (and re-seed cache)
    try:
        pg_val = await _pg_get(org_id, month)
        try:
            r = await _get_redis()
            if r is not None:
                await r.set(_redis_key(org_id, month), pg_val, ex=60 * 60 * 24 * 40)  # ~40d TTL
        except Exception:
            pass
        return pg_val
    except Exception as exc:
        logger.warning("[local_quota] pg read failed for %s (fail-open=0): %s", org_id, exc)
        return 0


async def add_local_tokens(org_id: str, tokens: int) -> None:
    """Record `tokens` of LOCAL usage for the org's current month. Never raises."""
    if not org_id or not tokens or tokens <= 0:
        return
    month = current_billing_month()
    # Durable write (system of record)
    try:
        from database import get_db_connection
        async with await get_db_connection() as conn:
            await conn.execute(
                """
                INSERT INTO org_local_token_usage (org_id, billing_month, tokens_used, updated_at)
                VALUES ($1, $2, $3, now())
                ON CONFLICT (org_id, billing_month)
                DO UPDATE SET tokens_used = org_local_token_usage.tokens_used + EXCLUDED.tokens_used,
                              updated_at = now()
                """,
                org_id, month, int(tokens),
            )
    except Exception as exc:
        logger.warning("[local_quota] pg record failed for %s (+%s): %s", org_id, tokens, exc)
    # Cache increment (best-effort)
    try:
        r = await _get_redis()
        if r is not None:
            key = _redis_key(org_id, month)
            await r.incrby(key, int(tokens))
            await r.expire(key, 60 * 60 * 24 * 40)
    except Exception as exc:
        logger.debug("[local_quota] redis incr failed for %s: %s", org_id, exc)
