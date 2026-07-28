"""
Per-(app, model) included-vs-metered inference policy.

Two billing axes are orthogonal: subscription = app ACCESS (+ some *included*
inference bundled into the product), and credits = a *metered* inference wallet.
This module is the policy layer that decides, for a given (app, model), whether
a call is:

  - "included"  → bundled into the app subscription; cost absorbed, charge nothing
                  (e.g. Meeting-Ops summaries on Qwen3.6, Parakeet STT), or
  - "metered"   → drawn from the org's credit wallet (the default).

It is keyed by the calling UC app (the service-key `service_name`) and the model.
With ZERO rows in `app_model_policy`, everything resolves to "metered" — i.e. no
behavior change until an admin adds explicit "included" rows.

Matching is most-specific-wins: exact model > longest prefix (`Qwen3.6-*`) > app
wildcard (`*`). The row set is cached in-process (60s); on a refresh error the
stale cache keeps serving, and a cold cache with no DB defaults to "metered"
(revenue-safe, matches the no-rows baseline).
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CACHE_TTL = 60.0
_cache: Dict[str, Any] = {"ts": 0.0, "rows": None}  # rows: list[dict] or None (never loaded)

METERED = "metered"
INCLUDED = "included"


async def _load_rows(db_pool) -> List[Dict[str, Any]]:
    async with db_pool.acquire() as conn:
        recs = await conn.fetch(
            "SELECT app, model, policy FROM app_model_policy"
        )
    return [{"app": r["app"], "model": r["model"], "policy": r["policy"]} for r in recs]


async def _rows(db_pool) -> List[Dict[str, Any]]:
    """Cached policy rows; stale-cache-on-error, never raises."""
    now = time.monotonic()
    if _cache["rows"] is not None and (now - _cache["ts"]) <= _CACHE_TTL:
        return _cache["rows"]
    if db_pool is None:
        return _cache["rows"] or []
    try:
        rows = await _load_rows(db_pool)
        _cache["rows"] = rows
        _cache["ts"] = now
        return rows
    except Exception as exc:
        logger.debug("app_model_policy load failed (using stale/empty): %s", exc)
        _cache["ts"] = now
        return _cache["rows"] or []


def _specificity(row_model: str) -> int:
    """Higher = more specific. exact > prefix(by length) > '*'."""
    if row_model == "*":
        return 0
    if row_model.endswith("*"):
        return 1 + len(row_model)  # longer prefix wins among prefixes
    return 10_000  # exact match always wins


def _matches(row_model: str, model: str) -> bool:
    if row_model == "*":
        return True
    if row_model.endswith("*"):
        return model.startswith(row_model[:-1])
    return row_model == model


async def resolve_inference_policy(
    app: Optional[str], model: Optional[str], db_pool=None
) -> str:
    """Return 'included' or 'metered' for this (app, model). Defaults to
    'metered' (no app context, no matching row, or any error)."""
    if not app or not model:
        return METERED
    try:
        rows = await _rows(db_pool)
    except Exception:
        return METERED
    best_policy = METERED
    best_spec = -1
    for r in rows:
        if r["app"] != app:
            continue
        if not _matches(r["model"], model):
            continue
        spec = _specificity(r["model"])
        if spec > best_spec:
            best_spec = spec
            best_policy = r["policy"] or METERED
    return best_policy


def _reset_cache_for_tests() -> None:
    _cache["ts"] = 0.0
    _cache["rows"] = None
