#!/usr/bin/env python3
"""
End-to-End Credential API Integration Tests

Tests the complete CRUD workflow without authentication (for testing).
In production, all endpoints require admin authentication.

Author: Integration Testing & Deployment Lead
Date: October 23, 2025
"""

import asyncio
import asyncpg
import os
import sys
from typing import Dict, Any, Optional

# Add services directory to path
sys.path.append('/app/services')
from credential_manager import CredentialManager

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://unicorn:your-postgres-password@unicorn-postgresql:5432/unicorn_db")

# Test data
TEST_USER_ID = "test-admin-user-123"
TEST_CLOUDFLARE_TOKEN = "cf_test_token_abcdefghijklmnopqrstuvwxyz1234567890"
TEST_CLOUDFLARE_TOKEN_UPDATED = "cf_updated_token_zyxwvutsrqponmlkjihgfedcba0987654321"
TEST_NAMECHEAP_API_KEY = "nc_test_api_key_1234567890abcdef"
TEST_NAMECHEAP_USERNAME = "test_user"


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
            print(f"✓ PASSED: {test_name}")
        else:
            self.failed += 1
            print(f"✗ FAILED: {test_name}")
        if message:
            print(f"  → {message}")

    def summary(self):
        """Print summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        print("=" * 60)

        if self.failed == 0:
            print("✓ ALL TESTS PASSED!")
            return 0
        else:
            print(f"✗ {self.failed} TEST(S) FAILED")
            return 1


async def test_credential_manager():
    """Test CredentialManager directly"""
    results = TestResults()

    print("=" * 60)
    print("CREDENTIAL API END-TO-END TESTS")
    print("=" * 60)
    print()

    # Connect to database using get_db_pool
    print("Connecting to database...")
    try:
        from database.connection import get_db_pool
        pool = await get_db_pool()
        conn = await pool.acquire()
        db_name = await conn.fetchval("SELECT current_database()")
        print(f"✓ Connected to database: {db_name}")
    except Exception as e:
        results.record("Database Connection", False, f"Error: {e}")
        results.summary()
        return results.failed

    # Initialize CredentialManager
    credential_manager = CredentialManager(db_connection=conn)

    try:
        # === TEST 1: Create Cloudflare Credential ===
        print("\n[1] Creating Cloudflare API Token...")
        try:
            await credential_manager.store_credential(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token",
                value=TEST_CLOUDFLARE_TOKEN,
                metadata={"description": "Test Cloudflare token", "created_by": "e2e_test"}
            )
            results.record("Create Cloudflare Credential", True, "Credential created successfully")
        except Exception as e:
            results.record("Create Cloudflare Credential", False, f"Error: {e}")

        # === TEST 2: Retrieve Cloudflare Credential ===
        print("\n[2] Retrieving Cloudflare API Token...")
        try:
            retrieved = await credential_manager.get_credential(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token"
            )
            if retrieved:
                # Check if value matches (decrypted)
                decrypted_value = retrieved.get("decrypted_value")
                if decrypted_value == TEST_CLOUDFLARE_TOKEN:
                    results.record("Retrieve Cloudflare Credential", True, f"Masked: {retrieved.get('masked_value')}")
                else:
                    results.record("Retrieve Cloudflare Credential", False, "Decrypted value doesn't match")
            else:
                results.record("Retrieve Cloudflare Credential", False, "Credential not found")
        except Exception as e:
            results.record("Retrieve Cloudflare Credential", False, f"Error: {e}")

        # === TEST 3: Get Credential for API (Decrypted) ===
        print("\n[3] Getting Decrypted Cloudflare Token for API Use...")
        try:
            api_token = await credential_manager.get_credential_for_api(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token"
            )
            if api_token == TEST_CLOUDFLARE_TOKEN:
                results.record("Get Credential for API", True, "Decrypted token matches")
            else:
                results.record("Get Credential for API", False, "Decrypted token doesn't match")
        except Exception as e:
            results.record("Get Credential for API", False, f"Error: {e}")

        # === TEST 4: Update Cloudflare Credential ===
        print("\n[4] Updating Cloudflare API Token...")
        try:
            await credential_manager.store_credential(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token",
                value=TEST_CLOUDFLARE_TOKEN_UPDATED,
                metadata={"description": "Updated test token", "updated_by": "e2e_test"}
            )

            # Verify update
            updated = await credential_manager.get_credential_for_api(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token"
            )
            if updated == TEST_CLOUDFLARE_TOKEN_UPDATED:
                results.record("Update Cloudflare Credential", True, "Token updated successfully")
            else:
                results.record("Update Cloudflare Credential", False, "Updated token doesn't match")
        except Exception as e:
            results.record("Update Cloudflare Credential", False, f"Error: {e}")

        # === TEST 5: Create NameCheap Credentials ===
        print("\n[5] Creating NameCheap Credentials...")
        try:
            # API Key
            await credential_manager.store_credential(
                user_id=TEST_USER_ID,
                service="namecheap",
                credential_type="api_key",
                value=TEST_NAMECHEAP_API_KEY,
                metadata={"description": "NameCheap API Key"}
            )

            # Username
            await credential_manager.store_credential(
                user_id=TEST_USER_ID,
                service="namecheap",
                credential_type="username",
                value=TEST_NAMECHEAP_USERNAME,
                metadata={"description": "NameCheap Username"}
            )

            results.record("Create NameCheap Credentials", True, "Both api_key and username created")
        except Exception as e:
            results.record("Create NameCheap Credentials", False, f"Error: {e}")

        # === TEST 6: List All Credentials for User ===
        print("\n[6] Listing All Credentials for User...")
        try:
            all_creds = await credential_manager.list_credentials(user_id=TEST_USER_ID)
            if len(all_creds) >= 3:  # cloudflare (1) + namecheap (2)
                results.record("List All Credentials", True, f"Found {len(all_creds)} credentials")
                for cred in all_creds:
                    print(f"  - {cred['service']}/{cred['credential_type']}: {cred['masked_value']}")
            else:
                results.record("List All Credentials", False, f"Expected >= 3, found {len(all_creds)}")
        except Exception as e:
            results.record("List All Credentials", False, f"Error: {e}")

        # === TEST 7: Delete Cloudflare Credential ===
        print("\n[7] Deleting Cloudflare API Token...")
        try:
            deleted = await credential_manager.delete_credential(
                user_id=TEST_USER_ID,
                service="cloudflare",
                credential_type="api_token"
            )
            if deleted:
                # Verify deletion
                verify = await credential_manager.get_credential(
                    user_id=TEST_USER_ID,
                    service="cloudflare",
                    credential_type="api_token"
                )
                if verify is None:
                    results.record("Delete Cloudflare Credential", True, "Credential deleted and verified")
                else:
                    results.record("Delete Cloudflare Credential", False, "Credential still exists after deletion")
            else:
                results.record("Delete Cloudflare Credential", False, "Delete returned False")
        except Exception as e:
            results.record("Delete Cloudflare Credential", False, f"Error: {e}")

        # === TEST 8: Verify Encryption (Check Database) ===
        print("\n[8] Verifying Encryption in Database...")
        try:
            row = await conn.fetchrow(
                "SELECT encrypted_value, masked_value FROM service_credentials WHERE user_id = $1 AND service = $2 LIMIT 1",
                TEST_USER_ID,
                "namecheap"
            )
            if row:
                encrypted = row['encrypted_value']
                masked = row['masked_value']

                # Encrypted value should be long gibberish (Fernet encrypted)
                if len(encrypted) > 100 and "gAAAAA" in encrypted:  # Fernet signature
                    results.record("Verify Encryption", True, f"Encrypted length: {len(encrypted)}, Masked: {masked}")
                else:
                    results.record("Verify Encryption", False, f"Encrypted value doesn't look Fernet encrypted: {encrypted[:50]}")
            else:
                results.record("Verify Encryption", False, "No credential found in database")
        except Exception as e:
            results.record("Verify Encryption", False, f"Error: {e}")

        # === TEST 9: Verify Audit Log ===
        print("\n[9] Verifying Audit Logs...")
        try:
            logs = await conn.fetch(
                "SELECT action, service, success FROM audit_logs WHERE user_id = $1 ORDER BY timestamp DESC LIMIT 10",
                TEST_USER_ID
            )
            if len(logs) > 0:
                results.record("Verify Audit Logs", True, f"Found {len(logs)} audit log entries")
                for log in logs[:5]:
                    print(f"  - {log['action']} {log['service']}: {'✓' if log['success'] else '✗'}")
            else:
                results.record("Verify Audit Logs", False, "No audit logs found")
        except Exception as e:
            results.record("Verify Audit Logs", False, f"Error: {e}")

    finally:
        # Cleanup
        print("\n[Cleanup] Removing test credentials...")
        try:
            await conn.execute("DELETE FROM service_credentials WHERE user_id = $1", TEST_USER_ID)
            await conn.execute("DELETE FROM audit_logs WHERE user_id = $1", TEST_USER_ID)
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")

        # Release connection back to pool
        await pool.release(conn)

    # Summary
    results.summary()
    return results.failed


if __name__ == "__main__":
    exit_code = asyncio.run(test_credential_manager())
    sys.exit(exit_code)
