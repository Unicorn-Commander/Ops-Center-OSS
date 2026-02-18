#!/usr/bin/env python3
"""
Detailed Authenticated Backend API Testing Script
Tests with proper authentication and database verification

Usage:
    # Set authentication token first
    export AUTH_TOKEN="your_jwt_token_here"
    python3 test_detailed_authenticated.py
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

BASE_URL = "http://localhost:8084"
API_BASE = f"{BASE_URL}/api/v1"
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")

# Test results storage
detailed_results = {
    "api_key_management": [],
    "user_management": [],
    "billing": [],
    "organizations": [],
    "2fa": [],
    "subscription_tiers": [],
    "llm": [],
    "monitoring": [],
    "bugs": []
}

def get_headers(include_auth: bool = True) -> Dict:
    """Get request headers with optional auth"""
    headers = {"Content-Type": "application/json"}
    if include_auth and AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers

def log_test(category: str, test_name: str, result: str, details: str = ""):
    """Log test result"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status = "✅" if "PASS" in result else "❌" if "FAIL" in result else "⚠️"
    print(f"{status} [{timestamp}] {category}: {test_name} - {result}")
    if details:
        print(f"   └─ {details}")

    detailed_results[category].append({
        "test": test_name,
        "result": result,
        "details": details,
        "timestamp": timestamp
    })

def query_database(query: str) -> Optional[List]:
    """Query PostgreSQL database"""
    try:
        cmd = f'docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "{query}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return lines
        return None
    except Exception as e:
        return None

def test_api_key_management():
    """Test API Key Management endpoints"""
    print("\n" + "="*80)
    print("TESTING: API KEY MANAGEMENT")
    print("="*80)

    # Get test user ID
    response = requests.get(f"{API_BASE}/admin/users", headers=get_headers(), timeout=10)
    if response.status_code == 200:
        users = response.json().get("users", [])
        if users:
            test_user = users[0]
            user_id = test_user.get("id")
            log_test("api_key_management", "Found test user", "PASS", f"User: {user_id}")

            # Test 1: Create API key
            try:
                create_response = requests.post(
                    f"{API_BASE}/admin/users/{user_id}/api-keys",
                    headers=get_headers(),
                    json={"name": "Test API Key", "expires_in_days": 30},
                    timeout=10
                )
                if create_response.status_code == 200:
                    api_key_data = create_response.json()
                    log_test("api_key_management", "Create API key", "PASS",
                             f"Key ID: {api_key_data.get('id', 'N/A')}")

                    # Verify in database
                    db_result = query_database(f"SELECT id, name FROM api_keys WHERE user_id='{user_id}' LIMIT 1;")
                    if db_result:
                        log_test("api_key_management", "API key in database", "PASS", f"Found: {db_result[0]}")
                    else:
                        log_test("api_key_management", "API key in database", "FAIL", "Not found in database")
                        detailed_results["bugs"].append("API key created but not persisted to database")
                else:
                    log_test("api_key_management", "Create API key", "FAIL",
                             f"Status: {create_response.status_code}, {create_response.text[:200]}")
            except Exception as e:
                log_test("api_key_management", "Create API key", "FAIL", str(e))

            # Test 2: List API keys
            try:
                list_response = requests.get(
                    f"{API_BASE}/admin/users/{user_id}/api-keys",
                    headers=get_headers(),
                    timeout=10
                )
                if list_response.status_code == 200:
                    keys = list_response.json().get("api_keys", [])
                    log_test("api_key_management", "List API keys", "PASS",
                             f"Found {len(keys)} key(s)")
                else:
                    log_test("api_key_management", "List API keys", "FAIL",
                             f"Status: {list_response.status_code}")
            except Exception as e:
                log_test("api_key_management", "List API keys", "FAIL", str(e))

            # Test 3: Delete API key
            if create_response.status_code == 200 and api_key_data:
                try:
                    key_id = api_key_data.get("id")
                    delete_response = requests.delete(
                        f"{API_BASE}/admin/users/{user_id}/api-keys/{key_id}",
                        headers=get_headers(),
                        timeout=10
                    )
                    if delete_response.status_code == 200:
                        log_test("api_key_management", "Delete API key", "PASS")
                    else:
                        log_test("api_key_management", "Delete API key", "FAIL",
                                 f"Status: {delete_response.status_code}")
                except Exception as e:
                    log_test("api_key_management", "Delete API key", "FAIL", str(e))

        else:
            log_test("api_key_management", "Found test user", "FAIL", "No users in database")
    else:
        log_test("api_key_management", "Get users for testing", "FAIL",
                 f"Status: {response.status_code}")

def test_user_management():
    """Test User Management endpoints"""
    print("\n" + "="*80)
    print("TESTING: USER MANAGEMENT")
    print("="*80)

    # Test 1: List users
    try:
        response = requests.get(f"{API_BASE}/admin/users", headers=get_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("user_management", "List users", "PASS",
                     f"Found {data.get('total', 0)} users")
        else:
            log_test("user_management", "List users", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("user_management", "List users", "FAIL", str(e))

    # Test 2: User analytics summary
    try:
        response = requests.get(f"{API_BASE}/admin/users/analytics/summary",
                                headers=get_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("user_management", "Analytics summary", "PASS",
                     f"Total: {data.get('total_users', 0)}, Active: {data.get('active_users', 0)}")

            # Check if metrics match database
            db_count = query_database("SELECT COUNT(*) FROM keycloak_users;")
            if db_count:
                db_total = int(db_count[0])
                api_total = data.get('total_users', 0)
                if db_total != api_total:
                    log_test("user_management", "Analytics accuracy", "WARN",
                             f"DB: {db_total}, API: {api_total} - mismatch!")
                    detailed_results["bugs"].append(
                        f"User count mismatch: Database has {db_total}, API returns {api_total}"
                    )
        else:
            log_test("user_management", "Analytics summary", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("user_management", "Analytics summary", "FAIL", str(e))

    # Test 3: Advanced filtering
    filters = [
        ("tier=professional", "Filter by tier"),
        ("role=admin", "Filter by role"),
        ("status=enabled", "Filter by status"),
        ("search=aaron", "Search by email")
    ]

    for filter_param, description in filters:
        try:
            response = requests.get(f"{API_BASE}/admin/users?{filter_param}",
                                    headers=get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                log_test("user_management", description, "PASS",
                         f"Found {len(data.get('users', []))} user(s)")
            else:
                log_test("user_management", description, "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("user_management", description, "FAIL", str(e))

    # Test 4: Export users
    try:
        response = requests.get(f"{API_BASE}/admin/users/export",
                                headers=get_headers(), timeout=10)
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if "email" in content.lower() and "username" in content.lower():
                log_test("user_management", "Export users CSV", "PASS",
                         f"CSV size: {len(content)} bytes")
            else:
                log_test("user_management", "Export users CSV", "FAIL",
                         "CSV missing expected headers")
                detailed_results["bugs"].append("CSV export missing standard headers (email, username)")
        else:
            log_test("user_management", "Export users CSV", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("user_management", "Export users CSV", "FAIL", str(e))

def test_billing():
    """Test Billing endpoints"""
    print("\n" + "="*80)
    print("TESTING: BILLING")
    print("="*80)

    # Test 1: List plans
    try:
        response = requests.get(f"{API_BASE}/billing/plans", headers=get_headers(), timeout=10)
        if response.status_code == 200:
            plans = response.json()
            log_test("billing", "List subscription plans", "PASS",
                     f"Found {len(plans)} plan(s)")

            # Verify Lago integration
            expected_tiers = ["trial", "starter", "professional", "enterprise"]
            found_tiers = [p.get("code", "").lower() for p in plans]
            missing = [t for t in expected_tiers if t not in found_tiers]
            if missing:
                log_test("billing", "Verify plan tiers", "WARN",
                         f"Missing tiers: {missing}")
        else:
            log_test("billing", "List subscription plans", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("billing", "List subscription plans", "FAIL", str(e))

    # Test 2: Current subscription
    try:
        response = requests.get(f"{API_BASE}/billing/subscriptions/current",
                                headers=get_headers(), timeout=10)
        if response.status_code in [200, 404]:
            log_test("billing", "Get current subscription", "PASS")
        else:
            log_test("billing", "Get current subscription", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("billing", "Get current subscription", "FAIL", str(e))

    # Test 3: Invoice history
    try:
        response = requests.get(f"{API_BASE}/billing/invoices", headers=get_headers(), timeout=10)
        if response.status_code in [200, 404]:
            log_test("billing", "Get invoice history", "PASS")
        else:
            log_test("billing", "Get invoice history", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("billing", "Get invoice history", "FAIL", str(e))

def test_llm_api():
    """Test LLM API endpoints"""
    print("\n" + "="*80)
    print("TESTING: LLM API")
    print("="*80)

    # Test 1: List models
    try:
        response = requests.get(f"{API_BASE}/llm/models", headers=get_headers(), timeout=10)
        if response.status_code == 200:
            models = response.json().get("data", [])
            log_test("llm", "List models", "PASS", f"Found {len(models)} model(s)")
        else:
            log_test("llm", "List models", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("llm", "List models", "FAIL", str(e))

    # Test 2: Usage statistics
    try:
        response = requests.get(f"{API_BASE}/llm/usage", headers=get_headers(), timeout=10)
        if response.status_code in [200, 404]:
            log_test("llm", "Get usage statistics", "PASS")
        else:
            log_test("llm", "Get usage statistics", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        log_test("llm", "Get usage statistics", "FAIL", str(e))

    # Test 3: Chat completion with API key
    try:
        # Note: This will fail without proper API key setup
        response = requests.post(
            f"{API_BASE}/llm/chat/completions",
            headers=get_headers(),
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=30
        )
        if response.status_code == 200:
            log_test("llm", "Chat completion", "PASS")
        elif response.status_code == 401:
            log_test("llm", "Chat completion", "SKIP", "Requires API key configuration")
        else:
            log_test("llm", "Chat completion", "FAIL",
                     f"Status: {response.status_code}, {response.text[:200]}")
    except Exception as e:
        log_test("llm", "Chat completion", "FAIL", str(e))

def generate_detailed_report():
    """Generate comprehensive test report"""

    report = f"""# Ops-Center Backend API - Detailed Test Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Target**: {BASE_URL}
**Authentication**: {"✅ Configured" if AUTH_TOKEN else "❌ Not configured"}

---

## Executive Summary

| Category | Tests Run | Passed | Failed | Bugs Found |
|----------|-----------|--------|--------|------------|
| API Key Management | {len(detailed_results['api_key_management'])} | {sum(1 for t in detailed_results['api_key_management'] if 'PASS' in t['result'])} | {sum(1 for t in detailed_results['api_key_management'] if 'FAIL' in t['result'])} | {len([b for b in detailed_results['bugs'] if 'API key' in b])} |
| User Management | {len(detailed_results['user_management'])} | {sum(1 for t in detailed_results['user_management'] if 'PASS' in t['result'])} | {sum(1 for t in detailed_results['user_management'] if 'FAIL' in t['result'])} | {len([b for b in detailed_results['bugs'] if 'User' in b or 'count' in b])} |
| Billing | {len(detailed_results['billing'])} | {sum(1 for t in detailed_results['billing'] if 'PASS' in t['result'])} | {sum(1 for t in detailed_results['billing'] if 'FAIL' in t['result'])} | {len([b for b in detailed_results['bugs'] if 'billing' in b.lower()])} |
| LLM API | {len(detailed_results['llm'])} | {sum(1 for t in detailed_results['llm'] if 'PASS' in t['result'])} | {sum(1 for t in detailed_results['llm'] if 'FAIL' in t['result'])} | {len([b for b in detailed_results['bugs'] if 'LLM' in b or 'llm' in b])} |
| **Total** | {sum(len(v) for v in detailed_results.values() if isinstance(v, list) and v and 'test' in v[0])} | - | - | {len(detailed_results['bugs'])} |

---

## Detailed Test Results

"""

    categories = [
        ("api_key_management", "API Key Management"),
        ("user_management", "User Management"),
        ("billing", "Billing"),
        ("llm", "LLM API")
    ]

    for key, title in categories:
        if detailed_results[key]:
            report += f"\n### {title}\n\n"
            for test in detailed_results[key]:
                status = "✅" if "PASS" in test['result'] else "❌" if "FAIL" in test['result'] else "⚠️"
                report += f"{status} **{test['test']}**: {test['result']}\n"
                if test['details']:
                    report += f"   - {test['details']}\n"
            report += "\n"

    if detailed_results['bugs']:
        report += "\n## 🐛 Bugs Discovered\n\n"
        for i, bug in enumerate(detailed_results['bugs'], 1):
            report += f"{i}. {bug}\n"

    report += """

---

## Critical Issues Identified

### High Priority

1. **API Key Persistence**: Verify API keys are correctly stored with bcrypt hashing
2. **User Count Mismatch**: Database and API may return different user counts
3. **CSV Export Headers**: Verify all expected headers are present

### Medium Priority

1. **Error Response Consistency**: Standardize error formats across all endpoints
2. **Rate Limiting**: Verify rate limiting is applied correctly
3. **Audit Logging**: Ensure all actions are logged

### Low Priority

1. **Response Time Optimization**: Some queries may be slow under load
2. **Cache Invalidation**: Verify caches are cleared on updates
3. **Documentation**: Update API docs to match actual behavior

---

## Recommendations

### Immediate Actions

1. **Authentication Testing**: Set up proper test authentication for comprehensive testing
2. **Database Verification**: Add automated database state verification for all write operations
3. **Error Handling**: Review and standardize error responses

### Short-Term Improvements

1. **Integration Tests**: Create end-to-end user flow tests
2. **Load Testing**: Test performance under realistic traffic
3. **Security Audit**: Review for SQL injection, XSS, CSRF vulnerabilities

### Long-Term Enhancements

1. **Automated Testing**: Set up CI/CD pipeline with automated tests
2. **Monitoring**: Add real-time monitoring and alerting
3. **Documentation**: Generate OpenAPI/Swagger documentation

---

**Report End**
"""

    return report

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("OPS-CENTER BACKEND API - DETAILED AUTHENTICATED TESTING")
    print("="*80)

    if not AUTH_TOKEN:
        print("\n⚠️  WARNING: No authentication token provided!")
        print("   Set AUTH_TOKEN environment variable for full testing")
        print("   Example: export AUTH_TOKEN='your_jwt_token_here'\n")

    # Run test suites
    test_api_key_management()
    test_user_management()
    test_billing()
    test_llm_api()

    # Generate report
    report = generate_detailed_report()
    report_path = "/opt/ops-center/TEST_REPORT_BACKEND_DETAILED.md"

    with open(report_path, 'w') as f:
        f.write(report)

    print("\n" + "="*80)
    print(f"📄 Detailed report saved to: {report_path}")
    print("="*80)

    # Print bug summary
    if detailed_results['bugs']:
        print(f"\n🐛 {len(detailed_results['bugs'])} BUG(S) DISCOVERED:\n")
        for i, bug in enumerate(detailed_results['bugs'], 1):
            print(f"   {i}. {bug}")
    else:
        print("\n✅ No bugs discovered!")

if __name__ == "__main__":
    main()
