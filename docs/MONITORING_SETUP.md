# Ops-Center Production Monitoring Setup Guide

**Version**: 1.0.0
**Last Updated**: October 22, 2025
**Status**: Production Ready

---

## Overview

This guide covers the complete setup and configuration of production monitoring infrastructure for Ops-Center, including:

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization dashboards
- **Alertmanager** - Alert routing and notifications
- **Exporters** - PostgreSQL, Redis, Node, cAdvisor

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                         │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │  Prometheus   │   │   Grafana    │
            │  (Metrics)    │◄──┤ (Dashboards) │
            └───────┬───────┘   └──────────────┘
                    │
        ┌───────────┼───────────────────┐
        │           │                   │
    ┌───▼───┐  ┌───▼────┐         ┌────▼────┐
    │FastAPI│  │PostgreSQL│       │  Redis   │
    │/metrics│  │Exporter │        │ Exporter │
    └────────┘  └─────────┘        └──────────┘
```

---

## Prerequisites

### Required
- Docker and Docker Compose
- Ops-Center running (`ops-center-direct` container)
- Access to `unicorn-network`, `web`, and `uchub-network` Docker networks
- Traefik reverse proxy configured

### Optional
- Slack workspace (for Slack notifications)
- PagerDuty account (for critical alerts)
- SMTP server (for email notifications)

---

## Quick Start

### 1. Deploy Monitoring Stack

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/monitoring

# Start all monitoring services
docker compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker ps | grep -E "prometheus|grafana|alertmanager"

# Check logs
docker logs ops-center-prometheus
docker logs ops-center-grafana
docker logs ops-center-alertmanager
```

### 2. Install Python Dependencies

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Install prometheus-client and instrumentator
docker exec ops-center-direct pip install prometheus-client==0.19.0 prometheus-fastapi-instrumentator==6.1.0

# Or rebuild container
docker restart ops-center-direct
```

### 3. Integrate Metrics into Ops-Center

Add the following to `backend/server.py`:

```python
from metrics_exporter import metrics_collector, PrometheusMiddleware, metrics_endpoint

# Add middleware (after CORS middleware)
app.add_middleware(PrometheusMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return await metrics_endpoint()
```

### 4. Access Monitoring UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | https://monitoring.your-domain.com | admin / your-admin-password |
| **Prometheus** | https://metrics.your-domain.com | admin / (htpasswd protected) |
| **Alertmanager** | https://alerts.your-domain.com | admin / (htpasswd protected) |

---

## Configuration

### Prometheus

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/monitoring/prometheus/prometheus.yml`

**Scrape Targets**:
- Ops-Center FastAPI: `ops-center-direct:8084/metrics`
- PostgreSQL: `ops-center-postgres-exporter:9187`
- Redis: `ops-center-redis-exporter:9121`
- Node Exporter: `ops-center-node-exporter:9100`
- cAdvisor: `ops-center-cadvisor:8080`
- Keycloak: `uchub-keycloak:8080/metrics`
- Lago: `unicorn-lago-api:3000/metrics`

**Retention**: 30 days (configurable in docker-compose.yml)

**Alert Rules**: `/monitoring/prometheus/alert-rules.yml`
- 23 total alerts across critical/high/medium/business/security categories

### Grafana

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/monitoring/grafana/`

**Provisioning**:
- Datasources: `provisioning/datasources/prometheus.yml`
- Dashboards: `provisioning/dashboards/default.yml`
- Dashboard JSON files: `dashboards/*.json`

**Default Dashboard**: System Health Overview

**Plugin Requirements**:
- grafana-piechart-panel
- grafana-clock-panel

### Alertmanager

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/monitoring/alerting/alertmanager.yml`

**Notification Channels**:

1. **Critical Alerts**:
   - PagerDuty (integration key required)
   - Slack (#ops-center-critical)
   - Email (ops@magicunicorn.tech)

2. **High Alerts**:
   - Slack (#ops-center-alerts)
   - Email (ops@magicunicorn.tech)

3. **Medium Alerts**:
   - Slack (#ops-center-alerts)

4. **Security Alerts**:
   - All channels + #security-alerts

**Alert Grouping**:
- Group by: alertname, severity, service
- Group wait: 10s
- Group interval: 5m
- Repeat interval: 3h

---

## Setting Up Notifications

### Slack Integration

1. Create Slack App: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create webhook for channel #ops-center-alerts
4. Update `alertmanager.yml`:

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
```

5. Restart Alertmanager:

```bash
docker restart ops-center-alertmanager
```

### PagerDuty Integration

1. Create PagerDuty service
2. Add Prometheus integration
3. Copy integration key
4. Update `alertmanager.yml`:

```yaml
pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
```

### Email Notifications

1. Configure SMTP settings in `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: 'YOUR_APP_PASSWORD'
  smtp_require_tls: true
```

2. For Gmail:
   - Enable 2FA
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use app password in config

---

## Metrics Reference

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ops_center_api_requests_total` | Counter | Total API requests |
| `ops_center_api_request_duration_seconds` | Histogram | API request latency |
| `ops_center_api_errors_total` | Counter | Total API errors |

### Database Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ops_center_db_queries_total` | Counter | Total database queries |
| `ops_center_db_query_duration_seconds` | Histogram | Database query latency |
| `pg_stat_database_tup_fetched` | Counter | Tuples fetched |
| `pg_connections` | Gauge | Active connections |

### External API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ops_center_cloudflare_api_calls_total` | Counter | Cloudflare API calls |
| `ops_center_namecheap_api_calls_total` | Counter | NameCheap API calls |

### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ops_center_active_users` | Gauge | Active users by tier |
| `ops_center_lago_invoices_total` | Counter | Invoices by status |
| `ops_center_total_revenue_dollars` | Gauge | Total revenue |

---

## Dashboard Inventory

**15 Production Dashboards Created**:

1. **System Health Overview** - CPU, memory, disk, network
2. **API Performance** - Latency, throughput, errors
3. **Database Performance** - Connections, queries, slow queries
4. **Cloudflare API Monitoring** - Rate limits, zone operations
5. **NameCheap API Monitoring** - Migration jobs, DNS ops
6. **Keycloak SSO** - Logins, sessions, auth failures
7. **Lago Billing** - Subscriptions, invoices, webhooks
8. **Redis Performance** - Cache hit rate, memory, commands
9. **Docker Containers** - Resource usage per container
10. **Business Metrics** - Users, revenue, subscriptions
11. **Error Dashboard** - Error rates, types, trends
12. **SLA Dashboard** - 99.9% uptime tracking
13. **Migration Jobs** - Active migrations, queue depth
14. **DNS Operations** - Zone management, propagation
15. **Security Events** - Failed logins, rate limits

---

## Testing

### Verify Prometheus Scraping

```bash
# Check targets status
curl https://metrics.your-domain.com/targets

# Query metrics
curl https://metrics.your-domain.com/api/v1/query?query=up

# Check specific metric
curl https://metrics.your-domain.com/api/v1/query?query=ops_center_api_requests_total
```

### Test Alertmanager

```bash
# Check configuration
curl https://alerts.your-domain.com/api/v1/status

# Send test alert
curl -X POST https://alerts.your-domain.com/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "labels": {
        "alertname": "TestAlert",
        "severity": "critical"
      },
      "annotations": {
        "summary": "This is a test alert"
      }
    }
  ]'
```

### Validate Alert Rules

```bash
docker exec ops-center-prometheus promtool check rules /etc/prometheus/alert-rules.yml
```

### Test Grafana Dashboards

1. Login to Grafana
2. Navigate to Dashboards > Browse
3. Open "System Health Overview"
4. Verify data is loading
5. Test time range selector
6. Test panel refresh

---

## Troubleshooting

### Prometheus Not Scraping

**Problem**: Targets show as "DOWN" in Prometheus

**Solutions**:
```bash
# Check if Ops-Center metrics endpoint is accessible
curl http://ops-center-direct:8084/metrics

# Verify network connectivity
docker exec ops-center-prometheus wget -O- http://ops-center-direct:8084/metrics

# Check Prometheus logs
docker logs ops-center-prometheus --tail 100
```

### Grafana Shows "No Data"

**Problem**: Dashboards don't display metrics

**Solutions**:
```bash
# Verify Prometheus datasource
# In Grafana: Configuration > Data Sources > Prometheus > Test

# Check Prometheus is reachable from Grafana
docker exec ops-center-grafana wget -O- http://ops-center-prometheus:9090/api/v1/query?query=up

# Verify metrics exist in Prometheus
curl http://ops-center-prometheus:9090/api/v1/label/__name__/values
```

### Alerts Not Firing

**Problem**: Expected alerts don't trigger

**Solutions**:
```bash
# Check alert rule evaluation
curl http://ops-center-prometheus:9090/api/v1/rules

# Verify Alertmanager connection
curl http://ops-center-prometheus:9090/api/v1/alertmanagers

# Check Alertmanager status
docker logs ops-center-alertmanager --tail 100
```

### Slack Notifications Not Received

**Problem**: Alerts fire but Slack doesn't receive

**Solutions**:
```bash
# Test webhook manually
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test message from Alertmanager"}'

# Check Alertmanager logs for webhook errors
docker logs ops-center-alertmanager | grep -i slack

# Verify webhook URL in alertmanager.yml
docker exec ops-center-alertmanager cat /etc/alertmanager/alertmanager.yml | grep slack_api_url
```

---

## Maintenance

### Update Prometheus Configuration

```bash
# Edit prometheus.yml
vim /home/muut/Production/UC-Cloud/services/ops-center/monitoring/prometheus/prometheus.yml

# Reload configuration (no restart needed)
curl -X POST http://ops-center-prometheus:9090/-/reload

# Or restart if reload fails
docker restart ops-center-prometheus
```

### Add New Dashboard

```bash
# Copy dashboard JSON to dashboards directory
cp new-dashboard.json /home/muut/Production/UC-Cloud/services/ops-center/monitoring/grafana/dashboards/

# Grafana will auto-load in 30 seconds
# Or manually: Dashboards > Browse > Import
```

### Update Alert Rules

```bash
# Edit alert-rules.yml
vim /home/muut/Production/UC-Cloud/services/ops-center/monitoring/prometheus/alert-rules.yml

# Validate syntax
docker exec ops-center-prometheus promtool check rules /etc/prometheus/alert-rules.yml

# Reload Prometheus
curl -X POST http://ops-center-prometheus:9090/-/reload
```

### Backup Monitoring Data

```bash
# Backup Prometheus data
docker run --rm \
  -v ops-center-prometheus-data:/data \
  -v $(pwd)/backups:/backup \
  busybox tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /data

# Backup Grafana dashboards
docker run --rm \
  -v ops-center-grafana-data:/data \
  -v $(pwd)/backups:/backup \
  busybox tar czf /backup/grafana-$(date +%Y%m%d).tar.gz /data
```

---

## Performance Tuning

### Prometheus

**Storage Optimization**:
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=30d'  # Reduce for less storage
  - '--storage.tsdb.min-block-duration=2h'
  - '--storage.tsdb.max-block-duration=2h'
```

**Query Optimization**:
- Use recording rules for complex queries
- Reduce scrape intervals for non-critical metrics
- Enable query logging for slow queries

### Grafana

**Dashboard Performance**:
- Limit time range to 6h or less for real-time dashboards
- Use $__rate_interval for rate queries
- Enable query caching
- Reduce refresh interval (use 30s instead of 5s)

### Alertmanager

**Reduce Alert Noise**:
- Use inhibition rules to suppress duplicate alerts
- Increase group_interval to batch related alerts
- Use active_time_intervals for business-hours-only alerts

---

## Security

### Authentication

**Prometheus & Alertmanager**:
- Basic auth enabled via Traefik
- Default: admin / (generated htpasswd)
- Change password: `htpasswd -c .htpasswd admin`

**Grafana**:
- Admin password set in environment variable
- Default: admin / your-admin-password
- Change after first login

### Network Security

- All monitoring services on `unicorn-network` (internal)
- Only Grafana exposed via Traefik (HTTPS)
- Prometheus/Alertmanager require basic auth
- API endpoints protected by Ops-Center auth

### Secrets Management

**Sensitive Values**:
- Slack webhook URL
- PagerDuty integration key
- SMTP password
- Grafana admin password

**Best Practices**:
- Use environment variables for secrets
- Never commit secrets to Git
- Rotate credentials quarterly
- Use Docker secrets in production

---

## Monitoring the Monitors

### Prometheus Self-Monitoring

```promql
# Prometheus uptime
up{job="prometheus"}

# Scrape duration
scrape_duration_seconds

# Rule evaluation duration
prometheus_rule_evaluation_duration_seconds
```

### Grafana Health Checks

```bash
# API health
curl https://monitoring.your-domain.com/api/health

# Database health
docker exec ops-center-grafana grafana-cli admin health
```

### Alertmanager Health

```promql
# Alertmanager uptime
up{job="alertmanager"}

# Notification queue
alertmanager_notifications_total
alertmanager_notifications_failed_total
```

---

## Resources

### Documentation
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/

### Prometheus Query Examples
- PromQL Guide: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Recording Rules: https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/

### Grafana Resources
- Dashboard Gallery: https://grafana.com/grafana/dashboards/
- Panel Plugins: https://grafana.com/grafana/plugins/

### Exporters
- Node Exporter: https://github.com/prometheus/node_exporter
- PostgreSQL Exporter: https://github.com/prometheus-community/postgres_exporter
- Redis Exporter: https://github.com/oliver006/redis_exporter

---

## Support

**For Issues**:
1. Check logs: `docker logs <container-name>`
2. Verify configuration syntax
3. Test connectivity between services
4. Review alert runbook for specific alerts

**Contact**:
- Email: ops@magicunicorn.tech
- Slack: #ops-center-support

---

**Version History**:
- v1.0.0 (2025-10-22): Initial production monitoring setup
