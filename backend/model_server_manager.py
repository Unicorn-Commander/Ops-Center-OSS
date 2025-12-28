"""
Model Server Manager
Handles database operations and coordination for distributed model management
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncpg
from cryptography.fernet import Fernet
import base64
from model_adapters import create_adapter, ServerAdapter, ModelInfo, ServerMetrics

logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()
    logger.warning("No ENCRYPTION_KEY found, generated temporary key")

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if len(ENCRYPTION_KEY) == 44 else base64.urlsafe_b64encode(ENCRYPTION_KEY.encode()[:32]))

# Pydantic models for API
class ModelServerCreate(BaseModel):
    name: str
    server_type: str  # 'vllm', 'ollama', 'embedding', 'reranking'
    base_url: str
    api_key: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}

class ModelServerUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    capabilities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ModelServerResponse(BaseModel):
    id: str
    name: str
    server_type: str
    base_url: str
    is_active: bool
    capabilities: Dict[str, Any]
    metadata: Dict[str, Any]
    last_health_check: Optional[datetime]
    health_status: str
    created_at: datetime
    updated_at: datetime

class ModelRouteCreate(BaseModel):
    model_pattern: str
    server_priorities: List[Dict[str, Any]]
    load_balancing_strategy: str = 'round_robin'
    fallback_behavior: str = 'next_priority'

class ModelServerManager:
    """Manages model servers and routing"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.environ.get(
            'DATABASE_URL',
            f"postgresql://{os.environ.get('POSTGRES_USER', 'unicorn')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', 'password')}@"
            f"{os.environ.get('POSTGRES_HOST', 'unicorn-postgresql')}:5432/"
            f"{os.environ.get('POSTGRES_DB', 'unicorn_db')}"
        )
        self.db_pool = None
        self.adapters: Dict[str, ServerAdapter] = {}

    async def initialize(self):
        """Initialize database connection pool and run migrations"""
        try:
            self.db_pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=10)
            await self._run_migrations()
            logger.info("Model server manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model server manager: {e}")
            raise

    async def _run_migrations(self):
        """Run database migrations"""
        migration_file = os.path.join(
            os.path.dirname(__file__),
            'migrations',
            '001_model_servers.sql'
        )

        if os.path.exists(migration_file):
            async with self.db_pool.acquire() as conn:
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                    await conn.execute(migration_sql)
                    logger.info("Database migrations completed")

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        if api_key:
            return cipher_suite.encrypt(api_key.encode()).decode()
        return None

    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key from storage"""
        if encrypted_key:
            return cipher_suite.decrypt(encrypted_key.encode()).decode()
        return None

    async def create_server(self, server: ModelServerCreate) -> ModelServerResponse:
        """Create a new model server configuration"""
        async with self.db_pool.acquire() as conn:
            # Encrypt API key if provided
            encrypted_key = self._encrypt_api_key(server.api_key) if server.api_key else None

            # Test connection before saving
            try:
                adapter = create_adapter(server.server_type, server.base_url, server.api_key)
                is_connected = await adapter.test_connection()
                health_status = 'online' if is_connected else 'offline'
            except Exception as e:
                logger.error(f"Failed to test connection: {e}")
                health_status = 'unknown'

            # Insert into database
            row = await conn.fetchrow("""
                INSERT INTO model_servers (
                    name, server_type, base_url, api_key, capabilities, metadata,
                    health_status, last_health_check
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """, server.name, server.server_type, server.base_url, encrypted_key,
                json.dumps(server.capabilities), json.dumps(server.metadata),
                health_status, datetime.now())

            return ModelServerResponse(**dict(row))

    async def get_servers(self, server_type: Optional[str] = None) -> List[ModelServerResponse]:
        """Get all configured servers, optionally filtered by type"""
        async with self.db_pool.acquire() as conn:
            if server_type:
                rows = await conn.fetch(
                    "SELECT * FROM model_servers WHERE server_type = $1 ORDER BY created_at DESC",
                    server_type
                )
            else:
                rows = await conn.fetch("SELECT * FROM model_servers ORDER BY created_at DESC")

            return [ModelServerResponse(**dict(row)) for row in rows]

    async def get_server(self, server_id: str) -> ModelServerResponse:
        """Get a specific server configuration"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM model_servers WHERE id = $1",
                uuid.UUID(server_id)
            )
            if not row:
                raise ValueError(f"Server {server_id} not found")
            return ModelServerResponse(**dict(row))

    async def update_server(self, server_id: str, update: ModelServerUpdate) -> ModelServerResponse:
        """Update server configuration"""
        async with self.db_pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            values = []
            param_count = 1

            if update.name is not None:
                updates.append(f"name = ${param_count}")
                values.append(update.name)
                param_count += 1

            if update.base_url is not None:
                updates.append(f"base_url = ${param_count}")
                values.append(update.base_url)
                param_count += 1

            if update.api_key is not None:
                updates.append(f"api_key = ${param_count}")
                values.append(self._encrypt_api_key(update.api_key))
                param_count += 1

            if update.is_active is not None:
                updates.append(f"is_active = ${param_count}")
                values.append(update.is_active)
                param_count += 1

            if update.capabilities is not None:
                updates.append(f"capabilities = ${param_count}")
                values.append(json.dumps(update.capabilities))
                param_count += 1

            if update.metadata is not None:
                updates.append(f"metadata = ${param_count}")
                values.append(json.dumps(update.metadata))
                param_count += 1

            values.append(uuid.UUID(server_id))

            query = f"UPDATE model_servers SET {', '.join(updates)} WHERE id = ${param_count} RETURNING *"
            row = await conn.fetchrow(query, *values)

            return ModelServerResponse(**dict(row))

    async def delete_server(self, server_id: str) -> bool:
        """Delete a server configuration"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM model_servers WHERE id = $1",
                uuid.UUID(server_id)
            )
            return result.split()[-1] != '0'

    async def test_connection(self, server_id: str) -> Dict[str, Any]:
        """Test connection to a specific server"""
        server = await self.get_server(server_id)

        async with self.db_pool.acquire() as conn:
            # Get decrypted API key
            row = await conn.fetchrow(
                "SELECT api_key FROM model_servers WHERE id = $1",
                uuid.UUID(server_id)
            )
            api_key = self._decrypt_api_key(row['api_key']) if row['api_key'] else None

        # Create adapter and test
        adapter = create_adapter(server.server_type, server.base_url, api_key)
        is_connected = await adapter.test_connection()

        # Update health status
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE model_servers
                SET health_status = $1, last_health_check = $2
                WHERE id = $3
            """, 'online' if is_connected else 'offline', datetime.now(), uuid.UUID(server_id))

        return {
            "connected": is_connected,
            "server_id": server_id,
            "server_type": server.server_type,
            "base_url": server.base_url
        }

    async def get_server_models(self, server_id: str) -> List[ModelInfo]:
        """Get list of models available on a server"""
        server = await self.get_server(server_id)

        async with self.db_pool.acquire() as conn:
            # Get decrypted API key
            row = await conn.fetchrow(
                "SELECT api_key FROM model_servers WHERE id = $1",
                uuid.UUID(server_id)
            )
            api_key = self._decrypt_api_key(row['api_key']) if row['api_key'] else None

        # Create adapter and get models
        adapter = create_adapter(server.server_type, server.base_url, api_key)
        models = await adapter.list_models()

        # Update database with discovered models
        async with self.db_pool.acquire() as conn:
            # Clear existing models for this server
            await conn.execute(
                "DELETE FROM server_models WHERE server_id = $1",
                uuid.UUID(server_id)
            )

            # Insert discovered models
            for model in models:
                await conn.execute("""
                    INSERT INTO server_models (
                        server_id, model_id, model_name, model_size,
                        quantization, context_length, status, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, uuid.UUID(server_id), model.id, model.name, model.size,
                    model.quantization, model.context_length,
                    'loaded' if model.loaded else 'available',
                    json.dumps(model.metadata))

        return models

    async def get_server_metrics(self, server_id: str) -> ServerMetrics:
        """Get metrics for a specific server"""
        server = await self.get_server(server_id)

        async with self.db_pool.acquire() as conn:
            # Get decrypted API key
            row = await conn.fetchrow(
                "SELECT api_key FROM model_servers WHERE id = $1",
                uuid.UUID(server_id)
            )
            api_key = self._decrypt_api_key(row['api_key']) if row['api_key'] else None

        # Create adapter and get metrics
        adapter = create_adapter(server.server_type, server.base_url, api_key)
        metrics = await adapter.get_metrics()

        # Store metrics in database for history
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO server_metrics (
                    server_id, cpu_percent, memory_percent, gpu_percent,
                    gpu_memory_used, gpu_memory_total, active_requests,
                    total_requests, avg_response_time, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, uuid.UUID(server_id), metrics.cpu_percent, metrics.memory_percent,
                metrics.gpu_percent, metrics.gpu_memory_used, metrics.gpu_memory_total,
                metrics.active_requests, metrics.total_requests,
                metrics.avg_response_time, json.dumps(metrics.metadata))

        return metrics

    async def health_check_all(self):
        """Run health checks on all active servers"""
        servers = await self.get_servers()
        results = []

        for server in servers:
            if server.is_active:
                try:
                    result = await self.test_connection(server.id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Health check failed for {server.name}: {e}")
                    results.append({
                        "server_id": server.id,
                        "connected": False,
                        "error": str(e)
                    })

        return results

    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()

# Global instance
model_server_manager = ModelServerManager()