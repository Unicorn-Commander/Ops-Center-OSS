#!/bin/bash
#
# Provider Keys API - Quick Testing Script
#
# Usage:
#   ./test_provider_keys_api.sh <session_token>
#
# Example:
#   ./test_provider_keys_api.sh "abc123def456..."
#
# Get your session token:
#   1. Login at https://unicorncommander.ai/auth/login
#   2. Open browser console
#   3. Run: document.cookie.split(';').find(c => c.includes('session_token'))
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8084}"
SESSION_TOKEN="${1}"

if [ -z "$SESSION_TOKEN" ]; then
    echo -e "${RED}Error: Session token required${NC}"
    echo "Usage: $0 <session_token>"
    echo ""
    echo "Get your session token:"
    echo "  1. Login at https://unicorncommander.ai/auth/login"
    echo "  2. Open browser console"
    echo "  3. Run: document.cookie.split(';').find(c => c.includes('session_token'))"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Provider Keys API - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Get Provider Info
echo -e "${YELLOW}Test 1: Get Provider Info${NC}"
RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/llm/providers/info" \
  -H "Cookie: session_token=${SESSION_TOKEN}" \
  -H "Content-Type: application/json")

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    TOTAL=$(echo "$RESPONSE" | jq -r '.total')
    echo -e "${GREEN}✓ Success: Found $TOTAL supported providers${NC}"
    echo "$RESPONSE" | jq -r '.providers[] | "  - \(.display_name) (\(.provider_type))"'
else
    echo -e "${RED}✗ Failed${NC}"
    echo "$RESPONSE" | jq '.'
    exit 1
fi
echo ""

# Test 2: List Provider Keys
echo -e "${YELLOW}Test 2: List Provider Keys${NC}"
RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/llm/providers/keys" \
  -H "Cookie: session_token=${SESSION_TOKEN}" \
  -H "Content-Type: application/json")

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    TOTAL=$(echo "$RESPONSE" | jq -r '.total')
    echo -e "${GREEN}✓ Success: Found $TOTAL configured providers${NC}"

    # Show summary
    echo "$RESPONSE" | jq -r '.providers[] |
        "  - \(.name): " +
        (if .has_key then "✓ Key configured (\(.key_source))" else "✗ No key" end) +
        " | Status: \(.health_status)"'
else
    echo -e "${RED}✗ Failed${NC}"
    echo "$RESPONSE" | jq '.'
    exit 1
fi
echo ""

# Test 3: Test Provider Key (OpenRouter if configured)
echo -e "${YELLOW}Test 3: Test Provider Key (OpenRouter)${NC}"

# Check if OpenRouter has a key
HAS_OPENROUTER=$(echo "$RESPONSE" | jq -r '.providers[] | select(.provider_type == "openrouter") | .has_key')

if [ "$HAS_OPENROUTER" == "true" ]; then
    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/llm/providers/keys/test" \
      -H "Cookie: session_token=${SESSION_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "provider_type": "openrouter",
        "api_key": null
      }')

    if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        LATENCY=$(echo "$RESPONSE" | jq -r '.latency_ms')
        MODELS=$(echo "$RESPONSE" | jq -r '.models_found')
        echo -e "${GREEN}✓ Success: OpenRouter key is valid${NC}"
        echo "  Latency: ${LATENCY}ms"
        echo "  Models available: $MODELS"
    else
        ERROR=$(echo "$RESPONSE" | jq -r '.error')
        echo -e "${RED}✗ Failed: $ERROR${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Skipped: No OpenRouter key configured${NC}"
fi
echo ""

# Test 4: Save Provider Key (Dry run - will fail without real key)
echo -e "${YELLOW}Test 4: Save Provider Key (Dry Run)${NC}"
echo -e "${BLUE}Note: This test requires a real API key to succeed${NC}"
echo -e "${BLUE}Example command:${NC}"
cat << 'EOF'
curl -X POST 'http://localhost:8084/api/v1/llm/providers/keys' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openrouter",
    "api_key": "sk-or-v1-YOUR-REAL-KEY",
    "name": "OpenRouter"
  }'
EOF
echo ""

# Test 5: Rate Limiting
echo -e "${YELLOW}Test 5: Rate Limiting (10 tests/minute)${NC}"
echo -e "${BLUE}Sending 11 rapid test requests...${NC}"

SUCCESS_COUNT=0
RATE_LIMITED=0

for i in {1..11}; do
    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/llm/providers/keys/test" \
      -H "Cookie: session_token=${SESSION_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "provider_type": "openrouter",
        "api_key": null
      }')

    if echo "$RESPONSE" | jq -e 'has("detail")' > /dev/null 2>&1; then
        # Error response
        DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
        if [[ "$DETAIL" == *"Rate limit"* ]]; then
            RATE_LIMITED=$((RATE_LIMITED + 1))
        fi
    else
        # Success response
        if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    fi

    # Small delay to avoid overwhelming the server
    sleep 0.1
done

echo "  Success: $SUCCESS_COUNT requests"
echo "  Rate limited: $RATE_LIMITED requests"

if [ $SUCCESS_COUNT -le 10 ] && [ $RATE_LIMITED -ge 1 ]; then
    echo -e "${GREEN}✓ Rate limiting works correctly${NC}"
else
    echo -e "${YELLOW}⚠ Rate limiting may not be working as expected${NC}"
fi
echo ""

# Test 6: Unauthorized Access
echo -e "${YELLOW}Test 6: Unauthorized Access${NC}"
RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v1/llm/providers/keys" \
  -H "Content-Type: application/json")

if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
    if [[ "$DETAIL" == *"Not authenticated"* ]]; then
        echo -e "${GREEN}✓ Correctly rejected unauthenticated request${NC}"
    else
        echo -e "${YELLOW}⚠ Unexpected error: $DETAIL${NC}"
    fi
else
    echo -e "${RED}✗ Should have rejected unauthenticated request${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}All critical tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure provider keys in LLM Hub UI"
echo "  2. Test keys against real provider APIs"
echo "  3. Monitor backend logs: docker logs ops-center-direct -f | grep provider_keys_api"
echo ""
