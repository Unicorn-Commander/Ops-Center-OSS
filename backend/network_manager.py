"""
Network management for Ubuntu Server using native tools (netplan, ip, iw)
"""
import json
import os
import re
import subprocess
import yaml
import ipaddress
from pathlib import Path
from typing import Dict, List, Optional, Any


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address

    Args:
        ip: IP address string to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If IP address is invalid
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        raise ValidationError(f"Invalid IP address: {ip}")


def validate_interface_name(interface: str) -> bool:
    """
    Validate network interface name

    Interface names in Linux must be:
    - Alphanumeric plus underscore and hyphen
    - Maximum 15 characters
    - Not contain path traversal sequences

    Args:
        interface: Interface name to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If interface name is invalid
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', interface):
        raise ValidationError(f"Invalid interface name: {interface}")
    if len(interface) > 15:  # Linux max interface name length
        raise ValidationError("Interface name too long (max 15 characters)")
    # Prevent path traversal attempts
    if '..' in interface or '/' in interface:
        raise ValidationError("Interface name contains dangerous characters")
    return True


def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname per RFC 1123

    Args:
        hostname: Hostname to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If hostname is invalid
    """
    if len(hostname) > 255:
        raise ValidationError("Hostname too long (max 255 characters)")
    if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$',
                    hostname, re.IGNORECASE):
        raise ValidationError(f"Invalid hostname format: {hostname}")
    return True


def validate_ssid(ssid: str) -> bool:
    """
    Validate WiFi SSID

    SSID must be:
    - 1-32 characters
    - No dangerous shell characters

    Args:
        ssid: SSID to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If SSID is invalid
    """
    if not 1 <= len(ssid) <= 32:
        raise ValidationError("SSID must be 1-32 characters")
    # Prevent command injection via dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r', '"', "'", '\\']
    for char in dangerous_chars:
        if char in ssid:
            raise ValidationError(f"SSID contains dangerous character: {char}")
    return True


def validate_wifi_password(password: str) -> bool:
    """
    Validate WiFi password for WPA2

    Args:
        password: WiFi password to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If password is invalid
    """
    if not password or len(password) < 8 or len(password) > 63:
        raise ValidationError("WiFi password must be 8-63 characters")
    return True


def sanitize_for_yaml(value: str) -> str:
    """
    Sanitize string for safe YAML inclusion

    Prevents YAML injection by rejecting strings with dangerous characters
    that could break YAML structure or inject commands.

    Args:
        value: String to sanitize

    Returns:
        Original value if safe

    Raises:
        ValidationError: If value contains unsafe characters
    """
    # YAML special characters that could break structure or inject directives
    dangerous = [':', '{', '}', '[', ']', '!', '&', '*', '#', '?', '|', '>', '`', '\n', '\r']
    for char in dangerous:
        if char in value:
            raise ValidationError(f"Value contains unsafe YAML character: {char}")
    return value


def validate_cidr_prefix(prefix: int) -> bool:
    """
    Validate CIDR prefix length

    Args:
        prefix: Prefix length (0-32 for IPv4, 0-128 for IPv6)

    Returns:
        True if valid

    Raises:
        ValidationError: If prefix is invalid
    """
    if not 0 <= prefix <= 32:  # Assuming IPv4 for now
        raise ValidationError(f"Invalid CIDR prefix: {prefix} (must be 0-32)")
    return True

class UbuntuNetworkManager:
    """Manage network configuration on Ubuntu Server"""
    
    def __init__(self):
        self.netplan_dir = Path("/etc/netplan")
        
    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get all network interfaces and their status using ip command"""
        interfaces = {}
        
        try:
            # Get interface list with JSON output
            result = subprocess.run(
                ["ip", "-j", "link", "show"],
                capture_output=True, text=True, check=True
            )
            
            links = json.loads(result.stdout)
            
            # Get IP addresses
            addr_result = subprocess.run(
                ["ip", "-j", "addr", "show"],
                capture_output=True, text=True, check=True
            )
            
            addresses = json.loads(addr_result.stdout)
            addr_map = {addr['ifname']: addr for addr in addresses}
            
            for link in links:
                ifname = link.get('ifname', '')
                # Skip loopback and virtual interfaces
                if ifname == 'lo' or ifname.startswith(('veth', 'docker', 'br-')):
                    continue
                    
                interface_info = {
                    'name': ifname,
                    'state': link.get('operstate', 'UNKNOWN'),
                    'mac': link.get('address', ''),
                    'type': 'ethernet' if 'eth' in ifname or 'eno' in ifname or 'enp' in ifname else 'wifi' if 'wl' in ifname else 'unknown',
                    'ip_addresses': []
                }
                
                # Add IP addresses if available
                if ifname in addr_map:
                    addr_info = addr_map[ifname]
                    for addr in addr_info.get('addr_info', []):
                        if addr.get('family') == 'inet':  # IPv4
                            interface_info['ip_addresses'].append({
                                'address': addr.get('local'),
                                'prefix': addr.get('prefixlen'),
                                'scope': addr.get('scope')
                            })
                
                interfaces[ifname] = interface_info
                
        except Exception as e:
            print(f"Error getting network interfaces: {e}")
            
        return interfaces
    
    def get_wifi_networks(self) -> List[Dict[str, Any]]:
        """Scan for available WiFi networks"""
        networks = []
        
        try:
            # First, find wireless interfaces
            interfaces = self.get_network_interfaces()
            wifi_interfaces = [name for name, info in interfaces.items() if info['type'] == 'wifi']
            
            if not wifi_interfaces:
                return []
            
            # Use the first WiFi interface for scanning
            wifi_interface = wifi_interfaces[0]
            
            # Check if interface is up
            subprocess.run(["ip", "link", "set", wifi_interface, "up"], capture_output=True)
            
            # Scan using iw command
            result = subprocess.run(
                ["iw", "dev", wifi_interface, "scan"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Parse scan results
                current_network = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if line.startswith('BSS '):
                        # New network found
                        if current_network:
                            networks.append(current_network)
                        current_network = {
                            'bssid': line.split()[1].rstrip('('),
                            'ssid': '',
                            'signal': 0,
                            'security': 'Open',
                            'frequency': 0
                        }
                    elif 'SSID:' in line:
                        current_network['ssid'] = line.split(':', 1)[1].strip()
                    elif 'signal:' in line:
                        # Extract signal strength in dBm
                        match = re.search(r'signal:\s*(-?\d+)', line)
                        if match:
                            dbm = int(match.group(1))
                            # Convert dBm to percentage (rough approximation)
                            current_network['signal'] = max(0, min(100, (dbm + 100) * 2))
                    elif 'freq:' in line:
                        match = re.search(r'freq:\s*(\d+)', line)
                        if match:
                            current_network['frequency'] = int(match.group(1))
                    elif 'RSN:' in line or 'WPA:' in line:
                        current_network['security'] = 'WPA2' if 'RSN:' in line else 'WPA'
                
                # Add last network
                if current_network:
                    networks.append(current_network)
                    
        except subprocess.CalledProcessError as e:
            print(f"WiFi scan error: {e}")
        except FileNotFoundError:
            print("iw command not found. WiFi scanning requires wireless-tools.")
            
        return networks
    
    def get_current_wifi_connection(self) -> Optional[Dict[str, Any]]:
        """Get current WiFi connection info"""
        try:
            # Find wireless interfaces
            interfaces = self.get_network_interfaces()
            
            for name, info in interfaces.items():
                if info['type'] == 'wifi' and info['state'] == 'UP':
                    # Get connection info using iw
                    result = subprocess.run(
                        ["iw", "dev", name, "link"],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0 and 'Connected to' in result.stdout:
                        connection_info = {
                            'interface': name,
                            'ip_addresses': info['ip_addresses']
                        }
                        
                        # Parse connection details
                        for line in result.stdout.split('\n'):
                            if 'SSID:' in line:
                                connection_info['ssid'] = line.split(':', 1)[1].strip()
                            elif 'signal:' in line:
                                match = re.search(r'signal:\s*(-?\d+)', line)
                                if match:
                                    dbm = int(match.group(1))
                                    connection_info['signal'] = max(0, min(100, (dbm + 100) * 2))
                        
                        return connection_info
                        
        except Exception as e:
            print(f"Error getting WiFi connection: {e}")
            
        return None
    
    def read_netplan_config(self) -> Dict[str, Any]:
        """Read current netplan configuration"""
        config = {}
        
        try:
            # Find netplan config files
            config_files = list(self.netplan_dir.glob("*.yaml")) + list(self.netplan_dir.glob("*.yml"))
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        file_config = yaml.safe_load(f)
                        if file_config:
                            # Merge configurations
                            self._merge_configs(config, file_config)
                except Exception as e:
                    print(f"Error reading {config_file}: {e}")
                    
        except Exception as e:
            print(f"Error reading netplan config: {e}")
            
        return config
    
    def _merge_configs(self, base: Dict, update: Dict):
        """Recursively merge netplan configurations"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def update_interface_config(self, interface: str, config: Dict[str, Any]) -> bool:
        """
        Update network interface configuration in netplan

        Args:
            interface: Network interface name (validated)
            config: Configuration dictionary with method, address, gateway, dns

        Returns:
            True if successful

        Raises:
            ValidationError: If inputs are invalid
        """
        try:
            # CRITICAL SECURITY FIX: Validate interface name (CRIT-3)
            validate_interface_name(interface)

            # Read current config
            current_config = self.read_netplan_config()

            # Ensure network structure exists
            if 'network' not in current_config:
                current_config['network'] = {'version': 2}

            network = current_config['network']

            # Determine interface type
            interfaces = self.get_network_interfaces()
            if interface not in interfaces:
                raise ValueError(f"Interface {interface} not found")

            iface_type = 'ethernets' if interfaces[interface]['type'] == 'ethernet' else 'wifis'

            # Ensure interface type section exists
            if iface_type not in network:
                network[iface_type] = {}

            # Update interface configuration
            if config.get('method') == 'dhcp':
                network[iface_type][interface] = {
                    'dhcp4': True,
                    'dhcp6': False
                }
            else:  # static
                # CRITICAL SECURITY FIX: Validate all IP inputs (CRIT-1)
                if 'address' not in config:
                    raise ValidationError("IP address is required for static configuration")

                # Validate IP address
                validate_ip_address(config['address'])

                # Validate CIDR prefix
                prefix = config.get('prefix', 24)
                validate_cidr_prefix(prefix)

                # Validate gateway if provided
                if config.get('gateway'):
                    validate_ip_address(config['gateway'])

                # Validate DNS servers if provided
                dns_servers = config.get('dns', [])
                for dns in dns_servers:
                    validate_ip_address(dns)

                # CRITICAL SECURITY FIX: Sanitize values for YAML (CRIT-2)
                # Note: IP addresses are already validated, but sanitize as extra safety
                sanitized_address = sanitize_for_yaml(config['address'])

                network[iface_type][interface] = {
                    'dhcp4': False,
                    'dhcp6': False,
                    'addresses': [f"{sanitized_address}/{prefix}"],
                    'gateway4': config.get('gateway'),
                    'nameservers': {
                        'addresses': dns_servers
                    }
                }
            
            # Write config to a new file
            config_file = self.netplan_dir / "99-uc1-admin.yaml"
            with open(config_file, 'w') as f:
                # CRITICAL SECURITY FIX: Use safe_dump to prevent YAML injection (CRIT-2)
                yaml.safe_dump(current_config, f, default_flow_style=False, allow_unicode=True)
            
            # Apply configuration
            result = subprocess.run(
                ["netplan", "apply"],
                capture_output=True, text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error updating interface config: {e}")
            return False
    
    def connect_to_wifi(self, ssid: str, password: str, interface: Optional[str] = None) -> bool:
        """
        Connect to a WiFi network using netplan

        Args:
            ssid: WiFi network SSID (validated)
            password: WiFi password (validated, stored as plaintext in config)
            interface: Network interface name (optional, auto-detected if not provided)

        Returns:
            True if successful

        Raises:
            ValidationError: If SSID or password is invalid

        WARNING: Password is stored in plaintext in /etc/netplan/99-uc1-wifi.yaml
        This file should have 600 permissions (root-only read) to mitigate exposure.
        """
        try:
            # CRITICAL SECURITY FIX: Validate SSID and password (CRIT-2)
            validate_ssid(ssid)
            validate_wifi_password(password)

            # Find WiFi interface if not specified
            if not interface:
                interfaces = self.get_network_interfaces()
                wifi_interfaces = [name for name, info in interfaces.items() if info['type'] == 'wifi']
                if not wifi_interfaces:
                    raise ValueError("No WiFi interface found")
                interface = wifi_interfaces[0]

            # CRITICAL SECURITY FIX: Validate interface name (CRIT-3)
            validate_interface_name(interface)

            # Read current config
            current_config = self.read_netplan_config()

            # Ensure network structure exists
            if 'network' not in current_config:
                current_config['network'] = {'version': 2}

            network = current_config['network']

            # Ensure wifis section exists
            if 'wifis' not in network:
                network['wifis'] = {}

            # CRITICAL SECURITY FIX: Sanitize SSID for YAML safety (CRIT-2)
            # Note: SSID validation already rejects dangerous characters,
            # but we sanitize as an additional safety layer
            sanitized_ssid = sanitize_for_yaml(ssid)

            # Configure WiFi
            network['wifis'][interface] = {
                'dhcp4': True,
                'dhcp6': False,
                'access-points': {
                    sanitized_ssid: {
                        'password': password  # Note: Stored as plaintext (documented in docstring)
                    }
                }
            }

            # Write config
            config_file = self.netplan_dir / "99-uc1-wifi.yaml"
            with open(config_file, 'w') as f:
                # CRITICAL SECURITY FIX: Use safe_dump to prevent YAML injection (CRIT-2)
                yaml.safe_dump(current_config, f, default_flow_style=False, allow_unicode=True)
            
            # Apply configuration
            result = subprocess.run(
                ["netplan", "apply"],
                capture_output=True, text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error connecting to WiFi: {e}")
            return False
    
    def disconnect_wifi(self, interface: Optional[str] = None) -> bool:
        """
        Disconnect from WiFi

        Args:
            interface: Network interface name (optional, auto-detected if not provided)

        Returns:
            True if successful

        Raises:
            ValidationError: If interface name is invalid
        """
        try:
            # Find WiFi interface if not specified
            if not interface:
                wifi_conn = self.get_current_wifi_connection()
                if wifi_conn:
                    interface = wifi_conn['interface']
                else:
                    return True  # Already disconnected

            # CRITICAL SECURITY FIX: Validate interface name (CRIT-3)
            validate_interface_name(interface)

            # Remove WiFi configuration from netplan
            current_config = self.read_netplan_config()

            if ('network' in current_config and
                'wifis' in current_config['network'] and
                interface in current_config['network']['wifis']):

                del current_config['network']['wifis'][interface]

                # Write updated config
                config_file = self.netplan_dir / "99-uc1-wifi.yaml"
                if config_file.exists():
                    config_file.unlink()

                # If there are other configs, apply them
                if current_config['network'].get('wifis') or current_config['network'].get('ethernets'):
                    temp_file = self.netplan_dir / "99-uc1-temp.yaml"
                    with open(temp_file, 'w') as f:
                        # CRITICAL SECURITY FIX: Use safe_dump to prevent YAML injection (CRIT-2)
                        yaml.safe_dump(current_config, f, default_flow_style=False, allow_unicode=True)
                
                # Apply configuration
                subprocess.run(["netplan", "apply"], capture_output=True)
                
            return True
            
        except Exception as e:
            print(f"Error disconnecting WiFi: {e}")
            return False

# Global instance
network_manager = UbuntuNetworkManager()


# ============================================================================
# Inline Tests for Validation Functions
# ============================================================================

if __name__ == "__main__":
    """
    Run inline tests to verify security validation functions

    Usage:
        python3 network_manager.py
    """
    print("Running security validation tests...")
    print("=" * 60)

    test_results = {
        "passed": 0,
        "failed": 0
    }

    # Test 1: Valid IP addresses should pass
    print("\n[TEST 1] Valid IP Address Validation")
    try:
        validate_ip_address("192.168.1.1")
        validate_ip_address("10.0.0.1")
        validate_ip_address("8.8.8.8")
        validate_ip_address("::1")  # IPv6
        validate_ip_address("2001:db8::1")  # IPv6
        print("✅ PASS: Valid IP addresses accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 2: Invalid IP addresses should fail
    print("\n[TEST 2] Invalid IP Address Rejection")
    test_cases = [
        "999.999.999.999",
        "192.168.1.1; rm -rf /",
        "192.168.1.1\nmalicious",
        "not-an-ip",
        "192.168.1.256"
    ]
    failed_count = 0
    for test_ip in test_cases:
        try:
            validate_ip_address(test_ip)
            print(f"❌ FAIL: Invalid IP accepted: {test_ip}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} invalid IPs rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} invalid IPs were incorrectly accepted")
        test_results["failed"] += 1

    # Test 3: Valid interface names should pass
    print("\n[TEST 3] Valid Interface Name Validation")
    try:
        validate_interface_name("eth0")
        validate_interface_name("wlan0")
        validate_interface_name("enp0s3")
        validate_interface_name("wlp2s0")
        print("✅ PASS: Valid interface names accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 4: Invalid interface names should fail
    print("\n[TEST 4] Invalid Interface Name Rejection")
    test_cases = [
        "../../etc/passwd",
        "../../../etc/shadow",
        "eth0; rm -rf /",
        "eth0\nmalicious",
        "a" * 16,  # Too long (>15 chars)
        "eth/0"
    ]
    failed_count = 0
    for test_iface in test_cases:
        try:
            validate_interface_name(test_iface)
            print(f"❌ FAIL: Invalid interface name accepted: {test_iface}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} invalid interface names rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} invalid names were incorrectly accepted")
        test_results["failed"] += 1

    # Test 5: Valid hostnames should pass
    print("\n[TEST 5] Valid Hostname Validation")
    try:
        validate_hostname("example.com")
        validate_hostname("sub.example.com")
        validate_hostname("server1")
        validate_hostname("my-server")
        print("✅ PASS: Valid hostnames accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 6: Invalid hostnames should fail
    print("\n[TEST 6] Invalid Hostname Rejection")
    test_cases = [
        "a" * 256,  # Too long
        "-invalid",  # Starts with hyphen
        "invalid-",  # Ends with hyphen
        "invalid..com",  # Double dots
        "invalid_host",  # Underscore not allowed
    ]
    failed_count = 0
    for test_host in test_cases:
        try:
            validate_hostname(test_host)
            print(f"❌ FAIL: Invalid hostname accepted: {test_host}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} invalid hostnames rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} invalid hostnames were incorrectly accepted")
        test_results["failed"] += 1

    # Test 7: Valid SSIDs should pass
    print("\n[TEST 7] Valid SSID Validation")
    try:
        validate_ssid("MyWiFi")
        validate_ssid("Home Network")
        validate_ssid("WiFi-2.4GHz")
        validate_ssid("a" * 32)  # Max length
        print("✅ PASS: Valid SSIDs accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 8: Invalid SSIDs should fail (command injection prevention)
    print("\n[TEST 8] SSID Command Injection Prevention")
    test_cases = [
        "WiFi; rm -rf /",
        "WiFi && malicious",
        "WiFi | cat /etc/passwd",
        "WiFi`whoami`",
        "WiFi$USER",
        "WiFi\nmalicious",
        "a" * 33,  # Too long
        "",  # Empty
        'WiFi"injection'
    ]
    failed_count = 0
    for test_ssid in test_cases:
        try:
            validate_ssid(test_ssid)
            print(f"❌ FAIL: Dangerous SSID accepted: {test_ssid}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} dangerous SSIDs rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} dangerous SSIDs were incorrectly accepted")
        test_results["failed"] += 1

    # Test 9: Valid WiFi passwords should pass
    print("\n[TEST 9] Valid WiFi Password Validation")
    try:
        validate_wifi_password("password123")
        validate_wifi_password("a" * 8)  # Min length
        validate_wifi_password("a" * 63)  # Max length
        print("✅ PASS: Valid WiFi passwords accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 10: Invalid WiFi passwords should fail
    print("\n[TEST 10] Invalid WiFi Password Rejection")
    test_cases = [
        "short",  # Too short (<8)
        "a" * 64,  # Too long (>63)
        "",  # Empty
    ]
    failed_count = 0
    for test_pass in test_cases:
        try:
            validate_wifi_password(test_pass)
            print(f"❌ FAIL: Invalid password accepted: {test_pass}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} invalid passwords rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} invalid passwords were incorrectly accepted")
        test_results["failed"] += 1

    # Test 11: YAML injection prevention
    print("\n[TEST 11] YAML Injection Prevention")
    test_cases = [
        'value: malicious',
        'key{nested}',
        'array[injection]',
        'command!execute',
        'anchor&ref',
        'multiline\ninjection',
        'comment#injection'
    ]
    failed_count = 0
    for test_val in test_cases:
        try:
            sanitize_for_yaml(test_val)
            print(f"❌ FAIL: Dangerous YAML value accepted: {test_val}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} YAML injection attempts blocked")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} YAML injections were incorrectly accepted")
        test_results["failed"] += 1

    # Test 12: Valid CIDR prefixes should pass
    print("\n[TEST 12] Valid CIDR Prefix Validation")
    try:
        validate_cidr_prefix(0)
        validate_cidr_prefix(24)
        validate_cidr_prefix(32)
        print("✅ PASS: Valid CIDR prefixes accepted")
        test_results["passed"] += 1
    except ValidationError as e:
        print(f"❌ FAIL: {e}")
        test_results["failed"] += 1

    # Test 13: Invalid CIDR prefixes should fail
    print("\n[TEST 13] Invalid CIDR Prefix Rejection")
    test_cases = [-1, 33, 128, 999]
    failed_count = 0
    for test_prefix in test_cases:
        try:
            validate_cidr_prefix(test_prefix)
            print(f"❌ FAIL: Invalid CIDR prefix accepted: {test_prefix}")
            failed_count += 1
        except ValidationError:
            pass  # Expected to fail

    if failed_count == 0:
        print(f"✅ PASS: All {len(test_cases)} invalid CIDR prefixes rejected")
        test_results["passed"] += 1
    else:
        print(f"❌ FAIL: {failed_count}/{len(test_cases)} invalid prefixes were incorrectly accepted")
        test_results["failed"] += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    total = test_results["passed"] + test_results["failed"]
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")

    if test_results["failed"] == 0:
        print("\n🎉 All validation tests passed!")
        print("Security fixes are working correctly.")
    else:
        print("\n⚠️  Some validation tests failed.")
        print("Review the failures above and fix the validation logic.")

    print("=" * 60)