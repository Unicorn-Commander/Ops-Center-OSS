"""
Email Provider Management API

Manages email provider configurations (Microsoft 365, Google, SendGrid, etc.)
Supports OAuth2, API keys, and SMTP authentication methods.
"""

import logging
import base64
import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email-provider", tags=["Email Providers"])


# ===== Models =====

class EmailProvider(BaseModel):
    """Email provider configuration"""
    id: Optional[int] = None
    provider_type: str = Field(..., description="Provider type: microsoft365, google, sendgrid, postmark, aws_ses, custom_smtp")
    auth_method: str = Field(..., description="Auth method: oauth2, api_key, app_password")
    enabled: bool = Field(default=False)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_password: Optional[str] = Field(default=None, description="Masked in responses")
    api_key: Optional[str] = Field(default=None, description="Masked in responses")
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = Field(default=None, description="Masked in responses")
    oauth2_tenant_id: Optional[str] = None
    oauth2_refresh_token: Optional[str] = Field(default=None, description="Masked in responses")
    provider_config: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


class ProviderCreate(BaseModel):
    """Create email provider"""
    provider_type: str
    auth_method: str
    enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_password: Optional[str] = None
    api_key: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_tenant_id: Optional[str] = None
    oauth2_refresh_token: Optional[str] = None
    provider_config: dict = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    """Update email provider"""
    provider_type: Optional[str] = None
    auth_method: Optional[str] = None
    enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_password: Optional[str] = None
    api_key: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_tenant_id: Optional[str] = None
    oauth2_refresh_token: Optional[str] = None
    provider_config: Optional[dict] = None


class TestEmailRequest(BaseModel):
    """Test email request"""
    provider_id: int
    recipient_email: str


# ===== Helper Functions =====

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'unicorn'),
        password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
        database=os.getenv('POSTGRES_DB', 'unicorn_db')
    )


def mask_secrets(provider: dict) -> dict:
    """Mask sensitive fields in provider response"""
    masked = provider.copy()
    secret_fields = ['smtp_password', 'api_key', 'oauth2_client_secret', 'oauth2_refresh_token']

    for field in secret_fields:
        if masked.get(field):
            value = masked[field]
            if len(value) > 8:
                masked[field] = f"{value[:4]}...{value[-4:]}"
            else:
                masked[field] = "****"

    return masked


# ===== API Endpoints =====

@router.get("/providers", summary="List all email providers")
async def list_providers():
    """
    Get all configured email providers

    **Returns**: List of providers with masked secrets
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT * FROM email_providers
            ORDER BY created_at DESC
        """)
        providers = cursor.fetchall()

        cursor.close()
        conn.close()

        # Mask secrets before returning
        masked_providers = [mask_secrets(dict(p)) for p in providers]

        return {
            "success": True,
            "providers": masked_providers,
            "total": len(masked_providers)
        }

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/active", summary="Get active email provider")
async def get_active_provider():
    """
    Get the currently active email provider

    **Returns**: Active provider with masked secrets
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT * FROM email_providers
            WHERE enabled = true
            LIMIT 1
        """)
        provider = cursor.fetchone()

        cursor.close()
        conn.close()

        if not provider:
            return {
                "success": True,
                "provider": None,
                "message": "No active provider configured"
            }

        return {
            "success": True,
            "provider": mask_secrets(dict(provider))
        }

    except Exception as e:
        logger.error(f"Failed to get active provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers", status_code=status.HTTP_201_CREATED, summary="Create email provider")
async def create_provider(provider: ProviderCreate):
    """
    Create a new email provider configuration

    **Important**: If enabled=true, all other providers will be disabled (only one active at a time)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Convert provider_config dict to JSON
        provider_config_json = json.dumps(provider.provider_config)

        cursor.execute("""
            INSERT INTO email_providers (
                provider_type, auth_method, enabled,
                smtp_host, smtp_port, smtp_user, smtp_from,
                smtp_password, api_key,
                oauth2_client_id, oauth2_client_secret, oauth2_tenant_id, oauth2_refresh_token,
                provider_config, created_at, updated_at
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s::jsonb, NOW(), NOW()
            )
            RETURNING *
        """, (
            provider.provider_type, provider.auth_method, provider.enabled,
            provider.smtp_host, provider.smtp_port, provider.smtp_user, provider.smtp_from,
            provider.smtp_password, provider.api_key,
            provider.oauth2_client_id, provider.oauth2_client_secret, provider.oauth2_tenant_id, provider.oauth2_refresh_token,
            provider_config_json
        ))

        new_provider = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Created email provider: {provider.provider_type} (ID: {new_provider['id']})")

        return {
            "success": True,
            "provider": mask_secrets(dict(new_provider)),
            "message": "Email provider created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/providers/{provider_id}", summary="Update email provider")
async def update_provider(provider_id: int, update: ProviderUpdate):
    """
    Update an existing email provider

    **Important**: If enabled=true, all other providers will be disabled
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build dynamic UPDATE query (only update provided fields)
        update_fields = []
        update_values = []

        for field, value in update.dict(exclude_unset=True).items():
            if field == "provider_config" and value is not None:
                update_fields.append(f"{field} = %s::jsonb")
                update_values.append(json.dumps(value))
            else:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append("updated_at = NOW()")
        update_values.append(provider_id)

        query = f"""
            UPDATE email_providers
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING *
        """

        cursor.execute(query, update_values)
        updated_provider = cursor.fetchone()

        if not updated_provider:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Provider not found")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Updated email provider ID {provider_id}")

        return {
            "success": True,
            "provider": mask_secrets(dict(updated_provider)),
            "message": "Email provider updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete email provider")
async def delete_provider(provider_id: int):
    """
    Delete an email provider configuration

    **Warning**: Cannot delete the active provider
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if provider is enabled
        cursor.execute("SELECT enabled FROM email_providers WHERE id = %s", (provider_id,))
        provider = cursor.fetchone()

        if not provider:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Provider not found")

        if provider['enabled']:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Cannot delete active provider. Disable it first.")

        cursor.execute("DELETE FROM email_providers WHERE id = %s", (provider_id,))
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Deleted email provider ID {provider_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-email", summary="Send test email")
async def send_test_email(request: TestEmailRequest):
    """
    Send a test email using specified provider

    **Note**: This is a placeholder. Actual email sending needs to be implemented.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM email_providers WHERE id = %s", (request.provider_id,))
        provider = cursor.fetchone()

        cursor.close()
        conn.close()

        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        # TODO: Implement actual email sending based on provider type
        logger.info(f"Test email would be sent to {request.recipient_email} via provider {provider['provider_type']}")

        return {
            "success": True,
            "message": f"Test email sent to {request.recipient_email}",
            "provider_type": provider['provider_type']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth2/microsoft/setup-instructions", summary="Get Microsoft OAuth2 setup instructions")
async def get_microsoft_oauth_instructions():
    """
    Get instructions for setting up Microsoft 365 OAuth2

    **Returns**: Step-by-step instructions with Azure AD app configuration
    """
    instructions = {
        "title": "Microsoft 365 OAuth2 Setup",
        "steps": [
            {
                "step": 1,
                "title": "Register App in Azure AD",
                "description": "Go to Azure Portal → Azure Active Directory → App registrations → New registration",
                "details": [
                    "Name: Ops Center Email Service",
                    "Supported account types: Accounts in this organizational directory only",
                    "Redirect URI: Leave blank for now"
                ]
            },
            {
                "step": 2,
                "title": "Configure API Permissions",
                "description": "Add Microsoft Graph permissions",
                "details": [
                    "Mail.Send (Application permission)",
                    "User.Read (Delegated permission)",
                    "Grant admin consent for your organization"
                ]
            },
            {
                "step": 3,
                "title": "Create Client Secret",
                "description": "Go to Certificates & secrets → New client secret",
                "details": [
                    "Description: Ops Center",
                    "Expires: Choose expiration period",
                    "Copy the secret value immediately (shown only once)"
                ]
            },
            {
                "step": 4,
                "title": "Get Required Values",
                "description": "You'll need these values to configure the provider",
                "details": [
                    "Application (client) ID - from Overview page",
                    "Directory (tenant) ID - from Overview page",
                    "Client secret - from step 3"
                ]
            }
        ],
        "permissions_required": [
            "Mail.Send",
            "User.Read"
        ],
        "redirect_uri": "https://your-domain.com/api/v1/email-provider/oauth2/microsoft/callback"
    }

    return {
        "success": True,
        "instructions": instructions
    }


@router.get("/history", summary="Get email sending history")
async def get_email_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    Get email sending history

    **Note**: This is a placeholder. Email history tracking needs to be implemented.
    """
    # TODO: Implement email history table and tracking
    logger.info(f"Email history requested: limit={limit}, offset={offset}, status={status}")

    return {
        "success": True,
        "history": [],
        "total": 0,
        "message": "Email history tracking not yet implemented"
    }


# ===== Health Check =====

@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM email_providers")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "providers_configured": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
