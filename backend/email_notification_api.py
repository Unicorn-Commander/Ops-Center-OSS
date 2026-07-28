"""
Epic 2.3: Email Notifications System
Module: email_notification_api.py

Purpose: API endpoints for managing email notifications.

Features:
- Manual notification sending (testing)
- Notification preference management (enable/disable)
- Unsubscribe functionality
- Notification history viewing

Author: Email Notifications Team Lead
Date: October 24, 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import logging

from email_notifications import email_notification_service
from credit_system import credit_manager
from keycloak_integration import get_current_user_id
from audit_logger import audit_logger

# Logging setup
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/notifications", tags=["Email Notifications"])


# ===== REQUEST/RESPONSE MODELS =====

class SendLowBalanceAlertRequest(BaseModel):
    user_id: str


class SendMonthlyResetRequest(BaseModel):
    user_id: str


class SendCouponRedemptionRequest(BaseModel):
    user_id: str
    coupon_code: str
    credits_added: Decimal
    coupon_type: str = "Promotional"


class SendWelcomeEmailRequest(BaseModel):
    user_id: str
    tier: str = "trial"


class SendTierUpgradeRequest(BaseModel):
    user_id: str
    old_tier: str
    new_tier: str
    new_features: List[str]


class SendPaymentFailureRequest(BaseModel):
    user_id: str
    tier: str
    amount: Decimal
    failure_reason: str


class SendUsageSummaryRequest(BaseModel):
    user_id: str


class NotificationPreferenceUpdate(BaseModel):
    email_notifications_enabled: bool


class NotificationResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    email: Optional[str] = None


# ===== MANUAL NOTIFICATION ENDPOINTS =====

@router.post("/send/low-balance", response_model=NotificationResponse)
async def send_low_balance_alert(request: SendLowBalanceAlertRequest):
    """
    Manually send low balance alert email (for testing)

    Requires admin role.
    """
    try:
        # Get user's current credit balance
        balance = await credit_manager.get_balance(request.user_id)

        success = await email_notification_service.send_low_balance_alert(
            user_id=request.user_id,
            credits_remaining=balance["credits_remaining"],
            credits_allocated=balance["credits_allocated"],
            reset_date=balance["last_reset"]
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Low balance alert sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending low balance alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/monthly-reset", response_model=NotificationResponse)
async def send_monthly_reset(request: SendMonthlyResetRequest):
    """
    Manually send monthly credit reset notification (for testing)

    Requires admin role.
    """
    try:
        # Get user's current credit balance
        balance = await credit_manager.get_balance(request.user_id)

        # Get last month's transaction data
        transactions = await credit_manager.get_transactions(
            user_id=request.user_id,
            limit=1000,
            transaction_type="usage"
        )

        # Calculate last month's stats
        last_month_spent = sum(abs(t["amount"]) for t in transactions)
        last_month_calls = len(transactions)
        top_service = transactions[0]["service"] if transactions else "N/A"

        success = await email_notification_service.send_monthly_reset_notification(
            user_id=request.user_id,
            tier="professional",  # TODO: Get from Keycloak
            new_balance=balance["credits_remaining"],
            allocated=balance["credits_allocated"],
            previous_balance=Decimal("0.00"),
            last_month_spent=last_month_spent,
            last_month_calls=last_month_calls,
            top_service=top_service,
            next_reset_date=balance["last_reset"]
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Monthly reset notification sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending monthly reset notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/coupon-redeemed", response_model=NotificationResponse)
async def send_coupon_redeemed(request: SendCouponRedemptionRequest):
    """
    Manually send coupon redemption confirmation (for testing)

    Requires admin role.
    """
    try:
        # Get user's current balance
        balance = await credit_manager.get_balance(request.user_id)

        success = await email_notification_service.send_coupon_redemption_confirmation(
            user_id=request.user_id,
            coupon_code=request.coupon_code,
            credits_added=request.credits_added,
            new_balance=balance["credits_remaining"],
            coupon_type=request.coupon_type,
            expires_at=None,
            redeemed_at=datetime.utcnow()
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Coupon redemption confirmation sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending coupon redemption notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/welcome", response_model=NotificationResponse)
async def send_welcome_email(request: SendWelcomeEmailRequest):
    """
    Manually send welcome email (for testing)

    Requires admin role.
    """
    try:
        success = await email_notification_service.send_welcome_email(
            user_id=request.user_id,
            tier=request.tier
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Welcome email sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/tier-upgrade", response_model=NotificationResponse)
async def send_tier_upgrade(request: SendTierUpgradeRequest):
    """
    Manually send tier upgrade notification (for testing)

    Requires admin role.
    """
    try:
        # Get user's current balance
        balance = await credit_manager.get_balance(request.user_id)

        # Tier allocation mapping
        tier_allocations = {
            "trial": Decimal("5.00"),
            "starter": Decimal("20.00"),
            "professional": Decimal("60.00"),
            "enterprise": Decimal("999999.99")
        }

        success = await email_notification_service.send_tier_upgrade_notification(
            user_id=request.user_id,
            old_tier=request.old_tier,
            new_tier=request.new_tier,
            old_allocation=tier_allocations.get(request.old_tier, Decimal("0.00")),
            new_allocation=tier_allocations.get(request.new_tier, Decimal("0.00")),
            current_balance=balance["credits_remaining"],
            new_features=request.new_features,
            next_reset_date=balance["last_reset"]
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Tier upgrade notification sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending tier upgrade notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/payment-failure", response_model=NotificationResponse)
async def send_payment_failure(request: SendPaymentFailureRequest):
    """
    Manually send payment failure alert (for testing)

    Requires admin role.
    """
    try:
        success = await email_notification_service.send_payment_failure_alert(
            user_id=request.user_id,
            tier=request.tier,
            amount=request.amount,
            failure_reason=request.failure_reason,
            failed_at=datetime.utcnow(),
            grace_period=7,
            retry_in=3
        )

        if success:
            return NotificationResponse(
                success=True,
                message="Payment failure alert sent successfully",
                user_id=request.user_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending payment failure alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== PREFERENCE MANAGEMENT =====

@router.get("/preferences/{user_id}")
async def get_notification_preferences(user_id: str):
    """Get email notification preferences for a user"""
    try:
        enabled = await email_notification_service._check_notification_enabled(user_id)
        return {
            "user_id": user_id,
            "email_notifications_enabled": enabled
        }
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{user_id}")
async def update_notification_preferences(
    user_id: str,
    preferences: NotificationPreferenceUpdate
):
    """Update email notification preferences for a user"""
    try:
        async with email_notification_service.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_credits
                SET email_notifications_enabled = $1
                WHERE user_id = $2
                """,
                preferences.email_notifications_enabled,
                user_id
            )

        # Audit log
        await audit_logger.log(
            action="email.preferences_updated",
            user_id=user_id,
            resource_type="notification_preferences",
            resource_id=user_id,
            details={
                "email_notifications_enabled": preferences.email_notifications_enabled
            },
            status="success"
        )

        return {
            "success": True,
            "message": "Notification preferences updated successfully",
            "user_id": user_id,
            "email_notifications_enabled": preferences.email_notifications_enabled
        }
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unsubscribe/{user_id}")
async def unsubscribe_from_notifications(user_id: str):
    """
    Unsubscribe user from email notifications (public endpoint)

    This endpoint is linked in email footers.
    """
    try:
        async with email_notification_service.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_credits
                SET email_notifications_enabled = false
                WHERE user_id = $1
                """,
                user_id
            )

        # Audit log
        await audit_logger.log(
            action="email.unsubscribed",
            user_id=user_id,
            resource_type="notification_preferences",
            resource_id=user_id,
            details={"method": "unsubscribe_link"},
            status="success"
        )

        return {
            "success": True,
            "message": "You have been unsubscribed from email notifications",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error unsubscribing user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== HEALTH CHECK =====

@router.get("/health")
async def notification_health():
    """Health check for email notification service"""
    return {
        "status": "healthy",
        "service": "email_notifications",
        "scheduler_running": email_scheduler.is_running if 'email_scheduler' in globals() else False
    }
