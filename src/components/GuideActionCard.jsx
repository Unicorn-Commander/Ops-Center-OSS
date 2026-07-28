import React, { useState } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

// Confirm/Cancel card for a Guide-proposed account action (Phase 2 mutations).
// The model can only PROPOSE; nothing happens until the user clicks Confirm,
// which calls POST /api/v1/help/guide/confirm-action (executed server-side AS the
// user). Self-contained: it manages its own confirm → result/error lifecycle.
export default function GuideActionCard({ action }) {
  const [state, setState] = useState('idle'); // idle | working | done | error | cancelled
  const [result, setResult] = useState(null);
  const [err, setErr] = useState('');

  const confirm = async () => {
    setState('working');
    try {
      const res = await fetch('/api/v1/help/guide/confirm-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action_id: action.id }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        setErr(data.detail || 'That action could not be completed.');
        setState('error');
        return;
      }
      setResult(data.result || {});
      setState('done');
    } catch (e) {
      setErr('I could not reach the service to complete that.');
      setState('error');
    }
  };

  if (state === 'cancelled') {
    return <div className="text-xs italic text-gray-500 dark:text-gray-400">Cancelled — nothing was changed.</div>;
  }

  if (state === 'done') {
    const apiKey = result?.api_key;
    return (
      <div className="rounded-lg border border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20 p-3 text-sm">
        <div className="flex items-center gap-1.5 font-medium text-green-700 dark:text-green-300">
          <CheckCircleIcon className="h-4 w-4" /> Done
        </div>
        {apiKey ? (
          <div className="mt-2 space-y-1.5">
            <p className="text-xs text-gray-600 dark:text-gray-300">{result?.warning || 'Save this key now — you won’t be able to see it again.'}</p>
            <code className="block break-all rounded bg-gray-900 text-green-300 px-2 py-1.5 text-xs select-all">{apiKey}</code>
            {result?.expires_at && (
              <p className="text-[11px] text-gray-500">Expires {new Date(result.expires_at).toLocaleDateString()}. Manage keys under Account → API Keys.</p>
            )}
          </div>
        ) : (
          <p className="mt-1 text-xs text-gray-600 dark:text-gray-300">The action completed successfully.</p>
        )}
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="rounded-lg border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 p-3 text-sm text-red-700 dark:text-red-300">
        <div className="flex items-center gap-1.5"><ExclamationTriangleIcon className="h-4 w-4" /> {err}</div>
      </div>
    );
  }

  // idle / working — the confirmation card
  return (
    <div className="rounded-lg border border-purple-300 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20 p-3 text-sm">
      <p className="font-medium text-gray-800 dark:text-gray-100">{action.title}</p>
      {action.summary && <p className="mt-0.5 text-xs text-gray-600 dark:text-gray-300">{action.summary}</p>}
      <div className="mt-2 flex gap-2">
        <button
          onClick={confirm}
          disabled={state === 'working'}
          className="px-3 py-1 rounded text-xs font-medium bg-purple-600 text-white hover:bg-purple-500 disabled:opacity-50"
        >
          {state === 'working' ? 'Working…' : (action.confirm_label || 'Confirm')}
        </button>
        <button
          onClick={() => setState('cancelled')}
          disabled={state === 'working'}
          className="px-3 py-1 rounded text-xs border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
