# Extensions Marketplace Database Schema

**Version**: 1.0.0 (Phase 1 - MVP)
**Database**: PostgreSQL (unicorn_db)
**Created**: 2025-11-01
**Status**: ✅ Ready for Deployment

---

## 📦 What's Included

This directory contains the complete database schema for the Extensions Marketplace, including:

- **8 Core Tables** for product catalog, purchases, subscriptions, and pricing
- **30+ Performance Indexes** optimized for high-traffic queries
- **9 Pre-configured Add-ons** ready to sell
- **4 Sample Bundles** with discounts
- **4 Promotional Codes** for marketing campaigns
- **Comprehensive Test Suite** to validate everything

---

## 🚀 Quick Start

### Option 1: Full Migration (Recommended)

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
psql -U postgres -d unicorn_db -f backend/sql/extensions_migration.sql
psql -U postgres -d unicorn_db -f backend/sql/extensions_seed_data.sql
psql -U postgres -d unicorn_db -f backend/tests/test_extensions_schema.sql
```

### Option 2: Step by Step

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# 1. Create tables and triggers
psql -U postgres -d unicorn_db -f backend/sql/extensions_schema.sql

# 2. Add performance indexes
psql -U postgres -d unicorn_db -f backend/sql/extensions_indexes.sql

# 3. Load seed data
psql -U postgres -d unicorn_db -f backend/sql/extensions_seed_data.sql

# 4. Validate deployment
psql -U postgres -d unicorn_db -f backend/tests/test_extensions_schema.sql
```

### Option 3: Quick Validation

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
./backend/sql/validate_schema.sh
```

---

## 📁 File Structure

```
backend/sql/
├── README.md                      ← You are here
├── DEPLOYMENT_GUIDE.md            ← Detailed deployment instructions
├── SCHEMA_DIAGRAM.md              ← Visual ERD and relationships
├── extensions_schema.sql          ← Core table definitions (8 tables)
├── extensions_indexes.sql         ← Performance indexes (30+)
├── extensions_seed_data.sql       ← Pre-configured add-ons (9 products)
├── extensions_migration.sql       ← Alembic-style migration script
└── validate_schema.sh             ← Quick validation script

backend/tests/
└── test_extensions_schema.sql     ← Comprehensive test suite (9 tests)
```

---

## 📊 Database Tables

### Core Tables (8)

| Table | Purpose | Records (Seed) |
|-------|---------|----------------|
| **add_ons** | Product catalog | 9 add-ons |
| **user_add_ons** | User subscriptions | Empty (populated by purchases) |
| **add_on_purchases** | Transaction history | Empty (populated by Stripe) |
| **add_on_bundles** | Product bundles | 3 bundles |
| **pricing_rules** | Dynamic pricing | Empty (add as needed) |
| **cart_items** | Shopping cart | Empty (user session data) |
| **add_on_features** | Feature mappings | 40+ features |
| **promotional_codes** | Discount codes | 4 promo codes |

---

## 🎯 Pre-configured Products

| Add-on | Price/Month | Category | Description |
|--------|-------------|----------|-------------|
| Unicorn Orator (TTS) | $9.99 | AI Services | Text-to-speech, 30 languages |
| Amanuensis (STT) | $9.99 | AI Services | Speech-to-text, 95% accuracy |
| Brigade | $19.99 | AI Services | AI agent platform, 10 agents |
| Bolt | $14.99 | Development | AI dev environment, GPU hours |
| Presenton | $9.99 | Productivity | Presentation builder, 100 templates |
| Center-Deep Pro | $19.99 | Analytics | Semantic search, vector DB |
| Document Processing | $12.99 | Productivity | OCR, 5K pages/month |
| Vector Search | $14.99 | Infrastructure | 1M vectors, <10ms queries |
| GPU Compute | $49.99 | Infrastructure | A100/H100, 50 GPU hours |

---

## 🎫 Sample Promotional Codes

| Code | Discount | Max Uses | Valid For |
|------|----------|----------|-----------|
| LAUNCH2025 | 20% off | 100 | 30 days |
| FIRSTBUY | 15% off | Unlimited | 90 days |
| FRIEND50 | $5 off | 1000 | 60 days |
| VIP2025 | 30% off | 50 | 365 days (VIP only) |

---

## 🔍 Key Features

### Performance Optimizations
- ⚡ **GIN Indexes** on JSONB columns for feature queries
- ⚡ **Composite Indexes** for common JOIN patterns
- ⚡ **Partial Indexes** for active records only
- ⚡ **B-tree Indexes** on all foreign keys

### Data Integrity
- 🔒 **Foreign Key Constraints** with CASCADE/RESTRICT
- 🔒 **Check Constraints** for valid enums and ranges
- 🔒 **Unique Constraints** for business rules
- 🔒 **Automatic Triggers** for timestamp updates

### Extensibility
- 🔧 **JSONB Columns** for flexible metadata
- 🔧 **Array Columns** for multi-value relationships
- 🔧 **Conditional Pricing** via JSONB rules
- 🔧 **Feature Flags** for granular access control

---

## 🔗 Integration Points

### External Systems
- **Keycloak** - User authentication (user_id)
- **Stripe** - Payment processing (stripe_payment_id)
- **Lago** - Subscription billing (lago_subscription_id, lago_invoice_id)

### Existing Tables
- **subscription_tiers** - Referenced by pricing_rules (tier_code)
- **feature_definitions** - Referenced by add_on_features (feature_key)

---

## ✅ Validation Checklist

After deployment, verify:

```bash
# Quick validation
./backend/sql/validate_schema.sh

# Full test suite
psql -U postgres -d unicorn_db -f backend/tests/test_extensions_schema.sql

# Manual checks
psql -U postgres -d unicorn_db

# Check table count (should be 8)
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name IN ('add_ons', 'user_add_ons', 'add_on_purchases', 'add_on_bundles',
                     'pricing_rules', 'cart_items', 'add_on_features', 'promotional_codes');

# Check seed data
SELECT COUNT(*) FROM add_ons;  -- Should be 9
SELECT COUNT(*) FROM add_on_features;  -- Should be 40+
SELECT COUNT(*) FROM promotional_codes;  -- Should be 4
```

---

## 🔄 Rollback

If you need to rollback the deployment:

```sql
BEGIN;

-- Drop all tables
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

## 📈 Performance Expectations

| Query Type | Expected Performance |
|------------|---------------------|
| User's active add-ons | <5ms |
| Cart retrieval | <3ms |
| Purchase history | <10ms |
| JSONB feature search | <15ms |
| Bundle lookup | <8ms |

---

## 🛠️ Maintenance

### Daily
```sql
-- Clean up abandoned carts (older than 30 days)
DELETE FROM cart_items WHERE added_at < NOW() - INTERVAL '30 days';
```

### Weekly
```sql
-- Update expired subscriptions
UPDATE user_add_ons SET status = 'expired'
WHERE status = 'active' AND expires_at < NOW();

-- Deactivate expired promo codes
UPDATE promotional_codes SET is_active = FALSE
WHERE is_active = TRUE AND expires_at < NOW();
```

### Monthly
```sql
-- Optimize tables
ANALYZE add_ons;
ANALYZE user_add_ons;
ANALYZE add_on_purchases;
VACUUM ANALYZE;
```

---

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment instructions
- **SCHEMA_DIAGRAM.md** - Visual ERD and relationship diagrams
- **test_extensions_schema.sql** - Automated test suite with 9 test categories

---

## 🚀 Next Steps

After successful deployment:

1. ✅ Update ORM models (SQLAlchemy/Django)
2. ✅ Create REST API endpoints
3. ✅ Build frontend marketplace UI
4. ✅ Integrate Stripe checkout
5. ✅ Connect Lago billing
6. ✅ Implement feature flag middleware
7. ✅ Create admin dashboard
8. ✅ Set up analytics tracking

---

## 📞 Support

For issues or questions:

1. Review the test suite output: `test_extensions_schema.sql`
2. Check the deployment guide: `DEPLOYMENT_GUIDE.md`
3. View the schema diagram: `SCHEMA_DIAGRAM.md`
4. Run validation script: `./validate_schema.sh`

---

## 📄 License

Part of Ops-Center (UC-Cloud) Extensions Marketplace
© 2025 Unicorn Commander

---

**Status**: ✅ Ready for Production Deployment

Last Updated: 2025-11-01
