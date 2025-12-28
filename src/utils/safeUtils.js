// Safe utility functions to prevent null/undefined errors

// Safe array methods
export const safeMap = (arr, fn) => (Array.isArray(arr) ? arr.map(fn) : []);
export const safeFilter = (arr, fn) => (Array.isArray(arr) ? arr.filter(fn) : []);
export const safeFind = (arr, fn) => (Array.isArray(arr) ? arr.find(fn) : undefined);
export const safeSome = (arr, fn) => (Array.isArray(arr) ? arr.some(fn) : false);
export const safeEvery = (arr, fn) => (Array.isArray(arr) ? arr.every(fn) : true);
export const safeReduce = (arr, fn, init) => (Array.isArray(arr) ? arr.reduce(fn, init) : init);

// Safe number formatting
export const safeToFixed = (num, digits = 2) => {
  const n = Number(num);
  return isNaN(n) ? '0' : n.toFixed(digits);
};

// Safe string methods
export const safeToUpperCase = (str) => (typeof str === 'string' ? str.toUpperCase() : '');
export const safeToLowerCase = (str) => (typeof str === 'string' ? str.toLowerCase() : '');
export const safeIncludes = (str, search) => (typeof str === 'string' ? str.includes(search) : false);

// Safe property access
export const safeGet = (obj, path, defaultValue = undefined) => {
  if (!obj || typeof obj !== 'object') return defaultValue;
  const keys = path.split('.');
  let result = obj;
  for (const key of keys) {
    if (result == null || typeof result !== 'object') return defaultValue;
    result = result[key];
  }
  return result ?? defaultValue;
};

// Safe JSON parse
export const safeJSONParse = (str, defaultValue = {}) => {
  try {
    return JSON.parse(str) ?? defaultValue;
  } catch (e) {
    console.error('JSON parse error:', e);
    return defaultValue;
  }
};

// Safe localStorage
export const safeGetFromStorage = (key, defaultValue = null) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (e) {
    console.error(`Error reading ${key} from localStorage:`, e);
    return defaultValue;
  }
};

export const safeSetToStorage = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.error(`Error writing ${key} to localStorage:`, e);
    return false;
  }
};
