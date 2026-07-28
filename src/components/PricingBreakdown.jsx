import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../styles/glassmorphism';

/**
 * Pricing Breakdown Component
 * Shows itemized pricing: subtotal, discount, tax, total
 */
export default function PricingBreakdown({
  subtotal = 0,
  discount = 0,
  tax = 0,
  total = 0,
  promo_code = null,
  className = ''
}) {
  const { theme, currentTheme } = useTheme();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card} rounded-xl p-6 space-y-4 ${className}`}
    >
      <h3 className={`text-lg font-bold ${theme.text.primary} mb-4`}>
        Order Summary
      </h3>

      {/* Line items */}
      <div className="space-y-3">
        {/* Subtotal */}
        <div className="flex items-center justify-between">
          <span className={`text-sm ${theme.text.secondary}`}>Subtotal</span>
          <span className={`font-semibold ${theme.text.primary}`}>
            {formatCurrency(subtotal)}
          </span>
        </div>

        {/* Discount (if applied) */}
        {discount > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="flex items-center justify-between text-green-400"
          >
            <span className="text-sm flex items-center gap-2">
              <span>Discount</span>
              {promo_code && (
                <span className="px-2 py-0.5 bg-green-500/20 rounded text-xs font-mono">
                  {promo_code.code}
                </span>
              )}
            </span>
            <span className="font-semibold">
              -{formatCurrency(discount)}
            </span>
          </motion.div>
        )}

        {/* Tax (future feature) */}
        {tax > 0 && (
          <div className="flex items-center justify-between">
            <span className={`text-sm ${theme.text.secondary}`}>Tax</span>
            <span className={`font-semibold ${theme.text.primary}`}>
              {formatCurrency(tax)}
            </span>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="border-t border-white/10 my-4"></div>

      {/* Total */}
      <div className="flex items-center justify-between">
        <span className={`text-base font-bold ${theme.text.primary}`}>
          Total
        </span>
        <span className={`text-2xl font-bold ${theme.text.primary}`}>
          {formatCurrency(total)}
        </span>
      </div>

      {/* Billing notice */}
      <p className={`text-xs ${theme.text.secondary} text-center pt-2`}>
        Billed monthly. Cancel anytime.
      </p>
    </motion.div>
  );
}
