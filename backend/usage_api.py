"""
Usage Tracking API

Provides endpoints for monitoring API usage, subscription tier status,
and usage statistics for the current user.

Integrates with both Keycloak (user attributes) and Lago (metered usage).
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
import logging
import csv
import io

# Import Keycloak integration
from keycloak_integration import get_user_tier_info, reset_usage

# Import Lago integration
from lago_integration import (
    get_current_usage,
    get_subscription
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


async def get_current_user_email(request: Request) -> str:
    """Get current user's email from session"""

    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get sessions from app state
    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    email = user.get("email")

    if not email:
        raise HTTPException(status_code=401, detail="User email not found in session")

    return email


async def get_user_org_id(request: Request) -> str:
    """Get organization ID from user session"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sessions = getattr(request.app.state, "sessions", {})
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = session_data.get("user", {})
    org_id = user.get("org_id")

    if not org_id:
        # Fallback: generate org_id from email
        email = user.get("email")
        if email:
            org_id = f"org_{email.split('@')[0]}_{user.get('id', 'unknown')}"
            logger.warning(f"No org_id found, using generated: {org_id}")
        else:
            raise HTTPException(status_code=400, detail="Cannot determine org_id")

    return org_id


async def get_user_tier_data(user_email: str) -> Dict:
    """Fetch user tier and usage info from Keycloak"""
    try:
        tier_info = await get_user_tier_info(user_email)

        if not tier_info:
            raise HTTPException(status_code=404, detail="User not found")

        return tier_info

    except Exception as e:
        logger.error(f"Error fetching user tier from Keycloak: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch user tier information")


# Tier limits mapping
TIER_LIMITS = {
    "trial": {"daily": 100, "monthly": 3000, "name": "Trial"},
    "free": {"daily": 33, "monthly": 1000, "name": "Free"},
    "starter": {"daily": 33, "monthly": 1000, "name": "Starter"},
    "professional": {"daily": 333, "monthly": 10000, "name": "Professional"},
    "enterprise": {"daily": -1, "monthly": -1, "name": "Enterprise"},
}

# Tier features mapping
TIER_FEATURES = {
    "trial": ["chat", "ops-center"],
    "free": ["chat", "ops-center"],
    "starter": ["chat", "ops-center"],
    "professional": ["chat", "ops-center", "search", "litellm", "billing", "tts", "stt"],
    "enterprise": ["chat", "ops-center", "search", "litellm", "billing", "tts", "stt", "team-management", "sso", "audit-logs"],
}


@router.get("/current")
async def get_current_usage_endpoint(request: Request):
    """
    Get current usage statistics for the authenticated user.
    Integrates data from both Keycloak (tier) and Lago (metered usage).

    Returns tier info, usage counts, limits, and service breakdown.
    """

    user_email = await get_current_user_email(request)
    org_id = await get_user_org_id(request)
    tier_info = await get_user_tier_data(user_email)

    tier = tier_info.get("subscription_tier", "trial")

    # Get usage from Lago if available
    lago_usage = {}
    try:
        lago_usage = await get_current_usage(org_id)
        logger.info(f"Retrieved Lago usage for org {org_id}")
    except Exception as e:
        logger.warning(f"Could not retrieve Lago usage: {e}, using Keycloak data")

    # Use Lago usage if available, otherwise fall back to Keycloak
    if lago_usage and "charges" in lago_usage:
        # Parse Lago usage data
        api_calls_used = 0
        credits_used = 0

        for charge in lago_usage.get("charges", []):
            # Sum up all metered usage
            api_calls_used += charge.get("units", 0)

        used = int(api_calls_used)
    else:
        # Fallback to Keycloak data
        used = tier_info.get("api_calls_used", 0)

    tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS["trial"])
    daily_limit = tier_limits["daily"]
    monthly_limit = tier_limits["monthly"]

    # Calculate reset date
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    reset_date = tier_info.get("api_calls_reset_date")

    # Calculate percentage and remaining
    if monthly_limit > 0:
        percentage_used = (used / monthly_limit) * 100
        remaining = max(0, monthly_limit - used)
    else:
        percentage_used = 0
        remaining = -1  # Unlimited

    # Service usage breakdown (from Lago if available)
    service_usage = {
        "chat": 0,
        "search": 0,
        "tts": 0,
        "stt": 0
    }

    if lago_usage and "charges" in lago_usage:
        for charge in lago_usage.get("charges", []):
            charge_name = charge.get("charge_model", "").lower()
            if "chat" in charge_name or "llm" in charge_name:
                service_usage["chat"] += charge.get("units", 0)
            elif "search" in charge_name:
                service_usage["search"] += charge.get("units", 0)
            elif "tts" in charge_name or "orator" in charge_name:
                service_usage["tts"] += charge.get("units", 0)
            elif "stt" in charge_name or "amanuensis" in charge_name:
                service_usage["stt"] += charge.get("units", 0)

    return {
        "api_calls_used": used,
        "api_calls_limit": monthly_limit if monthly_limit > 0 else -1,
        "credits_used": 0,  # TODO: Implement credits system
        "credits_remaining": 0,
        "reset_date": reset_date or tomorrow.isoformat(),
        "services": service_usage,
        "peak_usage": 0,  # TODO: Calculate from historical data
        "peak_date": None,
        "user": {
            "email": tier_info["email"],
            "username": tier_info["username"],
        },
        "subscription": {
            "tier": tier,
            "tier_name": tier_limits["name"],
            "status": tier_info.get("subscription_status", "active"),
        }
    }


@router.get("/history")
async def get_usage_history(request: Request, days: int = 30):
    """
    Get historical usage data.

    Args:
        days: Number of days of history to return (default: 30)

    Note: This endpoint is a placeholder. Full implementation requires
    storing historical usage data in a time-series database.
    """

    user_email = await get_current_user_email(request)
    tier_info = await get_user_tier_data(user_email)

    # TODO: Implement actual historical tracking
    # For now, return placeholder data
    return {
        "user": tier_info["email"],
        "days": days,
        "data": [],
        "message": "Usage history tracking coming soon. Currently showing today's usage only.",
        "current_usage": tier_info.get("api_calls_used", 0),
    }


@router.get("/limits")
async def get_tier_limits(request: Request):
    """
    Get tier limits and pricing information.

    Returns limits for all tiers for comparison.
    """

    user_email = await get_current_user_email(request)
    tier_info = await get_user_tier_data(user_email)

    current_tier = tier_info.get("subscription_tier", "trial")

    return {
        "current_tier": current_tier,
        "tiers": {
            tier_name: {
                "name": info["name"],
                "daily_limit": info["daily"] if info["daily"] > 0 else "unlimited",
                "monthly_limit": info["monthly"] if info["monthly"] > 0 else "unlimited",
                "features": TIER_FEATURES.get(tier_name, []),
                "is_current": tier_name == current_tier,
            }
            for tier_name, info in TIER_LIMITS.items()
        }
    }


@router.get("/features")
async def get_tier_features(request: Request):
    """
    Get feature access information for current tier.

    Returns which features are available and which require upgrade.
    """

    user_email = await get_current_user_email(request)
    tier_info = await get_user_tier_data(user_email)

    current_tier = tier_info.get("subscription_tier", "trial")
    current_features = TIER_FEATURES.get(current_tier, [])

    # All possible features
    all_features = set()
    for features in TIER_FEATURES.values():
        all_features.update(features)

    # Features requiring upgrade
    locked_features = all_features - set(current_features)

    return {
        "tier": current_tier,
        "available_features": current_features,
        "locked_features": list(locked_features),
        "all_features": list(all_features),
    }


@router.post("/reset-demo")
async def reset_usage_demo(request: Request):
    """
    DEMO/TESTING ONLY: Reset usage counter for current user.

    This endpoint should be disabled in production or protected with admin auth.
    """

    # Check if in development mode
    if os.getenv("ENVIRONMENT", "production") == "production":
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in development mode"
        )

    user_email = await get_current_user_email(request)

    try:
        # Use Keycloak integration to reset usage
        success = await reset_usage(user_email)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset usage counter")

        return {
            "message": "Usage counter reset successfully",
            "user": user_email,
            "reset_date": datetime.utcnow().date().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error resetting usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export")
async def export_usage_data(request: Request, period: str = "month"):
    """
    Export usage data as CSV file.

    Args:
        period: Time period for export (week, month, year)

    Returns:
        CSV file with usage statistics
    """

    user_email = await get_current_user_email(request)
    org_id = await get_user_org_id(request)
    tier_info = await get_user_tier_data(user_email)

    # Get current usage
    try:
        lago_usage = await get_current_usage(org_id)
    except Exception as e:
        logger.warning(f"Could not retrieve Lago usage for export: {e}")
        lago_usage = {}

    # Prepare CSV data
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "User Email",
        "Organization ID",
        "Subscription Tier",
        "Period",
        "Export Date",
        "API Calls Used",
        "Service",
        "Usage Amount"
    ])

    # Get service breakdown
    service_usage = {
        "chat": 0,
        "search": 0,
        "tts": 0,
        "stt": 0
    }

    if lago_usage and "charges" in lago_usage:
        for charge in lago_usage.get("charges", []):
            charge_name = charge.get("charge_model", "").lower()
            units = charge.get("units", 0)

            if "chat" in charge_name or "llm" in charge_name:
                service_usage["chat"] += units
            elif "search" in charge_name:
                service_usage["search"] += units
            elif "tts" in charge_name:
                service_usage["tts"] += units
            elif "stt" in charge_name:
                service_usage["stt"] += units

    # Write data rows
    tier = tier_info.get("subscription_tier", "trial")
    export_date = datetime.utcnow().isoformat()
    total_usage = sum(service_usage.values())

    for service, usage in service_usage.items():
        writer.writerow([
            user_email,
            org_id,
            tier,
            period,
            export_date,
            total_usage,
            service.upper(),
            usage
        ])

    # Create streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=usage-report-{period}-{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )
