#!/usr/bin/env python3
"""
Test Ollama Cloud API Key Retrieval and Decryption

This script verifies:
1. Key is stored in database
2. Key can be decrypted
3. Decrypted key matches original
"""

import asyncio
import asyncpg
import os
from cryptography.fernet import Fernet

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "unicorn")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
POSTGRES_DB = os.getenv("POSTGRES_DB", "unicorn_db")

BYOK_ENCRYPTION_KEY = os.getenv("BYOK_ENCRYPTION_KEY")

# Expected key
EXPECTED_KEY = "your-ollama-cloud-api-key"


async def main():
    """Test key retrieval and decryption"""
    print("\n" + "=" * 70)
    print("OLLAMA CLOUD API KEY TEST")
    print("=" * 70)

    if not BYOK_ENCRYPTION_KEY:
        print("\n✗ BYOK_ENCRYPTION_KEY not set!")
        return False

    cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())

    def mask_key(key: str) -> str:
        """Mask key for display"""
        if len(key) < 12:
            return "****"
        return f"{key[:7]}...{key[-4:]}"

    # Connect to database
    print(f"\nConnecting to {POSTGRES_DB}@{POSTGRES_HOST}...")
    db_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )

    try:
        async with db_pool.acquire() as conn:
            # Retrieve provider
            row = await conn.fetchrow(
                """
                SELECT id, name, type, enabled,
                       api_key_encrypted, encrypted_api_key,
                       api_key_source, api_key_test_status
                FROM llm_providers
                WHERE name = 'ollama-cloud'
                """
            )

            if not row:
                print("✗ Provider 'ollama-cloud' not found!")
                return False

            print(f"\n✓ Provider found:")
            print(f"  ID: {row['id']}")
            print(f"  Name: {row['name']}")
            print(f"  Type: {row['type']}")
            print(f"  Enabled: {row['enabled']}")
            print(f"  Key Source: {row['api_key_source']}")
            print(f"  Test Status: {row['api_key_test_status']}")

            # Test decryption
            print(f"\nTesting decryption...")

            if not row['api_key_encrypted']:
                print("✗ No encrypted key found!")
                return False

            print(f"  Encrypted key length: {len(row['api_key_encrypted'])} bytes")

            decrypted = cipher.decrypt(row['api_key_encrypted'].encode()).decode()
            print(f"✓ Decryption successful")
            print(f"  Decrypted key: {mask_key(decrypted)}")

            # Verify match
            if decrypted == EXPECTED_KEY:
                print(f"\n✓ KEY VERIFICATION SUCCESSFUL")
                print(f"  Decrypted key matches expected value")
                print(f"  Expected: {mask_key(EXPECTED_KEY)}")
                print(f"  Got:      {mask_key(decrypted)}")
                return True
            else:
                print(f"\n✗ KEY MISMATCH!")
                print(f"  Expected: {mask_key(EXPECTED_KEY)}")
                print(f"  Got:      {mask_key(decrypted)}")
                return False

    finally:
        await db_pool.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    print("\n" + "=" * 70)
    if success:
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nThe Ollama Cloud API key is properly encrypted and stored.")
        print("You can now use it via the LiteLLM proxy.")
        exit(0)
    else:
        print("✗ TESTS FAILED")
        print("=" * 70)
        exit(1)
