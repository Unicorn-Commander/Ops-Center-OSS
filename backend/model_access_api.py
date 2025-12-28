"""
Model Access Control API - Epic 3.3

Filters models based on user tier and BYOK providers, validates access before proxying to LiteLLM.

Author: Backend Developer
Date: November 6, 2025
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from litellm_credit_system import CreditSystem
from byok_manager import BYOKManager
from litellm_api import get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["Model Management"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ModelCreate(BaseModel):
    model_id: str
    provider: str
    display_name: str
    description: Optional[str] = None
    tier_access: List[str] = ["trial", "starter", "professional", "enterprise"]
    pricing: Dict[str, float]  # {"input_per_1k": 0.01, "output_per_1k": 0.03}
    tier_markup: Optional[Dict[str, float]] = {"trial": 2.0, "starter": 1.5, "professional": 1.2, "enterprise": 1.0}
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    model_family: Optional[str] = None
    metadata: Optional[Dict] = {}


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    tier_access: Optional[List[str]] = None
    pricing: Optional[Dict[str, float]] = None
    tier_markup: Optional[Dict[str, float]] = None
    enabled: Optional[bool] = None
    deprecated: Optional[bool] = None
    replacement_model: Optional[str] = None
    metadata: Optional[Dict] = None


# ============================================================================
# Dependencies (will be injected from server.py)
# ============================================================================

# These will be set by server.py during startup
_db_pool = None
_credit_system = None
_byok_manager = None


def init_dependencies(db_pool: asyncpg.Pool, credit_system: CreditSystem, byok_manager: BYOKManager):
    """Initialize module dependencies (called by server.py on startup)"""
    global _db_pool, _credit_system, _byok_manager
    _db_pool = db_pool
    _credit_system = credit_system
    _byok_manager = byok_manager
    logger.info("Model Access API dependencies initialized")


async def get_db_pool() -> asyncpg.Pool:
    """Get database pool"""
    if _db_pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db_pool


async def get_credit_system() -> CreditSystem:
    """Get credit system"""
    if _credit_system is None:
        raise HTTPException(status_code=500, detail="Credit system not initialized")
    return _credit_system


async def get_byok_manager() -> BYOKManager:
    """Get BYOK manager"""
    if _byok_manager is None:
        raise HTTPException(status_code=500, detail="BYOK manager not initialized")
    return _byok_manager


# ============================================================================
# Core Function: Get Available Models
# ============================================================================

async def get_available_models(
    user_id: str,
    credit_system: CreditSystem,
    byok_manager: BYOKManager,
    db_pool: asyncpg.Pool
) -> List[Dict]:
    """
    Get models available to user based on tier and BYOK

    Args:
        user_id: User identifier
        credit_system: Credit system instance
        byok_manager: BYOK manager instance
        db_pool: Database connection pool

    Returns:
        List of model dictionaries with enhanced pricing info
    """
    try:
        # Get user context
        user_tier = await credit_system.get_user_tier(user_id)
        user_keys = await byok_manager.get_all_user_keys(user_id)
        byok_providers = list(user_keys.keys())

        logger.info(f"Fetching models for user {user_id}, tier: {user_tier}, BYOK providers: {byok_providers}")

        # NEW: Query with JOIN instead of JSONB contains
        query = """
            SELECT
                m.model_id,
                m.provider,
                m.display_name,
                m.description,
                m.pricing,
                m.context_length,
                m.max_output_tokens,
                m.supports_vision,
                m.supports_function_calling,
                m.supports_streaming,
                m.model_family,
                m.metadata,
                tma.markup_multiplier,
                st.tier_code,
                st.tier_name
            FROM model_access_control m
            INNER JOIN tier_model_access tma ON m.id = tma.model_id
            INNER JOIN subscription_tiers st ON tma.tier_id = st.id
            WHERE st.tier_code = $1
              AND tma.enabled = TRUE
              AND m.enabled = TRUE
              AND m.deprecated = FALSE
            ORDER BY
                CASE m.provider
                    WHEN 'ollama' THEN 1  -- Local models first
                    WHEN 'openrouter' THEN 2
                    ELSE 3
                END,
                m.model_family,
                m.display_name
        """

        models = await db_pool.fetch(query, user_tier)

        # Enhance with cost calculations
        enhanced_models = []
        for model in models:
            # Parse pricing
            pricing = model['pricing'] if isinstance(model['pricing'], dict) else json.loads(model['pricing'])

            # Calculate actual cost
            if model['provider'] in byok_providers:
                # User has BYOK for this provider - FREE
                cost_input = 0
                cost_output = 0
                using_byok = True
            else:
                # Using platform credits - apply tier markup from JOIN
                markup = float(model['markup_multiplier'])
                cost_input = pricing.get('input_per_1k', 0) * markup
                cost_output = pricing.get('output_per_1k', 0) * markup
                using_byok = False

            enhanced_models.append({
                "id": model['model_id'],
                "object": "model",
                "provider": model['provider'],
                "display_name": model['display_name'],
                "description": model['description'],
                "pricing": {
                    "input_per_1k_tokens": cost_input,
                    "output_per_1k_tokens": cost_output,
                    "using_byok": using_byok,
                    "provider": model['provider'] if using_byok else "platform"
                },
                "context_length": model['context_length'],
                "max_output_tokens": model['max_output_tokens'],
                "capabilities": {
                    "vision": model['supports_vision'],
                    "function_calling": model['supports_function_calling'],
                    "streaming": model['supports_streaming']
                },
                "family": model['model_family'],
                "metadata": model['metadata'] if isinstance(model['metadata'], dict) else json.loads(model['metadata'] or '{}')
            })

        logger.info(f"Returning {len(enhanced_models)} models for user {user_id}")
        return enhanced_models

    except Exception as e:
        logger.error(f"Error fetching available models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch available models")


# ============================================================================
# Core Function: Validate Model Access
# ============================================================================

async def validate_model_access(
    model_id: str,
    user_id: str,
    credit_system: CreditSystem,
    byok_manager: BYOKManager,
    db_pool: asyncpg.Pool
) -> Dict:
    """
    Validate user can access this model

    Args:
        model_id: Model identifier to validate
        user_id: User identifier
        credit_system: Credit system instance
        byok_manager: BYOK manager instance
        db_pool: Database connection pool

    Returns:
        Model info if allowed

    Raises:
        HTTPException 403: If model not available for user's tier
    """
    try:
        # Get user tier
        user_tier = await credit_system.get_user_tier(user_id)

        # NEW: Query with JOIN to check access directly
        query = """
            SELECT
                m.id,
                m.model_id,
                m.provider,
                m.display_name,
                m.description,
                m.pricing,
                m.context_length,
                m.max_output_tokens,
                m.supports_vision,
                m.supports_function_calling,
                m.supports_streaming,
                m.model_family,
                m.metadata,
                tma.markup_multiplier,
                st.tier_code,
                st.tier_name
            FROM model_access_control m
            INNER JOIN tier_model_access tma ON m.id = tma.model_id
            INNER JOIN subscription_tiers st ON tma.tier_id = st.id
            WHERE m.model_id = $1
              AND st.tier_code = $2
              AND tma.enabled = TRUE
              AND m.enabled = TRUE
              AND m.deprecated = FALSE
        """

        model = await db_pool.fetchrow(query, model_id, user_tier)

        if not model:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Model '{model_id}' is not available for your subscription tier ({user_tier}). "
                    f"Upgrade to Professional or Enterprise to access advanced models, or add your own API key (BYOK)."
                )
            )

        # Convert to dict and add BYOK info
        model_dict = dict(model)
        user_keys = await byok_manager.get_all_user_keys(user_id)
        model_dict['has_byok'] = model_dict['provider'] in user_keys

        return model_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating model access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to validate model access")


# ============================================================================
# API Endpoints: User-Facing
# ============================================================================

@router.get("/available")
async def list_available_models(
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system),
    byok_manager: BYOKManager = Depends(get_byok_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get models available to authenticated user

    Returns models filtered by:
    - User's subscription tier
    - User's BYOK providers (marked as free)
    - Admin-configured access control
    """
    models = await get_available_models(user_id, credit_system, byok_manager, db_pool)

    return {
        "object": "list",
        "data": models,
        "summary": {
            "total": len(models),
            "byok_free": len([m for m in models if m['pricing']['using_byok']]),
            "paid": len([m for m in models if not m['pricing']['using_byok']])
        }
    }


@router.get("/categorized")
async def list_categorized_models(
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system),
    byok_manager: BYOKManager = Depends(get_byok_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get models organized by category (BYOK free vs Paid)
    """
    models = await get_available_models(user_id, credit_system, byok_manager, db_pool)

    byok_models = [m for m in models if m['pricing']['using_byok']]
    paid_models = [m for m in models if not m['pricing']['using_byok']]

    return {
        "byok_models": {
            "count": len(byok_models),
            "models": byok_models,
            "note": "These models are FREE - using your API keys"
        },
        "platform_models": {
            "count": len(paid_models),
            "models": paid_models,
            "note": "These models charge credits from your account"
        }
    }


# ============================================================================
# API Endpoints: Admin CRUD
# ============================================================================

@router.get("/admin/models")
async def list_all_models_admin(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List ALL models in the system (admin view - not filtered by tier)

    Returns all models from model_access_control table for admin management.
    """
    try:
        rows = await db_pool.fetch(
            """
            SELECT
                id,
                model_id,
                provider,
                display_name,
                description,
                tier_access,
                pricing,
                tier_markup,
                context_length,
                max_output_tokens,
                supports_vision,
                supports_function_calling,
                supports_streaming,
                model_family,
                enabled,
                deprecated,
                replacement_model,
                metadata,
                created_at,
                updated_at
            FROM model_access_control
            WHERE enabled = TRUE
            ORDER BY display_name ASC
            """
        )

        models = []
        for row in rows:
            models.append({
                "id": row["id"],
                "model_id": row["model_id"],
                "provider": row["provider"],
                "display_name": row["display_name"],
                "description": row["description"],
                "tier_access": json.loads(row["tier_access"]) if row["tier_access"] else [],
                "pricing": json.loads(row["pricing"]) if row["pricing"] else {},
                "tier_markup": json.loads(row["tier_markup"]) if row["tier_markup"] else {},
                "context_length": row["context_length"],
                "max_output_tokens": row["max_output_tokens"],
                "supports_vision": row["supports_vision"],
                "supports_function_calling": row["supports_function_calling"],
                "supports_streaming": row["supports_streaming"],
                "model_family": row["model_family"],
                "enabled": row["enabled"],
                "deprecated": row["deprecated"],
                "replacement_model": row["replacement_model"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"])
            })

        return {
            "models": models,
            "total": len(models)
        }

    except Exception as e:
        logger.error(f"Error listing all models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.post("/admin/models")
async def create_model(
    model: ModelCreate,
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new model entry (admin only)
    """
    # TODO: Add admin role check

    try:
        model_id = await db_pool.fetchval(
            """
            INSERT INTO model_access_control (
                model_id, provider, display_name, description,
                tier_access, pricing, tier_markup,
                context_length, max_output_tokens,
                supports_vision, supports_function_calling, supports_streaming,
                model_family, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
            """,
            model.model_id, model.provider, model.display_name, model.description,
            json.dumps(model.tier_access), json.dumps(model.pricing), json.dumps(model.tier_markup),
            model.context_length, model.max_output_tokens,
            model.supports_vision, model.supports_function_calling, model.supports_streaming,
            model.model_family, json.dumps(model.metadata)
        )

        logger.info(f"Created model {model.model_id} by admin {user_id}")

        return {
            "success": True,
            "model_id": str(model_id),
            "message": f"Model {model.model_id} created successfully"
        }

    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=f"Model {model.model_id} already exists")
    except Exception as e:
        logger.error(f"Error creating model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create model")


@router.put("/admin/models/{model_id}")
async def update_model(
    model_id: str,
    update: ModelUpdate,
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update model entry (admin only)
    """
    # TODO: Add admin role check

    try:
        # Build dynamic update query
        updates = []
        values = []
        param_num = 1

        if update.display_name is not None:
            updates.append(f"display_name = ${param_num}")
            values.append(update.display_name)
            param_num += 1

        if update.description is not None:
            updates.append(f"description = ${param_num}")
            values.append(update.description)
            param_num += 1

        if update.tier_access is not None:
            updates.append(f"tier_access = ${param_num}::jsonb")
            values.append(json.dumps(update.tier_access))
            param_num += 1

        if update.pricing is not None:
            updates.append(f"pricing = ${param_num}::jsonb")
            values.append(json.dumps(update.pricing))
            param_num += 1

        if update.tier_markup is not None:
            updates.append(f"tier_markup = ${param_num}::jsonb")
            values.append(json.dumps(update.tier_markup))
            param_num += 1

        if update.enabled is not None:
            updates.append(f"enabled = ${param_num}")
            values.append(update.enabled)
            param_num += 1

        if update.deprecated is not None:
            updates.append(f"deprecated = ${param_num}")
            values.append(update.deprecated)
            param_num += 1

        if update.replacement_model is not None:
            updates.append(f"replacement_model = ${param_num}")
            values.append(update.replacement_model)
            param_num += 1

        if update.metadata is not None:
            updates.append(f"metadata = ${param_num}::jsonb")
            values.append(json.dumps(update.metadata))
            param_num += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")

        values.append(model_id)
        query = f"""
            UPDATE model_access_control
            SET {', '.join(updates)}
            WHERE model_id = ${param_num}
            RETURNING id
        """

        result = await db_pool.fetchval(query, *values)

        if not result:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        logger.info(f"Updated model {model_id} by admin {user_id}")

        return {
            "success": True,
            "message": f"Model {model_id} updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update model")


@router.delete("/admin/models/{model_id}")
async def delete_model(
    model_id: str,
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Delete model entry (admin only)
    """
    # TODO: Add admin role check

    try:
        result = await db_pool.execute(
            """
            DELETE FROM model_access_control
            WHERE model_id = $1
            """,
            model_id
        )

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        logger.info(f"Deleted model {model_id} by admin {user_id}")

        return {
            "success": True,
            "message": f"Model {model_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete model")


@router.get("/admin/models/analytics")
async def get_model_analytics(
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get usage statistics for models (admin only)
    """
    # TODO: Add admin role check

    try:
        # Get model usage stats from credit_transactions
        stats = await db_pool.fetch(
            """
            SELECT
                model,
                COUNT(*) as usage_count,
                SUM(tokens_used) as total_tokens,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost_per_request
            FROM credit_transactions
            WHERE transaction_type = 'usage'
                AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY model
            ORDER BY usage_count DESC
            LIMIT 50
            """
        )

        # Get total models count
        total_models = await db_pool.fetchval(
            "SELECT COUNT(*) FROM model_access_control WHERE enabled = true"
        )

        # Get models by provider
        provider_counts = await db_pool.fetch(
            """
            SELECT provider, COUNT(*) as count
            FROM model_access_control
            WHERE enabled = true
            GROUP BY provider
            ORDER BY count DESC
            """
        )

        return {
            "summary": {
                "total_models": total_models,
                "providers": [{"provider": r['provider'], "count": r['count']} for r in provider_counts],
                "period": "last_30_days"
            },
            "usage": [
                {
                    "model": r['model'],
                    "usage_count": r['usage_count'],
                    "total_tokens": r['total_tokens'],
                    "total_cost": float(r['total_cost']),
                    "avg_cost_per_request": float(r['avg_cost_per_request'])
                }
                for r in stats
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching model analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


# ============================================================================
# API Endpoints: Tier-Model Management (NEW)
# ============================================================================

@router.post("/admin/tiers/{tier_code}/models")
async def assign_models_to_tier(
    tier_code: str,
    model_ids: List[str],
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Assign multiple models to a tier (bulk operation)

    Args:
        tier_code: Tier code (trial, starter, professional, enterprise)
        model_ids: List of model IDs to assign
        user_id: Admin user ID
        db_pool: Database connection pool

    Returns:
        Success response with count of assigned models
    """
    # TODO: Add admin role check

    try:
        # Get tier ID
        tier = await db_pool.fetchrow(
            "SELECT id FROM subscription_tiers WHERE tier_code = $1",
            tier_code
        )
        if not tier:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_code}' not found")

        # Get model records by model_id
        models = await db_pool.fetch(
            "SELECT id FROM model_access_control WHERE model_id = ANY($1::text[])",
            model_ids
        )

        if not models:
            raise HTTPException(status_code=404, detail="No valid models found")

        # Bulk insert with default markup multiplier
        values = [(tier['id'], m['id']) for m in models]

        inserted = 0
        for tier_id, model_id in values:
            result = await db_pool.execute(
                """
                INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier)
                VALUES ($1, $2, 1.2)
                ON CONFLICT (tier_id, model_id) DO UPDATE SET enabled = TRUE
                """,
                tier_id, model_id
            )
            inserted += 1

        logger.info(f"Assigned {inserted} models to tier {tier_code} by admin {user_id}")

        return {
            "success": True,
            "assigned": inserted,
            "tier_code": tier_code,
            "message": f"Successfully assigned {inserted} models to {tier_code} tier"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning models to tier: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to assign models to tier")


@router.delete("/admin/tiers/{tier_code}/models/{model_id}")
async def remove_model_from_tier(
    tier_code: str,
    model_id: str,
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Remove model from tier (or disable access)

    Args:
        tier_code: Tier code
        model_id: Model identifier
        user_id: Admin user ID
        db_pool: Database connection pool

    Returns:
        Success response
    """
    # TODO: Add admin role check

    try:
        result = await db_pool.execute(
            """
            UPDATE tier_model_access tma
            SET enabled = FALSE
            FROM subscription_tiers st, model_access_control m
            WHERE tma.tier_id = st.id
              AND tma.model_id = m.id
              AND st.tier_code = $1
              AND m.model_id = $2
            """,
            tier_code,
            model_id
        )

        logger.info(f"Removed model {model_id} from tier {tier_code} by admin {user_id}")

        return {
            "success": True,
            "message": f"Model {model_id} removed from {tier_code} tier"
        }

    except Exception as e:
        logger.error(f"Error removing model from tier: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove model from tier")


@router.put("/admin/models/{model_id}/tiers")
async def update_model_tier_access(
    model_id: str,
    tier_assignments: Dict[str, bool],
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update which tiers can access a model

    Args:
        model_id: Model identifier
        tier_assignments: Dict mapping tier_code -> enabled (e.g., {"trial": true, "starter": false})
        user_id: Admin user ID
        db_pool: Database connection pool

    Returns:
        Success response with updated tier count
    """
    # TODO: Add admin role check

    try:
        # Get model
        model = await db_pool.fetchrow(
            "SELECT id FROM model_access_control WHERE model_id = $1",
            model_id
        )
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Update tier assignments
        updated = 0
        for tier_code, enabled in tier_assignments.items():
            tier = await db_pool.fetchrow(
                "SELECT id FROM subscription_tiers WHERE tier_code = $1",
                tier_code
            )
            if not tier:
                logger.warning(f"Tier {tier_code} not found, skipping")
                continue

            await db_pool.execute(
                """
                INSERT INTO tier_model_access (tier_id, model_id, enabled, markup_multiplier)
                VALUES ($1, $2, $3, 1.2)
                ON CONFLICT (tier_id, model_id)
                DO UPDATE SET enabled = $3
                """,
                tier['id'], model['id'], enabled
            )
            updated += 1

        logger.info(f"Updated tier access for model {model_id} by admin {user_id}")

        return {
            "success": True,
            "updated": updated,
            "message": f"Updated tier access for model {model_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model tier access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update tier access")


@router.get("/admin/tiers/{tier_code}/models")
async def get_tier_models(
    tier_code: str,
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get all models available for a specific tier

    Args:
        tier_code: Tier code
        user_id: Admin user ID
        db_pool: Database connection pool

    Returns:
        List of models with tier-specific pricing
    """
    # TODO: Add admin role check

    try:
        query = """
            SELECT
                m.model_id,
                m.provider,
                m.display_name,
                m.description,
                m.pricing,
                tma.markup_multiplier,
                tma.enabled,
                m.context_length,
                m.supports_vision,
                m.supports_function_calling
            FROM model_access_control m
            INNER JOIN tier_model_access tma ON m.id = tma.model_id
            INNER JOIN subscription_tiers st ON tma.tier_id = st.id
            WHERE st.tier_code = $1
            ORDER BY m.provider, m.display_name
        """

        models = await db_pool.fetch(query, tier_code)

        return {
            "tier_code": tier_code,
            "total_models": len(models),
            "models": [
                {
                    "model_id": m['model_id'],
                    "provider": m['provider'],
                    "display_name": m['display_name'],
                    "description": m['description'],
                    "markup_multiplier": float(m['markup_multiplier']),
                    "enabled": m['enabled'],
                    "context_length": m['context_length'],
                    "supports_vision": m['supports_vision'],
                    "supports_function_calling": m['supports_function_calling']
                }
                for m in models
            ]
        }

    except Exception as e:
        logger.error(f"Error getting tier models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get tier models")


@router.put("/admin/tiers/{tier_code}/models/{model_id}/markup")
async def update_model_markup(
    tier_code: str,
    model_id: str,
    markup_multiplier: float = Query(..., ge=0.0, le=10.0),
    user_id: str = Depends(get_user_id),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update pricing markup multiplier for a model in a specific tier

    Args:
        tier_code: Tier code
        model_id: Model identifier
        markup_multiplier: Pricing multiplier (1.0 = base cost, 1.5 = 50% markup)
        user_id: Admin user ID
        db_pool: Database connection pool

    Returns:
        Success response with new markup
    """
    # TODO: Add admin role check

    try:
        result = await db_pool.execute(
            """
            UPDATE tier_model_access tma
            SET markup_multiplier = $3
            FROM subscription_tiers st, model_access_control m
            WHERE tma.tier_id = st.id
              AND tma.model_id = m.id
              AND st.tier_code = $1
              AND m.model_id = $2
            """,
            tier_code,
            model_id,
            markup_multiplier
        )

        logger.info(f"Updated markup for model {model_id} in tier {tier_code} to {markup_multiplier} by admin {user_id}")

        return {
            "success": True,
            "tier_code": tier_code,
            "model_id": model_id,
            "markup_multiplier": markup_multiplier,
            "message": f"Markup updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating model markup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update markup")
