"""
Pricing Packages API - Public pricing information endpoint

This module provides PUBLIC (no auth required) endpoints for:
- Subscription tier pricing
- Feature comparison
- Credit package pricing
- Add-on pricing

Used by:
- Marketing landing pages
- Signup flows
- Public pricing pages

Author: Claude Code
Date: November 29, 2025
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
import asyncpg

from dependencies import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/public/pricing", tags=["Public Pricing"])


# ============================================================================
# Pydantic Models for Response
# ============================================================================

class SubscriptionTierPublic(BaseModel):
    """Public subscription tier information"""
    tier_code: str
    tier_name: str
    display_name: str
    description: Optional[str] = None
    monthly_price_usd: Decimal
    annual_price_usd: Optional[Decimal] = None
    annual_discount_pct: Optional[int] = None
    features: List[str] = []
    api_calls_limit: Optional[int] = None
    is_popular: bool = False
    badge_text: Optional[str] = None
    sort_order: int = 0


class CreditPackagePublic(BaseModel):
    """Public credit package information"""
    package_code: str
    package_name: str
    description: Optional[str] = None
    credits: int
    price_usd: Decimal
    price_per_credit: Decimal
    discount_percentage: int = 0
    is_featured: bool = False
    badge_text: Optional[str] = None
    savings_text: Optional[str] = None


class AddOnPublic(BaseModel):
    """Public add-on information"""
    addon_code: str
    addon_name: str
    description: Optional[str] = None
    category: str
    monthly_price_usd: Optional[Decimal] = None
    one_time_price_usd: Optional[Decimal] = None
    features: List[str] = []
    icon_url: Optional[str] = None


class PricingComparisonResponse(BaseModel):
    """Complete pricing comparison for landing pages"""
    tiers: List[SubscriptionTierPublic]
    credit_packages: List[CreditPackagePublic]
    addons: List[AddOnPublic]
    currency: str = "USD"
    last_updated: str


# ============================================================================
# Public Endpoints (No Authentication Required)
# ============================================================================

@router.get("/tiers", response_model=List[SubscriptionTierPublic])
async def get_public_pricing_tiers(
    request: Request,
    include_features: bool = Query(True, description="Include feature lists")
):
    """
    Get public subscription tier pricing

    This endpoint is PUBLIC - no authentication required.
    Used for landing pages and pricing pages.

    Returns:
        List of subscription tiers with pricing and features
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            # Get tiers
            tiers_rows = await conn.fetch("""
                SELECT
                    tier_code,
                    tier_name,
                    display_name,
                    description,
                    monthly_price_usd,
                    annual_price_usd,
                    annual_discount_pct,
                    api_calls_limit,
                    is_popular,
                    badge_text,
                    sort_order
                FROM subscription_tiers
                WHERE is_public = true AND is_active = true
                ORDER BY sort_order, monthly_price_usd
            """)

            tiers = []
            for tier_row in tiers_rows:
                tier_dict = dict(tier_row)

                # Get features if requested
                if include_features:
                    features_rows = await conn.fetch("""
                        SELECT f.feature_name, f.description
                        FROM tier_features tf
                        JOIN features f ON tf.feature_key = f.feature_key
                        WHERE tf.tier_code = $1 AND tf.is_enabled = true
                        ORDER BY f.display_order
                    """, tier_row['tier_code'])

                    tier_dict['features'] = [
                        f"{row['feature_name']}: {row['description']}" if row['description']
                        else row['feature_name']
                        for row in features_rows
                    ]
                else:
                    tier_dict['features'] = []

                tiers.append(SubscriptionTierPublic(**tier_dict))

            logger.info(f"Retrieved {len(tiers)} public pricing tiers")
            return tiers

    except asyncpg.PostgresError as e:
        logger.error(f"Database error retrieving pricing tiers: {e}")
        # Return default tiers instead of failing
        return get_default_pricing_tiers()
    except Exception as e:
        logger.error(f"Error retrieving pricing tiers: {e}")
        return get_default_pricing_tiers()


@router.get("/packages", response_model=List[CreditPackagePublic])
async def get_credit_packages(request: Request):
    """
    Get credit package pricing

    This endpoint is PUBLIC - no authentication required.
    Shows available credit packages for purchase.

    Returns:
        List of credit packages with pricing
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            packages_rows = await conn.fetch("""
                SELECT
                    package_code,
                    package_name,
                    description,
                    credits,
                    price_usd,
                    discount_percentage,
                    is_featured,
                    badge_text,
                    display_order
                FROM credit_packages
                WHERE is_active = true
                ORDER BY display_order, credits
            """)

            packages = []
            for row in packages_rows:
                package_dict = dict(row)

                # Calculate price per credit
                price_per_credit = package_dict['price_usd'] / package_dict['credits']
                package_dict['price_per_credit'] = Decimal(str(round(price_per_credit, 4)))

                # Generate savings text if discounted
                if package_dict['discount_percentage'] > 0:
                    package_dict['savings_text'] = f"Save {package_dict['discount_percentage']}%"

                packages.append(CreditPackagePublic(**package_dict))

            logger.info(f"Retrieved {len(packages)} credit packages")
            return packages

    except Exception as e:
        logger.error(f"Error retrieving credit packages: {e}")
        return get_default_credit_packages()


@router.get("/addons", response_model=List[AddOnPublic])
async def get_public_addons(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get add-on pricing

    This endpoint is PUBLIC - no authentication required.
    Shows available add-ons and extensions.

    Args:
        category: Optional category filter (services, tools, integrations)

    Returns:
        List of add-ons with pricing
    """
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            query = """
                SELECT
                    slug as addon_code,
                    name as addon_name,
                    description,
                    category,
                    monthly_price_usd,
                    one_time_price_usd,
                    icon_url,
                    features
                FROM add_ons
                WHERE is_public = true AND is_active = true
            """

            params = []
            if category:
                query += " AND category = $1"
                params.append(category)

            query += " ORDER BY category, name"

            addons_rows = await conn.fetch(query, *params)

            addons = []
            for row in addons_rows:
                addon_dict = dict(row)

                # Parse features JSON if present
                if addon_dict.get('features'):
                    if isinstance(addon_dict['features'], dict):
                        addon_dict['features'] = [
                            f"{k}: {v}" for k, v in addon_dict['features'].items()
                        ]
                    elif isinstance(addon_dict['features'], list):
                        pass  # Already a list
                    else:
                        addon_dict['features'] = []
                else:
                    addon_dict['features'] = []

                addons.append(AddOnPublic(**addon_dict))

            logger.info(f"Retrieved {len(addons)} public add-ons")
            return addons

    except Exception as e:
        logger.error(f"Error retrieving add-ons: {e}")
        return []


@router.get("/comparison", response_model=PricingComparisonResponse)
async def get_pricing_comparison():
    """
    Get complete pricing comparison

    This endpoint is PUBLIC - no authentication required.
    Returns all pricing information for comparison pages.

    Returns:
        Complete pricing data including tiers, packages, and add-ons
    """
    from datetime import datetime

    try:
        tiers = await get_public_pricing_tiers(include_features=True)
        packages = await get_credit_packages()
        addons = await get_public_addons()

        return PricingComparisonResponse(
            tiers=tiers,
            credit_packages=packages,
            addons=addons,
            currency="USD",
            last_updated=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error building pricing comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pricing information")


# ============================================================================
# Default/Fallback Data
# ============================================================================

def get_default_pricing_tiers() -> List[SubscriptionTierPublic]:
    """Fallback pricing tiers if database unavailable"""
    return [
        SubscriptionTierPublic(
            tier_code="trial",
            tier_name="Trial",
            display_name="Trial Plan",
            description="Try Unicorn Commander for free",
            monthly_price_usd=Decimal("1.00"),
            features=[
                "100 API calls per day",
                "Basic AI models",
                "Community support"
            ],
            api_calls_limit=700,
            sort_order=0
        ),
        SubscriptionTierPublic(
            tier_code="starter",
            tier_name="Starter",
            display_name="Starter Plan",
            description="For individuals and small projects",
            monthly_price_usd=Decimal("19.00"),
            annual_price_usd=Decimal("190.00"),
            annual_discount_pct=17,
            features=[
                "1,000 API calls per month",
                "All AI models",
                "BYOK support",
                "Email support"
            ],
            api_calls_limit=1000,
            sort_order=1
        ),
        SubscriptionTierPublic(
            tier_code="professional",
            tier_name="Professional",
            display_name="Professional Plan",
            description="For power users and small teams",
            monthly_price_usd=Decimal("49.00"),
            annual_price_usd=Decimal("490.00"),
            annual_discount_pct=17,
            features=[
                "10,000 API calls per month",
                "All services (Chat, Search, TTS, STT)",
                "Priority support",
                "Advanced analytics"
            ],
            api_calls_limit=10000,
            is_popular=True,
            badge_text="Most Popular",
            sort_order=2
        ),
        SubscriptionTierPublic(
            tier_code="enterprise",
            tier_name="Enterprise",
            display_name="Enterprise Plan",
            description="For teams and organizations",
            monthly_price_usd=Decimal("99.00"),
            annual_price_usd=Decimal("990.00"),
            annual_discount_pct=17,
            features=[
                "Unlimited API calls",
                "Team management (5+ seats)",
                "Custom integrations",
                "24/7 dedicated support",
                "White-label options"
            ],
            api_calls_limit=None,
            badge_text="Best Value",
            sort_order=3
        )
    ]


def get_default_credit_packages() -> List[CreditPackagePublic]:
    """Fallback credit packages if database unavailable"""
    return [
        CreditPackagePublic(
            package_code="small",
            package_name="Small Package",
            description="Perfect for occasional use",
            credits=100,
            price_usd=Decimal("10.00"),
            price_per_credit=Decimal("0.1000"),
            discount_percentage=0
        ),
        CreditPackagePublic(
            package_code="medium",
            package_name="Medium Package",
            description="Great for regular users",
            credits=500,
            price_usd=Decimal("45.00"),
            price_per_credit=Decimal("0.0900"),
            discount_percentage=10,
            savings_text="Save 10%"
        ),
        CreditPackagePublic(
            package_code="large",
            package_name="Large Package",
            description="Best value for heavy users",
            credits=1000,
            price_usd=Decimal("80.00"),
            price_per_credit=Decimal("0.0800"),
            discount_percentage=20,
            is_featured=True,
            badge_text="Best Value",
            savings_text="Save 20%"
        )
    ]


logger.info("Pricing Packages API initialized")
