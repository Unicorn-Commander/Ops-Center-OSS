#!/usr/bin/env python3
"""
List groups for a Keycloak user

Environment Variables:
    KEYCLOAK_URL - Keycloak server URL (default: http://localhost:8080)
    KEYCLOAK_REALM - Keycloak realm (default: uchub)
    KEYCLOAK_ADMIN_USER - Admin username (default: admin)
    KEYCLOAK_ADMIN_PASSWORD - Admin password (required)

Usage:
    KEYCLOAK_ADMIN_PASSWORD=secret python3 scripts/list-user-groups.py <username>

Example:
    python3 scripts/list-user-groups.py testuser
"""
import httpx
import sys
import os

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "uchub")
ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "change-me")


def get_admin_token():
    """Get admin access token"""
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


def find_user(token, username):
    """Find user by username"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
        headers=headers,
        params={"username": username, "exact": "true"},
        timeout=30.0
    )
    response.raise_for_status()
    users = response.json()
    return users[0] if users else None


def get_user_groups(token, user_id):
    """Get user's current groups"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/groups",
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def get_user_roles(token, user_id):
    """Get user's realm roles"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/realm",
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 list-user-groups.py <username>")
        print()
        print("Example:")
        print("  python3 list-user-groups.py aaron")
        sys.exit(1)

    username = sys.argv[1]

    print("=" * 70)
    print("Keycloak User Groups & Roles")
    print("=" * 70)
    print()

    try:
        # Authenticate
        print("→ Authenticating...")
        token = get_admin_token()

        # Find user
        print(f"→ Looking up user '{username}'...")
        user = find_user(token, username)
        if not user:
            print(f"  ✗ User '{username}' not found in realm '{REALM}'")
            sys.exit(1)

        print()
        print(f"User: {user['username']}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"ID: {user['id']}")
        print(f"Enabled: {user.get('enabled', False)}")
        print()

        # Get groups
        print("→ Fetching groups...")
        groups = get_user_groups(token, user["id"])
        if groups:
            print(f"  ✓ User is in {len(groups)} group(s):")
            for group in groups:
                print(f"    • {group['name']} (path: {group['path']})")
        else:
            print("  ℹ User is not in any groups")

        print()

        # Get roles
        print("→ Fetching realm roles...")
        roles = get_user_roles(token, user["id"])
        if roles:
            print(f"  ✓ User has {len(roles)} realm role(s):")
            for role in roles:
                print(f"    • {role['name']}")
        else:
            print("  ℹ User has no realm roles")

        print()
        print("=" * 70)

        # Show expected ops-center role
        print()
        print("Expected Ops-Center Role Mapping:")
        if any(g['name'] in ['uc1-admins', '/uc1-admins'] for g in groups):
            print("  → admin (from uc1-admins group)")
        elif any(g['name'] in ['uc1-power-users', '/uc1-power-users'] for g in groups):
            print("  → power_user (from uc1-power-users group)")
        elif any(g['name'] in ['uc1-users', '/uc1-users'] for g in groups):
            print("  → user (from uc1-users group)")
        elif any(g['name'] in ['uc1-viewers', '/uc1-viewers'] for g in groups):
            print("  → viewer (from uc1-viewers group)")
        else:
            print("  → viewer (default - no UC-1 groups assigned)")

        print()

        return 0

    except httpx.HTTPStatusError as e:
        print(f"  ✗ HTTP Error: {e.response.status_code}")
        print(f"    Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
