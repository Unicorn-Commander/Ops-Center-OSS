"""
Extensions Marketplace - Purchase API
Phase 1: Purchase and checkout endpoints with Stripe integration
"""

import os
import asyncpg
import stripe
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extensions", tags=["extensions-purchase"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_...")

# Database connection configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "unicorn"),
    "password": os.getenv("POSTGRES_PASSWORD", "unicorn"),
    "database": os.getenv("POSTGRES_DB", "unicorn_db")
}


async def get_db_connection():
    """Create database connection"""
    return await asyncpg.connect(**DB_CONFIG)


async def get_current_user(request: Request) -> str:
    """Get current authenticated user ID from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # TODO: Integrate with actual Keycloak/auth system
    # For now, return test user ID
    return "test-user-123"


# Pydantic models
class CheckoutRequest(BaseModel):
    promo_code: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PromoCodeRequest(BaseModel):
    code: str


class ActivatePurchaseResponse(BaseModel):
    success: bool
    features_granted: List[str]


# ============================================================================
# ENDPOINT 1: Create Checkout Session
# ============================================================================

@router.post("/checkout")
async def create_checkout(
    checkout_data: CheckoutRequest,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Create Stripe Checkout Session from cart

    Returns:
        - checkout_url: URL to redirect user to Stripe
        - session_id: Stripe session ID
    """
    conn = await get_db_connection()
    try:
        # Get cart items with addon details
        cart_query = """
            SELECT
                c.id,
                c.quantity,
                a.name,
                a.base_price,
                a.id as addon_id,
                a.category,
                a.features
            FROM cart_items c
            JOIN add_ons a ON c.add_on_id = a.id
            WHERE c.user_id = $1
        """
        cart_items = await conn.fetch(cart_query, user_id)

        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Build Stripe line items
        line_items = []
        total_amount = 0

        for item in cart_items:
            unit_amount = int(float(item['base_price']) * 100)  # Convert to cents
            total_amount += unit_amount * item['quantity']

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item['name'],
                        'description': f"{item['category']} extension",
                        'metadata': {
                            'addon_id': str(item['addon_id']),
                            'category': item['category']
                        }
                    },
                    'unit_amount': unit_amount,
                },
                'quantity': item['quantity'],
            })

        # Apply promo code if provided
        discount_amount = 0
        if checkout_data.promo_code:
            promo_query = """
                SELECT discount_type, discount_value, max_uses, current_uses, expires_at
                FROM promotional_codes
                WHERE code = $1 AND is_active = TRUE
            """
            promo = await conn.fetchrow(promo_query, checkout_data.promo_code)

            if promo:
                # Validate promo code
                if promo['expires_at'] and promo['expires_at'] < datetime.now():
                    raise HTTPException(status_code=400, detail="Promo code expired")

                if promo['max_uses'] and promo['current_uses'] >= promo['max_uses']:
                    raise HTTPException(status_code=400, detail="Promo code max uses reached")

                # Calculate discount
                if promo['discount_type'] == 'percentage':
                    discount_amount = int(total_amount * float(promo['discount_value']) / 100)
                elif promo['discount_type'] == 'fixed':
                    discount_amount = int(float(promo['discount_value']) * 100)

        # Prepare success and cancel URLs
        success_url = checkout_data.success_url or 'https://your-domain.com/extensions/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = checkout_data.cancel_url or 'https://your-domain.com/extensions/cancelled'

        # Create Stripe session
        session_params = {
            'payment_method_types': ['card'],
            'line_items': line_items,
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'client_reference_id': user_id,
            'metadata': {
                'user_id': user_id,
                'promo_code': checkout_data.promo_code or '',
                'cart_item_count': str(len(cart_items))
            },
        }

        # Add discount if applicable
        if discount_amount > 0:
            session_params['discounts'] = [{
                'coupon': checkout_data.promo_code
            }]

        session = stripe.checkout.Session.create(**session_params)

        # Log checkout session creation
        logger.info(f"Created Stripe checkout session {session.id} for user {user_id}")

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "total_amount": total_amount / 100,  # Convert back to dollars
            "discount_amount": discount_amount / 100 if discount_amount > 0 else None,
            "publishable_key": STRIPE_PUBLISHABLE_KEY
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in create_checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        await conn.close()


# ============================================================================
# ENDPOINT 2: Get Purchase History
# ============================================================================

@router.get("/purchases")
async def get_purchases(
    request: Request,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """
    Get user's purchase history

    Query Parameters:
        - status: Filter by purchase status (pending, completed, failed, refunded)
        - limit: Number of results (default 20)
        - offset: Pagination offset (default 0)
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT
                p.id,
                p.amount,
                p.currency,
                p.status,
                p.purchased_at,
                p.stripe_payment_id,
                a.name as addon_name,
                a.category,
                a.features,
                a.version
            FROM add_on_purchases p
            JOIN add_ons a ON p.add_on_id = a.id
            WHERE p.user_id = $1
        """
        params = [user_id]

        # Add status filter if provided
        if status:
            query += f" AND p.status = ${len(params)+1}"
            params.append(status)

        # Add ordering and pagination
        query += f" ORDER BY p.purchased_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([limit, offset])

        purchases = await conn.fetch(query, *params)

        # Convert to dict and format dates
        result = []
        for p in purchases:
            purchase_dict = dict(p)
            purchase_dict['purchased_at'] = purchase_dict['purchased_at'].isoformat() if purchase_dict['purchased_at'] else None
            purchase_dict['amount'] = float(purchase_dict['amount'])
            result.append(purchase_dict)

        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM add_on_purchases WHERE user_id = $1"
        count_params = [user_id]
        if status:
            count_query += " AND status = $2"
            count_params.append(status)

        total_count = await conn.fetchval(count_query, *count_params)

        return {
            "purchases": result,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        }

    except Exception as e:
        logger.error(f"Error in get_purchases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        await conn.close()


# ============================================================================
# ENDPOINT 3: Activate Purchase
# ============================================================================

@router.post("/purchase/{purchase_id}/activate", response_model=ActivatePurchaseResponse)
async def activate_purchase(
    purchase_id: str,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Activate a purchase and grant features to user

    This endpoint:
    - Verifies purchase ownership
    - Grants addon features to user
    - Creates user_add_ons record
    """
    conn = await get_db_connection()
    try:
        # Get purchase details with addon features
        purchase_query = """
            SELECT
                p.id,
                p.add_on_id,
                p.user_id,
                p.status,
                a.features,
                a.name,
                a.category
            FROM add_on_purchases p
            JOIN add_ons a ON p.add_on_id = a.id
            WHERE p.id = $1 AND p.user_id = $2
        """
        purchase = await conn.fetchrow(purchase_query, purchase_id, user_id)

        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")

        if purchase['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Purchase cannot be activated. Current status: {purchase['status']}"
            )

        # Parse features from JSONB
        features_data = purchase['features']
        if isinstance(features_data, str):
            features_data = json.loads(features_data)

        feature_list = features_data.get('features', []) if isinstance(features_data, dict) else []
        granted_features = []

        # Create or update user_add_ons record
        insert_query = """
            INSERT INTO user_add_ons (user_id, add_on_id, status, purchased_at)
            VALUES ($1, $2, 'active', NOW())
            ON CONFLICT (user_id, add_on_id)
            DO UPDATE SET
                status = 'active',
                updated_at = NOW()
            RETURNING id
        """
        user_addon_id = await conn.fetchval(insert_query, user_id, purchase['add_on_id'])

        # Grant individual features
        for feature_key in feature_list:
            granted_features.append(feature_key)

        # Update purchase to mark as activated
        update_query = """
            UPDATE add_on_purchases
            SET status = 'completed'
            WHERE id = $1
        """
        await conn.execute(update_query, purchase_id)

        logger.info(f"Activated purchase {purchase_id} for user {user_id}. Granted features: {granted_features}")

        return {
            "success": True,
            "features_granted": granted_features
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in activate_purchase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        await conn.close()


# ============================================================================
# ENDPOINT 4: Get Active Add-ons
# ============================================================================

@router.get("/active")
async def get_active_addons(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    List user's currently active add-ons

    Returns all add-ons with status='active' for the user
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT
                ua.id,
                ua.purchased_at,
                ua.expires_at,
                ua.status,
                a.id as addon_id,
                a.name,
                a.description,
                a.category,
                a.features,
                a.version,
                a.icon_url
            FROM user_add_ons ua
            JOIN add_ons a ON ua.add_on_id = a.id
            WHERE ua.user_id = $1 AND ua.status = 'active'
            ORDER BY ua.purchased_at DESC
        """
        active_addons = await conn.fetch(query, user_id)

        # Format results
        result = []
        for addon in active_addons:
            addon_dict = dict(addon)
            addon_dict['purchased_at'] = addon_dict['purchased_at'].isoformat() if addon_dict['purchased_at'] else None
            addon_dict['expires_at'] = addon_dict['expires_at'].isoformat() if addon_dict['expires_at'] else None

            # Parse features if string
            if isinstance(addon_dict['features'], str):
                addon_dict['features'] = json.loads(addon_dict['features'])

            result.append(addon_dict)

        return {
            "active_addons": result,
            "total_count": len(result)
        }

    except Exception as e:
        logger.error(f"Error in get_active_addons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        await conn.close()


# ============================================================================
# ENDPOINT 5: Stripe Webhook Handler
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events

    Events handled:
    - checkout.session.completed: Process successful payment
    - payment_intent.succeeded: Confirm payment
    - payment_intent.payment_failed: Handle failed payment
    """
    payload = await request.body()

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event['type']
    logger.info(f"Received Stripe webhook: {event_type}")

    # Handle checkout.session.completed
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        payment_intent = session.get('payment_intent')
        amount_total = session.get('amount_total', 0) / 100  # Convert cents to dollars

        conn = await get_db_connection()
        try:
            # Get cart items for this user
            cart_query = """
                SELECT add_on_id, quantity, user_id
                FROM cart_items
                WHERE user_id = $1
            """
            cart_items = await conn.fetch(cart_query, user_id)

            if not cart_items:
                logger.warning(f"No cart items found for user {user_id}")
                return {"received": True}

            # Create purchase records for each cart item
            for item in cart_items:
                # Get addon base price
                price_query = "SELECT base_price FROM add_ons WHERE id = $1"
                base_price = await conn.fetchval(price_query, item['add_on_id'])

                purchase_query = """
                    INSERT INTO add_on_purchases
                    (user_id, add_on_id, amount, currency, status, stripe_payment_id, purchased_at)
                    VALUES ($1, $2, $3, 'usd', 'completed', $4, NOW())
                    RETURNING id
                """
                purchase_id = await conn.fetchval(
                    purchase_query,
                    user_id,
                    item['add_on_id'],
                    base_price * item['quantity'],
                    payment_intent
                )

                logger.info(f"Created purchase {purchase_id} for addon {item['add_on_id']}")

            # Clear cart after successful payment
            await conn.execute("DELETE FROM cart_items WHERE user_id = $1", user_id)

            # Update promo code usage if one was used
            promo_code = session.get('metadata', {}).get('promo_code')
            if promo_code:
                promo_update = """
                    UPDATE promotional_codes
                    SET current_uses = current_uses + 1
                    WHERE code = $1
                """
                await conn.execute(promo_update, promo_code)

            logger.info(f"Successfully processed payment for user {user_id}. Amount: ${amount_total}")

        except Exception as e:
            logger.error(f"Error processing checkout.session.completed: {str(e)}")
            raise
        finally:
            await conn.close()

    # Handle payment_intent.payment_failed
    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        payment_id = payment_intent.get('id')

        conn = await get_db_connection()
        try:
            # Update purchase status to failed
            update_query = """
                UPDATE add_on_purchases
                SET status = 'failed'
                WHERE stripe_payment_id = $1
            """
            await conn.execute(update_query, payment_id)

            logger.warning(f"Payment failed: {payment_id}")
        finally:
            await conn.close()

    return {"received": True}


# ============================================================================
# ENDPOINT 6: Cancel Purchase (Phase 2 placeholder)
# ============================================================================

@router.post("/purchase/{purchase_id}/cancel")
async def cancel_purchase(
    purchase_id: str,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Cancel a purchase/subscription

    NOTE: Full cancellation logic will be implemented in Phase 2
    """
    conn = await get_db_connection()
    try:
        # Verify purchase exists and belongs to user
        purchase_query = """
            SELECT id, status, add_on_id
            FROM add_on_purchases
            WHERE id = $1 AND user_id = $2
        """
        purchase = await conn.fetchrow(purchase_query, purchase_id, user_id)

        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")

        # Phase 2: Implement full cancellation logic
        # - Handle refunds via Stripe
        # - Update subscription status
        # - Revoke features
        # - Send cancellation email

        return {
            "success": False,
            "message": "Cancellation available in Phase 2",
            "purchase_id": purchase_id,
            "current_status": purchase['status']
        }
    finally:
        await conn.close()


# ============================================================================
# ENDPOINT 7: Get Invoice (Phase 2 placeholder)
# ============================================================================

@router.get("/invoice/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Download invoice PDF

    NOTE: Invoice generation will be implemented in Phase 2
    """
    # Phase 2: Implement invoice generation
    # - Generate PDF from purchase data
    # - Include company details
    # - Format currency properly
    # - Return as downloadable file

    raise HTTPException(
        status_code=501,
        detail="Invoice download available in Phase 2"
    )


# ============================================================================
# ENDPOINT 8: Apply Promo Code
# ============================================================================

@router.post("/apply-promo")
async def apply_promo_code(
    promo_request: PromoCodeRequest,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Validate and apply promo code to cart

    Returns:
        - valid: Whether code is valid
        - discount_type: 'percentage' or 'fixed'
        - discount_value: Discount amount or percentage
    """
    conn = await get_db_connection()
    try:
        # Fetch promo code details
        promo_query = """
            SELECT
                code,
                discount_type,
                discount_value,
                max_uses,
                current_uses,
                expires_at,
                is_active,
                description
            FROM promotional_codes
            WHERE code = $1
        """
        promo = await conn.fetchrow(promo_query, promo_request.code)

        if not promo:
            raise HTTPException(status_code=404, detail="Promo code not found")

        # Validate promo code is active
        if not promo['is_active']:
            raise HTTPException(status_code=400, detail="Promo code is inactive")

        # Check expiry date
        if promo['expires_at'] and promo['expires_at'] < datetime.now():
            raise HTTPException(status_code=400, detail="Promo code has expired")

        # Check max uses
        if promo['max_uses'] and promo['current_uses'] >= promo['max_uses']:
            raise HTTPException(status_code=400, detail="Promo code has reached maximum uses")

        # Get current cart total for discount preview
        cart_query = """
            SELECT SUM(c.quantity * a.base_price) as total
            FROM cart_items c
            JOIN add_ons a ON c.add_on_id = a.id
            WHERE c.user_id = $1
        """
        cart_total = await conn.fetchval(cart_query, user_id)

        if not cart_total:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Calculate discount amount
        discount_amount = 0
        if promo['discount_type'] == 'percentage':
            discount_amount = float(cart_total) * float(promo['discount_value']) / 100
        elif promo['discount_type'] == 'fixed':
            discount_amount = float(promo['discount_value'])

        # Ensure discount doesn't exceed total
        discount_amount = min(discount_amount, float(cart_total))

        logger.info(f"Applied promo code {promo_request.code} for user {user_id}. Discount: ${discount_amount}")

        return {
            "valid": True,
            "code": promo['code'],
            "discount_type": promo['discount_type'],
            "discount_value": float(promo['discount_value']),
            "discount_amount": round(discount_amount, 2),
            "cart_total": float(cart_total),
            "final_total": round(float(cart_total) - discount_amount, 2),
            "description": promo['description']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in apply_promo_code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        await conn.close()


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/purchase/health")
async def purchase_health_check():
    """Health check for purchase API"""
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "stripe": "configured" if stripe.api_key else "not configured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
