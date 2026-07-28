import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCartIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { useExtensions } from '../contexts/ExtensionsContext';

/**
 * Reusable Add to Cart button with loading and success states
 */
export default function AddToCartButton({
  addon_id,
  addon_name = 'item',
  variant = 'primary',
  size = 'medium',
  className = '',
  onSuccess,
  onError
}) {
  const { addToCart } = useExtensions();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const result = await addToCart(addon_id, 1);
      if (result.success) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 2000);
        if (onSuccess) onSuccess(result.cart);
      } else {
        if (onError) onError(result.error);
      }
    } catch (error) {
      console.error('Add to cart failed:', error);
      if (onError) onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Size variants
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg'
  };

  // Variant styles
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white',
    secondary: 'bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white',
    outline: 'border-2 border-blue-500 text-blue-500 hover:bg-blue-500 hover:text-white',
    ghost: 'text-blue-500 hover:bg-blue-500/10'
  };

  const baseClasses = `
    rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl
    flex items-center justify-center gap-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${className}
  `.trim();

  return (
    <motion.button
      onClick={handleClick}
      disabled={loading || success}
      className={baseClasses}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {success ? (
        <>
          <CheckCircleIcon className="h-5 w-5" />
          <span>Added!</span>
        </>
      ) : loading ? (
        <>
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          <span>Adding...</span>
        </>
      ) : (
        <>
          <ShoppingCartIcon className="h-5 w-5" />
          <span>Add to Cart</span>
        </>
      )}
    </motion.button>
  );
}
