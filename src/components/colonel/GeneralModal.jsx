import React, { useState, useEffect, useCallback } from 'react';
import * as colonelApi from '../../services/colonelApi';

/**
 * The General - Multi-Colonel coordination modal.
 * Shows all registered Colonels across servers, their status,
 * and allows orchestration of cross-server operations.
 */

const ColonelAvatar = ({ size = 'md' }) => {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return <img src="/logos/The_Colonel.webp" alt="" className={`${sizes[size] || sizes.md} rounded-full object-cover`} />;
};

function StatusDot({ online }) {
  return (
    <span className={`w-2.5 h-2.5 rounded-full inline-block ${
      online ? 'bg-green-400' : 'bg-red-400'
    }`} />
  );
}

function ColonelCard({ colonel, onSelect }) {
  const isLocal = colonel.local || colonel.is_self;
  return (
    <div
      className={`rounded-xl border p-4 transition-all cursor-pointer hover:border-purple-500/50 ${
        isLocal
          ? 'bg-purple-900/20 border-purple-700/40'
          : colonel.online
          ? 'bg-gray-800/50 border-gray-700/50'
          : 'bg-gray-800/30 border-gray-700/30 opacity-60'
      }`}
      onClick={() => onSelect?.(colonel)}
    >
      <div className="flex items-center gap-3 mb-3">
        <ColonelAvatar size="md" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white truncate">{colonel.name}</h3>
            {isLocal && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-purple-800/60 text-purple-300">This Server</span>
            )}
          </div>
          <p className="text-xs text-gray-400 truncate">{colonel.server_name || colonel.hostname || 'Unknown server'}</p>
        </div>
        <StatusDot online={colonel.online !== false} />
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-gray-900/50 rounded-lg p-2">
          <div className="text-sm font-bold text-purple-300">{colonel.skills_count ?? colonel.skills_loaded ?? '—'}</div>
          <div className="text-[10px] text-gray-500">Skills</div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-2">
          <div className="text-sm font-bold text-blue-300">{colonel.active_sessions ?? '—'}</div>
          <div className="text-[10px] text-gray-500">Sessions</div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-2">
          <div className="text-sm font-bold text-amber-300">{colonel.memory_entries ?? '—'}</div>
          <div className="text-[10px] text-gray-500">Memory</div>
        </div>
      </div>

      {colonel.mission && (
        <div className="mt-2 text-xs text-gray-400 capitalize">
          Mission: {colonel.mission}
        </div>
      )}
    </div>
  );
}

export default function GeneralModal({ open, onClose }) {
  const [loading, setLoading] = useState(true);
  const [localStatus, setLocalStatus] = useState(null);
  const [colonels, setColonels] = useState([]);
  const [selectedColonel, setSelectedColonel] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusData, registryData] = await Promise.allSettled([
        colonelApi.getStatus(),
        colonelApi.getColonelRegistry(),
      ]);

      if (statusData.status === 'fulfilled') {
        setLocalStatus(statusData.value);
      }

      if (registryData.status === 'fulfilled' && registryData.value.colonels?.length > 0) {
        setColonels(registryData.value.colonels);
      } else if (statusData.status === 'fulfilled') {
        // No registry available - show local Colonel as the only one
        const s = statusData.value;
        setColonels([{
          id: 'local',
          name: s.config?.name || 'The Colonel',
          server_name: s.config?.server_name || 'This Server',
          online: s.online,
          local: true,
          is_self: true,
          skills_loaded: s.skills_loaded,
          active_sessions: s.active_sessions,
          memory_entries: s.memory_entries,
          mission: s.config?.mission,
          model: s.config?.model,
        }]);
      }
    } catch {
      // Best effort
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      fetchData();
      const interval = setInterval(fetchData, 15000);
      return () => clearInterval(interval);
    }
  }, [open, fetchData]);

  if (!open) return null;

  const onlineCount = colonels.filter(c => c.online !== false).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gradient-to-r from-purple-900/40 to-gray-900">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-xl">🎖️</span> The General — Command Overview
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {onlineCount} Colonel{onlineCount !== 1 ? 's' : ''} online across {colonels.length} server{colonels.length !== 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700/50 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              <span className="ml-3 text-gray-400">Scanning for Colonels...</span>
            </div>
          ) : colonels.length === 0 ? (
            <div className="text-center py-12">
              <span className="text-4xl mb-4 block">🎖️</span>
              <h3 className="text-lg font-semibold text-gray-200 mb-2">No Colonels Detected</h3>
              <p className="text-sm text-gray-400 max-w-md mx-auto">
                Deploy The Colonel on this server to get started. Once deployed, The General will coordinate
                all Colonels across your infrastructure.
              </p>
            </div>
          ) : (
            <>
              {/* Selected Colonel Detail */}
              {selectedColonel && (
                <div className="mb-4 bg-purple-900/20 rounded-xl border border-purple-600/40 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <ColonelAvatar size="md" />
                      <div>
                        <h3 className="font-semibold text-white">{selectedColonel.name}</h3>
                        <p className="text-xs text-gray-400">{selectedColonel.server_name || selectedColonel.hostname}</p>
                      </div>
                    </div>
                    <button onClick={() => setSelectedColonel(null)} className="text-gray-400 hover:text-white text-xs">Dismiss</button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-gray-900/50 rounded-lg p-2">
                      <span className="text-gray-500">Model:</span>{' '}
                      <span className="text-purple-300">{selectedColonel.model || 'Default'}</span>
                    </div>
                    <div className="bg-gray-900/50 rounded-lg p-2">
                      <span className="text-gray-500">Status:</span>{' '}
                      <span className={selectedColonel.online !== false ? 'text-green-400' : 'text-red-400'}>
                        {selectedColonel.online !== false ? 'Online' : 'Offline'}
                      </span>
                    </div>
                    {selectedColonel.mission && (
                      <div className="bg-gray-900/50 rounded-lg p-2 col-span-2">
                        <span className="text-gray-500">Mission:</span>{' '}
                        <span className="text-amber-300 capitalize">{selectedColonel.mission}</span>
                      </div>
                    )}
                  </div>
                  {(selectedColonel.local || selectedColonel.is_self) && (
                    <a
                      href="/admin/ai/colonel"
                      className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded-lg text-xs text-white transition-colors"
                    >
                      Open Chat
                    </a>
                  )}
                </div>
              )}

              {/* Colonel Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {colonels.map((colonel, i) => (
                  <ColonelCard
                    key={colonel.id || i}
                    colonel={colonel}
                    onSelect={setSelectedColonel}
                  />
                ))}
              </div>

              {/* A2A Protocol Info */}
              <div className="mt-6 bg-gray-800/50 rounded-xl border border-gray-700/50 p-4">
                <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <span>🌐</span> A2A Protocol
                </h3>
                <p className="text-xs text-gray-400">
                  Colonels communicate using the Linux Foundation's Agent-to-Agent (A2A) protocol.
                  Each Colonel publishes an Agent Card at <code className="bg-gray-900 px-1 py-0.5 rounded text-purple-300 text-[11px]">/.well-known/agent.json</code> for
                  discovery and invocation by The General and other agents in Brigade.
                </p>
              </div>

              {/* Future: Cross-server operations */}
              {colonels.length > 1 && (
                <div className="mt-4 bg-purple-900/20 rounded-xl border border-purple-700/30 p-4">
                  <h3 className="text-sm font-semibold text-purple-300 mb-2">Multi-Server Operations</h3>
                  <p className="text-xs text-gray-400">
                    With multiple Colonels online, The General can coordinate operations across servers — rolling
                    deployments, synchronized health checks, and cross-server log analysis.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 px-6 py-3 bg-gray-900/50 flex items-center justify-between">
          <p className="text-[11px] text-gray-500">
            The General orchestrates all Colonels via Brigade
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
