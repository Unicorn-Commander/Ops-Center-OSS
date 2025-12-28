#!/bin/bash
set -e

# Configuration - Override with environment variables
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-change-me}"

echo "=== Setting Up Automatic Username Sanitization ==="

TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN_USER}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

echo "Checking for username generation in identity provider mappers..."

# Get Google identity provider
GOOGLE_MAPPERS=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/google/mappers" \
  -H "Authorization: Bearer $TOKEN")

echo "Google IDP mappers:"
echo "$GOOGLE_MAPPERS" | jq -r '.[] | {name, identityProviderMapper}'

# Create username template mapper for Google
echo ""
echo "Creating username template mapper for Google IDP..."

# Check if mapper exists
EXISTING=$(echo "$GOOGLE_MAPPERS" | jq -r '.[] | select(.name=="username-importer") | .id')

if [ -n "$EXISTING" ]; then
  echo "Deleting existing mapper..."
  curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/google/mappers/$EXISTING" \
    -H "Authorization: Bearer $TOKEN"
fi

# Create new mapper that extracts local part of email
curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/google/mappers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "username-from-email",
    "identityProviderAlias": "google",
    "identityProviderMapper": "oidc-username-idp-mapper",
    "config": {
      "template": "${ALIAS}.${CLAIM.email | localPart}"
    }
  }'

echo "Created username mapper for Google (will use: google.{email_local_part})"

# Do the same for GitHub
echo ""
echo "Creating username mapper for GitHub IDP..."

GITHUB_MAPPERS=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/github/mappers" \
  -H "Authorization: Bearer $TOKEN")

EXISTING_GITHUB=$(echo "$GITHUB_MAPPERS" | jq -r '.[] | select(.name=="username-from-email") | .id')

if [ -n "$EXISTING_GITHUB" ]; then
  curl -s -X DELETE "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/github/mappers/$EXISTING_GITHUB" \
    -H "Authorization: Bearer $TOKEN"
fi

curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/github/mappers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "username-from-email",
    "identityProviderAlias": "github",
    "identityProviderMapper": "oidc-username-idp-mapper",
    "config": {
      "template": "${ALIAS}.${CLAIM.email | localPart}"
    }
  }'

echo "Created username mapper for GitHub"

echo ""
echo "=== Configuration Complete ==="
echo ""
echo "New users registering via Google will get username: google.{name}"
echo "New users registering via GitHub will get username: github.{name}"
echo "No @ symbols in usernames!"
echo ""
echo "Example:"
echo "  Email: user@example.com"
echo "  Username: google.user"
echo ""
echo "This will work automatically with Forgejo!"
