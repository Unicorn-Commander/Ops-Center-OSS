# Extensions Marketplace Testing Strategy

**Project**: Ops-Center Extensions Marketplace (Phase 1 MVP)
**Created**: November 1, 2025
**Status**: Ready for Implementation

---

## Executive Summary

This document outlines the comprehensive testing strategy for the Extensions Marketplace feature, a new e-commerce system within Ops-Center that allows users to purchase add-ons and premium features through Stripe Checkout.

**Test Pyramid**:
- **Unit Tests**: 70% coverage target (30+ tests)
- **Integration Tests**: 20% coverage target (5+ tests)
- **E2E Tests**: 10% coverage target (1-2 tests)

**Total Estimated Tests**: 40-50 tests
**Estimated Testing Time**: 8-12 hours
**Expected Coverage**: >75%

---

## Test Environments

### 1. Local Development
- **Database**: PostgreSQL test database (separate from prod)
- **Payment**: Mocked Stripe API calls
- **Authentication**: Test Keycloak users
- **Purpose**: Rapid iteration, unit/integration testing

### 2. CI/CD Pipeline (Future)
- **Platform**: GitHub Actions
- **Triggers**: Push to main, Pull Requests
- **Tests Run**: All unit, integration, security tests
- **Coverage Reports**: Codecov integration

### 3. Staging Environment
- **Database**: Staging PostgreSQL
- **Payment**: Stripe Test Mode with real API calls
- **Authentication**: Staging Keycloak instance
- **Purpose**: Pre-production validation, E2E testing

### 4. Production
- **Database**: Production PostgreSQL
- **Payment**: Stripe Live Mode
- **Monitoring**: Real-time error tracking (Sentry)
- **Testing**: Smoke tests only, no full test suite

---

## Critical User Journeys

### Journey 1: Successful Purchase (Happy Path)
**User Goal**: Browse marketplace → Add to cart → Checkout → Pay → Receive add-on

**Steps**:
1. User lands on `/admin/marketplace`
2. Browses catalog of 9 add-ons
3. Clicks "Add to Cart" on "TTS Premium Service" ($9.99/month)
4. Reviews cart, applies promo code "SAVE15" (15% discount)
5. Clicks "Checkout"
6. Redirected to Stripe Checkout
7. Enters payment info (test card: 4242 4242 4242 4242)
8. Completes payment
9. Redirected back with success message
10. Add-on activated immediately
11. Can access new TTS features

**Expected Outcome**: ✅ Purchase successful, add-on active, invoice generated

**Test Coverage**:
- Unit tests: Cart calculation with promo code
- Integration test: Full flow with mocked Stripe
- E2E test: Real Stripe test mode checkout

### Journey 2: Abandoned Cart
**User Goal**: Add items to cart but don't complete purchase

**Steps**:
1. Add 3 items to cart
2. Navigate away from checkout page
3. Return later
4. Cart persists with items

**Expected Outcome**: ✅ Cart persists for 24 hours

**Test Coverage**:
- Unit tests: Cart persistence
- Integration test: Session management

### Journey 3: Payment Failure
**User Goal**: Attempt purchase with declined card

**Steps**:
1. Complete checkout with declined card (4000 0000 0000 0002)
2. Stripe returns error
3. User sees error message
4. Can retry payment
5. Add-on NOT activated

**Expected Outcome**: ✅ Graceful error handling, no partial activation

**Test Coverage**:
- Integration test: Stripe webhook handling (payment_failed)
- Unit tests: Error state management

### Journey 4: Promo Code Usage
**User Goal**: Apply discount code at checkout

**Steps**:
1. Add $49.99 add-on to cart
2. Enter promo code "SAVE20"
3. See discount applied (-$10.00)
4. Final price: $39.99

**Expected Outcome**: ✅ Correct discount calculation, valid promo codes accepted

**Test Coverage**:
- Unit tests: Promo code validation (expired, invalid, valid)
- Unit tests: Discount calculation (percentage, fixed amount)

### Journey 5: Admin Creates Add-On
**User Goal**: Admin publishes new add-on to marketplace

**Steps**:
1. Admin navigates to `/admin/marketplace/manage`
2. Clicks "Create Add-On"
3. Fills in details (name, description, price, category, features)
4. Uploads icon image
5. Sets billing type (monthly/annual)
6. Clicks "Publish"
7. Add-on appears in marketplace immediately

**Expected Outcome**: ✅ Add-on created, visible to users, purchasable

**Test Coverage**:
- Unit tests: Add-on creation validation
- Integration test: End-to-end admin workflow

---

## Test Data Strategy

### Seed Data

#### 1. Add-Ons (9 Pre-configured)

**AI Services**:
1. **TTS Premium Service** - $9.99/month
   - Features: `tts_enabled`, `voice_customization`, `emotion_control`
   - Category: `ai-services`

2. **STT Professional** - $9.99/month
   - Features: `stt_enabled`, `speaker_diarization`, `100_languages`
   - Category: `ai-services`

3. **Image Generation Plus** - $14.99/month
   - Features: `image_gen_enabled`, `advanced_models`, `high_res_output`
   - Category: `ai-services`

**Storage & Compute**:
4. **Storage Expansion 100GB** - $4.99/month
   - Features: `storage_100gb`, `automatic_backups`
   - Category: `storage`

5. **Premium Compute** - $29.99/month
   - Features: `dedicated_gpu`, `priority_processing`
   - Category: `compute`

**Integrations**:
6. **GitHub Integration** - $7.99/month
   - Features: `github_sync`, `ci_cd_integration`
   - Category: `integrations`

7. **Slack Notifications** - $4.99/month
   - Features: `slack_webhook`, `custom_alerts`
   - Category: `integrations`

**Analytics**:
8. **Advanced Analytics** - $19.99/month
   - Features: `analytics_dashboard`, `export_reports`, `api_access`
   - Category: `analytics`

9. **Custom Branding** - $49.99/month
   - Features: `white_label`, `custom_domain`, `branding_removal`
   - Category: `enterprise`

#### 2. Promo Codes (3 Test Codes)

1. **SAVE15**
   - Type: Percentage
   - Discount: 15%
   - Status: Active
   - Expires: 2025-12-31

2. **WELCOME10**
   - Type: Fixed Amount
   - Discount: $10.00
   - Status: Active
   - Expires: 2025-12-31

3. **EXPIRED**
   - Type: Percentage
   - Discount: 20%
   - Status: Inactive
   - Expires: 2024-01-01

#### 3. Test Users (5 Users)

1. **Trial User**
   - Email: `trial@test.com`
   - Tier: Trial
   - Credits: 100
   - Active Add-ons: None

2. **Starter User**
   - Email: `starter@test.com`
   - Tier: Starter
   - Credits: 1000
   - Active Add-ons: None

3. **Professional User**
   - Email: `pro@test.com`
   - Tier: Professional
   - Credits: 10000
   - Active Add-ons: [TTS Premium, STT Professional]

4. **Enterprise User**
   - Email: `enterprise@test.com`
   - Tier: Enterprise
   - Credits: Unlimited
   - Active Add-ons: [All 9 add-ons]

5. **Admin User**
   - Email: `admin@test.com`
   - Role: Admin
   - Can: Create/edit/delete add-ons

#### 4. Test Stripe Cards

**Successful Payments**:
- `4242 4242 4242 4242` - Visa (always succeeds)
- `5555 5555 5555 4444` - Mastercard (always succeeds)

**Declined Payments**:
- `4000 0000 0000 0002` - Card declined
- `4000 0000 0000 9995` - Insufficient funds

**Requires Authentication** (3D Secure):
- `4000 0025 0000 3155` - Requires authentication

---

## Testing Tools & Frameworks

### Backend Testing

#### pytest (Primary Framework)
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

**Plugins**:
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `faker` - Test data generation

#### unittest.mock
```python
from unittest.mock import Mock, patch, MagicMock

# Mock Stripe API calls
with patch('stripe.checkout.Session.create') as mock_create:
    mock_create.return_value = {'id': 'cs_test_123', 'url': 'https://...'}
    result = create_checkout_session(user_id, cart_items)
```

### Frontend Testing

#### Jest + React Testing Library
```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

**Configuration** (`jest.config.js`):
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/**/*.test.{js,jsx}',
  ],
};
```

### E2E Testing

#### Stripe CLI (Webhook Testing)
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Trigger webhook
stripe trigger checkout.session.completed
```

#### Playwright (Future Enhancement)
```bash
npm install --save-dev @playwright/test
```

### Performance Testing

#### Locust (Load Testing)
```bash
pip install locust
```

**Example** (`locustfile.py`):
```python
from locust import HttpUser, task

class MarketplaceUser(HttpUser):
    @task
    def browse_catalog(self):
        self.client.get("/api/v1/marketplace/catalog")

    @task(2)
    def add_to_cart(self):
        self.client.post("/api/v1/marketplace/cart/add", json={
            "add_on_id": "tts-premium",
            "quantity": 1
        })
```

---

## Test Categories

### 1. Unit Tests (70% of tests)

**Backend Unit Tests** (`backend/tests/`):

#### test_catalog.py (10 tests)
- `test_get_all_addons()` - Retrieves all 9 add-ons
- `test_get_addon_by_id()` - Gets specific add-on
- `test_get_addon_not_found()` - 404 for invalid ID
- `test_filter_by_category()` - Filters add-ons by category
- `test_search_addons()` - Search by name/description
- `test_addon_price_formatting()` - Correct decimal handling
- `test_addon_features_list()` - Features array structure
- `test_addon_billing_types()` - Monthly vs annual billing
- `test_addon_sort_by_price()` - Sort ascending/descending
- `test_addon_pagination()` - Limit/offset pagination

#### test_cart.py (12 tests)
- `test_add_to_cart()` - Add item to cart
- `test_add_duplicate_item()` - Updates quantity, not duplicate
- `test_remove_from_cart()` - Remove specific item
- `test_clear_cart()` - Empty entire cart
- `test_cart_total_calculation()` - Correct subtotal
- `test_cart_with_promo_code()` - Apply percentage discount
- `test_cart_with_fixed_discount()` - Apply fixed amount discount
- `test_cart_with_expired_promo()` - Reject expired code
- `test_cart_with_invalid_promo()` - Reject invalid code
- `test_cart_persistence()` - Cart saved to session
- `test_cart_empty_check()` - Validate empty cart
- `test_cart_item_limit()` - Max 10 items per cart

#### test_promo_codes.py (6 tests)
- `test_validate_promo_code()` - Valid code accepted
- `test_expired_promo_code()` - Expired code rejected
- `test_invalid_promo_code()` - Invalid code rejected
- `test_percentage_discount_calculation()` - Correct % math
- `test_fixed_amount_discount()` - Correct $ math
- `test_promo_code_case_insensitive()` - "SAVE15" = "save15"

#### test_stripe_integration.py (8 tests)
- `test_create_checkout_session()` - Session created with line items
- `test_checkout_metadata()` - User/cart metadata included
- `test_webhook_signature_verification()` - Valid signatures accepted
- `test_webhook_invalid_signature()` - Invalid signatures rejected
- `test_webhook_payment_succeeded()` - Activates add-on on success
- `test_webhook_payment_failed()` - No activation on failure
- `test_webhook_subscription_created()` - Monthly billing created
- `test_webhook_refund_issued()` - Add-on deactivated on refund

**Frontend Unit Tests** (`src/tests/`):

#### ExtensionsMarketplace.test.jsx (8 tests)
- `renders marketplace with add-ons` - Page loads
- `displays 9 add-on cards` - All cards visible
- `filters by category` - Category filter works
- `search functionality` - Search bar filters results
- `add to cart button works` - Cart count increments
- `displays cart icon with count` - Badge shows item count
- `responsive grid layout` - Mobile/desktop layouts
- `loading state displayed` - Skeleton loader shown

#### CheckoutPage.test.jsx (6 tests)
- `displays cart items` - Shows all cart contents
- `calculates total correctly` - Subtotal accurate
- `applies promo code` - Discount applied
- `removes promo code` - Discount removed
- `empty cart message` - "Cart is empty" shown
- `proceed to checkout button` - Redirects to Stripe

### 2. Integration Tests (20% of tests)

**Integration Tests** (`backend/tests/integration/`):

#### test_purchase_flow.py (5 tests)
- `test_complete_purchase_flow()` - Full happy path
  1. Get catalog → 2. Add to cart → 3. Create checkout → 4. Webhook payment → 5. Verify activation

- `test_cart_to_checkout_flow()` - Cart operations
  1. Add 3 items → 2. Remove 1 item → 3. Apply promo → 4. Create checkout

- `test_promo_code_integration()` - Discount flow
  1. Add item → 2. Apply "SAVE15" → 3. Verify 15% discount

- `test_payment_failure_handling()` - Failure recovery
  1. Create checkout → 2. Simulate payment_failed webhook → 3. Verify no activation

- `test_admin_create_addon()` - Admin workflow
  1. Create add-on → 2. Publish → 3. Verify in catalog → 4. User can purchase

### 3. End-to-End Tests (10% of tests)

**E2E Tests** (`backend/tests/e2e/`):

#### test_stripe_checkout_e2e.py (2 tests)
- `test_real_stripe_checkout()` - Full Stripe test mode
  1. Create checkout session (real Stripe API)
  2. Use Stripe CLI to trigger `checkout.session.completed`
  3. Verify webhook processed
  4. Verify add-on activated
  5. Verify invoice created

- `test_subscription_lifecycle()` - Monthly billing
  1. Purchase monthly add-on
  2. Verify subscription created
  3. Simulate `invoice.upcoming` (30 days later)
  4. Verify renewal charge
  5. Cancel subscription
  6. Verify add-on deactivated

### 4. Security Tests

**Security Tests** (`backend/tests/security/`):

#### test_security.py (6 tests)
- `test_sql_injection_prevention()` - Parameterized queries
- `test_xss_prevention()` - Sanitized inputs
- `test_csrf_protection()` - CSRF tokens required
- `test_webhook_signature_required()` - Unsigned webhooks rejected
- `test_rate_limiting()` - API rate limits enforced
- `test_authentication_required()` - Unauthorized requests blocked

### 5. Performance Tests

**Performance Tests** (`backend/tests/performance/`):

#### test_load.py (Locust)
- **Scenario**: 100 concurrent users
- **Duration**: 5 minutes
- **Endpoints Tested**:
  - GET `/api/v1/marketplace/catalog` (50% of traffic)
  - POST `/api/v1/marketplace/cart/add` (30% of traffic)
  - POST `/api/v1/marketplace/checkout/create` (20% of traffic)
- **Success Criteria**:
  - 95th percentile response time < 500ms
  - Error rate < 1%
  - No memory leaks

---

## Test Fixtures & Setup

### pytest Configuration

**File**: `backend/tests/pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=backend
    --cov-report=html
    --cov-report=term
    --cov-report=xml
    --verbose
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow-running tests
    security: Security tests
```

### conftest.py (Shared Fixtures)

**File**: `backend/tests/conftest.py`
```python
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_engine("postgresql://test:test@localhost/test_marketplace")
    # Create tables
    Base.metadata.create_all(engine)
    yield engine
    # Cleanup
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_user():
    """Create test user"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "tier": "professional",
        "credits": 10000
    }

@pytest.fixture
def test_addons():
    """Return list of test add-ons"""
    return [
        {
            "id": "tts-premium",
            "name": "TTS Premium Service",
            "price": 9.99,
            "category": "ai-services",
            "features": ["tts_enabled", "voice_customization"]
        },
        {
            "id": "stt-professional",
            "name": "STT Professional",
            "price": 9.99,
            "category": "ai-services",
            "features": ["stt_enabled", "speaker_diarization"]
        }
    ]

@pytest.fixture
def mock_stripe():
    """Mock Stripe API"""
    with patch('stripe.checkout.Session') as mock:
        mock.create.return_value = {
            "id": "cs_test_123",
            "url": "https://checkout.stripe.com/test",
            "status": "open"
        }
        yield mock
```

---

## Coverage Goals

### Overall Coverage: >75%

**By Component**:
- **Catalog API**: 90% coverage
- **Cart Logic**: 85% coverage
- **Promo Codes**: 90% coverage
- **Stripe Integration**: 80% coverage
- **Webhook Handlers**: 75% coverage
- **Frontend Components**: 70% coverage

**Excluded from Coverage**:
- Third-party libraries
- Configuration files
- Test utilities

---

## CI/CD Integration (Future)

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`
```yaml
name: Extensions Marketplace Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_marketplace
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov

      - name: Run backend tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install frontend dependencies
        run: npm install

      - name: Run frontend tests
        run: npm test -- --coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml,./coverage/lcov.info
```

---

## Success Criteria

### Functional Requirements
- ✅ All 9 add-ons load in catalog
- ✅ Cart operations work (add, remove, update)
- ✅ Promo codes apply discounts correctly
- ✅ Stripe checkout creates sessions
- ✅ Webhooks activate add-ons on payment
- ✅ Add-ons appear in user's active list

### Non-Functional Requirements
- ✅ Test coverage >75%
- ✅ All tests run in <5 minutes
- ✅ No flaky tests (100% pass rate on re-runs)
- ✅ Performance: Catalog loads in <200ms
- ✅ Security: All injection tests pass

### Documentation Requirements
- ✅ Testing strategy document (this file)
- ✅ Test data seed documentation
- ✅ API endpoint test examples
- ✅ Frontend component test examples
- ✅ E2E test setup guide

---

## Risk Mitigation

### Risk 1: Stripe API Rate Limits
**Mitigation**: Use mocking for 90% of tests, only E2E uses real API

### Risk 2: Test Data Contamination
**Mitigation**: Each test uses isolated fixtures, database cleaned after each test

### Risk 3: Flaky Webhook Tests
**Mitigation**: Use deterministic test data, mock time-sensitive operations

### Risk 4: Long Test Execution Times
**Mitigation**: Parallel test execution, optimize slow tests, use test markers

---

## Next Steps

1. **Implement Test Infrastructure** (2 hours)
   - Set up pytest configuration
   - Create conftest.py with fixtures
   - Set up Jest configuration

2. **Create Test Data** (1 hour)
   - Seed 9 add-ons
   - Create 3 promo codes
   - Generate 5 test users

3. **Write Backend Unit Tests** (4 hours)
   - Catalog tests (10)
   - Cart tests (12)
   - Promo code tests (6)
   - Stripe integration tests (8)

4. **Write Frontend Unit Tests** (2 hours)
   - ExtensionsMarketplace component (8)
   - CheckoutPage component (6)

5. **Write Integration Tests** (2 hours)
   - Purchase flow (5 tests)

6. **Write E2E Tests** (1 hour)
   - Stripe checkout test (1 test)

7. **Run Tests & Generate Reports** (1 hour)
   - Execute all tests
   - Generate coverage reports
   - Document bugs found
   - Create recommendations

**Total Estimated Time**: 13 hours

---

## Conclusion

This testing strategy provides comprehensive coverage for the Extensions Marketplace feature. By following the test pyramid approach and focusing on critical user journeys, we ensure the marketplace is reliable, secure, and performant.

**Key Takeaways**:
- **70% Unit Tests**: Fast feedback on business logic
- **20% Integration Tests**: Verify component interactions
- **10% E2E Tests**: Validate complete user flows
- **Security First**: Prevent SQL injection, XSS, CSRF
- **Performance Validated**: Load testing ensures scalability

With this strategy in place, the Extensions Marketplace can be developed with confidence, knowing that comprehensive automated testing will catch issues early.
