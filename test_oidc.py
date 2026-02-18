#!/usr/bin/env python3
"""Test OIDC configuration and token exchange"""
import httpx
import asyncio
import os

KEYCLOAK_URL = "http://uchub-keycloak:8080"
KEYCLOAK_REALM = "uchub"
CLIENT_ID = "ops-center"
CLIENT_SECRET = "your-keycloak-client-secret"

async def test_oidc_discovery():
    """Test OIDC discovery endpoint"""
    print("=" * 60)
    print("Testing OIDC Discovery")
    print("=" * 60)

    discovery_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
    print(f"Discovery URL: {discovery_url}")

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(discovery_url)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                config = response.json()
                print(f"Issuer: {config.get('issuer')}")
                print(f"Authorization Endpoint: {config.get('authorization_endpoint')}")
                print(f"Token Endpoint: {config.get('token_endpoint')}")
                print(f"Userinfo Endpoint: {config.get('userinfo_endpoint')}")
                return config
            else:
                print(f"Error: {response.text}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

async def test_client_config():
    """Test if we can get client configuration"""
    print("\n" + "=" * 60)
    print("Testing Client Configuration")
    print("=" * 60)

    # First, get admin token
    token_url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

    async with httpx.AsyncClient(verify=False) as client:
        try:
            # Get admin token
            response = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": "your-admin-password"
                }
            )

            if response.status_code != 200:
                print(f"Failed to get admin token: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            admin_token = response.json().get("access_token")
            print(f"Got admin token: {admin_token[:20]}...")

            # Get clients list
            clients_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients"
            response = await client.get(
                clients_url,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            if response.status_code != 200:
                print(f"Failed to get clients: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            clients = response.json()
            ops_center_client = None

            for c in clients:
                if c.get("clientId") == CLIENT_ID:
                    ops_center_client = c
                    break

            if ops_center_client:
                print(f"Found ops-center client!")
                print(f"Client ID (UUID): {ops_center_client.get('id')}")
                print(f"Enabled: {ops_center_client.get('enabled')}")
                print(f"Redirect URIs: {ops_center_client.get('redirectUris')}")
                print(f"Web Origins: {ops_center_client.get('webOrigins')}")
                print(f"Public Client: {ops_center_client.get('publicClient')}")
                print(f"Protocol: {ops_center_client.get('protocol')}")
                print(f"Standard Flow Enabled: {ops_center_client.get('standardFlowEnabled')}")
                print(f"Direct Access Grants Enabled: {ops_center_client.get('directAccessGrantsEnabled')}")

                return ops_center_client
            else:
                print(f"ops-center client NOT FOUND!")
                print(f"Available clients: {[c.get('clientId') for c in clients]}")
                return None

        except Exception as e:
            print(f"Exception: {e}")
            return None

async def test_token_exchange():
    """Test token exchange with a mock authorization code"""
    print("\n" + "=" * 60)
    print("Testing Token Exchange")
    print("=" * 60)

    # NOTE: This will fail because we don't have a real authorization code
    # But it will show us what error Keycloak returns

    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    redirect_uri = "https://unicorncommander.ai/auth/callback"

    print(f"Token URL: {token_url}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Client Secret: {CLIENT_SECRET[:10]}...")
    print(f"Redirect URI: {redirect_uri}")

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": "fake_code_for_testing",
                    "redirect_uri": redirect_uri,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET
                }
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                tokens = response.json()
                print(f"Access Token: {tokens.get('access_token', 'None')[:20]}...")
                return tokens
            else:
                # Expected to fail, but let's see the error
                try:
                    error = response.json()
                    print(f"Error: {error.get('error')}")
                    print(f"Error Description: {error.get('error_description')}")
                except:
                    pass
                return None

        except Exception as e:
            print(f"Exception: {e}")
            return None

async def main():
    """Run all tests"""
    print("OIDC Authentication Testing")
    print("=" * 60)
    print()

    # Test 1: OIDC Discovery
    config = await test_oidc_discovery()

    # Test 2: Client Configuration
    client = await test_client_config()

    # Test 3: Token Exchange (will fail but shows error)
    await test_token_exchange()

    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
