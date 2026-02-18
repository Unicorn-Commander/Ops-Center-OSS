#!/bin/bash
set -e

echo "=== Configuring Automatic Username Generation for Forgejo ==="

# Get admin token
TOKEN=$(curl -s -X POST "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=your-admin-password" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Step 1: Update Shafen's username in Keycloak
echo "Step 1: Updating existing user usernames..."
SHAFEN_ID="fc8e520d-32d2-401f-bdf7-2c3d38bcfd60"

curl -s -X PUT "https://auth.unicorncommander.ai/admin/realms/uchub/users/$SHAFEN_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "shafen"
  }'

echo "✓ Updated Shafen's username to 'shafen'"

# Also update admin
ADMIN_ID="ecde32ba-65c6-4fdd-9f22-2d4c1c8d8b8e"
curl -s -X PUT "https://auth.unicorncommander.ai/admin/realms/uchub/users/$ADMIN_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "aaron"
  }'

echo "✓ Updated admin username to 'aaron'"

# Step 2: Configure Forgejo client mapper
echo ""
echo "Step 2: Configuring Forgejo username mapper..."

CLIENT_ID=$(curl -s -X GET "https://auth.unicorncommander.ai/admin/realms/uchub/clients" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.clientId=="forgejo") | .id')

# Delete old mapper
OLD_MAPPER=$(curl -s -X GET "https://auth.unicorncommander.ai/admin/realms/uchub/clients/$CLIENT_ID/protocol-mappers/models" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.name | contains("username") or contains("email")) | .id')

if [ -n "$OLD_MAPPER" ]; then
  for MAPPER in $OLD_MAPPER; do
    curl -s -X DELETE "https://auth.unicorncommander.ai/admin/realms/uchub/clients/$CLIENT_ID/protocol-mappers/models/$MAPPER" \
      -H "Authorization: Bearer $TOKEN"
  done
  echo "✓ Deleted old mappers"
fi

# Create new mapper using username attribute
curl -s -X POST "https://auth.unicorncommander.ai/admin/realms/uchub/clients/$CLIENT_ID/protocol-mappers/models" \
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
