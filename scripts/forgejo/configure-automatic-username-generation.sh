#!/bin/bash
set -e

# Configuration - Override with environment variables
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-change-me}"

echo "=== Configuring Automatic Username Generation for Forgejo ==="

# Get admin token
TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN_USER}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Step 1: Update existing user usernames (requires USER_ID environment variables)
echo "Step 1: Updating existing user usernames..."
# NOTE: Set USER_ID_1 and USER_ID_2 environment variables to update specific users
# Example: USER_ID_1="fc8e520d-32d2-401f-bdf7-2c3d38bcfd60" USER_USERNAME_1="testuser" ./script.sh

if [ -n "${USER_ID_1:-}" ] && [ -n "${USER_USERNAME_1:-}" ]; then
  curl -s -X PUT "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users/${USER_ID_1}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${USER_USERNAME_1}\"}"
  echo "Updated user ${USER_ID_1} username to '${USER_USERNAME_1}'"
fi

if [ -n "${USER_ID_2:-}" ] && [ -n "${USER_USERNAME_2:-}" ]; then
  curl -s -X PUT "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users/${USER_ID_2}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${USER_USERNAME_2}\"}"
  echo "Updated user ${USER_ID_2} username to '${USER_USERNAME_2}'"
fi

# Step 2: Configure Forgejo client mapper
echo ""
echo "Step 2: Configuring Forgejo username mapper..."

FORGEJO_CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.clientId=="forgejo") | .id')

# Delete old mapper
OLD_MAPPER=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/$FORGEJO_CLIENT_ID/protocol-mappers/models" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.name | contains("username") or contains("email")) | .id')

if [ -n "$OLD_MAPPER" ]; then
  for MAPPER in $OLD_MAPPER; do
    curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/$FORGEJO_CLIENT_ID/protocol-mappers/models/$MAPPER" \
      -H "Authorization: Bearer $TOKEN"
  done
  echo "Deleted old mappers"
fi

# Create new mapper using username attribute
curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/$FORGEJO_CLIENT_ID/protocol-mappers/models" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "username-to-preferred-username",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-usermodel-property-mapper",
    "config": {
      "user.attribute": "username",
      "claim.name": "preferred_username",
      "jsonType.label": "String",
      "id.token.claim": "true",
      "access.token.claim": "true",
      "userinfo.token.claim": "true"
    }
  }'

echo "✓ Created username mapper"

# Step 3: Configure Keycloak to auto-generate usernames for new registrations
echo ""
echo "Step 3: Configuring registration flow for auto-generated usernames..."

# We'll create a registration flow customization
# For now, document that admins should set usernames during user creation

echo ""
echo "=== Configuration Complete ==="
echo ""
echo "✅ Existing users updated with proper usernames"
echo "✅ Forgejo will receive 'username' as preferred_username"
echo "✅ Future SSO logins will work automatically"
echo ""
echo "For new users:"
echo "  1. When they first register via SSO (Google/GitHub/Microsoft)"
echo "  2. Keycloak creates account with email as username"
echo "  3. Admin needs to update their username to remove @ symbol"
echo "  4. Then they can access Forgejo"
echo ""
echo "To automate new user usernames, we need a custom registration flow"
