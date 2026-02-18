import React, { useState, useEffect, useRef, useCallback } from 'react';
import useColonelWebSocket from '../../hooks/useColonelWebSocket';

// ─── Inline Icons ───────────────────────────────────────────────────────

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const PopOutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
    <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

// ─── Minimal Message Rendering ──────────────────────────────────────────

function MiniMessage({ message }) {
  const isUser = message.role === 'user';
  const isSkillResult = message.role === 'skill_result';

  if (isSkillResult) {
    return (
      <div className="my-1 px-2">
        <div className={`rounded text-xs font-mono p-2 ${
          message.success ? 'bg-gray-900/60 text-green-400 border border-green-900/30' : 'bg-gray-900/60 text-red-400 border border-red-900/30'
        }`}>
          <span className="opacity-60">{message.success ? '✓' : '✗'} {message.skill_name}</span>
          <pre className="whitespace-pre-wrap break-words mt-1 max-h-20 overflow-auto text-[11px]">{message.content}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} my-1 px-2`}>
      {!isUser && (
        <img src="/logos/The_Colonel.webp" alt="" className="w-5 h-5 rounded-full mr-1.5 mt-0.5 flex-shrink-0" />
      )}
      <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
        isUser
          ? 'bg-purple-600/80 text-white'
          : 'bg-gray-800/80 border border-purple-800/20 text-gray-200'
      }`}>
        <span className="whitespace-pre-wrap break-words">{message.content}</span>
        {message._streaming && (
          <span className="inline-block w-1.5 h-3 bg-purple-400 animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  );
}

// ─── Main Chat Bubble Component ─────────────────────────────────────────

export default function ColonelChatBubble() {
  const [open, setOpen] = useState(() => {
    try { return localStorage.getItem('colonelBubbleOpen') === 'true'; } catch { return false; }
  });
  const [text, setText] = useState('');
  const [unread, setUnread] = useState(0);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const prevMsgCount = useRef(0);

  const {
    connected, connecting, colonelName,
    messages, isStreaming,
    activeSkill, pendingConfirm,
    sendMessage, confirmAction, startNewSession,
  } = useColonelWebSocket();

  // Persist open state
  useEffect(() => {
    try { localStorage.setItem('colonelBubbleOpen', String(open)); } catch {}
  }, [open]);

  // Track unread messages when panel is closed
  useEffect(() => {
    if (!open && messages.length > prevMsgCount.current) {
      const newMsgs = messages.slice(prevMsgCount.current);
      const assistantMsgs = newMsgs.filter(m => m.role === 'assistant');
      if (assistantMsgs.length > 0) {
        setUnread(prev => prev + assistantMsgs.length);
      }
    }
    prevMsgCount.current = messages.length;
  }, [messages, open]);

  // Clear unread when opening
  useEffect(() => {
    if (open) setUnread(0);
  }, [open]);

  // Auto-scroll
  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open, activeSkill]);

  // Focus textarea when opening
  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [open]);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || !connected || isStreaming) return;
    sendMessage(trimmed);
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [text, connected, isStreaming, sendMessage]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePopOut = () => {
    window.open(
      '/admin/ai/colonel-popout',
      'colonel-chat',
      'width=620,height=820,resizable=yes,scrollbars=yes'
    );
    setOpen(false);
  };

  return (
    <>
      {/* ── Chat Panel ─────────────────────────────────────────────── */}
      {open && (
        <div
          className="fixed bottom-20 right-6 z-[41] w-[380px] h-[500px] flex flex-col rounded-2xl shadow-2xl border border-purple-700/30 bg-gray-950 overflow-hidden"
          style={{ maxHeight: 'calc(100vh - 120px)' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2.5 bg-gradient-to-r from-purple-900/80 to-gray-900 border-b border-purple-800/30">
            <div className="flex items-center gap-2">
              <img src="/logos/The_Colonel.webp" alt="" className="w-6 h-6 rounded-full" />
              <div>
                <div className="text-sm font-semibold text-gray-100">{colonelName}</div>
                <div className="flex items-center gap-1 text-[10px] text-gray-400">
                  <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400' : connecting ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'}`} />
                  {connected ? 'Online' : connecting ? 'Connecting...' : 'Offline'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handlePopOut}
                className="p-1.5 hover:bg-gray-700/50 rounded-lg text-gray-400 hover:text-gray-200 transition-colors"
                title="Pop out to window"
              >
                <PopOutIcon />
              </button>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 hover:bg-gray-700/50 rounded-lg text-gray-400 hover:text-gray-200 transition-colors"
                title="Close"
              >
                <CloseIcon />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto py-2">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-6">
                <img src="/logos/The_Colonel.webp" alt="" className="w-12 h-12 rounded-full mb-3 opacity-80" />
                <p className="text-xs text-gray-400 mb-3">Ask The Colonel about your server</p>
                <div className="space-y-1.5 w-full">
                  {['What containers are running?', 'Show me system status'].map((s, i) => (
                    <button
                      key={i}
                      onClick={() => { if (connected) sendMessage(s); }}
                      className="w-full text-left px-3 py-2 bg-gray-800/40 hover:bg-purple-900/20 border border-gray-700/30 hover:border-purple-700/30 rounded-lg text-xs text-gray-300 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <MiniMessage key={msg.id || i} message={msg} />
                ))}
                {activeSkill && (
                  <div className="mx-2 my-1 px-2 py-1.5 bg-gray-800/50 border border-purple-800/20 rounded text-[11px] text-purple-300">
                    <div className="flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
                      {activeSkill.name} → {activeSkill.action}
                    </div>
                  </div>
                )}
                {pendingConfirm && (
                  <div className="mx-2 my-1 p-2 bg-yellow-900/20 border border-yellow-700/40 rounded text-xs">
                    <p className="text-yellow-300 mb-1.5">{pendingConfirm.description}</p>
                    <div className="flex gap-1.5">
                      <button onClick={() => confirmAction(pendingConfirm.confirm_id, true)} className="px-2.5 py-1 bg-yellow-600 hover:bg-yellow-500 text-white rounded text-[11px]">Confirm</button>
                      <button onClick={() => confirmAction(pendingConfirm.confirm_id, false)} className="px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-[11px]">Cancel</button>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-700/40 bg-gray-900/60 p-2">
            <div className="flex items-end gap-1.5">
              <textarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                onInput={() => {
                  const ta = textareaRef.current;
                  if (ta) { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 100) + 'px'; }
                }}
                placeholder="Ask The Colonel..."
                disabled={!connected || isStreaming}
                rows={1}
                className="flex-1 bg-gray-800/60 border border-gray-700/40 rounded-lg px-3 py-2 text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-1 focus:ring-purple-500/40 text-xs"
              />
              <button
                onClick={handleSend}
                disabled={!connected || isStreaming || !text.trim()}
                className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors text-white flex-shrink-0"
              >
                <SendIcon />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Floating Bubble Button ────────────────────────────────── */}
      <button
        onClick={() => setOpen(!open)}
        className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg transition-all duration-200 flex items-center justify-center group ${
          open
            ? 'bg-gray-800 border border-gray-600 hover:bg-gray-700'
            : 'bg-gradient-to-br from-purple-600 to-purple-800 border border-purple-500/30 hover:from-purple-500 hover:to-purple-700 hover:scale-105'
        }`}
        title={open ? 'Close Colonel chat' : 'Chat with The Colonel'}
      >
        {open ? (
          <CloseIcon />
        ) : (
          <>
            <img src="/logos/The_Colonel.webp" alt="The Colonel" className="w-9 h-9 rounded-full object-cover" />
            {/* Pulse ring when not open */}
            <span className="absolute inset-0 rounded-full border-2 border-purple-400/40 animate-ping opacity-30 pointer-events-none" />
          </>
        )}

        {/* Unread badge */}
        {!open && unread > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center border-2 border-gray-950">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
    </>
  );
}
