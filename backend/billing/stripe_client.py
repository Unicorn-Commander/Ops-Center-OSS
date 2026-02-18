"""
Stripe Client for Billing Operations
Provides high-level interface to Stripe API for subscription and payment management
"""
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class StripeClient:
    """
    Stripe integration client for UC-1 Pro billing

    Features:
    - Subscription management
    - Invoice retrieval
    - Payment method management
    - Customer statistics
    - Revenue reporting

    Usage:
        stripe_client = StripeClient()

        # Get customer subscription
        subscription = await stripe_client.get_customer_subscription(customer_id)

        # Get customer invoices
        invoices = await stripe_client.get_customer_invoices(customer_id, limit=10)

        # Admin: Get revenue stats
        stats = await stripe_client.get_revenue_stats()
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stripe client

        Args:
            api_key: Stripe secret key (or from env STRIPE_SECRET_KEY)
        """
        self.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY")

        # Initialize Stripe SDK
        try:
            import stripe
            self.stripe = stripe
            if self.api_key:
                self.stripe.api_key = self.api_key
                self.enabled = True
            else:
                self.enabled = False
                logger.warning("Stripe API key not configured - billing features disabled")
        except ImportError:
            self.stripe = None
            self.enabled = False
            logger.error("Stripe module not installed - run: pip install stripe")

    async def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """
        Find Stripe customer by email

        Args:
            email: Customer email address

        Returns:
            Customer object or None if not found
        """
        if not self.enabled:
            return None

        try:
            customers = self.stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching customer by email {email}: {e}")
            return None

    async def get_customer_subscription(self, customer_id: str) -> Optional[Dict]:
        """
        Get active subscription for a customer

        Args:
            customer_id: Stripe customer ID

        Returns:
            Subscription data or None if no active subscription
        """
        if not self.enabled:
            return None

        try:
            subscriptions = self.stripe.Subscription.list(
                customer=customer_id,
                status="active",
                limit=1
            )

            if subscriptions.data:
                sub = subscriptions.data[0]

                # Get tier from metadata
                tier = sub.metadata.get("tier", "trial")

                # Get price info
                price_item = sub["items"].data[0] if sub.get("items") else None
                amount = price_item.plan.amount / 100 if price_item else 0  # Convert cents to dollars
                interval = price_item.plan.interval if price_item else "month"

                return {
                    "id": sub.id,
                    "tier": tier,
                    "status": sub.status,
                    "current_period_start": datetime.fromtimestamp(sub.current_period_start, tz=timezone.utc).isoformat(),
                    "current_period_end": datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc).isoformat(),
                    "cancel_at_period_end": sub.cancel_at_period_end,
                    "amount": amount,
                    "interval": interval,
                    "currency": price_item.plan.currency if price_item else "usd"
                }

            return None
        except Exception as e:
            logger.error(f"Error fetching subscription for customer {customer_id}: {e}")
            return None

    async def get_customer_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get invoices for a customer

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return

        Returns:
            List of invoice objects
        """
        if not self.enabled:
            return []

        try:
            invoices = self.stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )

            result = []
            for invoice in invoices.data:
                result.append({
                    "id": invoice.id,
                    "number": invoice.number,
                    "amount_due": invoice.amount_due / 100,  # Convert cents to dollars
                    "amount_paid": invoice.amount_paid / 100,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "created": datetime.fromtimestamp(invoice.created, tz=timezone.utc).isoformat(),
                    "due_date": datetime.fromtimestamp(invoice.due_date, tz=timezone.utc).isoformat() if invoice.due_date else None,
                    "paid": invoice.paid,
                    "invoice_pdf": invoice.invoice_pdf,
                    "hosted_invoice_url": invoice.hosted_invoice_url
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching invoices for customer {customer_id}: {e}")
            return []

    async def get_customer_payment_methods(self, customer_id: str) -> List[Dict]:
        """
        Get payment methods for a customer

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of payment method objects
        """
        if not self.enabled:
            return []

        try:
            payment_methods = self.stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )

            result = []
            for pm in payment_methods.data:
                result.append({
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year
                    } if pm.card else None,
                    "created": datetime.fromtimestamp(pm.created, tz=timezone.utc).isoformat()
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching payment methods for customer {customer_id}: {e}")
            return []

    async def get_all_customers(self, limit: int = 100) -> List[Dict]:
        """
        Get all customers (admin only)

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of customer objects
        """
        if not self.enabled:
            return []

        try:
            customers = self.stripe.Customer.list(limit=limit)

            result = []
            for customer in customers.data:
                result.append({
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "created": datetime.fromtimestamp(customer.created, tz=timezone.utc).isoformat(),
                    "metadata": customer.metadata
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching all customers: {e}")
            return []

    async def get_all_subscriptions(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all subscriptions (admin only)

        Args:
            status: Filter by status (active, canceled, etc.)
            limit: Maximum number of subscriptions to return

        Returns:
            List of subscription objects
        """
        if not self.enabled:
            return []

        try:
            params = {"limit": limit}
            if status:
                params["status"] = status

            subscriptions = self.stripe.Subscription.list(**params)

            result = []
            for sub in subscriptions.data:
                price_item = sub["items"].data[0] if sub.get("items") else None
                amount = price_item.plan.amount / 100 if price_item else 0

                result.append({
                    "id": sub.id,
                    "customer": sub.customer,
                    "tier": sub.metadata.get("tier", "unknown"),
                    "status": sub.status,
                    "amount": amount,
                    "currency": price_item.plan.currency if price_item else "usd",
                    "interval": price_item.plan.interval if price_item else "month",
                    "current_period_end": datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc).isoformat(),
                    "cancel_at_period_end": sub.cancel_at_period_end
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching all subscriptions: {e}")
            return []

    async def get_revenue_stats(self) -> Dict:
        """
        Get revenue statistics (admin only)

        Returns:
            Revenue statistics including:
            - Total customers
            - Active subscriptions
            - Monthly recurring revenue
            - Subscription breakdown by tier
        """
        if not self.enabled:
            return {
                "total_customers": 0,
                "active_subscriptions": 0,
                "trial_subscriptions": 0,
                "monthly_revenue": 0,
                "tier_breakdown": {}
            }

        try:
            # Get all active subscriptions
            subscriptions = await self.get_all_subscriptions(status="active")

            # Calculate statistics
            total_customers = len(await self.get_all_customers())
            active_subs = len(subscriptions)
            trial_subs = len([s for s in subscriptions if s.get("tier") == "trial"])

            # Calculate MRR (Monthly Recurring Revenue)
            monthly_revenue = 0
            tier_breakdown = {}

            for sub in subscriptions:
                amount = sub.get("amount", 0)
                interval = sub.get("interval", "month")
                tier = sub.get("tier", "unknown")

                # Convert to monthly amount
                if interval == "year":
                    monthly_amount = amount / 12
                elif interval == "week":
                    monthly_amount = amount * 4.33  # Average weeks per month
                else:  # month
                    monthly_amount = amount

                monthly_revenue += monthly_amount

                # Track by tier
                if tier not in tier_breakdown:
                    tier_breakdown[tier] = {"count": 0, "revenue": 0}
                tier_breakdown[tier]["count"] += 1
                tier_breakdown[tier]["revenue"] += monthly_amount

            return {
                "total_customers": total_customers,
                "active_subscriptions": active_subs,
                "trial_subscriptions": trial_subs,
                "monthly_revenue": round(monthly_revenue, 2),
                "tier_breakdown": tier_breakdown
            }
        except Exception as e:
            logger.error(f"Error calculating revenue stats: {e}")
            return {
                "total_customers": 0,
                "active_subscriptions": 0,
                "trial_subscriptions": 0,
                "monthly_revenue": 0,
                "tier_breakdown": {},
                "error": str(e)
            }

    async def get_recent_charges(self, limit: int = 20) -> List[Dict]:
        """
        Get recent charges (admin only)

        Args:
            limit: Maximum number of charges to return

        Returns:
            List of charge objects
        """
        if not self.enabled:
            return []

        try:
            charges = self.stripe.Charge.list(limit=limit)

            result = []
            for charge in charges.data:
                result.append({
                    "id": charge.id,
                    "amount": charge.amount / 100,
                    "currency": charge.currency,
                    "status": charge.status,
                    "customer": charge.customer,
                    "description": charge.description,
                    "created": datetime.fromtimestamp(charge.created, tz=timezone.utc).isoformat(),
                    "paid": charge.paid,
                    "refunded": charge.refunded
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching recent charges: {e}")
            return []

    # ========================================================================
    # NEW METHODS: Epic 2.4 - Self-Service Upgrades
    # ========================================================================

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        customer_email: str,
        tier_name: str,
        billing_cycle: str = "monthly",
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a Stripe Checkout session for subscription upgrade.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription
            customer_email: Customer email
            tier_name: Subscription tier name
            billing_cycle: monthly or yearly
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after canceled payment

        Returns:
            Checkout session URL or None on failure
        """
        if not self.enabled:
            logger.error("Stripe not enabled")
            return None

        # Default URLs
        if not success_url:
            success_url = os.getenv(
                "STRIPE_SUCCESS_URL",
                "https://unicorncommander.ai/billing/success"
            )
        if not cancel_url:
            cancel_url = os.getenv(
                "STRIPE_CANCEL_URL",
                "https://unicorncommander.ai/billing/canceled"
            )

        try:
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={
                    'customer_email': customer_email,
                    'user_email': customer_email,  # Duplicate for compatibility
                    'tier_id': tier_name,
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

        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return None

    async def verify_checkout_session(self, session_id: str) -> Optional[Dict]:
        """
        Verify Stripe checkout session completed successfully.

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Session details if paid, None otherwise
        """
        if not self.enabled:
            return None

        try:
            session = self.stripe.checkout.Session.retrieve(session_id)

            if session.payment_status != "paid":
                logger.warning(f"Session {session_id} not paid: {session.payment_status}")
                return None

            return {
                "id": session.id,
                "customer": session.customer,
                "subscription": session.subscription,
                "payment_status": session.payment_status,
                "customer_email": session.customer_details.email if session.customer_details else None,
                "tier_name": session.metadata.get("tier_name"),
                "billing_cycle": session.metadata.get("billing_cycle")
            }

        except Exception as e:
            logger.error(f"Failed to verify checkout session {session_id}: {e}")
            return None

    async def calculate_proration_preview(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Optional[Dict]:
        """
        Get proration preview from Stripe for subscription change.

        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID

        Returns:
            Proration details or None on failure
        """
        if not self.enabled:
            return None

        try:
            # Get current subscription
            subscription = self.stripe.Subscription.retrieve(subscription_id)

            # Calculate proration using Stripe's upcoming invoice preview
            upcoming_invoice = self.stripe.Invoice.upcoming(
                customer=subscription.customer,
                subscription=subscription_id,
                subscription_items=[{
                    'id': subscription['items'].data[0].id,
                    'price': new_price_id,
                }],
                subscription_proration_behavior='always_invoice'
            )

            # Extract proration details
            proration_amount = 0
            for line in upcoming_invoice.lines.data:
                if line.proration:
                    proration_amount += line.amount

            return {
                "proration_amount": proration_amount / 100,  # Convert cents to dollars
                "total_amount": upcoming_invoice.total / 100,
                "currency": upcoming_invoice.currency,
                "period_start": datetime.fromtimestamp(
                    upcoming_invoice.period_start,
                    tz=timezone.utc
                ).isoformat(),
                "period_end": datetime.fromtimestamp(
                    upcoming_invoice.period_end,
                    tz=timezone.utc
                ).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to calculate proration: {e}")
            return None

    async def update_subscription_tier(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> bool:
        """
        Update subscription to a different price/tier.

        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)

            self.stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='always_invoice'
            )

            logger.info(f"Updated subscription {subscription_id} to price {new_price_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update subscription: {e}")
            return False

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> bool:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at period end; if False, cancel immediately

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if at_period_end:
                subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = self.stripe.Subscription.cancel(subscription_id)

            logger.info(f"Canceled subscription: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            name: Customer name
            metadata: Additional metadata to store with customer

        Returns:
            Stripe customer object or None on failure
        """
        if not self.enabled:
            return None

        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer

        except Exception as e:
            logger.error(f"Failed to create Stripe customer for {email}: {e}")
            return None
