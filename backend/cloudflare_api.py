"""
Cloudflare DNS Management API Endpoints for UC-Cloud Ops-Center
Provides REST API for managing Cloudflare zones and DNS records with authentication and rate limiting

Epic 1.6: Cloudflare DNS Management

Author: Backend API Developer Agent
Date: October 22, 2025
License: MIT
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re
import ipaddress

# Import Cloudflare manager
from cloudflare_manager import (
    CloudflareManager,
    CloudflareError,
    CloudflareAPIError,
    CloudflareAuthError,
    CloudflareRateLimitError as RateLimitError,
    CloudflareZoneLimitError,
    CloudflareValidationError
)

# Alias for backwards compatibility
ZoneNotFoundError = CloudflareAPIError

# Import authentication
from admin_subscriptions_api import require_admin

# Import rate limiting
from rate_limiter import check_rate_limit_manual

# Import credential integration
from cloudflare_credentials_integration import get_cloudflare_token

# Import database connection
from database.connection import get_db_pool

# Import universal credential helper
from get_credential import get_credential

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/cloudflare", tags=["cloudflare", "dns", "infrastructure"])

# Initialize Cloudflare manager with API token from database or environment
import os

# Lazy initialization function for Cloudflare manager
def get_cloudflare_manager():
    """
    Get or create Cloudflare manager with lazy initialization.

    This function checks for API token in database first, then environment variables,
    then creates a CloudflareManager instance with proper error handling.

    Returns:
        CloudflareManager: Initialized Cloudflare manager instance

    Raises:
        CloudflareAuthError: If API token is not configured
    """
    # Try database first, then environment variable
    token = get_credential("CLOUDFLARE_API_TOKEN")

    if not token:
        error_message = (
            "Cloudflare API token not configured. "
            "Please add CLOUDFLARE_API_TOKEN via Platform Settings or .env.auth file. "
            "See /docs/CLOUDFLARE_SETUP.md for detailed instructions."
        )
        logger.error(f"Cloudflare API initialization failed: {error_message}")
        raise CloudflareAuthError(error_message)

    logger.info(f"Initializing Cloudflare manager with token (length: {len(token)})")
    return CloudflareManager(api_token=token)


# ==================== Pydantic Request Models ====================

class ZoneCreateRequest(BaseModel):
    """Request model for creating a Cloudflare zone"""
    domain: str = Field(..., min_length=3, max_length=253, description="Domain name (e.g., example.com)")
    account_id: Optional[str] = Field(None, description="Cloudflare account ID (optional)")
    jump_start: bool = Field(True, description="Auto-import DNS records from current nameservers")
    priority: str = Field("normal", description="Queue priority (critical, high, normal, low)")

    @validator('domain')
    def validate_domain(cls, v):
        """Validate domain format (RFC 1035)"""
        # Convert to lowercase
        v = v.lower().strip()

        # RFC 1035 hostname validation
        pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)*[a-z0-9-]{1,63}(?<!-)$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain format: {v}")

        if len(v) > 253:
            raise ValueError("Domain name too long (max 253 characters)")

        # Check for invalid characters
        if '..' in v or v.startswith('.') or v.endswith('.'):
            raise ValueError("Invalid domain format")

        return v

    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority level"""
        valid_priorities = ['critical', 'high', 'normal', 'low']
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()


class DNSRecordCreateRequest(BaseModel):
    """Request model for creating DNS record"""
    type: str = Field(..., description="Record type (A, AAAA, CNAME, MX, TXT, SRV, CAA)")
    name: str = Field(..., max_length=255, description="Record name (@ for root, or subdomain)")
    content: str = Field(..., description="Record content (IP, hostname, text, etc.)")
    ttl: int = Field(1, ge=1, description="TTL in seconds (1 = auto)")
    proxied: bool = Field(False, description="Proxy through Cloudflare (orange cloud)")
    priority: Optional[int] = Field(None, ge=0, le=65535, description="Priority (for MX and SRV records)")

    @validator('type')
    def validate_type(cls, v):
        """Validate DNS record type"""
        valid_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'CAA', 'NS']
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid record type. Must be one of: {', '.join(valid_types)}")
        return v_upper

    @validator('ttl')
    def validate_ttl(cls, v):
        """Validate TTL value"""
        if v != 1 and (v < 120 or v > 86400):
            raise ValueError("TTL must be 1 (auto) or between 120 and 86400 seconds")
        return v

    @validator('content')
    def validate_content(cls, v, values):
        """Validate record content based on type"""
        if 'type' not in values:
            return v

        record_type = values['type']

        # A record validation
        if record_type == 'A':
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 address: {v}")

        # AAAA record validation
        elif record_type == 'AAAA':
            try:
                ipaddress.IPv6Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv6 address: {v}")

        # CNAME, MX, NS validation (hostname format)
        elif record_type in ['CNAME', 'MX', 'NS']:
            hostname_pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)*[a-z0-9-]{1,63}(?<!-)$'
            if not re.match(hostname_pattern, v.lower()):
                raise ValueError(f"Invalid hostname format: {v}")

        return v


class DNSRecordUpdateRequest(BaseModel):
    """Request model for updating DNS record"""
    content: Optional[str] = Field(None, description="New record content")
    ttl: Optional[int] = Field(None, ge=1, description="New TTL (1 = auto)")
    proxied: Optional[bool] = Field(None, description="Proxy status")
    priority: Optional[int] = Field(None, ge=0, le=65535, description="New priority")

    @validator('ttl')
    def validate_ttl(cls, v):
        """Validate TTL value"""
        if v is not None and v != 1 and (v < 120 or v > 86400):
            raise ValueError("TTL must be 1 (auto) or between 120 and 86400 seconds")
        return v


class BulkDomainRequest(BaseModel):
    """Request model for bulk domain addition"""
    domains: List[Dict[str, str]] = Field(..., max_items=100, description="List of domains with priority")

    @validator('domains')
    def validate_domains(cls, v):
        """Validate domain list format"""
        if not v:
            raise ValueError("Domain list cannot be empty")

        for item in v:
            if 'domain' not in item:
                raise ValueError("Each item must have 'domain' field")

            # Validate domain format
            domain = item['domain'].lower().strip()
            pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)*[a-z0-9-]{1,63}(?<!-)$'
            if not re.match(pattern, domain):
                raise ValueError(f"Invalid domain format: {domain}")

        return v


class NameserverUpdateRequest(BaseModel):
    """Request model for updating nameservers"""
    nameservers: List[str] = Field(..., min_items=2, max_items=4, description="Nameserver hostnames")

    @validator('nameservers')
    def validate_nameservers(cls, v):
        """Validate nameserver format"""
        for ns in v:
            pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)*[a-z0-9-]{1,63}(?<!-)$'
            if not re.match(pattern, ns.lower()):
                raise ValueError(f"Invalid nameserver format: {ns}")
        return v


class BulkDNSRecordRequest(BaseModel):
    """Request model for bulk DNS record creation"""
    records: List[Dict[str, Any]] = Field(..., max_items=100, description="List of DNS records")


# ==================== Pydantic Response Models ====================

class ZoneResponse(BaseModel):
    """Response model for zone details"""
    id: str
    name: str
    status: str
    nameservers: List[str]
    created_on: str
    activated_on: Optional[str]
    plan: Dict[str, str]


class DNSRecordResponse(BaseModel):
    """Response model for DNS record"""
    id: str
    type: str
    name: str
    content: str
    ttl: int
    proxied: bool
    priority: Optional[int]
    created_on: str
    modified_on: str


class PropagationStatusResponse(BaseModel):
    """Response model for propagation status"""
    domain: str
    status: str
    checks: Dict[str, bool]
    propagation_percent: float
    timestamp: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]]


# ==================== Helper Functions ====================

def get_username_from_request(request: Request) -> str:
    """Extract username from authenticated request"""
    user_info = getattr(request.state, 'user_info', {})
    username = user_info.get('preferred_username') or user_info.get('email') or 'unknown'
    return username


def log_cloudflare_action(action: str, details: str, username: str):
    """Log Cloudflare action for audit trail"""
    logger.info(f"CLOUDFLARE ACTION: {action} by {username} - {details}")


# ==================== Zone Management Endpoints ====================

@router.get("/zones")
async def list_zones(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (pending, active, deactivated)"),
    search: Optional[str] = Query(None, description="Search by domain name"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get all Cloudflare zones with optional filtering

    **Rate Limit**: 30 requests per minute

    **Filters**:
    - status: Filter by zone status (pending, active, deactivated)
    - search: Search by domain name
    - limit: Maximum results per page (1-100)
    - offset: Pagination offset

    **Returns**: List of zones with metadata
    """
    # Authentication required
    admin = await require_admin(request)
    user_id = admin.get("user_id") or admin.get("sub") or admin.get("id", "unknown")

    # Rate limiting (read operations - 30/minute)
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        # Get Cloudflare manager with lazy initialization
        manager = get_cloudflare_manager()

        # Get zones from Cloudflare
        zones_data = await manager.list_zones(
            status=status,
            search=search,
            limit=limit,
            offset=offset
        )

        log_cloudflare_action(
            "LIST_ZONES",
            f"Retrieved {len(zones_data['zones'])} zones (filters: status={status}, search={search})",
            username
        )

        return zones_data

    except CloudflareAuthError as e:
        # Return mock data if Cloudflare credentials not configured
        logger.warning(f"Cloudflare authentication failed, returning mock data: {e}")
        return {
            "zones": [
                {
                    "id": "mock-zone-1",
                    "name": "your-domain.com",
                    "status": "active",
                    "type": "full",
                    "name_servers": ["ns1.example.com", "ns2.example.com"],
                    "created_on": "2025-01-01T00:00:00Z",
                    "development_mode": False
                },
                {
                    "id": "mock-zone-2",
                    "name": "centerdeep.online",
                    "status": "active",
                    "type": "full",
                    "name_servers": ["ns1.example.com", "ns2.example.com"],
                    "created_on": "2025-01-01T00:00:00Z",
                    "development_mode": False
                }
            ],
            "total": 2,
            "source": "mock_data",
            "message": "Cloudflare credentials not configured. Showing mock data. Configure API token in Platform Settings."
        }
    except CloudflareError as e:
        logger.error(f"Error listing zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing zones: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/zones/{zone_id}")
async def get_zone(zone_id: str, request: Request):
    """
    Get detailed information about a specific zone

    **Rate Limit**: 30 requests per minute

    **Returns**: Zone details including DNS record count and status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        zone_data = await cloudflare_manager.get_zone(zone_id)

        log_cloudflare_action("GET_ZONE", f"Retrieved zone details for {zone_data['name']}", username)

        return zone_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error getting zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting zone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/zones", status_code=201)
async def create_zone(zone_request: ZoneCreateRequest, request: Request):
    """
    Create a new Cloudflare zone

    **Rate Limit**: 5 requests per minute (write operation)

    **Cloudflare Free Plan Limit**: Maximum 3 pending zones at once

    **Behavior**:
    - If under 3 pending zones: Zone created immediately
    - If at 3 pending zones: Zone added to queue

    **Returns**: Zone details or queue status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting (write operations - 5/minute)
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.create_zone(
            domain=zone_request.domain,
            account_id=zone_request.account_id,
            jump_start=zone_request.jump_start,
            priority=zone_request.priority,
            username=username
        )

        log_cloudflare_action(
            "CREATE_ZONE",
            f"Created zone {zone_request.domain} (priority: {zone_request.priority})",
            username
        )

        # Check if queued
        if result.get('status') == 'queued':
            return {
                "success": True,
                "queued": True,
                "domain": zone_request.domain,
                "queue_position": result.get('queue_position'),
                "estimated_wait": result.get('estimated_wait'),
                "message": f"Zone added to queue (position {result.get('queue_position')}). Maximum 3 pending zones at once."
            }

        return {
            "success": True,
            "zone_id": result['id'],
            "domain": result['name'],
            "status": result['status'],
            "nameservers": result['nameservers'],
            "message": f"Zone created. Update nameservers at your registrar to activate."
        }

    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except CloudflareValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating zone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: str, request: Request):
    """
    Delete a Cloudflare zone

    **Rate Limit**: 5 requests per minute (write operation)

    **Warning**: This permanently deletes the zone and all DNS records!

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        zone_info = await cloudflare_manager.delete_zone(zone_id, username=username)

        log_cloudflare_action("DELETE_ZONE", f"Deleted zone {zone_info['domain']}", username)

        return {
            "success": True,
            "message": f"Zone {zone_info['domain']} deleted successfully"
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error deleting zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting zone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/zones/{zone_id}/activate")
async def activate_zone(zone_id: str, request: Request):
    """
    Check and activate a pending zone

    **Rate Limit**: 10 requests per minute

    **Purpose**: Manually trigger activation check after nameservers are updated

    **Returns**: Updated zone status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.check_zone_activation(zone_id, username=username)

        log_cloudflare_action("ACTIVATE_ZONE", f"Checked activation for zone {result['domain']}", username)

        return result

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error activating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error activating zone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/zones/{zone_id}/status")
async def get_zone_status(zone_id: str, request: Request):
    """
    Get current status of a zone (pending, active, deactivated)

    **Rate Limit**: 30 requests per minute

    **Returns**: Zone status with activation details
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        status_data = await cloudflare_manager.get_zone_status(zone_id)

        log_cloudflare_action("GET_ZONE_STATUS", f"Retrieved status for zone {status_data['domain']}", username)

        return status_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error getting zone status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting zone status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== DNS Record Management Endpoints ====================

@router.get("/zones/{zone_id}/dns")
async def list_dns_records(
    zone_id: str,
    request: Request,
    type: Optional[str] = Query(None, description="Filter by record type (A, AAAA, CNAME, etc.)"),
    search: Optional[str] = Query(None, description="Search by name or content"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List DNS records for a zone

    **Rate Limit**: 30 requests per minute

    **Filters**:
    - type: Filter by record type (A, AAAA, CNAME, MX, TXT, SRV, CAA)
    - search: Search by name or content

    **Returns**: List of DNS records
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        records_data = await cloudflare_manager.list_dns_records(
            zone_id=zone_id,
            record_type=type,
            search=search,
            limit=limit,
            offset=offset
        )

        log_cloudflare_action(
            "LIST_DNS_RECORDS",
            f"Retrieved {len(records_data['records'])} DNS records for zone {zone_id}",
            username
        )

        return records_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error listing DNS records: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing DNS records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/zones/{zone_id}/dns", status_code=201)
async def create_dns_record(
    zone_id: str,
    record: DNSRecordCreateRequest,
    request: Request
):
    """
    Create a new DNS record

    **Rate Limit**: 10 requests per minute (write operation)

    **Record Types Supported**:
    - A: IPv4 address
    - AAAA: IPv6 address
    - CNAME: Canonical name (alias)
    - MX: Mail server (requires priority)
    - TXT: Text record (SPF, DKIM, DMARC, verification)
    - SRV: Service record (requires priority)
    - CAA: Certificate authority authorization

    **Returns**: Created DNS record details
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.create_dns_record(
            zone_id=zone_id,
            record_type=record.type,
            name=record.name,
            content=record.content,
            ttl=record.ttl,
            proxied=record.proxied,
            priority=record.priority,
            username=username
        )

        log_cloudflare_action(
            "CREATE_DNS_RECORD",
            f"Created {record.type} record: {record.name} → {record.content}",
            username
        )

        return {
            "success": True,
            "record": result,
            "message": f"{record.type} record created successfully"
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error creating DNS record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating DNS record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/zones/{zone_id}/dns/{record_id}")
async def update_dns_record(
    zone_id: str,
    record_id: str,
    record_update: DNSRecordUpdateRequest,
    request: Request
):
    """
    Update an existing DNS record

    **Rate Limit**: 10 requests per minute (write operation)

    **Updatable Fields**:
    - content: Record content (IP, hostname, text)
    - ttl: Time to live
    - proxied: Proxy through Cloudflare
    - priority: Priority (for MX and SRV records)

    **Returns**: Updated DNS record details
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.update_dns_record(
            zone_id=zone_id,
            record_id=record_id,
            content=record_update.content,
            ttl=record_update.ttl,
            proxied=record_update.proxied,
            priority=record_update.priority,
            username=username
        )

        log_cloudflare_action(
            "UPDATE_DNS_RECORD",
            f"Updated DNS record {record_id} in zone {zone_id}",
            username
        )

        return {
            "success": True,
            "record": result,
            "message": "DNS record updated successfully"
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error updating DNS record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating DNS record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/zones/{zone_id}/dns/{record_id}")
async def delete_dns_record(zone_id: str, record_id: str, request: Request):
    """
    Delete a DNS record

    **Rate Limit**: 10 requests per minute (write operation)

    **Warning**: Email-related records (MX, SPF, DKIM, DMARC) will show a warning

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.delete_dns_record(
            zone_id=zone_id,
            record_id=record_id,
            username=username
        )

        log_cloudflare_action(
            "DELETE_DNS_RECORD",
            f"Deleted DNS record {record_id} from zone {zone_id}",
            username
        )

        return {
            "success": True,
            "message": "DNS record deleted successfully",
            "warnings": result.get('warnings', [])
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error deleting DNS record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting DNS record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Nameserver Management ====================

@router.get("/zones/{zone_id}/nameservers")
async def get_nameservers(zone_id: str, request: Request):
    """
    Get assigned Cloudflare nameservers for a zone

    **Rate Limit**: 30 requests per minute

    **Returns**: Nameserver list with copy-to-clipboard support
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        nameservers = await cloudflare_manager.get_nameservers(zone_id)

        log_cloudflare_action("GET_NAMESERVERS", f"Retrieved nameservers for zone {zone_id}", username)

        return {
            "success": True,
            "zone_id": zone_id,
            "nameservers": nameservers['nameservers'],
            "instructions": "Update these nameservers at your domain registrar to activate the zone"
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error getting nameservers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting nameservers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/zones/{zone_id}/nameservers")
async def update_nameservers(
    zone_id: str,
    nameserver_request: NameserverUpdateRequest,
    request: Request
):
    """
    Update nameservers for a zone (advanced operation)

    **Rate Limit**: 5 requests per minute (write operation)

    **Warning**: This is rarely needed. Usually nameservers are assigned by Cloudflare.

    **Returns**: Updated nameserver list
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        result = await cloudflare_manager.update_nameservers(
            zone_id=zone_id,
            nameservers=nameserver_request.nameservers,
            username=username
        )

        log_cloudflare_action(
            "UPDATE_NAMESERVERS",
            f"Updated nameservers for zone {zone_id}",
            username
        )

        return {
            "success": True,
            "nameservers": result['nameservers'],
            "message": "Nameservers updated successfully"
        }

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error updating nameservers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating nameservers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Propagation & Analytics ====================

@router.get("/propagation/{zone_id}")
async def check_propagation(zone_id: str, request: Request):
    """
    Check DNS propagation status for a zone

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - Google DNS (8.8.8.8)
    - Cloudflare DNS (1.1.1.1)
    - Quad9 DNS (9.9.9.9)
    - OpenDNS (208.67.222.222)

    **Returns**: Propagation status across multiple DNS resolvers
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        propagation_data = await cloudflare_manager.check_propagation(zone_id)

        log_cloudflare_action(
            "CHECK_PROPAGATION",
            f"Checked propagation for zone {zone_id} ({propagation_data['propagation_percent']}% propagated)",
            username
        )

        return propagation_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error checking propagation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error checking propagation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/zones/{zone_id}/ssl")
async def get_ssl_status(zone_id: str, request: Request):
    """
    Get SSL/TLS status for a zone

    **Rate Limit**: 20 requests per minute

    **Returns**: SSL certificate status and configuration
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        ssl_data = await cloudflare_manager.get_ssl_status(zone_id)

        log_cloudflare_action("GET_SSL_STATUS", f"Retrieved SSL status for zone {zone_id}", username)

        return ssl_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error getting SSL status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting SSL status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/zones/{zone_id}/analytics")
async def get_zone_analytics(
    zone_id: str,
    request: Request,
    since: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    until: Optional[str] = Query(None, description="End date (ISO 8601)")
):
    """
    Get analytics data for a zone

    **Rate Limit**: 20 requests per minute

    **Metrics**:
    - Total requests
    - Bandwidth usage
    - Threat mitigation
    - Cache hit rate

    **Returns**: Analytics data for specified time period
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        analytics_data = await cloudflare_manager.get_zone_analytics(
            zone_id=zone_id,
            since=since,
            until=until
        )

        log_cloudflare_action("GET_ZONE_ANALYTICS", f"Retrieved analytics for zone {zone_id}", username)

        return analytics_data

    except ZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CloudflareError as e:
        logger.error(f"Error getting zone analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting zone analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Health Check ====================

@router.get("/health")
async def cloudflare_health_check():
    """
    Health check endpoint for Cloudflare API

    No authentication required for monitoring systems

    **Returns**: Health status and API connectivity
    """
    try:
        # Try to get Cloudflare manager
        manager = get_cloudflare_manager()

        # Check Cloudflare API connectivity by getting account status
        account_status = manager.get_account_status()
        is_connected = account_status.get("api_connected", False)

        return {
            "status": "healthy" if is_connected else "degraded",
            "cloudflare_api_connected": is_connected,
            "timestamp": datetime.now().isoformat()
        }

    except CloudflareAuthError as e:
        # Token not configured - this is expected if user hasn't set it up yet
        logger.warning(f"Cloudflare health check: {str(e)}")
        return {
            "status": "not_configured",
            "cloudflare_api_connected": False,
            "error": "API token not configured",
            "message": "See /docs/CLOUDFLARE_SETUP.md for setup instructions",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "cloudflare_api_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
