"""
Stripe Payment Integration for UC-1 Pro
Handles customer creation, subscriptions, and webhook processing
"""

import os
import logging
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx

# Import Keycloak integration for user management
from keycloak_integration import update_user_attributes, get_user_by_email

# Import universal credential helper
from get_credential import get_credential

logger = logging.getLogger(__name__)

# Initialize Stripe - read credentials from database first, then environment
STRIPE_SECRET_KEY = get_credential("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = get_credential("STRIPE_WEBHOOK_SECRET")
# Redirect back to signup-flow page after payment (success or cancel)
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://unicorncommander.ai/signup-flow.html?success=true")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://unicorncommander.ai/signup-flow.html?canceled=true")
LAGO_API_URL = os.getenv("LAGO_API_URL", "http://lago-api:3000")
LAGO_API_KEY = get_credential("LAGO_API_KEY")

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY


class StripeIntegration:
    """Handles all Stripe payment operations"""

    def __init__(self):
        self.api_key = STRIPE_SECRET_KEY
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
        stripe.api_key = self.api_key

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe customer

        Args:
            email: Customer email address
            name: Customer name
            metadata: Additional metadata to store with customer

        Returns:
            Stripe customer object or None on failure
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for {email}: {e}")
            return None

    async def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get Stripe customer by email

        Args:
            email: Customer email address

        Returns:
            Stripe customer object or None if not found
        """
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch customer for {email}: {e}")
            return None

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        customer_email: str,
        tier_name: str,
        billing_cycle: str = "monthly"
    ) -> Optional[str]:
        """
        Create a Stripe Checkout session

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription
            customer_email: Customer email
            tier_name: Subscription tier name
            billing_cycle: monthly or yearly

        Returns:
            Checkout session URL or None on failure
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=STRIPE_CANCEL_URL,
                metadata={
                    'customer_email': customer_email,
                    'user_email': customer_email,  # Duplicate for webhook compatibility
                    'tier_id': tier_name,  # Use tier_id for consistency
                    'tier_name': tier_name,
                    'billing_cycle': billing_cycle
                },
                subscription_data={
                    'metadata': {
                        'tier_id': tier_name,
                        'tier_name': tier_name,
                        'billing_cycle': billing_cycle
                    }
                }
            )
            logger.info(f"Created checkout session: {session.id} for {customer_email}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            return None

    async def create_customer_portal_session(
        self,
        customer_id: str
    ) -> Optional[str]:
        """
        Create a customer portal session for managing subscriptions

        Args:
            customer_id: Stripe customer ID

        Returns:
            Portal session URL or None on failure
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url="https://unicorncommander.ai/billing"
            )
            logger.info(f"Created portal session for customer: {customer_id}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            return None

    async def get_customer_payment_methods(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get customer's payment methods

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of payment method objects
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            return payment_methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch payment methods: {e}")
            return []

    async def get_customer_subscriptions(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get customer's active subscriptions

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of subscription objects
        """
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='all'
            )
            return subscriptions.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch subscriptions: {e}")
            return []

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> bool:
        """
        Cancel a subscription

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at period end; if False, cancel immediately

        Returns:
            True if successful, False otherwise
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.cancel(subscription_id)

            logger.info(f"Canceled subscription: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> bool:
        """
        Update subscription to a different price/tier

        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='always_invoice'
            )

            logger.info(f"Updated subscription {subscription_id} to price {new_price_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            return False

    async def sync_to_keycloak(
        self,
        email: str,
        tier: str,
        status: str,
        customer_id: str,
        subscription_id: Optional[str] = None,
        subscription_start: Optional[str] = None,
        subscription_end: Optional[str] = None
    ) -> bool:
        """
        Sync subscription data to Keycloak user attributes

        Args:
            email: User email
            tier: Subscription tier
            status: Subscription status
            customer_id: Stripe customer ID
            subscription_id: Stripe subscription ID
            subscription_start: Subscription start date
            subscription_end: Subscription end date

        Returns:
            True if successful, False otherwise
        """
        try:
            attributes = {
                "subscription_tier": [tier],
                "subscription_status": [status],
                "stripe_customer_id": [customer_id]
            }

            if subscription_id:
                attributes["stripe_subscription_id"] = [subscription_id]
            if subscription_start:
                attributes["subscription_start_date"] = [subscription_start]
            if subscription_end:
                attributes["subscription_end_date"] = [subscription_end]

            success = await update_user_attributes(email, attributes)

            if success:
                logger.info(f"Synced subscription to Keycloak for {email}: {tier} ({status})")
            else:
                logger.error(f"Failed to sync subscription to Keycloak for {email}")

            return success
        except Exception as e:
            logger.error(f"Error syncing to Keycloak: {e}")
            return False

    async def sync_to_lago(
        self,
        email: str,
        tier: str,
        customer_id: str,
        subscription_id: Optional[str] = None
    ) -> bool:
        """
        Sync subscription data to Lago billing platform

        Args:
            email: User email
            tier: Subscription tier
            customer_id: Stripe customer ID
            subscription_id: Stripe subscription ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create or update customer in Lago
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LAGO_API_URL}/api/v1/customers",
                    headers={
                        "Authorization": f"Bearer {LAGO_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "customer": {
                            "external_id": customer_id,
                            "email": email,
                            "name": email,
                            "billing_configuration": {
                                "payment_provider": "stripe",
                                "provider_customer_id": customer_id
                            },
                            "metadata": {
                                "tier": tier,
                                "stripe_subscription_id": subscription_id or ""
                            }
                        }
                    },
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Synced customer to Lago: {email}")
                    return True
                else:
                    logger.error(f"Failed to sync to Lago: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error syncing to Lago: {e}")
            return False

    async def process_webhook_event(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Process Stripe webhook event

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Dict with processing result
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            logger.info(f"Processing webhook event: {event['type']}")

            # Handle different event types
            event_type = event['type']
            event_data = event['data']['object']

            if event_type == 'checkout.session.completed':
                return await self._handle_checkout_completed(event_data)

            elif event_type == 'customer.subscription.created':
                return await self._handle_subscription_created(event_data)

            elif event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event_data)

            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event_data)

            elif event_type == 'invoice.paid':
                return await self._handle_invoice_paid(event_data)

            elif event_type == 'invoice.payment_failed':
                return await self._handle_invoice_payment_failed(event_data)

            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return {"status": "error", "message": "Invalid signature"}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout session"""
        customer_email = session.get('customer_email') or session.get('metadata', {}).get('customer_email')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        tier_name = session.get('metadata', {}).get('tier_name', 'trial')

        logger.info(f"Checkout completed for {customer_email}, tier: {tier_name}")

        # Sync to Keycloak
        await self.sync_to_keycloak(
            email=customer_email,
            tier=tier_name,
            status='active',
            customer_id=customer_id,
            subscription_id=subscription_id
        )

        # Sync to Lago
        await self.sync_to_lago(
            email=customer_email,
            tier=tier_name,
            customer_id=customer_id,
            subscription_id=subscription_id
        )

        return {"status": "success", "customer_email": customer_email}

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription creation"""
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')

        # Get customer details
        customer = await self.get_customer_by_email("")  # We need to get by customer_id
        customer_obj = stripe.Customer.retrieve(customer_id)
        customer_email = customer_obj.get('email')

        tier_name = subscription.get('metadata', {}).get('tier_name', 'trial')
        start_date = datetime.fromtimestamp(subscription.get('current_period_start')).isoformat()
        end_date = datetime.fromtimestamp(subscription.get('current_period_end')).isoformat()

        logger.info(f"Subscription created: {subscription_id} for {customer_email}")

        # Sync to Keycloak
        await self.sync_to_keycloak(
            email=customer_email,
            tier=tier_name,
            status='active',
            customer_id=customer_id,
            subscription_id=subscription_id,
            subscription_start=start_date,
            subscription_end=end_date
        )

        return {"status": "success", "subscription_id": subscription_id}

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update"""
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        status = subscription.get('status')

        customer_obj = stripe.Customer.retrieve(customer_id)
        customer_email = customer_obj.get('email')

        tier_name = subscription.get('metadata', {}).get('tier_name', 'trial')
        end_date = datetime.fromtimestamp(subscription.get('current_period_end')).isoformat()

        logger.info(f"Subscription updated: {subscription_id} for {customer_email}, status: {status}")

        # Sync to Keycloak
        await self.sync_to_keycloak(
            email=customer_email,
            tier=tier_name,
            status=status,
            customer_id=customer_id,
            subscription_id=subscription_id,
            subscription_end=end_date
        )

        return {"status": "success", "subscription_id": subscription_id}

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')

        customer_obj = stripe.Customer.retrieve(customer_id)
        customer_email = customer_obj.get('email')

        logger.info(f"Subscription deleted: {subscription_id} for {customer_email}")

        # Downgrade to trial tier
        await self.sync_to_keycloak(
            email=customer_email,
            tier='trial',
            status='cancelled',
            customer_id=customer_id,
            subscription_id=subscription_id
        )

        return {"status": "success", "subscription_id": subscription_id}

    async def _handle_invoice_paid(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment"""
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')

        customer_obj = stripe.Customer.retrieve(customer_id)
        customer_email = customer_obj.get('email')

        logger.info(f"Invoice paid for {customer_email}, subscription: {subscription_id}")

        # Update subscription status to active
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            tier_name = subscription.get('metadata', {}).get('tier_name', 'trial')

            await self.sync_to_keycloak(
                email=customer_email,
                tier=tier_name,
                status='active',
                customer_id=customer_id,
                subscription_id=subscription_id
            )

        return {"status": "success", "customer_email": customer_email}

    async def _handle_invoice_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed invoice payment"""
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')

        customer_obj = stripe.Customer.retrieve(customer_id)
        customer_email = customer_obj.get('email')

        logger.warning(f"Invoice payment failed for {customer_email}, subscription: {subscription_id}")

        # Mark subscription as past_due
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            tier_name = subscription.get('metadata', {}).get('tier_name', 'trial')

            await self.sync_to_keycloak(
                email=customer_email,
                tier=tier_name,
                status='past_due',
                customer_id=customer_id,
                subscription_id=subscription_id
            )

        return {"status": "success", "customer_email": customer_email}


# Global instance
stripe_integration = StripeIntegration()
