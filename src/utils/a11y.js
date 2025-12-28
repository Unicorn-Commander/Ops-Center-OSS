/**
 * Accessibility Utilities (a11y.js)
 *
 * Utilities for WCAG AA compliance and accessibility support
 */

/**
 * Calculate relative luminance of a color
 * Used for contrast ratio calculations
 *
 * @param {string} color - Hex color (#RRGGBB or #RGB)
 * @returns {number} Relative luminance (0-1)
 */
export const getLuminance = (color) => {
  // Convert hex to RGB
  let hex = color.replace('#', '');

  // Handle 3-digit hex
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('');
  }

  const r = parseInt(hex.substr(0, 2), 16) / 255;
  const g = parseInt(hex.substr(2, 2), 16) / 255;
  const b = parseInt(hex.substr(4, 2), 16) / 255;

  // Calculate relative luminance
  const toLinear = (val) => {
    return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
  };

  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
};

/**
 * Calculate contrast ratio between two colors
 * WCAG requires: 4.5:1 for normal text, 3:1 for large text
 *
 * @param {string} foreground - Foreground color (hex)
 * @param {string} background - Background color (hex)
 * @returns {number} Contrast ratio
 */
export const getContrastRatio = (foreground, background) => {
  const lum1 = getLuminance(foreground);
  const lum2 = getLuminance(background);

  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);

  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Check if color combination meets WCAG AA standards
 *
 * @param {string} foreground - Foreground color (hex)
 * @param {string} background - Background color (hex)
 * @param {boolean} isLargeText - Is text >= 18pt or bold >= 14pt?
 * @returns {Object} Accessibility check result
 */
export const checkColorContrast = (foreground, background, isLargeText = false) => {
  const ratio = getContrastRatio(foreground, background);
  const requiredRatio = isLargeText ? 3 : 4.5;

  return {
    ratio: ratio.toFixed(2),
    passes: ratio >= requiredRatio,
    level: ratio >= 7 ? 'AAA' : ratio >= requiredRatio ? 'AA' : 'Fail',
    required: requiredRatio,
  };
};

/**
 * Get accessible color by adjusting brightness
 * Ensures sufficient contrast with background
 *
 * @param {string} color - Original color (hex)
 * @param {string} backgroundColor - Background color (hex)
 * @param {boolean} isLargeText - Is text large?
 * @returns {string} Adjusted color (hex)
 */
export const getAccessibleColor = (color, backgroundColor, isLargeText = false) => {
  const check = checkColorContrast(color, backgroundColor, isLargeText);

  if (check.passes) {
    return color;
  }

  // Adjust brightness to meet contrast requirements
  let hex = color.replace('#', '');
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('');
  }

  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  const bgLum = getLuminance(backgroundColor);
  const shouldLighten = bgLum < 0.5;

  const adjust = (val, factor) => {
    if (shouldLighten) {
      return Math.min(255, Math.floor(val + (255 - val) * factor));
    } else {
      return Math.max(0, Math.floor(val * (1 - factor)));
    }
  };

  // Try adjusting in steps
  for (let factor = 0.2; factor <= 1; factor += 0.1) {
    const newR = adjust(r, factor);
    const newG = adjust(g, factor);
    const newB = adjust(b, factor);

    const newColor = `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
    const newCheck = checkColorContrast(newColor, backgroundColor, isLargeText);

    if (newCheck.passes) {
      return newColor;
    }
  }

  // Fallback to black or white
  return shouldLighten ? '#FFFFFF' : '#000000';
};

/**
 * Announce message to screen readers
 * Creates temporary element with aria-live region
 *
 * @param {string} message - Message to announce
 * @param {string} priority - 'polite' or 'assertive'
 */
export const announceToScreenReader = (message, priority = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'alert');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.textContent = message;

  // Hide visually but keep accessible to screen readers
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    if (announcement.parentNode) {
      document.body.removeChild(announcement);
    }
  }, 1000);
};

/**
 * Debounce function for performance optimization
 * Useful for window resize events
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Generate unique ID for aria-labelledby
 *
 * @param {string} prefix - Prefix for ID
 * @returns {string} Unique ID
 */
export const generateAriaId = (prefix = 'aria') => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Check if element is focusable
 *
 * @param {HTMLElement} element - DOM element
 * @returns {boolean} Is focusable?
 */
export const isFocusable = (element) => {
  if (!element) return false;

  const focusableTags = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
  const isFocusableTag = focusableTags.includes(element.tagName);
  const hasTabIndex = element.getAttribute('tabindex') !== null && element.getAttribute('tabindex') !== '-1';

  return (isFocusableTag || hasTabIndex) && !element.disabled && element.getAttribute('aria-hidden') !== 'true';
};

/**
 * Trap focus within element (for modals)
 *
 * @param {HTMLElement} element - Container element
 */
export const trapFocus = (element) => {
  const focusableElements = element.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length === 0) return;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  element.addEventListener('keydown', handleTabKey);

  // Focus first element
  firstElement.focus();

  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleTabKey);
  };
};

export default {
  getLuminance,
  getContrastRatio,
  checkColorContrast,
  getAccessibleColor,
  announceToScreenReader,
  debounce,
  generateAriaId,
  isFocusable,
  trapFocus,
};
