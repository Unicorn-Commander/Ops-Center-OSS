#!/usr/bin/env python3
"""
Stripe Product Setup Script for UC-1 Pro
Creates products and price points in Stripe for all subscription tiers

Run this script once to set up your Stripe account with UC-1 Pro products.
It will create 4 products (Trial, Starter, Professional, Enterprise) with
monthly and yearly pricing.

Usage:
    python setup_stripe_products.py

Environment Variables Required:
    STRIPE_API_KEY - Your Stripe secret API key
"""

import os
import sys
import stripe
from typing import Dict, List, Tuple
import json

# Import subscription plans
from subscription_manager import DEFAULT_PLANS

# Initialize Stripe
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")

if not STRIPE_API_KEY:
    print("ERROR: STRIPE_API_KEY environment variable not set")
    print("Please set your Stripe secret key:")
    print("  export STRIPE_API_KEY='sk_test_...'")
    sys.exit(1)

stripe.api_key = STRIPE_API_KEY


def create_product(name: str, description: str, metadata: Dict[str, str]) -> stripe.Product:
    """
    Create a Stripe product

    Args:
        name: Product name
        description: Product description
        metadata: Additional metadata

    Returns:
        Stripe Product object
    """
    try:
        product = stripe.Product.create(
            name=name,
            description=description,
            metadata=metadata
        )
        print(f"✓ Created product: {name} (ID: {product.id})")
        return product
    except stripe.error.StripeError as e:
        print(f"✗ Failed to create product {name}: {e}")
        sys.exit(1)


def create_price(
    product_id: str,
    amount: int,
    interval: str,
    nickname: str,
    metadata: Dict[str, str]
) -> stripe.Price:
    """
    Create a Stripe price

    Args:
        product_id: Stripe product ID
        amount: Amount in cents
        interval: Billing interval (month or year)
        nickname: Price nickname
        metadata: Additional metadata

    Returns:
        Stripe Price object
    """
    try:
        price = stripe.Price.create(
            product=product_id,
            unit_amount=amount,
            currency='usd',
            recurring={'interval': interval},
            nickname=nickname,
            metadata=metadata
        )
        print(f"  ✓ Created {interval}ly price: ${amount/100:.2f} (ID: {price.id})")
        return price
    except stripe.error.StripeError as e:
        print(f"  ✗ Failed to create price: {e}")
        sys.exit(1)


def setup_stripe_products() -> Dict[str, Dict[str, str]]:
    """
    Set up all Stripe products and prices for UC-1 Pro

    Returns:
        Dictionary mapping tier IDs to their price IDs
    """
    print("\n" + "="*60)
    print("UC-1 Pro Stripe Product Setup")
    print("="*60 + "\n")

    price_mapping = {}

    for plan in DEFAULT_PLANS:
        print(f"\nSetting up tier: {plan.display_name}")
        print("-" * 40)

        # Create product
        product = create_product(
            name=f"UC-1 Pro - {plan.display_name}",
            description=", ".join(plan.features[:3]),  # First 3 features
            metadata={
                "tier_id": plan.id,
                "tier_name": plan.name,
                "api_calls_limit": str(plan.api_calls_limit),
                "byok_enabled": str(plan.byok_enabled),
                "priority_support": str(plan.priority_support),
                "team_seats": str(plan.team_seats)
            }
        )

        # Create monthly price
        monthly_amount = int(plan.price_monthly * 100)  # Convert to cents
        monthly_price = create_price(
            product_id=product.id,
            amount=monthly_amount,
            interval='month',
            nickname=f"{plan.display_name} - Monthly",
            metadata={
                "tier_id": plan.id,
                "billing_cycle": "monthly"
            }
        )

        # Create yearly price if available
        yearly_price_id = None
        if plan.price_yearly:
            yearly_amount = int(plan.price_yearly * 100)  # Convert to cents
            yearly_price = create_price(
                product_id=product.id,
                amount=yearly_amount,
                interval='year',
                nickname=f"{plan.display_name} - Yearly",
                metadata={
                    "tier_id": plan.id,
                    "billing_cycle": "yearly"
                }
            )
            yearly_price_id = yearly_price.id

        # Store price IDs
        price_mapping[plan.id] = {
            "product_id": product.id,
            "monthly_price_id": monthly_price.id,
            "yearly_price_id": yearly_price_id
        }

    return price_mapping


def print_summary(price_mapping: Dict[str, Dict[str, str]]):
    """
    Print summary of created products and next steps

    Args:
        price_mapping: Dictionary of price IDs
    """
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60 + "\n")

    print("Created Products and Prices:")
    print("-" * 60)

    for tier_id, ids in price_mapping.items():
        plan = next((p for p in DEFAULT_PLANS if p.id == tier_id), None)
        if plan:
            print(f"\n{plan.display_name} ({tier_id}):")
            print(f"  Product ID:       {ids['product_id']}")
            print(f"  Monthly Price ID: {ids['monthly_price_id']}")
            if ids['yearly_price_id']:
                print(f"  Yearly Price ID:  {ids['yearly_price_id']}")

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60 + "\n")

    print("1. Update subscription_manager.py with Stripe price IDs:")
    print("\n   You need to add the monthly price IDs to each plan's stripe_price_id field.")
    print("   Edit subscription_manager.py and update DEFAULT_PLANS:\n")

    for tier_id, ids in price_mapping.items():
        print(f"   # {tier_id}")
        print(f"   stripe_price_id=\"{ids['monthly_price_id']}\",")

    print("\n2. Set up Stripe webhook endpoint:")
    print("   - Go to: https://dashboard.stripe.com/webhooks")
    print("   - Add endpoint: https://unicorncommander.ai/api/v1/billing/webhooks/stripe")
    print("   - Select events:")
    print("     • checkout.session.completed")
    print("     • customer.subscription.created")
    print("     • customer.subscription.updated")
    print("     • customer.subscription.deleted")
    print("     • invoice.paid")
    print("     • invoice.payment_failed")
    print("   - Copy the webhook signing secret")

    print("\n3. Update environment variables:")
    print("   Add to your .env file:")
    print(f"   STRIPE_API_KEY={STRIPE_API_KEY[:20]}...")
    print("   STRIPE_WEBHOOK_SECRET=whsec_... (from webhook setup)")
    print("   STRIPE_SUCCESS_URL=https://unicorncommander.ai/billing/success")
    print("   STRIPE_CANCEL_URL=https://unicorncommander.ai/billing/canceled")

    print("\n4. Save price mapping (optional):")
    print("   This information has been saved to stripe_price_mapping.json")

    # Save to file
    with open('stripe_price_mapping.json', 'w') as f:
        json.dump(price_mapping, f, indent=2)

    print("\n" + "="*60 + "\n")


def main():
    """Main execution"""
    try:
        # Check if running in test mode
        if stripe.api_key.startswith('sk_test_'):
            print("⚠️  Running in TEST mode")
            print("   Using Stripe test API key")
        else:
            print("✓ Running in LIVE mode")
            print("  Using Stripe live API key")

        response = input("\nContinue? (yes/no): ")
        if response.lower() != 'yes':
            print("Setup canceled")
            sys.exit(0)

        # Set up products
        price_mapping = setup_stripe_products()

        # Print summary
        print_summary(price_mapping)

    except KeyboardInterrupt:
        print("\n\nSetup canceled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
