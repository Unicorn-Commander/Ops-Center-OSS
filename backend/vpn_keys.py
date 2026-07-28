"""
VPN Key Management - Headscale pre-auth key + node control for Ops Center

Admins generate, list, and revoke Headscale pre-auth keys and manage
connected VPN nodes from the dashboard instead of SSH.

Headscale is invoked via `docker exec unicorn-headscale headscale ...`
(the ops-center container has /var/run/docker.sock mounted).

Admin-only. Uses session-based auth that mirrors llm_keys.py.
"""

import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/network", tags=["VPN / Network"])

HEADSCALE_CONTAINER = "unicorn-headscale"
HEADSCALE_USER_ID = "1"  # "unicorn"
CMD_TIMEOUT = 15


class HeadscaleUnavailable(Exception):
    """Raised when the Headscale (VPN) container is not deployed on this node."""
    pass


# ============================================================================
# Auth (session + admin)
# ============================================================================

async def get_current_user(request: Request) -> Dict:
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {}) or {}
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    user["user_id"] = user.get("user_id") or user.get("sub") or user.get("email", "unknown")
    return user


async def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ============================================================================
# Models
# ============================================================================

class CreateVPNKeyRequest(BaseModel):
    name: Optional[str] = Field(None, description="Human-readable name (stored in tag metadata)")
    tags: List[str] = Field(default_factory=lambda: ["tag:admin"])
    reusable: bool = False
    expiration: str = Field("87600h", description="Headscale-style duration (e.g. 24h, 30d, 87600h)")
    ephemeral: bool = False


class VPNKeyResponse(BaseModel):
    id: int
    key: str
    user: str
    reusable: bool
    ephemeral: bool
    used: bool
    tags: List[str]
    created_at: Optional[str]
    expiration: Optional[str]


class VPNNodeResponse(BaseModel):
    id: int
    name: str
    given_name: str
    ip_addresses: List[str]
    user: str
    last_seen: Optional[str]
    online: bool
    os: str
    tags: List[str]
    register_method: str
    expiry: Optional[str]


# ============================================================================
# Headscale CLI bridge
# ============================================================================

def _headscale(args: List[str]) -> str:
    cmd = ["docker", "exec", HEADSCALE_CONTAINER, "headscale"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CMD_TIMEOUT)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Docker CLI not available in container")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Headscale command timed out")

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        msg = stderr or stdout or "headscale command failed"
        logger.error("headscale %s failed (rc=%s): %s", " ".join(args), result.returncode, msg)
        # Distinguish "VPN not deployed on this node" from a genuine headscale error
        # so read endpoints can degrade gracefully instead of returning 500.
        low = msg.lower()
        if "no such container" in low or "cannot connect to the docker daemon" in low:
            raise HeadscaleUnavailable(msg)
        raise HTTPException(status_code=500, detail="Headscale: " + msg[:200])

    return result.stdout


def _headscale_json(args: List[str]):
    raw = _headscale(args + ["-o", "json"])
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse headscale JSON: %s — raw: %s", e, raw[:300])
        raise HTTPException(status_code=500, detail="Failed to parse headscale response")


def _proto_timestamp_to_iso(ts) -> Optional[str]:
    """Convert headscale gRPC timestamp {seconds, nanos} to ISO 8601 string."""
    if not ts:
        return None
    seconds = ts.get("seconds", 0) if isinstance(ts, dict) else 0
    if not seconds or seconds <= 0:
        return None
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return None


def _key_is_used(key_obj: dict) -> bool:
    """A preauthkey is considered used if it's one-shot (non-reusable) and has been consumed."""
    if key_obj.get("used"):
        return True
    # Some headscale versions expose used_count or similar; fall back to false
    return False


def _key_is_expired(key_obj: dict) -> bool:
    exp = key_obj.get("expiration") or {}
    seconds = exp.get("seconds", 0) if isinstance(exp, dict) else 0
    if not seconds:
        return False
    return datetime.now(tz=timezone.utc).timestamp() > seconds


def _node_is_online(node: dict) -> bool:
    """Consider a node online if last_seen is within 2 minutes."""
    ts = node.get("last_seen") or {}
    seconds = ts.get("seconds", 0) if isinstance(ts, dict) else 0
    if not seconds:
        return False
    return (datetime.now(tz=timezone.utc).timestamp() - seconds) < 120


def _serialize_key(k: dict) -> dict:
    return {
        "id": int(k.get("id", 0)),
        "key": k.get("key", ""),
        "user": (k.get("user") or {}).get("name", ""),
        "reusable": bool(k.get("reusable", False)),
        "ephemeral": bool(k.get("ephemeral", False)),
        "used": _key_is_used(k),
        "expired": _key_is_expired(k),
        "tags": list(k.get("aclTags") or k.get("acl_tags") or []),
        "created_at": _proto_timestamp_to_iso(k.get("created_at")),
        "expiration": _proto_timestamp_to_iso(k.get("expiration")),
    }


def _serialize_node(n: dict) -> dict:
    tags = list(n.get("forced_tags") or []) + list(n.get("valid_tags") or [])
    # de-dup while preserving order
    seen = set()
    unique_tags = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique_tags.append(t)

    return {
        "id": int(n.get("id", 0)),
        "name": n.get("name") or n.get("given_name") or "",
        "given_name": n.get("given_name") or n.get("name") or "",
        "ip_addresses": list(n.get("ip_addresses") or []),
        "user": (n.get("user") or {}).get("name", ""),
        "last_seen": _proto_timestamp_to_iso(n.get("last_seen")),
        "online": _node_is_online(n),
        "os": (n.get("host_info") or {}).get("OS") or (n.get("hostinfo") or {}).get("OS") or "",
        "hostname": (n.get("host_info") or {}).get("Hostname") or (n.get("hostinfo") or {}).get("Hostname") or "",
        "tags": unique_tags,
        "register_method": n.get("register_method") or "",
        "expiry": _proto_timestamp_to_iso(n.get("expiry")),
    }


# ============================================================================
# Pre-auth key endpoints
# ============================================================================

@router.get("/vpn-keys")
async def list_vpn_keys(_: Dict = Depends(require_admin)):
    # Note: `preauthkeys list` does not take a user filter; it returns all
    # keys across users, each stamped with its owning user object.
    try:
        data = _headscale_json(["preauthkeys", "list"])
    except HeadscaleUnavailable:
        logger.warning("Headscale not deployed on this node; returning empty VPN key list")
        return []
    keys = data if isinstance(data, list) else []
    # Filter to our configured user id so the UI only shows the mesh we manage.
    keys = [k for k in keys if str((k.get("user") or {}).get("id", "")) == HEADSCALE_USER_ID]
    return [_serialize_key(k) for k in keys]


@router.post("/vpn-keys", status_code=201)
async def create_vpn_key(req: CreateVPNKeyRequest, _: Dict = Depends(require_admin)):
    args = [
        "preauthkeys", "create",
        "-u", HEADSCALE_USER_ID,
        "--expiration", req.expiration,
    ]
    if req.reusable:
        args.append("--reusable")
    if req.ephemeral:
        args.append("--ephemeral")
    if req.tags:
        args += ["--tags", ",".join(req.tags)]

    # Note: headscale preauthkeys create -o json returns just the key string on some
    # versions and a full object on others. Fetch the new key via list afterward
    # to normalise the response shape.
    try:
        raw = _headscale(args + ["-o", "json"]).strip()
    except HeadscaleUnavailable:
        raise HTTPException(status_code=503, detail="Headscale (VPN) is not deployed on this node")
    created_key_str: Optional[str] = None
    parsed = None
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None

    if isinstance(parsed, str):
        created_key_str = parsed
    elif isinstance(parsed, dict):
        created_key_str = parsed.get("key")

    # Refresh list and find matching key to return full metadata
    all_keys_raw = _headscale_json(["preauthkeys", "list"]) or []
    all_keys = [k for k in all_keys_raw if str((k.get("user") or {}).get("id", "")) == HEADSCALE_USER_ID]
    match = None
    if created_key_str:
        for k in all_keys:
            if k.get("key") == created_key_str:
                match = k
                break

    if not match and isinstance(parsed, dict):
        match = parsed
    if not match and all_keys:
        match = all_keys[-1]  # fall back to most recent

    if not match:
        raise HTTPException(status_code=500, detail="Created key, but could not read it back")

    serialized = _serialize_key(match)
    if req.name:
        serialized["name"] = req.name
    logger.info("Created VPN pre-auth key id=%s tags=%s", serialized.get("id"), req.tags)
    return serialized


@router.delete("/vpn-keys/{key_id}")
async def expire_vpn_key(key_id: int, _: Dict = Depends(require_admin)):
    try:
        _headscale(["preauthkeys", "expire", "-i", str(key_id), "--force"])
    except HeadscaleUnavailable:
        raise HTTPException(status_code=503, detail="Headscale (VPN) is not deployed on this node")
    logger.info("Expired VPN pre-auth key id=%s", key_id)
    return {"success": True, "message": "VPN key expired"}


# ============================================================================
# Node endpoints
# ============================================================================

@router.get("/nodes")
async def list_nodes(_: Dict = Depends(require_admin)):
    try:
        data = _headscale_json(["nodes", "list"])
    except HeadscaleUnavailable:
        logger.warning("Headscale not deployed on this node; returning empty node list")
        return []
    nodes = data if isinstance(data, list) else []
    return [_serialize_node(n) for n in nodes]


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: int, _: Dict = Depends(require_admin)):
    try:
        _headscale(["nodes", "delete", "-i", str(node_id), "--force"])
    except HeadscaleUnavailable:
        raise HTTPException(status_code=503, detail="Headscale (VPN) is not deployed on this node")
    logger.info("Deleted VPN node id=%s", node_id)
    return {"success": True, "message": "Node removed"}


@router.post("/nodes/{node_id}/expire")
async def expire_node(node_id: int, _: Dict = Depends(require_admin)):
    try:
        _headscale(["nodes", "expire", "-i", str(node_id), "--force"])
    except HeadscaleUnavailable:
        raise HTTPException(status_code=503, detail="Headscale (VPN) is not deployed on this node")
    logger.info("Expired VPN node id=%s", node_id)
    return {"success": True, "message": "Node expired"}
