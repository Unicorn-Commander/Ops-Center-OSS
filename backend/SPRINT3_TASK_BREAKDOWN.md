# Sprint 3: Backend API Implementation

**Team Lead**: Sprint 3 Team Lead
**Working Directory**: `/opt/ops-center`
**Date**: October 25, 2025

---

## Task Allocation

### Agent 1: Traefik Dashboard & Metrics (C10 + C13)
**Estimated**: 6-10 hours
**Priority**: CRITICAL

#### C10: Dashboard Aggregation Endpoint
- **File**: `backend/traefik_api.py`
- **Endpoint**: `GET /api/v1/traefik/dashboard`
- **Requirements**:
  - Aggregate metrics from TraefikManager
  - Return: routes count, certificates count, services count, middleware count
  - Include: uptime, health status, recent changes
  - Response format: JSON with nested statistics

#### C13: Fix Metrics Endpoint
- **File**: `backend/traefik_api.py`
- **Endpoint**: `GET /api/v1/traefik/metrics`
- **Requirements**:
  - Fix endpoint mismatch (ensure consistency)
  - Add CSV export capability via query param `?format=csv`
  - Return: request counts, response times, error rates
  - CSV headers: timestamp, metric_name, value, unit

---

### Agent 2: Service Discovery (C11)
**Estimated**: 6-8 hours
**Priority**: CRITICAL

#### C11: Docker Service Discovery
- **File**: `backend/traefik_api.py`
- **Endpoint**: `GET /api/v1/traefik/services/discover`
- **Requirements**:
  - Query Docker API for running containers
  - Filter containers with labels: `traefik.enable=true`
  - Extract: container name, networks, ports, labels
  - Suggest Traefik route configuration for each
  - Return: List of discoverable services with auto-config templates

**Integration**:
- Use existing `simple_docker_manager.py` or Docker SDK
- Parse Docker labels for Traefik routing hints
- Generate suggested route rules (Host, PathPrefix, etc.)

---

### Agent 3: SSL Certificate Renewal (C12)
**Estimated**: 8-12 hours
**Priority**: CRITICAL

#### C12: Certificate Renewal Endpoints
- **File**: `backend/traefik_api.py`
- **Endpoints**:
  1. `POST /api/v1/traefik/ssl/renew/{id}` - Renew single certificate
  2. `POST /api/v1/traefik/ssl/renew/bulk` - Renew multiple certificates

**Requirements (Single Renewal)**:
- Accept certificate ID or domain name
- Trigger Let's Encrypt/ACME renewal
- Update acme.json
- Return: renewal status, new expiry date, errors

**Requirements (Bulk Renewal)**:
- Accept array of certificate IDs/domains
- Process renewals in parallel (asyncio)
- Return: success count, failure count, detailed results per cert
- Implement retry logic for failed renewals

**Integration**:
- Use existing `TraefikManager.request_certificate()`
- Add renewal logic to `TraefikManager` class
- Handle ACME challenge verification
- Implement DNS-01 or HTTP-01 challenge support

---

### Agent 4: Brigade Proxy Endpoints (H23)
**Estimated**: 4-6 hours
**Priority**: HIGH

#### H23: Brigade Usage & History
- **File**: `backend/brigade_api.py` (CREATE NEW)
- **Endpoints**:
  1. `GET /api/v1/brigade/usage` - User's Brigade usage stats
  2. `GET /api/v1/brigade/tasks/history` - Task execution history

**Requirements (Usage)**:
- Proxy to: `https://api.brigade.unicorncommander.ai/api/agents/usage`
- Add authentication headers from Ops-Center session
- Return: agent count, task count, compute hours, API calls

**Requirements (History)**:
- Proxy to: `https://api.brigade.unicorncommander.ai/api/tasks/history`
- Support pagination: `?limit=50&offset=0`
- Support filtering: `?status=completed&agent_id=123`
- Return: List of tasks with execution metadata

**Integration**:
- Use `httpx` for async HTTP proxying
- Forward user authentication (JWT token from Keycloak)
- Handle Brigade API errors gracefully
- Cache results in Redis (60s TTL)

---

## Implementation Guidelines

### Code Standards
1. **FastAPI Style**: Use async/await for all endpoints
2. **Error Handling**: Try-except with HTTPException
3. **Logging**: Use `logger.info()` and `logger.error()`
4. **Validation**: Pydantic models for request/response
5. **Documentation**: Docstrings with Args/Returns/Raises

### Testing Requirements
1. Manual testing with `curl` commands
2. Verify error responses (400, 404, 500)
3. Test authentication/authorization
4. Check response format consistency
5. Validate CSV export (if applicable)

### Registration in Server
After implementation, add router to `server.py`:
```python
from brigade_api import router as brigade_router
app.include_router(brigade_router)
```

---

## Deliverables

Each agent should deliver:
1. ✅ **Code Implementation**: Fully functional endpoints
2. ✅ **Error Handling**: All edge cases covered
3. ✅ **Manual Testing**: Curl commands + results
4. ✅ **Documentation**: Inline comments + docstrings
5. ✅ **Integration**: Registered in server.py (if new router)

---

## Timeline

**Total Estimated**: 24-36 hours
**With 4 Parallel Agents**: 6-9 hours

**Phases**:
1. **Hours 0-6**: Implementation by all 4 agents
2. **Hours 6-7**: Integration testing
3. **Hours 7-8**: Bug fixes and refinements
4. **Hours 8-9**: Documentation and git commit

---

## Success Criteria

- [ ] All 6 endpoints implemented and tested
- [ ] No breaking changes to existing endpoints
- [ ] Proper error handling (no unhandled exceptions)
- [ ] CSV export working for metrics
- [ ] Service discovery returns valid Docker containers
- [ ] SSL renewal triggers ACME challenges
- [ ] Brigade proxy forwards authentication correctly
- [ ] All endpoints documented in OpenAPI schema
- [ ] Git commit with clear commit message
- [ ] Summary report generated

---

## Notes

- **Traefik Manager**: Already has most certificate/route logic
- **Docker Integration**: Use existing `simple_docker_manager.py`
- **Brigade API**: External service, use HTTP client
- **Authentication**: All endpoints require admin role
- **Rate Limiting**: Respect TraefikManager rate limits

---

**Ready to spawn agents!** Each agent has clear tasks and deliverables.
