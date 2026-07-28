-- Federation Trust Modes — Phase 1: schema migration
--
-- Adds per-peer trust modes (full, scoped, consumer, publisher, isolated),
-- per-service publish/consume ACLs, capability token slot, and authority
-- tracking. Defaults preserve current full-mesh behavior — no-op for any
-- existing federation_peers row.
--
-- Spec: Unicorn-Ecosystem/FEDERATION_TRUST_MODES.md
-- Idempotent: safe to re-run.

BEGIN;

-- 1. New columns on federation_peers
ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS trust_mode VARCHAR(50) NOT NULL DEFAULT 'full';

ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS publish JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS consume JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS capability_token TEXT;

ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS authority_for JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE federation_peers
    ADD COLUMN IF NOT EXISTS consumer_of JSONB NOT NULL DEFAULT '[]'::jsonb;

-- Backfill any pre-existing rows that might have NULL (defensive — should be
-- impossible given NOT NULL DEFAULT, but ALTER on existing data is safer
-- this way).
UPDATE federation_peers SET trust_mode = 'full' WHERE trust_mode IS NULL;
UPDATE federation_peers SET publish = '[]'::jsonb WHERE publish IS NULL;
UPDATE federation_peers SET consume = '[]'::jsonb WHERE consume IS NULL;
UPDATE federation_peers SET authority_for = '[]'::jsonb WHERE authority_for IS NULL;
UPDATE federation_peers SET consumer_of = '[]'::jsonb WHERE consumer_of IS NULL;

-- Constraint: trust_mode must be one of the documented values.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'federation_peers_trust_mode_check'
    ) THEN
        ALTER TABLE federation_peers
            ADD CONSTRAINT federation_peers_trust_mode_check
            CHECK (trust_mode IN ('full', 'scoped', 'consumer', 'publisher', 'isolated'));
    END IF;
END $$;

-- 2. federation_authorities table — tracks who owns each authoritative
-- resource type. resource_type is free-form for now (e.g. 'users',
-- 'billing', 'model_catalog', 'federation_keys').
CREATE TABLE IF NOT EXISTS federation_authorities (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(100) NOT NULL,
    node_id VARCHAR(36) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    since TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT federation_authorities_node_id_fkey
        FOREIGN KEY (node_id)
        REFERENCES federation_nodes(id)
        ON DELETE CASCADE,
    CONSTRAINT federation_authorities_unique_primary
        UNIQUE (resource_type, is_primary) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_federation_authorities_resource
    ON federation_authorities (resource_type) WHERE is_primary;

CREATE INDEX IF NOT EXISTS idx_federation_authorities_node
    ON federation_authorities (node_id);

-- Helpful comments
COMMENT ON COLUMN federation_peers.trust_mode IS
    'Per-peer trust mode: full | scoped | consumer | publisher | isolated. See FEDERATION_TRUST_MODES.md.';
COMMENT ON COLUMN federation_peers.publish IS
    'JSON array of service-type strings this peer is allowed to SEE on us. Only consulted in scoped mode.';
COMMENT ON COLUMN federation_peers.consume IS
    'JSON array of service-type strings this peer is allowed to CALL on us. Only consulted in scoped mode.';
COMMENT ON COLUMN federation_peers.capability_token IS
    'JWT issued by an authoritative node attesting this peer-pair config. Optional in Phase 1.';
COMMENT ON COLUMN federation_peers.authority_for IS
    'JSON array of resource_type strings this peer claims authority over (e.g. ["users","billing"]).';
COMMENT ON COLUMN federation_peers.consumer_of IS
    'JSON array of "resource_type@authoritative_node_id" strings, e.g. ["users@uc-commander"].';
COMMENT ON TABLE federation_authorities IS
    'Local view of which node is authoritative for each resource type. Editable from admin UI in later phase.';

COMMIT;
