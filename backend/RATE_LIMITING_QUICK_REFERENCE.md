# Rate Limiting Quick Reference

## Installation (3 Steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (copy and edit)
cp .env.ratelimit .env.ratelimit.local

# 3. Integrate into server.py
python scripts/integrate_rate_limiting.py
```

## Configuration (.env.ratelimit)

```bash
# Enable/disable
RATE_LIMIT_ENABLED=true

# Redis
REDIS_URL=redis://unicorn-lago-redis:6379/0

# Limits (format: "count/period")
RATE_LIMIT_AUTH=5/minute      # Auth endpoints
RATE_LIMIT_ADMIN=100/minute   # Admin endpoints
RATE_LIMIT_READ=200/minute    # Read endpoints
RATE_LIMIT_WRITE=50/minute    # Write endpoints

# Options
RATE_LIMIT_STRATEGY=sliding_window
RATE_LIMIT_ADMIN_BYPASS=true
RATE_LIMIT_FAIL_OPEN=true
```

## Usage

### Method 1: Decorator (Recommended)

```python
from rate_limiter import rate_limit

@app.post("/api/v1/auth/login")
@rate_limit("auth")
async def login(request: Request, creds: LoginCredentials):
    ...
```

### Method 2: Manual Check

```python
from rate_limiter import check_rate_limit_manual

@app.post("/api/v1/endpoint")
async def endpoint(request: Request):
    await check_rate_limit_manual(request, "write")
    ...
```

### Method 3: Global Middleware

```python
from rate_limiter import RateLimitMiddleware, rate_limiter

app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
```

## Categories

| Category | Default | Use For |
|----------|---------|---------|
| `auth` | 5/minute | Login, logout, password |
| `admin` | 100/minute | User mgmt, SSO, API keys |
| `read` | 200/minute | GET requests, status |
| `write` | 50/minute | POST/PUT/DELETE |
| `health` | No limit | Health checks |

## Testing

```bash
# Manual test
for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
  echo "Request $i"
done

# Check headers
curl -v http://localhost:8084/api/v1/services 2>&1 | grep -i ratelimit

# Run test suite
pytest tests/test_rate_limiting.py -v
```

## Response Format

### Success
```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 145
X-RateLimit-Reset: 1728475200
```

### Rate Limited (HTTP 429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 42 seconds.",
  "retry_after": 42
}
```

Headers:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728475200
Retry-After: 42
```

## Monitoring

```bash
# Check Redis
docker exec -it unicorn-lago-redis redis-cli
KEYS ratelimit:*
ZRANGE ratelimit:read:192.168.1.100 0 -1 WITHSCORES

# Check logs
docker logs unicorn-ops-center | grep -i "rate limit"
docker logs -f unicorn-ops-center | grep -i "exceeded"
```

## Common Issues

### Not Working?
```bash
# Check Redis
docker ps | grep redis
docker exec unicorn-lago-redis redis-cli ping

# Check config
cat .env.ratelimit | grep ENABLED

# Check logs
docker logs unicorn-ops-center | grep -i rate
```

### Too Strict?
```bash
# Increase limits
RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_READ=500/minute

# Or disable for dev
RATE_LIMIT_ENABLED=false
```

## Performance

- **Overhead**: 1-2ms per request
- **Throughput**: 10,000+ checks/second
- **Memory**: ~100 bytes per active key

## Files Reference

| File | Purpose |
|------|---------|
| `rate_limiter.py` | Core implementation |
| `.env.ratelimit` | Configuration |
| `requirements.txt` | Dependencies |
| `scripts/integrate_rate_limiting.py` | Auto-integration |
| `docs/RATE_LIMITING_README.md` | Full docs |
| `docs/RATE_LIMITING_INTEGRATION.md` | Integration guide |
| `tests/test_rate_limiting.py` | Test suite |
| `RATE_LIMITING_SUMMARY.md` | Implementation summary |

## Key Commands

```bash
# Integrate
python scripts/integrate_rate_limiting.py --dry-run
python scripts/integrate_rate_limiting.py

# Install deps
pip install -r requirements.txt

# Test
pytest tests/test_rate_limiting.py -v

# Restart
docker restart unicorn-ops-center

# Monitor
docker logs -f unicorn-ops-center
docker exec -it unicorn-lago-redis redis-cli MONITOR
```

## Need More?

- Full docs: `docs/RATE_LIMITING_README.md`
- Integration: `docs/RATE_LIMITING_INTEGRATION.md`
- Summary: `RATE_LIMITING_SUMMARY.md`
