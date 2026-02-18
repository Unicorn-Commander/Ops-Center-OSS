#!/usr/bin/env python3
"""
Comprehensive Lago Integration Tests
Tests org-based customer creation and subscription management
"""

import asyncio
import time
import uuid
import sys
sys.path.insert(0, '/app')

from lago_integration import (
    check_lago_health,
    create_org_customer,
    subscribe_org_to_plan,
    record_api_call,
    get_subscription,
    get_current_usage,
    get_customer
)


async def test_health_check():
    """Test 1: Lago API Health Check"""
    try:
        result = await check_lago_health()
        status = result.get('status')
        if status == 'healthy':
            print('✅ Test 1: Lago health check - PASSED')
            print(f'   API URL: {result.get("api_url")}')
            return True
        else:
            print('❌ Test 1: Lago health check - FAILED')
            print(f'   Status: {status}')
            return False
    except Exception as e:
        print(f'❌ Test 1: Lago health check - FAILED: {e}')
        return False


async def test_create_customer():
    """Test 2: Create Organization Customer"""
    try:
        org_id = f'org_test_{int(time.time())}'
        customer = await create_org_customer(
            org_id=org_id,
            org_name='Test Organization',
            email='test@example.com',
            user_id='user_test_123'
        )

        ext_id = customer.get('external_id')
        if ext_id == org_id:
            print('✅ Test 2: Create org customer - PASSED')
            print(f'   Org ID: {org_id}')
            print(f'   Name: {customer.get("name")}')
            print(f'   Email: {customer.get("email")}')
            return True, org_id
        else:
            print('❌ Test 2: Create org customer - FAILED')
            print(f'   Expected ID: {org_id}, Got: {ext_id}')
            return False, None
    except Exception as e:
        print(f'❌ Test 2: Create org customer - FAILED: {e}')
        return False, None


async def test_subscribe_to_plan():
    """Test 3: Subscribe Organization to Plan"""
    try:
        org_id = f'org_sub_{int(time.time())}'
        subscription = await subscribe_org_to_plan(
            org_id=org_id,
            plan_code='founders_friend',
            org_name='Test Subscription Org',
            email='testsub@example.com',
            user_id='user_sub_test'
        )

        status = subscription.get('status')
        plan_code = subscription.get('plan_code')

        if status == 'active' and plan_code == 'founders_friend':
            print('✅ Test 3: Subscribe to plan - PASSED')
            print(f'   Org ID: {org_id}')
            print(f'   Plan: {plan_code}')
            print(f'   Status: {status}')
            print(f'   Subscription ID: {subscription.get("lago_id")}')
            return True, org_id
        else:
            print('❌ Test 3: Subscribe to plan - FAILED')
            print(f'   Status: {status}, Plan: {plan_code}')
            return False, None
    except Exception as e:
        print(f'❌ Test 3: Subscribe to plan - FAILED: {e}')
        return False, None


async def test_record_usage(org_id):
    """Test 4: Record API Usage Event"""
    try:
        transaction_id = str(uuid.uuid4())
        result = await record_api_call(
            org_id=org_id,
            transaction_id=transaction_id,
            endpoint='/api/test',
            user_id='user_test',
            tokens=150,
            model='gpt-4'
        )

        if result:
            print('✅ Test 4: Record usage event - PASSED')
            print(f'   Org ID: {org_id}')
            print(f'   Transaction ID: {transaction_id[:30]}...')
            print(f'   Tokens: 150, Model: gpt-4')
            return True
        else:
            print('❌ Test 4: Record usage event - FAILED')
            print(f'   Result: {result}')
            return False
    except Exception as e:
        print(f'❌ Test 4: Record usage event - FAILED: {e}')
        return False


async def test_query_customer():
    """Test 5: Query Lago for Customers"""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://unicorn-lago-api:3000/api/v1/customers',
                headers={'Authorization': 'Bearer your-lago-api-key'},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                customers = data.get('customers', [])
                test_customers = [c for c in customers if 'test' in c.get('external_id', '').lower()]

                print('✅ Test 5: Query customer - PASSED')
                print(f'   Total customers: {len(customers)}')
                print(f'   Test customers: {len(test_customers)}')

                if test_customers:
                    print('\n   Recent test customers:')
                    for customer in test_customers[-3:]:
                        ext_id = customer.get('external_id')
                        name = customer.get('name')
                        email = customer.get('email')
                        print(f'     - {ext_id}: {name} ({email})')

                return True
            else:
                print('❌ Test 5: Query customer - FAILED')
                print(f'   Status: {response.status_code}')
                return False
    except Exception as e:
        print(f'❌ Test 5: Query customer - FAILED: {e}')
        return False


async def main():
    """Run all Lago integration tests"""
    print('LAGO INTEGRATION TESTS:')
    print('=' * 50)
    print()

    results = []

    # Test 1: Health Check
    results.append(await test_health_check())
    print()

    # Test 2: Create Customer
    success, customer_org_id = await test_create_customer()
    results.append(success)
    print()

    # Test 3: Subscribe to Plan
    success, subscription_org_id = await test_subscribe_to_plan()
    results.append(success)
    print()

    # Test 4: Record Usage (only if Test 3 passed)
    if subscription_org_id:
        results.append(await test_record_usage(subscription_org_id))
    else:
        print('⏭️  Test 4: Record usage event - SKIPPED (Test 3 failed)')
        results.append(False)
    print()

    # Test 5: Query Customers
    results.append(await test_query_customer())
    print()

    # Summary
    passed = sum(results)
    total = len(results)

    print('=' * 50)
    print(f'SUMMARY: {passed}/{total} tests passed')
    if passed < total:
        print(f'         {total - passed}/{total} tests failed')
    print('=' * 50)

    return passed == total


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
