# Migration API Quick Reference

**Base Path**: `/api/v1/migration`
**Authentication**: Bearer token (admin required)
**Total Endpoints**: 20

---

## Phase 1: Discovery (3 endpoints)

```bash
# List all NameCheap domains
GET /namecheap/domains?status=active&search=unicorn&limit=50&offset=0

# Get domain details
GET /namecheap/domains/{domain}

# Bulk check domains
POST /namecheap/domains/bulk-check
{
  "domains": ["example.com", "example.net"]
}
```

---

## Phase 2: Export (3 endpoints)

```bash
# Export DNS records
GET /namecheap/domains/{domain}/dns?format=json

# Detect email service
GET /namecheap/domains/{domain}/email

# Bulk export DNS
POST /namecheap/domains/bulk-export
{
  "domains": ["example.com", "example.net"],
  "format": "json"
}
```

---

## Phase 3: Review (3 endpoints)

```bash
# Create migration preview
POST /migration/preview
{
  "domains": ["example.com"],
  "options": {"preserve_email": true}
}

# Get preview details
GET /migration/preview/{migration_id}

# Validate DNS records
POST /migration/validate
{
  "domain": "example.com",
  "records": [...]
}
```

---

## Phase 4: Execute (5 endpoints)

```bash
# Execute migration
POST /migration/execute
{
  "migration_id": "uuid",
  "confirm": true
}

# Get migration status
GET /migration/{migration_id}/status

# Pause migration
POST /migration/{migration_id}/pause

# Resume migration
POST /migration/{migration_id}/resume

# Rollback migration
POST /migration/{migration_id}/rollback
```

---

## Phase 5: Verify (5 endpoints)

```bash
# Verify DNS propagation
POST /migration/{migration_id}/verify/dns

# Verify SSL certificates
POST /migration/{migration_id}/verify/ssl

# Verify email functionality
POST /migration/{migration_id}/verify/email

# Verify website accessibility
POST /migration/{migration_id}/verify/website

# Overall health check
GET /migration/{migration_id}/health
```

---

## Health Check (1 endpoint)

```bash
# API health status
GET /health
```

---

## Rate Limits

| Operation | Limit | Category |
|-----------|-------|----------|
| Read (GET) | 30/min | read |
| Write (POST bulk) | 10/min | write |
| Critical (execute/rollback) | 5/min | critical |

---

## Response Codes

- `200 OK` - Success
- `201 Created` - Migration created
- `400 Bad Request` - Validation error
- `404 Not Found` - Domain/migration not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service not configured

---

## Example Workflow

### 1. List domains from NameCheap
```bash
curl -X GET "http://localhost:8084/api/v1/migration/namecheap/domains" \
  -H "Authorization: Bearer <token>"
```

### 2. Check email services
```bash
curl -X GET "http://localhost:8084/api/v1/migration/namecheap/domains/example.com/email" \
  -H "Authorization: Bearer <token>"
```

### 3. Preview migration
```bash
curl -X POST "http://localhost:8084/api/v1/migration/migration/preview" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com"], "options": {}}'
```

### 4. Execute migration
```bash
curl -X POST "http://localhost:8084/api/v1/migration/migration/execute" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"migration_id": "uuid-from-preview", "confirm": true}'
```

### 5. Monitor progress
```bash
curl -X GET "http://localhost:8084/api/v1/migration/migration/{migration_id}/status" \
  -H "Authorization: Bearer <token>"
```

### 6. Verify health
```bash
curl -X GET "http://localhost:8084/api/v1/migration/migration/{migration_id}/health" \
  -H "Authorization: Bearer <token>"
```

---

## Key Features

✅ 20 RESTful endpoints
✅ Pydantic request/response validation
✅ Multi-level rate limiting
✅ Background task orchestration
✅ Email service preservation
✅ DNS propagation monitoring
✅ SSL certificate verification
✅ Rollback capability
✅ Audit logging
✅ Comprehensive error handling

---

**Status**: Ready for integration with NameCheapManager and MigrationOrchestrator
