/**
 * Mobile Performance Test Suite
 * Epic 2.7: Mobile Responsiveness
 *
 * Tests performance metrics on mobile devices
 * - Page load time (< 3s on 3G)
 * - Time to Interactive (< 5s)
 * - First Contentful Paint (< 2s)
 * - Cumulative Layout Shift (< 0.1)
 * - Touch response time (< 100ms)
 * - Scroll performance (60fps)
 *
 * @author Mobile Testing Lead
 * @date October 24, 2025
 */

const { chromium } = require('playwright');

const runPlaywright = process.env.RUN_PLAYWRIGHT === 'true';
const suite = runPlaywright ? describe : describe.skip;
const lighthouse = require('lighthouse');
const { URL } = require('url');

const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:8084';
const TIMEOUT = 60000;

// Network throttling presets
const NETWORK_PRESETS = {
  FAST_3G: {
    offline: false,
    downloadThroughput: (1.6 * 1024 * 1024) / 8, // 1.6 Mbps
    uploadThroughput: (750 * 1024) / 8, // 750 Kbps
    latency: 150 // ms
  },
  SLOW_3G: {
    offline: false,
    downloadThroughput: (400 * 1024) / 8, // 400 Kbps
    uploadThroughput: (400 * 1024) / 8, // 400 Kbps
    latency: 400 // ms
  },
  FAST_4G: {
    offline: false,
    downloadThroughput: (4 * 1024 * 1024) / 8, // 4 Mbps
    uploadThroughput: (3 * 1024 * 1024) / 8, // 3 Mbps
    latency: 20 // ms
  }
};

// Mobile device configurations
const MOBILE_DEVICE = { width: 390, height: 844 };

suite('Mobile Performance Test Suite', () => {
  let browser;
  let context;
  let page;

  beforeAll(async () => {
    browser = await chromium.launch({ headless: true });
  });

  afterAll(async () => {
    await browser.close();
  });

  beforeEach(async () => {
    context = await browser.newContext({
      viewport: MOBILE_DEVICE,
      deviceScaleFactor: 2
    });
    page = await context.newPage();
  });

  afterEach(async () => {
    await page.close();
    await context.close();
  });

  // =================================================================
  // PAGE LOAD PERFORMANCE TESTS
  // =================================================================

  describe('Page Load Performance', () => {
    test('Dashboard loads in < 3 seconds on Fast 3G', async () => {
      const cdpSession = await context.newCDPSession(page);
      await cdpSession.send('Network.emulateNetworkConditions', NETWORK_PRESETS.FAST_3G);

      const startTime = Date.now();
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      console.log(`Dashboard load time (Fast 3G): ${loadTime}ms`);
      expect(loadTime).toBeLessThan(3000);
    }, TIMEOUT);

    test('User Management page loads in < 4 seconds on Fast 3G', async () => {
      const cdpSession = await context.newCDPSession(page);
      await cdpSession.send('Network.emulateNetworkConditions', NETWORK_PRESETS.FAST_3G);

      const startTime = Date.now();
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      console.log(`User Management load time (Fast 3G): ${loadTime}ms`);
      expect(loadTime).toBeLessThan(4000);
    }, TIMEOUT);

    test('Account Settings page loads in < 3 seconds on Fast 4G', async () => {
      const cdpSession = await context.newCDPSession(page);
      await cdpSession.send('Network.emulateNetworkConditions', NETWORK_PRESETS.FAST_4G);

      const startTime = Date.now();
      await page.goto(`${BASE_URL}/admin/account/profile`, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      console.log(`Account Settings load time (Fast 4G): ${loadTime}ms`);
      expect(loadTime).toBeLessThan(3000);
    }, TIMEOUT);

    test('Initial page load (DOMContentLoaded) < 2 seconds on Fast 3G', async () => {
      const cdpSession = await context.newCDPSession(page);
      await cdpSession.send('Network.emulateNetworkConditions', NETWORK_PRESETS.FAST_3G);

      const performanceTiming = await page.evaluate(() => {
        return new Promise((resolve) => {
          window.addEventListener('DOMContentLoaded', () => {
            const timing = performance.timing;
            const loadTime = timing.domContentLoadedEventEnd - timing.navigationStart;
            resolve(loadTime);
          });
        });
      });

      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'domcontentloaded' });

      console.log(`DOMContentLoaded: ${performanceTiming}ms`);
      expect(performanceTiming).toBeLessThan(2000);
    }, TIMEOUT);

    test('Subsequent page loads use cache effectively', async () => {
      // First load
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      // Second load (should be faster due to cache)
      const startTime = Date.now();
      await page.reload({ waitUntil: 'networkidle' });
      const reloadTime = Date.now() - startTime;

      console.log(`Cached reload time: ${reloadTime}ms`);
      expect(reloadTime).toBeLessThan(1500);
    }, TIMEOUT);
  });

  // =================================================================
  // WEB VITALS TESTS (Core Web Vitals)
  // =================================================================

  describe('Web Vitals Performance', () => {
    test('First Contentful Paint (FCP) < 2 seconds', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'domcontentloaded' });

      const fcp = await page.evaluate(() => {
        return new Promise((resolve) => {
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const fcp = entries.find(entry => entry.name === 'first-contentful-paint');
            if (fcp) {
              resolve(fcp.startTime);
            }
          }).observe({ type: 'paint', buffered: true });
        });
      });

      console.log(`First Contentful Paint: ${Math.round(fcp)}ms`);
      expect(fcp).toBeLessThan(2000);
    }, TIMEOUT);

    test('Largest Contentful Paint (LCP) < 2.5 seconds', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const lcp = await page.evaluate(() => {
        return new Promise((resolve) => {
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            resolve(lastEntry.startTime);
          }).observe({ type: 'largest-contentful-paint', buffered: true });

          // Resolve after 5 seconds if no LCP
          setTimeout(() => resolve(5000), 5000);
        });
      });

      console.log(`Largest Contentful Paint: ${Math.round(lcp)}ms`);
      expect(lcp).toBeLessThan(2500);
    }, TIMEOUT);

    test('Cumulative Layout Shift (CLS) < 0.1', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      // Wait for page to settle
      await page.waitForTimeout(2000);

      const cls = await page.evaluate(() => {
        return new Promise((resolve) => {
          let clsValue = 0;

          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            }
            resolve(clsValue);
          }).observe({ type: 'layout-shift', buffered: true });

          // Resolve after collecting shifts
          setTimeout(() => resolve(clsValue), 1000);
        });
      });

      console.log(`Cumulative Layout Shift: ${cls.toFixed(3)}`);
      expect(cls).toBeLessThan(0.1);
    }, TIMEOUT);

    test('Time to Interactive (TTI) < 5 seconds', async () => {
      const startTime = Date.now();

      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'load' });

      // Wait until the page is interactive
      await page.waitForLoadState('networkidle');

      const tti = Date.now() - startTime;

      console.log(`Time to Interactive: ${tti}ms`);
      expect(tti).toBeLessThan(5000);
    }, TIMEOUT);

    test('First Input Delay (FID) simulation < 100ms', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      // Simulate user interaction
      const interactionTime = await page.evaluate(() => {
        return new Promise((resolve) => {
          const button = document.querySelector('button');
          if (!button) {
            resolve(0);
            return;
          }

          const startTime = performance.now();

          button.addEventListener('click', () => {
            const delay = performance.now() - startTime;
            resolve(delay);
          }, { once: true });

          // Simulate click
          button.click();
        });
      });

      console.log(`Simulated First Input Delay: ${Math.round(interactionTime)}ms`);
      expect(interactionTime).toBeLessThan(100);
    }, TIMEOUT);
  });

  // =================================================================
  // TOUCH RESPONSE PERFORMANCE
  // =================================================================

  describe('Touch Response Performance', () => {
    test('Touch events respond within 100ms', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const button = await page.$('button');
      if (button) {
        const responseTime = await button.evaluate((el) => {
          return new Promise((resolve) => {
            const startTime = performance.now();

            el.addEventListener('touchstart', () => {
              const delay = performance.now() - startTime;
              resolve(delay);
            }, { once: true, passive: true });

            // Simulate touch
            const touchEvent = new TouchEvent('touchstart', {
              bubbles: true,
              cancelable: true,
              touches: [{ clientX: 0, clientY: 0 }]
            });
            el.dispatchEvent(touchEvent);
          });
        });

        console.log(`Touch response time: ${Math.round(responseTime)}ms`);
        expect(responseTime).toBeLessThan(100);
      }
    }, TIMEOUT);

    test('Click events have no 300ms delay', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      // Check viewport meta tag prevents 300ms delay
      const viewportMeta = await page.$eval('meta[name="viewport"]', el => el.content);
      const hasProperViewport = viewportMeta.includes('width=device-width');

      expect(hasProperViewport).toBe(true);

      // Also check for touch-action CSS
      const hasTouchAction = await page.evaluate(() => {
        const style = window.getComputedStyle(document.body);
        return style.touchAction !== 'auto';
      });

      // At least one prevention method should be in place
      expect(hasProperViewport || hasTouchAction).toBe(true);
    }, TIMEOUT);

    test('Scroll starts within 16ms (60fps)', async () => {
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      const scrollResponse = await page.evaluate(() => {
        return new Promise((resolve) => {
          let scrollStarted = false;
          const startTime = performance.now();

          window.addEventListener('scroll', () => {
            if (!scrollStarted) {
              scrollStarted = true;
              const delay = performance.now() - startTime;
              resolve(delay);
            }
          }, { once: true, passive: true });

          // Trigger scroll
          window.scrollBy(0, 100);
        });
      });

      console.log(`Scroll response time: ${Math.round(scrollResponse)}ms`);
      expect(scrollResponse).toBeLessThan(16);
    }, TIMEOUT);
  });

  // =================================================================
  // SCROLL PERFORMANCE TESTS
  // =================================================================

  describe('Scroll Performance', () => {
    test('Scroll performance maintains 60fps', async () => {
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      const frameRates = await page.evaluate(() => {
        return new Promise((resolve) => {
          const frameRates = [];
          let lastTime = performance.now();
          let frameCount = 0;

          function measureFrame() {
            const currentTime = performance.now();
            const delta = currentTime - lastTime;
            const fps = 1000 / delta;

            frameRates.push(fps);
            lastTime = currentTime;
            frameCount++;

            if (frameCount < 60) {
              window.scrollBy(0, 10);
              requestAnimationFrame(measureFrame);
            } else {
              resolve(frameRates);
            }
          }

          // Start measuring
          requestAnimationFrame(measureFrame);
        });
      });

      const avgFps = frameRates.reduce((a, b) => a + b, 0) / frameRates.length;
      const minFps = Math.min(...frameRates);

      console.log(`Average FPS: ${Math.round(avgFps)}, Min FPS: ${Math.round(minFps)}`);

      // Allow some drops, but average should be near 60fps
      expect(avgFps).toBeGreaterThan(45);
      expect(minFps).toBeGreaterThan(30);
    }, TIMEOUT);

    test('Long lists use virtualization for performance', async () => {
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      // Check if only visible items are rendered
      const renderedItems = await page.evaluate(() => {
        const rows = document.querySelectorAll('table tbody tr, .user-card');
        return rows.length;
      });

      console.log(`Rendered items: ${renderedItems}`);

      // If there are many users, should use virtualization (render ~20-50 items max)
      expect(renderedItems).toBeLessThan(100);
    }, TIMEOUT);

    test('Infinite scroll loads smoothly', async () => {
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      // Scroll to bottom
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

      // Wait for potential lazy load
      await page.waitForTimeout(500);

      // Check if new content loaded
      const hasMoreContent = await page.evaluate(() => {
        const pagination = document.querySelector('.pagination, [aria-label*="pagination"]');
        return pagination !== null;
      });

      // Pagination or infinite scroll should be present
      expect(hasMoreContent).toBe(true);
    }, TIMEOUT);
  });

  // =================================================================
  // RESOURCE LOADING PERFORMANCE
  // =================================================================

  describe('Resource Loading Performance', () => {
    test('JavaScript bundle size < 500KB', async () => {
      const response = await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const resources = await page.evaluate(() => {
        return performance.getEntriesByType('resource')
          .filter(r => r.name.endsWith('.js'))
          .map(r => ({
            name: r.name.split('/').pop(),
            size: r.transferSize || r.encodedBodySize || 0
          }));
      });

      const totalJsSize = resources.reduce((sum, r) => sum + r.size, 0);

      console.log(`Total JavaScript size: ${Math.round(totalJsSize / 1024)}KB`);
      console.log('JS resources:', resources.slice(0, 5));

      expect(totalJsSize).toBeLessThan(500 * 1024);
    }, TIMEOUT);

    test('CSS bundle size < 200KB', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const cssResources = await page.evaluate(() => {
        return performance.getEntriesByType('resource')
          .filter(r => r.name.endsWith('.css'))
          .map(r => ({
            name: r.name.split('/').pop(),
            size: r.transferSize || r.encodedBodySize || 0
          }));
      });

      const totalCssSize = cssResources.reduce((sum, r) => sum + r.size, 0);

      console.log(`Total CSS size: ${Math.round(totalCssSize / 1024)}KB`);

      expect(totalCssSize).toBeLessThan(200 * 1024);
    }, TIMEOUT);

    test('Images are optimized and lazy-loaded', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const images = await page.$$eval('img', imgs => imgs.map(img => ({
        src: img.src.substring(0, 50),
        loading: img.loading,
        width: img.naturalWidth,
        height: img.naturalHeight
      })));

      // Check for lazy loading attribute
      const lazyImages = images.filter(img => img.loading === 'lazy');

      console.log(`Total images: ${images.length}, Lazy-loaded: ${lazyImages.length}`);

      // At least some images should be lazy-loaded
      if (images.length > 3) {
        expect(lazyImages.length).toBeGreaterThan(0);
      }
    }, TIMEOUT);

    test('Fonts load without blocking render', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'domcontentloaded' });

      const fontLoadTime = await page.evaluate(() => {
        return document.fonts.ready.then(() => performance.now());
      });

      console.log(`Font load time: ${Math.round(fontLoadTime)}ms`);

      // Fonts should load quickly and not block
      expect(fontLoadTime).toBeLessThan(3000);
    }, TIMEOUT);

    test('API calls are batched/debounced', async () => {
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      // Monitor network requests
      const apiCalls = [];
      page.on('request', request => {
        if (request.url().includes('/api/')) {
          apiCalls.push(request.url());
        }
      });

      // Type in search (should debounce)
      const searchInput = await page.$('input[type="search"]');
      if (searchInput) {
        await searchInput.type('test', { delay: 50 });

        // Wait for debounce
        await page.waitForTimeout(500);

        // Should not make API call for every keystroke
        expect(apiCalls.length).toBeLessThan(4);
      }
    }, TIMEOUT);
  });

  // =================================================================
  // MEMORY PERFORMANCE TESTS
  // =================================================================

  describe('Memory Performance', () => {
    test('Memory usage stays within reasonable limits', async () => {
      await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      // Navigate to heavy page
      await page.goto(`${BASE_URL}/admin/system/users`, { waitUntil: 'networkidle' });

      await page.waitForTimeout(1000);

      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      const memoryIncrease = finalMemory - initialMemory;

      console.log(`Memory increase: ${Math.round(memoryIncrease / 1024 / 1024)}MB`);

      // Memory increase should be reasonable (< 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    }, TIMEOUT);

    test('No memory leaks on page navigation', async () => {
      const measurements = [];

      for (let i = 0; i < 5; i++) {
        await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle' });

        const memory = await page.evaluate(() => {
          if (performance.memory) {
            return performance.memory.usedJSHeapSize;
          }
          return 0;
        });

        measurements.push(memory);
      }

      console.log('Memory measurements:', measurements.map(m => Math.round(m / 1024 / 1024) + 'MB'));

      // Memory should stabilize, not keep growing
      const lastTwo = measurements.slice(-2);
      const memoryGrowth = lastTwo[1] - lastTwo[0];

      expect(memoryGrowth).toBeLessThan(10 * 1024 * 1024); // < 10MB growth
    }, TIMEOUT);
  });

  // =================================================================
  // LIGHTHOUSE MOBILE AUDIT
  // =================================================================

  describe('Lighthouse Mobile Audit', () => {
    test.skip('Lighthouse mobile performance score > 80', async () => {
      // Note: This test requires lighthouse and is skipped by default
      // Run manually with: npx playwright test --grep "Lighthouse"

      const url = `${BASE_URL}/admin`;

      const runnerResult = await lighthouse(url, {
        port: new URL(browser.wsEndpoint()).port,
        output: 'json',
        onlyCategories: ['performance'],
        formFactor: 'mobile',
        throttling: {
          rttMs: 150,
          throughputKbps: 1638.4,
          cpuSlowdownMultiplier: 4
        },
        screenEmulation: {
          mobile: true,
          width: 390,
          height: 844,
          deviceScaleFactor: 2
        }
      });

      const score = runnerResult.lhr.categories.performance.score * 100;
      const metrics = runnerResult.lhr.audits;

      console.log(`Lighthouse Performance Score: ${Math.round(score)}/100`);
      console.log(`FCP: ${Math.round(metrics['first-contentful-paint'].numericValue)}ms`);
      console.log(`LCP: ${Math.round(metrics['largest-contentful-paint'].numericValue)}ms`);
      console.log(`TTI: ${Math.round(metrics['interactive'].numericValue)}ms`);
      console.log(`CLS: ${metrics['cumulative-layout-shift'].numericValue.toFixed(3)}`);

      expect(score).toBeGreaterThan(80);
    }, TIMEOUT);
  });
});

/**
 * Mobile Performance Test Summary
 * ================================
 *
 * Total Tests: 25+
 *
 * Performance Targets:
 * - Page Load (Fast 3G): < 3 seconds
 * - First Contentful Paint: < 2 seconds
 * - Largest Contentful Paint: < 2.5 seconds
 * - Cumulative Layout Shift: < 0.1
 * - Time to Interactive: < 5 seconds
 * - First Input Delay: < 100ms
 * - Scroll Performance: 60fps average
 * - Touch Response: < 100ms
 * - JS Bundle: < 500KB
 * - CSS Bundle: < 200KB
 * - Memory Usage: < 50MB increase
 * - Lighthouse Score: > 80/100
 *
 * Categories Tested:
 * 1. Page Load Performance (5 tests)
 * 2. Web Vitals (5 tests)
 * 3. Touch Response (3 tests)
 * 4. Scroll Performance (3 tests)
 * 5. Resource Loading (5 tests)
 * 6. Memory Performance (2 tests)
 * 7. Lighthouse Audit (1 test - optional)
 *
 * Network Conditions:
 * - Fast 3G: 1.6 Mbps down, 750 Kbps up, 150ms latency
 * - Slow 3G: 400 Kbps down, 400 Kbps up, 400ms latency
 * - Fast 4G: 4 Mbps down, 3 Mbps up, 20ms latency
 *
 * Tools Used:
 * - Playwright for automation
 * - Chrome DevTools Protocol for network throttling
 * - Performance API for web vitals
 * - Lighthouse for comprehensive audits
 *
 * Run Instructions:
 * -----------------
 * npm install playwright lighthouse
 * npx playwright test tests/mobile/mobile-performance.test.js
 *
 * For Lighthouse test:
 * npx playwright test --grep "Lighthouse"
 */
