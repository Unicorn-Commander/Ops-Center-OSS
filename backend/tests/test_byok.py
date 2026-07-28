#!/usr/bin/env python3
"""
BYOK API Testing Script

Tests the Bring Your Own Key functionality including:
- Key encryption/decryption
- API endpoints
- Provider validation
- Service integration
"""

import asyncio
import httpx
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from key_encryption import get_encryption, KeyEncryption
from byok_helpers import (
    get_user_api_key,
    get_user_api_key_or_default,
    get_llm_config_for_user,
    clear_user_key_cache
)

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8084")
TEST_SESSION_COOKIE = os.getenv("TEST_SESSION_COOKIE", "")

# Test data
TEST_API_KEY = "sk-test-1234567890abcdefghijklmnopqrstuvwxyz"
TEST_PROVIDER = "openai"
TEST_LABEL = "Test Key"

def test_encryption():
    """Test key encryption and decryption"""
    print("\n" + "="*60)
    print("Testing Key Encryption")
    print("="*60)

    try:
        # Check if encryption key is set
        if not os.getenv("ENCRYPTION_KEY"):
            print_error("ENCRYPTION_KEY environment variable not set")
            return False

        encryption = get_encryption()
        print_success("Encryption module initialized")

        # Test encryption
        encrypted = encryption.encrypt_key(TEST_API_KEY)
        print_success(f"Encrypted key: {encrypted[:40]}...")

        # Test decryption
        decrypted = encryption.decrypt_key(encrypted)
        if decrypted == TEST_API_KEY:
            print_success("Decryption successful - keys match")
        else:
            print_error("Decryption failed - keys don't match")
            return False

        # Test masking
        masked = encryption.mask_key(TEST_API_KEY)
        print_success(f"Masked key: {masked}")

        # Test invalid decryption
        try:
            encryption.decrypt_key("invalid-encrypted-data")
            print_error("Should have failed on invalid encrypted data")
            return False
        except ValueError:
            print_success("Correctly rejected invalid encrypted data")

        return True

    except Exception as e:
        print_error(f"Encryption test failed: {e}")
        return False

async def test_api_endpoints():
    """Test BYOK API endpoints"""
    print("\n" + "="*60)
    print("Testing API Endpoints")
    print("="*60)

    if not TEST_SESSION_COOKIE:
        print_warning("TEST_SESSION_COOKIE not set - skipping API tests")
        print_info("To test API endpoints, first login and set TEST_SESSION_COOKIE")
        return True

    headers = {"Cookie": f"session={TEST_SESSION_COOKIE}"}

    async with httpx.AsyncClient() as client:
        try:
            # Test 1: List providers
            print_info("Testing GET /api/v1/byok/providers")
            response = await client.get(
                f"{BASE_URL}/api/v1/byok/providers",
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                providers = response.json()
                print_success(f"Got {len(providers)} providers")
                for p in providers[:3]:
                    print(f"  - {p['name']} ({p['id']}): {'✓' if p['configured'] else '✗'}")
            else:
                print_error(f"Failed to list providers: {response.status_code}")
                return False

            # Test 2: List keys
            print_info("\nTesting GET /api/v1/byok/keys")
            response = await client.get(
                f"{BASE_URL}/api/v1/byok/keys",
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                keys = response.json()
                print_success(f"Got {len(keys)} configured keys")
                for key in keys:
                    print(f"  - {key['provider_name']}: {key['key_preview']}")
            else:
                print_error(f"Failed to list keys: {response.status_code}")
                return False

            # Test 3: Add a key
            print_info("\nTesting POST /api/v1/byok/keys/add")
            response = await client.post(
                f"{BASE_URL}/api/v1/byok/keys/add",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "provider": TEST_PROVIDER,
                    "key": TEST_API_KEY,
                    "label": TEST_LABEL
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                print_success(f"Added key for {result['provider_name']}")
            elif response.status_code == 403:
                print_warning("BYOK requires Starter tier or above")
                return True
            else:
                print_error(f"Failed to add key: {response.status_code} - {response.text}")
                return False

            # Test 4: Get stats
            print_info("\nTesting GET /api/v1/byok/stats")
            response = await client.get(
                f"{BASE_URL}/api/v1/byok/stats",
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                stats = response.json()
                print_success("Got BYOK stats:")
                print(f"  - Configured providers: {stats['configured_providers']}/{stats['total_providers']}")
                print(f"  - Valid providers: {stats['valid_providers']}")
                print(f"  - User tier: {stats['user_tier']}")
            else:
                print_error(f"Failed to get stats: {response.status_code}")
                return False

            # Test 5: Test the key (will fail with test key, but that's ok)
            print_info("\nTesting POST /api/v1/byok/keys/test/{provider}")
            response = await client.post(
                f"{BASE_URL}/api/v1/byok/keys/test/{TEST_PROVIDER}",
                headers=headers,
                timeout=20.0
            )

            if response.status_code == 200:
                result = response.json()
                print_info(f"Test result: {result['status']} - {result['message']}")
                if result['status'] == 'invalid':
                    print_success("Expected result (test key is not valid)")
            elif response.status_code == 404:
                print_warning("Key not found (may have been added after last test)")
            else:
                print_error(f"Failed to test key: {response.status_code}")
                return False

            # Test 6: Delete the key
            print_info("\nTesting DELETE /api/v1/byok/keys/{provider}")
            response = await client.delete(
                f"{BASE_URL}/api/v1/byok/keys/{TEST_PROVIDER}",
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                print_success(f"Deleted key for {result['provider']}")
            else:
                print_error(f"Failed to delete key: {response.status_code}")
                return False

            return True

        except httpx.TimeoutException:
            print_error("Request timeout - is the server running?")
            return False
        except Exception as e:
            print_error(f"API test failed: {e}")
            return False

async def test_service_integration():
    """Test service integration helpers"""
    print("\n" + "="*60)
    print("Testing Service Integration Helpers")
    print("="*60)

    try:
        # Test with non-existent user (should use fallback)
        print_info("Testing fallback to system key")

        # Set a test system key
        os.environ["OPENAI_API_KEY"] = "sk-system-fallback-key"

        try:
            key = await get_user_api_key_or_default(
                user_email="nonexistent@example.com",
                provider="openai",
                fallback_env_var="OPENAI_API_KEY"
            )

            if key == "sk-system-fallback-key":
                print_success("Correctly fell back to system key")
            else:
                print_error(f"Expected system key, got: {key}")
                return False

        except ValueError as e:
            # If no system key is configured, this is expected
            print_info(f"No system key configured: {e}")

        # Test LLM config
        print_info("\nTesting LLM config generation")
        os.environ["OPENAI_API_KEY"] = "sk-system-key-123"

        try:
            config = await get_llm_config_for_user(
                user_email="test@example.com",
                preferred_provider="openai"
            )

            print_success("Got LLM config:")
            print(f"  - Provider: {config['provider']}")
            print(f"  - Has API key: {len(config['api_key']) > 0}")
            print(f"  - Is BYOK: {config['is_byok']}")

        except ValueError as e:
            print_warning(f"Could not get LLM config (expected if no keys configured): {e}")

        # Test cache clearing
        print_info("\nTesting cache management")
        clear_user_key_cache()
        print_success("Cache cleared successfully")

        return True

    except Exception as e:
        print_error(f"Service integration test failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)

    try:
        encryption = get_encryption()

        # Test 1: Empty key
        try:
            encryption.encrypt_key("")
            print_error("Should reject empty key")
            return False
        except ValueError:
            print_success("Correctly rejected empty key")

        # Test 2: Invalid encrypted data
        try:
            encryption.decrypt_key("not-valid-encrypted-data")
            print_error("Should reject invalid encrypted data")
            return False
        except ValueError:
            print_success("Correctly rejected invalid encrypted data")

        # Test 3: Very long key
        long_key = "sk-" + ("x" * 1000)
        encrypted_long = encryption.encrypt_key(long_key)
        decrypted_long = encryption.decrypt_key(encrypted_long)

        if decrypted_long == long_key:
            print_success("Handles long keys correctly")
        else:
            print_error("Failed to handle long key")
            return False

        # Test 4: Special characters in key
        special_key = "sk-test-!@#$%^&*()_+-=[]{}|;:,.<>?"
        encrypted_special = encryption.encrypt_key(special_key)
        decrypted_special = encryption.decrypt_key(encrypted_special)

        if decrypted_special == special_key:
            print_success("Handles special characters correctly")
        else:
            print_error("Failed to handle special characters")
            return False

        return True

    except Exception as e:
        print_error(f"Edge case test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           BYOK (Bring Your Own Key) Test Suite              ║
╚══════════════════════════════════════════════════════════════╝
""")

    results = {
        "Encryption": test_encryption(),
        "API Endpoints": await test_api_endpoints(),
        "Service Integration": await test_service_integration(),
        "Edge Cases": test_edge_cases()
    }

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    for test_name, passed_test in results.items():
        status = "PASS" if passed_test else "FAIL"
        color = Colors.GREEN if passed_test else Colors.RED
        print(f"{color}{test_name}: {status}{Colors.RESET}")

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print_success("\n🎉 All tests passed!")
        return 0
    else:
        print_error(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
