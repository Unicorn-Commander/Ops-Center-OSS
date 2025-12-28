"""
Lago Webhook Handler for Subscription Events
Handles subscription lifecycle events from Lago billing system
Syncs subscription data to Keycloak user attributes
"""

from fastapi import APIRouter, HTTPException, Header, Request
from typing import Dict, Any, Optional
import hmac
import hashlib
import json
from datetime import datetime
import logging
import os
from keycloak_integration import (
    update_user_attributes,
    get_user_by_email
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# Lago webhook signature verification
LAGO_WEBHOOK_SECRET = os.getenv("LAGO_WEBHOOK_SECRET", "")


@router.post("/lago")
async def lago_webhook(
    request: Request,
    x_lago_signature: Optional[str] = Header(None)
):
    """
    Handle webhooks from Lago for subscription events

    Supported events:
    - subscription.created: New subscription created
    - subscription.updated: Subscription modified (upgrade/downgrade)
    - subscription.cancelled: Subscription cancelled
    - invoice.paid: Successful payment (reset usage counters)
    """
    body = await request.body()

    # Verify webhook signature
    if LAGO_WEBHOOK_SECRET and not verify_lago_signature(body, x_lago_signature):
        logger.warning("Invalid Lago webhook signature received")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received from Lago")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("webhook_type")

    logger.info(f"Received Lago webhook: {event_type}")

    # Handle different event types
    try:
        if event_type == "subscription.created":
            await handle_subscription_created(payload)
        elif event_type == "subscription.updated":
            await handle_subscription_updated(payload)
        elif event_type == "subscription.cancelled":
            await handle_subscription_cancelled(payload)
        elif event_type == "subscription.terminated":
            await handle_subscription_cancelled(payload)  # Same as cancelled
        elif event_type == "invoice.paid":
            await handle_invoice_paid(payload)
        elif event_type == "invoice.payment_status_updated":
            # Handle payment status changes
            invoice = payload.get("invoice", {})
            if invoice.get("payment_status") == "succeeded":
                await handle_invoice_paid(payload)
        else:
            logger.info(f"Unhandled webhook type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

    return {"status": "received", "event_type": event_type}


async def handle_subscription_created(payload: Dict[str, Any]):
    """Handle new subscription creation"""
    subscription = payload.get("subscription", {})
    customer = payload.get("customer", {})

    user_email = customer.get("email")
    plan_code = subscription.get("plan_code")
    status = subscription.get("status")
    subscription_id = subscription.get("lago_id")

    if not user_email:
        logger.error("No email found in subscription.created webhook")
        return

    logger.info(f"Creating subscription for {user_email}: {plan_code} ({status})")

    # Map plan codes to tier names
    tier = map_plan_to_tier(plan_code)

    # Update Authentik user attributes
    await update_user_subscription(
        user_email=user_email,
        tier=tier,
        status=status,
        subscription_id=subscription_id,
        plan_code=plan_code
    )


async def handle_subscription_updated(payload: Dict[str, Any]):
    """Handle subscription updates (upgrades, downgrades, status changes)"""
    subscription = payload.get("subscription", {})
    customer = payload.get("customer", {})

    user_email = customer.get("email")
    plan_code = subscription.get("plan_code")
    status = subscription.get("status")
    subscription_id = subscription.get("lago_id")

    if not user_email:
        logger.error("No email found in subscription.updated webhook")
        return

    logger.info(f"Updating subscription for {user_email}: {plan_code} ({status})")

    tier = map_plan_to_tier(plan_code)

    await update_user_subscription(
        user_email=user_email,
        tier=tier,
        status=status,
        subscription_id=subscription_id,
        plan_code=plan_code
    )


async def handle_subscription_cancelled(payload: Dict[str, Any]):
    """Handle subscription cancellation or termination"""
    subscription = payload.get("subscription", {})
    customer = payload.get("customer", {})

    user_email = customer.get("email")
    subscription_id = subscription.get("lago_id")

    if not user_email:
        logger.error("No email found in subscription.cancelled webhook")
        return

    logger.info(f"Cancelling subscription for {user_email}")

    # Downgrade to free tier
    await update_user_subscription(
        user_email=user_email,
        tier="free",
        status="cancelled",
        subscription_id=subscription_id,
        plan_code="free"
    )


async def handle_invoice_paid(payload: Dict[str, Any]):
    """Handle successful payment - reset usage counters for new billing period"""
    invoice = payload.get("invoice", {})
    customer = payload.get("customer", {})

    user_email = customer.get("email")

    if not user_email:
        logger.error("No email found in invoice.paid webhook")
        return

    logger.info(f"Processing successful payment for {user_email}")

    # Reset API call limits for the new billing period
    await reset_usage_counters(user_email)


async def update_user_subscription(
    user_email: str,
    tier: str,
    status: str,
    subscription_id: Optional[str] = None,
    plan_code: Optional[str] = None
):
    """
    Update user subscription in Keycloak user attributes

    Attributes set (as arrays per Keycloak requirements):
    - subscription_tier: Tier name (free, basic, professional, enterprise)
    - subscription_status: Status (active, cancelled, past_due, etc.)
    - subscription_id: Lago subscription ID
    - subscription_plan_code: Original plan code from Lago
    - subscription_updated_at: ISO timestamp
    - api_calls_used: Reset to 0 on subscription change
    """
    # Keycloak requires all attributes as arrays
    attributes = {
        "subscription_tier": [tier],
        "subscription_status": [status],
        "subscription_updated_at": [datetime.utcnow().isoformat()],
    }

    if subscription_id:
        attributes["subscription_id"] = [subscription_id]

    if plan_code:
        attributes["subscription_plan_code"] = [plan_code]

    # Reset usage on subscription change
    if status == "active":
        attributes["api_calls_used"] = ["0"]
        attributes["last_reset_date"] = [datetime.utcnow().isoformat()]

    try:
        await update_user_attributes(user_email, attributes)
        logger.info(f"Updated subscription for {user_email}: {tier} ({status})")
    except Exception as e:
        logger.error(f"Failed to update Keycloak attributes for {user_email}: {e}", exc_info=True)
        raise


async def reset_usage_counters(user_email: str):
    """Reset monthly usage counters after successful payment"""
    # Keycloak requires attributes as arrays
    attributes = {
        "api_calls_used": ["0"],
        "last_reset_date": [datetime.utcnow().isoformat()]
    }

    try:
        await update_user_attributes(user_email, attributes)
        logger.info(f"Reset usage counters for {user_email}")
    except Exception as e:
        logger.error(f"Failed to reset usage counters for {user_email}: {e}", exc_info=True)
        raise


# Removed: update_authentik_user_attributes - now using Keycloak integration module


def verify_lago_signature(body: bytes, signature: Optional[str]) -> bool:
    """
    Verify Lago webhook signature using HMAC SHA-256

    Args:
        body: Raw request body
        signature: X-Lago-Signature header value

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not LAGO_WEBHOOK_SECRET:
        # If no secret configured, skip verification (dev mode)
        if not LAGO_WEBHOOK_SECRET:
            logger.warning("LAGO_WEBHOOK_SECRET not configured - skipping signature verification")
        return True

    expected = hmac.new(
        LAGO_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def map_plan_to_tier(plan_code: str) -> str:
    """
    Map Lago plan code to subscription tier

    Args:
        plan_code: Plan code from Lago (e.g., "basic_monthly", "pro_annual")

    Returns:
        Tier name (free, basic, professional, enterprise)
    """
    # Normalize plan code
    plan_lower = plan_code.lower() if plan_code else ""

    # Map plan codes to tiers
    if "enterprise" in plan_lower or "unlimited" in plan_lower:
        return "enterprise"
    elif "pro" in plan_lower or "professional" in plan_lower:
        return "professional"
    elif "basic" in plan_lower or "starter" in plan_lower:
        return "basic"
    else:
        return "free"


# Health check endpoint for webhook
@router.get("/lago/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    keycloak_status = await keycloak_health_check()

    return {
        "status": "healthy",
        "webhook_endpoint": "/api/v1/webhooks/lago",
        "signature_verification": bool(LAGO_WEBHOOK_SECRET),
        "keycloak": keycloak_status
    }
