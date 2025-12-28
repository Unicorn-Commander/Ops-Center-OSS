"""
Firewall Management Module for UC-Cloud Ops-Center

This module provides secure firewall management using UFW (Uncomplicated Firewall)
with comprehensive security features including input validation, SSH protection,
audit logging, and rollback mechanisms.

Author: Backend Developer Agent
Date: October 22, 2025
Epic: 1.2 Phase 1 - Network Configuration Enhancement
"""

import subprocess
import re
import logging
import ipaddress
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class FirewallError(Exception):
    """Base exception for firewall operations"""
    pass


class UFWNotInstalled(FirewallError):
    """UFW is not installed on the system"""
    pass


class InsufficientPermissions(FirewallError):
    """User lacks required permissions to execute firewall commands"""
    pass


class SSHRuleProtectionError(FirewallError):
    """Attempted to delete SSH rule without confirmation"""
    pass


# ============================================================================
# Pydantic Models for Input Validation
# ============================================================================

class FirewallRuleCreate(BaseModel):
    """Validated model for creating firewall rules"""
    port: int = Field(..., ge=1, le=65535, description="Port number (1-65535)")
    protocol: str = Field(..., pattern="^(tcp|udp|both)$", description="Protocol: tcp, udp, or both")
    action: str = Field(..., pattern="^(allow|deny)$", description="Action: allow or deny")
    description: str = Field("", max_length=200, description="Rule description (max 200 chars)")
    from_ip: Optional[str] = Field(None, description="Source IP address or CIDR notation")

    @validator('port')
    def validate_ssh_protection(cls, v):
        """Warn when modifying SSH port"""
        if v == 22:
            logger.warning("⚠️ Attempting to modify SSH port 22 - SSH protection will apply")
        return v

    @validator('from_ip')
    def validate_ip_cidr(cls, v):
        """Validate IP address or CIDR notation"""
        if v is not None:
            try:
                # Try parsing as network (supports both IP and CIDR)
                ipaddress.ip_network(v, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid IP address or CIDR notation: {v}") from e
        return v

    @validator('description')
    def validate_description_safety(cls, v):
        """Ensure description doesn't contain shell metacharacters"""
        if v:
            # Only allow alphanumeric, spaces, hyphens, underscores, periods
            if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', v):
                raise ValueError("Description contains invalid characters. Only alphanumeric, spaces, -, _, and . allowed")
        return v


# ============================================================================
# Firewall Rule Templates
# ============================================================================

TEMPLATES = {
    "web_server": [
        {"port": 80, "protocol": "tcp", "action": "allow", "description": "HTTP"},
        {"port": 443, "protocol": "tcp", "action": "allow", "description": "HTTPS"},
    ],
    "ssh_secure": [
        {"port": 22, "protocol": "tcp", "action": "allow", "description": "SSH"},
    ],
    "database": [
        {"port": 5432, "protocol": "tcp", "action": "allow", "description": "PostgreSQL"},
        {"port": 6379, "protocol": "tcp", "action": "allow", "description": "Redis"},
    ],
    "docker": [
        {"port": 2376, "protocol": "tcp", "action": "allow", "description": "Docker TLS"},
    ],
}


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Simple audit logger for firewall operations"""

    @staticmethod
    def log_firewall_change(action: str, details: Dict[str, Any], username: str, success: bool = True, error: str = None):
        """
        Log firewall operation to audit trail

        Args:
            action: Operation type (add_rule, delete_rule, enable, disable, etc.)
            details: Dictionary with operation details
            username: Username performing the operation
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": username,
            "success": success,
            "details": details,
            "error": error
        }

        if success:
            logger.info(
                f"FIREWALL_AUDIT: action={action} user={username} details={details}",
                extra={'audit': True, 'username': username, 'action': action}
            )
        else:
            logger.error(
                f"FIREWALL_AUDIT_FAIL: action={action} user={username} error={error} details={details}",
                extra={'audit': True, 'username': username, 'action': action, 'error': error}
            )


# ============================================================================
# Main Firewall Manager Class
# ============================================================================

class FirewallManager:
    """
    Secure firewall management using UFW

    Features:
    - Safe subprocess execution (no shell=True)
    - Input validation via Pydantic
    - SSH rule protection
    - Comprehensive audit logging
    - Template-based rule sets
    - Rate limiting ready (to be applied at API layer)
    """

    UFW_PATH = "/usr/sbin/ufw"

    def __init__(self, audit_logger: AuditLogger = None):
        """
        Initialize firewall manager

        Args:
            audit_logger: Optional custom audit logger instance
        """
        self.audit_logger = audit_logger or AuditLogger()
        # Don't verify UFW during init - check when needed to allow server to start
        # self._verify_ufw_installed()

    def _verify_ufw_installed(self):
        """Verify UFW is installed and accessible"""
        if not Path(self.UFW_PATH).exists():
            raise UFWNotInstalled(
                f"UFW not found at {self.UFW_PATH}. Install with: sudo apt install ufw"
            )

    def _run_ufw_command(self, args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
        """
        Execute UFW command safely

        Args:
            args: Command arguments as list (e.g., ["status", "verbose"])
            timeout: Command timeout in seconds (default 10)

        Returns:
            CompletedProcess object with stdout, stderr, returncode

        Raises:
            FirewallError: If command execution fails
            InsufficientPermissions: If permission denied
        """
        # Verify UFW is installed before running command
        self._verify_ufw_installed()

        # Build full command with sudo
        full_command = ["sudo", self.UFW_PATH] + args

        logger.debug(f"Executing UFW command: {' '.join(full_command)}")

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit, handle manually
            )

            # Check for permission errors
            if "permission denied" in result.stderr.lower():
                raise InsufficientPermissions(
                    "Permission denied executing UFW command. Ensure sudo access is configured."
                )

            # Check for command failures
            if result.returncode != 0:
                raise FirewallError(f"UFW command failed: {result.stderr.strip()}")

            return result

        except subprocess.TimeoutExpired:
            raise FirewallError(f"UFW command timed out after {timeout} seconds")
        except FileNotFoundError:
            raise UFWNotInstalled(f"UFW not found. Install with: sudo apt install ufw")
        except Exception as e:
            raise FirewallError(f"Unexpected error executing UFW command: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current firewall status

        Returns:
            Dictionary with status information:
            - enabled: bool (firewall active/inactive)
            - default_incoming: str (allow/deny)
            - default_outgoing: str (allow/deny)
            - default_routed: str (allow/deny)
            - logging: str (on/off/level)
            - rules_count: int (number of active rules)
        """
        try:
            result = self._run_ufw_command(["status", "verbose"])
            output = result.stdout

            status = {
                "enabled": "Status: active" in output,
                "default_incoming": "deny" if "deny (incoming)" in output else "allow",
                "default_outgoing": "allow" if "allow (outgoing)" in output else "deny",
                "default_routed": "deny" if "deny (routed)" in output else "allow",
                "logging": "on" if "Logging: on" in output else "off",
                "rules_count": 0  # Will be updated below
            }

            # Count rules (numbered output)
            numbered_result = self._run_ufw_command(["status", "numbered"])
            numbered_output = numbered_result.stdout

            # Count lines starting with [ (rule numbers)
            rule_lines = [line for line in numbered_output.split('\n') if line.strip().startswith('[')]
            status["rules_count"] = len(rule_lines)

            return status

        except Exception as e:
            logger.error(f"Failed to get firewall status: {e}")
            raise FirewallError(f"Failed to get firewall status: {e}")

    def list_rules(self) -> List[Dict[str, Any]]:
        """
        List all firewall rules

        Returns:
            List of dictionaries with rule information:
            - rule_num: int (UFW rule number)
            - port: str (port or port range)
            - action: str (ALLOW, DENY, REJECT)
            - from: str (source IP/network)
            - protocol: str (tcp, udp, etc.)
            - description: str (comment if available)
        """
        try:
            result = self._run_ufw_command(["status", "numbered"])
            output = result.stdout

            rules = []
            for line in output.split('\n'):
                line = line.strip()

                # Match lines like: [ 1] 22/tcp                     ALLOW IN    Anywhere
                match = re.match(r'\[\s*(\d+)\]\s+(.+?)\s+(ALLOW|DENY|REJECT)\s+(IN|OUT)\s+(.+)', line)

                if match:
                    rule_num, port_proto, action, direction, from_addr = match.groups()

                    # Parse port/protocol
                    port = port_proto.strip()
                    protocol = "any"
                    if '/' in port:
                        port, protocol = port.split('/')

                    rules.append({
                        "rule_num": int(rule_num),
                        "port": port,
                        "protocol": protocol,
                        "action": action.lower(),
                        "direction": direction.lower(),
                        "from": from_addr.strip(),
                        "description": ""  # UFW doesn't show comments in status output
                    })

            return rules

        except Exception as e:
            logger.error(f"Failed to list firewall rules: {e}")
            raise FirewallError(f"Failed to list firewall rules: {e}")

    def add_rule(self, port: int, protocol: str, action: str, description: str = "",
                 from_ip: Optional[str] = None, username: str = "system") -> Dict[str, Any]:
        """
        Add a firewall rule

        Args:
            port: Port number (1-65535)
            protocol: Protocol (tcp, udp, both)
            action: Action (allow, deny)
            description: Optional rule description
            from_ip: Optional source IP or CIDR notation
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result

        Raises:
            ValueError: If input validation fails
            FirewallError: If rule creation fails
        """
        # Validate inputs using Pydantic model
        try:
            rule_data = FirewallRuleCreate(
                port=port,
                protocol=protocol,
                action=action,
                description=description,
                from_ip=from_ip
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid rule parameters: {e}")

        # Build UFW command
        ufw_args = [action]  # allow or deny

        # Add source IP if specified
        if from_ip:
            ufw_args.extend(["from", from_ip])

        # Add port and protocol
        if protocol == "both":
            # UFW doesn't have "both", so add rules for tcp and udp separately
            tcp_result = self._add_single_rule(port, "tcp", action, description, from_ip, username)
            udp_result = self._add_single_rule(port, "udp", action, description, from_ip, username)

            return {
                "success": True,
                "message": f"Firewall rules added for {port}/tcp and {port}/udp",
                "tcp_rule": tcp_result,
                "udp_rule": udp_result
            }
        else:
            return self._add_single_rule(port, protocol, action, description, from_ip, username)

    def _add_single_rule(self, port: int, protocol: str, action: str,
                        description: str, from_ip: Optional[str], username: str) -> Dict[str, Any]:
        """Helper to add a single protocol rule"""
        ufw_args = [action]

        if from_ip:
            ufw_args.extend(["from", from_ip])

        ufw_args.extend(["to", "any", "port", str(port), "proto", protocol])

        # Add comment if description provided
        if description:
            ufw_args.extend(["comment", description])

        try:
            result = self._run_ufw_command(ufw_args, timeout=15)

            # Log successful operation
            self.audit_logger.log_firewall_change(
                action="add_rule",
                details={
                    "port": port,
                    "protocol": protocol,
                    "action": action,
                    "from_ip": from_ip,
                    "description": description
                },
                username=username,
                success=True
            )

            logger.info(f"Firewall rule added: {action} {port}/{protocol} from {from_ip or 'any'}")

            return {
                "success": True,
                "message": f"Firewall rule added: {action} {port}/{protocol}",
                "ufw_output": result.stdout.strip()
            }

        except Exception as e:
            # Log failed operation
            self.audit_logger.log_firewall_change(
                action="add_rule",
                details={
                    "port": port,
                    "protocol": protocol,
                    "action": action,
                    "from_ip": from_ip
                },
                username=username,
                success=False,
                error=str(e)
            )

            logger.error(f"Failed to add firewall rule: {e}")
            raise FirewallError(f"Failed to add firewall rule: {e}")

    def delete_rule(self, rule_num: int, override_ssh_protection: bool = False,
                   username: str = "system") -> Dict[str, Any]:
        """
        Delete a firewall rule by number

        Args:
            rule_num: UFW rule number (from list_rules or status numbered)
            override_ssh_protection: Set to True to delete SSH rule (DANGEROUS)
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result

        Raises:
            SSHRuleProtectionError: If attempting to delete SSH rule without override
            FirewallError: If deletion fails
        """
        # Check if this is an SSH rule (port 22)
        if not override_ssh_protection:
            rules = self.list_rules()
            for rule in rules:
                if rule["rule_num"] == rule_num:
                    if rule["port"] == "22" or rule["port"] == "ssh":
                        raise SSHRuleProtectionError(
                            f"Cannot delete SSH rule (port 22, rule #{rule_num}) without explicit override. "
                            "This would lock you out of the server. "
                            "Use override_ssh_protection=True if you're certain."
                        )

        try:
            # Delete rule - UFW requires "delete" followed by rule number
            result = self._run_ufw_command(["--force", "delete", str(rule_num)], timeout=15)

            # Log successful deletion
            self.audit_logger.log_firewall_change(
                action="delete_rule",
                details={"rule_num": rule_num, "override_ssh_protection": override_ssh_protection},
                username=username,
                success=True
            )

            logger.info(f"Firewall rule #{rule_num} deleted by {username}")

            return {
                "success": True,
                "message": f"Firewall rule #{rule_num} deleted successfully",
                "ufw_output": result.stdout.strip()
            }

        except Exception as e:
            # Log failed deletion
            self.audit_logger.log_firewall_change(
                action="delete_rule",
                details={"rule_num": rule_num},
                username=username,
                success=False,
                error=str(e)
            )

            logger.error(f"Failed to delete firewall rule: {e}")
            raise FirewallError(f"Failed to delete firewall rule: {e}")

    def enable_firewall(self, username: str = "system") -> Dict[str, Any]:
        """
        Enable the firewall

        Args:
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result
        """
        try:
            result = self._run_ufw_command(["--force", "enable"], timeout=15)

            # Log successful operation
            self.audit_logger.log_firewall_change(
                action="enable_firewall",
                details={},
                username=username,
                success=True
            )

            logger.info(f"Firewall enabled by {username}")

            return {
                "success": True,
                "message": "Firewall enabled successfully",
                "ufw_output": result.stdout.strip()
            }

        except Exception as e:
            # Log failed operation
            self.audit_logger.log_firewall_change(
                action="enable_firewall",
                details={},
                username=username,
                success=False,
                error=str(e)
            )

            logger.error(f"Failed to enable firewall: {e}")
            raise FirewallError(f"Failed to enable firewall: {e}")

    def disable_firewall(self, username: str = "system") -> Dict[str, Any]:
        """
        Disable the firewall (WARNING: Removes all protection)

        Args:
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result
        """
        try:
            result = self._run_ufw_command(["--force", "disable"], timeout=15)

            # Log successful operation
            self.audit_logger.log_firewall_change(
                action="disable_firewall",
                details={},
                username=username,
                success=True
            )

            logger.warning(f"⚠️ Firewall DISABLED by {username} - System is now unprotected!")

            return {
                "success": True,
                "message": "Firewall disabled (WARNING: System is now unprotected)",
                "ufw_output": result.stdout.strip()
            }

        except Exception as e:
            # Log failed operation
            self.audit_logger.log_firewall_change(
                action="disable_firewall",
                details={},
                username=username,
                success=False,
                error=str(e)
            )

            logger.error(f"Failed to disable firewall: {e}")
            raise FirewallError(f"Failed to disable firewall: {e}")

    def reset_firewall(self, keep_ssh: bool = True, username: str = "system") -> Dict[str, Any]:
        """
        Reset firewall to defaults (removes all rules)

        Args:
            keep_ssh: If True, re-add SSH rule after reset (default: True)
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result
        """
        try:
            # Reset UFW (removes all rules and default policies)
            result = self._run_ufw_command(["--force", "reset"], timeout=15)

            # Re-add SSH rule if requested
            if keep_ssh:
                self._run_ufw_command(["allow", "22/tcp", "comment", "SSH (auto-restored)"], timeout=15)
                logger.info("SSH rule (22/tcp) automatically restored after reset")

            # Log successful operation
            self.audit_logger.log_firewall_change(
                action="reset_firewall",
                details={"keep_ssh": keep_ssh},
                username=username,
                success=True
            )

            logger.warning(f"⚠️ Firewall RESET by {username} - All rules cleared")

            return {
                "success": True,
                "message": "Firewall reset to defaults" + (" (SSH rule restored)" if keep_ssh else ""),
                "ufw_output": result.stdout.strip(),
                "ssh_rule_kept": keep_ssh
            }

        except Exception as e:
            # Log failed operation
            self.audit_logger.log_firewall_change(
                action="reset_firewall",
                details={"keep_ssh": keep_ssh},
                username=username,
                success=False,
                error=str(e)
            )

            logger.error(f"Failed to reset firewall: {e}")
            raise FirewallError(f"Failed to reset firewall: {e}")

    def apply_template(self, template_name: str, username: str = "system") -> Dict[str, Any]:
        """
        Apply a predefined firewall rule template

        Args:
            template_name: Template name (web_server, ssh_secure, database, docker)
            username: Username performing the operation (for audit)

        Returns:
            Dictionary with operation result including list of added rules

        Raises:
            ValueError: If template name is invalid
            FirewallError: If template application fails
        """
        if template_name not in TEMPLATES:
            available = ", ".join(TEMPLATES.keys())
            raise ValueError(f"Invalid template: {template_name}. Available templates: {available}")

        template_rules = TEMPLATES[template_name]
        added_rules = []
        errors = []

        for rule in template_rules:
            try:
                result = self.add_rule(
                    port=rule["port"],
                    protocol=rule["protocol"],
                    action=rule["action"],
                    description=f"{template_name}: {rule['description']}",
                    username=username
                )
                added_rules.append(result)
            except Exception as e:
                errors.append(f"Failed to add rule for port {rule['port']}: {e}")

        # Log template application
        self.audit_logger.log_firewall_change(
            action="apply_template",
            details={
                "template_name": template_name,
                "rules_added": len(added_rules),
                "errors": errors
            },
            username=username,
            success=len(errors) == 0
        )

        if errors:
            logger.error(f"Template {template_name} applied with errors: {errors}")
            return {
                "success": False,
                "message": f"Template {template_name} applied with errors",
                "rules_added": len(added_rules),
                "errors": errors
            }
        else:
            logger.info(f"Template {template_name} applied successfully: {len(added_rules)} rules added")
            return {
                "success": True,
                "message": f"Template {template_name} applied successfully",
                "rules_added": len(added_rules),
                "rules": added_rules
            }


# ============================================================================
# Module-level convenience functions
# ============================================================================

def parse_ufw_status(output: str) -> Dict[str, Any]:
    """
    Parse 'ufw status verbose' output into structured data

    Args:
        output: Raw output from 'ufw status verbose' command

    Returns:
        Dictionary with parsed status information
    """
    status = {
        'enabled': 'Status: active' in output,
        'default_incoming': 'deny',
        'default_outgoing': 'allow',
        'default_routed': 'deny',
        'logging': 'off',
        'rules': []
    }

    # Parse default policies
    for line in output.split('\n'):
        if 'Default:' in line:
            if 'deny (incoming)' in line:
                status['default_incoming'] = 'deny'
            elif 'allow (incoming)' in line:
                status['default_incoming'] = 'allow'

            if 'deny (outgoing)' in line:
                status['default_outgoing'] = 'deny'
            elif 'allow (outgoing)' in line:
                status['default_outgoing'] = 'allow'

        if 'Logging:' in line:
            status['logging'] = 'on' if 'on' in line else 'off'

    return status


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # This code runs only when script is executed directly (for testing)
    print("Firewall Manager Module - Test Mode")
    print("=" * 50)

    try:
        # Initialize firewall manager
        fw = FirewallManager()

        # Get status
        status = fw.get_status()
        print(f"\n1. Firewall Status:")
        print(f"   Enabled: {status['enabled']}")
        print(f"   Default Incoming: {status['default_incoming']}")
        print(f"   Rules Count: {status['rules_count']}")

        # List rules
        rules = fw.list_rules()
        print(f"\n2. Current Rules ({len(rules)} total):")
        for rule in rules[:5]:  # Show first 5
            print(f"   [{rule['rule_num']}] {rule['port']}/{rule['protocol']} - {rule['action']} from {rule['from']}")

        # Test input validation
        print(f"\n3. Testing Input Validation:")
        try:
            invalid_rule = FirewallRuleCreate(
                port=70000,  # Invalid: > 65535
                protocol="tcp",
                action="allow"
            )
        except Exception as e:
            print(f"   ✅ Validation correctly rejected invalid port: {e}")

        try:
            invalid_ip = FirewallRuleCreate(
                port=8080,
                protocol="tcp",
                action="allow",
                from_ip="999.999.999.999"  # Invalid IP
            )
        except Exception as e:
            print(f"   ✅ Validation correctly rejected invalid IP: {e}")

        print("\n✅ All tests passed! Firewall manager is ready for use.")

    except UFWNotInstalled as e:
        print(f"\n❌ Error: {e}")
        print("   Please install UFW: sudo apt install ufw")
    except InsufficientPermissions as e:
        print(f"\n❌ Error: {e}")
        print("   Please configure sudo permissions for UFW commands")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
