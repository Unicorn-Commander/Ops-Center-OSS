# Traefik Management API Reference

**Epic 1.3 - Developer Documentation**
**Version**: 1.0.0
**Last Updated**: October 23, 2025
**Base URL**: `/api/v1/traefik`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [SSL Certificate Endpoints](#ssl-certificate-endpoints)
5. [Route Endpoints](#route-endpoints)
6. [Middleware Endpoints](#middleware-endpoints)
7. [Configuration Endpoints](#configuration-endpoints)
8. [Backup & Restore Endpoints](#backup--restore-endpoints)
9. [Health & Status Endpoints](#health--status-endpoints)
10. [Error Codes](#error-codes)
11. [Rate Limiting](#rate-limiting)
12. [Code Examples](#code-examples)

---

## Overview

The Traefik Management API provides programmatic access to all Traefik configuration features available in the Ops-Center web interface.

### API Characteristics

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON Payloads**: All requests and responses use JSON
- **Authentication Required**: Bearer token authentication (except health endpoint)
- **Rate Limited**: 1000 requests/hour per API key
- **Versioned**: `/api/v1/` prefix for version 1
- **HTTPS Only**: All endpoints require SSL/TLS

### Base URL

```
https://yourdomain.com/api/v1/traefik
```

Replace `yourdomain.com` with your Ops-Center domain.

---

## Authentication

All endpoints (except `/health`) require authentication using a Bearer token.

### Obtaining an API Token

1. **Login to Ops-Center** via web interface
2. **Navigate to**: Admin → API Keys
3. **Click**: "Generate New API Key"
4. **Select Scopes**: `traefik:read`, `traefik:write`
5. **Copy Token**: Token displayed once only!

### Authentication Header

Include the token in every request:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Example Request

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://yourdomain.com/api/v1/traefik/certificates
```

### Token Scopes

| Scope | Permissions |
|-------|-------------|
| `traefik:read` | View certificates, routes, middleware, configuration |
| `traefik:write` | Create, update, delete all resources |
| `traefik:certificates` | Manage SSL certificates only |
| `traefik:routes` | Manage routes only |
| `traefik:middleware` | Manage middleware only |
| `traefik:config` | Edit configuration files |

**Best Practice**: Use least-privilege scopes. Read-only monitoring = `traefik:read`.

### Token Expiry

- **Default Expiry**: 90 days
- **Renewable**: Yes (before expiry)
- **Revocable**: Yes (immediately effective)

### Authentication Errors

| Status | Error | Meaning |
|--------|-------|---------|
| `401` | `missing_token` | No Authorization header |
| `401` | `invalid_token` | Token malformed or invalid |
| `401` | `expired_token` | Token past expiry date |
| `403` | `insufficient_scope` | Token lacks required scope |

---

## Common Response Formats

### Success Response

```json
{
  "success": true,
  "data": { /* response data */ },
  "meta": {
    "timestamp": "2025-10-23T12:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Domain name is required",
    "details": {
      "field": "domain",
      "constraint": "required"
    }
  },
  "meta": {
    "timestamp": "2025-10-23T12:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Pagination (List Endpoints)

```json
{
  "success": true,
  "data": [ /* items */ ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

**Pagination Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `sort`: Sort field (e.g., `created_at`)
- `order`: Sort order (`asc` or `desc`)

---

## SSL Certificate Endpoints

### List Certificates

**GET** `/certificates`

Retrieve all SSL certificates.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `valid`, `expiring`, `expired` |
| `domain` | string | Filter by domain (supports wildcards) |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/certificates?status=valid&per_page=10"
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "cert_abc123",
      "domain": "example.com",
      "status": "valid",
      "issuer": "Let's Encrypt",
      "valid_from": "2025-01-01T00:00:00Z",
      "valid_until": "2026-01-01T00:00:00Z",
      "renewal_date": "2025-12-02T00:00:00Z",
      "san": ["www.example.com", "api.example.com"],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10,
    "total_pages": 1
  }
}
```

---

### Get Certificate Details

**GET** `/certificates/{id}`

Retrieve detailed information about a specific certificate.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Certificate ID |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/certificates/cert_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "cert_abc123",
    "domain": "example.com",
    "status": "valid",
    "issuer": "Let's Encrypt",
    "serial_number": "03F5E1234567890ABCDEF",
    "algorithm": "RSA",
    "key_size": 2048,
    "valid_from": "2025-01-01T00:00:00Z",
    "valid_until": "2026-01-01T00:00:00Z",
    "renewal_date": "2025-12-02T00:00:00Z",
    "days_until_expiry": 340,
    "san": ["www.example.com", "api.example.com"],
    "certificate_chain": [
      {
        "subject": "CN=example.com",
        "issuer": "CN=Let's Encrypt Authority X3"
      },
      {
        "subject": "CN=Let's Encrypt Authority X3",
        "issuer": "CN=DST Root CA X3"
      }
    ],
    "auto_renewal": true,
    "last_renewal_attempt": "2025-10-15T00:00:00Z",
    "last_renewal_status": "success",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-10-15T00:00:00Z"
  }
}
```

---

### Request Certificate

**POST** `/certificates`

Request a new SSL certificate from Let's Encrypt.

**Request Body**:
```json
{
  "domain": "example.com",
  "email": "admin@example.com",
  "wildcard": false,
  "dns_provider": null
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | Yes | Domain name (e.g., example.com) |
| `email` | string | Yes | Admin email for notifications |
| `wildcard` | boolean | No | Request wildcard cert (*.domain) |
| `dns_provider` | string | No | DNS provider for wildcard (cloudflare, route53, etc.) |

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"domain": "example.com", "email": "admin@example.com"}' \
     https://yourdomain.com/api/v1/traefik/certificates
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "cert_xyz789",
    "domain": "example.com",
    "status": "pending",
    "message": "Certificate request initiated. Validation in progress.",
    "estimated_completion": "2025-10-23T12:05:00Z",
    "challenge_type": "HTTP-01",
    "challenge_url": "http://example.com/.well-known/acme-challenge/abc123"
  }
}
```

**Status Codes**:
- `201`: Certificate request created
- `400`: Invalid request (bad domain, email, etc.)
- `429`: Rate limit exceeded (Let's Encrypt limits)
- `500`: Server error

---

### Renew Certificate

**POST** `/certificates/{id}/renew`

Manually trigger certificate renewal.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Certificate ID |

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/certificates/cert_abc123/renew
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "cert_abc123",
    "domain": "example.com",
    "status": "renewing",
    "message": "Renewal initiated",
    "estimated_completion": "2025-10-23T12:05:00Z"
  }
}
```

**Status Codes**:
- `200`: Renewal initiated
- `400`: Certificate not eligible for renewal
- `404`: Certificate not found
- `429`: Rate limit exceeded

---

### Revoke Certificate

**DELETE** `/certificates/{id}`

Revoke an SSL certificate.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Certificate ID |

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `reason` | string | Revocation reason (optional) |

**Example Request**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/certificates/cert_abc123?reason=key_compromise"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "cert_abc123",
    "domain": "example.com",
    "status": "revoked",
    "revoked_at": "2025-10-23T12:00:00Z",
    "reason": "key_compromise"
  }
}
```

**Revocation Reasons**:
- `unspecified`
- `key_compromise`
- `superseded`
- `cessation_of_operation`

---

## Route Endpoints

### List Routes

**GET** `/routes`

Retrieve all configured routes.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | string | Filter by service name |
| `status` | string | Filter by status: `active`, `error`, `disabled` |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/routes?status=active"
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "route_abc123",
      "name": "api-production",
      "rule": "Host(`api.example.com`) && PathPrefix(`/v1`)",
      "service": "api-backend",
      "priority": 100,
      "middleware": ["auth", "rate-limit-100"],
      "status": "active",
      "entry_points": ["websecure"],
      "tls": {
        "enabled": true,
        "certificate_resolver": "letsencrypt"
      },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 20,
    "total_pages": 1
  }
}
```

---

### Get Route Details

**GET** `/routes/{id}`

Retrieve detailed information about a specific route.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Route ID |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/routes/route_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "route_abc123",
    "name": "api-production",
    "rule": "Host(`api.example.com`) && PathPrefix(`/v1`)",
    "service": "api-backend",
    "priority": 100,
    "middleware": ["auth", "rate-limit-100"],
    "status": "active",
    "entry_points": ["websecure"],
    "tls": {
      "enabled": true,
      "certificate_resolver": "letsencrypt",
      "domains": ["api.example.com"]
    },
    "metrics": {
      "requests_total": 152430,
      "requests_per_minute": 45,
      "avg_response_time_ms": 120,
      "errors_total": 234,
      "error_rate": 0.15
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
  }
}
```

---

### Create Route

**POST** `/routes`

Create a new route.

**Request Body**:
```json
{
  "name": "api-production",
  "rule": "Host(`api.example.com`) && PathPrefix(`/v1`)",
  "service": "api-backend",
  "priority": 100,
  "middleware": ["auth", "rate-limit-100"],
  "entry_points": ["websecure"],
  "tls": {
    "enabled": true,
    "certificate_resolver": "letsencrypt"
  }
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique route name (alphanumeric + hyphens) |
| `rule` | string | Yes | Traefik rule syntax |
| `service` | string | Yes | Docker service name |
| `priority` | integer | No | Priority (default: 1) |
| `middleware` | array | No | List of middleware names |
| `entry_points` | array | No | Entry points (default: ["websecure"]) |
| `tls` | object | No | TLS configuration |

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d @route.json \
     https://yourdomain.com/api/v1/traefik/routes
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "route_xyz789",
    "name": "api-production",
    "status": "active",
    "message": "Route created successfully",
    "reload_time_ms": 234
  }
}
```

**Status Codes**:
- `201`: Route created
- `400`: Validation error
- `409`: Route name already exists
- `500`: Server error

---

### Update Route

**PUT** `/routes/{id}`

Update an existing route.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Route ID |

**Request Body**: Same as Create Route (all fields optional)

**Example Request**:
```bash
curl -X PUT \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"priority": 200, "middleware": ["auth", "rate-limit-200"]}' \
     https://yourdomain.com/api/v1/traefik/routes/route_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "route_abc123",
    "message": "Route updated successfully",
    "reload_time_ms": 187
  }
}
```

**Status Codes**:
- `200`: Route updated
- `400`: Validation error
- `404`: Route not found
- `500`: Server error

---

### Delete Route

**DELETE** `/routes/{id}`

Delete a route.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Route ID |

**Example Request**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/routes/route_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "route_abc123",
    "message": "Route deleted successfully",
    "reload_time_ms": 156
  }
}
```

**Status Codes**:
- `200`: Route deleted
- `404`: Route not found
- `500`: Server error

---

### Test Route

**POST** `/routes/{id}/test`

Test a route by sending a sample request.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Route ID |

**Request Body**:
```json
{
  "method": "GET",
  "path": "/v1/users",
  "headers": {
    "User-Agent": "Test Client"
  }
}
```

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"method": "GET", "path": "/v1/users"}' \
     https://yourdomain.com/api/v1/traefik/routes/route_abc123/test
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "matched": true,
    "route": "api-production",
    "service": "api-backend",
    "middleware_applied": ["auth", "rate-limit-100"],
    "response": {
      "status": 200,
      "headers": {
        "Content-Type": "application/json",
        "X-RateLimit-Remaining": "99"
      },
      "response_time_ms": 145
    }
  }
}
```

---

## Middleware Endpoints

### List Middleware

**GET** `/middleware`

Retrieve all configured middleware.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by type: `basicAuth`, `rateLimit`, etc. |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/middleware?type=rateLimit"
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "mw_abc123",
      "name": "rate-limit-100",
      "type": "rateLimit",
      "description": "Limit 100 requests per minute",
      "config": {
        "average": 100,
        "period": "1m",
        "burst": 50
      },
      "used_by_routes": ["api-production", "admin-api"],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-10T00:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 20
  }
}
```

---

### Get Middleware Details

**GET** `/middleware/{id}`

Retrieve detailed information about specific middleware.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Middleware ID |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/middleware/mw_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "mw_abc123",
    "name": "rate-limit-100",
    "type": "rateLimit",
    "description": "Limit 100 requests per minute",
    "config": {
      "average": 100,
      "period": "1m",
      "burst": 50,
      "sourceCriterion": {
        "requestHeaderName": "X-Forwarded-For"
      }
    },
    "used_by_routes": [
      {
        "id": "route_abc123",
        "name": "api-production"
      }
    ],
    "metrics": {
      "requests_total": 50230,
      "requests_limited": 1234,
      "limit_rate": 2.45
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-10T00:00:00Z"
  }
}
```

---

### Create Middleware

**POST** `/middleware`

Create new middleware.

**Request Body**:
```json
{
  "name": "rate-limit-200",
  "type": "rateLimit",
  "description": "Limit 200 requests per minute",
  "config": {
    "average": 200,
    "period": "1m",
    "burst": 100
  }
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique middleware name |
| `type` | string | Yes | Middleware type |
| `description` | string | No | Human-readable description |
| `config` | object | Yes | Type-specific configuration |

**Middleware Types**:
- `basicAuth`: HTTP basic authentication
- `rateLimit`: Request rate limiting
- `redirectScheme`: HTTP to HTTPS redirect
- `compress`: Gzip compression
- `headers`: Add/modify headers
- `stripPrefix`: Remove path prefix
- `addPrefix`: Add path prefix
- `circuitBreaker`: Circuit breaker pattern
- `retry`: Automatic retries
- `ipWhiteList`: IP-based access control

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d @middleware.json \
     https://yourdomain.com/api/v1/traefik/middleware
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "mw_xyz789",
    "name": "rate-limit-200",
    "type": "rateLimit",
    "message": "Middleware created successfully"
  }
}
```

**Status Codes**:
- `201`: Middleware created
- `400`: Validation error
- `409`: Middleware name already exists
- `500`: Server error

---

### Update Middleware

**PUT** `/middleware/{id}`

Update existing middleware.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Middleware ID |

**Request Body**: Same as Create Middleware (all fields optional)

**Example Request**:
```bash
curl -X PUT \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"config": {"average": 150}}' \
     https://yourdomain.com/api/v1/traefik/middleware/mw_abc123
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "mw_abc123",
    "message": "Middleware updated successfully",
    "affected_routes": ["api-production", "admin-api"]
  }
}
```

**Warning**: Changes affect all routes using this middleware!

---

### Delete Middleware

**DELETE** `/middleware/{id}`

Delete middleware.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Middleware ID |

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `force` | boolean | Force delete even if used by routes |

**Example Request**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/middleware/mw_abc123?force=false"
```

**Example Response (middleware in use)**:
```json
{
  "success": false,
  "error": {
    "code": "middleware_in_use",
    "message": "Middleware is used by 2 routes. Use force=true to delete anyway.",
    "details": {
      "used_by_routes": ["api-production", "admin-api"]
    }
  }
}
```

**Example Response (successful deletion)**:
```json
{
  "success": true,
  "data": {
    "id": "mw_abc123",
    "message": "Middleware deleted successfully"
  }
}
```

---

## Configuration Endpoints

### Get Configuration

**GET** `/config`

Retrieve current Traefik configuration.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Response format: `yaml` or `json` (default: yaml) |
| `type` | string | Config type: `static` or `dynamic` (default: static) |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/config?format=yaml"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "content": "entryPoints:\n  web:\n    address: \":80\"\n...",
    "format": "yaml",
    "type": "static",
    "file_path": "/config/traefik.yml",
    "last_modified": "2025-10-23T10:00:00Z",
    "size_bytes": 2048
  }
}
```

---

### Update Configuration

**PUT** `/config`

Update Traefik configuration.

**Request Body**:
```json
{
  "content": "entryPoints:\n  web:\n    address: \":80\"\n...",
  "format": "yaml",
  "type": "static",
  "validate": true,
  "create_backup": true
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Configuration content |
| `format` | string | Yes | Format: `yaml` or `json` |
| `type` | string | Yes | Type: `static` or `dynamic` |
| `validate` | boolean | No | Validate before applying (default: true) |
| `create_backup` | boolean | No | Create backup first (default: true) |

**Example Request**:
```bash
curl -X PUT \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d @config.json \
     https://yourdomain.com/api/v1/traefik/config
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "message": "Configuration updated successfully",
    "backup_id": "backup_20251023_120000",
    "validation": {
      "valid": true,
      "errors": [],
      "warnings": []
    },
    "reload": {
      "status": "success",
      "reload_time_ms": 234
    }
  }
}
```

**Error Response (validation failed)**:
```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Configuration validation failed",
    "details": {
      "errors": [
        {
          "line": 5,
          "column": 10,
          "message": "entryPoints.websecure.address must be a string"
        }
      ]
    }
  }
}
```

---

### Validate Configuration

**POST** `/config/validate`

Validate configuration without applying.

**Request Body**:
```json
{
  "content": "entryPoints:\n  web:\n    address: \":80\"\n...",
  "format": "yaml",
  "type": "static"
}
```

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d @config.json \
     https://yourdomain.com/api/v1/traefik/config/validate
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [
      {
        "line": 20,
        "message": "Middleware 'old-auth' is deprecated. Use 'basicAuth' instead."
      }
    ],
    "summary": {
      "entry_points": 2,
      "routers": 5,
      "services": 3,
      "middleware": 4
    }
  }
}
```

---

## Backup & Restore Endpoints

### List Backups

**GET** `/backups`

Retrieve list of configuration backups.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Backup type: `automatic` or `manual` |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     "https://yourdomain.com/api/v1/traefik/backups?type=automatic"
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "backup_20251023_120000",
      "filename": "traefik_backup_20251023_120000.yml",
      "type": "automatic",
      "size_bytes": 2048,
      "created_at": "2025-10-23T12:00:00Z",
      "created_by": "system",
      "description": "Auto-backup before config update",
      "retention_until": "2025-11-22T12:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 20
  }
}
```

---

### Create Backup

**POST** `/backups`

Create a manual configuration backup.

**Request Body**:
```json
{
  "description": "Backup before major changes",
  "retention_days": 90
}
```

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"description": "Pre-upgrade backup"}' \
     https://yourdomain.com/api/v1/traefik/backups
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "backup_20251023_123045",
    "filename": "traefik_backup_20251023_123045.yml",
    "type": "manual",
    "size_bytes": 2048,
    "created_at": "2025-10-23T12:30:45Z",
    "retention_until": "2026-01-21T12:30:45Z"
  }
}
```

---

### Restore Backup

**POST** `/backups/{id}/restore`

Restore configuration from a backup.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Backup ID |

**Request Body**:
```json
{
  "create_backup_before_restore": true,
  "validate": true
}
```

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"create_backup_before_restore": true}' \
     https://yourdomain.com/api/v1/traefik/backups/backup_20251023_120000/restore
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "message": "Configuration restored successfully",
    "backup_id": "backup_20251023_120000",
    "new_backup_id": "backup_20251023_123100",
    "reload": {
      "status": "success",
      "reload_time_ms": 187
    }
  }
}
```

---

### Delete Backup

**DELETE** `/backups/{id}`

Delete a backup file.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Backup ID |

**Example Request**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/backups/backup_20251023_120000
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "id": "backup_20251023_120000",
    "message": "Backup deleted successfully"
  }
}
```

---

## Health & Status Endpoints

### Health Check

**GET** `/health`

Check API and Traefik health status.

**Authentication**: Not required

**Example Request**:
```bash
curl https://yourdomain.com/api/v1/traefik/health
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "traefik_available": true,
    "traefik_version": "2.10.0",
    "api_version": "1.0.0",
    "timestamp": "2025-10-23T12:00:00Z",
    "uptime_seconds": 864000,
    "checks": {
      "traefik_api": "ok",
      "config_file": "ok",
      "acme_storage": "ok",
      "backup_storage": "ok"
    }
  }
}
```

---

### System Status

**GET** `/status`

Get detailed Traefik status and metrics.

**Example Request**:
```bash
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/status
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "traefik": {
      "version": "2.10.0",
      "uptime_seconds": 864000,
      "pid": 1234,
      "config_last_reload": "2025-10-23T10:00:00Z"
    },
    "statistics": {
      "total_routes": 15,
      "active_routes": 14,
      "error_routes": 1,
      "total_middleware": 8,
      "total_certificates": 3,
      "expiring_certificates": 0
    },
    "metrics": {
      "requests_total": 1523400,
      "requests_per_second": 42.5,
      "avg_response_time_ms": 145,
      "errors_total": 2340,
      "error_rate": 0.15
    },
    "resources": {
      "memory_usage_mb": 256,
      "cpu_usage_percent": 12.5,
      "goroutines": 50
    }
  }
}
```

---

### Reload Traefik

**POST** `/reload`

Manually trigger Traefik configuration reload.

**Request Body**:
```json
{
  "type": "graceful"
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Reload type: `graceful` or `hard` (default: graceful) |

**Example Request**:
```bash
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"type": "graceful"}' \
     https://yourdomain.com/api/v1/traefik/reload
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "message": "Traefik reloaded successfully",
    "type": "graceful",
    "reload_time_ms": 234,
    "timestamp": "2025-10-23T12:00:00Z"
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `success` | 200-299 | Request successful |
| `missing_token` | 401 | No Authorization header provided |
| `invalid_token` | 401 | Token is malformed or invalid |
| `expired_token` | 401 | Token has expired |
| `insufficient_scope` | 403 | Token lacks required permissions |
| `not_found` | 404 | Resource not found |
| `validation_error` | 400 | Request validation failed |
| `duplicate_name` | 409 | Resource name already exists |
| `rate_limit_exceeded` | 429 | Too many requests |
| `middleware_in_use` | 400 | Middleware used by routes |
| `certificate_request_failed` | 500 | Let's Encrypt request failed |
| `config_invalid` | 400 | Configuration validation failed |
| `reload_failed` | 500 | Traefik reload failed |
| `backup_not_found` | 404 | Backup file not found |
| `restore_failed` | 500 | Backup restore failed |
| `internal_error` | 500 | Server error |

---

## Rate Limiting

### Default Limits

- **Authenticated**: 1000 requests/hour per API key
- **Unauthenticated**: 100 requests/hour per IP (/health endpoint only)

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1729684800
```

### Exceeding Rate Limit

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "rate_limit_exceeded",
    "message": "API rate limit exceeded. Try again in 3600 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2025-10-23T13:00:00Z"
    }
  }
}
```

**Status Code**: `429 Too Many Requests`

---

## Code Examples

### Python (requests library)

```python
import requests

BASE_URL = "https://yourdomain.com/api/v1/traefik"
API_TOKEN = "your_api_token_here"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# List certificates
response = requests.get(f"{BASE_URL}/certificates", headers=headers)
certificates = response.json()

# Request new certificate
cert_data = {
    "domain": "example.com",
    "email": "admin@example.com"
}
response = requests.post(
    f"{BASE_URL}/certificates",
    headers=headers,
    json=cert_data
)
result = response.json()

# Create route
route_data = {
    "name": "api-route",
    "rule": "Host(`api.example.com`)",
    "service": "api-backend",
    "middleware": ["rate-limit-100"]
}
response = requests.post(
    f"{BASE_URL}/routes",
    headers=headers,
    json=route_data
)
route = response.json()

# Get status
response = requests.get(f"{BASE_URL}/status", headers=headers)
status = response.json()
print(f"Total routes: {status['data']['statistics']['total_routes']}")
```

---

### JavaScript (fetch API)

```javascript
const BASE_URL = "https://yourdomain.com/api/v1/traefik";
const API_TOKEN = "your_api_token_here";

const headers = {
  "Authorization": `Bearer ${API_TOKEN}`,
  "Content-Type": "application/json"
};

// List routes
fetch(`${BASE_URL}/routes`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));

// Create middleware
const middlewareData = {
  name: "rate-limit-100",
  type: "rateLimit",
  config: {
    average: 100,
    period: "1m",
    burst: 50
  }
};

fetch(`${BASE_URL}/middleware`, {
  method: "POST",
  headers,
  body: JSON.stringify(middlewareData)
})
  .then(res => res.json())
  .then(data => console.log(data));

// Update route
const updateData = {
  priority: 200
};

fetch(`${BASE_URL}/routes/route_abc123`, {
  method: "PUT",
  headers,
  body: JSON.stringify(updateData)
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

### cURL Examples

```bash
# List certificates
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/certificates

# Request certificate
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"domain":"example.com","email":"admin@example.com"}' \
     https://yourdomain.com/api/v1/traefik/certificates

# Create route
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "api-route",
       "rule": "Host(`api.example.com`)",
       "service": "api-backend"
     }' \
     https://yourdomain.com/api/v1/traefik/routes

# Get status
curl -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/status

# Create backup
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"description":"Manual backup"}' \
     https://yourdomain.com/api/v1/traefik/backups

# Restore backup
curl -X POST \
     -H "Authorization: Bearer TOKEN" \
     https://yourdomain.com/api/v1/traefik/backups/backup_20251023_120000/restore
```

---

## Best Practices

### Security

1. **Rotate API Tokens Regularly**: Every 90 days minimum
2. **Use Minimal Scopes**: Only grant required permissions
3. **HTTPS Only**: Never send tokens over HTTP
4. **Store Tokens Securely**: Use environment variables or secrets manager
5. **Monitor API Usage**: Watch for unusual activity

### Performance

1. **Use Pagination**: Don't fetch all resources at once
2. **Cache Responses**: Respect cache headers
3. **Batch Operations**: Group multiple changes into one request
4. **Handle Rate Limits**: Implement exponential backoff
5. **Monitor Latency**: Track API response times

### Error Handling

1. **Check Status Codes**: Don't assume 200 OK
2. **Parse Error Messages**: Use `error.code` for programmatic handling
3. **Retry Transient Errors**: 5xx errors may be temporary
4. **Log API Errors**: Include request_id for support
5. **Validate Before Sending**: Check input locally first

### Integration

1. **Test in Staging**: Never test against production API
2. **Version Your Code**: Pin API version in URL
3. **Handle Breaking Changes**: Subscribe to API changelog
4. **Document Your Usage**: Keep track of API calls made
5. **Set Timeouts**: Don't wait forever for responses

---

## Changelog

### v1.0.0 (October 23, 2025)

- Initial API release
- SSL certificate management endpoints
- Route configuration endpoints
- Middleware management endpoints
- Configuration and backup endpoints
- Health and status endpoints

---

## Support

**Documentation**: https://unicorncommander.ai/docs
**API Support**: ops-support@unicorncommander.ai
**Bug Reports**: https://github.com/Unicorn-Commander/ops-center/issues

**Response Times**:
- Critical (production down): 1 hour
- High (feature broken): 4 hours
- Normal (question/bug): 24 hours
- Low (enhancement): 1 week

---

**API Version**: 1.0.0
**Last Updated**: October 23, 2025
**Maintained By**: Ops-Center API Team
