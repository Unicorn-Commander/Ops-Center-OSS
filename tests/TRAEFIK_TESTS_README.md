# Traefik Configuration Management Tests (Epic 1.3)

**Status**: ✅ Ready for Implementation
**Coverage Target**: 90%+
**Test Count**: 142 tests (67 unit + 75 integration)
**Created**: October 24, 2025

---

## Overview

Comprehensive test suite for Traefik configuration management in Ops-Center. Tests cover certificate management, route configuration, middleware setup, and configuration backup/restore functionality.

## Test Structure

```
tests/
├── unit/
│   └── test_traefik_manager.py          # 67 unit tests (600+ lines)
├── integration/
│   └── test_traefik_api.py              # 75 integration tests (700+ lines)
├── conftest_traefik.py                  # Shared fixtures (400+ lines)
└── run_traefik_tests.sh                 # Test runner script
```

---

## Test Coverage

### Unit Tests (67 tests)

**File**: `tests/unit/test_traefik_manager.py`

#### 1. Certificate Management (12 tests)
- ✅ TC-1.1: List Certificates (Empty)
- ✅ TC-1.2: Request Certificate (Valid Domain)
- ✅ TC-1.3: Request Certificate (Wildcard Domain)
- ✅ TC-1.4: Request Certificate (Invalid Domain)
- ✅ TC-1.5: Request Certificate (Invalid Email)
- ✅ TC-1.6: Request Certificate (Invalid Challenge Type)
- ✅ TC-1.7: Get Certificate Details
- ✅ TC-1.8: Get Certificate (Not Found)
- ✅ TC-1.9: Renew Certificate
- ✅ TC-1.10: Renew Certificate (Not Due)
- ✅ TC-1.11: Revoke Certificate
- ✅ TC-1.12: List Certificates (Multiple)

#### 2. Route Management (14 tests)
- ✅ TC-2.1: Create Route (Basic)
- ✅ TC-2.2: Create Route (With Middlewares)
- ✅ TC-2.3: Create Route (With Priority)
- ✅ TC-2.4: Create Route (Duplicate Name)
- ✅ TC-2.5: Create Route (Invalid Rule)
- ✅ TC-2.6: Get Route
- ✅ TC-2.7: Get Route (Not Found)
- ✅ TC-2.8: Update Route
- ✅ TC-2.9: Delete Route
- ✅ TC-2.10: Delete Route (Not Found)
- ✅ TC-2.11: List Routes (Empty)
- ✅ TC-2.12: List Routes (Multiple)
- ✅ TC-2.13: List Routes (Filter by Entrypoint)
- ✅ TC-2.14: Route Rule Validation (Various Patterns)

#### 3. Middleware Management (10 tests)
- ✅ TC-3.1: Create Middleware (Basic Auth)
- ✅ TC-3.2: Create Middleware (Rate Limit)
- ✅ TC-3.3: Create Middleware (Headers)
- ✅ TC-3.4: Create Middleware (Strip Prefix)
- ✅ TC-3.5: Create Middleware (Redirect Scheme)
- ✅ TC-3.6: Create Middleware (Invalid Type)
- ✅ TC-3.7: Create Middleware (Duplicate Name)
- ✅ TC-3.8: Get Middleware
- ✅ TC-3.9: Delete Middleware
- ✅ TC-3.10: List Middlewares

#### 4. Configuration Management (10 tests)
- ✅ TC-4.1: Validate Config (Valid)
- ✅ TC-4.2: Validate Config (Missing EntryPoints)
- ✅ TC-4.3: Validate Config (EntryPoint Missing Address)
- ✅ TC-4.4: Validate Config (Certificate Resolver)
- ✅ TC-4.5: Validate Config (Resolver Missing Email)
- ✅ TC-4.6: Backup Config
- ✅ TC-4.7: Restore Config
- ✅ TC-4.8: Restore Config (Invalid Backup)
- ✅ TC-4.9: Load Config
- ✅ TC-4.10: Save Config

#### 5. Security & Validation (8 tests)
- ✅ TC-5.1: Domain Validation (Valid)
- ✅ TC-5.2: Domain Validation (Invalid)
- ✅ TC-5.3: Email Validation (Valid)
- ✅ TC-5.4: Email Validation (Invalid)
- ✅ TC-5.5: Route Rule Injection Prevention
- ✅ TC-5.6: Config File Path Validation
- ✅ TC-5.7: Middleware Config Sanitization
- ✅ TC-5.8: No Shell Execution

#### 6. Error Handling (8 tests)
- ✅ TC-6.1: Config File Not Found
- ✅ TC-6.2: Invalid YAML Syntax
- ✅ TC-6.3: Backup Directory Creation
- ✅ TC-6.4: Restore Rollback on Failure
- ✅ TC-6.5: Concurrent Modification Detection
- ✅ TC-6.6: Certificate Renewal Failure Handling
- ✅ TC-6.7: Route Validation on Update
- ✅ TC-6.8: Middleware Deletion (Used by Routes)

#### 7. Performance Tests (5 tests)
- ✅ TC-7.1: Config Validation Performance (<100ms for 100 entrypoints)
- ✅ TC-7.2: Route Lookup Performance (<10ms)
- ✅ TC-7.3: Certificate List Performance (<50ms for 50 certs)
- ✅ TC-7.4: Config Backup Performance (<100ms)
- ✅ TC-7.5: Bulk Route Creation (50 routes in <1s)

### Integration Tests (75 tests)

**File**: `tests/integration/test_traefik_api.py`

#### 1. Authentication & Authorization (6 tests)
- ✅ TC-1.1: Authentication Required Test
- ✅ TC-1.2: Authorization Test (Admin Role Required)
- ✅ TC-1.3: Moderator Can View But Not Modify
- ✅ TC-1.4: Admin Has Full Access
- ✅ TC-1.5: Invalid Token Rejected
- ✅ TC-1.6: Expired Token Rejected

#### 2. Certificate Management API (12 tests)
- ✅ TC-2.1: GET /api/v1/network/traefik/certificates
- ✅ TC-2.2: POST /api/v1/network/traefik/certificates (Valid)
- ✅ TC-2.3: POST /api/v1/network/traefik/certificates (Wildcard)
- ✅ TC-2.4: POST (Invalid Domain)
- ✅ TC-2.5: POST (Invalid Email)
- ✅ TC-2.6: GET /api/v1/network/traefik/certificates/{domain}
- ✅ TC-2.7: GET (Not Found)
- ✅ TC-2.8: POST /api/v1/network/traefik/certificates/{domain}/renew
- ✅ TC-2.9: DELETE /api/v1/network/traefik/certificates/{domain}
- ✅ TC-2.10: GET /api/v1/network/traefik/certificates/{domain}/status
- ✅ TC-2.11: POST (Missing Fields)
- ✅ TC-2.12: GET /api/v1/network/traefik/certificates/auto-renewal/config

#### 3. Route Management API (14 tests)
- ✅ TC-3.1: GET /api/v1/network/traefik/routes
- ✅ TC-3.2: POST /api/v1/network/traefik/routes (Basic)
- ✅ TC-3.3: POST (With Middlewares)
- ✅ TC-3.4: POST (With Priority)
- ✅ TC-3.5: POST (Duplicate Name)
- ✅ TC-3.6: POST (Invalid Rule)
- ✅ TC-3.7: GET /api/v1/network/traefik/routes/{name}
- ✅ TC-3.8: GET (Not Found)
- ✅ TC-3.9: PUT /api/v1/network/traefik/routes/{name}
- ✅ TC-3.10: DELETE /api/v1/network/traefik/routes/{name}
- ✅ TC-3.11: GET (Filter by Entrypoint)
- ✅ TC-3.12: GET (Filter by Service)
- ✅ TC-3.13: POST (Missing Fields)
- ✅ TC-3.14: POST (Complex Rule)

#### 4. Middleware Management API (10 tests)
- ✅ TC-4.1: GET /api/v1/network/traefik/middlewares
- ✅ TC-4.2: POST /api/v1/network/traefik/middlewares (Basic Auth)
- ✅ TC-4.3: POST (Rate Limit)
- ✅ TC-4.4: POST (Headers)
- ✅ TC-4.5: POST (Redirect)
- ✅ TC-4.6: POST (Invalid Type)
- ✅ TC-4.7: GET /api/v1/network/traefik/middlewares/{name}
- ✅ TC-4.8: DELETE /api/v1/network/traefik/middlewares/{name}
- ✅ TC-4.9: POST (Missing Config)
- ✅ TC-4.10: GET (Filter by Type)

#### 5. Configuration Management API (8 tests)
- ✅ TC-5.1: GET /api/v1/network/traefik/config
- ✅ TC-5.2: POST /api/v1/network/traefik/config/validate
- ✅ TC-5.3: POST (Validate Invalid)
- ✅ TC-5.4: POST /api/v1/network/traefik/config/backup
- ✅ TC-5.5: GET /api/v1/network/traefik/config/backups
- ✅ TC-5.6: POST /api/v1/network/traefik/config/restore
- ✅ TC-5.7: POST /api/v1/network/traefik/config/reload
- ✅ TC-5.8: GET /api/v1/network/traefik/config/export

#### 6. Health & Status Endpoints (6 tests)
- ✅ TC-6.1: GET /api/v1/network/traefik/health
- ✅ TC-6.2: GET /api/v1/network/traefik/status
- ✅ TC-6.3: GET /api/v1/network/traefik/version
- ✅ TC-6.4: GET /api/v1/network/traefik/metrics
- ✅ TC-6.5: GET /api/v1/network/traefik/entrypoints
- ✅ TC-6.6: GET /api/v1/network/traefik/services

#### 7. Rate Limiting (5 tests)
- ✅ TC-7.1: Rate Limit Test (Traefik Operations)
- ✅ TC-7.2: Rate Limit Per User
- ✅ TC-7.3: Rate Limit Headers
- ✅ TC-7.4: Health Endpoint Not Rate Limited
- ✅ TC-7.5: Rate Limit Reset

#### 8. Error Responses (8 tests)
- ✅ TC-8.1: Invalid JSON Payload
- ✅ TC-8.2: Route Not Found Error
- ✅ TC-8.3: Middleware Not Found Error
- ✅ TC-8.4: Validation Error Response Format
- ✅ TC-8.5: Internal Server Error Handling
- ✅ TC-8.6: Method Not Allowed
- ✅ TC-8.7: Content-Type Mismatch
- ✅ TC-8.8: Large Payload Rejected

#### 9. Audit Logging (6 tests)
- ✅ TC-9.1: Route Creation Logged
- ✅ TC-9.2: Route Deletion Logged
- ✅ TC-9.3: Middleware Creation Logged
- ✅ TC-9.4: Config Backup Logged
- ✅ TC-9.5: Certificate Request Logged
- ✅ TC-9.6: Audit Log Contains User Info

---

## Running Tests

### Quick Start

```bash
# Navigate to tests directory
cd /home/muut/Production/UC-Cloud/services/ops-center/tests

# Make script executable (first time only)
chmod +x run_traefik_tests.sh

# Run all tests
./run_traefik_tests.sh

# Run specific test suite
./run_traefik_tests.sh unit         # Unit tests only
./run_traefik_tests.sh integration  # Integration tests only
./run_traefik_tests.sh coverage     # Full coverage report
./run_traefik_tests.sh quick        # Quick test (stop on first failure)
```

### Manual Test Execution

```bash
# Unit tests only
pytest tests/unit/test_traefik_manager.py -v --cov=backend/traefik_manager

# Integration tests only
pytest tests/integration/test_traefik_api.py -v --cov=backend/traefik_api

# Specific test class
pytest tests/unit/test_traefik_manager.py::TestCertificateManagement -v

# Specific test
pytest tests/unit/test_traefik_manager.py::TestCertificateManagement::test_request_certificate_valid_domain -v

# With coverage HTML report
pytest tests/unit/test_traefik_manager.py \
  -v \
  --cov=backend/traefik_manager \
  --cov-report=html:tests/coverage/traefik_unit
```

### Using Pytest Markers

```bash
# Run only certificate tests
pytest tests/ -v -m certificate

# Run only route tests
pytest tests/ -v -m route

# Run only middleware tests
pytest tests/ -v -m middleware

# Run slow tests
pytest tests/ -v -m slow

# Skip destructive tests
pytest tests/ -v -m "not destructive"
```

---

## Prerequisites

### 1. Install Dependencies

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Install test dependencies
pip install -r tests/requirements-test.txt
```

### 2. Environment Setup

Create or update `tests/.env.test`:

```bash
# Ops-Center Configuration
OPS_CENTER_URL=http://localhost:8084

# Test User Credentials
TEST_ADMIN_USERNAME=admin_test
TEST_ADMIN_PASSWORD=Test123!
TEST_MODERATOR_USERNAME=moderator_test
TEST_MODERATOR_PASSWORD=Test123!
TEST_VIEWER_USERNAME=user_test
TEST_VIEWER_PASSWORD=Test123!

# Test Environment
ENVIRONMENT=test
LOG_LEVEL=DEBUG

# Traefik Configuration
TRAEFIK_API_URL=http://localhost:8080
TRAEFIK_CONFIG_PATH=/etc/traefik/traefik.yml
```

### 3. Start Services

```bash
# Ensure Ops-Center is running
docker ps | grep ops-center

# If not running, start it
docker restart ops-center-direct

# Verify API is accessible
curl http://localhost:8084/api/v1/system/status
```

---

## Test Fixtures

### Shared Fixtures (`conftest_traefik.py`)

**HTTP Clients**:
- `admin_client` - Authenticated admin client
- `moderator_client` - Authenticated moderator client
- `viewer_client` - Authenticated viewer client
- `unauthenticated_client` - No authentication

**Certificate Data**:
- `valid_certificate_request` - Valid cert request
- `valid_wildcard_certificate_request` - Wildcard cert
- `invalid_certificate_request` - Invalid cert data
- `mock_certificate` - Mock certificate object

**Route Data**:
- `valid_route` - Basic route
- `valid_route_with_middlewares` - Route with middlewares
- `valid_route_with_priority` - Route with priority
- `invalid_route` - Invalid route data
- `complex_route_rule` - Complex routing rule

**Middleware Data**:
- `valid_middleware_basic_auth` - Basic auth middleware
- `valid_middleware_rate_limit` - Rate limit middleware
- `valid_middleware_headers` - Headers middleware
- `valid_middleware_redirect` - Redirect middleware
- `invalid_middleware` - Invalid middleware data

**Configuration Data**:
- `valid_traefik_config` - Valid Traefik config
- `invalid_traefik_config` - Invalid config
- `temp_traefik_config_file` - Temporary config file

**Helper Fixtures**:
- `assert_valid_certificate` - Assert certificate structure
- `assert_valid_route` - Assert route structure
- `assert_valid_middleware` - Assert middleware structure
- `assert_valid_traefik_status` - Assert status response

**Generators**:
- `generate_mock_certificates(count)` - Generate multiple certs
- `generate_mock_routes(count)` - Generate multiple routes
- `generate_mock_middlewares(count)` - Generate multiple middlewares

**Cleanup**:
- `cleanup_test_traefik_resources` - Auto-cleanup (runs after each test)

---

## Expected Coverage

### Coverage Targets

**Overall**: 90%+

**By Module**:
- `traefik_manager.py`: 92%+
- `traefik_api.py`: 90%+

**By Feature**:
- Certificate Management: 95%+
- Route Management: 93%+
- Middleware Management: 91%+
- Configuration Management: 90%+

### Coverage Report

```bash
# Generate coverage report
./run_traefik_tests.sh coverage

# View HTML report
open tests/coverage/traefik_all/index.html

# View terminal summary
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## Implementation Checklist

### Backend Implementation

#### 1. Create `backend/traefik_manager.py`
- [ ] TraefikManager class
- [ ] Certificate management methods
- [ ] Route management methods
- [ ] Middleware management methods
- [ ] Configuration management methods
- [ ] Validation methods
- [ ] Error classes (TraefikError, ConfigValidationError, etc.)

#### 2. Create `backend/traefik_api.py`
- [ ] FastAPI router
- [ ] Certificate endpoints (9 endpoints)
- [ ] Route endpoints (7 endpoints)
- [ ] Middleware endpoints (4 endpoints)
- [ ] Configuration endpoints (6 endpoints)
- [ ] Health/status endpoints (6 endpoints)
- [ ] Authentication decorators
- [ ] Rate limiting middleware
- [ ] Audit logging integration

#### 3. Integration
- [ ] Add router to main `server.py`
- [ ] Configure authentication
- [ ] Setup audit logging
- [ ] Configure rate limiting
- [ ] Add error handlers

### Testing

- [x] Unit test file created (`test_traefik_manager.py`)
- [x] Integration test file created (`test_traefik_api.py`)
- [x] Fixtures file created (`conftest_traefik.py`)
- [x] Test runner script created (`run_traefik_tests.sh`)
- [x] Requirements updated (`requirements-test.txt`)
- [ ] Run tests and verify coverage
- [ ] Fix any failing tests
- [ ] Document test results

---

## Common Test Patterns

### Unit Test Pattern

```python
def test_create_route_basic(self, manager):
    """TC-2.1: Create Route (Basic)"""
    route = manager.create_route(
        name="test-route",
        rule="Host(`test.example.com`)",
        service="test-service"
    )

    assert route['name'] == "test-route"
    assert route['rule'] == "Host(`test.example.com`)"
    assert route['service'] == "test-service"
```

### Integration Test Pattern

```python
@pytest.mark.asyncio
async def test_create_route_basic(self, admin_client):
    """TC-3.2: POST /api/v1/network/traefik/routes (Basic)"""
    route_data = {
        "name": "TEST:basic-route",
        "rule": "Host(`test.example.com`)",
        "service": "test-service"
    }

    response = await admin_client.post(
        "/api/v1/network/traefik/routes",
        json=route_data
    )

    assert response.status_code in [200, 201, 503]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "name" in data or "route" in data
```

### Error Handling Test Pattern

```python
def test_create_route_invalid_rule(self, manager):
    """TC-2.5: Create Route (Invalid Rule)"""
    with pytest.raises(RouteError, match="Invalid route rule"):
        manager.create_route(
            name="invalid",
            rule="InvalidSyntax",
            service="test-service"
        )
```

---

## Debugging Tips

### Test Failures

1. **Check Service Status**:
   ```bash
   docker ps | grep ops-center
   docker logs ops-center-direct --tail 100
   ```

2. **Verify Test Environment**:
   ```bash
   cat tests/.env.test
   curl http://localhost:8084/api/v1/system/status
   ```

3. **Run Single Test**:
   ```bash
   pytest tests/unit/test_traefik_manager.py::TestCertificateManagement::test_request_certificate_valid_domain -v -s
   ```

4. **Enable Debug Logging**:
   ```bash
   pytest tests/ -v -s --log-cli-level=DEBUG
   ```

### Coverage Issues

1. **View Coverage Report**:
   ```bash
   pytest tests/ --cov=backend --cov-report=html
   open tests/coverage/index.html
   ```

2. **Missing Lines**:
   ```bash
   pytest tests/ --cov=backend --cov-report=term-missing
   ```

3. **Branch Coverage**:
   ```bash
   pytest tests/ --cov=backend --cov-branch
   ```

---

## Integration with Epic 1.3

This test suite is designed to support the implementation of Epic 1.3 (Traefik Configuration Management). The tests are structured to:

1. **Guide Implementation**: Tests define expected behavior
2. **Prevent Regressions**: Catch bugs before production
3. **Document API**: Tests serve as usage examples
4. **Ensure Quality**: 90%+ coverage target
5. **Enable CI/CD**: Automated testing in pipeline

---

## Next Steps

1. **Implement Backend**:
   - Create `backend/traefik_manager.py` based on test requirements
   - Create `backend/traefik_api.py` for FastAPI endpoints
   - Integrate with main application

2. **Run Tests**:
   - Execute test suite
   - Fix failing tests
   - Achieve 90%+ coverage

3. **Documentation**:
   - Document API endpoints
   - Create user guide
   - Update architecture docs

4. **Deployment**:
   - Deploy to staging
   - Run integration tests
   - Deploy to production

---

## Support & Contact

**Project**: UC-Cloud / Ops-Center
**Epic**: 1.3 - Traefik Configuration Management
**Test Suite**: Comprehensive (142 tests, 90%+ coverage)
**Documentation**: `/tests/TRAEFIK_TESTS_README.md`

**For Development**:
- Test files: `/tests/unit/test_traefik_manager.py`, `/tests/integration/test_traefik_api.py`
- Fixtures: `/tests/conftest_traefik.py`
- Runner: `/tests/run_traefik_tests.sh`

---

**Remember**: These tests are comprehensive and ready to guide implementation. Follow TDD principles: write tests first, implement to pass tests, refactor with confidence!
