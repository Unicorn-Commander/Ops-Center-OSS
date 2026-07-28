#!/usr/bin/env python3
"""Create Ops-Center TEST products/prices and print database mappings."""

import asyncio
import json
import os
import sys
from decimal import Decimal

import asyncpg
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
SUITE = os.getenv("OPS_CENTER_STRIPE_SUITE", "unicorn-commander")

TIERS = [
    {
        "code": "free",
        "name": "Free",
        "description": "On-device or bring-your-own AI with local storage.",
        "monthly": Decimal("0.00"),
        "annual": Decimal("0.00"),
    },
    {
        "code": "app",
        "name": "App (Meeting + Contact)",
        "description": "Meeting-Ops and Contact-Ops with MCP and starter credits.",
        "monthly": Decimal("15.00"),
        "annual": Decimal("150.00"),
    },
    {
        "code": "byok",
        "name": "Suite - BYOK",
        "description": "All apps and MCP using customer-provided model keys.",
        "monthly": Decimal("49.00"),
        "annual": Decimal("490.00"),
    },
    {
        "code": "managed",
        "name": "Suite - Managed",
        "description": "All apps, MCP, hosted inference, and included credits.",
        "monthly": Decimal("65.00"),
        "annual": Decimal("650.00"),
    },
]


def require_test_key() -> None:
    if not STRIPE_SECRET_KEY:
        raise SystemExit("STRIPE_SECRET_KEY is required")
    if not STRIPE_SECRET_KEY.startswith("sk_test_"):
        raise SystemExit("Refusing to run: STRIPE_SECRET_KEY must be a Stripe TEST secret key")
    stripe.api_key = STRIPE_SECRET_KEY


def cents(amount: Decimal) -> int:
    return int(amount * 100)


def create_product_and_prices(item: dict, kind: str) -> dict:
    metadata = {"suite": SUITE, "catalog_type": kind, "catalog_code": item["code"]}
    product = stripe.Product.create(
        name=f"Unicorn Commander — {item['name']}",
        description=item["description"],
        metadata=metadata,
    )
    result = {"product_id": product.id}
    for cycle, interval in (("monthly", "month"), ("annual", "year")):
        amount = item.get(cycle)
        if amount is None:
            continue
        price = stripe.Price.create(
            product=product.id,
            currency="usd",
            unit_amount=cents(amount),
            recurring={"interval": interval},
            nickname=f"{item['name']} — {cycle.title()}",
            metadata={**metadata, "billing_cycle": cycle},
        )
        result[f"{cycle}_price_id"] = price.id
    return result


async def load_addons() -> list[dict]:
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db"),
    )
    try:
        rows = await conn.fetch(
            """
            SELECT slug, name, description, base_price, billing_type
            FROM add_ons
            WHERE is_active = TRUE AND is_public = TRUE AND base_price > 0
            ORDER BY sort_order, name
            """
        )
    finally:
        await conn.close()

    addons = []
    for row in rows:
        billing_type = row["billing_type"] or "monthly"
        if billing_type not in {"monthly", "annual"}:
            print(f"Skipping {row['slug']}: unsupported recurring billing_type={billing_type}")
            continue
        base_price = Decimal(str(row["base_price"]))
        monthly = base_price if billing_type == "monthly" else (base_price / Decimal("10"))
        annual = base_price if billing_type == "annual" else (base_price * Decimal("10"))
        item = {
            "code": row["slug"],
            "name": row["name"],
            "description": row["description"] or f"{row['name']} add-on",
            "monthly": monthly,
            "annual": annual,
        }
        addons.append(item)
    return addons


async def main() -> None:
    require_test_key()
    print("Stripe TEST mode confirmed. No live resources will be created.")

    mapping = {"tiers": {}, "addons": {}}
    for tier in TIERS:
        mapping["tiers"][tier["code"]] = create_product_and_prices(tier, "tier")

    for addon in await load_addons():
        mapping["addons"][addon["code"]] = create_product_and_prices(addon, "addon")

    print("\nCreated mapping:")
    print(json.dumps(mapping, indent=2))
    print("\nPaste-ready tier price update:")
    for code, ids in mapping["tiers"].items():
        print(
            "UPDATE subscription_tiers SET "
            f"stripe_price_monthly = '{ids.get('monthly_price_id')}', "
            f"stripe_price_yearly = '{ids.get('annual_price_id')}' "
            f"WHERE tier_code = '{code}';"
        )
    print("\nAdd-on Stripe IDs are printed above for the owner to persist in the catalog schema.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
