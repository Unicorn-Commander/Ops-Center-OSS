"""
LLM Configuration Manager
Manages AI servers and 3rd party API keys for Ops-Center

Handles:
- AI server configurations (vLLM, Ollama, llama.cpp, OpenAI-compatible)
- 3rd party API key storage (encrypted)
- Active provider selection for each purpose (chat/embeddings/reranking)
- Health checks and testing
- Audit logging
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json

import asyncpg
from cryptography.fernet import Fernet
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class ServerType(str, Enum):
    """Supported AI server types"""
    VLLM = "vllm"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    OPENAI_COMPATIBLE = "openai-compatible"


class HealthStatus(str, Enum):
    """Health status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ProviderType(str, Enum):
    """Provider types for active configuration"""
    AI_SERVER = "ai_server"
    API_KEY = "api_key"


class Purpose(str, Enum):
    """Purposes for LLM usage"""
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    RERANKING = "reranking"


@dataclass
class AIServer:
    """AI Server configuration"""
    id: Optional[int] = None
    name: str = ""
    server_type: str = ""
    base_url: str = ""
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    enabled: bool = True
    use_for_chat: bool = False
    use_for_embeddings: bool = False
    use_for_reranking: bool = False
    last_health_check: Optional[datetime] = None
    health_status: str = HealthStatus.UNKNOWN.value
    metadata: Dict[str, Any] = None
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class APIKey:
    """3rd Party API Key (encrypted)"""
    id: Optional[int] = None
    provider: str = ""
    key_name: str = ""
    encrypted_key: str = ""  # Never expose plaintext
    enabled: bool = True
    use_for_ops_center: bool = False
    last_used: Optional[datetime] = None
    requests_count: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = None
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def masked_key(self) -> str:
        """Return masked version of key (show only last 4 chars)"""
        if not self.encrypted_key:
            return "****"
        # This is the encrypted key, we need to decrypt first
        # But for display purposes, we'll show ****[last4]
        return "****"


@dataclass
class ActiveProvider:
    """Active provider configuration"""
    purpose: str
    provider_type: str
    provider_id: int
    fallback_provider_type: Optional[str] = None
    fallback_provider_id: Optional[int] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# LLM Configuration Manager
# ============================================================================

class LLMConfigManager:
    """Manages AI servers, API keys, and active provider configuration"""

    def __init__(self, db_pool: asyncpg.Pool, encryption_key: str):
        """
        Initialize manager

        Args:
            db_pool: PostgreSQL connection pool
            encryption_key: Fernet encryption key for API keys
        """
        self.db = db_pool
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()

    # ========================================================================
    # AI Server Management
    # ========================================================================

    async def list_ai_servers(self, user_id: Optional[str] = None, enabled_only: bool = False) -> List[AIServer]:
        """
        List all configured AI servers

        Args:
            user_id: Filter by creator (None = all)
            enabled_only: Only return enabled servers

        Returns:
            List of AIServer objects
        """
        try:
            query = "SELECT * FROM ai_servers WHERE 1=1"
            params = []

            if user_id:
                query += " AND created_by = $1"
                params.append(user_id)

            if enabled_only:
                query += f" AND enabled = ${len(params) + 1}"
                params.append(True)

            query += " ORDER BY created_at DESC"

            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, *params)

            servers = []
            for row in rows:
                servers.append(AIServer(
                    id=row['id'],
                    name=row['name'],
                    server_type=row['server_type'],
                    base_url=row['base_url'],
                    api_key=row['api_key'],
                    model_path=row['model_path'],
                    enabled=row['enabled'],
                    use_for_chat=row['use_for_chat'],
                    use_for_embeddings=row['use_for_embeddings'],
                    use_for_reranking=row['use_for_reranking'],
                    last_health_check=row['last_health_check'],
                    health_status=row['health_status'],
                    metadata=row['metadata'] or {},
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))

            logger.info(f"Listed {len(servers)} AI servers (user={user_id}, enabled_only={enabled_only})")
            return servers

        except Exception as e:
            logger.error(f"Failed to list AI servers: {e}")
            raise

    async def get_ai_server(self, server_id: int) -> Optional[AIServer]:
        """Get specific AI server by ID"""
        try:
            async with self.db.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM ai_servers WHERE id = $1", server_id)

            if not row:
                return None

            return AIServer(
                id=row['id'],
                name=row['name'],
                server_type=row['server_type'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                model_path=row['model_path'],
                enabled=row['enabled'],
                use_for_chat=row['use_for_chat'],
                use_for_embeddings=row['use_for_embeddings'],
                use_for_reranking=row['use_for_reranking'],
                last_health_check=row['last_health_check'],
                health_status=row['health_status'],
                metadata=row['metadata'] or {},
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

        except Exception as e:
            logger.error(f"Failed to get AI server {server_id}: {e}")
            raise

    async def add_ai_server(self, server: AIServer, user_id: str) -> AIServer:
        """
        Add new AI server configuration

        Args:
            server: AIServer object (id will be ignored)
            user_id: User creating the server

        Returns:
            Created AIServer with ID populated
        """
        try:
            async with self.db.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO ai_servers (
                        name, server_type, base_url, api_key, model_path,
                        enabled, use_for_chat, use_for_embeddings, use_for_reranking,
                        health_status, metadata, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING *
                    """,
                    server.name, server.server_type, server.base_url, server.api_key,
                    server.model_path, server.enabled, server.use_for_chat,
                    server.use_for_embeddings, server.use_for_reranking,
                    server.health_status, json.dumps(server.metadata), user_id
                )

            created = AIServer(
                id=row['id'],
                name=row['name'],
                server_type=row['server_type'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                model_path=row['model_path'],
                enabled=row['enabled'],
                use_for_chat=row['use_for_chat'],
                use_for_embeddings=row['use_for_embeddings'],
                use_for_reranking=row['use_for_reranking'],
                health_status=row['health_status'],
                metadata=row['metadata'] or {},
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

            # Audit log
            await self._audit_log(
                action="add_server",
                entity_type="ai_server",
                entity_id=created.id,
                user_id=user_id,
                changes={"server": asdict(created)}
            )

            logger.info(f"Added AI server: {created.name} (id={created.id})")
            return created

        except Exception as e:
            logger.error(f"Failed to add AI server: {e}")
            raise

    async def update_ai_server(self, server_id: int, updates: Dict[str, Any], user_id: str) -> AIServer:
        """
        Update AI server configuration

        Args:
            server_id: Server ID to update
            updates: Dictionary of fields to update
            user_id: User making the update

        Returns:
            Updated AIServer object
        """
        try:
            # Build dynamic UPDATE query
            allowed_fields = [
                'name', 'server_type', 'base_url', 'api_key', 'model_path',
                'enabled', 'use_for_chat', 'use_for_embeddings', 'use_for_reranking',
                'health_status', 'metadata'
            ]

            update_fields = []
            params = []
            param_idx = 1

            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'metadata' and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ${param_idx}")
                    params.append(value)
                    param_idx += 1

            if not update_fields:
                raise ValueError("No valid fields to update")

            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            params.append(datetime.utcnow())
            param_idx += 1

            # Add server_id as last param
            params.append(server_id)

            query = f"""
                UPDATE ai_servers
                SET {', '.join(update_fields)}
                WHERE id = ${param_idx}
                RETURNING *
            """

            async with self.db.acquire() as conn:
                row = await conn.fetchrow(query, *params)

            if not row:
                raise ValueError(f"Server {server_id} not found")

            updated = AIServer(
                id=row['id'],
                name=row['name'],
                server_type=row['server_type'],
                base_url=row['base_url'],
                api_key=row['api_key'],
                model_path=row['model_path'],
                enabled=row['enabled'],
                use_for_chat=row['use_for_chat'],
                use_for_embeddings=row['use_for_embeddings'],
                use_for_reranking=row['use_for_reranking'],
                last_health_check=row['last_health_check'],
                health_status=row['health_status'],
                metadata=row['metadata'] or {},
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )

            # Audit log
            await self._audit_log(
                action="update_server",
                entity_type="ai_server",
                entity_id=server_id,
                user_id=user_id,
                changes=updates
            )

            logger.info(f"Updated AI server {server_id}: {updates}")
            return updated

        except Exception as e:
            logger.error(f"Failed to update AI server {server_id}: {e}")
            raise

    async def delete_ai_server(self, server_id: int, user_id: str):
        """
        Delete AI server configuration

        Args:
            server_id: Server ID to delete
            user_id: User deleting the server
        """
        try:
            async with self.db.acquire() as conn:
                # Check if server is in use
                active = await conn.fetch(
                    "SELECT purpose FROM active_providers WHERE provider_type = 'ai_server' AND provider_id = $1",
                    server_id
                )

                if active:
                    purposes = [row['purpose'] for row in active]
                    raise ValueError(f"Cannot delete server in use for: {', '.join(purposes)}")

                # Delete server
                result = await conn.execute("DELETE FROM ai_servers WHERE id = $1", server_id)

            if result == "DELETE 0":
                raise ValueError(f"Server {server_id} not found")

            # Audit log
            await self._audit_log(
                action="delete_server",
                entity_type="ai_server",
                entity_id=server_id,
                user_id=user_id,
                changes={}
            )

            logger.info(f"Deleted AI server {server_id}")

        except Exception as e:
            logger.error(f"Failed to delete AI server {server_id}: {e}")
            raise

    async def test_ai_server(self, server_id: int) -> Tuple[HealthStatus, str]:
        """
        Test connection to AI server

        Args:
            server_id: Server ID to test

        Returns:
            Tuple of (HealthStatus, message)
        """
        try:
            server = await self.get_ai_server(server_id)
            if not server:
                return HealthStatus.DOWN, "Server not found"

            # Test based on server type
            if server.server_type == ServerType.VLLM.value:
                status, msg = await self._test_vllm(server)
            elif server.server_type == ServerType.OLLAMA.value:
                status, msg = await self._test_ollama(server)
            elif server.server_type == ServerType.LLAMACPP.value:
                status, msg = await self._test_llamacpp(server)
            elif server.server_type == ServerType.OPENAI_COMPATIBLE.value:
                status, msg = await self._test_openai_compatible(server)
            else:
                status, msg = HealthStatus.UNKNOWN, f"Unknown server type: {server.server_type}"

            # Update health status in database
            await self.update_ai_server(
                server_id,
                {
                    'health_status': status.value,
                    'last_health_check': datetime.utcnow()
                },
                user_id="system"
            )

            return status, msg

        except Exception as e:
            logger.error(f"Failed to test AI server {server_id}: {e}")
            return HealthStatus.DOWN, str(e)

    async def _test_vllm(self, server: AIServer) -> Tuple[HealthStatus, str]:
        """Test vLLM server via /v1/models endpoint"""
        try:
            headers = {}
            if server.api_key:
                headers['Authorization'] = f'Bearer {server.api_key}'

            response = await self.http_client.get(
                f"{server.base_url.rstrip('/')}/v1/models",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                return HealthStatus.HEALTHY, f"Healthy - {len(models)} models available"
            else:
                return HealthStatus.DOWN, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return HealthStatus.DOWN, str(e)

    async def _test_ollama(self, server: AIServer) -> Tuple[HealthStatus, str]:
        """Test Ollama server via /api/tags endpoint"""
        try:
            response = await self.http_client.get(
                f"{server.base_url.rstrip('/')}/api/tags"
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return HealthStatus.HEALTHY, f"Healthy - {len(models)} models available"
            else:
                return HealthStatus.DOWN, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return HealthStatus.DOWN, str(e)

    async def _test_llamacpp(self, server: AIServer) -> Tuple[HealthStatus, str]:
        """Test llama.cpp server via /v1/models endpoint"""
        try:
            response = await self.http_client.get(
                f"{server.base_url.rstrip('/')}/v1/models"
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                return HealthStatus.HEALTHY, f"Healthy - {len(models)} models available"
            else:
                return HealthStatus.DOWN, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return HealthStatus.DOWN, str(e)

    async def _test_openai_compatible(self, server: AIServer) -> Tuple[HealthStatus, str]:
        """Test OpenAI-compatible server"""
        try:
            headers = {}
            if server.api_key:
                headers['Authorization'] = f'Bearer {server.api_key}'

            response = await self.http_client.get(
                f"{server.base_url.rstrip('/')}/v1/models",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                return HealthStatus.HEALTHY, f"Healthy - {len(models)} models available"
            else:
                return HealthStatus.DOWN, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return HealthStatus.DOWN, str(e)

    async def get_ai_server_models(self, server_id: int) -> List[str]:
        """
        Get list of available models from AI server

        Args:
            server_id: Server ID

        Returns:
            List of model names
        """
        try:
            server = await self.get_ai_server(server_id)
            if not server:
                return []

            headers = {}
            if server.api_key:
                headers['Authorization'] = f'Bearer {server.api_key}'

            # Try /v1/models endpoint (vLLM, llama.cpp, OpenAI-compatible)
            if server.server_type in [ServerType.VLLM.value, ServerType.LLAMACPP.value, ServerType.OPENAI_COMPATIBLE.value]:
                response = await self.http_client.get(
                    f"{server.base_url.rstrip('/')}/v1/models",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m['id'] for m in data.get('data', [])]

            # Ollama uses different endpoint
            elif server.server_type == ServerType.OLLAMA.value:
                response = await self.http_client.get(
                    f"{server.base_url.rstrip('/')}/api/tags"
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m['name'] for m in data.get('models', [])]

            return []

        except Exception as e:
            logger.error(f"Failed to get models from server {server_id}: {e}")
            return []

    # ========================================================================
    # API Key Management
    # ========================================================================

    async def list_api_keys(self, user_id: Optional[str] = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all API keys (MASKED - never return plaintext)

        Args:
            user_id: Filter by creator (None = all)
            enabled_only: Only return enabled keys

        Returns:
            List of API key info (with masked keys)
        """
        try:
            query = "SELECT * FROM llm_api_keys WHERE 1=1"
            params = []

            if user_id:
                query += " AND created_by = $1"
                params.append(user_id)

            if enabled_only:
                query += f" AND enabled = ${len(params) + 1}"
                params.append(True)

            query += " ORDER BY created_at DESC"

            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, *params)

            keys = []
            for row in rows:
                # Return everything EXCEPT the encrypted key (show masked version)
                keys.append({
                    'id': row['id'],
                    'provider': row['provider'],
                    'key_name': row['key_name'],
                    'masked_key': '****' + (row['encrypted_key'][-4:] if len(row['encrypted_key']) > 4 else '****'),
                    'enabled': row['enabled'],
                    'use_for_ops_center': row['use_for_ops_center'],
                    'last_used': row['last_used'],
                    'requests_count': row['requests_count'],
                    'tokens_used': row['tokens_used'],
                    'cost_usd': float(row['cost_usd']),
                    'metadata': row['metadata'] or {},
                    'created_by': row['created_by'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            logger.info(f"Listed {len(keys)} API keys (user={user_id}, enabled_only={enabled_only})")
            return keys

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            raise

    async def get_api_key(self, key_id: int, decrypt: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get specific API key by ID

        Args:
            key_id: API key ID
            decrypt: If True, decrypt the key (USE CAREFULLY - for testing only)

        Returns:
            API key info (masked by default)
        """
        try:
            async with self.db.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM llm_api_keys WHERE id = $1", key_id)

            if not row:
                return None

            key_info = {
                'id': row['id'],
                'provider': row['provider'],
                'key_name': row['key_name'],
                'enabled': row['enabled'],
                'use_for_ops_center': row['use_for_ops_center'],
                'last_used': row['last_used'],
                'requests_count': row['requests_count'],
                'tokens_used': row['tokens_used'],
                'cost_usd': float(row['cost_usd']),
                'metadata': row['metadata'] or {},
                'created_by': row['created_by'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }

            if decrypt:
                # DANGER: Only use for testing/validation
                decrypted = self.cipher.decrypt(row['encrypted_key'].encode()).decode()
                key_info['api_key'] = decrypted
            else:
                key_info['masked_key'] = '****' + (row['encrypted_key'][-4:] if len(row['encrypted_key']) > 4 else '****')

            return key_info

        except Exception as e:
            logger.error(f"Failed to get API key {key_id}: {e}")
            raise

    async def add_api_key(self, provider: str, key_name: str, api_key: str,
                         use_for_ops_center: bool, user_id: str,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add new API key (encrypted)

        Args:
            provider: Provider name (openrouter, openai, anthropic, etc.)
            key_name: Friendly name for the key
            api_key: Plaintext API key (will be encrypted)
            use_for_ops_center: Use for ops-center services
            user_id: User adding the key
            metadata: Optional metadata (rate limits, etc.)

        Returns:
            Created API key info (masked)
        """
        try:
            # Encrypt the API key
            encrypted = self.cipher.encrypt(api_key.encode()).decode()

            async with self.db.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO llm_api_keys (
                        provider, key_name, encrypted_key, enabled,
                        use_for_ops_center, metadata, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    provider, key_name, encrypted, True, use_for_ops_center,
                    json.dumps(metadata or {}), user_id
                )

            created = {
                'id': row['id'],
                'provider': row['provider'],
                'key_name': row['key_name'],
                'masked_key': '****' + (encrypted[-4:] if len(encrypted) > 4 else '****'),
                'enabled': row['enabled'],
                'use_for_ops_center': row['use_for_ops_center'],
                'metadata': row['metadata'] or {},
                'created_by': row['created_by'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }

            # Audit log
            await self._audit_log(
                action="add_key",
                entity_type="api_key",
                entity_id=created['id'],
                user_id=user_id,
                changes={'provider': provider, 'key_name': key_name}
            )

            logger.info(f"Added API key: {provider}/{key_name} (id={created['id']})")
            return created

        except Exception as e:
            logger.error(f"Failed to add API key: {e}")
            raise

    async def update_api_key(self, key_id: int, updates: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Update API key

        Args:
            key_id: Key ID to update
            updates: Dictionary of fields to update (can include 'api_key' to re-encrypt)
            user_id: User making the update

        Returns:
            Updated API key info (masked)
        """
        try:
            # Build dynamic UPDATE query
            allowed_fields = ['key_name', 'enabled', 'use_for_ops_center', 'metadata']

            update_fields = []
            params = []
            param_idx = 1

            for field, value in updates.items():
                if field == 'api_key':
                    # Re-encrypt new key
                    encrypted = self.cipher.encrypt(value.encode()).decode()
                    update_fields.append(f"encrypted_key = ${param_idx}")
                    params.append(encrypted)
                    param_idx += 1
                elif field in allowed_fields:
                    if field == 'metadata' and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ${param_idx}")
                    params.append(value)
                    param_idx += 1

            if not update_fields:
                raise ValueError("No valid fields to update")

            # Add updated_at
            update_fields.append(f"updated_at = ${param_idx}")
            params.append(datetime.utcnow())
            param_idx += 1

            # Add key_id as last param
            params.append(key_id)

            query = f"""
                UPDATE llm_api_keys
                SET {', '.join(update_fields)}
                WHERE id = ${param_idx}
                RETURNING *
            """

            async with self.db.acquire() as conn:
                row = await conn.fetchrow(query, *params)

            if not row:
                raise ValueError(f"API key {key_id} not found")

            updated = {
                'id': row['id'],
                'provider': row['provider'],
                'key_name': row['key_name'],
                'masked_key': '****' + (row['encrypted_key'][-4:] if len(row['encrypted_key']) > 4 else '****'),
                'enabled': row['enabled'],
                'use_for_ops_center': row['use_for_ops_center'],
                'metadata': row['metadata'] or {},
                'created_by': row['created_by'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }

            # Audit log
            await self._audit_log(
                action="update_key",
                entity_type="api_key",
                entity_id=key_id,
                user_id=user_id,
                changes={k: v for k, v in updates.items() if k != 'api_key'}  # Don't log key
            )

            logger.info(f"Updated API key {key_id}: {list(updates.keys())}")
            return updated

        except Exception as e:
            logger.error(f"Failed to update API key {key_id}: {e}")
            raise

    async def delete_api_key(self, key_id: int, user_id: str):
        """
        Delete API key

        Args:
            key_id: Key ID to delete
            user_id: User deleting the key
        """
        try:
            async with self.db.acquire() as conn:
                # Check if key is in use
                active = await conn.fetch(
                    "SELECT purpose FROM active_providers WHERE provider_type = 'api_key' AND provider_id = $1",
                    key_id
                )

                if active:
                    purposes = [row['purpose'] for row in active]
                    raise ValueError(f"Cannot delete API key in use for: {', '.join(purposes)}")

                # Delete key
                result = await conn.execute("DELETE FROM llm_api_keys WHERE id = $1", key_id)

            if result == "DELETE 0":
                raise ValueError(f"API key {key_id} not found")

            # Audit log
            await self._audit_log(
                action="delete_key",
                entity_type="api_key",
                entity_id=key_id,
                user_id=user_id,
                changes={}
            )

            logger.info(f"Deleted API key {key_id}")

        except Exception as e:
            logger.error(f"Failed to delete API key {key_id}: {e}")
            raise

    async def test_api_key(self, key_id: int) -> Tuple[bool, str]:
        """
        Test API key validity with minimal request

        Args:
            key_id: Key ID to test

        Returns:
            Tuple of (success, message)
        """
        try:
            key_info = await self.get_api_key(key_id, decrypt=True)
            if not key_info:
                return False, "API key not found"

            api_key = key_info.get('api_key')
            provider = key_info['provider']

            # Test based on provider
            if provider == 'openrouter':
                success, msg = await self._test_openrouter_key(api_key)
            elif provider == 'openai':
                success, msg = await self._test_openai_key(api_key)
            elif provider == 'anthropic':
                success, msg = await self._test_anthropic_key(api_key)
            else:
                success, msg = False, f"Unknown provider: {provider}"

            return success, msg

        except Exception as e:
            logger.error(f"Failed to test API key {key_id}: {e}")
            return False, str(e)

    async def _test_openrouter_key(self, api_key: str) -> Tuple[bool, str]:
        """Test OpenRouter API key"""
        try:
            response = await self.http_client.get(
                "https://openrouter.ai/api/v1/models",
                headers={'Authorization': f'Bearer {api_key}'}
            )

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get('data', []))
                return True, f"Valid - {model_count} models available"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return False, str(e)

    async def _test_openai_key(self, api_key: str) -> Tuple[bool, str]:
        """Test OpenAI API key"""
        try:
            response = await self.http_client.get(
                "https://api.openai.com/v1/models",
                headers={'Authorization': f'Bearer {api_key}'}
            )

            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get('data', []))
                return True, f"Valid - {model_count} models available"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return False, str(e)

    async def _test_anthropic_key(self, api_key: str) -> Tuple[bool, str]:
        """Test Anthropic API key (minimal messages request)"""
        try:
            response = await self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 1,
                    'messages': [{'role': 'user', 'content': 'Hi'}]
                }
            )

            if response.status_code == 200:
                return True, "Valid - API key works"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            return False, str(e)

    # ========================================================================
    # Active Provider Configuration
    # ========================================================================

    async def get_active_provider(self, purpose: str) -> Optional[Dict[str, Any]]:
        """
        Get active provider for a purpose

        Args:
            purpose: chat, embeddings, or reranking

        Returns:
            Provider info or None
        """
        try:
            async with self.db.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM active_providers WHERE purpose = $1",
                    purpose
                )

            if not row:
                return None

            # Fetch the actual provider details
            if row['provider_type'] == ProviderType.AI_SERVER.value:
                provider = await self.get_ai_server(row['provider_id'])
                provider_dict = asdict(provider) if provider else None
            else:  # api_key
                provider = await self.get_api_key(row['provider_id'])
                provider_dict = provider

            return {
                'purpose': row['purpose'],
                'provider_type': row['provider_type'],
                'provider_id': row['provider_id'],
                'provider': provider_dict,
                'fallback_provider_type': row['fallback_provider_type'],
                'fallback_provider_id': row['fallback_provider_id'],
                'updated_by': row['updated_by'],
                'updated_at': row['updated_at']
            }

        except Exception as e:
            logger.error(f"Failed to get active provider for {purpose}: {e}")
            raise

    async def set_active_provider(self, purpose: str, provider_type: str,
                                  provider_id: int, user_id: str,
                                  fallback_provider_type: Optional[str] = None,
                                  fallback_provider_id: Optional[int] = None):
        """
        Set active provider for a purpose

        Args:
            purpose: chat, embeddings, or reranking
            provider_type: ai_server or api_key
            provider_id: ID of the provider
            user_id: User making the change
            fallback_provider_type: Optional fallback provider type
            fallback_provider_id: Optional fallback provider ID
        """
        try:
            # Verify provider exists
            if provider_type == ProviderType.AI_SERVER.value:
                provider = await self.get_ai_server(provider_id)
                if not provider:
                    raise ValueError(f"AI server {provider_id} not found")
            elif provider_type == ProviderType.API_KEY.value:
                provider = await self.get_api_key(provider_id)
                if not provider:
                    raise ValueError(f"API key {provider_id} not found")
            else:
                raise ValueError(f"Invalid provider_type: {provider_type}")

            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO active_providers (
                        purpose, provider_type, provider_id,
                        fallback_provider_type, fallback_provider_id, updated_by
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (purpose) DO UPDATE SET
                        provider_type = EXCLUDED.provider_type,
                        provider_id = EXCLUDED.provider_id,
                        fallback_provider_type = EXCLUDED.fallback_provider_type,
                        fallback_provider_id = EXCLUDED.fallback_provider_id,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = NOW()
                    """,
                    purpose, provider_type, provider_id,
                    fallback_provider_type, fallback_provider_id, user_id
                )

            # Audit log
            await self._audit_log(
                action="set_active",
                entity_type="active_provider",
                entity_id=None,
                user_id=user_id,
                changes={
                    'purpose': purpose,
                    'provider_type': provider_type,
                    'provider_id': provider_id
                }
            )

            logger.info(f"Set active provider for {purpose}: {provider_type}/{provider_id}")

        except Exception as e:
            logger.error(f"Failed to set active provider: {e}")
            raise

    async def get_all_active_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all active providers for all purposes"""
        try:
            providers = {}
            for purpose in [Purpose.CHAT.value, Purpose.EMBEDDINGS.value, Purpose.RERANKING.value]:
                provider = await self.get_active_provider(purpose)
                if provider:
                    providers[purpose] = provider
            return providers
        except Exception as e:
            logger.error(f"Failed to get all active providers: {e}")
            raise

    # ========================================================================
    # Utilities
    # ========================================================================

    async def _audit_log(self, action: str, entity_type: str, entity_id: Optional[int],
                        user_id: str, changes: Dict[str, Any]):
        """Log configuration change to audit table"""
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO llm_config_audit (action, entity_type, entity_id, user_id, changes)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    action, entity_type, entity_id, user_id, json.dumps(changes)
                )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            # Don't raise - audit log failure shouldn't break operations

    async def initialize_defaults(self):
        """Initialize default configuration (called on startup)"""
        try:
            # Check if any API keys exist
            existing_keys = await self.list_api_keys()

            if not existing_keys:
                # Pre-populate OpenRouter key
                logger.info("No API keys found - initializing default OpenRouter key")
                await self.add_api_key(
                    provider="openrouter",
                    key_name="Default OpenRouter Key",
                    api_key="sk-or-v1-your-openrouter-key",
                    use_for_ops_center=True,
                    user_id="system",
                    metadata={"source": "pre-populated"}
                )

                # Set as active provider for chat
                keys = await self.list_api_keys()
                if keys:
                    await self.set_active_provider(
                        purpose=Purpose.CHAT.value,
                        provider_type=ProviderType.API_KEY.value,
                        provider_id=keys[0]['id'],
                        user_id="system"
                    )
                    logger.info("Set default OpenRouter key as active chat provider")

        except Exception as e:
            logger.error(f"Failed to initialize defaults: {e}")
            # Don't raise - initialization failure shouldn't break startup
