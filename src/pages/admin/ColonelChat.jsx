import React, { useState, useEffect, useRef, useCallback, lazy, Suspense } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Highlight, themes } from 'prism-react-renderer';
import useColonelWebSocket from '../../hooks/useColonelWebSocket';
import ColonelSidebar from '../../components/colonel/ColonelSidebar';
import GeneralModal from '../../components/colonel/GeneralModal';

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

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* ignore */ }
  };
  return (
    <button
      onClick={handleCopy}
      className="text-gray-500 hover:text-gray-300 transition-colors text-[10px] flex items-center gap-1"
      title="Copy to clipboard"
    >
      {copied ? (
        <><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Copied</>
      ) : (
        <><svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</>
      )}
    </button>
  );
}

function renderInlineMarkdown(text) {
  if (!text) return text;
  // Process: **bold**, *italic*, `code`, [links](url)
  const tokens = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
  return tokens.map((token, i) => {
    if (token.startsWith('**') && token.endsWith('**')) {
      return <strong key={i}>{token.slice(2, -2)}</strong>;
    }
    if (token.startsWith('*') && token.endsWith('*') && !token.startsWith('**')) {
      return <em key={i}>{token.slice(1, -1)}</em>;
    }
    if (token.startsWith('`') && token.endsWith('`')) {
      return (
        <code key={i} className="bg-gray-800 px-1 py-0.5 rounded text-purple-300 text-xs">
          {token.slice(1, -1)}
        </code>
      );
    }
    const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a key={i} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline">
          {linkMatch[1]}
        </a>
      );
    }
    return token;
  });
}

function renderContent(content) {
  if (!content) return null;

  // Split by fenced code blocks
  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, i) => {
    // Fenced code block
    if (part.startsWith('```') && part.endsWith('```')) {
      const inner = part.slice(3, -3);
      const firstNewline = inner.indexOf('\n');
      const lang = firstNewline > 0 ? inner.slice(0, firstNewline).trim() : '';
      const code = firstNewline > 0 ? inner.slice(firstNewline + 1) : inner;
      // Map common language aliases for Prism
      const langMap = { sh: 'bash', shell: 'bash', yml: 'yaml', dockerfile: 'docker', js: 'javascript', ts: 'typescript', py: 'python', rb: 'ruby', rs: 'rust', tf: 'hcl' };
      const prismLang = langMap[lang] || lang || 'bash';
      return (
        <div key={i} className="relative group my-2">
          <div className="flex items-center justify-between bg-gray-800 rounded-t-lg px-3 py-1.5 border border-gray-700 border-b-0">
            <span className="text-gray-500 text-[10px] font-mono">{lang || 'text'}</span>
            <CopyButton text={code} />
          </div>
          <Highlight theme={themes.nightOwl} code={code} language={prismLang}>
            {({ style, tokens, getLineProps, getTokenProps }) => (
              <pre className="rounded-b-lg p-3 overflow-x-auto text-xs font-mono border border-gray-700 border-t-0" style={{ ...style, margin: 0, background: '#0a0a1a' }}>
                {tokens.map((line, li) => (
                  <div key={li} {...getLineProps({ line })}>
                    {line.map((token, ti) => (
                      <span key={ti} {...getTokenProps({ token })} />
                    ))}
                  </div>
                ))}
              </pre>
            )}
          </Highlight>
        </div>
      );
    }

    // Process non-code text line by line for block-level markdown
    const lines = part.split('\n');
    const elements = [];
    let listItems = [];
    let listType = null; // 'ul' or 'ol'

    const flushList = () => {
      if (listItems.length > 0) {
        const Tag = listType === 'ol' ? 'ol' : 'ul';
        const cls = listType === 'ol'
          ? 'list-decimal list-inside space-y-0.5 my-1 text-gray-300'
          : 'list-disc list-inside space-y-0.5 my-1 text-gray-300';
        elements.push(<Tag key={`list-${elements.length}`} className={cls}>{listItems}</Tag>);
        listItems = [];
        listType = null;
      }
    };

    lines.forEach((line, li) => {
      const trimmed = line.trimStart();

      // Headers
      if (trimmed.startsWith('### ')) {
        flushList();
        elements.push(<h4 key={`${i}-${li}`} className="text-sm font-semibold text-gray-100 mt-3 mb-1">{renderInlineMarkdown(trimmed.slice(4))}</h4>);
        return;
      }
      if (trimmed.startsWith('## ')) {
        flushList();
        elements.push(<h3 key={`${i}-${li}`} className="text-base font-semibold text-gray-100 mt-3 mb-1">{renderInlineMarkdown(trimmed.slice(3))}</h3>);
        return;
      }
      if (trimmed.startsWith('# ')) {
        flushList();
        elements.push(<h2 key={`${i}-${li}`} className="text-lg font-bold text-gray-100 mt-3 mb-1">{renderInlineMarkdown(trimmed.slice(2))}</h2>);
        return;
      }

      // Horizontal rule
      if (/^---+$/.test(trimmed) || /^\*\*\*+$/.test(trimmed)) {
        flushList();
        elements.push(<hr key={`${i}-${li}`} className="border-gray-700 my-2" />);
        return;
      }

      // Unordered list items
      if (/^[-*+]\s/.test(trimmed)) {
        if (listType !== 'ul') flushList();
        listType = 'ul';
        listItems.push(<li key={`${i}-${li}`}>{renderInlineMarkdown(trimmed.replace(/^[-*+]\s/, ''))}</li>);
        return;
      }

      // Ordered list items
      const olMatch = trimmed.match(/^(\d+)\.\s(.*)$/);
      if (olMatch) {
        if (listType !== 'ol') flushList();
        listType = 'ol';
        listItems.push(<li key={`${i}-${li}`}>{renderInlineMarkdown(olMatch[2])}</li>);
        return;
      }

      // Regular text (or blank line)
      flushList();
      if (trimmed === '') {
        if (li > 0 && li < lines.length - 1) {
          elements.push(<div key={`${i}-${li}`} className="h-2" />);
        }
      } else {
        elements.push(<span key={`${i}-${li}`}>{renderInlineMarkdown(line)}{li < lines.length - 1 ? '\n' : ''}</span>);
      }
    });

    flushList();
    return <span key={i}>{elements}</span>;
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

// Map skill names to suggested prompts and icons
const SKILL_SUGGESTIONS = {
  'docker-management':   { text: 'What containers are running?', icon: '🐳' },
  'system-status':       { text: 'Show me full system status', icon: '📊' },
  'service-health':      { text: 'Check the health of all services', icon: '🏥' },
  'log-viewer':          { text: 'Show recent error logs', icon: '📋' },
  'gpu-monitoring':      { text: 'Show GPU memory and utilization', icon: '🎮' },
  'postgresql-ops':      { text: 'List PostgreSQL databases', icon: '🐘' },
  'bash-execution':      { text: 'What disk space is available?', icon: '💾' },
  'network-diagnostics': { text: 'Check network connectivity', icon: '🌐' },
  'traefik-management':  { text: 'List all Traefik routes', icon: '🔀' },
  'backup-management':   { text: 'Show backup status', icon: '💿' },
  'resource-cleanup':    { text: 'Check for cleanup opportunities', icon: '🧹' },
  'keycloak-auth':       { text: 'Show Keycloak user count', icon: '🔑' },
  'litellm-management':  { text: 'Check LLM proxy health', icon: '🤖' },
  'forgejo-management':  { text: 'Show Git repositories', icon: '📦' },
  'frontend-management': { text: 'What can you change in the UI?', icon: '🎨' },
};

const FALLBACK_SUGGESTIONS = [
  { text: 'What containers are running?', icon: '🐳' },
  { text: 'Show me system status', icon: '📊' },
  { text: 'Check the health of all services', icon: '🏥' },
  { text: 'Show recent error logs', icon: '📋' },
  { text: 'Show GPU memory and utilization', icon: '🎮' },
  { text: 'What disk space is available?', icon: '💾' },
];

function EmptyState({ colonelName, onSuggestion, skills }) {
  // Build suggestions from loaded skills, fall back to defaults
  const suggestions = React.useMemo(() => {
    if (!skills || skills.length === 0) return FALLBACK_SUGGESTIONS;
    const matched = skills
      .filter(s => s.enabled && SKILL_SUGGESTIONS[s.name])
      .map(s => SKILL_SUGGESTIONS[s.name]);
    return matched.length >= 4 ? matched.slice(0, 6) : FALLBACK_SUGGESTIONS;
  }, [skills]);

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
            onClick={() => onSuggestion?.(s.text)}
            className="text-left px-4 py-3 bg-gray-800/50 hover:bg-purple-900/30 border border-gray-700/50 hover:border-purple-700/30 rounded-xl text-sm text-gray-300 transition-all group"
          >
            <span className="mr-2 group-hover:scale-110 inline-block transition-transform">{s.icon}</span>
            {s.text}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Model Selector ─────────────────────────────────────────────────────

const COLONEL_MODELS = [
  { id: 'anthropic/claude-opus-4-6', name: 'Claude Opus 4.6', provider: 'Anthropic', badge: 'Latest' },
  { id: 'anthropic/claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5', provider: 'Anthropic', badge: 'Recommended' },
  { id: 'anthropic/claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', provider: 'Anthropic', badge: 'Fast' },
  { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
  { id: 'google/gemini-2.0-flash-exp:free', name: 'Gemini 2.0 Flash (Free)', provider: 'Google', badge: 'Free' },
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
                  m.badge === 'Recommended' ? 'bg-emerald-800/60 text-emerald-300' :
                  m.badge === 'Fast' ? 'bg-blue-800/60 text-blue-300' :
                  m.badge === 'Budget' ? 'bg-green-800/60 text-green-300' :
                  m.badge === 'Free' ? 'bg-gray-800 text-gray-300' :
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
  const [generalOpen, setGeneralOpen] = useState(false);
  const [loadedSkills, setLoadedSkills] = useState([]);

  // Load skills for dynamic suggestions
  useEffect(() => {
    fetch('/api/v1/colonel/skills', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.skills) setLoadedSkills(data.skills); })
      .catch(() => {});
  }, []);

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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (sidebarOpen) setSidebarOpen(false);
        if (generalOpen) setGeneralOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen, generalOpen]);

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
          {!isPopout && (
            <button
              onClick={() => setGeneralOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700/50 rounded-lg text-xs text-gray-300 transition-colors"
              title="The General — Multi-Colonel overview"
            >
              <span className="text-sm">🎖️</span> General
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
          <EmptyState colonelName={colonelName} skills={loadedSkills} onSuggestion={(text) => { if (connected) sendMessage(text); }} />
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

      {/* The General Modal */}
      <GeneralModal open={generalOpen} onClose={() => setGeneralOpen(false)} />
    </div>
  );
}
