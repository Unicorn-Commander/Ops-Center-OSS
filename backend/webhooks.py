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

# Suite marker — the Stripe account is SHARED across suites (unicorn-commander,
# magicunicorn, majiks, ...) and Stripe fans every event out to all webhooks.
# The ops-center webhook ONLY acts on events carrying this marker, so another
# suite's purchase can never trigger ops-center paid-org provisioning.
OPS_CENTER_SUITE = os.getenv("OPS_CENTER_STRIPE_SUITE", "unicorn-commander")

# Email service
email_service = EmailNotificationService()


async def _resolve_org_by_email(email: str) -> Optional[str]:
    """Map a Stripe customer email -> the org_<uuid> the gateway/Lago use."""
    if not email:
        return None
    try:
        user = await get_user_by_email(email)
        if not user:
            return None
        user_id = user.get("id")
        return user.get("attributes", {}).get("org_id", [f"org_{user_id}"])[0]
    except Exception as e:
        logger.error(f"org resolve by email failed for {email}: {e}")
        return None


@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """UNIFIED Stripe webhook — verify signature once, dispatch by event type.
    Point ONE Stripe endpoint at https://<host>/api/v1/webhooks/stripe with the
    events below. checkout.session.completed -> provision_paid_org (full paid-org
    provisioning incl the cloud hard cap); customer.subscription.deleted ->
    downgrade_org (re-cap the key, stop cloud spend); invoice.payment_failed ->
    log (Stripe retries; we downgrade only on final subscription.deleted).
    Failure-isolated: returns a status, never 500s on dispatch errors.
    """
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Invalid Stripe payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    etype = event.get("type")
    obj = event.get("data", {}).get("object", {})
    from paid_org_provisioning import provision_paid_org, downgrade_org
    try:
        if etype == "checkout.session.completed":
            md = obj.get("metadata", {}) or {}
            # Suite guard: ignore checkouts that aren't ops-center's (shared account).
            if (md.get("suite") or "") != OPS_CENTER_SUITE:
                return {"status": "ignored", "reason": f"other suite ({md.get('suite')})"}
            tier = md.get("tier_name") or md.get("tier_id") or md.get("plan_code")
            email = obj.get("customer_email") or (obj.get("customer_details", {}) or {}).get("email")
            if obj.get("payment_status") != "paid":
                return {"status": "ignored", "reason": f"payment_status={obj.get('payment_status')}"}
            if not tier or not email:
                return {"status": "ignored", "reason": "missing tier/email metadata"}
            org_id = await _resolve_org_by_email(email)
            if not org_id:
                return {"status": "error", "reason": "org not found for " + email}
            r = await provision_paid_org(org_id, tier, email=email, source="stripe")
            return {"status": "provisioned", "org_id": org_id, "result": r}

        if etype == "customer.subscription.deleted":
            # Suite guard: only downgrade our own subscriptions (shared account).
            if ((obj.get("metadata", {}) or {}).get("suite") or "") != OPS_CENTER_SUITE:
                return {"status": "ignored", "reason": "other suite (cancel)"}
            email = (obj.get("customer_details", {}) or {}).get("email")
            if not email:
                # subscription objects carry only the customer id — fetch the email
                try:
                    cust = stripe.Customer.retrieve(obj.get("customer"))
                    email = cust.get("email")
                except Exception as e:
                    logger.error(f"could not retrieve Stripe customer {obj.get('customer')}: {e}")
            org_id = await _resolve_org_by_email(email)
            if not org_id:
                return {"status": "ignored", "reason": "org not found (cancel)"}
            r = await downgrade_org(org_id, source="stripe-canceled")
            return {"status": "downgraded", "org_id": org_id, "result": r}

        if etype == "invoice.payment_failed":
            logger.warning("Stripe payment_failed: customer=%s sub=%s (Stripe retries; downgrade on subscription.deleted)",
                           obj.get("customer"), obj.get("subscription"))
            return {"status": "noted"}

        return {"status": "ignored", "event_type": etype}
    except Exception as e:
        logger.error(f"Stripe webhook dispatch error ({etype}): {e}")
        return {"status": "error", "detail": str(e)}


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
    tier_name = metadata.get('tier_name') or metadata.get('tier_id') or metadata.get('plan_code')

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

        # Get current subscription (for the upgrade email + to terminate the old Lago sub).
        current_subscription = await get_subscription(org_id)
        old_tier = "trial"
        if current_subscription:
            old_tier = current_subscription.get("plan_code", "").split("_")[0]
            lago_subscription_id = current_subscription.get("lago_id")
            if lago_subscription_id:
                try:
                    await terminate_subscription(org_id, lago_subscription_id)
                    logger.info(f"Terminated old subscription {lago_subscription_id}")
                except Exception as e:
                    logger.error(f"Failed to terminate old subscription: {e}")

        # Full, correct paid-org provisioning — the SAME path manual onboarding uses:
        # set tier + Lago subscription on the tier's REAL plan + gateway key cloud
        # HARD CAP + funded wallet. Reads pricing from subscription_tiers (no
        # hardcoded {tier}_monthly codes). org_id/tier forms are normalized inside.
        from paid_org_provisioning import provision_paid_org
        prov = await provision_paid_org(org_id, tier_code=tier_name, email=customer_email, source="stripe")
        logger.info(f"Stripe self-serve provisioned org {org_id} -> {tier_name}: {prov}")
        if prov.get("error"):
            logger.error(f"provision_paid_org error for org {org_id}: {prov['error']}")

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
