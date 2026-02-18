# Traefik Configuration Management - API Reference

**Version**: 1.0.0
**Epic**: 1.3 - Traefik Configuration Management
**Last Updated**: October 24, 2025
**Target Audience**: Developers integrating with the API

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Authentication](#2-authentication)
3. [Base URL & Endpoints](#3-base-url--endpoints)
4. [Health & Status](#4-health--status)
5. [Certificate Management](#5-certificate-management)
6. [Route Management](#6-route-management)
7. [Middleware Management](#7-middleware-management)
8. [Service Management](#8-service-management)
9. [Configuration Management](#9-configuration-management)
10. [Error Handling](#10-error-handling)
11. [Rate Limiting](#11-rate-limiting)
12. [Examples](#12-examples)

---

## 1. Introduction

### 1.1 Overview

The Traefik Configuration Management API provides programmatic access to manage Traefik reverse proxy configuration including SSL certificates, routes, middleware, and services.

**Key Features**:
- RESTful HTTP API
- JSON request/response format
- Bearer token authentication
- Automatic configuration validation
- Built-in backup/rollback
- Audit logging
- Rate limiting

### 1.2 API Versions

| Version | Status | Base Path |
|---------|--------|-----------|
| 1.0 | Current | `/api/v1/traefik` |

### 1.3 Technology Stack

**Backend**: FastAPI (Python 3.10+)
**Validation**: Pydantic models
**Configuration Format**: YAML
**Storage**: File-based (`/traefik/dynamic/*.yml`)

---

## 2. Authentication

### 2.1 Authentication Methods

All API endpoints require authentication using a Bearer token obtained through Keycloak SSO.

**Authentication Header**:
```
Authorization: Bearer <JWT_TOKEN>
```

### 2.2 Obtaining a Token

**Via Keycloak OAuth2 Flow**:

1. **Authorization Code Flow** (Web Applications):
```http
GET https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/auth
  ?client_id=ops-center
  &redirect_uri=https://unicorncommander.ai/auth/callback
  &response_type=code
  &scope=openid profile email
```

2. **Exchange Code for Token**:
```bash
curl -X POST https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=ops-center" \
  -d "client_secret=your-keycloak-client-secret" \
  -d "code=AUTH_CODE" \
  -d "redirect_uri=https://unicorncommander.ai/auth/callback"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI...",
  "expires_in": 300,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
  "token_type": "Bearer"
}
```

### 2.3 Token Storage

**Browser/JavaScript**:
```javascript
// Store in localStorage (Ops-Center default)
localStorage.setItem('authToken', access_token);

// Include in API requests
fetch('/api/v1/traefik/routes', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
  }
});
```

### 2.4 Authorization

**Required Roles**:
- `admin`: Full access (read, write, delete)
- `moderator`: Read-only access

**Insufficient Permissions**:
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Insufficient permissions. Admin role required."
}
```

---

## 3. Base URL & Endpoints

### 3.1 Base URL

**Production**: `https://unicorncommander.ai/api/v1/traefik`
**Development**: `http://localhost:8084/api/v1/traefik`

### 3.2 Endpoint Summary

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Health** | `/health` | GET | API health check |
| **Status** | `/status` | GET | Overall Traefik status |
| **Certificates** | `/certificates` | GET | List all certificates |
| **Certificates** | `/certificates` | POST | Request new certificate |
| **Certificates** | `/certificates/{domain}` | GET | Get certificate info |
| **Certificates** | `/certificates/{domain}` | DELETE | Revoke certificate |
| **ACME** | `/acme/status` | GET | ACME status |
| **Routes** | `/routes` | GET | List all routes |
| **Routes** | `/routes` | POST | Create route |
| **Routes** | `/routes/{name}` | GET | Get route details |
| **Routes** | `/routes/{name}` | PUT | Update route |
| **Routes** | `/routes/{name}` | DELETE | Delete route |
| **Middleware** | `/middleware` | GET | List all middleware |
| **Middleware** | `/middleware` | POST | Create middleware |
| **Middleware** | `/middleware/{name}` | GET | Get middleware details |
| **Middleware** | `/middleware/{name}` | PUT | Update middleware |
| **Middleware** | `/middleware/{name}` | DELETE | Delete middleware |
| **Services** | `/services` | GET | List all services |
| **Services** | `/services` | POST | Create service |
| **Services** | `/services/{name}` | GET | Get service details |
| **Services** | `/services/{name}` | PUT | Update service |
| **Services** | `/services/{name}` | DELETE | Delete service |
| **Config** | `/config` | GET | Get configuration |
| **Config** | `/config` | PUT | Update configuration |
| **Config** | `/config/validate` | POST | Validate configuration |
| **Config** | `/config/summary` | GET | Configuration summary |
| **Backup** | `/config/backup` | POST | Create backup |
| **Backup** | `/backups` | GET | List backups |
| **Restore** | `/config/restore/{backup_id}` | POST | Restore backup |
| **Reload** | `/reload` | POST | Reload Traefik |

---

## 4. Health & Status

### 4.1 Health Check

**GET** `/api/v1/traefik/health`

Check if the Traefik Management API is operational.

**Authentication**: Not required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "traefik-management-api",
  "version": "1.0.0-simplified",
  "epic": "1.3"
}
```

### 4.2 Traefik Status

**GET** `/api/v1/traefik/status`

Get overall Traefik operational status and statistics.

**Authentication**: Required (Bearer token)

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/status \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "status": "operational",
  "routes_count": 15,
  "certificates_count": 8,
  "timestamp": "2025-10-24T14:30:00.123456Z"
}
```

**Response Fields**:
- `status`: `operational`, `degraded`, or `down`
- `routes_count`: Total number of configured routes
- `certificates_count`: Total number of SSL certificates
- `timestamp`: ISO 8601 UTC timestamp

**Error Response** (500 Internal Server Error):
```json
{
  "detail": "Failed to fetch Traefik status: Connection refused"
}
```

---

## 5. Certificate Management

### 5.1 List Certificates

**GET** `/api/v1/traefik/certificates`

Retrieve all SSL/TLS certificates managed by Traefik.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/certificates \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "certificates": [
    {
      "domain": "unicorncommander.ai",
      "sans": ["www.unicorncommander.ai"],
      "resolver": "letsencrypt",
      "status": "active",
      "not_after": "2025-01-20T12:00:00Z",
      "certificate": "-----BEGIN CERTIFICATE-----\nMIIE...",
      "private_key_present": true
    },
    {
      "domain": "chat.unicorncommander.ai",
      "sans": [],
      "resolver": "letsencrypt",
      "status": "active",
      "not_after": "2025-01-15T09:30:00Z",
      "certificate": "-----BEGIN CERTIFICATE-----\nMIIF...",
      "private_key_present": true
    }
  ],
  "count": 2
}
```

**Response Fields**:
- `domain`: Primary domain name
- `sans`: Subject Alternative Names (additional domains)
- `resolver`: Certificate resolver name (e.g., `letsencrypt`)
- `status`: `active`, `pending`, `expired`, `revoked`, or `failed`
- `not_after`: Certificate expiry date (ISO 8601)
- `certificate`: First 50 characters of PEM certificate
- `private_key_present`: Boolean indicating if private key exists

**Error Response** (500):
```json
{
  "detail": "Failed to list certificates: ACME file not found"
}
```

### 5.2 Get Certificate Info

**GET** `/api/v1/traefik/certificates/{domain}`

Retrieve detailed information for a specific certificate.

**Authentication**: Required

**Path Parameters**:
- `domain`: Domain name (e.g., `unicorncommander.ai`)

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/certificates/unicorncommander.ai \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "certificate": {
    "domain": "unicorncommander.ai",
    "sans": ["www.unicorncommander.ai"],
    "resolver": "letsencrypt",
    "status": "active",
    "not_after": "2025-01-20T12:00:00Z",
    "certificate": "-----BEGIN CERTIFICATE-----\nMIIE...",
    "private_key_present": true
  }
}
```

**Error Response** (404):
```json
{
  "detail": "Certificate not found for domain: example.com"
}
```

### 5.3 Request Certificate

**POST** `/api/v1/traefik/certificates`

Request a new SSL certificate from Let's Encrypt.

**Authentication**: Required

**Request Body**:
```json
{
  "domain": "example.unicorncommander.ai",
  "email": "admin@unicorncommander.ai",
  "sans": ["www.example.unicorncommander.ai"]
}
```

**Request Fields**:
- `domain` (required): Primary domain name
- `email` (required): Contact email for Let's Encrypt notifications
- `sans` (optional): Array of Subject Alternative Names

**Request Example**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.unicorncommander.ai",
    "email": "admin@unicorncommander.ai"
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Certificate request initiated for example.unicorncommander.ai",
  "domain": "example.unicorncommander.ai",
  "sans": [],
  "status": "pending",
  "note": "Certificate will be automatically issued when DNS is properly configured"
}
```

**Validation Errors** (400):
```json
{
  "detail": "Invalid certificate request: Invalid domain format: example-.com"
}
```

### 5.4 Revoke Certificate

**DELETE** `/api/v1/traefik/certificates/{domain}`

Revoke an SSL certificate (removes from Traefik storage).

**Authentication**: Required

**Path Parameters**:
- `domain`: Domain name

**Request**:
```bash
curl -X DELETE https://unicorncommander.ai/api/v1/traefik/certificates/example.com \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Certificate revoked for example.com",
  "domain": "example.com",
  "note": "Certificate will be re-requested automatically if still in use"
}
```

**Error Response** (404):
```json
{
  "detail": "Certificate not found for domain: example.com"
}
```

### 5.5 ACME Status

**GET** `/api/v1/traefik/acme/status`

Get ACME (Let's Encrypt) configuration status.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/acme/status \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "acme_status": {
    "initialized": true,
    "total_certificates": 8,
    "resolvers": [
      {
        "name": "letsencrypt",
        "certificates": 8,
        "email": "admin@unicorncommander.ai",
        "ca_server": "https://acme-v02.api.letsencrypt.org/directory"
      }
    ],
    "acme_file": "/opt/uc-cloud/traefik/acme/acme.json",
    "file_size": 45678,
    "last_modified": "2025-10-24T10:15:30.123456Z"
  }
}
```

---

## 6. Route Management

### 6.1 List Routes

**GET** `/api/v1/traefik/routes`

List all HTTP/HTTPS routing rules.

**Authentication**: Required

**Query Parameters**:
- `limit` (optional): Maximum results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Request**:
```bash
curl -X GET "https://unicorncommander.ai/api/v1/traefik/routes?limit=50&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "routes": [
    {
      "name": "ops-center",
      "rule": "Host(`unicorncommander.ai`)",
      "service": "ops-center-svc",
      "entrypoints": ["websecure"],
      "middlewares": ["rate-limit", "security-headers"],
      "priority": 100,
      "tls_enabled": true,
      "cert_resolver": "letsencrypt",
      "source_file": "routes.yml"
    },
    {
      "name": "brigade-api",
      "rule": "Host(`api.brigade.unicorncommander.ai`)",
      "service": "brigade-backend-svc",
      "entrypoints": ["websecure"],
      "middlewares": [],
      "priority": 0,
      "tls_enabled": true,
      "cert_resolver": "letsencrypt",
      "source_file": "routes.yml"
    }
  ],
  "count": 2
}
```

**Response Fields**:
- `name`: Unique route identifier
- `rule`: Traefik matching rule
- `service`: Backend service name
- `entrypoints`: Network entry points (`web`, `websecure`)
- `middlewares`: Applied middleware names
- `priority`: Route priority (0-1000, higher = evaluated first)
- `tls_enabled`: HTTPS enabled
- `cert_resolver`: Certificate resolver name
- `source_file`: Configuration file name

### 6.2 Create Route

**POST** `/api/v1/traefik/routes`

Create a new routing rule.

**Authentication**: Required (admin role)

**Request Body**:
```json
{
  "name": "my-service-route",
  "rule": "Host(`example.unicorncommander.ai`)",
  "service": "my-service-svc",
  "entrypoints": ["websecure"],
  "middlewares": ["rate-limit"],
  "priority": 50,
  "tls_enabled": true,
  "cert_resolver": "letsencrypt"
}
```

**Request Fields**:
- `name` (required): Route name (lowercase, alphanumeric, hyphens only)
- `rule` (required): Traefik rule syntax
- `service` (required): Backend service name
- `entrypoints` (optional): Default `["websecure"]`
- `middlewares` (optional): Middleware names to apply
- `priority` (optional): 0-1000, default 0
- `tls_enabled` (optional): Default `true`
- `cert_resolver` (optional): Default `"letsencrypt"`

**Request Example**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/routes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-route",
    "rule": "Host(`api.example.com`) && PathPrefix(`/v1`)",
    "service": "api-backend-svc",
    "middlewares": ["rate-limit", "api-auth"]
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Route 'api-route' created successfully",
  "route": {
    "name": "api-route",
    "rule": "Host(`api.example.com`) && PathPrefix(`/v1`)",
    "service": "api-backend-svc",
    "entrypoints": ["websecure"],
    "middlewares": ["rate-limit", "api-auth"],
    "tls_enabled": true
  },
  "backup": "/traefik/backups/traefik_backup_20251024_143000"
}
```

**Validation Errors** (400):
```json
{
  "detail": "Invalid route parameters: Route name must be lowercase alphanumeric with hyphens only"
}
```

**Already Exists** (400):
```json
{
  "detail": "Route 'api-route' already exists"
}
```

### 6.3 Update Route

**PUT** `/api/v1/traefik/routes/{name}`

Update an existing route.

**Authentication**: Required (admin role)

**Path Parameters**:
- `name`: Route name

**Request Body**:
```json
{
  "rule": "Host(`api.example.com`) && PathPrefix(`/v2`)",
  "service": "api-v2-backend-svc",
  "middlewares": ["rate-limit", "api-auth", "compress"]
}
```

**Request Example**:
```bash
curl -X PUT https://unicorncommander.ai/api/v1/traefik/routes/api-route \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule": "Host(`api.example.com`) && PathPrefix(`/v2`)",
    "middlewares": ["rate-limit", "api-auth", "compress"]
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Route 'api-route' updated successfully",
  "route": {
    "rule": "Host(`api.example.com`) && PathPrefix(`/v2`)",
    "service": "api-v2-backend-svc",
    "entryPoints": ["websecure"],
    "middlewares": ["rate-limit", "api-auth", "compress"],
    "tls": {
      "certResolver": "letsencrypt"
    }
  },
  "backup": "/traefik/backups/traefik_backup_20251024_143500"
}
```

### 6.4 Delete Route

**DELETE** `/api/v1/traefik/routes/{name}`

Delete a routing rule.

**Authentication**: Required (admin role)

**Path Parameters**:
- `name`: Route name

**Request**:
```bash
curl -X DELETE https://unicorncommander.ai/api/v1/traefik/routes/api-route \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Route 'api-route' deleted successfully",
  "backup": "/traefik/backups/traefik_backup_20251024_144000"
}
```

**Error** (404):
```json
{
  "detail": "Route 'api-route' not found"
}
```

---

## 7. Middleware Management

### 7.1 List Middleware

**GET** `/api/v1/traefik/middleware`

List all middleware components.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/middleware \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "middleware": [
    {
      "name": "rate-limit",
      "type": "rateLimit",
      "config": {
        "average": 100,
        "period": "1m",
        "burst": 50
      },
      "source_file": "middleware.yml"
    },
    {
      "name": "security-headers",
      "type": "headers",
      "config": {
        "customResponseHeaders": {
          "X-Frame-Options": "SAMEORIGIN",
          "X-Content-Type-Options": "nosniff"
        }
      },
      "source_file": "middleware.yml"
    }
  ],
  "count": 2
}
```

### 7.2 Create Middleware

**POST** `/api/v1/traefik/middleware`

Create a new middleware component.

**Authentication**: Required (admin role)

**Request Body**:
```json
{
  "name": "api-rate-limit",
  "type": "rateLimit",
  "config": {
    "average": 50,
    "period": "1m",
    "burst": 25
  }
}
```

**Supported Middleware Types**:
- `rateLimit`: Rate limiting
- `headers`: Custom headers
- `cors`: CORS configuration
- `forwardAuth`: External authentication
- `redirectScheme`: HTTP to HTTPS redirect
- `compress`: Response compression
- `stripPrefix`: Remove path prefix
- `addPrefix`: Add path prefix
- `basicAuth`: Basic authentication
- `ipWhiteList`: IP address filtering

**Request Example**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/middleware \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-rate-limit",
    "type": "rateLimit",
    "config": {
      "average": 50,
      "period": "1m",
      "burst": 25
    }
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Middleware 'api-rate-limit' created successfully",
  "middleware": {
    "name": "api-rate-limit",
    "type": "rateLimit",
    "config": {
      "average": 50,
      "period": "1m",
      "burst": 25
    }
  },
  "backup": "/traefik/backups/traefik_backup_20251024_145000"
}
```

**Validation Errors** (400):
```json
{
  "detail": "Invalid middleware parameters: RateLimit middleware requires: ['average', 'period']"
}
```

### 7.3 Update Middleware

**PUT** `/api/v1/traefik/middleware/{name}`

Update an existing middleware.

**Authentication**: Required (admin role)

**Path Parameters**:
- `name`: Middleware name

**Request Body**:
```json
{
  "config": {
    "average": 100,
    "period": "1m",
    "burst": 50
  }
}
```

**Request Example**:
```bash
curl -X PUT https://unicorncommander.ai/api/v1/traefik/middleware/api-rate-limit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "average": 100,
      "period": "1m",
      "burst": 50
    }
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Middleware 'api-rate-limit' updated successfully",
  "middleware": {
    "rateLimit": {
      "average": 100,
      "period": "1m",
      "burst": 50
    }
  },
  "backup": "/traefik/backups/traefik_backup_20251024_145500"
}
```

### 7.4 Delete Middleware

**DELETE** `/api/v1/traefik/middleware/{name}`

Delete a middleware component.

**Authentication**: Required (admin role)

**Path Parameters**:
- `name`: Middleware name

**Request**:
```bash
curl -X DELETE https://unicorncommander.ai/api/v1/traefik/middleware/api-rate-limit \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Middleware 'api-rate-limit' deleted successfully",
  "backup": "/traefik/backups/traefik_backup_20251024_150000"
}
```

---

## 8. Service Management

### 8.1 List Services

**GET** `/api/v1/traefik/services`

List all backend service definitions.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/services \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "services": [
    "ops-center-svc",
    "brigade-backend-svc",
    "brigade-ui-svc",
    "openwebui-svc"
  ],
  "count": 4
}
```

**Note**: Service management endpoints (POST, PUT, DELETE) are not yet implemented in the current version. Services are typically auto-discovered from Docker containers.

---

## 9. Configuration Management

### 9.1 Get Configuration

**GET** `/api/v1/traefik/config`

Retrieve current Traefik configuration.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/config \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "config": "http:\n  routers:\n    ops-center:\n      rule: Host(`unicorncommander.ai`)\n      service: ops-center-svc\n      entryPoints:\n        - websecure\n      tls:\n        certResolver: letsencrypt\n  services:\n    ops-center-svc:\n      loadBalancer:\n        servers:\n          - url: http://ops-center-direct:8084\n  middlewares:\n    rate-limit:\n      rateLimit:\n        average: 100\n        period: 1m\n"
}
```

**Response Fields**:
- `config`: Full YAML configuration as string

### 9.2 Update Configuration

**PUT** `/api/v1/traefik/config`

Update Traefik configuration.

**Authentication**: Required (admin role)

**Request Body**:
```json
{
  "config": "http:\n  routers:\n    new-route:\n      rule: Host(`new.example.com`)\n      service: new-service\n"
}
```

**Request Example**:
```bash
curl -X PUT https://unicorncommander.ai/api/v1/traefik/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": "..."
  }'
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "backup": "/traefik/backups/traefik_backup_20251024_151000"
}
```

**Validation Error** (400):
```json
{
  "detail": "Configuration validation failed: Invalid YAML syntax at line 15"
}
```

### 9.3 Validate Configuration

**POST** `/api/v1/traefik/config/validate`

Validate configuration without saving.

**Authentication**: Required

**Request Body**:
```json
{
  "config": "http:\n  routers:\n    test-route:\n      rule: Host(`test.example.com`)\n      service: test-svc\n"
}
```

**Request Example**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/config/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": "..."
  }'
```

**Response** (200 OK):
```json
{
  "valid": true,
  "message": "Configuration is valid"
}
```

**Invalid Configuration** (400):
```json
{
  "detail": "Configuration validation failed: Router 'test-route' missing 'service'"
}
```

### 9.4 Configuration Summary

**GET** `/api/v1/traefik/config/summary`

Get a summary of current configuration.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/config/summary \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "summary": {
    "routes": 15,
    "certificates": 8
  },
  "timestamp": "2025-10-24T15:30:00.123456Z"
}
```

### 9.5 Create Backup

**POST** `/api/v1/traefik/config/backup`

Create a timestamped backup of all configurations.

**Authentication**: Required (admin role)

**Request**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/config/backup \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Backup created successfully",
  "backup_path": "/traefik/backups/traefik_backup_20251024_153000",
  "files_backed_up": [
    "traefik.yml",
    "dynamic/routes.yml",
    "dynamic/middleware.yml",
    "acme.json"
  ],
  "timestamp": "2025-10-24T15:30:00.123456Z"
}
```

### 9.6 List Backups

**GET** `/api/v1/traefik/backups`

List all available configuration backups.

**Authentication**: Required

**Request**:
```bash
curl -X GET https://unicorncommander.ai/api/v1/traefik/backups \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "backups": [
    "traefik_backup_20251024_153000",
    "traefik_backup_20251024_143000",
    "traefik_backup_20251024_133000",
    "traefik_backup_20251023_180000"
  ],
  "count": 4
}
```

### 9.7 Restore Backup

**POST** `/api/v1/traefik/config/restore/{backup_id}`

Restore configuration from a backup.

**Authentication**: Required (admin role)

**Path Parameters**:
- `backup_id`: Backup directory name (e.g., `traefik_backup_20251024_153000`)

**Request**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/config/restore/traefik_backup_20251024_153000 \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Configuration restored from backup: 2025-10-24T15:30:00Z",
  "backup_restored": "/traefik/backups/traefik_backup_20251024_153000",
  "safety_backup": "/traefik/backups/traefik_backup_20251024_154500"
}
```

**Note**: A safety backup of the current configuration is automatically created before restoring.

### 9.8 Reload Traefik

**POST** `/api/v1/traefik/reload`

Trigger Traefik configuration reload.

**Authentication**: Required (admin role)

**Request**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/reload \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Traefik configuration reloaded",
  "status": "healthy"
}
```

**Note**: Traefik automatically reloads when dynamic configuration files change. Manual reload is typically not needed.

---

## 10. Error Handling

### 10.1 HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters or validation error |
| 401 | Unauthorized | Authentication required or token invalid |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 501 | Not Implemented | Feature not yet implemented |

### 10.2 Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Examples**:

**Validation Error**:
```json
{
  "detail": "Invalid route parameters: Route name must be lowercase alphanumeric with hyphens only"
}
```

**Not Found**:
```json
{
  "detail": "Route 'unknown-route' not found"
}
```

**Authentication Error**:
```json
{
  "detail": "Authentication required. Please provide a valid Bearer token."
}
```

**Authorization Error**:
```json
{
  "detail": "Insufficient permissions. Admin role required."
}
```

**Rate Limit Error**:
```json
{
  "detail": "Rate limit exceeded: 5/5 changes in 60s. Wait 45s before retrying."
}
```

### 10.3 Validation Errors

Pydantic model validation errors provide detailed field-level information:

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "String should match pattern '^[a-z0-9-]+$'",
      "type": "string_pattern_mismatch"
    },
    {
      "loc": ["body", "rule"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

---

## 11. Rate Limiting

### 11.1 API Rate Limits

To prevent abuse and ensure system stability, the Traefik Management API implements rate limiting:

**Limits**:
- **5 configuration changes per minute** per user
- **Unlimited read operations** (GET requests)

**Affected Operations**:
- POST (create)
- PUT (update)
- DELETE (delete)

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1729785600
```

**Rate Limit Exceeded** (429):
```json
{
  "detail": "Rate limit exceeded: 5/5 changes in 60s. Wait 45s before retrying."
}
```

### 11.2 Best Practices

**Batch Operations**:
- Create multiple routes in a single configuration update instead of individual API calls
- Use the Configuration API (`PUT /config`) for bulk changes

**Cache Read Operations**:
- Cache route and middleware lists on the client side
- Refresh only when necessary

**Retry Logic**:
```javascript
async function createRouteWithRetry(routeData) {
  try {
    const response = await fetch('/api/v1/traefik/routes', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(routeData)
    });

    if (response.status === 429) {
      const data = await response.json();
      const waitTime = extractWaitTime(data.detail); // Parse "Wait 45s"
      await sleep(waitTime * 1000);
      return createRouteWithRetry(routeData); // Retry
    }

    return response.json();
  } catch (error) {
    console.error('Failed to create route:', error);
  }
}
```

---

## 12. Examples

### 12.1 Complete Route Creation Workflow

**Step 1: Request SSL Certificate**
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "myapp.unicorncommander.ai",
    "email": "admin@unicorncommander.ai"
  }'
```

**Step 2: Create Rate Limit Middleware**
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/middleware \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myapp-rate-limit",
    "type": "rateLimit",
    "config": {
      "average": 50,
      "period": "1m",
      "burst": 25
    }
  }'
```

**Step 3: Create Route**
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/routes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myapp-route",
    "rule": "Host(`myapp.unicorncommander.ai`)",
    "service": "myapp-backend-svc",
    "middlewares": ["myapp-rate-limit"],
    "tls_enabled": true
  }'
```

**Step 4: Verify Route**
```bash
# Test the route
curl -I https://myapp.unicorncommander.ai

# Should return 200 OK with SSL certificate
```

### 12.2 Updating Multiple Routes

```bash
# Get current routes
curl -X GET https://unicorncommander.ai/api/v1/traefik/routes \
  -H "Authorization: Bearer $TOKEN" > routes.json

# Modify routes.json (add new middleware)

# Update via configuration API
curl -X PUT https://unicorncommander.ai/api/v1/traefik/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @updated-config.json
```

### 12.3 Backup and Restore

**Create Backup Before Major Changes**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/config/backup \
  -H "Authorization: Bearer $TOKEN"

# Returns backup ID: traefik_backup_20251024_153000
```

**Make Changes**:
```bash
# ... perform route updates ...
```

**Restore if Something Goes Wrong**:
```bash
curl -X POST https://unicorncommander.ai/api/v1/traefik/config/restore/traefik_backup_20251024_153000 \
  -H "Authorization: Bearer $TOKEN"
```

### 12.4 Monitoring Certificate Expiry

```bash
# Get all certificates
curl -X GET https://unicorncommander.ai/api/v1/traefik/certificates \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.certificates[] | {domain, status, not_after}'

# Output:
# {
#   "domain": "unicorncommander.ai",
#   "status": "active",
#   "not_after": "2025-01-20T12:00:00Z"
# }
```

### 12.5 Python SDK Example

```python
import requests
import json
from datetime import datetime

class TraefikAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def list_routes(self):
        """List all routes"""
        response = requests.get(
            f'{self.base_url}/routes',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_route(self, name, rule, service, middlewares=None):
        """Create a new route"""
        data = {
            'name': name,
            'rule': rule,
            'service': service,
            'middlewares': middlewares or []
        }
        response = requests.post(
            f'{self.base_url}/routes',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def list_certificates(self):
        """List all SSL certificates"""
        response = requests.get(
            f'{self.base_url}/certificates',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def request_certificate(self, domain, email):
        """Request a new SSL certificate"""
        data = {
            'domain': domain,
            'email': email
        }
        response = requests.post(
            f'{self.base_url}/certificates',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

# Usage
api = TraefikAPI(
    base_url='https://unicorncommander.ai/api/v1/traefik',
    token='YOUR_JWT_TOKEN'
)

# List routes
routes = api.list_routes()
print(f"Total routes: {routes['count']}")

# Create route
result = api.create_route(
    name='my-api-route',
    rule='Host(`api.example.com`) && PathPrefix(`/v1`)',
    service='api-backend-svc',
    middlewares=['rate-limit', 'api-auth']
)
print(f"Route created: {result['message']}")

# List certificates
certs = api.list_certificates()
for cert in certs['certificates']:
    print(f"Domain: {cert['domain']}, Status: {cert['status']}")
```

### 12.6 JavaScript/Node.js Example

```javascript
const axios = require('axios');

class TraefikAPI {
  constructor(baseURL, token) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async listRoutes() {
    const response = await this.client.get('/routes');
    return response.data;
  }

  async createRoute(name, rule, service, middlewares = []) {
    const data = { name, rule, service, middlewares };
    const response = await this.client.post('/routes', data);
    return response.data;
  }

  async listCertificates() {
    const response = await this.client.get('/certificates');
    return response.data;
  }

  async requestCertificate(domain, email) {
    const data = { domain, email };
    const response = await this.client.post('/certificates', data);
    return response.data;
  }

  async createBackup() {
    const response = await this.client.post('/config/backup');
    return response.data;
  }
}

// Usage
const api = new TraefikAPI(
  'https://unicorncommander.ai/api/v1/traefik',
  'YOUR_JWT_TOKEN'
);

(async () => {
  try {
    // Create backup before changes
    const backup = await api.createBackup();
    console.log('Backup created:', backup.backup_path);

    // Create route
    const route = await api.createRoute(
      'my-route',
      'Host(`example.com`)',
      'my-service-svc',
      ['rate-limit']
    );
    console.log('Route created:', route.message);

    // List all routes
    const routes = await api.listRoutes();
    console.log('Total routes:', routes.count);

  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
  }
})();
```

---

## Appendix A: Traefik Rule Syntax Reference

### Host Matching
```
Host(`example.com`)
Host(`example.com`, `www.example.com`)
HostRegexp(`{subdomain:[a-z]+}.example.com`)
```

### Path Matching
```
Path(`/api`)
PathPrefix(`/api`)
PathRegexp(`^/api/v[0-9]+`)
```

### Method Matching
```
Method(`GET`)
Method(`GET`, `POST`)
```

### Header Matching
```
Headers(`Content-Type`, `application/json`)
HeadersRegexp(`User-Agent`, `.*Chrome.*`)
```

### Query Matching
```
Query(`debug`, `true`)
QueryRegexp(`version`, `^v[0-9]+$`)
```

### Combining Rules
```
Host(`example.com`) && PathPrefix(`/api`)
Host(`example.com`) || Host(`www.example.com`)
(Host(`example.com`) || Host(`www.example.com`)) && PathPrefix(`/api`)
```

---

## Appendix B: Middleware Configuration Examples

### Rate Limiting
```yaml
rateLimit:
  average: 100
  period: 1m
  burst: 50
```

### Basic Auth
```yaml
basicAuth:
  users:
    - "user:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
  realm: "Protected Area"
```

### HTTPS Redirect
```yaml
redirectScheme:
  scheme: https
  permanent: true
```

### Custom Headers
```yaml
headers:
  customResponseHeaders:
    X-Frame-Options: "SAMEORIGIN"
    X-Content-Type-Options: "nosniff"
  customRequestHeaders:
    X-Forwarded-Proto: "https"
```

### IP Whitelist
```yaml
ipWhiteList:
  sourceRange:
    - "192.168.1.0/24"
    - "10.0.0.0/8"
```

### Forward Auth
```yaml
forwardAuth:
  address: "http://authelia:9091/api/verify"
  trustForwardHeader: true
  authResponseHeaders:
    - "Remote-User"
    - "Remote-Groups"
```

---

## Appendix C: Postman Collection

Import this collection into Postman for quick API testing:

```json
{
  "info": {
    "name": "Traefik Configuration Management API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{JWT_TOKEN}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://unicorncommander.ai/api/v1/traefik"
    },
    {
      "key": "JWT_TOKEN",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/health"
      }
    },
    {
      "name": "List Routes",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/routes"
      }
    },
    {
      "name": "Create Route",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/routes",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"test-route\",\n  \"rule\": \"Host(`test.example.com`)\",\n  \"service\": \"test-svc\"\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        }
      }
    },
    {
      "name": "List Certificates",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/certificates"
      }
    },
    {
      "name": "Request Certificate",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/certificates",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"domain\": \"test.example.com\",\n  \"email\": \"admin@example.com\"\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        }
      }
    }
  ]
}
```

---

**Document Version**: 1.0.0
**Last Updated**: October 24, 2025
**API Endpoint**: https://unicorncommander.ai/api/v1/traefik
**Support**: support@magicunicorn.tech
