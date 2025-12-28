/**
 * Extensions Marketplace API Client
 * Handles all API calls for extensions, cart, purchases, and promo codes
 */

const API_BASE = '/api/v1';

/**
 * Generic API call wrapper with error handling
 */
async function apiCall(endpoint, options = {}) {
  const defaultOptions = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...defaultOptions,
      ...options
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Extensions API
 */
export const extensionsApi = {
  /**
   * CATALOG ENDPOINTS
   */

  // Get all extensions with optional filters
  getCatalog: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.search) params.append('search', filters.search);
    if (filters.sortBy) params.append('sort_by', filters.sortBy);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const queryString = params.toString();
    return apiCall(`/extensions/catalog${queryString ? `?${queryString}` : ''}`);
  },

  // Get single extension by ID
  getAddon: async (id) => {
    return apiCall(`/extensions/${id}`);
  },

  // Search extensions
  search: async (query) => {
    const params = new URLSearchParams({ q: query });
    return apiCall(`/extensions/search?${params.toString()}`);
  },

  /**
   * CART ENDPOINTS
   */

  // Get current user's cart
  getCart: async () => {
    return apiCall('/cart');
  },

  // Add item to cart
  addToCart: async (addon_id, quantity = 1) => {
    return apiCall('/cart/add', {
      method: 'POST',
      body: JSON.stringify({ addon_id, quantity })
    });
  },

  // Remove item from cart
  removeFromCart: async (item_id) => {
    return apiCall(`/cart/${item_id}`, {
      method: 'DELETE'
    });
  },

  // Update cart item quantity
  updateCartItem: async (item_id, quantity) => {
    return apiCall(`/cart/${item_id}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity })
    });
  },

  // Clear entire cart
  clearCart: async () => {
    return apiCall('/cart/clear', {
      method: 'DELETE'
    });
  },

  /**
   * PURCHASE ENDPOINTS
   */

  // Create Stripe checkout session
  createCheckout: async (promo_code = null) => {
    return apiCall('/extensions/checkout', {
      method: 'POST',
      body: JSON.stringify({ promo_code })
    });
  },

  // Get user's purchase history
  getPurchases: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.from_date) params.append('from_date', filters.from_date);
    if (filters.to_date) params.append('to_date', filters.to_date);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const queryString = params.toString();
    return apiCall(`/extensions/purchases${queryString ? `?${queryString}` : ''}`);
  },

  // Get active (purchased) add-ons
  getActiveAddons: async () => {
    return apiCall('/extensions/active');
  },

  // Get single purchase details
  getPurchase: async (purchase_id) => {
    return apiCall(`/extensions/purchases/${purchase_id}`);
  },

  // Download invoice (returns blob)
  downloadInvoice: async (purchase_id) => {
    const response = await fetch(`${API_BASE}/extensions/purchases/${purchase_id}/invoice`, {
      credentials: 'include'
    });
    if (!response.ok) throw new Error('Failed to download invoice');
    return response.blob();
  },

  /**
   * PROMO CODE ENDPOINTS
   */

  // Validate and apply promo code
  validatePromoCode: async (code) => {
    return apiCall('/cart/apply-promo', {
      method: 'POST',
      body: JSON.stringify({ code })
    });
  },

  // Remove promo code from cart
  removePromoCode: async () => {
    return apiCall('/cart/remove-promo', {
      method: 'DELETE'
    });
  },

  /**
   * CHECKOUT VERIFICATION ENDPOINTS
   */

  // Verify Stripe checkout session (after redirect)
  verifyCheckoutSession: async (session_id) => {
    return apiCall(`/extensions/checkout/verify?session_id=${session_id}`);
  },

  /**
   * ANALYTICS ENDPOINTS
   */

  // Get user's extension usage statistics
  getUsageStats: async () => {
    return apiCall('/extensions/usage');
  }
};

export default extensionsApi;
