import React from 'react';
import { InformationCircleIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';
import { useToast } from '../../Toast';

/**
 * MicrosoftSetupHelp - Microsoft 365 OAuth2 setup instructions
 *
 * Displays step-by-step instructions for configuring Microsoft 365 OAuth2
 * with copyable values for client ID, redirect URIs, etc.
 *
 * @param {Object} props
 * @param {Object} props.microsoftInstructions - Setup instructions from backend
 */
export default function MicrosoftSetupHelp({ microsoftInstructions }) {
  const { currentTheme } = useTheme();
  const toast = useToast();

  if (!microsoftInstructions) {
    return (
      <div className={`text-center py-8 ${
        currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
      }`}>
        Setup instructions are available for Microsoft 365 OAuth2
      </div>
    );
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      {/* Reuse Existing App Notice */}
      <div className={`p-4 rounded-lg ${
        currentTheme === 'unicorn'
          ? 'bg-blue-500/10 border border-blue-500/30'
          : currentTheme === 'light'
          ? 'bg-blue-50 border border-blue-200'
          : 'bg-blue-900/20 border border-blue-600'
      }`}>
        <div className="flex items-start gap-3">
          <InformationCircleIcon className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className={`font-semibold mb-2 ${
              currentTheme === 'unicorn' ? 'text-blue-300' : currentTheme === 'light' ? 'text-blue-900' : 'text-blue-300'
            }`}>
              Reuse Existing Azure AD Application
            </h3>
            <p className={`text-sm ${
              currentTheme === 'unicorn' ? 'text-blue-200' : currentTheme === 'light' ? 'text-blue-800' : 'text-blue-200'
            }`}>
              You can reuse the same Azure AD app that's configured for Keycloak SSO. Just add the Mail.Send permission.
            </p>
          </div>
        </div>
      </div>

      {/* Step-by-Step Instructions */}
      <div>
        <h3 className={`font-semibold mb-3 ${
          currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
        }`}>
          Step-by-Step Setup Instructions
        </h3>
        <ol className="space-y-4">
          {microsoftInstructions.steps?.map((step, index) => (
            <li key={index} className="flex gap-3">
              <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-500 text-white'
                  : currentTheme === 'light'
                  ? 'bg-blue-500 text-white'
                  : 'bg-blue-600 text-white'
              }`}>
                {index + 1}
              </span>
              <div className="flex-1">
                <p className={currentTheme === 'unicorn' ? 'text-purple-100' : currentTheme === 'light' ? 'text-gray-800' : 'text-gray-200'}>
                  {step.text}
                </p>
                {step.copyable && (
                  <div className="mt-2">
                    <div className={`flex items-center gap-2 p-3 rounded font-mono text-sm ${
                      currentTheme === 'unicorn'
                        ? 'bg-purple-900/30 border border-purple-500/30'
                        : currentTheme === 'light'
                        ? 'bg-gray-100 border border-gray-300'
                        : 'bg-gray-800 border border-gray-600'
                    }`}>
                      <code className="flex-1 overflow-x-auto">{step.value}</code>
                      <button
                        onClick={() => {
                          copyToClipboard(step.value);
                          toast.success('Copied to clipboard!');
                        }}
                        className="p-1 hover:bg-white/10 rounded"
                      >
                        <ClipboardDocumentIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
