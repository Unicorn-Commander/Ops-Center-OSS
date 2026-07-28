-- ============================================================================
-- Unified LLM Management System - Seed Data: Tier Access Rules
-- Epic 3.2: Initial Tier-Based Access Rules for Subscription Plans
--
-- This script populates tier_model_rules with sensible defaults for the
-- four subscription tiers: Trial, Starter, Professional, Enterprise
--
-- TIER HIERARCHY:
-- Trial       < Starter      < Professional  < Enterprise
-- $1/week       $19/month      $49/month       $99/month
-- 100 API/day   1k API/month   10k API/month   Unlimited
--
-- ACCESS STRATEGY:
-- - Trial: Local models only (Ollama) + free cloud models (OpenRouter free tier)
-- - Starter: Trial + mid-tier cloud models (OpenRouter, Together AI)
-- - Professional: Starter + premium models (OpenAI GPT-4, Anthropic Claude)
-- - Enterprise: Everything + custom providers
--
-- Author: Backend Database Specialist
-- Date: October 27, 2025
-- Version: 1.0.0
-- ============================================================================

BEGIN;

-- ============================================================================
-- Trial Tier Rules ($1/week, 100 API calls/day)
-- ============================================================================
-- Strategy: Local models + free cloud models only

INSERT INTO tier_model_rules (tier_code, model_pattern, allowed, max_requests_per_day, max_context_length, priority)
VALUES
    -- Allow: Local Ollama models
    ('trial', 'ollama/*', TRUE, 100, 2048, 100),

    -- Allow: OpenRouter free models
    ('trial', 'openrouter/free/*', TRUE, 100, 4096, 90),
    ('trial', 'openrouter/meta-llama/llama-3-8b-instruct', TRUE, 100, 8192, 90),
    ('trial', 'openrouter/mistralai/mistral-7b-instruct', TRUE, 100, 8192, 90),

    -- Allow: Groq free tier (ultra-fast inference)
    ('trial', 'groq/*', TRUE, 100, 8192, 85),

    -- Deny: Everything else (catch-all)
    ('trial', '*', FALSE, 0, 0, 0)

ON CONFLICT (tier_code, model_pattern) DO NOTHING;

-- Trial tier complete
DO $$ BEGIN RAISE NOTICE 'Seeded Trial tier rules (local + free models)'; END $$;

-- ============================================================================
-- Starter Tier Rules ($19/month, 1,000 API calls/month)
-- ============================================================================
-- Strategy: Trial + mid-tier cloud models

INSERT INTO tier_model_rules (tier_code, model_pattern, allowed, max_requests_per_day, max_context_length, priority)
VALUES
    -- Inherit Trial access (local + free)
    ('starter', 'ollama/*', TRUE, 200, 4096, 100),
    ('starter', 'openrouter/free/*', TRUE, 200, 8192, 95),
    ('starter', 'groq/*', TRUE, 200, 8192, 90),

    -- Allow: Mid-tier OpenRouter models
    ('starter', 'openrouter/google/gemini-pro', TRUE, 50, 32768, 85),
    ('starter', 'openrouter/meta-llama/llama-3-70b-instruct', TRUE, 50, 8192, 85),
    ('starter', 'openrouter/mistralai/mixtral-8x7b-instruct', TRUE, 50, 32768, 85),

    -- Allow: Together AI models
    ('starter', 'together/*', TRUE, 100, 8192, 80),

    -- Allow: Cohere models
    ('starter', 'cohere/command', TRUE, 50, 4096, 75),

    -- Deny: Premium models (GPT-4, Claude)
    ('starter', 'openai/gpt-4*', FALSE, 0, 0, 10),
    ('starter', 'anthropic/claude*', FALSE, 0, 0, 10),

    -- Deny: Everything else
    ('starter', '*', FALSE, 0, 0, 0)

ON CONFLICT (tier_code, model_pattern) DO NOTHING;

-- Starter tier complete
DO $$ BEGIN RAISE NOTICE 'Seeded Starter tier rules (local + free + mid-tier cloud)'; END $$;

-- ============================================================================
-- Professional Tier Rules ($49/month, 10,000 API calls/month)
-- ============================================================================
-- Strategy: Starter + premium models (GPT-4, Claude)

INSERT INTO tier_model_rules (tier_code, model_pattern, allowed, max_requests_per_day, max_context_length, priority)
VALUES
    -- Inherit Starter access
    ('professional', 'ollama/*', TRUE, NULL, 8192, 100),
    ('professional', 'openrouter/*', TRUE, NULL, 200000, 95),
    ('professional', 'groq/*', TRUE, NULL, 8192, 90),
    ('professional', 'together/*', TRUE, NULL, 32768, 85),
    ('professional', 'cohere/*', TRUE, NULL, 8192, 80),

    -- Allow: OpenAI premium models
    ('professional', 'openai/gpt-4o', TRUE, 500, 128000, 75),
    ('professional', 'openai/gpt-4-turbo', TRUE, 500, 128000, 75),
    ('professional', 'openai/gpt-4', TRUE, 300, 8192, 75),
    ('professional', 'openai/gpt-3.5-turbo', TRUE, 1000, 16384, 70),

    -- Allow: Anthropic Claude models
    ('professional', 'anthropic/claude-3-5-sonnet', TRUE, 500, 200000, 75),
    ('professional', 'anthropic/claude-3-opus', TRUE, 300, 200000, 75),
    ('professional', 'anthropic/claude-3-sonnet', TRUE, 500, 200000, 70),
    ('professional', 'anthropic/claude-3-haiku', TRUE, 1000, 200000, 65),

    -- Allow: Google Gemini premium
    ('professional', 'google/gemini-pro-1.5', TRUE, 500, 1000000, 70),

    -- Deny: Custom providers (enterprise only)
    ('professional', 'custom/*', FALSE, 0, 0, 10),

    -- Allow: Everything else (less common providers)
    ('professional', '*', TRUE, 100, 8192, 5)

ON CONFLICT (tier_code, model_pattern) DO NOTHING;

-- Professional tier complete
DO $$ BEGIN RAISE NOTICE 'Seeded Professional tier rules (premium models enabled)'; END $$;

-- ============================================================================
-- Enterprise Tier Rules ($99/month, Unlimited API calls)
-- ============================================================================
-- Strategy: Unrestricted access + custom providers

INSERT INTO tier_model_rules (tier_code, model_pattern, allowed, max_requests_per_day, max_context_length, priority)
VALUES
    -- Allow: Everything with no restrictions
    ('enterprise', '*', TRUE, NULL, NULL, 100),

    -- Explicitly allow custom providers
    ('enterprise', 'custom/*', TRUE, NULL, NULL, 95),

    -- Explicitly allow all cloud providers
    ('enterprise', 'openai/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'anthropic/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'google/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'openrouter/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'together/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'cohere/*', TRUE, NULL, NULL, 90),
    ('enterprise', 'groq/*', TRUE, NULL, NULL, 90),

    -- Explicitly allow all local providers
    ('enterprise', 'ollama/*', TRUE, NULL, NULL, 85),
    ('enterprise', 'vllm/*', TRUE, NULL, NULL, 85),
    ('enterprise', 'lmstudio/*', TRUE, NULL, NULL, 85),
    ('enterprise', 'llamacpp/*', TRUE, NULL, NULL, 85)

ON CONFLICT (tier_code, model_pattern) DO NOTHING;

-- Enterprise tier complete
DO $$ BEGIN RAISE NOTICE 'Seeded Enterprise tier rules (unrestricted access)'; END $$;

-- ============================================================================
-- Free Tier Rules (Legacy Support)
-- ============================================================================
-- Strategy: Same as Trial tier, for backward compatibility

INSERT INTO tier_model_rules (tier_code, model_pattern, allowed, max_requests_per_day, max_context_length, priority)
VALUES
    ('free', 'ollama/*', TRUE, 50, 2048, 100),
    ('free', 'openrouter/free/*', TRUE, 50, 4096, 90),
    ('free', 'groq/*', TRUE, 50, 8192, 85),
    ('free', '*', FALSE, 0, 0, 0)

ON CONFLICT (tier_code, model_pattern) DO NOTHING;

-- Free tier complete
DO $$ BEGIN RAISE NOTICE 'Seeded Free tier rules (legacy support)'; END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    rule_count INTEGER;
    tier_count INTEGER;
BEGIN
    -- Count total rules
    SELECT COUNT(*) INTO rule_count FROM tier_model_rules;

    -- Count distinct tiers
    SELECT COUNT(DISTINCT tier_code) INTO tier_count FROM tier_model_rules;

    RAISE NOTICE 'Seeded % rules across % tiers', rule_count, tier_count;

    IF tier_count < 5 THEN
        RAISE WARNING 'Expected 5 tiers (free, trial, starter, professional, enterprise), found %', tier_count;
    END IF;

    IF rule_count < 20 THEN
        RAISE WARNING 'Expected at least 20 rules, found %', rule_count;
    END IF;
END;
$$;

-- Display summary by tier
SELECT
    tier_code,
    COUNT(*) as total_rules,
    SUM(CASE WHEN allowed THEN 1 ELSE 0 END) as allow_rules,
    SUM(CASE WHEN NOT allowed THEN 1 ELSE 0 END) as deny_rules,
    MAX(max_requests_per_day) as max_daily_requests
FROM tier_model_rules
GROUP BY tier_code
ORDER BY
    CASE tier_code
        WHEN 'free' THEN 1
        WHEN 'trial' THEN 2
        WHEN 'starter' THEN 3
        WHEN 'professional' THEN 4
        WHEN 'enterprise' THEN 5
        ELSE 999
    END;

COMMIT;

-- ============================================================================
-- Seed Complete
-- ============================================================================

-- USAGE EXAMPLES:
--
-- 1. Check if user can access a model:
--    SELECT allowed FROM tier_model_rules
--    WHERE tier_code = 'starter'
--    AND 'openai/gpt-4' LIKE model_pattern
--    ORDER BY priority DESC
--    LIMIT 1;
--
-- 2. Get all allowed models for a tier:
--    SELECT model_pattern FROM tier_model_rules
--    WHERE tier_code = 'professional'
--    AND allowed = TRUE
--    ORDER BY priority DESC;
--
-- 3. Check daily quota:
--    SELECT max_requests_per_day FROM tier_model_rules
--    WHERE tier_code = 'trial'
--    AND 'ollama/llama3' LIKE model_pattern
--    AND allowed = TRUE
--    ORDER BY priority DESC
--    LIMIT 1;
