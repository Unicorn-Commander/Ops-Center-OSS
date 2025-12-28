"""
Brigade Proxy API - Ops-Center Integration
Epic: H23 - Brigade Usage & History Endpoints

This module provides proxy endpoints to Brigade API for:
- User usage statistics
- Task execution history

Author: Backend API Developer Agent
Date: October 25, 2025
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/brigade", tags=["Brigade Integration (H23)"])

# Brigade API configuration (use internal Docker network)
BRIGADE_API_URL = "http://unicorn-brigade:8112"
BRIGADE_TIMEOUT = 30.0  # seconds
BRIGADE_API_ENDPOINTS = {
    "usage": "/api/agents/usage",
    "tasks_history": "/api/tasks/history",
    "agents_list": "/api/agents",
    "task_detail": "/api/tasks/{task_id}"
}


# ==================== Health & Status ====================

@router.get("/health")
async def health_check():
    """Health check for Brigade proxy API"""
    return {
        "status": "healthy",
        "service": "brigade-proxy-api",
        "version": "1.0.0",
        "brigade_url": BRIGADE_API_URL
    }


@router.get("/status")
async def get_brigade_status():
    """Get Brigade service status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BRIGADE_API_URL}/health")

            if response.status_code == 200:
                return {
                    "status": "operational",
                    "brigade_api": "reachable",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "degraded",
                    "brigade_api": "unhealthy",
                    "status_code": response.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }

    except Exception as e:
        logger.error(f"Failed to check Brigade status: {e}")
        return {
            "status": "unavailable",
            "brigade_api": "unreachable",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ==================== Usage Statistics (H23) ====================

@router.get("/usage")
async def get_brigade_usage(
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID to filter usage")
):
    """
    Get Brigade usage statistics for current user (H23)

    Proxies to: https://api.brigade.your-domain.com/api/agents/usage

    Query Parameters:
        user_id: Optional user ID to filter (defaults to current authenticated user)

    Returns:
        Usage statistics including:
        - Agent count
        - Task count
        - Compute hours
        - API calls
        - Cost metrics
    """
    try:
        # Prepare headers for Brigade API
        headers = {
            "Content-Type": "application/json"
        }

        # Forward authorization header if provided
        if authorization:
            headers["Authorization"] = authorization

        # Build query parameters
        params = {}
        if user_id:
            params["user_id"] = user_id

        # Make request to Brigade API
        async with httpx.AsyncClient(timeout=BRIGADE_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{BRIGADE_API_URL}{BRIGADE_API_ENDPOINTS['usage']}",
                    headers=headers,
                    params=params
                )

                # Handle Brigade API response
                if response.status_code == 200:
                    usage_data = response.json()

                    # Add metadata
                    usage_data["metadata"] = {
                        "retrieved_at": datetime.utcnow().isoformat(),
                        "source": "brigade-api",
                        "cached": False
                    }

                    return usage_data

                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Unauthorized - Brigade API authentication failed"
                    )

                elif response.status_code == 404:
                    # User has no usage data yet
                    return {
                        "user_id": user_id,
                        "agent_count": 0,
                        "task_count": 0,
                        "compute_hours": 0,
                        "api_calls": 0,
                        "total_cost": 0,
                        "metadata": {
                            "retrieved_at": datetime.utcnow().isoformat(),
                            "source": "brigade-api",
                            "cached": False,
                            "note": "No usage data found - user may not have used Brigade yet"
                        }
                    }

                else:
                    logger.error(f"Brigade API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Brigade API error: {response.text}"
                    )

            except httpx.TimeoutException:
                logger.error("Brigade API request timed out")
                raise HTTPException(
                    status_code=504,
                    detail="Brigade API request timed out"
                )

            except httpx.RequestError as e:
                logger.error(f"Brigade API request failed: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to Brigade API: {str(e)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Brigade usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Task History (H23) ====================

@router.get("/tasks/history")
async def get_tasks_history(
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID to filter tasks"),
    status: Optional[str] = Query(None, description="Task status filter (completed, failed, running, pending)"),
    agent_id: Optional[str] = Query(None, description="Agent ID filter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get task execution history from Brigade (H23)

    Proxies to: https://api.brigade.your-domain.com/api/tasks/history

    Query Parameters:
        user_id: Filter by user ID
        status: Filter by task status (completed, failed, running, pending)
        agent_id: Filter by agent ID
        limit: Max tasks to return (1-500, default 50)
        offset: Pagination offset (default 0)

    Returns:
        List of tasks with execution metadata:
        - task_id, agent_id, status
        - created_at, started_at, completed_at
        - duration, input, output
        - error messages (if failed)
    """
    try:
        # Prepare headers for Brigade API
        headers = {
            "Content-Type": "application/json"
        }

        # Forward authorization header if provided
        if authorization:
            headers["Authorization"] = authorization

        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset
        }

        if user_id:
            params["user_id"] = user_id
        if status:
            params["status"] = status
        if agent_id:
            params["agent_id"] = agent_id

        # Make request to Brigade API
        async with httpx.AsyncClient(timeout=BRIGADE_TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{BRIGADE_API_URL}{BRIGADE_API_ENDPOINTS['tasks_history']}",
                    headers=headers,
                    params=params
                )

                # Handle Brigade API response
                if response.status_code == 200:
                    history_data = response.json()

                    # Add metadata
                    if isinstance(history_data, dict):
                        history_data["metadata"] = {
                            "retrieved_at": datetime.utcnow().isoformat(),
                            "source": "brigade-api",
                            "cached": False,
                            "pagination": {
                                "limit": limit,
                                "offset": offset
                            }
                        }

                    return history_data

                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Unauthorized - Brigade API authentication failed"
                    )

                elif response.status_code == 404:
                    # No tasks found
                    return {
                        "tasks": [],
                        "total": 0,
                        "metadata": {
                            "retrieved_at": datetime.utcnow().isoformat(),
                            "source": "brigade-api",
                            "cached": False,
                            "pagination": {
                                "limit": limit,
                                "offset": offset
                            },
                            "note": "No task history found"
                        }
                    }

                else:
                    logger.error(f"Brigade API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Brigade API error: {response.text}"
                    )

            except httpx.TimeoutException:
                logger.error("Brigade API request timed out")
                raise HTTPException(
                    status_code=504,
                    detail="Brigade API request timed out"
                )

            except httpx.RequestError as e:
                logger.error(f"Brigade API request failed: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to Brigade API: {str(e)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Additional Helper Endpoints ====================

@router.get("/agents")
async def list_brigade_agents(
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="Filter agents by user")
):
    """
    List available Brigade agents

    Proxies to Brigade API to get user's agents
    """
    try:
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = authorization

        params = {}
        if user_id:
            params["user_id"] = user_id

        async with httpx.AsyncClient(timeout=BRIGADE_TIMEOUT) as client:
            response = await client.get(
                f"{BRIGADE_API_URL}{BRIGADE_API_ENDPOINTS['agents_list']}",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Brigade API error: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed information about a specific task

    Args:
        task_id: Task ID to retrieve

    Returns:
        Detailed task information including full input/output
    """
    try:
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = authorization

        async with httpx.AsyncClient(timeout=BRIGADE_TIMEOUT) as client:
            response = await client.get(
                f"{BRIGADE_API_URL}/api/tasks/{task_id}",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task not found: {task_id}"
                )
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Brigade API error: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


logger.info("Brigade Proxy API (H23) initialized - Usage & Task History endpoints active")
