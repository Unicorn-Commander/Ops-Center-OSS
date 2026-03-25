"""
Federation Settings API - GUI configuration for federation.

Stores federation config in database instead of only env vars.
Env vars serve as bootstrap/defaults, GUI overrides take precedence.

Database Tables:
  - federation_config       (single-row node identity, branding, preferences)
  - federation_configured_peers  (manually added peer nodes)

Endpoints:
  GET    /api/v1/admin/federation/settings              - Full federation config
  PUT    /api/v1/admin/federation/settings              - Update federation settings
  POST   /api/v1/admin/federation/key/rotate            - Rotate federation key
  GET    /api/v1/admin/federation/peers                 - List configured peers
  POST   /api/v1/admin/federation/peers                 - Add peer node
  DELETE /api/v1/admin/federation/peers/{peer_id}       - Remove peer
  POST   /api/v1/admin/federation/peers/{peer_id}/test  - Test peer connectivity
  GET    /api/v1/admin/federation/services              - List local services + toggles
  PUT    /api/v1/admin/federation/services              - Toggle services on/off
  POST   /api/v1/admin/federation/discover              - Re-discover local services
  POST   /api/v1/admin/federation/test                  - Full federation self-test
  GET    /api/v1/admin/federation/hardware              - Current hardware profile

Security:
  All endpoints require admin authentication (same as service_keys_api.py).

Author: Backend Development Team
Date: March 2026
"""

import logging
import os
import secrets
import time
import json as json_lib
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import quote, unquote

import bcrypt
import httpx
import asyncpg
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

# Import admin authentication dependency (same as service_keys_api.py)
from admin_subscriptions_api import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/federation",
    tags=["Federation Settings"]
)


# ============================================================================
# Pydantic Models
# ============================================================================

class NodeIdentityConfig(BaseModel):
    """This node's identity in the federation."""
    node_id: str = Field(..., description="Unique slug for this node")
    display_name: str = Field(..., description="Human-readable name")
    endpoint_url: str = Field(..., description="Public URL for this node")
    region: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["inference"])
    is_billing_node: bool = False
    routing_priority: str = "cost"  # cost, latency, quality


class NodeBrandingConfig(BaseModel):
    """Per-node branding that travels with federation registration."""
    theme_id: str = "dark"
    logo_url: Optional[str] = None
    company_name: Optional[str] = None
    company_subtitle: Optional[str] = None
    accent_color: Optional[str] = None
    favicon_url: Optional[str] = None


class FederationSettingsUpdate(BaseModel):
    """Partial update payload for federation settings."""
    enabled: Optional[bool] = None
    identity: Optional[NodeIdentityConfig] = None
    branding: Optional[NodeBrandingConfig] = None
    heartbeat_interval: Optional[int] = None
    auto_discover_services: Optional[bool] = None


class FederationSettingsResponse(BaseModel):
    """Full federation settings for this node."""
    enabled: bool = False
    identity: Optional[NodeIdentityConfig] = None
    branding: Optional[NodeBrandingConfig] = None
    federation_key_preview: Optional[str] = None
    peers: List[Dict[str, Any]] = Field(default_factory=list)
    heartbeat_interval: int = 30
    auto_discover_services: bool = True
    advertised_services: Dict[str, bool] = Field(default_factory=dict)


class PeerConfig(BaseModel):
    """Configuration for a peer node."""
    peer_url: str
    display_name: Optional[str] = None
    federation_key: Optional[str] = None
    trust_level: str = "full"  # full, inference_only, read_only
    auto_connect: bool = True


class PeerResponse(BaseModel):
    """Response model for a configured peer."""
    id: str
    peer_url: str
    display_name: Optional[str] = None
    trust_level: str = "full"
    auto_connect: bool = True
    last_test_at: Optional[str] = None
    last_test_result: Optional[Dict[str, Any]] = None
    created_at: str


class ServiceToggle(BaseModel):
    """Toggle a service on/off for federation advertisement."""
    service_type: str
    enabled: bool


class KeyRotateResponse(BaseModel):
    """Response when rotating the federation key (full key shown once)."""
    federation_key: str
    federation_key_preview: str
    warning: str = "Save this federation key now. You won't be able to see it again."


class PeerTestResult(BaseModel):
    """Result of testing connectivity to a peer."""
    reachable: bool
    latency_ms: Optional[int] = None
    node_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def generate_federation_key() -> tuple:
    """
    Generate a secure federation key.
    Format: fk-{random_hex_32}-{year}
    Returns: (full_key, prefix)
    """
    random_hex = secrets.token_hex(16)
    year = datetime.utcnow().year
    full_key = f"fk-{random_hex}-{year}"
    prefix = f"fk-{random_hex[:8]}"
    return full_key, prefix


def hash_key(key: str) -> str:
    """Hash a key with bcrypt for secure storage."""
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state."""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


def _env_defaults() -> dict:
    """Env-var fallbacks for bootstrap (before DB is configured)."""
    return {
        "enabled": os.getenv("FEDERATION_ENABLED", "false").lower() == "true",
        "node_id": os.getenv("FEDERATION_NODE_ID", ""),
        "display_name": os.getenv("FEDERATION_DISPLAY_NAME", ""),
        "endpoint_url": os.getenv("FEDERATION_ENDPOINT_URL", ""),
        "region": os.getenv("FEDERATION_REGION", ""),
        "heartbeat_interval": int(os.getenv("FEDERATION_HEARTBEAT_INTERVAL", "30")),
    }


async def _get_config_row(pool: asyncpg.Pool) -> Optional[asyncpg.Record]:
    """Fetch the single federation_config row, if any."""
    try:
        return await pool.fetchrow("SELECT * FROM federation_config LIMIT 1")
    except Exception as e:
        logger.warning(f"federation_config table query failed (may not exist yet): {e}")
        return None


def _row_to_settings(row, peers: list) -> FederationSettingsResponse:
    """Convert a DB row + peers list to a FederationSettingsResponse."""
    roles = row["roles"] if row["roles"] else ["inference"]
    if isinstance(roles, str):
        roles = json_lib.loads(roles)

    branding_raw = row["branding"] if row["branding"] else {}
    if isinstance(branding_raw, str):
        branding_raw = json_lib.loads(branding_raw)

    advertised = row["advertised_services"] if row["advertised_services"] else {}
    if isinstance(advertised, str):
        advertised = json_lib.loads(advertised)

    identity = None
    if row["node_id"]:
        identity = NodeIdentityConfig(
            node_id=row["node_id"],
            display_name=row["display_name"] or "",
            endpoint_url=row["endpoint_url"] or "",
            region=row["region"],
            roles=roles,
            is_billing_node=row["is_billing_node"],
            routing_priority=row["routing_priority"] or "cost",
        )

    branding = NodeBrandingConfig(**branding_raw) if branding_raw else None

    key_preview = row["federation_key_prefix"] if row["federation_key_prefix"] else None

    peer_dicts = []
    for p in peers:
        test_result = p["last_test_result"]
        if isinstance(test_result, str):
            test_result = json_lib.loads(test_result)
        peer_dicts.append({
            "id": p["id"],
            "peer_url": p["peer_url"],
            "display_name": p["display_name"],
            "trust_level": p["trust_level"],
            "auto_connect": p["auto_connect"],
            "last_test_at": p["last_test_at"].isoformat() if p["last_test_at"] else None,
            "last_test_result": test_result,
            "created_at": p["created_at"].isoformat() if p["created_at"] else None,
        })

    return FederationSettingsResponse(
        enabled=row["enabled"],
        identity=identity,
        branding=branding,
        federation_key_preview=key_preview,
        peers=peer_dicts,
        heartbeat_interval=row["heartbeat_interval"],
        auto_discover_services=row["auto_discover_services"],
        advertised_services=advertised,
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/settings", response_model=FederationSettingsResponse)
async def get_federation_settings(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Get full federation configuration.
    Returns DB values with env-var fallbacks.
    """
    pool = await get_db_pool(request)
    row = await _get_config_row(pool)

    if not row:
        # No DB config yet — return env-var defaults
        defaults = _env_defaults()
        identity = None
        if defaults["node_id"]:
            identity = NodeIdentityConfig(
                node_id=defaults["node_id"],
                display_name=defaults["display_name"],
                endpoint_url=defaults["endpoint_url"],
                region=defaults["region"],
            )
        return FederationSettingsResponse(
            enabled=defaults["enabled"],
            identity=identity,
            heartbeat_interval=defaults["heartbeat_interval"],
        )

    peers = await pool.fetch(
        "SELECT * FROM federation_configured_peers ORDER BY created_at"
    )
    return _row_to_settings(row, peers)


@router.put("/settings", response_model=FederationSettingsResponse)
async def update_federation_settings(
    body: FederationSettingsUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Update federation identity, branding, and preferences.
    Creates the config row on first call (upsert).
    """
    pool = await get_db_pool(request)
    row = await _get_config_row(pool)

    if row is None:
        # First time — insert
        identity = body.identity
        branding = body.branding
        await pool.execute(
            """
            INSERT INTO federation_config (
                enabled, node_id, display_name, endpoint_url, region,
                roles, is_billing_node, routing_priority,
                branding, heartbeat_interval, auto_discover_services
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            body.enabled if body.enabled is not None else False,
            identity.node_id if identity else None,
            identity.display_name if identity else None,
            identity.endpoint_url if identity else None,
            identity.region if identity else None,
            json_lib.dumps(identity.roles) if identity else '["inference"]',
            identity.is_billing_node if identity else False,
            identity.routing_priority if identity else "cost",
            json_lib.dumps(branding.model_dump()) if branding else "{}",
            body.heartbeat_interval if body.heartbeat_interval is not None else 30,
            body.auto_discover_services if body.auto_discover_services is not None else True,
        )
    else:
        # Update existing row
        updates = []
        params = []
        idx = 1

        if body.enabled is not None:
            updates.append(f"enabled = ${idx}")
            params.append(body.enabled)
            idx += 1

        if body.identity is not None:
            for field, col in [
                ("node_id", "node_id"),
                ("display_name", "display_name"),
                ("endpoint_url", "endpoint_url"),
                ("region", "region"),
                ("is_billing_node", "is_billing_node"),
                ("routing_priority", "routing_priority"),
            ]:
                val = getattr(body.identity, field)
                updates.append(f"{col} = ${idx}")
                params.append(val)
                idx += 1
            updates.append(f"roles = ${idx}")
            params.append(json_lib.dumps(body.identity.roles))
            idx += 1

        if body.branding is not None:
            updates.append(f"branding = ${idx}")
            params.append(json_lib.dumps(body.branding.model_dump()))
            idx += 1

        if body.heartbeat_interval is not None:
            updates.append(f"heartbeat_interval = ${idx}")
            params.append(body.heartbeat_interval)
            idx += 1

        if body.auto_discover_services is not None:
            updates.append(f"auto_discover_services = ${idx}")
            params.append(body.auto_discover_services)
            idx += 1

        if updates:
            updates.append(f"updated_at = ${idx}")
            params.append(datetime.utcnow())
            idx += 1
            params.append(row["id"])
            await pool.execute(
                f"UPDATE federation_config SET {', '.join(updates)} WHERE id = ${idx}",
                *params,
            )

    # Re-fetch and return
    row = await _get_config_row(pool)
    peers = await pool.fetch(
        "SELECT * FROM federation_configured_peers ORDER BY created_at"
    )
    return _row_to_settings(row, peers)


@router.post("/key/rotate", response_model=KeyRotateResponse)
async def rotate_federation_key(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Generate a new federation key.
    The full key is returned ONCE in the response — store it securely.
    """
    pool = await get_db_pool(request)
    full_key, prefix = generate_federation_key()
    key_hash = hash_key(full_key)

    row = await _get_config_row(pool)
    if row is None:
        await pool.execute(
            """
            INSERT INTO federation_config (federation_key_hash, federation_key_prefix)
            VALUES ($1, $2)
            """,
            key_hash,
            prefix,
        )
    else:
        await pool.execute(
            """
            UPDATE federation_config
            SET federation_key_hash = $1, federation_key_prefix = $2, updated_at = $3
            WHERE id = $4
            """,
            key_hash,
            prefix,
            datetime.utcnow(),
            row["id"],
        )

    logger.info(f"Federation key rotated by admin {admin_user.get('email', 'unknown')}")

    return KeyRotateResponse(
        federation_key=full_key,
        federation_key_preview=prefix,
    )


# ---- Peers ----

@router.get("/peers", response_model=List[PeerResponse])
async def list_peers(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """List all configured peer nodes with their status."""
    pool = await get_db_pool(request)
    rows = await pool.fetch(
        "SELECT * FROM federation_configured_peers ORDER BY created_at"
    )
    results = []
    for p in rows:
        test_result = p["last_test_result"]
        if isinstance(test_result, str):
            test_result = json_lib.loads(test_result)
        results.append(PeerResponse(
            id=p["id"],
            peer_url=p["peer_url"],
            display_name=p["display_name"],
            trust_level=p["trust_level"],
            auto_connect=p["auto_connect"],
            last_test_at=p["last_test_at"].isoformat() if p["last_test_at"] else None,
            last_test_result=test_result,
            created_at=p["created_at"].isoformat() if p["created_at"] else None,
        ))
    return results


@router.post("/peers", response_model=PeerResponse, status_code=201)
async def add_peer(
    body: PeerConfig,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Add a new peer node.
    Triggers an immediate connectivity test.
    """
    pool = await get_db_pool(request)

    # Check for duplicate
    existing = await pool.fetchrow(
        "SELECT id FROM federation_configured_peers WHERE peer_url = $1",
        body.peer_url,
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Peer already configured: {body.peer_url}")

    # Test connectivity before saving
    test_result = await _test_peer_connectivity(body.peer_url, body.federation_key)

    row = await pool.fetchrow(
        """
        INSERT INTO federation_configured_peers (
            peer_url, display_name, federation_key_override,
            trust_level, auto_connect, last_test_at, last_test_result
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        body.peer_url,
        body.display_name,
        body.federation_key,  # stored as-is; consider encrypting in production
        body.trust_level,
        body.auto_connect,
        datetime.utcnow(),
        json_lib.dumps(test_result),
    )

    logger.info(f"Peer added: {body.peer_url} by admin {admin_user.get('email', 'unknown')}")

    tr = row["last_test_result"]
    if isinstance(tr, str):
        tr = json_lib.loads(tr)

    return PeerResponse(
        id=row["id"],
        peer_url=row["peer_url"],
        display_name=row["display_name"],
        trust_level=row["trust_level"],
        auto_connect=row["auto_connect"],
        last_test_at=row["last_test_at"].isoformat() if row["last_test_at"] else None,
        last_test_result=tr,
        created_at=row["created_at"].isoformat() if row["created_at"] else None,
    )


@router.delete("/peers/{peer_id}", status_code=204)
async def remove_peer(
    peer_id: str,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Remove a configured peer."""
    pool = await get_db_pool(request)
    result = await pool.execute(
        "DELETE FROM federation_configured_peers WHERE id = $1", peer_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Peer not found")

    logger.info(f"Peer {peer_id} removed by admin {admin_user.get('email', 'unknown')}")


@router.post("/peers/{peer_id}/test", response_model=PeerTestResult)
async def test_peer(
    peer_id: str,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Test connectivity to a specific peer."""
    pool = await get_db_pool(request)
    row = await pool.fetchrow(
        "SELECT * FROM federation_configured_peers WHERE id = $1", peer_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Peer not found")

    result = await _test_peer_connectivity(row["peer_url"], row["federation_key_override"])

    # Persist the test result
    await pool.execute(
        """
        UPDATE federation_configured_peers
        SET last_test_at = $1, last_test_result = $2, updated_at = $3
        WHERE id = $4
        """,
        datetime.utcnow(),
        json_lib.dumps(result),
        datetime.utcnow(),
        peer_id,
    )

    return PeerTestResult(**result)


async def _test_peer_connectivity(peer_url: str, federation_key: Optional[str] = None) -> dict:
    """
    Test connectivity to a peer node.
    Returns dict with reachable, latency_ms, node_info, error.
    """
    headers = {}
    if federation_key:
        headers["Authorization"] = f"Bearer {federation_key}"

    # Try the federation status endpoint
    test_url = f"{peer_url.rstrip('/')}/api/v1/federation/status"

    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            resp = await client.get(test_url, headers=headers)
        latency = int((time.monotonic() - start) * 1000)

        if resp.status_code < 400:
            try:
                node_info = resp.json()
            except Exception:
                node_info = {"raw": resp.text[:500]}
            return {
                "reachable": True,
                "latency_ms": latency,
                "node_info": node_info,
                "error": None,
            }
        else:
            return {
                "reachable": False,
                "latency_ms": latency,
                "node_info": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except httpx.TimeoutException:
        return {
            "reachable": False,
            "latency_ms": None,
            "node_info": None,
            "error": "Connection timed out (15s)",
        }
    except Exception as e:
        return {
            "reachable": False,
            "latency_ms": None,
            "node_info": None,
            "error": str(e),
        }


# ---- Services ----

@router.get("/services")
async def get_service_toggles(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    List locally detected services with their federation toggle state.
    Shows which services are advertised to the federation.
    """
    pool = await get_db_pool(request)
    row = await _get_config_row(pool)

    advertised = {}
    if row and row["advertised_services"]:
        advertised = row["advertised_services"]
        if isinstance(advertised, str):
            advertised = json_lib.loads(advertised)

    # Detect local services
    detected = await _detect_local_services()

    services = []
    for svc in detected:
        svc_type = svc["service_type"]
        services.append({
            **svc,
            "advertised": advertised.get(svc_type, True),  # default to advertised
        })

    return {"services": services, "source": "auto_detected"}


@router.put("/services")
async def update_service_toggles(
    body: List[ServiceToggle],
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Toggle services on/off for federation advertisement."""
    pool = await get_db_pool(request)
    row = await _get_config_row(pool)

    # Build the new advertised_services map
    current = {}
    if row and row["advertised_services"]:
        current = row["advertised_services"]
        if isinstance(current, str):
            current = json_lib.loads(current)

    for toggle in body:
        current[toggle.service_type] = toggle.enabled

    if row:
        await pool.execute(
            "UPDATE federation_config SET advertised_services = $1, updated_at = $2 WHERE id = $3",
            json_lib.dumps(current),
            datetime.utcnow(),
            row["id"],
        )
    else:
        await pool.execute(
            "INSERT INTO federation_config (advertised_services) VALUES ($1)",
            json_lib.dumps(current),
        )

    return {"advertised_services": current, "updated": True}


@router.post("/discover")
async def discover_services(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Trigger re-discovery of local services.
    Returns the updated list of detected services.
    """
    services = await _detect_local_services()
    return {"services": services, "discovered_at": datetime.utcnow().isoformat()}


async def _detect_local_services() -> List[dict]:
    """
    Detect locally running services by probing known endpoints.
    Returns a list of service dicts.
    """
    service_probes = [
        {"service_type": "llm", "name": "LLM Inference", "url": "http://localhost:8085/health"},
        {"service_type": "tts", "name": "Unicorn Orator TTS", "url": "http://localhost:8885/health"},
        {"service_type": "stt", "name": "Unicorn Amanuensis STT", "url": "http://localhost:9003/health"},
        {"service_type": "embeddings", "name": "Infinity Embeddings", "url": "http://localhost:8082/health"},
        {"service_type": "reranker", "name": "Infinity Reranker", "url": "http://localhost:8083/health"},
        {"service_type": "music_gen", "name": "Majik's Studio", "url": "http://localhost:8091/health"},
        {"service_type": "image_gen", "name": "Image Generation", "url": "http://localhost:8000/health"},
    ]

    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for probe in service_probes:
            try:
                resp = await client.get(probe["url"])
                status = "running" if resp.status_code < 400 else "error"
            except Exception:
                status = "offline"

            results.append({
                "service_type": probe["service_type"],
                "name": probe["name"],
                "status": status,
                "probe_url": probe["url"],
            })

    return results


# ---- Full Test & Hardware ----

@router.post("/test")
async def full_federation_test(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Full federation test:
    - Detect hardware
    - Discover local services
    - Test all configured peers
    Returns comprehensive test results.
    """
    pool = await get_db_pool(request)

    # 1. Hardware
    hardware = await _get_hardware_profile()

    # 2. Services
    services = await _detect_local_services()

    # 3. Peers
    peers = await pool.fetch(
        "SELECT * FROM federation_configured_peers ORDER BY created_at"
    )
    peer_results = []
    for p in peers:
        result = await _test_peer_connectivity(p["peer_url"], p["federation_key_override"])
        peer_results.append({
            "peer_url": p["peer_url"],
            "display_name": p["display_name"],
            **result,
        })
        # Update test result in DB
        await pool.execute(
            "UPDATE federation_configured_peers SET last_test_at = $1, last_test_result = $2 WHERE id = $3",
            datetime.utcnow(),
            json_lib.dumps(result),
            p["id"],
        )

    return {
        "tested_at": datetime.utcnow().isoformat(),
        "hardware": hardware,
        "services": services,
        "peers": peer_results,
        "summary": {
            "services_online": sum(1 for s in services if s["status"] == "running"),
            "services_total": len(services),
            "peers_reachable": sum(1 for p in peer_results if p["reachable"]),
            "peers_total": len(peer_results),
        },
    }


@router.get("/hardware")
async def get_hardware(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """Return current hardware detection results."""
    profile = await _get_hardware_profile()
    return profile


async def _get_hardware_profile() -> dict:
    """
    Get hardware profile using the federation hardware_detector if available,
    otherwise return a minimal profile.
    """
    try:
        from federation.hardware_detector import HardwareDetector
        detector = HardwareDetector()
        return detector.detect()
    except Exception as e:
        logger.warning(f"Hardware detection failed, returning minimal profile: {e}")
        # Minimal fallback
        import subprocess
        gpu_info = []
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        gpu_info.append({
                            "name": parts[0],
                            "memory_total_mb": int(parts[1]),
                            "memory_free_mb": int(parts[2]),
                        })
        except Exception:
            pass

        return {
            "gpus": gpu_info,
            "gpu_count": len(gpu_info),
            "detection_method": "fallback",
        }
