#!/bin/bash

#############################################################################
# Epic 1.7 NameCheap Migration Test Runner
#
# Executes all migration test suites:
# - Unit tests (test_namecheap_manager.py)
# - Integration tests (test_migration_api.py)
# - E2E tests (test_migration_e2e.py)
#
# Generates coverage report and outputs results in readable format
#############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$SCRIPT_DIR"
REPORTS_DIR="$TESTS_DIR/reports"
COVERAGE_DIR="$REPORTS_DIR/coverage"

# Create reports directory
mkdir -p "$REPORTS_DIR"
mkdir -p "$COVERAGE_DIR"

# Timestamp for reports
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORTS_DIR/migration_test_report_${TIMESTAMP}.txt"
COVERAGE_REPORT="$COVERAGE_DIR/migration_coverage_${TIMESTAMP}.html"
JSON_REPORT="$REPORTS_DIR/migration_test_results_${TIMESTAMP}.json"

# Test markers
UNIT_MARKER="unit"
INTEGRATION_MARKER="integration"
E2E_MARKER="e2e"

# Function to print section header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print info message
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

#############################################################################
# Main Test Execution
#############################################################################

main() {
    print_header "Epic 1.7 NameCheap Migration - Test Suite"

    # Check dependencies
    print_info "Checking test dependencies..."
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Please install: pip install pytest pytest-asyncio pytest-cov"
        exit 1
    fi
    print_success "Dependencies OK"

    # Parse command line arguments
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
    VERBOSE=false
    COVERAGE=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                RUN_INTEGRATION=false
                RUN_E2E=false
                shift
                ;;
            --integration-only)
                RUN_UNIT=false
                RUN_E2E=false
                shift
                ;;
            --e2e-only)
                RUN_UNIT=false
                RUN_INTEGRATION=false
                shift
                ;;
            --no-coverage)
                COVERAGE=false
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Initialize report
    {
        echo "=========================================="
        echo "Epic 1.7 Migration Test Report"
        echo "=========================================="
        echo "Timestamp: $(date)"
        echo "Test Environment: ${TEST_ENV:-local}"
        echo ""
    } > "$REPORT_FILE"

    # Test counters
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    SKIPPED_TESTS=0

    # Run unit tests
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests
    fi

    # Run integration tests
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
    fi

    # Run E2E tests
    if [ "$RUN_E2E" = true ]; then
        run_e2e_tests
    fi

    # Generate coverage report
    if [ "$COVERAGE" = true ]; then
        generate_coverage_report
    fi

    # Print summary
    print_test_summary

    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

#############################################################################
# Test Runners
#############################################################################

run_unit_tests() {
    print_header "Running Unit Tests (test_namecheap_manager.py)"

    local pytest_args=(
        "unit/test_namecheap_manager.py"
        "-v"
        "--tb=short"
        "--color=yes"
        "-m" "$UNIT_MARKER or not $INTEGRATION_MARKER and not $E2E_MARKER"
    )

    if [ "$COVERAGE" = true ]; then
        pytest_args+=(
            "--cov=backend.namecheap_manager"
            "--cov-append"
            "--cov-report=term-missing"
        )
    fi

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-vv" "-s")
    fi

    if pytest "${pytest_args[@]}" --json-report --json-report-file="$REPORTS_DIR/unit_tests.json" 2>&1 | tee -a "$REPORT_FILE"; then
        print_success "Unit tests passed"
        parse_test_results "$REPORTS_DIR/unit_tests.json"
    else
        print_error "Unit tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

run_integration_tests() {
    print_header "Running Integration Tests (test_migration_api.py)"

    local pytest_args=(
        "integration/test_migration_api.py"
        "-v"
        "--tb=short"
        "--color=yes"
        "-m" "$INTEGRATION_MARKER or not $UNIT_MARKER and not $E2E_MARKER"
    )

    if [ "$COVERAGE" = true ]; then
        pytest_args+=(
            "--cov=backend.api.migration"
            "--cov-append"
            "--cov-report=term-missing"
        )
    fi

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-vv" "-s")
    fi

    if pytest "${pytest_args[@]}" --json-report --json-report-file="$REPORTS_DIR/integration_tests.json" 2>&1 | tee -a "$REPORT_FILE"; then
        print_success "Integration tests passed"
        parse_test_results "$REPORTS_DIR/integration_tests.json"
    else
        print_error "Integration tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

run_e2e_tests() {
    print_header "Running E2E Tests (test_migration_e2e.py)"

    local pytest_args=(
        "e2e/test_migration_e2e.py"
        "-v"
        "--tb=short"
        "--color=yes"
        "-m" "$E2E_MARKER or not $UNIT_MARKER and not $INTEGRATION_MARKER"
    )

    if [ "$COVERAGE" = true ]; then
        pytest_args+=(
            "--cov=backend"
            "--cov-append"
            "--cov-report=term-missing"
        )
    fi

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-vv" "-s")
    fi

    if pytest "${pytest_args[@]}" --json-report --json-report-file="$REPORTS_DIR/e2e_tests.json" 2>&1 | tee -a "$REPORT_FILE"; then
        print_success "E2E tests passed"
        parse_test_results "$REPORTS_DIR/e2e_tests.json"
    else
        print_error "E2E tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

#############################################################################
# Reporting
#############################################################################

generate_coverage_report() {
    print_header "Generating Coverage Report"

    if command -v coverage &> /dev/null; then
        # Generate HTML coverage report
        coverage html -d "$COVERAGE_DIR" 2>&1 | tee -a "$REPORT_FILE"

        # Generate terminal summary
        echo "" >> "$REPORT_FILE"
        echo "Coverage Summary:" >> "$REPORT_FILE"
        echo "----------------" >> "$REPORT_FILE"
        coverage report >> "$REPORT_FILE"

        # Extract coverage percentage
        COVERAGE_PERCENT=$(coverage report | grep TOTAL | awk '{print $4}')

        print_info "Coverage Report: $COVERAGE_DIR/index.html"
        print_info "Overall Coverage: $COVERAGE_PERCENT"

        # Check if coverage meets target (90%)
        COVERAGE_NUM=$(echo "$COVERAGE_PERCENT" | sed 's/%//')
        if (( $(echo "$COVERAGE_NUM >= 90" | bc -l) )); then
            print_success "Coverage target met (≥90%)"
        else
            print_warning "Coverage below target: $COVERAGE_PERCENT < 90%"
        fi
    else
        print_warning "coverage command not found, skipping HTML report"
    fi
}

parse_test_results() {
    local json_file=$1
    if [ -f "$json_file" ]; then
        # Parse JSON test results (requires jq)
        if command -v jq &> /dev/null; then
            local passed=$(jq '.summary.passed // 0' "$json_file")
            local failed=$(jq '.summary.failed // 0' "$json_file")
            local skipped=$(jq '.summary.skipped // 0' "$json_file")
            local total=$(jq '.summary.total // 0' "$json_file")

            TOTAL_TESTS=$((TOTAL_TESTS + total))
            PASSED_TESTS=$((PASSED_TESTS + passed))
            FAILED_TESTS=$((FAILED_TESTS + failed))
            SKIPPED_TESTS=$((SKIPPED_TESTS + skipped))
        fi
    fi
}

print_test_summary() {
    print_header "Test Summary"

    {
        echo ""
        echo "=========================================="
        echo "Test Summary"
        echo "=========================================="
        echo "Total Tests:   $TOTAL_TESTS"
        echo "Passed:        $PASSED_TESTS"
        echo "Failed:        $FAILED_TESTS"
        echo "Skipped:       $SKIPPED_TESTS"
        echo ""
        echo "Success Rate:  $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"
        echo ""
        echo "Report saved to: $REPORT_FILE"
        echo "=========================================="
    } | tee -a "$REPORT_FILE"

    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All tests passed! ✨"
    else
        print_error "$FAILED_TESTS test suite(s) failed"
    fi
}

show_help() {
    cat << EOF
Epic 1.7 NameCheap Migration Test Runner

Usage: $0 [OPTIONS]

Options:
    --unit-only         Run only unit tests
    --integration-only  Run only integration tests
    --e2e-only          Run only E2E tests
    --no-coverage       Skip coverage report generation
    --verbose, -v       Verbose output
    --help, -h          Show this help message

Examples:
    # Run all tests with coverage
    $0

    # Run only unit tests
    $0 --unit-only

    # Run with verbose output
    $0 --verbose

    # Run without coverage
    $0 --no-coverage

Reports:
    Test reports are saved to: $REPORTS_DIR/
    Coverage reports are saved to: $COVERAGE_DIR/

EOF
}

#############################################################################
# Execute
#############################################################################

# Change to tests directory
cd "$TESTS_DIR"

# Run main function
main "$@"
