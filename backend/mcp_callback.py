"""
MCP Callback Handler

Manages callbacks to user's local MCP (Model Context Protocol) servers for tool execution.

Since user's MCP servers run locally, we need a mechanism for Brigade to call them:
- Option A: WebSocket tunnel (recommended) - User opens WS connection, Brigade sends tool calls
- Option B: Polling - User's MCP manager polls for pending tasks
- Option C: ngrok/expose - User temporarily exposes MCP servers via tunnel

This implementation supports all three methods.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Router for MCP callbacks
router = APIRouter(prefix="/api/mcp", tags=["mcp-callbacks"])

# ===================================================================
# WebSocket Tunnel Management (Option A - Recommended)
# ===================================================================

class MCPConnectionManager:
    """
    Manages WebSocket connections from users' local MCP servers.

    Each user can connect their local MCP server to Ops-Center via WebSocket.
    When Brigade needs to execute a tool, it sends the request through this tunnel.
    """

    def __init__(self):
        # Active WebSocket connections: {user_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Pending tool calls awaiting results: {call_id: asyncio.Future}
        self.pending_calls: Dict[str, asyncio.Future] = {}

        # Tool call timeout (seconds)
        self.timeout = 60

    async def connect(self, user_id: str, websocket: WebSocket):
        """Register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"MCP server connected for user {user_id}")

    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"MCP server disconnected for user {user_id}")

    async def send_tool_call(
        self,
        user_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a tool call to user's MCP server and wait for result.

        Returns:
            Tool execution result or error
        """
        if user_id not in self.active_connections:
            raise Exception(f"No MCP connection for user {user_id}")

        websocket = self.active_connections[user_id]
        call_id = f"call_{uuid.uuid4().hex[:16]}"

        # Create future for result
        future = asyncio.Future()
        self.pending_calls[call_id] = future

        try:
            # Send tool call request
            await websocket.send_json({
                "type": "tool_call",
                "call_id": call_id,
                "tool": tool_name,
                "input": tool_input,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Wait for result with timeout
            result = await asyncio.wait_for(
                future,
                timeout=timeout or self.timeout
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Tool call {call_id} timed out")
            return {
                "success": False,
                "error": f"Tool call timed out after {timeout or self.timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Tool call {call_id} failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up
            if call_id in self.pending_calls:
                del self.pending_calls[call_id]

    async def receive_tool_result(self, call_id: str, result: Dict[str, Any]):
        """Receive tool execution result from MCP server"""
        if call_id in self.pending_calls:
            future = self.pending_calls[call_id]
            if not future.done():
                future.set_result(result)
        else:
            logger.warning(f"Received result for unknown call_id: {call_id}")

    def is_connected(self, user_id: str) -> bool:
        """Check if user has an active MCP connection"""
        return user_id in self.active_connections

# Global connection manager
mcp_manager = MCPConnectionManager()

@router.websocket("/ws/{user_id}")
async def mcp_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for MCP server connections.

    Users should connect their local MCP server to:
    wss://api.unicorncommander.ai/api/mcp/ws/{user_id}

    Protocol:
    - Server -> Client: {"type": "tool_call", "call_id": "...", "tool": "...", "input": {...}}
    - Client -> Server: {"type": "tool_result", "call_id": "...", "result": {...}}
    - Server -> Client: {"type": "ping"}
    - Client -> Server: {"type": "pong"}
    """
    await mcp_manager.connect(user_id, websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            if data.get("type") == "tool_result":
                # Tool execution result
                call_id = data.get("call_id")
                result = data.get("result")
                await mcp_manager.receive_tool_result(call_id, result)

            elif data.get("type") == "pong":
                # Keepalive response
                pass

            elif data.get("type") == "register_tools":
                # Client registering available tools
                tools = data.get("tools", [])
                logger.info(f"User {user_id} registered {len(tools)} tools")
                # TODO: Store tool registry per user

    except WebSocketDisconnect:
        mcp_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        mcp_manager.disconnect(user_id)

# ===================================================================
# Polling API (Option B)
# ===================================================================

class ToolCallQueue:
    """Queue for pending tool calls (polling-based approach)"""

    def __init__(self):
        # Pending tool calls by user: {user_id: [tool_calls]}
        self.queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Results waiting for pickup: {call_id: result}
        self.results: Dict[str, Dict[str, Any]] = {}

        # Expiry time for results (10 minutes)
        self.result_expiry = timedelta(minutes=10)

    def add_tool_call(self, user_id: str, tool_call: Dict[str, Any]) -> str:
        """Add a tool call to user's queue"""
        call_id = f"call_{uuid.uuid4().hex[:16]}"
        tool_call["call_id"] = call_id
        tool_call["timestamp"] = datetime.utcnow().isoformat()
        self.queues[user_id].append(tool_call)
        return call_id

    def get_pending_calls(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pending tool calls for user"""
        calls = self.queues.get(user_id, [])
        self.queues[user_id] = []  # Clear queue
        return calls

    def submit_result(self, call_id: str, result: Dict[str, Any]):
        """Submit tool execution result"""
        self.results[call_id] = {
            "result": result,
            "timestamp": datetime.utcnow()
        }

    def get_result(self, call_id: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Get result for a tool call (blocking with timeout)"""
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            if call_id in self.results:
                result_data = self.results.pop(call_id)
                return result_data["result"]
            asyncio.sleep(0.1)
        return None

    def cleanup_expired_results(self):
        """Remove expired results"""
        now = datetime.utcnow()
        expired = [
            call_id for call_id, data in self.results.items()
            if now - data["timestamp"] > self.result_expiry
        ]
        for call_id in expired:
            del self.results[call_id]

# Global tool call queue
tool_queue = ToolCallQueue()

class ToolCallPoll(BaseModel):
    """Request model for polling"""
    user_id: str

class ToolResultSubmit(BaseModel):
    """Request model for submitting results"""
    call_id: str
    result: Dict[str, Any]

@router.post("/poll")
async def poll_for_tool_calls(request: ToolCallPoll):
    """
    Poll for pending tool calls.

    MCP manager should call this endpoint periodically (e.g., every 5 seconds)
    to check for pending tool execution requests.
    """
    calls = tool_queue.get_pending_calls(request.user_id)
    return {
        "pending_calls": calls,
        "count": len(calls)
    }

@router.post("/submit")
async def submit_tool_result(request: ToolResultSubmit):
    """
    Submit tool execution result.

    After executing a tool, MCP manager calls this endpoint to return the result.
    """
    tool_queue.submit_result(request.call_id, request.result)
    return {
        "success": True,
        "call_id": request.call_id
    }

# ===================================================================
# Tool Execution Orchestration
# ===================================================================

async def execute_tool(
    user_id: str,
    tool_name: str,
    tool_input: Dict[str, Any],
    method: str = "websocket",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Execute a tool via the appropriate method.

    Args:
        user_id: User identifier
        tool_name: Tool to execute
        tool_input: Tool parameters
        method: Execution method ("websocket", "polling", or "http")
        timeout: Timeout in seconds

    Returns:
        Tool execution result
    """
    try:
        if method == "websocket":
            # Use WebSocket tunnel
            if not mcp_manager.is_connected(user_id):
                return {
                    "success": False,
                    "error": "MCP server not connected via WebSocket"
                }

            result = await mcp_manager.send_tool_call(
                user_id,
                tool_name,
                tool_input,
                timeout
            )
            return result

        elif method == "polling":
            # Use polling queue
            call_id = tool_queue.add_tool_call(user_id, {
                "tool": tool_name,
                "input": tool_input
            })

            # Wait for result
            result = tool_queue.get_result(call_id, timeout)
            if result is None:
                return {
                    "success": False,
                    "error": "Tool execution timed out (polling)"
                }
            return result

        elif method == "http":
            # Direct HTTP call (user must expose endpoint)
            # This requires user to provide MCP server URL
            return {
                "success": False,
                "error": "HTTP method requires MCP server URL configuration"
            }

        else:
            return {
                "success": False,
                "error": f"Unknown execution method: {method}"
            }

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

# ===================================================================
# MCP Server Registry
# ===================================================================

class MCPServerRegistry:
    """Registry of user's MCP servers and their capabilities"""

    def __init__(self):
        # {user_id: {server_id: {url, tools, status}}}
        self.servers: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    def register_server(
        self,
        user_id: str,
        server_id: str,
        url: Optional[str],
        tools: List[str],
        method: str = "websocket"
    ):
        """Register an MCP server for a user"""
        self.servers[user_id][server_id] = {
            "url": url,
            "tools": tools,
            "method": method,
            "status": "active",
            "registered_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Registered MCP server {server_id} for user {user_id}")

    def unregister_server(self, user_id: str, server_id: str):
        """Unregister an MCP server"""
        if user_id in self.servers and server_id in self.servers[user_id]:
            del self.servers[user_id][server_id]
            logger.info(f"Unregistered MCP server {server_id} for user {user_id}")

    def get_server_for_tool(self, user_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find which server handles a specific tool"""
        if user_id not in self.servers:
            return None

        for server_id, server_info in self.servers[user_id].items():
            if tool_name in server_info["tools"]:
                return server_info

        return None

    def list_servers(self, user_id: str) -> List[Dict[str, Any]]:
        """List all registered servers for a user"""
        return list(self.servers.get(user_id, {}).values())

# Global registry
mcp_registry = MCPServerRegistry()

class MCPServerRegister(BaseModel):
    """Request model for server registration"""
    user_id: str
    server_id: str
    url: Optional[str] = None
    tools: List[str]
    method: str = "websocket"

@router.post("/register")
async def register_mcp_server(request: MCPServerRegister):
    """
    Register an MCP server.

    Users call this endpoint to register their local MCP server and its capabilities.
    """
    mcp_registry.register_server(
        request.user_id,
        request.server_id,
        request.url,
        request.tools,
        request.method
    )

    return {
        "success": True,
        "server_id": request.server_id,
        "method": request.method
    }

@router.get("/servers/{user_id}")
async def list_mcp_servers(user_id: str):
    """List all registered MCP servers for a user"""
    servers = mcp_registry.list_servers(user_id)
    return {
        "servers": servers,
        "count": len(servers)
    }

# ===================================================================
# Health & Monitoring
# ===================================================================

@router.get("/status")
async def mcp_status():
    """Get MCP callback system status"""
    return {
        "websocket_connections": len(mcp_manager.active_connections),
        "pending_calls": len(mcp_manager.pending_calls),
        "polling_queues": len(tool_queue.queues),
        "pending_results": len(tool_queue.results),
        "registered_servers": sum(len(servers) for servers in mcp_registry.servers.values())
    }
