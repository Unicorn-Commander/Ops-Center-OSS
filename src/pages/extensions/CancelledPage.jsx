import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  XCircleIcon,
  ArrowRightIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useExtensions } from '../../contexts/ExtensionsContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';

/**
 * Cancelled Page Component
 * Displayed when user cancels Stripe checkout
 * Shows friendly message and cart summary
 */
export default function CancelledPage() {
  const navigate = useNavigate();
  const { theme, currentTheme } = useTheme();
  const { cart } = useExtensions();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const cartTotal = cart.items?.reduce((sum, item) => sum + (item.price * item.quantity), 0) || 0;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl w-full"
      >
        <div className={`${glassStyles.card} rounded-3xl p-8 lg:p-12 text-center space-y-8`}>
          {/* Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="flex justify-center"
          >
            <div className="w-24 h-24 bg-gradient-to-br from-amber-500 to-orange-500 rounded-full flex items-center justify-center shadow-2xl">
              <XCircleIcon className="h-14 w-14 text-white" />
            </div>
          </motion.div>

          {/* Message */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <h1 className={`text-4xl font-bold ${theme.text.primary} mb-4`}>
              Payment Cancelled
            </h1>
            <p className={`text-lg ${theme.text.secondary}`}>
              No worries! We've saved your cart for you.
            </p>
          </motion.div>

          {/* Cart Summary */}
          {cart.items?.length > 0 && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className={`${glassStyles.card} rounded-xl p-6 text-left space-y-4`}
            >
              <h2 className={`text-xl font-bold ${theme.text.primary} flex items-center gap-2`}>
                <ShoppingCartIcon className="h-6 w-6" />
                Your Cart ({cart.items.length} {cart.items.length === 1 ? 'item' : 'items'})
              </h2>

              <div className="space-y-3">
                {cart.items.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 bg-gradient-to-br ${item.iconColor || 'from-blue-500 to-cyan-500'} rounded-lg flex items-center justify-center flex-shrink-0`}>
                        {item.icon && <item.icon className="h-5 w-5 text-white" />}
                      </div>
                      <div>
                        <p className={`text-sm font-semibold ${theme.text.primary}`}>
                          {item.name}
                        </p>
                        <p className={`text-xs ${theme.text.secondary}`}>
                          Qty: {item.quantity}
                        </p>
                      </div>
                    </div>
                    <span className={`font-semibold ${theme.text.primary}`}>
                      {formatCurrency(item.price * item.quantity)}
                    </span>
                  </div>
                ))}

                <div className="border-t border-white/10 pt-3">
                  <div className="flex items-center justify-between">
                    <span className={`text-lg font-bold ${theme.text.primary}`}>
                      Subtotal
                    </span>
                    <span className={`text-2xl font-bold ${theme.text.primary}`}>
                      {formatCurrency(cartTotal)}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Action Buttons */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={() => navigate('/extensions/checkout')}
              className="flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg font-bold text-lg transition-all shadow-lg transform hover:scale-105"
            >
              <ShoppingCartIcon className="h-6 w-6" />
              <span>Return to Cart</span>
            </button>

            <button
              onClick={() => navigate('/extensions')}
              className={`flex items-center justify-center gap-2 px-8 py-4 ${glassStyles.card} hover:bg-white/10 ${theme.text.primary} rounded-lg font-bold text-lg transition-all`}
            >
              <span>Continue Shopping</span>
              <ArrowRightIcon className="h-6 w-6" />
            </button>
          </motion.div>

          {/* Reassurance Message */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            className={`${glassStyles.card} rounded-xl p-6 text-left`}
          >
            <h3 className={`text-lg font-bold ${theme.text.primary} mb-4`}>
              Why Choose Our Extensions?
            </h3>
            <ul className={`space-y-3 text-sm ${theme.text.secondary}`}>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Instant activation - start using immediately after purchase</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Cancel anytime - no long-term commitments or contracts</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>24/7 customer support - we're here to help whenever you need us</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>14-day money-back guarantee - 100% satisfaction guaranteed</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Secure payments - encrypted and PCI-compliant checkout</span>
              </li>
            </ul>
          </motion.div>

          {/* Support Notice */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className={`text-sm ${theme.text.secondary}`}
          >
            Have questions? <button
              onClick={() => navigate('/admin/account/support')}
              className="text-blue-400 hover:text-blue-300 underline font-semibold"
            >
              Contact Support
            </button>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
