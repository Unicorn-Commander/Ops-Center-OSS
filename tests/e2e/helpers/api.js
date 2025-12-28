/**
 * API Helper for Playwright E2E Tests
 *
 * Utilities for testing API endpoints and responses
 */

/**
 * Check if API endpoint returns successful response
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} endpoint - API endpoint path
 * @param {Object} options - Request options
 * @returns {Promise<Object>} Response data
 */
export async function checkApiEndpoint(page, endpoint, options = {}) {
  const method = options.method || 'GET';
  const baseURL = options.baseURL || 'https://your-domain.com';
  const url = `${baseURL}${endpoint}`;

  console.log(`[API] Testing ${method} ${endpoint}`);

  const response = await page.request[method.toLowerCase()](url, {
    data: options.data,
    headers: options.headers,
  });

  const status = response.status();
  const isSuccess = status >= 200 && status < 300;

  console.log(`[API] Response: ${status} ${isSuccess ? '✓' : '✗'}`);

  if (!isSuccess && options.expectSuccess !== false) {
    console.error(`[API] Failed: ${status} ${response.statusText()}`);
    const text = await response.text();
    console.error(`[API] Body: ${text.substring(0, 200)}`);
  }

  return {
    status,
    ok: isSuccess,
    data: isSuccess ? await response.json().catch(() => null) : null,
    text: await response.text(),
  };
}

/**
 * Wait for API call and capture response
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} urlPattern - URL pattern to match
 * @returns {Promise<Object>} Response object
 */
export async function waitForApiCall(page, urlPattern) {
  console.log(`[API] Waiting for call to: ${urlPattern}`);

  const response = await page.waitForResponse(
    (resp) => resp.url().includes(urlPattern) && resp.status() !== 304,
    { timeout: 15000 }
  );

  const status = response.status();
  const isSuccess = status >= 200 && status < 300;

  console.log(`[API] Captured ${response.url()} - ${status} ${isSuccess ? '✓' : '✗'}`);

  return {
    status,
    ok: isSuccess,
    url: response.url(),
    data: isSuccess ? await response.json().catch(() => null) : null,
  };
}

/**
 * Capture all API calls made during an action
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {Function} action - Action to perform
 * @returns {Promise<Array<Object>>} Array of captured API calls
 */
export async function captureApiCalls(page, action) {
  const apiCalls = [];

  // Listen for all responses
  const listener = (response) => {
    const url = response.url();
    // Only capture API calls (not static assets)
    if (url.includes('/api/') || url.includes('/auth/')) {
      apiCalls.push({
        url,
        status: response.status(),
        method: response.request().method(),
        timestamp: new Date(),
      });
    }
  };

  page.on('response', listener);

  try {
    await action();
  } finally {
    page.off('response', listener);
  }

  console.log(`[API] Captured ${apiCalls.length} API calls`);
  return apiCalls;
}

/**
 * Check for API errors in console
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<Array<string>>} Array of error messages
 */
export async function captureApiErrors(page) {
  const errors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('pageerror', (error) => {
    errors.push(error.message);
  });

  return errors;
}

/**
 * Test API endpoint with authentication
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Request options
 * @returns {Promise<Object>}
 */
export async function testAuthenticatedEndpoint(page, endpoint, options = {}) {
  // Get cookies from page context for authentication
  const cookies = await page.context().cookies();
  const authCookie = cookies.find((c) => c.name.includes('session') || c.name.includes('token'));

  const headers = {
    ...options.headers,
  };

  if (authCookie) {
    headers['Cookie'] = `${authCookie.name}=${authCookie.value}`;
  }

  return await checkApiEndpoint(page, endpoint, {
    ...options,
    headers,
  });
}
