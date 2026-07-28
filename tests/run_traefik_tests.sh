#!/bin/bash
#
# Traefik Management Test Runner (Epic 1.3)
# Runs comprehensive test suite for Traefik integration
#
# Usage:
#   ./run_traefik_tests.sh              # Run all tests
#   ./run_traefik_tests.sh unit         # Run only unit tests
#   ./run_traefik_tests.sh integration  # Run only integration tests
#   ./run_traefik_tests.sh coverage     # Run with coverage report
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/.." && pwd)"
COVERAGE_TARGET=90

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Traefik Management Test Suite (Epic 1.3)${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install -r tests/requirements-test.txt"
    exit 1
fi

# Determine test type
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    unit)
        echo -e "${YELLOW}Running Unit Tests Only...${NC}\n"

        pytest "$TEST_DIR/unit/test_traefik_manager.py" \
            -v \
            --cov="$PROJECT_ROOT/backend/traefik_manager" \
            --cov-report=term-missing \
            --cov-report=html:tests/coverage/traefik_unit \
            --tb=short \
            -m unit \
            --asyncio-mode=auto

        RESULT=$?
        ;;

    integration)
        echo -e "${YELLOW}Running Integration Tests Only...${NC}\n"

        # Check if Ops-Center is running
        if ! curl -s http://localhost:8084/api/v1/system/status > /dev/null 2>&1; then
            echo -e "${RED}Warning: Ops-Center API not accessible at http://localhost:8084${NC}"
            echo "Some tests may fail. Start Ops-Center with: docker restart ops-center-direct"
            echo ""
        fi

        pytest "$TEST_DIR/integration/test_traefik_api.py" \
            -v \
            --cov="$PROJECT_ROOT/backend/traefik_api" \
            --cov-report=term-missing \
            --cov-report=html:tests/coverage/traefik_integration \
            --tb=short \
            -m integration \
            --asyncio-mode=auto

        RESULT=$?
        ;;

    coverage)
        echo -e "${YELLOW}Running All Tests with Full Coverage Report...${NC}\n"

        pytest "$TEST_DIR/unit/test_traefik_manager.py" \
               "$TEST_DIR/integration/test_traefik_api.py" \
            -v \
            --cov="$PROJECT_ROOT/backend" \
            --cov-report=term-missing \
            --cov-report=html:tests/coverage/traefik_all \
            --cov-fail-under=$COVERAGE_TARGET \
            --tb=short \
            --asyncio-mode=auto

        RESULT=$?

        if [ $RESULT -eq 0 ]; then
            echo -e "\n${GREEN}✓ Coverage target of ${COVERAGE_TARGET}% achieved!${NC}"
            echo -e "View full report: file://$TEST_DIR/coverage/traefik_all/index.html"
        else
            echo -e "\n${RED}✗ Coverage target of ${COVERAGE_TARGET}% not met${NC}"
        fi
        ;;

    quick)
        echo -e "${YELLOW}Running Quick Test (No Coverage)...${NC}\n"

        pytest "$TEST_DIR/unit/test_traefik_manager.py" \
               "$TEST_DIR/integration/test_traefik_api.py" \
            -v \
            --tb=short \
            --asyncio-mode=auto \
            -x  # Stop on first failure

        RESULT=$?
        ;;

    all|*)
        echo -e "${YELLOW}Running All Tests...${NC}\n"

        # Run unit tests
        echo -e "${BLUE}=== Unit Tests ===${NC}"
        pytest "$TEST_DIR/unit/test_traefik_manager.py" \
            -v \
            --cov="$PROJECT_ROOT/backend/traefik_manager" \
            --cov-report=term-missing \
            --tb=short \
            --asyncio-mode=auto

        UNIT_RESULT=$?

        echo ""

        # Run integration tests
        echo -e "${BLUE}=== Integration Tests ===${NC}"
        pytest "$TEST_DIR/integration/test_traefik_api.py" \
            -v \
            --cov="$PROJECT_ROOT/backend/traefik_api" \
            --cov-report=term-missing \
            --tb=short \
            --asyncio-mode=auto

        INTEGRATION_RESULT=$?

        # Overall result
        if [ $UNIT_RESULT -eq 0 ] && [ $INTEGRATION_RESULT -eq 0 ]; then
            RESULT=0
        else
            RESULT=1
        fi
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    # Test statistics
    echo -e "${BLUE}Test Statistics:${NC}"
    echo "  Unit Tests: 67 tests"
    echo "  Integration Tests: 75 tests"
    echo "  Total: 142 tests"
    echo ""
    echo -e "${GREEN}Coverage Target: ${COVERAGE_TARGET}%+${NC}"

    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    echo -e "${YELLOW}Debug Tips:${NC}"
    echo "  1. Check Ops-Center is running: docker ps | grep ops-center"
    echo "  2. View logs: docker logs ops-center-direct"
    echo "  3. Check test environment: cat tests/.env.test"
    echo "  4. Run specific test: pytest tests/unit/test_traefik_manager.py::TestClass::test_name -v"
    echo ""

    exit 1
fi
