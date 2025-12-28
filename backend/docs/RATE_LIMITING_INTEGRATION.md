# Rate Limiting Integration Guide

This document provides instructions for integrating the rate limiting system into server.py.

## Step 1: Add Import Statements

Add these imports after the existing imports (around line 50):

```python
# Rate limiting
try:
    from rate_limiter import rate_limiter, rate_limit, check_rate_limit_manual, RateLimitMiddleware
    RATE_LIMITING_ENABLED = True
except ImportError:
    print("Rate limiting not available")
    RATE_LIMITING_ENABLED = False
    rate_limit = lambda category: lambda func: func  # Dummy decorator
```

## Step 2: Initialize Rate Limiter on Startup

Add startup event handler after the app initialization (around line 140):

```python
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    if RATE_LIMITING_ENABLED:
        await rate_limiter.initialize()
        logger.info("Rate limiter initialized")

    # Other startup tasks...

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if RATE_LIMITING_ENABLED:
        await rate_limiter.close()
        logger.info("Rate limiter closed")

    # Other cleanup tasks...
```

## Step 3: Add Rate Limiting to Endpoints

Apply the `@rate_limit()` decorator to endpoints based on their category:

### Authentication Endpoints (5 requests/minute)

```python
@app.post("/api/v1/auth/login")
@rate_limit("auth")
async def login(request: Request, credentials: LoginCredentials):
    ...

@app.post("/api/v1/auth/logout")
@rate_limit("auth")
async def logout(request: Request):
    ...

@app.post("/api/v1/auth/change-password")
@rate_limit("auth")
async def change_password(request: Request, password_change: PasswordChange):
    ...

@app.get("/auth/login")
@rate_limit("auth")
async def auth_login(request: Request):
    ...

@app.post("/auth/direct-login")
@rate_limit("auth")
async def direct_login(request: Request):
    ...
```

### Admin Endpoints (100 requests/minute)

```python
@app.get("/api/v1/users")
@rate_limit("admin")
async def get_users(request: Request):
    ...

@app.post("/api/v1/users")
@rate_limit("admin")
async def create_user(request: Request, user: UserCreate):
    ...

@app.put("/api/v1/users/{user_id}")
@rate_limit("admin")
async def update_user(request: Request, user_id: str, user: UserUpdate):
    ...

@app.delete("/api/v1/users/{user_id}")
@rate_limit("admin")
async def delete_user(request: Request, user_id: str):
    ...

@app.get("/api/v1/api-keys")
@rate_limit("admin")
async def get_api_keys(request: Request):
    ...

@app.post("/api/v1/api-keys")
@rate_limit("admin")
async def create_api_key(request: Request, key_create: APIKeyCreate):
    ...

# SSO endpoints
@app.get("/api/v1/sso/users")
@rate_limit("admin")
async def get_sso_users(request: Request):
    ...

@app.post("/api/v1/sso/users")
@rate_limit("admin")
async def create_sso_user(request: Request, user: AuthentikUserCreate):
    ...

@app.put("/api/v1/sso/users/{user_id}")
@rate_limit("admin")
async def update_sso_user(request: Request, user_id: int, user: AuthentikUserUpdate):
    ...

@app.delete("/api/v1/sso/users/{user_id}")
@rate_limit("admin")
async def delete_sso_user(request: Request, user_id: int):
    ...
```

### Read Endpoints (200 requests/minute)

```python
@app.get("/api/v1/services")
@rate_limit("read")
async def get_services(request: Request):
    ...

@app.get("/api/v1/services/{container_name}/logs")
@rate_limit("read")
async def get_service_logs(request: Request, container_name: str):
    ...

@app.get("/api/v1/services/{container_name}/stats")
@rate_limit("read")
async def get_service_stats(request: Request, container_name: str):
    ...

@app.get("/api/v1/models")
@rate_limit("read")
async def get_models(request: Request):
    ...

@app.get("/api/v1/models/installed")
@rate_limit("read")
async def get_installed_models(request: Request):
    ...

@app.get("/api/v1/extensions")
@rate_limit("read")
async def get_extensions(request: Request):
    ...

@app.get("/api/v1/storage")
@rate_limit("read")
async def get_storage(request: Request):
    ...

@app.get("/api/v1/logs/sources")
@rate_limit("read")
async def get_log_sources(request: Request):
    ...

@app.get("/api/v1/settings")
@rate_limit("read")
async def get_settings(request: Request):
    ...

@app.get("/api/v1/landing/config")
@rate_limit("read")
async def get_landing_config(request: Request):
    ...
```

### Write Endpoints (50 requests/minute)

```python
@app.post("/api/v1/services/{container_name}/action")
@rate_limit("write")
async def service_action(request: Request, container_name: str, action: dict):
    ...

@app.post("/api/v1/models/download")
@rate_limit("write")
async def download_model(request: Request, model_request: ModelDownloadRequest):
    ...

@app.delete("/api/v1/models/{model_id:path}")
@rate_limit("write")
async def delete_model(request: Request, model_id: str):
    ...

@app.post("/api/v1/models/active")
@rate_limit("write")
async def set_active_model(request: Request, model_data: dict):
    ...

@app.put("/api/v1/models/{model_id:path}/config")
@rate_limit("write")
async def update_model_config(request: Request, model_id: str, config: dict):
    ...

@app.post("/api/v1/extensions/install")
@rate_limit("write")
async def install_extension(request: Request, extension: ExtensionInstallRequest):
    ...

@app.delete("/api/v1/extensions/{extension_id}")
@rate_limit("write")
async def uninstall_extension(request: Request, extension_id: str):
    ...

@app.post("/api/v1/backup/create")
@rate_limit("write")
async def create_backup(request: Request):
    ...

@app.put("/api/v1/settings")
@rate_limit("write")
async def update_settings(request: Request, settings: dict):
    ...

@app.post("/api/v1/landing/config")
@rate_limit("write")
async def update_landing_config(request: Request, config: dict):
    ...
```

### Health Check Endpoints (No Rate Limit)

These endpoints should NOT have rate limiting:

```python
@app.get("/api/v1/system/status")
async def system_status(request: Request):
    ...

@app.get("/health")
async def health_check():
    ...
```

## Step 4: Alternative - Use Middleware (Global Rate Limiting)

Instead of applying decorators to individual endpoints, you can use the middleware approach:

```python
# Add after other middleware (around line 140)
if RATE_LIMITING_ENABLED:
    from rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
    logger.info("Rate limiting middleware enabled")
```

This automatically applies rate limiting to all endpoints based on URL patterns.

## Step 5: Manual Rate Limit Checks

For complex scenarios where you need custom logic:

```python
from rate_limiter import check_rate_limit_manual

@app.post("/api/v1/custom-endpoint")
async def custom_endpoint(request: Request):
    # Get user info
    user_id = get_current_user_id(request)
    is_admin = check_if_admin(user_id)

    # Manually check rate limit
    await check_rate_limit_manual(
        request=request,
        category="write",
        user_id=user_id,
        is_admin=is_admin
    )

    # Continue with endpoint logic
    ...
```

## Configuration

1. Copy `.env.ratelimit` to your deployment directory
2. Adjust rate limits based on your needs
3. Set `RATE_LIMIT_ENABLED=true` to enable
4. For development, set `RATE_LIMIT_ENABLED=false` or use high limits

## Testing

Test rate limiting with curl:

```bash
# Test auth endpoint (5/minute limit)
for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "\nStatus: %{http_code}\n"
  echo "Request $i"
done

# Check headers
curl -v http://localhost:8084/api/v1/services \
  | grep -i "x-ratelimit"
```

Expected response when rate limited:

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

Check rate limit keys in Redis:

```bash
# Connect to Redis
docker exec -it unicorn-lago-redis redis-cli

# List all rate limit keys
KEYS ratelimit:*

# Check specific key
ZRANGE ratelimit:read:192.168.1.100 0 -1 WITHSCORES

# Monitor in real-time
MONITOR
```

## Troubleshooting

### Rate limiting not working

1. Check if Redis is running:
   ```bash
   docker ps | grep redis
   ```

2. Check environment variables:
   ```bash
   cat .env.ratelimit
   ```

3. Check logs:
   ```bash
   docker logs unicorn-ops-center | grep -i rate
   ```

### Redis connection errors

If Redis is unavailable and `RATE_LIMIT_FAIL_OPEN=true`, rate limiting is disabled automatically.

Set `RATE_LIMIT_FAIL_OPEN=false` to deny requests when Redis is down.

## Performance Considerations

- Redis operations are very fast (sub-millisecond)
- Sliding window uses sorted sets (efficient for time-based queries)
- Token bucket uses hash maps (constant time operations)
- Minimal overhead: ~1-2ms per request

## Security Best Practices

1. Use strict limits for authentication endpoints
2. Enable admin bypass for legitimate admin operations
3. Monitor rate limit violations in logs
4. Consider IP-based blocking for repeated violations
5. Use HTTPS to prevent header tampering
6. Combine with CSRF protection for write endpoints
