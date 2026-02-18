# Epic 1.8: Credit & Usage Metering System - Bugs Found

**Date**: October 24, 2025
**Tester**: QA Team Lead (Claude)
**Total Bugs**: 1
**P0 Blockers**: 1
**Status**: ❌ **CRITICAL - Deployment Blocked**

---

## Bug Summary

| ID | Severity | Component | Status | Description |
|----|----------|-----------|--------|-------------|
| #1 | P0 (Blocker) | credit_system.py | 🔴 Open | SQL INSERT mismatch prevents user credit creation |

---

## Bug #1: SQL INSERT Statement Column/Value Mismatch 🚨

**Severity**: P0 (BLOCKER)
**Component**: `backend/credit_system.py`
**Function**: `create_user_credits()` (lines 162-173)
**Reported**: October 24, 2025

### Description

The `create_user_credits()` function has a SQL INSERT statement that specifies 4 columns but provides 6 values, causing a PostgreSQL error: `"INSERT has more expressions than target columns"`

### Impact

- 🔴 **CRITICAL** - Blocks entire credit system
- Prevents any user from accessing `/api/v1/credits/balance` endpoint
- Breaks authentication flow for credit-dependent features
- Affects 100% of users attempting to use credit features
- Blocks all P1 and P2 testing

### Steps to Reproduce

1. Start ops-center backend
2. Make request to `GET /api/v1/credits/balance`
3. Backend attempts to create user credits (if user doesn't exist)
4. SQL INSERT statement fails with column mismatch error

### Error Message

```json
{"detail": "INSERT has more expressions than target columns"}
```

### Backend Log

```
ERROR:credit_api:Failed to get credit balance: INSERT has more expressions than target columns
```

### Root Cause

File: `backend/credit_system.py`, lines 162-173

**Buggy Code**:
```python
await conn.execute(
    """
    INSERT INTO user_credits (
        user_id, credits_remaining, credits_allocated,
         last_reset
    )
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (user_id) DO NOTHING
    """,
    user_id, allocated, allocated, Decimal("0.00"),
    Decimal("0.00"), last_reset
)
```

**Problem Analysis**:
- INSERT statement defines **4 columns**: `user_id`, `credits_remaining`, `credits_allocated`, `last_reset`
- VALUES clause provides **6 placeholders**: `$1, $2, $3, $4, $5, $6`
- Python passes **6 values**: `user_id`, `allocated`, `allocated`, `Decimal("0.00")`, `Decimal("0.00")`, `last_reset`

**Database Table Structure** (for reference):
```sql
CREATE TABLE user_credits (
    id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           varchar(255) NOT NULL UNIQUE,
    credits_remaining numeric(12,6) NOT NULL DEFAULT 0.0,
    credits_allocated numeric(12,6) NOT NULL DEFAULT 0.0,
    tier              varchar(50) NOT NULL DEFAULT 'free',
    monthly_cap       numeric(12,6),
    last_reset        timestamptz DEFAULT now(),
    created_at        timestamptz DEFAULT now(),
    updated_at        timestamptz DEFAULT now()
);
```

### Recommended Fix

**Option 1: Match columns to values** (Recommended)
```python
await conn.execute(
    """
    INSERT INTO user_credits (
        user_id, credits_remaining, credits_allocated,
        tier, last_reset
    )
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (user_id) DO NOTHING
    """,
    user_id, allocated, allocated, tier, last_reset
)
```

**Option 2: Use all columns explicitly**
```python
await conn.execute(
    """
    INSERT INTO user_credits (
        user_id, credits_remaining, credits_allocated,
        tier, monthly_cap, last_reset
    )
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (user_id) DO NOTHING
    """,
    user_id, allocated, allocated, tier,
    self._tier_allocations.get(tier, allocated), last_reset
)
```

**Option 3: Use DEFAULT for auto-generated columns**
```python
await conn.execute(
    """
    INSERT INTO user_credits (
        user_id, credits_remaining, credits_allocated, tier
    )
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (user_id) DO NOTHING
    """,
    user_id, allocated, allocated, tier
)
```

### Testing Required After Fix

1. ✅ Verify INSERT statement executes without errors
2. ✅ Test with fresh user (no existing credit record)
3. ✅ Test with existing user (ON CONFLICT clause)
4. ✅ Verify all columns populated correctly
5. ✅ Check default values for `created_at`, `updated_at`, `last_reset`
6. ✅ Re-run P0 authentication tests
7. ✅ Execute full P1 test suite

### Related Code

**Files to Review**:
- `backend/credit_system.py` (lines 142-198)
- `backend/credit_api.py` (line 276 calls `get_balance()`)
- Database migration that created `user_credits` table

**Similar Patterns to Check**:
Search for other INSERT statements in credit_system.py that might have the same issue:
```bash
grep -n "INSERT INTO" backend/credit_system.py
```

### Workaround

**For Testing**: Manually create user credit records in database:
```sql
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, last_reset
)
VALUES (
    'test-user-id', 5.00, 5.00, 'trial', NOW() + INTERVAL '30 days'
)
ON CONFLICT (user_id) DO NOTHING;
```

### Priority Justification

**Why P0 (Blocker)**:
1. **Affects Core Functionality** - Credit balance is fundamental to Epic 1.8
2. **Breaks All Users** - No user can access credit endpoints
3. **Blocks Testing** - Cannot test P1/P2 features without working P0
4. **Production Impact** - Would cause 100% failure rate in production
5. **No Workaround** - Users cannot bypass this error

---

## Bug Investigation Timeline

1. **10:00 AM** - Started P0 testing
2. **10:15 AM** - Database schema tests passed (100%)
3. **10:20 AM** - Public API tests passed (100%)
4. **10:25 AM** - Tested `/api/v1/credits/balance` endpoint
5. **10:26 AM** - Discovered SQL INSERT error
6. **10:30 AM** - Reviewed backend logs
7. **10:35 AM** - Located bug in `credit_system.py`
8. **10:40 AM** - Analyzed table structure vs INSERT statement
9. **10:45 AM** - Documented bug and recommended fixes
10. **10:50 AM** - Halted testing, reported blocker

---

## Additional Notes

### Code Quality Observations

1. **Good Practices**:
   - ✅ Using parameterized queries (prevents SQL injection)
   - ✅ Async/await pattern for database operations
   - ✅ Context manager for transaction management
   - ✅ Comprehensive error handling
   - ✅ Audit logging for credit operations

2. **Areas for Improvement**:
   - ❌ INSERT statement not validated against schema
   - ⚠️ Missing unit tests for `create_user_credits()`
   - ⚠️ No integration tests for credit creation
   - ⚠️ Consider using ORM (SQLAlchemy) to prevent column mismatches

### Recommendations

1. **Immediate**: Fix Bug #1 before any deployment
2. **Short-term**: Add unit tests for all database operations
3. **Medium-term**: Add CI/CD pipeline with automated testing
4. **Long-term**: Consider ORM to prevent similar issues

---

## Test Coverage Gaps Identified

The following areas lack adequate test coverage:

1. **Unit Tests**: No tests for `create_user_credits()` function
2. **Integration Tests**: No tests for first-time user credit creation
3. **Schema Validation**: No automated validation of INSERT statements
4. **Error Handling**: No tests for database constraint violations

**Recommendation**: Add pytest test suite covering all credit_system.py functions

---

## Attachments

- `EPIC_1.8_TEST_EXECUTION_REPORT.md` - Full test results
- `backend/credit_system.py` (lines 142-198) - Buggy code
- Backend logs showing error

---

**Report Generated**: October 24, 2025
**Next Review**: After Bug #1 is fixed
**Status**: 🔴 **OPEN - AWAITING FIX**
