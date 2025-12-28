"""
Admin Subscription Management API Endpoints
Provides admin-only access to manage all user subscriptions
Uses Keycloak for authentication and user management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from keycloak_integration import (
    get_all_users,
    get_user_by_email,
    update_user_attributes
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/subscriptions", tags=["admin"])

# Pydantic models
class SubscriptionUpdate(BaseModel):
    tier: str
    status: str
    notes: Optional[str] = None

class UsageReset(BaseModel):
    email: str
    reset_reason: Optional[str] = None

class SubscriptionResponse(BaseModel):
    email: str
    username: str
    tier: str
    status: str
    usage: int
    limit: int
    joined_date: Optional[str]
    last_login: Optional[str]

# Admin authentication dependency
async def require_admin(request: Request):
    """Verify user has admin role"""
    user = request.session.get("user", {})

    # Check if user is admin
    is_admin = (
        user.get("role") == "admin" or
        user.get("is_admin") == True or
        user.get("is_superuser") == True or
        "admin" in user.get("groups", [])
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user

# Helper functions
def get_byok_keys_list(attributes: dict) -> List[str]:
    """Extract list of configured BYOK providers from user attributes"""
    providers = []
    for key in attributes.keys():
        if key.startswith("byok_") and key.endswith("_key"):
            provider = key.replace("byok_", "").replace("_key", "")
            if provider:
                providers.append(provider)
    return providers

def get_attribute_value(attributes: dict, key: str, default: Any = None) -> Any:
    """
    Get attribute value from Keycloak attributes
    Keycloak stores attributes as arrays, so we extract the first value
    """
    value = attributes.get(key, [default])
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    return default

# API Endpoints

@router.get("/list")
async def list_all_subscriptions(admin: dict = Depends(require_admin)):
    """List all user subscriptions with usage stats"""
    try:
        users = await get_all_users()

        subscriptions = []
        for user in users:
            attributes = user.get("attributes", {})

            subscriptions.append({
                "email": user.get("email"),
                "username": user.get("username"),
                "tier": get_attribute_value(attributes, "subscription_tier", "free"),
                "status": get_attribute_value(attributes, "subscription_status", "active"),
                "usage": int(get_attribute_value(attributes, "api_calls_used", 0)),
                "limit": int(get_attribute_value(attributes, "api_calls_limit", 0)),
                "joined_date": user.get("createdTimestamp"),
                "last_login": user.get("lastAccess"),
                "is_active": user.get("enabled", True),
                "byok_providers": get_byok_keys_list(attributes)
            })

        return {
            "success": True,
            "subscriptions": subscriptions,
            "total": len(subscriptions)
        }

    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{email}")
async def get_user_subscription(email: str, admin: dict = Depends(require_admin)):
    """Get detailed subscription info for a specific user"""
    try:
        user_info = await get_user_by_email(email)

        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")

        attributes = user_info.get("attributes", {})

        return {
            "success": True,
            "user": {
                "email": email,
                "username": user_info.get("username"),
                "name": f"{user_info.get('firstName', '')} {user_info.get('lastName', '')}".strip(),
                "is_active": user_info.get("enabled"),
                "tier": get_attribute_value(attributes, "subscription_tier", "free"),
                "status": get_attribute_value(attributes, "subscription_status", "active"),
                "subscription_id": get_attribute_value(attributes, "subscription_id"),
                "usage": {
                    "api_calls_used": int(get_attribute_value(attributes, "api_calls_used", 0)),
                    "api_calls_limit": int(get_attribute_value(attributes, "api_calls_limit", 0)),
                    "period_start": get_attribute_value(attributes, "billing_period_start"),
                    "period_end": get_attribute_value(attributes, "billing_period_end")
                },
                "byok_keys": get_byok_keys_list(attributes),
                "subscription_updated_at": get_attribute_value(attributes, "subscription_updated_at"),
                "joined_date": user_info.get("createdTimestamp"),
                "last_login": user_info.get("lastAccess")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{email}")
async def update_user_subscription(
    email: str,
    update: SubscriptionUpdate,
    admin: dict = Depends(require_admin)
):
    """Manually update a user's subscription (for support cases)"""
    try:
        # Validate tier
        valid_tiers = ["free", "trial", "starter", "professional", "enterprise"]
        if update.tier not in valid_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")

        # Validate status
        valid_statuses = ["active", "cancelled", "suspended", "trial"]
        if update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        # Set API limits based on tier
        tier_limits = {
            "free": 100,
            "trial": 1000,
            "starter": 10000,
            "professional": 100000,
            "enterprise": 1000000
        }

        # Update attributes (Keycloak expects arrays for attribute values)
        attributes = {
            "subscription_tier": [update.tier],
            "subscription_status": [update.status],
            "api_calls_limit": [str(tier_limits.get(update.tier, 100))],
            "subscription_updated_at": [datetime.utcnow().isoformat()],
            "subscription_updated_by": [admin.get("email", "admin")],
        }

        if update.notes:
            attributes["admin_notes"] = [update.notes]

        success = await update_user_attributes(email, attributes)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update subscription")

        return {
            "success": True,
            "message": "Subscription updated successfully",
            "email": email,
            "tier": update.tier,
            "status": update.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{email}/reset-usage")
async def reset_user_usage(email: str, admin: dict = Depends(require_admin)):
    """Reset a user's API usage counters"""
    try:
        # Keycloak expects arrays for attribute values
        attributes = {
            "api_calls_used": ["0"],
            "last_reset_date": [datetime.utcnow().isoformat()],
            "reset_by_admin": [admin.get("email", "admin")],
            "billing_period_start": [datetime.utcnow().isoformat()]
        }

        success = await update_user_attributes(email, attributes)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset usage")

        return {
            "success": True,
            "message": "Usage reset successfully",
            "email": email,
            "reset_by": admin.get("email")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_subscription_analytics(admin: dict = Depends(require_admin)):
    """Get subscription analytics and revenue metrics"""
    try:
        users = await get_all_users()

        # Count by tier
        tier_counts = {}
        total_revenue = 0
        active_subscriptions = 0
        total_usage = 0

        # Tier pricing
        tier_prices = {
            "free": 0,
            "trial": 1,
            "starter": 19,
            "professional": 49,
            "enterprise": 99
        }

        for user in users:
            attributes = user.get("attributes", {})
            tier = get_attribute_value(attributes, "subscription_tier", "free")
            status = get_attribute_value(attributes, "subscription_status", "active")

            # Count tiers
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            # Calculate revenue (only active subscriptions)
            if status == "active":
                active_subscriptions += 1
                total_revenue += tier_prices.get(tier, 0)

            # Sum usage
            total_usage += int(get_attribute_value(attributes, "api_calls_used", 0))

        return {
            "success": True,
            "analytics": {
                "total_users": len(users),
                "active_subscriptions": active_subscriptions,
                "tier_distribution": tier_counts,
                "revenue": {
                    "monthly_recurring_revenue": total_revenue,
                    "annual_recurring_revenue": total_revenue * 12
                },
                "usage": {
                    "total_api_calls": total_usage,
                    "average_per_user": total_usage / len(users) if users else 0
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/revenue-by-tier")
async def get_revenue_by_tier(admin: dict = Depends(require_admin)):
    """Get revenue breakdown by subscription tier"""
    try:
        users = await get_all_users()

        tier_prices = {
            "free": 0,
            "trial": 1,
            "starter": 19,
            "professional": 49,
            "enterprise": 99
        }

        revenue_by_tier = {}

        for user in users:
            attributes = user.get("attributes", {})
            tier = get_attribute_value(attributes, "subscription_tier", "free")
            status = get_attribute_value(attributes, "subscription_status", "active")

            if status == "active":
                if tier not in revenue_by_tier:
                    revenue_by_tier[tier] = {
                        "users": 0,
                        "monthly_revenue": 0,
                        "annual_revenue": 0
                    }

                revenue_by_tier[tier]["users"] += 1
                revenue_by_tier[tier]["monthly_revenue"] += tier_prices.get(tier, 0)
                revenue_by_tier[tier]["annual_revenue"] += tier_prices.get(tier, 0) * 12

        return {
            "success": True,
            "revenue_by_tier": revenue_by_tier
        }

    except Exception as e:
        logger.error(f"Error getting revenue by tier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/usage-stats")
async def get_usage_statistics(admin: dict = Depends(require_admin)):
    """Get detailed usage statistics"""
    try:
        users = await get_all_users()

        usage_stats = {
            "total_users": len(users),
            "users_with_usage": 0,
            "total_api_calls": 0,
            "usage_by_tier": {}
        }

        for user in users:
            attributes = user.get("attributes", {})
            tier = get_attribute_value(attributes, "subscription_tier", "free")
            usage = int(get_attribute_value(attributes, "api_calls_used", 0))

            if usage > 0:
                usage_stats["users_with_usage"] += 1

            usage_stats["total_api_calls"] += usage

            if tier not in usage_stats["usage_by_tier"]:
                usage_stats["usage_by_tier"][tier] = {
                    "users": 0,
                    "total_calls": 0,
                    "average_calls": 0
                }

            usage_stats["usage_by_tier"][tier]["users"] += 1
            usage_stats["usage_by_tier"][tier]["total_calls"] += usage

        # Calculate averages
        for tier_data in usage_stats["usage_by_tier"].values():
            if tier_data["users"] > 0:
                tier_data["average_calls"] = tier_data["total_calls"] / tier_data["users"]

        return {
            "success": True,
            "usage_stats": usage_stats
        }

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
