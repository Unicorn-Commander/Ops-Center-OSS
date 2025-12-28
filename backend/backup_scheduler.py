"""
Automated Backup Scheduler for Ops-Center
Uses APScheduler for cron-based backup automation with email notifications
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import asyncio

from storage_manager import storage_backup_manager
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

class BackupScheduler:
    """Manages automated backup scheduling and execution"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
        self._email_enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    def start(self):
        """Start the backup scheduler"""
        try:
            # Load backup configuration
            config = storage_backup_manager.backup_config

            if not config.backup_enabled:
                logger.info("Automated backups disabled in configuration")
                return

            # Schedule backup job using cron expression
            self.scheduler.add_job(
                self._execute_scheduled_backup,
                trigger=CronTrigger.from_crontab(config.schedule),
                id='scheduled_backup',
                name='Scheduled System Backup',
                replace_existing=True
            )

            # Start scheduler
            self.scheduler.start()
            logger.info(f"Backup scheduler started with schedule: {config.schedule}")

            # Log to audit
            audit_logger.log(
                action="backup.scheduler.start",
                user_id="system",
                details={
                    "schedule": config.schedule,
                    "retention_days": config.retention_days,
                    "backup_location": config.backup_location
                }
            )

        except Exception as e:
            logger.error(f"Failed to start backup scheduler: {e}")
            raise

    def stop(self):
        """Stop the backup scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("Backup scheduler stopped")

                audit_logger.log(
                    action="backup.scheduler.stop",
                    user_id="system",
                    details={"timestamp": datetime.now().isoformat()}
                )
        except Exception as e:
            logger.error(f"Error stopping backup scheduler: {e}")

    def reschedule(self, cron_expression: str):
        """Update the backup schedule"""
        try:
            # Remove existing job
            if self.scheduler.get_job('scheduled_backup'):
                self.scheduler.remove_job('scheduled_backup')

            # Add new job with updated schedule
            self.scheduler.add_job(
                self._execute_scheduled_backup,
                trigger=CronTrigger.from_crontab(cron_expression),
                id='scheduled_backup',
                name='Scheduled System Backup',
                replace_existing=True
            )

            logger.info(f"Backup schedule updated to: {cron_expression}")

            audit_logger.log(
                action="backup.scheduler.reschedule",
                user_id="system",
                details={"new_schedule": cron_expression}
            )

        except Exception as e:
            logger.error(f"Failed to reschedule backups: {e}")
            raise

    async def _execute_scheduled_backup(self):
        """Execute a scheduled backup"""
        start_time = datetime.now()
        logger.info("Starting scheduled backup...")

        try:
            # Create backup
            backup_id = await storage_backup_manager.create_backup(backup_type="scheduled")

            end_time = datetime.now()
            duration = end_time - start_time

            # Log success
            logger.info(f"Scheduled backup completed: {backup_id} (took {duration})")

            audit_logger.log(
                action="backup.scheduled.success",
                user_id="system",
                details={
                    "backup_id": backup_id,
                    "duration": str(duration),
                    "timestamp": end_time.isoformat()
                }
            )

            # Send success notification
            await self._send_notification(
                subject="Backup Completed Successfully",
                backup_id=backup_id,
                status="success",
                duration=str(duration)
            )

        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")

            audit_logger.log(
                action="backup.scheduled.failed",
                user_id="system",
                details={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Send failure notification
            await self._send_notification(
                subject="Backup Failed",
                backup_id=None,
                status="failed",
                error=str(e)
            )

    async def _send_notification(
        self,
        subject: str,
        backup_id: Optional[str] = None,
        status: str = "success",
        duration: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Send email notification about backup status"""
        if not self._email_enabled:
            logger.debug("Email notifications disabled, skipping notification")
            return

        try:
            # Import email provider
            from email_provider import email_provider

            # Check if email provider is configured
            if not email_provider.is_configured():
                logger.warning("Email provider not configured, skipping notification")
                return

            # Get admin email from environment
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")

            # Build email body
            if status == "success":
                body = f"""
                Backup Completed Successfully
                ==============================

                Backup ID: {backup_id}
                Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Duration: {duration}
                Status: Success

                The scheduled system backup has completed successfully.
                Backup Location: {storage_backup_manager.backup_config.backup_location}

                ---
                UC-Cloud Ops-Center
                Automated Backup System
                """
            else:
                body = f"""
                Backup Failed
                =============

                Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Status: Failed
                Error: {error}

                The scheduled system backup has failed. Please check the logs for more details.

                Action Required: Review backup configuration and system status.

                ---
                UC-Cloud Ops-Center
                Automated Backup System
                """

            # Send email
            await email_provider.send_email(
                to_email=admin_email,
                subject=f"[Ops-Center] {subject}",
                body=body
            )

            logger.info(f"Backup notification sent to {admin_email}")

        except Exception as e:
            logger.error(f"Failed to send backup notification: {e}")

    def _job_executed_listener(self, event):
        """Listener for successful job execution"""
        logger.debug(f"Job {event.job_id} executed successfully")

    def _job_error_listener(self, event):
        """Listener for job execution errors"""
        logger.error(f"Job {event.job_id} failed with error: {event.exception}")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled backup time"""
        try:
            job = self.scheduler.get_job('scheduled_backup')
            if job:
                return job.next_run_time
            return None
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status information"""
        try:
            config = storage_backup_manager.backup_config
            next_run = self.get_next_run_time()

            return {
                "running": self.scheduler.running,
                "enabled": config.backup_enabled,
                "schedule": config.schedule,
                "next_run": next_run.isoformat() if next_run else None,
                "retention_days": config.retention_days,
                "backup_location": config.backup_location,
                "email_notifications": self._email_enabled
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "running": False,
                "enabled": False,
                "error": str(e)
            }

    async def trigger_manual_backup(self, user_id: str) -> str:
        """Trigger a manual backup (not scheduled)"""
        try:
            logger.info(f"Manual backup triggered by user: {user_id}")

            backup_id = await storage_backup_manager.create_backup(backup_type="manual")

            audit_logger.log(
                action="backup.manual.success",
                user_id=user_id,
                details={
                    "backup_id": backup_id,
                    "timestamp": datetime.now().isoformat()
                }
            )

            return backup_id

        except Exception as e:
            logger.error(f"Manual backup failed: {e}")

            audit_logger.log(
                action="backup.manual.failed",
                user_id=user_id,
                details={
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

            raise

# Create singleton instance
backup_scheduler = BackupScheduler()
