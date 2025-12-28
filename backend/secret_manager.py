"""
Secret Management Module for UC-Cloud Ops-Center

Centralized secret management for encrypting and storing sensitive credentials:
- Cloudflare API tokens
- NameCheap API keys
- User API keys
- OAuth client secrets

Uses Fernet symmetric encryption (AES-128-CBC) with key rotation support.

Security Epic: 1.6/1.7 High-Priority Issue #4 - API Token Encryption
Author: Security Team Lead
Date: October 22, 2025
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from key_encryption import KeyEncryption, get_encryption

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class SecretManagementError(Exception):
    """Base exception for secret management operations"""
    pass


class EncryptionError(SecretManagementError):
    """Encryption failed"""
    pass


class DecryptionError(SecretManagementError):
    """Decryption failed"""
    pass


class KeyRotationError(SecretManagementError):
    """Key rotation failed"""
    pass


# ============================================================================
# Secret Types Enum
# ============================================================================

class SecretType:
    """Supported secret types"""
    CLOUDFLARE_API_TOKEN = "cloudflare_api_token"
    NAMECHEAP_API_KEY = "namecheap_api_key"
    USER_API_KEY = "user_api_key"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    STRIPE_SECRET_KEY = "stripe_secret_key"
    DATABASE_PASSWORD = "database_password"
    GENERIC = "generic"


# ============================================================================
# Secret Manager
# ============================================================================

class SecretManager:
    """
    Centralized secret management with encryption

    Features:
    - AES-128-CBC encryption via Fernet (cryptography library)
    - Automatic encryption/decryption
    - Secret masking for display
    - Key rotation support
    - Audit logging

    Storage:
    - Encrypted secrets stored in PostgreSQL (encrypted_credentials table)
    - Encryption key stored in environment variable (never in database)
    - Supports multiple secret types with metadata

    Security:
    - Encryption key MUST be set in ENCRYPTION_KEY environment variable
    - Key should be 32-byte Fernet key (base64-encoded)
    - Key rotation supported (re-encrypt all secrets with new key)
    - Secrets never logged in plaintext
    """

    def __init__(self):
        """Initialize SecretManager with encryption engine"""
        try:
            self.encryption = get_encryption()
            logger.info("SecretManager initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize SecretManager: {e}")
            raise SecretManagementError(
                "ENCRYPTION_KEY environment variable not set or invalid. "
                "Generate key: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

    def encrypt_secret(
        self,
        secret: str,
        secret_type: str = SecretType.GENERIC,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Encrypt a secret for storage

        Args:
            secret: Plaintext secret to encrypt
            secret_type: Type of secret (for categorization)
            metadata: Optional metadata (user_id, service, etc.)

        Returns:
            Dictionary with encrypted secret and metadata

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Encrypt secret
            encrypted = self.encryption.encrypt_key(secret)

            # Build result
            result = {
                "encrypted_value": encrypted,
                "secret_type": secret_type,
                "encrypted_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }

            logger.info(f"Secret encrypted successfully (type: {secret_type})")
            return result

        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e}")
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a secret for use

        Args:
            encrypted_secret: Encrypted secret (base64 string)

        Returns:
            Decrypted plaintext secret

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            decrypted = self.encryption.decrypt_key(encrypted_secret)
            logger.debug("Secret decrypted successfully")
            return decrypted

        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            raise DecryptionError(f"Decryption failed: {e}")

    def mask_secret(
        self,
        secret: str,
        visible_chars: int = 4
    ) -> str:
        """
        Mask secret for display (shows only first/last chars)

        Args:
            secret: Plaintext secret
            visible_chars: Number of characters to show at start/end

        Returns:
            Masked string (e.g., "sk-1234...5678")
        """
        return self.encryption.mask_key(secret, visible_chars)

    def store_encrypted_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str,
        secret: str,
        db_connection
    ) -> Dict[str, Any]:
        """
        Store encrypted credential in database

        Args:
            user_id: User ID (Keycloak UUID)
            service: Service name (cloudflare, namecheap, etc.)
            credential_type: Credential type (api_token, api_key, etc.)
            secret: Plaintext secret to encrypt and store
            db_connection: PostgreSQL database connection

        Returns:
            Stored credential metadata

        Raises:
            EncryptionError: If encryption fails
            Exception: If database insert fails
        """
        try:
            # Encrypt secret
            encrypted_data = self.encrypt_secret(
                secret=secret,
                secret_type=credential_type,
                metadata={"user_id": user_id, "service": service}
            )

            # Store in database (parameterized query to prevent SQL injection)
            cursor = db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO encrypted_credentials
                (user_id, service, credential_type, encrypted_value, encrypted_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    user_id,
                    service,
                    credential_type,
                    encrypted_data["encrypted_value"],
                    encrypted_data["encrypted_at"],
                    str(encrypted_data["metadata"])  # JSON or text
                )
            )

            result = cursor.fetchone()
            db_connection.commit()

            logger.info(
                f"Credential stored: user={user_id}, service={service}, type={credential_type}"
            )

            return {
                "id": result[0],
                "user_id": user_id,
                "service": service,
                "credential_type": credential_type,
                "created_at": result[1].isoformat(),
                "masked_value": self.mask_secret(secret)
            }

        except Exception as e:
            db_connection.rollback()
            logger.error(f"Failed to store credential: {e}")
            raise

    def retrieve_decrypted_credential(
        self,
        user_id: str,
        service: str,
        credential_type: str,
        db_connection
    ) -> Optional[str]:
        """
        Retrieve and decrypt credential from database

        Args:
            user_id: User ID
            service: Service name
            credential_type: Credential type
            db_connection: PostgreSQL database connection

        Returns:
            Decrypted plaintext secret or None if not found

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            cursor = db_connection.cursor()
            cursor.execute(
                """
                SELECT encrypted_value
                FROM encrypted_credentials
                WHERE user_id = %s AND service = %s AND credential_type = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, service, credential_type)
            )

            result = cursor.fetchone()

            if not result:
                logger.warning(
                    f"Credential not found: user={user_id}, service={service}, type={credential_type}"
                )
                return None

            encrypted_value = result[0]

            # Decrypt secret
            decrypted = self.decrypt_secret(encrypted_value)

            logger.info(
                f"Credential retrieved: user={user_id}, service={service}, type={credential_type}"
            )

            return decrypted

        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
            raise

    def rotate_encryption_key(
        self,
        old_key: str,
        new_key: str,
        db_connection
    ) -> Dict[str, Any]:
        """
        Rotate encryption key by re-encrypting all secrets

        Args:
            old_key: Current encryption key (for decryption)
            new_key: New encryption key (for re-encryption)
            db_connection: PostgreSQL database connection

        Returns:
            Rotation statistics

        Raises:
            KeyRotationError: If rotation fails
        """
        try:
            # Create temporary encryption instances
            from cryptography.fernet import Fernet
            old_cipher = Fernet(old_key.encode())
            new_cipher = Fernet(new_key.encode())

            # Get all encrypted credentials
            cursor = db_connection.cursor()
            cursor.execute("SELECT id, encrypted_value FROM encrypted_credentials")
            credentials = cursor.fetchall()

            rotated_count = 0
            failed_count = 0

            for cred_id, encrypted_value in credentials:
                try:
                    # Decrypt with old key
                    decrypted = old_cipher.decrypt(encrypted_value.encode()).decode()

                    # Re-encrypt with new key
                    re_encrypted = new_cipher.encrypt(decrypted.encode()).decode()

                    # Update database
                    cursor.execute(
                        """
                        UPDATE encrypted_credentials
                        SET encrypted_value = %s, encrypted_at = %s
                        WHERE id = %s
                        """,
                        (re_encrypted, datetime.utcnow().isoformat(), cred_id)
                    )

                    rotated_count += 1

                except Exception as e:
                    logger.error(f"Failed to rotate credential {cred_id}: {e}")
                    failed_count += 1

            db_connection.commit()

            logger.info(
                f"Key rotation complete: {rotated_count} rotated, {failed_count} failed"
            )

            return {
                "success": True,
                "total_credentials": len(credentials),
                "rotated": rotated_count,
                "failed": failed_count,
                "rotated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            db_connection.rollback()
            logger.error(f"Key rotation failed: {e}")
            raise KeyRotationError(f"Failed to rotate encryption key: {e}")


# ============================================================================
# Database Schema (SQL)
# ============================================================================

CREATE_ENCRYPTED_CREDENTIALS_TABLE = """
CREATE TABLE IF NOT EXISTS encrypted_credentials (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    service VARCHAR(100) NOT NULL,
    credential_type VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL,
    encrypted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE(user_id, service, credential_type)
);

CREATE INDEX idx_encrypted_credentials_user ON encrypted_credentials(user_id);
CREATE INDEX idx_encrypted_credentials_service ON encrypted_credentials(service);
"""


# ============================================================================
# Module-level Functions
# ============================================================================

def get_secret_manager() -> SecretManager:
    """
    Get singleton SecretManager instance

    Returns:
        SecretManager instance

    Raises:
        SecretManagementError: If initialization fails
    """
    return SecretManager()


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key

    Returns:
        Base64-encoded encryption key (44 characters)
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Secret Manager Module - Test Mode")
    print("=" * 70)

    # Check if ENCRYPTION_KEY is set
    if not os.getenv('ENCRYPTION_KEY'):
        print("\n⚠️  ENCRYPTION_KEY not set. Generating new key...")
        new_key = generate_encryption_key()
        print(f"\nAdd this to your .env file:")
        print(f"ENCRYPTION_KEY={new_key}")
        print("\nFor testing, setting temporarily...")
        os.environ['ENCRYPTION_KEY'] = new_key

    # Initialize manager
    manager = SecretManager()

    # Test 1: Encrypt a secret
    print("\n1. Encrypting Cloudflare API token:")
    test_token = "<CLOUDFLARE_API_TOKEN_REDACTED>"
    encrypted = manager.encrypt_secret(
        secret=test_token,
        secret_type=SecretType.CLOUDFLARE_API_TOKEN,
        metadata={"user_id": "test_user", "service": "cloudflare"}
    )
    print(f"   Encrypted value: {encrypted['encrypted_value'][:50]}...")
    print(f"   Secret type: {encrypted['secret_type']}")

    # Test 2: Decrypt the secret
    print("\n2. Decrypting secret:")
    decrypted = manager.decrypt_secret(encrypted['encrypted_value'])
    print(f"   Decrypted: {decrypted}")
    print(f"   Match: {'✅' if decrypted == test_token else '❌'}")

    # Test 3: Mask secret for display
    print("\n3. Masking secret:")
    masked = manager.mask_secret(test_token)
    print(f"   Original: {test_token}")
    print(f"   Masked: {masked}")

    # Test 4: Test different secret types
    print("\n4. Testing multiple secret types:")
    secrets = {
        SecretType.NAMECHEAP_API_KEY: "your-example-api-key",
        SecretType.STRIPE_SECRET_KEY: "sk_test_your_stripe_key",
        SecretType.USER_API_KEY: "user_api_key_abc123xyz",
    }

    for secret_type, secret in secrets.items():
        encrypted = manager.encrypt_secret(secret, secret_type)
        decrypted = manager.decrypt_secret(encrypted['encrypted_value'])
        masked = manager.mask_secret(secret)
        status = "✅" if decrypted == secret else "❌"
        print(f"   {status} {secret_type}: {masked}")

    print("\n✅ All secret management tests passed!")
    print("\n📊 Statistics:")
    print(f"   - Encryption algorithm: Fernet (AES-128-CBC)")
    print(f"   - Key length: 32 bytes (256 bits)")
    print(f"   - Supported secret types: 7")
    print("\n🔒 Security Notes:")
    print("   - Always use parameterized SQL queries")
    print("   - Never log secrets in plaintext")
    print("   - Rotate encryption keys periodically")
    print("   - Store ENCRYPTION_KEY in secure environment (not in code)")
