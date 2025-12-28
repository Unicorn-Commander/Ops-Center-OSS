#!/usr/bin/env python3
"""
Migration Runner for UC-Cloud Ops-Center

This script applies database migrations safely with idempotency checks.
It connects to PostgreSQL and applies migration 002 (system API keys).

Usage:
    python3 run_migration.py                    # Apply migration 002
    python3 run_migration.py --rollback         # Rollback migration 002
    python3 run_migration.py --check            # Check migration status

Author: Backend API Developer
Date: October 27, 2025
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================================
# Configuration
# ============================================================================

# Database connection from environment
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'unicorn'),
    'password': os.getenv('POSTGRES_PASSWORD', 'unicorn'),
    'database': os.getenv('POSTGRES_DB', 'unicorn_db')
}

# Migration file paths
MIGRATIONS_DIR = Path(__file__).parent / 'migrations'
MIGRATION_002 = MIGRATIONS_DIR / '002_add_system_api_keys.sql'
MIGRATION_002_ROLLBACK = MIGRATIONS_DIR / '002_add_system_api_keys_rollback.sql'


# ============================================================================
# Helper Functions
# ============================================================================

def print_header(message: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}", file=sys.stderr)


def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


# ============================================================================
# Database Operations
# ============================================================================

async def get_db_connection():
    """
    Create PostgreSQL connection

    Returns:
        asyncpg.Connection: Database connection

    Raises:
        Exception: If connection fails
    """
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print_success(f"Connected to database: {DB_CONFIG['database']}")
        return conn
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        raise


async def check_migration_status(conn: asyncpg.Connection) -> dict:
    """
    Check if migration 002 has been applied

    Args:
        conn: Database connection

    Returns:
        dict: Status of each column
    """
    print_info("Checking migration status...")

    # Check if columns exist
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'llm_providers'
        AND column_name IN (
            'encrypted_api_key',
            'api_key_source',
            'api_key_updated_at',
            'api_key_last_tested',
            'api_key_test_status'
        )
        ORDER BY column_name;
    """

    rows = await conn.fetch(query)

    expected_columns = {
        'encrypted_api_key',
        'api_key_source',
        'api_key_updated_at',
        'api_key_last_tested',
        'api_key_test_status'
    }

    existing_columns = {row['column_name'] for row in rows}
    missing_columns = expected_columns - existing_columns

    status = {
        'is_applied': len(missing_columns) == 0,
        'existing_columns': list(existing_columns),
        'missing_columns': list(missing_columns),
        'column_details': [dict(row) for row in rows]
    }

    return status


async def apply_migration(conn: asyncpg.Connection) -> bool:
    """
    Apply migration 002 to add system API key columns

    Args:
        conn: Database connection

    Returns:
        bool: True if successful, False otherwise
    """
    print_header("Applying Migration 002: System API Key Storage")

    # Check if migration file exists
    if not MIGRATION_002.exists():
        print_error(f"Migration file not found: {MIGRATION_002}")
        return False

    try:
        # Read migration SQL
        migration_sql = MIGRATION_002.read_text()
        print_info(f"Loaded migration from: {MIGRATION_002}")

        # Execute migration
        print_info("Executing migration SQL...")
        await conn.execute(migration_sql)

        print_success("Migration 002 applied successfully!")
        return True

    except Exception as e:
        print_error(f"Migration failed: {e}")
        return False


async def rollback_migration(conn: asyncpg.Connection) -> bool:
    """
    Rollback migration 002 to remove system API key columns

    Args:
        conn: Database connection

    Returns:
        bool: True if successful, False otherwise
    """
    print_header("Rolling Back Migration 002")

    # Check if rollback file exists
    if not MIGRATION_002_ROLLBACK.exists():
        print_error(f"Rollback file not found: {MIGRATION_002_ROLLBACK}")
        return False

    try:
        # Read rollback SQL
        rollback_sql = MIGRATION_002_ROLLBACK.read_text()
        print_info(f"Loaded rollback from: {MIGRATION_002_ROLLBACK}")

        # Execute rollback
        print_warning("Executing rollback SQL (this will delete system API keys)...")
        await conn.execute(rollback_sql)

        print_success("Rollback completed successfully!")
        return True

    except Exception as e:
        print_error(f"Rollback failed: {e}")
        return False


async def display_migration_status(conn: asyncpg.Connection):
    """Display current migration status"""
    status = await check_migration_status(conn)

    print_header("Migration 002 Status")

    if status['is_applied']:
        print_success("Migration 002 is APPLIED")
        print("\nExisting columns:")
        for col in status['column_details']:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
    else:
        print_warning("Migration 002 is NOT APPLIED")
        print(f"\nMissing columns: {', '.join(status['missing_columns'])}")

        if status['existing_columns']:
            print(f"\nPartially applied (existing): {', '.join(status['existing_columns'])}")


async def verify_migration(conn: asyncpg.Connection):
    """Verify migration was applied correctly"""
    print_header("Verifying Migration")

    # Check table exists
    table_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'llm_providers'
        );
    """)

    if not table_exists:
        print_error("Table 'llm_providers' does not exist!")
        return False

    print_success("Table 'llm_providers' exists")

    # Check all columns
    status = await check_migration_status(conn)

    if status['is_applied']:
        print_success("All migration 002 columns exist")

        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'llm_providers'
            AND indexname IN (
                'idx_llm_providers_api_key_source',
                'idx_llm_providers_has_db_key'
            );
        """)

        index_names = [idx['indexname'] for idx in indexes]

        if 'idx_llm_providers_api_key_source' in index_names:
            print_success("Index 'idx_llm_providers_api_key_source' exists")
        else:
            print_warning("Index 'idx_llm_providers_api_key_source' missing")

        if 'idx_llm_providers_has_db_key' in index_names:
            print_success("Index 'idx_llm_providers_has_db_key' exists")
        else:
            print_warning("Index 'idx_llm_providers_has_db_key' missing")

        # Check row updates
        row_count = await conn.fetchval("""
            SELECT COUNT(*) FROM llm_providers
            WHERE api_key_source = 'environment';
        """)

        print_info(f"{row_count} provider(s) have api_key_source set to 'environment'")

        return True
    else:
        print_error(f"Missing columns: {', '.join(status['missing_columns'])}")
        return False


# ============================================================================
# Main Function
# ============================================================================

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Apply or rollback migration 002 for system API keys'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback migration 002 instead of applying it'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check migration status without applying'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force apply/rollback even if already applied/rolled back'
    )

    args = parser.parse_args()

    print_header(f"UC-Cloud Ops-Center Migration Runner")
    print(f"Migration: 002_add_system_api_keys.sql")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    try:
        conn = await get_db_connection()
    except Exception:
        return 1

    try:
        # Check current status
        status = await check_migration_status(conn)

        if args.check:
            # Just check status
            await display_migration_status(conn)
            return 0

        elif args.rollback:
            # Rollback migration
            if not status['is_applied'] and not args.force:
                print_warning("Migration 002 is not applied, nothing to rollback")
                print_info("Use --force to rollback anyway")
                return 0

            success = await rollback_migration(conn)
            if success:
                await verify_migration(conn)
                return 0
            return 1

        else:
            # Apply migration
            if status['is_applied'] and not args.force:
                print_warning("Migration 002 is already applied")
                print_info("Use --force to re-apply")
                await display_migration_status(conn)
                return 0

            success = await apply_migration(conn)
            if success:
                await verify_migration(conn)
                return 0
            return 1

    finally:
        await conn.close()
        print_info("Database connection closed")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
