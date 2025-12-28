"""
Feature Flag API Endpoints

Provides REST API for feature flag management and evaluation.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from config.feature_flags import FeatureFlags, get_enabled_features
from utils.monitoring import LLMHubMonitor, FeatureFlagAnalytics
import logging

logger = logging.getLogger("feature_flag_api")

router = APIRouter(prefix="/api/v1/features", tags=["Feature Flags"])


class FeatureFlagEvaluation(BaseModel):
    """Response model for feature flag evaluation."""
    flag: str
    enabled: bool
    config: Dict[str, Any]
    reason: Optional[str] = None


class FeatureFlagUpdate(BaseModel):
    """Request model for updating feature flags."""
    enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = None
    whitelist_users: Optional[List[str]] = None
    blacklist_users: Optional[List[str]] = None


# Dependency to get user ID from request
async def get_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from request.

    Try multiple sources:
    1. Auth token/session
    2. Request headers
    3. Query parameters
    """
    # Try to get from auth session (implement based on your auth system)
    user = getattr(request.state, "user", None)
    if user:
        return getattr(user, "id", None) or getattr(user, "email", None)

    # Try from header
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return user_id

    # Try from query parameter
    user_id = request.query_params.get("user_id")
    if user_id:
        return user_id

    return None


@router.get("/{flag_name}", response_model=FeatureFlagEvaluation)
async def get_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Check if feature flag is enabled for current user.

    Args:
        flag_name: Name of the feature flag
        user_id: User identifier (from auth or query params)

    Returns:
        Feature flag evaluation result
    """
    try:
        enabled = FeatureFlags.is_enabled(flag_name, user_id)
        config = FeatureFlags.get_flag_status(flag_name)

        if not config:
            raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        # Determine reason for decision
        reason = "unknown"
        if not config.get("enabled"):
            reason = "globally_disabled"
        elif user_id and user_id in config.get("blacklist_users", []):
            reason = "blacklisted"
        elif user_id and user_id in config.get("whitelist_users", []):
            reason = "whitelisted"
        elif enabled and config.get("rollout_percentage", 0) >= 100:
            reason = "full_rollout"
        elif enabled:
            reason = f"rollout_{config.get('rollout_percentage', 0)}%"
        else:
            reason = "rollout_not_reached"

        # Log evaluation for analytics
        if user_id:
            FeatureFlagAnalytics.log_flag_evaluation(flag_name, user_id, enabled, reason)

        return FeatureFlagEvaluation(
            flag=flag_name,
            enabled=enabled,
            config=config,
            reason=reason
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating feature flag '{flag_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=Dict[str, Dict[str, Any]])
async def list_feature_flags(
    tags: Optional[str] = None
):
    """
    List all feature flags, optionally filtered by tags.

    Args:
        tags: Comma-separated list of tags to filter by

    Returns:
        Dictionary of all feature flags and their configurations
    """
    try:
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            flags = FeatureFlags.list_flags(tag_list)
        else:
            flags = FeatureFlags.list_flags()

        return flags

    except Exception as e:
        logger.error(f"Error listing feature flags: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/enabled", response_model=Dict[str, bool])
async def get_user_enabled_flags(user_id: str):
    """
    Get all feature flags enabled for a specific user.

    Args:
        user_id: User identifier

    Returns:
        Dictionary of flag_name -> enabled status
    """
    try:
        flags = FeatureFlags.get_user_flags(user_id)
        return flags

    except Exception as e:
        logger.error(f"Error getting flags for user '{user_id}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/features", response_model=List[str])
async def get_user_feature_names(user_id: str):
    """
    Get list of feature names enabled for a user.

    Args:
        user_id: User identifier

    Returns:
        List of enabled feature names
    """
    try:
        features = get_enabled_features(user_id)
        return features

    except Exception as e:
        logger.error(f"Error getting feature names for user '{user_id}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{flag_name}", response_model=Dict[str, Any])
async def update_feature_flag(
    flag_name: str,
    update: FeatureFlagUpdate,
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Update feature flag configuration.

    WARNING: Changes are in-memory only and will be lost on restart.
    For persistent changes, update environment variables.

    Args:
        flag_name: Name of the feature flag
        update: Fields to update
        user_id: User making the change (for audit log)

    Returns:
        Updated flag configuration
    """
    try:
        # Get old configuration for audit
        old_config = FeatureFlags.get_flag_status(flag_name).copy()

        if not old_config:
            raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        # Update flag
        update_dict = update.dict(exclude_unset=True)
        success = FeatureFlags.set_flag(flag_name, **update_dict)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update feature flag")

        # Get new configuration
        new_config = FeatureFlags.get_flag_status(flag_name)

        # Log change for audit
        changed_by = user_id or "system"
        FeatureFlagAnalytics.log_flag_change(flag_name, changed_by, old_config, new_config)

        logger.info(f"Feature flag '{flag_name}' updated by {changed_by}")

        return {
            "flag": flag_name,
            "old_config": old_config,
            "new_config": new_config,
            "changed_by": changed_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature flag '{flag_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{flag_name}/enable", response_model=Dict[str, Any])
async def enable_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Quick enable feature flag (set to 100% rollout).

    Args:
        flag_name: Name of the feature flag
        user_id: User making the change

    Returns:
        Updated flag configuration
    """
    try:
        old_config = FeatureFlags.get_flag_status(flag_name)

        if not old_config:
            raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        success = FeatureFlags.set_flag(
            flag_name,
            enabled=True,
            rollout_percentage=100
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to enable feature flag")

        new_config = FeatureFlags.get_flag_status(flag_name)

        changed_by = user_id or "system"
        FeatureFlagAnalytics.log_flag_change(flag_name, changed_by, old_config, new_config)

        logger.info(f"Feature flag '{flag_name}' enabled by {changed_by}")

        return {
            "flag": flag_name,
            "enabled": True,
            "config": new_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling feature flag '{flag_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{flag_name}/disable", response_model=Dict[str, Any])
async def disable_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Quick disable feature flag.

    Args:
        flag_name: Name of the feature flag
        user_id: User making the change

    Returns:
        Updated flag configuration
    """
    try:
        old_config = FeatureFlags.get_flag_status(flag_name)

        if not old_config:
            raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        success = FeatureFlags.set_flag(flag_name, enabled=False)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to disable feature flag")

        new_config = FeatureFlags.get_flag_status(flag_name)

        changed_by = user_id or "system"
        FeatureFlagAnalytics.log_flag_change(flag_name, changed_by, old_config, new_config)

        logger.info(f"Feature flag '{flag_name}' disabled by {changed_by}")

        return {
            "flag": flag_name,
            "enabled": False,
            "config": new_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling feature flag '{flag_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{flag_name}/rollout/{percentage}", response_model=Dict[str, Any])
async def set_rollout_percentage(
    flag_name: str,
    percentage: int,
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Set feature flag rollout percentage.

    Args:
        flag_name: Name of the feature flag
        percentage: Rollout percentage (0-100)
        user_id: User making the change

    Returns:
        Updated flag configuration
    """
    try:
        if not 0 <= percentage <= 100:
            raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")

        old_config = FeatureFlags.get_flag_status(flag_name)

        if not old_config:
            raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")

        success = FeatureFlags.set_flag(flag_name, rollout_percentage=percentage)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update rollout percentage")

        new_config = FeatureFlags.get_flag_status(flag_name)

        changed_by = user_id or "system"
        FeatureFlagAnalytics.log_flag_change(flag_name, changed_by, old_config, new_config)

        logger.info(f"Feature flag '{flag_name}' rollout set to {percentage}% by {changed_by}")

        return {
            "flag": flag_name,
            "rollout_percentage": percentage,
            "config": new_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting rollout for '{flag_name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
