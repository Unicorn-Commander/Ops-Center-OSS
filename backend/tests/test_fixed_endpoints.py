#!/usr/bin/env python3
"""
Test suite for fixed API endpoints in Services.jsx, System.jsx, and SubscriptionUsage.jsx
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8084"
RESULTS = []

def test_endpoint(name, method, path, expected_status=200, data=None, headers=None):
    """Test a single endpoint and record results"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Determine response type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            response_type = "JSON"
            try:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)[:500]}...")
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
        status_ok = response.status_code == expected_status
        has_content = len(response.text) > 0
        is_valid_json = response_type == "JSON" or response_type == "CSV"
        
        passed = status_ok and (has_content or response.status_code == 204)
        
        result = {
            "name": name,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "response_type": response_type,
            "passed": passed,
            "error": None if passed else f"Status: {response.status_code}, Expected: {expected_status}"
        }
        
        print(f"\nStatus Code: {response.status_code} (Expected: {expected_status})")
        print(f"Response Type: {response_type}")
        print(f"Result: {'✅ PASS' if passed else '❌ FAIL'}")
        
        RESULTS.append(result)
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {str(e)}")
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
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
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
            print(f"   Error: {result['error']}")
        print(f"\n{'='*80}\n")

def main():
    print(f"\n{'#'*80}")
    print("TESTING FIXED API ENDPOINTS")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'#'*80}\n")
    
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
        data={"action": "status"},  # Safe no-op action
        expected_status=200
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
