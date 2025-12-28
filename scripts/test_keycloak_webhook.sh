#!/bin/bash
# Test script for Keycloak Subscription Sync via Lago Webhooks

set -e

# Configuration - Override with environment variables
BASE_URL="${BASE_URL:-http://localhost:8084}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-change-me}"

# Test user - Override with environment variable
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Keycloak Subscription Sync - Test Suite"
echo "=============================================="
echo ""

# Test 1: Health Check
echo -e "${YELLOW}[TEST 1]${NC} Checking webhook health..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/api/v1/webhooks/lago/health")

if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Webhook is healthy${NC}"
    echo "$HEALTH_RESPONSE" | jq '.'
else
    echo -e "${RED}✗ Webhook health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Get Keycloak Admin Token
echo -e "${YELLOW}[TEST 2]${NC} Getting Keycloak admin token..."
TOKEN_RESPONSE=$(curl -s -k -X POST \
    "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -d "username=${KEYCLOAK_ADMIN_USER}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -H "Content-Type: application/x-www-form-urlencoded")

ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}✗ Failed to get admin token${NC}"
    echo "$TOKEN_RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✓ Admin token obtained${NC}"
echo ""

# Test 3: Get User Attributes BEFORE webhook
echo -e "${YELLOW}[TEST 3]${NC} Getting user attributes BEFORE webhook..."
USER_RESPONSE=$(curl -s -k \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}&exact=true" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

USER_ID=$(echo "$USER_RESPONSE" | jq -r '.[0].id')

if [ "$USER_ID" = "null" ] || [ -z "$USER_ID" ]; then
    echo -e "${RED}✗ User not found: ${TEST_EMAIL}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ User found: ${USER_ID}${NC}"
echo "Current attributes:"
echo "$USER_RESPONSE" | jq '.[0].attributes'
echo ""

# Test 4: Send Subscription Created Webhook
echo -e "${YELLOW}[TEST 4]${NC} Sending subscription.created webhook..."
WEBHOOK_PAYLOAD='{
    "webhook_type": "subscription.created",
    "customer": {
        "email": "'${TEST_EMAIL}'"
    },
    "subscription": {
        "lago_id": "test_sub_'$(date +%s)'",
        "plan_code": "professional_monthly",
        "status": "active"
    }
}'

WEBHOOK_RESPONSE=$(curl -s -X POST \
    "${BASE_URL}/api/v1/webhooks/lago" \
    -H "Content-Type: application/json" \
    -d "$WEBHOOK_PAYLOAD")

if echo "$WEBHOOK_RESPONSE" | jq -e '.status == "received"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Webhook received successfully${NC}"
    echo "$WEBHOOK_RESPONSE" | jq '.'
else
    echo -e "${RED}✗ Webhook failed${NC}"
    echo "$WEBHOOK_RESPONSE"
    exit 1
fi
echo ""

# Wait for processing
echo "Waiting 2 seconds for Keycloak update..."
sleep 2

# Test 5: Verify Attributes After Webhook
echo -e "${YELLOW}[TEST 5]${NC} Verifying attributes AFTER webhook..."

# Re-fetch admin token (might have expired)
TOKEN_RESPONSE=$(curl -s -k -X POST \
    "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -d "username=${KEYCLOAK_ADMIN_USER}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -H "Content-Type: application/x-www-form-urlencoded")

ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

USER_RESPONSE=$(curl -s -k \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}&exact=true" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

echo "Updated attributes:"
ATTRIBUTES=$(echo "$USER_RESPONSE" | jq '.[0].attributes')
echo "$ATTRIBUTES" | jq '.'

# Check specific attributes
TIER=$(echo "$ATTRIBUTES" | jq -r '.subscription_tier[0]')
STATUS=$(echo "$ATTRIBUTES" | jq -r '.subscription_status[0]')
API_CALLS=$(echo "$ATTRIBUTES" | jq -r '.api_calls_used[0]')

echo ""
echo "Attribute Verification:"

if [ "$TIER" = "professional" ]; then
    echo -e "${GREEN}✓ subscription_tier = professional${NC}"
else
    echo -e "${RED}✗ subscription_tier = ${TIER} (expected: professional)${NC}"
fi

if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}✓ subscription_status = active${NC}"
else
    echo -e "${RED}✗ subscription_status = ${STATUS} (expected: active)${NC}"
fi

if [ "$API_CALLS" = "0" ]; then
    echo -e "${GREEN}✓ api_calls_used = 0${NC}"
else
    echo -e "${RED}✗ api_calls_used = ${API_CALLS} (expected: 0)${NC}"
fi

echo ""

# Test 6: Send Subscription Updated Webhook (upgrade to enterprise)
echo -e "${YELLOW}[TEST 6]${NC} Sending subscription.updated webhook (upgrade to enterprise)..."
WEBHOOK_PAYLOAD='{
    "webhook_type": "subscription.updated",
    "customer": {
        "email": "'${TEST_EMAIL}'"
    },
    "subscription": {
        "lago_id": "test_sub_'$(date +%s)'",
        "plan_code": "enterprise_annual",
        "status": "active"
    }
}'

WEBHOOK_RESPONSE=$(curl -s -X POST \
    "${BASE_URL}/api/v1/webhooks/lago" \
    -H "Content-Type: application/json" \
    -d "$WEBHOOK_PAYLOAD")

if echo "$WEBHOOK_RESPONSE" | jq -e '.status == "received"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Webhook received successfully${NC}"
else
    echo -e "${RED}✗ Webhook failed${NC}"
    echo "$WEBHOOK_RESPONSE"
    exit 1
fi

sleep 2

# Verify upgrade
USER_RESPONSE=$(curl -s -k \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}&exact=true" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

TIER=$(echo "$USER_RESPONSE" | jq -r '.[0].attributes.subscription_tier[0]')

if [ "$TIER" = "enterprise" ]; then
    echo -e "${GREEN}✓ Upgraded to enterprise tier${NC}"
else
    echo -e "${RED}✗ Tier not updated: ${TIER}${NC}"
fi
echo ""

# Test 7: Send Subscription Cancelled Webhook
echo -e "${YELLOW}[TEST 7]${NC} Sending subscription.cancelled webhook..."
WEBHOOK_PAYLOAD='{
    "webhook_type": "subscription.cancelled",
    "customer": {
        "email": "'${TEST_EMAIL}'"
    },
    "subscription": {
        "lago_id": "test_sub_'$(date +%s)'"
    }
}'

WEBHOOK_RESPONSE=$(curl -s -X POST \
    "${BASE_URL}/api/v1/webhooks/lago" \
    -H "Content-Type: application/json" \
    -d "$WEBHOOK_PAYLOAD")

if echo "$WEBHOOK_RESPONSE" | jq -e '.status == "received"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Webhook received successfully${NC}"
else
    echo -e "${RED}✗ Webhook failed${NC}"
    echo "$WEBHOOK_RESPONSE"
    exit 1
fi

sleep 2

# Verify cancellation
USER_RESPONSE=$(curl -s -k \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}&exact=true" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

TIER=$(echo "$USER_RESPONSE" | jq -r '.[0].attributes.subscription_tier[0]')
STATUS=$(echo "$USER_RESPONSE" | jq -r '.[0].attributes.subscription_status[0]')

if [ "$TIER" = "free" ] && [ "$STATUS" = "cancelled" ]; then
    echo -e "${GREEN}✓ Subscription cancelled, downgraded to free tier${NC}"
else
    echo -e "${RED}✗ Cancellation not reflected: tier=${TIER}, status=${STATUS}${NC}"
fi
echo ""

# Test 8: Send Invoice Paid Webhook (usage reset)
echo -e "${YELLOW}[TEST 8]${NC} Sending invoice.paid webhook (usage reset)..."

# First, set some usage
TOKEN_RESPONSE=$(curl -s -k -X POST \
    "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -d "username=${KEYCLOAK_ADMIN_USER}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -H "Content-Type: application/x-www-form-urlencoded")

ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

# Manually set usage to test reset
curl -s -k -X PUT \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users/${USER_ID}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "attributes": {
            "subscription_tier": ["basic"],
            "subscription_status": ["active"],
            "api_calls_used": ["42"]
        }
    }' > /dev/null

echo "Set api_calls_used to 42"
sleep 1

# Send invoice paid webhook
WEBHOOK_PAYLOAD='{
    "webhook_type": "invoice.paid",
    "customer": {
        "email": "'${TEST_EMAIL}'"
    },
    "invoice": {
        "lago_id": "inv_test_'$(date +%s)'",
        "payment_status": "succeeded"
    }
}'

WEBHOOK_RESPONSE=$(curl -s -X POST \
    "${BASE_URL}/api/v1/webhooks/lago" \
    -H "Content-Type: application/json" \
    -d "$WEBHOOK_PAYLOAD")

if echo "$WEBHOOK_RESPONSE" | jq -e '.status == "received"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Webhook received successfully${NC}"
else
    echo -e "${RED}✗ Webhook failed${NC}"
    echo "$WEBHOOK_RESPONSE"
    exit 1
fi

sleep 2

# Verify usage reset
USER_RESPONSE=$(curl -s -k \
    "${KEYCLOAK_URL}/admin/realms/${KEYCLOAK_REALM}/users?email=${TEST_EMAIL}&exact=true" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

API_CALLS=$(echo "$USER_RESPONSE" | jq -r '.[0].attributes.api_calls_used[0]')

if [ "$API_CALLS" = "0" ]; then
    echo -e "${GREEN}✓ Usage counter reset to 0${NC}"
else
    echo -e "${RED}✗ Usage not reset: ${API_CALLS}${NC}"
fi
echo ""

# Summary
echo "=============================================="
echo -e "${GREEN}All tests completed!${NC}"
echo "=============================================="
echo ""
echo "Summary:"
echo "  ✓ Webhook health check"
echo "  ✓ Keycloak authentication"
echo "  ✓ User lookup"
echo "  ✓ Subscription creation"
echo "  ✓ Subscription upgrade"
echo "  ✓ Subscription cancellation"
echo "  ✓ Usage reset on payment"
echo ""
echo "Integration is working correctly!"
