#!/usr/bin/env python3
"""
Rate Limiting Integration Script

This script modifies server.py to add rate limiting functionality.
It creates a backup before making changes.

Usage:
    python scripts/integrate_rate_limiting.py [--dry-run]

Options:
    --dry-run    Show changes without applying them
"""

import sys
import re
import shutil
from pathlib import Path
from datetime import datetime


def backup_file(filepath: Path) -> Path:
    """Create a backup of the file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}.backup.{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path


def add_import_statements(content: str) -> str:
    """Add rate limiting imports"""

    # Find the line after csrf_protection imports
    import_pattern = r"(from csrf_protection import.*\n)"

    rate_limit_import = '''
# Rate limiting
try:
    from rate_limiter import rate_limiter, rate_limit, check_rate_limit_manual, RateLimitMiddleware
    RATE_LIMITING_ENABLED = True
except ImportError:
    print("Rate limiting not available")
    RATE_LIMITING_ENABLED = False
    rate_limit = lambda category: lambda func: func  # Dummy decorator
'''

    # Check if already added
    if "from rate_limiter import" in content:
        print("Rate limiting imports already present")
        return content

    content = re.sub(import_pattern, r"\1" + rate_limit_import, content)
    print("Added rate limiting imports")
    return content


def add_startup_handlers(content: str) -> str:
    """Add startup and shutdown event handlers"""

    # Check if startup handler already exists
    if '@app.on_event("startup")' in content or '@app.on_event("shutdown")' in content:
        print("Startup/shutdown handlers already present")
        return content

    # Find the line after app initialization and middleware setup
    # Look for "logger.info(f" after CSRF setup
    pattern = r'(logger\.info\(f"CSRF Protection:.*\n)'

    startup_code = '''
# Initialize rate limiter on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    if RATE_LIMITING_ENABLED:
        try:
            await rate_limiter.initialize()
            logger.info("Rate limiter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            if not rate_limiter.config.fail_open:
                raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if RATE_LIMITING_ENABLED:
        await rate_limiter.close()
        logger.info("Rate limiter closed")

'''

    content = re.sub(pattern, r"\1\n" + startup_code, content)
    print("Added startup/shutdown handlers")
    return content


def add_rate_limit_decorators(content: str, dry_run: bool = False) -> str:
    """Add rate limit decorators to endpoints"""

    # Patterns for different endpoint categories
    patterns = {
        "auth": [
            r'(@app\.post\("/api/v1/auth/login"\))',
            r'(@app\.post\("/api/v1/auth/logout"\))',
            r'(@app\.post\("/api/v1/auth/change-password"\))',
            r'(@app\.get\("/auth/login"\))',
            r'(@app\.post\("/auth/direct-login"\))',
            r'(@app\.get\("/auth/callback"\))',
        ],
        "admin": [
            r'(@app\.get\("/api/v1/users"\))',
            r'(@app\.post\("/api/v1/users"\))',
            r'(@app\.put\("/api/v1/users/\{user_id\}"\))',
            r'(@app\.delete\("/api/v1/users/\{user_id\}"\))',
            r'(@app\.get\("/api/v1/api-keys"\))',
            r'(@app\.post\("/api/v1/api-keys"\))',
            r'(@app\.delete\("/api/v1/api-keys/\{key_id\}"\))',
            r'(@app\.get\("/api/v1/sso/users"\))',
            r'(@app\.post\("/api/v1/sso/users"\))',
            r'(@app\.put\("/api/v1/sso/users/\{user_id\}"\))',
            r'(@app\.delete\("/api/v1/sso/users/\{user_id\}"\))',
            r'(@app\.post\("/api/v1/sso/users/\{user_id\}/set-password"\))',
        ],
        "write": [
            r'(@app\.post\("/api/v1/services/\{container_name\}/action"\))',
            r'(@app\.post\("/api/v1/models/download"\))',
            r'(@app\.delete\("/api/v1/models/\{model_id:path\}"\))',
            r'(@app\.post\("/api/v1/models/active"\))',
            r'(@app\.put\("/api/v1/models/\{model_id:path\}/config"\))',
            r'(@app\.put\("/api/v1/settings"\))',
            r'(@app\.post\("/api/v1/landing/config"\))',
            r'(@app\.post\("/api/v1/extensions/install"\))',
            r'(@app\.delete\("/api/v1/extensions/\{extension_id\}"\))',
            r'(@app\.post\("/api/v1/backup/create"\))',
            r'(@app\.post\("/api/v1/backup/\{backup_id\}/restore"\))',
        ],
        "read": [
            r'(@app\.get\("/api/v1/services"\))',
            r'(@app\.get\("/api/v1/services/\{container_name\}/logs"\))',
            r'(@app\.get\("/api/v1/services/\{container_name\}/stats"\))',
            r'(@app\.get\("/api/v1/models"\))',
            r'(@app\.get\("/api/v1/models/installed"\))',
            r'(@app\.get\("/api/v1/extensions"\))',
            r'(@app\.get\("/api/v1/storage"\))',
            r'(@app\.get\("/api/v1/logs/sources"\))',
            r'(@app\.get\("/api/v1/settings"\))',
            r'(@app\.get\("/api/v1/landing/config"\))',
        ],
    }

    changes_made = 0

    for category, endpoint_patterns in patterns.items():
        decorator = f'@rate_limit("{category}")'

        for pattern in endpoint_patterns:
            # Check if decorator already exists
            full_pattern = f'{decorator}\\s*\\n\\s*{pattern}'
            if re.search(full_pattern, content):
                continue

            # Add decorator before endpoint
            replacement = f'{decorator}\n\\1'
            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                changes_made += 1
                content = new_content
                if dry_run:
                    print(f"Would add {decorator} to endpoint matching {pattern}")

    if changes_made > 0:
        print(f"Added {changes_made} rate limit decorators")
    else:
        print("No new rate limit decorators added (may already exist)")

    return content


def main():
    dry_run = "--dry-run" in sys.argv

    # Find server.py
    server_path = Path(__file__).parent.parent / "server.py"

    if not server_path.exists():
        print(f"Error: server.py not found at {server_path}")
        sys.exit(1)

    print(f"Processing {server_path}")

    if dry_run:
        print("\n=== DRY RUN MODE - No changes will be made ===\n")

    # Read content
    with open(server_path, "r") as f:
        content = f.read()

    # Create backup (even in dry run)
    if not dry_run:
        backup_file(server_path)

    # Apply modifications
    print("\n1. Adding import statements...")
    content = add_import_statements(content)

    print("\n2. Adding startup handlers...")
    content = add_startup_handlers(content)

    print("\n3. Adding rate limit decorators...")
    content = add_rate_limit_decorators(content, dry_run)

    # Write changes
    if not dry_run:
        with open(server_path, "w") as f:
            f.write(content)
        print(f"\n✓ Successfully integrated rate limiting into {server_path}")
        print("\nNext steps:")
        print("1. Review the changes")
        print("2. Copy .env.ratelimit to your deployment directory")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Restart the server")
        print("5. Test rate limiting with the examples in docs/RATE_LIMITING_INTEGRATION.md")
    else:
        print("\n=== DRY RUN COMPLETE - No changes made ===")
        print("\nRun without --dry-run to apply changes")


if __name__ == "__main__":
    main()
