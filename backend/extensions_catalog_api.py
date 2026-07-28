"""
Extensions Catalog API
Browse and search marketplace extensions with filtering and categorization.
"""

import os
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

import asyncpg
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Router configuration
router = APIRouter(prefix="/api/v1/extensions", tags=["extensions-catalog"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AddOnResponse(BaseModel):
    """Add-on catalog response"""
    id: str
    name: str
    description: str
    category: str
    base_price: Decimal
    billing_type: str
    features: dict  # JSONB field
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Category with count"""
    category: str
    count: int


# =============================================================================
# Database Connection
# =============================================================================

async def get_db_connection():
    """Create database connection."""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db")
    )


# =============================================================================
# Catalog Endpoints
# =============================================================================

@router.get("/catalog")
async def list_addons(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    limit: int = Query(20, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List all available add-ons with optional filtering.

    - **category**: Filter by category (ai-services, infrastructure, etc.)
    - **search**: Search in name and description
    - **limit**: Max results (default 20, max 100)
    - **offset**: Pagination offset

    Returns: List[AddOnResponse]
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, name, description, category, base_price, billing_type,
                   features, is_active, created_at
            FROM add_ons
            WHERE is_active = TRUE
        """
        params = []

        if category:
            query += f" AND category = ${len(params) + 1}"
            params.append(category)

        if search:
            idx = len(params) + 1
            query += f" AND (name ILIKE ${idx} OR description ILIKE ${idx})"
            params.append(f"%{search}%")

        query += f" ORDER BY sort_order, name LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        # Convert rows to dict, handling JSONB and numeric types
        result = []
        for row in rows:
            addon = dict(row)
            # Ensure features is a dict (JSONB automatically decoded by asyncpg)
            if addon.get('features') is None:
                addon['features'] = {}
            result.append(addon)

        return result
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()


# ============================================================================
# ROUTE: List Categories
# ============================================================================

@router.get("/categories/list")
async def list_categories():
    """
    List all add-on categories with counts.

    Returns: List[CategoryResponse]
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT category, COUNT(*) as count
            FROM add_ons
            WHERE is_active = TRUE
            GROUP BY category
            ORDER BY category
        """
        rows = await conn.fetch(query)

        return [
            {"category": row["category"], "count": row["count"]}
            for row in rows
        ]
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/featured")
async def get_featured(
    limit: int = Query(6, le=20, description="Maximum featured add-ons to return")
):
    """
    Get featured add-ons.

    - **limit**: Max results (default 6, max 20)

    Returns: List[AddOnResponse]
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, name, description, category, base_price, billing_type, features
            FROM add_ons
            WHERE is_active = TRUE AND is_featured = TRUE
            ORDER BY sort_order
            LIMIT $1
        """
        rows = await conn.fetch(query, limit)

        # Convert rows to dict, handling JSONB
        result = []
        for row in rows:
            addon = dict(row)
            if addon.get('features') is None:
                addon['features'] = {}
            result.append(addon)

        return result
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/recommended")
async def get_recommended(
    user_tier: Optional[str] = Query(None, description="User's subscription tier")
):
    """
    Get recommended add-ons based on user tier.

    Note: Requires authentication in production to check user's installed add-ons.

    - **user_tier**: User's subscription tier (trial, starter, professional, enterprise)

    Returns: List[AddOnResponse]
    """
    conn = await get_db_connection()
    try:
        # Simple recommendation: show add-ons the user doesn't have
        # In production, this would check user_add_ons table against authenticated user
        # For now, just return top add-ons by sort order
        query = """
            SELECT id, name, description, category, base_price, billing_type, features
            FROM add_ons
            WHERE is_active = TRUE
            ORDER BY sort_order
            LIMIT 6
        """
        rows = await conn.fetch(query)

        # Convert rows to dict, handling JSONB
        result = []
        for row in rows:
            addon = dict(row)
            if addon.get('features') is None:
                addon['features'] = {}
            result.append(addon)

        return result
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/search")
async def search_addons(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    limit: int = Query(20, le=100, description="Maximum results to return")
):
    """
    Full-text search in add-ons with advanced filtering.

    - **q**: Search query (minimum 2 characters)
    - **category**: Filter by category
    - **min_price**: Minimum base price
    - **max_price**: Maximum base price
    - **limit**: Max results (default 20, max 100)

    Returns: List[AddOnResponse]
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, name, description, category, base_price, billing_type, features
            FROM add_ons
            WHERE is_active = TRUE
            AND (name ILIKE $1 OR description ILIKE $1)
        """
        params = [f"%{q}%"]

        if category:
            query += f" AND category = ${len(params)+1}"
            params.append(category)

        if min_price is not None:
            query += f" AND base_price >= ${len(params)+1}"
            params.append(min_price)

        if max_price is not None:
            query += f" AND base_price <= ${len(params)+1}"
            params.append(max_price)

        query += f" ORDER BY name LIMIT ${len(params)+1}"
        params.append(limit)

        rows = await conn.fetch(query, *params)

        # Convert rows to dict, handling JSONB
        result = []
        for row in rows:
            addon = dict(row)
            if addon.get('features') is None:
                addon['features'] = {}
            result.append(addon)

        return result
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()


# ============================================================================
# ROUTE: Get Single Add-On (MUST BE LAST - parameterized route)
# ============================================================================

@router.get("/{addon_id}")
async def get_addon(addon_id: int):
    """
    Get detailed information about specific add-on.

    - **addon_id**: Add-on ID (integer)

    Returns: AddOnResponse
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, name, description, category, base_price, billing_type,
                   features, is_active, created_at, updated_at
            FROM add_ons
            WHERE id = $1 AND is_active = TRUE
        """
        row = await conn.fetchrow(query, addon_id)

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Add-on ID {addon_id} not found"
            )

        addon = dict(row)
        # Ensure features is a dict
        if addon.get('features') is None:
            addon['features'] = {}

        return addon
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        await conn.close()
