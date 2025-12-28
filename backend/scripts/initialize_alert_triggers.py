#!/usr/bin/env python3
"""
Initialize Default Alert Triggers
Version: 1.0.0
Author: Backend Team Lead
Date: November 29, 2025

Purpose: Register default alert triggers for production use.

Default Triggers:
1. Service Health Monitor (system_critical)
2. Database Error Monitor (system_critical)
3. Payment Failure Monitor (billing)
4. Failed Login Monitor (security)
5. Quota Usage Monitor (usage)
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert_triggers import alert_trigger_manager
from alert_conditions import (
    check_service_health,
    check_database_errors,
    check_api_failures,
    check_payment_failures,
    check_subscription_expiring,
    check_failed_logins,
    check_api_key_compromise,
    check_quota_usage,
    check_quota_exceeded
)


def initialize_default_triggers():
    """
    Register default alert triggers

    Configuration:
    - Admin email from environment variable ADMIN_EMAIL
    - Cooldown periods optimized for production
    - All triggers enabled by default
    """
    # Get admin email from environment
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    support_email = os.getenv('SUPPORT_EMAIL', 'support@your-domain.com')

    print(f"Initializing alert triggers...")
    print(f"Admin email: {admin_email}")
    print(f"Support email: {support_email}")
    print()

    # ===== SYSTEM CRITICAL TRIGGERS =====

    print("Registering system critical triggers...")

    # 1. Service Health Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="service-health",
        name="Service Health Monitor",
        alert_type="system_critical",
        condition_func=check_service_health,
        recipients=[admin_email],
        cooldown_minutes=30,  # Alert every 30 minutes if service down
        priority="critical",
        metadata={
            "description": "Monitors Docker container health status",
            "condition_name": "check_service_health"
        }
    )
    print("✓ Registered: Service Health Monitor")

    # 2. Database Error Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="database-errors",
        name="Database Error Monitor",
        alert_type="system_critical",
        condition_func=check_database_errors,
        recipients=[admin_email],
        cooldown_minutes=60,  # Alert hourly if database down
        priority="critical",
        metadata={
            "description": "Monitors PostgreSQL connection health",
            "condition_name": "check_database_errors"
        }
    )
    print("✓ Registered: Database Error Monitor")

    # 3. API Failure Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="api-failures",
        name="API Failure Monitor",
        alert_type="system_critical",
        condition_func=check_api_failures,
        recipients=[admin_email],
        cooldown_minutes=120,  # Alert every 2 hours if high error rate
        priority="high",
        metadata={
            "description": "Monitors API error rate (> 10% triggers alert)",
            "condition_name": "check_api_failures"
        }
    )
    print("✓ Registered: API Failure Monitor")

    # ===== BILLING TRIGGERS =====

    print("\nRegistering billing triggers...")

    # 4. Payment Failure Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="payment-failures",
        name="Payment Failure Monitor",
        alert_type="billing",
        condition_func=check_payment_failures,
        recipients=[admin_email, support_email],
        cooldown_minutes=60,  # Alert hourly for payment failures
        priority="high",
        metadata={
            "description": "Monitors Stripe payment failures",
            "condition_name": "check_payment_failures"
        }
    )
    print("✓ Registered: Payment Failure Monitor")

    # 5. Subscription Expiring Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="subscription-expiring",
        name="Subscription Expiring Monitor",
        alert_type="billing",
        condition_func=check_subscription_expiring,
        recipients=[support_email],
        cooldown_minutes=1440,  # Alert daily (24 hours)
        priority="medium",
        metadata={
            "description": "Monitors subscriptions expiring in next 7 days",
            "condition_name": "check_subscription_expiring"
        }
    )
    print("✓ Registered: Subscription Expiring Monitor")

    # ===== SECURITY TRIGGERS =====

    print("\nRegistering security triggers...")

    # 6. Failed Login Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="failed-logins",
        name="Failed Login Monitor",
        alert_type="security",
        condition_func=check_failed_logins,
        recipients=[admin_email],
        cooldown_minutes=60,  # Alert hourly for suspicious logins
        priority="high",
        metadata={
            "description": "Monitors failed login attempts (5+ in 10 min)",
            "condition_name": "check_failed_logins"
        }
    )
    print("✓ Registered: Failed Login Monitor")

    # 7. API Key Compromise Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="api-key-compromise",
        name="API Key Compromise Monitor",
        alert_type="security",
        condition_func=check_api_key_compromise,
        recipients=[admin_email],
        cooldown_minutes=30,  # Alert every 30 minutes for suspicious keys
        priority="critical",
        metadata={
            "description": "Monitors suspicious API key usage patterns",
            "condition_name": "check_api_key_compromise"
        }
    )
    print("✓ Registered: API Key Compromise Monitor")

    # ===== USAGE TRIGGERS =====

    print("\nRegistering usage triggers...")

    # 8. Quota Usage Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="quota-usage",
        name="Quota Usage Monitor",
        alert_type="usage",
        condition_func=check_quota_usage,
        recipients=[support_email],
        cooldown_minutes=1440,  # Alert daily (users notified individually)
        priority="medium",
        metadata={
            "description": "Monitors users at 80%+ API quota",
            "condition_name": "check_quota_usage"
        }
    )
    print("✓ Registered: Quota Usage Monitor")

    # 9. Quota Exceeded Monitor
    alert_trigger_manager.register_trigger(
        trigger_id="quota-exceeded",
        name="Quota Exceeded Monitor",
        alert_type="usage",
        condition_func=check_quota_exceeded,
        recipients=[support_email],
        cooldown_minutes=1440,  # Alert daily (users notified individually)
        priority="high",
        metadata={
            "description": "Monitors users who exceeded API quota",
            "condition_name": "check_quota_exceeded"
        }
    )
    print("✓ Registered: Quota Exceeded Monitor")

    # ===== SUMMARY =====

    print("\n" + "=" * 60)
    print("Alert Triggers Initialization Complete")
    print("=" * 60)

    stats = alert_trigger_manager.get_statistics()

    print(f"\nTotal Triggers: {stats['total_triggers']}")
    print(f"Enabled: {stats['enabled_triggers']}")
    print(f"\nBy Alert Type:")
    for alert_type, count in stats['by_alert_type'].items():
        print(f"  - {alert_type}: {count}")

    print(f"\nBy Priority:")
    for priority, count in stats['by_priority'].items():
        print(f"  - {priority}: {count}")

    print("\n✅ All triggers registered successfully!")


async def test_triggers():
    """Test all triggers"""
    print("\n" + "=" * 60)
    print("Testing Alert Triggers")
    print("=" * 60)

    results = await alert_trigger_manager.check_all_triggers()

    print(f"\nChecked {len(results)} triggers")

    for trigger_id, success in results.items():
        status = "✓ SENT" if success else "○ No alert needed"
        print(f"{status}: {trigger_id}")

    alerts_sent = sum(1 for success in results.values() if success)
    print(f"\n📧 Alerts sent: {alerts_sent}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize alert triggers")
    parser.add_argument('--test', action='store_true', help='Test all triggers after initialization')
    args = parser.parse_args()

    # Initialize triggers
    initialize_default_triggers()

    # Test if requested
    if args.test:
        asyncio.run(test_triggers())
