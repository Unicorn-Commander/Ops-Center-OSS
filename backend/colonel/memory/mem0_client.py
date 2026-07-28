"""
Mem0 Semantic Memory Client for The Colonel.

Uses Qdrant as vector store and BGE-M3 embeddings via Infinity proxy.
Falls back gracefully if Mem0 or Qdrant is unavailable.
"""

import logging
import os
from typing import Optional, List

logger = logging.getLogger("colonel.memory.mem0")

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "unicorn-qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
EMBEDDER_URL = os.getenv("COLONEL_EMBEDDER_URL", "http://unicorn-infinity-proxy:8080/v1")
EMBEDDER_MODEL = os.getenv("COLONEL_EMBEDDER_MODEL", "BAAI/bge-m3")
LLM_URL = os.getenv("COLONEL_LLM_URL", "http://ops-center-direct:8084/api/v1/llm")
LLM_MODEL = os.getenv("COLONEL_MEMORY_LLM", "anthropic/claude-sonnet-4-5-20250929")
COLLECTION_NAME = "colonel_memories"


class ColonelMemoryClient:
    """
    Semantic memory client using Mem0 with Qdrant backend.

    If mem0ai is not installed or Qdrant is unreachable, all operations
    gracefully return empty results without raising errors.
    """

    def __init__(self):
        self._mem0 = None
        self._initialized = False
        self._init_attempted = False

    def _ensure_init(self):
        """Lazy-initialize Mem0 client on first use."""
        if self._init_attempted:
            return
        self._init_attempted = True

        try:
            from mem0 import Memory

            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": QDRANT_HOST,
                        "port": QDRANT_PORT,
                        "collection_name": COLLECTION_NAME,
                        "embedding_model_dims": 1024,
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "api_key": "not-needed",
                        "openai_base_url": EMBEDDER_URL,
                        "model": EMBEDDER_MODEL,
                    },
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "api_key": os.getenv("LITELLM_MASTER_KEY", "not-needed"),
                        "openai_base_url": LLM_URL,
                        "model": LLM_MODEL,
                    },
                },
            }

            self._mem0 = Memory.from_config(config)
            self._initialized = True
            logger.info(f"Mem0 initialized with Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")

        except ImportError:
            logger.warning("mem0ai not installed — memory features disabled. Install with: pip install mem0ai")
        except Exception as e:
            logger.warning(f"Failed to initialize Mem0: {e}")

    async def recall(self, query: str, user_id: str, limit: int = 5) -> Optional[List[str]]:
        """
        Search for relevant memories based on a query.
        Returns list of memory text strings or None.
        """
        self._ensure_init()
        if not self._initialized:
            return None

        try:
            results = self._mem0.search(query=query, user_id=f"colonel:{user_id}", limit=limit)

            if not results:
                return None

            # Extract memory text from results
            memories = []
            if isinstance(results, dict) and "results" in results:
                for r in results["results"]:
                    text = r.get("memory") or r.get("text", "")
                    if text:
                        memories.append(text)
            elif isinstance(results, list):
                for r in results:
                    if isinstance(r, dict):
                        text = r.get("memory") or r.get("text", "")
                        if text:
                            memories.append(text)
                    elif isinstance(r, str):
                        memories.append(r)

            return memories if memories else None

        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")
            return None

    async def store(self, user_message: str, assistant_response: str, user_id: str):
        """
        Store a conversation exchange. Mem0 automatically extracts
        relevant facts and stores them as memories.
        """
        self._ensure_init()
        if not self._initialized:
            return

        try:
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_response},
            ]
            self._mem0.add(messages=messages, user_id=f"colonel:{user_id}")
            logger.debug(f"Stored memory for user {user_id}")
        except Exception as e:
            logger.warning(f"Memory store failed: {e}")

    async def count(self) -> int:
        """Get total number of stored memories."""
        self._ensure_init()
        if not self._initialized:
            return 0

        try:
            all_memories = self._mem0.get_all()
            if isinstance(all_memories, dict) and "results" in all_memories:
                return len(all_memories["results"])
            elif isinstance(all_memories, list):
                return len(all_memories)
            return 0
        except Exception as e:
            logger.warning(f"Memory count failed: {e}")
            return 0

    async def search(self, query: str, limit: int = 10) -> List[dict]:
        """Search all memories (admin endpoint)."""
        self._ensure_init()
        if not self._initialized:
            return []

        try:
            results = self._mem0.search(query=query, limit=limit)
            if isinstance(results, dict) and "results" in results:
                return results["results"]
            elif isinstance(results, list):
                return results
            return []
        except Exception as e:
            logger.warning(f"Memory search failed: {e}")
            return []
