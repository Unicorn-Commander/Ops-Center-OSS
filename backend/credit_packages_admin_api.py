"""
Credit Packages Admin API - Admin CRUD for buyable credit packs.

Manages the ``credit_packages`` table (the one-time credit packs surfaced to
buyers by ``credit_purchase_api.py``). Until now these rows were seeded by
hand-written SQL; this router gives admins a UI-backed CRUD surface.

Endpoints (all admin-gated):
  GET    /api/v1/admin/credit-packages          - List ALL packs (incl. inactive)
  POST   /api/v1/admin/credit-packages          - Create a pack
  PUT    /api/v1/admin/credit-packages/{id}     - Partial update
  DELETE /api/v1/admin/credit-packages/{id}     - Soft delete (is_active = false)

Notes:
  - Validation mirrors the DB CHECK constraints (credits > 0, price_usd > 0,
    0 <= discount_percentage <= 100) so we return clean 422s instead of
    leaking raw asyncpg constraint errors.
  - DELETE is a SOFT delete (sets is_active = false) to avoid orphaning rows in
    credit_purchases that reference a package by name. Hard delete is
    intentionally not exposed here.
  - This module NEVER touches the buyer flow (credit_purchase_api.py). The
    Stripe ids it edits are plain string columns; they only take effect the
    next time a buyer initiates checkout for that package_code.

Security:
  All endpoints require admin authentication (same Redis/browser session used
  by the other admin pages, copied from federation_settings_api.py).

Author: Backend Development Team
Date: June 2026
"""

import logging
import os
import sys
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List, Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from audit_logger import audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/credit-packages",
    tags=["Credit Packages Admin"],
)


# ============================================================================
# Auth (copied from federation_settings_api.py — Redis/browser session)
# ============================================================================

async def require_admin(request: Request):
    """Verify admin access using the same Redis/browser session used by admin pages."""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    user = getattr(request, "session", {}).get("user", {}) if hasattr(request, "session") else {}
    session_token = request.cookies.get("session_token")

    if not user and session_token:
        redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        sessions = RedisSessionManager(host=redis_host, port=redis_port, password=os.getenv("REDIS_PASSWORD"))
        if session_token in sessions:
            user = sessions[session_token].get("user", {})

    is_admin = (
        user.get("role") == "admin"
        or user.get("is_admin") is True
        or user.get("is_superuser") is True
        or "admin" in user.get("groups", [])
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get the shared database pool from app state."""
    if not hasattr(request.app.state, 'db_pool') or not request.app.state.db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return request.app.state.db_pool


# ============================================================================
# Pydantic Models
# ============================================================================

class CreditPackageResponse(BaseModel):
    """A credit package row as returned to the admin UI."""
    id: str
    package_code: str
    package_name: str
    description: Optional[str] = None
    credits: int
    price_usd: float
    discount_percentage: int = 0
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreditPackageCreate(BaseModel):
    """Create payload for a credit package."""
    package_code: str = Field(..., min_length=1, max_length=50, description="Unique machine code (e.g. 'starter')")
    package_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Marketing blurb shown on the card")
    credits: int = Field(..., description="Credits granted (must be > 0)")
    price_usd: float = Field(..., description="Price in USD (must be > 0)")
    discount_percentage: int = Field(0, description="Discount badge percent (0-100)")
    stripe_price_id: Optional[str] = Field(None, max_length=255, description="Optional Stripe price id")
    stripe_product_id: Optional[str] = Field(None, max_length=255, description="Optional Stripe product id")
    is_active: bool = Field(True, description="Whether buyers can see/purchase this pack")
    display_order: int = Field(0, description="Sort order (lower shows first)")


class CreditPackageUpdate(BaseModel):
    """Partial update payload — only provided fields are changed."""
    package_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    credits: Optional[int] = None
    price_usd: Optional[float] = None
    discount_percentage: Optional[int] = None
    stripe_price_id: Optional[str] = Field(None, max_length=255)
    stripe_product_id: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


# ============================================================================
# Helpers
# ============================================================================

def _row_to_response(row: asyncpg.Record) -> CreditPackageResponse:
    """Convert a DB row into the API response model."""
    return CreditPackageResponse(
        id=str(row["id"]),
        package_code=row["package_code"],
        package_name=row["package_name"],
        description=row["description"],
        credits=row["credits"],
        price_usd=float(row["price_usd"]),
        discount_percentage=row["discount_percentage"] if row["discount_percentage"] is not None else 0,
        stripe_price_id=row["stripe_price_id"],
        stripe_product_id=row["stripe_product_id"],
        is_active=row["is_active"],
        display_order=row["display_order"] if row["display_order"] is not None else 0,
        created_at=row["created_at"].isoformat() if row.get("created_at") else None,
        updated_at=row["updated_at"].isoformat() if row.get("updated_at") else None,
    )


def _validate_credits(credits: int) -> None:
    if credits is None or credits <= 0:
        raise HTTPException(status_code=422, detail="credits must be greater than 0")


def _validate_price(price_usd: float) -> Decimal:
    """Validate price > 0 and return it as a Decimal for the numeric(10,2) column."""
    try:
        dec = Decimal(str(price_usd))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="price_usd must be a valid number")
    if dec <= 0:
        raise HTTPException(status_code=422, detail="price_usd must be greater than 0")
    return dec


def _validate_discount(discount: int) -> None:
    if discount is None or discount < 0 or discount > 100:
        raise HTTPException(status_code=422, detail="discount_percentage must be between 0 and 100")


def _actor(admin_user: dict) -> dict:
    """Pull stable id/name fields off the admin session for audit logging."""
    user_id = admin_user.get("user_id") or admin_user.get("sub") or admin_user.get("id")
    username = admin_user.get("username") or admin_user.get("email") or "unknown"
    return {"user_id": user_id, "username": username}


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[CreditPackageResponse])
@router.get("/", response_model=List[CreditPackageResponse])
async def list_credit_packages(
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    List ALL credit packages, including inactive ones, ordered by display_order
    then package_code. Returns an empty list (never 500) if the table is missing.
    """
    pool = await get_db_pool(request)
    try:
        rows = await pool.fetch(
            """
            SELECT id, package_code, package_name, description, credits, price_usd,
                   discount_percentage, stripe_price_id, stripe_product_id,
                   is_active, display_order, created_at, updated_at
            FROM credit_packages
            ORDER BY display_order, package_code
            """
        )
    except asyncpg.UndefinedTableError:
        logger.warning("credit_packages table missing; returning empty list")
        return []
    except Exception as e:
        logger.error(f"Failed to list credit packages: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Failed to list credit packages")

    return [_row_to_response(r) for r in rows]


@router.post("", response_model=CreditPackageResponse, status_code=201)
@router.post("/", response_model=CreditPackageResponse, status_code=201)
async def create_credit_package(
    body: CreditPackageCreate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Create a new credit package.

    Validates against the table CHECK constraints first (clean 422), returns
    409 on a duplicate package_code, and audits the write.
    """
    pool = await get_db_pool(request)

    # Validate against CHECK constraints BEFORE touching the DB.
    _validate_credits(body.credits)
    price = _validate_price(body.price_usd)
    _validate_discount(body.discount_percentage)

    package_code = body.package_code.strip()
    if not package_code:
        raise HTTPException(status_code=422, detail="package_code is required")

    # Duplicate check (also guarded by the UNIQUE constraint below).
    existing = await pool.fetchrow(
        "SELECT id FROM credit_packages WHERE package_code = $1", package_code
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Package code '{package_code}' already exists")

    try:
        row = await pool.fetchrow(
            """
            INSERT INTO credit_packages (
                package_code, package_name, description, credits, price_usd,
                discount_percentage, stripe_price_id, stripe_product_id,
                is_active, display_order
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, package_code, package_name, description, credits, price_usd,
                      discount_percentage, stripe_price_id, stripe_product_id,
                      is_active, display_order, created_at, updated_at
            """,
            package_code,
            body.package_name,
            body.description,
            body.credits,
            price,
            body.discount_percentage,
            body.stripe_price_id,
            body.stripe_product_id,
            body.is_active,
            body.display_order,
        )
    except asyncpg.UniqueViolationError:
        # Race: another request inserted the same code between our check and insert.
        raise HTTPException(status_code=409, detail=f"Package code '{package_code}' already exists")
    except asyncpg.CheckViolationError as e:
        logger.warning(f"Credit package CHECK violation on create: {e}")
        raise HTTPException(status_code=422, detail="Package values violate database constraints")

    actor = _actor(admin_user)
    await audit_logger.log(
        action="admin.credit_package.create",
        result="success",
        user_id=actor["user_id"],
        username=actor["username"],
        resource_type="credit_package",
        resource_id=str(row["id"]),
        metadata={
            "package_code": package_code,
            "package_name": body.package_name,
            "credits": body.credits,
            "price_usd": float(price),
            "discount_percentage": body.discount_percentage,
            "is_active": body.is_active,
        },
    )
    logger.info(f"Credit package '{package_code}' created by {actor['username']}")

    return _row_to_response(row)


@router.put("/{package_id}", response_model=CreditPackageResponse)
async def update_credit_package(
    package_id: str,
    body: CreditPackageUpdate,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Partially update a credit package. 404 if it doesn't exist. Validates any
    provided constrained fields (clean 422). Audits the before/after state.

    package_code is intentionally immutable here (it's the stable join key used
    by the buyer flow / purchase history).
    """
    pool = await get_db_pool(request)

    try:
        existing = await pool.fetchrow(
            """
            SELECT id, package_code, package_name, description, credits, price_usd,
                   discount_percentage, stripe_price_id, stripe_product_id,
                   is_active, display_order, created_at, updated_at
            FROM credit_packages WHERE id = $1
            """,
            package_id,
        )
    except asyncpg.DataError:
        # Malformed UUID — treat as not found rather than 500.
        raise HTTPException(status_code=404, detail="Credit package not found")

    if not existing:
        raise HTTPException(status_code=404, detail="Credit package not found")

    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=422, detail="No fields provided to update")

    # Validate constrained fields when present.
    if "credits" in fields:
        _validate_credits(fields["credits"])
    if "price_usd" in fields:
        fields["price_usd"] = _validate_price(fields["price_usd"])
    if "discount_percentage" in fields:
        _validate_discount(fields["discount_percentage"])

    set_clauses = []
    params = []
    idx = 1
    for col, val in fields.items():
        set_clauses.append(f"{col} = ${idx}")
        params.append(val)
        idx += 1

    params.append(package_id)
    query = f"""
        UPDATE credit_packages
        SET {', '.join(set_clauses)}
        WHERE id = ${idx}
        RETURNING id, package_code, package_name, description, credits, price_usd,
                  discount_percentage, stripe_price_id, stripe_product_id,
                  is_active, display_order, created_at, updated_at
    """

    try:
        row = await pool.fetchrow(query, *params)
    except asyncpg.CheckViolationError as e:
        logger.warning(f"Credit package CHECK violation on update: {e}")
        raise HTTPException(status_code=422, detail="Package values violate database constraints")

    actor = _actor(admin_user)
    # Audit a before/after diff of just the changed fields.
    before = {k: (float(existing["price_usd"]) if k == "price_usd" else existing[k]) for k in fields.keys()}
    after = {k: (float(v) if k == "price_usd" else v) for k, v in fields.items()}
    await audit_logger.log(
        action="admin.credit_package.update",
        result="success",
        user_id=actor["user_id"],
        username=actor["username"],
        resource_type="credit_package",
        resource_id=package_id,
        metadata={
            "package_code": existing["package_code"],
            "before": before,
            "after": after,
        },
    )
    logger.info(f"Credit package {package_id} updated by {actor['username']}: {list(fields.keys())}")

    return _row_to_response(row)


@router.delete("/{package_id}")
async def delete_credit_package(
    package_id: str,
    request: Request,
    admin_user: dict = Depends(require_admin),
):
    """
    Soft-delete a credit package by setting is_active = false.

    We deliberately do NOT hard-delete: credit_purchases rows reference packages
    by name and a hard delete would orphan purchase history. Deactivating hides
    the pack from the buyer flow (which filters on is_active = TRUE) while
    preserving the row. Audits the change. Idempotent.
    """
    pool = await get_db_pool(request)

    try:
        existing = await pool.fetchrow(
            "SELECT id, package_code, is_active FROM credit_packages WHERE id = $1",
            package_id,
        )
    except asyncpg.DataError:
        raise HTTPException(status_code=404, detail="Credit package not found")

    if not existing:
        raise HTTPException(status_code=404, detail="Credit package not found")

    await pool.execute(
        "UPDATE credit_packages SET is_active = FALSE WHERE id = $1",
        package_id,
    )

    actor = _actor(admin_user)
    await audit_logger.log(
        action="admin.credit_package.deactivate",
        result="success",
        user_id=actor["user_id"],
        username=actor["username"],
        resource_type="credit_package",
        resource_id=package_id,
        metadata={
            "package_code": existing["package_code"],
            "was_active": existing["is_active"],
            "delete_type": "soft",
        },
    )
    logger.info(f"Credit package {package_id} ({existing['package_code']}) soft-deleted by {actor['username']}")

    return {
        "success": True,
        "message": f"Package '{existing['package_code']}' deactivated (soft delete)",
        "id": package_id,
    }
