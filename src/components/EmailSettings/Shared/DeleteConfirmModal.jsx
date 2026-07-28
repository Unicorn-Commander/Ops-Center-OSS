import React from 'react';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * DeleteConfirmModal - Delete confirmation dialog
 *
 * Displays a warning modal before deleting an email provider.
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 * @param {Function} props.onConfirm - Delete confirmation handler
 * @param {string} props.providerId - ID of provider to delete
 */
export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, providerId }) {
  const { currentTheme } = useTheme();

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className={`w-full max-w-md rounded-lg p-6 ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900 border border-red-500/50'
              : currentTheme === 'light'
              ? 'bg-white border border-red-300'
              : 'bg-gray-800 border border-red-600'
          }`}
        >
          <div className="flex items-start gap-4 mb-4">
            <ExclamationCircleIcon className="w-8 h-8 text-red-500 flex-shrink-0" />
            <div>
              <h2 className={`text-xl font-bold mb-2 ${
                currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
              }`}>
                Delete Provider?
              </h2>
              <p className={`text-sm ${
                currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
              }`}>
                This action cannot be undone. All configuration will be permanently deleted.
              </p>
            </div>
          </div>
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onClose}
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
              onClick={() => onConfirm(providerId)}
              className="px-6 py-2 rounded-lg font-semibold bg-red-600 hover:bg-red-700 text-white transition"
            >
              Delete Provider
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
