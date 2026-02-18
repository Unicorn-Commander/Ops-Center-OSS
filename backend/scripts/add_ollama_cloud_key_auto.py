#!/usr/bin/env python3
"""
Add Ollama Cloud API Key as System Key (Non-Interactive)

This script:
1. Creates 'ollama-cloud' provider in llm_providers table if not exists
2. Encrypts the provided API key using Fernet
3. Stores the encrypted key in the database
4. Verifies the key was stored correctly

Usage:
    python3 add_ollama_cloud_key_auto.py
"""

import asyncio
import asyncpg
import os
import sys
import json
from cryptography.fernet import Fernet
from datetime import datetime

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "unicorn-postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "unicorn")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "unicorn")
POSTGRES_DB = os.getenv("POSTGRES_DB", "unicorn_db")

BYOK_ENCRYPTION_KEY = os.getenv("BYOK_ENCRYPTION_KEY")

# Ollama Cloud Configuration
OLLAMA_CLOUD_API_KEY = "your-ollama-cloud-api-key"

PROVIDER_CONFIG = {
    "name": "ollama-cloud",
    "type": "ollama-cloud",
    "enabled": True,
    "priority": 50,
    "config": {
        "base_url": "https://api.ollama.ai/v1",
        "model_prefixes": ["ollama-cloud/"],
        "description": "Ollama Cloud - AI models from the Ollama platform"
    }
}


async def main():
    """Main execution flow"""
    print("\n" + "=" * 70)
    print("OLLAMA CLOUD API KEY SETUP (AUTO)")
    print("=" * 70)

    if not BYOK_ENCRYPTION_KEY:
        print("\n✗ BYOK_ENCRYPTION_KEY environment variable not set!")
        sys.exit(1)

    # Initialize encryption
    cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())

    def mask_key(api_key: str) -> str:
        """Mask API key for display"""
        if len(api_key) < 12:
            return "****"
        return f"{api_key[:7]}...{api_key[-4:]}"

    print(f"\nAPI Key (masked): {mask_key(OLLAMA_CLOUD_API_KEY)}")
    print(f"Database: {POSTGRES_DB}@{POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"Encryption: BYOK_ENCRYPTION_KEY (SET)")

    # Connect to database
    print(f"\nConnecting to PostgreSQL...")
    db_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        min_size=1,
        max_size=5
    )
    print("✓ Database connection established")

    try:
        async with db_pool.acquire() as conn:
            # Check if provider exists
            existing = await conn.fetchrow(
                """
                SELECT id, name, type, enabled, api_key_encrypted
                FROM llm_providers
                WHERE name = $1 OR type = $1
                """,
                "ollama-cloud"
            )

            if existing:
                print(f"\n⚠️  Provider 'ollama-cloud' already exists:")
                print(f"   ID: {existing['id']}")
                print(f"   Name: {existing['name']}")
                print(f"   Has Key: {bool(existing['api_key_encrypted'])}")
                print("\nUpdating existing provider...")

                provider_id = str(existing['id'])

                # Update provider
                await conn.execute(
                    """
                    UPDATE llm_providers
                    SET type = $1,
                        enabled = $2,
                        priority = $3,
                        config = $4,
                        updated_at = $5,
                        api_key_source = $6
                    WHERE id = $7
                    """,
                    PROVIDER_CONFIG["type"],
                    PROVIDER_CONFIG["enabled"],
                    PROVIDER_CONFIG["priority"],
                    json.dumps(PROVIDER_CONFIG["config"]),  # Convert to JSON string
                    datetime.utcnow(),
                    "database",
                    provider_id
                )
                print(f"✓ Provider updated: {PROVIDER_CONFIG['name']}")

            # Encrypt API key FIRST (before insert/update)
            print(f"\nEncrypting API key...")
            encrypted_key = cipher.encrypt(OLLAMA_CLOUD_API_KEY.encode()).decode()
            print(f"✓ API key encrypted (preview: {mask_key(OLLAMA_CLOUD_API_KEY)})")
            print(f"  Encrypted length: {len(encrypted_key)} bytes")

            if not existing:
                print(f"\nCreating new provider: {PROVIDER_CONFIG['name']}...")

                # Create provider with encrypted key
                row = await conn.fetchrow(
                    """
                    INSERT INTO llm_providers (
                        name, type, api_key_encrypted, encrypted_api_key,
                        enabled, priority, config,
                        created_at, updated_at,
                        health_status, api_key_source,
                        api_key_updated_at, api_key_test_status
                    )
                    VALUES ($1, $2, $3, $3, $4, $5, $6, $7, $7, $8, $9, $7, $10)
                    RETURNING id, name
                    """,
                    PROVIDER_CONFIG["name"],
                    PROVIDER_CONFIG["type"],
                    encrypted_key,  # api_key_encrypted
                    PROVIDER_CONFIG["enabled"],
                    PROVIDER_CONFIG["priority"],
                    json.dumps(PROVIDER_CONFIG["config"]),
                    datetime.utcnow(),
                    "unknown",
                    "database",
                    "pending"
                )

                provider_id = str(row["id"])
                print(f"✓ Provider created: {row['name']} (ID: {provider_id})")

            else:
                # Update encrypted key for existing provider
                await conn.execute(
                    """
                    UPDATE llm_providers
                    SET api_key_encrypted = $1,
                        encrypted_api_key = $1,
                        api_key_source = 'database',
                        api_key_updated_at = $2,
                        api_key_last_tested = NULL,
                        api_key_test_status = 'pending',
                        updated_at = $2
                    WHERE id = $3
                    """,
                    encrypted_key,
                    datetime.utcnow(),
                    provider_id
                )
                print(f"✓ API key updated in database")

            # Verify key
            print(f"\nVerifying stored key...")
            row = await conn.fetchrow(
                """
                SELECT api_key_encrypted, name
                FROM llm_providers
                WHERE id = $1
                """,
                provider_id
            )

            if not row or not row["api_key_encrypted"]:
                print("✗ No encrypted key found!")
                sys.exit(1)

            decrypted = cipher.decrypt(row["api_key_encrypted"].encode()).decode()

            if decrypted == OLLAMA_CLOUD_API_KEY:
                print(f"✓ Key verification successful for: {row['name']}")
                print(f"  Decrypted key matches original: {mask_key(decrypted)}")
            else:
                print(f"✗ Key mismatch!")
                sys.exit(1)

            # Show summary
            print("\n" + "=" * 70)
            print("OLLAMA-CLOUD PROVIDER SUMMARY")
            print("=" * 70)

            rows = await conn.fetch(
                """
                SELECT id, name, type, enabled,
                       api_key_encrypted IS NOT NULL as has_key,
                       api_key_source, api_key_test_status,
                       health_status, priority, config
                FROM llm_providers
                WHERE name ILIKE '%ollama%' OR type ILIKE '%ollama%'
                ORDER BY name
                """
            )

            for row in rows:
                print(f"\nProvider: {row['name']}")
                print(f"  ID: {row['id']}")
                print(f"  Type: {row['type']}")
                print(f"  Enabled: {row['enabled']}")
                print(f"  Has Key: {row['has_key']}")
                print(f"  Key Source: {row['api_key_source']}")
                print(f"  Test Status: {row['api_key_test_status']}")
                print(f"  Health: {row['health_status']}")
                print(f"  Priority: {row['priority']}")

            print("\n" + "=" * 70)
            print("✓ OLLAMA-CLOUD API KEY SUCCESSFULLY ADDED")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Test the API key via Ops-Center UI")
            print("   URL: https://unicorncommander.ai/admin/llm/providers")
            print("2. Add Ollama Cloud models to the model catalog")
            print("3. Configure routing rules if needed")
            print("\nAPI Endpoints:")
            print("  GET  /api/v1/llm/providers/keys")
            print("  POST /api/v1/llm/providers/keys/test")

    finally:
        await db_pool.close()
        print("\n✓ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
