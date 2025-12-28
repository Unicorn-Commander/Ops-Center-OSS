/**
 * Safe Array Utilities
 *
 * Defensive array operations that never crash and always return predictable values.
 * Use these instead of native array methods when dealing with potentially unsafe data.
 *
 * @module safeArrayUtils
 */

/**
 * Safe map - never crashes, always returns an array
 * @param {any} arr - Input array (may be null/undefined)
 * @param {Function} fn - Map function
 * @param {Array} fallback - Fallback value if arr is not an array
 * @returns {Array} Mapped array or fallback
 *
 * @example
 * // Before (crashes if users is undefined)
 * const names = users.map(u => u.name);
 *
 * // After (safe)
 * const names = safeMap(users, u => u.name, []);
 */
export const safeMap = (arr, fn, fallback = []) => {
  if (!Array.isArray(arr)) {
    console.warn('safeMap: Input is not an array:', arr);
    return fallback;
  }
  try {
    return arr.map(fn);
  } catch (e) {
    console.error('safeMap error:', e);
    return fallback;
  }
};

/**
 * Safe find - returns null instead of undefined
 * @param {any} arr - Input array
 * @param {Function} predicate - Find predicate
 * @returns {any|null} Found item or null
 *
 * @example
 * // Before (returns undefined, crashes on .name)
 * const user = users.find(u => u.id === 5);
 * const name = user.name; // Error if not found
 *
 * // After (safe)
 * const user = safeFind(users, u => u.id === 5);
 * const name = user?.name || 'Unknown';
 */
export const safeFind = (arr, predicate) => {
  if (!Array.isArray(arr)) {
    console.warn('safeFind: Input is not an array:', arr);
    return null;
  }
  try {
    return arr.find(predicate) || null;
  } catch (e) {
    console.error('safeFind error:', e);
    return null;
  }
};

/**
 * Safe filter - always returns an array
 * @param {any} arr - Input array
 * @param {Function} predicate - Filter predicate
 * @returns {Array} Filtered array or empty array
 *
 * @example
 * // Before (crashes if arr is undefined)
 * const active = users.filter(u => u.active);
 *
 * // After (safe)
 * const active = safeFilter(users, u => u.active);
 */
export const safeFilter = (arr, predicate) => {
  if (!Array.isArray(arr)) {
    console.warn('safeFilter: Input is not an array:', arr);
    return [];
  }
  try {
    return arr.filter(predicate);
  } catch (e) {
    console.error('safeFilter error:', e);
    return [];
  }
};

/**
 * Safe reduce - handles empty arrays and errors
 * @param {any} arr - Input array
 * @param {Function} reducer - Reducer function
 * @param {any} initialValue - Initial value
 * @returns {any} Reduced value or initialValue
 *
 * @example
 * // Before (crashes if arr is undefined or empty)
 * const total = arr.reduce((sum, item) => sum + item.value, 0);
 *
 * // After (safe)
 * const total = safeReduce(arr, (sum, item) => sum + item.value, 0);
 */
export const safeReduce = (arr, reducer, initialValue) => {
  if (!Array.isArray(arr)) {
    console.warn('safeReduce: Input is not an array:', arr);
    return initialValue;
  }
  if (arr.length === 0) {
    return initialValue;
  }
  try {
    return arr.reduce(reducer, initialValue);
  } catch (e) {
    console.error('safeReduce error:', e);
    return initialValue;
  }
};

/**
 * Safe slice - extracts array segment safely
 * @param {any} arr - Input array
 * @param {number} start - Start index
 * @param {number} end - End index
 * @returns {Array} Sliced array or empty array
 *
 * @example
 * const firstFive = safeSlice(items, 0, 5);
 */
export const safeSlice = (arr, start = 0, end) => {
  if (!Array.isArray(arr)) {
    console.warn('safeSlice: Input is not an array:', arr);
    return [];
  }
  try {
    return arr.slice(start, end);
  } catch (e) {
    console.error('safeSlice error:', e);
    return [];
  }
};

/**
 * Safe sort - sorts without modifying original
 * @param {any} arr - Input array
 * @param {Function} compareFn - Compare function
 * @returns {Array} Sorted copy or empty array
 *
 * @example
 * const sorted = safeSort(users, (a, b) => a.name.localeCompare(b.name));
 */
export const safeSort = (arr, compareFn) => {
  if (!Array.isArray(arr)) {
    console.warn('safeSort: Input is not an array:', arr);
    return [];
  }
  try {
    return [...arr].sort(compareFn);
  } catch (e) {
    console.error('safeSort error:', e);
    return [...arr];
  }
};

/**
 * Safe join - joins array elements safely
 * @param {any} arr - Input array
 * @param {string} separator - Separator string
 * @returns {string} Joined string or empty string
 *
 * @example
 * const csv = safeJoin(values, ', ');
 */
export const safeJoin = (arr, separator = ',') => {
  if (!Array.isArray(arr)) {
    console.warn('safeJoin: Input is not an array:', arr);
    return '';
  }
  try {
    return arr.join(separator);
  } catch (e) {
    console.error('safeJoin error:', e);
    return '';
  }
};

/**
 * Safe indexOf - finds index safely
 * @param {any} arr - Input array
 * @param {any} searchElement - Element to find
 * @returns {number} Index or -1
 *
 * @example
 * const index = safeIndexOf(items, targetItem);
 */
export const safeIndexOf = (arr, searchElement) => {
  if (!Array.isArray(arr)) {
    console.warn('safeIndexOf: Input is not an array:', arr);
    return -1;
  }
  try {
    return arr.indexOf(searchElement);
  } catch (e) {
    console.error('safeIndexOf error:', e);
    return -1;
  }
};

/**
 * Safe includes - checks inclusion safely
 * @param {any} arr - Input array
 * @param {any} searchElement - Element to check
 * @returns {boolean} True if included, false otherwise
 *
 * @example
 * const hasItem = safeIncludes(items, targetItem);
 */
export const safeIncludes = (arr, searchElement) => {
  if (!Array.isArray(arr)) {
    console.warn('safeIncludes: Input is not an array:', arr);
    return false;
  }
  try {
    return arr.includes(searchElement);
  } catch (e) {
    console.error('safeIncludes error:', e);
    return false;
  }
};

/**
 * Safe some - checks if any element matches
 * @param {any} arr - Input array
 * @param {Function} predicate - Test function
 * @returns {boolean} True if any match, false otherwise
 *
 * @example
 * const hasActive = safeSome(users, u => u.active);
 */
export const safeSome = (arr, predicate) => {
  if (!Array.isArray(arr)) {
    console.warn('safeSome: Input is not an array:', arr);
    return false;
  }
  try {
    return arr.some(predicate);
  } catch (e) {
    console.error('safeSome error:', e);
    return false;
  }
};

/**
 * Safe every - checks if all elements match
 * @param {any} arr - Input array
 * @param {Function} predicate - Test function
 * @returns {boolean} True if all match, false otherwise
 *
 * @example
 * const allActive = safeEvery(users, u => u.active);
 */
export const safeEvery = (arr, predicate) => {
  if (!Array.isArray(arr)) {
    console.warn('safeEvery: Input is not an array:', arr);
    return false;
  }
  try {
    return arr.every(predicate);
  } catch (e) {
    console.error('safeEvery error:', e);
    return false;
  }
};

/**
 * Get array length safely
 * @param {any} arr - Input array
 * @returns {number} Length or 0
 *
 * @example
 * const count = safeLength(items);
 */
export const safeLength = (arr) => {
  if (!Array.isArray(arr)) {
    return 0;
  }
  return arr.length;
};

/**
 * Get first element safely
 * @param {any} arr - Input array
 * @param {any} fallback - Fallback value
 * @returns {any} First element or fallback
 *
 * @example
 * const first = safeFirst(items, null);
 */
export const safeFirst = (arr, fallback = null) => {
  if (!Array.isArray(arr) || arr.length === 0) {
    return fallback;
  }
  return arr[0];
};

/**
 * Get last element safely
 * @param {any} arr - Input array
 * @param {any} fallback - Fallback value
 * @returns {any} Last element or fallback
 *
 * @example
 * const last = safeLast(items, null);
 */
export const safeLast = (arr, fallback = null) => {
  if (!Array.isArray(arr) || arr.length === 0) {
    return fallback;
  }
  return arr[arr.length - 1];
};
