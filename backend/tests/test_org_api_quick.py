#!/usr/bin/env python3
"""
Quick verification test for Organization API
Tests that all endpoints are properly defined and callable
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_org_api_imports():
    """Test that org_api can be imported"""
    try:
        from org_api import router
        print("✅ org_api.router imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import org_api: {e}")
        return False


def test_org_manager_integration():
    """Test that org_manager is properly integrated"""
    try:
        from org_manager import org_manager, Organization, OrgUser
        print("✅ org_manager classes imported successfully")

        # Test creating an organization
        org_id = org_manager.create_organization("Test Org", "professional")
        print(f"✅ Created test organization: {org_id}")

        # Test retrieving organization
        org = org_manager.get_org(org_id)
        if org:
            print(f"✅ Retrieved organization: {org.name}")
        else:
            print(f"❌ Failed to retrieve organization")
            return False

        # Test adding user
        success = org_manager.add_user_to_org(org_id, "test@example.com", "owner")
        if success:
            print("✅ Added user to organization")
        else:
            print("❌ Failed to add user")
            return False

        # Test getting members
        members = org_manager.get_org_users(org_id)
        if members and len(members) == 1:
            print(f"✅ Retrieved {len(members)} member(s)")
        else:
            print(f"❌ Expected 1 member, got {len(members)}")
            return False

        # Cleanup
        org_manager.remove_user_from_org(org_id, "test@example.com")
        print("✅ Cleaned up test data")

        return True

    except Exception as e:
        print(f"❌ org_manager integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_definitions():
    """Test that all 9 endpoints are defined"""
    try:
        from org_api import router

        # Get all routes
        routes = router.routes

        print(f"\n📋 Found {len(routes)} endpoint(s) in org_api:")

        expected_endpoints = [
            ("GET", "/api/v1/org/roles"),
            ("GET", "/api/v1/org/{org_id}/members"),
            ("POST", "/api/v1/org/{org_id}/members"),
            ("PUT", "/api/v1/org/{org_id}/members/{user_id}/role"),
            ("DELETE", "/api/v1/org/{org_id}/members/{user_id}"),
            ("GET", "/api/v1/org/{org_id}/stats"),
            ("GET", "/api/v1/org/{org_id}/billing"),
            ("GET", "/api/v1/org/{org_id}/settings"),
            ("PUT", "/api/v1/org/{org_id}/settings"),
        ]

        found_endpoints = []
        for route in routes:
            method = list(route.methods)[0] if route.methods else "UNKNOWN"
            path = route.path
            found_endpoints.append((method, path))
            print(f"   {method:7} {path}")

        # Check if all expected endpoints are present
        missing = []
        for expected in expected_endpoints:
            if expected not in found_endpoints:
                missing.append(expected)

        if missing:
            print(f"\n❌ Missing {len(missing)} endpoint(s):")
            for method, path in missing:
                print(f"   {method:7} {path}")
            return False
        else:
            print(f"\n✅ All 9 expected endpoints are defined!")
            return True

    except Exception as e:
        print(f"❌ Failed to check endpoint definitions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_models():
    """Test that all Pydantic models are valid"""
    try:
        from org_api import (
            OrganizationMemberAdd,
            OrganizationMemberRoleUpdate,
            OrganizationSettingsUpdate
        )

        print("\n📦 Testing Pydantic models:")

        # Test OrganizationMemberAdd
        member_add = OrganizationMemberAdd(user_id="test@example.com", role="member")
        print(f"   ✅ OrganizationMemberAdd: {member_add.dict()}")

        # Test OrganizationMemberRoleUpdate
        role_update = OrganizationMemberRoleUpdate(role="billing_admin")
        print(f"   ✅ OrganizationMemberRoleUpdate: {role_update.dict()}")

        # Test OrganizationSettingsUpdate
        settings_update = OrganizationSettingsUpdate(settings={"key": "value"})
        print(f"   ✅ OrganizationSettingsUpdate: {settings_update.dict()}")

        print("✅ All Pydantic models are valid!")
        return True

    except Exception as e:
        print(f"❌ Pydantic model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Organization API Quick Verification Test")
    print("=" * 60)

    tests = [
        ("Import Test", test_org_api_imports),
        ("OrgManager Integration", test_org_manager_integration),
        ("Endpoint Definitions", test_endpoint_definitions),
        ("Pydantic Models", test_pydantic_models),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! org_api.py is ready for integration.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix before integration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
