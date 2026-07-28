-- P-00107: Ops apps catalog + Suite entitlement (readiness ladder, 2026-06-24).
--
-- Registers every retail *-Ops app as an add_on with feature_key + metadata, and grants
-- the full app set to the Suite tiers (byok, managed) + vip_founder. The "App" $15 tier's
-- meeting+contact grant is seeded by self_service_storefront.sql and left intact here.
--
-- Readiness ladder (per Aaron, 2026-06-24):
--   meeting-ops    flagship, SaaS now        -> active, public, featured
--   contact-ops    companion (bundled w/ Meeting in $15 App tier)   -> active, public
--   brand-ops      done                      -> active, public
--   project-ops    standalone, complete      -> active, public
--   customer-ops   standalone                -> active, public
--   accounting-ops complete, UI in testing   -> active, public, BETA (no standalone price yet)
--   tax-ops        complete, UI in testing   -> active, public, BETA (no standalone price yet)
--   email-ops      Suite-only until Gmail OAuth/CASA clears  -> active, public, BETA
--   brigade        backend/admin tooling     -> registered, NOT public (admin-grant only)
--
-- NOTE: standalone à-la-carte purchase requires base_price + a Stripe price on the add_on
--       row. Those are intentionally left at 0.00 / NULL here: at launch every app except
--       Meeting+Contact (sold via the $15 App tier) is reachable only through the Suite.
--       Flip an app to standalone later = set its base_price + Stripe price; no code change.
--       launch_url values follow the existing magicunicorn.dev convention and can be retuned.

BEGIN;

-- ── 1. Catalog registrations (idempotent upsert by slug) ───────────────────────────────
INSERT INTO add_ons (
    name, slug, description, long_description, category, feature_key,
    launch_url, icon_url, base_price, billing_type, is_active, is_featured,
    is_public, access_type, min_org_role, sort_order, features
) VALUES
  ('Meeting-Ops', 'meeting-ops',
   'AI meeting intelligence — record, transcribe, summarize, and action your meetings',
   'Meeting-Ops captures meetings end to end: live transcription, speaker diarization, AI summaries, and tracked action items, with calendar and contact context. The flagship Unicorn Commander app.',
   'productivity', 'meeting_ops_access',
   'https://meetingops.magicunicorn.dev', '/logos/meeting-ops.png',
   0.00, 'monthly', TRUE, TRUE, TRUE, 'tier_included', 'member', 10,
   '{"transcription": "Live transcription & diarization", "summaries": "AI meeting summaries", "action_items": "Tracked action items", "calendar": "Calendar integration", "sso": "Keycloak SSO"}'::jsonb),

  ('Contact-Ops', 'contact-ops',
   'Relationship and contact operations workspace',
   'Contact-Ops organizes contacts, relationship context, follow-ups, and communication workflows. Pairs with Meeting-Ops in the App tier.',
   'productivity', 'contact_ops_access',
   'https://contacts.magicunicorn.dev', '/logos/contact-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 11,
   '{"contacts": "Contact and relationship management", "follow_up": "Follow-up workflows", "sso": "Keycloak SSO"}'::jsonb),

  ('Brand-Ops', 'brand-ops',
   'Brand identity and asset operations',
   'Brand-Ops manages brand identity, asset libraries, and creative consistency across the organization.',
   'productivity', 'brand_ops_access',
   'https://brand.magicunicorn.dev', '/logos/brand-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 12,
   '{"assets": "Brand asset library", "guidelines": "Brand guidelines", "sso": "Keycloak SSO"}'::jsonb),

  ('Project-Ops', 'project-ops',
   'Project, task, and time operations',
   'Project-Ops runs projects end to end: tasks, time tracking, approvals, capacity, and profitability reporting, with RBAC matching the rest of the suite.',
   'productivity', 'project_ops_access',
   'https://projects.magicunicorn.dev', '/logos/project-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 13,
   '{"tasks": "Tasks & projects", "time": "Time tracking & approvals", "reporting": "Profitability & utilization reporting", "sso": "Keycloak SSO"}'::jsonb),

  ('Customer-Ops', 'customer-ops',
   'Customer relationship and lifecycle operations',
   'Customer-Ops manages the customer lifecycle: accounts, engagements, and federated customer actors across the platform.',
   'productivity', 'customer_ops_access',
   'https://customers.magicunicorn.dev', '/logos/customer-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 14,
   '{"accounts": "Customer accounts", "lifecycle": "Lifecycle management", "sso": "Keycloak SSO"}'::jsonb),

  ('Accounting-Ops', 'accounting-ops',
   'Living Ledger — accounting and financial operations',
   'Accounting-Ops (Living Ledger) provides real-time financial dashboards, ledger lineage, and agent-assisted bookkeeping. Functionally complete; human interface in beta testing.',
   'finance', 'accounting_ops_access',
   'https://accounting.magicunicorn.dev', '/logos/accounting-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 15,
   '{"status": "beta", "ledger": "Living ledger dashboard", "lineage": "Transaction lineage", "agents": "Agent-assisted bookkeeping", "sso": "Keycloak SSO"}'::jsonb),

  ('Tax-Planning-Ops', 'tax-ops',
   'Tax planning and compliance operations',
   'Tax-Planning-Ops handles tax planning, scenario modeling, and compliance workflows. Functionally complete; human interface in beta testing.',
   'finance', 'tax_ops_access',
   'https://tax.magicunicorn.dev', '/logos/tax-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 16,
   '{"status": "beta", "planning": "Tax planning", "scenarios": "Scenario modeling", "compliance": "Compliance workflows", "sso": "Keycloak SSO"}'::jsonb),

  ('Email-Ops', 'email-ops',
   'Agent email command center + mailbox operations',
   'Email-Ops runs mailbox cleanup and an agent email command center with autonomy controls and audit. Suite-only until public Gmail OAuth verification (CASA) clears.',
   'productivity', 'email_ops_access',
   'https://email-ops.magicunicorn.dev', '/logos/email-ops.png',
   0.00, 'monthly', TRUE, FALSE, TRUE, 'tier_included', 'member', 17,
   '{"status": "beta", "cleaner": "Mailbox cleanup", "agent_inbox": "Agent email command center", "autonomy": "Per-agent autonomy controls", "sso": "Keycloak SSO"}'::jsonb),

  ('Brigade', 'brigade',
   'AI agent factory and orchestration (admin)',
   'Unicorn Brigade is the agent factory and orchestration plane — backend/administrator tooling, not a retail end-user app.',
   'tools', 'brigade_access',
   'https://brigade.unicorncommander.ai', '/logos/brigade-logo.png',
   0.00, 'monthly', TRUE, FALSE, FALSE, 'tier_included', 'admin', 90,
   '{"agents": "Agent factory", "orchestration": "Multi-agent orchestration", "admin_only": "Administrator tooling"}'::jsonb)
ON CONFLICT (slug) DO UPDATE SET
    name             = EXCLUDED.name,
    description      = EXCLUDED.description,
    long_description = EXCLUDED.long_description,
    category         = EXCLUDED.category,
    feature_key      = EXCLUDED.feature_key,
    launch_url       = EXCLUDED.launch_url,
    icon_url         = EXCLUDED.icon_url,
    billing_type     = EXCLUDED.billing_type,
    is_active        = EXCLUDED.is_active,
    is_featured      = EXCLUDED.is_featured,
    is_public        = EXCLUDED.is_public,
    access_type      = EXCLUDED.access_type,
    min_org_role     = EXCLUDED.min_org_role,
    sort_order       = EXCLUDED.sort_order,
    features         = EXCLUDED.features;

-- ── 2. Suite = everything. Grant the full retail app set to byok, managed, vip_founder. ──
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, f.feature_key, 'true', TRUE
FROM subscription_tiers st
CROSS JOIN (VALUES
    ('meeting_ops_access'),
    ('contact_ops_access'),
    ('brand_ops_access'),
    ('project_ops_access'),
    ('customer_ops_access'),
    ('accounting_ops_access'),
    ('tax_ops_access'),
    ('email_ops_access')
) AS f(feature_key)
WHERE st.tier_code IN ('byok', 'managed', 'vip_founder')
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;
