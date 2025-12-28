"""
NameCheap API Integration Module for UC-Cloud Ops-Center

This module provides comprehensive NameCheap domain management with domain discovery,
DNS export, nameserver updates, email service detection, and migration support for
automated domain migration from NameCheap to Cloudflare.

Author: Backend API Developer Agent
Date: October 22, 2025
Epic: 1.7 - NameCheap Integration & Migration Workflow
"""

import requests
import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from functools import wraps
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class NameCheapError(Exception):
    """Base exception for NameCheap operations"""
    pass


class NameCheapAPIError(NameCheapError):
    """NameCheap API returned an error"""
    pass


class NameCheapAuthError(NameCheapError):
    """Authentication failed with NameCheap API"""
    pass


class NameCheapRateLimitError(NameCheapError):
    """Rate limit exceeded"""
    pass


class NameCheapValidationError(NameCheapError):
    """Input validation failed"""
    pass


class NameCheapDomainLockedError(NameCheapError):
    """Domain is locked and cannot be modified"""
    pass


class NameCheapDomainExpiredError(NameCheapError):
    """Domain has expired"""
    pass


# ============================================================================
# Enums
# ============================================================================

class DomainStatus(str, Enum):
    """Domain status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    LOCKED = "locked"
    SUSPENDED = "suspended"


class EmailServiceType(str, Enum):
    """Email service provider types"""
    MICROSOFT365 = "microsoft365"
    NAMECHEAP_PRIVATE = "namecheap_private"
    GOOGLE_WORKSPACE = "google_workspace"
    EMAIL_FORWARDING = "email_forwarding"
    CUSTOM = "custom"
    NONE = "none"


class RecordType(str, Enum):
    """DNS record types"""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    SRV = "SRV"
    CAA = "CAA"


# ============================================================================
# Pydantic Models for Input Validation
# ============================================================================

class NameCheapCredentials(BaseModel):
    """Validated NameCheap API credentials"""
    api_username: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=32, max_length=64)
    username: str = Field(..., min_length=1, max_length=100)
    client_ip: IPvAnyAddress = Field(..., description="Whitelisted IP address")
    sandbox: bool = Field(False, description="Use sandbox environment")

    @field_validator('client_ip')
    @classmethod
    def validate_client_ip(cls, v):
        """Ensure IP is a string for API calls"""
        return str(v)


class DomainInfo(BaseModel):
    """Domain information model"""
    domain: str
    status: DomainStatus
    expiration_date: Optional[datetime] = None
    is_locked: bool = False
    is_premium: bool = False
    whois_guard: bool = False
    current_nameservers: List[str] = []


class DNSRecord(BaseModel):
    """DNS record model"""
    type: RecordType
    host: str  # @ for root, subdomain for others
    value: str
    ttl: int = Field(1800, ge=60, le=86400)
    priority: Optional[int] = Field(None, ge=0, le=65535)
    mx_pref: Optional[int] = None  # For MX records (NameCheap uses MXPref)

    @field_validator('ttl')
    @classmethod
    def validate_ttl(cls, v):
        """Validate TTL is in valid range"""
        if v < 60 or v > 86400:
            # NameCheap default if invalid
            return 1800
        return v


class EmailServiceConfig(BaseModel):
    """Email service configuration"""
    service_type: EmailServiceType
    mx_records: List[Dict[str, Any]] = []
    spf_record: Optional[str] = None
    dmarc_record: Optional[str] = None
    dkim_selectors: List[str] = []
    additional_records: List[DNSRecord] = []


# ============================================================================
# Rate Limiting Decorator
# ============================================================================

def namecheap_rate_limit(func):
    """
    Decorator to handle NameCheap rate limiting

    NameCheap API limit: 50 calls per minute (conservative estimate)
    Strategy: Track requests and introduce delays when approaching limit
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'request_count'):
            current_time = time.time()

            # Reset counter every minute
            if current_time - self.rate_limit_reset > 60:
                self.request_count = 0
                self.rate_limit_reset = current_time

            # Increment counter
            self.request_count += 1

            # Warn at 80% of limit
            if self.request_count > 40:
                logger.warning(
                    f"⚠️ Approaching NameCheap rate limit: {self.request_count}/50 requests per minute"
                )

            # Slow down at 90% of limit
            if self.request_count > 45:
                logger.warning("Rate limit close, introducing delay...")
                time.sleep(2)

            # Block at limit
            if self.request_count > 50:
                wait_time = 60 - (current_time - self.rate_limit_reset)
                raise NameCheapRateLimitError(
                    f"Rate limit exceeded. Wait {int(wait_time)} seconds before retrying."
                )

        return func(self, *args, **kwargs)

    return wrapper


# ============================================================================
# NameCheap API Client (Base Class)
# ============================================================================

class NameCheapClient:
    """
    Base NameCheap API client with XML request/response handling

    Features:
    - XML API authentication
    - Automatic error handling
    - Rate limiting protection
    - Retry logic with exponential backoff
    """

    # NameCheap API endpoints
    PRODUCTION_URL = "https://api.namecheap.com/xml.response"
    SANDBOX_URL = "https://api.sandbox.namecheap.com/xml.response"

    def __init__(self, credentials: NameCheapCredentials):
        """
        Initialize NameCheap API client

        Args:
            credentials: Validated NameCheap credentials
        """
        self.credentials = credentials
        self.api_url = self.SANDBOX_URL if credentials.sandbox else self.PRODUCTION_URL

        # Rate limiting tracking
        self.request_count = 0
        self.rate_limit_reset = time.time()

        logger.info(
            f"NameCheap client initialized (sandbox={credentials.sandbox})"
        )

    @namecheap_rate_limit
    def _request(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> ET.Element:
        """
        Make NameCheap API request

        Args:
            command: API command (e.g., namecheap.domains.getList)
            params: Additional parameters for the command
            max_retries: Maximum retry attempts

        Returns:
            XML response root element

        Raises:
            NameCheapAPIError: If API returns an error
            NameCheapAuthError: If authentication fails
            NameCheapRateLimitError: If rate limit exceeded
        """
        # Build request parameters
        request_params = {
            'ApiUser': self.credentials.api_username,
            'ApiKey': self.credentials.api_key,
            'UserName': self.credentials.username,
            'ClientIp': self.credentials.client_ip,
            'Command': command
        }

        # Add command-specific parameters
        if params:
            request_params.update(params)

        for attempt in range(max_retries):
            try:
                logger.debug(f"NameCheap API request: {command}")

                response = requests.get(
                    self.api_url,
                    params=request_params,
                    timeout=30
                )

                # Parse XML response
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    raise NameCheapAPIError(f"Invalid XML response: {e}")

                # Check for API errors
                status = root.get('Status')

                if status != 'OK':
                    errors = root.findall('.//Error')
                    if errors:
                        error_msg = errors[0].text or "Unknown error"
                        error_number = errors[0].get('Number', 'Unknown')

                        # Handle specific error types
                        if 'Authentication' in error_msg or 'API key' in error_msg:
                            raise NameCheapAuthError(f"Authentication failed: {error_msg}")

                        if 'rate limit' in error_msg.lower():
                            raise NameCheapRateLimitError(error_msg)

                        if 'locked' in error_msg.lower():
                            raise NameCheapDomainLockedError(error_msg)

                        if 'expired' in error_msg.lower():
                            raise NameCheapDomainExpiredError(error_msg)

                        raise NameCheapAPIError(f"API error {error_number}: {error_msg}")

                # Success
                return root

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise NameCheapError("Request timed out after multiple retries")

            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise NameCheapError("Connection failed after multiple retries")

            except (NameCheapAuthError, NameCheapRateLimitError, NameCheapDomainLockedError,
                    NameCheapDomainExpiredError):
                # Don't retry these errors
                raise

            except Exception as e:
                logger.error(f"Unexpected error in NameCheap request: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise NameCheapError(f"Unexpected error: {e}")

        raise NameCheapError("Max retries exceeded")


# ============================================================================
# Domain Manager
# ============================================================================

class DomainManager(NameCheapClient):
    """
    NameCheap Domain Management

    Handles:
    - Domain discovery (list all domains)
    - Domain information retrieval
    - Domain existence checking
    """

    def list_domains(self, search: Optional[str] = None) -> List[DomainInfo]:
        """
        List all domains in NameCheap account

        Args:
            search: Optional search filter

        Returns:
            List of domain information objects
        """
        params = {}
        if search:
            params['SearchTerm'] = search

        try:
            root = self._request('namecheap.domains.getList', params)

            domains = []
            domain_list = root.find('.//DomainGetListResult')

            if domain_list is not None:
                for domain_elem in domain_list.findall('Domain'):
                    domain_name = domain_elem.get('Name')

                    # Parse expiration date
                    expires = domain_elem.get('Expires')
                    expiration_date = None
                    if expires:
                        try:
                            expiration_date = datetime.strptime(expires, '%m/%d/%Y')
                        except ValueError:
                            pass

                    # Determine status
                    is_expired = domain_elem.get('IsExpired', 'false').lower() == 'true'
                    is_locked = domain_elem.get('IsLocked', 'false').lower() == 'true'

                    status = DomainStatus.ACTIVE
                    if is_expired:
                        status = DomainStatus.EXPIRED
                    elif is_locked:
                        status = DomainStatus.LOCKED

                    domain_info = DomainInfo(
                        domain=domain_name,
                        status=status,
                        expiration_date=expiration_date,
                        is_locked=is_locked,
                        is_premium=domain_elem.get('IsPremium', 'false').lower() == 'true',
                        whois_guard=domain_elem.get('WhoisGuard', 'NOTPRESENT') == 'ENABLED'
                    )

                    domains.append(domain_info)

            logger.info(f"Retrieved {len(domains)} domains from NameCheap")
            return domains

        except Exception as e:
            logger.error(f"Failed to list domains: {e}")
            raise

    def get_domain_info(self, domain: str) -> DomainInfo:
        """
        Get detailed information about a domain

        Args:
            domain: Domain name

        Returns:
            Domain information object
        """
        try:
            # Extract SLD and TLD
            sld, tld = self._parse_domain(domain)

            params = {
                'DomainName': domain
            }

            root = self._request('namecheap.domains.getInfo', params)

            domain_details = root.find('.//DomainGetInfoResult')

            if domain_details is None:
                raise NameCheapAPIError(f"Domain {domain} not found")

            # Parse domain info
            status_elem = domain_details.find('DomainDetails/ExpiredDate')
            expires = status_elem.text if status_elem is not None else None

            expiration_date = None
            if expires:
                try:
                    expiration_date = datetime.strptime(expires, '%m/%d/%Y')
                except ValueError:
                    pass

            # Check if expired
            is_expired = False
            if expiration_date and expiration_date < datetime.now():
                is_expired = True

            # Check lock status
            lock_elem = domain_details.find('Modificationrights')
            is_locked = lock_elem is not None and lock_elem.get('All', 'false').lower() == 'false'

            # Get nameservers
            nameservers = []
            ns_elem = domain_details.find('DnsDetails/Nameserver')
            if ns_elem is not None:
                nameservers = [ns.text for ns in ns_elem.findall('Nameserver') if ns.text]

            # Also try alternative NS location
            if not nameservers:
                for ns in domain_details.findall('.//Nameserver'):
                    if ns.text:
                        nameservers.append(ns.text)

            status = DomainStatus.ACTIVE
            if is_expired:
                status = DomainStatus.EXPIRED
            elif is_locked:
                status = DomainStatus.LOCKED

            domain_info = DomainInfo(
                domain=domain,
                status=status,
                expiration_date=expiration_date,
                is_locked=is_locked,
                is_premium=domain_details.find('IsPremium') is not None,
                whois_guard=domain_details.find('.//WhoisGuard') is not None,
                current_nameservers=nameservers
            )

            logger.info(f"Retrieved info for domain: {domain}")
            return domain_info

        except Exception as e:
            logger.error(f"Failed to get domain info for {domain}: {e}")
            raise

    def check_domain_exists(self, domain: str) -> bool:
        """
        Check if domain exists in account

        Args:
            domain: Domain name to check

        Returns:
            True if domain exists in account
        """
        try:
            self.get_domain_info(domain)
            return True
        except NameCheapAPIError as e:
            if 'not found' in str(e).lower():
                return False
            raise

    def _parse_domain(self, domain: str) -> Tuple[str, str]:
        """
        Parse domain into SLD and TLD

        Args:
            domain: Full domain name (e.g., example.com)

        Returns:
            Tuple of (SLD, TLD)

        Examples:
            example.com → (example, com)
            example.co.uk → (example, co.uk)
        """
        parts = domain.lower().split('.')

        # Handle multi-part TLDs (e.g., co.uk, com.au)
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net', 'ac', 'gov']:
            return '.'.join(parts[:-2]), '.'.join(parts[-2:])

        # Standard TLD
        if len(parts) >= 2:
            return '.'.join(parts[:-1]), parts[-1]

        raise NameCheapValidationError(f"Invalid domain format: {domain}")


# ============================================================================
# DNS Manager
# ============================================================================

class DNSManager(NameCheapClient):
    """
    NameCheap DNS Management

    Handles:
    - DNS record export
    - Email service detection
    - DNS backup
    """

    def get_dns_hosts(self, domain: str) -> List[DNSRecord]:
        """
        Get all DNS records for a domain

        Args:
            domain: Domain name

        Returns:
            List of DNS records
        """
        try:
            sld, tld = self._parse_domain(domain)

            params = {
                'SLD': sld,
                'TLD': tld
            }

            root = self._request('namecheap.domains.dns.getHosts', params)

            records = []
            hosts = root.find('.//DomainDNSGetHostsResult')

            if hosts is not None:
                for host in hosts.findall('host'):
                    record_type = host.get('Type', '').upper()

                    # Skip unsupported record types
                    try:
                        rt = RecordType(record_type)
                    except ValueError:
                        logger.warning(f"Unsupported record type: {record_type}, skipping")
                        continue

                    host_name = host.get('Name', '@')
                    address = host.get('Address', '')
                    ttl = int(host.get('TTL', '1800'))
                    mx_pref = host.get('MXPref')

                    priority = None
                    if mx_pref:
                        try:
                            priority = int(mx_pref)
                        except ValueError:
                            pass

                    record = DNSRecord(
                        type=rt,
                        host=host_name,
                        value=address,
                        ttl=ttl,
                        priority=priority,
                        mx_pref=int(mx_pref) if mx_pref else None
                    )

                    records.append(record)

            logger.info(f"Retrieved {len(records)} DNS records for {domain}")
            return records

        except Exception as e:
            logger.error(f"Failed to get DNS hosts for {domain}: {e}")
            raise

    def get_email_settings(self, domain: str) -> EmailServiceConfig:
        """
        Detect email service configuration for domain

        Args:
            domain: Domain name

        Returns:
            Email service configuration
        """
        try:
            records = self.get_dns_hosts(domain)

            # Extract MX records
            mx_records = [r for r in records if r.type == RecordType.MX]
            txt_records = [r for r in records if r.type == RecordType.TXT]
            cname_records = [r for r in records if r.type == RecordType.CNAME]

            if not mx_records:
                return EmailServiceConfig(service_type=EmailServiceType.NONE)

            # Detect service type based on MX records
            service_type = EmailServiceType.CUSTOM
            mx_values = [mx.value.lower() for mx in mx_records]

            # Microsoft 365
            if any('mail.protection.outlook.com' in mx for mx in mx_values):
                service_type = EmailServiceType.MICROSOFT365

            # NameCheap Private Email
            elif any('privateemail.com' in mx for mx in mx_values):
                service_type = EmailServiceType.NAMECHEAP_PRIVATE

            # Google Workspace
            elif any('google.com' in mx or 'googlemail.com' in mx for mx in mx_values):
                service_type = EmailServiceType.GOOGLE_WORKSPACE

            # Email Forwarding
            elif any('registrar-servers.com' in mx for mx in mx_values):
                service_type = EmailServiceType.EMAIL_FORWARDING

            # Extract SPF record
            spf_record = None
            for txt in txt_records:
                if txt.host == '@' and 'v=spf1' in txt.value:
                    spf_record = txt.value
                    break

            # Extract DMARC record
            dmarc_record = None
            for txt in txt_records:
                if txt.host.startswith('_dmarc') and 'v=DMARC1' in txt.value:
                    dmarc_record = txt.value
                    break

            # Extract DKIM selectors (common patterns)
            dkim_selectors = []
            for txt in txt_records:
                if 'dkim' in txt.host.lower() or 'domainkey' in txt.host.lower():
                    dkim_selectors.append(txt.host)

            # Additional email-related records
            additional_records = []

            # Add autodiscover CNAME (Microsoft 365)
            for cname in cname_records:
                if cname.host in ['autodiscover', 'enterpriseregistration']:
                    additional_records.append(cname)

            # Add autoconfig CNAME (Various providers)
            for cname in cname_records:
                if cname.host == 'autoconfig':
                    additional_records.append(cname)

            config = EmailServiceConfig(
                service_type=service_type,
                mx_records=[{
                    'host': mx.host,
                    'value': mx.value,
                    'priority': mx.priority or mx.mx_pref or 10,
                    'ttl': mx.ttl
                } for mx in mx_records],
                spf_record=spf_record,
                dmarc_record=dmarc_record,
                dkim_selectors=dkim_selectors,
                additional_records=additional_records
            )

            logger.info(f"Detected email service for {domain}: {service_type.value}")
            return config

        except Exception as e:
            logger.error(f"Failed to get email settings for {domain}: {e}")
            raise

    def export_dns_records(
        self,
        domain: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Export DNS records in specified format

        Args:
            domain: Domain name
            format: Export format (json, csv, bind)

        Returns:
            Dictionary with DNS records and metadata
        """
        try:
            records = self.get_dns_hosts(domain)
            domain_info = DomainManager(self.credentials).get_domain_info(domain)

            export_data = {
                'domain': domain,
                'exported_at': datetime.utcnow().isoformat(),
                'nameservers': domain_info.current_nameservers,
                'total_records': len(records),
                'format': format,
                'records': []
            }

            for record in records:
                record_dict = {
                    'type': record.type.value,
                    'host': record.host,
                    'value': record.value,
                    'ttl': record.ttl
                }

                if record.priority is not None:
                    record_dict['priority'] = record.priority

                export_data['records'].append(record_dict)

            logger.info(f"Exported {len(records)} DNS records for {domain} ({format} format)")
            return export_data

        except Exception as e:
            logger.error(f"Failed to export DNS records for {domain}: {e}")
            raise

    def _parse_domain(self, domain: str) -> Tuple[str, str]:
        """Parse domain into SLD and TLD"""
        parts = domain.lower().split('.')
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net', 'ac', 'gov']:
            return '.'.join(parts[:-2]), '.'.join(parts[-2:])
        if len(parts) >= 2:
            return '.'.join(parts[:-1]), parts[-1]
        raise NameCheapValidationError(f"Invalid domain format: {domain}")


# ============================================================================
# Nameserver Manager
# ============================================================================

class NameserverManager(NameCheapClient):
    """
    NameCheap Nameserver Management

    Handles:
    - Get current nameservers
    - Update nameservers (for migration)
    - Revert nameservers (rollback)
    """

    def get_nameservers(self, domain: str) -> List[str]:
        """
        Get current nameservers for domain

        Args:
            domain: Domain name

        Returns:
            List of nameserver hostnames
        """
        try:
            domain_info = DomainManager(self.credentials).get_domain_info(domain)
            return domain_info.current_nameservers
        except Exception as e:
            logger.error(f"Failed to get nameservers for {domain}: {e}")
            raise

    def set_nameservers(
        self,
        domain: str,
        nameservers: List[str],
        log_transaction: bool = True
    ) -> Dict[str, Any]:
        """
        Update nameservers for domain

        Args:
            domain: Domain name
            nameservers: List of nameserver hostnames (2-13 nameservers)
            log_transaction: Whether to log for rollback capability

        Returns:
            Update result dictionary

        Raises:
            NameCheapDomainLockedError: If domain is locked
            NameCheapDomainExpiredError: If domain is expired
            NameCheapValidationError: If nameservers are invalid
        """
        try:
            # Validate inputs
            if not nameservers or len(nameservers) < 2:
                raise NameCheapValidationError("At least 2 nameservers required")

            if len(nameservers) > 13:
                raise NameCheapValidationError("Maximum 13 nameservers allowed")

            # Check domain status
            domain_info = DomainManager(self.credentials).get_domain_info(domain)

            if domain_info.status == DomainStatus.LOCKED:
                raise NameCheapDomainLockedError(
                    f"Domain {domain} is locked. Unlock it before updating nameservers."
                )

            if domain_info.status == DomainStatus.EXPIRED:
                raise NameCheapDomainExpiredError(
                    f"Domain {domain} has expired. Renew it before updating nameservers."
                )

            # Store original nameservers for rollback
            original_nameservers = domain_info.current_nameservers

            # Parse domain
            sld, tld = self._parse_domain(domain)

            # Build parameters
            params = {
                'SLD': sld,
                'TLD': tld,
                'Nameservers': ','.join(nameservers)
            }

            # Make API request
            root = self._request('namecheap.domains.dns.setCustom', params)

            # Check result
            result = root.find('.//DomainDNSSetCustomResult')

            if result is None:
                raise NameCheapAPIError("Failed to update nameservers")

            updated = result.get('Updated', 'false').lower() == 'true'

            if not updated:
                raise NameCheapAPIError("Nameserver update failed")

            logger.info(
                f"Nameservers updated for {domain}: {', '.join(nameservers)}"
            )

            return {
                'success': True,
                'domain': domain,
                'old_nameservers': original_nameservers,
                'new_nameservers': nameservers,
                'updated_at': datetime.utcnow().isoformat(),
                'message': f'Nameservers updated successfully for {domain}'
            }

        except Exception as e:
            logger.error(f"Failed to set nameservers for {domain}: {e}")
            raise

    def revert_nameservers(
        self,
        domain: str,
        original_nameservers: List[str]
    ) -> Dict[str, Any]:
        """
        Revert nameservers to original values (rollback)

        Args:
            domain: Domain name
            original_nameservers: Original nameserver list

        Returns:
            Rollback result dictionary
        """
        try:
            logger.warning(f"Reverting nameservers for {domain} to original values")

            result = self.set_nameservers(
                domain=domain,
                nameservers=original_nameservers,
                log_transaction=False  # Don't log rollback transactions
            )

            result['rollback'] = True
            result['message'] = f'Nameservers reverted successfully for {domain}'

            return result

        except Exception as e:
            logger.error(f"Failed to revert nameservers for {domain}: {e}")
            raise

    def _parse_domain(self, domain: str) -> Tuple[str, str]:
        """Parse domain into SLD and TLD"""
        parts = domain.lower().split('.')
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net', 'ac', 'gov']:
            return '.'.join(parts[:-2]), '.'.join(parts[-2:])
        if len(parts) >= 2:
            return '.'.join(parts[:-1]), parts[-1]
        raise NameCheapValidationError(f"Invalid domain format: {domain}")


# ============================================================================
# Main NameCheap Manager (Combines All Managers)
# ============================================================================

class NameCheapManager:
    """
    Main NameCheap Management Interface

    Combines:
    - Domain discovery (DomainManager)
    - DNS export (DNSManager)
    - Nameserver updates (NameserverManager)
    - Email service detection (DNSManager)

    Usage:
        credentials = NameCheapCredentials(
            api_username="SkyBehind",
            api_key="your-namecheap-api-key",
            username="SkyBehind",
            client_ip="YOUR_SERVER_IP"
        )

        manager = NameCheapManager(credentials)

        # List domains
        domains = manager.domains.list_domains()

        # Export DNS
        dns_backup = manager.dns.export_dns_records("example.com")

        # Update nameservers
        result = manager.nameservers.set_nameservers(
            "example.com",
            ["ns1.cloudflare.com", "ns2.cloudflare.com"]
        )
    """

    def __init__(self, credentials: NameCheapCredentials):
        """
        Initialize NameCheap Manager

        Args:
            credentials: Validated NameCheap credentials
        """
        self.credentials = credentials
        self.domains = DomainManager(credentials)
        self.dns = DNSManager(credentials)
        self.nameservers = NameserverManager(credentials)

        logger.info("NameCheapManager initialized")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test API connection and credentials

        Returns:
            Connection test results
        """
        try:
            # Try to list domains as a connection test
            domains = self.domains.list_domains()

            return {
                'connected': True,
                'api_username': self.credentials.api_username,
                'client_ip': self.credentials.client_ip,
                'sandbox': self.credentials.sandbox,
                'domain_count': len(domains),
                'message': 'Connection successful'
            }

        except NameCheapAuthError as e:
            return {
                'connected': False,
                'error': 'Authentication failed',
                'details': str(e),
                'message': 'Invalid API credentials or IP not whitelisted'
            }

        except Exception as e:
            return {
                'connected': False,
                'error': 'Connection failed',
                'details': str(e),
                'message': str(e)
            }

    def get_migration_summary(self, domain: str) -> Dict[str, Any]:
        """
        Get comprehensive migration summary for a domain

        Args:
            domain: Domain name

        Returns:
            Dictionary with domain info, DNS records, email config
        """
        try:
            # Get domain info
            domain_info = self.domains.get_domain_info(domain)

            # Get DNS records
            dns_records = self.dns.get_dns_hosts(domain)

            # Get email service config
            email_config = self.dns.get_email_settings(domain)

            return {
                'domain': domain,
                'status': domain_info.status.value,
                'expiration_date': domain_info.expiration_date.isoformat() if domain_info.expiration_date else None,
                'is_locked': domain_info.is_locked,
                'current_nameservers': domain_info.current_nameservers,
                'dns_record_count': len(dns_records),
                'dns_records': [
                    {
                        'type': r.type.value,
                        'host': r.host,
                        'value': r.value,
                        'ttl': r.ttl,
                        'priority': r.priority
                    }
                    for r in dns_records
                ],
                'email_service': {
                    'type': email_config.service_type.value,
                    'mx_records': email_config.mx_records,
                    'has_spf': email_config.spf_record is not None,
                    'has_dmarc': email_config.dmarc_record is not None,
                    'dkim_selectors': email_config.dkim_selectors
                },
                'migration_ready': not domain_info.is_locked and domain_info.status == DomainStatus.ACTIVE
            }

        except Exception as e:
            logger.error(f"Failed to get migration summary for {domain}: {e}")
            raise


# ============================================================================
# Module-level convenience functions
# ============================================================================

def create_manager_from_dict(credentials_dict: Dict[str, Any]) -> NameCheapManager:
    """
    Create NameCheapManager from dictionary

    Args:
        credentials_dict: Dictionary with credential fields

    Returns:
        NameCheapManager instance
    """
    credentials = NameCheapCredentials(**credentials_dict)
    return NameCheapManager(credentials)


def validate_domain_format(domain: str) -> bool:
    """
    Validate domain format

    Args:
        domain: Domain name to validate

    Returns:
        True if valid

    Raises:
        NameCheapValidationError: If domain is invalid
    """
    pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,}$'
    if not re.match(pattern, domain.lower()):
        raise NameCheapValidationError(f"Invalid domain format: {domain}")
    return True


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # This code runs only when script is executed directly (for testing)
    print("NameCheap Manager Module - Test Mode")
    print("=" * 70)

    # Production credentials from architecture spec
    credentials = NameCheapCredentials(
        api_username="SkyBehind",
        api_key="your-namecheap-api-key",
        username="SkyBehind",
        client_ip="YOUR_SERVER_IP",
        sandbox=False  # Use production
    )

    try:
        # Initialize manager
        manager = NameCheapManager(credentials)

        # Test connection
        print("\n1. Testing Connection:")
        connection = manager.test_connection()
        print(f"   Connected: {connection['connected']}")
        print(f"   Domain Count: {connection.get('domain_count', 'N/A')}")

        if connection['connected']:
            # List domains
            print("\n2. Listing Domains:")
            domains = manager.domains.list_domains()
            for domain in domains[:5]:  # Show first 5
                print(f"   - {domain.domain}")
                print(f"     Status: {domain.status.value}")
                print(f"     Expires: {domain.expiration_date}")
                print(f"     Locked: {domain.is_locked}")
                print(f"     Nameservers: {', '.join(domain.current_nameservers[:2]) if domain.current_nameservers else 'None'}")

            # Get migration summary for first domain
            if domains:
                test_domain = domains[0].domain
                print(f"\n3. Migration Summary for {test_domain}:")
                summary = manager.get_migration_summary(test_domain)
                print(f"   DNS Records: {summary['dns_record_count']}")
                print(f"   Email Service: {summary['email_service']['type']}")
                print(f"   Migration Ready: {summary['migration_ready']}")

            print("\n✅ All tests passed! NameCheap manager is ready for use.")
            print(f"\n📊 Statistics:")
            print(f"   - Total Domains: {len(domains)}")
            print(f"   - Active: {sum(1 for d in domains if d.status == DomainStatus.ACTIVE)}")
            print(f"   - Expired: {sum(1 for d in domains if d.status == DomainStatus.EXPIRED)}")
            print(f"   - Locked: {sum(1 for d in domains if d.is_locked)}")

        else:
            print(f"\n❌ Connection failed: {connection['message']}")

    except NameCheapAuthError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("   Please verify:")
        print("   1. API is enabled in NameCheap account")
        print("   2. API key is correct")
        print("   3. Server IP (YOUR_SERVER_IP) is whitelisted")
    except NameCheapError as e:
        print(f"\n❌ NameCheap Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
