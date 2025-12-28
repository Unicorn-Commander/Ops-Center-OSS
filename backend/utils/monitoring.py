"""
LLM Hub Monitoring and Analytics Utilities

Provides structured logging, metrics collection, and analytics
for the unified LLM Management system.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback

logger = logging.getLogger("llm_hub")


class EventType(str, Enum):
    """Event types for structured logging."""
    PAGE_VIEW = "page_view"
    FEATURE_USAGE = "feature_usage"
    API_CALL = "api_call"
    ERROR = "error"
    WARNING = "warning"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER_ACTION = "user_action"


class LLMHubMonitor:
    """
    Monitor LLM Hub usage, errors, and performance.

    Provides structured logging for:
    - Page views and navigation
    - Feature usage and adoption
    - API calls and responses
    - Errors and warnings
    - Security events
    - Performance metrics
    """

    @staticmethod
    def _log_event(
        event_type: EventType,
        message: str,
        user_id: Optional[str] = None,
        level: str = "info",
        **kwargs
    ):
        """
        Internal method to log structured events.

        Args:
            event_type: Type of event
            message: Event message
            user_id: Optional user identifier
            level: Log level (debug, info, warning, error, critical)
            **kwargs: Additional context data
        """
        log_data = {
            "event_type": event_type.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            **kwargs
        }

        log_message = f"[{event_type.value.upper()}] {message}"

        # Route to appropriate log level
        log_func = getattr(logger, level, logger.info)
        log_func(log_message, extra=log_data)

    @classmethod
    def log_page_view(
        cls,
        user_id: str,
        page: str,
        tab: Optional[str] = None,
        referrer: Optional[str] = None
    ):
        """
        Log when user views LLM Hub page.

        Args:
            user_id: User identifier
            page: Page name (e.g., 'llm_hub', 'old_provider_keys')
            tab: Active tab (e.g., 'provider_keys', 'model_catalog')
            referrer: Previous page URL
        """
        cls._log_event(
            EventType.PAGE_VIEW,
            f"User viewed {page}",
            user_id=user_id,
            page=page,
            tab=tab,
            referrer=referrer
        )

    @classmethod
    def log_feature_usage(
        cls,
        user_id: str,
        feature: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log feature usage for analytics.

        Args:
            user_id: User identifier
            feature: Feature name (e.g., 'provider_key_management')
            action: Action performed (e.g., 'create', 'update', 'delete')
            details: Optional additional details
        """
        cls._log_event(
            EventType.FEATURE_USAGE,
            f"Feature '{feature}' action '{action}'",
            user_id=user_id,
            feature=feature,
            action=action,
            details=details or {}
        )

    @classmethod
    def log_api_call(
        cls,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """
        Log API call metrics.

        Args:
            user_id: User identifier
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            request_size: Request body size in bytes
            response_size: Response body size in bytes
        """
        cls._log_event(
            EventType.API_CALL,
            f"{method} {endpoint} - {status_code}",
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            request_size=request_size,
            response_size=response_size
        )

    @classmethod
    def log_error(
        cls,
        user_id: Optional[str],
        error: Exception,
        context: Dict[str, Any],
        include_traceback: bool = True
    ):
        """
        Log errors in LLM Hub.

        Args:
            user_id: User identifier (if known)
            error: Exception object
            context: Additional context about the error
            include_traceback: Whether to include full traceback
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }

        if include_traceback:
            error_data["traceback"] = traceback.format_exc()

        cls._log_event(
            EventType.ERROR,
            f"Error: {str(error)}",
            user_id=user_id,
            level="error",
            **error_data
        )

    @classmethod
    def log_warning(
        cls,
        user_id: Optional[str],
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log warnings.

        Args:
            user_id: User identifier (if known)
            message: Warning message
            context: Optional additional context
        """
        cls._log_event(
            EventType.WARNING,
            message,
            user_id=user_id,
            level="warning",
            **(context or {})
        )

    @classmethod
    def log_security_event(
        cls,
        user_id: Optional[str],
        event: str,
        severity: str,
        details: Dict[str, Any]
    ):
        """
        Log security-related events.

        Args:
            user_id: User identifier (if known)
            event: Security event description
            severity: Event severity (low, medium, high, critical)
            details: Event details
        """
        cls._log_event(
            EventType.SECURITY,
            f"Security event: {event}",
            user_id=user_id,
            level="warning" if severity in ["low", "medium"] else "error",
            severity=severity,
            **details
        )

    @classmethod
    def log_performance_metric(
        cls,
        user_id: Optional[str],
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log performance metrics.

        Args:
            user_id: User identifier (if known)
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (ms, bytes, count, etc.)
            context: Optional additional context
        """
        cls._log_event(
            EventType.PERFORMANCE,
            f"Performance metric: {metric_name}",
            user_id=user_id,
            metric_name=metric_name,
            value=value,
            unit=unit,
            **(context or {})
        )

    @classmethod
    def log_user_action(
        cls,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log user actions for audit trail.

        Args:
            user_id: User identifier
            action: Action performed (create, read, update, delete)
            resource_type: Type of resource (provider_key, model, routing_rule)
            resource_id: Resource identifier (if applicable)
            result: Action result (success, failure, partial)
            details: Optional additional details
        """
        cls._log_event(
            EventType.USER_ACTION,
            f"User action: {action} {resource_type}",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            details=details or {}
        )


class FeatureFlagAnalytics:
    """
    Analytics specifically for feature flag adoption.
    """

    @staticmethod
    def log_flag_evaluation(
        flag_name: str,
        user_id: str,
        enabled: bool,
        reason: str
    ):
        """
        Log feature flag evaluation for analytics.

        Args:
            flag_name: Feature flag name
            user_id: User identifier
            enabled: Whether flag was enabled
            reason: Reason for the decision (whitelist, rollout, etc.)
        """
        logger.info(
            f"Feature flag evaluation: {flag_name}",
            extra={
                "event_type": "feature_flag",
                "flag_name": flag_name,
                "user_id": user_id,
                "enabled": enabled,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def log_flag_change(
        flag_name: str,
        changed_by: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any]
    ):
        """
        Log feature flag configuration changes.

        Args:
            flag_name: Feature flag name
            changed_by: User who made the change
            old_config: Previous configuration
            new_config: New configuration
        """
        logger.info(
            f"Feature flag changed: {flag_name}",
            extra={
                "event_type": "feature_flag_change",
                "flag_name": flag_name,
                "changed_by": changed_by,
                "old_config": old_config,
                "new_config": new_config,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class MetricsCollector:
    """
    Collect and aggregate metrics for reporting.
    """

    def __init__(self):
        self.metrics: Dict[str, list] = {}

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for filtering/grouping
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {}
        })

    def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list:
        """
        Retrieve metrics within time range.

        Args:
            metric_name: Name of the metric
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of metric data points
        """
        if metric_name not in self.metrics:
            return []

        metrics = self.metrics[metric_name]

        if start_time or end_time:
            filtered = []
            for metric in metrics:
                timestamp = datetime.fromisoformat(metric["timestamp"])
                if start_time and timestamp < start_time:
                    continue
                if end_time and timestamp > end_time:
                    continue
                filtered.append(metric)
            return filtered

        return metrics

    def clear_metrics(self, metric_name: Optional[str] = None):
        """
        Clear collected metrics.

        Args:
            metric_name: Specific metric to clear, or None for all
        """
        if metric_name:
            self.metrics.pop(metric_name, None)
        else:
            self.metrics.clear()


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience function for quick metric recording
def record_metric(metric_name: str, value: float, **tags):
    """
    Quick function to record a metric.

    Args:
        metric_name: Name of the metric
        value: Metric value
        **tags: Optional tags as keyword arguments
    """
    metrics_collector.record_metric(metric_name, value, tags)
