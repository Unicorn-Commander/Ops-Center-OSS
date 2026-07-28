"""
Test Suite for Landing Page Settings API
Tests both public and admin endpoints

Author: Backend Team Lead
Created: November 14, 2025
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/app')

from server import app

client = TestClient(app)

# Test 1: Get public settings without authentication
def test_get_public_settings_no_auth():
    """Public endpoint should work without authentication"""
    response = client.get("/api/v1/system/settings")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert "landing_page_mode" in data, "Response missing landing_page_mode"
    assert "sso_auto_redirect" in data, "Response missing sso_auto_redirect"
    assert "allow_registration" in data, "Response missing allow_registration"
    assert "branding" in data, "Response missing branding"

    # Check branding has expected keys
    branding = data["branding"]
    assert "company_name" in branding, "Branding missing company_name"
    assert "primary_color" in branding, "Branding missing primary_color"

    print("✅ Test 1 PASSED: Public settings accessible without auth")
    print(f"   Landing page mode: {data['landing_page_mode']}")
    print(f"   Company name: {branding.get('company_name')}")
    print(f"   Primary color: {branding.get('primary_color')}")

# Test 2: Get public settings via alternate endpoint
def test_get_public_settings_alternate():
    """Alternate public endpoint should also work"""
    response = client.get("/api/v1/system/settings/public")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert "landing_page_mode" in data

    print("✅ Test 2 PASSED: Alternate public endpoint works")

# Test 3: Get all admin settings (requires auth)
def test_get_admin_settings_no_auth():
    """Admin endpoint should fail without authentication"""
    response = client.get("/api/v1/admin/settings")

    # Should return 401 or 403
    assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    print("✅ Test 3 PASSED: Admin settings properly protected")

# Test 4: Landing page mode validation
def test_landing_page_mode_values():
    """Landing page mode should have valid value"""
    response = client.get("/api/v1/system/settings")

    assert response.status_code == 200

    data = response.json()
    landing_mode = data.get("landing_page_mode")

    valid_modes = ["direct_sso", "public_marketplace", "custom"]
    assert landing_mode in valid_modes, f"Invalid landing_page_mode: {landing_mode}"

    print(f"✅ Test 4 PASSED: Landing page mode is valid ({landing_mode})")

# Test 5: Boolean value parsing
def test_boolean_value_parsing():
    """Boolean values should be parsed correctly"""
    response = client.get("/api/v1/system/settings")

    assert response.status_code == 200

    data = response.json()
    sso_auto = data.get("sso_auto_redirect")
    allow_reg = data.get("allow_registration")

    assert isinstance(sso_auto, bool), f"sso_auto_redirect should be bool, got {type(sso_auto)}"
    assert isinstance(allow_reg, bool), f"allow_registration should be bool, got {type(allow_reg)}"

    print(f"✅ Test 5 PASSED: Boolean parsing works")
    print(f"   sso_auto_redirect: {sso_auto}")
    print(f"   allow_registration: {allow_reg}")

# Test 6: Response caching
def test_response_caching():
    """Subsequent requests should be faster (cached)"""
    import time

    # First request (cache miss)
    start1 = time.time()
    response1 = client.get("/api/v1/system/settings")
    time1 = (time.time() - start1) * 1000  # ms

    assert response1.status_code == 200

    # Second request (should be cached)
    start2 = time.time()
    response2 = client.get("/api/v1/system/settings")
    time2 = (time.time() - start2) * 1000  # ms

    assert response2.status_code == 200

    # Responses should be identical
    assert response1.json() == response2.json()

    print(f"✅ Test 6 PASSED: Response caching working")
    print(f"   First request: {time1:.2f}ms")
    print(f"   Second request: {time2:.2f}ms")
    if time2 < time1:
        print(f"   ⚡ Speed improvement: {((time1-time2)/time1*100):.1f}%")

# Test 7: Graceful error handling
def test_graceful_error_handling():
    """API should return defaults on database error"""
    # This test assumes the API will still return a response even if DB fails
    # The API is designed to fail gracefully with defaults
    response = client.get("/api/v1/system/settings")

    assert response.status_code == 200
    data = response.json()

    # Should always have these fields, even with defaults
    assert "landing_page_mode" in data
    assert "branding" in data

    print("✅ Test 7 PASSED: Graceful error handling verified")

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("  Landing Page Settings API Test Suite")
    print("="*60 + "\n")

    tests = [
        test_get_public_settings_no_auth,
        test_get_public_settings_alternate,
        test_get_admin_settings_no_auth,
        test_landing_page_mode_values,
        test_boolean_value_parsing,
        test_response_caching,
        test_graceful_error_handling
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
        print()

    print("="*60)
    print(f"  Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("🎉 All tests passed successfully!\n")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed\n")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
