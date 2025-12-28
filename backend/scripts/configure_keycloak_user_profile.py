#!/usr/bin/env python3
"""
Keycloak User Profile Configuration Script

Configures custom user attributes in Keycloak User Profile to ensure persistence
across sessions. Requires Keycloak 26.0+ with User Profile feature enabled.

Custom Attributes:
1. subscription_tier - User's subscription level
2. subscription_status - Account status
3. api_calls_limit - API call quota
4. api_calls_used - Current usage
5. api_calls_reset_date - When quota resets

Usage:
    python3 configure_keycloak_user_profile.py

Author: Ops-Center DevOps Team
Date: November 29, 2025
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime

# Keycloak Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ops-center")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "change-me")

# User Profile Attribute Configuration
USER_ATTRIBUTES = [
    {
        "name": "subscription_tier",
        "displayName": "Subscription Tier",
        "required": False,
        "readOnly": False,
        "validators": {
            "options": {
                "options": ["trial", "free", "starter", "professional", "enterprise",
                           "vip_founder", "founder_friend", "byok", "managed"]
            }
        },
        "annotations": {
            "description": "User's subscription tier level",
            "userEditable": "false",
            "adminEditable": "true"
        },
        "permissions": {
            "view": ["admin", "user"],
            "edit": ["admin"]
        }
    },
    {
        "name": "subscription_status",
        "displayName": "Subscription Status",
        "required": False,
        "readOnly": False,
        "validators": {
            "options": {
                "options": ["active", "inactive", "suspended", "cancelled", "pending"]
            }
        },
        "annotations": {
            "description": "Current subscription account status",
            "userEditable": "false",
            "adminEditable": "true"
        },
        "permissions": {
            "view": ["admin", "user"],
            "edit": ["admin"]
        }
    },
    {
        "name": "api_calls_limit",
        "displayName": "API Calls Limit",
        "required": False,
        "readOnly": False,
        "validators": {
            "integer": {
                "min": 0,
                "max": 1000000
            }
        },
        "annotations": {
            "description": "Maximum API calls per billing cycle",
            "userEditable": "false",
            "adminEditable": "true"
        },
        "permissions": {
            "view": ["admin", "user"],
            "edit": ["admin"]
        }
    },
    {
        "name": "api_calls_used",
        "displayName": "API Calls Used",
        "required": False,
        "readOnly": False,
        "validators": {
            "integer": {
                "min": 0,
                "max": 1000000
            }
        },
        "annotations": {
            "description": "Current API call usage in billing cycle",
            "userEditable": "false",
            "adminEditable": "true"
        },
        "permissions": {
            "view": ["admin", "user"],
            "edit": ["admin"]
        }
    },
    {
        "name": "api_calls_reset_date",
        "displayName": "API Calls Reset Date",
        "required": False,
        "readOnly": False,
        "annotations": {
            "description": "Date when API call quota resets (ISO 8601 format)",
            "userEditable": "false",
            "adminEditable": "true"
        },
        "permissions": {
            "view": ["admin", "user"],
            "edit": ["admin"]
        }
    }
]


async def get_admin_token() -> str:
    """Get Keycloak admin access token"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": KEYCLOAK_ADMIN_USER,
                    "password": KEYCLOAK_ADMIN_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )

            if response.status_code == 200:
                token_data = response.json()
                print("✓ Successfully obtained Keycloak admin token")
                return token_data["access_token"]
            else:
                print(f"✗ Failed to get admin token: {response.status_code}")
                print(f"  Response: {response.text}")
                sys.exit(1)

    except Exception as e:
        print(f"✗ Error getting admin token: {e}")
        sys.exit(1)


async def check_user_profile_enabled(token: str) -> bool:
    """Check if User Profile feature is enabled"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Check if realm has userProfileEnabled attribute
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                realm_data = response.json()
                attributes = realm_data.get("attributes", {})
                enabled = attributes.get("userProfileEnabled", "false") == "true"

                if enabled:
                    print("✓ User Profile feature is enabled")
                else:
                    print("✗ User Profile feature is NOT enabled")
                    print("  Attempting to enable...")
                    return await enable_user_profile(token)

                return enabled
            else:
                print(f"✗ Failed to check User Profile status: {response.status_code}")
                return False

    except Exception as e:
        print(f"✗ Error checking User Profile: {e}")
        return False


async def enable_user_profile(token: str) -> bool:
    """Enable User Profile feature for realm"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Update realm to enable User Profile
            response = await client.put(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "attributes": {
                        "userProfileEnabled": "true"
                    }
                },
                timeout=10.0
            )

            if response.status_code == 204:
                print("✓ User Profile feature enabled successfully")
                return True
            else:
                print(f"✗ Failed to enable User Profile: {response.status_code}")
                print(f"  Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ Error enabling User Profile: {e}")
        return False


async def get_user_profile_config(token: str) -> dict:
    """Get current User Profile configuration"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/profile",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                print("✓ Retrieved User Profile configuration")
                return response.json()
            else:
                print(f"⚠ User Profile API not available (status {response.status_code})")
                print(f"  This may be expected for older Keycloak versions")
                return {}

    except Exception as e:
        print(f"⚠ User Profile endpoint not accessible: {e}")
        return {}


async def configure_user_profile_attribute(token: str, attribute: dict) -> bool:
    """Configure a single user attribute in User Profile"""
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Try to update User Profile via API
            # Note: This endpoint may not be available in all Keycloak versions
            response = await client.post(
                f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/profile/attributes",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=attribute,
                timeout=10.0
            )

            if response.status_code in [200, 201, 204]:
                print(f"✓ Configured attribute: {attribute['name']}")
                return True
            elif response.status_code == 404:
                print(f"⚠ User Profile API endpoint not available")
                print(f"  Manual configuration required via Web UI")
                return False
            else:
                print(f"✗ Failed to configure {attribute['name']}: {response.status_code}")
                print(f"  Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ Error configuring attribute {attribute['name']}: {e}")
        return False


async def verify_configuration() -> dict:
    """Verify User Profile configuration is correct"""
    print("\n" + "="*80)
    print("KEYCLOAK USER PROFILE CONFIGURATION VERIFICATION")
    print("="*80 + "\n")

    # Get admin token
    token = await get_admin_token()

    # Check if User Profile is enabled
    print("\n1. Checking User Profile Status...")
    profile_enabled = await check_user_profile_enabled(token)

    # Get current configuration
    print("\n2. Retrieving User Profile Configuration...")
    current_config = await get_user_profile_config(token)

    # Try to configure attributes via API
    print("\n3. Attempting to Configure Attributes via API...")
    api_configured = False
    for attribute in USER_ATTRIBUTES:
        result = await configure_user_profile_attribute(token, attribute)
        api_configured = api_configured or result

    # Verify attributes exist on a test user
    print("\n4. Verifying Attributes on Test User...")
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={"Authorization": f"Bearer {token}"},
            params={"max": 1},
            timeout=10.0
        )

        if response.status_code == 200:
            users = response.json()
            if users:
                user = users[0]
                user_attrs = user.get("attributes", {})

                print(f"\n  Test User: {user.get('username')}")
                print(f"  Attributes found:")
                for attr in USER_ATTRIBUTES:
                    attr_name = attr["name"]
                    has_attr = attr_name in user_attrs
                    status = "✓" if has_attr else "✗"
                    value = user_attrs.get(attr_name, ["(not set)"])[0] if has_attr else "(not set)"
                    print(f"    {status} {attr_name}: {value}")

    # Generate summary
    return {
        "profile_enabled": profile_enabled,
        "api_configured": api_configured,
        "current_config": current_config,
        "timestamp": datetime.utcnow().isoformat()
    }


async def main():
    """Main configuration function"""
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║            Keycloak User Profile Configuration Utility                     ║
║                                                                            ║
║  This script configures custom user attributes in Keycloak User Profile   ║
║  to ensure persistence across sessions.                                   ║
║                                                                            ║
║  Target Realm: {KEYCLOAK_REALM}                                                ║
║  Keycloak URL: {KEYCLOAK_URL}                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Run verification
    result = await verify_configuration()

    # Print summary
    print("\n" + "="*80)
    print("CONFIGURATION SUMMARY")
    print("="*80)
    print(f"User Profile Enabled: {'✓ Yes' if result['profile_enabled'] else '✗ No'}")
    print(f"API Configuration: {'✓ Successful' if result['api_configured'] else '⚠ Manual Required'}")
    print(f"Timestamp: {result['timestamp']}")

    # Print next steps
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)

    if not result['api_configured']:
        print("""
⚠ MANUAL CONFIGURATION REQUIRED

The User Profile API is not available or configuration failed.
Please configure manually via Keycloak Admin Console:

1. Login to: <YOUR_KEYCLOAK_URL>/admin/<YOUR_REALM>/console
   Username: admin
   Password: <KEYCLOAK_ADMIN_PASSWORD from environment>

2. Navigate to: Realm Settings → User Profile

3. For each attribute below, click "Add attribute":

   a) subscription_tier
      - Display Name: Subscription Tier
      - Validators: Options (trial, free, starter, professional, enterprise,
                            vip_founder, founder_friend, byok, managed)
      - Permissions: View: user, admin | Edit: admin

   b) subscription_status
      - Display Name: Subscription Status
      - Validators: Options (active, inactive, suspended, cancelled, pending)
      - Permissions: View: user, admin | Edit: admin

   c) api_calls_limit
      - Display Name: API Calls Limit
      - Validators: Integer (min: 0, max: 1000000)
      - Permissions: View: user, admin | Edit: admin

   d) api_calls_used
      - Display Name: API Calls Used
      - Validators: Integer (min: 0, max: 1000000)
      - Permissions: View: user, admin | Edit: admin

   e) api_calls_reset_date
      - Display Name: API Calls Reset Date
      - Validators: None (stores ISO 8601 date string)
      - Permissions: View: user, admin | Edit: admin

4. Click "Save" after adding all attributes

5. Run attribute population script:
   docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py

6. Verify attributes persist across user login/logout
        """)
    else:
        print("""
✓ CONFIGURATION COMPLETE

User Profile attributes have been configured via API.

Next Steps:
1. Run attribute population script:
   docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py

2. Verify attributes persist:
   - Login to Ops-Center dashboard
   - Check User Management metrics
   - Logout and login again
   - Verify metrics still show correct values

3. If metrics show 0 after logout, manual Web UI configuration may be required
   (See manual configuration steps above)
        """)

    print("\n" + "="*80)
    print(f"Configuration completed at: {datetime.utcnow().isoformat()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
