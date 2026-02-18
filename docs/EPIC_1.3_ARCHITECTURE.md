# Epic 1.3: Traefik Configuration Management
## System Architecture Design Document

**Version**: 1.0
**Created**: October 23, 2025
**Author**: System Architecture Designer
**Status**: Design Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Overall Architecture](#overall-architecture)
3. [Configuration Storage Design](#configuration-storage-design)
4. [API Architecture](#api-architecture)
5. [Data Models](#data-models)
6. [Traefik Integration Strategy](#traefik-integration-strategy)
7. [Frontend Architecture](#frontend-architecture)
8. [Security Architecture](#security-architecture)
9. [High Availability & Resilience](#high-availability--resilience)
10. [SSL/TLS Management](#ssltls-management)
11. [Deployment Strategy](#deployment-strategy)
12. [Migration Plan](#migration-plan)
13. [Performance Considerations](#performance-considerations)
14. [Appendix](#appendix)

---

## Executive Summary

### Problem Statement

Currently, Traefik configuration in UC-Cloud is managed manually through YAML files in `/home/deploy/Infrastructure/traefik/dynamic/`. This approach has several limitations:

- **No validation**: Configuration errors only discovered after applying changes
- **No rollback**: Failed changes require manual file restoration
- **No audit trail**: No tracking of who made what changes and when
- **No conflict detection**: Multiple admins can create conflicting routes
- **No discovery**: Services must be manually added to Traefik config
- **Complex SSL management**: Let's Encrypt certificate lifecycle requires manual monitoring

### Solution Overview

Epic 1.3 delivers a **web-based Traefik management interface** integrated into Ops-Center, providing:

- **Dynamic route management**: Create, update, delete routes without Traefik restart
- **Visual configuration**: Intuitive UI for route, service, and middleware management
- **Real-time validation**: Detect conflicts and errors before applying changes
- **Automated SSL**: Let's Encrypt certificate provisioning and renewal monitoring
- **Service discovery**: Auto-detect Docker containers with Traefik labels
- **Audit logging**: Complete change history with rollback capability
- **Health monitoring**: Real-time traffic metrics and health status

### Technology Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Configuration Method** | File Provider (YAML) | Simple, reliable, well-tested; Traefik watches directory |
| **Storage Backend** | PostgreSQL + File System | Hybrid approach: DB for metadata, files for actual config |
| **Cache Layer** | Redis | Fast lookups for route validation and metrics |
| **Validation** | Pre-apply validation engine | Prevent invalid config from reaching Traefik |
| **SSL Management** | Let's Encrypt + File watcher | Automated cert lifecycle with monitoring |
| **Service Discovery** | Docker API + PostgreSQL | Track both Docker labels and manual routes |

---

## Overall Architecture

### Architecture Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                Ops-Center                                    │
│                     https://unicorncommander.ai                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │                              │
            ┌───────▼────────┐            ┌────────▼────────┐
            │  Frontend UI    │            │  Backend API    │
            │  (React SPA)    │            │  (FastAPI)      │
            │                 │            │                 │
            │ - Route Editor  │            │ - Validation    │
            │ - SSL Monitor   │            │ - File Writer   │
            │ - Traffic View  │            │ - Health Check  │
            └─────────────────┘            └────────┬────────┘
                                                    │
                                    ┌───────────────┼──────────────┐
                                    │               │              │
                            ┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
                            │ PostgreSQL   │ │   Redis   │ │File System│
                            │              │ │           │ │           │
                            │ - Routes     │ │ - Cache   │ │ - YAML    │
                            │ - Metadata   │ │ - Metrics │ │ - Configs │
                            │ - Audit Log  │ │           │ │           │
                            └──────────────┘ └───────────┘ └─────┬─────┘
                                                                  │
                                                          ┌───────▼───────┐
                                                          │    Traefik    │
                                                          │   (v3.0)      │
                                                          │               │
                                                          │ - Watches     │
                                                          │   /dynamic    │
                                                          │ - Hot Reload  │
                                                          │ - No Restart  │
                                                          └───────┬───────┘
                                                                  │
                                                    ┌─────────────┼─────────────┐
                                                    │             │             │
                                            ┌───────▼──────┐ ┌───▼─────┐ ┌────▼────┐
                                            │ ops-center   │ │chat.uc  │ │brigade  │
                                            │ :8084        │ │ :8080   │ │ :8102   │
                                            └──────────────┘ └─────────┘ └─────────┘
```

### Component Interaction Flow

```
1. Admin creates route via UI
   ↓
2. Frontend sends request to /api/v1/traefik/routes
   ↓
3. Backend validates:
   - No conflicting routes
   - Valid service exists
   - Middleware chain valid
   - Domain available
   ↓
4. Backend writes to PostgreSQL (metadata + audit)
   ↓
5. Backend generates YAML config
   ↓
6. Backend writes to /dynamic/ops-center-managed.yml
   ↓
7. Traefik detects file change (inotify)
   ↓
8. Traefik hot-reloads config (no restart)
   ↓
9. Backend verifies route is active
   ↓
10. Backend updates cache (Redis)
   ↓
11. Frontend shows success notification
```

### Design Decision: File Provider vs HTTP Provider

**Evaluated Options**:

#### Option A: File Provider (YAML)
**Pros**:
- ✅ Simple and reliable
- ✅ Well-documented and tested
- ✅ No Traefik restart needed
- ✅ Easy to debug (human-readable YAML)
- ✅ Can be version-controlled
- ✅ Traefik watches directory with inotify

**Cons**:
- ❌ Requires file system access
- ❌ Potential file locking issues
- ❌ Latency in file system operations

#### Option B: HTTP Provider
**Pros**:
- ✅ Dynamic config via HTTP endpoint
- ✅ No file system dependency
- ✅ Faster propagation

**Cons**:
- ❌ Requires ops-center to serve Traefik config
- ❌ More complex error handling
- ❌ Less mature than file provider
- ❌ Requires keeping config in memory

#### Option C: Docker Labels (Programmatic)
**Pros**:
- ✅ Native Traefik integration
- ✅ Automatic service discovery

**Cons**:
- ❌ Cannot manage non-Docker services
- ❌ Requires Docker API access
- ❌ Complex label syntax
- ❌ Hard to manage externally

#### DECISION: Hybrid Approach (File + Docker)

**Selected Strategy**:
- **Use File Provider** for ops-center managed routes
- **Keep Docker Provider** for container auto-discovery
- **Store metadata in PostgreSQL** for validation and audit
- **Use Redis** for caching and fast lookups

**Rationale**:
1. File provider is proven and reliable
2. Docker provider handles container auto-discovery
3. PostgreSQL provides rich querying and audit
4. Redis gives fast validation and metrics
5. Hybrid approach leverages strengths of each

---

## Configuration Storage Design

### Database Schema (PostgreSQL)

```sql
-- Routes table: Core routing configuration
CREATE TABLE traefik_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    rule TEXT NOT NULL,  -- Host(`example.com`) && PathPrefix(`/api`)
    service_id UUID NOT NULL REFERENCES traefik_services(id),
    priority INTEGER DEFAULT 0,
    entrypoints TEXT[] DEFAULT ARRAY['http', 'https'],
    tls_enabled BOOLEAN DEFAULT true,
    tls_cert_resolver VARCHAR(50) DEFAULT 'letsencrypt',
    middlewares TEXT[],  -- Array of middleware names
    status VARCHAR(20) DEFAULT 'active',  -- active, disabled, pending
    source VARCHAR(20) DEFAULT 'manual',  -- manual, docker, imported
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    CONSTRAINT valid_status CHECK (status IN ('active', 'disabled', 'pending', 'error')),
    CONSTRAINT valid_source CHECK (source IN ('manual', 'docker', 'imported'))
);

CREATE INDEX idx_routes_status ON traefik_routes(status);
CREATE INDEX idx_routes_source ON traefik_routes(source);
CREATE INDEX idx_routes_created_at ON traefik_routes(created_at);
CREATE INDEX idx_routes_rule ON traefik_routes USING GIN (to_tsvector('english', rule));

-- Services table: Backend service configuration
CREATE TABLE traefik_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(20) DEFAULT 'loadbalancer',  -- loadbalancer, weighted, mirroring
    servers JSONB NOT NULL,  -- [{"url": "http://backend:8080", "weight": 1}]
    pass_host_header BOOLEAN DEFAULT true,
    health_check JSONB,  -- {"path": "/health", "interval": "30s", "timeout": "5s"}
    sticky_sessions JSONB,  -- {"cookie": {"name": "session", "secure": true}}
    circuit_breaker JSONB,  -- {"expression": "NetworkErrorRatio() > 0.5"}
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    CONSTRAINT valid_service_type CHECK (type IN ('loadbalancer', 'weighted', 'mirroring'))
);

CREATE INDEX idx_services_status ON traefik_services(status);
CREATE INDEX idx_services_name ON traefik_services(name);

-- Middleware table: Reusable middleware configurations
CREATE TABLE traefik_middleware (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- rateLimit, headers, auth, stripPrefix, etc.
    config JSONB NOT NULL,  -- Type-specific configuration
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    usage_count INTEGER DEFAULT 0,  -- How many routes use this
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    CONSTRAINT valid_middleware_type CHECK (type IN (
        'rateLimit', 'headers', 'basicAuth', 'forwardAuth',
        'stripPrefix', 'compress', 'redirect', 'ipWhiteList',
        'circuitBreaker', 'retry', 'buffering'
    ))
);

CREATE INDEX idx_middleware_type ON traefik_middleware(type);
CREATE INDEX idx_middleware_status ON traefik_middleware(status);

-- SSL Certificates table: Track Let's Encrypt certificates
CREATE TABLE traefik_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(20) DEFAULT 'acme',  -- acme, manual, wildcard
    resolver VARCHAR(50) DEFAULT 'letsencrypt',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, valid, expiring, expired, error
    issued_at TIMESTAMP,
    expires_at TIMESTAMP,
    last_renewal_attempt TIMESTAMP,
    renewal_attempts INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_cert_status CHECK (status IN ('pending', 'valid', 'expiring', 'expired', 'error'))
);

CREATE INDEX idx_certs_domain ON traefik_certificates(domain);
CREATE INDEX idx_certs_expires_at ON traefik_certificates(expires_at);
CREATE INDEX idx_certs_status ON traefik_certificates(status);

-- Audit log: Track all configuration changes
CREATE TABLE traefik_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- route, service, middleware
    entity_id UUID NOT NULL,
    entity_name VARCHAR(255),
    action VARCHAR(50) NOT NULL,  -- create, update, delete, enable, disable
    changes JSONB,  -- {"field": {"old": "value", "new": "value"}}
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_entity_type CHECK (entity_type IN ('route', 'service', 'middleware', 'certificate')),
    CONSTRAINT valid_action CHECK (action IN ('create', 'update', 'delete', 'enable', 'disable', 'apply', 'rollback'))
);

CREATE INDEX idx_audit_entity_type ON traefik_audit_log(entity_type);
CREATE INDEX idx_audit_entity_id ON traefik_audit_log(entity_id);
CREATE INDEX idx_audit_action ON traefik_audit_log(action);
CREATE INDEX idx_audit_created_at ON traefik_audit_log(created_at DESC);
CREATE INDEX idx_audit_user_id ON traefik_audit_log(user_id);

-- Configuration snapshots: For rollback
CREATE TABLE traefik_config_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_name VARCHAR(255),
    description TEXT,
    config_data JSONB NOT NULL,  -- Complete config state
    file_content TEXT,  -- Actual YAML content
    is_automatic BOOLEAN DEFAULT false,  -- Auto-created before changes
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    restored_at TIMESTAMP,
    restored_by VARCHAR(255)
);

CREATE INDEX idx_snapshots_created_at ON traefik_config_snapshots(created_at DESC);
CREATE INDEX idx_snapshots_is_automatic ON traefik_config_snapshots(is_automatic);

-- Route conflicts: Track potential conflicts
CREATE TABLE traefik_route_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id_1 UUID NOT NULL REFERENCES traefik_routes(id),
    route_id_2 UUID NOT NULL REFERENCES traefik_routes(id),
    conflict_type VARCHAR(50) NOT NULL,  -- duplicate_host, priority_conflict, regex_overlap
    severity VARCHAR(20) DEFAULT 'warning',  -- warning, error, critical
    description TEXT,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_conflict_type CHECK (conflict_type IN ('duplicate_host', 'priority_conflict', 'regex_overlap', 'middleware_chain')),
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'error', 'critical'))
);

CREATE INDEX idx_conflicts_resolved ON traefik_route_conflicts(resolved);
CREATE INDEX idx_conflicts_severity ON traefik_route_conflicts(severity);
```

### File System Structure

```
/home/deploy/Infrastructure/traefik/
├── traefik.yml                              # Static config (unchanged)
├── docker-compose.yml                       # Traefik container (unchanged)
├── acme/                                    # Let's Encrypt certificates
│   └── acme.json                            # Certificate storage
└── dynamic/                                 # Dynamic configuration directory
    ├── ops-center-managed.yml               # ⭐ NEW: Generated by Ops-Center
    ├── ops-center-routes.yml                # ⭐ NEW: Active routes
    ├── ops-center-services.yml              # ⭐ NEW: Backend services
    ├── ops-center-middleware.yml            # ⭐ NEW: Middleware definitions
    ├── middlewares.yml                      # Existing (keep for compatibility)
    ├── domains.yml                          # Existing (migrate to ops-center)
    ├── api-domains.yml                      # Existing (migrate to ops-center)
    ├── billing-routes.yml                   # Existing (migrate to ops-center)
    └── *.yml.backup.YYYYMMDD-HHMMSS        # Automatic backups before changes
```

### Redis Cache Structure

```
traefik:routes:all                  # SET: All route IDs
traefik:routes:{id}                 # HASH: Route details
traefik:routes:by_domain:{domain}   # SET: Route IDs for domain
traefik:services:all                # SET: All service IDs
traefik:services:{id}               # HASH: Service details
traefik:middleware:all              # SET: All middleware IDs
traefik:middleware:{id}             # HASH: Middleware details
traefik:certs:all                   # SET: All certificate domains
traefik:certs:{domain}              # HASH: Certificate details
traefik:metrics:requests:{route}    # ZSET: Request count per route
traefik:metrics:errors:{route}      # ZSET: Error count per route
traefik:metrics:latency:{route}     # ZSET: Average latency per route
traefik:conflicts:active            # SET: Active conflict IDs
traefik:validation:cache:{hash}     # STRING: Validation result cache (TTL 300s)
```

**Cache TTL Strategy**:
- Route/Service/Middleware data: 60 seconds
- Metrics: 10 seconds
- Conflicts: 30 seconds
- Validation cache: 300 seconds (5 minutes)

---

## API Architecture

### API Endpoints Specification

#### Routes Management

```yaml
GET /api/v1/traefik/routes
  Description: List all routes with filtering and pagination
  Query Parameters:
    - search: string (search in name, rule, domain)
    - status: string (active, disabled, pending, error)
    - source: string (manual, docker, imported)
    - domain: string (filter by domain)
    - service_id: uuid (filter by service)
    - limit: integer (default 50, max 500)
    - offset: integer (default 0)
    - sort: string (name, created_at, priority) (default created_at)
    - order: string (asc, desc) (default desc)
  Response:
    {
      "total": 42,
      "limit": 50,
      "offset": 0,
      "routes": [
        {
          "id": "uuid",
          "name": "unicorncommander-ai",
          "rule": "Host(`unicorncommander.ai`) || Host(`www.unicorncommander.ai`)",
          "service_id": "uuid",
          "service_name": "ops-center",
          "priority": 0,
          "entrypoints": ["http", "https"],
          "tls": {
            "enabled": true,
            "cert_resolver": "letsencrypt",
            "domains": ["unicorncommander.ai", "www.unicorncommander.ai"]
          },
          "middlewares": ["security-headers", "compress"],
          "status": "active",
          "source": "manual",
          "metrics": {
            "requests_total": 15234,
            "requests_per_minute": 12.5,
            "error_rate": 0.02,
            "avg_latency_ms": 45.3
          },
          "created_at": "2025-10-23T12:00:00Z",
          "updated_at": "2025-10-23T12:00:00Z"
        }
      ]
    }

GET /api/v1/traefik/routes/{id}
  Description: Get detailed route information
  Response:
    {
      "id": "uuid",
      "name": "unicorncommander-ai",
      "rule": "Host(`unicorncommander.ai`)",
      "service": {
        "id": "uuid",
        "name": "ops-center",
        "servers": [{"url": "http://ops-center-direct:8000"}],
        "health_status": "healthy"
      },
      "priority": 0,
      "entrypoints": ["http", "https"],
      "tls": {
        "enabled": true,
        "cert_resolver": "letsencrypt",
        "certificate": {
          "domain": "unicorncommander.ai",
          "status": "valid",
          "issued_at": "2025-09-23T00:00:00Z",
          "expires_at": "2025-12-22T00:00:00Z",
          "days_until_expiry": 60
        }
      },
      "middlewares": [
        {
          "name": "security-headers",
          "type": "headers",
          "config": {...}
        }
      ],
      "status": "active",
      "source": "manual",
      "health": {
        "status": "healthy",
        "last_check": "2025-10-23T12:00:00Z",
        "response_time_ms": 12.5
      },
      "metrics": {
        "requests": {
          "total": 15234,
          "per_minute": 12.5,
          "per_hour": 750
        },
        "errors": {
          "total": 42,
          "rate": 0.02,
          "4xx": 35,
          "5xx": 7
        },
        "latency": {
          "avg_ms": 45.3,
          "p50_ms": 42.0,
          "p95_ms": 78.5,
          "p99_ms": 125.0
        }
      },
      "conflicts": [],
      "metadata": {},
      "created_at": "2025-10-23T12:00:00Z",
      "created_by": "admin@example.com",
      "updated_at": "2025-10-23T12:00:00Z",
      "updated_by": "admin@example.com"
    }

POST /api/v1/traefik/routes
  Description: Create new route
  Request Body:
    {
      "name": "my-service",
      "rule": "Host(`my-service.unicorncommander.ai`)",
      "service_id": "uuid",  # OR create new service
      "service": {  # If service_id not provided
        "name": "my-service-backend",
        "servers": [
          {"url": "http://my-service:8000", "weight": 1}
        ],
        "health_check": {
          "path": "/health",
          "interval": "30s",
          "timeout": "5s"
        }
      },
      "priority": 0,
      "entrypoints": ["https"],
      "tls": {
        "enabled": true,
        "cert_resolver": "letsencrypt"
      },
      "middlewares": ["security-headers", "rate-limit"],
      "metadata": {
        "description": "My awesome service",
        "owner": "team-platform"
      }
    }
  Response:
    {
      "id": "uuid",
      "name": "my-service",
      "status": "pending",
      "validation": {
        "passed": true,
        "warnings": [],
        "errors": []
      },
      "applied": false,
      "message": "Route created successfully. Applying configuration..."
    }

PUT /api/v1/traefik/routes/{id}
  Description: Update existing route
  Request Body: Same as POST
  Response: Same as POST

DELETE /api/v1/traefik/routes/{id}
  Description: Delete route
  Query Parameters:
    - force: boolean (skip conflict checks)
  Response:
    {
      "success": true,
      "message": "Route deleted successfully",
      "snapshot_id": "uuid"  # Rollback snapshot created
    }

POST /api/v1/traefik/routes/{id}/enable
  Description: Enable disabled route
  Response: {"success": true, "message": "Route enabled"}

POST /api/v1/traefik/routes/{id}/disable
  Description: Disable active route
  Response: {"success": true, "message": "Route disabled"}

POST /api/v1/traefik/routes/validate
  Description: Validate route configuration without applying
  Request Body: Same as POST /routes
  Response:
    {
      "valid": true,
      "warnings": [
        "Priority 0 conflicts with route 'existing-route'"
      ],
      "errors": [],
      "conflicts": [
        {
          "route_id": "uuid",
          "route_name": "existing-route",
          "conflict_type": "priority_conflict",
          "severity": "warning",
          "description": "Both routes have priority 0 and may conflict"
        }
      ]
    }
```

#### Services Management

```yaml
GET /api/v1/traefik/services
  Description: List all backend services
  Query Parameters: Same as routes
  Response: Similar structure to routes

GET /api/v1/traefik/services/{id}
  Description: Get service details with health status
  Response:
    {
      "id": "uuid",
      "name": "ops-center",
      "type": "loadbalancer",
      "servers": [
        {
          "url": "http://ops-center-direct:8000",
          "weight": 1,
          "health": {
            "status": "healthy",
            "last_check": "2025-10-23T12:00:00Z",
            "response_time_ms": 12.5,
            "consecutive_failures": 0
          }
        }
      ],
      "pass_host_header": true,
      "health_check": {
        "path": "/health",
        "interval": "30s",
        "timeout": "5s"
      },
      "sticky_sessions": null,
      "circuit_breaker": null,
      "status": "active",
      "routes_using": 3,  # Number of routes using this service
      "metrics": {
        "requests_total": 45678,
        "error_rate": 0.01
      }
    }

POST /api/v1/traefik/services
  Description: Create new service
  Request Body:
    {
      "name": "my-backend",
      "type": "loadbalancer",
      "servers": [
        {"url": "http://backend1:8000", "weight": 2},
        {"url": "http://backend2:8000", "weight": 1}
      ],
      "health_check": {
        "path": "/health",
        "interval": "30s",
        "timeout": "5s",
        "follow_redirects": true
      },
      "sticky_sessions": {
        "cookie": {
          "name": "lb_session",
          "secure": true,
          "http_only": true
        }
      }
    }

PUT /api/v1/traefik/services/{id}
  Description: Update service
  Request Body: Same as POST

DELETE /api/v1/traefik/services/{id}
  Description: Delete service (fails if routes using it)
  Query Parameters:
    - cascade: boolean (also delete routes using this service)
```

#### Middleware Management

```yaml
GET /api/v1/traefik/middleware
  Description: List all middleware
  Response:
    {
      "total": 15,
      "middleware": [
        {
          "id": "uuid",
          "name": "security-headers",
          "type": "headers",
          "usage_count": 12,
          "status": "active",
          "created_at": "2025-10-23T12:00:00Z"
        }
      ]
    }

GET /api/v1/traefik/middleware/{id}
  Description: Get middleware details
  Response:
    {
      "id": "uuid",
      "name": "security-headers",
      "type": "headers",
      "config": {
        "stsSeconds": 31536000,
        "stsIncludeSubdomains": true,
        "frameDeny": true,
        "contentTypeNosniff": true
      },
      "usage_count": 12,
      "routes_using": [
        {"id": "uuid", "name": "unicorncommander-ai"},
        {"id": "uuid", "name": "chat-unicorncommander"}
      ]
    }

POST /api/v1/traefik/middleware
  Description: Create new middleware
  Request Body:
    {
      "name": "api-rate-limit",
      "type": "rateLimit",
      "config": {
        "average": 100,
        "burst": 50,
        "period": "1m"
      },
      "description": "Rate limit for public API endpoints"
    }

PUT /api/v1/traefik/middleware/{id}
  Description: Update middleware
  Request Body: Same as POST

DELETE /api/v1/traefik/middleware/{id}
  Description: Delete middleware (fails if in use)
  Query Parameters:
    - force: boolean (remove from routes and delete)
```

#### SSL Certificates

```yaml
GET /api/v1/traefik/certificates
  Description: List all SSL certificates
  Query Parameters:
    - status: string (pending, valid, expiring, expired, error)
    - expiring_days: integer (filter certs expiring within N days)
  Response:
    {
      "total": 8,
      "certificates": [
        {
          "id": "uuid",
          "domain": "unicorncommander.ai",
          "type": "acme",
          "resolver": "letsencrypt",
          "status": "valid",
          "issued_at": "2025-09-23T00:00:00Z",
          "expires_at": "2025-12-22T00:00:00Z",
          "days_until_expiry": 60,
          "auto_renew": true,
          "last_renewal_attempt": null
        }
      ]
    }

GET /api/v1/traefik/certificates/{id}
  Description: Get certificate details
  Response:
    {
      "id": "uuid",
      "domain": "unicorncommander.ai",
      "type": "acme",
      "resolver": "letsencrypt",
      "status": "valid",
      "issued_at": "2025-09-23T00:00:00Z",
      "expires_at": "2025-12-22T00:00:00Z",
      "days_until_expiry": 60,
      "auto_renew": true,
      "renewal_attempts": 0,
      "routes_using": [
        {"id": "uuid", "name": "unicorncommander-ai"}
      ],
      "certificate_info": {
        "subject": "CN=unicorncommander.ai",
        "issuer": "C=US, O=Let's Encrypt, CN=R10",
        "serial_number": "...",
        "signature_algorithm": "SHA256-RSA"
      }
    }

POST /api/v1/traefik/certificates/{id}/renew
  Description: Force certificate renewal
  Response:
    {
      "success": true,
      "message": "Renewal initiated",
      "status": "pending"
    }

POST /api/v1/traefik/certificates/check-renewals
  Description: Check all certificates and renew expiring ones
  Response:
    {
      "checked": 8,
      "renewed": 2,
      "failed": 0,
      "results": [
        {
          "domain": "unicorncommander.ai",
          "action": "renewed",
          "success": true
        }
      ]
    }
```

#### Health & Metrics

```yaml
GET /api/v1/traefik/health
  Description: Traefik health status
  Response:
    {
      "status": "healthy",
      "version": "3.0.0",
      "uptime_seconds": 3456789,
      "routes_active": 15,
      "services_active": 10,
      "middleware_active": 8,
      "certificates_valid": 7,
      "certificates_expiring": 1,
      "last_config_reload": "2025-10-23T12:00:00Z",
      "config_reload_success": true
    }

GET /api/v1/traefik/metrics
  Description: Traffic metrics
  Query Parameters:
    - timeframe: string (1h, 6h, 24h, 7d, 30d) (default 24h)
    - route_id: uuid (filter by route)
  Response:
    {
      "timeframe": "24h",
      "total_requests": 123456,
      "total_errors": 234,
      "error_rate": 0.0019,
      "avg_latency_ms": 45.3,
      "routes": [
        {
          "route_id": "uuid",
          "route_name": "unicorncommander-ai",
          "requests": 45678,
          "errors": 123,
          "error_rate": 0.0027,
          "avg_latency_ms": 42.1,
          "status_codes": {
            "2xx": 45234,
            "3xx": 321,
            "4xx": 98,
            "5xx": 25
          }
        }
      ]
    }

GET /api/v1/traefik/logs
  Description: Access logs
  Query Parameters:
    - route_id: uuid
    - level: string (info, warn, error)
    - limit: integer (default 100, max 1000)
    - offset: integer
  Response:
    {
      "total": 1234,
      "logs": [
        {
          "timestamp": "2025-10-23T12:00:00Z",
          "level": "info",
          "route": "unicorncommander-ai",
          "method": "GET",
          "path": "/api/v1/health",
          "status": 200,
          "latency_ms": 12.5,
          "ip": "1.2.3.4",
          "user_agent": "Mozilla/5.0..."
        }
      ]
    }
```

#### Configuration Management

```yaml
GET /api/v1/traefik/config/current
  Description: Get current full configuration
  Response:
    {
      "routes": [...],
      "services": [...],
      "middleware": [...],
      "certificates": [...],
      "generated_at": "2025-10-23T12:00:00Z"
    }

POST /api/v1/traefik/config/apply
  Description: Apply pending changes to Traefik
  Response:
    {
      "success": true,
      "changes_applied": 3,
      "snapshot_id": "uuid",
      "message": "Configuration applied successfully"
    }

GET /api/v1/traefik/config/snapshots
  Description: List configuration snapshots
  Response:
    {
      "snapshots": [
        {
          "id": "uuid",
          "snapshot_name": "Before adding my-service",
          "description": "Automatic snapshot",
          "is_automatic": true,
          "created_at": "2025-10-23T12:00:00Z",
          "created_by": "admin@example.com"
        }
      ]
    }

POST /api/v1/traefik/config/snapshots
  Description: Create manual snapshot
  Request Body:
    {
      "snapshot_name": "Production Config 2025-10-23",
      "description": "Before major update"
    }

POST /api/v1/traefik/config/rollback/{snapshot_id}
  Description: Rollback to snapshot
  Response:
    {
      "success": true,
      "message": "Rolled back to snapshot",
      "new_snapshot_id": "uuid"  # Snapshot of state before rollback
    }

POST /api/v1/traefik/config/validate
  Description: Validate entire configuration
  Response:
    {
      "valid": true,
      "errors": [],
      "warnings": [
        "Certificate for domain 'example.com' expires in 10 days"
      ],
      "conflicts": []
    }

POST /api/v1/traefik/config/import
  Description: Import configuration from file
  Request: multipart/form-data with YAML file
  Response:
    {
      "success": true,
      "imported": {
        "routes": 5,
        "services": 3,
        "middleware": 2
      },
      "errors": []
    }

GET /api/v1/traefik/config/export
  Description: Export configuration as YAML
  Response: application/x-yaml file download
```

#### Service Discovery

```yaml
GET /api/v1/traefik/discovery/docker
  Description: List Docker containers with Traefik labels
  Response:
    {
      "containers": [
        {
          "container_id": "abc123",
          "name": "ops-center-direct",
          "image": "ops-center:latest",
          "status": "running",
          "traefik_enabled": true,
          "labels": {
            "traefik.enable": "true",
            "traefik.http.routers.ops-center.rule": "Host(`unicorncommander.ai`)",
            "traefik.http.services.ops-center.loadbalancer.server.port": "8000"
          },
          "managed_by_ops_center": true,
          "route_id": "uuid"
        }
      ]
    }

POST /api/v1/traefik/discovery/sync
  Description: Sync Docker containers to ops-center routes
  Response:
    {
      "success": true,
      "synced": 5,
      "created": 2,
      "updated": 3,
      "unchanged": 0
    }
```

---

## Data Models

### Route Model

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class TLSConfig(BaseModel):
    enabled: bool = True
    cert_resolver: str = "letsencrypt"
    domains: Optional[List[str]] = None

class RouteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, regex=r'^[a-z0-9-]+$')
    rule: str = Field(..., min_length=1)
    service_id: Optional[UUID] = None
    service: Optional['ServiceCreate'] = None  # Inline service creation
    priority: int = Field(default=0, ge=0)
    entrypoints: List[str] = Field(default=["http", "https"])
    tls: Optional[TLSConfig] = TLSConfig()
    middlewares: List[str] = Field(default=[])
    metadata: Dict[str, Any] = Field(default={})

    @validator('rule')
    def validate_rule(cls, v):
        # Validate Traefik rule syntax
        # Must contain Host() or PathPrefix() or other valid matchers
        if not any(matcher in v for matcher in ['Host(', 'PathPrefix(', 'Path(', 'Method(')):
            raise ValueError('Rule must contain valid Traefik matcher (Host, PathPrefix, etc.)')
        return v

    @validator('middlewares')
    def validate_middleware(cls, v):
        # Validate middleware names exist
        # This would check against database in actual implementation
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "my-service",
                "rule": "Host(`my-service.unicorncommander.ai`)",
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "priority": 0,
                "entrypoints": ["https"],
                "tls": {"enabled": True, "cert_resolver": "letsencrypt"},
                "middlewares": ["security-headers", "rate-limit"],
                "metadata": {"owner": "team-platform"}
            }
        }

class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, regex=r'^[a-z0-9-]+$')
    rule: Optional[str] = None
    service_id: Optional[UUID] = None
    priority: Optional[int] = None
    entrypoints: Optional[List[str]] = None
    tls: Optional[TLSConfig] = None
    middlewares: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class RouteResponse(BaseModel):
    id: UUID
    name: str
    rule: str
    service_id: UUID
    service_name: str
    priority: int
    entrypoints: List[str]
    tls: TLSConfig
    middlewares: List[str]
    status: str  # active, disabled, pending, error
    source: str  # manual, docker, imported
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    updated_by: Optional[str]
```

### Service Model

```python
class ServerConfig(BaseModel):
    url: str = Field(..., regex=r'^https?://.+')
    weight: int = Field(default=1, ge=1, le=100)

class HealthCheckConfig(BaseModel):
    path: str = "/health"
    interval: str = "30s"
    timeout: str = "5s"
    follow_redirects: bool = True
    headers: Optional[Dict[str, str]] = None

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, regex=r'^[a-z0-9-]+$')
    type: str = Field(default="loadbalancer", regex=r'^(loadbalancer|weighted|mirroring)$')
    servers: List[ServerConfig] = Field(..., min_items=1)
    pass_host_header: bool = True
    health_check: Optional[HealthCheckConfig] = None
    sticky_sessions: Optional[Dict[str, Any]] = None
    circuit_breaker: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default={})

class ServiceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    servers: List[ServerConfig]
    pass_host_header: bool
    health_check: Optional[HealthCheckConfig]
    status: str
    routes_using: int
    metrics: Optional[Dict[str, Any]]
    created_at: datetime
```

### Middleware Model

```python
class MiddlewareCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, regex=r'^[a-z0-9-]+$')
    type: str = Field(..., regex=r'^(rateLimit|headers|basicAuth|forwardAuth|stripPrefix|compress|redirect|ipWhiteList)$')
    config: Dict[str, Any] = Field(...)
    description: Optional[str] = None

    @validator('config')
    def validate_config(cls, v, values):
        # Validate config based on middleware type
        middleware_type = values.get('type')
        if middleware_type == 'rateLimit':
            required_fields = ['average', 'burst', 'period']
            if not all(field in v for field in required_fields):
                raise ValueError(f'rateLimit middleware requires: {required_fields}')
        elif middleware_type == 'headers':
            # Validate headers config
            pass
        # Add more type-specific validation
        return v

class MiddlewareResponse(BaseModel):
    id: UUID
    name: str
    type: str
    config: Dict[str, Any]
    description: Optional[str]
    usage_count: int
    status: str
    created_at: datetime
```

### Certificate Model

```python
class CertificateResponse(BaseModel):
    id: UUID
    domain: str
    type: str  # acme, manual, wildcard
    resolver: str
    status: str  # pending, valid, expiring, expired, error
    issued_at: Optional[datetime]
    expires_at: Optional[datetime]
    days_until_expiry: Optional[int]
    auto_renew: bool = True
    last_renewal_attempt: Optional[datetime]
    renewal_attempts: int = 0
    routes_using: List[Dict[str, str]]
```

### Validation Models

```python
class ValidationWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"  # info, warning, error, critical

class ConflictInfo(BaseModel):
    route_id: UUID
    route_name: str
    conflict_type: str
    severity: str
    description: str

class ValidationResponse(BaseModel):
    valid: bool
    warnings: List[ValidationWarning] = []
    errors: List[ValidationWarning] = []
    conflicts: List[ConflictInfo] = []
```

---

## Traefik Integration Strategy

### Configuration File Generation

#### YAML Structure

```yaml
# /home/deploy/Infrastructure/traefik/dynamic/ops-center-routes.yml

# This file is AUTO-GENERATED by Ops-Center
# DO NOT EDIT MANUALLY - Changes will be overwritten
# Last updated: 2025-10-23 12:00:00 UTC
# Snapshot ID: 550e8400-e29b-41d4-a716-446655440000

http:
  routers:
    # Route: unicorncommander-ai
    # Created: 2025-10-23 by admin@example.com
    # Status: active
    unicorncommander-ai:
      rule: "Host(`unicorncommander.ai`) || Host(`www.unicorncommander.ai`)"
      service: ops-center-service
      entryPoints:
        - https
      tls:
        certResolver: letsencrypt
      middlewares:
        - security-headers@file
        - compress@file
      priority: 0
```

#### File Writing Strategy

```python
class TraefikConfigWriter:
    """Writes Traefik configuration files with atomic operations"""

    def __init__(self, config_dir: str = "/home/deploy/Infrastructure/traefik/dynamic"):
        self.config_dir = Path(config_dir)
        self.lock_file = self.config_dir / ".ops-center.lock"

    async def write_config(self, config_data: dict, snapshot_id: str) -> bool:
        """
        Atomically write configuration to file

        1. Acquire file lock
        2. Create backup of existing config
        3. Write to temporary file
        4. Validate YAML syntax
        5. Atomic rename (temp -> actual)
        6. Wait for Traefik to reload
        7. Verify Traefik health
        8. Release lock
        """
        async with self._file_lock():
            try:
                # Step 1: Backup existing config
                backup_path = await self._backup_current_config()

                # Step 2: Generate YAML content
                yaml_content = self._generate_yaml(config_data, snapshot_id)

                # Step 3: Write to temp file
                temp_file = self.config_dir / f".ops-center-routes.yml.tmp"
                async with aiofiles.open(temp_file, 'w') as f:
                    await f.write(yaml_content)

                # Step 4: Validate YAML syntax
                await self._validate_yaml_syntax(temp_file)

                # Step 5: Atomic rename
                target_file = self.config_dir / "ops-center-routes.yml"
                temp_file.rename(target_file)

                # Step 6: Wait for Traefik to detect change (inotify)
                await asyncio.sleep(2)

                # Step 7: Verify Traefik health
                if not await self._verify_traefik_health():
                    # Rollback to backup
                    await self._rollback_config(backup_path)
                    return False

                return True

            except Exception as e:
                logger.error(f"Failed to write config: {e}")
                if backup_path:
                    await self._rollback_config(backup_path)
                return False

    def _generate_yaml(self, config_data: dict, snapshot_id: str) -> str:
        """Generate YAML with comments and metadata"""
        header = f"""# This file is AUTO-GENERATED by Ops-Center
# DO NOT EDIT MANUALLY - Changes will be overwritten
# Last updated: {datetime.utcnow().isoformat()} UTC
# Snapshot ID: {snapshot_id}

"""
        yaml_content = yaml.dump(config_data, default_flow_style=False, sort_keys=False)
        return header + yaml_content

    async def _backup_current_config(self) -> Path:
        """Create timestamped backup of current config"""
        source = self.config_dir / "ops-center-routes.yml"
        if not source.exists():
            return None

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        backup = self.config_dir / f"ops-center-routes.yml.backup.{timestamp}"
        shutil.copy2(source, backup)
        return backup

    async def _validate_yaml_syntax(self, file_path: Path) -> bool:
        """Validate YAML is parseable"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                yaml.safe_load(content)
            return True
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")

    async def _verify_traefik_health(self) -> bool:
        """Check if Traefik successfully loaded new config"""
        try:
            async with httpx.AsyncClient() as client:
                # Check Traefik API health endpoint
                response = await client.get("http://traefik:8080/ping", timeout=5)
                return response.status_code == 200
        except Exception:
            return False

    async def _rollback_config(self, backup_path: Path):
        """Restore configuration from backup"""
        target = self.config_dir / "ops-center-routes.yml"
        shutil.copy2(backup_path, target)
        logger.warning(f"Rolled back configuration from {backup_path}")

    @asynccontextmanager
    async def _file_lock(self):
        """Acquire file lock to prevent concurrent writes"""
        import fcntl
        lock_file = open(self.lock_file, 'w')
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
```

### Conflict Detection Engine

```python
class ConflictDetector:
    """Detects conflicts between routes"""

    async def detect_conflicts(self, new_route: RouteCreate, existing_routes: List[RouteResponse]) -> List[ConflictInfo]:
        """
        Detect conflicts with existing routes

        Conflict Types:
        1. Duplicate Host: Exact same Host() matcher
        2. Priority Conflict: Same host + same priority
        3. Regex Overlap: Similar regex patterns
        4. Middleware Chain: Incompatible middleware order
        """
        conflicts = []

        # Parse new route rule
        new_hosts = self._extract_hosts(new_route.rule)
        new_paths = self._extract_paths(new_route.rule)

        for existing in existing_routes:
            if existing.status != 'active':
                continue

            existing_hosts = self._extract_hosts(existing.rule)
            existing_paths = self._extract_paths(existing.rule)

            # Check for duplicate hosts
            common_hosts = set(new_hosts) & set(existing_hosts)
            if common_hosts:
                # Same host detected
                if new_route.priority == existing.priority:
                    conflicts.append(ConflictInfo(
                        route_id=existing.id,
                        route_name=existing.name,
                        conflict_type="priority_conflict",
                        severity="error",
                        description=f"Routes share host {common_hosts} with same priority {new_route.priority}"
                    ))

                # Check path overlap
                if self._paths_overlap(new_paths, existing_paths):
                    conflicts.append(ConflictInfo(
                        route_id=existing.id,
                        route_name=existing.name,
                        conflict_type="path_overlap",
                        severity="warning",
                        description=f"Routes share host and have overlapping paths"
                    ))

        return conflicts

    def _extract_hosts(self, rule: str) -> List[str]:
        """Extract host patterns from rule"""
        import re
        # Match Host(`example.com`) or Host(`example.com`, `www.example.com`)
        pattern = r"Host\(`([^`]+)`\)"
        matches = re.findall(pattern, rule)
        return matches

    def _extract_paths(self, rule: str) -> List[str]:
        """Extract path patterns from rule"""
        import re
        pattern = r"PathPrefix\(`([^`]+)`\)"
        matches = re.findall(pattern, rule)
        return matches if matches else ["/"]  # Default to root

    def _paths_overlap(self, paths1: List[str], paths2: List[str]) -> bool:
        """Check if path lists have overlap"""
        for p1 in paths1:
            for p2 in paths2:
                if p1.startswith(p2) or p2.startswith(p1):
                    return True
        return False
```

### Service Discovery

```python
class ServiceDiscovery:
    """Discovers services from Docker API"""

    def __init__(self):
        self.docker_client = docker.from_env()

    async def discover_docker_services(self) -> List[dict]:
        """
        Scan Docker containers for Traefik labels

        Returns list of services that should be managed by Traefik
        """
        discovered = []

        for container in self.docker_client.containers.list():
            labels = container.labels

            # Check if Traefik enabled
            if labels.get('traefik.enable') != 'true':
                continue

            # Extract Traefik configuration from labels
            service_info = {
                'container_id': container.id,
                'container_name': container.name,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'status': container.status,
                'traefik_labels': self._extract_traefik_labels(labels),
                'networks': list(container.attrs['NetworkSettings']['Networks'].keys())
            }

            discovered.append(service_info)

        return discovered

    def _extract_traefik_labels(self, labels: dict) -> dict:
        """Extract Traefik-specific labels"""
        traefik_labels = {}
        for key, value in labels.items():
            if key.startswith('traefik.'):
                traefik_labels[key] = value
        return traefik_labels

    async def sync_to_database(self, discovered_services: List[dict]):
        """
        Sync discovered services to PostgreSQL

        - Create routes for new containers
        - Update existing routes
        - Mark removed containers
        """
        for service in discovered_services:
            # Check if route exists
            existing_route = await self._find_route_by_container(service['container_id'])

            if existing_route:
                # Update if changed
                await self._update_route_from_labels(existing_route, service)
            else:
                # Create new route
                await self._create_route_from_labels(service)
```

---

## Frontend Architecture

### Component Hierarchy

```
TraefikManagement (Page)
├── RoutesDashboard
│   ├── RoutesList
│   │   ├── RouteCard
│   │   ├── RouteFilters
│   │   └── RouteActions
│   ├── RouteEditor (Modal)
│   │   ├── RouteForm
│   │   ├── ServiceSelector
│   │   ├── MiddlewareBuilder
│   │   └── TLSConfig
│   ├── ConflictWarnings
│   └── QuickActions
├── ServicesDashboard
│   ├── ServicesList
│   ├── ServiceEditor (Modal)
│   └── HealthMonitor
├── MiddlewareDashboard
│   ├── MiddlewareList
│   ├── MiddlewareEditor (Modal)
│   └── MiddlewareTemplates
├── SSLDashboard
│   ├── CertificatesList
│   ├── CertificateDetails (Modal)
│   └── RenewalSchedule
├── TrafficMonitor
│   ├── RequestsChart
│   ├── LatencyChart
│   ├── ErrorRateChart
│   └── RouteMetricsTable
└── ConfigManagement
    ├── SnapshotsList
    ├── ImportExport
    └── RollbackConfirmation
```

### Key UI Components

#### RoutesDashboard.jsx

```jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  MenuItem,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as EnableIcon,
  Stop as DisableIcon,
  Search as SearchIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';

export default function RoutesDashboard() {
  const [routes, setRoutes] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    source: 'all'
  });
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [conflicts, setConflicts] = useState([]);

  useEffect(() => {
    loadRoutes();
  }, [filters]);

  const loadRoutes = async () => {
    const params = new URLSearchParams({
      search: filters.search,
      status: filters.status !== 'all' ? filters.status : '',
      source: filters.source !== 'all' ? filters.source : ''
    });

    const response = await fetch(`/api/v1/traefik/routes?${params}`);
    const data = await response.json();
    setRoutes(data.routes);
  };

  const handleCreateRoute = () => {
    setSelectedRoute(null);
    setEditorOpen(true);
  };

  const handleEditRoute = (route) => {
    setSelectedRoute(route);
    setEditorOpen(true);
  };

  const handleDeleteRoute = async (routeId) => {
    if (!confirm('Are you sure you want to delete this route?')) return;

    await fetch(`/api/v1/traefik/routes/${routeId}`, {
      method: 'DELETE'
    });

    loadRoutes();
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      disabled: 'default',
      pending: 'warning',
      error: 'error'
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Traefik Routes</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateRoute}
        >
          Create Route
        </Button>
      </Box>

      {/* Conflicts Alert */}
      {conflicts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {conflicts.length} route conflict{conflicts.length > 1 ? 's' : ''} detected
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search"
                placeholder="Search by name, domain, or rule..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Status"
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="disabled">Disabled</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Source"
                value={filters.source}
                onChange={(e) => setFilters({...filters, source: e.target.value})}
              >
                <MenuItem value="all">All Sources</MenuItem>
                <MenuItem value="manual">Manual</MenuItem>
                <MenuItem value="docker">Docker</MenuItem>
                <MenuItem value="imported">Imported</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Routes Table */}
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Rule</TableCell>
              <TableCell>Service</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Requests/min</TableCell>
              <TableCell>Error Rate</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {routes.map((route) => (
              <TableRow key={route.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {route.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {route.source}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {route.rule}
                  </Typography>
                </TableCell>
                <TableCell>{route.service_name}</TableCell>
                <TableCell>
                  <Chip
                    label={route.status}
                    color={getStatusColor(route.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{route.metrics?.requests_per_minute.toFixed(1)}</TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={route.metrics?.error_rate > 0.05 ? 'error' : 'text.primary'}
                  >
                    {(route.metrics?.error_rate * 100).toFixed(2)}%
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEditRoute(route)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDeleteRoute(route.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Route Editor Modal */}
      <RouteEditor
        open={editorOpen}
        route={selectedRoute}
        onClose={() => setEditorOpen(false)}
        onSave={() => {
          setEditorOpen(false);
          loadRoutes();
        }}
      />
    </Box>
  );
}
```

#### RouteEditor.jsx

```jsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControlLabel,
  Switch,
  Chip,
  Autocomplete,
  Alert,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';

export default function RouteEditor({ open, route, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    rule: '',
    service_id: null,
    priority: 0,
    entrypoints: ['https'],
    tls: { enabled: true, cert_resolver: 'letsencrypt' },
    middlewares: []
  });

  const [services, setServices] = useState([]);
  const [middlewareList, setMiddlewareList] = useState([]);
  const [validation, setValidation] = useState(null);
  const [activeStep, setActiveStep] = useState(0);

  const steps = ['Basic Info', 'Service', 'Middleware', 'Review'];

  useEffect(() => {
    if (route) {
      setFormData({
        name: route.name,
        rule: route.rule,
        service_id: route.service_id,
        priority: route.priority,
        entrypoints: route.entrypoints,
        tls: route.tls,
        middlewares: route.middlewares
      });
    }
    loadServices();
    loadMiddleware();
  }, [route]);

  const loadServices = async () => {
    const response = await fetch('/api/v1/traefik/services');
    const data = await response.json();
    setServices(data.services || []);
  };

  const loadMiddleware = async () => {
    const response = await fetch('/api/v1/traefik/middleware');
    const data = await response.json();
    setMiddlewareList(data.middleware || []);
  };

  const validateRoute = async () => {
    const response = await fetch('/api/v1/traefik/routes/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    const data = await response.json();
    setValidation(data);
    return data.valid;
  };

  const handleNext = async () => {
    if (activeStep === steps.length - 2) {
      // Validate before moving to review
      await validateRoute();
    }
    setActiveStep(activeStep + 1);
  };

  const handleSave = async () => {
    const method = route ? 'PUT' : 'POST';
    const url = route
      ? `/api/v1/traefik/routes/${route.id}`
      : '/api/v1/traefik/routes';

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });

    if (response.ok) {
      onSave();
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Route Name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                helperText="Lowercase alphanumeric and hyphens only"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Rule"
                value={formData.rule}
                onChange={(e) => setFormData({...formData, rule: e.target.value})}
                helperText="Example: Host(`example.com`) && PathPrefix(`/api`)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Priority"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
                helperText="Higher priority routes are evaluated first"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Autocomplete
                multiple
                options={['http', 'https']}
                value={formData.entrypoints}
                onChange={(e, value) => setFormData({...formData, entrypoints: value})}
                renderInput={(params) => (
                  <TextField {...params} label="Entry Points" />
                )}
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Autocomplete
                options={services}
                getOptionLabel={(option) => option.name}
                value={services.find(s => s.id === formData.service_id) || null}
                onChange={(e, value) => setFormData({...formData, service_id: value?.id})}
                renderInput={(params) => (
                  <TextField {...params} label="Backend Service" />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.tls.enabled}
                    onChange={(e) => setFormData({
                      ...formData,
                      tls: {...formData.tls, enabled: e.target.checked}
                    })}
                  />
                }
                label="Enable TLS/SSL"
              />
            </Grid>
            {formData.tls.enabled && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Certificate Resolver"
                  value={formData.tls.cert_resolver}
                  onChange={(e) => setFormData({
                    ...formData,
                    tls: {...formData.tls, cert_resolver: e.target.value}
                  })}
                />
              </Grid>
            )}
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                options={middlewareList.map(m => m.name)}
                value={formData.middlewares}
                onChange={(e, value) => setFormData({...formData, middlewares: value})}
                renderInput={(params) => (
                  <TextField {...params} label="Middleware" helperText="Applied in order" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip label={option} {...getTagProps({ index })} />
                  ))
                }
              />
            </Grid>
          </Grid>
        );

      case 3:
        return (
          <Box>
            {/* Validation Results */}
            {validation && (
              <>
                {validation.errors.length > 0 && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    <Typography variant="subtitle2">Errors:</Typography>
                    <ul>
                      {validation.errors.map((err, idx) => (
                        <li key={idx}>{err.message}</li>
                      ))}
                    </ul>
                  </Alert>
                )}

                {validation.warnings.length > 0 && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="subtitle2">Warnings:</Typography>
                    <ul>
                      {validation.warnings.map((warn, idx) => (
                        <li key={idx}>{warn.message}</li>
                      ))}
                    </ul>
                  </Alert>
                )}

                {validation.conflicts.length > 0 && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="subtitle2">Conflicts:</Typography>
                    <ul>
                      {validation.conflicts.map((conflict, idx) => (
                        <li key={idx}>
                          {conflict.route_name}: {conflict.description}
                        </li>
                      ))}
                    </ul>
                  </Alert>
                )}

                {validation.valid && (
                  <Alert severity="success">
                    Configuration is valid and ready to apply
                  </Alert>
                )}
              </>
            )}

            {/* Configuration Summary */}
            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>Configuration Summary</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Name:</Typography>
                <Typography variant="body1">{formData.name}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Rule:</Typography>
                <Typography variant="body1">{formData.rule}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Service:</Typography>
                <Typography variant="body1">
                  {services.find(s => s.id === formData.service_id)?.name || 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Middleware:</Typography>
                <Box>
                  {formData.middlewares.map(m => (
                    <Chip key={m} label={m} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {route ? 'Edit Route' : 'Create Route'}
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 2 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent(activeStep)}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={() => setActiveStep(activeStep - 1)}
          disabled={activeStep === 0}
        >
          Back
        </Button>
        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext}>
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={validation && !validation.valid}
          >
            Save Route
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
```

#### SSLDashboard.jsx

```jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  Button,
  Grid,
  Alert
} from '@mui/material';
import { Refresh as RefreshIcon, Warning as WarningIcon } from '@mui/icons-material';

export default function SSLDashboard() {
  const [certificates, setCertificates] = useState([]);
  const [expiringCerts, setExpiringCerts] = useState([]);

  useEffect(() => {
    loadCertificates();
  }, []);

  const loadCertificates = async () => {
    const response = await fetch('/api/v1/traefik/certificates');
    const data = await response.json();
    setCertificates(data.certificates);

    // Filter expiring certificates (< 30 days)
    const expiring = data.certificates.filter(cert =>
      cert.days_until_expiry !== null && cert.days_until_expiry < 30
    );
    setExpiringCerts(expiring);
  };

  const handleRenew = async (certId) => {
    await fetch(`/api/v1/traefik/certificates/${certId}/renew`, {
      method: 'POST'
    });
    loadCertificates();
  };

  const handleCheckRenewals = async () => {
    await fetch('/api/v1/traefik/certificates/check-renewals', {
      method: 'POST'
    });
    loadCertificates();
  };

  const getCertStatusColor = (status) => {
    const colors = {
      valid: 'success',
      expiring: 'warning',
      expired: 'error',
      pending: 'info',
      error: 'error'
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">SSL Certificates</Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={handleCheckRenewals}
        >
          Check Renewals
        </Button>
      </Box>

      {expiringCerts.length > 0 && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
          {expiringCerts.length} certificate{expiringCerts.length > 1 ? 's' : ''} expiring in the next 30 days
        </Alert>
      )}

      <Grid container spacing={3}>
        {certificates.map((cert) => (
          <Grid item xs={12} md={6} lg={4} key={cert.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Typography variant="h6" sx={{ wordBreak: 'break-all' }}>
                    {cert.domain}
                  </Typography>
                  <Chip
                    label={cert.status}
                    color={getCertStatusColor(cert.status)}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Issued: {new Date(cert.issued_at).toLocaleDateString()}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Expires: {new Date(cert.expires_at).toLocaleDateString()}
                </Typography>

                {cert.days_until_expiry !== null && (
                  <>
                    <Box mt={2} mb={1}>
                      <Typography variant="caption" color="text.secondary">
                        Days until expiry: {cert.days_until_expiry}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.max(0, (cert.days_until_expiry / 90) * 100)}
                      color={cert.days_until_expiry < 30 ? 'warning' : 'success'}
                    />
                  </>
                )}

                {cert.status === 'expiring' && (
                  <Button
                    fullWidth
                    variant="outlined"
                    size="small"
                    sx={{ mt: 2 }}
                    onClick={() => handleRenew(cert.id)}
                  >
                    Renew Now
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

---

## Security Architecture

### Authentication & Authorization

**Access Control**:
- **Admin-only feature**: Only users with `admin` or `moderator` role can access
- **Audit logging**: All changes logged with user identity
- **Two-factor confirmation**: Critical operations require confirmation
- **Session validation**: JWT tokens validated on every request

**API Security**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require admin or moderator role"""
    # Validate JWT token
    token = credentials.credentials
    payload = decode_jwt(token)

    # Check user role
    user_role = payload.get('role')
    if user_role not in ['admin', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator role required"
        )

    return payload

# Apply to all Traefik endpoints
@app.get("/api/v1/traefik/routes", dependencies=[Depends(require_admin)])
async def list_routes():
    ...
```

### Input Validation

**Route Rule Validation**:
```python
import re

def validate_traefik_rule(rule: str) -> bool:
    """
    Validate Traefik rule syntax

    Valid matchers:
    - Host(`example.com`)
    - PathPrefix(`/api`)
    - Path(`/exact`)
    - Method(`GET`, `POST`)
    - Headers(`X-Custom`, `value`)
    - Query(`param`, `value`)

    Operators: &&, ||, !
    """
    # Check for basic syntax
    if not rule.strip():
        raise ValueError("Rule cannot be empty")

    # Check for valid matchers
    valid_matchers = [
        r'Host\([^)]+\)',
        r'PathPrefix\([^)]+\)',
        r'Path\([^)]+\)',
        r'Method\([^)]+\)',
        r'Headers\([^)]+\)',
        r'Query\([^)]+\)'
    ]

    # Remove valid matchers and operators
    cleaned = rule
    for matcher in valid_matchers:
        cleaned = re.sub(matcher, '', cleaned)
    cleaned = re.sub(r'\s*(&&|\|\||!)\s*', '', cleaned)
    cleaned = cleaned.strip()

    # If anything remains, it's invalid
    if cleaned:
        raise ValueError(f"Invalid rule syntax: {rule}")

    return True
```

**SQL Injection Prevention**:
- Use parameterized queries (SQLAlchemy ORM)
- Validate all UUIDs
- Escape user input in YAML comments

**Path Traversal Prevention**:
```python
def safe_file_path(base_dir: Path, user_input: str) -> Path:
    """Prevent path traversal attacks"""
    # Resolve absolute path
    requested_path = (base_dir / user_input).resolve()

    # Ensure it's within base directory
    if not requested_path.is_relative_to(base_dir):
        raise ValueError("Path traversal attempt detected")

    return requested_path
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply rate limits to write operations
@app.post("/api/v1/traefik/routes")
@limiter.limit("10/minute")  # Max 10 route creations per minute
async def create_route():
    ...

@app.delete("/api/v1/traefik/routes/{id}")
@limiter.limit("20/minute")  # Max 20 deletions per minute
async def delete_route():
    ...
```

### Audit Logging

```python
async def log_audit(
    entity_type: str,
    entity_id: UUID,
    action: str,
    changes: dict,
    user_id: str,
    ip_address: str,
    success: bool = True,
    error_message: str = None
):
    """Log all configuration changes"""
    async with get_db() as db:
        await db.execute("""
            INSERT INTO traefik_audit_log
            (entity_type, entity_id, entity_name, action, changes,
             user_id, user_email, ip_address, success, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, entity_type, entity_id, ..., success, error_message)
```

---

## High Availability & Resilience

### Automatic Snapshots

**Before every change**:
```python
async def create_automatic_snapshot(description: str) -> UUID:
    """Create snapshot before applying changes"""
    config = await get_current_config()
    yaml_content = await read_config_file()

    snapshot_id = uuid4()
    async with get_db() as db:
        await db.execute("""
            INSERT INTO traefik_config_snapshots
            (id, snapshot_name, description, config_data, file_content, is_automatic, created_by)
            VALUES ($1, $2, $3, $4, $5, true, $6)
        """, snapshot_id, f"Auto-snapshot {datetime.now()}", description,
            json.dumps(config), yaml_content, current_user.email)

    return snapshot_id
```

### Rollback Mechanism

```python
async def rollback_to_snapshot(snapshot_id: UUID, user: str) -> bool:
    """Rollback configuration to snapshot"""
    # 1. Create snapshot of current state (for undo)
    current_snapshot_id = await create_automatic_snapshot("Before rollback")

    # 2. Load snapshot
    async with get_db() as db:
        snapshot = await db.fetchrow("""
            SELECT file_content, config_data
            FROM traefik_config_snapshots
            WHERE id = $1
        """, snapshot_id)

    if not snapshot:
        raise ValueError("Snapshot not found")

    # 3. Write snapshot config to file
    success = await write_config_file(snapshot['file_content'])

    if not success:
        # Rollback failed, restore current state
        await rollback_to_snapshot(current_snapshot_id, user)
        return False

    # 4. Update database with snapshot config
    await restore_database_from_snapshot(snapshot['config_data'])

    # 5. Mark snapshot as restored
    async with get_db() as db:
        await db.execute("""
            UPDATE traefik_config_snapshots
            SET restored_at = NOW(), restored_by = $1
            WHERE id = $2
        """, user, snapshot_id)

    return True
```

### Health Monitoring

```python
import asyncio

class TraefikHealthMonitor:
    """Monitor Traefik health after config changes"""

    async def monitor_after_change(self, timeout: int = 30) -> bool:
        """
        Monitor Traefik health for specified timeout

        Returns True if Traefik remains healthy
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            health = await self.check_traefik_health()

            if not health['healthy']:
                logger.error(f"Traefik unhealthy: {health['error']}")
                return False

            # Check if routes are accessible
            routes_ok = await self.check_routes_accessible()
            if not routes_ok:
                logger.error("Routes not accessible after config change")
                return False

            await asyncio.sleep(5)

        return True

    async def check_traefik_health(self) -> dict:
        """Check Traefik API health endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://traefik:8080/ping", timeout=5)
                return {
                    'healthy': response.status_code == 200,
                    'status_code': response.status_code
                }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

    async def check_routes_accessible(self) -> bool:
        """Sample check: Verify critical routes are accessible"""
        critical_routes = [
            'https://unicorncommander.ai',
            'https://chat.unicorncommander.ai',
            'https://auth.unicorncommander.ai'
        ]

        async with httpx.AsyncClient() as client:
            for url in critical_routes:
                try:
                    response = await client.get(url, timeout=10, follow_redirects=True)
                    if response.status_code >= 500:
                        logger.warning(f"Route {url} returned {response.status_code}")
                        return False
                except Exception as e:
                    logger.error(f"Route {url} not accessible: {e}")
                    return False

        return True
```

### Graceful Degradation

**If Traefik is down**:
- UI shows "Traefik Unavailable" warning
- Read-only mode: View existing config, cannot apply changes
- Queue changes for later application

**If PostgreSQL is down**:
- Fallback to reading config from file system
- Cache recent data in Redis
- Cannot create/update routes (error shown)

**If Redis is down**:
- Direct database queries (slower)
- No caching (acceptable for admin operations)
- Validation may be slower

---

## SSL/TLS Management

### Let's Encrypt Integration

Traefik handles Let's Encrypt automatically. Ops-Center monitors certificate status.

#### Certificate Monitoring

```python
import json
from pathlib import Path

class CertificateMonitor:
    """Monitor Let's Encrypt certificates from acme.json"""

    def __init__(self, acme_file: str = "/home/deploy/Infrastructure/traefik/acme/acme.json"):
        self.acme_file = Path(acme_file)

    async def parse_acme_json(self) -> List[dict]:
        """Parse acme.json and extract certificate info"""
        if not self.acme_file.exists():
            return []

        with open(self.acme_file, 'r') as f:
            acme_data = json.load(f)

        certificates = []

        # Parse Let's Encrypt certificate data
        for resolver_name, resolver_data in acme_data.items():
            if 'Certificates' not in resolver_data:
                continue

            for cert in resolver_data['Certificates']:
                domain = cert['domain']['main']

                # Parse certificate to get expiration
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend

                cert_bytes = cert['certificate']
                x509_cert = x509.load_pem_x509_certificate(cert_bytes.encode(), default_backend())

                issued_at = x509_cert.not_valid_before
                expires_at = x509_cert.not_valid_after
                days_until_expiry = (expires_at - datetime.utcnow()).days

                certificates.append({
                    'domain': domain,
                    'resolver': resolver_name,
                    'issued_at': issued_at,
                    'expires_at': expires_at,
                    'days_until_expiry': days_until_expiry,
                    'status': self._determine_status(days_until_expiry)
                })

        return certificates

    def _determine_status(self, days_until_expiry: int) -> str:
        if days_until_expiry < 0:
            return 'expired'
        elif days_until_expiry < 30:
            return 'expiring'
        else:
            return 'valid'

    async def sync_to_database(self):
        """Sync certificate info to PostgreSQL"""
        certificates = await self.parse_acme_json()

        async with get_db() as db:
            for cert in certificates:
                await db.execute("""
                    INSERT INTO traefik_certificates
                    (domain, type, resolver, status, issued_at, expires_at, updated_at)
                    VALUES ($1, 'acme', $2, $3, $4, $5, NOW())
                    ON CONFLICT (domain) DO UPDATE SET
                        status = EXCLUDED.status,
                        issued_at = EXCLUDED.issued_at,
                        expires_at = EXCLUDED.expires_at,
                        updated_at = NOW()
                """, cert['domain'], cert['resolver'], cert['status'],
                    cert['issued_at'], cert['expires_at'])
```

#### Certificate Renewal Alerts

```python
async def check_expiring_certificates():
    """Background task: Check for expiring certificates"""
    async with get_db() as db:
        expiring = await db.fetch("""
            SELECT domain, expires_at, days_until_expiry
            FROM traefik_certificates
            WHERE status IN ('expiring', 'expired')
            AND type = 'acme'
        """)

    if expiring:
        # Send notification to admins
        for cert in expiring:
            await send_notification(
                type='certificate_expiring',
                severity='warning' if cert['status'] == 'expiring' else 'error',
                message=f"Certificate for {cert['domain']} expires in {cert['days_until_expiry']} days"
            )
```

### Manual Certificate Support

For certificates not managed by Let's Encrypt:

```python
async def upload_certificate(
    domain: str,
    cert_file: UploadFile,
    key_file: UploadFile,
    user: str
):
    """Upload manual SSL certificate"""
    # 1. Validate certificate files
    cert_data = await cert_file.read()
    key_data = await key_file.read()

    # Validate certificate is valid PEM format
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    try:
        x509_cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    except Exception as e:
        raise ValueError(f"Invalid certificate: {e}")

    # 2. Store certificate files
    cert_dir = Path("/home/deploy/Infrastructure/traefik/certs")
    cert_dir.mkdir(exist_ok=True)

    cert_path = cert_dir / f"{domain}.crt"
    key_path = cert_dir / f"{domain}.key"

    with open(cert_path, 'wb') as f:
        f.write(cert_data)

    with open(key_path, 'wb') as f:
        f.write(key_data)

    # 3. Update database
    issued_at = x509_cert.not_valid_before
    expires_at = x509_cert.not_valid_after

    async with get_db() as db:
        await db.execute("""
            INSERT INTO traefik_certificates
            (domain, type, status, issued_at, expires_at, created_by)
            VALUES ($1, 'manual', 'valid', $2, $3, $4)
        """, domain, issued_at, expires_at, user)

    # 4. Update Traefik config to use manual cert
    await update_route_tls(domain, cert_path, key_path)
```

---

## Deployment Strategy

### Phase 1: Backend API (Week 1-2)

**Goals**:
- Implement core API endpoints
- Set up PostgreSQL schema
- Implement config writer and validation

**Deliverables**:
- Routes CRUD endpoints functional
- Services CRUD endpoints functional
- Config file generation working
- Traefik hot-reload verified

**Testing**:
- Create route via API
- Verify YAML generated
- Verify Traefik picks up change
- Verify route accessible

### Phase 2: Basic Frontend (Week 2-3)

**Goals**:
- Routes dashboard UI
- Route editor with validation
- Service management UI

**Deliverables**:
- Routes list page
- Route creation/editing modal
- Services list page
- Basic service editor

**Testing**:
- Create route via UI
- Edit existing route
- Delete route
- Verify changes in Traefik

### Phase 3: Advanced Features (Week 3-4)

**Goals**:
- Middleware management
- SSL certificate monitoring
- Conflict detection
- Traffic metrics

**Deliverables**:
- Middleware CRUD UI
- SSL dashboard
- Conflict warnings
- Real-time metrics display

**Testing**:
- Create custom middleware
- Apply middleware to route
- View certificate expiration
- Monitor traffic metrics

### Phase 4: Config Management (Week 4-5)

**Goals**:
- Snapshot/rollback
- Import/export
- Audit logging
- Service discovery

**Deliverables**:
- Snapshot list UI
- Rollback functionality
- Import YAML wizard
- Docker container sync

**Testing**:
- Create manual snapshot
- Rollback to snapshot
- Import existing YAML
- Sync Docker containers

### Phase 5: Polish & Production (Week 5-6)

**Goals**:
- Performance optimization
- Documentation
- Error handling
- Production deployment

**Deliverables**:
- Comprehensive error messages
- User documentation
- API documentation
- Production deployment

**Testing**:
- Load testing
- Error scenario testing
- User acceptance testing

---

## Migration Plan

### Current State Analysis

**Existing Configuration Files**:
- `/home/deploy/Infrastructure/traefik/dynamic/domains.yml` - 15 routes
- `/home/deploy/Infrastructure/traefik/dynamic/middlewares.yml` - 8 middleware
- `/home/deploy/Infrastructure/traefik/dynamic/billing-routes.yml` - 5 routes
- `/home/deploy/Infrastructure/traefik/dynamic/api-domains.yml` - 8 routes

**Total**: ~36 routes, 10 services, 8 middleware

### Migration Steps

#### Step 1: Inventory Existing Config

```bash
# Run inventory script
python3 backend/scripts/traefik_inventory.py

# Output: JSON file with all existing routes, services, middleware
# /tmp/traefik_inventory_20251023.json
```

#### Step 2: Import to Database

```python
async def import_existing_config():
    """Import existing Traefik config to database"""
    # 1. Parse all YAML files
    config_dir = Path("/home/deploy/Infrastructure/traefik/dynamic")
    all_routes = []
    all_services = []
    all_middleware = []

    for yaml_file in config_dir.glob("*.yml"):
        if yaml_file.name.startswith("ops-center"):
            continue  # Skip our generated files

        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)

        # Extract routes
        if 'http' in data and 'routers' in data['http']:
            for name, config in data['http']['routers'].items():
                all_routes.append({
                    'name': name,
                    'rule': config.get('rule'),
                    'service': config.get('service'),
                    'priority': config.get('priority', 0),
                    'entrypoints': config.get('entryPoints', ['http', 'https']),
                    'tls': config.get('tls', {}),
                    'middlewares': config.get('middlewares', []),
                    'source_file': yaml_file.name
                })

        # Extract services
        if 'http' in data and 'services' in data['http']:
            for name, config in data['http']['services'].items():
                all_services.append({
                    'name': name,
                    'config': config,
                    'source_file': yaml_file.name
                })

        # Extract middleware
        if 'http' in data and 'middlewares' in data['http']:
            for name, config in data['http']['middlewares'].items():
                all_middleware.append({
                    'name': name,
                    'config': config,
                    'source_file': yaml_file.name
                })

    # 2. Import to database
    async with get_db() as db:
        # Import services first
        service_id_map = {}
        for svc in all_services:
            service_id = uuid4()
            await db.execute("""
                INSERT INTO traefik_services
                (id, name, type, servers, status, metadata, created_by)
                VALUES ($1, $2, 'loadbalancer', $3, 'active', $4, 'migration')
            """, service_id, svc['name'], json.dumps(svc['config'].get('loadBalancer', {})),
                json.dumps({'source_file': svc['source_file']}))
            service_id_map[svc['name']] = service_id

        # Import middleware
        for mw in all_middleware:
            mw_type = list(mw['config'].keys())[0]  # First key is middleware type
            await db.execute("""
                INSERT INTO traefik_middleware
                (id, name, type, config, status, created_by)
                VALUES ($1, $2, $3, $4, 'active', 'migration')
            """, uuid4(), mw['name'], mw_type, json.dumps(mw['config']))

        # Import routes
        for route in all_routes:
            service_id = service_id_map.get(route['service'])
            await db.execute("""
                INSERT INTO traefik_routes
                (id, name, rule, service_id, priority, entrypoints,
                 tls_enabled, middlewares, status, source, metadata, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', 'imported', $9, 'migration')
            """, uuid4(), route['name'], route['rule'], service_id,
                route['priority'], route['entrypoints'],
                'tls' in route and route['tls'].get('certResolver') is not None,
                route['middlewares'], json.dumps({'source_file': route['source_file']}))

    print(f"Imported {len(all_routes)} routes, {len(all_services)} services, {len(all_middleware)} middleware")
```

#### Step 3: Parallel Operation

**For 1-2 weeks, run both systems in parallel**:
- Existing YAML files remain active
- Ops-Center generates separate `ops-center-*.yml` files
- Monitor both for consistency

```bash
# Backup existing files
cp /home/deploy/Infrastructure/traefik/dynamic/domains.yml \
   /home/deploy/Infrastructure/traefik/dynamic/domains.yml.backup.migration

# Ops-Center writes to separate files
# /home/deploy/Infrastructure/traefik/dynamic/ops-center-routes.yml
```

#### Step 4: Cutover

**After validation period**:
1. Create final snapshot of current state
2. Rename old files to `.archived`
3. Ops-Center becomes source of truth
4. Document manual → ops-center migration complete

```bash
# Archive old files
cd /home/deploy/Infrastructure/traefik/dynamic
for f in domains.yml middlewares.yml api-domains.yml billing-routes.yml; do
    mv "$f" "$f.archived.$(date +%Y%m%d)"
done

# Ops-Center now manages all routes
```

#### Step 5: Cleanup

- Remove archived files after 30 days
- Document new workflow in team wiki
- Update runbooks to use Ops-Center UI

---

## Performance Considerations

### Database Optimization

**Indexes**:
- All foreign keys indexed
- Status columns indexed (for filtering)
- Created_at/updated_at indexed (for sorting)
- Full-text index on rule column (for search)

**Query Optimization**:
```sql
-- Use EXPLAIN ANALYZE to optimize queries
EXPLAIN ANALYZE
SELECT r.*, s.name as service_name
FROM traefik_routes r
JOIN traefik_services s ON r.service_id = s.id
WHERE r.status = 'active'
ORDER BY r.created_at DESC
LIMIT 50;

-- Add covering index if needed
CREATE INDEX idx_routes_active_sorted ON traefik_routes(status, created_at DESC)
WHERE status = 'active';
```

### Caching Strategy

**Redis Cache TTLs**:
- Route/Service/Middleware list: 60 seconds
- Individual route details: 120 seconds
- Metrics: 10 seconds
- Conflicts: 30 seconds
- Validation results: 300 seconds

**Cache Invalidation**:
```python
async def invalidate_cache_after_change(entity_type: str, entity_id: UUID):
    """Invalidate relevant cache keys after change"""
    redis = await get_redis()

    # Invalidate list cache
    await redis.delete(f'traefik:{entity_type}:all')

    # Invalidate specific entity cache
    await redis.delete(f'traefik:{entity_type}:{entity_id}')

    # If route changed, invalidate domain cache
    if entity_type == 'routes':
        route = await get_route(entity_id)
        hosts = extract_hosts(route.rule)
        for host in hosts:
            await redis.delete(f'traefik:routes:by_domain:{host}')
```

### File Write Performance

**Atomic Operations**:
- Write to temp file first
- Atomic rename (avoids partial reads)
- File locking prevents concurrent writes

**Batch Operations**:
```python
async def apply_bulk_changes(changes: List[dict]):
    """Apply multiple changes in single config write"""
    # 1. Validate all changes
    for change in changes:
        await validate_change(change)

    # 2. Apply all to database in transaction
    async with get_db() as db:
        async with db.transaction():
            for change in changes:
                await apply_change_to_db(change, db)

    # 3. Generate config once with all changes
    await write_config_file()

    # Result: Single Traefik reload instead of N reloads
```

### Frontend Performance

**Lazy Loading**:
- Routes table uses virtual scrolling
- Load 50 routes at a time
- Infinite scroll for large lists

**Optimistic UI Updates**:
- Update UI immediately
- Revert if API call fails
- Show loading states

**Debouncing**:
- Search input debounced (300ms)
- Filter changes debounced (300ms)
- Prevents excessive API calls

---

## Appendix

### A. Traefik Rule Syntax Reference

```yaml
# Host matching
Host(`example.com`)
Host(`example.com`, `www.example.com`)
HostRegexp(`^.+\.example\.com$`)

# Path matching
Path(`/exact/path`)
PathPrefix(`/api`)
PathRegexp(`^/api/v[0-9]+`)

# Method matching
Method(`GET`, `POST`)

# Header matching
Headers(`X-Custom-Header`, `value`)
HeadersRegexp(`X-Custom`, `^value.*`)

# Query parameter matching
Query(`param`, `value`)
QueryRegexp(`param`, `^value.*`)

# Client IP matching
ClientIP(`10.0.0.0/8`, `192.168.1.0/24`)

# Combining rules
Host(`example.com`) && PathPrefix(`/api`)
Host(`example.com`) || Host(`www.example.com`)
!PathPrefix(`/admin`)
```

### B. Middleware Configuration Examples

```yaml
# Rate limiting
rateLimit:
  average: 100  # requests per period
  burst: 50     # max burst
  period: 1m    # time period

# Headers
headers:
  customRequestHeaders:
    X-Custom: "value"
  customResponseHeaders:
    X-Powered-By: "UC-1 Pro"
  stsSeconds: 31536000
  stsIncludeSubdomains: true
  frameDeny: true
  contentTypeNosniff: true

# Basic Auth
basicAuth:
  users:
    - "admin:$apr1$xyz$..." # htpasswd format

# Forward Auth
forwardAuth:
  address: "http://auth-service:8000/verify"
  trustForwardHeader: true
  authResponseHeaders:
    - "X-User-Email"
    - "X-User-Role"

# Strip Prefix
stripPrefix:
  prefixes:
    - "/api/v1"
    - "/api/v2"

# Compress
compress: {}

# Redirect
redirectScheme:
  scheme: https
  permanent: true

# IP Whitelist
ipWhiteList:
  sourceRange:
    - "10.0.0.0/8"
    - "192.168.0.0/16"

# Circuit Breaker
circuitBreaker:
  expression: "NetworkErrorRatio() > 0.5"

# Retry
retry:
  attempts: 3
  initialInterval: 100ms
```

### C. Service Configuration Examples

```yaml
# Load Balancer
loadBalancer:
  servers:
    - url: "http://backend1:8080"
      weight: 2
    - url: "http://backend2:8080"
      weight: 1
  passHostHeader: true
  healthCheck:
    path: /health
    interval: 30s
    timeout: 5s
    followRedirects: true
  sticky:
    cookie:
      name: lb_session
      secure: true
      httpOnly: true

# Weighted
weighted:
  services:
    - name: service1
      weight: 3
    - name: service2
      weight: 1

# Mirroring
mirroring:
  service: main-service
  mirrors:
    - name: mirror-service
      percent: 10  # Mirror 10% of traffic
```

### D. API Rate Limits

| Endpoint | Rate Limit | Burst | Notes |
|----------|------------|-------|-------|
| GET /routes | 60/min | 120 | List routes |
| POST /routes | 10/min | 20 | Create route |
| PUT /routes/{id} | 20/min | 40 | Update route |
| DELETE /routes/{id} | 20/min | 40 | Delete route |
| POST /routes/validate | 30/min | 60 | Validate config |
| POST /config/apply | 5/min | 10 | Apply changes |
| POST /config/rollback | 5/min | 10 | Rollback config |
| GET /metrics | 120/min | 240 | Traffic metrics |

### E. Error Codes

| Code | Message | Description |
|------|---------|-------------|
| TR-001 | Invalid route rule syntax | Rule doesn't match Traefik syntax |
| TR-002 | Duplicate route name | Route with this name already exists |
| TR-003 | Service not found | Referenced service doesn't exist |
| TR-004 | Middleware not found | Referenced middleware doesn't exist |
| TR-005 | Route conflict detected | Rule conflicts with existing route |
| TR-006 | Invalid priority | Priority must be >= 0 |
| TR-007 | Config write failed | Failed to write YAML file |
| TR-008 | Traefik health check failed | Traefik not responding after change |
| TR-009 | Snapshot not found | Requested snapshot doesn't exist |
| TR-010 | Rollback failed | Failed to restore from snapshot |
| TR-011 | Certificate not found | SSL certificate doesn't exist |
| TR-012 | Certificate renewal failed | Let's Encrypt renewal error |

### F. Database Backup

```bash
# Daily backup of Traefik config tables
pg_dump -U unicorn -d unicorn_db \
  -t traefik_routes \
  -t traefik_services \
  -t traefik_middleware \
  -t traefik_certificates \
  -t traefik_audit_log \
  -t traefik_config_snapshots \
  -t traefik_route_conflicts \
  --data-only \
  --inserts \
  > /backups/traefik_config_$(date +%Y%m%d).sql

# Restore
psql -U unicorn -d unicorn_db < /backups/traefik_config_20251023.sql
```

---

## Summary

This architecture document provides a complete blueprint for implementing Traefik Configuration Management in Ops-Center. The design emphasizes:

1. **Simplicity**: File-based provider is simple and reliable
2. **Safety**: Validation, conflict detection, automatic snapshots
3. **Flexibility**: Support for all Traefik features
4. **Auditability**: Complete change history
5. **Resilience**: Automatic rollback on failures
6. **User Experience**: Intuitive UI with real-time validation

**Key Decisions**:
- ✅ File provider for configuration delivery
- ✅ PostgreSQL for metadata and audit
- ✅ Redis for caching and performance
- ✅ Hybrid approach: Docker discovery + manual routes
- ✅ Automatic snapshots before all changes
- ✅ Real-time health monitoring

**Next Steps**:
1. Review and approve architecture
2. Create Epic 1.3 implementation tasks
3. Set up development environment
4. Begin Phase 1 (Backend API)

---

**Document Version**: 1.0
**Last Updated**: October 23, 2025
**Status**: Ready for Review
**Estimated Implementation**: 5-6 weeks
