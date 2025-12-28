import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSystem } from '../../contexts/SystemContext';
import { useToast } from '../Toast';
import ModelSettingsForm from '../ModelSettingsForm';
import modelApi from '../../services/modelApi';
import { serviceInfo } from '../../data/serviceInfo';
import ErrorBoundary from '../ErrorBoundary';

// Component imports
import ServiceTabs from './ServiceTabs';
import ServiceInfoCard from './ServiceInfoCard';
import GlobalSettingsPanel from './GlobalSettings';
import SearchBar from './ModelSearch/SearchBar';
import SearchFilters from './ModelSearch/SearchFilters';
import SearchResults from './ModelSearch/SearchResults';
import InstalledModels from './InstalledModels';
import ModelDetailsModal from './ModelDetailsModal';
import { XCircleIcon } from '@heroicons/react/24/outline';

function AIModelManagementCore() {
  const { systemStatus } = useSystem();
  const toast = useToast();

  // Tab state
  const [activeTab, setActiveTab] = useState('vllm');

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('downloads');
  const [searchTimer, setSearchTimer] = useState(null);
  const [filters, setFilters] = useState({
    quantization: '',
    minSize: '',
    maxSize: '',
    license: '',
    task: '',
    language: ''
  });

  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  const [showModelSettings, setShowModelSettings] = useState(null);

  // Models state
  const [installedModels, setInstalledModels] = useState({
    vllm: [],
    ollama: [],
    embeddings: [],
    reranker: []
  });
  const [loadingModels, setLoadingModels] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState({});
  const [modelOverrides, setModelOverrides] = useState({});

  // Global settings state
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

  // Load installed models
  const loadInstalledModels = useCallback(async () => {
    setLoadingModels(true);
    try {
      const models = await modelApi.getInstalledModels();

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

      const downloads = await modelApi.getAllDownloads().catch(() => ({}));
      const progressMap = {};
      Object.entries(downloads || {}).forEach(([taskId, task]) => {
        if (task?.status === 'downloading' && task?.model_id) {
          progressMap[task.model_id] = task.progress || 0;
        }
      });
      setDownloadProgress(progressMap);
    } catch (error) {
      console.error('Failed to load models:', error);
      toast.error(`Failed to load installed models: ${error.message}`);
    } finally {
      setLoadingModels(false);
    }
  }, [activeTab, toast]);

  // Load global settings
  const loadGlobalSettings = async () => {
    try {
      const [vllm, ollama] = await Promise.all([
        modelApi.getGlobalSettings('vllm').catch(err => {
          console.warn('Failed to load vLLM settings:', err);
          return vllmSettings;
        }),
        modelApi.getGlobalSettings('ollama').catch(err => {
          console.warn('Failed to load Ollama settings:', err);
          return ollamaSettings;
        })
      ]);
      setVllmSettings(prevSettings => ({ ...prevSettings, ...vllm }));
      setOllamaSettings(prevSettings => ({ ...prevSettings, ...ollama }));
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error(`Failed to load global settings: ${error.message}`);
    }
  };

  // Load on mount
  useEffect(() => {
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

  // Service-specific filters
  const currentServiceFilters = useMemo(() => {
    if (!serviceInfo[activeTab]?.defaultFilters) return {};
    return serviceInfo[activeTab].defaultFilters;
  }, [activeTab]);

  // Advanced search from Hugging Face (with debouncing)
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
        const defaultFilters = currentServiceFilters;
        let searchUrl = `https://huggingface.co/api/models?search=${encodeURIComponent(searchQuery)}`;

        if (defaultFilters.task) {
          searchUrl += `&pipeline_tag=${defaultFilters.task}`;
        }
        if (filters.task) {
          searchUrl += `&pipeline_tag=${filters.task}`;
        }
        if (filters.language) {
          searchUrl += `&language=${filters.language}`;
        }
        if (filters.license) {
          searchUrl += `&license=${filters.license}`;
        }

        searchUrl += '&limit=100';

        const response = await fetch(searchUrl);

        if (response.ok) {
          let data = await response.json();

          // Apply client-side filters
          data = data.filter(model => {
            // Service-specific filtering logic
            if (activeTab === 'vllm') {
              const isTextGeneration = model.pipeline_tag === 'text-generation' ||
                                     model.tags?.some(tag => tag.toLowerCase().includes('text-generation'));
              if (!isTextGeneration) return false;

              if (defaultFilters.quantization && !filters.quantization) {
                const hasQuantization = model.tags?.some(tag =>
                  defaultFilters.quantization.some(q => tag.toLowerCase().includes(q))
                );
                model._hasQuantization = hasQuantization;
              }
            } else if (activeTab === 'ollama') {
              if (defaultFilters.format && !filters.quantization) {
                const hasGGUF = model.tags?.some(tag =>
                  tag.toLowerCase().includes('gguf')
                ) || model.modelId.toLowerCase().includes('gguf');
                model._hasGGUF = hasGGUF;
              }
            } else if (activeTab === 'embeddings') {
              if (defaultFilters.library) {
                const hasLibrary = model.tags?.some(tag =>
                  tag.toLowerCase().includes(defaultFilters.library)
                ) || model.library_name === defaultFilters.library ||
                  model.pipeline_tag === 'feature-extraction';
                if (!hasLibrary) return false;
              }
            } else if (activeTab === 'reranker') {
              const isReranker = model.tags?.some(tag =>
                tag.toLowerCase().includes('rerank') ||
                tag.toLowerCase().includes('cross-encoder')
              ) || model.pipeline_tag === 'sentence-similarity' ||
                model.modelId.toLowerCase().includes('rerank') ||
                model.modelId.toLowerCase().includes('cross-encoder');
              if (!isReranker) return false;
            }

            if (filters.quantization) {
              const hasQuantization = model.tags?.some(tag =>
                tag.toLowerCase().includes(filters.quantization.toLowerCase())
              );
              if (!hasQuantization) return false;
            }

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
            const aCompatible = a._hasQuantization || a._hasGGUF || false;
            const bCompatible = b._hasQuantization || b._hasGGUF || false;

            if (aCompatible && !bCompatible) return -1;
            if (!aCompatible && bCompatible) return 1;

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
    }, searchQuery.length > 2 ? 300 : 1000);

    setSearchTimer(timer);

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [searchQuery, activeTab, filters, sortBy, currentServiceFilters]);

  // Download handlers
  const downloadVllmModel = async (modelId) => {
    try {
      const result = await modelApi.downloadModel(modelId, 'vllm', vllmSettings);
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
          loadInstalledModels();
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

  // Save model-specific settings
  const saveModelSettings = async (modelId, settings) => {
    try {
      await modelApi.updateModelSettings(modelId, activeTab, settings);

      setModelOverrides(prev => ({
        ...prev,
        [modelId]: settings
      }));
      setShowModelSettings(null);
      loadInstalledModels();
    } catch (error) {
      console.error('Failed to save model settings:', error);
      toast.error(`Failed to save settings: ${error.message}`);
    }
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

  // Save global settings
  const handleSaveGlobalSettings = async () => {
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

      <ServiceTabs activeTab={activeTab} setActiveTab={setActiveTab} />

      <ServiceInfoCard activeTab={activeTab} />

      <GlobalSettingsPanel
        activeTab={activeTab}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
        vllmSettings={vllmSettings}
        setVllmSettings={setVllmSettings}
        ollamaSettings={ollamaSettings}
        setOllamaSettings={setOllamaSettings}
        embeddingsSettings={embeddingsSettings}
        setEmbeddingsSettings={setEmbeddingsSettings}
        rerankerSettings={rerankerSettings}
        setRerankerSettings={setRerankerSettings}
        onSave={handleSaveGlobalSettings}
      />

      <SearchBar
        activeTab={activeTab}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        showFilters={showFilters}
        setShowFilters={setShowFilters}
        sortBy={sortBy}
        setSortBy={setSortBy}
        searching={searching}
      />

      <SearchFilters
        filters={filters}
        setFilters={setFilters}
        showFilters={showFilters}
      />

      <SearchResults
        searchResults={searchResults}
        activeTab={activeTab}
        downloadVllmModel={downloadVllmModel}
        downloadOllamaModel={downloadOllamaModel}
        setSelectedModel={setSelectedModel}
      />

      <InstalledModels
        activeTab={activeTab}
        installedModels={installedModels}
        formatBytes={formatBytes}
        downloadProgress={downloadProgress}
        setShowModelSettings={setShowModelSettings}
        activateModel={activateModel}
        deleteModel={deleteModel}
        embeddingsSettings={embeddingsSettings}
        rerankerSettings={rerankerSettings}
      />

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

      <ModelDetailsModal
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        activeTab={activeTab}
        downloadVllmModel={downloadVllmModel}
        downloadOllamaModel={downloadOllamaModel}
      />
    </div>
  );
}

// Wrap component with ErrorBoundary for crash protection
export default function AIModelManagement() {
  return (
    <ErrorBoundary>
      <AIModelManagementCore />
    </ErrorBoundary>
  );
}
