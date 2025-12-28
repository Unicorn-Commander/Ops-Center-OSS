# LiteLLM Database - Quick Reference

**Version**: 1.0.0
**Last Updated**: 2025-10-20

## Installation

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Initialize schema
python scripts/initialize_litellm_db.py

# Initialize with test data (development)
python scripts/initialize_litellm_db.py --test-data

# Reset and recreate (DESTRUCTIVE!)
python scripts/initialize_litellm_db.py --reset
```

## Common Operations

### Create User Account

```sql
-- Give user 100 bonus credits
SELECT * FROM add_user_credits(
    'user-keycloak-id',
    100.0,
    'bonus',
    'trial',
    NULL,
    NULL,
    'Welcome bonus'
);
```

### Process LLM Request

```sql
-- 1. Check balance
SELECT credits_remaining FROM get_user_balance('user-id');

-- 2. Debit credits
SELECT * FROM debit_user_credits(
    'user-id',
    0.05,          -- Cost in credits
    'openai',      -- Provider
    'gpt-4',       -- Model
    100,           -- Prompt tokens
    200,           -- Completion tokens
    'balanced',    -- Power level
    '{"request_id": "req-123"}'::JSONB
);

-- 3. Log usage
INSERT INTO llm_usage_log (
    user_id, provider, model, power_level,
    prompt_tokens, completion_tokens, total_tokens,
    cost_credits, success, latency_ms, request_id
) VALUES (
    'user-id', 'openai', 'gpt-4', 'balanced',
    100, 200, 300, 0.05, TRUE, 1234, 'req-123'
);
```

### Purchase Credits

```sql
-- Process Stripe payment
SELECT * FROM add_user_credits(
    'user-id',
    500.0,                    -- Credits
    'purchase',               -- Transaction type
    'stripe',                 -- Payment method
    'ch_1234567890',          -- Stripe charge ID
    2,                        -- Package ID (Value Pack)
    NULL
);
```

### Add BYOK Key

```python
from cryptography.fernet import Fernet

# Encrypt API key
cipher = Fernet(ENCRYPTION_KEY)
encrypted_key = cipher.encrypt(b'sk-openai-key-123').decode()

# Store key
cursor.execute("""
    INSERT INTO user_provider_keys (
        user_id, provider, encrypted_api_key, key_name
    ) VALUES (%s, %s, %s, %s);
""", ('user-id', 'openai', encrypted_key, 'My OpenAI Key'))
```

## Common Queries

### User Statistics

```sql
-- Get user balance and stats
SELECT * FROM get_user_balance('user-id');

-- User's usage in last 7 days
SELECT
    date,
    SUM(total_cost) as daily_cost,
    SUM(request_count) as daily_requests
FROM llm_usage_summary
WHERE user_id = 'user-id'
  AND date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date DESC;

-- Top models used
SELECT
    model,
    SUM(request_count) as requests,
    SUM(total_cost) as cost
FROM llm_usage_summary
WHERE user_id = 'user-id'
GROUP BY model
ORDER BY cost DESC
LIMIT 5;
```

### Provider Health

```sql
-- Get healthy providers
SELECT provider, avg_latency_ms, success_rate
FROM provider_health
WHERE status = 'healthy'
ORDER BY avg_latency_ms ASC;

-- Update provider status
INSERT INTO provider_health (provider, status, avg_latency_ms, success_rate)
VALUES ('openai', 'healthy', 1200, 99.5)
ON CONFLICT (provider) DO UPDATE
SET status = EXCLUDED.status,
    avg_latency_ms = EXCLUDED.avg_latency_ms,
    success_rate = EXCLUDED.success_rate,
    last_check = NOW();
```

### Analytics

```sql
-- Refresh materialized view
SELECT refresh_usage_summary();

-- Top spenders
SELECT
    user_id,
    SUM(total_cost) as total_spent
FROM llm_usage_summary
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_spent DESC
LIMIT 10;

-- Provider usage breakdown
SELECT
    provider,
    COUNT(DISTINCT user_id) as users,
    SUM(request_count) as requests,
    SUM(total_cost) as revenue
FROM llm_usage_summary
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY provider
ORDER BY revenue DESC;
```

### Transaction History

```sql
-- User's recent transactions
SELECT
    transaction_type,
    amount,
    balance_after,
    provider,
    model,
    created_at
FROM credit_transactions
WHERE user_id = 'user-id'
ORDER BY created_at DESC
LIMIT 20;

-- All purchases today
SELECT
    user_id,
    amount,
    payment_method,
    stripe_transaction_id,
    created_at
FROM credit_transactions
WHERE transaction_type = 'purchase'
  AND created_at >= CURRENT_DATE
ORDER BY created_at DESC;
```

## Power Levels

| Level | Providers | Cost | Max Latency | Min Quality |
|-------|-----------|------|-------------|-------------|
| **Eco** | openrouter, together, deepinfra | 0.7x | 5000ms | 70 |
| **Balanced** | openai, anthropic, openrouter | 1.0x | 3000ms | 85 |
| **Precision** | anthropic, openai | 1.5x | 2000ms | 95 |

## Credit Packages

| Package | Credits | Price | Discount |
|---------|---------|-------|----------|
| Starter Pack | 100 | $10.00 | 0% |
| Value Pack | 500 | $45.00 | 10% |
| Pro Pack | 1,000 | $80.00 | 20% |
| Enterprise Pack | 5,000 | $350.00 | 30% |

## Database Maintenance

```bash
# Refresh analytics (schedule daily)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT refresh_usage_summary();"

# Backup credit system
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db \
  -t user_credits -t credit_transactions -t llm_usage_log \
  > backup_$(date +%Y%m%d).sql

# Archive old logs (90+ days)
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
  CREATE TABLE llm_usage_log_archive AS
  SELECT * FROM llm_usage_log
  WHERE created_at < NOW() - INTERVAL '90 days';

  DELETE FROM llm_usage_log
  WHERE created_at < NOW() - INTERVAL '90 days';
"
```

## Testing

```bash
# Run all tests
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
pytest tests/test_litellm_schema.py -v

# Run specific test
pytest tests/test_litellm_schema.py::TestUserCredits::test_add_user_credits_creates_user -v

# Run with coverage
pytest tests/test_litellm_schema.py --cov=. --cov-report=html
```

## Environment Variables

```bash
# Required for Python scripts
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=unicorn_db
export POSTGRES_USER=unicorn
export POSTGRES_PASSWORD=your_password

# For BYOK encryption
export LITELLM_ENCRYPTION_KEY=<fernet-key>
```

## Troubleshooting

```sql
-- Check if schema exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'user_credits'
);

-- Count records
SELECT
    (SELECT COUNT(*) FROM user_credits) as users,
    (SELECT COUNT(*) FROM credit_transactions) as transactions,
    (SELECT COUNT(*) FROM llm_usage_log) as usage_logs;

-- Find user with negative balance (shouldn't exist)
SELECT * FROM user_credits WHERE credits_remaining < 0;

-- Check for failed requests
SELECT
    provider,
    error_type,
    COUNT(*) as count
FROM llm_usage_log
WHERE success = FALSE
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY provider, error_type
ORDER BY count DESC;
```

## Python Integration Example

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect
conn = psycopg2.connect(
    host='localhost',
    database='unicorn_db',
    user='unicorn',
    password='password'
)

# Process LLM request
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    # 1. Check balance
    cur.execute("SELECT * FROM get_user_balance(%s)", (user_id,))
    balance = cur.fetchone()

    if balance['credits_remaining'] < estimated_cost:
        raise InsufficientCreditsError()

    # 2. Debit credits
    cur.execute("""
        SELECT * FROM debit_user_credits(
            %s, %s, %s, %s, %s, %s, %s, %s::JSONB
        )
    """, (
        user_id, cost, provider, model,
        prompt_tokens, completion_tokens, power_level,
        json.dumps(metadata)
    ))

    result = cur.fetchone()
    if not result['success']:
        raise CreditDebitError(result['error_message'])

    # 3. Log usage
    cur.execute("""
        INSERT INTO llm_usage_log (
            user_id, provider, model, power_level,
            prompt_tokens, completion_tokens, total_tokens,
            cost_credits, success, latency_ms, request_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, provider, model, power_level,
        prompt_tokens, completion_tokens, total_tokens,
        cost, True, latency_ms, request_id
    ))

    conn.commit()
```

## Files

- **Schema**: `/backend/sql/litellm_schema.sql`
- **Documentation**: `/backend/docs/LITELLM_DATABASE_SCHEMA.md`
- **Init Script**: `/backend/scripts/initialize_litellm_db.py`
- **Tests**: `/backend/tests/test_litellm_schema.py`
- **Quick Ref**: `/backend/docs/LITELLM_QUICK_REFERENCE.md` (this file)
