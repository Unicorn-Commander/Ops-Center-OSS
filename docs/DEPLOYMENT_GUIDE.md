# Ops-Center Deployment Guide

## Quick Start

### Prerequisites

1. **Server Access**: SSH access to target server
2. **Docker Installed**: Docker and Docker Compose on server
3. **Environment Variables**: Configured .env file
4. **Database**: PostgreSQL instance running
5. **Authentication**: Keycloak instance running

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/Unicorn-Commander/Ops-Center.git
cd Ops-Center

# Copy and configure environment
cp .env.example .env.auth
vim .env.auth  # Fill in your values

# Run deployment script
./scripts/deploy.sh
```

## Deployment Methods

### Method 1: Automated CI/CD (Recommended)

Best for: Production and staging environments

**Setup**:
```bash
# 1. Fork/clone repository
# 2. Configure GitHub Secrets (see CI_CD_PIPELINE.md)
# 3. Push to main branch

git checkout main
git merge feature/my-feature
git push origin main

# Automatically triggers:
# - Build workflow
# - Deploy to staging workflow
```

**Deploy to Production**:
```bash
# Via GitHub CLI
gh workflow run deploy-production.yml -f version=v2.1.0

# Or via GitHub UI:
# Actions → Deploy to Production → Run workflow
```

### Method 2: Manual Deployment

Best for: Initial setup, troubleshooting, or custom deployments

**Step-by-Step**:

#### 1. Prepare Server

```bash
# SSH to server
ssh user@your-server.com

# Create directories
sudo mkdir -p /opt/ops-center/{deployment,backups,releases}
sudo chown $USER:$USER /opt/ops-center

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 2. Clone Repository

```bash
cd /opt/ops-center
git clone https://github.com/Unicorn-Commander/Ops-Center.git deployment
cd deployment
```

#### 3. Configure Environment

```bash
# Copy template
cp .env.example .env.auth

# Edit configuration
vim .env.auth
```

**Required Variables**:
```bash
# Keycloak
KEYCLOAK_CLIENT_SECRET=your-secret-here

# Database
POSTGRES_PASSWORD=your-db-password-here

# Lago
LAGO_API_KEY=your-lago-key-here

# Stripe
STRIPE_SECRET_KEY=sk_test_your-key-here

# Application
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
```

#### 4. Build Images

```bash
# Build optimized images
docker build -f docker/Dockerfile.backend -t ops-center-backend:latest .
docker build -f docker/Dockerfile.frontend -t ops-center-frontend:latest .

# Or pull from registry (if available)
docker pull ghcr.io/unicorn-commander/ops-center-backend:latest
docker pull ghcr.io/unicorn-commander/ops-center-frontend:latest
```

#### 5. Run Deployment

```bash
# Using deployment script
./scripts/deploy.sh

# Or manually with docker-compose
docker compose -f docker-compose.prod.yml up -d
```

#### 6. Verify Deployment

```bash
# Run health check
./scripts/health_check.sh

# Check logs
docker logs ops-center-direct --tail 50

# Test endpoints
curl https://your-domain.com/api/v1/health
curl https://your-domain.com/api/v1/system/status
```

### Method 3: Docker Compose Only

Best for: Development or simple setups

```bash
# Clone repository
git clone https://github.com/Unicorn-Commander/Ops-Center.git
cd Ops-Center

# Configure environment
cp .env.example .env.auth
vim .env.auth

# Start services
docker compose -f docker-compose.direct.yml up -d

# Check status
docker compose -f docker-compose.direct.yml ps
```

## Deployment Strategies

### Rolling Deployment

**Use Case**: Standard deployments, minimal downtime acceptable

**Command**:
```bash
./scripts/deploy.sh --strategy=rolling --environment=production
```

**Timeline**:
1. Backup (30s)
2. Pull images (2m)
3. Update backend (30s)
4. Health check (30s)
5. Update frontend (30s)
6. Final health check (30s)

**Total**: ~5 minutes, ~10 seconds downtime

### Blue-Green Deployment

**Use Case**: Zero-downtime deployments, instant rollback

**Command**:
```bash
./scripts/deploy.sh --strategy=blue-green --environment=production
```

**Timeline**:
1. Backup (30s)
2. Pull images (2m)
3. Start green environment (1m)
4. Health check green (1m)
5. Switch traffic (instant)
6. Stop blue environment (30s)

**Total**: ~5 minutes, zero downtime

### Canary Deployment

**Use Case**: Gradual rollout, risk mitigation

**Command**:
```bash
# Step 1: Deploy canary (10% traffic)
./scripts/deploy.sh --strategy=canary --environment=production

# Step 2: Monitor for 5-10 minutes
# Watch metrics, logs, error rates

# Step 3: Promote or rollback
./scripts/deploy.sh --promote-canary  # If successful
./scripts/rollback.sh                 # If issues detected
```

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (`npm run test`, `pytest`)
- [ ] Code linted (`ruff check .`, `eslint src`)
- [ ] No security vulnerabilities (`npm audit`, `safety check`)
- [ ] Code reviewed and approved

### Infrastructure

- [ ] Database backup recent (<24h)
- [ ] Sufficient disk space (>10GB free)
- [ ] Server resources available (CPU <70%, RAM <80%)
- [ ] Dependencies up to date

### Configuration

- [ ] Environment variables configured
- [ ] Secrets properly set
- [ ] Feature flags reviewed
- [ ] Email settings tested

### Testing

- [ ] Tested in development
- [ ] Tested in staging
- [ ] Smoke tests prepared
- [ ] Rollback plan ready

## Post-Deployment Checklist

### Immediate (0-5 minutes)

- [ ] Health check passed
- [ ] All containers running
- [ ] No errors in logs
- [ ] Frontend accessible
- [ ] Backend API responding

### Short-term (5-30 minutes)

- [ ] Authentication working (SSO login)
- [ ] Database queries successful
- [ ] Redis cache functioning
- [ ] Email sending working
- [ ] Billing integration active

### Long-term (30m - 24h)

- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify scheduled tasks
- [ ] Test all critical features
- [ ] Monitor user feedback

## Environment-Specific Instructions

### Development

```bash
# Use development configuration
cp config/development.env .env

# Run with hot reload
npm run dev

# Backend with auto-reload
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8084
```

### Staging

```bash
# Use staging configuration
cp config/staging.env .env.auth

# Deploy to staging
./scripts/deploy.sh \
  --environment=staging \
  --strategy=rolling \
  --tag=staging-$(git rev-parse --short HEAD)
```

### Production

```bash
# Use production configuration
cp config/production.env .env.auth

# Create release tag
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0

# Deploy with blue-green strategy
./scripts/deploy.sh \
  --environment=production \
  --strategy=blue-green \
  --tag=v2.1.0
```

## Rollback Procedures

### Automatic Rollback

Automatic rollback triggers on:
- Health check failure
- Deployment script error
- Critical service failure

```bash
# Deployment with automatic rollback (default)
./scripts/deploy.sh --rollback-on-failure

# Deployment without automatic rollback
./scripts/deploy.sh --no-rollback
```

### Manual Rollback

```bash
# Rollback to latest backup
./scripts/rollback.sh

# Rollback to specific backup
./scripts/rollback.sh --backup-timestamp=20251022_153000

# Interactive rollback (prompts for confirmation)
./scripts/rollback.sh

# Non-interactive rollback (CI/CD)
./scripts/rollback.sh < /dev/null
```

### Rollback Verification

After rollback:
```bash
# Run health check
./scripts/health_check.sh

# Check service version
curl https://your-domain.com/api/v1/system/status | jq '.version'

# Verify database state
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM users;"

# Check logs for errors
docker logs ops-center-direct --since 5m | grep -i error
```

## Troubleshooting

### Deployment Fails

**Symptom**: Deployment script exits with error

**Solutions**:

1. Check prerequisites:
```bash
# Docker running?
docker info

# Disk space?
df -h

# Network connectivity?
ping ghcr.io
```

2. Review logs:
```bash
# Deployment log
cat /opt/ops-center/deployment/deploy.log

# Container logs
docker logs ops-center-direct --tail 100
```

3. Verify environment:
```bash
# Check .env file
cat .env.auth | grep -v PASSWORD

# Test database connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"
```

### Health Check Fails

**Symptom**: `./scripts/health_check.sh` returns errors

**Solutions**:

1. Check individual services:
```bash
# Backend
curl http://localhost:8084/api/v1/health

# Database
docker exec unicorn-postgresql pg_isready

# Redis
docker exec unicorn-redis redis-cli ping
```

2. Review service logs:
```bash
# Backend errors
docker logs ops-center-direct | grep -i error

# Database errors
docker logs unicorn-postgresql | grep -i error
```

3. Verify configuration:
```bash
# Check environment variables
docker exec ops-center-direct env | grep -E "POSTGRES|REDIS|KEYCLOAK"
```

### Database Migration Fails

**Symptom**: Migration errors during deployment

**Solutions**:

1. Restore database backup:
```bash
# Find latest backup
ls -lh /opt/ops-center/backups/db_backup_*

# Restore
docker exec -i unicorn-postgresql psql -U unicorn unicorn_db < /opt/ops-center/backups/db_backup_TIMESTAMP.sql
```

2. Run migration manually:
```bash
# Access container
docker exec -it ops-center-direct bash

# Run migration
python -m alembic upgrade head

# Or run specific migration
python -m alembic upgrade +1
```

3. Check migration status:
```bash
docker exec ops-center-direct python -m alembic current
```

### Service Won't Start

**Symptom**: Container exits immediately

**Solutions**:

1. Check logs:
```bash
docker logs ops-center-direct
```

2. Test command manually:
```bash
docker run -it --rm \
  --env-file .env.auth \
  ops-center-backend:latest \
  bash

# Inside container
uvicorn server:app --host 0.0.0.0 --port 8084
```

3. Verify dependencies:
```bash
# Check if dependencies are accessible
docker exec ops-center-direct ping unicorn-postgresql
docker exec ops-center-direct nc -zv unicorn-postgresql 5432
```

## Security Considerations

### Secrets Management

**Never commit secrets**:
```bash
# Add to .gitignore
echo ".env*" >> .gitignore
echo "!.env.example" >> .gitignore

# Use GitHub Secrets for CI/CD
gh secret set POSTGRES_PASSWORD --body "your-password"
```

**Rotate secrets regularly**:
```bash
# Generate new secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET

# Update in .env.auth
# Restart services
docker compose restart
```

### SSL/TLS

**Use Traefik for automatic SSL**:
```yaml
# docker-compose.prod.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.ops-center.tls=true"
  - "traefik.http.routers.ops-center.tls.certresolver=letsencrypt"
```

**Or use custom certificates**:
```bash
# Copy certificates
cp your-cert.crt /opt/ops-center/certs/
cp your-key.key /opt/ops-center/certs/

# Configure Nginx
# See docker/nginx.conf
```

### Network Security

**Firewall rules**:
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Block direct access to backend
sudo ufw deny 8084/tcp
```

**Docker network isolation**:
```yaml
# docker-compose.prod.yml
networks:
  internal:
    internal: true  # No external access
  web:
    external: true  # Internet-facing
```

## Performance Optimization

### Database

```bash
# Configure connection pool
DB_POOL_MIN=5
DB_POOL_MAX=20

# Enable query caching
CACHE_TTL_LONG=3600
```

### Redis

```bash
# Configure Redis memory
docker run -d \
  --name unicorn-redis \
  redis:7-alpine \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru
```

### Frontend

```bash
# Enable Gzip compression (Nginx)
gzip on;
gzip_types text/css application/javascript;

# Set cache headers
expires 1y;
add_header Cache-Control "public, immutable";
```

## Monitoring

### Health Checks

```bash
# Automated monitoring
watch -n 30 './scripts/health_check.sh'

# Or with cron
echo "*/5 * * * * /opt/ops-center/deployment/scripts/health_check.sh" | crontab -
```

### Logs

```bash
# Follow logs
docker logs ops-center-direct -f

# Export logs
docker logs ops-center-direct > ops-center-$(date +%Y%m%d).log

# Log rotation
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  ops-center-backend
```

### Metrics

```bash
# Prometheus metrics (if enabled)
curl http://localhost:9090/metrics

# Resource usage
docker stats ops-center-direct

# Disk usage
du -sh /var/lib/docker/volumes/
```

## References

- [CI/CD Pipeline Documentation](./CI_CD_PIPELINE.md)
- [Rollback Guide](./ROLLBACK_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
