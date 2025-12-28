# Epic 1.7 NameCheap Migration - Test Suite Documentation

## Overview

Comprehensive test suite for Epic 1.7 NameCheap to Cloudflare migration functionality. This test suite covers all aspects of the migration workflow including domain discovery, DNS export, email service detection, nameserver updates, health checks, and rollback capability.

**Test Coverage Target**: 90%+
**Total Test Files**: 4
**Estimated Test Count**: 100+ tests

---

## Test Structure

```
tests/
├── conftest_migration.py                 # Test fixtures and mocks
├── unit/
│   └── test_namecheap_manager.py        # Unit tests for NameCheapManager class
├── integration/
│   └── test_migration_api.py            # API endpoint integration tests
├── e2e/
│   └── test_migration_e2e.py            # End-to-end workflow tests
├── run_migration_tests.sh                # Test runner script
└── MIGRATION_TESTS_README.md            # This file
```

---

## Test Files

### 1. `conftest_migration.py` - Test Fixtures

**Purpose**: Provides reusable test fixtures and mocks for all migration tests.

**Key Fixtures**:
- `mock_namecheap_client` - Mock NameCheap API client with standard responses
- `mock_namecheap_error_client` - Mock client that returns errors
- `mock_cloudflare_client` - Mock Cloudflare API client
- `sample_active_domain` - Sample active domain data
- `sample_expired_domain` - Sample expired domain data
- `sample_locked_domain` - Sample locked domain data
- `sample_basic_dns_records` - Basic DNS records (A, CNAME, MX)
- `sample_microsoft365_dns_records` - Microsoft 365 email DNS records
- `sample_namecheap_private_email_records` - NameCheap Private Email DNS records
- `sample_google_workspace_records` - Google Workspace email DNS records
- `sample_all_record_types` - All supported DNS record types
- `detected_microsoft365_service` - Detected Microsoft 365 email service
- `detected_namecheap_private_email` - Detected NameCheap Private Email service
- `detected_google_workspace` - Detected Google Workspace email service
- `sample_migration_job` - Sample migration job
- `sample_migration_domain_queue` - Sample migration queue entries
- `sample_dns_backup` - Sample DNS backup
- `sample_health_check_results` - Sample health check results
- `namecheap_api_error_responses` - Sample API error responses
- `mock_migration_db` - Mock migration database

**Lines of Code**: ~700

---

### 2. `unit/test_namecheap_manager.py` - Unit Tests

**Purpose**: Test NameCheapManager class methods in isolation.

**Test Classes**:

#### `TestNameCheapManagerInitialization` (3 tests)
- ✓ Initialize with valid credentials
- ✓ Initialize with sandbox mode
- ✓ Fail initialization with missing credentials

#### `TestDomainListing` (4 tests)
- ✓ Get domain list successfully
- ✓ Filter domains by status (active/expired)
- ✓ Filter domains by TLD (.com, .ai, etc.)
- ✓ Filter locked domains

#### `TestDNSExport` (4 tests)
- ✓ Export DNS records in JSON format
- ✓ Export DNS records in CSV format
- ✓ Export DNS records in BIND format
- ✓ Parse all DNS record types (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS)

#### `TestEmailServiceDetection` (4 tests)
- ✓ Detect Microsoft 365 email service
- ✓ Detect NameCheap Private Email service
- ✓ Detect Google Workspace email service
- ✓ Handle no recognized email service

#### `TestNameserverUpdates` (4 tests)
- ✓ Update nameservers successfully
- ✓ Validate nameserver format
- ✓ Fail update for locked domain
- ✓ Batch update nameservers for multiple domains

#### `TestRollbackCapability` (3 tests)
- ✓ Rollback nameservers to original values
- ✓ Verify original nameservers exist before rollback
- ✓ Track rollback in history

#### `TestErrorHandling` (4 tests)
- ✓ Handle API rate limit errors
- ✓ Handle XML parsing errors
- ✓ Handle domain not found errors
- ✓ Handle connection timeouts

#### `TestIPWhitelisting` (2 tests)
- ✓ Verify IP is whitelisted
- ✓ Handle IP not whitelisted error

#### `TestMigrationIntegration` (4 tests)
- ✓ Prepare domain for migration
- ✓ Validate migration readiness (active domain)
- ✓ Validate locked domain not ready
- ✓ Validate expired domain not ready

**Total Unit Tests**: ~32
**Target Coverage**: 90%+
**Lines of Code**: ~900

---

### 3. `integration/test_migration_api.py` - Integration Tests

**Purpose**: Test all 20 migration API endpoints with full request/response cycle.

**Test Classes**:

#### `TestNameCheapAccountManagement` (4 tests)
- ✓ `POST /api/v1/namecheap/accounts` - Create account
- ✓ `GET /api/v1/namecheap/accounts` - List accounts
- ✓ `POST /api/v1/namecheap/accounts/{id}/test-connection` - Test connection
- ✓ `DELETE /api/v1/namecheap/accounts/{id}` - Delete account

#### `TestDomainDiscovery` (2 tests)
- ✓ `POST /api/v1/namecheap/domains/sync` - Sync domains from NameCheap
- ✓ `GET /api/v1/namecheap/domains` - Get domains with filters

#### `TestDNSExport` (4 tests)
- ✓ `GET /api/v1/namecheap/domains/{domain}/dns` - Get DNS records
- ✓ `POST .../dns/export?format=json` - Export as JSON
- ✓ `POST .../dns/export?format=csv` - Export as CSV
- ✓ `POST .../dns/export?format=bind` - Export as BIND

#### `TestMigrationJobManagement` (6 tests)
- ✓ `POST /api/v1/migration/jobs` - Create migration job
- ✓ `GET /api/v1/migration/jobs` - List migrations
- ✓ `GET /api/v1/migration/jobs/{job_id}` - Get job details
- ✓ `DELETE /api/v1/migration/jobs/{job_id}` - Cancel migration
- ✓ `POST /api/v1/migration/jobs/{job_id}/pause` - Pause migration
- ✓ `POST /api/v1/migration/jobs/{job_id}/resume` - Resume migration

#### `TestMigrationQueue` (3 tests)
- ✓ `GET /api/v1/migration/jobs/{job_id}/queue` - Get migration queue
- ✓ `POST .../queue/{domain}/retry` - Retry failed domain
- ✓ `PUT .../queue/{domain}/priority` - Update domain priority

#### `TestProgressTracking` (2 tests)
- ✓ `GET /api/v1/migration/jobs/{job_id}/progress` - Get migration progress
- ✓ `GET .../domains/{domain}/status` - Get domain status

#### `TestHealthChecks` (3 tests)
- ✓ `POST /api/v1/migration/health-check` - Run full health check
- ✓ `GET /api/v1/migration/jobs/{job_id}/health-checks` - Get job health checks
- ✓ `POST .../domains/{domain}/health-check` - Run domain health check

#### `TestRollback` (3 tests)
- ✓ `POST /api/v1/migration/jobs/{job_id}/rollback` - Rollback full migration
- ✓ `POST .../domains/{domain}/rollback` - Rollback single domain
- ✓ `GET /api/v1/migration/rollback-history` - Get rollback history

#### `TestRateLimiting` (2 tests)
- ✓ Rate limiting enforced at 10 req/min
- ✓ Rate limiting per-user

#### `TestAuthentication` (3 tests)
- ✓ Unauthenticated requests rejected
- ✓ Invalid token rejected
- ✓ Admin-only endpoints require admin role

#### `TestErrorHandling` (3 tests)
- ✓ Invalid domain format
- ✓ Nonexistent job ID
- ✓ Missing required fields

**Total Integration Tests**: ~35
**Lines of Code**: ~850

---

### 4. `e2e/test_migration_e2e.py` - End-to-End Tests

**Purpose**: Test complete migration workflows from start to finish.

**Test Classes**:

#### `TestSingleDomainMigration` (1 test)
- ✓ Complete single domain migration workflow:
  1. Discover domain from NameCheap
  2. Export DNS records
  3. Add to Cloudflare
  4. Update nameservers
  5. Monitor propagation
  6. Verify health checks

#### `TestBatchMigration` (1 test)
- ✓ Migrate 3 domains simultaneously:
  - Handle Cloudflare's 3-zone pending limit
  - Queue excess domains
  - Process queue as slots become available

#### `TestEmailServicePreservation` (1 test)
- ✓ Migrate domain with Microsoft 365 email:
  - Detect email service
  - Preserve all email-related records
  - Verify email functionality post-migration

#### `TestMigrationPauseResume` (1 test)
- ✓ Pause and resume migration:
  - Start migration with multiple domains
  - Pause after first domain
  - Verify migration paused
  - Resume migration
  - Verify all domains complete

#### `TestMigrationRollback` (2 tests)
- ✓ Rollback single domain:
  - Migrate domain
  - Rollback nameservers
  - Verify original nameservers restored
- ✓ Rollback entire migration:
  - Migrate multiple domains
  - Rollback all domains
  - Verify all nameservers restored

#### `TestHealthVerification` (1 test)
- ✓ Complete health check workflow:
  - Migrate domain
  - Run all health checks (DNS, SSL, email, website)
  - Verify propagation status

#### `TestDryRunMode` (1 test)
- ✓ Dry run migration:
  - Preview migration without executing
  - Verify no actual changes made
  - Show what would happen

#### `TestErrorRecovery` (1 test)
- ✓ Retry failed domain:
  - Simulate failure (domain locked)
  - Verify automatic retry
  - Manually retry if needed

**Total E2E Tests**: ~9
**Lines of Code**: ~650

---

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
cd /home/muut/Production/UC-Cloud/services/ops-center/tests
./run_migration_tests.sh
```

### Run Specific Test Suites

```bash
# Unit tests only
./run_migration_tests.sh --unit-only

# Integration tests only
./run_migration_tests.sh --integration-only

# E2E tests only
./run_migration_tests.sh --e2e-only

# Verbose output
./run_migration_tests.sh --verbose

# Skip coverage report
./run_migration_tests.sh --no-coverage
```

### Run Individual Test Files

```bash
# Run unit tests
pytest unit/test_namecheap_manager.py -v

# Run integration tests
pytest integration/test_migration_api.py -v

# Run E2E tests
pytest e2e/test_migration_e2e.py -v

# Run specific test class
pytest unit/test_namecheap_manager.py::TestDomainListing -v

# Run specific test
pytest unit/test_namecheap_manager.py::TestDomainListing::test_get_domain_list_success -v
```

---

## Test Reports

### Report Locations

All test reports are saved to `/tests/reports/`:

- **Test Report**: `migration_test_report_YYYYMMDD_HHMMSS.txt`
- **Coverage Report**: `coverage/migration_coverage_YYYYMMDD_HHMMSS.html`
- **JSON Results**: `migration_test_results_YYYYMMDD_HHMMSS.json`

### Sample Report Output

```
==========================================
Epic 1.7 Migration Test Report
==========================================
Timestamp: 2025-10-22 22:30:00
Test Environment: local

========================================
Running Unit Tests
========================================
✓ test_init_with_valid_credentials PASSED
✓ test_init_with_sandbox_mode PASSED
✓ test_get_domain_list_success PASSED
✓ test_filter_domains_by_status PASSED
...

========================================
Running Integration Tests
========================================
✓ test_create_namecheap_account PASSED
✓ test_get_namecheap_accounts PASSED
...

========================================
Running E2E Tests
========================================
✓ test_complete_single_domain_migration PASSED
✓ test_migrate_multiple_domains PASSED
...

========================================
Test Summary
========================================
Total Tests:   76
Passed:        76
Failed:        0
Skipped:       0

Success Rate:  100.0%

Coverage Summary:
----------------
backend/namecheap_manager.py      427    38    91%
backend/api/migration.py          312    25    92%
backend/migration_orchestrator.py 284    22    92%
TOTAL                            1023    85    92%

All tests passed! ✨
```

---

## Coverage Requirements

### Target Coverage: 90%+

**Coverage by Module**:
- `backend/namecheap_manager.py` - NameCheap API integration: **≥90%**
- `backend/api/migration.py` - Migration API endpoints: **≥90%**
- `backend/migration_orchestrator.py` - Migration workflow: **≥90%**

### How to Check Coverage

```bash
# Generate HTML coverage report
coverage html -d tests/reports/coverage

# View coverage report
open tests/reports/coverage/index.html

# Terminal coverage report
coverage report

# Coverage for specific module
coverage report --include="backend/namecheap_manager.py"
```

---

## Test Data

### Mock API Responses

All tests use mocked API responses to avoid real API calls:

**NameCheap API**:
- Domain list with 4 domains (active, expired, locked)
- DNS records for various email services
- Nameserver update responses
- Error responses (locked, expired, rate limit)

**Cloudflare API**:
- Zone creation responses
- DNS record creation responses
- Zone status responses

### Sample Domains

**Test domains used throughout tests**:
1. `your-domain.com` - Active domain with Microsoft 365 email
2. `superiorbsolutions.com` - Active domain with Microsoft 365 email
3. `magicunicorn.tech` - Active domain with NameCheap Private Email
4. `expired-domain.com` - Expired domain (migration should fail)
5. `locked-domain.com` - Locked domain (migration should fail)

---

## Environment Variables

### Required for Testing

Create `.env.test` file:

```bash
# NameCheap API (Sandbox)
NAMECHEAP_API_USERNAME=test_user
NAMECHEAP_API_KEY=test_api_key_12345
NAMECHEAP_CLIENT_IP=127.0.0.1
NAMECHEAP_SANDBOX_MODE=true

# Cloudflare API (Mock)
CLOUDFLARE_API_TOKEN=mock_cloudflare_token
CLOUDFLARE_ACCOUNT_ID=mock_account_id

# Database (Test DB)
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_db

# Redis (Test instance)
REDIS_URL=redis://localhost:6379/15

# Test mode
TEST_MODE=true
MOCK_EXTERNAL_APIS=true
```

---

## Continuous Integration

### GitHub Actions Workflow

Add to `.github/workflows/migration-tests.yml`:

```yaml
name: Epic 1.7 Migration Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/namecheap_manager.py'
      - 'backend/api/migration.py'
      - 'backend/migration_orchestrator.py'
      - 'tests/unit/test_namecheap_manager.py'
      - 'tests/integration/test_migration_api.py'
      - 'tests/e2e/test_migration_e2e.py'
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt

      - name: Run migration tests
        run: |
          cd tests
          ./run_migration_tests.sh

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          files: tests/reports/coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=90
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Error**: `ModuleNotFoundError: No module named 'backend'`

**Fix**:
```bash
export PYTHONPATH="${PYTHONPATH}:/home/muut/Production/UC-Cloud/services/ops-center"
```

#### 2. Async Test Warnings

**Error**: `RuntimeWarning: coroutine was never awaited`

**Fix**: Ensure all async tests use `@pytest.mark.asyncio` decorator

#### 3. Mock Not Called

**Error**: `AssertionError: Expected mock to be called`

**Fix**: Verify mock is properly patched and async mocks use `AsyncMock`

#### 4. Database Connection Errors

**Error**: `psycopg2.OperationalError: could not connect to server`

**Fix**: Ensure test database is running or set `MOCK_EXTERNAL_APIS=true`

---

## Development Workflow

### Adding New Tests

1. **Identify test type**: Unit, integration, or E2E?
2. **Add test to appropriate file**:
   - Unit → `unit/test_namecheap_manager.py`
   - Integration → `integration/test_migration_api.py`
   - E2E → `e2e/test_migration_e2e.py`
3. **Use existing fixtures** from `conftest_migration.py`
4. **Run tests**: `pytest <test_file> -v`
5. **Check coverage**: `coverage report`
6. **Update documentation** if needed

### Test Naming Convention

- **Unit tests**: `test_<method_name>_<scenario>`
- **Integration tests**: `test_<endpoint>_<action>`
- **E2E tests**: `test_<workflow>_<scenario>`

**Examples**:
- `test_get_domain_list_success`
- `test_create_namecheap_account`
- `test_complete_single_domain_migration`

---

## Test Maintenance

### Regular Tasks

- [ ] Update mocks when API changes
- [ ] Add tests for new features
- [ ] Review coverage reports weekly
- [ ] Fix failing tests immediately
- [ ] Update fixtures as needed
- [ ] Keep documentation current

### Performance Benchmarks

**Target test execution times**:
- Unit tests: <5 seconds
- Integration tests: <30 seconds
- E2E tests: <60 seconds
- Full suite: <90 seconds

---

## Contact & Support

**Epic Owner**: Epic 1.7 Team
**Test Suite Author**: QA Specialist
**Last Updated**: October 22, 2025

For questions or issues with the test suite, please contact the development team or open an issue in the project repository.

---

**Test Suite Status**: ✅ Complete
**Coverage**: 90%+ target
**Total Tests**: 76+
**Last Run**: Pending first execution
