"""
Token-accepting entitlement endpoint for cross-app gating.

Sister apps (Meeting-Ops, Customer-Ops, Project-Ops, Brand-Ops, ...) hold a Keycloak
access token but NOT an Ops-Center session cookie. This endpoint verifies a Keycloak
Bearer token (RS256 via JWKS) and returns the caller's org entitlements — the single
source of truth being Ops-Center's tier_features ∪ org_features (via get_combined_features).

Apps call this post-auth with the user's bearer token and allow access if their feature_key
is present. Fail-closed: no token / bad token → 401; no resolvable org → empty entitlements.

    GET /api/v1/entitlements                       -> {org_id, tier, entitlements:[...]}
    GET /api/v1/entitlements?feature_key=foo_access -> {... , authorized: bool}
"""
import logging
import os
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException, Request
from jwt import PyJWKClient

from my_apps_api import get_combined_features, get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entitlements", tags=["Entitlements"])

# uchub realm issuers across nodes (prod + dogfood). A token's `iss` must be in this set,
# and the JWKS is fetched from the matched issuer. Add more via KEYCLOAK_EXTRA_ISSUERS (csv).
_DEFAULT_ISSUERS = [
    "https://auth.unicorncommander.ai/realms/uchub",
    "https://auth.magicunicorn.dev/realms/uchub",
]
ALLOWED_ISSUERS = set(_DEFAULT_ISSUERS) | {
    i.strip() for i in os.getenv("KEYCLOAK_EXTRA_ISSUERS", "").split(",") if i.strip()
}

# The realm hosts (auth.*.dev / .ai) sit behind Cloudflare, which 403s bare Python
# (urllib) User-Agents via bot-management — so the JWKS fetch must send a browser-like UA
# (same fix already in the sister apps' auth clients). Overridable via env.
_JWKS_UA = os.getenv(
    "ENTITLEMENTS_JWKS_UA",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)

_jwks_clients: dict = {}


def _jwks_for(issuer: str) -> PyJWKClient:
    client = _jwks_clients.get(issuer)
    if client is None:
        client = PyJWKClient(
            f"{issuer}/protocol/openid-connect/certs",
            cache_keys=True, lifespan=3600, timeout=10,
            headers={"User-Agent": _JWKS_UA},
        )
        _jwks_clients[issuer] = client
    return client


def _verify_bearer(token: str) -> dict:
    """Verify a Keycloak access token: RS256 signature (JWKS) + allowlisted iss + exp.

    Returns the verified claims. Raises HTTPException(401) on any failure. We do NOT pin
    `aud` — any valid uchub user token may ask for ITS OWN org entitlements (the org is
    resolved from the token's `sub`, so a caller can only ever read their own grants).
    """
    try:
        issuer = jwt.decode(token, options={"verify_signature": False}).get("iss")
    except Exception as exc:
        logger.warning("entitlements: malformed token (%s)", exc)
        raise HTTPException(status_code=401, detail="Malformed token")
    if issuer not in ALLOWED_ISSUERS:
        logger.warning("entitlements: untrusted issuer %r", issuer)
        raise HTTPException(status_code=401, detail="Untrusted token issuer")
    try:
        signing_key = _jwks_for(issuer).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": ["exp", "iss"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        logger.warning("entitlements: token verification failed (iss=%s): %s", issuer, exc)
        raise HTTPException(status_code=401, detail=f"Token verification failed: {exc}")


async def _resolve_membership(claims: dict, conn, requested_org_id: Optional[str] = None):
    """Resolve the caller's active org + org-role from their Keycloak sub.

    Returns (org_id, org_role) or (None, None). The org_role is the Ops-Center
    organization membership role (owner/admin/billing_admin/member) — apps can seed their
    own in-app role from it (e.g. owner→ADMIN, else→STAFF) and refine in-app.

    Active-workspace support: if `requested_org_id` is given (the active workspace the app
    resolved from the bearer), we return it ONLY after verifying the caller is a member —
    so a per-user token can never read another org's grants (no IDOR). With no
    requested_org_id we fall back to the user's primary org."""
    sub = claims.get("sub")
    if not sub:
        return None, None
    if requested_org_id:
        row = await conn.fetchrow(
            """
            SELECT om.org_id, om.role
            FROM users u
            JOIN organization_members om ON u.id::text = om.user_id
            WHERE u.zitadel_id = $1 AND om.org_id::text = $2
            LIMIT 1
            """,
            str(sub), str(requested_org_id),
        )
        if not row:
            raise HTTPException(status_code=403, detail="Not a member of the requested org")
        return str(row["org_id"]), row["role"]
    row = await conn.fetchrow(
        """
        SELECT om.org_id, om.role
        FROM users u
        JOIN organization_members om ON u.id::text = om.user_id
        WHERE u.zitadel_id = $1
        LIMIT 1
        """,
        str(sub),
    )
    return (str(row["org_id"]), row["role"]) if row else (None, None)


@router.get("")
@router.get("/")
async def get_entitlements(
    request: Request,
    feature_key: Optional[str] = None,
    org_id: Optional[str] = None,
):
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    claims = _verify_bearer(token)

    conn = await get_db_connection()
    try:
        resolved_org, org_role = await _resolve_membership(claims, conn, requested_org_id=org_id)
        if not resolved_org:
            result = {"org_id": None, "tier": None, "role": None, "entitlements": []}
        else:
            tier_row = await conn.fetchrow(
                "SELECT plan_tier FROM organizations WHERE id = $1", resolved_org
            )
            tier = (tier_row["plan_tier"] if tier_row and tier_row["plan_tier"] else "free")
            try:
                features = await get_combined_features(tier, resolved_org, conn)
            except HTTPException:
                # Unknown/invalid tier → no entitlements (fail-closed), don't 400 the caller.
                features = set()
            result = {
                "org_id": resolved_org,
                "tier": tier,
                "role": org_role,
                "entitlements": sorted(features),
            }
    finally:
        await conn.close()

    if feature_key:
        result["authorized"] = feature_key in set(result["entitlements"])
    return result
