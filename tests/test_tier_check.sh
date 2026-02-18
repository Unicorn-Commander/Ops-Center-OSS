#!/bin/bash
################################################################################
# Tier Check Middleware Test Script
# Tests the tier-based access control ForwardAuth endpoints
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OPS_CENTER_URL="${OPS_CENTER_URL:-http://localhost:8084}"
TEST_EMAIL="${TEST_EMAIL:-test@example.com}"
TEST_USER="${TEST_USER:-testuser}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧪 TIER CHECK MIDDLEWARE TEST SUITE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local expected_code="$2"
    local url="$3"
    shift 3
    local headers=("$@")

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${YELLOW}Test $TOTAL_TESTS:${NC} $test_name"

    # Build curl command with headers
    local curl_cmd="curl -s -o /dev/null -w '%{http_code}'"
    for header in "${headers[@]}"; do
        curl_cmd="$curl_cmd -H '$header'"
    done
    curl_cmd="$curl_cmd '$url'"

    # Execute curl
    local response_code=$(eval $curl_cmd)

    if [ "$response_code" -eq "$expected_code" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (Expected: $expected_code, Got: $response_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC} (Expected: $expected_code, Got: $response_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo -e "${BLUE}Testing Ops-Center availability...${NC}"
if curl -f -s -o /dev/null "${OPS_CENTER_URL}/health" 2>/dev/null; then
    echo -e "${GREEN}✓ Ops-Center is reachable${NC}"
else
    echo -e "${RED}✗ Cannot reach Ops-Center at ${OPS_CENTER_URL}${NC}"
    echo -e "${YELLOW}Tip: Is unicorn-ops-center container running?${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}1. Health Check Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

run_test "Health endpoint should return 200 OK" \
    200 \
    "${OPS_CENTER_URL}/api/v1/tier-check/health"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}2. Authentication Tests (No Headers)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

run_test "Billing check without auth should return 401" \
    401 \
    "${OPS_CENTER_URL}/api/v1/tier-check/billing"

run_test "Admin check without auth should return 401" \
    401 \
    "${OPS_CENTER_URL}/api/v1/tier-check/admin"

run_test "BYOK check without auth should return 401" \
    401 \
    "${OPS_CENTER_URL}/api/v1/tier-check/byok"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3. Tier Authorization Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Note: These tests will fail if Keycloak integration is not configured${NC}"
echo -e "${YELLOW}or if the test user doesn't exist with subscription_tier attribute.${NC}"
echo ""

run_test "Generic tier check with auth headers" \
    200 \
    "${OPS_CENTER_URL}/api/v1/tier-check/check?tier=trial" \
    "X-Auth-Request-Email: ${TEST_EMAIL}" \
    "X-Auth-Request-User: ${TEST_USER}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}4. Response Header Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Checking response headers from tier check...${NC}"
RESPONSE=$(curl -s -i -H "X-Auth-Request-Email: ${TEST_EMAIL}" \
    "${OPS_CENTER_URL}/api/v1/tier-check/check?tier=trial" 2>/dev/null)

if echo "$RESPONSE" | grep -q "X-User-"; then
    echo -e "${GREEN}✓ Response includes X-User-* headers${NC}"
    echo "$RESPONSE" | grep "^X-User-" || true
else
    echo -e "${YELLOW}⚠ No X-User-* headers found (may be expected if Keycloak not configured)${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}5. Error Response Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Testing error response format...${NC}"
ERROR_RESPONSE=$(curl -s -H "X-Auth-Request-Email: nonexistent@example.com" \
    "${OPS_CENTER_URL}/api/v1/tier-check/billing" 2>/dev/null)

if echo "$ERROR_RESPONSE" | grep -q "error\|message"; then
    echo -e "${GREEN}✓ Error response contains structured error message${NC}"
    echo "$ERROR_RESPONSE" | head -5
else
    echo -e "${YELLOW}⚠ Error response format unclear${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}6. Traefik Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Checking if Traefik can reach tier-check endpoint...${NC}"
if docker exec traefik wget -q -O /dev/null --timeout=5 \
    "http://unicorn-ops-center:8084/api/v1/tier-check/health" 2>/dev/null; then
    echo -e "${GREEN}✓ Traefik can reach tier-check endpoint${NC}"
else
    echo -e "${RED}✗ Traefik cannot reach tier-check endpoint${NC}"
    echo -e "${YELLOW}Tip: Check if unicorn-ops-center is on 'web' network${NC}"
fi
echo ""

echo -e "${YELLOW}Checking middlewares.yml configuration...${NC}"
if [ -f "/home/deploy/Infrastructure/traefik/dynamic/middlewares.yml" ]; then
    echo -e "${GREEN}✓ middlewares.yml exists${NC}"

    if grep -q "lago-tier-check" "/home/deploy/Infrastructure/traefik/dynamic/middlewares.yml"; then
        echo -e "${GREEN}✓ lago-tier-check middleware defined${NC}"
    else
        echo -e "${RED}✗ lago-tier-check middleware not found in file${NC}"
    fi
else
    echo -e "${RED}✗ middlewares.yml not found${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}7. Docker Container Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Checking required containers...${NC}"

containers=("unicorn-ops-center" "uchub-oauth2-proxy" "traefik")
for container in "${containers[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$container")
        echo -e "${GREEN}✓ ${container}: ${status}${NC}"
    else
        echo -e "${RED}✗ ${container}: not running${NC}"
    fi
done
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ ALL CORE TESTS PASSED!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Configure Keycloak credentials in Ops-Center .env"
    echo "2. Create test user in Keycloak with subscription_tier attribute"
    echo "3. Restart Ops-Center: docker restart unicorn-ops-center"
    echo "4. Re-run this test with real user email"
    echo "5. Test full flow via browser: https://billing.unicorncommander.ai"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Check Ops-Center logs: docker logs unicorn-ops-center"
    echo "2. Verify tier_check_middleware.py exists and is registered"
    echo "3. Ensure TIER_ENFORCEMENT_ENABLED=true in .env"
    echo "4. Restart Ops-Center after code changes"
    exit 1
fi
