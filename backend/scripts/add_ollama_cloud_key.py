#!/usr/bin/env python3
"""
Add Ollama Cloud API Key as System Key

This script:
1. Creates 'ollama-cloud' provider in llm_providers table if not exists
2. Encrypts the provided API key using Fernet
3. Stores the encrypted key in the database
4. Verifies the key was stored correctly

Usage:
    python3 add_ollama_cloud_key.py
"""

import asyncio
import asyncpg
import os
import sys
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


class OllamaCloudKeyManager:
    """Manager for adding Ollama Cloud system API key"""

    def __init__(self):
        """Initialize encryption and database connection"""
        if not BYOK_ENCRYPTION_KEY:
            raise ValueError("BYOK_ENCRYPTION_KEY environment variable not set")

        self.cipher = Fernet(BYOK_ENCRYPTION_KEY.encode())
        self.db_pool = None

    async def connect(self):
        """Create database connection pool"""
        print(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}...")

        self.db_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=int(POSTGRES_PORT),
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            min_size=1,
            max_size=5
        )

        print("✓ Database connection established")

    async def disconnect(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            print("✓ Database connection closed")

    def encrypt_key(self, api_key: str) -> str:
        """
        Encrypt API key using Fernet

        Args:
            api_key: Plain text API key

        Returns:
            Encrypted API key as base64 string
        """
        encrypted = self.cipher.encrypt(api_key.encode())
        return encrypted.decode()

    def decrypt_key(self, encrypted_key: str) -> str:
        """
        Decrypt API key for verification

        Args:
            encrypted_key: Encrypted API key

        Returns:
            Decrypted plain text API key
        """
        decrypted = self.cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()

    def mask_key(self, api_key: str) -> str:
        """
        Mask API key for safe display

        Args:
            api_key: Plain text API key

        Returns:
            Masked key (e.g., "c190...8ub")
        """
        if len(api_key) < 12:
            return "****"
        return f"{api_key[:7]}...{api_key[-4:]}"

    async def check_provider_exists(self) -> dict:
        """
        Check if ollama-cloud provider already exists

        Returns:
            dict: Provider record if exists, None otherwise
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, type, enabled, api_key_encrypted, config
                FROM llm_providers
                WHERE name = $1 OR type = $1
                """,
                "ollama-cloud"
            )

            if row:
                return dict(row)
            return None

    async def create_provider(self) -> str:
        """
        Create ollama-cloud provider in database

        Returns:
            str: Provider UUID
        """
        print(f"\nCreating provider: {PROVIDER_CONFIG['name']}...")

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO llm_providers (
                    name, type, enabled, priority, config,
                    created_at, updated_at,
                    health_status, api_key_source
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, name
                """,
                PROVIDER_CONFIG["name"],
                PROVIDER_CONFIG["type"],
                PROVIDER_CONFIG["enabled"],
                PROVIDER_CONFIG["priority"],
                PROVIDER_CONFIG["config"],
                datetime.utcnow(),
                datetime.utcnow(),
                "unknown",
                "database"
            )

            provider_id = str(row["id"])
            provider_name = row["name"]

            print(f"✓ Provider created: {provider_name} (ID: {provider_id})")
            return provider_id

    async def update_provider(self, provider_id: str) -> None:
        """
        Update existing provider configuration

        Args:
            provider_id: Provider UUID
        """
        print(f"\nUpdating provider: {PROVIDER_CONFIG['name']}...")

        async with self.db_pool.acquire() as conn:
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
                PROVIDER_CONFIG["config"],
                datetime.utcnow(),
                "database",
                provider_id
            )

            print(f"✓ Provider updated: {PROVIDER_CONFIG['name']}")

    async def store_api_key(self, provider_id: str) -> None:
        """
        Encrypt and store API key in database

        Args:
            provider_id: Provider UUID
        """
        print(f"\nEncrypting API key...")
        encrypted_key = self.encrypt_key(OLLAMA_CLOUD_API_KEY)
        masked_key = self.mask_key(OLLAMA_CLOUD_API_KEY)

        print(f"✓ API key encrypted (preview: {masked_key})")
        print(f"  Length: {len(encrypted_key)} bytes")

        async with self.db_pool.acquire() as conn:
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

            print(f"✓ API key stored in database for provider: {provider_id}")

    async def verify_key(self, provider_id: str) -> bool:
        """
        Verify the stored key can be decrypted

        Args:
            provider_id: Provider UUID

        Returns:
            bool: True if verification successful
        """
        print(f"\nVerifying stored key...")

        async with self.db_pool.acquire() as conn:
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
                return False

            try:
                decrypted = self.decrypt_key(row["api_key_encrypted"])

                if decrypted == OLLAMA_CLOUD_API_KEY:
                    print(f"✓ Key verification successful for: {row['name']}")
                    print(f"  Decrypted key matches original: {self.mask_key(decrypted)}")
                    return True
                else:
                    print(f"✗ Key mismatch!")
                    print(f"  Original:  {self.mask_key(OLLAMA_CLOUD_API_KEY)}")
                    print(f"  Decrypted: {self.mask_key(decrypted)}")
                    return False

            except Exception as e:
                print(f"✗ Decryption failed: {e}")
                return False

    async def get_provider_summary(self) -> None:
        """Print summary of all ollama providers"""
        print("\n" + "=" * 70)
        print("OLLAMA-CLOUD PROVIDER SUMMARY")
        print("=" * 70)

        async with self.db_pool.acquire() as conn:
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

            if not rows:
                print("No ollama providers found")
                return

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
                print(f"  Config: {row['config']}")

    async def run(self) -> bool:
        """
        Main execution flow

        Returns:
            bool: True if successful
        """
        try:
            # Connect to database
            await self.connect()

            # Check if provider exists
            existing = await self.check_provider_exists()

            if existing:
                print(f"\n⚠️  Provider 'ollama-cloud' already exists:")
                print(f"   ID: {existing['id']}")
                print(f"   Name: {existing['name']}")
                print(f"   Type: {existing['type']}")
                print(f"   Has Key: {bool(existing['api_key_encrypted'])}")

                response = input("\nUpdate existing provider? [y/N]: ").strip().lower()
                if response != 'y':
                    print("Aborted.")
                    return False

                provider_id = str(existing['id'])
                await self.update_provider(provider_id)
            else:
                provider_id = await self.create_provider()

            # Store encrypted API key
            await self.store_api_key(provider_id)

            # Verify key was stored correctly
            if not await self.verify_key(provider_id):
                print("\n✗ Key verification failed!")
                return False

            # Show summary
            await self.get_provider_summary()

            print("\n" + "=" * 70)
            print("✓ OLLAMA-CLOUD API KEY SUCCESSFULLY ADDED")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Test the API key via Ops-Center UI")
            print("2. Add Ollama Cloud models to the model catalog")
            print("3. Configure routing rules if needed")
            print("\nAPI Endpoint to test:")
            print("  GET /api/v1/llm/providers/keys")
            print("  POST /api/v1/llm/providers/keys/test")

            return True

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await self.disconnect()


async def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("OLLAMA CLOUD API KEY SETUP")
    print("=" * 70)
    print(f"\nAPI Key (masked): {OllamaCloudKeyManager().mask_key(OLLAMA_CLOUD_API_KEY)}")
    print(f"Database: {POSTGRES_DB}@{POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"Encryption: BYOK_ENCRYPTION_KEY ({'SET' if BYOK_ENCRYPTION_KEY else 'NOT SET'})")

    if not BYOK_ENCRYPTION_KEY:
        print("\n✗ BYOK_ENCRYPTION_KEY environment variable not set!")
        print("Cannot proceed without encryption key.")
        sys.exit(1)

    print("\nThis script will:")
    print("1. Create or update 'ollama-cloud' provider")
    print("2. Encrypt and store the API key")
    print("3. Verify the key was stored correctly")

    response = input("\nProceed? [y/N]: ").strip().lower()
    if response != 'y':
        print("Aborted.")
        sys.exit(0)

    manager = OllamaCloudKeyManager()
    success = await manager.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
