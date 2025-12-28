"""
App Definitions API
Management endpoints for app definitions and toggles.
"""

import os
from typing import List, Optional
from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

# Router configuration
router = APIRouter(prefix="/api/v1/admin/apps", tags=["admin", "apps"])


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

class AppDefinitionCreate(BaseModel):
    """Schema for creating a new app definition."""
    app_key: str = Field(..., description="Unique identifier for the app")
    app_name: str = Field(..., description="Human-readable app name")
    category: str = Field(..., description="App category (e.g., 'ui', 'api', 'integration')")
    description: Optional[str] = Field(None, description="App description")
    is_active: bool = Field(True, description="Whether the app is active")
    sort_order: int = Field(0, description="Display order")

    class Config:
        json_schema_extra = {
            "example": {
                "app_key": "advanced_monitoring",
                "app_name": "Advanced Monitoring",
                "category": "monitoring",
                "description": "Enable advanced GPU and system monitoring",
                "is_active": True,
                "sort_order": 10
            }
        }


class AppDefinitionUpdate(BaseModel):
    """Schema for updating an existing app definition."""
    app_key: Optional[str] = Field(None, description="Unique identifier for the app")
    app_name: Optional[str] = Field(None, description="Human-readable app name")
    category: Optional[str] = Field(None, description="App category")
    description: Optional[str] = Field(None, description="App description")
    is_active: Optional[bool] = Field(None, description="Whether the app is active")
    sort_order: Optional[int] = Field(None, description="Display order")

    class Config:
        json_schema_extra = {
            "example": {
                "app_name": "Updated App Name",
                "is_active": False
            }
        }


class AppDefinitionResponse(BaseModel):
    """Schema for app definition responses."""
    id: int
    app_key: str
    app_name: str
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
                "app_key": "advanced_monitoring",
                "app_name": "Advanced Monitoring",
                "category": "monitoring",
                "description": "Enable advanced GPU and system monitoring",
                "is_active": True,
                "sort_order": 10,
                "created_at": "2025-10-30T12:00:00Z",
                "updated_at": "2025-10-30T12:00:00Z"
            }
        }


class AppReorderItem(BaseModel):
    """Single item in reorder request."""
    id: int = Field(..., description="App ID")
    sort_order: int = Field(..., description="New sort order")


class AppReorderRequest(BaseModel):
    """Schema for bulk reordering apps."""
    items: List[AppReorderItem] = Field(..., description="List of apps to reorder")

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

@router.get("/", response_model=List[AppDefinitionResponse])
async def list_apps(
    category: Optional[str] = None,
    active_only: bool = True,
    admin: str = Depends(get_current_admin)
):
    """
    List all app definitions.

    - **category**: Filter by category (optional)
    - **active_only**: Only return active apps (default: true)
    """
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM app_definitions WHERE 1=1"
        params = []
        param_count = 1

        if active_only:
            query += " AND is_active = TRUE"

        if category:
            query += f" AND category = ${param_count}"
            params.append(category)
            param_count += 1

        query += " ORDER BY sort_order ASC, app_name ASC"

        if params:
            rows = await conn.fetch(query, *params)
        else:
            rows = await conn.fetch(query)

        return [dict(row) for row in rows]

    finally:
        await conn.close()


@router.get("/{app_id}", response_model=AppDefinitionResponse)
async def get_app(
    app_id: int,
    admin: str = Depends(get_current_admin)
):
    """
    Get a single app definition by ID.
    """
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM app_definitions WHERE id = $1"
        row = await conn.fetchrow(query, app_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"App with ID {app_id} not found"
            )

        return dict(row)

    finally:
        await conn.close()


@router.post("/", response_model=AppDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    app: AppDefinitionCreate,
    admin: str = Depends(get_current_admin)
):
    """
    Create a new app definition.

    Returns the created app with generated ID and timestamps.
    """
    conn = await get_db_connection()
    try:
        # Check if app_key already exists
        check_query = "SELECT id FROM app_definitions WHERE app_key = $1"
        existing = await conn.fetchrow(check_query, app.app_key)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"App with key '{app.app_key}' already exists"
            )

        # Insert new app
        insert_query = """
            INSERT INTO app_definitions
            (app_key, app_name, category, description, is_active, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            RETURNING *
        """

        row = await conn.fetchrow(
            insert_query,
            app.app_key,
            app.app_name,
            app.category,
            app.description,
            app.is_active,
            app.sort_order
        )

        return dict(row)

    finally:
        await conn.close()


@router.put("/{app_id}", response_model=AppDefinitionResponse)
async def update_app(
    app_id: int,
    app: AppDefinitionUpdate,
    admin: str = Depends(get_current_admin)
):
    """
    Update an existing app definition.

    Only provided fields will be updated. Returns the updated app.
    """
    conn = await get_db_connection()
    try:
        # Check if app exists
        check_query = "SELECT * FROM app_definitions WHERE id = $1"
        existing = await conn.fetchrow(check_query, app_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"App with ID {app_id} not found"
            )

        # Check for duplicate app_key if updating it
        if app.app_key and app.app_key != existing['app_key']:
            dup_check = "SELECT id FROM app_definitions WHERE app_key = $1 AND id != $2"
            duplicate = await conn.fetchrow(dup_check, app.app_key, app_id)

            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"App with key '{app.app_key}' already exists"
                )

        # Build dynamic update query
        update_fields = []
        params = []
        param_count = 1

        if app.app_key is not None:
            update_fields.append(f"app_key = ${param_count}")
            params.append(app.app_key)
            param_count += 1

        if app.app_name is not None:
            update_fields.append(f"app_name = ${param_count}")
            params.append(app.app_name)
            param_count += 1

        if app.category is not None:
            update_fields.append(f"category = ${param_count}")
            params.append(app.category)
            param_count += 1

        if app.description is not None:
            update_fields.append(f"description = ${param_count}")
            params.append(app.description)
            param_count += 1

        if app.is_active is not None:
            update_fields.append(f"is_active = ${param_count}")
            params.append(app.is_active)
            param_count += 1

        if app.sort_order is not None:
            update_fields.append(f"sort_order = ${param_count}")
            params.append(app.sort_order)
            param_count += 1

        if not update_fields:
            # No fields to update, return existing
            return dict(existing)

        # Always update updated_at
        update_fields.append("updated_at = NOW()")

        # Add app_id as last parameter
        params.append(app_id)

        update_query = f"""
            UPDATE app_definitions
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """

        row = await conn.fetchrow(update_query, *params)
        return dict(row)

    finally:
        await conn.close()


@router.delete("/{app_id}", status_code=status.HTTP_200_OK)
async def delete_app(
    app_id: int,
    hard_delete: bool = False,
    admin: str = Depends(get_current_admin)
):
    """
    Delete an app definition.

    By default, performs a soft delete (sets is_active = false).
    Use hard_delete=true to permanently remove the app.

    Returns a success message.
    """
    conn = await get_db_connection()
    try:
        # Check if app exists
        check_query = "SELECT id FROM app_definitions WHERE id = $1"
        existing = await conn.fetchrow(check_query, app_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"App with ID {app_id} not found"
            )

        if hard_delete:
            # Permanently delete
            delete_query = "DELETE FROM app_definitions WHERE id = $1"
            await conn.execute(delete_query, app_id)
            message = f"App {app_id} permanently deleted"
        else:
            # Soft delete - set is_active = false
            update_query = """
                UPDATE app_definitions
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1
            """
            await conn.execute(update_query, app_id)
            message = f"App {app_id} deactivated"

        return {
            "success": True,
            "message": message,
            "app_id": app_id
        }

    finally:
        await conn.close()


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_apps(
    reorder: AppReorderRequest,
    admin: str = Depends(get_current_admin)
):
    """
    Bulk update sort_order for multiple apps.

    Used for drag-and-drop reordering in the UI.
    Returns the count of updated apps.
    """
    conn = await get_db_connection()
    try:
        updated_count = 0

        # Update each app's sort_order
        for item in reorder.items:
            query = """
                UPDATE app_definitions
                SET sort_order = $1, updated_at = NOW()
                WHERE id = $2
            """
            result = await conn.execute(query, item.sort_order, item.id)

            # Check if row was actually updated
            if result.split()[-1] != '0':
                updated_count += 1

        return {
            "success": True,
            "message": f"Updated sort order for {updated_count} apps",
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
    Get list of all unique app categories.

    Useful for populating category filter dropdowns.
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT DISTINCT category
            FROM app_definitions
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """
        rows = await conn.fetch(query)
        return [row['category'] for row in rows]

    finally:
        await conn.close()
