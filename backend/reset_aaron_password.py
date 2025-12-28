#!/usr/bin/env python3
"""
Reset password for a user in Keycloak realm.

Usage:
    Set environment variables before running:
    - KEYCLOAK_URL: Keycloak server URL
    - KEYCLOAK_REALM: Target realm
    - KEYCLOAK_ADMIN_USER: Admin username
    - KEYCLOAK_ADMIN_PASSWORD: Admin password
    - TARGET_USER_ID: User ID to reset password for
    - NEW_PASSWORD: New password to set
"""

import asyncio
import httpx
import os

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")
TARGET_USER_ID = os.getenv("TARGET_USER_ID", "")
NEW_PASSWORD = os.getenv("NEW_PASSWORD", "")

async def get_admin_token():
    """Get admin token from Keycloak"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "username": KEYCLOAK_ADMIN_USER,
                "password": KEYCLOAK_ADMIN_PASSWORD,
                "grant_type": "password",
                "client_id": "admin-cli"
            },
            timeout=10.0
        )

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Failed to get token: {response.status_code}")
            print(f"Response: {response.text}")
            return None

async def reset_password(user_id, password, token):
    """Reset user password"""
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.put(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/reset-password",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "type": "password",
                "value": password,
                "temporary": False
            },
            timeout=10.0
        )

        return response.status_code == 204

async def main():
    # Validate required environment variables
    if not KEYCLOAK_ADMIN_PASSWORD:
        print("Error: KEYCLOAK_ADMIN_PASSWORD environment variable is required", flush=True)
        return
    if not TARGET_USER_ID:
        print("Error: TARGET_USER_ID environment variable is required", flush=True)
        return
    if not NEW_PASSWORD:
        print("Error: NEW_PASSWORD environment variable is required", flush=True)
        return

    print(f"Resetting password for user ID: {TARGET_USER_ID}...", flush=True)

    # Get admin token
    print("Getting admin token...", flush=True)
    token = await get_admin_token()

    if not token:
        print("Failed to authenticate as admin", flush=True)
        return

    print("Admin token obtained", flush=True)

    # Reset password
    print("Resetting password...", flush=True)
    success = await reset_password(TARGET_USER_ID, NEW_PASSWORD, token)

    if success:
        print("\n" + "="*60, flush=True)
        print("PASSWORD RESET SUCCESSFUL!", flush=True)
        print("="*60, flush=True)
        print(f"User ID: {TARGET_USER_ID}", flush=True)
        print("Password has been updated.", flush=True)
    else:
        print("Failed to reset password", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
