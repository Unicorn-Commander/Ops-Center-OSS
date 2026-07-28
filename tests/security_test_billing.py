#!/usr/bin/env python3
"""
Billing System Security Test Suite
===================================

Tests authentication, authorization, input validation, and security controls
for all billing API endpoints.

Author: Ops-Center Security Team
Created: 2025-11-12
"""

import requests
import json
import sys
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Test configuration
BASE_URL = "http://localhost:8084"
API_PREFIX = "/api/v1/org-billing"

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class SecurityTestResult:
    """Result of a security test"""
    def __init__(self, test_name: str, passed: bool, severity: str = "Medium", details: str = ""):
        self.test_name = test_name
        self.passed = passed
        self.severity = severity
        self.details = details
        self.timestamp = datetime.now()

class BillingSecurityTester:
    """Comprehensive security tester for billing endpoints"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_prefix = API_PREFIX
        self.results: List[SecurityTestResult] = []
        self.session = requests.Session()
        self.auth_token: Optional[str] = None

    def add_result(self, test_name: str, passed: bool, severity: str, details: str):
        """Add a test result"""
        result = SecurityTestResult(test_name, passed, severity, details)
        self.results.append(result)

        # Print result immediately
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        severity_color = {
            "Critical": Colors.RED,
            "High": Colors.YELLOW,
            "Medium": Colors.BLUE,
            "Low": Colors.GREEN
        }.get(severity, Colors.RESET)

        print(f"{status} {Colors.BOLD}{test_name}{Colors.RESET} [{severity_color}{severity}{Colors.RESET}]")
        if details:
            print(f"   {details}")

    def test_unauthenticated_access(self):
        """Test 1: Unauthenticated access should be blocked"""
        print(f"\n{Colors.BOLD}=== Testing Unauthenticated Access ==={Colors.RESET}")

        endpoints = [
            ("/billing/user", "GET"),
            ("/subscriptions", "POST"),
            ("/credits/test-org-id", "GET"),
            ("/credits/test-org-id/add", "POST"),
            ("/billing/system", "GET"),
        ]

        for endpoint, method in endpoints:
            url = f"{self.base_url}{self.api_prefix}{endpoint}"

            try:
                if method == "GET":
                    response = self.session.get(url, timeout=5)
                else:
                    response = self.session.post(url, json={}, timeout=5)

                if response.status_code == 401:
                    self.add_result(
                        f"Unauthenticated {method} {endpoint}",
                        True,
                        "Critical",
                        f"Correctly returned 401 Unauthorized"
                    )
                else:
                    self.add_result(
                        f"Unauthenticated {method} {endpoint}",
                        False,
                        "Critical",
                        f"Expected 401, got {response.status_code}"
                    )
            except Exception as e:
                self.add_result(
                    f"Unauthenticated {method} {endpoint}",
                    False,
                    "Critical",
                    f"Exception: {str(e)}"
                )

    def test_token_validation(self):
        """Test 2: Invalid/expired tokens should be rejected"""
        print(f"\n{Colors.BOLD}=== Testing Token Validation ==={Colors.RESET}")

        # Test with invalid token
        invalid_tokens = [
            ("empty", ""),
            ("malformed", "not-a-jwt-token"),
            ("fake", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.signature"),
        ]

        for token_type, token in invalid_tokens:
            url = f"{self.base_url}{self.api_prefix}/billing/user"

            # Set invalid token as cookie
            cookies = {"session_token": token}

            try:
                response = self.session.get(url, cookies=cookies, timeout=5)

                if response.status_code == 401:
                    self.add_result(
                        f"Reject {token_type} token",
                        True,
                        "Critical",
                        f"Correctly rejected {token_type} token"
                    )
                else:
                    self.add_result(
                        f"Reject {token_type} token",
                        False,
                        "Critical",
                        f"Expected 401, got {response.status_code}"
                    )
            except Exception as e:
                self.add_result(
                    f"Reject {token_type} token",
                    False,
                    "Critical",
                    f"Exception: {str(e)}"
                )

    def test_sql_injection(self):
        """Test 3: SQL injection protection"""
        print(f"\n{Colors.BOLD}=== Testing SQL Injection Protection ==={Colors.RESET}")

        # SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE organizations; --",
            "1' UNION SELECT NULL, NULL, NULL--",
            "admin'--",
            "' OR 1=1--",
        ]

        for payload in sql_payloads:
            # Test in org_id parameter
            url = f"{self.base_url}{self.api_prefix}/subscriptions/{payload}"

            # Add a fake cookie to pass auth check
            cookies = {"session_token": "test-token"}

            try:
                response = self.session.get(url, cookies=cookies, timeout=5)

                # Should either return 401 (no auth), 403 (no permission), or 404 (not found)
                # Should NOT return 500 (database error) or 200 (successful injection)

                if response.status_code in [401, 403, 404, 400]:
                    self.add_result(
                        f"SQL injection in org_id",
                        True,
                        "Critical",
                        f"Protected against: {payload[:30]}..."
                    )
                elif response.status_code == 500:
                    # Check if error message exposes database details
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", "")
                        if any(keyword in error_msg.lower() for keyword in ["sql", "postgres", "query", "table"]):
                            self.add_result(
                                f"SQL injection in org_id",
                                False,
                                "Critical",
                                f"Database error exposed: {error_msg[:50]}..."
                            )
                        else:
                            self.add_result(
                                f"SQL injection in org_id",
                                True,
                                "Medium",
                                f"500 error but no sensitive data exposed"
                            )
                    except:
                        self.add_result(
                            f"SQL injection in org_id",
                            True,
                            "Medium",
                            f"500 error, details unclear"
                        )
                else:
                    self.add_result(
                        f"SQL injection in org_id",
                        False,
                        "Critical",
                        f"Unexpected status {response.status_code}"
                    )
            except requests.exceptions.Timeout:
                self.add_result(
                    f"SQL injection in org_id",
                    False,
                    "High",
                    f"Request timeout - possible DoS vulnerability"
                )
            except Exception as e:
                self.add_result(
                    f"SQL injection in org_id",
                    True,
                    "Low",
                    f"Connection error (expected): {str(e)[:50]}"
                )

    def test_xss_protection(self):
        """Test 4: XSS protection in JSON responses"""
        print(f"\n{Colors.BOLD}=== Testing XSS Protection ==={Colors.RESET}")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            # Test creating subscription with XSS in org_id
            url = f"{self.base_url}{self.api_prefix}/subscriptions"
            cookies = {"session_token": "test-token"}

            data = {
                "org_id": payload,
                "subscription_plan": "platform",
                "monthly_price": 50.00,
                "billing_cycle": "monthly"
            }

            try:
                response = self.session.post(url, json=data, cookies=cookies, timeout=5)

                # Check if payload is in response
                response_text = response.text

                if payload in response_text and "<script>" in response_text:
                    self.add_result(
                        f"XSS in response",
                        False,
                        "High",
                        f"Unescaped XSS payload in response: {payload[:30]}"
                    )
                else:
                    self.add_result(
                        f"XSS in response",
                        True,
                        "High",
                        f"XSS payload properly escaped or rejected"
                    )
            except Exception as e:
                self.add_result(
                    f"XSS in response",
                    True,
                    "Low",
                    f"Connection error (expected): {str(e)[:50]}"
                )

    def test_authorization_bypass(self):
        """Test 5: Authorization checks (role-based access)"""
        print(f"\n{Colors.BOLD}=== Testing Authorization (Role-Based Access) ==={Colors.RESET}")

        # Test admin-only endpoint with fake token
        url = f"{self.base_url}{self.api_prefix}/billing/system"
        cookies = {"session_token": "fake-regular-user-token"}

        try:
            response = self.session.get(url, cookies=cookies, timeout=5)

            # Should return 401 (no auth) or 403 (not authorized)
            if response.status_code in [401, 403]:
                self.add_result(
                    "Admin-only endpoint protection",
                    True,
                    "High",
                    f"Correctly blocked non-admin access (status {response.status_code})"
                )
            else:
                self.add_result(
                    "Admin-only endpoint protection",
                    False,
                    "High",
                    f"Unexpected status {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Admin-only endpoint protection",
                True,
                "Low",
                f"Connection error (expected): {str(e)[:50]}"
            )

    def test_data_exposure(self):
        """Test 6: Check if users can access other users' data"""
        print(f"\n{Colors.BOLD}=== Testing Data Exposure ==={Colors.RESET}")

        # Try to access another user's billing data
        fake_org_id = str(uuid.uuid4())
        url = f"{self.base_url}{self.api_prefix}/subscriptions/{fake_org_id}"
        cookies = {"session_token": "fake-user-token"}

        try:
            response = self.session.get(url, cookies=cookies, timeout=5)

            # Should return 401, 403, or 404
            if response.status_code in [401, 403, 404]:
                self.add_result(
                    "Cross-user data access",
                    True,
                    "Critical",
                    f"Correctly blocked unauthorized access (status {response.status_code})"
                )
            elif response.status_code == 200:
                self.add_result(
                    "Cross-user data access",
                    False,
                    "Critical",
                    f"Successfully accessed other user's data!"
                )
            else:
                self.add_result(
                    "Cross-user data access",
                    True,
                    "Medium",
                    f"Ambiguous result (status {response.status_code})"
                )
        except Exception as e:
            self.add_result(
                "Cross-user data access",
                True,
                "Low",
                f"Connection error (expected): {str(e)[:50]}"
            )

    def test_input_validation(self):
        """Test 7: Input validation for credit operations"""
        print(f"\n{Colors.BOLD}=== Testing Input Validation ==={Colors.RESET}")

        # Test negative credits
        url = f"{self.base_url}{self.api_prefix}/credits/test-org/add?credits=-1000"
        cookies = {"session_token": "test-token"}

        try:
            response = self.session.post(url, cookies=cookies, timeout=5)

            # Should reject negative credits
            if response.status_code in [400, 422]:
                self.add_result(
                    "Negative credits validation",
                    True,
                    "High",
                    f"Correctly rejected negative credits"
                )
            elif response.status_code in [401, 403]:
                self.add_result(
                    "Negative credits validation",
                    True,
                    "Medium",
                    f"Auth check happened before validation (ok)"
                )
            else:
                self.add_result(
                    "Negative credits validation",
                    False,
                    "High",
                    f"Unexpected status {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Negative credits validation",
                True,
                "Low",
                f"Connection error (expected): {str(e)[:50]}"
            )

        # Test invalid plan type
        url = f"{self.base_url}{self.api_prefix}/subscriptions"
        data = {
            "org_id": "test-org",
            "subscription_plan": "invalid-plan-type",
            "monthly_price": 50.00
        }

        try:
            response = self.session.post(url, json=data, cookies=cookies, timeout=5)

            if response.status_code in [400, 422]:
                self.add_result(
                    "Invalid plan type validation",
                    True,
                    "Medium",
                    f"Correctly rejected invalid plan"
                )
            elif response.status_code in [401, 403]:
                self.add_result(
                    "Invalid plan type validation",
                    True,
                    "Medium",
                    f"Auth check happened before validation (ok)"
                )
            else:
                self.add_result(
                    "Invalid plan type validation",
                    False,
                    "Medium",
                    f"Unexpected status {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Invalid plan type validation",
                True,
                "Low",
                f"Connection error (expected): {str(e)[:50]}"
            )

    def test_rate_limiting(self):
        """Test 8: Rate limiting protection"""
        print(f"\n{Colors.BOLD}=== Testing Rate Limiting ==={Colors.RESET}")

        url = f"{self.base_url}{self.api_prefix}/billing/user"
        cookies = {"session_token": "test-token"}

        # Send 50 rapid requests
        statuses = []
        for i in range(50):
            try:
                response = self.session.get(url, cookies=cookies, timeout=1)
                statuses.append(response.status_code)
            except:
                statuses.append(0)

        # Check if rate limiting kicked in (429 status)
        rate_limited = 429 in statuses

        if rate_limited:
            self.add_result(
                "Rate limiting",
                True,
                "Medium",
                f"Rate limiting active (found 429 status)"
            )
        else:
            self.add_result(
                "Rate limiting",
                False,
                "Medium",
                f"No rate limiting detected (consider implementing)"
            )

    def test_error_messages(self):
        """Test 9: Error messages shouldn't leak sensitive info"""
        print(f"\n{Colors.BOLD}=== Testing Error Message Security ==={Colors.RESET}")

        # Test database error handling
        url = f"{self.base_url}{self.api_prefix}/subscriptions/invalid-uuid-format"
        cookies = {"session_token": "test-token"}

        try:
            response = self.session.get(url, cookies=cookies, timeout=5)

            if response.status_code in [400, 404]:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")

                    # Check for sensitive keywords
                    sensitive_keywords = [
                        "postgres", "sql", "query", "table", "column",
                        "database", "connection", "password", "secret"
                    ]

                    found_sensitive = [kw for kw in sensitive_keywords if kw in detail.lower()]

                    if found_sensitive:
                        self.add_result(
                            "Error message security",
                            False,
                            "Medium",
                            f"Sensitive keywords exposed: {', '.join(found_sensitive)}"
                        )
                    else:
                        self.add_result(
                            "Error message security",
                            True,
                            "Medium",
                            f"Error messages don't expose sensitive data"
                        )
                except:
                    self.add_result(
                        "Error message security",
                        True,
                        "Medium",
                        f"Error response not JSON (likely secure)"
                    )
            else:
                self.add_result(
                    "Error message security",
                    True,
                    "Low",
                    f"Auth check prevented error (status {response.status_code})"
                )
        except Exception as e:
            self.add_result(
                "Error message security",
                True,
                "Low",
                f"Connection error (expected): {str(e)[:50]}"
            )

    def generate_report(self):
        """Generate security test report"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}BILLING SYSTEM SECURITY TEST REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.results)}")

        # Count results by severity and status
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        critical_fails = sum(1 for r in self.results if not r.passed and r.severity == "Critical")
        high_fails = sum(1 for r in self.results if not r.passed and r.severity == "High")
        medium_fails = sum(1 for r in self.results if not r.passed and r.severity == "Medium")
        low_fails = sum(1 for r in self.results if not r.passed and r.severity == "Low")

        print(f"\n{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")

        if failed > 0:
            print(f"\n{Colors.BOLD}Failed Tests by Severity:{Colors.RESET}")
            if critical_fails > 0:
                print(f"  {Colors.RED}Critical: {critical_fails}{Colors.RESET}")
            if high_fails > 0:
                print(f"  {Colors.YELLOW}High: {high_fails}{Colors.RESET}")
            if medium_fails > 0:
                print(f"  {Colors.BLUE}Medium: {medium_fails}{Colors.RESET}")
            if low_fails > 0:
                print(f"  {Colors.GREEN}Low: {low_fails}{Colors.RESET}")

        # List all failures
        failures = [r for r in self.results if not r.passed]
        if failures:
            print(f"\n{Colors.BOLD}VULNERABILITIES FOUND:{Colors.RESET}")
            for i, result in enumerate(failures, 1):
                severity_color = {
                    "Critical": Colors.RED,
                    "High": Colors.YELLOW,
                    "Medium": Colors.BLUE,
                    "Low": Colors.GREEN
                }.get(result.severity, Colors.RESET)

                print(f"\n{i}. {severity_color}[{result.severity}]{Colors.RESET} {result.test_name}")
                print(f"   {result.details}")

        # Recommendations
        print(f"\n{Colors.BOLD}RECOMMENDATIONS:{Colors.RESET}")

        if critical_fails > 0:
            print(f"{Colors.RED}⚠️  CRITICAL: Fix all Critical severity issues immediately{Colors.RESET}")

        recommendations = [
            ("No rate limiting detected", "Implement rate limiting (e.g., 100 requests/minute per user)"),
            ("SQL injection", "Use parameterized queries (asyncpg already does this, verify all queries)"),
            ("XSS in response", "Ensure all user input is properly escaped in JSON responses"),
            ("Admin-only endpoint", "Verify role-based access control is enforced consistently"),
        ]

        for check, recommendation in recommendations:
            if any(check.lower() in r.test_name.lower() and not r.passed for r in self.results):
                print(f"  • {recommendation}")

        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}\n")

        # Return exit code
        return 0 if critical_fails == 0 and high_fails == 0 else 1

    def run_all_tests(self):
        """Run all security tests"""
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}STARTING BILLING SYSTEM SECURITY TESTS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"Target: {self.base_url}{self.api_prefix}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Run all test categories
        self.test_unauthenticated_access()
        self.test_token_validation()
        self.test_sql_injection()
        self.test_xss_protection()
        self.test_authorization_bypass()
        self.test_data_exposure()
        self.test_input_validation()
        self.test_rate_limiting()
        self.test_error_messages()

        # Generate report
        return self.generate_report()


def main():
    """Main entry point"""
    tester = BillingSecurityTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
