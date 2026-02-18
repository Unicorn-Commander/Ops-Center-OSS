#!/usr/bin/env python3
"""
Keycloak OIDC Client Setup Script for UC-1 Pro Operations Center

This script automatically configures the Ops Center OIDC client in Keycloak
using the Admin API. It is idempotent and can be run multiple times safely.

Requirements:
    - httpx library
    - Keycloak Admin credentials
    - Network access to Keycloak server

Usage:
    python setup-keycloak-client.py
"""

import sys
import json
import httpx
from pathlib import Path
from typing import Dict, Optional, Tuple


# Configuration
KEYCLOAK_URL = "https://auth.unicorncommander.ai"
REALM = "uchub"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your-admin-password"
CLIENT_ID = "ops-center"

# Client configuration
CLIENT_CONFIG = {
    "clientId": CLIENT_ID,
    "name": "UC-1 Pro Operations Center",
    "description": "Main operations and management console for UC-1 Pro platform",
    "enabled": True,
    "protocol": "openid-connect",
    "publicClient": False,
    "confidentialClient": True,
    "redirectUris": [
        "https://unicorncommander.ai/auth/callback",
        "http://localhost:8000/auth/callback"
    ],
    "webOrigins": [
        "https://unicorncommander.ai",
        "http://localhost:8000"
    ],
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": True,
    "implicitFlowEnabled": False,
    "serviceAccountsEnabled": False,
    "defaultClientScopes": ["openid", "email", "profile", "roles"],
    "attributes": {
        "post.logout.redirect.uris": "https://unicorncommander.ai+##http://localhost:8000"
    }
}

# Output file
ENV_FILE = Path("/home/deploy/Production/UC-1-Pro/services/ops-center/.env.keycloak")


class KeycloakAdmin:
    """Keycloak Admin API client"""

    def __init__(self, base_url: str, realm: str):
        self.base_url = base_url.rstrip('/')
        self.realm = realm
        self.client = httpx.Client(verify=True, timeout=30.0)
        self.access_token: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with Keycloak Admin API and get access token

        Args:
            username: Admin username
            password: Admin password

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get("access_token")
            return bool(self.access_token)

        except httpx.HTTPStatusError as e:
            print(f"✗ Authentication failed: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"✗ Network error during authentication: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during authentication: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_client(self, client_id: str) -> Optional[Dict]:
        """
        Get client by client_id

        Args:
            client_id: The client ID to search for

        Returns:
            Client data if found, None otherwise
        """
        try:
            response = self.client.get(
                f"{self.base_url}/admin/realms/{self.realm}/clients",
                headers=self._get_headers(),
                params={"clientId": client_id}
            )
            response.raise_for_status()

            clients = response.json()
            return clients[0] if clients else None

        except httpx.HTTPStatusError as e:
            print(f"✗ Error fetching client: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error fetching client: {e}")
            return None

    def create_client(self, config: Dict) -> Optional[str]:
        """
        Create a new client

        Args:
            config: Client configuration

        Returns:
            Client UUID if successful, None otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/admin/realms/{self.realm}/clients",
                headers=self._get_headers(),
                json=config
            )
            response.raise_for_status()

            # Get the created client's UUID from Location header
            location = response.headers.get("Location", "")
            client_uuid = location.split("/")[-1] if location else None

            if not client_uuid:
                # Fallback: fetch by clientId
                client = self.get_client(config["clientId"])
                client_uuid = client.get("id") if client else None

            return client_uuid

        except httpx.HTTPStatusError as e:
            print(f"✗ Error creating client: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error creating client: {e}")
            return None

    def update_client(self, client_uuid: str, config: Dict) -> bool:
        """
        Update an existing client

        Args:
            client_uuid: The UUID of the client to update
            config: Client configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.put(
                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_uuid}",
                headers=self._get_headers(),
                json=config
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            print(f"✗ Error updating client: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error updating client: {e}")
            return False

    def get_client_secret(self, client_uuid: str) -> Optional[str]:
        """
        Get client secret

        Args:
            client_uuid: The UUID of the client

        Returns:
            Client secret if successful, None otherwise
        """
        try:
            response = self.client.get(
                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_uuid}/client-secret",
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            return data.get("value")

        except httpx.HTTPStatusError as e:
            print(f"✗ Error fetching client secret: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error fetching client secret: {e}")
            return None

    def regenerate_client_secret(self, client_uuid: str) -> Optional[str]:
        """
        Regenerate client secret

        Args:
            client_uuid: The UUID of the client

        Returns:
            New client secret if successful, None otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/admin/realms/{self.realm}/clients/{client_uuid}/client-secret",
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            return data.get("value")

        except httpx.HTTPStatusError as e:
            print(f"✗ Error regenerating client secret: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error regenerating client secret: {e}")
            return None


def save_env_file(client_secret: str) -> bool:
    """
    Save client secret to .env.keycloak file

    Args:
        client_secret: The client secret to save

    Returns:
        True if successful, False otherwise
    """
    try:
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# Keycloak OIDC Client Configuration
# Generated by setup-keycloak-client.py

KEYCLOAK_URL={KEYCLOAK_URL}
KEYCLOAK_REALM={REALM}
KEYCLOAK_CLIENT_ID={CLIENT_ID}
KEYCLOAK_CLIENT_SECRET={client_secret}
"""

        ENV_FILE.write_text(content)
        return True

    except Exception as e:
        print(f"✗ Error saving .env.keycloak file: {e}")
        return False


def main() -> int:
    """
    Main execution function

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("UC-1 Pro Operations Center - Keycloak OIDC Client Setup")
    print("=" * 70)
    print()

    # Connect to Keycloak
    print(f"→ Connecting to Keycloak at {KEYCLOAK_URL}...")

    with KeycloakAdmin(KEYCLOAK_URL, REALM) as admin:
        # Authenticate
        print(f"→ Authenticating as '{ADMIN_USERNAME}'...")
        if not admin.authenticate(ADMIN_USERNAME, ADMIN_PASSWORD):
            print()
            print("✗ Failed to authenticate with Keycloak")
            print("  Please check your credentials and network connection.")
            return 1

        print(f"✓ Authenticated successfully")
        print()

        # Check if client exists
        print(f"→ Checking if client '{CLIENT_ID}' exists...")
        existing_client = admin.get_client(CLIENT_ID)

        client_uuid = None
        is_update = False

        if existing_client:
            print(f"✓ Client '{CLIENT_ID}' already exists")
            print(f"→ Updating client configuration...")
            client_uuid = existing_client.get("id")
            is_update = True

            # Update existing client
            if not admin.update_client(client_uuid, CLIENT_CONFIG):
                print()
                print("✗ Failed to update client configuration")
                return 1

            print(f"✓ Client configuration updated successfully")
        else:
            print(f"→ Client '{CLIENT_ID}' not found, creating new client...")

            # Create new client
            client_uuid = admin.create_client(CLIENT_CONFIG)
            if not client_uuid:
                print()
                print("✗ Failed to create client")
                return 1

            print(f"✓ Client '{CLIENT_ID}' created successfully")

        print()

        # Get client secret
        print("→ Retrieving client secret...")
        client_secret = admin.get_client_secret(client_uuid)

        if not client_secret:
            print()
            print("✗ Failed to retrieve client secret")
            return 1

        print(f"✓ Client secret retrieved successfully")
        print()

        # Save to .env file
        print(f"→ Saving configuration to {ENV_FILE}...")
        if not save_env_file(client_secret):
            print()
            print("✗ Failed to save configuration file")
            print(f"  Please manually save the client secret: {client_secret}")
            return 1

        print(f"✓ Configuration saved to .env.keycloak")
        print()

        # Print summary
        print("=" * 70)
        print("✓ Setup completed successfully!")
        print("=" * 70)
        print()
        print("Client Configuration:")
        print(f"  Keycloak URL:  {KEYCLOAK_URL}")
        print(f"  Realm:         {REALM}")
        print(f"  Client ID:     {CLIENT_ID}")
        print(f"  Client Secret: {client_secret}")
        print()
        print("Redirect URIs:")
        for uri in CLIENT_CONFIG["redirectUris"]:
            print(f"  - {uri}")
        print()
        print("Next Steps:")
        print("=" * 70)
        print()
        print("1. Export the client secret as an environment variable:")
        print(f'   export KEYCLOAK_CLIENT_SECRET="{client_secret}"')
        print()
        print("2. Update your docker-compose.yml or application configuration")
        print("   to use the new Keycloak settings")
        print()
        print("3. Rebuild the Ops Center container:")
        print("   docker-compose up -d --build ops-center")
        print()
        print("4. Test the SSO login flow:")
        print("   https://unicorncommander.ai/login")
        print()
        print("Configuration saved to:")
        print(f"  {ENV_FILE}")
        print()

        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("✗ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
