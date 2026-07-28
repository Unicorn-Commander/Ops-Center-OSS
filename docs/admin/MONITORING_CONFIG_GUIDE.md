# Admin Monitoring Configuration Guide

**Last Updated**: February 22, 2026
**Audience**: System administrators
**Version**: 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Umami Analytics](#umami-analytics)
3. [Grafana Dashboards](#grafana-dashboards)
4. [Prometheus Metrics](#prometheus-metrics)
5. [Troubleshooting](#troubleshooting)
6. [Future Enhancements](#future-enhancements)

---

## Overview

Ops-Center provides configuration pages for three monitoring services. As of v2.5.1, settings are persisted to browser localStorage and restored on page load.

**Important**: Settings are saved per-browser. They are NOT synced across browsers or users. Backend persistence will be added in a future release.

**Monitoring Pages:**

| Service | URL | Purpose |
|---------|-----|---------|
| Umami | `/admin/monitoring/umami` | Web analytics (visitors, page views) |
| Grafana | `/admin/monitoring/grafana` | Infrastructure dashboards |
| Prometheus | `/admin/monitoring/prometheus` | Metrics collection and alerting |

**v2.5.1 Changes:**
- All monitoring configuration pages now use relative URLs instead of hardcoded `localhost:8084`
- Settings persist to localStorage across page refreshes
- Swapped Visitors/Page Views labels in Umami fixed
- All fetch calls include `credentials: 'include'` for SSO cookie forwarding

---

## Umami Analytics (`/admin/monitoring/umami`)

### Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Umami URL** | The URL of your Umami analytics instance | `https://analytics.magicunicorn.dev` |
| **API Key** | Authentication key for the Umami API | `umami_api_key_...` |
| **Tracking Code** | Your site's tracking ID | `abc123-def456` |
| **Privacy Mode** | Strict mode respects Do Not Track headers | Enabled/Disabled |
| **Session Tracking** | Enable/disable session-based analytics | Enabled/Disabled |

### Dashboard Metrics

Once configured, the Umami dashboard displays:

| Metric | Source Field | Description |
|--------|-------------|-------------|
| **Visitors** | `uniques` | Unique visitors in the selected time range |
| **Page Views** | `pageviews` | Total page views in the selected time range |
| **Bounce Rate** | Calculated | Percentage of single-page sessions |
| **Average Time** | Calculated | Average session duration |

**Note (v2.5.1 fix):** In previous versions, the Visitors and Page Views labels were swapped in the UI. This has been corrected.

### Saving

Click **Save Configuration** to persist settings to localStorage. Settings survive page refreshes but are browser-specific.

**What Gets Saved:**
- Umami URL
- API Key
- Tracking Code
- Privacy Mode toggle
- Session Tracking toggle

### Health Check

The health check button tests connectivity to your Umami instance via `/api/v1/monitoring/umami`.

**Expected Responses:**

| Response | Meaning |
|----------|---------|
| Green checkmark | Umami is reachable and responding |
| Red X | Connection failed -- check URL and network |
| Yellow warning | Partial response (API key may be invalid) |

---

## Grafana Dashboards (`/admin/monitoring/grafana`)

### Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Grafana URL** | URL of your Grafana instance | `https://grafana.magicunicorn.dev` |
| **Admin Username** | Credentials for Grafana API access | `admin` |
| **Admin Password** | Credentials for Grafana API access | `********` |
| **API Key** | Alternative to username/password authentication | `eyJr...` |
| **Organization Name** | Grafana organization to use | `Magic Unicorn` |

**Authentication:** You can use either username/password or API key. API key is recommended for automated integrations.

### Grafana Viewer (`/admin/monitoring/grafana/viewer`)

The embedded Grafana viewer provides an in-dashboard experience without navigating to Grafana directly.

**Viewer Controls:**

| Control | Description | Persisted to localStorage |
|---------|-------------|--------------------------|
| **Theme** | Dark or light mode | Yes |
| **Time Range** | Configurable time window (1h, 6h, 24h, 7d, 30d) | Yes |
| **Refresh Interval** | Auto-refresh rate (off, 5s, 10s, 30s, 1m, 5m) | Yes |
| **Fullscreen** | Toggle fullscreen mode | No |
| **Dashboard Selection** | Browse and select from available dashboards | No |

### Saving

- **Config Page:** Settings persist on clicking the **Save** button
- **Viewer Page:** Theme, time range, and refresh interval persist to localStorage automatically when changed

---

## Prometheus Metrics (`/admin/monitoring/prometheus`)

### Configuration

| Field | Description | Default |
|-------|-------------|---------|
| **Prometheus URL** | URL of your Prometheus instance | `http://prometheus:9090` |
| **Scrape Interval** | How often Prometheus scrapes targets | `15s` |
| **Evaluation Interval** | How often rules are evaluated | `15s` |
| **Retention Time** | How long data is kept | `15d` |
| **Retention Size** | Maximum storage size | `50GB` |

### Scrape Targets

Add and manage Prometheus scrape targets from the configuration page.

**Target Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Human-readable target name | `ops-center-metrics` |
| **Endpoint** | URL to scrape metrics from | `http://ops-center-direct:8084/metrics` |
| **Interval** | Per-target scrape interval | `15s` |
| **Enabled** | Toggle target on/off | On/Off |
| **Labels** | Key-value labels for the target | `env=production, service=ops-center` |

**Common Targets for UC-Cloud:**

| Target | Endpoint | Description |
|--------|----------|-------------|
| Ops-Center | `http://ops-center-direct:8084/metrics` | Application metrics |
| GPU Exporter | `http://gpu-exporter:9835/metrics` | NVIDIA GPU metrics |
| Node Exporter | `http://node-exporter:9100/metrics` | System-level metrics |
| Redis Exporter | `http://redis-exporter:9121/metrics` | Redis cache metrics |
| PostgreSQL Exporter | `http://postgres-exporter:9187/metrics` | Database metrics |

### Saving

Click **Save Configuration** to persist to localStorage. This saves all configuration fields and the scrape targets list.

**Note:** These settings configure the Ops-Center UI display only. To actually change Prometheus server configuration, you need to edit the Prometheus configuration file and restart the Prometheus container.

---

## Troubleshooting

### Settings Lost After Browser Clear

**Cause:** Settings are stored in localStorage. Clearing browser data removes them.

**Solution:** Re-enter your configuration and click Save again.

**Prevention:** Consider exporting your settings before clearing browser data (copy the values to a secure note).

### Health Check Fails

**Step-by-step diagnosis:**

1. **Verify the service URL is correct and reachable**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://your-monitoring-url/health
   ```

2. **Check that the service is running**
   ```bash
   docker ps | grep prometheus
   docker ps | grep grafana
   docker ps | grep umami
   ```

3. **Check network connectivity from the Ops-Center container**
   ```bash
   docker exec ops-center-direct curl -s http://prometheus:9090/-/healthy
   docker exec ops-center-direct curl -s http://grafana:3000/api/health
   ```

4. **Review Ops-Center logs for errors**
   ```bash
   docker logs ops-center-direct --tail 50 | grep -i "monitoring\|umami\|grafana\|prometheus"
   ```

### Metrics Not Loading

**Common causes and fixes:**

| Problem | Cause | Fix |
|---------|-------|-----|
| CORS errors in browser console | Services on different domains | Configure CORS headers on monitoring service |
| 401 Unauthorized | Invalid API key or credentials | Re-enter credentials and save |
| Connection refused | Service not running | Start the service: `docker compose up -d <service>` |
| Timeout | Network issue or service overloaded | Check container resources with `docker stats` |
| Mixed content | HTTPS page loading HTTP resource | Ensure monitoring services use HTTPS |

### Grafana Viewer Shows Blank

**Possible causes:**

1. **Grafana URL incorrect** - Verify the URL in configuration
2. **Authentication failed** - Check API key or username/password
3. **No dashboards exist** - Create a dashboard in Grafana first
4. **Iframe blocking** - Grafana may block iframe embedding by default

**Fix iframe blocking in Grafana:**
```ini
# In grafana.ini or environment variable
[security]
allow_embedding = true
```

Or via Docker environment:
```yaml
environment:
  - GF_SECURITY_ALLOW_EMBEDDING=true
```

---

## Future Enhancements

Backend persistence for monitoring configuration is planned. This will:

- **Sync settings across browsers and users** - Configuration saved to PostgreSQL database
- **Enable API-driven configuration management** - REST endpoints for programmatic access
- **Support configuration backup and restore** - Export/import settings as JSON
- **Admin-level defaults** - Set organization-wide monitoring defaults that individual admins can override
- **Configuration audit trail** - Track who changed what and when

**Current Workaround:** For now, document your monitoring URLs and credentials in a secure location outside the browser so they can be re-entered if localStorage is cleared.

---

**Last Updated:** February 22, 2026
**Version:** 1.0.0
