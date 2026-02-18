import React, { useState, useEffect, useRef, useCallback, lazy, Suspense } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import useColonelWebSocket from '../../hooks/useColonelWebSocket';
import ColonelSidebar from '../../components/colonel/ColonelSidebar';

// ─── Icons (inline SVG to avoid extra deps) ────────────────────────────

const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const PlusIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const StarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
);
const ColonelAvatar = ({ size = 'md' }) => {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12', xl: 'w-16 h-16' };
  return <img src="/logos/The_Colonel.webp" alt="The Colonel" className={`${sizes[size] || sizes.md} rounded-full object-cover`} />;
};

// ─── Message Bubble ─────────────────────────────────────────────────────

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isSkillResult = message.role === 'skill_result';

  if (isSkillResult) {
    return (
      <div className="mx-4 my-2">
        <div className={`rounded-lg border p-3 text-sm font-mono ${
          message.success
            ? 'bg-gray-900/50 border-green-800/50 text-green-300'
            : 'bg-gray-900/50 border-red-800/50 text-red-300'
        }`}>
          <div className="flex items-center gap-2 mb-1 text-xs opacity-70">
            <span>{message.success ? '✓' : '✗'}</span>
            <span>{message.skill_name} → {message.action}</span>
            {message.duration_ms && <span>({message.duration_ms}ms)</span>}
          </div>
          <pre className="whitespace-pre-wrap break-words text-xs leading-relaxed max-h-64 overflow-auto">
            {message.content}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mx-4 my-2`}>
      {!isUser && (
        <div className="flex-shrink-0 mr-2 mt-1">
          <ColonelAvatar size="sm" />
        </div>
      )}
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser
          ? 'bg-purple-600/80 text-white'
          : 'bg-gradient-to-r from-purple-900/40 to-purple-800/20 border border-purple-700/30 text-gray-100'
      }`}>
        {/* Simple markdown-like rendering */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {renderContent(message.content)}
        </div>
        {message._streaming && (
          <span className="inline-block w-2 h-4 bg-purple-400 animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
}

function renderContent(content) {
  if (!content) return null;

  // Split by code blocks
  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, i) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const lines = part.slice(3, -3);
      const firstNewline = lines.indexOf('\n');
      const lang = firstNewline > 0 ? lines.slice(0, firstNewline).trim() : '';
      const code = firstNewline > 0 ? lines.slice(firstNewline + 1) : lines;
      return (
        <pre key={i} className="bg-gray-950 rounded-lg p-3 my-2 overflow-x-auto text-xs font-mono text-green-300 border border-gray-800">
          {lang && <div className="text-gray-500 text-[10px] mb-1">{lang}</div>}
          <code>{code}</code>
        </pre>
      );
    }

    // Bold: **text**
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return (
      <span key={i}>
        {boldParts.map((bp, j) => {
          if (bp.startsWith('**') && bp.endsWith('**')) {
            return <strong key={j}>{bp.slice(2, -2)}</strong>;
          }
          // Inline code: `text`
          const codeParts = bp.split(/(`[^`]+`)/g);
          return codeParts.map((cp, k) => {
            if (cp.startsWith('`') && cp.endsWith('`')) {
              return (
                <code key={`${j}-${k}`} className="bg-gray-800 px-1 py-0.5 rounded text-purple-300 text-xs">
                  {cp.slice(1, -1)}
                </code>
              );
            }
            return cp;
          });
        })}
      </span>
    );
  });
}

// ─── Chat Input ─────────────────────────────────────────────────────────

function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    }
  };

  return (
    <div className="border-t border-gray-700/50 bg-gray-900/50 p-4">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask The Colonel anything about your server..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-gray-800/80 border border-gray-700/50 rounded-xl px-4 py-3 text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 text-sm"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="flex items-center justify-center w-10 h-10 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors text-white"
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}

// ─── Active Skill Indicator ─────────────────────────────────────────────

function SkillIndicator({ skill }) {
  if (!skill) return null;
  return (
    <div className="mx-4 my-2">
      <div className="bg-gray-800/50 border border-purple-800/30 rounded-lg p-3 text-sm">
        <div className="flex items-center gap-2 text-purple-300">
          <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
          <span>Executing: {skill.name} → {skill.action}</span>
        </div>
        {skill.output && (
          <pre className="mt-2 text-xs text-gray-400 font-mono max-h-32 overflow-auto whitespace-pre-wrap">
            {skill.output}
          </pre>
        )}
      </div>
    </div>
  );
}

// ─── Confirmation Dialog ────────────────────────────────────────────────

function ConfirmationDialog({ confirm, onConfirm, onDeny }) {
  if (!confirm) return null;
  return (
    <div className="mx-4 my-2">
      <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4 text-sm">
        <div className="font-semibold text-yellow-300 mb-2">Confirmation Required</div>
        <p className="text-gray-300 mb-1">{confirm.description}</p>
        <p className="text-xs text-gray-500 mb-3">
          {confirm.skill_name} → {confirm.action}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => onConfirm(confirm.confirm_id, true)}
            className="px-4 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-xs font-medium transition-colors"
          >
            Confirm
          </button>
          <button
            onClick={() => onDeny(confirm.confirm_id, false)}
            className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Empty State ────────────────────────────────────────────────────────

function EmptyState({ colonelName }) {
  const suggestions = [
    'What containers are running?',
    'Show me system status',
    'Check the health of all services',
    'Show recent PostgreSQL logs',
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 py-16">
      <div className="mb-4"><ColonelAvatar size="xl" /></div>
      <h2 className="text-xl font-bold text-gray-100 mb-2">{colonelName}</h2>
      <p className="text-gray-400 mb-8 max-w-md">
        Your AI command agent. Ask me about containers, system health, logs, or anything about this server.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
        {suggestions.map((s, i) => (
          <button
            key={i}
            className="text-left px-4 py-3 bg-gray-800/50 hover:bg-purple-900/30 border border-gray-700/50 hover:border-purple-700/30 rounded-xl text-sm text-gray-300 transition-all"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Model Selector ─────────────────────────────────────────────────────

const COLONEL_MODELS = [
  { id: 'claude-opus-4-6', name: 'Claude Opus 4.6', provider: 'Anthropic', badge: 'Latest' },
  { id: 'claude-opus-4.5', name: 'Claude Opus 4.5', provider: 'Anthropic' },
  { id: 'claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'Anthropic', badge: 'Fast' },
  { id: 'moonshotai/kimi-k2.5', name: 'Kimi K2.5', provider: 'Moonshot', badge: '262K ctx' },
  { id: 'openai/gpt-5.2-codex', name: 'GPT-5.2 Codex', provider: 'OpenAI', badge: '400K ctx' },
  { id: 'openai/gpt-5.1-codex-mini', name: 'GPT-5.1 Codex Mini', provider: 'OpenAI', badge: 'Budget' },
];

function ModelSelector({ currentModel, onModelChange, disabled }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const current = COLONEL_MODELS.find(m => m.id === currentModel) || { name: currentModel || 'Unknown', provider: '?' };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="flex items-center gap-1.5 px-2.5 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors disabled:opacity-50"
        title="Switch model"
      >
        <span className="max-w-[120px] truncate">{current.name}</span>
        <svg className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-64 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 py-1 overflow-hidden">
          {COLONEL_MODELS.map(m => (
            <button
              key={m.id}
              onClick={() => { onModelChange(m.id); setOpen(false); }}
              className={`w-full text-left px-3 py-2 text-sm transition-colors flex items-center justify-between ${
                m.id === currentModel
                  ? 'bg-purple-900/30 text-purple-300'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <div>
                <div className="font-medium">{m.name}</div>
                <div className="text-[10px] text-gray-500">{m.provider}</div>
              </div>
              {m.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                  m.badge === 'Latest' ? 'bg-purple-800/60 text-purple-300' :
                  m.badge === 'Fast' ? 'bg-blue-800/60 text-blue-300' :
                  m.badge === 'Budget' ? 'bg-green-800/60 text-green-300' :
                  'bg-gray-800 text-gray-400'
                }`}>{m.badge}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────

const PopOutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
    <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

export default function ColonelChat({ popout = false }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionIdParam = searchParams.get('session');
  const isPopout = popout || searchParams.get('popout') === 'true';

  const {
    connected, connecting, colonelName, serverName, writeEnabled,
    currentSessionId, messages, isStreaming, error,
    activeSkill, pendingConfirm,
    sendMessage, confirmAction, startNewSession, clearError,
  } = useColonelWebSocket(sessionIdParam);

  const messagesEndRef = useRef(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);

  // Load current model from config
  useEffect(() => {
    fetch('/api/v1/colonel/config', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.model) setCurrentModel(data.model); })
      .catch(() => {});
  }, []);

  const handleModelChange = async (modelId) => {
    setCurrentModel(modelId);
    try {
      await fetch('/api/v1/colonel/config', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId }),
      });
    } catch { /* best-effort */ }
  };

  // Fetch sessions for sidebar
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/colonel/sessions', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions, currentSessionId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeSkill]);

  const handlePopOut = () => {
    window.open(
      '/admin/ai/colonel-popout',
      'colonel-chat',
      'width=620,height=820,resizable=yes,scrollbars=yes'
    );
  };

  // Check if onboarded (skip in popout mode)
  const [onboarded, setOnboarded] = useState(isPopout ? true : null);

  useEffect(() => {
    if (isPopout) return;
    fetch('/api/v1/colonel/onboarded', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && !data.onboarded) {
          navigate('/admin/ai/colonel/setup');
        } else {
          setOnboarded(true);
        }
      })
      .catch(() => setOnboarded(true)); // Fail open
  }, [navigate, isPopout]);

  if (onboarded === null) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${isPopout ? 'h-screen' : 'h-[calc(100vh-64px)]'} bg-gray-950`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/50 bg-gray-900/80">
        <div className="flex items-center gap-3">
          <ColonelAvatar size="md" />
          <div>
            <h1 className="text-base font-semibold text-gray-100">{colonelName}</h1>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400' : connecting ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'}`} />
              {connected ? `Online — ${serverName || 'Server'}` : connecting ? 'Connecting...' : 'Offline'}
              {connected && writeEnabled && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-yellow-800/60 text-yellow-300">Read/Write</span>
              )}
              {connected && !writeEnabled && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-700/60 text-gray-400">Read Only</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ModelSelector
            currentModel={currentModel}
            onModelChange={handleModelChange}
            disabled={isStreaming}
          />
          {!isPopout && (
            <button
              onClick={handlePopOut}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors"
              title="Pop out to window"
            >
              <PopOutIcon /> Pop Out
            </button>
          )}
          {!isPopout && (
            <button
              onClick={() => navigate('/admin/ai/colonel/status')}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors"
              title="Status dashboard"
            >
              Status
            </button>
          )}
          <button
            onClick={startNewSession}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors"
            title="New session"
          >
            <PlusIcon /> New Chat
          </button>
          {!isPopout && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors"
              title="Open sidebar"
            >
              ☰
            </button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-4 mt-2 px-4 py-2 bg-red-900/30 border border-red-800/50 rounded-lg text-sm text-red-300 flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-400 hover:text-red-300 text-xs">Dismiss</button>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 ? (
          <EmptyState colonelName={colonelName} />
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={msg.id || i} message={msg} />
            ))}
            <SkillIndicator skill={activeSkill} />
            <ConfirmationDialog
              confirm={pendingConfirm}
              onConfirm={confirmAction}
              onDeny={confirmAction}
            />
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={!connected || isStreaming}
      />

      {/* Sidebar */}
      <ColonelSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sessions={sessions}
        onSelectSession={(id, prompt) => {
          if (id) {
            navigate(`/admin/ai/colonel?session=${id}`);
          }
          if (prompt) {
            sendMessage(prompt);
          }
          setSidebarOpen(false);
        }}
        onNewSession={() => {
          startNewSession();
          setSidebarOpen(false);
        }}
        currentSessionId={currentSessionId}
        colonelName={colonelName}
        serverName={serverName}
        online={connected}
      />
    </div>
  );
}
