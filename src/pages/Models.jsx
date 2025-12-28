import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon, 
  CloudArrowDownIcon,
  TrashIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ChatBubbleLeftIcon,
  SparklesIcon,
  ArrowUpTrayIcon,
  CogIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useSystem } from '../contexts/SystemContext';
import HelpTooltip from '../components/HelpTooltip';

// Model task categories
const MODEL_TASKS = {
  'text-generation': { label: 'Text Generation', icon: ChatBubbleLeftIcon },
  'text2text-generation': { label: 'Text to Text', icon: DocumentTextIcon },
  'text-classification': { label: 'Classification', icon: FunnelIcon },
  'token-classification': { label: 'Token Classification', icon: SparklesIcon },
  'question-answering': { label: 'Q&A', icon: ChatBubbleLeftIcon },
  'summarization': { label: 'Summarization', icon: DocumentTextIcon },
  'translation': { label: 'Translation', icon: DocumentTextIcon },
  'conversational': { label: 'Conversational', icon: ChatBubbleLeftIcon },
  'feature-extraction': { label: 'Embeddings', icon: CpuChipIcon },
};

// Popular embedding models
const EMBEDDING_MODELS = [
  {
    id: 'BAAI/bge-base-en-v1.5',
    name: 'BGE Base EN v1.5',
    description: 'High-quality English embedding model with excellent performance on semantic search tasks.',
    downloads: 2800000,
    likes: 15000,
    size: '~1.3GB',
    dimensions: 768,
    max_length: 512,
    recommended: true,
    type: 'embedding'
  },
  {
    id: 'BAAI/bge-large-en-v1.5',
    name: 'BGE Large EN v1.5',
    description: 'Large English embedding model for the highest quality semantic representations.',
    downloads: 1500000,
    likes: 8000,
    size: '~3.5GB',
    dimensions: 1024,
    max_length: 512,
    type: 'embedding'
  },
  {
    id: 'sentence-transformers/all-MiniLM-L6-v2',
    name: 'All-MiniLM-L6-v2',
    description: 'Compact and fast sentence embedding model, perfect for lightweight applications.',
    downloads: 4200000,
    likes: 12000,
    size: '~80MB',
    dimensions: 384,
    max_length: 256,
    type: 'embedding'
  },
  {
    id: 'intfloat/e5-large-v2',
    name: 'E5 Large v2',
    description: 'Multi-language embedding model with strong performance across various tasks.',
    downloads: 800000,
    likes: 5000,
    size: '~1.3GB',
    dimensions: 1024,
    max_length: 512,
    type: 'embedding'
  }
];

// Popular reranker models
const RERANKER_MODELS = [
  {
    id: 'BAAI/bge-reranker-v2-m3',
    name: 'BGE Reranker v2 M3',
    description: 'State-of-the-art cross-encoder reranking model for improved search relevance.',
    downloads: 450000,
    likes: 3500,
    size: '~2.3GB',
    max_length: 8192,
    recommended: true,
    type: 'reranker'
  },
  {
    id: 'BAAI/bge-reranker-base',
    name: 'BGE Reranker Base',
    description: 'Base reranker model offering good performance with lower resource requirements.',
    downloads: 320000,
    likes: 2800,
    size: '~1.1GB',
    max_length: 512,
    type: 'reranker'
  },
  {
    id: 'cross-encoder/ms-marco-MiniLM-L-6-v2',
    name: 'MS MARCO MiniLM L6 v2',
    description: 'Efficient cross-encoder trained on MS MARCO dataset for document ranking.',
    downloads: 680000,
    likes: 4200,
    size: '~90MB',
    max_length: 512,
    type: 'reranker'
  },
  {
    id: 'mixedbread-ai/mxbai-rerank-large-v1',
    name: 'MxBai Rerank Large v1',
    description: 'Advanced multilingual reranker with support for 100+ languages.',
    downloads: 180000,
    likes: 1200,
    size: '~1.8GB',
    max_length: 8192,
    type: 'reranker'
  }
];

// Popular vLLM-compatible models to showcase
const FEATURED_MODELS = [
  {
    id: 'Qwen/Qwen2.5-32B-Instruct-AWQ',
    name: 'Qwen 2.5 32B Instruct (AWQ)',
    description: 'vLLM-optimized AWQ quantized model with excellent performance. 32K context length.',
    downloads: 1800000,
    likes: 12000,
    size: '~16GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
    recommended: true,
  },
  {
    id: 'TheBloke/Llama-2-13B-chat-AWQ',
    name: 'Llama 2 13B Chat (AWQ)',
    description: 'AWQ quantized Llama 2 model optimized for vLLM. Great balance of quality and speed.',
    downloads: 2500000,
    likes: 15000,
    size: '~7GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
  },
  {
    id: 'TheBloke/Mistral-7B-Instruct-v0.2-AWQ',
    name: 'Mistral 7B Instruct v0.2 (AWQ)',
    description: 'Efficient AWQ quantized model with sliding window attention. Perfect for RTX 5090.',
    downloads: 3200000,
    likes: 18000,
    size: '~4GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
  },
  {
    id: 'mistralai/Mixtral-8x7B-Instruct-v0.1',
    name: 'Mixtral 8x7B Instruct',
    description: 'Mixture of Experts model. Requires FP16 for vLLM but delivers exceptional quality.',
    downloads: 1500000,
    likes: 10000,
    size: '~90GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'FP16',
    note: 'High VRAM usage',
  },
  {
    id: 'deepseek-ai/deepseek-coder-33b-instruct',
    name: 'DeepSeek Coder 33B',
    description: 'Specialized coding model. Works great with vLLM in FP16 format.',
    downloads: 800000,
    likes: 5000,
    size: '~66GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'FP16',
    specialized: 'coding',
  },
  // Gemma 3 Models
  {
    id: 'gaunernst/gemma-3-27b-it-int4-awq',
    name: 'Gemma 3 27B IT (AWQ)',
    description: 'Google\'s latest multimodal model with vision capabilities. AWQ quantized for efficiency.',
    downloads: 450000,
    likes: 3200,
    size: '~14GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
    multimodal: true,
    recommended: true,
  },
  {
    id: 'gaunernst/gemma-3-12b-it-int4-awq',
    name: 'Gemma 3 12B IT (AWQ)',
    description: 'Mid-sized Gemma 3 with vision support. Excellent balance of capability and resource usage.',
    downloads: 380000,
    likes: 2800,
    size: '~6.6GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
    multimodal: true,
  },
  {
    id: 'google/gemma-2-9b-it',
    name: 'Gemma 3 4B IT',
    description: 'Compact Gemma model with vision capabilities. Ideal for resource-constrained deployments.',
    downloads: 520000,
    likes: 4100,
    size: '~2.6GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'FP16',
    multimodal: true,
  },
  {
    id: 'gaunernst/gemma-3-1b-it-int4-awq',
    name: 'Gemma 3 1B IT (AWQ)',
    description: 'Smallest Gemma 3 model, text-only. Ultra-fast inference for simple tasks.',
    downloads: 620000,
    likes: 5200,
    size: '~0.5GB',
    task: 'text-generation',
    vllm_ready: true,
    quantization: 'AWQ (4-bit)',
  },
];

export default function Models() {
  const { models, systemStatus } = useSystem();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(FEATURED_MODELS);
  const [searching, setSearching] = useState(false);
  const [downloading, setDownloading] = useState({});
  const [activeTab, setActiveTab] = useState('llm');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedTask, setSelectedTask] = useState('all');
  const [selectedQuantization, setSelectedQuantization] = useState({});
  const [downloadProgress, setDownloadProgress] = useState({});
  const [globalRetention, setGlobalRetention] = useState('keep');
  const [defaultContextSize, setDefaultContextSize] = useState('16384');
  const [modelRetention, setModelRetention] = useState({});
  const [modelContextSize, setModelContextSize] = useState({});
  const [estimatedMemory, setEstimatedMemory] = useState({});
  const [ws, setWs] = useState(null);
  const [embeddingModels, setEmbeddingModels] = useState([]);
  const [rerankerModels, setRerankerModels] = useState([]);
  const [currentEmbeddingModel, setCurrentEmbeddingModel] = useState('BAAI/bge-base-en-v1.5');
  const [currentRerankerModel, setCurrentRerankerModel] = useState('BAAI/bge-reranker-v2-m3');

  // Debounce timer for search
  const [searchTimer, setSearchTimer] = useState(null);
  
  // WebSocket connection for download progress
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const websocket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setWs(websocket);
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'download_progress') {
          setDownloadProgress(prev => ({
            ...prev,
            [data.model_id]: data.data.progress || 0
          }));
          
          if (data.data.status === 'completed') {
            setDownloading(prev => ({ ...prev, [data.model_id]: false }));
            // Refresh models list
            window.location.reload();
          } else if (data.data.status === 'failed') {
            setDownloading(prev => ({ ...prev, [data.model_id]: false }));
            alert(`Download failed for ${data.model_id}: ${data.data.error || 'Unknown error'}`);
          }
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setWs(null);
    };
    
    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, []);

  // Real-time search as user types
  useEffect(() => {
    if (searchTimer) {
      clearTimeout(searchTimer);
    }
    
    if (!searchQuery.trim()) {
      setSearchResults(FEATURED_MODELS);
      setSearching(false);
      return;
    }
    
    setSearching(true);
    
    // Debounce search by 300ms
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/v1/models/search?q=${encodeURIComponent(searchQuery)}`);
        if (!response.ok) throw new Error('Search failed');
        const data = await response.json();
        setSearchResults(data.length > 0 ? data : []);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    
    setSearchTimer(timer);
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [searchQuery]);

  const downloadModel = async (modelId, quantization = null) => {
    setDownloading(prev => ({ ...prev, [modelId]: true }));
    setDownloadProgress(prev => ({ ...prev, [modelId]: 0 }));
    
    try {
      const response = await fetch('/api/v1/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          model_id: modelId,
          backend: 'vllm', // Default to vLLM for downloads from browse page
          settings: {
            quantization: quantization || selectedQuantization[modelId] || 'AWQ'
          }
        }),
      });
      if (!response.ok) throw new Error('Download failed');
      
      // Simulate download progress
      const interval = setInterval(() => {
        setDownloadProgress(prev => {
          const current = prev[modelId] || 0;
          if (current >= 100) {
            clearInterval(interval);
            setDownloading(prev => ({ ...prev, [modelId]: false }));
            return prev;
          }
          return { ...prev, [modelId]: current + 10 };
        });
      }, 500);
    } catch (error) {
      console.error('Download error:', error);
      setDownloading(prev => ({ ...prev, [modelId]: false }));
      setDownloadProgress(prev => ({ ...prev, [modelId]: 0 }));
    }
  };

  const deleteModel = async (model) => {
    if (!confirm('Are you sure you want to delete this model?')) return;
    
    try {
      // Use the new backend-aware delete endpoint
      const backend = model.backend || 'vllm'; // fallback to vllm if not specified
      const response = await fetch(`/api/v1/models/${backend}/${encodeURIComponent(model.id)}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Delete failed');
      
      // Refresh models list
      window.location.reload();
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete model: ' + error.message);
    }
  };

  const handleModelUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('model', file);
    
    try {
      const response = await fetch('/api/v1/models/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      
      alert('Model uploaded successfully!');
      // Refresh models list
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload model');
    }
  };

  const setActiveModel = async (model) => {
    try {
      // Use the new backend-aware activate endpoint
      const backend = model.backend || 'vllm';
      const response = await fetch(`/api/v1/models/${backend}/${encodeURIComponent(model.id)}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error('Failed to set active model');
      
      // Refresh models to update active status
      window.location.reload();
    } catch (error) {
      console.error('Set active model error:', error);
      alert('Failed to activate model: ' + error.message);
    }
  };

  const filteredResults = searchResults.filter(model => {
    if (selectedTask !== 'all' && model.task !== selectedTask) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          vLLM Model Management
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Search HuggingFace, download to your server, and manage locally installed models for vLLM inference
        </p>
        <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>💡 Best Results:</strong> Use AWQ or GPTQ quantized models (4-bit) for faster inference and lower VRAM usage. Example: Qwen/Qwen2.5-32B-Instruct-AWQ
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('llm')}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'llm'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ChatBubbleLeftIcon className="h-5 w-5" />
            LLM Models
          </button>
          <button
            onClick={() => setActiveTab('embeddings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'embeddings'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CpuChipIcon className="h-5 w-5" />
            Embedding Models
          </button>
          <button
            onClick={() => setActiveTab('rerankers')}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'rerankers'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FunnelIcon className="h-5 w-5" />
            Reranker Models
          </button>
          <button
            onClick={() => setActiveTab('installed')}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === 'installed'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CheckCircleIcon className="h-5 w-5" />
            Installed ({models.length})
          </button>
        </nav>
      </div>

      {activeTab === 'llm' && (
        <div className="space-y-6">
          {/* Search Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex gap-4 mb-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search vLLM-compatible models (AWQ, GPTQ, FP16)..."
                  className="w-full px-4 py-2 pl-10 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
            </div>

            {/* Filters */}
            <div className="flex gap-4 items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Filter by task:</span>
              <select
                value={selectedTask}
                onChange={(e) => setSelectedTask(e.target.value)}
                className="px-3 py-1 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
              >
                <option value="all">All Tasks</option>
                {Object.entries(MODEL_TASKS).map(([key, task]) => (
                  <option key={key} value={key}>{task.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Search Results */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 dark:text-white">
              {searchQuery ? 'Search Results' : 'Featured vLLM-Compatible Models'}
            </h3>
            {filteredResults.map((model) => (
              <motion.div
                key={model.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-6"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                        {model.name || model.id}
                      </h4>
                      {model.vllm_ready && (
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full flex items-center gap-1">
                          <CheckCircleIcon className="h-3 w-3" />
                          vLLM Ready
                        </span>
                      )}
                      {model.recommended && (
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                          Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                      {model.description || 'No description available'}
                    </p>
                    <div className="flex gap-6 mt-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <ArrowDownTrayIcon className="h-4 w-4" />
                        {model.downloads?.toLocaleString() || 0} downloads
                      </span>
                      <span>❤️ {model.likes?.toLocaleString() || 0}</span>
                      <span>Size: {model.size || 'Unknown'}</span>
                      {model.quantization && (
                        <span className="font-medium">Format: {model.quantization}</span>
                      )}
                    </div>
                    
                    {/* vLLM Compatibility Note */}
                    {model.note && (
                      <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <p className="text-sm text-yellow-800 dark:text-yellow-200">
                          ⚠️ {model.note}
                        </p>
                      </div>
                    )}
                    
                    {model.specialized && (
                      <div className="mt-3 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                        <p className="text-sm text-purple-800 dark:text-purple-200">
                          🎯 Specialized for: {model.specialized}
                        </p>
                      </div>
                    )}

                    {/* Memory Estimation */}
                    {estimatedMemory[model.id] && (
                      <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <h5 className="text-sm font-medium mb-2">Memory Requirements:</h5>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Model:</span>
                            <span className="ml-2 font-medium">{estimatedMemory[model.id].model} GB</span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Context:</span>
                            <span className="ml-2 font-medium">{estimatedMemory[model.id].context} GB</span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Total:</span>
                            <span className="ml-2 font-medium">{estimatedMemory[model.id].total} GB</span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">GPU Usage:</span>
                            <span className={`ml-2 font-medium ${
                              parseFloat(estimatedMemory[model.id].percentage) > 90 ? 'text-red-600' :
                              parseFloat(estimatedMemory[model.id].percentage) > 70 ? 'text-yellow-600' :
                              'text-green-600'
                            }`}>
                              {estimatedMemory[model.id].percentage}%
                            </span>
                          </div>
                        </div>
                        {parseFloat(estimatedMemory[model.id].percentage) > 90 && (
                          <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                            ⚠️ Warning: This model may not fit in available GPU memory
                          </div>
                        )}
                      </div>
                    )}

                    {/* Download Progress */}
                    {downloading[model.id] && downloadProgress[model.id] > 0 && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span>Downloading...</span>
                          <span>{downloadProgress[model.id]}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${downloadProgress[model.id]}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => downloadModel(model.id)}
                    disabled={downloading[model.id]}
                    className="ml-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <CloudArrowDownIcon className="h-5 w-5" />
                    {downloading[model.id] ? 'Downloading...' : 'Download'}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Upload Model Button */}
          <div className="mt-6">
            <button
              onClick={() => document.getElementById('model-upload').click()}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <ArrowUpTrayIcon className="h-5 w-5" />
              Upload Model
            </button>
            <input
              id="model-upload"
              type="file"
              accept=".gguf,.bin,.safetensors"
              className="hidden"
              onChange={handleModelUpload}
            />
          </div>
        </div>
      )}

      {/* Embedding Models Tab */}
      {activeTab === 'embeddings' && (
        <div className="space-y-6">
          {/* Current Embedding Model Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Current Embedding Model
              </h3>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <span className="text-sm text-green-600 dark:text-green-400">Active</span>
              </div>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 dark:text-blue-100">{currentEmbeddingModel}</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Currently running on port 8082 • {EMBEDDING_MODELS.find(m => m.id === currentEmbeddingModel)?.dimensions || 768} dimensions
              </p>
            </div>
          </div>
          
          {/* Available Embedding Models */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Available Embedding Models
            </h3>
            <div className="space-y-4">
              {EMBEDDING_MODELS.map((model) => (
                <motion.div
                  key={model.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {model.name}
                        </h4>
                        {model.recommended && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 text-xs font-medium rounded">
                            Recommended
                          </span>
                        )}
                        {model.id === currentEmbeddingModel && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 text-xs font-medium rounded">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {model.description}
                      </p>
                      <div className="flex gap-4 text-sm text-gray-500">
                        <span>📊 {model.dimensions} dimensions</span>
                        <span>📏 Max {model.max_length} tokens</span>
                        <span>💾 {model.size}</span>
                        <span>⬇️ {model.downloads?.toLocaleString()} downloads</span>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      {model.id !== currentEmbeddingModel ? (
                        <>
                          <button className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                            Switch To
                          </button>
                          <button className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1">
                            <CloudArrowDownIcon className="h-4 w-4" />
                            Download
                          </button>
                        </>
                      ) : (
                        <button className="px-3 py-2 bg-gray-600 text-white rounded-lg text-sm flex items-center gap-1">
                          <CogIcon className="h-4 w-4" />
                          Configure
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Reranker Models Tab */}
      {activeTab === 'rerankers' && (
        <div className="space-y-6">
          {/* Current Reranker Model Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Current Reranker Model
              </h3>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
                <span className="text-sm text-green-600 dark:text-green-400">Active</span>
              </div>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <h4 className="font-medium text-purple-900 dark:text-purple-100">{currentRerankerModel}</h4>
              <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                Currently running on port 8083 • {RERANKER_MODELS.find(m => m.id === currentRerankerModel)?.max_length || 512} max tokens
              </p>
            </div>
          </div>
          
          {/* Available Reranker Models */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Available Reranker Models
            </h3>
            <div className="space-y-4">
              {RERANKER_MODELS.map((model) => (
                <motion.div
                  key={model.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {model.name}
                        </h4>
                        {model.recommended && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 text-xs font-medium rounded">
                            Recommended
                          </span>
                        )}
                        {model.id === currentRerankerModel && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 text-xs font-medium rounded">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {model.description}
                      </p>
                      <div className="flex gap-4 text-sm text-gray-500">
                        <span>📏 Max {model.max_length} tokens</span>
                        <span>💾 {model.size}</span>
                        <span>⬇️ {model.downloads?.toLocaleString()} downloads</span>
                        <span>❤️ {model.likes?.toLocaleString()} likes</span>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      {model.id !== currentRerankerModel ? (
                        <>
                          <button className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
                            Switch To
                          </button>
                          <button className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm flex items-center gap-1">
                            <CloudArrowDownIcon className="h-4 w-4" />
                            Download
                          </button>
                        </>
                      ) : (
                        <button className="px-3 py-2 bg-gray-600 text-white rounded-lg text-sm flex items-center gap-1">
                          <CogIcon className="h-4 w-4" />
                          Configure
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'installed' && (
        <div className="space-y-6">
          {/* Model Management Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Model Management Settings
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Default Model Retention
                  <HelpTooltip 
                    title="Model Retention"
                    content="Controls how long inactive models stay loaded in GPU memory. Lower values free up memory sooner but require reloading models more often."
                  />
                </label>
                <div className="flex items-center gap-4">
                  <select
                    value={globalRetention}
                    onChange={(e) => setGlobalRetention(e.target.value)}
                    className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  >
                    <option value="keep">Keep Forever</option>
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="24h">24 Hours</option>
                    <option value="7d">7 Days</option>
                    <option value="30d">30 Days</option>
                  </select>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Unload models from memory after this period of inactivity
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Default Context Size
                  <HelpTooltip 
                    title="Context Window"
                    content="The maximum number of tokens the model can process at once. Larger contexts use more memory but allow longer conversations."
                  />
                </label>
                <input
                  type="number"
                  value={defaultContextSize}
                  onChange={(e) => setDefaultContextSize(e.target.value)}
                  min="512"
                  max="131072"
                  step="512"
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 w-32"
                />
                <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">tokens</span>
              </div>
            </div>
          </div>

          {/* Installed Models */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Installed Models
            </h2>
            <div className="space-y-4">
              {models.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                  No models installed locally yet. Use the Browse tab to search HuggingFace and download models compatible with vLLM (AWQ, GPTQ, or FP16 quantized models work best).
                </p>
              ) : (
              models.map((model) => (
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
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          model.backend === 'vllm' 
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' 
                            : 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
                        }`}>
                          {model.backend === 'vllm' ? 'vLLM' : 'Ollama'}
                        </span>
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-gray-500">
                        <span>Backend: {model.type}</span>
                        <span>Size: {model.size}</span>
                        <span>Last used: {model.last_used || 'Never'}</span>
                        {model.has_overrides && (
                          <span className="text-blue-600">Custom Settings</span>
                        )}
                      </div>
                      
                      {/* Per-Model Settings */}
                      <div className="mt-4 pt-4 border-t dark:border-gray-700">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm text-gray-600 dark:text-gray-400">Retention</label>
                            <select
                              value={modelRetention[model.id] || 'default'}
                              onChange={(e) => setModelRetention({...modelRetention, [model.id]: e.target.value})}
                              className="mt-1 px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 w-full"
                            >
                              <option value="default">Use Default</option>
                              <option value="keep">Keep Forever</option>
                              <option value="1h">1 Hour</option>
                              <option value="4h">4 Hours</option>
                              <option value="24h">24 Hours</option>
                              <option value="7d">7 Days</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-sm text-gray-600 dark:text-gray-400">Context Size</label>
                            <input
                              type="number"
                              value={modelContextSize[model.id] || defaultContextSize}
                              onChange={(e) => setModelContextSize({...modelContextSize, [model.id]: e.target.value})}
                              min="512"
                              max="131072"
                              step="512"
                              className="mt-1 px-2 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 w-full"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!model.active && (
                        <button
                          onClick={() => setActiveModel(model)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                          title="Set as active model"
                        >
                          <PlayIcon className="h-4 w-4" />
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => deleteModel(model)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                        title="Delete model"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}