#!/usr/bin/env python3
"""
Generate BYOK Encryption Key for Ops-Center

This script generates a Fernet encryption key for encrypting BYOK API keys
and adds it to .env.auth if not already present.

Usage:
    python3 generate_encryption_key.py

Warning:
    DO NOT CHANGE the encryption key after users have added API keys!
    Changing the key will make all encrypted keys unreadable.

Author: Ops-Center Backend Team
Date: October 20, 2025
"""

import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

def generate_key():
    """Generate a new Fernet encryption key."""
    key = Fernet.generate_key()
    return key.decode('utf-8')

def check_existing_key(env_file_path):
    """Check if BYOK_ENCRYPTION_KEY already exists in .env.auth."""
    if not os.path.exists(env_file_path):
        return None

    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('BYOK_ENCRYPTION_KEY='):
                # Extract the value
                parts = line.split('=', 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    if value:
                        return value
    return None

def add_key_to_env(env_file_path, key):
    """Add BYOK_ENCRYPTION_KEY to .env.auth."""
    # Read existing content
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Check if key already exists (even if empty)
    key_exists = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('BYOK_ENCRYPTION_KEY='):
            # Replace existing line
            new_lines.append(f'BYOK_ENCRYPTION_KEY={key}\n')
            key_exists = True
        else:
            new_lines.append(line)

    # Add key if it doesn't exist
    if not key_exists:
        # Find the section where BYOK_ENCRYPTION_KEY should go
        # (after BYOK comment block)
        insert_index = len(new_lines)

        for i, line in enumerate(new_lines):
            if 'BYOK_ENCRYPTION_KEY' in line or 'BYOK Encryption Key' in line:
                insert_index = i + 1
                break

        new_lines.insert(insert_index, f'BYOK_ENCRYPTION_KEY={key}\n')

    # Write back
    with open(env_file_path, 'w') as f:
        f.writelines(new_lines)

def main():
    """Main function."""
    print("=" * 70)
    print("BYOK Encryption Key Generator")
    print("=" * 70)

    # Determine .env.auth path
    # Script is in backend/scripts/, .env.auth is in ops-center root
    script_dir = Path(__file__).parent
    ops_center_dir = script_dir.parent.parent
    env_file = ops_center_dir / '.env.auth'

    print(f"\nEnvironment file: {env_file}")

    # Check if key already exists
    existing_key = check_existing_key(env_file)

    if existing_key:
        print("\n✅ BYOK_ENCRYPTION_KEY already exists in .env.auth")
        print(f"\nKey: {existing_key}")
        print("\n⚠️  WARNING: DO NOT CHANGE this key if users have already added API keys!")
        print("   Changing the key will make all encrypted keys unreadable.")

        # Ask if user wants to regenerate
        response = input("\nDo you want to generate a NEW key? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n✅ Keeping existing key. No changes made.")
            return 0

        print("\n⚠️  Generating NEW key - all existing encrypted keys will be invalid!")

    # Generate new key
    print("\n🔑 Generating new Fernet encryption key...")
    new_key = generate_key()

    print(f"\nGenerated key: {new_key}")

    # Add to .env.auth
    print(f"\n📝 Adding key to {env_file}...")
    add_key_to_env(env_file, new_key)

    print("\n✅ Success! BYOK_ENCRYPTION_KEY added to .env.auth")

    # Verify
    verify_key = check_existing_key(env_file)
    if verify_key == new_key:
        print("✅ Verification passed - key correctly written to file")
    else:
        print("❌ Verification failed - key mismatch!")
        return 1

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Restart ops-center service to load the new key:")
    print("   docker restart ops-center-direct")
    print("")
    print("2. Test the integration:")
    print("   python3 backend/scripts/test_provider_integration.py")
    print("")
    print("3. API keys can now be securely encrypted/decrypted")
    print("=" * 70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
