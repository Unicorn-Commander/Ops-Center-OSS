"""
Security Validators Module for UC-Cloud Ops-Center

This module provides comprehensive input validation with security hardening to prevent:
- DNS rebinding attacks (private IP ranges)
- SQL injection attacks
- Cross-Site Scripting (XSS)
- Internationalized Domain Name (IDN) attacks
- Punycode homograph attacks

Security Epic: 1.7 Critical Issue #3 - DNS Rebinding + High-Priority Issues #5-8
Author: Security Team Lead
Date: October 22, 2025
"""

import ipaddress
import re
import html
from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# Security Exceptions
# ============================================================================

class SecurityValidationError(Exception):
    """Base exception for security validation failures"""
    pass


class DNSRebindingError(SecurityValidationError):
    """DNS rebinding attack detected"""
    pass


class PrivateIPError(SecurityValidationError):
    """Private IP address detected"""
    pass


class SQLInjectionError(SecurityValidationError):
    """Potential SQL injection detected"""
    pass


class XSSError(SecurityValidationError):
    """Potential XSS attack detected"""
    pass


class IDNAttackError(SecurityValidationError):
    """Internationalized Domain Name attack detected"""
    pass


# ============================================================================
# Private IP Ranges (RFC 1918, RFC 4193, RFC 3927)
# ============================================================================

PRIVATE_IPV4_RANGES = [
    ipaddress.IPv4Network('127.0.0.0/8'),      # Loopback
    ipaddress.IPv4Network('10.0.0.0/8'),       # Private class A
    ipaddress.IPv4Network('172.16.0.0/12'),    # Private class B
    ipaddress.IPv4Network('192.168.0.0/16'),   # Private class C
    ipaddress.IPv4Network('169.254.0.0/16'),   # Link-local
    ipaddress.IPv4Network('0.0.0.0/8'),        # Current network
    ipaddress.IPv4Network('255.255.255.255/32'),  # Broadcast
]

PRIVATE_IPV6_RANGES = [
    ipaddress.IPv6Network('::1/128'),          # Loopback
    ipaddress.IPv6Network('fe80::/10'),        # Link-local
    ipaddress.IPv6Network('fc00::/7'),         # Unique local addresses (ULA)
    ipaddress.IPv6Network('::/128'),           # Unspecified
]


# ============================================================================
# SQL Injection Patterns
# ============================================================================

SQL_INJECTION_PATTERNS = [
    r"(\bunion\b.*\bselect\b)",                # UNION SELECT
    r"(\bselect\b.*\bfrom\b.*\bwhere\b)",      # SELECT FROM WHERE
    r"(\binsert\b.*\binto\b.*\bvalues\b)",     # INSERT INTO VALUES
    r"(\bupdate\b.*\bset\b)",                   # UPDATE SET
    r"(\bdelete\b.*\bfrom\b)",                  # DELETE FROM
    r"(\bdrop\b.*\btable\b)",                   # DROP TABLE
    r"(\bdrop\b.*\bdatabase\b)",                # DROP DATABASE
    r"(--|;|\/\*|\*\/)",                        # SQL comments
    r"(\bor\b.*=.*)",                           # OR 1=1
    r"(\band\b.*=.*)",                          # AND 1=1
    r"('.*OR.*'.*=.*')",                        # 'x' OR 'x'='x'
    r"(\bexec\b|\bexecute\b)",                  # EXEC/EXECUTE
    r"(\bxp_cmdshell\b)",                       # xp_cmdshell (SQL Server)
]


# ============================================================================
# XSS Patterns
# ============================================================================

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",              # <script> tags
    r"javascript:",                             # javascript: protocol
    r"on\w+\s*=",                              # Event handlers (onclick, onerror, etc.)
    r"<iframe[^>]*>",                          # <iframe> tags
    r"<embed[^>]*>",                           # <embed> tags
    r"<object[^>]*>",                          # <object> tags
]


# ============================================================================
# IP Validation
# ============================================================================

def validate_public_ip(
    ip_str: str,
    allow_private: bool = False
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """
    Validate IP address and ensure it's not a private/internal address

    Args:
        ip_str: IP address string
        allow_private: Allow private IP ranges (default: False for security)

    Returns:
        Validated IP address object

    Raises:
        PrivateIPError: If IP is in private range
        ValueError: If IP format is invalid
    """
    try:
        # Parse IP address (supports both IPv4 and IPv6)
        ip = ipaddress.ip_address(ip_str)

        # Check if private/internal (DNS rebinding protection)
        if not allow_private:
            if isinstance(ip, ipaddress.IPv4Address):
                for private_range in PRIVATE_IPV4_RANGES:
                    if ip in private_range:
                        raise PrivateIPError(
                            f"Private IPv4 address detected: {ip_str}. "
                            f"DNS rebinding attack prevented. Range: {private_range}"
                        )

            elif isinstance(ip, ipaddress.IPv6Address):
                for private_range in PRIVATE_IPV6_RANGES:
                    if ip in private_range:
                        raise PrivateIPError(
                            f"Private IPv6 address detected: {ip_str}. "
                            f"DNS rebinding attack prevented. Range: {private_range}"
                        )

        return ip

    except ValueError as e:
        raise ValueError(f"Invalid IP address format: {ip_str}. {e}")


def is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is private/internal

    Args:
        ip_str: IP address string

    Returns:
        True if private, False if public
    """
    try:
        validate_public_ip(ip_str, allow_private=False)
        return False
    except PrivateIPError:
        return True
    except ValueError:
        return False


# ============================================================================
# Domain Validation (Enhanced)
# ============================================================================

def validate_domain_secure(domain: str, allow_idn: bool = False) -> str:
    """
    Validate domain with enhanced security checks

    Security Checks:
    - RFC 1035 compliance (hostname format)
    - Punycode/IDN attack prevention
    - Homograph attack prevention (consecutive hyphens)
    - Length limits (max 253 chars total, 63 per label)
    - SQL injection patterns
    - XSS patterns

    Args:
        domain: Domain name to validate
        allow_idn: Allow internationalized domain names (default: False for security)

    Returns:
        Validated lowercase domain string

    Raises:
        SecurityValidationError: If security checks fail
        ValueError: If domain format is invalid
    """
    domain = domain.lower().strip()

    # Check length
    if len(domain) > 253:
        raise ValueError("Domain name exceeds maximum length (253 characters)")

    # RFC 1035 hostname validation
    pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,}$'
    if not re.match(pattern, domain):
        raise ValueError(f"Invalid domain format (RFC 1035): {domain}")

    # Punycode/IDN check (xn-- prefix indicates punycode)
    if 'xn--' in domain and not allow_idn:
        raise IDNAttackError(
            f"Internationalized domain names (punycode) detected: {domain}. "
            "IDN domains are disabled for security (homograph attacks)."
        )

    # Homograph attack check: consecutive hyphens
    if '--' in domain:
        raise IDNAttackError(
            f"Consecutive hyphens detected: {domain}. "
            "Potential homograph attack (e.g., paypal--secure.com)."
        )

    # Check each label length (between dots)
    labels = domain.split('.')
    for label in labels:
        if len(label) > 63:
            raise ValueError(f"Domain label exceeds maximum length (63 characters): {label}")

        # Labels cannot start or end with hyphen
        if label.startswith('-') or label.endswith('-'):
            raise ValueError(f"Domain labels cannot start or end with hyphen: {label}")

    # SQL injection check
    check_sql_injection(domain, context="domain")

    # XSS check
    check_xss(domain, context="domain")

    return domain


# ============================================================================
# SQL Injection Protection
# ============================================================================

def check_sql_injection(value: str, context: str = "input") -> str:
    """
    Check for SQL injection patterns

    Args:
        value: Input string to validate
        context: Context of input (for error messages)

    Returns:
        Original value if safe

    Raises:
        SQLInjectionError: If SQL injection pattern detected
    """
    value_lower = value.lower()

    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise SQLInjectionError(
                f"Potential SQL injection detected in {context}: pattern '{pattern}' matched. "
                f"Input: {value[:50]}..."
            )

    return value


def sanitize_sql_input(value: str) -> str:
    """
    Sanitize input for SQL queries (use parameterized queries instead!)

    Args:
        value: Input string

    Returns:
        Sanitized string (single quotes escaped)

    Note:
        This is a fallback. ALWAYS use parameterized queries (psycopg2 placeholders)
    """
    # Check for injection first
    check_sql_injection(value)

    # Escape single quotes
    return value.replace("'", "''")


# ============================================================================
# XSS Protection
# ============================================================================

def check_xss(value: str, context: str = "input") -> str:
    """
    Check for XSS attack patterns

    Args:
        value: Input string to validate
        context: Context of input (for error messages)

    Returns:
        Original value if safe

    Raises:
        XSSError: If XSS pattern detected
    """
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise XSSError(
                f"Potential XSS attack detected in {context}: pattern '{pattern}' matched. "
                f"Input: {value[:50]}..."
            )

    return value


def sanitize_html(value: str) -> str:
    """
    Sanitize HTML by escaping special characters

    Args:
        value: Input string

    Returns:
        HTML-escaped string
    """
    return html.escape(value)


# ============================================================================
# Pydantic Validators (for FastAPI models)
# ============================================================================

def validate_public_ip_field(ip: str) -> str:
    """Pydantic field validator for public IPs"""
    validate_public_ip(ip, allow_private=False)
    return ip


def validate_domain_field(domain: str) -> str:
    """Pydantic field validator for domains"""
    return validate_domain_secure(domain, allow_idn=False)


def validate_safe_string(value: str) -> str:
    """Pydantic field validator for safe strings (SQL + XSS checks)"""
    check_sql_injection(value)
    check_xss(value)
    return value


# ============================================================================
# DNS Record Content Validation (Enhanced)
# ============================================================================

def validate_dns_record_content(
    record_type: str,
    content: str,
    allow_private_ips: bool = False
) -> str:
    """
    Validate DNS record content based on type

    Args:
        record_type: DNS record type (A, AAAA, CNAME, etc.)
        content: Record content value
        allow_private_ips: Allow private IPs in A/AAAA records (default: False)

    Returns:
        Validated content string

    Raises:
        SecurityValidationError: If security checks fail
        ValueError: If content format is invalid
    """
    content = content.strip()

    if record_type.upper() == 'A':
        # IPv4 address validation with private IP check
        try:
            ip = validate_public_ip(content, allow_private=allow_private_ips)
            return str(ip)
        except PrivateIPError:
            raise DNSRebindingError(
                f"Private IPv4 address in DNS A record: {content}. "
                "This could enable DNS rebinding attacks."
            )

    elif record_type.upper() == 'AAAA':
        # IPv6 address validation with private IP check
        try:
            ip = validate_public_ip(content, allow_private=allow_private_ips)
            return str(ip)
        except PrivateIPError:
            raise DNSRebindingError(
                f"Private IPv6 address in DNS AAAA record: {content}. "
                "This could enable DNS rebinding attacks."
            )

    elif record_type.upper() in ['CNAME', 'MX', 'NS']:
        # Hostname/domain validation
        return validate_domain_secure(content.rstrip('.'))

    elif record_type.upper() == 'TXT':
        # TXT records: check for XSS and SQL injection
        check_xss(content, context="TXT record")
        check_sql_injection(content, context="TXT record")
        return content

    else:
        # Generic validation for other record types
        check_sql_injection(content, context=f"{record_type} record")
        return content


# ============================================================================
# Email Validation (Security-Enhanced)
# ============================================================================

def validate_email_secure(email: str) -> str:
    """
    Validate email address with security checks

    Args:
        email: Email address

    Returns:
        Validated lowercase email

    Raises:
        SecurityValidationError: If security checks fail
        ValueError: If email format is invalid
    """
    email = email.lower().strip()

    # Basic email format validation
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    # SQL injection check
    check_sql_injection(email, context="email")

    # XSS check
    check_xss(email, context="email")

    # Split email
    local, domain = email.split('@')

    # Validate domain part
    validate_domain_secure(domain)

    return email


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Security Validators Module - Test Mode")
    print("=" * 70)

    # Test 1: Private IP detection
    print("\n1. Testing private IP detection:")
    test_ips = [
        ("8.8.8.8", False),          # Public
        ("127.0.0.1", True),         # Loopback
        ("192.168.1.1", True),       # Private
        ("10.0.0.1", True),          # Private
        ("172.16.0.1", True),        # Private
        ("::1", True),               # IPv6 loopback
    ]

    for ip, should_be_private in test_ips:
        result = is_private_ip(ip)
        status = "✅" if result == should_be_private else "❌"
        print(f"   {status} {ip}: {'Private' if result else 'Public'}")

    # Test 2: SQL injection detection
    print("\n2. Testing SQL injection detection:")
    sql_tests = [
        ("normal_text", False),
        ("' OR '1'='1", True),
        ("admin'--", True),
        ("UNION SELECT", True),
        ("DROP TABLE users", True),
    ]

    for test_input, should_fail in sql_tests:
        try:
            check_sql_injection(test_input)
            status = "❌" if should_fail else "✅"
            print(f"   {status} '{test_input}': Passed validation")
        except SQLInjectionError:
            status = "✅" if should_fail else "❌"
            print(f"   {status} '{test_input}': Blocked (SQL injection)")

    # Test 3: Domain validation
    print("\n3. Testing domain validation:")
    domain_tests = [
        ("example.com", True),
        ("xn--e1afmkfd.xn--p1ai", False),  # Punycode
        ("test--domain.com", False),        # Consecutive hyphens
        ("-invalid.com", False),            # Starts with hyphen
    ]

    for domain, should_pass in domain_tests:
        try:
            validate_domain_secure(domain)
            status = "✅" if should_pass else "❌"
            print(f"   {status} {domain}: Valid")
        except (SecurityValidationError, ValueError) as e:
            status = "✅" if not should_pass else "❌"
            print(f"   {status} {domain}: Blocked ({type(e).__name__})")

    # Test 4: DNS rebinding protection
    print("\n4. Testing DNS rebinding protection:")
    dns_tests = [
        ("A", "8.8.8.8", True),
        ("A", "127.0.0.1", False),   # Loopback
        ("A", "192.168.1.1", False), # Private
        ("AAAA", "::1", False),       # IPv6 loopback
    ]

    for record_type, content, should_pass in dns_tests:
        try:
            validate_dns_record_content(record_type, content, allow_private_ips=False)
            status = "✅" if should_pass else "❌"
            print(f"   {status} {record_type} {content}: Allowed")
        except DNSRebindingError:
            status = "✅" if not should_pass else "❌"
            print(f"   {status} {record_type} {content}: Blocked (DNS rebinding)")

    print("\n✅ All security validators loaded successfully")
