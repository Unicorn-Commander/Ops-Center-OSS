"""
Model Admin API - Complete CRUD Operations for LLM Model Management

Provides admin endpoints for managing the model catalog with:
- Full CRUD operations for models
- Tier-based access control
- Pricing and markup management
- Provider management
- Filtering and search
- Audit logging
- Redis caching

Database: models table in unicorn_db
Authentication: Admin or moderator role required
Author: Backend API Team Lead
Date: November 8, 2025
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

import asyncpg
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator

from audit_logger import audit_logger
from audit_helpers import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models/admin", tags=["Model Administration"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ModelCreate(BaseModel):
    """Create new model request"""
    model_id: str = Field(..., description="Unique model identifier (e.g., gpt-4o)")
    provider: str = Field(..., description="Provider name (openai, anthropic, openrouter, etc.)")
    display_name: str = Field(..., description="User-friendly display name")
    description: Optional[str] = Field(None, description="Model description")

    # Access Control
    tier_access: List[str] = Field(
        default=["trial", "starter", "professional", "enterprise"],
        description="List of tiers that can access this model"
    )

    # Pricing (per 1K tokens)
    pricing: Dict[str, float] = Field(
        ...,
        description="Pricing per 1K tokens (input_per_1k, output_per_1k)"
    )
    tier_markup: Optional[Dict[str, float]] = Field(
        default={"trial": 2.0, "starter": 1.5, "professional": 1.2, "enterprise": 1.0},
        description="Pricing markup multiplier per tier"
    )

    # Capabilities
    context_length: Optional[int] = Field(None, description="Maximum context length")
    max_output_tokens: Optional[int] = Field(None, description="Maximum output tokens")
    supports_vision: bool = Field(default=False, description="Supports image input")
    supports_function_calling: bool = Field(default=False, description="Supports function calling")
    supports_streaming: bool = Field(default=True, description="Supports streaming responses")

    # Metadata
    model_family: Optional[str] = Field(None, description="Model family (gpt-4, claude-3, etc.)")
    release_date: Optional[str] = Field(None, description="Release date (YYYY-MM-DD)")
    metadata: Optional[Dict] = Field(default={}, description="Additional metadata")
    enabled: bool = Field(default=True, description="Model enabled/disabled")

    @validator('pricing')
    def validate_pricing(cls, v):
        """Ensure pricing has required fields and positive values"""
        required = ['input_per_1k', 'output_per_1k']
        for field in required:
            if field not in v:
                raise ValueError(f"Pricing must include '{field}'")
            if v[field] < 0:
                raise ValueError(f"Pricing values must be positive")
        return v

    @validator('tier_access')
    def validate_tier_access(cls, v):
        """Validate tier codes"""
        valid_tiers = {'trial', 'starter', 'professional', 'enterprise', 'vip_founder', 'byok', 'managed'}
        invalid = set(v) - valid_tiers
        if invalid:
            raise ValueError(f"Invalid tier codes: {invalid}")
        return v


class ModelUpdate(BaseModel):
    """Update existing model request"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    tier_access: Optional[List[str]] = None
    pricing: Optional[Dict[str, float]] = None
    tier_markup: Optional[Dict[str, float]] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_streaming: Optional[bool] = None
    model_family: Optional[str] = None
    release_date: Optional[str] = None
    enabled: Optional[bool] = None
    deprecated: Optional[bool] = None
    replacement_model: Optional[str] = None
    metadata: Optional[Dict] = None

    @validator('pricing')
    def validate_pricing(cls, v):
        """Ensure pricing has positive values"""
        if v is not None:
            for field, value in v.items():
                if value < 0:
                    raise ValueError(f"Pricing values must be positive")
        return v

    @validator('tier_access')
    def validate_tier_access(cls, v):
        """Validate tier codes"""
        if v is not None:
            valid_tiers = {'trial', 'starter', 'professional', 'enterprise', 'vip_founder', 'byok', 'managed'}
            invalid = set(v) - valid_tiers
            if invalid:
                raise ValueError(f"Invalid tier codes: {invalid}")
        return v


class ModelResponse(BaseModel):
    """Model response format"""
    id: str
    model_id: str
    provider: str
    display_name: str
    description: Optional[str] = None
    enabled: bool
    tier_access: List[str]
    pricing: Dict[str, float]
    tier_markup: Optional[Dict[str, float]] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: bool
    supports_function_calling: bool
    supports_streaming: bool
    model_family: Optional[str] = None
    release_date: Optional[str] = None
    deprecated: bool
    replacement_model: Optional[str] = None
    metadata: Dict
    created_at: str
    updated_at: str


class ModelListResponse(BaseModel):
    """Paginated model list response"""
    models: List[ModelResponse]
    total: int
    page: int
    limit: int
    filters_applied: Dict[str, Any]


# ============================================================================
# DEPENDENCIES
# ============================================================================

# These will be set by server.py during startup
_db_pool = None
_redis_client = None


def init_dependencies(db_pool: asyncpg.Pool, redis_client: aioredis.Redis):
    """Initialize module dependencies (called by server.py on startup)"""
    global _db_pool, _redis_client
    _db_pool = db_pool
    _redis_client = redis_client
    logger.info("Model Admin API dependencies initialized")


async def get_db_pool() -> asyncpg.Pool:
    """Get database pool"""
    if _db_pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db_pool


async def get_redis_client() -> aioredis.Redis:
    """Get Redis client"""
    if _redis_client is None:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return _redis_client


async def require_admin(request: Request):
    """Verify user is authenticated and has admin/moderator role"""
    import sys
    import os

    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Initialize session manager
    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Check admin or moderator role
    role = user.get("role", "")
    is_admin = user.get("is_admin", False)

    if not is_admin and role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admin or moderator access required")

    return user


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def invalidate_model_cache(redis: aioredis.Redis):
    """Invalidate model list cache"""
    try:
        await redis.delete("models:list:*")
        logger.info("Model cache invalidated")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")


async def get_cached_models(
    redis: aioredis.Redis,
    cache_key: str,
    ttl: int = 60
) -> Optional[List[Dict]]:
    """Get cached model list"""
    try:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache read failed: {e}")
    return None


async def set_cached_models(
    redis: aioredis.Redis,
    cache_key: str,
    data: List[Dict],
    ttl: int = 60
):
    """Cache model list"""
    try:
        await redis.setex(cache_key, ttl, json.dumps(data))
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


def format_model_response(row) -> Dict:
    """Format database row to model response"""
    return {
        "id": str(row['id']),
        "model_id": row['model_id'],
        "provider": row['provider'],
        "display_name": row['display_name'],
        "description": row['description'],
        "enabled": row['enabled'],
        "tier_access": row['tier_access'] if isinstance(row['tier_access'], list) else json.loads(row['tier_access'] or '[]'),
        "pricing": row['pricing'] if isinstance(row['pricing'], dict) else json.loads(row['pricing'] or '{}'),
        "tier_markup": row['tier_markup'] if isinstance(row['tier_markup'], dict) else json.loads(row['tier_markup'] or '{}'),
        "context_length": row['context_length'],
        "max_output_tokens": row['max_output_tokens'],
        "supports_vision": row['supports_vision'],
        "supports_function_calling": row['supports_function_calling'],
        "supports_streaming": row['supports_streaming'],
        "model_family": row['model_family'],
        "release_date": row['release_date'].isoformat() if row['release_date'] else None,
        "deprecated": row['deprecated'],
        "replacement_model": row['replacement_model'],
        "metadata": row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'] or '{}'),
        "created_at": row['created_at'].isoformat(),
        "updated_at": row['updated_at'].isoformat()
    }


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.get("/models", response_model=ModelListResponse)
async def list_models(
    request: Request,
    provider: Optional[str] = Query(None, description="Filter by provider"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    tier: Optional[str] = Query(None, description="Filter by tier access"),
    search: Optional[str] = Query(None, description="Search model_id or display_name"),
    deprecated: Optional[bool] = Query(False, description="Include deprecated models"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """
    List all models with filtering and pagination

    Requires: Admin or moderator role

    Features:
    - Filter by provider, enabled status, tier
    - Search by model_id or display_name
    - Pagination support
    - Redis caching (60s TTL)
    """
    try:
        # Build cache key
        filters = {
            "provider": provider,
            "enabled": enabled,
            "tier": tier,
            "search": search,
            "deprecated": deprecated,
            "page": page,
            "limit": limit
        }
        cache_key = f"models:list:{json.dumps(filters, sort_keys=True)}"

        # Check cache
        cached = await get_cached_models(redis, cache_key)
        if cached:
            logger.info("Returning cached model list")
            return cached

        # Build query
        conditions = []
        params = []
        param_idx = 1

        if not deprecated:
            conditions.append("deprecated = false")

        if provider:
            conditions.append(f"provider = ${param_idx}")
            params.append(provider)
            param_idx += 1

        if enabled is not None:
            conditions.append(f"enabled = ${param_idx}")
            params.append(enabled)
            param_idx += 1

        if tier:
            conditions.append(f"tier_access @> ${param_idx}::jsonb")
            params.append(json.dumps([tier]))
            param_idx += 1

        if search:
            conditions.append(f"(model_id ILIKE ${param_idx} OR display_name ILIKE ${param_idx})")
            params.append(f"%{search}%")
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Count total
        count_query = f"SELECT COUNT(*) FROM models {where_clause}"
        async with db_pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)

            # Fetch paginated results
            offset = (page - 1) * limit
            query = f"""
                SELECT * FROM models
                {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit} OFFSET {offset}
            """

            rows = await conn.fetch(query, *params)

        # Format response
        models = [format_model_response(row) for row in rows]

        response = {
            "models": models,
            "total": total,
            "page": page,
            "limit": limit,
            "filters_applied": {k: v for k, v in filters.items() if v is not None and k not in ['page', 'limit']}
        }

        # Cache response
        await set_cached_models(redis, cache_key, response)

        # Audit log
        await audit_logger.log(
            action="list_models",
            user_id=user.get("id"),
            resource_type="model",
            details={
                "filters": filters,
                "total_results": total,
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request)
            },
            status="success"
        )

        return response

    except Exception as e:
        logger.error(f"Error listing models: {e}")

        await audit_logger.log(
            action="list_models",
            user_id=user.get("id"),
            resource_type="model",
            details={"error": str(e)},
            status="error"
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(
    request: Request,
    model: ModelCreate,
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """
    Create new model

    Requires: Admin or moderator role

    Validation:
    - Unique model_id
    - Valid tier codes
    - Positive pricing
    - Valid provider
    """
    try:
        model_uuid = str(uuid.uuid4())

        async with db_pool.acquire() as conn:
            # Check if model_id already exists
            existing = await conn.fetchval(
                "SELECT id FROM models WHERE model_id = $1",
                model.model_id
            )

            if existing:
                raise HTTPException(status_code=400, detail=f"Model '{model.model_id}' already exists")

            # Insert model
            query = """
                INSERT INTO models (
                    id, model_id, provider, display_name, description, enabled,
                    tier_access, pricing, tier_markup,
                    context_length, max_output_tokens,
                    supports_vision, supports_function_calling, supports_streaming,
                    model_family, release_date, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
                )
                RETURNING *
            """

            row = await conn.fetchrow(
                query,
                model_uuid,
                model.model_id,
                model.provider,
                model.display_name,
                model.description,
                model.enabled,
                json.dumps(model.tier_access),
                json.dumps(model.pricing),
                json.dumps(model.tier_markup),
                model.context_length,
                model.max_output_tokens,
                model.supports_vision,
                model.supports_function_calling,
                model.supports_streaming,
                model.model_family,
                model.release_date,
                json.dumps(model.metadata)
            )

        # Invalidate cache
        await invalidate_model_cache(redis)

        # Audit log
        await audit_logger.log(
            action="create_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model.model_id,
            details={
                "model_id": model.model_id,
                "provider": model.provider,
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request)
            },
            status="success"
        )

        return format_model_response(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating model: {e}")

        await audit_logger.log(
            action="create_model",
            user_id=user.get("id"),
            resource_type="model",
            details={"model_id": model.model_id, "error": str(e)},
            status="error"
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    request: Request,
    model_id: str,
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get model details by model_id

    Requires: Admin or moderator role
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM models WHERE model_id = $1",
                model_id
            )

        if not row:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        # Audit log
        await audit_logger.log(
            action="get_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={"ip": get_client_ip(request)},
            status="success"
        )

        return format_model_response(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    request: Request,
    model_id: str,
    updates: ModelUpdate,
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """
    Update existing model

    Requires: Admin or moderator role

    Updates only provided fields (partial update)
    """
    try:
        # Build update query dynamically
        update_fields = []
        params = [model_id]
        param_idx = 2

        update_data = updates.dict(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = ${param_idx}")

                # Convert lists/dicts to JSON
                if isinstance(value, (list, dict)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)

                param_idx += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Always update updated_at
        update_fields.append("updated_at = NOW()")

        query = f"""
            UPDATE models
            SET {', '.join(update_fields)}
            WHERE model_id = $1
            RETURNING *
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        # Invalidate cache
        await invalidate_model_cache(redis)

        # Audit log
        await audit_logger.log(
            action="update_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={
                "updated_fields": list(update_data.keys()),
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request)
            },
            status="success"
        )

        return format_model_response(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model: {e}")

        await audit_logger.log(
            action="update_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={"error": str(e)},
            status="error"
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{model_id}")
async def delete_model(
    request: Request,
    model_id: str,
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """
    Delete model

    Requires: Admin or moderator role

    Note: This permanently deletes the model from the database
    """
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM models WHERE model_id = $1",
                model_id
            )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        # Invalidate cache
        await invalidate_model_cache(redis)

        # Audit log
        await audit_logger.log(
            action="delete_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request)
            },
            status="success"
        )

        return {"message": f"Model '{model_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}")

        await audit_logger.log(
            action="delete_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={"error": str(e)},
            status="error"
        )

        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/models/{model_id}/toggle")
async def toggle_model(
    request: Request,
    model_id: str,
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    """
    Enable/disable model (toggle)

    Requires: Admin or moderator role

    Convenience endpoint to quickly toggle model availability
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE models
                SET enabled = NOT enabled, updated_at = NOW()
                WHERE model_id = $1
                RETURNING model_id, enabled
                """,
                model_id
            )

        if not row:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        # Invalidate cache
        await invalidate_model_cache(redis)

        # Audit log
        await audit_logger.log(
            action="toggle_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={
                "new_status": "enabled" if row['enabled'] else "disabled",
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request)
            },
            status="success"
        )

        return {
            "model_id": row['model_id'],
            "enabled": row['enabled'],
            "message": f"Model {'enabled' if row['enabled'] else 'disabled'} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling model: {e}")

        await audit_logger.log(
            action="toggle_model",
            user_id=user.get("id"),
            resource_type="model",
            resource_id=model_id,
            details={"error": str(e)},
            status="error"
        )

        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS & STATS
# ============================================================================

@router.get("/models/stats/summary")
async def get_model_stats(
    user: Dict = Depends(require_admin),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get model catalog statistics

    Requires: Admin or moderator role

    Returns:
    - Total models
    - Enabled/disabled counts
    - Provider distribution
    - Tier coverage
    """
    try:
        async with db_pool.acquire() as conn:
            # Total counts
            total = await conn.fetchval("SELECT COUNT(*) FROM models")
            enabled = await conn.fetchval("SELECT COUNT(*) FROM models WHERE enabled = true")
            deprecated = await conn.fetchval("SELECT COUNT(*) FROM models WHERE deprecated = true")

            # Provider distribution
            providers = await conn.fetch(
                "SELECT provider, COUNT(*) as count FROM models GROUP BY provider ORDER BY count DESC"
            )

            # Tier coverage
            tier_counts = {}
            for tier in ['trial', 'starter', 'professional', 'enterprise', 'vip_founder', 'byok', 'managed']:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM models WHERE tier_access @> $1::jsonb",
                    json.dumps([tier])
                )
                tier_counts[tier] = count

        return {
            "total_models": total,
            "enabled_models": enabled,
            "disabled_models": total - enabled,
            "deprecated_models": deprecated,
            "provider_distribution": {row['provider']: row['count'] for row in providers},
            "tier_coverage": tier_counts
        }

    except Exception as e:
        logger.error(f"Error getting model stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
