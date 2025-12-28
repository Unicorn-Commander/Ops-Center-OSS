"""Database Migration: Create Audit Logs Table

This migration creates the audit_logs table and necessary indexes.
"""

import sqlite3
import sys
import os
from pathlib import Path


def migrate(db_path: str = "data/ops_center.db"):
    """Apply migration to create audit_logs table"""
    print(f"Applying migration: Create audit_logs table")
    print(f"Database: {db_path}")

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                ip_address TEXT,
                user_agent TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                result TEXT NOT NULL,
                error_message TEXT,
                metadata TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created audit_logs table")

        # Create indexes for performance
        indexes = [
            ("idx_audit_timestamp", "timestamp"),
            ("idx_audit_user_id", "user_id"),
            ("idx_audit_username", "username"),
            ("idx_audit_action", "action"),
            ("idx_audit_result", "result"),
            ("idx_audit_ip_address", "ip_address"),
            ("idx_audit_resource", "resource_type, resource_id"),
        ]

        for idx_name, idx_columns in indexes:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON audit_logs({idx_columns})
            """)
            print(f"✓ Created index: {idx_name}")

        # Create migration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Record this migration
        cursor.execute("""
            INSERT OR IGNORE INTO migrations (migration_name)
            VALUES (?)
        """, ("001_create_audit_logs",))

        conn.commit()
        print("✓ Migration completed successfully")

        # Show table info
        cursor.execute("PRAGMA table_info(audit_logs)")
        columns = cursor.fetchall()
        print("\nAudit logs table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        return False

    finally:
        conn.close()


def rollback(db_path: str = "data/ops_center.db"):
    """Rollback migration (drop audit_logs table)"""
    print(f"Rolling back migration: Drop audit_logs table")
    print(f"Database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Drop indexes
        indexes = [
            "idx_audit_timestamp",
            "idx_audit_user_id",
            "idx_audit_username",
            "idx_audit_action",
            "idx_audit_result",
            "idx_audit_ip_address",
            "idx_audit_resource"
        ]

        for idx_name in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
            print(f"✓ Dropped index: {idx_name}")

        # Drop table
        cursor.execute("DROP TABLE IF EXISTS audit_logs")
        print("✓ Dropped audit_logs table")

        # Remove migration record
        cursor.execute("""
            DELETE FROM migrations
            WHERE migration_name = ?
        """, ("001_create_audit_logs",))

        conn.commit()
        print("✓ Rollback completed successfully")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Rollback failed: {e}", file=sys.stderr)
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit logs migration")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration"
    )
    parser.add_argument(
        "--db",
        default="data/ops_center.db",
        help="Path to database file"
    )

    args = parser.parse_args()

    if args.rollback:
        success = rollback(args.db)
    else:
        success = migrate(args.db)

    sys.exit(0 if success else 1)
