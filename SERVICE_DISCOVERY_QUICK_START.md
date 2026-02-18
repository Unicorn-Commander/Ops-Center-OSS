# Service Discovery - Quick Start Guide

## What Changed?

Service URLs are now **dynamically discovered** instead of hardcoded. This means the Ops Center automatically adapts to your deployment configuration.

## Do I Need to Configure Anything?

### For Most Users: NO

Service discovery works automatically with zero configuration for:
- Standard Docker Compose deployments
- Local development (localhost)
- Default UC-1 Pro setups

Just run:
```bash
docker compose up -d
```

### For Custom Deployments: YES (Optional)

If you have a custom deployment, you can configure service URLs.

## Quick Configuration

### 1. Copy Environment Template

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
cp .env.template .env
```

### 2. Edit for Your Deployment

Open `.env` and uncomment the section that matches your setup:

#### **Local Development**
```env
EXTERNAL_HOST=localhost
EXTERNAL_PROTOCOL=http
```

#### **Production with Custom Domain**
```env
EXTERNAL_HOST=yourcompany.com
EXTERNAL_PROTOCOL=https
OPENWEBUI_URL=https://chat.yourcompany.com
AUTHENTIK_URL=https://auth.yourcompany.com
```

#### **Remote Services**
```env
OLLAMA_URL=http://ollama-server:11434
VLLM_URL=http://gpu-server:8000
```

### 3. Restart Ops Center

```bash
docker compose restart ops-center
```

## Verify It Works

### Test Discovery API
```bash
curl http://localhost:8084/api/v1/services/discovery | jq
```

### Check Browser Console
1. Open Ops Center in browser
2. Go to AI Model Management
3. Open Developer Tools (F12)
4. Type: `await modelApi.discoverServices()`
5. Should show all service URLs

## Common Scenarios

### Scenario 1: Services on Different Ports

```env
# Custom ports
OLLAMA_URL=http://localhost:12345
VLLM_URL=http://localhost:9000
```

### Scenario 2: Remote GPU Server

```env
# GPU server on different host
VLLM_URL=http://gpu-server.local:8000
EMBEDDINGS_URL=http://cpu-server.local:8082
```

### Scenario 3: Kubernetes Deployment

```env
# K8s service DNS
OLLAMA_URL=http://ollama-svc.ucpro.svc.cluster.local:11434
VLLM_URL=http://vllm-svc.ucpro.svc.cluster.local:8000
```

### Scenario 4: Behind Traefik/Reverse Proxy

```env
EXTERNAL_HOST=unicorncommander.ai
EXTERNAL_PROTOCOL=https

# Services automatically use subdomain routing
# chat.unicorncommander.ai
# search.unicorncommander.ai
# auth.unicorncommander.ai
```

## Troubleshooting

### Problem: Services Not Found

**Solution**: Check if containers are running
```bash
docker ps | grep unicorn
```

### Problem: Wrong URLs

**Solution**: Check environment variables
```bash
docker exec unicorn-ops-center env | grep _URL
```

### Problem: Frontend Shows Errors

**Solution**: Refresh service discovery cache
```javascript
// In browser console
modelApi.refreshServiceDiscovery();
```

### Problem: Can't Connect to Services

**Solution**: Test discovery endpoint
```bash
curl http://localhost:8084/api/v1/services/discovery
```

## Testing

Run the test suite:
```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
./test_service_discovery.sh
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://unicorn-ollama:11434` | Ollama LLM service |
| `OPENWEBUI_URL` | `http://unicorn-open-webui:8080` | Chat interface |
| `VLLM_URL` | `http://unicorn-vllm:8000` | vLLM inference |
| `EMBEDDINGS_URL` | `http://unicorn-embeddings:8001` | Embeddings service |
| `RERANKER_URL` | `http://unicorn-reranker:8002` | Reranker service |
| `CENTERDEEP_URL` | `http://unicorn-center-deep:8890` | Search service |
| `AUTHENTIK_URL` | `http://authentik-server:9000` | SSO/Auth |
| `QDRANT_URL` | `http://unicorn-qdrant:6333` | Vector database |
| `EXTERNAL_HOST` | `localhost` | Public hostname |
| `EXTERNAL_PROTOCOL` | `http` | Protocol (http/https) |

## Need Help?

1. Check full documentation: `SERVICE_DISCOVERY_IMPLEMENTATION.md`
2. Review `.env.template` for examples
3. Run test suite: `./test_service_discovery.sh`
4. Check logs: `docker logs unicorn-ops-center`

## Migration from Hardcoded URLs

If upgrading from an older version:

1. No changes needed for standard deployments
2. If you modified source code with custom URLs:
   - Remove hardcoded URLs from code
   - Add them to `.env` instead
3. Frontend automatically picks up new discovery system
4. Clear browser cache if needed (Ctrl+Shift+R)

## Benefits

- ✅ **Zero Configuration**: Works out-of-the-box
- ✅ **Flexible Deployment**: Adapts to any environment
- ✅ **Easy Customization**: Simple `.env` configuration
- ✅ **Production Ready**: Supports reverse proxies, custom domains
- ✅ **Developer Friendly**: Localhost fallback for development
- ✅ **Future Proof**: Easy to add new services

---

**Last Updated**: October 9, 2025
**Version**: 1.0
