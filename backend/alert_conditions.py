"""
Alert Trigger Conditions for Ops-Center
Version: 1.0.0
Author: Backend Team Lead
Date: November 29, 2025

Purpose: Define conditions that trigger automated email alerts.

Trigger Types:
1. System Critical - Service health, errors, resource exhaustion
2. Billing - Payment failures, subscription changes
3. Security - Failed logins, suspicious activity
4. Usage - Quota warnings, tier limits
"""

import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Tuple, Dict, Any
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ==================== DATABASE HELPERS ====================

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
        database=os.getenv('POSTGRES_DB', 'unicorn_db')
    )


# ==================== SYSTEM CRITICAL CONDITIONS ====================

async def check_service_health() -> Tuple[bool, Dict[str, Any]]:
    """
    Check if any critical services are down

    Triggers when:
    - Any service health check fails
    - Service has been down for > 5 minutes

    Returns:
        (should_trigger, context)
    """
    try:
        # Check Docker container health
        import subprocess
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return True, {
                'subject': '🚨 CRITICAL: Docker service check failed',
                'message': 'Unable to check Docker container status',
                'error': result.stderr,
                'severity': 'critical'
            }

        # Parse container status
        down_services = []
        for line in result.stdout.strip().split('\n'):
            if '\t' in line:
                name, status = line.split('\t', 1)
                if 'unhealthy' in status.lower() or 'exited' in status.lower():
                    down_services.append({'name': name, 'status': status})

        if down_services:
            return True, {
                'subject': f'🚨 CRITICAL: {len(down_services)} service(s) down',
                'message': f"The following services are unhealthy: {', '.join(s['name'] for s in down_services)}",
                'services': down_services,
                'severity': 'critical',
                'action_required': 'Immediate investigation required'
            }

        return False, {}

    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        return True, {
            'subject': '🚨 CRITICAL: Service health check error',
            'message': f'Health check failed with error: {str(e)}',
            'severity': 'critical'
        }


async def check_database_errors() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for database connection errors

    Triggers when:
    - Database connection fails
    - Database error rate is high

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Test query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result or result['test'] != 1:
            return True, {
                'subject': '🚨 CRITICAL: Database health check failed',
                'message': 'Database query returned unexpected result',
                'severity': 'critical'
            }

        return False, {}

    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return True, {
            'subject': '🚨 CRITICAL: Database connection error',
            'message': f'Unable to connect to PostgreSQL: {str(e)}',
            'severity': 'critical',
            'action_required': 'Check database service and credentials'
        }


async def check_api_failures() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for high API error rate

    Triggers when:
    - API error rate > 10% in last 10 minutes

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check audit logs for recent errors (if table exists)
        cursor.execute("""
            SELECT COUNT(*) as error_count
            FROM audit_logs
            WHERE created_at > NOW() - INTERVAL '10 minutes'
              AND (status_code >= 500 OR status_code = 0)
        """)
        result = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as total_count
            FROM audit_logs
            WHERE created_at > NOW() - INTERVAL '10 minutes'
        """)
        total_result = cursor.fetchone()

        cursor.close()
        conn.close()

        error_count = result['error_count'] if result else 0
        total_count = total_result['total_count'] if total_result else 0

        if total_count > 0:
            error_rate = (error_count / total_count) * 100

            if error_rate > 10:
                return True, {
                    'subject': f'⚠️ WARNING: High API error rate ({error_rate:.1f}%)',
                    'message': f'{error_count} errors out of {total_count} requests in last 10 minutes',
                    'error_rate': error_rate,
                    'error_count': error_count,
                    'total_count': total_count,
                    'severity': 'high'
                }

        return False, {}

    except Exception as e:
        logger.warning(f"API failure check error: {e}")
        return False, {}


# ==================== BILLING CONDITIONS ====================

async def check_payment_failures() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for recent payment failures from Stripe webhooks

    Triggers when:
    - Payment status = "failed" in last hour

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check for recent payment failures
        cursor.execute("""
            SELECT user_email, amount, stripe_payment_id, created_at
            FROM billing_events
            WHERE event_type = 'payment_failed'
              AND created_at > NOW() - INTERVAL '1 hour'
              AND notified = false
            ORDER BY created_at DESC
            LIMIT 10
        """)
        failures = cursor.fetchall()

        if failures:
            # Mark as notified
            for failure in failures:
                cursor.execute("""
                    UPDATE billing_events
                    SET notified = true
                    WHERE stripe_payment_id = %s
                """, (failure['stripe_payment_id'],))

            conn.commit()

        cursor.close()
        conn.close()

        if failures:
            return True, {
                'subject': f'💳 BILLING ALERT: {len(failures)} payment failure(s)',
                'message': f"Payment failures detected for {len(failures)} user(s)",
                'failures': [dict(f) for f in failures],
                'count': len(failures),
                'severity': 'high'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"Payment failure check error: {e}")
        return False, {}


async def check_subscription_expiring() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for subscriptions expiring in next 7 days

    Triggers when:
    - Subscription end_date within 7 days
    - User hasn't been notified yet

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT user_email, tier_code, end_date
            FROM user_subscriptions
            WHERE end_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
              AND renewal_notified = false
            ORDER BY end_date ASC
            LIMIT 10
        """)
        expiring = cursor.fetchall()

        if expiring:
            # Mark as notified
            for sub in expiring:
                cursor.execute("""
                    UPDATE user_subscriptions
                    SET renewal_notified = true
                    WHERE user_email = %s
                """, (sub['user_email'],))

            conn.commit()

        cursor.close()
        conn.close()

        if expiring:
            return True, {
                'subject': f'⏰ REMINDER: {len(expiring)} subscription(s) expiring soon',
                'message': f'{len(expiring)} subscriptions will expire in the next 7 days',
                'subscriptions': [dict(s) for s in expiring],
                'severity': 'medium'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"Subscription expiring check error: {e}")
        return False, {}


# ==================== SECURITY CONDITIONS ====================

async def check_failed_logins() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for multiple failed login attempts

    Triggers when:
    - 5+ failed login attempts from same IP in 10 minutes

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT ip_address, COUNT(*) as attempt_count, MAX(created_at) as last_attempt
            FROM audit_logs
            WHERE action = 'login_failed'
              AND created_at > NOW() - INTERVAL '10 minutes'
            GROUP BY ip_address
            HAVING COUNT(*) >= 5
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        suspicious_ips = cursor.fetchall()

        cursor.close()
        conn.close()

        if suspicious_ips:
            return True, {
                'subject': f'🔒 SECURITY ALERT: {len(suspicious_ips)} IP(s) with failed login attempts',
                'message': f'Detected {len(suspicious_ips)} IP addresses with 5+ failed logins',
                'ips': [dict(ip) for ip in suspicious_ips],
                'severity': 'high',
                'action_required': 'Consider IP blocking or rate limiting'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"Failed login check error: {e}")
        return False, {}


async def check_api_key_compromise() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for suspicious API key usage

    Triggers when:
    - API key used from unusual location
    - Rapid increase in API usage

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check for API keys with unusual usage patterns
        cursor.execute("""
            SELECT api_key_id, user_id, COUNT(*) as request_count,
                   COUNT(DISTINCT ip_address) as ip_count
            FROM audit_logs
            WHERE created_at > NOW() - INTERVAL '1 hour'
              AND api_key_id IS NOT NULL
            GROUP BY api_key_id, user_id
            HAVING COUNT(*) > 1000 OR COUNT(DISTINCT ip_address) > 5
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)
        suspicious_keys = cursor.fetchall()

        cursor.close()
        conn.close()

        if suspicious_keys:
            return True, {
                'subject': f'🔐 SECURITY: Suspicious API key activity detected',
                'message': f'{len(suspicious_keys)} API key(s) showing unusual patterns',
                'keys': [dict(k) for k in suspicious_keys],
                'severity': 'critical',
                'action_required': 'Investigate and potentially revoke keys'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"API key compromise check error: {e}")
        return False, {}


# ==================== USAGE CONDITIONS ====================

async def check_quota_usage() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for users approaching API quota limits

    Triggers when:
    - User has used >= 80% of quota
    - User has used >= 95% of quota

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT user_id, user_email, tier_code,
                   api_calls_used, api_calls_limit,
                   (api_calls_used::float / api_calls_limit::float * 100) as usage_percent
            FROM user_subscriptions
            WHERE api_calls_limit > 0
              AND (api_calls_used::float / api_calls_limit::float) >= 0.80
              AND quota_warning_sent = false
            ORDER BY (api_calls_used::float / api_calls_limit::float) DESC
            LIMIT 20
        """)
        high_usage_users = cursor.fetchall()

        if high_usage_users:
            # Mark as notified
            for user in high_usage_users:
                cursor.execute("""
                    UPDATE user_subscriptions
                    SET quota_warning_sent = true
                    WHERE user_id = %s
                """, (user['user_id'],))

            conn.commit()

        cursor.close()
        conn.close()

        if high_usage_users:
            critical_users = [u for u in high_usage_users if u['usage_percent'] >= 95]
            warning_users = [u for u in high_usage_users if 80 <= u['usage_percent'] < 95]

            return True, {
                'subject': f'📊 USAGE ALERT: {len(high_usage_users)} user(s) approaching quota',
                'message': f'{len(critical_users)} users at 95%+, {len(warning_users)} users at 80%+',
                'critical_users': [dict(u) for u in critical_users],
                'warning_users': [dict(u) for u in warning_users],
                'severity': 'medium'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"Quota usage check error: {e}")
        return False, {}


async def check_quota_exceeded() -> Tuple[bool, Dict[str, Any]]:
    """
    Check for users who have exceeded quota

    Triggers when:
    - User has used > 100% of quota

    Returns:
        (should_trigger, context)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT user_id, user_email, tier_code,
                   api_calls_used, api_calls_limit
            FROM user_subscriptions
            WHERE api_calls_limit > 0
              AND api_calls_used > api_calls_limit
              AND quota_exceeded_sent = false
            ORDER BY (api_calls_used - api_calls_limit) DESC
            LIMIT 10
        """)
        exceeded_users = cursor.fetchall()

        if exceeded_users:
            # Mark as notified
            for user in exceeded_users:
                cursor.execute("""
                    UPDATE user_subscriptions
                    SET quota_exceeded_sent = true
                    WHERE user_id = %s
                """, (user['user_id'],))

            conn.commit()

        cursor.close()
        conn.close()

        if exceeded_users:
            return True, {
                'subject': f'🚫 ALERT: {len(exceeded_users)} user(s) exceeded quota',
                'message': f'{len(exceeded_users)} users have exceeded their API quota',
                'users': [dict(u) for u in exceeded_users],
                'severity': 'high',
                'action_required': 'Users should upgrade tier or requests will be blocked'
            }

        return False, {}

    except Exception as e:
        logger.warning(f"Quota exceeded check error: {e}")
        return False, {}
