# Anthropic API Proxy - Deployment Checklist

## Pre-Deployment Verification

- [ ] All files created successfully
  - [ ] `/backend/anthropic_proxy.py`
  - [ ] `/backend/brigade_adapter.py`
  - [ ] `/backend/mcp_callback.py`
  - [ ] `/backend/server.py` (modified)
  - [ ] `/docs/ANTHROPIC_PROXY_SETUP.md`
  - [ ] `/tests/test_anthropic_proxy.py`
  - [ ] `/scripts/mcp_connector.py`
  - [ ] `ANTHROPIC_PROXY_README.md`

- [ ] Dependencies installed
  - [ ] `httpx` (async HTTP client)
  - [ ] `websockets` (WebSocket support)
  - [ ] `pydantic` (data validation)

## Configuration

### 1. Environment Variables

- [ ] Add to `.env.auth`:
```bash
BRIGADE_URL=http://unicorn-brigade:8112
LITELLM_URL=http://localhost:4000
ANTHROPIC_PROXY_ENABLED=true
EXTERNAL_API_URL=https://api.unicorncommander.ai
```

### 2. Traefik Configuration

- [ ] Add domain routing for `api.unicorncommander.ai`
- [ ] Update `docker-compose.direct.yml`:
```yaml
labels:
  - "traefik.http.routers.ops-api.rule=Host(`api.unicorncommander.ai`)"
  - "traefik.http.routers.ops-api.entrypoints=https"
  - "traefik.http.routers.ops-api.tls.certresolver=letsencrypt"
```

### 3. DNS Configuration

- [ ] Add DNS A record: `api.unicorncommander.ai` → server IP
- [ ] Verify DNS propagation: `dig api.unicorncommander.ai`

## Deployment Steps

### 1. Install Dependencies

```bash
cd /opt/ops-center/backend
pip install httpx websockets pydantic
```

### 2. Restart Ops-Center

```bash
cd /opt/ops-center
docker-compose -f docker-compose.direct.yml restart
```

### 3. Verify Services

```bash
# Check Ops-Center is running
docker ps | grep ops-center

# Check Brigade is running
docker ps | grep brigade

# Check logs for errors
docker logs ops-center-direct --tail 50
```

## Testing

### 1. Local Testing

```bash
# Test health endpoint
curl http://localhost:8084/v1/health

# Expected: {"status": "healthy", "brigade_connected": true}
```

### 2. Run Test Suite

```bash
cd /opt/ops-center
python3 tests/test_anthropic_proxy.py
```

### 3. Test External Access

```bash
# Test from external machine
curl https://api.unicorncommander.ai/v1/health

# Expected: {"status": "healthy", ...}
```

### 4. Test MCP Status

```bash
curl http://localhost:8084/api/mcp/status

# Expected: {"websocket_connections": 0, "pending_calls": 0, ...}
```

## Client Setup

### 1. Generate API Key

```bash
# Login to Ops-Center
# Go to Settings > API Keys
# Create new key with scopes: anthropic-proxy, mcp-callback
# Save the generated key securely
```

### 2. Configure Claude Code

```bash
# Set environment variables
export ANTHROPIC_BASE_URL="https://api.unicorncommander.ai/v1"
export ANTHROPIC_API_KEY="sk-ant-uc-<your-key>"
```

### 3. Test Claude Code Connection

```bash
# Run a simple command
claude-code "Write a hello world function in Python"

# Should route through Ops-Center instead of Anthropic
```

## MCP Connector Setup

### 1. Install MCP Connector

```bash
# On client machine
cd /opt/ops-center/scripts

# Make executable
chmod +x mcp_connector.py

# Copy to user's local machine or run directly
```

### 2. Configure MCP Connector

```bash
# Set environment variables
export MCP_USER_ID="<your-keycloak-user-id>"
export MCP_API_KEY="<your-api-key>"
export MCP_ALLOWED_PATHS="/home/user/projects,/tmp"
```

### 3. Run MCP Connector

```bash
python3 mcp_connector.py

# Expected output:
# INFO - Initialized MCP Connector for user <id>
# INFO - Connecting to wss://api.unicorncommander.ai/api/mcp/ws/<id>
# INFO - Connected successfully!
# INFO - Registered 7 tools
```

### 4. Verify MCP Registration

```bash
curl https://api.unicorncommander.ai/api/mcp/servers/<your-user-id>

# Expected: List of registered MCP servers
```

## Monitoring

### 1. Check Logs

```bash
# Ops-Center logs
docker logs -f ops-center-direct

# Brigade logs
docker logs -f unicorn-brigade

# Look for:
# - "Anthropic API proxy endpoints registered"
# - "MCP callback endpoints registered"
# - Incoming requests to /v1/messages
```

### 2. Monitor Usage

```bash
# Check API usage
curl -H "Authorization: Bearer <jwt>" \
     https://api.unicorncommander.ai/api/v1/usage/current

# Check MCP status
curl https://api.unicorncommander.ai/api/mcp/status
```

### 3. Performance Metrics

```bash
# Brigade metrics
curl http://localhost:8101/api/metrics

# LiteLLM health
curl http://localhost:4000/health
```

## Troubleshooting

### Issue: Connection Refused

**Check:**
- [ ] Ops-Center container is running
- [ ] Port 8084 is accessible
- [ ] Firewall rules allow traffic

**Fix:**
```bash
docker-compose -f docker-compose.direct.yml restart
```

### Issue: Brigade Not Connected

**Check:**
- [ ] Brigade container is running
- [ ] Network connectivity between containers
- [ ] Brigade health endpoint responds

**Fix:**
```bash
docker network inspect unicorn-network
docker restart unicorn-brigade
```

### Issue: Authentication Fails

**Check:**
- [ ] API key is valid
- [ ] Keycloak is accessible
- [ ] JWT token hasn't expired

**Fix:**
```bash
# Regenerate API key in Ops-Center
# Or refresh JWT token
```

### Issue: MCP Tools Not Working

**Check:**
- [ ] MCP connector is running
- [ ] WebSocket connection is active
- [ ] Tools are registered properly

**Fix:**
```bash
# Restart MCP connector
python3 mcp_connector.py

# Check MCP status
curl https://api.unicorncommander.ai/api/mcp/status
```

## Post-Deployment

### 1. Documentation

- [ ] Update user documentation
- [ ] Add to main README
- [ ] Create usage examples
- [ ] Record demo video

### 2. Communication

- [ ] Notify users about new feature
- [ ] Send setup instructions
- [ ] Schedule training session
- [ ] Create FAQ document

### 3. Monitoring Setup

- [ ] Configure alerts for failures
- [ ] Set up usage dashboards
- [ ] Enable error tracking
- [ ] Schedule regular health checks

## Rollback Plan

If issues occur:

### 1. Disable New Endpoints

```bash
# Comment out in server.py:
# app.include_router(anthropic_router)
# app.include_router(mcp_callback_router)
```

### 2. Restart Service

```bash
docker-compose -f docker-compose.direct.yml restart
```

### 3. Investigate Issues

```bash
# Check logs
docker logs ops-center-direct --tail 100

# Check error patterns
grep -i error /path/to/logs
```

## Success Criteria

- [ ] Health endpoint responds with 200 OK
- [ ] Test suite passes all tests
- [ ] Claude Code can connect successfully
- [ ] Simple message creation works
- [ ] MCP connector connects and registers tools
- [ ] Tool execution works end-to-end
- [ ] Streaming responses work
- [ ] Rate limiting is enforced
- [ ] Usage is tracked in Lago
- [ ] No errors in logs
- [ ] External domain is accessible
- [ ] SSL certificate is valid

## Sign-off

- [ ] Tested by: _________________ Date: _______
- [ ] Reviewed by: ________________ Date: _______
- [ ] Approved by: ________________ Date: _______

## Notes

_Add any deployment notes, issues encountered, or special configurations here:_

---

**Deployment Date**: _______________
**Version**: 1.0.0
**Status**: Ready for Production
