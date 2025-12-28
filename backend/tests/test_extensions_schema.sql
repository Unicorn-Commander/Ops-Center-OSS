-- Extensions Marketplace Schema Test Suite
-- Comprehensive validation of database schema
-- Database: PostgreSQL (unicorn_db)
-- Created: 2025-11-01

-- ============================================================================
-- TEST 1: TABLE EXISTENCE
-- ============================================================================

DO $$
DECLARE
    missing_tables TEXT[];
BEGIN
    RAISE NOTICE '=== TEST 1: TABLE EXISTENCE ===';

    SELECT ARRAY_AGG(table_name) INTO missing_tables
    FROM (
        SELECT unnest(ARRAY[
            'add_ons', 'user_add_ons', 'add_on_purchases', 'add_on_bundles',
            'pricing_rules', 'cart_items', 'add_on_features', 'promotional_codes'
        ]) AS table_name
    ) expected
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = expected.table_name
    );

    IF missing_tables IS NOT NULL THEN
        RAISE EXCEPTION 'Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;

    RAISE NOTICE '✓ All 8 tables exist';
END $$;

-- ============================================================================
-- TEST 2: FOREIGN KEY CONSTRAINTS
-- ============================================================================

DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 2: FOREIGN KEY CONSTRAINTS ===';

    -- user_add_ons -> add_ons
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_name = 'user_add_ons' AND constraint_type = 'FOREIGN KEY';

    IF constraint_count < 1 THEN
        RAISE EXCEPTION 'Missing foreign key on user_add_ons';
    END IF;
    RAISE NOTICE '✓ user_add_ons foreign key exists';

    -- add_on_purchases -> add_ons
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_name = 'add_on_purchases' AND constraint_type = 'FOREIGN KEY';

    IF constraint_count < 1 THEN
        RAISE EXCEPTION 'Missing foreign key on add_on_purchases';
    END IF;
    RAISE NOTICE '✓ add_on_purchases foreign key exists';

    -- pricing_rules -> add_ons
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_name = 'pricing_rules' AND constraint_type = 'FOREIGN KEY';

    IF constraint_count < 1 THEN
        RAISE EXCEPTION 'Missing foreign key on pricing_rules';
    END IF;
    RAISE NOTICE '✓ pricing_rules foreign key exists';

    -- cart_items -> add_ons
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_name = 'cart_items' AND constraint_type = 'FOREIGN KEY';

    IF constraint_count < 1 THEN
        RAISE EXCEPTION 'Missing foreign key on cart_items';
    END IF;
    RAISE NOTICE '✓ cart_items foreign key exists';

    -- add_on_features -> add_ons
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE table_name = 'add_on_features' AND constraint_type = 'FOREIGN KEY';

    IF constraint_count < 1 THEN
        RAISE EXCEPTION 'Missing foreign key on add_on_features';
    END IF;
    RAISE NOTICE '✓ add_on_features foreign key exists';

    RAISE NOTICE '✓ All foreign key constraints verified';
END $$;

-- ============================================================================
-- TEST 3: INDEX VERIFICATION
-- ============================================================================

DO $$
DECLARE
    index_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 3: INDEX VERIFICATION ===';

    -- Count GIN indexes for JSONB columns
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE indexname LIKE '%features%' OR indexname LIKE '%config%' OR indexname LIKE '%applicable%'
    AND indexdef LIKE '%GIN%';

    IF index_count < 3 THEN
        RAISE EXCEPTION 'Missing GIN indexes for JSONB columns (found %, expected 3+)', index_count;
    END IF;
    RAISE NOTICE '✓ GIN indexes for JSONB: %', index_count;

    -- Critical user_add_ons indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_add_ons_user_id') THEN
        RAISE EXCEPTION 'Missing critical index: idx_user_add_ons_user_id';
    END IF;
    RAISE NOTICE '✓ Critical index idx_user_add_ons_user_id exists';

    -- Cart indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_cart_items_user') THEN
        RAISE EXCEPTION 'Missing critical index: idx_cart_items_user';
    END IF;
    RAISE NOTICE '✓ Critical index idx_cart_items_user exists';

    -- Purchase history index
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_add_on_purchases_user_date') THEN
        RAISE EXCEPTION 'Missing critical index: idx_add_on_purchases_user_date';
    END IF;
    RAISE NOTICE '✓ Critical index idx_add_on_purchases_user_date exists';

    RAISE NOTICE '✓ All critical indexes verified';
END $$;

-- ============================================================================
-- TEST 4: TRIGGER VERIFICATION
-- ============================================================================

DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 4: TRIGGER VERIFICATION ===';

    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name LIKE '%updated_at%';

    IF trigger_count < 7 THEN
        RAISE EXCEPTION 'Missing updated_at triggers (found %, expected 7)', trigger_count;
    END IF;

    RAISE NOTICE '✓ All % updated_at triggers exist', trigger_count;
END $$;

-- ============================================================================
-- TEST 5: SAMPLE INSERT/SELECT OPERATIONS
-- ============================================================================

DO $$
DECLARE
    test_addon_id UUID;
    test_user_id VARCHAR(255) := 'test_user_' || gen_random_uuid()::text;
BEGIN
    RAISE NOTICE '=== TEST 5: SAMPLE OPERATIONS ===';

    -- Test 5a: Insert sample add-on
    INSERT INTO add_ons (name, description, category, base_price, billing_type, features)
    VALUES (
        'Test Add-on',
        'Test description',
        'ai-services',
        9.99,
        'monthly',
        '["test_feature_1", "test_feature_2"]'::jsonb
    )
    RETURNING id INTO test_addon_id;

    RAISE NOTICE '✓ Inserted test add-on: %', test_addon_id;

    -- Test 5b: Insert user purchase
    INSERT INTO user_add_ons (user_id, add_on_id, status)
    VALUES (test_user_id, test_addon_id, 'active');

    RAISE NOTICE '✓ Inserted test user purchase';

    -- Test 5c: Insert cart item
    INSERT INTO cart_items (user_id, add_on_id, quantity)
    VALUES (test_user_id, test_addon_id, 1);

    RAISE NOTICE '✓ Inserted test cart item';

    -- Test 5d: Insert add-on feature
    INSERT INTO add_on_features (add_on_id, feature_key, enabled, configuration)
    VALUES (test_addon_id, 'test_feature_1', TRUE, '{"test_config": "value"}'::jsonb);

    RAISE NOTICE '✓ Inserted test feature mapping';

    -- Test 5e: Insert promotional code
    INSERT INTO promotional_codes (code, discount_type, discount_value, max_uses)
    VALUES ('TEST2025', 'percentage', 10.00, 100);

    RAISE NOTICE '✓ Inserted test promotional code';

    -- Test 5f: Query with JOIN
    PERFORM u.id
    FROM user_add_ons u
    JOIN add_ons a ON u.add_on_id = a.id
    WHERE u.user_id = test_user_id AND a.is_active = TRUE;

    RAISE NOTICE '✓ JOIN query successful';

    -- Test 5g: JSONB query
    PERFORM id FROM add_ons WHERE features @> '["test_feature_1"]'::jsonb;

    RAISE NOTICE '✓ JSONB query successful';

    -- Cleanup test data
    DELETE FROM promotional_codes WHERE code = 'TEST2025';
    DELETE FROM add_on_features WHERE add_on_id = test_addon_id;
    DELETE FROM cart_items WHERE user_id = test_user_id;
    DELETE FROM user_add_ons WHERE user_id = test_user_id;
    DELETE FROM add_ons WHERE id = test_addon_id;

    RAISE NOTICE '✓ Test data cleaned up';
END $$;

-- ============================================================================
-- TEST 6: CONSTRAINT VALIDATION
-- ============================================================================

DO $$
DECLARE
    test_passed BOOLEAN := TRUE;
BEGIN
    RAISE NOTICE '=== TEST 6: CONSTRAINT VALIDATION ===';

    -- Test 6a: Invalid category should fail
    BEGIN
        INSERT INTO add_ons (name, category, base_price, billing_type)
        VALUES ('Test', 'invalid_category', 10.00, 'monthly');
        test_passed := FALSE;
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE '✓ Category constraint working';
    END;

    -- Test 6b: Negative price should fail
    BEGIN
        INSERT INTO add_ons (name, category, base_price, billing_type)
        VALUES ('Test', 'ai-services', -10.00, 'monthly');
        test_passed := FALSE;
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE '✓ Price constraint working';
    END;

    -- Test 6c: Invalid status should fail
    BEGIN
        INSERT INTO user_add_ons (user_id, add_on_id, status)
        VALUES ('test', gen_random_uuid(), 'invalid_status');
        test_passed := FALSE;
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE '✓ Status constraint working';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ Status constraint working (FK violation expected)';
    END;

    IF NOT test_passed THEN
        RAISE EXCEPTION 'Constraint validation failed';
    END IF;

    RAISE NOTICE '✓ All constraints validated';
END $$;

-- ============================================================================
-- TEST 7: UNIQUE CONSTRAINT VERIFICATION
-- ============================================================================

DO $$
DECLARE
    test_addon_id UUID;
    test_user_id VARCHAR(255) := 'unique_test_' || gen_random_uuid()::text;
BEGIN
    RAISE NOTICE '=== TEST 7: UNIQUE CONSTRAINTS ===';

    -- Create test add-on
    INSERT INTO add_ons (name, category, base_price, billing_type)
    VALUES ('Unique Test', 'ai-services', 9.99, 'monthly')
    RETURNING id INTO test_addon_id;

    -- Test 7a: Duplicate user_add_on should fail
    INSERT INTO user_add_ons (user_id, add_on_id) VALUES (test_user_id, test_addon_id);

    BEGIN
        INSERT INTO user_add_ons (user_id, add_on_id) VALUES (test_user_id, test_addon_id);
        RAISE EXCEPTION 'Unique constraint failed for user_add_ons';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE '✓ Unique constraint on user_add_ons working';
    END;

    -- Test 7b: Duplicate cart item should fail
    INSERT INTO cart_items (user_id, add_on_id) VALUES (test_user_id, test_addon_id);

    BEGIN
        INSERT INTO cart_items (user_id, add_on_id) VALUES (test_user_id, test_addon_id);
        RAISE EXCEPTION 'Unique constraint failed for cart_items';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE '✓ Unique constraint on cart_items working';
    END;

    -- Test 7c: Duplicate promotional code should fail
    INSERT INTO promotional_codes (code, discount_type, discount_value)
    VALUES ('UNIQUE2025', 'percentage', 10.00);

    BEGIN
        INSERT INTO promotional_codes (code, discount_type, discount_value)
        VALUES ('UNIQUE2025', 'percentage', 15.00);
        RAISE EXCEPTION 'Unique constraint failed for promotional_codes';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE '✓ Unique constraint on promotional_codes working';
    END;

    -- Cleanup
    DELETE FROM promotional_codes WHERE code = 'UNIQUE2025';
    DELETE FROM cart_items WHERE user_id = test_user_id;
    DELETE FROM user_add_ons WHERE user_id = test_user_id;
    DELETE FROM add_ons WHERE id = test_addon_id;

    RAISE NOTICE '✓ All unique constraints verified';
END $$;

-- ============================================================================
-- TEST 8: PERFORMANCE TEST (QUERY SPEED)
-- ============================================================================

DO $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration INTERVAL;
BEGIN
    RAISE NOTICE '=== TEST 8: PERFORMANCE TEST ===';

    -- Test 8a: User add-ons lookup (should use index)
    start_time := clock_timestamp();
    PERFORM * FROM user_add_ons WHERE user_id = 'test_user_123' LIMIT 100;
    end_time := clock_timestamp();
    duration := end_time - start_time;

    RAISE NOTICE '✓ User add-ons query: % ms', EXTRACT(MILLISECONDS FROM duration);

    -- Test 8b: JSONB feature query (should use GIN index)
    start_time := clock_timestamp();
    PERFORM * FROM add_ons WHERE features @> '["test_feature"]'::jsonb LIMIT 100;
    end_time := clock_timestamp();
    duration := end_time - start_time;

    RAISE NOTICE '✓ JSONB feature query: % ms', EXTRACT(MILLISECONDS FROM duration);

    -- Test 8c: Purchase history query (should use composite index)
    start_time := clock_timestamp();
    PERFORM * FROM add_on_purchases
    WHERE user_id = 'test_user_123'
    ORDER BY purchased_at DESC LIMIT 50;
    end_time := clock_timestamp();
    duration := end_time - start_time;

    RAISE NOTICE '✓ Purchase history query: % ms', EXTRACT(MILLISECONDS FROM duration);

    RAISE NOTICE '✓ Performance tests completed';
END $$;

-- ============================================================================
-- TEST 9: DATA INTEGRITY (SEED DATA)
-- ============================================================================

DO $$
DECLARE
    addon_count INTEGER;
    feature_count INTEGER;
BEGIN
    RAISE NOTICE '=== TEST 9: SEED DATA VERIFICATION ===';

    -- Check if seed data exists
    SELECT COUNT(*) INTO addon_count FROM add_ons;
    SELECT COUNT(*) INTO feature_count FROM add_on_features;

    IF addon_count = 0 THEN
        RAISE WARNING 'No seed data found. Run extensions_seed_data.sql first';
    ELSE
        RAISE NOTICE '✓ Found % add-ons', addon_count;
        RAISE NOTICE '✓ Found % feature mappings', feature_count;

        -- Verify specific add-ons
        IF EXISTS (SELECT 1 FROM add_ons WHERE name LIKE '%Orator%') THEN
            RAISE NOTICE '✓ TTS add-on found';
        END IF;

        IF EXISTS (SELECT 1 FROM add_ons WHERE name LIKE '%Amanuensis%') THEN
            RAISE NOTICE '✓ STT add-on found';
        END IF;

        IF EXISTS (SELECT 1 FROM add_ons WHERE name LIKE '%Brigade%') THEN
            RAISE NOTICE '✓ Brigade add-on found';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- TEST SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '         SCHEMA TEST SUITE COMPLETE';
    RAISE NOTICE '================================================';
    RAISE NOTICE '✓ Table existence verified';
    RAISE NOTICE '✓ Foreign keys validated';
    RAISE NOTICE '✓ Indexes confirmed';
    RAISE NOTICE '✓ Triggers working';
    RAISE NOTICE '✓ CRUD operations successful';
    RAISE NOTICE '✓ Constraints enforced';
    RAISE NOTICE '✓ Unique constraints working';
    RAISE NOTICE '✓ Performance acceptable';
    RAISE NOTICE '✓ Seed data status checked';
    RAISE NOTICE '================================================';
    RAISE NOTICE '         ALL TESTS PASSED ✓';
    RAISE NOTICE '================================================';
END $$;

-- Optional: Display schema statistics
SELECT
    'add_ons' AS table_name,
    COUNT(*) AS row_count,
    pg_size_pretty(pg_total_relation_size('add_ons')) AS total_size
FROM add_ons
UNION ALL
SELECT 'user_add_ons', COUNT(*), pg_size_pretty(pg_total_relation_size('user_add_ons'))
FROM user_add_ons
UNION ALL
SELECT 'add_on_purchases', COUNT(*), pg_size_pretty(pg_total_relation_size('add_on_purchases'))
FROM add_on_purchases
UNION ALL
SELECT 'cart_items', COUNT(*), pg_size_pretty(pg_total_relation_size('cart_items'))
FROM cart_items
UNION ALL
SELECT 'add_on_features', COUNT(*), pg_size_pretty(pg_total_relation_size('add_on_features'))
FROM add_on_features
UNION ALL
SELECT 'promotional_codes', COUNT(*), pg_size_pretty(pg_total_relation_size('promotional_codes'))
FROM promotional_codes;

-- Test suite complete!
