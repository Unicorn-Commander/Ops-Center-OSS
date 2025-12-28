# Database Migrations

This directory contains SQL migrations for the UC-Cloud Ops-Center database.

## Migration Files

### Migration 001: Initial LLM Tables
- **File**: `001_create_llm_tables.sql`
- **Status**: ✅ Applied (October 23, 2025)
- **Description**: Creates initial LLM infrastructure tables
- **Tables Created**:
  - `llm_providers` - LLM provider definitions
  - `llm_models` - Individual model configurations
  - `user_api_keys` - User BYOK storage
  - `llm_routing_rules` - Power level routing
  - `llm_usage_logs` - Usage tracking

### Migration 002: System API Key Storage
- **File**: `002_add_system_api_keys.sql`
- **Rollback**: `002_add_system_api_keys_rollback.sql`
- **Status**: ⏳ Ready to apply
- **Description**: Adds system-level API key storage to `llm_providers` table
- **Changes**:
  - Adds `encrypted_api_key` column (TEXT)
  - Adds `api_key_source` column (VARCHAR(50))
  - Adds `api_key_updated_at` column (TIMESTAMP)
  - Adds `api_key_last_tested` column (TIMESTAMP)
  - Adds `api_key_test_status` column (VARCHAR(20))
  - Creates 2 indexes for performance
  - Adds column documentation comments

## Migration Tools

### `run_migration.py`
Python script for applying/rolling back migrations with idempotency checks.

**Usage**:
```bash
# Check status
python3 /app/run_migration.py --check

# Apply migration
python3 /app/run_migration.py

# Rollback migration
python3 /app/run_migration.py --rollback

# Force re-apply
python3 /app/run_migration.py --force
```

### `test_migration.sh`
Bash script for verifying migration success (9 test suites, 18+ tests).

**Usage**:
```bash
bash /app/test_migration.sh
```

## Quick Commands

### Inside Container

```bash
# Check migration status
docker exec ops-center-direct python3 /app/run_migration.py --check

# Apply migration 002
docker exec ops-center-direct python3 /app/run_migration.py

# Test migration
docker exec ops-center-direct bash /app/test_migration.sh

# Rollback if needed
docker exec ops-center-direct python3 /app/run_migration.py --rollback
```

### Direct PostgreSQL

```bash
# Check if columns exist
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT column_name FROM information_schema.columns
WHERE table_name='llm_providers'
AND column_name IN ('encrypted_api_key', 'api_key_source');
"

# View full schema
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_providers"

# Apply migration manually
docker cp migrations/002_add_system_api_keys.sql unicorn-postgresql:/tmp/
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /tmp/002_add_system_api_keys.sql
```

## Documentation

- **Schema Documentation**: `../SCHEMA.md`
- **Migration Summary**: `../MIGRATION_002_SUMMARY.md`
- **Main UC-Cloud Docs**: `/home/muut/Production/UC-Cloud/CLAUDE.md`

## Best Practices

1. **Always backup before migrating**:
   ```bash
   docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > backup_$(date +%Y%m%d).sql
   ```

2. **Test on development first**: Never apply to production without testing

3. **Use the Python script**: It has built-in safety checks and idempotency

4. **Verify after migration**: Always run `test_migration.sh` to confirm success

5. **Document changes**: Update `SCHEMA.md` when schema changes

## Migration History

| Migration | Date Applied | Description |
|-----------|--------------|-------------|
| 001 | 2025-10-23 | Initial LLM infrastructure tables |
| 002 | Pending | System API key storage |

## Rollback Strategy

All migrations include rollback scripts:
- `001_*.sql` → (not applicable, initial schema)
- `002_add_system_api_keys.sql` → `002_add_system_api_keys_rollback.sql`

Always export critical data before rollback:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT provider_slug, encrypted_api_key
FROM llm_providers
WHERE encrypted_api_key IS NOT NULL;
" > system_keys_backup.txt
```

## Troubleshooting

### Migration fails with "relation does not exist"
**Solution**: Ensure migration 001 was applied first
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT tablename FROM pg_tables WHERE tablename LIKE 'llm_%';
"
```

### Column already exists
**Solution**: Use `--force` to re-apply or rollback first
```bash
python3 run_migration.py --rollback
python3 run_migration.py
```

### Connection refused
**Solution**: Check PostgreSQL container is running
```bash
docker ps | grep postgresql
docker logs unicorn-postgresql
```

## Contact

For questions or issues with migrations, see:
- **Ops-Center Docs**: `/services/ops-center/CLAUDE.md`
- **UC-Cloud Main**: `/CLAUDE.md`
