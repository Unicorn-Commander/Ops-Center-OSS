-- DANGEROUS / SIGN-OFF REQUIRED — credit_packages.id  integer -> uuid  (commander)
-- ===========================================================================
-- WHY: suite-wide PK convention is uuid; bigboy is already uuid. The admin
-- credit-packs CRUD binds package_id as a STRING with no cast, so UPDATE/DELETE
-- `WHERE id = $1` works against a uuid column (bigboy) but asyncpg rejects a
-- string against commander's int4 column -> the admin edit/delete path is a
-- latent 500 on commander TODAY. Converging commander to uuid fixes it.
-- SAFETY: 4 rows; NO incoming FK references (verified pg_constraint both nodes);
-- ids are not referenced outside the admin session. Run inside a txn; back up
-- credit_packages (schema+data) on commander FIRST. Idempotent-guarded: no-op if
-- id is already uuid.
-- BACKUP (run on the node before applying):
--   docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db -t credit_packages \
--     | gzip > /tmp/credit_packages_$(date +%s).sql.gz
-- ===========================================================================
DO $$
DECLARE pk_name text;
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='credit_packages' AND column_name='id') = 'uuid' THEN
        RAISE NOTICE 'credit_packages.id already uuid — skipping';
        RETURN;
    END IF;

    -- new uuid column, populate every row
    ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS id_uuid uuid DEFAULT uuid_generate_v4();
    UPDATE credit_packages SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL;

    -- drop the existing integer PK (name discovered dynamically), then the int id
    SELECT conname INTO pk_name FROM pg_constraint
      WHERE conrelid='credit_packages'::regclass AND contype='p';
    IF pk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE credit_packages DROP CONSTRAINT ' || quote_ident(pk_name);
    END IF;
    ALTER TABLE credit_packages DROP COLUMN id;          -- auto-drops the owned id sequence

    -- promote id_uuid -> id, make it the uuid PK with the suite-standard default
    ALTER TABLE credit_packages RENAME COLUMN id_uuid TO id;
    ALTER TABLE credit_packages ALTER COLUMN id SET DEFAULT uuid_generate_v4();
    ALTER TABLE credit_packages ALTER COLUMN id SET NOT NULL;
    ALTER TABLE credit_packages ADD PRIMARY KEY (id);
    RAISE NOTICE 'credit_packages.id converted integer -> uuid';
END $$;
