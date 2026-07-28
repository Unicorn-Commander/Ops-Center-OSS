-- core parity 0003 — organizations / organization_members tenancy union (Phase B)
-- server.py reads organizations.subscription_tier unconditionally (would 500 on a
-- node lacking it); my_apps_api ORDER BYs organization_members.is_default and
-- org_api INSERTs it. The two nodes split these columns across the two tables, so
-- ensure BOTH columns exist on BOTH tables on BOTH nodes. Defaults match
-- commander's semantics so existing rows backfill cleanly.
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT false;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_service_account BOOLEAN DEFAULT false;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(64) DEFAULT 'managed';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tier_id INTEGER;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS slug VARCHAR(255);

ALTER TABLE organization_members ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT false;
