#!/usr/bin/env python3
"""
Programmatically set up ops-center client in uchub realm
"""
import requests
import json
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
KEYCLOAK_URL = "https://auth.unicorncommander.ai"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Cmon Widja2626"
REALM = "uchub"

class KeycloakAdmin:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.token = None

    def get_admin_token(self):
        """Get admin access token"""
        print("🔑 Getting admin access token...")
        response = self.session.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "grant_type": "password"
            }
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
            print("   ✅ Admin token obtained")
            return True
        else:
            print(f"   ❌ Failed to get token: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def check_realm_exists(self):
        """Check if uchub realm exists"""
        print(f"\n🔍 Checking if {REALM} realm exists...")
        response = self.session.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}")

        if response.status_code == 200:
            realm_data = response.json()
            print(f"   ✅ Realm found: {realm_data.get('displayName', REALM)}")
            return True
        else:
            print(f"   ❌ Realm not found: {response.status_code}")
            return False

    def list_identity_providers(self):
        """List identity providers in the realm"""
        print(f"\n🔍 Checking identity providers in {REALM} realm...")
        response = self.session.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/identity-provider/instances"
        )

        if response.status_code == 200:
            idps = response.json()
            if idps:
                print(f"   ✅ Found {len(idps)} identity provider(s):")
                for idp in idps:
                    print(f"      - {idp['alias']} ({idp['providerId']}) - Enabled: {idp.get('enabled', False)}")
                return idps
            else:
                print("   ⚠️  No identity providers found")
                return []
        else:
            print(f"   ❌ Failed to get identity providers: {response.status_code}")
            return []

    def check_client_exists(self, client_id):
        """Check if client already exists"""
        print(f"\n🔍 Checking if {client_id} client exists...")
        response = self.session.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients",
            params={"clientId": client_id}
        )

        if response.status_code == 200:
            clients = response.json()
            if clients:
                print(f"   ✅ Client already exists (ID: {clients[0]['id']})")
                return clients[0]
            else:
                print(f"   ℹ️  Client does not exist yet")
                return None
        else:
            print(f"   ❌ Failed to check client: {response.status_code}")
            return None

    def create_client(self):
        """Create ops-center client"""
        print(f"\n🚀 Creating ops-center client in {REALM} realm...")

        client_data = {
            "clientId": "ops-center",
            "name": "Ops Center",
            "description": "UC Cloud Operations Center",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "secret": "your-keycloak-client-secret",
            "publicClient": False,
            "bearerOnly": False,
            "consentRequired": False,
            "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": False,
            "authorizationServicesEnabled": False,
            "protocol": "openid-connect",
            "attributes": {
                "saml.assertion.signature": "false",
                "saml.force.post.binding": "false",
                "saml.multivalued.roles": "false",
                "saml.encrypt": "false",
                "saml.server.signature": "false",
                "saml.server.signature.keyinfo.ext": "false",
                "exclude.session.state.from.auth.response": "false",
                "saml_force_name_id_format": "false",
                "saml.client.signature": "false",
                "tls.client.certificate.bound.access.tokens": "false",
                "saml.authnstatement": "false",
                "display.on.consent.screen": "false",
                "saml.onetimeuse.condition": "false"
            },
            "redirectUris": [
                "https://unicorncommander.ai/*",
                "https://unicorncommander.ai/auth/callback"
            ],
            "webOrigins": [
                "https://unicorncommander.ai"
            ],
            "rootUrl": "https://unicorncommander.ai",
            "baseUrl": "https://unicorncommander.ai",
            "adminUrl": "",
            "surrogateAuthRequired": False,
            "fullScopeAllowed": True,
            "nodeReRegistrationTimeout": -1,
            "defaultClientScopes": [
                "web-origins",
                "acr",
                "profile",
                "roles",
                "email"
            ],
            "optionalClientScopes": [
                "address",
                "phone",
                "offline_access",
                "microprofile-jwt"
            ]
        }

        response = self.session.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients",
            json=client_data
        )

        if response.status_code == 201:
            print("   ✅ Client created successfully!")
            # Get the created client ID from Location header
            location = response.headers.get('Location', '')
            if location:
                client_uuid = location.split('/')[-1]
                print(f"   Client UUID: {client_uuid}")
            return True
        else:
            print(f"   ❌ Failed to create client: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def update_client_secret(self, client_uuid):
        """Update client secret"""
        print(f"\n🔐 Setting client secret...")

        secret_data = {
            "type": "secret",
            "value": "your-keycloak-client-secret"
        }

        response = self.session.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_uuid}/client-secret",
            json=secret_data
        )

        if response.status_code in [200, 204]:
            print("   ✅ Client secret set successfully!")
            return True
        else:
            print(f"   ⚠️  Response: {response.status_code} (secret may have been set during creation)")
            return True  # Don't fail if secret was already set

    def run(self):
        """Run the full setup"""
        print("="*80)
        print("🦄 KEYCLOAK UCHUB REALM - OPS-CENTER CLIENT SETUP")
        print("="*80)

        # Step 1: Get admin token
        if not self.get_admin_token():
            print("\n❌ Failed to authenticate. Exiting.")
            return False

        # Step 2: Check realm exists
        if not self.check_realm_exists():
            print("\n❌ Realm does not exist. Exiting.")
            return False

        # Step 3: List identity providers
        idps = self.list_identity_providers()

        # Step 4: Check if client exists
        existing_client = self.check_client_exists("ops-center")

        if existing_client:
            print("\n✅ Client already exists! No action needed.")
            print(f"   Client ID: ops-center")
            print(f"   Client UUID: {existing_client['id']}")
            print(f"   Redirect URIs: {existing_client.get('redirectUris', [])}")
            return True

        # Step 5: Create client
        if not self.create_client():
            return False

        # Step 6: Verify client was created
        created_client = self.check_client_exists("ops-center")
        if created_client:
            print("\n" + "="*80)
            print("📊 SETUP COMPLETE!")
            print("="*80)
            print(f"✅ Realm: {REALM}")
            print(f"✅ Client ID: ops-center")
            print(f"✅ Client Secret: your-keycloak-client-secret")
            print(f"✅ Redirect URIs: {created_client.get('redirectUris', [])}")
            print(f"✅ Identity Providers: {len(idps)} configured")
            if idps:
                for idp in idps:
                    print(f"   - {idp['alias']}")
            print("\n🎉 SSO should now work with Google/GitHub/Microsoft!")
            print("="*80)
            return True
        else:
            print("\n⚠️  Client creation reported success but verification failed")
            return False

if __name__ == "__main__":
    admin = KeycloakAdmin()
    success = admin.run()
    exit(0 if success else 1)
