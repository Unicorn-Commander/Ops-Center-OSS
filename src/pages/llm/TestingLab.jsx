/**
 * Testing Lab - Interactive LLM Model Testing
 *
 * Features:
 * - 10 pre-built test templates
 * - Model selector with search/filter
 * - Real-time streaming responses (SSE)
 * - Parameter controls (temperature, max_tokens, top_p)
 * - Response metrics (tokens, cost, latency, tokens/sec)
 * - Test history sidebar
 *
 * Author: UC-Cloud Development Team
 * Date: October 27, 2025
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Play,
  X,
  ChevronDown,
  Search,
  TrendingUp,
  Clock,
  DollarSign,
  Zap,
  History,
  RefreshCcw,
  AlertTriangle,
  CheckCircle,
  Settings,
  ChevronRight,
  Loader,
} from 'lucide-react';

export default function TestingLab() {
  // ============================================================================
  // State Management
  // ============================================================================

  // Templates & Models
  const [templates, setTemplates] = useState([]);
  const [models, setModels] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [loadingModels, setLoadingModels] = useState(true);

  // Selected values
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [prompt, setPrompt] = useState('');

  // Parameters
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [topP, setTopP] = useState(1.0);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Streaming & Response
  const [isStreaming, setIsStreaming] = useState(false);
  const [response, setResponse] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  // History
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // UI State
  const [modelSearch, setModelSearch] = useState('');
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Refs
  const responseRef = useRef(null);
  const eventSourceRef = useRef(null);
  const dropdownRef = useRef(null);

  // ============================================================================
  // Data Fetching
  // ============================================================================

  useEffect(() => {
    fetchTemplates();
    fetchModels();

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowModelDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/api/v1/llm/test/templates');
      if (!res.ok) throw new Error('Failed to load templates');
      const data = await res.json();
      setTemplates(data);
    } catch (err) {
      console.error('Error loading templates:', err);
      setError('Failed to load test templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch('/api/v1/llm/models?limit=100');
      if (!res.ok) throw new Error('Failed to load models');
      const data = await res.json();

      // Ensure data is always an array
      let modelsArray = [];
      if (Array.isArray(data)) {
        modelsArray = data;
      } else if (data && Array.isArray(data.models)) {
        modelsArray = data.models;
      } else if (data && Array.isArray(data.data)) {
        modelsArray = data.data;
      } else if (data && typeof data === 'object') {
        console.warn('Unexpected API response structure:', data);
        modelsArray = [];
      }

      setModels(modelsArray);
      if (modelsArray.length > 0) {
        setSelectedModel(modelsArray[0]);
      }
    } catch (err) {
      console.error('Error loading models:', err);
      setError('Failed to load model catalog');
      setModels([]); // Ensure models is always an array
    } finally {
      setLoadingModels(false);
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch('/api/v1/llm/test/history?limit=10');
      if (!res.ok) throw new Error('Failed to load history');
      const data = await res.json();
      setHistory(data.tests || []);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory && history.length === 0) {
      fetchHistory();
    }
  }, [showHistory]);

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setPrompt(template.prompt);
    setError(null);

    // Auto-select suggested model if available
    if (template.suggested_models && template.suggested_models.length > 0) {
      const suggestedModel = models.find(m =>
        template.suggested_models.some(sm =>
          m.name === sm || m.display_name === sm || m.id === sm
        )
      );
      if (suggestedModel) {
        setSelectedModel(suggestedModel);
      }
    }
  };

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    setShowModelDropdown(false);
    setError(null);
  };

  const handleTestModel = async () => {
    if (!selectedModel || !prompt.trim()) {
      setError('Please select a model and enter a prompt');
      return;
    }

    // Reset state
    setIsStreaming(true);
    setResponse('');
    setMetrics(null);
    setError(null);

    const startTime = Date.now();

    try {
      // Create EventSource for SSE
      const params = new URLSearchParams({
        model_id: selectedModel.name || selectedModel.id,
        messages: JSON.stringify([{ role: 'user', content: prompt }]),
        temperature: temperature.toString(),
        max_tokens: maxTokens.toString(),
        top_p: topP.toString(),
        stream: 'true'
      });

      const url = `/api/v1/llm/test/test?${params.toString()}`;
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            setError(data.error);
            setIsStreaming(false);
            eventSource.close();
            return;
          }

          if (data.done) {
            // Final metrics received
            setMetrics({
              input_tokens: data.input_tokens,
              output_tokens: data.output_tokens,
              total_tokens: data.total_tokens,
              cost: data.cost,
              latency_ms: data.latency_ms,
              tokens_per_sec: data.output_tokens / (data.latency_ms / 1000)
            });
            setIsStreaming(false);
            eventSource.close();

            // Refresh history
            if (showHistory) {
              fetchHistory();
            }
          } else if (data.content) {
            // Stream token received
            setResponse((prev) => prev + data.content);

            // Auto-scroll to bottom
            if (responseRef.current) {
              responseRef.current.scrollTop = responseRef.current.scrollHeight;
            }
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        setError('Connection error. Please check your authentication and try again.');
        setIsStreaming(false);
        eventSource.close();
      };
    } catch (err) {
      console.error('Test error:', err);
      setError(err.message || 'Failed to test model');
      setIsStreaming(false);
    }
  };

  const handleStopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  const handleClear = () => {
    setPrompt('');
    setResponse('');
    setMetrics(null);
    setError(null);
    setSelectedTemplate(null);
  };

  const handleLoadHistoryItem = (item) => {
    setPrompt(item.prompt);
    setResponse(item.response);
    setMetrics({
      input_tokens: item.input_tokens,
      output_tokens: item.output_tokens,
      total_tokens: item.tokens_used,
      cost: item.cost,
      latency_ms: item.latency_ms,
      tokens_per_sec: item.output_tokens / (item.latency_ms / 1000)
    });

    // Try to select the same model
    const model = models.find(m => m.name === item.model_id || m.id === item.model_id);
    if (model) {
      setSelectedModel(model);
    }

    setShowHistory(false);
  };

  // ============================================================================
  // Computed Values
  // ============================================================================

  const filteredModels = (Array.isArray(models) ? models : []).filter(model => {
    if (!modelSearch) return true;
    const search = modelSearch.toLowerCase();
    return (
      (model.display_name || '').toLowerCase().includes(search) ||
      (model.name || '').toLowerCase().includes(search) ||
      (model.provider || '').toLowerCase().includes(search)
    );
  });

  const charCount = prompt.length;
  const estimatedTokens = Math.ceil(prompt.split(/\s+/).length * 1.3);

  // ============================================================================
  // Category Badge Component
  // ============================================================================

  const CategoryBadge = ({ category }) => {
    const colors = {
      explanation: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      creative: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      coding: 'bg-green-500/20 text-green-300 border-green-500/30',
      analysis: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      reasoning: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
      summarization: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      translation: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
      mathematics: 'bg-red-500/20 text-red-300 border-red-500/30',
      conversation: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    };

    return (
      <span className={`px-2 py-0.5 rounded-full text-xs border ${colors[category] || colors.explanation}`}>
        {category}
      </span>
    );
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="h-full flex flex-col lg:flex-row gap-4 p-4 overflow-hidden">
      {/* Main Content */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">

        {/* Top Section: Templates */}
        <div className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">Test Templates</h3>
          </div>

          {loadingTemplates ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="w-6 h-6 text-purple-400 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className={`
                    p-3 rounded-lg border transition-all text-left
                    ${selectedTemplate?.id === template.id
                      ? 'bg-purple-600/20 border-purple-500 shadow-lg'
                      : 'bg-slate-700/50 border-slate-600 hover:bg-slate-700 hover:border-slate-500'
                    }
                  `}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-sm font-medium text-white line-clamp-1">
                      {template.name}
                    </h4>
                    <CategoryBadge category={template.category} />
                  </div>
                  <p className="text-xs text-gray-400 line-clamp-2">
                    {template.description}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Middle Section: Model Selector & Parameters */}
        <div className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Model Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Select Model
              </label>
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowModelDropdown(!showModelDropdown)}
                  disabled={loadingModels}
                  className="w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-left flex items-center justify-between hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="flex-1 min-w-0">
                    {selectedModel ? (
                      <div>
                        <div className="font-medium truncate">{selectedModel.display_name || selectedModel.name}</div>
                        <div className="text-xs text-gray-400">
                          {selectedModel.provider} • ${(selectedModel.cost_per_1m_input_tokens || 0).toFixed(2)}/1M tokens
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-400">
                        {loadingModels ? 'Loading models...' : 'Select a model'}
                      </span>
                    )}
                  </div>
                  <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                </button>

                {showModelDropdown && !loadingModels && (
                  <div className="absolute z-50 mt-2 w-full bg-slate-800 border border-slate-600 rounded-lg shadow-xl max-h-80 overflow-hidden">
                    {/* Search */}
                    <div className="p-2 border-b border-slate-700">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="text"
                          placeholder="Search models..."
                          value={modelSearch}
                          onChange={(e) => setModelSearch(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
                        />
                      </div>
                    </div>

                    {/* Model List */}
                    <div className="overflow-y-auto max-h-64">
                      {filteredModels.length === 0 ? (
                        <div className="p-4 text-center text-gray-400">
                          No models found
                        </div>
                      ) : (
                        filteredModels.map((model) => (
                          <button
                            key={model.id || model.name}
                            onClick={() => handleModelSelect(model)}
                            className={`
                              w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors border-b border-slate-700/50 last:border-0
                              ${selectedModel?.name === model.name ? 'bg-purple-900/30' : ''}
                            `}
                          >
                            <div className="font-medium text-white truncate">
                              {model.display_name || model.name}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-xs rounded">
                                {model.provider}
                              </span>
                              <span className="text-xs text-gray-400">
                                ${(model.cost_per_1m_input_tokens || 0).toFixed(2)}/1M in • ${(model.cost_per_1m_output_tokens || 0).toFixed(2)}/1M out
                              </span>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Parameters */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-300">
                  Parameters
                </label>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                >
                  <Settings className="w-3 h-3" />
                  {showAdvanced ? 'Hide' : 'Show'} Advanced
                </button>
              </div>

              <div className="space-y-3">
                {/* Temperature */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-gray-400">Temperature</label>
                    <span className="text-xs text-white font-mono">{temperature.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                </div>

                {/* Max Tokens */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-gray-400">Max Tokens</label>
                    <span className="text-xs text-white font-mono">{maxTokens}</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="4096"
                    step="1"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                </div>

                {/* Top P (Advanced) */}
                {showAdvanced && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs text-gray-400">Top P</label>
                      <span className="text-xs text-white font-mono">{topP.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={topP}
                      onChange={(e) => setTopP(parseFloat(e.target.value))}
                      className="w-full accent-purple-500"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Prompt & Response */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">

          {/* Prompt Editor */}
          <div className="flex flex-col bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4 min-h-0">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Prompt</h3>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">
                  {charCount} chars • ~{estimatedTokens} tokens
                </span>
                <button
                  onClick={handleClear}
                  className="p-1 hover:bg-slate-700 rounded transition-colors"
                  title="Clear"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here or select a template above..."
              className="flex-1 w-full px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none font-mono text-sm"
            />

            <div className="flex items-center gap-2 mt-3">
              <button
                onClick={handleTestModel}
                disabled={isStreaming || !selectedModel || !prompt.trim()}
                className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20"
              >
                {isStreaming ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Streaming...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Test Model
                  </>
                )}
              </button>

              {isStreaming && (
                <button
                  onClick={handleStopStreaming}
                  className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium flex items-center gap-2 transition-all"
                >
                  <X className="w-5 h-5" />
                  Stop
                </button>
              )}
            </div>
          </div>

          {/* Response Display */}
          <div className="flex flex-col bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4 min-h-0">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Response</h3>
              {metrics && (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />
                  Complete
                </span>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-3 p-3 bg-red-900/20 border border-red-700/50 rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-300">{error}</div>
              </div>
            )}

            {/* Response Text */}
            <div
              ref={responseRef}
              className="flex-1 w-full px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-gray-100 overflow-y-auto font-mono text-sm whitespace-pre-wrap"
            >
              {response || (
                <span className="text-gray-500">
                  {isStreaming ? 'Waiting for response...' : 'Response will appear here...'}
                </span>
              )}
            </div>

            {/* Metrics */}
            {metrics && (
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                    <TrendingUp className="w-3 h-3" />
                    Tokens
                  </div>
                  <div className="text-sm font-mono text-white">
                    {metrics.input_tokens} in • {metrics.output_tokens} out
                  </div>
                </div>

                <div className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                    <DollarSign className="w-3 h-3" />
                    Cost
                  </div>
                  <div className="text-sm font-mono text-white">
                    ${metrics.cost.toFixed(6)}
                  </div>
                </div>

                <div className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                    <Clock className="w-3 h-3" />
                    Latency
                  </div>
                  <div className="text-sm font-mono text-white">
                    {metrics.latency_ms}ms
                  </div>
                </div>

                <div className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg">
                  <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                    <Zap className="w-3 h-3" />
                    Speed
                  </div>
                  <div className="text-sm font-mono text-white">
                    {metrics.tokens_per_sec.toFixed(1)} tok/s
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* History Sidebar */}
      <div className={`
        lg:w-80 flex flex-col bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-lg overflow-hidden transition-all
        ${showHistory ? 'lg:block' : 'lg:w-12'}
      `}>
        {/* Toggle Button */}
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="flex items-center justify-between p-4 hover:bg-slate-700/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-purple-400" />
            {showHistory && <span className="text-sm font-semibold text-white">Test History</span>}
          </div>
          <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${showHistory ? 'rotate-90' : ''}`} />
        </button>

        {/* History List */}
        {showHistory && (
          <div className="flex-1 overflow-y-auto p-4 pt-0">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-8">
                <Loader className="w-6 h-6 text-purple-400 animate-spin" />
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No test history yet
              </div>
            ) : (
              <div className="space-y-2">
                {history.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleLoadHistoryItem(item)}
                    className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-left transition-all"
                  >
                    <div className="text-xs text-gray-400 mb-1">
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                    <div className="text-sm text-white font-medium line-clamp-1 mb-2">
                      {item.prompt}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span>{item.tokens_used} tokens</span>
                      <span>•</span>
                      <span>${item.cost.toFixed(4)}</span>
                      <span>•</span>
                      <span>{item.latency_ms}ms</span>
                    </div>
                  </button>
                ))}

                <button
                  onClick={fetchHistory}
                  className="w-full px-4 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm text-purple-400 flex items-center justify-center gap-2 transition-all"
                >
                  <RefreshCcw className="w-4 h-4" />
                  Refresh
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
