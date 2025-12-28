/**
 * Validation Utilities for Ops-Center
 *
 * Provides reusable validation functions for form inputs across the application.
 * All validators return `null` for valid input, or an error message string for invalid input.
 */

/**
 * Email validation
 * @param {string} value - Email address to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateEmail = (value) => {
  if (!value || !value.trim()) {
    return 'Email address is required';
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return 'Please enter a valid email address';
  }

  return null;
};

/**
 * Required field validation
 * @param {string} value - Value to validate
 * @param {string} fieldName - Name of field for error message
 * @returns {string|null} Error message or null if valid
 */
export const validateRequired = (value, fieldName = 'This field') => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return `${fieldName} is required`;
  }
  return null;
};

/**
 * Minimum length validation
 * @param {number} min - Minimum length
 * @returns {function} Validator function
 */
export const validateMinLength = (min) => (value) => {
  if (!value) return null; // Let required validator handle empty values
  if (value.length < min) {
    return `Minimum ${min} characters required`;
  }
  return null;
};

/**
 * Maximum length validation
 * @param {number} max - Maximum length
 * @returns {function} Validator function
 */
export const validateMaxLength = (max) => (value) => {
  if (!value) return null;
  if (value.length > max) {
    return `Maximum ${max} characters allowed`;
  }
  return null;
};

/**
 * Number range validation
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {function} Validator function
 */
export const validateNumberRange = (min, max) => (value) => {
  if (!value && value !== 0) return null;

  const num = Number(value);
  if (isNaN(num)) {
    return 'Must be a valid number';
  }

  if (num < min || num > max) {
    return `Must be between ${min} and ${max}`;
  }

  return null;
};

/**
 * URL validation
 * @param {string} value - URL to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateUrl = (value) => {
  if (!value || !value.trim()) {
    return 'URL is required';
  }

  try {
    new URL(value);
    return null;
  } catch {
    return 'Please enter a valid URL (e.g., https://example.com)';
  }
};

/**
 * GUID/UUID validation
 * @param {string} value - GUID to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateGuid = (value) => {
  if (!value || !value.trim()) {
    return 'GUID is required';
  }

  const guidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!guidRegex.test(value)) {
    return 'Please enter a valid GUID (e.g., 12345678-1234-1234-1234-123456789012)';
  }

  return null;
};

/**
 * Hostname/IP validation
 * @param {string} value - Hostname or IP address to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateHostname = (value) => {
  if (!value || !value.trim()) {
    return 'Hostname is required';
  }

  // Simple hostname/IP validation
  const hostnameRegex = /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;

  if (!hostnameRegex.test(value) && !ipRegex.test(value)) {
    return 'Please enter a valid hostname or IP address';
  }

  return null;
};

/**
 * Port number validation
 * @param {string|number} value - Port number to validate
 * @returns {string|null} Error message or null if valid
 */
export const validatePort = (value) => {
  if (!value && value !== 0) {
    return 'Port is required';
  }

  const port = Number(value);
  if (isNaN(port) || port < 1 || port > 65535 || !Number.isInteger(port)) {
    return 'Port must be a number between 1 and 65535';
  }

  return null;
};

/**
 * Domain validation
 * @param {string} value - Domain to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateDomain = (value) => {
  if (!value || !value.trim()) {
    return 'Domain is required';
  }

  const domainRegex = /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  if (!domainRegex.test(value)) {
    return 'Please enter a valid domain (e.g., example.com)';
  }

  return null;
};

/**
 * Future date validation
 * @param {string|Date} value - Date to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateFutureDate = (value) => {
  if (!value) {
    return 'Date is required';
  }

  const date = new Date(value);
  const now = new Date();

  if (isNaN(date.getTime())) {
    return 'Please enter a valid date';
  }

  if (date <= now) {
    return 'Date must be in the future';
  }

  return null;
};

/**
 * JSON validation
 * @param {string} value - JSON string to validate
 * @returns {string|null} Error message or null if valid
 */
export const validateJson = (value) => {
  if (!value || !value.trim()) {
    return null; // Allow empty JSON (will default to {})
  }

  try {
    JSON.parse(value);
    return null;
  } catch (e) {
    return `Invalid JSON: ${e.message}`;
  }
};

/**
 * Composite validator - runs multiple validators on a value
 * @param {Array<function>} validators - Array of validator functions
 * @returns {function} Combined validator function
 */
export const combineValidators = (...validators) => (value) => {
  for (const validator of validators) {
    const error = validator(value);
    if (error) return error;
  }
  return null;
};

/**
 * Conditional validator - only validates if condition is true
 * @param {function} condition - Function that returns boolean
 * @param {function} validator - Validator to run if condition is true
 * @returns {function} Conditional validator function
 */
export const validateIf = (condition, validator) => (value, formData) => {
  if (condition(formData)) {
    return validator(value);
  }
  return null;
};

/**
 * Critical process names that require extra confirmation before killing
 */
export const CRITICAL_PROCESSES = [
  'ops-center',
  'ops-center-direct',
  'postgres',
  'postgresql',
  'unicorn-postgresql',
  'redis',
  'unicorn-redis',
  'traefik',
  'keycloak',
  'uchub-keycloak',
  'authentik',
  'nginx'
];

/**
 * Check if a process name is critical
 * @param {string} processName - Name of the process
 * @returns {boolean} True if process is critical
 */
export const isCriticalProcess = (processName) => {
  if (!processName) return false;

  const name = processName.toLowerCase();
  return CRITICAL_PROCESSES.some(critical => name.includes(critical));
};

/**
 * Get warning message for critical process
 * @param {string} processName - Name of the process
 * @param {number} pid - Process ID
 * @returns {object} Warning message details
 */
export const getCriticalProcessWarning = (processName, pid) => {
  const impacts = {
    'ops-center': ['Service downtime', 'Loss of admin access', 'Interrupted user sessions'],
    'postgres': ['Database unavailable', 'Data access lost', 'All services affected'],
    'redis': ['Cache cleared', 'Session data lost', 'Performance degradation'],
    'traefik': ['All external access lost', 'SSL/TLS termination stopped', 'Service routing broken'],
    'keycloak': ['Authentication broken', 'Users cannot login', 'SSO unavailable'],
    'nginx': ['Web server stopped', 'Frontend unavailable', 'API proxy broken']
  };

  // Find matching impact list
  let impactList = ['Service downtime', 'Potential data loss', 'System instability'];
  for (const [key, impacts] of Object.entries(impacts)) {
    if (processName.toLowerCase().includes(key)) {
      impactList = impacts;
      break;
    }
  }

  return {
    title: '⚠️ Kill Critical Process?',
    processName,
    pid,
    impacts: impactList,
    requireConfirmation: true,
    confirmationText: processName
  };
};

/**
 * Validate form data object
 * @param {object} formData - Form data to validate
 * @param {object} validationRules - Map of field names to validator functions
 * @returns {object} Object with field names as keys and error messages as values
 */
export const validateForm = (formData, validationRules) => {
  const errors = {};

  for (const [field, validator] of Object.entries(validationRules)) {
    const value = formData[field];
    const error = typeof validator === 'function'
      ? validator(value, formData)
      : null;

    if (error) {
      errors[field] = error;
    }
  }

  return errors;
};

/**
 * Default export with all validators
 */
export default {
  email: validateEmail,
  required: validateRequired,
  minLength: validateMinLength,
  maxLength: validateMaxLength,
  numberRange: validateNumberRange,
  url: validateUrl,
  guid: validateGuid,
  hostname: validateHostname,
  port: validatePort,
  domain: validateDomain,
  futureDate: validateFutureDate,
  json: validateJson,
  combine: combineValidators,
  validateIf,
  isCriticalProcess,
  getCriticalProcessWarning,
  validateForm
};
