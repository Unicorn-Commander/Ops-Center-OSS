"""
API Key Encryption Utility
Encrypts and decrypts user API keys using Fernet symmetric encryption
"""
import os
from cryptography.fernet import Fernet
from typing import Optional


class KeyEncryption:
    """Handles encryption and decryption of API keys"""

    def __init__(self):
        """Initialize encryption with key from environment"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

        try:
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")

    def encrypt_key(self, api_key: str) -> str:
        """
        Encrypt an API key

        Args:
            api_key: Plain text API key

        Returns:
            Encrypted API key as base64 string
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    def decrypt_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key

        Args:
            encrypted_key: Base64 encrypted API key

        Returns:
            Decrypted plain text API key
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")

        try:
            decrypted = self.cipher.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def mask_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for display

        Args:
            api_key: Plain text API key
            visible_chars: Number of characters to show at start and end

        Returns:
            Masked API key (e.g., "sk-1234...5678")
        """
        if not api_key or len(api_key) < visible_chars * 2:
            return "****"

        return f"{api_key[:visible_chars]}...{api_key[-visible_chars:]}"


# Singleton instance
_encryption_instance: Optional[KeyEncryption] = None


def get_encryption() -> KeyEncryption:
    """Get or create singleton encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = KeyEncryption()
    return _encryption_instance
