// Comprehensive, route-aware Help content for the Ops-Center admin console.
// Authored grounded in the actual page components (do not invent features).
// Consumed by src/components/HelpPanel.jsx (static help) and seeded into the
// Colonel "Guide" persona's knowledge (the specialized help agent).
//
// Shape:
//   helpContent[key] = { title, sections: [{ title, content }] }
//   routeHelp        = ordered [pathnameMatcher, key] — most specific first
//   guideFaqs        = [{ area, q, a }] (the Guide agent's Q&A knowledge base)

export const helpContent = {
  // ---- Platform / dashboard ----------------------------------------------
  dashboard: {
    title: 'Admin Dashboard',
    sections: [
      { title: 'System Health', content: 'Real-time status of critical services (PostgreSQL, Redis, Keycloak, inference gateway, Traefik). Green = all core systems up; red = at least one is down. Check here first when things seem slow.' },
      { title: 'GPU & Local AI', content: 'Shows detected GPUs and local inference runtimes. Verify local models are running before requests fall through to cloud providers.' },
      { title: 'Resource Utilization', content: 'CPU, memory, and disk for this server. Sustained 90%+ means the box is near capacity and inference/downloads/DB writes may slow.' },
      { title: 'Hosted Sites & Activity', content: 'Live sites behind Traefik with health, plus a timeline of recent events (logins, restarts, backups, billing).' },
    ],
  },
  user_dashboard: {
    title: 'My Dashboard',
    sections: [
      { title: 'Credit Balance', content: 'Your remaining credits with a usage bar. Unlimited tiers show "Unlimited"; paid tiers show % used before the monthly reset.' },
      { title: 'Usage & Spending', content: 'Credits spent this period vs your allocation, with a month-end projection to help budget peak usage.' },
      { title: 'Subscription & Renewal', content: 'Your tier and next reset date. "Upgrade Plan" moves you to a higher tier for more credits/features.' },
      { title: 'Usage Breakdown', content: 'Which models and services consumed the most this month — find your cost drivers.' },
    ],
  },
  'platform-landing': {
    title: 'Landing Page Customization',
    sections: [
      { title: 'Theme & Colors', content: 'Pick a preset or set primary/secondary/accent colors for the public landing page; preview before saving.' },
      { title: 'Branding', content: 'Company name, tagline, logo, and emoji shown in the landing header and browser tab.' },
      { title: 'Services & Links', content: 'Add/remove/reorder service cards and custom links; enable each individually.' },
    ],
  },
  'platform-white-label': {
    title: 'White-Label Builder',
    sections: [
      { title: 'Company Branding', content: 'Logo, display name, tagline shown in headers and auth screens, with a live preview.' },
      { title: 'Colors & Presets', content: 'Define brand colors via picker/hex or apply a preset; buttons, links and highlights follow them.' },
      { title: 'Custom Domain & CSS', content: 'Set a custom domain and optional custom CSS; hide "Powered by" attribution for a fully-owned feel.' },
    ],
  },
  'platform-extensions': {
    title: 'Extensions Marketplace',
    sections: [
      { title: 'Browse', content: 'Catalog of optional add-ons (TTS, STT, agents, analytics) by category and price. BYOK extensions are free if you bring your own key.' },
      { title: 'Search & Filter', content: 'Keyword search, category filter, and sort by popularity or price.' },
      { title: 'Cart & Checkout', content: 'Add extensions, review the monthly subtotal, and check out.' },
    ],
  },
  'system-settings': {
    title: 'System Settings',
    sections: [
      { title: 'Authentication', content: 'SSO providers, session timeouts, password policy, and 2FA — affects how everyone signs in.' },
      { title: 'Branding & Features', content: 'Platform-wide defaults plus feature toggles to turn major capabilities on/off without a deploy.' },
      { title: 'Integrations', content: 'Third-party setup (Stripe, Lago, webhooks) with per-integration test buttons.' },
    ],
  },
  'system-security': {
    title: 'Security Center',
    sections: [
      { title: 'Audit Log', content: 'Read-only security events: logins, password changes, key additions, failed attempts — with timestamp and actor.' },
      { title: 'Users via Keycloak', content: 'Accounts, roles, passwords and MFA are managed in Keycloak; use the "Manage in Keycloak" link.' },
      { title: 'Sessions', content: 'Review and revoke active sessions to force re-authentication.' },
    ],
  },

  // ---- Billing & plans ----------------------------------------------------
  'billing-tiers': {
    title: 'Subscription Tiers',
    sections: [
      { title: 'What It Does', content: 'Create/manage subscription plans — price, API-call limits, seats, LLM markup, and which apps each tier includes.' },
      { title: 'Tier Features', content: 'Use the sync (⟳) icon on a tier to toggle which apps it includes; features are many-to-many with tiers.' },
      { title: 'Clone, Edit, Migrate', content: 'Clone a tier to make a variant, edit pricing/limits (the tier code is fixed after creation), and migrate a user between tiers with an audited reason.' },
      { title: 'Invite-only Tiers', content: 'Mark special tiers (VIP/founder/beta) invite-only so users can’t self-select them — admins grant them.' },
    ],
  },
  'billing-apps': {
    title: 'App Management',
    sections: [
      { title: 'What It Does', content: 'Define the apps/features that can be granted to tiers — each has a machine key, name, category, description.' },
      { title: 'Create / Activate', content: 'Create an app with a lowercase_underscore key and category; toggle active to show/hide it from new tier configs.' },
      { title: 'Tier Coverage', content: 'The Subscription Tiers column shows which tiers include each app.' },
    ],
  },
  'billing-pricing': {
    title: 'Dynamic Pricing',
    sections: [
      { title: 'BYOK vs Platform', content: 'Set markups for bring-your-own-key users (small, ~5%) vs platform pricing per tier (the platform absorbs provider cost and bills with markup).' },
      { title: 'Credit Packages', content: 'Create buyable credit packs; effective price/1k credits is shown. Optional Stripe price ID ties to live checkout.' },
      { title: 'Calculator & Analytics', content: 'Estimate request cost across tiers/providers and view revenue by BYOK vs platform.' },
    ],
  },
  'billing-rates': {
    title: 'Pricing & Rates (Rate Book)',
    sections: [
      { title: 'What It Does', content: 'The rate book: what providers charge you vs what you bill users. Set global markup, credit value, local strategy, and per-model overrides.' },
      { title: 'Credit Value & Markup', content: 'Credit value (default $0.01) sets credits-per-dollar; default markup applies to all cloud models; the safety buffer absorbs provider price hikes.' },
      { title: 'Local Inference', content: '"Bundled" = free, fair-use throttled (local GPUs); "Metered" = flat rate per million tokens.' },
      { title: 'Refresh & Overrides', content: 'Refresh pulls live provider costs from OpenRouter (your markup preserved); inline-edit a model’s markup to override the default.' },
    ],
  },
  'billing-revenue': {
    title: 'Revenue Dashboard',
    sections: [
      { title: 'Overview', content: 'Total revenue, customers, ARPU, churn, MRR and trends.' },
      { title: 'Per-User', content: 'Revenue by customer — tier, total spend, usage, trend. Spot high-value customers and churn risks.' },
      { title: 'System', content: 'Platform billing: total invoiced, open invoices, failed payments, refunds, revenue by tier.' },
    ],
  },
  'billing-credits': {
    title: 'Buy Credits',
    sections: [
      { title: 'Balance', content: 'Your current credit balance and monthly allocation — drawn down as you use metered AI.' },
      { title: 'Packages', content: 'Active credit packs with price, effective rate, and a Buy button (Stripe checkout). Credits are added instantly on payment.' },
      { title: 'History', content: 'Past purchases with date, pack, credits, amount, and status.' },
    ],
  },
  'billing-inference-policy': {
    title: 'Inference Pricing Policy',
    sections: [
      { title: 'What It Does', content: 'Decide which models are bundled into a subscription (included, cost absorbed) vs billed from the credit wallet (metered) — per (app, model).' },
      { title: 'Default = Metered', content: 'Every (app, model) defaults to metered. Add an "included" row to bundle a model into a specific app.' },
      { title: 'Matching', content: 'Most-specific wins: exact model > prefix (Qwen3.6-*) > wildcard (*). Bundle a premium model for one app while metering it elsewhere.' },
      { title: 'Safe by Default', content: 'No rows = everything metered (no behavior change). Deleting a row reverts that pair to metered.' },
    ],
  },
  'billing-credit-packs': {
    title: 'Credit Packages',
    sections: [
      { title: 'What It Does', content: 'Define the one-time credit packs shown on the Buy Credits page — credits, price, optional discount and Stripe IDs.' },
      { title: 'Pricing', content: 'Effective price per 1,000 credits is computed automatically; the discount % is a visual badge — set the USD price to change what customers pay.' },
      { title: 'Stripe & Activation', content: 'Optional Stripe price/product IDs tie a pack to live checkout for accurate reporting; toggle Active to show/hide without losing history.' },
    ],
  },
  'billing-agent-pricing': {
    title: 'Federation Agent Pricing',
    sections: [
      { title: 'What It Does', content: 'Set how many units each federated agent invocation costs; the Lago plan decides what a unit bills.' },
      { title: 'Default + Overrides', content: 'A default applies to all agents; add per-agent rows to charge specific agents more (e.g. deep-research = 5 units) or less.' },
      { title: 'Validation', content: 'Units must be numbers ≥ 0; agent IDs unique; empty rows rejected on save.' },
    ],
  },

  // ---- AI & models --------------------------------------------------------
  'ai-hub': {
    title: 'AI Hub',
    sections: [
      { title: 'Overview', content: 'Central AI view: model catalog, providers, a testing lab, and usage analytics in one place.' },
    ],
  },
  'ai-models': {
    title: 'Model Catalog',
    sections: [
      { title: 'What It Does', content: 'Unified catalog of federation (local-GPU) models plus cloud models via the gateway. Enable/disable and filter by source.' },
      { title: 'Federation vs Cloud', content: 'Federation models run on your GPUs (free/bundled); cloud models route through the LiteLLM gateway at cost + markup.' },
      { title: 'Tier Visibility', content: 'Curated model lists control which models each app/tier sees.' },
    ],
  },
  'ai-model-lists': {
    title: 'Model Lists',
    sections: [
      { title: 'Curated Lists', content: 'Build per-app model lists (e.g. for a chat app) with tier-based visibility and ordering; import/export as JSON.' },
    ],
  },
  'ai-colonel': {
    title: 'The Colonel',
    sections: [
      { title: 'What It Is', content: 'Colonel is the ops-center-native AI agent — it runs inside Ops-Center (not dependent on Brigade) and can help manage the server, including Brigade itself if Brigade is down.' },
      { title: 'Chat & Skills', content: 'Talk to Colonel for server tasks; it has skills (logs, services, GPU, DB, etc.) and can delegate specialist work to Brigade agents.' },
      { title: 'The Guide', content: 'A safe, read-only Guide persona of Colonel powers the Help panel’s "Ask the Guide" tab — it answers how-to questions but can’t run destructive actions.' },
    ],
  },
  'ai-local-models': {
    title: 'Local Models',
    sections: [
      { title: 'What It Does', content: 'Monitor LLM services running on federation nodes — status, VRAM, latency.' },
    ],
  },
  'ai-gpu-services': {
    title: 'GPU Services',
    sections: [
      { title: 'What It Does', content: 'Federated GPU inventory across nodes — VRAM, temperature, utilization — to plan where heavy workloads run.' },
    ],
  },
  'ai-rag-services': {
    title: 'RAG Services',
    sections: [
      { title: 'What It Does', content: 'Manage embeddings/reranker (Infinity) services and their GPU memory for retrieval-augmented features.' },
    ],
  },

  // ---- Infrastructure & federation ---------------------------------------
  'infra-services': {
    title: 'Services',
    sections: [
      { title: 'Manage Services', content: 'View status (running/starting/stopped), CPU/memory, and act — restart, start, stop, view logs, open the service UI.' },
      { title: 'Auto-Discovery', content: 'Services are auto-discovered from Docker containers and registered in the federation.' },
    ],
  },
  'infra-resources': {
    title: 'System Resources',
    sections: [
      { title: 'Health', content: 'CPU, memory, disk and network with real-time and historical trends; alerts highlight critical (>90%) usage.' },
      { title: 'Disk & Network', content: 'Per-mount disk space and network throughput/packet-loss; cleanup tools free space when low.' },
    ],
  },
  'infra-hardware': {
    title: 'Hardware',
    sections: [
      { title: 'Inventory', content: 'Auto-detected hardware across federated nodes — GPUs/VRAM, CPU, RAM, storage — with list and topology views.' },
      { title: 'Capacity Planning', content: 'See total available resources and utilization to plan workload distribution.' },
    ],
  },
  'infra-network': {
    title: 'Network',
    sections: [
      { title: 'Config & Firewall', content: 'Routing, DNS, firewall rules, and which interfaces carry federation traffic (encrypted over a WireGuard mesh).' },
      { title: 'VPN Keys', content: 'Manage/rotate WireGuard peer keys for secure federation connections.' },
    ],
  },
  'infra-storage': {
    title: 'Storage & Backup',
    sections: [
      { title: 'Backups', content: 'Schedule backups (cron), view history/size/retention, and restore from a point in time.' },
      { title: 'Monitoring', content: 'Disk usage across partitions with alerts at ~80%; cleanup and retention policies free space.' },
    ],
  },
  'infra-traefik': {
    title: 'Traefik',
    sections: [
      { title: 'Reverse Proxy', content: 'Traefik terminates TLS and routes traffic to services; manages certificates automatically (Let’s Encrypt).' },
      { title: 'Routes & SSL', content: 'View/configure host- and path-based routes, backends, and certificate expiry.' },
    ],
  },
  'infra-federation': {
    title: 'Federation Settings',
    sections: [
      { title: 'Node Identity & Branding', content: 'This node’s ID, display name, public URL, region, and branding shown to peers.' },
      { title: 'Peers & Discovery', content: 'Add/test/remove peer nodes and toggle which local services are advertised. (Enforced trust is set on the Contracts page.)' },
      { title: 'Key & Heartbeat', content: 'Rotate the federation key and set the heartbeat interval (default 30s).' },
    ],
  },
  'infra-federation-contracts': {
    title: 'Federation Contracts',
    sections: [
      { title: 'What They Are', content: 'ENFORCED trust rules per peer: trust_mode, publish[] (what a peer can see), consume[] (what it can call). This is what actually gates federation traffic.' },
      { title: 'Trust Modes', content: 'full = unrestricted both ways; scoped = only publish/consume grants; consumer = peer calls you; publisher = you call peer; isolated = no traffic.' },
      { title: 'Publish / Consume ACLs', content: 'List service types (llm, embeddings, agents, image_gen) or specific grants like agents/sql-analyst.' },
      { title: 'Global Default', content: 'Governs unknown peers with no contract. isolated = deny-by-default (the secure default). Changes apply within ~30s.' },
    ],
  },

  // ---- People & access ----------------------------------------------------
  'people-users': {
    title: 'User Management',
    sections: [
      { title: 'Overview & Filters', content: 'All users with stats; filter by tier, role, status, org, dates, email-verified, BYOK. Search by email/name.' },
      { title: 'Actions', content: 'Create/edit users, manage roles, reset passwords, view/revoke sessions, delete — all audited.' },
      { title: 'Bulk & API Keys', content: 'CSV import/export, bulk role/tier/suspend; users can generate bcrypt-hashed API keys metered to their tier.' },
    ],
  },
  'people-users-detail': {
    title: 'User Profile',
    sections: [
      { title: 'Account & Subscription', content: 'Profile, verification, source (Keycloak), plus tier, billing IDs, and subscription dates.' },
      { title: 'Roles & Orgs', content: 'Assigned roles (with a permission grid) and org memberships (member/admin/owner per org).' },
      { title: 'Activity & Usage', content: 'Timeline of auth/role/billing events, API-quota progress, and active sessions.' },
    ],
  },
  'people-organizations': {
    title: 'Organizations',
    sections: [
      { title: 'Tenants', content: 'Organizations are workspaces/tenants — teams that share billing, a credit pool, and config. Browse with status/tier filters.' },
      { title: 'Actions & Members', content: 'Create/suspend/delete orgs; from an org, invite members and assign roles (member/admin/owner).' },
    ],
  },
  'people-organizations-billing': {
    title: 'Organization Billing',
    sections: [
      { title: 'Plan & Credit Pool', content: 'The org’s plan and an org-wide credit pool (total/allocated/used/remaining); add credits charged to the org card.' },
      { title: 'Team Allocations', content: 'Give members per-user monthly budgets and see usage attribution by member and model.' },
    ],
  },
  'people-invite-codes': {
    title: 'Invite Codes',
    sections: [
      { title: 'What They Do', content: 'Signup codes that grant a specific tier. Track status (active/expired/exhausted), uses, and expiry.' },
      { title: 'Generate & Limit', content: 'Create a code for a tier with optional max-uses and expiry; activate/deactivate and add internal notes.' },
    ],
  },
  'people-authentication': {
    title: 'Authentication & SSO',
    sections: [
      { title: 'Keycloak SSO', content: 'Keycloak (uchub realm) is the identity provider — health, users, sessions, and a link to its admin console.' },
      { title: 'Identity Providers', content: 'Brokered Google/GitHub/Microsoft login; first social login auto-creates an account.' },
      { title: 'Sessions & TLS', content: 'Session timeout settings and SSL/TLS status protecting auth traffic.' },
    ],
  },
  'people-org-features': {
    title: 'Org Feature Grants',
    sections: [
      { title: 'What It Does', content: 'Grant specific apps to an organization regardless of its tier — for trials, partner deals, or enterprise extras.' },
      { title: 'Grant / Revoke', content: 'Pick an org, grant an app with an audited reason; grants persist across tier changes. Revoke to remove access.' },
    ],
  },

  // ---- Monitoring & integrations -----------------------------------------
  'monitoring-analytics': {
    title: 'Analytics',
    sections: [
      { title: 'Tabs', content: 'Overview, Users, Billing, Services, and LLM tabs with time-series charts; filter by date range.' },
    ],
  },
  'monitoring-logs': {
    title: 'Logs & Diagnostics',
    sections: [
      { title: 'Live & History', content: 'Stream container logs in real time with level filters, or search history with regex and date filters.' },
      { title: 'Export', content: 'Export filtered logs as JSON; adjust buffer size and auto-scroll.' },
    ],
  },
  'monitoring-alerts': {
    title: 'Alerts',
    sections: [
      { title: 'Active & Rules', content: 'Current alerts (critical/warning/info) you can acknowledge, plus thresholds for CPU/memory/disk/service checks.' },
      { title: 'History', content: 'Resolved alerts with creation/resolution times and duration; active alerts refresh every 30s.' },
    ],
  },
  'monitoring-audit': {
    title: 'Audit Log',
    sections: [
      { title: 'Timeline', content: 'Color-coded system/user/admin events with severity; filter by date, type, user, or action.' },
      { title: 'Details & Export', content: 'Expand an event for IP, user agent, request ID, and metadata; export to CSV for compliance.' },
    ],
  },
  'monitoring-website': {
    title: 'Website Monitor',
    sections: [
      { title: 'Status', content: 'Monitored sites with up/down/degraded status, response time, uptime %, and SSL validity.' },
      { title: 'Checks', content: 'Trigger checks manually or auto-discover sites from Traefik/DNS; set per-site intervals.' },
    ],
  },
  'monitoring-tools': {
    title: 'External Monitoring Tools',
    sections: [
      { title: 'Connect', content: 'Configure Grafana, Prometheus, and Umami endpoints/keys with connection tests.' },
    ],
  },
  'integrations-credentials': {
    title: 'Platform Settings (Credentials)',
    sections: [
      { title: 'Credentials', content: 'Integration keys by category (Stripe, Lago, Keycloak, Cloudflare, Forgejo, Federation, Billing) with one-click connection tests.' },
      { title: 'Save vs Restart', content: '"Save" hot-updates settings; "Save & Restart" applies env-var changes with ~5–10s downtime.' },
    ],
  },
  'integrations-email': {
    title: 'Email Settings',
    sections: [
      { title: 'Providers', content: 'Configure Microsoft 365 / Google / SendGrid / Postmark / SES / custom SMTP; one provider is active for outgoing mail.' },
      { title: 'Test & History', content: 'Send a test email to verify; view recent sent mail with delivery status.' },
    ],
  },
  'integrations-cloudflare': {
    title: 'Cloudflare DNS',
    sections: [
      { title: 'Zones & Records', content: 'Manage zones and full DNS records (A/AAAA/CNAME/MX/TXT/etc.), TTL, and proxying.' },
      { title: 'Nameservers', content: 'Step-by-step nameserver-update guidance; zone status tracks when it goes active.' },
    ],
  },
  'integrations-webhooks': {
    title: 'Webhooks',
    sections: [
      { title: 'Create & Subscribe', content: 'Create webhooks to HTTPS endpoints and subscribe to events (Users, Billing, Services).' },
      { title: 'Secrets & History', content: 'Generate signing secrets (whsec_) for HMAC verification; view delivery attempts and test manually.' },
    ],
  },
};

// Ordered route → help-key resolver (most specific patterns first).
export const routeHelp = [
  ['/admin/infra/federation/contracts', 'infra-federation-contracts'],
  ['/admin/infra/federation', 'infra-federation'],
  ['/admin/infra/services', 'infra-services'],
  ['/admin/infra/resources', 'infra-resources'],
  ['/admin/infra/hardware', 'infra-hardware'],
  ['/admin/infra/network', 'infra-network'],
  ['/admin/infra/storage', 'infra-storage'],
  ['/admin/infra/traefik', 'infra-traefik'],
  ['/admin/billing/tiers', 'billing-tiers'],
  ['/admin/billing/apps', 'billing-apps'],
  ['/admin/billing/pricing', 'billing-pricing'],
  ['/admin/billing/rates', 'billing-rates'],
  ['/admin/billing/revenue', 'billing-revenue'],
  ['/admin/billing/credit-packs', 'billing-credit-packs'],
  ['/admin/billing/credits', 'billing-credits'],
  ['/admin/billing/inference-policy', 'billing-inference-policy'],
  ['/admin/billing/agent-pricing', 'billing-agent-pricing'],
  ['/admin/ai/models', 'ai-models'],
  ['/admin/ai/model-lists', 'ai-model-lists'],
  ['/admin/ai/colonel', 'ai-colonel'],
  ['/admin/ai/local-models', 'ai-local-models'],
  ['/admin/ai/gpu-services', 'ai-gpu-services'],
  ['/admin/ai/rag-services', 'ai-rag-services'],
  ['/admin/ai', 'ai-hub'],
  ['/admin/people/users', 'people-users'],
  ['/admin/people/organizations', 'people-organizations'],
  ['/admin/people/invite-codes', 'people-invite-codes'],
  ['/admin/people/authentication', 'people-authentication'],
  ['/admin/people/org-features', 'people-org-features'],
  ['/admin/monitoring/analytics', 'monitoring-analytics'],
  ['/admin/monitoring/logs', 'monitoring-logs'],
  ['/admin/monitoring/alerts', 'monitoring-alerts'],
  ['/admin/monitoring/audit', 'monitoring-audit'],
  ['/admin/monitoring/website-monitor', 'monitoring-website'],
  ['/admin/monitoring/tools', 'monitoring-tools'],
  ['/admin/integrations/credentials', 'integrations-credentials'],
  ['/admin/integrations/email', 'integrations-email'],
  ['/admin/integrations/cloudflare', 'integrations-cloudflare'],
  ['/admin/integrations/webhooks', 'integrations-webhooks'],
  ['/admin/platform/landing', 'platform-landing'],
  ['/admin/platform/white-label', 'platform-white-label'],
  ['/admin/platform/extensions', 'platform-extensions'],
  ['/admin/system/settings', 'system-settings'],
  ['/admin/system/security', 'system-security'],
  ['/admin/my-dashboard', 'user_dashboard'],
  ['/admin', 'dashboard'],
];

// Resolve the current pathname to a help key (longest/first match wins).
export function helpKeyForPath(pathname) {
  if (!pathname) return 'dashboard';
  for (const [prefix, key] of routeHelp) {
    if (pathname === prefix || pathname.startsWith(prefix + '/') || pathname.startsWith(prefix + '?')) {
      return key;
    }
  }
  // fall back to the first path segment area
  if (pathname.startsWith('/admin/billing')) return 'billing-rates';
  if (pathname.startsWith('/admin/ai')) return 'ai-hub';
  if (pathname.startsWith('/admin/infra')) return 'infra-services';
  if (pathname.startsWith('/admin/people')) return 'people-users';
  if (pathname.startsWith('/admin/monitoring')) return 'monitoring-analytics';
  if (pathname.startsWith('/admin/integrations')) return 'integrations-credentials';
  if (pathname.startsWith('/admin/platform')) return 'platform-landing';
  return 'dashboard';
}

// The Guide agent's Q&A knowledge base (seeded into its system prompt).
export const guideFaqs = [
  { area: 'billing', q: 'How do subscription tiers work?', a: 'Tiers are plans with a price, an included app set, and API-call limits. Manage them at /admin/billing/tiers; toggle which apps a tier includes via the sync (⟳) icon.' },
  { area: 'billing', q: 'What is the difference between metered and included models?', a: 'Included = bundled into a subscription (you absorb the cost). Metered = billed per-use from the org credit wallet. Set this per (app, model) at /admin/billing/inference-policy; default is metered.' },
  { area: 'billing', q: 'How does the credit wallet work?', a: 'One wallet spans free local models ($0) and paid cloud models (cost + markup). Credits come from a tier allocation or buyable packs (Stripe). Credit value defaults to $0.01.' },
  { area: 'billing', q: 'Subscription vs credits — are they the same?', a: 'No, they are orthogonal. Subscription = app access (+ some included inference). Credits = a metered inference wallet. A solo founder can need far more credits than an enterprise.' },
  { area: 'billing', q: 'What is markup / the rate book?', a: 'At /admin/billing/rates you set what you bill on top of provider cost (default markup % + a safety buffer), the credit value, and per-model overrides. Local models are bundled ($0) or metered flat.' },
  { area: 'billing', q: 'How do I add a buyable credit pack?', a: 'Go to /admin/billing/credit-packs → Add Package. Set credits, USD price, optional discount, and optional Stripe price/product IDs for live checkout.' },
  { area: 'billing', q: 'How is an agent invocation billed?', a: 'Each federated agent call is metered in units (set at /admin/billing/agent-pricing — a default plus per-agent overrides); the Lago plan decides what a unit costs.' },
  { area: 'ai', q: 'What is Colonel?', a: 'Colonel is the ops-center-native AI agent. It runs inside Ops-Center (no Brigade dependency) and can manage the server — including helping fix Brigade if Brigade is down. It can also delegate specialist work to Brigade agents.' },
  { area: 'ai', q: 'Federation models vs cloud models?', a: 'Federation models run on your own GPUs (free/bundled, fair-use throttled). Cloud models route through the LiteLLM gateway at provider cost + markup. Both appear in the Model Catalog (/admin/ai/models).' },
  { area: 'ai', q: 'What happens if a local GPU goes down mid-request?', a: 'The gateway alias (uc/chat-default) has an ordered failover chain: local GPU-A → local GPU-B → cheap cloud (DeepSeek V4 Flash) → premium cloud (OpenRouter). If a backend errors or times out, LiteLLM automatically retries the next rung — the caller gets a normal response and never sees the switch.' },
  { area: 'billing', q: 'Does my plan use cloud or local AI — and how am I billed?', a: 'Local-first: your requests run on our own GPUs (the bulk of every plan, fast and included). Third-party cloud is invisible insurance — used only when local is overwhelmed or down, and only within your plan’s allowance. Free tier is local-only (cloud is fail-closed); paid tiers include a bundled cloud allowance gated by a per-org budget.' },
  { area: 'ai', q: 'How do I control which models an app shows?', a: 'Use curated Model Lists (/admin/ai/model-lists) — per-app lists with tier-based visibility and ordering.' },
  { area: 'infra', q: 'Federation Settings vs Federation Contracts?', a: 'Settings (/admin/infra/federation) is node identity, branding, peers, and advertised services. Contracts (/admin/infra/federation/contracts) is the ENFORCED trust — trust_mode + publish/consume ACLs that actually gate traffic.' },
  { area: 'infra', q: 'How do I restrict a peer to certain services?', a: 'On the Contracts page set that peer to "scoped" and list the allowed service types in publish[]/consume[] (or specific grants like agents/sql-analyst). Changes apply within ~30s.' },
  { area: 'infra', q: 'What does the global default trust mode do?', a: 'It governs unknown peers that have no explicit contract. "isolated" = deny-by-default (the secure default); set it to scoped/full only if you trust unknown peers.' },
  { area: 'people', q: 'Tier vs role — what is the difference?', a: 'Tier (Trial/Starter/Pro/Enterprise) controls which apps a user can access and their quotas. Role (admin/moderator/developer/analyst/viewer) controls what they can do inside Ops-Center.' },
  { area: 'people', q: 'How do I give one org a premium app without changing its tier?', a: 'Use /admin/people/org-features — grant the specific app to that organization with an audited reason. It persists across tier changes; revoke to remove.' },
  { area: 'people', q: 'How does SSO work?', a: 'Keycloak (uchub realm) is the identity provider, with brokered Google/GitHub/Microsoft login. First social login auto-creates an account; accounts, passwords and MFA are managed in Keycloak.' },
  { area: 'people', q: 'What is an organization?', a: 'An organization is a tenant/workspace — a team that shares billing, a credit pool, and config. Users can belong to multiple orgs with different roles.' },
  { area: 'monitoring', q: 'Where do I configure integration credentials?', a: 'At /admin/integrations/credentials (Platform Settings) — Stripe/Lago/Keycloak/Cloudflare/Forgejo keys, each with a connection test. "Save & Restart" is needed for env-var changes.' },
  { area: 'monitoring', q: 'How do I see who changed what?', a: 'The Audit Log (/admin/monitoring/audit) is a filterable timeline of system/user/admin actions; expand an event for IP/request details, or export to CSV.' },
  { area: 'platform', q: 'Admin Dashboard vs My Dashboard?', a: 'Admin Dashboard (/admin) is infrastructure health for ops. My Dashboard (/admin/my-dashboard) is your personal credits, usage, and subscription.' },
  { area: 'platform', q: 'How do I white-label the platform?', a: 'Use /admin/platform/white-label (logo, colors, custom domain, hide attribution) and /admin/platform/landing (public landing theme and service cards).' },
];
