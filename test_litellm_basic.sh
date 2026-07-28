#!/bin/bash

# LiteLLM Basic Deployment Tests
# Version: 1.0.0
# Usage: ./test_litellm_basic.sh

set -e

echo "=========================================="
echo "LiteLLM Deployment Basic Tests"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
}

# Test 1: Database Tables Exist
echo "Test 1: Database Tables"
echo "------------------------"
TABLE_COUNT=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'litellm%';" 2>/dev/null || echo "0")
TABLE_COUNT=$(echo $TABLE_COUNT | xargs)

if [ "$TABLE_COUNT" -eq "7" ]; then
    pass "All 7 LiteLLM tables exist"

    # List tables
    echo "   Tables found:"
    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt litellm*" | grep litellm | awk '{print "   -", $3}'
else
    fail "Expected 7 tables, found $TABLE_COUNT"
    warn "Run: docker exec ops-center-direct python3 /app/scripts/initialize_litellm_db.py"
fi
echo ""

# Test 2: Backend Health
echo "Test 2: Ops-Center Backend Health"
echo "----------------------------------"
BACKEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8084/api/v1/llm/health 2>/dev/null || echo "000")

if [ "$BACKEND_RESPONSE" -eq "200" ]; then
    pass "Ops-Center LLM health endpoint responding"

    # Show response
    HEALTH_DATA=$(curl -s http://localhost:8084/api/v1/llm/health 2>/dev/null)
    echo "   Response: $HEALTH_DATA"
else
    fail "Ops-Center backend not responding (HTTP $BACKEND_RESPONSE)"
    warn "Check: docker logs ops-center-direct --tail 50"
fi
echo ""

# Test 3: LiteLLM Proxy Health
echo "Test 3: LiteLLM Proxy Health"
echo "----------------------------"
LITELLM_RUNNING=$(docker ps --filter "name=unicorn-litellm-wilmer" --format "{{.Status}}" | grep -c "Up" || echo "0")

if [ "$LITELLM_RUNNING" -eq "1" ]; then
    pass "LiteLLM container is running"

    # Check health endpoint
    PROXY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/health 2>/dev/null || echo "000")

    if [ "$PROXY_RESPONSE" -eq "200" ]; then
        pass "LiteLLM proxy health check passing"
    else
        fail "LiteLLM proxy not responding (HTTP $PROXY_RESPONSE)"
        warn "Check: docker logs unicorn-litellm-wilmer --tail 50"
    fi
else
    fail "LiteLLM container not running"
    warn "Start: docker compose -f docker-compose.litellm.yml up -d"
fi
echo ""

# Test 4: Available Models
echo "Test 4: Available Models"
echo "------------------------"
MODELS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8084/api/v1/llm/models 2>/dev/null || echo "000")

if [ "$MODELS_RESPONSE" -eq "200" ]; then
    MODEL_COUNT=$(curl -s http://localhost:8084/api/v1/llm/models 2>/dev/null | grep -o '"model_name"' | wc -l)

    if [ "$MODEL_COUNT" -gt "0" ]; then
        pass "Models endpoint returning $MODEL_COUNT models"

        # Show first 5 models
        echo "   First 5 models:"
        curl -s http://localhost:8084/api/v1/llm/models 2>/dev/null | grep -o '"model_name":"[^"]*"' | head -5 | sed 's/"model_name":"//g' | sed 's/"//g' | awk '{print "   -", $0}'
    else
        warn "Models endpoint responding but no models found"
    fi
else
    fail "Models endpoint not responding (HTTP $MODELS_RESPONSE)"
fi
echo ""

# Test 5: Database Credit Tables
echo "Test 5: Credit System Tables"
echo "----------------------------"
CREDIT_USERS=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM litellm_user_credits;" 2>/dev/null || echo "ERROR")

if [ "$CREDIT_USERS" != "ERROR" ] && [ "$CREDIT_USERS" -gt "0" ]; then
    CREDIT_USERS=$(echo $CREDIT_USERS | xargs)
    pass "Credit system initialized for $CREDIT_USERS users"

    # Show total credits
    TOTAL_CREDITS=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT SUM(credits_remaining) FROM litellm_user_credits;" 2>/dev/null | xargs)
    echo "   Total platform credits: $TOTAL_CREDITS"
else
    warn "Credit system not initialized or no users found"
    warn "Run: docker exec ops-center-direct python3 /app/scripts/initialize_litellm_db.py"
fi
echo ""

# Test 6: Provider Configuration
echo "Test 6: Provider Configuration"
echo "------------------------------"
PROVIDER_COUNT=$(docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -t -c "SELECT COUNT(*) FROM litellm_providers;" 2>/dev/null || echo "0")
PROVIDER_COUNT=$(echo $PROVIDER_COUNT | xargs)

if [ "$PROVIDER_COUNT" -gt "0" ]; then
    pass "Found $PROVIDER_COUNT providers configured"

    # List providers
    echo "   Providers:"
    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT provider_name, is_active FROM litellm_providers LIMIT 10;" 2>/dev/null | grep -v "^-" | grep -v "row" | tail -n +3 | awk '{print "   -", $1, "(active:", $3 ")"}'
else
    warn "No providers configured in database"
fi
echo ""

# Test 7: WilmerAI Router
echo "Test 7: WilmerAI Router Service"
echo "--------------------------------"
WILMER_RUNNING=$(docker ps --filter "name=unicorn-wilmer-router" --format "{{.Status}}" | grep -c "Up" || echo "0")

if [ "$WILMER_RUNNING" -eq "1" ]; then
    pass "WilmerAI router container is running"

    # Check health endpoint
    WILMER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4001/health 2>/dev/null || echo "000")

    if [ "$WILMER_RESPONSE" -eq "200" ]; then
        pass "WilmerAI router health check passing"
    else
        warn "WilmerAI router not responding on port 4001"
    fi
else
    warn "WilmerAI router container not running (optional service)"
fi
echo ""

# Test 8: Network Connectivity
echo "Test 8: Network Connectivity"
echo "----------------------------"
# Test if ops-center can reach litellm
NETWORK_TEST=$(docker exec ops-center-direct curl -s -o /dev/null -w "%{http_code}" http://unicorn-litellm-wilmer:4000/health 2>/dev/null || echo "000")

if [ "$NETWORK_TEST" -eq "200" ]; then
    pass "Ops-Center can communicate with LiteLLM proxy"
else
    fail "Network connectivity issue between ops-center and litellm"
    warn "Check: docker network inspect unicorn-network | grep -A 10 ops-center"
fi
echo ""

# Test 9: Configuration Files
echo "Test 9: Configuration Files"
echo "---------------------------"
if [ -f "litellm_config.yaml" ]; then
    pass "litellm_config.yaml exists"

    # Count models in config
    MODEL_COUNT=$(grep "model_name:" litellm_config.yaml | wc -l)
    echo "   Models configured: $MODEL_COUNT"
else
    fail "litellm_config.yaml not found"
fi

if [ -f "docker-compose.litellm.yml" ]; then
    pass "docker-compose.litellm.yml exists"
else
    fail "docker-compose.litellm.yml not found"
fi

if [ -f ".env.litellm" ]; then
    pass ".env.litellm exists"

    # Check for required keys (without showing values)
    if grep -q "LITELLM_MASTER_KEY=" .env.litellm 2>/dev/null; then
        echo "   ✓ LITELLM_MASTER_KEY set"
    else
        warn "   LITELLM_MASTER_KEY not set"
    fi

    if grep -q "GROQ_API_KEY=" .env.litellm 2>/dev/null; then
        echo "   ✓ GROQ_API_KEY set (free tier recommended)"
    else
        warn "   GROQ_API_KEY not set (recommended for testing)"
    fi
else
    warn ".env.litellm not found (required for production)"
    warn "Create from template: cp .env.litellm.example .env.litellm"
fi
echo ""

# Test 10: Dependencies
echo "Test 10: Python Dependencies"
echo "----------------------------"
LITELLM_INSTALLED=$(docker exec ops-center-direct python3 -c "import litellm; print('INSTALLED')" 2>/dev/null || echo "MISSING")

if [ "$LITELLM_INSTALLED" = "INSTALLED" ]; then
    pass "litellm package installed in ops-center"

    # Get version
    VERSION=$(docker exec ops-center-direct python3 -c "import litellm; print(litellm.__version__)" 2>/dev/null || echo "unknown")
    echo "   Version: $VERSION"
else
    fail "litellm package not installed"
    warn "Add to requirements.txt: litellm>=1.40.0"
    warn "Rebuild: docker compose -f docker-compose.direct.yml build"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Success Rate: $SUCCESS_RATE% ($TESTS_PASSED/$TOTAL_TESTS)"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! LiteLLM deployment ready.${NC}"
    exit 0
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠ Most tests passed, but some issues need attention.${NC}"
    echo "Review warnings above and fix before production deployment."
    exit 1
else
    echo -e "${RED}✗ Multiple critical issues detected.${NC}"
    echo "Address failed tests before proceeding."
    exit 1
fi
