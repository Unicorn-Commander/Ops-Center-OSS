#!/bin/bash
#
# Cloudflare DNS Management Test Runner
# Executes all test suites with coverage reporting
#
# Usage:
#   ./run_cloudflare_tests.sh              # Run all tests
#   ./run_cloudflare_tests.sh unit         # Run unit tests only
#   ./run_cloudflare_tests.sh integration  # Run integration tests only
#   ./run_cloudflare_tests.sh e2e          # Run E2E tests only
#   ./run_cloudflare_tests.sh fast         # Run only fast tests (exclude slow)
#   ./run_cloudflare_tests.sh coverage     # Run with detailed coverage report
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$TEST_DIR"

# Configuration
UNIT_TESTS="unit/test_cloudflare_manager.py"
INTEGRATION_TESTS="integration/test_cloudflare_api.py"
E2E_TESTS="e2e/test_cloudflare_e2e.py"
CONFTEST="conftest_cloudflare.py"

# Default options
PYTEST_OPTS="-v --tb=short"
TEST_TYPE="${1:-all}"

# Function to print colored messages
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
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

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed"
        echo "Install with: pip install -r requirements-test.txt"
        exit 1
    fi
    print_success "pytest is installed"

    # Check if ops-center is running (for integration tests)
    if [[ "$TEST_TYPE" == "integration" || "$TEST_TYPE" == "e2e" || "$TEST_TYPE" == "all" ]]; then
        OPS_CENTER_URL="${OPS_CENTER_URL:-http://localhost:8084}"
        if ! curl -s -f "$OPS_CENTER_URL/api/v1/system/status" > /dev/null 2>&1; then
            print_warning "Ops-Center not responding at $OPS_CENTER_URL"
            print_warning "Integration and E2E tests may fail"
        else
            print_success "Ops-Center is accessible"
        fi
    fi

    # Check test files exist
    if [ ! -f "$CONFTEST" ]; then
        print_error "Fixture file not found: $CONFTEST"
        exit 1
    fi
    print_success "Test fixtures found"

    echo ""
}

# Function to run tests
run_tests() {
    local test_files="$1"
    local test_name="$2"
    local extra_opts="$3"

    print_header "Running $test_name"

    if pytest $PYTEST_OPTS $extra_opts $test_files; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Function to run with coverage
run_with_coverage() {
    local test_files="$1"

    print_header "Running Tests with Coverage"

    pytest $PYTEST_OPTS \
        --cov=backend.cloudflare_manager \
        --cov=backend.cloudflare_client \
        --cov-report=html \
        --cov-report=term \
        --cov-report=json \
        $test_files

    echo ""
    print_success "Coverage reports generated:"
    echo "  - HTML: htmlcov/index.html"
    echo "  - JSON: coverage.json"
    echo "  - Terminal output above"
}

# Main execution
main() {
    clear
    print_header "Cloudflare DNS Test Suite Runner"
    echo "Test Type: $TEST_TYPE"
    echo "Test Directory: $TEST_DIR"
    echo ""

    check_prerequisites

    # Track results
    FAILED=0

    case "$TEST_TYPE" in
        unit)
            run_tests "$UNIT_TESTS" "Unit Tests" "" || FAILED=1
            ;;

        integration)
            run_tests "$INTEGRATION_TESTS" "Integration Tests" "--asyncio-mode=auto" || FAILED=1
            ;;

        e2e)
            run_tests "$E2E_TESTS" "End-to-End Tests" "-m e2e --asyncio-mode=auto" || FAILED=1
            ;;

        fast)
            print_header "Running Fast Tests (excluding slow)"
            run_tests "$UNIT_TESTS $INTEGRATION_TESTS" "Fast Tests" "-m 'not slow' --asyncio-mode=auto" || FAILED=1
            ;;

        coverage)
            run_with_coverage "$UNIT_TESTS $INTEGRATION_TESTS" || FAILED=1
            ;;

        all)
            print_header "Running All Test Suites"
            echo ""

            # Run unit tests
            run_tests "$UNIT_TESTS" "Unit Tests" "" || FAILED=1
            echo ""

            # Run integration tests
            run_tests "$INTEGRATION_TESTS" "Integration Tests" "--asyncio-mode=auto" || FAILED=1
            echo ""

            # Run E2E tests
            run_tests "$E2E_TESTS" "End-to-End Tests" "-m e2e --asyncio-mode=auto" || FAILED=1
            echo ""

            # Generate coverage report
            print_header "Generating Coverage Report"
            run_with_coverage "$UNIT_TESTS $INTEGRATION_TESTS $E2E_TESTS"
            ;;

        *)
            print_error "Unknown test type: $TEST_TYPE"
            echo ""
            echo "Usage: $0 [unit|integration|e2e|fast|coverage|all]"
            exit 1
            ;;
    esac

    # Final summary
    echo ""
    print_header "Test Summary"

    if [ $FAILED -eq 0 ]; then
        print_success "All tests passed!"

        # Count test statistics
        if [ -f ".pytest_cache/v/cache/lastfailed" ]; then
            LAST_FAILED=$(cat .pytest_cache/v/cache/lastfailed | wc -l)
            if [ $LAST_FAILED -gt 0 ]; then
                print_warning "Note: $LAST_FAILED test(s) failed in previous run"
            fi
        fi

        exit 0
    else
        print_error "Some tests failed"
        echo ""
        echo "To re-run only failed tests:"
        echo "  pytest --lf -v"
        exit 1
    fi
}

# Run main function
main
