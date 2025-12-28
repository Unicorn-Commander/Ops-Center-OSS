"""
Dynamic Pricing API - RESTful endpoints for pricing configuration

This module provides admin and user endpoints for:
- BYOK pricing rule management
- Platform pricing rule management
- Credit package management
- Pricing analytics and dashboards
- Cost calculation and preview

Author: System Architecture Designer
Date: January 12, 2025
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator
import asyncpg

from pricing_engine import get_pricing_engine, PricingEngine
from dependencies import get_db_pool, require_admin, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pricing", tags=["Dynamic Pricing"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class BYOKRuleCreate(BaseModel):
    provider: str = Field(..., pattern=r'^[a-z0-9_*]+$', max_length=50)
    markup_type: str = Field('percentage', pattern=r'^(percentage|fixed|none)$')
    markup_value: Decimal = Field(..., ge=0, le=1.0)
    min_charge: Decimal = Field(0.001, ge=0.0001, le=1.0)
    free_credits_monthly: Decimal = Field(0.0, ge=0)
    applies_to_tiers: List[str] = ['trial', 'starter', 'professional', 'enterprise']
    rule_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: int = Field(0, ge=0, le=100)

    @validator('markup_value')
    def validate_markup(cls, v, values):
        if values.get('markup_type') == 'percentage' and v > 1.0:
            raise ValueError("Percentage markup cannot exceed 100%")
        return v


class BYOKRuleUpdate(BaseModel):
    markup_value: Optional[Decimal] = Field(None, ge=0, le=1.0)
    min_charge: Optional[Decimal] = Field(None, ge=0.0001, le=1.0)
    free_credits_monthly: Optional[Decimal] = Field(None, ge=0)
    applies_to_tiers: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PlatformRuleUpdate(BaseModel):
    markup_value: Optional[Decimal] = Field(None, ge=0, le=2.0)
    provider_overrides: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CreditPackageCreate(BaseModel):
    package_code: str = Field(..., pattern=r'^[a-z0-9_]+$', max_length=50)
    package_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    credits: int = Field(..., gt=0)
    price_usd: Decimal = Field(..., gt=0)
    discount_percentage: int = Field(0, ge=0, le=100)
    display_order: int = Field(0, ge=0)
    is_featured: bool = False
    badge_text: Optional[str] = Field(None, max_length=50)
    available_to_tiers: List[str] = ['trial', 'starter', 'professional', 'enterprise']
    tags: List[str] = []


class CreditPackageUpdate(BaseModel):
    package_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price_usd: Optional[Decimal] = Field(None, gt=0)
    discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    is_featured: Optional[bool] = None
    badge_text: Optional[str] = Field(None, max_length=50)


class PromotionalPricing(BaseModel):
    promo_price: Decimal = Field(..., gt=0)
    promo_code: str = Field(..., max_length=50)
    promo_start_date: datetime
    promo_end_date: datetime


class CostCalculationRequest(BaseModel):
    provider: str
    model: str
    tokens_used: int = Field(..., gt=0)
    user_tier: str = Field('professional', pattern=r'^(trial|starter|professional|enterprise)$')


# ============================================================================
# BYOK Pricing Rule Endpoints
# ============================================================================

@router.get("/rules/byok")
async def list_byok_rules(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    is_active: bool = Query(True, description="Filter by active status"),
    include_inactive: bool = Query(False, description="Include inactive rules"),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """List all BYOK pricing rules."""
    async with db_pool.acquire() as conn:
        query = """
            SELECT * FROM pricing_rules
            WHERE rule_type = 'byok'
        """
        params = []

        if provider:
            query += " AND provider = $1"
            params.append(provider)

        if not include_inactive:
            query += f" AND is_active = ${len(params) + 1}"
            params.append(is_active)

        query += " ORDER BY priority DESC, provider"

        rows = await conn.fetch(query, *params)

        return {
            "rules": [dict(row) for row in rows],
            "total": len(rows)
        }


@router.post("/rules/byok")
async def create_byok_rule(
    rule: BYOKRuleCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    admin: bool = Depends(require_admin)
):
    """Create new BYOK pricing rule."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO pricing_rules (
                rule_type, provider, markup_type, markup_value, min_charge,
                free_credits_monthly, applies_to_tiers, rule_name, description,
                priority, created_by, updated_by
            )
            VALUES (
                'byok', $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10
            )
            RETURNING *
            """,
            rule.provider, rule.markup_type, rule.markup_value, rule.min_charge,
            rule.free_credits_monthly, rule.applies_to_tiers, rule.rule_name,
            rule.description, rule.priority, current_user.get("user_id")
        )

        return dict(row)


@router.put("/rules/byok/{rule_id}")
async def update_byok_rule(
    rule_id: UUID,
    updates: BYOKRuleUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    admin: bool = Depends(require_admin)
):
    """Update existing BYOK pricing rule."""
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        param_idx = 1

        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_by
        update_fields.append(f"updated_by = ${param_idx}")
        params.append(current_user.get("user_id"))
        param_idx += 1

        # Add updated_at
        update_fields.append(f"updated_at = NOW()")

        # Add rule_id for WHERE clause
        params.append(str(rule_id))

        query = f"""
            UPDATE pricing_rules
            SET {', '.join(update_fields)}
            WHERE id = ${param_idx} AND rule_type = 'byok'
            RETURNING *
        """

        row = await conn.fetchrow(query, *params)

        if not row:
            raise HTTPException(status_code=404, detail="BYOK rule not found")

        return dict(row)


@router.delete("/rules/byok/{rule_id}")
async def delete_byok_rule(
    rule_id: UUID,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Delete BYOK pricing rule."""
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM pricing_rules
            WHERE id = $1 AND rule_type = 'byok'
            """,
            str(rule_id)
        )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="BYOK rule not found")

        return {"status": "deleted", "rule_id": str(rule_id)}


# ============================================================================
# Platform Pricing Rule Endpoints
# ============================================================================

@router.get("/rules/platform")
async def list_platform_rules(
    tier_code: Optional[str] = Query(None, description="Filter by tier"),
    is_active: bool = Query(True, description="Filter by active status"),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """List all Platform pricing rules."""
    async with db_pool.acquire() as conn:
        query = """
            SELECT * FROM pricing_rules
            WHERE rule_type = 'platform'
        """
        params = []

        if tier_code:
            query += " AND tier_code = $1"
            params.append(tier_code)

        query += f" AND is_active = ${len(params) + 1}"
        params.append(is_active)

        query += " ORDER BY tier_code"

        rows = await conn.fetch(query, *params)

        return {
            "rules": [dict(row) for row in rows],
            "total": len(rows)
        }


@router.put("/rules/platform/{tier_code}")
async def update_platform_rule(
    tier_code: str,
    updates: PlatformRuleUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    admin: bool = Depends(require_admin)
):
    """Update Platform pricing rule for specific tier."""
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        param_idx = 1

        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_by
        update_fields.append(f"updated_by = ${param_idx}")
        params.append(current_user.get("user_id"))
        param_idx += 1

        # Add updated_at
        update_fields.append(f"updated_at = NOW()")

        # Add tier_code for WHERE clause
        params.append(tier_code)

        query = f"""
            UPDATE pricing_rules
            SET {', '.join(update_fields)}
            WHERE tier_code = ${param_idx} AND rule_type = 'platform'
            RETURNING *
        """

        row = await conn.fetchrow(query, *params)

        if not row:
            raise HTTPException(status_code=404, detail="Platform rule not found")

        return dict(row)


# ============================================================================
# Cost Calculation Endpoints
# ============================================================================

@router.post("/calculate/byok")
async def calculate_byok_cost_preview(
    request: CostCalculationRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user),
    admin: bool = Depends(require_admin)
):
    """Calculate BYOK cost preview (admin testing)."""
    engine = await get_pricing_engine(db_pool)

    # Mock base cost calculation
    base_cost = Decimal(str(request.tokens_used / 1000 * 0.01))

    result = await engine.calculate_byok_cost(
        provider=request.provider,
        base_cost=base_cost,
        user_tier=request.user_tier,
        user_id=current_user.get("user_id"),
        model=request.model,
        tokens_used=request.tokens_used
    )

    return result


@router.post("/calculate/platform")
async def calculate_platform_cost_preview(
    request: CostCalculationRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Calculate Platform cost preview (admin testing)."""
    engine = await get_pricing_engine(db_pool)

    result = await engine.calculate_platform_cost(
        provider=request.provider,
        model=request.model,
        tokens_used=request.tokens_used,
        user_tier=request.user_tier
    )

    return result


@router.post("/calculate/comparison")
async def calculate_cost_comparison(
    request: CostCalculationRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """Calculate side-by-side BYOK vs Platform cost comparison."""
    engine = await get_pricing_engine(db_pool)

    result = await engine.calculate_cost_comparison(
        provider=request.provider,
        model=request.model,
        tokens_used=request.tokens_used,
        user_tier=request.user_tier,
        user_id=current_user.get("user_id")
    )

    return result


# ============================================================================
# Credit Package Management Endpoints
# ============================================================================

@router.get("/packages")
async def list_credit_packages(
    is_active: bool = Query(True, description="Filter by active status"),
    include_inactive: bool = Query(False, description="Include inactive packages"),
    tier: Optional[str] = Query(None, description="Filter by available tier"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """List all credit packages."""
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM credit_packages WHERE 1=1"
        params = []

        if not include_inactive:
            query += f" AND is_active = ${len(params) + 1}"
            params.append(is_active)

        if tier:
            query += f" AND ${len(params) + 1} = ANY(available_to_tiers)"
            params.append(tier)

        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            query += f" AND tags && ${len(params) + 1}"
            params.append(tag_list)

        query += " ORDER BY display_order, credits"

        rows = await conn.fetch(query, *params)

        return {
            "packages": [dict(row) for row in rows],
            "total": len(rows)
        }


@router.post("/packages")
async def create_credit_package(
    package: CreditPackageCreate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Create new credit package."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO credit_packages (
                package_code, package_name, description, credits, price_usd,
                discount_percentage, display_order, is_featured, badge_text,
                available_to_tiers, tags
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
            """,
            package.package_code, package.package_name, package.description,
            package.credits, package.price_usd, package.discount_percentage,
            package.display_order, package.is_featured, package.badge_text,
            package.available_to_tiers, package.tags
        )

        return dict(row)


@router.put("/packages/{package_id}")
async def update_credit_package(
    package_id: UUID,
    updates: CreditPackageUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Update credit package."""
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        update_fields = []
        params = []
        param_idx = 1

        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_at
        update_fields.append(f"updated_at = NOW()")

        # Add package_id for WHERE clause
        params.append(str(package_id))

        query = f"""
            UPDATE credit_packages
            SET {', '.join(update_fields)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        row = await conn.fetchrow(query, *params)

        if not row:
            raise HTTPException(status_code=404, detail="Package not found")

        return dict(row)


@router.post("/packages/{package_id}/promo")
async def add_promotional_pricing(
    package_id: UUID,
    promo: PromotionalPricing,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Add promotional pricing to package."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE credit_packages
            SET promo_price = $1,
                promo_code = $2,
                promo_start_date = $3,
                promo_end_date = $4,
                updated_at = NOW()
            WHERE id = $5
            RETURNING *
            """,
            promo.promo_price, promo.promo_code, promo.promo_start_date,
            promo.promo_end_date, str(package_id)
        )

        if not row:
            raise HTTPException(status_code=404, detail="Package not found")

        return dict(row)


# ============================================================================
# Analytics & Dashboard Endpoints
# ============================================================================

@router.get("/dashboard/overview")
async def get_pricing_overview(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    admin: bool = Depends(require_admin)
):
    """Get pricing dashboard overview."""
    async with db_pool.acquire() as conn:
        # Count active rules
        byok_rules = await conn.fetchval(
            "SELECT COUNT(*) FROM pricing_rules WHERE rule_type = 'byok' AND is_active = TRUE"
        )
        platform_rules = await conn.fetchval(
            "SELECT COUNT(*) FROM pricing_rules WHERE rule_type = 'platform' AND is_active = TRUE"
        )
        active_packages = await conn.fetchval(
            "SELECT COUNT(*) FROM credit_packages WHERE is_active = TRUE"
        )

        # Count users with BYOK
        users_with_byok = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM user_byok_credits"
        )

        # Sum total BYOK credits
        total_allocated = await conn.fetchval(
            "SELECT COALESCE(SUM(monthly_allowance), 0) FROM user_byok_credits"
        )
        total_used = await conn.fetchval(
            "SELECT COALESCE(SUM(credits_used), 0) FROM user_byok_credits"
        )

        return {
            "summary": {
                "byok_rules_active": byok_rules,
                "platform_rules_active": platform_rules,
                "credit_packages_active": active_packages,
                "users_with_byok": users_with_byok,
                "total_byok_credits_allocated": float(total_allocated),
                "total_byok_credits_used": float(total_used),
                "avg_byok_utilization": f"{(total_used / total_allocated * 100):.1f}%" if total_allocated > 0 else "0%"
            }
        }


@router.get("/users/{user_id}/byok/balance")
async def get_user_byok_balance(
    user_id: str,
    tier_code: str = Query(..., description="User's tier code"),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    """Get user's BYOK credit balance."""
    # Verify user can only access their own data (unless admin)
    if current_user.get("user_id") != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    engine = await get_pricing_engine(db_pool)
    balance = await engine.get_byok_balance(user_id, tier_code)

    return balance
