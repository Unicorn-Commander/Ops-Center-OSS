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
        """Extract user data from session cookie OR service key + X-User-ID header"""
        try:
            # Check for service key pattern (for bolt.diy, presenton, brigade, etc.)
            x_user_id = request.headers.get('X-User-ID')
            auth_header = request.headers.get('Authorization', '')

            if auth_header.startswith('Bearer sk-'):
                # Service key authentication - extract service name
                token = auth_header[7:]  # Remove "Bearer "

                # Known service keys mapping
                service_keys = {
                    'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
                    'sk-presenton-service-key-2025': 'presenton-service',
                    'sk-brigade-service-key-2025': 'brigade-service',
                    'sk-centerdeep-service-key-2025': 'centerdeep-service',
                    'sk-partnerpulse-service-key-2025': 'partnerpulse-service'
                }

                service_name = service_keys.get(token)
                if service_name:
                    if x_user_id:
                        # Service key with user context - return user data
                        logger.info(f"Service key request with user context: {x_user_id}")
                        return {
                            "user_id": x_user_id,
                            "subscription_tier": "professional",  # Default tier for service key users
                        }
                    else:
                        # Service key without user context - use service account
                        logger.info(f"Service key request without user context: {service_name}")
                        return {
                            "user_id": service_name,
                            "subscription_tier": "enterprise",  # Service accounts get enterprise tier
                        }
                else:
                    # Unknown service key - let endpoint handle authentication
                    logger.warning(f"Unknown service key in credit middleware: {token[:20]}...")
                    return None

            # Otherwise, try to get user from session cookie
            from redis_session import RedisSessionManager

            session_token = request.cookies.get("session_token")
            if not session_token:
                return None

            redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            sessions = RedisSessionManager(host=redis_host, port=redis_port)
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
            # Import here to avoid circular dependencies
            from byok_manager import BYOKManager

            byok_manager = BYOKManager()

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
                    "org_id": org_id,
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
