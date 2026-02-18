# System Management API - Quick Reference

## Base URL
```
https://unicorncommander.ai/api/v1/system
```

## Authentication
All endpoints require admin role:
```bash
Authorization: Bearer <JWT_TOKEN>
```

## Endpoints Overview

| Method | Endpoint | Description | Admin Required |
|--------|----------|-------------|----------------|
| GET | `/network` | Get network configuration | Yes |
| PUT | `/network` | Update network configuration | Yes |
| POST | `/user/password` | Change user password | Yes |
| GET | `/packages` | List available package updates | Yes |

## Quick Examples

### 1. Get Network Configuration
```bash
curl -X GET "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response:**
```json
{
  "ip": "192.168.1.100",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns_servers": ["1.1.1.1", "8.8.8.8"],
  "hostname": "uc1-server",
  "interface": "eth0",
  "dhcp": false
}
```

### 2. Update Network (Static IP)
```bash
curl -X PUT "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.150",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns_servers": ["1.1.1.1", "8.8.8.8"],
    "dhcp": false
  }'
```

### 3. Update Network (DHCP)
```bash
curl -X PUT "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dhcp": true}'
```

### 4. Change User Password
```bash
curl -X POST "https://unicorncommander.ai/api/v1/system/user/password" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ubuntu",
    "current_password": "OldPass123",
    "new_password": "NewPass456"
  }'
```

**Password Requirements:**
- Min 8 characters
- 1+ uppercase
- 1+ lowercase
- 1+ digit
- Cannot change root password

### 5. Get Available Updates
```bash
curl -X GET "https://unicorncommander.ai/api/v1/system/packages" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response:**
```json
{
  "packages": [
    {
      "name": "nginx",
      "current_version": "1.18.0-1",
      "available_version": "1.18.0-2",
      "size": "1024 kB",
      "description": "High performance web server"
    }
  ],
  "total_count": 15,
  "last_check": "2025-10-09T14:23:45.123456"
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid token) |
| 403 | Forbidden (not admin) |
| 500 | Internal Server Error |

## Python Client Example

```python
import requests

class SystemManager:
    def __init__(self, base_url, jwt_token):
        self.base_url = f"{base_url}/api/v1/system"
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

    def get_network_config(self):
        response = requests.get(f"{self.base_url}/network", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_network_config(self, config):
        response = requests.put(
            f"{self.base_url}/network",
            headers=self.headers,
            json=config
        )
        response.raise_for_status()
        return response.json()

    def change_password(self, username, current_password, new_password):
        response = requests.post(
            f"{self.base_url}/user/password",
            headers=self.headers,
            json={
                "username": username,
                "current_password": current_password,
                "new_password": new_password
            }
        )
        response.raise_for_status()
        return response.json()

    def get_available_updates(self):
        response = requests.get(f"{self.base_url}/packages", headers=self.headers)
        response.raise_for_status()
        return response.json()

# Usage
manager = SystemManager("https://unicorncommander.ai", "your_jwt_token")
network = manager.get_network_config()
print(f"Current IP: {network['ip']}")
```

## JavaScript/Fetch Example

```javascript
class SystemAPI {
  constructor(baseUrl, jwtToken) {
    this.baseUrl = `${baseUrl}/api/v1/system`;
    this.headers = {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    };
  }

  async getNetworkConfig() {
    const response = await fetch(`${this.baseUrl}/network`, {
      headers: this.headers
    });
    return response.json();
  }

  async updateNetworkConfig(config) {
    const response = await fetch(`${this.baseUrl}/network`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify(config)
    });
    return response.json();
  }

  async changePassword(username, currentPassword, newPassword) {
    const response = await fetch(`${this.baseUrl}/user/password`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        username,
        current_password: currentPassword,
        new_password: newPassword
      })
    });
    return response.json();
  }

  async getAvailableUpdates() {
    const response = await fetch(`${this.baseUrl}/packages`, {
      headers: this.headers
    });
    return response.json();
  }
}

// Usage
const api = new SystemAPI('https://unicorncommander.ai', 'your_jwt_token');
const network = await api.getNetworkConfig();
console.log(`Current IP: ${network.ip}`);
```

## Security Checklist

- [ ] Always use HTTPS in production
- [ ] Store JWT tokens securely
- [ ] Implement token rotation
- [ ] Enable audit logging
- [ ] Have backup access before network changes
- [ ] Test in non-production first
- [ ] Keep system updated
- [ ] Use strong passwords
- [ ] Limit admin access
- [ ] Monitor audit logs

## Files

- **Backend Module:** `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/system_manager.py`
- **API Endpoints:** `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py`
- **Full Documentation:** `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/docs/SYSTEM_MANAGEMENT_API.md`
