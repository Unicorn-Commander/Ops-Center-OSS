/**
 * Accessibility Helper for Playwright E2E Tests
 *
 * Utilities for testing accessibility compliance (WCAG 2.1)
 */

import AxeBuilder from '@axe-core/playwright';

/**
 * Run accessibility audit on current page
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {Object} options - Axe options
 * @returns {Promise<Object>} Accessibility scan results
 */
export async function runAccessibilityAudit(page, options = {}) {
  console.log('[A11y] Running accessibility audit...');

  const axe = new AxeBuilder({ page })
    .withTags(options.tags || ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .exclude(options.exclude || []);

  if (options.include) {
    axe.include(options.include);
  }

  const results = await axe.analyze();

  const violationCount = results.violations.length;
  const incompleteCount = results.incomplete.length;

  console.log(`[A11y] Violations: ${violationCount}, Incomplete: ${incompleteCount}`);

  if (violationCount > 0) {
    console.log('[A11y] Violations found:');
    results.violations.forEach((violation, index) => {
      console.log(`  ${index + 1}. ${violation.id}: ${violation.description}`);
      console.log(`     Impact: ${violation.impact}, Nodes: ${violation.nodes.length}`);
    });
  }

  return results;
}

/**
 * Check for keyboard navigation support
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @returns {Promise<boolean>}
 */
export async function checkKeyboardNavigation(page, selector) {
  console.log(`[A11y] Checking keyboard navigation for: ${selector}`);

  const element = page.locator(selector).first();

  // Focus element with Tab key
  await element.focus();

  // Check if element is focused
  const isFocused = await element.evaluate((el) => el === document.activeElement);

  if (!isFocused) {
    console.log(`[A11y] ✗ Element not focusable: ${selector}`);
    return false;
  }

  // Try pressing Enter
  await page.keyboard.press('Enter');

  // Try pressing Space
  await page.keyboard.press('Space');

  console.log(`[A11y] ✓ Keyboard navigation works for: ${selector}`);
  return true;
}

/**
 * Check for ARIA labels and roles
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @returns {Promise<Object>}
 */
export async function checkAriaAttributes(page, selector) {
  console.log(`[A11y] Checking ARIA attributes for: ${selector}`);

  const element = page.locator(selector).first();

  const ariaLabel = await element.getAttribute('aria-label');
  const ariaLabelledBy = await element.getAttribute('aria-labelledby');
  const role = await element.getAttribute('role');
  const ariaDescribedBy = await element.getAttribute('aria-describedby');

  const hasLabel = !!(ariaLabel || ariaLabelledBy);

  console.log(`[A11y] Label: ${ariaLabel || ariaLabelledBy || 'none'}, Role: ${role || 'none'}`);

  return {
    hasLabel,
    ariaLabel,
    ariaLabelledBy,
    role,
    ariaDescribedBy,
  };
}

/**
 * Check color contrast ratios
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @returns {Promise<Object>}
 */
export async function checkColorContrast(page, selector) {
  console.log(`[A11y] Checking color contrast for: ${selector}`);

  const element = page.locator(selector).first();

  const contrast = await element.evaluate((el) => {
    const computedStyle = window.getComputedStyle(el);
    const color = computedStyle.color;
    const backgroundColor = computedStyle.backgroundColor;

    // Simple contrast calculation (not perfect, but good enough for testing)
    const getRgb = (colorStr) => {
      const match = colorStr.match(/\d+/g);
      return match ? match.map(Number) : [0, 0, 0];
    };

    const getLuminance = (rgb) => {
      const [r, g, b] = rgb.map((val) => {
        val = val / 255;
        return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const fgRgb = getRgb(color);
    const bgRgb = getRgb(backgroundColor);

    const fgLuminance = getLuminance(fgRgb);
    const bgLuminance = getLuminance(bgRgb);

    const lighter = Math.max(fgLuminance, bgLuminance);
    const darker = Math.min(fgLuminance, bgLuminance);

    const ratio = (lighter + 0.05) / (darker + 0.05);

    return {
      ratio: ratio.toFixed(2),
      passesAA: ratio >= 4.5,
      passesAAA: ratio >= 7,
      color,
      backgroundColor,
    };
  });

  console.log(
    `[A11y] Contrast ratio: ${contrast.ratio}:1 (AA: ${contrast.passesAA ? '✓' : '✗'}, AAA: ${contrast.passesAAA ? '✓' : '✗'})`
  );

  return contrast;
}

/**
 * Check for focus indicators
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} selector - Element selector
 * @returns {Promise<boolean>}
 */
export async function checkFocusIndicator(page, selector) {
  console.log(`[A11y] Checking focus indicator for: ${selector}`);

  const element = page.locator(selector).first();

  await element.focus();

  const hasFocusIndicator = await element.evaluate((el) => {
    const computedStyle = window.getComputedStyle(el);
    const outline = computedStyle.outline;
    const outlineWidth = computedStyle.outlineWidth;
    const boxShadow = computedStyle.boxShadow;
    const border = computedStyle.border;

    // Check if any focus indicator is present
    return (
      (outline && outline !== 'none' && outlineWidth !== '0px') ||
      (boxShadow && boxShadow !== 'none') ||
      (border && border !== 'none')
    );
  });

  console.log(`[A11y] Focus indicator: ${hasFocusIndicator ? '✓' : '✗'}`);

  return hasFocusIndicator;
}

/**
 * Check for semantic HTML structure
 *
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<Object>}
 */
export async function checkSemanticHTML(page) {
  console.log('[A11y] Checking semantic HTML structure...');

  const structure = await page.evaluate(() => {
    return {
      hasHeader: !!document.querySelector('header, [role="banner"]'),
      hasMain: !!document.querySelector('main, [role="main"]'),
      hasNav: !!document.querySelector('nav, [role="navigation"]'),
      hasFooter: !!document.querySelector('footer, [role="contentinfo"]'),
      headingLevels: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(
        (h) => h.tagName
      ),
      landmarkCount: document.querySelectorAll('[role="region"], section, article, aside').length,
    };
  });

  console.log(`[A11y] Structure:`, structure);

  return structure;
}

/**
 * Generate accessibility report
 *
 * @param {Object} auditResults - Results from runAccessibilityAudit
 * @returns {Object} Summary report
 */
export function generateAccessibilityReport(auditResults) {
  const { violations, incomplete, passes } = auditResults;

  const report = {
    summary: {
      violations: violations.length,
      incomplete: incomplete.length,
      passes: passes.length,
      total: violations.length + incomplete.length + passes.length,
    },
    criticalIssues: violations.filter((v) => v.impact === 'critical'),
    seriousIssues: violations.filter((v) => v.impact === 'serious'),
    moderateIssues: violations.filter((v) => v.impact === 'moderate'),
    minorIssues: violations.filter((v) => v.impact === 'minor'),
    byCategory: {},
  };

  // Group violations by category
  violations.forEach((violation) => {
    violation.tags.forEach((tag) => {
      if (!report.byCategory[tag]) {
        report.byCategory[tag] = [];
      }
      report.byCategory[tag].push(violation);
    });
  });

  return report;
}
