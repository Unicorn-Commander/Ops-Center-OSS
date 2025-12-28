# Network Management Features

The UC-1 Pro Admin Dashboard provides comprehensive network management capabilities using Ubuntu Server's native tools.

## Features

### 1. Network Status Monitoring
- View all network interfaces (Ethernet, WiFi)
- Real-time connection status
- IP address information
- Interface state monitoring

### 2. WiFi Management
- **Scan for available networks** - Discover nearby WiFi access points
- **Signal strength indicators** - Visual feedback on connection quality
- **Security detection** - Shows WPA/WPA2/Open networks
- **Connect to networks** - Easy connection with password support
- **Disconnect from WiFi** - Clean disconnection

### 3. Network Configuration
- **DHCP Configuration** - Automatic IP assignment
- **Static IP Configuration** - Manual IP address setup
  - IP Address
  - Subnet mask
  - Gateway
  - DNS servers (primary & secondary)
- **Persistent configuration** - Settings saved in netplan

### 4. Bluetooth Status
- Check if Bluetooth service is enabled
- Count of paired devices

## Technology Stack

### Ubuntu Server Native Tools
- **netplan** - Network configuration management
- **ip** - Interface and routing management
- **iw** - Wireless device configuration
- **systemctl** - Service management

### Configuration Files
The dashboard manages these netplan configuration files:
- `/etc/netplan/99-uc1-admin.yaml` - Ethernet configurations
- `/etc/netplan/99-uc1-wifi.yaml` - WiFi configurations

## Usage Guide

### Viewing Network Status
1. Navigate to the Network page
2. Current connections show at the top
3. Green check marks indicate active connections

### Connecting to WiFi
1. Click "Scan Networks" to discover available networks
2. Click on a network to select it
3. Enter the password if required
4. Click "Connect"

### Configuring Static IP
1. Click the "Configure" button
2. Select "Static IP" from the dropdown
3. Enter:
   - IP Address (e.g., 192.168.1.100)
   - Subnet Mask (e.g., 255.255.255.0)
   - Gateway (e.g., 192.168.1.1)
   - DNS Servers (e.g., 8.8.8.8, 8.8.4.4)
4. Click "Apply"

### Switching to DHCP
1. Click the "Configure" button
2. Select "DHCP (Automatic)"
3. Click "Apply"

## Troubleshooting

### "Network scan failed" Error
**Cause**: Missing network tools or permissions
**Solution**: 
```bash
# Install required tools
sudo apt-get install iw wireless-tools

# Run the full installation script
sudo ./install.sh
```

### Cannot Connect to WiFi
**Possible Causes**:
1. WiFi interface is down
2. Incorrect password
3. Permission issues

**Solutions**:
```bash
# Check WiFi interface status
ip link show

# Bring interface up
sudo ip link set wlan0 up

# Check permissions
./check-dependencies.sh
```

### Configuration Not Applied
**Cause**: Netplan syntax error or permissions
**Solution**:
```bash
# Test configuration
sudo netplan try

# Check syntax
sudo netplan get

# Apply manually
sudo netplan apply
```

### No WiFi Networks Found
**Possible Causes**:
1. No WiFi adapter
2. WiFi disabled
3. Driver issues

**Solutions**:
```bash
# List wireless interfaces
iw dev

# Check if blocked
rfkill list

# Unblock if needed
sudo rfkill unblock wifi
```

## Security Considerations

1. **Passwords**: WiFi passwords are written to netplan files with restricted permissions
2. **Permissions**: Network configuration requires elevated privileges
3. **Validation**: All input is validated before applying changes

## API Endpoints

- `GET /api/v1/network/status` - Get current network status
- `GET /api/v1/network/wifi/scan` - Scan for WiFi networks
- `POST /api/v1/network/wifi/connect` - Connect to WiFi
- `POST /api/v1/network/wifi/disconnect` - Disconnect WiFi
- `POST /api/v1/network/configure` - Configure network interface

## Future Enhancements

- [ ] Network speed testing
- [ ] Data usage monitoring
- [ ] VPN configuration
- [ ] Firewall management
- [ ] Network diagnostics (ping, traceroute)
- [ ] Multiple WiFi profile management
- [ ] 802.1X enterprise authentication
- [ ] IPv6 configuration support