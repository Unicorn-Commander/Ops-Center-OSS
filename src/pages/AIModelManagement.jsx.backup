import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  CubeIcon,
  MagnifyingGlassIcon, 
  CloudArrowDownIcon,
  TrashIcon,
  PlayIcon,
  StopIcon,
  CogIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ChartBarIcon,
  DocumentTextIcon,
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  FunnelIcon,
  ArrowsUpDownIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  ArrowTopRightOnSquareIcon,
  ServerIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import { useSystem } from '../contexts/SystemContext';
import { useToast } from '../components/Toast';
import ModelSettingsForm from '../components/ModelSettingsForm';
import modelApi from '../services/modelApi';
import { serviceInfo, modelTips } from '../data/serviceInfo';
import SkeletonCard, { SkeletonTable } from '../components/SkeletonCard';

export default function AIModelManagement() {
  const { systemStatus } = useSystem();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('vllm');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showModelSettings, setShowModelSettings] = useState(null); // For per-model settings
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('downloads'); // downloads, likes, lastModified
  const [installedModels, setInstalledModels] = useState({ 
    vllm: [], 
    ollama: [], 
    embeddings: [], 
    reranker: [] 
  });
  const [loadingModels, setLoadingModels] = useState(false); // Start with instant display
  const [filters, setFilters] = useState({
    quantization: '',
    minSize: '',
    maxSize: '',
    license: '',
    task: '',
    language: ''
  });
  
  // Global settings
  const [vllmSettings, setVllmSettings] = useState({
    gpu_memory_utilization: 0.95,
    max_model_len: 16384,
    tensor_parallel_size: 1,
    quantization: 'auto',
    dtype: 'auto',
    trust_remote_code: false,
    download_dir: '/home/ucadmin/UC-1-Pro/volumes/vllm_models',
    cpu_offload_gb: 0,
    enforce_eager: false,
    max_num_batched_tokens: null,
    max_num_seqs: 256,
    disable_log_stats: false,
    disable_log_requests: false
  });
  
  const [ollamaSettings, setOllamaSettings] = useState({
    models_path: '/home/ucadmin/.ollama/models',
    gpu_layers: -1,
    context_size: 2048,
    num_thread: 0,
    use_mmap: true,
    use_mlock: false,
    repeat_penalty: 1.1,
    temperature: 0.8,
    top_k: 40,
    top_p: 0.9,
    seed: -1
  });
  
  const [embeddingsSettings, setEmbeddingsSettings] = useState({
    model_name: 'nomic-ai/nomic-embed-text-v1.5',
    device: 'cpu',
    max_length: 8192,
    normalize: true,
    batch_size: 32,
    models_cache_dir: '/home/ucadmin/.cache/huggingface',
    trust_remote_code: true
  });
  
  const [rerankerSettings, setRerankerSettings] = useState({
    model_name: 'mixedbread-ai/mxbai-rerank-large-v1',
    device: 'cpu',
    max_length: 512,
    batch_size: 32,
    models_cache_dir: '/home/ucadmin/.cache/huggingface',
    trust_remote_code: true
  });
  
  // Per-model settings overrides
  const [modelOverrides, setModelOverrides] = useState({});
  const [ollamaModels, setOllamaModels] = useState([]);
  const [downloadProgress, setDownloadProgress] = useState({});

  // Search timer for debouncing
  const [searchTimer, setSearchTimer] = useState(null);

  const loadInstalledModels = useCallback(async () => {
    setLoadingModels(true);
    try {
      // Load models for vLLM and Ollama from existing API
      const models = await modelApi.getInstalledModels();
      
      // Load cached models for embeddings and reranker services only if needed
      const promises = [];
      if (activeTab === 'embeddings' || activeTab === 'vllm') {
        promises.push(modelApi.getCachedModels('embeddings').catch(() => ({ cached_models: [] })));
      }
      if (activeTab === 'reranker' || activeTab === 'vllm') {
        promises.push(modelApi.getCachedModels('reranker').catch(() => ({ cached_models: [] })));
      }
      
      const [embeddingsModels, rerankerModels] = await Promise.all([
        ...promises,
        Promise.resolve({ cached_models: [] }),
        Promise.resolve({ cached_models: [] })
      ].slice(0, 2));
      
      setInstalledModels(prevModels => ({
        ...prevModels,
        ...models,
        embeddings: embeddingsModels?.cached_models || prevModels.embeddings || [],
        reranker: rerankerModels?.cached_models || prevModels.reranker || []
      }));
      
      // Also load any active downloads
      const downloads = await modelApi.getAllDownloads().catch(() => ({}));
      // Update download progress state
      const progressMap = {};
      Object.entries(downloads || {}).forEach(([taskId, task]) => {
        if (task?.status === 'downloading' && task?.model_id) {
          progressMap[task.model_id] = task.progress || 0;
        }
      });
      setDownloadProgress(progressMap);
    } catch (error) {
      console.error('Failed to load models:', error);
      // Keep existing models on error
    } finally {
      setLoadingModels(false);
    }
  }, [activeTab]);

  // Load installed models and settings on mount
  useEffect(() => {
    // Allow page to render first, then load data
    const timer = setTimeout(() => {
      setLoadingModels(true);
      loadInstalledModels();
      loadGlobalSettings();
    }, 200);
    
    return () => clearTimeout(timer);
  }, [loadInstalledModels]);

  // Reload models when tab changes
  useEffect(() => {
    loadInstalledModels();
  }, [activeTab, loadInstalledModels]);

  const loadGlobalSettings = async () => {
    try {
      const [vllm, ollama] = await Promise.all([
        modelApi.getGlobalSettings('vllm').catch(err => {
          console.warn('Failed to load vLLM settings:', err);
          return vllmSettings; // Keep current settings
        }),
        modelApi.getGlobalSettings('ollama').catch(err => {
          console.warn('Failed to load Ollama settings:', err);
          return ollamaSettings; // Keep current settings
        })
      ]);
      setVllmSettings(prevSettings => ({ ...prevSettings, ...vllm }));
      setOllamaSettings(prevSettings => ({ ...prevSettings, ...ollama }));
    } catch (error) {
      console.error('Failed to load settings:', error);
      // Settings will remain at their default values
    }
  };

  // Memoized service-specific filters
  const currentServiceFilters = useMemo(() => {
    if (!serviceInfo[activeTab]?.defaultFilters) return {};
    return serviceInfo[activeTab].defaultFilters;
  }, [activeTab]);

  // Get service-specific filters
  const getServiceFilters = useCallback((service) => {
    if (!serviceInfo[service]?.defaultFilters) return {};
    return serviceInfo[service].defaultFilters;
  }, []);

  // Advanced search from Hugging Face
  useEffect(() => {
    if (searchTimer) {
      clearTimeout(searchTimer);
    }
    
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearching(false);
      return;
    }
    
    setSearching(true);
    
    const timer = setTimeout(async () => {
      try {
        // Get service-specific default filters
        const defaultFilters = currentServiceFilters;
        
        // Build search parameters with filters
        let searchUrl = `https://huggingface.co/api/models?search=${encodeURIComponent(searchQuery)}`;
        
        // Add service-specific default filters
        if (defaultFilters.task) {
          searchUrl += `&pipeline_tag=${defaultFilters.task}`;
        }
        
        // Add user-selected filters (override defaults if specified)
        if (filters.task) {
          searchUrl += `&pipeline_tag=${filters.task}`;
        }
        if (filters.language) {
          searchUrl += `&language=${filters.language}`;
        }
        if (filters.license) {
          searchUrl += `&license=${filters.license}`;
        }
        
        searchUrl += '&limit=100'; // Get more results for filtering
        
        const response = await fetch(searchUrl);
        
        if (response.ok) {
          let data = await response.json();
          
          // Apply client-side filters
          data = data.filter(model => {
            // Service-specific filtering
            if (activeTab === 'vllm') {
              // vLLM: prefer quantized models (AWQ, GPTQ, FP8)
              const isTextGeneration = model.pipeline_tag === 'text-generation' || 
                                     model.tags?.some(tag => tag.toLowerCase().includes('text-generation'));
              if (!isTextGeneration) return false;
              
              // Boost models with quantization tags
              if (defaultFilters.quantization && !filters.quantization) {
                const hasQuantization = model.tags?.some(tag => 
                  defaultFilters.quantization.some(q => tag.toLowerCase().includes(q))
                );
                model._hasQuantization = hasQuantization;
              }
            } else if (activeTab === 'ollama') {
              // Ollama: prefer GGUF models
              if (defaultFilters.format && !filters.quantization) {
                const hasGGUF = model.tags?.some(tag => 
                  tag.toLowerCase().includes('gguf')
                ) || model.modelId.toLowerCase().includes('gguf');
                model._hasGGUF = hasGGUF;
              }
            } else if (activeTab === 'embeddings') {
              // Embeddings: filter for sentence-transformers models
              if (defaultFilters.library) {
                const hasLibrary = model.tags?.some(tag => 
                  tag.toLowerCase().includes(defaultFilters.library)
                ) || model.library_name === defaultFilters.library ||
                  model.pipeline_tag === 'feature-extraction';
                if (!hasLibrary) return false;
              }
            } else if (activeTab === 'reranker') {
              // Reranker: filter for cross-encoder models or reranking task
              const isReranker = model.tags?.some(tag => 
                tag.toLowerCase().includes('rerank') || 
                tag.toLowerCase().includes('cross-encoder')
              ) || model.pipeline_tag === 'sentence-similarity' ||
                model.modelId.toLowerCase().includes('rerank') ||
                model.modelId.toLowerCase().includes('cross-encoder');
              if (!isReranker) return false;
            }
            
            // User-specified quantization filter
            if (filters.quantization) {
              const hasQuantization = model.tags?.some(tag => 
                tag.toLowerCase().includes(filters.quantization.toLowerCase())
              );
              if (!hasQuantization) return false;
            }
            
            // Size filters (if available in metadata)
            if (filters.minSize || filters.maxSize) {
              const sizeMatch = model.modelId.match(/(\d+)B/i);
              if (sizeMatch) {
                const size = parseInt(sizeMatch[1]);
                if (filters.minSize && size < parseInt(filters.minSize)) return false;
                if (filters.maxSize && size > parseInt(filters.maxSize)) return false;
              }
            }
            
            return true;
          });
          
          // Sort results with compatibility boost
          data.sort((a, b) => {
            // First, prioritize compatible models
            const aCompatible = a._hasQuantization || a._hasGGUF || false;
            const bCompatible = b._hasQuantization || b._hasGGUF || false;
            
            if (aCompatible && !bCompatible) return -1;
            if (!aCompatible && bCompatible) return 1;
            
            // Then sort by user preference
            switch (sortBy) {
              case 'downloads':
                return (b.downloads || 0) - (a.downloads || 0);
              case 'likes':
                return (b.likes || 0) - (a.likes || 0);
              case 'lastModified':
                return new Date(b.lastModified || 0) - new Date(a.lastModified || 0);
              default:
                return 0;
            }
          });
          
          setSearchResults(data);
        }
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, searchQuery.length > 2 ? 300 : 1000); // Longer delay for short queries
    
    setSearchTimer(timer);
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [searchQuery, activeTab, filters, sortBy]);

  const downloadVllmModel = async (modelId) => {
    try {
      const result = await modelApi.downloadModel(modelId, 'vllm', vllmSettings);
      
      // Monitor download progress
      if (result.task_id) {
        monitorDownloadProgress(result.task_id, modelId);
      }
    } catch (error) {
      console.error('Download error:', error);
      toast.error(`Failed to start download: ${error.message}`);
    }
  };

  const downloadOllamaModel = async (modelName) => {
    try {
      const result = await modelApi.downloadModel(modelName, 'ollama');
      
      // Monitor download progress
      if (result.task_id) {
        monitorDownloadProgress(result.task_id, modelName);
      }
    } catch (error) {
      console.error('Ollama download error:', error);
      toast.error(`Failed to start download: ${error.message}`);
    }
  };

  const monitorDownloadProgress = async (taskId, modelId) => {
    try {
      await modelApi.monitorDownload(taskId, (status) => {
        setDownloadProgress(prev => ({
          ...prev,
          [modelId]: status.progress || 0
        }));
        
        if (status.status === 'completed') {
          // Reload models after successful download
          loadInstalledModels();
          // Clear download progress after a delay
          setTimeout(() => {
            setDownloadProgress(prev => {
              const newProgress = { ...prev };
              delete newProgress[modelId];
              return newProgress;
            });
          }, 2000);
        }
      });
    } catch (error) {
      console.error('Error monitoring download:', error);
      setDownloadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[modelId];
        return newProgress;
      });
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatModelSize = (model) => {
    if (activeTab === 'ollama') {
      return formatBytes(model.size);
    }
    // For Hugging Face models, estimate size
    return model.safetensors ? 'Safetensors' : 'Unknown';
  };

  // Save model-specific settings
  const saveModelSettings = async (modelId, settings) => {
    try {
      await modelApi.updateModelSettings(modelId, activeTab, settings);
      
      // Update local state
      setModelOverrides(prev => ({
        ...prev,
        [modelId]: settings
      }));
      setShowModelSettings(null);
      
      // Reload models to get updated override status
      loadInstalledModels();
    } catch (error) {
      console.error('Failed to save model settings:', error);
      toast.error(`Failed to save settings: ${error.message}`);
    }
  };

  // Get effective settings for a model (global + overrides)
  const getEffectiveSettings = (modelId) => {
    const globalSettings = activeTab === 'vllm' ? vllmSettings : ollamaSettings;
    const overrides = modelOverrides[modelId] || {};
    return { ...globalSettings, ...overrides };
  };

  // Activate a model
  const activateModel = async (backend, modelId) => {
    try {
      const result = await modelApi.activateModel(backend, modelId);
      toast.success(`Model activated: ${result.message || 'Success'}`);
      loadInstalledModels();
    } catch (error) {
      console.error('Failed to activate model:', error);
      toast.error(`Failed to activate model: ${error.message}`);
    }
  };

  // Delete a model
  const deleteModel = async (backend, modelId) => {
    if (!confirm(`Are you sure you want to delete this model?\n\n${modelId}`)) {
      return;
    }
    
    try {
      await modelApi.deleteModel(backend, modelId);
      toast.success('Model deleted successfully');
      loadInstalledModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
      toast.error(`Failed to delete model: ${error.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          AI Model Management
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Manage models for vLLM, Ollama, Embedding, and Reranker services with granular control
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('vllm')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'vllm'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CubeIcon className="h-5 w-5" />
              vLLM Models
            </div>
          </button>
          <button
            onClick={() => setActiveTab('ollama')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'ollama'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CubeIcon className="h-5 w-5" />
              Ollama Models
            </div>
          </button>
          <button
            onClick={() => setActiveTab('embeddings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'embeddings'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CubeIcon className="h-5 w-5" />
              iGPU Embeddings
            </div>
          </button>
          <button
            onClick={() => setActiveTab('reranker')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'reranker'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CubeIcon className="h-5 w-5" />
              iGPU Reranker
            </div>
          </button>
        </nav>
      </div>

      {/* Service Information Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              {activeTab === 'vllm' || activeTab === 'ollama' ? (
                <ServerIcon className="h-8 w-8 text-blue-500" />
              ) : (
                <CpuChipIcon className="h-8 w-8 text-purple-500" />
              )}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {serviceInfo[activeTab].name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {activeTab === 'vllm' || activeTab === 'ollama' ? 'GPU Accelerated' : 'Intel iGPU Optimized'}
                </p>
              </div>
            </div>
            
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              {serviceInfo[activeTab].description}
            </p>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Key Features:</h4>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  {serviceInfo[activeTab]?.features?.slice(0, 3).map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Compatible Models:</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {serviceInfo[activeTab]?.compatibleModels}
                </p>
                
                <div className="mt-3 bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                  <p className="text-xs text-blue-800 dark:text-blue-200">
                    <strong>Tip:</strong> {modelTips[activeTab]?.selection}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              {serviceInfo[activeTab]?.homepage && (
                <a
                  href={serviceInfo[activeTab]?.homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  Homepage
                </a>
              )}
              {serviceInfo[activeTab]?.github && (
                <a
                  href={serviceInfo[activeTab]?.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  GitHub
                </a>
              )}
              {serviceInfo[activeTab]?.docs && (
                <a
                  href={serviceInfo[activeTab]?.docs}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <DocumentTextIcon className="h-4 w-4" />
                  Documentation
                </a>
              )}
            </div>
          </div>
          
          <div className="ml-4">
            <div className="relative group">
              <QuestionMarkCircleIcon className="h-6 w-6 text-gray-400 hover:text-gray-600 cursor-help" />
              <div className="absolute right-0 mt-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                <div className="space-y-2">
                  <p><strong>Memory:</strong> {modelTips[activeTab]?.memory}</p>
                  <p><strong>Performance:</strong> {modelTips[activeTab]?.performance}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Button */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
        >
          <AdjustmentsHorizontalIcon className="h-5 w-5" />
          Global {
            activeTab === 'vllm' ? 'vLLM' : 
            activeTab === 'ollama' ? 'Ollama' :
            activeTab === 'embeddings' ? 'Embeddings' :
            'Reranker'
          } Settings
        </button>
      </div>

      {/* Global Settings Panel */}
      {showSettings && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <h3 className="text-lg font-semibold mb-4">
            Global {
              activeTab === 'vllm' ? 'vLLM' : 
              activeTab === 'ollama' ? 'Ollama' :
              activeTab === 'embeddings' ? 'Embeddings' :
              'Reranker'
            } Settings
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            These settings apply to all models unless overridden by model-specific settings.
          </p>
          
          {activeTab === 'vllm' && (
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">GPU Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      GPU Memory Utilization
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.05"
                      value={vllmSettings.gpu_memory_utilization}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        gpu_memory_utilization: parseFloat(e.target.value)
                      })}
                      className="w-full"
                    />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {(vllmSettings.gpu_memory_utilization * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Tensor Parallel Size
                    </label>
                    <select
                      value={vllmSettings.tensor_parallel_size}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        tensor_parallel_size: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value={1}>1 (Single GPU)</option>
                      <option value={2}>2 GPUs</option>
                      <option value={4}>4 GPUs</option>
                      <option value={8}>8 GPUs</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      CPU Offload (GB)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="64"
                      value={vllmSettings.cpu_offload_gb}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        cpu_offload_gb: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Model Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Max Model Length
                    </label>
                    <select
                      value={vllmSettings.max_model_len}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        max_model_len: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value={2048}>2K</option>
                      <option value={4096}>4K</option>
                      <option value={8192}>8K</option>
                      <option value={16384}>16K</option>
                      <option value={32768}>32K</option>
                      <option value={65536}>64K</option>
                      <option value={131072}>128K</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Quantization
                    </label>
                    <select
                      value={vllmSettings.quantization}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        quantization: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="auto">Auto-detect</option>
                      <option value="awq">AWQ</option>
                      <option value="gptq">GPTQ</option>
                      <option value="squeezellm">SqueezeLLM</option>
                      <option value="fp8">FP8</option>
                      <option value="none">None (FP16)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Data Type
                    </label>
                    <select
                      value={vllmSettings.dtype}
                      onChange={(e) => setVllmSettings({
                        ...vllmSettings,
                        dtype: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="auto">Auto</option>
                      <option value="half">FP16</option>
                      <option value="float16">float16</option>
                      <option value="bfloat16">bfloat16</option>
                      <option value="float">FP32</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="col-span-2">
                <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={vllmSettings.trust_remote_code}
                        onChange={(e) => setVllmSettings({
                          ...vllmSettings,
                          trust_remote_code: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Trust Remote Code</span>
                    </label>
                  </div>

                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={vllmSettings.enforce_eager}
                        onChange={(e) => setVllmSettings({
                          ...vllmSettings,
                          enforce_eager: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Enforce Eager Mode</span>
                    </label>
                  </div>

                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={vllmSettings.disable_log_stats}
                        onChange={(e) => setVllmSettings({
                          ...vllmSettings,
                          disable_log_stats: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Disable Log Stats</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ollama' && (
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      GPU Layers
                    </label>
                    <input
                      type="number"
                      min="-1"
                      value={ollamaSettings.gpu_layers}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        gpu_layers: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                    <span className="text-xs text-gray-500">-1 = use all layers</span>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Context Size
                    </label>
                    <select
                      value={ollamaSettings.context_size}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        context_size: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value={512}>512</option>
                      <option value={1024}>1024</option>
                      <option value={2048}>2048</option>
                      <option value={4096}>4096</option>
                      <option value={8192}>8192</option>
                      <option value={16384}>16384</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      CPU Threads
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={ollamaSettings.num_thread}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        num_thread: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                    <span className="text-xs text-gray-500">0 = auto-detect</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Generation Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Temperature ({ollamaSettings.temperature})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={ollamaSettings.temperature}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        temperature: parseFloat(e.target.value)
                      })}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Top K
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={ollamaSettings.top_k}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        top_k: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Top P ({ollamaSettings.top_p})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={ollamaSettings.top_p}
                      onChange={(e) => setOllamaSettings({
                        ...ollamaSettings,
                        top_p: parseFloat(e.target.value)
                      })}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              <div className="col-span-2">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={ollamaSettings.use_mmap}
                        onChange={(e) => setOllamaSettings({
                          ...ollamaSettings,
                          use_mmap: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Use Memory Mapping</span>
                    </label>
                  </div>

                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={ollamaSettings.use_mlock}
                        onChange={(e) => setOllamaSettings({
                          ...ollamaSettings,
                          use_mlock: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Lock Model in RAM</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'embeddings' && (
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Embeddings Model Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Current Model
                    </label>
                    <select
                      value={embeddingsSettings.model_name}
                      onChange={(e) => setEmbeddingsSettings({
                        ...embeddingsSettings,
                        model_name: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="nomic-ai/nomic-embed-text-v1.5">Nomic Embed Text v1.5 (768 dim)</option>
                      <option value="BAAI/bge-base-en-v1.5">BGE Base EN v1.5 (768 dim)</option>
                      <option value="BAAI/bge-large-en-v1.5">BGE Large EN v1.5 (1024 dim)</option>
                      <option value="BAAI/bge-small-en-v1.5">BGE Small EN v1.5 (384 dim)</option>
                      <option value="sentence-transformers/all-MiniLM-L6-v2">All-MiniLM-L6-v2 (384 dim)</option>
                      <option value="sentence-transformers/all-mpnet-base-v2">All-MPNet-Base-v2 (768 dim)</option>
                      <option value="thenlper/gte-large">GTE Large (1024 dim)</option>
                      <option value="thenlper/gte-base">GTE Base (768 dim)</option>
                      <option value="thenlper/gte-small">GTE Small (384 dim)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Device
                    </label>
                    <select
                      value={embeddingsSettings.device}
                      onChange={(e) => setEmbeddingsSettings({
                        ...embeddingsSettings,
                        device: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="cpu">CPU (Intel iGPU via OpenVINO)</option>
                      <option value="cuda">CUDA (NVIDIA GPU)</option>
                      <option value="mps">MPS (Apple Silicon)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Max Length
                    </label>
                    <select
                      value={embeddingsSettings.max_length}
                      onChange={(e) => setEmbeddingsSettings({
                        ...embeddingsSettings,
                        max_length: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value={512}>512 tokens</option>
                      <option value={1024}>1024 tokens</option>
                      <option value={2048}>2048 tokens</option>
                      <option value={4096}>4096 tokens</option>
                      <option value={8192}>8192 tokens</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Batch Size
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="128"
                      value={embeddingsSettings.batch_size}
                      onChange={(e) => setEmbeddingsSettings({
                        ...embeddingsSettings,
                        batch_size: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Model Cache Directory
                    </label>
                    <input
                      type="text"
                      value={embeddingsSettings.models_cache_dir}
                      onChange={(e) => setEmbeddingsSettings({
                        ...embeddingsSettings,
                        models_cache_dir: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={embeddingsSettings.normalize}
                        onChange={(e) => setEmbeddingsSettings({
                          ...embeddingsSettings,
                          normalize: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Normalize embeddings (L2 normalization)</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={embeddingsSettings.trust_remote_code}
                        onChange={(e) => setEmbeddingsSettings({
                          ...embeddingsSettings,
                          trust_remote_code: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Trust remote code (required for some models)</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'reranker' && (
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Reranker Model Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Current Model
                    </label>
                    <select
                      value={rerankerSettings.model_name}
                      onChange={(e) => setRerankerSettings({
                        ...rerankerSettings,
                        model_name: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="mixedbread-ai/mxbai-rerank-large-v1">MxBai Rerank Large v1</option>
                      <option value="mixedbread-ai/mxbai-rerank-base-v1">MxBai Rerank Base v1</option>
                      <option value="BAAI/bge-reranker-v2-m3">BGE Reranker v2 M3</option>
                      <option value="BAAI/bge-reranker-large">BGE Reranker Large</option>
                      <option value="BAAI/bge-reranker-base">BGE Reranker Base</option>
                      <option value="cross-encoder/ms-marco-MiniLM-L-6-v2">MS-MARCO MiniLM L6 v2</option>
                      <option value="cross-encoder/ms-marco-MiniLM-L-12-v2">MS-MARCO MiniLM L12 v2</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Device
                    </label>
                    <select
                      value={rerankerSettings.device}
                      onChange={(e) => setRerankerSettings({
                        ...rerankerSettings,
                        device: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value="cpu">CPU (Intel iGPU via OpenVINO)</option>
                      <option value="cuda">CUDA (NVIDIA GPU)</option>
                      <option value="mps">MPS (Apple Silicon)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Max Length
                    </label>
                    <select
                      value={rerankerSettings.max_length}
                      onChange={(e) => setRerankerSettings({
                        ...rerankerSettings,
                        max_length: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    >
                      <option value={256}>256 tokens</option>
                      <option value={512}>512 tokens</option>
                      <option value={1024}>1024 tokens</option>
                      <option value={2048}>2048 tokens</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Batch Size
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="128"
                      value={rerankerSettings.batch_size}
                      onChange={(e) => setRerankerSettings({
                        ...rerankerSettings,
                        batch_size: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Model Cache Directory
                    </label>
                    <input
                      type="text"
                      value={rerankerSettings.models_cache_dir}
                      onChange={(e) => setRerankerSettings({
                        ...rerankerSettings,
                        models_cache_dir: e.target.value
                      })}
                      className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>

                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={rerankerSettings.trust_remote_code}
                        onChange={(e) => setRerankerSettings({
                          ...rerankerSettings,
                          trust_remote_code: e.target.checked
                        })}
                        className="rounded"
                      />
                      <span className="text-sm">Trust remote code (required for some models)</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 flex justify-end gap-2">
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              onClick={async () => {
                try {
                  let settingsToSave;
                  if (activeTab === 'vllm') {
                    settingsToSave = vllmSettings;
                  } else if (activeTab === 'ollama') {
                    settingsToSave = ollamaSettings;
                  } else if (activeTab === 'embeddings') {
                    settingsToSave = embeddingsSettings;
                  } else if (activeTab === 'reranker') {
                    settingsToSave = rerankerSettings;
                  }

                  await modelApi.updateGlobalSettings(activeTab, settingsToSave);
                  toast.success('Global settings saved successfully');
                  setShowSettings(false);
                } catch (error) {
                  console.error('Failed to save settings:', error);
                  toast.error(`Failed to save settings: ${error.message}`);
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save Global Settings
            </button>
          </div>
        </motion.div>
      )}

      {/* Search Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="space-y-4">
          {/* Search Bar and Controls */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={`Search Hugging Face for ${
                  activeTab === 'vllm' ? 'text generation (AWQ/GPTQ quantized)' :
                  activeTab === 'ollama' ? 'GGUF format' :
                  activeTab === 'embeddings' ? 'sentence-transformers embedding' :
                  'cross-encoder reranking'
                } models...`}
                className="w-full px-4 py-2 pl-10 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 border rounded-lg flex items-center gap-2 ${
                showFilters ? 'bg-blue-50 border-blue-300 text-blue-700' : 'hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="h-5 w-5" />
              Filters
            </button>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="downloads">Sort by Downloads</option>
              <option value="likes">Sort by Likes</option>
              <option value="lastModified">Sort by Last Modified</option>
            </select>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="grid grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <div>
                <label className="block text-sm font-medium mb-1">Quantization</label>
                <select
                  value={filters.quantization}
                  onChange={(e) => setFilters({ ...filters, quantization: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="">Any</option>
                  <option value="awq">AWQ</option>
                  <option value="gptq">GPTQ</option>
                  <option value="gguf">GGUF</option>
                  <option value="fp8">FP8</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Model Size (B)</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.minSize}
                    onChange={(e) => setFilters({ ...filters, minSize: e.target.value })}
                    className="w-1/2 px-2 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.maxSize}
                    onChange={(e) => setFilters({ ...filters, maxSize: e.target.value })}
                    className="w-1/2 px-2 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">License</label>
                <select
                  value={filters.license}
                  onChange={(e) => setFilters({ ...filters, license: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="">Any</option>
                  <option value="apache-2.0">Apache 2.0</option>
                  <option value="mit">MIT</option>
                  <option value="cc-by-sa-4.0">CC BY-SA 4.0</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Task</label>
                <select
                  value={filters.task}
                  onChange={(e) => setFilters({ ...filters, task: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="">Any</option>
                  <option value="text-generation">Text Generation</option>
                  <option value="text2text-generation">Text2Text Generation</option>
                  <option value="conversational">Conversational</option>
                  <option value="feature-extraction">Feature Extraction</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Language</label>
                <select
                  value={filters.language}
                  onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="">Any</option>
                  <option value="en">English</option>
                  <option value="zh">Chinese</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="multilingual">Multilingual</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <button
                  onClick={() => setFilters({
                    quantization: '',
                    minSize: '',
                    maxSize: '',
                    license: '',
                    task: '',
                    language: ''
                  })}
                  className="w-full px-3 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Clear Filters
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {searching && (
          <div className="mt-4 text-center text-gray-500">
            <ArrowPathIcon className="h-6 w-6 animate-spin mx-auto" />
            Searching Hugging Face...
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
            {searchResults.map((model) => (
              <div
                key={model.modelId}
                className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                onClick={() => setSelectedModel(model)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {model.modelId}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {model.author} • {model.downloads?.toLocaleString() || 0} downloads • {model.likes || 0} likes
                    </p>
                    <div className="flex gap-2 mt-2">
                      {model.pipeline_tag && (
                        <span className="inline-block px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                          {model.pipeline_tag}
                        </span>
                      )}
                      {model.tags?.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (activeTab === 'vllm') {
                        downloadVllmModel(model.modelId);
                      } else {
                        downloadOllamaModel(model.modelId);
                      }
                    }}
                    className="ml-4 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    <CloudArrowDownIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Installed Models */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Installed {
            activeTab === 'vllm' ? 'vLLM' : 
            activeTab === 'ollama' ? 'Ollama' :
            activeTab === 'embeddings' ? 'Embedding' :
            'Reranker'
          } Models
        </h2>

        <div className="space-y-4">
          {activeTab === 'vllm' && (
            !installedModels?.vllm || installedModels.vllm.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No vLLM models installed yet. Search and download models above.
              </p>
            ) : (
              installedModels.vllm.map((model) => (
                <motion.div
                  key={model.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{model.name}</h4>
                        {model.active && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                            Active
                          </span>
                        )}
                        {model.has_overrides && (
                          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                            Custom Settings
                          </span>
                        )}
                        {downloadProgress[model.id] !== undefined && (
                          <div className="flex items-center gap-2">
                            <ArrowPathIcon className="h-4 w-4 animate-spin text-blue-500" />
                            <span className="text-xs text-blue-600 dark:text-blue-400">
                              Downloading: {Math.round(downloadProgress[model.id])}%
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-gray-500">
                        <span>Path: {model.path}</span>
                        <span>Size: {formatBytes(model.size)}</span>
                        <span>Modified: {new Date(model.last_modified).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowModelSettings(model.id)}
                        className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-1"
                        title="Model-specific settings"
                      >
                        <Cog6ToothIcon className="h-4 w-4" />
                      </button>
                      {!model.active && (
                        <button
                          onClick={() => activateModel('vllm', model.id)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                        >
                          <PlayIcon className="h-4 w-4" />
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => deleteModel('vllm', model.id)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )
          )}

          {activeTab === 'ollama' && (
            !installedModels?.ollama || installedModels.ollama.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No Ollama models installed yet. Search and download models above.
              </p>
            ) : (
              installedModels.ollama.map((model) => (
                <motion.div
                  key={model.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{model.name}</h4>
                        {model.has_overrides && (
                          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                            Custom Settings
                          </span>
                        )}
                        {downloadProgress[model.name] !== undefined && (
                          <div className="flex items-center gap-2">
                            <ArrowPathIcon className="h-4 w-4 animate-spin text-blue-500" />
                            <span className="text-xs text-blue-600 dark:text-blue-400">
                              Downloading: {Math.round(downloadProgress[model.name])}%
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-gray-500">
                        <span>Size: {formatBytes(model.size)}</span>
                        <span>Modified: {new Date(model.last_modified).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowModelSettings(model.name)}
                        className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-1"
                        title="Model-specific settings"
                      >
                        <Cog6ToothIcon className="h-4 w-4" />
                      </button>
                      <button
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                      >
                        <PlayIcon className="h-4 w-4" />
                        Run
                      </button>
                      <button
                        onClick={() => deleteModel('ollama', model.name)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )
          )}

          {activeTab === 'embeddings' && (
            !installedModels?.embeddings || installedModels.embeddings.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Current embedding model: {embeddingsSettings.model_name}
                </p>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg max-w-md mx-auto">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    The embedding service runs on Intel iGPU for optimal resource allocation.
                    You can change the model in the Global Settings above.
                  </p>
                </div>
              </div>
            ) : (
              installedModels.embeddings.map((model) => (
                <motion.div
                  key={model.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{model.name}</h4>
                        {model.active && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                            Active
                          </span>
                        )}
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                          {model.dimensions} dimensions
                        </span>
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-gray-500">
                        <span>Size: {formatBytes(model.size)}</span>
                        <span>Device: {model.device || 'CPU (iGPU)'}</span>
                        {model.last_used && (
                          <span>Last used: {new Date(model.last_used).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!model.active && (
                        <button
                          onClick={() => activateModel('embeddings', model.name)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                        >
                          <PlayIcon className="h-4 w-4" />
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => deleteModel('embeddings', model.name)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )
          )}

          {activeTab === 'reranker' && (
            !installedModels?.reranker || installedModels.reranker.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Current reranker model: {rerankerSettings.model_name}
                </p>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg max-w-md mx-auto">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    The reranker service runs on Intel iGPU for optimal resource allocation.
                    You can change the model in the Global Settings above.
                  </p>
                </div>
              </div>
            ) : (
              installedModels.reranker.map((model) => (
                <motion.div
                  key={model.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{model.name}</h4>
                        {model.active && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                            Active
                          </span>
                        )}
                        <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                          Cross-encoder
                        </span>
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-gray-500">
                        <span>Size: {formatBytes(model.size)}</span>
                        <span>Device: {model.device || 'CPU (iGPU)'}</span>
                        {model.last_used && (
                          <span>Last used: {new Date(model.last_used).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!model.active && (
                        <button
                          onClick={() => activateModel('reranker', model.name)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                        >
                          <PlayIcon className="h-4 w-4" />
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => deleteModel('reranker', model.name)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )
          )}
        </div>
      </div>

      {/* Model-Specific Settings Modal */}
      {showModelSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-semibold">Model-Specific Settings</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Settings for: {showModelSettings}
                </p>
              </div>
              <button
                onClick={() => setShowModelSettings(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircleIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  These settings override the global {activeTab === 'vllm' ? 'vLLM' : 'Ollama'} settings for this specific model.
                  Leave fields empty to use global defaults.
                </p>
              </div>

              <ModelSettingsForm
                modelId={showModelSettings}
                activeTab={activeTab}
                globalSettings={activeTab === 'vllm' ? vllmSettings : ollamaSettings}
                existingOverrides={modelOverrides[showModelSettings] || {}}
                onSave={saveModelSettings}
                onCancel={() => setShowModelSettings(null)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Model Details Panel */}
      {selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold">{selectedModel.modelId}</h3>
              <button
                onClick={() => setSelectedModel(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircleIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Model Information</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Author: {selectedModel.author}</div>
                  <div>Downloads: {selectedModel.downloads?.toLocaleString() || 0}</div>
                  <div>Likes: {selectedModel.likes || 0}</div>
                  <div>Task: {selectedModel.pipeline_tag || 'Unknown'}</div>
                  {selectedModel.lastModified && (
                    <div>Updated: {new Date(selectedModel.lastModified).toLocaleDateString()}</div>
                  )}
                  {selectedModel.library_name && (
                    <div>Library: {selectedModel.library_name}</div>
                  )}
                </div>
              </div>

              {selectedModel.tags && selectedModel.tags.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedModel.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-sm rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    if (activeTab === 'vllm') {
                      downloadVllmModel(selectedModel.modelId);
                    } else {
                      downloadOllamaModel(selectedModel.modelId);
                    }
                    setSelectedModel(null);
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2"
                >
                  <CloudArrowDownIcon className="h-5 w-5" />
                  Download Model
                </button>
                <a
                  href={`https://huggingface.co/${selectedModel.modelId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  View on Hugging Face
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}