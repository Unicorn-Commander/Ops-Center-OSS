"""
Credit Deduction Middleware
============================

Automatic credit deduction middleware for LiteLLM API requests.

This middleware intercepts all /api/v1/llm/* requests and:
1. Checks org/individual credits BEFORE processing request
2. Returns 402 Payment Required if insufficient credits
3. Processes the LLM request
4. Deducts exact credits AFTER response based on actual token usage
5. Adds credit usage headers to responses
6. Handles BYOK passthrough (no credit deduction)
7. Implements fail-open design (never blocks users due to billing failures)

Headers added to responses:
- X-Credits-Used: Credits deducted for this request
- X-Credits-Remaining: Credits remaining in account
- X-Org-Credits: true if org credits used, false if individual
- X-BYOK: true if BYOK key used (no credits charged)

Author: Backend Integration Teamlead
Date: November 15, 2025
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from datetime import datetime
from typing import Optional, Tuple
import re
import json
import os
import sys

# Add /app to path for imports
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from org_credit_integration import get_org_credit_integration
from litellm_credit_system import CreditSystem

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURABLE BILLING SETTINGS
# =============================================================================
# These can be customized per deployment via environment variables.
# Personal servers or internal company servers can disable billing entirely
# by setting BILLING_ENABLED=false or by listing all tiers in CREDIT_EXEMPT_TIERS.

# Tiers that are exempt from credit charges (comma-separated)
# Default includes common "unlimited" tier names. Customize for your deployment.
# Set to "*" to exempt ALL tiers (effectively disabling billing)
CREDIT_EXEMPT_TIERS_ENV = os.getenv("CREDIT_EXEMPT_TIERS", "free,vip_founder,vip,founder,admin,unlimited,internal")
# Env-derived defaults (the fallback floor). The EFFECTIVE values are DB-first
# (platform_settings), so a change made in the admin GUI survives a container
# restart instead of resetting to whatever the env baked in at deploy time.
CREDIT_EXEMPT_TIERS = set(t.strip() for t in CREDIT_EXEMPT_TIERS_ENV.split(",") if t.strip())
BILLING_ENABLED = os.getenv("BILLING_ENABLED", "true").lower() == "true"

# Runtime billing config, refreshed from platform_settings (DB-first) by the
# middleware on each request (cached). None = not yet loaded → use env defaults.
import time as _time
_billing_cfg = {"ts": 0.0, "enabled": None, "exempt": None}
_BILLING_CFG_TTL = 30.0


async def refresh_billing_config(db_pool=None) -> None:
    """Refresh BILLING_ENABLED / CREDIT_EXEMPT_TIERS from platform_settings.

    DB-first so the admin GUI's billing posture persists across restarts; falls
    back to the env defaults. Cached (30s); never raises.
    """
    now = _time.monotonic()
    if _billing_cfg["enabled"] is not None and (now - _billing_cfg["ts"]) < _BILLING_CFG_TTL:
        return
    enabled, exempt = None, None
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT key, value FROM platform_settings WHERE key = ANY($1)",
                    ["BILLING_ENABLED", "CREDIT_EXEMPT_TIERS"],
                )
            kv = {r["key"]: r["value"] for r in rows}
            if kv.get("BILLING_ENABLED") is not None:
                enabled = str(kv["BILLING_ENABLED"]).strip().lower() == "true"
            if kv.get("CREDIT_EXEMPT_TIERS"):
                exempt = set(t.strip() for t in str(kv["CREDIT_EXEMPT_TIERS"]).split(",") if t.strip())
        except Exception as e:
            logger.debug(f"Billing config DB refresh failed (using env/defaults): {e}")
    _billing_cfg["enabled"] = enabled if enabled is not None else BILLING_ENABLED
    _billing_cfg["exempt"] = exempt if exempt is not None else CREDIT_EXEMPT_TIERS
    _billing_cfg["ts"] = now


def is_credit_exempt(user_tier: str) -> bool:
    """Check if a user tier is exempt from credit charges.

    Uses the DB-backed runtime config when loaded (refresh_billing_config),
    else falls back to the env defaults (cold start / no DB) = prior behavior.
    """
    enabled = _billing_cfg["enabled"]
    exempt = _billing_cfg["exempt"]
    if enabled is None:
        enabled = BILLING_ENABLED
    if exempt is None:
        exempt = CREDIT_EXEMPT_TIERS
    if not enabled:
        return True
    if "*" in exempt:
        return True
    return user_tier in exempt


class CreditDeductionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically deduct credits for LLM API requests.

    Integrates with:
    - Organization credit pools (org_credit_integration.py)
    - Individual credit system (litellm_credit_system.py)
    - BYOK manager (byok_manager.py)

    Design Principles:
    - Check credits BEFORE processing (prevent wasteful API calls)
    - Deduct exact credits AFTER response (based on actual token usage)
    - Fail-open (billing failures should NOT block users)
    - Atomic transactions (deduction + attribution in single operation)
    - BYOK passthrough (no credits charged when using own keys)
    """

    # Endpoints that require credit deduction (regex patterns)
    CREDIT_ENDPOINTS = [
        r"^/api/v1/llm/chat/completions$",
        r"^/api/v1/llm/completions$",
        r"^/api/v1/llm/image/generations$",
        r"^/api/v1/llm/embeddings$"
    ]

    # Endpoints that don't consume credits
    EXCLUDED_ENDPOINTS = [
        r"^/api/v1/llm/models",      # Model list
        r"^/api/v1/llm/health",      # Health check
        r"^/api/v1/llm/usage",       # Usage stats
        r"^/api/v1/admin/",          # Admin endpoints
        r"^/api/v1/billing/",        # Billing endpoints
        r"^/api/v1/credits/",        # Credit management
        r"^/api/v1/usage/"           # Usage tracking
    ]

    # Estimated tokens for pre-check (average conversation)
    ESTIMATED_TOKENS = 1500
    # Estimated cost per 1K tokens (conservative)
    ESTIMATED_COST_PER_1K = 0.006  # $0.006 = 6 credits per 1K tokens

    def __init__(self, app):
        super().__init__(app)
        self.initialized = False
        self.credit_system = None
        self.org_integration = None
        self.byok_manager = None

    async def _ensure_initialized(self, request: Request):
        """Lazy initialization of credit systems"""
        if not self.initialized:
            try:
                # Get db_pool and redis_client from app.state
                db_pool = request.app.state.db_pool
                redis_client = request.app.state.redis_client

                # Initialize credit system with required dependencies
                self.credit_system = CreditSystem(db_pool, redis_client)
                self.org_integration = get_org_credit_integration()
                self.byok_manager = request.app.state.byok_manager
                self.initialized = True
                logger.info("CreditDeductionMiddleware initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize credit systems: {e}", exc_info=True)
                # Mark as initialized but disabled to prevent repeated init attempts
                self.initialized = True
                self.credit_system = None
                self.org_integration = None
                logger.warning("Credit deduction DISABLED due to initialization failure")

    async def _should_deduct_credits(self, path: str) -> bool:
        """Check if endpoint requires credit deduction"""
        # Check exclusions first
        for pattern in self.EXCLUDED_ENDPOINTS:
            if re.match(pattern, path):
                return False

        # Check if matches credit-consuming patterns
        for pattern in self.CREDIT_ENDPOINTS:
            if re.match(pattern, path):
                return True

        return False

    async def _get_user_from_session(self, request: Request) -> Optional[dict]:
        """Extract user data from session cookie OR service key OR API key + X-User-ID header"""
        try:
            # Check for service key pattern (for bolt.diy, presenton, brigade, etc.)
            x_user_id = request.headers.get('X-User-ID')
            auth_header = request.headers.get('Authorization', '')

            # Check for user API key (uc_<hex>) - for remote API access
            if auth_header.startswith('Bearer uc_'):
                token = auth_header[7:]  # Remove "Bearer "
                try:
                    from api_key_manager import get_api_key_manager
                    manager = get_api_key_manager()
                    user_info = await manager.validate_api_key(token)

                    if user_info:
                        uid = user_info['user_id']
                        # Resolve the key OWNER's REAL tier — do NOT blanket-exempt
                        # direct-API callers (that = we eat the cost). The owner's
                        # actual tier decides exempt-vs-metered: internal/founder
                        # owners (e.g. admin@example.com → vip_founder) stay
                        # exempt naturally; a real paid customer gets billed.
                        # get_user_tier already fails safe to "free" (exempt), so a
                        # lookup error never wrongly charges (fail-open).
                        try:
                            owner_tier = await self.credit_system.get_user_tier(uid)
                        except Exception as tier_exc:
                            logger.warning(
                                f"uc_ key tier lookup failed for {uid}; exempting (fail-open): {tier_exc}"
                            )
                            owner_tier = "free"
                        logger.info(f"API key authenticated user: {uid} (tier={owner_tier})")
                        return {
                            "user_id": uid,
                            "subscription_tier": owner_tier,
                        }
                    else:
                        logger.warning(f"Invalid API key in credit middleware")
                        return None
                except Exception as e:
                    logger.error(f"API key validation error in middleware: {e}")
                    return None

            if auth_header.startswith('Bearer sk-'):
                # Service key authentication - extract service name
                token = auth_header[7:]  # Remove "Bearer "

                # Known service keys mapping
                service_keys = {
                    'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
                    'sk-presenton-service-key-2025': 'presenton-service',
                    'sk-brigade-service-key-2025': 'brigade-service',
                    'sk-centerdeep-service-key-REDACTED': 'centerdeep-service',
                    'sk-partnerpulse-service-key-2025': 'partnerpulse-service',
                    'sk-open-webui-service-key-2026': 'open-webui-service',
                    'sk-colonel-service-key-2026': 'colonel-service',
                    'sk-majiks-service-key-2025': 'majiks-service'
                }

                # Map service names to organization UUIDs (matches litellm_api.py)
                service_org_ids = {
                    'bolt-diy-service': '3766e9ee-7cc1-472f-92ae-afec687f0d74',
                    'presenton-service': '13587747-66e6-43df-b21d-4411c7373465',
                    'brigade-service': 'e9b40f6b-b683-4bcf-b462-9fd526cfbb37',
                    'centerdeep-service': '91d3b68e-e4c4-457e-80ce-de6997243c34',
                    'partnerpulse-service': '8f5bf9a9-2e7c-4465-93d8-97f18bdac098',
                    'open-webui-service': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
                    'colonel-service': 'e9b40f6b-b683-4bcf-b462-9fd526cfbb37',
                    'majiks-service': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
                }

                # Internal services exempt from billing
                # All platform-internal service accounts run on the org's own
                # 'internal' tier when called without an X-User-ID context;
                # user-context calls (X-User-ID set) bill the user's tier.
                internal_services = {
                    'colonel-service',
                    'brigade-service',
                    'majiks-service',
                    'centerdeep-service',
                    'open-webui-service',
                    'bolt-diy-service',
                    'presenton-service',
                    'partnerpulse-service',
                }

                service_name = service_keys.get(token)
                if service_name:
                    tier = "internal" if service_name in internal_services else "professional"
                    if x_user_id:
                        # Service key with user context - return user data.
                        # _app carries the calling UC app so the per-(app,model)
                        # included-vs-metered policy can apply (see dispatch).
                        logger.info(f"Service key request with user context: {x_user_id}")
                        return {
                            "user_id": x_user_id,
                            "subscription_tier": tier,
                            "_app": service_name,
                        }
                    else:
                        # Service key without user context - use org-prefixed ID for billing
                        service_org_id = service_org_ids.get(service_name)
                        if service_org_id:
                            org_prefixed_id = f"org_{service_org_id}"
                            logger.info(f"Service key request using org credits: {org_prefixed_id}")
                            return {
                                "user_id": org_prefixed_id,
                                "subscription_tier": tier,
                                "is_service_account": True,
                                "_app": service_name,
                            }
                        else:
                            logger.error(f"Service org ID not configured for: {service_name}")
                            return None
                else:
                    # Unknown service key - let endpoint handle authentication
                    logger.warning(f"Unknown service key in credit middleware: {token[:20]}...")
                    return None

            # Otherwise, try to get user from session cookie
            from redis_session import RedisSessionManager

            session_token = request.cookies.get("session_token")
            if not session_token:
                return None

            redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            sessions = RedisSessionManager(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
            user_data = sessions.get(session_token)

            if not user_data:
                return None

            # Ensure user_id field exists (Keycloak compatibility)
            if "user_id" not in user_data:
                user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

            return user_data

        except Exception as e:
            logger.error(f"Error extracting user from session: {e}")
            return None

    async def _check_byok_enabled(self, user_id: str, model: str = None) -> Tuple[bool, str]:
        """
        Check if user has BYOK (Bring Your Own Key) enabled for this model.

        Returns:
            (is_byok: bool, provider: str)
        """
        try:
            # Reuse the app-state singleton initialized at startup
            byok_manager = self.byok_manager
            if byok_manager is None:
                logger.debug("BYOK manager not yet initialized; skipping BYOK check")
                return False, None

            # Check if user has any BYOK keys configured
            user_providers = await byok_manager.get_user_providers(user_id)

            if not user_providers:
                return False, None

            # If model specified, check if user has key for that provider
            if model:
                # Extract provider from model name (e.g., "openai/gpt-4" -> "openai")
                provider = model.split('/')[0] if '/' in model else None

                if provider and provider in user_providers:
                    logger.info(f"BYOK enabled for user {user_id}, provider {provider}")
                    return True, provider

            # User has BYOK but not for this specific model
            return False, None

        except Exception as e:
            logger.error(f"Error checking BYOK status: {e}", exc_info=True)
            # Fail open: assume no BYOK on error
            return False, None

    async def _estimate_credits_needed(self, request: Request) -> float:
        """
        Estimate credit cost for pre-check.

        Uses conservative estimate based on:
        - Average conversation: ~1500 tokens
        - Average cost: ~$0.006 per 1K tokens = 6 credits per 1K tokens
        - Estimated cost: 1500 * 0.006 = 9 credits

        For image generation, estimates based on model and size.
        """
        path = request.url.path

        # Image generation has different pricing
        if "image/generations" in path:
            # Conservative estimate for images
            # DALL-E 3 1024x1024 standard = 48 credits
            return 48.0

        # Chat/completions/embeddings
        # Use average tokens * cost per 1K
        estimated_tokens = self.ESTIMATED_TOKENS
        cost_per_token = self.ESTIMATED_COST_PER_1K / 1000.0
        estimated_cost = estimated_tokens * cost_per_token

        return estimated_cost

    async def _extract_actual_cost(self, request: Request, response: Response) -> Tuple[float, int, str]:
        """
        Extract actual credit cost from response.

        Returns:
            (credits_used: float, tokens_used: int, provider: str)
            Returns None if streaming response (handled by litellm_api.py)
        """
        try:
            # CRITICAL: Check if this is a streaming response BEFORE consuming body
            # StreamingResponse uses media_type text/event-stream
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                logger.debug("Detected streaming response (text/event-stream), skipping middleware credit extraction")
                return None

            # Try to read response body (only for non-streaming responses)
            body = b""
            # FIX: Convert to async generator properly
            if hasattr(response.body_iterator, '__aiter__'):
                # Already async iterator
                async for chunk in response.body_iterator:
                    body += chunk
            else:
                # Regular iterator - convert to list first
                body_parts = list(response.body_iterator)
                for chunk in body_parts:
                    body += chunk

            # Parse JSON response
            try:
                response_data = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Non-JSON response - skip middleware credit tracking
                logger.debug("Non-JSON response detected, skipping middleware credit extraction")
                return None

            # The endpoint handler is the authoritative debit point and stamps
            # the response when it has already settled credits:
            #   - credits_settled: chat/completions + image/generations already
            #     deducted org/individual credits and metered usage. Re-debiting
            #     here would DOUBLE-CHARGE the same call.
            #   - gateway_metered: federation-served — billed by the PUBLISHER's
            #     gateway under the org's per-org key (one Lago ai_api_call event).
            # (Endpoints with no handler-side debit — e.g. embeddings — omit both
            #  flags, so the middleware remains their sole billing path.)
            _meta = response_data.get("_metadata") or {}
            if _meta.get("credits_settled") or _meta.get("gateway_metered"):
                logger.debug(
                    "Response already settled by handler (credits_settled=%s, "
                    "gateway_metered=%s) — skipping middleware credit extraction",
                    _meta.get("credits_settled"), _meta.get("gateway_metered"),
                )
                # The body iterator was consumed; restore it for the client.
                async def _restored_body():
                    yield body
                response.body_iterator = _restored_body()
                return None

            # Extract token usage
            tokens_used = 0
            if "usage" in response_data:
                tokens_used = response_data["usage"].get("total_tokens", 0)

            # Extract cost (if available from litellm_api.py)
            credits_used = 0.0
            if "cost" in response_data:
                credits_used = float(response_data["cost"])
            elif tokens_used > 0:
                # Fallback: estimate from tokens
                credits_used = tokens_used * (self.ESTIMATED_COST_PER_1K / 1000.0)

            # Extract provider
            provider = response_data.get("model", "unknown")
            if "/" in provider:
                provider = provider.split("/")[0]

            # FIX: Recreate response with async generator
            async def body_generator():
                yield body
            response.body_iterator = body_generator()

            return credits_used, tokens_used, provider

        except Exception as e:
            logger.error(f"Error extracting cost from response: {e}", exc_info=True)
            # FIX: Add await for async function
            return await self._estimate_credits_needed(request), 0, "unknown"

    async def _check_sufficient_credits(
        self,
        user_id: str,
        credits_needed: float,
        user_tier: str,
        request_state: Optional[dict] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if user has sufficient credits (org or individual).

        Returns:
            (has_credits: bool, org_id: Optional[str], message: str)
        """
        try:
            # Skip for free tier
            if user_tier == 'free':
                return True, None, "Free tier - no credit check"

            # Try organizational billing first
            has_org_credits, org_id, message = await self.org_integration.has_sufficient_org_credits(
                user_id=user_id,
                credits_needed=credits_needed,
                request_state=request_state
            )

            if org_id:
                # User belongs to organization
                if not has_org_credits:
                    return False, org_id, message
                return True, org_id, "Sufficient org credits"

            # Fallback to individual credits
            current_balance = await self.credit_system.get_user_credits(user_id)

            if current_balance < credits_needed:
                return False, None, f"Insufficient credits. Balance: {current_balance:.6f}, needed: {credits_needed:.6f}"

            # Check monthly cap
            within_cap = await self.credit_system.check_monthly_cap(user_id, credits_needed)
            if not within_cap:
                return False, None, "Monthly spending cap exceeded"

            return True, None, "Sufficient individual credits"

        except Exception as e:
            logger.error(f"Error checking credits: {e}", exc_info=True)
            # Fail open: allow request on error
            return True, None, f"Credit check failed (allowing request): {str(e)}"

    async def _deduct_credits(
        self,
        user_id: str,
        credits_used: float,
        tokens_used: int,
        provider: str,
        model: str,
        org_id: Optional[str] = None,
        request_state: Optional[dict] = None
    ) -> Tuple[bool, float]:
        """
        Deduct credits after successful request.

        Returns:
            (success: bool, remaining_credits: float)
        """
        try:
            if org_id:
                # Deduct from organization credits
                success, used_org_id, remaining = await self.org_integration.deduct_org_credits(
                    user_id=user_id,
                    credits_used=credits_used,
                    service_name=provider,
                    provider=provider,
                    model=model,
                    tokens_used=tokens_used,
                    power_level="balanced",  # Default
                    task_type="llm_inference",
                    request_id=None,
                    org_id=org_id,
                    request_state=request_state
                )

                if success:
                    # Convert milicredits to credits
                    remaining_credits = remaining / 1000.0 if remaining else 0.0
                    logger.info(f"Deducted {credits_used:.6f} credits from org {org_id} for user {user_id}")
                    return True, remaining_credits
                else:
                    logger.error(f"Failed to deduct org credits for user {user_id}")
                    return False, 0.0

            else:
                # Deduct from individual credits
                new_balance, transaction_id = await self.credit_system.debit_credits(
                    user_id=user_id,
                    amount=credits_used,
                    metadata={
                        "description": f"LLM API call - {model} ({tokens_used} tokens)",
                        "provider": provider,
                        "model": model,
                        "tokens_used": tokens_used
                    }
                )

                logger.info(f"Deducted {credits_used:.6f} credits from user {user_id}. New balance: {new_balance:.6f}")
                return True, new_balance

        except Exception as e:
            logger.error(f"Error deducting credits: {e}", exc_info=True)
            # Fail open: don't block user if deduction fails
            return False, 0.0

    async def dispatch(self, request: Request, call_next):
        """
        Main middleware logic.

        Flow:
        1. Check if endpoint requires credit deduction
        2. Get user from session
        3. Check if BYOK enabled (skip credit deduction if true)
        4. Estimate credits needed
        5. Check sufficient credits BEFORE request
        6. If insufficient, return 402 Payment Required
        7. Process request
        8. Extract actual cost from response
        9. Deduct exact credits
        10. Add credit headers to response
        """
        path = request.url.path

        # Check if we should deduct credits for this endpoint
        should_deduct = await self._should_deduct_credits(path)

        if not should_deduct:
            # Not a credit-consuming endpoint, pass through
            return await call_next(request)

        # Initialize credit systems if needed
        await self._ensure_initialized(request)

        # Refresh DB-backed billing posture (BILLING_ENABLED / CREDIT_EXEMPT_TIERS)
        # so admin-GUI changes survive restarts. Cached 30s; fail-soft to env.
        await refresh_billing_config(getattr(request.app.state, "db_pool", None))

        # If credit system failed to initialize, pass through without credit checks
        if self.credit_system is None:
            logger.warning("Credit system disabled - passing request through without credit deduction")
            return await call_next(request)

        # Get user from session
        user = await self._get_user_from_session(request)

        if not user:
            # No user session - return 401
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Authentication required. Please login to access this endpoint."
                }
            )

        user_id = user.get("user_id")
        user_tier = user.get("subscription_tier", "trial")

        # Try to get model from request body (for BYOK check)
        model = None
        try:
            if request.method == "POST":
                body = await request.body()
                body_data = json.loads(body.decode())
                model = body_data.get("model")
                # Re-set body for downstream processing
                request._body = body
        except:
            pass

        # Check if billing is disabled globally or user is in credit-exempt tier
        # Configurable via BILLING_ENABLED and CREDIT_EXEMPT_TIERS env vars
        if is_credit_exempt(user_tier):
            exempt_reason = "billing disabled" if not BILLING_ENABLED else f"tier '{user_tier}' is credit-exempt"
            logger.info(f"Credit exempt for user {user_id} - {exempt_reason}")

            response = await call_next(request)

            # Add exempt tier headers
            response.headers["X-Credit-Exempt"] = "true"
            response.headers["X-Credits-Used"] = "0.0"
            response.headers["X-Credits-Remaining"] = "unlimited"

            return response

        # Per-(app, model) policy: a non-exempt customer using a UC app (service
        # key + X-User-ID) may have SOME inference bundled into their app
        # subscription (e.g. Parakeet STT, Qwen3.6 summaries) and the rest
        # metered. If this (app, model) is "included", the subscription covers
        # it — pass through free. With no app_model_policy rows this never
        # triggers (default "metered"), so behavior is unchanged until an admin
        # adds explicit "included" rows.
        app_ctx = user.get("_app")
        if app_ctx and model:
            try:
                from inference_policy import resolve_inference_policy
                db_pool = getattr(request.app.state, "db_pool", None)
                policy = await resolve_inference_policy(app_ctx, model, db_pool)
            except Exception as pol_exc:
                logger.debug(f"Inference policy resolution failed (defaulting metered): {pol_exc}")
                policy = "metered"
            if policy == "included":
                logger.info(
                    f"Inference INCLUDED for app='{app_ctx}' model='{model}' "
                    f"(bundled in subscription) — no credit charge"
                )
                response = await call_next(request)
                response.headers["X-Inference-Included"] = "true"
                response.headers["X-Credits-Used"] = "0.0"
                return response

        # Check if BYOK enabled for this user/model
        is_byok, byok_provider = await self._check_byok_enabled(user_id, model)

        if is_byok:
            # BYOK enabled - skip credit deduction, just pass through
            logger.info(f"BYOK enabled for user {user_id} with provider {byok_provider} - no credits charged")

            response = await call_next(request)

            # Add BYOK headers
            response.headers["X-BYOK"] = "true"
            response.headers["X-BYOK-Provider"] = byok_provider
            response.headers["X-Credits-Used"] = "0.0"
            response.headers["X-Credits-Remaining"] = "unlimited"

            return response

        # Estimate credits needed for pre-check
        estimated_cost = await self._estimate_credits_needed(request)

        # Check sufficient credits BEFORE processing request
        has_credits, org_id, message = await self._check_sufficient_credits(
            user_id=user_id,
            credits_needed=estimated_cost,
            user_tier=user_tier,
            request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
        )

        if not has_credits:
            # Insufficient credits - return 402
            logger.warning(f"Insufficient credits for user {user_id}: {message}")

            return JSONResponse(
                status_code=402,
                content={
                    "error": "Payment Required",
                    "message": f"Insufficient credits. {message}",
                    "estimated_cost": estimated_cost,
                    "org_credits": org_id is not None,
                    "org_id": str(org_id) if org_id else None,
                    "upgrade_url": "/admin/subscription/plan"
                },
                headers={
                    "X-Credits-Required": str(estimated_cost),
                    "X-Org-Credits": "true" if org_id else "false"
                }
            )

        # Process the request
        response = await call_next(request)

        # Only deduct credits if response was successful
        if response.status_code < 400:
            try:
                # Extract actual cost from response
                result = await self._extract_actual_cost(request, response)

                # Skip if None (streaming response handled by litellm_api.py)
                if result is None:
                    logger.debug("Skipping middleware credit deduction (handled by endpoint)")
                    return response

                credits_used, tokens_used, provider = result

                if credits_used > 0:
                    # Deduct exact credits
                    success, remaining_credits = await self._deduct_credits(
                        user_id=user_id,
                        credits_used=credits_used,
                        tokens_used=tokens_used,
                        provider=provider,
                        model=model or "unknown",
                        org_id=org_id,
                        request_state=getattr(request, 'state', None) if hasattr(request, 'state') else None
                    )

                    # Add credit usage headers
                    response.headers["X-Credits-Used"] = f"{credits_used:.6f}"
                    response.headers["X-Credits-Remaining"] = f"{remaining_credits:.2f}"
                    response.headers["X-Org-Credits"] = "true" if org_id else "false"
                    response.headers["X-BYOK"] = "false"

                    if not success:
                        logger.error(f"Credit deduction failed for user {user_id}, but request succeeded (fail-open)")

            except Exception as e:
                logger.error(f"Error in credit deduction: {e}", exc_info=True)
                # Fail open: don't break the response if deduction fails

        return response


# Backward compatibility: export as function for older code
def create_credit_deduction_middleware():
    """Factory function to create middleware instance"""
    return CreditDeductionMiddleware
