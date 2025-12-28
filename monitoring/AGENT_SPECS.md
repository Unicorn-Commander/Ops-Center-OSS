# Monitoring Team Agent Specifications

## Project Context

**Project**: Ops-Center Production Monitoring Infrastructure
**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`
**Stack**: FastAPI, React, PostgreSQL, Redis, Keycloak, Docker
**Container**: `ops-center-direct` (port 8084)

## Existing Infrastructure

**Already Running** (TaxSquare instance):
- Prometheus: `taxsquare-prometheus` (port 9091)
- Grafana: `taxsquare-grafana` (port 3102)

**Existing Monitoring Code**:
- `backend/resource_monitor.py` - System resource monitoring class
- `backend/requirements.txt` - Python dependencies (needs prometheus_client added)

**Services to Monitor**:
1. Ops-Center API (FastAPI backend)
2. PostgreSQL (`unicorn-postgresql`)
3. Redis (`unicorn-redis`, `unicorn-lago-redis`)
4. Keycloak SSO (`uchub-keycloak`)
5. Cloudflare API (via backend proxy)
6. NameCheap API (via backend proxy)
7. Lago Billing (`unicorn-lago-api`)
8. Traefik Reverse Proxy
9. Docker containers (all services)

---

## Agent 1: Prometheus Setup Specialist

### Your Mission
Configure complete Prometheus metrics collection for all Ops-Center services.

### Deliverables

1. **docker-compose.monitoring.yml** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/docker-compose.monitoring.yml`)
   - Prometheus container (port 9090)
   - Grafana container (port 3000)
   - Alertmanager container (port 9093)
   - Networks: `unicorn-network`, `web`, `uchub-network`
   - Volumes for persistence
   - Traefik labels for HTTPS access

2. **prometheus.yml** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/prometheus/prometheus.yml`)
   - Global config (scrape_interval: 15s, evaluation_interval: 15s)
   - Scrape configs for:
     - Ops-Center FastAPI `/metrics` endpoint (ops-center-direct:8084)
     - PostgreSQL exporter (if available)
     - Redis exporter (if available)
     - Docker container metrics (cAdvisor)
     - Node exporter for system metrics
     - Alertmanager itself
   - Service discovery for Docker containers
   - Relabeling rules for clean metrics

3. **metrics_exporter.py** (`/home/muut/Production/UC-Cloud/services/ops-center/backend/metrics_exporter.py`)
   - FastAPI `/metrics` endpoint using `prometheus_client`
   - Custom metrics:
     - `ops_center_api_requests_total` (Counter) - API request count by endpoint
     - `ops_center_api_request_duration_seconds` (Histogram) - API latency
     - `ops_center_api_errors_total` (Counter) - Errors by type
     - `ops_center_db_queries_total` (Counter) - Database query count
     - `ops_center_db_query_duration_seconds` (Histogram) - DB query latency
     - `ops_center_cloudflare_api_calls_total` (Counter) - Cloudflare API usage
     - `ops_center_namecheap_api_calls_total` (Counter) - NameCheap API usage
     - `ops_center_keycloak_logins_total` (Counter) - SSO login count
     - `ops_center_lago_invoices_total` (Counter) - Billing invoice count
     - `ops_center_active_users` (Gauge) - Current active users
   - Integration with existing `resource_monitor.py`
   - Middleware for automatic request tracking

4. **requirements.txt update**
   - Add: `prometheus-client==0.19.0`
   - Add: `prometheus-fastapi-instrumentator==6.1.0`

5. **Update server.py** (`/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py`)
   - Import metrics_exporter
   - Add `/metrics` endpoint
   - Add middleware for request tracking

### Implementation Patterns

**Use existing patterns from Ops-Center**:
- Follow FastAPI router pattern (see `firewall_api.py`, `cloudflare_api.py`)
- Use existing logging patterns (see `audit_logger.py`)
- Follow Docker compose patterns (see `docker-compose.direct.yml`)

**Prometheus Best Practices**:
- Use histograms for latency with buckets: [0.1, 0.5, 1, 2, 5, 10]
- Use counters for cumulative metrics
- Use gauges for current values
- Label metrics appropriately (endpoint, method, status_code)

---

## Agent 2: Grafana Dashboards Specialist

### Your Mission
Create 15 production-ready Grafana dashboards with visualizations for all Ops-Center services.

### Deliverables

**15 Grafana Dashboard JSON files** in `/home/muut/Production/UC-Cloud/services/ops-center/monitoring/grafana/dashboards/`:

1. **system-health-overview.json**
   - Panels: CPU usage, memory usage, disk usage, network I/O
   - Time series graphs for all metrics
   - Current value gauges
   - Threshold alerts visualization

2. **api-performance.json**
   - Request rate (requests/second)
   - Latency percentiles (p50, p95, p99)
   - Error rate by endpoint
   - Top 10 slowest endpoints
   - HTTP status code distribution

3. **database-performance.json**
   - PostgreSQL connection count
   - Query execution time
   - Slow queries (>1s)
   - Table sizes
   - Transaction rate

4. **cloudflare-api-monitoring.json**
   - API call rate to Cloudflare
   - Rate limit tracking
   - Zone operation success/failure
   - DNS record operations
   - Error types distribution

5. **namecheap-api-monitoring.json**
   - Migration job queue depth
   - Migration success/failure rate
   - DNS operation latency
   - Active migrations count
   - Domain transfer status

6. **keycloak-sso.json**
   - Login success/failure rate
   - Active sessions count
   - Authentication failures by reason
   - Session duration distribution
   - Top users by login count

7. **lago-billing.json**
   - Active subscriptions by tier
   - Invoice generation rate
   - Payment success/failure
   - Webhook processing time
   - Revenue metrics

8. **redis-performance.json**
   - Cache hit rate
   - Memory usage
   - Connected clients
   - Commands/second
   - Keyspace statistics

9. **docker-containers.json**
   - CPU usage per container
   - Memory usage per container
   - Network I/O per container
   - Container restart count
   - Container health status

10. **business-metrics.json**
    - Active users (total, by tier)
    - API usage by user
    - Subscription tier distribution
    - Revenue trend
    - User growth rate

11. **error-dashboard.json**
    - Error rate timeline
    - Errors by type (500, 404, 403, etc.)
    - Error rate by endpoint
    - Stack trace aggregation
    - Error trend analysis

12. **sla-dashboard.json**
    - 99.9% uptime tracking
    - Service availability per component
    - Mean time to recovery (MTTR)
    - Mean time between failures (MTBF)
    - SLA compliance percentage

13. **migration-jobs.json**
    - Active migration jobs
    - Migration queue depth
    - Success/failure rate
    - Average migration time
    - Failed migration details

14. **dns-operations.json**
    - Zone creation rate
    - DNS record updates
    - Propagation delays
    - DNSSEC operations
    - Zone health status

15. **security-events.json**
    - Failed login attempts
    - Rate limit hits by IP
    - Suspicious activity alerts
    - Firewall rule triggers
    - API key usage anomalies

### Implementation Patterns

**Dashboard Structure** (JSON format):
```json
{
  "dashboard": {
    "title": "Dashboard Name",
    "tags": ["ops-center", "category"],
    "timezone": "browser",
    "panels": [...],
    "templating": {
      "list": [
        {"name": "instance", "type": "datasource"},
        {"name": "interval", "type": "interval"}
      ]
    },
    "time": {"from": "now-6h", "to": "now"},
    "refresh": "30s"
  }
}
```

**Panel Types to Use**:
- Time series (line/bar charts)
- Stat (current value)
- Gauge (percentage metrics)
- Table (detailed lists)
- Heatmap (activity patterns)
- Pie chart (distributions)

**Grafana Best Practices**:
- Use template variables for dynamic filtering
- Set appropriate refresh intervals (30s for critical, 1m for others)
- Use meaningful panel titles and descriptions
- Set color thresholds (green <70%, yellow 70-90%, red >90%)
- Group related panels in rows

---

## Agent 3: Alerting Rules Specialist

### Your Mission
Configure comprehensive alerting rules for production monitoring with Slack/email/PagerDuty integration.

### Deliverables

1. **alertmanager.yml** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/alerting/alertmanager.yml`)
   - Route configuration
   - Receiver definitions:
     - Slack webhook (channel: #ops-center-alerts)
     - Email (to: ops@magicunicorn.tech)
     - PagerDuty (integration key placeholder)
   - Grouping rules (by severity, service)
   - Inhibition rules (suppress lower severity when higher severity active)

2. **alert-rules.yml** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/prometheus/alert-rules.yml`)

   **Critical Alerts** (PagerDuty + Slack + Email):
   - `OpsCenterDown` - API not responding for 2 minutes
   - `DatabaseDown` - PostgreSQL unreachable
   - `DiskSpaceOver90Percent` - Disk >90% full
   - `MemoryOver90Percent` - Memory >90% used
   - `RedisDown` - Redis unreachable
   - `KeycloakDown` - SSO service unreachable

   **High Priority Alerts** (Slack + Email):
   - `HighErrorRate` - Error rate >5% for 5 minutes
   - `HighAPILatency` - p95 latency >1s for 5 minutes
   - `HighAuthFailureRate` - >10 failed logins/minute
   - `DiskSpaceOver80Percent` - Disk >80% full
   - `CPUOver80Percent` - CPU >80% for 10 minutes

   **Medium Priority Alerts** (Slack only):
   - `ModerateDiskUsage` - Disk >70% full
   - `ModerateMemoryUsage` - Memory >70% used
   - `HighCacheMissRate` - Redis cache miss rate >50%
   - `SlowDatabaseQueries` - >10 slow queries/minute

3. **notification-templates/** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/alerting/templates/`)
   - `slack-template.tmpl` - Formatted Slack notifications
   - `email-template.tmpl` - HTML email notifications
   - `pagerduty-template.tmpl` - PagerDuty alert format

4. **ALERT_RUNBOOK.md** (`/home/muut/Production/UC-Cloud/services/ops-center/docs/ALERT_RUNBOOK.md`)
   - For each alert type:
     - Description: What triggered the alert
     - Impact: What users experience
     - Diagnosis: How to investigate
     - Resolution: Step-by-step fix procedures
     - Escalation: When to escalate
   - Example:
     ```markdown
     ## OpsCenterDown

     **Description**: Ops-Center API has not responded to health checks for 2+ minutes

     **Impact**:
     - Users cannot access the dashboard
     - API requests failing
     - All administrative functions unavailable

     **Diagnosis**:
     1. Check container status: `docker ps | grep ops-center-direct`
     2. Check container logs: `docker logs ops-center-direct --tail 100`
     3. Check resource usage: `docker stats ops-center-direct`

     **Resolution**:
     1. If container stopped: `docker restart ops-center-direct`
     2. If OOM error: Increase container memory limit
     3. If application error: Check logs and restart

     **Escalation**: Page on-call engineer if not resolved in 5 minutes
     ```

5. **alert-test-script.sh** (`/home/muut/Production/UC-Cloud/services/ops-center/monitoring/alerting/test-alerts.sh`)
   - Script to test each alert condition
   - Verify Slack/email delivery
   - Test alert grouping and routing

### Implementation Patterns

**Alert Rule Format**:
```yaml
groups:
  - name: critical
    interval: 30s
    rules:
      - alert: OpsCenterDown
        expr: up{job="ops-center"} == 0
        for: 2m
        labels:
          severity: critical
          service: ops-center
        annotations:
          summary: "Ops-Center API is down"
          description: "{{ $labels.instance }} has been down for more than 2 minutes"
```

**Alert Manager Routing**:
```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true
    - match:
        severity: high
      receiver: slack-high
    - match:
        severity: medium
      receiver: slack-medium
```

---

## Coordination & Success Criteria

### Communication
- Each agent works independently on their deliverables
- Use existing Ops-Center patterns and conventions
- Document all configurations thoroughly
- Create runnable, testable artifacts

### Testing Requirements
- All configurations must be syntactically valid YAML/JSON
- Prometheus config must pass: `promtool check config prometheus.yml`
- Alert rules must pass: `promtool check rules alert-rules.yml`
- Dashboards must be importable in Grafana
- Python code must follow FastAPI patterns

### File Locations Summary
```
services/ops-center/
├── monitoring/
│   ├── docker-compose.monitoring.yml
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alert-rules.yml
│   ├── grafana/
│   │   └── dashboards/ (15 JSON files)
│   └── alerting/
│       ├── alertmanager.yml
│       └── templates/
├── backend/
│   ├── metrics_exporter.py (new)
│   ├── server.py (update)
│   └── requirements.txt (update)
└── docs/
    ├── MONITORING_SETUP.md
    ├── DASHBOARD_GUIDE.md
    └── ALERT_RUNBOOK.md
```

### Success Metrics
- ✅ Prometheus collecting metrics from all services
- ✅ 15 Grafana dashboards operational
- ✅ Alert rules configured and tested
- ✅ Complete documentation created
- ✅ Integration with existing Ops-Center code
- ✅ Zero breaking changes to existing functionality

---

**Remember**: This is production infrastructure. Focus on reliability, observability, and actionable insights!
