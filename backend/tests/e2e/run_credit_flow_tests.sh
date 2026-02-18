#!/bin/bash
#
# Credit Flow E2E Test Runner
# ===========================
#
# Runs comprehensive end-to-end tests for the complete credit flow system.
#
# Usage:
#   ./run_credit_flow_tests.sh [options]
#
# Options:
#   --setup-only     Only run setup (create test users, org)
#   --teardown-only  Only run teardown (cleanup test data)
#   --flow=NAME      Run specific flow (individual, org, byok, edge)
#   --skip-setup     Skip setup phase
#   --skip-teardown  Skip teardown phase
#   --verbose        Verbose output
#   --quick          Quick smoke test (skip manual edge cases)
#   --ci             CI mode (fail fast, no interactive)
#
# Examples:
#   ./run_credit_flow_tests.sh                      # Run all tests
#   ./run_credit_flow_tests.sh --flow=individual   # Test individual flow only
#   ./run_credit_flow_tests.sh --quick             # Quick smoke test
#   ./run_credit_flow_tests.sh --ci                # CI/CD pipeline mode
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/opt/ops-center"
REPORT_DIR="/tmp/credit_flow_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Environment variables
export OPS_CENTER_URL="${OPS_CENTER_URL:-http://localhost:8084}"
export KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
export KEYCLOAK_REALM="uchub"
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"

# Default options
SETUP_ONLY=false
TEARDOWN_ONLY=false
SKIP_SETUP=false
SKIP_TEARDOWN=false
VERBOSE=false
QUICK=false
CI_MODE=false
SPECIFIC_FLOW=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --teardown-only)
            TEARDOWN_ONLY=true
            shift
            ;;
        --flow=*)
            SPECIFIC_FLOW="${1#*=}"
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --skip-teardown)
            SKIP_TEARDOWN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        -h|--help)
            head -n 30 "$0" | grep "^#" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running in correct directory
    if [[ ! -f "$PROJECT_ROOT/backend/tests/e2e/test_complete_credit_flow.py" ]]; then
        log_error "Test file not found. Are you in the correct directory?"
        exit 1
    fi

    # Check if services are running
    log_info "Checking required services..."

    if ! docker ps | grep -q "ops-center-direct"; then
        log_error "Ops-Center container not running!"
        log_info "Start with: docker restart ops-center-direct"
        exit 1
    fi

    if ! docker ps | grep -q "uchub-keycloak"; then
        log_error "Keycloak container not running!"
        log_info "Start with: docker restart uchub-keycloak"
        exit 1
    fi

    if ! docker ps | grep -q "unicorn-postgresql"; then
        log_error "PostgreSQL container not running!"
        exit 1
    fi

    if ! docker ps | grep -q "unicorn-redis"; then
        log_error "Redis container not running!"
        exit 1
    fi

    log_success "All required services are running"

    # Check if Python dependencies are installed
    if ! python3 -c "import httpx, pytest" 2>/dev/null; then
        log_warning "Missing Python dependencies. Installing..."
        pip install -q httpx pytest pytest-asyncio
    fi

    # Check if Ops-Center API is accessible
    if ! curl -s -f "$OPS_CENTER_URL/api/v1/system/status" > /dev/null; then
        log_error "Ops-Center API not accessible at $OPS_CENTER_URL"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

create_report_dir() {
    mkdir -p "$REPORT_DIR"
    log_info "Reports will be saved to: $REPORT_DIR"
}

run_tests() {
    log_info "Starting E2E Credit Flow Tests..."
    echo ""

    cd "$PROJECT_ROOT"

    # Build pytest command
    PYTEST_CMD="pytest backend/tests/e2e/test_complete_credit_flow.py"

    if [ "$VERBOSE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -vv -s"
    else
        PYTEST_CMD="$PYTEST_CMD -v"
    fi

    if [ "$CI_MODE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -x --tb=short"
    fi

    if [ -n "$SPECIFIC_FLOW" ]; then
        PYTEST_CMD="$PYTEST_CMD -k test_${SPECIFIC_FLOW}_user_flow"
        log_info "Running specific flow: $SPECIFIC_FLOW"
    fi

    # Run tests
    if eval "$PYTEST_CMD"; then
        log_success "All tests passed!"
        return 0
    else
        log_error "Some tests failed!"
        return 1
    fi
}

run_setup_only() {
    log_info "Running setup only..."
    cd "$PROJECT_ROOT"
    python3 -c "
import asyncio
from backend.tests.e2e.test_complete_credit_flow import CreditFlowTestSuite

async def main():
    suite = CreditFlowTestSuite()
    await suite.setup()
    print('\\nSetup complete! Test data ready.')
    print('Organization ID:', suite.test_org_id)

asyncio.run(main())
"
}

run_teardown_only() {
    log_info "Running teardown only..."
    cd "$PROJECT_ROOT"
    python3 -c "
import asyncio
from backend.tests.e2e.test_complete_credit_flow import CreditFlowTestSuite

async def main():
    suite = CreditFlowTestSuite()
    await suite.teardown()
    print('\\nTeardown complete! Test data cleaned up.')

asyncio.run(main())
"
}

generate_summary_report() {
    log_info "Generating summary report..."

    REPORT_FILE="$REPORT_DIR/credit_flow_summary_${TIMESTAMP}.txt"

    cat > "$REPORT_FILE" << EOF
================================================================================
CREDIT FLOW E2E TEST SUMMARY
================================================================================

Test Run: $TIMESTAMP
Environment: $OPS_CENTER_URL
Keycloak: $KEYCLOAK_URL

Test Execution:
- Setup Skipped: $SKIP_SETUP
- Teardown Skipped: $SKIP_TEARDOWN
- Specific Flow: ${SPECIFIC_FLOW:-"All flows"}
- Quick Mode: $QUICK
- CI Mode: $CI_MODE

Services Status:
EOF

    # Add service status
    docker ps --format "- {{.Names}}: {{.Status}}" | grep -E "(ops-center|keycloak|postgresql|redis|lago|litellm)" >> "$REPORT_FILE"

    echo "" >> "$REPORT_FILE"
    echo "Detailed report: /tmp/credit_flow_e2e_report.txt" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    log_success "Summary report saved to: $REPORT_FILE"
}

# Main execution
main() {
    echo ""
    echo "================================================================================"
    echo "                   CREDIT FLOW E2E TEST SUITE"
    echo "================================================================================"
    echo ""

    create_report_dir

    if [ "$TEARDOWN_ONLY" = true ]; then
        run_teardown_only
        exit 0
    fi

    check_prerequisites

    if [ "$SETUP_ONLY" = true ]; then
        run_setup_only
        exit 0
    fi

    # Run tests
    if run_tests; then
        TEST_RESULT=0
    else
        TEST_RESULT=1
    fi

    # Generate summary
    generate_summary_report

    echo ""
    echo "================================================================================"
    if [ $TEST_RESULT -eq 0 ]; then
        log_success "TEST RUN COMPLETED SUCCESSFULLY"
    else
        log_error "TEST RUN COMPLETED WITH FAILURES"
    fi
    echo "================================================================================"
    echo ""

    exit $TEST_RESULT
}

# Run main function
main
