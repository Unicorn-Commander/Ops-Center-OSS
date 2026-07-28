"""
Inference Proxy Router
======================

Authenticated proxy for GPU inference services (Majiks Studio, Artwork Studio, etc.).
Provides Keycloak auth + credit deduction + usage tracking for all inference requests.

Routes:
  /api/v1/inference/music/*   → Majiks Studio (ACE-Step music generation)
  /api/v1/inference/image/*   → Artwork Studio (FLUX image generation)
  /api/v1/inference/audio/*   → Artwork Studio (Whisper alignment/transcription)

Author: Ops-Center Inference Team
Created: 2026-03-26
"""

import os
import logging
import time
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from auth_dependencies import require_authenticated_user

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment variables
# ---------------------------------------------------------------------------

MAJIKS_API_URL = os.getenv("MAJIKS_API_URL", "http://unicorn-majiks-api:8090")
MAJIKS_SERVICE_KEY = os.getenv("MAJIKS_SERVICE_KEY", "")
ARTWORK_API_URL = os.getenv("ARTWORK_API_URL", "http://unicorn-artwork-api:8095")
ARTWORK_SERVICE_KEY = os.getenv("ARTWORK_SERVICE_KEY", "")

BILLING_ENABLED = os.getenv("BILLING_ENABLED", "true").lower() == "true"
CREDIT_EXEMPT_TIERS_ENV = os.getenv(
    "CREDIT_EXEMPT_TIERS",
    "free,vip_founder,vip,founder,founder_friend,admin,unlimited,internal",
)
CREDIT_EXEMPT_TIERS = set(
    t.strip() for t in CREDIT_EXEMPT_TIERS_ENV.split(",") if t.strip()
)

# ---------------------------------------------------------------------------
# Credit costs per service type (from federation/credit_estimator.py)
# ---------------------------------------------------------------------------

SERVICE_CREDIT_COSTS: Dict[str, int] = {
    "music_gen": 83,    # ACE-Step ~120s compute
    "image_gen": 21,    # FLUX ~30s compute
    "audio_align": 7,   # Whisper alignment ~10s per minute
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_credit_exempt(user_tier: str) -> bool:
    """Check whether a user tier is exempt from credit charges."""
    if not BILLING_ENABLED:
        return True
    if "*" in CREDIT_EXEMPT_TIERS:
        return True
    return user_tier in CREDIT_EXEMPT_TIERS


def _extract_user_tier(user_info: Dict[str, Any]) -> str:
    """Pull the subscription tier from user session data."""
    tier = user_info.get("subscription_tier") or user_info.get("tier", "")
    if not tier:
        # Try nested attributes (Keycloak custom attrs)
        attrs = user_info.get("attributes", {})
        if isinstance(attrs, dict):
            tier = attrs.get("subscription_tier", [""])[0] if isinstance(
                attrs.get("subscription_tier"), list
            ) else attrs.get("subscription_tier", "")
    return tier or "unknown"


def _user_id_from_info(user_info: Dict[str, Any]) -> str:
    """Extract user_id from session data."""
    return (
        user_info.get("user_id")
        or user_info.get("sub")
        or user_info.get("id", "unknown")
    )


async def _get_credit_system(request: Request):
    """Get credit system from app state (same as litellm_api)."""
    return getattr(request.app.state, "credit_system", None)


# ---------------------------------------------------------------------------
# Generic proxy function
# ---------------------------------------------------------------------------


async def _proxy_request(
    request: Request,
    target_url: str,
    service_key: str,
    method: str = "POST",
    service_type: str = "music_gen",
    user_info: Dict[str, Any] | None = None,
    stream_response: bool = False,
    is_multipart: bool = False,
) -> Response:
    """Forward request to inference service with auth + credit tracking.

    Args:
        request: The incoming FastAPI request.
        target_url: Full URL of the downstream inference service.
        service_key: Bearer token for service-to-service auth.
        method: HTTP method to use (GET, POST, etc.).
        service_type: Key into SERVICE_CREDIT_COSTS for billing.
        user_info: Authenticated user data from session.
        stream_response: If True, return a StreamingResponse (for downloads).
        is_multipart: If True, forward multipart/form-data body.

    Returns:
        FastAPI Response proxied from the inference service.
    """
    user_info = user_info or {}
    user_id = _user_id_from_info(user_info)
    user_email = user_info.get("email", "unknown")
    user_tier = _extract_user_tier(user_info)
    request_id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # 1. Credit pre-check (non-exempt tiers only)
    # ------------------------------------------------------------------
    credit_cost = SERVICE_CREDIT_COSTS.get(service_type, 0)
    exempt = _is_credit_exempt(user_tier)
    credit_system = await _get_credit_system(request)

    if not exempt and credit_cost > 0 and credit_system:
        try:
            balance = await credit_system.get_user_credits(user_id)
            if balance < credit_cost:
                logger.warning(
                    f"[inference-proxy] Insufficient credits for {user_email}: "
                    f"balance={balance}, cost={credit_cost}, service={service_type}"
                )
                return JSONResponse(
                    status_code=402,
                    content={
                        "error": "Insufficient credits",
                        "detail": (
                            f"This request costs {credit_cost} credits but you only "
                            f"have {int(balance)} credits remaining."
                        ),
                        "credits_required": credit_cost,
                        "credits_available": int(balance),
                    },
                )
        except Exception as exc:
            # Fail-open: don't block users if credit check fails
            logger.error(f"[inference-proxy] Credit pre-check failed (fail-open): {exc}")

    # ------------------------------------------------------------------
    # 2. Build downstream request
    # ------------------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {service_key}",
        "X-Request-ID": request_id,
        "X-Forwarded-User": user_email,
        "X-Forwarded-User-ID": user_id,
    }

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            if method.upper() == "GET":
                downstream = await client.get(target_url, headers=headers)
            elif is_multipart:
                # Forward multipart file uploads
                form = await request.form()
                files = {}
                data = {}
                for key, value in form.items():
                    if hasattr(value, "read"):
                        # UploadFile
                        content = await value.read()
                        files[key] = (value.filename, content, value.content_type or "application/octet-stream")
                    else:
                        data[key] = value
                downstream = await client.post(
                    target_url, headers=headers, files=files, data=data
                )
            else:
                # JSON body
                try:
                    body = await request.json()
                except Exception:
                    body = {}
                downstream = await client.request(
                    method.upper(), target_url, headers=headers, json=body
                )
    except httpx.TimeoutException:
        logger.error(f"[inference-proxy] Timeout proxying to {target_url}")
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway Timeout", "detail": "Inference service did not respond in time."},
        )
    except httpx.ConnectError:
        logger.error(f"[inference-proxy] Cannot connect to {target_url}")
        return JSONResponse(
            status_code=503,
            content={"error": "Service Unavailable", "detail": "Inference service is not running. It may need to be started."},
        )
    except Exception as exc:
        logger.error(f"[inference-proxy] Proxy error: {exc}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad Gateway", "detail": str(exc)},
        )

    elapsed = time.time() - start_time

    # ------------------------------------------------------------------
    # 3. Stream binary responses (audio/image downloads)
    # ------------------------------------------------------------------
    if stream_response and downstream.status_code == 200:
        content_type = downstream.headers.get("content-type", "application/octet-stream")
        resp_headers = {}
        if "content-disposition" in downstream.headers:
            resp_headers["content-disposition"] = downstream.headers["content-disposition"]
        if "content-length" in downstream.headers:
            resp_headers["content-length"] = downstream.headers["content-length"]

        return StreamingResponse(
            iter([downstream.content]),
            status_code=200,
            media_type=content_type,
            headers=resp_headers,
        )

    # ------------------------------------------------------------------
    # 4. Deduct credits after successful response (non-exempt only)
    # ------------------------------------------------------------------
    if (
        downstream.status_code in (200, 201, 202)
        and not exempt
        and credit_cost > 0
        and credit_system
    ):
        try:
            new_balance, tx_id = await credit_system.debit_credits(
                user_id,
                credit_cost,
                {
                    "service": "inference_proxy",
                    "service_type": service_type,
                    "request_id": request_id,
                    "target_url": target_url,
                    "elapsed_seconds": round(elapsed, 2),
                },
            )
            logger.info(
                f"[inference-proxy] Debited {credit_cost} credits from {user_email} "
                f"for {service_type} (balance={new_balance}, tx={tx_id})"
            )
        except Exception as exc:
            # Fail-open: don't retroactively fail the response
            logger.error(f"[inference-proxy] Credit deduction failed (fail-open): {exc}")

    # ------------------------------------------------------------------
    # 5. Log usage for analytics
    # ------------------------------------------------------------------
    try:
        from usage_metering import usage_meter

        await usage_meter.record_event(
            user_id=user_id,
            service="inference_proxy",
            event_type=service_type,
            metadata={
                "request_id": request_id,
                "target_url": target_url,
                "status_code": downstream.status_code,
                "elapsed_seconds": round(elapsed, 2),
                "credits_charged": credit_cost if not exempt else 0,
                "user_email": user_email,
                "user_tier": user_tier,
            },
        )
    except Exception as exc:
        # Non-blocking — usage logging failure should never break the proxy
        logger.debug(f"[inference-proxy] Usage logging failed: {exc}")

    # ------------------------------------------------------------------
    # 6. Return downstream response
    # ------------------------------------------------------------------
    response_headers = {
        "X-Request-ID": request_id,
        "X-Credits-Charged": str(credit_cost if not exempt else 0),
    }

    return Response(
        content=downstream.content,
        status_code=downstream.status_code,
        media_type=downstream.headers.get("content-type", "application/json"),
        headers=response_headers,
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/inference",
    tags=["inference-proxy"],
)


# ===========================================================================
# Music Generation (ACE-Step via Majiks Studio)
# ===========================================================================


@router.post("/music/generate")
async def music_generate(
    request: Request,
    user: Dict = Depends(require_authenticated_user),
):
    """Submit a music generation job to Majiks Studio."""
    return await _proxy_request(
        request=request,
        target_url=f"{MAJIKS_API_URL}/api/v1/studio/generate",
        service_key=MAJIKS_SERVICE_KEY,
        method="POST",
        service_type="music_gen",
        user_info=user,
    )


@router.get("/music/jobs/{job_id}")
async def music_job_status(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Poll Majiks Studio for music generation job status."""
    return await _proxy_request(
        request=request,
        target_url=f"{MAJIKS_API_URL}/api/v1/studio/jobs/{job_id}",
        service_key=MAJIKS_SERVICE_KEY,
        method="GET",
        service_type="music_gen",
        user_info=user,
    )


@router.get("/music/jobs/{job_id}/audio")
async def music_download(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Download generated audio from Majiks Studio."""
    return await _proxy_request(
        request=request,
        target_url=f"{MAJIKS_API_URL}/api/v1/studio/jobs/{job_id}/audio",
        service_key=MAJIKS_SERVICE_KEY,
        method="GET",
        service_type="music_gen",
        user_info=user,
        stream_response=True,
    )


# ===========================================================================
# Image Generation (FLUX via Artwork Studio)
# ===========================================================================


@router.post("/image/generate")
async def image_generate(
    request: Request,
    user: Dict = Depends(require_authenticated_user),
):
    """Submit an image generation job to Artwork Studio."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/album-artwork",
        service_key=ARTWORK_SERVICE_KEY,
        method="POST",
        service_type="image_gen",
        user_info=user,
    )


@router.get("/image/status/{job_id}")
async def image_status(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Poll Artwork Studio for image generation job status."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/status/{job_id}",
        service_key=ARTWORK_SERVICE_KEY,
        method="GET",
        service_type="image_gen",
        user_info=user,
    )


@router.get("/image/download/{job_id}")
async def image_download(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Download generated image from Artwork Studio."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/download/{job_id}",
        service_key=ARTWORK_SERVICE_KEY,
        method="GET",
        service_type="image_gen",
        user_info=user,
        stream_response=True,
    )


# ===========================================================================
# Audio Alignment / Transcription (Whisper via Artwork Studio)
# ===========================================================================


@router.post("/audio/align")
async def audio_align(
    request: Request,
    user: Dict = Depends(require_authenticated_user),
):
    """Submit a lyrics alignment / transcription job (multipart file upload)."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/align-lyrics",
        service_key=ARTWORK_SERVICE_KEY,
        method="POST",
        service_type="audio_align",
        user_info=user,
        is_multipart=True,
    )


@router.get("/audio/status/{job_id}")
async def audio_status(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Poll Artwork Studio for audio alignment job status."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/status/{job_id}",
        service_key=ARTWORK_SERVICE_KEY,
        method="GET",
        service_type="audio_align",
        user_info=user,
    )


@router.get("/audio/download/{job_id}")
async def audio_download(
    request: Request,
    job_id: str,
    user: Dict = Depends(require_authenticated_user),
):
    """Download alignment/transcription result from Artwork Studio."""
    return await _proxy_request(
        request=request,
        target_url=f"{ARTWORK_API_URL}/studio/download/{job_id}",
        service_key=ARTWORK_SERVICE_KEY,
        method="GET",
        service_type="audio_align",
        user_info=user,
        stream_response=True,
    )
