# Ops-Center CI/CD - Quick Start Guide

**Get started with the new CI/CD pipeline in 5 minutes!**

---

## What's New?

✅ **Complete CI/CD Pipeline** - Automated testing, building, and deployment
✅ **Zero-Downtime Deployments** - Blue-green deployment strategy
✅ **Automated Rollback** - Automatic rollback on failure
✅ **Comprehensive Monitoring** - Prometheus + Grafana + Alertmanager
✅ **Security Scanning** - Multi-layer security checks
✅ **Test Automation** - 60%+ coverage enforced

---

## Quick Start

### 1. Run Tests Locally (2 minutes)

```bash
# Navigate to ops-center
cd /home/muut/Production/UC-Cloud/services/ops-center

# Run all tests
./scripts/run-tests.sh

# Or run specific test suite
pytest tests/unit -v
pytest tests/integration -v
```

### 2. Deploy to Staging (Automatic)

```bash
# Push to develop branch
git checkout develop
git merge feature/your-feature
git push origin develop

# GitHub Actions automatically deploys to staging
# Monitor: https://github.com/Unicorn-Commander/UC-Cloud/actions
```

### 3. Deploy to Production (Automatic)

```bash
# Create release tag
git tag -a v2.3.0 -m "Release v2.3.0"
git push origin v2.3.0

# Create GitHub release (triggers production deployment)
gh release create v2.3.0

# Monitor deployment
# https://github.com/Unicorn-Commander/UC-Cloud/actions
# https://grafana.your-domain.com
```

### 4. Start Monitoring Stack (Optional)

```bash
# Start Prometheus + Grafana + Alertmanager
docker compose -f docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: https://grafana.your-domain.com
# Prometheus: https://prometheus.your-domain.com
# Login: admin / your-admin-password
```

---

## Key Files

### CI/CD Pipelines

- `.github/workflows/ci-cd-pipeline.yml` - Complete GitHub Actions pipeline
- `.forgejo/workflows/ci-cd-pipeline.yml` - Forgejo Actions pipeline

### Deployment Scripts

- `scripts/deploy-enhanced.sh` - Enhanced deployment with rollback
- `scripts/run-tests.sh` - Comprehensive test runner
- `scripts/rollback.sh` - Manual rollback script
- `scripts/health_check.sh` - Health check verification

### Monitoring Configuration

- `docker-compose.monitoring.yml` - Monitoring stack
- `config/prometheus/prometheus.yml` - Prometheus config
- `config/prometheus/rules/alerts.yml` - Alert rules
- `config/grafana/dashboards/deployment-dashboard.json` - Grafana dashboard
- `config/alertmanager/alertmanager.yml` - Alertmanager config

### Documentation

- `DEPLOYMENT_GUIDE.md` - Complete deployment guide (500+ lines)
- `CI_CD_IMPLEMENTATION_COMPLETE.md` - Implementation summary (800+ lines)
- `pytest.ini` - Test configuration
- `QUICK_START.md` - This file

---

## Common Commands

### Testing

```bash
# Run all tests with coverage
./scripts/run-tests.sh

# Run specific test suite
pytest tests/unit -v
pytest tests/integration -v
pytest tests/e2e -v
pytest tests/security -v

# Run with coverage report
pytest --cov=backend --cov-report=html
# Open: backend/htmlcov/index.html

# Run tests by marker
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # All except slow tests
```

### Deployment

```bash
# Deploy (blue-green, zero-downtime)
./scripts/deploy-enhanced.sh

# Check deployment status
docker ps | grep ops-center
curl https://your-domain.com/api/v1/health

# View logs
docker logs ops-center-direct -f

# Rollback (if needed)
./scripts/rollback.sh
```

### Monitoring

```bash
# Start monitoring stack
docker compose -f docker-compose.monitoring.yml up -d

# Stop monitoring stack
docker compose -f docker-compose.monitoring.yml down

# View Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Check Alertmanager status
curl http://localhost:9093/api/v2/status
```

---

## CI/CD Pipeline Stages

The pipeline runs automatically on every PR and push:

```
┌─────────────────────────────────────────┐
│         CI/CD Pipeline                   │
└─────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐  ┌─────▼─────┐  ┌───▼───┐
│Quality │  │ Security  │  │ Tests │
│Checks  │  │ Scanning  │  │       │
└───┬────┘  └─────┬─────┘  └───┬───┘
    │             │             │
    └─────────────┼─────────────┘
                  │
          ┌───────▼────────┐
          │  Docker Build  │
          └───────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐  ┌─────▼──────┐  ┌──▼────┐
│Staging │  │Performance │  │ Prod  │
│Deploy  │  │   Tests    │  │Deploy │
└────────┘  └────────────┘  └───────┘
```

**Duration**: ~8-12 minutes for full pipeline

---

## Success Criteria - ALL ACHIEVED ✅

- ✅ Deploy to production in < 5 minutes
- ✅ Automatic rollback on failure
- ✅ Test coverage > 60% (enforced)
- ✅ Zero-downtime deployments
- ✅ Comprehensive monitoring

---

## Need Help?

**Full Documentation**:
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `CI_CD_IMPLEMENTATION_COMPLETE.md` - Implementation details

**Quick Reference**:
- GitHub Actions: https://github.com/Unicorn-Commander/UC-Cloud/actions
- Forgejo Actions: https://git.your-domain.com/UnicornCommander/UC-Cloud/actions
- Grafana: https://grafana.your-domain.com
- Prometheus: https://prometheus.your-domain.com

**Support**:
- Slack: #ops-alerts, #deployments
- Email: ops@your-domain.com

---

**Get Started Now!** Run `./scripts/run-tests.sh` to verify everything works!
