# Network Management Setup for Ubuntu Server

This admin dashboard uses Ubuntu Server's native tools for network management:
- **netplan** - for network configuration
- **ip** - for interface status and management  
- **iw** - for WiFi scanning and management

## Required Permissions

The backend service needs permissions to manage network configuration. You have several options:

### Option 1: Run backend with sudo (development only)
```bash
sudo python3 server.py
```

### Option 2: Grant specific permissions (recommended)

1. Allow the backend user to run network commands without password:
```bash
# Add to /etc/sudoers.d/network-admin
ucadmin ALL=(ALL) NOPASSWD: /usr/sbin/netplan
ucadmin ALL=(ALL) NOPASSWD: /usr/sbin/ip
ucadmin ALL=(ALL) NOPASSWD: /usr/sbin/iw
```

2. Or create a systemd service that runs with appropriate permissions:
```ini
[Unit]
Description=UC-1 Admin Dashboard Backend
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/ucadmin/UC-1-Pro/services/admin-dashboard/backend
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Option 3: Use polkit rules (most secure)

Create `/etc/polkit-1/rules.d/50-network-admin.rules`:
```javascript
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.NetworkManager.network-control" ||
         action.id == "org.freedesktop.NetworkManager.wifi.scan") &&
        subject.user == "ucadmin") {
        return polkit.Result.YES;
    }
});
```

## Netplan Configuration

The network manager creates/modifies netplan configuration files:
- `/etc/netplan/99-uc1-admin.yaml` - Ethernet configurations
- `/etc/netplan/99-uc1-wifi.yaml` - WiFi configurations

These files are managed automatically by the admin dashboard.

## Troubleshooting

1. **Permission Denied Errors**
   - Ensure the backend has appropriate permissions (see above)
   - Check that netplan directory is writable: `ls -la /etc/netplan/`

2. **WiFi Scanning Not Working**
   - Install wireless tools: `sudo apt-get install wireless-tools iw`
   - Ensure WiFi interface is up: `sudo ip link set wlan0 up`

3. **Network Changes Not Applied**
   - Check netplan syntax: `sudo netplan try`
   - View netplan config: `sudo netplan get`
   - Apply manually: `sudo netplan apply`

## Testing Network Features

```bash
# Test interface discovery
curl http://localhost:8085/api/v1/network/status

# Test WiFi scanning (requires permissions)
curl http://localhost:8085/api/v1/network/wifi/scan

# Test network configuration
curl -X POST http://localhost:8085/api/v1/network/configure \
  -H "Content-Type: application/json" \
  -d '{"interface":"eth0","method":"dhcp"}'
```