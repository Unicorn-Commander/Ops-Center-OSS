# Epic 1.3: Traefik Configuration Management
## Architecture Diagrams

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                           ADMIN USER (Browser)                               │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OPS-CENTER FRONTEND                                 │
│                          (React SPA on Nginx)                                │
│                                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   Routes    │  │   Services   │  │  Middleware  │  │  SSL Dashboard  │ │
│  │  Dashboard  │  │  Dashboard   │  │  Dashboard   │  │                 │ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   Traffic   │  │    Config    │  │     Audit    │  │     Service     │ │
│  │   Monitor   │  │  Management  │  │     Logs     │  │    Discovery    │ │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘ │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │ REST API (JSON)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OPS-CENTER BACKEND                                  │
│                          (FastAPI on Python)                                 │
│                                                                              │
│  ┌─────────────────────┐  ┌────────────────────┐  ┌───────────────────┐   │
│  │  Route API          │  │  Service API       │  │  Middleware API   │   │
│  │  /api/v1/traefik/   │  │  /api/v1/traefik/  │  │  /api/v1/traefik/ │   │
│  │  routes             │  │  services          │  │  middleware       │   │
│  └─────────────────────┘  └────────────────────┘  └───────────────────┘   │
│                                                                              │
│  ┌─────────────────────┐  ┌────────────────────┐  ┌───────────────────┐   │
│  │  Validation Engine  │  │  Conflict Detector │  │  Config Writer    │   │
│  │  - Rule syntax      │  │  - Host conflicts  │  │  - YAML generator │   │
│  │  - Service check    │  │  - Priority issues │  │  - Atomic write   │   │
│  │  - Middleware chain │  │  - Path overlap    │  │  - File locking   │   │
│  └─────────────────────┘  └────────────────────┘  └───────────────────┘   │
│                                                                              │
│  ┌─────────────────────┐  ┌────────────────────┐  ┌───────────────────┐   │
│  │  Health Monitor     │  │  Audit Logger      │  │  Snapshot Manager │   │
│  │  - Traefik ping     │  │  - Change tracking │  │  - Auto snapshots │   │
│  │  - Route checks     │  │  - User actions    │  │  - Rollback       │   │
│  │  - Auto rollback    │  │  - IP logging      │  │  - Export/Import  │   │
│  └─────────────────────┘  └────────────────────┘  └───────────────────┘   │
│                                                                              │
└──┬────────────────────────┬────────────────────────┬─────────────────────┬──┘
   │                        │                        │                     │
   │ SQL                    │ Cache                  │ File I/O            │ Docker API
   │                        │                        │                     │
   ▼                        ▼                        ▼                     ▼
┌──────────┐          ┌──────────┐          ┌─────────────┐      ┌──────────────┐
│PostgreSQL│          │  Redis   │          │File System  │      │Docker Engine │
│          │          │          │          │             │      │              │
│- Routes  │          │- Cache   │          │- YAML files │      │- Containers  │
│- Services│          │- Metrics │          │- Backups    │      │- Labels      │
│- Midware │◄─────────┤- Locks   │          │- Snapshots  │      │- Networks    │
│- Certs   │  Sync    │          │          │             │      │              │
│- Audit   │          │          │          │             │      │              │
│- Snapshots│         │          │          │             │      │              │
│- Conflicts│         │          │          │             │      │              │
└──────────┘          └──────────┘          └──────┬──────┘      └──────────────┘
                                                    │
                                                    │ inotify watch
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │   TRAEFIK     │
                                            │   (v3.0)      │
                                            │               │
                                            │ - Watches     │
                                            │   /dynamic/   │
                                            │ - Hot reload  │
                                            │ - No restart  │
                                            │               │
                                            └───────┬───────┘
                                                    │
                                                    │ Routes traffic to
                                                    │
                        ┌───────────────────────────┼───────────────────────────┐
                        │                           │                           │
                        ▼                           ▼                           ▼
                ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
                │  ops-center   │          │ chat.unicorn  │          │   brigade     │
                │  :8084        │          │  :8080        │          │   :8102       │
                └───────────────┘          └───────────────┘          └───────────────┘
```

---

## 2. Configuration Flow

```
┌──────────────┐
│ Admin clicks │
│ "Create      │
│  Route"      │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ Fill out form:          │
│ - Name: my-service      │
│ - Rule: Host(`...`)     │
│ - Service: backend      │
│ - Middleware: security  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend validates      │
│ - Required fields       │
│ - Basic syntax          │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ POST /api/v1/traefik/   │
│      routes             │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend validation:     │
│ 1. Rule syntax ✓        │
│ 2. Service exists ✓     │
│ 3. No conflicts ✓       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Create snapshot         │
│ (before changes)        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Insert to PostgreSQL:   │
│ - traefik_routes        │
│ - traefik_audit_log     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Generate YAML:          │
│                         │
│ http:                   │
│   routers:              │
│     my-service:         │
│       rule: Host(...)   │
│       service: backend  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Atomic file write:      │
│ 1. Write to .tmp        │
│ 2. Validate YAML        │
│ 3. Rename .tmp → .yml   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Traefik detects change  │
│ (inotify on /dynamic)   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Traefik hot reload      │
│ (no restart needed)     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend health check:   │
│ - Ping Traefik API ✓    │
│ - Test route access ✓   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Update Redis cache      │
│ Invalidate stale data   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Return success to UI    │
│ Show toast notification │
└─────────────────────────┘
```

---

## 3. Conflict Detection Flow

```
┌──────────────┐
│ Admin creates│
│ new route    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Extract from rule:                  │
│ - Hosts: [example.com]              │
│ - Paths: [/api]                     │
│ - Priority: 0                       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Query PostgreSQL for active routes  │
│ WHERE status = 'active'             │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ For each existing route:            │
│ 1. Extract hosts and paths          │
│ 2. Check for overlap                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ CONFLICT TYPE 1:                    │
│ Same host + Same priority           │
│                                     │
│ New:      Host(`example.com`) @ 0   │
│ Existing: Host(`example.com`) @ 0   │
│                                     │
│ ❌ ERROR - Will conflict!           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ CONFLICT TYPE 2:                    │
│ Same host + Overlapping paths       │
│                                     │
│ New:      /api/v1/*                 │
│ Existing: /api/*                    │
│                                     │
│ ⚠️  WARNING - May conflict          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Insert conflicts to DB:             │
│ - traefik_route_conflicts           │
│ - Severity: error/warning           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Return validation response:         │
│                                     │
│ {                                   │
│   "valid": false,                   │
│   "errors": [                       │
│     "Route conflicts with 'api-v1'" │
│   ],                                │
│   "warnings": [                     │
│     "Path overlap detected"         │
│   ],                                │
│   "conflicts": [...]                │
│ }                                   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ UI shows warnings in editor         │
│                                     │
│ ⚠️  WARNING                         │
│ This route conflicts with:          │
│ - api-v1 (same host, priority 0)    │
│                                     │
│ Suggested fix:                      │
│ - Change priority to 1              │
│ - Or modify rule                    │
│                                     │
│ [ Cancel ]  [ Force Create ]        │
└─────────────────────────────────────┘
```

---

## 4. Rollback Flow

```
┌──────────────┐
│ Admin clicks │
│ "Rollback to │
│  snapshot"   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ Load snapshot from DB:  │
│ - Config data           │
│ - YAML content          │
│ - Created at: 2025-10-20│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Create snapshot of      │
│ CURRENT state           │
│ (for undo)              │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Write snapshot YAML     │
│ to file system          │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Traefik hot reload      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Health check:           │
│ Is Traefik healthy?     │
└──────┬──────────────────┘
       │
       ├─── YES ───────────┐
       │                   ▼
       │           ┌───────────────────┐
       │           │ Restore DB from   │
       │           │ snapshot config   │
       │           └───────┬───────────┘
       │                   │
       │                   ▼
       │           ┌───────────────────┐
       │           │ Mark snapshot as  │
       │           │ restored          │
       │           └───────┬───────────┘
       │                   │
       │                   ▼
       │           ┌───────────────────┐
       │           │ Clear Redis cache │
       │           └───────┬───────────┘
       │                   │
       │                   ▼
       │           ┌───────────────────┐
       │           │ Success message   │
       │           │ to UI             │
       │           └───────────────────┘
       │
       └─── NO ────────────┐
                           ▼
                   ┌───────────────────┐
                   │ ROLLBACK FAILED!  │
                   │ Restore current   │
                   │ state             │
                   └───────┬───────────┘
                           │
                           ▼
                   ┌───────────────────┐
                   │ Error message     │
                   │ to UI             │
                   └───────────────────┘
```

---

## 5. SSL Certificate Monitoring

```
┌─────────────────────────┐
│ Background Task         │
│ (runs every 6 hours)    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Read acme.json file     │
│ /traefik/acme/acme.json │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Parse certificates:     │
│                         │
│ For each cert:          │
│ - Domain                │
│ - Issued at             │
│ - Expires at            │
│ - Certificate data      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Calculate days until    │
│ expiry:                 │
│                         │
│ days = (expires_at -    │
│         now).days       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Determine status:       │
│                         │
│ if days < 0:            │
│   status = 'expired'    │
│ elif days < 30:         │
│   status = 'expiring'   │
│ else:                   │
│   status = 'valid'      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Update PostgreSQL:      │
│                         │
│ INSERT/UPDATE           │
│ traefik_certificates    │
│ SET status, expires_at  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Check for expiring:     │
│                         │
│ SELECT * WHERE          │
│ status IN ('expiring',  │
│            'expired')   │
└──────┬──────────────────┘
       │
       ├─── Found expiring ─┐
       │                    ▼
       │            ┌───────────────────┐
       │            │ Send notification │
       │            │ to admins:        │
       │            │                   │
       │            │ "Certificate for  │
       │            │ example.com       │
       │            │ expires in 25 days│
       │            └───────────────────┘
       │
       └─── All valid ──────┐
                            ▼
                    ┌───────────────────┐
                    │ Log: All certs OK │
                    └───────────────────┘
```

---

## 6. Service Discovery

```
┌─────────────────────────┐
│ Background Task         │
│ (runs every 5 minutes)  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Query Docker API:       │
│                         │
│ docker.containers.list()│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ For each container:     │
│ Check labels            │
│                         │
│ if 'traefik.enable' ==  │
│    'true'               │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Extract Traefik config  │
│ from labels:            │
│                         │
│ - Router rule           │
│ - Service port          │
│ - Middleware            │
│ - TLS config            │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Check if route exists   │
│ in PostgreSQL:          │
│                         │
│ SELECT * FROM routes    │
│ WHERE name = ...        │
└──────┬──────────────────┘
       │
       ├─── EXISTS ─────────┐
       │                    ▼
       │            ┌───────────────────┐
       │            │ Compare config:   │
       │            │ Changed?          │
       │            └───────┬───────────┘
       │                    │
       │                    ├─── YES ───┐
       │                    │           ▼
       │                    │   ┌───────────────┐
       │                    │   │ Update route  │
       │                    │   └───────────────┘
       │                    │
       │                    └─── NO ────┐
       │                                ▼
       │                        ┌───────────────┐
       │                        │ Skip (no      │
       │                        │ changes)      │
       │                        └───────────────┘
       │
       └─── NOT EXISTS ────────┐
                               ▼
                       ┌───────────────────┐
                       │ Create new route: │
                       │ - Name from label │
                       │ - Rule from label │
                       │ - Service: auto   │
                       │ - Source: docker  │
                       └───────┬───────────┘
                               │
                               ▼
                       ┌───────────────────┐
                       │ Mark as           │
                       │ auto-discovered   │
                       └───────┬───────────┘
                               │
                               ▼
                       ┌───────────────────┐
                       │ Regenerate YAML   │
                       │ config            │
                       └───────────────────┘
```

---

## 7. Database Entity Relationships

```
┌─────────────────────────┐
│   traefik_routes        │
│─────────────────────────│
│ PK  id (UUID)           │
│     name (UNIQUE)       │
│     rule                │
│ FK  service_id ─────────┼──┐
│     priority            │  │
│     entrypoints[]       │  │
│     tls_enabled         │  │
│     middlewares[]       │  │
│     status              │  │
│     source              │  │
│     metadata (JSONB)    │  │
│     created_at          │  │
│     created_by          │  │
└─────────────────────────┘  │
                             │
                             │
                             ▼
              ┌──────────────────────────┐
              │   traefik_services       │
              │──────────────────────────│
              │ PK  id (UUID)            │
              │     name (UNIQUE)        │
              │     type                 │
              │     servers (JSONB)      │
              │     pass_host_header     │
              │     health_check (JSONB) │
              │     status               │
              │     created_at           │
              └──────────────────────────┘


┌─────────────────────────┐
│  traefik_middleware     │
│─────────────────────────│
│ PK  id (UUID)           │
│     name (UNIQUE)       │
│     type                │
│     config (JSONB)      │
│     description         │
│     usage_count         │
│     status              │
│     created_at          │
└─────────────────────────┘


┌─────────────────────────┐        ┌─────────────────────────┐
│  traefik_certificates   │        │  traefik_audit_log      │
│─────────────────────────│        │─────────────────────────│
│ PK  id (UUID)           │        │ PK  id (UUID)           │
│     domain (UNIQUE)     │        │     entity_type         │
│     type                │        │     entity_id           │
│     resolver            │        │     entity_name         │
│     status              │        │     action              │
│     issued_at           │        │     changes (JSONB)     │
│     expires_at          │        │     user_id             │
│     renewal_attempts    │        │     user_email          │
│     error_message       │        │     ip_address          │
└─────────────────────────┘        │     success             │
                                   │     created_at          │
                                   └─────────────────────────┘

┌─────────────────────────┐        ┌─────────────────────────┐
│ traefik_config_snapshots│        │ traefik_route_conflicts │
│─────────────────────────│        │─────────────────────────│
│ PK  id (UUID)           │        │ PK  id (UUID)           │
│     snapshot_name       │        │ FK  route_id_1          │
│     description         │        │ FK  route_id_2          │
│     config_data (JSONB) │        │     conflict_type       │
│     file_content (TEXT) │        │     severity            │
│     is_automatic        │        │     description         │
│     created_at          │        │     resolved            │
│     created_by          │        │     resolved_at         │
│     restored_at         │        │     created_at          │
└─────────────────────────┘        └─────────────────────────┘
```

---

## 8. Authentication & Authorization Flow

```
┌──────────────┐
│ User visits  │
│ /admin/      │
│ traefik      │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend checks:        │
│ localStorage.authToken  │
└──────┬──────────────────┘
       │
       ├─── Token exists ──┐
       │                   ▼
       │           ┌───────────────────┐
       │           │ Send API request  │
       │           │ Authorization:    │
       │           │ Bearer <token>    │
       │           └───────┬───────────┘
       │                   │
       │                   ▼
       │           ┌───────────────────┐
       │           │ Backend validates │
       │           │ JWT token         │
       │           └───────┬───────────┘
       │                   │
       │                   ├─── Valid & Admin ─┐
       │                   │                    ▼
       │                   │            ┌───────────────┐
       │                   │            │ Process       │
       │                   │            │ request       │
       │                   │            └───────┬───────┘
       │                   │                    │
       │                   │                    ▼
       │                   │            ┌───────────────┐
       │                   │            │ Return data   │
       │                   │            └───────────────┘
       │                   │
       │                   └─── Invalid/No Admin ──┐
       │                                            ▼
       │                                    ┌───────────────┐
       │                                    │ 401/403 Error │
       │                                    └───────┬───────┘
       │                                            │
       └─── No token ───────────────────────────────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │ Redirect to   │
                                            │ /auth/login   │
                                            └───────┬───────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │ Keycloak SSO  │
                                            │ Login page    │
                                            └───────────────┘
```

---

## 9. Frontend Component Tree

```
App
└── Router
    └── TraefikManagement (Page)
        ├── Header
        │   ├── Title
        │   └── ActionButtons
        │       ├── CreateRouteButton
        │       ├── SyncDockerButton
        │       └── ExportConfigButton
        │
        ├── TabNavigation
        │   ├── RoutesTab
        │   ├── ServicesTab
        │   ├── MiddlewareTab
        │   ├── SSLTab
        │   ├── TrafficTab
        │   └── ConfigTab
        │
        └── TabContent
            │
            ├── RoutesDashboard (if RoutesTab active)
            │   ├── RouteFilters
            │   │   ├── SearchField
            │   │   ├── StatusFilter
            │   │   └── SourceFilter
            │   │
            │   ├── ConflictWarnings (if conflicts)
            │   │
            │   ├── RoutesList
            │   │   └── RouteCard (foreach route)
            │   │       ├── RouteHeader
            │   │       ├── RouteMetrics
            │   │       └── RouteActions
            │   │           ├── EditButton
            │   │           ├── EnableButton
            │   │           ├── DisableButton
            │   │           └── DeleteButton
            │   │
            │   └── RouteEditor (Modal)
            │       ├── Stepper
            │       │   ├── BasicInfoStep
            │       │   ├── ServiceStep
            │       │   ├── MiddlewareStep
            │       │   └── ReviewStep
            │       │
            │       ├── StepContent
            │       │   ├── BasicInfoForm
            │       │   │   ├── NameField
            │       │   │   ├── RuleField
            │       │   │   ├── PriorityField
            │       │   │   └── EntryPointsSelect
            │       │   │
            │       │   ├── ServiceForm
            │       │   │   ├── ServiceSelector
            │       │   │   ├── TLSToggle
            │       │   │   └── CertResolverField
            │       │   │
            │       │   ├── MiddlewareForm
            │       │   │   └── MiddlewareMultiSelect
            │       │   │
            │       │   └── ReviewPanel
            │       │       ├── ValidationResults
            │       │       ├── ConflictWarnings
            │       │       └── ConfigSummary
            │       │
            │       └── DialogActions
            │           ├── CancelButton
            │           ├── BackButton
            │           ├── NextButton
            │           └── SaveButton
            │
            ├── ServicesDashboard (if ServicesTab active)
            │   ├── ServicesList
            │   │   └── ServiceCard (foreach service)
            │   │       ├── ServiceHeader
            │   │       ├── ServersList
            │   │       ├── HealthStatus
            │   │       └── ServiceActions
            │   │
            │   └── ServiceEditor (Modal)
            │       ├── ServiceForm
            │       │   ├── NameField
            │       │   ├── TypeSelect
            │       │   ├── ServersEditor
            │       │   │   └── ServerRow (foreach server)
            │       │   │       ├── URLField
            │       │   │       └── WeightField
            │       │   │
            │       │   ├── HealthCheckConfig
            │       │   └── StickySessionsConfig
            │       │
            │       └── DialogActions
            │
            ├── MiddlewareDashboard (if MiddlewareTab active)
            │   ├── MiddlewareList
            │   │   └── MiddlewareCard (foreach middleware)
            │   │       ├── MiddlewareHeader
            │   │       ├── UsageCount
            │   │       └── MiddlewareActions
            │   │
            │   └── MiddlewareEditor (Modal)
            │       ├── MiddlewareForm
            │       │   ├── NameField
            │       │   ├── TypeSelect
            │       │   └── ConfigEditor (dynamic based on type)
            │       │       ├── RateLimitConfig (if type=rateLimit)
            │       │       ├── HeadersConfig (if type=headers)
            │       │       ├── AuthConfig (if type=basicAuth)
            │       │       └── ...
            │       │
            │       └── DialogActions
            │
            ├── SSLDashboard (if SSLTab active)
            │   ├── ExpirationAlert (if certs expiring)
            │   │
            │   ├── CertificatesList
            │   │   └── CertificateCard (foreach cert)
            │   │       ├── DomainName
            │   │       ├── StatusBadge
            │   │       ├── ExpirationDate
            │   │       ├── ExpirationProgress
            │   │       └── RenewButton (if expiring)
            │   │
            │   └── CertificateDetails (Modal)
            │       ├── CertificateInfo
            │       ├── RoutesUsing
            │       └── RenewalHistory
            │
            ├── TrafficMonitor (if TrafficTab active)
            │   ├── MetricsCards
            │   │   ├── TotalRequestsCard
            │   │   ├── ErrorRateCard
            │   │   ├── AvgLatencyCard
            │   │   └── ActiveRoutesCard
            │   │
            │   ├── ChartsSection
            │   │   ├── RequestsChart (Line chart)
            │   │   ├── LatencyChart (Area chart)
            │   │   └── ErrorRateChart (Bar chart)
            │   │
            │   └── RouteMetricsTable
            │       └── RouteMetricRow (foreach route)
            │
            └── ConfigManagement (if ConfigTab active)
                ├── SnapshotsList
                │   └── SnapshotCard (foreach snapshot)
                │       ├── SnapshotInfo
                │       ├── RestoreButton
                │       └── DeleteButton
                │
                ├── ImportExport
                │   ├── ImportButton
                │   └── ExportButton
                │
                └── ImportWizard (Modal)
                    ├── FileUpload
                    ├── ValidationResults
                    └── ImportActions
```

---

**Document**: EPIC_1.3_ARCHITECTURE.md (full details)
**Summary**: EPIC_1.3_ARCHITECTURE_SUMMARY.md
**Diagrams**: This file

These diagrams provide visual representations of the key architectural components and flows for Epic 1.3.
