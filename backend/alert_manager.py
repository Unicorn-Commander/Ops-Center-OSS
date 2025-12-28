"""
Alert Manager

System alert generation and management.
Monitors system health and generates alerts for issues requiring attention.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import psutil
import docker
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert types."""
    HIGH_CPU = "high_cpu"
    LOW_MEMORY = "low_memory"
    LOW_DISK = "low_disk"
    SERVICE_DOWN = "service_down"
    SERVICE_UNHEALTHY = "service_unhealthy"
    HIGH_TEMPERATURE = "high_temperature"
    NETWORK_ERRORS = "network_errors"
    BACKUP_FAILED = "backup_failed"
    SECURITY_WARNING = "security_warning"
    DISK_IO_HIGH = "disk_io_high"
    SWAP_USAGE_HIGH = "swap_usage_high"


class Alert:
    """Alert data structure."""

    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Optional[Dict] = None,
        dismissible: bool = True
    ):
        self.id = f"{alert_type}_{int(datetime.utcnow().timestamp())}"
        self.type = alert_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.dismissible = dismissible
        self.dismissed = False

    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "dismissible": self.dismissible,
            "dismissed": self.dismissed
        }


class AlertManager:
    """
    Manage system alerts and notifications.

    Features:
    - Automatic alert generation based on thresholds
    - Alert deduplication and persistence
    - Alert dismissal and history
    - Configurable thresholds
    """

    # Alert thresholds
    CPU_WARNING = 80  # % CPU usage
    CPU_CRITICAL = 95

    MEMORY_WARNING = 80  # % memory used
    MEMORY_CRITICAL = 95

    DISK_WARNING = 80  # % disk used
    DISK_CRITICAL = 90

    SWAP_WARNING = 50  # % swap used

    TEMPERATURE_WARNING = 80  # °C
    TEMPERATURE_CRITICAL = 90

    NETWORK_ERROR_RATE = 0.01  # 1% error rate

    # Alert persistence durations
    ALERT_MIN_DURATION = 60  # Seconds before re-alerting
    ALERT_HISTORY_RETENTION = timedelta(days=7)

    def __init__(self):
        """Initialize alert manager."""
        self.active_alerts: Dict[str, Alert] = {}
        self.dismissed_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_check_times: Dict[str, datetime] = {}

        # Track persistent issues (for duration-based alerts)
        self.persistent_issues: Dict[str, datetime] = {}

    async def check_alerts(self) -> List[Dict]:
        """
        Check for new alerts based on system metrics.

        Returns:
            List of active alerts
        """
        try:
            new_alerts = []

            # Check CPU
            cpu_alerts = await self._check_cpu_alerts()
            new_alerts.extend(cpu_alerts)

            # Check Memory
            memory_alerts = await self._check_memory_alerts()
            new_alerts.extend(memory_alerts)

            # Check Disk
            disk_alerts = await self._check_disk_alerts()
            new_alerts.extend(disk_alerts)

            # Check Services
            service_alerts = await self._check_service_alerts()
            new_alerts.extend(service_alerts)

            # Check Network
            network_alerts = await self._check_network_alerts()
            new_alerts.extend(network_alerts)

            # Check Temperature
            temp_alerts = await self._check_temperature_alerts()
            new_alerts.extend(temp_alerts)

            # Add new alerts to active alerts
            for alert in new_alerts:
                if alert.id not in self.active_alerts and alert.id not in self.dismissed_alerts:
                    self.active_alerts[alert.id] = alert
                    self.alert_history.append(alert)
                    logger.info(f"New alert: {alert.type.value} - {alert.message}")

            # Cleanup old alerts
            self._cleanup_old_alerts()

            return [a.to_dict() for a in self.active_alerts.values() if not a.dismissed]

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []

    async def _check_cpu_alerts(self) -> List[Alert]:
        """Check for CPU-related alerts."""
        alerts = []

        try:
            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent >= self.CPU_CRITICAL:
                alerts.append(Alert(
                    alert_type=AlertType.HIGH_CPU,
                    severity=AlertSeverity.CRITICAL,
                    message=f"CPU usage critical: {cpu_percent:.1f}%",
                    details={
                        "cpu_percent": cpu_percent,
                        "threshold": self.CPU_CRITICAL,
                        "recommendation": "Stop non-essential services immediately"
                    }
                ))
            elif cpu_percent >= self.CPU_WARNING:
                # Only alert if sustained for 5 minutes
                if self._is_persistent_issue("high_cpu", duration_seconds=300):
                    alerts.append(Alert(
                        alert_type=AlertType.HIGH_CPU,
                        severity=AlertSeverity.WARNING,
                        message=f"CPU usage elevated: {cpu_percent:.1f}%",
                        details={
                            "cpu_percent": cpu_percent,
                            "threshold": self.CPU_WARNING,
                            "recommendation": "Monitor CPU-intensive processes"
                        }
                    ))
            else:
                # Clear persistent issue
                self._clear_persistent_issue("high_cpu")

        except Exception as e:
            logger.error(f"CPU alert check error: {e}")

        return alerts

    async def _check_memory_alerts(self) -> List[Alert]:
        """Check for memory-related alerts."""
        alerts = []

        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Check memory
            if mem.percent >= self.MEMORY_CRITICAL:
                alerts.append(Alert(
                    alert_type=AlertType.LOW_MEMORY,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Memory critically low: {mem.available / (1024**3):.1f} GB available",
                    details={
                        "memory_percent": mem.percent,
                        "available_gb": mem.available / (1024**3),
                        "threshold": self.MEMORY_CRITICAL,
                        "recommendation": "Stop containers or add RAM immediately"
                    }
                ))
            elif mem.percent >= self.MEMORY_WARNING:
                alerts.append(Alert(
                    alert_type=AlertType.LOW_MEMORY,
                    severity=AlertSeverity.WARNING,
                    message=f"Memory usage high: {mem.percent:.1f}%",
                    details={
                        "memory_percent": mem.percent,
                        "available_gb": mem.available / (1024**3),
                        "threshold": self.MEMORY_WARNING,
                        "recommendation": "Monitor memory usage closely"
                    }
                ))

            # Check swap
            if swap.percent >= self.SWAP_WARNING:
                alerts.append(Alert(
                    alert_type=AlertType.SWAP_USAGE_HIGH,
                    severity=AlertSeverity.WARNING,
                    message=f"Swap usage high: {swap.percent:.1f}%",
                    details={
                        "swap_percent": swap.percent,
                        "swap_used_gb": swap.used / (1024**3),
                        "recommendation": "System may be low on RAM"
                    }
                ))

        except Exception as e:
            logger.error(f"Memory alert check error: {e}")

        return alerts

    async def _check_disk_alerts(self) -> List[Alert]:
        """Check for disk-related alerts."""
        alerts = []

        try:
            disk = psutil.disk_usage('/')

            if disk.percent >= self.DISK_CRITICAL:
                alerts.append(Alert(
                    alert_type=AlertType.LOW_DISK,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Disk space critically low: {disk.free / (1024**3):.1f} GB free",
                    details={
                        "disk_percent": disk.percent,
                        "free_gb": disk.free / (1024**3),
                        "threshold": self.DISK_CRITICAL,
                        "recommendation": "Delete files or add storage immediately"
                    }
                ))
            elif disk.percent >= self.DISK_WARNING:
                alerts.append(Alert(
                    alert_type=AlertType.LOW_DISK,
                    severity=AlertSeverity.WARNING,
                    message=f"Disk space low: {disk.percent:.1f}% used",
                    details={
                        "disk_percent": disk.percent,
                        "free_gb": disk.free / (1024**3),
                        "threshold": self.DISK_WARNING,
                        "recommendation": "Consider cleanup or expansion"
                    }
                ))

        except Exception as e:
            logger.error(f"Disk alert check error: {e}")

        return alerts

    async def _check_service_alerts(self) -> List[Alert]:
        """Check for service-related alerts."""
        alerts = []

        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)

            stopped_services = []
            unhealthy_services = []

            for container in containers:
                if container.status != 'running':
                    stopped_services.append(container.name)
                else:
                    health = container.attrs.get('State', {}).get('Health', {}).get('Status')
                    if health == 'unhealthy':
                        unhealthy_services.append(container.name)

            # Alert for stopped services
            if stopped_services:
                alerts.append(Alert(
                    alert_type=AlertType.SERVICE_DOWN,
                    severity=AlertSeverity.ERROR,
                    message=f"{len(stopped_services)} service(s) stopped",
                    details={
                        "services": stopped_services,
                        "count": len(stopped_services),
                        "recommendation": "Check logs and restart services"
                    }
                ))

            # Alert for unhealthy services
            if unhealthy_services:
                alerts.append(Alert(
                    alert_type=AlertType.SERVICE_UNHEALTHY,
                    severity=AlertSeverity.WARNING,
                    message=f"{len(unhealthy_services)} service(s) unhealthy",
                    details={
                        "services": unhealthy_services,
                        "count": len(unhealthy_services),
                        "recommendation": "Investigate health check failures"
                    }
                ))

        except Exception as e:
            logger.error(f"Service alert check error: {e}")

        return alerts

    async def _check_network_alerts(self) -> List[Alert]:
        """Check for network-related alerts."""
        alerts = []

        try:
            net_io = psutil.net_io_counters()

            # Calculate error rate
            total_packets = net_io.packets_sent + net_io.packets_recv
            total_errors = net_io.errin + net_io.errout

            if total_packets > 0:
                error_rate = total_errors / total_packets

                if error_rate >= self.NETWORK_ERROR_RATE:
                    alerts.append(Alert(
                        alert_type=AlertType.NETWORK_ERRORS,
                        severity=AlertSeverity.WARNING,
                        message=f"Network errors detected: {error_rate:.2%}",
                        details={
                            "error_rate": error_rate,
                            "total_errors": total_errors,
                            "total_packets": total_packets,
                            "recommendation": "Check network connectivity"
                        }
                    ))

        except Exception as e:
            logger.error(f"Network alert check error: {e}")

        return alerts

    async def _check_temperature_alerts(self) -> List[Alert]:
        """Check for temperature-related alerts."""
        alerts = []

        try:
            # Try CPU temperatures
            if hasattr(psutil, 'sensors_temperatures'):
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    for entry in entries:
                        if entry.current >= self.TEMPERATURE_CRITICAL:
                            alerts.append(Alert(
                                alert_type=AlertType.HIGH_TEMPERATURE,
                                severity=AlertSeverity.CRITICAL,
                                message=f"{entry.label or name} critically hot: {entry.current:.1f}°C",
                                details={
                                    "sensor": entry.label or name,
                                    "temperature": entry.current,
                                    "threshold": self.TEMPERATURE_CRITICAL,
                                    "recommendation": "Check cooling system immediately"
                                }
                            ))
                        elif entry.current >= self.TEMPERATURE_WARNING:
                            alerts.append(Alert(
                                alert_type=AlertType.HIGH_TEMPERATURE,
                                severity=AlertSeverity.WARNING,
                                message=f"{entry.label or name} temperature high: {entry.current:.1f}°C",
                                details={
                                    "sensor": entry.label or name,
                                    "temperature": entry.current,
                                    "threshold": self.TEMPERATURE_WARNING,
                                    "recommendation": "Monitor temperature closely"
                                }
                            ))

        except Exception as e:
            logger.debug(f"Temperature alert check error: {e}")

        return alerts

    def _is_persistent_issue(self, issue_key: str, duration_seconds: int) -> bool:
        """
        Check if an issue has persisted for the specified duration.

        Args:
            issue_key: Unique key for the issue
            duration_seconds: Required duration in seconds

        Returns:
            True if issue has persisted long enough
        """
        now = datetime.utcnow()

        if issue_key not in self.persistent_issues:
            self.persistent_issues[issue_key] = now
            return False

        elapsed = (now - self.persistent_issues[issue_key]).total_seconds()
        return elapsed >= duration_seconds

    def _clear_persistent_issue(self, issue_key: str):
        """Clear a persistent issue."""
        if issue_key in self.persistent_issues:
            del self.persistent_issues[issue_key]

    def _cleanup_old_alerts(self):
        """Remove old alerts from history."""
        cutoff = datetime.utcnow() - self.ALERT_HISTORY_RETENTION

        # Clean history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff
        ]

        # Clean dismissed alerts older than retention period
        self.dismissed_alerts = {
            alert_id: alert for alert_id, alert in self.dismissed_alerts.items()
            if alert.timestamp > cutoff
        }

    async def dismiss_alert(self, alert_id: str) -> bool:
        """
        Dismiss an active alert.

        Args:
            alert_id: Alert ID to dismiss

        Returns:
            True if alert was dismissed, False if not found
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            if alert.dismissible:
                alert.dismissed = True
                self.dismissed_alerts[alert_id] = alert
                del self.active_alerts[alert_id]
                logger.info(f"Alert dismissed: {alert_id}")
                return True

        return False

    async def get_active_alerts(self) -> List[Dict]:
        """
        Get all active (non-dismissed) alerts.

        Returns:
            List of alert dictionaries
        """
        return [
            alert.to_dict() for alert in self.active_alerts.values()
            if not alert.dismissed
        ]

    async def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity (optional)

        Returns:
            List of alert dictionaries
        """
        history = self.alert_history

        if severity:
            history = [a for a in history if a.severity == severity]

        # Sort by timestamp (newest first)
        history = sorted(history, key=lambda a: a.timestamp, reverse=True)

        return [alert.to_dict() for alert in history[:limit]]

    def get_alert_summary(self) -> Dict:
        """
        Get summary of current alerts.

        Returns:
            Dictionary with alert counts by severity
        """
        active = [a for a in self.active_alerts.values() if not a.dismissed]

        summary = {
            "total": len(active),
            "critical": len([a for a in active if a.severity == AlertSeverity.CRITICAL]),
            "error": len([a for a in active if a.severity == AlertSeverity.ERROR]),
            "warning": len([a for a in active if a.severity == AlertSeverity.WARNING]),
            "info": len([a for a in active if a.severity == AlertSeverity.INFO]),
            "dismissed": len(self.dismissed_alerts),
            "history_count": len(self.alert_history)
        }

        return summary
