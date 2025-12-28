#!/usr/bin/env python3
"""
Verify User Attributes Persistence

Tests that custom user attributes persist correctly across sessions.
Creates a test user, populates attributes, and verifies they remain after logout/login.

Usage:
    python3 verify_user_attributes.py

Author: Ops-Center DevOps Team
Date: November 29, 2025
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ops-center")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "change-me")

# Test user configuration
TEST_USER_EMAIL = "test-persistence@example.com"
TEST_USER_USERNAME = "test-persistence"
TEST_USER_PASSWORD = "TestPassword123!"

# Expected attributes
EXPECTED_ATTRIBUTES = {
    "subscription_tier": "professional",
    "subscription_status": "active",
    "api_calls_limit": "10000",
    "api_calls_used": "150",
    "api_calls_reset_date": datetime.utcnow().date().isoformat()
}


async def get_admin_token() -> str:
    """Get admin access token"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": "admin",
                "password": KEYCLOAK_ADMIN_PASSWORD
            },
            timeout=10.0
        )

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Failed to get admin token: {response.status_code}")


async def delete_test_user_if_exists(token: str):
    """Delete test user if it already exists"""
    async with httpx.AsyncClient(verify=False) as client:
        # Check if user exists
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={"Authorization": f"Bearer {token}"},
            params={"email": TEST_USER_EMAIL, "exact": "true"},
            timeout=10.0
        )

        if response.status_code == 200:
            users = response.json()
            if users:
                user_id = users[0]["id"]
                print(f"  Deleting existing test user: {user_id}")

                # Delete user
                delete_response = await client.delete(
                    f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )

                if delete_response.status_code == 204:
                    print(f"  ✓ Test user deleted")
                else:
                    print(f"  ✗ Failed to delete test user: {delete_response.status_code}")


async def create_test_user(token: str) -> str:
    """Create test user with attributes"""
    async with httpx.AsyncClient(verify=False) as client:
        # Create user
        user_data = {
            "email": TEST_USER_EMAIL,
            "username": TEST_USER_USERNAME,
            "enabled": True,
            "emailVerified": True,
            "firstName": "Test",
            "lastName": "User",
            "attributes": {
                k: [v] for k, v in EXPECTED_ATTRIBUTES.items()
            }
        }

        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=user_data,
            timeout=10.0
        )

        if response.status_code == 201:
            # Extract user ID from Location header
            location = response.headers.get("Location", "")
            user_id = location.split("/")[-1]
            print(f"  ✓ Test user created: {user_id}")

            # Set password
            password_response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/reset-password",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "password",
                    "value": TEST_USER_PASSWORD,
                    "temporary": False
                },
                timeout=10.0
            )

            if password_response.status_code == 204:
                print(f"  ✓ Password set")

            return user_id
        else:
            raise Exception(f"Failed to create user: {response.status_code} - {response.text}")


async def get_user_attributes(token: str, user_id: str) -> dict:
    """Get user's attributes"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )

        if response.status_code == 200:
            user_data = response.json()
            return user_data.get("attributes", {})
        else:
            raise Exception(f"Failed to get user: {response.status_code}")


async def test_user_login(user_id: str) -> tuple[bool, str]:
    """Test user login and token retrieval"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "ops-center",
                "username": TEST_USER_USERNAME,
                "password": TEST_USER_PASSWORD
            },
            timeout=10.0
        )

        if response.status_code == 200:
            token_data = response.json()
            user_token = token_data.get("access_token")
            return True, user_token
        else:
            return False, f"Login failed: {response.status_code} - {response.text}"


async def logout_user_sessions(admin_token: str, user_id: str):
    """Logout all user sessions"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10.0
        )

        if response.status_code == 204:
            print(f"  ✓ User sessions logged out")
        else:
            print(f"  ⚠ Logout status: {response.status_code}")


async def verify_attributes(token: str, user_id: str, step: str) -> dict:
    """Verify user attributes match expected values"""
    attrs = await get_user_attributes(token, user_id)

    print(f"\n  Attributes {step}:")
    results = {}

    for key, expected_value in EXPECTED_ATTRIBUTES.items():
        actual_values = attrs.get(key, [])
        actual_value = actual_values[0] if actual_values else None
        matches = actual_value == expected_value

        status = "✓" if matches else "✗"
        print(f"    {status} {key}: {actual_value} {'(expected: ' + expected_value + ')' if not matches else ''}")

        results[key] = {
            "expected": expected_value,
            "actual": actual_value,
            "matches": matches
        }

    return results


async def main():
    """Main verification function"""
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         User Attributes Persistence Verification                           ║
║                                                                            ║
║  This script tests that custom user attributes persist across sessions     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Step 1: Get admin token
        print("\n1. Getting admin token...")
        admin_token = await get_admin_token()
        print("  ✓ Admin token obtained")

        # Step 2: Clean up existing test user
        print("\n2. Cleaning up existing test user (if any)...")
        await delete_test_user_if_exists(admin_token)

        # Step 3: Create test user
        print("\n3. Creating test user with attributes...")
        user_id = await create_test_user(admin_token)

        # Step 4: Verify attributes immediately after creation
        print("\n4. Verifying attributes after creation...")
        results_after_creation = await verify_attributes(admin_token, user_id, "after creation")

        # Step 5: Test user login
        print("\n5. Testing user login...")
        login_success, user_token = await test_user_login(user_id)
        if login_success:
            print(f"  ✓ User login successful")
        else:
            print(f"  ✗ User login failed: {user_token}")

        # Step 6: Logout user
        print("\n6. Logging out user sessions...")
        await logout_user_sessions(admin_token, user_id)

        # Step 7: Wait a bit
        print("\n7. Waiting 2 seconds...")
        await asyncio.sleep(2)

        # Step 8: Verify attributes persist after logout
        print("\n8. Verifying attributes after logout...")
        results_after_logout = await verify_attributes(admin_token, user_id, "after logout")

        # Step 9: Login again
        print("\n9. Testing re-login...")
        relogin_success, _ = await test_user_login(user_id)
        if relogin_success:
            print(f"  ✓ User re-login successful")
        else:
            print(f"  ✗ User re-login failed")

        # Step 10: Final verification
        print("\n10. Final attribute verification...")
        results_after_relogin = await verify_attributes(admin_token, user_id, "after re-login")

        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)

        all_matched_after_creation = all(r["matches"] for r in results_after_creation.values())
        all_matched_after_logout = all(r["matches"] for r in results_after_logout.values())
        all_matched_after_relogin = all(r["matches"] for r in results_after_relogin.values())

        print(f"\nAfter Creation: {'✓ All attributes correct' if all_matched_after_creation else '✗ Some attributes incorrect'}")
        print(f"After Logout:   {'✓ All attributes persist' if all_matched_after_logout else '✗ Some attributes lost'}")
        print(f"After Re-login: {'✓ All attributes persist' if all_matched_after_relogin else '✗ Some attributes lost'}")

        if all_matched_after_creation and all_matched_after_logout and all_matched_after_relogin:
            print("\n" + "="*80)
            print("✓ SUCCESS: All attributes persist correctly across sessions!")
            print("="*80)
            print("\nUser Profile is configured correctly. Attributes are persistent.")
        else:
            print("\n" + "="*80)
            print("✗ FAILURE: Attributes not persisting correctly")
            print("="*80)
            print("\nUser Profile may need manual configuration via Keycloak Admin Console.")
            print("See: https://auth.your-domain.com/admin/uchub/console")
            print("Navigate to: Realm Settings → User Profile")

        # Cleanup
        print("\n11. Cleaning up test user...")
        await delete_test_user_if_exists(admin_token)

        print("\n" + "="*80)
        print(f"Verification completed at: {datetime.utcnow().isoformat()}")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
