#!/usr/bin/env python3
"""
Initialize OpenRouter API Key
Pre-populates the default OpenRouter key for testing
"""

import asyncio
import asyncpg
import sys
from cryptography.fernet import Fernet
import os

# Generate encryption key (this should match the one in your environment)
# For now, generate a new one - in production this should be from environment variable
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

async def initialize_openrouter_key():
    """Pre-populate OpenRouter API key"""

    # Database connection
    db_url = "postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db"

    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")

        # Check if any keys exist
        count = await conn.fetchval("SELECT COUNT(*) FROM llm_api_keys")
        print(f"📊 Existing API keys: {count}")

        if count == 0:
            # Encrypt the API key
            api_key = "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"
            encrypted_key = fernet.encrypt(api_key.encode()).decode()

            # Insert the key
            await conn.execute("""
                INSERT INTO llm_api_keys (
                    provider, key_name, encrypted_key,
                    use_for_ops_center, enabled,
                    created_by, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7
                )
            """,
                "openrouter",
                "Default OpenRouter Key",
                encrypted_key,
                True,  # use_for_ops_center
                True,  # enabled
                "system",
                '{"source": "pre-populated"}'
            )

            print("✅ OpenRouter key added successfully")

            # Get the key ID
            key_id = await conn.fetchval("""
                SELECT id FROM llm_api_keys
                WHERE provider = 'openrouter'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            # Set as active provider for chat
            await conn.execute("""
                INSERT INTO active_providers (purpose, provider_type, provider_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (purpose) DO UPDATE SET
                    provider_type = EXCLUDED.provider_type,
                    provider_id = EXCLUDED.provider_id
            """, "chat", "api_key", key_id)

            print(f"✅ Set as active chat provider (ID: {key_id})")
            print(f"\n⚠️  IMPORTANT: Save this encryption key to your environment:")
            print(f"BYOK_ENCRYPTION_KEY={ENCRYPTION_KEY.decode()}")

        else:
            print("ℹ️  API keys already exist - skipping initialization")

        # Close connection
        await conn.close()
        print("\n✅ Initialization complete")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(initialize_openrouter_key())
