# Troubleshooting Guide

## Common Issues

### 1. Service Won't Start

#### Backend Container Exits Immediately

**Symptoms**:
```bash
$ docker ps | grep ops-center
# No results, or container shows "Exited"
```

**Diagnosis**:
```bash
# Check logs
docker logs ops-center-direct

# Check exit code
docker inspect ops-center-direct | grep ExitCode
```

**Common Causes**:

**A. Missing Environment Variables**
```bash
# Solution: Check required variables
docker exec ops-center-direct env | grep -E "POSTGRES|REDIS|KEYCLOAK"

# Add missing variables to .env.auth
vim .env.auth

# Restart container
docker restart ops-center-direct
```

**B. Database Connection Failed**
```bash
# Solution: Verify PostgreSQL is running
docker ps | grep postgresql

# Test connection
docker exec unicorn-postgresql pg_isready

# Check network
docker exec ops-center-direct ping unicorn-postgresql
```

**C. Port Already in Use**
```bash
# Solution: Check what's using port 8084
sudo lsof -i :8084

# Change port in docker-compose.yml or stop conflicting service
```

#### Frontend Container Exits

**Symptoms**:
```bash
$ curl http://localhost:80
curl: (7) Failed to connect
```

**Diagnosis**:
```bash
# Check Nginx configuration
docker logs ops-center-frontend

# Verify build artifacts exist
docker exec ops-center-frontend ls -la /usr/share/nginx/html/
```

**Solutions**:

**A. Missing Build Files**
```bash
# Rebuild frontend
npm run build
cp -r dist/* public/

# Rebuild container
docker build -f docker/Dockerfile.frontend -t ops-center-frontend:latest .
```

**B. Nginx Configuration Error**
```bash
# Test configuration
docker exec ops-center-frontend nginx -t

# Fix syntax errors in docker/nginx.conf
```

### 2. Health Check Failures

#### Database Health Check Fails

**Symptoms**:
```bash
$ ./scripts/health_check.sh --service=database
[✗] PostgreSQL database connection failed
```

**Diagnosis**:
```bash
# Check PostgreSQL status
docker ps | grep postgresql

# Check PostgreSQL logs
docker logs unicorn-postgresql --tail 50

# Test connection manually
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"
```

**Solutions**:

**A. PostgreSQL Not Running**
```bash
docker restart unicorn-postgresql
sleep 10
./scripts/health_check.sh --service=database
```

**B. Wrong Credentials**
```bash
# Check environment variables
docker exec ops-center-direct env | grep POSTGRES

# Update .env.auth with correct credentials
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=your-password
POSTGRES_DB=unicorn_db
```

**C. Database Doesn't Exist**
```bash
# Create database
docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_db;"

# Verify
docker exec unicorn-postgresql psql -U unicorn -c "\l"
```

#### Redis Health Check Fails

**Symptoms**:
```bash
$ ./scripts/health_check.sh --service=redis
[✗] Redis connection failed
```

**Solutions**:
```bash
# Restart Redis
docker restart unicorn-redis

# Test connection
docker exec unicorn-redis redis-cli ping
# Should return: PONG

# Check Redis configuration
docker exec ops-center-direct env | grep REDIS
```

#### Keycloak Health Check Fails

**Symptoms**:
```bash
$ ./scripts/health_check.sh --service=keycloak
[✗] Keycloak health check failed
```

**Solutions**:
```bash
# Check Keycloak status
docker ps | grep keycloak

# Test Keycloak endpoint
curl -I https://auth.your-domain.com/realms/uchub

# Verify Keycloak configuration
docker exec ops-center-direct env | grep KEYCLOAK
```

### 3. Authentication Issues

#### SSO Login Fails

**Symptoms**:
- Redirect loop
- "Invalid redirect_uri" error
- "Client not found" error

**Diagnosis**:
```bash
# Check Keycloak client configuration
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password $KEYCLOAK_ADMIN_PASSWORD

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get clients \
  --realm uchub | grep ops-center
```

**Solutions**:

**A. Fix Redirect URI**
```bash
# Update client redirect URIs
CLIENT_ID=$(docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get clients \
  --realm uchub --fields id,clientId | grep -B 1 '"clientId" : "ops-center"' | \
  grep '"id"' | cut -d'"' -f4)

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh update clients/$CLIENT_ID \
  --realm uchub \
  -s 'redirectUris=["https://your-domain.com/auth/callback","http://localhost:8084/auth/callback"]'
```

**B. Fix Client Secret**
```bash
# Regenerate client secret
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh create \
  clients/$CLIENT_ID/client-secret --realm uchub

# Update .env.auth with new secret
KEYCLOAK_CLIENT_SECRET=new-secret-here
```

#### Session Expired Errors

**Symptoms**:
- Frequent logouts
- "Session expired" messages

**Solutions**:
```bash
# Increase session timeout in .env.auth
SESSION_TIMEOUT=7200  # 2 hours

# Check Redis session store
docker exec unicorn-redis redis-cli KEYS "session:*"

# Clear old sessions
docker exec unicorn-redis redis-cli FLUSHDB
```

### 4. API Errors

#### 401 Unauthorized

**Symptoms**:
```bash
$ curl https://your-domain.com/api/v1/admin/users
{"detail":"Unauthorized"}
```

**Solutions**:

**A. Missing or Invalid Token**
```bash
# Login to get token
curl -X POST https://your-domain.com/auth/oidc/login

# Use token in requests
curl -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/admin/users
```

**B. Expired Token**
```bash
# Check token expiration
# JWT_EXPIRATION in .env.auth

# Refresh token or login again
```

#### 403 Forbidden

**Symptoms**:
```bash
$ curl -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/admin/users
{"detail":"Forbidden"}
```

**Solutions**:
```bash
# Check user role
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "SELECT email, roles FROM users WHERE email = 'your-email@example.com';"

# Assign admin role via Keycloak
# https://auth.your-domain.com/admin/uchub/console
# Users → Select user → Role mapping → Assign role: admin
```

#### 500 Internal Server Error

**Symptoms**:
```bash
$ curl https://your-domain.com/api/v1/admin/users
{"detail":"Internal Server Error"}
```

**Diagnosis**:
```bash
# Check backend logs
docker logs ops-center-direct --tail 50 | grep -i error

# Check error details
docker logs ops-center-direct --tail 100 | grep -A 10 "Internal Server Error"
```

**Common Causes**:

**A. Database Query Error**
```bash
# Check PostgreSQL logs
docker logs unicorn-postgresql | grep ERROR

# Verify database schema
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"
```

**B. Redis Connection Error**
```bash
# Restart Redis
docker restart unicorn-redis

# Clear cache
docker exec unicorn-redis redis-cli FLUSHALL
```

### 5. Deployment Issues

#### Docker Build Fails

**Symptoms**:
```bash
$ docker build -f docker/Dockerfile.backend -t test .
ERROR: failed to solve...
```

**Solutions**:

**A. Build Context Too Large**
```bash
# Check .dockerignore
cat .dockerignore

# Add more exclusions
echo "node_modules" >> .dockerignore
echo "*.tar.gz" >> .dockerignore

# Check build context size
tar -czf - . --exclude='.git' | wc -c
```

**B. Layer Cache Issues**
```bash
# Build without cache
docker build --no-cache -f docker/Dockerfile.backend -t test .
```

**C. Network Timeout**
```bash
# Increase build timeout
docker build --build-arg BUILDKIT_INLINE_CACHE=1 \
  --network=host \
  -f docker/Dockerfile.backend -t test .
```

#### Image Push Fails

**Symptoms**:
```bash
$ docker push ghcr.io/unicorn-commander/ops-center-backend:latest
unauthorized: authentication required
```

**Solutions**:
```bash
# Login to registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or use GitHub CLI
gh auth token | docker login ghcr.io -u USERNAME --password-stdin

# Verify credentials
docker logout ghcr.io
docker login ghcr.io
```

#### Deployment Timeout

**Symptoms**:
```bash
$ ./scripts/deploy.sh
[ERROR] Timeout waiting for Backend after 120s
```

**Solutions**:
```bash
# Increase timeout
./scripts/deploy.sh --timeout=300  # 5 minutes

# Check what's slow
docker logs ops-center-direct -f

# Check resource usage
docker stats
df -h
free -h
```

### 6. Performance Issues

#### Slow API Responses

**Symptoms**:
```bash
$ time curl https://your-domain.com/api/v1/admin/users
real    0m15.423s
```

**Diagnosis**:
```bash
# Check database query performance
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "EXPLAIN ANALYZE SELECT * FROM users LIMIT 100;"

# Check Redis hit rate
docker exec unicorn-redis redis-cli INFO stats | grep hit
```

**Solutions**:

**A. Missing Indexes**
```bash
# Add index to frequently queried columns
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "CREATE INDEX idx_users_email ON users(email);"

docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c \
  "CREATE INDEX idx_users_created_at ON users(created_at);"
```

**B. Cache Not Working**
```bash
# Verify Redis configuration
docker exec ops-center-direct env | grep CACHE_TTL

# Check cache size
docker exec unicorn-redis redis-cli INFO memory

# Clear and rebuild cache
docker exec unicorn-redis redis-cli FLUSHDB
```

**C. Too Many Workers**
```bash
# Reduce workers in production
# Edit docker/Dockerfile.backend
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8084", "--workers", "2"]
```

#### High Memory Usage

**Symptoms**:
```bash
$ docker stats ops-center-direct
CONTAINER           MEM USAGE / LIMIT
ops-center-direct   2.5GiB / 4GiB
```

**Solutions**:
```bash
# Limit container memory
docker update --memory="2g" --memory-swap="2g" ops-center-direct

# Or in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

### 7. Database Issues

#### Database Connection Pool Exhausted

**Symptoms**:
```bash
docker logs ops-center-direct | grep "connection pool exhausted"
```

**Solutions**:
```bash
# Increase pool size in .env.auth
DB_POOL_MIN=5
DB_POOL_MAX=20

# Restart backend
docker restart ops-center-direct
```

#### Migration Fails

**Symptoms**:
```bash
$ docker exec ops-center-direct python -m alembic upgrade head
ERROR: (psycopg2.errors.DuplicateTable)
```

**Solutions**:
```bash
# Check migration status
docker exec ops-center-direct python -m alembic current

# Stamp current version
docker exec ops-center-direct python -m alembic stamp head

# Or downgrade and re-run
docker exec ops-center-direct python -m alembic downgrade -1
docker exec ops-center-direct python -m alembic upgrade head
```

## Diagnostic Commands

### System Health

```bash
# Overall health check
./scripts/health_check.sh

# Individual services
./scripts/health_check.sh --service=database
./scripts/health_check.sh --service=redis
./scripts/health_check.sh --service=backend
./scripts/health_check.sh --service=frontend
```

### Logs

```bash
# Backend logs
docker logs ops-center-direct --tail 100 -f

# Database logs
docker logs unicorn-postgresql --tail 50

# Redis logs
docker logs unicorn-redis --tail 50

# All ops-center related logs
docker ps --filter "name=ops-center" --format "{{.Names}}" | \
  xargs -I {} docker logs {} --tail 20
```

### Resource Usage

```bash
# Container stats
docker stats --no-stream

# Disk usage
df -h
du -sh /var/lib/docker/volumes/*

# Memory usage
free -h

# CPU usage
top -b -n 1 | head -20
```

### Network

```bash
# Test connectivity
docker exec ops-center-direct ping unicorn-postgresql
docker exec ops-center-direct nc -zv unicorn-postgresql 5432

# List networks
docker network ls

# Inspect network
docker network inspect unicorn-network
```

## Getting Help

### Collect Diagnostic Information

```bash
#!/bin/bash
# diagnostic_report.sh

REPORT_DIR="/tmp/ops-center-diagnostic-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

# System info
uname -a > "$REPORT_DIR/system_info.txt"
docker version >> "$REPORT_DIR/system_info.txt"
docker compose version >> "$REPORT_DIR/system_info.txt"

# Container status
docker ps -a > "$REPORT_DIR/containers.txt"

# Logs
docker logs ops-center-direct --tail 200 > "$REPORT_DIR/backend.log" 2>&1
docker logs unicorn-postgresql --tail 100 > "$REPORT_DIR/postgresql.log" 2>&1
docker logs unicorn-redis --tail 100 > "$REPORT_DIR/redis.log" 2>&1

# Resource usage
docker stats --no-stream > "$REPORT_DIR/resource_usage.txt"
df -h > "$REPORT_DIR/disk_usage.txt"
free -h > "$REPORT_DIR/memory_usage.txt"

# Configuration (sanitized)
cat .env.auth | grep -v PASSWORD | grep -v SECRET > "$REPORT_DIR/config.txt"

# Create archive
tar -czf "$REPORT_DIR.tar.gz" -C /tmp "$(basename $REPORT_DIR)"

echo "Diagnostic report created: $REPORT_DIR.tar.gz"
```

### Support Channels

- **GitHub Issues**: https://github.com/Unicorn-Commander/Ops-Center/issues
- **Documentation**: `/home/muut/Production/UC-Cloud/services/ops-center/docs/`
- **Logs**: Check container logs first

## References

- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Rollback Guide](./ROLLBACK_GUIDE.md)
- [CI/CD Pipeline](./CI_CD_PIPELINE.md)
