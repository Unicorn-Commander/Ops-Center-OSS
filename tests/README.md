# UC-1 Pro Billing System Tests

Comprehensive E2E test suite for the billing system including Keycloak SSO, Lago billing, Stripe payments, and BYOK functionality.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-test.txt

# 2. Configure environment
cp .env.test.example .env.test
# Edit .env.test with your credentials

# 3. Setup test users
python3 setup_test_data.py --setup

# 4. Run all tests
pytest -v

# 5. Cleanup
python3 setup_test_data.py --cleanup
```

## Test Files

- **`e2e_billing_test.py`** - Complete E2E test suite (pytest)
- **`test_billing_integration.sh`** - API endpoint integration tests (bash)
- **`setup_test_data.py`** - Test user management for Keycloak
- **`simulate_webhooks.py`** - Webhook event simulator
- **`conftest.py`** - Shared pytest fixtures
- **`pytest.ini`** - Pytest configuration
- **`TEST_REPORT.md`** - Comprehensive test documentation

## Running Tests

### All Tests
```bash
pytest tests/ -v --html=report.html
```

### E2E Tests Only
```bash
pytest tests/e2e_billing_test.py -v
```

### Integration Tests
```bash
./tests/test_billing_integration.sh
```

### Specific Test Class
```bash
pytest tests/e2e_billing_test.py::TestUserSignupFlow -v
```

### With Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

## Test Data Management

### Setup Test Users
```bash
python3 tests/setup_test_data.py --setup
```

### List Test Users
```bash
python3 tests/setup_test_data.py --list
```

### Cleanup Test Users
```bash
python3 tests/setup_test_data.py --cleanup
```

### Full Reset
```bash
python3 tests/setup_test_data.py --reset
```

## Webhook Testing

### Single Webhook
```bash
python3 tests/simulate_webhooks.py \
  --type lago_subscription_created \
  --email test@example.com
```

### All Webhooks
```bash
python3 tests/simulate_webhooks.py --run-all
```

## Environment Variables

Required variables in `.env.test`:

```bash
# Keycloak
KEYCLOAK_URL=https://auth.unicorncommander.ai
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=your_password

# Stripe (Test Mode)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# BYOK
ENCRYPTION_KEY=your_fernet_key

# Base URL
BASE_URL=http://localhost:8084
```

## Test Coverage

Current coverage: **~87%**

| Component | Coverage |
|-----------|----------|
| Keycloak Integration | 90% |
| Stripe Client | 85% |
| Lago Webhooks | 95% |
| Tier Enforcement | 92% |
| BYOK System | 87% |
| Usage Tracking | 90% |

## Test Users

The following test users are created:

| Tier | Email | API Limit | BYOK |
|------|-------|-----------|------|
| Trial | test-trial@example.com | 100 | No |
| Starter | test-starter@example.com | 10,000 | Yes |
| Professional | test-professional@example.com | 100,000 | Yes |
| Enterprise | test-enterprise@example.com | 1,000,000 | Yes |

## Troubleshooting

### Tests fail with "Connection refused"
- Ensure Keycloak is accessible
- Check BASE_URL is correct
- Verify network connectivity

### "Admin token failed"
- Check Keycloak credentials
- Verify admin user has correct permissions
- Check realm name

### Stripe tests skipped
- Set STRIPE_SECRET_KEY in .env.test
- Use test mode keys only

### Test users not found
- Run `setup_test_data.py --setup` first
- Check Keycloak connection
- Verify realm name is correct

## Documentation

See **TEST_REPORT.md** for comprehensive documentation including:
- Test architecture
- Test scenarios
- Known issues
- Production readiness assessment
- Recommendations

## Support

For issues or questions:
- Check TEST_REPORT.md
- Review test output logs
- Check Keycloak admin console
- Verify environment variables

## Contributing

When adding new tests:
1. Follow existing patterns in e2e_billing_test.py
2. Add appropriate markers (@pytest.mark.*)
3. Update TEST_REPORT.md
4. Ensure cleanup in fixtures
5. Document environment variables needed
