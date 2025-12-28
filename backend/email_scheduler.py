"""
Epic 2.3: Email Notifications System
Module: email_scheduler.py

Purpose: Automated scheduling of email notifications using APScheduler.

Features:
- Daily low balance checks (9 AM)
- Monthly credit reset notifications (1st day at midnight)
- Weekly usage summaries (Monday at 9 AM)
- Async job execution
- Error handling and retry logic

Author: Email Notifications Team Lead
Date: October 24, 2025
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import asyncpg
import os

from email_notifications import email_notification_service
from credit_system import credit_manager
from audit_logger import audit_logger

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EmailScheduler:
    """
    Manages scheduled email notifications using APScheduler.

    Features:
    - Daily low balance checks
    - Monthly credit reset notifications
    - Weekly usage summaries
    - Async job execution with error handling
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_pool: asyncpg.Pool = None
        self.is_running = False

    async def initialize(self):
        """Initialize database connection and scheduler"""
        if self.db_pool:
            return

        try:
            # Initialize database connection
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "unicorn"),
                password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
                database=os.getenv("POSTGRES_DB", "unicorn_db"),
                min_size=2,
                max_size=10
            )

            # Initialize services
            await email_notification_service.initialize()
            await credit_manager.initialize()

            # Add event listeners
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener,
                EVENT_JOB_ERROR
            )

            logger.info("EmailScheduler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EmailScheduler: {e}")
            raise

    async def close(self):
        """Shutdown scheduler and close connections"""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False

        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None

        await email_notification_service.close()
        await credit_manager.close()

        logger.info("EmailScheduler closed")

    def _job_executed_listener(self, event):
        """Listener for successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")

    def _job_error_listener(self, event):
        """Listener for job execution errors"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")

    async def start(self):
        """Start the scheduler with all jobs"""
        if self.is_running:
            logger.warning("EmailScheduler is already running")
            return

        await self.initialize()

        # Daily low balance check (9 AM)
        self.scheduler.add_job(
            func=self._check_low_balances,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_low_balance_check",
            name="Daily Low Balance Check",
            replace_existing=True
        )
        logger.info("Scheduled: Daily low balance check (9 AM)")

        # Monthly credit reset (1st day at midnight)
        self.scheduler.add_job(
            func=self._send_monthly_reset_notifications,
            trigger=CronTrigger(day=1, hour=0, minute=0),
            id="monthly_credit_reset",
            name="Monthly Credit Reset Notifications",
            replace_existing=True
        )
        logger.info("Scheduled: Monthly credit reset (1st day at midnight)")

        # Weekly usage summary (Monday at 9 AM)
        self.scheduler.add_job(
            func=self._send_weekly_usage_summaries,
            trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_usage_summary",
            name="Weekly Usage Summaries",
            replace_existing=True
        )
        logger.info("Scheduled: Weekly usage summary (Monday 9 AM)")

        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        logger.info("EmailScheduler started successfully")

    # ===== SCHEDULED JOB METHODS =====

    async def _check_low_balances(self):
        """Check all users for low credit balances and send alerts"""
        logger.info("Running daily low balance check...")

        try:
            async with self.db_pool.acquire() as conn:
                # Get all users with low balances (< 10% remaining)
                rows = await conn.fetch(
                    """
                    SELECT user_id, credits_remaining, credits_allocated, last_reset
                    FROM user_credits
                    WHERE credits_remaining > 0
                      AND credits_remaining < (credits_allocated * 0.10)
                      AND email_notifications_enabled = true
                    """
                )

                logger.info(f"Found {len(rows)} users with low balances")

                # Send alerts
                sent = 0
                for row in rows:
                    try:
                        success = await email_notification_service.send_low_balance_alert(
                            user_id=row["user_id"],
                            credits_remaining=row["credits_remaining"],
                            credits_allocated=row["credits_allocated"],
                            reset_date=row["last_reset"]
                        )
                        if success:
                            sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send low balance alert to {row['user_id']}: {e}")

                logger.info(f"Sent {sent}/{len(rows)} low balance alerts")

                # Audit log
                await audit_logger.log(
                    action="email.low_balance_check",
                    user_id="system",
                    resource_type="scheduled_job",
                    resource_id="daily_low_balance_check",
                    details={
                        "users_checked": len(rows),
                        "emails_sent": sent
                    },
                    status="success"
                )

        except Exception as e:
            logger.error(f"Low balance check failed: {e}")
            await audit_logger.log(
                action="email.low_balance_check",
                user_id="system",
                resource_type="scheduled_job",
                resource_id="daily_low_balance_check",
                details={"error": str(e)},
                status="failure"
            )

    async def _send_monthly_reset_notifications(self):
        """Send monthly credit reset notifications to all users"""
        logger.info("Running monthly credit reset notifications...")

        try:
            async with self.db_pool.acquire() as conn:
                # Get all users who had credits reset this month
                rows = await conn.fetch(
                    """
                    SELECT
                        uc.user_id,
                        uc.credits_remaining,
                        uc.credits_allocated,
                        uc.last_reset,
                        COALESCE(
                            (SELECT SUM(ABS(amount))
                             FROM credit_transactions
                             WHERE user_id = uc.user_id
                               AND transaction_type = 'usage'
                               AND created_at >= (CURRENT_DATE - INTERVAL '30 days')
                               AND created_at < CURRENT_DATE), 0
                        ) as last_month_spent,
                        COALESCE(
                            (SELECT COUNT(*)
                             FROM credit_transactions
                             WHERE user_id = uc.user_id
                               AND transaction_type = 'usage'
                               AND created_at >= (CURRENT_DATE - INTERVAL '30 days')
                               AND created_at < CURRENT_DATE), 0
                        ) as last_month_calls
                    FROM user_credits uc
                    WHERE uc.email_notifications_enabled = true
                    """
                )

                logger.info(f"Found {len(rows)} users for monthly reset notifications")

                # Send notifications
                sent = 0
                for row in rows:
                    try:
                        # Get most used service
                        top_service_row = await conn.fetchrow(
                            """
                            SELECT service, SUM(ABS(amount)) as total
                            FROM credit_transactions
                            WHERE user_id = $1
                              AND transaction_type = 'usage'
                              AND created_at >= (CURRENT_DATE - INTERVAL '30 days')
                            GROUP BY service
                            ORDER BY total DESC
                            LIMIT 1
                            """,
                            row["user_id"]
                        )
                        top_service = top_service_row["service"] if top_service_row else "N/A"

                        # Calculate previous balance (before reset)
                        previous_balance = row["credits_remaining"] - row["credits_allocated"]

                        success = await email_notification_service.send_monthly_reset_notification(
                            user_id=row["user_id"],
                            tier="professional",  # TODO: Get from Keycloak user attributes
                            new_balance=row["credits_remaining"],
                            allocated=row["credits_allocated"],
                            previous_balance=max(Decimal("0.00"), previous_balance),
                            last_month_spent=row["last_month_spent"],
                            last_month_calls=row["last_month_calls"],
                            top_service=top_service,
                            next_reset_date=row["last_reset"]
                        )
                        if success:
                            sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send monthly reset notification to {row['user_id']}: {e}")

                logger.info(f"Sent {sent}/{len(rows)} monthly reset notifications")

                # Audit log
                await audit_logger.log(
                    action="email.monthly_reset",
                    user_id="system",
                    resource_type="scheduled_job",
                    resource_id="monthly_credit_reset",
                    details={
                        "users_notified": len(rows),
                        "emails_sent": sent
                    },
                    status="success"
                )

        except Exception as e:
            logger.error(f"Monthly reset notifications failed: {e}")
            await audit_logger.log(
                action="email.monthly_reset",
                user_id="system",
                resource_type="scheduled_job",
                resource_id="monthly_credit_reset",
                details={"error": str(e)},
                status="failure"
            )

    async def _send_weekly_usage_summaries(self):
        """Send weekly usage summary emails to all users"""
        logger.info("Running weekly usage summaries...")

        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=7)

            async with self.db_pool.acquire() as conn:
                # Get all active users
                rows = await conn.fetch(
                    """
                    SELECT
                        uc.user_id,
                        uc.credits_remaining,
                        uc.credits_allocated,
                        uc.last_reset,
                        COALESCE(
                            (SELECT SUM(ABS(amount))
                             FROM credit_transactions
                             WHERE user_id = uc.user_id
                               AND transaction_type = 'usage'
                               AND created_at >= $1
                               AND created_at <= $2), 0
                        ) as week_spent,
                        COALESCE(
                            (SELECT COUNT(*)
                             FROM credit_transactions
                             WHERE user_id = uc.user_id
                               AND transaction_type = 'usage'
                               AND created_at >= $1
                               AND created_at <= $2), 0
                        ) as week_calls
                    FROM user_credits uc
                    WHERE uc.email_notifications_enabled = true
                      AND EXISTS (
                          SELECT 1 FROM credit_transactions
                          WHERE user_id = uc.user_id
                            AND created_at >= $1
                      )
                    """,
                    period_start, period_end
                )

                logger.info(f"Found {len(rows)} users for weekly usage summaries")

                # Send summaries
                sent = 0
                for row in rows:
                    try:
                        # Get top 3 services
                        top_services_rows = await conn.fetch(
                            """
                            SELECT service, SUM(ABS(amount)) as cost
                            FROM credit_transactions
                            WHERE user_id = $1
                              AND transaction_type = 'usage'
                              AND created_at >= $2
                              AND created_at <= $3
                            GROUP BY service
                            ORDER BY cost DESC
                            LIMIT 3
                            """,
                            row["user_id"], period_start, period_end
                        )
                        top_services = [
                            {"name": r["service"], "cost": f"{r['cost']:.2f}"}
                            for r in top_services_rows
                        ]

                        # Calculate usage percentage
                        usage_percentage = (
                            (row["credits_allocated"] - row["credits_remaining"]) /
                            row["credits_allocated"] * 100
                            if row["credits_allocated"] > 0 else 0
                        )

                        # Find most active day
                        most_active_row = await conn.fetchrow(
                            """
                            SELECT DATE(created_at) as day, SUM(ABS(amount)) as total
                            FROM credit_transactions
                            WHERE user_id = $1
                              AND transaction_type = 'usage'
                              AND created_at >= $2
                              AND created_at <= $3
                            GROUP BY DATE(created_at)
                            ORDER BY total DESC
                            LIMIT 1
                            """,
                            row["user_id"], period_start, period_end
                        )
                        most_active_day = most_active_row["day"].strftime("%A") if most_active_row else "N/A"

                        # Calculate averages
                        avg_daily_spend = row["week_spent"] / 7 if row["week_spent"] > 0 else Decimal("0.00")
                        estimated_monthly = avg_daily_spend * 30

                        success = await email_notification_service.send_usage_summary(
                            user_id=row["user_id"],
                            tier="professional",  # TODO: Get from Keycloak
                            period_start=period_start,
                            period_end=period_end,
                            total_spent=row["week_spent"],
                            api_calls=row["week_calls"],
                            credits_remaining=row["credits_remaining"],
                            usage_percentage=float(usage_percentage),
                            top_services=top_services,
                            most_active_day=most_active_day,
                            avg_daily_spend=avg_daily_spend,
                            estimated_monthly=estimated_monthly,
                            reset_date=row["last_reset"]
                        )
                        if success:
                            sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send usage summary to {row['user_id']}: {e}")

                logger.info(f"Sent {sent}/{len(rows)} weekly usage summaries")

                # Audit log
                await audit_logger.log(
                    action="email.usage_summary",
                    user_id="system",
                    resource_type="scheduled_job",
                    resource_id="weekly_usage_summary",
                    details={
                        "users_summarized": len(rows),
                        "emails_sent": sent,
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat()
                    },
                    status="success"
                )

        except Exception as e:
            logger.error(f"Weekly usage summaries failed: {e}")
            await audit_logger.log(
                action="email.usage_summary",
                user_id="system",
                resource_type="scheduled_job",
                resource_id="weekly_usage_summary",
                details={"error": str(e)},
                status="failure"
            )


# Global instance
email_scheduler = EmailScheduler()
