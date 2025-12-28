# Extensions Marketplace Database Deployment Guide

**Database**: PostgreSQL (unicorn_db)
**Phase**: 1 - MVP
**Created**: 2025-11-01
**Tables**: 8 core tables + indexes + seed data

---

## 📋 Quick Overview

This deployment creates the complete database schema for the Extensions Marketplace, including:

- **8 Core Tables**: Product catalog, purchases, cart, bundles, pricing, features, promos
- **20+ Indexes**: Optimized for high-performance queries
- **9 Pre-configured Add-ons**: Ready-to-use products
- **4 Sample Bundles**: Pre-built product bundles
- **4 Promotional Codes**: Launch marketing campaigns

---

## 🚀 Deployment Steps

### Option 1: Full Migration (Recommended for Production)

```bash
# 1. Connect to database
psql -U postgres -d unicorn_db

# 2. Run migration (creates tables + indexes + triggers)
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/sql/extensions_migration.sql

# 3. Load seed data (9 add-ons + features + promos)
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/sql/extensions_seed_data.sql

# 4. Run test suite (validates everything)
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/tests/test_extensions_schema.sql
```

### Option 2: Step-by-Step (Recommended for Development)

```bash
# 1. Connect to database
psql -U postgres -d unicorn_db

# 2. Create tables and triggers
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/sql/extensions_schema.sql

# 3. Create performance indexes
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/sql/extensions_indexes.sql

# 4. Load seed data
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/sql/extensions_seed_data.sql

# 5. Run tests
\i /home/muut/Production/UC-Cloud/services/ops-center/backend/tests/test_extensions_schema.sql
```

---

## 📊 Database Schema

### 8 Core Tables

#### 1. **add_ons** (Product Catalog)
```sql
- id: UUID PRIMARY KEY
- name: VARCHAR(255) - Product name
- description: TEXT - Detailed description
- category: VARCHAR(100) - 'ai-services', 'infrastructure', 'analytics', 'development', 'productivity'
- base_price: DECIMAL(10,2) - Base price in USD
- billing_type: VARCHAR(50) - 'one_time', 'monthly', 'annual', 'usage_based'
- features: JSONB - Array of feature keys
- is_active: BOOLEAN - Product availability
- metadata: JSONB - Additional flexible data
```

#### 2. **user_add_ons** (User Subscriptions)
```sql
- id: UUID PRIMARY KEY
- user_id: VARCHAR(255) - Keycloak user ID
- add_on_id: UUID -> add_ons(id)
- status: VARCHAR(50) - 'active', 'cancelled', 'expired', 'pending', 'suspended'
- purchased_at: TIMESTAMP
- expires_at: TIMESTAMP - NULL for lifetime purchases
- lago_subscription_id: VARCHAR(255) - Lago integration
- auto_renew: BOOLEAN
```

#### 3. **add_on_purchases** (Transaction History)
```sql
- id: UUID PRIMARY KEY
- user_id: VARCHAR(255)
- add_on_id: UUID -> add_ons(id)
- amount: DECIMAL(10,2)
- currency: VARCHAR(3) - Default 'USD'
- stripe_payment_id: VARCHAR(255)
- lago_invoice_id: VARCHAR(255)
- status: VARCHAR(50) - 'pending', 'completed', 'failed', 'refunded'
- purchased_at: TIMESTAMP
```

#### 4. **add_on_bundles** (Product Bundles)
```sql
- id: UUID PRIMARY KEY
- name: VARCHAR(255)
- description: TEXT
- add_on_ids: UUID[] - Array of bundled add-on IDs
- discount_percent: DECIMAL(5,2)
- discount_amount: DECIMAL(10,2)
- is_active: BOOLEAN
- valid_from/valid_until: TIMESTAMP
```

#### 5. **pricing_rules** (Dynamic Pricing)
```sql
- id: UUID PRIMARY KEY
- add_on_id: UUID -> add_ons(id)
- tier_code: VARCHAR(50) - References subscription_tiers
- discount_percent: DECIMAL(5,2)
- conditions: JSONB - Complex pricing rules
- priority: INTEGER - Rule application order
```

#### 6. **cart_items** (Shopping Cart)
```sql
- id: UUID PRIMARY KEY
- user_id: VARCHAR(255)
- add_on_id: UUID -> add_ons(id)
- quantity: INTEGER
- added_at: TIMESTAMP
```

#### 7. **add_on_features** (Feature Mappings)
```sql
- id: UUID PRIMARY KEY
- add_on_id: UUID -> add_ons(id)
- feature_key: VARCHAR(100) - References feature_definitions
- enabled: BOOLEAN
- configuration: JSONB - Feature-specific config
```

#### 8. **promotional_codes** (Discount Codes)
```sql
- id: UUID PRIMARY KEY
- code: VARCHAR(50) UNIQUE
- discount_type: 'percentage' | 'fixed_amount'
- discount_value: DECIMAL(10,2)
- max_uses: INTEGER
- current_uses: INTEGER
- applicable_to: UUID[] - Specific add-ons or NULL for all
- expires_at: TIMESTAMP
```

---

## 🔍 Key Features

### Performance Optimizations
- **GIN Indexes** on JSONB columns for feature queries
- **Composite Indexes** for common JOIN operations
- **Partial Indexes** for active/valid records only
- **B-tree Indexes** on foreign keys and lookup columns

### Data Integrity
- **Foreign Key Constraints** with CASCADE/RESTRICT
- **Check Constraints** for valid enums and ranges
- **Unique Constraints** for business logic (user+addon, promo codes)
- **Triggers** for automatic timestamp updates

### Extensibility
- **JSONB Columns** for flexible metadata
- **Array Columns** for multi-value relationships
- **Conditional Pricing** via JSONB rules
- **Feature Flags** for granular control

---

## 📦 Pre-configured Add-ons (Seed Data)

| Add-on | Price | Category | Key Features |
|--------|-------|----------|-------------|
| **Unicorn Orator - TTS** | $9.99/mo | AI Services | Neural voices, 30 languages, SSML |
| **Amanuensis - STT** | $9.99/mo | AI Services | 95% accuracy, diarization, real-time |
| **Brigade - Agent Platform** | $19.99/mo | AI Services | 10 agents, orchestration, monitoring |
| **Bolt - AI Dev Environment** | $14.99/mo | Development | Code gen, GPU hours, Docker, CI/CD |
| **Presenton - Presentations** | $9.99/mo | Productivity | AI slides, 100 templates, exports |
| **Center-Deep Pro** | $19.99/mo | Analytics | Semantic search, vector embeddings |
| **Document Processing Suite** | $12.99/mo | Productivity | OCR, 5K pages/mo, 50 languages |
| **Vector Search Engine** | $14.99/mo | Infrastructure | 1M vectors, <10ms queries |
| **GPU Compute Access** | $49.99/mo | Infrastructure | A100/H100, 50 GPU hours |

---

## 🎯 Sample Bundles

1. **AI Productivity Bundle** ($25.47/mo - save 15%)
   - TTS + STT + Presenton
   - Original: $29.97

2. **Developer Pro Bundle** ($39.98/mo - save 20%)
   - Brigade + Bolt + Vector Search
   - Original: $49.97

3. **Enterprise Suite** (25% off all services)
   - All 9 add-ons included

---

## 🎫 Promotional Codes

| Code | Type | Value | Max Uses | Expires |
|------|------|-------|----------|---------|
| LAUNCH2025 | Percentage | 20% | 100 | 30 days |
| FIRSTBUY | Percentage | 15% | Unlimited | 90 days |
| FRIEND50 | Fixed | $5 | 1000 | 60 days |
| VIP2025 | Percentage | 30% | 50 | 365 days |

---

## ✅ Verification Checklist

After deployment, verify:

```bash
# Run comprehensive test suite
psql -U postgres -d unicorn_db -f backend/tests/test_extensions_schema.sql

# Manual verification
psql -U postgres -d unicorn_db

# Check table count
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name IN ('add_ons', 'user_add_ons', 'add_on_purchases', 'add_on_bundles',
                     'pricing_rules', 'cart_items', 'add_on_features', 'promotional_codes');
-- Expected: 8

# Check seed data
SELECT COUNT(*) FROM add_ons;  -- Expected: 9
SELECT COUNT(*) FROM add_on_features;  -- Expected: 40+
SELECT COUNT(*) FROM promotional_codes;  -- Expected: 4
SELECT COUNT(*) FROM add_on_bundles;  -- Expected: 3

# Check indexes
SELECT COUNT(*) FROM pg_indexes WHERE tablename LIKE 'add_%' OR tablename LIKE '%_add_%';
-- Expected: 30+

# Check foreign keys
SELECT COUNT(*) FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND table_name IN ('user_add_ons', 'add_on_purchases', 'pricing_rules',
                   'cart_items', 'add_on_features');
-- Expected: 5+
```

---

## 🔄 Rollback Procedure

If deployment fails or needs to be reverted:

```sql
BEGIN;

-- Drop all tables (cascades to indexes and triggers)
DROP TABLE IF EXISTS promotional_codes CASCADE;
DROP TABLE IF EXISTS add_on_features CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS pricing_rules CASCADE;
DROP TABLE IF EXISTS add_on_bundles CASCADE;
DROP TABLE IF EXISTS add_on_purchases CASCADE;
DROP TABLE IF EXISTS user_add_ons CASCADE;
DROP TABLE IF EXISTS add_ons CASCADE;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Remove migration record
DELETE FROM alembic_version WHERE version_num = '001_extensions_marketplace';

COMMIT;
```

---

## 🔗 Integration Points

### Existing Tables Referenced
- **subscription_tiers** (via `tier_code` in pricing_rules)
- **feature_definitions** (via `feature_key` in add_on_features)
- **Keycloak users** (via `user_id` VARCHAR(255))

### External Systems
- **Stripe** - Payment processing (via `stripe_payment_id`)
- **Lago** - Subscription billing (via `lago_subscription_id`, `lago_invoice_id`)
- **Keycloak** - User authentication (via `user_id`)

---

## 📈 Performance Expectations

| Query Type | Expected Performance |
|------------|---------------------|
| User's active add-ons | <5ms (indexed) |
| Cart retrieval | <3ms (indexed) |
| Purchase history | <10ms (composite index) |
| JSONB feature search | <15ms (GIN index) |
| Bundle lookup | <8ms (GIN array index) |

---

## 🛠️ Maintenance Tasks

### Daily
```sql
-- Clean up abandoned carts (older than 30 days)
DELETE FROM cart_items WHERE added_at < NOW() - INTERVAL '30 days';
```

### Weekly
```sql
-- Update expired subscriptions
UPDATE user_add_ons
SET status = 'expired'
WHERE status = 'active'
  AND expires_at < NOW();

-- Deactivate expired promotional codes
UPDATE promotional_codes
SET is_active = FALSE
WHERE is_active = TRUE
  AND expires_at < NOW();
```

### Monthly
```sql
-- Analyze tables for query optimization
ANALYZE add_ons;
ANALYZE user_add_ons;
ANALYZE add_on_purchases;

-- Vacuum to reclaim space
VACUUM ANALYZE add_ons;
VACUUM ANALYZE user_add_ons;
VACUUM ANALYZE add_on_purchases;
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue**: Migration fails with "relation already exists"
**Solution**: Tables already exist. Either drop them manually or use `IF NOT EXISTS` clause.

**Issue**: Foreign key violation on seed data
**Solution**: Ensure add_ons are inserted before add_on_features.

**Issue**: Slow JSONB queries
**Solution**: Verify GIN indexes exist: `\di idx_add_ons_features`

**Issue**: Test suite fails
**Solution**: Run each test section individually to identify the failing component.

---

## 🚀 Next Steps (Post-Deployment)

1. **Update ORM Models** - Sync SQLAlchemy/Django models with schema
2. **API Endpoints** - Create REST API for marketplace operations
3. **Frontend Integration** - Connect React components to API
4. **Payment Flow** - Integrate Stripe checkout
5. **Billing System** - Connect Lago for recurring billing
6. **Feature Flags** - Implement feature checking middleware
7. **Admin Dashboard** - Create management interface
8. **Analytics** - Set up revenue and usage tracking

---

## 📝 Notes

- All monetary values use DECIMAL(10,2) for precision
- UUIDs are generated via `gen_random_uuid()` (requires pgcrypto)
- Timestamps use `NOW()` for consistency across timezones
- JSONB is used for flexible metadata storage
- Array columns (UUID[]) are used for many-to-many relationships

---

## 📄 File Manifest

```
backend/sql/
├── extensions_schema.sql        # Core table definitions + triggers
├── extensions_indexes.sql       # Performance indexes
├── extensions_seed_data.sql     # 9 add-ons + features + promos
├── extensions_migration.sql     # Alembic-style migration
└── DEPLOYMENT_GUIDE.md         # This file

backend/tests/
└── test_extensions_schema.sql  # Comprehensive test suite
```

---

**Deployment Complete! 🎉**

For issues or questions, refer to the test suite output or consult the project documentation.
