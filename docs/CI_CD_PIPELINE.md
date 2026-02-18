# CI/CD Pipeline Documentation

## Overview

The Ops-Center CI/CD pipeline automates testing, building, and deployment using GitHub Actions. The pipeline ensures code quality, security, and reliable deployments with automatic rollback capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Pipeline                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │  Pull Request │   │ Merge to Main│
            └───────┬───────┘   └──────┬───────┘
                    │                   │
        ┌───────────┼───────────────────┼──────────┐
        │           │                   │          │
    ┌───▼───┐  ┌───▼───┐          ┌────▼────┐ ┌──▼───┐
    │ Test  │  │ Lint  │          │  Build  │ │Deploy│
    │ Suite │  │Security│         │ Images  │ │Staging│
    └───┬───┘  └───┬───┘          └────┬────┘ └──┬───┘
        │          │                    │          │
        └──────────┴────────────────────┴──────────┘
                          │
                  ┌───────┴────────┐
                  │                │
            ┌─────▼─────┐    ┌────▼─────┐
            │  Manual   │    │Production│
            │  Approval │    │ Deploy   │
            └───────────┘    └──────────┘
```

## Workflows

### 1. Test Workflow (`test.yml`)

**Trigger**: Every pull request and push to `develop` branch

**Jobs**:

#### Backend Lint
- Runs Ruff linter for code quality
- Runs Black formatter check
- Runs MyPy type checker (continues on error initially)

#### Backend Tests
- Spins up PostgreSQL and Redis test containers
- Runs unit tests with pytest
- Runs integration tests (continues on error if more setup needed)
- Generates coverage report
- Uploads coverage to Codecov

#### Frontend Lint
- Runs ESLint on React code
- Allows up to 50 warnings initially

#### Frontend Build
- Builds production bundle with Vite
- Reports bundle size
- Uploads build artifacts (retained for 7 days)

#### Frontend Tests
- Runs Vitest unit tests
- Generates coverage report
- Uploads coverage to Codecov

#### Security Scan
- Runs Trivy vulnerability scanner on filesystem
- Checks npm dependencies with `npm audit`
- Checks Python dependencies with `safety`
- Uploads results to GitHub Security tab

#### Test Summary
- Aggregates results from all test jobs
- Provides overall pass/fail status

**Example**:
```yaml
# Automatically runs on PR:
git checkout -b feature/my-feature
git push origin feature/my-feature
# Create PR → Tests run automatically
```

### 2. Build Workflow (`build.yml`)

**Trigger**: Merge to `main` branch, or manual dispatch

**Jobs**:

#### Build Backend Image
- Uses multi-stage Dockerfile for optimization
- Builds image with Docker Buildx
- Tags with branch name, commit SHA, and `latest`
- Pushes to GitHub Container Registry (ghcr.io)
- Uses layer caching for faster builds

**Image Tags**:
- `ghcr.io/unicorn-commander/ops-center-backend:main`
- `ghcr.io/unicorn-commander/ops-center-backend:main-abc1234`
- `ghcr.io/unicorn-commander/ops-center-backend:latest`

#### Build Frontend Image
- Uses multi-stage Dockerfile with Nginx
- Optimizes for small image size (<50MB target)
- Tags and pushes to registry

#### Scan Images
- Runs Trivy security scanner on built images
- Scans for vulnerabilities in both backend and frontend
- Uploads results to GitHub Security

**Example**:
```bash
# Automatically runs on merge to main
git checkout main
git merge feature/my-feature
git push origin main
# Build workflow triggers automatically
```

### 3. Deploy to Staging Workflow (`deploy-staging.yml`)

**Trigger**: Merge to `main` branch, or manual dispatch

**Environment**: `staging` (https://staging.unicorncommander.ai)

**Steps**:

1. **Checkout Code**: Pulls latest code from main branch

2. **Set up SSH**: Configures SSH to connect to staging server
   - Uses `STAGING_SSH_KEY` secret
   - Adds staging host to known hosts

3. **Create Deployment Directory**: Creates required directories on server
   - `/opt/ops-center/deployment`
   - `/opt/ops-center/backups`

4. **Copy Deployment Scripts**: Transfers scripts to server
   - `deploy.sh`
   - `health_check.sh`
   - `docker-compose.prod.yml`

5. **Run Database Migrations**: Backs up and migrates database
   - Creates database backup before migration
   - Runs Alembic migrations (if configured)

6. **Deploy Services**: Runs deployment script
   - Sets environment to `staging`
   - Pulls latest images with commit SHA tag
   - Starts services with new images

7. **Health Checks**: Verifies deployment
   - Waits 15 seconds for services to start
   - Runs comprehensive health check script
   - Checks all endpoints and services

8. **Smoke Tests**: Tests critical functionality
   - Tests `/api/v1/system/status` endpoint
   - Tests `/api/v1/health` endpoint

9. **Notify Success/Failure**: Updates GitHub summary
   - On success: Shows deployment details
   - On failure: Triggers automatic rollback

**Example**:
```bash
# Manually trigger staging deployment
gh workflow run deploy-staging.yml
```

### 4. Deploy to Production Workflow (`deploy-production.yml`)

**Trigger**: Manual dispatch only (requires input)

**Environment**: `production` (https://unicorncommander.ai)

**Required Input**: Version/tag to deploy

**Steps**:

1. **Validate Version**: Ensures the specified version exists
   - Fetches git tags
   - Verifies version exists in repository

2. **Backup Current State**: Creates comprehensive backup
   - Backs up PostgreSQL database
   - Saves current docker-compose configuration
   - Saves current image tags for rollback

3. **Deploy with Zero-Downtime**: Uses blue-green deployment
   - Starts new version alongside current
   - Switches traffic after health check
   - Stops old version

4. **Comprehensive Health Checks**: Extensive verification
   - Waits 30 seconds for stabilization
   - Runs all health checks
   - Verifies no errors in logs

5. **Production Smoke Tests**: Critical endpoint testing
   - Tests system status
   - Tests authentication
   - Tests admin endpoints (if configured)

6. **Automatic Rollback on Failure**: Reverts to previous version
   - Runs rollback script automatically
   - Verifies rollback health
   - Sends alerts (if configured)

**Example**:
```bash
# Manually trigger production deployment
gh workflow run deploy-production.yml -f version=v2.1.0

# Or via GitHub UI:
# Actions → Deploy to Production → Run workflow → Enter version
```

## Deployment Strategies

The deployment scripts support multiple strategies:

### Rolling Deployment (Default)

Updates services one at a time with minimal downtime.

```bash
./scripts/deploy.sh --strategy=rolling
```

**Process**:
1. Update backend service
2. Health check backend
3. Update frontend service
4. Health check frontend

**Downtime**: ~5-10 seconds (during restart)

### Blue-Green Deployment

Runs new version alongside old, switches traffic after verification.

```bash
./scripts/deploy.sh --strategy=blue-green
```

**Process**:
1. Deploy to green environment (if blue is current)
2. Health check green environment
3. Switch traffic from blue to green
4. Stop blue environment

**Downtime**: Zero (instant traffic switch)

### Canary Deployment

Deploys to small percentage of traffic for testing.

```bash
./scripts/deploy.sh --strategy=canary
```

**Process**:
1. Deploy canary version (10% traffic)
2. Monitor metrics for 5 minutes
3. Manual decision to promote or rollback
4. If promoting: `./scripts/deploy.sh --promote-canary`

**Downtime**: Zero

## Secrets Configuration

Required GitHub Secrets:

### For All Workflows
- `GITHUB_TOKEN`: Automatically provided by GitHub
- `CODECOV_TOKEN`: For uploading coverage reports (optional)

### For Staging Deployment
- `STAGING_SSH_KEY`: SSH private key for staging server
- `STAGING_HOST`: Staging server hostname/IP
- `STAGING_USER`: SSH username for staging server

### For Production Deployment
- `PRODUCTION_SSH_KEY`: SSH private key for production server
- `PRODUCTION_HOST`: Production server hostname/IP
- `PRODUCTION_USER`: SSH username for production server
- `PROD_API_KEY`: API key for production smoke tests (optional)
- `SLACK_WEBHOOK`: For deployment notifications (optional)

### Setting Secrets

```bash
# Via GitHub CLI
gh secret set STAGING_SSH_KEY < ~/.ssh/id_rsa_staging
gh secret set STAGING_HOST --body "staging.unicorncommander.ai"

# Or via GitHub UI:
# Settings → Secrets and variables → Actions → New repository secret
```

## Environment Variables

Each environment has its own configuration:

### Development (`config/development.env`)
- Local database and services
- Debug mode enabled
- Relaxed security settings

### Staging (`config/staging.env`)
- Staging database and services
- Test Stripe keys
- Verbose logging

### Production (`config/production.env`)
- Production database and services
- Live Stripe keys (when ready)
- Strict security settings

## Monitoring & Alerts

### Build Status Badge

Add to README.md:
```markdown
![CI](https://github.com/Unicorn-Commander/Ops-Center/workflows/Test%20Suite/badge.svg)
```

### Deployment Notifications

Configure Slack/Discord webhooks in workflow files:

```yaml
- name: Notify deployment
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -d '{"text":"✅ Deployed to production: ${{ inputs.version }}"}'
```

## Troubleshooting

### Test Failures

**Problem**: Tests fail on PR

**Solution**:
```bash
# Run tests locally first
cd backend
pytest tests/unit -v

# Check linting
ruff check .
black --check .

# Frontend tests
npm run test
```

### Build Failures

**Problem**: Docker build fails

**Solution**:
```bash
# Test build locally
docker build -f docker/Dockerfile.backend -t test .
docker build -f docker/Dockerfile.frontend -t test .

# Check .dockerignore
# Ensure required files aren't excluded
```

### Deployment Failures

**Problem**: Health check fails after deployment

**Solution**:
```bash
# SSH to server
ssh user@staging.unicorncommander.ai

# Check logs
docker logs ops-center-direct --tail 100

# Run health check manually
cd /opt/ops-center/deployment
./health_check.sh

# Rollback if needed
./rollback.sh
```

### Rollback Issues

**Problem**: Automatic rollback fails

**Solution**:
```bash
# SSH to server
ssh user@production.unicorncommander.ai

# List available backups
ls -lh /opt/ops-center/backups/

# Manual rollback to specific backup
cd /opt/ops-center/deployment
./rollback.sh --backup-timestamp=20251022_153000
```

## Best Practices

### 1. Never Skip Tests

Always ensure tests pass before merging:
```bash
# Run full test suite locally
npm run test
cd backend && pytest
```

### 2. Use Feature Branches

```bash
git checkout -b feature/new-feature
# Make changes
git push origin feature/new-feature
# Create PR
```

### 3. Tag Releases

```bash
# Create annotated tag
git tag -a v2.1.0 -m "Release v2.1.0: Added CI/CD pipeline"
git push origin v2.1.0

# Deploy specific tag to production
gh workflow run deploy-production.yml -f version=v2.1.0
```

### 4. Monitor Deployments

- Check GitHub Actions logs
- Monitor server logs during deployment
- Watch metrics dashboard (if configured)

### 5. Test in Staging First

Always deploy to staging before production:
```bash
# Merge to main → Auto-deploy to staging
# Verify staging works
# Then manually deploy to production
```

## Performance Metrics

### Build Times (Expected)

- **Backend Lint**: ~1 minute
- **Backend Tests**: ~3 minutes
- **Frontend Lint**: ~30 seconds
- **Frontend Build**: ~2 minutes
- **Frontend Tests**: ~1 minute
- **Docker Build**: ~5 minutes (with cache: ~2 minutes)
- **Total Pipeline**: ~10-15 minutes

### Deployment Times (Expected)

- **Staging Deployment**: ~5 minutes
- **Production Deployment**: ~10 minutes (including health checks)
- **Rollback**: ~2 minutes

### Image Sizes (Target)

- **Backend**: <500MB (currently ~1GB without optimization)
- **Frontend**: <50MB (Nginx + static files)

## Next Steps

1. **Configure GitHub Secrets**: Add all required secrets
2. **Test Workflows**: Create a test PR to verify workflows
3. **Configure Codecov**: Set up code coverage tracking
4. **Set Up Monitoring**: Configure alerts for failed deployments
5. **Document Runbooks**: Create operational procedures

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
