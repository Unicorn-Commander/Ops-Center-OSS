import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Confetti from 'react-confetti';
import {
  CheckCircleIcon,
  ArrowRightIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useExtensions } from '../../contexts/ExtensionsContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';

/**
 * Success Page Component
 * Displayed after successful Stripe checkout
 * Features confetti animation, order summary, and auto-redirect
 */
export default function SuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { theme, currentTheme } = useTheme();
  const { verifyCheckout } = useExtensions();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [purchase, setPurchase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(true);
  const [countdown, setCountdown] = useState(10);

  // Verify checkout session
  useEffect(() => {
    const session_id = searchParams.get('session_id');
    if (session_id) {
      verifyCheckout(session_id).then(result => {
        if (result.success) {
          setPurchase(result.purchase);
        }
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [searchParams, verifyCheckout]);

  // Stop confetti after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowConfetti(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  // Countdown for auto-redirect
  useEffect(() => {
    if (countdown === 0) {
      navigate('/admin');
      return;
    }

    const timer = setTimeout(() => {
      setCountdown(countdown - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [countdown, navigate]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Verifying your purchase...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Confetti Animation */}
      {showConfetti && (
        <Confetti
          width={window.innerWidth}
          height={window.innerHeight}
          recycle={false}
          numberOfPieces={500}
          gravity={0.3}
        />
      )}

      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl w-full"
      >
        <div className={`${glassStyles.card} rounded-3xl p-8 lg:p-12 text-center space-y-8`}>
          {/* Success Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="flex justify-center"
          >
            <div className="w-24 h-24 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center shadow-2xl">
              <CheckCircleIcon className="h-14 w-14 text-white" />
            </div>
          </motion.div>

          {/* Success Message */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <h1 className={`text-4xl font-bold ${theme.text.primary} mb-4`}>
              Payment Successful! 🎉
            </h1>
            <p className={`text-lg ${theme.text.secondary}`}>
              Thank you for your purchase! Your add-ons have been activated.
            </p>
          </motion.div>

          {/* Order Summary */}
          {purchase && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className={`${glassStyles.card} rounded-xl p-6 text-left space-y-4`}
            >
              <h2 className={`text-xl font-bold ${theme.text.primary} flex items-center gap-2`}>
                <DocumentTextIcon className="h-6 w-6" />
                Order Summary
              </h2>

              <div className="space-y-3">
                {purchase.items?.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className={theme.text.secondary}>{item.name}</span>
                    <span className={`font-semibold ${theme.text.primary}`}>
                      {formatCurrency(item.price)}
                    </span>
                  </div>
                ))}

                <div className="border-t border-white/10 pt-3">
                  <div className="flex items-center justify-between">
                    <span className={`text-lg font-bold ${theme.text.primary}`}>
                      Total Paid
                    </span>
                    <span className={`text-2xl font-bold ${theme.text.primary}`}>
                      {formatCurrency(purchase.total)}
                    </span>
                  </div>
                </div>

                <p className={`text-xs ${theme.text.secondary} text-center pt-2`}>
                  Order #{purchase.id || 'N/A'} • {new Date(purchase.created_at || Date.now()).toLocaleDateString()}
                </p>
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
              onClick={() => navigate('/admin/purchases')}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg"
            >
              <DocumentTextIcon className="h-5 w-5" />
              <span>View Purchase History</span>
            </button>

            <button
              onClick={() => navigate('/extensions')}
              className={`flex items-center justify-center gap-2 px-6 py-3 ${glassStyles.card} hover:bg-white/10 ${theme.text.primary} rounded-lg font-semibold transition-all`}
            >
              <span>Continue Shopping</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </motion.div>

          {/* Auto-redirect Notice */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className={`text-sm ${theme.text.secondary}`}
          >
            Redirecting to dashboard in <span className="font-bold text-green-400">{countdown}</span> seconds...
          </motion.div>

          {/* What's Next */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.7 }}
            className={`${glassStyles.card} rounded-xl p-6 text-left`}
          >
            <h3 className={`text-lg font-bold ${theme.text.primary} mb-4`}>
              What's Next?
            </h3>
            <ul className={`space-y-3 text-sm ${theme.text.secondary}`}>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Your add-ons are now active and ready to use</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Check your email for receipt and access instructions</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Manage your subscriptions in Account Settings</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 flex-shrink-0">✓</span>
                <span>Need help? Contact our 24/7 support team</span>
              </li>
            </ul>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
