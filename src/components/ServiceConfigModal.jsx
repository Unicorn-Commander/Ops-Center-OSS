import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const CONFIG_TEMPLATES = {
  'vllm': {
    'Model Settings': {
      model: { type: 'text', value: '', description: 'Model name or path' },
      max_model_len: { type: 'number', value: 16384, description: 'Maximum model context length' },
      gpu_memory_utilization: { type: 'number', value: 0.95, min: 0.1, max: 1.0, step: 0.05, description: 'GPU memory utilization ratio' },
      tensor_parallel_size: { type: 'number', value: 1, description: 'Number of GPUs for tensor parallelism' }
    },
    'Performance': {
      max_num_seqs: { type: 'number', value: 256, description: 'Maximum number of sequences' },
      max_paddings: { type: 'number', value: 256, description: 'Maximum padding sequences' },
      dtype: { type: 'select', value: 'auto', options: ['auto', 'float16', 'bfloat16'], description: 'Data type for model weights' }
    }
  },
  'open-webui': {
    'General': {
      DEFAULT_USER_ROLE: { type: 'select', value: 'pending', options: ['admin', 'user', 'pending'], description: 'Default role for new users' },
      ENABLE_SIGNUP: { type: 'boolean', value: true, description: 'Allow new user registration' },
      WEBUI_NAME: { type: 'text', value: 'UC-1 Pro Chat', description: 'Application name' }
    },
    'API': {
      OPENAI_API_BASE_URL: { type: 'text', value: 'http://vllm:8000/v1', description: 'OpenAI compatible API endpoint' },
      ENABLE_API_KEY: { type: 'boolean', value: false, description: 'Require API key for access' }
    }
  },
  'whisperx': {
    'Model Settings': {
      model_size: { type: 'select', value: 'base', options: ['tiny', 'base', 'small', 'medium', 'large'], description: 'Whisper model size' },
      device: { type: 'select', value: 'auto', options: ['auto', 'cpu', 'cuda'], description: 'Device for inference' },
      compute_type: { type: 'select', value: 'float16', options: ['float16', 'float32', 'int8'], description: 'Compute type' }
    },
    'Processing': {
      batch_size: { type: 'number', value: 16, description: 'Batch size for processing' },
      diarize: { type: 'boolean', value: true, description: 'Enable speaker diarization' }
    }
  }
};

export default function ServiceConfigModal({ service, onClose, onSave }) {
  const [config, setConfig] = useState({});
  const [originalConfig, setOriginalConfig] = useState({});
  const [activeTab, setActiveTab] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [errors, setErrors] = useState({});

  // Load service configuration
  useEffect(() => {
    const loadConfig = async () => {
      try {
        // In a real implementation, this would fetch from API
        const response = await fetch(`/api/v1/services/${service.name}/config`);
        if (response.ok) {
          const configData = await response.json();
          setConfig(configData);
          setOriginalConfig(configData);
        } else {
          // Use template as fallback
          const template = CONFIG_TEMPLATES[service.name] || {};
          const defaultConfig = {};
          
          Object.keys(template).forEach(section => {
            defaultConfig[section] = {};
            Object.keys(template[section]).forEach(key => {
              defaultConfig[section][key] = template[section][key].value;
            });
          });
          
          setConfig(defaultConfig);
          setOriginalConfig(defaultConfig);
        }
        
        // Set first tab as active
        const template = CONFIG_TEMPLATES[service.name];
        if (template) {
          setActiveTab(Object.keys(template)[0]);
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [service.name]);

  // Check for changes
  useEffect(() => {
    const configChanged = JSON.stringify(config) !== JSON.stringify(originalConfig);
    setHasChanges(configChanged);
  }, [config, originalConfig]);

  const handleConfigChange = (section, key, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));

    // Clear error for this field
    const errorKey = `${section}.${key}`;
    if (errors[errorKey]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  const validateConfig = () => {
    const newErrors = {};
    const template = CONFIG_TEMPLATES[service.name];

    if (template) {
      Object.keys(template).forEach(section => {
        Object.keys(template[section]).forEach(key => {
          const field = template[section][key];
          const value = config[section]?.[key];
          const errorKey = `${section}.${key}`;

          if (field.type === 'number') {
            if (typeof value !== 'number' || isNaN(value)) {
              newErrors[errorKey] = 'Must be a valid number';
            } else if (field.min !== undefined && value < field.min) {
              newErrors[errorKey] = `Must be at least ${field.min}`;
            } else if (field.max !== undefined && value > field.max) {
              newErrors[errorKey] = `Must be at most ${field.max}`;
            }
          }

          if (field.type === 'text' && field.required && (!value || value.trim() === '')) {
            newErrors[errorKey] = 'This field is required';
          }
        });
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateConfig()) {
      return;
    }

    setSaving(true);
    try {
      await onSave(config);
      setOriginalConfig(config);
      setHasChanges(false);
      
      // Show success message
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (error) {
      console.error('Failed to save config:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(originalConfig);
    setErrors({});
  };

  const renderConfigField = (section, key, field) => {
    const value = config[section]?.[key] ?? field.value;
    const errorKey = `${section}.${key}`;
    const hasError = errors[errorKey];

    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleConfigChange(section, key, e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              hasError 
                ? 'border-red-300 dark:border-red-600' 
                : 'border-gray-300 dark:border-gray-600'
            } bg-white dark:bg-gray-800 text-gray-900 dark:text-white`}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            min={field.min}
            max={field.max}
            step={field.step || 1}
            onChange={(e) => handleConfigChange(section, key, parseFloat(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              hasError 
                ? 'border-red-300 dark:border-red-600' 
                : 'border-gray-300 dark:border-gray-600'
            } bg-white dark:bg-gray-800 text-gray-900 dark:text-white`}
          />
        );

      case 'boolean':
        return (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleConfigChange(section, key, e.target.checked)}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              {value ? 'Enabled' : 'Disabled'}
            </span>
          </label>
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleConfigChange(section, key, e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              hasError 
                ? 'border-red-300 dark:border-red-600' 
                : 'border-gray-300 dark:border-gray-600'
            } bg-white dark:bg-gray-800 text-gray-900 dark:text-white`}
          >
            {field.options.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      default:
        return (
          <span className="text-gray-500 italic">
            Unsupported field type: {field.type}
          </span>
        );
    }
  };

  const template = CONFIG_TEMPLATES[service.name];

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent" />
            <span className="text-gray-900 dark:text-white">Loading configuration...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-5/6 overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
            <div className="flex items-center gap-3">
              <Cog6ToothIcon className="h-6 w-6 text-blue-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Service Configuration
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {service.display_name || service.name}
                </p>
              </div>
            </div>
            
            {hasChanges && (
              <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
                <ExclamationTriangleIcon className="h-5 w-5" />
                <span className="text-sm font-medium">Unsaved changes</span>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div className="flex flex-1 overflow-hidden">
            {/* Sidebar Tabs */}
            {template && (
              <div className="w-64 border-r dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-4">
                <div className="space-y-2">
                  {Object.keys(template).map(section => (
                    <button
                      key={section}
                      onClick={() => setActiveTab(section)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        activeTab === section
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {section}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
              {!template ? (
                <div className="text-center py-12">
                  <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    No Configuration Template
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Configuration interface for {service.name} is not yet available.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      {activeTab}
                    </h3>
                    
                    <div className="grid gap-6">
                      {Object.entries(template[activeTab] || {}).map(([key, field]) => {
                        const errorKey = `${activeTab}.${key}`;
                        const hasError = errors[errorKey];
                        
                        return (
                          <div key={key} className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                              {key}
                            </label>
                            
                            {renderConfigField(activeTab, key, field)}
                            
                            {hasError && (
                              <p className="text-sm text-red-600 dark:text-red-400">
                                {hasError}
                              </p>
                            )}
                            
                            {field.description && (
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                {field.description}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          {template && (
            <div className="flex items-center justify-between p-6 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <InformationCircleIcon className="h-4 w-4" />
                <span>
                  Changes require service restart to take effect
                </span>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  disabled={!hasChanges}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 transition-colors"
                >
                  Reset
                </button>
                
                <button
                  onClick={handleSave}
                  disabled={saving || !hasChanges || Object.keys(errors).length > 0}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {saving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckIcon className="h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}