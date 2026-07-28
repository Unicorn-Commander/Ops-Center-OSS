/**
 * Network - VPN Keys (Admin)
 *
 * Manage Headscale pre-auth keys and connected VPN nodes from the dashboard.
 * Admin-only. Proxies through the ops-center backend to `docker exec` into
 * the unicorn-headscale container.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  KeyIcon, PlusIcon, TrashIcon, ClipboardDocumentIcon,
  CheckCircleIcon, ExclamationCircleIcon, ArrowPathIcon,
  ShieldCheckIcon, ClockIcon, ServerStackIcon, TagIcon,
  SignalIcon, SignalSlashIcon, ComputerDesktopIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

export default function NetworkVPNKeys() {
  const { currentTheme } = useTheme();
  const [tab, setTab] = useState('keys');

  const [keys, setKeys] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [loadingKeys, setLoadingKeys] = useState(true);
  const [loadingNodes, setLoadingNodes] = useState(true);
  const [keysError, setKeysError] = useState(null);
  const [nodesError, setNodesError] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmRevoke, setConfirmRevoke] = useState(null);
  const [confirmRemoveNode, setConfirmRemoveNode] = useState(null);

  const [keyName, setKeyName] = useState('');
  const [keyTag, setKeyTag] = useState('tag:admin');
  const [reusable, setReusable] = useState(true);
  const [ephemeral, setEphemeral] = useState(false);
  const [expiration, setExpiration] = useState('87600h');

  const isUnicorn = currentTheme === 'unicorn';
  const isLight = currentTheme === 'light';

  const tc = {
    card: isUnicorn ? 'bg-purple-900/50 backdrop-blur-xl border-white/20' : isLight ? 'bg-white border-gray-200' : 'bg-slate-800 border-slate-700',
    text: isUnicorn ? 'text-purple-100' : isLight ? 'text-gray-900' : 'text-slate-100',
    sub: isUnicorn ? 'text-purple-300' : isLight ? 'text-gray-600' : 'text-slate-400',
    input: isUnicorn ? 'bg-purple-900/50 border-white/20 text-purple-100' : isLight ? 'bg-gray-50 border-gray-300 text-gray-900' : 'bg-slate-900 border-slate-600 text-slate-100',
    btn: isUnicorn ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white',
    btnGhost: isLight ? 'bg-gray-200 hover:bg-gray-300 text-gray-800' : 'bg-slate-700 hover:bg-slate-600 text-slate-100',
    row: isLight ? 'bg-gray-50 border-gray-200' : 'bg-black/20 border-white/10',
    tabActive: isUnicorn ? 'bg-purple-600 text-white' : isLight ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white',
    tabIdle: isLight ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' : 'bg-slate-700/40 text-slate-300 hover:bg-slate-700',
    badgeOn: 'bg-green-500/20 text-green-400 border border-green-500/40',
    badgeOff: isLight ? 'bg-gray-200 text-gray-500 border border-gray-300' : 'bg-slate-700 text-slate-400 border border-slate-600',
    badgeWarn: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40',
  };

  const showToast = useCallback(function(type, message) {
    setToast({ type: type, message: message });
    setTimeout(function() { setToast(null); }, 4000);
  }, []);

  const loadKeys = useCallback(function() {
    setLoadingKeys(true);
    fetch('/api/v1/network/vpn-keys', { credentials: 'include' })
      .then(function(resp) {
        if (resp.status === 403) throw new Error('forbidden');
        if (!resp.ok) throw new Error('load failed');
        return resp.json();
      })
      .then(function(data) { setKeys(Array.isArray(data) ? data : []); setKeysError(null); })
      .catch(function(e) {
        setKeys([]);
        setKeysError(e.message === 'forbidden' ? 'Admin access required.' : 'Could not load VPN keys. Headscale may be unavailable.');
      })
      .finally(function() { setLoadingKeys(false); });
  }, []);

  const loadNodes = useCallback(function() {
    setLoadingNodes(true);
    fetch('/api/v1/network/nodes', { credentials: 'include' })
      .then(function(resp) {
        if (resp.status === 403) throw new Error('forbidden');
        if (!resp.ok) throw new Error('load failed');
        return resp.json();
      })
      .then(function(data) { setNodes(Array.isArray(data) ? data : []); setNodesError(null); })
      .catch(function(e) {
        setNodes([]);
        setNodesError(e.message === 'forbidden' ? 'Admin access required.' : 'Could not load VPN nodes.');
      })
      .finally(function() { setLoadingNodes(false); });
  }, []);

  useEffect(function() { loadKeys(); loadNodes(); }, [loadKeys, loadNodes]);

  useEffect(function() {
    if (tab !== 'nodes') return;
    const id = setInterval(loadNodes, 30000);
    return function() { clearInterval(id); };
  }, [tab, loadNodes]);

  const handleGenerate = function() {
    setGenerating(true);
    const body = {
      name: keyName.trim() || null,
      tags: [keyTag],
      reusable: reusable,
      ephemeral: ephemeral,
      expiration: expiration,
    };
    fetch('/api/v1/network/vpn-keys', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(function(resp) {
        if (!resp.ok) return resp.text().then(function(t) { throw new Error(t || 'failed'); });
        return resp.json();
      })
      .then(function(data) {
        setNewKey(data.key);
        showToast('success', 'VPN pre-auth key generated');
        setShowForm(false);
        setKeyName('');
        loadKeys();
      })
      .catch(function(e) {
        showToast('error', 'Failed to generate key');
        console.error(e);
      })
      .finally(function() { setGenerating(false); });
  };

  const handleRevoke = function(keyId) {
    fetch('/api/v1/network/vpn-keys/' + keyId, { method: 'DELETE', credentials: 'include' })
      .then(function(resp) {
        if (!resp.ok) throw new Error('revoke failed');
        showToast('success', 'Key expired');
        setConfirmRevoke(null);
        loadKeys();
      })
      .catch(function() { showToast('error', 'Failed to expire key'); });
  };

  const handleRemoveNode = function(nodeId) {
    fetch('/api/v1/network/nodes/' + nodeId, { method: 'DELETE', credentials: 'include' })
      .then(function(resp) {
        if (!resp.ok) throw new Error('remove failed');
        showToast('success', 'Node removed');
        setConfirmRemoveNode(null);
        loadNodes();
      })
      .catch(function() { showToast('error', 'Failed to remove node'); });
  };

  const copyKey = function() {
    navigator.clipboard.writeText(newKey);
    setCopied(true);
    showToast('success', 'Copied to clipboard');
    setTimeout(function() { setCopied(false); }, 2500);
  };

  const truncateKey = function(k) {
    if (!k) return '';
    if (k.length <= 24) return k;
    return k.slice(0, 18) + '…' + k.slice(-4);
  };

  const formatDate = function(iso) {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch (e) { return iso; }
  };

  const relativeTime = function(iso) {
    if (!iso) return 'never';
    const t = new Date(iso).getTime();
    if (isNaN(t)) return iso;
    const diff = Date.now() - t;
    const s = Math.round(diff / 1000);
    if (s < 60) return s + 's ago';
    const m = Math.round(s / 60);
    if (m < 60) return m + 'm ago';
    const h = Math.round(m / 60);
    if (h < 48) return h + 'h ago';
    const d = Math.round(h / 24);
    return d + 'd ago';
  };

  return (
    <div className="space-y-4">
      <div className={'rounded-xl border p-6 ' + tc.card}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className={'text-2xl font-bold flex items-center gap-2 ' + tc.text}>
              <ShieldCheckIcon className="h-7 w-7" />
              VPN Network
            </h2>
            <p className={'mt-1 ' + tc.sub}>
              Headscale mesh at <code className="px-1 py-0.5 rounded bg-black/20 text-sm">headscale.unicorncommander.ai</code>
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={function() { setTab('keys'); }} className={'px-4 py-2 rounded-lg text-sm font-medium transition ' + (tab === 'keys' ? tc.tabActive : tc.tabIdle)}>
              Pre-Auth Keys
            </button>
            <button onClick={function() { setTab('nodes'); }} className={'px-4 py-2 rounded-lg text-sm font-medium transition ' + (tab === 'nodes' ? tc.tabActive : tc.tabIdle)}>
              Connected Nodes
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {toast && (
          <motion.div initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} exit={{opacity:0}}
            className={'p-3 rounded-lg flex items-center gap-2 ' + (toast.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400')}>
            {toast.type === 'success' ? <CheckCircleIcon className="h-5 w-5" /> : <ExclamationCircleIcon className="h-5 w-5" />}
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      {tab === 'keys' ? (
        <div className={'rounded-xl border p-6 ' + tc.card}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className={'text-lg font-semibold ' + tc.text}>Pre-Auth Keys</h3>
              <p className={'text-sm ' + tc.sub}>
                Used by <code className="px-1 py-0.5 rounded bg-black/20">tailscale up --authkey ...</code> to join the mesh.
              </p>
            </div>
            <button onClick={function() { setShowForm(!showForm); }} className={'px-4 py-2 rounded-lg flex items-center gap-2 ' + tc.btn}>
              <PlusIcon className="h-5 w-5" /> Generate Key
            </button>
          </div>

          {newKey && (
            <div className="mb-6 p-4 rounded-lg border-2 border-green-500 bg-green-500/10">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="font-semibold text-green-400">Pre-auth key generated</span>
              </div>
              <p className="text-sm text-yellow-300 mb-3">Copy it now — Headscale stores it, but this is the cleanest time to grab it.</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 rounded bg-black/50 text-green-300 font-mono text-sm break-all select-all">{newKey}</code>
                <button onClick={copyKey} className={'px-3 py-2 rounded-lg text-white text-sm flex items-center gap-1 ' + (copied ? 'bg-green-700' : 'bg-green-600 hover:bg-green-700')}>
                  <ClipboardDocumentIcon className="h-4 w-4" /> {copied ? 'Copied' : 'Copy'}
                </button>
                <button onClick={function() { setNewKey(null); }} className={'px-3 py-2 rounded-lg text-sm ' + tc.btnGhost}>Dismiss</button>
              </div>
              <div className={'mt-3 text-xs ' + tc.sub}>
                Register a device:&nbsp;
                <code className="px-1 py-0.5 rounded bg-black/40">sudo tailscale up --login-server https://headscale.unicorncommander.ai --authkey {newKey}</code>
              </div>
            </div>
          )}

          <AnimatePresence>
            {showForm && (
              <motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}} className="mb-6 overflow-hidden">
                <div className={'p-4 rounded-lg border ' + (isLight ? 'bg-gray-50 border-gray-200' : 'bg-black/20 border-white/10')}>
                  <h4 className={'font-semibold mb-4 ' + tc.text}>New pre-auth key</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="md:col-span-2">
                      <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Name (note — stored locally for your reference)</label>
                      <input value={keyName} onChange={function(e) { setKeyName(e.target.value); }} placeholder="e.g. strix-halo-laptop" className={'w-full px-3 py-2 rounded-lg border ' + tc.input} />
                    </div>
                    <div>
                      <label className={'block text-sm font-medium mb-1 ' + tc.sub}>ACL Tag</label>
                      <select value={keyTag} onChange={function(e) { setKeyTag(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input}>
                        <option value="tag:admin">tag:admin — full mesh</option>
                        <option value="tag:trusted">tag:trusted — service ports only</option>
                        <option value="tag:partner">tag:partner — commander only</option>
                      </select>
                    </div>
                    <div>
                      <label className={'block text-sm font-medium mb-1 ' + tc.sub}>Expiration</label>
                      <select value={expiration} onChange={function(e) { setExpiration(e.target.value); }} className={'w-full px-3 py-2 rounded-lg border ' + tc.input}>
                        <option value="24h">1 day</option>
                        <option value="168h">7 days</option>
                        <option value="720h">30 days</option>
                        <option value="8760h">1 year</option>
                        <option value="87600h">10 years (effectively permanent)</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className={'flex items-center gap-2 text-sm ' + tc.text}>
                        <input type="checkbox" checked={reusable} onChange={function(e) { setReusable(e.target.checked); }} />
                        Reusable (one key, many devices)
                      </label>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className={'flex items-center gap-2 text-sm ' + tc.text}>
                        <input type="checkbox" checked={ephemeral} onChange={function(e) { setEphemeral(e.target.checked); }} />
                        Ephemeral (node disappears on disconnect)
                      </label>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={handleGenerate} disabled={generating} className={'px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 ' + tc.btn}>
                      {generating ? <ArrowPathIcon className="h-5 w-5 animate-spin" /> : <KeyIcon className="h-5 w-5" />}
                      {generating ? 'Generating…' : 'Generate'}
                    </button>
                    <button onClick={function() { setShowForm(false); }} className={'px-4 py-2 rounded-lg ' + tc.btnGhost}>Cancel</button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {loadingKeys ? (
            <div className="flex justify-center py-10"><ArrowPathIcon className={'h-8 w-8 animate-spin ' + tc.sub} /></div>
          ) : keysError ? (
            <div className={'rounded-lg border p-6 text-center ' + tc.card}>
              <ExclamationCircleIcon className="h-10 w-10 mx-auto mb-2 text-red-400" />
              <p className={tc.sub}>{keysError}</p>
            </div>
          ) : keys.length === 0 ? (
            <div className={'rounded-lg border-2 border-dashed p-8 text-center ' + tc.card}>
              <KeyIcon className={'h-10 w-10 mx-auto mb-3 ' + tc.sub} />
              <p className={tc.sub}>No pre-auth keys yet. Generate one to enroll a device.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {keys.map(function(k) {
                return (
                  <div key={k.id} className={'rounded-lg border p-4 ' + tc.row}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <KeyIcon className={'h-4 w-4 ' + tc.sub} />
                          <code className={'text-sm font-mono ' + tc.text}>{truncateKey(k.key)}</code>
                          <span className={'text-xs px-1.5 py-0.5 rounded ' + (isLight ? 'bg-gray-200 text-gray-700' : 'bg-black/30 text-slate-300')}>id {k.id}</span>
                          {k.reusable && <span className={'text-xs px-1.5 py-0.5 rounded ' + tc.badgeOn}>reusable</span>}
                          {k.ephemeral && <span className={'text-xs px-1.5 py-0.5 rounded ' + tc.badgeWarn}>ephemeral</span>}
                          {k.used && <span className={'text-xs px-1.5 py-0.5 rounded ' + tc.badgeWarn}>used</span>}
                          {k.expired && <span className={'text-xs px-1.5 py-0.5 rounded ' + tc.badgeOff}>expired</span>}
                        </div>
                        <div className={'flex flex-wrap gap-4 text-xs ' + tc.sub}>
                          <span className="flex items-center gap-1"><TagIcon className="h-3.5 w-3.5" />{k.tags && k.tags.length ? k.tags.join(', ') : 'no tags'}</span>
                          <span className="flex items-center gap-1"><ClockIcon className="h-3.5 w-3.5" />created {formatDate(k.created_at)}</span>
                          <span className="flex items-center gap-1"><ClockIcon className="h-3.5 w-3.5" />expires {formatDate(k.expiration)}</span>
                        </div>
                      </div>
                      {confirmRevoke === k.id ? (
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-sm text-red-400">Expire?</span>
                          <button onClick={function() { handleRevoke(k.id); }} className="px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs">Yes</button>
                          <button onClick={function() { setConfirmRevoke(null); }} className={'px-2 py-1 rounded text-xs ' + tc.btnGhost}>No</button>
                        </div>
                      ) : (
                        <button onClick={function() { setConfirmRevoke(k.id); }} className="p-1.5 rounded hover:bg-red-500/20 text-red-400 shrink-0" title="Expire key">
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className={'rounded-xl border p-6 ' + tc.card}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className={'text-lg font-semibold ' + tc.text}>Connected Nodes</h3>
              <p className={'text-sm ' + tc.sub}>Devices registered in the Headscale mesh. Auto-refreshes every 30s.</p>
            </div>
            <button onClick={loadNodes} className={'px-3 py-2 rounded-lg flex items-center gap-2 text-sm ' + tc.btnGhost}>
              <ArrowPathIcon className={'h-4 w-4 ' + (loadingNodes ? 'animate-spin' : '')} /> Refresh
            </button>
          </div>

          {loadingNodes && nodes.length === 0 ? (
            <div className="flex justify-center py-10"><ArrowPathIcon className={'h-8 w-8 animate-spin ' + tc.sub} /></div>
          ) : nodesError ? (
            <div className={'rounded-lg border p-6 text-center ' + tc.card}>
              <ExclamationCircleIcon className="h-10 w-10 mx-auto mb-2 text-red-400" />
              <p className={tc.sub}>{nodesError}</p>
            </div>
          ) : nodes.length === 0 ? (
            <div className={'rounded-lg border-2 border-dashed p-8 text-center ' + tc.card}>
              <ServerStackIcon className={'h-10 w-10 mx-auto mb-3 ' + tc.sub} />
              <p className={tc.sub}>No nodes connected yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className={'text-left ' + tc.sub}>
                    <th className="py-2 pr-3 font-medium">Name</th>
                    <th className="py-2 pr-3 font-medium">Tailscale IP</th>
                    <th className="py-2 pr-3 font-medium">Status</th>
                    <th className="py-2 pr-3 font-medium">Last seen</th>
                    <th className="py-2 pr-3 font-medium">Tags</th>
                    <th className="py-2 pr-3 font-medium">OS</th>
                    <th className="py-2 pr-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {nodes.map(function(n) {
                    const v4 = (n.ip_addresses || []).find(function(ip) { return ip && ip.indexOf(':') === -1; }) || (n.ip_addresses || [])[0] || '—';
                    return (
                      <tr key={n.id} className={'border-t ' + (isLight ? 'border-gray-200' : 'border-white/10')}>
                        <td className={'py-2 pr-3 ' + tc.text}>
                          <div className="flex items-center gap-2">
                            <ComputerDesktopIcon className={'h-4 w-4 ' + tc.sub} />
                            <span className="font-medium">{n.given_name || n.name || ('node-' + n.id)}</span>
                          </div>
                        </td>
                        <td className={'py-2 pr-3 font-mono text-xs ' + tc.text}>{v4}</td>
                        <td className="py-2 pr-3">
                          {n.online ? (
                            <span className={'inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded ' + tc.badgeOn}>
                              <SignalIcon className="h-3.5 w-3.5" /> online
                            </span>
                          ) : (
                            <span className={'inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded ' + tc.badgeOff}>
                              <SignalSlashIcon className="h-3.5 w-3.5" /> offline
                            </span>
                          )}
                        </td>
                        <td className={'py-2 pr-3 text-xs ' + tc.sub}>{relativeTime(n.last_seen)}</td>
                        <td className={'py-2 pr-3 text-xs ' + tc.sub}>{(n.tags || []).join(', ') || '—'}</td>
                        <td className={'py-2 pr-3 text-xs ' + tc.sub}>{n.os || '—'}</td>
                        <td className="py-2 pr-3 text-right">
                          {confirmRemoveNode === n.id ? (
                            <div className="flex items-center gap-2 justify-end">
                              <span className="text-xs text-red-400">Remove?</span>
                              <button onClick={function() { handleRemoveNode(n.id); }} className="px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs">Yes</button>
                              <button onClick={function() { setConfirmRemoveNode(null); }} className={'px-2 py-1 rounded text-xs ' + tc.btnGhost}>No</button>
                            </div>
                          ) : (
                            <button onClick={function() { setConfirmRemoveNode(n.id); }} className="p-1.5 rounded hover:bg-red-500/20 text-red-400" title="Remove node">
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
