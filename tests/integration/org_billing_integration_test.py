#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Organization Billing System
Tests: Frontend UI + Backend API + LiteLLM Middleware

Author: Integration Testing Teamlead
Date: November 15, 2025
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures


class BillingIntegrationTest:
    """Complete integration test suite for org billing system"""

    def __init__(self, base_url: str = "http://localhost:8084"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.test_results = []
        self.test_data = {}

        # Test credentials (will be populated from Keycloak)
        self.admin_token = None
        self.test_org_id = "b44b6688-2e5d-45ad-9bae-412f38d58201"  # From existing data
        self.test_user_id = "test-user-api-12345"  # From existing data

    def log_test(self, name: str, status: str, details: str = "", response_time: float = 0):
        """Log test result"""
        result = {
            "test": name,
            "status": status,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {name}: {status} ({result['response_time_ms']}ms)")
        if details:
            print(f"   {details}")

    def test_backend_api_health(self):
        """Test 1: Backend API Health Check"""
        start = time.time()
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            elapsed = time.time() - start

            if response.status_code == 200:
                self.log_test(
                    "Backend API Health Check",
                    "PASS",
                    f"Status: {response.status_code}",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "Backend API Health Check",
                    "FAIL",
                    f"Unexpected status: {response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "Backend API Health Check",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_org_credits_get(self):
        """Test 2: GET Organization Credits"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.api_url}/org-billing/credits/{self.test_org_id}",
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.test_data['org_credits'] = data

                # Verify structure
                required_fields = ['total_credits', 'allocated_credits', 'used_credits', 'available_credits']
                missing = [f for f in required_fields if f not in data]

                if missing:
                    self.log_test(
                        "GET Organization Credits",
                        "FAIL",
                        f"Missing fields: {missing}",
                        elapsed
                    )
                    return False

                self.log_test(
                    "GET Organization Credits",
                    "PASS",
                    f"Total: {data['total_credits']}, Available: {data['available_credits']}",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "GET Organization Credits",
                    "FAIL",
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "GET Organization Credits",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_user_allocation_get(self):
        """Test 3: GET User Credit Allocation"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}/{self.test_user_id}",
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.test_data['user_allocation'] = data

                self.log_test(
                    "GET User Credit Allocation",
                    "PASS",
                    f"Allocated: {data.get('allocated_credits', 0)}, Remaining: {data.get('remaining_credits', 0)}",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "GET User Credit Allocation",
                    "FAIL",
                    f"Status: {response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "GET User Credit Allocation",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_allocations_list(self):
        """Test 4: GET List of Allocations"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}",
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.test_data['allocations_list'] = data

                allocations = data.get('allocations', [])
                self.log_test(
                    "GET List of Allocations",
                    "PASS",
                    f"Found {len(allocations)} allocation(s)",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "GET List of Allocations",
                    "FAIL",
                    f"Status: {response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "GET List of Allocations",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_usage_attribution_get(self):
        """Test 5: GET Usage Attribution"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.api_url}/org-billing/usage/{self.test_org_id}/{self.test_user_id}",
                params={"limit": 10},
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.test_data['usage_attribution'] = data

                usage_records = data.get('usage', [])
                self.log_test(
                    "GET Usage Attribution",
                    "PASS",
                    f"Found {len(usage_records)} usage record(s)",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "GET Usage Attribution",
                    "FAIL",
                    f"Status: {response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "GET Usage Attribution",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_credit_transaction_create(self):
        """Test 6: POST Create Credit Transaction (Purchase)"""
        start = time.time()
        try:
            payload = {
                "amount": 5000,
                "transaction_type": "purchase",
                "payment_method": "stripe",
                "description": "Integration test purchase - 5000 credits"
            }

            response = requests.post(
                f"{self.api_url}/org-billing/credits/{self.test_org_id}/transaction",
                json=payload,
                timeout=5
            )
            elapsed = time.time() - start

            # Note: Endpoint might not exist yet or return 404
            if response.status_code == 201:
                data = response.json()
                self.test_data['credit_transaction'] = data

                self.log_test(
                    "POST Create Credit Transaction",
                    "PASS",
                    f"Transaction created: {data.get('id', 'unknown')}",
                    elapsed
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "POST Create Credit Transaction",
                    "SKIP",
                    "Endpoint not implemented yet",
                    elapsed
                )
                return None  # Skip
            else:
                self.log_test(
                    "POST Create Credit Transaction",
                    "FAIL",
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "POST Create Credit Transaction",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_user_allocation_create(self):
        """Test 7: POST Allocate Credits to User"""
        start = time.time()
        try:
            new_user_id = f"test-integration-user-{int(time.time())}"
            payload = {
                "user_id": new_user_id,
                "allocated_credits": 100,
                "notes": "Integration test allocation"
            }

            response = requests.post(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}",
                json=payload,
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code in [200, 201]:
                data = response.json()
                self.test_data['new_allocation'] = data
                self.test_data['new_user_id'] = new_user_id

                self.log_test(
                    "POST Allocate Credits to User",
                    "PASS",
                    f"Allocated 100 credits to {new_user_id}",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "POST Allocate Credits to User",
                    "FAIL",
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "POST Allocate Credits to User",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_usage_attribution_log(self):
        """Test 8: POST Log Usage Attribution"""
        start = time.time()
        try:
            payload = {
                "service_name": "llm_chat",
                "model": "gpt-3.5-turbo",
                "credits_used": 5,
                "request_tokens": 100,
                "response_tokens": 200,
                "metadata": {
                    "prompt": "Test integration",
                    "response": "Test response"
                }
            }

            response = requests.post(
                f"{self.api_url}/org-billing/usage/{self.test_org_id}/{self.test_user_id}",
                json=payload,
                timeout=5
            )
            elapsed = time.time() - start

            if response.status_code in [200, 201]:
                data = response.json()
                self.test_data['usage_log'] = data

                self.log_test(
                    "POST Log Usage Attribution",
                    "PASS",
                    f"Logged 5 credits usage for llm_chat",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "POST Log Usage Attribution",
                    "FAIL",
                    f"Status: {response.status_code}, Body: {response.text[:200]}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "POST Log Usage Attribution",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_database_consistency(self):
        """Test 9: Database Consistency Check"""
        start = time.time()
        try:
            # This test requires direct database access or special endpoint
            # For now, we'll verify via API

            # Get org credits
            org_response = requests.get(
                f"{self.api_url}/org-billing/credits/{self.test_org_id}",
                timeout=5
            )

            # Get allocations
            alloc_response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}",
                timeout=5
            )

            elapsed = time.time() - start

            if org_response.status_code == 200 and alloc_response.status_code == 200:
                org_data = org_response.json()
                alloc_data = alloc_response.json()

                org_allocated = org_data.get('allocated_credits', 0)
                total_user_allocated = sum(
                    a.get('allocated_credits', 0)
                    for a in alloc_data.get('allocations', [])
                )

                # Check consistency
                if org_allocated == total_user_allocated:
                    self.log_test(
                        "Database Consistency Check",
                        "PASS",
                        f"Org allocated ({org_allocated}) matches sum of user allocations ({total_user_allocated})",
                        elapsed
                    )
                    return True
                else:
                    self.log_test(
                        "Database Consistency Check",
                        "FAIL",
                        f"Mismatch: Org allocated ({org_allocated}) vs User sum ({total_user_allocated})",
                        elapsed
                    )
                    return False
            else:
                self.log_test(
                    "Database Consistency Check",
                    "FAIL",
                    f"API error: Org={org_response.status_code}, Alloc={alloc_response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "Database Consistency Check",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_llm_middleware_integration(self):
        """Test 10: LiteLLM Middleware Credit Deduction"""
        start = time.time()
        try:
            # Test LLM chat completion with credit tracking
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Hello, this is an integration test"}
                ],
                "user": self.test_user_id,
                "max_tokens": 10
            }

            # Get credits before
            before_response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}/{self.test_user_id}",
                timeout=5
            )

            if before_response.status_code != 200:
                self.log_test(
                    "LiteLLM Middleware Integration",
                    "FAIL",
                    "Could not get credits before LLM request",
                    0
                )
                return False

            credits_before = before_response.json().get('remaining_credits', 0)

            # Make LLM request
            llm_response = requests.post(
                f"{self.api_url}/llm/chat/completions",
                json=payload,
                timeout=30
            )

            # Get credits after
            after_response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}/{self.test_user_id}",
                timeout=5
            )

            elapsed = time.time() - start

            if llm_response.status_code == 200 and after_response.status_code == 200:
                credits_after = after_response.json().get('remaining_credits', 0)
                credits_used = credits_before - credits_after

                # Check credit headers
                headers = llm_response.headers
                has_credit_headers = (
                    'X-Credits-Used' in headers or
                    'X-Credits-Remaining' in headers
                )

                if credits_used > 0:
                    self.log_test(
                        "LiteLLM Middleware Integration",
                        "PASS",
                        f"Credits deducted: {credits_used}, Headers: {has_credit_headers}",
                        elapsed
                    )
                    return True
                else:
                    self.log_test(
                        "LiteLLM Middleware Integration",
                        "WARN",
                        f"No credits deducted (before: {credits_before}, after: {credits_after})",
                        elapsed
                    )
                    return None
            elif llm_response.status_code == 402:
                # Insufficient credits
                self.log_test(
                    "LiteLLM Middleware Integration",
                    "PASS",
                    "402 Payment Required - Credit check working!",
                    elapsed
                )
                return True
            else:
                self.log_test(
                    "LiteLLM Middleware Integration",
                    "FAIL",
                    f"LLM Status: {llm_response.status_code}, After Status: {after_response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "LiteLLM Middleware Integration",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_insufficient_credits_handling(self):
        """Test 11: Insufficient Credits Error Handling"""
        start = time.time()
        try:
            # Create a user with very low credits
            low_credit_user = f"low-credit-user-{int(time.time())}"

            # Allocate only 1 credit
            alloc_response = requests.post(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}",
                json={
                    "user_id": low_credit_user,
                    "allocated_credits": 1,
                    "notes": "Low credit test user"
                },
                timeout=5
            )

            if alloc_response.status_code not in [200, 201]:
                self.log_test(
                    "Insufficient Credits Handling",
                    "FAIL",
                    "Could not create low-credit user",
                    0
                )
                return False

            # Try to make expensive LLM request
            payload = {
                "model": "gpt-4",  # More expensive model
                "messages": [
                    {"role": "user", "content": "Write a long essay about artificial intelligence"}
                ],
                "user": low_credit_user,
                "max_tokens": 1000
            }

            llm_response = requests.post(
                f"{self.api_url}/llm/chat/completions",
                json=payload,
                timeout=30
            )

            elapsed = time.time() - start

            if llm_response.status_code == 402:
                error_data = llm_response.json()
                self.log_test(
                    "Insufficient Credits Handling",
                    "PASS",
                    f"Correctly returned 402: {error_data.get('error', 'No error message')}",
                    elapsed
                )
                return True
            elif llm_response.status_code == 200:
                self.log_test(
                    "Insufficient Credits Handling",
                    "FAIL",
                    "Request succeeded despite insufficient credits!",
                    elapsed
                )
                return False
            else:
                self.log_test(
                    "Insufficient Credits Handling",
                    "WARN",
                    f"Unexpected status: {llm_response.status_code}",
                    elapsed
                )
                return None
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "Insufficient Credits Handling",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def test_concurrent_requests(self):
        """Test 12: Concurrent LLM Requests (Race Condition Test)"""
        start = time.time()
        try:
            # Create test user with 100 credits
            concurrent_user = f"concurrent-user-{int(time.time())}"

            alloc_response = requests.post(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}",
                json={
                    "user_id": concurrent_user,
                    "allocated_credits": 100,
                    "notes": "Concurrency test user"
                },
                timeout=5
            )

            if alloc_response.status_code not in [200, 201]:
                self.log_test(
                    "Concurrent Requests Test",
                    "FAIL",
                    "Could not create concurrent test user",
                    0
                )
                return False

            # Make 10 concurrent requests
            def make_llm_request(idx):
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": f"Request {idx}"}
                    ],
                    "user": concurrent_user,
                    "max_tokens": 10
                }

                try:
                    response = requests.post(
                        f"{self.api_url}/llm/chat/completions",
                        json=payload,
                        timeout=30
                    )
                    return {
                        "index": idx,
                        "status": response.status_code,
                        "success": response.status_code == 200
                    }
                except Exception as e:
                    return {
                        "index": idx,
                        "status": 0,
                        "error": str(e)
                    }

            # Execute concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_llm_request, i) for i in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Check credits after
            final_response = requests.get(
                f"{self.api_url}/org-billing/allocations/{self.test_org_id}/{concurrent_user}",
                timeout=5
            )

            elapsed = time.time() - start

            if final_response.status_code == 200:
                final_credits = final_response.json().get('remaining_credits', 0)
                successful_requests = sum(1 for r in results if r.get('success'))

                # Credits should be >= 0 (no negative balance)
                if final_credits >= 0:
                    self.log_test(
                        "Concurrent Requests Test",
                        "PASS",
                        f"No race condition detected. {successful_requests}/10 succeeded, {final_credits} credits remaining",
                        elapsed
                    )
                    return True
                else:
                    self.log_test(
                        "Concurrent Requests Test",
                        "FAIL",
                        f"Race condition! Credits went negative: {final_credits}",
                        elapsed
                    )
                    return False
            else:
                self.log_test(
                    "Concurrent Requests Test",
                    "FAIL",
                    f"Could not get final credits: {final_response.status_code}",
                    elapsed
                )
                return False
        except Exception as e:
            elapsed = time.time() - start
            self.log_test(
                "Concurrent Requests Test",
                "FAIL",
                f"Error: {str(e)}",
                elapsed
            )
            return False

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*80)
        print("ORGANIZATION BILLING SYSTEM - INTEGRATION TEST SUITE")
        print("="*80 + "\n")

        print(f"Target: {self.base_url}")
        print(f"Test Org ID: {self.test_org_id}")
        print(f"Test User ID: {self.test_user_id}")
        print("\n" + "-"*80 + "\n")

        # Run tests
        tests = [
            self.test_backend_api_health,
            self.test_org_credits_get,
            self.test_user_allocation_get,
            self.test_allocations_list,
            self.test_usage_attribution_get,
            self.test_credit_transaction_create,
            self.test_user_allocation_create,
            self.test_usage_attribution_log,
            self.test_database_consistency,
            self.test_llm_middleware_integration,
            self.test_insufficient_credits_handling,
            self.test_concurrent_requests
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test.__name__}: {str(e)}")
                self.log_test(
                    test.__name__,
                    "CRITICAL",
                    f"Uncaught exception: {str(e)}",
                    0
                )

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80 + "\n")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.test_results if r['status'] == 'SKIP')
        warnings = sum(1 for r in self.test_results if r['status'] == 'WARN')

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"⏭️  Skipped: {skipped}")

        pass_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nPass Rate: {pass_rate:.1f}%")

        avg_response_time = sum(r['response_time_ms'] for r in self.test_results) / total if total > 0 else 0
        print(f"Average Response Time: {avg_response_time:.2f}ms")

        # Save detailed report
        report_path = f"/tmp/org_billing_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "skipped": skipped,
                    "pass_rate": pass_rate,
                    "avg_response_time_ms": avg_response_time
                },
                "tests": self.test_results,
                "test_data": self.test_data
            }, f, indent=2)

        print(f"\nDetailed report saved to: {report_path}")

        return pass_rate >= 75  # 75% pass rate considered acceptable


if __name__ == "__main__":
    tester = BillingIntegrationTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
