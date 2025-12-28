"""
Stripe Integration for Extensions Marketplace
Handles one-time payments for add-on purchases
"""

import os
import logging
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from sqlalchemy import text
from database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Stripe with credentials from database or environment
try:
    from get_credential import get_credential
    STRIPE_SECRET_KEY = get_credential("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = get_credential("STRIPE_WEBHOOK_SECRET")
except Exception as e:
    logger.warning(f"Could not load Stripe credentials from database, using environment: {e}")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://your-domain.com/extensions/success")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://your-domain.com/extensions/cancelled")

# Configure Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    logger.error("STRIPE_SECRET_KEY not configured!")


class StripeExtensionsIntegration:
    """Handles Stripe payment operations for extensions marketplace"""

    def __init__(self):
        self.api_key = STRIPE_SECRET_KEY
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
        
        if self.api_key:
            stripe.api_key = self.api_key

    def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        cart_items: List[Dict[str, Any]],
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for add-on purchases

        Args:
            user_id: User ID from Keycloak
            user_email: User email address
            cart_items: List of cart items with add-on details
            promo_code: Optional promo code for discounts

        Returns:
            Dict with checkout_url and session_id
        """
        try:
            if not stripe.api_key:
                raise ValueError("Stripe API key not configured")

            # Build line items from cart
            line_items = []
            cart_item_ids = []
            
            for item in cart_items:
                addon = item.get('addon')
                quantity = item.get('quantity', 1)
                
                if not addon:
                    continue
                
                cart_item_ids.append(str(item.get('id')))
                
                line_items.append({
                    'price_data': {
                        'currency': addon.get('currency', 'usd'),
                        'product_data': {
                            'name': addon['name'],
                            'description': addon.get('description', ''),
                            'images': [addon['icon_url']] if addon.get('icon_url') else [],
                        },
                        'unit_amount': int(float(addon['base_price']) * 100),  # Convert to cents
                    },
                    'quantity': quantity,
                })

            if not line_items:
                raise ValueError("No valid items in cart")

            # Apply promo code if provided
            discount_coupons = []
            if promo_code:
                # Validate promo code in database
                coupon = self._validate_promo_code(promo_code)
                if coupon and coupon.get('stripe_coupon_id'):
                    discount_coupons = [{'coupon': coupon['stripe_coupon_id']}]

            # Create Stripe Checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',  # One-time payment
                customer_email=user_email,
                client_reference_id=user_id,
                metadata={
                    'user_id': user_id,
                    'user_email': user_email,
                    'cart_item_ids': ','.join(cart_item_ids),
                    'promo_code': promo_code or '',
                },
                success_url=f"{STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=STRIPE_CANCEL_URL,
                discounts=discount_coupons if discount_coupons else None,
                allow_promotion_codes=True,  # Allow users to enter promo codes in Stripe UI
            )

            logger.info(f"Created Stripe checkout session {session.id} for user {user_email}")

            return {
                'checkout_url': session.url,
                'session_id': session.id,
                'success': True
            }

        except stripe.error.CardError as e:
            logger.error(f"Card error: {e}")
            return {'success': False, 'error': 'payment_declined', 'message': str(e)}
        except stripe.error.RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            return {'success': False, 'error': 'rate_limit', 'message': 'Too many requests, please try again later'}
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request: {e}")
            return {'success': False, 'error': 'invalid_request', 'message': str(e)}
        except stripe.error.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            return {'success': False, 'error': 'auth_error', 'message': 'Payment system unavailable'}
        except stripe.error.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            return {'success': False, 'error': 'connection_error', 'message': 'Please try again'}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {'success': False, 'error': 'payment_error', 'message': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            return {'success': False, 'error': 'unknown_error', 'message': str(e)}

    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str
    ) -> Optional[stripe.Event]:
        """
        Verify Stripe webhook signature

        Args:
            payload: Raw webhook payload
            sig_header: Stripe-Signature header

        Returns:
            Verified Stripe Event or None
        """
        try:
            if not self.webhook_secret:
                raise ValueError("Webhook secret not configured")

            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve checkout session details

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Session object or None
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return dict(session)
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def get_payment_intent(self, payment_intent_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve payment intent details

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            PaymentIntent object or None
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return dict(payment_intent)
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent {payment_intent_id}: {e}")
            return None

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Amount to refund in cents (None for full refund)
            reason: Refund reason

        Returns:
            Refund result
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}
            
            if amount:
                refund_params['amount'] = amount
            
            if reason:
                refund_params['reason'] = reason

            refund = stripe.Refund.create(**refund_params)
            
            logger.info(f"Created refund {refund.id} for payment {payment_intent_id}")
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount,
                'status': refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {e}")
            return {'success': False, 'error': str(e)}

    def _validate_promo_code(self, promo_code: str) -> Optional[Dict[str, Any]]:
        """
        Validate promo code in database

        Args:
            promo_code: Promo code string

        Returns:
            Coupon details or None
        """
        try:
            db = next(get_db())
            query = text("""
                SELECT id, code, discount_type, discount_value, stripe_coupon_id,
                       valid_from, valid_until, max_uses, current_uses, is_active
                FROM coupon_codes
                WHERE code = :code
                  AND is_active = true
                  AND (valid_from IS NULL OR valid_from <= NOW())
                  AND (valid_until IS NULL OR valid_until >= NOW())
                  AND (max_uses IS NULL OR current_uses < max_uses)
            """)
            result = db.execute(query, {'code': promo_code}).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'code': result[1],
                    'discount_type': result[2],
                    'discount_value': result[3],
                    'stripe_coupon_id': result[4]
                }
            return None

        except Exception as e:
            logger.error(f"Error validating promo code: {e}")
            return None


# Global instance
stripe_extensions = StripeExtensionsIntegration()
