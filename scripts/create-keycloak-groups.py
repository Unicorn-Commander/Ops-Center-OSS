#!/usr/bin/env python3
"""
Create UC-1 Pro role groups in Keycloak

This script creates the four UC-1 Pro role groups in Keycloak:
- uc1-admins
- uc1-power-users
- uc1-users
- uc1-viewers

Usage:
    python3 scripts/create-keycloak-groups.py
"""
import httpx
import sys

KEYCLOAK_URL = "https://auth.unicorncommander.ai"
REALM = "uchub"
ADMIN_USER = "admin"
ADMIN_PASS = "your-admin-password"

GROUPS = [
    {
        "name": "uc1-admins",
        "description": "UC-1 Pro Administrators - Full system access"
    },
    {
        "name": "uc1-power-users",
        "description": "UC-1 Pro Power Users - Advanced features and configuration"
    },
    {
        "name": "uc1-users",
        "description": "UC-1 Pro Standard Users - Core feature access"
    },
    {
        "name": "uc1-viewers",
        "description": "UC-1 Pro Viewers - Read-only access"
    }
]


def get_admin_token():
    """Get admin access token from Keycloak"""
    try:
        response = httpx.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": ADMIN_USER,
                "password": ADMIN_PASS
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except httpx.HTTPStatusError as e:
        print(f"✗ Authentication failed: {e.response.status_code}")
        print(f"  Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"✗ Error getting admin token: {e}")
        raise


def create_group(token, group_data):
    """Create a group in Keycloak"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Check if group exists
    try:
        response = httpx.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
            headers=headers,
            params={"search": group_data["name"]},
            timeout=30.0
        )
        response.raise_for_status()
        existing = response.json()

        # Check for exact name match
        if any(g["name"] == group_data["name"] for g in existing):
            print(f"  ✓ Group '{group_data['name']}' already exists")
            return False

    except Exception as e:
        print(f"  ✗ Error checking for existing group: {e}")
        return False

    # Create group
    try:
        response = httpx.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
            headers=headers,
            json={
                "name": group_data["name"],
                "attributes": {
                    "description": [group_data["description"]]
                }
            },
            timeout=30.0
        )
        response.raise_for_status()
        print(f"  ✓ Created group '{group_data['name']}'")
        return True

    except httpx.HTTPStatusError as e:
        print(f"  ✗ Failed to create group '{group_data['name']}': {e.response.status_code}")
        print(f"    Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"  ✗ Error creating group '{group_data['name']}': {e}")
        return False


def main():
    print("=" * 70)
    print("UC-1 Pro Keycloak Groups Setup")
    print("=" * 70)
    print()
    print(f"Keycloak URL: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}")
    print(f"Admin User: {ADMIN_USER}")
    print()

    try:
        # Get admin token
        print("→ Authenticating as admin...")
        token = get_admin_token()
        print("  ✓ Authentication successful")
        print()

        # Create groups
        print("→ Creating UC-1 Pro role groups...")
        created_count = 0
        for group in GROUPS:
            if create_group(token, group):
                created_count += 1

        print()
        print("=" * 70)
        print(f"✓ Complete! Created {created_count} new groups ({len(GROUPS) - created_count} already existed)")
        print("=" * 70)
        print()

        if created_count > 0:
            print("Next Steps:")
            print("1. Assign users to groups in Keycloak Admin UI")
            print("2. Configure group mapper for ops-center client")
            print("3. Test login with a user in uc1-admins group")
            print()
            print("Or use the add-user-to-group.py script:")
            print("  python3 scripts/add-user-to-group.py aaron uc1-admins")
            print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ Error: {e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
