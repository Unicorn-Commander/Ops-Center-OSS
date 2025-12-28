# LiteLLM Credit System - Database Schema Documentation

**Version**: 1.0.0
**Date**: 2025-10-20
**Database**: PostgreSQL 14+
**Schema File**: `/backend/sql/litellm_schema.sql`

## Overview

The LiteLLM credit system provides a comprehensive database schema for managing:
- **Credit-based billing** for LLM usage
- **Multi-provider routing** (OpenAI, Anthropic, OpenRouter, etc.)
- **BYOK (Bring Your Own Key)** support
- **Power level optimization** (Eco, Balanced, Precision)
- **Usage analytics** and performance tracking
- **Provider health monitoring**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LiteLLM Credit System                     │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │   Users   │      │ Providers │      │ Analytics │
    │  Credits  │      │   Health  │      │  Summary  │
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                   │                   │
    ┌─────▼─────────────┬────▼────────────┬──────▼──────┐
    │                   │                 │             │
┌───▼────┐    ┌────────▼──────┐   ┌─────▼─────┐  ┌────▼─────┐
│Credits │    │Transactions  │   │Usage Log  │  │Packages  │
│Balance │    │Audit Trail   │   │Analytics  │  │Pricing   │
└────────┘    └──────────────┘   └───────────┘  └──────────┘
```

## Tables

### 1. `user_credits`

**Purpose**: Track user credit balances and subscription tiers

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | TEXT | NOT NULL, UNIQUE | Keycloak user ID |
| `credits_remaining` | FLOAT | NOT NULL, >= 0 | Current credit balance |
| `credits_lifetime` | FLOAT | NOT NULL, >= 0 | Total credits ever purchased |
| `monthly_cap` | FLOAT | NULL | Optional spending limit (NULL = unlimited) |
| `tier` | TEXT | NOT NULL | Subscription tier (free/starter/professional/enterprise) |
| `power_level` | TEXT | NOT NULL | Default routing mode (eco/balanced/precision) |
| `auto_recharge` | BOOLEAN | DEFAULT FALSE | Auto-purchase when below threshold |
| `recharge_threshold` | FLOAT | DEFAULT 10.0 | Threshold for auto-recharge |
| `recharge_amount` | FLOAT | DEFAULT 100.0 | Amount to auto-purchase |
| `stripe_customer_id` | TEXT | NULL | Stripe customer ID for billing |
| `last_reset` | TIMESTAMP | NULL | Last time monthly cap was reset |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_user_credits_user_id` on `user_id`
- `idx_user_credits_tier` on `tier`
- `idx_user_credits_updated_at` on `updated_at DESC`

**Constraints**:
- `valid_tier` - tier must be in (free, starter, professional, enterprise)
- `valid_power_level` - power_level must be in (eco, balanced, precision)
- `positive_credits` - credits_remaining >= 0
- `positive_lifetime` - credits_lifetime >= 0

---

### 2. `credit_transactions`

**Purpose**: Complete audit log of all credit movements

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | TEXT | NOT NULL | Keycloak user ID |
| `transaction_type` | TEXT | NOT NULL | Type: purchase/debit/refund/bonus/adjustment |
| `amount` | FLOAT | NOT NULL | Positive for credit, negative for debit |
| `balance_after` | FLOAT | NOT NULL | Balance after transaction |
| **LLM Usage Details** | | | |
| `provider` | TEXT | NULL | LLM provider (openai, anthropic, etc.) |
| `model` | TEXT | NULL | Model name (gpt-4, claude-3-opus, etc.) |
| `prompt_tokens` | INTEGER | NULL | Prompt tokens used |
| `completion_tokens` | INTEGER | NULL | Completion tokens generated |
| `tokens_used` | INTEGER | NULL | Total tokens (prompt + completion) |
| `cost_per_token` | FLOAT | NULL | Cost calculation |
| `power_level` | TEXT | NULL | Power level used (eco/balanced/precision) |
| `byok_used` | BOOLEAN | DEFAULT FALSE | True if user's API key was used |
| **Payment Details** | | | |
| `payment_method` | TEXT | NULL | Payment method (stripe/paypal/manual/bonus) |
| `stripe_transaction_id` | TEXT | NULL | Stripe payment ID |
| `stripe_invoice_id` | TEXT | NULL | Stripe invoice ID |
| `package_id` | INTEGER | NULL | Reference to credit_packages |
| **Additional Context** | | | |
| `metadata` | JSONB | NULL | Additional context (request_id, session_id, etc.) |
| `notes` | TEXT | NULL | Human-readable notes for manual adjustments |
| `admin_user_id` | TEXT | NULL | Admin who made manual adjustment |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Transaction timestamp |

**Indexes**:
- `idx_credit_transactions_user_id` on `user_id`
- `idx_credit_transactions_created_at` on `created_at DESC`
- `idx_credit_transactions_type` on `transaction_type`
- `idx_credit_transactions_user_date` on `(user_id, created_at DESC)`
- `idx_credit_transactions_stripe` on `stripe_transaction_id` (partial: WHERE NOT NULL)

**Constraints**:
- `valid_transaction_type` - type in (purchase, debit, refund, bonus, adjustment)
- `valid_payment_method` - method in (stripe, paypal, manual, bonus, trial) or NULL

---

### 3. `user_provider_keys`

**Purpose**: Store encrypted user API keys for BYOK (Bring Your Own Key)

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | TEXT | NOT NULL | Keycloak user ID |
| `provider` | TEXT | NOT NULL | Provider name (openai, anthropic, etc.) |
| `encrypted_api_key` | TEXT | NOT NULL | Fernet encrypted API key |
| `key_name` | TEXT | NULL | User-friendly name (e.g., "My OpenAI Key") |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether key is active |
| `is_default` | BOOLEAN | DEFAULT FALSE | Default key for this provider |
| **Usage Statistics** | | | |
| `total_requests` | INTEGER | DEFAULT 0 | Total requests made with this key |
| `total_tokens` | INTEGER | DEFAULT 0 | Total tokens consumed |
| `last_used` | TIMESTAMP | NULL | Last time key was used |
| **Key Management** | | | |
| `expires_at` | TIMESTAMP | NULL | Optional key expiration |
| `rotation_reminder` | TIMESTAMP | NULL | When to remind user to rotate |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Key creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_user_provider_keys_user_id` on `user_id`
- `idx_user_provider_keys_provider` on `provider`
- `idx_user_provider_keys_active` on `(user_id, is_active)` (partial: WHERE is_active = TRUE)
- `idx_user_provider_keys_default` on `(user_id, provider, is_default)` (partial: WHERE is_default = TRUE)

**Constraints**:
- `UNIQUE(user_id, provider, key_name)` - Unique key names per user/provider
- `valid_provider` - provider in (openai, anthropic, openrouter, google, cohere, together, anyscale, deepinfra, custom)

**Security**:
- API keys are encrypted using Fernet (symmetric encryption)
- Encryption key stored in environment variable (not in database)
- Keys are only decrypted when needed for API calls

---

### 4. `llm_usage_log`

**Purpose**: Detailed log of every LLM request for analytics

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | TEXT | NOT NULL | Keycloak user ID |
| **Provider & Model Info** | | | |
| `provider` | TEXT | NOT NULL | LLM provider |
| `model` | TEXT | NOT NULL | Model name |
| `power_level` | TEXT | NOT NULL | Power level (eco/balanced/precision) |
| **Token Usage** | | | |
| `prompt_tokens` | INTEGER | NOT NULL, >= 0 | Prompt tokens |
| `completion_tokens` | INTEGER | NOT NULL, >= 0 | Completion tokens |
| `total_tokens` | INTEGER | NOT NULL, >= 0 | Total tokens |
| **Cost & Billing** | | | |
| `cost_credits` | FLOAT | NOT NULL | Cost in credits |
| `cost_per_token` | FLOAT | NULL | Cost per token |
| `byok_used` | BOOLEAN | DEFAULT FALSE | User's API key used |
| `provider_key_id` | INTEGER | NULL | Reference to user_provider_keys |
| **Request Details** | | | |
| `request_id` | TEXT | UNIQUE | Unique request identifier |
| `session_id` | TEXT | NULL | User session |
| `app_id` | TEXT | NULL | App that made request (Brigade, Open-WebUI, etc.) |
| `endpoint` | TEXT | NULL | API endpoint (/v1/chat/completions, etc.) |
| **Performance Metrics** | | | |
| `latency_ms` | INTEGER | NULL | Response time in milliseconds |
| `time_to_first_token_ms` | INTEGER | NULL | Time until first token streamed |
| `tokens_per_second` | FLOAT | NULL | Generation speed |
| **Status & Errors** | | | |
| `success` | BOOLEAN | NOT NULL | Whether request succeeded |
| `status_code` | INTEGER | NULL | HTTP status code |
| `error_message` | TEXT | NULL | Error message if failed |
| `error_type` | TEXT | NULL | Error type (rate_limit, insufficient_credits, etc.) |
| **Additional Context** | | | |
| `metadata` | JSONB | NULL | Full request/response metadata |
| `user_agent` | TEXT | NULL | Client user agent |
| `ip_address` | INET | NULL | Client IP address |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Request timestamp |

**Indexes**:
- `idx_llm_usage_log_user_id` on `user_id`
- `idx_llm_usage_log_created_at` on `created_at DESC`
- `idx_llm_usage_log_provider` on `provider`
- `idx_llm_usage_log_model` on `model`
- `idx_llm_usage_log_success` on `success`
- `idx_llm_usage_log_request_id` on `request_id`
- `idx_llm_usage_log_session_id` on `session_id`
- `idx_llm_usage_log_app_id` on `app_id`
- `idx_llm_usage_log_user_date` on `(user_id, created_at DESC)`

**Constraints**:
- `positive_tokens` - All token counts >= 0
- `valid_power_level_usage` - power_level in (eco, balanced, precision)

---

### 5. `provider_health`

**Purpose**: Cached health status of LLM providers

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `provider` | TEXT | NOT NULL, UNIQUE | Provider name |
| `status` | TEXT | NOT NULL | Health status (healthy/degraded/down) |
| **Performance Metrics** | | | |
| `avg_latency_ms` | INTEGER | NULL | Average latency in milliseconds |
| `p95_latency_ms` | INTEGER | NULL | 95th percentile latency |
| `success_rate` | FLOAT | 0-100 | Success rate percentage |
| **Capacity Metrics** | | | |
| `requests_last_hour` | INTEGER | DEFAULT 0 | Requests in last hour |
| `rate_limit_remaining` | INTEGER | NULL | Remaining rate limit quota |
| **Health Check Details** | | | |
| `last_check` | TIMESTAMP | DEFAULT NOW() | Last health check timestamp |
| `last_success` | TIMESTAMP | NULL | Last successful request |
| `last_failure` | TIMESTAMP | NULL | Last failed request |
| `consecutive_failures` | INTEGER | DEFAULT 0 | Consecutive failure count |
| **Error Details** | | | |
| `last_error` | TEXT | NULL | Last error message |
| `error_count_24h` | INTEGER | DEFAULT 0 | Errors in last 24 hours |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_provider_health_status` on `status`
- `idx_provider_health_updated_at` on `updated_at DESC`

**Constraints**:
- `valid_status` - status in (healthy, degraded, down)
- `valid_success_rate` - success_rate between 0 and 100

---

### 6. `credit_packages`

**Purpose**: Available credit packages for purchase

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `name` | TEXT | NOT NULL | Package name |
| `credits` | FLOAT | NOT NULL, > 0 | Credits in package |
| `price_usd` | FLOAT | NOT NULL, > 0 | Price in USD |
| `discount_percent` | FLOAT | 0-100 | Discount percentage |
| **Tier Restrictions** | | | |
| `min_tier` | TEXT | NULL | Minimum tier required (NULL = any) |
| **Status** | | | |
| `is_active` | BOOLEAN | DEFAULT TRUE | Package is available |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Show as featured |
| `sort_order` | INTEGER | DEFAULT 0 | Display order |
| **Display** | | | |
| `description` | TEXT | NULL | Package description |
| `badge_text` | TEXT | NULL | Badge (e.g., "BEST VALUE") |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_credit_packages_active` on `is_active` (partial: WHERE is_active = TRUE)
- `idx_credit_packages_featured` on `(is_featured, sort_order)` (partial: WHERE is_featured = TRUE)

**Constraints**:
- `positive_credits_pkg` - credits > 0
- `positive_price` - price_usd > 0
- `valid_discount` - discount_percent between 0 and 100

**Default Packages**:
1. **Starter Pack**: 100 credits, $10.00 (0% discount)
2. **Value Pack**: 500 credits, $45.00 (10% discount) - MOST POPULAR
3. **Pro Pack**: 1,000 credits, $80.00 (20% discount) - BEST VALUE
4. **Enterprise Pack**: 5,000 credits, $350.00 (30% discount)

---

### 7. `power_level_configs`

**Purpose**: Configuration for power level routing strategies

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `power_level` | TEXT | NOT NULL, UNIQUE | Power level (eco/balanced/precision) |
| `name` | TEXT | NOT NULL | Display name |
| `description` | TEXT | NULL | Description |
| **Routing Strategy** | | | |
| `preferred_providers` | JSONB | NULL | Array of providers in preference order |
| `fallback_strategy` | TEXT | DEFAULT 'next_available' | Fallback strategy |
| **Cost Multiplier** | | | |
| `cost_multiplier` | FLOAT | DEFAULT 1.0 | Relative cost vs balanced |
| **Performance Targets** | | | |
| `max_latency_ms` | INTEGER | NULL | Maximum acceptable latency |
| `min_quality_score` | FLOAT | NULL | Minimum quality score (0-100) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Configuration is active |

**Constraints**:
- `valid_power_level_config` - power_level in (eco, balanced, precision)

**Default Configurations**:

| Power Level | Preferred Providers | Cost Multiplier | Max Latency | Min Quality |
|-------------|---------------------|-----------------|-------------|-------------|
| **Eco** | openrouter, together, deepinfra | 0.7x | 5000ms | 70 |
| **Balanced** | openai, anthropic, openrouter | 1.0x | 3000ms | 85 |
| **Precision** | anthropic, openai | 1.5x | 2000ms | 95 |

---

## Materialized Views

### `llm_usage_summary`

**Purpose**: Pre-aggregated usage statistics for fast analytics

**Aggregation**: Daily, per user, provider, model, and power level

**Columns**:
- `user_id` - User ID
- `provider` - LLM provider
- `model` - Model name
- `power_level` - Power level
- `date` - Date (day granularity)
- `request_count` - Total requests
- `success_count` - Successful requests
- `error_count` - Failed requests
- `total_prompt_tokens` - Total prompt tokens
- `total_completion_tokens` - Total completion tokens
- `total_tokens` - Total tokens
- `avg_tokens_per_request` - Average tokens per request
- `total_cost` - Total cost in credits
- `avg_cost_per_request` - Average cost per request
- `avg_latency_ms` - Average latency
- `p95_latency_ms` - 95th percentile latency
- `avg_tokens_per_second` - Average generation speed
- `success_rate` - Success rate percentage
- `byok_requests` - Requests using BYOK

**Refresh**:
```sql
-- Manual refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY llm_usage_summary;

-- Or use function
SELECT refresh_usage_summary();
```

**Indexes**:
- Unique index on `(user_id, provider, model, power_level, date)`
- Index on `(user_id, date DESC)` for user queries
- Index on `date DESC` for global queries

---

## Functions

### `debit_user_credits()`

**Purpose**: Atomically debit credits from user account

**Signature**:
```sql
debit_user_credits(
    p_user_id TEXT,
    p_amount FLOAT,
    p_provider TEXT,
    p_model TEXT,
    p_prompt_tokens INTEGER,
    p_completion_tokens INTEGER,
    p_power_level TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS TABLE(
    new_balance FLOAT,
    transaction_id INTEGER,
    success BOOLEAN,
    error_message TEXT
)
```

**Usage**:
```sql
-- Debit credits for LLM request
SELECT * FROM debit_user_credits(
    'user-123',
    0.05,
    'openai',
    'gpt-4',
    100,
    200,
    'balanced',
    '{"request_id": "req-abc123"}'::JSONB
);
```

**Returns**:
- `new_balance` - Balance after debit
- `transaction_id` - Transaction record ID
- `success` - TRUE if successful, FALSE otherwise
- `error_message` - Error message if failed (NULL if success)

**Features**:
- **Atomic operation** - Uses row-level locking
- **Validation** - Checks user exists and has sufficient credits
- **Audit trail** - Creates transaction record automatically

---

### `add_user_credits()`

**Purpose**: Add credits to user account (purchase, bonus, refund)

**Signature**:
```sql
add_user_credits(
    p_user_id TEXT,
    p_amount FLOAT,
    p_transaction_type TEXT,
    p_payment_method TEXT DEFAULT NULL,
    p_stripe_transaction_id TEXT DEFAULT NULL,
    p_package_id INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS TABLE(
    new_balance FLOAT,
    transaction_id INTEGER,
    success BOOLEAN,
    error_message TEXT
)
```

**Usage**:
```sql
-- Add credits from purchase
SELECT * FROM add_user_credits(
    'user-123',
    100.0,
    'purchase',
    'stripe',
    'ch_1234567890',
    1,  -- package_id
    NULL
);

-- Add bonus credits
SELECT * FROM add_user_credits(
    'user-123',
    50.0,
    'bonus',
    'bonus',
    NULL,
    NULL,
    'Referral bonus'
);
```

**Features**:
- **Auto-creates user** if doesn't exist
- **Updates lifetime credits** for purchases
- **Audit trail** - Creates transaction record

---

### `get_user_balance()`

**Purpose**: Get current credit balance for user

**Signature**:
```sql
get_user_balance(p_user_id TEXT)
RETURNS TABLE(
    credits_remaining FLOAT,
    credits_lifetime FLOAT,
    tier TEXT,
    power_level TEXT
)
```

**Usage**:
```sql
-- Get user balance
SELECT * FROM get_user_balance('user-123');
```

---

### `refresh_usage_summary()`

**Purpose**: Refresh materialized view for latest analytics

**Signature**:
```sql
refresh_usage_summary() RETURNS VOID
```

**Usage**:
```sql
-- Refresh analytics
SELECT refresh_usage_summary();
```

**Note**: Uses `REFRESH MATERIALIZED VIEW CONCURRENTLY` to avoid locking.

---

## Triggers

### Auto-update `updated_at`

**Applies to**:
- `user_credits`
- `user_provider_keys`
- `credit_packages`

**Function**: `update_updated_at_column()`

**Behavior**: Automatically sets `updated_at = NOW()` on UPDATE

---

## Installation

### 1. Run Schema Script

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend

# Execute schema
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f sql/litellm_schema.sql
```

### 2. Verify Installation

```sql
-- Check tables created
\dt

-- Check functions
\df

-- Check materialized views
\dm

-- Check triggers
\dy
```

### 3. Initial Data

Schema includes seed data:
- 4 credit packages (Starter, Value, Pro, Enterprise)
- 3 power level configs (eco, balanced, precision)

---

## Usage Examples

### Create User Account

```sql
-- Create user with initial credits
SELECT * FROM add_user_credits(
    'user-123',
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
SELECT credits_remaining FROM get_user_balance('user-123');

-- 2. Debit credits for request
SELECT * FROM debit_user_credits(
    'user-123',
    0.05,
    'openai',
    'gpt-4',
    100,
    200,
    'balanced',
    '{"request_id": "req-abc123", "session_id": "sess-xyz"}'::JSONB
);

-- 3. Log usage
INSERT INTO llm_usage_log (
    user_id, provider, model, power_level,
    prompt_tokens, completion_tokens, total_tokens,
    cost_credits, success, latency_ms, request_id
) VALUES (
    'user-123', 'openai', 'gpt-4', 'balanced',
    100, 200, 300,
    0.05, TRUE, 1234, 'req-abc123'
);
```

### Purchase Credits

```sql
-- Process Stripe payment
SELECT * FROM add_user_credits(
    'user-123',
    500.0,
    'purchase',
    'stripe',
    'ch_1234567890',
    2,  -- Value Pack
    NULL
);
```

### Get User Statistics

```sql
-- Get user's usage summary for last 7 days
SELECT
    date,
    provider,
    model,
    request_count,
    total_tokens,
    total_cost,
    success_rate
FROM llm_usage_summary
WHERE user_id = 'user-123'
  AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, total_cost DESC;
```

### Monitor Provider Health

```sql
-- Get healthy providers
SELECT provider, status, avg_latency_ms, success_rate
FROM provider_health
WHERE status = 'healthy'
ORDER BY avg_latency_ms ASC;
```

---

## Maintenance

### Refresh Analytics

```bash
# Schedule daily refresh (cron)
0 2 * * * docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT refresh_usage_summary();"
```

### Archive Old Data

```sql
-- Archive usage logs older than 90 days
CREATE TABLE llm_usage_log_archive AS
SELECT * FROM llm_usage_log
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM llm_usage_log
WHERE created_at < NOW() - INTERVAL '90 days';

-- Vacuum to reclaim space
VACUUM FULL llm_usage_log;
```

### Backup

```bash
# Backup credit system tables
docker exec unicorn-postgresql pg_dump -U unicorn -d unicorn_db \
  -t user_credits \
  -t credit_transactions \
  -t user_provider_keys \
  -t llm_usage_log \
  > litellm_backup_$(date +%Y%m%d).sql
```

---

## Performance Considerations

### Indexes

All tables have appropriate indexes for common queries:
- User lookups (O(log n) instead of O(n))
- Time-range queries (DESC indexes for recent data)
- Provider filtering
- Transaction type filtering

### Materialized View

`llm_usage_summary` pre-aggregates data for fast analytics:
- Reduces query time from seconds to milliseconds
- Refresh concurrently (no locking)
- Schedule refresh during low-traffic periods

### Partitioning (Future)

For high-volume deployments, consider partitioning:
- `llm_usage_log` by date (monthly or quarterly)
- `credit_transactions` by date
- Automatically drop old partitions

### Connection Pooling

Use connection pooling (e.g., PgBouncer) for high concurrency:
```
Max connections: 100
Pool size: 20 per worker
```

---

## Security

### Encryption

- **API Keys**: Encrypted with Fernet (symmetric encryption)
- **Encryption Key**: Stored in environment variable, NOT in database
- **Key Rotation**: Support for periodic key rotation

### Access Control

```sql
-- Create dedicated user (recommended)
CREATE USER litellm_user WITH PASSWORD 'secure_password';

-- Grant minimal privileges
GRANT CONNECT ON DATABASE unicorn_db TO litellm_user;
GRANT USAGE ON SCHEMA public TO litellm_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO litellm_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO litellm_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO litellm_user;
```

### Audit Trail

All credit movements logged in `credit_transactions`:
- Who (user_id, admin_user_id)
- What (transaction_type, amount)
- When (created_at)
- Why (notes, metadata)

---

## Troubleshooting

### Check User Balance

```sql
SELECT * FROM user_credits WHERE user_id = 'user-123';
```

### View Recent Transactions

```sql
SELECT * FROM credit_transactions
WHERE user_id = 'user-123'
ORDER BY created_at DESC
LIMIT 10;
```

### Check Provider Health

```sql
SELECT * FROM provider_health ORDER BY updated_at DESC;
```

### Find Expensive Requests

```sql
SELECT
    user_id,
    provider,
    model,
    cost_credits,
    total_tokens,
    created_at
FROM llm_usage_log
WHERE cost_credits > 1.0
ORDER BY cost_credits DESC
LIMIT 20;
```

### Identify Failed Requests

```sql
SELECT
    user_id,
    provider,
    model,
    error_type,
    error_message,
    COUNT(*) as error_count
FROM llm_usage_log
WHERE success = FALSE
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY user_id, provider, model, error_type, error_message
ORDER BY error_count DESC;
```

---

## Schema Version

**Current Version**: 1.0.0

Check schema version:
```sql
SELECT * FROM schema_version ORDER BY applied_at DESC LIMIT 1;
```

---

## References

- **Schema File**: `/backend/sql/litellm_schema.sql`
- **Migration Script**: `/backend/scripts/initialize_litellm_db.py`
- **Test Suite**: `/backend/tests/test_litellm_schema.py`

---

**End of Documentation**
