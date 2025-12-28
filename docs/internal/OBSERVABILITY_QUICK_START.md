# Ops-Center Observability - Quick Start Guide

**Time to Implement**: 15 minutes
**Difficulty**: Easy
**Impact**: Immediate visibility into all operations

---

## What You'll Get

After following this guide, you'll have:

✅ **Structured JSON logging** with correlation IDs and PII redaction
✅ **40+ Prometheus metrics** at `/metrics` endpoint
✅ **Health check endpoints** at `/health`, `/health/ready`, `/health/detailed`
✅ **Distributed tracing** (optional, configurable)
✅ **50+ alerting rules** ready for Prometheus AlertManager

---

## Step 1: Install Dependencies (2 minutes)

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
pip install -r requirements.txt
```

This installs:
- OpenTelemetry packages for distributed tracing
- (Prometheus client already installed)

---

## Step 2: Update server.py (5 minutes)

### Option A: Minimal Integration (Recommended for Quick Start)

Add **3 lines** to `backend/server.py`:

```python
from observability import setup_observability

app = FastAPI(title="Ops-Center API")

# Add this single line:
setup_observability(app)

# Continue with existing routes...
```

That's it! You now have:
- ✅ Structured logging
- ✅ Metrics at /metrics
- ✅ Health checks at /health/*
- ✅ Automatic HTTP metrics

### Option B: Full Integration (Recommended for Production)

Add correlation ID middleware for request tracing:

```python
from fastapi import FastAPI, Request
from observability import setup_observability, get_logger, log_context
import uuid

logger = get_logger(__name__)

app = FastAPI(title="Ops-Center API")

# Setup observability
observability_config = setup_observability(app)
logger.info("Observability initialized", config=observability_config)

# Add correlation ID middleware
@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    with log_context(correlation_id=correlation_id):
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Continue with existing routes...
```

---

## Step 3: Configure Environment (3 minutes)

Add to `.env.auth`:

```bash
# Logging level
LOG_LEVEL=INFO

# Tracing (optional - set to 'console' for development, 'jaeger' for production)
OTEL_EXPORTER_TYPE=console

# Service info (optional but recommended)
OPS_CENTER_VERSION=2.3.0
ENVIRONMENT=production
```

---

## Step 4: Restart Service (1 minute)

```bash
docker restart ops-center-direct
```

---

## Step 5: Verify It's Working (4 minutes)

### Test 1: Health Checks

```bash
# Liveness check
curl http://localhost:8084/health

# Expected output:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-12T10:30:45.123456Z",
#   "service": "ops-center",
#   "version": "2.3.0"
# }

# Readiness check
curl http://localhost:8084/health/ready

# Detailed health
curl http://localhost:8084/health/detailed | jq
```

### Test 2: Metrics

```bash
# View all metrics
curl http://localhost:8084/metrics

# Check for specific metrics
curl http://localhost:8084/metrics | grep ops_center_http_requests_total
```

### Test 3: Structured Logs

```bash
# View recent logs (should be JSON format)
docker logs ops-center-direct --tail 20

# Expected format:
# {
#   "timestamp": "2025-11-12T10:30:45.123456Z",
#   "level": "INFO",
#   "logger": "backend.server",
#   "message": "Application startup",
#   "correlation_id": null,
#   "user_id": null
# }
```

### Test 4: Generate Traffic

```bash
# Make requests to generate metrics
curl http://localhost:8084/api/v1/admin/users
curl http://localhost:8084/api/v1/billing/plans

# Check metrics updated
curl http://localhost:8084/metrics | grep ops_center_http_requests_total
# Should show increased counters
```

---

## Success! What's Next?

### Immediate Benefits (No Additional Work)

You now have:
- **Structured logging** - All logs in JSON format with metadata
- **Automatic HTTP metrics** - Request counts, latency, errors by endpoint
- **Health checks** - Kubernetes-compatible liveness/readiness probes
- **Correlation IDs** - Track requests across services (if Option B used)

### Optional: Setup Monitoring Stack (Recommended)

#### Prometheus + Grafana (15 minutes)

1. **Start Prometheus**:
```bash
docker run -d -p 9090:9090 \
  -v /home/muut/Production/UC-Cloud/services/ops-center/config/alerting_rules.yml:/etc/prometheus/rules.yml \
  prom/prometheus \
  --config.file=/etc/prometheus/prometheus.yml
```

2. **Configure scraping** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'ops-center'
    static_configs:
      - targets: ['host.docker.internal:8084']
```

3. **Start Grafana**:
```bash
docker run -d -p 3000:3000 grafana/grafana
```

4. **Add Prometheus data source** in Grafana at http://localhost:3000

#### Jaeger (Distributed Tracing) (5 minutes)

1. **Start Jaeger**:
```bash
docker run -d \
  -p 16686:16686 \
  -p 6831:6831/udp \
  jaegertracing/all-in-one:latest
```

2. **Update `.env.auth`**:
```bash
OTEL_EXPORTER_TYPE=jaeger
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

3. **Restart Ops-Center**:
```bash
docker restart ops-center-direct
```

4. **View traces** at http://localhost:16686

---

## Usage Examples

### Log Business Events

```python
from observability import get_logger

logger = get_logger(__name__)

logger.business_event(
    "credit_purchase",
    user_id="user123",
    amount=1000,
    payment_method="stripe"
)
```

### Record Custom Metrics

```python
from observability import metrics

metrics.credit_balance.labels(
    user_id="user123",
    organization_id="org456",
    tier="professional"
).set(8543)
```

### Trace Functions

```python
from observability import trace_request, add_span_attribute

@trace_request("process_payment")
async def process_payment(user_id: str, amount: float):
    add_span_attribute("payment.amount", amount)
    # ... payment logic
    return result
```

### Use Log Context

```python
from observability import log_context

with log_context(correlation_id="abc123", user_id="user456"):
    logger.info("Processing request")
    # All logs in this block include correlation_id and user_id
```

---

## Troubleshooting

### Logs Not in JSON Format

**Check**:
```bash
docker logs ops-center-direct | head -5
```

**Fix**:
- Verify `setup_observability(app)` was called
- Check for import errors in logs

### Metrics Endpoint 404

**Check**:
```bash
curl -I http://localhost:8084/metrics
```

**Fix**:
- Verify observability was setup before routes
- Check app startup logs for errors

### Health Checks Return 503

**Check**:
```bash
curl http://localhost:8084/health/detailed | jq '.checks'
```

**Common Issues**:
- PostgreSQL not running: `docker ps | grep postgresql`
- Redis not running: `docker ps | grep redis`
- Keycloak not running: `docker ps | grep keycloak`

### No Traces in Jaeger

**Check**:
```bash
docker exec ops-center-direct printenv | grep OTEL
```

**Fix**:
- Verify `OTEL_EXPORTER_TYPE=jaeger`
- Check Jaeger is running: `docker ps | grep jaeger`
- Verify Jaeger port: `curl http://localhost:16686`

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `OTEL_EXPORTER_TYPE` | `console` | Tracing exporter (console, jaeger, otlp) |
| `JAEGER_AGENT_HOST` | `localhost` | Jaeger agent hostname |
| `JAEGER_AGENT_PORT` | `6831` | Jaeger agent port |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP exporter endpoint |
| `OPS_CENTER_VERSION` | `2.3.0` | Service version |
| `GIT_COMMIT` | `unknown` | Git commit hash |
| `BUILD_DATE` | `unknown` | Build date |
| `ENVIRONMENT` | `production` | Environment (production, staging, development) |

### Health Check Endpoints

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `GET /health` | Liveness | Kubernetes liveness probe |
| `GET /health/ready` | Readiness | Kubernetes readiness probe, load balancer |
| `GET /health/detailed` | Diagnostics | Admin dashboard, debugging |

### Metrics Endpoint

| Endpoint | Format | Description |
|----------|--------|-------------|
| `GET /metrics` | Prometheus | All metrics in Prometheus exposition format |

---

## Next Steps

1. **Read Full Documentation**: `docs/OBSERVABILITY_GUIDE.md` (80+ pages)
2. **Review Implementation**: `OBSERVABILITY_IMPLEMENTATION_SUMMARY.md`
3. **Check Examples**: `backend/observability/INTEGRATION_EXAMPLE.py`
4. **Setup Alerting**: Import `config/alerting_rules.yml` to Prometheus
5. **Create Dashboards**: Build Grafana dashboards for your metrics

---

## Support

- **Full Documentation**: `/docs/OBSERVABILITY_GUIDE.md`
- **Implementation Summary**: `/OBSERVABILITY_IMPLEMENTATION_SUMMARY.md`
- **Integration Examples**: `/backend/observability/INTEGRATION_EXAMPLE.py`
- **Alert Rules**: `/config/alerting_rules.yml`

---

## Summary

**What You Did** (15 minutes):
1. ✅ Installed dependencies
2. ✅ Added 1 line to server.py
3. ✅ Configured environment variables
4. ✅ Restarted service
5. ✅ Verified it's working

**What You Got**:
- ✅ Structured JSON logging with PII redaction
- ✅ 40+ Prometheus metrics
- ✅ 3 health check endpoints
- ✅ Distributed tracing support (optional)
- ✅ 50+ pre-configured alerting rules

**ROI**: Production-grade observability with minimal integration effort!

---

**Quick Start Version**: 1.0
**Last Updated**: November 12, 2025
**Estimated Time**: 15 minutes
**Status**: Ready to Use
