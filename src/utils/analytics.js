/**
 * Suite Analytics Bootstrap — Umami + PostHog
 *
 * Single source of analytics for Ops-Center. This is the ONE place every UC
 * suite app should copy to wire tracking, so behaviour stays identical across
 * Ops-Center, Meeting-Ops, etc.
 *
 * Two complementary signals:
 *   - Umami   (web/pageview, self-hosted on commander) — cookieless, privacy-first
 *   - PostHog (product analytics, Cloud US)            — events, identified_only
 *
 * HARD GATE: nothing is loaded unless BOTH of these hold:
 *   1. import.meta.env.PROD  — keeps dev (`npm run dev`) traffic out entirely
 *   2. the relevant key/id is set at build time
 *
 * When a key/id is missing the matching tracker simply no-ops with ZERO network
 * activity. Keys are publish-safe by design (Umami website-id is public, the
 * PostHog `phc_...` key is a publishable project key), so shipping them in the
 * built bundle is expected and fine.
 *
 * Activation (set in the prod build env, e.g. .env.auth on the deploy host):
 *   VITE_UMAMI_WEBSITE_ID  — register Ops-Center as a site in the Umami UI to get it
 *   VITE_POSTHOG_KEY       — create an Ops-Center project in PostHog to get the phc_ key
 *   VITE_POSTHOG_HOST      — optional, defaults to https://us.i.posthog.com
 */

import posthog from 'posthog-js';

// Canonical self-hosted Umami instance (Keycloak-gated, on commander).
const UMAMI_SCRIPT_URL = 'https://analytics.unicorncommander.ai/script.js';
const UMAMI_WEBSITE_ID = import.meta.env.VITE_UMAMI_WEBSITE_ID;

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY;
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com';

// Single gate: only ever track in a production build. Dev builds short-circuit
// before any key is read, so there is no chance of dev traffic leaking out.
const ANALYTICS_ENABLED = import.meta.env.PROD;

/**
 * Inject the Umami pageview script.
 *
 * index.html cannot read Vite env vars, so the snippet lives here instead of the
 * raw HTML. Umami auto-tracks pageviews (incl. SPA route changes) once loaded —
 * no per-route calls needed. Cookieless / default config.
 */
function initUmami() {
  if (!UMAMI_WEBSITE_ID) {
    return; // not registered yet — no script, no network
  }

  // Guard against a double-inject (e.g. HMR or a stray re-call).
  if (document.querySelector('script[data-website-id]')) {
    return;
  }

  const script = document.createElement('script');
  script.async = true;
  script.defer = true;
  script.src = UMAMI_SCRIPT_URL;
  script.setAttribute('data-website-id', UMAMI_WEBSITE_ID);
  document.head.appendChild(script);
}

/**
 * Initialize PostHog product analytics.
 *
 * Config mirrors Meeting-Ops to stay inside the free tier and avoid surprise
 * cost: autocapture OFF, session replay OFF, person profiles only for users we
 * explicitly identify().
 */
function initPostHog() {
  if (!POSTHOG_KEY) {
    return; // no project key — fully inert, zero network
  }

  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    person_profiles: 'identified_only', // don't create profiles for anon visitors
    autocapture: false,                 // cost control — no auto DOM event capture
    disable_session_recording: true,    // cost control — session replay OFF
    capture_pageview: true,             // lightweight pageviews are fine
  });
}

/**
 * Bootstrap all analytics. Call once at app startup (src/main.jsx).
 *
 * Safe to call unconditionally — it self-gates on PROD + key presence and never
 * throws (analytics must never break the app).
 */
export function initAnalytics() {
  if (!ANALYTICS_ENABLED) {
    return; // dev build — stay completely silent
  }

  try {
    initUmami();
  } catch (error) {
    console.debug('Umami init skipped:', error?.message);
  }

  try {
    initPostHog();
  } catch (error) {
    console.debug('PostHog init skipped:', error?.message);
  }
}

// Re-export the PostHog client so feature code can capture events / identify
// users. It is a harmless no-op when PostHog was never initialized.
export { posthog };

export default initAnalytics;
