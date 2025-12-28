"""
Invite Code Management API for Ops-Center
Provides admin and user endpoints for invite code management

Author: Claude Code
Created: November 12, 2025
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import asyncpg
import secrets
import string

# Import Keycloak integration for user tier updates
from keycloak_integration import update_user_attributes, get_user_by_id

logger = logging.getLogger(__name__)

# Admin router
admin_router = APIRouter(prefix="/api/v1/admin/invite-codes", tags=["admin-invite-codes"])

# User router
user_router = APIRouter(prefix="/api/v1/invite-codes", tags=["invite-codes"])


# ============================================
# Pydantic Models
# ============================================

class InviteCodeCreate(BaseModel):
    """Create invite code request"""
    tier_code: str = Field(..., description="Target subscription tier code")
    max_uses: Optional[int] = Field(None, ge=1, description="Max uses (null = unlimited)")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiry (null = never)")
    notes: Optional[str] = Field(None, max_length=500, description="Admin notes")


class InviteCodeUpdate(BaseModel):
    """Update invite code request"""
    is_active: Optional[bool] = Field(None, description="Active status")
    max_uses: Optional[int] = Field(None, ge=1, description="Max uses")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    notes: Optional[str] = Field(None, max_length=500, description="Admin notes")


class InviteCodeResponse(BaseModel):
    """Invite code response"""
    id: int
    code: str
    tier_code: str
    tier_name: Optional[str] = None
    max_uses: Optional[int]
    current_uses: int
    remaining_uses: Optional[int]
    expires_at: Optional[datetime]
    is_active: bool
    is_expired: bool
    is_exhausted: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    notes: Optional[str]
    redemption_count: int = 0


class RedemptionResponse(BaseModel):
    """Redemption response"""
    id: int
    invite_code_id: int
    code: str
    user_id: str
    user_email: Optional[str]
    redeemed_at: datetime


class RedeemCodeRequest(BaseModel):
    """Redeem invite code request"""
    code: str = Field(..., min_length=5, max_length=50, description="Invite code")


class ValidateCodeResponse(BaseModel):
    """Validate code response"""
    valid: bool
    code: str
    tier_code: Optional[str] = None
    tier_name: Optional[str] = None
    message: str
    expires_at: Optional[datetime] = None
    remaining_uses: Optional[int] = None


# ============================================
# Dependency: Get database connection
# ============================================

async def get_db_connection():
    """Get PostgreSQL database connection"""
    import os
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "uchub-postgres"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )
        yield conn
    finally:
        if conn:
            await conn.close()


async def get_current_admin(request: Request) -> str:
    """Get current admin user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    username = user.get("username") or user.get("email", "unknown")

    # Check if user has admin role
    roles = user.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    return username


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return session_data.get("user", {})


# ============================================
# Helper Functions
# ============================================

def generate_invite_code(prefix: str = "VIP-FOUNDER") -> str:
    """
    Generate unique invite code

    Args:
        prefix: Code prefix (default: VIP-FOUNDER)

    Returns:
        Unique invite code (e.g., VIP-FOUNDER-ABC123)
    """
    # Generate 6 random uppercase alphanumeric characters
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{suffix}"


async def check_code_validity(code: str, conn: asyncpg.Connection) -> Dict[str, Any]:
    """
    Check if invite code is valid

    Args:
        code: Invite code
        conn: Database connection

    Returns:
        Dict with validity status and details
    """
    query = """
        SELECT
            ic.id,
            ic.code,
            ic.tier_code,
            st.tier_name,
            ic.max_uses,
            ic.current_uses,
            ic.expires_at,
            ic.is_active,
            CASE
                WHEN ic.max_uses IS NULL THEN NULL
                ELSE (ic.max_uses - ic.current_uses)
            END as remaining_uses
        FROM invite_codes ic
        LEFT JOIN subscription_tiers st ON ic.tier_code = st.tier_code
        WHERE ic.code = $1
    """

    row = await conn.fetchrow(query, code)

    if not row:
        return {
            "valid": False,
            "message": "Invalid invite code",
            "code": code
        }

    # Check if active
    if not row['is_active']:
        return {
            "valid": False,
            "message": "This invite code has been deactivated",
            "code": code
        }

    # Check if expired
    if row['expires_at'] and row['expires_at'] < datetime.now():
        return {
            "valid": False,
            "message": "This invite code has expired",
            "code": code,
            "expires_at": row['expires_at']
        }

    # Check if exhausted
    if row['max_uses'] is not None and row['current_uses'] >= row['max_uses']:
        return {
            "valid": False,
            "message": "This invite code has been fully redeemed",
            "code": code,
            "remaining_uses": 0
        }

    # Valid code
    return {
        "valid": True,
        "message": "Valid invite code",
        "code": code,
        "tier_code": row['tier_code'],
        "tier_name": row['tier_name'],
        "expires_at": row['expires_at'],
        "remaining_uses": row['remaining_uses']
    }


# ============================================
# ADMIN ENDPOINTS
# ============================================

@admin_router.post("/generate", response_model=InviteCodeResponse)
async def generate_code(
    request: Request,
    data: InviteCodeCreate,
    admin: str = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Generate new invite code (Admin only)

    Args:
        data: Invite code creation data
        admin: Current admin username
        conn: Database connection

    Returns:
        Created invite code
    """
    try:
        # Verify tier exists
        tier_check = await conn.fetchrow(
            "SELECT tier_code, tier_name FROM subscription_tiers WHERE tier_code = $1",
            data.tier_code
        )

        if not tier_check:
            raise HTTPException(status_code=404, detail=f"Tier '{data.tier_code}' not found")

        # Generate unique code
        code = generate_invite_code()

        # Calculate expiration date
        expires_at = None
        if data.expires_in_days:
            expires_at = datetime.now() + timedelta(days=data.expires_in_days)

        # Insert invite code
        query = """
            INSERT INTO invite_codes (
                code, tier_code, max_uses, expires_at, created_by, notes
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, code, tier_code, max_uses, current_uses, expires_at,
                      is_active, created_by, created_at, updated_at, notes
        """

        row = await conn.fetchrow(
            query,
            code,
            data.tier_code,
            data.max_uses,
            expires_at,
            admin,
            data.notes
        )

        # Calculate derived fields
        remaining_uses = None
        if row['max_uses'] is not None:
            remaining_uses = row['max_uses'] - row['current_uses']

        is_expired = row['expires_at'] < datetime.now() if row['expires_at'] else False
        is_exhausted = (row['max_uses'] is not None and
                       row['current_uses'] >= row['max_uses'])

        logger.info(f"Admin '{admin}' generated invite code: {code} for tier: {data.tier_code}")

        return InviteCodeResponse(
            id=row['id'],
            code=row['code'],
            tier_code=row['tier_code'],
            tier_name=tier_check['tier_name'],
            max_uses=row['max_uses'],
            current_uses=row['current_uses'],
            remaining_uses=remaining_uses,
            expires_at=row['expires_at'],
            is_active=row['is_active'],
            is_expired=is_expired,
            is_exhausted=is_exhausted,
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            notes=row['notes'],
            redemption_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invite code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/", response_model=List[InviteCodeResponse])
async def list_codes(
    tier_code: Optional[str] = None,
    active_only: bool = False,
    conn: asyncpg.Connection = Depends(get_db_connection),
    admin: str = Depends(get_current_admin)
):
    """
    List all invite codes (Admin only)

    Args:
        tier_code: Filter by tier code
        active_only: Show only active codes
        conn: Database connection
        admin: Current admin username

    Returns:
        List of invite codes
    """
    try:
        query = """
            SELECT
                ic.id,
                ic.code,
                ic.tier_code,
                st.tier_name,
                ic.max_uses,
                ic.current_uses,
                ic.expires_at,
                ic.is_active,
                ic.created_by,
                ic.created_at,
                ic.updated_at,
                ic.notes,
                COUNT(icr.id) as redemption_count
            FROM invite_codes ic
            LEFT JOIN subscription_tiers st ON ic.tier_code = st.tier_code
            LEFT JOIN invite_code_redemptions icr ON ic.id = icr.invite_code_id
            WHERE 1=1
        """

        params = []
        param_num = 1

        if tier_code:
            query += f" AND ic.tier_code = ${param_num}"
            params.append(tier_code)
            param_num += 1

        if active_only:
            query += " AND ic.is_active = TRUE"

        query += """
            GROUP BY ic.id, st.tier_name
            ORDER BY ic.created_at DESC
        """

        rows = await conn.fetch(query, *params)

        codes = []
        for row in rows:
            remaining_uses = None
            if row['max_uses'] is not None:
                remaining_uses = row['max_uses'] - row['current_uses']

            is_expired = row['expires_at'] < datetime.now() if row['expires_at'] else False
            is_exhausted = (row['max_uses'] is not None and
                           row['current_uses'] >= row['max_uses'])

            codes.append(InviteCodeResponse(
                id=row['id'],
                code=row['code'],
                tier_code=row['tier_code'],
                tier_name=row['tier_name'],
                max_uses=row['max_uses'],
                current_uses=row['current_uses'],
                remaining_uses=remaining_uses,
                expires_at=row['expires_at'],
                is_active=row['is_active'],
                is_expired=is_expired,
                is_exhausted=is_exhausted,
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                notes=row['notes'],
                redemption_count=row['redemption_count']
            ))

        return codes

    except Exception as e:
        logger.error(f"Error listing invite codes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put("/{code_id}", response_model=InviteCodeResponse)
async def update_code(
    code_id: int,
    data: InviteCodeUpdate,
    admin: str = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Update invite code (Admin only)

    Args:
        code_id: Invite code ID
        data: Update data
        admin: Current admin username
        conn: Database connection

    Returns:
        Updated invite code
    """
    try:
        # Check if code exists
        existing = await conn.fetchrow("SELECT id FROM invite_codes WHERE id = $1", code_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Invite code not found")

        # Build update query dynamically
        update_fields = []
        params = []
        param_num = 1

        if data.is_active is not None:
            update_fields.append(f"is_active = ${param_num}")
            params.append(data.is_active)
            param_num += 1

        if data.max_uses is not None:
            update_fields.append(f"max_uses = ${param_num}")
            params.append(data.max_uses)
            param_num += 1

        if data.expires_at is not None:
            update_fields.append(f"expires_at = ${param_num}")
            params.append(data.expires_at)
            param_num += 1

        if data.notes is not None:
            update_fields.append(f"notes = ${param_num}")
            params.append(data.notes)
            param_num += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(code_id)

        query = f"""
            UPDATE invite_codes
            SET {', '.join(update_fields)}
            WHERE id = ${param_num}
            RETURNING id, code, tier_code, max_uses, current_uses, expires_at,
                      is_active, created_by, created_at, updated_at, notes
        """

        row = await conn.fetchrow(query, *params)

        # Get tier name
        tier = await conn.fetchrow(
            "SELECT tier_name FROM subscription_tiers WHERE tier_code = $1",
            row['tier_code']
        )

        # Calculate derived fields
        remaining_uses = None
        if row['max_uses'] is not None:
            remaining_uses = row['max_uses'] - row['current_uses']

        is_expired = row['expires_at'] < datetime.now() if row['expires_at'] else False
        is_exhausted = (row['max_uses'] is not None and
                       row['current_uses'] >= row['max_uses'])

        logger.info(f"Admin '{admin}' updated invite code {code_id}")

        return InviteCodeResponse(
            id=row['id'],
            code=row['code'],
            tier_code=row['tier_code'],
            tier_name=tier['tier_name'] if tier else None,
            max_uses=row['max_uses'],
            current_uses=row['current_uses'],
            remaining_uses=remaining_uses,
            expires_at=row['expires_at'],
            is_active=row['is_active'],
            is_expired=is_expired,
            is_exhausted=is_exhausted,
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            notes=row['notes'],
            redemption_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invite code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/{code_id}")
async def delete_code(
    code_id: int,
    admin: str = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Delete invite code (Admin only)

    Args:
        code_id: Invite code ID
        admin: Current admin username
        conn: Database connection

    Returns:
        Success message
    """
    try:
        # Check if code exists
        existing = await conn.fetchrow(
            "SELECT code FROM invite_codes WHERE id = $1",
            code_id
        )

        if not existing:
            raise HTTPException(status_code=404, detail="Invite code not found")

        # Delete code (redemptions will cascade)
        await conn.execute("DELETE FROM invite_codes WHERE id = $1", code_id)

        logger.info(f"Admin '{admin}' deleted invite code: {existing['code']}")

        return {"message": "Invite code deleted successfully", "code": existing['code']}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting invite code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/{code_id}/redemptions", response_model=List[RedemptionResponse])
async def get_redemptions(
    code_id: int,
    admin: str = Depends(get_current_admin),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get redemptions for invite code (Admin only)

    Args:
        code_id: Invite code ID
        admin: Current admin username
        conn: Database connection

    Returns:
        List of redemptions
    """
    try:
        query = """
            SELECT
                icr.id,
                icr.invite_code_id,
                ic.code,
                icr.user_id,
                icr.user_email,
                icr.redeemed_at
            FROM invite_code_redemptions icr
            JOIN invite_codes ic ON icr.invite_code_id = ic.id
            WHERE icr.invite_code_id = $1
            ORDER BY icr.redeemed_at DESC
        """

        rows = await conn.fetch(query, code_id)

        return [
            RedemptionResponse(
                id=row['id'],
                invite_code_id=row['invite_code_id'],
                code=row['code'],
                user_id=row['user_id'],
                user_email=row['user_email'],
                redeemed_at=row['redeemed_at']
            )
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error fetching redemptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# USER ENDPOINTS
# ============================================

@user_router.get("/validate/{code}", response_model=ValidateCodeResponse)
async def validate_code(
    code: str,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Validate invite code (Public)

    Args:
        code: Invite code
        conn: Database connection

    Returns:
        Validation result
    """
    try:
        result = await check_code_validity(code, conn)
        return ValidateCodeResponse(**result)

    except Exception as e:
        logger.error(f"Error validating code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@user_router.post("/redeem")
async def redeem_code(
    request: Request,
    data: RedeemCodeRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Redeem invite code (Authenticated users)

    Args:
        request: HTTP request
        data: Redeem request
        user: Current user
        conn: Database connection

    Returns:
        Success message with tier assigned
    """
    try:
        user_id = user.get("user_id") or user.get("sub") or user.get("id")
        user_email = user.get("email", "unknown")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in session")

        # Validate code
        validity = await check_code_validity(data.code, conn)

        if not validity['valid']:
            raise HTTPException(status_code=400, detail=validity['message'])

        # Get code details
        code_row = await conn.fetchrow(
            "SELECT id, tier_code FROM invite_codes WHERE code = $1",
            data.code
        )

        # Check if user already redeemed this code
        existing = await conn.fetchrow(
            "SELECT id FROM invite_code_redemptions WHERE invite_code_id = $1 AND user_id = $2",
            code_row['id'],
            user_id
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="You have already redeemed this invite code"
            )

        # Start transaction
        async with conn.transaction():
            # Record redemption
            await conn.execute("""
                INSERT INTO invite_code_redemptions (invite_code_id, user_id, user_email)
                VALUES ($1, $2, $3)
            """, code_row['id'], user_id, user_email)

            # Increment current_uses
            await conn.execute("""
                UPDATE invite_codes
                SET current_uses = current_uses + 1
                WHERE id = $1
            """, code_row['id'])

            # Update user's subscription tier in Keycloak
            try:
                await update_user_attributes(user_id, {
                    "subscription_tier": code_row['tier_code']
                })
                logger.info(f"Updated user {user_id} to tier: {code_row['tier_code']}")
            except Exception as e:
                logger.error(f"Error updating Keycloak attributes: {e}")
                # Don't fail the redemption if Keycloak update fails

        logger.info(f"User {user_id} redeemed invite code: {data.code}")

        return {
            "message": "Invite code redeemed successfully",
            "tier_code": code_row['tier_code'],
            "tier_name": validity.get('tier_name', 'Unknown')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error redeeming code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export routers
__all__ = ['admin_router', 'user_router']
