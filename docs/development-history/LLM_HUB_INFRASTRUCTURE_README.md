# LLM Hub Development Infrastructure

## Overview

This document describes the complete development infrastructure for the unified LLM Management system (Phase 1). All infrastructure is configured for safe, incremental rollout with feature flags, monitoring, and rollback capabilities.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Feature Flag System](#feature-flag-system)
4. [Development Environment](#development-environment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Logging](#monitoring--logging)
7. [Testing](#testing)
8. [Rollback Procedures](#rollback-procedures)
9. [Deployment](#deployment)

---

## Quick Start

### 1. Setup Development Environment

```bash
# Navigate to ops-center
cd /opt/ops-center

# Copy development environment
cp .env.development .env

# Create and setup test database
./backend/scripts/setup_test_db.sh

# Install Python dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd ../
npm install
```

### 2. Enable Feature Flag (Development)

```bash
# Edit .env file
export FEATURE_UNIFIED_LLM_HUB=true
export FEATURE_LLM_HUB_ROLLOUT=0
export FEATURE_LLM_HUB_WHITELIST=admin@unicorncommander.ai,admin@example.com

# Or use API
curl -X POST http://localhost:8084/api/v1/features/unified_llm_hub/enable
```

### 3. Start Development Server

```bash
# Backend (with hot reload)
cd backend
uvicorn server:app --reload --port 8084

# Frontend (separate terminal)
cd ../
npm run dev  # Runs on port 5173
```

### 4. Test Feature Flag

```bash
# Check if feature is enabled
curl http://localhost:8084/api/v1/features/unified_llm_hub

# Expected response:
{
  "flag": "unified_llm_hub",
  "enabled": true,
  "config": {
    "enabled": true,
    "rollout_percentage": 0,
    "whitelist_users": ["admin@unicorncommander.ai", "admin@example.com"]
  },
  "reason": "whitelisted"
}
```

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  LLM Hub Infrastructure                      │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │ Feature Flags │   │  Monitoring  │
            │   System      │   │   System     │
            └───────┬───────┘   └──────┬───────┘
                    │                   │
        ┌───────────┼───────────────────┼──────────┐
        │           │                   │          │
    ┌───▼───┐  ┌───▼───┐          ┌────▼────┐ ┌──▼───┐
    │Old UI │  │New UI │          │ Backend │ │  DB  │
    │(Stable)│ │(Test) │          │   API   │ │(Test)│
    └───────┘  └───────┘          └─────────┘ └──────┘
```

### File Structure

```
services/ops-center/
├── backend/
│   ├── config/
│   │   └── feature_flags.py          # Feature flag system ✅
│   ├── utils/
│   │   └── monitoring.py             # Monitoring utilities ✅
│   ├── scripts/
│   │   ├── setup_test_db.sh          # Test database setup ✅
│   │   └── rollback_migration.sh     # Database rollback
│   ├── migrations/
│   │   ├── 002_llm_management_tables.sql      # Forward migration
│   │   └── rollback_llm_management_tables.sql # Rollback migration
│   ├── feature_flag_api.py           # Feature flag API ✅
│   └── server.py                     # Main FastAPI app
├── .env.development                  # Development environment ✅
├── .github/
│   └── workflows/
│       └── llm-hub-ci.yml           # CI/CD pipeline ✅
├── DEVELOPMENT_WORKFLOW.md          # Development guide ✅
├── ROLLBACK_PLAN.md                 # Rollback procedures ✅
└── LLM_HUB_INFRASTRUCTURE_README.md # This file ✅
```

---

## Feature Flag System

### Configuration

Feature flags are configured via environment variables in `.env.development`:

```bash
# Enable/disable feature globally
FEATURE_UNIFIED_LLM_HUB=true

# Rollout percentage (0-100)
# Start at 0 and gradually increase: 0 → 10 → 25 → 50 → 100
FEATURE_LLM_HUB_ROLLOUT=0

# Whitelist users (always enabled)
FEATURE_LLM_HUB_WHITELIST=admin@unicorncommander.ai,admin@example.com

# Blacklist users (always disabled)
FEATURE_LLM_HUB_BLACKLIST=

# Date gates (ISO 8601 format)
FEATURE_LLM_HUB_START_DATE=2025-10-27
FEATURE_LLM_HUB_END_DATE=
```

### API Endpoints

#### Check Feature Flag
```bash
GET /api/v1/features/{flag_name}
```

**Example**:
```bash
curl http://localhost:8084/api/v1/features/unified_llm_hub

# Response:
{
  "flag": "unified_llm_hub",
  "enabled": true,
  "config": {...},
  "reason": "whitelisted"
}
```

#### List All Flags
```bash
GET /api/v1/features/
```

#### Get User's Enabled Features
```bash
GET /api/v1/features/user/{user_id}/enabled
```

#### Enable Feature (Admin)
```bash
POST /api/v1/features/{flag_name}/enable
```

#### Disable Feature (Admin)
```bash
POST /api/v1/features/{flag_name}/disable
```

#### Set Rollout Percentage (Admin)
```bash
POST /api/v1/features/{flag_name}/rollout/{percentage}
```

### Usage in Code

#### Backend (Python)
```python
from config.feature_flags import is_unified_llm_hub_enabled

# Check if feature is enabled
if is_unified_llm_hub_enabled(user_id):
    # Serve new UI
    return new_llm_hub_ui()
else:
    # Serve old UI
    return old_llm_pages()
```

#### Frontend (JavaScript)
```javascript
// Check feature flag via API
const response = await fetch('/api/v1/features/unified_llm_hub');
const { enabled } = await response.json();

if (enabled) {
  // Show new UI
  return <NewLLMHub />;
} else {
  // Show old UI
  return <OldLLMPages />;
}
```

### Rollout Strategy

**Phase 1: Internal Testing (0-10%)**
- Enable for whitelist users only
- Test all functionality
- Fix critical bugs
- Duration: 1-2 weeks

**Phase 2: Limited Rollout (10-25%)**
- Enable for 25% of users
- Monitor error rates and performance
- Collect user feedback
- Duration: 1 week

**Phase 3: Expanded Rollout (25-50%)**
- Enable for 50% of users
- Confirm stability
- Address feedback
- Duration: 1 week

**Phase 4: Majority Rollout (50-90%)**
- Enable for 90% of users
- Final bug fixes
- Prepare for full launch
- Duration: 1 week

**Phase 5: Full Launch (100%)**
- Enable for all users
- Deprecate old UI
- Monitor for issues
- Duration: Ongoing

---

## Development Environment

### Environment Variables

See `.env.development` for complete configuration. Key variables:

```bash
# Feature Flags
FEATURE_UNIFIED_LLM_HUB=true
FEATURE_LLM_HUB_ROLLOUT=0

# Database (use test database)
DATABASE_URL=postgresql://unicorn:unicorn@localhost:5432/unicorn_test

# Redis (use separate DB for dev)
REDIS_URL=redis://localhost:6379/1

# Debug Settings
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FEATURE_FLAGS=true
```

### Test Database Setup

The test database script creates a clean database with all required schemas:

```bash
./backend/scripts/setup_test_db.sh
```

**What it does**:
1. Drops existing test database
2. Creates new `unicorn_test` database
3. Applies baseline schema (if exists)
4. Applies LLM Hub schema
5. Seeds tier rules
6. Creates test users
7. Displays connection string

**Output**:
```
================================================
✓ Test database setup complete!
================================================

Connection String:
postgresql://unicorn:unicorn@localhost:5432/unicorn_test

Quick Commands:
  Connect: docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_test
  List tables: docker exec unicorn-postgresql psql -U unicorn -d unicorn_test -c '\dt'
```

### Local Development Commands

```bash
# Start backend with hot reload
cd backend
uvicorn server:app --reload --port 8084

# Start frontend dev server
npm run dev

# Run tests
pytest backend/tests/ -v

# Run linting
ruff check backend/

# Build frontend
npm run build
```

---

## CI/CD Pipeline

The CI/CD pipeline is configured in `.github/workflows/llm-hub-ci.yml`.

### Pipeline Jobs

#### 1. Backend Tests
- Installs Python dependencies
- Runs database migrations
- Executes unit tests with coverage
- Uploads coverage reports

#### 2. Code Quality
- Runs Ruff linter
- Checks Black formatting
- Runs MyPy type checking
- Runs Bandit security scan

#### 3. Database Migration Test
- Tests forward migration
- Tests rollback migration
- Verifies schema changes

#### 4. Feature Flag Test
- Tests feature flag system
- Verifies configuration loading
- Tests evaluation logic

#### 5. Build Validation
- Builds Docker image
- Tests container startup

### Branch Protection

**main**: Requires all checks to pass + 2 approvals
**staging**: Requires all checks to pass + 1 approval
**feature/llm-hub**: Requires all checks to pass

### Running CI Locally

```bash
# Install Act (GitHub Actions local runner)
# https://github.com/nektos/act

# Run all jobs
act pull_request

# Run specific job
act -j backend-tests
```

---

## Monitoring & Logging

### Monitoring System

The monitoring system (`backend/utils/monitoring.py`) provides:

- **Structured Logging**: JSON-formatted logs for analysis
- **Event Types**: PAGE_VIEW, FEATURE_USAGE, API_CALL, ERROR, etc.
- **Metrics Collection**: Performance and usage metrics
- **Feature Flag Analytics**: Track flag evaluations and changes

### Usage Examples

#### Log Page View
```python
from utils.monitoring import LLMHubMonitor

LLMHubMonitor.log_page_view(
    user_id="user@example.com",
    page="llm_hub",
    tab="provider_keys",
    referrer="/admin/dashboard"
)
```

#### Log Feature Usage
```python
LLMHubMonitor.log_feature_usage(
    user_id="user@example.com",
    feature="provider_key_management",
    action="create",
    details={"provider": "openai"}
)
```

#### Log Error
```python
try:
    # Some operation
    pass
except Exception as e:
    LLMHubMonitor.log_error(
        user_id="user@example.com",
        error=e,
        context={"operation": "create_key"}
    )
```

#### Record Metric
```python
from utils.monitoring import record_metric

record_metric(
    "llm_hub_page_load_time",
    value=234.5,
    page="provider_keys"
)
```

### View Logs

```bash
# View all logs
docker logs ops-center-direct -f

# Filter by event type
docker logs ops-center-direct | grep PAGE_VIEW

# Filter by user
docker logs ops-center-direct | grep "user@example.com"

# View feature flag evaluations
docker logs ops-center-direct | grep feature_flag
```

### Metrics Dashboard

Metrics can be exported to Grafana, Prometheus, or custom dashboards.

---

## Testing

### Test Levels

#### 1. Unit Tests
```bash
cd backend
pytest tests/test_feature_flags.py -v
pytest tests/test_monitoring.py -v
```

#### 2. Integration Tests
```bash
pytest tests/integration/ -v
```

#### 3. End-to-End Tests
```bash
# Requires running services
pytest tests/e2e/ -v
```

### Test Database

Always use the test database for development:

```bash
export DATABASE_URL=postgresql://unicorn:unicorn@localhost:5432/unicorn_test
```

### Testing Checklist

**Feature Flag Tests**:
- [ ] Global enable/disable works
- [ ] Whitelist users always enabled
- [ ] Blacklist users always disabled
- [ ] Rollout percentage deterministic
- [ ] Date gates functional

**Database Migration Tests**:
- [ ] Forward migration successful
- [ ] Tables created correctly
- [ ] Indexes created
- [ ] Foreign keys set up
- [ ] Rollback migration successful
- [ ] No orphaned data

**API Tests**:
- [ ] All endpoints return 200 OK
- [ ] Authentication required
- [ ] Rate limiting works
- [ ] Error handling correct

**UI Tests**:
- [ ] Old pages load when flag disabled
- [ ] New hub loads when flag enabled
- [ ] Navigation works
- [ ] Forms submit correctly

---

## Rollback Procedures

See `ROLLBACK_PLAN.md` for complete rollback procedures.

### Emergency Rollback (< 5 minutes)

```bash
# 1. Disable feature flag
export FEATURE_UNIFIED_LLM_HUB=false
docker restart ops-center-direct

# 2. Verify old pages work
curl https://unicorncommander.ai/admin/llm-provider-keys

# 3. Check logs
docker logs ops-center-direct --tail 50
```

### Full Rollback with Database

```bash
# 1. Stop service
docker compose stop ops-center-direct

# 2. Backup current database
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db \
  -f /tmp/pre_rollback_backup.dump

# 3. Run rollback migration
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db \
  < backend/migrations/rollback_llm_management_tables.sql

# 4. Restore old code version
git checkout tags/v1.0.0-pre-llm-hub

# 5. Restart service
docker compose up -d ops-center-direct
```

### Rollback Criteria

Execute immediate rollback if:
- Data loss detected
- Security breach
- Error rate > 5%
- Performance degradation > 50%
- Critical bug affecting all users

---

## Deployment

### Development → Staging

```bash
# 1. Merge to staging branch
git checkout staging
git merge feature/llm-hub

# 2. Deploy to staging
docker compose -f docker-compose.staging.yml up -d

# 3. Run smoke tests
./scripts/smoke-test.sh staging

# 4. Monitor logs
docker logs staging-ops-center -f
```

### Staging → Production

```bash
# 1. Merge to main branch
git checkout main
git merge staging

# 2. Tag release
git tag -a v1.0.0-llm-hub -m "LLM Hub Phase 1 release"

# 3. Deploy to production
docker compose -f docker-compose.prod.yml up -d

# 4. Run health checks
./scripts/health-check-detailed.sh

# 5. Monitor metrics
# Check error rates, response times, user feedback
```

### Gradual Rollout

```bash
# Start at 0% (whitelisted users only)
curl -X POST https://unicorncommander.ai/api/v1/features/unified_llm_hub/rollout/0

# Increase to 10% after testing
curl -X POST https://unicorncommander.ai/api/v1/features/unified_llm_hub/rollout/10

# Monitor for 48 hours, then increase
curl -X POST https://unicorncommander.ai/api/v1/features/unified_llm_hub/rollout/25

# Continue gradual rollout: 50% → 75% → 100%
```

---

## Troubleshooting

### Feature Flag Not Working

**Problem**: Feature flag doesn't enable/disable

**Solutions**:
1. Check environment variables loaded
2. Verify user in whitelist
3. Check logs for errors
4. Restart service

### Database Migration Failed

**Problem**: Migration script fails

**Solutions**:
1. Check current database state
2. Verify PostgreSQL running
3. Check for conflicting tables
4. Run rollback and retry

### Tests Failing

**Problem**: Unit or integration tests fail

**Solutions**:
1. Clear test database
2. Re-run migrations
3. Clear pytest cache
4. Check test fixtures

---

## Resources

- **Architecture**: `LLM_HUB_ARCHITECTURE.md`
- **Database Schema**: `LLM_HUB_DATABASE_SCHEMA.md`
- **API Docs**: `LLM_HUB_API_DOCS.md`
- **Development Workflow**: `DEVELOPMENT_WORKFLOW.md`
- **Rollback Plan**: `ROLLBACK_PLAN.md`

---

## Summary

The LLM Hub development infrastructure provides:

✅ **Feature Flag System** - Safe, gradual rollout
✅ **Test Database** - Isolated development environment
✅ **CI/CD Pipeline** - Automated testing and quality checks
✅ **Monitoring System** - Structured logging and metrics
✅ **Rollback Plan** - Quick recovery from issues
✅ **Development Workflow** - Clear branching and deployment strategy

All infrastructure is production-ready and follows best practices for:
- Incremental delivery
- Risk mitigation
- Quality assurance
- Observability
- Developer productivity

**Next Step**: Begin Phase 1 implementation using this infrastructure!
