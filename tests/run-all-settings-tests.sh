#!/bin/bash
#
# Master Test Runner for System Settings
#
# Runs complete test suite including:
# - Backend API integration tests
# - Backend API performance tests
# - Frontend React component tests
# - Frontend custom hook tests
# - End-to-end Playwright tests
#
# Usage:
#   ./tests/run-all-settings-tests.sh [options]
#
# Options:
#   --backend-only     Run only backend tests
#   --frontend-only    Run only frontend tests
#   --e2e-only         Run only E2E tests
#   --quick            Run quick smoke tests only
#   --coverage         Generate coverage reports
#   --verbose          Verbose output
#   --help             Show this help
#
# Author: QA Testing Team Lead
# Created: November 14, 2025

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_BACKEND=true
RUN_FRONTEND=true
RUN_E2E=true
QUICK_MODE=false
COVERAGE=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --backend-only)
      RUN_BACKEND=true
      RUN_FRONTEND=false
      RUN_E2E=false
      shift
      ;;
    --frontend-only)
      RUN_BACKEND=false
      RUN_FRONTEND=true
      RUN_E2E=false
      shift
      ;;
    --e2e-only)
      RUN_BACKEND=false
      RUN_FRONTEND=false
      RUN_E2E=true
      shift
      ;;
    --quick)
      QUICK_MODE=true
      shift
      ;;
    --coverage)
      COVERAGE=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      head -n 30 "$0" | grep "^#" | sed 's/^# //'
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     System Settings - Comprehensive Test Suite                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Track results
BACKEND_PASSED=0
FRONTEND_PASSED=0
E2E_PASSED=0
TOTAL_TESTS=0
FAILED_TESTS=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${YELLOW}Working directory: $(pwd)${NC}"
echo -e "${YELLOW}Date: $(date)${NC}"
echo ""

# ============================================================================
# 1. Backend API Integration Tests
# ============================================================================

if [ "$RUN_BACKEND" = true ]; then
  echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║  1️⃣  Backend API Integration Tests                                   ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Check if ops-center container is running
  if ! docker ps | grep -q ops-center-direct; then
    echo -e "${RED}❌ ops-center-direct container is not running!${NC}"
    echo -e "${YELLOW}Please start it with: docker start ops-center-direct${NC}"
    exit 1
  fi

  # Run integration tests
  echo -e "${YELLOW}Running integration tests...${NC}"
  if docker exec ops-center-direct python3 /app/tests/test_settings_integration.py; then
    BACKEND_PASSED=$((BACKEND_PASSED + 1))
    echo -e "${GREEN}✅ Backend integration tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Backend integration tests FAILED${NC}"
  fi
  echo ""

  # Run performance tests
  echo -e "${YELLOW}Running performance tests...${NC}"
  if docker exec ops-center-direct python3 /app/tests/test_settings_performance.py; then
    BACKEND_PASSED=$((BACKEND_PASSED + 1))
    echo -e "${GREEN}✅ Backend performance tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Backend performance tests FAILED${NC}"
  fi
  echo ""

  TOTAL_TESTS=$((TOTAL_TESTS + 2))
fi

# ============================================================================
# 2. Frontend React Component Tests
# ============================================================================

if [ "$RUN_FRONTEND" = true ] && [ "$QUICK_MODE" = false ]; then
  echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║  2️⃣  Frontend React Component Tests                                  ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Check if package.json exists
  if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found!${NC}"
    echo -e "${YELLOW}Run this script from ops-center root directory${NC}"
    exit 1
  fi

  # Install dependencies if needed
  if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
  fi

  # Run Jest tests
  echo -e "${YELLOW}Running React component tests...${NC}"

  JEST_CMD="npm test -- --testPathPattern=SystemSettings.test.jsx --passWithNoTests"

  if [ "$COVERAGE" = true ]; then
    JEST_CMD="$JEST_CMD --coverage --coverageReporters=text --coverageReporters=html"
  fi

  if [ "$VERBOSE" = true ]; then
    JEST_CMD="$JEST_CMD --verbose"
  fi

  if eval "$JEST_CMD"; then
    FRONTEND_PASSED=$((FRONTEND_PASSED + 1))
    echo -e "${GREEN}✅ Component tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Component tests FAILED${NC}"
  fi
  echo ""

  # Run hook tests
  echo -e "${YELLOW}Running custom hook tests...${NC}"

  HOOK_CMD="npm test -- --testPathPattern=useSystemSettings.test.js --passWithNoTests"

  if [ "$VERBOSE" = true ]; then
    HOOK_CMD="$HOOK_CMD --verbose"
  fi

  if eval "$HOOK_CMD"; then
    FRONTEND_PASSED=$((FRONTEND_PASSED + 1))
    echo -e "${GREEN}✅ Hook tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Hook tests FAILED${NC}"
  fi
  echo ""

  TOTAL_TESTS=$((TOTAL_TESTS + 2))

  # Show coverage report location
  if [ "$COVERAGE" = true ] && [ -f "coverage/index.html" ]; then
    echo -e "${YELLOW}📊 Coverage report: file://$(pwd)/coverage/index.html${NC}"
    echo ""
  fi
fi

# ============================================================================
# 3. End-to-End Tests with Playwright
# ============================================================================

if [ "$RUN_E2E" = true ] && [ "$QUICK_MODE" = false ]; then
  echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║  3️⃣  End-to-End Tests (Playwright)                                   ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Check if Playwright is installed
  if ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ npx not found! Install Node.js first.${NC}"
    exit 1
  fi

  # Check if @playwright/test is installed
  if ! npm list @playwright/test &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright...${NC}"
    npm install -D @playwright/test
    npx playwright install
  fi

  # Run E2E tests
  echo -e "${YELLOW}Running E2E tests...${NC}"

  E2E_CMD="npx playwright test tests/e2e/settings.spec.js"

  if [ "$VERBOSE" = true ]; then
    E2E_CMD="$E2E_CMD --reporter=list"
  else
    E2E_CMD="$E2E_CMD --reporter=dot"
  fi

  # Run in headless mode (for CI)
  E2E_CMD="$E2E_CMD --headed=false"

  if eval "$E2E_CMD"; then
    E2E_PASSED=$((E2E_PASSED + 1))
    echo -e "${GREEN}✅ E2E tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ E2E tests FAILED${NC}"

    # Show Playwright report link
    if [ -d "playwright-report" ]; then
      echo -e "${YELLOW}📊 Playwright report: file://$(pwd)/playwright-report/index.html${NC}"
    fi
  fi
  echo ""

  TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# ============================================================================
# Quick Smoke Tests
# ============================================================================

if [ "$QUICK_MODE" = true ]; then
  echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║  🚀 Quick Smoke Tests                                                ║${NC}"
  echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # Just run backend integration tests and E2E smoke test
  echo -e "${YELLOW}Running quick backend checks...${NC}"
  if docker exec ops-center-direct python3 /app/tests/test_settings_integration.py | grep -q "PASSED"; then
    echo -e "${GREEN}✅ Backend smoke tests PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ Backend smoke tests FAILED${NC}"
  fi

  echo -e "${YELLOW}Running E2E smoke test...${NC}"
  if npx playwright test tests/e2e/settings.spec.js --grep "Smoke" --headed=false; then
    echo -e "${GREEN}✅ E2E smoke test PASSED${NC}"
  else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}❌ E2E smoke test FAILED${NC}"
  fi

  TOTAL_TESTS=2
fi

# ============================================================================
# Final Results Summary
# ============================================================================

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  📊 Test Results Summary                                             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$RUN_BACKEND" = true ]; then
  echo -e "  Backend Tests: ${YELLOW}$BACKEND_PASSED/2${NC} passed"
fi

if [ "$RUN_FRONTEND" = true ] && [ "$QUICK_MODE" = false ]; then
  echo -e "  Frontend Tests: ${YELLOW}$FRONTEND_PASSED/2${NC} passed"
fi

if [ "$RUN_E2E" = true ] && [ "$QUICK_MODE" = false ]; then
  echo -e "  E2E Tests: ${YELLOW}$E2E_PASSED/1${NC} passed"
fi

echo ""
echo -e "  ${YELLOW}Total Test Suites: $TOTAL_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "  ${GREEN}Failed: 0${NC}"
  echo ""
  echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║  🎉 All tests passed successfully!             ║${NC}"
  echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
  exit 0
else
  echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
  echo ""
  echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║  ⚠️  Some tests failed                          ║${NC}"
  echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${YELLOW}Review the output above for details.${NC}"
  echo ""
  echo -e "${YELLOW}Useful commands:${NC}"
  echo -e "  - View coverage report: ${BLUE}open coverage/index.html${NC}"
  echo -e "  - View Playwright report: ${BLUE}npx playwright show-report${NC}"
  echo -e "  - Run tests in debug mode: ${BLUE}npx playwright test --debug${NC}"
  exit 1
fi
