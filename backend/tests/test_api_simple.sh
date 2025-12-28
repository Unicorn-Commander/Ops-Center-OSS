#!/bin/bash
# ============================================================================
# Extensions Marketplace API Test Script
# ============================================================================
# Simple curl-based tests for all 25 endpoints
# Run: bash tests/test_api_simple.sh
# ============================================================================

BASE_URL="http://localhost:8084"
PASSED=0
FAILED=0
TOTAL=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=$4
    local extra_args="${5:-}"

    TOTAL=$((TOTAL + 1))

    echo -n "Test $TOTAL: $description... "

    response=$(curl -s -w "\n%{http_code}" -X $method \
        -H "Content-Type: application/json" \
        $extra_args \
        "$BASE_URL$endpoint" 2>&1)

    status_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC} ($status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "============================================================================"
echo "Extensions Marketplace API Tests"
echo "============================================================================"
echo ""

echo "=== CATALOG API TESTS (6 endpoints) ==="

# 1. List catalog
test_endpoint "GET" "/api/v1/extensions/catalog" "List catalog" "200"

# 2. List catalog with filter
test_endpoint "GET" "/api/v1/extensions/catalog?category=Analytics" "List catalog (filtered)" "200"

# 3. Get specific add-on
test_endpoint "GET" "/api/v1/extensions/1" "Get add-on by ID" "200"

# 4. List categories
test_endpoint "GET" "/api/v1/extensions/categories/list" "List categories" "200"

# 5. Featured add-ons
test_endpoint "GET" "/api/v1/extensions/featured" "Get featured add-ons" "200"

# 6. Search add-ons
test_endpoint "GET" "/api/v1/extensions/search?q=analytics" "Search add-ons" "200"

echo ""
echo "=== CART API TESTS (6 endpoints) ==="

# 7. Get cart (unauthenticated - should fail)
test_endpoint "GET" "/api/v1/cart" "Get cart (no auth)" "401"

# 8. Get cart (with session)
test_endpoint "GET" "/api/v1/cart" "Get cart (with auth)" "200" \
    "--cookie 'session_token=test-session-token-user'"

# 9. Add to cart
test_endpoint "POST" "/api/v1/cart/add?addon_id=1&quantity=2" "Add to cart" "200" \
    "--cookie 'session_token=test-session-token-user'"

# 10. Update cart item (need to get cart_item_id first)
CART_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/cart" --cookie "session_token=test-session-token-user")
CART_ITEM_ID=$(echo "$CART_RESPONSE" | grep -o '"cart_item_id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ ! -z "$CART_ITEM_ID" ]; then
    test_endpoint "PUT" "/api/v1/cart/$CART_ITEM_ID?quantity=3" "Update cart quantity" "200" \
        "--cookie 'session_token=test-session-token-user'"
else
    echo "Test 10: Update cart quantity... ${YELLOW}SKIP${NC} (no items in cart)"
    TOTAL=$((TOTAL + 1))
fi

# 11. Remove from cart
if [ ! -z "$CART_ITEM_ID" ]; then
    test_endpoint "DELETE" "/api/v1/cart/$CART_ITEM_ID" "Remove from cart" "200" \
        "--cookie 'session_token=test-session-token-user'"
else
    echo "Test 11: Remove from cart... ${YELLOW}SKIP${NC} (no items in cart)"
    TOTAL=$((TOTAL + 1))
fi

# 12. Clear cart
test_endpoint "DELETE" "/api/v1/cart/clear" "Clear cart" "200" \
    "--cookie 'session_token=test-session-token-user'"

echo ""
echo "=== PURCHASE API TESTS (8 endpoints) ==="

# Add item back to cart for purchase tests
curl -s -X POST "$BASE_URL/api/v1/cart/add?addon_id=1&quantity=1" \
    --cookie "session_token=test-session-token-user" > /dev/null

# 13. Create checkout session
test_endpoint "POST" "/api/v1/extensions/checkout" "Create checkout session" "200" \
    '--cookie "session_token=test-session-token-user" -d "{\"success_url\": \"https://example.com/success\", \"cancel_url\": \"https://example.com/cancel\"}"'

# 14. Stripe webhook (will fail signature validation - expected)
test_endpoint "POST" "/api/v1/extensions/webhook/stripe" "Stripe webhook" "400" \
    '-H "Stripe-Signature: invalid" -d "{}"'

# 15. List purchases
test_endpoint "GET" "/api/v1/extensions/purchases" "List purchases" "200" \
    "--cookie 'session_token=test-session-token-user'"

# 16. Activate purchase (may not have any purchases)
PURCHASES=$(curl -s -X GET "$BASE_URL/api/v1/extensions/purchases" --cookie "session_token=test-session-token-user")
PURCHASE_ID=$(echo "$PURCHASES" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ ! -z "$PURCHASE_ID" ]; then
    test_endpoint "POST" "/api/v1/extensions/purchases/$PURCHASE_ID/activate" "Activate purchase" "200" \
        "--cookie 'session_token=test-session-token-user'"
else
    echo "Test 16: Activate purchase... ${YELLOW}SKIP${NC} (no purchases)"
    TOTAL=$((TOTAL + 1))
fi

# 17. List active add-ons
test_endpoint "GET" "/api/v1/extensions/active" "List active add-ons" "200" \
    "--cookie 'session_token=test-session-token-user'"

# 18. Apply promo code (may not exist)
test_endpoint "POST" "/api/v1/extensions/promo/apply" "Apply promo code" "404" \
    '--cookie "session_token=test-session-token-user" -d "{\"code\": \"WELCOME25\"}"'

# 19. Cancel purchase
if [ ! -z "$PURCHASE_ID" ]; then
    test_endpoint "POST" "/api/v1/extensions/purchases/$PURCHASE_ID/cancel" "Cancel purchase" "200" \
        "--cookie 'session_token=test-session-token-user'"
else
    echo "Test 19: Cancel purchase... ${YELLOW}SKIP${NC} (no purchases)"
    TOTAL=$((TOTAL + 1))
fi

# 20. Get invoice
if [ ! -z "$PURCHASE_ID" ]; then
    test_endpoint "GET" "/api/v1/extensions/purchases/$PURCHASE_ID/invoice" "Get invoice" "404" \
        "--cookie 'session_token=test-session-token-user'"
else
    echo "Test 20: Get invoice... ${YELLOW}SKIP${NC} (no purchases)"
    TOTAL=$((TOTAL + 1))
fi

echo ""
echo "=== ADMIN API TESTS (5 endpoints) ==="

# 21. Create add-on (admin only)
test_endpoint "POST" "/api/v1/admin/extensions/addons" "Create add-on (admin)" "200" \
    '--cookie "session_token=test-session-token-admin" -d "{\"name\": \"Test Add-on\", \"description\": \"Test\", \"category\": \"Productivity\", \"base_price\": 9.99, \"billing_type\": \"monthly\", \"features\": {\"test\": true}}"'

# 22. Update add-on
test_endpoint "PUT" "/api/v1/admin/extensions/addons/1" "Update add-on" "200" \
    '--cookie "session_token=test-session-token-admin" -d "{\"name\": \"Updated Add-on\", \"base_price\": 19.99}"'

# 23. Delete add-on (soft delete)
test_endpoint "DELETE" "/api/v1/admin/extensions/addons/999" "Soft delete add-on" "404" \
    "--cookie 'session_token=test-session-token-admin'"

# 24. Sales analytics
test_endpoint "GET" "/api/v1/admin/extensions/analytics" "Sales analytics" "200" \
    "--cookie 'session_token=test-session-token-admin'"

# 25. Create promo code
test_endpoint "POST" "/api/v1/admin/extensions/promo" "Create promo code" "200" \
    '--cookie "session_token=test-session-token-admin" -d "{\"code\": \"TEST20\", \"discount_type\": \"percentage\", \"discount_value\": 20.0, \"valid_until\": \"2025-12-31T23:59:59\"}"'

echo ""
echo "============================================================================"
echo "Test Summary"
echo "============================================================================"
echo -e "Total Tests:  $TOTAL"
echo -e "Passed:       ${GREEN}$PASSED${NC}"
echo -e "Failed:       ${RED}$FAILED${NC}"
echo -e "Success Rate: $(( PASSED * 100 / TOTAL ))%"
echo "============================================================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
