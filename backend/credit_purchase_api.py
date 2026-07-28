"""
Credit Purchase API - One-time credit purchases via Stripe

Provides endpoints for:
- Listing available credit packages
- Creating Stripe checkout sessions
- Processing purchase webhooks
- Viewing purchase history

Author: Backend Team Lead
Date: November 12, 2025
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal
import logging
import os
import stripe
import asyncpg

# Import credit system components
from credit_system import credit_manager, CreditError
from audit_logger import audit_logger
from email_notifications import EmailNotificationService

# Import authentication
from credit_api import get_current_user_from_request, require_admin_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing/credits", tags=["credit-purchases"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_CREDITS", os.getenv("STRIPE_WEBHOOK_SECRET"))

# Email service
email_service = EmailNotificationService()

# Database connection
async def get_db_connection():
    """Get database connection"""
    pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db"),
        min_size=2,
        max_size=10
    )
    return pool


# ============================================================================
# Pydantic Models
# ============================================================================

class CreditPackage(BaseModel):
    """Credit package information"""
    id: str
    package_code: str
    package_name: str
    description: Optional[str]
    credits: int
    price_usd: Decimal
    discount_percentage: int
    is_active: bool
    stripe_price_id: Optional[str]
    stripe_product_id: Optional[str]

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PurchaseRequest(BaseModel):
    """Request to purchase credits"""
    package_code: str = Field(..., description="Package code to purchase")
    success_url: Optional[str] = Field(None, description="URL to redirect after success")
    cancel_url: Optional[str] = Field(None, description="URL to redirect after cancel")


class PurchaseResponse(BaseModel):
    """Response from purchase request"""
    checkout_url: str = Field(..., description="Stripe checkout URL")
    session_id: str = Field(..., description="Stripe checkout session ID")


class PurchaseHistory(BaseModel):
    """Purchase history record"""
    id: str
    package_name: str
    amount_credits: Decimal
    amount_paid: Decimal
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    stripe_payment_id: Optional[str]

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/packages", response_model=List[CreditPackage])
async def list_credit_packages(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user_from_request)
):
    """
    List available credit packages

    Returns all active credit packages with pricing and discount information.
    Admin users can optionally see inactive packages.
    """
    try:
        pool = await get_db_connection()

        async with pool.acquire() as conn:
            if include_inactive and current_user.get("role") == "admin":
                query = "SELECT * FROM credit_packages ORDER BY display_order, credits"
            else:
                query = "SELECT * FROM credit_packages WHERE is_active = TRUE ORDER BY display_order, credits"

            rows = await conn.fetch(query)

            packages = []
            for row in rows:
                packages.append(CreditPackage(
                    id=str(row["id"]),
                    package_code=row["package_code"],
                    package_name=row["package_name"],
                    description=row["description"],
                    credits=row["credits"],
                    price_usd=row["price_usd"],
                    discount_percentage=row["discount_percentage"],
                    is_active=row["is_active"],
                    stripe_price_id=row["stripe_price_id"],
                    stripe_product_id=row["stripe_product_id"]
                ))

        await pool.close()

        logger.info(f"User {current_user.get('user_id')} listed {len(packages)} credit packages")
        return packages

    except asyncpg.UndefinedTableError:
        logger.warning("credit_packages table missing; returning empty package list")
        return []
    except Exception as e:
        logger.error(f"Failed to list credit packages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list packages: {str(e)}")


@router.post("/purchase", response_model=PurchaseResponse)
async def create_purchase_checkout(
    request: PurchaseRequest,
    current_user: dict = Depends(get_current_user_from_request)
):
    """
    Create Stripe checkout session for credit purchase

    Creates a one-time payment checkout session and returns the URL for redirect.
    On successful payment, credits are automatically added via webhook.
    """
    user_id = current_user.get("user_id")
    user_email = current_user.get("email", "unknown@example.com")

    try:
        pool = await get_db_connection()

        async with pool.acquire() as conn:
            # Get package details
            package = await conn.fetchrow(
                "SELECT * FROM credit_packages WHERE package_code = $1 AND is_active = TRUE",
                request.package_code
            )

            if not package:
                raise HTTPException(status_code=404, detail=f"Package '{request.package_code}' not found or inactive")

            # Determine URLs
            base_url = os.getenv("EXTERNAL_URL", "https://unicorncommander.ai")
            success_url = request.success_url or f"{base_url}/admin/credits?purchase=success"
            cancel_url = request.cancel_url or f"{base_url}/admin/credits?purchase=cancelled"

            # Create or get Stripe customer
            stripe_customer = None
            try:
                customers = stripe.Customer.list(email=user_email, limit=1)
                if customers.data:
                    stripe_customer = customers.data[0]
                else:
                    stripe_customer = stripe.Customer.create(
                        email=user_email,
                        metadata={
                            "user_id": user_id,
                            "source": "ops-center"
                        }
                    )
            except stripe.error.StripeError as e:
                logger.warning(f"Stripe customer lookup/create failed: {e}, proceeding without customer")

            # Create Stripe checkout session
            line_items = [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(float(package["price_usd"]) * 100),  # Convert to cents
                    "product_data": {
                        "name": package["package_name"],
                        "description": f"{package['credits']:,} credits - {package['description']}",
                        "metadata": {
                            "package_code": package["package_code"],
                            "credits": str(package["credits"])
                        }
                    }
                },
                "quantity": 1
            }]

            checkout_params = {
                "payment_method_types": ["card"],
                "line_items": line_items,
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": user_id,
                    "package_code": package["package_code"],
                    "credits": str(package["credits"]),
                    "source": "credit_purchase"
                }
            }

            if stripe_customer:
                checkout_params["customer"] = stripe_customer.id
            else:
                checkout_params["customer_email"] = user_email

            checkout_session = stripe.checkout.Session.create(**checkout_params)

            # Create purchase record
            purchase_id = await conn.fetchval(
                """
                INSERT INTO credit_purchases (
                    user_id, package_name, amount_credits, amount_paid,
                    stripe_checkout_session_id, status, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                user_id,
                package["package_name"],
                Decimal(str(package["credits"])),
                package["price_usd"],
                checkout_session.id,
                "pending",
                {
                    "package_code": package["package_code"],
                    "discount_percentage": package["discount_percentage"]
                }
            )

            # Audit log
            await audit_logger.log_credit_purchase_initiated(
                user_id=user_id,
                purchase_id=str(purchase_id),
                package_name=package["package_name"],
                amount=float(package["price_usd"]),
                credits=package["credits"]
            )

        await pool.close()

        logger.info(f"Created checkout session for user {user_id}: {checkout_session.id}")

        return PurchaseResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")


@router.get("/history", response_model=List[PurchaseHistory])
async def get_purchase_history(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user_from_request)
):
    """
    Get user's credit purchase history

    Returns list of all credit purchases made by the authenticated user,
    ordered by most recent first.
    """
    user_id = current_user.get("user_id")

    try:
        pool = await get_db_connection()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, package_name, amount_credits, amount_paid,
                       status, created_at, completed_at, stripe_payment_id
                FROM credit_purchases
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )

            history = []
            for row in rows:
                history.append(PurchaseHistory(
                    id=str(row["id"]),
                    package_name=row["package_name"],
                    amount_credits=row["amount_credits"],
                    amount_paid=row["amount_paid"],
                    status=row["status"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    stripe_payment_id=row["stripe_payment_id"]
                ))

        await pool.close()

        logger.info(f"User {user_id} fetched {len(history)} purchase records")
        return history

    except Exception as e:
        logger.error(f"Failed to fetch purchase history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for credit purchases

    Processes checkout.session.completed events to add credits to user accounts
    after successful payment.

    This endpoint is called by Stripe, not by the frontend.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Extract metadata
        session_id = session.get("id")
        payment_intent = session.get("payment_intent")
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        credits = int(metadata.get("credits", 0))
        package_code = metadata.get("package_code")

        if not user_id or not credits:
            logger.error(f"Missing metadata in webhook: user_id={user_id}, credits={credits}")
            return {"status": "error", "message": "Missing required metadata"}

        try:
            pool = await get_db_connection()
            result: Dict[str, Any] = {"status": "success"}
            purchase_id = None
            credits_granted = False

            try:
                # Single connection + single transaction so the grant and the status flip
                # commit atomically. The FOR UPDATE lock serializes concurrent duplicate
                # deliveries: the second delivery blocks, then sees status='completed' and
                # no-ops. This makes the webhook idempotent / exactly-once.
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        purchase = await conn.fetchrow(
                            """
                            SELECT id, status, amount_credits, package_name
                            FROM credit_purchases
                            WHERE stripe_checkout_session_id = $1
                            FOR UPDATE
                            """,
                            session_id
                        )

                        if not purchase:
                            # Unknown session: do NOT 500 (a 500 forces endless Stripe
                            # retries for an event we can never satisfy). Ack with 200.
                            logger.error(
                                f"Purchase not found for session {session_id}; acking to stop retries"
                            )
                            result = {"status": "ignored", "message": "Unknown checkout session"}
                        elif purchase["status"] == "completed":
                            # Idempotent no-op: this session was already granted (duplicate
                            # / redelivered event). Do not grant again.
                            logger.info(
                                f"Session {session_id} already completed; skipping duplicate grant"
                            )
                            result = {"status": "already_processed"}
                        else:
                            # Grant credits ON THIS CONNECTION so the balance update and the
                            # status flip are in the SAME transaction. A crash between them
                            # rolls BOTH back, so a Stripe retry re-attempts exactly once.
                            await credit_manager.allocate_credits_on_conn(
                                conn,
                                user_id=user_id,
                                amount=Decimal(str(credits)),
                                source="purchase",
                                metadata={
                                    "purchase_id": str(purchase["id"]),
                                    "package_code": package_code,
                                    "stripe_session_id": session_id,
                                    "stripe_payment_intent": payment_intent
                                }
                            )

                            await conn.execute(
                                """
                                UPDATE credit_purchases
                                SET status = 'completed',
                                    completed_at = NOW(),
                                    stripe_payment_intent_id = $1,
                                    updated_at = NOW()
                                WHERE id = $2
                                """,
                                payment_intent,
                                purchase["id"]
                            )

                            purchase_id = purchase["id"]
                            credits_granted = True
                            result = {"status": "success"}
            finally:
                await pool.close()

            # Post-commit side effects run ONLY on a fresh grant, and never roll back the
            # already-committed credits (a failure here must not trigger a re-grant).
            if credits_granted:
                try:
                    await audit_logger.log_credit_purchase_completed(
                        user_id=user_id,
                        purchase_id=str(purchase_id),
                        credits_added=credits
                    )
                except Exception as e:
                    logger.warning(
                        f"Audit log after credit grant failed (credits already committed): {e}"
                    )

                # Send confirmation email (best-effort; never re-grant on failure)
                try:
                    logger.info(f"TODO: Send purchase confirmation email to user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to send confirmation email: {e}")

                logger.info(
                    f"Successfully processed credit purchase for user {user_id}: {credits} credits"
                )

            return result

        except Exception as e:
            # After this fix a 500 + Stripe retry is SAFE: the retry re-locks the row and
            # either re-attempts (grant rolled back) or no-ops (already completed). We only
            # 500 on genuinely unexpected/transient faults so Stripe retries them.
            logger.error(f"Failed to process webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}


@router.get("/admin/purchases", response_model=List[PurchaseHistory])
async def admin_list_all_purchases(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin_from_request)
):
    """
    Admin endpoint: List all credit purchases across all users

    Requires admin role. Used for monitoring and support.
    """
    try:
        pool = await get_db_connection()

        async with pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT id, package_name, amount_credits, amount_paid,
                           status, created_at, completed_at, stripe_payment_id
                    FROM credit_purchases
                    WHERE status = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    status, limit, offset
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, package_name, amount_credits, amount_paid,
                           status, created_at, completed_at, stripe_payment_id
                    FROM credit_purchases
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit, offset
                )

            purchases = []
            for row in rows:
                purchases.append(PurchaseHistory(
                    id=str(row["id"]),
                    package_name=row["package_name"],
                    amount_credits=row["amount_credits"],
                    amount_paid=row["amount_paid"],
                    status=row["status"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    stripe_payment_id=row["stripe_payment_id"]
                ))

        await pool.close()

        logger.info(f"Admin {current_user.get('user_id')} listed {len(purchases)} purchases")
        return purchases

    except Exception as e:
        logger.error(f"Failed to list purchases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list purchases: {str(e)}")
