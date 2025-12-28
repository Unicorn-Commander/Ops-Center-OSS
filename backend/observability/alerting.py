"""
Alerting Rules and Thresholds

Defines alert conditions for:
- API error rates
- Response time degradation
- Credit pool depletion
- Failed payments
- Security events
- Service availability

Can be exported to Prometheus AlertManager or similar systems.
"""

from typing import Dict, List, Any
from datetime import timedelta


class AlertingRules:
    """
    Alerting rules configuration for Ops-Center.

    Can be used to:
    1. Generate Prometheus alert rules
    2. Configure AlertManager
    3. Define thresholds for custom alerting
    """

    @staticmethod
    def get_all_rules() -> List[Dict[str, Any]]:
        """
        Get all alerting rules.

        Returns:
            List of alert rule definitions
        """
        return [
            *AlertingRules.get_api_rules(),
            *AlertingRules.get_billing_rules(),
            *AlertingRules.get_security_rules(),
            *AlertingRules.get_infrastructure_rules(),
            *AlertingRules.get_business_rules()
        ]

    @staticmethod
    def get_api_rules() -> List[Dict[str, Any]]:
        """API performance and availability rules."""
        return [
            {
                "alert": "HighAPIErrorRate",
                "expr": 'rate(ops_center_http_errors_total[5m]) > 0.01',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "api"
                },
                "annotations": {
                    "summary": "High API error rate detected",
                    "description": "API error rate is above 1% for the last 5 minutes. Current rate: {{ $value | humanize }}%"
                }
            },
            {
                "alert": "CriticalAPIErrorRate",
                "expr": 'rate(ops_center_http_errors_total[5m]) > 0.05',
                "for": "2m",
                "labels": {
                    "severity": "critical",
                    "category": "api"
                },
                "annotations": {
                    "summary": "Critical API error rate",
                    "description": "API error rate is above 5% for the last 2 minutes. Immediate attention required. Current rate: {{ $value | humanize }}%"
                }
            },
            {
                "alert": "SlowAPIResponse",
                "expr": 'histogram_quantile(0.95, rate(ops_center_http_request_duration_seconds_bucket[5m])) > 0.5',
                "for": "10m",
                "labels": {
                    "severity": "warning",
                    "category": "api"
                },
                "annotations": {
                    "summary": "Slow API response times",
                    "description": "95th percentile API response time is above 500ms for endpoint {{ $labels.endpoint }}. Current: {{ $value | humanizeDuration }}"
                }
            },
            {
                "alert": "VerySlowAPIResponse",
                "expr": 'histogram_quantile(0.95, rate(ops_center_http_request_duration_seconds_bucket[5m])) > 2.0',
                "for": "5m",
                "labels": {
                    "severity": "critical",
                    "category": "api"
                },
                "annotations": {
                    "summary": "Very slow API response times",
                    "description": "95th percentile API response time is above 2 seconds for endpoint {{ $labels.endpoint }}. Current: {{ $value | humanizeDuration }}"
                }
            },
            {
                "alert": "HighAPIRequestRate",
                "expr": 'rate(ops_center_http_requests_total[1m]) > 1000',
                "for": "5m",
                "labels": {
                    "severity": "info",
                    "category": "api"
                },
                "annotations": {
                    "summary": "High API request rate",
                    "description": "API is receiving more than 1000 requests per second. Current: {{ $value | humanize }} req/s"
                }
            }
        ]

    @staticmethod
    def get_billing_rules() -> List[Dict[str, Any]]:
        """Billing and credit system rules."""
        return [
            {
                "alert": "LowCreditBalance",
                "expr": 'ops_center_credit_balance < 100',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "Low credit balance for user",
                    "description": "User {{ $labels.user_id }} has low credit balance ({{ $value }} credits). Tier: {{ $labels.tier }}"
                }
            },
            {
                "alert": "CriticalCreditBalance",
                "expr": 'ops_center_credit_balance < 10',
                "for": "1m",
                "labels": {
                    "severity": "critical",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "Critical credit balance",
                    "description": "User {{ $labels.user_id }} has critically low credit balance ({{ $value }} credits). Service interruption imminent."
                }
            },
            {
                "alert": "HighCreditUsage",
                "expr": 'rate(ops_center_credit_usage_total[1h]) > 1000',
                "for": "30m",
                "labels": {
                    "severity": "info",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "High credit usage detected",
                    "description": "Organization {{ $labels.organization_id }} is using credits at a high rate ({{ $value }} credits/hour)"
                }
            },
            {
                "alert": "PaymentFailed",
                "expr": 'increase(ops_center_payment_transactions_total{status="failed"}[5m]) > 3',
                "for": "0m",
                "labels": {
                    "severity": "critical",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "Multiple payment failures detected",
                    "description": "{{ $value }} payment failures in the last 5 minutes. Payment method: {{ $labels.payment_method }}"
                }
            },
            {
                "alert": "SubscriptionChurn",
                "expr": 'increase(ops_center_subscription_changes_total{change_type="cancelled"}[24h]) > 10',
                "for": "0m",
                "labels": {
                    "severity": "warning",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "High subscription churn",
                    "description": "{{ $value }} subscriptions cancelled in the last 24 hours. Investigate reasons."
                }
            },
            {
                "alert": "LLMCostSpike",
                "expr": 'rate(ops_center_llm_cost_total[1h]) > (rate(ops_center_llm_cost_total[24h]) * 3)',
                "for": "15m",
                "labels": {
                    "severity": "warning",
                    "category": "billing"
                },
                "annotations": {
                    "summary": "LLM cost spike detected",
                    "description": "LLM costs are 3x higher than 24-hour average for organization {{ $labels.organization_id }}"
                }
            }
        ]

    @staticmethod
    def get_security_rules() -> List[Dict[str, Any]]:
        """Security and authentication rules."""
        return [
            {
                "alert": "HighAuthFailureRate",
                "expr": 'rate(ops_center_auth_failures_total[5m]) > 10',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "security"
                },
                "annotations": {
                    "summary": "High authentication failure rate",
                    "description": "More than 10 authentication failures per second. Possible brute force attack. Method: {{ $labels.method }}"
                }
            },
            {
                "alert": "RateLimitExceeded",
                "expr": 'increase(ops_center_rate_limit_exceeded_total[1m]) > 100',
                "for": "2m",
                "labels": {
                    "severity": "warning",
                    "category": "security"
                },
                "annotations": {
                    "summary": "Rate limit frequently exceeded",
                    "description": "User {{ $labels.user_id }} has exceeded rate limit {{ $value }} times in the last minute"
                }
            },
            {
                "alert": "SuspiciousAPIKeyUsage",
                "expr": 'increase(ops_center_api_key_usage_total[5m]) > 1000',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "security"
                },
                "annotations": {
                    "summary": "Suspicious API key usage",
                    "description": "API key {{ $labels.key_id }} has made {{ $value }} requests in 5 minutes. Possible abuse."
                }
            },
            {
                "alert": "UnauthorizedAccessAttempts",
                "expr": 'increase(ops_center_http_errors_total{status="403"}[5m]) > 50',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "security"
                },
                "annotations": {
                    "summary": "High unauthorized access attempts",
                    "description": "{{ $value }} forbidden (403) errors in the last 5 minutes on endpoint {{ $labels.endpoint }}"
                }
            }
        ]

    @staticmethod
    def get_infrastructure_rules() -> List[Dict[str, Any]]:
        """Infrastructure and service health rules."""
        return [
            {
                "alert": "DatabaseConnectionPoolExhausted",
                "expr": 'ops_center_db_connections_idle{database="unicorn_db"} < 2',
                "for": "5m",
                "labels": {
                    "severity": "critical",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "Database connection pool exhausted",
                    "description": "Less than 2 idle database connections available. Performance will degrade."
                }
            },
            {
                "alert": "SlowDatabaseQueries",
                "expr": 'histogram_quantile(0.95, rate(ops_center_db_query_duration_seconds_bucket[5m])) > 1.0',
                "for": "10m",
                "labels": {
                    "severity": "warning",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "Slow database queries detected",
                    "description": "95th percentile query time is above 1 second for {{ $labels.query_type }} on {{ $labels.table }}"
                }
            },
            {
                "alert": "HighMemoryUsage",
                "expr": 'process_resident_memory_bytes > 2e9',  # 2GB
                "for": "10m",
                "labels": {
                    "severity": "warning",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "High memory usage",
                    "description": "Ops-Center is using {{ $value | humanize }}B of memory. Consider scaling."
                }
            },
            {
                "alert": "KeycloakDown",
                "expr": 'up{job="keycloak"} == 0',
                "for": "2m",
                "labels": {
                    "severity": "critical",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "Keycloak authentication service is down",
                    "description": "Users cannot authenticate. Immediate attention required."
                }
            },
            {
                "alert": "RedisDown",
                "expr": 'up{job="redis"} == 0',
                "for": "2m",
                "labels": {
                    "severity": "critical",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "Redis cache is down",
                    "description": "Session management and caching unavailable. Performance will degrade."
                }
            },
            {
                "alert": "PostgreSQLDown",
                "expr": 'up{job="postgresql"} == 0',
                "for": "1m",
                "labels": {
                    "severity": "critical",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "PostgreSQL database is down",
                    "description": "Critical: Database is unreachable. Service is unavailable."
                }
            },
            {
                "alert": "LiteLLMProxyDown",
                "expr": 'up{job="litellm"} == 0',
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "category": "infrastructure"
                },
                "annotations": {
                    "summary": "LiteLLM proxy is down",
                    "description": "LLM services unavailable. Users cannot make AI requests."
                }
            }
        ]

    @staticmethod
    def get_business_rules() -> List[Dict[str, Any]]:
        """Business metrics and KPIs."""
        return [
            {
                "alert": "LowUserRegistrations",
                "expr": 'increase(ops_center_user_registrations_total[24h]) < 5',
                "for": "0m",
                "labels": {
                    "severity": "info",
                    "category": "business"
                },
                "annotations": {
                    "summary": "Low user registrations",
                    "description": "Only {{ $value }} new registrations in the last 24 hours. Below expected threshold."
                }
            },
            {
                "alert": "LowActiveUsers",
                "expr": 'increase(ops_center_user_logins_total[1h]) < 10',
                "for": "1h",
                "labels": {
                    "severity": "info",
                    "category": "business"
                },
                "annotations": {
                    "summary": "Low user activity",
                    "description": "Only {{ $value }} user logins in the last hour. Check for service issues."
                }
            },
            {
                "alert": "HighFeatureAccessDenials",
                "expr": 'rate(ops_center_feature_access_total{allowed="false"}[1h]) > 100',
                "for": "30m",
                "labels": {
                    "severity": "info",
                    "category": "business"
                },
                "annotations": {
                    "summary": "High feature access denials",
                    "description": "Feature {{ $labels.feature }} is being denied {{ $value }} times per hour. Consider tier adjustments."
                }
            },
            {
                "alert": "WebhookDeliveryFailures",
                "expr": 'increase(ops_center_webhook_deliveries_total{status="failed"}[1h]) > 10',
                "for": "30m",
                "labels": {
                    "severity": "warning",
                    "category": "business"
                },
                "annotations": {
                    "summary": "Webhook delivery failures",
                    "description": "{{ $value }} webhook deliveries failed in the last hour for {{ $labels.event_type }}"
                }
            }
        ]

    @staticmethod
    def export_prometheus_rules(file_path: str = "alerting_rules.yml"):
        """
        Export rules in Prometheus AlertManager format.

        Args:
            file_path: Output file path

        Returns:
            Path to exported file
        """
        import yaml

        rules = AlertingRules.get_all_rules()

        # Group rules by category
        groups = {}
        for rule in rules:
            category = rule["labels"]["category"]
            if category not in groups:
                groups[category] = {
                    "name": f"ops_center_{category}",
                    "interval": "30s",
                    "rules": []
                }
            groups[category]["rules"].append(rule)

        # Create Prometheus rules structure
        prometheus_rules = {
            "groups": list(groups.values())
        }

        # Write to file
        with open(file_path, 'w') as f:
            yaml.dump(prometheus_rules, f, default_flow_style=False, sort_keys=False)

        return file_path

    @staticmethod
    def get_thresholds() -> Dict[str, Any]:
        """
        Get alerting thresholds as a dictionary.

        Useful for custom alerting implementations.

        Returns:
            Dictionary of alert thresholds
        """
        return {
            "api": {
                "error_rate_warning": 0.01,  # 1%
                "error_rate_critical": 0.05,  # 5%
                "response_time_p95_warning": 0.5,  # 500ms
                "response_time_p95_critical": 2.0,  # 2s
                "request_rate_high": 1000  # req/s
            },
            "billing": {
                "credit_balance_warning": 100,
                "credit_balance_critical": 10,
                "credit_usage_high": 1000,  # credits/hour
                "payment_failures": 3,  # in 5min
                "subscription_churn": 10,  # in 24h
                "llm_cost_spike_multiplier": 3
            },
            "security": {
                "auth_failure_rate": 10,  # per second
                "rate_limit_violations": 100,  # in 1min
                "api_key_abuse": 1000,  # requests in 5min
                "unauthorized_attempts": 50  # in 5min
            },
            "infrastructure": {
                "db_connections_min_idle": 2,
                "db_query_time_p95": 1.0,  # 1s
                "memory_usage_bytes": 2e9,  # 2GB
                "service_down_duration": 120  # 2min
            },
            "business": {
                "registrations_min_daily": 5,
                "logins_min_hourly": 10,
                "feature_denials_per_hour": 100,
                "webhook_failures_per_hour": 10
            }
        }
