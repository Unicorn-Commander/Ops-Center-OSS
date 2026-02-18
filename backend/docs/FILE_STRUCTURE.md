# Tier Enforcement - File Structure

## Directory Layout

```
/home/deploy/Production/UC-1-Pro/services/ops-center/
│
├── TIER_ENFORCEMENT_COMPLETE.md          # Main summary (this was the mission)
│
└── backend/
    ├── keycloak_integration.py           # NEW: Keycloak API client (16 KB)
    ├── tier_enforcement_middleware.py    # UPDATED: Uses Keycloak (7.8 KB)
    ├── usage_api.py                      # UPDATED: Uses Keycloak (8.2 KB)
    ├── server.py                         # UNCHANGED: Already integrated
    │
    ├── docs/
    │   ├── TIER_ENFORCEMENT_SETUP.md            # Setup and configuration guide
    │   ├── TIER_ENFORCEMENT_IMPLEMENTATION.md   # Implementation details
    │   ├── QUICK_TEST_GUIDE.md                  # Quick testing reference
    │   └── FILE_STRUCTURE.md                    # This file
    │
    └── tests/
        ├── test_tier_enforcement.py      # Python test suite (10 KB)
        └── test_tier_enforcement.sh      # Bash test script (5.4 KB)
```

## File Descriptions

### Core Implementation

#### `keycloak_integration.py` (NEW)
**Purpose**: Keycloak Admin API client for tier management
**Functions**:
- `get_admin_token()` - Authenticate with Keycloak
- `get_user_by_email(email)` - Retrieve user
- `get_user_tier_info(email)` - Get tier and usage
- `increment_usage(email, current)` - Increment API counter
- `reset_usage(email)` - Reset counter
- `set_subscription_tier(email, tier, status)` - Update tier
- `update_user_attributes(email, attrs)` - Update attributes

**Key Features**:
- Token caching (5 min expiry)
- Handles Keycloak array attributes
- Automatic daily reset
- Error handling

#### `tier_enforcement_middleware.py` (UPDATED)
**Purpose**: FastAPI middleware for tier enforcement
**Changes**: Replaced Authentik with Keycloak integration
**Flow**:
1. Extract user from session
2. Fetch tier from Keycloak
3. Check limits
4. Increment usage
5. Add headers

**Configuration**:
- Exempt paths: auth, webhooks, subscription, usage
- Tier limits: trial=100, starter=33, pro=333, enterprise=unlimited
- Service access: search, litellm (pro+), team (enterprise)

#### `usage_api.py` (UPDATED)
**Purpose**: REST API for usage information
**Changes**: Replaced Authentik calls with Keycloak integration
**Endpoints**:
- `GET /api/v1/usage/current` - Current usage stats
- `GET /api/v1/usage/limits` - All tier limits
- `GET /api/v1/usage/features` - Feature access
- `GET /api/v1/usage/history` - Historical data (TODO)
- `POST /api/v1/usage/reset-demo` - Reset (dev only)

### Documentation

#### `docs/TIER_ENFORCEMENT_SETUP.md`
**Audience**: System administrators, DevOps
**Contents**:
- Environment variables
- Keycloak user attributes
- Subscription tiers
- Setup instructions
- Troubleshooting guide
- Production considerations

#### `docs/TIER_ENFORCEMENT_IMPLEMENTATION.md`
**Audience**: Developers, technical leads
**Contents**:
- Implementation summary
- Architecture overview
- File descriptions
- Integration details
- API documentation
- Success criteria
- Future enhancements

#### `docs/QUICK_TEST_GUIDE.md`
**Audience**: QA, developers
**Contents**:
- Quick test commands
- Common scenarios
- Debugging commands
- Troubleshooting fixes
- Production checklist

#### `docs/FILE_STRUCTURE.md`
**Audience**: All (orientation)
**Contents**: This file - directory layout and file descriptions

### Tests

#### `tests/test_tier_enforcement.py`
**Purpose**: Comprehensive Python test suite
**Tests**:
1. Keycloak connection
2. User retrieval
3. Tier info retrieval
4. Usage reset
5. Usage increment
6. Tier change
7. Tier limits configuration
8. Middleware simulation

**Usage**:
```bash
python3 tests/test_tier_enforcement.py [email]
```

#### `tests/test_tier_enforcement.sh`
**Purpose**: Live API integration tests
**Tests**:
1. Authentication status
2. Current usage API
3. Tier limits API
4. Tier features API
5. Tier enforcement headers
6. Usage counter increment
7. Rate limit enforcement

**Usage**:
```bash
SESSION_FILE=/tmp/session.txt ./tests/test_tier_enforcement.sh
```

### Project Root

#### `TIER_ENFORCEMENT_COMPLETE.md`
**Purpose**: Main implementation summary and status report
**Contents**:
- Mission summary
- What was built
- Files created/modified
- Architecture diagram
- Configuration guide
- Testing instructions
- Success criteria
- Next steps

## Import Dependencies

```
keycloak_integration.py
    └── (imports: httpx, os, logging, typing, datetime)

tier_enforcement_middleware.py
    ├── from keycloak_integration import get_user_tier_info, increment_usage
    └── (imports: fastapi, starlette, logging, typing, os, datetime, json, asyncio)

usage_api.py
    ├── from keycloak_integration import get_user_tier_info, reset_usage
    └── (imports: fastapi, datetime, typing, os, logging)

server.py
    ├── from tier_enforcement_middleware import TierEnforcementMiddleware
    ├── from usage_api import router as usage_router
    └── (already configured, no changes needed)
```

## Data Flow

```
Client Request
    │
    ▼
TierEnforcementMiddleware
    │
    ├─► keycloak_integration.get_user_tier_info()
    │       │
    │       └─► Keycloak Admin API
    │               └─► User Attributes
    │
    ├─► Check Limits
    │
    ├─► keycloak_integration.increment_usage()
    │       │
    │       └─► Keycloak Admin API
    │               └─► Update User Attributes
    │
    └─► Add Headers & Continue
            │
            ▼
        Protected API Endpoint
            │
            ▼
        Response with X-Tier-* headers
```

## Configuration Files

### Environment Variables
```
.env (or docker-compose.yml environment section)
```

### Keycloak User Attributes
```
Keycloak Admin Console → Users → [User] → Attributes
- subscription_tier: ["trial"]
- subscription_status: ["active"]
- api_calls_used: ["0"]
- api_calls_reset_date: ["2025-10-10"]
```

## Testing Files

### Test Session File
```
/tmp/session.txt (created by curl -c)
```

### Test Output
```
stdout (for both Python and Bash tests)
```

## Log Files

### Application Logs
```bash
docker logs unicorn-ops-center
```

### Filtered Logs
```bash
docker logs unicorn-ops-center | grep -E "Tier|Keycloak|usage"
```

## Quick Access Commands

```bash
# Go to backend directory
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend

# View main implementation
less keycloak_integration.py

# View documentation
less docs/TIER_ENFORCEMENT_SETUP.md

# Run tests
python3 tests/test_tier_enforcement.py your@email.com
./tests/test_tier_enforcement.sh

# View logs
docker logs -f unicorn-ops-center | grep -E "Tier|Keycloak"
```

## File Sizes

```
keycloak_integration.py           16 KB
tier_enforcement_middleware.py    7.8 KB
usage_api.py                      8.2 KB
test_tier_enforcement.py          10 KB
test_tier_enforcement.sh          5.4 KB
TIER_ENFORCEMENT_SETUP.md        11 KB
TIER_ENFORCEMENT_IMPLEMENTATION.md 11 KB
QUICK_TEST_GUIDE.md              8 KB
```

**Total**: ~77 KB of code and documentation

## Quick Reference

| Need | File |
|------|------|
| Setup instructions | `docs/TIER_ENFORCEMENT_SETUP.md` |
| Quick testing | `docs/QUICK_TEST_GUIDE.md` |
| Implementation details | `docs/TIER_ENFORCEMENT_IMPLEMENTATION.md` |
| Status report | `../TIER_ENFORCEMENT_COMPLETE.md` |
| File layout | `docs/FILE_STRUCTURE.md` (this file) |

---

**Last Updated**: October 10, 2025
