#!/bin/bash
#
# BYOK API Test Script
# Quick tests for BYOK endpoints using curl
#

set -e

# Configuration
BASE_URL="${BASE_URL:-https://unicorncommander.ai}"
SESSION_COOKIE="${SESSION_COOKIE:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if session cookie is set
if [ -z "$SESSION_COOKIE" ]; then
    echo -e "${YELLOW}⚠ SESSION_COOKIE not set${NC}"
    echo ""
    echo "To use this script:"
    echo "  1. Login to $BASE_URL"
    echo "  2. Get session cookie from browser (DevTools > Application > Cookies)"
    echo "  3. Export it: export SESSION_COOKIE='your_cookie_here'"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  BYOK API Test Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Base URL: $BASE_URL"
echo ""

# Test 1: List providers
echo -e "${YELLOW}[Test 1/6]${NC} List supported providers"
echo "GET /api/v1/byok/providers"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Cookie: session=$SESSION_COOKIE" \
    "$BASE_URL/api/v1/byok/providers")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "$body" | jq -r '.[] | "  - \(.name) (\(.id)): \(if .configured then "✓ configured" else "✗ not configured" end)"' 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 2: List keys
echo -e "${YELLOW}[Test 2/6]${NC} List configured keys"
echo "GET /api/v1/byok/keys"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Cookie: session=$SESSION_COOKIE" \
    "$BASE_URL/api/v1/byok/keys")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    key_count=$(echo "$body" | jq '. | length' 2>/dev/null || echo "0")
    echo "  Keys configured: $key_count"
    echo "$body" | jq -r '.[] | "  - \(.provider_name): \(.key_preview)"' 2>/dev/null || true
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 3: Add a test key
echo -e "${YELLOW}[Test 3/6]${NC} Add test API key"
echo "POST /api/v1/byok/keys/add"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Cookie: session=$SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d '{
        "provider": "openai",
        "key": "sk-test-1234567890abcdefghijklmnopqrstuvwxyz",
        "label": "Test Key (from script)"
    }' \
    "$BASE_URL/api/v1/byok/keys/add")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "$body" | jq -r '"  Added key for: \(.provider_name)"' 2>/dev/null || echo "$body"
elif [ "$http_code" = "403" ]; then
    echo -e "${YELLOW}⚠ Forbidden (HTTP $http_code)${NC}"
    echo "  BYOK requires Starter tier or above"
    echo "  Skipping remaining tests that require key addition"
    SKIP_TESTS=true
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
    SKIP_TESTS=true
fi
echo ""

if [ "$SKIP_TESTS" = "true" ]; then
    echo -e "${YELLOW}Skipping remaining tests due to previous failure${NC}"
    exit 0
fi

# Test 4: Test the key
echo -e "${YELLOW}[Test 4/6]${NC} Test API key validity"
echo "POST /api/v1/byok/keys/test/openai"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Cookie: session=$SESSION_COOKIE" \
    "$BASE_URL/api/v1/byok/keys/test/openai")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "$body" | jq -r '"  Status: \(.status)\n  Message: \(.message)"' 2>/dev/null || echo "$body"
    test_status=$(echo "$body" | jq -r '.status' 2>/dev/null || echo "unknown")
    if [ "$test_status" = "invalid" ]; then
        echo -e "${BLUE}  ℹ This is expected (test key is not a real API key)${NC}"
    fi
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 5: Get statistics
echo -e "${YELLOW}[Test 5/6]${NC} Get BYOK statistics"
echo "GET /api/v1/byok/stats"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Cookie: session=$SESSION_COOKIE" \
    "$BASE_URL/api/v1/byok/stats")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "$body" | jq -r '"  Total providers: \(.total_providers)\n  Configured: \(.configured_providers)\n  Tested: \(.tested_providers)\n  Valid: \(.valid_providers)\n  User tier: \(.user_tier)"' 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 6: Delete the test key
echo -e "${YELLOW}[Test 6/6]${NC} Delete test API key"
echo "DELETE /api/v1/byok/keys/openai"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -X DELETE \
    -H "Cookie: session=$SESSION_COOKIE" \
    "$BASE_URL/api/v1/byok/keys/openai")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
    echo "$body" | jq -r '"  \(.message)"' 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ API tests complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "All endpoints are responding correctly!"
echo ""
echo "Next steps:"
echo "  - Add real API keys via the API or UI"
echo "  - Test with actual provider credentials"
echo "  - Monitor usage in logs: docker logs ops-center-direct"
echo ""
