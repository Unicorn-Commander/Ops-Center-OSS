# Redis Session Storage Integration

## Overview
Replaced in-memory session storage with Redis-backed persistent sessions for UC-Cloud Ops Center.

## Configuration

### Redis Connection
- **Host**: `unicorn-lago-redis` (container name)
- **Port**: `6379`
- **Database**: `0`
- **Session TTL**: `7200` seconds (2 hours)

### Environment Variables
```bash
REDIS_HOST=unicorn-lago-redis
REDIS_PORT=6379
REDIS_DB=0
SESSION_TTL=7200
SESSION_KEY_PREFIX=session:
```

## Files Modified

### 1. `/backend/redis_session.py` (NEW)
Redis session manager with full dict-like interface:
- `set(session_id, data)` - Store session with TTL
- `get(session_id)` - Retrieve session
- `delete(session_id)` - Remove session
- `exists(session_id)` - Check if session exists
- `refresh(session_id)` - Reset TTL
- `count()` - Count active sessions
- Supports dict-style operations: `sessions[id]`, `id in sessions`, `del sessions[id]`

### 2. `/backend/server.py`
**Line 70**: Added import
```python
from redis_session import redis_session_manager
```

**Line 111**: Replaced in-memory dict
```python
# Old: sessions = {}
# New:
sessions = redis_session_manager
```

**Line 1037**: Updated get_current_user to save session changes back to Redis
```python
session["user"] = user_data
sessions[session_token] = session  # Save back to Redis
```

### 3. `/backend/csrf_protection.py`
**Line 191**: Added save back to Redis after generating CSRF token
```python
session["csrf_token"] = csrf_token
self.sessions_store[session_token] = session  # Save back to Redis
```

### 4. `/backend/test_redis_session.py` (NEW)
Comprehensive test suite for Redis session operations:
- Connection test
- CRUD operations
- Dict-style access
- TTL verification
- All tests passing ✓

## Session Storage Format

Sessions are stored as JSON strings in Redis:
```json
{
  "user": {
    "username": "aaron",
    "email": "aaron@example.com",
    "role": "admin",
    "sub": "user-uuid",
    "preferred_username": "aaron"
  },
  "access_token": "keycloak_access_token",
  "created": 1234567890.0,
  "csrf_token": "csrf_token_value"
}
```

Redis key format: `session:{session_token}`

## Benefits

1. **Persistence**: Sessions survive server restarts
2. **Scalability**: Supports horizontal scaling (multiple backend instances)
3. **Automatic Expiration**: TTL-based cleanup (2 hours)
4. **Performance**: Redis is optimized for session storage
5. **Memory Efficient**: Sessions stored in Redis, not process memory

## Testing

### Run Test Suite (inside container)
```bash
docker exec ops-center-direct python3 /app/test_redis_session.py
```

### Verify Connection
```bash
docker exec ops-center-direct python3 -c "from redis_session import redis_session_manager; print('Connected:', redis_session_manager._client.ping())"
```

### Check Active Sessions
```bash
docker exec unicorn-lago-redis redis-cli KEYS "session:*"
```

### View Session Data
```bash
docker exec unicorn-lago-redis redis-cli GET "session:{session_token}"
```

### Count Active Sessions
```bash
docker exec unicorn-lago-redis redis-cli DBSIZE
```

## Backward Compatibility

The Redis session manager implements a dict-like interface, ensuring backward compatibility with existing code:

- `if session_token in sessions:` ✓ Works
- `session = sessions[session_token]` ✓ Works  
- `sessions[session_token] = data` ✓ Works
- `del sessions[session_token]` ✓ Works
- `sessions.get(session_token)` ✓ Works (added method)

## Security

- Sessions auto-expire after 2 hours
- Session tokens are cryptographically secure (32-byte urlsafe random)
- Redis connection uses localhost/internal Docker network
- No authentication bypass - sessions still validated

## Deployment

The changes are **already deployed** in the `ops-center-direct` container:
- Server restarted successfully
- Redis connection verified
- All tests passing
- No errors in logs

## Monitoring

Check session metrics:
```bash
# Active sessions
docker exec ops-center-direct python3 -c "from redis_session import redis_session_manager; print('Active sessions:', redis_session_manager.count())"

# Redis memory usage
docker exec unicorn-lago-redis redis-cli INFO memory | grep used_memory_human
```

## Future Enhancements

1. Add session refresh on activity (extend TTL on each request)
2. Implement session cleanup job (remove expired sessions)
3. Add session analytics (login times, active users, etc.)
4. Support session migration (copy sessions between Redis instances)
5. Add Redis Sentinel support for high availability
