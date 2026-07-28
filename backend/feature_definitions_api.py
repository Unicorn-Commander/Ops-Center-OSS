"""
Feature Definitions API
Management endpoints for feature definitions and toggles.
"""

import os
from typing import List, Optional
from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

# Router configuration
router = APIRouter(prefix="/api/v1/admin/features", tags=["admin", "features"])


# =============================================================================
# Authentication
# =============================================================================

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
    # Session stores role as singular string (not plural list)
    role = user.get("role", "").lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return username


# =============================================================================
# Pydantic Models
# =============================================================================

class FeatureDefinitionCreate(BaseModel):
    """Schema for creating a new feature definition."""
    feature_key: str = Field(..., description="Unique identifier for the feature")
    feature_name: str = Field(..., description="Human-readable feature name")
    category: str = Field(..., description="Feature category (e.g., 'ui', 'api', 'integration')")
    description: Optional[str] = Field(None, description="Feature description")
    is_active: bool = Field(True, description="Whether the feature is active")
    sort_order: int = Field(0, description="Display order")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_key": "advanced_monitoring",
                "feature_name": "Advanced Monitoring",
                "category": "monitoring",
                "description": "Enable advanced GPU and system monitoring",
                "is_active": True,
                "sort_order": 10
            }
        }


class FeatureDefinitionUpdate(BaseModel):
    """Schema for updating an existing feature definition."""
    feature_key: Optional[str] = Field(None, description="Unique identifier for the feature")
    feature_name: Optional[str] = Field(None, description="Human-readable feature name")
    category: Optional[str] = Field(None, description="Feature category")
    description: Optional[str] = Field(None, description="Feature description")
    is_active: Optional[bool] = Field(None, description="Whether the feature is active")
    sort_order: Optional[int] = Field(None, description="Display order")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_name": "Updated Feature Name",
                "is_active": False
            }
        }


class FeatureDefinitionResponse(BaseModel):
    """Schema for feature definition responses."""
    id: int
    feature_key: str
    feature_name: str
    category: str
    description: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "feature_key": "advanced_monitoring",
                "feature_name": "Advanced Monitoring",
                "category": "monitoring",
                "description": "Enable advanced GPU and system monitoring",
                "is_active": True,
                "sort_order": 10,
                "created_at": "2025-10-30T12:00:00Z",
                "updated_at": "2025-10-30T12:00:00Z"
            }
        }


class FeatureReorderItem(BaseModel):
    """Single item in reorder request."""
    id: int = Field(..., description="Feature ID")
    sort_order: int = Field(..., description="New sort order")


class FeatureReorderRequest(BaseModel):
    """Schema for bulk reordering features."""
    items: List[FeatureReorderItem] = Field(..., description="List of features to reorder")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": 1, "sort_order": 0},
                    {"id": 2, "sort_order": 1},
                    {"id": 3, "sort_order": 2}
                ]
            }
        }


# =============================================================================
# Database Connection
# =============================================================================

async def get_db_connection():
    """Create database connection."""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db")
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/", response_model=List[FeatureDefinitionResponse])
async def list_features(
    category: Optional[str] = None,
    active_only: bool = True,
    admin: str = Depends(get_current_admin)
):
    """
    List all feature definitions.

    - **category**: Filter by category (optional)
    - **active_only**: Only return active features (default: true)
    """
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM feature_definitions WHERE 1=1"
        params = []
        param_count = 1

        if active_only:
            query += " AND is_active = TRUE"

        if category:
            query += f" AND category = ${param_count}"
            params.append(category)
            param_count += 1

        query += " ORDER BY sort_order ASC, feature_name ASC"

        if params:
            rows = await conn.fetch(query, *params)
        else:
            rows = await conn.fetch(query)

        return [dict(row) for row in rows]

    finally:
        await conn.close()


@router.get("/{feature_id}", response_model=FeatureDefinitionResponse)
async def get_feature(
    feature_id: int,
    admin: str = Depends(get_current_admin)
):
    """
    Get a single feature definition by ID.
    """
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM feature_definitions WHERE id = $1"
        row = await conn.fetchrow(query, feature_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature with ID {feature_id} not found"
            )

        return dict(row)

    finally:
        await conn.close()


@router.post("/", response_model=FeatureDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    feature: FeatureDefinitionCreate,
    admin: str = Depends(get_current_admin)
):
    """
    Create a new feature definition.

    Returns the created feature with generated ID and timestamps.
    """
    conn = await get_db_connection()
    try:
        # Check if feature_key already exists
        check_query = "SELECT id FROM feature_definitions WHERE feature_key = $1"
        existing = await conn.fetchrow(check_query, feature.feature_key)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feature with key '{feature.feature_key}' already exists"
            )

        # Insert new feature
        insert_query = """
            INSERT INTO feature_definitions
            (feature_key, feature_name, category, description, is_active, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING *
        """

        row = await conn.fetchrow(
            insert_query,
            feature.feature_key,
            feature.feature_name,
            feature.category,
            feature.description,
            feature.is_active,
            feature.sort_order
        )

        return dict(row)

    finally:
        await conn.close()


@router.put("/{feature_id}", response_model=FeatureDefinitionResponse)
async def update_feature(
    feature_id: int,
    feature: FeatureDefinitionUpdate,
    admin: str = Depends(get_current_admin)
):
    """
    Update an existing feature definition.

    Only provided fields will be updated. Returns the updated feature.
    """
    conn = await get_db_connection()
    try:
        # Check if feature exists
        check_query = "SELECT * FROM feature_definitions WHERE id = $1"
        existing = await conn.fetchrow(check_query, feature_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature with ID {feature_id} not found"
            )

        # Check for duplicate feature_key if updating it
        if feature.feature_key and feature.feature_key != existing['feature_key']:
            dup_check = "SELECT id FROM feature_definitions WHERE feature_key = $1 AND id != $2"
            duplicate = await conn.fetchrow(dup_check, feature.feature_key, feature_id)

            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Feature with key '{feature.feature_key}' already exists"
                )

        # Build dynamic update query
        update_fields = []
        params = []
        param_count = 1

        if feature.feature_key is not None:
            update_fields.append(f"feature_key = ${param_count}")
            params.append(feature.feature_key)
            param_count += 1

        if feature.feature_name is not None:
            update_fields.append(f"feature_name = ${param_count}")
            params.append(feature.feature_name)
            param_count += 1

        if feature.category is not None:
            update_fields.append(f"category = ${param_count}")
            params.append(feature.category)
            param_count += 1

        if feature.description is not None:
            update_fields.append(f"description = ${param_count}")
            params.append(feature.description)
            param_count += 1

        if feature.is_active is not None:
            update_fields.append(f"is_active = ${param_count}")
            params.append(feature.is_active)
            param_count += 1

        if feature.sort_order is not None:
            update_fields.append(f"sort_order = ${param_count}")
            params.append(feature.sort_order)
            param_count += 1

        if not update_fields:
            # No fields to update, return existing
            return dict(existing)

        # Always update updated_at
        update_fields.append("updated_at = NOW()")

        # Add feature_id as last parameter
        params.append(feature_id)

        update_query = f"""
            UPDATE feature_definitions
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """

        row = await conn.fetchrow(update_query, *params)
        return dict(row)

    finally:
        await conn.close()


@router.delete("/{feature_id}", status_code=status.HTTP_200_OK)
async def delete_feature(
    feature_id: int,
    hard_delete: bool = False,
    admin: str = Depends(get_current_admin)
):
    """
    Delete a feature definition.

    By default, performs a soft delete (sets is_active = false).
    Use hard_delete=true to permanently remove the feature.

    Returns a success message.
    """
    conn = await get_db_connection()
    try:
        # Check if feature exists
        check_query = "SELECT id FROM feature_definitions WHERE id = $1"
        existing = await conn.fetchrow(check_query, feature_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature with ID {feature_id} not found"
            )

        if hard_delete:
            # Permanently delete
            delete_query = "DELETE FROM feature_definitions WHERE id = $1"
            await conn.execute(delete_query, feature_id)
            message = f"Feature {feature_id} permanently deleted"
        else:
            # Soft delete - set is_active = false
            update_query = """
                UPDATE feature_definitions
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1
            """
            await conn.execute(update_query, feature_id)
            message = f"Feature {feature_id} deactivated"

        return {
            "success": True,
            "message": message,
            "feature_id": feature_id
        }

    finally:
        await conn.close()


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_features(
    reorder: FeatureReorderRequest,
    admin: str = Depends(get_current_admin)
):
    """
    Bulk update sort_order for multiple features.

    Used for drag-and-drop reordering in the UI.
    Returns the count of updated features.
    """
    conn = await get_db_connection()
    try:
        updated_count = 0

        # Update each feature's sort_order
        for item in reorder.items:
            query = """
                UPDATE feature_definitions
                SET sort_order = $1, updated_at = NOW()
                WHERE id = $2
            """
            result = await conn.execute(query, item.sort_order, item.id)

            # Check if row was actually updated
            if result.split()[-1] != '0':
                updated_count += 1

        return {
            "success": True,
            "message": f"Updated sort order for {updated_count} features",
            "updated_count": updated_count,
            "total_requested": len(reorder.items)
        }

    finally:
        await conn.close()


@router.get("/categories/list", response_model=List[str])
async def list_categories(
    admin: str = Depends(get_current_admin)
):
    """
    Get list of all unique feature categories.

    Useful for populating category filter dropdowns.
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT DISTINCT category
            FROM feature_definitions
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """
        rows = await conn.fetch(query)
        return [row['category'] for row in rows]

    finally:
        await conn.close()
