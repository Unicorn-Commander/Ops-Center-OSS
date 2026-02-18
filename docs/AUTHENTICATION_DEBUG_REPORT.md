# UC-1 Pro Authentication System - Debug Report
**Date**: October 3, 2025
**System**: ops-center-direct container
**Location**: /home/deploy/Production/UC-1-Pro/services/ops-center

## Executive Summary

Successfully identified and fixed **3 critical authentication issues** in the UC-1 Pro ops-center authentication system:

1. ✅ **OAuth Callback Error** - Fixed key mapping issue
2. ✅ **Database Schema** - Added password fields and made oauth_id nullable
3. ✅ **Redis Connection** - Updated to use correct Redis instance

## Issues Identified

### Issue 1: OAuth Authentication Failing
**Error Message**:
```
OAuth callback error: NOT NULL constraint failed: users.oauth_id
```

**Root Cause**:
The `oauth_manager.handle_callback()` returns user info with key `provider_user_id`, but the code was trying to access `user_info.get("id")` which doesn't exist.

**Fix Applied**:
- **File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py`
- **Line**: 344-348
- **Change**:
  ```python
  # OLD (BROKEN):
  oauth_id=user_info.get("id"),

  # NEW (FIXED):
  oauth_id=user_info.get("provider_user_id"),
  ```

### Issue 2: Database Schema Missing Password Fields
**Error Message**:
```
sqlite3.OperationalError: table users has no column named password_hash
```

**Root Cause**:
The database schema created by `init_database()` was missing `password_hash` and `password_salt` columns needed for password authentication. Additionally, `oauth_id` was marked as NOT NULL which prevented password-only users.

**Fix Applied**:
- **File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py`
- **Lines**: 169-191
- **Changes**:
  ```sql
  -- Added columns:
  password_hash TEXT,
  password_salt TEXT,

  -- Made nullable (removed NOT NULL):
  oauth_provider TEXT,
  oauth_id TEXT,
  ```

### Issue 3: Redis Connection Failing
**Error Message**:
```
redis.exceptions.ConnectionError: Error -3 connecting to unicorn-redis:6379.
Temporary failure in name resolution.
```

**Root Cause**:
The container was configured to connect to `unicorn-redis:6379` but no container with that name exists. The actual Redis instance is `unicorn-lago-redis`.

**Fix Applied**:
- **File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/.env.auth`
- **Line**: 31
- **Change**:
  ```env
  # OLD:
  REDIS_URL=redis://unicorn-redis:6379/0

  # NEW:
  REDIS_URL=redis://unicorn-lago-redis:6379/0
  ```

### Issue 4: No Persistent Database Storage
**Root Cause**:
The docker-compose configuration didn't include a volume mapping, so the database was lost on every container restart.

**Fix Applied**:
- **File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/docker-compose.direct.yml`
- **Added**:
  ```yaml
  volumes:
    - ./data:/app/data
  ports:
    - "8000:8000"
  ```

## Files Modified

1. **/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py**
   - Fixed OAuth callback key mapping (line 346)
   - Updated database schema to include password fields (lines 175-191)

2. **/home/deploy/Production/UC-1-Pro/services/ops-center/.env.auth**
   - Updated Redis URL to unicorn-lago-redis (line 31)

3. **/home/deploy/Production/UC-1-Pro/services/ops-center/docker-compose.direct.yml**
   - Added env_file directive (line 10)
   - Added volume mapping (line 17)
   - Added port mapping (lines 18-19)

## Next Steps Required

### Step 1: Rebuild Docker Image
The Docker image `uc-1-pro-ops-center` needs to be rebuilt with the updated server.py:

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
docker build -t uc-1-pro-ops-center .
```

### Step 2: Recreate Container
```bash
docker compose -f docker-compose.direct.yml down
docker compose -f docker-compose.direct.yml up -d
```

### Step 3: Initialize Database and Create Admin User

**Option A: Let server initialize on startup** (preferred)
The server will automatically create the database schema on startup. Just wait 5 seconds after container starts.

**Option B: Manual initialization** (if startup fails)
Run this Python script inside the container:

```bash
docker exec ops-center-direct python3 << 'EOF'
import sqlite3
import hashlib
import secrets

def hash_password(password, salt=None):
    pepper = "UC1Pro_Pepper_2025"
    if not salt:
        salt = secrets.token_hex(32)
    combined = f"{password}{salt}{pepper}"
    hashed = combined
    for _ in range(10000):
        hashed = hashlib.sha256(hashed.encode()).hexdigest()
    return hashed, salt

# Connect to database
conn = sqlite3.connect("/app/data/ops_center.db")
cursor = conn.cursor()

# Create schema
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    oauth_provider TEXT,
    oauth_id TEXT,
    password_hash TEXT,
    password_salt TEXT,
    subscription_tier TEXT DEFAULT 'trial',
    stripe_customer_id TEXT,
    lago_customer_id TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_stripe ON users(stripe_customer_id)")

# Create admin user
user_id = secrets.token_urlsafe(16)
password_hash, salt = hash_password("your-admin-password")

cursor.execute("""
INSERT INTO users (id, email, name, oauth_provider, oauth_id, password_hash, password_salt, subscription_tier, is_admin)
VALUES (?, ?, ?, 'password', ?, ?, ?, 'enterprise', 1)
""", (user_id, "admin@example.com", "Admin User", user_id, password_hash, salt))

conn.commit()
print("✓ Database initialized and admin user created")
print(f"  Email: admin@example.com")
print(f"  Password: your-admin-password")
print(f"  Tier: enterprise")
print(f"  Is Admin: True")
conn.close()
EOF
```

### Step 4: Test Authentication

**Test Password Login:**
```bash
curl -X POST http://localhost:8000/auth/login/password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your-admin-password"}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "redirect": "/dashboard"
}
```

**Test OAuth Login:**
1. Visit: http://localhost:8000/auth/login/google
2. Complete Google OAuth flow
3. Should redirect to /dashboard with session cookie

## SQL Commands for Direct Database Access

### Check Existing Users
```sql
SELECT id, email, name, oauth_provider, subscription_tier, is_admin
FROM users;
```

### Create Admin User Manually
```sql
-- Note: password_hash and password_salt must be generated using the Python script above
INSERT INTO users (
    id,
    email,
    name,
    oauth_provider,
    oauth_id,
    password_hash,
    password_salt,
    subscription_tier,
    is_admin
) VALUES (
    'admin_user_id_12345',
    'admin@example.com',
    'Admin User',
    'password',
    'admin_user_id_12345',
    '<generated_password_hash>',
    '<generated_salt>',
    'enterprise',
    1
);
```

### Update User to Admin
```sql
UPDATE users
SET is_admin = 1, subscription_tier = 'enterprise'
WHERE email = 'admin@example.com';
```

### Delete User
```sql
DELETE FROM users WHERE email = 'admin@example.com';
```

## Verification Checklist

- [ ] Docker image rebuilt with updated server.py
- [ ] Container recreated with new configuration
- [ ] Database file exists at `/app/data/ops_center.db`
- [ ] Admin user exists in database
- [ ] Password login works (returns success=true)
- [ ] OAuth login works (redirects to dashboard)
- [ ] Session cookie is set correctly
- [ ] Redis connection succeeds (no error logs)

## Container Configuration Summary

**Network**:
- unicorn-network (for Redis and service communication)
- web (for Traefik)

**Environment Variables**:
- Loaded from `.env.auth` file
- REDIS_URL=redis://unicorn-lago-redis:6379/0
- EXTERNAL_HOST=unicorncommander.ai
- EXTERNAL_PROTOCOL=https

**Volumes**:
- ./data:/app/data (persistent database storage)

**Ports**:
- 8000:8000 (FastAPI server)

**Access URLs**:
- HTTP: http://localhost:8000
- HTTPS: https://unicorncommander.ai (via Traefik)

## Troubleshooting

### If password login still fails:
1. Check logs: `docker logs ops-center-direct | tail -50`
2. Verify user exists: `docker exec ops-center-direct python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/ops_center.db'); print(conn.execute('SELECT * FROM users').fetchall())"`
3. Test Redis connection: `docker exec ops-center-direct python3 -c "import redis; r = redis.from_url('redis://unicorn-lago-redis:6379/0'); print(r.ping())"`

### If OAuth login fails:
1. Check OAuth credentials in `.env.auth`
2. Verify redirect URI matches what's configured in Google/GitHub/Microsoft OAuth apps
3. Check browser console for CORS errors

### If database is empty:
1. Trigger initialization: `curl http://localhost:8000/`
2. Check if /app/data is writable: `docker exec ops-center-direct touch /app/data/test`
3. Run manual initialization script from Step 3

## Conclusion

All authentication issues have been identified and fixes have been applied to the codebase. The remaining step is to **rebuild the Docker image** and restart the container for changes to take effect.

**Estimated time to complete**: 5-10 minutes

**Success criteria**:
- ✅ Admin user can login with password
- ✅ Users can login with Google OAuth
- ✅ Session persists across requests
- ✅ Database persists across container restarts
