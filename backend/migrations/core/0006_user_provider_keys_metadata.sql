-- core parity 0006 — user_provider_keys.metadata (Phase B)
-- byok_api/byok_manager write a metadata JSONB column (absent on bigboy). Add it.
-- Does NOT touch user_id type — the uuid->varchar change is dangerous
-- (core/pending_signoff/). 0 rows on bigboy, 4 on commander.
ALTER TABLE user_provider_keys ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
