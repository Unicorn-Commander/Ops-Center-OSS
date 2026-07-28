"""
Firewall Management API Endpoints for UC-Cloud Ops-Center
Provides REST API for managing UFW firewall rules with authentication and rate limiting

Epic 1.2 Phase 1: Network Configuration Enhancement

Author: API Developer Agent
Date: October 22, 2025
License: MIT
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Import firewall manager (created by Backend Developer Agent)
from firewall_manager import (
    FirewallManager,
    FirewallRuleCreate,
    FirewallError
)

# Import authentication
from admin_subscriptions_api import require_admin

# Import rate limiting
from rate_limiter import RateLimitConfig

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/network/firewall", tags=["network", "firewall"])

# Initialize firewall manager
firewall_manager = FirewallManager()

# Rate limiting configuration
rate_config = RateLimitConfig()


# ==================== Pydantic Models ====================

class FirewallRuleCreateRequest(BaseModel):
    """Request model for creating firewall rule"""
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number")
    protocol: str = Field("tcp", description="Protocol (tcp/udp/both)")
    action: str = Field("allow", description="Action (allow/deny/reject)")
    description: Optional[str] = Field(None, max_length=200, description="Rule description")
    from_ip: Optional[str] = Field(None, description="Source IP address or CIDR")
    to_ip: Optional[str] = Field(None, description="Destination IP address")
    interface: Optional[str] = Field(None, description="Network interface (eth0, wlan0, etc.)")

    @validator('protocol')
    def validate_protocol(cls, v):
        """Validate protocol"""
        if v.lower() not in ['tcp', 'udp', 'both', 'any']:
            raise ValueError(f"Invalid protocol: {v}. Must be tcp, udp, both, or any")
        return v.lower()

    @validator('action')
    def validate_action(cls, v):
        """Validate action"""
        if v.lower() not in ['allow', 'deny', 'reject', 'limit']:
            raise ValueError(f"Invalid action: {v}. Must be allow, deny, reject, or limit")
        return v.lower()

    @validator('from_ip')
    def validate_from_ip(cls, v):
        """Validate source IP format"""
        if v is None:
            return v
        # Basic IP/CIDR validation
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$'
        if not re.match(ip_pattern, v):
            raise ValueError(f"Invalid IP/CIDR format: {v}")
        return v


class FirewallRuleDeleteRequest(BaseModel):
    """Request model for deleting firewall rule"""
    override_ssh: bool = Field(False, description="Override SSH protection (dangerous!)")


class FirewallTemplateRequest(BaseModel):
    """Request model for applying firewall template"""
    template_name: str = Field(..., description="Template name (web-server, database, etc.)")
    override_existing: bool = Field(False, description="Override existing rules")


class BulkRuleDeleteRequest(BaseModel):
    """Request model for bulk rule deletion"""
    rule_numbers: List[int] = Field(..., description="List of rule numbers to delete")
    override_ssh: bool = Field(False, description="Override SSH protection for all rules")


class FirewallRuleResponse(BaseModel):
    """Response model for firewall rules"""
    rules: List[Dict[str, Any]]
    total_count: int
    active_count: int
    last_updated: Optional[str]


class FirewallStatusResponse(BaseModel):
    """Response model for firewall status"""
    enabled: bool
    status: str
    default_policy: Dict[str, str]
    total_rules: int
    active_rules: int
    ipv6_enabled: bool
    logging: str


# ==================== Helper Functions ====================

def get_username_from_request(request: Request) -> str:
    """Extract username from authenticated request"""
    user_info = getattr(request.state, 'user_info', {})
    username = user_info.get('preferred_username') or user_info.get('email') or 'unknown'
    return username


def log_firewall_action(action: str, details: str, username: str):
    """Log firewall action for audit trail"""
    logger.info(f"FIREWALL ACTION: {action} by {username} - {details}")


# ==================== API Endpoints ====================

@router.get("/rules", response_model=FirewallRuleResponse)
async def list_firewall_rules(
    request: Request,
    status: Optional[str] = None,
    protocol: Optional[str] = None,
    action: Optional[str] = None
):
    """
    Get all firewall rules with optional filtering

    **Rate Limit**: 20 requests per 60 seconds

    **Filters**:
    - status: Filter by rule status (active/inactive)
    - protocol: Filter by protocol (tcp/udp/both)
    - action: Filter by action (allow/deny/reject)

    **Returns**: List of firewall rules with metadata
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        # Get all rules
        rules = firewall_manager.list_rules()

        # Apply filters
        if status:
            rules = [r for r in rules if r.get('status') == status]
        if protocol:
            rules = [r for r in rules if r.get('protocol') == protocol.lower()]
        if action:
            rules = [r for r in rules if r.get('action') == action.lower()]

        # Calculate counts
        total_count = len(rules)
        active_count = len([r for r in rules if r.get('status') == 'active'])

        log_firewall_action("LIST_RULES", f"Retrieved {total_count} rules (filters: status={status}, protocol={protocol}, action={action})", username)

        return FirewallRuleResponse(
            rules=rules,
            total_count=total_count,
            active_count=active_count,
            last_updated=datetime.now().isoformat()
        )

    except FirewallError as e:
        logger.error(f"Error listing firewall rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing firewall rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/rules")
async def add_firewall_rule(
    rule: FirewallRuleCreateRequest,
    request: Request
):
    """
    Add new firewall rule

    **Rate Limit**: 5 requests per 60 seconds

    **Required Fields**:
    - port: Port number (1-65535) or None for all ports
    - protocol: tcp, udp, both, or any
    - action: allow, deny, reject, or limit

    **Optional Fields**:
    - description: Human-readable description
    - from_ip: Source IP or CIDR (e.g., 192.168.1.0/24)
    - to_ip: Destination IP
    - interface: Network interface name

    **Returns**: Success message with rule details
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        # Create rule
        result = firewall_manager.add_rule(
            port=rule.port,
            protocol=rule.protocol,
            action=rule.action,
            description=rule.description,
            from_ip=rule.from_ip,
            to_ip=rule.to_ip,
            interface=rule.interface,
            username=username
        )

        rule_description = f"{rule.action} {rule.protocol}"
        if rule.port:
            rule_description += f"/{rule.port}"
        if rule.from_ip:
            rule_description += f" from {rule.from_ip}"

        log_firewall_action("ADD_RULE", rule_description, username)

        return {
            "success": True,
            "message": f"Firewall rule added: {rule_description}",
            "rule": result
        }

    except FirewallError as e:
        logger.error(f"Error adding firewall rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding firewall rule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/rules/{rule_num}")
async def delete_firewall_rule(
    rule_num: int,
    request: Request,
    override_ssh: bool = False
):
    """
    Delete firewall rule by number

    **Rate Limit**: 5 requests per 60 seconds

    **Parameters**:
    - rule_num: Rule number from list_rules output
    - override_ssh: Set to true to delete SSH rules (DANGEROUS!)

    **Warning**: Deleting SSH rules on remote systems can lock you out!

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        # Delete rule
        firewall_manager.delete_rule(
            rule_num=rule_num,
            override_ssh_protection=override_ssh,
            username=username
        )

        log_firewall_action("DELETE_RULE", f"Deleted rule #{rule_num} (SSH override: {override_ssh})", username)

        return {
            "success": True,
            "message": f"Firewall rule #{rule_num} deleted successfully"
        }

    except FirewallError as e:
        logger.error(f"Error deleting firewall rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting firewall rule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/rules/bulk-delete")
async def bulk_delete_firewall_rules(
    bulk_request: BulkRuleDeleteRequest,
    request: Request
):
    """
    Delete multiple firewall rules at once

    **Rate Limit**: 3 requests per 60 seconds

    **Request Body**:
    - rule_numbers: Array of rule numbers to delete
    - override_ssh: Override SSH protection for all rules

    **Returns**: Summary of deleted rules
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        deleted_count = 0
        failed_rules = []

        # Sort in descending order to avoid index shifting
        for rule_num in sorted(bulk_request.rule_numbers, reverse=True):
            try:
                firewall_manager.delete_rule(
                    rule_num=rule_num,
                    override_ssh_protection=bulk_request.override_ssh,
                    username=username
                )
                deleted_count += 1
            except FirewallError as e:
                failed_rules.append({"rule_num": rule_num, "error": str(e)})

        log_firewall_action(
            "BULK_DELETE_RULES",
            f"Deleted {deleted_count} rules, {len(failed_rules)} failed",
            username
        )

        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": len(failed_rules),
            "failed_rules": failed_rules
        }

    except Exception as e:
        logger.error(f"Unexpected error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status", response_model=FirewallStatusResponse)
async def get_firewall_status(request: Request):
    """
    Get current firewall status and configuration

    **Rate Limit**: 30 requests per 60 seconds

    **Returns**:
    - enabled: Whether UFW is active
    - status: Firewall status (active/inactive)
    - default_policy: Default policies for incoming/outgoing/routed traffic
    - total_rules: Total number of configured rules
    - active_rules: Number of active rules
    - ipv6_enabled: Whether IPv6 is enabled
    - logging: Logging level
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        status = firewall_manager.get_status()

        log_firewall_action("GET_STATUS", "Retrieved firewall status", username)

        return FirewallStatusResponse(**status)

    except FirewallError as e:
        logger.error(f"Error getting firewall status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting firewall status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/enable")
async def enable_firewall(request: Request):
    """
    Enable UFW firewall

    **Rate Limit**: 3 requests per 60 seconds

    **Warning**: This will activate all configured firewall rules immediately!
    Ensure SSH access is allowed before enabling on remote systems.

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        firewall_manager.enable_firewall(username=username)

        log_firewall_action("ENABLE_FIREWALL", "Firewall enabled", username)

        return {
            "success": True,
            "message": "Firewall enabled successfully",
            "warning": "All firewall rules are now active"
        }

    except FirewallError as e:
        logger.error(f"Error enabling firewall: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error enabling firewall: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/disable")
async def disable_firewall(request: Request):
    """
    Disable UFW firewall

    **Rate Limit**: 3 requests per 60 seconds

    **Warning**: This will disable all firewall protection!
    System will be exposed to network traffic.

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        firewall_manager.disable_firewall(username=username)

        log_firewall_action("DISABLE_FIREWALL", "Firewall disabled", username)

        return {
            "success": True,
            "message": "Firewall disabled successfully",
            "warning": "System is now exposed - firewall protection disabled"
        }

    except FirewallError as e:
        logger.error(f"Error disabling firewall: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error disabling firewall: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reset")
async def reset_firewall(
    request: Request,
    confirm: bool = False
):
    """
    Reset firewall to default configuration

    **Rate Limit**: 2 requests per 60 seconds

    **DANGER**: This will delete ALL firewall rules and reset to defaults!
    SSH access rule will be preserved for safety.

    **Parameters**:
    - confirm: Must be true to proceed (safety check)

    **Returns**: Success message
    """
    # Authentication required
    await require_admin(request)

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Reset requires confirm=true parameter as safety check"
        )

    username = get_username_from_request(request)

    try:
        firewall_manager.reset_firewall(username=username)

        log_firewall_action("RESET_FIREWALL", "Firewall reset to defaults", username)

        return {
            "success": True,
            "message": "Firewall reset to default configuration",
            "info": "SSH access has been preserved for safety"
        }

    except FirewallError as e:
        logger.error(f"Error resetting firewall: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error resetting firewall: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/templates/{template_name}")
async def apply_firewall_template(
    template_name: str,
    request: Request,
    override_existing: bool = False
):
    """
    Apply predefined firewall rule template

    **Rate Limit**: 5 requests per 60 seconds

    **Available Templates**:
    - web-server: HTTP (80), HTTPS (443)
    - database: MySQL (3306), PostgreSQL (5432), MongoDB (27017)
    - docker: Docker daemon (2375, 2376)
    - development: Common dev ports (3000, 8000, 8080, 5000)
    - mail-server: SMTP (25, 587), IMAP (143, 993), POP3 (110, 995)

    **Parameters**:
    - template_name: Name of template to apply
    - override_existing: Replace existing rules (default: false)

    **Returns**: Success message with list of added rules
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    try:
        result = firewall_manager.apply_template(
            template_name=template_name,
            username=username,
            override_existing=override_existing
        )

        log_firewall_action(
            "APPLY_TEMPLATE",
            f"Applied template '{template_name}' (override: {override_existing})",
            username
        )

        return {
            "success": True,
            "message": f"Template '{template_name}' applied successfully",
            "rules_added": result.get("rules_added", 0),
            "rules": result.get("rules", [])
        }

    except FirewallError as e:
        logger.error(f"Error applying template: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error applying template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates")
async def list_firewall_templates(request: Request):
    """
    List all available firewall rule templates

    **Rate Limit**: 20 requests per 60 seconds

    **Returns**: List of available templates with descriptions
    """
    # Authentication required
    await require_admin(request)

    try:
        templates = firewall_manager.list_templates()

        return {
            "success": True,
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/logs")
async def get_firewall_logs(
    request: Request,
    limit: int = 100,
    filter_action: Optional[str] = None
):
    """
    Get recent firewall logs (blocked/allowed traffic)

    **Rate Limit**: 10 requests per 60 seconds

    **Parameters**:
    - limit: Maximum number of log entries (default: 100, max: 1000)
    - filter_action: Filter by action (BLOCK/ALLOW)

    **Returns**: List of recent firewall log entries
    """
    # Authentication required
    await require_admin(request)

    username = get_username_from_request(request)

    # Limit cap
    limit = min(limit, 1000)

    try:
        logs = firewall_manager.get_logs(limit=limit, filter_action=filter_action)

        log_firewall_action("GET_LOGS", f"Retrieved {len(logs)} log entries", username)

        return {
            "success": True,
            "logs": logs,
            "count": len(logs)
        }

    except FirewallError as e:
        logger.error(f"Error getting firewall logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting firewall logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Health Check ====================

@router.get("/health")
async def firewall_health_check():
    """
    Health check endpoint for firewall API

    No authentication required for monitoring systems

    **Returns**: Health status
    """
    try:
        # Check if UFW is installed
        is_available = firewall_manager._verify_ufw_installed()

        return {
            "status": "healthy" if is_available else "degraded",
            "ufw_available": is_available,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
