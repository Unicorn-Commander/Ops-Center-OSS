"""
Federation startup hooks for integration with server lifecycle.
"""


import logging
import os
import socket
from typing import Optional

from federation.node_agent import NodeAgent

logger = logging.getLogger("federation")

_agent: Optional[NodeAgent] = None


def get_node_agent() -> NodeAgent:
    global _agent
    if _agent is None:
        hostname = socket.gethostname().split(".")[0]
        _agent = NodeAgent(
            node_id=os.getenv("FEDERATION_NODE_ID", f"uc-{hostname}"),
            display_name=os.getenv("FEDERATION_NODE_NAME", hostname),
            endpoint_url=os.getenv("FEDERATION_ENDPOINT_URL", "http://localhost:8084"),
            peers=[peer.strip() for peer in os.getenv("FEDERATION_PEERS", "").split(",") if peer.strip()],
            auth_token=os.getenv("FEDERATION_SHARED_SECRET"),
            heartbeat_interval=int(os.getenv("FEDERATION_HEARTBEAT_INTERVAL", "30")),
        )
    return _agent


async def start_federation_agent():
    try:
        agent = get_node_agent()
        if agent.peers:
            await agent.start()
    except Exception as exc:
        logger.error("Failed to start federation agent: %s", exc)


async def stop_federation_agent():
    try:
        agent = get_node_agent()
        await agent.stop()
    except Exception as exc:
        logger.error("Error stopping federation agent: %s", exc)
