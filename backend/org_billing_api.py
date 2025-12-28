"""
Organization Billing API
-------------------------
RESTful API endpoints for managing organization-level billing, credit pools,
user credit allocations, and usage tracking.

Supports three billing plan types:
- Platform ($50/mo): Managed credits with markup
- BYOK ($30/mo): Bring Your Own Keys with passthrough pricing
- Hybrid ($99/mo): Mix of managed and BYOK

Author: Ops-Center Team
Created: 2025-11-12
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import logging
import asyncpg

# Database connection (shared)
from database import get_db_connection

# Authentication dependencies (fix auth order issue)
from auth_dependencies import require_authenticated_user, require_admin_user

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/org-billing", tags=["organization-billing"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# ==================== Pydantic Models ====================

class SubscriptionPlanEnum:
    """Subscription plan types"""
    PLATFORM = "platform"
    BYOK = "byok"
    HYBRID = "hybrid"


class SubscriptionStatusEnum:
    """Subscription status types"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PAUSED = "paused"


class OrganizationSubscriptionCreate(BaseModel):
    """Request model for creating org subscription"""
    org_id: str = Field(..., description="Organization UUID")
    subscription_plan: str = Field(..., description="Plan type (platform/byok/hybrid)")
    monthly_price: Decimal = Field(..., description="Monthly subscription cost")
    billing_cycle: str = Field(default="monthly", description="Billing frequency")
    trial_days: Optional[int] = Field(None, description="Trial period in days")

    @validator('subscription_plan')
    def validate_plan(cls, v):
        if v not in ['platform', 'byok', 'hybrid']:
            raise ValueError("Plan must be platform, byok, or hybrid")
        return v


class OrganizationSubscriptionResponse(BaseModel):
    """Response model for subscription"""
    id: str
    org_id: str
    org_name: Optional[str]
    subscription_plan: str
    monthly_price: Decimal
    billing_cycle: str
    status: str
    trial_ends_at: Optional[datetime]
    current_period_start: datetime
    current_period_end: Optional[datetime]
    created_at: datetime


class CreditPoolResponse(BaseModel):
    """Response model for credit pool"""
    id: str
    org_id: str
    org_name: Optional[str]
    total_credits: int
    allocated_credits: int
    used_credits: int
    available_credits: int
    monthly_refresh_amount: int
    last_refresh_date: datetime
    next_refresh_date: Optional[datetime]
    allow_overage: bool
    overage_limit: int
    lifetime_purchased_credits: int
    lifetime_spent_amount: Decimal


class UserCreditAllocationCreate(BaseModel):
    """Request model for allocating credits to user"""
    user_id: str = Field(..., description="Keycloak user UUID")
    allocated_credits: int = Field(..., ge=0, description="Credits to allocate")
    reset_period: str = Field(default="monthly", description="When to reset (daily/weekly/monthly/never)")
    notes: Optional[str] = Field(None, description="Allocation notes")

    @validator('reset_period')
    def validate_period(cls, v):
        if v not in ['daily', 'weekly', 'monthly', 'never']:
            raise ValueError("Period must be daily, weekly, monthly, or never")
        return v


class UserCreditAllocationResponse(BaseModel):
    """Response model for user credit allocation"""
    id: str
    org_id: str
    user_id: str
    user_email: Optional[str]
    user_name: Optional[str]
    allocated_credits: int
    used_credits: int
    remaining_credits: int
    reset_period: str
    last_reset_date: datetime
    next_reset_date: Optional[datetime]
    is_active: bool
    created_at: datetime


class CreditUsageStatsResponse(BaseModel):
    """Response model for credit usage statistics"""
    org_id: str
    total_credits_used: int
    user_count: int
    service_breakdown: Dict[str, int]
    top_users: List[Dict[str, Any]]
    date_range_start: datetime
    date_range_end: datetime


class BillingHistoryResponse(BaseModel):
    """Response model for billing history"""
    id: str
    org_id: str
    event_type: str
    amount: Decimal
    currency: str
    payment_status: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime


# ==================== Helper Functions ====================

async def get_current_user(request: Request) -> Dict:
    """Extract current user from session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})

    # Map Keycloak 'sub' field to 'user_id' if needed
    if "user_id" not in user and "sub" in user:
        user["user_id"] = user["sub"]

    return user


async def check_org_admin(conn: asyncpg.Connection, org_id: str, user_id: str) -> bool:
    """Check if user is org admin"""
    result = await conn.fetchval(
        "SELECT is_org_admin($1, $2)",
        org_id, user_id
    )
    return result


async def check_system_admin(user: Dict) -> bool:
    """Check if user has system admin role"""
    roles = user.get("roles", [])
    return "admin" in roles or "system_admin" in roles


# ==================== Organization Subscription Endpoints ====================

@router.post("/subscriptions", response_model=OrganizationSubscriptionResponse)
@limiter.limit("20/minute")  # Rate limit: 20 POST requests per minute
async def create_organization_subscription(
    request: Request,
    user: Dict = Depends(require_authenticated_user),  # ← Auth checked FIRST
    subscription: OrganizationSubscriptionCreate = None  # ← Validation happens AFTER auth
):
    """
    Create organization-level subscription

    **Required Role**: Org Admin or System Admin

    **Plan Types**:
    - `platform` ($50/mo): Managed credits with 1.5x markup
    - `byok` ($30/mo): Bring Your Own Keys with passthrough pricing
    - `hybrid` ($99/mo): Mix of managed and BYOK credits

    **Security**: Authentication checked before request body validation
    """
    # User is already authenticated via dependency

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, subscription.org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to create subscription")

        # Check if org exists
        org = await conn.fetchrow(
            "SELECT id, name FROM organizations WHERE id = $1",
            subscription.org_id
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Calculate trial end date
        trial_ends_at = None
        if subscription.trial_days:
            trial_ends_at = datetime.utcnow() + timedelta(days=subscription.trial_days)

        # Calculate period end (30 days from now)
        current_period_end = datetime.utcnow() + timedelta(days=30)

        # Create subscription
        sub = await conn.fetchrow(
            """
            INSERT INTO organization_subscriptions (
                org_id, subscription_plan, monthly_price, billing_cycle,
                status, trial_ends_at, current_period_end
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, org_id, subscription_plan, monthly_price, billing_cycle,
                      status, trial_ends_at, current_period_start, current_period_end, created_at
            """,
            subscription.org_id,
            subscription.subscription_plan,
            subscription.monthly_price,
            subscription.billing_cycle,
            SubscriptionStatusEnum.TRIALING if trial_ends_at else SubscriptionStatusEnum.ACTIVE,
            trial_ends_at,
            current_period_end
        )

        # Create credit pool for organization if doesn't exist
        await conn.execute(
            """
            INSERT INTO organization_credit_pools (org_id, total_credits)
            VALUES ($1, 0)
            ON CONFLICT (org_id) DO NOTHING
            """,
            subscription.org_id
        )

        # Record billing history
        await conn.execute(
            """
            INSERT INTO org_billing_history (org_id, subscription_id, event_type, amount, currency)
            VALUES ($1, $2, 'subscription_created', $3, 'USD')
            """,
            subscription.org_id,
            sub["id"],
            subscription.monthly_price
        )

        logger.info(f"Created subscription {sub['id']} for org {org['name']}")

        return OrganizationSubscriptionResponse(
            id=str(sub["id"]),
            org_id=str(sub["org_id"]),
            org_name=org["name"],
            subscription_plan=sub["subscription_plan"],
            monthly_price=sub["monthly_price"],
            billing_cycle=sub["billing_cycle"],
            status=sub["status"],
            trial_ends_at=sub["trial_ends_at"],
            current_period_start=sub["current_period_start"],
            current_period_end=sub["current_period_end"],
            created_at=sub["created_at"]
        )

    finally:
        await conn.close()


@router.get("/subscriptions/{org_id}", response_model=OrganizationSubscriptionResponse)
async def get_organization_subscription(org_id: str, request: Request):
    """
    Get current organization subscription

    **Required Role**: Org Member or System Admin
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check if user belongs to org or is system admin
        is_admin = await check_system_admin(user)
        if not is_admin:
            member = await conn.fetchval(
                "SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2",
                org_id, user["user_id"]
            )
            if not member:
                raise HTTPException(status_code=403, detail="Not a member of this organization")

        # Get active subscription
        sub = await conn.fetchrow(
            """
            SELECT s.*, o.name as org_name
            FROM organization_subscriptions s
            JOIN organizations o ON s.org_id = o.id
            WHERE s.org_id = $1 AND s.status = 'active'
            """,
            org_id
        )

        if not sub:
            raise HTTPException(status_code=404, detail="No active subscription found")

        return OrganizationSubscriptionResponse(
            id=str(sub["id"]),
            org_id=str(sub["org_id"]),
            org_name=sub["org_name"],
            subscription_plan=sub["subscription_plan"],
            monthly_price=sub["monthly_price"],
            billing_cycle=sub["billing_cycle"],
            status=sub["status"],
            trial_ends_at=sub["trial_ends_at"],
            current_period_start=sub["current_period_start"],
            current_period_end=sub["current_period_end"],
            created_at=sub["created_at"]
        )

    finally:
        await conn.close()


@router.put("/subscriptions/{org_id}/upgrade")
async def upgrade_organization_subscription(
    org_id: str,
    new_plan: str = Query(..., description="New plan (platform/byok/hybrid)"),
    request: Request = None
):
    """
    Upgrade organization subscription plan

    **Required Role**: Org Admin or System Admin

    **Upgrade Paths**:
    - BYOK → Platform ($30 → $50)
    - BYOK → Hybrid ($30 → $99)
    - Platform → Hybrid ($50 → $99)
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to upgrade subscription")

        # Validate plan
        if new_plan not in ['platform', 'byok', 'hybrid']:
            raise HTTPException(status_code=400, detail="Invalid plan")

        # Get current subscription
        current_sub = await conn.fetchrow(
            "SELECT * FROM organization_subscriptions WHERE org_id = $1 AND status = 'active'",
            org_id
        )

        if not current_sub:
            raise HTTPException(status_code=404, detail="No active subscription found")

        # Calculate new price
        price_map = {
            'byok': Decimal('30.00'),
            'platform': Decimal('50.00'),
            'hybrid': Decimal('99.00')
        }
        new_price = price_map[new_plan]

        # Update subscription
        updated_sub = await conn.fetchrow(
            """
            UPDATE organization_subscriptions
            SET subscription_plan = $1,
                monthly_price = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE org_id = $3 AND status = 'active'
            RETURNING *
            """,
            new_plan,
            new_price,
            org_id
        )

        # Record billing history
        await conn.execute(
            """
            INSERT INTO org_billing_history (org_id, subscription_id, event_type, amount, currency)
            VALUES ($1, $2, 'subscription_upgraded', $3, 'USD')
            """,
            org_id,
            updated_sub["id"],
            new_price
        )

        logger.info(f"Upgraded org {org_id} subscription from {current_sub['subscription_plan']} to {new_plan}")

        return {
            "success": True,
            "message": f"Subscription upgraded to {new_plan}",
            "old_plan": current_sub['subscription_plan'],
            "new_plan": new_plan,
            "old_price": float(current_sub['monthly_price']),
            "new_price": float(new_price)
        }

    finally:
        await conn.close()


# ==================== Credit Pool Management Endpoints ====================

@router.get("/credits/{org_id}", response_model=CreditPoolResponse)
async def get_organization_credit_pool(org_id: str, request: Request):
    """
    Get organization credit pool details

    **Required Role**: Org Member or System Admin

    **Returns**:
    - Total credits in pool
    - Allocated credits to users
    - Used credits
    - Available credits for allocation
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check membership
        is_admin = await check_system_admin(user)
        if not is_admin:
            member = await conn.fetchval(
                "SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2",
                org_id, user["user_id"]
            )
            if not member:
                raise HTTPException(status_code=403, detail="Not a member of this organization")

        # Get credit pool
        pool = await conn.fetchrow(
            """
            SELECT cp.*, o.name as org_name
            FROM organization_credit_pools cp
            JOIN organizations o ON cp.org_id = o.id
            WHERE cp.org_id = $1
            """,
            org_id
        )

        if not pool:
            raise HTTPException(status_code=404, detail="Credit pool not found")

        return CreditPoolResponse(
            id=str(pool["id"]),
            org_id=str(pool["org_id"]),
            org_name=pool["org_name"],
            total_credits=pool["total_credits"],
            allocated_credits=pool["allocated_credits"],
            used_credits=pool["used_credits"],
            available_credits=pool["available_credits"],
            monthly_refresh_amount=pool["monthly_refresh_amount"],
            last_refresh_date=pool["last_refresh_date"],
            next_refresh_date=pool["next_refresh_date"],
            allow_overage=pool["allow_overage"],
            overage_limit=pool["overage_limit"],
            lifetime_purchased_credits=pool["lifetime_purchased_credits"],
            lifetime_spent_amount=pool["lifetime_spent_amount"]
        )

    finally:
        await conn.close()


@router.post("/credits/{org_id}/add")
@limiter.limit("20/minute")  # Rate limit: 20 POST requests per minute
async def add_credits_to_pool(
    request: Request,
    org_id: str,
    user: Dict = Depends(require_authenticated_user),  # ← Auth checked FIRST
    credits: int = Query(..., ge=1, description="Number of credits to add"),
    purchase_amount: Decimal = Query(default=Decimal('0.00'), description="Purchase amount ($)")
):
    """
    Add credits to organization pool

    **Required Role**: Org Admin or System Admin

    **Use Cases**:
    - Manual credit purchase
    - Subscription renewal
    - Bonus credits
    - Refund credits

    **Security**: Authentication checked before query parameter validation
    """
    # User is already authenticated via dependency

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to add credits")

        # Add credits using stored function
        await conn.execute(
            "SELECT add_credits_to_pool($1, $2, $3)",
            org_id, credits, purchase_amount
        )

        # Record billing history if purchase
        if purchase_amount > 0:
            await conn.execute(
                """
                INSERT INTO org_billing_history (org_id, event_type, amount, currency)
                VALUES ($1, 'credit_purchase', $2, 'USD')
                """,
                org_id, purchase_amount
            )

        logger.info(f"Added {credits} credits to org {org_id} (purchase: ${purchase_amount})")

        # Get updated pool
        pool = await conn.fetchrow(
            "SELECT * FROM organization_credit_pools WHERE org_id = $1",
            org_id
        )

        return {
            "success": True,
            "message": f"Added {credits} credits to pool",
            "total_credits": pool["total_credits"],
            "available_credits": pool["available_credits"]
        }

    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await conn.close()


@router.post("/credits/{org_id}/allocate", response_model=UserCreditAllocationResponse)
@limiter.limit("20/minute")  # Rate limit: 20 POST requests per minute
async def allocate_credits_to_user(
    request: Request,
    org_id: str,
    user: Dict = Depends(require_authenticated_user),  # ← Auth checked FIRST
    allocation: UserCreditAllocationCreate = None  # ← Validation happens AFTER auth
):
    """
    Allocate credits from org pool to specific user

    **Required Role**: Org Admin or System Admin

    **Allocation Limits**:
    - Cannot exceed available credits in pool
    - Can set daily/weekly/monthly reset periods
    - Can add notes for tracking

    **Security**: Authentication checked before request body validation
    """
    # User is already authenticated via dependency

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to allocate credits")

        # Check if target user is org member
        member = await conn.fetchval(
            "SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2",
            org_id, allocation.user_id
        )
        if not member:
            raise HTTPException(status_code=400, detail="User is not a member of this organization")

        # Allocate credits using stored function
        try:
            await conn.execute(
                "SELECT allocate_credits_to_user($1, $2, $3, $4)",
                org_id,
                allocation.user_id,
                allocation.allocated_credits,
                user["user_id"]
            )
        except asyncpg.exceptions.RaiseException as e:
            # Handle insufficient credits error
            if "Insufficient credits" in str(e):
                raise HTTPException(status_code=400, detail=str(e))
            raise

        # Calculate next reset date
        next_reset = None
        if allocation.reset_period == 'daily':
            next_reset = datetime.utcnow() + timedelta(days=1)
        elif allocation.reset_period == 'weekly':
            next_reset = datetime.utcnow() + timedelta(weeks=1)
        elif allocation.reset_period == 'monthly':
            next_reset = datetime.utcnow() + timedelta(days=30)

        # Update reset date and notes if provided
        if next_reset or allocation.notes:
            await conn.execute(
                """
                UPDATE user_credit_allocations
                SET next_reset_date = COALESCE($1, next_reset_date),
                    notes = COALESCE($2, notes),
                    reset_period = $3
                WHERE org_id = $4 AND user_id = $5
                """,
                next_reset, allocation.notes, allocation.reset_period,
                org_id, allocation.user_id
            )

        logger.info(f"Allocated {allocation.allocated_credits} credits to user {allocation.user_id} in org {org_id}")

        # Get updated allocation
        alloc = await conn.fetchrow(
            """
            SELECT * FROM user_credit_allocations
            WHERE org_id = $1 AND user_id = $2
            """,
            org_id, allocation.user_id
        )

        return UserCreditAllocationResponse(
            id=str(alloc["id"]),
            org_id=str(alloc["org_id"]),
            user_id=alloc["user_id"],
            user_email=None,  # TODO: Fetch from Keycloak
            user_name=None,
            allocated_credits=alloc["allocated_credits"],
            used_credits=alloc["used_credits"],
            remaining_credits=alloc["remaining_credits"],
            reset_period=alloc["reset_period"],
            last_reset_date=alloc["last_reset_date"],
            next_reset_date=alloc["next_reset_date"],
            is_active=alloc["is_active"],
            created_at=alloc["created_at"]
        )

    finally:
        await conn.close()


@router.get("/credits/{org_id}/allocations", response_model=List[UserCreditAllocationResponse])
async def get_organization_credit_allocations(org_id: str, request: Request):
    """
    Get all user credit allocations for organization

    **Required Role**: Org Admin or System Admin

    **Returns**: List of all users with credit allocations in this org
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to view allocations")

        # Get all allocations
        allocations = await conn.fetch(
            """
            SELECT * FROM user_credit_allocations
            WHERE org_id = $1 AND is_active = TRUE
            ORDER BY created_at DESC
            """,
            org_id
        )

        return [
            UserCreditAllocationResponse(
                id=str(a["id"]),
                org_id=str(a["org_id"]),
                user_id=a["user_id"],
                user_email=None,  # TODO: Fetch from Keycloak
                user_name=None,
                allocated_credits=a["allocated_credits"],
                used_credits=a["used_credits"],
                remaining_credits=a["remaining_credits"],
                reset_period=a["reset_period"],
                last_reset_date=a["last_reset_date"],
                next_reset_date=a["next_reset_date"],
                is_active=a["is_active"],
                created_at=a["created_at"]
            )
            for a in allocations
        ]

    finally:
        await conn.close()


@router.get("/credits/{org_id}/usage", response_model=CreditUsageStatsResponse)
async def get_organization_credit_usage(
    org_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    request: Request = None
):
    """
    Get organization credit usage statistics

    **Required Role**: Org Member or System Admin

    **Returns**:
    - Total credits used in period
    - Service breakdown (LLM, image generation, etc.)
    - Top users by usage
    - Daily usage trends
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check membership
        is_admin = await check_system_admin(user)
        if not is_admin:
            member = await conn.fetchval(
                "SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2",
                org_id, user["user_id"]
            )
            if not member:
                raise HTTPException(status_code=403, detail="Not a member of this organization")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get usage summary
        usage = await conn.fetchrow(
            """
            SELECT
                COUNT(DISTINCT user_id) as user_count,
                SUM(credits_used) as total_credits_used
            FROM credit_usage_attribution
            WHERE org_id = $1 AND created_at >= $2 AND created_at <= $3
            """,
            org_id, start_date, end_date
        )

        # Get service breakdown
        services = await conn.fetch(
            """
            SELECT service_type, SUM(credits_used) as credits
            FROM credit_usage_attribution
            WHERE org_id = $1 AND created_at >= $2 AND created_at <= $3
            GROUP BY service_type
            ORDER BY credits DESC
            """,
            org_id, start_date, end_date
        )

        service_breakdown = {s["service_type"]: s["credits"] for s in services}

        # Get top users
        top_users = await conn.fetch(
            """
            SELECT
                user_id,
                SUM(credits_used) as total_credits,
                COUNT(*) as request_count
            FROM credit_usage_attribution
            WHERE org_id = $1 AND created_at >= $2 AND created_at <= $3
            GROUP BY user_id
            ORDER BY total_credits DESC
            LIMIT 10
            """,
            org_id, start_date, end_date
        )

        top_users_list = [
            {
                "user_id": u["user_id"],
                "total_credits": u["total_credits"],
                "request_count": u["request_count"]
            }
            for u in top_users
        ]

        return CreditUsageStatsResponse(
            org_id=org_id,
            total_credits_used=usage["total_credits_used"] or 0,
            user_count=usage["user_count"] or 0,
            service_breakdown=service_breakdown,
            top_users=top_users_list,
            date_range_start=start_date,
            date_range_end=end_date
        )

    finally:
        await conn.close()


# ==================== Billing Screen Endpoints ====================

@router.get("/billing/user", response_model=Dict)
@limiter.limit("100/minute")  # Rate limit: 100 GET requests per minute
async def get_user_billing_dashboard(request: Request):
    """
    User billing dashboard - shows all organizations user belongs to

    **Required Role**: Any authenticated user

    **Returns**:
    - List of organizations user is member of
    - Credit allocation in each org
    - Personal usage statistics
    - Multi-org credit selector
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Get all organizations user belongs to
        orgs = await conn.fetch(
            """
            SELECT
                o.id as org_id,
                o.name as org_name,
                om.role,
                uca.allocated_credits,
                uca.used_credits,
                uca.remaining_credits,
                os.subscription_plan,
                os.monthly_price
            FROM organization_members om
            JOIN organizations o ON om.org_id = o.id
            LEFT JOIN user_credit_allocations uca ON uca.org_id = o.id AND uca.user_id = om.user_id AND uca.is_active = TRUE
            LEFT JOIN organization_subscriptions os ON os.org_id = o.id AND os.status = 'active'
            WHERE om.user_id = $1 AND o.status = 'active'
            ORDER BY o.name
            """,
            user["user_id"]
        )

        # Get user's total usage across all orgs
        total_usage = await conn.fetchrow(
            """
            SELECT
                SUM(credits_used) as total_credits_used,
                COUNT(DISTINCT org_id) as org_count,
                COUNT(*) as request_count
            FROM credit_usage_attribution
            WHERE user_id = $1 AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            """,
            user["user_id"]
        )

        return {
            "user_id": user["user_id"],
            "user_email": user.get("email"),
            "organizations": [
                {
                    "org_id": str(org["org_id"]),
                    "org_name": org["org_name"],
                    "role": org["role"],
                    "subscription_plan": org["subscription_plan"],
                    "monthly_price": float(org["monthly_price"]) if org["monthly_price"] else 0,
                    "allocated_credits": org["allocated_credits"] or 0,
                    "used_credits": org["used_credits"] or 0,
                    "remaining_credits": org["remaining_credits"] or 0
                }
                for org in orgs
            ],
            "total_usage_last_30_days": {
                "total_credits_used": total_usage["total_credits_used"] or 0,
                "org_count": total_usage["org_count"] or 0,
                "request_count": total_usage["request_count"] or 0
            }
        }

    finally:
        await conn.close()


@router.get("/billing/org/{org_id}", response_model=Dict)
async def get_org_admin_billing_screen(org_id: str, request: Request):
    """
    Organization admin billing screen

    **Required Role**: Org Admin or System Admin

    **Returns**:
    - Organization subscription plan
    - Credit pool management
    - Per-user allocations table
    - Usage attribution by user
    - Upgrade/downgrade options
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to view org billing")

        # Get organization info
        org = await conn.fetchrow(
            "SELECT * FROM organizations WHERE id = $1",
            org_id
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Get subscription
        subscription = await conn.fetchrow(
            "SELECT * FROM organization_subscriptions WHERE org_id = $1 AND status = 'active'",
            org_id
        )

        # Get credit pool
        credit_pool = await conn.fetchrow(
            "SELECT * FROM organization_credit_pools WHERE org_id = $1",
            org_id
        )

        # Get user allocations
        allocations = await conn.fetch(
            """
            SELECT * FROM user_credit_allocations
            WHERE org_id = $1 AND is_active = TRUE
            ORDER BY used_credits DESC
            """,
            org_id
        )

        # Get usage stats (last 30 days)
        usage_stats = await conn.fetchrow(
            """
            SELECT
                SUM(credits_used) as total_credits_used,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_requests
            FROM credit_usage_attribution
            WHERE org_id = $1 AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            """,
            org_id
        )

        return {
            "organization": {
                "id": str(org["id"]),
                "name": org["name"],
                "display_name": org["display_name"],
                "max_seats": org["max_seats"],
                "status": org["status"]
            },
            "subscription": {
                "plan": subscription["subscription_plan"] if subscription else None,
                "monthly_price": float(subscription["monthly_price"]) if subscription else 0,
                "status": subscription["status"] if subscription else None,
                "current_period_end": subscription["current_period_end"] if subscription else None
            } if subscription else None,
            "credit_pool": {
                "total_credits": credit_pool["total_credits"] if credit_pool else 0,
                "allocated_credits": credit_pool["allocated_credits"] if credit_pool else 0,
                "used_credits": credit_pool["used_credits"] if credit_pool else 0,
                "available_credits": credit_pool["available_credits"] if credit_pool else 0,
                "monthly_refresh_amount": credit_pool["monthly_refresh_amount"] if credit_pool else 0
            } if credit_pool else None,
            "user_allocations": [
                {
                    "user_id": a["user_id"],
                    "allocated_credits": a["allocated_credits"],
                    "used_credits": a["used_credits"],
                    "remaining_credits": a["remaining_credits"],
                    "reset_period": a["reset_period"]
                }
                for a in allocations
            ],
            "usage_stats_30_days": {
                "total_credits_used": usage_stats["total_credits_used"] or 0,
                "active_users": usage_stats["active_users"] or 0,
                "total_requests": usage_stats["total_requests"] or 0
            }
        }

    finally:
        await conn.close()


@router.get("/billing/system", response_model=Dict)
async def get_system_admin_billing_screen(request: Request):
    """
    System admin billing overview screen

    **Required Role**: System Admin

    **Returns**:
    - All organizations list with billing status
    - Revenue analytics (MRR, ARR)
    - Subscription distribution (Platform vs BYOK vs Hybrid)
    - Top organizations by usage
    - Credit pool summaries
    """
    user = await get_current_user(request)

    # Check system admin
    is_admin = await check_system_admin(user)
    if not is_admin:
        raise HTTPException(status_code=403, detail="System admin access required")

    conn = await get_db_connection()
    try:
        # Get all organizations with billing data
        orgs = await conn.fetch(
            """
            SELECT * FROM org_billing_summary
            ORDER BY lifetime_spent_amount DESC
            """
        )

        # Get subscription distribution
        sub_distribution = await conn.fetch(
            """
            SELECT
                subscription_plan,
                COUNT(*) as count,
                SUM(monthly_price) as total_mrr
            FROM organization_subscriptions
            WHERE status = 'active'
            GROUP BY subscription_plan
            """
        )

        # Calculate total MRR and ARR
        total_mrr = sum(float(d["total_mrr"]) for d in sub_distribution)
        total_arr = total_mrr * 12

        # Get top credit users across all orgs
        top_orgs = await conn.fetch(
            """
            SELECT
                org_id,
                SUM(credits_used) as total_credits,
                COUNT(DISTINCT user_id) as user_count
            FROM credit_usage_attribution
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            GROUP BY org_id
            ORDER BY total_credits DESC
            LIMIT 10
            """
        )

        return {
            "organizations": [
                {
                    "org_id": str(org["org_id"]),
                    "org_name": org["org_name"],
                    "subscription_plan": org["subscription_plan"],
                    "monthly_price": float(org["monthly_price"]) if org["monthly_price"] else 0,
                    "subscription_status": org["subscription_status"],
                    "total_credits": org["total_credits"],
                    "used_credits": org["used_credits"],
                    "member_count": org["member_count"],
                    "lifetime_spent": float(org["lifetime_spent_amount"])
                }
                for org in orgs
            ],
            "revenue_metrics": {
                "total_mrr": total_mrr,
                "total_arr": total_arr,
                "active_subscriptions": sum(d["count"] for d in sub_distribution)
            },
            "subscription_distribution": [
                {
                    "plan": d["subscription_plan"],
                    "count": d["count"],
                    "mrr": float(d["total_mrr"])
                }
                for d in sub_distribution
            ],
            "top_organizations_by_usage": [
                {
                    "org_id": str(org["org_id"]),
                    "total_credits_30_days": org["total_credits"],
                    "user_count": org["user_count"]
                }
                for org in top_orgs
            ]
        }

    finally:
        await conn.close()


# ==================== Billing History Endpoints ====================

@router.get("/billing/{org_id}/history", response_model=List[BillingHistoryResponse])
async def get_billing_history(
    org_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    request: Request = None
):
    """
    Get organization billing history (invoices, payments, events)

    **Required Role**: Org Admin or System Admin
    """
    user = await get_current_user(request)

    conn = await get_db_connection()
    try:
        # Check permissions
        is_admin = await check_system_admin(user)
        is_org_admin = await check_org_admin(conn, org_id, user["user_id"])

        if not is_admin and not is_org_admin:
            raise HTTPException(status_code=403, detail="Not authorized to view billing history")

        history = await conn.fetch(
            """
            SELECT * FROM org_billing_history
            WHERE org_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            org_id, limit, offset
        )

        return [
            BillingHistoryResponse(
                id=str(h["id"]),
                org_id=str(h["org_id"]),
                event_type=h["event_type"],
                amount=h["amount"],
                currency=h["currency"],
                payment_status=h["payment_status"],
                period_start=h["period_start"],
                period_end=h["period_end"],
                created_at=h["created_at"]
            )
            for h in history
        ]

    finally:
        await conn.close()
