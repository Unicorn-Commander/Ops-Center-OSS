import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Ops-Center E2E Tests
 *
 * This configuration is optimized for Mac Studio testing with Chrome.
 * It includes accessibility testing, screenshot capture, and proper test organization.
 *
 * Usage:
 *   npx playwright test                    # Run all tests
 *   npx playwright test --ui               # Run with UI mode
 *   npx playwright test --headed           # Run with browser visible
 *   npx playwright test --project=chromium # Run specific browser
 *   npx playwright show-report             # View HTML report
 */

export default defineConfig({
  // Test directory
  testDir: './tests/e2e',

  // Maximum time one test can run for
  timeout: 60 * 1000,

  // Maximum time expect() should wait for the condition to be met
  expect: {
    timeout: 10 * 1000,
  },

  // Run tests in files in parallel
  fullyParallel: false, // Sequential for E2E tests to avoid conflicts

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : 1, // Single worker for E2E tests

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'test-results/playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.BASE_URL || 'https://your-domain.com',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Take screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'retain-on-failure',

    // Browser context options
    viewport: { width: 1920, height: 1080 },

    // Emulate timezone
    timezoneId: 'America/Los_Angeles',

    // Emulate locale
    locale: 'en-US',

    // User agent
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',

    // Ignore HTTPS errors (useful for self-signed certificates in testing)
    ignoreHTTPSErrors: true,

    // Context options for network
    extraHTTPHeaders: {
      'Accept': 'application/json, text/plain, */*',
    },
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Mac Studio with Chrome
        launchOptions: {
          args: [
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
          ],
        },
      },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile viewports for responsive testing
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },

    // Accessibility testing project
    {
      name: 'accessibility',
      testMatch: /.*accessibility.*\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Folder for test artifacts such as screenshots, videos, traces, etc.
  outputDir: 'test-results/artifacts',

  // Run your local dev server before starting the tests
  // webServer: {
  //   command: 'npm run dev',
  //   port: 8084,
  //   timeout: 120 * 1000,
  //   reuseExistingServer: !process.env.CI,
  // },
});
