/**
 * Credential Service API Client
 *
 * Manages API credentials for integrated services (Cloudflare, NameCheap, etc.)
 * All credentials are encrypted at rest on the backend.
 */

const API_BASE = '/api/v1/credentials';

export const credentialService = {
  /**
   * List all credentials (values are masked)
   * @returns {Promise<Array>} Array of credential objects
   */
  async list() {
    const response = await fetch(API_BASE, {
      credentials: 'include'  // Include cookies for admin auth
    });
    if (!response.ok) {
      throw new Error('Failed to load credentials');
    }
    return response.json();
  },

  /**
   * Get a single credential by service and type
   * @param {string} service - Service name (e.g., 'cloudflare')
   * @param {string} credentialType - Credential type (e.g., 'api_token')
   * @returns {Promise<Object>} Credential object (value masked)
   */
  async get(service, credentialType) {
    const response = await fetch(`${API_BASE}/${service}/${credentialType}`, {
      credentials: 'include'
    });
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error('Failed to get credential');
    }
    return response.json();
  },

  /**
   * Create a new credential
   * @param {string} service - Service name
   * @param {string} credentialType - Credential type
   * @param {string} value - Credential value (will be encrypted)
   * @param {Object} metadata - Optional metadata
   * @returns {Promise<Object>} Created credential object
   */
  async create(service, credentialType, value, metadata = {}) {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        service,
        credential_type: credentialType,
        value,
        metadata
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || error.detail || 'Failed to create credential');
    }
    return response.json();
  },

  /**
   * Update an existing credential
   * @param {string} service - Service name
   * @param {string} credentialType - Credential type
   * @param {string} value - New credential value
   * @param {Object} metadata - Optional metadata
   * @returns {Promise<Object>} Updated credential object
   */
  async update(service, credentialType, value, metadata = {}) {
    const response = await fetch(`${API_BASE}/${service}/${credentialType}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ value, metadata })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || error.detail || 'Failed to update credential');
    }
    return response.json();
  },

  /**
   * Delete a credential
   * @param {string} service - Service name
   * @param {string} credentialType - Credential type
   * @returns {Promise<Object>} Delete confirmation
   */
  async delete(service, credentialType) {
    const response = await fetch(`${API_BASE}/${service}/${credentialType}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || error.detail || 'Failed to delete credential');
    }
    return response.json();
  },

  /**
   * Test a credential's validity
   * @param {string} service - Service name
   * @param {string|null} value - Optional credential value to test (if null, tests saved credential)
   * @returns {Promise<Object>} Test result { success: boolean, message?: string, error?: string }
   */
  async test(service, value = null) {
    const response = await fetch(`${API_BASE}/${service}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(value ? { value } : {})
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return {
        success: false,
        error: data.error || data.detail || `HTTP ${response.status}: ${response.statusText}`
      };
    }

    return {
      success: true,
      message: data.message || 'Connection successful',
      ...data
    };
  }
};

export default credentialService;
