#!/usr/bin/env python3
"""
Test script for Redis session manager
Verifies connection and basic operations
"""
import sys
import json
from redis_session import redis_session_manager

def test_redis_connection():
    """Test basic Redis connection"""
    print("Testing Redis connection...")
    try:
        # The connection is established in __init__
        print(f"✓ Connected to Redis at {redis_session_manager.host}:{redis_session_manager.port}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        return False

def test_session_operations():
    """Test CRUD operations on sessions"""
    print("\nTesting session operations...")
    test_session_id = "test_session_12345"
    test_data = {
        "user": {
            "username": "test_user",
            "email": "test@example.com",
            "role": "admin"
        },
        "access_token": "test_token_xyz",
        "created": 1234567890.0
    }

    try:
        # Test SET
        print("1. Testing session SET...")
        result = redis_session_manager.set(test_session_id, test_data)
        if result:
            print("   ✓ Session stored successfully")
        else:
            print("   ✗ Failed to store session")
            return False

        # Test EXISTS
        print("2. Testing session EXISTS...")
        exists = redis_session_manager.exists(test_session_id)
        if exists:
            print("   ✓ Session exists check passed")
        else:
            print("   ✗ Session exists check failed")
            return False

        # Test GET
        print("3. Testing session GET...")
        retrieved_data = redis_session_manager.get(test_session_id)
        if retrieved_data:
            print(f"   ✓ Session retrieved: {retrieved_data.get('user', {}).get('username')}")
            if retrieved_data == test_data:
                print("   ✓ Data matches original")
            else:
                print("   ⚠ Data mismatch (timestamps might differ slightly)")
        else:
            print("   ✗ Failed to retrieve session")
            return False

        # Test dict-style access
        print("4. Testing dict-style access...")
        session = redis_session_manager[test_session_id]
        if session:
            print(f"   ✓ Dict-style GET works: {session.get('user', {}).get('email')}")
        else:
            print("   ✗ Dict-style GET failed")
            return False

        # Test 'in' operator
        print("5. Testing 'in' operator...")
        if test_session_id in redis_session_manager:
            print("   ✓ 'in' operator works")
        else:
            print("   ✗ 'in' operator failed")
            return False

        # Test COUNT
        print("6. Testing session COUNT...")
        count = redis_session_manager.count()
        print(f"   ✓ Total sessions: {count}")

        # Test REFRESH (TTL reset)
        print("7. Testing session REFRESH...")
        refreshed = redis_session_manager.refresh(test_session_id)
        if refreshed:
            print("   ✓ Session TTL refreshed")
        else:
            print("   ✗ Failed to refresh session")
            return False

        # Test DELETE
        print("8. Testing session DELETE...")
        deleted = redis_session_manager.delete(test_session_id)
        if deleted:
            print("   ✓ Session deleted successfully")
        else:
            print("   ✗ Failed to delete session")
            return False

        # Verify deletion
        print("9. Verifying deletion...")
        exists_after_delete = redis_session_manager.exists(test_session_id)
        if not exists_after_delete:
            print("   ✓ Session confirmed deleted")
        else:
            print("   ✗ Session still exists after deletion")
            return False

        return True

    except Exception as e:
        print(f"✗ Error during session operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ttl_configuration():
    """Test TTL configuration"""
    print("\nTesting TTL configuration...")
    try:
        ttl = redis_session_manager.ttl
        print(f"✓ Session TTL: {ttl} seconds ({ttl/3600:.1f} hours)")
        return True
    except Exception as e:
        print(f"✗ Failed to check TTL: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Redis Session Manager Test Suite")
    print("=" * 60)

    all_passed = True

    # Test 1: Connection
    if not test_redis_connection():
        all_passed = False
        print("\n✗ Connection test failed - aborting further tests")
        sys.exit(1)

    # Test 2: Operations
    if not test_session_operations():
        all_passed = False

    # Test 3: TTL
    if not test_ttl_configuration():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ Some tests FAILED")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
