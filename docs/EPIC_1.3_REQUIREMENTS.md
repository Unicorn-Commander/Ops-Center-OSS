# Epic 1.3: Traefik Configuration Management

**Status**: Requirements Phase
**Priority**: High (P1)
**Estimated Effort**: 4-5 days
**Created**: October 23, 2025
**Last Updated**: October 23, 2025

---

## Executive Summary

Create a comprehensive web-based GUI for managing Traefik reverse proxy configuration. This will enable administrators to dynamically configure routes, services, middleware, and SSL certificates without manual file editing, reducing deployment time and configuration errors.

**Current State**: All Traefik configuration is done via manual editing of YAML files and Docker labels.

**Desired State**: Web-based management interface integrated into Ops-Center for dynamic, real-time Traefik configuration.

---

## Table of Contents

1. [Current Traefik Setup Analysis](#current-traefik-setup-analysis)
2. [Gap Analysis](#gap-analysis)
3. [Feature Requirements](#feature-requirements)
4. [API Requirements](#api-requirements)
5. [Database Schema](#database-schema)
6. [Security Requirements](#security-requirements)
7. [UI/UX Requirements](#uiux-requirements)
8. [Integration Requirements](#integration-requirements)
9. [Implementation Plan](#implementation-plan)
10. [Use Cases](#use-cases)
11. [Technical Challenges](#technical-challenges)
12. [Success Criteria](#success-criteria)

---

## Current Traefik Setup Analysis

### 1. Infrastructure Overview

**Traefik Version**: 3.0.4 (Codename: beaufort)
**Container**: `traefik`
**Status**: Running (Up 17 hours)
**Exposed Ports**:
- 80/tcp (HTTP)
- 443/tcp (HTTPS)
- 8080/tcp (Dashboard/API)

**Networks**:
- `web` (external, bridge) - Used for exposing services

### 2. Configuration Architecture

Traefik uses a **hybrid configuration model**:

#### Static Configuration (`/home/deploy/Infrastructure/traefik/traefik.yml`)

**Purpose**: Core Traefik settings that require restart to change

```yaml
api:
  dashboard: true
  debug: true

entryPoints:
  http:
    address: ":80"
  https:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: web
  file:
    directory: /dynamic
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@unicorncommander.ai
      storage: /acme/acme.json
      keyType: EC256
      httpChallenge:
        entryPoint: http
```

**Key Settings**:
- API/Dashboard enabled on port 8080
- Docker provider enabled (reads container labels)
- File provider enabled (watches `/dynamic` directory)
- Let's Encrypt certificate resolver configured

#### Dynamic Configuration (File Provider)

**Location**: `/home/deploy/Infrastructure/traefik/dynamic/*.yml`

**Files**:
1. `domains.yml` - Main service routing (314 lines)
2. `middlewares.yml` - Reusable middleware configurations (137 lines)
3. `billing-routes.yml` - Billing-specific routes (124 lines)
4. `keycloak.yml` - Keycloak SSO routing (25 lines)
5. `api-domains.yml` - API endpoint routing
6. `cloudflare.yml` - Cloudflare-specific settings
7. `firstselect.yml`, `realestate.yml`, `taxsquare.yml` - Project-specific routes

**Configuration Format**:
```yaml
http:
  routers:
    router-name:
      rule: "Host(`domain.com`)"
      service: service-name
      tls:
        certResolver: letsencrypt
      middlewares:
        - middleware-1
        - middleware-2

  services:
    service-name:
      loadBalancer:
        servers:
          - url: "http://backend:8080"
        passHostHeader: true
        healthCheck:
          path: /health
          interval: 30s

  middlewares:
    middleware-name:
      forwardAuth:
        address: "http://auth-service:9000"
```

#### Docker Label Configuration

**Example** (from `docker-compose.traefik.yml`):
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.traefik.entrypoints=http"
  - "traefik.http.routers.traefik.rule=Host(`traefik.unicorncommander.ai`)"
  - "traefik.http.routers.traefik-secure.entrypoints=https"
  - "traefik.http.routers.traefik-secure.tls=true"
  - "traefik.http.routers.traefik-secure.tls.certresolver=letsencrypt"
```

### 3. Current Routes & Services

**Discovered Routes** (from `domains.yml`):

| Domain | Service | Backend | Port | SSL |
|--------|---------|---------|------|-----|
| unicorncommander.ai | Ops-Center | ops-center-direct | 8000 | ✅ |
| chat.unicorncommander.ai | Open-WebUI | unicorn-open-webui | 8080 | ✅ |
| search.unicorncommander.ai | Center-Deep | unicorn-centerdeep | 8890 | ✅ |
| auth.unicorncommander.ai | Keycloak | uchub-keycloak | 8080 | ✅ |
| billing.unicorncommander.ai | Lago Frontend | unicorn-lago-front | 80 | ✅ |
| billing-api.unicorncommander.ai | Lago API | unicorn-lago-api | 3000 | ✅ |
| ai.unicorncommander.ai | LiteLLM Proxy | unicorn-litellm | 4000 | ✅ |
| usage.unicorncommander.ai | Metabase | unicorn-usage-dashboard | 3000 | ✅ |
| brigade.unicorncommander.ai | Brigade UI | unicorn-brigade-ui | 80 | ✅ |
| api.brigade.unicorncommander.ai | Brigade API | unicorn-brigade | 8112 | ✅ |
| git.unicorncommander.ai | Forgejo | unicorn-forgejo | 3003 | ✅ |
| ci.unicorncommander.ai | Woodpecker CI | unicorn-woodpecker-server | 8004 | ✅ |
| code.unicorncommander.ai | Bolt.DIY (OAuth2) | uchub-oauth2-proxy | 4180 | ✅ |
| api2.unicorncommander.ai | GPU Server (RunPod) | 174.171.202.141 | 8080 | ✅ |
| gpu.unicorncommander.ai | GPU Phone Home | gpu-ip-updater | 8082 | ✅ |

**Total**: 15+ active routes

### 4. Middleware Configurations

**Available Middlewares** (from `middlewares.yml`):

1. **Authentication/Authorization**:
   - `lago-tier-check` - Checks Professional+ tier for Lago access
   - `admin-tier-check` - Checks Enterprise tier for admin access
   - `byok-tier-check` - Checks Starter+ tier for BYOK
   - `tier-check` - Generic tier validation

2. **Security**:
   - `security-headers` - HSTS, XSS protection, frame denial
   - `api-cors` - CORS headers for API endpoints
   - `api-rate-limit` - 100 req/min with 50 burst

3. **Headers**:
   - `pass-auth-header` - Custom forwarded host header
   - `oauth2-headers` - OAuth2 proxy headers
   - `loopnet-headers` - LoopNet-specific CORS

4. **Redirects**:
   - `redirect-to-https` - HTTP → HTTPS redirect

5. **Compression**:
   - `compress` - Response compression

### 5. SSL/TLS Configuration

**Certificate Resolver**: Let's Encrypt (HTTP-01 Challenge)
**Storage**: `/home/deploy/Infrastructure/traefik/acme/acme.json` (203KB)
**Key Type**: EC256 (Elliptic Curve)
**Email**: admin@unicorncommander.ai

**Certificate Status**:
- ✅ Automated renewal via ACME
- ✅ Wildcard support not enabled (would require DNS-01 challenge)
- ✅ Multiple domains/subdomains supported
- ✅ Last updated: October 23, 2025 02:06

### 6. Traefik API

**Dashboard URL**: http://localhost:8080/dashboard/ (currently returns 000 - connection refused)
**API Base**: http://localhost:8080/api/

**Known API Endpoints** (based on Traefik documentation):
```
GET /api/overview              # System overview
GET /api/entrypoints           # Entry points list
GET /api/http/routers          # HTTP routers
GET /api/http/services         # HTTP services
GET /api/http/middlewares      # HTTP middlewares
GET /api/tcp/routers           # TCP routers
GET /api/tcp/services          # TCP services
GET /api/udp/routers           # UDP routers
GET /api/udp/services          # UDP services
GET /api/version               # Traefik version
```

**Current Status**: API appears to be enabled but not accessible (authentication required?)

### 7. Current Pain Points

**Identified Issues**:

1. **Manual Configuration**: All changes require SSH access and file editing
2. **No Validation**: YAML syntax errors only discovered at runtime
3. **No Route Testing**: Can't verify routes work before deployment
4. **No Centralized View**: Routes spread across 7+ files
5. **Backup Proliferation**: 20+ backup files in `/dynamic` directory
6. **No Conflict Detection**: Duplicate routes can be created accidentally
7. **Certificate Management**: No visibility into cert status/expiration
8. **Middleware Reuse**: Hard to know which middlewares are available
9. **Docker Label Sprawl**: Container labels mixed with file config
10. **No Audit Trail**: No history of who changed what and when

---

## Gap Analysis

### What Exists Today

✅ Traefik installed and operational
✅ API/Dashboard enabled in static config
✅ File provider with hot-reload enabled
✅ Docker provider for container-based routing
✅ Let's Encrypt certificate automation
✅ 15+ production routes configured
✅ 8+ middleware configurations
✅ Security headers and rate limiting

### What's Missing

❌ Web-based configuration interface
❌ API integration for dynamic updates
❌ Route validation and conflict detection
❌ Certificate status visibility
❌ Middleware management UI
❌ Service health monitoring
❌ Configuration backup/restore
❌ Audit logging for changes
❌ Route testing functionality
❌ Import/export capabilities
❌ Template-based route creation
❌ Bulk operations support

### Critical Gaps

**Priority 1 (Must Have)**:
1. View all routes in web UI
2. Create/edit/delete routes via GUI
3. SSL certificate status visibility
4. Configuration validation before save
5. Route conflict detection

**Priority 2 (Should Have)**:
6. Middleware CRUD operations
7. Service health checks
8. Configuration backup/restore
9. Audit logging
10. Route testing

**Priority 3 (Nice to Have)**:
11. Template library
12. Bulk operations
13. Import/export
14. Visual topology map
15. Performance metrics

---

## Feature Requirements

### Core Features (MVP)

#### 1. Route Management

**Description**: CRUD operations for HTTP/HTTPS routes

**Functional Requirements**:
- **List Routes**: Display all configured routes with key info
  - Router name
  - Domain/path rule
  - Backend service
  - Entry points (HTTP/HTTPS)
  - Middleware chain
  - TLS status
  - Health status
- **Create Route**: Form to create new route
  - Input: Domain/subdomain
  - Input: Path rule (Host, Path, PathPrefix, Headers, etc.)
  - Select: Backend service (from Docker containers or manual URL)
  - Select: Entry points (http, https, both)
  - Toggle: Enable TLS
  - Select: Certificate resolver
  - Multi-select: Middleware chain
  - Input: Priority (for multiple routes on same domain)
- **Edit Route**: Modify existing route configuration
  - All fields from Create Route
  - Show current values
  - Validation before save
- **Delete Route**: Remove route with confirmation
  - Warning if route is actively used
  - Cascade delete option for related middleware
- **Duplicate Route**: Clone existing route for quick creation
- **Enable/Disable Route**: Temporarily disable without deletion

**Technical Details**:
- Read from Traefik API: `GET /api/http/routers`
- Write to file provider: Update YAML in `/dynamic/domains.yml`
- Real-time updates: File watcher picks up changes automatically
- Rollback capability: Keep last 5 versions of each file

**UI Mockup**:
```
┌─────────────────────────────────────────────────────────────┐
│ Routes Management                               [+ Add Route]│
├─────────────────────────────────────────────────────────────┤
│ Search: [________________]  Filter: [All ▾] [HTTP ▾] [TLS ▾]│
├─────────────────────────────────────────────────────────────┤
│ Name                    Domain              Service      TLS │
│ ─────────────────────────────────────────────────────────── │
│ ● chat-unicorncommander chat.unicorncomm... open-webui   ✓  │
│ ● billing-api-unicornco billing-api.unic... lago-api     ✓  │
│ ● search-unicorncommande search.unicornco... centerdeep   ✓  │
│   ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Service Management

**Description**: View and manage backend services

**Functional Requirements**:
- **List Services**: Display all configured services
  - Service name
  - Backend URL(s)
  - Load balancer config
  - Health check status
  - Linked routers
- **Create Service**: Define new backend service
  - Input: Service name
  - Input: Backend URL (supports multiple for load balancing)
  - Toggle: Pass host header
  - Health check configuration:
    - Path (e.g., `/health`)
    - Interval (seconds)
    - Timeout (seconds)
    - Threshold (consecutive failures)
  - Load balancer method (round-robin, weighted, etc.)
- **Edit Service**: Modify service configuration
- **Delete Service**: Remove service (check for router dependencies)
- **Test Service**: Send test request to backend

**Docker Integration**:
- Auto-discover running containers on `web` network
- Suggest service names based on container names
- Auto-populate backend URLs from container ports

**Technical Details**:
- Read from Traefik API: `GET /api/http/services`
- Read from Docker API: List containers on `web` network
- Write to file provider: Update YAML in `/dynamic/domains.yml`

#### 3. Middleware Management

**Description**: CRUD operations for middleware

**Functional Requirements**:
- **List Middleware**: Display all configured middleware
  - Middleware name
  - Type (forwardAuth, headers, rateLimit, etc.)
  - Configuration summary
  - Usage count (how many routers use it)
- **Create Middleware**: Form-based middleware creation
  - Select: Middleware type
  - Dynamic form fields based on type:
    - **forwardAuth**: Auth service URL, headers
    - **headers**: Custom request/response headers
    - **rateLimit**: Average, burst, period
    - **redirect**: Scheme, permanent flag
    - **compress**: Enable compression
    - **stripPrefix**: Prefixes to strip
    - **basicAuth**: Username/password (hashed)
  - Input: Description/notes
- **Edit Middleware**: Modify existing middleware
- **Delete Middleware**: Remove middleware (check router dependencies)
- **Preview**: Show middleware configuration in YAML format

**Middleware Templates**:
- Pre-defined templates for common use cases:
  - Security headers (HSTS, XSS, CSP)
  - CORS headers (API endpoints)
  - Rate limiting (public APIs)
  - OAuth2 authentication
  - IP whitelist
  - Redirect to HTTPS

**Technical Details**:
- Read from Traefik API: `GET /api/http/middlewares`
- Write to file provider: Update YAML in `/dynamic/middlewares.yml`

#### 4. SSL/TLS Certificate Management

**Description**: View and manage SSL certificates

**Functional Requirements**:
- **Certificate Dashboard**: Overview of all certificates
  - Domain name
  - Issuer (Let's Encrypt, custom)
  - Issue date
  - Expiration date
  - Days until expiry
  - Renewal status
  - Certificate type (single, SAN, wildcard)
- **Certificate Details**: View certificate info
  - Subject Alternative Names (SANs)
  - Key type (RSA, EC)
  - Certificate chain
  - Serial number
- **Force Renewal**: Manually trigger certificate renewal
- **Certificate Alerts**: Warnings for:
  - Certificates expiring in < 30 days
  - Failed renewal attempts
  - Revoked certificates

**ACME Configuration**:
- View current ACME settings
- Edit email address
- Switch challenge type (HTTP-01, DNS-01)
- Configure DNS provider (Cloudflare, Route53, etc.)

**Technical Details**:
- Read from ACME storage: Parse `/acme/acme.json`
- Traefik API: Certificate status
- Write to static config: ACME settings (requires Traefik restart)

**Security Note**: Never expose private keys via API

#### 5. Configuration Validation

**Description**: Validate configuration before deployment

**Functional Requirements**:
- **Syntax Validation**: Check YAML syntax
- **Schema Validation**: Verify against Traefik schema
- **Conflict Detection**:
  - Duplicate router names
  - Conflicting rules on same domain/path
  - Middleware chain errors (missing middleware)
  - Service references to non-existent backends
- **Dependency Check**:
  - Routers referencing missing services
  - Routers referencing missing middleware
  - Certificate resolvers not configured
- **Preview**: Show generated YAML before save
- **Dry Run**: Test configuration without applying

**Real-time Validation**:
- Form field validation as user types
- Immediate feedback on conflicts
- Suggestions for fixes

#### 6. Monitoring & Health Checks

**Description**: Real-time service health monitoring

**Functional Requirements**:
- **Service Health Dashboard**: Visual status of all services
  - Green: Healthy (last check succeeded)
  - Yellow: Degraded (some backends down)
  - Red: Down (all backends down)
  - Gray: Unknown (no health check configured)
- **Health Check History**: Timeline of health check results
  - Last 24 hours of checks
  - Downtime incidents
  - Response time graph
- **Alert Configuration**:
  - Email/webhook alerts on service down
  - Configurable thresholds
  - Notification frequency

**Metrics Display**:
- Request count per route
- Response time percentiles (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active connections

**Technical Details**:
- Poll Traefik API: `/api/http/services` (health status)
- Integrate with Prometheus metrics (if available)
- Store health check history in database

### Advanced Features (Post-MVP)

#### 7. Route Testing

**Description**: Test routes before deployment

**Functional Requirements**:
- **Test Route**: Send HTTP request through Traefik
  - Input: Domain to test
  - Input: Path
  - Input: Headers
  - Input: Method (GET, POST, etc.)
  - Output: Response status, headers, body
- **cURL Generator**: Generate cURL command for testing
- **Integration Tests**: Run suite of tests against routes

#### 8. Configuration Backup/Restore

**Description**: Version control for Traefik configuration

**Functional Requirements**:
- **Automatic Backups**: Create backup before each change
- **Manual Backups**: Trigger backup on demand
- **Backup List**: View all backups with metadata
  - Timestamp
  - User who made change
  - Description
  - File changed
  - Diff preview
- **Restore**: Roll back to previous configuration
  - Show diff before restore
  - Confirm restoration
  - Automatic Traefik reload

**Technical Details**:
- Store backups in database (YAML as TEXT)
- Keep last 50 backups per file
- Auto-clean old backups (>90 days)

#### 9. Audit Logging

**Description**: Track all configuration changes

**Functional Requirements**:
- **Audit Log**: Chronological list of changes
  - Timestamp
  - User (email/username)
  - Action (create, update, delete)
  - Resource (router, service, middleware)
  - Resource name
  - Old value → New value
  - Success/failure
- **Filter & Search**:
  - By user
  - By action type
  - By resource type
  - By date range
- **Export**: Download audit log as CSV

**Technical Details**:
- Store in PostgreSQL `traefik_audit_logs` table
- Triggered on every API call
- Include API request details

#### 10. Bulk Operations

**Description**: Perform operations on multiple routes/services

**Functional Requirements**:
- **Bulk Enable/Disable**: Toggle multiple routes
- **Bulk Middleware Assignment**: Add middleware to selected routes
- **Bulk Delete**: Remove multiple routes with confirmation
- **Bulk Tag Assignment**: Organize routes with tags
- **CSV Import**: Import routes from CSV file
- **CSV Export**: Export all routes to CSV

#### 11. Template Library

**Description**: Pre-defined route templates for common scenarios

**Templates**:
1. **Simple HTTP → HTTPS Redirect**
2. **Reverse Proxy with Auth** (OAuth2)
3. **API Gateway** (with rate limiting and CORS)
4. **Static Site** (with caching headers)
5. **WebSocket Proxy** (with sticky sessions)
6. **Load Balanced Service** (round-robin)
7. **Blue-Green Deployment** (weighted load balancer)
8. **Microservice** (with health checks and circuit breaker)

**Functionality**:
- Browse template library
- Preview template configuration
- Clone template and customize
- Share custom templates (export/import)

#### 12. Visual Topology

**Description**: Interactive diagram of routing topology

**Features**:
- Graph view of routes → services → backends
- Click node to view details
- Highlight path for specific domain
- Show middleware chain visually
- Export diagram as PNG/SVG

---

## API Requirements

### Backend API Endpoints

**Base Path**: `/api/v1/traefik`

#### Route Management

```python
# List all routes
GET /api/v1/traefik/routes
Query params:
  - search: str (filter by name/domain)
  - entrypoint: str (http, https)
  - tls: bool
  - middleware: str (filter by middleware name)
  - service: str (filter by service name)
  - status: str (enabled, disabled, error)
Response: {
  "routes": [
    {
      "name": "chat-unicorncommander",
      "rule": "Host(`chat.unicorncommander.ai`)",
      "service": "open-webui-service",
      "entryPoints": ["https"],
      "middlewares": ["security-headers"],
      "tls": {
        "certResolver": "letsencrypt",
        "domains": [{"main": "chat.unicorncommander.ai"}]
      },
      "priority": 100,
      "status": "enabled",
      "provider": "file"
    }
  ],
  "total": 15
}

# Get single route details
GET /api/v1/traefik/routes/{route_name}
Response: {
  "route": { ... },
  "service": { ... },
  "middlewares": [ ... ],
  "health": "healthy",
  "metrics": {
    "requests_total": 12345,
    "requests_per_second": 10.5,
    "error_rate": 0.02,
    "avg_response_time_ms": 45
  }
}

# Create new route
POST /api/v1/traefik/routes
Body: {
  "name": "new-service",
  "rule": "Host(`new.unicorncommander.ai`)",
  "service": "new-service-backend",
  "entryPoints": ["https"],
  "middlewares": ["security-headers"],
  "tls": {
    "certResolver": "letsencrypt"
  },
  "priority": 100
}
Response: {
  "route": { ... },
  "file": "domains.yml",
  "backup_created": true
}

# Update existing route
PUT /api/v1/traefik/routes/{route_name}
Body: { ... }
Response: { ... }

# Delete route
DELETE /api/v1/traefik/routes/{route_name}
Query params:
  - cascade: bool (delete unused services/middleware)
Response: {
  "deleted": true,
  "backup_created": true
}

# Validate route configuration
POST /api/v1/traefik/routes/validate
Body: { ... }
Response: {
  "valid": true,
  "errors": [],
  "warnings": [
    "Middleware 'rate-limit' is not defined"
  ],
  "conflicts": [
    {
      "route": "existing-route",
      "reason": "Rule overlaps with new route"
    }
  ]
}

# Test route
POST /api/v1/traefik/routes/{route_name}/test
Body: {
  "method": "GET",
  "path": "/api/health",
  "headers": {"Authorization": "Bearer token"}
}
Response: {
  "status": 200,
  "response_time_ms": 45,
  "headers": { ... },
  "body": "..."
}
```

#### Service Management

```python
# List all services
GET /api/v1/traefik/services
Response: {
  "services": [
    {
      "name": "open-webui-service",
      "type": "loadBalancer",
      "servers": [
        {
          "url": "http://unicorn-open-webui:8080",
          "weight": 1
        }
      ],
      "passHostHeader": true,
      "healthCheck": {
        "path": "/health",
        "interval": "30s",
        "timeout": "10s",
        "status": "healthy"
      },
      "routers": ["chat-unicorncommander"]
    }
  ]
}

# Get service details
GET /api/v1/traefik/services/{service_name}

# Create service
POST /api/v1/traefik/services
Body: {
  "name": "new-service-backend",
  "servers": [
    {"url": "http://container:8080"}
  ],
  "passHostHeader": true,
  "healthCheck": {
    "path": "/health",
    "interval": "30s",
    "timeout": "10s"
  }
}

# Update service
PUT /api/v1/traefik/services/{service_name}

# Delete service
DELETE /api/v1/traefik/services/{service_name}

# Test service connectivity
POST /api/v1/traefik/services/{service_name}/test
Response: {
  "servers": [
    {
      "url": "http://unicorn-open-webui:8080",
      "reachable": true,
      "response_time_ms": 12,
      "status_code": 200
    }
  ]
}
```

#### Middleware Management

```python
# List all middleware
GET /api/v1/traefik/middlewares
Response: {
  "middlewares": [
    {
      "name": "security-headers",
      "type": "headers",
      "config": {
        "browserXssFilter": true,
        "contentTypeNosniff": true,
        "frameDeny": true,
        "stsSeconds": 31536000
      },
      "usage_count": 12,
      "routers": ["chat-unicorncommander", ...]
    }
  ]
}

# Get middleware details
GET /api/v1/traefik/middlewares/{middleware_name}

# Create middleware
POST /api/v1/traefik/middlewares
Body: {
  "name": "api-rate-limit",
  "type": "rateLimit",
  "config": {
    "average": 100,
    "burst": 50,
    "period": "1m"
  }
}

# Update middleware
PUT /api/v1/traefik/middlewares/{middleware_name}

# Delete middleware
DELETE /api/v1/traefik/middlewares/{middleware_name}

# Get middleware types and schemas
GET /api/v1/traefik/middlewares/types
Response: {
  "types": [
    {
      "name": "forwardAuth",
      "description": "Forward authentication to external service",
      "schema": { ... }
    },
    {
      "name": "headers",
      "description": "Add/modify HTTP headers",
      "schema": { ... }
    }
  ]
}
```

#### SSL/TLS Management

```python
# List all certificates
GET /api/v1/traefik/certificates
Response: {
  "certificates": [
    {
      "domain": "chat.unicorncommander.ai",
      "sans": [],
      "issuer": "Let's Encrypt",
      "not_before": "2025-10-01T00:00:00Z",
      "not_after": "2026-01-01T00:00:00Z",
      "days_until_expiry": 70,
      "status": "valid",
      "key_type": "EC256",
      "resolver": "letsencrypt"
    }
  ]
}

# Get certificate details
GET /api/v1/traefik/certificates/{domain}
Response: {
  "certificate": { ... },
  "chain": [ ... ],
  "routers": ["chat-unicorncommander"]
}

# Force certificate renewal
POST /api/v1/traefik/certificates/{domain}/renew
Response: {
  "success": true,
  "message": "Certificate renewal initiated"
}

# Get ACME configuration
GET /api/v1/traefik/acme/config
Response: {
  "email": "admin@unicorncommander.ai",
  "storage": "/acme/acme.json",
  "key_type": "EC256",
  "challenge": {
    "type": "http",
    "entryPoint": "http"
  }
}

# Update ACME configuration (requires restart)
PUT /api/v1/traefik/acme/config
Body: {
  "email": "admin@unicorncommander.ai",
  "key_type": "EC256"
}
Response: {
  "updated": true,
  "restart_required": true
}
```

#### Configuration Management

```python
# Get configuration files
GET /api/v1/traefik/config/files
Response: {
  "files": [
    {
      "name": "domains.yml",
      "path": "/dynamic/domains.yml",
      "size": 8692,
      "last_modified": "2025-10-22T21:01:00Z",
      "routers": 15,
      "services": 15,
      "middlewares": 0
    },
    {
      "name": "middlewares.yml",
      "path": "/dynamic/middlewares.yml",
      "size": 5000,
      "last_modified": "2025-10-09T22:36:00Z",
      "routers": 0,
      "services": 0,
      "middlewares": 8
    }
  ]
}

# Get file content
GET /api/v1/traefik/config/files/{filename}
Response: {
  "filename": "domains.yml",
  "content": "...",
  "format": "yaml"
}

# Validate configuration
POST /api/v1/traefik/config/validate
Body: {
  "content": "..."
}
Response: {
  "valid": true,
  "errors": [],
  "warnings": []
}

# Create backup
POST /api/v1/traefik/config/backups
Body: {
  "description": "Before adding new route"
}
Response: {
  "backup_id": "uuid",
  "timestamp": "2025-10-23T12:00:00Z",
  "files": ["domains.yml", "middlewares.yml"]
}

# List backups
GET /api/v1/traefik/config/backups
Response: {
  "backups": [
    {
      "id": "uuid",
      "timestamp": "2025-10-23T12:00:00Z",
      "user": "admin@example.com",
      "description": "Before adding new route",
      "files": ["domains.yml"]
    }
  ]
}

# Restore backup
POST /api/v1/traefik/config/backups/{backup_id}/restore
Response: {
  "restored": true,
  "files": ["domains.yml"]
}
```

#### Docker Integration

```python
# List Docker containers on web network
GET /api/v1/traefik/docker/containers
Response: {
  "containers": [
    {
      "id": "abc123",
      "name": "unicorn-open-webui",
      "image": "ghcr.io/open-webui/open-webui:main",
      "status": "running",
      "networks": ["unicorn-network", "web"],
      "ports": [
        {"container": 8080, "host": 8080}
      ],
      "labels": {
        "traefik.enable": "false"
      },
      "suggested_service_name": "open-webui-service",
      "suggested_backend_url": "http://unicorn-open-webui:8080"
    }
  ]
}

# Get container details
GET /api/v1/traefik/docker/containers/{container_id}
```

#### Analytics & Metrics

```python
# Get route metrics
GET /api/v1/traefik/metrics/routes
Query params:
  - route: str (filter by route)
  - from: datetime
  - to: datetime
Response: {
  "metrics": [
    {
      "route": "chat-unicorncommander",
      "requests_total": 12345,
      "requests_per_second": 10.5,
      "error_rate": 0.02,
      "avg_response_time_ms": 45,
      "p95_response_time_ms": 120,
      "p99_response_time_ms": 250
    }
  ]
}

# Get service health history
GET /api/v1/traefik/metrics/health
Query params:
  - service: str
  - from: datetime
  - to: datetime
Response: {
  "history": [
    {
      "timestamp": "2025-10-23T12:00:00Z",
      "service": "open-webui-service",
      "status": "healthy",
      "response_time_ms": 12
    }
  ]
}
```

#### Audit Logs

```python
# List audit logs
GET /api/v1/traefik/audit/logs
Query params:
  - user: str
  - action: str (create, update, delete)
  - resource_type: str (route, service, middleware)
  - from: datetime
  - to: datetime
Response: {
  "logs": [
    {
      "id": "uuid",
      "timestamp": "2025-10-23T12:00:00Z",
      "user_email": "admin@example.com",
      "action": "create",
      "resource_type": "route",
      "resource_name": "new-service",
      "old_value": null,
      "new_value": { ... },
      "success": true,
      "ip_address": "192.168.1.100"
    }
  ]
}

# Export audit logs
GET /api/v1/traefik/audit/logs/export
Query params: (same as list)
Response: CSV file download
```

### Traefik API Integration

**Traefik API Base**: http://traefik:8080/api/

**Authentication**: Need to investigate if API is protected (likely basic auth or no auth on internal network)

**Endpoints to Use**:
- `GET /api/http/routers` - Read current routers
- `GET /api/http/services` - Read current services
- `GET /api/http/middlewares` - Read current middleware
- `GET /api/overview` - System overview
- `GET /api/version` - Traefik version

**File Provider Strategy**:
- Traefik API is **read-only** (can't write config)
- Must write to YAML files in `/dynamic` directory
- Traefik watches directory and hot-reloads changes
- No restart required for file provider changes

**Implementation**:
```python
import httpx
import yaml
from pathlib import Path

TRAEFIK_API_URL = "http://traefik:8080/api"
DYNAMIC_CONFIG_DIR = "/home/deploy/Infrastructure/traefik/dynamic"

async def get_routes():
    """Read routes from Traefik API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TRAEFIK_API_URL}/http/routers")
        return response.json()

def write_route_to_file(route_config: dict, filename: str = "domains.yml"):
    """Write route to YAML file"""
    filepath = Path(DYNAMIC_CONFIG_DIR) / filename

    # Load existing config
    with open(filepath, 'r') as f:
        config = yaml.safe_load(f) or {"http": {"routers": {}, "services": {}}}

    # Add/update route
    config["http"]["routers"][route_config["name"]] = route_config

    # Write back
    with open(filepath, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

---

## Database Schema

### Tables Required

#### 1. `traefik_backups`

**Purpose**: Store configuration backups for rollback

```sql
CREATE TABLE traefik_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,  -- User email
    description TEXT,
    filename VARCHAR(255) NOT NULL,  -- e.g., "domains.yml"
    content TEXT NOT NULL,  -- YAML content
    file_hash VARCHAR(64) NOT NULL,  -- SHA256 for duplicate detection
    metadata JSONB  -- Additional info
);

CREATE INDEX idx_traefik_backups_created_at ON traefik_backups(created_at DESC);
CREATE INDEX idx_traefik_backups_filename ON traefik_backups(filename);
```

#### 2. `traefik_audit_logs`

**Purpose**: Track all configuration changes

```sql
CREATE TABLE traefik_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),  -- Keycloak user ID
    action VARCHAR(50) NOT NULL,  -- create, update, delete, restore
    resource_type VARCHAR(50) NOT NULL,  -- route, service, middleware, certificate
    resource_name VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT
);

CREATE INDEX idx_traefik_audit_logs_timestamp ON traefik_audit_logs(timestamp DESC);
CREATE INDEX idx_traefik_audit_logs_user ON traefik_audit_logs(user_email);
CREATE INDEX idx_traefik_audit_logs_resource ON traefik_audit_logs(resource_type, resource_name);
```

#### 3. `traefik_health_history`

**Purpose**: Store service health check history

```sql
CREATE TABLE traefik_health_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    service_name VARCHAR(255) NOT NULL,
    server_url VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- healthy, degraded, down, unknown
    response_time_ms INTEGER,
    error_message TEXT
);

CREATE INDEX idx_traefik_health_history_timestamp ON traefik_health_history(timestamp DESC);
CREATE INDEX idx_traefik_health_history_service ON traefik_health_history(service_name);

-- Partition by month for performance
CREATE TABLE traefik_health_history_2025_10 PARTITION OF traefik_health_history
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

#### 4. `traefik_route_templates`

**Purpose**: Store reusable route templates

```sql
CREATE TABLE traefik_route_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),  -- reverse-proxy, api-gateway, static-site, etc.
    icon VARCHAR(50),  -- For UI
    config_template JSONB NOT NULL,  -- Template with {{variables}}
    variables JSONB NOT NULL,  -- Variable definitions
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_traefik_route_templates_category ON traefik_route_templates(category);
```

#### 5. `traefik_alerts`

**Purpose**: Alert configurations for service monitoring

```sql
CREATE TABLE traefik_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    alert_type VARCHAR(50) NOT NULL,  -- service_down, cert_expiring, high_error_rate
    resource_type VARCHAR(50) NOT NULL,  -- route, service, certificate
    resource_name VARCHAR(255),
    conditions JSONB NOT NULL,  -- Alert thresholds
    notification_channels JSONB NOT NULL,  -- email, webhook, slack
    cooldown_minutes INTEGER DEFAULT 60,  -- Prevent alert spam
    last_triggered_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_traefik_alerts_enabled ON traefik_alerts(enabled);
```

---

## Security Requirements

### 1. Authentication & Authorization

**Requirements**:
- All Traefik management endpoints require authentication
- Only users with `admin` or `moderator` roles can access
- Keycloak SSO integration (same as other Ops-Center features)
- Session-based authentication with JWT tokens

**Implementation**:
```python
from fastapi import Depends, HTTPException
from backend.keycloak_integration import get_current_user

@app.get("/api/v1/traefik/routes")
async def get_routes(current_user = Depends(get_current_user)):
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    # ... implementation
```

### 2. Input Validation

**Requirements**:
- Validate all user inputs (domain names, URLs, etc.)
- Sanitize inputs to prevent YAML injection
- Validate against Traefik schema
- Detect malicious patterns

**Validation Rules**:
- Domain names: RFC 1035 compliant
- URLs: Valid HTTP/HTTPS scheme
- Path rules: No directory traversal (`../`)
- Middleware names: Alphanumeric + hyphens/underscores
- YAML content: Parse and validate before writing

**Implementation**:
```python
import re
from urllib.parse import urlparse

def validate_domain(domain: str) -> bool:
    """Validate domain name"""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def validate_backend_url(url: str) -> bool:
    """Validate backend URL"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
    except:
        return False

def sanitize_yaml(content: str) -> str:
    """Sanitize YAML content"""
    # Parse and re-serialize to remove malicious content
    parsed = yaml.safe_load(content)
    return yaml.dump(parsed)
```

### 3. File System Security

**Requirements**:
- Restrict file operations to `/home/deploy/Infrastructure/traefik/dynamic/` directory
- Prevent path traversal attacks
- Validate file names
- Set proper file permissions (644 for config files)

**Implementation**:
```python
from pathlib import Path

DYNAMIC_CONFIG_DIR = Path("/home/deploy/Infrastructure/traefik/dynamic")

def safe_file_path(filename: str) -> Path:
    """Return safe file path or raise exception"""
    # Remove any path components
    filename = Path(filename).name

    # Validate filename
    if not re.match(r'^[a-zA-Z0-9_-]+\.yml$', filename):
        raise ValueError("Invalid filename")

    filepath = DYNAMIC_CONFIG_DIR / filename

    # Ensure path is within allowed directory
    if not filepath.resolve().is_relative_to(DYNAMIC_CONFIG_DIR.resolve()):
        raise ValueError("Path traversal detected")

    return filepath
```

### 4. Audit Logging

**Requirements**:
- Log all configuration changes
- Log authentication attempts
- Log failed operations
- Store logs in database for searchability
- Retain logs for 90 days minimum

**What to Log**:
- User ID and email
- Action performed
- Resource affected
- Old and new values
- Timestamp
- IP address
- User agent
- Success/failure
- Error messages (if any)

### 5. Rate Limiting

**Requirements**:
- Prevent API abuse
- Rate limit per user
- Higher limits for admin users

**Limits**:
- Standard users: 100 requests/minute
- Admin users: 500 requests/minute
- Burst: 50 requests
- Implement using Redis

**Implementation**:
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.get("/api/v1/traefik/routes", dependencies=[Depends(RateLimiter(times=100, minutes=1))])
async def get_routes():
    # ... implementation
```

### 6. Backup Integrity

**Requirements**:
- Verify backup integrity with checksums
- Encrypt sensitive data in backups (API keys, passwords)
- Automatic backup before any destructive operation
- Backup retention policy (keep last 50 per file)

**Implementation**:
```python
import hashlib

def create_backup(filename: str, content: str, user_email: str, description: str = None):
    """Create configuration backup"""
    # Calculate hash
    file_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check if duplicate
    existing = db.query(TraefikBackup).filter_by(
        filename=filename,
        file_hash=file_hash
    ).first()

    if existing:
        return existing.id  # Don't create duplicate

    # Create backup
    backup = TraefikBackup(
        filename=filename,
        content=content,
        file_hash=file_hash,
        created_by=user_email,
        description=description
    )
    db.add(backup)
    db.commit()

    # Clean old backups
    cleanup_old_backups(filename, keep=50)

    return backup.id
```

### 7. Certificate Security

**Requirements**:
- Never expose private keys via API
- Store ACME credentials securely
- Encrypt certificate storage
- Alert on certificate expiry
- Auto-renewal enabled by default

**Security Notes**:
- `/acme/acme.json` contains private keys (permissions: 600)
- Only read certificate metadata via API
- Private keys stay on server, never transmitted

---

## UI/UX Requirements

### 1. Page Structure

**Location**: `/admin/system/traefik`

**Navigation**:
```
Admin Dashboard
└── System
    └── Traefik Management
        ├── Routes
        ├── Services
        ├── Middleware
        ├── SSL Certificates
        ├── Configuration Files
        └── Audit Logs
```

### 2. Routes Page

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Traefik Management > Routes                    [+ Add Route]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Search: [____________________]  Filter: [All ▾] [⚙️]   │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┬──────────────────┬──────────────┬─────────────┐│
│ │ Status  │ Name / Domain    │ Service      │ Actions     ││
│ ├─────────┼──────────────────┼──────────────┼─────────────┤│
│ │ ● 🔒    │ chat-unicorncomm │ open-webui   │ ✏️ 🗑️ ⚙️  ││
│ │         │ chat.unicorncom… │              │             ││
│ │         │ Middlewares: 2   │              │             ││
│ ├─────────┼──────────────────┼──────────────┼─────────────┤│
│ │ ● 🔒    │ billing-api-unic │ lago-api     │ ✏️ 🗑️ ⚙️  ││
│ │         │ billing-api.uni… │              │             ││
│ │         │ Middlewares: 3   │              │             ││
│ └─────────┴──────────────────┴──────────────┴─────────────┘│
├─────────────────────────────────────────────────────────────┤
│ Showing 1-10 of 15 routes              [< 1 2 >]           │
└─────────────────────────────────────────────────────────────┘

Legend:
● Green = Healthy
● Yellow = Degraded
● Red = Down
🔒 = TLS enabled
```

**Filters**:
- Entry Point: All, HTTP, HTTPS
- TLS Status: All, Enabled, Disabled
- Service: Dropdown of all services
- Middleware: Dropdown of all middleware
- Status: All, Healthy, Degraded, Down

**Actions**:
- ✏️ Edit - Open edit modal
- 🗑️ Delete - Confirm and delete
- ⚙️ Settings - Advanced settings
- 🔄 Test - Test route connectivity

### 3. Create/Edit Route Modal

**Form Fields**:

```
┌─────────────────────────────────────────────────────────────┐
│ Add New Route                                    [✖️ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Basic Information                                             │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Route Name *                                           │   │
│ │ [____________________]                                 │   │
│ │ Example: my-service-https                              │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Domain *                                               │   │
│ │ [____________________] .unicorncommander.ai            │   │
│ │ Or full domain: [____________________]                 │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Routing Rule                                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Rule Type: [Host ▾]                                    │   │
│ │ ☐ Add path prefix: [/api ▾]                           │   │
│ │ ☐ Add headers: [+ Add Header]                         │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Backend Service                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ● Existing service: [Select service... ▾]             │   │
│ │ ○ Docker container: [Select container... ▾]           │   │
│ │ ○ Manual URL: [http://backend:8080_____]              │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Entry Points                                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ☑ HTTP (Port 80)                                       │   │
│ │ ☑ HTTPS (Port 443)                                     │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ SSL/TLS Configuration                                         │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ☑ Enable TLS                                           │   │
│ │   Certificate Resolver: [letsencrypt ▾]               │   │
│ │   ☐ Force HTTPS redirect                              │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Middleware Chain (Optional)                                   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ ┌──────────────────────────────────────────────────┐  │   │
│ │ │ [security-headers ▾] [+ Add Middleware]          │  │   │
│ │ │ [rate-limit       ▾]                              │  │   │
│ │ └──────────────────────────────────────────────────┘  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Advanced Settings (Optional)                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Priority: [100__]                                      │   │
│ │ ☐ Enable route                                         │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ ┌──────────────────────────────────────────────────┐        │
│ │ [Preview YAML]  [Validate]  [Cancel]  [Create]  │        │
│ └──────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Validation**:
- Real-time validation as user types
- Show errors below fields in red
- Disable Create button until form is valid
- Show warnings (not errors) in yellow

**Preview YAML**:
- Opens side panel with generated YAML
- Syntax highlighted
- Copyable

### 4. Services Page

**Layout**: Similar to Routes page

**Columns**:
- Status (● color coded)
- Name
- Backend URLs
- Health Check (✓ or ✗)
- Routes Using (count)
- Actions

**Service Detail**:
- Show all backend servers
- Health check configuration
- Load balancer settings
- Linked routes
- Test connectivity button

### 5. Middleware Page

**Layout**: Similar to Routes page

**Columns**:
- Name
- Type (badge)
- Configuration (summary)
- Usage Count
- Actions

**Middleware Types** (color-coded badges):
- 🔐 forwardAuth (blue)
- 📋 headers (green)
- ⏱️ rateLimit (orange)
- 🔀 redirect (purple)
- 🗜️ compress (gray)
- ✂️ stripPrefix (yellow)

### 6. SSL Certificates Page

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ SSL Certificates                            [⚙️ ACME Config]│
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Status: [All ▾]  Expiring: [< 30 days]  [🔍 Search]  │   │
│ └───────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ ┌──────┬───────────────────────┬────────┬──────┬─────────┐ │
│ │Status│ Domain                │ Issuer │Expiry│ Actions │ │
│ ├──────┼───────────────────────┼────────┼──────┼─────────┤ │
│ │ ✅   │ chat.unicorncommander │LE      │70 d  │ 🔄 ℹ️   │ │
│ │      │ .ai                   │        │      │         │ │
│ ├──────┼───────────────────────┼────────┼──────┼─────────┤ │
│ │ ⚠️   │ billing.unicorncomman │ LE     │15 d  │ 🔄 ℹ️   │ │
│ │      │ der.ai                │        │      │         │ │
│ └──────┴───────────────────────┴────────┴──────┴─────────┘ │
└─────────────────────────────────────────────────────────────┘

Legend:
✅ Valid (> 30 days)
⚠️ Expiring soon (< 30 days)
❌ Expired
LE = Let's Encrypt
```

**Certificate Detail Modal**:
- Domain
- Subject Alternative Names (SANs)
- Issuer
- Issue Date
- Expiration Date
- Days until expiry
- Key type (RSA, EC)
- Certificate chain
- Routes using this certificate

**Actions**:
- 🔄 Force Renewal
- ℹ️ View Details
- 📋 Copy Certificate (PEM format, no private key)

### 7. Configuration Files Page

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Configuration Files                       [📦 Create Backup]│
├─────────────────────────────────────────────────────────────┤
│ ┌────────────────────┬──────┬─────────────────┬─────────┐  │
│ │ File               │ Size │ Last Modified   │ Actions │  │
│ ├────────────────────┼──────┼─────────────────┼─────────┤  │
│ │ domains.yml        │ 8.5K │ Oct 22, 21:01   │ 👁️ ✏️ 📥 │  │
│ │ 15 routes, 15 svc  │      │                 │         │  │
│ ├────────────────────┼──────┼─────────────────┼─────────┤  │
│ │ middlewares.yml    │ 5.0K │ Oct 09, 22:36   │ 👁️ ✏️ 📥 │  │
│ │ 8 middleware       │      │                 │         │  │
│ └────────────────────┴──────┴─────────────────┴─────────┘  │
│                                                              │
│ Backups                                       [View All]     │
│ ┌────────────────────┬─────────────────┬─────────┐         │
│ │ Backup             │ Created         │ Actions │         │
│ ├────────────────────┼─────────────────┼─────────┤         │
│ │ domains.yml        │ Oct 23, 12:00   │ 🔄 📥   │         │
│ │ by admin@ex.com    │                 │         │         │
│ └────────────────────┴─────────────────┴─────────┘         │
└─────────────────────────────────────────────────────────────┘

Actions:
👁️ View
✏️ Edit (opens Monaco editor)
📥 Download
🔄 Restore
```

**File Editor**:
- Monaco editor (YAML syntax highlighting)
- Real-time validation
- Show errors inline
- Preview changes before save
- Auto-backup on save

### 8. Audit Logs Page

**Layout**: Standard table with filters

**Columns**:
- Timestamp
- User
- Action (badge)
- Resource Type
- Resource Name
- Status (✓ or ✗)
- Actions (View Details)

**Filters**:
- User (autocomplete)
- Action (create, update, delete, restore)
- Resource Type (route, service, middleware, certificate)
- Date Range (picker)
- Status (success, failure)

**Export**:
- Download as CSV
- Date range selection
- Apply current filters

### 9. Responsive Design

**Requirements**:
- Mobile-friendly (min-width: 320px)
- Tablet-optimized (768px+)
- Desktop-optimized (1024px+)
- Touch-friendly buttons (min 44px)
- Collapsible sidebars on mobile

### 10. Accessibility

**Requirements**:
- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Focus indicators
- Semantic HTML

### 11. Theme Support

**Requirements**:
- Support all three Ops-Center themes:
  - Magic Unicorn (purple gradient)
  - Dark Mode
  - Light Mode
- Consistent with existing Ops-Center UI
- Use same color palette and typography

---

## Integration Requirements

### 1. Ops-Center Integration

**Authentication**:
- Use existing Keycloak SSO integration
- Respect role-based access control (admin, moderator)
- Share session state with Ops-Center

**Navigation**:
- Add "Traefik" menu item under "System" section
- Update breadcrumbs
- Consistent header/sidebar

**API**:
- Mount Traefik API under `/api/v1/traefik`
- Use existing FastAPI app
- Share database connection
- Use existing audit logging

**UI**:
- Use existing React components (Layout, Toast, etc.)
- Follow existing design system
- Use MUI theme

### 2. Docker Integration

**Requirements**:
- Mount Docker socket for container discovery
- Read container labels for Traefik config
- Suggest services based on running containers
- Auto-populate backend URLs

**Implementation**:
```python
import docker

client = docker.from_env()

def get_web_containers():
    """Get all containers on web network"""
    containers = client.containers.list()
    web_containers = []

    for container in containers:
        networks = container.attrs['NetworkSettings']['Networks']
        if 'web' in networks:
            web_containers.append({
                'id': container.id,
                'name': container.name,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'status': container.status,
                'ports': container.ports,
                'labels': container.labels
            })

    return web_containers
```

### 3. File System Integration

**Requirements**:
- Mount `/home/deploy/Infrastructure/traefik` directory
- Read/write YAML files in `/dynamic` subdirectory
- Monitor file changes
- Create backups before modifications

**Docker Volume**:
```yaml
volumes:
  - /home/deploy/Infrastructure/traefik:/traefik:rw
```

### 4. Notification Integration

**Requirements**:
- Email alerts for certificate expiry
- Webhook alerts for service down
- Toast notifications in UI for operations
- Slack/Discord integration (optional)

**Channels**:
- Email (via existing email provider system)
- Webhook (HTTP POST)
- In-app notifications (toast)

### 5. Monitoring Integration

**Requirements**:
- Integrate with Prometheus metrics (if available)
- Display metrics in UI
- Alert based on metrics
- Historical data visualization

**Metrics to Track**:
- Request count per route
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Certificate expiry
- Service health status

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)

**Day 1: Backend Setup**
- [ ] Create database schema (3 tables)
- [ ] Set up Traefik API client (httpx)
- [ ] Implement file operations (read/write YAML)
- [ ] Create backup system
- [ ] Set up audit logging

**Day 2: Core API Endpoints**
- [ ] Routes CRUD API (6 endpoints)
- [ ] Services CRUD API (6 endpoints)
- [ ] Middleware CRUD API (6 endpoints)
- [ ] Configuration validation
- [ ] Docker integration (container discovery)

**Deliverables**:
- Working backend API
- Database tables created
- Basic YAML file operations
- API documentation

### Phase 2: UI Development (Days 3-4)

**Day 3: Routes Management UI**
- [ ] Routes list page
- [ ] Create/Edit route modal
- [ ] Route detail view
- [ ] Validation and error handling
- [ ] Delete confirmation
- [ ] Route testing

**Day 4: Services & Middleware UI**
- [ ] Services list page
- [ ] Create/Edit service modal
- [ ] Middleware list page
- [ ] Create/Edit middleware modal
- [ ] Middleware type selector
- [ ] Service health indicators

**Deliverables**:
- Functional UI for routes, services, middleware
- Form validation
- Real-time updates
- User-friendly error messages

### Phase 3: Advanced Features (Day 5)

**Day 5: SSL, Config, Audit Logs**
- [ ] SSL certificates page
- [ ] Certificate detail view
- [ ] Configuration files page
- [ ] File editor (Monaco)
- [ ] Backup/restore UI
- [ ] Audit logs page
- [ ] Export functionality

**Optional (if time permits)**:
- [ ] Route templates
- [ ] Bulk operations
- [ ] Alert configuration
- [ ] Visual topology

**Deliverables**:
- Complete feature set
- Comprehensive testing
- Documentation
- Deployment guide

### Phase 4: Testing & Deployment (Included in Phases 1-3)

**Continuous Testing**:
- Unit tests for backend functions
- Integration tests for API endpoints
- Frontend component tests
- End-to-end tests for critical flows

**Deployment Checklist**:
- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] Docker volume mounts correct
- [ ] Permissions verified
- [ ] Backup system tested
- [ ] Rollback plan documented

---

## Use Cases

### Use Case 1: Add New Service

**Actor**: System Administrator
**Goal**: Deploy new container and configure Traefik route

**Preconditions**:
- Admin is logged in
- New service container is running on web network
- Domain DNS is configured

**Steps**:
1. Admin navigates to "Traefik Management > Routes"
2. Clicks "+ Add Route" button
3. Fills in form:
   - Route name: `api-new-service`
   - Domain: `api.unicorncommander.ai`
   - Backend: Select from Docker containers dropdown → `new-service-container`
   - Entry Points: HTTPS
   - Enable TLS: Yes
   - Certificate resolver: `letsencrypt`
   - Middleware: `security-headers`, `api-cors`
4. Clicks "Validate" button
5. System validates:
   - ✓ Domain format valid
   - ✓ No conflicting routes
   - ✓ Backend container reachable
   - ✓ Middleware exists
6. Admin reviews generated YAML in preview
7. Clicks "Create" button
8. System:
   - Creates backup of `domains.yml`
   - Adds route to YAML file
   - Logs action in audit log
   - Traefik auto-detects change and reloads
9. Admin sees success toast: "Route created successfully"
10. Admin clicks "Test" button
11. System sends test request:
    - `GET https://api.unicorncommander.ai/health`
    - Returns: 200 OK (12ms)
12. SSL certificate auto-issued by Let's Encrypt within 60 seconds

**Postconditions**:
- Route is live
- SSL certificate issued
- Backup created
- Audit log entry created

**Success Criteria**:
- New service accessible via domain
- HTTPS working with valid certificate
- No existing routes affected

### Use Case 2: Update Middleware Configuration

**Actor**: System Administrator
**Goal**: Modify rate limit settings for API route

**Preconditions**:
- Admin is logged in
- Rate limit middleware exists

**Steps**:
1. Admin navigates to "Traefik Management > Middleware"
2. Finds `api-rate-limit` middleware
3. Clicks "✏️ Edit" button
4. Modal opens showing current config:
   - Type: rateLimit
   - Average: 100 requests
   - Burst: 50 requests
   - Period: 1 minute
5. Admin changes:
   - Average: 200 requests
   - Burst: 100 requests
6. Clicks "Validate" button
7. System checks:
   - ✓ Config valid
   - ⚠️ Warning: 12 routes use this middleware (will be affected)
8. Admin reviews affected routes
9. Clicks "Update" button
10. System:
    - Creates backup of `middlewares.yml`
    - Updates middleware config
    - Logs action in audit log
    - Traefik auto-reloads
11. Admin sees success toast: "Middleware updated successfully"

**Postconditions**:
- Middleware config updated
- All routes using middleware now have new rate limits
- Backup created
- Audit log entry created

**Success Criteria**:
- Rate limit changes take effect immediately
- No service disruption
- All affected routes listed

### Use Case 3: Troubleshoot Route Not Working

**Actor**: System Administrator
**Goal**: Diagnose why a route is not accessible

**Preconditions**:
- Admin is logged in
- User reports issue with `chat.unicorncommander.ai`

**Steps**:
1. Admin navigates to "Traefik Management > Routes"
2. Searches for "chat"
3. Finds `chat-unicorncommander` route
4. Status indicator shows: ● Red (Down)
5. Admin clicks route to view details
6. Route detail page shows:
   - Route configuration
   - Backend service: `open-webui-service`
   - Service health: ❌ Down
   - Last health check: Failed (connection refused)
7. Admin clicks "Test Service" button
8. System tests backend:
   - URL: `http://unicorn-open-webui:8080/health`
   - Result: Connection refused
9. Admin checks service:
   - Clicks "Services" tab
   - Finds `open-webui-service`
   - Backend URL: `http://unicorn-open-webui:8080`
10. Admin checks Docker container:
    - Views Docker containers list
    - Finds `unicorn-open-webui` is stopped
11. Admin starts container via Ops-Center Services page
12. Returns to Traefik page
13. Clicks "Test Service" again
14. Result: 200 OK (45ms)
15. Route status changes to: ● Green (Healthy)

**Postconditions**:
- Root cause identified (container stopped)
- Service restarted
- Route working

**Success Criteria**:
- Admin diagnosed issue using Traefik UI
- Clear error messages guided troubleshooting
- Service health monitoring accurate

### Use Case 4: Certificate Expiring Soon

**Actor**: System Administrator
**Goal**: Renew SSL certificate before expiry

**Preconditions**:
- Admin is logged in
- Certificate for `billing.unicorncommander.ai` expires in 15 days
- Email alert sent to admin

**Steps**:
1. Admin receives email: "SSL Certificate Expiring Soon: billing.unicorncommander.ai (15 days)"
2. Admin logs into Ops-Center
3. Navigates to "Traefik Management > SSL Certificates"
4. Certificate list shows:
   - ⚠️ `billing.unicorncommander.ai` - Expires in 15 days
5. Admin clicks "ℹ️ View Details"
6. Certificate detail modal shows:
   - Domain: billing.unicorncommander.ai
   - Issuer: Let's Encrypt
   - Issued: July 24, 2025
   - Expires: November 7, 2025
   - Days until expiry: 15
   - Auto-renewal: Enabled
   - Next renewal attempt: November 2, 2025
7. Admin clicks "🔄 Force Renewal" button
8. System triggers ACME renewal:
   - Contacts Let's Encrypt
   - Performs HTTP-01 challenge
   - Issues new certificate
   - Updates Traefik config
9. Success toast: "Certificate renewed successfully"
10. Certificate detail updated:
    - Issued: October 23, 2025
    - Expires: January 21, 2026
    - Days until expiry: 90

**Postconditions**:
- Certificate renewed
- New expiry date in 90 days
- Alert cleared
- Audit log entry created

**Success Criteria**:
- Certificate renewal successful
- No service downtime
- Clear visibility into certificate status

### Use Case 5: Rollback Bad Configuration

**Actor**: System Administrator
**Goal**: Restore previous configuration after error

**Preconditions**:
- Admin is logged in
- Admin made changes that broke routing

**Steps**:
1. Admin navigates to "Traefik Management > Configuration Files"
2. Sees `domains.yml` last modified 2 minutes ago
3. Routes are not working correctly
4. Admin clicks "View All" backups
5. Backup list shows:
   - `domains.yml` - Oct 23, 12:00 - by admin@example.com - "Before adding new route"
   - `domains.yml` - Oct 23, 11:58 - by admin@example.com - "Automatic backup"
6. Admin clicks "ℹ️ View" on first backup
7. Backup detail shows:
   - Timestamp
   - User
   - Description
   - File diff (showing changes)
8. Admin reviews diff
9. Admin clicks "🔄 Restore" button
10. Confirmation modal:
    - "Are you sure you want to restore this backup?"
    - "Current configuration will be backed up before restore"
    - Shows diff preview
11. Admin clicks "Confirm Restore"
12. System:
    - Creates backup of current config
    - Restores previous config
    - Logs action in audit log
    - Traefik auto-reloads
13. Success toast: "Configuration restored successfully"
14. Admin verifies routes are working

**Postconditions**:
- Previous configuration restored
- Current config backed up before restore
- Routes working correctly
- Audit log entry created

**Success Criteria**:
- Restore process fast (<5 seconds)
- No data loss
- Clear diff preview
- Audit trail preserved

---

## Technical Challenges

### 1. File Provider Hot-Reload Timing

**Challenge**: Traefik watches files and reloads, but timing is non-deterministic

**Solution**:
- After writing file, poll Traefik API to verify changes loaded
- Timeout after 10 seconds
- Show loading indicator in UI
- Retry mechanism if reload fails

**Implementation**:
```python
async def wait_for_reload(route_name: str, timeout: int = 10):
    """Wait for Traefik to reload and detect new route"""
    start = time.time()
    while time.time() - start < timeout:
        routes = await get_traefik_routes()
        if route_name in routes:
            return True
        await asyncio.sleep(0.5)
    return False
```

### 2. YAML Merge Conflicts

**Challenge**: Multiple admins editing config files simultaneously

**Solution**:
- Lock file during edit (Redis lock)
- Detect conflicts before save
- Show diff to user
- Allow manual merge

**Implementation**:
```python
from redis import Redis
from contextlib import contextmanager

redis = Redis()

@contextmanager
def file_lock(filename: str, timeout: int = 30):
    """Acquire distributed file lock"""
    lock = redis.lock(f"traefik:file:{filename}", timeout=timeout)
    acquired = lock.acquire(blocking=True, blocking_timeout=10)
    if not acquired:
        raise Exception("Could not acquire file lock")
    try:
        yield
    finally:
        lock.release()

async def update_route(filename: str, route_config: dict):
    """Update route with file locking"""
    with file_lock(filename):
        # Load current file
        current_config = load_yaml(filename)

        # Check for conflicts
        if current_config["modified"] > route_config["last_seen"]:
            raise ConflictError("File modified by another user")

        # Update and save
        current_config["http"]["routers"][route_config["name"]] = route_config
        save_yaml(filename, current_config)
```

### 3. Route Conflict Detection

**Challenge**: Detecting when two routes have overlapping rules

**Solution**:
- Parse all route rules
- Check for overlaps (same Host + PathPrefix)
- Consider priority values
- Warn user before creating conflicting route

**Implementation**:
```python
def detect_conflicts(new_route: dict, existing_routes: list) -> list:
    """Detect route conflicts"""
    conflicts = []

    new_rule = parse_rule(new_route["rule"])
    new_priority = new_route.get("priority", 0)

    for route in existing_routes:
        existing_rule = parse_rule(route["rule"])
        existing_priority = route.get("priority", 0)

        # Same host and path prefix
        if (new_rule["host"] == existing_rule["host"] and
            new_rule["path"].startswith(existing_rule["path"])):

            # Conflict if same priority
            if new_priority == existing_priority:
                conflicts.append({
                    "route": route["name"],
                    "reason": "Same host and path with equal priority"
                })
            # Warning if different priority
            elif new_priority < existing_priority:
                conflicts.append({
                    "route": route["name"],
                    "reason": "Existing route has higher priority (will match first)",
                    "severity": "warning"
                })

    return conflicts
```

### 4. Traefik API Authentication

**Challenge**: Traefik API may be protected or require authentication

**Solution**:
- Check if API requires auth
- If yes, configure Basic Auth credentials
- Store credentials securely (encrypted)
- Fall back to file-only mode if API unavailable

**Implementation**:
```python
async def get_traefik_client():
    """Get authenticated Traefik API client"""
    auth = None

    # Check if auth required
    if TRAEFIK_API_AUTH_ENABLED:
        auth = httpx.BasicAuth(
            username=TRAEFIK_API_USER,
            password=TRAEFIK_API_PASSWORD
        )

    client = httpx.AsyncClient(
        base_url=TRAEFIK_API_URL,
        auth=auth,
        timeout=10.0
    )

    # Test connection
    try:
        response = await client.get("/api/version")
        response.raise_for_status()
    except httpx.HTTPError:
        # API not accessible, fall back to file-only mode
        raise TraefikAPIUnavailable()

    return client
```

### 5. Certificate Storage Security

**Challenge**: `/acme/acme.json` contains private keys (highly sensitive)

**Solution**:
- Never read or expose private keys via API
- Only read certificate metadata
- Use Traefik API for certificate info (doesn't include private keys)
- Set strict file permissions (600)

**Implementation**:
```python
def get_certificate_info(domain: str) -> dict:
    """Get certificate info WITHOUT private key"""
    # Read from Traefik API (no private keys)
    async with get_traefik_client() as client:
        response = await client.get("/api/http/routers")
        # ... parse response

    # Never parse acme.json directly (contains private keys)
    # If we must read acme.json, only extract certificate metadata
    acme_data = load_json("/acme/acme.json")
    cert_data = acme_data["letsencrypt"]["Certificates"][domain]

    return {
        "domain": cert_data["domain"]["main"],
        "sans": cert_data["domain"]["sans"],
        "not_before": cert_data["certificate"]["NotBefore"],
        "not_after": cert_data["certificate"]["NotAfter"],
        # DO NOT include private key!
    }
```

### 6. Real-time Updates

**Challenge**: Show real-time status updates without constant polling

**Solution**:
- WebSocket connection for live updates
- Server pushes updates when Traefik reloads
- File watcher on backend detects changes
- Client reconnects on disconnect

**Implementation**:
```python
from fastapi import WebSocket

@app.websocket("/api/v1/traefik/ws")
async def traefik_websocket(websocket: WebSocket):
    """WebSocket for real-time Traefik updates"""
    await websocket.accept()

    # Watch for file changes
    watcher = FileWatcher(DYNAMIC_CONFIG_DIR)

    try:
        async for event in watcher:
            if event.type == "modified":
                # File changed, notify client
                await websocket.send_json({
                    "type": "config_updated",
                    "file": event.filename,
                    "timestamp": time.time()
                })

                # Wait for Traefik reload
                await asyncio.sleep(1)

                # Send updated data
                routes = await get_traefik_routes()
                await websocket.send_json({
                    "type": "routes_updated",
                    "routes": routes
                })
    except WebSocketDisconnect:
        pass
```

### 7. Docker Socket Permissions

**Challenge**: Ops-Center container needs Docker socket access for container discovery

**Solution**:
- Mount Docker socket read-only
- Run Docker commands as non-root user
- Add ops-center user to docker group
- Validate container network before suggesting

**Docker Compose**:
```yaml
ops-center:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  user: "${UID}:${DOCKER_GID}"
  group_add:
    - docker
```

---

## Success Criteria

### Functional Success Criteria

1. **Routes Management**:
   - ✓ Can create new routes via GUI
   - ✓ Can edit existing routes
   - ✓ Can delete routes with confirmation
   - ✓ Changes reflected in Traefik within 5 seconds
   - ✓ No manual file editing required

2. **Service Management**:
   - ✓ Can create and manage backend services
   - ✓ Docker containers auto-discovered
   - ✓ Service health checks functional
   - ✓ Health status updated every 30 seconds

3. **Middleware Management**:
   - ✓ Can create middleware of all supported types
   - ✓ Middleware reusable across routes
   - ✓ Usage count accurate

4. **SSL/TLS Management**:
   - ✓ Certificate status visible
   - ✓ Expiry warnings shown (< 30 days)
   - ✓ Manual renewal works
   - ✓ Auto-renewal enabled by default

5. **Validation**:
   - ✓ Configuration validated before save
   - ✓ Conflicts detected and shown
   - ✓ Helpful error messages
   - ✓ No invalid config can be saved

6. **Backup/Restore**:
   - ✓ Automatic backup before changes
   - ✓ Manual backup on demand
   - ✓ Restore previous config works
   - ✓ Last 50 backups retained

7. **Audit Logging**:
   - ✓ All changes logged
   - ✓ Logs searchable and filterable
   - ✓ Logs exportable to CSV
   - ✓ 90-day retention

### Performance Success Criteria

1. **Response Times**:
   - API endpoints respond in < 500ms (p95)
   - Page load time < 2 seconds
   - File operations < 1 second
   - Traefik reload detection < 5 seconds

2. **Scalability**:
   - Handle 100+ routes efficiently
   - Support 10+ concurrent users
   - Database queries optimized
   - No N+1 query issues

3. **Reliability**:
   - 99.9% uptime
   - Automatic recovery from Traefik API failures
   - Graceful handling of file conflicts
   - No data loss on errors

### Security Success Criteria

1. **Authentication**:
   - ✓ All endpoints require authentication
   - ✓ Only admin/moderator roles can access
   - ✓ Session timeout enforced
   - ✓ No unauthenticated access

2. **Input Validation**:
   - ✓ All inputs validated
   - ✓ YAML injection prevented
   - ✓ Path traversal prevented
   - ✓ XSS prevented

3. **Audit Trail**:
   - ✓ All actions logged
   - ✓ User identity tracked
   - ✓ IP address recorded
   - ✓ Tampering detected

4. **Sensitive Data**:
   - ✓ Private keys never exposed
   - ✓ Credentials encrypted
   - ✓ Secure file permissions
   - ✓ No secrets in logs

### Usability Success Criteria

1. **User Experience**:
   - Intuitive navigation
   - Clear error messages
   - Helpful tooltips
   - Fast feedback on actions
   - Undo capability (rollback)

2. **Documentation**:
   - User guide created
   - API documentation complete
   - Troubleshooting guide included
   - Video tutorials (optional)

3. **Accessibility**:
   - WCAG 2.1 AA compliant
   - Keyboard navigation works
   - Screen reader compatible
   - High contrast mode supported

### Testing Success Criteria

1. **Unit Tests**:
   - 80%+ code coverage
   - All critical functions tested
   - Edge cases covered

2. **Integration Tests**:
   - API endpoints tested
   - File operations tested
   - Docker integration tested
   - Traefik API integration tested

3. **End-to-End Tests**:
   - Create route flow works
   - Edit route flow works
   - Delete route flow works
   - Restore backup works
   - Certificate renewal works

4. **User Acceptance Testing**:
   - Admin can complete all use cases
   - No blockers or critical bugs
   - Performance acceptable
   - UI responsive and intuitive

---

## Appendix

### A. Traefik Configuration Reference

**Static Configuration** (requires restart):
- Entry points
- Providers (docker, file, etc.)
- Certificate resolvers
- API/Dashboard settings
- Log settings

**Dynamic Configuration** (hot-reload):
- HTTP routers
- HTTP services
- HTTP middleware
- TCP routers (not in scope)
- UDP routers (not in scope)

**Configuration Sources**:
1. File provider (`/dynamic/*.yml`)
2. Docker provider (container labels)
3. Kubernetes provider (not used)
4. Consul/Etcd (not used)

### B. Middleware Types

**Supported Middleware**:

1. **AddPrefix**: Add path prefix
2. **BasicAuth**: HTTP Basic Authentication
3. **Buffering**: Buffer requests/responses
4. **Chain**: Combine multiple middleware
5. **CircuitBreaker**: Prevent cascading failures
6. **Compress**: Compress responses (gzip, br)
7. **DigestAuth**: HTTP Digest Authentication
8. **Errors**: Custom error pages
9. **ForwardAuth**: Forward authentication
10. **Headers**: Modify request/response headers
11. **IPWhiteList**: IP-based access control
12. **InFlightReq**: Limit concurrent requests
13. **PassTLSClientCert**: Pass client certificate
14. **RateLimit**: Rate limiting
15. **RedirectRegex**: Regex-based redirect
16. **RedirectScheme**: HTTP → HTTPS redirect
17. **ReplacePath**: Replace path
18. **ReplacePathRegex**: Regex-based path replace
19. **Retry**: Retry failed requests
20. **StripPrefix**: Remove path prefix
21. **StripPrefixRegex**: Regex-based prefix removal

**Most Commonly Used**:
- Headers (security headers, CORS)
- ForwardAuth (authentication)
- RateLimit (DDoS protection)
- Compress (performance)
- RedirectScheme (HTTPS redirect)

### C. Traefik API Endpoints

**Read-Only Endpoints**:
```
GET /api/version
GET /api/overview
GET /api/rawdata
GET /api/entrypoints
GET /api/http/routers
GET /api/http/routers/{name}
GET /api/http/services
GET /api/http/services/{name}
GET /api/http/middlewares
GET /api/http/middlewares/{name}
GET /api/tcp/routers
GET /api/tcp/services
GET /api/udp/routers
GET /api/udp/services
```

**Dashboard**:
```
GET /dashboard/
GET /api/http/routers?search=...
```

**Write Operations**: Not supported via API
- Must use file provider or Docker labels

### D. YAML Structure

**HTTP Router**:
```yaml
http:
  routers:
    my-router:
      rule: "Host(`example.com`) && PathPrefix(`/api`)"
      service: my-service
      entryPoints:
        - https
      middlewares:
        - middleware-1
        - middleware-2
      tls:
        certResolver: letsencrypt
        domains:
          - main: example.com
            sans:
              - www.example.com
      priority: 100
```

**HTTP Service**:
```yaml
http:
  services:
    my-service:
      loadBalancer:
        servers:
          - url: "http://backend-1:8080"
          - url: "http://backend-2:8080"
        sticky:
          cookie:
            name: sticky
        healthCheck:
          path: /health
          interval: "30s"
          timeout: "10s"
          scheme: http
        passHostHeader: true
```

**Middleware**:
```yaml
http:
  middlewares:
    my-middleware:
      headers:
        customRequestHeaders:
          X-Custom-Header: "value"
        customResponseHeaders:
          X-Frame-Options: "SAMEORIGIN"
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
```

### E. Environment Variables

**Required**:
```bash
# Traefik API
TRAEFIK_API_URL=http://traefik:8080/api
TRAEFIK_API_AUTH_ENABLED=false

# Dynamic Config Directory
TRAEFIK_DYNAMIC_CONFIG_DIR=/home/deploy/Infrastructure/traefik/dynamic

# ACME Storage
TRAEFIK_ACME_STORAGE=/home/deploy/Infrastructure/traefik/acme/acme.json

# Docker Socket
DOCKER_HOST=unix:///var/run/docker.sock

# Database (use existing Ops-Center DB)
POSTGRES_HOST=unicorn-postgresql
POSTGRES_PORT=5432
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=<from .env>
POSTGRES_DB=unicorn_db

# Redis (for locking)
REDIS_HOST=unicorn-redis
REDIS_PORT=6379
```

### F. Resources & References

**Traefik Documentation**:
- Official Docs: https://doc.traefik.io/traefik/
- API Reference: https://doc.traefik.io/traefik/operations/api/
- File Provider: https://doc.traefik.io/traefik/providers/file/
- Docker Provider: https://doc.traefik.io/traefik/providers/docker/
- Let's Encrypt: https://doc.traefik.io/traefik/https/acme/

**Similar Tools** (for inspiration):
- Traefik Pilot (deprecated)
- Portainer (Docker UI)
- Rancher (Kubernetes UI)
- Nginx Proxy Manager
- Caddy (competitor with built-in UI)

**Technologies**:
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Material-UI: https://mui.com/
- Monaco Editor: https://microsoft.github.io/monaco-editor/
- YAML Parser: https://pyyaml.org/

---

## Questions for Stakeholder

Before starting implementation, clarify:

1. **Priority**: Which features are MVP vs nice-to-have?
2. **Traefik API Access**: Is Traefik API accessible? Authentication required?
3. **Permissions**: Can Ops-Center container mount Traefik config directory?
4. **Docker Socket**: Can Ops-Center access Docker socket for container discovery?
5. **Notifications**: Which notification channels are required (email, webhook, slack)?
6. **Monitoring**: Is Prometheus available for metrics integration?
7. **Backup Retention**: How many backups to keep? How long to retain?
8. **User Roles**: Should moderators have full access or read-only?
9. **Multi-User**: Expected number of concurrent admin users?
10. **Deployment Timeline**: When is feature needed in production?

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Author**: Research Agent
**Status**: Ready for Architecture Phase
