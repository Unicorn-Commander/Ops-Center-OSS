import { useEffect, useState } from 'react';

/**
 * useBillingConfig — reads this deployment's PLUGGABLE billing provider.
 *
 * Ops-Center is the single pane of glass; billing is configured per-server.
 * The backend (/api/v1/billing/provider-config) tells us whether THIS console
 * bills locally (its own Stripe + credits) or federates to a central hub
 * (e.g. billing.unicorncommander.ai). The UI adapts off this — same code on
 * every deployment, only config changes.
 *
 * Fetched once and cached at module scope (config is per-deployment, not
 * per-user). Degrades safely to a "local, full UI" default if the endpoint
 * is missing, so older nodes never break.
 */

const DEFAULT_CONFIG = {
  provider: 'local', // local | federated | disabled
  display_name: 'This deployment',
  manage_url: '',
  buy_credits_url: '',
  currency: 'usd',
  capabilities: { saved_cards: true, buy_credits: true, invoices: true, subscriptions: true },
  source: { kind: 'local', label: 'This server' },
  // Federated provenance (branding only; blank unless provider === 'federated').
  // Defaulted here so older nodes whose endpoint predates these fields degrade safely.
  provider_display_name: '',
  provider_url: '',
  provider_logo_url: '',
  stripe_publishable_key: '',
};

let _cache = null;
let _inflight = null;

export async function fetchBillingConfig() {
  if (_cache) return _cache;
  if (_inflight) return _inflight;
  _inflight = fetch('/api/v1/billing/provider-config', { credentials: 'include' })
    .then((r) => (r.ok ? r.json() : DEFAULT_CONFIG))
    .then((cfg) => {
      _cache = { ...DEFAULT_CONFIG, ...cfg, capabilities: { ...DEFAULT_CONFIG.capabilities, ...(cfg?.capabilities || {}) } };
      _inflight = null;
      return _cache;
    })
    .catch(() => {
      _inflight = null;
      return DEFAULT_CONFIG;
    });
  return _inflight;
}

export function useBillingConfig() {
  const [config, setConfig] = useState(_cache);
  const [loading, setLoading] = useState(!_cache);

  useEffect(() => {
    let alive = true;
    fetchBillingConfig().then((cfg) => {
      if (alive) {
        setConfig(cfg);
        setLoading(false);
      }
    });
    return () => {
      alive = false;
    };
  }, []);

  return { config: config || DEFAULT_CONFIG, loading };
}

export default useBillingConfig;
