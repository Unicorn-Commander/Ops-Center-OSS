#!/bin/bash
# Test script for service discovery implementation

set -e

echo "================================================"
echo "UC-1 Pro Service Discovery Test Suite"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "1. Testing Backend Module Import"
echo "=================================="
python3 -c "from backend.service_discovery import service_discovery; print('Module loaded successfully')" 2>&1
test_result $? "Backend module import"
echo ""

echo "2. Testing Service Discovery API Endpoint"
echo "========================================="
# Check if server is running
if curl -s -f http://localhost:8084/api/v1/services/discovery > /dev/null; then
    echo -e "${GREEN}Server is running${NC}"

    # Test discovery endpoint
    RESPONSE=$(curl -s http://localhost:8084/api/v1/services/discovery)

    # Check if response contains expected fields
    if echo "$RESPONSE" | jq -e '.services' > /dev/null 2>&1; then
        test_result 0 "Discovery endpoint returns services"
    else
        test_result 1 "Discovery endpoint returns services"
    fi

    if echo "$RESPONSE" | jq -e '.internal_urls' > /dev/null 2>&1; then
        test_result 0 "Discovery endpoint returns internal_urls"
    else
        test_result 1 "Discovery endpoint returns internal_urls"
    fi

    if echo "$RESPONSE" | jq -e '.external_urls' > /dev/null 2>&1; then
        test_result 0 "Discovery endpoint returns external_urls"
    else
        test_result 1 "Discovery endpoint returns external_urls"
    fi

    if echo "$RESPONSE" | jq -e '.deployment' > /dev/null 2>&1; then
        test_result 0 "Discovery endpoint returns deployment info"
    else
        test_result 1 "Discovery endpoint returns deployment info"
    fi

    echo ""
    echo "Discovered Services:"
    echo "$RESPONSE" | jq -r '.internal_urls | to_entries | .[] | "  - \(.key): \(.value)"'
    echo ""
else
    echo -e "${YELLOW}⚠ Server not running - skipping API tests${NC}"
    echo "  Start server with: cd /home/muut/Production/UC-1-Pro/services/ops-center && python3 backend/server.py"
fi
echo ""

echo "3. Testing Service URL Resolution"
echo "================================="
python3 << 'PYTHON_TEST'
import sys
sys.path.insert(0, 'backend')

from service_discovery import service_discovery

# Test URL resolution for each service
services = ['ollama', 'vllm', 'openwebui', 'embeddings', 'reranker']
for service in services:
    url = service_discovery.get_service_url(service)
    print(f"  - {service}: {url}")
PYTHON_TEST
test_result $? "Service URL resolution"
echo ""

echo "4. Testing Environment Variable Override"
echo "========================================"
export OLLAMA_URL="http://custom-ollama:11434"
python3 << 'PYTHON_TEST'
import sys
import os
sys.path.insert(0, 'backend')

from service_discovery import service_discovery

# Refresh to pick up new env var
service_discovery._init_docker_client()
url = service_discovery.get_service_url('ollama')

if url == "http://custom-ollama:11434":
    print(f"  ✓ Environment override works: {url}")
    sys.exit(0)
else:
    print(f"  ✗ Environment override failed: expected http://custom-ollama:11434, got {url}")
    sys.exit(1)
PYTHON_TEST
test_result $? "Environment variable override"
unset OLLAMA_URL
echo ""

echo "5. Testing Docker Container Discovery"
echo "====================================="
# Check if Docker is available
if command -v docker &> /dev/null; then
    # List UC-1 Pro containers
    echo "  Running UC-1 Pro containers:"
    docker ps --filter "name=unicorn-" --format "  - {{.Names}} ({{.Status}})" | head -5
    test_result 0 "Docker container listing"
else
    echo -e "${YELLOW}  ⚠ Docker not available - skipping container discovery tests${NC}"
fi
echo ""

echo "6. Testing File Existence"
echo "========================="
FILES=(
    "backend/service_discovery.py"
    ".env.template"
    "SERVICE_DISCOVERY_IMPLEMENTATION.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        test_result 0 "File exists: $file"
    else
        test_result 1 "File exists: $file"
    fi
done
echo ""

echo "7. Testing Configuration Files"
echo "=============================="

# Check if .env.template has required variables
REQUIRED_VARS=(
    "OLLAMA_URL"
    "OPENWEBUI_URL"
    "VLLM_URL"
    "EMBEDDINGS_URL"
    "RERANKER_URL"
    "EXTERNAL_HOST"
    "EXTERNAL_PROTOCOL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "$var" .env.template; then
        test_result 0 ".env.template contains $var"
    else
        test_result 1 ".env.template contains $var"
    fi
done
echo ""

echo "8. Testing modelApi.js Updates"
echo "=============================="
if [ -f "src/services/modelApi.js" ]; then
    # Check for new methods
    if grep -q "discoverServices" src/services/modelApi.js; then
        test_result 0 "modelApi.js has discoverServices method"
    else
        test_result 1 "modelApi.js has discoverServices method"
    fi

    if grep -q "getServiceUrl" src/services/modelApi.js; then
        test_result 0 "modelApi.js has getServiceUrl method"
    else
        test_result 1 "modelApi.js has getServiceUrl method"
    fi

    if grep -q "refreshServiceDiscovery" src/services/modelApi.js; then
        test_result 0 "modelApi.js has refreshServiceDiscovery method"
    else
        test_result 1 "modelApi.js has refreshServiceDiscovery method"
    fi
else
    test_result 1 "modelApi.js file exists"
fi
echo ""

echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Review the output above.${NC}"
    exit 1
fi
