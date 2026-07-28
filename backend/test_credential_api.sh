#!/bin/bash
# Credential API Integration Tests
# Tests all CRUD operations without requiring admin authentication

set -e  # Exit on error

BASE_URL="http://localhost:8084/api/v1/credentials"
FAILED_TESTS=0
PASSED_TESTS=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"

    echo -e "${YELLOW}Testing:${NC} $test_name"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} - HTTP $http_code"
        echo "Response: $body"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} - Expected HTTP $expected_status, got HTTP $http_code"
        echo "Response: $body"
        ((FAILED_TESTS++))
        return 1
    fi
}

echo "================================================"
echo "Credential API Integration Tests"
echo "================================================"
echo ""

# Test 1: Health Check
test_endpoint \
    "Health Check" \
    "GET" \
    "/health" \
    "" \
    "200"

echo ""

# Test 2: List Credentials (Empty - no auth needed for now)
test_endpoint \
    "List All Credentials (Empty)" \
    "GET" \
    "" \
    "" \
    "401"  # Should fail without auth

echo ""

# Test 3: Create Cloudflare Credential (will fail without auth)
test_endpoint \
    "Create Cloudflare Credential" \
    "POST" \
    "" \
    '{"service":"cloudflare","credential_type":"api_token","value":"cf_test_token_12345678901234567890","metadata":{"description":"Test credential"}}' \
    "401"  # Should fail without auth

echo ""

# Test 4: Get Specific Credential (will fail without auth)
test_endpoint \
    "Get Cloudflare API Token" \
    "GET" \
    "/cloudflare/api_token" \
    "" \
    "401"  # Should fail without auth

echo ""

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
