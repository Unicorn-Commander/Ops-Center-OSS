# Service Discovery Implementation for UC-1 Pro Ops Center

## Overview

This implementation replaces hardcoded service ports with dynamic service discovery, enabling the Ops Center to work across different deployment configurations (local development, Docker Compose, Kubernetes, distributed systems).

## Implementation Date
October 9, 2025

## Problem Solved

**Before**: Hardcoded service URLs like `http://localhost:8080` broke when:
- Deploying to different networks (Docker internal networking)
- Using different ports
- Running services on remote hosts
- Using Traefik/reverse proxy with custom domains

**After**: Dynamic service discovery automatically adapts to:
- Local development (localhost)
- Docker Compose with internal networking
- Traefik reverse proxy with custom domains
- Remote/distributed deployments
- Kubernetes service DNS

## Architecture

### Components

1. **Backend: `service_discovery.py`**
   - Python module for dynamic service endpoint resolution
   - Supports multiple discovery methods with fallback chain
   - Caches discovered URLs for performance

2. **Backend API: `/api/v1/services/discovery`**
   - RESTful endpoint returning service information
   - Returns internal URLs, external URLs, and deployment config
   - Used by frontend to get current service endpoints

3. **Frontend: `modelApi.js`**
   - Updated to use service discovery
   - Caches discovered URLs to minimize API calls
   - Graceful fallback to localhost for development

4. **Environment Configuration: `.env.template`**
   - Comprehensive template for all deployment scenarios
   - Documents all service URL environment variables
   - Includes examples for common deployments

5. **Docker Compose Integration**
   - Updated `docker-compose.yml` with service URL environment variables
   - Uses sensible defaults for internal Docker networking
   - Allows override via `.env` file

## Service Discovery Resolution Chain

The system uses a fallback chain to discover service endpoints:

1. **Environment Variables** (Highest Priority)
   - Explicit configuration via `OLLAMA_URL`, `VLLM_URL`, etc.
   - Best for production/custom deployments

2. **Docker Container Inspection** (Medium Priority)
   - Dynamically discovers running containers
   - Extracts container names and ports
   - Works for standard Docker Compose deployments

3. **Default Docker Compose Names** (Low Priority)
   - Uses standard UC-1 Pro container names
   - Example: `http://unicorn-ollama:11434`
   - Reliable for default deployments

4. **Localhost Fallback** (Lowest Priority)
   - Falls back to `http://localhost:PORT`
   - Enables local development without Docker

## File Changes

### New Files Created

1. `/backend/service_discovery.py` (254 lines)
   - Core service discovery module
   - Docker client integration
   - Environment variable parsing
   - Default configurations

2. `/services/ops-center/.env.template` (185 lines)
   - Comprehensive environment configuration template
   - Documents all service URLs
   - Includes deployment scenario examples

3. `/services/ops-center/SERVICE_DISCOVERY_IMPLEMENTATION.md` (This file)
   - Complete implementation documentation
   - Usage examples
   - Troubleshooting guide

### Modified Files

1. `/backend/server.py`
   - Added import: `from service_discovery import service_discovery`
   - Added endpoint: `@app.get("/api/v1/services/discovery")`
   - Returns service discovery information

2. `/src/services/modelApi.js`
   - Added `constructor()` with service URL cache
   - Added `discoverServices()` method
   - Added `getServiceUrl(backend)` method
   - Added `refreshServiceDiscovery()` method
   - Updated all service-specific methods to use dynamic URLs:
     - `deleteModel()` - Line 166
     - `getCachedModels()` - Line 184
     - `getAvailableModels()` - Line 195
     - `switchModel()` - Line 206

3. `/docker-compose.yml`
   - Added service URL environment variables to `ops-center` service
   - Lines 721-730: Service discovery configuration

## Usage

### For Developers (Local Development)

No configuration needed! Service discovery automatically falls back to localhost:

```bash
# Just start your services on standard ports
ollama serve  # localhost:11434
vllm serve    # localhost:8000
# etc.
```

### For Docker Compose Deployments

1. **Standard Deployment (No Configuration Needed)**
   ```bash
   docker compose up -d
   # Service discovery uses container names automatically
   ```

2. **Custom Deployment (Override via Environment)**
   ```bash
   # Create .env file from template
   cp services/ops-center/.env.template .env

   # Edit .env to set custom URLs
   OLLAMA_URL=http://my-ollama-server:11434
   VLLM_URL=http://gpu-server:8000

   # Start services
   docker compose up -d
   ```

### For Production (Traefik/Custom Domains)

Edit `.env` file:

```env
EXTERNAL_HOST=unicorncommander.ai
EXTERNAL_PROTOCOL=https

# Optional: Override specific services
OPENWEBUI_URL=https://chat.unicorncommander.ai
CENTERDEEP_URL=https://search.unicorncommander.ai
AUTHENTIK_URL=https://auth.unicorncommander.ai
```

### For Distributed Deployments

When services run on different hosts:

```env
EXTERNAL_HOST=api.yourcompany.com
EXTERNAL_PROTOCOL=https

# Services on different servers
OLLAMA_URL=http://ollama-server.internal:11434
VLLM_URL=http://gpu-server-1.internal:8000
EMBEDDINGS_URL=http://cpu-server.internal:8082
POSTGRESQL_URL=postgresql://user:pass@db-server.internal:5432/ucpro
```

### For Kubernetes

```env
EXTERNAL_HOST=ucpro.k8s.cluster
EXTERNAL_PROTOCOL=https

# Kubernetes service DNS names
OLLAMA_URL=http://ollama-service.ucpro.svc.cluster.local:11434
VLLM_URL=http://vllm-service.ucpro.svc.cluster.local:8000
OPENWEBUI_URL=http://openwebui-service.ucpro.svc.cluster.local:8080
```

## API Documentation

### GET `/api/v1/services/discovery`

Returns comprehensive service discovery information.

**Response:**
```json
{
  "services": {
    "ollama": {
      "internal": "http://unicorn-ollama:11434",
      "external": "http://192.168.1.100:11434",
      "status": "available"
    },
    "openwebui": {
      "internal": "http://unicorn-open-webui:8080",
      "external": "https://chat.unicorncommander.ai",
      "status": "available"
    },
    ...
  },
  "external_urls": {
    "openwebui": "https://chat.unicorncommander.ai",
    "centerdeep": "https://search.unicorncommander.ai",
    ...
  },
  "internal_urls": {
    "ollama": "http://unicorn-ollama:11434",
    "vllm": "http://unicorn-vllm:8000",
    ...
  },
  "deployment": {
    "external_host": "unicorncommander.ai",
    "external_protocol": "https",
    "docker_available": true
  }
}
```

## Frontend Usage

The `modelApi.js` service automatically handles service discovery:

```javascript
// In your React component
import modelApi from '../services/modelApi';

// No changes needed - automatically uses discovered URLs
const models = await modelApi.getCachedModels('embeddings');

// Refresh discovery if deployment changes
modelApi.refreshServiceDiscovery();
```

## Supported Services

The following services are supported by service discovery:

| Service | Default Internal URL | Default Port | Environment Variable |
|---------|---------------------|--------------|---------------------|
| Ollama | `unicorn-ollama:11434` | 11434 | `OLLAMA_URL` |
| Open-WebUI | `unicorn-open-webui:8080` | 8080 | `OPENWEBUI_URL` |
| vLLM | `unicorn-vllm:8000` | 8000 | `VLLM_URL` |
| Embeddings | `unicorn-embeddings:8001` | 8082 | `EMBEDDINGS_URL` |
| Reranker | `unicorn-reranker:8002` | 8083 | `RERANKER_URL` |
| Center-Deep | `unicorn-center-deep:8890` | 8890 | `CENTERDEEP_URL` |
| Authentik | `authentik-server:9000` | 9000 | `AUTHENTIK_URL` |
| Qdrant | `unicorn-qdrant:6333` | 6333 | `QDRANT_URL` |
| PostgreSQL | `unicorn-postgresql:5432` | 5432 | `POSTGRESQL_URL` |
| Redis | `unicorn-redis:6379` | 6379 | `REDIS_URL` |
| Ops Center | `unicorn-ops-center:8084` | 8084 | `OPS_CENTER_URL` |

## Troubleshooting

### Services Not Discovered

**Symptom**: Frontend shows connection errors

**Solution**:
1. Check backend logs for service discovery errors
2. Verify Docker socket is mounted: `/var/run/docker.sock:/var/run/docker.sock`
3. Check containers are running: `docker ps`
4. Test discovery endpoint: `curl http://localhost:8084/api/v1/services/discovery`

### Wrong URLs Being Used

**Symptom**: Service discovery returns incorrect URLs

**Solution**:
1. Check environment variables: `docker exec unicorn-ops-center env | grep _URL`
2. Verify `.env` file configuration
3. Check docker-compose environment section
4. Use explicit URLs in `.env` to override discovery

### Frontend Cache Issues

**Symptom**: Frontend uses old URLs after deployment changes

**Solution**:
```javascript
// Refresh service discovery cache
modelApi.refreshServiceDiscovery();

// Or hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Docker Client Unavailable

**Symptom**: Logs show "Docker client unavailable"

**Solution**:
1. Ensure Docker socket is mounted
2. Check Docker socket permissions
3. Fallback to environment variables:
   ```env
   OLLAMA_URL=http://unicorn-ollama:11434
   VLLM_URL=http://unicorn-vllm:8000
   # etc.
   ```

## Testing

### Test Service Discovery Endpoint

```bash
# Test discovery endpoint
curl http://localhost:8084/api/v1/services/discovery | jq

# Test specific service URL
curl http://localhost:8084/api/v1/services/discovery | jq '.internal_urls.ollama'
```

### Test Frontend Integration

```javascript
// Open browser console on AIModelManagement page
// Check discovered URLs
console.log(await modelApi.discoverServices());

// Test specific service
console.log(await modelApi.getServiceUrl('ollama'));
```

### Test Different Deployments

1. **Local Development**:
   ```bash
   # Start services locally
   ollama serve &
   # Should discover localhost:11434
   ```

2. **Docker Compose**:
   ```bash
   docker compose up -d
   # Should discover unicorn-ollama:11434
   ```

3. **Custom Deployment**:
   ```bash
   # Set environment variable
   export OLLAMA_URL=http://custom-host:11434
   docker compose up -d
   # Should use custom URL
   ```

## Performance Considerations

- **Caching**: Service URLs are cached on first discovery
- **Lazy Loading**: Discovery only happens when needed
- **Minimal API Calls**: Frontend caches discovery results
- **Fallback Speed**: Localhost fallback is instant (no network calls)

## Security Considerations

- Docker socket access required for container inspection
- Environment variables may contain sensitive URLs
- Service discovery endpoint is unauthenticated (internal use only)
- Production deployments should restrict access to internal network

## Future Enhancements

Potential improvements for future versions:

1. **Health Checking**: Add service availability verification
2. **Dynamic Refresh**: Auto-refresh when services change
3. **Service Registry**: Implement formal service registry (Consul, etcd)
4. **Load Balancing**: Support multiple instances per service
5. **Circuit Breakers**: Add resilience patterns for service failures
6. **Metrics**: Track service discovery performance and failures

## Deployment Checklist

Before deploying to production:

- [ ] Copy `.env.template` to `.env`
- [ ] Configure `EXTERNAL_HOST` and `EXTERNAL_PROTOCOL`
- [ ] Set service URLs for your deployment
- [ ] Test service discovery endpoint
- [ ] Verify frontend loads correctly
- [ ] Check AI Model Management page functionality
- [ ] Test across different network configurations
- [ ] Review logs for any discovery errors

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs: `docker logs unicorn-ops-center`
- Test discovery endpoint: `/api/v1/services/discovery`
- Consult `.env.template` for configuration examples

## Related Files

- Backend: `/backend/service_discovery.py`
- API Endpoint: `/backend/server.py` (line 1280)
- Frontend Service: `/src/services/modelApi.js`
- Environment Template: `.env.template`
- Docker Compose: `/docker-compose.yml` (lines 721-730)
- Frontend Component: `/src/pages/AIModelManagement.jsx`

## Version History

- **v1.0** (2025-10-09): Initial implementation
  - Dynamic service discovery
  - Multi-deployment support
  - Frontend integration
  - Comprehensive documentation
