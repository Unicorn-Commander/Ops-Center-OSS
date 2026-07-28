import React, { useState } from 'react';
import { useTheme } from '../../../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import { validateEmail } from '../../../utils/validation';

/**
 * TestEmailModal - Test email dialog
 *
 * Modal for sending a test email using the active provider.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 * @param {Function} props.onSend - Send test email handler
 */
export default function TestEmailModal({ isOpen, onClose, onSend }) {
  const { currentTheme } = useTheme();
  const [testEmail, setTestEmail] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleEmailChange = (e) => {
    const value = e.target.value;
    setTestEmail(value);

    // Real-time validation
    if (value) {
      const validationError = validateEmail(value);
      setError(validationError || '');
    } else {
      setError('');
    }
  };

  const handleSend = () => {
    // Validate before sending
    const validationError = validateEmail(testEmail);
    if (validationError) {
      setError(validationError);
      return;
    }

    onSend(testEmail);
    setTestEmail('');
    setError('');
  };

  const handleClose = () => {
    setTestEmail('');
    setError('');
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className={`w-full max-w-md rounded-lg p-6 ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900 border border-purple-500/30'
              : currentTheme === 'light'
              ? 'bg-white border border-gray-200'
              : 'bg-gray-800 border border-gray-700'
          }`}
        >
          <h2 className={`text-xl font-bold mb-4 ${
            currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            Send Test Email
          </h2>
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
            }`}>
              Recipient Email Address <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={testEmail}
              onChange={handleEmailChange}
              placeholder="you@example.com"
              className={`w-full px-4 py-2 rounded-lg border ${
                error
                  ? 'border-red-500 bg-red-500/10'
                  : currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300'
                  : 'bg-gray-700 border-gray-600'
              } ${
                currentTheme === 'unicorn' || currentTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}
            />
            {error && (
              <p className="text-red-500 text-sm mt-1">{error}</p>
            )}
            {!error && testEmail && (
              <p className={`text-sm mt-1 ${
                currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-400'
              }`}>
                Valid email address
              </p>
            )}
          </div>
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={handleClose}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30'
                  : currentTheme === 'light'
                  ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={!testEmail || !!error}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                !testEmail || error
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : currentTheme === 'unicorn'
                  ? 'bg-purple-600 hover:bg-purple-700 text-white'
                  : currentTheme === 'light'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              Send Test
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
