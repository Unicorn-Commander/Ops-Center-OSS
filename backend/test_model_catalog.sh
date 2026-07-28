#!/bin/bash
# Model Catalog API - Testing Script
# Tests all endpoints to verify functionality
# Author: Backend Developer
# Date: October 27, 2025

BASE_URL="http://localhost:8084"
API_PREFIX="/api/v1/llm"

echo "======================================"
echo "Model Catalog API - Test Suite"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="$3"

    echo -n "Testing: $name ... "

    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))

        # Show sample data
        if [ "$expected_status" -eq 200 ]; then
            echo "$body" | jq -r 'if .total then "  -> Total models: \(.total)" elif .success then "  -> \(.message)" else "  -> Response: \(.)" end' 2>/dev/null || echo "  -> OK"
        fi
    else
        echo -e "${RED}FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        FAILED=$((FAILED + 1))
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
    echo ""
}

# Test 1: List all models
test_endpoint "List all models" "$API_PREFIX/models?limit=10" 200

# Test 2: Filter by provider
test_endpoint "Filter by OpenRouter" "$API_PREFIX/models?provider=openrouter&limit=5" 200

# Test 3: Filter by Anthropic
test_endpoint "Filter by Anthropic" "$API_PREFIX/models?provider=anthropic" 200

# Test 4: Search models
test_endpoint "Search for 'claude'" "$API_PREFIX/models?search=claude&limit=5" 200

# Test 5: Filter by capability
test_endpoint "Filter by vision capability" "$API_PREFIX/models?capability=vision&limit=5" 200

# Test 6: Filter by enabled status
test_endpoint "Filter enabled models" "$API_PREFIX/models?enabled=true&limit=5" 200

# Test 7: Sort by price
test_endpoint "Sort by price" "$API_PREFIX/models?sort=price&limit=5" 200

# Test 8: Sort by context length
test_endpoint "Sort by context length" "$API_PREFIX/models?sort=context_length&limit=5" 200

# Test 9: Get model statistics
test_endpoint "Get model statistics" "$API_PREFIX/models/stats" 200

# Test 10: List providers
test_endpoint "List providers" "$API_PREFIX/providers" 200

# Test 11: Get specific model (Claude 3.5 Sonnet)
test_endpoint "Get Claude 3.5 Sonnet details" "$API_PREFIX/models/anthropic/claude-3-5-sonnet-20241022" 200

# Test 12: Get non-existent model (should fail)
test_endpoint "Get non-existent model" "$API_PREFIX/models/invalid/model-xyz" 404

# Test 13: Pagination test
test_endpoint "Pagination (offset=10, limit=5)" "$API_PREFIX/models?offset=10&limit=5" 200

# Test 14: Combined filters
test_endpoint "Combined filters" "$API_PREFIX/models?provider=openrouter&capability=vision&enabled=true&sort=price&limit=10" 200

echo "======================================"
echo "Test Results"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
