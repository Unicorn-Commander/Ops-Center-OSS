#!/usr/bin/env python3
"""
Test suite for fixed API endpoints with proper CSRF handling
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8084"
RESULTS = []

# Create session to maintain cookies
session = requests.Session()

def get_csrf_token():
    """Get CSRF token from the server"""
    try:
        # Get CSRF token from the token endpoint
        response = session.get(f"{BASE_URL}/api/csrf-token", timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get('csrf_token')
            if token:
                print(f"✅ Got CSRF token: {token[:20]}...")
                # Add to session headers
                session.headers.update({'X-CSRF-Token': token})
                return token
    except Exception as e:
        print(f"Failed to get CSRF token: {e}")
    return None

def test_endpoint(name, method, path, expected_status=200, data=None, skip_csrf=False):
    """Test a single endpoint and record results"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        # Get fresh CSRF token for POST requests
        if method == "POST" and not skip_csrf:
            csrf_token = get_csrf_token()
            if not csrf_token:
                print("⚠️  Warning: No CSRF token available")
        
        if method == "GET":
            response = session.get(url, timeout=10)
        elif method == "POST":
            response = session.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Determine response type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            response_type = "JSON"
            try:
                response_data = response.json()
                # Truncate large responses
                json_str = json.dumps(response_data, indent=2)
                if len(json_str) > 500:
                    print(f"Response Data: {json_str[:500]}... [truncated]")
                else:
                    print(f"Response Data: {json_str}")
            except:
                response_data = response.text[:500]
                print(f"Response Text: {response_data}")
        elif 'text/csv' in content_type:
            response_type = "CSV"
            response_data = response.text[:200]
            print(f"CSV Data (first 200 chars): {response_data}")
        else:
            response_type = content_type or "Unknown"
            response_data = response.text[:200]
            print(f"Response: {response_data}")
        
        # Determine pass/fail
        # For path corrections, we mainly care that the endpoint exists (not 404)
        # Auth errors (401) are expected since we're not logged in
        # We're testing PATH corrections, not authentication
        if response.status_code == 404:
            passed = False
            error = f"Endpoint not found (404) - PATH ERROR"
        elif response.status_code in [401, 403]:
            # Auth required is OK - means endpoint exists
            passed = True
            error = None
            print(f"ℹ️  Auth required (expected) - endpoint path is correct")
        elif response.status_code == expected_status:
            passed = True
            error = None
        else:
            passed = False
            error = f"Status: {response.status_code}, Expected: {expected_status}"
        
        result = {
            "name": name,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "response_type": response_type,
            "passed": passed,
            "error": error
        }
        
        print(f"\nStatus Code: {response.status_code} (Expected: {expected_status})")
        print(f"Response Type: {response_type}")
        print(f"Result: {'✅ PASS' if passed else '❌ FAIL'}")
        if error:
            print(f"Error: {error}")
        
        RESULTS.append(result)
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        result = {
            "name": name,
            "method": method,
            "path": path,
            "status_code": "ERROR",
            "expected_status": expected_status,
            "response_type": "ERROR",
            "passed": False,
            "error": str(e)
        }
        RESULTS.append(result)
        return result

def print_summary():
    """Print test summary"""
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}\n")
    
    passed = sum(1 for r in RESULTS if r['passed'])
    failed = len(RESULTS) - passed
    
    print(f"Total Tests: {len(RESULTS)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/len(RESULTS)*100):.1f}%\n")
    
    print(f"{'='*80}")
    print(f"{'Test Name':<40} {'Method':<8} {'Status':<10} {'Type':<12} {'Result':<8}")
    print(f"{'='*80}")
    
    for result in RESULTS:
        status = str(result['status_code'])
        result_str = '✅ PASS' if result['passed'] else '❌ FAIL'
        print(f"{result['name']:<40} {result['method']:<8} {status:<10} {result['response_type']:<12} {result_str}")
    
    print(f"{'='*80}\n")
    
    # Print failures
    failures = [r for r in RESULTS if not r['passed']]
    if failures:
        print("\nFAILURE DETAILS:")
        print(f"{'='*80}")
        for result in failures:
            print(f"\n❌ {result['name']}")
            print(f"   Path: {result['path']}")
            print(f"   Status: {result['status_code']}")
            print(f"   Error: {result['error']}")
        print(f"\n{'='*80}\n")
    
    # Print test interpretation
    print("\nTEST INTERPRETATION:")
    print(f"{'='*80}")
    print("We're testing PATH CORRECTIONS, not authentication.")
    print("")
    print("✅ PASS criteria:")
    print("   - 401/403 (Auth required) = Path is correct, endpoint exists")
    print("   - 200 (OK) = Path is correct, endpoint works")
    print("   - 500 (Server error) = Path is correct, but internal error")
    print("")
    print("❌ FAIL criteria:")
    print("   - 404 (Not found) = PATH IS WRONG")
    print("   - Connection errors = Service issues")
    print(f"{'='*80}\n")

def main():
    print(f"\n{'#'*80}")
    print("TESTING FIXED API ENDPOINT PATHS")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'#'*80}\n")
    
    print("ℹ️  NOTE: We're testing that endpoint PATHS are correct.")
    print("   401/403 responses are OK - they mean the endpoint exists.\n")
    
    # Get initial CSRF token
    get_csrf_token()
    
    # Services.jsx endpoints
    print("\n" + "="*80)
    print("SERVICES.JSX ENDPOINTS")
    print("="*80)
    
    test_endpoint(
        name="1. Get All Services",
        method="GET",
        path="/api/v1/services"
    )
    
    test_endpoint(
        name="2. Get System Status",
        method="GET",
        path="/api/v1/system/status"
    )
    
    test_endpoint(
        name="3. Service Action (No-op)",
        method="POST",
        path="/api/v1/services/ops-center-direct/action",
        data={"action": "status"}
    )
    
    # System.jsx endpoints
    print("\n" + "="*80)
    print("SYSTEM.JSX ENDPOINTS")
    print("="*80)
    
    test_endpoint(
        name="4. Get Hardware Info",
        method="GET",
        path="/api/v1/system/hardware"
    )
    
    test_endpoint(
        name="5. Get Disk I/O Stats",
        method="GET",
        path="/api/v1/system/disk-io"
    )
    
    test_endpoint(
        name="6. Get Network Status",
        method="GET",
        path="/api/v1/network/status"
    )
    
    # SubscriptionUsage.jsx endpoints
    print("\n" + "="*80)
    print("SUBSCRIPTIONUSAGE.JSX ENDPOINTS")
    print("="*80)
    
    test_endpoint(
        name="7. Get Current Usage",
        method="GET",
        path="/api/v1/usage/current"
    )
    
    test_endpoint(
        name="8. Get Usage History (30 days)",
        method="GET",
        path="/api/v1/usage/history?days=30"
    )
    
    test_endpoint(
        name="9. Export Usage (CSV)",
        method="GET",
        path="/api/v1/usage/export?period=month"
    )
    
    # Print summary
    print_summary()
    
    # Return exit code
    failed = sum(1 for r in RESULTS if not r['passed'])
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
