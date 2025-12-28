# LiteLLM Database Quick Reference

**Database**: `unicorn_db` on `unicorn-postgresql`
**Schema Version**: 1.0.0
**Status**: ✅ Production Ready

---

## Tables Overview

| Table | Purpose | Rows | Key Columns |
|-------|---------|------|-------------|
| **user_credits** | User balances & tiers | Dynamic | user_id, balance, tier, power_level |
| **credit_transactions** | Audit log | Dynamic | user_id, amount, type, balance_after |
| **credit_packages** | Purchase options | 4 | name, credits, price_usd, discount |
| **power_level_configs** | Routing strategy | 3 | power_level, preferred_providers, cost_multiplier |
| **user_provider_keys** | BYOK keys | Dynamic | user_id, provider, encrypted_key |
| **llm_usage_log** | Request analytics | Dynamic | request_id, model, tokens, credits_used |

---

## Credit Package Tiers

```
Starter Pack:     100 credits = $10  (0% discount)
Value Pack:       500 credits = $45  (10% discount) ⭐ MOST POPULAR
Pro Pack:        1000 credits = $80  (20% discount) 💎 BEST VALUE
Enterprise Pack: 5000 credits = $350 (30% discount)
```

---

## Power Levels

```
ECO Mode:       0.7x cost | 5000ms latency | 70% quality
                → openrouter, together, deepinfra

BALANCED Mode:  1.0x cost | 3000ms latency | 85% quality
                → openai, anthropic, openrouter

PRECISION Mode: 1.5x cost | 2000ms latency | 95% quality
                → anthropic, openai
```

---

## Subscription Tiers

```
TRIAL         → Free tier (limited credits)
STARTER       → $19/month (1,000 credits)
PROFESSIONAL  → $49/month (10,000 credits)
ENTERPRISE    → $99/month (unlimited credits)
```

---

## Common Queries

### Check User Balance
```sql
SELECT
  user_id,
  balance,
  tier,
  power_level,
  monthly_allowance,
  credits_used_this_month,
  ROUND((credits_used_this_month::numeric / NULLIF(monthly_allowance, 0)) * 100, 2) as usage_percent
FROM user_credits
WHERE user_id = 'USER_UUID';
```

### Recent Transactions
```sql
SELECT
  created_at,
  transaction_type,
  amount,
  balance_after,
  description,
  reference_id
FROM credit_transactions
WHERE user_id = 'USER_UUID'
ORDER BY created_at DESC
LIMIT 10;
```

### LLM Usage Stats (Last 24 Hours)
```sql
SELECT
  model,
  COUNT(*) as request_count,
  SUM(total_tokens) as total_tokens,
  SUM(credits_used) as total_credits,
  AVG(latency_ms) as avg_latency_ms,
  SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_rate
FROM llm_usage_log
WHERE user_id = 'USER_UUID'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY model
ORDER BY total_credits DESC;
```

### User BYOK Keys
```sql
SELECT
  provider,
  key_name,
  is_default,
  is_active,
  last_used_at,
  usage_count_this_month
FROM user_provider_keys
WHERE user_id = 'USER_UUID'
  AND is_active = true
ORDER BY is_default DESC, provider;
```

---

## Using Stored Functions

### Add Credits
```sql
-- Purchase credits
SELECT * FROM add_user_credits(
  'USER_UUID'::uuid,           -- user_id
  100.00,                       -- amount
  'purchase',                   -- transaction_type
  'pi_stripe_123',              -- payment_intent_id
  'Purchased Starter Pack'      -- description
);

-- Returns: (success, new_balance, transaction_id)
```

### Debit Credits
```sql
-- Use credits for LLM request
SELECT * FROM debit_user_credits(
  'USER_UUID'::uuid,            -- user_id
  2.50,                         -- amount
  'usage',                      -- transaction_type
  'req_abc123',                 -- request_id
  'GPT-4 completion'            -- description
);

-- Returns: (success, new_balance, transaction_id)
```

### Check Quota Usage
```sql
SELECT get_quota_usage_percentage('USER_UUID'::uuid);
-- Returns: 45.67 (percentage)
```

---

## Transaction Types

- **purchase** - User bought credits (Stripe payment)
- **usage** - Credits deducted for LLM request
- **refund** - Stripe refund processed
- **admin_adjustment** - Manual admin credit adjustment
- **bonus** - Promotional credits added

---

## Key Indexes

**High-Performance Queries**:
- `idx_llm_usage_log_user_date` - Fast user history lookups
- `idx_credit_transactions_user_date` - Fast transaction history
- `idx_user_credits_user_id` - Instant balance lookups
- `idx_llm_usage_log_request_id` - Request deduplication

**Filtering & Analytics**:
- `idx_llm_usage_log_model` - Group by model
- `idx_llm_usage_log_provider` - Group by provider
- `idx_llm_usage_log_success` - Filter errors
- `idx_credit_transactions_type` - Filter by transaction type

---

## Typical Credit Costs

```
Model                Input Tokens   Output Tokens   Example Cost
-------------------- -------------- --------------- ------------
GPT-3.5 Turbo        $0.50/1M       $1.50/1M       ~0.002 credits
GPT-4                $30/1M         $60/1M         ~0.045 credits
GPT-4 Turbo          $10/1M         $30/1M         ~0.020 credits
Claude 3 Opus        $15/1M         $75/1M         ~0.045 credits
Claude 3 Sonnet      $3/1M          $15/1M         ~0.009 credits
Claude 3 Haiku       $0.25/1M       $1.25/1M       ~0.001 credits

Note: Actual costs vary by power level (eco 0.7x, balanced 1.0x, precision 1.5x)
```

---

## Database Access

### Via Docker Exec
```bash
# Connect to database
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

# Quick query
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM user_credits;"

# Export data
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "COPY (SELECT * FROM credit_packages) TO STDOUT WITH CSV HEADER;" > credit_packages.csv
```

### Via Python (asyncpg)
```python
import asyncpg

async def get_user_balance(user_id: str):
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="unicorn",
        password=os.getenv("POSTGRES_PASSWORD"),
        database="unicorn_db"
    )

    balance = await conn.fetchval(
        "SELECT balance FROM user_credits WHERE user_id = $1",
        user_id
    )

    await conn.close()
    return balance
```

---

## Maintenance Commands

### Vacuum Tables (Weekly)
```sql
VACUUM ANALYZE user_credits;
VACUUM ANALYZE credit_transactions;
VACUUM ANALYZE llm_usage_log;
```

### Check Table Sizes
```sql
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('user_credits', 'credit_transactions', 'llm_usage_log',
                    'user_provider_keys', 'credit_packages', 'power_level_configs')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Rebuild Indexes (If Needed)
```sql
REINDEX TABLE user_credits;
REINDEX TABLE credit_transactions;
REINDEX TABLE llm_usage_log;
```

---

## Monitoring Queries

### Active Users (Last 7 Days)
```sql
SELECT COUNT(DISTINCT user_id)
FROM llm_usage_log
WHERE created_at > NOW() - INTERVAL '7 days';
```

### Revenue Summary (This Month)
```sql
SELECT
  COUNT(*) as purchases,
  SUM(amount) as total_credits_sold,
  SUM(amount * (SELECT price_usd FROM credit_packages WHERE credits = amount LIMIT 1)) as estimated_revenue
FROM credit_transactions
WHERE transaction_type = 'purchase'
  AND created_at >= DATE_TRUNC('month', NOW());
```

### Top Models (This Month)
```sql
SELECT
  model,
  COUNT(*) as requests,
  SUM(total_tokens) as total_tokens,
  SUM(credits_used) as total_credits,
  AVG(latency_ms) as avg_latency
FROM llm_usage_log
WHERE created_at >= DATE_TRUNC('month', NOW())
GROUP BY model
ORDER BY requests DESC
LIMIT 10;
```

### Users with Low Balance
```sql
SELECT
  user_id,
  balance,
  tier,
  credits_used_this_month,
  monthly_allowance
FROM user_credits
WHERE balance < 10
  AND tier != 'enterprise'
ORDER BY balance ASC;
```

---

## Schema Version Check

```sql
SELECT * FROM schema_version ORDER BY applied_at DESC LIMIT 1;
```

---

## Troubleshooting

### No Balance Record for User
```sql
-- Create initial balance record
INSERT INTO user_credits (user_id, balance, tier, power_level, monthly_allowance, billing_cycle_start)
VALUES ('USER_UUID', 0.00, 'trial', 'balanced', 100, NOW())
ON CONFLICT (user_id) DO NOTHING;
```

### Transaction Failed (Insufficient Balance)
```sql
-- Check current balance
SELECT balance FROM user_credits WHERE user_id = 'USER_UUID';

-- Check last transaction
SELECT * FROM credit_transactions
WHERE user_id = 'USER_UUID'
ORDER BY created_at DESC
LIMIT 1;
```

### Find Duplicate Requests
```sql
SELECT request_id, COUNT(*)
FROM llm_usage_log
GROUP BY request_id
HAVING COUNT(*) > 1;
```

---

## Support

- **Schema File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/sql/litellm_schema.sql`
- **Full Report**: `/home/muut/Production/UC-Cloud/services/ops-center/LITELLM_DATABASE_DEPLOYMENT_REPORT.md`
- **Container**: `unicorn-postgresql`
- **Database**: `unicorn_db`
- **User**: `unicorn`

---

**Last Updated**: October 20, 2025
**Schema Version**: 1.0.0
