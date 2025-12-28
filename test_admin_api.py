#!/usr/bin/env python3
"""
Test script for Admin User Management API endpoints

Tests all admin API endpoints to verify functionality.
Requires KEYCLOAK_ADMIN_PASSWORD environment variable.

Usage:
    export KEYCLOAK_ADMIN_PASSWORD="your-admin-password"
    python3 test_admin_api.py
"""

import asyncio
import sys
import os
from auth.keycloak_admin import KeycloakAdmin

async def test_keycloak_admin():
    """Test Keycloak Admin API functionality"""

    # Check for admin password
    admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
    if not admin_password:
        print("❌ KEYCLOAK_ADMIN_PASSWORD environment variable not set")
        print("\nPlease set it with:")
        print("  export KEYCLOAK_ADMIN_PASSWORD='your-password'")
        return False

    print("🔧 Testing Keycloak Admin API Integration")
    print("=" * 60)

    try:
        # Initialize admin client
        print("\n1️⃣  Initializing Keycloak Admin client...")
        admin = KeycloakAdmin(
            keycloak_url="https://auth.your-domain.com",
            realm="uchub",
            admin_username="admin",
            admin_password=admin_password
        )
        print("   ✅ Admin client initialized")

        # Test authentication
        print("\n2️⃣  Testing admin authentication...")
        token = await admin._get_admin_token()
        print(f"   ✅ Admin token obtained: {token[:20]}...")

        # Test listing users
        print("\n3️⃣  Testing user list...")
        users = await admin.list_users(max=5)
        print(f"   ✅ Retrieved {len(users)} users")
        if users:
            print(f"   First user: {users[0].get('username')} ({users[0].get('email')})")

        # Test getting user count
        print("\n4️⃣  Testing user count...")
        count = await admin.get_user_count()
        print(f"   ✅ Total users in realm: {count}")

        # Test getting roles
        print("\n5️⃣  Testing available roles...")
        roles = await admin.get_available_roles()
        print(f"   ✅ Retrieved {len(roles)} roles")
        if roles:
            role_names = [r.get('name') for r in roles[:5]]
            print(f"   Roles: {', '.join(role_names)}")

        # Test realm statistics
        print("\n6️⃣  Testing realm statistics...")
        stats = await admin.get_realm_stats()
        print(f"   ✅ Realm: {stats['realm']}")
        print(f"   Total users: {stats['total_users']}")
        print(f"   Enabled users: {stats['enabled_users']}")
        print(f"   Disabled users: {stats['disabled_users']}")
        print(f"   Verified emails: {stats['verified_emails']}")

        # Test user search
        print("\n7️⃣  Testing user search...")
        search_results = await admin.list_users(search="aaron")
        print(f"   ✅ Found {len(search_results)} users matching 'aaron'")

        # If test user exists, test additional features
        if users and len(users) > 0:
            test_user = users[0]
            user_id = test_user['id']

            print(f"\n8️⃣  Testing get user details for: {test_user.get('username')}")
            user_details = await admin.get_user(user_id)
            print(f"   ✅ Retrieved user: {user_details.get('username')}")

            print(f"\n9️⃣  Testing get user roles...")
            user_roles = await admin.get_user_roles(user_id)
            print(f"   ✅ User has {len(user_roles)} roles")

            print(f"\n🔟 Testing get user sessions...")
            sessions = await admin.get_user_sessions(user_id)
            print(f"   ✅ User has {len(sessions)} active sessions")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("\n📋 Summary:")
        print(f"   • Keycloak URL: https://auth.your-domain.com")
        print(f"   • Realm: uchub")
        print(f"   • Total users: {count}")
        print(f"   • Available roles: {len(roles)}")
        print("\n🎯 Admin API is ready to use!")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test that all API endpoints are properly defined"""
    print("\n\n🔍 Checking API Endpoint Definitions")
    print("=" * 60)

    from server import app

    admin_routes = [
        ("GET", "/api/v1/admin/users", "List users"),
        ("GET", "/api/v1/admin/users/{user_id}", "Get user details"),
        ("POST", "/api/v1/admin/users", "Create user"),
        ("PUT", "/api/v1/admin/users/{user_id}", "Update user"),
        ("DELETE", "/api/v1/admin/users/{user_id}", "Delete user"),
        ("POST", "/api/v1/admin/users/{user_id}/reset-password", "Reset password"),
        ("GET", "/api/v1/admin/users/{user_id}/roles", "Get user roles"),
        ("POST", "/api/v1/admin/users/{user_id}/roles", "Add role"),
        ("DELETE", "/api/v1/admin/users/{user_id}/roles/{role_name}", "Remove role"),
        ("GET", "/api/v1/admin/users/{user_id}/sessions", "Get sessions"),
        ("POST", "/api/v1/admin/users/{user_id}/logout", "Logout user"),
        ("GET", "/api/v1/admin/stats", "Get statistics"),
        ("GET", "/api/v1/admin/roles", "Get available roles"),
    ]

    found_count = 0
    for method, path, description in admin_routes:
        # Check if route exists
        route_found = False
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                if method in route.methods and route.path == path:
                    route_found = True
                    break

        if route_found:
            print(f"   ✅ {method:6} {path:50} - {description}")
            found_count += 1
        else:
            print(f"   ❌ {method:6} {path:50} - {description}")

    print("\n" + "=" * 60)
    print(f"✅ Found {found_count}/{len(admin_routes)} admin endpoints")

    return found_count == len(admin_routes)

async def main():
    """Run all tests"""
    print("\n🚀 UC-1 Pro Admin API Test Suite")
    print("=" * 60)

    # Test Keycloak Admin API
    admin_test_passed = await test_keycloak_admin()

    # Test API endpoints
    endpoints_test_passed = await test_api_endpoints()

    # Final summary
    print("\n\n📊 Test Summary")
    print("=" * 60)
    print(f"   Keycloak Admin API: {'✅ PASSED' if admin_test_passed else '❌ FAILED'}")
    print(f"   API Endpoints: {'✅ PASSED' if endpoints_test_passed else '❌ FAILED'}")

    if admin_test_passed and endpoints_test_passed:
        print("\n🎉 All tests passed! Admin API is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
