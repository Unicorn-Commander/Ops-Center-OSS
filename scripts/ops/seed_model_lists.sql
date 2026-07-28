-- ============================================================================
-- Seed default curated model lists (idempotent)
--
-- SQL translation of backend/scripts/seed_model_lists.py against the CURRENT
-- converged schema (backend/migrations/model_lists_schema.sql, including the
-- 2026-07-02 convergence patch that added the columns the application code
-- actually reads: is_active / is_featured / tier_*_access / metadata JSONB).
--
-- Differences from the Python script, on purpose:
--   * Fully idempotent via INSERT ... ON CONFLICT DO NOTHING — re-running
--     NEVER overwrites admin edits (the Python script re-seeds/updates rows).
--   * The Global list gets app_identifier = 'global' (the Python script used
--     NULL; the admin UI and the /model-lists APIs match on app_identifier).
--   * Items populate BOTH the legacy display columns (description / is_free /
--     context_length / tier_trial..tier_byok) AND the code-expected columns
--     (is_active, is_featured, tier_*_access, metadata). description,
--     context_length and is_free are mirrored into metadata because the
--     admin API only returns the metadata column, not the legacy columns.
--   * The legacy tier_vip_founder / tier_byok flags are set TRUE exactly as
--     the Python seed did; the converged API tier columns cover only
--     trial/starter/professional/enterprise.
--
-- Usage (run manually against the Ops-Center database — this file is never
-- executed automatically):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/ops/seed_model_lists.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1) Lists
--    ON CONFLICT DO NOTHING (no arbiter) also tolerates the partial unique
--    index idx_unique_default_per_app on (app_identifier) WHERE is_default.
-- ----------------------------------------------------------------------------
INSERT INTO app_model_lists (name, slug, description, app_identifier, is_default, is_active, created_by)
VALUES
    ('Global Default', 'global',
     'Best FREE models for all apps - used as fallback when no app-specific list exists',
     'global', TRUE, TRUE, 'system'),
    ('Bolt.diy Coding', 'bolt-diy',
     'Coding-focused models optimized for AI development environment',
     'bolt-diy', TRUE, TRUE, 'system'),
    ('Presenton Content', 'presenton',
     'Content generation models optimized for AI presentation creation',
     'presenton', TRUE, TRUE, 'system'),
    ('Open-WebUI General', 'open-webui',
     'General purpose models for the main chat interface',
     'open-webui', TRUE, TRUE, 'system')
ON CONFLICT DO NOTHING;

-- If the Global list already existed with the legacy NULL app_identifier
-- (created by the original model_lists_schema.sql seed), converge it to the
-- string 'global' WITHOUT touching any other admin-edited fields.
UPDATE app_model_lists
SET app_identifier = 'global'
WHERE slug = 'global' AND app_identifier IS NULL;

-- ----------------------------------------------------------------------------
-- 2) Items — Global Default (slug 'global')
-- ----------------------------------------------------------------------------
INSERT INTO app_model_list_items (
    list_id, model_id, display_name, description, category, sort_order,
    is_free, context_length,
    tier_trial, tier_starter, tier_professional, tier_enterprise, tier_vip_founder, tier_byok,
    is_active, is_featured,
    tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
    metadata
)
SELECT l.id, v.model_id, v.display_name, v.description, v.category, v.sort_order,
       v.is_free, v.context_length,
       TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
       TRUE, FALSE,
       TRUE, TRUE, TRUE, TRUE,
       jsonb_build_object(
           'description', v.description,
           'is_free', v.is_free,
           'context_length', v.context_length
       )
FROM (
    VALUES
        ('qwen/qwen3-coder:free', 'Qwen3 Coder (Free)',
         'Best FREE coding model - excellent for code generation and debugging',
         'coding', 1, TRUE, 262144),
        ('deepseek/deepseek-r1:free', 'DeepSeek R1 (Free)',
         'Excellent for complex reasoning and problem solving',
         'reasoning', 2, TRUE, 163840),
        ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash (Free)',
         'Fast, versatile model for general tasks with large context',
         'general', 3, TRUE, 1048576),
        ('google/gemini-2.5-flash-preview-05-20:free', 'Gemini 2.5 Flash Preview (Free)',
         'Latest Gemini preview with improved capabilities',
         'fast', 4, TRUE, 1048576),
        ('mistralai/mistral-small-3.1-24b-instruct:free', 'Mistral Small 3.1 (Free)',
         'Efficient small model for quick responses',
         'general', 5, TRUE, 32768),
        ('meta-llama/llama-3.3-70b-instruct:free', 'Llama 3.3 70B (Free)',
         'Large open-source model with great general performance',
         'general', 6, TRUE, 131072)
) AS v(model_id, display_name, description, category, sort_order, is_free, context_length)
JOIN app_model_lists l ON l.slug = 'global'
ON CONFLICT (list_id, model_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3) Items — Bolt.diy Coding (slug 'bolt-diy')
-- ----------------------------------------------------------------------------
INSERT INTO app_model_list_items (
    list_id, model_id, display_name, description, category, sort_order,
    is_free, context_length,
    tier_trial, tier_starter, tier_professional, tier_enterprise, tier_vip_founder, tier_byok,
    is_active, is_featured,
    tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
    metadata
)
SELECT l.id, v.model_id, v.display_name, v.description, v.category, v.sort_order,
       v.is_free, v.context_length,
       TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
       TRUE, FALSE,
       TRUE, TRUE, TRUE, TRUE,
       jsonb_build_object(
           'description', v.description,
           'is_free', v.is_free,
           'context_length', v.context_length
       )
FROM (
    VALUES
        ('qwen/qwen3-coder:free', 'Qwen3 Coder (Free)',
         'Best FREE coding model - ideal for code generation, debugging, and refactoring',
         'coding', 1, TRUE, 262144),
        ('deepseek/deepseek-r1:free', 'DeepSeek R1 (Free)',
         'Great for complex problems requiring step-by-step reasoning',
         'reasoning', 2, TRUE, 163840),
        ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash (Free)',
         'Fast iterations with massive 1M context window',
         'fast', 3, TRUE, 1048576),
        ('meta-llama/llama-3.3-70b-instruct:free', 'Llama 3.3 70B (Free)',
         'Strong general performance for various coding tasks',
         'general', 4, TRUE, 131072),
        ('mistralai/mistral-small-3.1-24b-instruct:free', 'Mistral Small 3.1 (Free)',
         'Efficient model for quick code completions',
         'general', 5, TRUE, 32768),
        ('deepseek/deepseek-chat-v3-0324:free', 'DeepSeek Chat V3 (Free)',
         'Good all-around model for code discussion',
         'general', 6, TRUE, 65536)
) AS v(model_id, display_name, description, category, sort_order, is_free, context_length)
JOIN app_model_lists l ON l.slug = 'bolt-diy'
ON CONFLICT (list_id, model_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 4) Items — Presenton Content (slug 'presenton')
-- ----------------------------------------------------------------------------
INSERT INTO app_model_list_items (
    list_id, model_id, display_name, description, category, sort_order,
    is_free, context_length,
    tier_trial, tier_starter, tier_professional, tier_enterprise, tier_vip_founder, tier_byok,
    is_active, is_featured,
    tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
    metadata
)
SELECT l.id, v.model_id, v.display_name, v.description, v.category, v.sort_order,
       v.is_free, v.context_length,
       TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
       TRUE, FALSE,
       TRUE, TRUE, TRUE, TRUE,
       jsonb_build_object(
           'description', v.description,
           'is_free', v.is_free,
           'context_length', v.context_length
       )
FROM (
    VALUES
        ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash (Free)',
         'Excellent for presentations - fast, creative, and handles long content well',
         'general', 1, TRUE, 1048576),
        ('deepseek/deepseek-chat-v3-0324:free', 'DeepSeek Chat V3 (Free)',
         'Good for generating well-structured presentation content',
         'general', 2, TRUE, 65536),
        ('mistralai/mistral-small-3.1-24b-instruct:free', 'Mistral Small 3.1 (Free)',
         'Creative writing and engaging slide narratives',
         'creative', 3, TRUE, 32768),
        ('meta-llama/llama-3.3-70b-instruct:free', 'Llama 3.3 70B (Free)',
         'Strong general performance for diverse presentation topics',
         'general', 4, TRUE, 131072),
        ('google/gemini-2.5-flash-preview-05-20:free', 'Gemini 2.5 Flash Preview (Free)',
         'Latest preview with improved content generation',
         'fast', 5, TRUE, 1048576)
) AS v(model_id, display_name, description, category, sort_order, is_free, context_length)
JOIN app_model_lists l ON l.slug = 'presenton'
ON CONFLICT (list_id, model_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5) Items — Open-WebUI General (slug 'open-webui')
-- ----------------------------------------------------------------------------
INSERT INTO app_model_list_items (
    list_id, model_id, display_name, description, category, sort_order,
    is_free, context_length,
    tier_trial, tier_starter, tier_professional, tier_enterprise, tier_vip_founder, tier_byok,
    is_active, is_featured,
    tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
    metadata
)
SELECT l.id, v.model_id, v.display_name, v.description, v.category, v.sort_order,
       v.is_free, v.context_length,
       TRUE, TRUE, TRUE, TRUE, TRUE, TRUE,
       TRUE, FALSE,
       TRUE, TRUE, TRUE, TRUE,
       jsonb_build_object(
           'description', v.description,
           'is_free', v.is_free,
           'context_length', v.context_length
       )
FROM (
    VALUES
        ('google/gemini-2.0-flash-exp:free', 'Gemini 2.0 Flash (Free)',
         'Best all-around model - fast, capable, and free',
         'general', 1, TRUE, 1048576),
        ('meta-llama/llama-3.3-70b-instruct:free', 'Llama 3.3 70B (Free)',
         'Large open-source model for comprehensive responses',
         'general', 2, TRUE, 131072),
        ('deepseek/deepseek-r1:free', 'DeepSeek R1 (Free)',
         'Advanced reasoning for complex questions',
         'reasoning', 3, TRUE, 163840),
        ('mistralai/mistral-small-3.1-24b-instruct:free', 'Mistral Small 3.1 (Free)',
         'Quick and efficient for everyday queries',
         'general', 4, TRUE, 32768),
        ('qwen/qwen3-coder:free', 'Qwen3 Coder (Free)',
         'Specialized for coding-related questions',
         'coding', 5, TRUE, 262144)
) AS v(model_id, display_name, description, category, sort_order, is_free, context_length)
JOIN app_model_lists l ON l.slug = 'open-webui'
ON CONFLICT (list_id, model_id) DO NOTHING;

COMMIT;
