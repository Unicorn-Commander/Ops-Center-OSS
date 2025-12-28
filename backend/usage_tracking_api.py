"""
Usage Tracking API Endpoints
=============================

RESTful API for accessing usage data, statistics, and limits.

Endpoints:
- GET /api/v1/usage/current - Current usage for authenticated user
- GET /api/v1/usage/history - Historical usage data
- GET /api/v1/admin/usage/organization/{org_id} - Org-wide usage (admin)
- GET /api/v1/usage/limits - Tier limits information
- POST /api/v1/usage/reset - Reset quota (admin only)

Author: Usage Tracking Team Lead
Date: November 12, 2025
"""

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from auth_dependencies import require_authenticated_user, require_admin_user
from usage_tracking import usage_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usage", tags=["usage-tracking"])


@router.get("/current")
async def get_current_usage(
    user: Dict = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    """
    Get current usage statistics for the authenticated user.

    Returns:
    - API calls used this period
    - Current limit based on tier
    - Remaining calls
    - Reset date
    - Daily and monthly breakdown
    """
    user_id = user.get("user_id")

    try:
        stats = await usage_tracker.get_usage_stats(user_id, period="current")

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "email": user.get("email"),
                "tier": stats["tier"],
                "status": stats["status"],
                "usage": {
                    "used": stats["used"],
                    "limit": stats["limit"],
                    "remaining": stats["remaining"],
                    "percentage": round((stats["used"] / stats["limit"]) * 100, 2) if stats["limit"] > 0 else 0
                },
                "daily": {
                    "used": stats["daily_usage"],
                    "limit": stats["daily_limit"]
                },
                "reset": {
                    "date": stats["reset_date"],
                    "days_until": (datetime.fromisoformat(stats["reset_date"]) - datetime.utcnow()).days
                }
            }
        }

    except Exception as e:
        logger.error(f"Error fetching usage for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch usage data")


@router.get("/history")
async def get_usage_history(
    period: str = Query("weekly", description="Time period: daily, weekly, monthly"),
    user: Dict = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    """
    Get historical usage data for charts and analytics.

    Args:
        period: Time period (daily, weekly, monthly)

    Returns:
        Historical usage data grouped by date
    """
    user_id = user.get("user_id")

    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use: daily, weekly, or monthly")

    try:
        stats = await usage_tracker.get_usage_stats(user_id, period=period)

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "period": period,
                "tier": stats["tier"],
                "current_usage": {
                    "used": stats["used"],
                    "limit": stats["limit"],
                    "remaining": stats["remaining"]
                },
                "history": stats.get("history", []),
                "summary": {
                    "total_calls": sum(h["calls"] for h in stats.get("history", [])),
                    "total_tokens": sum(h["tokens"] for h in stats.get("history", [])),
                    "total_cost": sum(h["cost"] for h in stats.get("history", []))
                }
            }
        }

    except Exception as e:
        logger.error(f"Error fetching usage history for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch usage history")


@router.get("/limits")
async def get_tier_limits(
    user: Dict = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    """
    Get tier limits information for all available tiers.

    Useful for showing upgrade options and comparing plans.
    """
    user_id = user.get("user_id")

    try:
        # Get user's current tier
        stats = await usage_tracker.get_usage_stats(user_id, period="current")
        current_tier = stats["tier"]

        # Get all tier limits
        all_limits = {}
        for tier_code in ["trial", "starter", "professional", "enterprise", "vip_founder", "byok"]:
            limits = usage_tracker.get_tier_limits(tier_code)
            all_limits[tier_code] = {
                "tier_code": tier_code,
                "tier_name": tier_code.replace("_", " ").title(),
                "daily_limit": limits["daily_limit"] if limits["daily_limit"] > 0 else "unlimited",
                "monthly_limit": limits["monthly_limit"] if limits["monthly_limit"] > 0 else "unlimited",
                "reset_period": limits["reset_period"],
                "is_current": tier_code == current_tier
            }

        return {
            "success": True,
            "data": {
                "current_tier": current_tier,
                "tiers": all_limits
            }
        }

    except Exception as e:
        logger.error(f"Error fetching tier limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch tier limits")


@router.get("/admin/organization/{org_id}")
async def get_org_usage(
    org_id: str,
    period: str = Query("current", description="Time period: current, daily, weekly, monthly"),
    user: Dict = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Get organization-wide usage statistics (admin only).

    Args:
        org_id: Organization UUID
        period: Time period for stats

    Returns:
        Aggregated usage across all org members
    """
    try:
        # Import org manager to get org members
        import sys
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')

        from org_manager import org_manager

        # Get organization members
        members = await org_manager.get_organization_members(org_id)

        if not members:
            raise HTTPException(status_code=404, detail="Organization not found or has no members")

        # Aggregate usage across all members
        total_used = 0
        total_limit = 0
        member_usage = []

        for member in members:
            member_id = member.get("user_id")
            if not member_id:
                continue

            try:
                stats = await usage_tracker.get_usage_stats(member_id, period=period)

                total_used += stats["used"]
                if stats["limit"] > 0:
                    total_limit += stats["limit"]

                member_usage.append({
                    "user_id": member_id,
                    "email": member.get("email"),
                    "name": member.get("name"),
                    "role": member.get("role"),
                    "tier": stats["tier"],
                    "used": stats["used"],
                    "limit": stats["limit"],
                    "remaining": stats["remaining"]
                })

            except Exception as e:
                logger.warning(f"Error fetching usage for member {member_id}: {e}")
                continue

        return {
            "success": True,
            "data": {
                "org_id": org_id,
                "period": period,
                "summary": {
                    "total_members": len(members),
                    "total_used": total_used,
                    "total_limit": total_limit if total_limit > 0 else "unlimited",
                    "total_remaining": total_limit - total_used if total_limit > 0 else "unlimited"
                },
                "members": sorted(member_usage, key=lambda x: x["used"], reverse=True)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching org usage for {org_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch organization usage")


@router.post("/reset")
async def reset_usage_quota(
    user_id: str = Query(..., description="User ID to reset quota for"),
    user: Dict = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Reset usage quota for a user (admin only).

    This is typically done automatically at the end of billing cycles,
    but admins can manually reset if needed.

    Args:
        user_id: Keycloak user ID to reset

    Returns:
        Success status
    """
    try:
        success = await usage_tracker.reset_quota(user_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset quota")

        # Get new stats to verify
        stats = await usage_tracker.get_usage_stats(user_id, period="current")

        return {
            "success": True,
            "message": f"Quota reset successfully for user {user_id}",
            "data": {
                "user_id": user_id,
                "used": stats["used"],
                "limit": stats["limit"],
                "reset_date": stats["reset_date"],
                "reset_by": user.get("email")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting quota for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset quota")


@router.get("/stats/summary")
async def get_usage_summary(
    user: Dict = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    """
    Get a comprehensive usage summary for the user.

    Includes:
    - Current period usage
    - Last 7 days breakdown
    - Top services used
    - Cost breakdown
    """
    user_id = user.get("user_id")

    try:
        # Get current stats
        current = await usage_tracker.get_usage_stats(user_id, period="current")

        # Get weekly history
        weekly = await usage_tracker.get_usage_stats(user_id, period="weekly")

        return {
            "success": True,
            "data": {
                "user": {
                    "user_id": user_id,
                    "email": user.get("email"),
                    "tier": current["tier"]
                },
                "current_period": {
                    "used": current["used"],
                    "limit": current["limit"],
                    "remaining": current["remaining"],
                    "percentage": round((current["used"] / current["limit"]) * 100, 2) if current["limit"] > 0 else 0,
                    "reset_date": current["reset_date"]
                },
                "daily_usage": {
                    "today": current["daily_usage"],
                    "limit": current["daily_limit"]
                },
                "last_7_days": weekly.get("history", []),
                "warnings": []
            }
        }

    except Exception as e:
        logger.error(f"Error fetching usage summary for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch usage summary")


@router.get("/health")
async def usage_tracking_health() -> Dict[str, Any]:
    """
    Health check for usage tracking system.

    Verifies:
    - Redis connection
    - PostgreSQL connection
    - System operational status
    """
    try:
        await usage_tracker.initialize()

        # Test Redis
        redis_ok = usage_tracker.redis is not None
        if redis_ok:
            try:
                await usage_tracker.redis.ping()
            except:
                redis_ok = False

        # Test PostgreSQL
        db_ok = usage_tracker.db_pool is not None
        if db_ok:
            try:
                async with usage_tracker.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            except:
                db_ok = False

        healthy = redis_ok and db_ok

        return {
            "success": True,
            "healthy": healthy,
            "components": {
                "redis": "ok" if redis_ok else "error",
                "postgresql": "ok" if db_ok else "error"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
