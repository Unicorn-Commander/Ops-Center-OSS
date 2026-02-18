import React, { useState, useEffect, useCallback } from 'react';

const ColonelAvatar = ({ size = 'md' }) => {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12', xl: 'w-16 h-16' };
  return <img src="/logos/The_Colonel.webp" alt="The Colonel" className={`${sizes[size] || sizes.md} rounded-full object-cover`} />;
};

/**
 * Collapsible sidebar for Colonel chat page.
 * Shows sessions, memory search, quick actions, and skills.
 */
export default function ColonelSidebar({
  open,
  onClose,
  sessions = [],
  onSelectSession,
  onNewSession,
  currentSessionId,
  colonelName,
  serverName,
  online,
}) {
  const [memoryQuery, setMemoryQuery] = useState('');
  const [memoryResults, setMemoryResults] = useState([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('sessions');

  const searchMemory = useCallback(async () => {
    if (!memoryQuery.trim()) {
      setMemoryResults([]);
      return;
    }
    try {
      setMemoryLoading(true);
      const res = await fetch(`/api/v1/colonel/memory/search?q=${encodeURIComponent(memoryQuery)}&limit=10`);
      if (res.ok) {
        const data = await res.json();
        setMemoryResults(data.results || []);
      }
    } catch {
      // ignore
    } finally {
      setMemoryLoading(false);
    }
  }, [memoryQuery]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (memoryQuery.length >= 2) searchMemory();
    }, 400);
    return () => clearTimeout(timeout);
  }, [memoryQuery, searchMemory]);

  const quickActions = [
    { label: 'System Status', prompt: 'Show me the full system status' },
    { label: 'Containers', prompt: 'List all running containers' },
    { label: 'Disk Usage', prompt: 'Check disk usage across all drives' },
    { label: 'GPU Status', prompt: 'Show GPU memory and utilization' },
    { label: 'Recent Logs', prompt: 'Show recent error logs from all containers' },
    { label: 'Service Health', prompt: 'Run a health check on all services' },
  ];

  if (!open) return null;

  return (
    <div className="fixed inset-y-0 left-0 z-50 flex" onClick={onClose}>
      <div
        className="w-72 bg-gray-900 border-r border-gray-700 flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-700 bg-gradient-to-r from-purple-900/40 to-gray-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ColonelAvatar size="md" />
              <div>
                <p className="text-sm font-semibold text-white">{colonelName || 'The Colonel'}</p>
                <p className="text-xs text-gray-400">{serverName || 'Server'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${online ? 'bg-green-400' : 'bg-red-400'}`} />
              <button onClick={onClose} className="text-gray-400 hover:text-white">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Section Tabs */}
        <div className="flex border-b border-gray-700">
          {['sessions', 'memory', 'actions'].map(section => (
            <button
              key={section}
              onClick={() => setActiveSection(section)}
              className={`flex-1 py-2 text-xs font-medium capitalize transition-colors ${
                activeSection === section
                  ? 'text-purple-400 border-b-2 border-purple-400 bg-purple-900/10'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {section}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Sessions */}
          {activeSection === 'sessions' && (
            <div className="p-3 space-y-2">
              <button
                onClick={onNewSession}
                className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Session
              </button>
              {sessions.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-4">No sessions yet</p>
              ) : (
                sessions.map(session => (
                  <button
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      session.id === currentSessionId
                        ? 'bg-purple-900/30 text-purple-300 border border-purple-700'
                        : 'text-gray-300 hover:bg-gray-800'
                    }`}
                  >
                    <p className="truncate font-medium">{session.title || 'New Session'}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {session.message_count} messages
                    </p>
                  </button>
                ))
              )}
            </div>
          )}

          {/* Memory Search */}
          {activeSection === 'memory' && (
            <div className="p-3 space-y-3">
              <div className="relative">
                <input
                  type="text"
                  value={memoryQuery}
                  onChange={e => setMemoryQuery(e.target.value)}
                  placeholder="Search memories..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
                {memoryLoading && (
                  <div className="absolute right-3 top-2.5">
                    <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
              </div>
              {memoryResults.length > 0 ? (
                <div className="space-y-2">
                  {memoryResults.map((mem, i) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                      <p className="text-xs text-gray-300">{typeof mem === 'string' ? mem : mem.memory || mem.text || JSON.stringify(mem)}</p>
                    </div>
                  ))}
                </div>
              ) : memoryQuery.length >= 2 && !memoryLoading ? (
                <p className="text-xs text-gray-500 text-center py-4">No memories found</p>
              ) : (
                <p className="text-xs text-gray-500 text-center py-4">Type to search Colonel's memory</p>
              )}
            </div>
          )}

          {/* Quick Actions */}
          {activeSection === 'actions' && (
            <div className="p-3 space-y-2">
              <p className="text-xs text-gray-400 mb-2">Quick commands</p>
              {quickActions.map(action => (
                <button
                  key={action.label}
                  onClick={() => {
                    onSelectSession(null, action.prompt);
                    onClose();
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {/* Overlay */}
      <div className="flex-1 bg-black/50" />
    </div>
  );
}
