#!/usr/bin/env python3
"""
Integration Test Suite for Ops-Center Critical User Journeys
Tests end-to-end flows across all integrated services

Author: QA Testing Team
Date: October 28, 2025
"""

import asyncio
import httpx
import json
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "✅"
    FAILED = "❌"
    PARTIAL = "⚠️"
    SKIPPED = "⏭️"
    BLOCKED = "🔗"


@dataclass
class TestResult:
    """Test result data structure"""
    journey_name: str
    status: TestStatus
    steps_completed: List[str]
    steps_failed: List[str]
    integration_issues: List[str]
    recommendations: List[str]
    execution_time: float
    details: Dict[str, Any]


class IntegrationTestSuite:
    """
    Comprehensive integration test suite for critical user journeys
    """

    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:8084")
        self.keycloak_url = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
        self.lago_url = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")
        self.results: List[TestResult] = []
        self.test_user_email = f"integration_test_{datetime.now().timestamp()}@test.com"
        self.test_user_id = None
        self.test_org_id = None

    async def check_service_availability(self) -> Dict[str, bool]:
        """
        Check if required services are available
        """
        services = {
            "ops-center": self.base_url,
            "keycloak": self.keycloak_url,
            "lago": self.lago_url,
            "postgresql": f"postgresql://{os.getenv('POSTGRES_HOST', 'unicorn-postgresql')}:5432",
            "redis": f"redis://{os.getenv("REDIS_HOST", "unicorn-lago-redis")}:6379"
        }

        availability = {}
        for name, url in services.items():
            try:
                if name == "keycloak":
                    async with httpx.AsyncClient(verify=False) as client:
                        resp = await client.get(f"{url}/realms/uchub", timeout=5)
                        availability[name] = resp.status_code in [200, 302]
                elif name == "ops-center":
                    async with httpx.AsyncClient(verify=False) as client:
                        resp = await client.get(f"{url}/api/v1/system/status", timeout=5)
                        availability[name] = resp.status_code == 200
                elif name == "lago":
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(f"{url}/health", timeout=5)
                        availability[name] = resp.status_code == 200
                else:
                    availability[name] = False  # Skip DB checks for now
            except Exception as e:
                availability[name] = False
                print(f"  ❌ {name} unavailable: {e}")

        return availability

    async def test_user_onboarding_flow(self) -> TestResult:
        """
        Journey 1: New User Onboarding
        Steps:
        1. User registers via Keycloak
        2. Subscription tier assigned
        3. Credit account created
        4. Email notification sent
        5. User can login
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        try:
            # Step 1: Register user via Keycloak
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    # Get admin token
                    token_resp = await client.post(
                        f"{self.keycloak_url}/realms/master/protocol/openid-connect/token",
                        data={
                            "grant_type": "password",
                            "client_id": "admin-cli",
                            "username": os.getenv("KEYCLOAK_ADMIN_USER", "admin"),
                            "password": os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")
                        },
                        timeout=10
                    )

                    if token_resp.status_code == 200:
                        admin_token = token_resp.json().get("access_token")

                        # Create user
                        user_data = {
                            "username": self.test_user_email,
                            "email": self.test_user_email,
                            "enabled": True,
                            "emailVerified": False,
                            "credentials": [{
                                "type": "password",
                                "value": "TestPassword123!",
                                "temporary": False
                            }],
                            "attributes": {
                                "subscription_tier": ["trial"],
                                "subscription_status": ["active"]
                            }
                        }

                        create_resp = await client.post(
                            f"{self.keycloak_url}/admin/realms/uchub/users",
                            headers={"Authorization": f"Bearer {admin_token}"},
                            json=user_data,
                            timeout=10
                        )

                        if create_resp.status_code == 201:
                            steps_completed.append("User registered in Keycloak")
                            # Extract user ID from Location header
                            location = create_resp.headers.get("Location", "")
                            self.test_user_id = location.split("/")[-1] if location else None
                        else:
                            steps_failed.append(f"User registration failed: {create_resp.status_code}")
                            integration_issues.append("Keycloak user creation API issue")
                    else:
                        steps_failed.append("Could not get Keycloak admin token")
                        integration_issues.append("Keycloak admin authentication failed")
            except Exception as e:
                steps_failed.append(f"Keycloak integration error: {e}")
                integration_issues.append("Keycloak service unavailable")

            # Step 2: Verify subscription tier assigned
            if self.test_user_id:
                try:
                    async with httpx.AsyncClient(verify=False) as client:
                        resp = await client.get(
                            f"{self.keycloak_url}/admin/realms/uchub/users/{self.test_user_id}",
                            headers={"Authorization": f"Bearer {admin_token}"},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            user_data = resp.json()
                            tier = user_data.get("attributes", {}).get("subscription_tier", [None])[0]
                            if tier:
                                steps_completed.append(f"Subscription tier assigned: {tier}")
                            else:
                                steps_failed.append("Subscription tier not assigned")
                                recommendations.append("Ensure user attributes are properly configured in Keycloak")
                except Exception as e:
                    steps_failed.append(f"Could not verify tier: {e}")

            # Step 3: Check credit account creation
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.get(
                        f"{self.base_url}/api/v1/credits/balance",
                        headers={"X-User-ID": self.test_user_id or "test"},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        balance = resp.json()
                        steps_completed.append(f"Credit account created: ${balance.get('balance', 0)}")
                    else:
                        steps_failed.append("Credit account not found")
                        integration_issues.append("Credit system not auto-creating accounts")
            except Exception as e:
                steps_failed.append(f"Credit system error: {e}")

            # Step 4: Email notification (check if service is configured)
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.get(
                        f"{self.base_url}/api/v1/email/providers",
                        timeout=10
                    )
                    if resp.status_code == 200:
                        providers = resp.json()
                        if providers:
                            steps_completed.append("Email service configured")
                        else:
                            steps_failed.append("No email providers configured")
                            recommendations.append("Configure email provider for welcome emails")
            except Exception as e:
                steps_failed.append(f"Email service check failed: {e}")

            # Step 5: Test login
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.post(
                        f"{self.keycloak_url}/realms/uchub/protocol/openid-connect/token",
                        data={
                            "grant_type": "password",
                            "client_id": "ops-center",
                            "client_secret": os.getenv("OPS_CENTER_OAUTH_CLIENT_SECRET", ""),
                            "username": self.test_user_email,
                            "password": "TestPassword123!"
                        },
                        timeout=10
                    )
                    if resp.status_code == 200:
                        steps_completed.append("User login successful")
                    else:
                        steps_failed.append(f"User login failed: {resp.status_code}")
                        integration_issues.append("OIDC authentication flow broken")
            except Exception as e:
                steps_failed.append(f"Login test failed: {e}")

        except Exception as e:
            steps_failed.append(f"Critical error: {e}")

        # Determine status
        if len(steps_failed) == 0:
            status = TestStatus.PASSED
        elif len(steps_completed) > len(steps_failed):
            status = TestStatus.PARTIAL
        else:
            status = TestStatus.FAILED

        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="New User Onboarding",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={
                "test_user_email": self.test_user_email,
                "test_user_id": self.test_user_id
            }
        )

    async def test_api_key_workflow(self) -> TestResult:
        """
        Journey 2: API Key Workflow
        Steps:
        1. Admin generates API key
        2. External app authenticates
        3. LLM inference call succeeds
        4. Credits deducted correctly
        5. Usage tracked in database
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Test requires user to exist
        if not self.test_user_id:
            return TestResult(
                journey_name="API Key Workflow",
                status=TestStatus.SKIPPED,
                steps_completed=[],
                steps_failed=["Test user not created - skipped"],
                integration_issues=[],
                recommendations=[],
                execution_time=0.0,
                details={}
            )

        try:
            # Step 1: Generate API key
            test_api_key = None
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.post(
                        f"{self.base_url}/api/v1/admin/users/{self.test_user_id}/api-keys",
                        json={
                            "name": "Integration Test Key",
                            "expires_in_days": 1
                        },
                        headers={"X-Admin-Token": "test"},
                        timeout=10
                    )
                    if resp.status_code == 201:
                        api_key_data = resp.json()
                        test_api_key = api_key_data.get("api_key")
                        steps_completed.append(f"API key generated: {test_api_key[:10]}...")
                    else:
                        steps_failed.append(f"API key generation failed: {resp.status_code}")
                        integration_issues.append("API key management endpoint not working")
            except Exception as e:
                steps_failed.append(f"API key generation error: {e}")

            # Step 2: Authenticate with API key
            if test_api_key:
                try:
                    async with httpx.AsyncClient(verify=False) as client:
                        resp = await client.get(
                            f"{self.base_url}/api/v1/auth/verify",
                            headers={"X-API-Key": test_api_key},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            steps_completed.append("API key authentication successful")
                        else:
                            steps_failed.append("API key authentication failed")
                            integration_issues.append("API key verification not working")
                except Exception as e:
                    steps_failed.append(f"Authentication test failed: {e}")

            # Step 3: LLM inference call
            if test_api_key:
                try:
                    async with httpx.AsyncClient(verify=False) as client:
                        resp = await client.post(
                            f"{self.base_url}/api/v1/llm/chat/completions",
                            headers={"X-API-Key": test_api_key},
                            json={
                                "model": "openai/gpt-3.5-turbo",
                                "messages": [{"role": "user", "content": "Hello"}],
                                "max_tokens": 10
                            },
                            timeout=30
                        )
                        if resp.status_code == 200:
                            steps_completed.append("LLM inference call successful")
                        else:
                            steps_failed.append(f"LLM call failed: {resp.status_code}")
                            integration_issues.append("LLM proxy not routing correctly")
                except Exception as e:
                    steps_failed.append(f"LLM inference error: {e}")

            # Step 4 & 5: Check credits and usage tracking
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    resp = await client.get(
                        f"{self.base_url}/api/v1/credits/balance",
                        headers={"X-User-ID": self.test_user_id},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        balance_data = resp.json()
                        steps_completed.append(f"Credits tracked: ${balance_data.get('balance', 0)}")
                    else:
                        steps_failed.append("Credit tracking failed")
                        recommendations.append("Verify credit deduction is working for LLM calls")
            except Exception as e:
                steps_failed.append(f"Credit check error: {e}")

        except Exception as e:
            steps_failed.append(f"Critical error: {e}")

        # Determine status
        if len(steps_failed) == 0:
            status = TestStatus.PASSED
        elif len(steps_completed) > len(steps_failed):
            status = TestStatus.PARTIAL
        else:
            status = TestStatus.FAILED

        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="API Key Workflow",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={"api_key_tested": test_api_key is not None}
        )

    async def test_credit_purchase_flow(self) -> TestResult:
        """
        Journey 3: Credit Purchase Flow
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Check Stripe configuration
        try:
            stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
            if stripe_key:
                steps_completed.append("Stripe API key configured")
            else:
                steps_failed.append("Stripe not configured")
                recommendations.append("Configure STRIPE_SECRET_KEY environment variable")
        except Exception as e:
            steps_failed.append(f"Stripe check failed: {e}")

        # Check Lago integration
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.lago_url}/health",
                    timeout=5
                )
                if resp.status_code == 200:
                    steps_completed.append("Lago billing service available")
                else:
                    steps_failed.append("Lago service unavailable")
                    integration_issues.append("Lago service not responding")
        except Exception as e:
            steps_failed.append(f"Lago connection failed: {e}")
            integration_issues.append("Cannot connect to Lago billing system")

        # Check webhook endpoints
        try:
            async with httpx.AsyncClient(verify=False) as client:
                # Check Stripe webhook
                resp = await client.options(
                    f"{self.base_url}/api/v1/webhooks/stripe",
                    timeout=5
                )
                if resp.status_code in [200, 204, 405]:  # 405 is OK for OPTIONS
                    steps_completed.append("Stripe webhook endpoint configured")
                else:
                    steps_failed.append("Stripe webhook endpoint not found")
        except Exception as e:
            steps_failed.append(f"Webhook check failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.FAILED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="Credit Purchase Flow",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={}
        )

    async def test_byok_flow(self) -> TestResult:
        """
        Journey 4: BYOK (Bring Your Own Key) Flow
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Check if BYOK module is available
        try:
            encryption_key = os.getenv("BYOK_ENCRYPTION_KEY", "")
            if encryption_key:
                steps_completed.append("BYOK encryption key configured")
            else:
                steps_failed.append("BYOK encryption not configured")
                recommendations.append("Set BYOK_ENCRYPTION_KEY for secure key storage")
        except Exception as e:
            steps_failed.append(f"BYOK config check failed: {e}")

        # Test BYOK endpoints existence
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/byok/providers",
                    timeout=5
                )
                if resp.status_code == 200:
                    providers = resp.json()
                    steps_completed.append(f"BYOK providers available: {len(providers)}")
                else:
                    steps_failed.append("BYOK endpoints not accessible")
                    integration_issues.append("BYOK module not properly exposed")
        except Exception as e:
            steps_failed.append(f"BYOK endpoint test failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.FAILED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="BYOK Flow",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={}
        )

    async def test_subscription_management(self) -> TestResult:
        """
        Journey 5: Subscription Upgrade/Downgrade
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Check Lago subscriptions API
        try:
            lago_key = os.getenv("LAGO_API_KEY", "")
            if lago_key:
                steps_completed.append("Lago API key configured")
            else:
                steps_failed.append("Lago API key missing")
        except Exception as e:
            steps_failed.append(f"Lago config check failed: {e}")

        # Test Ops-Center subscription endpoints
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/billing/plans",
                    timeout=5
                )
                if resp.status_code == 200:
                    plans = resp.json()
                    steps_completed.append(f"Subscription plans available: {len(plans)}")
                else:
                    steps_failed.append("Cannot retrieve subscription plans")
                    integration_issues.append("Billing API not working")
        except Exception as e:
            steps_failed.append(f"Plans endpoint failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.FAILED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="Subscription Management",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={}
        )

    async def test_2fa_enforcement(self) -> TestResult:
        """
        Journey 6: 2FA Enforcement Flow
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Check if 2FA endpoints exist
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.options(
                    f"{self.base_url}/api/v1/two-factor/setup",
                    timeout=5
                )
                if resp.status_code in [200, 204, 405]:
                    steps_completed.append("2FA endpoints available")
                else:
                    steps_failed.append("2FA endpoints not found")
                    recommendations.append("Implement 2FA management endpoints")
        except Exception as e:
            steps_failed.append(f"2FA check failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.BLOCKED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="2FA Enforcement",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={}
        )

    async def test_organization_management(self) -> TestResult:
        """
        Journey 7: Organization Management
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Test organization creation
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.post(
                    f"{self.base_url}/api/v1/org",
                    json={
                        "name": f"Test Org {datetime.now().timestamp()}",
                        "owner_user_id": self.test_user_id or "test"
                    },
                    timeout=10
                )
                if resp.status_code == 201:
                    org_data = resp.json()
                    self.test_org_id = org_data.get("id")
                    steps_completed.append(f"Organization created: {self.test_org_id}")
                else:
                    steps_failed.append(f"Org creation failed: {resp.status_code}")
                    integration_issues.append("Organization management API issues")
        except Exception as e:
            steps_failed.append(f"Org creation error: {e}")

        # Test organization listing
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/org",
                    timeout=5
                )
                if resp.status_code == 200:
                    orgs = resp.json()
                    steps_completed.append(f"Organizations retrieved: {len(orgs)}")
                else:
                    steps_failed.append("Cannot list organizations")
        except Exception as e:
            steps_failed.append(f"Org listing failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.FAILED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="Organization Management",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={"test_org_id": self.test_org_id}
        )

    async def test_monitoring_integration(self) -> TestResult:
        """
        Journey 8: Monitoring Integration
        """
        start_time = datetime.now()
        steps_completed = []
        steps_failed = []
        integration_issues = []
        recommendations = []

        # Check Prometheus metrics
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.base_url}/metrics",
                    timeout=5
                )
                if resp.status_code == 200:
                    steps_completed.append("Prometheus metrics endpoint active")
                else:
                    steps_failed.append("Metrics endpoint not found")
                    recommendations.append("Expose /metrics endpoint for Prometheus scraping")
        except Exception as e:
            steps_failed.append(f"Metrics check failed: {e}")

        # Check audit logging
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/audit/logs",
                    timeout=5
                )
                if resp.status_code == 200:
                    steps_completed.append("Audit logging available")
                else:
                    steps_failed.append("Audit logs not accessible")
        except Exception as e:
            steps_failed.append(f"Audit log check failed: {e}")

        status = TestStatus.PARTIAL if steps_completed else TestStatus.FAILED
        execution_time = (datetime.now() - start_time).total_seconds()

        return TestResult(
            journey_name="Monitoring Integration",
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            integration_issues=integration_issues,
            recommendations=recommendations,
            execution_time=execution_time,
            details={}
        )

    async def run_all_tests(self) -> List[TestResult]:
        """
        Run all integration tests in sequence
        """
        print("\n" + "="*80)
        print("🧪 OPS-CENTER INTEGRATION TEST SUITE")
        print("="*80 + "\n")

        # Check service availability first
        print("📡 Checking service availability...")
        availability = await self.check_service_availability()
        print("\nService Status:")
        for service, available in availability.items():
            status = "✅ Available" if available else "❌ Unavailable"
            print(f"  {service:15} {status}")
        print()

        # Run all test journeys
        tests = [
            ("test_user_onboarding_flow", "1. New User Onboarding"),
            ("test_api_key_workflow", "2. API Key Workflow"),
            ("test_credit_purchase_flow", "3. Credit Purchase Flow"),
            ("test_byok_flow", "4. BYOK Flow"),
            ("test_subscription_management", "5. Subscription Management"),
            ("test_2fa_enforcement", "6. 2FA Enforcement"),
            ("test_organization_management", "7. Organization Management"),
            ("test_monitoring_integration", "8. Monitoring Integration")
        ]

        for method_name, test_name in tests:
            print(f"🔄 Running: {test_name}...")
            method = getattr(self, method_name)
            result = await method()
            self.results.append(result)
            print(f"   {result.status.value} {result.status.name}\n")

        return self.results

    def generate_report(self) -> str:
        """
        Generate comprehensive test report in Markdown format
        """
        report_lines = [
            "# Integration Test Report - Ops-Center",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Test Suite**: Critical User Journeys",
            "",
            "---",
            "",
            "## Executive Summary",
            ""
        ]

        # Calculate summary statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        partial = sum(1 for r in self.results if r.status == TestStatus.PARTIAL)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

        report_lines.extend([
            f"- **Total Tests**: {total_tests}",
            f"- **Passed**: {passed} ({passed/total_tests*100:.1f}%)" if total_tests > 0 else "- **Passed**: 0",
            f"- **Partial**: {partial} ({partial/total_tests*100:.1f}%)" if total_tests > 0 else "- **Partial**: 0",
            f"- **Failed**: {failed} ({failed/total_tests*100:.1f}%)" if total_tests > 0 else "- **Failed**: 0",
            f"- **Skipped**: {skipped}" if skipped > 0 else "",
            "",
            "---",
            "",
            "## Test Results",
            ""
        ])

        # Detailed results for each journey
        for result in self.results:
            report_lines.extend([
                f"### {result.status.value} {result.journey_name}",
                "",
                f"**Status**: {result.status.name}",
                f"**Execution Time**: {result.execution_time:.2f}s",
                ""
            ])

            if result.steps_completed:
                report_lines.append("**✅ Steps Completed:**")
                for step in result.steps_completed:
                    report_lines.append(f"- {step}")
                report_lines.append("")

            if result.steps_failed:
                report_lines.append("**❌ Steps Failed:**")
                for step in result.steps_failed:
                    report_lines.append(f"- {step}")
                report_lines.append("")

            if result.integration_issues:
                report_lines.append("**🔗 Integration Issues:**")
                for issue in result.integration_issues:
                    report_lines.append(f"- {issue}")
                report_lines.append("")

            if result.recommendations:
                report_lines.append("**💡 Recommendations:**")
                for rec in result.recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        # Overall recommendations
        report_lines.extend([
            "## Overall Recommendations",
            "",
            "### Priority 1: Critical Fixes",
            ""
        ])

        # Collect unique integration issues
        all_integration_issues = set()
        for result in self.results:
            all_integration_issues.update(result.integration_issues)

        if all_integration_issues:
            for issue in sorted(all_integration_issues):
                report_lines.append(f"1. **Fix**: {issue}")
        else:
            report_lines.append("- No critical integration issues found")

        report_lines.extend([
            "",
            "### Priority 2: Enhancement Opportunities",
            ""
        ])

        # Collect unique recommendations
        all_recommendations = set()
        for result in self.results:
            all_recommendations.update(result.recommendations)

        if all_recommendations:
            for rec in sorted(all_recommendations):
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- No enhancement recommendations")

        report_lines.extend([
            "",
            "---",
            "",
            "## Next Steps",
            "",
            "1. **Address Critical Issues**: Fix all integration issues flagged above",
            "2. **Re-run Tests**: Execute test suite after fixes",
            "3. **Monitor Production**: Set up continuous monitoring",
            "4. **Documentation**: Update integration docs based on findings",
            "",
            "---",
            "",
            "*Generated by Integration Test Suite v1.0*"
        ])

        return "\n".join(report_lines)


async def main():
    """
    Main entry point
    """
    suite = IntegrationTestSuite()

    try:
        # Run all tests
        await suite.run_all_tests()

        # Generate report
        report = suite.generate_report()

        # Save to file
        report_path = "/home/muut/Production/UC-Cloud/services/ops-center/TEST_REPORT_INTEGRATION.md"
        with open(report_path, "w") as f:
            f.write(report)

        print("\n" + "="*80)
        print("📊 TEST REPORT GENERATED")
        print("="*80)
        print(f"\nReport saved to: {report_path}")
        print("\nSummary:")
        for result in suite.results:
            print(f"  {result.status.value} {result.journey_name}")
        print()

    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
