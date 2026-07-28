#!/usr/bin/env python3
"""
LiteLLM Database Schema Test Suite

Tests for validating the LiteLLM credit system database schema.

Usage:
    pytest test_litellm_schema.py
    pytest test_litellm_schema.py -v
    pytest test_litellm_schema.py -k test_user_credits
"""

import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import json
from datetime import datetime, timedelta


@pytest.fixture(scope='module')
def db_connection():
    """Create database connection for tests"""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'unicorn_db'),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
    )
    yield conn
    conn.close()


@pytest.fixture
def cursor(db_connection):
    """Create cursor for tests"""
    cur = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cur
    db_connection.rollback()  # Rollback after each test
    cur.close()


class TestSchemaStructure:
    """Test database schema structure"""

    def test_user_credits_table_exists(self, cursor):
        """Test user_credits table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'user_credits'
            );
        """)
        assert cursor.fetchone()['exists'], "user_credits table should exist"

    def test_credit_transactions_table_exists(self, cursor):
        """Test credit_transactions table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'credit_transactions'
            );
        """)
        assert cursor.fetchone()['exists'], "credit_transactions table should exist"

    def test_user_provider_keys_table_exists(self, cursor):
        """Test user_provider_keys table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'user_provider_keys'
            );
        """)
        assert cursor.fetchone()['exists'], "user_provider_keys table should exist"

    def test_llm_usage_log_table_exists(self, cursor):
        """Test llm_usage_log table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'llm_usage_log'
            );
        """)
        assert cursor.fetchone()['exists'], "llm_usage_log table should exist"

    def test_provider_health_table_exists(self, cursor):
        """Test provider_health table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'provider_health'
            );
        """)
        assert cursor.fetchone()['exists'], "provider_health table should exist"

    def test_credit_packages_table_exists(self, cursor):
        """Test credit_packages table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'credit_packages'
            );
        """)
        assert cursor.fetchone()['exists'], "credit_packages table should exist"

    def test_power_level_configs_table_exists(self, cursor):
        """Test power_level_configs table exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'power_level_configs'
            );
        """)
        assert cursor.fetchone()['exists'], "power_level_configs table should exist"

    def test_llm_usage_summary_view_exists(self, cursor):
        """Test llm_usage_summary materialized view exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_matviews
                WHERE schemaname = 'public'
                AND matviewname = 'llm_usage_summary'
            );
        """)
        assert cursor.fetchone()['exists'], "llm_usage_summary view should exist"


class TestFunctions:
    """Test database functions"""

    def test_debit_user_credits_function_exists(self, cursor):
        """Test debit_user_credits function exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'debit_user_credits'
            );
        """)
        assert cursor.fetchone()['exists'], "debit_user_credits function should exist"

    def test_add_user_credits_function_exists(self, cursor):
        """Test add_user_credits function exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'add_user_credits'
            );
        """)
        assert cursor.fetchone()['exists'], "add_user_credits function should exist"

    def test_get_user_balance_function_exists(self, cursor):
        """Test get_user_balance function exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'get_user_balance'
            );
        """)
        assert cursor.fetchone()['exists'], "get_user_balance function should exist"

    def test_refresh_usage_summary_function_exists(self, cursor):
        """Test refresh_usage_summary function exists"""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'refresh_usage_summary'
            );
        """)
        assert cursor.fetchone()['exists'], "refresh_usage_summary function should exist"


class TestIndexes:
    """Test database indexes"""

    def test_user_credits_indexes(self, cursor):
        """Test user_credits table has proper indexes"""
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'user_credits'
            AND schemaname = 'public';
        """)
        indexes = [row['indexname'] for row in cursor.fetchall()]

        assert 'idx_user_credits_user_id' in indexes
        assert 'idx_user_credits_tier' in indexes
        assert 'idx_user_credits_updated_at' in indexes

    def test_credit_transactions_indexes(self, cursor):
        """Test credit_transactions table has proper indexes"""
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'credit_transactions'
            AND schemaname = 'public';
        """)
        indexes = [row['indexname'] for row in cursor.fetchall()]

        assert 'idx_credit_transactions_user_id' in indexes
        assert 'idx_credit_transactions_created_at' in indexes
        assert 'idx_credit_transactions_type' in indexes

    def test_llm_usage_log_indexes(self, cursor):
        """Test llm_usage_log table has proper indexes"""
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'llm_usage_log'
            AND schemaname = 'public';
        """)
        indexes = [row['indexname'] for row in cursor.fetchall()]

        assert 'idx_llm_usage_log_user_id' in indexes
        assert 'idx_llm_usage_log_created_at' in indexes
        assert 'idx_llm_usage_log_provider' in indexes
        assert 'idx_llm_usage_log_model' in indexes


class TestSeedData:
    """Test seed data"""

    def test_credit_packages_seeded(self, cursor):
        """Test credit packages are seeded"""
        cursor.execute("SELECT COUNT(*) as count FROM credit_packages;")
        count = cursor.fetchone()['count']
        assert count >= 4, "Should have at least 4 credit packages"

    def test_power_level_configs_seeded(self, cursor):
        """Test power level configs are seeded"""
        cursor.execute("SELECT COUNT(*) as count FROM power_level_configs;")
        count = cursor.fetchone()['count']
        assert count == 3, "Should have exactly 3 power level configs"

    def test_power_levels_correct(self, cursor):
        """Test power level configs have correct values"""
        cursor.execute("""
            SELECT power_level, cost_multiplier
            FROM power_level_configs
            ORDER BY cost_multiplier;
        """)
        configs = cursor.fetchall()

        assert configs[0]['power_level'] == 'eco'
        assert configs[0]['cost_multiplier'] == 0.7

        assert configs[1]['power_level'] == 'balanced'
        assert configs[1]['cost_multiplier'] == 1.0

        assert configs[2]['power_level'] == 'precision'
        assert configs[2]['cost_multiplier'] == 1.5


class TestUserCredits:
    """Test user_credits functionality"""

    def test_add_user_credits_creates_user(self, cursor, db_connection):
        """Test adding credits creates new user"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 100.0, 'bonus', 'trial', NULL, NULL, 'Test bonus'
            );
        """, (test_user_id,))

        result = cursor.fetchone()
        assert result['success'] is True
        assert result['new_balance'] == 100.0
        assert result['error_message'] is None

        # Verify user exists
        cursor.execute(
            "SELECT credits_remaining FROM user_credits WHERE user_id = %s;",
            (test_user_id,)
        )
        user = cursor.fetchone()
        assert user is not None
        assert user['credits_remaining'] == 100.0

        db_connection.rollback()

    def test_debit_user_credits_reduces_balance(self, cursor, db_connection):
        """Test debiting credits reduces balance"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Create user with 100 credits
        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 100.0, 'bonus', 'trial', NULL, NULL, 'Test'
            );
        """, (test_user_id,))

        # Debit 10 credits
        cursor.execute("""
            SELECT * FROM debit_user_credits(
                %s, 10.0, 'openai', 'gpt-4', 100, 200, 'balanced',
                '{}'::JSONB
            );
        """, (test_user_id,))

        result = cursor.fetchone()
        assert result['success'] is True
        assert result['new_balance'] == 90.0

        db_connection.rollback()

    def test_debit_insufficient_credits_fails(self, cursor, db_connection):
        """Test debiting more than available credits fails"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Create user with 10 credits
        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 10.0, 'bonus', 'trial', NULL, NULL, 'Test'
            );
        """, (test_user_id,))

        # Try to debit 20 credits
        cursor.execute("""
            SELECT * FROM debit_user_credits(
                %s, 20.0, 'openai', 'gpt-4', 100, 200, 'balanced',
                '{}'::JSONB
            );
        """, (test_user_id,))

        result = cursor.fetchone()
        assert result['success'] is False
        assert 'Insufficient credits' in result['error_message']

        db_connection.rollback()

    def test_get_user_balance(self, cursor, db_connection):
        """Test getting user balance"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Create user
        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 150.0, 'purchase', 'stripe', 'ch_123', 1, NULL
            );
        """, (test_user_id,))

        # Get balance
        cursor.execute("SELECT * FROM get_user_balance(%s);", (test_user_id,))
        balance = cursor.fetchone()

        assert balance is not None
        assert balance['credits_remaining'] == 150.0
        assert balance['credits_lifetime'] == 150.0
        assert balance['tier'] == 'free'
        assert balance['power_level'] == 'balanced'

        db_connection.rollback()


class TestCreditTransactions:
    """Test credit_transactions audit trail"""

    def test_transaction_created_on_add_credits(self, cursor, db_connection):
        """Test transaction record created when adding credits"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 100.0, 'purchase', 'stripe', 'ch_123', 1, 'Test purchase'
            );
        """, (test_user_id,))

        # Check transaction exists
        cursor.execute("""
            SELECT * FROM credit_transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
        """, (test_user_id,))

        txn = cursor.fetchone()
        assert txn is not None
        assert txn['transaction_type'] == 'purchase'
        assert txn['amount'] == 100.0
        assert txn['balance_after'] == 100.0
        assert txn['payment_method'] == 'stripe'
        assert txn['stripe_transaction_id'] == 'ch_123'

        db_connection.rollback()

    def test_transaction_created_on_debit_credits(self, cursor, db_connection):
        """Test transaction record created when debiting credits"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Add credits
        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 100.0, 'bonus', 'trial', NULL, NULL, 'Test'
            );
        """, (test_user_id,))

        # Debit credits
        cursor.execute("""
            SELECT * FROM debit_user_credits(
                %s, 5.0, 'anthropic', 'claude-3-opus', 150, 300, 'precision',
                '{"request_id": "req-123"}'::JSONB
            );
        """, (test_user_id,))

        # Check transaction
        cursor.execute("""
            SELECT * FROM credit_transactions
            WHERE user_id = %s AND transaction_type = 'debit'
            ORDER BY created_at DESC
            LIMIT 1;
        """, (test_user_id,))

        txn = cursor.fetchone()
        assert txn is not None
        assert txn['transaction_type'] == 'debit'
        assert txn['amount'] == -5.0
        assert txn['provider'] == 'anthropic'
        assert txn['model'] == 'claude-3-opus'
        assert txn['power_level'] == 'precision'
        assert txn['tokens_used'] == 450

        db_connection.rollback()


class TestProviderKeys:
    """Test user_provider_keys BYOK functionality"""

    def test_insert_provider_key(self, cursor, db_connection):
        """Test inserting provider key"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        cursor.execute("""
            INSERT INTO user_provider_keys (
                user_id, provider, encrypted_api_key, key_name
            ) VALUES (%s, 'openai', 'encrypted_key_123', 'My OpenAI Key')
            RETURNING id;
        """, (test_user_id,))

        key_id = cursor.fetchone()['id']
        assert key_id is not None

        # Verify key exists
        cursor.execute(
            "SELECT * FROM user_provider_keys WHERE id = %s;",
            (key_id,)
        )
        key = cursor.fetchone()
        assert key['user_id'] == test_user_id
        assert key['provider'] == 'openai'
        assert key['is_active'] is True

        db_connection.rollback()

    def test_unique_constraint_provider_keys(self, cursor, db_connection):
        """Test unique constraint on (user_id, provider, key_name)"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Insert first key
        cursor.execute("""
            INSERT INTO user_provider_keys (
                user_id, provider, encrypted_api_key, key_name
            ) VALUES (%s, 'openai', 'key1', 'My Key');
        """, (test_user_id,))

        # Try to insert duplicate
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO user_provider_keys (
                    user_id, provider, encrypted_api_key, key_name
                ) VALUES (%s, 'openai', 'key2', 'My Key');
            """, (test_user_id,))

        db_connection.rollback()


class TestUsageLog:
    """Test llm_usage_log functionality"""

    def test_insert_usage_log(self, cursor, db_connection):
        """Test inserting usage log entry"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        cursor.execute("""
            INSERT INTO llm_usage_log (
                user_id, provider, model, power_level,
                prompt_tokens, completion_tokens, total_tokens,
                cost_credits, success, latency_ms, request_id
            ) VALUES (
                %s, 'openai', 'gpt-4', 'balanced',
                100, 200, 300, 0.05, TRUE, 1234, 'req-123'
            ) RETURNING id;
        """, (test_user_id,))

        log_id = cursor.fetchone()['id']
        assert log_id is not None

        # Verify log exists
        cursor.execute(
            "SELECT * FROM llm_usage_log WHERE id = %s;",
            (log_id,)
        )
        log = cursor.fetchone()
        assert log['provider'] == 'openai'
        assert log['model'] == 'gpt-4'
        assert log['total_tokens'] == 300
        assert log['cost_credits'] == 0.05
        assert log['success'] is True

        db_connection.rollback()

    def test_usage_log_unique_request_id(self, cursor, db_connection):
        """Test request_id is unique"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Insert first log
        cursor.execute("""
            INSERT INTO llm_usage_log (
                user_id, provider, model, power_level,
                prompt_tokens, completion_tokens, total_tokens,
                cost_credits, success, request_id
            ) VALUES (
                %s, 'openai', 'gpt-4', 'balanced',
                100, 200, 300, 0.05, TRUE, 'unique-req-123'
            );
        """, (test_user_id,))

        # Try to insert duplicate request_id
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO llm_usage_log (
                    user_id, provider, model, power_level,
                    prompt_tokens, completion_tokens, total_tokens,
                    cost_credits, success, request_id
                ) VALUES (
                    %s, 'openai', 'gpt-4', 'balanced',
                    100, 200, 300, 0.05, TRUE, 'unique-req-123'
                );
            """, (test_user_id,))

        db_connection.rollback()


class TestConstraints:
    """Test database constraints"""

    def test_tier_constraint(self, cursor, db_connection):
        """Test tier must be valid value"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO user_credits (user_id, tier)
                VALUES (%s, 'invalid_tier');
            """, (test_user_id,))

        db_connection.rollback()

    def test_power_level_constraint(self, cursor, db_connection):
        """Test power_level must be valid value"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO user_credits (user_id, power_level)
                VALUES (%s, 'invalid_level');
            """, (test_user_id,))

        db_connection.rollback()

    def test_positive_credits_constraint(self, cursor, db_connection):
        """Test credits_remaining must be >= 0"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute("""
                INSERT INTO user_credits (user_id, credits_remaining)
                VALUES (%s, -10.0);
            """, (test_user_id,))

        db_connection.rollback()


class TestPerformance:
    """Test query performance"""

    def test_user_lookup_performance(self, cursor, db_connection):
        """Test user lookup is fast (uses index)"""
        test_user_id = f'test-user-{datetime.now().timestamp()}'

        # Create user
        cursor.execute("""
            SELECT * FROM add_user_credits(
                %s, 100.0, 'bonus', 'trial', NULL, NULL, 'Test'
            );
        """, (test_user_id,))

        # Explain analyze query
        cursor.execute("""
            EXPLAIN ANALYZE
            SELECT * FROM user_credits WHERE user_id = %s;
        """, (test_user_id,))

        explain = '\n'.join([row[0] for row in cursor.fetchall()])
        assert 'Index Scan' in explain or 'Bitmap Heap Scan' in explain

        db_connection.rollback()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
