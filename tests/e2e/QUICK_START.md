# E2E Tests - Quick Start Guide

Get started with Ops-Center E2E testing in 5 minutes on Mac Studio.

## 🚀 Quick Setup

### 1. Install Playwright (One-Time Setup)

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Install Playwright browsers
npm run playwright:install

# Install system dependencies
npm run playwright:install:deps
```

### 2. Configure Environment

Create `.env.test` file:

```bash
cat > .env.test << 'EOF'
BASE_URL=https://your-domain.com
TEST_USERNAME=aaron
TEST_PASSWORD=your-admin-password
EOF
```

## ▶️ Run Tests

### Basic Commands

```bash
# Run all E2E tests
npm run test:e2e

# Run with interactive UI (recommended)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug
```

### Browser-Specific Tests

```bash
# Chrome/Chromium (fastest, recommended)
npm run test:e2e:chromium

# Firefox
npm run test:e2e:firefox

# Safari/WebKit
npm run test:e2e:webkit
```

### Accessibility Tests

```bash
# Run only accessibility tests
npm run test:e2e:accessibility
```

## 📊 View Results

```bash
# Open HTML report
npm run test:e2e:report

# Or manually
open test-results/playwright-report/index.html
```

## 🎯 Run Specific Tests

```bash
# Run User Management tests only
npx playwright test -g "User Management"

# Run Billing tests only
npx playwright test -g "Billing"

# Run single test
npx playwright test -g "Sidebar collapse keyboard navigation"
```

## 🐛 Debugging Failed Tests

```bash
# Run specific test in debug mode
npx playwright test -g "User Management page loads" --debug

# View trace for failed test
npx playwright show-trace test-results/trace.zip
```

## 📝 Test Coverage

The test suite covers:

✅ **Accessibility** - WCAG 2.1 compliance, keyboard navigation
✅ **User Management** - CRUD, filtering, bulk operations
✅ **Billing** - Dashboard, charts, plans
✅ **Security** - Audit logs, activity timeline
✅ **Analytics** - Metrics, charts, data accuracy
✅ **Services** - Status, management, actions
✅ **Monitoring** - System metrics, network, GPU
✅ **Subscriptions** - Usage, plans, billing

## 🔧 Troubleshooting

### Tests fail with timeout

```bash
# Increase timeout in playwright.config.js
timeout: 120 * 1000  # 2 minutes
```

### Can't login

```bash
# Verify credentials
cat .env.test

# Test manually in browser
open https://your-domain.com
```

### Browser not found

```bash
# Reinstall browsers
npm run playwright:install
```

## 📚 Full Documentation

See `README.md` in this directory for complete documentation.

## 🎓 Learn More

- **Playwright Docs**: https://playwright.dev/docs/intro
- **Test File**: `ops-center.spec.js` (60+ tests)
- **Helper Functions**: `helpers/` directory

---

**Last Updated**: October 26, 2025
**Ready to test!** 🎉
