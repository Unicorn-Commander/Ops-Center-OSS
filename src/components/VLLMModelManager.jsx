import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudArrowDownIcon,
  TrashIcon,
  PlayIcon,
  CogIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ServerIcon,
  CpuChipIcon,
  DocumentTextIcon,
  EyeIcon,
  WrenchIcon,
  BoltIcon,
  InformationCircleIcon,
  ClipboardDocumentIcon,
  ArrowsRightLeftIcon
} from '@heroicons/react/24/outline';

// Gemma 3 model configurations with latest compatibility info (Sept 2025)
const GEMMA_MODELS = [
  {
    id: 'RedHatAI/gemma-3-12b-it-quantized.w8a8',
    name: 'Gemma 3 12B IT (INT8)',
    description: 'INT8 quantized, multimodal support, optimized for vLLM 0.8.0+',
    size: '~12GB',
    quantization: 'INT8',
    multimodal: true,
    recommended: true,
    vllm_version: '0.8.0+',
    released: 'June 4, 2025'
  },
  {
    id: 'gaunernst/gemma-3-27b-it-int4-awq',
    name: 'Gemma 3 27B IT (AWQ)',
    description: 'AWQ 4-bit quantized, multimodal with vision capabilities',
    size: '~14GB',
    quantization: 'AWQ',
    multimodal: true
  },
  {
    id: 'MaziyarPanahi/gemma-3-27b-it-GPTQ',
    name: 'Gemma 3 27B IT (GPTQ)',
    description: 'GPTQ quantized, requires vLLM main branch + Transformers ≥4.50',
    size: '~13GB',
    quantization: 'GPTQ',
    multimodal: true,
    requirements: 'vLLM main branch, Transformers ≥4.50'
  },
  {
    id: 'gaunernst/gemma-3-12b-it-int4-awq',
    name: 'Gemma 3 12B IT (AWQ)',
    description: 'Mid-sized AWQ model with vision support',
    size: '~6.6GB',
    quantization: 'AWQ',
    multimodal: true
  },
  {
    id: 'MaziyarPanahi/gemma-3-12b-it-GPTQ',
    name: 'Gemma 3 12B IT (GPTQ)',
    description: 'GPTQ version, requires latest vLLM',
    size: '~6GB',
    quantization: 'GPTQ',
    multimodal: true,
    requirements: 'vLLM main branch, Transformers ≥4.50'
  },
  {
    id: 'google/gemma-2-9b-it',
    name: 'Gemma 2 9B IT',
    description: 'Compact model with vision capabilities',
    size: '~18GB',
    quantization: 'FP16',
    multimodal: true
  },
  {
    id: 'gaunernst/gemma-3-1b-it-int4-awq',
    name: 'Gemma 3 1B IT (AWQ)',
    description: 'Ultra-lightweight, text-only, fast inference',
    size: '~0.5GB',
    quantization: 'AWQ',
    multimodal: false
  }
];

export default function VLLMModelManager() {
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState({});
  const [endpoint, setEndpoint] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [editingParams, setEditingParams] = useState({});
  const [showEndpointInfo, setShowEndpointInfo] = useState(false);
  const [switchingModel, setSwitchingModel] = useState(false);
  const [unifiedManagerAvailable, setUnifiedManagerAvailable] = useState(false);

  useEffect(() => {
    fetchModels();
    fetchEndpoint();
    checkUnifiedManager();
  }, []);

  const checkUnifiedManager = async () => {
    try {
      const response = await fetch('/api/v1/vllm/endpoint');
      const data = await response.json();
      setUnifiedManagerAvailable(data.status !== 'traditional');
    } catch (error) {
      console.error('Error checking unified manager:', error);
    }
  };

  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/vllm/models');
      const data = await response.json();
      
      if (data.data) {
        setModels(data.data);
        const active = data.data.find(m => m.active || m.metadata?.active);
        if (active) {
          setActiveModel(active.id || active.model_id);
        }
      }
    } catch (error) {
      console.error('Error fetching models:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEndpoint = async () => {
    try {
      const response = await fetch('/api/v1/vllm/endpoint');
      const data = await response.json();
      setEndpoint(data);
    } catch (error) {
      console.error('Error fetching endpoint:', error);
    }
  };

  const downloadModel = async (modelId, quantization = null) => {
    setDownloading(prev => ({ ...prev, [modelId]: true }));
    
    try {
      const response = await fetch('/api/v1/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelId,
          backend: 'vllm',
          settings: { quantization }
        })
      });
      
      if (!response.ok) throw new Error('Download failed');
      
      const data = await response.json();
      
      // Poll for download progress
      const pollProgress = setInterval(async () => {
        try {
          const statusResponse = await fetch('/api/v1/models/downloads');
          const downloads = await statusResponse.json();
          
          if (downloads[data.task_id]) {
            const task = downloads[data.task_id];
            
            if (task.status === 'completed') {
              clearInterval(pollProgress);
              setDownloading(prev => ({ ...prev, [modelId]: false }));
              fetchModels();
            } else if (task.status === 'failed') {
              clearInterval(pollProgress);
              setDownloading(prev => ({ ...prev, [modelId]: false }));
              alert(`Download failed: ${task.error || 'Unknown error'}`);
            }
          }
        } catch (error) {
          console.error('Error checking download status:', error);
        }
      }, 5000);
      
    } catch (error) {
      console.error('Download error:', error);
      setDownloading(prev => ({ ...prev, [modelId]: false }));
      alert('Failed to start download');
    }
  };

  const switchModel = async (modelId) => {
    setSwitchingModel(true);
    
    try {
      const response = await fetch('/api/v1/vllm/switch-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      });
      
      if (!response.ok) throw new Error('Switch failed');
      
      const data = await response.json();
      
      if (data.status === 'success' || data.status === 'activated') {
        setActiveModel(modelId);
        fetchEndpoint();
        alert(`Successfully switched to ${modelId}`);
      } else if (data.status === 'already_active') {
        alert('Model is already active');
      }
      
    } catch (error) {
      console.error('Switch error:', error);
      alert('Failed to switch model');
    } finally {
      setSwitchingModel(false);
      fetchModels();
    }
  };

  const deleteModel = async (modelId) => {
    if (!confirm(`Are you sure you want to delete ${modelId}?`)) return;
    
    try {
      const response = await fetch(`/api/v1/models/vllm/${encodeURIComponent(modelId)}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Delete failed');
      
      fetchModels();
      alert('Model deleted successfully');
      
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete model');
    }
  };

  const editModelParams = async (modelId) => {
    try {
      const response = await fetch('/api/v1/models/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelId,
          backend: 'vllm',
          settings: editingParams[modelId] || {}
        })
      });
      
      if (!response.ok) throw new Error('Update failed');
      
      alert('Model parameters updated');
      setSelectedModel(null);
      setEditingParams({});
      
    } catch (error) {
      console.error('Update error:', error);
      alert('Failed to update parameters');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="space-y-6">
      {/* Header with Unified Manager Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <ServerIcon className="h-8 w-8" />
              vLLM Model Manager
            </h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Unified endpoint with fast model switching for all vLLM models
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {unifiedManagerAvailable ? (
              <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm flex items-center gap-1">
                <CheckCircleIcon className="h-4 w-4" />
                Unified Manager Active
              </span>
            ) : (
              <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-full text-sm flex items-center gap-1">
                <XCircleIcon className="h-4 w-4" />
                Traditional Mode
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Endpoint Information */}
      {endpoint && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6"
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Active vLLM Endpoint
              </h3>
              
              {endpoint.status === 'active' ? (
                <div className="space-y-2">
                  <p className="text-blue-800 dark:text-blue-200">
                    <strong>Model:</strong> {endpoint.model_id}
                  </p>
                  <p className="text-blue-800 dark:text-blue-200">
                    <strong>Endpoint:</strong> {endpoint.external_endpoint}
                  </p>
                  <p className="text-blue-800 dark:text-blue-200">
                    <strong>Docker:</strong> {endpoint.docker_endpoint}
                  </p>
                  
                  {endpoint.capabilities && (
                    <div className="flex gap-2 mt-2">
                      {endpoint.capabilities.chat && (
                        <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded text-xs">Chat</span>
                      )}
                      {endpoint.capabilities.vision && (
                        <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded text-xs">Vision</span>
                      )}
                      {endpoint.capabilities.tools && (
                        <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded text-xs">Tools</span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-blue-700 dark:text-blue-300">
                  No model currently active. Select a model below to activate.
                </p>
              )}
            </div>
            
            <button
              onClick={() => setShowEndpointInfo(!showEndpointInfo)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <InformationCircleIcon className="h-5 w-5" />
              OpenWebUI Config
            </button>
          </div>
          
          {/* OpenWebUI Configuration */}
          {showEndpointInfo && endpoint.openwebui_config && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800"
            >
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                OpenWebUI Connection Settings:
              </h4>
              <div className="bg-white dark:bg-gray-800 rounded p-4 font-mono text-sm">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Name:</span>
                    <span>{endpoint.openwebui_config.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">URL:</span>
                    <div className="flex items-center gap-2">
                      <span>{endpoint.openwebui_config.url}</span>
                      <button
                        onClick={() => copyToClipboard(endpoint.openwebui_config.url)}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">API Key:</span>
                    <div className="flex items-center gap-2">
                      <span>{endpoint.openwebui_config.api_key || 'Not required'}</span>
                      {endpoint.openwebui_config.api_key && (
                        <button
                          onClick={() => copyToClipboard(endpoint.openwebui_config.api_key)}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Gemma 3 Models Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Gemma 3 Models (Latest Compatibility - Sept 2025)
        </h3>
        
        <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Note:</strong> GGUF format not yet supported. Use AWQ, GPTQ, or INT8 quantized versions.
            GPTQ models require vLLM main branch and Transformers ≥4.50.
          </p>
        </div>
        
        <div className="grid gap-4">
          {GEMMA_MODELS.map(model => (
            <motion.div
              key={model.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {model.name}
                    </h4>
                    {model.recommended && (
                      <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded">
                        Recommended
                      </span>
                    )}
                    {model.multimodal && (
                      <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded flex items-center gap-1">
                        <EyeIcon className="h-3 w-3" />
                        Multimodal
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {model.description}
                  </p>
                  
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>💾 {model.size}</span>
                    <span>🔧 {model.quantization}</span>
                    {model.vllm_version && <span>📦 vLLM {model.vllm_version}</span>}
                    {model.released && <span>📅 {model.released}</span>}
                  </div>
                  
                  {model.requirements && (
                    <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                      ⚠️ Requires: {model.requirements}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 ml-4">
                  {models.find(m => m.id === model.id) ? (
                    <>
                      {activeModel === model.id ? (
                        <span className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm flex items-center gap-1">
                          <CheckCircleIcon className="h-4 w-4" />
                          Active
                        </span>
                      ) : (
                        <button
                          onClick={() => switchModel(model.id)}
                          disabled={switchingModel}
                          className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center gap-1 disabled:opacity-50"
                        >
                          <ArrowsRightLeftIcon className="h-4 w-4" />
                          {switchingModel ? 'Switching...' : 'Switch To'}
                        </button>
                      )}
                      <button
                        onClick={() => deleteModel(model.id)}
                        className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => downloadModel(model.id, model.quantization)}
                      disabled={downloading[model.id]}
                      className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1 disabled:opacity-50"
                    >
                      <CloudArrowDownIcon className="h-4 w-4" />
                      {downloading[model.id] ? 'Downloading...' : 'Download'}
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Installed Models */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          All Installed Models
        </h3>
        
        {loading ? (
          <div className="flex justify-center py-8">
            <ArrowPathIcon className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : models.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No models installed yet. Download models from the sections above.
          </p>
        ) : (
          <div className="space-y-4">
            {models.map(model => (
              <motion.div
                key={model.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="border dark:border-gray-700 rounded-lg p-4"
              >
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {model.name || model.id}
                      </h4>
                      {(model.active || model.metadata?.active) && (
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                          Active
                        </span>
                      )}
                      {model.metadata?.status && (
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          model.metadata.status === 'running' 
                            ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                            : model.metadata.status === 'loading'
                            ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                            : 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200'
                        }`}>
                          {model.metadata.status}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex gap-4 mt-2 text-sm text-gray-500">
                      {model.metadata?.architecture && (
                        <span>🏗️ {model.metadata.architecture}</span>
                      )}
                      {model.metadata?.quantization && (
                        <span>🔧 {model.metadata.quantization}</span>
                      )}
                      {model.metadata?.max_model_len && (
                        <span>📏 {model.metadata.max_model_len} tokens</span>
                      )}
                      {model.metadata?.multimodal && (
                        <span>👁️ Multimodal</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    {!(model.active || model.metadata?.active) && (
                      <button
                        onClick={() => switchModel(model.id)}
                        disabled={switchingModel}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1 disabled:opacity-50"
                      >
                        <PlayIcon className="h-4 w-4" />
                        Activate
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setSelectedModel(model.id);
                        setEditingParams({ [model.id]: {} });
                      }}
                      className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      <CogIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteModel(model.id)}
                      className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Model Parameters Editor Modal */}
      <AnimatePresence>
        {selectedModel && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setSelectedModel(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Edit Model Parameters: {selectedModel}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Model Length
                  </label>
                  <input
                    type="number"
                    placeholder="16384"
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        max_model_len: parseInt(e.target.value)
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    GPU Memory Utilization
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    placeholder="0.95"
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        gpu_memory_utilization: parseFloat(e.target.value)
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tensor Parallel Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    placeholder="1"
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        tensor_parallel_size: parseInt(e.target.value)
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Quantization Method
                  </label>
                  <select
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        quantization: e.target.value
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="">None</option>
                    <option value="awq">AWQ</option>
                    <option value="gptq">GPTQ</option>
                    <option value="squeezellm">SqueezeLLM</option>
                    <option value="fp8">FP8</option>
                  </select>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="trust-remote-code"
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        trust_remote_code: e.target.checked
                      }
                    })}
                    className="mr-2"
                  />
                  <label htmlFor="trust-remote-code" className="text-sm text-gray-700 dark:text-gray-300">
                    Trust Remote Code
                  </label>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="enable-multimodal"
                    onChange={(e) => setEditingParams({
                      ...editingParams,
                      [selectedModel]: {
                        ...editingParams[selectedModel],
                        multimodal: e.target.checked
                      }
                    })}
                    className="mr-2"
                  />
                  <label htmlFor="enable-multimodal" className="text-sm text-gray-700 dark:text-gray-300">
                    Enable Multimodal (Vision)
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setSelectedModel(null)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={() => editModelParams(selectedModel)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Save Changes
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}