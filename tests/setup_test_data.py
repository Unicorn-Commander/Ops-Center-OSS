#!/usr/bin/env python3
"""
Test Data Setup Script
Creates test users in Keycloak for each subscription tier
Generates test API keys for BYOK testing
Can reset test environment

Usage:
    # Setup test users
    python3 setup_test_data.py --setup

    # Cleanup test users
    python3 setup_test_data.py --cleanup

    # Reset environment (cleanup + setup)
    python3 setup_test_data.py --reset

    # List test users
    python3 setup_test_data.py --list
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from keycloak_integration import (
    create_user,
    delete_user,
    get_user_by_email,
    update_user_attributes,
    get_all_users,
    set_subscription_tier
)

# Test users configuration
TEST_USERS = {
    "trial": {
        "email": "test-trial@example.com",
        "username": "test_trial",
        "password": "TestPassword123!",
        "first_name": "Trial",
        "last_name": "User",
        "tier": "trial",
        "attributes": {
            "subscription_tier": ["trial"],
            "subscription_status": ["active"],
            "api_calls_used": ["0"],
            "api_calls_limit": ["100"],
            "test_user": ["true"],
            "created_by": ["test_script"],
            "created_at": [datetime.utcnow().isoformat()]
        }
    },
    "starter": {
        "email": "test-starter@example.com",
        "username": "test_starter",
        "password": "TestPassword123!",
        "first_name": "Starter",
        "last_name": "User",
        "tier": "starter",
        "attributes": {
            "subscription_tier": ["starter"],
            "subscription_status": ["active"],
            "api_calls_used": ["0"],
            "api_calls_limit": ["10000"],
            "stripe_customer_id": ["cus_test_starter"],
            "test_user": ["true"],
            "created_by": ["test_script"],
            "created_at": [datetime.utcnow().isoformat()]
        }
    },
    "professional": {
        "email": "test-professional@example.com",
        "username": "test_professional",
        "password": "TestPassword123!",
        "first_name": "Professional",
        "last_name": "User",
        "tier": "professional",
        "attributes": {
            "subscription_tier": ["professional"],
            "subscription_status": ["active"],
            "api_calls_used": ["0"],
            "api_calls_limit": ["100000"],
            "stripe_customer_id": ["cus_test_professional"],
            "test_user": ["true"],
            "created_by": ["test_script"],
            "created_at": [datetime.utcnow().isoformat()]
        }
    },
    "enterprise": {
        "email": "test-enterprise@example.com",
        "username": "test_enterprise",
        "password": "TestPassword123!",
        "first_name": "Enterprise",
        "last_name": "User",
        "tier": "enterprise",
        "attributes": {
            "subscription_tier": ["enterprise"],
            "subscription_status": ["active"],
            "api_calls_used": ["0"],
            "api_calls_limit": ["1000000"],
            "stripe_customer_id": ["cus_test_enterprise"],
            "test_user": ["true"],
            "created_by": ["test_script"],
            "created_at": [datetime.utcnow().isoformat()]
        }
    },
    "cancelled": {
        "email": "test-cancelled@example.com",
        "username": "test_cancelled",
        "password": "TestPassword123!",
        "first_name": "Cancelled",
        "last_name": "User",
        "tier": "trial",
        "attributes": {
            "subscription_tier": ["trial"],
            "subscription_status": ["cancelled"],
            "api_calls_used": ["500"],
            "api_calls_limit": ["100"],
            "stripe_customer_id": ["cus_test_cancelled"],
            "test_user": ["true"],
            "created_by": ["test_script"],
            "created_at": [datetime.utcnow().isoformat()]
        }
    }
}

# ANSI colors
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


async def setup_test_users():
    """Create all test users in Keycloak"""
    print_section("SETTING UP TEST USERS")

    created = []
    failed = []

    for tier, user_data in TEST_USERS.items():
        print_info(f"Creating {tier} user: {user_data['email']}")

        try:
            # Check if user already exists
            existing = await get_user_by_email(user_data['email'])
            if existing:
                print_warning(f"User already exists: {user_data['email']}")
                print_info("Updating user attributes...")

                # Update attributes
                success = await update_user_attributes(
                    user_data['email'],
                    user_data['attributes']
                )

                if success:
                    print_success(f"Updated: {user_data['email']}")
                    created.append(user_data['email'])
                else:
                    print_error(f"Failed to update: {user_data['email']}")
                    failed.append(user_data['email'])
                continue

            # Create new user
            user_id = await create_user(
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                attributes=user_data['attributes']
            )

            if user_id:
                print_success(f"Created: {user_data['email']} (ID: {user_id})")
                created.append(user_data['email'])
            else:
                print_error(f"Failed to create: {user_data['email']}")
                failed.append(user_data['email'])

        except Exception as e:
            print_error(f"Error creating {user_data['email']}: {e}")
            failed.append(user_data['email'])

    # Summary
    print_section("SETUP SUMMARY")
    print_info(f"Created/Updated: {len(created)} users")
    if failed:
        print_warning(f"Failed: {len(failed)} users")
        for email in failed:
            print_error(f"  - {email}")

    return len(failed) == 0


async def cleanup_test_users():
    """Delete all test users from Keycloak"""
    print_section("CLEANING UP TEST USERS")

    deleted = []
    failed = []

    for tier, user_data in TEST_USERS.items():
        email = user_data['email']
        print_info(f"Deleting user: {email}")

        try:
            # Check if user exists
            user = await get_user_by_email(email)
            if not user:
                print_warning(f"User not found: {email}")
                continue

            # Delete user
            success = await delete_user(email)

            if success:
                print_success(f"Deleted: {email}")
                deleted.append(email)
            else:
                print_error(f"Failed to delete: {email}")
                failed.append(email)

        except Exception as e:
            print_error(f"Error deleting {email}: {e}")
            failed.append(email)

    # Summary
    print_section("CLEANUP SUMMARY")
    print_info(f"Deleted: {len(deleted)} users")
    if failed:
        print_warning(f"Failed: {len(failed)} users")
        for email in failed:
            print_error(f"  - {email}")

    return len(failed) == 0


async def list_test_users():
    """List all test users"""
    print_section("TEST USERS")

    found = []
    not_found = []

    for tier, user_data in TEST_USERS.items():
        email = user_data['email']

        try:
            user = await get_user_by_email(email)

            if user:
                attrs = user.get('attributes', {})
                tier_value = attrs.get('subscription_tier', ['unknown'])[0]
                status = attrs.get('subscription_status', ['unknown'])[0]

                print_success(f"{tier.upper()}: {email}")
                print_info(f"  User ID: {user.get('id')}")
                print_info(f"  Tier: {tier_value}")
                print_info(f"  Status: {status}")
                print_info(f"  Enabled: {user.get('enabled')}")
                found.append(email)
            else:
                print_error(f"{tier.upper()}: {email} - NOT FOUND")
                not_found.append(email)

        except Exception as e:
            print_error(f"Error checking {email}: {e}")
            not_found.append(email)

    # Summary
    print_section("SUMMARY")
    print_info(f"Found: {len(found)} users")
    print_info(f"Not Found: {len(not_found)} users")

    return found


async def generate_test_credentials():
    """Generate test credentials file"""
    print_section("GENERATING TEST CREDENTIALS")

    credentials = {
        "base_url": "http://localhost:8084",
        "keycloak_url": os.getenv("KEYCLOAK_URL", "https://auth.unicorncommander.ai"),
        "test_users": {}
    }

    for tier, user_data in TEST_USERS.items():
        credentials["test_users"][tier] = {
            "email": user_data['email'],
            "username": user_data['username'],
            "password": user_data['password'],
            "tier": user_data['tier']
        }

    # Write to file
    output_file = os.path.join(os.path.dirname(__file__), "test_credentials.json")

    with open(output_file, 'w') as f:
        json.dump(credentials, f, indent=2)

    print_success(f"Credentials written to: {output_file}")
    print_warning("IMPORTANT: This file contains passwords - do not commit to git!")

    return output_file


async def verify_setup():
    """Verify test environment is set up correctly"""
    print_section("VERIFYING TEST SETUP")

    checks = {
        "keycloak_connection": False,
        "all_users_exist": False,
        "correct_tiers": False,
        "byok_ready": False
    }

    # Check Keycloak connection
    try:
        from keycloak_integration import get_admin_token
        token = await get_admin_token()
        if token:
            print_success("Keycloak connection working")
            checks["keycloak_connection"] = True
        else:
            print_error("Failed to get admin token")
    except Exception as e:
        print_error(f"Keycloak connection failed: {e}")

    # Check all users exist
    found_users = await list_test_users()
    if len(found_users) == len(TEST_USERS):
        print_success(f"All {len(TEST_USERS)} test users exist")
        checks["all_users_exist"] = True
    else:
        print_warning(f"Only {len(found_users)}/{len(TEST_USERS)} users found")

    # Check tiers are correct
    tier_errors = []
    for tier, user_data in TEST_USERS.items():
        try:
            user = await get_user_by_email(user_data['email'])
            if user:
                attrs = user.get('attributes', {})
                actual_tier = attrs.get('subscription_tier', ['unknown'])[0]
                expected_tier = user_data['tier']

                if actual_tier != expected_tier:
                    tier_errors.append(f"{user_data['email']}: {actual_tier} != {expected_tier}")
        except:
            pass

    if len(tier_errors) == 0:
        print_success("All user tiers are correct")
        checks["correct_tiers"] = True
    else:
        print_error("Tier mismatches found:")
        for error in tier_errors:
            print_warning(f"  - {error}")

    # Check BYOK configuration
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key:
        print_success("BYOK encryption key configured")
        checks["byok_ready"] = True
    else:
        print_warning("BYOK encryption key not configured")
        print_info("Set ENCRYPTION_KEY environment variable")

    # Summary
    print_section("VERIFICATION SUMMARY")
    passed = sum(checks.values())
    total = len(checks)

    print_info(f"Checks passed: {passed}/{total}")

    for check, status in checks.items():
        if status:
            print_success(check)
        else:
            print_error(check)

    return passed == total


async def main():
    parser = argparse.ArgumentParser(
        description="Test Data Setup Script for UC-1 Pro Billing System"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create test users"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete test users"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Cleanup and setup (full reset)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List test users"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify test setup"
    )
    parser.add_argument(
        "--credentials",
        action="store_true",
        help="Generate test credentials file"
    )

    args = parser.parse_args()

    # Default to listing if no args
    if not any([args.setup, args.cleanup, args.reset, args.list, args.verify, args.credentials]):
        args.list = True

    print_section("UC-1 PRO BILLING SYSTEM - TEST DATA SETUP")
    print_info(f"Keycloak URL: {os.getenv('KEYCLOAK_URL', 'Not set')}")
    print_info(f"Realm: {os.getenv('KEYCLOAK_REALM', 'Not set')}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")

    try:
        if args.reset:
            print_info("Performing full reset...")
            await cleanup_test_users()
            await asyncio.sleep(1)  # Brief pause
            await setup_test_users()
            await generate_test_credentials()
            await verify_setup()

        elif args.setup:
            await setup_test_users()
            await generate_test_credentials()

        elif args.cleanup:
            await cleanup_test_users()

        elif args.list:
            await list_test_users()

        elif args.verify:
            await verify_setup()

        elif args.credentials:
            await generate_test_credentials()

        print_section("COMPLETE")
        print_success("Operation completed successfully")

    except Exception as e:
        print_section("ERROR")
        print_error(f"Operation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
