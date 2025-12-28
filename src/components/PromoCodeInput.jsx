import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TagIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { useExtensions } from '../contexts/ExtensionsContext';
import { useTheme } from '../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../styles/glassmorphism';

/**
 * Promo Code Input Component
 * Allows users to apply/remove promo codes with validation feedback
 */
export default function PromoCodeInput({ className = '' }) {
  const { theme, currentTheme } = useTheme();
  const { cart, applyPromoCode, removePromoCode } = useExtensions();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleApply = async () => {
    if (!code.trim()) {
      setError('Please enter a promo code');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    const result = await applyPromoCode(code.trim().toUpperCase());

    setLoading(false);

    if (result.success) {
      setSuccess(true);
      setCode('');
      setTimeout(() => setSuccess(false), 3000);
    } else {
      setError(result.error || 'Invalid promo code');
    }
  };

  const handleRemove = async () => {
    setLoading(true);
    await removePromoCode();
    setLoading(false);
    setCode('');
    setError(null);
    setSuccess(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !cart.promo_code) {
      handleApply();
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center gap-2">
        <TagIcon className={`h-5 w-5 ${theme.text.secondary}`} />
        <label className={`text-sm font-semibold ${theme.text.primary}`}>
          Promo Code
        </label>
      </div>

      {cart.promo_code ? (
        // Promo code applied
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${glassStyles.card} rounded-lg p-4`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                <CheckCircleIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className={`text-sm font-semibold ${theme.text.primary}`}>
                  {cart.promo_code.code}
                </p>
                <p className={`text-xs ${theme.text.secondary}`}>
                  {cart.promo_code.discount_percent}% off applied
                </p>
              </div>
            </div>
            <button
              onClick={handleRemove}
              disabled={loading}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                loading
                  ? 'bg-gray-500/20 text-gray-400 cursor-not-allowed'
                  : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              }`}
            >
              {loading ? 'Removing...' : 'Remove'}
            </button>
          </div>
        </motion.div>
      ) : (
        // Promo code input
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={code}
              onChange={(e) => {
                setCode(e.target.value.toUpperCase());
                setError(null);
              }}
              onKeyPress={handleKeyPress}
              placeholder="Enter code (e.g., SAVE20)"
              disabled={loading}
              className={`
                flex-1 px-4 py-2 rounded-lg ${glassStyles.card}
                ${theme.text.primary} placeholder-gray-500
                focus:ring-2 focus:ring-blue-500 focus:outline-none
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            />
            <button
              onClick={handleApply}
              disabled={loading || !code.trim()}
              className="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                'Apply'
              )}
            </button>
          </div>

          {/* Validation feedback */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-red-400 text-sm"
            >
              <XCircleIcon className="h-4 w-4" />
              <span>{error}</span>
            </motion.div>
          )}

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-green-400 text-sm"
            >
              <CheckCircleIcon className="h-4 w-4" />
              <span>Promo code applied successfully!</span>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
