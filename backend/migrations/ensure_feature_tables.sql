-- ============================================================================
-- ensure_feature_tables.sql  —  IDEMPOTENT FEATURE-TABLE ENSURE MIGRATION
-- ----------------------------------------------------------------------------
-- Date: 2026-06-08
-- Database: unicorn_db (PostgreSQL, owner role: unicorn)
--
-- PURPOSE
--   A number of Ops-Center admin endpoints were returning HTTP 500 because the
--   feature tables/views they SELECT/INSERT against do not exist on the dev DB.
--   This file creates EVERY one of those missing tables (and one view) in a
--   single, dependency-ordered, fully-idempotent script.
--
-- HOW IT IS APPLIED
--   - Manually:   psql -U unicorn -d unicorn_db -f migrations/ensure_feature_tables.sql
--   - On startup: the backend runs this on every boot, so it MUST be safe to
--                 run repeatedly. Therefore:
--                   * every table  -> CREATE TABLE IF NOT EXISTS
--                   * every index  -> CREATE INDEX IF NOT EXISTS
--                   * every view   -> CREATE OR REPLACE VIEW
--                   * every seed   -> INSERT ... ON CONFLICT DO NOTHING
--                   * every trigger-> DROP TRIGGER IF EXISTS ... then CREATE
--                 NO DROP TABLE / TRUNCATE / unconditional CREATE INDEX anywhere.
--
-- WHAT IT DOES *NOT* TOUCH (these already exist; we never recreate or ALTER them)
--   add_ons, api_keys, user_api_keys, billing_events, organization_credit_pools,
--   subscription_tiers, organizations, organization_members,
--   organization_subscriptions.
--
-- COLUMN-PARITY NOTES
--   Several source schemas predate the handler code and use different column
--   names than the queries that 500'd. Where that happened, the EXTRA
--   handler-required columns are added IN ADDITION to the original columns and
--   are flagged with a "HANDLER-PARITY" comment so the actual API queries
--   succeed. No existing-table columns are altered.
-- ============================================================================

-- Required for gen_random_uuid()/uuid_generate_v4() used below.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Shared trigger function for updated_at maintenance (idempotent definition).
-- 001_organization_tables.sql also defines update_updated_at_column(); we use a
-- dedicated name here so this file is self-contained even if that ran or not.
-- ============================================================================
CREATE OR REPLACE FUNCTION eft_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 1. platform_settings   (inline — canonical CREATE in platform_settings_api.py:307)
--    Handler: platform_keys_api.get_platform_key_from_db
--      SELECT value FROM platform_settings WHERE key=$1 AND category='api_keys' AND is_secret=TRUE
-- ============================================================================
CREATE TABLE IF NOT EXISTS platform_settings (
    key        VARCHAR(255) PRIMARY KEY,
    value      TEXT,
    category   VARCHAR(100),
    is_secret  BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_platform_settings_category ON platform_settings(category);


-- ============================================================================
-- 2. landing_page_settings   (inline — derived from landing_page_settings_api.py
--    GET selects: landing_page_mode, branding, sso_enabled, allow_registration,
--                 show_pricing, show_features, custom_css_url, custom_js_url,
--                 announcement_banner, created_at, updated_at, updated_by,
--                 and filters WHERE is_active = true
--    INSERT cols: ... is_active, created_by, updated_by
--    UPDATE uses: id (PK)
-- ============================================================================
CREATE TABLE IF NOT EXISTS landing_page_settings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    landing_page_mode   VARCHAR(50) NOT NULL DEFAULT 'direct_sso',
    branding            JSONB,
    sso_enabled         BOOLEAN DEFAULT TRUE,
    allow_registration  BOOLEAN DEFAULT FALSE,
    show_pricing        BOOLEAN DEFAULT TRUE,
    show_features       BOOLEAN DEFAULT TRUE,
    custom_css_url      TEXT,
    custom_js_url       TEXT,
    announcement_banner JSONB,
    is_active           BOOLEAN DEFAULT TRUE,
    created_by          VARCHAR(255),
    updated_by          VARCHAR(255),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_landing_page_settings_active ON landing_page_settings(is_active);

DROP TRIGGER IF EXISTS trg_landing_page_settings_updated_at ON landing_page_settings;
CREATE TRIGGER trg_landing_page_settings_updated_at
    BEFORE UPDATE ON landing_page_settings
    FOR EACH ROW EXECUTE FUNCTION eft_set_updated_at();


-- ============================================================================
-- 3. credit_transactions   (source: migrations/create_credit_system_tables.sql)
--    Handler A: litellm_credit_system.get_credit_history
--       SELECT id, amount, transaction_type, provider, model, tokens_used,
--              cost, metadata, created_at FROM credit_transactions WHERE user_id=$1
--    Handler B: billing_analytics_api.get_usage_summary
--       SELECT SUM(credits_consumed) FROM credit_transactions WHERE created_at >= ...
--    => 'credits_consumed' is NOT in the source schema; added below as
--       HANDLER-PARITY so get_usage_summary stops 500'ing.
-- ============================================================================
CREATE TABLE IF NOT EXISTS credit_transactions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          VARCHAR(255) NOT NULL,
    amount           DECIMAL(12, 6) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    provider         VARCHAR(100),
    model            VARCHAR(200),
    tokens_used      INTEGER,
    cost             DECIMAL(12, 6),
    metadata         JSONB,
    -- HANDLER-PARITY: billing_analytics_api.get_usage_summary aggregates this
    -- column. Not in the original credit-system schema; added so SUM() resolves.
    credits_consumed DECIMAL(12, 6),
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('usage', 'purchase', 'bonus', 'refund', 'adjustment')
    )
);

CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id    ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type       ON credit_transactions(transaction_type);


-- ============================================================================
-- 4. credit_packages   (source: migrations/add_credit_purchases.sql)
--    Defined BEFORE credit_purchases for readability (no FK between them).
-- ============================================================================
CREATE TABLE IF NOT EXISTS credit_packages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_code        VARCHAR(50) UNIQUE NOT NULL,
    package_name        VARCHAR(100) NOT NULL,
    description         TEXT,
    credits             INTEGER NOT NULL,
    price_usd           DECIMAL(10, 2) NOT NULL,
    discount_percentage INTEGER DEFAULT 0,
    stripe_price_id     VARCHAR(255),
    stripe_product_id   VARCHAR(255),
    is_active           BOOLEAN DEFAULT TRUE,
    display_order       INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT credits_positive CHECK (credits > 0),
    CONSTRAINT price_positive   CHECK (price_usd > 0),
    CONSTRAINT discount_valid   CHECK (discount_percentage >= 0 AND discount_percentage <= 100)
);

-- Schema convergence: some older deployments created credit_packages with a
-- legacy shape (id integer, name/price_cents NOT NULL, no stripe_* columns).
-- CREATE TABLE IF NOT EXISTS above is a no-op there, so additively reconcile to
-- the canonical columns the app reads, and relax legacy NOT NULLs the current
-- code doesn't populate. Idempotent + safe on canonical nodes (all no-ops).
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS stripe_price_id   VARCHAR(255);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS stripe_product_id VARCHAR(255);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW();
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'credit_packages' AND column_name = 'name'
               AND is_nullable = 'NO') THEN
        ALTER TABLE credit_packages ALTER COLUMN name DROP NOT NULL;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'credit_packages' AND column_name = 'price_cents'
               AND is_nullable = 'NO') THEN
        ALTER TABLE credit_packages ALTER COLUMN price_cents DROP NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_credit_packages_code   ON credit_packages(package_code);
CREATE INDEX IF NOT EXISTS idx_credit_packages_active ON credit_packages(is_active);

-- Seed default packages (idempotent).
INSERT INTO credit_packages (package_code, package_name, description, credits, price_usd, discount_percentage, display_order)
VALUES
    ('starter',    'Starter Pack',    '1,000 credits - Perfect for trying out the platform', 1000,  10.00,  0, 1),
    ('standard',   'Standard Pack',   '5,000 credits - Best value with 10% discount',         5000,  45.00, 10, 2),
    ('pro',        'Pro Pack',        '10,000 credits - Popular choice with 20% discount',    10000,  80.00, 20, 3),
    ('enterprise', 'Enterprise Pack', '50,000 credits - Maximum value with 30% discount',     50000, 350.00, 30, 4)
ON CONFLICT (package_code) DO NOTHING;


-- ============================================================================
-- 5. credit_purchases   (source: migrations/add_credit_purchases.sql)
--    Handler: credit_purchase_api.admin_list_all_purchases
--       SELECT id, package_name, amount_credits, amount_paid, status,
--              created_at, completed_at, stripe_payment_id FROM credit_purchases
--    All columns present in the source schema. Triggers ported idempotently.
-- ============================================================================
CREATE TABLE IF NOT EXISTS credit_purchases (
    id                         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                    VARCHAR(255) NOT NULL,
    package_name               VARCHAR(100) NOT NULL,
    amount_credits             DECIMAL(12, 6) NOT NULL,
    amount_paid                DECIMAL(10, 2) NOT NULL,
    discount_applied           DECIMAL(10, 2) DEFAULT 0.0,
    stripe_payment_id          VARCHAR(255) UNIQUE,
    stripe_checkout_session_id VARCHAR(255),
    stripe_payment_intent_id   VARCHAR(255),
    status                     VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at               TIMESTAMP WITH TIME ZONE,
    updated_at                 TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata                   JSONB,
    CONSTRAINT valid_purchase_status CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'refunded')
    ),
    CONSTRAINT amount_credits_positive CHECK (amount_credits > 0),
    CONSTRAINT amount_paid_positive    CHECK (amount_paid > 0)
);

CREATE INDEX IF NOT EXISTS idx_credit_purchases_user_id        ON credit_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_status         ON credit_purchases(status);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_created_at     ON credit_purchases(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_stripe_payment ON credit_purchases(stripe_payment_id);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_stripe_session ON credit_purchases(stripe_checkout_session_id);

-- updated_at trigger for credit_purchases + credit_packages (idempotent).
CREATE OR REPLACE FUNCTION update_credit_purchases_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_credit_purchases_timestamp ON credit_purchases;
CREATE TRIGGER trigger_update_credit_purchases_timestamp
    BEFORE UPDATE ON credit_purchases
    FOR EACH ROW EXECUTE FUNCTION update_credit_purchases_timestamp();

DROP TRIGGER IF EXISTS trigger_update_credit_packages_timestamp ON credit_packages;
CREATE TRIGGER trigger_update_credit_packages_timestamp
    BEFORE UPDATE ON credit_packages
    FOR EACH ROW EXECUTE FUNCTION update_credit_purchases_timestamp();


-- ============================================================================
-- 6. openrouter_accounts   (source: migrations/create_credit_system_tables.sql)
-- ============================================================================
CREATE TABLE IF NOT EXISTS openrouter_accounts (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                     VARCHAR(255) UNIQUE NOT NULL,
    openrouter_api_key_encrypted TEXT NOT NULL,
    openrouter_account_id       VARCHAR(255),
    free_credits                DECIMAL(12, 6) DEFAULT 0.0,
    last_synced                 TIMESTAMP WITH TIME ZONE,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_openrouter_accounts_user_id ON openrouter_accounts(user_id);


-- ============================================================================
-- 7. coupon_codes   (source: migrations/create_credit_system_tables.sql)
-- ============================================================================
CREATE TABLE IF NOT EXISTS coupon_codes (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code           VARCHAR(50) UNIQUE NOT NULL,
    discount_type  VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    max_uses       INTEGER DEFAULT 1,
    times_used     INTEGER DEFAULT 0,
    valid_from     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at     TIMESTAMP WITH TIME ZONE,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_discount_type     CHECK (discount_type IN ('percentage', 'fixed')),
    CONSTRAINT discount_value_positive CHECK (discount_value > 0)
);

CREATE INDEX IF NOT EXISTS idx_coupon_codes_code ON coupon_codes(code);


-- ============================================================================
-- 8. llm_providers   (source: init_litellm_db.sql)
--    Created BEFORE llm_models and llm_usage_logs (FK targets).
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    enabled         BOOLEAN DEFAULT TRUE,
    priority        INTEGER DEFAULT 50,
    config          JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

CREATE INDEX IF NOT EXISTS idx_providers_enabled  ON llm_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_providers_priority ON llm_providers(priority DESC);


-- ============================================================================
-- 9. llm_models   (source: init_litellm_db.sql; FK -> llm_providers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_models (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id        UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
    name               VARCHAR(255) NOT NULL,
    display_name       VARCHAR(255),
    cost_per_1m_tokens DECIMAL(10, 4) DEFAULT 0,
    context_length     INTEGER DEFAULT 4096,
    enabled            BOOLEAN DEFAULT TRUE,
    metadata           JSONB DEFAULT '{}',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, name)
);

CREATE INDEX IF NOT EXISTS idx_models_provider ON llm_models(provider_id);
CREATE INDEX IF NOT EXISTS idx_models_enabled  ON llm_models(enabled);


-- ============================================================================
-- 10. llm_usage_logs   (source: init_litellm_db.sql; FK -> llm_providers)
--     Handler A: model_catalog_api.get_model_usage_stats
--        SELECT model_name, COUNT(*), SUM(total_tokens), SUM(cost), created_at ...
--     Handler B: testing_lab_api (INSERT + SELECT)
--        INSERT INTO llm_usage_logs (user_id, model_name, input_tokens,
--             output_tokens, total_tokens, cost, latency_ms, success, metadata, created_at)
--        SELECT ... WHERE user_id=$1 AND metadata->>'source'='testing_lab'
--     => source schema has request_tokens/response_tokens and NO metadata.
--        testing_lab_api needs input_tokens, output_tokens AND metadata.
--        Added below as HANDLER-PARITY columns (originals kept for other writers).
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         VARCHAR(255),
    provider_id     UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model_name      VARCHAR(255),
    request_tokens  INTEGER DEFAULT 0,
    response_tokens INTEGER DEFAULT 0,
    -- HANDLER-PARITY: testing_lab_api inserts input_tokens / output_tokens
    -- (names differ from request_tokens/response_tokens used elsewhere).
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    cost            DECIMAL(10, 6) DEFAULT 0,
    latency_ms      INTEGER DEFAULT 0,
    success         BOOLEAN DEFAULT TRUE,
    error_message   TEXT,
    -- HANDLER-PARITY: testing_lab_api stores prompt/response/params/source here
    -- and filters on metadata->>'source'. Not in the original litellm schema.
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_user     ON llm_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON llm_usage_logs(provider_id);
CREATE INDEX IF NOT EXISTS idx_usage_created  ON llm_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_model    ON llm_usage_logs(model_name);


-- ============================================================================
-- 11. model_access_control   (source: sql/model_access_control_schema.sql)
--     NOTE: the source file begins with `DROP TABLE IF EXISTS ... CASCADE` — that
--     DROP is intentionally OMITTED here and converted to CREATE TABLE IF NOT
--     EXISTS (idempotent, never destructive).
--     Handler: model_access_api.list_all_models_admin / get_available_models
--        SELECT id, model_id, provider, display_name, description, tier_access,
--               pricing, tier_markup, context_length, max_output_tokens,
--               supports_vision, supports_function_calling, supports_streaming,
--               model_family, enabled, deprecated, replacement_model, metadata,
--               created_at, updated_at FROM model_access_control WHERE enabled=TRUE
--     Created BEFORE tier_model_access (FK target).
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_access_control (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id     VARCHAR(255) NOT NULL UNIQUE,
    provider     VARCHAR(50) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description  TEXT,
    enabled      BOOLEAN DEFAULT TRUE,
    tier_access  JSONB DEFAULT '["trial","starter","professional","enterprise"]',
    pricing      JSONB,
    tier_markup  JSONB DEFAULT '{"trial": 2.0, "starter": 1.5, "professional": 1.2, "enterprise": 1.0}',
    context_length            INTEGER,
    max_output_tokens         INTEGER,
    supports_vision           BOOLEAN DEFAULT FALSE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_streaming        BOOLEAN DEFAULT TRUE,
    model_family      VARCHAR(100),
    release_date      DATE,
    deprecated        BOOLEAN DEFAULT FALSE,
    replacement_model VARCHAR(255),
    metadata          JSONB DEFAULT '{}',
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_access_enabled    ON model_access_control(enabled);
CREATE INDEX IF NOT EXISTS idx_model_access_provider   ON model_access_control(provider);
CREATE INDEX IF NOT EXISTS idx_model_access_tier       ON model_access_control USING GIN(tier_access);
CREATE INDEX IF NOT EXISTS idx_model_access_family     ON model_access_control(model_family);
CREATE INDEX IF NOT EXISTS idx_model_access_deprecated ON model_access_control(deprecated);

DROP TRIGGER IF EXISTS model_access_updated_at ON model_access_control;
CREATE TRIGGER model_access_updated_at
    BEFORE UPDATE ON model_access_control
    FOR EACH ROW EXECUTE FUNCTION eft_set_updated_at();


-- ============================================================================
-- 12. tier_model_access   (source: migrations/001_create_tier_model_access.sql)
--     FKs: tier_id -> subscription_tiers(id) [exists],
--          model_id -> model_access_control(id) [created above]
--     Handler: model_access_api.get_available_models
--        model_access_control m INNER JOIN tier_model_access tma ON m.id=tma.model_id
--        INNER JOIN subscription_tiers st ... WHERE tma.enabled=TRUE
--     Indexes converted to IF NOT EXISTS (originals were unconditional).
-- ============================================================================
CREATE TABLE IF NOT EXISTS tier_model_access (
    id                SERIAL PRIMARY KEY,
    tier_id           INTEGER NOT NULL REFERENCES subscription_tiers(id) ON DELETE CASCADE,
    model_id          UUID NOT NULL REFERENCES model_access_control(id) ON DELETE CASCADE,
    enabled           BOOLEAN NOT NULL DEFAULT TRUE,
    markup_multiplier NUMERIC(4,2) NOT NULL DEFAULT 1.0,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tier_model_access_unique UNIQUE (tier_id, model_id)
);

CREATE INDEX IF NOT EXISTS idx_tier_model_access_tier    ON tier_model_access(tier_id)  WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_tier_model_access_model   ON tier_model_access(model_id) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_tier_model_access_enabled ON tier_model_access(enabled);

DROP TRIGGER IF EXISTS trg_tier_model_access_update ON tier_model_access;
CREATE TRIGGER trg_tier_model_access_update
    BEFORE UPDATE ON tier_model_access
    FOR EACH ROW EXECUTE FUNCTION eft_set_updated_at();


-- ============================================================================
-- 12b. Seed tier_model_access  (source: migrations/003_populate_tier_model_access.sql)
--      Assign every active, non-deprecated model to vip_founder/byok/managed
--      tiers with the appropriate markup. Made idempotent via ON CONFLICT.
--      Guarded so it is a no-op if subscription_tiers has none of these codes.
-- ============================================================================
INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
SELECT st.id, m.id, 0.0, TRUE
FROM subscription_tiers st
CROSS JOIN model_access_control m
WHERE st.tier_code = 'vip_founder'
  AND m.enabled = TRUE
  AND m.deprecated = FALSE
ON CONFLICT (tier_id, model_id) DO NOTHING;

INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
SELECT st.id, m.id, 0.0, TRUE
FROM subscription_tiers st
CROSS JOIN model_access_control m
WHERE st.tier_code = 'byok'
  AND m.enabled = TRUE
  AND m.deprecated = FALSE
ON CONFLICT (tier_id, model_id) DO NOTHING;

INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
SELECT st.id, m.id, 1.2, TRUE
FROM subscription_tiers st
CROSS JOIN model_access_control m
WHERE st.tier_code = 'managed'
  AND m.enabled = TRUE
  AND m.deprecated = FALSE
ON CONFLICT (tier_id, model_id) DO NOTHING;


-- ============================================================================
-- EXTENSIONS MARKETPLACE
-- (translated from alembic/versions/20251101_create_extensions_marketplace_tables.py)
--   add_ons ALREADY EXISTS -> NOT recreated here.
--   Creating: add_on_categories, add_on_purchases, cart_items, add_on_reviews,
--             user_add_ons.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 13. add_on_categories   (alembic op.create_table('add_on_categories'))
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS add_on_categories (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    slug          VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT,
    icon          VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_addon_categories_slug ON add_on_categories(slug);

-- Seed initial categories (alembic op.execute INSERT). Idempotent on slug.
INSERT INTO add_on_categories (name, slug, description, display_order) VALUES
    ('AI Models',           'ai-models',     'Additional AI models and fine-tunes',            1),
    ('Integrations',        'integrations',  'Third-party service integrations',               2),
    ('Development Tools',   'dev-tools',     'Developer tools and utilities',                  3),
    ('Monitoring',          'monitoring',    'System monitoring and analytics',                4),
    ('Security',            'security',      'Security and compliance tools',                  5),
    ('Workflow Automation', 'automation',    'Workflow automation and orchestration',          6),
    ('Storage & Backup',    'storage',       'Storage solutions and backup tools',             7),
    ('Communication',       'communication', 'Communication and collaboration tools',          8)
ON CONFLICT (slug) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 14. add_on_purchases   (alembic op.create_table('add_on_purchases'); FK -> add_ons)
--     ⚠ HANDLER-PARITY: extensions_purchase_api.get_purchases AND
--       extensions_admin_api.get_analytics query columns that DIFFER from the
--       alembic schema:
--         handlers use:   amount, currency, purchased_at, stripe_payment_id
--         alembic has:    amount_paid, currency, created_at, stripe_payment_intent_id
--     Both sets of columns are included so the live API queries succeed while the
--     alembic-named columns remain for any code written against the migration.
--     FK to add_ons(id): add_ons already exists with an INTEGER PK 'id'.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS add_on_purchases (
    id                       SERIAL PRIMARY KEY,
    user_id                  VARCHAR(255) NOT NULL,
    add_on_id                INTEGER NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    stripe_session_id        VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    -- HANDLER-PARITY: get_purchases selects p.stripe_payment_id
    stripe_payment_id        VARCHAR(255),
    amount_paid              NUMERIC(10, 2) NOT NULL DEFAULT 0,
    -- HANDLER-PARITY: handlers select/sum p.amount (not amount_paid)
    amount                   NUMERIC(10, 2) NOT NULL DEFAULT 0,
    currency                 VARCHAR(3) DEFAULT 'usd',
    status                   VARCHAR(50) DEFAULT 'pending',
    promo_code               VARCHAR(100),
    discount_amount          NUMERIC(10, 2) DEFAULT 0,
    features_granted         JSONB,
    activated_at             TIMESTAMP,
    -- HANDLER-PARITY: handlers order by / filter on p.purchased_at
    purchased_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at               TIMESTAMP,
    refunded_at              TIMESTAMP,
    refund_reason            TEXT,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchases_user           ON add_on_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_addon          ON add_on_purchases(add_on_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status         ON add_on_purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_stripe_session ON add_on_purchases(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_purchases_purchased_at   ON add_on_purchases(purchased_at DESC);

-- ----------------------------------------------------------------------------
-- 15. cart_items   (alembic op.create_table('cart_items'); FK -> add_ons)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cart_items (
    id        SERIAL PRIMARY KEY,
    user_id   VARCHAR(255) NOT NULL,
    add_on_id INTEGER NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    quantity  INTEGER DEFAULT 1,
    added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_addon_cart UNIQUE (user_id, add_on_id)
);

CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_items(user_id);

-- ----------------------------------------------------------------------------
-- 16. add_on_reviews   (alembic op.create_table('add_on_reviews'); FK -> add_ons)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS add_on_reviews (
    id                  SERIAL PRIMARY KEY,
    add_on_id           INTEGER NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    user_id             VARCHAR(255) NOT NULL,
    rating              INTEGER NOT NULL,
    review_text         TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count       INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_addon_review UNIQUE (add_on_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_addon ON add_on_reviews(add_on_id);

-- ----------------------------------------------------------------------------
-- 17. user_add_ons   (inline — derived from extensions_purchase_api.py)
--     INSERT INTO user_add_ons (user_id, add_on_id, status, purchased_at)
--       VALUES (...,'active',NOW())
--       ON CONFLICT (user_id, add_on_id) DO UPDATE SET status='active', updated_at=NOW()
--       RETURNING id
--     SELECT ua.id, ua.purchased_at, ua.expires_at, ua.status, ua.add_on_id ...
--     => needs: id, user_id, add_on_id, status, purchased_at, expires_at,
--        updated_at, and UNIQUE(user_id, add_on_id). FK -> add_ons(id).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_add_ons (
    id           SERIAL PRIMARY KEY,
    user_id      VARCHAR(255) NOT NULL,
    add_on_id    INTEGER NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    status       VARCHAR(50) DEFAULT 'active',
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_addon UNIQUE (user_id, add_on_id)
);

CREATE INDEX IF NOT EXISTS idx_user_add_ons_user   ON user_add_ons(user_id);
CREATE INDEX IF NOT EXISTS idx_user_add_ons_status ON user_add_ons(status);


-- ============================================================================
-- 18. promotional_codes   (inline — derived from extensions_admin_api.create_promo_code)
--     INSERT INTO promotional_codes (code, discount_type, discount_value,
--          max_uses, current_uses, expires_at, is_active, created_at)
--       VALUES ($1,$2,$3,$4,0,$5,TRUE,NOW())
--       RETURNING id, code, discount_type, discount_value, max_uses,
--                 current_uses, expires_at, is_active, created_at
--     NOTE: column is 'current_uses' here (distinct from coupon_codes.times_used).
--     discount_type accepts 'percentage' | 'fixed_amount' (per Pydantic validator).
-- ============================================================================
CREATE TABLE IF NOT EXISTS promotional_codes (
    id             SERIAL PRIMARY KEY,
    code           VARCHAR(50) NOT NULL UNIQUE,
    discount_type  VARCHAR(20) NOT NULL,
    discount_value NUMERIC(10, 2) NOT NULL,
    max_uses       INTEGER,
    current_uses   INTEGER DEFAULT 0,
    expires_at     TIMESTAMP WITH TIME ZONE,
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_promotional_codes_code   ON promotional_codes(code);
CREATE INDEX IF NOT EXISTS idx_promotional_codes_active ON promotional_codes(is_active);


-- ============================================================================
-- 19. org_billing_summary  (VIEW — canonical definition from migrations/create_org_billing.sql)
--     Handler: org_billing_api.get_system_admin_billing_screen
--        SELECT * FROM org_billing_summary ORDER BY lifetime_spent_amount DESC
--        reads: org_id, org_name, subscription_plan, monthly_price,
--               subscription_status, total_credits, used_credits, member_count,
--               lifetime_spent_amount
--     All join tables exist (organizations, organization_subscriptions,
--     organization_credit_pools, organization_members) EXCEPT
--     user_credit_allocations, which create_org_billing.sql also creates. To keep
--     THIS file self-sufficient and avoid referencing a possibly-absent table,
--     a minimal user_credit_allocations is ensured first (matches create_org_billing.sql).
-- ============================================================================

-- Ensure the one join dependency that is not in the "already-exists" set.
CREATE TABLE IF NOT EXISTS user_credit_allocations (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id            UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id           VARCHAR(255) NOT NULL,
    allocated_credits BIGINT NOT NULL DEFAULT 0,
    used_credits      BIGINT NOT NULL DEFAULT 0,
    remaining_credits BIGINT GENERATED ALWAYS AS (allocated_credits - used_credits) STORED,
    reset_period      VARCHAR(20) DEFAULT 'monthly',
    last_reset_date   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_reset_date   TIMESTAMP WITH TIME ZONE,
    is_active         BOOLEAN DEFAULT TRUE,
    allocated_by      VARCHAR(255),
    notes             TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_credit_alloc_org    ON user_credit_allocations(org_id);
CREATE INDEX IF NOT EXISTS idx_user_credit_alloc_user   ON user_credit_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credit_alloc_active ON user_credit_allocations(is_active);

CREATE OR REPLACE VIEW org_billing_summary AS
SELECT
    o.id                       AS org_id,
    o.name                     AS org_name,
    os.subscription_plan       AS subscription_plan,
    os.monthly_price           AS monthly_price,
    os.status                  AS subscription_status,
    ocp.total_credits          AS total_credits,
    ocp.allocated_credits      AS allocated_credits,
    ocp.used_credits           AS used_credits,
    ocp.available_credits      AS available_credits,
    ocp.lifetime_spent_amount  AS lifetime_spent_amount,
    COUNT(DISTINCT om.user_id) AS member_count,
    COUNT(DISTINCT uca.id)     AS allocated_users_count
FROM organizations o
LEFT JOIN organization_subscriptions os
       ON o.id = os.org_id AND os.status = 'active'
LEFT JOIN organization_credit_pools ocp
       ON o.id = ocp.org_id
LEFT JOIN organization_members om
       ON o.id = om.org_id
LEFT JOIN user_credit_allocations uca
       ON o.id = uca.org_id AND uca.is_active = TRUE
WHERE o.status = 'active'
GROUP BY o.id, o.name, os.subscription_plan, os.monthly_price, os.status,
         ocp.total_credits, ocp.allocated_credits, ocp.used_credits,
         ocp.available_credits, ocp.lifetime_spent_amount;


-- ============================================================================
-- GRANTS  (owner is 'unicorn'; harmless if already owner. Wrapped so a missing
--          role never aborts the run.)
-- ============================================================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'unicorn') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON
            platform_settings, landing_page_settings, credit_transactions,
            credit_packages, credit_purchases, openrouter_accounts, coupon_codes,
            llm_providers, llm_models, llm_usage_logs, model_access_control,
            tier_model_access, add_on_categories, add_on_purchases, cart_items,
            add_on_reviews, user_add_ons, promotional_codes, user_credit_allocations
            TO unicorn';
        EXECUTE 'GRANT SELECT ON org_billing_summary TO unicorn';
    END IF;
END $$;


-- ============================================================================
-- COLUMN BACKFILL — for tables that may PRE-EXIST in an older/incomplete form.
-- CREATE TABLE IF NOT EXISTS above is a no-op when a table already exists, so it
-- cannot add columns a newer handler needs. These idempotent ALTERs close that gap
-- (verified missing on magicunicorn.dev 2026-06-09):
--   llm_usage_logs lacked metadata + total_tokens (testing-lab + model-stats handlers)
--   add_ons lacked version (extensions get_active_addons: SELECT a.version)
-- ============================================================================
ALTER TABLE llm_usage_logs ADD COLUMN IF NOT EXISTS metadata JSONB;
ALTER TABLE llm_usage_logs ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS version VARCHAR(50);

-- Durable profile-picture URL (2026-06-09). The PUT /api/v1/auth/profile upload
-- saved the avatar file to /app/public/avatars and wrote the URL ONLY into the
-- Redis session, so it was lost on session expiry / re-login. Persist it here so
-- get_session_info + the OAuth callback can rehydrate user.avatar durably.
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Per-org gateway key (metered-inference billing keystone, 2026-06-09).
-- Each org gets ONE LiteLLM virtual key (user_id == org_id) carrying its budget
-- + model allow-list + metering identity. We store the LiteLLM token id and the
-- Fernet-encrypted key value so provisioning is idempotent (see
-- gateway_key_provisioning.provision_org_gateway_key).
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS litellm_gateway_key_id VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS litellm_gateway_key_encrypted TEXT;
CREATE INDEX IF NOT EXISTS idx_organizations_gateway_key_id ON organizations(litellm_gateway_key_id);


-- ============================================================================
-- app_model_policy — per-(app, model) included-vs-metered inference policy.
-- Empty by default → everything resolves "metered" (no behavior change).
-- app   = calling UC app (service-key service_name) or feature_key
-- model = exact model id, a prefix ending in '*' (e.g. 'Qwen3.6-*'), or '*'
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_model_policy (
    id SERIAL PRIMARY KEY,
    app VARCHAR(128) NOT NULL,
    model VARCHAR(255) NOT NULL,
    policy VARCHAR(16) NOT NULL DEFAULT 'metered' CHECK (policy IN ('included','metered')),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (app, model)
);

-- ============================================================================
-- DONE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'ensure_feature_tables.sql applied: feature tables + org_billing_summary view ensured.';
END $$;
