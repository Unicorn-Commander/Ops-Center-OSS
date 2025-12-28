"""
Epic 1.8: Credit & Usage Metering System
Module: credit_api.py

Purpose: Comprehensive REST API for credit management, usage tracking,
         OpenRouter BYOK, and coupon redemption.

Author: Backend Team Lead
Date: October 23, 2025

Endpoints: 20 total
- Credit Management: 5 endpoints
- OpenRouter BYOK: 4 endpoints
- Usage Metering: 5 endpoints
- Coupon System: 5 endpoints
- Tier Management: 1 endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from credit_system import credit_manager, InsufficientCreditsError, CreditError
from openrouter_automation import openrouter_manager, OpenRouterError
from usage_metering import usage_meter
from coupon_system import coupon_manager, CouponError
from audit_logger import audit_logger
from email_notifications import EmailNotificationService

# Email notification service
email_service = EmailNotificationService()

# Import Request for manual session handling (avoids circular import)
from fastapi import Request

# Manual authentication function (matches server.py logic)
async def get_current_user_from_request(request: Request):
    """Get current user from session cookie (avoids circular import with server.py)"""
    # Import here to avoid circular dependency
    import sys
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    # Import sessions from server module
    from redis_session import RedisSessionManager
    import os

    # Get Redis connection (same as server.py)
    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session token from cookie
    session_token = request.cookies.get("session_token")

    if not session_token or session_token not in sessions:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = sessions[session_token]
    user_data = session.get("user", {})

    # Ensure user_id field exists (map from Keycloak 'sub' field)
    if "user_id" not in user_data:
        user_data["user_id"] = user_data.get("sub") or user_data.get("id", "unknown")

    return user_data

# Admin check function
async def require_admin_from_request(current_user: dict = Depends(get_current_user_from_request)):
    """Require admin role"""
    from fastapi import HTTPException
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Aliases for compatibility
get_current_user = get_current_user_from_request
require_admin = require_admin_from_request


# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Router
router = APIRouter(prefix="/api/v1/credits", tags=["credits"])


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

# Credit Models
class CreditBalance(BaseModel):
    """User credit balance response"""
    user_id: str
    balance: Decimal  # maps to credits_remaining
    allocated_monthly: Decimal  # maps to credits_allocated
    bonus_credits: Decimal = Decimal("0.00")  # calculated field (not in DB)
    free_tier_used: Decimal = Decimal("0.00")  # calculated field (not in DB)
    reset_date: datetime  # maps to last_reset
    last_updated: datetime  # maps to updated_at
    tier: str  # subscription tier from DB
    created_at: datetime


class CreditTransaction(BaseModel):
    """Credit transaction record"""
    id: str  # UUID in database
    user_id: str
    amount: Decimal
    balance_after: Decimal
    transaction_type: str
    service: Optional[str]  # maps to 'provider' column
    model: Optional[str]
    cost_breakdown: Optional[Decimal]  # maps to 'cost' column
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class CreditAllocationRequest(BaseModel):
    """Request to allocate credits to user"""
    user_id: str = Field(..., description="Keycloak user ID")
    amount: Decimal = Field(..., gt=0, description="Credit amount to allocate")
    source: str = Field(..., description="Source of allocation (tier_upgrade, manual, bonus, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class CreditDeductionRequest(BaseModel):
    """Request to deduct credits from user"""
    user_id: str = Field(..., description="Keycloak user ID")
    amount: Decimal = Field(..., gt=0, description="Credit amount to deduct")
    service: str = Field(..., description="Service name (openrouter, embedding, tts, etc.)")
    model: Optional[str] = Field(None, description="Model name")
    cost_breakdown: Optional[Dict[str, Any]] = Field(None, description="Cost breakdown")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class CreditRefundRequest(BaseModel):
    """Request to refund credits to user"""
    user_id: str = Field(..., description="Keycloak user ID")
    amount: Decimal = Field(..., gt=0, description="Refund amount")
    reason: str = Field(..., description="Reason for refund")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


# OpenRouter Models
class OpenRouterCreateRequest(BaseModel):
    """Request to create OpenRouter BYOK account"""
    api_key: str = Field(..., description="User's OpenRouter API key")
    email: Optional[str] = Field(None, description="User's email (optional)")


class OpenRouterAccount(BaseModel):
    """OpenRouter account information"""
    user_id: str
    email: Optional[str]
    account_id: Optional[str]
    free_credits_remaining: Decimal
    is_active: bool
    last_synced: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Usage Metering Models
class UsageTrackRequest(BaseModel):
    """Request to track usage event"""
    service: str = Field(..., description="Service name (openrouter, embedding, tts, etc.)")
    model: Optional[str] = Field(None, description="Model name")
    tokens: Optional[int] = Field(None, ge=0, description="Tokens used")
    cost: Optional[Decimal] = Field(None, ge=0, description="Cost in credits (optional, will be calculated)")
    is_free: bool = Field(False, description="Whether this is free tier usage")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UsageEvent(BaseModel):
    """Usage event record"""
    id: int
    user_id: str
    service: str
    model: Optional[str]
    tokens_used: Optional[int]
    provider_cost: Decimal
    platform_markup: Decimal
    total_cost: Decimal
    is_free_tier: bool
    created_at: datetime


class UsageSummary(BaseModel):
    """Aggregated usage summary"""
    total_events: int
    total_tokens: int
    total_cost: Decimal
    free_tier_events: int
    paid_tier_events: int
    services: Dict[str, Dict[str, Any]]
    period: Dict[str, str]


class UsageByModel(BaseModel):
    """Usage breakdown by model"""
    service: str
    model: str
    event_count: int
    total_tokens: int
    total_cost: Decimal
    avg_tokens: float
    free_events: int


class UsageByService(BaseModel):
    """Usage breakdown by service"""
    service: str
    event_count: int
    total_tokens: int
    total_cost: Decimal
    unique_models: int
    free_events: int


# Coupon Models
class CouponCode(BaseModel):
    """Coupon code information"""
    code: str
    coupon_type: str
    value: Decimal
    description: Optional[str]
    max_uses: Optional[int]
    used_count: int
    remaining_uses: Optional[int]
    expires_at: Optional[datetime]
    is_active: bool
    is_expired: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CouponCreateRequest(BaseModel):
    """Request to create coupon"""
    coupon_type: str = Field(..., description="Type: free_month, credit_bonus, percentage_discount, fixed_discount")
    value: Decimal = Field(..., gt=0, description="Coupon value (credits, percentage, or dollar amount)")
    code: Optional[str] = Field(None, description="Custom code (optional, will be generated)")
    description: Optional[str] = Field(None, description="Human-readable description")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum redemptions allowed (None = unlimited)")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (None = never expires)")

    @validator("coupon_type")
    def validate_coupon_type(cls, v):
        valid_types = ["free_month", "credit_bonus", "percentage_discount", "fixed_discount"]
        if v not in valid_types:
            raise ValueError(f"Invalid coupon type. Must be one of: {valid_types}")
        return v


class CouponRedeemRequest(BaseModel):
    """Request to redeem coupon"""
    code: str = Field(..., description="Coupon code to redeem")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CouponValidation(BaseModel):
    """Coupon validation result"""
    valid: bool
    reason: Optional[str] = None
    coupon: Optional[CouponCode] = None


class CouponRedemption(BaseModel):
    """Coupon redemption result"""
    code: str
    coupon_type: str
    value: Decimal
    credits_awarded: Decimal
    redeemed_at: datetime


# Tier Models
class TierInfo(BaseModel):
    """Subscription tier information"""
    tier: str
    price_monthly: Decimal
    credits_monthly: Decimal
    features: List[str]


class TierSwitchRequest(BaseModel):
    """Request to switch subscription tier"""
    new_tier: str = Field(..., description="New tier: trial, starter, professional, enterprise")

    @validator("new_tier")
    def validate_tier(cls, v):
        valid_tiers = ["trial", "starter", "professional", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier. Must be one of: {valid_tiers}")
        return v


# ============================================================================
# Credit Management Endpoints (5 endpoints)
# ============================================================================

@router.get("/balance", response_model=CreditBalance)
async def get_credit_balance(current_user: dict = Depends(get_current_user)):
    """
    Get user's current credit balance.

    Returns:
        CreditBalance: Current balance and allocation details
    """
    try:
        balance = await credit_manager.get_balance(current_user["user_id"])
        return CreditBalance(**balance)
    except Exception as e:
        logger.error(f"Failed to get credit balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/allocate", response_model=CreditBalance)
async def allocate_credits(
    request: CreditAllocationRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Allocate credits to a user (admin only).

    Args:
        request: Credit allocation details

    Returns:
        CreditBalance: Updated balance information
    """
    try:
        balance = await credit_manager.allocate_credits(
            user_id=request.user_id,
            amount=request.amount,
            source=request.source,
            metadata=request.metadata
        )
        return CreditBalance(**balance)
    except Exception as e:
        logger.error(f"Failed to allocate credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[CreditTransaction])
async def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    transaction_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get credit transaction history.

    Args:
        limit: Maximum number of transactions (1-500)
        offset: Pagination offset
        transaction_type: Filter by type (optional)

    Returns:
        List[CreditTransaction]: Transaction history
    """
    try:
        transactions = await credit_manager.get_transactions(
            user_id=current_user["user_id"],
            limit=limit,
            offset=offset,
            transaction_type=transaction_type
        )
        return [CreditTransaction(**tx) for tx in transactions]
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deduct", response_model=CreditBalance)
async def deduct_credits(
    request: CreditDeductionRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Deduct credits from user (internal/admin only).

    Args:
        request: Credit deduction details

    Returns:
        CreditBalance: Updated balance information

    Raises:
        HTTPException 400: Insufficient credits
    """
    # Add audit log
    logger.info(
        f"AUDIT: Admin credit deduction - admin={current_user.get('user_id', 'unknown')}, "
        f"target_user={request.user_id}, amount={request.amount}, service={request.service}"
    )

    try:
        balance = await credit_manager.deduct_credits(
            user_id=request.user_id,
            amount=request.amount,
            service=request.service,
            model=request.model,
            cost_breakdown=request.cost_breakdown,
            metadata=request.metadata
        )
        return CreditBalance(**balance)
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deduct credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund", response_model=CreditBalance)
async def refund_credits(
    request: CreditRefundRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Refund credits to user (admin only).

    Args:
        request: Refund details

    Returns:
        CreditBalance: Updated balance information
    """
    try:
        balance = await credit_manager.refund_credits(
            user_id=request.user_id,
            amount=request.amount,
            reason=request.reason,
            metadata=request.metadata
        )
        return CreditBalance(**balance)
    except Exception as e:
        logger.error(f"Failed to refund credits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OpenRouter BYOK Endpoints (4 endpoints)
# ============================================================================

@router.post("/openrouter/create-account", response_model=OpenRouterAccount)
async def create_openrouter_account(
    request: OpenRouterCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create OpenRouter BYOK account for user.

    Args:
        request: OpenRouter API key and email

    Returns:
        OpenRouterAccount: Account information
    """
    try:
        account = await openrouter_manager.create_account(
            user_id=current_user["user_id"],
            api_key=request.api_key,
            user_email=request.email
        )
        return OpenRouterAccount(**account)
    except OpenRouterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create OpenRouter account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openrouter/account", response_model=Optional[OpenRouterAccount])
async def get_openrouter_account(current_user: dict = Depends(get_current_user)):
    """
    Get OpenRouter account details.

    Returns:
        OpenRouterAccount | None: Account information or None if not configured
    """
    try:
        account = await openrouter_manager.get_account(current_user["user_id"])
        if not account:
            return None
        return OpenRouterAccount(**account)
    except Exception as e:
        logger.error(f"Failed to get OpenRouter account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/openrouter/sync-balance", response_model=Dict[str, Decimal])
async def sync_openrouter_balance(current_user: dict = Depends(get_current_user)):
    """
    Sync free credits from OpenRouter API.

    Returns:
        Dict: {"free_credits": Decimal}
    """
    try:
        free_credits = await openrouter_manager.sync_free_credits(current_user["user_id"])
        return {"free_credits": free_credits}
    except OpenRouterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync OpenRouter balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/openrouter/account", response_model=Dict[str, str])
async def delete_openrouter_account(current_user: dict = Depends(get_current_user)):
    """
    Delete OpenRouter BYOK account.

    Returns:
        Dict: Success message
    """
    try:
        await openrouter_manager.delete_account(current_user["user_id"])
        return {"message": "OpenRouter account deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete OpenRouter account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Usage Metering Endpoints (5 endpoints)
# ============================================================================

@router.post("/usage/track", response_model=UsageEvent)
async def track_usage(
    request: UsageTrackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Track API usage event.

    Args:
        request: Usage event details

    Returns:
        UsageEvent: Created usage event
    """
    try:
        event = await usage_meter.track_usage(
            user_id=current_user["user_id"],
            service=request.service,
            model=request.model,
            tokens=request.tokens,
            cost=request.cost,
            is_free=request.is_free,
            metadata=request.metadata
        )
        return UsageEvent(**event)
    except Exception as e:
        logger.error(f"Failed to track usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/summary", response_model=UsageSummary)
async def get_usage_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get usage summary for user.

    Args:
        start_date: Start date (optional, defaults to 30 days ago)
        end_date: End date (optional, defaults to now)

    Returns:
        UsageSummary: Aggregated usage statistics
    """
    try:
        summary = await usage_meter.get_usage_summary(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
        return UsageSummary(**summary)
    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/by-model", response_model=List[UsageByModel])
async def get_usage_by_model(current_user: dict = Depends(get_current_user)):
    """
    Get usage breakdown by model.

    Returns:
        List[UsageByModel]: Per-model usage statistics
    """
    try:
        usage = await usage_meter.get_usage_by_model(current_user["user_id"])
        return [UsageByModel(**item) for item in usage]
    except Exception as e:
        logger.error(f"Failed to get usage by model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/by-service", response_model=List[UsageByService])
async def get_usage_by_service(current_user: dict = Depends(get_current_user)):
    """
    Get usage breakdown by service.

    Returns:
        List[UsageByService]: Per-service usage statistics
    """
    try:
        usage = await usage_meter.get_usage_by_service(current_user["user_id"])
        return [UsageByService(**item) for item in usage]
    except Exception as e:
        logger.error(f"Failed to get usage by service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/free-tier", response_model=Dict[str, Any])
async def get_free_tier_usage(current_user: dict = Depends(get_current_user)):
    """
    Get free tier usage statistics.

    Returns:
        Dict: Free tier usage summary
    """
    try:
        usage = await usage_meter.get_free_tier_usage(current_user["user_id"])
        return usage
    except Exception as e:
        logger.error(f"Failed to get free tier usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Coupon Endpoints (5 endpoints)
# ============================================================================

@router.post("/coupons/redeem", response_model=CouponRedemption)
async def redeem_coupon(
    request: CouponRedeemRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Redeem coupon code.

    Args:
        request: Coupon code to redeem

    Returns:
        CouponRedemption: Redemption details with credits awarded
    """
    try:
        redemption = await coupon_manager.redeem_coupon(
            code=request.code,
            user_id=current_user["user_id"],
            metadata=request.metadata
        )

        # Send coupon redemption confirmation email (don't fail if email fails)
        try:
            # Get updated balance after redemption
            balance = await credit_manager.get_balance(current_user["user_id"])
            await email_service.send_coupon_redemption_confirmation(
                user_id=current_user["user_id"],
                coupon_code=request.code,
                credits_added=redemption["credits_awarded"],
                new_balance=balance["credits_remaining"]
            )
            logger.info(f"Coupon redemption confirmation sent to user {current_user['user_id']}")
        except Exception as e:
            logger.error(f"Failed to send coupon confirmation email: {e}")

        return CouponRedemption(**redemption)
    except CouponError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to redeem coupon: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coupons/create", response_model=CouponCode)
async def create_coupon(
    request: CouponCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create coupon code (admin only).

    Args:
        request: Coupon details

    Returns:
        CouponCode: Created coupon information
    """
    try:
        coupon = await coupon_manager.create_coupon(
            coupon_type=request.coupon_type,
            value=request.value,
            code=request.code,
            description=request.description,
            max_uses=request.max_uses,
            expires_at=request.expires_at,
            created_by=current_user["user_id"]
        )
        return CouponCode(**coupon)
    except CouponError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create coupon: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coupons/validate/{code}", response_model=CouponValidation)
async def validate_coupon(code: str, current_user: dict = Depends(get_current_user)):
    """
    Validate coupon code.

    Args:
        code: Coupon code to validate

    Returns:
        CouponValidation: Validation result
    """
    try:
        validation = await coupon_manager.validate_coupon(code, current_user["user_id"])

        if validation["valid"] and validation.get("coupon"):
            validation["coupon"] = CouponCode(**validation["coupon"])

        return CouponValidation(**validation)
    except Exception as e:
        logger.error(f"Failed to validate coupon: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coupons", response_model=List[CouponCode])
async def list_coupons(
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """
    List all coupons (admin only).

    Args:
        active_only: Only return active coupons
        limit: Maximum number of coupons
        offset: Pagination offset

    Returns:
        List[CouponCode]: List of coupons
    """
    try:
        coupons = await coupon_manager.list_coupons(
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        return [CouponCode(**coupon) for coupon in coupons]
    except Exception as e:
        logger.error(f"Failed to list coupons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/coupons/{code}", response_model=Dict[str, str])
async def delete_coupon(
    code: str,
    current_user: dict = Depends(require_admin)
):
    """
    Deactivate coupon (admin only).

    Args:
        code: Coupon code to deactivate

    Returns:
        Dict: Success message
    """
    try:
        await coupon_manager.deactivate_coupon(code, current_user["user_id"])
        return {"message": f"Coupon '{code}' deactivated successfully"}
    except CouponError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete coupon: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tier Management Endpoint (1 endpoint)
# ============================================================================

@router.get("/tiers/compare", response_model=List[TierInfo])
async def compare_tiers():
    """
    Compare subscription tiers.

    Returns:
        List[TierInfo]: Available subscription tiers
    """
    tiers = [
        {
            "tier": "trial",
            "price_monthly": Decimal("4.00"),
            "credits_monthly": Decimal("5.00"),
            "features": [
                "100 API calls per day",
                "Open-WebUI access",
                "Basic AI models",
                "Community support"
            ]
        },
        {
            "tier": "starter",
            "price_monthly": Decimal("19.00"),
            "credits_monthly": Decimal("20.00"),
            "features": [
                "1,000 API calls per month",
                "Open-WebUI + Center-Deep",
                "All AI models",
                "BYOK support",
                "Email support"
            ]
        },
        {
            "tier": "professional",
            "price_monthly": Decimal("49.00"),
            "credits_monthly": Decimal("60.00"),
            "features": [
                "10,000 API calls per month",
                "All services (Chat, Search, TTS, STT)",
                "Billing dashboard access",
                "Priority support",
                "BYOK support"
            ]
        },
        {
            "tier": "enterprise",
            "price_monthly": Decimal("99.00"),
            "credits_monthly": Decimal("999999.99"),
            "features": [
                "Unlimited API calls",
                "Team management (5 seats)",
                "Custom integrations",
                "24/7 dedicated support",
                "White-label options"
            ]
        }
    ]

    return [TierInfo(**tier) for tier in tiers]


@router.post("/tiers/switch", response_model=CreditBalance)
async def switch_tier(
    request: TierSwitchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Switch subscription tier (triggers monthly credit reset).

    Args:
        request: New tier selection

    Returns:
        CreditBalance: Updated balance with new allocation
    """
    try:
        balance = await credit_manager.reset_monthly_credits(
            user_id=current_user["user_id"],
            new_tier=request.new_tier
        )
        return CreditBalance(**balance)
    except Exception as e:
        logger.error(f"Failed to switch tier: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@router.on_event("startup")
async def startup():
    """Initialize all managers on startup"""
    await credit_manager.initialize()
    await openrouter_manager.initialize()
    await usage_meter.initialize()
    await coupon_manager.initialize()
    logger.info("Credit API initialized successfully")


@router.on_event("shutdown")
async def shutdown():
    """Close all managers on shutdown"""
    await credit_manager.close()
    await openrouter_manager.close()
    await usage_meter.close()
    await coupon_manager.close()
    logger.info("Credit API shutdown complete")
