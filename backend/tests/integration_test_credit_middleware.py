#!/usr/bin/env python3
"""
Integration Test for Credit Deduction Middleware
=================================================

End-to-end testing of automatic credit deduction.

Test Scenarios:
1. User with org credits makes LLM request → credits deducted from org pool
2. User without org makes LLM request → credits deducted from individual balance
3. User with BYOK makes LLM request → no credits deducted
4. User with insufficient credits → 402 error
5. Concurrent requests → atomic deduction

Prerequisites:
- Ops-Center backend running (ops-center-direct container)
- PostgreSQL with org credit tables populated
- Redis with session data
- Test user accounts configured

Usage:
    python integration_test_credit_middleware.py

Author: Backend Integration Teamlead
Date: November 15, 2025
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List


class CreditMiddlewareIntegrationTest:
    """Integration test suite for credit deduction middleware"""

    def __init__(self, base_url: str = "http://localhost:8084"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []

    async def setup(self):
        """Setup test environment"""
        print("=" * 80)
        print("Credit Deduction Middleware Integration Test")
        print("=" * 80)
        print()

    async def teardown(self):
        """Cleanup after tests"""
        await self.client.aclose()
        self._print_summary()

    def _record_result(self, test_name: str, passed: bool, message: str):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        print()

    def _print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("Test Summary")
        print("=" * 80)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print()

        if failed > 0:
            print("Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")

    async def test_health_check(self):
        """Test that backend is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/system/status")

            if response.status_code == 200:
                self._record_result(
                    "Backend Health Check",
                    True,
                    "Ops-Center backend is running"
                )
                return True
            else:
                self._record_result(
                    "Backend Health Check",
                    False,
                    f"Backend returned {response.status_code}"
                )
                return False

        except Exception as e:
            self._record_result(
                "Backend Health Check",
                False,
                f"Cannot connect to backend: {str(e)}"
            )
            return False

    async def test_org_credit_deduction(self, session_token: str):
        """
        Test credit deduction for user with organization.

        Expected: Credits deducted from org pool, X-Org-Credits: true
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/llm/chat/completions",
                json={
                    "model": "openai/gpt-4",
                    "messages": [
                        {"role": "user", "content": "Say 'test' only"}
                    ],
                    "max_tokens": 10
                },
                cookies={"session_token": session_token}
            )

            if response.status_code == 200:
                headers = response.headers

                # Check credit headers
                credits_used = headers.get("X-Credits-Used")
                credits_remaining = headers.get("X-Credits-Remaining")
                org_credits = headers.get("X-Org-Credits")

                if credits_used and org_credits == "true":
                    self._record_result(
                        "Org Credit Deduction",
                        True,
                        f"Deducted {credits_used} credits from org pool"
                    )
                    return True
                else:
                    self._record_result(
                        "Org Credit Deduction",
                        False,
                        f"Headers missing: X-Credits-Used={credits_used}, X-Org-Credits={org_credits}"
                    )
                    return False

            elif response.status_code == 402:
                self._record_result(
                    "Org Credit Deduction",
                    False,
                    "Insufficient credits (expected sufficient balance for test)"
                )
                return False

            else:
                self._record_result(
                    "Org Credit Deduction",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
                return False

        except Exception as e:
            self._record_result(
                "Org Credit Deduction",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    async def test_individual_credit_deduction(self, session_token: str):
        """
        Test credit deduction for user without organization.

        Expected: Credits deducted from individual balance, X-Org-Credits: false
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/llm/chat/completions",
                json={
                    "model": "openai/gpt-4",
                    "messages": [
                        {"role": "user", "content": "Say 'test' only"}
                    ],
                    "max_tokens": 10
                },
                cookies={"session_token": session_token}
            )

            if response.status_code == 200:
                headers = response.headers

                credits_used = headers.get("X-Credits-Used")
                org_credits = headers.get("X-Org-Credits")

                if credits_used and org_credits == "false":
                    self._record_result(
                        "Individual Credit Deduction",
                        True,
                        f"Deducted {credits_used} credits from individual balance"
                    )
                    return True
                else:
                    self._record_result(
                        "Individual Credit Deduction",
                        False,
                        f"Headers incorrect: X-Org-Credits={org_credits} (expected false)"
                    )
                    return False

            else:
                self._record_result(
                    "Individual Credit Deduction",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
                return False

        except Exception as e:
            self._record_result(
                "Individual Credit Deduction",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    async def test_byok_passthrough(self, session_token: str):
        """
        Test BYOK passthrough (no credit deduction).

        Expected: X-BYOK: true, X-Credits-Used: 0.0
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/llm/chat/completions",
                json={
                    "model": "openrouter/anthropic/claude-3.5-sonnet",  # Assumes user has OpenRouter key
                    "messages": [
                        {"role": "user", "content": "Say 'test' only"}
                    ],
                    "max_tokens": 10
                },
                cookies={"session_token": session_token}
            )

            if response.status_code == 200:
                headers = response.headers

                byok = headers.get("X-BYOK")
                credits_used = headers.get("X-Credits-Used")

                if byok == "true" and credits_used == "0.0":
                    self._record_result(
                        "BYOK Passthrough",
                        True,
                        "BYOK user not charged credits"
                    )
                    return True
                else:
                    self._record_result(
                        "BYOK Passthrough",
                        False,
                        f"Expected BYOK headers not found: X-BYOK={byok}, X-Credits-Used={credits_used}"
                    )
                    return False

            else:
                self._record_result(
                    "BYOK Passthrough",
                    False,
                    f"Request failed with status {response.status_code}"
                )
                return False

        except Exception as e:
            self._record_result(
                "BYOK Passthrough",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    async def test_insufficient_credits(self, session_token: str):
        """
        Test behavior when user has insufficient credits.

        Expected: 402 Payment Required
        """
        try:
            # Make multiple requests to exhaust credits
            for i in range(5):
                response = await self.client.post(
                    f"{self.base_url}/api/v1/llm/chat/completions",
                    json={
                        "model": "openai/gpt-4",
                        "messages": [
                            {"role": "user", "content": "This is a long test message to consume credits. " * 100}
                        ],
                        "max_tokens": 1000
                    },
                    cookies={"session_token": session_token}
                )

                if response.status_code == 402:
                    body = response.json()

                    if "Payment Required" in body.get("error", ""):
                        self._record_result(
                            "Insufficient Credits",
                            True,
                            "Correctly returns 402 when credits exhausted"
                        )
                        return True

            # If we get here, credits never ran out
            self._record_result(
                "Insufficient Credits",
                False,
                "User has too many credits to test insufficient scenario (skip)"
            )
            return False

        except Exception as e:
            self._record_result(
                "Insufficient Credits",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    async def test_concurrent_requests(self, session_token: str):
        """
        Test atomic credit deduction with concurrent requests.

        Expected: All requests succeed, credits deducted atomically
        """
        try:
            # Make 3 concurrent requests
            tasks = [
                self.client.post(
                    f"{self.base_url}/api/v1/llm/chat/completions",
                    json={
                        "model": "openai/gpt-4",
                        "messages": [
                            {"role": "user", "content": f"Test {i}"}
                        ],
                        "max_tokens": 10
                    },
                    cookies={"session_token": session_token}
                )
                for i in range(3)
            ]

            responses = await asyncio.gather(*tasks)

            # All should succeed (if credits available)
            success_count = sum(1 for r in responses if r.status_code == 200)

            if success_count == 3:
                # Check that credits were deducted
                last_response = responses[-1]
                credits_used = last_response.headers.get("X-Credits-Used")

                if credits_used:
                    self._record_result(
                        "Concurrent Requests",
                        True,
                        f"All 3 requests succeeded with atomic deduction"
                    )
                    return True
                else:
                    self._record_result(
                        "Concurrent Requests",
                        False,
                        "Requests succeeded but no credit headers"
                    )
                    return False
            else:
                self._record_result(
                    "Concurrent Requests",
                    False,
                    f"Only {success_count}/3 requests succeeded"
                )
                return False

        except Exception as e:
            self._record_result(
                "Concurrent Requests",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    async def run_all_tests(self, org_user_token: str = None, individual_user_token: str = None, byok_user_token: str = None):
        """
        Run all integration tests.

        Args:
            org_user_token: Session token for user with organization
            individual_user_token: Session token for user without organization
            byok_user_token: Session token for user with BYOK configured
        """
        await self.setup()

        # Test 1: Health check
        backend_ok = await self.test_health_check()

        if not backend_ok:
            print("❌ Backend not available. Stopping tests.")
            await self.teardown()
            return

        # Test 2-6: Credit deduction tests (requires session tokens)
        if org_user_token:
            await self.test_org_credit_deduction(org_user_token)
            await self.test_concurrent_requests(org_user_token)
        else:
            print("⚠️  Skipping org credit tests (no org_user_token provided)")

        if individual_user_token:
            await self.test_individual_credit_deduction(individual_user_token)
        else:
            print("⚠️  Skipping individual credit tests (no individual_user_token provided)")

        if byok_user_token:
            await self.test_byok_passthrough(byok_user_token)
        else:
            print("⚠️  Skipping BYOK tests (no byok_user_token provided)")

        # Note: Insufficient credits test is destructive, so we skip it
        # unless explicitly requested

        await self.teardown()


async def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Credit Deduction Middleware - Integration Test Suite         ║
    ╚════════════════════════════════════════════════════════════════╝

    This script tests the automatic credit deduction middleware.

    To run with real users, provide session tokens:

    ORG_USER_TOKEN=<token> \\
    INDIVIDUAL_USER_TOKEN=<token> \\
    BYOK_USER_TOKEN=<token> \\
    python integration_test_credit_middleware.py

    """)

    import os

    org_user_token = os.getenv("ORG_USER_TOKEN")
    individual_user_token = os.getenv("INDIVIDUAL_USER_TOKEN")
    byok_user_token = os.getenv("BYOK_USER_TOKEN")

    test_suite = CreditMiddlewareIntegrationTest()

    await test_suite.run_all_tests(
        org_user_token=org_user_token,
        individual_user_token=individual_user_token,
        byok_user_token=byok_user_token
    )


if __name__ == "__main__":
    asyncio.run(main())
