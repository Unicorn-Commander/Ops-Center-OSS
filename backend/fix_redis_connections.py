#!/usr/bin/env python3
"""
Fix all Redis connection issues in Ops-Center backend

Replaces hardcoded 'unicorn-redis:6379' with correct 'unicorn-lago-redis:6379'
or environment variable lookups.
"""

import os
import re
import sys
from pathlib import Path

# Files to fix
FILES_TO_FIX = [
    "user_analytics.py",
    "white_label_api.py",
    "credit_deduction_middleware.py",
    "auth_dependencies.py",
    "model_admin_api.py",
    "litellm_routing_api.py",
    "integration_test_suite.py",
    "testing_lab_api.py",
]

BACKEND_DIR = Path(__file__).parent

# Correct Redis host (the actual container name)
CORRECT_REDIS_HOST = "unicorn-lago-redis"

def fix_redis_host_in_file(filepath: Path) -> bool:
    """Fix Redis host in a single file"""
    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        return False

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # Pattern 1: Hardcoded redis://unicorn-redis:6379
    pattern1 = r'redis://unicorn-redis:6379'
    if re.search(pattern1, content):
        content = re.sub(pattern1, f'redis://{CORRECT_REDIS_HOST}:6379', content)
        changes_made.append(f"Fixed hardcoded Redis URL")

    # Pattern 2: REDIS_HOST = "unicorn-redis"
    pattern2 = r'REDIS_HOST\s*=\s*["\']unicorn-redis["\']'
    if re.search(pattern2, content):
        content = re.sub(
            pattern2,
            f'REDIS_HOST = os.getenv("REDIS_HOST", "{CORRECT_REDIS_HOST}")',
            content
        )
        changes_made.append(f"Fixed REDIS_HOST variable")

    # Pattern 3: redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    pattern3 = r'os\.getenv\(["\']REDIS_HOST["\']\s*,\s*["\']unicorn-redis["\']\)'
    if re.search(pattern3, content):
        content = re.sub(
            pattern3,
            f'os.getenv("REDIS_HOST", "{CORRECT_REDIS_HOST}")',
            content
        )
        changes_made.append(f"Fixed getenv default value")

    if content != original_content:
        # Create backup
        backup_path = filepath.with_suffix('.py.backup')
        with open(backup_path, 'w') as f:
            f.write(original_content)

        # Write fixed content
        with open(filepath, 'w') as f:
            f.write(content)

        print(f"✅ Fixed {filepath.name}:")
        for change in changes_made:
            print(f"   - {change}")
        print(f"   - Backup saved: {backup_path.name}")
        return True
    else:
        print(f"ℹ️  No changes needed: {filepath.name}")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing Redis connections in Ops-Center backend\n")
    print(f"Replacing 'unicorn-redis' with '{CORRECT_REDIS_HOST}'\n")

    fixed_count = 0
    for filename in FILES_TO_FIX:
        filepath = BACKEND_DIR / filename
        if fix_redis_host_in_file(filepath):
            fixed_count += 1
        print()

    print(f"\n✨ Complete! Fixed {fixed_count} file(s)")
    print(f"\nNext steps:")
    print(f"1. Review changes in the modified files")
    print(f"2. Restart ops-center-direct: docker restart ops-center-direct")
    print(f"3. Test endpoints: curl http://localhost:8084/api/v1/analytics/users/engagement")

if __name__ == "__main__":
    main()
