# Traefik API Test Suite

Comprehensive test suite for Epic 1.3: Traefik Configuration Management

## Test Files

### 1. `test_traefik_manager.py` - Backend Unit Tests
**Purpose**: Tests all TraefikManager methods with mocked file I/O and Docker commands

**Coverage**:
- Certificate management (list, get, request, revoke)
- Route management (CRUD operations)
- Middleware management (CRUD operations)
- Configuration management (backup, restore, validate)
- Rate limiting
- Input validation
- Error handling
- Edge cases

**Test Count**: 50+ unit tests

### 2. `test_traefik_api.py` - API Integration Tests
**Purpose**: Tests all FastAPI endpoints using TestClient

**Coverage**:
- Health and status endpoints
- Route management API
- Certificate management API
- Configuration API
- Request validation
- Response format validation
- Error responses
- Edge cases

**Test Count**: 40+ integration tests

### 3. `test_traefik_e2e.sh` - End-to-End Test Script
**Purpose**: Tests complete workflows using curl

**Coverage**:
- Complete CRUD workflows
- Route → service → middleware relationships
- Configuration reload verification
- Data consistency across endpoints
- Error handling (404, 400, 500)
- HTTP response codes

**Test Count**: 15+ E2E scenarios

## Prerequisites

### Python Dependencies
```bash
pip install pytest pytest-asyncio httpx
```

### System Dependencies
```bash
# For E2E tests
sudo apt-get install curl jq
```

### Service Requirements
The Traefik API service should be running:
```bash
docker ps | grep ops-center
```

## Running Tests

### 1. Run Unit Tests (traefik_manager.py)

```bash
# Run all unit tests
cd /opt/ops-center/backend/tests
pytest test_traefik_manager.py -v

# Run specific test class
pytest test_traefik_manager.py::TestCertificateManagement -v

# Run specific test
pytest test_traefik_manager.py::TestCertificateManagement::test_list_certificates_success -v

# Run with coverage
pytest test_traefik_manager.py --cov=traefik_manager --cov-report=html

# Run with detailed output
pytest test_traefik_manager.py -vv --tb=long
```

**Expected Results**:
- All tests should pass if traefik_manager.py is implemented correctly
- Some tests may be marked as `xfail` if features are not yet implemented

### 2. Run API Integration Tests (traefik_api.py)

```bash
# Run all API tests
pytest test_traefik_api.py -v

# Run specific test class
pytest test_traefik_api.py::TestHealthAndStatus -v

# Run with FastAPI test client debugging
pytest test_traefik_api.py -vv --log-cli-level=DEBUG

# Run tests expecting 501 (not implemented)
pytest test_traefik_api.py -k "not_implemented" -v
```

**Expected Results**:
- Health and status tests should pass
- Certificate listing tests should pass
- Route creation tests will return 501 (not yet implemented)

### 3. Run End-to-End Tests (bash script)

```bash
# Run E2E tests (default: http://localhost:8084)
./test_traefik_e2e.sh

# Run with custom API URL
API_URL=https://unicorncommander.ai ./test_traefik_e2e.sh

# Run with verbose output
VERBOSE=1 ./test_traefik_e2e.sh

# Run and save output to file
./test_traefik_e2e.sh | tee e2e_test_results.txt
```

**Expected Results**:
```
========================================
Test Results Summary
========================================
Tests Run:    25
Tests Passed: 23
Tests Failed: 2

✅ All critical tests passed!
```

### 4. Run All Tests

```bash
# Run everything
cd /opt/ops-center/backend/tests

# Unit tests
pytest test_traefik_manager.py -v

# API tests
pytest test_traefik_api.py -v

# E2E tests
./test_traefik_e2e.sh

# Generate comprehensive coverage report
pytest test_traefik_manager.py test_traefik_api.py \
    --cov=traefik_manager \
    --cov=traefik_api \
    --cov-report=html \
    --cov-report=term-missing
```

## Test Organization

### Unit Tests (test_traefik_manager.py)

**Test Classes**:
1. `TestCertificateManagement` - SSL certificate operations
2. `TestRouteManagement` - Route CRUD operations
3. `TestMiddlewareManagement` - Middleware CRUD operations
4. `TestConfigurationManagement` - Config backup/restore
5. `TestRateLimiting` - Rate limiter functionality
6. `TestValidation` - Input validation (Pydantic models)
7. `TestAuditLogging` - Audit log functionality
8. `TestEdgeCases` - Edge cases and error handling
9. `TestIntegration` - Integration workflows

**Fixtures**:
- `temp_traefik_dir` - Temporary Traefik directory with config files
- `traefik_manager` - TraefikManager instance with temp directory
- `mock_audit_logger` - Mock audit logger
- `mock_rate_limiter` - Mock rate limiter
- `sample_route_config` - Sample route configuration

### API Tests (test_traefik_api.py)

**Test Classes**:
1. `TestHealthAndStatus` - Health and status endpoints
2. `TestRouteManagementAPI` - Route API endpoints
3. `TestCertificateManagementAPI` - Certificate API endpoints
4. `TestConfigurationManagementAPI` - Configuration API endpoints
5. `TestRequestValidation` - Request body validation
6. `TestResponseFormats` - Response format consistency
7. `TestEdgeCasesAPI` - Edge cases and error scenarios
8. `TestCORSAndHeaders` - CORS and HTTP headers
9. `TestAuthenticationAPI` - Authentication (placeholder)

**Fixtures**:
- `client` - FastAPI TestClient
- `mock_traefik_manager` - Mock TraefikManager
- `sample_routes` - Sample route data
- `sample_certificates` - Sample certificate data

### E2E Tests (test_traefik_e2e.sh)

**Test Suites**:
1. Health & Status - Basic health checks
2. Route Management - Route CRUD workflows
3. Certificate Management - Certificate listing and retrieval
4. Configuration Management - Config summary
5. Error Handling - 404, 400, 422 responses
6. Complete Workflow - End-to-end data consistency

## Coverage Goals

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| traefik_manager.py | 80%+ | TBD (run coverage) |
| traefik_api.py | 80%+ | TBD (run coverage) |
| Overall | 80%+ | TBD (run coverage) |

## Test Data

### Sample Valid Inputs

**Route Creation**:
```json
{
    "name": "test-route",
    "rule": "Host(`example.com`)",
    "service": "test-service",
    "entrypoints": ["websecure"],
    "priority": 100,
    "middlewares": []
}
```

**Middleware Creation**:
```json
{
    "name": "api-ratelimit",
    "type": "rateLimit",
    "config": {
        "average": 100,
        "period": "1s"
    }
}
```

**Certificate Request**:
```json
{
    "domain": "example.com",
    "email": "admin@example.com",
    "sans": ["www.example.com"]
}
```

### Sample Invalid Inputs

**Invalid Route Name** (has spaces):
```json
{
    "name": "invalid route name",
    "rule": "Host(`example.com`)",
    "service": "test-service"
}
```

**Invalid Rule** (missing Host/Path):
```json
{
    "name": "test-route",
    "rule": "invalid rule",
    "service": "test-service"
}
```

**Invalid Middleware Config** (missing required fields):
```json
{
    "name": "bad-ratelimit",
    "type": "rateLimit",
    "config": {}
}
```

## Continuous Integration

### GitHub Actions Workflow (Example)

```yaml
name: Traefik API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov httpx

      - name: Run unit tests
        run: |
          cd backend/tests
          pytest test_traefik_manager.py -v --cov=traefik_manager

      - name: Run API tests
        run: |
          cd backend/tests
          pytest test_traefik_api.py -v --cov=traefik_api

      - name: Run E2E tests
        run: |
          cd backend/tests
          ./test_traefik_e2e.sh
```

## Troubleshooting

### Tests Fail with "Module not found"

**Problem**: Python can't find traefik_manager or traefik_api modules

**Solution**:
```bash
# Set PYTHONPATH
export PYTHONPATH=/opt/ops-center/backend:$PYTHONPATH

# Or run from backend directory
cd /opt/ops-center/backend
pytest tests/test_traefik_manager.py -v
```

### E2E Tests Fail with "Connection Refused"

**Problem**: Ops-Center service is not running

**Solution**:
```bash
# Check if service is running
docker ps | grep ops-center

# Start service
cd /opt/uc-cloud
docker restart ops-center-direct

# Wait for startup
sleep 5

# Test connection
curl http://localhost:8084/health
```

### Tests Pass but Coverage is Low

**Problem**: Tests don't cover all code paths

**Solution**:
```bash
# Generate coverage report
pytest test_traefik_manager.py --cov=traefik_manager --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check which lines are not covered
pytest test_traefik_manager.py --cov=traefik_manager --cov-report=term-missing
```

### Fixture Errors

**Problem**: Fixtures not found or not working

**Solution**:
```bash
# Run pytest with fixture debugging
pytest test_traefik_manager.py --fixtures

# Check fixture scope
pytest test_traefik_manager.py -v --setup-show
```

## Test Maintenance

### Adding New Tests

1. **Unit Tests**: Add to appropriate test class in `test_traefik_manager.py`
2. **API Tests**: Add to appropriate test class in `test_traefik_api.py`
3. **E2E Tests**: Add new function to `test_traefik_e2e.sh`

### Updating Tests After Code Changes

When `traefik_manager.py` or `traefik_api.py` changes:

1. Review affected test cases
2. Update mock expectations
3. Add new tests for new features
4. Remove/update tests for removed features
5. Run full test suite to ensure nothing broke

### Best Practices

1. **Test Naming**: Use descriptive names (`test_list_routes_success`, not `test1`)
2. **One Assertion Per Test**: Each test should verify one behavior
3. **Independent Tests**: Tests should not depend on each other
4. **Mock External Dependencies**: Don't rely on actual Docker, files, or network
5. **Use Fixtures**: Reuse common setup code via fixtures
6. **Test Error Cases**: Test both success and failure paths
7. **Document Assumptions**: Add comments for complex test logic

## Performance Benchmarks

### Expected Test Execution Times

- **Unit Tests**: < 5 seconds (50+ tests)
- **API Tests**: < 10 seconds (40+ tests)
- **E2E Tests**: < 30 seconds (15+ tests)
- **Full Suite**: < 45 seconds

If tests take significantly longer, consider:
- Reducing sleep/wait times
- Optimizing fixture setup
- Parallelizing tests with `pytest-xdist`

## Code Quality Checks

### Linting Tests

```bash
# Lint test files
pylint backend/tests/test_traefik_*.py

# Check code style
black backend/tests/test_traefik_*.py --check

# Type checking
mypy backend/tests/test_traefik_*.py
```

## Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Pydantic Validation**: https://docs.pydantic.dev/

## Questions & Support

If tests fail unexpectedly:
1. Check service is running: `docker ps`
2. Check logs: `docker logs ops-center-direct`
3. Verify configuration files exist
4. Check Python dependencies are installed
5. Review test output for specific error messages

---

**Last Updated**: October 24, 2025
**Author**: Testing & QA Specialist Agent
**Epic**: 1.3 - Traefik Configuration Management
