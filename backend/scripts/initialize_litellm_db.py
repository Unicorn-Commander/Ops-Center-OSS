#!/usr/bin/env python3
"""
LiteLLM Database Initialization Script

This script initializes the LiteLLM credit system database schema.

Usage:
    python initialize_litellm_db.py [--reset] [--test-data]

Options:
    --reset      Drop existing tables before creating (DESTRUCTIVE!)
    --test-data  Insert test data for development
    --help       Show this help message

Examples:
    # Initialize schema (safe - won't drop existing data)
    python initialize_litellm_db.py

    # Reset and initialize (DESTRUCTIVE - drops all data)
    python initialize_litellm_db.py --reset

    # Initialize with test data
    python initialize_litellm_db.py --test-data
"""

import sys
import os
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class LiteLLMDatabaseInitializer:
    """Initialize LiteLLM credit system database"""

    def __init__(self, db_config=None):
        """Initialize with database configuration"""
        self.db_config = db_config or self.get_default_config()
        self.conn = None
        self.cursor = None

    @staticmethod
    def get_default_config():
        """Get database configuration from environment"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'unicorn_db'),
            'user': os.getenv('POSTGRES_USER', 'unicorn'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
        }

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            print(f"Connecting to PostgreSQL at {self.db_config['host']}:{self.db_config['port']}...")
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            print("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            return False

    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Disconnected from PostgreSQL")

    def execute_sql_file(self, filepath):
        """Execute SQL file"""
        try:
            print(f"\nExecuting SQL file: {filepath}")
            with open(filepath, 'r') as f:
                sql = f.read()

            # Execute SQL (handles multi-statement files)
            self.cursor.execute(sql)
            print(f"✅ Successfully executed {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to execute {filepath}: {e}")
            return False

    def check_schema_exists(self):
        """Check if LiteLLM schema already exists"""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'user_credits'
                );
            """)
            exists = self.cursor.fetchone()[0]
            return exists
        except Exception as e:
            print(f"Error checking schema: {e}")
            return False

    def drop_schema(self):
        """Drop existing LiteLLM tables (DESTRUCTIVE!)"""
        print("\n⚠️  WARNING: Dropping existing LiteLLM tables...")
        print("This will delete ALL credit system data!")

        response = input("Type 'YES' to confirm: ")
        if response != 'YES':
            print("Aborted.")
            return False

        try:
            # Drop tables in correct order (respect foreign keys)
            tables = [
                'llm_usage_log',
                'credit_transactions',
                'user_provider_keys',
                'user_credits',
                'provider_health',
                'credit_packages',
                'power_level_configs',
                'schema_version',
            ]

            for table in tables:
                print(f"Dropping table: {table}")
                self.cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

            # Drop materialized views
            print("Dropping materialized view: llm_usage_summary")
            self.cursor.execute("DROP MATERIALIZED VIEW IF EXISTS llm_usage_summary CASCADE;")

            # Drop functions
            functions = [
                'debit_user_credits',
                'add_user_credits',
                'get_user_balance',
                'refresh_usage_summary',
                'update_updated_at_column',
            ]

            for func in functions:
                print(f"Dropping function: {func}")
                self.cursor.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE;")

            print("✅ Schema dropped successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to drop schema: {e}")
            return False

    def verify_installation(self):
        """Verify schema installation"""
        print("\n🔍 Verifying installation...")

        checks = {
            'Tables': [
                'user_credits',
                'credit_transactions',
                'user_provider_keys',
                'llm_usage_log',
                'provider_health',
                'credit_packages',
                'power_level_configs',
                'schema_version',
            ],
            'Functions': [
                'debit_user_credits',
                'add_user_credits',
                'get_user_balance',
                'refresh_usage_summary',
            ],
            'Materialized Views': [
                'llm_usage_summary',
            ],
        }

        all_passed = True

        # Check tables
        print("\n📋 Checking tables...")
        for table in checks['Tables']:
            self.cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = '{table}'
                );
            """)
            exists = self.cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
            if not exists:
                all_passed = False

        # Check functions
        print("\n⚙️  Checking functions...")
        for func in checks['Functions']:
            self.cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = '{func}'
                );
            """)
            exists = self.cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {func}()")
            if not exists:
                all_passed = False

        # Check materialized views
        print("\n📊 Checking materialized views...")
        for view in checks['Materialized Views']:
            self.cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM pg_matviews
                    WHERE schemaname = 'public' AND matviewname = '{view}'
                );
            """)
            exists = self.cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {view}")
            if not exists:
                all_passed = False

        # Check seed data
        print("\n🌱 Checking seed data...")
        self.cursor.execute("SELECT COUNT(*) FROM credit_packages;")
        package_count = self.cursor.fetchone()[0]
        print(f"  ✅ {package_count} credit packages")

        self.cursor.execute("SELECT COUNT(*) FROM power_level_configs;")
        config_count = self.cursor.fetchone()[0]
        print(f"  ✅ {config_count} power level configs")

        return all_passed

    def insert_test_data(self):
        """Insert test data for development"""
        print("\n🧪 Inserting test data...")

        try:
            # Test user
            test_user_id = 'test-user-123'

            # 1. Create test user with credits
            print(f"Creating test user: {test_user_id}")
            self.cursor.execute("""
                SELECT * FROM add_user_credits(
                    %s, 1000.0, 'bonus', 'trial', NULL, NULL, 'Test user welcome bonus'
                );
            """, (test_user_id,))
            result = self.cursor.fetchone()
            print(f"  ✅ User created with {result[0]} credits")

            # 2. Insert some test BYOK keys (encrypted with placeholder)
            print("Creating test provider keys...")
            from cryptography.fernet import Fernet
            cipher_key = Fernet.generate_key()
            cipher = Fernet(cipher_key)

            test_keys = [
                ('openai', 'sk-test-openai-key-123', 'My OpenAI Key'),
                ('anthropic', 'sk-ant-test-key-456', 'My Claude Key'),
                ('openrouter', 'sk-or-test-key-789', 'OpenRouter Key'),
            ]

            for provider, api_key, key_name in test_keys:
                encrypted_key = cipher.encrypt(api_key.encode()).decode()
                self.cursor.execute("""
                    INSERT INTO user_provider_keys (
                        user_id, provider, encrypted_api_key, key_name, is_active
                    ) VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT DO NOTHING;
                """, (test_user_id, provider, encrypted_key, key_name))
            print(f"  ✅ Created {len(test_keys)} test API keys")

            # 3. Simulate some usage
            print("Simulating LLM usage...")
            test_requests = [
                {
                    'provider': 'openai',
                    'model': 'gpt-4',
                    'power_level': 'balanced',
                    'prompt_tokens': 100,
                    'completion_tokens': 200,
                    'cost': 0.05,
                    'latency_ms': 1234,
                },
                {
                    'provider': 'anthropic',
                    'model': 'claude-3-opus-20240229',
                    'power_level': 'precision',
                    'prompt_tokens': 150,
                    'completion_tokens': 300,
                    'cost': 0.08,
                    'latency_ms': 2345,
                },
                {
                    'provider': 'openrouter',
                    'model': 'openai/gpt-3.5-turbo',
                    'power_level': 'eco',
                    'prompt_tokens': 80,
                    'completion_tokens': 120,
                    'cost': 0.02,
                    'latency_ms': 890,
                },
            ]

            for i, req in enumerate(test_requests):
                # Debit credits
                self.cursor.execute("""
                    SELECT * FROM debit_user_credits(
                        %s, %s, %s, %s, %s, %s, %s,
                        %s::JSONB
                    );
                """, (
                    test_user_id,
                    req['cost'],
                    req['provider'],
                    req['model'],
                    req['prompt_tokens'],
                    req['completion_tokens'],
                    req['power_level'],
                    json.dumps({'request_id': f'test-req-{i+1}'}),
                ))

                # Log usage
                self.cursor.execute("""
                    INSERT INTO llm_usage_log (
                        user_id, provider, model, power_level,
                        prompt_tokens, completion_tokens, total_tokens,
                        cost_credits, success, latency_ms, request_id,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s,
                        NOW() - INTERVAL '%s days'
                    );
                """, (
                    test_user_id,
                    req['provider'],
                    req['model'],
                    req['power_level'],
                    req['prompt_tokens'],
                    req['completion_tokens'],
                    req['prompt_tokens'] + req['completion_tokens'],
                    req['cost'],
                    req['latency_ms'],
                    f'test-req-{i+1}',
                    i  # Spread over last 3 days
                ))

            print(f"  ✅ Created {len(test_requests)} test LLM requests")

            # 4. Update provider health
            print("Updating provider health...")
            providers = ['openai', 'anthropic', 'openrouter', 'google', 'cohere']
            for provider in providers:
                self.cursor.execute("""
                    INSERT INTO provider_health (
                        provider, status, avg_latency_ms, success_rate,
                        last_check, last_success
                    ) VALUES (
                        %s, 'healthy', %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (provider) DO UPDATE
                    SET status = EXCLUDED.status,
                        avg_latency_ms = EXCLUDED.avg_latency_ms,
                        success_rate = EXCLUDED.success_rate,
                        last_check = EXCLUDED.last_check,
                        last_success = EXCLUDED.last_success;
                """, (provider, 1500, 99.5))
            print(f"  ✅ Updated health for {len(providers)} providers")

            # 5. Refresh materialized view
            print("Refreshing analytics...")
            self.cursor.execute("SELECT refresh_usage_summary();")
            print("  ✅ Analytics refreshed")

            # 6. Display test user summary
            print("\n📊 Test User Summary:")
            self.cursor.execute("SELECT * FROM get_user_balance(%s);", (test_user_id,))
            balance = self.cursor.fetchone()
            print(f"  Credits Remaining: {balance[0]:.2f}")
            print(f"  Credits Lifetime: {balance[1]:.2f}")
            print(f"  Tier: {balance[2]}")
            print(f"  Power Level: {balance[3]}")

            print("\n✅ Test data inserted successfully")
            print(f"\n💡 Test user ID: {test_user_id}")
            print(f"💡 Encryption key (save for testing): {cipher_key.decode()}")

            return True

        except Exception as e:
            print(f"❌ Failed to insert test data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, reset=False, test_data=False):
        """Run database initialization"""
        print("=" * 60)
        print("LiteLLM Database Initialization")
        print("=" * 60)

        # Connect to database
        if not self.connect():
            return False

        try:
            # Check if schema exists
            schema_exists = self.check_schema_exists()

            if schema_exists and not reset:
                print("\n⚠️  LiteLLM schema already exists!")
                print("Use --reset flag to drop and recreate (DESTRUCTIVE!)")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return False

            # Reset if requested
            if reset and schema_exists:
                if not self.drop_schema():
                    return False

            # Execute schema file
            schema_file = Path(__file__).parent.parent / 'sql' / 'litellm_schema.sql'
            if not schema_file.exists():
                print(f"❌ Schema file not found: {schema_file}")
                return False

            if not self.execute_sql_file(schema_file):
                return False

            # Verify installation
            if not self.verify_installation():
                print("\n❌ Verification failed!")
                return False

            # Insert test data if requested
            if test_data:
                if not self.insert_test_data():
                    return False

            print("\n" + "=" * 60)
            print("✅ LiteLLM Database Initialization Complete!")
            print("=" * 60)

            # Final summary
            print("\n📊 Database Summary:")
            self.cursor.execute("SELECT COUNT(*) FROM user_credits;")
            print(f"  Users: {self.cursor.fetchone()[0]}")

            self.cursor.execute("SELECT COUNT(*) FROM credit_transactions;")
            print(f"  Transactions: {self.cursor.fetchone()[0]}")

            self.cursor.execute("SELECT COUNT(*) FROM llm_usage_log;")
            print(f"  Usage Logs: {self.cursor.fetchone()[0]}")

            self.cursor.execute("SELECT COUNT(*) FROM credit_packages WHERE is_active = TRUE;")
            print(f"  Active Packages: {self.cursor.fetchone()[0]}")

            return True

        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.disconnect()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize LiteLLM credit system database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop existing tables before creating (DESTRUCTIVE!)'
    )
    parser.add_argument(
        '--test-data',
        action='store_true',
        help='Insert test data for development'
    )

    args = parser.parse_args()

    # Initialize database
    initializer = LiteLLMDatabaseInitializer()
    success = initializer.run(reset=args.reset, test_data=args.test_data)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
