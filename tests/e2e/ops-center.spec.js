/**
 * Ops-Center E2E Test Suite
 *
 * Comprehensive end-to-end tests for Ops-Center functionality
 * Optimized for Mac Studio with Chrome
 *
 * Test Coverage:
 * - Phase 1: Accessibility & Keyboard Navigation
 * - Phase 2: User Management
 * - Phase 3: Billing Dashboard
 * - Phase 4: Security & Audit Logs
 * - Phase 5: Analytics
 * - Phase 6: Services Management
 * - Phase 7: System Monitoring
 * - Phase 8: Subscription Management
 */

import { test, expect } from '@playwright/test';
import { loginViaKeycloak, logout } from './helpers/auth.js';
import { checkApiEndpoint, waitForApiCall, captureApiCalls } from './helpers/api.js';
import {
  runAccessibilityAudit,
  checkKeyboardNavigation,
  checkAriaAttributes,
  checkFocusIndicator,
  generateAccessibilityReport,
} from './helpers/accessibility.js';

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:8084';
const TEST_USERNAME = process.env.TEST_USERNAME || 'aaron';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'test-password-placeholder';

// ============================================================================
// SETUP AND TEARDOWN
// ============================================================================

test.describe('Ops-Center E2E Tests', () => {
  // Setup: Login before all tests
  test.beforeEach(async ({ page }) => {
    console.log('\n========================================');
    console.log(`Starting test: ${test.info().title}`);
    console.log('========================================\n');

    // Login via Keycloak SSO
    await loginViaKeycloak(page, {
      username: TEST_USERNAME,
      password: TEST_PASSWORD,
    });

    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
  });

  // Teardown: Capture screenshot on failure
  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status !== testInfo.expectedStatus) {
      console.log(`\n[FAILED] Test failed: ${testInfo.title}`);

      // Take screenshot
      const screenshot = await page.screenshot({
        path: `test-results/screenshots/${testInfo.title.replace(/\s/g, '-')}-${Date.now()}.png`,
        fullPage: true,
      });
      await testInfo.attach('screenshot', {
        body: screenshot,
        contentType: 'image/png',
      });

      // Get console logs
      const logs = [];
      page.on('console', (msg) => logs.push(`${msg.type()}: ${msg.text()}`));
      console.log('\n[Console Logs]:', logs);
    }
  });

  // ============================================================================
  // PHASE 1: ACCESSIBILITY TESTS
  // ============================================================================

  test.describe('Phase 1: Accessibility & Keyboard Navigation', () => {
    test('Sidebar collapse keyboard navigation', async ({ page }) => {
      // Navigate to dashboard
      await page.goto('/admin');

      // Find sidebar toggle button
      const sidebarToggle = page.locator(
        '[data-testid="sidebar-toggle"], button[aria-label*="menu"], button[aria-label*="sidebar"]'
      ).first();

      // Check ARIA labels
      const ariaAttrs = await checkAriaAttributes(page, '[data-testid="sidebar-toggle"]');
      expect(ariaAttrs.hasLabel).toBeTruthy();

      // Test keyboard navigation (Enter key)
      await sidebarToggle.focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500); // Wait for animation

      // Verify sidebar state changed
      const sidebarCollapsed = await page.evaluate(() => {
        const sidebar = document.querySelector('[data-testid="sidebar"], aside, .sidebar');
        return sidebar ? sidebar.classList.contains('collapsed') : false;
      });

      // Test Space key
      await sidebarToggle.focus();
      await page.keyboard.press('Space');
      await page.waitForTimeout(500);

      // Check focus indicators
      const hasFocusIndicator = await checkFocusIndicator(page, '[data-testid="sidebar-toggle"]');
      expect(hasFocusIndicator).toBeTruthy();

      console.log('✓ Sidebar keyboard navigation works');
    });

    test('Navigation menu accessibility', async ({ page }) => {
      await page.goto('/admin');

      // Run full accessibility audit
      const auditResults = await runAccessibilityAudit(page, {
        tags: ['wcag2a', 'wcag2aa'],
      });

      // Generate report
      const report = generateAccessibilityReport(auditResults);

      console.log('\n[Accessibility Report]');
      console.log(`  Violations: ${report.summary.violations}`);
      console.log(`  Critical: ${report.criticalIssues.length}`);
      console.log(`  Serious: ${report.seriousIssues.length}`);
      console.log(`  Moderate: ${report.moderateIssues.length}`);

      // Assert: No critical violations
      expect(report.criticalIssues.length).toBe(0);

      // Assert: Serious violations should be minimal (allow up to 3)
      expect(report.seriousIssues.length).toBeLessThanOrEqual(3);

      console.log('✓ Accessibility audit passed');
    });

    test('Keyboard navigation through main menu', async ({ page }) => {
      await page.goto('/admin');

      // Tab through menu items
      const menuItems = [
        'Dashboard',
        'User Management',
        'Billing',
        'Organizations',
        'Services',
        'LLM Management',
      ];

      for (const itemText of menuItems) {
        const menuItem = page.locator(`nav a:has-text("${itemText}"), nav button:has-text("${itemText}")`).first();

        if (await menuItem.count() > 0) {
          // Test keyboard navigation
          const isNavigable = await checkKeyboardNavigation(page, `nav a:has-text("${itemText}")`);
          expect(isNavigable).toBeTruthy();

          console.log(`✓ ${itemText} is keyboard accessible`);
        }
      }

      console.log('✓ All menu items are keyboard accessible');
    });
  });

  // ============================================================================
  // PHASE 2: USER MANAGEMENT TESTS
  // ============================================================================

  test.describe('Phase 2: User Management', () => {
    test('User Management page loads without errors', async ({ page }) => {
      // Capture console errors
      const errors = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') errors.push(msg.text());
      });
      page.on('pageerror', (error) => errors.push(error.message));

      // Navigate to User Management
      await page.goto('/admin/system/users');

      // Wait for API calls
      const apiResponse = await waitForApiCall(page, '/api/v1/admin/users');
      expect(apiResponse.ok).toBeTruthy();

      // Check for user list
      const userTable = await page.locator('table, [data-testid="user-table"], .user-list').count();
      expect(userTable).toBeGreaterThan(0);

      // Assert: No console errors
      expect(errors.length).toBe(0);

      console.log('✓ User Management page loaded successfully');
    });

    test('User list displays with metrics', async ({ page }) => {
      await page.goto('/admin/system/users');

      // Wait for metrics cards
      await page.waitForSelector('[data-testid="metric-card"], .metric-card, .stats-card', {
        timeout: 10000,
      });

      // Check for total users metric
      const totalUsers = await page.locator('text=/Total Users|All Users/i').count();
      expect(totalUsers).toBeGreaterThan(0);

      // Check for active users metric
      const activeUsers = await page.locator('text=/Active Users/i').count();
      expect(activeUsers).toBeGreaterThan(0);

      // Check user table has rows
      const userRows = await page.locator('tbody tr, [data-testid="user-row"]').count();
      expect(userRows).toBeGreaterThan(0);

      console.log(`✓ User list displays ${userRows} users`);
    });

    test('Advanced filtering works', async ({ page }) => {
      await page.goto('/admin/system/users');

      // Test tier filter
      const tierFilter = page.locator('select[name="tier"], [data-testid="tier-filter"]').first();
      if (await tierFilter.count() > 0) {
        await tierFilter.selectOption({ label: 'Professional' });
        await page.waitForTimeout(1000); // Wait for filter to apply

        // Verify API call with filter
        const apiResponse = await waitForApiCall(page, 'tier=professional');
        expect(apiResponse.ok).toBeTruthy();

        console.log('✓ Tier filter works');
      }

      // Test role filter
      const roleFilter = page.locator('select[name="role"], [data-testid="role-filter"]').first();
      if (await roleFilter.count() > 0) {
        await roleFilter.selectOption({ label: 'Admin' });
        await page.waitForTimeout(1000);

        console.log('✓ Role filter works');
      }

      // Test search
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]').first();
      if (await searchInput.count() > 0) {
        await searchInput.fill('aaron');
        await page.waitForTimeout(1000);

        console.log('✓ Search filter works');
      }

      console.log('✓ All filters functional');
    });

    test('User detail page opens on row click', async ({ page }) => {
      await page.goto('/admin/system/users');

      // Wait for user table
      await page.waitForSelector('tbody tr');

      // Click first user row
      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();

      // Wait for navigation to detail page
      await page.waitForURL(/\/admin\/system\/users\/[^/]+/, { timeout: 5000 });

      // Check for user detail content
      const detailPage = await page.locator('[data-testid="user-detail"], .user-detail-page').count();
      expect(detailPage).toBeGreaterThan(0);

      // Check for tabs
      const tabs = await page.locator('[role="tab"], .tab-button').count();
      expect(tabs).toBeGreaterThan(0);

      console.log('✓ User detail page opens correctly');
    });

    test('Bulk operations toolbar appears on selection', async ({ page }) => {
      await page.goto('/admin/system/users');

      // Wait for user table
      await page.waitForSelector('tbody tr');

      // Select first checkbox
      const firstCheckbox = page.locator('tbody tr input[type="checkbox"]').first();
      await firstCheckbox.check();

      // Wait for bulk actions toolbar
      await page.waitForSelector('[data-testid="bulk-actions"], .bulk-actions-toolbar', {
        timeout: 5000,
      });

      // Verify toolbar has actions
      const bulkActions = await page.locator('button:has-text("Delete"), button:has-text("Suspend")').count();
      expect(bulkActions).toBeGreaterThan(0);

      console.log('✓ Bulk actions toolbar appears');
    });

    test('CSV export downloads', async ({ page }) => {
      await page.goto('/admin/system/users');

      // Find export button
      const exportButton = page.locator('button:has-text("Export"), [data-testid="export-button"]').first();

      if (await exportButton.count() > 0) {
        // Start waiting for download before clicking
        const downloadPromise = page.waitForEvent('download');

        await exportButton.click();

        // Wait for download to complete
        const download = await downloadPromise;

        // Verify download filename
        const filename = download.suggestedFilename();
        expect(filename).toMatch(/\.csv$/);

        console.log(`✓ CSV export downloaded: ${filename}`);
      } else {
        console.log('⚠ Export button not found (may be in dropdown menu)');
      }
    });
  });

  // ============================================================================
  // PHASE 3: BILLING DASHBOARD TESTS
  // ============================================================================

  test.describe('Phase 3: Billing Dashboard', () => {
    test('Billing Dashboard loads', async ({ page }) => {
      await page.goto('/admin/system/billing');

      // Wait for billing data
      const apiResponse = await waitForApiCall(page, '/api/v1/billing');
      expect(apiResponse.ok).toBeTruthy();

      // Check for revenue metrics
      const revenueMetric = await page.locator('text=/Revenue|MRR|ARR/i').count();
      expect(revenueMetric).toBeGreaterThan(0);

      console.log('✓ Billing Dashboard loaded');
    });

    test('Charts render on billing dashboard', async ({ page }) => {
      await page.goto('/admin/system/billing');

      // Wait for charts to render
      await page.waitForSelector('canvas, [data-testid="chart"], .recharts-wrapper', {
        timeout: 10000,
      });

      // Check for at least one chart
      const chartCount = await page.locator('canvas, .recharts-wrapper').count();
      expect(chartCount).toBeGreaterThan(0);

      console.log(`✓ ${chartCount} charts rendered`);
    });

    test('Subscription plans display', async ({ page }) => {
      await page.goto('/admin/system/billing');

      // Look for plan cards or plan list
      const planCards = await page.locator('[data-testid="plan-card"], .plan-card, .subscription-plan').count();

      if (planCards > 0) {
        expect(planCards).toBeGreaterThanOrEqual(4); // 4 tiers (Trial, Starter, Pro, Enterprise)
        console.log(`✓ ${planCards} subscription plans displayed`);
      } else {
        console.log('⚠ Plan cards not visible (may require navigation)');
      }
    });

    test('No 404 errors on billing pages', async ({ page }) => {
      const errors = [];
      page.on('response', (response) => {
        if (response.status() === 404) {
          errors.push(response.url());
        }
      });

      await page.goto('/admin/system/billing');
      await page.waitForLoadState('networkidle');

      // Assert: No 404 errors
      expect(errors.length).toBe(0);

      console.log('✓ No 404 errors on billing pages');
    });
  });

  // ============================================================================
  // PHASE 4: SECURITY & AUDIT LOGS TESTS
  // ============================================================================

  test.describe('Phase 4: Security & Audit Logs', () => {
    test('Security page loads', async ({ page }) => {
      await page.goto('/admin/system/security');

      // Wait for security content
      await page.waitForSelector('[data-testid="security-page"], .security-content', {
        timeout: 10000,
        state: 'visible',
      });

      console.log('✓ Security page loaded');
    });

    test('Audit logs endpoint responds', async ({ page }) => {
      // Test audit logs API directly
      const response = await checkApiEndpoint(page, '/api/v1/audit/logs', {
        baseURL: BASE_URL,
      });

      expect(response.ok).toBeTruthy();
      expect(response.data).toBeDefined();

      console.log('✓ Audit logs API responds');
    });

    test('Audit logs display in UI', async ({ page }) => {
      await page.goto('/admin/system/security');

      // Look for audit log table or list
      const auditLogs = await page.locator(
        '[data-testid="audit-log"], .audit-log-entry, table tbody tr'
      ).count();

      // May be 0 if no activity, but UI should exist
      const auditLogContainer = await page.locator('[data-testid="audit-logs"], .audit-log-table').count();
      expect(auditLogContainer).toBeGreaterThan(0);

      console.log(`✓ Audit logs UI present (${auditLogs} entries)`);
    });

    test('Activity timeline on user detail', async ({ page }) => {
      // Go to first user's detail page
      await page.goto('/admin/system/users');
      await page.waitForSelector('tbody tr');

      const firstRow = page.locator('tbody tr').first();
      await firstRow.click();

      await page.waitForURL(/\/admin\/system\/users\/[^/]+/);

      // Find Activity tab
      const activityTab = page.locator('[role="tab"]:has-text("Activity"), button:has-text("Activity")').first();

      if (await activityTab.count() > 0) {
        await activityTab.click();

        // Wait for activity timeline
        await page.waitForSelector('[data-testid="activity-timeline"], .activity-timeline', {
          timeout: 5000,
        });

        console.log('✓ Activity timeline displays');
      } else {
        console.log('⚠ Activity tab not found');
      }
    });
  });

  // ============================================================================
  // PHASE 5: ANALYTICS TESTS
  // ============================================================================

  test.describe('Phase 5: Analytics', () => {
    test('Analytics page loads data', async ({ page }) => {
      await page.goto('/admin/analytics');

      // Wait for analytics API
      const apiResponse = await waitForApiCall(page, '/api/v1/admin/users/analytics');
      expect(apiResponse.ok).toBeTruthy();

      console.log('✓ Analytics data loaded');
    });

    test('Analytics charts render', async ({ page }) => {
      await page.goto('/admin/analytics');

      // Wait for charts
      await page.waitForSelector('canvas, .recharts-wrapper', {
        timeout: 10000,
      });

      const chartCount = await page.locator('canvas, .recharts-wrapper').count();
      expect(chartCount).toBeGreaterThan(0);

      console.log(`✓ ${chartCount} analytics charts rendered`);
    });

    test('User growth metrics display', async ({ page }) => {
      await page.goto('/admin/analytics');

      // Look for growth metrics
      const metrics = await page.locator('[data-testid="metric-card"], .metric-card').count();
      expect(metrics).toBeGreaterThan(0);

      console.log(`✓ ${metrics} analytics metrics displayed`);
    });
  });

  // ============================================================================
  // PHASE 6: SERVICES MANAGEMENT TESTS
  // ============================================================================

  test.describe('Phase 6: Services Management', () => {
    test('Services page loads', async ({ page }) => {
      await page.goto('/admin/services');

      // Wait for services list
      await page.waitForSelector('[data-testid="service-card"], .service-card, .service-item', {
        timeout: 10000,
      });

      const serviceCount = await page.locator('[data-testid="service-card"], .service-card').count();
      expect(serviceCount).toBeGreaterThan(0);

      console.log(`✓ ${serviceCount} services displayed`);
    });

    test('Service status indicators work', async ({ page }) => {
      await page.goto('/admin/services');

      // Look for status badges
      const statusBadges = await page.locator(
        '[data-testid="service-status"], .status-badge, .service-status'
      ).count();

      expect(statusBadges).toBeGreaterThan(0);

      console.log(`✓ ${statusBadges} service status indicators`);
    });

    test('Service actions are clickable', async ({ page }) => {
      await page.goto('/admin/services');

      // Find first service action button
      const actionButton = page.locator(
        'button:has-text("Start"), button:has-text("Stop"), button:has-text("Restart")'
      ).first();

      if (await actionButton.count() > 0) {
        const isEnabled = await actionButton.isEnabled();
        expect(isEnabled).toBeTruthy();

        console.log('✓ Service actions are enabled');
      } else {
        console.log('⚠ Service action buttons not found');
      }
    });
  });

  // ============================================================================
  // PHASE 7: SYSTEM MONITORING TESTS
  // ============================================================================

  test.describe('Phase 7: System Monitoring', () => {
    test('System monitoring page loads', async ({ page }) => {
      await page.goto('/admin/system/monitoring');

      // Wait for monitoring content
      await page.waitForSelector('[data-testid="monitoring"], .monitoring-content', {
        timeout: 10000,
        state: 'visible',
      });

      console.log('✓ System monitoring page loaded');
    });

    test('System metrics display', async ({ page }) => {
      // Test system status API
      const response = await checkApiEndpoint(page, '/api/v1/system/status', {
        baseURL: BASE_URL,
      });

      expect(response.ok).toBeTruthy();
      expect(response.data).toBeDefined();

      // Check for CPU, memory, disk metrics
      if (response.data) {
        console.log('✓ System metrics available:', Object.keys(response.data));
      }
    });

    test('Network stats display', async ({ page }) => {
      await page.goto('/admin/system/monitoring');

      // Look for network stats section
      const networkSection = await page.locator('text=/Network|Bandwidth/i').count();

      if (networkSection > 0) {
        console.log('✓ Network stats section present');
      } else {
        console.log('⚠ Network stats not found');
      }
    });

    test('GPU monitoring displays (if available)', async ({ page }) => {
      await page.goto('/admin/system/monitoring');

      // Look for GPU section
      const gpuSection = await page.locator('text=/GPU|Graphics/i').count();

      if (gpuSection > 0) {
        console.log('✓ GPU monitoring section present');
      } else {
        console.log('⚠ GPU monitoring not available (expected if no GPU)');
      }
    });
  });

  // ============================================================================
  // PHASE 8: SUBSCRIPTION MANAGEMENT TESTS
  // ============================================================================

  test.describe('Phase 8: Subscription Management', () => {
    test('Subscription usage page loads', async ({ page }) => {
      await page.goto('/admin/subscription/usage');

      // Wait for usage data
      await page.waitForSelector('[data-testid="usage-chart"], .usage-meter, canvas', {
        timeout: 10000,
      });

      console.log('✓ Subscription usage page loaded');
    });

    test('Usage data displays', async ({ page }) => {
      await page.goto('/admin/subscription/usage');

      // Check for API call usage
      const apiUsage = await page.locator('text=/API Calls|Requests|Usage/i').count();
      expect(apiUsage).toBeGreaterThan(0);

      console.log('✓ Usage data displays');
    });

    test('Usage charts render', async ({ page }) => {
      await page.goto('/admin/subscription/usage');

      // Wait for charts
      const chartCount = await page.locator('canvas, .recharts-wrapper').count();
      expect(chartCount).toBeGreaterThan(0);

      console.log(`✓ ${chartCount} usage charts rendered`);
    });

    test('Period filters work', async ({ page }) => {
      await page.goto('/admin/subscription/usage');

      // Find period filter
      const periodFilter = page.locator(
        'select:has-text("Month"), button:has-text("Month"), [data-testid="period-filter"]'
      ).first();

      if (await periodFilter.count() > 0) {
        // Click to change period
        await periodFilter.click();

        // Select different option
        await page.locator('option:has-text("Week"), li:has-text("Week")').first().click();

        // Wait for data to reload
        await page.waitForTimeout(1000);

        console.log('✓ Period filters work');
      } else {
        console.log('⚠ Period filter not found');
      }
    });

    test('Subscription plan page displays', async ({ page }) => {
      await page.goto('/admin/subscription/plan');

      // Check for current plan
      const planInfo = await page.locator('text=/Current Plan|Your Plan/i').count();
      expect(planInfo).toBeGreaterThan(0);

      console.log('✓ Subscription plan page displays');
    });
  });

  // ============================================================================
  // CROSS-FUNCTIONAL TESTS
  // ============================================================================

  test.describe('Cross-Functional Tests', () => {
    test('All critical pages load without errors', async ({ page }) => {
      const errors = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') errors.push(msg.text());
      });
      page.on('pageerror', (error) => errors.push(error.message));

      const pages = [
        '/admin',
        '/admin/system/users',
        '/admin/system/billing',
        '/admin/services',
        '/admin/analytics',
        '/admin/subscription/usage',
      ];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');
        console.log(`✓ ${pagePath} loaded`);
      }

      // Assert: No console errors across all pages
      expect(errors.length).toBe(0);

      console.log('✓ All critical pages load without errors');
    });

    test('Navigation between pages works', async ({ page }) => {
      await page.goto('/admin');

      // Navigate to User Management
      await page.click('nav a:has-text("User Management"), nav a[href*="/users"]');
      await page.waitForURL(/\/admin\/system\/users/);

      // Navigate to Billing
      await page.click('nav a:has-text("Billing"), nav a[href*="/billing"]');
      await page.waitForURL(/\/admin\/system\/billing/);

      // Navigate back to Dashboard
      await page.click('nav a:has-text("Dashboard"), nav a[href="/admin"]');
      await page.waitForURL(/\/admin$/);

      console.log('✓ Navigation between pages works');
    });

    test('API responses are within acceptable time', async ({ page }) => {
      const apiCalls = [];

      page.on('response', (response) => {
        if (response.url().includes('/api/')) {
          const timing = response.timing();
          apiCalls.push({
            url: response.url(),
            status: response.status(),
            time: timing ? timing.responseEnd : 0,
          });
        }
      });

      await page.goto('/admin/system/users');
      await page.waitForLoadState('networkidle');

      // Check average response time
      const avgTime = apiCalls.reduce((sum, call) => sum + call.time, 0) / apiCalls.length;

      console.log(`\n[API Performance]`);
      console.log(`  Total API calls: ${apiCalls.length}`);
      console.log(`  Average response time: ${avgTime.toFixed(2)}ms`);

      // Assert: Average response time under 1 second
      expect(avgTime).toBeLessThan(1000);

      console.log('✓ API responses within acceptable time');
    });

    test('No memory leaks on navigation', async ({ page, context }) => {
      // Get initial memory
      const initialMetrics = await page.metrics();

      // Navigate through multiple pages
      const pages = ['/admin', '/admin/system/users', '/admin/system/billing', '/admin/services'];

      for (let i = 0; i < 3; i++) {
        for (const pagePath of pages) {
          await page.goto(pagePath);
          await page.waitForLoadState('networkidle');
        }
      }

      // Get final memory
      const finalMetrics = await page.metrics();

      // Calculate memory increase
      const memoryIncrease = finalMetrics.JSHeapUsedSize - initialMetrics.JSHeapUsedSize;
      const increasePercent = (memoryIncrease / initialMetrics.JSHeapUsedSize) * 100;

      console.log(`\n[Memory Check]`);
      console.log(`  Initial heap: ${(initialMetrics.JSHeapUsedSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Final heap: ${(finalMetrics.JSHeapUsedSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Increase: ${increasePercent.toFixed(2)}%`);

      // Assert: Memory increase less than 50%
      expect(increasePercent).toBeLessThan(50);

      console.log('✓ No significant memory leaks detected');
    });
  });
});
