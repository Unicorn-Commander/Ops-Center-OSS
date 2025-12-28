"""
Alert Trigger System for Ops-Center
Version: 1.0.0
Author: Backend Team Lead
Date: November 29, 2025

Purpose: Automated email alert trigger manager with cooldown and deduplication.

Features:
- Trigger registration and management
- Condition checking with configurable thresholds
- Alert cooldown periods to prevent spam
- Duplicate alert detection
- Integration with email alert service
- Audit logging
- Redis-based deduplication cache
"""

import logging
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

from email_alerts import email_alert_service

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class AlertTrigger:
    """Alert trigger definition"""
    trigger_id: str
    name: str
    alert_type: str  # system_critical, billing, security, usage
    condition_func: Callable
    recipients: List[str]
    cooldown_minutes: int = 60  # Default 1 hour cooldown
    enabled: bool = True
    priority: str = "medium"  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertTriggerManager:
    """
    Manages automated email alert triggers

    Features:
    - Register triggers with conditions
    - Check conditions and send alerts
    - Prevent duplicate alerts with cooldown
    - Track alert history
    - Redis-based deduplication
    """

    def __init__(self, redis_client=None):
        # Redis client for deduplication cache
        if redis_client:
            self.redis_client = redis_client
        else:
            import os
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'unicorn-redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True
            )

        # Registered triggers
        self.triggers: Dict[str, AlertTrigger] = {}

        # Alert history (in-memory cache)
        self.alert_history: List[Dict] = []

        logger.info("AlertTriggerManager initialized")

    def register_trigger(
        self,
        trigger_id: str,
        name: str,
        alert_type: str,
        condition_func: Callable,
        recipients: List[str],
        cooldown_minutes: int = 60,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertTrigger:
        """
        Register a new alert trigger

        Args:
            trigger_id: Unique trigger identifier
            name: Human-readable trigger name
            alert_type: Alert type (system_critical, billing, security, usage)
            condition_func: Async function that returns (should_trigger: bool, context: dict)
            recipients: List of email addresses
            cooldown_minutes: Minimum minutes between alerts (default: 60)
            priority: Alert priority (low, medium, high, critical)
            metadata: Additional trigger metadata

        Returns:
            AlertTrigger object
        """
        trigger = AlertTrigger(
            trigger_id=trigger_id,
            name=name,
            alert_type=alert_type,
            condition_func=condition_func,
            recipients=recipients,
            cooldown_minutes=cooldown_minutes,
            priority=priority,
            metadata=metadata or {}
        )

        self.triggers[trigger_id] = trigger
        logger.info(f"Registered trigger: {trigger_id} ({name})")

        return trigger

    def unregister_trigger(self, trigger_id: str) -> bool:
        """
        Unregister a trigger

        Args:
            trigger_id: Trigger to remove

        Returns:
            True if removed, False if not found
        """
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            logger.info(f"Unregistered trigger: {trigger_id}")
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[AlertTrigger]:
        """Get trigger by ID"""
        return self.triggers.get(trigger_id)

    def list_triggers(self) -> List[AlertTrigger]:
        """List all registered triggers"""
        return list(self.triggers.values())

    def _get_cooldown_key(self, trigger_id: str, context: Dict) -> str:
        """
        Generate unique cooldown key for deduplication

        Uses trigger_id + hash of context to identify unique alert conditions
        """
        context_hash = hashlib.md5(
            json.dumps(context, sort_keys=True).encode()
        ).hexdigest()[:8]

        return f"alert_cooldown:{trigger_id}:{context_hash}"

    def _is_in_cooldown(self, trigger_id: str, context: Dict, cooldown_minutes: int) -> bool:
        """
        Check if alert is in cooldown period

        Args:
            trigger_id: Trigger ID
            context: Alert context (for deduplication)
            cooldown_minutes: Cooldown period in minutes

        Returns:
            True if in cooldown, False otherwise
        """
        cooldown_key = self._get_cooldown_key(trigger_id, context)

        try:
            last_sent = self.redis_client.get(cooldown_key)

            if last_sent:
                last_sent_time = float(last_sent)
                cooldown_seconds = cooldown_minutes * 60
                time_since_last = time.time() - last_sent_time

                if time_since_last < cooldown_seconds:
                    remaining = cooldown_seconds - time_since_last
                    logger.debug(
                        f"Alert {trigger_id} in cooldown. "
                        f"Remaining: {remaining/60:.1f} minutes"
                    )
                    return True

            return False

        except Exception as e:
            logger.warning(f"Redis cooldown check failed: {e}. Allowing alert.")
            return False

    def _set_cooldown(self, trigger_id: str, context: Dict, cooldown_minutes: int):
        """
        Set cooldown period for alert

        Args:
            trigger_id: Trigger ID
            context: Alert context
            cooldown_minutes: Cooldown period in minutes
        """
        cooldown_key = self._get_cooldown_key(trigger_id, context)
        cooldown_seconds = cooldown_minutes * 60

        try:
            self.redis_client.setex(
                cooldown_key,
                cooldown_seconds,
                str(time.time())
            )
            logger.debug(f"Set cooldown for {trigger_id}: {cooldown_minutes} minutes")

        except Exception as e:
            logger.warning(f"Failed to set cooldown: {e}")

    async def check_and_send(
        self,
        trigger_id: str,
        subject: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check trigger and send alert if conditions met

        Args:
            trigger_id: Trigger to check
            subject: Email subject
            message: Email message
            context: Additional context for template

        Returns:
            True if alert sent, False otherwise
        """
        trigger = self.get_trigger(trigger_id)

        if not trigger:
            logger.error(f"Trigger not found: {trigger_id}")
            return False

        if not trigger.enabled:
            logger.debug(f"Trigger disabled: {trigger_id}")
            return False

        context = context or {}

        # Check cooldown
        if self._is_in_cooldown(trigger_id, context, trigger.cooldown_minutes):
            logger.info(f"Alert {trigger_id} skipped due to cooldown")
            return False

        # Send alert
        try:
            success = await email_alert_service.send_alert(
                alert_type=trigger.alert_type,
                subject=subject,
                message=message,
                recipients=trigger.recipients,
                context={
                    **context,
                    "trigger_id": trigger_id,
                    "trigger_name": trigger.name,
                    "priority": trigger.priority
                }
            )

            if success:
                # Set cooldown
                self._set_cooldown(trigger_id, context, trigger.cooldown_minutes)

                # Log to history
                self._log_alert_sent(trigger_id, subject, context)

                logger.info(f"Alert sent: {trigger_id}")
                return True
            else:
                logger.warning(f"Alert send failed: {trigger_id}")
                return False

        except Exception as e:
            logger.error(f"Error sending alert {trigger_id}: {e}")
            return False

    async def check_trigger_condition(self, trigger_id: str) -> tuple[bool, Dict]:
        """
        Check if trigger condition is met

        Args:
            trigger_id: Trigger to check

        Returns:
            (should_trigger: bool, context: dict)
        """
        trigger = self.get_trigger(trigger_id)

        if not trigger:
            return False, {}

        if not trigger.enabled:
            return False, {}

        try:
            # Call condition function
            should_trigger, context = await trigger.condition_func()
            return should_trigger, context

        except Exception as e:
            logger.error(f"Error checking trigger {trigger_id}: {e}")
            return False, {}

    async def check_all_triggers(self) -> Dict[str, bool]:
        """
        Check all registered triggers

        Returns:
            Dict mapping trigger_id to success status
        """
        results = {}

        for trigger_id, trigger in self.triggers.items():
            if not trigger.enabled:
                continue

            try:
                should_trigger, context = await self.check_trigger_condition(trigger_id)

                if should_trigger:
                    # Build alert subject/message from context
                    subject = context.get('subject', f"Alert: {trigger.name}")
                    message = context.get('message', f"Trigger {trigger.name} activated")

                    success = await self.check_and_send(
                        trigger_id=trigger_id,
                        subject=subject,
                        message=message,
                        context=context
                    )

                    results[trigger_id] = success
                else:
                    results[trigger_id] = False

            except Exception as e:
                logger.error(f"Error checking trigger {trigger_id}: {e}")
                results[trigger_id] = False

        return results

    def _log_alert_sent(self, trigger_id: str, subject: str, context: Dict):
        """
        Log alert to history (in-memory and database)

        Args:
            trigger_id: Trigger ID
            subject: Email subject
            context: Alert context
        """
        entry = {
            "trigger_id": trigger_id,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }

        # In-memory cache (limited to 1000 entries)
        self.alert_history.append(entry)
        if len(self.alert_history) > 1000:
            self.alert_history.pop(0)

        # Database log (async, non-blocking)
        try:
            import os
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'unicorn'),
                password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
                database=os.getenv('POSTGRES_DB', 'unicorn_db')
            )
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO alert_trigger_history (
                    trigger_id, subject, context, created_at
                ) VALUES (%s, %s, %s, NOW())
            """, (trigger_id, subject, json.dumps(context)))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.warning(f"Failed to log alert to database: {e}")

    def get_alert_history(
        self,
        trigger_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get alert history

        Args:
            trigger_id: Filter by trigger ID (optional)
            limit: Maximum entries to return

        Returns:
            List of alert history entries
        """
        history = self.alert_history

        if trigger_id:
            history = [h for h in history if h['trigger_id'] == trigger_id]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get trigger statistics

        Returns:
            Statistics dict
        """
        total_triggers = len(self.triggers)
        enabled_triggers = sum(1 for t in self.triggers.values() if t.enabled)

        # Count by alert type
        by_type = {}
        for trigger in self.triggers.values():
            by_type[trigger.alert_type] = by_type.get(trigger.alert_type, 0) + 1

        # Count by priority
        by_priority = {}
        for trigger in self.triggers.values():
            by_priority[trigger.priority] = by_priority.get(trigger.priority, 0) + 1

        return {
            "total_triggers": total_triggers,
            "enabled_triggers": enabled_triggers,
            "disabled_triggers": total_triggers - enabled_triggers,
            "by_alert_type": by_type,
            "by_priority": by_priority,
            "total_alerts_sent": len(self.alert_history)
        }


# Singleton instance
alert_trigger_manager = AlertTriggerManager()
