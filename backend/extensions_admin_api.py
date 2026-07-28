"""
Extensions Marketplace - Admin API
===================================
Admin-only endpoints for managing add-ons, analytics, and promotional codes.

Requires admin role verification through Keycloak session.
"""

import os
import asyncpg
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/extensions", tags=["extensions-admin"])

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

async def get_db_connection():
    """Create asyncpg connection to PostgreSQL database"""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db")
    )

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

async def get_current_admin(request: Request) -> str:
    """
    Verify user is admin through Keycloak session.

    TODO: In production, implement proper role check:
    1. Extract session_token from cookies
    2. Validate with Keycloak
    3. Check for 'admin' role in user's realm roles
    4. Return user ID if admin, otherwise raise 403

    Current implementation allows all authenticated users (DEV ONLY).
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Admin access required."
        )

    # TODO: Implement Keycloak role verification
    # For now, extract user_id from session or use placeholder
    # In production, this should call Keycloak's token introspection endpoint

    # SECURITY WARNING: Replace this with actual role check
    admin_id = "admin-user-123"  # Placeholder

    logger.info(f"Admin access granted to user: {admin_id}")
    return admin_id

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateAddOnRequest(BaseModel):
    """Request model for creating a new add-on"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    base_price: Decimal = Field(..., ge=0)
    billing_type: str = Field(default="monthly")
    features: Dict[str, Any] = Field(default_factory=dict)

    @validator('billing_type')
    def validate_billing_type(cls, v):
        allowed = ['one_time', 'monthly', 'yearly']
        if v not in allowed:
            raise ValueError(f"billing_type must be one of: {', '.join(allowed)}")
        return v

    @validator('features')
    def validate_features(cls, v):
        # Ensure features is valid JSON-serializable
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            raise ValueError("features must be JSON-serializable")


class UpdateAddOnRequest(BaseModel):
    """Request model for updating an add-on"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    base_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    features: Optional[Dict[str, Any]] = None

    @validator('features')
    def validate_features(cls, v):
        if v is not None:
            try:
                json.dumps(v)
                return v
            except (TypeError, ValueError):
                raise ValueError("features must be JSON-serializable")
        return v


class CreatePromoCodeRequest(BaseModel):
    """Request model for creating a promotional code"""
    code: str = Field(..., min_length=3, max_length=50)
    discount_type: str = Field(...)
    discount_value: Decimal = Field(..., ge=0)
    max_uses: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = None

    @validator('discount_type')
    def validate_discount_type(cls, v):
        if v not in ['percentage', 'fixed_amount']:
            raise ValueError("discount_type must be 'percentage' or 'fixed_amount'")
        return v

    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values and values['discount_type'] == 'percentage':
            if v < 0 or v > 100:
                raise ValueError("Percentage discount must be between 0 and 100")
        return v

    @validator('code')
    def validate_code_format(cls, v):
        # Ensure code is alphanumeric with optional hyphens/underscores
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Code must be alphanumeric (hyphens and underscores allowed)")
        return v.upper()


class AnalyticsResponse(BaseModel):
    """Response model for analytics data"""
    total_revenue: float
    total_purchases: int
    top_sellers: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    period: Dict[str, datetime]


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.post("", response_model=Dict[str, Any])
async def create_addon(
    addon: CreateAddOnRequest,
    request: Request,
    admin_id: str = Depends(get_current_admin)
):
    """
    Create new add-on (admin only)

    Creates a new add-on in the marketplace with specified details.
    The add-on is automatically set to active status.

    Args:
        addon: Add-on creation details
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        Dict containing created add-on details

    Raises:
        HTTPException 400: Invalid input data
        HTTPException 401: Not authenticated
        HTTPException 500: Database error
    """
    conn = await get_db_connection()
    try:
        insert_query = """
            INSERT INTO add_ons (
                name, description, category, base_price,
                billing_type, features, is_active, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, TRUE, NOW(), NOW())
            RETURNING
                id, name, description, category, base_price,
                billing_type, features, is_active, created_at, updated_at
        """

        created_addon = await conn.fetchrow(
            insert_query,
            addon.name,
            addon.description,
            addon.category,
            addon.base_price,
            addon.billing_type,
            json.dumps(addon.features)
        )

        logger.info(
            f"Admin {admin_id} created add-on: {addon.name} "
            f"(ID: {created_addon['id']}, Price: {addon.base_price})"
        )

        # Convert asyncpg.Record to dict and parse features JSON
        result = dict(created_addon)
        result['features'] = json.loads(result['features']) if result['features'] else {}
        result['base_price'] = float(result['base_price'])

        return result

    except asyncpg.UniqueViolationError:
        logger.warning(f"Admin {admin_id} attempted to create duplicate add-on: {addon.name}")
        raise HTTPException(
            status_code=400,
            detail=f"Add-on with name '{addon.name}' already exists"
        )
    except Exception as e:
        logger.error(f"Error creating add-on: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create add-on")
    finally:
        await conn.close()


@router.put("/{addon_id}", response_model=Dict[str, Any])
async def update_addon(
    addon_id: str,
    updates: UpdateAddOnRequest,
    request: Request,
    admin_id: str = Depends(get_current_admin)
):
    """
    Update add-on (admin only)

    Updates one or more fields of an existing add-on.
    Only provided fields will be updated.

    Args:
        addon_id: UUID of the add-on to update
        updates: Fields to update (only non-null fields are updated)
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        Dict containing updated add-on details

    Raises:
        HTTPException 400: No fields to update or invalid data
        HTTPException 401: Not authenticated
        HTTPException 404: Add-on not found
        HTTPException 500: Database error
    """
    conn = await get_db_connection()
    try:
        # Build dynamic update query
        update_fields = []
        params = []
        param_idx = 1

        if updates.name is not None:
            update_fields.append(f"name = ${param_idx}")
            params.append(updates.name)
            param_idx += 1

        if updates.description is not None:
            update_fields.append(f"description = ${param_idx}")
            params.append(updates.description)
            param_idx += 1

        if updates.base_price is not None:
            update_fields.append(f"base_price = ${param_idx}")
            params.append(updates.base_price)
            param_idx += 1

        if updates.is_active is not None:
            update_fields.append(f"is_active = ${param_idx}")
            params.append(updates.is_active)
            param_idx += 1

        if updates.features is not None:
            update_fields.append(f"features = ${param_idx}")
            params.append(json.dumps(updates.features))
            param_idx += 1

        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="No fields to update. Provide at least one field."
            )

        # Always update the updated_at timestamp
        update_fields.append("updated_at = NOW()")
        params.append(addon_id)

        query = f"""
            UPDATE add_ons
            SET {', '.join(update_fields)}
            WHERE id = ${param_idx}
            RETURNING
                id, name, description, category, base_price,
                billing_type, features, is_active, created_at, updated_at
        """

        updated_addon = await conn.fetchrow(query, *params)

        if not updated_addon:
            raise HTTPException(
                status_code=404,
                detail=f"Add-on with ID '{addon_id}' not found"
            )

        logger.info(
            f"Admin {admin_id} updated add-on {addon_id} "
            f"(Fields: {', '.join([f.split(' = ')[0] for f in update_fields[:-1]])})"
        )

        # Convert to dict and parse features JSON
        result = dict(updated_addon)
        result['features'] = json.loads(result['features']) if result['features'] else {}
        result['base_price'] = float(result['base_price'])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating add-on {addon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update add-on")
    finally:
        await conn.close()


@router.delete("/{addon_id}", response_model=Dict[str, Any])
async def delete_addon(
    addon_id: str,
    request: Request,
    admin_id: str = Depends(get_current_admin)
):
    """
    Soft delete add-on (admin only)

    Performs a soft delete by setting is_active = FALSE.
    The add-on remains in the database but won't appear in listings.
    Existing user subscriptions are not affected.

    Args:
        addon_id: UUID of the add-on to delete
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        Dict with success message

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 404: Add-on not found
        HTTPException 500: Database error
    """
    conn = await get_db_connection()
    try:
        delete_query = """
            UPDATE add_ons
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = $1 AND is_active = TRUE
            RETURNING id, name
        """

        deleted = await conn.fetchrow(delete_query, addon_id)

        if not deleted:
            # Check if it exists but is already inactive
            check_query = "SELECT id, name, is_active FROM add_ons WHERE id = $1"
            existing = await conn.fetchrow(check_query, addon_id)

            if existing:
                if not existing['is_active']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Add-on '{existing['name']}' is already deleted"
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Add-on with ID '{addon_id}' not found"
                )

        logger.info(
            f"Admin {admin_id} deleted add-on {addon_id} "
            f"(Name: {deleted['name']})"
        )

        return {
            "success": True,
            "message": f"Add-on '{deleted['name']}' successfully deleted",
            "addon_id": str(deleted['id'])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting add-on {addon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete add-on")
    finally:
        await conn.close()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    request: Request = None,
    admin_id: str = Depends(get_current_admin)
):
    """
    Get sales analytics (admin only)

    Retrieves comprehensive sales analytics including:
    - Total revenue and purchase count
    - Top 10 best-selling add-ons
    - Revenue breakdown by category

    Args:
        from_date: Start date for analytics (default: 30 days ago)
        to_date: End date for analytics (default: now)
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        AnalyticsResponse with revenue, purchases, and breakdowns

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 500: Database error
    """
    # Default date range: last 30 days
    if not from_date:
        from_date = datetime.now() - timedelta(days=30)
    if not to_date:
        to_date = datetime.now()

    conn = await get_db_connection()
    try:
        # Total revenue and purchase count
        revenue_query = """
            SELECT
                COALESCE(SUM(amount), 0) as total_revenue,
                COUNT(*) as total_purchases
            FROM add_on_purchases
            WHERE purchased_at BETWEEN $1 AND $2
            AND status = 'completed'
        """
        revenue_data = await conn.fetchrow(revenue_query, from_date, to_date)

        # Top 10 best-selling add-ons
        top_sellers_query = """
            SELECT
                a.id,
                a.name,
                a.category,
                COUNT(*) as purchases,
                SUM(p.amount) as revenue
            FROM add_on_purchases p
            JOIN add_ons a ON p.add_on_id = a.id
            WHERE p.purchased_at BETWEEN $1 AND $2
            AND p.status = 'completed'
            GROUP BY a.id, a.name, a.category
            ORDER BY revenue DESC
            LIMIT 10
        """
        top_sellers = await conn.fetch(top_sellers_query, from_date, to_date)

        # Revenue breakdown by category
        category_query = """
            SELECT
                a.category,
                COUNT(DISTINCT a.id) as addon_count,
                COUNT(*) as purchases,
                SUM(p.amount) as revenue
            FROM add_on_purchases p
            JOIN add_ons a ON p.add_on_id = a.id
            WHERE p.purchased_at BETWEEN $1 AND $2
            AND p.status = 'completed'
            GROUP BY a.category
            ORDER BY revenue DESC
        """
        categories = await conn.fetch(category_query, from_date, to_date)

        logger.info(
            f"Admin {admin_id} retrieved analytics for period "
            f"{from_date.date()} to {to_date.date()}"
        )

        return AnalyticsResponse(
            total_revenue=float(revenue_data['total_revenue']),
            total_purchases=revenue_data['total_purchases'],
            top_sellers=[
                {
                    "id": str(seller['id']),
                    "name": seller['name'],
                    "category": seller['category'],
                    "purchases": seller['purchases'],
                    "revenue": float(seller['revenue'])
                }
                for seller in top_sellers
            ],
            categories=[
                {
                    "category": cat['category'],
                    "addon_count": cat['addon_count'],
                    "purchases": cat['purchases'],
                    "revenue": float(cat['revenue'])
                }
                for cat in categories
            ],
            period={"from": from_date, "to": to_date}
        )

    except Exception as e:
        logger.error(f"Error retrieving analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
    finally:
        await conn.close()


@router.post("/promo-codes", response_model=Dict[str, Any])
async def create_promo_code(
    promo: CreatePromoCodeRequest,
    request: Request,
    admin_id: str = Depends(get_current_admin)
):
    """
    Create promotional code (admin only)

    Creates a new promotional code that can be applied to purchases.

    Discount types:
    - 'percentage': Discount as percentage (0-100)
    - 'fixed_amount': Fixed dollar amount discount

    Args:
        promo: Promotional code details
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        Dict containing created promo code details

    Raises:
        HTTPException 400: Invalid data or duplicate code
        HTTPException 401: Not authenticated
        HTTPException 500: Database error
    """
    conn = await get_db_connection()
    try:
        insert_query = """
            INSERT INTO promotional_codes (
                code, discount_type, discount_value,
                max_uses, current_uses, expires_at,
                is_active, created_at
            )
            VALUES ($1, $2, $3, $4, 0, $5, TRUE, NOW())
            RETURNING
                id, code, discount_type, discount_value,
                max_uses, current_uses, expires_at,
                is_active, created_at
        """

        created_promo = await conn.fetchrow(
            insert_query,
            promo.code,
            promo.discount_type,
            promo.discount_value,
            promo.max_uses,
            promo.expires_at
        )

        logger.info(
            f"Admin {admin_id} created promo code: {promo.code} "
            f"({promo.discount_type}: {promo.discount_value})"
        )

        # Convert to dict and format response
        result = dict(created_promo)
        result['discount_value'] = float(result['discount_value'])

        return result

    except asyncpg.UniqueViolationError:
        logger.warning(
            f"Admin {admin_id} attempted to create duplicate promo code: {promo.code}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Promotional code '{promo.code}' already exists"
        )
    except Exception as e:
        logger.error(f"Error creating promo code: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create promo code")
    finally:
        await conn.close()


# ============================================================================
# ADDITIONAL UTILITY ENDPOINTS
# ============================================================================

@router.get("/promo-codes", response_model=List[Dict[str, Any]])
async def list_promo_codes(
    active_only: bool = True,
    request: Request = None,
    admin_id: str = Depends(get_current_admin)
):
    """
    List all promotional codes (admin only)

    Args:
        active_only: If True, only return active codes
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        List of promotional codes
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT
                id, code, discount_type, discount_value,
                max_uses, current_uses, expires_at,
                is_active, created_at
            FROM promotional_codes
            WHERE ($1 = FALSE OR is_active = TRUE)
            ORDER BY created_at DESC
        """

        promo_codes = await conn.fetch(query, active_only)

        return [
            {
                **dict(promo),
                'discount_value': float(promo['discount_value'])
            }
            for promo in promo_codes
        ]

    finally:
        await conn.close()


@router.get("/{addon_id}/purchases", response_model=List[Dict[str, Any]])
async def get_addon_purchases(
    addon_id: str,
    limit: int = 50,
    request: Request = None,
    admin_id: str = Depends(get_current_admin)
):
    """
    Get purchase history for a specific add-on (admin only)

    Args:
        addon_id: UUID of the add-on
        limit: Maximum number of purchases to return
        request: FastAPI request object
        admin_id: Authenticated admin user ID

    Returns:
        List of purchases
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT
                p.id, p.user_id, p.amount, p.status,
                p.purchased_at, p.subscription_ends_at,
                u.email as user_email
            FROM add_on_purchases p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.add_on_id = $1
            ORDER BY p.purchased_at DESC
            LIMIT $2
        """

        purchases = await conn.fetch(query, addon_id, limit)

        return [
            {
                **dict(purchase),
                'amount': float(purchase['amount'])
            }
            for purchase in purchases
        ]

    finally:
        await conn.close()
