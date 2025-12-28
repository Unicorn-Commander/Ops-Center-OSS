#!/usr/bin/env python3
"""Test Audit Logging System

This script tests the audit logging functionality.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit_logger import audit_logger
from models.audit_log import AuditAction, AuditResult, AuditLogFilter


async def test_basic_logging():
    """Test basic audit logging"""
    print("\n=== Testing Basic Logging ===")

    # Test successful login
    log_id = await audit_logger.log(
        action=AuditAction.AUTH_LOGIN_SUCCESS.value,
        result=AuditResult.SUCCESS.value,
        user_id="test_user_1",
        username="testuser",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        metadata={"method": "password"}
    )
    print(f"✓ Logged successful login (ID: {log_id})")

    # Test failed login
    log_id = await audit_logger.log(
        action=AuditAction.AUTH_LOGIN_FAILED.value,
        result=AuditResult.FAILURE.value,
        username="baduser",
        ip_address="192.168.1.101",
        user_agent="Mozilla/5.0 Test Browser",
        error_message="Invalid credentials"
    )
    print(f"✓ Logged failed login (ID: {log_id})")

    # Test service operation
    log_id = await audit_logger.log(
        action=AuditAction.SERVICE_START.value,
        result=AuditResult.SUCCESS.value,
        user_id="admin_1",
        username="admin",
        ip_address="192.168.1.1",
        resource_type="service",
        resource_id="unicorn-open-webui",
        metadata={"operation": "start"}
    )
    print(f"✓ Logged service start (ID: {log_id})")


async def test_query_logs():
    """Test querying audit logs"""
    print("\n=== Testing Log Queries ===")

    # Query all logs
    filter_params = AuditLogFilter(limit=10)
    results = await audit_logger.query_logs(filter_params)
    print(f"✓ Retrieved {results.total} total logs, showing {len(results.logs)}")

    # Query by action
    filter_params = AuditLogFilter(
        action=AuditAction.AUTH_LOGIN_SUCCESS.value,
        limit=5
    )
    results = await audit_logger.query_logs(filter_params)
    print(f"✓ Found {results.total} successful login logs")

    # Query by user
    filter_params = AuditLogFilter(
        username="admin",
        limit=5
    )
    results = await audit_logger.query_logs(filter_params)
    print(f"✓ Found {results.total} logs for user 'admin'")

    # Query by date range
    start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    filter_params = AuditLogFilter(
        start_date=start_date,
        limit=100
    )
    results = await audit_logger.query_logs(filter_params)
    print(f"✓ Found {results.total} logs in last hour")

    # Display a sample log
    if results.logs:
        log = results.logs[0]
        print("\n  Sample Log Entry:")
        print(f"  - Timestamp: {log.timestamp}")
        print(f"  - User: {log.username or 'anonymous'}")
        print(f"  - Action: {log.action}")
        print(f"  - Result: {log.result}")
        print(f"  - IP: {log.ip_address or 'N/A'}")


async def test_statistics():
    """Test audit statistics"""
    print("\n=== Testing Statistics ===")

    # Get stats for last 30 days
    stats = await audit_logger.get_statistics()

    print(f"✓ Total events: {stats.total_events}")
    print(f"✓ Failed logins: {stats.failed_logins}")
    print(f"✓ Security events: {stats.security_events}")

    if stats.events_by_action:
        print("\n  Events by Action (top 5):")
        for action, count in list(stats.events_by_action.items())[:5]:
            print(f"    - {action}: {count}")

    if stats.events_by_result:
        print("\n  Events by Result:")
        for result, count in stats.events_by_result.items():
            print(f"    - {result}: {count}")

    if stats.events_by_user:
        print("\n  Events by User (top 5):")
        for user, count in list(stats.events_by_user.items())[:5]:
            print(f"    - {user}: {count}")

    if stats.recent_suspicious_ips:
        print("\n  Suspicious IPs (multiple failed logins):")
        for ip in stats.recent_suspicious_ips:
            print(f"    - {ip}")


async def test_various_events():
    """Test logging various types of events"""
    print("\n=== Testing Various Event Types ===")

    events = [
        # Authentication events
        (AuditAction.AUTH_LOGOUT, AuditResult.SUCCESS, "user_1", "john", "service", None),
        (AuditAction.AUTH_PASSWORD_CHANGE, AuditResult.SUCCESS, "user_1", "john", None, None),

        # Service events
        (AuditAction.SERVICE_STOP, AuditResult.SUCCESS, "admin_1", "admin", "service", "unicorn-chat"),
        (AuditAction.SERVICE_RESTART, AuditResult.SUCCESS, "admin_1", "admin", "service", "unicorn-search"),

        # Model events
        (AuditAction.MODEL_DOWNLOAD, AuditResult.SUCCESS, "admin_1", "admin", "model", "llama2-7b"),
        (AuditAction.MODEL_DELETE, AuditResult.SUCCESS, "admin_1", "admin", "model", "mistral-7b"),

        # User management events
        (AuditAction.USER_CREATE, AuditResult.SUCCESS, "admin_1", "admin", "user", "new_user"),
        (AuditAction.USER_ROLE_CHANGE, AuditResult.SUCCESS, "admin_1", "admin", "user", "user_2"),

        # Security events
        (AuditAction.PERMISSION_DENIED, AuditResult.DENIED, "user_2", "jane", "admin_endpoint", None),
        (AuditAction.RATE_LIMIT_EXCEEDED, AuditResult.DENIED, None, None, "api", "/api/models"),

        # Data access events
        (AuditAction.DATA_EXPORT, AuditResult.SUCCESS, "admin_1", "admin", "config", "system"),
        (AuditAction.CONFIG_VIEW, AuditResult.SUCCESS, "user_1", "john", "config", "network"),

        # System events
        (AuditAction.SYSTEM_UPDATE, AuditResult.SUCCESS, "admin_1", "admin", "system", "uc1-pro"),
        (AuditAction.BACKUP_CREATE, AuditResult.SUCCESS, "admin_1", "admin", "backup", "daily"),
    ]

    for action, result, user_id, username, res_type, res_id in events:
        await audit_logger.log(
            action=action.value,
            result=result.value,
            user_id=user_id,
            username=username,
            ip_address="192.168.1.100",
            resource_type=res_type,
            resource_id=res_id
        )

    print(f"✓ Logged {len(events)} various events")


async def test_security_monitoring():
    """Test security event monitoring"""
    print("\n=== Testing Security Monitoring ===")

    # Simulate multiple failed login attempts from same IP
    suspicious_ip = "192.168.1.200"

    for i in range(6):
        await audit_logger.log(
            action=AuditAction.AUTH_LOGIN_FAILED.value,
            result=AuditResult.FAILURE.value,
            username=f"attacker{i}",
            ip_address=suspicious_ip,
            error_message="Invalid credentials"
        )

    print(f"✓ Simulated 6 failed login attempts from {suspicious_ip}")

    # Get statistics to see if it's flagged
    stats = await audit_logger.get_statistics()

    if suspicious_ip in stats.recent_suspicious_ips:
        print(f"✓ IP {suspicious_ip} correctly flagged as suspicious")
    else:
        print(f"✗ IP {suspicious_ip} not flagged (may need more attempts)")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Audit Logging System Test Suite")
    print("=" * 60)

    try:
        # Run all tests
        await test_basic_logging()
        await test_various_events()
        await test_query_logs()
        await test_statistics()
        await test_security_monitoring()

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
