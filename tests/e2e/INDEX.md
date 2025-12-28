# E2E Test Suite - Documentation Index

Quick reference guide to all E2E test documentation.

---

## 🚀 Quick Start

**New to the test suite? Start here:**

1. **[QUICK_START.md](QUICK_START.md)** - Get testing in 5 minutes
   - Installation
   - Basic commands
   - First test run

---

## 📚 Complete Documentation

### Setup & Configuration

- **[README.md](README.md)** - Complete setup and usage guide
  - Mac Studio requirements
  - Installation steps
  - Configuration
  - Running tests
  - Troubleshooting

- **[../.env.test.example](../.env.test.example)** - Environment configuration
  - Required variables
  - Optional settings

### Test Suite

- **[ops-center.spec.js](ops-center.spec.js)** - Main test suite
  - 37+ tests across 8 phases
  - Accessibility tests
  - User management tests
  - Billing tests
  - Security tests
  - Analytics tests
  - Services tests
  - Monitoring tests
  - Subscription tests

### Helper Libraries

- **[helpers/auth.js](helpers/auth.js)** - Keycloak SSO authentication
  - `loginViaKeycloak()`
  - `logout()`
  - `isLoggedIn()`

- **[helpers/api.js](helpers/api.js)** - API testing utilities
  - `checkApiEndpoint()`
  - `waitForApiCall()`
  - `captureApiCalls()`

- **[helpers/accessibility.js](helpers/accessibility.js)** - Accessibility testing
  - `runAccessibilityAudit()`
  - `checkKeyboardNavigation()`
  - `checkAriaAttributes()`

---

## 📊 Reports & Summaries

- **[TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)** - Comprehensive overview
  - Test coverage breakdown
  - Key features
  - Performance benchmarks
  - Success metrics

- **[../E2E_TEST_SUITE_DELIVERY.md](../E2E_TEST_SUITE_DELIVERY.md)** - Delivery report
  - Files created
  - Installation instructions
  - Directory structure
  - Next steps

---

## 🔧 Configuration Files

- **[../playwright.config.js](../playwright.config.js)** - Playwright configuration
  - Browser settings
  - Timeout configuration
  - Reporter setup
  - Mac Studio optimizations

- **[../package.json](../package.json)** - NPM scripts
  - `test:e2e` - Run all tests
  - `test:e2e:ui` - Interactive mode
  - `test:e2e:debug` - Debug mode
  - [See all scripts →](../package.json)

---

## 🤖 CI/CD

- **[../.github/workflows/e2e-tests.yml](../.github/workflows/e2e-tests.yml)** - GitHub Actions
  - Automated test runs
  - Multi-browser testing
  - Scheduled runs
  - Failure notifications

---

## 📖 How to Use This Index

### I want to...

#### **...get started quickly**
→ Read [QUICK_START.md](QUICK_START.md)

#### **...understand the full setup**
→ Read [README.md](README.md)

#### **...see what tests exist**
→ Read [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)

#### **...understand the implementation**
→ Read [ops-center.spec.js](ops-center.spec.js)

#### **...add authentication to tests**
→ Check [helpers/auth.js](helpers/auth.js)

#### **...test API endpoints**
→ Check [helpers/api.js](helpers/api.js)

#### **...test accessibility**
→ Check [helpers/accessibility.js](helpers/accessibility.js)

#### **...configure the tests**
→ Edit [../playwright.config.js](../playwright.config.js)

#### **...run specific tests**
→ See NPM scripts in [README.md](README.md#running-tests)

#### **...troubleshoot issues**
→ See [README.md - Troubleshooting](README.md#troubleshooting)

#### **...set up CI/CD**
→ Read [../.github/workflows/e2e-tests.yml](../.github/workflows/e2e-tests.yml)

#### **...understand what was delivered**
→ Read [../E2E_TEST_SUITE_DELIVERY.md](../E2E_TEST_SUITE_DELIVERY.md)

---

## 🎯 Common Tasks

### Run Tests

```bash
# All tests
npm run test:e2e

# Interactive UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug

# Specific browser
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit

# Accessibility only
npm run test:e2e:accessibility
```

### View Reports

```bash
# Open HTML report
npm run test:e2e:report

# Or manually
open test-results/playwright-report/index.html
```

### Debug Failed Tests

```bash
# Run specific test in debug mode
npx playwright test -g "Test name" --debug

# View trace
npx playwright show-trace test-results/trace.zip
```

---

## 📁 File Structure

```
tests/e2e/
├── INDEX.md                          # This file
├── QUICK_START.md                    # 5-minute setup guide
├── README.md                         # Complete documentation
├── TEST_SUITE_SUMMARY.md             # Comprehensive summary
├── ops-center.spec.js                # Main test suite
└── helpers/
    ├── auth.js                       # Authentication helpers
    ├── api.js                        # API testing utilities
    └── accessibility.js              # Accessibility testing
```

---

## 🔗 External Resources

- **Playwright Documentation**: https://playwright.dev/docs/intro
- **Axe-Core Documentation**: https://github.com/dequelabs/axe-core
- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

## 📞 Support

**Have questions?**

1. Check the [README.md](README.md) troubleshooting section
2. Review test output in HTML report
3. Debug with `npm run test:e2e:debug`
4. Check GitHub Actions logs for CI failures

---

**Last Updated**: October 26, 2025
**Version**: 1.0.0
