#!/bin/bash

################################################################################
# Build Dependency Verification Script
#
# Purpose: Verify all build dependencies are correct before attempting build
# Author: Ops-Center Build Team
# Created: 2025-10-30
#
# Usage: ./scripts/verify-build-deps.sh [--fix]
#
# Options:
#   --fix    Attempt to fix detected issues automatically
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#   2 - Critical error (e.g., missing Node.js)
################################################################################

set -e  # Exit on first error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0
FIX_MODE=0

# Check for --fix flag
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=1
    echo -e "${BLUE}Running in FIX mode - will attempt to repair issues${NC}\n"
fi

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

version_compare() {
    # Returns 0 if $1 >= $2, 1 otherwise
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

################################################################################
# CHECK 1: Node.js Version
################################################################################

print_header "CHECK 1: Node.js Version"

REQUIRED_NODE_VERSION="18.0.0"
RECOMMENDED_NODE_VERSION="20.0.0"

if ! command -v node &> /dev/null; then
    check_fail "Node.js is not installed"
    echo -e "    ${RED}CRITICAL:${NC} Please install Node.js ${RECOMMENDED_NODE_VERSION}+ from https://nodejs.org/"
    exit 2
fi

NODE_VERSION=$(node --version | cut -d'v' -f2)
echo -e "  Found Node.js version: ${BLUE}v${NODE_VERSION}${NC}"

if version_compare "$NODE_VERSION" "$REQUIRED_NODE_VERSION"; then
    if version_compare "$NODE_VERSION" "$RECOMMENDED_NODE_VERSION"; then
        check_pass "Node.js version meets recommended requirements (>= v${RECOMMENDED_NODE_VERSION})"
    else
        check_warn "Node.js version meets minimum requirements but upgrade to v${RECOMMENDED_NODE_VERSION}+ recommended"
    fi
else
    check_fail "Node.js version v${NODE_VERSION} is below minimum v${REQUIRED_NODE_VERSION}"
    echo -e "    ${RED}Please upgrade Node.js to v${RECOMMENDED_NODE_VERSION}+${NC}"
    exit 2
fi

################################################################################
# CHECK 2: npm Version
################################################################################

print_header "CHECK 2: npm Version"

REQUIRED_NPM_VERSION="9.0.0"
RECOMMENDED_NPM_VERSION="10.0.0"

if ! command -v npm &> /dev/null; then
    check_fail "npm is not installed"
    exit 2
fi

NPM_VERSION=$(npm --version)
echo -e "  Found npm version: ${BLUE}v${NPM_VERSION}${NC}"

if version_compare "$NPM_VERSION" "$REQUIRED_NPM_VERSION"; then
    if version_compare "$NPM_VERSION" "$RECOMMENDED_NPM_VERSION"; then
        check_pass "npm version meets recommended requirements (>= v${RECOMMENDED_NPM_VERSION})"
    else
        check_warn "npm version meets minimum requirements but upgrade recommended"
        if [[ $FIX_MODE -eq 1 ]]; then
            echo -e "    ${YELLOW}Attempting to upgrade npm...${NC}"
            npm install -g npm@latest || check_warn "Failed to upgrade npm automatically"
        fi
    fi
else
    check_fail "npm version v${NPM_VERSION} is below minimum v${REQUIRED_NPM_VERSION}"
    if [[ $FIX_MODE -eq 1 ]]; then
        echo -e "    ${YELLOW}Attempting to upgrade npm...${NC}"
        npm install -g npm@${RECOMMENDED_NPM_VERSION} || check_fail "Failed to upgrade npm"
    else
        echo -e "    ${RED}Run: npm install -g npm@latest${NC}"
    fi
fi

################################################################################
# CHECK 3: package.json Integrity
################################################################################

print_header "CHECK 3: package.json Integrity"

if [[ ! -f "package.json" ]]; then
    check_fail "package.json not found in current directory"
    echo -e "    ${RED}Please run this script from the ops-center root directory${NC}"
    exit 2
fi

check_pass "package.json found"

# Validate JSON syntax
if ! node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8'))" 2>/dev/null; then
    check_fail "package.json has invalid JSON syntax"
    exit 2
else
    check_pass "package.json has valid JSON syntax"
fi

# Check for critical dependencies
CRITICAL_DEPS=(
    "react"
    "react-dom"
    "react-router-dom"
    "@mui/material"
    "@mui/icons-material"
    "@emotion/react"
    "@emotion/styled"
    "vite"
)

echo -e "\n  Checking critical dependencies:"
for dep in "${CRITICAL_DEPS[@]}"; do
    if node -e "const pkg = JSON.parse(require('fs').readFileSync('package.json', 'utf8')); process.exit(pkg.dependencies['$dep'] || pkg.devDependencies['$dep'] ? 0 : 1)" 2>/dev/null; then
        check_pass "$dep is declared"
    else
        check_fail "$dep is missing from dependencies"
    fi
done

################################################################################
# CHECK 4: node_modules Integrity
################################################################################

print_header "CHECK 4: node_modules Integrity"

if [[ ! -d "node_modules" ]]; then
    check_fail "node_modules directory not found"
    if [[ $FIX_MODE -eq 1 ]]; then
        echo -e "    ${YELLOW}Running npm install...${NC}"
        npm install || check_fail "npm install failed"
    else
        echo -e "    ${YELLOW}Run: npm install${NC}"
    fi
else
    check_pass "node_modules directory exists"

    # Check if node_modules is up-to-date
    if [[ package.json -nt node_modules ]]; then
        check_warn "package.json is newer than node_modules - dependencies may be outdated"
        if [[ $FIX_MODE -eq 1 ]]; then
            echo -e "    ${YELLOW}Running npm install...${NC}"
            npm install || check_warn "npm install encountered issues"
        else
            echo -e "    ${YELLOW}Run: npm install${NC}"
        fi
    else
        check_pass "node_modules appears up-to-date"
    fi
fi

# Check for peer dependency warnings
echo -e "\n  Checking for peer dependency issues:"
if npm list --depth=0 &>/dev/null; then
    check_pass "No missing peer dependencies detected"
else
    check_warn "Some peer dependencies may be missing"
    if [[ $FIX_MODE -eq 1 ]]; then
        echo -e "    ${YELLOW}Attempting to install peer dependencies...${NC}"
        npm install --legacy-peer-deps || check_warn "Could not auto-fix peer dependencies"
    else
        echo -e "    ${YELLOW}Run: npm install --legacy-peer-deps${NC}"
    fi
fi

################################################################################
# CHECK 5: Critical Component Integrity
################################################################################

print_header "CHECK 5: Critical Component Integrity"

# Check SubscriptionManagement component (the one that failed on fresh system)
SUBSCRIPTION_MGMT_PATH="src/pages/admin/SubscriptionManagement.jsx"

if [[ ! -f "$SUBSCRIPTION_MGMT_PATH" ]]; then
    check_fail "SubscriptionManagement.jsx not found at $SUBSCRIPTION_MGMT_PATH"
else
    check_pass "SubscriptionManagement.jsx file exists"

    # Check for export statement
    if grep -q "export default SubscriptionManagement" "$SUBSCRIPTION_MGMT_PATH"; then
        check_pass "SubscriptionManagement has default export"
    else
        check_fail "SubscriptionManagement missing default export"
    fi

    # Check for React import
    if grep -q "import React" "$SUBSCRIPTION_MGMT_PATH"; then
        check_pass "SubscriptionManagement imports React"
    else
        check_warn "SubscriptionManagement doesn't explicitly import React (may use new JSX transform)"
    fi
fi

# Check App.jsx imports it correctly
if grep -q "SubscriptionManagement.*from.*pages/admin/SubscriptionManagement" "src/App.jsx"; then
    check_pass "App.jsx correctly imports SubscriptionManagement"
else
    check_fail "App.jsx has incorrect import path for SubscriptionManagement"
fi

################################################################################
# CHECK 6: Build Configuration
################################################################################

print_header "CHECK 6: Build Configuration"

# Check vite.config.js
if [[ ! -f "vite.config.js" ]]; then
    check_fail "vite.config.js not found"
else
    check_pass "vite.config.js exists"

    # Check for React plugin
    if grep -q "@vitejs/plugin-react" "vite.config.js"; then
        check_pass "Vite React plugin configured"
    else
        check_fail "Vite React plugin not found in config"
    fi
fi

# Check for .env files
if [[ -f ".env" ]]; then
    check_pass ".env file exists"
else
    check_warn ".env file not found (may use .env.example or environment variables)"
fi

################################################################################
# CHECK 7: Circular Dependencies
################################################################################

print_header "CHECK 7: Circular Dependencies"

# Check for common circular dependency patterns
CIRCULAR_PATTERNS=(
    "SystemContext.*OrganizationContext"
    "OrganizationContext.*SystemContext"
)

echo -e "  Checking for circular import patterns:"
CIRCULAR_FOUND=0

for pattern in "${CIRCULAR_PATTERNS[@]}"; do
    if grep -r "$pattern" src/ &>/dev/null; then
        check_warn "Potential circular dependency: $pattern"
        CIRCULAR_FOUND=1
    fi
done

if [[ $CIRCULAR_FOUND -eq 0 ]]; then
    check_pass "No obvious circular dependencies detected"
fi

################################################################################
# CHECK 8: TypeScript Configuration (if applicable)
################################################################################

print_header "CHECK 8: TypeScript Configuration"

if [[ -f "tsconfig.json" ]]; then
    check_warn "tsconfig.json found but project uses .jsx files"
    echo -e "    ${YELLOW}Consider migrating to TypeScript or removing tsconfig.json${NC}"
elif [[ -f "jsconfig.json" ]]; then
    check_pass "jsconfig.json found for JavaScript IntelliSense"
else
    check_warn "No jsconfig.json found - IDE may have limited IntelliSense"
fi

################################################################################
# CHECK 9: Build Output Directory
################################################################################

print_header "CHECK 9: Build Output Directory"

if [[ -d "dist" ]]; then
    check_pass "dist/ directory exists (previous build found)"

    # Check if dist is stale
    if [[ src/ -nt dist/ ]]; then
        check_warn "dist/ appears outdated - src/ has newer changes"
        echo -e "    ${YELLOW}Recommendation: Run fresh build${NC}"
    else
        check_pass "dist/ appears up-to-date"
    fi
else
    check_warn "dist/ directory not found (no previous build)"
    echo -e "    ${YELLOW}This is normal for first-time builds${NC}"
fi

################################################################################
# CHECK 10: Memory & Resource Availability
################################################################################

print_header "CHECK 10: System Resources"

# Check available memory (Linux only)
if [[ -f /proc/meminfo ]]; then
    AVAILABLE_MEM=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    AVAILABLE_MEM_GB=$((AVAILABLE_MEM / 1024 / 1024))

    echo -e "  Available memory: ${BLUE}${AVAILABLE_MEM_GB} GB${NC}"

    if [[ $AVAILABLE_MEM_GB -ge 4 ]]; then
        check_pass "Sufficient memory available (>= 4GB)"
    elif [[ $AVAILABLE_MEM_GB -ge 2 ]]; then
        check_warn "Limited memory (${AVAILABLE_MEM_GB}GB) - builds may be slow"
    else
        check_fail "Insufficient memory (${AVAILABLE_MEM_GB}GB) - build may fail"
        echo -e "    ${RED}Recommendation: Close other applications or increase RAM${NC}"
    fi
else
    check_warn "Unable to check memory (not on Linux)"
fi

################################################################################
# Final Report
################################################################################

print_header "VERIFICATION SUMMARY"

echo -e "  ${GREEN}Passed:${NC}  $PASSED checks"
if [[ $WARNINGS -gt 0 ]]; then
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS checks"
fi
if [[ $FAILED -gt 0 ]]; then
    echo -e "  ${RED}Failed:${NC}  $FAILED checks"
fi

echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo -e "${GREEN}You can proceed with: npm run build${NC}\n"

    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}Note: $WARNINGS warning(s) detected but build should still work${NC}\n"
    fi

    exit 0
else
    echo -e "${RED}✗ $FAILED critical check(s) failed${NC}"
    echo -e "${RED}Please fix the issues above before building${NC}\n"

    if [[ $FIX_MODE -eq 0 ]]; then
        echo -e "${YELLOW}Tip: Run with --fix to attempt automatic repairs:${NC}"
        echo -e "${YELLOW}  ./scripts/verify-build-deps.sh --fix${NC}\n"
    fi

    exit 1
fi
