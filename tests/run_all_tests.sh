#!/bin/bash
#
# Master Test Runner for UC-1 Pro Billing System
# Runs complete test suite with setup, execution, and cleanup
#
# Usage: ./run_all_tests.sh [options]
#
# Options:
#   --no-setup    Skip test user setup
#   --no-cleanup  Skip test user cleanup
#   --quick       Run only quick tests (skip slow tests)
#   --e2e-only    Run only E2E tests
#   --integration-only  Run only integration tests
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR="$SCRIPT_DIR"

# Parse arguments
SKIP_SETUP=false
SKIP_CLEANUP=false
QUICK_MODE=false
E2E_ONLY=false
INTEGRATION_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-setup)
            SKIP_SETUP=true
            shift
            ;;
        --no-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --e2e-only)
            E2E_ONLY=true
            shift
            ;;
        --integration-only)
            INTEGRATION_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Print functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Start
print_header "UC-1 PRO BILLING SYSTEM - TEST RUNNER"
echo "Start Time: $(date)"
echo "Test Directory: $TEST_DIR"
echo ""

# Check environment
print_header "ENVIRONMENT CHECK"

required_vars=("KEYCLOAK_URL" "KEYCLOAK_REALM" "KEYCLOAK_ADMIN_USERNAME" "KEYCLOAK_ADMIN_PASSWORD")
missing_vars=0

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "$var not set"
        ((missing_vars++))
    else
        print_success "$var is set"
    fi
done

if [ $missing_vars -gt 0 ]; then
    print_error "Missing required environment variables!"
    print_info "Load .env.test file or set variables manually"
    exit 1
fi

# Check dependencies
print_header "DEPENDENCY CHECK"

if command -v pytest &> /dev/null; then
    print_success "pytest installed"
else
    print_error "pytest not found"
    print_info "Run: pip install -r requirements-test.txt"
    exit 1
fi

if command -v python3 &> /dev/null; then
    print_success "python3 installed"
else
    print_error "python3 not found"
    exit 1
fi

# Setup test users
if [ "$SKIP_SETUP" = false ] && [ "$INTEGRATION_ONLY" = false ]; then
    print_header "SETTING UP TEST USERS"

    cd "$TEST_DIR"
    if python3 setup_test_data.py --setup; then
        print_success "Test users created"
    else
        print_error "Failed to setup test users"
        exit 1
    fi
fi

# Run E2E tests
if [ "$INTEGRATION_ONLY" = false ]; then
    print_header "RUNNING E2E TESTS"

    cd "$TEST_DIR"

    if [ "$QUICK_MODE" = true ]; then
        pytest_args="-v -m 'not slow'"
    else
        pytest_args="-v"
    fi

    if pytest e2e_billing_test.py $pytest_args --html=e2e_report.html --self-contained-html; then
        print_success "E2E tests passed"
    else
        print_error "E2E tests failed"
        exit 1
    fi
fi

# Run integration tests
if [ "$E2E_ONLY" = false ]; then
    print_header "RUNNING INTEGRATION TESTS"

    cd "$TEST_DIR"

    if bash test_billing_integration.sh; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
fi

# Run webhook tests
if [ "$E2E_ONLY" = false ] && [ "$QUICK_MODE" = false ]; then
    print_header "RUNNING WEBHOOK TESTS"

    cd "$TEST_DIR"

    if python3 simulate_webhooks.py --run-all; then
        print_success "Webhook tests passed"
    else
        print_error "Webhook tests failed"
        exit 1
    fi
fi

# Generate coverage report
if [ "$INTEGRATION_ONLY" = false ] && [ "$QUICK_MODE" = false ]; then
    print_header "GENERATING COVERAGE REPORT"

    cd "$TEST_DIR"

    if pytest --cov=backend --cov-report=html --cov-report=term-missing e2e_billing_test.py; then
        print_success "Coverage report generated: htmlcov/index.html"
    else
        print_error "Coverage report failed"
    fi
fi

# Cleanup test users
if [ "$SKIP_CLEANUP" = false ] && [ "$INTEGRATION_ONLY" = false ]; then
    print_header "CLEANING UP TEST USERS"

    cd "$TEST_DIR"

    if python3 setup_test_data.py --cleanup; then
        print_success "Test users cleaned up"
    else
        print_error "Cleanup failed (non-critical)"
    fi
fi

# Summary
print_header "TEST SUMMARY"

echo ""
print_success "All tests completed successfully!"
echo ""
print_info "Reports generated:"
echo "  - E2E Report: $TEST_DIR/e2e_report.html"
echo "  - Coverage Report: $TEST_DIR/htmlcov/index.html"
echo ""
print_info "End Time: $(date)"
echo ""

exit 0
