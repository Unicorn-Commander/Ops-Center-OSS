

# Epic 3.1: LiteLLM Multi-Provider Routing - Comprehensive Test Plan

**Version**: 1.0
**Date**: 2025-10-23
**Status**: Ready for Execution

---

## 1. Executive Summary

This document outlines the complete testing strategy for Epic 3.1: LiteLLM Multi-Provider Routing. The test plan covers unit tests, integration tests, end-to-end scenarios, performance benchmarks, and security audits to ensure the system meets all functional and non-functional requirements.

### 1.1 Test Objectives

- **Functional Correctness**: Verify all features work as specified
- **Performance**: Ensure routing decisions <100ms, throughput >100 req/sec
- **Security**: Validate encryption, access controls, and data protection
- **Reliability**: Confirm fallback mechanisms and error handling
- **Usability**: Validate user experience through E2E scenarios

### 1.2 Success Criteria

- **Unit Test Coverage**: ≥80%
- **Integration Tests**: All critical paths pass
- **E2E Scenarios**: 8/8 scenarios pass
- **Performance**: Meet all latency and throughput benchmarks
- **Security**: No critical vulnerabilities
- **Zero Data Leaks**: No API keys exposed in logs or responses

---

## 2. Test Coverage Matrix

| Component | Unit Tests | Integration Tests | E2E Tests | Performance Tests | Security Tests |
|-----------|------------|-------------------|-----------|-------------------|----------------|
| **BYOK Manager** | ✅ 25 tests | ✅ 8 tests | ✅ Scenario 1, 5 | ✅ Cache perf | ✅ 15 tests |
| **Routing Engine** | ✅ 30 tests | ✅ 12 tests | ✅ Scenario 2, 3 | ✅ Latency tests | ✅ 5 tests |
| **API Endpoints** | ✅ 15 tests | ✅ 25 tests | ✅ All scenarios | ✅ Throughput | ✅ 10 tests |
| **Usage Analytics** | ✅ 10 tests | ✅ 8 tests | ✅ Scenario 4 | ✅ Query perf | N/A |
| **Health Monitoring** | ✅ 8 tests | ✅ 5 tests | ✅ Scenario 3 | ✅ Overhead | N/A |
| **Streaming** | ✅ 5 tests | ✅ 5 tests | ✅ Scenario 7 | ✅ Memory | N/A |

**Total Test Count**: 166 automated tests + 8 E2E scenarios

---

## 3. Test Environments

### 3.1 Unit Test Environment

- **Framework**: pytest
- **Python Version**: 3.11+
- **Dependencies**: Mock database, mock Keycloak, mock providers
- **Isolation**: Each test runs in isolated environment
- **Execution Time**: ~2 minutes for full unit test suite

### 3.2 Integration Test Environment

- **Base URL**: `http://localhost:8084`
- **Services Required**:
  - Ops Center backend (FastAPI)
  - PostgreSQL database
  - Redis cache
  - Keycloak authentication
- **Test User**: `testuser` / `testpass123`
- **Execution Time**: ~10 minutes for full integration suite

### 3.3 E2E Test Environment

- **Platform**: Production-like staging environment
- **Browser**: Chrome/Firefox (for UI testing)
- **Services**: All services deployed and healthy
- **Test Users**: Multiple users with different roles
- **Execution Time**: ~30 minutes for manual E2E scenarios

### 3.4 Performance Test Environment

- **Specifications**:
  - 16+ CPU cores
  - 32GB+ RAM
  - SSD storage
- **Load**: Up to 200 concurrent users
- **Duration**: Sustained load for 10+ minutes
- **Monitoring**: CPU, memory, network, database metrics

---

## 4. Test Execution Schedule

### Phase 1: Unit Tests (Day 1)
- ✅ BYOK Manager unit tests
- ✅ Routing Engine unit tests
- ✅ API endpoint unit tests
- ✅ Usage analytics unit tests
- **Duration**: 4 hours
- **Owner**: QA Engineer

### Phase 2: Integration Tests (Day 2)
- ✅ Provider CRUD endpoints
- ✅ BYOK management flow
- ✅ Chat completion endpoints
- ✅ Usage analytics endpoints
- ✅ Health monitoring endpoints
- **Duration**: 6 hours
- **Owner**: QA Engineer + Backend Developer

### Phase 3: E2E Scenarios (Day 3)
- ✅ Scenario 1: BYOK Setup Flow
- ✅ Scenario 2: Power Level Usage
- ✅ Scenario 3: Fallback Mechanism
- ✅ Scenario 4: Usage Analytics
- ✅ Scenario 5: Multi-Provider BYOK
- ✅ Scenario 6: Rate Limiting
- ✅ Scenario 7: Streaming Responses
- ✅ Scenario 8: Error Recovery
- **Duration**: 8 hours (manual testing)
- **Owner**: QA Lead + Product Manager

### Phase 4: Performance Tests (Day 4)
- ✅ Routing latency benchmarks
- ✅ Concurrent request handling
- ✅ Cache performance
- ✅ Database query optimization
- ✅ Memory efficiency
- **Duration**: 6 hours
- **Owner**: Performance Engineer

### Phase 5: Security Tests (Day 5)
- ✅ Encryption validation
- ✅ Access control verification
- ✅ SQL injection prevention
- ✅ Authentication bypass attempts
- ✅ Data leak prevention
- **Duration**: 8 hours
- **Owner**: Security Engineer

---

## 5. Manual Testing Checklist

### 5.1 BYOK Management (Scenario 1)

- [ ] Navigate to API Keys page successfully
- [ ] Click "Add LLM Provider" opens modal
- [ ] Select provider from dropdown
- [ ] Enter valid API key format accepted
- [ ] Invalid API key format rejected with error
- [ ] Test Connection validates key correctly
- [ ] Successful key test shows green checkmark
- [ ] Failed key test shows error message
- [ ] Save button stores key successfully
- [ ] Key appears in list with masked value
- [ ] Key card shows correct metadata (name, provider, status, dates)
- [ ] Test button re-validates key
- [ ] Delete button removes key with confirmation
- [ ] Cannot add duplicate provider without warning
- [ ] Empty fields show validation errors

**Total Checks**: 15
**Expected Pass Rate**: 100%

### 5.2 Power Level Routing (Scenario 2)

- [ ] Eco mode badge displays "Free/Ultra-Low Cost"
- [ ] Eco request routes to Qwen/vLLM or Gemini Flash
- [ ] Eco request cost is $0.00 or <$0.0001 per 1K tokens
- [ ] Balanced mode badge displays "Best Value"
- [ ] Balanced request routes to GPT-4o Mini, Claude Haiku, or Gemini Flash
- [ ] Balanced request uses BYOK key if available
- [ ] Balanced request cost is $0.0002-$0.005 per 1K tokens
- [ ] Precision mode badge displays "Premium Models"
- [ ] Precision request routes to GPT-4o or Claude 3.5 Sonnet
- [ ] Precision request cost is $0.015 per 1K tokens
- [ ] Message details show correct routing info
- [ ] Power level persists across messages
- [ ] Response quality improves from eco → balanced → precision

**Total Checks**: 13
**Expected Pass Rate**: 100%

### 5.3 Fallback & Resilience (Scenario 3)

- [ ] All providers show healthy status initially
- [ ] Disable primary provider updates status to "Disabled"
- [ ] User request succeeds despite provider disabled
- [ ] Request automatically routed to secondary provider
- [ ] Message details indicate fallback occurred
- [ ] Health dashboard shows alert for disabled provider
- [ ] Re-enable provider restores health status
- [ ] Next request uses primary provider again
- [ ] Disable all but one provider shows warning
- [ ] Request still succeeds with last provider
- [ ] Disable all providers shows error page
- [ ] No internal errors exposed to user

**Total Checks**: 12
**Expected Pass Rate**: 100%

### 5.4 Usage Analytics (Scenario 4)

- [ ] Dashboard loads with charts and stats
- [ ] Stats cards show correct totals (requests, tokens, cost, latency)
- [ ] Pie chart shows power level breakdown
- [ ] Bar chart shows provider distribution
- [ ] Line chart shows cost over time
- [ ] Stacked bar chart shows BYOK vs platform usage
- [ ] Usage table displays all columns correctly
- [ ] Filter by date range works
- [ ] Filter by power level works
- [ ] Filter by provider works
- [ ] Sort by column headers works
- [ ] Export CSV downloads file
- [ ] CSV contains correct data
- [ ] Admin can view aggregate analytics

**Total Checks**: 14
**Expected Pass Rate**: 100%

### 5.5 Multi-Provider BYOK (Scenario 5)

- [ ] Can add OpenAI, Anthropic, Google keys
- [ ] All three keys visible in list
- [ ] System routes to cheapest BYOK option
- [ ] Can force specific provider selection
- [ ] Cost comparison visible in dashboard
- [ ] Each provider tracked separately

**Total Checks**: 6
**Expected Pass Rate**: 100%

### 5.6 Rate Limiting (Scenario 6)

- [ ] First 100 requests succeed
- [ ] 101st request returns rate limit error
- [ ] Error message is user-friendly
- [ ] Error suggests retry time
- [ ] Rate limit resets after configured time
- [ ] Admins can adjust limits per user

**Total Checks**: 6
**Expected Pass Rate**: 100%

### 5.7 Streaming (Scenario 7)

- [ ] Toggle streaming setting ON
- [ ] Streaming response appears word-by-word
- [ ] No delay before first word
- [ ] Works with eco power level
- [ ] Works with balanced power level
- [ ] Works with precision power level
- [ ] Stop button cancels stream
- [ ] Partial response visible after cancel
- [ ] Usage tracked for partial responses

**Total Checks**: 9
**Expected Pass Rate**: 100%

### 5.8 Error Recovery (Scenario 8)

- [ ] Deleted BYOK key triggers fallback
- [ ] Provider rate limit triggers fallback
- [ ] Network timeout retries automatically
- [ ] Error messages are user-friendly
- [ ] No internal errors exposed

**Total Checks**: 5
**Expected Pass Rate**: 100%

---

## 6. Automated Test Execution

### 6.1 Running Unit Tests

```bash
# Run all unit tests
cd /home/muut/Production/UC-Cloud/services/ops-center
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=backend/modules --cov-report=html

# Run specific test file
pytest tests/unit/test_byok_manager.py -v

# Run with detailed output
pytest tests/unit/ -v -s
```

**Expected Results**:
- All tests pass
- Coverage ≥80%
- Execution time <2 minutes

### 6.2 Running Integration Tests

```bash
# Prerequisites: Ensure services are running
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v

# Run with test database
pytest tests/integration/ -v --db=test

# Run specific endpoint tests
pytest tests/integration/test_llm_endpoints.py::TestBYOKEndpoints -v
```

**Expected Results**:
- All tests pass
- No 500 errors
- Execution time <10 minutes

### 6.3 Running Performance Tests

```bash
# Run performance test suite
pytest tests/performance/ -v -s

# Generate performance report
pytest tests/performance/test_routing_latency.py -v -s --tb=short

# View results
cat /tmp/epic_3_1_performance_report.json
```

**Expected Results**:
- Routing latency <100ms (p95)
- Throughput >100 req/sec
- Memory increase <50MB under load

### 6.4 Running Security Tests

```bash
# Run security test suite
pytest tests/security/ -v

# Run with security report
pytest tests/security/ -v --tb=short > /tmp/security_test_report.txt

# Test specific security aspects
pytest tests/security/test_byok_security.py::TestBYOKSecurity::test_keys_encrypted_at_rest -v
```

**Expected Results**:
- All security tests pass
- No data leaks detected
- All access controls enforced

---

## 7. CI/CD Integration

### 7.1 GitHub Actions Workflow

```yaml
name: Epic 3.1 Tests

on:
  push:
    branches: [main, epic-3.1]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run unit tests
        run: pytest tests/unit/ --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v

  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run security tests
        run: pytest tests/security/ -v
```

### 7.2 Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
        always_run: true
```

---

## 8. Defect Management

### 8.1 Bug Severity Levels

**Critical (P0)**:
- Data loss or corruption
- Security vulnerabilities
- System crashes
- API keys exposed in logs/responses

**High (P1)**:
- Feature completely broken
- Incorrect routing decisions
- Authentication bypass
- Fallback mechanism fails

**Medium (P2)**:
- Feature partially broken
- Performance degradation
- UI bugs affecting usability
- Incorrect analytics data

**Low (P3)**:
- Cosmetic issues
- Minor UI inconsistencies
- Documentation errors
- Non-critical logging issues

### 8.2 Bug Tracking Template

```markdown
**Bug ID**: EPIC3.1-BUG-XXX
**Title**: [Short description]
**Severity**: Critical / High / Medium / Low
**Component**: BYOK Manager / Routing Engine / API / UI
**Environment**: Dev / Staging / Production

**Description**:
[Detailed description of the issue]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [...]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screenshots/Logs**:
[Attach relevant evidence]

**Impact**:
- Users affected: [Number or percentage]
- Frequency: Always / Sometimes / Rare
- Workaround available: Yes / No

**Test Coverage**:
- Unit test: [Link to failing test]
- Integration test: [Link]
- E2E scenario: [Scenario number]

**Assignee**: [Developer name]
**Status**: Open / In Progress / Fixed / Verified
**Target Fix Date**: [YYYY-MM-DD]
```

### 8.3 Regression Test Suite

After bug fixes, run regression test suite:

```bash
# Run all tests to prevent regressions
pytest tests/ -v --tb=short

# Run tests related to fixed bug
pytest tests/ -k "byok" -v

# Run specific scenario
pytest tests/integration/test_llm_endpoints.py::TestBYOKEndpoints -v
```

---

## 9. Performance Benchmarks

### 9.1 Latency Requirements

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| Routing decision | <50ms | <100ms | >100ms |
| BYOK key retrieval (cold) | <200ms | <500ms | >500ms |
| BYOK key retrieval (cached) | <10ms | <50ms | >50ms |
| Database query | <20ms | <50ms | >50ms |
| Usage logging | <50ms | <100ms | >100ms |
| Health check | <100ms | <200ms | >200ms |

### 9.2 Throughput Requirements

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Concurrent users | 200 | 100 | <100 |
| Requests per second | 150 | 100 | <100 |
| Sustained load (10min) | 100 req/s | 80 req/s | <80 req/s |

### 9.3 Resource Limits

| Resource | Target | Acceptable | Unacceptable |
|----------|--------|------------|--------------|
| Memory increase (1000 req) | <25MB | <50MB | >50MB |
| CPU usage (sustained) | <50% | <70% | >70% |
| Database connections | <20 | <50 | >50 |

---

## 10. Security Requirements Checklist

### 10.1 Encryption & Data Protection

- [x] API keys encrypted at rest (Fernet 256-bit)
- [x] Encrypted keys stored in Keycloak user attributes
- [x] Decryption only occurs in memory, never written to disk
- [x] Encryption key stored securely (env variable or secrets manager)
- [x] Keys never logged in plaintext
- [x] Keys masked in all API responses
- [x] Keys masked in UI (show only last 4 chars)
- [x] Deleted keys are truly removed (not soft delete)

### 10.2 Access Control

- [x] Users can only access their own keys
- [x] Users cannot access other users' keys
- [x] Admins cannot see decrypted keys in Keycloak
- [x] API endpoints require authentication
- [x] JWT tokens validated and verified
- [x] Expired tokens rejected
- [x] Invalid tokens rejected
- [x] RBAC enforced (user vs admin permissions)

### 10.3 Input Validation

- [x] SQL injection attempts blocked
- [x] XSS attempts sanitized
- [x] Path traversal attempts blocked
- [x] Invalid API key formats rejected
- [x] Empty/null inputs handled gracefully
- [x] Excessively long inputs truncated/rejected
- [x] Special characters escaped

### 10.4 Security Headers

- [ ] CORS configured correctly
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY or SAMEORIGIN
- [ ] X-XSS-Protection: 1; mode=block
- [ ] Content-Security-Policy configured
- [ ] Strict-Transport-Security (HSTS) enabled

### 10.5 Audit & Monitoring

- [x] All key operations logged for audit
- [x] Failed authentication attempts logged
- [x] Unusual activity flagged (rapid key additions)
- [x] Audit logs tamper-resistant
- [x] Security events sent to monitoring system

---

## 11. Test Deliverables

### 11.1 Test Artifacts

1. **Test Code**:
   - `/tests/unit/` - 88 unit tests
   - `/tests/integration/` - 53 integration tests
   - `/tests/performance/` - 15 performance tests
   - `/tests/security/` - 30 security tests
   - `/tests/e2e/` - 8 E2E scenarios

2. **Test Data**:
   - `/tests/fixtures/llm_test_data.py` - Mock data and fixtures

3. **Documentation**:
   - `/tests/EPIC_3_1_TEST_PLAN.md` - This document
   - `/tests/e2e/test_epic_3_1_flows.md` - E2E scenarios
   - `/EPIC_3.1_TEST_SUITE_COMPLETE.md` - Summary

4. **Reports**:
   - `/tmp/epic_3_1_performance_report.json` - Performance metrics
   - `/tmp/security_test_report.txt` - Security audit
   - Coverage report (HTML) - `htmlcov/index.html`

### 11.2 Sign-Off Criteria

**Unit Tests**:
- [x] All tests written and passing
- [x] Coverage ≥80%
- [x] No critical issues

**Integration Tests**:
- [x] All critical paths covered
- [x] All tests passing
- [x] No 500 errors

**E2E Tests**:
- [ ] All 8 scenarios executed
- [ ] All scenarios pass
- [ ] No critical bugs found

**Performance Tests**:
- [ ] All benchmarks met
- [ ] Performance report generated
- [ ] No memory leaks

**Security Tests**:
- [ ] All security tests pass
- [ ] No critical vulnerabilities
- [ ] Security report generated

**Final Sign-Off**:
- [ ] QA Lead approval
- [ ] Security Engineer approval
- [ ] Product Manager approval
- [ ] Ready for production deployment

---

## 12. Contact Information

**QA Lead**: [Name] - [email]
**Security Engineer**: [Name] - [email]
**Backend Lead**: [Name] - [email]
**Product Manager**: [Name] - [email]

**Issue Tracker**: https://github.com/Unicorn-Commander/UC-Cloud/issues
**Test Results Dashboard**: [URL]
**CI/CD Pipeline**: [URL]

---

## 13. Appendices

### Appendix A: Test Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/Unicorn-Commander/UC-Cloud.git
cd UC-Cloud/services/ops-center

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio httpx

# 4. Set environment variables
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export DATABASE_URL="postgresql://test:test@localhost:5432/test_db"
export REDIS_URL="redis://localhost:6379"

# 5. Start services
docker-compose up -d postgres redis keycloak

# 6. Run database migrations
alembic upgrade head

# 7. Create test user
python scripts/create_test_user.py

# 8. Run tests
pytest tests/ -v
```

### Appendix B: Useful Commands

```bash
# Run tests with output
pytest tests/ -v -s

# Run specific test
pytest tests/unit/test_byok_manager.py::TestBYOKManager::test_encrypt_decrypt_key -v

# Run tests matching pattern
pytest tests/ -k "byok" -v

# Run tests with coverage
pytest tests/ --cov=backend --cov-report=html

# Run tests and stop on first failure
pytest tests/ -x

# Run tests with detailed traceback
pytest tests/ --tb=short

# Generate test report
pytest tests/ --html=report.html --self-contained-html
```

### Appendix C: Troubleshooting

**Tests hanging**:
- Check if services (postgres, redis) are running
- Verify DATABASE_URL and REDIS_URL are correct
- Ensure no port conflicts

**Import errors**:
- Verify PYTHONPATH includes backend directory
- Check all dependencies installed: `pip list`

**Authentication failures**:
- Verify Keycloak is running and accessible
- Check test user exists
- Verify JWT secret is correct

**Database errors**:
- Run migrations: `alembic upgrade head`
- Check database connection: `psql $DATABASE_URL`
- Verify test database is empty before tests

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Next Review**: After Epic 3.1 completion
