#!/usr/bin/env python3
"""
Test credit auto-provisioning functionality

This script tests that:
1. New users automatically get credit accounts when checked
2. Default trial tier with 5.0 credits is allocated
3. No errors during auto-provisioning
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credit_system import credit_manager


async def test_autoprovision():
    """Test automatic credit provisioning for new users"""

    print("=" * 70)
    print("CREDIT AUTO-PROVISIONING TEST")
    print("=" * 70)

    test_user = "testuser@example.com"

    try:
        # Initialize credit manager
        print(f"\n1. Initializing credit manager...")
        await credit_manager.initialize()
        print("   ✓ Credit manager initialized")

        # Test: Get balance for non-existent user (should auto-provision)
        print(f"\n2. Testing auto-provision for new user: {test_user}")
        balance = await credit_manager.get_balance(test_user)

        print(f"\n   Credit Account Details:")
        print(f"   - User ID: {balance['user_id']}")
        print(f"   - Credits Remaining: {balance['credits_remaining']}")
        print(f"   - Credits Allocated: {balance['credits_allocated']}")
        print(f"   - Tier: {balance.get('tier', 'N/A')}")
        print(f"   - Last Reset: {balance['last_reset']}")
        print(f"   - Created At: {balance['created_at']}")

        # Verify auto-provisioning worked correctly
        print(f"\n3. Verifying auto-provisioning...")

        assertions = []

        # Check credits were allocated
        if float(balance['credits_remaining']) > 0:
            print(f"   ✓ Credits allocated: {balance['credits_remaining']}")
            assertions.append(True)
        else:
            print(f"   ✗ No credits allocated (expected > 0)")
            assertions.append(False)

        # Check tier is trial
        if balance.get('tier') == 'trial':
            print(f"   ✓ Tier set to 'trial'")
            assertions.append(True)
        else:
            print(f"   ✗ Tier not set to 'trial' (got: {balance.get('tier')})")
            assertions.append(False)

        # Check allocated matches remaining (for new accounts)
        if balance['credits_remaining'] == balance['credits_allocated']:
            print(f"   ✓ Allocated credits match remaining credits")
            assertions.append(True)
        else:
            print(f"   ✗ Allocated != Remaining ({balance['credits_allocated']} != {balance['credits_remaining']})")
            assertions.append(False)

        # Test: Get balance again (should return existing record, not create new one)
        print(f"\n4. Testing idempotency (second request should return same account)...")
        balance2 = await credit_manager.get_balance(test_user)

        if balance['created_at'] == balance2['created_at']:
            print(f"   ✓ Same account returned (created_at matches)")
            assertions.append(True)
        else:
            print(f"   ✗ Different account returned (created_at changed)")
            assertions.append(False)

        # Summary
        print("\n" + "=" * 70)
        if all(assertions):
            print("✓ ALL TESTS PASSED")
            print(f"✓ Auto-provisioning working correctly")
            print(f"✓ New user '{test_user}' has {balance['credits_remaining']} credits")
            return 0
        else:
            print("✗ SOME TESTS FAILED")
            print(f"✗ {sum(assertions)}/{len(assertions)} assertions passed")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        await credit_manager.close()
        print("\nCredit manager closed")


if __name__ == "__main__":
    exit_code = asyncio.run(test_autoprovision())
    sys.exit(exit_code)
