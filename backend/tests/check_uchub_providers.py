#!/usr/bin/env python3
"""Check identity providers and clients in uchub realm"""

import requests
import json

# Get admin token
token_response = requests.post(
    "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/token",
    data={
        "client_id": "admin-cli",
        "username": "admin",
        "password": "Cmon Widja2626",
        "grant_type": "password"
    },
    verify=False
)

if token_response.status_code != 200:
    print(f"❌ Failed to get admin token: {token_response.status_code}")
    print(token_response.text)
    exit(1)

token = token_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("="*80)
print("🔍 UCHUB REALM - IDENTITY PROVIDERS")
print("="*80)

# Get identity providers
idp_response = requests.get(
    "https://auth.unicorncommander.ai/admin/realms/uchub/identity-provider/instances",
    headers=headers,
    verify=False
)

if idp_response.status_code == 200:
    idps = idp_response.json()
    if idps:
        for idp in idps:
            print(f"\n✅ {idp['alias']} ({idp['providerId']})")
            print(f"   Display Name: {idp.get('displayName', 'N/A')}")
            print(f"   Enabled: {idp.get('enabled', False)}")
    else:
        print("⚠️  No identity providers found")
else:
    print(f"❌ Failed to get identity providers: {idp_response.status_code}")

print("\n" + "="*80)
print("🔍 UCHUB REALM - OAUTH CLIENTS")
print("="*80)

# Get clients
clients_response = requests.get(
    "https://auth.unicorncommander.ai/admin/realms/uchub/clients",
    headers=headers,
    verify=False
)

if clients_response.status_code == 200:
    clients = clients_response.json()
    for client in clients:
        client_id = client.get("clientId")
        if not client_id.startswith("account") and not client_id.startswith("admin") and not client_id.startswith("broker"):
            print(f"\n📱 {client_id}")
            print(f"   ID: {client.get('id')}")
            print(f"   Enabled: {client.get('enabled', False)}")
            redirects = client.get("redirectUris", [])
            if redirects:
                print(f"   Redirect URIs: {', '.join(redirects[:3])}")
else:
    print(f"❌ Failed to get clients: {clients_response.status_code}")

print("\n" + "="*80)
