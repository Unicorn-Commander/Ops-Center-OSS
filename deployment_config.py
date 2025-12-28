"""
Deployment-specific configuration for UC-1 Pro subscription system.

This module handles different deployment types (UC-Cloud, UC-1 Pro GPU, Self-hosted)
and configures product availability, features, and pricing accordingly.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import os

class DeploymentType(Enum):
    """Supported deployment types."""
    UC_CLOUD = "uc_cloud"  # VPS/CPU deployment
    UC_1_PRO_GPU = "uc_1_pro_gpu"  # GPU server deployment
    SELF_HOSTED = "self_hosted"  # Customer-hosted

@dataclass
class DeploymentConfig:
    """Configuration for a specific deployment type."""
    deployment_type: DeploymentType
    name: str
    description: str

    # Available products
    available_products: Set[str]

    # Available features
    available_features: Set[str]

    # Default settings
    default_inference_credits: int
    default_api_calls: int
    default_storage_gb: int

    # Pricing modifiers
    pricing_multiplier: float = 1.0

    # Infrastructure
    has_local_gpu: bool = False
    has_local_inference: bool = False
    requires_license: bool = False

    # URLs
    base_url: str = ""
    auth_url: str = ""

    # Metadata
    metadata: Dict = None

class DeploymentConfigManager:
    """
    Manages deployment-specific configuration.
    """

    # Define all deployment configurations
    CONFIGS: Dict[DeploymentType, DeploymentConfig] = {
        DeploymentType.UC_CLOUD: DeploymentConfig(
            deployment_type=DeploymentType.UC_CLOUD,
            name="UC-Cloud (CPU)",
            description="Shared VPS infrastructure with remote LLM inference",

            available_products={
                "platform_free",
                "platform_pro",
                "platform_enterprise",
                "app_openwebui_pro",
                "app_bolt_diy_pro",
                "app_n8n_pro",
                "app_center_deep_pro",
                "feature_openwebui_custom_models",
                "feature_bolt_diy_templates",
                "usage_inference_credits",
                "usage_api_calls",
                "usage_storage"
            },

            available_features={
                "openwebui:basic",
                "openwebui:custom_models",
                "openwebui:advanced_prompts",
                "bolt_diy:templates",
                "bolt_diy:export",
                "bolt_diy:github_integration",
                "n8n:workflows",
                "n8n:custom_nodes",
                "center_deep:search",
                "center_deep:ai_summary"
            },

            default_inference_credits=100,
            default_api_calls=1000,
            default_storage_gb=1,

            pricing_multiplier=1.0,  # Base pricing

            has_local_gpu=False,
            has_local_inference=False,
            requires_license=False,

            base_url="https://your-domain.com",
            auth_url="https://auth.your-domain.com",

            metadata={
                "sla": "99%",
                "support_tier": "standard",
                "inference_type": "remote_api"
            }
        ),

        DeploymentType.UC_1_PRO_GPU: DeploymentConfig(
            deployment_type=DeploymentType.UC_1_PRO_GPU,
            name="UC-1 Pro GPU",
            description="Dedicated GPU servers with local inference",

            available_products={
                "platform_pro_gpu",
                "platform_enterprise_gpu",
                "app_openwebui_pro",
                "app_bolt_diy_pro",
                "app_n8n_pro",
                "app_center_deep_pro",
                "feature_openwebui_custom_models",
                "feature_bolt_diy_gpu_inference",
                "feature_bolt_diy_templates",
                "usage_inference_credits",
                "usage_gpu_hours",
                "usage_api_calls",
                "usage_storage"
            },

            available_features={
                "openwebui:basic",
                "openwebui:custom_models",
                "openwebui:advanced_prompts",
                "openwebui:local_inference",
                "bolt_diy:templates",
                "bolt_diy:export",
                "bolt_diy:github_integration",
                "bolt_diy:gpu_inference",
                "bolt_diy:local_models",
                "n8n:workflows",
                "n8n:custom_nodes",
                "center_deep:search",
                "center_deep:ai_summary",
                "platform:local_gpu"
            },

            default_inference_credits=1000,  # More credits for GPU tier
            default_api_calls=10000,
            default_storage_gb=10,

            pricing_multiplier=2.0,  # GPU deployments cost more

            has_local_gpu=True,
            has_local_inference=True,
            requires_license=False,

            base_url="https://gpu.your-domain.com",
            auth_url="https://auth.gpu.your-domain.com",

            metadata={
                "sla": "99.9%",
                "support_tier": "priority",
                "inference_type": "local_gpu",
                "gpu_type": "A100"
            }
        ),

        DeploymentType.SELF_HOSTED: DeploymentConfig(
            deployment_type=DeploymentType.SELF_HOSTED,
            name="Self-Hosted",
            description="Customer-owned infrastructure with perpetual licensing",

            available_products={
                "license_uc1_pro_gpu_perpetual",
                "license_uc1_pro_gpu_5year",
                "license_uc1_pro_gpu_annual",
                "maintenance_renewal",
                # All apps included with license
                "app_openwebui_pro",
                "app_bolt_diy_pro",
                "app_n8n_pro",
                "app_center_deep_pro"
            },

            available_features={
                # All features available
                "openwebui:basic",
                "openwebui:custom_models",
                "openwebui:advanced_prompts",
                "openwebui:local_inference",
                "bolt_diy:templates",
                "bolt_diy:export",
                "bolt_diy:github_integration",
                "bolt_diy:gpu_inference",
                "bolt_diy:local_models",
                "n8n:workflows",
                "n8n:custom_nodes",
                "center_deep:search",
                "center_deep:ai_summary",
                "center_deep:custom_crawlers",
                "platform:local_gpu",
                "platform:air_gapped",
                "platform:custom_branding",
                "platform:unlimited_users"
            },

            default_inference_credits=-1,  # Unlimited (local inference)
            default_api_calls=-1,  # Unlimited
            default_storage_gb=-1,  # Unlimited (customer storage)

            pricing_multiplier=0.0,  # No recurring charges (license-based)

            has_local_gpu=True,
            has_local_inference=True,
            requires_license=True,

            base_url="",  # Customer-specified
            auth_url="",  # Customer-specified

            metadata={
                "sla": "customer_managed",
                "support_tier": "maintenance_dependent",
                "inference_type": "local_customer",
                "deployment": "customer_infrastructure"
            }
        )
    }

    @classmethod
    def get_config(cls, deployment_type: DeploymentType) -> DeploymentConfig:
        """Get configuration for a deployment type."""
        return cls.CONFIGS.get(deployment_type)

    @classmethod
    def get_current_deployment(cls) -> DeploymentConfig:
        """
        Detect and return current deployment configuration.

        Uses environment variable or auto-detection.
        """
        # Check environment variable
        deployment_env = os.getenv("UC_DEPLOYMENT_TYPE")
        if deployment_env:
            try:
                deployment_type = DeploymentType(deployment_env)
                return cls.get_config(deployment_type)
            except ValueError:
                pass

        # Auto-detect based on environment
        if os.path.exists("/opt/uc1pro/license.key"):
            # Self-hosted deployment
            return cls.get_config(DeploymentType.SELF_HOSTED)
        elif os.path.exists("/dev/nvidia0"):
            # GPU available
            return cls.get_config(DeploymentType.UC_1_PRO_GPU)
        else:
            # Default to UC-Cloud
            return cls.get_config(DeploymentType.UC_CLOUD)

    @classmethod
    def is_product_available(cls, product_code: str, deployment_type: Optional[DeploymentType] = None) -> bool:
        """Check if a product is available in the current deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return product_code in config.available_products

    @classmethod
    def is_feature_available(cls, feature_key: str, deployment_type: Optional[DeploymentType] = None) -> bool:
        """Check if a feature is available in the current deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return feature_key in config.available_features

    @classmethod
    def get_pricing_multiplier(cls, deployment_type: Optional[DeploymentType] = None) -> float:
        """Get pricing multiplier for the deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return config.pricing_multiplier

    @classmethod
    def get_available_products(cls, deployment_type: Optional[DeploymentType] = None) -> Set[str]:
        """Get all available products for the deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return config.available_products

    @classmethod
    def get_available_features(cls, deployment_type: Optional[DeploymentType] = None) -> Set[str]:
        """Get all available features for the deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return config.available_features

    @classmethod
    def get_default_credits(cls, deployment_type: Optional[DeploymentType] = None) -> Dict[str, int]:
        """Get default credit allocations for the deployment."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return {
            "inference_credits": config.default_inference_credits,
            "api_calls": config.default_api_calls,
            "storage_gb": config.default_storage_gb
        }

    @classmethod
    def requires_license_validation(cls, deployment_type: Optional[DeploymentType] = None) -> bool:
        """Check if deployment requires license validation."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return config.requires_license

    @classmethod
    def has_local_gpu_access(cls, deployment_type: Optional[DeploymentType] = None) -> bool:
        """Check if deployment has local GPU access."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return config.has_local_gpu

    @classmethod
    def get_deployment_info(cls, deployment_type: Optional[DeploymentType] = None) -> Dict:
        """Get comprehensive deployment information."""
        if deployment_type is None:
            config = cls.get_current_deployment()
        else:
            config = cls.get_config(deployment_type)

        return {
            "deployment_type": config.deployment_type.value,
            "name": config.name,
            "description": config.description,
            "has_local_gpu": config.has_local_gpu,
            "has_local_inference": config.has_local_inference,
            "requires_license": config.requires_license,
            "base_url": config.base_url,
            "auth_url": config.auth_url,
            "metadata": config.metadata,
            "available_products_count": len(config.available_products),
            "available_features_count": len(config.available_features)
        }


# Product availability matrix by deployment
PRODUCT_AVAILABILITY_MATRIX = {
    "platform_free": [DeploymentType.UC_CLOUD],
    "platform_pro": [DeploymentType.UC_CLOUD],
    "platform_pro_gpu": [DeploymentType.UC_1_PRO_GPU],
    "platform_enterprise": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU],

    "app_openwebui_pro": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],
    "app_bolt_diy_pro": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],
    "app_n8n_pro": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],
    "app_center_deep_pro": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],

    "feature_openwebui_custom_models": [DeploymentType.UC_CLOUD, DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],
    "feature_bolt_diy_gpu_inference": [DeploymentType.UC_1_PRO_GPU, DeploymentType.SELF_HOSTED],

    "license_uc1_pro_gpu_perpetual": [DeploymentType.SELF_HOSTED],
    "license_uc1_pro_gpu_5year": [DeploymentType.SELF_HOSTED],
    "license_uc1_pro_gpu_annual": [DeploymentType.SELF_HOSTED],
}


# Example usage
if __name__ == "__main__":
    # Get current deployment
    current = DeploymentConfigManager.get_current_deployment()
    print(f"Current deployment: {current.name}")
    print(f"Has local GPU: {current.has_local_gpu}")
    print(f"Available products: {len(current.available_products)}")
    print(f"Available features: {len(current.available_features)}")

    # Check product availability
    print(f"\nBolt.DIY Pro available: {DeploymentConfigManager.is_product_available('app_bolt_diy_pro')}")
    print(f"GPU inference feature available: {DeploymentConfigManager.is_feature_available('bolt_diy:gpu_inference')}")

    # Get default credits
    credits = DeploymentConfigManager.get_default_credits()
    print(f"\nDefault credits: {credits}")

    # Get deployment info
    info = DeploymentConfigManager.get_deployment_info()
    print(f"\nDeployment info: {info}")
