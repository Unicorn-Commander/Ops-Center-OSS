"""
Migration Wizard REST API Endpoints for UC-Cloud Ops-Center
Provides REST API for automated domain migration from NameCheap to Cloudflare

Epic 1.7: NameCheap Integration & Migration Workflow

Author: Backend API Developer Agent
Date: October 22, 2025
License: MIT
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re
import ipaddress
from enum import Enum

# Import managers
from namecheap_manager import (
    NameCheapManager,
    NameCheapError,
    NameCheapAPIError,
    NameCheapAuthError,
    NameCheapRateLimitError,
    NameCheapValidationError
)
from cloudflare_manager import (
    CloudflareManager,
    CloudflareError,
    CloudflareZoneLimitError
)

# Import authentication
from admin_subscriptions_api import require_admin

# Import rate limiting
from rate_limiter import check_rate_limit_manual

# Import universal credential helper
from get_credential import get_credential

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/migration", tags=["migration", "namecheap", "dns"])

# Initialize managers
import os
# Read credentials from database first, then environment
NAMECHEAP_API_KEY = get_credential("NAMECHEAP_API_KEY")
NAMECHEAP_USERNAME = get_credential("NAMECHEAP_USERNAME")
NAMECHEAP_CLIENT_IP = get_credential("NAMECHEAP_CLIENT_IP")
CLOUDFLARE_API_TOKEN = get_credential("CLOUDFLARE_API_TOKEN")

namecheap_manager = None
cloudflare_manager = None

if NAMECHEAP_API_KEY and NAMECHEAP_USERNAME:
    from namecheap_manager import NameCheapCredentials
    credentials = NameCheapCredentials(
        api_username=NAMECHEAP_USERNAME,
        api_key=NAMECHEAP_API_KEY,
        username=NAMECHEAP_USERNAME,
        client_ip=NAMECHEAP_CLIENT_IP or "127.0.0.1",
        sandbox=False
    )
    namecheap_manager = NameCheapManager(credentials)

if CLOUDFLARE_API_TOKEN:
    cloudflare_manager = CloudflareManager(api_token=CLOUDFLARE_API_TOKEN)


# ==================== Enums ====================

class MigrationStatus(str, Enum):
    """Migration job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class MigrationPhase(str, Enum):
    """Migration phase for individual domains"""
    QUEUED = "queued"
    ADDING_CF = "adding_cf"
    UPDATING_NS = "updating_ns"
    PROPAGATING = "propagating"
    COMPLETE = "complete"
    FAILED = "failed"


class EmailProvider(str, Enum):
    """Email service providers"""
    MICROSOFT365 = "microsoft365"
    NAMECHEAP_PRIVATE = "namecheap_private"
    GOOGLE_WORKSPACE = "google_workspace"
    EMAIL_FORWARDING = "email_forwarding"
    NONE = "none"


# ==================== Pydantic Request Models ====================

class DomainBulkCheckRequest(BaseModel):
    """Request model for bulk domain check"""
    domains: List[str] = Field(..., max_items=100, description="List of domain names")

    @validator('domains')
    def validate_domains(cls, v):
        """Validate domain list"""
        if not v:
            raise ValueError("Domain list cannot be empty")
        for domain in v:
            pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)*[a-z0-9-]{1,63}(?<!-)$'
            if not re.match(pattern, domain.lower()):
                raise ValueError(f"Invalid domain format: {domain}")
        return [d.lower() for d in v]


class BulkExportRequest(BaseModel):
    """Request model for bulk DNS export"""
    domains: List[str] = Field(..., max_items=50, description="List of domains to export")
    format: str = Field("json", description="Export format (json, csv, bind)")

    @validator('format')
    def validate_format(cls, v):
        """Validate export format"""
        valid_formats = ['json', 'csv', 'bind']
        if v.lower() not in valid_formats:
            raise ValueError(f"Format must be one of: {', '.join(valid_formats)}")
        return v.lower()


class MigrationPreviewRequest(BaseModel):
    """Request model for migration preview"""
    domains: List[str] = Field(..., max_items=50, description="List of domains to migrate")
    options: Dict[str, Any] = Field(default_factory=dict, description="Migration options")

    @validator('domains')
    def validate_domains(cls, v):
        """Validate domain list"""
        if not v:
            raise ValueError("Domain list cannot be empty")
        return [d.lower() for d in v]


class MigrationExecuteRequest(BaseModel):
    """Request model for migration execution"""
    migration_id: str = Field(..., description="Migration job ID from preview")
    confirm: bool = Field(..., description="Confirmation required")

    @validator('confirm')
    def validate_confirmation(cls, v):
        """Validate confirmation"""
        if not v:
            raise ValueError("Migration confirmation required")
        return v


class DNSValidationRequest(BaseModel):
    """Request model for DNS record validation"""
    domain: str = Field(..., description="Domain name")
    records: List[Dict[str, Any]] = Field(..., description="DNS records to validate")


# ==================== Pydantic Response Models ====================

class DomainInfoResponse(BaseModel):
    """Response model for domain information"""
    domain: str
    status: str
    nameservers: List[str]
    expiration_date: Optional[str]
    is_locked: bool
    whois_guard: bool
    migration_status: str


class EmailServiceResponse(BaseModel):
    """Response model for email service detection"""
    domain: str
    provider: EmailProvider
    mx_records: List[Dict[str, Any]]
    spf_record: Optional[str]
    dkim_records: List[str]
    dmarc_record: Optional[str]
    critical_records: List[Dict[str, Any]]


class DNSRecordResponse(BaseModel):
    """Response model for DNS record"""
    type: str
    name: str
    content: str
    ttl: int
    priority: Optional[int]


class MigrationStatusResponse(BaseModel):
    """Response model for migration status"""
    migration_id: str
    status: MigrationStatus
    progress: int
    total_domains: int
    completed_domains: int
    failed_domains: int
    errors: List[Dict[str, str]]
    rollback_available: bool
    estimated_completion: Optional[str]


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    domain: str
    dns_ok: bool
    ssl_ok: bool
    email_ok: bool
    website_ok: bool
    propagation_percent: float
    issues: List[str]


# ==================== Helper Functions ====================

def get_username_from_request(request: Request) -> str:
    """Extract username from authenticated request"""
    user_info = getattr(request.state, 'user_info', {})
    username = user_info.get('preferred_username') or user_info.get('email') or 'unknown'
    return username


def log_migration_action(action: str, details: str, username: str):
    """Log migration action for audit trail"""
    logger.info(f"MIGRATION ACTION: {action} by {username} - {details}")


# ==================== Phase 1: Discovery Endpoints ====================

@router.get("/namecheap/domains")
async def list_namecheap_domains(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (active, expired, locked)"),
    search: Optional[str] = Query(None, description="Search by domain name"),
    limit: int = Query(100, ge=1, le=500, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get all domains from NameCheap account

    **Rate Limit**: 10 requests per minute

    **Filters**:
    - status: Filter by domain status (active, expired, locked)
    - search: Search by domain name

    **Returns**: List of NameCheap domains with migration status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        domains_data = await namecheap_manager.list_domains(
            status=status,
            search=search,
            limit=limit,
            offset=offset
        )

        log_migration_action(
            "LIST_NAMECHEAP_DOMAINS",
            f"Retrieved {len(domains_data['domains'])} domains",
            username
        )

        return domains_data

    except NameCheapError as e:
        logger.error(f"Error listing NameCheap domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namecheap/domains/{domain}")
async def get_namecheap_domain(domain: str, request: Request):
    """
    Get detailed information about a specific domain from NameCheap

    **Rate Limit**: 10 requests per minute

    **Returns**: Domain details including DNS, nameservers, and status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        domain_info = await namecheap_manager.get_domain_info(domain)

        log_migration_action("GET_DOMAIN_INFO", f"Retrieved info for {domain}", username)

        return domain_info

    except NameCheapAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NameCheapError as e:
        logger.error(f"Error getting domain info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/namecheap/domains/bulk-check")
async def bulk_check_domains(
    check_request: DomainBulkCheckRequest,
    request: Request
):
    """
    Check availability and status of multiple domains

    **Rate Limit**: 5 requests per minute (write operation)

    **Returns**: Status and migration readiness for each domain
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        results = await namecheap_manager.bulk_check_domains(check_request.domains)

        log_migration_action(
            "BULK_CHECK_DOMAINS",
            f"Checked {len(check_request.domains)} domains",
            username
        )

        return {
            "success": True,
            "total": len(check_request.domains),
            "results": results
        }

    except NameCheapError as e:
        logger.error(f"Error bulk checking domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Phase 2: Export Endpoints ====================

@router.get("/namecheap/domains/{domain}/dns")
async def export_dns_records(
    domain: str,
    request: Request,
    format: str = Query("json", description="Export format (json, csv, bind)")
):
    """
    Export DNS records from NameCheap for a domain

    **Rate Limit**: 10 requests per minute

    **Formats**:
    - json: JSON format (default)
    - csv: CSV format
    - bind: BIND zone file format

    **Returns**: DNS records in requested format
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        dns_data = await namecheap_manager.export_dns_records(domain, format=format)

        log_migration_action(
            "EXPORT_DNS",
            f"Exported DNS for {domain} in {format} format",
            username
        )

        return dns_data

    except NameCheapAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NameCheapError as e:
        logger.error(f"Error exporting DNS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namecheap/domains/{domain}/email")
async def detect_email_service(domain: str, request: Request):
    """
    Detect email service provider for a domain

    **Rate Limit**: 10 requests per minute

    **Detects**:
    - Microsoft 365
    - NameCheap Private Email
    - Google Workspace
    - Email forwarding

    **Returns**: Email service details and critical records to preserve
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        email_info = await namecheap_manager.detect_email_service(domain)

        log_migration_action(
            "DETECT_EMAIL",
            f"Detected {email_info['provider']} for {domain}",
            username
        )

        return email_info

    except NameCheapError as e:
        logger.error(f"Error detecting email service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/namecheap/domains/bulk-export")
async def bulk_export_dns(
    export_request: BulkExportRequest,
    request: Request
):
    """
    Export DNS records for multiple domains

    **Rate Limit**: 5 requests per minute (write operation)

    **Returns**: DNS records for all requested domains
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        results = await namecheap_manager.bulk_export_dns(
            domains=export_request.domains,
            format=export_request.format
        )

        log_migration_action(
            "BULK_EXPORT_DNS",
            f"Exported DNS for {len(export_request.domains)} domains",
            username
        )

        return {
            "success": True,
            "format": export_request.format,
            "total": len(export_request.domains),
            "exports": results
        }

    except NameCheapError as e:
        logger.error(f"Error bulk exporting DNS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Phase 3: Review Endpoints ====================

@router.post("/migration/preview")
async def preview_migration(
    preview_request: MigrationPreviewRequest,
    request: Request
):
    """
    Preview migration plan before execution

    **Rate Limit**: 5 requests per minute (write operation)

    **Creates**:
    - Migration job record
    - DNS record preview
    - Email service validation
    - Nameserver update plan

    **Returns**: Migration preview ID and detailed plan
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager or not cloudflare_manager:
        raise HTTPException(status_code=503, detail="Migration services not configured")

    try:
        # Create migration preview
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        preview = await orchestrator.create_migration_preview(
            domains=preview_request.domains,
            options=preview_request.options,
            username=username
        )

        log_migration_action(
            "CREATE_MIGRATION_PREVIEW",
            f"Created preview for {len(preview_request.domains)} domains",
            username
        )

        return preview

    except Exception as e:
        logger.error(f"Error creating migration preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/preview/{migration_id}")
async def get_migration_preview(migration_id: str, request: Request):
    """
    Get details of a migration preview

    **Rate Limit**: 20 requests per minute

    **Returns**: Full migration plan with DNS records and warnings
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        preview = await orchestrator.get_migration_preview(migration_id)

        log_migration_action("GET_MIGRATION_PREVIEW", f"Retrieved preview {migration_id}", username)

        return preview

    except Exception as e:
        logger.error(f"Error getting migration preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/validate")
async def validate_migration(
    validation_request: DNSValidationRequest,
    request: Request
):
    """
    Validate DNS records before migration

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - Valid IP addresses
    - Valid hostnames
    - MX record priorities
    - Email service records

    **Returns**: Validation results with warnings and errors
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        validation = await orchestrator.validate_dns_records(
            domain=validation_request.domain,
            records=validation_request.records
        )

        log_migration_action(
            "VALIDATE_DNS",
            f"Validated {len(validation_request.records)} records for {validation_request.domain}",
            username
        )

        return validation

    except Exception as e:
        logger.error(f"Error validating DNS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Phase 4: Execute Endpoints ====================

@router.post("/migration/execute", status_code=201)
async def execute_migration(
    execute_request: MigrationExecuteRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Execute a migration job

    **Rate Limit**: 3 requests per minute (critical operation)

    **Process**:
    1. Add domains to Cloudflare (with queue handling)
    2. Import DNS records
    3. Update nameservers at NameCheap
    4. Monitor propagation

    **Returns**: Migration job ID and initial status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting (strict for critical operations)
    await check_rate_limit_manual(request, category="critical", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager or not cloudflare_manager:
        raise HTTPException(status_code=503, detail="Migration services not configured")

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        # Execute migration in background
        migration_job = await orchestrator.execute_migration(
            migration_id=execute_request.migration_id,
            username=username
        )

        # Add background task for monitoring
        background_tasks.add_task(
            orchestrator.monitor_migration_progress,
            migration_id=execute_request.migration_id
        )

        log_migration_action(
            "EXECUTE_MIGRATION",
            f"Started migration {execute_request.migration_id}",
            username
        )

        return {
            "success": True,
            "migration_id": execute_request.migration_id,
            "status": migration_job['status'],
            "total_domains": migration_job['total_domains'],
            "message": "Migration started. Monitor progress via /migration/{migration_id}/status"
        }

    except Exception as e:
        logger.error(f"Error executing migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/{migration_id}/status")
async def get_migration_status(migration_id: str, request: Request):
    """
    Get current status of a migration job

    **Rate Limit**: 30 requests per minute

    **Returns**: Real-time migration progress and status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        status = await orchestrator.get_migration_status(migration_id)

        log_migration_action("GET_MIGRATION_STATUS", f"Checked status {migration_id}", username)

        return status

    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/pause")
async def pause_migration(migration_id: str, request: Request):
    """
    Pause a running migration job

    **Rate Limit**: 5 requests per minute

    **Returns**: Updated migration status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.pause_migration(migration_id, username=username)

        log_migration_action("PAUSE_MIGRATION", f"Paused migration {migration_id}", username)

        return result

    except Exception as e:
        logger.error(f"Error pausing migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/resume")
async def resume_migration(
    migration_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Resume a paused migration job

    **Rate Limit**: 5 requests per minute

    **Returns**: Updated migration status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="write", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.resume_migration(migration_id, username=username)

        # Resume background monitoring
        background_tasks.add_task(
            orchestrator.monitor_migration_progress,
            migration_id=migration_id
        )

        log_migration_action("RESUME_MIGRATION", f"Resumed migration {migration_id}", username)

        return result

    except Exception as e:
        logger.error(f"Error resuming migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/rollback")
async def rollback_migration(migration_id: str, request: Request):
    """
    Rollback a migration (revert nameservers to original values)

    **Rate Limit**: 3 requests per minute (critical operation)

    **Warning**: This reverts nameservers at NameCheap but keeps Cloudflare zone

    **Returns**: Rollback status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="critical", is_admin=True)

    username = get_username_from_request(request)

    if not namecheap_manager:
        raise HTTPException(status_code=503, detail="NameCheap integration not configured")

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.rollback_migration(migration_id, username=username)

        log_migration_action(
            "ROLLBACK_MIGRATION",
            f"Rolled back migration {migration_id}",
            username
        )

        return result

    except Exception as e:
        logger.error(f"Error rolling back migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Phase 5: Verify Endpoints ====================

@router.post("/migration/{migration_id}/verify/dns")
async def verify_dns_propagation(migration_id: str, request: Request):
    """
    Check DNS propagation status across multiple resolvers

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - Google DNS (8.8.8.8)
    - Cloudflare DNS (1.1.1.1)
    - Quad9 DNS (9.9.9.9)
    - OpenDNS (208.67.222.222)

    **Returns**: Propagation status per resolver and overall percentage
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.verify_dns_propagation(migration_id)

        log_migration_action(
            "VERIFY_DNS_PROPAGATION",
            f"Checked DNS propagation for migration {migration_id}",
            username
        )

        return result

    except Exception as e:
        logger.error(f"Error verifying DNS propagation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/verify/ssl")
async def verify_ssl_certificates(migration_id: str, request: Request):
    """
    Verify SSL certificates for migrated domains

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - SSL certificate issued
    - Certificate valid
    - Certificate matches domain
    - Certificate issuer (Cloudflare)

    **Returns**: SSL status per domain
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.verify_ssl_certificates(migration_id)

        log_migration_action(
            "VERIFY_SSL",
            f"Verified SSL for migration {migration_id}",
            username
        )

        return result

    except Exception as e:
        logger.error(f"Error verifying SSL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/verify/email")
async def verify_email_functionality(migration_id: str, request: Request):
    """
    Test email delivery for migrated domains

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - MX records present
    - SPF record configured
    - DMARC record configured
    - DKIM records present

    **Returns**: Email service health status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.verify_email_functionality(migration_id)

        log_migration_action(
            "VERIFY_EMAIL",
            f"Verified email for migration {migration_id}",
            username
        )

        return result

    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/{migration_id}/verify/website")
async def verify_website_accessibility(migration_id: str, request: Request):
    """
    Check website accessibility for migrated domains

    **Rate Limit**: 10 requests per minute

    **Checks**:
    - HTTP accessible (with redirect to HTTPS)
    - HTTPS accessible
    - Valid response codes
    - Cloudflare proxy active

    **Returns**: Website accessibility status
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        result = await orchestrator.verify_website_accessibility(migration_id)

        log_migration_action(
            "VERIFY_WEBSITE",
            f"Verified website for migration {migration_id}",
            username
        )

        return result

    except Exception as e:
        logger.error(f"Error verifying website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/{migration_id}/health")
async def get_migration_health(migration_id: str, request: Request):
    """
    Get overall health check for a migration

    **Rate Limit**: 20 requests per minute

    **Combines**:
    - DNS propagation status
    - SSL certificate status
    - Email functionality
    - Website accessibility

    **Returns**: Comprehensive health check results
    """
    # Authentication required
    await require_admin(request)

    # Rate limiting
    await check_rate_limit_manual(request, category="read", is_admin=True)

    username = get_username_from_request(request)

    try:
        from migration_orchestrator import MigrationOrchestrator

        orchestrator = MigrationOrchestrator(
            namecheap_manager=namecheap_manager,
            cloudflare_manager=cloudflare_manager
        )

        health = await orchestrator.get_migration_health(migration_id)

        log_migration_action(
            "GET_MIGRATION_HEALTH",
            f"Retrieved health for migration {migration_id}",
            username
        )

        return health

    except Exception as e:
        logger.error(f"Error getting migration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@router.get("/health")
async def migration_health_check():
    """
    Health check endpoint for migration API

    No authentication required for monitoring systems

    **Returns**: Health status and service connectivity
    """
    try:
        # Check service connectivity
        namecheap_ok = namecheap_manager is not None
        cloudflare_ok = cloudflare_manager is not None

        if namecheap_manager:
            namecheap_ok = await namecheap_manager.check_connectivity()

        if cloudflare_manager:
            cloudflare_ok = await cloudflare_manager.check_connectivity()

        status = "healthy" if (namecheap_ok and cloudflare_ok) else "degraded"

        return {
            "status": status,
            "namecheap_api_connected": namecheap_ok,
            "cloudflare_api_connected": cloudflare_ok,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
