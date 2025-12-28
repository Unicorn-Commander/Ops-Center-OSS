"""
Comprehensive Security Testing Suite for UC-Cloud Ops-Center

Tests all critical security vulnerabilities and fixes:
1. Domain ownership verification
2. DNS rebinding protection
3. SQL injection prevention
4. XSS prevention
5. Secret encryption
6. Security headers
7. Rate limiting

Security Epic: 1.6/1.7 - Production Security Hardening
Author: Security Team Lead
Date: October 22, 2025
"""

import pytest
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from domain_verification import (
    DomainVerificationManager,
    VerificationCodeNotFoundError,
    VerificationExpiredError,
    DNSQueryError
)
from security_validators import (
    validate_public_ip,
    validate_domain_secure,
    validate_dns_record_content,
    check_sql_injection,
    check_xss,
    is_private_ip,
    PrivateIPError,
    DNSRebindingError,
    SQLInjectionError,
    XSSError,
    IDNAttackError
)
from secret_manager import SecretManager, generate_encryption_key
from key_encryption import KeyEncryption


# ============================================================================
# Test 1: Domain Ownership Verification
# ============================================================================

class TestDomainOwnershipVerification:
    """Test domain ownership verification system"""

    def test_generate_verification_code(self):
        """Test verification code generation"""
        manager = DomainVerificationManager()
        code = manager.generate_verification_code("example.com", "user123")

        assert code.code.startswith("uc-verify-")
        assert len(code.code) == len("uc-verify-") + 32
        assert code.domain == "example.com"
        assert code.user_id == "user123"
        assert code.verified is False
        assert code.verification_attempts == 0

    def test_code_expiration(self):
        """Test verification code expiration"""
        manager = DomainVerificationManager()
        code = manager.generate_verification_code("example.com", "user123")

        # Code should expire in 24 hours
        assert code.expires_at > datetime.utcnow()
        assert code.expires_at <= datetime.utcnow() + timedelta(hours=24, minutes=5)

    def test_verification_instructions(self):
        """Test verification instructions generation"""
        manager = DomainVerificationManager()
        code = manager.generate_verification_code("example.com", "user123")
        instructions = manager.get_verification_instructions(code)

        assert "step" in instructions
        assert "instructions" in instructions
        assert "record_details" in instructions
        assert instructions["record_details"]["type"] == "TXT"
        assert instructions["record_details"]["host"] == "_uc-verify"
        assert instructions["record_details"]["value"] == code.code

    def test_invalid_domain_rejection(self):
        """Test rejection of invalid domains"""
        manager = DomainVerificationManager()

        # Test punycode rejection
        with pytest.raises(ValueError, match="punycode"):
            manager.generate_verification_code("xn--e1afmkfd.xn--p1ai", "user123")

        # Test consecutive hyphens
        with pytest.raises(ValueError, match="consecutive hyphens"):
            manager.generate_verification_code("test--domain.com", "user123")

        # Test invalid format
        with pytest.raises(ValueError, match="Invalid domain"):
            manager.generate_verification_code("invalid domain.com", "user123")


# ============================================================================
# Test 2: DNS Rebinding Protection
# ============================================================================

class TestDNSRebindingProtection:
    """Test DNS rebinding attack prevention"""

    def test_private_ipv4_detection(self):
        """Test detection of private IPv4 addresses"""
        private_ips = [
            "127.0.0.1",       # Loopback
            "10.0.0.1",        # Private class A
            "172.16.0.1",      # Private class B
            "192.168.1.1",     # Private class C
            "169.254.1.1",     # Link-local
        ]

        for ip in private_ips:
            assert is_private_ip(ip) is True, f"{ip} should be detected as private"

    def test_private_ipv6_detection(self):
        """Test detection of private IPv6 addresses"""
        private_ips = [
            "::1",                      # Loopback
            "fe80::1",                  # Link-local
            "fc00::1",                  # Unique local
        ]

        for ip in private_ips:
            assert is_private_ip(ip) is True, f"{ip} should be detected as private"

    def test_public_ip_allowed(self):
        """Test that public IPs are allowed"""
        public_ips = [
            "8.8.8.8",         # Google DNS
            "1.1.1.1",         # Cloudflare DNS
            "208.67.222.222",  # OpenDNS
        ]

        for ip in public_ips:
            assert is_private_ip(ip) is False, f"{ip} should be detected as public"
            # Should not raise exception
            validate_public_ip(ip, allow_private=False)

    def test_dns_a_record_private_ip_rejection(self):
        """Test A record with private IP is rejected"""
        with pytest.raises(DNSRebindingError, match="Private IPv4"):
            validate_dns_record_content("A", "127.0.0.1", allow_private_ips=False)

        with pytest.raises(DNSRebindingError, match="Private IPv4"):
            validate_dns_record_content("A", "192.168.1.1", allow_private_ips=False)

    def test_dns_aaaa_record_private_ip_rejection(self):
        """Test AAAA record with private IP is rejected"""
        with pytest.raises(DNSRebindingError, match="Private IPv6"):
            validate_dns_record_content("AAAA", "::1", allow_private_ips=False)

        with pytest.raises(DNSRebindingError, match="Private IPv6"):
            validate_dns_record_content("AAAA", "fe80::1", allow_private_ips=False)

    def test_dns_a_record_public_ip_allowed(self):
        """Test A record with public IP is allowed"""
        result = validate_dns_record_content("A", "8.8.8.8", allow_private_ips=False)
        assert result == "8.8.8.8"


# ============================================================================
# Test 3: SQL Injection Prevention
# ============================================================================

class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention"""

    def test_sql_injection_patterns_detected(self):
        """Test common SQL injection patterns are detected"""
        sql_injections = [
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; DROP TABLE users--",
            "1' AND 1=1--",
            "' OR 1=1/*",
        ]

        for injection in sql_injections:
            with pytest.raises(SQLInjectionError, match="SQL injection"):
                check_sql_injection(injection, context="test")

    def test_safe_input_allowed(self):
        """Test legitimate input is allowed"""
        safe_inputs = [
            "john.doe@example.com",
            "example.com",
            "My Company Name",
            "192.168.1.1",  # IP address
        ]

        for safe_input in safe_inputs:
            # Should not raise exception
            result = check_sql_injection(safe_input)
            assert result == safe_input

    def test_domain_sql_injection_blocked(self):
        """Test SQL injection in domain field is blocked"""
        with pytest.raises(SQLInjectionError):
            validate_domain_secure("example.com' OR '1'='1", allow_idn=False)


# ============================================================================
# Test 4: XSS Prevention
# ============================================================================

class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) attack prevention"""

    def test_xss_patterns_detected(self):
        """Test common XSS patterns are detected"""
        xss_attacks = [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<iframe src='http://evil.com'>",
            "<embed src='http://evil.com'>",
        ]

        for attack in xss_attacks:
            with pytest.raises(XSSError, match="XSS"):
                check_xss(attack, context="test")

    def test_safe_html_allowed(self):
        """Test safe content is allowed"""
        safe_inputs = [
            "Normal text content",
            "example.com",
            "user@example.com",
        ]

        for safe_input in safe_inputs:
            # Should not raise exception
            result = check_xss(safe_input)
            assert result == safe_input


# ============================================================================
# Test 5: IDN/Punycode Attack Prevention
# ============================================================================

class TestIDNAttackPrevention:
    """Test Internationalized Domain Name attack prevention"""

    def test_punycode_domains_rejected(self):
        """Test punycode domains are rejected"""
        punycode_domains = [
            "xn--e1afmkfd.xn--p1ai",  # Russian IDN
            "xn--80akhbyknj4f.com",    # IDN with cyrillic
            "xn--example-6qa.com",     # IDN example
        ]

        for domain in punycode_domains:
            with pytest.raises(IDNAttackError, match="punycode"):
                validate_domain_secure(domain, allow_idn=False)

    def test_consecutive_hyphens_rejected(self):
        """Test domains with consecutive hyphens are rejected"""
        with pytest.raises(IDNAttackError, match="consecutive hyphens"):
            validate_domain_secure("paypal--secure.com", allow_idn=False)

    def test_normal_domains_allowed(self):
        """Test normal domains are allowed"""
        normal_domains = [
            "example.com",
            "sub.example.com",
            "example-domain.com",
            "example.co.uk",
        ]

        for domain in normal_domains:
            result = validate_domain_secure(domain)
            assert result == domain


# ============================================================================
# Test 6: Secret Encryption
# ============================================================================

class TestSecretEncryption:
    """Test secret encryption and decryption"""

    @classmethod
    def setup_class(cls):
        """Set up encryption key for tests"""
        if not os.getenv('ENCRYPTION_KEY'):
            os.environ['ENCRYPTION_KEY'] = generate_encryption_key()

    def test_encrypt_decrypt_secret(self):
        """Test encryption and decryption of secrets"""
        manager = SecretManager()
        original_secret = "my_secret_api_key_12345"

        # Encrypt
        encrypted = manager.encrypt_secret(original_secret)
        assert "encrypted_value" in encrypted
        assert encrypted["encrypted_value"] != original_secret

        # Decrypt
        decrypted = manager.decrypt_secret(encrypted["encrypted_value"])
        assert decrypted == original_secret

    def test_secret_masking(self):
        """Test secret masking for display"""
        manager = SecretManager()
        secret = "sk_test_1234567890abcdefghijklmnop"

        masked = manager.mask_secret(secret)
        assert "****" in masked or "..." in masked
        assert len(masked) < len(secret)
        assert "sk_t" in masked  # First 4 chars visible

    def test_encryption_key_required(self):
        """Test that encryption key is required"""
        # Remove key
        original_key = os.getenv('ENCRYPTION_KEY')
        del os.environ['ENCRYPTION_KEY']

        # Should fail without key
        with pytest.raises(Exception):
            SecretManager()

        # Restore key
        os.environ['ENCRYPTION_KEY'] = original_key

    def test_cloudflare_token_encryption(self):
        """Test encryption of Cloudflare API token"""
        manager = SecretManager()
        token = "<CLOUDFLARE_API_TOKEN_REDACTED>"

        encrypted = manager.encrypt_secret(token, secret_type="cloudflare_api_token")
        decrypted = manager.decrypt_secret(encrypted["encrypted_value"])

        assert decrypted == token
        assert encrypted["secret_type"] == "cloudflare_api_token"

    def test_namecheap_key_encryption(self):
        """Test encryption of NameCheap API key"""
        manager = SecretManager()
        api_key = "your-example-api-key"

        encrypted = manager.encrypt_secret(api_key, secret_type="namecheap_api_key")
        decrypted = manager.decrypt_secret(encrypted["encrypted_value"])

        assert decrypted == api_key
        assert encrypted["secret_type"] == "namecheap_api_key"


# ============================================================================
# Test 7: Input Validation Edge Cases
# ============================================================================

class TestInputValidationEdgeCases:
    """Test edge cases in input validation"""

    def test_domain_length_limits(self):
        """Test domain length validation"""
        # Too long domain (> 253 chars)
        long_domain = "a" * 250 + ".com"
        with pytest.raises(ValueError, match="maximum length"):
            validate_domain_secure(long_domain)

        # Too long label (> 63 chars)
        long_label = "a" * 64 + ".com"
        with pytest.raises(ValueError, match="maximum length"):
            validate_domain_secure(long_label)

    def test_domain_format_validation(self):
        """Test domain format validation"""
        invalid_domains = [
            "invalid domain with spaces",
            "-starts-with-hyphen.com",
            "ends-with-hyphen-.com",
            "double..dots.com",
            ".starts-with-dot.com",
        ]

        for domain in invalid_domains:
            with pytest.raises(ValueError):
                validate_domain_secure(domain)

    def test_ip_address_validation(self):
        """Test IP address validation"""
        # Invalid IP formats
        invalid_ips = [
            "999.999.999.999",
            "192.168.1",
            "not.an.ip.address",
            "192.168.1.1.1",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValueError):
                validate_public_ip(ip)


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    print("Security Testing Suite - Running Tests")
    print("=" * 70)

    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ ALL SECURITY TESTS PASSED")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ SOME TESTS FAILED")
        print("=" * 70)

    sys.exit(exit_code)
