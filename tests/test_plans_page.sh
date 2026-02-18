#!/bin/bash
# Comprehensive test suite for plans.html and subscription API
# UC-1 Pro - Plans Page Testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Test URLs
BASE_URL="https://unicorncommander.ai"
PLANS_PAGE="$BASE_URL/plans.html"
API_ENDPOINT="$BASE_URL/api/v1/subscriptions/plans"
SIGNUP_FLOW="$BASE_URL/signup-flow.html"

echo "============================================"
echo "UC-1 Pro Plans Page Test Suite"
echo "============================================"
echo ""

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        ((PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        echo -e "  ${RED}Error: $message${NC}"
        ((FAILED++))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠ WARN${NC} - $test_name"
        echo -e "  ${YELLOW}Warning: $message${NC}"
        ((WARNINGS++))
    fi
}

# Test 1: Plans page HTTP status
echo -e "${BLUE}[1] Testing Plans Page Loading...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PLANS_PAGE")
if [ "$STATUS" = "200" ]; then
    print_result "Plans page HTTP status" "PASS"
else
    print_result "Plans page HTTP status" "FAIL" "Expected 200, got $STATUS"
fi

# Test 2: Plans page content type
CONTENT_TYPE=$(curl -s -I "$PLANS_PAGE" | grep -i "content-type" | awk '{print $2}' | tr -d '\r')
if [[ "$CONTENT_TYPE" == *"text/html"* ]]; then
    print_result "Plans page content type" "PASS"
else
    print_result "Plans page content type" "FAIL" "Expected text/html, got $CONTENT_TYPE"
fi

# Test 3: Plans page size (not empty)
PAGE_SIZE=$(curl -s -o /dev/null -w "%{size_download}" "$PLANS_PAGE")
if [ "$PAGE_SIZE" -gt 5000 ]; then
    print_result "Plans page size (>5KB)" "PASS"
else
    print_result "Plans page size" "WARN" "Page size is $PAGE_SIZE bytes (expected >5000)"
fi

# Test 4: API endpoint HTTP status
echo ""
echo -e "${BLUE}[2] Testing API Endpoint...${NC}"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT")
if [ "$API_STATUS" = "200" ]; then
    print_result "API endpoint HTTP status" "PASS"
else
    print_result "API endpoint HTTP status" "FAIL" "Expected 200, got $API_STATUS"
fi

# Test 5: API response is valid JSON
API_RESPONSE=$(curl -s "$API_ENDPOINT")
if echo "$API_RESPONSE" | jq empty 2>/dev/null; then
    print_result "API response valid JSON" "PASS"
else
    print_result "API response valid JSON" "FAIL" "Response is not valid JSON"
fi

# Test 6: API returns plans array
PLANS_COUNT=$(echo "$API_RESPONSE" | jq '.plans | length' 2>/dev/null || echo "0")
if [ "$PLANS_COUNT" -eq 4 ]; then
    print_result "API returns 4 plans" "PASS"
elif [ "$PLANS_COUNT" -gt 0 ]; then
    print_result "API returns 4 plans" "WARN" "Got $PLANS_COUNT plans instead of 4"
else
    print_result "API returns 4 plans" "FAIL" "No plans returned"
fi

# Test 7: Trial tier exists
echo ""
echo -e "${BLUE}[3] Testing Trial Tier Configuration...${NC}"
TRIAL_EXISTS=$(echo "$API_RESPONSE" | jq '.plans[] | select(.name == "trial")' | jq 'length' 2>/dev/null || echo "0")
if [ "$TRIAL_EXISTS" -gt 0 ]; then
    print_result "Trial tier exists" "PASS"
else
    print_result "Trial tier exists" "FAIL" "Trial tier not found in API response"
fi

# Test 8: Trial tier price is $1
TRIAL_PRICE=$(echo "$API_RESPONSE" | jq -r '.plans[] | select(.name == "trial") | .price_monthly' 2>/dev/null || echo "0")
if [ "$TRIAL_PRICE" = "1" ] || [ "$TRIAL_PRICE" = "1.0" ]; then
    print_result "Trial tier price (\$1/month)" "PASS"
else
    print_result "Trial tier price" "FAIL" "Expected \$1, got \$$TRIAL_PRICE"
fi

# Test 9: Trial tier has 7-day features
TRIAL_FEATURES=$(echo "$API_RESPONSE" | jq -r '.plans[] | select(.name == "trial") | .features[]' 2>/dev/null || echo "")
if echo "$TRIAL_FEATURES" | grep -q "7-day"; then
    print_result "Trial tier 7-day period" "PASS"
else
    print_result "Trial tier 7-day period" "WARN" "7-day period not mentioned in features"
fi

# Test 10: Trial tier API limit (700 = 7 days * 100/day)
TRIAL_LIMIT=$(echo "$API_RESPONSE" | jq -r '.plans[] | select(.name == "trial") | .api_calls_limit' 2>/dev/null || echo "0")
if [ "$TRIAL_LIMIT" = "700" ]; then
    print_result "Trial tier API limit (700 calls)" "PASS"
else
    print_result "Trial tier API limit" "WARN" "Expected 700, got $TRIAL_LIMIT"
fi

# Test 11: All required tier names present
echo ""
echo -e "${BLUE}[4] Testing All Subscription Tiers...${NC}"
TIERS=("trial" "starter" "professional" "enterprise")
for tier in "${TIERS[@]}"; do
    TIER_EXISTS=$(echo "$API_RESPONSE" | jq -r ".plans[] | select(.name == \"$tier\") | .name" 2>/dev/null || echo "")
    if [ "$TIER_EXISTS" = "$tier" ]; then
        print_result "Tier '$tier' exists" "PASS"
    else
        print_result "Tier '$tier' exists" "FAIL" "Tier not found"
    fi
done

# Test 12: Plans have required fields
echo ""
echo -e "${BLUE}[5] Testing Plan Structure...${NC}"
REQUIRED_FIELDS=("name" "display_name" "price_monthly" "features" "services")
FIRST_PLAN=$(echo "$API_RESPONSE" | jq '.plans[0]' 2>/dev/null)
for field in "${REQUIRED_FIELDS[@]}"; do
    HAS_FIELD=$(echo "$FIRST_PLAN" | jq "has(\"$field\")" 2>/dev/null || echo "false")
    if [ "$HAS_FIELD" = "true" ]; then
        print_result "Plan has field '$field'" "PASS"
    else
        print_result "Plan has field '$field'" "FAIL" "Field missing"
    fi
done

# Test 13: Signup flow page exists
echo ""
echo -e "${BLUE}[6] Testing Navigation Flow...${NC}"
SIGNUP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SIGNUP_FLOW")
if [ "$SIGNUP_STATUS" = "200" ]; then
    print_result "Signup flow page exists" "PASS"
else
    print_result "Signup flow page exists" "FAIL" "Expected 200, got $SIGNUP_STATUS"
fi

# Test 14: Plans page contains JavaScript
PLANS_HTML=$(curl -s "$PLANS_PAGE")
if echo "$PLANS_HTML" | grep -q "fetch('/api/v1/subscriptions/plans')"; then
    print_result "Plans page has API fetch call" "PASS"
else
    print_result "Plans page has API fetch call" "FAIL" "fetch() call not found"
fi

# Test 15: Plans page has error handling
if echo "$PLANS_HTML" | grep -q "Failed to load subscription plans"; then
    print_result "Plans page has error handling" "PASS"
else
    print_result "Plans page has error handling" "WARN" "Error message not found"
fi

# Test 16: Plans page has loading state
if echo "$PLANS_HTML" | grep -q "Loading plans..."; then
    print_result "Plans page has loading state" "PASS"
else
    print_result "Plans page has loading state" "WARN" "Loading message not found"
fi

# Test 17: Edge case - Invalid HTTP method
echo ""
echo -e "${BLUE}[7] Testing Edge Cases...${NC}"
POST_RESPONSE=$(curl -s -X POST "$API_ENDPOINT" 2>&1)
if echo "$POST_RESPONSE" | grep -qi "error\|not allowed\|method"; then
    print_result "API rejects POST method" "PASS"
else
    print_result "API rejects POST method" "WARN" "POST might be accepted (should be GET only)"
fi

# Test 18: Edge case - Invalid endpoint
INVALID_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/subscriptions/invalid")
if [ "$INVALID_RESPONSE" = "404" ] || [ "$INVALID_RESPONSE" = "400" ]; then
    print_result "Invalid API endpoint returns error" "PASS"
else
    print_result "Invalid API endpoint returns error" "WARN" "Expected 404, got $INVALID_RESPONSE"
fi

# Test 19: API response time
echo ""
echo -e "${BLUE}[8] Testing Performance...${NC}"
API_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$API_ENDPOINT")
API_TIME_MS=$(echo "$API_TIME * 1000" | bc | cut -d. -f1)
if [ "$API_TIME_MS" -lt 500 ]; then
    print_result "API response time (<500ms)" "PASS"
elif [ "$API_TIME_MS" -lt 1000 ]; then
    print_result "API response time" "WARN" "Took ${API_TIME_MS}ms (acceptable but slow)"
else
    print_result "API response time" "FAIL" "Took ${API_TIME_MS}ms (too slow)"
fi

# Test 20: Page load time
PAGE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$PLANS_PAGE")
PAGE_TIME_MS=$(echo "$PAGE_TIME * 1000" | bc | cut -d. -f1)
if [ "$PAGE_TIME_MS" -lt 1000 ]; then
    print_result "Page load time (<1000ms)" "PASS"
elif [ "$PAGE_TIME_MS" -lt 2000 ]; then
    print_result "Page load time" "WARN" "Took ${PAGE_TIME_MS}ms (acceptable but slow)"
else
    print_result "Page load time" "FAIL" "Took ${PAGE_TIME_MS}ms (too slow)"
fi

# Summary
echo ""
echo "============================================"
echo "Test Summary"
echo "============================================"
echo -e "${GREEN}Passed:  $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed:  $FAILED${NC}"
echo ""

# Test trial tier details
echo "============================================"
echo "Trial Tier Details"
echo "============================================"
echo "$API_RESPONSE" | jq '.plans[] | select(.name == "trial")'
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review.${NC}"
    exit 1
fi
