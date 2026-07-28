-- core parity 0007 — usage_events metering column union (Phase B)
-- Two metering writers disagree on shape: usage_metering.py inserts
-- (user_id, service, model, tokens_used, cost, is_free, metadata) and OMITS
-- event_type; commander's metering path writes event_type/provider/total_cost/
-- provider_cost/platform_markup/is_free_tier and has event_type NOT NULL with no
-- default — so the first writer 500s on commander. Fix = union the columns AND
-- relax event_type to nullable + DEFAULT 'usage', so BOTH writers work on BOTH
-- nodes. 226 rows bigboy / 912 commander; all ADDs are nullable/defaulted =
-- metadata-only, no rewrite. Existing rows are untouched.
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS org_id UUID;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS is_free BOOLEAN DEFAULT false;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(64) DEFAULT 'usage';
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS provider VARCHAR(64);
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS power_level VARCHAR(32);
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS success BOOLEAN DEFAULT true;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS total_cost NUMERIC;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS provider_cost NUMERIC DEFAULT 0;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS platform_markup NUMERIC DEFAULT 0;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS is_free_tier BOOLEAN DEFAULT false;
-- make omitted-event_type inserts (usage_metering.py) succeed on commander:
ALTER TABLE usage_events ALTER COLUMN event_type SET DEFAULT 'usage';
ALTER TABLE usage_events ALTER COLUMN event_type DROP NOT NULL;
