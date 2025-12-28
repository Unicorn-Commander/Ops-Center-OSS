import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingCartIcon,
  XMarkIcon,
  CreditCardIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useExtensions } from '../../contexts/ExtensionsContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';
import PromoCodeInput from '../../components/PromoCodeInput';
import PricingBreakdown from '../../components/PricingBreakdown';
import { useToast } from '../../components/Toast';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

/**
 * Checkout Page Component
 * Complete checkout flow with cart review, promo codes, and Stripe payment
 */
export default function CheckoutPage() {
  const navigate = useNavigate();
  const { theme, currentTheme } = useTheme();
  const { cart, removeFromCart, updateCartItemQuantity, checkout, loading } = useExtensions();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [processingPayment, setProcessingPayment] = useState(false);

  // Calculate totals
  const subtotal = cart.items?.reduce((sum, item) => sum + (item.price * item.quantity), 0) || 0;
  const discount = cart.discount || 0;
  const tax = 0; // Future feature
  const total = subtotal - discount + tax;

  // Redirect if cart is empty
  useEffect(() => {
    if (!loading.cart && cart.items?.length === 0) {
      toast.info('Your cart is empty');
      navigate('/extensions');
    }
  }, [cart.items, loading.cart, navigate, toast]);

  const handleQuantityChange = async (item_id, newQuantity) => {
    if (newQuantity < 1) return;
    if (newQuantity > 10) {
      toast.warning('Maximum quantity is 10');
      return;
    }
    await updateCartItemQuantity(item_id, newQuantity);
  };

  const handleRemoveItem = async (item_id) => {
    await removeFromCart(item_id);
  };

  const handleCheckout = async () => {
    setProcessingPayment(true);
    try {
      const result = await checkout();
      if (!result.success) {
        setProcessingPayment(false);
        toast.error(result.error || 'Failed to start checkout');
      }
      // If successful, user will be redirected to Stripe
    } catch (error) {
      setProcessingPayment(false);
      toast.error('Failed to start checkout');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading.cart) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Loading checkout...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-7xl mx-auto px-4 py-8 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/extensions')}
            className={`p-2 rounded-lg ${glassStyles.card} hover:bg-white/10 transition-colors`}
          >
            <ArrowLeftIcon className={`h-5 w-5 ${theme.text.secondary}`} />
          </button>
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary}`}>
              Checkout
            </h1>
            <p className={`text-sm ${theme.text.secondary} mt-1`}>
              Review your order and complete payment
            </p>
          </div>
        </div>
        <div className={`${glassStyles.card} rounded-xl px-4 py-3`}>
          <p className={`text-sm ${theme.text.secondary}`}>Order Total</p>
          <p className={`text-2xl font-bold ${theme.text.primary}`}>
            {formatCurrency(total)}
          </p>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Cart Items */}
        <div className="lg:col-span-2 space-y-6">
          {/* Cart Review Section */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <ShoppingCartIcon className={`h-6 w-6 ${theme.text.accent}`} />
              <h2 className={`text-xl font-bold ${theme.text.primary}`}>
                Cart Items ({cart.items?.length || 0})
              </h2>
            </div>

            <div className="space-y-4">
              {cart.items?.map((item, index) => (
                <motion.div
                  key={item.id || index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`${glassStyles.card} rounded-xl p-4 flex items-start gap-4`}
                >
                  {/* Item Icon */}
                  <div className={`w-16 h-16 bg-gradient-to-br ${item.iconColor || 'from-blue-500 to-cyan-500'} rounded-xl flex items-center justify-center flex-shrink-0`}>
                    {item.icon && <item.icon className="h-8 w-8 text-white" />}
                  </div>

                  {/* Item Details */}
                  <div className="flex-1 min-w-0">
                    <h3 className={`text-lg font-semibold ${theme.text.primary} truncate`}>
                      {item.name}
                    </h3>
                    <p className={`text-sm ${theme.text.secondary} line-clamp-2 mt-1`}>
                      {item.description}
                    </p>
                    <div className="flex items-center gap-4 mt-3">
                      {/* Quantity Selector */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                          disabled={item.quantity <= 1}
                          className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                        >
                          <span className={theme.text.primary}>−</span>
                        </button>
                        <span className={`w-12 text-center font-semibold ${theme.text.primary}`}>
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                          disabled={item.quantity >= 10}
                          className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                        >
                          <span className={theme.text.primary}>+</span>
                        </button>
                      </div>

                      {/* Price */}
                      <div className={`text-sm ${theme.text.secondary}`}>
                        {formatCurrency(item.price)} / {item.period}
                      </div>
                    </div>
                  </div>

                  {/* Item Total & Remove Button */}
                  <div className="flex flex-col items-end gap-3">
                    <div className={`text-xl font-bold ${theme.text.primary}`}>
                      {formatCurrency(item.price * item.quantity)}
                    </div>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors"
                      title="Remove from cart"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Promo Code Section */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <PromoCodeInput />
          </motion.div>
        </div>

        {/* Sidebar - Order Summary & Checkout */}
        <div className="lg:col-span-1 space-y-6">
          {/* Order Summary (Sticky) */}
          <div className="sticky top-24 space-y-6">
            {/* Pricing Breakdown */}
            <motion.div variants={itemVariants}>
              <PricingBreakdown
                subtotal={subtotal}
                discount={discount}
                tax={tax}
                total={total}
                promo_code={cart.promo_code}
              />
            </motion.div>

            {/* Checkout Button */}
            <motion.div variants={itemVariants}>
              <button
                onClick={handleCheckout}
                disabled={processingPayment || cart.items?.length === 0}
                className={`
                  w-full py-4 px-6 rounded-xl font-bold text-lg
                  bg-gradient-to-r from-green-500 to-emerald-500
                  hover:from-green-600 hover:to-emerald-600
                  text-white shadow-2xl hover:shadow-emerald-500/30
                  transition-all transform hover:scale-105
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
                  flex items-center justify-center gap-3
                `}
              >
                {processingPayment ? (
                  <>
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <CreditCardIcon className="h-6 w-6" />
                    <span>Proceed to Payment</span>
                    <ArrowRightIcon className="h-5 w-5" />
                  </>
                )}
              </button>
            </motion.div>

            {/* Security Notice */}
            <motion.div
              variants={itemVariants}
              className={`${glassStyles.card} rounded-xl p-4 text-center`}
            >
              <p className={`text-xs ${theme.text.secondary}`}>
                🔒 Secure checkout powered by <span className="font-semibold">Stripe</span>
                <br />
                Your payment information is encrypted and secure
              </p>
            </motion.div>

            {/* Features Notice */}
            <motion.div
              variants={itemVariants}
              className={`${glassStyles.card} rounded-xl p-4`}
            >
              <h3 className={`text-sm font-bold ${theme.text.primary} mb-3`}>
                What's included:
              </h3>
              <ul className={`space-y-2 text-xs ${theme.text.secondary}`}>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Instant activation after payment</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Cancel anytime, no long-term contracts</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>24/7 customer support</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>14-day money-back guarantee</span>
                </li>
              </ul>
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
