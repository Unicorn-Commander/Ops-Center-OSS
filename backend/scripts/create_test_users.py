#!/usr/bin/env python3
"""
Create Test Users at Different Subscription Tiers
==================================================

This script creates 4 test users with different subscription tiers to enable
comprehensive testing of tier-based model access controls.

Test Users Created:
1. Trial User - trial tier (5.00 credits, 50-80 models)
2. Starter User - starter tier (20.00 credits, 150-200 models)
3. Professional User - professional tier (60.00 credits, 250-300 models)
4. Enterprise User - enterprise tier (999999.99 credits, all 370+ models)

Database: unicorn_db @ unicorn-postgresql
Table: user_credits

Author: Ops-Center Team
Date: November 6, 2025
"""

import asyncpg
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
import sys
import os

# Database connection
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER", "ops_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change-me")
DB_NAME = os.getenv("POSTGRES_DB", "ops_center_db")

# Test user configurations
TEST_USERS = [
    {
        "user_id": "test-trial-user-00000000-0000-0000-0000-000000000001",
        "email": "trial@test.example.com",
        "tier": "trial",
        "credits_allocated": Decimal("5.00"),
        "credits_remaining": Decimal("5.00"),
        "description": "Trial user - should see 50-80 free/cheap models only"
    },
    {
        "user_id": "test-starter-user-00000000-0000-0000-0000-000000000002",
        "email": "starter@test.example.com",
        "tier": "starter",
        "credits_allocated": Decimal("20.00"),
        "credits_remaining": Decimal("20.00"),
        "description": "Starter user - should see 150-200 models"
    },
    {
        "user_id": "test-professional-user-00000000-0000-0000-0000-000000000003",
        "email": "professional@test.example.com",
        "tier": "professional",
        "credits_allocated": Decimal("60.00"),
        "credits_remaining": Decimal("60.00"),
        "description": "Professional user - should see 250-300 models"
    },
    {
        "user_id": "test-enterprise-user-00000000-0000-0000-0000-000000000004",
        "email": "enterprise@test.example.com",
        "tier": "enterprise",
        "credits_allocated": Decimal("999999.99"),
        "credits_remaining": Decimal("999999.99"),
        "description": "Enterprise user - should see all 370+ models"
    }
]


async def create_test_users():
    """Create test users in the database"""

    # Connect to database
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    print("✓ Connected to database\n")

    try:
        # Check if test users already exist
        existing = await conn.fetch(
            "SELECT user_id, tier FROM user_credits WHERE user_id LIKE 'test-%'"
        )

        if existing:
            print("⚠️  Found existing test users:")
            for row in existing:
                print(f"  - {row['user_id']} ({row['tier']})")

            response = input("\nDelete existing test users and recreate? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return

            # Delete existing test users
            deleted = await conn.execute(
                "DELETE FROM user_credits WHERE user_id LIKE 'test-%'"
            )
            print(f"✓ Deleted existing test users\n")

        # Create new test users
        print("Creating test users...\n")

        for user in TEST_USERS:
            last_reset = datetime.utcnow() + timedelta(days=30)

            await conn.execute(
                """
                INSERT INTO user_credits (
                    user_id,
                    credits_remaining,
                    credits_allocated,
                    tier,
                    monthly_cap,
                    last_reset,
                    email_notifications_enabled
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user["user_id"],
                user["credits_remaining"],
                user["credits_allocated"],
                user["tier"],
                user["credits_allocated"],  # monthly_cap = allocated
                last_reset,
                True
            )

            print(f"✓ Created {user['tier'].upper()} user:")
            print(f"  User ID: {user['user_id']}")
            print(f"  Email: {user['email']}")
            print(f"  Credits: {user['credits_remaining']}")
            print(f"  Expected Models: {user['description']}")
            print()

        # Verify creation
        print("\n" + "="*70)
        print("VERIFICATION - All Test Users Created:")
        print("="*70 + "\n")

        rows = await conn.fetch(
            """
            SELECT user_id, tier, credits_remaining, credits_allocated
            FROM user_credits
            WHERE user_id LIKE 'test-%'
            ORDER BY
                CASE tier
                    WHEN 'trial' THEN 1
                    WHEN 'starter' THEN 2
                    WHEN 'professional' THEN 3
                    WHEN 'enterprise' THEN 4
                END
            """
        )

        for row in rows:
            print(f"Tier: {row['tier'].upper():<15} "
                  f"User ID: {row['user_id']:<50} "
                  f"Credits: {row['credits_remaining']}")

        print("\n" + "="*70)
        print("SUCCESS - Test users created successfully!")
        print("="*70)

        # Save credentials to file
        credentials_file = os.path.join(os.path.dirname(__file__), "..", "tests", "test_users.json")
        os.makedirs(os.path.dirname(credentials_file), exist_ok=True)

        import json
        with open(credentials_file, 'w') as f:
            json.dump({
                "test_users": [
                    {
                        "user_id": user["user_id"],
                        "email": user["email"],
                        "tier": user["tier"],
                        "credits": str(user["credits_remaining"]),
                        "description": user["description"]
                    }
                    for user in TEST_USERS
                ],
                "created_at": datetime.utcnow().isoformat(),
                "database": f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
            }, f, indent=2)

        print(f"\n✓ Test user credentials saved to: {credentials_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await conn.close()
        print("\n✓ Database connection closed")


if __name__ == "__main__":
    asyncio.run(create_test_users())
