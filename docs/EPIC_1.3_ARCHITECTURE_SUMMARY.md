# Epic 1.3: Traefik Configuration Management
## Architecture Summary

**Status**: Design Complete - Ready for Implementation
**Estimated Timeline**: 5-6 weeks
**Document**: See `EPIC_1.3_ARCHITECTURE.md` for full details

---

## Quick Overview

### What We're Building

A **web-based Traefik management interface** integrated into Ops-Center that allows admins to:

- ✅ Create, edit, delete routes without touching YAML files
- ✅ Manage backend services and middleware visually
- ✅ Monitor SSL certificates and auto-renewals
- ✅ View real-time traffic metrics
- ✅ Detect and resolve conflicts automatically
- ✅ Rollback changes with snapshots
- ✅ Import/export configurations

### Why It Matters

**Current Pain Points**:
- Manual YAML editing is error-prone
- No validation until Traefik loads config
- No audit trail of changes
- No conflict detection
- Complex SSL certificate management

**After Implementation**:
- Point-and-click route creation
- Real-time validation and conflict warnings
- Complete audit history
- Automatic SSL monitoring
- One-click rollback

---

## Architecture Decisions

### 1. Configuration Delivery: File Provider (YAML)

**Why**: Simple, reliable, no Traefik restart needed

```
Ops-Center → Writes YAML → Traefik watches directory → Hot reload
```

**Alternative Rejected**: HTTP Provider (more complex, less mature)

### 2. Storage: Hybrid (PostgreSQL + File System)

**Why**: Best of both worlds

- **PostgreSQL**: Metadata, audit logs, validation
- **File System**: Actual Traefik config (YAML)
- **Redis**: Caching and fast lookups

### 3. Service Discovery: Docker + Manual

**Why**: Support both auto-discovered containers and manual routes

- Docker containers with labels → Auto-discovered
- Manual routes → Added via UI
- Both stored in PostgreSQL

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Ops-Center Frontend                         │
│  React UI with Route Editor, SSL Monitor, Traffic Dashboard │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ops-Center Backend API                      │
│  FastAPI with Validation Engine, Conflict Detector, Writer  │
└───┬─────────────────┬─────────────────┬─────────────────────┘
    │                 │                 │
    ▼                 ▼                 ▼
┌──────────┐    ┌──────────┐    ┌───────────────┐
│PostgreSQL│    │  Redis   │    │ File System   │
│- Routes  │    │- Cache   │    │- YAML configs │
│- Audit   │    │- Metrics │    │- Backups      │
└──────────┘    └──────────┘    └───────┬───────┘
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │   Traefik   │
                                  │ (watches &  │
                                  │ hot reloads)│
                                  └─────────────┘
```

---

## Database Schema (Summary)

**7 Main Tables**:

1. `traefik_routes` - Route configurations
2. `traefik_services` - Backend services
3. `traefik_middleware` - Reusable middleware
4. `traefik_certificates` - SSL certificate tracking
5. `traefik_audit_log` - Complete change history
6. `traefik_config_snapshots` - Rollback points
7. `traefik_route_conflicts` - Conflict tracking

**Key Features**:
- UUID primary keys
- JSONB for flexible config
- Full audit trail with user tracking
- Automatic timestamps
- Status tracking (active, disabled, pending, error)

---

## API Endpoints (Summary)

### Routes Management
```
GET    /api/v1/traefik/routes              # List routes
POST   /api/v1/traefik/routes              # Create route
GET    /api/v1/traefik/routes/{id}         # Get route details
PUT    /api/v1/traefik/routes/{id}         # Update route
DELETE /api/v1/traefik/routes/{id}         # Delete route
POST   /api/v1/traefik/routes/validate     # Validate config
POST   /api/v1/traefik/routes/{id}/enable  # Enable route
POST   /api/v1/traefik/routes/{id}/disable # Disable route
```

### Services Management
```
GET    /api/v1/traefik/services        # List services
POST   /api/v1/traefik/services        # Create service
PUT    /api/v1/traefik/services/{id}   # Update service
DELETE /api/v1/traefik/services/{id}   # Delete service
```

### Middleware Management
```
GET    /api/v1/traefik/middleware        # List middleware
POST   /api/v1/traefik/middleware        # Create middleware
PUT    /api/v1/traefik/middleware/{id}   # Update middleware
DELETE /api/v1/traefik/middleware/{id}   # Delete middleware
```

### SSL Certificates
```
GET  /api/v1/traefik/certificates                # List certificates
GET  /api/v1/traefik/certificates/{id}           # Certificate details
POST /api/v1/traefik/certificates/{id}/renew     # Force renewal
POST /api/v1/traefik/certificates/check-renewals # Check all
```

### Health & Metrics
```
GET /api/v1/traefik/health    # Traefik health status
GET /api/v1/traefik/metrics   # Traffic metrics
GET /api/v1/traefik/logs      # Access logs
```

### Configuration Management
```
GET  /api/v1/traefik/config/current            # Current config
POST /api/v1/traefik/config/apply              # Apply changes
GET  /api/v1/traefik/config/snapshots          # List snapshots
POST /api/v1/traefik/config/snapshots          # Create snapshot
POST /api/v1/traefik/config/rollback/{id}      # Rollback
POST /api/v1/traefik/config/validate           # Validate all
POST /api/v1/traefik/config/import             # Import YAML
GET  /api/v1/traefik/config/export             # Export YAML
```

### Service Discovery
```
GET  /api/v1/traefik/discovery/docker  # List Docker containers
POST /api/v1/traefik/discovery/sync    # Sync to database
```

**Total**: 35+ endpoints

---

## Frontend Components

### Main Pages

1. **RoutesDashboard**
   - List all routes with filtering
   - Status indicators
   - Quick actions (enable, disable, delete)
   - Search and filter

2. **RouteEditor** (Modal)
   - 4-step wizard: Basic Info → Service → Middleware → Review
   - Real-time validation
   - Conflict warnings
   - Preview before save

3. **ServicesDashboard**
   - List backend services
   - Health status monitoring
   - Server configuration

4. **MiddlewareDashboard**
   - List middleware
   - Usage tracking
   - Templates for common patterns

5. **SSLDashboard**
   - Certificate list with expiration
   - Renewal status
   - Auto-renewal monitoring
   - Manual certificate upload

6. **TrafficMonitor**
   - Real-time request charts
   - Latency visualization
   - Error rate tracking
   - Per-route metrics

7. **ConfigManagement**
   - Snapshot list
   - Import/Export wizard
   - Rollback interface

---

## Key Features

### 1. Conflict Detection

**Automatic Detection**:
- Duplicate host rules
- Priority conflicts
- Path overlaps
- Middleware incompatibilities

**Resolution**:
- Visual warnings before applying
- Suggested fixes
- Force option for overrides

### 2. Validation Engine

**Pre-Apply Validation**:
- Traefik rule syntax
- Service existence
- Middleware availability
- Domain conflicts
- SSL certificate status

**Post-Apply Health Check**:
- Monitor Traefik health
- Verify routes accessible
- Auto-rollback on failure

### 3. Automatic Snapshots

**Before every change**:
- Automatic snapshot created
- Stored in database
- Includes YAML content
- One-click rollback

**Snapshot Retention**:
- Automatic: 30 days
- Manual: Indefinite
- Cleanup job runs daily

### 4. Audit Logging

**Every action logged**:
- What changed
- Who changed it
- When it changed
- Old vs new values
- IP address
- User agent

**Query capabilities**:
- Filter by user
- Filter by date range
- Filter by entity type
- Export audit reports

### 5. SSL Management

**Automatic Monitoring**:
- Parse `acme.json` file
- Track expiration dates
- Alert on expiring certs (< 30 days)
- Monitor renewal attempts

**Manual Certificates**:
- Upload PEM files
- Validate certificate
- Update routes
- Expiration tracking

---

## Security

### Authentication
- Admin or Moderator role required
- JWT token validation
- Session tracking

### Authorization
- Route-level permissions
- Audit logging
- Two-factor confirmation for critical ops

### Input Validation
- Rule syntax validation
- SQL injection prevention
- Path traversal prevention
- YAML injection prevention

### Rate Limiting
- 10 route creates per minute
- 20 deletes per minute
- 5 config applies per minute

---

## Migration Plan

### Phase 1: Import Existing Config (Day 1)
- Inventory current YAML files (~36 routes)
- Import to PostgreSQL
- Verify accuracy

### Phase 2: Parallel Operation (Week 1-2)
- Existing YAML files remain active
- Ops-Center writes separate files
- Monitor consistency

### Phase 3: Cutover (Week 2)
- Archive old YAML files
- Ops-Center becomes source of truth
- Document new workflow

### Phase 4: Cleanup (Week 3)
- Remove archived files
- Update documentation
- Team training

---

## Implementation Timeline

### Week 1-2: Backend API
- PostgreSQL schema
- Core CRUD endpoints
- Config writer
- Validation engine

### Week 2-3: Basic Frontend
- Routes dashboard
- Route editor
- Services list
- Basic service editor

### Week 3-4: Advanced Features
- Middleware management
- SSL monitoring
- Conflict detection
- Traffic metrics

### Week 4-5: Config Management
- Snapshots/rollback
- Import/export
- Audit logging
- Service discovery

### Week 5-6: Polish & Production
- Error handling
- Documentation
- Testing
- Deployment

**Total**: 5-6 weeks

---

## Performance Optimizations

### Caching
- Redis cache with 60s TTL
- Cache invalidation on changes
- Metrics cached 10s

### Database
- Indexes on all foreign keys
- Full-text search on rules
- Query optimization

### File Operations
- Atomic writes (temp → rename)
- File locking
- Batch operations

### Frontend
- Virtual scrolling for large lists
- Lazy loading
- Optimistic UI updates
- Debounced search (300ms)

---

## Testing Strategy

### Unit Tests
- API endpoint tests
- Validation engine tests
- Conflict detection tests
- Config writer tests

### Integration Tests
- End-to-end route creation
- Traefik hot-reload verification
- Rollback functionality
- SSL monitoring

### Load Tests
- 100 concurrent route creates
- Large route list rendering
- Metrics dashboard performance

### User Acceptance Tests
- Admin creates route
- Admin edits route
- Admin rolls back change
- SSL certificate renewal

---

## Success Metrics

### Adoption
- 90% of routes managed via Ops-Center within 30 days
- 100% of new routes created via UI

### Reliability
- Zero unplanned Traefik restarts
- < 1% failed config applies
- < 5 second config propagation time

### Usability
- < 2 minutes to create a route
- < 30 seconds to rollback
- Zero YAML syntax errors

### Operations
- 100% audit trail coverage
- SSL certificate renewal success rate > 99%
- Zero expired certificates

---

## Risk Mitigation

### Risk: Traefik doesn't reload config
**Mitigation**: Health monitoring, automatic rollback

### Risk: Config file corruption
**Mitigation**: Atomic writes, automatic backups, snapshots

### Risk: Database unavailable
**Mitigation**: Fallback to file system, queue changes

### Risk: Concurrent modifications
**Mitigation**: File locking, database transactions, optimistic locking

### Risk: User error
**Mitigation**: Validation, warnings, two-step confirmation, easy rollback

---

## Documentation Deliverables

1. **API Documentation** - OpenAPI spec for all endpoints
2. **User Guide** - How to create/edit routes via UI
3. **Admin Guide** - Troubleshooting and maintenance
4. **Migration Guide** - Step-by-step migration from manual YAML
5. **Developer Guide** - Architecture and code structure
6. **Runbook** - Common operations and procedures

---

## Next Steps

1. **Review**: Architecture review with stakeholders
2. **Approval**: Get sign-off on approach
3. **Planning**: Break into implementation tasks
4. **Setup**: Create development environment
5. **Build**: Begin Week 1 development

---

## Questions & Answers

### Q: Why not use Docker labels exclusively?
**A**: Docker labels only work for containerized services. We need to support:
- External services (RunPod GPU server)
- Non-Docker deployments
- Complex routing rules

### Q: Why PostgreSQL instead of just files?
**A**: PostgreSQL provides:
- Rich querying and filtering
- Audit history
- Conflict detection
- Metrics storage
- Relationships (routes → services → middleware)

### Q: What if Traefik is down during a change?
**A**: Changes are queued and applied when Traefik comes back up. UI shows "Traefik Unavailable" warning.

### Q: Can we revert the entire system?
**A**: Yes, snapshots capture complete configuration state. One-click rollback restores everything.

### Q: How do we handle Traefik version upgrades?
**A**: Config format is Traefik v3 compatible. If upgrading to v4, we'd need migration scripts (but v3 is stable for years).

---

**Document**: EPIC_1.3_ARCHITECTURE.md (full details)
**Status**: Design Complete
**Estimated LOC**: ~5,000 backend + ~3,000 frontend = 8,000 lines
**Estimated Effort**: 200-250 hours (5-6 weeks)
