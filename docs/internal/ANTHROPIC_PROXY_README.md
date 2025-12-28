# Anthropic API Proxy Implementation - Complete

## Overview

A complete implementation of an Anthropic-compatible API proxy that allows Claude Code to communicate with Ops-Center instead of directly calling Anthropic's API. This enables agent orchestration via Brigade, flexible LLM routing via LiteLLM, and secure local tool execution via MCP callbacks.

## What Was Created

### 1. Core Backend Files

#### `/backend/anthropic_proxy.py`
Main API endpoint that mimics Anthropic's `/v1/messages` API format.

**Features:**
- Full Anthropic API compatibility
- Streaming support via Server-Sent Events (SSE)
- JWT and API key authentication
- Health check and model listing endpoints
- Integration with Brigade for orchestration
- Usage tracking for billing

**Endpoints:**
- `POST /v1/messages` - Main message endpoint
- `POST /v1/messages/stream` - Streaming endpoint
- `GET /v1/models` - List available models
- `GET /v1/health` - Health check

#### `/backend/brigade_adapter.py`
Format conversion layer between Anthropic API and Brigade's internal format.

**Features:**
- Converts Anthropic requests to Brigade task format
- Intelligent task type inference (code_generation, debugging, etc.)
- Agent selection based on task type
- Tool format conversion
- Token counting and usage tracking
- Response conversion back to Anthropic format

**Key Functions:**
- `convert_anthropic_to_brigade()` - Request conversion
- `convert_brigade_to_anthropic()` - Response conversion
- `infer_task_type()` - Task type detection
- `select_agents_for_task()` - Agent selection
- `execute_tool_with_mcp()` - MCP tool execution

#### `/backend/mcp_callback.py`
MCP (Model Context Protocol) callback handler for local tool execution.

**Features:**
- WebSocket tunnel for real-time tool calls
- Polling-based fallback for restricted networks
- Tool call queue management
- MCP server registry
- Connection management with auto-reconnect
- Security: Path validation and command filtering

**Components:**
- `MCPConnectionManager` - WebSocket connection management
- `ToolCallQueue` - Polling queue system
- `MCPServerRegistry` - Server capability tracking

**Endpoints:**
- `WebSocket /api/mcp/ws/{user_id}` - WebSocket tunnel
- `POST /api/mcp/poll` - Poll for pending tool calls
- `POST /api/mcp/submit` - Submit tool results
- `POST /api/mcp/register` - Register MCP server
- `GET /api/mcp/servers/{user_id}` - List servers
- `GET /api/mcp/status` - System status

### 2. Integration

#### `/backend/server.py` (Modified)
Added router inclusions for new endpoints:

```python
from anthropic_proxy import router as anthropic_router
from mcp_callback import router as mcp_callback_router

app.include_router(anthropic_router)
app.include_router(mcp_callback_router)
```

### 3. Documentation

#### `/docs/ANTHROPIC_PROXY_SETUP.md`
Comprehensive setup guide covering:
- Architecture overview
- API endpoint documentation
- Configuration instructions
- Client setup (Claude Code)
- MCP server setup (3 methods)
- Authentication options
- Rate limiting details
- Troubleshooting guide
- Security best practices
- Advanced configuration

### 4. Testing & Tools

#### `/tests/test_anthropic_proxy.py`
Complete test suite with 7 test cases:
- Health check
- Model listing
- Simple message creation
- Tool-based message
- Streaming responses
- MCP status
- MCP registration

Run tests:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
python3 tests/test_anthropic_proxy.py
```

#### `/scripts/mcp_connector.py`
Full-featured MCP connector for local tool execution:
- WebSocket connection with auto-reconnect
- Supports all standard tools (read_file, write_file, bash, etc.)
- Path security (whitelist-based)
- Command safety (blocks dangerous commands)
- Graceful shutdown handling

Run connector:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
python3 scripts/mcp_connector.py \
  --user-id <your-user-id> \
  --api-key <your-api-key> \
  --allowed-paths /home/user/projects,/tmp
```

## Architecture Flow

```
┌─────────────────┐
│  Claude Code    │ (Local machine)
│  (Desktop App)  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────┐
│  Anthropic API Proxy            │
│  /v1/messages                   │
│  (Ops-Center Backend)           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Brigade Adapter                │
│  - Task type inference          │
│  - Agent selection              │
│  - Format conversion            │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Unicorn Brigade                │
│  - Agent orchestration          │
│  - Task distribution            │
│  - Workflow management          │
└────┬────────────────────────┬───┘
     │                        │
     ▼                        ▼
┌──────────┐          ┌──────────────┐
│ LiteLLM  │          │ MCP Callback │
│ (Model   │          │ Handler      │
│ Routing) │          └───────┬──────┘
└──────────┘                  │
                              │ WebSocket/Poll
                              ▼
                      ┌───────────────┐
                      │ MCP Connector │
                      │ (Local)       │
                      └───────┬───────┘
                              │
                              ▼
                      ┌───────────────┐
                      │ Local Tools   │
                      │ (File System) │
                      └───────────────┘
```

## Configuration Steps

### 1. Server Configuration

Add to `.env.auth`:
```bash
# Anthropic Proxy
BRIGADE_URL=http://unicorn-brigade:8112
LITELLM_URL=http://localhost:4000
ANTHROPIC_PROXY_ENABLED=true
EXTERNAL_API_URL=https://api.your-domain.com
```

### 2. Traefik Configuration

For external access, add to `docker-compose.direct.yml`:

```yaml
services:
  ops-center-direct:
    labels:
      # ... existing labels ...
      - "traefik.http.routers.ops-api.rule=Host(`api.your-domain.com`)"
      - "traefik.http.routers.ops-api.entrypoints=https"
      - "traefik.http.routers.ops-api.tls.certresolver=letsencrypt"
```

### 3. Restart Services

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
docker-compose -f docker-compose.direct.yml restart
```

### 4. Verify Installation

```bash
# Test health endpoint
curl http://localhost:8084/v1/health

# Expected response:
# {"status": "healthy", "brigade_connected": true, "timestamp": "..."}
```

## Client Setup (Claude Code)

### Method 1: Environment Variables

```bash
export ANTHROPIC_BASE_URL="https://api.your-domain.com/v1"
export ANTHROPIC_API_KEY="<your-ops-center-api-key>"
```

### Method 2: Config File

Create `~/.config/claude-code/config.json`:
```json
{
  "api": {
    "base_url": "https://api.your-domain.com/v1",
    "api_key": "<your-api-key>"
  }
}
```

### Method 3: Command Line

```bash
claude-code \
  --api-base-url https://api.your-domain.com/v1 \
  --api-key <your-key>
```

## MCP Server Setup

### WebSocket Method (Recommended)

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Set your credentials
export MCP_USER_ID="your-user-id"
export MCP_API_KEY="your-api-key"
export MCP_ALLOWED_PATHS="/home/user/projects,/tmp"

# Run connector
python3 scripts/mcp_connector.py
```

### Polling Method

For environments without WebSocket support:

```bash
python3 scripts/mcp_connector_polling.py
```

## API Key Generation

Generate an API key via Ops-Center:

```bash
curl -X POST https://api.your-domain.com/api/v1/api-keys \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Claude Code Integration",
    "scopes": ["anthropic-proxy", "mcp-callback"]
  }'
```

## Rate Limits by Tier

| Tier       | Requests/Min | Requests/Day | Token Limit    |
|------------|--------------|--------------|----------------|
| Free       | 10           | 100          | 10K tokens/day |
| Starter    | 60           | 1,000        | 100K tokens/day|
| Pro        | 300          | Unlimited    | 1M tokens/day  |
| Enterprise | Unlimited    | Unlimited    | Unlimited      |

Rate limiting is automatically enforced via the existing middleware.

## Security Features

1. **Authentication**
   - JWT token validation via Keycloak
   - API key authentication
   - Token refresh support

2. **Path Security**
   - Whitelist-based file access
   - Configurable allowed paths
   - No access outside allowed directories

3. **Command Safety**
   - Dangerous command blocking
   - Timeout limits (30 seconds)
   - Resource limits

4. **Audit Logging**
   - All API calls logged
   - Tool execution tracking
   - Usage metering for billing

5. **Rate Limiting**
   - Per-user rate limits
   - Tier-based enforcement
   - Automatic throttling

## Usage Tracking

All API calls are tracked via Lago for billing:

- Input tokens consumed
- Output tokens generated
- Model used
- Execution time
- Tool calls made
- User/organization context

View usage in Ops-Center: **Billing > Usage**

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to API endpoint

**Solution:**
```bash
# Check Ops-Center is running
docker ps | grep ops-center

# Check Brigade connectivity
curl http://localhost:8101/health

# Check Traefik routing
docker logs traefik | grep api.unicorncommander
```

### Authentication Failures

**Problem:** 401 Unauthorized

**Solution:**
```bash
# Verify API key is valid
curl -H "Authorization: Bearer <your-key>" \
     https://api.your-domain.com/v1/health

# Check Keycloak connectivity
curl https://auth.your-domain.com/realms/uchub/.well-known/openid-configuration
```

### Tool Execution Failures

**Problem:** MCP tools not working

**Solution:**
```bash
# Check MCP connector is running
ps aux | grep mcp_connector

# Verify WebSocket connection
curl https://api.your-domain.com/api/mcp/status

# Check registered servers
curl https://api.your-domain.com/api/mcp/servers/<user-id>
```

### High Latency

**Problem:** Slow response times

**Solution:**
```bash
# Check Brigade performance
curl http://localhost:8101/api/metrics

# Enable caching in Brigade
# Edit Brigade config to enable response caching

# Check LiteLLM health
curl http://localhost:4000/health
```

## File Locations

| File | Path | Purpose |
|------|------|---------|
| Main proxy | `/backend/anthropic_proxy.py` | API endpoints |
| Brigade adapter | `/backend/brigade_adapter.py` | Format conversion |
| MCP callback | `/backend/mcp_callback.py` | Tool execution |
| Server integration | `/backend/server.py` | Router registration |
| Setup guide | `/docs/ANTHROPIC_PROXY_SETUP.md` | Documentation |
| Test suite | `/tests/test_anthropic_proxy.py` | Testing |
| MCP connector | `/scripts/mcp_connector.py` | Local tool runner |

## Next Steps

1. **Deploy to Production**
   ```bash
   cd /home/muut/Production/UC-Cloud/services/ops-center
   docker-compose -f docker-compose.direct.yml up -d
   ```

2. **Configure Traefik**
   - Add `api.your-domain.com` domain routing
   - Ensure SSL certificate is obtained

3. **Test End-to-End**
   ```bash
   python3 tests/test_anthropic_proxy.py
   ```

4. **Setup MCP Connector**
   ```bash
   python3 scripts/mcp_connector.py --user-id <id> --api-key <key>
   ```

5. **Configure Claude Code**
   - Set `ANTHROPIC_BASE_URL` to Ops-Center
   - Test with simple code generation task

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/unicorncommander/ops-center/issues
- **Email**: support@your-domain.com
- **Documentation**: `/docs/ANTHROPIC_PROXY_SETUP.md`

## License

Part of UC-1 Pro Ops-Center - Proprietary

---

**Implementation Date**: October 20, 2025
**Status**: Complete and Ready for Testing
**Author**: Claude Code + Backend API Developer Agent
