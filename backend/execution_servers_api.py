"""
Execution Servers API
Manages user-configured execution environments for code execution via Brigade
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
import asyncpg
import os
from datetime import datetime
import logging
import uuid
import json
import asyncio

from key_encryption import get_encryption
from tier_middleware import require_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/execution-servers", tags=["execution-servers"])

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ops_center")

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ===================================================================
# Request/Response Models
# ===================================================================

class SSHConfig(BaseModel):
    """SSH connection configuration"""
    host: str
    port: int = 22
    username: str
    auth_method: Literal["password", "key"] = "key"
    password: Optional[str] = None  # Encrypted
    private_key: Optional[str] = None  # Encrypted

class DockerConfig(BaseModel):
    """Docker execution configuration"""
    image: str = "python:3.11-slim"
    container_name: Optional[str] = None
    volumes: Optional[Dict[str, str]] = None
    environment: Optional[Dict[str, str]] = None

class KubernetesConfig(BaseModel):
    """Kubernetes execution configuration"""
    cluster_url: str
    namespace: str = "default"
    service_account_token: Optional[str] = None  # Encrypted
    kubeconfig: Optional[str] = None  # Encrypted

class ExecutionServerCreate(BaseModel):
    """Request to create execution server"""
    name: str = Field(..., min_length=1, max_length=255)
    server_type: Literal["ssh", "local", "docker", "kubernetes"]
    connection_config: Dict[str, Any]
    workspace_path: Optional[str] = Field(None, max_length=500)
    is_default: bool = False

    @validator('connection_config')
    def validate_config(cls, v, values):
        """Validate configuration based on server type"""
        server_type = values.get('server_type')

        if server_type == 'ssh':
            SSHConfig(**v)  # Validates structure
        elif server_type == 'docker':
            DockerConfig(**v)
        elif server_type == 'kubernetes':
            KubernetesConfig(**v)
        elif server_type == 'local':
            # Local doesn't need much config
            pass

        return v

class ExecutionServerUpdate(BaseModel):
    """Request to update execution server"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    connection_config: Optional[Dict[str, Any]] = None
    workspace_path: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class ExecutionServerResponse(BaseModel):
    """Response with execution server info"""
    id: str
    name: str
    server_type: str
    connection_config: Dict[str, Any]  # Sensitive data masked
    workspace_path: Optional[str]
    is_default: bool
    is_active: bool
    last_tested_at: Optional[str]
    test_status: Optional[str]
    created_at: str
    updated_at: str

class TestResult(BaseModel):
    """Result of server connection test"""
    status: Literal["success", "failed", "error"]
    message: str
    details: Optional[Dict[str, Any]] = None

# ===================================================================
# Helper Functions
# ===================================================================

async def get_user_email(request: Request) -> str:
    """Extract user email from session"""
    user = request.session.get("user")
    if not user or not user.get("email"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user["email"]

def mask_sensitive_config(config: Dict[str, Any], server_type: str) -> Dict[str, Any]:
    """Mask sensitive fields in connection config"""
    masked = config.copy()

    if server_type == 'ssh':
        if 'password' in masked:
            masked['password'] = '***masked***'
        if 'private_key' in masked:
            masked['private_key'] = '***masked***'
    elif server_type == 'kubernetes':
        if 'service_account_token' in masked:
            masked['service_account_token'] = '***masked***'
        if 'kubeconfig' in masked:
            masked['kubeconfig'] = '***masked***'

    return masked

def encrypt_sensitive_fields(config: Dict[str, Any], server_type: str) -> Dict[str, Any]:
    """Encrypt sensitive fields before storing"""
    encryption = get_encryption()
    encrypted = config.copy()

    if server_type == 'ssh':
        if 'password' in encrypted and encrypted['password']:
            encrypted['password'] = encryption.encrypt_key(encrypted['password'])
        if 'private_key' in encrypted and encrypted['private_key']:
            encrypted['private_key'] = encryption.encrypt_key(encrypted['private_key'])
    elif server_type == 'kubernetes':
        if 'service_account_token' in encrypted and encrypted['service_account_token']:
            encrypted['service_account_token'] = encryption.encrypt_key(encrypted['service_account_token'])
        if 'kubeconfig' in encrypted and encrypted['kubeconfig']:
            encrypted['kubeconfig'] = encryption.encrypt_key(encrypted['kubeconfig'])

    return encrypted

def decrypt_sensitive_fields(config: Dict[str, Any], server_type: str) -> Dict[str, Any]:
    """Decrypt sensitive fields when retrieving"""
    encryption = get_encryption()
    decrypted = config.copy()

    try:
        if server_type == 'ssh':
            if 'password' in decrypted and decrypted['password']:
                decrypted['password'] = encryption.decrypt_key(decrypted['password'])
            if 'private_key' in decrypted and decrypted['private_key']:
                decrypted['private_key'] = encryption.decrypt_key(decrypted['private_key'])
        elif server_type == 'kubernetes':
            if 'service_account_token' in decrypted and decrypted['service_account_token']:
                decrypted['service_account_token'] = encryption.decrypt_key(decrypted['service_account_token'])
            if 'kubeconfig' in decrypted and decrypted['kubeconfig']:
                decrypted['kubeconfig'] = encryption.decrypt_key(decrypted['kubeconfig'])
    except Exception as e:
        logger.error(f"Decryption failed: {e}")

    return decrypted

async def test_ssh_connection(config: Dict[str, Any]) -> TestResult:
    """Test SSH connection"""
    try:
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            'hostname': config['host'],
            'port': config.get('port', 22),
            'username': config['username'],
            'timeout': 10
        }

        if config.get('auth_method') == 'password' and config.get('password'):
            connect_kwargs['password'] = config['password']
        elif config.get('auth_method') == 'key' and config.get('private_key'):
            from io import StringIO
            key_file = StringIO(config['private_key'])
            connect_kwargs['pkey'] = paramiko.RSAKey.from_private_key(key_file)

        ssh.connect(**connect_kwargs)

        # Test command execution
        stdin, stdout, stderr = ssh.exec_command('echo "Connection successful"')
        output = stdout.read().decode().strip()

        ssh.close()

        if output == "Connection successful":
            return TestResult(
                status="success",
                message="SSH connection successful",
                details={"output": output}
            )
        else:
            return TestResult(
                status="failed",
                message="SSH connection failed: unexpected output"
            )

    except Exception as e:
        logger.error(f"SSH test failed: {e}")
        return TestResult(
            status="error",
            message=f"SSH connection error: {str(e)}"
        )

async def test_docker_connection(config: Dict[str, Any]) -> TestResult:
    """Test Docker connection"""
    try:
        import docker

        client = docker.from_env()

        # Test by listing containers
        containers = client.containers.list()

        return TestResult(
            status="success",
            message="Docker connection successful",
            details={"container_count": len(containers)}
        )
    except Exception as e:
        logger.error(f"Docker test failed: {e}")
        return TestResult(
            status="error",
            message=f"Docker connection error: {str(e)}"
        )

# ===================================================================
# API Endpoints
# ===================================================================

@router.get("", response_model=List[ExecutionServerResponse])
async def list_servers(request: Request):
    """List user's execution servers"""
    try:
        user_email = await get_user_email(request)

        # Get user ID from Keycloak
        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        conn = await get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, name, server_type, connection_config, workspace_path,
                       is_default, is_active, last_tested_at, test_status,
                       created_at, updated_at
                FROM user_execution_servers
                WHERE user_id = $1
                ORDER BY is_default DESC, created_at DESC
            """, user_id)

            servers = []
            for row in rows:
                # Mask sensitive data
                masked_config = mask_sensitive_config(
                    json.loads(row['connection_config']) if isinstance(row['connection_config'], str) else row['connection_config'],
                    row['server_type']
                )

                servers.append(ExecutionServerResponse(
                    id=str(row['id']),
                    name=row['name'],
                    server_type=row['server_type'],
                    connection_config=masked_config,
                    workspace_path=row['workspace_path'],
                    is_default=row['is_default'],
                    is_active=row['is_active'],
                    last_tested_at=row['last_tested_at'].isoformat() if row['last_tested_at'] else None,
                    test_status=row['test_status'],
                    created_at=row['created_at'].isoformat(),
                    updated_at=row['updated_at'].isoformat()
                ))

            return servers
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list execution servers")

@router.post("", response_model=ExecutionServerResponse)
@require_tier(["starter", "professional", "enterprise"])
async def create_server(server_data: ExecutionServerCreate, request: Request):
    """Create execution server (requires Starter tier or above)"""
    try:
        user_email = await get_user_email(request)

        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        # Encrypt sensitive fields
        encrypted_config = encrypt_sensitive_fields(
            server_data.connection_config,
            server_data.server_type
        )

        conn = await get_db_connection()
        try:
            server_id = uuid.uuid4()

            row = await conn.fetchrow("""
                INSERT INTO user_execution_servers
                (id, user_id, name, server_type, connection_config, workspace_path, is_default)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, name, server_type, connection_config, workspace_path,
                          is_default, is_active, last_tested_at, test_status,
                          created_at, updated_at
            """, server_id, user_id, server_data.name, server_data.server_type,
                json.dumps(encrypted_config), server_data.workspace_path, server_data.is_default)

            # Return masked config
            masked_config = mask_sensitive_config(encrypted_config, server_data.server_type)

            logger.info(f"Created execution server for {user_email}: {server_data.name}")

            return ExecutionServerResponse(
                id=str(row['id']),
                name=row['name'],
                server_type=row['server_type'],
                connection_config=masked_config,
                workspace_path=row['workspace_path'],
                is_default=row['is_default'],
                is_active=row['is_active'],
                last_tested_at=row['last_tested_at'].isoformat() if row['last_tested_at'] else None,
                test_status=row['test_status'],
                created_at=row['created_at'].isoformat(),
                updated_at=row['updated_at'].isoformat()
            )
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create execution server: {str(e)}")

@router.put("/{server_id}", response_model=ExecutionServerResponse)
async def update_server(server_id: str, server_data: ExecutionServerUpdate, request: Request):
    """Update execution server"""
    try:
        user_email = await get_user_email(request)

        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        conn = await get_db_connection()
        try:
            # Check ownership
            existing = await conn.fetchrow("""
                SELECT server_type, connection_config FROM user_execution_servers
                WHERE id = $1 AND user_id = $2
            """, uuid.UUID(server_id), user_id)

            if not existing:
                raise HTTPException(status_code=404, detail="Execution server not found")

            # Build update query dynamically
            updates = []
            values = []
            param_num = 1

            if server_data.name is not None:
                updates.append(f"name = ${param_num}")
                values.append(server_data.name)
                param_num += 1

            if server_data.connection_config is not None:
                encrypted_config = encrypt_sensitive_fields(
                    server_data.connection_config,
                    existing['server_type']
                )
                updates.append(f"connection_config = ${param_num}")
                values.append(json.dumps(encrypted_config))
                param_num += 1

            if server_data.workspace_path is not None:
                updates.append(f"workspace_path = ${param_num}")
                values.append(server_data.workspace_path)
                param_num += 1

            if server_data.is_default is not None:
                updates.append(f"is_default = ${param_num}")
                values.append(server_data.is_default)
                param_num += 1

            if server_data.is_active is not None:
                updates.append(f"is_active = ${param_num}")
                values.append(server_data.is_active)
                param_num += 1

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            values.extend([uuid.UUID(server_id), user_id])

            row = await conn.fetchrow(f"""
                UPDATE user_execution_servers
                SET {', '.join(updates)}
                WHERE id = ${param_num} AND user_id = ${param_num + 1}
                RETURNING id, name, server_type, connection_config, workspace_path,
                          is_default, is_active, last_tested_at, test_status,
                          created_at, updated_at
            """, *values)

            config = json.loads(row['connection_config']) if isinstance(row['connection_config'], str) else row['connection_config']
            masked_config = mask_sensitive_config(config, row['server_type'])

            return ExecutionServerResponse(
                id=str(row['id']),
                name=row['name'],
                server_type=row['server_type'],
                connection_config=masked_config,
                workspace_path=row['workspace_path'],
                is_default=row['is_default'],
                is_active=row['is_active'],
                last_tested_at=row['last_tested_at'].isoformat() if row['last_tested_at'] else None,
                test_status=row['test_status'],
                created_at=row['created_at'].isoformat(),
                updated_at=row['updated_at'].isoformat()
            )
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating server: {e}")
        raise HTTPException(status_code=500, detail="Failed to update execution server")

@router.delete("/{server_id}")
async def delete_server(server_id: str, request: Request):
    """Delete execution server"""
    try:
        user_email = await get_user_email(request)

        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        conn = await get_db_connection()
        try:
            result = await conn.execute("""
                DELETE FROM user_execution_servers
                WHERE id = $1 AND user_id = $2
            """, uuid.UUID(server_id), user_id)

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Execution server not found")

            logger.info(f"Deleted execution server {server_id} for {user_email}")

            return {"message": "Execution server deleted successfully"}
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete execution server")

@router.post("/{server_id}/test", response_model=TestResult)
async def test_server(server_id: str, request: Request):
    """Test execution server connection"""
    try:
        user_email = await get_user_email(request)

        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        conn = await get_db_connection()
        try:
            row = await conn.fetchrow("""
                SELECT server_type, connection_config
                FROM user_execution_servers
                WHERE id = $1 AND user_id = $2
            """, uuid.UUID(server_id), user_id)

            if not row:
                raise HTTPException(status_code=404, detail="Execution server not found")

            config = json.loads(row['connection_config']) if isinstance(row['connection_config'], str) else row['connection_config']
            decrypted_config = decrypt_sensitive_fields(config, row['server_type'])

            # Test based on server type
            if row['server_type'] == 'ssh':
                result = await test_ssh_connection(decrypted_config)
            elif row['server_type'] == 'docker':
                result = await test_docker_connection(decrypted_config)
            elif row['server_type'] == 'local':
                result = TestResult(status="success", message="Local execution available")
            else:
                result = TestResult(status="error", message="Test not implemented for this server type")

            # Update test results
            await conn.execute("""
                UPDATE user_execution_servers
                SET last_tested_at = $1, test_status = $2
                WHERE id = $3
            """, datetime.utcnow(), result.status, uuid.UUID(server_id))

            return result
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing server: {e}")
        raise HTTPException(status_code=500, detail="Failed to test execution server")

@router.get("/default", response_model=Optional[ExecutionServerResponse])
async def get_default_server(request: Request):
    """Get user's default execution server"""
    try:
        user_email = await get_user_email(request)

        from keycloak_integration import get_user_by_email
        user = await get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user.get("id")

        conn = await get_db_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, name, server_type, connection_config, workspace_path,
                       is_default, is_active, last_tested_at, test_status,
                       created_at, updated_at
                FROM user_execution_servers
                WHERE user_id = $1 AND is_default = true AND is_active = true
            """, user_id)

            if not row:
                return None

            config = json.loads(row['connection_config']) if isinstance(row['connection_config'], str) else row['connection_config']
            masked_config = mask_sensitive_config(config, row['server_type'])

            return ExecutionServerResponse(
                id=str(row['id']),
                name=row['name'],
                server_type=row['server_type'],
                connection_config=masked_config,
                workspace_path=row['workspace_path'],
                is_default=row['is_default'],
                is_active=row['is_active'],
                last_tested_at=row['last_tested_at'].isoformat() if row['last_tested_at'] else None,
                test_status=row['test_status'],
                created_at=row['created_at'].isoformat(),
                updated_at=row['updated_at'].isoformat()
            )
        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default server: {e}")
        raise HTTPException(status_code=500, detail="Failed to get default execution server")
