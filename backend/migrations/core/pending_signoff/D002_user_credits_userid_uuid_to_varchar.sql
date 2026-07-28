-- DANGEROUS / SIGN-OFF REQUIRED — user_credits.user_id  uuid -> varchar  (bigboy)
-- ===========================================================================
-- WHY: user_id is the Keycloak subject and is varchar EVERYWHERE else in the
-- suite (organization_members, credit_transactions, usage_events on BOTH nodes,
-- and user_credits on commander). bigboy's uuid user_id is the lone outlier;
-- older code paths (litellm_credit_system.py, email_notification_api.py) bind
-- plain strings with NO cast and would break on a uuid column. Converge bigboy
-- to varchar to match the suite + commander.
-- SAFETY: bigboy only; 1 row; NO incoming FK references. uuid->varchar has a
-- lossless implicit cast (uuid::text). UNIQUE(user_id) is preserved by the type
-- change. Idempotent-guarded. Back up first:
--   docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -t user_credits \
--     | gzip > /tmp/user_credits_$(date +%s).sql.gz
-- ===========================================================================
-- NOTE: bigboy's user_id is a uuid FK -> users.id. The uuid values ARE the
-- Keycloak subjects already used (as varchar) in organization_members /
-- credit_transactions / usage_events, so retyping to varchar preserves identity;
-- we drop the local-users FK (commander has none; users mirrors Keycloak and is
-- not joined by the hot-path credit code, which keys on user_id::text).
DO $$
DECLARE fk_name text;
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='user_credits' AND column_name='user_id') = 'character varying' THEN
        RAISE NOTICE 'user_credits.user_id already varchar — skipping';
        RETURN;
    END IF;
    SELECT con.conname INTO fk_name FROM pg_constraint con
      JOIN unnest(con.conkey) k(attnum) ON true
      JOIN pg_attribute a ON a.attrelid=con.conrelid AND a.attnum=k.attnum
      WHERE con.contype='f' AND con.conrelid='user_credits'::regclass AND a.attname='user_id';
    IF fk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE user_credits DROP CONSTRAINT ' || quote_ident(fk_name);
    END IF;
    ALTER TABLE user_credits ALTER COLUMN user_id TYPE varchar(255) USING user_id::text;
    RAISE NOTICE 'user_credits.user_id converted uuid -> varchar (dropped FK %)', fk_name;
END $$;
