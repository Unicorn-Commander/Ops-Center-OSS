# Epic 3.1: LiteLLM Multi-Provider Routing - Quick Start Guide

**For Developers and QA Engineers**

---

## Quick Test Execution

### Run All Epic 3.1 Tests

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Set encryption key
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Run all tests
pytest tests/unit/test_byok_manager.py tests/unit/test_llm_routing_engine.py tests/integration/test_llm_endpoints.py tests/performance/test_routing_latency.py tests/security/test_byok_security.py -v

# Run with coverage
pytest tests/unit/test_byok_manager.py tests/unit/test_llm_routing_engine.py --cov=backend/modules --cov-report=term
```

---

## Test File Locations

```
tests/
├── fixtures/llm_test_data.py          # Mock data (462 lines)
├── unit/
│   ├── test_byok_manager.py           # 25 tests (528 lines)
│   └── test_llm_routing_engine.py     # 30 tests (673 lines)
├── integration/
│   └── test_llm_endpoints.py          # 53 tests (792 lines)
├── performance/
│   └── test_routing_latency.py        # 15 tests (521 lines)
├── security/
│   └── test_byok_security.py          # 30 tests (637 lines)
├── e2e/
│   └── test_epic_3_1_flows.md         # 8 scenarios (650 lines)
└── EPIC_3_1_TEST_PLAN.md              # Comprehensive plan (950 lines)
```

**Total**: 153 automated tests across 4,513 lines of test code

---

## Run Tests by Category

### Unit Tests Only (Fast - 2 minutes)

```bash
pytest tests/unit/test_byok_manager.py -v
pytest tests/unit/test_llm_routing_engine.py -v
```

### Integration Tests (Requires Services - 10 minutes)

```bash
# Start services first
docker-compose up -d unicorn-postgresql unicorn-redis uchub-keycloak ops-center-direct

# Run tests
pytest tests/integration/test_llm_endpoints.py -v
```

### Performance Tests (15 minutes)

```bash
pytest tests/performance/test_routing_latency.py -v -s
```

### Security Tests (5 minutes)

```bash
pytest tests/security/test_byok_security.py -v
```

---

## Key Test Commands

### Run Specific Test

```bash
# Single test function
pytest tests/unit/test_byok_manager.py::TestBYOKManager::test_encrypt_decrypt_key -v

# Test class
pytest tests/integration/test_llm_endpoints.py::TestBYOKEndpoints -v

# Tests matching pattern
pytest tests/ -k "byok" -v
```

### Generate Coverage Report

```bash
pytest tests/unit/ --cov=backend/modules --cov-report=html
firefox htmlcov/index.html  # Or: open htmlcov/index.html
```

### Run with Detailed Output

```bash
pytest tests/unit/ -v -s --tb=short
```

### Stop on First Failure

```bash
pytest tests/ -x
```

---

## Test Coverage Targets

| Component | Tests | Target Coverage |
|-----------|-------|-----------------|
| BYOK Manager | 25 | 85%+ |
| Routing Engine | 30 | 82%+ |
| API Endpoints | 53 | 100% of critical paths |
| Performance | 15 | All benchmarks met |
| Security | 30 | 100% pass |

---

## Performance Benchmarks

| Metric | Target | Measured |
|--------|--------|----------|
| Routing Latency (p95) | <100ms | [ ] |
| Throughput | >100 req/s | [ ] |
| Memory (1000 req) | <50MB | [ ] |
| Cache Speedup | >2x | [ ] |

---

## E2E Manual Testing

See: `/tests/e2e/test_epic_3_1_flows.md`

**8 Scenarios**:
1. BYOK Setup Flow (15 checks)
2. Power Level Usage (13 checks)
3. Fallback Mechanism (12 checks)
4. Usage Analytics (14 checks)
5. Multi-Provider BYOK (6 checks)
6. Rate Limiting (6 checks)
7. Streaming Responses (9 checks)
8. Error Recovery (5 checks)

**Total**: 80 manual validation points

---

## Troubleshooting

**Tests not found**:
```bash
# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/muut/Production/UC-Cloud/services/ops-center/backend"
```

**Import errors**:
```bash
# Install dependencies
pip install pytest pytest-cov pytest-asyncio httpx psutil cryptography
```

**Database errors**:
```bash
# Ensure PostgreSQL is running
docker ps | grep postgresql
```

**Encryption key errors**:
```bash
# Generate and export key
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo $ENCRYPTION_KEY  # Verify it's set
```

---

## Quick Test Status Check

```bash
# Run all tests and generate summary
pytest tests/unit/ tests/integration/ tests/performance/ tests/security/ --tb=short | tee test_results.txt

# Count passed/failed
grep -E "passed|failed" test_results.txt
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Epic 3.1 Tests
  run: |
    export ENCRYPTION_KEY=${{ secrets.TEST_ENCRYPTION_KEY }}
    pytest tests/unit/test_byok_manager.py tests/unit/test_llm_routing_engine.py --cov --cov-report=xml
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/unit/ -q || exit 1
```

---

## Documentation Links

- **Test Plan**: `/tests/EPIC_3_1_TEST_PLAN.md`
- **E2E Scenarios**: `/tests/e2e/test_epic_3_1_flows.md`
- **Delivery Summary**: `/EPIC_3.1_TEST_SUITE_COMPLETE.md`
- **Test Data**: `/tests/fixtures/llm_test_data.py`

---

## Contact for Questions

- Test Plan Issues: See `EPIC_3_1_TEST_PLAN.md`
- Test Execution Problems: Check test logs
- Coverage Questions: Review `htmlcov/index.html`

---

**Last Updated**: 2025-10-23
**Version**: 1.0
