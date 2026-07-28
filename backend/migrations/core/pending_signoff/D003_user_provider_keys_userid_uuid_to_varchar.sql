-- DANGEROUS / SIGN-OFF REQUIRED — user_provider_keys.user_id  uuid -> varchar  (bigboy)
-- ===========================================================================
-- WHY: same as D002 — byok_manager/byok_api bind user_id as a plain string (and
-- even branch on len(user_id)<32 / startswith('org_')); the suite + commander use
-- varchar. bigboy's uuid is the outlier.
-- SAFETY: bigboy only; 0 rows (trivially safe); NO incoming FK references. The
-- composite UNIQUE(user_id, provider) is preserved by the in-place type change.
-- Idempotent-guarded. Back up first (table is empty but for symmetry):
--   docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -t user_provider_keys \
--     | gzip > /tmp/user_provider_keys_$(date +%s).sql.gz
-- ===========================================================================
-- NOTE: like D002, drops the local-users FK (bigboy-only; commander has none) and
-- retypes to the suite-standard varchar Keycloak subject. 0 rows -> trivially safe.
DO $$
DECLARE fk_name text;
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='user_provider_keys' AND column_name='user_id') = 'character varying' THEN
        RAISE NOTICE 'user_provider_keys.user_id already varchar — skipping';
        RETURN;
    END IF;
    SELECT con.conname INTO fk_name FROM pg_constraint con
      JOIN unnest(con.conkey) k(attnum) ON true
      JOIN pg_attribute a ON a.attrelid=con.conrelid AND a.attnum=k.attnum
      WHERE con.contype='f' AND con.conrelid='user_provider_keys'::regclass AND a.attname='user_id';
    IF fk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE user_provider_keys DROP CONSTRAINT ' || quote_ident(fk_name);
    END IF;
    ALTER TABLE user_provider_keys ALTER COLUMN user_id TYPE varchar(255) USING user_id::text;
    RAISE NOTICE 'user_provider_keys.user_id converted uuid -> varchar (dropped FK %)', fk_name;
END $$;
