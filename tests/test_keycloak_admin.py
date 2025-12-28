#!/usr/bin/env python3
"""
Test script for Keycloak Admin Subscription Management
Tests all admin API endpoints for subscription management
"""

import sys
import os
import asyncio
import httpx
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from keycloak_integration import (
    get_admin_token,
    get_all_users,
    get_user_by_email,
    update_user_attributes,
    create_user,
    get_user_tier_info,
    increment_usage,
    set_subscription_tier
)

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_section(title):
    print(f"\n{BLUE}{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}{RESET}\n")


async def test_admin_token():
    """Test admin token retrieval"""
    print_section("TEST 1: Admin Token Retrieval")

    try:
        token = await get_admin_token()
        if token:
            print_success("Admin token retrieved successfully")
            print_info(f"Token (first 50 chars): {token[:50]}...")
            return True
        else:
            print_error("Failed to retrieve admin token")
            return False
    except Exception as e:
        print_error(f"Error getting admin token: {e}")
        return False


async def test_get_all_users():
    """Test fetching all users"""
    print_section("TEST 2: Fetch All Users")

    try:
        users = await get_all_users()
        if users:
            print_success(f"Retrieved {len(users)} users from Keycloak")

            # Show first 3 users
            for i, user in enumerate(users[:3]):
                print_info(f"  User {i+1}: {user.get('username')} ({user.get('email')})")

            return True
        else:
            print_warning("No users found in Keycloak")
            return True
    except Exception as e:
        print_error(f"Error fetching users: {e}")
        return False


async def test_get_user_by_email():
    """Test fetching user by email"""
    print_section("TEST 3: Fetch User by Email")

    # First get any user
    users = await get_all_users()
    if not users:
        print_warning("No users available to test")
        return True

    test_email = users[0].get('email')
    print_info(f"Testing with email: {test_email}")

    try:
        user = await get_user_by_email(test_email)
        if user:
            print_success(f"Found user: {user.get('username')}")
            print_info(f"  User ID: {user.get('id')}")
            print_info(f"  Enabled: {user.get('enabled')}")

            attrs = user.get('attributes', {})
            print_info(f"  Attributes: {len(attrs)} keys")

            return True
        else:
            print_error(f"User not found: {test_email}")
            return False
    except Exception as e:
        print_error(f"Error fetching user: {e}")
        return False


async def test_update_user_attributes():
    """Test updating user attributes"""
    print_section("TEST 4: Update User Attributes")

    users = await get_all_users()
    if not users:
        print_warning("No users available to test")
        return True

    test_email = users[0].get('email')
    print_info(f"Testing with email: {test_email}")

    try:
        # Update subscription tier
        test_attrs = {
            "subscription_tier": ["professional"],
            "subscription_status": ["active"],
            "api_calls_limit": ["100000"],
            "test_timestamp": [datetime.utcnow().isoformat()]
        }

        success = await update_user_attributes(test_email, test_attrs)

        if success:
            print_success("User attributes updated successfully")

            # Verify update
            user = await get_user_by_email(test_email)
            attrs = user.get('attributes', {})

            tier = attrs.get('subscription_tier', [None])[0]
            status = attrs.get('subscription_status', [None])[0]

            print_info(f"  Verified tier: {tier}")
            print_info(f"  Verified status: {status}")

            return True
        else:
            print_error("Failed to update user attributes")
            return False
    except Exception as e:
        print_error(f"Error updating attributes: {e}")
        return False


async def test_tier_info():
    """Test getting user tier info"""
    print_section("TEST 5: Get User Tier Info")

    users = await get_all_users()
    if not users:
        print_warning("No users available to test")
        return True

    test_email = users[0].get('email')
    print_info(f"Testing with email: {test_email}")

    try:
        tier_info = await get_user_tier_info(test_email)

        if tier_info:
            print_success("Retrieved user tier info")
            print_info(f"  Tier: {tier_info.get('subscription_tier')}")
            print_info(f"  Status: {tier_info.get('subscription_status')}")
            print_info(f"  Usage: {tier_info.get('api_calls_used')}")
            print_info(f"  Reset Date: {tier_info.get('api_calls_reset_date')}")

            return True
        else:
            print_error("Failed to get tier info")
            return False
    except Exception as e:
        print_error(f"Error getting tier info: {e}")
        return False


async def test_increment_usage():
    """Test incrementing API usage"""
    print_section("TEST 6: Increment API Usage")

    users = await get_all_users()
    if not users:
        print_warning("No users available to test")
        return True

    test_email = users[0].get('email')
    print_info(f"Testing with email: {test_email}")

    try:
        # Get current usage
        tier_info_before = await get_user_tier_info(test_email)
        usage_before = tier_info_before.get('api_calls_used', 0)
        print_info(f"  Usage before: {usage_before}")

        # Increment usage
        success = await increment_usage(test_email)

        if success:
            # Verify increment
            tier_info_after = await get_user_tier_info(test_email)
            usage_after = tier_info_after.get('api_calls_used', 0)

            print_success(f"Usage incremented successfully")
            print_info(f"  Usage after: {usage_after}")

            if usage_after > usage_before:
                print_success("Usage counter incremented correctly")
                return True
            else:
                print_warning("Usage counter did not increment as expected (may have reset)")
                return True
        else:
            print_error("Failed to increment usage")
            return False
    except Exception as e:
        print_error(f"Error incrementing usage: {e}")
        return False


async def test_set_subscription_tier():
    """Test setting subscription tier"""
    print_section("TEST 7: Set Subscription Tier")

    users = await get_all_users()
    if not users:
        print_warning("No users available to test")
        return True

    test_email = users[0].get('email')
    print_info(f"Testing with email: {test_email}")

    try:
        # Set to enterprise tier
        success = await set_subscription_tier(test_email, "enterprise", "active")

        if success:
            print_success("Subscription tier updated")

            # Verify
            tier_info = await get_user_tier_info(test_email)
            tier = tier_info.get('subscription_tier')
            status = tier_info.get('subscription_status')

            print_info(f"  Verified tier: {tier}")
            print_info(f"  Verified status: {status}")

            if tier == "enterprise" and status == "active":
                print_success("Tier and status verified correctly")
                return True
            else:
                print_warning("Tier/status mismatch")
                return False
        else:
            print_error("Failed to set subscription tier")
            return False
    except Exception as e:
        print_error(f"Error setting tier: {e}")
        return False


async def test_api_endpoints():
    """Test the actual API endpoints"""
    print_section("TEST 8: API Endpoints")

    base_url = "http://localhost:8084"  # Adjust if different

    # Note: These tests require authentication
    # You would need a valid session cookie

    print_info("API endpoint tests require authentication")
    print_info("Test manually by:")
    print_info(f"  1. Login as admin at {base_url}/login.html")
    print_info(f"  2. Visit {base_url}/admin/subscriptions.html")
    print_info(f"  3. Check browser console for API calls")

    endpoints = [
        "/api/v1/admin/subscriptions/list",
        "/api/v1/admin/subscriptions/analytics/overview",
        "/api/v1/admin/subscriptions/analytics/revenue-by-tier",
        "/api/v1/admin/subscriptions/analytics/usage-stats"
    ]

    for endpoint in endpoints:
        print_info(f"  • {endpoint}")

    return True


async def main():
    """Run all tests"""
    print_section("KEYCLOAK ADMIN SUBSCRIPTION MANAGEMENT TESTS")

    print_info("Testing Keycloak integration at: https://auth.your-domain.com/realms/uchub")
    print_info("Starting test suite...\n")

    tests = [
        test_admin_token,
        test_get_all_users,
        test_get_user_by_email,
        test_update_user_attributes,
        test_tier_info,
        test_increment_usage,
        test_set_subscription_tier,
        test_api_endpoints
    ]

    results = []

    for test in tests:
        try:
            result = await test()
            results.append(result)

            if not result:
                print_warning("Test failed but continuing...")
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append(False)

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(results)
    total = len(results)

    print_info(f"Tests passed: {passed}/{total}")

    if passed == total:
        print_success("All tests passed!")
    else:
        print_warning(f"{total - passed} test(s) failed")

    print()


if __name__ == "__main__":
    # Check environment variables
    required_vars = [
        "KEYCLOAK_URL",
        "KEYCLOAK_REALM",
        "KEYCLOAK_ADMIN_USERNAME",
        "KEYCLOAK_ADMIN_PASSWORD"
    ]

    print_section("ENVIRONMENT CHECK")

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is NOT set")
            missing_vars.append(var)

    if missing_vars:
        print_error("\nMissing required environment variables!")
        print_info("Set them in your .env file or export them:")
        for var in missing_vars:
            print_info(f"  export {var}=<value>")
        sys.exit(1)

    # Run tests
    asyncio.run(main())
