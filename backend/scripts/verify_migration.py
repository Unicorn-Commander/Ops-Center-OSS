#!/usr/bin/env python3
"""
Tier Migration Verification Script
Validates the tier_model_access table and confirms data integrity

Usage:
    python3 verify_migration.py [--detailed]

Options:
    --detailed  Show detailed breakdown of all tier-model relationships
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List


async def verify_migration(detailed=False):
    """Run comprehensive migration verification"""

    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db")
    )

    print("\n" + "="*70)
    print("TIER MIGRATION VERIFICATION REPORT")
    print("="*70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    all_checks_passed = True

    try:
        # Check 1: Table exists
        print("✓ Checking if tier_model_access table exists...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'tier_model_access'
            )
        """)

        if table_exists:
            print("  ✅ tier_model_access table exists\n")
        else:
            print("  ❌ tier_model_access table NOT FOUND\n")
            all_checks_passed = False
            return

        # Check 2: Foreign keys
        print("✓ Checking foreign key constraints...")
        fks = await conn.fetch("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'tier_model_access'
        """)

        if len(fks) >= 2:
            print(f"  ✅ Found {len(fks)} foreign key constraints:")
            for fk in fks:
                print(f"    • {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        else:
            print(f"  ⚠️  Expected 2 foreign keys, found {len(fks)}")
            all_checks_passed = False
        print()

        # Check 3: Indexes
        print("✓ Checking indexes...")
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'tier_model_access'
            AND indexname NOT LIKE '%pkey'
        """)

        if len(indexes) >= 3:
            print(f"  ✅ Found {len(indexes)} performance indexes:")
            for idx in indexes:
                print(f"    • {idx['indexname']}")
        else:
            print(f"  ⚠️  Expected at least 3 indexes, found {len(indexes)}")
            all_checks_passed = False
        print()

        # Check 4: Data migration
        print("✓ Checking data migration...")

        total_models = await conn.fetchval("""
            SELECT COUNT(*) FROM model_access_control WHERE enabled = TRUE
        """)

        total_tiers = await conn.fetchval("""
            SELECT COUNT(*) FROM subscription_tiers WHERE is_active = TRUE
        """)

        total_associations = await conn.fetchval("""
            SELECT COUNT(*) FROM tier_model_access
        """)

        models_with_assoc = await conn.fetchval("""
            SELECT COUNT(DISTINCT model_id) FROM tier_model_access
        """)

        print(f"  • Total active models: {total_models}")
        print(f"  • Total active tiers: {total_tiers}")
        print(f"  • Total associations created: {total_associations}")
        print(f"  • Models with associations: {models_with_assoc}")

        if total_associations > 0:
            coverage = (models_with_assoc / total_models * 100) if total_models > 0 else 0
            print(f"  • Coverage: {coverage:.1f}% of models have tier associations")

            if coverage >= 80:
                print("  ✅ Good coverage of tier associations")
            elif coverage >= 50:
                print("  ⚠️  Moderate coverage - review tier_access data")
                all_checks_passed = False
            else:
                print("  ❌ Low coverage - migration may have issues")
                all_checks_passed = False
        else:
            print("  ❌ No associations created - migration failed")
            all_checks_passed = False
        print()

        # Check 5: Tier breakdown
        print("✓ Checking tier-model distribution...")

        tier_stats = await conn.fetch("""
            SELECT
                st.tier_code,
                st.tier_name,
                COUNT(tma.model_id) AS model_count,
                ROUND(AVG(tma.markup_multiplier)::numeric, 2) AS avg_markup
            FROM subscription_tiers st
            LEFT JOIN tier_model_access tma ON st.id = tma.tier_id AND tma.enabled = TRUE
            WHERE st.is_active = TRUE
            GROUP BY st.tier_code, st.tier_name, st.sort_order
            ORDER BY st.sort_order, st.tier_code
        """)

        print(f"  {'Tier Code':<20} {'Model Count':<15} {'Avg Markup':<10}")
        print(f"  {'-'*20} {'-'*15} {'-'*10}")
        for tier in tier_stats:
            print(f"  {tier['tier_code']:<20} {tier['model_count']:<15} {tier['avg_markup'] or 'N/A':<10}")

        tiers_with_models = sum(1 for t in tier_stats if t['model_count'] > 0)
        if tiers_with_models == len(tier_stats):
            print(f"\n  ✅ All {len(tier_stats)} tiers have model associations")
        else:
            print(f"\n  ⚠️  Only {tiers_with_models}/{len(tier_stats)} tiers have models")
            all_checks_passed = False
        print()

        # Check 6: View and functions
        print("✓ Checking compatibility layer...")

        view_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views
                WHERE table_name = 'v_model_tier_access'
            )
        """)

        if view_exists:
            print("  ✅ Compatibility view 'v_model_tier_access' exists")

            view_count = await conn.fetchval("SELECT COUNT(*) FROM v_model_tier_access")
            print(f"    • View returns {view_count} rows")
        else:
            print("  ❌ Compatibility view NOT FOUND")
            all_checks_passed = False

        # Check functions
        functions = ['get_models_for_tier', 'is_model_available_for_tier']
        for func in functions:
            func_exists = await conn.fetchval("""
                SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = $1)
            """, func)

            if func_exists:
                print(f"  ✅ Function '{func}' exists")
            else:
                print(f"  ❌ Function '{func}' NOT FOUND")
                all_checks_passed = False
        print()

        # Check 7: Performance test
        print("✓ Running performance test...")

        import time
        start = time.time()

        test_results = await conn.fetch("""
            SELECT
                model_id,
                model_identifier,
                provider,
                tier_code,
                markup_multiplier
            FROM v_model_tier_access
            LIMIT 100
        """)

        elapsed = (time.time() - start) * 1000  # Convert to ms

        if elapsed < 50:
            print(f"  ✅ Query completed in {elapsed:.2f}ms (excellent)")
        elif elapsed < 100:
            print(f"  ✅ Query completed in {elapsed:.2f}ms (good)")
        elif elapsed < 200:
            print(f"  ⚠️  Query completed in {elapsed:.2f}ms (acceptable)")
        else:
            print(f"  ⚠️  Query completed in {elapsed:.2f}ms (slow, check indexes)")
            all_checks_passed = False
        print()

        # Check 8: Data integrity
        print("✓ Checking data integrity...")

        # Check for orphaned records
        orphaned_tiers = await conn.fetchval("""
            SELECT COUNT(*)
            FROM tier_model_access tma
            LEFT JOIN subscription_tiers st ON tma.tier_id = st.id
            WHERE st.id IS NULL
        """)

        orphaned_models = await conn.fetchval("""
            SELECT COUNT(*)
            FROM tier_model_access tma
            LEFT JOIN model_access_control m ON tma.model_id = m.id
            WHERE m.id IS NULL
        """)

        if orphaned_tiers == 0 and orphaned_models == 0:
            print("  ✅ No orphaned records found (referential integrity intact)")
        else:
            print(f"  ❌ Found {orphaned_tiers} orphaned tier refs, {orphaned_models} orphaned model refs")
            all_checks_passed = False

        # Check for duplicate associations
        duplicates = await conn.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT tier_id, model_id, COUNT(*)
                FROM tier_model_access
                GROUP BY tier_id, model_id
                HAVING COUNT(*) > 1
            ) AS dups
        """)

        if duplicates == 0:
            print("  ✅ No duplicate tier-model associations")
        else:
            print(f"  ❌ Found {duplicates} duplicate associations")
            all_checks_passed = False
        print()

        # Detailed breakdown (if requested)
        if detailed:
            print("="*70)
            print("DETAILED TIER-MODEL BREAKDOWN")
            print("="*70 + "\n")

            for tier in tier_stats:
                if tier['model_count'] > 0:
                    print(f"\n{tier['tier_name']} ({tier['tier_code']}):")
                    print(f"  Total models: {tier['model_count']}")

                    providers = await conn.fetch("""
                        SELECT
                            m.provider,
                            COUNT(*) AS count
                        FROM tier_model_access tma
                        JOIN model_access_control m ON tma.model_id = m.id
                        JOIN subscription_tiers st ON tma.tier_id = st.id
                        WHERE st.tier_code = $1 AND tma.enabled = TRUE
                        GROUP BY m.provider
                        ORDER BY count DESC
                    """, tier['tier_code'])

                    print("  Providers:")
                    for prov in providers:
                        print(f"    • {prov['provider']}: {prov['count']} models")

        # Final summary
        print("\n" + "="*70)
        if all_checks_passed:
            print("✅ ALL CHECKS PASSED - Migration successful!")
        else:
            print("⚠️  SOME CHECKS FAILED - Review issues above")
        print("="*70 + "\n")

    finally:
        await conn.close()

    return all_checks_passed


async def main():
    parser = argparse.ArgumentParser(description='Verify tier migration')
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    args = parser.parse_args()

    try:
        success = await verify_migration(detailed=args.detailed)
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
