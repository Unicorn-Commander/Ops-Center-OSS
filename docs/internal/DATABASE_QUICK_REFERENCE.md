# Database Migrations - Quick Reference Card

**Status**: ✅ Production Ready
**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`

---

## 🚀 Common Commands

```bash
# Check migration status
./scripts/database/migration_status.sh

# Create new migration
./scripts/database/create_migration.sh "description"

# Preview SQL (dry-run)
./scripts/database/run_migrations.sh --dry-run

# Apply migrations
./scripts/database/run_migrations.sh

# Rollback last migration
./scripts/database/rollback_migration.sh

# Create backup
./scripts/database/backup_database.sh

# Restore from backup
./scripts/database/restore_database.sh /path/to/backup.sql
```

---

## 📁 Important Locations

| Item | Location |
|------|----------|
| **Models** | `backend/database/models.py` |
| **Migrations** | `alembic/versions/` |
| **Config** | `alembic.ini` |
| **Scripts** | `scripts/database/` |
| **Backups** | `/home/muut/backups/database/` |
| **Docs** | `docs/DATABASE_*.md` |

---

## 📊 Current Status

**Database**: `unicorn_db`
**Current Version**: `f6570c470a28` (baseline)
**Tables**: 12
**Backup Retention**: 7 days
**Last Backup**: Check `/home/muut/backups/database/`

---

## 🔧 Database Password

**IMPORTANT**: Scripts need this environment variable:

```bash
export POSTGRES_PASSWORD='CCCzgFZlaDb0JSL1xdPAzwGO'
```

Or run commands in container:

```bash
docker exec ops-center-direct bash -c "
  cd /app && \
  export POSTGRES_PASSWORD='CCCzgFZlaDb0JSL1xdPAzwGO' && \
  alembic current
"
```

---

## 📋 12 Tables Defined

1. **organizations** - Organization records
2. **organization_members** - User-organization relationships
3. **organization_invitations** - Pending invitations
4. **api_keys** - User API keys
5. **audit_logs** - System-wide audit trail
6. **cloudflare_zones** - DNS zones
7. **cloudflare_dns_records** - DNS records
8. **cloudflare_firewall_rules** - Firewall rules
9. **migration_jobs** - Domain migration tracking
10. **namecheap_domains** - Namecheap registrations
11. **cloudflare_domains** - Cloudflare registrations
12. **alembic_version** - Migration tracking (auto-created)

---

## 🔄 Typical Workflow

### Adding a New Feature

```bash
# 1. Edit models
vim backend/database/models.py

# 2. Create migration
./scripts/database/create_migration.sh "add feature X"

# 3. Review migration
cat alembic/versions/<latest>.py

# 4. Test with dry-run
./scripts/database/run_migrations.sh --dry-run

# 5. Apply
./scripts/database/run_migrations.sh
# (Automatic backup created)

# 6. Commit
git add backend/database/models.py alembic/versions/<new>.py
git commit -m "feat: add feature X (migration abc123)"
```

---

## 🆘 Emergency Rollback

```bash
# 1. Rollback migration
./scripts/database/rollback_migration.sh

# 2. Restart application
docker restart ops-center-direct

# 3. Verify
./scripts/database/migration_status.sh
curl http://localhost:8084/api/v1/system/status

# 4. If still broken, restore from backup
./scripts/database/restore_database.sh /home/muut/backups/database/unicorn_db_LATEST.sql
```

---

## 📚 Documentation

- **Main Guide**: `docs/DATABASE_MIGRATIONS.md` (712 lines)
- **Workflows**: `docs/MIGRATION_WORKFLOW.md` (483 lines)
- **Rollback**: `docs/ROLLBACK_PROCEDURE.md` (412 lines)
- **Backup**: `docs/BACKUP_RESTORE.md` (609 lines)
- **Report**: `docs/DATABASE_MIGRATION_DEPLOYMENT_REPORT.md`

---

## ✅ Best Practices

**DO**:
- ✅ Always review auto-generated migrations
- ✅ Test in development first
- ✅ Use dry-run before applying
- ✅ Backup before major changes
- ✅ Commit migrations to Git
- ✅ Document complex migrations

**DON'T**:
- ❌ Edit applied migrations
- ❌ Delete migration files
- ❌ Skip backups
- ❌ Run untested migrations in production
- ❌ Ignore warnings
- ❌ Manually modify alembic_version table

---

## 🔍 Troubleshooting

### Migration Fails
```bash
# Rollback
./scripts/database/rollback_migration.sh

# Fix migration file
vim alembic/versions/<failed>.py

# Try again
./scripts/database/run_migrations.sh
```

### Password Authentication Failed
```bash
# Set password environment variable
export POSTGRES_PASSWORD='CCCzgFZlaDb0JSL1xdPAzwGO'

# Or run in container
docker exec ops-center-direct bash -c "cd /app && export POSTGRES_PASSWORD='CCCzgFZlaDb0JSL1xdPAzwGO' && alembic current"
```

### Container Not Running
```bash
# Start containers
docker start ops-center-direct unicorn-postgresql

# Verify
docker ps | grep -E 'ops-center|postgresql'
```

---

## 📞 Support

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`

**Check logs**:
```bash
docker logs ops-center-direct --tail 50
docker logs unicorn-postgresql --tail 50
```

**Database access**:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db
```

---

**Last Updated**: October 23, 2025
**Version**: 1.0.0
**Migration System**: Alembic 1.13.1

---

**Remember**: Always backup before migrations, test in development first, and review auto-generated migrations carefully!
