"""
Example Integration: Lago Org-Based Billing
Demonstrates how to integrate the new org-based Lago billing into your application
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import uuid4
import logging

# Import the new org-based Lago integration
from lago_integration import (
    get_or_create_customer,
    subscribe_org_to_plan,
    record_api_call,
    get_current_usage,
    get_subscription,
    get_invoices,
    terminate_subscription,
    create_subscription,
    LagoIntegrationError,
    check_lago_health
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing/org", tags=["org-billing"])


# ============================================
# Request/Response Models
# ============================================

class OrganizationCreate(BaseModel):
    """Request model for creating an organization with billing"""
    org_name: str
    billing_email: str
    plan_code: str = "starter_monthly"
    user_id: str  # User creating the org


class SubscriptionUpdate(BaseModel):
    """Request model for updating subscription"""
    plan_code: str


class UsageEvent(BaseModel):
    """Request model for recording usage"""
    endpoint: str
    user_id: str
    tokens: int = 0
    model: Optional[str] = None


# ============================================
# Organization Billing Endpoints
# ============================================

@router.post("/organizations/{org_id}/setup")
async def setup_organization_billing(org_id: str, data: OrganizationCreate):
    """
    Set up billing for a new organization.
    Creates Lago customer and subscribes to initial plan.
    """
    try:
        # Create customer and subscription in Lago
        subscription = await subscribe_org_to_plan(
            org_id=org_id,
            plan_code=data.plan_code,
            org_name=data.org_name,
            email=data.billing_email,
            user_id=data.user_id
        )

        logger.info(f"Set up billing for org {org_id} on plan {data.plan_code}")

        return {
            "success": True,
            "message": "Billing setup successful",
            "org_id": org_id,
            "plan_code": data.plan_code,
            "subscription": subscription
        }

    except LagoIntegrationError as e:
        logger.error(f"Failed to setup billing for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Billing setup failed: {str(e)}")


@router.get("/organizations/{org_id}/subscription")
async def get_organization_subscription(org_id: str):
    """Get current subscription details for an organization"""
    subscription = await get_subscription(org_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    return {
        "org_id": org_id,
        "subscription": subscription,
        "plan_code": subscription.get("plan_code"),
        "status": subscription.get("status"),
        "started_at": subscription.get("started_at")
    }


@router.put("/organizations/{org_id}/subscription")
async def update_organization_subscription(org_id: str, data: SubscriptionUpdate):
    """
    Update organization subscription (upgrade/downgrade).
    Terminates current subscription and creates new one.
    """
    try:
        # Get current subscription
        current_sub = await get_subscription(org_id)
        if not current_sub:
            raise HTTPException(status_code=404, detail="No active subscription found")

        # Terminate current subscription
        success = await terminate_subscription(org_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to terminate current subscription")

        # Create new subscription
        new_subscription = await create_subscription(org_id, data.plan_code)

        logger.info(f"Updated org {org_id} subscription to {data.plan_code}")

        return {
            "success": True,
            "message": "Subscription updated successfully",
            "org_id": org_id,
            "previous_plan": current_sub.get("plan_code"),
            "new_plan": data.plan_code,
            "subscription": new_subscription
        }

    except LagoIntegrationError as e:
        logger.error(f"Failed to update subscription for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Subscription update failed: {str(e)}")


@router.delete("/organizations/{org_id}/subscription")
async def cancel_organization_subscription(org_id: str):
    """Cancel organization subscription"""
    success = await terminate_subscription(org_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    logger.info(f"Cancelled subscription for org {org_id}")

    return {
        "success": True,
        "message": "Subscription cancelled successfully",
        "org_id": org_id
    }


# ============================================
# Usage Tracking Endpoints
# ============================================

@router.post("/organizations/{org_id}/usage/record")
async def record_organization_usage(org_id: str, event: UsageEvent):
    """
    Manually record a usage event for an organization.
    Typically used by middleware or background tasks.
    """
    try:
        transaction_id = f"tx_{uuid4()}"

        success = await record_api_call(
            org_id=org_id,
            transaction_id=transaction_id,
            endpoint=event.endpoint,
            user_id=event.user_id,
            tokens=event.tokens,
            model=event.model
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to record usage")

        return {
            "success": True,
            "message": "Usage recorded successfully",
            "transaction_id": transaction_id,
            "org_id": org_id
        }

    except Exception as e:
        logger.error(f"Failed to record usage for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Usage recording failed: {str(e)}")


@router.get("/organizations/{org_id}/usage/current")
async def get_organization_usage(org_id: str):
    """Get current billing period usage for an organization"""
    usage = await get_current_usage(org_id)

    if not usage:
        raise HTTPException(status_code=404, detail="No usage data found")

    return {
        "org_id": org_id,
        "usage": usage,
        "billing_period": usage.get("from_datetime"),
        "total_amount": usage.get("total_amount")
    }


# ============================================
# Invoice Endpoints
# ============================================

@router.get("/organizations/{org_id}/invoices")
async def get_organization_invoices(org_id: str, limit: int = 10):
    """Get invoices for an organization"""
    invoices = await get_invoices(org_id, limit=limit)

    return {
        "org_id": org_id,
        "invoices": invoices,
        "count": len(invoices)
    }


# ============================================
# Health & Status
# ============================================

@router.get("/health")
async def billing_health():
    """Check if Lago billing integration is healthy"""
    health = await check_lago_health()

    if health.get("status") != "healthy":
        raise HTTPException(status_code=503, detail=health.get("message"))

    return health


# ============================================
# Middleware Example
# ============================================

async def org_billing_middleware(request: Request, call_next):
    """
    Example middleware to automatically track API usage per organization.
    Add this to your FastAPI app to automatically record all API calls.

    Usage:
        app.middleware("http")(org_billing_middleware)
    """
    # Skip billing endpoints and health checks
    if request.url.path.startswith("/api/v1/billing") or request.url.path == "/health":
        return await call_next(request)

    # Get org_id from request state (set by auth middleware)
    org_id = getattr(request.state, "org_id", None)
    user_id = getattr(request.state, "user_id", None)

    # Process request
    response = await call_next(request)

    # Record usage if org_id is available
    if org_id and response.status_code < 400:
        try:
            # Extract usage info from response headers (if available)
            tokens = int(response.headers.get("X-Tokens-Used", 0))
            model = response.headers.get("X-Model-Used", None)

            # Record in background (don't block response)
            transaction_id = f"tx_{uuid4()}"
            await record_api_call(
                org_id=org_id,
                transaction_id=transaction_id,
                endpoint=request.url.path,
                user_id=user_id or "unknown",
                tokens=tokens,
                model=model
            )
        except Exception as e:
            # Log but don't fail the request
            logger.error(f"Failed to record usage for org {org_id}: {e}")

    return response


# ============================================
# Helper Functions for Your Application
# ============================================

async def check_org_has_active_subscription(org_id: str) -> bool:
    """
    Helper to check if an organization has an active subscription.
    Use this in access control logic.
    """
    subscription = await get_subscription(org_id)
    return subscription and subscription.get("status") == "active"


async def get_org_plan_limits(org_id: str) -> Dict[str, Any]:
    """
    Get plan limits for an organization.
    Returns limits based on their current subscription plan.
    """
    subscription = await get_subscription(org_id)

    if not subscription:
        # Return trial limits
        return {
            "api_calls_limit": 100,
            "team_seats": 1,
            "features": ["basic"]
        }

    plan_code = subscription.get("plan_code", "")

    # Map plan codes to limits (customize based on your plans)
    plan_limits = {
        "starter": {
            "api_calls_limit": 1000,
            "team_seats": 3,
            "features": ["basic", "byok"]
        },
        "professional": {
            "api_calls_limit": 10000,
            "team_seats": 10,
            "features": ["basic", "byok", "priority_support", "advanced_models"]
        },
        "enterprise": {
            "api_calls_limit": -1,  # Unlimited
            "team_seats": 50,
            "features": ["all"]
        }
    }

    # Find matching plan
    for plan_key, limits in plan_limits.items():
        if plan_key in plan_code.lower():
            return limits

    # Default to starter
    return plan_limits["starter"]


async def enforce_usage_limits(org_id: str) -> bool:
    """
    Check if organization is within usage limits.
    Returns True if usage is OK, False if over limit.
    Use this before allowing API calls.
    """
    try:
        # Get current usage
        usage_data = await get_current_usage(org_id)
        if not usage_data:
            return True  # No usage tracking, allow

        # Get plan limits
        limits = await get_org_plan_limits(org_id)
        api_limit = limits.get("api_calls_limit", -1)

        # Unlimited plan
        if api_limit == -1:
            return True

        # Extract actual usage (structure depends on Lago response)
        # This is a simplified example
        usage = usage_data.get("charges_usage", [])
        total_calls = sum(charge.get("units", 0) for charge in usage)

        # Check if over limit
        if total_calls >= api_limit:
            logger.warning(f"Org {org_id} has exceeded usage limit: {total_calls}/{api_limit}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error checking usage limits for org {org_id}: {e}")
        # On error, allow the request (fail open)
        return True


# ============================================
# Integration with Existing Auth
# ============================================

def get_current_org(request: Request) -> Dict[str, Any]:
    """
    Extract organization info from request.
    Assumes auth middleware has set request.state.user
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization associated with user")

    return {
        "org_id": org_id,
        "org_name": user.get("org_name", "Unknown"),
        "user_id": user.get("id"),
        "user_role": user.get("role", "member")
    }


# ============================================
# Example Protected Endpoint
# ============================================

@router.get("/organizations/{org_id}/dashboard")
async def organization_dashboard(org_id: str):
    """
    Example protected endpoint showing org billing dashboard.
    Combines subscription, usage, and invoice data.
    """
    # Check if org has active subscription
    has_subscription = await check_org_has_active_subscription(org_id)

    if not has_subscription:
        return {
            "org_id": org_id,
            "subscription_status": "inactive",
            "message": "No active subscription. Please subscribe to a plan."
        }

    # Get subscription details
    subscription = await get_subscription(org_id)

    # Get current usage
    usage = await get_current_usage(org_id)

    # Get recent invoices
    invoices = await get_invoices(org_id, limit=5)

    # Get plan limits
    limits = await get_org_plan_limits(org_id)

    return {
        "org_id": org_id,
        "subscription": {
            "plan_code": subscription.get("plan_code"),
            "status": subscription.get("status"),
            "started_at": subscription.get("started_at")
        },
        "usage": usage,
        "limits": limits,
        "recent_invoices": invoices,
        "subscription_status": "active"
    }
