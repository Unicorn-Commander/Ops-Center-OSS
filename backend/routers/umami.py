"""
Umami Analytics API Router

Provides integration with Umami analytics for viewing website stats,
visitors, pageviews, and other analytics data.
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/umami", tags=["umami"])

# Umami configuration
UMAMI_URL = os.getenv("UMAMI_URL", "http://unicorn-umami:3000")
UMAMI_USERNAME = os.getenv("UMAMI_USERNAME", "admin")
UMAMI_PASSWORD = os.getenv("UMAMI_PASSWORD", "umami")

# Cache for auth token
_auth_cache = {
    "token": None,
    "expires": None
}


class UmamiWebsite(BaseModel):
    id: str
    name: str
    domain: str
    createdAt: Optional[str] = None


class UmamiStats(BaseModel):
    pageviews: int = 0
    visitors: int = 0
    visits: int = 0
    bounces: int = 0
    totaltime: int = 0


class WebsiteWithStats(BaseModel):
    id: str
    name: str
    domain: str
    stats: Optional[UmamiStats] = None
    status: str = "unknown"


async def get_umami_token() -> str:
    """Get or refresh Umami auth token"""
    global _auth_cache

    # Check if we have a valid cached token
    if _auth_cache["token"] and _auth_cache["expires"]:
        if datetime.now() < _auth_cache["expires"]:
            return _auth_cache["token"]

    # Get new token
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{UMAMI_URL}/api/auth/login",
                json={
                    "username": UMAMI_USERNAME,
                    "password": UMAMI_PASSWORD
                }
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    _auth_cache["token"] = token
                    _auth_cache["expires"] = datetime.now() + timedelta(hours=1)
                    return token

            logger.error(f"Umami auth failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=401, detail="Failed to authenticate with Umami")

    except httpx.RequestError as e:
        logger.error(f"Umami connection error: {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to Umami")


@router.get("/health")
async def umami_health():
    """Check Umami service health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{UMAMI_URL}/api/heartbeat")
            if response.status_code == 200:
                return {"status": "healthy", "umami_url": UMAMI_URL}
            return {"status": "unhealthy", "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/websites")
async def get_websites():
    """Get all websites tracked in Umami"""
    try:
        token = await get_umami_token()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                # Umami API returns {"data": [...]} format
                websites = data.get("data", []) if isinstance(data, dict) else data
                return {"websites": websites, "count": len(websites)}

            logger.error(f"Failed to get websites: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch websites")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/{website_id}/stats")
async def get_website_stats(website_id: str, period: str = "24h"):
    """Get stats for a specific website"""
    try:
        token = await get_umami_token()

        # Calculate date range based on period
        end_date = datetime.now()
        if period == "24h":
            start_date = end_date - timedelta(hours=24)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(hours=24)

        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites/{website_id}/stats",
                params={"startAt": start_ts, "endAt": end_ts},
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return response.json()

            raise HTTPException(status_code=response.status_code, detail="Failed to fetch stats")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/{website_id}/pageviews")
async def get_website_pageviews(website_id: str, period: str = "7d"):
    """Get pageview data over time for a website"""
    try:
        token = await get_umami_token()

        end_date = datetime.now()
        if period == "24h":
            start_date = end_date - timedelta(hours=24)
            unit = "hour"
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
            unit = "day"
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
            unit = "day"
        else:
            start_date = end_date - timedelta(days=7)
            unit = "day"

        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites/{website_id}/pageviews",
                params={"startAt": start_ts, "endAt": end_ts, "unit": unit},
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return response.json()

            raise HTTPException(status_code=response.status_code, detail="Failed to fetch pageviews")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pageviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websites/{website_id}/metrics")
async def get_website_metrics(website_id: str, metric_type: str = "url", period: str = "7d"):
    """Get metrics breakdown (urls, referrers, browsers, etc)"""
    try:
        token = await get_umami_token()

        end_date = datetime.now()
        if period == "24h":
            start_date = end_date - timedelta(hours=24)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites/{website_id}/metrics",
                params={"startAt": start_ts, "endAt": end_ts, "type": metric_type},
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return response.json()

            raise HTTPException(status_code=response.status_code, detail="Failed to fetch metrics")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(period: str = "24h"):
    """Get aggregated dashboard data for all websites"""
    try:
        token = await get_umami_token()

        # Get all websites
        async with httpx.AsyncClient(timeout=10.0) as client:
            websites_response = await client.get(
                f"{UMAMI_URL}/api/websites",
                headers={"Authorization": f"Bearer {token}"}
            )

            if websites_response.status_code != 200:
                raise HTTPException(status_code=websites_response.status_code, detail="Failed to fetch websites")

            websites_data = websites_response.json()
            # Umami API returns {"data": [...]} format
            websites = websites_data.get("data", []) if isinstance(websites_data, dict) else websites_data

            # Calculate date range
            end_date = datetime.now()
            if period == "24h":
                start_date = end_date - timedelta(hours=24)
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(hours=24)

            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)

            # Get stats for each website
            websites_with_stats = []
            total_pageviews = 0
            total_visitors = 0
            total_visits = 0

            for website in websites:
                website_id = website.get("id")
                try:
                    stats_response = await client.get(
                        f"{UMAMI_URL}/api/websites/{website_id}/stats",
                        params={"startAt": start_ts, "endAt": end_ts},
                        headers={"Authorization": f"Bearer {token}"}
                    )

                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        website["stats"] = stats
                        total_pageviews += stats.get("pageviews", {}).get("value", 0)
                        total_visitors += stats.get("visitors", {}).get("value", 0)
                        total_visits += stats.get("visits", {}).get("value", 0)
                    else:
                        website["stats"] = None
                except Exception as e:
                    logger.warning(f"Failed to get stats for website {website_id}: {e}")
                    website["stats"] = None

                websites_with_stats.append(website)

            return {
                "websites": websites_with_stats,
                "totals": {
                    "pageviews": total_pageviews,
                    "visitors": total_visitors,
                    "visits": total_visits,
                    "websites_count": len(websites)
                },
                "period": period
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
