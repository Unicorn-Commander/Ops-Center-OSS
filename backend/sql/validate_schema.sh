#!/bin/bash
# Schema Validation Script
# Quickly validates the Extensions Marketplace schema deployment

set -e

DB_NAME="${DB_NAME:-unicorn_db}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "================================================"
echo "  Extensions Marketplace Schema Validator"
echo "================================================"
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check PostgreSQL connection
echo "🔍 Testing database connection..."
if ! psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Failed to connect to database"
    exit 1
fi
echo "✅ Database connection successful"
echo ""

# Check table count
echo "🔍 Checking table existence..."
TABLE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('add_ons', 'user_add_ons', 'add_on_purchases', 'add_on_bundles', 
                       'pricing_rules', 'cart_items', 'add_on_features', 'promotional_codes');
")

if [ "$TABLE_COUNT" -eq 8 ]; then
    echo "✅ All 8 tables exist"
else
    echo "❌ Expected 8 tables, found $TABLE_COUNT"
    exit 1
fi
echo ""

# Check seed data
echo "🔍 Checking seed data..."
ADDON_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT COUNT(*) FROM add_ons;")
FEATURE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT COUNT(*) FROM add_on_features;")
PROMO_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT COUNT(*) FROM promotional_codes;")

echo "  - Add-ons: $ADDON_COUNT (expected: 9)"
echo "  - Features: $FEATURE_COUNT (expected: 40+)"
echo "  - Promos: $PROMO_COUNT (expected: 4+)"

if [ "$ADDON_COUNT" -ge 9 ] && [ "$FEATURE_COUNT" -ge 40 ] && [ "$PROMO_COUNT" -ge 4 ]; then
    echo "✅ Seed data loaded"
else
    echo "⚠️  Seed data incomplete (run extensions_seed_data.sql)"
fi
echo ""

# Check indexes
echo "🔍 Checking indexes..."
INDEX_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "
    SELECT COUNT(*) FROM pg_indexes 
    WHERE tablename LIKE 'add_%' OR tablename LIKE '%_add_%';
")

if [ "$INDEX_COUNT" -ge 25 ]; then
    echo "✅ Found $INDEX_COUNT indexes"
else
    echo "⚠️  Only $INDEX_COUNT indexes found (expected 30+)"
fi
echo ""

# Check foreign keys
echo "🔍 Checking foreign key constraints..."
FK_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "
    SELECT COUNT(*) FROM information_schema.table_constraints 
    WHERE constraint_type = 'FOREIGN KEY' 
    AND table_name IN ('user_add_ons', 'add_on_purchases', 'pricing_rules', 
                       'cart_items', 'add_on_features');
")

if [ "$FK_COUNT" -ge 5 ]; then
    echo "✅ Found $FK_COUNT foreign key constraints"
else
    echo "❌ Only $FK_COUNT foreign keys found (expected 5+)"
    exit 1
fi
echo ""

# Check triggers
echo "🔍 Checking triggers..."
TRIGGER_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -tAc "
    SELECT COUNT(*) FROM information_schema.triggers 
    WHERE trigger_name LIKE '%updated_at%';
")

if [ "$TRIGGER_COUNT" -ge 7 ]; then
    echo "✅ Found $TRIGGER_COUNT triggers"
else
    echo "⚠️  Only $TRIGGER_COUNT triggers found (expected 7)"
fi
echo ""

# Summary
echo "================================================"
echo "  ✅ SCHEMA VALIDATION COMPLETE"
echo "================================================"
echo ""
echo "Summary:"
echo "  - Tables: $TABLE_COUNT/8"
echo "  - Indexes: $INDEX_COUNT"
echo "  - Foreign Keys: $FK_COUNT"
echo "  - Triggers: $TRIGGER_COUNT"
echo "  - Seed Data: $ADDON_COUNT add-ons, $FEATURE_COUNT features"
echo ""
echo "Next steps:"
echo "  1. Run full test suite: psql -U $DB_USER -d $DB_NAME -f backend/tests/test_extensions_schema.sql"
echo "  2. Update application ORM models"
echo "  3. Create API endpoints"
echo "  4. Integrate with frontend"
echo ""
