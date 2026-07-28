#!/usr/bin/env python3
"""Initialize audit logging database

This script initializes the audit logging database tables.
It should be run with appropriate permissions.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit_logger import AuditLogger

def main():
    """Initialize the audit logging database"""
    print("Initializing audit logging database...")

    try:
        # Create audit logger instance (will initialize database)
        audit_logger = AuditLogger(
            db_path="data/ops_center.db",
            log_dir="/var/log/ops-center",
            enable_file_logging=True,
            enable_db_logging=True
        )

        print("✓ Audit logging database initialized successfully")
        print("  - Database: data/ops_center.db")
        print("  - Log directory: /var/log/ops-center")
        print("  - Table created: audit_logs")
        print("  - Indexes created for performance")

        return 0

    except Exception as e:
        print(f"✗ Failed to initialize audit logging: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
