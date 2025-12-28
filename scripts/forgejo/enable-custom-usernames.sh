#!/bin/bash
set -e

# Configuration - Override with environment variables
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-change-me}"

echo "=== Enabling Custom Usernames in Keycloak ==="

# Get admin token
TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN_USER}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Get current realm settings
echo "Current realm settings:"
curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    registrationEmailAsUsername,
    editUsernameAllowed,
    loginWithEmailAllowed
  }'

echo ""
echo "Updating realm to allow custom usernames..."

# Update realm settings
curl -s -X PUT "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}" \
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
curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    registrationEmailAsUsername,
    editUsernameAllowed,
    loginWithEmailAllowed
  }'

echo ""
echo "Realm updated to support custom usernames"
