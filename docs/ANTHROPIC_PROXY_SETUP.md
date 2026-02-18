# Anthropic API Proxy - Setup Guide

## Overview

The Anthropic API Proxy allows Claude Code to communicate with Ops-Center instead of directly calling Anthropic's API. This enables:

1. **Agent Orchestration**: Brigade coordinates multiple agents for complex tasks
2. **LLM Routing**: LiteLLM provides flexible model routing and fallbacks
3. **Local Tool Execution**: MCP servers enable secure local file/system operations
4. **Usage Tracking**: All API calls are metered for billing via Lago
5. **BYOK Support**: Users can use their own API keys

## Architecture

```
Claude Code (Local)
    ↓ HTTPS
Anthropic API Proxy (Ops-Center)
    ↓
Brigade (Agent Orchestration)
    ↓
LiteLLM (Model Routing)
    ↓
Various LLM Providers (Anthropic, OpenAI, etc.)

Claude Code ←→ MCP Callback Handler ←→ Local MCP Servers
```

## API Endpoints

### Main Endpoints

#### POST /v1/messages
Mimics Anthropic's `/v1/messages` endpoint for non-streaming requests.

**Request:**
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {
      "role": "user",
      "content": "Write a REST API for user management"
    }
  ],
  "max_tokens": 4096,
  "system": "You are a helpful coding assistant",
  "tools": [
    {
      "name": "read_file",
      "description": "Read file contents",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {"type": "string"}
        },
        "required": ["path"]
      }
    }
  ]
}
```

**Response:**
```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll help you build a REST API..."
    },
    {
      "type": "tool_use",
      "id": "toolu_xyz789",
      "name": "write_file",
      "input": {
        "path": "server.js",
        "content": "const express = require('express')..."
      }
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 250
  }
}
```

#### POST /v1/messages/stream
Streaming version using Server-Sent Events (SSE).

#### GET /v1/models
Lists available models based on user's BYOK configuration.

#### GET /v1/health
Health check for the proxy service.

### MCP Callback Endpoints

#### WebSocket /api/mcp/ws/{user_id}
WebSocket connection for local MCP servers to receive tool execution requests.

**Protocol:**
```javascript
// Server -> Client (Tool Call Request)
{
  "type": "tool_call",
  "call_id": "call_abc123",
  "tool": "read_file",
  "input": {
    "path": "/home/user/project/server.js"
  },
  "timestamp": "2025-10-20T10:30:00Z"
}

// Client -> Server (Tool Result)
{
  "type": "tool_result",
  "call_id": "call_abc123",
  "result": {
    "success": true,
    "content": "const express = require('express')..."
  }
}
```

#### POST /api/mcp/poll
Polling endpoint for MCP servers that can't maintain WebSocket connections.

#### POST /api/mcp/submit
Submit tool execution results (for polling mode).

#### POST /api/mcp/register
Register an MCP server and its capabilities.

#### GET /api/mcp/servers/{user_id}
List registered MCP servers.

## Configuration

### Environment Variables

Add to `/opt/ops-center/.env.auth`:

```bash
# Anthropic Proxy Configuration
BRIGADE_URL=http://unicorn-brigade:8112
LITELLM_URL=http://localhost:4000
ANTHROPIC_PROXY_ENABLED=true

# External API URL (for Claude Code to connect)
EXTERNAL_API_URL=https://api.unicorncommander.ai
```

### Traefik Configuration

Add to docker-compose file for external access:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.ops-api.rule=Host(`api.unicorncommander.ai`)"
  - "traefik.http.routers.ops-api.entrypoints=https"
  - "traefik.http.routers.ops-api.tls.certresolver=letsencrypt"
  - "traefik.http.services.ops-api.loadbalancer.server.port=8084"
```

## Client Setup (Claude Code)

### Option 1: Environment Variable

Set the Anthropic API base URL to point to Ops-Center:

```bash
export ANTHROPIC_BASE_URL="https://api.unicorncommander.ai/v1"
export ANTHROPIC_API_KEY="sk-ant-<your-ops-center-api-key>"
```

### Option 2: Configuration File

Create `~/.config/claude-code/config.json`:

```json
{
  "api": {
    "base_url": "https://api.unicorncommander.ai/v1",
    "api_key": "sk-ant-<your-ops-center-api-key>"
  }
}
```

### Option 3: Command Line

```bash
claude-code --api-base-url https://api.unicorncommander.ai/v1 \
            --api-key sk-ant-<your-key>
```

## MCP Server Setup

### WebSocket Method (Recommended)

Create a simple MCP connector script:

```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def connect_mcp_server():
    user_id = "your-user-id"
    uri = f"wss://api.unicorncommander.ai/api/mcp/ws/{user_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to Ops-Center MCP endpoint")

        # Register available tools
        await websocket.send(json.dumps({
            "type": "register_tools",
            "tools": ["read_file", "write_file", "bash", "glob", "grep"]
        }))

        # Listen for tool calls
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "tool_call":
                # Execute tool locally
                result = execute_tool(data["tool"], data["input"])

                # Send result back
                await websocket.send(json.dumps({
                    "type": "tool_result",
                    "call_id": data["call_id"],
                    "result": result
                }))

def execute_tool(tool_name, tool_input):
    """Execute tool locally and return result"""
    if tool_name == "read_file":
        with open(tool_input["path"], "r") as f:
            return {"success": True, "content": f.read()}
    # Add other tools...

if __name__ == "__main__":
    asyncio.run(connect_mcp_server())
```

Run the connector:

```bash
python3 mcp_connector.py
```

### Polling Method

For environments where WebSocket isn't available:

```python
#!/usr/bin/env python3
import requests
import time
import json

def poll_and_execute():
    user_id = "your-user-id"
    api_url = "https://api.unicorncommander.ai/api/mcp"

    while True:
        # Poll for pending tool calls
        response = requests.post(f"{api_url}/poll", json={"user_id": user_id})
        pending_calls = response.json()["pending_calls"]

        for call in pending_calls:
            # Execute tool
            result = execute_tool(call["tool"], call["input"])

            # Submit result
            requests.post(f"{api_url}/submit", json={
                "call_id": call["call_id"],
                "result": result
            })

        time.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    poll_and_execute()
```

## Authentication

### Using JWT Token

If you have a Keycloak session:

```bash
export ANTHROPIC_API_KEY="Bearer <your-jwt-token>"
```

### Using API Key

Generate an API key in Ops-Center:

```bash
curl -X POST https://api.unicorncommander.ai/api/v1/api-keys \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Claude Code API Key", "scopes": ["anthropic-proxy"]}'
```

Use the returned API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-uc-<key>"
```

## Rate Limiting

Rate limits are enforced based on subscription tier:

- **Free**: 10 requests/minute, 100 requests/day
- **Starter**: 60 requests/minute, 1000 requests/day
- **Pro**: 300 requests/minute, unlimited daily
- **Enterprise**: Unlimited

## Usage Tracking

All API calls are tracked via Lago:

- Input tokens
- Output tokens
- Model used
- Execution time
- Tool calls made

View usage in Ops-Center dashboard under Billing > Usage.

## Troubleshooting

### Connection Refused

Check that Ops-Center is running:

```bash
docker ps | grep ops-center
```

Check Brigade connectivity:

```bash
curl http://localhost:8101/health
```

### Authentication Failed

Verify your API key:

```bash
curl -H "Authorization: Bearer <your-key>" \
     https://api.unicorncommander.ai/v1/health
```

### Tool Calls Not Working

Check MCP server connection:

```bash
curl https://api.unicorncommander.ai/api/mcp/status
```

Verify your user ID has registered servers:

```bash
curl https://api.unicorncommander.ai/api/mcp/servers/<your-user-id>
```

### High Latency

Check Brigade performance:

```bash
curl http://localhost:8101/api/metrics
```

Enable caching in Brigade config:

```yaml
cache:
  enabled: true
  ttl: 300
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **MCP Servers**: Only connect trusted MCP servers
3. **Tool Execution**: Validate all tool inputs before execution
4. **Rate Limiting**: Enforced automatically per subscription tier
5. **Audit Logging**: All API calls are logged for security review

## Advanced Configuration

### Custom Model Mapping

Map Anthropic models to other providers:

```json
{
  "model_mapping": {
    "claude-3-5-sonnet-20241022": "gpt-4",
    "claude-3-opus-20240229": "gpt-4-turbo"
  }
}
```

### Agent Selection

Control which Brigade agents handle tasks:

```json
{
  "agent_config": {
    "code_generation": ["code_writer", "tester"],
    "code_review": ["code_reviewer", "security_auditor"]
  }
}
```

### Custom Tools

Register custom tools for your workflow:

```bash
curl -X POST https://api.unicorncommander.ai/api/mcp/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "server_id": "custom-tools",
    "tools": ["deploy", "test", "lint"],
    "method": "websocket"
  }'
```

## Support

For issues or questions:
- GitHub: https://github.com/unicorncommander/ops-center/issues
- Email: support@unicorncommander.ai
- Discord: https://discord.gg/unicorncommander
