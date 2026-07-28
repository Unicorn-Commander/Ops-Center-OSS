"""
Default-deny Authentication Middleware
======================================

Companion to the CSRF middleware. Gates EVERY `/api/*` request that is not on an
explicit public allowlist, requiring a valid session — the same check used by
`require_authenticated_user` (session_token cookie -> Redis).

WHY (2026-06-08 audit): the console protected endpoints only via per-endpoint
`Depends(require_*)`. Routers that forgot the dependency were silently public — 110+
endpoints leaked real data unauthenticated (analytics/revenue, audit logs, system/KC,
permissions, ...). This middleware makes "forgot the dependency" fail **closed**.

WHY IT'S SAFE for logged-in users: the frontend sends `credentials:'include'` on every
fetch, so authenticated browser traffic always carries the session_token cookie and
passes untouched. Only *unauthenticated* access is gated. The allowlist therefore only
needs to cover:
  - pre-login public surfaces (landing, login/oauth handshake, branding, public pricing)
  - machine-to-machine callers that authenticate with their OWN credentials, not a
    session cookie (federation/compute/inference/uuda/a2a, llm API-key, signed webhooks)

Endpoints that live UNDER an allowlisted m2m prefix but are really admin dashboards
(e.g. /api/v1/llm/usage) are protected separately with per-endpoint `require_admin_user`.

KILL SWITCH: set `AUTH_MIDDLEWARE_ENABLED=false` and recreate the container to disable.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Exact public paths (full-path match, no auth required)
PUBLIC_EXACT = {
    "/api/v1/my-apps/marketplace",    # public app marketplace (pre-login browse)
    "/api/v1/auth/csrf-token",
    "/api/v1/auth/password-policy",
    "/api/v1/auth/validate-key",      # m2m API-key validation
    "/api/v1/auth/session",           # bootstrap: "am I logged in?" check (handler returns own auth state)
    "/api/v1/branding/config",
    "/api/v1/deployment/config",      # bootstrap: deployment shell config (urls/features/branding, no secrets) — app needs it PRE-AUTH to render + redirect to login; was public before the auth middleware
    "/api/v1/system/status",          # bootstrap health probe — handler uses get_current_user_optional ("works with or without auth" by design); App.jsx gates the WHOLE admin render on it returning 200, so gating it shows "Connection Error" instead of the login page. Sensitive sibling /system/* paths stay gated (exact-match only).
    "/api/v1/billing/provider-config",  # public Stripe publishable key + provider name
    "/api/v1/billing/plans",
    "/api/v1/subscriptions/plans",
    "/api/v1/billing/events",         # m2m agent-key metering INGEST (POST, bare path only;
                                      # the GET /events/summary|by-property|markup-revenue
                                      # dashboards are NOT exact matches -> stay session-gated)
    "/api/v1/website-monitor/public-status",  # /status page data — handler is sanitized for
                                      # anonymous use (name/url/status/uptime only); the rest
                                      # of /website-monitor/* stays session-gated
}

# Public path PREFIXES (startswith match)
PUBLIC_PREFIXES = (
    # --- auth handshake (login / logout / oauth callback) ---
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/callback",
    # --- truly public surfaces ---
    "/api/v1/public/",
    "/api/v1/branding/",
    "/api/v1/landing/",
    "/api/v1/pricing/",               # public pricing calc + packages
    "/api/v1/billing/webhooks/",      # Stripe/Lago signed webhooks
    "/api/v1/analytics/web-vitals",   # high-frequency public web-vitals ingest
    "/api/v1/tier-check/",
    # --- machine-to-machine (own key/agent auth, no session cookie) ---
    "/api/v1/federation/",
    "/api/v1/compute/",
    "/api/v1/inference/",
    "/api/v1/uuda/",
    "/api/v1/entitlements",  # token-authed cross-app entitlement endpoint (verifies its own KC Bearer)
    "/api/v1/metered/",               # metered compute: /report is service-key m2m;
                                      # /embeddings & /rerank still enforce session via
                                      # their own require_authenticated_user dependency
    "/api/v1/internal/llm/",          # gateway local-pricing preflight: service-key (X-Internal-Key) m2m
    "/api/v1/llm/",                   # API-key (Brigade/Open-WebUI/Bolt). Admin subpaths
                                      # (usage/providers/costs/routing/...) get their own
                                      # per-endpoint require_admin_user.
    "/api/llmcall",                   # Bolt.diy m2m proxy
    "/api/github-template",           # Bolt.diy m2m
    "/api/v1/webhooks/",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Default-deny session gate for /api/* routes."""

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    @staticmethod
    def _is_public(path: str, method: str) -> bool:
        if method == "OPTIONS":               # CORS preflight
            return True
        # Frontend SPA, static assets, OAuth callbacks (/auth/*), /.well-known, /docs,
        # /openapi.json, /a2a (m2m) — anything not under /api/ is not session-gated here.
        if not path.startswith("/api/"):
            return True
        if path.endswith("/health"):          # service health checks
            return True
        if path in PUBLIC_EXACT:
            return True
        return any(path.startswith(p) for p in PUBLIC_PREFIXES)

    async def dispatch(self, request, call_next):
        if not self.enabled:
            return await call_next(request)

        if self._is_public(request.url.path, request.method):
            return await call_next(request)

        # Default-deny: require a valid session (identical check to require_authenticated_user).
        # NB: return a response rather than raise — raising inside BaseHTTPMiddleware bypasses
        # FastAPI's exception handlers and surfaces as a 500 (the CSRF middleware's known quirk).
        from auth_dependencies import require_authenticated_user
        try:
            await require_authenticated_user(request)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:  # infra error (e.g. Redis blip) -> fail closed, distinguishable
            logger.error(f"[auth-mw] auth check error for {request.url.path}: {e}")
            return JSONResponse(status_code=503, content={"detail": "Authentication temporarily unavailable"})

        return await call_next(request)


def create_auth_middleware(enabled: bool = True):
    """Factory mirroring create_csrf_protection — returns a callable for app.add_middleware."""
    return lambda app: AuthenticationMiddleware(app=app, enabled=enabled)
