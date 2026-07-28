#!/usr/bin/env python3
"""
MCP Connector for Ops-Center Anthropic Proxy

This script connects your local MCP server to Ops-Center, enabling
Claude Code to execute tools on your local machine.

Features:
- WebSocket connection for real-time tool execution
- Automatic reconnection on disconnect
- Support for all standard MCP tools (read_file, write_file, bash, etc.)
- Secure execution with configurable permissions

Usage:
    python3 mcp_connector.py --user-id <your-user-id> --api-key <your-api-key>

Environment Variables:
    MCP_USER_ID: Your Ops-Center user ID
    MCP_API_KEY: Your Ops-Center API key
    MCP_API_URL: Ops-Center API URL (default: https://api.unicorncommander.ai)
    MCP_ALLOWED_PATHS: Comma-separated list of allowed paths (default: current directory)
"""

import asyncio
import websockets
import json
import os
import sys
import subprocess
import argparse
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_API_URL = "wss://api.unicorncommander.ai"
DEFAULT_ALLOWED_PATHS = [str(Path.home())]

class MCPConnector:
    """
    MCP Connector for Ops-Center integration
    """

    def __init__(
        self,
        user_id: str,
        api_key: str,
        api_url: str = DEFAULT_API_URL,
        allowed_paths: Optional[List[str]] = None
    ):
        self.user_id = user_id
        self.api_key = api_key
        self.api_url = api_url.replace("https://", "wss://").replace("http://", "ws://")
        self.allowed_paths = allowed_paths or DEFAULT_ALLOWED_PATHS
        self.ws = None
        self.should_reconnect = True

        # Available tools
        self.tools = [
            "read_file",
            "write_file",
            "edit_file",
            "bash",
            "glob",
            "grep",
            "list_directory",
        ]

        logger.info(f"Initialized MCP Connector for user {user_id}")
        logger.info(f"Allowed paths: {', '.join(self.allowed_paths)}")

    def is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed directories"""
        abs_path = os.path.abspath(path)
        for allowed in self.allowed_paths:
            if abs_path.startswith(os.path.abspath(allowed)):
                return True
        return False

    async def connect(self):
        """Establish WebSocket connection"""
        ws_url = f"{self.api_url}/api/mcp/ws/{self.user_id}"
        logger.info(f"Connecting to {ws_url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            self.ws = await websockets.connect(ws_url, extra_headers=headers)
            logger.info("Connected successfully!")

            # Register available tools
            await self.register_tools()

            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def register_tools(self):
        """Register available tools with server"""
        await self.ws.send(json.dumps({
            "type": "register_tools",
            "tools": self.tools,
            "version": "1.0.0"
        }))
        logger.info(f"Registered {len(self.tools)} tools")

    async def handle_tool_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return result"""
        call_id = call_data.get("call_id")
        tool_name = call_data.get("tool")
        tool_input = call_data.get("input", {})

        logger.info(f"Executing tool: {tool_name} (call_id: {call_id})")

        try:
            if tool_name == "read_file":
                result = await self.read_file(tool_input)
            elif tool_name == "write_file":
                result = await self.write_file(tool_input)
            elif tool_name == "edit_file":
                result = await self.edit_file(tool_input)
            elif tool_name == "bash":
                result = await self.execute_bash(tool_input)
            elif tool_name == "glob":
                result = await self.glob_pattern(tool_input)
            elif tool_name == "grep":
                result = await self.grep_search(tool_input)
            elif tool_name == "list_directory":
                result = await self.list_directory(tool_input)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

            logger.info(f"Tool execution completed: {tool_name}")
            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def read_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        path = input_data.get("path")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            with open(path, "r") as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def write_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write file contents"""
        path = input_data.get("path")
        content = input_data.get("content")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w") as f:
                f.write(content)

            return {
                "success": True,
                "path": path,
                "bytes_written": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def edit_file(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit file (replace old_string with new_string)"""
        path = input_data.get("path")
        old_string = input_data.get("old_string")
        new_string = input_data.get("new_string")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            with open(path, "r") as f:
                content = f.read()

            if old_string not in content:
                return {
                    "success": False,
                    "error": "String not found in file"
                }

            new_content = content.replace(old_string, new_string, 1)

            with open(path, "w") as f:
                f.write(new_content)

            return {
                "success": True,
                "path": path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_bash(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash command"""
        command = input_data.get("command")

        # Safety checks
        dangerous_commands = ["rm -rf /", "dd if=", "mkfs", "format"]
        if any(cmd in command for cmd in dangerous_commands):
            return {
                "success": False,
                "error": "Dangerous command blocked"
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def glob_pattern(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find files matching glob pattern"""
        import glob

        pattern = input_data.get("pattern")
        path = input_data.get("path", ".")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            matches = glob.glob(os.path.join(path, pattern), recursive=True)
            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def grep_search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for pattern in files"""
        pattern = input_data.get("pattern")
        path = input_data.get("path", ".")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            result = subprocess.run(
                ["grep", "-r", pattern, path],
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "success": True,
                "matches": result.stdout.split("\n"),
                "count": len(result.stdout.split("\n"))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def list_directory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents"""
        path = input_data.get("path", ".")

        if not self.is_path_allowed(path):
            return {
                "success": False,
                "error": f"Path not allowed: {path}"
            }

        try:
            entries = []
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                entries.append({
                    "name": entry,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                })

            return {
                "success": True,
                "entries": entries,
                "count": len(entries)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def listen(self):
        """Listen for incoming tool calls"""
        try:
            async for message in self.ws:
                data = json.loads(message)

                if data.get("type") == "tool_call":
                    # Execute tool
                    result = await self.handle_tool_call(data)

                    # Send result back
                    await self.ws.send(json.dumps({
                        "type": "tool_result",
                        "call_id": data.get("call_id"),
                        "result": result
                    }))

                elif data.get("type") == "ping":
                    # Respond to keepalive
                    await self.ws.send(json.dumps({"type": "pong"}))

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by server")
        except Exception as e:
            logger.error(f"Error in listen loop: {e}", exc_info=True)

    async def run(self):
        """Main run loop with auto-reconnect"""
        while self.should_reconnect:
            try:
                if await self.connect():
                    await self.listen()
            except Exception as e:
                logger.error(f"Error: {e}")

            if self.should_reconnect:
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    def stop(self):
        """Stop the connector"""
        logger.info("Stopping MCP connector...")
        self.should_reconnect = False
        if self.ws:
            asyncio.create_task(self.ws.close())

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP Connector for Ops-Center")
    parser.add_argument("--user-id", help="Your Ops-Center user ID", default=os.environ.get("MCP_USER_ID"))
    parser.add_argument("--api-key", help="Your Ops-Center API key", default=os.environ.get("MCP_API_KEY"))
    parser.add_argument("--api-url", help="Ops-Center API URL", default=os.environ.get("MCP_API_URL", DEFAULT_API_URL))
    parser.add_argument("--allowed-paths", help="Comma-separated list of allowed paths", default=os.environ.get("MCP_ALLOWED_PATHS"))

    args = parser.parse_args()

    if not args.user_id or not args.api_key:
        print("Error: --user-id and --api-key are required")
        print("Set via arguments or environment variables MCP_USER_ID and MCP_API_KEY")
        sys.exit(1)

    allowed_paths = args.allowed_paths.split(",") if args.allowed_paths else DEFAULT_ALLOWED_PATHS

    connector = MCPConnector(
        user_id=args.user_id,
        api_key=args.api_key,
        api_url=args.api_url,
        allowed_paths=allowed_paths
    )

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal")
        connector.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run connector
    try:
        asyncio.run(connector.run())
    except KeyboardInterrupt:
        logger.info("Stopped by user")

if __name__ == "__main__":
    main()
