#!/usr/bin/env python3
"""
Test script for Keycloak Tier Enforcement

Tests:
1. Keycloak connection and authentication
2. User tier retrieval
3. Usage counter increment
4. Tier enforcement middleware
5. Usage API endpoints

Usage:
    python3 test_tier_enforcement.py [test_user_email]
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules to test
from keycloak_integration import (
    get_admin_token,
    get_user_by_email,
    get_user_tier_info,
    increment_usage,
    reset_usage,
    set_subscription_tier
)


class TierEnforcementTester:
    """Test suite for tier enforcement with Keycloak"""

    def __init__(self, test_email: str = None):
        self.test_email = test_email or os.getenv("TEST_USER_EMAIL", "admin@example.com")
        self.tests_passed = 0
        self.tests_failed = 0

    def report(self, test_name: str, passed: bool, message: str = ""):
        """Report test result"""
        if passed:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            self.tests_failed += 1
            status = "❌ FAIL"

        logger.info(f"{status} | {test_name} | {message}")

    async def test_keycloak_connection(self):
        """Test 1: Can we connect to Keycloak and get admin token?"""
        try:
            token = await get_admin_token()
            self.report(
                "Keycloak Connection",
                bool(token),
                f"Token obtained: {token[:20]}..." if token else "Failed to get token"
            )
            return bool(token)
        except Exception as e:
            self.report("Keycloak Connection", False, f"Exception: {e}")
            return False

    async def test_user_retrieval(self):
        """Test 2: Can we retrieve user by email?"""
        try:
            user = await get_user_by_email(self.test_email)
            self.report(
                "User Retrieval",
                bool(user),
                f"User found: {user.get('username') if user else 'None'}"
            )
            return user
        except Exception as e:
            self.report("User Retrieval", False, f"Exception: {e}")
            return None

    async def test_tier_info_retrieval(self):
        """Test 3: Can we get user tier information?"""
        try:
            tier_info = await get_user_tier_info(self.test_email)

            if tier_info:
                tier = tier_info.get("subscription_tier", "unknown")
                status = tier_info.get("subscription_status", "unknown")
                usage = tier_info.get("api_calls_used", 0)

                self.report(
                    "Tier Info Retrieval",
                    True,
                    f"Tier: {tier}, Status: {status}, Usage: {usage}"
                )
                return tier_info
            else:
                self.report("Tier Info Retrieval", False, "No tier info returned")
                return None

        except Exception as e:
            self.report("Tier Info Retrieval", False, f"Exception: {e}")
            return None

    async def test_usage_reset(self):
        """Test 4: Can we reset usage counter?"""
        try:
            # Get current usage before reset
            tier_info_before = await get_user_tier_info(self.test_email)
            usage_before = tier_info_before.get("api_calls_used", 0) if tier_info_before else 0

            # Reset usage
            success = await reset_usage(self.test_email)

            if success:
                # Verify reset
                tier_info_after = await get_user_tier_info(self.test_email)
                usage_after = tier_info_after.get("api_calls_used", 0) if tier_info_after else -1

                self.report(
                    "Usage Reset",
                    usage_after == 0,
                    f"Before: {usage_before}, After: {usage_after}"
                )
                return usage_after == 0
            else:
                self.report("Usage Reset", False, "Reset failed")
                return False

        except Exception as e:
            self.report("Usage Reset", False, f"Exception: {e}")
            return False

    async def test_usage_increment(self):
        """Test 5: Can we increment usage counter?"""
        try:
            # Get current usage
            tier_info_before = await get_user_tier_info(self.test_email)
            usage_before = tier_info_before.get("api_calls_used", 0) if tier_info_before else 0

            # Increment usage
            success = await increment_usage(self.test_email, usage_before)

            if success:
                # Verify increment
                await asyncio.sleep(1)  # Give Keycloak time to update
                tier_info_after = await get_user_tier_info(self.test_email)
                usage_after = tier_info_after.get("api_calls_used", 0) if tier_info_after else 0

                self.report(
                    "Usage Increment",
                    usage_after == usage_before + 1,
                    f"Before: {usage_before}, After: {usage_after}"
                )
                return usage_after == usage_before + 1
            else:
                self.report("Usage Increment", False, "Increment failed")
                return False

        except Exception as e:
            self.report("Usage Increment", False, f"Exception: {e}")
            return False

    async def test_tier_change(self):
        """Test 6: Can we change user's subscription tier?"""
        try:
            # Get current tier
            tier_info_before = await get_user_tier_info(self.test_email)
            tier_before = tier_info_before.get("subscription_tier", "unknown") if tier_info_before else "unknown"

            # Change to professional (for testing)
            test_tier = "professional"
            success = await set_subscription_tier(self.test_email, test_tier, "active")

            if success:
                # Verify change
                await asyncio.sleep(1)
                tier_info_after = await get_user_tier_info(self.test_email)
                tier_after = tier_info_after.get("subscription_tier", "unknown") if tier_info_after else "unknown"

                self.report(
                    "Tier Change",
                    tier_after == test_tier,
                    f"Before: {tier_before}, After: {tier_after}"
                )

                # Restore original tier
                if tier_before != test_tier:
                    await set_subscription_tier(self.test_email, tier_before, "active")

                return tier_after == test_tier
            else:
                self.report("Tier Change", False, "Tier change failed")
                return False

        except Exception as e:
            self.report("Tier Change", False, f"Exception: {e}")
            return False

    async def test_tier_limits(self):
        """Test 7: Verify tier limits are correctly defined"""
        from tier_enforcement_middleware import TierEnforcementMiddleware

        expected_limits = {
            "trial": 100,
            "starter": 33,
            "professional": 333,
            "enterprise": -1
        }

        actual_limits = TierEnforcementMiddleware.TIER_LIMITS

        matches = all(
            actual_limits.get(tier) == limit
            for tier, limit in expected_limits.items()
        )

        self.report(
            "Tier Limits Configuration",
            matches,
            f"Limits: {actual_limits}"
        )

        return matches

    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("=" * 70)
        logger.info(f"Starting Tier Enforcement Tests for user: {self.test_email}")
        logger.info("=" * 70)

        # Run tests in sequence
        await self.test_keycloak_connection()
        await self.test_user_retrieval()
        await self.test_tier_info_retrieval()
        await self.test_usage_reset()
        await self.test_usage_increment()
        await self.test_tier_change()
        await self.test_tier_limits()

        # Summary
        logger.info("=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Tests: {self.tests_passed + self.tests_failed}")
        logger.info(f"Passed: {self.tests_passed}")
        logger.info(f"Failed: {self.tests_failed}")
        logger.info("=" * 70)

        return self.tests_failed == 0


async def test_middleware_headers():
    """Test 8: Simulate middleware behavior"""
    import httpx

    logger.info("\n" + "=" * 70)
    logger.info("Testing Middleware Headers (Manual Test)")
    logger.info("=" * 70)
    logger.info("After deployment, test with:")
    logger.info("  curl -H 'Cookie: session_token=YOUR_SESSION' \\")
    logger.info("       https://your-domain.com/api/v1/services \\")
    logger.info("       -v 2>&1 | grep -E 'X-Tier|X-API-Calls'")
    logger.info("")
    logger.info("Expected headers:")
    logger.info("  X-Tier: <tier_name>")
    logger.info("  X-Tier-Status: <status>")
    logger.info("  X-API-Calls-Used: <count>")
    logger.info("  X-API-Calls-Limit: <limit>")
    logger.info("  X-API-Calls-Remaining: <remaining>")
    logger.info("=" * 70)


async def main():
    """Main test runner"""
    # Get test user email from command line or environment
    test_email = sys.argv[1] if len(sys.argv) > 1 else None

    # Run test suite
    tester = TierEnforcementTester(test_email)
    success = await tester.run_all_tests()

    # Show manual test instructions
    await test_middleware_headers()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
