"""
Service Access Control Middleware
Manages user access to different services based on subscription tier
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Service access matrix - which tiers can access which services
SERVICE_ACCESS_MATRIX = {
    "trial": {
        "services": ["ops-center", "chat"],
        "features": ["basic_models"],
        "api_calls": 100,
        "valid_days": 7
    },
    "byok": {  # Bring Your Own Keys - Starter tier
        "services": ["ops-center", "chat", "search"],
        "features": ["basic_models", "byok"],
        "api_calls": 1000,
        "valid_days": 30
    },
    "professional": {
        "services": ["ops-center", "chat", "search", "billing", "litellm", "lago", "tts", "stt"],
        "features": ["all_models", "byok", "priority_support", "team_management"],
        "api_calls": 10000,
        "valid_days": 30
    },
    "enterprise": {
        "services": ["*"],  # All services
        "features": ["all_models", "byok", "priority_support", "team_management", "sso", "audit_logs", "sla"],
        "api_calls": -1,  # Unlimited
        "valid_days": 30
    }
}

# Service URLs and metadata
PROTECTED_SERVICES = {
    "ops-center": {
        "name": "Operations Center",
        "urls": ["https://your-domain.com", "/", "/admin", "/dashboard"],
        "min_tier": "trial"
    },
    "chat": {
        "name": "Chat UI",
        "urls": ["https://chat.your-domain.com", "/chat"],
        "min_tier": "trial"
    },
    "search": {
        "name": "Center-Deep Search",
        "urls": ["https://search.your-domain.com", "/search"],
        "min_tier": "byok"
    },
    "billing": {
        "name": "Billing Dashboard",
        "urls": ["https://billing.your-domain.com", "/billing"],
        "min_tier": "professional"
    },
    "litellm": {
        "name": "AI Gateway",
        "urls": ["https://ai.your-domain.com", "/ai"],
        "min_tier": "professional"
    },
    "tts": {
        "name": "Text to Speech",
        "urls": ["https://tts.your-domain.com", "/tts"],
        "min_tier": "professional"
    },
    "stt": {
        "name": "Speech to Text",
        "urls": ["https://stt.your-domain.com", "/stt"],
        "min_tier": "professional"
    }
}

class ServiceAccessManager:
    """Manages user access to services based on subscription"""

    def __init__(self):
        self.access_matrix = SERVICE_ACCESS_MATRIX
        self.services = PROTECTED_SERVICES

    def check_user_access(self, user_info: Dict, service: str) -> Dict:
        """
        Check if user has access to a specific service

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "tier_required": str,
                "user_tier": str,
                "upgrade_url": str (if not allowed)
            }
        """
        # Get user's subscription tier
        user_tier = self._get_user_tier(user_info)

        # Check if service exists
        if service not in self.services:
            return {
                "allowed": True,  # Allow unknown services by default
                "reason": "Service not in protected list",
                "user_tier": user_tier
            }

        # Get minimum tier required for service
        min_tier = self.services[service]["min_tier"]

        # Check if user's tier allows access
        if user_tier == "enterprise":
            # Enterprise users have access to everything
            return {
                "allowed": True,
                "reason": "Enterprise tier has unlimited access",
                "user_tier": user_tier,
                "tier_required": min_tier
            }

        # Check if service is in user's allowed services
        tier_config = self.access_matrix.get(user_tier, {})
        allowed_services = tier_config.get("services", [])

        if "*" in allowed_services or service in allowed_services:
            # Check if subscription is still valid
            if self._is_subscription_valid(user_info, user_tier):
                return {
                    "allowed": True,
                    "reason": f"Service allowed for {user_tier} tier",
                    "user_tier": user_tier,
                    "tier_required": min_tier
                }
            else:
                return {
                    "allowed": False,
                    "reason": "Subscription expired",
                    "user_tier": user_tier,
                    "tier_required": min_tier,
                    "upgrade_url": "/pricing"
                }
        else:
            # User needs to upgrade
            return {
                "allowed": False,
                "reason": f"Service requires {min_tier} tier or higher",
                "user_tier": user_tier,
                "tier_required": min_tier,
                "upgrade_url": f"/upgrade?from={user_tier}&to={min_tier}"
            }

    def get_user_services(self, user_info: Dict) -> List[Dict]:
        """Get list of all services available to user"""
        user_tier = self._get_user_tier(user_info)
        tier_config = self.access_matrix.get(user_tier, {})
        allowed_services = tier_config.get("services", [])

        services = []
        for service_key, service_info in self.services.items():
            if "*" in allowed_services or service_key in allowed_services:
                services.append({
                    "key": service_key,
                    "name": service_info["name"],
                    "url": service_info["urls"][0],
                    "available": True
                })
            else:
                services.append({
                    "key": service_key,
                    "name": service_info["name"],
                    "url": service_info["urls"][0],
                    "available": False,
                    "required_tier": service_info["min_tier"]
                })

        return services

    def get_user_limits(self, user_info: Dict) -> Dict:
        """Get user's API limits and usage"""
        user_tier = self._get_user_tier(user_info)
        tier_config = self.access_matrix.get(user_tier, {})

        return {
            "tier": user_tier,
            "api_calls_limit": tier_config.get("api_calls", 0),
            "api_calls_used": user_info.get("attributes", {}).get("api_calls_used", 0),
            "features": tier_config.get("features", []),
            "valid_until": self._get_subscription_expiry(user_info, user_tier)
        }

    def _get_user_tier(self, user_info: Dict) -> str:
        """Extract user's subscription tier from user info"""
        # Check user attributes first
        attributes = user_info.get("attributes", {})
        tier = attributes.get("subscription_tier")

        if tier:
            return tier

        # Check user groups
        groups = user_info.get("groups", [])
        for group in groups:
            if isinstance(group, str) and group.startswith("subscription_"):
                return group.replace("subscription_", "")
            elif isinstance(group, dict):
                group_name = group.get("name", "")
                if group_name.startswith("subscription_"):
                    return group_name.replace("subscription_", "")

        # Check for admin status
        if user_info.get("is_superuser") or user_info.get("role") == "admin":
            return "enterprise"

        # Default to trial for new users
        return "trial"

    def _is_subscription_valid(self, user_info: Dict, tier: str) -> bool:
        """Check if user's subscription is still valid"""
        if tier == "enterprise":
            return True  # Enterprise always valid

        attributes = user_info.get("attributes", {})

        # Check subscription expiry date
        expiry_str = attributes.get("subscription_expires")
        if expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)
                return expiry > datetime.now()
            except:
                pass

        # Check Stripe subscription status
        stripe_status = attributes.get("stripe_subscription_status")
        if stripe_status in ["active", "trialing"]:
            return True

        # For trial, check account creation date
        if tier == "trial":
            created_str = attributes.get("date_joined") or user_info.get("date_joined")
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    trial_expiry = created + timedelta(days=7)
                    return trial_expiry > datetime.now()
                except:
                    pass

        return False

    def _get_subscription_expiry(self, user_info: Dict, tier: str) -> Optional[str]:
        """Get subscription expiry date"""
        attributes = user_info.get("attributes", {})

        # Check stored expiry
        expiry_str = attributes.get("subscription_expires")
        if expiry_str:
            return expiry_str

        # Calculate based on tier
        if tier == "trial":
            created_str = attributes.get("date_joined") or user_info.get("date_joined")
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    trial_expiry = created + timedelta(days=7)
                    return trial_expiry.isoformat()
                except:
                    pass

        return None

    def upgrade_user_tier(self, user_info: Dict, new_tier: str, duration_days: int = 30) -> Dict:
        """
        Upgrade user to a new tier
        This should be called after successful payment
        """
        expiry = datetime.now() + timedelta(days=duration_days)

        return {
            "subscription_tier": new_tier,
            "subscription_expires": expiry.isoformat(),
            "subscription_started": datetime.now().isoformat(),
            "previous_tier": self._get_user_tier(user_info)
        }


# Singleton instance
service_access_manager = ServiceAccessManager()