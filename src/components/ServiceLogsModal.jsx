import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  MagnifyingGlassIcon,
  DocumentArrowDownIcon,
  PauseIcon,
  PlayIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const LOG_LEVELS = {
  ERROR: { color: 'text-red-400', bg: 'bg-red-900/20' },
  WARN: { color: 'text-yellow-400', bg: 'bg-yellow-900/20' },
  INFO: { color: 'text-blue-400', bg: 'bg-blue-900/20' },
  DEBUG: { color: 'text-gray-400', bg: 'bg-gray-900/20' },
  DEFAULT: { color: 'text-green-400', bg: 'bg-transparent' }
};

export default function ServiceLogsModal({ service, onClose }) {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [maxLines, setMaxLines] = useState(1000);
  const logsEndRef = useRef(null);
  const logsContainerRef = useRef(null);

  // Simulate fetching logs (replace with actual API call)
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        // In a real implementation, this would be an API call
        const response = await fetch(`/api/v1/services/${service.name}/logs?lines=${maxLines}`);
        if (response.ok) {
          const logData = await response.json();
          setLogs(logData.logs || []);
        } else {
          // Fallback to mock data for now
          generateMockLogs();
        }
      } catch (error) {
        console.error('Failed to fetch logs:', error);
        generateMockLogs();
      }
    };

    const generateMockLogs = () => {
      const mockLogs = [];
      const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
      const messages = [
        'Service started successfully',
        'Processing request from client',
        'Database connection established',
        'Cache miss for key: user_123',
        'Memory usage: 45.2MB',
        'Request completed in 125ms',
        'Scheduled task executed',
        'Configuration loaded',
        'Health check passed',
        'Connection timeout detected'
      ];

      for (let i = 0; i < 150; i++) {
        const level = levels[Math.floor(Math.random() * levels.length)];
        const message = messages[Math.floor(Math.random() * messages.length)];
        const timestamp = new Date(Date.now() - (150 - i) * 1000).toISOString();
        
        mockLogs.push({
          id: i,
          timestamp,
          level,
          message: `${message} - Line ${i + 1}`,
          raw: `${timestamp} [${level}] ${service.name}: ${message} - Line ${i + 1}`
        });
      }
      
      setLogs(mockLogs);
    };

    fetchLogs();

    // Set up real-time log streaming (WebSocket)
    if (!isPaused) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs/${service.name}`);
      
      ws.onmessage = (event) => {
        try {
          const logEntry = JSON.parse(event.data);
          setLogs(prev => {
            const updated = [...prev, logEntry];
            return updated.slice(-maxLines); // Keep only recent logs
          });
        } catch (error) {
          console.error('Failed to parse log entry:', error);
        }
      };

      return () => {
        ws.close();
      };
    }
  }, [service.name, maxLines, isPaused]);

  // Filter logs based on search term and level
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.level.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedLevel !== 'all') {
      filtered = filtered.filter(log => log.level === selectedLevel);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, selectedLevel]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (isAutoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, isAutoScroll]);

  const handleScroll = () => {
    if (logsContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop === clientHeight;
      setIsAutoScroll(isAtBottom);
    }
  };

  const scrollToTop = () => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
      setIsAutoScroll(false);
    }
  };

  const scrollToBottom = () => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTo({ 
        top: logsContainerRef.current.scrollHeight, 
        behavior: 'smooth' 
      });
      setIsAutoScroll(true);
    }
  };

  const downloadLogs = () => {
    const logContent = filteredLogs.map(log => log.raw).join('\n');
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${service.name}-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    setLogs([]);
    setFilteredLogs([]);
  };

  const getLogLevelStyle = (level) => {
    return LOG_LEVELS[level] || LOG_LEVELS.DEFAULT;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

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
          className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-6xl h-5/6 flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Service Logs: {service.display_name || service.name}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {filteredLogs.length} of {logs.length} log entries
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-400" />
            </button>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-4 p-4 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>

            {/* Level Filter */}
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="all">All Levels</option>
              <option value="ERROR">Errors</option>
              <option value="WARN">Warnings</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPaused(!isPaused)}
                className={`flex items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                  isPaused 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                }`}
              >
                {isPaused ? <PlayIcon className="h-4 w-4" /> : <PauseIcon className="h-4 w-4" />}
                {isPaused ? 'Resume' : 'Pause'}
              </button>
              
              <button
                onClick={scrollToTop}
                className="p-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                title="Scroll to top"
              >
                <ArrowUpIcon className="h-4 w-4" />
              </button>
              
              <button
                onClick={scrollToBottom}
                className="p-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                title="Scroll to bottom"
              >
                <ArrowDownIcon className="h-4 w-4" />
              </button>
              
              <button
                onClick={downloadLogs}
                className="flex items-center gap-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <DocumentArrowDownIcon className="h-4 w-4" />
                Download
              </button>
              
              <button
                onClick={clearLogs}
                className="flex items-center gap-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                <TrashIcon className="h-4 w-4" />
                Clear
              </button>
            </div>
          </div>

          {/* Logs Content */}
          <div 
            ref={logsContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-auto bg-gray-900 text-green-400 font-mono text-sm p-4"
          >
            {filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No logs available</p>
                  {searchTerm && <p className="text-sm mt-2">Try adjusting your search criteria</p>}
                </div>
              </div>
            ) : (
              <>
                {filteredLogs.map((log, index) => {
                  const levelStyle = getLogLevelStyle(log.level);
                  return (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: Math.min(index * 0.01, 0.5) }}
                      className={`flex items-start gap-4 py-1 px-2 rounded ${levelStyle.bg} hover:bg-gray-800/50 transition-colors`}
                    >
                      <span className="text-gray-500 text-xs min-w-20 mt-0.5">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      <span className={`${levelStyle.color} text-xs min-w-12 font-bold mt-0.5`}>
                        [{log.level}]
                      </span>
                      <span className="flex-1 break-all">
                        {log.message}
                      </span>
                    </motion.div>
                  );
                })}
                <div ref={logsEndRef} />
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>
                Auto-scroll: {isAutoScroll ? '✓ On' : '✗ Off'}
              </span>
              <span>
                Status: {isPaused ? '⏸ Paused' : '▶ Live'}
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600 dark:text-gray-400">
                Max lines:
              </label>
              <select
                value={maxLines}
                onChange={(e) => setMaxLines(parseInt(e.target.value))}
                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value={500}>500</option>
                <option value={1000}>1000</option>
                <option value={2000}>2000</option>
                <option value={5000}>5000</option>
              </select>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}