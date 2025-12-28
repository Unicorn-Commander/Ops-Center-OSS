#!/usr/bin/env python3
"""
Dynamic Tier Migration Script
Converts hardcoded JSONB tier names to relational many-to-many model

This script:
1. Reads the SQL migration file
2. Executes the migration in a transaction
3. Verifies the results
4. Provides detailed reporting

Usage:
    python3 migrate_tiers.py [--dry-run] [--verbose]

Options:
    --dry-run   Run migration but rollback at the end (for testing)
    --verbose   Show detailed SQL execution logs
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path


class TierMigrationRunner:
    """Handles the execution of tier-to-model relationship migration"""

    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.conn = None
        self.migration_start = None
        self.results = {}

    async def connect(self):
        """Establish database connection"""
        try:
            self.conn = await asyncpg.connect(
                host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", "unicorn"),
                password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
                database=os.getenv("POSTGRES_DB", "unicorn_db")
            )
            print(f"✅ Connected to database: {os.getenv('POSTGRES_DB', 'unicorn_db')}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            print("✅ Database connection closed")

    def read_migration_sql(self):
        """Read the SQL migration file"""
        sql_file = Path(__file__).parent.parent / "sql" / "migrate_to_dynamic_tiers.sql"

        if not sql_file.exists():
            print(f"❌ Migration file not found: {sql_file}")
            return None

        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            print(f"✅ Loaded migration SQL ({len(sql_content)} bytes)")
            return sql_content
        except Exception as e:
            print(f"❌ Failed to read migration file: {e}")
            return None

    async def verify_prerequisites(self):
        """Verify that required tables exist"""
        print("\n🔍 Verifying prerequisites...")

        required_tables = [
            'subscription_tiers',
            'model_access_control'
        ]

        for table in required_tables:
            exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = $1
                )
            """, table)

            if not exists:
                print(f"❌ Required table '{table}' does not exist")
                return False
            print(f"  ✅ Table '{table}' exists")

        return True

    async def get_pre_migration_stats(self):
        """Gather statistics before migration"""
        print("\n📊 Pre-migration statistics:")

        stats = {}

        # Count active models
        stats['total_models'] = await self.conn.fetchval("""
            SELECT COUNT(*) FROM model_access_control WHERE enabled = TRUE
        """)
        print(f"  • Total active models: {stats['total_models']}")

        # Count active tiers
        stats['total_tiers'] = await self.conn.fetchval("""
            SELECT COUNT(*) FROM subscription_tiers WHERE is_active = TRUE
        """)
        print(f"  • Total active tiers: {stats['total_tiers']}")

        # Count models with tier_access
        stats['models_with_tiers'] = await self.conn.fetchval("""
            SELECT COUNT(*)
            FROM model_access_control
            WHERE tier_access IS NOT NULL AND tier_access != 'null'::jsonb
        """)
        print(f"  • Models with tier access: {stats['models_with_tiers']}")

        # Sample tier data
        sample_tiers = await self.conn.fetch("""
            SELECT tier_code, tier_name
            FROM subscription_tiers
            WHERE is_active = TRUE
            ORDER BY sort_order
            LIMIT 5
        """)
        print(f"  • Sample tiers: {', '.join([t['tier_code'] for t in sample_tiers])}")

        self.results['pre_migration'] = stats
        return stats

    async def execute_migration(self, sql_content):
        """Execute the migration SQL"""
        print("\n🚀 Executing migration...")
        self.migration_start = datetime.now()

        try:
            # Execute within a transaction
            async with self.conn.transaction():
                # Split SQL into statements (simple approach)
                # Note: This doesn't handle all SQL edge cases
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]

                executed = 0
                for i, statement in enumerate(statements, 1):
                    # Skip comments and empty statements
                    if (not statement or
                        statement.startswith('--') or
                        statement.startswith('/*') or
                        statement.upper().startswith('COMMENT')):
                        continue

                    if self.verbose:
                        print(f"  Executing statement {i}...")

                    try:
                        await self.conn.execute(statement)
                        executed += 1
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"  ⚠️  Statement {i} warning: {e}")

                print(f"  ✅ Executed {executed} SQL statements")

                if self.dry_run:
                    print("\n⚠️  DRY RUN MODE: Rolling back transaction...")
                    raise Exception("Dry run - intentional rollback")

            migration_duration = (datetime.now() - self.migration_start).total_seconds()
            print(f"✅ Migration completed in {migration_duration:.2f} seconds")
            return True

        except Exception as e:
            if self.dry_run and "Dry run" in str(e):
                print("✅ Dry run completed successfully (changes rolled back)")
                return True
            else:
                print(f"❌ Migration failed: {e}")
                return False

    async def verify_migration(self):
        """Verify migration results"""
        print("\n🔍 Verifying migration results...")

        try:
            # Check if tier_model_access table exists
            table_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'tier_model_access'
                )
            """)

            if not table_exists:
                print("❌ tier_model_access table was not created")
                return False

            print("  ✅ tier_model_access table exists")

            # Count associations
            total_associations = await self.conn.fetchval("""
                SELECT COUNT(*) FROM tier_model_access
            """)
            print(f"  • Total tier-model associations: {total_associations}")

            # Count models with associations
            models_with_assoc = await self.conn.fetchval("""
                SELECT COUNT(DISTINCT model_id) FROM tier_model_access
            """)
            print(f"  • Models with associations: {models_with_assoc}")

            # Get tier breakdown
            tier_breakdown = await self.conn.fetch("""
                SELECT
                    st.tier_code,
                    st.tier_name,
                    COUNT(tma.model_id) AS model_count
                FROM subscription_tiers st
                LEFT JOIN tier_model_access tma ON st.id = tma.tier_id
                WHERE st.is_active = TRUE
                GROUP BY st.tier_code, st.tier_name
                ORDER BY st.tier_code
            """)

            print("\n  📋 Models per tier:")
            for row in tier_breakdown:
                print(f"    • {row['tier_code']:15} {row['model_count']:4} models")

            # Check view exists
            view_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.views
                    WHERE table_name = 'v_model_tier_access'
                )
            """)

            if view_exists:
                print("  ✅ Compatibility view 'v_model_tier_access' exists")
            else:
                print("  ⚠️  Compatibility view was not created")

            # Check functions exist
            functions = ['get_models_for_tier', 'is_model_available_for_tier']
            for func in functions:
                func_exists = await self.conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_proc
                        WHERE proname = $1
                    )
                """, func)

                if func_exists:
                    print(f"  ✅ Function '{func}' exists")
                else:
                    print(f"  ⚠️  Function '{func}' was not created")

            self.results['post_migration'] = {
                'total_associations': total_associations,
                'models_with_associations': models_with_assoc,
                'tier_breakdown': tier_breakdown
            }

            return True

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    async def test_helper_functions(self):
        """Test the newly created helper functions"""
        print("\n🧪 Testing helper functions...")

        try:
            # Test get_models_for_tier
            first_tier = await self.conn.fetchval("""
                SELECT tier_code FROM subscription_tiers
                WHERE is_active = TRUE
                ORDER BY sort_order
                LIMIT 1
            """)

            if first_tier:
                models = await self.conn.fetch("""
                    SELECT * FROM get_models_for_tier($1)
                    LIMIT 5
                """, first_tier)

                print(f"  ✅ get_models_for_tier('{first_tier}') returned {len(models)} models")

            # Test is_model_available_for_tier
            test_model = await self.conn.fetchrow("""
                SELECT model_id, tier_id
                FROM tier_model_access
                LIMIT 1
            """)

            if test_model:
                tier_code = await self.conn.fetchval("""
                    SELECT tier_code FROM subscription_tiers WHERE id = $1
                """, test_model['tier_id'])

                is_available = await self.conn.fetchval("""
                    SELECT is_model_available_for_tier($1, $2)
                """, test_model['model_id'], tier_code)

                print(f"  ✅ is_model_available_for_tier() test: {is_available}")

            return True

        except Exception as e:
            print(f"⚠️  Function testing failed: {e}")
            return False

    def print_summary(self):
        """Print migration summary"""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)

        if 'pre_migration' in self.results:
            pre = self.results['pre_migration']
            print(f"Before: {pre['models_with_tiers']} models had tier access data")

        if 'post_migration' in self.results:
            post = self.results['post_migration']
            print(f"After:  {post['total_associations']} tier-model associations created")
            print(f"        {post['models_with_associations']} models now have explicit tier links")

        if self.migration_start:
            duration = (datetime.now() - self.migration_start).total_seconds()
            print(f"\nMigration completed in: {duration:.2f} seconds")

        if self.dry_run:
            print("\n⚠️  This was a DRY RUN - no changes were persisted")
        else:
            print("\n✅ Migration completed successfully!")

        print("="*60 + "\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Migrate tier-model relationships to relational model')
    parser.add_argument('--dry-run', action='store_true', help='Run migration but rollback changes')
    parser.add_argument('--verbose', action='store_true', help='Show detailed execution logs')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("TIER-MODEL RELATIONSHIP MIGRATION")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print("="*60 + "\n")

    runner = TierMigrationRunner(dry_run=args.dry_run, verbose=args.verbose)

    try:
        # Connect to database
        if not await runner.connect():
            return 1

        # Verify prerequisites
        if not await runner.verify_prerequisites():
            return 1

        # Get pre-migration stats
        await runner.get_pre_migration_stats()

        # Read migration SQL
        sql_content = runner.read_migration_sql()
        if not sql_content:
            return 1

        # Execute migration
        if not await runner.execute_migration(sql_content):
            return 1

        # Verify results (skip in dry-run mode)
        if not args.dry_run:
            if not await runner.verify_migration():
                print("\n⚠️  Verification failed, but migration may be partially complete")
                return 1

            # Test helper functions
            await runner.test_helper_functions()

        # Print summary
        runner.print_summary()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await runner.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
