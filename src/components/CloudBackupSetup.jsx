import React, { useState } from 'react';
import {
  CloudIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  KeyIcon
} from '@heroicons/react/24/outline';

/**
 * CloudBackupSetup Component
 *
 * Configure cloud storage providers for backup synchronization.
 * Supports S3, Backblaze B2, and Wasabi.
 */
export default function CloudBackupSetup({ onSave, onTest, existingConfig = null }) {
  const [provider, setProvider] = useState(existingConfig?.provider || 's3');
  const [config, setConfig] = useState(existingConfig || {
    provider: 's3',
    access_key: '',
    secret_key: '',
    bucket_name: '',
    region: 'us-east-1',
    endpoint: '',
    enabled: false
  });
  const [isTesting, setIsTesting] = useState(false);
  const [testStatus, setTestStatus] = useState(null); // null, 'success', 'error'
  const [testMessage, setTestMessage] = useState('');
  const [showSecrets, setShowSecrets] = useState(false);

  const providers = {
    s3: {
      name: 'Amazon S3',
      icon: '🪣',
      regions: ['us-east-1', 'us-west-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1'],
      needsEndpoint: false,
      docs: 'https://docs.aws.amazon.com/s3/'
    },
    backblaze: {
      name: 'Backblaze B2',
      icon: '☁️',
      regions: [],
      needsEndpoint: true,
      defaultEndpoint: 's3.us-west-004.backblazeb2.com',
      docs: 'https://www.backblaze.com/b2/docs/'
    },
    wasabi: {
      name: 'Wasabi',
      icon: '🗄️',
      regions: ['us-east-1', 'us-east-2', 'us-west-1', 'eu-central-1', 'ap-northeast-1'],
      needsEndpoint: true,
      defaultEndpoint: 's3.wasabisys.com',
      docs: 'https://wasabi.com/help/'
    }
  };

  const handleProviderChange = (newProvider) => {
    setProvider(newProvider);
    setConfig({
      ...config,
      provider: newProvider,
      endpoint: providers[newProvider].defaultEndpoint || '',
      region: providers[newProvider].regions[0] || 'us-east-1'
    });
    setTestStatus(null);
  };

  const handleConfigChange = (field, value) => {
    setConfig({
      ...config,
      [field]: value
    });
    setTestStatus(null); // Reset test status when config changes
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestStatus(null);
    setTestMessage('');

    try {
      const result = await onTest(config);
      if (result.success) {
        setTestStatus('success');
        setTestMessage(result.message || 'Connection successful! Bucket accessible.');
      } else {
        setTestStatus('error');
        setTestMessage(result.message || 'Connection failed. Please check your credentials.');
      }
    } catch (error) {
      setTestStatus('error');
      setTestMessage(error.message || 'Failed to test connection');
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = () => {
    if (testStatus !== 'success') {
      alert('Please test the connection before saving');
      return;
    }
    onSave(config);
  };

  const isValid = () => {
    return config.access_key && config.secret_key && config.bucket_name &&
           (providers[provider].needsEndpoint ? config.endpoint : true);
  };

  return (
    <div className="space-y-6">
      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Cloud Storage Provider
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {Object.entries(providers).map(([key, providerInfo]) => (
            <button
              key={key}
              onClick={() => handleProviderChange(key)}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                provider === key
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{providerInfo.icon}</span>
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {providerInfo.name}
                  </div>
                  {provider === key && (
                    <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      Selected
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration Form */}
      <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            {providers[provider].name} Configuration
          </h3>
          <a
            href={providers[provider].docs}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
          >
            <InformationCircleIcon className="h-4 w-4" />
            Documentation
          </a>
        </div>

        {/* Access Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Access Key ID
          </label>
          <div className="relative">
            <input
              type={showSecrets ? 'text' : 'password'}
              value={config.access_key}
              onChange={(e) => handleConfigChange('access_key', e.target.value)}
              placeholder="Enter your access key"
              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
            <KeyIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
        </div>

        {/* Secret Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Secret Access Key
          </label>
          <div className="relative">
            <input
              type={showSecrets ? 'text' : 'password'}
              value={config.secret_key}
              onChange={(e) => handleConfigChange('secret_key', e.target.value)}
              placeholder="Enter your secret key"
              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
            <KeyIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          <div className="mt-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showSecrets}
                onChange={(e) => setShowSecrets(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                Show credentials
              </span>
            </label>
          </div>
        </div>

        {/* Bucket Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Bucket Name
          </label>
          <input
            type="text"
            value={config.bucket_name}
            onChange={(e) => handleConfigChange('bucket_name', e.target.value)}
            placeholder="my-backup-bucket"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Region (for S3 and Wasabi) */}
        {providers[provider].regions.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Region
            </label>
            <select
              value={config.region}
              onChange={(e) => handleConfigChange('region', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              {providers[provider].regions.map(region => (
                <option key={region} value={region}>{region}</option>
              ))}
            </select>
          </div>
        )}

        {/* Endpoint (for Backblaze and Wasabi) */}
        {providers[provider].needsEndpoint && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Endpoint URL
            </label>
            <input
              type="text"
              value={config.endpoint}
              onChange={(e) => handleConfigChange('endpoint', e.target.value)}
              placeholder={providers[provider].defaultEndpoint}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Default: {providers[provider].defaultEndpoint}
            </p>
          </div>
        )}

        {/* Enable/Disable */}
        <div className="pt-4 border-t dark:border-gray-700">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => handleConfigChange('enabled', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">
              Enable automatic cloud backup sync
            </span>
          </label>
          <p className="ml-6 text-xs text-gray-500 dark:text-gray-400 mt-1">
            Backups will be automatically uploaded to {providers[provider].name} after creation
          </p>
        </div>
      </div>

      {/* Test Connection Button */}
      <div>
        <button
          onClick={handleTestConnection}
          disabled={!isValid() || isTesting}
          className="w-full px-4 py-3 bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
        >
          {isTesting ? (
            <>
              <ArrowPathIcon className="h-5 w-5 animate-spin" />
              Testing Connection...
            </>
          ) : (
            <>
              <CloudIcon className="h-5 w-5" />
              Test Connection
            </>
          )}
        </button>
      </div>

      {/* Test Status */}
      {testStatus === 'success' && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-500" />
            <div>
              <h4 className="text-sm font-medium text-green-800 dark:text-green-400">
                Connection Successful
              </h4>
              <p className="text-sm text-green-700 dark:text-green-500 mt-1">
                {testMessage}
              </p>
            </div>
          </div>
        </div>
      )}

      {testStatus === 'error' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-500 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-red-800 dark:text-red-400">
                Connection Failed
              </h4>
              <p className="text-sm text-red-700 dark:text-red-500 mt-1">
                {testMessage}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-400">
            <strong>Getting Started:</strong>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Create a bucket in your cloud provider console</li>
              <li>Generate API credentials (access key and secret key)</li>
              <li>Grant the credentials permissions to: PutObject, GetObject, DeleteObject, ListBucket</li>
              <li>Test the connection before saving</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-700">
        <button
          onClick={handleSave}
          disabled={testStatus !== 'success'}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
}
