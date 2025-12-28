import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import extensionsApi from '../api/extensionsApi';
import { useToast } from '../components/Toast';

const ExtensionsContext = createContext();

export const useExtensions = () => {
  const context = useContext(ExtensionsContext);
  if (!context) {
    throw new Error('useExtensions must be used within ExtensionsProvider');
  }
  return context;
};

export const ExtensionsProvider = ({ children }) => {
  const toast = useToast();

  // State
  const [cart, setCart] = useState({ items: [], total: 0, promo_code: null, discount: 0 });
  const [purchases, setPurchases] = useState([]);
  const [activeAddons, setActiveAddons] = useState([]);
  const [loading, setLoading] = useState({
    cart: false,
    purchases: false,
    activeAddons: false
  });

  /**
   * Load cart from backend
   */
  const loadCart = useCallback(async () => {
    try {
      setLoading(prev => ({ ...prev, cart: true }));
      const data = await extensionsApi.getCart();
      setCart(data.cart || { items: [], total: 0, promo_code: null, discount: 0 });
    } catch (error) {
      console.error('Failed to load cart:', error);
      // Initialize empty cart on error
      setCart({ items: [], total: 0, promo_code: null, discount: 0 });
    } finally {
      setLoading(prev => ({ ...prev, cart: false }));
    }
  }, []);

  /**
   * Load purchase history
   */
  const loadPurchases = useCallback(async (filters = {}) => {
    try {
      setLoading(prev => ({ ...prev, purchases: true }));
      const data = await extensionsApi.getPurchases(filters);
      setPurchases(data.purchases || []);
    } catch (error) {
      console.error('Failed to load purchases:', error);
      toast.error('Failed to load purchase history');
      setPurchases([]);
    } finally {
      setLoading(prev => ({ ...prev, purchases: false }));
    }
  }, [toast]);

  /**
   * Load active add-ons
   */
  const loadActiveAddons = useCallback(async () => {
    try {
      setLoading(prev => ({ ...prev, activeAddons: true }));
      const data = await extensionsApi.getActiveAddons();
      setActiveAddons(data.addons || []);
    } catch (error) {
      console.error('Failed to load active add-ons:', error);
      setActiveAddons([]);
    } finally {
      setLoading(prev => ({ ...prev, activeAddons: false }));
    }
  }, []);

  /**
   * Add item to cart
   */
  const addToCart = useCallback(async (addon_id, quantity = 1) => {
    try {
      const data = await extensionsApi.addToCart(addon_id, quantity);
      setCart(data.cart);
      toast.success('Added to cart');
      return { success: true, cart: data.cart };
    } catch (error) {
      console.error('Failed to add to cart:', error);
      toast.error(error.message || 'Failed to add to cart');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Remove item from cart
   */
  const removeFromCart = useCallback(async (item_id) => {
    try {
      const data = await extensionsApi.removeFromCart(item_id);
      setCart(data.cart);
      toast.success('Removed from cart');
      return { success: true, cart: data.cart };
    } catch (error) {
      console.error('Failed to remove from cart:', error);
      toast.error(error.message || 'Failed to remove from cart');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Update cart item quantity
   */
  const updateCartItemQuantity = useCallback(async (item_id, quantity) => {
    try {
      const data = await extensionsApi.updateCartItem(item_id, quantity);
      setCart(data.cart);
      return { success: true, cart: data.cart };
    } catch (error) {
      console.error('Failed to update cart item:', error);
      toast.error(error.message || 'Failed to update quantity');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Clear cart
   */
  const clearCart = useCallback(async () => {
    try {
      await extensionsApi.clearCart();
      setCart({ items: [], total: 0, promo_code: null, discount: 0 });
      toast.success('Cart cleared');
      return { success: true };
    } catch (error) {
      console.error('Failed to clear cart:', error);
      toast.error(error.message || 'Failed to clear cart');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Apply promo code
   */
  const applyPromoCode = useCallback(async (code) => {
    try {
      const data = await extensionsApi.validatePromoCode(code);
      setCart(data.cart);
      toast.success(`Promo code applied! ${data.discount_percent}% off`);
      return { success: true, cart: data.cart };
    } catch (error) {
      console.error('Failed to apply promo code:', error);
      toast.error(error.message || 'Invalid promo code');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Remove promo code
   */
  const removePromoCode = useCallback(async () => {
    try {
      const data = await extensionsApi.removePromoCode();
      setCart(data.cart);
      toast.info('Promo code removed');
      return { success: true, cart: data.cart };
    } catch (error) {
      console.error('Failed to remove promo code:', error);
      toast.error(error.message || 'Failed to remove promo code');
      return { success: false, error: error.message };
    }
  }, [toast]);

  /**
   * Create checkout session (navigate to Stripe)
   */
  const checkout = useCallback(async () => {
    try {
      const data = await extensionsApi.createCheckout(cart.promo_code);
      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return { success: true, checkout_url: data.checkout_url };
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (error) {
      console.error('Failed to create checkout:', error);
      toast.error(error.message || 'Failed to start checkout');
      return { success: false, error: error.message };
    }
  }, [cart.promo_code, toast]);

  /**
   * Verify checkout session (after Stripe redirect)
   */
  const verifyCheckout = useCallback(async (session_id) => {
    try {
      const data = await extensionsApi.verifyCheckoutSession(session_id);
      // Reload cart and active add-ons
      await Promise.all([loadCart(), loadActiveAddons(), loadPurchases()]);
      return { success: true, purchase: data.purchase };
    } catch (error) {
      console.error('Failed to verify checkout:', error);
      return { success: false, error: error.message };
    }
  }, [loadCart, loadActiveAddons, loadPurchases]);

  /**
   * Download invoice
   */
  const downloadInvoice = useCallback(async (purchase_id) => {
    try {
      const blob = await extensionsApi.downloadInvoice(purchase_id);
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${purchase_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Invoice downloaded');
      return { success: true };
    } catch (error) {
      console.error('Failed to download invoice:', error);
      toast.error(error.message || 'Failed to download invoice');
      return { success: false, error: error.message };
    }
  }, [toast]);

  // Load cart on mount
  useEffect(() => {
    loadCart();
  }, [loadCart]);

  const value = {
    // State
    cart,
    purchases,
    activeAddons,
    loading,

    // Cart actions
    loadCart,
    addToCart,
    removeFromCart,
    updateCartItemQuantity,
    clearCart,

    // Promo code actions
    applyPromoCode,
    removePromoCode,

    // Purchase actions
    loadPurchases,
    loadActiveAddons,
    checkout,
    verifyCheckout,
    downloadInvoice
  };

  return (
    <ExtensionsContext.Provider value={value}>
      {children}
    </ExtensionsContext.Provider>
  );
};

export default ExtensionsProvider;
