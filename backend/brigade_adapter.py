"""
Brigade Adapter - Format Conversion Layer

Converts between Anthropic API format and Brigade's internal format for
task orchestration and agent communication.

This adapter:
1. Converts Anthropic requests to Brigade task format
2. Converts Brigade responses back to Anthropic format
3. Handles tool calls and MCP server callbacks
4. Manages token counting and usage tracking
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# Anthropic -> Brigade Conversion
# ===================================================================

def convert_anthropic_to_brigade(
    anthropic_request: Any,
    user: Dict[str, Any],
    provider_config: Optional[Dict[str, Any]] = None,
    execution_server: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert Anthropic API request to Brigade task format.

    Anthropic format:
    {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "..."}],
        "system": "You are a helpful assistant",
        "tools": [...]
    }

    Brigade format:
    {
        "task_type": "code_generation",
        "context": {...},
        "agents": [...],
        "tools": [...],
        "user_id": "...",
        "mcp_servers": [...],
        "llm_config": {...},  # BYOK configuration
        "execution_server": {...}  # Execution environment config
    }
    """
    # Extract conversation context
    messages = anthropic_request.messages
    system_prompt = anthropic_request.system or "You are a helpful AI assistant."

    # Determine task type based on content
    task_type = infer_task_type(messages)

    # Extract tools and convert to Brigade format
    brigade_tools = []
    if anthropic_request.tools:
        brigade_tools = [
            convert_tool_to_brigade(tool)
            for tool in anthropic_request.tools
        ]

    # Build LLM config from provider config (BYOK or default)
    llm_config = {}
    if provider_config:
        llm_config = {
            "provider": provider_config.get("provider"),
            "model": provider_config.get("model"),
            "api_key": provider_config.get("api_key"),
            "base_url": provider_config.get("base_url"),
            "format": provider_config.get("format", "openai"),
            "is_byok": provider_config.get("is_byok", False),
            "supports_streaming": provider_config.get("supports_streaming", True)
        }

    # Build Brigade request
    brigade_request = {
        "task_id": f"task_{uuid.uuid4().hex[:16]}",
        "task_type": task_type,
        "user_id": user.get("user_id"),
        "context": {
            "system_prompt": system_prompt,
            "conversation_history": convert_messages_to_history(messages),
            "model": anthropic_request.model,
            "max_tokens": anthropic_request.max_tokens,
            "temperature": anthropic_request.temperature or 1.0,
            "top_p": anthropic_request.top_p,
            "top_k": anthropic_request.top_k,
            "stop_sequences": anthropic_request.stop_sequences or [],
        },
        "agents": select_agents_for_task(task_type, messages),
        "tools": brigade_tools,
        "mcp_servers": user.get("mcp_servers", []),
        "user_config": {
            "subscription_tier": user.get("subscription_tier", "free"),
            "email": user.get("email"),
            "username": user.get("username"),
        },
        "llm_config": llm_config,  # BYOK configuration for LiteLLM
        "execution_server": execution_server,  # User's execution environment
        "metadata": {
            "anthropic_request_id": f"msg_{uuid.uuid4().hex[:16]}",
            "timestamp": datetime.utcnow().isoformat(),
            "stream": anthropic_request.stream or False,
        }
    }

    return brigade_request

def infer_task_type(messages: List[Any]) -> str:
    """
    Infer task type from conversation content.

    Types:
    - code_generation: Writing/editing code
    - code_review: Reviewing code
    - debugging: Finding and fixing bugs
    - system_design: Architecture planning
    - documentation: Writing docs
    - general: General assistance
    """
    # Get last user message
    last_message = None
    for msg in reversed(messages):
        if msg.role == "user":
            last_message = msg
            break

    if not last_message:
        return "general"

    # Extract content
    content = ""
    if isinstance(last_message.content, str):
        content = last_message.content.lower()
    elif isinstance(last_message.content, list):
        for block in last_message.content:
            if hasattr(block, 'text') and block.text:
                content += block.text.lower() + " "

    # Pattern matching for task types
    if any(keyword in content for keyword in ["write", "create", "implement", "build", "code", "function", "class"]):
        return "code_generation"
    elif any(keyword in content for keyword in ["review", "check", "analyze", "audit", "improve"]):
        return "code_review"
    elif any(keyword in content for keyword in ["bug", "error", "fix", "debug", "issue", "problem"]):
        return "debugging"
    elif any(keyword in content for keyword in ["design", "architecture", "system", "scalable", "infrastructure"]):
        return "system_design"
    elif any(keyword in content for keyword in ["document", "readme", "explain", "guide", "tutorial"]):
        return "documentation"
    else:
        return "general"

def convert_messages_to_history(messages: List[Any]) -> List[Dict[str, Any]]:
    """Convert Anthropic message format to Brigade conversation history"""
    history = []

    for msg in messages:
        role = msg.role
        content_blocks = []

        # Parse content
        if isinstance(msg.content, str):
            content_blocks.append({
                "type": "text",
                "text": msg.content
            })
        elif isinstance(msg.content, list):
            for block in msg.content:
                if hasattr(block, 'type'):
                    if block.type == "text":
                        content_blocks.append({
                            "type": "text",
                            "text": block.text
                        })
                    elif block.type == "tool_use":
                        content_blocks.append({
                            "type": "tool_call",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                    elif block.type == "tool_result":
                        content_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": block.tool_use_id,
                            "content": block.content
                        })

        history.append({
            "role": role,
            "content": content_blocks,
            "timestamp": datetime.utcnow().isoformat()
        })

    return history

def convert_tool_to_brigade(tool: Any) -> Dict[str, Any]:
    """Convert Anthropic tool definition to Brigade format"""
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.input_schema.properties,
        "required": tool.input_schema.required or [],
        "type": "mcp_tool"  # Indicates this should be routed to user's MCP server
    }

def select_agents_for_task(task_type: str, messages: List[Any]) -> List[str]:
    """
    Select appropriate Brigade agents for the task.

    Agent types:
    - code_writer: Generates code
    - code_reviewer: Reviews code quality
    - debugger: Finds and fixes bugs
    - architect: Designs system architecture
    - tester: Writes tests
    - documentation_writer: Creates documentation
    """
    agent_mapping = {
        "code_generation": ["code_writer", "tester"],
        "code_review": ["code_reviewer"],
        "debugging": ["debugger", "tester"],
        "system_design": ["architect"],
        "documentation": ["documentation_writer"],
        "general": ["code_writer"]
    }

    return agent_mapping.get(task_type, ["code_writer"])

# ===================================================================
# Brigade -> Anthropic Conversion
# ===================================================================

def convert_brigade_to_anthropic(
    brigade_response: Dict[str, Any],
    model: str,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert Brigade response to Anthropic API format.

    Brigade response:
    {
        "task_id": "...",
        "status": "completed",
        "result": {
            "content": "...",
            "tool_calls": [...]
        },
        "usage": {...}
    }

    Anthropic response:
    {
        "id": "msg_...",
        "type": "message",
        "role": "assistant",
        "content": [...],
        "model": "...",
        "stop_reason": "...",
        "usage": {...}
    }
    """
    # Extract result
    result = brigade_response.get("result", {})
    content_blocks = []

    # Parse content
    if isinstance(result.get("content"), str):
        content_blocks.append({
            "type": "text",
            "text": result["content"]
        })
    elif isinstance(result.get("content"), list):
        for block in result["content"]:
            if block.get("type") == "text":
                content_blocks.append({
                    "type": "text",
                    "text": block["text"]
                })

    # Add tool calls
    if result.get("tool_calls"):
        for tool_call in result["tool_calls"]:
            content_blocks.append({
                "type": "tool_use",
                "id": tool_call.get("id", f"toolu_{uuid.uuid4().hex[:16]}"),
                "name": tool_call["name"],
                "input": tool_call.get("input", {})
            })

    # Determine stop reason
    stop_reason = "end_turn"
    if result.get("tool_calls"):
        stop_reason = "tool_use"
    elif brigade_response.get("status") == "max_tokens":
        stop_reason = "max_tokens"
    elif result.get("stop_sequence"):
        stop_reason = "stop_sequence"

    # Build usage info
    usage = brigade_response.get("usage", {})
    usage_info = {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0)
    }

    # Build Anthropic response
    anthropic_response = {
        "id": brigade_response.get("task_id", f"msg_{uuid.uuid4().hex[:16]}"),
        "type": "message",
        "role": "assistant",
        "content": content_blocks,
        "model": model,
        "stop_reason": stop_reason,
        "stop_sequence": result.get("stop_sequence"),
        "usage": usage_info
    }

    return anthropic_response

# ===================================================================
# Tool Execution & MCP Callbacks
# ===================================================================

async def execute_tool_with_mcp(
    tool_call: Dict[str, Any],
    mcp_servers: List[str],
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a tool call by routing to the appropriate MCP server.

    This function:
    1. Identifies which MCP server handles the tool
    2. Sends the tool call to that server
    3. Returns the result

    MCP servers should be in format:
    [
        {
            "url": "http://localhost:3000",
            "tools": ["read_file", "write_file", "bash"]
        }
    ]
    """
    import httpx

    tool_name = tool_call["name"]
    tool_input = tool_call.get("input", {})

    # Find appropriate MCP server
    target_server = None
    for server in mcp_servers:
        if tool_name in server.get("tools", []):
            target_server = server
            break

    if not target_server:
        logger.warning(f"No MCP server found for tool: {tool_name}")
        return {
            "success": False,
            "error": f"No MCP server configured for tool: {tool_name}"
        }

    # Call MCP server
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{target_server['url']}/tools/execute",
                json={
                    "tool": tool_name,
                    "input": tool_input,
                    "user_id": user.get("user_id")
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {user.get('token', '')}"
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"MCP tool execution failed: {e}")
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }

# ===================================================================
# Token Counting & Usage Tracking
# ===================================================================

def count_tokens(text: str, model: str) -> int:
    """
    Estimate token count for text.

    This is a simple approximation. In production, use tiktoken or
    the actual model's tokenizer.
    """
    # Simple approximation: ~4 characters per token
    return len(text) // 4

def track_usage(
    user: Dict[str, Any],
    input_tokens: int,
    output_tokens: int,
    model: str
) -> None:
    """
    Track token usage for billing and rate limiting.

    This should integrate with Lago for usage metering.
    """
    try:
        import httpx
        import asyncio

        async def send_usage():
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://ops-center-direct:8084/api/v1/brigade/usage/record",
                    json={
                        "user_id": user.get("user_id"),
                        "tokens_used": input_tokens + output_tokens,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "model": model,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

        # Run async in background
        asyncio.create_task(send_usage())
    except Exception as e:
        logger.error(f"Failed to track usage: {e}")
