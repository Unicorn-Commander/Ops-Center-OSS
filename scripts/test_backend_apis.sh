#!/bin/bash
# Backend API Verification Script
# Tests Platform Settings, Local Users, and BYOK APIs
# Created: October 25, 2025

set -e  # Exit on error

BASE_URL="http://localhost:8084"
RESULTS_FILE="/tmp/backend_api_test_results_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$RESULTS_FILE"
}

success() {
    echo -e "${GREEN}✓ PASS:${NC} $1" | tee -a "$RESULTS_FILE"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

failure() {
    echo -e "${RED}✗ FAIL:${NC} $1" | tee -a "$RESULTS_FILE"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

warning() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1" | tee -a "$RESULTS_FILE"
}

# Test helper function
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local description="$3"
    local expected_status="${4:-200}"
    local data="$5"

    log "Testing: $description"
    log "  Method: $method $endpoint"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" -H "Content-Type: application/json" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" -eq "$expected_status" ]; then
        success "$description (HTTP $status_code)"
        if command -v jq &> /dev/null && [ -n "$body" ]; then
            echo "$body" | jq '.' >> "$RESULTS_FILE" 2>&1 || echo "$body" >> "$RESULTS_FILE"
        else
            echo "$body" >> "$RESULTS_FILE"
        fi
    else
        failure "$description (Expected HTTP $expected_status, got $status_code)"
        echo "Response: $body" >> "$RESULTS_FILE"
    fi

    echo "" >> "$RESULTS_FILE"
}

# Start testing
log "=========================================="
log "Backend API Verification Test Suite"
log "=========================================="
log "Base URL: $BASE_URL"
log "Results: $RESULTS_FILE"
log ""

# ============================================================================
# H20: PLATFORM SETTINGS API TESTS
# ============================================================================
log "=========================================="
log "H20: Platform Settings API Tests"
log "=========================================="

# Test 1: Get platform settings
test_endpoint "GET" "/api/v1/platform/settings" \
    "Get all platform settings" 200

# Test 2: Get settings by category
test_endpoint "GET" "/api/v1/platform/settings?category=stripe" \
    "Get Stripe settings" 200

test_endpoint "GET" "/api/v1/platform/settings?category=lago" \
    "Get Lago settings" 200

test_endpoint "GET" "/api/v1/platform/settings?category=keycloak" \
    "Get Keycloak settings" 200

# Test 3: Update settings (will likely fail without auth, but tests endpoint exists)
test_endpoint "PUT" "/api/v1/platform/settings" \
    "Update platform settings" 401 \
    '{"settings": {"TEST_KEY": "test_value"}}'

# Test 4: Test connection (will likely fail without auth)
test_endpoint "POST" "/api/v1/platform/settings/test" \
    "Test platform connection" 401 \
    '{"category": "stripe", "credentials": {}}'

# ============================================================================
# H21: LOCAL USERS API TESTS
# ============================================================================
log "=========================================="
log "H21: Local Users API Tests"
log "=========================================="

# Test 1: List local users
test_endpoint "GET" "/api/v1/admin/system/local-users" \
    "List all local users" 200

# Test 2: List available groups
test_endpoint "GET" "/api/v1/admin/system/local-users/groups" \
    "List available system groups" 200

# Test 3: Get specific user (will fail if user doesn't exist, but tests endpoint)
test_endpoint "GET" "/api/v1/admin/system/local-users/muut" \
    "Get specific user details" 200

# Test 4: Create user (will likely fail without auth)
test_endpoint "POST" "/api/v1/admin/system/local-users" \
    "Create new local user" 401 \
    '{"username": "testuser", "password": "TestPass123!", "groups": ["users"]}'

# Test 5: SSH key management endpoints exist
test_endpoint "GET" "/api/v1/admin/system/local-users/muut/ssh-keys" \
    "List SSH keys for user" 200

# Test 6: Add SSH key (will fail without auth, but tests endpoint)
test_endpoint "POST" "/api/v1/admin/system/local-users/muut/ssh-keys" \
    "Add SSH key" 401 \
    '{"key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC test@example.com"}'

# Test 7: Delete SSH key (will fail without proper key_id)
test_endpoint "DELETE" "/api/v1/admin/system/local-users/muut/ssh-keys/1" \
    "Delete SSH key by ID" 401

# ============================================================================
# H22: BYOK API TESTS
# ============================================================================
log "=========================================="
log "H22: BYOK (Bring Your Own Key) API Tests"
log "=========================================="

# Test 1: List supported providers
test_endpoint "GET" "/api/v1/byok/providers" \
    "List supported BYOK providers" 200

# Test 2: List user's API keys (will fail without auth)
test_endpoint "GET" "/api/v1/byok/keys" \
    "List user's API keys" 401

# Test 3: Add API key (will fail without auth)
test_endpoint "POST" "/api/v1/byok/keys" \
    "Add new API key" 401 \
    '{"provider": "openai", "key": "sk-test123456789", "label": "Test Key"}'

# Test 4: Test API key (will fail without auth)
test_endpoint "POST" "/api/v1/byok/keys/test" \
    "Test API key validity" 401 \
    '{"provider": "openai", "key": "sk-test123456789"}'

# Test 5: Delete API key (will fail without auth)
test_endpoint "DELETE" "/api/v1/byok/keys/openai" \
    "Delete API key" 401

# Test 6: Get API key usage stats (will fail without auth)
test_endpoint "GET" "/api/v1/byok/usage" \
    "Get BYOK usage statistics" 401

# ============================================================================
# FRONTEND INTEGRATION VERIFICATION
# ============================================================================
log "=========================================="
log "Frontend Integration Verification"
log "=========================================="

# Check if frontend files exist
log "Checking frontend files..."

if [ -f "src/pages/PlatformSettings.jsx" ]; then
    success "Platform Settings frontend exists"
else
    failure "Platform Settings frontend missing"
fi

if [ -f "src/components/LocalUserManagement/index.jsx" ]; then
    success "Local User Management frontend exists"
else
    failure "Local User Management frontend missing"
fi

if [ -f "src/pages/account/AccountAPIKeys.jsx" ]; then
    success "Account API Keys frontend exists"
else
    failure "Account API Keys frontend missing"
fi

if [ -f "src/components/APIKeysManager.jsx" ]; then
    success "API Keys Manager component exists"
else
    failure "API Keys Manager component missing"
fi

# ============================================================================
# API ENDPOINT DOCUMENTATION CHECK
# ============================================================================
log "=========================================="
log "API Documentation Check"
log "=========================================="

# Check if OpenAPI/Swagger docs are available
test_endpoint "GET" "/docs" \
    "OpenAPI documentation available" 200

test_endpoint "GET" "/openapi.json" \
    "OpenAPI spec available" 200

# ============================================================================
# SECURITY VERIFICATION
# ============================================================================
log "=========================================="
log "Security Verification"
log "=========================================="

log "Checking authentication requirements..."

# These should all return 401 Unauthorized without proper auth
test_endpoint "POST" "/api/v1/platform/settings" \
    "Platform settings require auth" 401 \
    '{"settings": {}}'

test_endpoint "POST" "/api/v1/admin/system/local-users" \
    "Local user creation requires auth" 401 \
    '{"username": "test"}'

test_endpoint "POST" "/api/v1/byok/keys" \
    "BYOK key addition requires auth" 401 \
    '{"provider": "openai", "key": "test"}'

# ============================================================================
# SUMMARY
# ============================================================================
log ""
log "=========================================="
log "Test Summary"
log "=========================================="
log "Total Tests: $TESTS_TOTAL"
log "Passed: $TESTS_PASSED"
log "Failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    log "${GREEN}All tests passed!${NC}"
    log ""
    log "Backend API Verification: SUCCESS ✓"
else
    log "${RED}Some tests failed.${NC}"
    log ""
    log "Backend API Verification: PARTIAL (Review failures)"
fi

log ""
log "Full results saved to: $RESULTS_FILE"
log ""

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
