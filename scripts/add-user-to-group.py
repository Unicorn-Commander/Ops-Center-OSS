#!/usr/bin/env python3
"""
Add a user to a Keycloak group

Usage:
    python3 scripts/add-user-to-group.py <username> <groupname>

Examples:
    python3 scripts/add-user-to-group.py aaron uc1-admins
    python3 scripts/add-user-to-group.py john uc1-users
"""
import httpx
import sys

KEYCLOAK_URL = "https://auth.unicorncommander.ai"
REALM = "uchub"
ADMIN_USER = "admin"
ADMIN_PASS = "your-admin-password"


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


def find_group(token, groupname):
    """Find group by name"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
        headers=headers,
        params={"search": groupname},
        timeout=30.0
    )
    response.raise_for_status()
    groups = response.json()
    return next((g for g in groups if g["name"] == groupname), None)


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


def add_user_to_group(token, user_id, group_id):
    """Add user to group"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.put(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/groups/{group_id}",
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 add-user-to-group.py <username> <groupname>")
        print()
        print("Examples:")
        print("  python3 add-user-to-group.py aaron uc1-admins")
        print("  python3 add-user-to-group.py john uc1-users")
        print()
        print("Available groups:")
        print("  - uc1-admins       (Full system access)")
        print("  - uc1-power-users  (Advanced features)")
        print("  - uc1-users        (Standard access)")
        print("  - uc1-viewers      (Read-only access)")
        sys.exit(1)

    username = sys.argv[1]
    groupname = sys.argv[2]

    print("=" * 70)
    print("Add User to Keycloak Group")
    print("=" * 70)
    print()
    print(f"User: {username}")
    print(f"Group: {groupname}")
    print()

    try:
        # Authenticate
        print("→ Authenticating...")
        token = get_admin_token()
        print("  ✓ Authenticated")

        # Find user
        print(f"→ Looking up user '{username}'...")
        user = find_user(token, username)
        if not user:
            print(f"  ✗ User '{username}' not found in realm '{REALM}'")
            sys.exit(1)
        print(f"  ✓ Found user: {user['username']} ({user.get('email', 'no email')})")

        # Find group
        print(f"→ Looking up group '{groupname}'...")
        group = find_group(token, groupname)
        if not group:
            print(f"  ✗ Group '{groupname}' not found")
            print()
            print("Available groups:")
            print("  - uc1-admins")
            print("  - uc1-power-users")
            print("  - uc1-users")
            print("  - uc1-viewers")
            sys.exit(1)
        print(f"  ✓ Found group: {group['name']}")

        # Check if user is already in group
        print(f"→ Checking user's current groups...")
        current_groups = get_user_groups(token, user["id"])
        if any(g["id"] == group["id"] for g in current_groups):
            print(f"  ℹ User '{username}' is already in group '{groupname}'")
            print()
            print("Current groups:")
            for g in current_groups:
                print(f"  - {g['name']}")
            sys.exit(0)

        # Add user to group
        print(f"→ Adding user to group...")
        add_user_to_group(token, user["id"], group["id"])
        print(f"  ✓ User '{username}' added to group '{groupname}'")

        # Verify
        print(f"→ Verifying...")
        updated_groups = get_user_groups(token, user["id"])
        print(f"  ✓ User now in {len(updated_groups)} groups:")
        for g in updated_groups:
            print(f"    - {g['name']}")

        print()
        print("=" * 70)
        print("✓ Success!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. User should logout and login again")
        print("2. Check ops-center logs for role mapping")
        print("3. Verify user can access appropriate features")
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
