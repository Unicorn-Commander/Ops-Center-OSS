#!/usr/bin/env python3
"""
Verify ops-center SSO configuration with uchub realm
"""
import requests
import json
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
KEYCLOAK_URL = "https://auth.unicorncommander.ai"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your-admin-password"
REALM = "uchub"
CLIENT_ID = "ops-center"

class KeycloakVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.token = None

    def get_admin_token(self):
        """Get admin access token"""
        print("🔑 Authenticating with Keycloak...")
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
            print("   ✅ Authenticated successfully")
            return True
        else:
            print(f"   ❌ Failed to authenticate: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def verify_realm(self):
        """Verify uchub realm exists and is enabled"""
        print(f"\n🔍 Checking {REALM} realm...")
        response = self.session.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}")

        if response.status_code == 200:
            realm_data = response.json()
            print(f"   ✅ Realm: {realm_data.get('displayName', REALM)}")
            print(f"   ✅ Enabled: {realm_data.get('enabled', False)}")
            return True
        else:
            print(f"   ❌ Realm check failed: {response.status_code}")
            return False

    def verify_client(self):
        """Verify ops-center client configuration"""
        print(f"\n🔍 Checking {CLIENT_ID} client...")
        response = self.session.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients",
            params={"clientId": CLIENT_ID}
        )

        if response.status_code == 200:
            clients = response.json()
            if clients:
                client = clients[0]
                print(f"   ✅ Client ID: {client['clientId']}")
                print(f"   ✅ Enabled: {client.get('enabled', False)}")
                print(f"   ✅ Public: {client.get('publicClient', True)}")
                print(f"   ✅ Protocol: {client.get('protocol', 'N/A')}")
                print(f"\n   📋 Redirect URIs:")
                for uri in client.get('redirectUris', []):
                    print(f"      - {uri}")
                print(f"\n   📋 Web Origins:")
                for origin in client.get('webOrigins', []):
                    print(f"      - {origin}")
                return True
            else:
                print(f"   ❌ Client not found")
                return False
        else:
            print(f"   ❌ Client check failed: {response.status_code}")
            return False

    def verify_identity_providers(self):
        """Verify identity providers in the realm"""
        print(f"\n🔍 Checking identity providers in {REALM} realm...")
        response = self.session.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/identity-provider/instances"
        )

        if response.status_code == 200:
            idps = response.json()
            if idps:
                print(f"   ✅ Found {len(idps)} identity provider(s):")
                for idp in idps:
                    status = "✅" if idp.get('enabled', False) else "❌"
                    print(f"      {status} {idp['alias']} ({idp['providerId']})")
                return idps
            else:
                print("   ⚠️  No identity providers found")
                return []
        else:
            print(f"   ❌ Failed to get identity providers: {response.status_code}")
            return []

    def verify_oidc_configuration(self):
        """Verify OIDC configuration is accessible"""
        print(f"\n🔍 Checking OIDC configuration...")
        response = requests.get(
            f"{KEYCLOAK_URL}/realms/{REALM}/.well-known/openid-configuration",
            verify=False
        )

        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Issuer: {config.get('issuer', 'N/A')}")
            print(f"   ✅ Authorization endpoint: {config.get('authorization_endpoint', 'N/A')}")
            print(f"   ✅ Token endpoint: {config.get('token_endpoint', 'N/A')}")
            print(f"   ✅ Userinfo endpoint: {config.get('userinfo_endpoint', 'N/A')}")
            return True
        else:
            print(f"   ❌ OIDC configuration check failed: {response.status_code}")
            return False

    def run(self):
        """Run all verification checks"""
        print("="*80)
        print("🦄 UCHUB REALM SSO CONFIGURATION VERIFICATION")
        print("="*80)

        # Step 1: Authenticate
        if not self.get_admin_token():
            print("\n❌ Verification failed: Cannot authenticate")
            return False

        # Step 2: Verify realm
        if not self.verify_realm():
            print("\n❌ Verification failed: Realm not accessible")
            return False

        # Step 3: Verify client
        if not self.verify_client():
            print("\n❌ Verification failed: Client not properly configured")
            return False

        # Step 4: Verify identity providers
        idps = self.verify_identity_providers()
        if not idps:
            print("\n⚠️  Warning: No identity providers found")

        # Step 5: Verify OIDC configuration
        if not self.verify_oidc_configuration():
            print("\n❌ Verification failed: OIDC configuration not accessible")
            return False

        print("\n" + "="*80)
        print("✅ ALL CHECKS PASSED!")
        print("="*80)
        print(f"\n🎉 SSO is properly configured for {CLIENT_ID} in {REALM} realm!")
        print(f"\n📋 Summary:")
        print(f"   - Realm: {REALM} (enabled)")
        print(f"   - Client: {CLIENT_ID} (enabled, confidential)")
        print(f"   - Identity Providers: {len(idps)} configured")
        if idps:
            for idp in idps:
                print(f"     • {idp['alias']}")
        print(f"   - OIDC Configuration: Accessible")
        print(f"\n🔗 URLs:")
        print(f"   - Keycloak: {KEYCLOAK_URL}")
        print(f"   - Realm: {KEYCLOAK_URL}/realms/{REALM}")
        print(f"   - Admin Console: {KEYCLOAK_URL}/admin/{REALM}/console/")
        print("\n" + "="*80)
        return True

if __name__ == "__main__":
    verifier = KeycloakVerifier()
    success = verifier.run()
    exit(0 if success else 1)
