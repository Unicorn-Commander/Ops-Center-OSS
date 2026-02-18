#!/usr/bin/env python3
"""
Setup Stripe Products for Credit Packages

This script creates Stripe products and prices for all credit packages
defined in the database. It updates the database with the Stripe IDs.

Usage:
    python3 setup_stripe_credit_products.py

Requirements:
    - STRIPE_SECRET_KEY environment variable
    - Database connection configured

Author: Backend Team Lead
Date: November 12, 2025
"""

import os
import sys
import asyncio
import asyncpg
import stripe
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

if not stripe.api_key:
    print("ERROR: STRIPE_SECRET_KEY environment variable not set")
    sys.exit(1)


async def get_db_connection():
    """Create database connection pool"""
    return await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db"),
        min_size=1,
        max_size=2
    )


async def get_credit_packages(pool) -> List[Dict[str, Any]]:
    """Fetch all credit packages from database"""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, package_code, package_name, description,
                   credits, price_usd, discount_percentage,
                   stripe_product_id, stripe_price_id
            FROM credit_packages
            WHERE is_active = TRUE
            ORDER BY display_order
            """
        )

        packages = []
        for row in rows:
            packages.append({
                "id": str(row["id"]),
                "package_code": row["package_code"],
                "package_name": row["package_name"],
                "description": row["description"],
                "credits": row["credits"],
                "price_usd": float(row["price_usd"]),
                "discount_percentage": row["discount_percentage"],
                "stripe_product_id": row["stripe_product_id"],
                "stripe_price_id": row["stripe_price_id"]
            })

        return packages


async def create_or_update_stripe_product(package: Dict[str, Any]) -> Dict[str, str]:
    """
    Create or update Stripe product and price for a credit package

    Returns dict with stripe_product_id and stripe_price_id
    """
    print(f"\n{'='*80}")
    print(f"Processing: {package['package_name']}")
    print(f"{'='*80}")

    # Prepare product data
    product_name = package["package_name"]
    product_description = f"{package['credits']:,} credits"
    if package.get("description"):
        product_description += f" - {package['description']}"
    if package["discount_percentage"] > 0:
        product_description += f" ({package['discount_percentage']}% discount)"

    metadata = {
        "package_code": package["package_code"],
        "credits": str(package["credits"]),
        "discount_percentage": str(package["discount_percentage"]),
        "source": "ops-center-credit-purchase"
    }

    # Create or update product
    stripe_product_id = package.get("stripe_product_id")

    if stripe_product_id:
        try:
            # Update existing product
            product = stripe.Product.modify(
                stripe_product_id,
                name=product_name,
                description=product_description,
                metadata=metadata
            )
            print(f"✓ Updated existing product: {product.id}")
        except stripe.error.InvalidRequestError:
            print(f"⚠ Product {stripe_product_id} not found, creating new one...")
            stripe_product_id = None

    if not stripe_product_id:
        # Create new product
        product = stripe.Product.create(
            name=product_name,
            description=product_description,
            metadata=metadata
        )
        stripe_product_id = product.id
        print(f"✓ Created new product: {product.id}")

    # Create price (always create new price, Stripe prices are immutable)
    price_cents = int(package["price_usd"] * 100)

    # Check if we already have a price with this exact amount
    stripe_price_id = package.get("stripe_price_id")
    create_new_price = True

    if stripe_price_id:
        try:
            existing_price = stripe.Price.retrieve(stripe_price_id)
            if existing_price.unit_amount == price_cents and existing_price.product == stripe_product_id:
                print(f"✓ Using existing price: {stripe_price_id} (${package['price_usd']:.2f})")
                create_new_price = False
        except stripe.error.InvalidRequestError:
            print(f"⚠ Price {stripe_price_id} not found, creating new one...")

    if create_new_price:
        price = stripe.Price.create(
            product=stripe_product_id,
            unit_amount=price_cents,
            currency="usd",
            metadata={
                "package_code": package["package_code"],
                "credits": str(package["credits"])
            }
        )
        stripe_price_id = price.id
        print(f"✓ Created new price: {price.id} (${package['price_usd']:.2f})")

    print(f"\nResults:")
    print(f"  Product ID: {stripe_product_id}")
    print(f"  Price ID:   {stripe_price_id}")
    print(f"  Amount:     ${package['price_usd']:.2f} USD")
    print(f"  Credits:    {package['credits']:,}")

    return {
        "stripe_product_id": stripe_product_id,
        "stripe_price_id": stripe_price_id
    }


async def update_database(pool, package_id: str, stripe_ids: Dict[str, str]):
    """Update database with Stripe IDs"""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE credit_packages
            SET stripe_product_id = $1,
                stripe_price_id = $2,
                updated_at = NOW()
            WHERE id = $3
            """,
            stripe_ids["stripe_product_id"],
            stripe_ids["stripe_price_id"],
            package_id
        )


async def main():
    """Main execution"""
    print("=" * 80)
    print("Stripe Credit Package Setup")
    print("=" * 80)

    try:
        # Connect to database
        print("\nConnecting to database...")
        pool = await get_db_connection()
        print("✓ Database connected")

        # Fetch packages
        print("\nFetching credit packages...")
        packages = await get_credit_packages(pool)
        print(f"✓ Found {len(packages)} active credit packages")

        if not packages:
            print("\n⚠ No active credit packages found in database")
            print("Run the database migration first: add_credit_purchases.sql")
            return

        # Process each package
        print("\n" + "=" * 80)
        print("Creating/Updating Stripe Products")
        print("=" * 80)

        for package in packages:
            try:
                stripe_ids = await create_or_update_stripe_product(package)
                await update_database(pool, package["id"], stripe_ids)
                print("✓ Database updated with Stripe IDs")

            except stripe.error.StripeError as e:
                print(f"✗ Stripe error: {e}")
                continue
            except Exception as e:
                print(f"✗ Error: {e}")
                continue

        # Summary
        print("\n" + "=" * 80)
        print("Setup Complete!")
        print("=" * 80)
        print(f"\nProcessed {len(packages)} credit packages")
        print("\nNext steps:")
        print("1. Configure Stripe webhook endpoint:")
        print("   URL: https://unicorncommander.ai/api/v1/billing/credits/webhook")
        print("   Events: checkout.session.completed")
        print("2. Update STRIPE_WEBHOOK_SECRET_CREDITS in .env.auth")
        print("3. Restart ops-center-direct container")
        print("\nStripe Dashboard: https://dashboard.stripe.com/test/products")

        await pool.close()

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
