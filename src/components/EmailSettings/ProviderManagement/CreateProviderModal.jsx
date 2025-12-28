import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import ProviderTypeTab from '../ProviderForms/ProviderTypeTab';
import AuthenticationTab from '../ProviderForms/AuthenticationTab';
import SettingsTab from '../ProviderForms/SettingsTab';
import MicrosoftSetupHelp from '../SetupHelp/MicrosoftSetupHelp';

/**
 * CreateProviderModal - Main provider create/edit modal
 *
 * Multi-tab modal for creating or editing email providers.
 * Contains 4 tabs:
 * 1. Provider Type - Select provider type (8 options)
 * 2. Authentication - Configure auth (OAuth2, SMTP, API Key)
 * 3. Settings - From email, advanced config, enable toggle
 * 4. Setup Help - Microsoft 365 OAuth2 instructions
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 * @param {Function} props.onSave - Save handler
 * @param {Object} props.formData - Form state
 * @param {Function} props.setFormData - Form state setter
 * @param {Object} props.showSensitive - Password visibility state
 * @param {Function} props.setShowSensitive - Password visibility setter
 * @param {number} props.currentTab - Active tab index
 * @param {Function} props.setCurrentTab - Tab setter
 * @param {Object} props.editingProvider - Provider being edited (null for new)
 * @param {Object} props.microsoftInstructions - Microsoft setup instructions
 */
export default function CreateProviderModal({
  isOpen,
  onClose,
  onSave,
  formData,
  setFormData,
  showSensitive,
  setShowSensitive,
  currentTab,
  setCurrentTab,
  editingProvider,
  microsoftInstructions
}) {
  const { currentTheme } = useTheme();

  if (!isOpen) return null;

  const tabs = ['Provider Type', 'Authentication', 'Settings', 'Setup Help'];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className={`w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-lg ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900 border border-purple-500/30'
              : currentTheme === 'light'
              ? 'bg-white border border-gray-200'
              : 'bg-gray-800 border border-gray-700'
          }`}
        >
          {/* Dialog Header */}
          <div className="p-6 border-b border-current">
            <div className="flex items-center justify-between">
              <h2 className={`text-2xl font-bold ${
                currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
              }`}>
                {editingProvider ? 'Edit Provider' : 'Add Email Provider'}
              </h2>
              <button
                onClick={onClose}
                className="p-2 rounded hover:bg-white/10"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className={`flex border-b ${
            currentTheme === 'unicorn'
              ? 'border-purple-500/30'
              : currentTheme === 'light'
              ? 'border-gray-200'
              : 'border-gray-700'
          }`}>
            {tabs.map((tab, index) => (
              <button
                key={tab}
                onClick={() => setCurrentTab(index)}
                className={`flex-1 px-4 py-3 font-semibold transition ${
                  currentTab === index
                    ? currentTheme === 'unicorn'
                      ? 'bg-purple-500/20 text-white border-b-2 border-purple-500'
                      : currentTheme === 'light'
                      ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                      : 'bg-blue-900/20 text-blue-300 border-b-2 border-blue-500'
                    : currentTheme === 'unicorn'
                      ? 'text-purple-300 hover:bg-purple-500/10'
                      : currentTheme === 'light'
                      ? 'text-gray-600 hover:bg-gray-50'
                      : 'text-gray-400 hover:bg-gray-700/50'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {currentTab === 0 && (
              <ProviderTypeTab
                formData={formData}
                setFormData={setFormData}
              />
            )}
            {currentTab === 1 && (
              <AuthenticationTab
                formData={formData}
                setFormData={setFormData}
                showSensitive={showSensitive}
                setShowSensitive={setShowSensitive}
              />
            )}
            {currentTab === 2 && (
              <SettingsTab
                formData={formData}
                setFormData={setFormData}
              />
            )}
            {currentTab === 3 && (
              <MicrosoftSetupHelp
                microsoftInstructions={microsoftInstructions}
              />
            )}
          </div>

          {/* Dialog Footer */}
          <div className="p-6 border-t border-current flex items-center justify-end gap-3">
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
              onClick={onSave}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-600 hover:bg-purple-700 text-white'
                  : currentTheme === 'light'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {editingProvider ? 'Update Provider' : 'Create Provider'}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
