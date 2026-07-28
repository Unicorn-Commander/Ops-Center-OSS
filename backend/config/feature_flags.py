"""
Feature Flag System for Ops Center
Supports gradual rollout of new features with user-based targeting.
"""
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger("feature_flags")


class FeatureFlags:
    """
    Feature flags for gradual rollout of unified LLM Management.

    Features can be:
    - Globally enabled/disabled
    - Rolled out to percentage of users
    - Whitelisted for specific users
    - Blacklisted for specific users
    - Time-gated with start/end dates
    """

    FLAGS: Dict[str, Dict[str, Any]] = {
        "unified_llm_hub": {
            "enabled": os.getenv("FEATURE_UNIFIED_LLM_HUB", "false").lower() == "true",
            "rollout_percentage": int(os.getenv("FEATURE_LLM_HUB_ROLLOUT", "0")),
            "whitelist_users": [u.strip() for u in os.getenv("FEATURE_LLM_HUB_WHITELIST", "").split(",") if u.strip()],
            "blacklist_users": [u.strip() for u in os.getenv("FEATURE_LLM_HUB_BLACKLIST", "").split(",") if u.strip()],
            "start_date": os.getenv("FEATURE_LLM_HUB_START_DATE"),
            "end_date": os.getenv("FEATURE_LLM_HUB_END_DATE"),
            "description": "Unified LLM management interface (replaces 4 old pages)",
            "tags": ["llm", "ui", "admin"],
            "owner": "platform-team"
        },
        "advanced_analytics": {
            "enabled": os.getenv("FEATURE_ADVANCED_ANALYTICS", "false").lower() == "true",
            "rollout_percentage": int(os.getenv("FEATURE_ANALYTICS_ROLLOUT", "0")),
            "whitelist_users": [u.strip() for u in os.getenv("FEATURE_ANALYTICS_WHITELIST", "").split(",") if u.strip()],
            "blacklist_users": [],
            "start_date": None,
            "end_date": None,
            "description": "Enhanced analytics dashboard with ML insights",
            "tags": ["analytics", "ml", "admin"],
            "owner": "data-team"
        },
        "model_recommendations": {
            "enabled": os.getenv("FEATURE_MODEL_RECOMMENDATIONS", "false").lower() == "true",
            "rollout_percentage": int(os.getenv("FEATURE_MODEL_REC_ROLLOUT", "0")),
            "whitelist_users": [],
            "blacklist_users": [],
            "start_date": None,
            "end_date": None,
            "description": "AI-powered model recommendations based on usage",
            "tags": ["llm", "ml", "recommendations"],
            "owner": "ml-team"
        }
    }

    @classmethod
    def is_enabled(cls, flag_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if feature is enabled for user.

        Decision hierarchy:
        1. If flag doesn't exist -> False
        2. If globally disabled -> False
        3. If user in blacklist -> False
        4. If user in whitelist -> True
        5. If date-gated and outside range -> False
        6. If rollout percentage and user hash matches -> True
        7. If rollout 100% -> True

        Args:
            flag_name: Name of the feature flag
            user_id: User identifier (email, keycloak_id, etc.)

        Returns:
            True if feature is enabled for this user, False otherwise
        """
        if flag_name not in cls.FLAGS:
            logger.warning(f"Feature flag '{flag_name}' not found")
            return False

        flag = cls.FLAGS[flag_name]

        # Check if feature globally disabled
        if not flag["enabled"]:
            logger.debug(f"Feature '{flag_name}' globally disabled")
            return False

        # Check blacklist
        if user_id and user_id in flag["blacklist_users"]:
            logger.debug(f"User '{user_id}' blacklisted for '{flag_name}'")
            return False

        # Check whitelist (always enabled)
        if user_id and user_id in flag["whitelist_users"]:
            logger.debug(f"User '{user_id}' whitelisted for '{flag_name}'")
            return True

        # Check date gates
        if flag.get("start_date"):
            try:
                start_date = datetime.fromisoformat(flag["start_date"])
                if datetime.utcnow() < start_date:
                    logger.debug(f"Feature '{flag_name}' not yet started")
                    return False
            except ValueError:
                logger.error(f"Invalid start_date for '{flag_name}': {flag['start_date']}")

        if flag.get("end_date"):
            try:
                end_date = datetime.fromisoformat(flag["end_date"])
                if datetime.utcnow() > end_date:
                    logger.debug(f"Feature '{flag_name}' expired")
                    return False
            except ValueError:
                logger.error(f"Invalid end_date for '{flag_name}': {flag['end_date']}")

        # Check rollout percentage
        rollout = flag["rollout_percentage"]

        if rollout >= 100:
            logger.debug(f"Feature '{flag_name}' at 100% rollout")
            return True

        if rollout <= 0:
            logger.debug(f"Feature '{flag_name}' at 0% rollout")
            return False

        if user_id:
            # Hash user_id to deterministic 0-99 range
            hash_val = int(hashlib.md5(f"{user_id}:{flag_name}".encode()).hexdigest(), 16) % 100
            enabled = hash_val < rollout
            logger.debug(f"Feature '{flag_name}' for user '{user_id}': hash={hash_val}, rollout={rollout}, enabled={enabled}")
            return enabled

        # No user_id provided, check global rollout
        return rollout >= 100

    @classmethod
    def get_flag_status(cls, flag_name: str) -> Dict[str, Any]:
        """
        Get full flag configuration.

        Args:
            flag_name: Name of the feature flag

        Returns:
            Dictionary with flag configuration, or empty dict if not found
        """
        return cls.FLAGS.get(flag_name, {}).copy()

    @classmethod
    def list_flags(cls, tags: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        List all feature flags, optionally filtered by tags.

        Args:
            tags: Optional list of tags to filter by

        Returns:
            Dictionary of flag_name -> flag_config
        """
        if not tags:
            return cls.FLAGS.copy()

        return {
            name: config.copy()
            for name, config in cls.FLAGS.items()
            if any(tag in config.get("tags", []) for tag in tags)
        }

    @classmethod
    def get_user_flags(cls, user_id: str) -> Dict[str, bool]:
        """
        Get all flags enabled for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of flag_name -> enabled_status
        """
        return {
            name: cls.is_enabled(name, user_id)
            for name in cls.FLAGS.keys()
        }

    @classmethod
    def set_flag(cls, flag_name: str, **kwargs) -> bool:
        """
        Dynamically update flag configuration.
        WARNING: Changes are in-memory only, won't persist across restarts.

        Args:
            flag_name: Name of the feature flag
            **kwargs: Flag attributes to update (enabled, rollout_percentage, etc.)

        Returns:
            True if flag was updated, False if flag doesn't exist
        """
        if flag_name not in cls.FLAGS:
            logger.error(f"Cannot set non-existent flag '{flag_name}'")
            return False

        for key, value in kwargs.items():
            if key in cls.FLAGS[flag_name]:
                old_value = cls.FLAGS[flag_name][key]
                cls.FLAGS[flag_name][key] = value
                logger.info(f"Updated flag '{flag_name}.{key}': {old_value} -> {value}")
            else:
                logger.warning(f"Invalid attribute '{key}' for flag '{flag_name}'")

        return True


# Convenience functions for common operations
def is_unified_llm_hub_enabled(user_id: Optional[str] = None) -> bool:
    """Check if unified LLM hub is enabled for user."""
    return FeatureFlags.is_enabled("unified_llm_hub", user_id)


def get_enabled_features(user_id: str) -> List[str]:
    """Get list of feature names enabled for user."""
    return [
        name for name, enabled in FeatureFlags.get_user_flags(user_id).items()
        if enabled
    ]
