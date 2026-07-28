"""
Billing Management Module for UC-1 Pro Ops Center
Handles API keys, subscriptions, and billing configuration
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import os
import json
import httpx
from datetime import datetime
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Configuration file paths
BILLING_CONFIG_PATH = "/app/config/billing_config.json"
USER_KEYS_PATH = "/app/config/user_keys.json"

class ProviderKey(BaseModel):
    """API key configuration for AI providers"""
    provider: str
    key: str = Field(..., min_length=1)
    is_active: bool = True
    added_date: Optional[str] = None

class StripeConfig(BaseModel):
    """Stripe configuration"""
    publishable_key: str
    secret_key: str
    webhook_secret: str
    test_mode: bool = True

class SubscriptionTier(BaseModel):
    """Subscription tier configuration"""
    name: str
    price: float
    tokens_per_month: int
    features: List[str]
    byok_enabled: bool = False

class BillingConfig(BaseModel):
    """Complete billing configuration"""
    stripe: Optional[StripeConfig] = None
    provider_keys: List[ProviderKey] = []
    subscription_tiers: List[SubscriptionTier] = []
    lago_api_key: Optional[str] = None
    litellm_master_key: Optional[str] = None
    billing_enabled: bool = False

class UserAccountInfo(BaseModel):
    """User account information"""
    user_id: str
    email: str
    subscription_tier: str = "free"
    usage_this_month: Dict[str, Any] = {}
    payment_method: Optional[str] = None
    byok_keys: List[ProviderKey] = []

def load_billing_config() -> BillingConfig:
    """Load billing configuration from file"""
    if os.path.exists(BILLING_CONFIG_PATH):
        try:
            with open(BILLING_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return BillingConfig(**data)
        except Exception as e:
            logger.error(f"Error loading billing config: {e}")

    # Return default config
    return BillingConfig(
        subscription_tiers=[
            SubscriptionTier(
                name="free",
                price=0,
                tokens_per_month=10000,
                features=["Basic AI access", "Community support"],
                byok_enabled=False
            ),
            SubscriptionTier(
                name="basic",
                price=19,
                tokens_per_month=100000,
                features=["Extended AI access", "BYOK support", "Email support"],
                byok_enabled=True
            ),
            SubscriptionTier(
                name="pro",
                price=49,
                tokens_per_month=500000,
                features=["Priority AI access", "BYOK support", "Priority support", "Advanced models"],
                byok_enabled=True
            ),
            SubscriptionTier(
                name="enterprise",
                price=99,
                tokens_per_month=-1,  # Unlimited
                features=["Unlimited AI access", "BYOK support", "24/7 support", "Custom models", "Team management"],
                byok_enabled=True
            )
        ]
    )

def save_billing_config(config: BillingConfig):
    """Save billing configuration to file"""
    os.makedirs(os.path.dirname(BILLING_CONFIG_PATH), exist_ok=True)
    with open(BILLING_CONFIG_PATH, 'w') as f:
        json.dump(config.dict(), f, indent=2, default=str)

def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request (mock for now, integrate with Authentik later)"""
    # TODO: Integrate with Authentik JWT validation
    # For now, check if admin based on header or session
    is_admin = request.headers.get("X-Admin-Token") == os.getenv("ADMIN_TOKEN", "admin-secret")

    return {
        "user_id": "admin" if is_admin else "user-" + secrets.token_hex(4),
        "email": "admin@unicorncommander.ai" if is_admin else "user@example.com",
        "is_admin": is_admin,
        "subscription_tier": "enterprise" if is_admin else "free"
    }

# ============================================
# Admin Endpoints
# ============================================

@router.get("/config")
async def get_billing_configuration(request: Request):
    """Get billing configuration (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    config = load_billing_config()
    return config

@router.post("/config")
async def update_billing_configuration(config: BillingConfig, request: Request):
    """Update billing configuration (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Add timestamps to new keys
    for key in config.provider_keys:
        if not key.added_date:
            key.added_date = datetime.now().isoformat()

    save_billing_config(config)
    return {"message": "Billing configuration updated successfully"}

@router.post("/config/stripe")
async def update_stripe_configuration(stripe_config: StripeConfig, request: Request):
    """Update Stripe configuration (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    config = load_billing_config()
    config.stripe = stripe_config
    save_billing_config(config)

    return {"message": "Stripe configuration updated successfully"}

@router.post("/config/provider-keys")
async def add_provider_key(key: ProviderKey, request: Request):
    """Add or update provider API key (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    config = load_billing_config()
    key.added_date = datetime.now().isoformat()

    # Update existing or add new
    existing = next((k for k in config.provider_keys if k.provider == key.provider), None)
    if existing:
        config.provider_keys.remove(existing)
    config.provider_keys.append(key)

    save_billing_config(config)
    return {"message": f"Provider key for {key.provider} updated successfully"}

@router.delete("/config/provider-keys/{provider}")
async def delete_provider_key(provider: str, request: Request):
    """Delete provider API key (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    config = load_billing_config()
    config.provider_keys = [k for k in config.provider_keys if k.provider != provider]
    save_billing_config(config)

    return {"message": f"Provider key for {provider} deleted"}

@router.get("/config/subscription-tiers")
async def get_subscription_tiers(request: Request):
    """Get available subscription tiers (public)"""
    config = load_billing_config()
    return config.subscription_tiers

@router.post("/config/subscription-tiers")
async def update_subscription_tiers(tiers: List[SubscriptionTier], request: Request):
    """Update subscription tiers (admin only)"""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    config = load_billing_config()
    config.subscription_tiers = tiers
    save_billing_config(config)

    return {"message": "Subscription tiers updated successfully"}

# ============================================
# User Self-Service Endpoints
# ============================================

@router.get("/account")
async def get_user_account(request: Request):
    """Get current user's account information"""
    user = get_current_user(request)

    # Load user-specific data
    user_keys = []
    if os.path.exists(USER_KEYS_PATH):
        with open(USER_KEYS_PATH, 'r') as f:
            all_keys = json.load(f)
            user_keys = all_keys.get(user["user_id"], [])

    return UserAccountInfo(
        user_id=user["user_id"],
        email=user["email"],
        subscription_tier=user.get("subscription_tier", "free"),
        usage_this_month={
            "tokens": 5432,
            "requests": 234,
            "cost": 12.34
        },
        byok_keys=user_keys
    )

@router.post("/account/byok-keys")
async def update_user_byok_keys(key: ProviderKey, request: Request):
    """Update user's BYOK API keys"""
    user = get_current_user(request)

    # Load existing keys
    all_keys = {}
    if os.path.exists(USER_KEYS_PATH):
        with open(USER_KEYS_PATH, 'r') as f:
            all_keys = json.load(f)

    # Update user's keys
    if user["user_id"] not in all_keys:
        all_keys[user["user_id"]] = []

    user_keys = all_keys[user["user_id"]]
    key.added_date = datetime.now().isoformat()

    # Update existing or add new
    existing = next((k for k in user_keys if k["provider"] == key.provider), None)
    if existing:
        user_keys.remove(existing)
    user_keys.append(key.dict())

    # Save
    os.makedirs(os.path.dirname(USER_KEYS_PATH), exist_ok=True)
    with open(USER_KEYS_PATH, 'w') as f:
        json.dump(all_keys, f, indent=2)

    # Also update in Authentik (if integrated)
    await update_authentik_user_attributes(user["user_id"], {f"{key.provider}_api_key": key.key})

    return {"message": f"BYOK key for {key.provider} updated successfully"}

@router.delete("/account/byok-keys/{provider}")
async def delete_user_byok_key(provider: str, request: Request):
    """Delete user's BYOK API key"""
    user = get_current_user(request)

    # Load and update keys
    if os.path.exists(USER_KEYS_PATH):
        with open(USER_KEYS_PATH, 'r') as f:
            all_keys = json.load(f)

        if user["user_id"] in all_keys:
            all_keys[user["user_id"]] = [
                k for k in all_keys[user["user_id"]]
                if k.get("provider") != provider
            ]

            with open(USER_KEYS_PATH, 'w') as f:
                json.dump(all_keys, f, indent=2)

    return {"message": f"BYOK key for {provider} deleted"}

@router.get("/account/usage")
async def get_user_usage(request: Request):
    """Get user's current usage statistics"""
    user = get_current_user(request)

    # TODO: Fetch from Lago billing API
    return {
        "user_id": user["user_id"],
        "current_month": {
            "tokens_used": 45234,
            "tokens_limit": 100000,
            "requests": 1234,
            "cost": 23.45,
            "models_used": {
                "gpt-4o": 30000,
                "claude-3.5-sonnet": 15234
            }
        },
        "last_month": {
            "tokens_used": 89432,
            "cost": 45.67
        }
    }

@router.post("/account/subscription")
async def update_user_subscription(tier: str, request: Request):
    """Update user's subscription tier"""
    user = get_current_user(request)

    # TODO: Integrate with Stripe for payment
    # TODO: Update in Authentik user groups

    return {
        "message": f"Subscription updated to {tier}",
        "payment_required": tier != "free",
        "checkout_url": f"https://billing.unicorncommander.ai/checkout?tier={tier}&user={user['user_id']}"
    }

# ============================================
# Integration Endpoints
# ============================================

@router.get("/services/status")
async def get_billing_services_status():
    """Check status of billing services"""
    services = {
        "lago": {"url": "http://unicorn-lago-api:3000/health", "status": "unknown"},
        "litellm": {"url": "http://unicorn-litellm:4000/health", "status": "unknown"},
        "stripe": {"configured": False},
        "authentik": {"integrated": False}
    }

    # Check Lago
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(services["lago"]["url"], timeout=2.0)
            services["lago"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["lago"]["status"] = "offline"

    # Check LiteLLM
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(services["litellm"]["url"], timeout=2.0)
            services["litellm"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["litellm"]["status"] = "offline"

    # Check Stripe config
    config = load_billing_config()
    services["stripe"]["configured"] = config.stripe is not None

    return services

async def update_authentik_user_attributes(user_id: str, attributes: Dict[str, Any]):
    """Update user attributes in Authentik"""
    # TODO: Implement Authentik API integration
    authentik_url = os.getenv("AUTHENTIK_URL", "http://authentik-server:9000")
    authentik_token = os.getenv("AUTHENTIK_API_TOKEN")

    if not authentik_token:
        logger.warning("Authentik API token not configured")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{authentik_url}/api/v3/core/users/{user_id}/",
                headers={"Authorization": f"Bearer {authentik_token}"},
                json={"attributes": attributes}
            )
            if response.status_code != 200:
                logger.error(f"Failed to update Authentik attributes: {response.text}")
    except Exception as e:
        logger.error(f"Error updating Authentik: {e}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "billing-manager"}