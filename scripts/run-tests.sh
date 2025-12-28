#!/bin/bash
set -euo pipefail

# ==============================================================================
# Comprehensive Test Runner Script
# ==============================================================================
# This script runs the complete test suite with coverage reporting
# ==============================================================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-60}
TIMEOUT=${TIMEOUT:-30}
MAXFAIL=${MAXFAIL:-10}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# ==============================================================================
# Test Environment Setup
# ==============================================================================
setup_test_environment() {
    log_info "Setting up test environment..."

    # Start required services for integration tests
    log_info "Starting PostgreSQL and Redis for testing..."
    docker compose up -d unicorn-postgresql unicorn-redis

    # Wait for services
    log_info "Waiting for services to be ready..."
    sleep 10

    # Verify services
    docker exec unicorn-postgresql pg_isready -U unicorn || {
        log_error "PostgreSQL not ready"
        exit 1
    }

    docker exec unicorn-redis redis-cli ping || {
        log_error "Redis not ready"
        exit 1
    }

    log_success "Test environment ready"
}

# ==============================================================================
# Run Test Suites
# ==============================================================================
run_unit_tests() {
    log_info "========================================"
    log_info "Running Unit Tests"
    log_info "========================================"

    cd backend
    pytest tests/unit -v \
        --cov=. \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --timeout=$TIMEOUT \
        --maxfail=$MAXFAIL \
        -m unit || return 1

    cd ..
    log_success "Unit tests passed"
    return 0
}

run_integration_tests() {
    log_info "========================================"
    log_info "Running Integration Tests"
    log_info "========================================"

    cd backend
    pytest tests/integration -v \
        --cov=. \
        --cov-append \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        --timeout=60 \
        --maxfail=5 \
        -m integration || return 1

    cd ..
    log_success "Integration tests passed"
    return 0
}

run_e2e_tests() {
    log_info "========================================"
    log_info "Running E2E Tests"
    log_info "========================================"

    cd backend
    pytest tests/e2e -v \
        --timeout=120 \
        --maxfail=3 \
        -m e2e || return 1

    cd ..
    log_success "E2E tests passed"
    return 0
}

run_security_tests() {
    log_info "========================================"
    log_info "Running Security Tests"
    log_info "========================================"

    cd backend
    pytest tests/security -v \
        --timeout=$TIMEOUT \
        --maxfail=5 \
        -m security || return 1

    cd ..
    log_success "Security tests passed"
    return 0
}

# ==============================================================================
# Code Quality Checks
# ==============================================================================
run_linting() {
    log_info "========================================"
    log_info "Running Code Quality Checks"
    log_info "========================================"

    cd backend

    # Ruff
    log_info "Running Ruff linter..."
    ruff check . || {
        log_error "Ruff linting failed"
        return 1
    }

    # Black
    log_info "Running Black formatter check..."
    black --check --diff . || {
        log_error "Black formatting check failed"
        return 1
    }

    # MyPy
    log_info "Running MyPy type checker..."
    mypy . --ignore-missing-imports --no-strict-optional || {
        log_error "MyPy type checking failed"
        return 1
    }

    cd ..
    log_success "Code quality checks passed"
    return 0
}

# ==============================================================================
# Security Scanning
# ==============================================================================
run_security_scan() {
    log_info "========================================"
    log_info "Running Security Scans"
    log_info "========================================"

    # Bandit (Python security)
    log_info "Running Bandit security scanner..."
    cd backend
    bandit -r . -f json -o bandit-report.json || true
    bandit -r . || {
        log_error "Bandit security scan found issues"
        return 1
    }
    cd ..

    # Safety (dependency check)
    log_info "Running Safety dependency check..."
    safety check -r backend/requirements.txt || {
        log_error "Safety found vulnerable dependencies"
        return 1
    }

    # npm audit (frontend)
    log_info "Running npm audit..."
    npm audit --production --audit-level=moderate || {
        log_error "npm audit found vulnerabilities"
        return 1
    }

    log_success "Security scans passed"
    return 0
}

# ==============================================================================
# Generate Reports
# ==============================================================================
generate_reports() {
    log_info "========================================"
    log_info "Generating Test Reports"
    log_info "========================================"

    # Coverage summary
    cd backend
    coverage report || true

    # Generate badges
    log_info "Coverage HTML report: backend/htmlcov/index.html"
    log_info "Coverage XML report: backend/coverage.xml"

    cd ..

    # Test summary
    echo ""
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo "Coverage threshold: ${COVERAGE_THRESHOLD}%"
    echo "Total test files: $(find tests -name "test_*.py" | wc -l)"
    echo "Reports available in:"
    echo "  - backend/htmlcov/index.html (coverage)"
    echo "  - backend/bandit-report.json (security)"
    echo "========================================"
    echo ""
}

# ==============================================================================
# Cleanup
# ==============================================================================
cleanup() {
    log_info "Cleaning up test environment..."
    # Optionally stop test services
    # docker compose down unicorn-postgresql unicorn-redis
    log_success "Cleanup complete"
}

# ==============================================================================
# Main Test Flow
# ==============================================================================
main() {
    local start_time=$(date +%s)
    local failed_tests=()

    log_info "========================================"
    log_info "Ops-Center Test Suite"
    log_info "========================================"

    # Setup
    setup_test_environment || exit 1

    # Run linting
    if ! run_linting; then
        failed_tests+=("linting")
    fi

    # Run security scan
    if ! run_security_scan; then
        failed_tests+=("security_scan")
    fi

    # Run unit tests
    if ! run_unit_tests; then
        failed_tests+=("unit_tests")
    fi

    # Run integration tests
    if ! run_integration_tests; then
        failed_tests+=("integration_tests")
    fi

    # Run E2E tests
    if ! run_e2e_tests; then
        failed_tests+=("e2e_tests")
    fi

    # Run security tests
    if ! run_security_tests; then
        failed_tests+=("security_tests")
    fi

    # Generate reports
    generate_reports

    # Cleanup
    cleanup

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Summary
    echo ""
    log_info "========================================"
    log_info "Test Run Complete"
    log_info "========================================"
    log_info "Total duration: ${duration} seconds"

    if [ ${#failed_tests[@]} -eq 0 ]; then
        log_success "All tests passed!"
        exit 0
    else
        log_error "Failed test suites: ${failed_tests[*]}"
        exit 1
    fi
}

# Run main
main "$@"
