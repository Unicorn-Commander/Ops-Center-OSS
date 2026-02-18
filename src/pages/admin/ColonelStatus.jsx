import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const ColonelAvatar = ({ size = 'md' }) => {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12', xl: 'w-16 h-16' };
  return <img src="/logos/The_Colonel.webp" alt="The Colonel" className={`${sizes[size] || sizes.md} rounded-full object-cover`} />;
};

export default function ColonelStatus() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [skills, setSkills] = useState([]);
  const [audit, setAudit] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, skillsRes, auditRes, sessionsRes] = await Promise.allSettled([
        fetch('/api/v1/colonel/status'),
        fetch('/api/v1/colonel/skills'),
        fetch('/api/v1/colonel/audit?limit=20'),
        fetch('/api/v1/colonel/sessions'),
      ]);

      if (statusRes.status === 'fulfilled' && statusRes.value.ok) {
        setStatus(await statusRes.value.json());
      }
      if (skillsRes.status === 'fulfilled' && skillsRes.value.ok) {
        const data = await skillsRes.value.json();
        setSkills(data.skills || []);
      }
      if (auditRes.status === 'fulfilled' && auditRes.value.ok) {
        const data = await auditRes.value.json();
        setAudit(data.entries || []);
      }
      if (sessionsRes.status === 'fulfilled' && sessionsRes.value.ok) {
        const data = await sessionsRes.value.json();
        setSessions(data.sessions || []);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const toggleSkill = async (skillId) => {
    try {
      const res = await fetch(`/api/v1/colonel/skills/${skillId}/toggle`, { method: 'PUT' });
      if (res.ok) {
        const data = await res.json();
        setSkills(prev => prev.map(s => s.id === skillId ? { ...s, enabled: data.enabled } : s));
      }
    } catch (e) {
      console.error('Failed to toggle skill:', e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading Colonel status...</p>
        </div>
      </div>
    );
  }

  const config = status?.config || {};

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/60 to-gray-900 border-b border-purple-800/30">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <ColonelAvatar size="lg" />
                {config.name || 'The Colonel'} — Status Dashboard
              </h1>
              <p className="text-gray-400 mt-1">{config.server_name || 'Server'} • {config.mission || 'general'} mode</p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => navigate('/admin/ai/colonel')} className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors">
                Open Chat
              </button>
              <button onClick={() => navigate('/admin/ai/colonel/setup')} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
                Reconfigure
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6 mt-4">
        <div className="flex gap-1 border-b border-gray-700">
          {['overview', 'skills', 'sessions', 'audit'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'text-purple-400 border-b-2 border-purple-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatusCard
                label="Status"
                value={status?.online ? 'Online' : 'Offline'}
                color={status?.online ? 'green' : 'red'}
                icon="⚡"
              />
              <StatusCard
                label="Active Sessions"
                value={status?.active_sessions ?? 0}
                color="blue"
                icon="💬"
              />
              <StatusCard
                label="Skills Loaded"
                value={status?.skills_loaded ?? 0}
                color="purple"
                icon="🛠️"
              />
              <StatusCard
                label="Memory Entries"
                value={status?.memory_entries ?? 0}
                color="amber"
                icon="🧠"
              />
            </div>

            {/* A2A & Graph Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-5">
                <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span>🌐</span> A2A Protocol
                </h2>
                <p className="text-sm text-gray-400 mb-2">Agent Card published at:</p>
                <code className="text-xs text-purple-400 bg-gray-900 px-2 py-1 rounded">
                  /.well-known/agent.json
                </code>
                <p className="text-xs text-gray-500 mt-2">
                  Other agents (e.g. Brigade) can discover and invoke this Colonel via the A2A protocol.
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-5">
                <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span>🔗</span> Knowledge Graph
                </h2>
                {status?.graph_stats?.available ? (
                  <div className="space-y-1">
                    <ConfigRow label="Servers" value={status.graph_stats.server_count ?? 0} />
                    <ConfigRow label="Containers" value={status.graph_stats.container_count ?? 0} />
                    <ConfigRow label="Services" value={status.graph_stats.service_count ?? 0} />
                    <ConfigRow label="Users" value={status.graph_stats.user_count ?? 0} />
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    Graph DB not available. Install kuzu: <code className="text-xs bg-gray-900 px-1 rounded">pip install kuzu</code>
                  </p>
                )}
              </div>
            </div>

            {/* Configuration Details */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Configuration</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ConfigRow label="Name" value={config.name} />
                <ConfigRow label="Server" value={config.server_name} />
                <ConfigRow label="Mission" value={config.mission} />
                <ConfigRow label="Model" value={config.model} />
                <ConfigRow label="Admin Only" value={config.admin_only ? 'Yes' : 'No'} />
                <ConfigRow label="Onboarded" value={config.onboarded ? 'Yes' : 'No'} />
              </div>
              {config.personality && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Personality</h3>
                  <div className="flex gap-6">
                    <PersonalityBar label="Formality" value={config.personality.formality} />
                    <PersonalityBar label="Verbosity" value={config.personality.verbosity} />
                    <PersonalityBar label="Humor" value={config.personality.humor} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'skills' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Skills ({skills.length})</h2>
            {skills.length === 0 ? (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
                <p className="text-gray-400">No skills loaded. The skill router may not be initialized.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {skills.map(skill => (
                  <div key={skill.id} className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-white">{skill.name}</h3>
                      <button
                        onClick={() => toggleSkill(skill.id)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          skill.enabled
                            ? 'bg-green-900/40 text-green-400 hover:bg-green-900/60'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                        }`}
                      >
                        {skill.enabled ? 'Enabled' : 'Disabled'}
                      </button>
                    </div>
                    <p className="text-sm text-gray-400">{skill.description}</p>
                    {skill.actions && (
                      <p className="text-xs text-gray-500 mt-2">{skill.actions} actions</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Chat Sessions ({sessions.length})</h2>
            {sessions.length === 0 ? (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
                <p className="text-gray-400">No sessions found.</p>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg border border-gray-700 divide-y divide-gray-700">
                {sessions.map(session => (
                  <div key={session.id} className="p-4 hover:bg-gray-750 transition-colors">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-white">{session.title || 'Untitled'}</p>
                        <p className="text-xs text-gray-500">
                          {session.message_count} messages • {session.updated_at ? new Date(session.updated_at).toLocaleString() : 'Unknown'}
                        </p>
                      </div>
                      <button
                        onClick={() => navigate(`/admin/ai/colonel?session=${session.id}`)}
                        className="px-3 py-1 text-xs bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 rounded transition-colors"
                      >
                        Resume
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Audit Log ({audit.length})</h2>
            {audit.length === 0 ? (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
                <p className="text-gray-400">No audit entries yet.</p>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-750">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Action</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Skill</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Result</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {audit.map(entry => (
                      <tr key={entry.id} className="hover:bg-gray-750">
                        <td className="px-4 py-3 text-sm text-gray-400">
                          {entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-white">
                          {entry.action_name || entry.action_type}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400">
                          {entry.skill_name || '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400 max-w-xs truncate">
                          {entry.result_summary || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            entry.success
                              ? 'bg-green-900/40 text-green-400'
                              : 'bg-red-900/40 text-red-400'
                          }`}>
                            {entry.success ? 'OK' : 'Failed'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusCard({ label, value, color, icon }) {
  const colors = {
    green: 'bg-green-900/30 border-green-700 text-green-400',
    red: 'bg-red-900/30 border-red-700 text-red-400',
    blue: 'bg-blue-900/30 border-blue-700 text-blue-400',
    purple: 'bg-purple-900/30 border-purple-700 text-purple-400',
    amber: 'bg-amber-900/30 border-amber-700 text-amber-400',
  };

  return (
    <div className={`rounded-lg border p-4 ${colors[color] || colors.blue}`}>
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-2xl font-bold">{value}</span>
      </div>
      <p className="text-sm mt-1 opacity-80">{label}</p>
    </div>
  );
}

function ConfigRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-400">{label}</span>
      <span className="text-sm text-white font-medium">{value || '—'}</span>
    </div>
  );
}

function PersonalityBar({ label, value }) {
  const pct = ((value || 5) / 10) * 100;
  return (
    <div className="flex-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-400">{label}</span>
        <span className="text-xs text-gray-500">{value || 5}/10</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full bg-purple-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
