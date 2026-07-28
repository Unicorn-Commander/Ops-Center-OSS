/**
 * LLM API Keys Component - Generate and manage LiteLLM virtual keys (sk-...)
 *
 * Users generate sk-... keys to use with any OpenAI-compatible client
 * (opencode, Cursor, custom apps) against the LLM gateway.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  KeyIcon, PlusIcon, TrashIcon, ClipboardDocumentIcon,
  CheckCircleIcon, ExclamationCircleIcon, ArrowPathIcon,
  BoltIcon, CurrencyDollarIcon, ClockIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function LLMApiKeys() {
  const { theme, currentTheme } = useTheme();
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Form state
  const [keyName, setKeyName] = useState('');
  const [maxBudget, setMaxBudget] = useState('10');
  const [budgetDuration, setBudgetDuration] = useState('30d');
  const [rpmLimit, setRpmLimit] = useState('60');
  const [tpmLimit, setTpmLimit] = useState('100000');
  const [expiration, setExpiration] = useState('90d');

  const isUnicorn = currentTheme === 'unicorn';
  const isLight = currentTheme === 'light';

  const tc = {
    card: isUnicorn ? 'bg-purple-900/50 backdrop-blur-xl border-white/20' : isLight ? 'bg-white border-gray-200' : 'bg-slate-800 border-slate-700',
    text: isUnicorn ? 'text-purple-100' : isLight ? 'text-gray-900' : 'text-slate-100',
    sub: isUnicorn ? 'text-purple-300' : isLight ? 'text-gray-600' : 'text-slate-400',
    input: isUnicorn ? 'bg-purple-900/50 border-white/20 text-purple-100' : isLight ? 'bg-gray-50 border-gray-300 text-gray-900' : 'bg-slate-900 border-slate-600 text-slate-100',
    btn: isUnicorn ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white',
    row: isLight ? 'bg-gray-50 border-gray-200' : 'bg-black/20 border-white/10',
  };

  const showToast = useCallback(function(type, message) {
    setToast({ type: type, message: message });
    setTimeout(function() { setToast(null); }, 4000);
  }, []);

  const loadKeys = useCallback(function() {
    fetch('/api/v1/llm/keys', { credentials: 'include' })
      .then(function(resp) {
        if (resp.ok) return resp.json();
        throw new Error('Failed to load');
      })
      .then(function(data) {
        setKeys(data || []);
        setLoadError(null);
      })
      .catch(function(e) {
        console.error('Failed to load LLM keys:', e);
        setKeys([]);
        setLoadError('Could not load LLM keys. The service may be unavailable.');
      })
      .finally(function() { setLoading(false); });
  }, []);

  useEffect(function() { loadKeys(); }, [loadKeys]);

  var handleGenerate = function() {
    if (!keyName.trim()) { showToast('error', 'Please enter a key name'); return; }
    setGenerating(true);
    fetch('/api/v1/llm/keys', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: keyName.trim(),
        max_budget: parseFloat(maxBudget) || 10,
        budget_duration: budgetDuration,
        rpm_limit: parseInt(rpmLimit) || 60,
        tpm_limit: parseInt(tpmLimit) || 100000,
        duration: expiration || null,
      })
    })
      .then(function(resp) {
        if (!resp.ok) throw new Error('Generation failed');
        return resp.json();
      })
      .then(function(data) {
        setNewKey(data.key);
        showToast('success', 'LLM API key generated!');
        setShowForm(false);
        setKeyName('');
        loadKeys();
      })
      .catch(function(e) { showToast('error', 'Failed to generate key'); })
      .finally(function() { setGenerating(false); });
  };

  var handleRevoke = function(keyId) {
    fetch('/api/v1/llm/keys/' + keyId, { method: 'DELETE', credentials: 'include' })
      .then(function(resp) {
        if (resp.ok) { showToast('success', 'Key revoked'); setConfirmDelete(null); loadKeys(); }
        else showToast('error', 'Failed to revoke key');
      })
      .catch(function() { showToast('error', 'Failed to revoke key'); });
  };

  var copyKey = function() {
    navigator.clipboard.writeText(newKey);
    setCopied(true);
    showToast('success', 'Copied to clipboard!');
    setTimeout(function() { setCopied(false); }, 3000);
  };

  var formatSpend = function(k) {
    var spend = (k.spend != null) ? k.spend.toFixed(4) : '0.0000';
    var budget = k.max_budget || '\u221E';
    var dur = k.budget_duration ? ' per ' + k.budget_duration : '';
    return '$' + spend + ' / $' + budget + dur;
  };

  // If loading failed, show inline error instead of crashing
  if (loadError && !loading) {
    return (
      <div className={'rounded-xl border p-6 ' + tc.card}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={'text-2xl font-bold ' + tc.text + ' flex items-center gap-2'}>
            <BoltIcon className="h-6 w-6" />
            LLM API Keys
          </h2>
        </div>
        <p className={tc.sub}>{loadError}</p>
      </div>
    );
  }

  return (
    <div className={'rounded-xl border p-6 ' + tc.card}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className={'text-2xl font-bold ' + tc.text + ' flex items-center gap-2'}>
            <BoltIcon className="h-6 w-6" />
            LLM API Keys
          </h2>
          <p className={'mt-2 ' + tc.sub}>
            Generate <code className="px-1 py-0.5 rounded bg-black/20 text-sm">sk-...</code> keys for OpenAI-compatible clients (opencode, Cursor, custom apps)
          </p>
          <p className={'mt-1 text-sm ' + tc.sub}>
            Base URL: <code className="px-1 py-0.5 rounded bg-black/20">https://llm.unicorncommander.ai/v1</code>
          </p>
        </div>
        <button onClick={function() { setShowForm(!showForm); }} className={'px-4 py-2 rounded-lg ' + tc.btn + ' flex items-center gap-2'}>
          <PlusIcon className="h-5 w-5" /> New Key
        </button>
      </div>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} exit={{opacity:0}}
            className={'mb-4 p-3 rounded-lg flex items-center gap-2 ' + (toast.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400')}>
            {toast.type === 'success' ? <CheckCircleIcon className="h-5 w-5" /> : <ExclamationCircleIcon className="h-5 w-5" />}
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Generated Key Display */}
      {newKey && (
        <div className="mb-6 p-4 rounded-lg border-2 border-green-500 bg-green-500/10">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
            <span className="font-semibold text-green-400">Key Generated Successfully</span>
          </div>
          <p className="text-sm text-yellow-300 mb-3">Copy this key now. You will not be able to see it again.</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 px-3 py-2 rounded bg-black/50 text-green-300 font-mono text-sm break-all select-all">{newKey}</code>
            <button onClick={copyKey} className={'px-3 py-2 rounded-lg text-white text-sm flex items-center gap-1 ' + (copied ? 'bg-green-700' : 'bg-green-600 hover:bg-green-700')}>
              <ClipboardDocumentIcon className="h-4 w-4" /> {copied ? 'Copied!' : 'Copy'}
            </button>
            <button onClick={function() { setNewKey(null); }} className="px-3 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white text-sm">Dismiss</button>
          </div>
        </div>
      )}

      {/* Create Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}} className="mb-6 overflow-hidden">
            <div className={'p-4 rounded-lg border ' + (isLight ? 'bg-gray-50 border-gray-200' : 'bg-black/20 border-white/10')}>
              <h3 className={'font-semibold mb-4 ' + tc.text}>Generate New LLM Key</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                <div className="md:col-span-2 lg:col-span-3">
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Key Name *</label>
                  <input value={keyName} onChange={function(e) { setKeyName(e.target.value); }} placeholder="e.g. opencode-mac, production-server" className={'w-full px-3 py-2 rounded-lg border ' + tc.input} />
                </div>
                <div>
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Max Budget (USD)</label>
                  <input type="number" value={maxBudget} onChange={function(e) { setMaxBudget(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input} />
                </div>
                <div>
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Budget Reset</label>
                  <select value={budgetDuration} onChange={function(e) { setBudgetDuration(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input}>
                    <option value="1d">Daily</option>
                    <option value="7d">Weekly</option>
                    <option value="30d">Monthly</option>
                    <option value="365d">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Expiration</label>
                  <select value={expiration} onChange={function(e) { setExpiration(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input}>
                    <option value="30d">30 days</option>
                    <option value="90d">90 days</option>
                    <option value="180d">6 months</option>
                    <option value="365d">1 year</option>
                    <option value="">Never</option>
                  </select>
                </div>
                <div>
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Rate Limit (RPM)</label>
                  <input type="number" value={rpmLimit} onChange={function(e) { setRpmLimit(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input} />
                </div>
                <div>
                  <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Token Limit (TPM)</label>
                  <input type="number" value={tpmLimit} onChange={function(e) { setTpmLimit(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleGenerate} disabled={generating || !keyName.trim()} className={'px-4 py-2 rounded-lg ' + tc.btn + ' flex items-center gap-2 disabled:opacity-50'}>
                  {generating ? <ArrowPathIcon className="h-5 w-5 animate-spin" /> : <KeyIcon className="h-5 w-5" />}
                  {generating ? 'Generating...' : 'Generate Key'}
                </button>
                <button onClick={function() { setShowForm(false); }} className="px-4 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white">Cancel</button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keys List */}
      {loading ? (
        <div className="flex justify-center py-8"><ArrowPathIcon className={'h-8 w-8 animate-spin ' + tc.sub} /></div>
      ) : keys.length === 0 && !newKey ? (
        <div className={'rounded-lg border-2 border-dashed p-8 text-center ' + tc.card}>
          <BoltIcon className={'h-12 w-12 mx-auto mb-3 ' + tc.sub} />
          <p className={tc.sub + ' mb-2'}>No LLM API keys yet.</p>
          <p className={'text-sm ' + tc.sub}>Generate a key to start using the inference API with any OpenAI-compatible client.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {keys.map(function(k) {
            return (
              <div key={k.key_id} className={'rounded-lg border p-4 ' + tc.row}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <KeyIcon className={'h-5 w-5 ' + tc.sub} />
                    <div>
                      <span className={'font-semibold ' + tc.text}>{k.key_name}</span>
                      <code className={'ml-2 px-2 py-0.5 rounded text-xs ' + (isLight ? 'bg-gray-200 text-gray-700' : 'bg-black/30 text-gray-400')}>{k.key_preview}</code>
                    </div>
                  </div>
                  {confirmDelete === k.key_id ? (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-red-400">Revoke?</span>
                      <button onClick={function() { handleRevoke(k.key_id); }} className="px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs">Yes</button>
                      <button onClick={function() { setConfirmDelete(null); }} className="px-2 py-1 rounded bg-gray-600 text-white text-xs">No</button>
                    </div>
                  ) : (
                    <button onClick={function() { setConfirmDelete(k.key_id); }} className="p-1.5 rounded hover:bg-red-500/20 text-red-400" title="Revoke key">
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className={'flex flex-wrap gap-4 text-xs ' + tc.sub}>
                  <span className="flex items-center gap-1"><CurrencyDollarIcon className="h-3.5 w-3.5" /> {formatSpend(k)}</span>
                  <span className="flex items-center gap-1"><BoltIcon className="h-3.5 w-3.5" /> {k.rpm_limit || '\u221E'} RPM</span>
                  <span className="flex items-center gap-1"><ClockIcon className="h-3.5 w-3.5" /> {k.expires ? new Date(k.expires).toLocaleDateString() : 'No expiry'}</span>
                  {k.models && k.models.length > 0 && <span>Models: {k.models.join(', ')}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
