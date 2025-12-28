#!/bin/bash

##############################################################################
# Firewall Management Test Suite Runner
# Epic 1.2 Phase 1 - Comprehensive Test Execution
#
# Usage:
#   ./run_firewall_tests.sh [options]
#
# Options:
#   unit         - Run unit tests only
#   integration  - Run integration tests only
#   coverage     - Run with coverage report
#   parallel     - Run tests in parallel
#   quick        - Run quick tests only (no slow tests)
#   all          - Run all tests (default)
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_TESTS="$SCRIPT_DIR/unit/test_firewall_manager.py"
INTEGRATION_TESTS="$SCRIPT_DIR/integration/test_firewall_api.py"

# Banner
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Firewall Management Test Suite${NC}"
echo -e "${BLUE}  Epic 1.2 Phase 1${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install -r $SCRIPT_DIR/requirements-test.txt"
    exit 1
fi

# Check if UFW is installed
if ! command -v ufw &> /dev/null; then
    echo -e "${YELLOW}Warning: UFW is not installed${NC}"
    echo "Some tests may be skipped"
    echo "Install with: sudo apt-get install ufw"
    echo ""
fi

# Parse command line arguments
MODE="${1:-all}"

case "$MODE" in
    unit)
        echo -e "${GREEN}Running Unit Tests Only${NC}"
        echo ""
        pytest "$UNIT_TESTS" -v \
            --tb=short \
            --color=yes
        ;;

    integration)
        echo -e "${GREEN}Running Integration Tests Only${NC}"
        echo ""

        # Check if Ops-Center is running
        if ! curl -s http://localhost:8084/api/v1/system/status > /dev/null 2>&1; then
            echo -e "${YELLOW}Warning: Ops-Center may not be running at http://localhost:8084${NC}"
            echo "Some tests may fail"
            echo ""
        fi

        pytest "$INTEGRATION_TESTS" -v \
            --asyncio-mode=auto \
            --tb=short \
            --color=yes
        ;;

    coverage)
        echo -e "${GREEN}Running All Tests with Coverage${NC}"
        echo ""
        pytest "$UNIT_TESTS" "$INTEGRATION_TESTS" -v \
            --asyncio-mode=auto \
            --cov=backend.firewall_manager \
            --cov=backend.network_manager \
            --cov=backend.audit_logger \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-report=xml \
            --tb=short \
            --color=yes

        echo ""
        echo -e "${GREEN}Coverage report generated at: htmlcov/index.html${NC}"
        ;;

    parallel)
        echo -e "${GREEN}Running All Tests in Parallel${NC}"
        echo ""
        pytest "$UNIT_TESTS" "$INTEGRATION_TESTS" -v \
            --asyncio-mode=auto \
            -n auto \
            --tb=short \
            --color=yes
        ;;

    quick)
        echo -e "${GREEN}Running Quick Tests Only (excluding slow tests)${NC}"
        echo ""
        pytest "$UNIT_TESTS" "$INTEGRATION_TESTS" -v \
            --asyncio-mode=auto \
            -m "not slow" \
            --tb=short \
            --color=yes
        ;;

    all|*)
        echo -e "${GREEN}Running All Tests${NC}"
        echo ""
        echo -e "${BLUE}Phase 1: Unit Tests${NC}"
        echo "-------------------"
        pytest "$UNIT_TESTS" -v \
            --tb=short \
            --color=yes

        echo ""
        echo -e "${BLUE}Phase 2: Integration Tests${NC}"
        echo "-------------------------"
        pytest "$INTEGRATION_TESTS" -v \
            --asyncio-mode=auto \
            --tb=short \
            --color=yes
        ;;
esac

# Test results
EXIT_CODE=$?

echo ""
echo -e "${BLUE}============================================${NC}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All Tests Passed!${NC}"
else
    echo -e "${RED}✗ Some Tests Failed${NC}"
fi

echo -e "${BLUE}============================================${NC}"

exit $EXIT_CODE
