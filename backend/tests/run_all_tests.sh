#!/bin/bash
# Comprehensive Test Runner for Traefik API
#
# Runs all test suites and generates reports
#
# Author: Testing & QA Specialist Agent
# Date: October 24, 2025
# Epic: 1.3 - Traefik Configuration Management

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$TEST_DIR")"
COVERAGE_DIR="$TEST_DIR/coverage_reports"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ============================================================================
# Pre-flight checks
# ============================================================================

preflight_checks() {
    log_info "Running preflight checks..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check pytest
    if ! python3 -c "import pytest" 2>/dev/null; then
        log_error "pytest is not installed. Run: pip install pytest pytest-cov"
        exit 1
    fi

    # Check if in correct directory
    if [ ! -f "$TEST_DIR/test_traefik_manager.py" ]; then
        log_error "Not in tests directory. Please cd to backend/tests/"
        exit 1
    fi

    log_success "Preflight checks passed"
    echo ""
}

# ============================================================================
# Test runners
# ============================================================================

run_unit_tests() {
    echo "========================================"
    echo "Running Unit Tests (traefik_manager.py)"
    echo "========================================"
    echo ""

    cd "$TEST_DIR"

    if pytest test_traefik_manager.py -v --tb=short; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

run_api_tests() {
    echo ""
    echo "========================================"
    echo "Running API Tests (traefik_api.py)"
    echo "========================================"
    echo ""

    cd "$TEST_DIR"

    if pytest test_traefik_api.py -v --tb=short; then
        log_success "API tests passed"
        return 0
    else
        log_error "API tests failed"
        return 1
    fi
}

run_e2e_tests() {
    echo ""
    echo "========================================"
    echo "Running E2E Tests (curl)"
    echo "========================================"
    echo ""

    cd "$TEST_DIR"

    if [ ! -x "./test_traefik_e2e.sh" ]; then
        chmod +x ./test_traefik_e2e.sh
    fi

    if ./test_traefik_e2e.sh; then
        log_success "E2E tests passed"
        return 0
    else
        log_error "E2E tests failed"
        return 1
    fi
}

run_coverage_tests() {
    echo ""
    echo "========================================"
    echo "Running Tests with Coverage"
    echo "========================================"
    echo ""

    cd "$TEST_DIR"

    # Create coverage directory
    mkdir -p "$COVERAGE_DIR"

    # Run tests with coverage
    if pytest test_traefik_manager.py test_traefik_api.py \
        --cov="$BACKEND_DIR" \
        --cov-report=html:"$COVERAGE_DIR/html" \
        --cov-report=term-missing \
        --cov-report=json:"$COVERAGE_DIR/coverage.json" \
        -v; then

        log_success "Coverage tests passed"

        # Display coverage summary
        echo ""
        log_info "Coverage report saved to: $COVERAGE_DIR/html/index.html"

        # Try to open in browser (Linux)
        if command -v xdg-open &> /dev/null; then
            log_info "Opening coverage report in browser..."
            xdg-open "$COVERAGE_DIR/html/index.html" 2>/dev/null &
        fi

        return 0
    else
        log_error "Coverage tests failed"
        return 1
    fi
}

# ============================================================================
# Report generation
# ============================================================================

generate_report() {
    echo ""
    echo "========================================"
    echo "Test Execution Summary"
    echo "========================================"
    echo ""

    local unit_status=$1
    local api_status=$2
    local e2e_status=$3

    if [ $unit_status -eq 0 ]; then
        echo -e "${GREEN}✅${NC} Unit Tests: PASSED"
    else
        echo -e "${RED}❌${NC} Unit Tests: FAILED"
    fi

    if [ $api_status -eq 0 ]; then
        echo -e "${GREEN}✅${NC} API Tests: PASSED"
    else
        echo -e "${RED}❌${NC} API Tests: FAILED"
    fi

    if [ $e2e_status -eq 0 ]; then
        echo -e "${GREEN}✅${NC} E2E Tests: PASSED"
    else
        echo -e "${RED}❌${NC} E2E Tests: FAILED"
    fi

    echo ""

    local total_failures=$((unit_status + api_status + e2e_status))

    if [ $total_failures -eq 0 ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}   🎉 ALL TESTS PASSED! 🎉${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 0
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}   ❌ SOME TESTS FAILED ❌${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 1
    fi
}

# ============================================================================
# Main execution
# ============================================================================

main() {
    local start_time=$(date +%s)

    echo "========================================"
    echo "Traefik API Comprehensive Test Suite"
    echo "========================================"
    echo "Test Directory: $TEST_DIR"
    echo "Backend Directory: $BACKEND_DIR"
    echo ""

    preflight_checks

    # Run test suites
    local unit_status=0
    local api_status=0
    local e2e_status=0

    run_unit_tests || unit_status=$?
    run_api_tests || api_status=$?
    run_e2e_tests || e2e_status=$?

    # Generate coverage report (optional)
    if [ "${COVERAGE:-0}" == "1" ]; then
        run_coverage_tests
    fi

    # Generate final report
    generate_report $unit_status $api_status $e2e_status
    local exit_code=$?

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    log_info "Total execution time: ${duration}s"
    echo ""

    exit $exit_code
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            export COVERAGE=1
            shift
            ;;
        --unit|-u)
            preflight_checks
            run_unit_tests
            exit $?
            ;;
        --api|-a)
            preflight_checks
            run_api_tests
            exit $?
            ;;
        --e2e|-e)
            preflight_checks
            run_e2e_tests
            exit $?
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage, -c    Generate coverage report"
            echo "  --unit, -u        Run only unit tests"
            echo "  --api, -a         Run only API tests"
            echo "  --e2e, -e         Run only E2E tests"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                Run all tests"
            echo "  $0 --coverage     Run all tests with coverage"
            echo "  $0 --unit         Run only unit tests"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main
main
