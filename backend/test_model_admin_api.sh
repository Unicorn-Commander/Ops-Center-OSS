#!/bin/bash
# ============================================================================
# Model Admin API Test Suite
# Tests all CRUD operations for model management
#
# Prerequisites:
# - ops-center-direct container running
# - Admin user logged in (session cookie)
# - PostgreSQL with model_access_control table
#
# Usage: bash test_model_admin_api.sh
# ============================================================================

set -e

BASE_URL="http://localhost:8084/api/v1/models/admin"
SESSION_COOKIE="session_token=YOUR_SESSION_TOKEN_HERE"

echo "========================================="
echo "Model Admin API Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for tests
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"

    echo -e "${YELLOW}Testing: ${name}${NC}"

    if [ -z "$data" ]; then
        response=$(curl -s -X "$method" \
            -H "Cookie: $SESSION_COOKIE" \
            -H "Content-Type: application/json" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -X "$method" \
            -H "Cookie: $SESSION_COOKIE" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    if echo "$response" | grep -q "error\|Error\|401\|403\|500"; then
        echo -e "${RED}❌ FAILED${NC}"
        echo "Response: $response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASSED${NC}"
        echo "Response: $response" | jq '.' 2>/dev/null || echo "$response"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
    echo ""
}

# ============================================================================
# Test 1: List Models (no filters)
# ============================================================================
echo "========================================="
echo "Test 1: List All Models"
echo "========================================="
test_endpoint \
    "GET /models (all models)" \
    "GET" \
    "/models?limit=10&page=1"

echo ""

# ============================================================================
# Test 2: List Models with Filters
# ============================================================================
echo "========================================="
echo "Test 2: List Models with Filters"
echo "========================================="

test_endpoint \
    "GET /models (filter by provider)" \
    "GET" \
    "/models?provider=openrouter&limit=10"

test_endpoint \
    "GET /models (filter by enabled)" \
    "GET" \
    "/models?enabled=true&limit=10"

test_endpoint \
    "GET /models (filter by tier)" \
    "GET" \
    "/models?tier=professional&limit=10"

test_endpoint \
    "GET /models (search)" \
    "GET" \
    "/models?search=gpt&limit=10"

echo ""

# ============================================================================
# Test 3: Create Model
# ============================================================================
echo "========================================="
echo "Test 3: Create New Model"
echo "========================================="

test_endpoint \
    "POST /models (create)" \
    "POST" \
    "/models" \
    '{
        "model_id": "test-model-123",
        "provider": "test-provider",
        "display_name": "Test Model GPT-4",
        "description": "Test model for API validation",
        "tier_access": ["trial", "starter", "professional"],
        "pricing": {
            "input_per_1k": 0.01,
            "output_per_1k": 0.03
        },
        "tier_markup": {
            "trial": 2.0,
            "starter": 1.5,
            "professional": 1.2
        },
        "context_length": 8192,
        "max_output_tokens": 4096,
        "supports_vision": false,
        "supports_function_calling": true,
        "supports_streaming": true,
        "model_family": "gpt-4",
        "enabled": true
    }'

echo ""

# ============================================================================
# Test 4: Get Model Details
# ============================================================================
echo "========================================="
echo "Test 4: Get Model Details"
echo "========================================="

test_endpoint \
    "GET /models/{model_id}" \
    "GET" \
    "/models/test-model-123"

echo ""

# ============================================================================
# Test 5: Update Model
# ============================================================================
echo "========================================="
echo "Test 5: Update Model"
echo "========================================="

test_endpoint \
    "PUT /models/{model_id} (update)" \
    "PUT" \
    "/models/test-model-123" \
    '{
        "display_name": "Test Model GPT-4 (Updated)",
        "description": "Updated test model",
        "pricing": {
            "input_per_1k": 0.02,
            "output_per_1k": 0.04
        }
    }'

echo ""

# ============================================================================
# Test 6: Toggle Model (Enable/Disable)
# ============================================================================
echo "========================================="
echo "Test 6: Toggle Model Status"
echo "========================================="

test_endpoint \
    "PATCH /models/{model_id}/toggle (disable)" \
    "PATCH" \
    "/models/test-model-123/toggle"

test_endpoint \
    "PATCH /models/{model_id}/toggle (re-enable)" \
    "PATCH" \
    "/models/test-model-123/toggle"

echo ""

# ============================================================================
# Test 7: Model Stats
# ============================================================================
echo "========================================="
echo "Test 7: Model Statistics"
echo "========================================="

test_endpoint \
    "GET /models/stats/summary" \
    "GET" \
    "/models/stats/summary"

echo ""

# ============================================================================
# Test 8: Delete Model (Cleanup)
# ============================================================================
echo "========================================="
echo "Test 8: Delete Model"
echo "========================================="

test_endpoint \
    "DELETE /models/{model_id}" \
    "DELETE" \
    "/models/test-model-123"

echo ""

# ============================================================================
# Test 9: Validation Tests (Should Fail)
# ============================================================================
echo "========================================="
echo "Test 9: Validation Tests"
echo "========================================="

echo "Testing invalid tier codes (should fail)..."
curl -s -X POST \
    -H "Cookie: $SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d '{
        "model_id": "invalid-tier-test",
        "provider": "test",
        "display_name": "Invalid Tier Test",
        "tier_access": ["invalid_tier"],
        "pricing": {"input_per_1k": 0.01, "output_per_1k": 0.03}
    }' \
    "$BASE_URL/models" | jq '.'

echo ""
echo "Testing negative pricing (should fail)..."
curl -s -X POST \
    -H "Cookie: $SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d '{
        "model_id": "negative-price-test",
        "provider": "test",
        "display_name": "Negative Price Test",
        "tier_access": ["trial"],
        "pricing": {"input_per_1k": -0.01, "output_per_1k": 0.03}
    }' \
    "$BASE_URL/models" | jq '.'

echo ""
echo "Testing duplicate model_id (should fail)..."
# First create a model
curl -s -X POST \
    -H "Cookie: $SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d '{
        "model_id": "duplicate-test",
        "provider": "test",
        "display_name": "Duplicate Test",
        "tier_access": ["trial"],
        "pricing": {"input_per_1k": 0.01, "output_per_1k": 0.03}
    }' \
    "$BASE_URL/models" > /dev/null

# Try to create again (should fail)
curl -s -X POST \
    -H "Cookie: $SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d '{
        "model_id": "duplicate-test",
        "provider": "test",
        "display_name": "Duplicate Test 2",
        "tier_access": ["trial"],
        "pricing": {"input_per_1k": 0.01, "output_per_1k": 0.03}
    }' \
    "$BASE_URL/models" | jq '.'

# Cleanup
curl -s -X DELETE \
    -H "Cookie: $SESSION_COOKIE" \
    "$BASE_URL/models/duplicate-test" > /dev/null

echo ""

# ============================================================================
# Test 10: Pagination
# ============================================================================
echo "========================================="
echo "Test 10: Pagination"
echo "========================================="

test_endpoint \
    "GET /models (page 1)" \
    "GET" \
    "/models?limit=5&page=1"

test_endpoint \
    "GET /models (page 2)" \
    "GET" \
    "/models?limit=5&page=2"

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
