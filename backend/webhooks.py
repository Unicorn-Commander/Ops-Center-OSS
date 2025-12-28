"""
Webhook Handlers for Stripe and Lago Events
Handles subscription lifecycle events from payment providers
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import logging
import os
import stripe

from lago_integration import (
    create_subscription,
    terminate_subscription,
    get_subscription,
    update_subscription_plan
)
from keycloak_integration import update_user_attributes, get_user_by_email
from email_notifications import EmailNotificationService

# Import universal credential helper
from get_credential import get_credential

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# Initialize Stripe - read credentials from database first, then environment
STRIPE_WEBHOOK_SECRET = get_credential("STRIPE_WEBHOOK_SECRET")
stripe.api_key = get_credential("STRIPE_SECRET_KEY")

# Email service
email_service = EmailNotificationService()


@router.post("/stripe/checkout-completed")
async def handle_stripe_checkout_completed(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe checkout.session.completed webhook.
    Triggered when user completes payment for subscription upgrade.

    Flow:
    1. Verify webhook signature
    2. Extract session data (customer, tier, subscription)
    3. Update subscription in Lago
    4. Update user tier in Keycloak
    5. Send confirmation email
    """
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Get raw payload
    payload = await request.body()

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error parsing webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Extract event data
    event_type = event['type']
    if event_type != 'checkout.session.completed':
        logger.warning(f"Unexpected event type: {event_type}")
        return {"status": "ignored", "event_type": event_type}

    session = event['data']['object']

    # Extract important fields
    customer_id = session.get('customer')
    customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email')
    subscription_id = session.get('subscription')
    payment_status = session.get('payment_status')

    # Get tier from metadata
    metadata = session.get('metadata', {})
    tier_name = metadata.get('tier_name') or metadata.get('tier_id')

    logger.info(f"Processing checkout completed: {customer_email} -> {tier_name}")

    # Verify payment completed
    if payment_status != 'paid':
        logger.warning(f"Payment not completed for {customer_email}: {payment_status}")
        return {
            "status": "pending",
            "message": "Payment not yet completed",
            "payment_status": payment_status
        }

    if not customer_email or not tier_name:
        logger.error(f"Missing required data: email={customer_email}, tier={tier_name}")
        raise HTTPException(status_code=400, detail="Missing customer email or tier")

    try:
        # Get user from Keycloak
        user = await get_user_by_email(customer_email)
        if not user:
            logger.error(f"User not found in Keycloak: {customer_email}")
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")
        org_id = user.get("attributes", {}).get("org_id", [f"org_{user_id}"])[0]

        # Get current subscription
        current_subscription = await get_subscription(org_id)
        old_tier = "trial"

        if current_subscription:
            old_tier = current_subscription.get("plan_code", "").split("_")[0]

            # Terminate old subscription in Lago
            lago_subscription_id = current_subscription.get("lago_id")
            if lago_subscription_id:
                await terminate_subscription(org_id, lago_subscription_id)
                logger.info(f"Terminated old subscription {lago_subscription_id}")

        # Create new subscription in Lago
        lago_plan_code = f"{tier_name}_monthly"
        try:
            new_subscription = await create_subscription(org_id, lago_plan_code)
            logger.info(f"Created Lago subscription for {org_id}: {new_subscription.get('lago_id')}")
        except Exception as e:
            logger.error(f"Failed to create Lago subscription: {e}")
            # Continue even if Lago fails - user paid, so honor the upgrade

        # Update user tier in Keycloak
        await update_user_attributes(
            customer_email,
            {
                "subscription_tier": [tier_name],
                "subscription_status": ["active"],
                "stripe_customer_id": [customer_id],
                "stripe_subscription_id": [subscription_id]
            }
        )
        logger.info(f"Updated Keycloak attributes for {customer_email}")

        # Send upgrade confirmation email (don't fail if email fails)
        try:
            await email_service.send_tier_upgrade_notification(
                user_id=user_id,
                old_tier=old_tier,
                new_tier=tier_name
            )
            logger.info(f"Sent upgrade email to {customer_email}")
        except Exception as e:
            logger.error(f"Failed to send upgrade email: {e}")

        # Record subscription change in database
        try:
            from sqlalchemy import text
            from database.connection import get_db_connection
            from datetime import datetime

            async with get_db_connection() as db:
                change_id = f"{org_id}_{int(datetime.now().timestamp())}"

                await db.execute(
                    text("""
                        INSERT INTO subscription_changes
                        (id, user_id, old_tier, new_tier, change_type, effective_date, stripe_session_id, lago_subscription_id)
                        VALUES (:id, :user_id, :old_tier, :new_tier, 'upgrade', NOW(), :session_id, :lago_id)
                    """),
                    {
                        "id": change_id,
                        "user_id": user_id,
                        "old_tier": old_tier,
                        "new_tier": tier_name,
                        "session_id": session.get("id"),
                        "lago_id": new_subscription.get("lago_id") if 'new_subscription' in locals() else None
                    }
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to record subscription change: {e}")

        return {
            "status": "success",
            "customer_email": customer_email,
            "old_tier": old_tier,
            "new_tier": tier_name,
            "message": "Subscription upgraded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing checkout webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/stripe/subscription-updated")
async def handle_stripe_subscription_updated(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe customer.subscription.updated webhook.
    Triggered when subscription changes (status, plan, etc).
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Error verifying webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event['type']
    if event_type != 'customer.subscription.updated':
        return {"status": "ignored", "event_type": event_type}

    subscription = event['data']['object']

    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    status = subscription.get('status')

    metadata = subscription.get('metadata', {})
    tier_name = metadata.get('tier_name') or metadata.get('tier_id', 'trial')

    logger.info(f"Processing subscription updated: {subscription_id}, status={status}, tier={tier_name}")

    try:
        # Get customer details from Stripe
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer.get('email')

        if not customer_email:
            logger.error(f"No email for customer {customer_id}")
            return {"status": "error", "message": "Customer email not found"}

        # Update Keycloak attributes
        await update_user_attributes(
            customer_email,
            {
                "subscription_status": [status],
                "subscription_tier": [tier_name]
            }
        )

        logger.info(f"Updated subscription status for {customer_email}: {status}")

        return {
            "status": "success",
            "customer_email": customer_email,
            "subscription_id": subscription_id,
            "new_status": status
        }

    except Exception as e:
        logger.error(f"Error processing subscription update webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lago/subscription-updated")
async def handle_lago_subscription_updated(request: Request):
    """
    Handle Lago subscription.updated webhook.
    Triggered when subscription changes in Lago.

    Note: Lago webhook signature verification would go here.
    """
    try:
        payload = await request.json()

        logger.info(f"Received Lago webhook: {payload.get('webhook_type')}")

        # Extract subscription data
        subscription_data = payload.get('subscription', {})
        external_customer_id = subscription_data.get('external_customer_id')
        plan_code = subscription_data.get('plan_code')
        status = subscription_data.get('status')

        if not external_customer_id:
            logger.warning("No external_customer_id in Lago webhook")
            return {"status": "ignored"}

        # Log the change
        logger.info(f"Lago subscription updated: org={external_customer_id}, plan={plan_code}, status={status}")

        # In production, you might sync this back to Keycloak or trigger other actions

        return {
            "status": "success",
            "org_id": external_customer_id,
            "plan_code": plan_code
        }

    except Exception as e:
        logger.error(f"Error processing Lago webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
