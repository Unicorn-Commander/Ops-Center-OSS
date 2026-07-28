"""
App-Model Pricing Policy API - admin CRUD for the per-(app, model)
included-vs-metered inference policy.

Two billing axes are orthogonal: a subscription grants app ACCESS (and may
*include* some inference bundled into the product), while credits are a
*metered* inference wallet. The `app_model_policy` table is the policy layer
that decides, for a given (app, model), whether a call is:

  - "included" -> bundled into the app subscription; cost absorbed, charge nothing
  - "metered"  -> drawn from the org's credit wallet (the DEFAULT)

The resolver that READS this table lives in `inference_policy.py`
(most-specific match: exact model > longest `prefix*` > `*`; default metered;
60s cache). This module is the write/admin side: with ZERO rows everything
resolves to "metered" (no behavior change); rows only ADD "included"
exceptions.

Endpoints (admin-gated, every write audited):
  GET    /api/v1/admin/inference-policy        - list all rows
  POST   /api/v1/admin/inference-policy        - create a row (409 on duplicate)
  PUT    /api/v1/admin/inference-policy/{id}   - update policy and/or note
  DELETE /api/v1/admin/inference-policy/{id}   - delete a row

Matching/validation here is kept in lock-step with the resolver's contract:
`model` must be an exact id, a prefix ending in '*' (e.g. 'Qwen3.6-*'), or the
bare wildcard '*'; `policy` must be 'included' or 'metered'.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/inference-policy",
    tags=["Inference Policy"],
)

VALID_POLICIES = {"included", "metered"}


# ============================================================================
# Auth (mirrors federation_settings_api.require_admin — Redis-session based)
# ============================================================================

async def require_admin(request: Request):
    """Verify admin access using the same Redis/browser session used by admin pages."""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    user = getattr(request, "session", {}).get("user", {}) if hasattr(request, "session") else {}
    session_token = request.cookies.get("session_token")

    if not user and session_token:
        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        sessions = RedisSessionManager(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
        if session_token in sessions:
            user = sessions[session_token].get("user", {})

    is_admin = (
        user.get("role") == "admin"
        or user.get("is_admin") is True
        or user.get("is_superuser") is True
        or "admin" in user.get("groups", [])
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state."""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Validation helpers (kept in lock-step with inference_policy.py matching)
# ============================================================================

def _validate_model(model: str) -> str:
    """A model selector is an exact id, a 'prefix*', or the bare '*'.

    The resolver treats a trailing '*' as a prefix match and a bare '*' as the
    app wildcard; a '*' anywhere else is not meaningful, so reject it to keep
    rows honest.
    """
    model = (model or "").strip()
    if not model:
        raise ValueError("model is required")
    if model == "*":
        return model
    star_count = model.count("*")
    if star_count == 0:
        return model  # exact match
    if star_count == 1 and model.endswith("*"):
        if len(model) == 1:  # just "*" handled above; guard for safety
            return model
        return model  # prefix match like 'Qwen3.6-*'
    raise ValueError(
        "model must be an exact id, a prefix ending in '*' (e.g. 'Qwen3.6-*'), or '*'"
    )


def _validate_policy(policy: str) -> str:
    policy = (policy or "").strip().lower()
    if policy not in VALID_POLICIES:
        raise ValueError("policy must be 'included' or 'metered'")
    return policy


# ============================================================================
# Pydantic Models
# ============================================================================

class PolicyRow(BaseModel):
    """A single app_model_policy row."""
    id: int
    app: str
    model: str
    policy: str
    note: Optional[str] = None
    created_at: Optional[str] = None


class PolicyCreate(BaseModel):
    """Create payload for a new policy row."""
    app: str = Field(..., description="Calling service_name / feature_key, e.g. 'meeting-ops-service'")
    model: str = Field(..., description="Exact model id, a prefix ending in '*', or '*'")
    policy: str = Field("metered", description="'included' or 'metered'")
    note: Optional[str] = Field(None, description="Free-text reason for this exception")

    @field_validator("app")
    @classmethod
    def _app_nonempty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("app is required")
        return v

    @field_validator("model")
    @classmethod
    def _model_valid(cls, v: str) -> str:
        return _validate_model(v)

    @field_validator("policy")
    @classmethod
    def _policy_valid(cls, v: str) -> str:
        return _validate_policy(v)


class PolicyUpdate(BaseModel):
    """Partial update — set policy and/or note. At least one must be provided."""
    policy: Optional[str] = None
    note: Optional[str] = None

    @field_validator("policy")
    @classmethod
    def _policy_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_policy(v)


# ============================================================================
# Row serialization
# ============================================================================

def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
    created = row["created_at"]
    return {
        "id": row["id"],
        "app": row["app"],
        "model": row["model"],
        "policy": row["policy"],
        "note": row["note"],
        "created_at": created.isoformat() if isinstance(created, datetime) else created,
    }


# ============================================================================
# Audit (best-effort; never let a logging failure break the write)
# ============================================================================

async def _audit(action: str, result: str, admin_user: dict, resource_id, metadata: dict):
    try:
        from audit_logger import audit_logger
        await audit_logger.log(
            action=action,
            result=result,
            user_id=admin_user.get("id") or admin_user.get("user_id") or admin_user.get("sub"),
            username=admin_user.get("username") or admin_user.get("email"),
            resource_type="app_model_policy",
            resource_id=str(resource_id) if resource_id is not None else None,
            metadata=metadata,
        )
    except Exception as exc:  # pragma: no cover - audit must never break the request
        logger.warning("audit log failed for %s: %s", action, exc)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[PolicyRow])
@router.get("/", response_model=List[PolicyRow])
async def list_policies(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """List all app_model_policy rows, ordered by app then model."""
    pool = await get_db_pool(request)
    try:
        rows = await pool.fetch(
            "SELECT id, app, model, policy, note, created_at "
            "FROM app_model_policy ORDER BY app, model"
        )
    except Exception as exc:
        logger.error("Failed to list app_model_policy rows: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load policy rows")
    return [_row_to_dict(r) for r in rows]


@router.post("", response_model=PolicyRow, status_code=201)
@router.post("/", response_model=PolicyRow, status_code=201)
async def create_policy(
    body: PolicyCreate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Create a policy row. Returns 409 if (app, model) already exists."""
    pool = await get_db_pool(request)
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO app_model_policy (app, model, policy, note)
            VALUES ($1, $2, $3, $4)
            RETURNING id, app, model, policy, note, created_at
            """,
            body.app,
            body.model,
            body.policy,
            body.note,
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=409,
            detail=f"A policy for app '{body.app}' and model '{body.model}' already exists",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create app_model_policy row: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create policy row")

    result = _row_to_dict(row)
    await _audit(
        "inference_policy.create", "success", admin_user, result["id"],
        {"app": body.app, "model": body.model, "policy": body.policy, "note": body.note},
    )
    return result


@router.put("/{policy_id}", response_model=PolicyRow)
async def update_policy(
    policy_id: int,
    body: PolicyUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Update policy and/or note on an existing row. 404 if missing."""
    if body.policy is None and body.note is None:
        raise HTTPException(status_code=400, detail="Provide policy and/or note to update")

    pool = await get_db_pool(request)

    existing = await pool.fetchrow(
        "SELECT id, app, model, policy, note, created_at FROM app_model_policy WHERE id = $1",
        policy_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Policy row not found")

    before = _row_to_dict(existing)
    new_policy = body.policy if body.policy is not None else existing["policy"]
    new_note = body.note if body.note is not None else existing["note"]

    try:
        row = await pool.fetchrow(
            """
            UPDATE app_model_policy SET policy = $1, note = $2 WHERE id = $3
            RETURNING id, app, model, policy, note, created_at
            """,
            new_policy,
            new_note,
            policy_id,
        )
    except Exception as exc:
        logger.error("Failed to update app_model_policy row %s: %s", policy_id, exc)
        raise HTTPException(status_code=500, detail="Failed to update policy row")

    after = _row_to_dict(row)
    await _audit(
        "inference_policy.update", "success", admin_user, policy_id,
        {"before": before, "after": after},
    )
    return after


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: int,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Delete a policy row. 404 if missing. Reverts that (app, model) to metered."""
    pool = await get_db_pool(request)

    existing = await pool.fetchrow(
        "SELECT id, app, model, policy, note, created_at FROM app_model_policy WHERE id = $1",
        policy_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Policy row not found")

    deleted = _row_to_dict(existing)
    try:
        await pool.execute("DELETE FROM app_model_policy WHERE id = $1", policy_id)
    except Exception as exc:
        logger.error("Failed to delete app_model_policy row %s: %s", policy_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete policy row")

    await _audit(
        "inference_policy.delete", "success", admin_user, policy_id, {"deleted": deleted},
    )
    return None
