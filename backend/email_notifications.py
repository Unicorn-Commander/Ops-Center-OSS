"""
Epic 2.3: Email Notifications System
Module: email_notifications.py

Purpose: Automated email notifications for credit system events using existing
         email infrastructure.

Features:
- Low balance alerts (< 10% remaining)
- Monthly credit reset notifications
- Coupon redemption confirmations
- Welcome emails for new users
- Tier upgrade notifications
- Payment failure alerts
- Weekly usage summaries

Integration:
- Uses existing email_service.py for sending
- Fetches user data from Keycloak via keycloak_integration.py
- Reads credit data from credit_system.py
- Respects user email notification preferences

Author: Email Notifications Team Lead
Date: October 24, 2025
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from jinja2 import Template
import asyncpg
from email_service import email_service
from keycloak_integration import get_user_by_id
from audit_logger import audit_logger

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EmailNotificationService:
    """
    Manages automated email notifications for credit system events.

    Features:
    - Template-based email rendering (HTML + plain text)
    - User preference checking (unsubscribe support)
    - Keycloak user data integration
    - Comprehensive audit logging
    - Rate limiting to prevent spam
    """

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.template_dir = os.path.join(os.path.dirname(__file__), "email_templates")
        self.dashboard_url = os.getenv("APP_URL", "http://localhost:8084")
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@example.com")
        self._rate_limit = {}  # Rate limiting dictionary

    async def initialize(self):
        """Initialize database connection pool"""
        if self.db_pool:
            return

        try:
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "unicorn"),
                password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
                database=os.getenv("POSTGRES_DB", "unicorn_db"),
                min_size=2,
                max_size=10
            )
            logger.info("EmailNotificationService initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EmailNotificationService: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None
            logger.info("EmailNotificationService closed")

    async def _load_template(self, template_name: str, format: str = "html") -> str:
        """Load email template from file"""
        ext = "html" if format == "html" else "txt"
        template_path = os.path.join(self.template_dir, f"{template_name}.{ext}")

        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Template not found: {template_path}")
            raise

    async def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context"""
        template = Template(template_content)
        return template.render(**context)

    async def _get_user_email_and_name(self, user_id: str) -> tuple[Optional[str], Optional[str]]:
        """Fetch user email and username from Keycloak"""
        try:
            user = await get_user_by_id(user_id)
            if not user:
                logger.warning(f"User not found in Keycloak: {user_id}")
                return None, None

            email = user.get("email")
            username = user.get("username") or user.get("firstName", "User")

            return email, username
        except Exception as e:
            logger.error(f"Failed to fetch user from Keycloak: {e}")
            return None, None

    async def _check_notification_enabled(self, user_id: str) -> bool:
        """Check if user has email notifications enabled"""
        if not self.db_pool:
            await self.initialize()

        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT email_notifications_enabled
                    FROM user_credits
                    WHERE user_id = $1
                    """,
                    user_id
                )

                if not row:
                    # Default to enabled if no preference set
                    return True

                return row.get("email_notifications_enabled", True)
        except Exception as e:
            logger.error(f"Failed to check notification preference: {e}")
            # Default to enabled on error
            return True

    async def _check_rate_limit(self, user_id: str, notification_type: str) -> bool:
        """Check if notification is rate-limited (max 1 per day for alerts)"""
        if notification_type not in ["low_balance", "payment_failure"]:
            # Only rate limit alert-type notifications
            return True

        key = f"{user_id}:{notification_type}"
        last_sent = self._rate_limit.get(key)

        if last_sent:
            elapsed = datetime.utcnow() - last_sent
            if elapsed < timedelta(days=1):
                logger.info(f"Rate limit hit for {key} (last sent {elapsed.total_seconds():.0f}s ago)")
                return False

        # Update rate limit tracker
        self._rate_limit[key] = datetime.utcnow()
        return True

    async def _send_notification(
        self,
        user_id: str,
        notification_type: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """Internal method to send notification email"""
        try:
            # Check if notifications are enabled for user
            if not await self._check_notification_enabled(user_id):
                logger.info(f"Notifications disabled for user {user_id}")
                return False

            # Check rate limit
            if not await self._check_rate_limit(user_id, notification_type):
                return False

            # Get user email and name
            email, username = await self._get_user_email_and_name(user_id)
            if not email:
                logger.warning(f"No email found for user {user_id}")
                return False

            # Add common context variables
            context.update({
                "username": username,
                "dashboard_url": self.dashboard_url,
                "support_email": self.support_email,
                "year": datetime.utcnow().year,
                "unsubscribe_url": f"{self.dashboard_url}/api/v1/notifications/unsubscribe/{user_id}"
            })

            # Load and render templates
            html_template = await self._load_template(template_name, "html")
            text_template = await self._load_template(template_name, "txt")

            html_content = await self._render_template(html_template, context)
            text_content = await self._render_template(text_template, context)

            # Send email
            success = await email_service.send_email(
                to=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            # Audit log
            if success:
                await audit_logger.log(
                    action=f"email.{notification_type}",
                    user_id=user_id,
                    resource_type="email_notification",
                    resource_id=email,
                    details={
                        "notification_type": notification_type,
                        "subject": subject,
                        "template": template_name
                    },
                    status="success"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to send {notification_type} notification to {user_id}: {e}")
            await audit_logger.log(
                action=f"email.{notification_type}",
                user_id=user_id,
                resource_type="email_notification",
                resource_id="",
                details={
                    "notification_type": notification_type,
                    "error": str(e)
                },
                status="failure"
            )
            return False

    # ===== PUBLIC NOTIFICATION METHODS =====

    async def send_low_balance_alert(
        self,
        user_id: str,
        credits_remaining: Decimal,
        credits_allocated: Decimal,
        reset_date: datetime
    ) -> bool:
        """Send low balance alert email (< 10% remaining)"""
        percentage = (credits_remaining / credits_allocated * 100) if credits_allocated > 0 else 0

        context = {
            "credits_remaining": f"{credits_remaining:.2f}",
            "percentage": f"{percentage:.1f}",
            "reset_date": reset_date.strftime("%B %d, %Y")
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="low_balance",
            subject="⚠️ Low Credit Balance Alert",
            template_name="low_balance",
            context=context
        )

    async def send_monthly_reset_notification(
        self,
        user_id: str,
        tier: str,
        new_balance: Decimal,
        allocated: Decimal,
        previous_balance: Decimal,
        last_month_spent: Decimal,
        last_month_calls: int,
        top_service: str,
        next_reset_date: datetime
    ) -> bool:
        """Send monthly credit reset notification"""
        context = {
            "tier": tier.title(),
            "new_balance": f"{new_balance:.2f}",
            "allocated": f"{allocated:.2f}",
            "previous_balance": f"{previous_balance:.2f}",
            "last_month_spent": f"{last_month_spent:.2f}",
            "last_month_calls": f"{last_month_calls:,}",
            "top_service": top_service,
            "next_reset_date": next_reset_date.strftime("%B %d, %Y")
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="monthly_reset",
            subject="✨ Your Monthly Credits Have Been Refreshed!",
            template_name="monthly_reset",
            context=context
        )

    async def send_coupon_redemption_confirmation(
        self,
        user_id: str,
        coupon_code: str,
        credits_added: Decimal,
        new_balance: Decimal,
        coupon_type: str,
        expires_at: Optional[datetime] = None,
        redeemed_at: Optional[datetime] = None
    ) -> bool:
        """Send coupon redemption confirmation email"""
        context = {
            "coupon_code": coupon_code,
            "credits_added": f"{credits_added:.2f}",
            "new_balance": f"{new_balance:.2f}",
            "coupon_type": coupon_type,
            "expires_at": expires_at.strftime("%B %d, %Y") if expires_at else "Never",
            "redeemed_at": (redeemed_at or datetime.utcnow()).strftime("%B %d, %Y at %I:%M %p")
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="coupon_redeemed",
            subject="🎉 Coupon Redeemed Successfully!",
            template_name="coupon_redeemed",
            context=context
        )

    async def send_welcome_email(
        self,
        user_id: str,
        tier: str
    ) -> bool:
        """Send welcome email to new user"""
        context = {
            "tier": tier.title()
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="welcome",
            subject="🦄 Welcome to UC-1 Pro Operations Center!",
            template_name="welcome",
            context=context
        )

    async def send_tier_upgrade_notification(
        self,
        user_id: str,
        old_tier: str,
        new_tier: str,
        old_allocation: Decimal,
        new_allocation: Decimal,
        current_balance: Decimal,
        new_features: List[str],
        next_reset_date: datetime
    ) -> bool:
        """Send tier upgrade notification"""
        context = {
            "old_tier": old_tier.title(),
            "new_tier": new_tier.title(),
            "old_allocation": f"{old_allocation:.2f}",
            "new_allocation": f"{new_allocation:.2f}",
            "current_balance": f"{current_balance:.2f}",
            "new_features": new_features,
            "next_reset_date": next_reset_date.strftime("%B %d, %Y")
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="tier_upgrade",
            subject="🚀 Subscription Tier Upgraded!",
            template_name="tier_upgrade",
            context=context
        )

    async def send_payment_failure_alert(
        self,
        user_id: str,
        tier: str,
        amount: Decimal,
        failure_reason: str,
        failed_at: datetime,
        grace_period: int = 7,
        retry_in: int = 3
    ) -> bool:
        """Send payment failure alert"""
        context = {
            "tier": tier.title(),
            "amount": f"{amount:.2f}",
            "failure_reason": failure_reason,
            "failed_at": failed_at.strftime("%B %d, %Y at %I:%M %p"),
            "grace_period": grace_period,
            "retry_in": retry_in
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="payment_failure",
            subject="⚠️ Payment Failed - Action Required",
            template_name="payment_failure",
            context=context
        )

    async def send_usage_summary(
        self,
        user_id: str,
        tier: str,
        period_start: datetime,
        period_end: datetime,
        total_spent: Decimal,
        api_calls: int,
        credits_remaining: Decimal,
        usage_percentage: float,
        top_services: List[Dict[str, Any]],
        most_active_day: str,
        avg_daily_spend: Decimal,
        estimated_monthly: Decimal,
        reset_date: datetime
    ) -> bool:
        """Send weekly usage summary email"""
        context = {
            "tier": tier.title(),
            "period_start": period_start.strftime("%b %d"),
            "period_end": period_end.strftime("%b %d, %Y"),
            "total_spent": f"{total_spent:.2f}",
            "api_calls": f"{api_calls:,}",
            "credits_remaining": f"{credits_remaining:.2f}",
            "usage_percentage": f"{usage_percentage:.1f}",
            "top_services": top_services,
            "most_active_day": most_active_day,
            "avg_daily_spend": f"{avg_daily_spend:.2f}",
            "estimated_monthly": f"{estimated_monthly:.2f}",
            "reset_date": reset_date.strftime("%B %d, %Y")
        }

        return await self._send_notification(
            user_id=user_id,
            notification_type="usage_summary",
            subject="📊 Your Weekly Usage Summary",
            template_name="usage_summary",
            context=context
        )


# Global instance
email_notification_service = EmailNotificationService()
