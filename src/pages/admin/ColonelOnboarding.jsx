import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ColonelAvatar = ({ size = 'md' }) => {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12', xl: 'w-16 h-16' };
  return <img src="/logos/The_Colonel.webp" alt="The Colonel" className={`${sizes[size] || sizes.md} rounded-full object-cover`} />;
};

const STEPS = [
  { label: 'Detect', description: 'Scanning environment' },
  { label: 'Skills', description: 'Select capabilities' },
  { label: 'Name', description: 'Name your Colonel' },
  { label: 'Mission', description: 'Set focus area' },
  { label: 'Personality', description: 'Communication style' },
  { label: 'Access', description: 'Who can use it' },
  { label: 'Model', description: 'Choose LLM' },
  { label: 'Deploy', description: 'Review & deploy' },
];

const MISSIONS = [
  { id: 'devops', label: 'DevOps', desc: 'Container management, deployments, system health', icon: '🐳' },
  { id: 'monitoring', label: 'Monitoring', desc: 'Logs, alerts, performance metrics', icon: '📊' },
  { id: 'security', label: 'Security', desc: 'Access control, audit trails, vulnerability scanning', icon: '🔒' },
  { id: 'general', label: 'General', desc: 'All-purpose server management assistant', icon: '🎖️' },
];

const NAME_SUGGESTIONS = ['Col. Corelli', 'Col. Tensor', 'Col. Atlas', 'Col. Phoenix', 'Col. Nova'];

const MODELS = [
  { id: 'anthropic/claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5', desc: 'Best balance of speed and capability (Recommended)' },
  { id: 'anthropic/claude-opus-4-6', label: 'Claude Opus 4.6', desc: 'Most capable, slower and more expensive' },
  { id: 'anthropic/claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5', desc: 'Fastest, good for simple tasks' },
  { id: 'openai/gpt-4o', label: 'GPT-4o', desc: 'OpenAI flagship model' },
  { id: 'google/gemini-2.0-flash-exp:free', label: 'Gemini 2.0 Flash (Free)', desc: 'Free tier, good for testing' },
];

export default function ColonelOnboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detection, setDetection] = useState(null);

  // Config state
  const [config, setConfig] = useState({
    name: 'Col. Corelli',
    server_name: '',
    mission: 'devops',
    personality: { formality: 7, verbosity: 5, humor: 4 },
    model: 'anthropic/claude-sonnet-4-5-20250929',
    enabled_skills: [],
    admin_only: true,
  });

  // Step 0: Auto-detect environment
  useEffect(() => {
    if (step === 0 && !detection) {
      setLoading(true);
      fetch('/api/v1/colonel/detect', { credentials: 'include' })
        .then(r => r.json())
        .then(data => {
          setDetection(data);
          setConfig(prev => ({
            ...prev,
            server_name: data.hostname || 'Server',
            enabled_skills: data.available_skills
              ?.filter(s => s.detected)
              .map(s => s.id) || ['docker-management', 'bash-execution', 'system-status'],
          }));
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [step, detection]);

  const handleDeploy = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/colonel/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(config),
      });
      if (resp.ok) {
        navigate('/admin/ai/colonel');
      } else {
        alert('Failed to deploy Colonel. Check console for details.');
      }
    } catch (e) {
      console.error('Deploy failed:', e);
      alert('Deploy failed: ' + e.message);
    }
    setLoading(false);
  };

  const next = () => setStep(s => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep(s => Math.max(s - 1, 0));

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center py-8 px-4">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="mb-3"><ColonelAvatar size="xl" /></div>
        <h1 className="text-2xl font-bold">Deploy The Colonel</h1>
        <p className="text-gray-400 mt-1">Set up your AI command agent in 8 simple steps</p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-1 mb-8 overflow-x-auto max-w-full px-4">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center">
            <div
              onClick={() => i < step && setStep(i)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium cursor-pointer transition-all ${
                i === step
                  ? 'bg-purple-600 text-white'
                  : i < step
                  ? 'bg-purple-900/50 text-purple-300 hover:bg-purple-800/50'
                  : 'bg-gray-800 text-gray-500'
              }`}
            >
              <span className="w-5 h-5 rounded-full bg-black/30 flex items-center justify-center text-[10px]">
                {i < step ? '✓' : i + 1}
              </span>
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < STEPS.length - 1 && <div className="w-4 h-px bg-gray-700 mx-0.5" />}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="w-full max-w-2xl bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
        {/* Step 0: Detect */}
        {step === 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Environment Detection</h2>
            {loading ? (
              <div className="flex items-center gap-3 text-gray-400">
                <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                Scanning your server...
              </div>
            ) : detection ? (
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-gray-400 text-xs">Hostname</div>
                    <div className="font-medium">{detection.hostname}</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-gray-400 text-xs">OS</div>
                    <div className="font-medium">{detection.os}</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-gray-400 text-xs">CPU</div>
                    <div className="font-medium">{detection.cpu_cores} cores</div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-gray-400 text-xs">RAM</div>
                    <div className="font-medium">{detection.ram_gb} GB</div>
                  </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-2">Containers ({detection.containers?.length || 0})</div>
                  <div className="flex flex-wrap gap-1">
                    {detection.containers?.slice(0, 20).map((c, i) => (
                      <span key={i} className="px-2 py-0.5 bg-green-900/30 text-green-300 rounded text-xs">{c.name}</span>
                    ))}
                    {(detection.containers?.length || 0) > 20 && (
                      <span className="px-2 py-0.5 bg-gray-700 text-gray-400 rounded text-xs">
                        +{detection.containers.length - 20} more
                      </span>
                    )}
                  </div>
                </div>
                {detection.gpus?.length > 0 && (
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="text-gray-400 text-xs mb-2">GPUs</div>
                    {detection.gpus.map((g, i) => (
                      <div key={i} className="text-sm">{g.name} ({g.memory_mb} MB)</div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-400">Detection failed. You can still proceed with manual setup.</p>
            )}
          </div>
        )}

        {/* Step 1: Skills */}
        {step === 1 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Select Skills</h2>
            <p className="text-sm text-gray-400 mb-4">Choose what The Colonel can do. Skills can be toggled later.</p>
            <div className="space-y-2">
              {(detection?.available_skills || []).map(skill => (
                <label
                  key={skill.id}
                  className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                    config.enabled_skills.includes(skill.id)
                      ? 'bg-purple-900/30 border border-purple-700/50'
                      : 'bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={config.enabled_skills.includes(skill.id)}
                    onChange={(e) => {
                      setConfig(prev => ({
                        ...prev,
                        enabled_skills: e.target.checked
                          ? [...prev.enabled_skills, skill.id]
                          : prev.enabled_skills.filter(s => s !== skill.id),
                      }));
                    }}
                    className="w-4 h-4 rounded accent-purple-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{skill.name}</div>
                    {!skill.detected && <span className="text-[10px] text-yellow-400">Not detected</span>}
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Name */}
        {step === 2 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Name Your Colonel</h2>
            <input
              type="text"
              value={config.name}
              onChange={e => setConfig(prev => ({ ...prev, name: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 mb-4"
              placeholder="Enter a name..."
            />
            <div className="flex flex-wrap gap-2">
              {NAME_SUGGESTIONS.map(name => (
                <button
                  key={name}
                  onClick={() => setConfig(prev => ({ ...prev, name }))}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                    config.name === name
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {name}
                </button>
              ))}
            </div>
            <div className="mt-4">
              <label className="text-sm text-gray-400 block mb-1">Server Name</label>
              <input
                type="text"
                value={config.server_name}
                onChange={e => setConfig(prev => ({ ...prev, server_name: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-sm"
                placeholder="e.g. Yoda, Production-1"
              />
            </div>
          </div>
        )}

        {/* Step 3: Mission */}
        {step === 3 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Mission Focus</h2>
            <p className="text-sm text-gray-400 mb-4">This shapes how The Colonel prioritizes and responds.</p>
            <div className="grid grid-cols-2 gap-3">
              {MISSIONS.map(m => (
                <button
                  key={m.id}
                  onClick={() => setConfig(prev => ({ ...prev, mission: m.id }))}
                  className={`text-left p-4 rounded-xl transition-all ${
                    config.mission === m.id
                      ? 'bg-purple-900/40 border-2 border-purple-500'
                      : 'bg-gray-800/50 border-2 border-gray-700/50 hover:border-gray-600'
                  }`}
                >
                  <div className="text-2xl mb-2">{m.icon}</div>
                  <div className="font-semibold text-sm">{m.label}</div>
                  <div className="text-xs text-gray-400 mt-1">{m.desc}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Personality */}
        {step === 4 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Communication Style</h2>
            {[
              { key: 'formality', label: 'Formality', low: 'Casual', high: 'Formal' },
              { key: 'verbosity', label: 'Verbosity', low: 'Brief', high: 'Detailed' },
              { key: 'humor', label: 'Humor', low: 'Serious', high: 'Witty' },
            ].map(slider => (
              <div key={slider.key} className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">{slider.label}</span>
                  <span className="text-purple-300">{config.personality[slider.key]}/10</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={config.personality[slider.key]}
                  onChange={e => setConfig(prev => ({
                    ...prev,
                    personality: { ...prev.personality, [slider.key]: parseInt(e.target.value) },
                  }))}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{slider.low}</span>
                  <span>{slider.high}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Step 5: Access */}
        {step === 5 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Access Control</h2>
            <label className="flex items-center gap-3 p-4 bg-gray-800/50 rounded-xl cursor-pointer">
              <input
                type="checkbox"
                checked={config.admin_only}
                onChange={e => setConfig(prev => ({ ...prev, admin_only: e.target.checked }))}
                className="w-5 h-5 rounded accent-purple-500"
              />
              <div>
                <div className="font-medium text-sm">Admin Only</div>
                <div className="text-xs text-gray-400">Only administrators can interact with The Colonel</div>
              </div>
            </label>
            <p className="text-xs text-gray-500 mt-3">
              Recommended: Keep admin-only enabled. The Colonel can execute server commands
              and access sensitive information.
            </p>
          </div>
        )}

        {/* Step 6: Model */}
        {step === 6 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Choose LLM</h2>
            <p className="text-sm text-gray-400 mb-4">Select the AI model that powers The Colonel.</p>
            <div className="space-y-2">
              {MODELS.map(m => (
                <button
                  key={m.id}
                  onClick={() => setConfig(prev => ({ ...prev, model: m.id }))}
                  className={`w-full text-left p-3 rounded-lg transition-all ${
                    config.model === m.id
                      ? 'bg-purple-900/40 border border-purple-500'
                      : 'bg-gray-800/50 border border-gray-700/30 hover:bg-gray-800'
                  }`}
                >
                  <div className="font-medium text-sm">{m.label}</div>
                  <div className="text-xs text-gray-400">{m.desc}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 7: Deploy */}
        {step === 7 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Review & Deploy</h2>
            <div className="space-y-3 text-sm">
              <div className="bg-gray-800/50 rounded-lg p-3 grid grid-cols-2 gap-y-2 gap-x-4">
                <div className="text-gray-400">Name</div><div>{config.name}</div>
                <div className="text-gray-400">Server</div><div>{config.server_name}</div>
                <div className="text-gray-400">Mission</div><div className="capitalize">{config.mission}</div>
                <div className="text-gray-400">Model</div><div>{MODELS.find(m => m.id === config.model)?.label || config.model}</div>
                <div className="text-gray-400">Access</div><div>{config.admin_only ? 'Admin Only' : 'All Users'}</div>
                <div className="text-gray-400">Skills</div><div>{config.enabled_skills.length} enabled</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-2">Personality</div>
                <div className="flex gap-4 text-xs">
                  <span>Formality: {config.personality.formality}/10</span>
                  <span>Verbosity: {config.personality.verbosity}/10</span>
                  <span>Humor: {config.personality.humor}/10</span>
                </div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <div className="text-gray-400 text-xs mb-2">Enabled Skills</div>
                <div className="flex flex-wrap gap-1">
                  {config.enabled_skills.map(s => (
                    <span key={s} className="px-2 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs">{s}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-800">
          <button
            onClick={step === 0 ? () => navigate('/admin/ai/colonel') : back}
            className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            {step === 0 ? 'Skip Setup' : 'Back'}
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={next}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleDeploy}
              disabled={loading}
              className="px-6 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Deploying...
                </>
              ) : (
                'Deploy The Colonel'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
