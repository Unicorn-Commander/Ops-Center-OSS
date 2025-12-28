# Ops-Center Deployment Runbook
**Version**: 2.1.0
**Last Updated**: 2025-10-28
**Maintainer**: Infrastructure Team

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Standard Deployment](#standard-deployment)
3. [Hotfix Deployment](#hotfix-deployment)
4. [Rollback Procedures](#rollback-procedures)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Before Every Deployment

- [ ] **Code Review**: All changes peer-reviewed and approved
- [ ] **Tests Pass**: All unit, integration, and E2E tests passing
- [ ] **Changelog Updated**: CHANGELOG.md contains all changes
- [ ] **Environment Variables**: .env.auth reviewed for new variables
- [ ] **Database Migrations**: Alembic migrations tested locally
- [ ] **Backup Created**: Recent backup of database exists
- [ ] **Communication**: Team notified of deployment window
- [ ] **Monitoring Ready**: Grafana dashboards open, alerts configured

### Environment Variables to Verify

```bash
# Check critical environment variables
docker exec ops-center-direct printenv | grep -E "(KEYCLOAK|POSTGRES|REDIS|LAGO|STRIPE)"

# Expected output should include:
# KEYCLOAK_URL=http://uchub-keycloak:8080
# POSTGRES_HOST=unicorn-postgresql
# REDIS_HOST=unicorn-redis
# LAGO_API_KEY=...
```

---

## Standard Deployment

### Step 1: Prepare Deployment Package

```bash
#!/bin/bash
# deploy_prepare.sh

set -e

# Navigate to ops-center directory
cd /home/muut/Production/UC-Cloud/services/ops-center

# Ensure on correct branch
git fetch origin
git checkout main
git pull origin main

# Verify no uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "ERROR: Uncommitted changes detected. Commit or stash changes first."
    exit 1
fi

# Get latest commit hash (for rollback reference)
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "Deploying commit: $COMMIT_HASH"

# Save commit hash for rollback
echo "$COMMIT_HASH" > /tmp/last_deployment.txt
echo "Deployment prepared: $COMMIT_HASH"
```

### Step 2: Build Frontend

```bash
#!/bin/bash
# deploy_build_frontend.sh

set -e

cd /home/muut/Production/UC-Cloud/services/ops-center

# Install dependencies (if package.json changed)
npm install

# Run tests
npm run test || { echo "Tests failed! Aborting deployment."; exit 1; }

# Build production bundle
npm run build

# Verify build output
if [ ! -f "dist/index.html" ]; then
    echo "ERROR: Build failed - index.html not found"
    exit 1
fi

# Check bundle size
BUNDLE_SIZE=$(du -sh dist | cut -f1)
echo "Bundle size: $BUNDLE_SIZE"

echo "Frontend build successful"
```

### Step 3: Database Migrations

```bash
#!/bin/bash
# deploy_migrate_database.sh

set -e

cd /home/muut/Production/UC-Cloud/services/ops-center

# Create database backup BEFORE migration
BACKUP_FILE="/home/muut/backups/ops-center-db-$(date +%Y%m%d_%H%M%S).sql"
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > "$BACKUP_FILE"
echo "Database backup created: $BACKUP_FILE"

# Run migrations
docker exec ops-center-direct alembic upgrade head

# Verify migrations
docker exec ops-center-direct alembic current

echo "Database migrations completed"
```

### Step 4: Deploy to Production

```bash
#!/bin/bash
# deploy_production.sh

set -e

cd /home/muut/Production/UC-Cloud/services/ops-center

# Stop services gracefully
echo "Stopping ops-center..."
docker stop ops-center-direct

# Deploy frontend assets
echo "Deploying frontend..."
cp -r dist/* public/

# Rebuild backend (if backend changes)
echo "Rebuilding backend..."
docker compose -f docker-compose.direct.yml build

# Start services
echo "Starting ops-center..."
docker compose -f docker-compose.direct.yml up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

# Health check
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8084/api/v1/system/status || echo "000")

    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
        echo "✓ Ops-Center is healthy (HTTP $HTTP_CODE)"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for service... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Service failed to start"
    exit 1
fi

echo "Deployment completed successfully!"
```

### Step 5: Post-Deployment Verification

```bash
#!/bin/bash
# deploy_verify.sh

set -e

BASE_URL="http://localhost:8084"

echo "Running post-deployment verification..."

# Test 1: System status endpoint
echo "Test 1: System status endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/system/status)
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 2: Frontend loads
echo "Test 2: Frontend index page"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 3: Database connection
echo "Test 3: Database connection"
docker exec ops-center-direct python3 -c "from backend.database import engine; engine.connect()" && echo "  ✓ PASS" || echo "  ✗ FAIL"

# Test 4: Redis connection
echo "Test 4: Redis connection"
docker exec unicorn-redis redis-cli ping | grep -q PONG && echo "  ✓ PASS" || echo "  ✗ FAIL"

# Test 5: Keycloak connectivity
echo "Test 5: Keycloak connectivity"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/realms/uchub/.well-known/openid-configuration)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL (HTTP $HTTP_CODE)"
fi

echo ""
echo "All verification tests passed!"
```

---

## Hotfix Deployment

**When to Use**: Critical bugs in production requiring immediate fix

### Hotfix Process

```bash
#!/bin/bash
# hotfix_deploy.sh

set -e

HOTFIX_BRANCH="$1"

if [ -z "$HOTFIX_BRANCH" ]; then
    echo "Usage: ./hotfix_deploy.sh <hotfix-branch-name>"
    exit 1
fi

cd /home/muut/Production/UC-Cloud/services/ops-center

# Create hotfix backup
BACKUP_DIR="/home/muut/backups/hotfix-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > "$BACKUP_DIR/database.sql"

# Backup current frontend
cp -r public/ "$BACKUP_DIR/public_backup/"

# Backup current environment
cp .env.auth "$BACKUP_DIR/.env.auth.backup"

echo "Backup created: $BACKUP_DIR"

# Checkout hotfix branch
git fetch origin
git checkout "$HOTFIX_BRANCH"

# Quick build (skip tests for emergency)
npm run build
cp -r dist/* public/

# Restart backend
docker restart ops-center-direct

# Wait and verify
sleep 10
curl -s http://localhost:8084/api/v1/system/status || {
    echo "HOTFIX FAILED! Rolling back..."
    # Restore from backup
    cp -r "$BACKUP_DIR/public_backup/"* public/
    docker restart ops-center-direct
    exit 1
}

echo "Hotfix deployed successfully"
echo "Backup location: $BACKUP_DIR"
```

---

## Rollback Procedures

### Automatic Rollback (Preferred)

```bash
#!/bin/bash
# rollback.sh

set -e

# Get previous deployment commit
if [ ! -f /tmp/last_deployment.txt ]; then
    echo "ERROR: No previous deployment found"
    exit 1
fi

PREVIOUS_COMMIT=$(cat /tmp/last_deployment.txt)
echo "Rolling back to commit: $PREVIOUS_COMMIT"

cd /home/muut/Production/UC-Cloud/services/ops-center

# Checkout previous commit
git checkout "$PREVIOUS_COMMIT"

# Rebuild and deploy
npm run build
cp -r dist/* public/
docker restart ops-center-direct

# Wait and verify
sleep 10
curl -s http://localhost:8084/api/v1/system/status && echo "Rollback successful" || echo "Rollback failed"
```

### Database Rollback

```bash
#!/bin/bash
# rollback_database.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./rollback_database.sh <backup-file.sql>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop application
docker stop ops-center-direct

# Restore database
cat "$BACKUP_FILE" | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db

# Downgrade migrations (if needed)
docker exec ops-center-direct alembic downgrade -1

# Restart application
docker start ops-center-direct

echo "Database rollback completed"
```

---

## Post-Deployment Verification

### Manual Verification Checklist

After deployment, verify the following in the UI:

- [ ] **Login**: SSO login via Keycloak works
- [ ] **Dashboard**: Main dashboard loads with correct data
- [ ] **User Management**: User list displays (if admin)
- [ ] **Organizations**: Organization selector works
- [ ] **Billing**: Subscription information displays
- [ ] **LLM Hub**: LLM models list loads
- [ ] **Geeses**: ATLAS Multi-Agent page accessible
- [ ] **API Keys**: Can generate new API key
- [ ] **Logs**: Log viewer displays recent logs
- [ ] **Metrics**: System metrics charts render

### Automated Smoke Tests

```bash
#!/bin/bash
# smoke_tests.sh

set -e

BASE_URL="http://localhost:8084"

echo "Running smoke tests..."

# Array of critical endpoints
declare -a ENDPOINTS=(
    "/api/v1/system/status"
    "/api/v1/system/info"
    "/api/v1/auth/session"
    "/admin"
    "/admin/geeses"
)

FAILED=0

for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")

    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 400 ]; then
        echo "✓ $endpoint (HTTP $HTTP_CODE)"
    else
        echo "✗ $endpoint (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
done

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "All smoke tests passed!"
    exit 0
else
    echo ""
    echo "Failed: $FAILED tests"
    exit 1
fi
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Container Won't Start

**Symptoms**: `docker ps` shows container exited immediately

**Diagnosis**:
```bash
# Check container logs
docker logs ops-center-direct --tail 50

# Common errors:
# - "Address already in use" → Another service on port 8084
# - "Database connection failed" → PostgreSQL not running
# - "Module not found" → Missing Python dependencies
```

**Fix**:
```bash
# If port conflict
sudo lsof -i :8084
sudo kill -9 <PID>

# If database issue
docker restart unicorn-postgresql
sleep 5

# If dependency issue
docker compose -f docker-compose.direct.yml build --no-cache
```

#### Issue 2: Frontend Not Loading

**Symptoms**: Blank page or 404 errors

**Diagnosis**:
```bash
# Check if frontend files exist
ls -la /home/muut/Production/UC-Cloud/services/ops-center/public/

# Check nginx logs
docker logs ops-center-direct | grep nginx
```

**Fix**:
```bash
# Rebuild and redeploy frontend
cd /home/muut/Production/UC-Cloud/services/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct
```

#### Issue 3: Authentication Failures

**Symptoms**: "401 Unauthorized" or "Session invalid"

**Diagnosis**:
```bash
# Check Keycloak is running
docker ps | grep keycloak

# Test Keycloak endpoint
curl http://localhost:8080/realms/uchub/.well-known/openid-configuration
```

**Fix**:
```bash
# Restart Keycloak
docker restart uchub-keycloak

# Clear Redis session cache
docker exec unicorn-redis redis-cli FLUSHDB

# Restart ops-center
docker restart ops-center-direct
```

#### Issue 4: Database Migration Errors

**Symptoms**: "alembic.util.exc.CommandError"

**Diagnosis**:
```bash
# Check current migration version
docker exec ops-center-direct alembic current

# Check migration history
docker exec ops-center-direct alembic history
```

**Fix**:
```bash
# Downgrade to previous version
docker exec ops-center-direct alembic downgrade -1

# Or stamp current version (if migrations out of sync)
docker exec ops-center-direct alembic stamp head
```

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Lead Engineer | TBD | TBD | 24/7 |
| DevOps Engineer | TBD | TBD | Business Hours |
| Database Admin | TBD | TBD | On-Call |

---

## Deployment History Log

| Date | Version | Deployed By | Notes |
|------|---------|-------------|-------|
| 2025-10-28 | 2.1.0 | Night Shift | Geeses route added, QA improvements |
| 2025-10-27 | 2.0.9 | TBD | LLM Hub Phase 3 |
| 2025-10-26 | 2.0.8 | TBD | Grafana integration |

---

## Appendix: Useful Commands

### Docker Commands
```bash
# View all ops-center related containers
docker ps --filter "name=ops-center"

# View logs (real-time)
docker logs ops-center-direct -f

# Restart container
docker restart ops-center-direct

# Rebuild container
docker compose -f docker-compose.direct.yml build --no-cache

# Enter container shell
docker exec -it ops-center-direct /bin/bash
```

### Database Commands
```bash
# Access PostgreSQL
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

# List tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"

# Count users
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM keycloak_users;"

# Backup database
docker exec unicorn-postgresql pg_dump -U unicorn unicorn_db > backup.sql

# Restore database
cat backup.sql | docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db
```

### Redis Commands
```bash
# Check Redis connection
docker exec unicorn-redis redis-cli ping

# View all keys
docker exec unicorn-redis redis-cli KEYS "*"

# Clear all cache
docker exec unicorn-redis redis-cli FLUSHDB

# Monitor Redis commands
docker exec unicorn-redis redis-cli MONITOR
```

---

**Document Version**: 1.0
**Last Reviewed**: 2025-10-28
**Next Review Date**: 2025-11-28
