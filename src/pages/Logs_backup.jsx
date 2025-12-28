import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  DocumentTextIcon,
  ArrowPathIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  ClockIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XMarkIcon,
  PlayIcon,
  PauseIcon,
  TrashIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
};

const logLevels = {
  ERROR: { color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20', icon: ExclamationCircleIcon },
  WARN: { color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20', icon: ExclamationTriangleIcon },
  INFO: { color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20', icon: InformationCircleIcon },
  DEBUG: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-50 dark:bg-gray-900/20', icon: CheckCircleIcon },
  SUCCESS: { color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20', icon: CheckCircleIcon }
};

const serviceLogSources = [
  { id: 'all', name: 'All Services', icon: ServerIcon },
  { id: 'vllm', name: 'vLLM API', icon: ServerIcon },
  { id: 'open-webui', name: 'Chat UI', icon: ServerIcon },
  { id: 'whisperx', name: 'WhisperX', icon: ServerIcon },
  { id: 'kokoro', name: 'Kokoro TTS', icon: ServerIcon },
  { id: 'embeddings', name: 'Embeddings', icon: ServerIcon },
  { id: 'reranker', name: 'Reranker', icon: ServerIcon },
  { id: 'admin-dashboard', name: 'Admin Dashboard', icon: ServerIcon },
  { id: 'system', name: 'System Logs', icon: ServerIcon }
];

export default function Logs() {
  const [activeTab, setActiveTab] = useState('live');
  const [selectedService, setSelectedService] = useState('all');
  const [logLevel, setLogLevel] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [maxLines, setMaxLines] = useState(1000);
  const [logSources, setLogSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);
  const logsContainerRef = useRef(null);

  // Load log sources on mount
  useEffect(() => {
    loadLogSources();
    return () => {
      // Cleanup WebSocket on unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
    {
      id: 2,
      timestamp: new Date(Date.now() - 1000).toISOString(),
      level: 'SUCCESS',
      service: 'open-webui',
      message: 'User authentication successful',
      details: 'User: admin, Session: abc123'
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 2000).toISOString(),
      level: 'WARN',
      service: 'whisperx',
      message: 'Audio processing took longer than expected',
      details: 'Processing time: 5.2s, File size: 12MB'
    },
    {
      id: 4,
      timestamp: new Date(Date.now() - 3000).toISOString(),
      level: 'ERROR',
      service: 'kokoro',
      message: 'Voice synthesis failed for request',
      details: 'Error: Model not found, Voice: af_bella'
    },
    {
      id: 5,
      timestamp: new Date(Date.now() - 4000).toISOString(),
      level: 'DEBUG',
      service: 'embeddings',
      message: 'Processing embedding request',
      details: 'Batch size: 32, Model: BAAI/bge-base-en-v1.5'
    },
    {
      id: 6,
      timestamp: new Date(Date.now() - 5000).toISOString(),
      level: 'INFO',
      service: 'system',
      message: 'Docker container health check passed',
      details: 'Container: unicorn-vllm, Status: healthy'
    },
    {
      id: 7,
      timestamp: new Date(Date.now() - 6000).toISOString(),
      level: 'WARN',
      service: 'admin-dashboard',
      message: 'High memory usage detected',
      details: 'Memory usage: 87%, Threshold: 85%'
    },
    {
      id: 8,
      timestamp: new Date(Date.now() - 7000).toISOString(),
      level: 'INFO',
      service: 'reranker',
      message: 'Reranking request completed',
      details: 'Documents: 150, Time: 0.8s, Model: BAAI/bge-reranker-v2-m3'
    }
  ]);

  useEffect(() => {
    loadLogs();
  }, [selectedService, logLevel]);

  useEffect(() => {
    filterLogs();
  }, [logs, searchQuery, logLevel, selectedService]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`/api/v1/logs?service=${selectedService}&level=${logLevel}&limit=${maxLines}`);
      // const data = await response.json();
      
      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      setLogs(mockLogs);
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterLogs = () => {
    let filtered = [...logs];

    // Filter by service
    if (selectedService !== 'all') {
      filtered = filtered.filter(log => log.service === selectedService);
    }

    // Filter by log level
    if (logLevel !== 'all') {
      filtered = filtered.filter(log => log.level === logLevel);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(query) ||
        log.service.toLowerCase().includes(query) ||
        log.details?.toLowerCase().includes(query)
      );
    }

    // Limit number of logs
    filtered = filtered.slice(0, maxLines);

    setFilteredLogs(filtered);
  };

  const toggleStreaming = () => {
    setIsStreaming(!isStreaming);
    if (!isStreaming) {
      // Start streaming (mock implementation)
      const interval = setInterval(() => {
        const newLog = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: ['INFO', 'WARN', 'ERROR', 'DEBUG', 'SUCCESS'][Math.floor(Math.random() * 5)],
          service: serviceLogSources[Math.floor(Math.random() * (serviceLogSources.length - 1)) + 1].id,
          message: 'Real-time log message generated',
          details: 'This is a simulated real-time log entry'
        };
        setLogs(prevLogs => [newLog, ...prevLogs.slice(0, maxLines - 1)]);
      }, 2000);

      // Clean up interval when component unmounts or streaming stops
      return () => clearInterval(interval);
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setFilteredLogs([]);
  };

  const exportLogs = () => {
    const logText = filteredLogs.map(log => 
      `${log.timestamp} [${log.level}] ${log.service}: ${log.message}${log.details ? ` - ${log.details}` : ''}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getLogCount = (level) => {
    if (level === 'all') return logs.length;
    return logs.filter(log => log.level === level).length;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden" 
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Logs & Diagnostics
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Monitor system logs, troubleshoot issues, and analyze service behavior
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={exportLogs}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Export
          </button>
          <button
            onClick={clearLogs}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <TrashIcon className="h-5 w-5" />
            Clear
          </button>
          <button
            onClick={loadLogs}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-5 w-5" />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{getLogCount('all')}</p>
            </div>
            <DocumentTextIcon className="h-6 w-6 text-gray-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Errors</p>
              <p className="text-xl font-bold text-red-600">{getLogCount('ERROR')}</p>
            </div>
            <ExclamationCircleIcon className="h-6 w-6 text-red-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Warnings</p>
              <p className="text-xl font-bold text-yellow-600">{getLogCount('WARN')}</p>
            </div>
            <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Info</p>
              <p className="text-xl font-bold text-blue-600">{getLogCount('INFO')}</p>
            </div>
            <InformationCircleIcon className="h-6 w-6 text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Success</p>
              <p className="text-xl font-bold text-green-600">{getLogCount('SUCCESS')}</p>
            </div>
            <CheckCircleIcon className="h-6 w-6 text-green-500" />
          </div>
        </div>
      </motion.div>

      {/* Controls */}
      <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Service Filter */}
            <div className="flex items-center gap-2">
              <ServerIcon className="h-5 w-5 text-gray-500" />
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                {serviceLogSources.map(service => (
                  <option key={service.id} value={service.id}>{service.name}</option>
                ))}
              </select>
            </div>

            {/* Log Level Filter */}
            <div className="flex items-center gap-2">
              <FunnelIcon className="h-5 w-5 text-gray-500" />
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="all">All Levels</option>
                <option value="ERROR">Errors</option>
                <option value="WARN">Warnings</option>
                <option value="INFO">Info</option>
                <option value="DEBUG">Debug</option>
                <option value="SUCCESS">Success</option>
              </select>
            </div>

            {/* Search */}
            <div className="flex items-center gap-2">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-500" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Auto-scroll toggle */}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Auto-scroll</span>
            </label>

            {/* Streaming toggle */}
            <button
              onClick={toggleStreaming}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
                isStreaming 
                  ? 'bg-red-600 text-white hover:bg-red-700' 
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isStreaming ? <PauseIcon className="h-4 w-4" /> : <PlayIcon className="h-4 w-4" />}
              {isStreaming ? 'Stop' : 'Stream'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Log Viewer */}
      <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Live Logs ({filteredLogs.length})
            </h2>
            <div className="flex items-center gap-2">
              {isStreaming && (
                <div className="flex items-center gap-2 text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm">Streaming</span>
                </div>
              )}
              <ClockIcon className="h-5 w-5 text-gray-500" />
              <span className="text-sm text-gray-500">{formatTimestamp(new Date().toISOString())}</span>
            </div>
          </div>
        </div>

        <div 
          ref={logsContainerRef}
          className="h-96 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900 font-mono text-sm"
        >
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No logs found</h3>
                <p className="mt-1 text-sm text-gray-500">Try adjusting your filters or check back later.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredLogs.map((log) => {
                const logConfig = logLevels[log.level] || logLevels.INFO;
                const LogIcon = logConfig.icon;
                
                return (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`p-3 rounded-lg border-l-4 ${logConfig.bg} border-l-current ${logConfig.color}`}
                  >
                    <div className="flex items-start gap-3">
                      <LogIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatTimestamp(log.timestamp)}
                          </span>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${logConfig.color} bg-current bg-opacity-10`}>
                            {log.level}
                          </span>
                          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                            {log.service}
                          </span>
                        </div>
                        <p className="text-gray-900 dark:text-white break-words">
                          {log.message}
                        </p>
                        {log.details && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {log.details}
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}