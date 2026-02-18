# System Management API Documentation

## Overview

The System Management API provides headless server management capabilities for UC-1 Pro Ops Center. These endpoints allow administrators to manage network configuration, user passwords, and system package updates through a secure REST API.

**Version:** 1.0
**Base URL:** `/api/v1/system`
**Authentication:** Admin role required for all endpoints

## Security

All system management endpoints require:
- **Authentication**: Valid JWT token
- **Authorization**: Admin role (`user.is_admin = true`)
- **Logging**: All operations are logged for audit trails
- **Validation**: All inputs are validated with Pydantic models

## Endpoints

### 1. Get Network Configuration

**Endpoint:** `GET /api/v1/system/network`
**Authentication:** Admin required
**Description:** Retrieve current network configuration from the system.

#### Response Model: `NetworkStatus`

```json
{
  "ip": "192.168.1.100",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns_servers": ["8.8.8.8", "8.8.4.4"],
  "hostname": "uc1-pro-server",
  "interface": "eth0",
  "dhcp": false
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `ip` | string (nullable) | Current IP address |
| `netmask` | string (nullable) | Network mask |
| `gateway` | string (nullable) | Default gateway |
| `dns_servers` | array[string] | List of DNS servers |
| `hostname` | string | System hostname |
| `interface` | string | Primary network interface |
| `dhcp` | boolean | Whether DHCP is enabled |

#### Example Request

```bash
curl -X GET "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Example Response

```json
{
  "ip": "192.168.1.100",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns_servers": ["1.1.1.1", "8.8.8.8"],
  "hostname": "uc1-ops-center",
  "interface": "ens33",
  "dhcp": false
}
```

#### Error Responses

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: User is not an admin
- **500 Internal Server Error**: Failed to read network configuration

---

### 2. Update Network Configuration

**Endpoint:** `PUT /api/v1/system/network`
**Authentication:** Admin required
**Description:** Update network configuration using netplan.

#### Request Model: `NetworkConfig`

```json
{
  "ip": "192.168.1.150",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns_servers": ["1.1.1.1", "8.8.8.8"],
  "hostname": "new-hostname",
  "dhcp": false
}
```

#### Request Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `ip` | string | No* | Static IP address | Must be valid IPv4 format |
| `netmask` | string | No* | Network mask | Must be valid netmask format |
| `gateway` | string | No | Default gateway | Must be valid IPv4 format |
| `dns_servers` | array[string] | No | DNS server list | Each must be valid IPv4 |
| `hostname` | string | No | System hostname | Valid hostname format |
| `dhcp` | boolean | No | Use DHCP | Default: false |

*Required for static IP configuration (when `dhcp = false`)

#### Validation Rules

1. **Static IP Configuration** (dhcp = false):
   - Both `ip` and `netmask` are required
   - IP address must be valid IPv4 format (e.g., "192.168.1.100")
   - Netmask must be valid (e.g., "255.255.255.0")

2. **DHCP Configuration** (dhcp = true):
   - IP and netmask are ignored
   - Gateway and DNS servers are optional

3. **DNS Servers**:
   - Must be valid IPv4 addresses
   - Array can be empty

4. **Hostname**:
   - Must match pattern: `^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$`
   - Max 63 characters

#### Example Request: Static IP

```bash
curl -X PUT "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.150",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns_servers": ["1.1.1.1", "8.8.8.8"],
    "hostname": "uc1-server",
    "dhcp": false
  }'
```

#### Example Request: DHCP

```bash
curl -X PUT "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dhcp": true,
    "hostname": "uc1-server"
  }'
```

#### Example Response

```json
{
  "message": "Network configuration updated successfully",
  "configuration": {
    "ip": "192.168.1.150",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns_servers": ["1.1.1.1", "8.8.8.8"],
    "hostname": "uc1-server",
    "interface": "ens33",
    "dhcp": false
  },
  "warning": "Network changes may cause temporary connection interruption"
}
```

#### Security Features

- Creates backup before applying changes
- Tests configuration with `netplan try` (30-second timeout)
- Logs all configuration changes with admin username
- Validates all inputs before applying

#### Error Responses

- **400 Bad Request**: Invalid configuration (e.g., missing IP for static config)
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: User is not an admin
- **500 Internal Server Error**: Failed to apply configuration

---

### 3. Change User Password

**Endpoint:** `POST /api/v1/system/user/password`
**Authentication:** Admin required
**Description:** Change Linux system user password with verification.

#### Request Model: `SystemPasswordChange`

```json
{
  "username": "ubuntu",
  "current_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

#### Request Fields

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `username` | string | Yes | Username to change password for | Cannot be "root" |
| `current_password` | string | Yes | Current password for verification | - |
| `new_password` | string | Yes | New password to set | Min 8 chars, see rules below |

#### Password Validation Rules

The new password must meet these requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

#### Example Request

```bash
curl -X POST "https://unicorncommander.ai/api/v1/system/user/password" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ubuntu",
    "current_password": "OldPassword123",
    "new_password": "NewSecurePass456"
  }'
```

#### Example Response

```json
{
  "message": "Password changed successfully for user 'ubuntu'",
  "username": "ubuntu"
}
```

#### Security Features

- Verifies current password before allowing change
- Prevents changing root password via API
- Validates password strength
- Logs all password change attempts (without actual passwords)
- Does not return sensitive information in responses
- Requires admin role

#### Error Responses

- **400 Bad Request**:
  - Current password is incorrect
  - Password does not meet strength requirements
  - Invalid input format
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**:
  - User is not an admin
  - Attempt to change root password
- **500 Internal Server Error**: Failed to change password

---

### 4. Get Available Package Updates

**Endpoint:** `GET /api/v1/system/packages`
**Authentication:** Admin required
**Description:** Retrieve list of available system package updates.

#### Response Model: `PackageList`

```json
{
  "packages": [
    {
      "name": "nginx",
      "current_version": "1.18.0-0ubuntu1.2",
      "available_version": "1.18.0-0ubuntu1.4",
      "size": "1024 kB",
      "description": "High performance web server"
    }
  ],
  "total_count": 15,
  "last_check": "2025-10-09T12:34:56.789000"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `packages` | array[PackageInfo] | List of packages with updates |
| `total_count` | integer | Total number of packages with updates |
| `last_check` | datetime | When the package cache was last updated |

#### PackageInfo Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Package name |
| `current_version` | string | Currently installed version |
| `available_version` | string | Version available for update |
| `size` | string (nullable) | Package size (if available) |
| `description` | string (nullable) | Package description (if available) |

#### Example Request

```bash
curl -X GET "https://unicorncommander.ai/api/v1/system/packages" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Example Response

```json
{
  "packages": [
    {
      "name": "docker-ce",
      "current_version": "24.0.5-1",
      "available_version": "24.0.7-1",
      "size": "50.2 MB",
      "description": "Docker container runtime"
    },
    {
      "name": "python3",
      "current_version": "3.10.6-1",
      "available_version": "3.10.8-1",
      "size": "5.4 MB",
      "description": "Python programming language"
    },
    {
      "name": "nginx",
      "current_version": "1.18.0-0ubuntu1.2",
      "available_version": "1.18.0-0ubuntu1.4",
      "size": "1024 kB",
      "description": "High performance web server"
    }
  ],
  "total_count": 3,
  "last_check": "2025-10-09T14:23:45.123456"
}
```

#### Behavior

- Updates apt package cache before checking (`apt-get update`)
- Uses `apt list --upgradable` to get package list
- Fetches size and description from `apt-cache show` (if available)
- Returns empty array if no updates available

#### Security Features

- Read-only operation (does not install updates)
- Requires admin role
- Logs all access attempts

#### Error Responses

- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: User is not an admin
- **500 Internal Server Error**: Failed to retrieve package information

---

## Common Error Responses

All endpoints may return these error responses:

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 400 Bad Request
```json
{
  "detail": "Specific error message describing the validation failure"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Specific error message describing the failure"
}
```

## Logging and Auditing

All system management operations are logged with the following information:
- Admin username performing the action
- Timestamp of the operation
- Action performed
- Success/failure status
- Error messages (if applicable)

**Log Format Example:**
```
2025-10-09 14:23:45 INFO: Network configuration read by admin user: aaron
2025-10-09 14:24:12 INFO: Network configuration update initiated by admin user: aaron
2025-10-09 14:24:12 INFO: Configuration: DHCP=False, IP=192.168.1.150, Gateway=192.168.1.1
2025-10-09 14:24:18 INFO: Network configuration updated successfully by user: aaron
```

## Best Practices

### Network Configuration
1. **Always test in non-production first**: Network changes can cause connectivity loss
2. **Have console access**: Keep SSH session open and have physical/IPMI access ready
3. **Backup configurations**: System creates backups automatically, but keep manual backups too
4. **Use netplan try**: The API uses `netplan try` with 30-second timeout for safety

### Password Changes
1. **Strong passwords**: Use password manager to generate secure passwords
2. **Regular rotation**: Change passwords periodically
3. **Audit logs**: Review password change logs regularly
4. **Avoid root**: Don't use root account for daily operations

### Package Updates
1. **Review before applying**: Check package list before upgrading
2. **Test in staging**: Test updates in non-production environment first
3. **Backup first**: Create system backup before major updates
4. **Schedule maintenance**: Plan updates during maintenance windows

## Integration Examples

### Python Example

```python
import requests

BASE_URL = "https://unicorncommander.ai/api/v1/system"
JWT_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Get current network configuration
response = requests.get(f"{BASE_URL}/network", headers=headers)
network_config = response.json()
print(f"Current IP: {network_config['ip']}")

# Update network configuration
new_config = {
    "ip": "192.168.1.200",
    "netmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns_servers": ["1.1.1.1", "8.8.8.8"],
    "dhcp": False
}
response = requests.put(f"{BASE_URL}/network", headers=headers, json=new_config)
print(response.json())

# Get available package updates
response = requests.get(f"{BASE_URL}/packages", headers=headers)
packages = response.json()
print(f"Available updates: {packages['total_count']}")
for pkg in packages['packages']:
    print(f"  - {pkg['name']}: {pkg['current_version']} → {pkg['available_version']}")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = "https://unicorncommander.ai/api/v1/system";
const JWT_TOKEN = "your_jwt_token_here";

const headers = {
  "Authorization": `Bearer ${JWT_TOKEN}`,
  "Content-Type": "application/json"
};

// Get network configuration
async function getNetworkConfig() {
  const response = await fetch(`${BASE_URL}/network`, { headers });
  const config = await response.json();
  console.log("Current IP:", config.ip);
  return config;
}

// Update network configuration
async function updateNetworkConfig(config) {
  const response = await fetch(`${BASE_URL}/network`, {
    method: "PUT",
    headers,
    body: JSON.stringify(config)
  });
  const result = await response.json();
  console.log("Update result:", result);
  return result;
}

// Change user password
async function changePassword(username, currentPassword, newPassword) {
  const response = await fetch(`${BASE_URL}/user/password`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      username,
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  const result = await response.json();
  console.log("Password change result:", result);
  return result;
}

// Get available updates
async function getAvailableUpdates() {
  const response = await fetch(`${BASE_URL}/packages`, { headers });
  const packages = await response.json();
  console.log(`Available updates: ${packages.total_count}`);
  packages.packages.forEach(pkg => {
    console.log(`  - ${pkg.name}: ${pkg.current_version} → ${pkg.available_version}`);
  });
  return packages;
}
```

## Testing

### Using FastAPI Interactive Docs

Navigate to `https://unicorncommander.ai/docs` to access the interactive Swagger UI documentation where you can:
- View all endpoints and their schemas
- Test endpoints directly in the browser
- See request/response examples
- Download OpenAPI specification

### Using curl

```bash
# Set your JWT token
export JWT_TOKEN="your_jwt_token_here"

# Get network configuration
curl -X GET "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Update to DHCP
curl -X PUT "https://unicorncommander.ai/api/v1/system/network" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dhcp": true}'

# Get available updates
curl -X GET "https://unicorncommander.ai/api/v1/system/packages" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Security Considerations

1. **Transport Security**: Always use HTTPS in production
2. **Token Security**: Store JWT tokens securely, never in plain text
3. **Token Expiration**: Tokens expire after configured time period
4. **Role-Based Access**: Only admin users can access these endpoints
5. **Audit Logging**: All operations are logged for security auditing
6. **Input Validation**: All inputs are validated before processing
7. **Rate Limiting**: Consider implementing rate limiting in production
8. **Network Changes**: Can cause connectivity loss - have backup access

## Support

For issues or questions:
- GitHub: https://github.com/Unicorn-Commander/UC-1-Pro/issues
- Documentation: https://unicorncommander.ai/docs

---

**Last Updated:** October 9, 2025
**API Version:** 1.0
**Module:** system_manager.py
**Endpoints:** server.py
