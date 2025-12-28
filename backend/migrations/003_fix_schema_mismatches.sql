-- ============================================================================
-- Fix Schema Mismatches - Critical Database Fixes
--
-- This migration adds missing columns that the backend code expects
-- Fixes 500 errors in credit_api, usage_metering, and LLM APIs
--
-- Date: October 28, 2025
-- ============================================================================

-- Fix 1: Add balance_after column to credit_transactions
-- The credit_api.py expects this column to track running balance
ALTER TABLE credit_transactions
ADD COLUMN IF NOT EXISTS balance_after DECIMAL(12, 6);

COMMENT ON COLUMN credit_transactions.balance_after IS 'User credit balance after this transaction';

-- Create index for balance queries
CREATE INDEX IF NOT EXISTS idx_credit_transactions_balance ON credit_transactions(user_id, created_at DESC);

-- Fix 2: Add total_cost as computed column or alias for cost in usage_events
-- Option A: Add it as a generated column (PostgreSQL 12+)
-- Option B: Add it as a regular column that mirrors cost
-- We'll use Option B for compatibility

ALTER TABLE usage_events
ADD COLUMN IF NOT EXISTS total_cost DECIMAL(12, 6);

-- Update existing rows to copy cost to total_cost
UPDATE usage_events
SET total_cost = cost
WHERE total_cost IS NULL;

COMMENT ON COLUMN usage_events.total_cost IS 'Total cost of the usage event (same as cost, kept for API compatibility)';

-- Fix 3: Add input_tokens and output_tokens as aliases for request_tokens and response_tokens
ALTER TABLE llm_usage_logs
ADD COLUMN IF NOT EXISTS input_tokens INTEGER;

ALTER TABLE llm_usage_logs
ADD COLUMN IF NOT EXISTS output_tokens INTEGER;

-- Update existing rows to copy from request_tokens and response_tokens
UPDATE llm_usage_logs
SET input_tokens = request_tokens,
    output_tokens = response_tokens
WHERE input_tokens IS NULL OR output_tokens IS NULL;

COMMENT ON COLUMN llm_usage_logs.input_tokens IS 'Input tokens (same as request_tokens, kept for API compatibility)';
COMMENT ON COLUMN llm_usage_logs.output_tokens IS 'Output tokens (same as response_tokens, kept for API compatibility)';

-- Fix 4: Add provider_cost and platform_markup columns to usage_events
-- These are expected by the usage_metering.py code
ALTER TABLE usage_events
ADD COLUMN IF NOT EXISTS provider_cost DECIMAL(12, 6) DEFAULT 0,
ADD COLUMN IF NOT EXISTS platform_markup DECIMAL(12, 6) DEFAULT 0;

-- Update existing rows: assume all cost is provider_cost, 0 markup
UPDATE usage_events
SET provider_cost = cost,
    platform_markup = 0
WHERE provider_cost IS NULL;

COMMENT ON COLUMN usage_events.provider_cost IS 'Cost charged by the LLM provider';
COMMENT ON COLUMN usage_events.platform_markup IS 'Platform markup on top of provider cost';

-- Fix 5: Create trigger to keep cost and total_cost in sync
CREATE OR REPLACE FUNCTION sync_usage_events_cost()
RETURNS TRIGGER AS $$
BEGIN
    -- Keep total_cost in sync with cost
    IF NEW.cost IS NOT NULL THEN
        NEW.total_cost := NEW.cost;
    END IF;

    -- Calculate cost from provider_cost + platform_markup if not set
    IF NEW.cost IS NULL AND NEW.provider_cost IS NOT NULL THEN
        NEW.cost := NEW.provider_cost + COALESCE(NEW.platform_markup, 0);
        NEW.total_cost := NEW.cost;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_usage_events_cost
    BEFORE INSERT OR UPDATE ON usage_events
    FOR EACH ROW
    EXECUTE FUNCTION sync_usage_events_cost();

-- Fix 6: Create trigger to keep input_tokens and output_tokens in sync with request_tokens and response_tokens
CREATE OR REPLACE FUNCTION sync_llm_usage_tokens()
RETURNS TRIGGER AS $$
BEGIN
    -- Keep input_tokens in sync with request_tokens
    IF NEW.request_tokens IS NOT NULL THEN
        NEW.input_tokens := NEW.request_tokens;
    END IF;

    -- Keep output_tokens in sync with response_tokens
    IF NEW.response_tokens IS NOT NULL THEN
        NEW.output_tokens := NEW.response_tokens;
    END IF;

    -- Reverse sync: if input_tokens set but not request_tokens
    IF NEW.input_tokens IS NOT NULL AND NEW.request_tokens IS NULL THEN
        NEW.request_tokens := NEW.input_tokens;
    END IF;

    IF NEW.output_tokens IS NOT NULL AND NEW.response_tokens IS NULL THEN
        NEW.response_tokens := NEW.output_tokens;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_llm_usage_tokens
    BEFORE INSERT OR UPDATE ON llm_usage_logs
    FOR EACH ROW
    EXECUTE FUNCTION sync_llm_usage_tokens();

-- Verification queries
DO $$
BEGIN
    RAISE NOTICE 'Schema fixes complete!';
    RAISE NOTICE 'Added columns:';
    RAISE NOTICE '  - credit_transactions.balance_after';
    RAISE NOTICE '  - usage_events.total_cost';
    RAISE NOTICE '  - usage_events.provider_cost';
    RAISE NOTICE '  - usage_events.platform_markup';
    RAISE NOTICE '  - llm_usage_logs.input_tokens';
    RAISE NOTICE '  - llm_usage_logs.output_tokens';
    RAISE NOTICE 'Created triggers for automatic column synchronization';
END $$;

-- Show table structures for verification
SELECT
    'credit_transactions' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'credit_transactions'
    AND column_name IN ('balance_after', 'amount', 'cost')
ORDER BY ordinal_position;

SELECT
    'usage_events' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'usage_events'
    AND column_name IN ('cost', 'total_cost', 'provider_cost', 'platform_markup')
ORDER BY ordinal_position;

SELECT
    'llm_usage_logs' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'llm_usage_logs'
    AND column_name IN ('request_tokens', 'response_tokens', 'input_tokens', 'output_tokens')
ORDER BY ordinal_position;
