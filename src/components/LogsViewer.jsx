import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, ArrowPathIcon, ArrowDownIcon } from '@heroicons/react/24/outline';

export default function LogsViewer({ containerName, isOpen, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [lines, setLines] = useState(100);
  const logsEndRef = useRef(null);
  const logsContainerRef = useRef(null);

  const fetchLogs = async () => {
    if (!containerName) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/monitoring/logs/${containerName}?lines=${lines}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && containerName) {
      fetchLogs();
      // Set up polling for live logs
      const interval = setInterval(fetchLogs, 3000);
      return () => clearInterval(interval);
    }
  }, [isOpen, containerName, lines]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (logsContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 10;
      setAutoScroll(isAtBottom);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Container Logs: {containerName}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Showing last {lines} lines
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={lines}
              onChange={(e) => setLines(Number(e.target.value))}
              className="px-3 py-1 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value={50}>50 lines</option>
              <option value={100}>100 lines</option>
              <option value={200}>200 lines</option>
              <option value={500}>500 lines</option>
              <option value={1000}>1000 lines</option>
            </select>
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
              title="Refresh logs"
            >
              <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`p-2 rounded-lg ${autoScroll ? 'bg-blue-100 dark:bg-blue-900' : 'bg-gray-100 dark:bg-gray-700'} hover:bg-gray-200 dark:hover:bg-gray-600`}
              title="Auto-scroll"
            >
              <ArrowDownIcon className="h-5 w-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Logs Content */}
        <div 
          ref={logsContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-auto bg-gray-900 p-4 font-mono text-sm"
        >
          {loading && logs.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              Loading logs...
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              No logs available
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <LogLine key={index} log={log} />
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t dark:border-gray-700 flex items-center justify-between text-sm">
          <div className="text-gray-500 dark:text-gray-400">
            {logs.length} lines • {autoScroll ? 'Auto-scrolling' : 'Manual scroll'}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function LogLine({ log }) {
  // Parse log level and colorize accordingly
  const getLogColor = () => {
    const lowerLog = log.toLowerCase();
    if (lowerLog.includes('error') || lowerLog.includes('fatal')) {
      return 'text-red-400';
    } else if (lowerLog.includes('warn')) {
      return 'text-yellow-400';
    } else if (lowerLog.includes('info')) {
      return 'text-blue-400';
    } else if (lowerLog.includes('debug')) {
      return 'text-gray-400';
    } else if (lowerLog.includes('success') || lowerLog.includes('started')) {
      return 'text-green-400';
    }
    return 'text-gray-300';
  };

  // Extract timestamp if present
  const timestampMatch = log.match(/^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.\d]*[Z\+\-\d]*)/);
  const timestamp = timestampMatch ? timestampMatch[1] : null;
  const message = timestamp ? log.substring(timestamp.length).trim() : log;

  return (
    <div className="flex gap-2 text-xs leading-relaxed hover:bg-gray-800 px-2 py-0.5 rounded">
      {timestamp && (
        <span className="text-gray-500 whitespace-nowrap">
          {new Date(timestamp).toLocaleTimeString()}
        </span>
      )}
      <span className={`flex-1 break-all ${getLogColor()}`}>
        {message}
      </span>
    </div>
  );
}