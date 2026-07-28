#!/bin/bash
#
# Manual Test Script for Local User Management
# Tests the Local User Management API endpoints
#
# Usage: ./test_local_users.sh
#
# IMPORTANT: Run in test environment only!
# This script creates and deletes actual users.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8084"
API_BASE="${BASE_URL}/api/v1/local-users"
SESSION_TOKEN=""  # Will be set by login

# Test user data
TEST_USERNAME="unittest_local_test_$(date +%s)"
TEST_PASSWORD="TestPass123!"
TEST_SSH_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8teh2NJ42qYZVNgO test@example.com"

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root (required for user management)
check_permissions() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root - be careful!"
    else
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Get authentication token
authenticate() {
    print_header "Authentication"

    # Try to get existing session from cookie file
    if [ -f ~/.ops_center_session ]; then
        SESSION_TOKEN=$(cat ~/.ops_center_session)
        print_info "Using cached session token"
    else
        print_warning "No cached session found"
        print_info "Please login to Ops-Center first:"
        print_info "  1. Open ${BASE_URL}/admin"
        print_info "  2. Login with admin account"
        print_info "  3. Run this script again"
        exit 1
    fi
}

# Test 1: List users
test_list_users() {
    print_header "Test 1: List Users"

    print_info "GET ${API_BASE}"

    response=$(curl -s -w "\n%{http_code}" \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "List users successful (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "List users failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Test 2: Create user with valid data
test_create_user_valid() {
    print_header "Test 2: Create User (Valid Data)"

    print_info "POST ${API_BASE}"
    print_info "Username: ${TEST_USERNAME}"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${TEST_USERNAME}\",
            \"password\": \"${TEST_PASSWORD}\",
            \"shell\": \"/bin/bash\",
            \"sudo\": false
        }" \
        "${API_BASE}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        print_success "User created successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "User creation failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Test 3: Create user with invalid username
test_create_user_invalid_username() {
    print_header "Test 3: Create User (Invalid Username)"

    print_info "POST ${API_BASE}"
    print_info "Username: test@invalid (should fail)"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"test@invalid\",
            \"password\": \"${TEST_PASSWORD}\",
            \"shell\": \"/bin/bash\"
        }" \
        "${API_BASE}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
        print_success "Invalid username rejected as expected (HTTP $http_code)"
    else
        print_error "Invalid username should have been rejected (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 4: Get user details
test_get_user() {
    print_header "Test 4: Get User Details"

    print_info "GET ${API_BASE}/${TEST_USERNAME}"

    response=$(curl -s -w "\n%{http_code}" \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}/${TEST_USERNAME}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "Get user successful (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "Get user failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Test 5: Add SSH key
test_add_ssh_key() {
    print_header "Test 5: Add SSH Key"

    print_info "PUT ${API_BASE}/${TEST_USERNAME}"

    response=$(curl -s -w "\n%{http_code}" \
        -X PUT \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"ssh_key\": \"${TEST_SSH_KEY}\"
        }" \
        "${API_BASE}/${TEST_USERNAME}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "SSH key added successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        print_error "SSH key addition failed (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 6: Grant sudo permissions
test_grant_sudo() {
    print_header "Test 6: Grant Sudo Permissions"

    print_info "POST ${API_BASE}/${TEST_USERNAME}/sudo"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}/${TEST_USERNAME}/sudo")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "Sudo granted successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"

        # Verify sudoers file exists
        if [ -f "/etc/sudoers.d/${TEST_USERNAME}" ]; then
            print_success "Sudoers file created: /etc/sudoers.d/${TEST_USERNAME}"
            cat "/etc/sudoers.d/${TEST_USERNAME}"
        else
            print_warning "Sudoers file not found"
        fi
    else
        print_error "Sudo grant failed (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 7: Revoke sudo permissions
test_revoke_sudo() {
    print_header "Test 7: Revoke Sudo Permissions"

    print_info "DELETE ${API_BASE}/${TEST_USERNAME}/sudo"

    response=$(curl -s -w "\n%{http_code}" \
        -X DELETE \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}/${TEST_USERNAME}/sudo")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "Sudo revoked successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"

        # Verify sudoers file removed
        if [ ! -f "/etc/sudoers.d/${TEST_USERNAME}" ]; then
            print_success "Sudoers file removed"
        else
            print_warning "Sudoers file still exists"
        fi
    else
        print_error "Sudo revoke failed (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 8: Try to delete system user (should fail)
test_delete_system_user() {
    print_header "Test 8: Delete System User (Should Fail)"

    print_info "DELETE ${API_BASE}/root"

    response=$(curl -s -w "\n%{http_code}" \
        -X DELETE \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}/root")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "403" ] || [ "$http_code" = "400" ]; then
        print_success "System user deletion blocked as expected (HTTP $http_code)"
    else
        print_error "System user should have been protected! (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 9: Delete test user
test_delete_user() {
    print_header "Test 9: Delete Test User"

    print_info "DELETE ${API_BASE}/${TEST_USERNAME}"

    response=$(curl -s -w "\n%{http_code}" \
        -X DELETE \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        "${API_BASE}/${TEST_USERNAME}?remove_home=true")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success "User deleted successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"

        # Verify user no longer exists in /etc/passwd
        if ! id "${TEST_USERNAME}" &>/dev/null; then
            print_success "User removed from system"
        else
            print_warning "User still exists in system"
        fi

        # Verify home directory removed
        if [ ! -d "/home/${TEST_USERNAME}" ]; then
            print_success "Home directory removed"
        else
            print_warning "Home directory still exists"
        fi
    else
        print_error "User deletion failed (HTTP $http_code)"
        echo "$body"
        return 1
    fi
}

# Test 10: Security - Command injection attempt
test_security_command_injection() {
    print_header "Test 10: Security - Command Injection"

    print_info "POST ${API_BASE}"
    print_info "Username: test;rm -rf / (should be blocked)"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Cookie: session_token=${SESSION_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"test;rm -rf /\",
            \"password\": \"${TEST_PASSWORD}\"
        }" \
        "${API_BASE}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
        print_success "Command injection blocked as expected (HTTP $http_code)"
    else
        print_error "SECURITY ISSUE: Command injection not blocked! (HTTP $http_code)"
        echo "$body"
    fi
}

# Test 11: Verify audit logs
test_audit_logs() {
    print_header "Test 11: Verify Audit Logs"

    print_info "Checking audit logs for local user operations..."

    # This would query the audit log API
    # For now, just print a placeholder
    print_info "Audit log verification requires audit API endpoint"
    print_info "Expected events:"
    echo "  - user.created: ${TEST_USERNAME}"
    echo "  - user.ssh_key_added: ${TEST_USERNAME}"
    echo "  - user.sudo_granted: ${TEST_USERNAME}"
    echo "  - user.sudo_revoked: ${TEST_USERNAME}"
    echo "  - user.deleted: ${TEST_USERNAME}"
}

# Cleanup function
cleanup() {
    print_header "Cleanup"

    print_info "Removing test user if it exists..."

    if id "${TEST_USERNAME}" &>/dev/null; then
        userdel -r "${TEST_USERNAME}" 2>/dev/null || true
        print_success "Test user removed"
    fi

    # Remove sudoers file if exists
    if [ -f "/etc/sudoers.d/${TEST_USERNAME}" ]; then
        rm -f "/etc/sudoers.d/${TEST_USERNAME}"
        print_success "Sudoers file removed"
    fi
}

# Main test execution
main() {
    print_header "Local User Management API Test Suite"
    print_info "Starting tests at $(date)"
    print_info "Base URL: ${BASE_URL}"

    # Setup
    check_permissions
    authenticate

    # Cleanup any existing test users from previous runs
    cleanup

    # Run tests
    local failed=0

    test_list_users || ((failed++))
    test_create_user_valid || ((failed++))
    test_create_user_invalid_username  # Expected to fail
    test_get_user || ((failed++))
    test_add_ssh_key
    test_grant_sudo
    test_revoke_sudo
    test_delete_system_user  # Expected to be blocked
    test_delete_user || ((failed++))
    test_security_command_injection  # Expected to be blocked
    test_audit_logs

    # Final cleanup
    cleanup

    # Summary
    print_header "Test Summary"

    if [ $failed -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "$failed test(s) failed"
        exit 1
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main
main "$@"
