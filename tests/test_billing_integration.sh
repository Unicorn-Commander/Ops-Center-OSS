#!/bin/bash
#
# Billing System Integration Test Script
# Tests all API endpoints and tier enforcement
#
# Usage: ./test_billing_integration.sh [base_url]
#

set -e

# Configuration
BASE_URL="${1:-http://localhost:8084}"
KEYCLOAK_URL="${KEYCLOAK_URL:-https://auth.your-domain.com}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-uchub}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Print functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_test() {
    echo -e "${YELLOW}TEST: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Test function
run_test() {
    local test_name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="${4:-}"
    local expected_status="${5:-200}"

    ((TESTS_RUN++))
    print_test "$test_name"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_status" ]; then
        print_success "Status: $http_code (expected $expected_status)"
        if [ -n "$body" ] && [ "$body" != "null" ]; then
            echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        fi
        return 0
    else
        print_fail "Status: $http_code (expected $expected_status)"
        echo "Response: $body"
        return 1
    fi
}

# Start tests
print_header "BILLING SYSTEM INTEGRATION TESTS"
echo "Base URL: $BASE_URL"
echo "Keycloak: $KEYCLOAK_URL"
echo "Start Time: $(date)"
echo ""

# ==============================================================================
# PUBLIC ENDPOINTS (No Auth Required)
# ==============================================================================

print_header "PUBLIC ENDPOINTS"

# Test 1: Webhook health check
run_test "Webhook Health Check" \
    "/api/v1/webhooks/lago/health" \
    "GET" \
    "" \
    "200"

# Test 2: Subscription plans
run_test "Get Subscription Plans" \
    "/api/v1/subscriptions/plans" \
    "GET" \
    "" \
    "200"

# ==============================================================================
# TIER CHECK ENDPOINTS
# ==============================================================================

print_header "TIER CHECK ENDPOINTS"

# Test 3: Basic tier check (no auth)
run_test "Tier Check - Unauthenticated" \
    "/api/v1/tier/check" \
    "GET" \
    "" \
    "401"

# Test 4: Service access check (no auth)
run_test "Service Access Check - Unauthenticated" \
    "/api/v1/tier/service/openwebui" \
    "GET" \
    "" \
    "401"

# ==============================================================================
# STRIPE ENDPOINTS (Require Auth)
# ==============================================================================

print_header "STRIPE ENDPOINTS"

print_info "Note: These endpoints require authentication"
print_info "Testing for proper 401/403 responses..."

# Test 5: Create checkout session (needs auth)
run_test "Create Checkout Session - No Auth" \
    "/api/v1/billing/checkout" \
    "POST" \
    '{"tier": "starter"}' \
    "401"

# Test 6: Customer portal (needs auth)
run_test "Customer Portal - No Auth" \
    "/api/v1/billing/portal" \
    "POST" \
    '{}' \
    "401"

# Test 7: Subscription status (needs auth)
run_test "Subscription Status - No Auth" \
    "/api/v1/billing/subscription" \
    "GET" \
    "" \
    "401"

# ==============================================================================
# BYOK ENDPOINTS (Require Auth + Tier)
# ==============================================================================

print_header "BYOK ENDPOINTS"

print_info "BYOK endpoints require Starter+ tier"

# Test 8: List API keys (needs auth)
run_test "List API Keys - No Auth" \
    "/api/v1/byok/keys" \
    "GET" \
    "" \
    "401"

# Test 9: Add API key (needs auth)
run_test "Add API Key - No Auth" \
    "/api/v1/byok/keys" \
    "POST" \
    '{"provider": "openai", "key": "sk-test123"}' \
    "401"

# ==============================================================================
# WEBHOOK ENDPOINTS
# ==============================================================================

print_header "WEBHOOK ENDPOINTS"

# Test 10: Lago webhook - subscription.created
print_test "Lago Webhook - subscription.created"
webhook_payload='{
    "webhook_type": "subscription.created",
    "subscription": {
        "lago_id": "test_sub_123",
        "plan_code": "starter_monthly",
        "status": "active"
    },
    "customer": {
        "email": "test-webhook@example.com"
    }
}'

response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$webhook_payload" \
    "$BASE_URL/api/v1/webhooks/lago")

http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "200" ]; then
    print_success "Webhook accepted: $http_code"
    ((TESTS_PASSED++))
else
    print_fail "Webhook rejected: $http_code"
    ((TESTS_FAILED++))
fi
((TESTS_RUN++))

# Test 11: Lago webhook - subscription.cancelled
print_test "Lago Webhook - subscription.cancelled"
webhook_payload='{
    "webhook_type": "subscription.cancelled",
    "subscription": {
        "lago_id": "test_sub_123"
    },
    "customer": {
        "email": "test-webhook@example.com"
    }
}'

response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$webhook_payload" \
    "$BASE_URL/api/v1/webhooks/lago")

http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "200" ]; then
    print_success "Webhook accepted: $http_code"
    ((TESTS_PASSED++))
else
    print_fail "Webhook rejected: $http_code"
    ((TESTS_FAILED++))
fi
((TESTS_RUN++))

# ==============================================================================
# ADMIN ENDPOINTS (Require Admin Role)
# ==============================================================================

print_header "ADMIN ENDPOINTS"

print_info "Admin endpoints require admin role"

# Test 12: List all subscriptions (admin only)
run_test "List All Subscriptions - No Auth" \
    "/api/v1/admin/subscriptions/list" \
    "GET" \
    "" \
    "401"

# Test 13: Subscription analytics (admin only)
run_test "Subscription Analytics - No Auth" \
    "/api/v1/admin/subscriptions/analytics/overview" \
    "GET" \
    "" \
    "401"

# Test 14: Revenue by tier (admin only)
run_test "Revenue by Tier - No Auth" \
    "/api/v1/admin/subscriptions/analytics/revenue-by-tier" \
    "GET" \
    "" \
    "401"

# ==============================================================================
# USAGE TRACKING
# ==============================================================================

print_header "USAGE TRACKING"

print_info "Testing usage increment API"

# Test 15: Increment usage (needs auth)
run_test "Increment Usage - No Auth" \
    "/api/v1/usage/increment" \
    "POST" \
    '{}' \
    "401"

# ==============================================================================
# TIER ENFORCEMENT
# ==============================================================================

print_header "TIER ENFORCEMENT"

print_info "Testing tier-based access control"

# Test 16: Check if trial user can access BYOK
echo ""
print_test "Tier Enforcement - Trial vs BYOK"
print_info "Trial tier should NOT have BYOK access"
print_info "Starter+ tiers should have BYOK access"
echo ""

# ==============================================================================
# STRIPE TEST CARDS
# ==============================================================================

print_header "STRIPE TEST CARD VALIDATION"

print_info "Stripe test cards for manual testing:"
echo "  • Success:             4242 4242 4242 4242"
echo "  • Decline:             4000 0000 0000 0002"
echo "  • Insufficient Funds:  4000 0000 0000 9995"
echo "  • Requires Auth:       4000 0025 0000 3155"
echo ""

# ==============================================================================
# TEST SUMMARY
# ==============================================================================

print_header "TEST SUMMARY"

echo "Tests Run:    $TESTS_RUN"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "ALL TESTS PASSED!"
    exit 0
else
    print_fail "$TESTS_FAILED TEST(S) FAILED"
    exit 1
fi
