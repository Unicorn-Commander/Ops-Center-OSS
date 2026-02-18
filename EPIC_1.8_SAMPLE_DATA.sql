-- Epic 1.8: Credit & Usage Metering System - Sample Test Data
-- Date: October 24, 2025
-- Purpose: Realistic test data for Epic 1.8 testing
--
-- Contents:
-- - 5 test users with different tiers
-- - 10 sample credit transactions
-- - 3 active coupon codes
-- - 5 usage events
-- - 2 OpenRouter BYOK accounts

-- ============================================================================
-- CLEANUP (Optional - only run if you want to start fresh)
-- ============================================================================

-- Uncomment to clear existing test data:
-- DELETE FROM usage_events WHERE user_id LIKE 'test-user-%';
-- DELETE FROM credit_transactions WHERE user_id LIKE 'test-user-%';
-- DELETE FROM openrouter_accounts WHERE user_id LIKE 'test-user-%';
-- DELETE FROM coupon_codes WHERE code LIKE 'TEST%';
-- DELETE FROM user_credits WHERE user_id LIKE 'test-user-%';

-- ============================================================================
-- TEST USERS (5 users with different tiers and balances)
-- ============================================================================

-- User 1: Trial tier - Active, some credits remaining
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
)
VALUES (
    'test-user-trial-001',
    3.50,  -- Remaining credits
    5.00,  -- Allocated monthly
    'trial',
    5.00,  -- Monthly cap
    NOW() + INTERVAL '25 days'  -- Reset in 25 days
)
ON CONFLICT (user_id) DO UPDATE SET
    credits_remaining = EXCLUDED.credits_remaining,
    credits_allocated = EXCLUDED.credits_allocated,
    tier = EXCLUDED.tier,
    monthly_cap = EXCLUDED.monthly_cap,
    last_reset = EXCLUDED.last_reset,
    updated_at = NOW();

-- User 2: Starter tier - Almost depleted
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
)
VALUES (
    'test-user-starter-002',
    2.00,  -- Almost out
    20.00,
    'starter',
    20.00,
    NOW() + INTERVAL '15 days'
)
ON CONFLICT (user_id) DO UPDATE SET
    credits_remaining = EXCLUDED.credits_remaining,
    credits_allocated = EXCLUDED.credits_allocated,
    tier = EXCLUDED.tier,
    monthly_cap = EXCLUDED.monthly_cap,
    last_reset = EXCLUDED.last_reset,
    updated_at = NOW();

-- User 3: Professional tier - Plenty of credits
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
)
VALUES (
    'test-user-professional-003',
    45.00,  -- Plenty remaining
    60.00,
    'professional',
    60.00,
    NOW() + INTERVAL '20 days'
)
ON CONFLICT (user_id) DO UPDATE SET
    credits_remaining = EXCLUDED.credits_remaining,
    credits_allocated = EXCLUDED.credits_allocated,
    tier = EXCLUDED.tier,
    monthly_cap = EXCLUDED.monthly_cap,
    last_reset = EXCLUDED.last_reset,
    updated_at = NOW();

-- User 4: Enterprise tier - Unlimited
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
)
VALUES (
    'test-user-enterprise-004',
    999999.00,  -- Unlimited
    999999.99,
    'enterprise',
    NULL,  -- No cap
    NOW() + INTERVAL '30 days'
)
ON CONFLICT (user_id) DO UPDATE SET
    credits_remaining = EXCLUDED.credits_remaining,
    credits_allocated = EXCLUDED.credits_allocated,
    tier = EXCLUDED.tier,
    monthly_cap = EXCLUDED.monthly_cap,
    last_reset = EXCLUDED.last_reset,
    updated_at = NOW();

-- User 5: Trial tier - No credits left (test edge case)
INSERT INTO user_credits (
    user_id, credits_remaining, credits_allocated, tier, monthly_cap, last_reset
)
VALUES (
    'test-user-depleted-005',
    0.00,  -- Depleted
    5.00,
    'trial',
    5.00,
    NOW() + INTERVAL '5 days'  -- Reset soon
)
ON CONFLICT (user_id) DO UPDATE SET
    credits_remaining = EXCLUDED.credits_remaining,
    credits_allocated = EXCLUDED.credits_allocated,
    tier = EXCLUDED.tier,
    monthly_cap = EXCLUDED.monthly_cap,
    last_reset = EXCLUDED.last_reset,
    updated_at = NOW();

-- ============================================================================
-- CREDIT TRANSACTIONS (10 transactions showing various operations)
-- ============================================================================

-- Transaction 1: Initial allocation (trial user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-trial-001',
    5.00,
    5.00,
    'allocation',
    NULL,
    NULL,
    NULL,
    '{"tier": "trial", "reason": "initial_allocation"}',
    NOW() - INTERVAL '30 days'
);

-- Transaction 2: Deduction (LLM API call)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-trial-001',
    -1.50,
    3.50,
    'deduction',
    'openrouter',
    'gpt-4',
    '{"provider_cost": 1.20, "markup": 0.30}',
    '{"tokens": 1500, "prompt_tokens": 1000, "completion_tokens": 500}',
    NOW() - INTERVAL '5 days'
);

-- Transaction 3: Coupon redemption (starter user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-starter-002',
    10.00,
    30.00,
    'allocation',
    NULL,
    NULL,
    NULL,
    '{"source": "coupon", "coupon_code": "WELCOME10"}',
    NOW() - INTERVAL '20 days'
);

-- Transaction 4: Multiple API calls (starter user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-starter-002',
    -3.00,
    27.00,
    'deduction',
    'openrouter',
    'claude-3-opus',
    '{"provider_cost": 2.50, "markup": 0.50}',
    '{"tokens": 2000}',
    NOW() - INTERVAL '18 days'
);

-- Transaction 5: Embedding service (starter user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-starter-002',
    -0.50,
    26.50,
    'deduction',
    'embedding',
    'text-embedding-ada-002',
    '{"provider_cost": 0.40, "markup": 0.10}',
    '{"tokens": 500}',
    NOW() - INTERVAL '15 days'
);

-- Transaction 6: Professional tier allocation
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-professional-003',
    60.00,
    60.00,
    'allocation',
    NULL,
    NULL,
    NULL,
    '{"tier": "professional", "reason": "monthly_reset"}',
    NOW() - INTERVAL '10 days'
);

-- Transaction 7: Large batch processing (professional user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-professional-003',
    -15.00,
    45.00,
    'deduction',
    'openrouter',
    'gpt-4',
    '{"provider_cost": 12.00, "markup": 3.00}',
    '{"tokens": 15000, "batch_size": 10}',
    NOW() - INTERVAL '8 days'
);

-- Transaction 8: Refund (professional user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-professional-003',
    5.00,
    50.00,
    'refund',
    'openrouter',
    'gpt-4',
    NULL,
    '{"reason": "API error - request failed", "original_transaction_id": 7}',
    NOW() - INTERVAL '7 days'
);

-- Transaction 9: Enterprise allocation (unlimited)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-enterprise-004',
    999999.99,
    999999.99,
    'allocation',
    NULL,
    NULL,
    NULL,
    '{"tier": "enterprise", "reason": "unlimited_allocation"}',
    NOW() - INTERVAL '30 days'
);

-- Transaction 10: Bonus credits (depleted user)
INSERT INTO credit_transactions (
    user_id, amount, balance_after, transaction_type, service, model,
    cost_breakdown, metadata, created_at
)
VALUES (
    'test-user-depleted-005',
    2.00,
    2.00,
    'allocation',
    NULL,
    NULL,
    NULL,
    '{"source": "bonus", "reason": "customer_satisfaction"}',
    NOW() - INTERVAL '3 days'
);

-- ============================================================================
-- COUPON CODES (3 active coupons for testing)
-- ============================================================================

-- Coupon 1: Welcome bonus (credit_bonus)
INSERT INTO coupon_codes (
    code, coupon_type, value, description, max_uses, used_count,
    expires_at, is_active, created_by, created_at
)
VALUES (
    'WELCOME10',
    'credit_bonus',
    10.00,
    'Welcome bonus: 10 free credits for new users',
    100,
    5,  -- Already used 5 times
    NOW() + INTERVAL '90 days',
    true,
    'admin',
    NOW() - INTERVAL '30 days'
)
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description,
    max_uses = EXCLUDED.max_uses,
    expires_at = EXCLUDED.expires_at,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Coupon 2: Limited time offer (percentage_discount)
INSERT INTO coupon_codes (
    code, coupon_type, value, description, max_uses, used_count,
    expires_at, is_active, created_by, created_at
)
VALUES (
    'SUMMER2025',
    'percentage_discount',
    25.00,  -- 25% off
    'Summer sale: 25% off all subscriptions',
    500,
    42,
    NOW() + INTERVAL '60 days',
    true,
    'admin',
    NOW() - INTERVAL '15 days'
)
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description,
    max_uses = EXCLUDED.max_uses,
    expires_at = EXCLUDED.expires_at,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Coupon 3: Fixed discount (for testing redemption)
INSERT INTO coupon_codes (
    code, coupon_type, value, description, max_uses, used_count,
    expires_at, is_active, created_by, created_at
)
VALUES (
    'TEST5OFF',
    'fixed_discount',
    5.00,
    'Test coupon: $5 off subscription',
    10,
    0,  -- Not used yet
    NOW() + INTERVAL '30 days',
    true,
    'admin',
    NOW() - INTERVAL '1 day'
)
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description,
    max_uses = EXCLUDED.max_uses,
    expires_at = EXCLUDED.expires_at,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ============================================================================
-- USAGE EVENTS (5 events for metering tests)
-- ============================================================================

-- Event 1: LLM completion (trial user)
INSERT INTO usage_events (
    user_id, service, model, tokens_used, provider_cost,
    platform_markup, total_cost, is_free_tier, metadata, created_at
)
VALUES (
    'test-user-trial-001',
    'openrouter',
    'gpt-4',
    1500,
    1.20,
    0.30,
    1.50,
    false,
    '{"prompt_tokens": 1000, "completion_tokens": 500, "response_time_ms": 2500}',
    NOW() - INTERVAL '5 days'
);

-- Event 2: Embedding (starter user)
INSERT INTO usage_events (
    user_id, service, model, tokens_used, provider_cost,
    platform_markup, total_cost, is_free_tier, metadata, created_at
)
VALUES (
    'test-user-starter-002',
    'embedding',
    'text-embedding-ada-002',
    500,
    0.40,
    0.10,
    0.50,
    false,
    '{"dimension": 1536, "response_time_ms": 150}',
    NOW() - INTERVAL '15 days'
);

-- Event 3: TTS (Text-to-Speech) (professional user)
INSERT INTO usage_events (
    user_id, service, model, tokens_used, provider_cost,
    platform_markup, total_cost, is_free_tier, metadata, created_at
)
VALUES (
    'test-user-professional-003',
    'tts',
    'unicorn-orator',
    NULL,  -- TTS doesn't use tokens
    0.50,
    0.10,
    0.60,
    false,
    '{"characters": 250, "voice": "af", "response_time_ms": 800}',
    NOW() - INTERVAL '8 days'
);

-- Event 4: Free tier usage (trial user)
INSERT INTO usage_events (
    user_id, service, model, tokens_used, provider_cost,
    platform_markup, total_cost, is_free_tier, metadata, created_at
)
VALUES (
    'test-user-trial-001',
    'openrouter',
    'gpt-3.5-turbo',
    800,
    0.00,  -- Free tier, no cost
    0.00,
    0.00,
    true,
    '{"free_tier": true, "daily_limit": 100}',
    NOW() - INTERVAL '2 days'
);

-- Event 5: Large batch processing (enterprise user)
INSERT INTO usage_events (
    user_id, service, model, tokens_used, provider_cost,
    platform_markup, total_cost, is_free_tier, metadata, created_at
)
VALUES (
    'test-user-enterprise-004',
    'openrouter',
    'claude-3-opus',
    25000,
    50.00,
    10.00,
    60.00,
    false,
    '{"batch_size": 50, "parallel_requests": 10, "response_time_ms": 15000}',
    NOW() - INTERVAL '3 days'
);

-- ============================================================================
-- OPENROUTER BYOK ACCOUNTS (2 accounts for testing)
-- ============================================================================

-- Account 1: Starter user with BYOK
INSERT INTO openrouter_accounts (
    user_id, openrouter_api_key_encrypted, email, account_id,
    free_credits_remaining, is_active, last_synced, created_at
)
VALUES (
    'test-user-starter-002',
    'gAAAAABmZ3h5dGVzdC1lbmNyeXB0ZWQta2V5LTEyMzQ1Njc4OTA=',  -- Fake encrypted key
    'test-starter@example.com',
    'or-acct-starter-002',
    5.00,  -- $5 free credits from OpenRouter
    true,
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '20 days'
)
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    account_id = EXCLUDED.account_id,
    free_credits_remaining = EXCLUDED.free_credits_remaining,
    is_active = EXCLUDED.is_active,
    last_synced = EXCLUDED.last_synced,
    updated_at = NOW();

-- Account 2: Professional user with BYOK
INSERT INTO openrouter_accounts (
    user_id, openrouter_api_key_encrypted, email, account_id,
    free_credits_remaining, is_active, last_synced, created_at
)
VALUES (
    'test-user-professional-003',
    'gAAAAABmZ3h5dGVzdC1lbmNyeXB0ZWQta2V5LXByb2Zlc3Npb25hbA==',  -- Fake encrypted key
    'test-pro@example.com',
    'or-acct-pro-003',
    15.00,  -- $15 free credits from OpenRouter
    true,
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '10 days'
)
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    account_id = EXCLUDED.account_id,
    free_credits_remaining = EXCLUDED.free_credits_remaining,
    is_active = EXCLUDED.is_active,
    last_synced = EXCLUDED.last_synced,
    updated_at = NOW();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Uncomment to verify data was inserted correctly:

-- SELECT 'User Credits' as table_name, COUNT(*) as count FROM user_credits WHERE user_id LIKE 'test-user-%'
-- UNION ALL
-- SELECT 'Credit Transactions', COUNT(*) FROM credit_transactions WHERE user_id LIKE 'test-user-%'
-- UNION ALL
-- SELECT 'Coupon Codes', COUNT(*) FROM coupon_codes WHERE code LIKE 'TEST%' OR code LIKE '%2025'
-- UNION ALL
-- SELECT 'Usage Events', COUNT(*) FROM usage_events WHERE user_id LIKE 'test-user-%'
-- UNION ALL
-- SELECT 'OpenRouter Accounts', COUNT(*) FROM openrouter_accounts WHERE user_id LIKE 'test-user-%';

-- ============================================================================
-- TESTING SCENARIOS
-- ============================================================================

-- After loading this data, you can test:
--
-- 1. Credit Balance Query:
--    SELECT * FROM user_credits WHERE user_id = 'test-user-trial-001';
--
-- 2. Transaction History:
--    SELECT * FROM credit_transactions WHERE user_id = 'test-user-starter-002' ORDER BY created_at DESC;
--
-- 3. Coupon Validation:
--    SELECT * FROM coupon_codes WHERE code = 'WELCOME10' AND is_active = true;
--
-- 4. Usage Metrics:
--    SELECT service, COUNT(*), SUM(total_cost)
--    FROM usage_events
--    WHERE user_id = 'test-user-professional-003'
--    GROUP BY service;
--
-- 5. OpenRouter BYOK:
--    SELECT user_id, email, free_credits_remaining, last_synced
--    FROM openrouter_accounts
--    WHERE is_active = true;

-- ============================================================================
-- END OF SAMPLE DATA
-- ============================================================================
