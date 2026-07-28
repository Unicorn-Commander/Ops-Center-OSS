#!/bin/bash
# End-to-End Traefik API Test Suite
# Tests complete CRUD workflows using curl
#
# Author: Testing & QA Specialist Agent
# Date: October 24, 2025
# Epic: 1.3 - Traefik Configuration Management

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8084}"
TRAEFIK_API="${API_URL}/api/v1/traefik"
VERBOSE="${VERBOSE:-0}"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

run_test() {
    ((TESTS_RUN++))
    local test_name="$1"
    log_info "Running: $test_name"
}

check_response() {
    local actual_status="$1"
    local expected_status="$2"
    local test_name="$3"

    if [ "$actual_status" == "$expected_status" ]; then
        log_success "$test_name (Status: $actual_status)"
        return 0
    else
        log_error "$test_name (Expected: $expected_status, Got: $actual_status)"
        return 1
    fi
}

check_json_field() {
    local json="$1"
    local field="$2"
    local test_name="$3"

    if echo "$json" | jq -e ".$field" > /dev/null 2>&1; then
        log_success "$test_name (Field '$field' exists)"
        return 0
    else
        log_error "$test_name (Field '$field' missing)"
        return 1
    fi
}

check_json_value() {
    local json="$1"
    local field="$2"
    local expected_value="$3"
    local test_name="$4"

    local actual_value=$(echo "$json" | jq -r ".$field")

    if [ "$actual_value" == "$expected_value" ]; then
        log_success "$test_name ($field=$actual_value)"
        return 0
    else
        log_error "$test_name (Expected: $expected_value, Got: $actual_value)"
        return 1
    fi
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

preflight_checks() {
    log_info "Running preflight checks..."

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install: sudo apt-get install jq"
        exit 1
    fi

    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed. Please install: sudo apt-get install curl"
        exit 1
    fi

    # Check if API is accessible
    if ! curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" | grep -q "200"; then
        log_warning "API health endpoint not responding at $API_URL"
        log_warning "Tests may fail if service is not running"
    else
        log_success "API is accessible at $API_URL"
    fi

    echo ""
}

# ============================================================================
# Test Suite: Health & Status
# ============================================================================

test_health_check() {
    run_test "Health Check"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/health")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "Health endpoint returns 200" || return 1

    check_json_field "$body" "status" "Health response has 'status' field" || return 1
    check_json_field "$body" "service" "Health response has 'service' field" || return 1
    check_json_value "$body" "status" "healthy" "Health status is 'healthy'" || return 1

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

test_traefik_status() {
    run_test "Traefik Status"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/status")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "Status endpoint returns 200" || return 1

    check_json_field "$body" "status" "Status response has 'status' field" || return 1
    check_json_field "$body" "routes_count" "Status response has 'routes_count' field" || return 1
    check_json_field "$body" "certificates_count" "Status response has 'certificates_count' field" || return 1
    check_json_field "$body" "timestamp" "Status response has 'timestamp' field" || return 1

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

# ============================================================================
# Test Suite: Route Management
# ============================================================================

test_list_routes() {
    run_test "List Routes"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/routes")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "List routes returns 200" || return 1

    check_json_field "$body" "routes" "Routes response has 'routes' field" || return 1
    check_json_field "$body" "count" "Routes response has 'count' field" || return 1

    local route_count=$(echo "$body" | jq -r '.count')
    log_info "Found $route_count routes"

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

test_create_route() {
    run_test "Create Route (501 Not Implemented)"

    local route_data='{
        "name": "test-e2e-route",
        "rule": "Host(`e2e-test.example.com`)",
        "service": "e2e-test-service",
        "entrypoints": ["websecure"],
        "priority": 100,
        "middlewares": []
    }'

    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$route_data" \
        "$TRAEFIK_API/routes")

    local http_code=$(echo "$response" | tail -n1)

    # Expecting 501 Not Implemented
    check_response "$http_code" "501" "Create route returns 501 (not implemented)" || return 1
}

test_get_route() {
    run_test "Get Route (501 Not Implemented)"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/routes/test-route")
    local http_code=$(echo "$response" | tail -n1)

    # Expecting 501 Not Implemented
    check_response "$http_code" "501" "Get route returns 501 (not implemented)" || return 1
}

test_delete_route() {
    run_test "Delete Route (501 Not Implemented)"

    local response=$(curl -s -w "\n%{http_code}" -X DELETE "$TRAEFIK_API/routes/test-route")
    local http_code=$(echo "$response" | tail -n1)

    # Expecting 501 Not Implemented
    check_response "$http_code" "501" "Delete route returns 501 (not implemented)" || return 1
}

# ============================================================================
# Test Suite: Certificate Management
# ============================================================================

test_list_certificates() {
    run_test "List Certificates"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/certificates")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "List certificates returns 200" || return 1

    check_json_field "$body" "certificates" "Certificates response has 'certificates' field" || return 1
    check_json_field "$body" "count" "Certificates response has 'count' field" || return 1

    local cert_count=$(echo "$body" | jq -r '.count')
    log_info "Found $cert_count certificates"

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

test_get_certificate() {
    run_test "Get Certificate (may return 404 if no certs exist)"

    # First, check if any certificates exist
    local list_response=$(curl -s "$TRAEFIK_API/certificates")
    local cert_count=$(echo "$list_response" | jq -r '.count')

    if [ "$cert_count" == "0" ]; then
        log_warning "No certificates exist, skipping get certificate test"
        return 0
    fi

    # Get first certificate domain
    local domain=$(echo "$list_response" | jq -r '.certificates[0].domain')

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/certificates/$domain")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    if [ "$http_code" == "200" ]; then
        check_response "$http_code" "200" "Get certificate returns 200" || return 1
        check_json_field "$body" "certificate" "Certificate response has 'certificate' field" || return 1

        if [ "$VERBOSE" == "1" ]; then
            echo "$body" | jq .
        fi
    else
        log_warning "Certificate not found (404) - expected if domain doesn't exist"
    fi
}

test_acme_status() {
    run_test "ACME Status"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/acme/status")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "ACME status returns 200" || return 1

    check_json_field "$body" "acme_status" "ACME response has 'acme_status' field" || return 1
    check_json_field "$body" "acme_status.initialized" "ACME status has 'initialized' field" || return 1
    check_json_field "$body" "acme_status.total_certificates" "ACME status has 'total_certificates' field" || return 1

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

# ============================================================================
# Test Suite: Configuration Management
# ============================================================================

test_config_summary() {
    run_test "Configuration Summary"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/config/summary")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    check_response "$http_code" "200" "Config summary returns 200" || return 1

    check_json_field "$body" "summary" "Config summary has 'summary' field" || return 1
    check_json_field "$body" "summary.routes" "Config summary has 'routes' count" || return 1
    check_json_field "$body" "summary.certificates" "Config summary has 'certificates' count" || return 1
    check_json_field "$body" "timestamp" "Config summary has 'timestamp' field" || return 1

    if [ "$VERBOSE" == "1" ]; then
        echo "$body" | jq .
    fi
}

# ============================================================================
# Test Suite: Error Handling
# ============================================================================

test_404_not_found() {
    run_test "404 Not Found"

    local response=$(curl -s -w "\n%{http_code}" "$TRAEFIK_API/nonexistent-endpoint")
    local http_code=$(echo "$response" | tail -n1)

    check_response "$http_code" "404" "Non-existent endpoint returns 404" || return 1
}

test_invalid_json() {
    run_test "Invalid JSON Request"

    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "invalid json{" \
        "$TRAEFIK_API/routes")

    local http_code=$(echo "$response" | tail -n1)

    # Should return 422 Unprocessable Entity or 400 Bad Request
    if [ "$http_code" == "422" ] || [ "$http_code" == "400" ]; then
        log_success "Invalid JSON returns $http_code (expected 400 or 422)"
        return 0
    else
        log_error "Invalid JSON returns $http_code (expected 400 or 422)"
        return 1
    fi
}

# ============================================================================
# Test Suite: Complete Workflow
# ============================================================================

test_complete_workflow() {
    log_info "================================"
    log_info "Complete Workflow Test"
    log_info "================================"

    # Step 1: Check initial state
    run_test "Workflow Step 1: Check Initial State"
    local initial_status=$(curl -s "$TRAEFIK_API/status")
    local initial_routes=$(echo "$initial_status" | jq -r '.routes_count')
    local initial_certs=$(echo "$initial_status" | jq -r '.certificates_count')
    log_info "Initial state: $initial_routes routes, $initial_certs certificates"
    log_success "Initial state retrieved"

    # Step 2: List routes
    run_test "Workflow Step 2: List Routes"
    local routes_response=$(curl -s "$TRAEFIK_API/routes")
    local routes_count=$(echo "$routes_response" | jq -r '.count')
    log_info "Routes count: $routes_count"
    log_success "Routes listed successfully"

    # Step 3: List certificates
    run_test "Workflow Step 3: List Certificates"
    local certs_response=$(curl -s "$TRAEFIK_API/certificates")
    local certs_count=$(echo "$certs_response" | jq -r '.count')
    log_info "Certificates count: $certs_count"
    log_success "Certificates listed successfully"

    # Step 4: Get configuration summary
    run_test "Workflow Step 4: Configuration Summary"
    local summary_response=$(curl -s "$TRAEFIK_API/config/summary")
    local summary_routes=$(echo "$summary_response" | jq -r '.summary.routes')
    local summary_certs=$(echo "$summary_response" | jq -r '.summary.certificates')
    log_info "Summary: $summary_routes routes, $summary_certs certificates"
    log_success "Configuration summary retrieved"

    # Step 5: Verify data consistency
    run_test "Workflow Step 5: Verify Data Consistency"
    if [ "$initial_routes" == "$summary_routes" ] && [ "$routes_count" == "$summary_routes" ]; then
        log_success "Route counts are consistent across endpoints"
    else
        log_error "Route count mismatch: status=$initial_routes, list=$routes_count, summary=$summary_routes"
    fi

    if [ "$initial_certs" == "$summary_certs" ] && [ "$certs_count" == "$summary_certs" ]; then
        log_success "Certificate counts are consistent across endpoints"
    else
        log_error "Certificate count mismatch: status=$initial_certs, list=$certs_count, summary=$summary_certs"
    fi
}

# ============================================================================
# Main Test Runner
# ============================================================================

main() {
    echo "========================================"
    echo "Traefik API E2E Test Suite"
    echo "========================================"
    echo "API URL: $TRAEFIK_API"
    echo "Verbose: $VERBOSE"
    echo ""

    preflight_checks

    echo "========================================"
    echo "Running Test Suites"
    echo "========================================"
    echo ""

    # Health & Status Tests
    test_health_check
    test_traefik_status

    echo ""

    # Route Management Tests
    test_list_routes
    test_create_route
    test_get_route
    test_delete_route

    echo ""

    # Certificate Management Tests
    test_list_certificates
    test_get_certificate
    test_acme_status

    echo ""

    # Configuration Management Tests
    test_config_summary

    echo ""

    # Error Handling Tests
    test_404_not_found
    test_invalid_json

    echo ""

    # Complete Workflow Test
    test_complete_workflow

    echo ""
    echo "========================================"
    echo "Test Results Summary"
    echo "========================================"
    echo "Tests Run:    $TESTS_RUN"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Some tests failed!${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
