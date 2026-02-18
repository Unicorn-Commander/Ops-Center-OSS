#!/bin/bash
set -e

echo "=== Enabling Custom Usernames in Keycloak ==="

# Get admin token
TOKEN=$(curl -s -X POST "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=your-admin-password" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Get current realm settings
echo "Current realm settings:"
curl -s -X GET "https://auth.unicorncommander.ai/admin/realms/uchub" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    registrationEmailAsUsername,
    editUsernameAllowed,
    loginWithEmailAllowed
  }'

echo ""
echo "Updating realm to allow custom usernames..."

# Update realm settings
curl -s -X PUT "https://auth.unicorncommander.ai/admin/realms/uchub" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "registrationEmailAsUsername": false,
    "editUsernameAllowed": true,
    "loginWithEmailAllowed": true
  }'

echo ""
echo "Waiting 2 seconds for changes to apply..."
sleep 2

echo ""
echo "Verification:"
curl -s -X GET "https://auth.unicorncommander.ai/admin/realms/uchub" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    registrationEmailAsUsername,
    editUsernameAllowed,
    loginWithEmailAllowed
  }'

echo ""
echo "✅ Realm updated to support custom usernames"
