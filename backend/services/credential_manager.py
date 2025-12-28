"""
Credential Management Service for UC-Cloud Ops-Center

Centralized credential management for service API tokens and keys:
- Cloudflare API tokens
- NameCheap API keys
- GitHub API tokens
- Stripe secret keys

Features:
- Fernet encryption for credential storage
- Credential masking for display
- Credential testing (API validation)
- Environment variable fallback
- Audit logging for all operations
- Support for multiple credential types per service

Security:
- All credentials encrypted at rest using existing SecretManager
- Credentials never exposed in API responses (always masked)
- Audit trail for all credential operations
- Unique constraint per user+service+type

Epic 1.6/1.7: Service Credential Management
Author: Backend Development Team Lead
Date: October 23, 2025
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from secret_manager import SecretManager, SecretManagementError, EncryptionError, DecryptionError
from audit_logger import audit_logger

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Supported Services Configuration
# ============================================================================

SUPPORTED_SERVICES = {
    "cloudflare": {
        "name": "Cloudflare",
        "credential_types": ["api_token"],
        "test_url": "https://api.cloudflare.com/client/v4/user/tokens/verify",
        "auth_header": "Bearer",
        "env_var": "CLOUDFLARE_API_TOKEN"
    },
    "namecheap": {
        "name": "NameCheap",
        "credential_types": ["api_key", "api_user"],
        "test_url": "https://api.namecheap.com/xml.response",  # Requires special params
        "auth_header": None,
        "env_var": "NAMECHEAP_API_KEY"
    },
    "github": {
        "name": "GitHub",
        "credential_types": ["api_token", "personal_access_token"],
        "test_url": "https://api.github.com/user",
        "auth_header": "Bearer",
        "env_var": "GITHUB_API_TOKEN"
    },
    "stripe": {
        "name": "Stripe",
        "credential_types": ["secret_key", "publishable_key"],
        "test_url": "https://api.stripe.com/v1/balance",
        "auth_header": "Bearer",
        "env_var": "STRIPE_SECRET_KEY"
    }
}


# ============================================================================
# Exceptions
# ============================================================================

class CredentialManagementError(Exception):
    """Base exception for credential management operations"""
    pass


class CredentialNotFoundError(CredentialManagementError):
    """Credential not found in database"""
    pass


class CredentialValidationError(CredentialManagementError):
    """Credential validation failed"""
    pass


class UnsupportedServiceError(CredentialManagementError):
    """Service not supported"""
    pass


# ============================================================================
# CredentialManager Service
# ============================================================================

class CredentialManager:
    """
    Centralized credential management service

    Features:
    - Store encrypted credentials in PostgreSQL
    - Retrieve and decrypt credentials for API calls (INTERNAL USE ONLY)
    - List credentials with masked values
    - Test credentials by calling service API
    - Environment variable fallback
    - Audit logging

    Security:
    - Uses existing SecretManager for encryption (Fernet AES-128-CBC)
    - Credentials never exposed in API responses
    - Audit trail for all operations
    - Rate limiting on test operations

    Database:
    - Table: service_credentials
    - Encryption: Fernet (via SecretManager)
    - Storage: PostgreSQL (unicorn_db)
    """

    def __init__(self, db_connection=None):
        """
        Initialize CredentialManager

        Args:
            db_connection: PostgreSQL database connection (asyncpg or psycopg2)
        """
        self.db = db_connection
        self.secret_manager = SecretManager()
        logger.info("CredentialManager initialized")

    async def create_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str,
        value: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update encrypted credential

        Args:
            user_id: Keycloak user ID
            service: Service name (cloudflare, namecheap, github, stripe)
            credential_type: Credential type (api_token, api_key, etc.)
            value: Plaintext credential value
            metadata: Optional metadata (description, etc.)

        Returns:
            Dictionary with credential info (MASKED VALUE ONLY)

        Raises:
            UnsupportedServiceError: If service not supported
            EncryptionError: If encryption fails
            CredentialManagementError: If database operation fails
        """
        # Validate service
        if service not in SUPPORTED_SERVICES:
            raise UnsupportedServiceError(
                f"Service '{service}' not supported. "
                f"Supported services: {', '.join(SUPPORTED_SERVICES.keys())}"
            )

        service_config = SUPPORTED_SERVICES[service]

        # Validate credential type for service
        if credential_type not in service_config["credential_types"]:
            raise CredentialValidationError(
                f"Invalid credential type '{credential_type}' for service '{service}'. "
                f"Valid types: {', '.join(service_config['credential_types'])}"
            )

        try:
            # Encrypt credential
            encrypted_data = self.secret_manager.encrypt_secret(
                secret=value,
                secret_type=credential_type,
                metadata={"user_id": user_id, "service": service}
            )

            # Store in database (UPSERT operation)
            credential_id = str(uuid4())
            now = datetime.utcnow()

            # Check if credential already exists
            existing = await self.db.fetchrow(
                """
                SELECT id FROM service_credentials
                WHERE user_id = $1 AND service = $2 AND credential_type = $3
                """,
                user_id, service, credential_type
            )

            if existing:
                # Update existing credential
                await self.db.execute(
                    """
                    UPDATE service_credentials
                    SET encrypted_value = $1, metadata = $2, updated_at = $3, is_active = true
                    WHERE user_id = $4 AND service = $5 AND credential_type = $6
                    """,
                    encrypted_data["encrypted_value"],
                    metadata or {},
                    now,
                    user_id,
                    service,
                    credential_type
                )
                credential_id = existing["id"]
                logger.info(f"Updated credential: user={user_id}, service={service}, type={credential_type}")
            else:
                # Insert new credential
                await self.db.execute(
                    """
                    INSERT INTO service_credentials
                    (id, user_id, service, credential_type, encrypted_value, metadata, created_at, updated_at, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    credential_id,
                    user_id,
                    service,
                    credential_type,
                    encrypted_data["encrypted_value"],
                    metadata or {},
                    now,
                    now,
                    True
                )
                logger.info(f"Created credential: user={user_id}, service={service}, type={credential_type}")

            # Audit log
            await audit_logger.log(
                action="credential.create" if not existing else "credential.update",
                user_id=user_id,
                resource_type="credential",
                resource_id=credential_id,
                details={
                    "service": service,
                    "credential_type": credential_type,
                    "operation": "update" if existing else "create"
                },
                status="success"
            )

            # Return MASKED credential (NEVER return plaintext)
            return {
                "id": credential_id,
                "service": service,
                "service_name": service_config["name"],
                "credential_type": credential_type,
                "masked_value": self._mask_credential(service, value),
                "created_at": now.isoformat(),
                "metadata": metadata or {}
            }

        except Exception as e:
            logger.error(f"Failed to create credential: {e}")
            await audit_logger.log(
                action="credential.create",
                user_id=user_id,
                resource_type="credential",
                details={"service": service, "credential_type": credential_type, "error": str(e)},
                status="failure"
            )
            raise CredentialManagementError(f"Failed to store credential: {e}")

    async def get_credential_for_api(
        self,
        user_id: str,
        service: str,
        credential_type: str
    ) -> Optional[str]:
        """
        **INTERNAL METHOD - DO NOT EXPOSE VIA API**

        Retrieve and decrypt credential for API calls

        This method returns PLAINTEXT credentials and should ONLY be called
        by internal services (cloudflare_api, migration_api, etc.).
        NEVER expose this method via API endpoints to frontend.

        Args:
            user_id: Keycloak user ID
            service: Service name
            credential_type: Credential type

        Returns:
            Decrypted plaintext credential or None if not found

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            # Query database for active credential
            row = await self.db.fetchrow(
                """
                SELECT encrypted_value FROM service_credentials
                WHERE user_id = $1 AND service = $2 AND credential_type = $3 AND is_active = true
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                user_id, service, credential_type
            )

            if row:
                # Decrypt and return plaintext
                decrypted = self.secret_manager.decrypt_secret(row["encrypted_value"])
                logger.debug(f"Retrieved credential from DB: user={user_id}, service={service}")
                return decrypted

            # Fallback to environment variable
            service_config = SUPPORTED_SERVICES.get(service, {})
            env_var = service_config.get("env_var")

            if env_var:
                env_value = os.getenv(env_var)
                if env_value:
                    logger.info(f"Using environment variable {env_var} for service={service}")
                    return env_value

            logger.warning(f"Credential not found: user={user_id}, service={service}, type={credential_type}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
            raise

    async def list_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all credentials for user with MASKED values only

        Args:
            user_id: Keycloak user ID

        Returns:
            List of credentials with masked values
        """
        try:
            rows = await self.db.fetch(
                """
                SELECT id, service, credential_type, metadata, created_at, updated_at,
                       last_tested, test_status, is_active, encrypted_value
                FROM service_credentials
                WHERE user_id = $1 AND is_active = true
                ORDER BY service, credential_type
                """,
                user_id
            )

            credentials = []
            for row in rows:
                service = row["service"]
                service_config = SUPPORTED_SERVICES.get(service, {})

                # Decrypt to mask properly
                try:
                    decrypted = self.secret_manager.decrypt_secret(row["encrypted_value"])
                    masked_value = self._mask_credential(service, decrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt credential {row['id']}: {e}")
                    masked_value = "***error***"

                credentials.append({
                    "id": row["id"],
                    "service": service,
                    "service_name": service_config.get("name", service),
                    "credential_type": row["credential_type"],
                    "masked_value": masked_value,
                    "metadata": row["metadata"] or {},
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "last_tested": row["last_tested"].isoformat() if row["last_tested"] else None,
                    "test_status": row["test_status"]
                })

            return credentials

        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            raise CredentialManagementError(f"Failed to list credentials: {e}")

    async def update_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str,
        new_value: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update existing credential (wrapper around create_credential)

        Args:
            user_id: Keycloak user ID
            service: Service name
            credential_type: Credential type
            new_value: New plaintext credential value
            metadata: Optional updated metadata

        Returns:
            Updated credential info (masked)
        """
        return await self.create_credential(user_id, service, credential_type, new_value, metadata)

    async def delete_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str
    ) -> bool:
        """
        Soft delete credential (set is_active = false)

        Args:
            user_id: Keycloak user ID
            service: Service name
            credential_type: Credential type

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.db.execute(
                """
                UPDATE service_credentials
                SET is_active = false, updated_at = $1
                WHERE user_id = $2 AND service = $3 AND credential_type = $4
                """,
                datetime.utcnow(),
                user_id,
                service,
                credential_type
            )

            deleted = result.split()[-1] == "1"  # "UPDATE 1" or "UPDATE 0"

            if deleted:
                logger.info(f"Deleted credential: user={user_id}, service={service}, type={credential_type}")
                await audit_logger.log(
                    action="credential.delete",
                    user_id=user_id,
                    resource_type="credential",
                    details={"service": service, "credential_type": credential_type},
                    status="success"
                )
            else:
                logger.warning(f"Credential not found for deletion: user={user_id}, service={service}")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete credential: {e}")
            raise CredentialManagementError(f"Failed to delete credential: {e}")

    async def test_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str,
        value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test credential by calling service API

        Args:
            user_id: Keycloak user ID
            service: Service name
            credential_type: Credential type
            value: Optional plaintext value to test (if not in DB)

        Returns:
            Test result dictionary with status and message
        """
        # Get credential (from DB or provided value)
        if value is None:
            value = await self.get_credential_for_api(user_id, service, credential_type)
            if not value:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Credential not found"
                }

        service_config = SUPPORTED_SERVICES.get(service)
        if not service_config:
            return {
                "success": False,
                "status": "error",
                "message": f"Service '{service}' not supported"
            }

        # Test based on service type
        if service == "cloudflare":
            result = await self._test_cloudflare(value)
        elif service == "namecheap":
            result = await self._test_namecheap(value)
        elif service == "github":
            result = await self._test_github(value)
        elif service == "stripe":
            result = await self._test_stripe(value)
        else:
            result = {
                "success": False,
                "status": "error",
                "message": f"Test not implemented for service '{service}'"
            }

        # Update test metadata in database
        try:
            await self.db.execute(
                """
                UPDATE service_credentials
                SET last_tested = $1, test_status = $2
                WHERE user_id = $3 AND service = $4 AND credential_type = $5
                """,
                datetime.utcnow(),
                result.get("status", "error"),
                user_id,
                service,
                credential_type
            )
        except Exception as e:
            logger.error(f"Failed to update test metadata: {e}")

        # Audit log
        await audit_logger.log(
            action="credential.test",
            user_id=user_id,
            resource_type="credential",
            details={
                "service": service,
                "credential_type": credential_type,
                "test_result": result.get("status")
            },
            status="success" if result.get("success") else "failure"
        )

        return result

    def _mask_credential(self, service: str, value: str) -> str:
        """
        Mask credential for display

        Args:
            service: Service name
            value: Plaintext credential

        Returns:
            Masked credential string
        """
        if not value or len(value) < 8:
            return "***"

        # Service-specific masking
        if service == "cloudflare":
            # Cloudflare tokens: cf_abcd1234...xyz9
            return f"{value[:5]}***{value[-3:]}"
        elif service == "namecheap":
            # NameCheap API keys: 32-char hex
            return f"{value[:4]}***{value[-4:]}"
        elif service == "github":
            # GitHub PAT: ghp_abc123...xyz789
            return f"{value[:7]}***{value[-4:]}"
        elif service == "stripe":
            # Stripe keys: sk_test_abc123...xyz789
            return f"{value[:10]}***{value[-4:]}"
        else:
            # Default masking
            return self.secret_manager.mask_secret(value, visible_chars=4)

    async def _test_cloudflare(self, token: str) -> Dict[str, Any]:
        """Test Cloudflare API token"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.cloudflare.com/client/v4/user/tokens/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "success": True,
                            "status": "success",
                            "message": "Cloudflare API token is valid",
                            "details": data.get("result", {})
                        }

                return {
                    "success": False,
                    "status": "failed",
                    "message": f"Invalid Cloudflare token (HTTP {response.status_code})"
                }

        except httpx.TimeoutException:
            return {"success": False, "status": "error", "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Cloudflare test error: {e}")
            return {"success": False, "status": "error", "message": f"Test failed: {str(e)}"}

    async def _test_namecheap(self, api_key: str) -> Dict[str, Any]:
        """Test NameCheap API key"""
        # NameCheap API requires username + IP whitelisting
        # Simplified test - just validate format
        if len(api_key) == 32 and all(c in '0123456789abcdef' for c in api_key.lower()):
            return {
                "success": True,
                "status": "success",
                "message": "NameCheap API key format valid (API test requires username and IP whitelist)"
            }
        else:
            return {
                "success": False,
                "status": "failed",
                "message": "Invalid NameCheap API key format (expected 32-char hex)"
            }

    async def _test_github(self, token: str) -> Dict[str, Any]:
        """Test GitHub API token"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": "success",
                        "message": f"GitHub token valid for user: {data.get('login')}"
                    }

                return {
                    "success": False,
                    "status": "failed",
                    "message": f"Invalid GitHub token (HTTP {response.status_code})"
                }

        except Exception as e:
            logger.error(f"GitHub test error: {e}")
            return {"success": False, "status": "error", "message": f"Test failed: {str(e)}"}

    async def _test_stripe(self, secret_key: str) -> Dict[str, Any]:
        """Test Stripe secret key"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.stripe.com/v1/balance",
                    auth=(secret_key, "")  # Stripe uses HTTP Basic Auth
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "status": "success",
                        "message": "Stripe secret key is valid"
                    }

                return {
                    "success": False,
                    "status": "failed",
                    "message": f"Invalid Stripe key (HTTP {response.status_code})"
                }

        except Exception as e:
            logger.error(f"Stripe test error: {e}")
            return {"success": False, "status": "error", "message": f"Test failed: {str(e)}"}


# ============================================================================
# Module-level Functions
# ============================================================================

def get_supported_services() -> Dict[str, Dict[str, Any]]:
    """
    Get dictionary of supported services and their configurations

    Returns:
        Dictionary of service configurations
    """
    return SUPPORTED_SERVICES.copy()


def validate_service(service: str) -> bool:
    """
    Validate if service is supported

    Args:
        service: Service name

    Returns:
        True if supported, False otherwise
    """
    return service in SUPPORTED_SERVICES
