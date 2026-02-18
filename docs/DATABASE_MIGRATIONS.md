# Database Migrations Guide - Ops-Center

**Last Updated**: October 22, 2025
**Version**: 1.0.0
**Status**: Production Ready

---

## Overview

Ops-Center uses **Alembic** for database schema migrations. This allows safe, reversible, and trackable changes to the PostgreSQL database schema.

**Key Benefits**:
- ✅ **Reversible migrations** - Easily rollback changes
- ✅ **Version control** - Track schema changes in Git
- ✅ **Auto-generation** - Generate migrations from SQLAlchemy models
- ✅ **Automatic backups** - Backup before every migration
- ✅ **Team collaboration** - Share migrations across developers

---

## Quick Reference

### Common Commands

```bash
# Check migration status
./scripts/database/migration_status.sh

# Create a new migration
./scripts/database/create_migration.sh "description of changes"

# Run migrations (with backup)
./scripts/database/run_migrations.sh

# Run dry-run (preview SQL)
./scripts/database/run_migrations.sh --dry-run

# Rollback last migration
./scripts/database/rollback_migration.sh

# Rollback multiple migrations
./scripts/database/rollback_migration.sh 3

# Manual backup
./scripts/database/backup_database.sh

# Restore from backup
./scripts/database/restore_database.sh /path/to/backup.sql
```

---

## Directory Structure

```
services/ops-center/
├── alembic/                    # Alembic migration system
│   ├── env.py                 # Environment configuration
│   ├── script.py.mako         # Migration template
│   ├── README                 # Alembic documentation
│   └── versions/              # Migration files
│       ├── 20251022_initial_schema_abc123.py
│       ├── 20251023_add_feature_def456.py
│       └── ...
├── alembic.ini                # Alembic configuration
├── backend/
│   └── database/              # Database models
│       ├── __init__.py
│       └── models.py          # SQLAlchemy models
└── scripts/
    └── database/              # Migration scripts
        ├── backup_database.sh
        ├── restore_database.sh
        ├── create_migration.sh
        ├── run_migrations.sh
        ├── rollback_migration.sh
        └── migration_status.sh
```

---

## Database Models

All database tables are defined as SQLAlchemy models in:
**`backend/database/models.py`**

### Current Tables

1. **Organizations**
   - `organizations` - Organization records
   - `organization_members` - User-organization relationships
   - `organization_invitations` - Pending invitations

2. **Authentication**
   - `api_keys` - User API keys

3. **Audit**
   - `audit_logs` - System-wide audit trail

4. **Cloudflare Integration** (Epic 1.6)
   - `cloudflare_zones` - DNS zones
   - `cloudflare_dns_records` - DNS records
   - `cloudflare_firewall_rules` - Firewall rules

5. **Domain Migration** (Epic 1.7)
   - `migration_jobs` - Domain migration tracking
   - `namecheap_domains` - Namecheap domain registrations
   - `cloudflare_domains` - Cloudflare domain registrations

---

## Migration Workflow

### 1. Creating a New Migration

When you add/modify a database table in `backend/database/models.py`, create a migration:

```bash
# Step 1: Edit models.py
vim backend/database/models.py

# Step 2: Create migration (auto-generates from models)
./scripts/database/create_migration.sh "add user preferences table"

# Step 3: Review the generated migration file
# Check: alembic/versions/<timestamp>_add_user_preferences_table.py

# Step 4: Test with dry-run first
./scripts/database/run_migrations.sh --dry-run

# Step 5: Apply the migration
./scripts/database/run_migrations.sh
```

### 2. Running Migrations

Migrations are applied automatically with backup:

```bash
# Run all pending migrations
./scripts/database/run_migrations.sh

# What happens:
# 1. Creates backup in /opt/backups/database/
# 2. Shows pending migrations
# 3. Asks for confirmation
# 4. Applies migrations
# 5. Verifies success
```

**Automatic Backup**: Every migration run creates a timestamped backup:
```
/opt/backups/database/unicorn_db_20251022_143025.sql
```

### 3. Rolling Back Migrations

If something goes wrong, rollback:

```bash
# Rollback last migration
./scripts/database/rollback_migration.sh

# Rollback multiple migrations
./scripts/database/rollback_migration.sh 3

# What happens:
# 1. Creates backup before rollback
# 2. Shows migration history
# 3. Asks for confirmation
# 4. Reverts migrations
# 5. Verifies success
```

### 4. Checking Migration Status

```bash
# Quick status
./scripts/database/migration_status.sh

# Verbose history
./scripts/database/migration_status.sh --verbose

# Output shows:
# - Current migration version
# - Latest available version
# - Pending migrations
# - Database size and table count
```

---

## Migration File Structure

Example migration file:

```python
# alembic/versions/20251022_1430_abc123_add_user_preferences.py

"""add user preferences table

Revision ID: abc123
Revises: def456
Create Date: 2025-10-22 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration - create table"""
    op.create_table('user_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('theme', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])


def downgrade() -> None:
    """Revert migration - drop table"""
    op.drop_index('ix_user_preferences_user_id', 'user_preferences')
    op.drop_table('user_preferences')
```

---

## Backup System

### Automatic Backups

**When backups are created**:
1. Before running migrations (`run_migrations.sh`)
2. Before rolling back migrations (`rollback_migration.sh`)
3. Before restoring from backup (`restore_database.sh`)
4. Manual backup (`backup_database.sh`)

**Backup location**:
```
/opt/backups/database/
  ├── unicorn_db_20251022_143025.sql
  ├── unicorn_db_20251022_143025.metadata.json
  ├── unicorn_db_20251022_150000.sql
  └── ...
```

**Backup retention**: 7 days (configurable in `backup_database.sh`)

### Manual Backup

```bash
# Create backup
./scripts/database/backup_database.sh

# Output:
# - Backup file: /opt/backups/database/unicorn_db_TIMESTAMP.sql
# - Metadata: /opt/backups/database/unicorn_db_TIMESTAMP.metadata.json
# - Cleanup: Removes backups older than 7 days
```

### Restoring from Backup

```bash
# List available backups
./scripts/database/restore_database.sh

# Restore specific backup
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_20251022_143025.sql

# Safety features:
# 1. Creates backup of current database first
# 2. Asks for confirmation
# 3. Verifies restoration
```

---

## Best Practices

### DO ✅

1. **Always review auto-generated migrations** - Alembic doesn't catch everything
2. **Test in development first** - Never run untested migrations in production
3. **Use descriptive migration names** - "add user email verification" not "update users"
4. **Run dry-run before applying** - Preview SQL before executing
5. **Keep migrations small and focused** - One feature per migration
6. **Commit migrations to Git** - Version control is essential
7. **Document complex migrations** - Add comments in migration file
8. **Test rollback works** - Verify `downgrade()` function is correct

### DON'T ❌

1. **Don't edit applied migrations** - Create a new migration instead
2. **Don't delete migration files** - Breaks migration history
3. **Don't skip backups** - Always backup before migrations
4. **Don't ignore warnings** - Review and fix before applying
5. **Don't modify alembic_version table manually** - Use Alembic commands
6. **Don't run migrations on production without testing** - Test first!
7. **Don't mix manual SQL with Alembic** - Use migrations for schema changes

---

## Advanced Operations

### Creating Empty Migration

For data migrations or manual SQL:

```bash
# Create empty migration
docker exec ops-center-direct bash -c "cd /app && alembic revision -m 'migrate user data'"

# Edit the migration file manually
vim alembic/versions/<timestamp>_migrate_user_data.py
```

### Branching and Merging

For complex scenarios with parallel development:

```bash
# Create branch
alembic revision --branch-label feature_x -m "feature X tables"

# Merge branches
alembic merge -m "merge branches" head1 head2
```

### SQL-Only Migrations

Generate SQL without applying:

```bash
# Generate SQL for all pending migrations
docker exec ops-center-direct bash -c "cd /app && alembic upgrade head --sql > migration.sql"

# Review and apply manually if needed
```

### Stamping Database

Mark database at specific version without running migrations:

```bash
# Stamp database as current version (for initial setup)
docker exec ops-center-direct bash -c "cd /app && alembic stamp head"

# Stamp at specific version
docker exec ops-center-direct bash -c "cd /app && alembic stamp abc123"
```

---

## Troubleshooting

### Migration Fails

**Problem**: Migration fails with error

**Solution**:
```bash
# 1. Check the error message
docker logs ops-center-direct --tail 50

# 2. Review the migration file
cat alembic/versions/<failed_migration>.py

# 3. Restore from backup
./scripts/database/restore_database.sh /opt/backups/database/unicorn_db_LATEST.sql

# 4. Fix the migration file
vim alembic/versions/<failed_migration>.py

# 5. Try again
./scripts/database/run_migrations.sh
```

### Alembic Detects Incorrect Changes

**Problem**: `alembic revision --autogenerate` creates unwanted changes

**Solution**:
```bash
# 1. Review what changed in models.py
git diff backend/database/models.py

# 2. Check SQLAlchemy import issues
# - Ensure all models are imported in __init__.py
# - Verify metadata is correctly set

# 3. Delete incorrect migration
rm alembic/versions/<incorrect_migration>.py

# 4. Recreate migration
./scripts/database/create_migration.sh "correct description"
```

### Database Out of Sync

**Problem**: Alembic thinks database is at version X, but it's not

**Solution**:
```bash
# Option 1: Stamp database at correct version
docker exec ops-center-direct bash -c "cd /app && alembic stamp <correct_version>"

# Option 2: Reset and re-apply
# 1. Backup database
./scripts/database/backup_database.sh

# 2. Drop alembic_version table
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "DROP TABLE IF EXISTS alembic_version;"

# 3. Re-stamp at head
docker exec ops-center-direct bash -c "cd /app && alembic stamp head"
```

### Container Not Running

**Problem**: Scripts can't connect to containers

**Solution**:
```bash
# Check container status
docker ps | grep ops-center
docker ps | grep postgresql

# Start containers
docker start ops-center-direct
docker start unicorn-postgresql

# Verify
docker ps
```

---

## Environment Variables

Alembic uses these environment variables (configured in container):

```bash
# PostgreSQL connection
POSTGRES_HOST=unicorn-postgresql
POSTGRES_PORT=5432
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=unicorn
POSTGRES_DB=unicorn_db

# Or full URL
SQLALCHEMY_DATABASE_URL=postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db
```

---

## Production Deployment

### Initial Setup (First Time)

```bash
# 1. Install Alembic dependencies
docker exec ops-center-direct pip install alembic sqlalchemy asyncpg psycopg2-binary

# 2. Create initial migration (captures current schema)
docker exec ops-center-direct bash -c "cd /app && alembic revision --autogenerate -m 'initial schema'"

# 3. Mark database as stamped (don't run initial migration)
docker exec ops-center-direct bash -c "cd /app && alembic stamp head"

# 4. Verify
./scripts/database/migration_status.sh
```

### Regular Migrations

```bash
# 1. Pull latest code
git pull origin main

# 2. Check for new migrations
./scripts/database/migration_status.sh

# 3. Run dry-run first
./scripts/database/run_migrations.sh --dry-run

# 4. Apply migrations
./scripts/database/run_migrations.sh

# 5. Verify application works
curl http://localhost:8084/api/v1/system/status
```

---

## Testing Migrations

### Development Testing

```bash
# 1. Create test migration
./scripts/database/create_migration.sh "add test table"

# 2. Review migration
cat alembic/versions/<latest_migration>.py

# 3. Test upgrade
./scripts/database/run_migrations.sh --dry-run
./scripts/database/run_migrations.sh

# 4. Verify table exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# 5. Test rollback
./scripts/database/rollback_migration.sh

# 6. Verify table removed
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# 7. Re-apply
./scripts/database/run_migrations.sh
```

---

## Support

**Documentation**:
- This guide: `docs/DATABASE_MIGRATIONS.md`
- Migration workflow: `docs/MIGRATION_WORKFLOW.md`
- Rollback procedure: `docs/ROLLBACK_PROCEDURE.md`
- Backup/restore: `docs/BACKUP_RESTORE.md`

**Alembic Documentation**: https://alembic.sqlalchemy.org/

**Contact**: See project README for support channels

---

**Remember**: Always backup before migrations, test in development first, and review auto-generated migrations carefully!
