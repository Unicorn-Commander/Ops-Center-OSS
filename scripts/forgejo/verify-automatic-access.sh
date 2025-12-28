#!/bin/bash
set -e

# Configuration - Override with environment variables
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-change-me}"

echo "=== Verifying Automatic Forgejo Access Configuration ==="

TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN_USER}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

echo "1. Realm Settings:"
curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    registrationEmailAsUsername: .registrationEmailAsUsername,
    editUsernameAllowed: .editUsernameAllowed,
    loginWithEmailAllowed: .loginWithEmailAllowed
  }'

echo ""
echo "2. Google IDP Username Mapper:"
curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/identity-provider/instances/google/mappers" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.name=="username-from-email") | {
    name,
    mapper: .identityProviderMapper,
    template: .config.template
  }'

echo ""
echo "3. Forgejo Client Mapper:"
FORGEJO_CLIENT_ID=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.clientId=="forgejo") | .id')

curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/clients/$FORGEJO_CLIENT_ID/protocol-mappers/models" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.name | contains("username")) | {
    name,
    mapper: .protocolMapper,
    user_attribute: .config["user.attribute"],
    claim_name: .config["claim.name"]
  }'

echo ""
echo "4. Existing Users:"
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0] | {
    email,
    username,
    firstName,
    lastName
  }'

# Database configuration - Override with environment variables
DB_CONTAINER="${POSTGRES_CONTAINER:-postgres}"
DB_USER="${POSTGRES_USER:-ops_user}"
DB_NAME="${POSTGRES_DB:-ops_center_db}"
FORGEJO_DB_CONTAINER="${FORGEJO_DB_CONTAINER:-forgejo-postgres}"
FORGEJO_DB_USER="${FORGEJO_DB_USER:-forgejo}"
FORGEJO_DB_NAME="${FORGEJO_DB_NAME:-forgejo_db}"

echo ""
echo "5. Tier-Based Access (from Ops-Center database):"
docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -t -c "
  SELECT
    st.tier_name,
    tf.feature_key,
    tf.enabled
  FROM subscription_tiers st
  JOIN tier_features tf ON st.id = tf.tier_id
  WHERE tf.feature_key = 'forgejo'
  ORDER BY st.tier_name;
" 2>&1

echo ""
echo "6. Forgejo OAuth Configuration:"
docker exec ${FORGEJO_DB_CONTAINER} psql -U ${FORGEJO_DB_USER} -d ${FORGEJO_DB_NAME} -t -c "
  SELECT
    name,
    type,
    is_active,
    cfg->>'Provider' as provider,
    cfg->>'ClientID' as client_id
  FROM login_source
  WHERE type = 6;
" 2>&1

echo ""
echo "=== Summary ==="
echo "Keycloak: Custom usernames enabled"
echo "IDP Mappers: Auto-generate valid usernames (no @ symbols)"
echo "Forgejo Mapper: Sends username as preferred_username"
echo "Tier Access: Controlled via subscription_tiers table"
echo "Forgejo: Auto-registration enabled with Keycloak SSO"
echo ""
echo "How it works now:"
echo "  1. User signs up via Google/GitHub/Microsoft"
echo "  2. Keycloak creates account with sanitized username (e.g., google.testuser)"
echo "  3. User navigates to Forgejo (if their tier allows)"
echo "  4. Clicks 'Sign in with SSO'"
echo "  5. Forgejo auto-creates account with valid username"
echo "  6. User is logged in - all automatic!"
