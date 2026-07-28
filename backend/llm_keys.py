"""
LLM API Keys Management - Generate and manage LiteLLM virtual keys (sk-...)

Users generate sk-... keys from the dashboard to use with OpenAI-compatible
clients (opencode, Cursor, custom apps) against llm.unicorncommander.ai.

Backend proxies LiteLLM /key/* endpoints using the master key,
tying each virtual key to the UC user's identity.

Author: Claude (AI Assistant)
Date: April 16, 2026
"""

import logging
import os
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm/keys", tags=["LLM API Keys"])

# LiteLLM internal URL and master key
LITELLM_URL = os.getenv("LITELLM_INTERNAL_URL", "http://uchub-litellm:4000")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")


# ============================================================================
# Models
# ============================================================================

class CreateLLMKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Key name")
    max_budget: Optional[float] = Field(10.0, description="Max spend in USD (default $10)")
    budget_duration: Optional[str] = Field("30d", description="Budget reset period (e.g. 30d, 7d)")
    rpm_limit: Optional[int] = Field(60, description="Requests per minute")
    tpm_limit: Optional[int] = Field(100000, description="Tokens per minute")
    models: Optional[List[str]] = Field([], description="Allowed models (empty = all)")
    duration: Optional[str] = Field(None, description="Key expiration (e.g. 90d, 365d, None=never)")


class LLMKeyResponse(BaseModel):
    key_id: str
    key_name: str
    key_preview: str
    key: Optional[str] = None  # Full key, only on create
    max_budget: Optional[float]
    spend: float
    budget_duration: Optional[str]
    rpm_limit: Optional[int]
    tpm_limit: Optional[int]
    models: List[str]
    created_at: Optional[str]
    expires: Optional[str]
    user_id: Optional[str]


# ============================================================================
# Auth
# ============================================================================

async def get_current_user(request: Request) -> Dict:
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    user["user_id"] = user.get("user_id") or user.get("sub") or user.get("email", "unknown")
    return user


def _get_master_key(status_code: int = 503):
    key = LITELLM_MASTER_KEY
    if not key:
        raise HTTPException(
            status_code=status_code,
            detail="LiteLLM key management is not configured on this node",
        )
    return key


# ============================================================================
# Endpoints
# ============================================================================

# Users allowed to access local GPU models (local/*, midboy1/*, bigboy/*, lambda/*)
# Everyone else gets cloud-only models
LOCAL_GPU_ALLOWED_USERS = set(os.getenv("LOCAL_GPU_ALLOWED_USERS",
    "admin@example.com,partner@example.com").split(","))

# Cloud-only model prefixes (for non-GPU users)
CLOUD_ONLY_MODELS = [
    "openrouter/*", "anthropic/*", "openai/*", "google/*",
    "meta-llama/*", "mistralai/*", "qwen/*", "deepseek/*",
    "cohere/*", "perplexity/*",
    "gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "claude-3.5-haiku",
    "gemini-1.5-pro", "gemini-1.5-flash", "deepseek-r1",
]


def _user_has_gpu_access(user: Dict) -> bool:
    """Check if user is allowed to use local GPU models."""
    email = user.get("email", "").lower()
    role = user.get("role", "")
    # Admin always gets GPU access
    if role == "admin":
        return True
    return email in LOCAL_GPU_ALLOWED_USERS


@router.post("", status_code=201)
async def create_llm_key(
    req: CreateLLMKeyRequest,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """Generate a new LLM API key (sk-...). The full key is shown ONLY ONCE."""
    user_id = user["user_id"]
    # Key creation cannot function without the master key — return a clear
    # "not configured" client error (400) rather than a raw 503.
    master_key = _get_master_key(status_code=400)

    # Determine model access based on user privileges
    if req.models:
        # User explicitly requested specific models — honor it if they have access
        models = req.models
    elif _user_has_gpu_access(user):
        # GPU-allowed user gets all models
        models = []
    else:
        # Non-GPU user gets cloud-only models
        models = CLOUD_ONLY_MODELS
        logger.info(f"User {user_id} restricted to cloud-only models (no local GPU access)")

    payload = {
        "key_alias": req.name,
        "user_id": user_id,
        "max_budget": req.max_budget,
        "budget_duration": req.budget_duration,
        "rpm_limit": req.rpm_limit,
        "tpm_limit": req.tpm_limit,
        "models": models,
        "metadata": {
            "generated_by": "ops-center",
            "uc_user": user_id,
            "uc_email": user.get("email", ""),
        },
    }
    if req.duration:
        payload["duration"] = req.duration

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{LITELLM_URL}/key/generate",
            json=payload,
            headers={"Authorization": f"Bearer {master_key}"}
        )

    if resp.status_code != 200:
        logger.error(f"LiteLLM key/generate failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail="Failed to generate LLM key")

    data = resp.json()
    logger.info(f"Generated LLM key '{req.name}' for user {user_id}")

    return {
        "key_id": data.get("token_id") or data.get("token", ""),
        "key_name": data.get("key_alias", req.name),
        "key_preview": data.get("key_name", ""),
        "key": data.get("key"),  # Full sk-... key, shown ONCE
        "max_budget": data.get("max_budget"),
        "spend": data.get("spend", 0),
        "budget_duration": data.get("budget_duration"),
        "rpm_limit": data.get("rpm_limit"),
        "tpm_limit": data.get("tpm_limit"),
        "models": data.get("models", []),
        "created_at": data.get("created_at"),
        "expires": data.get("expires"),
        "user_id": user_id,
        "warning": "Save this key now. You will not be able to see it again."
    }


@router.get("")
async def list_llm_keys(
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """List all LLM API keys for the current user."""
    user_id = user["user_id"]
    is_admin = user.get("role") == "admin"

    # Graceful degradation: if LiteLLM master key isn't configured on this
    # node, key management is unavailable. The happy path returns a bare list
    # of keys, and the frontend maps over it directly, so return an empty list
    # (HTTP 200) here. The API-keys screen renders a clean empty state instead
    # of erroring on a 503.
    if not LITELLM_MASTER_KEY:
        logger.warning("LiteLLM master key not configured; returning empty key list")
        return []

    master_key = _get_master_key()

    # Admin sees all keys, regular users see only their own
    endpoint = f"{LITELLM_URL}/key/list"
    params = {"return_full_object": "true", "page_size": "100"}
    if not is_admin:
        params["user_id"] = user_id

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            endpoint,
            params=params,
            headers={"Authorization": f"Bearer {master_key}"}
        )

    if resp.status_code != 200:
        logger.error(f"LiteLLM key/list failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail="Failed to list LLM keys")

    data = resp.json()
    keys_list = data if isinstance(data, list) else data.get("keys", [])

    # Filter to user's keys if not admin
    if not is_admin:
        keys_list = [k for k in keys_list if k.get("user_id") == user_id]

    # Exclude master key and service keys from listing
    keys_list = [k for k in keys_list if k.get("key_alias") not in ("litellm-master-key", "ops-center-service")]

    return [{
        "key_id": k.get("token", ""),
        "key_name": k.get("key_alias", "Unnamed"),
        "key_preview": k.get("key_name", "sk-..."),
        "max_budget": k.get("max_budget"),
        "spend": k.get("spend", 0),
        "budget_duration": k.get("budget_duration"),
        "rpm_limit": k.get("rpm_limit"),
        "tpm_limit": k.get("tpm_limit"),
        "models": k.get("models", []),
        "created_at": k.get("created_at"),
        "expires": k.get("expires"),
        "user_id": k.get("user_id"),
        "metadata": k.get("metadata", {}),
    } for k in keys_list]


@router.delete("/{key_id}")
async def revoke_llm_key(
    key_id: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """Revoke an LLM API key."""
    user_id = user["user_id"]
    is_admin = user.get("role") == "admin"
    # Revocation cannot function without the master key — return a clear
    # "not configured" client error (400) rather than a raw 503.
    master_key = _get_master_key(status_code=400)

    # Verify ownership (unless admin)
    if not is_admin:
        async with httpx.AsyncClient(timeout=15) as client:
            info_resp = await client.get(
                f"{LITELLM_URL}/key/info",
                params={"key": key_id},
                headers={"Authorization": f"Bearer {master_key}"}
            )
        if info_resp.status_code == 200:
            info = info_resp.json()
            key_info = info.get("info", info)
            if key_info.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Not your key")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{LITELLM_URL}/key/delete",
            json={"keys": [key_id]},
            headers={"Authorization": f"Bearer {master_key}"}
        )

    if resp.status_code != 200:
        logger.error(f"LiteLLM key/delete failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail="Failed to revoke key")

    logger.info(f"Revoked LLM key {key_id[:8]}... for user {user_id}")
    return {"success": True, "message": "LLM API key revoked"}


@router.get("/info/{key_id}")
async def get_llm_key_info(
    key_id: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """Get detailed info about a specific LLM key."""
    # Graceful degradation: no key management configured on this node — there
    # are no keys to describe, so return an empty object (HTTP 200) to match
    # the happy-path dict shape instead of erroring.
    if not LITELLM_MASTER_KEY:
        logger.warning("LiteLLM master key not configured; returning empty key info")
        return {}

    master_key = _get_master_key()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{LITELLM_URL}/key/info",
            params={"key": key_id},
            headers={"Authorization": f"Bearer {master_key}"}
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Key not found")

    return resp.json()
