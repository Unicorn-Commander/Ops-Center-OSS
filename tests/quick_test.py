#!/usr/bin/env python3
"""Quick test to verify Keycloak connection"""

import sys
import os
import asyncio

# Set environment variables
os.environ['KEYCLOAK_URL'] = 'https://auth.your-domain.com'
os.environ['KEYCLOAK_REALM'] = 'uchub'
os.environ['KEYCLOAK_CLIENT_ID'] = 'admin-cli'
os.environ['KEYCLOAK_ADMIN_USERNAME'] = 'admin'
os.environ['KEYCLOAK_ADMIN_PASSWORD'] = 'your-test-password'

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from keycloak_integration import get_admin_token, get_all_users

async def main():
    print("Testing Keycloak connection...")
    print(f"URL: {os.getenv('KEYCLOAK_URL')}")
    print(f"Realm: {os.getenv('KEYCLOAK_REALM')}")
    print()

    try:
        print("1. Getting admin token...")
        token = await get_admin_token()
        print(f"   ✓ Token retrieved: {token[:50]}...")
        print()

        print("2. Fetching users...")
        users = await get_all_users()
        print(f"   ✓ Found {len(users)} users")

        if users:
            print(f"\n   First user:")
            print(f"   - Username: {users[0].get('username')}")
            print(f"   - Email: {users[0].get('email')}")
            print(f"   - Enabled: {users[0].get('enabled')}")

        print("\n✓ Keycloak connection successful!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
