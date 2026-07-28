import React, { useState, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { XMarkIcon, BookOpenIcon, AcademicCapIcon, QuestionMarkCircleIcon, ChatBubbleLeftRightIcon, MagnifyingGlassIcon, SparklesIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { helpContent, helpKeyForPath, guideFaqs } from '../data/helpContent';
import GuideActionCard from './GuideActionCard';

// Route-aware, comprehensive Help panel. Help content + FAQs live in
// src/data/helpContent.js (also seeds the Colonel "Guide" persona). The panel
// auto-selects the right help for the current route; an explicit `currentPage`
// prop (legacy callers) overrides the route lookup when provided.
export default function HelpPanel({ isOpen, onClose, currentPage }) {
  const [activeTab, setActiveTab] = useState('guide');
  const [faqQuery, setFaqQuery] = useState('');
  const [guideMsgs, setGuideMsgs] = useState([]);
  const [guideInput, setGuideInput] = useState('');
  const [guideLoading, setGuideLoading] = useState(false);

  // Derive the active help key from the current route, unless a caller passed
  // an explicit currentPage. useLocation is safe here (panel renders inside the
  // admin Router); fall back gracefully if location is unavailable.
  let pathname = '';
  try { pathname = useLocation()?.pathname || ''; } catch (_) { pathname = ''; }
  const helpKey = (currentPage && helpContent[currentPage]) ? currentPage : helpKeyForPath(pathname);
  const pageHelp = helpContent[helpKey] || helpContent.dashboard;

  const filteredFaqs = useMemo(() => {
    const q = faqQuery.trim().toLowerCase();
    if (!q) return guideFaqs;
    return guideFaqs.filter(
      (f) => f.q.toLowerCase().includes(q) || f.a.toLowerCase().includes(q) || (f.area || '').includes(q)
    );
  }, [faqQuery]);

  const sendGuide = async () => {
    const q = guideInput.trim();
    if (!q || guideLoading) return;
    const history = guideMsgs.map((m) => ({ role: m.role, content: m.content }));
    setGuideMsgs((prev) => [...prev, { role: 'user', content: q }]);
    setGuideInput('');
    setGuideLoading(true);
    try {
      const pageHelpText = `${pageHelp.title}: ` + pageHelp.sections.map((s) => `${s.title} — ${s.content}`).join(' ');
      const res = await fetch('/api/v1/help/guide/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question: q, page: pathname, page_help: pageHelpText, history }),
      });
      const data = await res.json();
      setGuideMsgs((prev) => [...prev, { role: 'assistant', content: data.answer || 'Sorry, I could not get an answer right now — try the FAQ tab.', pendingAction: data.pending_action || null }]);
    } catch (e) {
      setGuideMsgs((prev) => [...prev, { role: 'assistant', content: "I'm having trouble reaching my knowledge service — try the FAQ tab in the meantime." }]);
    } finally {
      setGuideLoading(false);
    }
  };

  if (!isOpen) return null;

  const tabBtn = (id, Icon, label) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-sm ${
        activeTab === id
          ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );

  return (
    <div className="fixed inset-y-0 right-0 w-96 max-w-full bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b dark:border-gray-700">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Help &amp; Documentation</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            aria-label="Close help"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1.5 mt-4">
          {tabBtn('guide', SparklesIcon, 'Ask the Guide')}
          {tabBtn('help', QuestionMarkCircleIcon, 'Help')}
          {tabBtn('faq', ChatBubbleLeftRightIcon, 'FAQ')}
          {tabBtn('tutorial', AcademicCapIcon, 'Tutorial')}
          {tabBtn('docs', BookOpenIcon, 'Docs')}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'guide' && (
          <div className="flex flex-col h-full">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                <SparklesIcon className="h-5 w-5 text-white" />
              </span>
              <div>
                <p className="font-medium text-gray-900 dark:text-white leading-tight">The Guide</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 leading-tight">Friendly help — explains things, never changes anything</p>
              </div>
            </div>

            <div className="flex-1 space-y-3 mb-3">
              {guideMsgs.length === 0 && (
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-3">
                  <p>Hi! I’m the Guide. Ask me how anything works in Unicorn Commander — billing &amp; credits, federation, models, access, and more. I’ll point you to the right page; I can’t change settings for you.</p>
                  <div className="flex flex-wrap gap-1.5">
                    {['How do credits work?', 'What is a trust mode?', 'How do I upgrade my plan?', 'Metered vs included models?'].map((s) => (
                      <button
                        key={s}
                        onClick={() => { setGuideInput(s); }}
                        className="text-xs px-2 py-1 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {guideMsgs.map((m, i) => (
                <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[85%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                  }`}>
                    {m.content}
                  </div>
                  {m.pendingAction && (
                    <div className="mt-1.5 w-[85%]"><GuideActionCard action={m.pendingAction} /></div>
                  )}
                </div>
              ))}
              {guideLoading && (
                <div className="flex justify-start">
                  <div className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">The Guide is thinking…</div>
                </div>
              )}
            </div>

            <div className="sticky bottom-0 bg-white dark:bg-gray-800 pt-2">
              <div className="flex items-end gap-2">
                <textarea
                  rows={1}
                  value={guideInput}
                  onChange={(e) => setGuideInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendGuide(); } }}
                  placeholder="Ask the Guide…"
                  className="flex-1 resize-none px-3 py-2 text-sm rounded border bg-gray-50 dark:bg-gray-700 dark:border-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400"
                />
                <button
                  onClick={sendGuide}
                  disabled={guideLoading || !guideInput.trim()}
                  className="flex-shrink-0 p-2 rounded bg-blue-600 text-white disabled:opacity-40 hover:bg-blue-700"
                  aria-label="Send"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
              </div>
              <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">The Guide can’t run commands or change settings — it only helps you find your way.</p>
            </div>
          </div>
        )}

        {activeTab === 'help' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">{pageHelp.title}</h3>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Help for this page</p>
            </div>
            {pageHelp.sections.map((section, index) => (
              <div key={index}>
                <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-1">{section.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">{section.content}</p>
              </div>
            ))}
            <div className="pt-2 border-t dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Looking for something else? Try the <button onClick={() => setActiveTab('faq')} className="text-blue-600 dark:text-blue-400 underline">FAQ</button> tab — it covers billing, federation, AI, access, and more.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'faq' && (
          <div className="space-y-4">
            <div className="relative">
              <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={faqQuery}
                onChange={(e) => setFaqQuery(e.target.value)}
                placeholder="Search FAQs (e.g. credits, trust mode, SSO)..."
                className="w-full pl-9 pr-3 py-2 text-sm rounded border bg-gray-50 dark:bg-gray-700 dark:border-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400"
              />
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500">{filteredFaqs.length} answer{filteredFaqs.length === 1 ? '' : 's'}</p>
            <div className="space-y-4">
              {filteredFaqs.map((f, i) => (
                <div key={i}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400">{f.area}</span>
                    <h4 className="font-medium text-gray-800 dark:text-gray-200 text-sm">{f.q}</h4>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{f.a}</p>
                </div>
              ))}
              {filteredFaqs.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">No FAQ matches “{faqQuery}”. Try a different term.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'tutorial' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Quick Start</h3>
            <ol className="space-y-3 text-sm">
              {[
                ['Check system health', 'On the Dashboard, confirm core services, GPUs, and resources are healthy.'],
                ['Set up models & pricing', 'In AI & Models, review the model catalog; in Billing → Rates, set markup and credit value.'],
                ['Configure access', 'In People & Access, manage users/orgs and grant apps by tier or per-org.'],
                ['Use the metered gateway', 'Run local ($0) and cloud (cost + margin) models through the OpenAI-compatible gateway — usage is metered per request.'],
              ].map(([t, d], i) => (
                <li key={i} className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">{i + 1}</span>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-200">{t}</p>
                    <p className="text-gray-600 dark:text-gray-400">{d}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Documentation Links</h3>
            <div className="space-y-2">
              {[
                ['https://unicorncommander.ai', '🦄 Unicorn Commander', 'Suite home & documentation'],
                ['https://git.unicorncommander.ai/UnicornCommander', '🐙 Source Repositories', 'Ops-Center & suite source code'],
                ['/admin/billing/rates', '💳 Rates & Margin', 'Inference rate book & cost-plus pricing'],
                ['/admin/infra/federation/contracts', '🔗 Federation Contracts', 'Per-peer trust modes & ACLs'],
              ].map(([href, title, sub], i) => (
                <a
                  key={i}
                  href={href}
                  target={href.startsWith('http') ? '_blank' : undefined}
                  rel="noopener noreferrer"
                  className="block p-3 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  <p className="font-medium text-gray-800 dark:text-gray-200">{title}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{sub}</p>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t dark:border-gray-700 text-center text-sm text-gray-500 dark:text-gray-400">
        Press <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">?</kbd> for keyboard shortcuts
      </div>
    </div>
  );
}
