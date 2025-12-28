"""
Model List Management - Business Logic Layer

Provides business logic for managing app-specific curated model lists.
Supports CRUD operations for lists, models within lists, user preferences,
and comprehensive audit logging.

Author: Backend Team
Date: November 19, 2025

Classes:
- ModelListManager: Core business logic for model list management
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import asyncpg
import json

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# Exceptions
# =============================================================================

class ModelListError(Exception):
    """Base exception for model list operations"""
    pass

class ModelListNotFoundError(ModelListError):
    """Raised when a model list is not found"""
    pass

class ModelNotInListError(ModelListError):
    """Raised when a model is not found in a list"""
    pass

class DuplicateModelError(ModelListError):
    """Raised when attempting to add a duplicate model to a list"""
    pass


# =============================================================================
# Model List Manager
# =============================================================================

class ModelListManager:
    """
    Business logic for managing app-specific curated model lists.

    Handles:
    - List CRUD operations
    - Model management within lists
    - User preferences (favorites, hidden)
    - Audit logging for all changes
    """

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        """
        Initialize the manager.

        Args:
            pool: Optional connection pool. If not provided, connections will be created on demand.
        """
        self.pool = pool

    async def _get_connection(self):
        """Get a database connection."""
        if self.pool:
            return await self.pool.acquire()

        return await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "unicorn"),
            password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
            database=os.getenv("POSTGRES_DB", "unicorn_db")
        )

    async def _release_connection(self, conn):
        """Release a database connection."""
        if self.pool:
            await self.pool.release(conn)
        else:
            await conn.close()

    # =========================================================================
    # List Operations
    # =========================================================================

    async def get_lists(
        self,
        app_identifier: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all model lists with model counts.

        Args:
            app_identifier: Optional filter by app (e.g., 'bolt-diy', 'presenton')
            is_active: Optional filter by active status

        Returns:
            List of model lists with metadata
        """
        conn = await self._get_connection()
        try:
            query = """
                SELECT
                    l.id,
                    l.name,
                    l.slug,
                    l.description,
                    l.app_identifier,
                    l.is_default,
                    l.is_active,
                    l.created_at,
                    l.updated_at,
                    COUNT(m.id) as model_count
                FROM app_model_lists l
                LEFT JOIN app_model_list_items m ON l.id = m.list_id AND m.is_active = TRUE
                WHERE 1=1
            """
            params = []
            param_idx = 1

            if app_identifier:
                query += f" AND l.app_identifier = ${param_idx}"
                params.append(app_identifier)
                param_idx += 1

            if is_active is not None:
                query += f" AND l.is_active = ${param_idx}"
                params.append(is_active)
                param_idx += 1

            query += " GROUP BY l.id ORDER BY l.app_identifier, l.name"

            rows = await conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "description": row["description"],
                    "app_identifier": row["app_identifier"],
                    "is_default": row["is_default"],
                    "is_active": row["is_active"],
                    "model_count": row["model_count"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }
                for row in rows
            ]
        finally:
            await self._release_connection(conn)

    async def get_list_by_id(self, list_id: int) -> Dict[str, Any]:
        """
        Get a single model list by ID.

        Args:
            list_id: The list ID

        Returns:
            Model list details

        Raises:
            ModelListNotFoundError: If list not found
        """
        conn = await self._get_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT
                    l.id,
                    l.name,
                    l.slug,
                    l.description,
                    l.app_identifier,
                    l.is_default,
                    l.is_active,
                    l.created_at,
                    l.updated_at,
                    COUNT(m.id) as model_count
                FROM app_model_lists l
                LEFT JOIN app_model_list_items m ON l.id = m.list_id AND m.is_active = TRUE
                WHERE l.id = $1
                GROUP BY l.id
                """,
                list_id
            )

            if not row:
                raise ModelListNotFoundError(f"Model list {list_id} not found")

            return {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "description": row["description"],
                "app_identifier": row["app_identifier"],
                "is_default": row["is_default"],
                "is_active": row["is_active"],
                "model_count": row["model_count"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        finally:
            await self._release_connection(conn)

    async def create_list(
        self,
        name: str,
        app_identifier: str,
        description: Optional[str] = None,
        slug: Optional[str] = None,
        is_default: bool = False,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new model list.

        Args:
            name: List name
            app_identifier: App this list is for (e.g., 'bolt-diy')
            description: Optional description
            slug: Optional URL-safe slug (generated from name if not provided)
            is_default: Whether this is the default list for the app
            admin_user_id: Admin user creating the list (for audit)

        Returns:
            Created list details
        """
        conn = await self._get_connection()
        try:
            # Generate slug if not provided
            if not slug:
                slug = name.lower().replace(" ", "-").replace("_", "-")

            # If setting as default, unset other defaults for this app
            if is_default:
                await conn.execute(
                    """
                    UPDATE app_model_lists
                    SET is_default = FALSE, updated_at = NOW()
                    WHERE app_identifier = $1 AND is_default = TRUE
                    """,
                    app_identifier
                )

            # Create the list
            row = await conn.fetchrow(
                """
                INSERT INTO app_model_lists (name, slug, description, app_identifier, is_default, is_active)
                VALUES ($1, $2, $3, $4, $5, TRUE)
                RETURNING id, name, slug, description, app_identifier, is_default, is_active, created_at, updated_at
                """,
                name, slug, description, app_identifier, is_default
            )

            # Log audit
            await self.log_audit(
                action="create_list",
                list_id=row["id"],
                admin_user_id=admin_user_id,
                details={"name": name, "app_identifier": app_identifier},
                conn=conn
            )

            return {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "description": row["description"],
                "app_identifier": row["app_identifier"],
                "is_default": row["is_default"],
                "is_active": row["is_active"],
                "model_count": 0,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        finally:
            await self._release_connection(conn)

    async def update_list(
        self,
        list_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        slug: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a model list.

        Args:
            list_id: List ID to update
            name: Optional new name
            description: Optional new description
            slug: Optional new slug
            is_default: Optional set as default
            is_active: Optional set active status
            admin_user_id: Admin user making changes (for audit)

        Returns:
            Updated list details

        Raises:
            ModelListNotFoundError: If list not found
        """
        conn = await self._get_connection()
        try:
            # Get current list to verify it exists and get app_identifier
            current = await conn.fetchrow(
                "SELECT * FROM app_model_lists WHERE id = $1",
                list_id
            )

            if not current:
                raise ModelListNotFoundError(f"Model list {list_id} not found")

            # Build update query dynamically
            updates = []
            params = []
            param_idx = 1

            if name is not None:
                updates.append(f"name = ${param_idx}")
                params.append(name)
                param_idx += 1

            if description is not None:
                updates.append(f"description = ${param_idx}")
                params.append(description)
                param_idx += 1

            if slug is not None:
                updates.append(f"slug = ${param_idx}")
                params.append(slug)
                param_idx += 1

            if is_active is not None:
                updates.append(f"is_active = ${param_idx}")
                params.append(is_active)
                param_idx += 1

            # Handle is_default separately to unset others
            if is_default is not None:
                if is_default:
                    await conn.execute(
                        """
                        UPDATE app_model_lists
                        SET is_default = FALSE, updated_at = NOW()
                        WHERE app_identifier = $1 AND is_default = TRUE AND id != $2
                        """,
                        current["app_identifier"], list_id
                    )
                updates.append(f"is_default = ${param_idx}")
                params.append(is_default)
                param_idx += 1

            if not updates:
                # Nothing to update, return current
                return await self.get_list_by_id(list_id)

            # Add updated_at and list_id
            updates.append("updated_at = NOW()")
            params.append(list_id)

            query = f"""
                UPDATE app_model_lists
                SET {', '.join(updates)}
                WHERE id = ${param_idx}
                RETURNING id, name, slug, description, app_identifier, is_default, is_active, created_at, updated_at
            """

            row = await conn.fetchrow(query, *params)

            # Log audit
            await self.log_audit(
                action="update_list",
                list_id=list_id,
                admin_user_id=admin_user_id,
                details={"updates": {k: v for k, v in [("name", name), ("description", description), ("slug", slug), ("is_default", is_default), ("is_active", is_active)] if v is not None}},
                conn=conn
            )

            result = {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "description": row["description"],
                "app_identifier": row["app_identifier"],
                "is_default": row["is_default"],
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }

            # Get model count
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM app_model_list_items WHERE list_id = $1 AND is_active = TRUE",
                list_id
            )
            result["model_count"] = count

            return result
        finally:
            await self._release_connection(conn)

    async def delete_list(
        self,
        list_id: int,
        admin_user_id: Optional[str] = None
    ) -> bool:
        """
        Soft delete a model list (sets is_active = FALSE).

        Args:
            list_id: List ID to delete
            admin_user_id: Admin user deleting (for audit)

        Returns:
            True if deleted successfully

        Raises:
            ModelListNotFoundError: If list not found
        """
        conn = await self._get_connection()
        try:
            # Verify list exists
            exists = await conn.fetchval(
                "SELECT id FROM app_model_lists WHERE id = $1",
                list_id
            )

            if not exists:
                raise ModelListNotFoundError(f"Model list {list_id} not found")

            # Soft delete
            await conn.execute(
                """
                UPDATE app_model_lists
                SET is_active = FALSE, is_default = FALSE, updated_at = NOW()
                WHERE id = $1
                """,
                list_id
            )

            # Log audit
            await self.log_audit(
                action="delete_list",
                list_id=list_id,
                admin_user_id=admin_user_id,
                details={"soft_delete": True},
                conn=conn
            )

            return True
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Model Operations within Lists
    # =========================================================================

    async def get_list_models(
        self,
        list_id: int,
        category: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all models in a list.

        Args:
            list_id: The list ID
            category: Optional filter by category
            include_inactive: Whether to include inactive models

        Returns:
            List of models with their configuration
        """
        conn = await self._get_connection()
        try:
            query = """
                SELECT
                    id,
                    list_id,
                    model_id,
                    display_name,
                    category,
                    sort_order,
                    is_featured,
                    tier_trial_access,
                    tier_starter_access,
                    tier_professional_access,
                    tier_enterprise_access,
                    is_active,
                    metadata,
                    created_at,
                    updated_at
                FROM app_model_list_items
                WHERE list_id = $1
            """
            params = [list_id]
            param_idx = 2

            if not include_inactive:
                query += " AND is_active = TRUE"

            if category:
                query += f" AND category = ${param_idx}"
                params.append(category)
                param_idx += 1

            query += " ORDER BY sort_order, display_name"

            rows = await conn.fetch(query, *params)

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
                for row in rows
            ]
        finally:
            await self._release_connection(conn)

    async def add_model_to_list(
        self,
        list_id: int,
        model_id: str,
        display_name: Optional[str] = None,
        category: str = "general",
        sort_order: int = 0,
        is_featured: bool = False,
        tier_trial_access: bool = False,
        tier_starter_access: bool = True,
        tier_professional_access: bool = True,
        tier_enterprise_access: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a model to a list.

        Args:
            list_id: Target list ID
            model_id: LiteLLM model ID (e.g., 'openai/gpt-4')
            display_name: Optional friendly display name
            category: Model category (e.g., 'chat', 'coding', 'image')
            sort_order: Sort position in the list
            is_featured: Whether to feature this model
            tier_*_access: Access control by tier
            metadata: Additional metadata
            admin_user_id: Admin user adding (for audit)

        Returns:
            Created model item details

        Raises:
            ModelListNotFoundError: If list not found
            DuplicateModelError: If model already in list
        """
        conn = await self._get_connection()
        try:
            # Verify list exists
            list_exists = await conn.fetchval(
                "SELECT id FROM app_model_lists WHERE id = $1",
                list_id
            )

            if not list_exists:
                raise ModelListNotFoundError(f"Model list {list_id} not found")

            # Check for duplicates
            duplicate = await conn.fetchval(
                "SELECT id FROM app_model_list_items WHERE list_id = $1 AND model_id = $2",
                list_id, model_id
            )

            if duplicate:
                raise DuplicateModelError(f"Model {model_id} already exists in list {list_id}")

            # Use model_id as display_name if not provided
            if not display_name:
                display_name = model_id.split("/")[-1] if "/" in model_id else model_id

            # Insert the model
            row = await conn.fetchrow(
                """
                INSERT INTO app_model_list_items (
                    list_id, model_id, display_name, category, sort_order, is_featured,
                    tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
                    is_active, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE, $11)
                RETURNING *
                """,
                list_id, model_id, display_name, category, sort_order, is_featured,
                tier_trial_access, tier_starter_access, tier_professional_access, tier_enterprise_access,
                json.dumps(metadata) if metadata else None
            )

            # Log audit
            await self.log_audit(
                action="add_model",
                list_id=list_id,
                model_id=model_id,
                admin_user_id=admin_user_id,
                details={"display_name": display_name, "category": category},
                conn=conn
            )

            return {
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
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        finally:
            await self._release_connection(conn)

    async def update_model_in_list(
        self,
        list_id: int,
        model_id: int,
        display_name: Optional[str] = None,
        category: Optional[str] = None,
        sort_order: Optional[int] = None,
        is_featured: Optional[bool] = None,
        tier_trial_access: Optional[bool] = None,
        tier_starter_access: Optional[bool] = None,
        tier_professional_access: Optional[bool] = None,
        tier_enterprise_access: Optional[bool] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a model in a list.

        Args:
            list_id: The list ID
            model_id: The model item ID (database ID, not model_id string)
            [other args]: Fields to update
            admin_user_id: Admin user updating (for audit)

        Returns:
            Updated model item details

        Raises:
            ModelNotInListError: If model not found in list
        """
        conn = await self._get_connection()
        try:
            # Verify model exists in list
            exists = await conn.fetchval(
                "SELECT id FROM app_model_list_items WHERE id = $1 AND list_id = $2",
                model_id, list_id
            )

            if not exists:
                raise ModelNotInListError(f"Model {model_id} not found in list {list_id}")

            # Build update query dynamically
            updates = []
            params = []
            param_idx = 1

            field_mappings = [
                ("display_name", display_name),
                ("category", category),
                ("sort_order", sort_order),
                ("is_featured", is_featured),
                ("tier_trial_access", tier_trial_access),
                ("tier_starter_access", tier_starter_access),
                ("tier_professional_access", tier_professional_access),
                ("tier_enterprise_access", tier_enterprise_access),
                ("is_active", is_active),
            ]

            for field, value in field_mappings:
                if value is not None:
                    updates.append(f"{field} = ${param_idx}")
                    params.append(value)
                    param_idx += 1

            if metadata is not None:
                updates.append(f"metadata = ${param_idx}")
                params.append(json.dumps(metadata))
                param_idx += 1

            if not updates:
                # Nothing to update, return current
                row = await conn.fetchrow(
                    "SELECT * FROM app_model_list_items WHERE id = $1",
                    model_id
                )
            else:
                updates.append("updated_at = NOW()")
                params.extend([model_id, list_id])

                query = f"""
                    UPDATE app_model_list_items
                    SET {', '.join(updates)}
                    WHERE id = ${param_idx} AND list_id = ${param_idx + 1}
                    RETURNING *
                """

                row = await conn.fetchrow(query, *params)

            # Log audit
            await self.log_audit(
                action="update_model",
                list_id=list_id,
                model_id=row["model_id"],
                admin_user_id=admin_user_id,
                details={"item_id": model_id},
                conn=conn
            )

            return {
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
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        finally:
            await self._release_connection(conn)

    async def remove_model_from_list(
        self,
        list_id: int,
        model_id: int,
        admin_user_id: Optional[str] = None
    ) -> bool:
        """
        Remove a model from a list (soft delete).

        Args:
            list_id: The list ID
            model_id: The model item ID (database ID)
            admin_user_id: Admin user removing (for audit)

        Returns:
            True if removed successfully

        Raises:
            ModelNotInListError: If model not found in list
        """
        conn = await self._get_connection()
        try:
            # Get model info for audit before removing
            model_row = await conn.fetchrow(
                "SELECT model_id FROM app_model_list_items WHERE id = $1 AND list_id = $2",
                model_id, list_id
            )

            if not model_row:
                raise ModelNotInListError(f"Model {model_id} not found in list {list_id}")

            # Soft delete
            await conn.execute(
                """
                UPDATE app_model_list_items
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1 AND list_id = $2
                """,
                model_id, list_id
            )

            # Log audit
            await self.log_audit(
                action="remove_model",
                list_id=list_id,
                model_id=model_row["model_id"],
                admin_user_id=admin_user_id,
                details={"item_id": model_id, "soft_delete": True},
                conn=conn
            )

            return True
        finally:
            await self._release_connection(conn)

    async def reorder_models(
        self,
        list_id: int,
        order_updates: List[Dict[str, int]],
        admin_user_id: Optional[str] = None
    ) -> bool:
        """
        Bulk update sort order for models in a list.

        Args:
            list_id: The list ID
            order_updates: List of {"model_id": int, "sort_order": int}
            admin_user_id: Admin user reordering (for audit)

        Returns:
            True if reordered successfully
        """
        conn = await self._get_connection()
        try:
            # Verify list exists
            list_exists = await conn.fetchval(
                "SELECT id FROM app_model_lists WHERE id = $1",
                list_id
            )

            if not list_exists:
                raise ModelListNotFoundError(f"Model list {list_id} not found")

            # Update each model's sort order
            for update in order_updates:
                await conn.execute(
                    """
                    UPDATE app_model_list_items
                    SET sort_order = $1, updated_at = NOW()
                    WHERE id = $2 AND list_id = $3
                    """,
                    update["sort_order"], update["model_id"], list_id
                )

            # Log audit
            await self.log_audit(
                action="reorder_models",
                list_id=list_id,
                admin_user_id=admin_user_id,
                details={"updates_count": len(order_updates)},
                conn=conn
            )

            return True
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # User Preferences
    # =========================================================================

    async def get_user_preferences(
        self,
        user_id: str,
        list_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get user's model preferences (favorites and hidden).

        Args:
            user_id: Keycloak user ID
            list_id: Optional filter by list

        Returns:
            User preferences grouped by category
        """
        conn = await self._get_connection()
        try:
            query = """
                SELECT
                    p.id,
                    p.user_id,
                    p.model_id,
                    p.is_favorite,
                    p.is_hidden,
                    p.custom_settings,
                    p.created_at,
                    p.updated_at,
                    m.list_id,
                    m.display_name
                FROM user_model_preferences p
                JOIN app_model_list_items m ON p.model_id = m.model_id
                WHERE p.user_id = $1
            """
            params = [user_id]

            if list_id:
                query += " AND m.list_id = $2"
                params.append(list_id)

            rows = await conn.fetch(query, *params)

            favorites = []
            hidden = []
            custom_settings = {}

            for row in rows:
                pref = {
                    "model_id": row["model_id"],
                    "display_name": row["display_name"],
                    "list_id": row["list_id"],
                    "custom_settings": row["custom_settings"] if row["custom_settings"] else {}
                }

                if row["is_favorite"]:
                    favorites.append(pref)
                if row["is_hidden"]:
                    hidden.append(pref)
                if row["custom_settings"]:
                    custom_settings[row["model_id"]] = row["custom_settings"]

            return {
                "user_id": user_id,
                "favorites": favorites,
                "hidden": hidden,
                "custom_settings": custom_settings
            }
        finally:
            await self._release_connection(conn)

    async def update_user_preference(
        self,
        user_id: str,
        model_id: str,
        is_favorite: Optional[bool] = None,
        is_hidden: Optional[bool] = None,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update user's preference for a specific model.

        Args:
            user_id: Keycloak user ID
            model_id: Model ID string (e.g., 'openai/gpt-4')
            is_favorite: Set as favorite
            is_hidden: Set as hidden
            custom_settings: Custom user settings for this model

        Returns:
            Updated preference
        """
        conn = await self._get_connection()
        try:
            # Check if preference exists
            existing = await conn.fetchrow(
                "SELECT * FROM user_model_preferences WHERE user_id = $1 AND model_id = $2",
                user_id, model_id
            )

            if existing:
                # Update existing
                updates = []
                params = []
                param_idx = 1

                if is_favorite is not None:
                    updates.append(f"is_favorite = ${param_idx}")
                    params.append(is_favorite)
                    param_idx += 1

                if is_hidden is not None:
                    updates.append(f"is_hidden = ${param_idx}")
                    params.append(is_hidden)
                    param_idx += 1

                if custom_settings is not None:
                    updates.append(f"custom_settings = ${param_idx}")
                    params.append(json.dumps(custom_settings))
                    param_idx += 1

                if updates:
                    updates.append("updated_at = NOW()")
                    params.extend([user_id, model_id])

                    query = f"""
                        UPDATE user_model_preferences
                        SET {', '.join(updates)}
                        WHERE user_id = ${param_idx} AND model_id = ${param_idx + 1}
                        RETURNING *
                    """

                    row = await conn.fetchrow(query, *params)
                else:
                    row = existing
            else:
                # Insert new
                row = await conn.fetchrow(
                    """
                    INSERT INTO user_model_preferences (user_id, model_id, is_favorite, is_hidden, custom_settings)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                    """,
                    user_id, model_id,
                    is_favorite if is_favorite is not None else False,
                    is_hidden if is_hidden is not None else False,
                    json.dumps(custom_settings) if custom_settings else None
                )

            return {
                "user_id": row["user_id"],
                "model_id": row["model_id"],
                "is_favorite": row["is_favorite"],
                "is_hidden": row["is_hidden"],
                "custom_settings": json.loads(row["custom_settings"]) if row["custom_settings"] else {},
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        finally:
            await self._release_connection(conn)

    # =========================================================================
    # Audit Logging
    # =========================================================================

    async def log_audit(
        self,
        action: str,
        list_id: Optional[int] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        admin_user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        conn: Optional[asyncpg.Connection] = None
    ):
        """
        Write an audit log entry.

        Args:
            action: Action performed (create_list, update_list, add_model, etc.)
            list_id: Related list ID
            model_id: Related model ID
            user_id: User affected (for preference changes)
            admin_user_id: Admin who made the change
            details: Additional details
            conn: Optional existing connection
        """
        close_conn = False
        if not conn:
            conn = await self._get_connection()
            close_conn = True

        try:
            await conn.execute(
                """
                INSERT INTO model_access_audit (
                    action, list_id, model_id, user_id, admin_user_id, details, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                action, list_id, model_id, user_id, admin_user_id,
                json.dumps(details) if details else None
            )
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")
        finally:
            if close_conn:
                await self._release_connection(conn)


# =============================================================================
# Singleton Instance
# =============================================================================

_manager_instance: Optional[ModelListManager] = None

def get_model_list_manager() -> ModelListManager:
    """Get the singleton ModelListManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModelListManager()
    return _manager_instance


async def init_model_list_manager(pool: asyncpg.Pool) -> ModelListManager:
    """Initialize the ModelListManager with a connection pool."""
    global _manager_instance
    _manager_instance = ModelListManager(pool)
    return _manager_instance
