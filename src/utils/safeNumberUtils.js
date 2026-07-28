/**
 * Safe Number Utilities
 *
 * Defensive number operations that handle undefined, null, NaN, and edge cases.
 * Use these for all numeric formatting and calculations with external data.
 *
 * @module safeNumberUtils
 */

/**
 * Safe toFixed - handles undefined/null/NaN
 * @param {any} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number or zero string
 *
 * @example
 * // Before (crashes if undefined)
 * const price = item.price.toFixed(2); // Error if price is undefined
 *
 * // After (safe)
 * const price = safeToFixed(item.price, 2); // Returns "0.00"
 */
export const safeToFixed = (num, decimals = 2) => {
  if (num === undefined || num === null || isNaN(num)) {
    return '0.' + '0'.repeat(decimals);
  }
  try {
    return Number(num).toFixed(decimals);
  } catch (e) {
    console.error('safeToFixed error:', e);
    return '0.' + '0'.repeat(decimals);
  }
};

/**
 * Safe percentage calculation
 * @param {any} value - Numerator
 * @param {any} total - Denominator
 * @param {number} decimals - Decimal places
 * @returns {number} Percentage or 0
 *
 * @example
 * // Before (returns NaN or Infinity)
 * const percent = (used / total) * 100;
 *
 * // After (safe)
 * const percent = safePercent(used, total); // Returns 0 if invalid
 */
export const safePercent = (value, total, decimals = 1) => {
  const val = parseFloat(value);
  const tot = parseFloat(total);

  if (isNaN(val) || isNaN(tot) || tot === 0) {
    return 0;
  }

  try {
    return parseFloat(((val / tot) * 100).toFixed(decimals));
  } catch (e) {
    console.error('safePercent error:', e);
    return 0;
  }
};

/**
 * Format bytes to human-readable string
 * @param {any} bytes - Number of bytes
 * @param {number} decimals - Decimal places
 * @returns {string} Formatted size (e.g., "1.5 GB")
 *
 * @example
 * const size = formatBytes(1536000000); // "1.43 GB"
 */
export const formatBytes = (bytes, decimals = 2) => {
  const num = parseFloat(bytes);

  if (isNaN(num) || num === 0) {
    return '0 Bytes';
  }

  try {
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(num) / Math.log(k));
    const formattedNum = parseFloat((num / Math.pow(k, i)).toFixed(decimals));
    return formattedNum + ' ' + sizes[i];
  } catch (e) {
    console.error('formatBytes error:', e);
    return '0 Bytes';
  }
};

/**
 * Parse number safely with fallback
 * @param {any} value - Value to parse
 * @param {number} fallback - Fallback value
 * @returns {number} Parsed number or fallback
 *
 * @example
 * const count = safeParseInt(data.count, 0);
 */
export const safeParseInt = (value, fallback = 0) => {
  try {
    const num = parseInt(value, 10);
    return isNaN(num) ? fallback : num;
  } catch (e) {
    console.error('safeParseInt error:', e);
    return fallback;
  }
};

/**
 * Parse float safely with fallback
 * @param {any} value - Value to parse
 * @param {number} fallback - Fallback value
 * @returns {number} Parsed number or fallback
 *
 * @example
 * const price = safeParseFloat(data.price, 0.0);
 */
export const safeParseFloat = (value, fallback = 0) => {
  try {
    const num = parseFloat(value);
    return isNaN(num) ? fallback : num;
  } catch (e) {
    console.error('safeParseFloat error:', e);
    return fallback;
  }
};

/**
 * Format number with thousands separator
 * @param {any} num - Number to format
 * @param {string} locale - Locale string
 * @returns {string} Formatted number (e.g., "1,234,567")
 *
 * @example
 * const formatted = formatNumber(1234567); // "1,234,567"
 */
export const formatNumber = (num, locale = 'en-US') => {
  const value = parseFloat(num);

  if (isNaN(value)) {
    return '0';
  }

  try {
    return value.toLocaleString(locale);
  } catch (e) {
    console.error('formatNumber error:', e);
    return String(value);
  }
};

/**
 * Format currency safely
 * @param {any} amount - Amount to format
 * @param {string} currency - Currency code (e.g., 'USD')
 * @param {string} locale - Locale string
 * @returns {string} Formatted currency (e.g., "$1,234.56")
 *
 * @example
 * const price = formatCurrency(1234.56); // "$1,234.56"
 */
export const formatCurrency = (amount, currency = 'USD', locale = 'en-US') => {
  const value = parseFloat(amount);

  if (isNaN(value)) {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    }).format(0);
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    }).format(value);
  } catch (e) {
    console.error('formatCurrency error:', e);
    return `${currency} ${value.toFixed(2)}`;
  }
};

/**
 * Clamp number between min and max
 * @param {any} num - Number to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 *
 * @example
 * const percent = safeClamp(value, 0, 100); // Ensures 0-100 range
 */
export const safeClamp = (num, min, max) => {
  const value = parseFloat(num);

  if (isNaN(value)) {
    return min;
  }

  return Math.min(Math.max(value, min), max);
};

/**
 * Round to specified decimal places
 * @param {any} num - Number to round
 * @param {number} decimals - Decimal places
 * @returns {number} Rounded number
 *
 * @example
 * const rounded = safeRound(3.14159, 2); // 3.14
 */
export const safeRound = (num, decimals = 0) => {
  const value = parseFloat(num);

  if (isNaN(value)) {
    return 0;
  }

  try {
    const multiplier = Math.pow(10, decimals);
    return Math.round(value * multiplier) / multiplier;
  } catch (e) {
    console.error('safeRound error:', e);
    return value;
  }
};

/**
 * Calculate average safely
 * @param {Array} numbers - Array of numbers
 * @returns {number} Average or 0
 *
 * @example
 * const avg = safeAverage([1, 2, 3, 4, 5]); // 3
 */
export const safeAverage = (numbers) => {
  if (!Array.isArray(numbers) || numbers.length === 0) {
    return 0;
  }

  try {
    const validNumbers = numbers.filter(n => !isNaN(parseFloat(n)));
    if (validNumbers.length === 0) return 0;

    const sum = validNumbers.reduce((acc, n) => acc + parseFloat(n), 0);
    return sum / validNumbers.length;
  } catch (e) {
    console.error('safeAverage error:', e);
    return 0;
  }
};

/**
 * Calculate sum safely
 * @param {Array} numbers - Array of numbers
 * @returns {number} Sum or 0
 *
 * @example
 * const total = safeSum([1, 2, 3, 4, 5]); // 15
 */
export const safeSum = (numbers) => {
  if (!Array.isArray(numbers) || numbers.length === 0) {
    return 0;
  }

  try {
    return numbers.reduce((acc, n) => {
      const num = parseFloat(n);
      return acc + (isNaN(num) ? 0 : num);
    }, 0);
  } catch (e) {
    console.error('safeSum error:', e);
    return 0;
  }
};

/**
 * Check if value is a valid number
 * @param {any} value - Value to check
 * @returns {boolean} True if valid number
 *
 * @example
 * if (isValidNumber(input)) { ... }
 */
export const isValidNumber = (value) => {
  if (value === null || value === undefined) {
    return false;
  }
  const num = parseFloat(value);
  return !isNaN(num) && isFinite(num);
};

/**
 * Format duration in seconds to human-readable string
 * @param {any} seconds - Duration in seconds
 * @returns {string} Formatted duration (e.g., "1h 23m 45s")
 *
 * @example
 * const duration = formatDuration(5025); // "1h 23m 45s"
 */
export const formatDuration = (seconds) => {
  const value = parseFloat(seconds);

  if (isNaN(value) || value < 0) {
    return '0s';
  }

  try {
    const h = Math.floor(value / 3600);
    const m = Math.floor((value % 3600) / 60);
    const s = Math.floor(value % 60);

    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0 || parts.length === 0) parts.push(`${s}s`);

    return parts.join(' ');
  } catch (e) {
    console.error('formatDuration error:', e);
    return '0s';
  }
};

/**
 * Format large numbers with K, M, B suffixes
 * @param {any} num - Number to format
 * @param {number} decimals - Decimal places
 * @returns {string} Formatted number (e.g., "1.5M")
 *
 * @example
 * const formatted = formatLargeNumber(1500000); // "1.5M"
 */
export const formatLargeNumber = (num, decimals = 1) => {
  const value = parseFloat(num);

  if (isNaN(value)) {
    return '0';
  }

  try {
    if (value >= 1e9) {
      return (value / 1e9).toFixed(decimals) + 'B';
    } else if (value >= 1e6) {
      return (value / 1e6).toFixed(decimals) + 'M';
    } else if (value >= 1e3) {
      return (value / 1e3).toFixed(decimals) + 'K';
    } else {
      return value.toFixed(decimals);
    }
  } catch (e) {
    console.error('formatLargeNumber error:', e);
    return String(value);
  }
};
