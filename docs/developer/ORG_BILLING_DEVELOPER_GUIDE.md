# Organization Billing - Developer Guide

**Version**: 1.0.0
**Audience**: Backend developers, frontend developers, QA engineers
**Last Updated**: November 15, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development Setup](#local-development-setup)
3. [Testing Strategies](#testing-strategies)
4. [Common Development Scenarios](#common-development-scenarios)
5. [Debugging](#debugging)
6. [Performance Optimization](#performance-optimization)
7. [Common Pitfalls](#common-pitfalls)

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL client (`psql`) for database access
- Python 3.10+ for backend development
- Node.js 18+ for frontend development
- Valid Keycloak session token for API testing

### 5-Minute Setup

```bash
# 1. Navigate to ops-center
cd /opt/ops-center

# 2. Check database migration applied
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\dt org*"

# Should show:
# - organization_subscriptions
# - organization_credit_pools
# - user_credit_allocations
# - credit_usage_attribution
# - org_billing_history

# 3. Verify backend loaded org_billing_api.py
docker logs ops-center-direct | grep "Organization Billing API"

# Should show: "Organization Billing API endpoints registered"

# 4. Test API health
curl http://localhost:8084/api/v1/system/status

# 5. Create test organization
cat << 'EOF' | docker exec -i uchub-postgres psql -U unicorn -d unicorn_db
INSERT INTO organizations (id, org_name, slug, created_by)
VALUES ('test-dev-org', 'Developer Test Org', 'dev-test-org', 'test-user-123');

INSERT INTO organization_members (org_id, user_id, role, status)
VALUES ('test-dev-org', 'test-user-123', 'admin', 'active');

SELECT add_credits_to_pool('test-dev-org'::VARCHAR, 10000000::BIGINT, 100.00::DECIMAL);

SELECT allocate_credits_to_user(
    'test-dev-org'::VARCHAR,
    'test-user-123'::VARCHAR,
    5000000::BIGINT,
    'system'::VARCHAR
);
EOF

# 6. Verify setup
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
SELECT 'Pool' as type, total_credits/1000.0 as value
FROM organization_credit_pools WHERE org_id = 'test-dev-org'
UNION ALL
SELECT 'Allocation', allocated_credits/1000.0
FROM user_credit_allocations
WHERE org_id = 'test-dev-org' AND user_id = 'test-user-123';
"

# Expected output:
#   type    | value
# ----------+--------
#  Pool     | 10000
#  Allocation| 5000
```

✅ **You're ready to develop!**

---

## Local Development Setup

### Backend Development

#### Environment Setup

```bash
# Create Python virtual environment (optional)
cd /opt/ops-center/backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Running Backend Locally

```bash
# Option 1: Run in Docker (recommended)
docker restart ops-center-direct

# Option 2: Run locally for debugging
cd backend
uvicorn server:app --reload --port 8084

# With auto-reload on file changes
uvicorn server:app --reload --host 0.0.0.0 --port 8084
```

#### Hot Reload Development

```bash
# Edit backend files
vim backend/org_billing_api.py

# Changes auto-reload if using --reload flag
# Or manually restart container
docker restart ops-center-direct

# Check logs
docker logs ops-center-direct -f
```

### Frontend Development

#### Environment Setup

```bash
cd /opt/ops-center

# Install dependencies
npm install

# If adding new packages
npm install package-name --save
```

#### Running Frontend Locally

```bash
# Option 1: Development server with hot reload
npm run dev

# Access at: http://localhost:5173
# Auto-proxies API calls to http://localhost:8084

# Option 2: Build and deploy to public/
npm run build
cp -r dist/* public/

# Then access via ops-center container at http://localhost:8084
```

### Database Development

#### Direct PostgreSQL Access

```bash
# Interactive psql shell
docker exec -it uchub-postgres psql -U unicorn -d unicorn_db

# Run SQL file
cat migration.sql | docker exec -i uchub-postgres psql -U unicorn -d unicorn_db

# Query from bash
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM organizations;"
```

#### Schema Migrations

```bash
# 1. Create migration file
cat > backend/migrations/add_feature_xyz.sql << 'EOF'
-- Add new column to organization_credit_pools
ALTER TABLE organization_credit_pools
ADD COLUMN feature_xyz VARCHAR(255);

-- Create index
CREATE INDEX idx_org_credit_pools_feature_xyz
ON organization_credit_pools(feature_xyz);
EOF

# 2. Test migration (rollback)
docker exec -i uchub-postgres psql -U unicorn -d unicorn_db << 'EOF'
BEGIN;
\i /path/to/migration.sql
SELECT * FROM organization_credit_pools LIMIT 1;
ROLLBACK;
EOF

# 3. Apply migration
cat backend/migrations/add_feature_xyz.sql | docker exec -i uchub-postgres psql -U unicorn -d unicorn_db

# 4. Verify
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\d organization_credit_pools"
```

---

## Testing Strategies

### Unit Tests

#### Testing Database Functions

```python
# tests/test_org_billing_functions.py

import pytest
import asyncpg

@pytest.fixture
async def db_connection():
    """Create database connection for tests."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="unicorn",
        password="unicorn",
        database="unicorn_db"
    )
    yield conn
    await conn.close()

@pytest.mark.asyncio
async def test_has_sufficient_credits(db_connection):
    """Test has_sufficient_credits function."""
    # Setup: Create test org and allocation
    await db_connection.execute("""
        INSERT INTO organizations (id, org_name, slug, created_by)
        VALUES ('test-org-unit', 'Test Org', 'test-org-unit', 'test-user');
    """)

    await db_connection.execute("""
        SELECT add_credits_to_pool('test-org-unit', 10000000, 100.00);
    """)

    await db_connection.execute("""
        SELECT allocate_credits_to_user(
            'test-org-unit', 'test-user', 5000000, 'system'
        );
    """)

    # Test: Check sufficient credits
    result = await db_connection.fetchval("""
        SELECT has_sufficient_credits('test-org-unit', 'test-user', 1000000);
    """)

    assert result is True, "Should have sufficient credits"

    # Test: Check insufficient credits
    result = await db_connection.fetchval("""
        SELECT has_sufficient_credits('test-org-unit', 'test-user', 10000000);
    """)

    assert result is False, "Should not have sufficient credits"

    # Cleanup
    await db_connection.execute("""
        DELETE FROM user_credit_allocations WHERE org_id = 'test-org-unit';
        DELETE FROM organization_credit_pools WHERE org_id = 'test-org-unit';
        DELETE FROM organizations WHERE id = 'test-org-unit';
    """)

@pytest.mark.asyncio
async def test_deduct_credits_atomic(db_connection):
    """Test atomic credit deduction."""
    # Setup
    org_id = 'test-org-atomic'
    user_id = 'test-user-atomic'

    await db_connection.execute(f"""
        INSERT INTO organizations (id, org_name, slug, created_by)
        VALUES ('{org_id}', 'Test Atomic', '{org_id}', '{user_id}');
    """)

    await db_connection.execute(f"""
        SELECT add_credits_to_pool('{org_id}', 10000000, 100.00);
        SELECT allocate_credits_to_user('{org_id}', '{user_id}', 5000000, 'system');
    """)

    # Test: Successful deduction
    result = await db_connection.fetchrow(f"""
        SELECT * FROM deduct_credits(
            '{org_id}'::VARCHAR,
            '{user_id}'::VARCHAR,
            50000::BIGINT,
            'test'::VARCHAR,
            'test-model'::VARCHAR,
            'req-123'::VARCHAR,
            '{{}}'::JSONB
        );
    """)

    assert result['success'] is True, "Deduction should succeed"
    assert result['remaining_credits'] == 4950000, "Should have 4,950 credits remaining"

    # Test: Verify usage attribution recorded
    count = await db_connection.fetchval(f"""
        SELECT COUNT(*) FROM credit_usage_attribution
        WHERE org_id = '{org_id}' AND user_id = '{user_id}' AND request_id = 'req-123';
    """)

    assert count == 1, "Should have recorded usage attribution"

    # Cleanup
    await db_connection.execute(f"""
        DELETE FROM credit_usage_attribution WHERE org_id = '{org_id}';
        DELETE FROM user_credit_allocations WHERE org_id = '{org_id}';
        DELETE FROM organization_credit_pools WHERE org_id = '{org_id}';
        DELETE FROM organizations WHERE id = '{org_id}';
    """)
```

#### Running Unit Tests

```bash
# Run all tests
cd /opt/ops-center/backend
pytest tests/test_org_billing_functions.py -v

# Run specific test
pytest tests/test_org_billing_functions.py::test_has_sufficient_credits -v

# Run with coverage
pytest tests/test_org_billing_functions.py --cov=org_billing_api --cov-report=html
```

### Integration Tests

#### Testing API Endpoints

```python
# tests/test_org_billing_api.py

import pytest
from httpx import AsyncClient
from server import app

@pytest.mark.asyncio
async def test_create_subscription():
    """Test subscription creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/org-billing/subscriptions",
            json={
                "org_id": "test-api-org",
                "plan_code": "professional",
                "org_name": "Test API Org",
                "billing_email": "test@example.com",
                "initial_credits": 5000.0,
                "user_id": "test-user-api"
            },
            headers={"Cookie": "session_token=valid-test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['subscription']['org_id'] == "test-api-org"
        assert data['credit_pool']['total_credits'] == 5000.0

@pytest.mark.asyncio
async def test_allocate_credits():
    """Test credit allocation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/org-billing/credits/test-api-org/allocate",
            json={
                "user_id": "test-user-api",
                "credits": 2000.0
            },
            headers={"Cookie": "session_token=valid-test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['allocation']['allocated_credits'] == 2000.0
        assert data['pool_updated']['available_credits'] == 3000.0
```

### End-to-End Tests

#### Complete User Journey

```bash
#!/bin/bash
# tests/e2e_org_billing.sh

set -e

echo "🧪 E2E Test: Organization Billing Flow"

# 1. Create organization subscription
echo "1️⃣ Creating subscription..."
SUB_RESPONSE=$(curl -s -X POST http://localhost:8084/api/v1/org-billing/subscriptions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "org_id": "e2e-test-org",
    "plan_code": "professional",
    "org_name": "E2E Test Organization",
    "billing_email": "e2e@test.com",
    "initial_credits": 10000.0,
    "user_id": "e2e-user-123"
  }')

ORG_ID=$(echo $SUB_RESPONSE | jq -r '.subscription.org_id')
echo "✅ Subscription created: $ORG_ID"

# 2. Allocate credits to user
echo "2️⃣ Allocating credits to user..."
ALLOC_RESPONSE=$(curl -s -X POST http://localhost:8084/api/v1/org-billing/credits/$ORG_ID/allocate \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "user_id": "e2e-user-123",
    "credits": 5000.0
  }')

ALLOCATED=$(echo $ALLOC_RESPONSE | jq -r '.allocation.allocated_credits')
echo "✅ Allocated: $ALLOCATED credits"

# 3. Make LLM request
echo "3️⃣ Making LLM API request..."
LLM_RESPONSE=$(curl -s -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Test e2e billing"}
    ]
  }')

COST=$(echo $LLM_RESPONSE | jq -r '.headers["X-Cost-Incurred"]')
REMAINING=$(echo $LLM_RESPONSE | jq -r '.headers["X-Credits-Remaining"]')
echo "✅ LLM request completed. Cost: $COST, Remaining: $REMAINING"

# 4. Verify usage attribution
echo "4️⃣ Verifying usage attribution..."
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
  SELECT COUNT(*) as count
  FROM credit_usage_attribution
  WHERE org_id = '$ORG_ID' AND user_id = 'e2e-user-123';
" | grep -q "1" && echo "✅ Usage attributed correctly"

# 5. Get usage stats
echo "5️⃣ Getting usage statistics..."
USAGE_RESPONSE=$(curl -s "http://localhost:8084/api/v1/org-billing/credits/$ORG_ID/usage" \
  -H "Cookie: session_token=$SESSION_TOKEN")

TOTAL_USED=$(echo $USAGE_RESPONSE | jq -r '.total_credits_used')
echo "✅ Total credits used: $TOTAL_USED"

# 6. Cleanup
echo "6️⃣ Cleaning up test data..."
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "
  DELETE FROM credit_usage_attribution WHERE org_id = '$ORG_ID';
  DELETE FROM user_credit_allocations WHERE org_id = '$ORG_ID';
  DELETE FROM organization_credit_pools WHERE org_id = '$ORG_ID';
  DELETE FROM organization_subscriptions WHERE org_id = '$ORG_ID';
  DELETE FROM organization_members WHERE org_id = '$ORG_ID';
  DELETE FROM organizations WHERE id = '$ORG_ID';
"
echo "✅ Cleanup complete"

echo ""
echo "🎉 All E2E tests passed!"
```

Run the E2E test:

```bash
SESSION_TOKEN="your-valid-session-token" bash tests/e2e_org_billing.sh
```

### Load Testing

#### Concurrent Credit Deductions

```python
# tests/load_test_credit_deductions.py

import asyncio
import asyncpg
import time
from concurrent.futures import ThreadPoolExecutor

async def deduct_credits_worker(org_id: str, user_id: str, request_num: int):
    """Worker function to deduct credits."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="unicorn",
        password="unicorn",
        database="unicorn_db"
    )

    try:
        result = await conn.fetchrow("""
            SELECT * FROM deduct_credits(
                $1::VARCHAR, $2::VARCHAR, 50::BIGINT,
                'load_test'::VARCHAR, 'test-model'::VARCHAR,
                $3::VARCHAR, '{}'::JSONB
            )
        """, org_id, user_id, f"req-{request_num}")

        return result['success']

    finally:
        await conn.close()

async def load_test_concurrent_deductions(num_workers: int = 100):
    """Test concurrent credit deductions."""
    org_id = "load-test-org"
    user_id = "load-test-user"

    # Setup: Create org with credits
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="unicorn",
        password="unicorn",
        database="unicorn_db"
    )

    await conn.execute(f"""
        INSERT INTO organizations (id, org_name, slug, created_by)
        VALUES ('{org_id}', 'Load Test Org', '{org_id}', '{user_id}')
        ON CONFLICT DO NOTHING;
    """)

    await conn.execute(f"""
        SELECT add_credits_to_pool('{org_id}', 10000000, 100.00);
        SELECT allocate_credits_to_user('{org_id}', '{user_id}', 10000000, 'system');
    """)

    await conn.close()

    # Run concurrent deductions
    start_time = time.time()

    tasks = [
        deduct_credits_worker(org_id, user_id, i)
        for i in range(num_workers)
    ]

    results = await asyncio.gather(*tasks)

    end_time = time.time()

    # Verify results
    successes = sum(1 for r in results if r)
    failures = num_workers - successes

    print(f"\n🚀 Load Test Results:")
    print(f"  Workers: {num_workers}")
    print(f"  Successes: {successes}")
    print(f"  Failures: {failures}")
    print(f"  Time: {end_time - start_time:.2f}s")
    print(f"  Throughput: {num_workers / (end_time - start_time):.2f} req/s")

    # Verify final balance
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="unicorn",
        password="unicorn",
        database="unicorn_db"
    )

    final_used = await conn.fetchval(f"""
        SELECT used_credits / 1000.0
        FROM user_credit_allocations
        WHERE org_id = '{org_id}' AND user_id = '{user_id}';
    """)

    expected_used = successes * 0.05
    print(f"\n  Final credits used: {final_used}")
    print(f"  Expected: {expected_used}")
    print(f"  Difference: {abs(final_used - expected_used):.3f}")

    # Cleanup
    await conn.execute(f"""
        DELETE FROM credit_usage_attribution WHERE org_id = '{org_id}';
        DELETE FROM user_credit_allocations WHERE org_id = '{org_id}';
        DELETE FROM organization_credit_pools WHERE org_id = '{org_id}';
        DELETE FROM organizations WHERE id = '{org_id}';
    """)

    await conn.close()

    assert failures == 0, f"{failures} deductions failed"
    assert abs(final_used - expected_used) < 0.001, "Final balance mismatch"

# Run load test
if __name__ == "__main__":
    asyncio.run(load_test_concurrent_deductions(100))
```

Run load test:

```bash
python tests/load_test_credit_deductions.py
```

---

## Common Development Scenarios

### Scenario 1: Adding a New API Endpoint

```python
# backend/org_billing_api.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()

class CreditTransferRequest(BaseModel):
    from_user_id: str
    to_user_id: str
    credits: float

@router.post("/api/v1/org-billing/credits/{org_id}/transfer")
async def transfer_credits(
    org_id: str,
    transfer: CreditTransferRequest,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Transfer credits between users in the same organization.

    Requires org admin permission.
    """
    # Check permission
    is_admin = await check_org_admin(org_id, current_user['user_id'], db_pool)
    if not is_admin:
        raise HTTPException(403, "Org admin permission required")

    # Validate users belong to org
    async with db_pool.acquire() as conn:
        from_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM organization_members
                WHERE org_id = $1 AND user_id = $2 AND status = 'active'
            )
            """,
            org_id, transfer.from_user_id
        )

        to_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM organization_members
                WHERE org_id = $1 AND user_id = $2 AND status = 'active'
            )
            """,
            org_id, transfer.to_user_id
        )

        if not (from_exists and to_exists):
            raise HTTPException(400, "Both users must be members of the organization")

        # Execute transfer (atomic transaction)
        try:
            milicredits = int(transfer.credits * 1000)

            await conn.execute("BEGIN")

            # Deduct from source user
            from_remaining = await conn.fetchval(
                """
                UPDATE user_credit_allocations
                SET allocated_credits = allocated_credits - $3,
                    updated_at = NOW()
                WHERE org_id = $1 AND user_id = $2 AND is_active = TRUE
                  AND (allocated_credits - used_credits) >= $3
                RETURNING (allocated_credits - used_credits)
                """,
                org_id, transfer.from_user_id, milicredits
            )

            if from_remaining is None:
                raise HTTPException(400, "Insufficient credits to transfer")

            # Add to destination user
            await conn.execute(
                """
                UPDATE user_credit_allocations
                SET allocated_credits = allocated_credits + $3,
                    updated_at = NOW()
                WHERE org_id = $1 AND user_id = $2 AND is_active = TRUE
                """,
                org_id, transfer.to_user_id, milicredits
            )

            # Log transfer
            await conn.execute(
                """
                INSERT INTO credit_usage_attribution (
                    org_id, user_id, service_type, service_name,
                    credits_used, request_metadata
                ) VALUES (
                    $1, $2, 'credit_transfer', 'internal',
                    $3, $4
                )
                """,
                org_id, transfer.from_user_id, -milicredits,
                {
                    "transfer_to": transfer.to_user_id,
                    "transferred_by": current_user['user_id']
                }
            )

            await conn.execute("COMMIT")

        except Exception as e:
            await conn.execute("ROLLBACK")
            raise

    return {
        "success": True,
        "transferred_credits": transfer.credits,
        "from_user_id": transfer.from_user_id,
        "to_user_id": transfer.to_user_id
    }
```

### Scenario 2: Adding Database Migration

```bash
# 1. Create migration file
cat > backend/migrations/202511151200_add_credit_expiration.sql << 'EOF'
-- Add expiration tracking to credit allocations
ALTER TABLE user_credit_allocations
ADD COLUMN expires_at TIMESTAMPTZ,
ADD COLUMN auto_renew BOOLEAN DEFAULT FALSE;

-- Create index for expired allocations query
CREATE INDEX idx_user_allocations_expires
ON user_credit_allocations(expires_at)
WHERE is_active = TRUE;

-- Function to deactivate expired allocations
CREATE OR REPLACE FUNCTION deactivate_expired_allocations()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE user_credit_allocations
    SET is_active = FALSE
    WHERE is_active = TRUE
      AND expires_at IS NOT NULL
      AND expires_at < NOW()
    RETURNING COUNT(*) INTO v_count;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Add comment
COMMENT ON COLUMN user_credit_allocations.expires_at IS
    'When this allocation expires and becomes inactive';
EOF

# 2. Test migration
docker exec -i uchub-postgres psql -U unicorn -d unicorn_db << 'EOF'
BEGIN;
\i /app/migrations/202511151200_add_credit_expiration.sql
-- Test query
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'user_credit_allocations' AND column_name = 'expires_at';
ROLLBACK;
EOF

# 3. Apply migration
cat backend/migrations/202511151200_add_credit_expiration.sql | docker exec -i uchub-postgres psql -U unicorn -d unicorn_db

# 4. Verify
docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\d user_credit_allocations"
```

### Scenario 3: Adding Frontend Component

```jsx
// src/components/CreditTransferDialog.jsx

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  Alert
} from '@mui/material';

export function CreditTransferDialog({ open, onClose, orgId, users }) {
  const [fromUserId, setFromUserId] = useState('');
  const [toUserId, setToUserId] = useState('');
  const [credits, setCredits] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTransfer = async () => {
    setError('');
    setLoading(true);

    try {
      const response = await fetch(
        `/api/v1/org-billing/credits/${orgId}/transfer`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            from_user_id: fromUserId,
            to_user_id: toUserId,
            credits: parseFloat(credits)
          })
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Transfer failed');
      }

      onClose(true); // Success callback
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Transfer Credits</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <TextField
          select
          fullWidth
          label="From User"
          value={fromUserId}
          onChange={(e) => setFromUserId(e.target.value)}
          margin="normal"
        >
          {users.map(user => (
            <MenuItem key={user.user_id} value={user.user_id}>
              {user.user_email} ({user.remaining_credits} credits)
            </MenuItem>
          ))}
        </TextField>

        <TextField
          select
          fullWidth
          label="To User"
          value={toUserId}
          onChange={(e) => setToUserId(e.target.value)}
          margin="normal"
        >
          {users.filter(u => u.user_id !== fromUserId).map(user => (
            <MenuItem key={user.user_id} value={user.user_id}>
              {user.user_email}
            </MenuItem>
          ))}
        </TextField>

        <TextField
          type="number"
          fullWidth
          label="Credits to Transfer"
          value={credits}
          onChange={(e) => setCredits(e.target.value)}
          margin="normal"
          InputProps={{
            inputProps: { min: 0, step: 0.001 }
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onClose(false)} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleTransfer}
          variant="contained"
          disabled={!fromUserId || !toUserId || !credits || loading}
        >
          {loading ? 'Transferring...' : 'Transfer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## Debugging

### Backend Debugging

#### Enable Detailed Logging

```python
# backend/server.py

import logging

# Set log level to DEBUG
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger('org_billing_api').setLevel(logging.DEBUG)
logging.getLogger('org_credit_integration').setLevel(logging.DEBUG)
```

#### View Logs

```bash
# Real-time logs
docker logs ops-center-direct -f

# Filter for org billing logs
docker logs ops-center-direct 2>&1 | grep "org_billing"

# Last 100 lines
docker logs ops-center-direct --tail 100

# Since specific time
docker logs ops-center-direct --since 2h
```

#### Debug Credit Deduction Issues

```sql
-- Check user allocation before request
SELECT
    org_id,
    user_id,
    allocated_credits / 1000.0 as allocated,
    used_credits / 1000.0 as used,
    (allocated_credits - used_credits) / 1000.0 as remaining
FROM user_credit_allocations
WHERE org_id = 'ORG_ID' AND user_id = 'USER_ID' AND is_active = TRUE;

-- Check if deduction was recorded
SELECT
    created_at,
    service_name,
    credits_used / 1000.0 as credits,
    request_id,
    request_metadata
FROM credit_usage_attribution
WHERE org_id = 'ORG_ID' AND user_id = 'USER_ID'
ORDER BY created_at DESC
LIMIT 10;

-- Check pool consistency
SELECT
    'Allocation' as type,
    SUM(allocated_credits) / 1000.0 as value
FROM user_credit_allocations
WHERE org_id = 'ORG_ID' AND is_active = TRUE
UNION ALL
SELECT
    'Pool Allocated',
    allocated_credits / 1000.0
FROM organization_credit_pools
WHERE org_id = 'ORG_ID';

-- Should match!
```

### Frontend Debugging

#### Browser Console Debugging

```javascript
// Log all API calls
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  console.log('API Call:', args[0], args[1]);
  const response = await originalFetch(...args);
  console.log('API Response:', response.status, await response.clone().json());
  return response;
};

// Check current user context
fetch('/api/v1/auth/user')
  .then(r => r.json())
  .then(user => console.log('Current user:', user));

// Test org billing endpoint
fetch('/api/v1/org-billing/credits/org-id')
  .then(r => r.json())
  .then(data => console.log('Credit pool:', data));
```

#### React DevTools

```bash
# Install React DevTools extension
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools

# Inspect component state
# 1. Open React DevTools
# 2. Select component (e.g., OrganizationBillingPro)
# 3. Inspect props and state
# 4. Profile component re-renders
```

---

## Performance Optimization

### Database Query Optimization

#### Use EXPLAIN ANALYZE

```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT
    uca.user_id,
    uca.allocated_credits / 1000.0 as allocated,
    uca.used_credits / 1000.0 as used,
    SUM(cua.credits_used) / 1000.0 as total_usage
FROM user_credit_allocations uca
LEFT JOIN credit_usage_attribution cua
    ON cua.org_id = uca.org_id
    AND cua.user_id = uca.user_id
    AND cua.created_at >= NOW() - INTERVAL '30 days'
WHERE uca.org_id = 'org_abc123'
  AND uca.is_active = TRUE
GROUP BY uca.user_id, uca.allocated_credits, uca.used_credits;

-- Look for "Seq Scan" - add indexes to avoid
-- Target: < 50ms execution time
```

#### Add Missing Indexes

```sql
-- If seeing slow queries on created_at + org_id
CREATE INDEX CONCURRENTLY idx_usage_attribution_org_created
ON credit_usage_attribution(org_id, created_at DESC);

-- Verify index usage
EXPLAIN ANALYZE
SELECT * FROM credit_usage_attribution
WHERE org_id = 'org_abc123'
  AND created_at >= NOW() - INTERVAL '30 days';

-- Should show "Index Scan" not "Seq Scan"
```

### API Response Caching

```python
# backend/org_billing_api.py

from functools import lru_cache
import hashlib
import json

@lru_cache(maxsize=1000)
async def get_cached_credit_pool(org_id: str, cache_key: str):
    """
    Cache credit pool queries for 30 seconds.

    cache_key is a timestamp rounded to 30-second intervals.
    """
    async with get_db_pool().acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM organization_credit_pools WHERE org_id = $1",
            org_id
        )

@router.get("/api/v1/org-billing/credits/{org_id}")
async def get_credit_pool_cached(org_id: str):
    """Get credit pool with caching."""
    import time

    # Create cache key (changes every 30 seconds)
    cache_key = str(int(time.time() / 30))

    pool = await get_cached_credit_pool(org_id, cache_key)

    return {
        "org_id": org_id,
        "total_credits": pool['total_credits'] / 1000.0,
        "allocated_credits": pool['allocated_credits'] / 1000.0,
        "used_credits": pool['used_credits'] / 1000.0,
        "available_credits": pool['available_credits'] / 1000.0
    }
```

---

## Common Pitfalls

### Pitfall 1: Forgetting Milicredits Conversion

❌ **Wrong**:
```python
# This will insert 5000 credits as 5000 milicredits = 5 credits!
credits = 5000.0
await conn.execute(
    "INSERT INTO organization_credit_pools (org_id, total_credits) VALUES ($1, $2)",
    org_id, credits
)
```

✅ **Correct**:
```python
credits = 5000.0
milicredits = int(credits * 1000)  # 5000 * 1000 = 5,000,000
await conn.execute(
    "INSERT INTO organization_credit_pools (org_id, total_credits) VALUES ($1, $2)",
    org_id, milicredits
)
```

### Pitfall 2: Not Checking Active Allocations

❌ **Wrong**:
```sql
-- Gets all allocations including inactive ones!
SELECT * FROM user_credit_allocations
WHERE org_id = 'org_id' AND user_id = 'user_id';
```

✅ **Correct**:
```sql
SELECT * FROM user_credit_allocations
WHERE org_id = 'org_id'
  AND user_id = 'user_id'
  AND is_active = TRUE;  -- Only active allocation!
```

### Pitfall 3: Race Conditions in Credit Deduction

❌ **Wrong**:
```python
# Check then deduct (race condition!)
balance = await get_user_credits(user_id)
if balance >= cost:
    await deduct_credits(user_id, cost)  # Another request might deduct in between!
```

✅ **Correct**:
```python
# Use atomic database function
result = await conn.fetchrow(
    "SELECT * FROM deduct_credits($1, $2, $3, ...)",
    org_id, user_id, milicredits, ...
)

if not result['success']:
    raise HTTPException(402, "Insufficient credits")
```

### Pitfall 4: Not Using Transactions

❌ **Wrong**:
```python
# Multiple operations without transaction
await conn.execute("UPDATE table1 ...")
await conn.execute("UPDATE table2 ...")  # If this fails, table1 is inconsistent!
```

✅ **Correct**:
```python
async with conn.transaction():
    await conn.execute("UPDATE table1 ...")
    await conn.execute("UPDATE table2 ...")
    # Both commit together or rollback together
```

### Pitfall 5: Hardcoding User IDs in Tests

❌ **Wrong**:
```python
# Hardcoded user ID might not exist
await allocate_credits("org_id", "hardcoded-user-123", 5000.0)
```

✅ **Correct**:
```python
# Create test user dynamically
test_user_id = f"test-user-{uuid.uuid4()}"
await create_test_user(test_user_id)
await allocate_credits("org_id", test_user_id, 5000.0)
# Cleanup
await delete_test_user(test_user_id)
```

---

## Conclusion

This developer guide provides everything needed to:

✅ Set up local development environment
✅ Write unit, integration, and E2E tests
✅ Add new features and endpoints
✅ Debug common issues
✅ Optimize performance
✅ Avoid common pitfalls

**Next Steps**:
1. Complete the 5-minute quick start setup
2. Run the E2E test to verify your environment
3. Start developing your feature using the provided examples
4. Refer to this guide when debugging issues

**Need Help?**
- Check the API Reference: `/docs/api/ORG_BILLING_API.md`
- Review the Integration Guide: `/docs/billing/ORG_BILLING_INTEGRATION.md`
- Ask in #ops-center-dev Slack channel

---

**Developer Guide Version**: 1.0.0
**Last Updated**: November 15, 2025
**Maintained By**: Ops-Center Development Team
