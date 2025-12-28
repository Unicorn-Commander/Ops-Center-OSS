"""
Subscription Management API - Self-Service Subscription Changes
Handles upgrade, downgrade, cancellation, and subscription change preview
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os
import logging
import stripe
import httpx
from enum import Enum

# Import subscription manager
from subscription_manager import subscription_manager, DEFAULT_PLANS

# Manual authentication function (matches server.py logic - avoids circular import)
async def get_current_user(request):
    """Get current user from session cookie (avoids circular import with server.py)"""
    from fastapi import Request, HTTPException
    import sys
    sys.path.insert(0, '/app')
    from server import sessions  # Import sessions from server.py

    session_cookie = request.cookies.get("ops_center_session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_data = sessions.get(session_cookie)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Map Keycloak 'sub' field to 'user_id' for compatibility
    if "user_id" not in user_data:
        user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

    return user_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscription Management"])

# ============================================================================
# Request/Response Models
# ============================================================================

class SubscriptionChangeRequest(BaseModel):
    """Request to change subscription plan"""
    plan_code: str = Field(..., description="Target subscription plan code")
    effective_date: str = Field(default="immediate", description="When to apply change: 'immediate' or 'next_cycle'")


class SubscriptionCancelRequest(BaseModel):
    """Request to cancel subscription"""
    reason: str = Field(..., description="Cancellation reason")
    feedback: Optional[str] = Field(None, description="Additional feedback")
    immediate: bool = Field(default=False, description="Cancel immediately vs end of period")


class SubscriptionPreviewResponse(BaseModel):
    """Preview of subscription change"""
    current_plan: str
    target_plan: str
    current_price: float
    target_price: float
    price_difference: float
    proration_amount: Optional[float] = None
    effective_date: str
    features_added: List[str] = []
    features_removed: List[str] = []
    is_upgrade: bool


class SubscriptionHistoryEntry(BaseModel):
    """Subscription change history entry"""
    id: int
    change_type: str  # 'upgrade', 'downgrade', 'cancel', 'reactivate'
    from_plan: Optional[str]
    to_plan: Optional[str]
    effective_date: datetime
    reason: Optional[str]
    feedback: Optional[str]
    created_at: datetime


class CancellationReason(str, Enum):
    """Standard cancellation reasons"""
    TOO_EXPENSIVE = "too_expensive"
    NOT_USING = "not_using_service"
    MISSING_FEATURES = "missing_features"
    FOUND_ALTERNATIVE = "found_alternative"
    TECHNICAL_ISSUES = "technical_issues"
    OTHER = "other"


# ============================================================================
# Helper Functions
# ============================================================================

async def get_lago_customer_id(user_email: str) -> Optional[str]:
    """Get Lago customer ID from email"""
    try:
        # Call Lago API to find customer
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('LAGO_API_URL', 'http://unicorn-lago-api:3000')}/api/v1/customers",
                headers={
                    "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                    "Content-Type": "application/json"
                },
                params={"external_id": user_email}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("customers") and len(data["customers"]) > 0:
                    return data["customers"][0]["lago_id"]

            logger.warning(f"Lago customer not found for email: {user_email}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Lago customer: {str(e)}")
        return None


async def get_lago_subscription(customer_id: str) -> Optional[Dict]:
    """Get active Lago subscription for customer"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions",
                headers={
                    "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                    "Content-Type": "application/json"
                },
                params={"external_customer_id": customer_id, "status": "active"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("subscriptions") and len(data["subscriptions"]) > 0:
                    return data["subscriptions"][0]

            return None
    except Exception as e:
        logger.error(f"Error fetching Lago subscription: {str(e)}")
        return None


def get_plan_by_code(plan_code: str):
    """Get plan object by plan code"""
    for plan in DEFAULT_PLANS:
        if plan.id == plan_code or plan.name == plan_code:
            return plan
    return None


def calculate_proration(current_plan, target_plan, days_remaining: int):
    """Calculate prorated amount for plan change"""
    if not current_plan or not target_plan:
        return 0.0

    # Calculate daily rates
    current_daily = current_plan.price_monthly / 30
    target_daily = target_plan.price_monthly / 30

    # Proration for remaining days
    current_credit = current_daily * days_remaining
    target_charge = target_daily * days_remaining

    return round(target_charge - current_credit, 2)


async def log_subscription_change(
    user_id: str,
    change_type: str,
    from_plan: Optional[str],
    to_plan: Optional[str],
    reason: Optional[str] = None,
    feedback: Optional[str] = None
):
    """Log subscription change to database"""
    import asyncpg

    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )

        # Insert subscription change record
        await conn.execute("""
            INSERT INTO subscription_changes
            (user_id, change_type, from_plan, to_plan, reason, feedback, effective_date, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        """, user_id, change_type, from_plan, to_plan, reason, feedback)

        await conn.close()
        logger.info(f"Logged subscription change: {change_type} for user {user_id}")
    except Exception as e:
        logger.error(f"Error logging subscription change: {str(e)}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upgrade", summary="Upgrade subscription to higher tier")
async def upgrade_subscription(
    request: SubscriptionChangeRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Upgrade user to higher tier

    Creates a Stripe Checkout session and returns checkout URL.
    The webhook will handle subscription creation in Lago after payment.
    """
    try:
        user_email = user.get("email")
        user_id = user.get("user_id") or user.get("sub")

        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found in session"
            )

        # Get target plan
        target_plan = get_plan_by_code(request.plan_code)
        if not target_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan '{request.plan_code}' not found"
            )

        # Verify it's an upgrade (higher tier)
        lago_subscription = await get_lago_subscription(user_email)
        if lago_subscription:
            current_plan = get_plan_by_code(lago_subscription.get("plan_code"))
            if current_plan and target_plan.price_monthly <= current_plan.price_monthly:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Use downgrade endpoint for lower tiers"
                )

        # Create Stripe Checkout session
        if not target_plan.stripe_price_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe price ID not configured for this plan"
            )

        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=["card"],
            line_items=[{
                "price": target_plan.stripe_price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=os.getenv("STRIPE_SUCCESS_URL", "https://your-domain.com/admin/subscription/success") + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=os.getenv("STRIPE_CANCEL_URL", "https://your-domain.com/admin/subscription/plan") + "?canceled=true",
            metadata={
                "plan_code": target_plan.id,
                "user_id": user_id,
                "user_email": user_email,
                "change_type": "upgrade"
            }
        )

        # Log the upgrade attempt
        await log_subscription_change(
            user_id=user_id,
            change_type="upgrade",
            from_plan=lago_subscription.get("plan_code") if lago_subscription else None,
            to_plan=target_plan.id
        )

        logger.info(f"Created Stripe checkout session for {user_email}: {checkout_session.id}")

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "plan": target_plan.dict()
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during upgrade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/downgrade", summary="Downgrade subscription to lower tier")
async def downgrade_subscription(
    request: SubscriptionChangeRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Downgrade user to lower tier

    Updates Lago subscription with new plan.
    Change is effective immediately or at next billing cycle.
    """
    try:
        user_email = user.get("email")
        user_id = user.get("user_id") or user.get("sub")

        # Get current subscription from Lago
        lago_customer_id = await get_lago_customer_id(user_email)
        if not lago_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        lago_subscription = await get_lago_subscription(user_email)
        if not lago_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        current_plan = get_plan_by_code(lago_subscription.get("plan_code"))
        target_plan = get_plan_by_code(request.plan_code)

        if not target_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan '{request.plan_code}' not found"
            )

        # Verify it's a downgrade
        if target_plan.price_monthly >= current_plan.price_monthly:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use upgrade endpoint for higher tiers"
            )

        # Update subscription in Lago
        async with httpx.AsyncClient() as client:
            # Determine when to apply the change
            if request.effective_date == "immediate":
                # Terminate current subscription and create new one
                terminate_response = await client.delete(
                    f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions/{lago_subscription['lago_id']}",
                    headers={
                        "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                        "Content-Type": "application/json"
                    }
                )

                if terminate_response.status_code not in [200, 204]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to terminate current subscription"
                    )

                # Create new subscription with lower tier
                create_response = await client.post(
                    f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "subscription": {
                            "external_customer_id": user_email,
                            "plan_code": target_plan.id,
                            "subscription_date": datetime.utcnow().isoformat()
                        }
                    }
                )

                if create_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create new subscription"
                    )

                effective_msg = "Downgrade applied immediately"
            else:
                # Schedule downgrade for next billing cycle
                # Update subscription with pending_plan_change
                update_response = await client.put(
                    f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions/{lago_subscription['lago_id']}",
                    headers={
                        "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "subscription": {
                            "plan_code": target_plan.id,
                            "ending_at": lago_subscription.get("next_billing_date")
                        }
                    }
                )

                if update_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to schedule downgrade"
                    )

                effective_msg = f"Downgrade scheduled for {lago_subscription.get('next_billing_date')}"

        # Log the downgrade
        await log_subscription_change(
            user_id=user_id,
            change_type="downgrade",
            from_plan=current_plan.id,
            to_plan=target_plan.id
        )

        logger.info(f"Downgraded subscription for {user_email}: {current_plan.id} -> {target_plan.id}")

        return {
            "success": True,
            "message": effective_msg,
            "from_plan": current_plan.dict(),
            "to_plan": target_plan.dict(),
            "effective_date": request.effective_date
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downgrading subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cancel", summary="Cancel subscription")
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Cancel subscription

    Marks subscription as canceled in Lago.
    Access continues until end of current billing period unless immediate=True.
    """
    try:
        user_email = user.get("email")
        user_id = user.get("user_id") or user.get("sub")

        # Get current subscription
        lago_subscription = await get_lago_subscription(user_email)
        if not lago_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        current_plan = get_plan_by_code(lago_subscription.get("plan_code"))

        # Cancel in Lago
        async with httpx.AsyncClient() as client:
            if request.immediate:
                # Terminate immediately
                response = await client.delete(
                    f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions/{lago_subscription['lago_id']}",
                    headers={
                        "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code not in [200, 204]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to cancel subscription"
                    )

                access_until = "Immediately"
            else:
                # Cancel at end of period
                response = await client.put(
                    f"{os.getenv('LAGO_API_URL')}/api/v1/subscriptions/{lago_subscription['lago_id']}",
                    headers={
                        "Authorization": f"Bearer {os.getenv('LAGO_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "subscription": {
                            "status": "pending_cancellation",
                            "ending_at": lago_subscription.get("next_billing_date")
                        }
                    }
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to schedule cancellation"
                    )

                access_until = lago_subscription.get("next_billing_date")

        # Log the cancellation
        await log_subscription_change(
            user_id=user_id,
            change_type="cancel",
            from_plan=current_plan.id if current_plan else None,
            to_plan=None,
            reason=request.reason,
            feedback=request.feedback
        )

        logger.info(f"Canceled subscription for {user_email}: {request.reason}")

        return {
            "success": True,
            "message": "Subscription canceled successfully",
            "access_until": access_until,
            "cancellation_reason": request.reason,
            "immediate": request.immediate
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/preview-change", response_model=SubscriptionPreviewResponse, summary="Preview subscription change")
async def preview_subscription_change(
    new_plan_code: str,
    user: Dict = Depends(get_current_user)
):
    """
    Preview cost change and feature differences

    Shows prorated amount, new billing amount, and feature changes.
    """
    try:
        user_email = user.get("email")

        # Get current subscription
        lago_subscription = await get_lago_subscription(user_email)
        if not lago_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        current_plan = get_plan_by_code(lago_subscription.get("plan_code"))
        target_plan = get_plan_by_code(new_plan_code)

        if not target_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan '{new_plan_code}' not found"
            )

        # Calculate days remaining in billing period
        next_billing = datetime.fromisoformat(lago_subscription.get("next_billing_date").replace('Z', '+00:00'))
        days_remaining = (next_billing - datetime.utcnow()).days

        # Calculate proration
        proration = calculate_proration(current_plan, target_plan, days_remaining)

        # Feature comparison
        current_features = set(current_plan.features)
        target_features = set(target_plan.features)

        features_added = list(target_features - current_features)
        features_removed = list(current_features - target_features)

        is_upgrade = target_plan.price_monthly > current_plan.price_monthly

        return SubscriptionPreviewResponse(
            current_plan=current_plan.display_name,
            target_plan=target_plan.display_name,
            current_price=current_plan.price_monthly,
            target_price=target_plan.price_monthly,
            price_difference=round(target_plan.price_monthly - current_plan.price_monthly, 2),
            proration_amount=proration,
            effective_date=next_billing.strftime("%Y-%m-%d"),
            features_added=features_added,
            features_removed=features_removed,
            is_upgrade=is_upgrade
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing subscription change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history", response_model=List[SubscriptionHistoryEntry], summary="Get subscription change history")
async def get_subscription_history(
    limit: int = 50,
    offset: int = 0,
    user: Dict = Depends(get_current_user)
):
    """
    Get subscription change history

    Returns all upgrades, downgrades, and cancellations with timestamps and reasons.
    """
    import asyncpg

    try:
        user_id = user.get("user_id") or user.get("sub")

        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )

        # Fetch subscription history
        rows = await conn.fetch("""
            SELECT id, change_type, from_plan, to_plan, effective_date, reason, feedback, created_at
            FROM subscription_changes
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)

        await conn.close()

        history = []
        for row in rows:
            history.append(SubscriptionHistoryEntry(
                id=row['id'],
                change_type=row['change_type'],
                from_plan=row['from_plan'],
                to_plan=row['to_plan'],
                effective_date=row['effective_date'],
                reason=row['reason'],
                feedback=row['feedback'],
                created_at=row['created_at']
            ))

        return history

    except Exception as e:
        logger.error(f"Error fetching subscription history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
