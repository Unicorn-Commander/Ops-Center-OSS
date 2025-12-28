/**
 * Authentication Helper for Playwright E2E Tests
 *
 * Handles Keycloak SSO login flow for Ops-Center testing
 */

/**
 * Login via Keycloak SSO
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Username or email
 * @param {string} credentials.password - Password
 * @returns {Promise<void>}
 */
export async function loginViaKeycloak(page, credentials = {}) {
  const username = credentials.username || process.env.TEST_USERNAME || 'aaron';
  const password = credentials.password || process.env.TEST_PASSWORD || 'test-password-placeholder';

  console.log(`[Auth] Logging in as: ${username}`);

  // Navigate to Ops-Center
  await page.goto('/');

  // Check if already logged in
  const isLoggedIn = await page.locator('[data-testid="user-menu"]').count() > 0;
  if (isLoggedIn) {
    console.log('[Auth] Already logged in, skipping login');
    return;
  }

  // Click login button or navigate to login
  const loginButton = page.locator('button:has-text("Login"), a:has-text("Login"), a[href*="/auth/login"]').first();
  if (await loginButton.count() > 0) {
    await loginButton.click();
  } else {
    await page.goto('/auth/login');
  }

  // Wait for Keycloak login page
  const authDomain = process.env.AUTH_DOMAIN || 'localhost';
  await page.waitForURL(new RegExp(`${authDomain.replace('.', '\\.')}.*`), { timeout: 10000 });

  // Fill in credentials
  await page.fill('input[name="username"], input[id="username"]', username);
  await page.fill('input[name="password"], input[id="password"]', password);

  // Click login button
  await page.click('input[type="submit"], button[type="submit"], button:has-text("Sign In")');

  // Wait for redirect back to Ops-Center
  const appDomain = process.env.APP_DOMAIN || 'localhost';
  await page.waitForURL(new RegExp(appDomain.replace('.', '\\.')), { timeout: 15000 });

  // Wait for user menu to appear (indicates successful login)
  await page.waitForSelector('[data-testid="user-menu"], .user-menu, [aria-label*="user menu"]', {
    timeout: 10000,
  });

  console.log('[Auth] Login successful');
}

/**
 * Logout from Ops-Center
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<void>}
 */
export async function logout(page) {
  console.log('[Auth] Logging out');

  // Click user menu
  await page.click('[data-testid="user-menu"], .user-menu, [aria-label*="user menu"]');

  // Click logout button
  await page.click('button:has-text("Logout"), a:has-text("Logout"), [data-testid="logout-button"]');

  // Wait for redirect to login page or home
  await page.waitForURL(/\/(login|auth\/login)?$/, { timeout: 10000 });

  console.log('[Auth] Logout successful');
}

/**
 * Check if user is logged in
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<boolean>}
 */
export async function isLoggedIn(page) {
  const userMenuCount = await page.locator('[data-testid="user-menu"], .user-menu').count();
  return userMenuCount > 0;
}

/**
 * Get authentication state for reuse
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<Object>}
 */
export async function getAuthState(page) {
  return await page.context().storageState();
}

/**
 * Login and save authentication state to file
 * This can be used to speed up tests by reusing auth state
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} statePath - Path to save auth state
 * @param {Object} credentials - Login credentials
 * @returns {Promise<void>}
 */
export async function loginAndSaveState(page, statePath, credentials = {}) {
  await loginViaKeycloak(page, credentials);

  // Save signed-in state
  await page.context().storageState({ path: statePath });

  console.log(`[Auth] Auth state saved to: ${statePath}`);
}
