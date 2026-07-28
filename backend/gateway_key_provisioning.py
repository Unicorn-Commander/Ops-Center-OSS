"""
Per-Org Gateway-Key Provisioning — Metered-Inference Billing Keystone
=====================================================================

Each organization gets ONE LiteLLM virtual key that carries its:
  - metering identity  (user_id == org_id → Lago usage events keyed external_subscription_id=org_id)
  - budget             (max_budget)
  - model allow-list   (models)
  - rate limits        (rpm/tpm, optional)

The gateway runs with LITELLM_SUCCESS_CALLBACK=lago and charge_by=user_id, so a
virtual key whose user_id == org_id emits Lago usage events keyed to that org,
which attach to the org's Lago subscription (external_id == org_id) and bill at
the plan's usage charge. This was proven end-to-end; this module makes the
per-org key the contract primitive.

Design notes:
  - IDEMPOTENT: the org→key reference is persisted on the `organizations` row
    (litellm_gateway_key_id + litellm_gateway_key_encrypted). If a stored
    reference exists we return it. If not, we fall back to LiteLLM
    /key/list?user_id=<org_id> and match key_alias == "org-<org_id>" before
    creating, so a row wiped of its reference never produces a duplicate key.
  - FAILURE-ISOLATED: if the gateway (LiteLLM) is unreachable or misconfigured
    we log a warning and return None — we NEVER raise into the subscribe flow.
  - Reuses the repo's env conventions (LITELLM_PROXY_URL / LITELLM_MASTER_KEY,
    same as .env.example and litellm_api.py) and the Fernet helper in
    key_encryption.py for at-rest encryption of the key value.

Author: Claude (AI Assistant)
Date: 2026-06-09
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from auth_dependencies import require_authenticated_user
from get_credential import get_credential
from database import get_db_connection as _pkg_get_db_connection


async def get_db_connection():
    # The `database` package's get_db_connection() returns a PoolAcquireContext
    # (meant for `async with`), NOT a live connection — so the `conn = await
    # get_db_connection()` pattern used below needs the double-await shim that the
    # rest of this repo (e.g. org_billing_api.py) uses to get a real connection.
    return await (await _pkg_get_db_connection())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gateway (LiteLLM) configuration — same env vars as .env.example / litellm_api.py.
# Fall back to LITELLM_INTERNAL_URL (used by llm_keys.py) so any node that only
# sets one of the two still resolves the gateway.
# ---------------------------------------------------------------------------
# Resolve gateway creds DB-first (platform_settings) then env — the same
# get_credential helper lago_integration uses for LAGO_API_KEY, so the master key
# is DB-managed (settable in platform_settings without a container recreate).
# Module-level defaults are ENV-ONLY: get_credential() reads the DB, but at import
# time inside the running server the event loop is already running, so its sync DB
# path falls back to env and caches empty. We instead resolve DB-first LAZILY at
# call time via _resolve_gateway_creds() (get_credential_async), using these env
# values only as the fallback.
LITELLM_PROXY_URL = (
    os.getenv("LITELLM_PROXY_URL")
    or os.getenv("LITELLM_INTERNAL_URL")
    or "http://unicorn-litellm:4000"
).rstrip("/")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")


async def _resolve_gateway_creds():
    """Resolve (proxy_url, master_key) DB-first (platform_settings via
    get_credential_async) at CALL time, falling back to the env-derived module
    defaults. Avoids the import-time 'event loop already running' fallback that
    left the live server with an empty master key."""
    url, key = LITELLM_PROXY_URL, LITELLM_MASTER_KEY
    try:
        from get_credential import get_credential_async
        url = (await get_credential_async("LITELLM_PROXY_URL")) or url
        key = (await get_credential_async("LITELLM_MASTER_KEY")) or key
    except Exception as e:
        logger.warning("Gateway cred resolve fell back to env: %s", e)
    return (url or "").rstrip("/"), (key or "")

# Network timeout for gateway calls (provisioning must never hang a request).
_GATEWAY_TIMEOUT = float(os.getenv("LITELLM_PROVISION_TIMEOUT", "15"))


def _key_alias(org_id: str) -> str:
    """Stable per-org alias. One key per org → one alias per org."""
    return f"org-{org_id}"


def _get_encryptor():
    """
    Return the repo's Fernet encryptor, or None if ENCRYPTION_KEY is not set on
    this node. Encryption is best-effort: when unavailable we still persist the
    key id (and can re-fetch the secret from LiteLLM on demand), we just don't
    store the secret value at rest.
    """
    try:
        from key_encryption import get_encryption

        return get_encryption()
    except Exception as e:  # ValueError when ENCRYPTION_KEY missing/invalid
        logger.warning(
            "ENCRYPTION_KEY unavailable; gateway key value will not be stored at rest: %s",
            e,
        )
        return None


def _encrypt_key_value(key_value: Optional[str]) -> Optional[str]:
    if not key_value:
        return None
    enc = _get_encryptor()
    if not enc:
        return None
    try:
        return enc.encrypt_key(key_value)
    except Exception as e:
        logger.warning("Failed to encrypt gateway key value (storing id only): %s", e)
        return None


def _decrypt_key_value(encrypted: Optional[str]) -> Optional[str]:
    if not encrypted:
        return None
    enc = _get_encryptor()
    if not enc:
        return None
    try:
        return enc.decrypt_key(encrypted)
    except Exception as e:
        logger.warning("Failed to decrypt stored gateway key value: %s", e)
        return None


# org_id is the OrgManager id ("org_<uuid>", a STRING) — NOT the bare-UUID
# organizations.id (a different id space, JSON store vs Postgres). So persist into
# a dedicated string-keyed table, created on demand, decoupled from organizations.
_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS org_gateway_keys (
    org_id VARCHAR(255) PRIMARY KEY,
    litellm_key_id VARCHAR(255),
    litellm_key_encrypted TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


async def _read_stored_key(conn, org_id: str) -> Optional[Dict[str, Any]]:
    """Return the persisted org→key reference from org_gateway_keys (keyed by the
    string org_id, e.g. 'org_<uuid>'), or None. Self-heals the table so a fresh
    node degrades gracefully instead of erroring."""
    try:
        await conn.execute(_TABLE_DDL)
        row = await conn.fetchrow(
            "SELECT litellm_key_id, litellm_key_encrypted FROM org_gateway_keys WHERE org_id = $1",
            org_id,
        )
    except Exception as e:
        logger.warning("Could not read stored gateway key for org %s: %s", org_id, e)
        return None

    if not row or not row["litellm_key_id"]:
        return None

    return {
        "key_id": row["litellm_key_id"],
        "key": _decrypt_key_value(row["litellm_key_encrypted"]),
        "org_id": org_id,
    }


async def _persist_key(conn, org_id: str, key_id: str, key_value: Optional[str]) -> None:
    """Persist the org→key reference idempotently. Best-effort: a persistence
    failure must not break provisioning (the key already exists on the gateway
    and is discoverable by alias)."""
    encrypted = _encrypt_key_value(key_value)
    try:
        await conn.execute(_TABLE_DDL)
        await conn.execute(
            """
            INSERT INTO org_gateway_keys (org_id, litellm_key_id, litellm_key_encrypted, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (org_id) DO UPDATE SET
                litellm_key_id = EXCLUDED.litellm_key_id,
                litellm_key_encrypted = COALESCE(EXCLUDED.litellm_key_encrypted, org_gateway_keys.litellm_key_encrypted),
                updated_at = CURRENT_TIMESTAMP
            """,
            org_id,
            key_id,
            encrypted,
        )
    except Exception as e:
        logger.warning("Could not persist gateway key reference for org %s: %s", org_id, e)


async def _find_existing_key_by_alias(org_id: str, master_key: str, proxy_url: str) -> Optional[Dict[str, Any]]:
    """
    Fallback idempotency: ask the gateway for keys owned by user_id == org_id and
    match our alias. Covers the case where the org row lost its stored reference
    (e.g. restored DB) but the key still exists on the gateway.
    """
    alias = _key_alias(org_id)
    try:
        async with httpx.AsyncClient(timeout=_GATEWAY_TIMEOUT) as client:
            resp = await client.get(
                f"{proxy_url}/key/list",
                params={"user_id": org_id, "return_full_object": "true", "page_size": "100"},
                headers={"Authorization": f"Bearer {master_key}"},
            )
    except httpx.RequestError as e:
        logger.warning("Gateway unreachable during key/list for org %s: %s", org_id, e)
        return None

    if resp.status_code != 200:
        logger.warning("Gateway key/list returned %s for org %s", resp.status_code, org_id)
        return None

    data = resp.json()
    keys_list = data if isinstance(data, list) else data.get("keys", [])
    for k in keys_list:
        if k.get("key_alias") == alias:
            # /key/list does not return the raw secret; we only get the token id.
            return {
                "key_id": k.get("token", "") or k.get("token_id", ""),
                "key": None,  # secret not retrievable post-creation
                "org_id": org_id,
            }
    return None


async def provision_org_gateway_key(
    org_id: str,
    plan_code: Optional[str] = None,
    tier: Optional[str] = None,
    models: Optional[List[str]] = None,
    max_budget: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Idempotently ensure the org has exactly one LiteLLM gateway key and return it.

    Returns a dict {key_id, key, org_id, plan, created} on success, or None when
    the gateway is unreachable/misconfigured (failure-isolated — never raises into
    the subscribe flow).

    Idempotency order:
      1. Stored reference on the organizations row → return it.
      2. Gateway /key/list?user_id=org_id matched by alias → adopt + persist.
      3. Create a new key via /key/generate → persist.
    """
    if not org_id:
        logger.warning("provision_org_gateway_key called without org_id; skipping")
        return None

    proxy_url, master_key = await _resolve_gateway_creds()
    if not master_key:
        logger.warning(
            "LITELLM_MASTER_KEY not configured; skipping gateway key provisioning for org %s",
            org_id,
        )
        return None

    conn = None
    try:
        conn = await get_db_connection()

        # (1) Already provisioned? Return the stored reference.
        stored = await _read_stored_key(conn, org_id)
        if stored:
            logger.info("Org %s already has gateway key %s (stored)", org_id, stored["key_id"][:12])
            stored["plan"] = plan_code
            stored["created"] = False
            return stored

        # (2) Key may exist on the gateway without a stored reference — adopt it.
        existing = await _find_existing_key_by_alias(org_id, master_key, proxy_url)
        if existing and existing.get("key_id"):
            await _persist_key(conn, org_id, existing["key_id"], existing.get("key"))
            logger.info("Adopted existing gateway key %s for org %s", existing["key_id"][:12], org_id)
            existing["plan"] = plan_code
            existing["created"] = False
            return existing

        # (3) Create a fresh per-org key.
        payload: Dict[str, Any] = {
            "user_id": org_id,  # ← metering identity: charge_by=user_id keys Lago events to org
            "key_alias": _key_alias(org_id),
            "metadata": {
                "org_id": org_id,
                "plan": plan_code,
                "tier": tier,
                "provisioned_by": "ops-center",
            },
        }
        if max_budget is not None:
            payload["max_budget"] = max_budget
        if models:
            payload["models"] = models

        try:
            async with httpx.AsyncClient(timeout=_GATEWAY_TIMEOUT) as client:
                resp = await client.post(
                    f"{proxy_url}/key/generate",
                    json=payload,
                    headers={"Authorization": f"Bearer {master_key}"},
                )
        except httpx.RequestError as e:
            logger.warning("Gateway unreachable during key/generate for org %s: %s", org_id, e)
            return None

        if resp.status_code != 200:
            logger.warning(
                "Gateway key/generate failed for org %s: %s %s",
                org_id,
                resp.status_code,
                resp.text[:300],
            )
            return None

        data = resp.json()
        key_value = data.get("key")
        key_id = data.get("token_id") or data.get("token") or ""
        if not key_id and not key_value:
            logger.warning("Gateway key/generate returned no token for org %s", org_id)
            return None

        await _persist_key(conn, org_id, key_id, key_value)
        logger.info("Provisioned new gateway key %s for org %s (plan=%s)", key_id[:12], org_id, plan_code)
        return {
            "key_id": key_id,
            "key": key_value,
            "org_id": org_id,
            "plan": plan_code,
            "created": True,
        }

    except Exception as e:
        # Catch-all: provisioning is best-effort and must never raise into callers.
        logger.warning("Unexpected error provisioning gateway key for org %s: %s", org_id, e)
        return None
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass


async def update_org_gateway_key_budget(
    org_id: str,
    max_budget: Optional[float],
    plan_code: Optional[str] = None,
) -> bool:
    """Apply/refresh the budget on an org's EXISTING gateway key.

    provision_org_gateway_key is create-only idempotent — a key that already
    exists is returned untouched, so plan changes never updated budgets.
    This closes that gap via LiteLLM /key/update. max_budget=None is a no-op
    (unlimited stays unlimited); pass 0.0 to hard-block.

    Failure-isolated: returns False on any problem, never raises.
    """
    if not org_id or max_budget is None:
        return False
    proxy_url, master_key = await _resolve_gateway_creds()
    if not master_key:
        logger.warning("No gateway master key; cannot update budget for org %s", org_id)
        return False

    conn = None
    try:
        conn = await get_db_connection()
        stored = await _read_stored_key(conn, org_id)
    except Exception as e:
        logger.warning("Could not read stored key for budget update (org %s): %s", org_id, e)
        return False
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

    if not stored:
        return False
    # /key/update accepts the raw key value or the hashed token id.
    key_ref = stored.get("key") or stored.get("key_id")
    if not key_ref:
        return False

    payload: Dict[str, Any] = {"key": key_ref, "max_budget": float(max_budget)}
    if plan_code:
        payload["metadata"] = {"org_id": org_id, "plan": plan_code,
                               "provisioned_by": "ops-center"}
    try:
        async with httpx.AsyncClient(timeout=_GATEWAY_TIMEOUT) as client:
            resp = await client.post(
                f"{proxy_url}/key/update",
                json=payload,
                headers={"Authorization": f"Bearer {master_key}"},
            )
    except httpx.RequestError as e:
        logger.warning("Gateway unreachable during key/update for org %s: %s", org_id, e)
        return False
    if resp.status_code != 200:
        logger.warning(
            "Gateway key/update failed for org %s: %s %s",
            org_id, resp.status_code, resp.text[:200],
        )
        return False
    logger.info("Set max_budget=%.2f on gateway key for org %s (plan=%s)",
                max_budget, org_id, plan_code)
    return True


# ===========================================================================
# Endpoint — multi-tenant apps fetch the right gateway key for their org.
# Authed; provisions on demand if missing (idempotent).
# ===========================================================================

router = APIRouter(prefix="/api/v1/org", tags=["Org Gateway Key"])


def _user_is_org_member_admin(user: Dict[str, Any]) -> bool:
    """Org owner/admin (or system admin) may read the org's gateway key. The
    key is an org-level billing/metering secret, so members are excluded."""
    role = user.get("role", "")
    roles = user.get("roles", []) or []
    if role in ("admin", "system_admin") or "admin" in roles or "system_admin" in roles:
        return True
    org_role = (user.get("org_role") or "").lower()
    return org_role in ("owner", "admin")


@router.get("/gateway-key")
async def get_org_gateway_key(
    request: Request,
    user: Dict[str, Any] = Depends(require_authenticated_user),
):
    """
    Return the caller's organization gateway key (the per-org LiteLLM virtual
    key carrying its budget + model allow-list + metering identity).

    - Scoped to the caller's active org (from session); never accepts an org_id
      from the client, so one tenant can't fetch another's key.
    - Org owner/admin (or system admin) only.
    - Provisions on demand if missing (idempotent).
    """
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="No active organization for this user")

    if not _user_is_org_member_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Organization owner/admin access required to read the gateway key",
        )

    # Resolve the org's current plan so on-demand provisioning carries it.
    plan_code = None
    try:
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT plan_tier FROM organizations WHERE id::text = $1", org_id
            )
            if row:
                plan_code = row["plan_tier"]
        finally:
            await conn.close()
    except Exception as e:
        logger.debug("Could not resolve plan_tier for org %s: %s", org_id, e)

    result = await provision_org_gateway_key(org_id=org_id, plan_code=plan_code)
    if not result:
        # Gateway unreachable / not configured — surface as 503 so callers retry.
        raise HTTPException(
            status_code=503,
            detail="Gateway key is temporarily unavailable. Please retry shortly.",
        )

    gateway_url, _ = await _resolve_gateway_creds()
    return {
        "org_id": org_id,
        "key_id": result.get("key_id"),
        # `key` (the raw sk-...) is present on fresh creation or when decryptable
        # from storage; null when the value isn't retrievable (key already exists
        # on the gateway and the secret was not stored at rest).
        "key": result.get("key"),
        "plan": result.get("plan"),
        "gateway_url": gateway_url,
    }
