-- core parity 0004 — add_ons catalog column union (Phase B)
-- extensions_manager reads add_ons.rating_avg / rating_count / is_public
-- unconditionally (SELECT list) — absent on commander -> latent 500. commander
-- carries a richer marketplace catalog (currency/author/screenshots/etc.) that
-- bigboy lacks. Union both column sets on both nodes; benign type nuances
-- (icon_url text/varchar) are left as-is per the drift audit (same class).
-- bigboy-side (code-required reads):
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT true;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS rating_avg NUMERIC DEFAULT 0.00;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS access_type VARCHAR(32) DEFAULT 'purchase';
-- commander-side (marketplace catalog):
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS currency VARCHAR(8);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS stripe_product_id VARCHAR(255);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS stripe_price_id VARCHAR(255);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS author VARCHAR(255);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS screenshot_urls JSONB;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS requirements JSONB;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS compatibility JSONB;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS download_url VARCHAR(512);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS documentation_url VARCHAR(512);
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS rating NUMERIC DEFAULT 0.00;
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
