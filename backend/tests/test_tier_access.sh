#!/bin/bash
#
# Test Tier-Based Model Access
# =============================
#
# This script tests that each subscription tier can only access
# the appropriate models based on their pricing/access rules.
#
# Expected Model Counts:
# - Trial: 50-80 models (free/cheap only)
# - Starter: 150-200 models
# - Professional: 250-300 models
# - Enterprise: 370+ models (all models)
#
# Author: Ops-Center Team
# Date: November 6, 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API endpoint
API_BASE="http://localhost:8084/api/v1"

# Test users file
TEST_USERS_FILE="/home/muut/Production/UC-Cloud/services/ops-center/backend/tests/test_users.json"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Testing Tier-Based Model Access                          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if test users file exists
if [ ! -f "$TEST_USERS_FILE" ]; then
    echo -e "${RED}❌ Test users file not found: $TEST_USERS_FILE${NC}"
    echo -e "${YELLOW}Run create_test_users.py first to create test users.${NC}"
    exit 1
fi

# Extract user IDs from JSON
TRIAL_USER=$(jq -r '.test_users[] | select(.tier == "trial") | .user_id' "$TEST_USERS_FILE")
STARTER_USER=$(jq -r '.test_users[] | select(.tier == "starter") | .user_id' "$TEST_USERS_FILE")
PROFESSIONAL_USER=$(jq -r '.test_users[] | select(.tier == "professional") | .user_id' "$TEST_USERS_FILE")
ENTERPRISE_USER=$(jq -r '.test_users[] | select(.tier == "enterprise") | .user_id' "$TEST_USERS_FILE")

echo -e "${BLUE}Test Users Loaded:${NC}"
echo "  Trial: $TRIAL_USER"
echo "  Starter: $STARTER_USER"
echo "  Professional: $PROFESSIONAL_USER"
echo "  Enterprise: $ENTERPRISE_USER"
echo ""

# Function to test model access for a tier
test_tier_access() {
    local tier=$1
    local user_id=$2
    local expected_min=$3
    local expected_max=$4

    echo -e "${YELLOW}Testing ${tier} User...${NC}"

    # Get available models (passing user_id to filter by tier)
    response=$(curl -s "${API_BASE}/llm/models/available?user_id=${user_id}")

    # Count models
    model_count=$(echo "$response" | jq '. | length')

    # Display results
    echo -e "  User ID: ${user_id}"
    echo -e "  Models Available: ${model_count}"
    echo -e "  Expected Range: ${expected_min}-${expected_max}"

    # Check if within expected range
    if [ "$model_count" -ge "$expected_min" ] && [ "$model_count" -le "$expected_max" ]; then
        echo -e "  ${GREEN}✓ PASS${NC} - Model count within expected range"
    else
        echo -e "  ${RED}✗ FAIL${NC} - Model count outside expected range"
    fi

    # Show sample of available models (first 5)
    echo -e "  Sample models:"
    echo "$response" | jq -r '.[:5] | .[] | "    - \(.id) (\(.provider))"'

    echo ""
}

# Test each tier
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Running Tests                                             ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

test_tier_access "TRIAL" "$TRIAL_USER" 50 80
test_tier_access "STARTER" "$STARTER_USER" 150 200
test_tier_access "PROFESSIONAL" "$PROFESSIONAL_USER" 250 300
test_tier_access "ENTERPRISE" "$ENTERPRISE_USER" 370 500

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Test Summary                                              ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✓ Tier-based model access tests completed${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Verify model counts match expectations"
echo "2. Check that trial users can't access premium models"
echo "3. Ensure enterprise users see all available models"
echo "4. Test API key generation for each tier"
echo ""
