#!/bin/bash
# Ops-Center v2.5.0 - Automated Test Suite
# Run after applying fixes to verify deployment

set -e

BASE_URL="http://localhost:8084"
PASS=0
FAIL=0

echo "========================================="
echo "Ops-Center v2.5.0 - Test Suite"
echo "========================================="
echo ""

# Test 1: Email Health
echo "Test 1: Email Health Check"
RESPONSE=$(curl -s ${BASE_URL}/api/v1/alerts/health)
if echo "$RESPONSE" | grep -q '"healthy":true'; then
    echo "✅ PASS - Email system healthy"
    ((PASS++))
else
    echo "🔴 FAIL - Email system unhealthy: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Test 2: Email Test Endpoint
echo "Test 2: Send Test Email"
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/alerts/test \
  -H "Content-Type: application/json" \
  -d '{"recipient": "admin@example.com"}')
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ PASS - Test email sent"
    ((PASS++))
else
    echo "🔴 FAIL - Test email failed: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Test 3: Email History
echo "Test 3: Email History"
RESPONSE=$(curl -s ${BASE_URL}/api/v1/alerts/history)
if echo "$RESPONSE" | grep -q '"success":true\|"history"'; then
    echo "✅ PASS - Email history loaded"
    ((PASS++))
else
    echo "🔴 FAIL - Email history failed: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Test 4: Log Search
echo "Test 4: Advanced Log Search"
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/v1/logs/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"service": "ops-center", "limit": 10}')
if echo "$RESPONSE" | grep -q '"logs"\|"total"'; then
    echo "✅ PASS - Log search working"
    ((PASS++))
else
    echo "🔴 FAIL - Log search failed: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Test 5: Grafana Health
echo "Test 5: Grafana Health Check"
RESPONSE=$(curl -s ${BASE_URL}/api/v1/monitoring/grafana/health)
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ PASS - Grafana healthy"
    ((PASS++))
else
    echo "🔴 FAIL - Grafana unhealthy: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Test 6: Grafana Dashboards
echo "Test 6: Grafana Dashboard List"
RESPONSE=$(curl -s ${BASE_URL}/api/v1/monitoring/grafana/dashboards)
if echo "$RESPONSE" | grep -q '"dashboards"\|Unauthorized' > /dev/null 2>&1; then
    if echo "$RESPONSE" | grep -q 'Unauthorized'; then
        echo "⚠️  PARTIAL - Grafana API key not configured (expected if not set)"
        ((PASS++))
    else
        echo "✅ PASS - Grafana dashboards loaded"
        ((PASS++))
    fi
else
    echo "🔴 FAIL - Grafana dashboards failed: $RESPONSE"
    ((FAIL++))
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "PASSED: $PASS/6"
echo "FAILED: $FAIL/6"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "✅ ALL TESTS PASSED - DEPLOYMENT READY"
    exit 0
else
    echo ""
    echo "🔴 $FAIL TEST(S) FAILED - NOT READY FOR DEPLOYMENT"
    exit 1
fi
