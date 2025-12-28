# Migration Workflow - Step-by-Step Guide

**Last Updated**: October 22, 2025

---

## Scenario 1: Adding a New Feature (New Table)

### Example: Add user preferences table

**Step 1: Update Models**

Edit `backend/database/models.py`:

```python
class UserPreference(Base):
    """User preferences table"""
    __tablename__ = 'user_preferences'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    theme = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 2: Create Migration**

```bash
./scripts/database/create_migration.sh "add user preferences table"
```

**Step 3: Review Generated Migration**

```bash
cat alembic/versions/<timestamp>_add_user_preferences_table.py
```

Check:
- ✅ Table name correct
- ✅ All columns included
- ✅ Indexes created
- ✅ `downgrade()` properly removes table

**Step 4: Test with Dry-Run**

```bash
./scripts/database/run_migrations.sh --dry-run
```

Review SQL output to ensure it matches expectations.

**Step 5: Apply Migration**

```bash
./scripts/database/run_migrations.sh
```

Automatic backup created, migration applied.

**Step 6: Verify**

```bash
# Check migration status
./scripts/database/migration_status.sh

# Verify table exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d user_preferences"

# Test application
curl http://localhost:8084/api/v1/system/status
```

**Step 7: Commit to Git**

```bash
git add backend/database/models.py
git add alembic/versions/<migration_file>.py
git commit -m "feat: add user preferences table (migration abc123)"
git push origin main
```

---

## Scenario 2: Modifying Existing Table (Add Column)

### Example: Add email_verified column to api_keys

**Step 1: Update Model**

```python
class APIKey(Base):
    # ... existing columns ...
    email_verified = Column(Boolean, default=False, index=True)  # NEW
```

**Step 2: Create Migration**

```bash
./scripts/database/create_migration.sh "add email_verified to api_keys"
```

**Step 3: Review & Edit Migration**

Auto-generated migration might be:

```python
def upgrade() -> None:
    op.add_column('api_keys', sa.Column('email_verified', sa.Boolean(), nullable=True))
```

**Edit to set default**:

```python
def upgrade() -> None:
    # Add column with default
    op.add_column('api_keys',
        sa.Column('email_verified', sa.Boolean(),
                  nullable=False, server_default='false'))

    # Create index
    op.create_index('ix_api_keys_email_verified', 'api_keys', ['email_verified'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_email_verified', 'api_keys')
    op.drop_column('api_keys', 'email_verified')
```

**Step 4-7**: Same as Scenario 1

---

## Scenario 3: Data Migration

### Example: Migrate old user tier format

**Step 1: Create Empty Migration**

```bash
docker exec ops-center-direct bash -c "cd /app && alembic revision -m 'migrate user tier format'"
```

**Step 2: Edit Migration Manually**

```python
def upgrade() -> None:
    # Get database connection
    conn = op.get_bind()

    # Update tier values
    conn.execute(
        sa.text("""
            UPDATE organizations
            SET metadata_json = jsonb_set(
                COALESCE(metadata_json, '{}'::jsonb),
                '{tier}',
                to_jsonb(CASE
                    WHEN metadata_json->>'tier' = 'free' THEN 'trial'
                    WHEN metadata_json->>'tier' = 'basic' THEN 'starter'
                    WHEN metadata_json->>'tier' = 'pro' THEN 'professional'
                    ELSE metadata_json->>'tier'
                END)
            )
            WHERE metadata_json->>'tier' IS NOT NULL
        """)
    )


def downgrade() -> None:
    # Reverse the migration
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            UPDATE organizations
            SET metadata_json = jsonb_set(
                metadata_json,
                '{tier}',
                to_jsonb(CASE
                    WHEN metadata_json->>'tier' = 'trial' THEN 'free'
                    WHEN metadata_json->>'tier' = 'starter' THEN 'basic'
                    WHEN metadata_json->>'tier' = 'professional' THEN 'pro'
                    ELSE metadata_json->>'tier'
                END)
            )
            WHERE metadata_json->>'tier' IS NOT NULL
        """)
    )
```

**Step 3-7**: Apply and test

---

## Scenario 4: Renaming Column

**⚠️ Alembic cannot auto-detect renames!**

### Example: Rename `key_hash` to `api_key_hash`

**Step 1: Create Empty Migration**

```bash
docker exec ops-center-direct bash -c "cd /app && alembic revision -m 'rename key_hash to api_key_hash'"
```

**Step 2: Edit Migration**

```python
def upgrade() -> None:
    op.alter_column('api_keys', 'key_hash', new_column_name='api_key_hash')


def downgrade() -> None:
    op.alter_column('api_keys', 'api_key_hash', new_column_name='key_hash')
```

**Step 3: Update Model**

```python
class APIKey(Base):
    api_key_hash = Column(String(255), nullable=False)  # Renamed
```

---

## Scenario 5: Rollback After Error

### Example: Migration failed, need to rollback

**Step 1: Check Error**

```bash
docker logs ops-center-direct --tail 50
```

**Step 2: Rollback**

```bash
./scripts/database/rollback_migration.sh
```

This:
- Creates backup
- Rolls back last migration
- Database returns to previous state

**Step 3: Fix Migration**

Edit the migration file to fix the error.

**Step 4: Re-apply**

```bash
./scripts/database/run_migrations.sh
```

---

## Scenario 6: Production Deployment

### Example: Deploy new feature to production

**Development (Local)**:

```bash
# 1. Create and test migration
./scripts/database/create_migration.sh "add feature X"
./scripts/database/run_migrations.sh --dry-run
./scripts/database/run_migrations.sh

# 2. Test application
npm run test

# 3. Commit
git add .
git commit -m "feat: add feature X with migration"
git push origin main
```

**Production**:

```bash
# 1. Pull latest code
git pull origin main

# 2. Check migration status
./scripts/database/migration_status.sh

# 3. Preview changes
./scripts/database/run_migrations.sh --dry-run

# 4. Create manual backup (extra safety)
./scripts/database/backup_database.sh

# 5. Apply migrations
./scripts/database/run_migrations.sh

# 6. Verify application
curl http://localhost:8084/api/v1/system/status
docker logs ops-center-direct --tail 20

# 7. If error, rollback
./scripts/database/rollback_migration.sh
```

---

## Scenario 7: Zero-Downtime Migration

### Example: Add column without downtime

**Phase 1: Add Column (Nullable)**

```python
def upgrade() -> None:
    # Add as nullable first
    op.add_column('users', sa.Column('new_field', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'new_field')
```

Apply migration - application keeps running.

**Phase 2: Deploy Code Update**

Update application code to use new column.

**Phase 3: Backfill Data**

```python
def upgrade() -> None:
    # Backfill existing rows
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE users SET new_field = 'default' WHERE new_field IS NULL"))
```

**Phase 4: Make Non-Nullable**

```python
def upgrade() -> None:
    # Now safe to make NOT NULL
    op.alter_column('users', 'new_field', nullable=False)
```

---

## Quick Reference Cheat Sheet

```bash
# Check status
./scripts/database/migration_status.sh

# Create migration
./scripts/database/create_migration.sh "description"

# Preview SQL
./scripts/database/run_migrations.sh --dry-run

# Apply migrations
./scripts/database/run_migrations.sh

# Rollback
./scripts/database/rollback_migration.sh

# Backup
./scripts/database/backup_database.sh

# Restore
./scripts/database/restore_database.sh /path/to/backup.sql
```

---

## Common Pitfalls

### ❌ Don't Do This

1. **Don't edit applied migrations**
   ```bash
   # Wrong:
   vim alembic/versions/applied_migration.py
   ./scripts/database/run_migrations.sh
   ```

   **Right**:
   ```bash
   # Create new migration
   ./scripts/database/create_migration.sh "fix previous migration"
   ```

2. **Don't skip backups**
   ```bash
   # Wrong:
   docker exec ops-center-direct alembic upgrade head
   ```

   **Right**:
   ```bash
   # Use script (includes backup)
   ./scripts/database/run_migrations.sh
   ```

3. **Don't ignore dry-run**
   ```bash
   # Wrong:
   ./scripts/database/run_migrations.sh  # Apply immediately
   ```

   **Right**:
   ```bash
   ./scripts/database/run_migrations.sh --dry-run  # Review first
   ./scripts/database/run_migrations.sh            # Then apply
   ```

---

## Emergency Rollback Procedure

If production breaks after migration:

```bash
# 1. IMMEDIATELY rollback
./scripts/database/rollback_migration.sh

# 2. Restart application
docker restart ops-center-direct

# 3. Verify application is working
curl http://localhost:8084/api/v1/system/status

# 4. Check logs
docker logs ops-center-direct --tail 100

# 5. If still broken, restore from backup
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_LATEST.sql

# 6. Investigate issue
cat alembic/versions/<failed_migration>.py
docker logs ops-center-direct | grep -i error
```

---

**Remember**: Test locally, use dry-run, always backup, and rollback if anything goes wrong!
