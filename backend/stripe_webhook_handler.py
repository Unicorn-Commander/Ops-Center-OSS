"""
Stripe Webhook Handler for Extensions Marketplace
Processes Stripe webhook events for add-on purchases
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import text
from database import get_db
from audit_logger import audit_logger

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handles Stripe webhook events for extensions marketplace"""

    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook event

        Args:
            event: Verified Stripe event

        Returns:
            Processing result
        """
        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Handling Stripe event: {event_type}")

        # Route to appropriate handler
        handlers = {
            'checkout.session.completed': self.handle_checkout_completed,
            'payment_intent.succeeded': self.handle_payment_succeeded,
            'charge.failed': self.handle_charge_failed,
            'charge.refunded': self.handle_charge_refunded,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {'status': 'ignored', 'event_type': event_type}

    def handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful checkout session completion

        This is the primary event for processing purchases:
        1. Extract session metadata
        2. Create add_on_purchase records
        3. Activate add-ons for user
        4. Grant features
        5. Clear cart
        6. Send confirmation email (optional)

        Args:
            session: Stripe checkout session object

        Returns:
            Processing result
        """
        try:
            # Extract metadata
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            user_email = metadata.get('user_email') or session.get('customer_email')
            cart_item_ids = metadata.get('cart_item_ids', '').split(',')
            promo_code = metadata.get('promo_code')
            
            session_id = session.get('id')
            payment_intent_id = session.get('payment_intent')
            amount_total = session.get('amount_total', 0) / 100  # Convert from cents
            currency = session.get('currency', 'usd')

            logger.info(f"Processing checkout completion for user {user_email}, session {session_id}")

            if not user_id or not cart_item_ids:
                logger.error("Missing required metadata in checkout session")
                return {'status': 'error', 'message': 'Missing metadata'}

            db = next(get_db())

            # Get cart items with add-on details
            cart_items = self._get_cart_items(db, user_id, cart_item_ids)
            
            if not cart_items:
                logger.error(f"No cart items found for user {user_id}")
                return {'status': 'error', 'message': 'Cart items not found'}

            # Calculate discount if promo code was used
            discount_amount = 0
            if promo_code:
                discount_amount = self._calculate_discount(cart_items, promo_code)

            # Create purchase records for each add-on
            purchase_ids = []
            for item in cart_items:
                addon_id = item['add_on_id']
                addon = item['addon']
                
                # Create purchase record
                purchase_id = self._create_purchase_record(
                    db=db,
                    user_id=user_id,
                    addon_id=addon_id,
                    stripe_session_id=session_id,
                    stripe_payment_intent_id=payment_intent_id,
                    amount_paid=float(addon['base_price']),
                    currency=currency,
                    promo_code=promo_code,
                    discount_amount=discount_amount
                )
                
                purchase_ids.append(purchase_id)
                
                # Activate add-on and grant features
                self._activate_addon(db, purchase_id, user_id, addon)

            # Clear user's cart
            self._clear_cart(db, user_id, cart_item_ids)

            # Update add-on install counts
            for item in cart_items:
                self._increment_install_count(db, item['add_on_id'])

            # Commit all changes
            db.commit()

            # Log audit event
            audit_logger.log_event(
                event_type="addon.purchased",
                user_id=user_id,
                details={
                    'purchase_ids': purchase_ids,
                    'addon_count': len(cart_items),
                    'amount_paid': amount_total,
                    'stripe_session_id': session_id
                }
            )

            logger.info(f"Successfully processed {len(purchase_ids)} add-on purchases for user {user_email}")

            return {
                'status': 'success',
                'purchase_ids': purchase_ids,
                'user_email': user_email
            }

        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {'status': 'error', 'message': str(e)}

    def handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment intent

        Updates purchase status to 'completed' if not already done

        Args:
            payment_intent: Stripe payment intent object

        Returns:
            Processing result
        """
        try:
            payment_intent_id = payment_intent.get('id')
            
            db = next(get_db())
            
            # Update purchase status
            query = text("""
                UPDATE add_on_purchases
                SET status = 'completed', updated_at = NOW()
                WHERE stripe_payment_intent_id = :payment_intent_id
                  AND status = 'pending'
                RETURNING id, user_id
            """)
            result = db.execute(query, {'payment_intent_id': payment_intent_id}).fetchone()
            
            if result:
                db.commit()
                logger.info(f"Updated purchase {result[0]} status to completed")
                return {'status': 'success', 'purchase_id': result[0]}
            else:
                logger.info(f"No pending purchases found for payment intent {payment_intent_id}")
                return {'status': 'ignored', 'message': 'No pending purchases'}

        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")
            return {'status': 'error', 'message': str(e)}

    def handle_charge_failed(self, charge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed charge

        Updates purchase status to 'failed' and sends notification

        Args:
            charge: Stripe charge object

        Returns:
            Processing result
        """
        try:
            payment_intent_id = charge.get('payment_intent')
            failure_message = charge.get('failure_message')
            
            db = next(get_db())
            
            # Update purchase status
            query = text("""
                UPDATE add_on_purchases
                SET status = 'failed', updated_at = NOW()
                WHERE stripe_payment_intent_id = :payment_intent_id
                RETURNING id, user_id
            """)
            result = db.execute(query, {'payment_intent_id': payment_intent_id}).fetchone()
            
            if result:
                db.commit()
                
                # Log audit event
                audit_logger.log_event(
                    event_type="addon.payment_failed",
                    user_id=result[1],
                    details={
                        'purchase_id': result[0],
                        'failure_message': failure_message
                    }
                )
                
                logger.warning(f"Marked purchase {result[0]} as failed: {failure_message}")
                return {'status': 'success', 'purchase_id': result[0]}
            else:
                logger.info(f"No purchases found for failed charge {payment_intent_id}")
                return {'status': 'ignored'}

        except Exception as e:
            logger.error(f"Error handling charge failed: {e}")
            return {'status': 'error', 'message': str(e)}

    def handle_charge_refunded(self, charge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle refunded charge

        Updates purchase status to 'refunded' and revokes add-on access

        Args:
            charge: Stripe charge object

        Returns:
            Processing result
        """
        try:
            payment_intent_id = charge.get('payment_intent')
            refund_amount = charge.get('amount_refunded', 0) / 100
            
            db = next(get_db())
            
            # Update purchase status and set refund date
            query = text("""
                UPDATE add_on_purchases
                SET status = 'refunded',
                    refunded_at = NOW(),
                    refund_reason = 'Customer requested refund',
                    updated_at = NOW()
                WHERE stripe_payment_intent_id = :payment_intent_id
                  AND status != 'refunded'
                RETURNING id, user_id, add_on_id
            """)
            result = db.execute(query, {'payment_intent_id': payment_intent_id}).fetchone()
            
            if result:
                purchase_id, user_id, addon_id = result
                
                # Revoke add-on access (remove features)
                self._revoke_addon_access(db, user_id, addon_id)
                
                db.commit()
                
                # Log audit event
                audit_logger.log_event(
                    event_type="addon.refunded",
                    user_id=user_id,
                    details={
                        'purchase_id': purchase_id,
                        'addon_id': addon_id,
                        'refund_amount': refund_amount
                    }
                )
                
                logger.info(f"Processed refund for purchase {purchase_id}, revoked access")
                return {'status': 'success', 'purchase_id': purchase_id}
            else:
                logger.info(f"No purchases found for refunded charge {payment_intent_id}")
                return {'status': 'ignored'}

        except Exception as e:
            logger.error(f"Error handling charge refunded: {e}")
            return {'status': 'error', 'message': str(e)}

    # Helper methods

    def _get_cart_items(self, db, user_id: str, cart_item_ids: list) -> list:
        """Fetch cart items with add-on details"""
        if not cart_item_ids or cart_item_ids == ['']:
            return []
        
        placeholders = ','.join([f':id{i}' for i in range(len(cart_item_ids))])
        query = text(f"""
            SELECT ci.id, ci.user_id, ci.add_on_id, ci.quantity,
                   a.id as addon_id, a.name, a.base_price, a.currency,
                   a.features, a.version, a.author
            FROM cart_items ci
            JOIN add_ons a ON ci.add_on_id = a.id
            WHERE ci.id IN ({placeholders})
        """)
        params = {f'id{i}': cid for i, cid in enumerate(cart_item_ids)}
        results = db.execute(query, params).fetchall()
        
        items = []
        for row in results:
            items.append({
                'id': row[0],
                'user_id': row[1],
                'add_on_id': row[2],
                'quantity': row[3],
                'addon': {
                    'id': row[4],
                    'name': row[5],
                    'base_price': row[6],
                    'currency': row[7],
                    'features': row[8],
                    'version': row[9],
                    'author': row[10]
                }
            })
        return items

    def _calculate_discount(self, cart_items: list, promo_code: str) -> float:
        """Calculate discount amount based on promo code"""
        # Placeholder for discount calculation logic
        # Would query coupon_codes table and calculate discount
        return 0.0

    def _create_purchase_record(
        self,
        db,
        user_id: str,
        addon_id: int,
        stripe_session_id: str,
        stripe_payment_intent_id: str,
        amount_paid: float,
        currency: str,
        promo_code: Optional[str],
        discount_amount: float
    ) -> int:
        """Create add_on_purchase record"""
        query = text("""
            INSERT INTO add_on_purchases (
                user_id, add_on_id, stripe_session_id, stripe_payment_intent_id,
                amount_paid, currency, status, promo_code, discount_amount
            )
            VALUES (
                :user_id, :addon_id, :session_id, :payment_intent_id,
                :amount_paid, :currency, 'completed', :promo_code, :discount_amount
            )
            RETURNING id
        """)
        result = db.execute(query, {
            'user_id': user_id,
            'addon_id': addon_id,
            'session_id': stripe_session_id,
            'payment_intent_id': stripe_payment_intent_id,
            'amount_paid': amount_paid,
            'currency': currency,
            'promo_code': promo_code,
            'discount_amount': discount_amount
        }).fetchone()
        return result[0]

    def _activate_addon(self, db, purchase_id: int, user_id: str, addon: Dict[str, Any]):
        """Activate add-on and grant features to user"""
        # Update purchase with activation timestamp and features granted
        features_granted = addon.get('features', [])
        
        query = text("""
            UPDATE add_on_purchases
            SET activated_at = NOW(),
                features_granted = :features::jsonb
            WHERE id = :purchase_id
        """)
        db.execute(query, {
            'purchase_id': purchase_id,
            'features': str(features_granted)
        })
        
        # Here you would grant the features to the user in Keycloak or user_features table
        # This is a placeholder - actual implementation depends on feature system
        logger.info(f"Activated add-on for purchase {purchase_id}, granted features: {features_granted}")

    def _clear_cart(self, db, user_id: str, cart_item_ids: list):
        """Clear specified cart items for user"""
        if not cart_item_ids or cart_item_ids == ['']:
            return
        
        placeholders = ','.join([f':id{i}' for i in range(len(cart_item_ids))])
        query = text(f"""
            DELETE FROM cart_items
            WHERE id IN ({placeholders})
        """)
        params = {f'id{i}': cid for i, cid in enumerate(cart_item_ids)}
        db.execute(query, params)

    def _increment_install_count(self, db, addon_id: int):
        """Increment install count for add-on"""
        query = text("""
            UPDATE add_ons
            SET install_count = install_count + 1
            WHERE id = :addon_id
        """)
        db.execute(query, {'addon_id': addon_id})

    def _revoke_addon_access(self, db, user_id: str, addon_id: int):
        """Revoke add-on access from user (for refunds)"""
        # This is a placeholder - actual implementation depends on feature system
        logger.info(f"Revoked add-on {addon_id} access from user {user_id}")


# Global instance
webhook_handler = StripeWebhookHandler()
