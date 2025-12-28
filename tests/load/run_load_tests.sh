#!/bin/bash
# ============================================================================
# Load Testing Automation Script
# ============================================================================
# Runs comprehensive load tests and generates performance reports
#
# Usage:
#   ./run_load_tests.sh --tool locust --duration 300
#   ./run_load_tests.sh --tool k6 --vus 1000
#   ./run_load_tests.sh --all
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8084}"
RESULTS_DIR="results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
TOOL="locust"
DURATION=300
VUS=100
SPAWN_RATE=10

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --tool)
      TOOL="$2"
      shift 2
      ;;
    --duration)
      DURATION="$2"
      shift 2
      ;;
    --vus)
      VUS="$2"
      shift 2
      ;;
    --spawn-rate)
      SPAWN_RATE="$2"
      shift 2
      ;;
    --all)
      RUN_ALL=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --tool TOOL          Testing tool (locust|k6|both)"
      echo "  --duration SECONDS   Test duration in seconds"
      echo "  --vus NUMBER         Virtual users (k6 only)"
      echo "  --spawn-rate RATE    User spawn rate (locust only)"
      echo "  --all                Run all tests (benchmark + load + stress)"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Ops-Center Performance Testing Suite                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Base URL:        $BASE_URL"
echo -e "  Testing Tool:    $TOOL"
echo -e "  Duration:        ${DURATION}s"
echo -e "  Virtual Users:   $VUS"
echo -e "  Results Dir:     $RESULTS_DIR"
echo ""

# ============================================================================
# Check Prerequisites
# ============================================================================

echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if API is accessible
if curl -s -f -o /dev/null "$BASE_URL/api/v1/health" 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} API is accessible at $BASE_URL"
else
  echo -e "  ${RED}✗${NC} API is not accessible at $BASE_URL"
  echo -e "  ${YELLOW}Make sure the Ops-Center backend is running${NC}"
  exit 1
fi

# Check for required tools
if [ "$TOOL" = "locust" ] || [ "$TOOL" = "both" ]; then
  if ! command -v locust &> /dev/null; then
    echo -e "  ${YELLOW}⚠${NC} Locust not found. Installing..."
    pip install locust
  else
    echo -e "  ${GREEN}✓${NC} Locust is installed ($(locust --version))"
  fi
fi

if [ "$TOOL" = "k6" ] || [ "$TOOL" = "both" ]; then
  if ! command -v k6 &> /dev/null; then
    echo -e "  ${YELLOW}⚠${NC} k6 not found. Installing..."
    # Install k6 (Linux)
    if [ -f /etc/debian_version ]; then
      sudo gpg -k
      sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
      echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
      sudo apt-get update
      sudo apt-get install k6
    else
      echo -e "  ${RED}✗${NC} Please install k6 manually: https://k6.io/docs/getting-started/installation/"
      exit 1
    fi
  else
    echo -e "  ${GREEN}✓${NC} k6 is installed ($(k6 version))"
  fi
fi

echo ""

# ============================================================================
# Run Baseline Benchmark
# ============================================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Phase 1: Baseline Performance Benchmark${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""

python3 ../performance/benchmark.py \
  --endpoint all \
  --iterations 1000 \
  --base-url "$BASE_URL" \
  --output "$RESULTS_DIR/baseline_${TIMESTAMP}.json"

echo ""

# ============================================================================
# Run Load Tests
# ============================================================================

if [ "$TOOL" = "locust" ] || [ "$TOOL" = "both" ]; then
  echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
  echo -e "${YELLOW}Phase 2: Locust Load Testing${NC}"
  echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
  echo ""

  LOCUST_FILE="locustfile.py"
  LOCUST_REPORT="$RESULTS_DIR/locust_report_${TIMESTAMP}.html"

  echo -e "${GREEN}Starting Locust load test...${NC}"
  echo -e "  Users: $VUS"
  echo -e "  Spawn rate: $SPAWN_RATE users/second"
  echo -e "  Duration: ${DURATION}s"
  echo ""

  locust \
    -f "$LOCUST_FILE" \
    --host="$BASE_URL" \
    --users="$VUS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="${DURATION}s" \
    --headless \
    --html="$LOCUST_REPORT" \
    --csv="$RESULTS_DIR/locust_${TIMESTAMP}" \
    --loglevel WARNING

  echo ""
  echo -e "${GREEN}✓ Locust report saved to: $LOCUST_REPORT${NC}"
  echo ""
fi

if [ "$TOOL" = "k6" ] || [ "$TOOL" = "both" ]; then
  echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
  echo -e "${YELLOW}Phase 3: k6 Load Testing${NC}"
  echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
  echo ""

  K6_SCRIPT="k6_load_test.js"
  K6_REPORT="$RESULTS_DIR/k6_results_${TIMESTAMP}.json"

  echo -e "${GREEN}Starting k6 load test...${NC}"
  echo ""

  BASE_URL="$BASE_URL" k6 run \
    --out json="$K6_REPORT" \
    --summary-export="$RESULTS_DIR/k6_summary_${TIMESTAMP}.json" \
    "$K6_SCRIPT"

  echo ""
  echo -e "${GREEN}✓ k6 results saved to: $K6_REPORT${NC}"
  echo ""
fi

# ============================================================================
# Analyze Results
# ============================================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Phase 4: Results Analysis${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}Performance Test Summary${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

# Parse k6 summary if available
if [ -f "$RESULTS_DIR/k6_summary_${TIMESTAMP}.json" ]; then
  echo ""
  echo -e "${BLUE}k6 Test Results:${NC}"

  python3 -c "
import json
with open('$RESULTS_DIR/k6_summary_${TIMESTAMP}.json') as f:
    data = json.load(f)
    metrics = data.get('metrics', {})

    print(f\"  Total Requests:     {metrics.get('http_reqs', {}).get('count', 0)}\")
    print(f\"  Failed Requests:    {metrics.get('http_req_failed', {}).get('count', 0)}\")
    print(f\"  Avg Response Time:  {metrics.get('http_req_duration', {}).get('values', {}).get('avg', 0):.2f}ms\")
    print(f\"  p95 Response Time:  {metrics.get('http_req_duration', {}).get('values', {}).get('p(95)', 0):.2f}ms\")
    print(f\"  p99 Response Time:  {metrics.get('http_req_duration', {}).get('values', {}).get('p(99)', 0):.2f}ms\")

    # Check if thresholds passed
    for name, threshold in data.get('thresholds', {}).items():
        status = '✓ PASS' if threshold['ok'] else '✗ FAIL'
        print(f\"  Threshold {name}: {status}\")
"
fi

# Parse locust results if available
if [ -f "$RESULTS_DIR/locust_${TIMESTAMP}_stats.csv" ]; then
  echo ""
  echo -e "${BLUE}Locust Test Results:${NC}"

  python3 -c "
import csv
with open('$RESULTS_DIR/locust_${TIMESTAMP}_stats.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    total_requests = sum(int(r.get('Request Count', 0)) for r in rows if r.get('Type') != 'Aggregated')
    failed_requests = sum(int(r.get('Failure Count', 0)) for r in rows if r.get('Type') != 'Aggregated')
    avg_response = sum(float(r.get('Average Response Time', 0)) for r in rows if r.get('Type') != 'Aggregated') / len(rows)

    print(f\"  Total Requests:     {total_requests}\")
    print(f\"  Failed Requests:    {failed_requests} ({failed_requests/total_requests*100:.2f}%)\")
    print(f\"  Avg Response Time:  {avg_response:.2f}ms\")
"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# Performance Recommendations
# ============================================================================

echo -e "${YELLOW}Performance Recommendations:${NC}"
echo ""

# Check if results meet targets
python3 -c "
import json
import sys

if sys.argv[1] == 'k6':
    with open('$RESULTS_DIR/k6_summary_${TIMESTAMP}.json') as f:
        data = json.load(f)
        metrics = data.get('metrics', {})
        p95 = metrics.get('http_req_duration', {}).get('values', {}).get('p(95)', 0)

        if p95 < 100:
            print('  ✓ EXCELLENT: p95 latency < 100ms - System performing optimally')
        elif p95 < 200:
            print('  ✓ GOOD: p95 latency < 200ms - Performance is acceptable')
        elif p95 < 500:
            print('  ⚠ ACCEPTABLE: p95 latency < 500ms - Consider optimizations:')
            print('      - Add Redis caching for hot paths')
            print('      - Optimize database queries with indexes')
            print('      - Enable connection pooling')
        else:
            print('  ✗ NEEDS OPTIMIZATION: p95 latency > 500ms - Critical issues:')
            print('      - Review slow query logs')
            print('      - Add database indexes immediately')
            print('      - Implement aggressive caching')
            print('      - Check for N+1 query patterns')
" "k6"

echo ""

# ============================================================================
# Final Summary
# ============================================================================

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Test Execution Complete                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Results Location:${NC} $RESULTS_DIR"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review detailed reports in $RESULTS_DIR"
echo "  2. Apply database indexes: psql -f backend/migrations/performance_indexes.sql"
echo "  3. Enable Redis caching in production"
echo "  4. Re-run tests to measure improvements"
echo ""
echo -e "${BLUE}For more information:${NC}"
echo "  - Locust report: $LOCUST_REPORT"
echo "  - k6 results: $K6_REPORT"
echo "  - Baseline benchmark: $RESULTS_DIR/baseline_${TIMESTAMP}.json"
echo ""
