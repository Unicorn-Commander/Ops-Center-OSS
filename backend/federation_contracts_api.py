"""
Admin API for enforced federation trust contracts.

This router edits federation_peers, which is the table consumed by
federation.trust.TrustModeEnforcer. The older federation_configured_peers
table remains connection/bootstrap configuration only.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, validator

from audit_helpers import get_client_ip, get_session_id, get_user_agent
from audit_logger import audit_logger
from federation.trust import VALID_TRUST_MODES
from federation_settings_api import get_db_pool, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/federation",
    tags=["Federation Contracts"],
)

SERVICE_TYPES: Set[str] = {
    "llm",
    "embeddings",
    "reranker",
    "agents",
    "image_gen",
    "tts",
    "stt",
    "music_gen",
}
RESOURCE_GRANT_RE = re.compile(r"^[a-z_]+/[A-Za-z0-9._-]+$")
DEFAULT_TRUST_KEY = "FEDERATION_DEFAULT_TRUST_MODE"


class ContractUpdate(BaseModel):
    trust_mode: Optional[str] = None
    publish: Optional[List[str]] = None
    consume: Optional[List[str]] = None
    is_active: Optional[bool] = None

    class Config:
        extra = "forbid"

    @validator("trust_mode")
    def _normalize_mode(cls, value):
        if value is None:
            return value
        return value.lower()


class DefaultTrustModeUpdate(BaseModel):
    trust_mode: str = Field(..., description="Default trust mode for unknown peers")

    class Config:
        extra = "forbid"

    @validator("trust_mode")
    def _validate_mode(cls, value):
        mode = value.lower()
        if mode not in VALID_TRUST_MODES:
            raise ValueError(
                f"trust_mode must be one of: {', '.join(sorted(VALID_TRUST_MODES))}"
            )
        return mode


def _fields_set(model: BaseModel) -> Set[str]:
    """Pydantic v1/v2 compatible set of fields supplied by the client."""
    return set(getattr(model, "model_fields_set", getattr(model, "__fields_set__", set())))


def _normalize_json_list(value: Any) -> List[str]:
    """JSONB may arrive from asyncpg as a JSON string, list, or None."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _validate_trust_mode(mode: Optional[str]) -> str:
    if mode is None:
        raise HTTPException(status_code=422, detail="trust_mode cannot be null")
    normalized = mode.lower()
    if normalized not in VALID_TRUST_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"trust_mode must be one of: {', '.join(sorted(VALID_TRUST_MODES))}",
        )
    return normalized


def _validate_acl_entries(name: str, values: Optional[List[str]]) -> List[str]:
    if values is None:
        raise HTTPException(status_code=422, detail=f"{name} cannot be null")
    if not isinstance(values, list):
        raise HTTPException(status_code=422, detail=f"{name} must be a list")

    normalized: List[str] = []
    for raw in values:
        if not isinstance(raw, str):
            raise HTTPException(status_code=422, detail=f"{name} entries must be strings")
        entry = raw.strip()
        if not entry:
            raise HTTPException(status_code=422, detail=f"{name} entries cannot be empty")
        if entry in SERVICE_TYPES or RESOURCE_GRANT_RE.match(entry):
            normalized.append(entry)
            continue
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid {name} entry '{raw}'. Use a known service type "
                "or a type/resource grant like agents/sql-analyst."
            ),
        )
    return normalized


def _contract_state(row: Any) -> Dict[str, Any]:
    item = dict(row)
    return {
        "trust_mode": (item.get("trust_mode") or "full").lower(),
        "publish": _normalize_json_list(item.get("publish")),
        "consume": _normalize_json_list(item.get("consume")),
        "is_active": bool(item.get("is_active")),
    }


def _row_to_contract(row: Any) -> Dict[str, Any]:
    item = dict(row)
    return {
        "peer_row_id": item["peer_row_id"],
        "remote_node_id": item["remote_node_id"],
        "display_name": item.get("display_name"),
        "status": item.get("status"),
        "last_heartbeat": _iso(item.get("last_heartbeat")),
        "trust_mode": (item.get("trust_mode") or "full").lower(),
        "publish": _normalize_json_list(item.get("publish")),
        "consume": _normalize_json_list(item.get("consume")),
        "is_active": bool(item.get("is_active")),
        "capability_token": bool(item.get("capability_token")),
        "authority_for": _normalize_json_list(item.get("authority_for")),
        "consumer_of": _normalize_json_list(item.get("consumer_of")),
    }


async def _resolve_local_node_id(pool) -> Optional[str]:
    env_id = os.getenv("FEDERATION_LOCAL_NODE_ID") or os.getenv("FEDERATION_NODE_ID")
    if env_id:
        return env_id
    try:
        return await pool.fetchval("SELECT node_id FROM federation_config LIMIT 1")
    except Exception as exc:
        logger.warning("Unable to resolve local federation node_id from federation_config: %s", exc)
        return None


async def _get_default_trust_mode(pool) -> str:
    env_mode = os.getenv(DEFAULT_TRUST_KEY, "full").lower()
    if env_mode not in VALID_TRUST_MODES:
        env_mode = "isolated"
    try:
        value = await pool.fetchval(
            "SELECT value FROM platform_settings WHERE key = $1",
            DEFAULT_TRUST_KEY,
        )
    except Exception as exc:
        logger.debug("Default federation trust lookup failed, using env/default: %s", exc)
        value = None
    if value and value.lower() in VALID_TRUST_MODES:
        return value.lower()
    return env_mode


async def _fetch_contracts(pool, local_node_id: str) -> List[Dict[str, Any]]:
    rows = await pool.fetch(
        """
        SELECT fp.id AS peer_row_id,
               rn.node_id AS remote_node_id,
               rn.display_name,
               rn.status::text AS status,
               rn.last_heartbeat,
               fp.trust_mode,
               fp.publish,
               fp.consume,
               fp.is_active,
               fp.capability_token,
               fp.authority_for,
               fp.consumer_of
        FROM federation_peers fp
        JOIN federation_nodes ln ON ln.id = fp.local_node_id
        JOIN federation_nodes rn ON rn.id = fp.remote_node_id
        WHERE ln.node_id = $1
        ORDER BY rn.display_name NULLS LAST, rn.node_id
        """,
        local_node_id,
    )
    return [_row_to_contract(row) for row in rows]


async def _fetch_contract_row(pool, peer_row_id: str):
    return await pool.fetchrow(
        """
        SELECT fp.id,
               ln.node_id AS local_node_id,
               rn.node_id AS remote_node_id,
               fp.trust_mode,
               fp.publish,
               fp.consume,
               fp.is_active
        FROM federation_peers fp
        JOIN federation_nodes ln ON ln.id = fp.local_node_id
        JOIN federation_nodes rn ON rn.id = fp.remote_node_id
        WHERE fp.id = $1
        """,
        peer_row_id,
    )


async def _audit_contract_change(
    *,
    request: Request,
    admin_user: Dict[str, Any],
    action: str,
    resource_id: str,
    metadata: Dict[str, Any],
) -> None:
    try:
        await audit_logger.log(
            action=action,
            result="success",
            user_id=admin_user.get("id") or admin_user.get("user_id") or admin_user.get("email"),
            username=admin_user.get("email") or admin_user.get("username"),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            session_id=get_session_id(request),
            resource_type="federation_contract",
            resource_id=resource_id,
            metadata=metadata,
        )
    except Exception as exc:
        # Auditing must never mask the completed DB write, but it should be visible in logs.
        logger.error("Failed to audit federation contract change: %s", exc)


@router.get("/contracts")
async def list_contracts(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """List enforced trust contracts for this local node."""
    pool = await get_db_pool(request)
    local_node_id = await _resolve_local_node_id(pool)
    default_mode = await _get_default_trust_mode(pool)
    if not local_node_id:
        return {
            "local_node_id": None,
            "default_trust_mode": default_mode,
            "contracts": [],
            "warning": "Local federation node id is not configured.",
        }
    return {
        "local_node_id": local_node_id,
        "default_trust_mode": default_mode,
        "contracts": await _fetch_contracts(pool, local_node_id),
    }


@router.put("/contracts/default-trust-mode")
async def update_default_trust_mode(
    body: DefaultTrustModeUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Set the default trust mode used for unknown peers."""
    pool = await get_db_pool(request)
    before = await _get_default_trust_mode(pool)
    await pool.execute(
        """
        INSERT INTO platform_settings (key, value, category, is_secret, updated_at)
        VALUES ($1, $2, 'federation', FALSE, NOW())
        ON CONFLICT (key)
        DO UPDATE SET
            value = EXCLUDED.value,
            category = EXCLUDED.category,
            is_secret = EXCLUDED.is_secret,
            updated_at = NOW()
        """,
        DEFAULT_TRUST_KEY,
        body.trust_mode,
    )
    await _audit_contract_change(
        request=request,
        admin_user=admin_user,
        action="federation.default_trust_mode.update",
        resource_id=DEFAULT_TRUST_KEY,
        metadata={
            "before": {"trust_mode": before},
            "after": {"trust_mode": body.trust_mode},
        },
    )
    return {
        "trust_mode": body.trust_mode,
        "note": (
            "Applies within ~30s and only to unknown peers with no explicit "
            "federation_peers contract."
        ),
    }


@router.put("/contracts/{peer_row_id}")
async def update_contract(
    peer_row_id: str,
    body: ContractUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Partially update one enforced SELF -> peer trust contract."""
    pool = await get_db_pool(request)
    local_node_id = await _resolve_local_node_id(pool)
    if not local_node_id:
        raise HTTPException(status_code=400, detail="Local federation node id is not configured")

    supplied = _fields_set(body)
    if not supplied:
        raise HTTPException(status_code=422, detail="At least one field must be supplied")

    updates = []
    params: List[Any] = []
    idx = 1

    if "trust_mode" in supplied:
        updates.append(f"trust_mode = ${idx}")
        params.append(_validate_trust_mode(body.trust_mode))
        idx += 1
    if "publish" in supplied:
        updates.append(f"publish = ${idx}::jsonb")
        params.append(json.dumps(_validate_acl_entries("publish", body.publish)))
        idx += 1
    if "consume" in supplied:
        updates.append(f"consume = ${idx}::jsonb")
        params.append(json.dumps(_validate_acl_entries("consume", body.consume)))
        idx += 1
    if "is_active" in supplied:
        if body.is_active is None:
            raise HTTPException(status_code=422, detail="is_active cannot be null")
        updates.append(f"is_active = ${idx}")
        params.append(body.is_active)
        idx += 1

    before_row = await _fetch_contract_row(pool, peer_row_id)
    if not before_row:
        raise HTTPException(status_code=404, detail="Federation contract not found")
    if before_row["local_node_id"] != local_node_id:
        raise HTTPException(status_code=404, detail="Federation contract not found for local node")

    before = _contract_state(before_row)
    params.append(peer_row_id)
    await pool.execute(
        f"UPDATE federation_peers SET {', '.join(updates)} WHERE id = ${idx}",
        *params,
    )

    after_row = await _fetch_contract_row(pool, peer_row_id)
    after = _contract_state(after_row)
    await _audit_contract_change(
        request=request,
        admin_user=admin_user,
        action="federation.contract.update",
        resource_id=peer_row_id,
        metadata={
            "local_node_id": local_node_id,
            "peer_node_id": before_row["remote_node_id"],
            "before": before,
            "after": after,
        },
    )

    return {
        "updated": True,
        "peer_row_id": peer_row_id,
        "remote_node_id": before_row["remote_node_id"],
        **after,
    }


@router.get("/contracts/agent-choices")
async def agent_choices(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Return local agent grant choices as agents/<id> strings when available."""
    pool = await get_db_pool(request)
    local_node_id = await _resolve_local_node_id(pool)
    if not local_node_id:
        return {"agents": []}
    try:
        rows = await pool.fetch(
            """
            SELECT fs.models
            FROM federation_services fs
            JOIN federation_nodes fn ON fn.id = fs.node_id
            WHERE fn.node_id = $1 AND fs.service_type::text = 'agents'
            """,
            local_node_id,
        )
    except Exception as exc:
        logger.debug("Local federation agent choices unavailable: %s", exc)
        return {"agents": []}

    agent_ids: Set[str] = set()
    for row in rows:
        for agent_id in _normalize_json_list(row["models"]):
            if agent_id:
                agent_ids.add(agent_id)
    return {
        "agents": [
            {"agent_id": agent_id, "grant": f"agents/{agent_id}"}
            for agent_id in sorted(agent_ids)
        ]
    }
