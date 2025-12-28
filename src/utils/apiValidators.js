/**
 * API Response Validators
 *
 * Validate and normalize API responses to prevent crashes from unexpected data shapes.
 * Use these for all external API calls before using the data.
 *
 * @module apiValidators
 */

/**
 * Validate array response with detailed logging
 * @param {any} data - Data to validate
 * @param {string} fieldName - Field name for logging
 * @returns {Array} Validated array or empty array
 *
 * @example
 * // Before (crashes if data.users is null)
 * const users = response.data.users;
 * users.map(u => u.name); // Error if null
 *
 * // After (safe)
 * const users = validateArrayResponse(response.data.users, 'users');
 * users.map(u => u.name); // Always works
 */
export const validateArrayResponse = (data, fieldName = 'data') => {
  if (data === null || data === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined`);
    return [];
  }

  if (!Array.isArray(data)) {
    console.warn(`[API Validator] ${fieldName} is not an array:`, {
      type: typeof data,
      value: data
    });
    return [];
  }

  return data;
};

/**
 * Validate numeric field with fallback
 * @param {any} value - Value to validate
 * @param {number} fallback - Fallback value
 * @param {string} fieldName - Field name for logging
 * @returns {number} Validated number or fallback
 *
 * @example
 * const count = validateNumber(response.data.count, 0, 'count');
 */
export const validateNumber = (value, fallback = 0, fieldName = 'value') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback: ${fallback}`);
    return fallback;
  }

  const num = parseFloat(value);

  if (isNaN(num)) {
    console.warn(`[API Validator] ${fieldName} is not a valid number:`, value);
    return fallback;
  }

  return num;
};

/**
 * Validate string field with fallback
 * @param {any} value - Value to validate
 * @param {string} fallback - Fallback value
 * @param {string} fieldName - Field name for logging
 * @returns {string} Validated string or fallback
 *
 * @example
 * const name = validateString(response.data.name, 'Unknown', 'name');
 */
export const validateString = (value, fallback = '', fieldName = 'value') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback: "${fallback}"`);
    return fallback;
  }

  if (typeof value !== 'string') {
    console.warn(`[API Validator] ${fieldName} is not a string:`, {
      type: typeof value,
      value: value
    });
    return String(value);
  }

  return value;
};

/**
 * Validate boolean field with fallback
 * @param {any} value - Value to validate
 * @param {boolean} fallback - Fallback value
 * @param {string} fieldName - Field name for logging
 * @returns {boolean} Validated boolean or fallback
 *
 * @example
 * const isActive = validateBoolean(response.data.active, false, 'active');
 */
export const validateBoolean = (value, fallback = false, fieldName = 'value') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback: ${fallback}`);
    return fallback;
  }

  if (typeof value !== 'boolean') {
    console.warn(`[API Validator] ${fieldName} is not a boolean:`, {
      type: typeof value,
      value: value
    });
    return Boolean(value);
  }

  return value;
};

/**
 * Validate object field with fallback
 * @param {any} value - Value to validate
 * @param {Object} fallback - Fallback value
 * @param {string} fieldName - Field name for logging
 * @returns {Object} Validated object or fallback
 *
 * @example
 * const config = validateObject(response.data.config, {}, 'config');
 */
export const validateObject = (value, fallback = {}, fieldName = 'value') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback`);
    return fallback;
  }

  if (typeof value !== 'object' || Array.isArray(value)) {
    console.warn(`[API Validator] ${fieldName} is not a plain object:`, {
      type: typeof value,
      isArray: Array.isArray(value),
      value: value
    });
    return fallback;
  }

  return value;
};

/**
 * Validate pagination response structure
 * @param {any} data - Response data
 * @returns {Object} Validated pagination object
 *
 * @example
 * const { items, total, page, pageSize } = validatePaginationResponse(response.data);
 */
export const validatePaginationResponse = (data) => {
  const validated = {
    items: validateArrayResponse(data?.items || data?.data, 'items'),
    total: validateNumber(data?.total, 0, 'total'),
    page: validateNumber(data?.page, 1, 'page'),
    pageSize: validateNumber(data?.pageSize || data?.page_size, 10, 'pageSize'),
    hasMore: validateBoolean(data?.hasMore || data?.has_more, false, 'hasMore')
  };

  return validated;
};

/**
 * Validate API error response
 * @param {any} error - Error object
 * @returns {Object} Normalized error object
 *
 * @example
 * catch (error) {
 *   const normalized = validateErrorResponse(error);
 *   showError(normalized.message);
 * }
 */
export const validateErrorResponse = (error) => {
  const normalized = {
    message: 'An unexpected error occurred',
    status: 500,
    code: 'UNKNOWN_ERROR',
    details: null
  };

  if (!error) {
    return normalized;
  }

  // Extract error message
  if (error.response?.data?.message) {
    normalized.message = error.response.data.message;
  } else if (error.response?.data?.error) {
    normalized.message = error.response.data.error;
  } else if (error.message) {
    normalized.message = error.message;
  }

  // Extract status code
  if (error.response?.status) {
    normalized.status = error.response.status;
  }

  // Extract error code
  if (error.response?.data?.code) {
    normalized.code = error.response.data.code;
  } else if (error.code) {
    normalized.code = error.code;
  }

  // Extract additional details
  if (error.response?.data?.details) {
    normalized.details = error.response.data.details;
  }

  console.error('[API Validator] Error:', normalized);

  return normalized;
};

/**
 * Validate required fields in object
 * @param {Object} obj - Object to validate
 * @param {Array<string>} requiredFields - Required field names
 * @param {string} objectName - Object name for logging
 * @returns {Object} Validation result
 *
 * @example
 * const validation = validateRequiredFields(userData, ['id', 'email', 'name'], 'user');
 * if (!validation.isValid) {
 *   console.error('Missing fields:', validation.missingFields);
 * }
 */
export const validateRequiredFields = (obj, requiredFields, objectName = 'object') => {
  const missingFields = [];

  if (!obj || typeof obj !== 'object') {
    console.error(`[API Validator] ${objectName} is not a valid object`);
    return {
      isValid: false,
      missingFields: requiredFields,
      object: obj
    };
  }

  for (const field of requiredFields) {
    if (obj[field] === null || obj[field] === undefined) {
      missingFields.push(field);
    }
  }

  if (missingFields.length > 0) {
    console.warn(`[API Validator] ${objectName} is missing required fields:`, missingFields);
  }

  return {
    isValid: missingFields.length === 0,
    missingFields,
    object: obj
  };
};

/**
 * Validate and normalize date field
 * @param {any} value - Date value (string, number, Date)
 * @param {Date} fallback - Fallback date
 * @param {string} fieldName - Field name for logging
 * @returns {Date} Validated Date object or fallback
 *
 * @example
 * const createdAt = validateDate(response.data.created_at, new Date(), 'created_at');
 */
export const validateDate = (value, fallback = new Date(), fieldName = 'date') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback`);
    return fallback;
  }

  try {
    const date = new Date(value);

    if (isNaN(date.getTime())) {
      console.warn(`[API Validator] ${fieldName} is not a valid date:`, value);
      return fallback;
    }

    return date;
  } catch (e) {
    console.error(`[API Validator] Error parsing ${fieldName}:`, e);
    return fallback;
  }
};

/**
 * Validate enum/choice field
 * @param {any} value - Value to validate
 * @param {Array} validOptions - Valid option values
 * @param {any} fallback - Fallback value
 * @param {string} fieldName - Field name for logging
 * @returns {any} Validated value or fallback
 *
 * @example
 * const status = validateEnum(
 *   response.data.status,
 *   ['active', 'pending', 'inactive'],
 *   'pending',
 *   'status'
 * );
 */
export const validateEnum = (value, validOptions, fallback, fieldName = 'value') => {
  if (value === null || value === undefined) {
    console.warn(`[API Validator] ${fieldName} is null or undefined, using fallback: ${fallback}`);
    return fallback;
  }

  if (!validOptions.includes(value)) {
    console.warn(`[API Validator] ${fieldName} has invalid value:`, {
      value,
      validOptions
    });
    return fallback;
  }

  return value;
};

/**
 * Sanitize API response by removing null/undefined values
 * @param {any} data - Data to sanitize
 * @param {any} fallback - Fallback for null values
 * @returns {any} Sanitized data
 *
 * @example
 * const clean = sanitizeResponse(apiResponse, {});
 */
export const sanitizeResponse = (data, fallback = {}) => {
  if (data === null || data === undefined) {
    return fallback;
  }

  if (Array.isArray(data)) {
    return data.map(item => sanitizeResponse(item, fallback));
  }

  if (typeof data === 'object') {
    const sanitized = {};

    for (const [key, value] of Object.entries(data)) {
      if (value !== null && value !== undefined) {
        sanitized[key] = sanitizeResponse(value, fallback);
      }
    }

    return sanitized;
  }

  return data;
};
