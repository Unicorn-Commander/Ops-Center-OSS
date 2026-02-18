#!/bin/bash
# Ops-Center Monitoring Test Script
# Tests all monitoring components

set -e

echo "================================================"
echo "Ops-Center Monitoring Test Suite"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1 || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $response)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "1. Testing Container Status"
echo "----------------------------"

containers=("ops-center-prometheus" "ops-center-grafana" "ops-center-alertmanager" "ops-center-node-exporter" "ops-center-cadvisor" "ops-center-redis-exporter" "ops-center-postgres-exporter")

for container in "${containers[@]}"; do
    TESTS_RUN=$((TESTS_RUN + 1))
    if docker ps | grep -q "$container"; then
        echo -e "${GREEN}✓${NC} $container is running"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $container is NOT running"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

echo ""
echo "2. Testing Prometheus"
echo "---------------------"

test_endpoint "Prometheus Health" "http://localhost:9090/-/healthy"
test_endpoint "Prometheus Targets" "http://localhost:9090/api/v1/targets"
test_endpoint "Prometheus Rules" "http://localhost:9090/api/v1/rules"

# Test specific metrics
TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Testing Ops-Center metrics... "
metrics=$(curl -s http://ops-center-direct:8084/metrics 2>&1 || echo "")
if echo "$metrics" | grep -q "ops_center_api_requests_total"; then
    echo -e "${GREEN}✓ PASS${NC} (Metrics endpoint working)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Metrics endpoint not responding)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "3. Testing Grafana"
echo "------------------"

test_endpoint "Grafana Health" "http://localhost:3000/api/health"
test_endpoint "Grafana Login" "http://localhost:3000/login" 302

# Test datasource
TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Testing Grafana Datasource... "
datasource=$(curl -s -u admin:your-admin-password http://localhost:3000/api/datasources 2>&1 || echo "[]")
if echo "$datasource" | grep -q "Prometheus"; then
    echo -e "${GREEN}✓ PASS${NC} (Prometheus datasource configured)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARN${NC} (Prometheus datasource not found)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "4. Testing Alertmanager"
echo "-----------------------"

test_endpoint "Alertmanager Health" "http://localhost:9093/-/healthy"
test_endpoint "Alertmanager Status" "http://localhost:9093/api/v1/status"

# Send test alert
TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Sending test alert... "
alert_response=$(curl -s -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "labels": {
        "alertname": "TestAlert",
        "severity": "medium",
        "service": "test"
      },
      "annotations": {
        "summary": "This is a test alert from test script",
        "description": "Testing Alertmanager notification routing"
      }
    }
  ]' 2>&1 || echo "error")

if echo "$alert_response" | grep -q "success\|Accepted"; then
    echo -e "${GREEN}✓ PASS${NC} (Test alert sent)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "  ${YELLOW}→${NC} Check Slack/Email for test alert notification"
else
    echo -e "${RED}✗ FAIL${NC} (Failed to send test alert)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "5. Testing Exporters"
echo "--------------------"

test_endpoint "Node Exporter" "http://localhost:9100/metrics"
test_endpoint "Redis Exporter" "http://localhost:9121/metrics"
test_endpoint "Postgres Exporter" "http://localhost:9187/metrics"
test_endpoint "cAdvisor" "http://localhost:8080/metrics"

echo ""
echo "6. Validating Configurations"
echo "-----------------------------"

TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Validating Prometheus config... "
config_check=$(docker exec ops-center-prometheus promtool check config /etc/prometheus/prometheus.yml 2>&1)
if echo "$config_check" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✓ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "$config_check"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Validating alert rules... "
rules_check=$(docker exec ops-center-prometheus promtool check rules /etc/prometheus/alert-rules.yml 2>&1)
if echo "$rules_check" | grep -q "SUCCESS"; then
    echo -e "${GREEN}✓ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "$rules_check"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "7. Testing Alert Rules"
echo "----------------------"

# Check if alerts are loaded
TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Checking loaded alert rules... "
rules=$(curl -s http://localhost:9090/api/v1/rules 2>&1)
rule_count=$(echo "$rules" | grep -o '"alertname"' | wc -l)
if [ "$rule_count" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($rule_count alerts loaded)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No alert rules loaded)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "8. Testing Metrics Collection"
echo "------------------------------"

# Check if Prometheus is scraping targets
TESTS_RUN=$((TESTS_RUN + 1))
echo -n "Checking scrape targets... "
targets=$(curl -s http://localhost:9090/api/v1/targets 2>&1)
active_targets=$(echo "$targets" | grep -o '"health":"up"' | wc -l)
if [ "$active_targets" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} ($active_targets targets UP)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARN${NC} (No targets are UP yet)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test sample queries
echo ""
echo "Testing sample PromQL queries..."

queries=(
    "up"
    "ops_center_api_requests_total"
    "node_cpu_seconds_total"
    "redis_up"
    "pg_up"
)

for query in "${queries[@]}"; do
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "  Query: $query... "
    result=$(curl -s "http://localhost:9090/api/v1/query?query=$query" 2>&1)
    if echo "$result" | grep -q '"status":"success"'; then
        echo -e "${GREEN}✓${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠${NC} (No data yet)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo "Total Tests: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Access Grafana: https://monitoring.unicorncommander.ai"
    echo "2. Login with: admin / your-admin-password"
    echo "3. Import dashboards from grafana.com"
    echo "4. Configure Slack webhook in alertmanager.yml"
    echo "5. Configure PagerDuty integration key"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review errors above.${NC}"
    echo ""
    echo "Common issues:"
    echo "- Services may still be starting up (wait 1-2 minutes)"
    echo "- Check container logs: docker logs <container-name>"
    echo "- Verify network connectivity between containers"
    echo "- Ensure Ops-Center has /metrics endpoint enabled"
    exit 1
fi
