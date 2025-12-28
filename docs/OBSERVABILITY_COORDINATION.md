# Observability Team Coordination Document

**Date**: October 22, 2025
**Team Lead**: Observability Team Lead
**Sprint**: Production Readiness - Observability Implementation

---

## Team Structure

### Agent 1: Sentry Integration Specialist
**Responsibility**: Error tracking and performance monitoring
**Deliverables**:
- Sentry.io project setup (self-hosted preferred)
- Python SDK integration in FastAPI backend
- JavaScript SDK integration in React frontend
- Error grouping and tagging by service/endpoint/user tier
- Performance monitoring with transaction tracing
- Release tracking
- Custom error context (user ID, subscription tier, API endpoint)
- Slack/PagerDuty integration for critical errors
- `backend/sentry_config.py`
- `src/utils/sentry.js`
- Documentation: `docs/ERROR_TRACKING_GUIDE.md`

### Agent 2: Structured Logging Specialist
**Responsibility**: JSON logging and correlation IDs
**Deliverables**:
- JSON log format for all services
- Correlation ID implementation (UUID4 format)
- Request/response logging middleware
- Log levels properly configured (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Sensitive data redaction (API keys, passwords, tokens)
- Log rotation and retention (7 days)
- `backend/logging_config.py`
- Integration with Grafana (send ERROR logs)
- Documentation: `docs/LOGGING_STANDARDS.md`

### Agent 3: Distributed Tracing Specialist
**Responsibility**: OpenTelemetry instrumentation (optional/nice-to-have)
**Deliverables**:
- OpenTelemetry SDK setup
- Trace propagation across service boundaries
- Span creation for key operations (DB queries, external APIs, migrations)
- Jaeger or Tempo backend setup (Docker container)
- Trace visualization in Grafana
- `backend/tracing_config.py`
- Documentation: `docs/TRACING_GUIDE.md`

---

## Coordination Standards

### Correlation ID Format
**Standard**: UUID4 (RFC 4122)
**Header Name**: `X-Correlation-ID`
**Example**: `550e8400-e29b-41d4-a716-446655440000`

**Implementation**:
- Generate at request entry (middleware)
- Propagate to all downstream calls
- Include in all log entries
- Include in error reports
- Include in traces

### Log Format (JSON)
```json
{
  "timestamp": "2025-10-22T23:30:45.123Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "ops-center",
  "component": "user_management_api",
  "message": "User created successfully",
  "user_id": "user@example.com",
  "subscription_tier": "professional",
  "endpoint": "/api/v1/admin/users",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 145
}
```

### Sensitive Data Redaction
**Fields to Redact**:
- `password`, `passwd`, `pwd`
- `api_key`, `apikey`, `token`
- `secret`, `private_key`
- `authorization` header
- `credit_card`, `ssn`, `tax_id`

**Redaction Format**: `"password": "***REDACTED***"`

### Error Context Tags
**Sentry Tags**:
- `service`: "ops-center"
- `component`: "user_management" | "billing" | "llm" | "cloudflare" | "namecheap"
- `user_tier`: "trial" | "starter" | "professional" | "enterprise"
- `environment`: "production" | "staging" | "development"
- `api_endpoint`: "/api/v1/admin/users"
- `http_method`: "GET" | "POST" | "PUT" | "DELETE"

---

## Integration Points

### Existing Services
**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`

**Backend Services**:
- `backend/server.py` - Main FastAPI app
- `backend/user_management_api.py` - User management
- `backend/billing_api.py` - Billing operations
- `backend/cloudflare_api.py` - Cloudflare integration
- `backend/namecheap_manager.py` - NameCheap DNS (NEW - to be added)
- `backend/lago_integration.py` - Lago billing
- `backend/litellm_api.py` - LLM proxy

**Frontend Services**:
- `src/App.jsx` - Main React app
- `src/pages/*.jsx` - All page components
- `src/components/*.jsx` - Reusable components

### Monitoring Stack (Existing)
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3000)
- **PostgreSQL**: Application database
- **Redis**: Session store and cache

---

## Implementation Order

### Phase 1: Structured Logging (PRIORITY 1)
**Why First**: Foundation for all observability
**Timeline**: 2-3 hours
**Deliverables**:
- `backend/logging_config.py` created
- Correlation ID middleware implemented
- JSON logging enabled for all endpoints
- Sensitive data redaction active

### Phase 2: Sentry Integration (PRIORITY 2)
**Why Second**: Critical for error tracking
**Timeline**: 3-4 hours
**Deliverables**:
- Sentry container running (self-hosted)
- Python SDK integrated
- JavaScript SDK integrated
- Error context tags configured
- Alert rules set up

### Phase 3: Distributed Tracing (PRIORITY 3 - OPTIONAL)
**Why Last**: Nice-to-have enhancement
**Timeline**: 4-5 hours (if time permits)
**Deliverables**:
- OpenTelemetry instrumented
- Jaeger container running
- Key operations traced
- Grafana dashboard created

---

## Success Criteria

### Logging
- [ ] All API requests logged in JSON format
- [ ] Correlation IDs present in all logs
- [ ] Sensitive data properly redacted
- [ ] Log rotation configured (7 days retention)
- [ ] ERROR/CRITICAL logs sent to Grafana
- [ ] Log format validated with sample requests

### Error Tracking
- [ ] Sentry capturing all Python exceptions
- [ ] Sentry capturing all JavaScript errors
- [ ] Error grouping working correctly
- [ ] Custom context tags present
- [ ] Critical errors trigger Slack alerts
- [ ] Performance transactions tracked
- [ ] Release tracking functional

### Tracing (Optional)
- [ ] Traces propagate across service calls
- [ ] Database queries create spans
- [ ] External API calls create spans
- [ ] Traces visible in Grafana
- [ ] Correlation IDs match logs and traces

### Documentation
- [ ] `ERROR_TRACKING_GUIDE.md` complete
- [ ] `LOGGING_STANDARDS.md` complete
- [ ] `TRACING_GUIDE.md` complete (if Phase 3)
- [ ] Code examples provided
- [ ] Troubleshooting guide included

---

## Dependencies to Add

### Backend (requirements.txt)
```
# Logging
python-json-logger==2.0.7
structlog==24.1.0

# Sentry
sentry-sdk[fastapi]==1.45.0

# OpenTelemetry (optional)
opentelemetry-api==1.23.0
opentelemetry-sdk==1.23.0
opentelemetry-instrumentation-fastapi==0.44b0
opentelemetry-instrumentation-sqlalchemy==0.44b0
opentelemetry-instrumentation-redis==0.44b0
opentelemetry-exporter-jaeger==1.23.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "@sentry/react": "^7.109.0",
    "@sentry/tracing": "^7.109.0"
  }
}
```

---

## Communication Protocol

### Agent Updates
Each agent should provide updates in this format:
```markdown
## [Agent Name] Update - [Timestamp]

**Status**: [In Progress | Blocked | Complete]
**Completion**: [0-100%]

**Completed**:
- [Task 1]
- [Task 2]

**In Progress**:
- [Task 3] - [ETA]

**Blockers**:
- [Issue 1] - Needs input from [Agent/Lead]

**Next Steps**:
- [Task 4]
- [Task 5]
```

### Handoff Points
1. **Logging → Sentry**: Correlation ID format must be agreed before Sentry implementation
2. **Logging → Tracing**: Log format and correlation IDs must be finalized
3. **Sentry → Tracing**: Error context tags should align with trace tags

---

## Testing Strategy

### Unit Tests
- Test correlation ID generation and propagation
- Test sensitive data redaction
- Test JSON log formatting
- Test Sentry error capture

### Integration Tests
- End-to-end request with correlation ID tracking
- Error thrown → captured in Sentry → logged with context
- Trace created → correlation ID matches logs

### Manual Tests
1. Trigger error in UI → verify Sentry capture
2. Make API call → verify JSON log entry
3. Check Grafana → verify ERROR logs appear
4. Check Jaeger → verify trace visualization (if Phase 3)

---

## Deliverable Checklist

### Code Files
- [ ] `backend/logging_config.py`
- [ ] `backend/sentry_config.py`
- [ ] `backend/tracing_config.py` (optional)
- [ ] `backend/middleware/correlation_id.py`
- [ ] `backend/middleware/request_logging.py`
- [ ] `src/utils/sentry.js`
- [ ] `docker-compose.observability.yml` (Sentry/Jaeger containers)

### Documentation Files
- [ ] `docs/ERROR_TRACKING_GUIDE.md`
- [ ] `docs/LOGGING_STANDARDS.md`
- [ ] `docs/TRACING_GUIDE.md`
- [ ] `docs/OBSERVABILITY_COORDINATION.md` (this file)
- [ ] `docs/OBSERVABILITY_TESTING_GUIDE.md`

### Configuration Files
- [ ] Updated `backend/requirements.txt`
- [ ] Updated `package.json`
- [ ] Updated `.env` with Sentry DSN
- [ ] Updated `docker-compose.direct.yml` if needed

---

## Timeline

**Total Estimated Time**: 8-12 hours

| Phase | Agent | Hours | Priority |
|-------|-------|-------|----------|
| Logging | Agent 2 | 2-3 | P1 |
| Sentry | Agent 1 | 3-4 | P2 |
| Tracing | Agent 3 | 4-5 | P3 (Optional) |

**Parallel Execution**: Agents 1 and 2 can work in parallel after initial coordination.
**Sequential Dependencies**: Agent 3 depends on Agent 2's correlation ID implementation.

---

## Final Deliverable

**Observability Implementation Report**

Should include:
- Architecture diagram (logging/error tracking/tracing flow)
- Correlation ID strategy and implementation
- Sentry configuration and usage guide
- Log format specification
- Sample queries for Grafana
- Troubleshooting common issues
- Performance impact analysis
- Retention policies
- Cost estimation (if using Sentry.io cloud)

---

**Last Updated**: October 22, 2025 23:30 UTC
**Next Review**: After Phase 1 completion (logging)
