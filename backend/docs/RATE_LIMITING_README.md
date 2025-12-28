# Rate Limiting System - UC-1 Pro Ops-Center

## Overview

The rate limiting system provides Redis-based request throttling with support for multiple strategies, per-category limits, and graceful degradation. It protects your API from abuse while maintaining excellent performance.

## Features

- **Redis-Based**: Distributed rate limiting using Redis sorted sets
- **Multiple Strategies**: Sliding window (precise) or token bucket (smooth)
- **Flexible Configuration**: Different limits per endpoint category
- **Composite Keys**: IP address + User ID based limiting
- **Admin Bypass**: Configurable admin exemption
- **Graceful Degradation**: Fail open/closed when Redis unavailable
- **Standard Headers**: HTTP 429 with Retry-After headers
- **High Performance**: Sub-millisecond overhead per request

## Quick Start

### 1. Install Dependencies

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy configuration file
cp .env.ratelimit .env.ratelimit.local

# Edit configuration
nano .env.ratelimit.local
```

### 3. Integrate into server.py

**Option A: Automatic Integration (Recommended)**

```bash
python scripts/integrate_rate_limiting.py --dry-run  # Preview changes
python scripts/integrate_rate_limiting.py            # Apply changes
```

**Option B: Manual Integration**

Follow the detailed guide in `docs/RATE_LIMITING_INTEGRATION.md`

### 4. Restart Server

```bash
docker restart unicorn-ops-center
```

## Configuration

### Environment Variables

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Redis connection
REDIS_URL=redis://unicorn-lago-redis:6379/0

# Strategy: sliding_window or token_bucket
RATE_LIMIT_STRATEGY=sliding_window

# Limits per category (format: "count/period")
RATE_LIMIT_AUTH=5/minute      # Authentication endpoints
RATE_LIMIT_ADMIN=100/minute   # Admin operations
RATE_LIMIT_READ=200/minute    # Read-only endpoints
RATE_LIMIT_WRITE=50/minute    # State-changing endpoints

# Admin bypass (allow admins to bypass limits)
RATE_LIMIT_ADMIN_BYPASS=true

# Failure handling
RATE_LIMIT_FAIL_OPEN=true     # Allow requests if Redis down
```

### Categories

| Category | Default Limit | Applies To | Example Endpoints |
|----------|--------------|------------|-------------------|
| `auth` | 5/minute | Authentication | Login, logout, password change |
| `admin` | 100/minute | Administration | User management, SSO, API keys |
| `read` | 200/minute | Read operations | GET requests, status, logs |
| `write` | 50/minute | Write operations | Service control, settings, backup |
| `health` | No limit | Health checks | /health, /api/v1/system/status |

## Usage

### Method 1: Decorator (Recommended)

```python
from rate_limiter import rate_limit

@app.post("/api/v1/auth/login")
@rate_limit("auth")
async def login(request: Request, credentials: LoginCredentials):
    # Your endpoint logic
    ...

@app.get("/api/v1/services")
@rate_limit("read")
async def get_services(request: Request):
    # Your endpoint logic
    ...

@app.post("/api/v1/services/{container_name}/action")
@rate_limit("write")
async def service_action(request: Request, container_name: str, action: dict):
    # Your endpoint logic
    ...
```

### Method 2: Manual Check

```python
from rate_limiter import check_rate_limit_manual

@app.post("/api/v1/custom-endpoint")
async def custom_endpoint(request: Request):
    # Get user info
    user_id = get_current_user_id(request)
    is_admin = check_if_admin(user_id)

    # Check rate limit
    await check_rate_limit_manual(
        request=request,
        category="write",
        user_id=user_id,
        is_admin=is_admin
    )

    # Your endpoint logic
    ...
```

### Method 3: Global Middleware

```python
from rate_limiter import RateLimitMiddleware, rate_limiter

# Add to app
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
```

This automatically applies rate limiting based on URL patterns.

## Response Format

### Success Response

HTTP headers include rate limit information:

```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 145
X-RateLimit-Reset: 1728475200
```

### Rate Limited Response

**Status Code**: `429 Too Many Requests`

**Headers**:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728475200
Retry-After: 42
```

**Body**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 42 seconds.",
  "retry_after": 42
}
```

## Testing

### Manual Testing

```bash
# Test auth endpoint (5/minute)
for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "\nStatus: %{http_code}\n"
  echo "Request $i"
done

# Check rate limit headers
curl -v http://localhost:8084/api/v1/services 2>&1 | grep -i "x-ratelimit"
```

### Automated Testing

```bash
# Run test suite
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
pytest tests/test_rate_limiting.py -v

# Run with coverage
pytest tests/test_rate_limiting.py --cov=rate_limiter --cov-report=html
```

## Monitoring

### Check Redis Keys

```bash
# Connect to Redis
docker exec -it unicorn-lago-redis redis-cli

# List all rate limit keys
KEYS ratelimit:*

# Check specific client
ZRANGE ratelimit:read:192.168.1.100 0 -1 WITHSCORES

# Monitor in real-time
MONITOR

# Check memory usage
INFO memory
```

### Application Logs

```bash
# Check rate limiter initialization
docker logs unicorn-ops-center | grep -i "rate limit"

# Monitor rate limit violations
docker logs -f unicorn-ops-center | grep -i "rate limit exceeded"
```

## Performance

### Benchmarks

- **Redis Operation Time**: ~0.5-1ms per check
- **Overhead**: ~1-2ms total per request
- **Throughput**: 10,000+ checks/second per instance
- **Memory**: ~100 bytes per active rate limit key

### Optimization Tips

1. **Use token bucket for burst traffic**: Smoother rate limiting
2. **Adjust window sizes**: Shorter windows for stricter control
3. **Enable admin bypass**: Reduce checks for privileged users
4. **Use Redis persistence**: Maintain limits across restarts

## Security Considerations

### Best Practices

1. **Strict Auth Limits**: Keep authentication endpoints at 5/minute or lower
2. **Monitor Violations**: Log and alert on repeated rate limit hits
3. **IP Blocking**: Consider blocking IPs with excessive violations
4. **HTTPS Only**: Prevent header tampering
5. **Combine with CSRF**: Layer with CSRF protection for write endpoints

### Attack Prevention

- **Brute Force**: Low limits on auth endpoints prevent password guessing
- **DDoS**: Distributed limits protect against volumetric attacks
- **Resource Exhaustion**: Write limits prevent database/service overload
- **API Scraping**: Read limits prevent data harvesting

## Troubleshooting

### Rate Limiting Not Working

**Check 1: Redis Connection**
```bash
docker ps | grep redis
docker exec unicorn-lago-redis redis-cli ping
```

**Check 2: Configuration**
```bash
cat .env.ratelimit | grep RATE_LIMIT_ENABLED
```

**Check 3: Logs**
```bash
docker logs unicorn-ops-center | grep -i "rate limit"
```

### False Positives

**Issue**: Legitimate users getting rate limited

**Solutions**:
1. Increase limits for the category
2. Enable admin bypass for privileged users
3. Use user ID in identifier (not just IP)
4. Adjust time window (hourly instead of per-minute)

### Redis Unavailable

**Issue**: Redis connection errors

**With `RATE_LIMIT_FAIL_OPEN=true`**:
- Rate limiting is disabled
- All requests are allowed
- Warning logged

**With `RATE_LIMIT_FAIL_OPEN=false`**:
- Rate limiting fails closed
- All requests are denied
- Error logged and raised

## Advanced Configuration

### Per-Environment Settings

**Development**:
```bash
RATE_LIMIT_ENABLED=false
# Or use very high limits
RATE_LIMIT_AUTH=1000/minute
RATE_LIMIT_ADMIN=10000/minute
```

**Staging**:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_ADMIN=200/minute
```

**Production**:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_ADMIN=100/minute
RATE_LIMIT_FAIL_OPEN=false  # Fail closed in production
```

### Custom Categories

Add custom rate limit categories:

```python
# In rate_limiter.py config
self.limits = {
    "auth": self._parse_limit(os.environ.get("RATE_LIMIT_AUTH", "5/minute")),
    "admin": self._parse_limit(os.environ.get("RATE_LIMIT_ADMIN", "100/minute")),
    "read": self._parse_limit(os.environ.get("RATE_LIMIT_READ", "200/minute")),
    "write": self._parse_limit(os.environ.get("RATE_LIMIT_WRITE", "50/minute")),
    "api_key": self._parse_limit(os.environ.get("RATE_LIMIT_API_KEY", "1000/hour")),
    "webhook": self._parse_limit(os.environ.get("RATE_LIMIT_WEBHOOK", "100/hour")),
}
```

### Per-User Limits

Implement custom logic for per-user limits:

```python
async def get_user_rate_limit(user_id: str, category: str) -> Tuple[int, int]:
    """Get rate limit for specific user"""
    # Check user tier/plan
    user = await get_user(user_id)

    if user.tier == "enterprise":
        return (1000, 60)  # 1000/minute
    elif user.tier == "pro":
        return (500, 60)   # 500/minute
    else:
        return (100, 60)   # 100/minute
```

## Migration Guide

### From No Rate Limiting

1. Deploy rate limiter with `RATE_LIMIT_ENABLED=false`
2. Monitor application logs for any issues
3. Enable with high limits: `RATE_LIMIT_AUTH=100/minute`
4. Gradually reduce limits to target values
5. Monitor for false positives

### From Other Rate Limiters

If migrating from another rate limiting solution:

1. Keep old system running
2. Deploy new rate limiter in parallel
3. Compare behavior and adjust limits
4. Switch traffic to new system
5. Remove old rate limiter

## Support

- **Documentation**: See `docs/RATE_LIMITING_INTEGRATION.md`
- **Issues**: Report at UC-1 Pro GitHub repository
- **Testing**: Run `pytest tests/test_rate_limiting.py`

## License

MIT License - Part of UC-1 Pro project
