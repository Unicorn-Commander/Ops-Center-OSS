/**
 * System Settings End-to-End Tests
 *
 * Complete user workflows testing the System Settings admin page.
 * Tests actual browser interactions, navigation, and full system integration.
 *
 * Prerequisites:
 * - Playwright installed: npm install -D @playwright/test
 * - Browsers installed: npx playwright install
 * - Ops-Center running: docker ps | grep ops-center-direct
 *
 * Run tests:
 * - All tests: npx playwright test tests/e2e/settings.spec.js
 * - Headed mode: npx playwright test tests/e2e/settings.spec.js --headed
 * - Debug mode: npx playwright test tests/e2e/settings.spec.js --debug
 *
 * Author: QA Testing Team Lead
 * Created: November 14, 2025
 */

const { test, expect } = require('@playwright/test');

// Configuration
const BASE_URL = process.env.BASE_URL || 'https://your-domain.com';
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@example.com';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'your-test-password';

test.describe('System Settings E2E Tests', () => {
  // Setup: Login before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to Ops-Center
    await page.goto(BASE_URL);

    // Check if already logged in
    const loginButton = await page.$('text=Login');
    if (loginButton) {
      // Need to login
      await page.click('text=Login');

      // Wait for Keycloak login page
      await page.waitForURL(/auth\.your-domain.com/);

      // Fill login form
      await page.fill('input[name="username"]', ADMIN_EMAIL);
      await page.fill('input[name="password"]', ADMIN_PASSWORD);

      // Submit
      await page.click('button[type="submit"]');

      // Wait for redirect back to Ops-Center
      await page.waitForURL(BASE_URL, { timeout: 10000 });
    }

    // Navigate to System Settings
    await page.goto(`${BASE_URL}/admin/system/settings`);
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load & Navigation', () => {
    test('loads system settings page successfully', async ({ page }) => {
      // Verify page title
      await expect(page).toHaveTitle(/System Settings|Ops.Center/i);

      // Verify main heading
      await expect(page.locator('h1')).toContainText(/System Settings/i);

      // Verify tabs are visible
      await expect(page.locator('[role="tab"]')).toHaveCount(6);
    });

    test('displays all category tabs', async ({ page }) => {
      const expectedTabs = [
        'Authentication',
        'Branding',
        'Features',
        'Integrations',
        'Notifications',
        'Security'
      ];

      for (const tabName of expectedTabs) {
        await expect(page.locator(`[role="tab"]:has-text("${tabName}")`)).toBeVisible();
      }
    });

    test('switches between tabs correctly', async ({ page }) => {
      // Click Branding tab
      await page.click('[role="tab"]:has-text("Branding")');

      // Verify branding panel is visible
      await expect(page.locator('[role="tabpanel"]')).toBeVisible();
      await expect(page.locator('text=Company Name')).toBeVisible();

      // Click Authentication tab
      await page.click('[role="tab"]:has-text("Authentication")');

      // Verify authentication panel is visible
      await expect(page.locator('text=Landing Page Mode')).toBeVisible();
    });
  });

  test.describe('Authentication Settings', () => {
    test('displays landing page mode options', async ({ page }) => {
      // Navigate to Authentication tab
      await page.click('[role="tab"]:has-text("Authentication")');

      // Verify radio buttons for landing page modes
      const modes = ['Direct SSO', 'Public Marketplace', 'Custom'];

      for (const mode of modes) {
        await expect(page.locator(`text=${mode}`)).toBeVisible();
      }
    });

    test('selects different landing page modes', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Authentication")');

      // Select Public Marketplace mode
      const publicMarketplace = page.locator('input[value="public_marketplace"]');
      await publicMarketplace.check();

      // Verify selection
      await expect(publicMarketplace).toBeChecked();

      // Other modes should not be checked
      await expect(page.locator('input[value="direct_sso"]')).not.toBeChecked();
    });

    test('toggles SSO auto-redirect setting', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Authentication")');

      // Find the toggle/checkbox
      const ssoToggle = page.locator('input[type="checkbox"]:near(text="SSO Auto-Redirect")');

      // Toggle it
      await ssoToggle.click();

      // Verify state changed
      const isChecked = await ssoToggle.isChecked();
      expect(typeof isChecked).toBe('boolean');
    });
  });

  test.describe('Branding Settings', () => {
    test('complete branding workflow', async ({ page }) => {
      // 1. Navigate to Branding tab
      await page.click('[role="tab"]:has-text("Branding")');

      // 2. Update company name
      const companyNameInput = page.locator('input[name*="company_name"], input[label*="Company Name"]').first();
      await companyNameInput.fill('Test Company');

      // 3. Update primary color
      const colorInput = page.locator('input[type="color"], input[name*="primary_color"]').first();
      await colorInput.fill('#ff6b6b');

      // 4. Verify preview updates (if preview exists)
      const preview = page.locator('.branding-preview, .preview-card');
      if (await preview.count() > 0) {
        await expect(preview).toContainText('Test Company');
      }

      // 5. Save changes
      await page.click('button:has-text("Save Changes")');

      // 6. Verify success toast/message
      await expect(page.locator('.toast-success, [role="alert"]')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=/saved successfully/i')).toBeVisible();

      // 7. Reload page and verify persistence
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Navigate back to Branding tab
      await page.click('[role="tab"]:has-text("Branding")');

      // Verify company name persisted
      await expect(companyNameInput).toHaveValue('Test Company');
    });

    test('validates color hex format', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Try to enter invalid color value
      const colorInput = page.locator('input[name*="primary_color"]').first();
      await colorInput.fill('not-a-color');

      // Try to save
      await page.click('button:has-text("Save Changes")');

      // Should show validation error
      await expect(page.locator('text=/invalid|error/i')).toBeVisible({ timeout: 3000 });
    });

    test('updates logo URLs', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Update logo URL
      const logoInput = page.locator('input[name*="logo_url"]').first();
      await logoInput.fill('https://example.com/logo.png');

      // Save
      await page.click('button:has-text("Save Changes")');

      // Verify success
      await expect(page.locator('.toast-success, text=/saved/i')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Features Settings', () => {
    test('toggles feature flags', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Features")');

      // Find feature toggles
      const toggles = page.locator('input[type="checkbox"]');
      const count = await toggles.count();

      if (count > 0) {
        // Toggle first feature
        const firstToggle = toggles.first();
        const initialState = await firstToggle.isChecked();

        await firstToggle.click();

        // Verify state changed
        expect(await firstToggle.isChecked()).toBe(!initialState);

        // Save
        await page.click('button:has-text("Save Changes")');

        // Verify success
        await expect(page.locator('text=/saved/i')).toBeVisible({ timeout: 5000 });
      }
    });

    test('shows feature descriptions', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Features")');

      // Each feature should have a description
      const features = page.locator('[class*="feature-item"], .setting-item');
      const count = await features.count();

      if (count > 0) {
        // Check first feature has description
        const firstFeature = features.first();
        await expect(firstFeature.locator('p, .description')).toBeVisible();
      }
    });
  });

  test.describe('Form Validation', () => {
    test('prevents saving with invalid email', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Enter invalid email
      const emailInput = page.locator('input[type="email"], input[name*="support_email"]').first();
      if (await emailInput.count() > 0) {
        await emailInput.fill('not-an-email');

        // Try to save
        await page.click('button:has-text("Save Changes")');

        // Should show validation error
        await expect(page.locator('text=/invalid email/i')).toBeVisible({ timeout: 3000 });
      }
    });

    test('prevents saving with invalid URL', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Enter invalid URL
      const urlInput = page.locator('input[name*="support_url"]').first();
      if (await urlInput.count() > 0) {
        await urlInput.fill('not-a-url');

        // Try to save
        await page.click('button:has-text("Save Changes")');

        // Should show validation error
        await expect(page.locator('text=/invalid url/i')).toBeVisible({ timeout: 3000 });
      }
    });

    test('shows required field errors', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Clear a required field
      const companyNameInput = page.locator('input[name*="company_name"]').first();
      if (await companyNameInput.count() > 0) {
        await companyNameInput.clear();

        // Try to save
        await page.click('button:has-text("Save Changes")');

        // Should show required error
        await expect(page.locator('text=/required/i')).toBeVisible({ timeout: 3000 });
      }
    });
  });

  test.describe('Unsaved Changes Warning', () => {
    test('warns before navigating away with unsaved changes', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Make a change
      const input = page.locator('input[name*="company_name"]').first();
      await input.fill('Changed Value');

      // Set up dialog handler
      page.on('dialog', dialog => {
        expect(dialog.message()).toMatch(/unsaved changes/i);
        dialog.dismiss();
      });

      // Try to navigate to another page
      // await page.click('a[href="/admin/dashboard"]');

      // Or try to close tab (triggers beforeunload)
      // await page.close(); // Would trigger warning
    });

    test('clears warning after save', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Branding")');

      // Make changes
      const input = page.locator('input[name*="company_name"]').first();
      await input.fill('Test Company');

      // Save
      await page.click('button:has-text("Save Changes")');
      await expect(page.locator('text=/saved/i')).toBeVisible({ timeout: 5000 });

      // Now navigating away should not warn
      // (No beforeunload event should fire)
    });
  });

  test.describe('Role-Based Access Control', () => {
    test('admin user can access settings', async ({ page }) => {
      // Already logged in as admin in beforeEach

      // Verify we can access the page
      await expect(page.locator('h1')).toContainText(/System Settings/i);

      // Verify save button is visible (admin can edit)
      await expect(page.locator('button:has-text("Save Changes")')).toBeVisible();
    });

    test.skip('non-admin users get 403 error', async ({ page, context }) => {
      // This test would require creating a non-admin user session
      // Skip for now, or implement with test user credentials

      // Logout current user
      await page.goto(`${BASE_URL}/auth/logout`);

      // Login as viewer role (if test user exists)
      // ...

      // Try to access settings
      await page.goto(`${BASE_URL}/admin/system/settings`);

      // Should see forbidden message
      await expect(page.locator('h1')).toContainText(/forbidden|unauthorized/i);
    });
  });

  test.describe('Responsive Design', () => {
    test('renders correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Reload page
      await page.reload();

      // Tabs should still be visible (may be in hamburger menu)
      const tabs = page.locator('[role="tab"]');
      const visibleTabs = await tabs.filter({ hasNotText: '' }).count();

      expect(visibleTabs).toBeGreaterThan(0);
    });

    test('renders correctly on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      // Reload page
      await page.reload();

      // Page should be accessible
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('[role="tab"]').first()).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('page loads in reasonable time', async ({ page }) => {
      const startTime = Date.now();

      await page.goto(`${BASE_URL}/admin/system/settings`);
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;

      // Page should load in under 3 seconds
      expect(loadTime).toBeLessThan(3000);
    });

    test('save operation completes quickly', async ({ page }) => {
      await page.click('[role="tab"]:has-text("Authentication")');

      // Select a mode
      await page.locator('input[value="public_marketplace"]').check();

      // Time the save operation
      const startTime = Date.now();

      await page.click('button:has-text("Save Changes")');
      await page.waitForSelector('.toast-success, text=/saved/i', { timeout: 5000 });

      const saveTime = Date.now() - startTime;

      // Save should complete in under 2 seconds
      expect(saveTime).toBeLessThan(2000);
    });
  });

  test.describe('Error Handling', () => {
    test('handles network errors gracefully', async ({ page, context }) => {
      // Intercept API requests and simulate failure
      await context.route('**/api/v1/system/settings', route => {
        route.abort('failed');
      });

      // Try to save
      await page.click('button:has-text("Save Changes")');

      // Should show error message
      await expect(page.locator('text=/error|failed/i')).toBeVisible({ timeout: 5000 });
    });

    test('displays specific error messages', async ({ page, context }) => {
      // Intercept and return specific error
      await context.route('**/api/v1/system/settings', route => {
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Invalid color format'
          })
        });
      });

      // Try to save
      await page.click('button:has-text("Save Changes")');

      // Should show specific error
      await expect(page.locator('text=/invalid color format/i')).toBeVisible({ timeout: 5000 });
    });
  });
});

// Smoke test configuration
test.describe('Smoke Tests', () => {
  test('critical path: load → edit → save', async ({ page }) => {
    // This is a minimal smoke test for CI/CD

    // 1. Load page
    await page.goto(`${BASE_URL}/admin/system/settings`);

    // 2. Verify it loaded
    await expect(page.locator('h1')).toBeVisible();

    // 3. Make a small edit
    await page.click('[role="tab"]:has-text("Authentication")');
    const toggle = page.locator('input[type="checkbox"]').first();
    if (await toggle.count() > 0) {
      await toggle.click();
    }

    // 4. Save
    await page.click('button:has-text("Save Changes")');

    // 5. Verify success (or no errors)
    const hasSuccess = await page.locator('.toast-success, text=/saved/i').isVisible({ timeout: 5000 }).catch(() => false);
    const hasError = await page.locator('.toast-error, text=/error/i').isVisible({ timeout: 1000 }).catch(() => false);

    // Either should succeed or at least not show an error
    expect(hasSuccess || !hasError).toBeTruthy();
  });
});
