"""
Test script for admin subscription management API endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8084"
ADMIN_EMAIL = "admin@example.com"

# Test session will be populated after login
session_cookies = {}

async def login_as_admin():
    """Login as admin user"""
    print("🔐 Logging in as admin...")

    # In a real scenario, you'd authenticate with Authentik
    # For testing, we'll assume the session is already set up
    print("⚠️  Note: This test requires an active admin session")
    print("   Please login via browser at http://localhost:8084 first")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/auth/me")

        if response.status_code == 200:
            user = response.json()
            print(f"✅ Logged in as: {user.get('email', 'unknown')}")
            return response.cookies
        else:
            print("❌ Not logged in - please login via browser first")
            return None

async def test_list_all_subscriptions():
    """Test listing all user subscriptions"""
    print("\n📋 Testing: GET /api/v1/admin/subscriptions/list")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/subscriptions/list",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Success! Found {data['total']} subscriptions")

                # Show first few subscriptions
                for i, sub in enumerate(data['subscriptions'][:3]):
                    print(f"\n  User {i+1}:")
                    print(f"    Email: {sub['email']}")
                    print(f"    Tier: {sub['tier']}")
                    print(f"    Status: {sub['status']}")
                    print(f"    Usage: {sub['usage']} / {sub['limit']}")

                return data['subscriptions']
            else:
                print(f"❌ API returned success=false")
        else:
            print(f"❌ Error: {response.text}")

    return []

async def test_get_user_subscription(email: str):
    """Test getting specific user subscription details"""
    print(f"\n🔍 Testing: GET /api/v1/admin/subscriptions/{email}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/subscriptions/{email}",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                user = data['user']
                print("✅ User details retrieved:")
                print(f"  Email: {user['email']}")
                print(f"  Tier: {user['tier']}")
                print(f"  Status: {user['status']}")
                print(f"  API Calls: {user['usage']['api_calls_used']} / {user['usage']['api_calls_limit']}")
                print(f"  BYOK Keys: {', '.join(user['byok_keys']) if user['byok_keys'] else 'None'}")
                return user
        else:
            print(f"❌ Error: {response.text}")

    return None

async def test_update_subscription(email: str):
    """Test updating a user's subscription"""
    print(f"\n✏️  Testing: PATCH /api/v1/admin/subscriptions/{email}")

    update_data = {
        "tier": "professional",
        "status": "active",
        "notes": "Test update from admin API test script"
    }

    print(f"Update data: {json.dumps(update_data, indent=2)}")

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/v1/admin/subscriptions/{email}",
            json=update_data,
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Subscription updated successfully")
                print(f"  New tier: {data['tier']}")
                print(f"  New status: {data['status']}")
                return True
        else:
            print(f"❌ Error: {response.text}")

    return False

async def test_reset_usage(email: str):
    """Test resetting user's API usage"""
    print(f"\n🔄 Testing: POST /api/v1/admin/subscriptions/{email}/reset-usage")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/admin/subscriptions/{email}/reset-usage",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Usage reset successfully")
                print(f"  Reset by: {data.get('reset_by', 'unknown')}")
                return True
        else:
            print(f"❌ Error: {response.text}")

    return False

async def test_analytics_overview():
    """Test getting subscription analytics overview"""
    print("\n📊 Testing: GET /api/v1/admin/subscriptions/analytics/overview")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/subscriptions/analytics/overview",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                analytics = data['analytics']
                print("✅ Analytics retrieved:")
                print(f"  Total Users: {analytics['total_users']}")
                print(f"  Active Subscriptions: {analytics['active_subscriptions']}")
                print(f"  MRR: ${analytics['revenue']['monthly_recurring_revenue']}")
                print(f"  ARR: ${analytics['revenue']['annual_recurring_revenue']}")
                print(f"  Total API Calls: {analytics['usage']['total_api_calls']:,}")
                print(f"\n  Tier Distribution:")
                for tier, count in analytics['tier_distribution'].items():
                    print(f"    {tier}: {count} users")
                return analytics
        else:
            print(f"❌ Error: {response.text}")

    return None

async def test_revenue_by_tier():
    """Test getting revenue breakdown by tier"""
    print("\n💰 Testing: GET /api/v1/admin/subscriptions/analytics/revenue-by-tier")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/subscriptions/analytics/revenue-by-tier",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Revenue by tier:")
                for tier, info in data['revenue_by_tier'].items():
                    print(f"  {tier}:")
                    print(f"    Users: {info['users']}")
                    print(f"    Monthly: ${info['monthly_revenue']}")
                    print(f"    Annual: ${info['annual_revenue']}")
                return data['revenue_by_tier']
        else:
            print(f"❌ Error: {response.text}")

    return None

async def test_usage_statistics():
    """Test getting usage statistics"""
    print("\n📈 Testing: GET /api/v1/admin/subscriptions/analytics/usage-stats")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/subscriptions/analytics/usage-stats",
            cookies=session_cookies
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data['usage_stats']
                print("✅ Usage statistics:")
                print(f"  Total Users: {stats['total_users']}")
                print(f"  Users with Usage: {stats['users_with_usage']}")
                print(f"  Total API Calls: {stats['total_api_calls']:,}")
                print(f"\n  Usage by Tier:")
                for tier, info in stats['usage_by_tier'].items():
                    print(f"    {tier}:")
                    print(f"      Users: {info['users']}")
                    print(f"      Total Calls: {info['total_calls']:,}")
                    print(f"      Average: {info['average_calls']:.1f}")
                return stats
        else:
            print(f"❌ Error: {response.text}")

    return None

async def run_all_tests():
    """Run all admin subscription API tests"""
    global session_cookies

    print("=" * 60)
    print("🚀 Admin Subscription Management API Tests")
    print("=" * 60)

    # Login
    cookies = await login_as_admin()
    if not cookies:
        print("\n❌ Cannot proceed without admin session")
        print("   Please visit http://localhost:8084 and login as admin")
        return

    session_cookies = cookies

    # Test 1: List all subscriptions
    subscriptions = await test_list_all_subscriptions()

    if not subscriptions:
        print("\n⚠️  No subscriptions found - skipping user-specific tests")
        return

    # Use first user for detailed tests
    test_user_email = subscriptions[0]['email']

    # Test 2: Get specific user details
    await test_get_user_subscription(test_user_email)

    # Test 3: Analytics overview
    await test_analytics_overview()

    # Test 4: Revenue by tier
    await test_revenue_by_tier()

    # Test 5: Usage statistics
    await test_usage_statistics()

    # Test 6: Reset usage (commented out to avoid modifying data)
    # print(f"\n⚠️  Skipping usage reset test to avoid modifying data")
    # await test_reset_usage(test_user_email)

    # Test 7: Update subscription (commented out to avoid modifying data)
    # print(f"\n⚠️  Skipping subscription update test to avoid modifying data")
    # await test_update_subscription(test_user_email)

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
