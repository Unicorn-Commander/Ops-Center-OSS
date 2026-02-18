# GPU Services Management - Ops-Center

**Last Updated**: January 25, 2026
**Feature**: Unified GPU Services Management Page
**Route**: `/admin/system/gpu-services`

---

## Overview

The GPU Services Management page provides a unified interface for managing all GPU-accelerated inference services across the Magic Unicorn infrastructure.

### Services Managed

| Category | Services | Server | Idle Timeout |
|----------|----------|--------|--------------|
| **RAG Services** | Embeddings, Reranker | your-domain.com | 30 minutes |
| **Extraction Services** | Granite 1, Granite 2 | your-domain.com | 5 minutes |

---

## Features

### 1. Service Status Dashboard

View real-time status for all GPU services:
- **Running/Stopped** status with color-coded indicators
- **Model name** currently loaded
- **Container name** for each service
- **Last activity** timestamp (e.g., "45s ago", "5m ago")

### 2. Manual Start/Stop Controls

Each service has dedicated Start/Stop buttons:
- **Start**: Manually start a stopped container
- **Stop**: Manually stop a running container
- Buttons show loading state during operations
- Success/error notifications after operations

### 3. GPU Memory Panel

Visual representation of GPU memory usage:
- Progress bars for each GPU (GPU 0, GPU 1)
- Color coding: Green (<70%), Orange (70-90%), Red (>90%)
- Shows used/total MB and percentage
- Total memory summary across all GPUs

### 4. Configuration Section

View current configuration:
- Infinity idle timeout (default: 1800 seconds / 30 minutes)
- Granite idle timeout (default: 300 seconds / 5 minutes)
- Proxy URLs for each service
- Last status update timestamp

### 5. Auto-Refresh

Status automatically refreshes every 30 seconds. Manual refresh button available for immediate updates.

---

## API Endpoints

### Base URL
```
https://unicorncommander.ai/api/v1/gpu-services
```

### Authentication
All endpoints require authentication via Keycloak SSO session cookie.

### Endpoints

#### Get All Services Status
```http
GET /api/v1/gpu-services/status
```

**Response:**
```json
{
  "infinity_proxy": {
    "healthy": true,
    "idle_timeout_seconds": 1800,
    "services": {
      "embeddings": {
        "container": "unicorn-embeddings",
        "running": true,
        "last_activity_seconds_ago": 120,
        "upstream": "http://unicorn-embeddings:7997",
        "service_status": "healthy"
      },
      "reranker": {
        "container": "unicorn-reranker",
        "running": false,
        "last_activity_seconds_ago": null,
        "upstream": "http://unicorn-reranker:7997",
        "service_status": "stopped"
      }
    }
  },
  "granite_proxy": {
    "healthy": true,
    "idle_timeout_seconds": 300,
    "services": {
      "granite1": {
        "container": "unicorn-granite-extraction",
        "running": true,
        "last_activity_seconds_ago": 45,
        "upstream": "http://unicorn-granite-extraction:8080"
      },
      "granite2": {
        "container": "unicorn-granite-extraction-2",
        "running": false,
        "last_activity_seconds_ago": null,
        "upstream": "http://unicorn-granite-extraction-2:8080"
      }
    }
  },
  "gpu_info": {
    "gpus": [
      {
        "index": 0,
        "name": "Tesla P40",
        "memory_used_mb": 4500,
        "memory_total_mb": 24576,
        "memory_free_mb": 20076,
        "utilization_percent": 18
      },
      {
        "index": 1,
        "name": "Tesla P40",
        "memory_used_mb": 8000,
        "memory_total_mb": 24576,
        "memory_free_mb": 16576,
        "utilization_percent": 32
      }
    ],
    "total_memory_mb": 49152,
    "used_memory_mb": 12500,
    "free_memory_mb": 36652
  },
  "last_updated": "2026-01-25T22:30:00Z"
}
```

#### Start a Service
```http
POST /api/v1/gpu-services/{service}/start
```

**Path Parameters:**
- `service`: One of `embeddings`, `reranker`, `granite1`, `granite2`

**Response:**
```json
{
  "success": true,
  "message": "Container unicorn-embeddings started successfully",
  "service": "embeddings",
  "operation": "start"
}
```

#### Stop a Service
```http
POST /api/v1/gpu-services/{service}/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Container unicorn-embeddings stopped successfully",
  "service": "embeddings",
  "operation": "stop"
}
```

#### Get GPU Memory Info
```http
GET /api/v1/gpu-services/gpu
```

**Response:**
```json
{
  "gpus": [
    {
      "index": 0,
      "name": "Tesla P40",
      "memory_used_mb": 4500,
      "memory_total_mb": 24576,
      "memory_free_mb": 20076,
      "utilization_percent": 18
    }
  ],
  "total_memory_mb": 49152,
  "used_memory_mb": 12500,
  "free_memory_mb": 36652
}
```

---

## Architecture

### Proxy Configuration

The GPU Services API communicates with two idle-management proxies:

| Proxy | URL | Port | Manages |
|-------|-----|------|---------|
| Infinity Proxy | `http://unicorn-infinity-proxy:8080` | 8086 | Embeddings, Reranker |
| Granite Proxy | `http://unicorn-granite-proxy:8080` | 8089 | Granite 1, Granite 2 |

### Environment Variables

```bash
# Ops-Center Backend
INFINITY_PROXY_URL=http://unicorn-infinity-proxy:8080
GRANITE_PROXY_URL=http://unicorn-granite-proxy:8080
```

### Network Requirements

The Ops-Center backend must be able to reach both proxies on the Docker network. Ensure:
- `ops-center-direct` container is on `unicorn-network`
- Proxies are accessible from Ops-Center

---

## Files

### Backend

| File | Description |
|------|-------------|
| `backend/routers/gpu_services.py` | Main API router |
| `backend/routers/rag_services.py` | Legacy RAG-only API (still functional) |

### Frontend

| File | Description |
|------|-------------|
| `src/pages/admin/GPUServicesManagement.jsx` | Main management page |
| `src/pages/admin/RAGServicesManagement.jsx` | Legacy RAG-only page |

### Navigation

The GPU Services link is in the sidebar under **AI/ML** section:
- **Location**: `src/components/Layout.jsx`
- **Route**: `/admin/system/gpu-services`
- **Icon**: `CpuChipIcon`

---

## Troubleshooting

### "Infinity Proxy not available"

The Ops-Center cannot reach the Infinity proxy.

**Solutions:**
1. Check if proxy is running: `docker ps | grep infinity-proxy`
2. Check proxy logs: `docker logs unicorn-infinity-proxy`
3. Verify network connectivity from Ops-Center container

### "Granite Proxy not available"

The Ops-Center cannot reach the Granite proxy.

**Solutions:**
1. Check if proxy is running: `docker ps | grep granite-proxy`
2. Check proxy logs: `docker logs unicorn-granite-proxy`
3. Verify the Granite proxy is on `unicorn-network`

### Start/Stop Operations Fail

**Solutions:**
1. Check proxy logs for errors
2. Verify Docker socket is mounted in proxy containers
3. Check container exists: `docker ps -a | grep <container-name>`

### GPU Info Not Available

The `nvidia-smi` command is not accessible.

**Solutions:**
1. Verify NVIDIA drivers are installed
2. Check if `nvidia-smi` works on host
3. Ops-Center may need NVIDIA runtime access

---

## Related Documentation

- [Inference Services Guide](/home/deploy/models/extraction/INFERENCE_SERVICES.md)
- [Infinity Proxy Configuration](/home/deploy/UC-Cloud-production/docker-compose.infinity-proxy.yml)
- [Granite Proxy Configuration](/home/deploy/models/extraction/docker-compose.extraction.yml)

---

## Changelog

### January 25, 2026
- Initial release
- Unified GPU Services Management page
- Support for Infinity (embeddings/reranker) and Granite (extraction) services
- Manual start/stop controls via proxy endpoints
- GPU memory monitoring
- Auto-refresh every 30 seconds
