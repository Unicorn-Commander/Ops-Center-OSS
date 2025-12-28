# Mobile Responsiveness Test Suite

**Epic**: 2.7 - Mobile Responsiveness
**Created**: October 24, 2025
**Status**: ✅ Production Ready

---

## Overview

This directory contains comprehensive automated tests for mobile responsiveness, accessibility, and performance of the Ops-Center application.

**Total Tests**: 135+ automated tests

- **mobile-responsiveness.test.js** - 80 tests (viewports, layout, touch targets, tables, forms, navigation)
- **mobile-accessibility.test.js** - 30 tests (WCAG compliance, screen readers, zoom support)
- **mobile-performance.test.js** - 25 tests (load times, Web Vitals, touch response, scroll performance)

---

## Quick Start

### Installation

```bash
# Install dependencies
cd /home/muut/Production/UC-Cloud/services/ops-center
npm install playwright @axe-core/playwright lighthouse

# Install Playwright browsers
npx playwright install --with-deps chromium
```

### Running Tests

```bash
# Run all mobile tests
npx playwright test tests/mobile/

# Run specific test suite
npx playwright test tests/mobile/mobile-responsiveness.test.js
npx playwright test tests/mobile/mobile-accessibility.test.js
npx playwright test tests/mobile/mobile-performance.test.js

# Run tests with UI (debug mode)
npx playwright test tests/mobile/ --ui

# Run specific device tests
npx playwright test -g "iPhone SE"
npx playwright test -g "iPad Mini"

# Generate HTML report
npx playwright test tests/mobile/ --reporter=html
npx playwright show-report
```

---

## Test Suites

### 1. Mobile Responsiveness Tests (80 tests)

**File**: `mobile-responsiveness.test.js` (1,237 lines)

Tests mobile-specific rendering and layout issues across 6 device viewports.

**Test Categories**:
- ✅ **Viewport Tests** (15 tests) - 6 devices x 2 pages + landscape
- ✅ **Layout Tests** (20 tests) - Grid collapse, stacking, responsive elements
- ✅ **Touch Target Tests** (15 tests) - Apple HIG compliance (44x44px)
- ✅ **Table Tests** (10 tests) - Responsive data display
- ✅ **Form Tests** (12 tests) - Input optimization, zoom prevention
- ✅ **Navigation Tests** (8 tests) - Mobile menu, breadcrumbs

**Devices Tested**:
- iPhone SE (375x667)
- iPhone 12 Pro (390x844)
- iPhone 12 Pro Max (428x926)
- Samsung Galaxy S21 (360x800)
- iPad Mini (768x1024)
- iPad Pro (1024x1366)

**Example**:
```bash
npx playwright test tests/mobile/mobile-responsiveness.test.js
```

---

### 2. Mobile Accessibility Tests (30 tests)

**File**: `mobile-accessibility.test.js` (794 lines)

Tests WCAG 2.1 AA compliance and mobile-specific accessibility requirements.

**Test Categories**:
- ✅ **Touch Target Accessibility** (5 tests) - 44x44px minimum, spacing
- ✅ **Font Size Accessibility** (3 tests) - 16px inputs (iOS zoom prevention)
- ✅ **Color Contrast** (3 tests) - WCAG AA 4.5:1 ratio, focus states
- ✅ **Screen Reader** (6 tests) - Alt text, labels, ARIA, headings
- ✅ **Zoom & Scaling** (3 tests) - 200% zoom support, user scaling
- ✅ **Orientation** (3 tests) - Landscape mode, form usability
- ✅ **Keyboard Navigation** (3 tests) - Tab order, skip links
- ✅ **Motion & Animation** (2 tests) - Reduced motion, no auto-play

**Standards Compliance**:
- WCAG 2.1 Level AA
- Apple Human Interface Guidelines
- Material Design Accessibility
- Section 508

**Example**:
```bash
npx playwright test tests/mobile/mobile-accessibility.test.js
```

---

### 3. Mobile Performance Tests (25 tests)

**File**: `mobile-performance.test.js` (679 lines)

Tests performance metrics on mobile devices with network throttling.

**Test Categories**:
- ✅ **Page Load Performance** (5 tests) - Fast 3G, Slow 3G, Fast 4G
- ✅ **Web Vitals** (5 tests) - FCP, LCP, CLS, TTI, FID
- ✅ **Touch Response** (3 tests) - < 100ms response time, no 300ms delay
- ✅ **Scroll Performance** (3 tests) - 60fps, virtualization, infinite scroll
- ✅ **Resource Loading** (5 tests) - JS/CSS bundle sizes, images, fonts
- ✅ **Memory Performance** (2 tests) - Reasonable limits, no leaks
- ✅ **Lighthouse Audit** (1 test) - Mobile score > 80 (optional)

**Network Conditions**:
- **Fast 3G**: 1.6 Mbps down, 750 Kbps up, 150ms latency
- **Slow 3G**: 400 Kbps down, 400 Kbps up, 400ms latency
- **Fast 4G**: 4 Mbps down, 3 Mbps up, 20ms latency

**Performance Targets**:
- Page Load (Fast 3G): < 3 seconds
- First Contentful Paint (FCP): < 2 seconds
- Largest Contentful Paint (LCP): < 2.5 seconds
- Cumulative Layout Shift (CLS): < 0.1
- Time to Interactive (TTI): < 5 seconds
- First Input Delay (FID): < 100ms

**Example**:
```bash
npx playwright test tests/mobile/mobile-performance.test.js
```

---

## Configuration

### Environment Variables

```bash
# Set base URL (default: http://localhost:8084)
export TEST_BASE_URL=http://localhost:8084

# Or pass via command line
TEST_BASE_URL=https://your-domain.com npx playwright test tests/mobile/
```

### Playwright Configuration

Create `playwright.config.js` in the project root:

```javascript
module.exports = {
  testDir: './tests/mobile',
  timeout: 30000,
  retries: 1,
  use: {
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
};
```

---

## Test Execution

### Pre-requisites

Before running tests:

1. **Ops-Center Running**:
   ```bash
   docker ps | grep ops-center-direct
   # Should show running container
   ```

2. **Test Data Available**:
   - Keycloak has test users (minimum 10)
   - Sample subscriptions exist
   - Sample organizations created

3. **Network Stable**:
   - Good internet connection for performance tests
   - No VPN (can affect network throttling)

### Running Tests

**All Tests**:
```bash
npx playwright test tests/mobile/
```

**Specific Suite**:
```bash
npx playwright test tests/mobile/mobile-responsiveness.test.js
```

**Specific Test**:
```bash
npx playwright test -g "iPhone SE - No horizontal scrolling"
```

**With UI (Debug)**:
```bash
npx playwright test tests/mobile/ --ui
```

**Debug Specific Test**:
```bash
npx playwright test --debug -g "touch targets"
```

### Viewing Results

**HTML Report**:
```bash
npx playwright show-report
```

**CI Mode**:
```bash
npx playwright test --reporter=line
```

---

## Troubleshooting

### Common Issues

**1. Tests Fail: "Page not found"**
```
Error: net::ERR_CONNECTION_REFUSED at http://localhost:8084
```

**Fix**: Ensure Ops-Center is running
```bash
docker ps | grep ops-center-direct
# If not running:
docker restart ops-center-direct
```

---

**2. Tests Fail: "Timeout waiting for element"**
```
Error: Timeout 30000ms exceeded waiting for selector "button"
```

**Fix**: Increase timeout or check if element selector changed
```javascript
test.setTimeout(60000); // Increase to 60 seconds
```

Or use Playwright Inspector:
```bash
npx playwright test --debug -g "failing test name"
```

---

**3. Accessibility Tests Fail: "axe violations"**
```
Error: Expected 0 contrast violations, found 3
```

**Fix**: Review violations and update styles
- Check color contrast ratios
- Ensure text meets WCAG AA (4.5:1)
- Use contrast checker: https://webaim.org/resources/contrastchecker/

---

**4. Performance Tests Fail: "Load time exceeded"**
```
Error: Expected load time < 3000ms, got 4523ms
```

**Possible Causes**:
- Network throttling too aggressive
- Server performance issue
- Large bundle sizes

**Fix**:
- Test on real device to verify
- Profile with Chrome DevTools
- Optimize assets if needed

---

**5. Browser Installation Issues**
```
Error: Executable doesn't exist at /path/to/chromium
```

**Fix**: Install Playwright browsers
```bash
npx playwright install --with-deps chromium
```

---

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/mobile-tests.yml`:

```yaml
name: Mobile Responsiveness Tests

on: [push, pull_request]

jobs:
  mobile-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd services/ops-center
          npm install

      - name: Install Playwright
        run: npx playwright install --with-deps chromium

      - name: Start Ops-Center
        run: |
          docker compose up -d ops-center-direct
          sleep 10

      - name: Run mobile tests
        run: npx playwright test tests/mobile/

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: mobile-test-results
          path: playwright-report/
```

---

## Documentation

### Related Documents

- **Mobile Testing Guide**: `/docs/MOBILE_TESTING_GUIDE.md` (1,449 lines)
  - Comprehensive manual testing procedures
  - Device matrix (20+ devices)
  - 100+ manual testing checklist items
  - Common issues & fixes
  - Screenshot guidelines

- **Delivery Report**: `/MOBILE_TESTING_DELIVERY_REPORT.md` (846 lines)
  - Testing infrastructure overview
  - Test execution guide
  - Findings & recommendations
  - Success metrics

### External Resources

- **Playwright Docs**: https://playwright.dev/
- **axe-core**: https://github.com/dequelabs/axe-core
- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **Apple HIG**: https://developer.apple.com/design/human-interface-guidelines/
- **Material Design**: https://m3.material.io/

---

## Test Statistics

### Coverage

**Pages Tested**:
- Dashboard (/admin)
- User Management (/admin/system/users)
- User Detail (/admin/system/users/:id)
- Billing Dashboard (/admin/system/billing)
- Organization Settings (/admin/organization/settings)
- Services Management (/admin/services)
- LLM Management (/admin/llm)
- Account Settings (/admin/account/profile)
- Account Security (/admin/account/security)
- Account API Keys (/admin/account/api-keys)
- Subscription Pages (/admin/subscription/*)
- Organization Pages (/admin/organization/*)
- Email Settings (/admin/settings/email)

**Devices Covered**:
- 6 devices automated (iPhone SE, 12 Pro, 12 Pro Max, Galaxy S21, iPad Mini, iPad Pro)
- 20+ devices manual testing (via BrowserStack or physical)

**Browsers Covered**:
- Chrome (automated + manual)
- Safari (manual on iOS)
- Firefox (manual)
- Edge (manual)
- Samsung Internet (manual on Android)

---

## Support

### Questions or Issues

**For test failures**:
1. Check this README troubleshooting section
2. Review test output for specific error
3. Use `--debug` flag to step through test
4. Check `/docs/MOBILE_TESTING_GUIDE.md` for solutions

**For new tests**:
1. Follow existing test patterns
2. Use descriptive test names
3. Add to appropriate test category
4. Update this README if needed

**For reporting bugs found**:
1. Use bug template in Mobile Testing Guide
2. Include device, browser, viewport
3. Attach screenshots
4. Provide console errors

---

## Changelog

**v1.0 - October 24, 2025**
- Initial mobile test suite created
- 135 automated tests (responsiveness, accessibility, performance)
- 6 device viewports covered
- WCAG 2.1 AA compliance testing
- Core Web Vitals performance testing

---

**Maintained By**: Mobile Testing Lead
**Last Updated**: October 24, 2025
