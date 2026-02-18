# Grafana Integration Guide

**Last Updated**: November 29, 2025
**Version**: 1.0.0
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Endpoints](#api-endpoints)
5. [Frontend Components](#frontend-components)
6. [Configuration](#configuration)
7. [Dashboard Embedding](#dashboard-embedding)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

The Grafana integration enables seamless embedding and management of Grafana monitoring dashboards within Ops-Center. This integration provides:

- **Health Monitoring**: Real-time Grafana instance status checks
- **Dashboard Management**: List, view, and embed existing dashboards
- **Data Source Management**: Configure Prometheus, PostgreSQL, Loki, and other data sources
- **Metric Queries**: Query Grafana data sources programmatically
- **Embedded Dashboards**: iframe embedding with theme and time range controls

### Current Grafana Instance

- **Container**: `taxsquare-grafana`
- **Internal Port**: 3000
- **External Port**: 3102
- **Version**: 12.2.0
- **Status**: Healthy ✅

---

## Architecture

### Service Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Ops-Center                               │
│         (unicorncommander.ai:8084)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │   Backend API  │   │  Frontend    │
            │  (FastAPI)     │   │  (React SPA) │
            └───────┬────────┘   └──────┬───────┘
                    │                   │
                    │ HTTP requests     │ iframe embeds
                    │                   │
            ┌───────▼───────────────────▼───────┐
            │       Grafana Container            │
            │   (taxsquare-grafana:3000)         │
            │   External: localhost:3102         │
            └────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
    ┌───▼───┐  ┌───▼───┐  ┌────▼────┐
    │Prometheus│ │PostgreSQL│ │  Loki   │
    │Data Source│ │Data Source│ │Data Source│
    └──────────┘  └─────────┘  └─────────┘
```

### Network Configuration

- **Internal Communication**: Backend → `http://taxsquare-grafana:3000`
- **External Access**: Browser → `http://localhost:3102`
- **Docker Network**: Both on `web` network for inter-container communication

---

## Setup Instructions

### 1. Verify Grafana is Running

```bash
# Check if Grafana container is running
docker ps | grep grafana

# Expected output:
# a9e1897fa888   grafana/grafana:latest   Up 2 weeks   0.0.0.0:3102->3000/tcp   taxsquare-grafana

# Test Grafana health
curl http://localhost:3102/api/health
```

### 2. Configure Environment Variables

Edit `/services/ops-center/.env.auth`:

```bash
# === Grafana Integration ===
GRAFANA_URL=http://taxsquare-grafana:3000
GRAFANA_EXTERNAL_URL=http://localhost:3102
GRAFANA_API_KEY=         # Optional - generate in Grafana UI
GRAFANA_ORG_ID=1
GRAFANA_TIMEOUT=30
```

### 3. Generate Grafana API Key (Optional)

API keys are **optional** for viewing existing dashboards but **required** for:
- Creating/deleting dashboards
- Managing data sources
- Querying metrics programmatically

**To Generate**:

1. Open Grafana: http://localhost:3102
2. Login with default credentials: `admin` / `admin`
3. Navigate to: **Configuration → API Keys**
4. Click **"New API Key"**
5. Settings:
   - **Name**: `ops-center-integration`
   - **Role**: `Viewer` (for read-only) or `Admin` (for full access)
   - **TTL**: 1 year or never expire
6. Copy the generated key and add to `.env.auth`:
   ```bash
   GRAFANA_API_KEY=eyJrIjoiYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY3ODkwIiwidCI6Im9wcy1jZW50ZXIifQ==
   ```

### 4. Restart Ops-Center

```bash
cd /opt/ops-center
docker restart ops-center-direct

# Verify backend loaded Grafana config
docker logs ops-center-direct | grep -i grafana
```

### 5. Access Grafana Viewer

Once configured, access Grafana dashboards via:

- **Grafana Config**: https://unicorncommander.ai/admin/monitoring/grafana
- **Dashboard Viewer**: https://unicorncommander.ai/admin/monitoring/grafana/dashboards
- **Direct Grafana**: http://localhost:3102

---

## API Endpoints

All Grafana endpoints are prefixed with `/api/v1/monitoring/grafana`.

### Health Check

```http
GET /api/v1/monitoring/grafana/health
```

**Response**:
```json
{
  "success": true,
  "status": "healthy",
  "version": "12.2.0",
  "database": "ok",
  "timestamp": "2025-11-29T12:00:00Z"
}
```

### List Dashboards

```http
GET /api/v1/monitoring/grafana/dashboards
```

**Query Parameters**:
- `api_key` (optional): Grafana API key

**Response**:
```json
{
  "success": true,
  "count": 3,
  "dashboards": [
    {
      "uid": "system-metrics",
      "title": "System Metrics",
      "type": "dash-db",
      "url": "/d/system-metrics",
      "tags": ["system", "monitoring"]
    }
  ]
}
```

### Get Dashboard by UID

```http
GET /api/v1/monitoring/grafana/dashboards/{uid}
```

**Response**:
```json
{
  "success": true,
  "dashboard": {
    "uid": "system-metrics",
    "title": "System Metrics",
    "panels": [...],
    "meta": {...}
  }
}
```

### Generate Embed URL

```http
GET /api/v1/monitoring/grafana/dashboards/{uid}/embed-url
```

**Query Parameters**:
- `theme` (default: "dark"): "light" or "dark"
- `refresh` (optional): Auto-refresh interval (e.g., "30s", "1m", "5m")
- `from_time` (default: "now-6h"): Start time
- `to_time` (default: "now"): End time
- `kiosk` (default: "tv"): Kiosk mode ("tv" or "full")

**Response**:
```json
{
  "success": true,
  "embed_url": "http://taxsquare-grafana:3000/d/abc123?theme=dark&kiosk=tv&from=now-6h&to=now",
  "external_url": "http://localhost:3102/d/abc123?theme=dark&kiosk=tv&from=now-6h&to=now",
  "uid": "abc123",
  "theme": "dark",
  "refresh": null,
  "time_range": {
    "from": "now-6h",
    "to": "now"
  }
}
```

### Query Metrics

```http
POST /api/v1/monitoring/grafana/query
```

**Request Body**:
```json
{
  "datasource": "prometheus",
  "query": "cpu_usage",
  "from": "now-5m",
  "to": "now",
  "interval": "15s"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": {...}
  },
  "metadata": {
    "datasource": "prometheus",
    "query": "cpu_usage",
    "time_range": {
      "from": "now-5m",
      "to": "now"
    }
  }
}
```

### List Data Sources

```http
GET /api/v1/monitoring/grafana/datasources
```

**Response**:
```json
{
  "success": true,
  "count": 2,
  "datasources": [
    {
      "id": 1,
      "name": "Prometheus",
      "type": "prometheus",
      "url": "http://prometheus:9090",
      "is_default": true
    }
  ]
}
```

---

## Frontend Components

### GrafanaDashboard Component

Reusable embedded dashboard component.

**Location**: `/src/components/GrafanaDashboard.jsx`

**Usage**:

```jsx
import GrafanaDashboard from '../components/GrafanaDashboard';

function MyPage() {
  return (
    <GrafanaDashboard
      dashboardUid="system-metrics"
      height={600}
      theme="dark"
      refreshInterval={30}
      timeRange={{ from: 'now-1h', to: 'now' }}
      onError={(err) => console.error(err)}
      onLoad={() => console.log('Dashboard loaded')}
    />
  );
}
```

**Props**:
- `dashboardUid` (required): Grafana dashboard UID
- `height` (default: 600): iframe height in pixels
- `theme` (default: "dark"): "light" or "dark"
- `refreshInterval` (optional): Auto-refresh in seconds (e.g., 30, 60, 300)
- `timeRange` (default: { from: "now-6h", to: "now" }): Time range object
- `kiosk` (default: "tv"): Kiosk mode
- `onError` (optional): Error callback
- `onLoad` (optional): Load callback

### GrafanaViewer Page

Full dashboard viewer with controls.

**Location**: `/src/pages/GrafanaViewer.jsx`

**Features**:
- Dashboard selector dropdown
- Theme toggle (light/dark)
- Time range selector (5m to 7d)
- Auto-refresh interval selector (off, 30s, 1m, 5m, 15m)
- Fullscreen mode
- Direct link to Grafana

**Access**: `/admin/monitoring/grafana/dashboards`

### GrafanaConfig Page

Grafana connection and data source management.

**Location**: `/src/pages/GrafanaConfig.jsx`

**Features**:
- Connection settings
- Authentication (API key or username/password)
- Data source listing and creation
- Dashboard listing
- Health status display

**Access**: `/admin/monitoring/grafana`

---

## Configuration

### Time Range Options

| Label | Value | Description |
|-------|-------|-------------|
| Last 5 minutes | now-5m | Recent metrics |
| Last 15 minutes | now-15m | Short-term view |
| Last 1 hour | now-1h | Hourly view |
| Last 6 hours | now-6h | Default range |
| Last 24 hours | now-24h | Daily view |
| Last 7 days | now-7d | Weekly view |

### Refresh Intervals

| Interval | Use Case |
|----------|----------|
| Off | Manual refresh only |
| 30 seconds | Real-time monitoring |
| 1 minute | Active dashboards |
| 5 minutes | Standard monitoring |
| 15 minutes | Background monitoring |

### Theme Options

- **Dark Theme**: Default - easier on eyes, professional
- **Light Theme**: High contrast for presentations

---

## Dashboard Embedding

### Basic Embedding

```jsx
<GrafanaDashboard dashboardUid="abc123" />
```

### Custom Time Range

```jsx
<GrafanaDashboard
  dashboardUid="abc123"
  timeRange={{ from: 'now-24h', to: 'now' }}
/>
```

### Auto-Refresh

```jsx
<GrafanaDashboard
  dashboardUid="abc123"
  refreshInterval={60}  // Refresh every 60 seconds
/>
```

### Light Theme

```jsx
<GrafanaDashboard
  dashboardUid="abc123"
  theme="light"
/>
```

### Error Handling

```jsx
<GrafanaDashboard
  dashboardUid="abc123"
  onError={(error) => {
    console.error('Dashboard error:', error);
    alert('Failed to load dashboard');
  }}
  onLoad={() => {
    console.log('Dashboard loaded successfully');
  }}
/>
```

---

## Testing

### Running Tests

```bash
cd /opt/ops-center/backend

# Run Grafana API tests
python -m pytest tests/test_grafana_api.py -v

# Run with coverage
python -m pytest tests/test_grafana_api.py --cov=grafana_api --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ Health check (success and failure cases)
- ✅ Dashboard listing
- ✅ Dashboard retrieval by UID
- ✅ Dashboard not found errors
- ✅ Embed URL generation (dark/light themes)
- ✅ Refresh interval configuration
- ✅ Custom time ranges
- ✅ Data source listing
- ✅ Metric queries
- ✅ Error handling (401, 404, 500)
- ✅ Invalid input validation

**Expected Results**: 100% pass rate (all tests passing)

### Manual Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8084/api/v1/monitoring/grafana/health
   ```

2. **List Dashboards**:
   ```bash
   curl http://localhost:8084/api/v1/monitoring/grafana/dashboards
   ```

3. **Generate Embed URL**:
   ```bash
   curl "http://localhost:8084/api/v1/monitoring/grafana/dashboards/abc123/embed-url?theme=dark"
   ```

4. **Frontend Access**:
   - Open: https://unicorncommander.ai/admin/monitoring/grafana/dashboards
   - Select a dashboard from dropdown
   - Toggle theme, time range, refresh interval
   - Verify dashboard loads in iframe

---

## Troubleshooting

### Issue: "Grafana service is not reachable"

**Symptoms**: Health check returns `{"success": false, "status": "unreachable"}`

**Solutions**:

1. **Check if Grafana is running**:
   ```bash
   docker ps | grep grafana
   ```

2. **Check network connectivity**:
   ```bash
   docker exec ops-center-direct ping taxsquare-grafana
   ```

3. **Verify Grafana is on web network**:
   ```bash
   docker network inspect web | grep -A 10 taxsquare-grafana
   ```

4. **Restart Grafana**:
   ```bash
   docker restart taxsquare-grafana
   ```

### Issue: "Dashboard not found" (404 error)

**Symptoms**: `GET /dashboards/{uid}` returns 404

**Solutions**:

1. **List all dashboards to get correct UID**:
   ```bash
   curl http://localhost:8084/api/v1/monitoring/grafana/dashboards
   ```

2. **Check dashboard exists in Grafana UI**: http://localhost:3102

3. **Verify UID is correct** (case-sensitive)

### Issue: "Unauthorized" (401 error)

**Symptoms**: Operations requiring API key fail with 401

**Solutions**:

1. **Generate new API key** in Grafana UI (see Setup Instructions #3)

2. **Verify API key in .env.auth**:
   ```bash
   grep GRAFANA_API_KEY /opt/ops-center/.env.auth
   ```

3. **Restart Ops-Center** to load new key:
   ```bash
   docker restart ops-center-direct
   ```

### Issue: iframe doesn't load dashboard

**Symptoms**: Blank iframe or loading spinner never resolves

**Solutions**:

1. **Check browser console** for errors (CORS, connection refused)

2. **Verify external URL is accessible**:
   ```bash
   curl http://localhost:3102/api/health
   ```

3. **Try accessing Grafana directly**: http://localhost:3102

4. **Check firewall rules** (port 3102 must be open)

5. **Clear browser cache** and reload page

### Issue: "Connection timeout"

**Symptoms**: Requests hang for 30 seconds then fail

**Solutions**:

1. **Increase timeout in .env.auth**:
   ```bash
   GRAFANA_TIMEOUT=60  # Increase from 30 to 60 seconds
   ```

2. **Check Grafana resource usage**:
   ```bash
   docker stats taxsquare-grafana
   ```

3. **Restart both services**:
   ```bash
   docker restart taxsquare-grafana ops-center-direct
   ```

---

## Best Practices

### Security

1. **API Key Rotation**: Generate new API keys every 90 days
2. **Least Privilege**: Use Viewer role unless Admin operations needed
3. **Environment Variables**: Never commit API keys to git
4. **HTTPS Only**: Use SSL/TLS in production environments

### Performance

1. **Caching**: Dashboard metadata is cached for 5 minutes
2. **Time Ranges**: Use shorter ranges for faster queries (e.g., now-1h vs now-7d)
3. **Refresh Intervals**: Use longer intervals (5m+) for background monitoring
4. **Dashboard Panels**: Limit panels to 10-15 per dashboard for best performance

### Dashboard Design

1. **Naming Convention**: Use descriptive UIDs (e.g., `system-cpu`, `network-traffic`)
2. **Tags**: Tag dashboards for easy categorization
3. **Variables**: Use Grafana template variables for flexibility
4. **Alerts**: Configure alerts in Grafana for critical metrics

### Monitoring

1. **Health Checks**: Monitor Grafana health endpoint every 5 minutes
2. **Error Tracking**: Log all API errors for debugging
3. **Usage Analytics**: Track which dashboards are most viewed
4. **Version Updates**: Keep Grafana updated (currently on 12.2.0)

---

## Additional Resources

### Grafana Documentation
- **API Reference**: https://grafana.com/docs/grafana/latest/developers/http_api/
- **Dashboard JSON Model**: https://grafana.com/docs/grafana/latest/dashboards/json-model/
- **Provisioning**: https://grafana.com/docs/grafana/latest/administration/provisioning/

### Ops-Center Documentation
- **Main README**: `/services/ops-center/README.md`
- **API Documentation**: `/services/ops-center/docs/API_REFERENCE.md`
- **CLAUDE.md**: `/services/ops-center/CLAUDE.md`

### Support

For issues or questions:
1. Check this documentation
2. Review Grafana logs: `docker logs taxsquare-grafana`
3. Review Ops-Center logs: `docker logs ops-center-direct`
4. Consult Grafana official documentation
5. File issue in UC-Cloud repository

---

**Document Version**: 1.0.0
**Last Updated**: November 29, 2025
**Maintained By**: Ops-Center Development Team
