"""
Extensions Marketplace - Cart Management API
Phase 1: Basic cart operations with asyncpg

Endpoints:
- GET /api/v1/cart - Get user's cart with totals
- POST /api/v1/cart/add - Add item to cart
- DELETE /api/v1/cart/{cart_item_id} - Remove item
- PUT /api/v1/cart/{cart_item_id} - Update quantity
- DELETE /api/v1/cart/clear - Clear entire cart
- POST /api/v1/cart/save-for-later - Save cart (Phase 2)
"""

import os
import asyncpg
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cart", tags=["extensions-cart"])


# ============================================================================
# Database Connection
# ============================================================================

async def get_db_connection():
    """Get asyncpg database connection"""
    try:
        return await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


# ============================================================================
# Authentication Helper
# ============================================================================

async def get_current_user(request: Request) -> str:
    """
    Get current user ID from session

    TODO: In production, integrate with Keycloak:
    1. Extract session_token from cookies
    2. Validate token with Keycloak
    3. Return user_id from validated session
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in."
        )

    # Placeholder: Return test user for development
    # In production, validate with Keycloak and return real user_id
    return "test-user-123"


# ============================================================================
# Pydantic Models
# ============================================================================

class CartItemResponse(BaseModel):
    """Individual cart item with add-on details"""
    cart_item_id: str = Field(..., description="Cart item ID")
    addon_id: str = Field(..., description="Add-on ID")
    name: str = Field(..., description="Add-on name")
    description: str = Field(..., description="Add-on description")
    category: str = Field(..., description="Add-on category")
    base_price: Decimal = Field(..., description="Price per unit")
    quantity: int = Field(..., ge=1, description="Quantity in cart")
    subtotal: Decimal = Field(..., description="Line item subtotal")
    added_at: datetime = Field(..., description="When added to cart")


class CartResponse(BaseModel):
    """Complete cart with calculated totals"""
    items: List[CartItemResponse] = Field(default_factory=list, description="Cart items")
    subtotal: Decimal = Field(..., description="Sum of all item subtotals")
    discount: Decimal = Field(default=Decimal("0.00"), description="Applied discounts")
    total: Decimal = Field(..., description="Final total after discounts")
    item_count: int = Field(..., description="Total number of items")


class AddToCartRequest(BaseModel):
    """Request to add item to cart"""
    addon_id: str = Field(..., description="Add-on ID to add")
    quantity: int = Field(default=1, ge=1, le=100, description="Quantity to add")


class UpdateCartItemRequest(BaseModel):
    """Request to update cart item quantity"""
    quantity: int = Field(..., ge=1, le=100, description="New quantity")


class CartActionResponse(BaseModel):
    """Generic action response"""
    success: bool
    message: str
    cart: Optional[CartResponse] = None


# ============================================================================
# Cart Endpoints
# ============================================================================

@router.get("", response_model=CartResponse)
async def get_cart(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Get user's shopping cart with calculated totals

    Returns:
    - List of cart items with add-on details
    - Subtotal, discounts, and total
    - Item count
    """
    conn = await get_db_connection()
    try:
        # Get cart items with add-on details
        query = """
            SELECT
                c.id as cart_item_id,
                c.quantity,
                c.added_at,
                a.id as addon_id,
                a.name,
                a.description,
                a.base_price,
                a.category
            FROM cart_items c
            JOIN add_ons a ON c.add_on_id = a.id
            WHERE c.user_id = $1 AND a.is_active = TRUE
            ORDER BY c.added_at DESC
        """
        items = await conn.fetch(query, user_id)

        # Build cart items with calculated subtotals
        cart_items = []
        subtotal = Decimal("0.00")

        for item in items:
            item_subtotal = Decimal(str(item['base_price'])) * item['quantity']
            subtotal += item_subtotal

            cart_items.append(CartItemResponse(
                cart_item_id=item['cart_item_id'],
                addon_id=item['addon_id'],
                name=item['name'],
                description=item['description'],
                category=item['category'],
                base_price=Decimal(str(item['base_price'])),
                quantity=item['quantity'],
                subtotal=item_subtotal,
                added_at=item['added_at']
            ))

        # Calculate totals (discount logic for Phase 2)
        discount = Decimal("0.00")  # TODO: Apply promo codes
        total = subtotal - discount

        return CartResponse(
            items=cart_items,
            subtotal=subtotal,
            discount=discount,
            total=total,
            item_count=len(cart_items)
        )
    except Exception as e:
        logger.error(f"Error fetching cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cart: {str(e)}")
    finally:
        await conn.close()


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: Request,
    addon_id: str = Query(..., description="Add-on ID to add"),
    quantity: int = Query(default=1, ge=1, le=100, description="Quantity to add"),
    user_id: str = Depends(get_current_user)
):
    """
    Add add-on to cart (or update quantity if exists)

    Logic:
    - If item exists in cart: increase quantity
    - If new item: create cart entry
    - Validates add-on exists and is active
    """
    conn = await get_db_connection()
    try:
        # Check if add-on exists and is active
        addon_query = """
            SELECT id, name, base_price, is_active
            FROM add_ons
            WHERE id = $1 AND is_active = TRUE
        """
        addon = await conn.fetchrow(addon_query, addon_id)

        if not addon:
            raise HTTPException(
                status_code=404,
                detail=f"Add-on not found or inactive: {addon_id}"
            )

        # Check if item already in cart
        check_query = """
            SELECT id, quantity
            FROM cart_items
            WHERE user_id = $1 AND add_on_id = $2
        """
        existing = await conn.fetchrow(check_query, user_id, addon_id)

        if existing:
            # Update quantity (add to existing)
            new_quantity = existing['quantity'] + quantity
            if new_quantity > 100:  # Sanity check
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add more than 100 of the same item"
                )

            update_query = """
                UPDATE cart_items
                SET quantity = $1, updated_at = NOW()
                WHERE user_id = $2 AND add_on_id = $3
            """
            await conn.execute(update_query, new_quantity, user_id, addon_id)
            logger.info(f"Updated cart: user={user_id}, addon={addon_id}, qty={new_quantity}")
        else:
            # Insert new item
            insert_query = """
                INSERT INTO cart_items (user_id, add_on_id, quantity)
                VALUES ($1, $2, $3)
            """
            await conn.execute(insert_query, user_id, addon_id, quantity)
            logger.info(f"Added to cart: user={user_id}, addon={addon_id}, qty={quantity}")

        # Return updated cart (reuse get_cart logic)
        await conn.close()  # Close before calling get_cart (it opens its own)
        return await get_cart(request, user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add to cart: {str(e)}")
    finally:
        if not conn.is_closed():
            await conn.close()


@router.delete("/{cart_item_id}", response_model=CartResponse)
async def remove_from_cart(
    cart_item_id: str,
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Remove item from cart

    Returns updated cart after removal
    """
    conn = await get_db_connection()
    try:
        # Delete cart item (verify ownership)
        delete_query = """
            DELETE FROM cart_items
            WHERE id = $1 AND user_id = $2
            RETURNING id, add_on_id
        """
        deleted = await conn.fetchrow(delete_query, cart_item_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Cart item not found: {cart_item_id}"
            )

        logger.info(f"Removed from cart: user={user_id}, item={cart_item_id}, addon={deleted['add_on_id']}")

        # Return updated cart
        await conn.close()
        return await get_cart(request, user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {str(e)}")
    finally:
        if not conn.is_closed():
            await conn.close()


@router.put("/{cart_item_id}", response_model=CartResponse)
async def update_cart_item(
    cart_item_id: str,
    quantity: int = Query(..., ge=1, le=100, description="New quantity"),
    request: Request = None,
    user_id: str = Depends(get_current_user)
):
    """
    Update cart item quantity

    Sets absolute quantity (not incremental)
    """
    conn = await get_db_connection()
    try:
        # Update quantity (verify ownership)
        update_query = """
            UPDATE cart_items
            SET quantity = $1, updated_at = NOW()
            WHERE id = $2 AND user_id = $3
            RETURNING id, add_on_id, quantity
        """
        updated = await conn.fetchrow(update_query, quantity, cart_item_id, user_id)

        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Cart item not found: {cart_item_id}"
            )

        logger.info(f"Updated cart item: user={user_id}, item={cart_item_id}, qty={quantity}")

        # Return updated cart
        await conn.close()
        return await get_cart(request, user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update quantity: {str(e)}")
    finally:
        if not conn.is_closed():
            await conn.close()


@router.delete("/clear", response_model=CartActionResponse)
async def clear_cart(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Clear entire cart for user

    Removes all items in one transaction
    """
    conn = await get_db_connection()
    try:
        # Delete all cart items for user
        delete_query = """
            DELETE FROM cart_items
            WHERE user_id = $1
            RETURNING id
        """
        deleted_items = await conn.fetch(delete_query, user_id)
        deleted_count = len(deleted_items)

        logger.info(f"Cleared cart: user={user_id}, removed={deleted_count} items")

        # Return empty cart
        await conn.close()
        empty_cart = await get_cart(request, user_id)

        return CartActionResponse(
            success=True,
            message=f"Cart cleared. Removed {deleted_count} items.",
            cart=empty_cart
        )

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cart: {str(e)}")
    finally:
        if not conn.is_closed():
            await conn.close()


@router.post("/save-for-later", response_model=CartActionResponse)
async def save_cart(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Save cart for later (Phase 2 feature)

    Future implementation:
    - Save cart snapshot to saved_carts table
    - Include expiration date
    - Allow restoring saved carts
    """
    # Placeholder for Phase 2
    logger.info(f"Save cart requested (Phase 2): user={user_id}")

    return CartActionResponse(
        success=True,
        message="Cart save feature coming in Phase 2",
        cart=None
    )


# ============================================================================
# Health Check (for testing)
# ============================================================================

@router.get("/health")
async def cart_health():
    """Cart API health check"""
    conn = await get_db_connection()
    try:
        # Test database connection
        result = await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "service": "extensions-cart-api",
            "database": "connected" if result == 1 else "error"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
    finally:
        await conn.close()
