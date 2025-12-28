import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import {
  Brain,
  Zap,
  DollarSign,
  Activity,
  Settings,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  TrendingUp,
  PieChart,
  BarChart3,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Edit,
  Play,
  User,
  Users,
  ArrowUpDown,
  Filter,
  Download
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';
import { Line, Pie, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

// Provider logos mapping
const PROVIDER_LOGOS = {
  openrouter: '/assets/providers/openrouter.png',
  openai: '/assets/providers/openai.png',
  anthropic: '/assets/providers/anthropic.png',
  together: '/assets/providers/together.png',
  huggingface: '/assets/providers/huggingface.png',
  cohere: '/assets/providers/cohere.png',
  groq: '/assets/providers/groq.png',
  mistral: '/assets/providers/mistral.png',
  custom: '/assets/providers/custom.png'
};

// Provider colors
const PROVIDER_COLORS = {
  openrouter: '#7C3AED',
  openai: '#10A37F',
  anthropic: '#D97706',
  together: '#3B82F6',
  huggingface: '#F59E0B',
  cohere: '#8B5CF6',
  groq: '#06B6D4',
  mistral: '#EC4899',
  custom: '#6B7280'
};

// Statistics Card Component
const StatCard = ({ title, value, icon: Icon, color, trend, theme }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`${theme.card} rounded-xl p-6 border ${color}/20 hover:border-${color}/40 transition-all`}
  >
    <div className="flex items-center justify-between">
      <div>
        <p className={`text-sm ${theme.text.secondary} mb-1`}>{title}</p>
        <h3 className={`text-3xl font-bold ${theme.text.primary}`}>{value}</h3>
        {trend && (
          <div className={`flex items-center gap-1 mt-2 text-sm ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            <TrendingUp className={`h-4 w-4 ${trend < 0 ? 'rotate-180' : ''}`} />
            <span>{Math.abs(trend)}% from last month</span>
          </div>
        )}
      </div>
      <div className={`w-12 h-12 rounded-lg bg-${color}/20 flex items-center justify-center`}>
        <Icon className={`h-6 w-6 text-${color}`} />
      </div>
    </div>
  </motion.div>
);

// Provider Card Component
const ProviderCard = ({ provider, onConfigure, onTest, onDisable, onDelete, theme }) => {
  const statusColors = {
    active: 'green-500',
    disabled: 'gray-500',
    error: 'red-500'
  };

  const statusColor = statusColors[provider.status] || 'gray-500';
  const providerColor = PROVIDER_COLORS[provider.type] || '#6B7280';

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`${theme.card} rounded-xl p-6 border border-${statusColor}/20 hover:border-${statusColor}/40 transition-all`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${providerColor}20` }}>
            {PROVIDER_LOGOS[provider.type] ? (
              <img src={PROVIDER_LOGOS[provider.type]} alt={provider.name} className="w-8 h-8" />
            ) : (
              <Brain className="h-6 w-6" style={{ color: providerColor }} />
            )}
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>{provider.name}</h3>
            <p className={`text-sm ${theme.text.secondary}`}>{provider.type}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium bg-${statusColor}/20 text-${statusColor}`}>
          {provider.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className={`text-xs ${theme.text.secondary} mb-1`}>Models</p>
          <p className={`text-lg font-semibold ${theme.text.primary}`}>{provider.model_count}</p>
        </div>
        <div>
          <p className={`text-xs ${theme.text.secondary} mb-1`}>Avg Cost</p>
          <p className={`text-lg font-semibold ${theme.text.primary}`}>${provider.avg_cost}/1M</p>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onConfigure(provider)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span className="text-sm">Configure</span>
        </button>
        <button
          onClick={() => onTest(provider)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
        >
          <Zap className="h-4 w-4" />
          <span className="text-sm">Test</span>
        </button>
        <button
          onClick={() => onDelete(provider)}
          className="px-3 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  );
};

// Add Provider Modal
const AddProviderModal = ({ isOpen, onClose, onAdd, theme }) => {
  const [formData, setFormData] = useState({
    type: 'openrouter',
    apiKey: '',
    priority: 50,
    autoFallback: true,
    models: []
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const providerTypes = [
    { value: 'openrouter', label: 'OpenRouter' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'together', label: 'Together AI' },
    { value: 'huggingface', label: 'HuggingFace' },
    { value: 'cohere', label: 'Cohere' },
    { value: 'groq', label: 'Groq' },
    { value: 'mistral', label: 'Mistral' },
    { value: 'custom', label: 'Custom Endpoint' }
  ];

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const response = await fetch('/api/v1/llm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          provider: formData.type,
          api_key: formData.apiKey
        })
      });
      const data = await response.json();
      setTestResult(data);
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setTesting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`${theme.card} rounded-xl p-6 max-w-2xl w-full m-4 max-h-[90vh] overflow-y-auto`}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-2xl font-bold ${theme.text.primary}`}>Add Provider</h2>
          <button onClick={onClose} className={`p-2 rounded-lg ${theme.button}`}>
            <XCircle className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Provider Type */}
          <div>
            <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
              Provider Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg ${theme.input} ${theme.text.primary}`}
            >
              {providerTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
              API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={formData.apiKey}
                onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                className={`w-full px-4 py-2 rounded-lg ${theme.input} ${theme.text.primary} pr-10`}
                placeholder="sk-..."
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                {showApiKey ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
              </button>
            </div>
          </div>

          {/* Test Connection */}
          <div>
            <button
              onClick={handleTestConnection}
              disabled={!formData.apiKey || testing}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-50"
            >
              <Zap className="h-4 w-4" />
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            {testResult && (
              <div className={`mt-2 p-3 rounded-lg ${testResult.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {testResult.success ? (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    <span>Connection successful! ({testResult.latency}ms)</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4" />
                    <span>Error: {testResult.error}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Priority */}
          <div>
            <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
              Priority (1-100)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
              className={`w-full px-4 py-2 rounded-lg ${theme.input} ${theme.text.primary}`}
            />
          </div>

          {/* Auto-fallback */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.autoFallback}
              onChange={(e) => setFormData({ ...formData, autoFallback: e.target.checked })}
              className="w-4 h-4 rounded"
            />
            <label className={`text-sm ${theme.text.secondary}`}>
              Enable automatic fallback to this provider
            </label>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={() => {
              onAdd(formData);
              onClose();
            }}
            className="flex-1 px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
          >
            Add Provider
          </button>
          <button
            onClick={onClose}
            className={`flex-1 px-4 py-2 rounded-lg ${theme.button}`}
          >
            Cancel
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// Routing Strategy Panel
const RoutingStrategyPanel = ({ strategy, onStrategyChange, theme }) => {
  const strategies = [
    {
      value: 'cost',
      label: 'Cost Optimized',
      description: 'Always use the cheapest available model',
      icon: DollarSign,
      color: 'green-500'
    },
    {
      value: 'balanced',
      label: 'Balanced',
      description: 'Balance between cost and quality',
      icon: Activity,
      color: 'blue-500'
    },
    {
      value: 'quality',
      label: 'Quality Optimized',
      description: 'Use the best available models',
      icon: Brain,
      color: 'purple-500'
    }
  ];

  return (
    <div className={`${theme.card} rounded-xl p-6`}>
      <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Routing Strategy</h3>
      <div className="space-y-3">
        {strategies.map(strat => (
          <label
            key={strat.value}
            className={`flex items-start gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
              strategy === strat.value
                ? `border-${strat.color} bg-${strat.color}/10`
                : 'border-transparent bg-gray-700/20 hover:bg-gray-700/30'
            }`}
          >
            <input
              type="radio"
              name="strategy"
              value={strat.value}
              checked={strategy === strat.value}
              onChange={(e) => onStrategyChange(e.target.value)}
              className="mt-1"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <strat.icon className={`h-5 w-5 text-${strat.color}`} />
                <span className={`font-semibold ${theme.text.primary}`}>{strat.label}</span>
              </div>
              <p className={`text-sm ${theme.text.secondary}`}>{strat.description}</p>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};

// Power Level Card
const PowerLevelCard = ({ level, theme }) => {
  const levels = {
    eco: {
      title: 'Eco Mode',
      cost: '$0.20/1M tokens',
      description: 'Uses OpenRouter with cheapest models',
      features: ['High-volume tasks', 'Simple queries', 'Cost-effective'],
      models: ['llama-3-8b', 'mixtral-8x7b'],
      color: 'green-500'
    },
    balanced: {
      title: 'Balanced Mode',
      cost: '$1.00/1M tokens',
      description: 'Mix of quality and cost',
      features: ['General purpose use', 'Moderate complexity', 'Best value'],
      models: ['gpt-4o-mini', 'claude-haiku'],
      color: 'blue-500'
    },
    precision: {
      title: 'Precision Mode',
      cost: '$5.00/1M tokens',
      description: 'Uses best available models',
      features: ['Complex reasoning', 'High accuracy', 'Premium quality'],
      models: ['gpt-4', 'claude-opus'],
      color: 'purple-500'
    }
  };

  const config = levels[level];

  return (
    <div className={`${theme.card} rounded-xl p-6 border border-${config.color}/20`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-xl font-bold ${theme.text.primary}`}>{config.title}</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${config.color}/20 text-${config.color}`}>
          {config.cost}
        </span>
      </div>
      <p className={`text-sm ${theme.text.secondary} mb-4`}>{config.description}</p>
      <div className="space-y-2 mb-4">
        {config.features.map((feature, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <CheckCircle className={`h-4 w-4 text-${config.color}`} />
            <span className={`text-sm ${theme.text.secondary}`}>{feature}</span>
          </div>
        ))}
      </div>
      <div>
        <p className={`text-xs ${theme.text.secondary} mb-2`}>Models:</p>
        <div className="flex flex-wrap gap-2">
          {config.models.map((model, idx) => (
            <span key={idx} className={`px-2 py-1 rounded text-xs bg-${config.color}/10 text-${config.color}`}>
              {model}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main Component
export default function LiteLLMManagement() {
  const { theme, currentTheme } = useTheme();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState([]);
  const [statistics, setStatistics] = useState({
    totalProviders: 0,
    activeModels: 0,
    totalCalls: 0,
    totalCost: 0
  });
  const [routingStrategy, setRoutingStrategy] = useState('balanced');
  const [usageData, setUsageData] = useState(null);
  const [costData, setCostData] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [timeRange, setTimeRange] = useState('30d');

  // Error handling state
  const [errors, setErrors] = useState({
    providers: null,
    statistics: null,
    usage: null,
    addProvider: null,
    testProvider: null,
    deleteProvider: null,
    updateStrategy: null
  });
  const [retryCount, setRetryCount] = useState({
    providers: 0,
    statistics: 0,
    usage: 0
  });

  useEffect(() => {
    fetchProviders();
    fetchStatistics();
    fetchUsageAnalytics();
  }, []);

  useEffect(() => {
    const interval = setInterval(fetchStatistics, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchProviders = async (attempt = 0) => {
    setLoading(true);
    try {
      setErrors(prev => ({ ...prev, providers: null }));
      const response = await fetch('/api/v1/llm/providers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setProviders(data.providers || []);
      setRetryCount(prev => ({ ...prev, providers: 0 }));
    } catch (error) {
      console.error('Failed to fetch providers:', error);
      const errorMsg = `Failed to load providers: ${error.message}`;

      // Retry logic with exponential backoff
      if (attempt < 2) {
        const delay = Math.pow(2, attempt + 1) * 1000; // 2s, 4s
        setRetryCount(prev => ({ ...prev, providers: attempt + 1 }));
        setTimeout(() => fetchProviders(attempt + 1), delay);
      } else {
        setErrors(prev => ({ ...prev, providers: errorMsg }));
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async (attempt = 0) => {
    try {
      setErrors(prev => ({ ...prev, statistics: null }));
      const response = await fetch('/api/v1/llm/usage', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setStatistics({
        totalProviders: data.total_providers || 0,
        activeModels: data.active_models || 0,
        totalCalls: data.total_calls || 0,
        totalCost: data.total_cost || 0
      });
      setRetryCount(prev => ({ ...prev, statistics: 0 }));
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
      const errorMsg = `Failed to load statistics: ${error.message}`;

      // Retry logic with exponential backoff
      if (attempt < 2) {
        const delay = Math.pow(2, attempt + 1) * 1000; // 2s, 4s
        setRetryCount(prev => ({ ...prev, statistics: attempt + 1 }));
        setTimeout(() => fetchStatistics(attempt + 1), delay);
      } else {
        setErrors(prev => ({ ...prev, statistics: errorMsg }));
        toast.error(errorMsg);
      }
    }
  };

  const fetchUsageAnalytics = async (attempt = 0) => {
    try {
      setErrors(prev => ({ ...prev, usage: null }));
      const response = await fetch(`/api/v1/llm/usage?period=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();

      // Prepare chart data
      setUsageData({
        labels: data.labels || [],
        datasets: [{
          label: 'API Calls',
          data: data.values || [],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        }]
      });

      setCostData({
        labels: data.cost_labels || [],
        datasets: [{
          label: 'Cost ($)',
          data: data.cost_values || [],
          backgroundColor: [
            'rgba(59, 130, 246, 0.5)',
            'rgba(16, 185, 129, 0.5)',
            'rgba(245, 158, 11, 0.5)',
            'rgba(239, 68, 68, 0.5)',
            'rgba(139, 92, 246, 0.5)'
          ]
        }]
      });
      setRetryCount(prev => ({ ...prev, usage: 0 }));
    } catch (error) {
      console.error('Failed to fetch usage analytics:', error);
      const errorMsg = `Failed to load usage analytics: ${error.message}`;

      // Retry logic with exponential backoff
      if (attempt < 2) {
        const delay = Math.pow(2, attempt + 1) * 1000; // 2s, 4s
        setRetryCount(prev => ({ ...prev, usage: attempt + 1 }));
        setTimeout(() => fetchUsageAnalytics(attempt + 1), delay);
      } else {
        setErrors(prev => ({ ...prev, usage: errorMsg }));
        toast.error(errorMsg);
      }
    }
  };

  const handleAddProvider = async (formData) => {
    try {
      setErrors(prev => ({ ...prev, addProvider: null }));
      const response = await fetch('/api/v1/llm/providers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(formData)
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      toast.success('Provider added successfully');
      fetchProviders();
      fetchStatistics();
    } catch (error) {
      console.error('Failed to add provider:', error);
      const errorMsg = `Failed to add provider: ${error.message}`;
      setErrors(prev => ({ ...prev, addProvider: errorMsg }));
      toast.error(errorMsg);
    }
  };

  const handleTestProvider = async (provider) => {
    try {
      setErrors(prev => ({ ...prev, testProvider: null }));
      const response = await fetch(`/api/v1/llm/providers/${provider.id}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      if (data.success) {
        toast.success(`Test successful! (${data.latency}ms)`);
      } else {
        throw new Error(data.error || 'Test failed');
      }
    } catch (error) {
      console.error('Failed to test provider:', error);
      const errorMsg = `Test failed: ${error.message}`;
      setErrors(prev => ({ ...prev, testProvider: errorMsg }));
      toast.error(errorMsg);
    }
  };

  const handleDeleteProvider = async (provider) => {
    if (!confirm(`Delete provider "${provider.name}"?`)) return;
    try {
      setErrors(prev => ({ ...prev, deleteProvider: null }));
      const response = await fetch(`/api/v1/llm/providers/${provider.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      toast.success('Provider deleted successfully');
      fetchProviders();
      fetchStatistics();
    } catch (error) {
      console.error('Failed to delete provider:', error);
      const errorMsg = `Failed to delete provider: ${error.message}`;
      setErrors(prev => ({ ...prev, deleteProvider: errorMsg }));
      toast.error(errorMsg);
    }
  };

  const handleUpdateStrategy = async (newStrategy) => {
    setRoutingStrategy(newStrategy);
    try {
      setErrors(prev => ({ ...prev, updateStrategy: null }));
      const response = await fetch('/api/v1/llm/routing/rules', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({ strategy: newStrategy })
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      toast.success('Routing strategy updated successfully');
    } catch (error) {
      console.error('Failed to update routing strategy:', error);
      const errorMsg = `Failed to update strategy: ${error.message}`;
      setErrors(prev => ({ ...prev, updateStrategy: errorMsg }));
      toast.error(errorMsg);
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            LLM Provider Management
          </h1>
          <p className={`${theme.text.secondary} mt-1 ml-13`}>
            Manage multi-provider LLM routing, cost optimization, and BYOK
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
        >
          <Plus className="h-5 w-5" />
          Add Provider
        </button>
      </div>

      {/* Statistics Cards */}
      {errors.statistics ? (
        <div className={`${theme.card} rounded-xl p-6 border border-red-500/20`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <div>
                <p className={`font-semibold ${theme.text.primary}`}>Error Loading Statistics</p>
                <p className={`text-sm ${theme.text.secondary}`}>{errors.statistics}</p>
                {retryCount.statistics > 0 && (
                  <p className={`text-xs ${theme.text.secondary} mt-1`}>
                    Retry attempt {retryCount.statistics}/2
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={() => fetchStatistics()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Providers"
            value={statistics.totalProviders}
            icon={Users}
            color="blue-500"
            theme={theme}
          />
          <StatCard
            title="Active Models"
            value={statistics.activeModels}
            icon={Brain}
            color="purple-500"
            trend={12}
            theme={theme}
          />
          <StatCard
            title="API Calls (30d)"
            value={statistics.totalCalls.toLocaleString()}
            icon={Activity}
            color="green-500"
            trend={8}
            theme={theme}
          />
          <StatCard
            title="Total Cost (30d)"
            value={`$${statistics.totalCost.toFixed(2)}`}
            icon={DollarSign}
            color="amber-500"
            trend={-5}
            theme={theme}
          />
        </div>
      )}

      {/* Provider Cards Grid */}
      <div>
        <h2 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Providers</h2>
        {errors.providers ? (
          <div className={`${theme.card} rounded-xl p-6 border border-red-500/20`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-6 w-6 text-red-500" />
                <div>
                  <p className={`font-semibold ${theme.text.primary}`}>Error Loading Providers</p>
                  <p className={`text-sm ${theme.text.secondary}`}>{errors.providers}</p>
                  {retryCount.providers > 0 && (
                    <p className={`text-xs ${theme.text.secondary} mt-1`}>
                      Retry attempt {retryCount.providers}/2
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => fetchProviders()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </button>
            </div>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : providers.length === 0 ? (
          <div className={`${theme.card} rounded-xl p-12 text-center`}>
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className={`${theme.text.secondary}`}>No providers configured yet. Click "Add Provider" to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {providers.map(provider => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                onConfigure={() => {}}
                onTest={handleTestProvider}
                onDisable={() => {}}
                onDelete={handleDeleteProvider}
                theme={theme}
              />
            ))}
          </div>
        )}
      </div>

      {/* Routing Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RoutingStrategyPanel
          strategy={routingStrategy}
          onStrategyChange={handleUpdateStrategy}
          theme={theme}
        />

        {/* BYOK Management */}
        <div className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>BYOK Management</h3>
          <p className={`text-sm ${theme.text.secondary} mb-4`}>
            Bring Your Own Key - Let users use their own API keys for providers
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-700/20">
              <div className="flex items-center gap-3">
                <User className="h-5 w-5 text-blue-400" />
                <div>
                  <p className={`text-sm font-medium ${theme.text.primary}`}>12 users with BYOK</p>
                  <p className={`text-xs ${theme.text.secondary}`}>Active this month</p>
                </div>
              </div>
              <button className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-sm">
                View
              </button>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-gray-700/20">
              <div className="flex items-center gap-3">
                <DollarSign className="h-5 w-5 text-green-400" />
                <div>
                  <p className={`text-sm font-medium ${theme.text.primary}`}>$2,456 saved</p>
                  <p className={`text-xs ${theme.text.secondary}`}>From BYOK usage</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* User Power Levels */}
      <div>
        <h2 className={`text-xl font-bold ${theme.text.primary} mb-4`}>User Power Levels</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PowerLevelCard level="eco" theme={theme} />
          <PowerLevelCard level="balanced" theme={theme} />
          <PowerLevelCard level="precision" theme={theme} />
        </div>
      </div>

      {/* Usage Analytics Dashboard */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-xl font-bold ${theme.text.primary}`}>Usage Analytics</h2>
          <div className="flex gap-2">
            {['7d', '30d', '90d', 'all'].map(range => (
              <button
                key={range}
                onClick={() => {
                  setTimeRange(range);
                  fetchUsageAnalytics();
                }}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  timeRange === range
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-700/20 text-gray-400 hover:bg-gray-700/30'
                }`}
              >
                {range === 'all' ? 'All Time' : `Last ${range}`}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Usage Over Time Chart */}
          <div className={`${theme.card} rounded-xl p-6`}>
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>API Calls Over Time</h3>
            {usageData ? (
              <Line
                data={usageData}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { display: false }
                  },
                  scales: {
                    y: { beginAtZero: true }
                  }
                }}
              />
            ) : (
              <div className="h-64 flex items-center justify-center">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            )}
          </div>

          {/* Cost by Provider Chart */}
          <div className={`${theme.card} rounded-xl p-6`}>
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>Cost by Provider</h3>
            {costData ? (
              <Pie
                data={costData}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { position: 'bottom' }
                  }
                }}
              />
            ) : (
              <div className="h-64 flex items-center justify-center">
                <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Provider Modal */}
      <AddProviderModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddProvider}
        theme={theme}
      />
    </div>
  );
}
