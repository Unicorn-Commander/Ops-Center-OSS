# Ops-Center E2E Tests - Mac Studio Setup Guide

Comprehensive end-to-end testing suite for Ops-Center using Playwright.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

---

## Prerequisites

### Mac Studio Requirements

- **macOS**: 12.0 (Monterey) or later
- **Node.js**: 18.x or 20.x (LTS)
- **Chrome**: Latest stable version
- **Terminal**: Terminal.app, iTerm2, or similar
- **Storage**: ~500MB for Playwright browsers

### Optional Tools

- **VS Code**: For test development
- **Playwright VS Code Extension**: For interactive test running

---

## Installation

### 1. Install Node.js (if not already installed)

```bash
# Using Homebrew
brew install node@20

# Verify installation
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

### 2. Install Playwright and Dependencies

Navigate to the ops-center directory:

```bash
cd /opt/ops-center
```

Install Playwright:

```bash
# Install Playwright browsers (Chromium, Firefox, WebKit)
npx playwright install

# Install system dependencies
npx playwright install-deps

# Or install only Chromium for faster setup
npx playwright install chromium
```

### 3. Install Test Dependencies

```bash
# Install all dependencies
npm install

# Verify Playwright is installed
npx playwright --version
```

### 4. Configure Environment

Create `.env.test` file:

```bash
cat > .env.test << 'EOF'
# Base URL for Ops-Center
BASE_URL=https://unicorncommander.ai

# Test credentials (Keycloak SSO)
TEST_USERNAME=admin
TEST_PASSWORD=your-admin-password

# Optional: Override specific settings
PLAYWRIGHT_WORKERS=1
PLAYWRIGHT_TIMEOUT=60000
EOF
```

---

## Running Tests

### Quick Start

```bash
# Run all E2E tests
npm run test:e2e

# Or use Playwright CLI directly
npx playwright test
```

### Interactive Mode (Recommended for Development)

```bash
# Run with Playwright UI (interactive mode)
npx playwright test --ui

# Run specific test file
npx playwright test tests/e2e/ops-center.spec.js --ui

# Run in headed mode (see browser)
npx playwright test --headed
```

### Running Specific Tests

```bash
# Run only accessibility tests
npx playwright test -g "Accessibility"

# Run only User Management tests
npx playwright test -g "User Management"

# Run specific test by name
npx playwright test -g "Sidebar collapse keyboard navigation"

# Run on specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Debug Mode

```bash
# Run in debug mode (step through tests)
npx playwright test --debug

# Debug specific test
npx playwright test -g "User Management" --debug

# Generate trace for failed tests
npx playwright test --trace on
```

### Viewing Reports

```bash
# Open HTML report
npx playwright show-report

# Or open manually
open test-results/playwright-report/index.html
```

---

## Test Structure

### Test Organization

```
tests/e2e/
├── ops-center.spec.js          # Main test suite
├── helpers/
│   ├── auth.js                 # Keycloak SSO authentication
│   ├── api.js                  # API testing utilities
│   └── accessibility.js        # Accessibility testing (axe-core)
└── README.md                   # This file
```

### Test Coverage

The test suite covers 8 major phases:

1. **Accessibility & Keyboard Navigation**
   - Sidebar keyboard controls
   - ARIA labels and roles
   - Focus indicators
   - WCAG 2.1 compliance

2. **User Management**
   - User list loading
   - Advanced filtering
   - User detail pages
   - Bulk operations
   - CSV export

3. **Billing Dashboard**
   - Revenue metrics
   - Chart rendering
   - Subscription plans
   - No 404 errors

4. **Security & Audit Logs**
   - Security page
   - Audit log API
   - Activity timeline

5. **Analytics**
   - Analytics data loading
   - Chart rendering
   - Growth metrics

6. **Services Management**
   - Service list
   - Status indicators
   - Service actions

7. **System Monitoring**
   - System metrics
   - Network stats
   - GPU monitoring

8. **Subscription Management**
   - Usage data
   - Usage charts
   - Period filters
   - Plan information

### Cross-Functional Tests

- Page loading performance
- Navigation flow
- API response times
- Memory leak detection

---

## Configuration

### Playwright Config

The `playwright.config.js` file includes:

- **Base URL**: Configurable via `BASE_URL` env var
- **Browsers**: Chromium, Firefox, WebKit
- **Reporters**: HTML, JSON, JUnit, List
- **Screenshots**: On failure only
- **Videos**: On failure only
- **Trace**: On first retry

### Test Timeouts

- **Test timeout**: 60 seconds
- **Expect timeout**: 10 seconds
- **Navigation timeout**: 30 seconds

### Environment Variables

```bash
# .env.test
BASE_URL=https://unicorncommander.ai
TEST_USERNAME=admin
TEST_PASSWORD=your-admin-password
PLAYWRIGHT_WORKERS=1
PLAYWRIGHT_TIMEOUT=60000
```

---

## Troubleshooting

### Common Issues

#### 1. "Executable doesn't exist" Error

**Problem**: Playwright browsers not installed

**Solution**:
```bash
npx playwright install chromium
```

#### 2. Timeout Errors

**Problem**: Tests timing out waiting for pages/elements

**Solution**:
```bash
# Increase timeout in playwright.config.js
timeout: 120 * 1000  # 2 minutes

# Or use headed mode to see what's happening
npx playwright test --headed
```

#### 3. Authentication Failures

**Problem**: Can't login via Keycloak

**Solution**:
```bash
# Verify credentials in .env.test
cat .env.test

# Test login manually in browser
open https://unicorncommander.ai

# Check Keycloak is accessible
curl -I https://auth.unicorncommander.ai
```

#### 4. SSL Certificate Errors

**Problem**: HTTPS errors on self-signed certificates

**Solution**:
Already handled in `playwright.config.js`:
```javascript
use: {
  ignoreHTTPSErrors: true
}
```

#### 5. Tests Pass Locally but Fail in CI

**Problem**: Environment differences

**Solution**:
```bash
# Run in CI mode locally
CI=true npx playwright test

# Check for hardcoded paths or URLs
grep -r "localhost" tests/

# Use environment variables instead
BASE_URL=${BASE_URL:-https://unicorncommander.ai}
```

### Debug Commands

```bash
# Show Playwright info
npx playwright --version
npx playwright show-trace trace.zip

# List installed browsers
npx playwright install --dry-run

# Check system requirements
npx playwright install-deps --dry-run

# Clear test artifacts
rm -rf test-results/

# Clear Playwright cache
rm -rf ~/.cache/ms-playwright/
npx playwright install chromium
```

---

## Mac Studio Specific Tips

### 1. Performance Optimization

Mac Studio has excellent performance, but you can optimize further:

```bash
# Use all CPU cores (default is 1 for E2E)
npx playwright test --workers=2

# Increase timeout for slower tests
PLAYWRIGHT_TIMEOUT=90000 npx playwright test
```

### 2. Screen Recording

Mac Studio can handle video recording without performance impact:

```javascript
// In playwright.config.js
use: {
  video: 'on'  // Record all tests
}
```

### 3. GPU Acceleration

Ensure Chrome uses GPU acceleration:

```bash
# Check GPU is available
system_profiler SPDisplaysDataType

# Chrome should use Metal API on Mac
```

### 4. Headless vs Headed

Mac Studio can run headed mode smoothly:

```bash
# Headed mode for debugging
npx playwright test --headed

# Headless for speed
npx playwright test
```

---

## CI/CD Integration

### GitHub Actions

See `.github/workflows/e2e-tests.yml` for CI/CD configuration.

### Running in CI

```bash
# Set CI environment variable
export CI=true

# Run tests with CI-specific config
npx playwright test --config=playwright.config.js

# Upload artifacts
npx playwright test --reporter=html,junit
```

### Test Reports

Reports are generated in:
- **HTML**: `test-results/playwright-report/index.html`
- **JSON**: `test-results/results.json`
- **JUnit**: `test-results/junit.xml`

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```javascript
test.beforeEach(async ({ page }) => {
  // Fresh login for each test
  await loginViaKeycloak(page);
});
```

### 2. Selector Strategy

Use stable selectors:

```javascript
// ✅ Good - data-testid
page.locator('[data-testid="user-menu"]')

// ✅ Good - ARIA labels
page.locator('[aria-label="User menu"]')

// ❌ Avoid - text content (can change)
page.locator('text=Click here')

// ❌ Avoid - CSS classes (can change)
page.locator('.btn-primary')
```

### 3. Wait Strategies

Use proper wait strategies:

```javascript
// ✅ Wait for network idle
await page.waitForLoadState('networkidle');

// ✅ Wait for specific API call
await page.waitForResponse(resp => resp.url().includes('/api/users'));

// ❌ Avoid - arbitrary timeouts
await page.waitForTimeout(5000);
```

### 4. Error Handling

Capture useful debug info on failure:

```javascript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== testInfo.expectedStatus) {
    // Screenshot
    await page.screenshot({ path: 'screenshot.png', fullPage: true });

    // Console logs
    const logs = await page.evaluate(() => console.logs);

    // Network requests
    const requests = await page.context().requests();
  }
});
```

---

## Test Development Workflow

### 1. Record a New Test

```bash
# Use Playwright codegen to record actions
npx playwright codegen https://unicorncommander.ai

# This opens browser and generates test code
```

### 2. Develop Test

```bash
# Run in UI mode for interactive development
npx playwright test --ui

# See live browser and step through tests
npx playwright test --debug
```

### 3. Debug Failing Test

```bash
# Run specific test in debug mode
npx playwright test -g "User Management" --debug

# Generate trace for analysis
npx playwright test --trace on
npx playwright show-trace trace.zip
```

### 4. Verify Test

```bash
# Run test multiple times
for i in {1..5}; do npx playwright test -g "Specific test"; done

# Run on all browsers
npx playwright test --project=chromium --project=firefox --project=webkit
```

---

## Resources

- **Playwright Docs**: https://playwright.dev/docs/intro
- **Playwright VS Code Extension**: https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright
- **Axe Core**: https://github.com/dequelabs/axe-core
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

---

## Support

For issues or questions:

1. **Check test output**: `npx playwright show-report`
2. **Review logs**: `cat test-results/results.json`
3. **Debug interactively**: `npx playwright test --debug`
4. **Check Ops-Center logs**: `docker logs ops-center-direct`

---

**Last Updated**: October 26, 2025
**Test Suite Version**: 1.0.0
**Playwright Version**: ^1.40.1
