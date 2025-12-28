# Load Testing Suite

Comprehensive load testing tools for the Ops-Center billing system.

## Quick Start

```bash
# Run all tests with automation script
./run_load_tests.sh --tool both --duration 300

# Run Locust only
./run_load_tests.sh --tool locust --duration 180 --vus 100

# Run k6 only
./run_load_tests.sh --tool k6 --duration 180
```

## Tools

### 1. Locust (`locustfile.py`)

Python-based load testing with realistic user simulation.

**Features**:
- Three user personas (End User, Org Admin, System Admin)
- Weighted task distribution
- Sequential workflows
- Web UI for monitoring

**Usage**:
```bash
# Web UI mode (recommended for interactive testing)
locust -f locustfile.py --host=http://localhost:8084
# Then open http://localhost:8089

# Headless mode (CI/CD)
locust -f locustfile.py \
  --host=http://localhost:8084 \
  --users=1000 \
  --spawn-rate=50 \
  --run-time=600s \
  --headless \
  --html=report.html
```

### 2. k6 (`k6_load_test.js`)

JavaScript-based load testing with advanced metrics.

**Features**:
- Staged load testing (gradual ramp-up)
- Custom metrics and thresholds
- JSON output for analysis
- Built-in performance checks

**Usage**:
```bash
# Default staged test
k6 run k6_load_test.js

# Custom configuration
k6 run --vus 1000 --duration 300s k6_load_test.js

# With JSON output
k6 run --out json=results.json k6_load_test.js
```

## Test Scenarios

### End User (70% of traffic)
- Check credit balance
- View usage summary
- Browse transaction history
- Purchase credits (occasional)

### Organization Admin (20% of traffic)
- View organization subscription
- Check credit pool
- Review member usage
- Allocate credits to users

### System Admin (10% of traffic)
- Platform analytics dashboard
- Revenue trends analysis
- All subscriptions list
- System-wide metrics

## Performance Targets

| Metric | Target | Tool |
|--------|--------|------|
| p95 Latency | <100ms | Both |
| p99 Latency | <500ms | Both |
| Throughput | 1000 req/s | k6 |
| Error Rate | <1% | Both |

## Results Analysis

Results are saved to `results/` directory:

- `locust_report_*.html` - Locust web report
- `locust_*_stats.csv` - Locust statistics
- `k6_results_*.json` - k6 detailed results
- `k6_summary_*.json` - k6 summary

## Troubleshooting

### Locust Issues

**Problem**: ImportError for locust
```bash
pip install locust
```

**Problem**: Connection refused
```bash
# Verify API is running
curl http://localhost:8084/api/v1/health
```

### k6 Issues

**Problem**: k6 command not found
```bash
# Install k6 (Ubuntu/Debian)
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests
on: [push]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install Locust
        run: pip install locust
      - name: Run Load Tests
        run: |
          cd tests/load
          ./run_load_tests.sh --tool locust --duration 60
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: tests/load/results/
```

## Best Practices

1. **Start Small**: Begin with 10-50 users, then scale up
2. **Monitor Resources**: Watch CPU, memory, database connections
3. **Test Incrementally**: After each optimization, re-test
4. **Use Realistic Data**: Match production traffic patterns
5. **Test in Staging**: Never load test production without approval

## Additional Resources

- [Locust Documentation](https://docs.locust.io)
- [k6 Documentation](https://k6.io/docs/)
- [Performance Report](../../docs/PERFORMANCE_REPORT.md)
