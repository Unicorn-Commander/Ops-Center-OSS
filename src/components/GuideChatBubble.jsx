import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { SparklesIcon, PaperAirplaneIcon, XMarkIcon } from '@heroicons/react/24/outline';
import GuideActionCard from './GuideActionCard';

// The Guide — the END-USER floating assistant (counterpart to the admin-only
// Colonel bubble). Read-only help agent: it explains the platform and points to
// the right page, and CANNOT run commands or change settings. Talks to
// POST /api/v1/help/guide/ask (internal/local model — free + safe).
export default function GuideChatBubble() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  let pathname = '';
  try { pathname = useLocation()?.pathname || ''; } catch (_) { pathname = ''; }

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs, loading, open]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    const history = msgs.map((m) => ({ role: m.role, content: m.content }));
    setMsgs((p) => [...p, { role: 'user', content: q }]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/v1/help/guide/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question: q, page: pathname, history }),
      });
      const data = await res.json();
      setMsgs((p) => [...p, { role: 'assistant', content: data.answer || 'Sorry, I could not get an answer right now.', pendingAction: data.pending_action || null }]);
    } catch (e) {
      setMsgs((p) => [...p, { role: 'assistant', content: "I'm having trouble reaching my knowledge service right now. Please try again in a moment." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Ask the Guide"
        aria-label="Ask the Guide"
        className="fixed bottom-5 right-5 z-40 flex items-center justify-center w-14 h-14 rounded-full shadow-lg text-white bg-gradient-to-br from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-colors"
      >
        <SparklesIcon className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 w-[360px] max-w-[calc(100vw-2rem)] h-[480px] max-h-[calc(100vh-2rem)] flex flex-col rounded-xl shadow-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20">
            <SparklesIcon className="h-5 w-5" />
          </span>
          <div className="leading-tight">
            <p className="font-medium text-sm">The Guide</p>
            <p className="text-[11px] text-white/80">Friendly help — never changes anything</p>
          </div>
        </div>
        <button onClick={() => setOpen(false)} aria-label="Close" className="text-white/80 hover:text-white">
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {msgs.length === 0 && (
          <div className="text-sm text-gray-600 dark:text-gray-300 space-y-3">
            <p>Hi! I’m the Guide. Ask me how anything works here — credits, billing, models, federation — and I can also look up your own account (balance, usage, plan, invoices). I’ll point you the right way; I can’t change settings for you.</p>
            <div className="flex flex-wrap gap-1.5">
              {["What's my balance?", 'Create an API key', 'Show my recent invoices', 'How do credits work?'].map((s) => (
                <button key={s} onClick={() => send(s)} className="text-xs px-2 py-1 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[85%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
              m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
            }`}>{m.content}</div>
            {m.pendingAction && (
              <div className="mt-1.5 w-[85%]"><GuideActionCard action={m.pendingAction} /></div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">The Guide is thinking…</div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-2">
        <div className="flex items-end gap-2">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Ask the Guide…"
            className="flex-1 resize-none px-3 py-2 text-sm rounded border bg-gray-50 dark:bg-gray-700 dark:border-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400"
          />
          <button onClick={() => send()} disabled={loading || !input.trim()} aria-label="Send"
            className="flex-shrink-0 p-2 rounded bg-blue-600 text-white disabled:opacity-40 hover:bg-blue-700">
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
