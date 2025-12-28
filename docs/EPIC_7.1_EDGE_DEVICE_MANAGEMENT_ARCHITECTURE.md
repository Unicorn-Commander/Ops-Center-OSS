# Epic 7.1: Edge Device Management Architecture
**Status**: Planning Phase
**Priority**: Medium
**Timeline**: Q1 2026 (Estimated)
**Team**: Strategic Planning

---

## Executive Summary

Epic 7.1 introduces **Edge Device Management** capabilities to Ops-Center, enabling centralized monitoring, configuration, and orchestration of distributed edge computing nodes. This feature is critical for enterprise deployments where UC-Cloud components run on customer premises, IoT gateways, or remote data centers.

**Key Capabilities**:
- Device registration and provisioning
- Real-time health monitoring
- Remote configuration management
- Over-the-air (OTA) updates
- Edge-to-cloud synchronization
- Multi-tenancy support

---

## Business Justification

### Market Need
1. **Enterprise Deployments**: Customers deploying UC-1-Pro on premise
2. **IoT Integration**: AI inference at the edge for low-latency applications
3. **Compliance**: Data residency requirements (EU, healthcare, finance)
4. **Cost Optimization**: Reduce cloud bandwidth costs by processing at edge

### Revenue Impact
- **Target Audience**: Enterprise customers with >10 edge devices
- **Pricing Model**: $50/month/device + $500/month management fee
- **Market Size**: Estimated 200 enterprise customers → $1.2M ARR

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Ops-Center (Cloud)                        │
│         Central Management & Orchestration Hub               │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
    ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
    │  Edge     │ │  Edge   │ │  Edge    │
    │ Device 1  │ │ Device 2│ │ Device N │
    │ (UC-1-Pro)│ │(Gateway)│ │(Custom)  │
    └───────────┘ └─────────┘ └──────────┘
          │            │            │
    ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
    │  Local    │ │ Local  │ │ Local    │
    │  Services │ │Services│ │ Services │
    └───────────┘ └────────┘ └──────────┘
```

### Data Flow

1. **Device Registration**: Edge device sends registration request → Ops-Center
2. **Authentication**: Ops-Center validates device credentials → Issues JWT token
3. **Heartbeat**: Edge device sends status every 30 seconds → Ops-Center updates dashboard
4. **Configuration Push**: Admin updates config in Ops-Center → Pushed to edge devices
5. **Telemetry Collection**: Edge devices stream metrics → Ops-Center aggregates
6. **OTA Updates**: Ops-Center deploys updates → Edge devices apply and restart

---

## Database Schema

### New Tables

```sql
-- Edge Devices Registry
CREATE TABLE edge_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,  -- 'uc1-pro', 'gateway', 'custom'
    organization_id UUID NOT NULL REFERENCES organizations(id),
    registration_token VARCHAR(255) UNIQUE,
    device_id VARCHAR(255) UNIQUE NOT NULL,  -- Hardware ID
    ip_address INET,
    last_seen TIMESTAMP,
    status VARCHAR(20) DEFAULT 'offline',  -- 'online', 'offline', 'maintenance', 'error'
    firmware_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(organization_id, device_name)
);

CREATE INDEX idx_edge_devices_org ON edge_devices(organization_id);
CREATE INDEX idx_edge_devices_status ON edge_devices(status);
CREATE INDEX idx_edge_devices_last_seen ON edge_devices(last_seen DESC);

-- Device Configuration
CREATE TABLE device_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES edge_devices(id) ON DELETE CASCADE,
    config_version INT NOT NULL DEFAULT 1,
    config_data JSONB NOT NULL,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES keycloak_users(id),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_device_config_device ON device_configurations(device_id, config_version DESC);

-- Device Metrics (Time-Series Data)
CREATE TABLE device_metrics (
    id BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL REFERENCES edge_devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL,  -- 'cpu', 'memory', 'disk', 'network', 'gpu'
    metric_value JSONB NOT NULL,
    INDEX idx_device_metrics_device_time (device_id, timestamp DESC)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE device_metrics_2025_11 PARTITION OF device_metrics
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Device Logs
CREATE TABLE device_logs (
    id BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL REFERENCES edge_devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    log_level VARCHAR(20) NOT NULL,  -- 'debug', 'info', 'warning', 'error', 'critical'
    service_name VARCHAR(100),
    message TEXT NOT NULL,
    metadata JSONB
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_device_logs_device_time ON device_logs(device_id, timestamp DESC);
CREATE INDEX idx_device_logs_level ON device_logs(log_level);

-- OTA Update Deployments
CREATE TABLE ota_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_name VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    target_version VARCHAR(50) NOT NULL,
    rollout_strategy VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'canary', 'rolling', 'immediate'
    rollout_percentage INT DEFAULT 100,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed', 'paused'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES keycloak_users(id),
    metadata JSONB
);

CREATE TABLE ota_deployment_devices (
    deployment_id UUID NOT NULL REFERENCES ota_deployments(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES edge_devices(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'downloading', 'installing', 'completed', 'failed', 'skipped'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    PRIMARY KEY (deployment_id, device_id)
);

CREATE INDEX idx_ota_deployment_devices ON ota_deployment_devices(deployment_id, status);
```

---

## API Endpoints

### Device Management

```python
# Device Registration
POST /api/v1/edge/devices/register
{
  "device_name": "warehouse-gateway-01",
  "device_type": "uc1-pro",
  "hardware_id": "ABCD-1234-EFGH-5678",
  "firmware_version": "2.1.0",
  "registration_token": "TOKEN_FROM_OPS_CENTER"
}
→ Returns: device_id, auth_token

# List Devices (Admin)
GET /api/v1/admin/edge/devices?org_id={org_id}&status={status}&page={page}
→ Returns: paginated device list

# Device Detail (Admin)
GET /api/v1/admin/edge/devices/{device_id}
→ Returns: device info, current config, recent metrics

# Update Device (Admin)
PUT /api/v1/admin/edge/devices/{device_id}
{
  "device_name": "updated-name",
  "status": "maintenance"
}

# Delete Device (Admin)
DELETE /api/v1/admin/edge/devices/{device_id}

# Device Heartbeat (Device → Cloud)
POST /api/v1/edge/devices/{device_id}/heartbeat
{
  "status": "online",
  "uptime": 86400,
  "services": [
    {"name": "vllm", "status": "running"},
    {"name": "open-webui", "status": "running"}
  ],
  "metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_percent": 32.1
  }
}
→ Returns: ack, any pending config updates
```

### Configuration Management

```python
# Get Active Config (Device → Cloud)
GET /api/v1/edge/devices/{device_id}/config
→ Returns: current configuration (JSON)

# Push Config (Admin → Device)
POST /api/v1/admin/edge/devices/{device_id}/config
{
  "config_data": {
    "vllm": {
      "model": "Qwen/Qwen2.5-32B-Instruct-AWQ",
      "gpu_memory_util": 0.90
    },
    "services": {
      "open-webui": true,
      "center-deep": false
    }
  },
  "apply_immediately": true
}
→ Returns: config_version

# Config History (Admin)
GET /api/v1/admin/edge/devices/{device_id}/config/history
→ Returns: list of config versions

# Rollback Config (Admin)
POST /api/v1/admin/edge/devices/{device_id}/config/rollback
{
  "config_version": 42
}
```

### Metrics & Monitoring

```python
# Stream Metrics (Device → Cloud)
POST /api/v1/edge/devices/{device_id}/metrics
{
  "metrics": [
    {
      "timestamp": "2025-10-28T06:00:00Z",
      "metric_type": "cpu",
      "value": {"percent": 45.2, "cores": 32}
    },
    {
      "timestamp": "2025-10-28T06:00:00Z",
      "metric_type": "gpu",
      "value": {"utilization": 89.5, "memory_used": 28672, "temperature": 72}
    }
  ]
}

# Query Metrics (Admin)
GET /api/v1/admin/edge/devices/{device_id}/metrics?metric_type={type}&from={timestamp}&to={timestamp}
→ Returns: time-series metrics data

# Get Device Logs (Admin)
GET /api/v1/admin/edge/devices/{device_id}/logs?level={level}&service={service}&limit={limit}
→ Returns: paginated logs
```

### OTA Updates

```python
# Create Deployment (Admin)
POST /api/v1/admin/edge/ota/deployments
{
  "deployment_name": "Firmware Update 2.2.0",
  "organization_id": "org-uuid",
  "target_version": "2.2.0",
  "device_filters": {
    "current_version": "<2.2.0",
    "device_type": "uc1-pro"
  },
  "rollout_strategy": "canary",
  "rollout_percentage": 10
}
→ Returns: deployment_id

# Start Deployment (Admin)
POST /api/v1/admin/edge/ota/deployments/{deployment_id}/start

# Pause/Resume Deployment (Admin)
POST /api/v1/admin/edge/ota/deployments/{deployment_id}/pause
POST /api/v1/admin/edge/ota/deployments/{deployment_id}/resume

# Deployment Status (Admin)
GET /api/v1/admin/edge/ota/deployments/{deployment_id}
→ Returns: deployment status, device-by-device progress

# Check for Updates (Device → Cloud)
GET /api/v1/edge/devices/{device_id}/updates
→ Returns: available updates, download URLs

# Report Update Status (Device → Cloud)
POST /api/v1/edge/devices/{device_id}/updates/{update_id}/status
{
  "status": "completed",
  "new_version": "2.2.0",
  "install_duration_seconds": 120
}
```

---

## Security Model

### Authentication & Authorization

#### Device Authentication
1. **Registration Token**: One-time token generated by admin
2. **Device Certificate**: X.509 certificate issued upon registration
3. **JWT Token**: Short-lived tokens (1 hour) refreshed via heartbeat

```python
# Device authentication flow
from cryptography import x509
from cryptography.hazmat.primitives import hashes

def register_device(hardware_id: str, registration_token: str):
    # Validate registration token
    if not validate_token(registration_token):
        raise HTTPException(401, "Invalid registration token")

    # Generate device certificate
    cert = generate_device_certificate(hardware_id)

    # Create device record
    device = await db.create_device(hardware_id, cert)

    # Issue JWT token
    jwt_token = create_jwt(device.id, expires_in=3600)

    return {
        "device_id": device.id,
        "certificate": cert.public_bytes(),
        "jwt_token": jwt_token
    }
```

#### Admin Authorization
- **System Admin**: Full access to all devices
- **Org Admin**: Access to organization's devices only
- **Org Member**: Read-only access to organization's devices

```python
@app.get("/api/v1/admin/edge/devices")
async def list_devices(
    org_id: str = None,
    current_user: User = Depends(get_current_user)
):
    # System admin can see all devices
    if current_user.has_role("admin"):
        return await db.get_all_devices(org_id)

    # Org admin can see their org's devices
    elif current_user.has_role("org_admin"):
        return await db.get_org_devices(current_user.org_id)

    else:
        raise HTTPException(403, "Insufficient permissions")
```

### Data Encryption

#### In Transit
- **TLS 1.3**: All device-to-cloud communication encrypted
- **mTLS**: Mutual TLS for device authentication
- **VPN Option**: Optional WireGuard VPN for added security

#### At Rest
- **Config Data**: Encrypted with org-specific keys
- **Sensitive Logs**: PII/secrets redacted before storage
- **Credentials**: Stored in HashiCorp Vault or AWS Secrets Manager

---

## Edge Device Agent

### Agent Architecture

```
┌─────────────────────────────────────────────────┐
│         Edge Device Agent (Python)              │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Heartbeat   │  │  Config      │            │
│  │  Manager     │  │  Watcher     │            │
│  └──────┬───────┘  └───────┬──────┘            │
│         │                  │                    │
│  ┌──────▼──────────────────▼──────┐            │
│  │      Cloud Sync Service        │            │
│  └──────┬─────────────────────────┘            │
│         │                                       │
│  ┌──────▼──────┐  ┌──────────────┐            │
│  │  Metrics    │  │  OTA Update  │            │
│  │  Collector  │  │  Manager     │            │
│  └──────┬──────┘  └──────┬───────┘            │
│         │                │                    │
│  ┌──────▼────────────────▼───────┐            │
│  │     Local Services Layer      │            │
│  │  (Docker, vLLM, Open-WebUI)   │            │
│  └───────────────────────────────┘            │
└─────────────────────────────────────────────────┘
```

### Agent Implementation

```python
# edge_agent/main.py
import asyncio
import aiohttp
from datetime import datetime

class EdgeAgent:
    def __init__(self, device_id: str, auth_token: str, cloud_url: str):
        self.device_id = device_id
        self.auth_token = auth_token
        self.cloud_url = cloud_url
        self.heartbeat_interval = 30  # seconds
        self.config_version = None

    async def start(self):
        await asyncio.gather(
            self.heartbeat_loop(),
            self.config_watcher(),
            self.metrics_collector(),
            self.update_checker()
        )

    async def heartbeat_loop(self):
        while True:
            try:
                # Collect current status
                status = await self.collect_status()

                # Send to cloud
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.cloud_url}/api/v1/edge/devices/{self.device_id}/heartbeat",
                        json=status,
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    ) as resp:
                        data = await resp.json()

                        # Check for pending config updates
                        if data.get("pending_config"):
                            await self.apply_config(data["pending_config"])

            except Exception as e:
                print(f"Heartbeat failed: {e}")

            await asyncio.sleep(self.heartbeat_interval)

    async def collect_status(self):
        return {
            "status": "online",
            "uptime": self.get_uptime(),
            "services": await self.check_services(),
            "metrics": await self.collect_metrics()
        }

    async def apply_config(self, new_config):
        # Backup current config
        await self.backup_config()

        # Apply new configuration
        try:
            await self.update_docker_compose(new_config)
            await self.restart_services()
            self.config_version = new_config["version"]
        except Exception as e:
            # Rollback on failure
            await self.rollback_config()
            raise e
```

### Agent Installation Script

```bash
#!/bin/bash
# install_edge_agent.sh

set -e

CLOUD_URL="https://your-domain.com"
REGISTRATION_TOKEN="$1"

if [ -z "$REGISTRATION_TOKEN" ]; then
    echo "Usage: ./install_edge_agent.sh <REGISTRATION_TOKEN>"
    exit 1
fi

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip docker.io

# Download agent
curl -fsSL ${CLOUD_URL}/downloads/edge-agent-latest.tar.gz | tar -xz
cd edge-agent

# Install Python dependencies
pip3 install -r requirements.txt

# Register device
python3 register.py --token "$REGISTRATION_TOKEN" --cloud-url "$CLOUD_URL"

# Start agent service
cp edge-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable edge-agent
systemctl start edge-agent

echo "Edge agent installed and running!"
echo "Device ID: $(cat /etc/edge-agent/device_id)"
```

---

## Frontend Components

### Device Management Dashboard

**Location**: `/admin/edge/devices`

**Components**:
1. **Device List Table**
   - Columns: Name, Type, Status, Last Seen, Firmware, Actions
   - Filters: Organization, Status, Type
   - Bulk Actions: Update Config, Deploy OTA, Restart

2. **Device Detail Page** (`/admin/edge/devices/{id}`)
   - **Overview Tab**: Basic info, current status
   - **Metrics Tab**: CPU, Memory, GPU charts (Chart.js)
   - **Logs Tab**: Real-time log viewer
   - **Configuration Tab**: Config editor (JSON or YAML)
   - **Updates Tab**: OTA deployment history

3. **Device Map View** (Stretch Goal)
   - Geographic map showing device locations
   - Status indicators (online/offline/error)
   - Click to view device details

### OTA Deployment Wizard

**Location**: `/admin/edge/ota/deploy`

**Steps**:
1. **Select Devices**: Filter by org, type, version
2. **Choose Update**: Select firmware version
3. **Rollout Strategy**: Immediate, Canary, Rolling
4. **Schedule**: Now or specific time
5. **Confirmation**: Review and deploy

---

## Integration Points

### 1. Keycloak SSO
- Device management requires admin role
- Org admins see only their devices
- Audit logs track all device operations

### 2. Lago Billing
- Device usage tracked per organization
- Billing meter: `edge_device_hours`
- Pricing: $50/device/month

### 3. Grafana Monitoring
- Device metrics exported to Prometheus
- Pre-built Grafana dashboards
- Alerts for offline devices, high resource usage

### 4. Brigade (Agent Orchestration)
- Brigade agents can be deployed to edge devices
- Remote agent execution via Ops-Center
- Centralized agent management

---

## Deployment Strategy

### Phase 1: Foundation (Month 1-2)
- [ ] Database schema implementation
- [ ] Core API endpoints (register, heartbeat, config)
- [ ] Basic edge agent (Python)
- [ ] Admin UI: Device list and detail pages

### Phase 2: Monitoring (Month 3)
- [ ] Metrics collection and storage
- [ ] Log aggregation
- [ ] Real-time device status dashboard
- [ ] Grafana integration

### Phase 3: Updates (Month 4)
- [ ] OTA update framework
- [ ] Deployment wizard UI
- [ ] Rollout strategies (canary, rolling)
- [ ] Update verification and rollback

### Phase 4: Advanced Features (Month 5-6)
- [ ] Device grouping and tags
- [ ] Custom metrics and alerts
- [ ] Remote shell access (secure)
- [ ] Device provisioning automation
- [ ] Geographic map view

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Device Registration Time | < 5 minutes | Time from token generation to first heartbeat |
| Heartbeat Latency | < 500ms | 95th percentile response time |
| Config Apply Time | < 30 seconds | Time from push to applied |
| OTA Success Rate | > 95% | Successful updates / total updates |
| Dashboard Load Time | < 2 seconds | Time to fully render device list |
| Device Uptime | > 99.5% | (Total time - downtime) / total time |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Network connectivity issues | High | Medium | Offline mode with queued updates |
| Failed OTA updates brick device | Critical | Low | Dual-boot system with rollback |
| Scalability (10,000+ devices) | High | Medium | Time-series DB (TimescaleDB) for metrics |
| Security vulnerabilities | Critical | Low | Regular security audits, mTLS |
| Complex multi-tenancy | Medium | Medium | Thorough testing, org isolation |

---

## Future Enhancements (Post-Launch)

1. **AI-Powered Anomaly Detection**
   - Automatically detect abnormal device behavior
   - Predict failures before they occur

2. **Edge-to-Edge Communication**
   - Devices communicate directly (P2P)
   - Distributed workload orchestration

3. **Mobile App**
   - iOS/Android app for device management
   - Push notifications for alerts

4. **Advanced Analytics**
   - Device performance trends
   - Cost optimization recommendations
   - Capacity planning tools

5. **Marketplace**
   - Community-contributed device configs
   - Third-party integrations

---

## Conclusion

Epic 7.1 positions Ops-Center as a **comprehensive edge device management platform**, enabling enterprise customers to deploy and manage UC-Cloud infrastructure at scale. With robust monitoring, secure OTA updates, and multi-tenancy support, this feature unlocks significant revenue opportunities in the enterprise market.

**Next Steps**:
1. Review and approve architecture
2. Create detailed technical specifications
3. Assign development team
4. Begin Phase 1 implementation

**Estimated LOE**: 6 months (3 full-time engineers)
**Estimated Cost**: $300K (development + testing)
**Projected Revenue**: $1.2M ARR (Year 1), $5M ARR (Year 3)

---

**Document Owner**: Strategic Planning Team
**Last Updated**: 2025-10-28
**Status**: Architecture Review Pending
