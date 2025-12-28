"""
Domain Ownership Verification Module for UC-Cloud Ops-Center

This module implements domain ownership verification via DNS TXT records to prevent
unauthorized domain migrations. Users must prove they control a domain before
migrating it to Cloudflare.

Security Epic: 1.7 Critical Issue #2 - Domain Ownership Verification
Author: Security Team Lead
Date: October 22, 2025
"""

import dns.resolver
import logging
import secrets
import string
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class DomainVerificationError(Exception):
    """Base exception for domain verification failures"""
    pass


class VerificationCodeNotFoundError(DomainVerificationError):
    """Verification TXT record not found in DNS"""
    pass


class VerificationExpiredError(DomainVerificationError):
    """Verification code has expired"""
    pass


class DNSQueryError(DomainVerificationError):
    """DNS query failed"""
    pass


# ============================================================================
# Pydantic Models
# ============================================================================

class VerificationRequest(BaseModel):
    """Domain verification request model"""
    domain: str = Field(..., min_length=3, max_length=253)
    user_id: str = Field(..., min_length=1)

    @field_validator('domain')
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format (RFC 1035)"""
        v = v.lower().strip()

        # RFC 1035 compliant pattern
        pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain format: {v}")

        # Reject internationalized domain names (IDN) with punycode
        if 'xn--' in v:
            raise ValueError("Internationalized domain names (punycode) are not supported for security reasons")

        # Reject domains with consecutive hyphens (potential homograph attack)
        if '--' in v:
            raise ValueError("Domains with consecutive hyphens are not allowed")

        return v


class VerificationCode(BaseModel):
    """Verification code model"""
    code: str
    domain: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    verified: bool = False
    verification_attempts: int = 0


# ============================================================================
# Domain Verification Manager
# ============================================================================

class DomainVerificationManager:
    """
    Manages domain ownership verification via DNS TXT records

    Workflow:
    1. User initiates migration for domain
    2. Generate unique verification code: uc-verify-{random_32_chars}
    3. User must add TXT record to domain: _uc-verify.domain.com
    4. System queries DNS for TXT record
    5. If verification code matches, domain ownership is proven
    6. Migration can proceed

    Security Features:
    - Cryptographically secure random codes (32 characters)
    - Time-limited verification (24-hour expiration)
    - Rate limiting on verification attempts (max 10 per code)
    - DNS query timeout protection
    - Multiple DNS resolver fallback (Google DNS + Cloudflare DNS)
    """

    VERIFICATION_PREFIX = "uc-verify-"
    VERIFICATION_SUBDOMAIN = "_uc-verify"
    CODE_LENGTH = 32
    EXPIRATION_HOURS = 24
    MAX_VERIFICATION_ATTEMPTS = 10

    # DNS resolvers for verification (fallback strategy)
    DNS_RESOLVERS = [
        "8.8.8.8",      # Google DNS (primary)
        "8.8.4.4",      # Google DNS (secondary)
        "1.1.1.1",      # Cloudflare DNS (primary)
        "1.0.0.1"       # Cloudflare DNS (secondary)
    ]

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialize verification manager

        Args:
            storage_backend: Optional storage backend (Redis, PostgreSQL, etc.)
                           If None, uses in-memory storage (NOT for production)
        """
        self.storage = storage_backend or {}  # In-memory fallback
        logger.info("DomainVerificationManager initialized")

    def generate_verification_code(
        self,
        domain: str,
        user_id: str
    ) -> VerificationCode:
        """
        Generate a new verification code for domain

        Args:
            domain: Domain to verify ownership
            user_id: User requesting verification

        Returns:
            VerificationCode object with code and expiration
        """
        # Validate domain
        validated = VerificationRequest(domain=domain, user_id=user_id)

        # Generate cryptographically secure random code
        # Using secrets module (not random) for security
        alphabet = string.ascii_lowercase + string.digits
        random_suffix = ''.join(secrets.choice(alphabet) for _ in range(self.CODE_LENGTH))
        verification_code = f"{self.VERIFICATION_PREFIX}{random_suffix}"

        # Set expiration
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.EXPIRATION_HOURS)

        # Create verification record
        code_obj = VerificationCode(
            code=verification_code,
            domain=validated.domain,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            verified=False,
            verification_attempts=0
        )

        # Store verification code (key: domain:user_id)
        storage_key = f"{validated.domain}:{user_id}"
        self.storage[storage_key] = code_obj.model_dump()

        logger.info(
            f"Verification code generated for {validated.domain} "
            f"(user: {user_id}, expires: {expires_at.isoformat()})"
        )

        return code_obj

    def get_verification_instructions(
        self,
        verification_code: VerificationCode
    ) -> Dict[str, Any]:
        """
        Get DNS setup instructions for user

        Args:
            verification_code: Generated verification code

        Returns:
            Dictionary with setup instructions
        """
        txt_record_name = f"{self.VERIFICATION_SUBDOMAIN}.{verification_code.domain}"

        return {
            "step": 1,
            "title": "Add DNS TXT Record",
            "instructions": [
                f"1. Login to your domain registrar (NameCheap, GoDaddy, etc.)",
                f"2. Navigate to DNS settings for {verification_code.domain}",
                f"3. Add a new TXT record with these values:",
                f"   - Host/Name: {self.VERIFICATION_SUBDOMAIN}",
                f"   - Type: TXT",
                f"   - Value: {verification_code.code}",
                f"   - TTL: 300 (5 minutes) or automatic",
                f"4. Save changes and wait 5-10 minutes for DNS propagation",
                f"5. Click 'Verify Ownership' button below"
            ],
            "record_details": {
                "type": "TXT",
                "host": self.VERIFICATION_SUBDOMAIN,
                "value": verification_code.code,
                "ttl": 300,
                "full_name": txt_record_name
            },
            "verification_code": verification_code.code,
            "expires_at": verification_code.expires_at.isoformat(),
            "time_remaining": str(verification_code.expires_at - datetime.utcnow())
        }

    def verify_domain_ownership(
        self,
        domain: str,
        user_id: str,
        expected_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify domain ownership by checking DNS TXT record

        Args:
            domain: Domain to verify
            user_id: User ID
            expected_code: Expected verification code (optional, fetched from storage)

        Returns:
            Verification result dictionary

        Raises:
            VerificationCodeNotFoundError: TXT record not found
            VerificationExpiredError: Verification code expired
            DNSQueryError: DNS query failed
        """
        # Get stored verification code
        storage_key = f"{domain}:{user_id}"
        stored_data = self.storage.get(storage_key)

        if not stored_data:
            raise VerificationCodeNotFoundError(
                f"No verification code found for {domain}. Generate a new code first."
            )

        code_obj = VerificationCode(**stored_data)

        # Check expiration
        if datetime.utcnow() > code_obj.expires_at:
            raise VerificationExpiredError(
                f"Verification code expired on {code_obj.expires_at.isoformat()}. Generate a new code."
            )

        # Check max attempts
        if code_obj.verification_attempts >= self.MAX_VERIFICATION_ATTEMPTS:
            raise DomainVerificationError(
                f"Maximum verification attempts ({self.MAX_VERIFICATION_ATTEMPTS}) exceeded. Generate a new code."
            )

        # Increment attempt counter
        code_obj.verification_attempts += 1
        self.storage[storage_key] = code_obj.model_dump()

        # Query DNS for TXT record
        txt_record_name = f"{self.VERIFICATION_SUBDOMAIN}.{domain}"

        logger.info(f"Querying DNS for {txt_record_name} (attempt {code_obj.verification_attempts})")

        try:
            # Query TXT records using multiple resolvers (fallback strategy)
            txt_records = self._query_txt_records_with_fallback(txt_record_name)

            if not txt_records:
                return {
                    "verified": False,
                    "error": "TXT record not found",
                    "message": f"DNS TXT record '{txt_record_name}' not found. Ensure record is added and DNS has propagated (5-10 minutes).",
                    "attempts_remaining": self.MAX_VERIFICATION_ATTEMPTS - code_obj.verification_attempts
                }

            # Check if any TXT record matches verification code
            verification_code = expected_code or code_obj.code

            if verification_code in txt_records:
                # SUCCESS: Domain ownership verified
                code_obj.verified = True
                self.storage[storage_key] = code_obj.model_dump()

                logger.info(f"✅ Domain ownership verified for {domain} (user: {user_id})")

                return {
                    "verified": True,
                    "domain": domain,
                    "verified_at": datetime.utcnow().isoformat(),
                    "message": f"Domain ownership verified successfully! You can now proceed with migration.",
                    "verification_code": verification_code
                }
            else:
                # TXT record exists but doesn't match
                return {
                    "verified": False,
                    "error": "Verification code mismatch",
                    "message": f"TXT record found but verification code doesn't match. Found: {txt_records[:3]}. Expected: {verification_code}",
                    "attempts_remaining": self.MAX_VERIFICATION_ATTEMPTS - code_obj.verification_attempts
                }

        except Exception as e:
            logger.error(f"DNS query failed for {txt_record_name}: {e}")
            raise DNSQueryError(f"Failed to query DNS: {e}")

    def _query_txt_records_with_fallback(
        self,
        domain: str,
        timeout: int = 10
    ) -> List[str]:
        """
        Query TXT records using multiple DNS resolvers with fallback

        Args:
            domain: Domain to query
            timeout: DNS query timeout in seconds

        Returns:
            List of TXT record values

        Raises:
            DNSQueryError: All DNS resolvers failed
        """
        txt_records = []
        last_error = None

        for resolver_ip in self.DNS_RESOLVERS:
            try:
                # Create custom resolver
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [resolver_ip]
                resolver.timeout = timeout
                resolver.lifetime = timeout

                # Query TXT records
                answers = resolver.resolve(domain, 'TXT')

                for rdata in answers:
                    # TXT records are returned as quoted strings, need to decode
                    for txt_string in rdata.strings:
                        decoded = txt_string.decode('utf-8')
                        txt_records.append(decoded)

                # Success - return results
                if txt_records:
                    logger.info(f"DNS query successful via {resolver_ip}: found {len(txt_records)} TXT records")
                    return txt_records

            except dns.resolver.NXDOMAIN:
                logger.warning(f"Domain {domain} does not exist (NXDOMAIN) via {resolver_ip}")
                last_error = f"Domain does not exist"

            except dns.resolver.NoAnswer:
                logger.warning(f"No TXT records found for {domain} via {resolver_ip}")
                last_error = f"No TXT records found"

            except dns.resolver.Timeout:
                logger.warning(f"DNS query timeout for {domain} via {resolver_ip}")
                last_error = f"DNS query timeout"

            except Exception as e:
                logger.warning(f"DNS query failed for {domain} via {resolver_ip}: {e}")
                last_error = str(e)

        # All resolvers failed
        if last_error:
            raise DNSQueryError(f"All DNS resolvers failed. Last error: {last_error}")

        return []

    def is_verified(self, domain: str, user_id: str) -> bool:
        """
        Check if domain has been verified

        Args:
            domain: Domain to check
            user_id: User ID

        Returns:
            True if verified and not expired
        """
        storage_key = f"{domain}:{user_id}"
        stored_data = self.storage.get(storage_key)

        if not stored_data:
            return False

        code_obj = VerificationCode(**stored_data)

        # Check if verified and not expired
        if code_obj.verified and datetime.utcnow() <= code_obj.expires_at:
            return True

        return False

    def cleanup_expired_codes(self) -> int:
        """
        Remove expired verification codes from storage

        Returns:
            Number of codes removed
        """
        now = datetime.utcnow()
        expired_keys = []

        for key, data in self.storage.items():
            code_obj = VerificationCode(**data)
            if now > code_obj.expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            del self.storage[key]

        logger.info(f"Cleaned up {len(expired_keys)} expired verification codes")
        return len(expired_keys)


# ============================================================================
# Module-level Functions
# ============================================================================

def create_verification_manager(storage_backend: Optional[Any] = None) -> DomainVerificationManager:
    """
    Factory function to create DomainVerificationManager

    Args:
        storage_backend: Storage backend (Redis recommended for production)

    Returns:
        DomainVerificationManager instance
    """
    return DomainVerificationManager(storage_backend=storage_backend)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Domain Verification Manager - Test Mode")
    print("=" * 70)

    # Initialize manager
    manager = DomainVerificationManager()

    # Example: Generate verification code
    print("\n1. Generating verification code:")
    code = manager.generate_verification_code(
        domain="example.com",
        user_id="user123"
    )
    print(f"   Code: {code.code}")
    print(f"   Expires: {code.expires_at.isoformat()}")

    # Example: Get setup instructions
    print("\n2. Setup instructions:")
    instructions = manager.get_verification_instructions(code)
    for instruction in instructions["instructions"]:
        print(f"   {instruction}")

    # Example: Test invalid domain (punycode)
    print("\n3. Testing punycode rejection:")
    try:
        manager.generate_verification_code(
            domain="xn--e1afmkfd.xn--p1ai",  # Russian IDN
            user_id="user123"
        )
    except ValueError as e:
        print(f"   ✅ Correctly rejected: {e}")

    print("\n✅ Module loaded successfully")
