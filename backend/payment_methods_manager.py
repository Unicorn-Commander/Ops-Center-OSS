"""
Payment Methods Manager Service
Handles Stripe payment method operations for UC-Cloud billing
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import stripe
from stripe.error import StripeError

logger = logging.getLogger(__name__)


class PaymentMethodsManager:
    """Manages payment methods via Stripe API"""

    def __init__(self, lago_client=None):
        """
        Initialize PaymentMethodsManager

        Args:
            lago_client: Lago API client for customer lookups
        """
        self.lago = lago_client
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        if not stripe.api_key:
            logger.warning("STRIPE_SECRET_KEY not configured")

    async def get_stripe_customer_id(self, user_email: str) -> Optional[str]:
        """
        Get Stripe customer ID from Lago customer

        Args:
            user_email: User's email address (external_id in Lago)

        Returns:
            Stripe customer ID or None if not found
        """
        try:
            if not self.lago:
                logger.error("Lago client not configured")
                return None

            # Query Lago for customer
            customer = await self.lago.get_customer(user_email)

            if not customer:
                logger.warning(f"Customer not found in Lago: {user_email}")
                return None

            # Get Stripe customer ID from Lago metadata
            stripe_id = customer.get("stripe_customer", {}).get("stripe_customer_id")

            if not stripe_id:
                logger.warning(f"Stripe customer ID not found for: {user_email}")
                return None

            return stripe_id

        except Exception as e:
            logger.error(f"Error fetching Stripe customer ID: {e}")
            return None

    async def list_payment_methods(
        self,
        stripe_customer_id: str
    ) -> Dict[str, any]:
        """
        List all payment methods for a customer

        Args:
            stripe_customer_id: Stripe customer ID

        Returns:
            Dict with payment_methods list and default_payment_method_id
        """
        try:
            # Fetch customer to get default payment method
            customer = stripe.Customer.retrieve(stripe_customer_id)
            default_pm_id = customer.get("invoice_settings", {}).get("default_payment_method")

            # Fetch all payment methods
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type="card",
                limit=100
            )

            # Format payment methods
            formatted_methods = []
            for pm in payment_methods.data:
                card = pm.card

                # Check if expiring soon (within 2 months)
                exp_date = datetime(card.exp_year, card.exp_month, 1)
                expires_soon = (exp_date - datetime.now()).days < 60

                formatted_methods.append({
                    "id": pm.id,
                    "brand": card.brand,  # visa, mastercard, amex, discover
                    "last4": card.last4,
                    "exp_month": card.exp_month,
                    "exp_year": card.exp_year,
                    "is_default": pm.id == default_pm_id,
                    "expires_soon": expires_soon,
                    "country": card.country,
                    "funding": card.funding,  # credit, debit, prepaid
                    "created": pm.created
                })

            return {
                "payment_methods": formatted_methods,
                "default_payment_method_id": default_pm_id,
                "count": len(formatted_methods)
            }

        except StripeError as e:
            logger.error(f"Stripe error listing payment methods: {e}")
            raise Exception(f"Failed to retrieve payment methods: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing payment methods: {e}")
            raise

    async def create_setup_intent(
        self,
        stripe_customer_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a SetupIntent for adding a new payment method

        Args:
            stripe_customer_id: Stripe customer ID
            metadata: Optional metadata to attach

        Returns:
            Dict with client_secret and setup_intent_id
        """
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=stripe_customer_id,
                payment_method_types=["card"],
                metadata=metadata or {},
                usage="off_session"  # Allow charging without customer present
            )

            return {
                "client_secret": setup_intent.client_secret,
                "setup_intent_id": setup_intent.id
            }

        except StripeError as e:
            logger.error(f"Stripe error creating SetupIntent: {e}")
            raise Exception(f"Failed to create payment setup: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating SetupIntent: {e}")
            raise

    async def set_default_payment_method(
        self,
        stripe_customer_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Set a payment method as the default for invoices

        Args:
            stripe_customer_id: Stripe customer ID
            payment_method_id: Payment method ID to set as default

        Returns:
            True if successful
        """
        try:
            # Verify payment method belongs to customer
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            if pm.customer != stripe_customer_id:
                raise Exception("Payment method does not belong to customer")

            # Update customer's default payment method
            stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )

            logger.info(
                f"Set default payment method {payment_method_id} "
                f"for customer {stripe_customer_id}"
            )
            return True

        except StripeError as e:
            logger.error(f"Stripe error setting default payment method: {e}")
            raise Exception(f"Failed to set default payment method: {str(e)}")
        except Exception as e:
            logger.error(f"Error setting default payment method: {e}")
            raise

    async def remove_payment_method(
        self,
        stripe_customer_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Remove a payment method from a customer

        Args:
            stripe_customer_id: Stripe customer ID
            payment_method_id: Payment method ID to remove

        Returns:
            True if successful

        Raises:
            Exception if it's the only payment method with active subscription
        """
        try:
            # Check if customer has active subscription
            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id,
                status="active",
                limit=1
            )

            # Check if this is the only payment method
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type="card",
                limit=2
            )

            if subscriptions.data and len(payment_methods.data) <= 1:
                raise Exception(
                    "Cannot remove the last payment method while subscription is active. "
                    "Please add another payment method first."
                )

            # Verify payment method belongs to customer
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            if pm.customer != stripe_customer_id:
                raise Exception("Payment method does not belong to customer")

            # Detach payment method
            stripe.PaymentMethod.detach(payment_method_id)

            logger.info(
                f"Removed payment method {payment_method_id} "
                f"from customer {stripe_customer_id}"
            )
            return True

        except StripeError as e:
            logger.error(f"Stripe error removing payment method: {e}")
            raise Exception(f"Failed to remove payment method: {str(e)}")
        except Exception as e:
            logger.error(f"Error removing payment method: {e}")
            raise

    async def update_billing_address(
        self,
        stripe_customer_id: str,
        address: Dict[str, str]
    ) -> bool:
        """
        Update billing address for a customer

        Args:
            stripe_customer_id: Stripe customer ID
            address: Dict with line1, line2, city, state, postal_code, country

        Returns:
            True if successful
        """
        try:
            # Update in Stripe
            stripe.Customer.modify(
                stripe_customer_id,
                address={
                    "line1": address.get("line1", ""),
                    "line2": address.get("line2"),
                    "city": address.get("city", ""),
                    "state": address.get("state"),
                    "postal_code": address.get("postal_code", ""),
                    "country": address.get("country", "US")
                }
            )

            # TODO: Update in Lago if needed
            # if self.lago:
            #     await self.lago.update_customer_address(...)

            logger.info(f"Updated billing address for customer {stripe_customer_id}")
            return True

        except StripeError as e:
            logger.error(f"Stripe error updating billing address: {e}")
            raise Exception(f"Failed to update billing address: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating billing address: {e}")
            raise

    async def get_upcoming_invoice(
        self,
        stripe_customer_id: str
    ) -> Optional[Dict]:
        """
        Get the upcoming invoice for a customer

        Args:
            stripe_customer_id: Stripe customer ID

        Returns:
            Dict with invoice details or None if no upcoming invoice
        """
        try:
            # Retrieve upcoming invoice
            invoice = stripe.Invoice.upcoming(customer=stripe_customer_id)

            if not invoice:
                return None

            # Get default payment method
            customer = stripe.Customer.retrieve(stripe_customer_id)
            default_pm_id = customer.get("invoice_settings", {}).get("default_payment_method")

            payment_method_info = None
            if default_pm_id:
                pm = stripe.PaymentMethod.retrieve(default_pm_id)
                if pm.type == "card":
                    payment_method_info = {
                        "id": pm.id,
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year
                    }

            return {
                "amount_due": invoice.amount_due,  # in cents
                "amount_remaining": invoice.amount_remaining,
                "currency": invoice.currency,
                "next_payment_attempt": invoice.next_payment_attempt,
                "period_start": invoice.period_start,
                "period_end": invoice.period_end,
                "default_payment_method": payment_method_info,
                "lines": [
                    {
                        "description": line.description,
                        "amount": line.amount,
                        "quantity": line.quantity,
                        "period_start": line.period.start if line.period else None,
                        "period_end": line.period.end if line.period else None
                    }
                    for line in invoice.lines.data
                ],
                "subtotal": invoice.subtotal,
                "tax": invoice.tax,
                "total": invoice.total
            }

        except stripe.error.InvalidRequestError as e:
            # No upcoming invoice (no active subscription)
            logger.info(f"No upcoming invoice for customer {stripe_customer_id}")
            return None
        except StripeError as e:
            logger.error(f"Stripe error fetching upcoming invoice: {e}")
            raise Exception(f"Failed to retrieve upcoming invoice: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching upcoming invoice: {e}")
            raise

    async def get_payment_method_details(
        self,
        payment_method_id: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a payment method

        Args:
            payment_method_id: Payment method ID

        Returns:
            Dict with payment method details
        """
        try:
            pm = stripe.PaymentMethod.retrieve(payment_method_id)

            if pm.type != "card":
                return None

            card = pm.card

            return {
                "id": pm.id,
                "type": pm.type,
                "brand": card.brand,
                "last4": card.last4,
                "exp_month": card.exp_month,
                "exp_year": card.exp_year,
                "country": card.country,
                "funding": card.funding,
                "fingerprint": card.fingerprint,
                "created": pm.created,
                "customer": pm.customer
            }

        except StripeError as e:
            logger.error(f"Stripe error fetching payment method details: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching payment method details: {e}")
            return None
