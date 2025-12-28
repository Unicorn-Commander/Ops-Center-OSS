"""
Deployment Configuration API
Provides deployment-specific configuration to frontend
"""

import os
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/api/v1/deployment", tags=["deployment"])


class DeploymentConfig(BaseModel):
    """Deployment configuration response model"""
    deployment_type: str  # standalone, hardware-appliance, enterprise
    primary_app_url: Optional[str]
    admin_only_mode: bool
    registered_applications: List[str]
    enabled_features: List[str]
    branding: Dict[str, str]


class DeploymentService:
    """Service for managing deployment configuration"""
    
    @staticmethod
    def detect_deployment_type() -> str:
        """Auto-detect the deployment type based on environment"""
        # Check explicit environment variable
        deployment_type = os.getenv("DEPLOYMENT_TYPE", "").lower()
        if deployment_type in ["hardware-appliance", "enterprise", "standalone"]:
            return deployment_type
        
        # Check for hardware appliance indicators
        if os.path.exists("/home/ucadmin/Meeting-Ops"):
            return "hardware-appliance"
        
        # Check for enterprise indicators (Authentik, etc.)
        if os.getenv("AUTHENTIK_URL"):
            return "enterprise"
        
        # Default to standalone
        return "standalone"
    
    @staticmethod
    def get_primary_app_url() -> Optional[str]:
        """Get the primary application URL for hardware appliance mode"""
        # Check environment variable first
        primary_url = os.getenv("PRIMARY_APP_URL")
        if primary_url:
            return primary_url
        
        # For hardware appliance, Meeting-Ops is primary
        deployment_type = DeploymentService.detect_deployment_type()
        if deployment_type == "hardware-appliance":
            # Use port 7777 for Meeting-Ops frontend
            return "http://localhost:7777"
        
        return None
    
    @staticmethod
    def get_registered_applications() -> List[str]:
        """Get list of registered applications"""
        apps = []
        
        # Check for Meeting-Ops
        if os.path.exists("/home/ucadmin/Meeting-Ops"):
            apps.append("meeting-ops")
        
        # Check for UC-1
        if os.path.exists("/home/ucadmin/UC-1"):
            apps.append("uc-1")
        
        # Check for UC-1-Pro
        if os.path.exists("/home/ucadmin/UC-1-Pro"):
            apps.append("uc-1-pro")
        
        return apps
    
    @staticmethod
    def get_enabled_features() -> List[str]:
        """Get list of enabled features based on deployment"""
        features = ["authentication", "monitoring"]
        
        deployment_type = DeploymentService.detect_deployment_type()
        
        if deployment_type == "hardware-appliance":
            features.extend([
                "npu-acceleration",
                "ollama-ai",
                "llamacpp",
                "meeting-recording",
                "live-transcription"
            ])
        elif deployment_type == "enterprise":
            features.extend([
                "sso-authentik",
                "multi-tenant",
                "advanced-security",
                "ldap-integration"
            ])
        else:  # standalone
            features.extend([
                "basic-auth",
                "local-models",
                "single-user"
            ])
        
        return features
    
    @staticmethod
    def is_admin_only_mode() -> bool:
        """Check if this deployment is admin-only mode"""
        deployment_type = DeploymentService.detect_deployment_type()
        return deployment_type == "hardware-appliance"
    
    @staticmethod
    def get_branding_config() -> Dict[str, str]:
        """Get branding configuration (alias for get_branding)"""
        return DeploymentService.get_branding()
    
    @staticmethod
    def get_branding() -> Dict[str, str]:
        """Get branding configuration"""
        deployment_type = DeploymentService.detect_deployment_type()
        
        if deployment_type == "hardware-appliance":
            return {
                "name": "Ops-Center - Outpost",
                "subtitle": "Meeting-Ops",
                "logo": "/assets/uc-logo.png",
                "theme": "dark"
            }
        elif deployment_type == "enterprise":
            return {
                "name": "UC-1-Pro Enterprise",
                "subtitle": "Enterprise Command Center",
                "logo": "/assets/uc-pro-logo.png",
                "theme": "blue"
            }
        else:
            return {
                "name": "Ops Center",
                "subtitle": "System Administration",
                "logo": "/assets/ops-center-logo.png",
                "theme": "gray"
            }


@router.get("/config", response_model=DeploymentConfig)
async def get_deployment_config():
    """Get deployment configuration for frontend"""
    service = DeploymentService()
    
    deployment_type = service.detect_deployment_type()
    
    return DeploymentConfig(
        deployment_type=deployment_type,
        primary_app_url=service.get_primary_app_url(),
        admin_only_mode=(deployment_type == "hardware-appliance"),
        registered_applications=service.get_registered_applications(),
        enabled_features=service.get_enabled_features(),
        branding=service.get_branding()
    )


@router.get("/type")
async def get_deployment_type():
    """Get just the deployment type"""
    return {
        "deployment_type": DeploymentService.detect_deployment_type()
    }


@router.get("/apps")
async def get_registered_apps():
    """Get list of registered applications"""
    return {
        "applications": DeploymentService.get_registered_applications()
    }


@router.post("/register-app")
async def register_application(app_name: str, app_url: str):
    """Register a new application with Ops-Center"""
    # This would typically save to a database or config file
    # For now, we'll just return success
    return {
        "status": "success",
        "message": f"Registered {app_name} at {app_url}"
    }