#!/usr/bin/env python3
"""
Feature Flag System Test Script

Tests all functionality of the feature flag system to ensure
it's working correctly before Phase 1 implementation.
"""
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.feature_flags import FeatureFlags


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result with color."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details and not passed:
        print(f"     {details}")


def test_global_enable_disable():
    """Test global enable/disable functionality."""
    print("\n" + "="*60)
    print("TEST 1: Global Enable/Disable")
    print("="*60)

    # Save original state
    original = FeatureFlags.FLAGS["unified_llm_hub"]["enabled"]

    try:
        # Test disable
        FeatureFlags.set_flag("unified_llm_hub", enabled=False)
        disabled = not FeatureFlags.is_enabled("unified_llm_hub", "test@example.com")
        print_test("Global disable works", disabled)

        # Test enable
        FeatureFlags.set_flag("unified_llm_hub", enabled=True)
        enabled = FeatureFlags.is_enabled("unified_llm_hub", None)
        print_test("Global enable works (100% rollout)", enabled)

        return disabled and enabled
    finally:
        # Restore original state
        FeatureFlags.set_flag("unified_llm_hub", enabled=original)


def test_whitelist():
    """Test whitelist functionality."""
    print("\n" + "="*60)
    print("TEST 2: Whitelist")
    print("="*60)

    # Add test users to whitelist
    FeatureFlags.set_flag(
        "unified_llm_hub",
        enabled=True,
        rollout_percentage=0,
        whitelist_users=["admin@test.com", "dev@test.com"]
    )

    # Test whitelisted users
    admin_enabled = FeatureFlags.is_enabled("unified_llm_hub", "admin@test.com")
    print_test("Whitelisted user 1 enabled", admin_enabled)

    dev_enabled = FeatureFlags.is_enabled("unified_llm_hub", "dev@test.com")
    print_test("Whitelisted user 2 enabled", dev_enabled)

    # Test non-whitelisted user
    regular_disabled = not FeatureFlags.is_enabled("unified_llm_hub", "regular@test.com")
    print_test("Non-whitelisted user disabled (0% rollout)", regular_disabled)

    return admin_enabled and dev_enabled and regular_disabled


def test_blacklist():
    """Test blacklist functionality."""
    print("\n" + "="*60)
    print("TEST 3: Blacklist")
    print("="*60)

    # Set up blacklist
    FeatureFlags.set_flag(
        "unified_llm_hub",
        enabled=True,
        rollout_percentage=100,
        blacklist_users=["blocked@test.com"]
    )

    # Test blacklisted user
    blocked_disabled = not FeatureFlags.is_enabled("unified_llm_hub", "blocked@test.com")
    print_test("Blacklisted user disabled (even at 100% rollout)", blocked_disabled)

    # Test non-blacklisted user
    regular_enabled = FeatureFlags.is_enabled("unified_llm_hub", "regular@test.com")
    print_test("Non-blacklisted user enabled", regular_enabled)

    return blocked_disabled and regular_enabled


def test_rollout_percentage():
    """Test rollout percentage functionality."""
    print("\n" + "="*60)
    print("TEST 4: Rollout Percentage")
    print("="*60)

    # Test 0% rollout
    FeatureFlags.set_flag(
        "unified_llm_hub",
        enabled=True,
        rollout_percentage=0,
        whitelist_users=[],
        blacklist_users=[]
    )

    zero_disabled = not FeatureFlags.is_enabled("unified_llm_hub", "test@example.com")
    print_test("0% rollout disables for all users", zero_disabled)

    # Test 100% rollout
    FeatureFlags.set_flag("unified_llm_hub", rollout_percentage=100)
    hundred_enabled = FeatureFlags.is_enabled("unified_llm_hub", "test@example.com")
    print_test("100% rollout enables for all users", hundred_enabled)

    # Test 50% rollout (deterministic)
    FeatureFlags.set_flag("unified_llm_hub", rollout_percentage=50)

    # Test multiple users to see distribution
    test_users = [f"user{i}@test.com" for i in range(100)]
    enabled_count = sum(1 for user in test_users if FeatureFlags.is_enabled("unified_llm_hub", user))

    # Should be approximately 50% (allow 40-60% range for hash distribution)
    percentage_ok = 40 <= enabled_count <= 60
    print_test(f"50% rollout distributes correctly ({enabled_count}/100 enabled)", percentage_ok)

    # Test deterministic behavior (same user always gets same result)
    result1 = FeatureFlags.is_enabled("unified_llm_hub", "user123@test.com")
    result2 = FeatureFlags.is_enabled("unified_llm_hub", "user123@test.com")
    deterministic = result1 == result2
    print_test("Rollout is deterministic (same user, same result)", deterministic)

    return zero_disabled and hundred_enabled and percentage_ok and deterministic


def test_flag_status():
    """Test getting flag status/configuration."""
    print("\n" + "="*60)
    print("TEST 5: Flag Status & Configuration")
    print("="*60)

    # Get status
    status = FeatureFlags.get_flag_status("unified_llm_hub")

    has_enabled = "enabled" in status
    print_test("Status contains 'enabled' field", has_enabled)

    has_rollout = "rollout_percentage" in status
    print_test("Status contains 'rollout_percentage' field", has_rollout)

    has_description = "description" in status
    print_test("Status contains 'description' field", has_description)

    # Test invalid flag
    invalid_status = FeatureFlags.get_flag_status("nonexistent_flag")
    invalid_empty = len(invalid_status) == 0
    print_test("Invalid flag returns empty dict", invalid_empty)

    return has_enabled and has_rollout and has_description and invalid_empty


def test_list_flags():
    """Test listing all flags."""
    print("\n" + "="*60)
    print("TEST 6: List Flags")
    print("="*60)

    # List all flags
    all_flags = FeatureFlags.list_flags()

    has_unified_hub = "unified_llm_hub" in all_flags
    print_test("List contains 'unified_llm_hub' flag", has_unified_hub)

    # List by tag
    llm_flags = FeatureFlags.list_flags(tags=["llm"])
    has_llm_tag = "unified_llm_hub" in llm_flags
    print_test("Tag filtering works ('llm' tag)", has_llm_tag)

    admin_flags = FeatureFlags.list_flags(tags=["admin"])
    has_admin_tag = "unified_llm_hub" in admin_flags
    print_test("Tag filtering works ('admin' tag)", has_admin_tag)

    return has_unified_hub and has_llm_tag and has_admin_tag


def test_user_flags():
    """Test getting all flags for a user."""
    print("\n" + "="*60)
    print("TEST 7: User Flags")
    print("="*60)

    # Set up flags
    FeatureFlags.set_flag(
        "unified_llm_hub",
        enabled=True,
        rollout_percentage=100
    )

    # Get user flags
    user_flags = FeatureFlags.get_user_flags("test@example.com")

    is_dict = isinstance(user_flags, dict)
    print_test("Returns dictionary", is_dict)

    has_unified_hub = "unified_llm_hub" in user_flags
    print_test("Contains 'unified_llm_hub' flag", has_unified_hub)

    hub_enabled = user_flags.get("unified_llm_hub", False)
    print_test("'unified_llm_hub' is enabled", hub_enabled)

    return is_dict and has_unified_hub and hub_enabled


def test_convenience_functions():
    """Test convenience functions."""
    print("\n" + "="*60)
    print("TEST 8: Convenience Functions")
    print("="*60)

    from config.feature_flags import is_unified_llm_hub_enabled, get_enabled_features

    # Set up flag
    FeatureFlags.set_flag(
        "unified_llm_hub",
        enabled=True,
        rollout_percentage=100
    )

    # Test is_unified_llm_hub_enabled
    hub_enabled = is_unified_llm_hub_enabled("test@example.com")
    print_test("is_unified_llm_hub_enabled() works", hub_enabled)

    # Test get_enabled_features
    features = get_enabled_features("test@example.com")

    is_list = isinstance(features, list)
    print_test("get_enabled_features() returns list", is_list)

    has_hub = "unified_llm_hub" in features
    print_test("Feature list contains 'unified_llm_hub'", has_hub)

    return hub_enabled and is_list and has_hub


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("FEATURE FLAG SYSTEM TEST SUITE")
    print("="*60)
    print("\nTesting feature flag infrastructure...")

    results = {}

    # Run all test suites
    results["Global Enable/Disable"] = test_global_enable_disable()
    results["Whitelist"] = test_whitelist()
    results["Blacklist"] = test_blacklist()
    results["Rollout Percentage"] = test_rollout_percentage()
    results["Flag Status"] = test_flag_status()
    results["List Flags"] = test_list_flags()
    results["User Flags"] = test_user_flags()
    results["Convenience Functions"] = test_convenience_functions()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} test suites passed")
    print("-"*60)

    if passed == total:
        print("\n🎉 All tests passed! Feature flag system is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please review and fix.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
