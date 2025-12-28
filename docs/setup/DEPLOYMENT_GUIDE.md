# Ops-Center Deployment Guide

**Complete CI/CD and Deployment Documentation**

Version: 1.0.0
Last Updated: November 12, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Deployment Strategies](#deployment-strategies)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

The Ops-Center deployment system provides **zero-downtime deployments** with **automated rollback** capabilities. It uses:

- **Blue-Green Deployment**: Minimize downtime with parallel environments
- **Automated Health Checks**: Verify deployment success before cutover
- **Automatic Rollback**: Revert to last known good state on failure
- **Comprehensive Monitoring**: Real-time metrics and alerting

### Key Features

- Zero-Downtime Deployments - Deploy without service interruption
- Automated Testing - Run 60+ tests on every PR
- Security Scanning - Trivy, npm audit, Safety checks
- Performance Monitoring - Prometheus + Grafana dashboards
- Automated Backups - Database and configuration backups before deployment
- Rollback on Failure - Automatic rollback if health checks fail
- Deployment in < 5 minutes - Optimized deployment pipeline

---

## Quick Start

### Deploy to Production

```bash
# Via GitHub Actions (recommended)
# 1. Create a release on GitHub
gh release create v2.3.0 --title "Release v2.3.0" --notes "See CHANGELOG.md"

# 2. Deployment runs automatically on release
# Monitor at: https://github.com/Unicorn-Commander/UC-Cloud/actions

# Manual deployment (emergency)
cd /opt/ops-center/deployment
export IMAGE_TAG=v2.3.0
./deploy-enhanced.sh
```

### Deploy to Staging

```bash
# Push to develop branch - auto-deploys to staging
git checkout develop
git merge feature/my-feature
git push origin develop

# Monitor at: https://staging.your-domain.com
```

---

## Prerequisites

### Required Services

```bash
# Check Docker services
docker ps | grep -E "unicorn-postgresql|unicorn-redis|uchub-keycloak|traefik"

# Required services:
# - unicorn-postgresql (database)
# - unicorn-redis (cache)
# - uchub-keycloak (authentication)
# - traefik (reverse proxy)
```

### Required Secrets

**For GitHub Actions:**

```yaml
PRODUCTION_SSH_KEY: SSH private key for server access
PRODUCTION_HOST: Production server hostname/IP
PRODUCTION_USER: SSH username
SLACK_WEBHOOK_URL: Slack webhook for notifications (optional)
```

### Environment Variables

Set these in `.env.auth`:

```bash
ENVIRONMENT=production
ROLLBACK_ON_FAILURE=true
BACKUP_RETENTION_DAYS=7
HEALTH_CHECK_RETRIES=30
```

---

## CI/CD Pipeline

### Pipeline Stages

```
Code Quality → Security Scan → Backend Tests → Frontend Tests
     ↓              ↓               ↓                ↓
     └──────────────┴───────────────┴────────────────┘
                          ↓
                    Docker Build
                          ↓
         ┌────────────────┼────────────────┐
         ↓                ↓                ↓
     Staging         Performance      Production
     Deploy            Tests            Deploy
```

### Test Coverage Requirements

- Backend: 60% minimum (target: 80%+)
- Frontend: 50% minimum (target: 70%+)
- Integration: 40% minimum (target: 60%+)

### Running Tests Locally

```bash
# Backend unit tests
cd backend
pytest tests/unit -v --cov=. --cov-report=html

# All tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Deployment Strategies

### Blue-Green Deployment (Default)

Zero-downtime deployment with parallel environments:

1. Deploy new version (green) alongside current (blue)
2. Health check green environment
3. Switch traffic to green
4. Shut down blue

```bash
export DEPLOYMENT_STRATEGY=blue-green
export IMAGE_TAG=v2.3.0
./deploy-enhanced.sh
```

### Rolling Deployment

Gradual update, container by container:

```bash
export DEPLOYMENT_STRATEGY=rolling
./deploy-enhanced.sh
```

### Canary Deployment

Deploy to small percentage first:

```bash
export DEPLOYMENT_STRATEGY=canary
export CANARY_PERCENTAGE=10
./deploy-enhanced.sh
```

---

## Monitoring & Alerts

### Prometheus Metrics

```promql
# Deployment success rate
sum(rate(deployment_total{status="success"}[5m])) / sum(rate(deployment_total[5m]))

# API error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana Dashboards

**Access:** https://your-domain.com:9090

**Dashboards:**
1. Deployment Dashboard - Deployment metrics, success rate
2. Application Dashboard - API performance, error rates
3. Infrastructure Dashboard - System resources

### Critical Alerts

- Deployment failed
- Health check failing
- Database down
- High API error rate (> 5%)

---

## Rollback Procedures

### Automatic Rollback

Deployment automatically rolls back on:
- Health checks fail
- Smoke tests fail
- Container crashes
- Database migrations fail

### Manual Rollback

```bash
# Quick rollback to last successful
cd /opt/ops-center/deployment
./rollback.sh

# Rollback to specific version
export ROLLBACK_VERSION=v2.2.0
./rollback.sh
```

### Database Rollback

```bash
# List backups
ls -lh backups/db_backup_*.sql.gz

# Restore backup
BACKUP_FILE="backups/db_backup_20251112_143022.sql.gz"
gunzip < "$BACKUP_FILE" | docker exec -i unicorn-postgresql psql -U unicorn unicorn_db
```

---

## Troubleshooting

### Health Checks Failing

```bash
# Check logs
docker logs ops-center-direct --tail 100

# Test endpoint
curl -v http://localhost:8084/api/v1/health

# Check dependencies
docker ps | grep -E "postgresql|redis|keycloak"
```

### Database Migration Failed

```bash
# Check status
docker exec ops-center-direct python -m alembic current

# Manually run migration
docker exec ops-center-direct python -m alembic upgrade head
```

### Out of Disk Space

```bash
# Check usage
df -h

# Clean Docker
docker system prune -a -f

# Remove old backups
find backups/ -type f -mtime +7 -delete
```

### Container Won't Start

```bash
# Check logs
docker logs ops-center-direct

# Rebuild from scratch
docker compose -f docker-compose.direct.yml build --no-cache
docker compose -f docker-compose.direct.yml up -d
```

---

## Best Practices

### 1. Always Test Locally

```bash
# Run full test suite
pytest tests/ -v --cov=backend

# Build and test Docker image
docker compose up -d
curl http://localhost:8084/api/v1/health
```

### 2. Use Feature Branches

```bash
git checkout -b feature/new-endpoint
# Make changes
git push origin feature/new-endpoint
# Create PR - CI/CD runs automatically
```

### 3. Tag Releases Properly

```bash
git tag -a v2.3.0 -m "Release v2.3.0"
git push origin v2.3.0
```

### 4. Monitor After Deployment

**First 15 Minutes:**
- Watch error rates
- Check logs
- Monitor response times

**First Hour:**
- Database performance
- Memory usage
- Cache hit rates

### 5. Maintain Backups

```bash
# Automated daily backups (cron)
0 2 * * * /opt/ops-center/scripts/automated-backup.sh

# Verify backups weekly
0 3 * * 0 /opt/ops-center/scripts/verify-backup.sh
```

---

## Quick Reference

### Deployment Commands

```bash
# Deploy
./scripts/deploy-enhanced.sh

# Check status
curl http://localhost:8084/api/v1/health

# View logs
docker logs ops-center-direct -f

# Rollback
./scripts/rollback.sh

# Health check
./scripts/health_check.sh
```

### Useful URLs

- **Production:** https://your-domain.com
- **API:** https://api.your-domain.com
- **Grafana:** https://your-domain.com:9090
- **GitHub Actions:** https://github.com/Unicorn-Commander/UC-Cloud/actions
- **Forgejo Actions:** https://git.your-domain.com/UnicornCommander/UC-Cloud/actions

---

**For detailed information, see:**
- `README.md` - Project overview
- `CLAUDE.md` - Complete project context
- `.github/workflows/` - CI/CD pipeline definitions
