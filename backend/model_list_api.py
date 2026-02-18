"""
Model List Management API - REST Endpoints

Provides admin and user endpoints for managing app-specific curated model lists.
Enables centralized control of which models appear in Bolt.diy, Presenton, Open-WebUI, etc.

Author: Backend Team
Date: November 19, 2025

Endpoints:
- Admin: /api/v1/admin/model-lists/* (CRUD for lists and models)
- User: /api/v1/user/model-preferences/* (favorites and hidden models)
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# Pydantic Models (Request/Response Schemas)
# =============================================================================

# List Models
class ModelListCreate(BaseModel):
    """Request to create a new model list"""
    name: str = Field(..., description="List name (e.g., 'Bolt.diy Default')")
    app_identifier: str = Field(..., description="App identifier (e.g., 'bolt-diy', 'presenton')")
    description: Optional[str] = Field(None, description="List description")
    slug: Optional[str] = Field(None, description="URL-safe slug (auto-generated if not provided)")
    is_default: bool = Field(False, description="Set as default list for this app")


class ModelListUpdate(BaseModel):
    """Request to update a model list"""
    name: Optional[str] = Field(None, description="New list name")
    description: Optional[str] = Field(None, description="New description")
    slug: Optional[str] = Field(None, description="New slug")
    is_default: Optional[bool] = Field(None, description="Set as default")
    is_active: Optional[bool] = Field(None, description="Set active status")


class ModelListResponse(BaseModel):
    """Model list response"""
    id: int
    name: str
    slug: str
    description: Optional[str]
    app_identifier: str
    is_default: bool
    is_active: bool
    model_count: int
    created_at: Optional[str]
    updated_at: Optional[str]


# Model Item Models
class ModelItemCreate(BaseModel):
    """Request to add a model to a list"""
    model_id: str = Field(..., description="LiteLLM model ID (e.g., 'openai/gpt-4')")
    display_name: Optional[str] = Field(None, description="Friendly display name")
    category: str = Field("general", description="Category (chat, coding, image, etc.)")
    sort_order: int = Field(0, description="Sort position")
    is_featured: bool = Field(False, description="Feature this model")
    tier_trial_access: bool = Field(False, description="Available to trial tier")
    tier_starter_access: bool = Field(True, description="Available to starter tier")
    tier_professional_access: bool = Field(True, description="Available to professional tier")
    tier_enterprise_access: bool = Field(True, description="Available to enterprise tier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ModelItemUpdate(BaseModel):
    """Request to update a model in a list"""
    display_name: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None
    tier_trial_access: Optional[bool] = None
    tier_starter_access: Optional[bool] = None
    tier_professional_access: Optional[bool] = None
    tier_enterprise_access: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelItemResponse(BaseModel):
    """Model item response"""
    id: int
    list_id: int
    model_id: str
    display_name: str
    category: str
    sort_order: int
    is_featured: bool
    tier_access: Dict[str, bool]
    is_active: bool
    metadata: Dict[str, Any]
    created_at: Optional[str]
    updated_at: Optional[str]


class ReorderItem(BaseModel):
    """Single item in reorder request"""
    model_id: int = Field(..., description="Model item ID (database ID)")
    sort_order: int = Field(..., description="New sort position")


class ReorderRequest(BaseModel):
    """Request to reorder models in a list"""
    items: List[ReorderItem] = Field(..., description="List of items with new sort orders")


# User Preference Models
class UserPreferenceUpdate(BaseModel):
    """Request to update user preference for a model"""
    is_favorite: Optional[bool] = Field(None, description="Set as favorite")
    is_hidden: Optional[bool] = Field(None, description="Hide this model")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Custom user settings")


class UserPreferenceResponse(BaseModel):
    """User preference response"""
    user_id: str
    model_id: str
    is_favorite: bool
    is_hidden: bool
    custom_settings: Dict[str, Any]
    created_at: Optional[str]
    updated_at: Optional[str]


class UserPreferencesResponse(BaseModel):
    """All user preferences response"""
    user_id: str
    favorites: List[Dict[str, Any]]
    hidden: List[Dict[str, Any]]
    custom_settings: Dict[str, Dict[str, Any]]


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def require_admin(request: Request):
    """Verify user is authenticated and has admin role (uses Redis session manager)"""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session data
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Check if user has admin role
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_current_user(request: Request):
    """Get current authenticated user from session"""
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session data
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Ensure user_id exists (map from Keycloak 'sub' field)
    if "user_id" not in user:
        user["user_id"] = user.get("sub") or user.get("id", "unknown")

    return user


# =============================================================================
# Routers
# =============================================================================

# Admin router for model list management
admin_router = APIRouter(
    prefix="/api/v1/admin/model-lists",
    tags=["Model List Management (Admin)"]
)

# User router for preferences
user_router = APIRouter(
    prefix="/api/v1/user/model-preferences",
    tags=["Model Preferences (User)"]
)


# =============================================================================
# Admin Endpoints - List Management
# =============================================================================

@admin_router.get(
    "",
    response_model=List[ModelListResponse],
    summary="List all model lists",
    description="Get all app model lists with optional filtering by app and active status"
)
async def list_model_lists(
    app_identifier: Optional[str] = Query(None, description="Filter by app (e.g., 'bolt-diy')"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    admin: dict = Depends(require_admin)
):
    """Get all model lists with model counts."""
    from model_list_manager import get_model_list_manager

    try:
        manager = get_model_list_manager()
        lists = await manager.get_lists(
            app_identifier=app_identifier,
            is_active=is_active
        )
        return lists
    except Exception as e:
        logger.error(f"Error listing model lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post(
    "",
    response_model=ModelListResponse,
    status_code=201,
    summary="Create model list",
    description="Create a new curated model list for an app"
)
async def create_model_list(
    request_body: ModelListCreate,
    admin: dict = Depends(require_admin)
):
    """Create a new model list."""
    from model_list_manager import get_model_list_manager

    try:
        manager = get_model_list_manager()
        result = await manager.create_list(
            name=request_body.name,
            app_identifier=request_body.app_identifier,
            description=request_body.description,
            slug=request_body.slug,
            is_default=request_body.is_default,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return result
    except Exception as e:
        logger.error(f"Error creating model list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get(
    "/{list_id}",
    response_model=ModelListResponse,
    summary="Get model list",
    description="Get details of a specific model list"
)
async def get_model_list(
    list_id: int,
    admin: dict = Depends(require_admin)
):
    """Get a specific model list by ID."""
    from model_list_manager import get_model_list_manager, ModelListNotFoundError

    try:
        manager = get_model_list_manager()
        result = await manager.get_list_by_id(list_id)
        return result
    except ModelListNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting model list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put(
    "/{list_id}",
    response_model=ModelListResponse,
    summary="Update model list",
    description="Update a model list's properties"
)
async def update_model_list(
    list_id: int,
    request_body: ModelListUpdate,
    admin: dict = Depends(require_admin)
):
    """Update a model list."""
    from model_list_manager import get_model_list_manager, ModelListNotFoundError

    try:
        manager = get_model_list_manager()
        result = await manager.update_list(
            list_id=list_id,
            name=request_body.name,
            description=request_body.description,
            slug=request_body.slug,
            is_default=request_body.is_default,
            is_active=request_body.is_active,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return result
    except ModelListNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating model list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete(
    "/{list_id}",
    summary="Delete model list",
    description="Soft delete a model list (sets is_active = FALSE)"
)
async def delete_model_list(
    list_id: int,
    admin: dict = Depends(require_admin)
):
    """Delete a model list (soft delete)."""
    from model_list_manager import get_model_list_manager, ModelListNotFoundError

    try:
        manager = get_model_list_manager()
        await manager.delete_list(
            list_id=list_id,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return {"message": f"Model list {list_id} deleted successfully"}
    except ModelListNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting model list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Admin Endpoints - Model Management within Lists
# =============================================================================

@admin_router.get(
    "/{list_id}/models",
    response_model=List[ModelItemResponse],
    summary="Get models in list",
    description="Get all models in a specific list with optional category filter"
)
async def get_list_models(
    list_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive models"),
    admin: dict = Depends(require_admin)
):
    """Get all models in a list."""
    from model_list_manager import get_model_list_manager

    try:
        manager = get_model_list_manager()
        models = await manager.get_list_models(
            list_id=list_id,
            category=category,
            include_inactive=include_inactive
        )
        return models
    except Exception as e:
        logger.error(f"Error getting list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post(
    "/{list_id}/models",
    response_model=ModelItemResponse,
    status_code=201,
    summary="Add model to list",
    description="Add a model to a curated list with tier access controls"
)
async def add_model_to_list(
    list_id: int,
    request_body: ModelItemCreate,
    admin: dict = Depends(require_admin)
):
    """Add a model to a list."""
    from model_list_manager import (
        get_model_list_manager,
        ModelListNotFoundError,
        DuplicateModelError
    )

    try:
        manager = get_model_list_manager()
        result = await manager.add_model_to_list(
            list_id=list_id,
            model_id=request_body.model_id,
            display_name=request_body.display_name,
            category=request_body.category,
            sort_order=request_body.sort_order,
            is_featured=request_body.is_featured,
            tier_trial_access=request_body.tier_trial_access,
            tier_starter_access=request_body.tier_starter_access,
            tier_professional_access=request_body.tier_professional_access,
            tier_enterprise_access=request_body.tier_enterprise_access,
            metadata=request_body.metadata,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return result
    except ModelListNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateModelError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding model to list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put(
    "/{list_id}/models/{model_id}",
    response_model=ModelItemResponse,
    summary="Update model in list",
    description="Update a model's configuration within a list"
)
async def update_model_in_list(
    list_id: int,
    model_id: int,
    request_body: ModelItemUpdate,
    admin: dict = Depends(require_admin)
):
    """Update a model in a list."""
    from model_list_manager import get_model_list_manager, ModelNotInListError

    try:
        manager = get_model_list_manager()
        result = await manager.update_model_in_list(
            list_id=list_id,
            model_id=model_id,
            display_name=request_body.display_name,
            category=request_body.category,
            sort_order=request_body.sort_order,
            is_featured=request_body.is_featured,
            tier_trial_access=request_body.tier_trial_access,
            tier_starter_access=request_body.tier_starter_access,
            tier_professional_access=request_body.tier_professional_access,
            tier_enterprise_access=request_body.tier_enterprise_access,
            is_active=request_body.is_active,
            metadata=request_body.metadata,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return result
    except ModelNotInListError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating model in list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete(
    "/{list_id}/models/{model_id}",
    summary="Remove model from list",
    description="Remove a model from a list (soft delete)"
)
async def remove_model_from_list(
    list_id: int,
    model_id: int,
    admin: dict = Depends(require_admin)
):
    """Remove a model from a list."""
    from model_list_manager import get_model_list_manager, ModelNotInListError

    try:
        manager = get_model_list_manager()
        await manager.remove_model_from_list(
            list_id=list_id,
            model_id=model_id,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return {"message": f"Model {model_id} removed from list {list_id}"}
    except ModelNotInListError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing model from list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put(
    "/{list_id}/reorder",
    summary="Reorder models",
    description="Bulk update sort order for models in a list"
)
async def reorder_models(
    list_id: int,
    request_body: ReorderRequest,
    admin: dict = Depends(require_admin)
):
    """Reorder models in a list."""
    from model_list_manager import get_model_list_manager, ModelListNotFoundError

    try:
        manager = get_model_list_manager()
        order_updates = [
            {"model_id": item.model_id, "sort_order": item.sort_order}
            for item in request_body.items
        ]
        await manager.reorder_models(
            list_id=list_id,
            order_updates=order_updates,
            admin_user_id=admin.get("user_id") or admin.get("sub")
        )
        return {"message": f"Reordered {len(order_updates)} models in list {list_id}"}
    except ModelListNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reordering models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# User Endpoints - Preferences
# =============================================================================

@user_router.get(
    "",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Get current user's model preferences (favorites and hidden)"
)
async def get_user_preferences(
    list_id: Optional[int] = Query(None, description="Filter by list"),
    user: dict = Depends(get_current_user)
):
    """Get user's model preferences."""
    from model_list_manager import get_model_list_manager

    try:
        manager = get_model_list_manager()
        user_id = user.get("user_id") or user.get("sub")
        preferences = await manager.get_user_preferences(
            user_id=user_id,
            list_id=list_id
        )
        return preferences
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@user_router.put(
    "/{model_id}",
    response_model=UserPreferenceResponse,
    summary="Update model preference",
    description="Set favorite/hidden status for a model"
)
async def update_user_preference(
    model_id: str,
    request_body: UserPreferenceUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user preference for a model."""
    from model_list_manager import get_model_list_manager

    try:
        manager = get_model_list_manager()
        user_id = user.get("user_id") or user.get("sub")
        result = await manager.update_user_preference(
            user_id=user_id,
            model_id=model_id,
            is_favorite=request_body.is_favorite,
            is_hidden=request_body.is_hidden,
            custom_settings=request_body.custom_settings
        )
        return result
    except Exception as e:
        logger.error(f"Error updating user preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Public Endpoint - Get Models for App
# =============================================================================

# This can be added to a separate public router if needed
public_router = APIRouter(
    prefix="/api/v1/model-lists",
    tags=["Model Lists (Public)"]
)


@public_router.get(
    "/{app_identifier}/default",
    response_model=List[ModelItemResponse],
    summary="Get default models for app",
    description="Get the default curated model list for an app (used by Bolt.diy, Presenton, etc.)"
)
async def get_default_models_for_app(
    app_identifier: str,
    user_tier: Optional[str] = Query("starter", description="User's subscription tier for filtering"),
    user: dict = Depends(get_current_user)
):
    """
    Get the default model list for an app, filtered by user's tier.

    This endpoint is called by apps like Bolt.diy and Presenton to get their
    curated model list based on the user's subscription tier.
    """
    from model_list_manager import get_model_list_manager
    import asyncpg

    try:
        manager = get_model_list_manager()

        # Get connection for custom query
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )

        try:
            # Find the default list for this app
            list_row = await conn.fetchrow(
                """
                SELECT id FROM app_model_lists
                WHERE app_identifier = $1 AND is_default = TRUE AND is_active = TRUE
                """,
                app_identifier
            )

            if not list_row:
                # Fall back to any active list for the app
                list_row = await conn.fetchrow(
                    """
                    SELECT id FROM app_model_lists
                    WHERE app_identifier = $1 AND is_active = TRUE
                    ORDER BY created_at
                    LIMIT 1
                    """,
                    app_identifier
                )

            if not list_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"No model list found for app '{app_identifier}'"
                )

            # Get models filtered by tier
            tier_column = f"tier_{user_tier}_access"
            valid_tiers = ["trial", "starter", "professional", "enterprise"]

            if user_tier not in valid_tiers:
                tier_column = "tier_starter_access"

            models = await conn.fetch(
                f"""
                SELECT
                    id, list_id, model_id, display_name, category, sort_order,
                    is_featured, tier_trial_access, tier_starter_access,
                    tier_professional_access, tier_enterprise_access,
                    is_active, metadata, created_at, updated_at
                FROM app_model_list_items
                WHERE list_id = $1 AND is_active = TRUE AND {tier_column} = TRUE
                ORDER BY sort_order, display_name
                """,
                list_row["id"]
            )

            return [
                {
                    "id": row["id"],
                    "list_id": row["list_id"],
                    "model_id": row["model_id"],
                    "display_name": row["display_name"],
                    "category": row["category"],
                    "sort_order": row["sort_order"],
                    "is_featured": row["is_featured"],
                    "tier_access": {
                        "trial": row["tier_trial_access"],
                        "starter": row["tier_starter_access"],
                        "professional": row["tier_professional_access"],
                        "enterprise": row["tier_enterprise_access"]
                    },
                    "is_active": row["is_active"],
                    "metadata": row["metadata"] if row["metadata"] else {},
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }
                for row in models
            ]
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default models for app: {e}")
        raise HTTPException(status_code=500, detail=str(e))
