"""
System Management Module for UC-1 Pro Ops Center
Provides headless server management capabilities for network, users, and packages.
"""

import json
import os
import re
import subprocess
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models for Request/Response Validation
class NetworkConfig(BaseModel):
    """Network configuration model"""
    ip: Optional[str] = Field(None, description="Static IP address")
    netmask: Optional[str] = Field(None, description="Network mask")
    gateway: Optional[str] = Field(None, description="Default gateway")
    dns_servers: Optional[List[str]] = Field(default_factory=list, description="DNS server list")
    hostname: Optional[str] = Field(None, description="System hostname")
    dhcp: Optional[bool] = Field(False, description="Use DHCP instead of static IP")

    @validator('ip')
    def validate_ip(cls, v):
        if v and not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
            raise ValueError('Invalid IP address format')
        return v

    @validator('dns_servers')
    def validate_dns(cls, v):
        for dns in v:
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', dns):
                raise ValueError(f'Invalid DNS server format: {dns}')
        return v


class NetworkStatus(BaseModel):
    """Current network status"""
    ip: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    dns_servers: List[str] = Field(default_factory=list)
    hostname: str
    interface: str
    dhcp: bool = False


class SystemPasswordChange(BaseModel):
    """System user password change request"""
    username: str = Field(..., description="Username to change password for")
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PackageInfo(BaseModel):
    """Package update information"""
    name: str
    current_version: str
    available_version: str
    size: Optional[str] = None
    description: Optional[str] = None


class PackageList(BaseModel):
    """List of available package updates"""
    packages: List[PackageInfo]
    total_count: int
    last_check: datetime


class SystemManager:
    """
    Manages system-level operations for headless server management.
    Includes network configuration, user management, and package updates.
    """

    def __init__(self):
        self.netplan_dir = Path("/etc/netplan")
        self.network_interfaces_file = Path("/etc/network/interfaces")

    def get_network_config(self) -> NetworkStatus:
        """
        Read current network configuration from system.
        Supports both netplan and traditional interfaces files.

        Returns:
            NetworkStatus: Current network configuration
        """
        try:
            # Get hostname
            hostname_result = subprocess.run(
                ["hostname"],
                capture_output=True,
                text=True,
                check=True
            )
            hostname = hostname_result.stdout.strip()

            # Get primary network interface
            route_result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                check=True
            )

            interface = "unknown"
            if route_result.stdout:
                match = re.search(r'dev\s+(\S+)', route_result.stdout)
                if match:
                    interface = match.group(1)

            # Get IP address and network info
            addr_result = subprocess.run(
                ["ip", "-j", "addr", "show", interface],
                capture_output=True,
                text=True,
                check=True
            )

            addr_data = json.loads(addr_result.stdout)
            ip_address = None
            netmask = None

            if addr_data and len(addr_data) > 0:
                for addr_info in addr_data[0].get('addr_info', []):
                    if addr_info.get('family') == 'inet':
                        ip_address = addr_info.get('local')
                        prefix_len = addr_info.get('prefixlen', 24)
                        # Convert prefix length to netmask
                        netmask = self._prefix_to_netmask(prefix_len)
                        break

            # Get gateway
            gateway = None
            if route_result.stdout:
                match = re.search(r'via\s+(\S+)', route_result.stdout)
                if match:
                    gateway = match.group(1)

            # Get DNS servers
            dns_servers = []
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns = line.split()[1]
                            dns_servers.append(dns)
            except Exception as e:
                logger.warning(f"Could not read DNS servers: {e}")

            # Check if using DHCP by examining netplan config
            dhcp = self._is_dhcp_enabled(interface)

            return NetworkStatus(
                ip=ip_address,
                netmask=netmask,
                gateway=gateway,
                dns_servers=dns_servers,
                hostname=hostname,
                interface=interface,
                dhcp=dhcp
            )

        except Exception as e:
            logger.error(f"Error reading network configuration: {e}")
            raise ValueError(f"Failed to read network configuration: {str(e)}")

    def _prefix_to_netmask(self, prefix_len: int) -> str:
        """Convert CIDR prefix length to netmask"""
        mask = (0xffffffff >> (32 - prefix_len)) << (32 - prefix_len)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"

    def _is_dhcp_enabled(self, interface: str) -> bool:
        """Check if interface is configured for DHCP in netplan"""
        try:
            if not self.netplan_dir.exists():
                return False

            for config_file in self.netplan_dir.glob("*.yaml"):
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)

                if not config or 'network' not in config:
                    continue

                # Check ethernets section
                ethernets = config['network'].get('ethernets', {})
                if interface in ethernets:
                    return ethernets[interface].get('dhcp4', False)

        except Exception as e:
            logger.warning(f"Could not determine DHCP status: {e}")

        return False

    def update_network_config(self, config: NetworkConfig) -> bool:
        """
        Update network configuration using netplan.

        Args:
            config: NetworkConfig object with new network settings

        Returns:
            bool: True if successful

        Raises:
            ValueError: If configuration is invalid
            PermissionError: If not running with sufficient privileges
        """
        try:
            # Get current primary interface
            current_status = self.get_network_config()
            interface = current_status.interface

            # Build netplan configuration
            netplan_config = {
                'network': {
                    'version': 2,
                    'renderer': 'networkd',
                    'ethernets': {
                        interface: {}
                    }
                }
            }

            interface_config = netplan_config['network']['ethernets'][interface]

            if config.dhcp:
                # Configure for DHCP
                interface_config['dhcp4'] = True
            else:
                # Configure static IP
                interface_config['dhcp4'] = False

                if config.ip and config.netmask:
                    # Convert netmask to CIDR prefix
                    prefix_len = self._netmask_to_prefix(config.netmask)
                    interface_config['addresses'] = [f"{config.ip}/{prefix_len}"]

                if config.gateway:
                    interface_config['routes'] = [{
                        'to': 'default',
                        'via': config.gateway
                    }]

                if config.dns_servers:
                    interface_config['nameservers'] = {
                        'addresses': config.dns_servers
                    }

            # Write netplan configuration
            netplan_file = self.netplan_dir / "99-uc1-network.yaml"

            # Backup existing config
            if netplan_file.exists():
                backup_file = self.netplan_dir / f"99-uc1-network.yaml.backup.{int(datetime.now().timestamp())}"
                subprocess.run(['cp', str(netplan_file), str(backup_file)], check=True)

            # Write new config
            with open(netplan_file, 'w') as f:
                yaml.dump(netplan_config, f, default_flow_style=False)

            # Set proper permissions
            subprocess.run(['chmod', '600', str(netplan_file)], check=True)

            # Test configuration
            test_result = subprocess.run(
                ['netplan', 'try', '--timeout', '30'],
                capture_output=True,
                text=True,
                input='',
                timeout=35
            )

            if test_result.returncode != 0:
                logger.error(f"Netplan test failed: {test_result.stderr}")
                raise ValueError(f"Network configuration test failed: {test_result.stderr}")

            # Apply configuration
            apply_result = subprocess.run(
                ['netplan', 'apply'],
                capture_output=True,
                text=True,
                check=True
            )

            if apply_result.returncode != 0:
                logger.error(f"Netplan apply failed: {apply_result.stderr}")
                raise ValueError(f"Failed to apply network configuration: {apply_result.stderr}")

            # Update hostname if provided
            if config.hostname:
                self._update_hostname(config.hostname)

            logger.info(f"Network configuration updated successfully for interface {interface}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Netplan try command timed out")
            raise ValueError("Network configuration test timed out")
        except PermissionError:
            logger.error("Insufficient permissions to update network configuration")
            raise PermissionError("Root/sudo privileges required to update network configuration")
        except Exception as e:
            logger.error(f"Error updating network configuration: {e}")
            raise ValueError(f"Failed to update network configuration: {str(e)}")

    def _netmask_to_prefix(self, netmask: str) -> int:
        """Convert netmask to CIDR prefix length"""
        octets = netmask.split('.')
        binary = ''.join([bin(int(octet))[2:].zfill(8) for octet in octets])
        return binary.count('1')

    def _update_hostname(self, hostname: str):
        """Update system hostname"""
        try:
            # Validate hostname
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', hostname):
                raise ValueError("Invalid hostname format")

            # Update hostname
            subprocess.run(['hostnamectl', 'set-hostname', hostname], check=True)

            # Update /etc/hosts
            hosts_file = Path('/etc/hosts')
            if hosts_file.exists():
                with open(hosts_file, 'r') as f:
                    hosts_content = f.read()

                # Update localhost entries
                hosts_content = re.sub(
                    r'127\.0\.1\.1\s+\S+',
                    f'127.0.1.1\t{hostname}',
                    hosts_content
                )

                with open(hosts_file, 'w') as f:
                    f.write(hosts_content)

            logger.info(f"Hostname updated to {hostname}")

        except Exception as e:
            logger.error(f"Error updating hostname: {e}")
            raise ValueError(f"Failed to update hostname: {str(e)}")

    def change_user_password(self, username: str, current_password: str, new_password: str) -> bool:
        """
        Change Linux user password with current password verification.

        Args:
            username: Username to change password for
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            bool: True if successful

        Raises:
            ValueError: If verification fails or password change fails
            PermissionError: If not running with sufficient privileges
        """
        try:
            # Verify current password using su command
            verify_result = subprocess.run(
                ['su', username, '-c', 'echo "verified"'],
                input=current_password + '\n',
                capture_output=True,
                text=True
            )

            if verify_result.returncode != 0:
                logger.warning(f"Password verification failed for user {username}")
                raise ValueError("Current password is incorrect")

            # Change password using chpasswd (requires root)
            chpasswd_input = f"{username}:{new_password}"
            change_result = subprocess.run(
                ['chpasswd'],
                input=chpasswd_input,
                capture_output=True,
                text=True
            )

            if change_result.returncode != 0:
                logger.error(f"Password change failed: {change_result.stderr}")
                raise ValueError(f"Failed to change password: {change_result.stderr}")

            logger.info(f"Password changed successfully for user {username}")
            return True

        except PermissionError:
            logger.error("Insufficient permissions to change password")
            raise PermissionError("Root/sudo privileges required to change user password")
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            raise ValueError(f"Failed to change password: {str(e)}")

    def get_available_updates(self) -> PackageList:
        """
        Get list of available system package updates.

        Returns:
            PackageList: List of packages with available updates

        Raises:
            ValueError: If package list cannot be retrieved
        """
        try:
            # Update package cache
            logger.info("Updating package cache...")
            update_result = subprocess.run(
                ['apt-get', 'update'],
                capture_output=True,
                text=True
            )

            if update_result.returncode != 0:
                logger.warning(f"Package cache update had warnings: {update_result.stderr}")

            # Get list of upgradable packages
            list_result = subprocess.run(
                ['apt', 'list', '--upgradable'],
                capture_output=True,
                text=True,
                check=True
            )

            packages = []
            for line in list_result.stdout.split('\n'):
                if not line or line.startswith('Listing'):
                    continue

                # Parse line format: package/repo version arch [upgradable from: old_version]
                match = re.match(
                    r'(\S+)/\S+\s+(\S+)\s+\S+\s+\[upgradable from:\s+(\S+)\]',
                    line
                )

                if match:
                    package_name = match.group(1)
                    new_version = match.group(2)
                    current_version = match.group(3)

                    # Get package size and description
                    size = None
                    description = None

                    try:
                        show_result = subprocess.run(
                            ['apt-cache', 'show', package_name],
                            capture_output=True,
                            text=True
                        )

                        if show_result.returncode == 0:
                            for show_line in show_result.stdout.split('\n'):
                                if show_line.startswith('Installed-Size:'):
                                    size = show_line.split(':', 1)[1].strip()
                                elif show_line.startswith('Description:'):
                                    description = show_line.split(':', 1)[1].strip()
                    except:
                        pass  # Size and description are optional

                    packages.append(PackageInfo(
                        name=package_name,
                        current_version=current_version,
                        available_version=new_version,
                        size=size,
                        description=description
                    ))

            return PackageList(
                packages=packages,
                total_count=len(packages),
                last_check=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting available updates: {e}")
            raise ValueError(f"Failed to retrieve package updates: {str(e)}")


# Global instance
system_manager = SystemManager()
