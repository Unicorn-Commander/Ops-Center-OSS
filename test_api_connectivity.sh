#!/bin/bash

# Ops-Center User Management API Connectivity Test
# Tests all user management endpoints to verify they exist and respond

BASE_URL="http://localhost:8084"
ADMIN_PATH="/api/v1/admin/users"

echo "================================================================"
echo "Ops-Center User Management API Connectivity Test"
echo "================================================================"
echo "Base URL: $BASE_URL"
echo "Test Time: $(date)"
echo "================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL=0
SUCCESS=0
FAIL=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local expected_status=$3
    local description=$4

    TOTAL=$((TOTAL + 1))

    # Make request
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path" 2>&1)
    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    # Check if status matches expected
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $method $path - $status ($description)"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗${NC} $method $path - Expected $expected_status, got $status ($description)"
        echo "  Response: $body"
        FAIL=$((FAIL + 1))
    fi
}

# Function to test OpenAPI schema
test_openapi() {
    echo "================================================================"
    echo "1. OpenAPI Schema Verification"
    echo "================================================================"

    response=$(curl -s "$BASE_URL/openapi.json")

    if echo "$response" | grep -q '"openapi"'; then
        echo -e "${GREEN}✓${NC} OpenAPI schema available"

        # Count user management endpoints
        count=$(echo "$response" | grep -o "/api/v1/admin/users" | wc -l)
        echo -e "${GREEN}✓${NC} Found $count user management endpoints in schema"

        SUCCESS=$((SUCCESS + 2))
        TOTAL=$((TOTAL + 2))
    else
        echo -e "${RED}✗${NC} OpenAPI schema not available"
        FAIL=$((FAIL + 2))
        TOTAL=$((TOTAL + 2))
    fi
    echo ""
}

# Function to test authentication
test_auth() {
    echo "================================================================"
    echo "2. Authentication Layer Verification"
    echo "================================================================"

    # All admin endpoints should return 401 without auth
    test_endpoint "GET" "$ADMIN_PATH" "401" "User list (requires auth)"
    test_endpoint "GET" "$ADMIN_PATH/analytics/summary" "401" "Analytics summary (requires auth)"
    test_endpoint "GET" "$ADMIN_PATH/roles/available" "401" "Available roles (requires auth)"

    echo ""
}

# Function to test endpoint existence
test_endpoints() {
    echo "================================================================"
    echo "3. Endpoint Existence Verification"
    echo "================================================================"

    # Note: We can't fully test POST/PUT/DELETE without auth,
    # but we can verify they exist by checking if they return 401 (not 404)

    echo "Read Endpoints:"
    test_endpoint "GET" "$ADMIN_PATH" "401" "List users"
    test_endpoint "GET" "$ADMIN_PATH/analytics/summary" "401" "Analytics summary"
    test_endpoint "GET" "$ADMIN_PATH/roles/available" "401" "Available roles"
    test_endpoint "GET" "$ADMIN_PATH/export" "401" "Export users CSV"

    echo ""
    echo "User Detail Endpoints:"
    test_endpoint "GET" "$ADMIN_PATH/test-user-id" "401" "Get user details"
    test_endpoint "GET" "$ADMIN_PATH/test-user-id/roles" "401" "Get user roles"
    test_endpoint "GET" "$ADMIN_PATH/test-user-id/sessions" "401" "Get user sessions"
    test_endpoint "GET" "$ADMIN_PATH/test-user-id/activity" "401" "Get user activity"
    test_endpoint "GET" "$ADMIN_PATH/test-user-id/api-keys" "401" "Get API keys"

    echo ""
    echo "Write Endpoints (expecting 401 or 405):"
    # These may return 405 if method not allowed without body
    test_endpoint "POST" "$ADMIN_PATH/test-user-id/reset-password" "401" "Reset password"
    test_endpoint "POST" "$ADMIN_PATH/test-user-id/roles/assign" "401" "Assign role"
    test_endpoint "POST" "$ADMIN_PATH/test-user-id/api-keys" "401" "Generate API key"
    test_endpoint "POST" "$ADMIN_PATH/test-user-id/impersonate/start" "401" "Start impersonation"

    echo ""
    echo "Bulk Operation Endpoints:"
    test_endpoint "POST" "$ADMIN_PATH/bulk/import" "401" "Bulk import"
    test_endpoint "POST" "$ADMIN_PATH/bulk/assign-roles" "401" "Bulk assign roles"
    test_endpoint "POST" "$ADMIN_PATH/bulk/delete" "401" "Bulk delete"
    test_endpoint "POST" "$ADMIN_PATH/bulk/set-tier" "401" "Bulk set tier"

    echo ""
}

# Function to test service health
test_health() {
    echo "================================================================"
    echo "4. Service Health Check"
    echo "================================================================"

    # Check if container is running
    if docker ps | grep -q "ops-center-direct"; then
        echo -e "${GREEN}✓${NC} Container 'ops-center-direct' is running"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗${NC} Container 'ops-center-direct' is NOT running"
        FAIL=$((FAIL + 1))
    fi
    TOTAL=$((TOTAL + 1))

    # Check if API responds
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/system/status" -o /dev/null)
    if [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo -e "${GREEN}✓${NC} API server is responding (status: $response)"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗${NC} API server not responding correctly (status: $response)"
        FAIL=$((FAIL + 1))
    fi
    TOTAL=$((TOTAL + 1))

    echo ""
}

# Function to check database connectivity
test_database() {
    echo "================================================================"
    echo "5. Database Connectivity Check"
    echo "================================================================"

    # Check PostgreSQL
    if docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;" &>/dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL connection successful"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗${NC} PostgreSQL connection failed"
        FAIL=$((FAIL + 1))
    fi
    TOTAL=$((TOTAL + 1))

    # Check if unicorn_db exists
    if docker exec unicorn-postgresql psql -U unicorn -l | grep -q "unicorn_db"; then
        echo -e "${GREEN}✓${NC} Database 'unicorn_db' exists"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}✗${NC} Database 'unicorn_db' does not exist"
        FAIL=$((FAIL + 1))
    fi
    TOTAL=$((TOTAL + 1))

    echo ""
}

# Function to list all registered routes
list_routes() {
    echo "================================================================"
    echo "6. Registered User Management Routes"
    echo "================================================================"

    routes=$(curl -s "$BASE_URL/openapi.json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    paths = sorted([p for p in data.get('paths', {}).keys() if 'admin/users' in p])
    for path in paths:
        methods = list(data['paths'][path].keys())
        print(f'  {path}')
        for method in methods:
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                desc = data['paths'][path][method].get('summary', 'No description')
                print(f'    {method.upper()}: {desc}')
except Exception as e:
    print(f'Error parsing OpenAPI schema: {e}')
" 2>&1)

    if [ -z "$routes" ]; then
        echo -e "${YELLOW}⚠${NC} Could not retrieve route list"
    else
        echo "$routes"
    fi

    echo ""
}

# Run all tests
echo "Starting API connectivity tests..."
echo ""

test_health
test_database
test_openapi
test_auth
test_endpoints
list_routes

# Summary
echo "================================================================"
echo "Test Summary"
echo "================================================================"
echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $SUCCESS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL${NC}"
else
    echo "Failed: 0"
fi
echo ""

# Calculate pass rate
if [ $TOTAL -gt 0 ]; then
    pass_rate=$(echo "scale=1; $SUCCESS * 100 / $TOTAL" | bc)
    echo "Pass Rate: ${pass_rate}%"
else
    echo "Pass Rate: N/A"
fi

echo ""
echo "================================================================"
echo "Conclusion"
echo "================================================================"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Backend is operational. All user management endpoints are:"
    echo "  - Registered and responding"
    echo "  - Properly secured (401 without auth)"
    echo "  - Available in OpenAPI schema"
    echo ""
    echo "Next Step: Manual frontend testing required"
    echo "  URL: https://your-domain.com/admin/system/users"
    echo ""
    echo "See API_CONNECTIVITY_TEST_REPORT.md for detailed testing guide"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Issues detected. Check logs:"
    echo "  docker logs ops-center-direct --tail 100"
    echo ""
    echo "Verify services are running:"
    echo "  docker ps | grep -E 'ops-center|postgresql'"
fi

echo "================================================================"

# Exit with error code if any tests failed
if [ $FAIL -gt 0 ]; then
    exit 1
else
    exit 0
fi
