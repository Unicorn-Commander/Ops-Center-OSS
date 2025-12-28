"""
Grafana API Integration
Manages Grafana dashboard configuration, data sources, and monitoring

This module provides a comprehensive API for integrating with Grafana monitoring:
- Health checks and connection testing
- Data source management (Prometheus, PostgreSQL, Loki, etc.)
- Dashboard listing and management
- Organization configuration
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import httpx
import logging
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/monitoring/grafana", tags=["Monitoring"])

# Grafana Configuration
# Using taxsquare-grafana hostname on shared 'web' network
# Alternatively, can use http://172.18.0.11:3000 (web network IP)
GRAFANA_URL = "http://taxsquare-grafana:3000"
GRAFANA_TIMEOUT = 30.0

class GrafanaConfig(BaseModel):
    """Grafana connection configuration"""
    url: str = Field(..., description="Grafana instance URL")
    api_key: Optional[str] = Field(None, description="Grafana API key (preferred)")
    username: Optional[str] = Field("admin", description="Admin username (fallback auth)")
    password: Optional[str] = Field(None, description="Admin password (fallback auth)")

class DataSourceConfig(BaseModel):
    """Grafana data source configuration"""
    name: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data source type (prometheus, postgres, loki, etc.)")
    url: str = Field(..., description="Data source URL")
    access: str = Field("proxy", description="Access mode: 'proxy' or 'direct'")
    is_default: bool = Field(False, description="Set as default data source")
    jsonData: Optional[Dict[str, Any]] = Field(None, description="Additional JSON configuration")
    secureJsonData: Optional[Dict[str, Any]] = Field(None, description="Secure credentials")

class DashboardImport(BaseModel):
    """Import Grafana dashboard configuration"""
    dashboard: Dict[str, Any] = Field(..., description="Dashboard JSON model")
    overwrite: bool = Field(False, description="Overwrite existing dashboard")
    folder_id: Optional[int] = Field(None, description="Folder to place dashboard in")

@router.get("/health")
async def check_grafana_health():
    """
    Check if Grafana is accessible and healthy

    Returns:
        - success: Boolean indicating if Grafana is reachable
        - status: healthy/unhealthy
        - version: Grafana version
        - database: Database status
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": "healthy",
                    "version": data.get("version", "unknown"),
                    "database": data.get("database", "unknown"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.utcnow().isoformat()
                }
    except httpx.ConnectError as e:
        logger.error(f"Grafana connection error: {e}")
        return {
            "success": False,
            "status": "unreachable",
            "error": "Cannot connect to Grafana instance. Is it running?",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Grafana health check failed: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/test-connection")
async def test_grafana_connection(config: GrafanaConfig):
    """
    Test Grafana API connection with provided credentials

    Args:
        config: Grafana connection configuration

    Returns:
        - success: Boolean indicating connection success
        - message: Human-readable status message
        - details: Organization details if successful
    """
    try:
        headers = {}
        auth = None

        # Prefer API key authentication
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
            logger.info("Testing Grafana connection with API key")
        elif config.username and config.password:
            auth = (config.username, config.password)
            logger.info(f"Testing Grafana connection with username/password: {config.username}")
        else:
            raise HTTPException(
                status_code=400,
                detail="Either API key or username/password must be provided"
            )

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            # Test connection by fetching organization info
            response = await client.get(
                f"{config.url}/api/org",
                headers=headers,
                auth=auth
            )

            if response.status_code == 200:
                org_data = response.json()
                logger.info(f"Successfully connected to Grafana: {org_data.get('name')}")
                return {
                    "success": True,
                    "message": f"Connected to Grafana (Org: {org_data.get('name', 'unknown')})",
                    "details": {
                        "id": org_data.get("id"),
                        "name": org_data.get("name"),
                        "address": org_data.get("address")
                    }
                }
            elif response.status_code == 401:
                logger.warning("Grafana authentication failed: Invalid credentials")
                return {
                    "success": False,
                    "message": "Authentication failed: Invalid API key or username/password",
                    "error": response.text
                }
            elif response.status_code == 403:
                logger.warning("Grafana access forbidden: Insufficient permissions")
                return {
                    "success": False,
                    "message": "Access forbidden: User does not have required permissions",
                    "error": response.text
                }
            else:
                logger.error(f"Grafana connection failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "message": f"Grafana connection failed: HTTP {response.status_code}",
                    "error": response.text
                }
    except httpx.ConnectError as e:
        logger.error(f"Cannot reach Grafana at {config.url}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Grafana at {config.url}. Is the service running?"
        )
    except Exception as e:
        logger.error(f"Grafana connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasources")
async def list_data_sources(api_key: Optional[str] = None):
    """
    List configured Grafana data sources

    Args:
        api_key: Grafana API key (optional, uses default URL if not provided)

    Returns:
        - success: Boolean
        - datasources: List of data source configurations
    """
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.get(
                f"{GRAFANA_URL}/api/datasources",
                headers=headers
            )

            if response.status_code == 200:
                datasources = response.json()
                logger.info(f"Retrieved {len(datasources)} data sources from Grafana")
                return {
                    "success": True,
                    "count": len(datasources),
                    "datasources": datasources
                }
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch data sources: {response.text}"
                )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Grafana: {e}")
        raise HTTPException(
            status_code=503,
            detail="Grafana service is not reachable"
        )
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datasources")
async def create_data_source(config: DataSourceConfig, api_key: str):
    """
    Create new Grafana data source

    Args:
        config: Data source configuration
        api_key: Grafana API key (required for write operations)

    Returns:
        - success: Boolean
        - message: Status message
        - data: Created data source details
    """
    try:
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="API key is required for creating data sources"
            )

        headers = {"Authorization": f"Bearer {api_key}"}
        payload = config.dict(exclude_none=True)

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.post(
                f"{GRAFANA_URL}/api/datasources",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Created data source '{config.name}' (ID: {result.get('id')})")
                return {
                    "success": True,
                    "message": f"Data source '{config.name}' created successfully",
                    "data": result
                }
            elif response.status_code == 409:
                raise HTTPException(
                    status_code=409,
                    detail=f"Data source '{config.name}' already exists"
                )
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create data source: {response.text}"
                )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Grafana: {e}")
        raise HTTPException(
            status_code=503,
            detail="Grafana service is not reachable"
        )
    except Exception as e:
        logger.error(f"Failed to create data source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/datasources/{datasource_id}")
async def delete_data_source(datasource_id: int, api_key: str):
    """
    Delete Grafana data source by ID

    Args:
        datasource_id: Data source ID to delete
        api_key: Grafana API key (required)

    Returns:
        - success: Boolean
        - message: Status message
    """
    try:
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="API key is required for deleting data sources"
            )

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.delete(
                f"{GRAFANA_URL}/api/datasources/{datasource_id}",
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Deleted data source ID {datasource_id}")
                return {
                    "success": True,
                    "message": f"Data source {datasource_id} deleted successfully"
                }
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Data source {datasource_id} not found"
                )
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to delete data source: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to delete data source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards")
async def list_dashboards(api_key: Optional[str] = None):
    """
    List Grafana dashboards

    Args:
        api_key: Grafana API key (optional)

    Returns:
        - success: Boolean
        - dashboards: List of dashboard metadata
    """
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.get(
                f"{GRAFANA_URL}/api/search?type=dash-db",
                headers=headers
            )

            if response.status_code == 200:
                dashboards = response.json()
                logger.info(f"Retrieved {len(dashboards)} dashboards from Grafana")
                return {
                    "success": True,
                    "count": len(dashboards),
                    "dashboards": dashboards
                }
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch dashboards: {response.text}"
                )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Grafana: {e}")
        raise HTTPException(
            status_code=503,
            detail="Grafana service is not reachable"
        )
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/{uid}")
async def get_dashboard(uid: str, api_key: Optional[str] = None):
    """
    Get dashboard by UID

    Args:
        uid: Dashboard unique identifier
        api_key: Grafana API key (optional)

    Returns:
        - success: Boolean
        - dashboard: Dashboard JSON model
    """
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.get(
                f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Retrieved dashboard: {uid}")
                return {
                    "success": True,
                    "dashboard": response.json()
                }
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dashboard {uid} not found"
                )
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch dashboard: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboards")
async def import_dashboard(config: DashboardImport, api_key: str):
    """
    Import/create Grafana dashboard

    Args:
        config: Dashboard import configuration
        api_key: Grafana API key (required)

    Returns:
        - success: Boolean
        - message: Status message
        - dashboard: Created dashboard details
    """
    try:
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="API key is required for importing dashboards"
            )

        headers = {"Authorization": f"Bearer {api_key}"}
        payload = config.dict(exclude_none=True)

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.post(
                f"{GRAFANA_URL}/api/dashboards/db",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Imported dashboard: {result.get('uid')}")
                return {
                    "success": True,
                    "message": "Dashboard imported successfully",
                    "dashboard": result
                }
            elif response.status_code == 412:
                raise HTTPException(
                    status_code=412,
                    detail="Dashboard already exists. Set overwrite=true to replace it."
                )
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to import dashboard: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to import dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/folders")
async def list_folders(api_key: Optional[str] = None):
    """
    List Grafana folders

    Args:
        api_key: Grafana API key (optional)

    Returns:
        - success: Boolean
        - folders: List of folder metadata
    """
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.get(
                f"{GRAFANA_URL}/api/folders",
                headers=headers
            )

            if response.status_code == 200:
                folders = response.json()
                logger.info(f"Retrieved {len(folders)} folders from Grafana")
                return {
                    "success": True,
                    "count": len(folders),
                    "folders": folders
                }
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch folders: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to list folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/{uid}/embed-url")
async def get_dashboard_embed_url(
    uid: str,
    theme: str = "dark",
    refresh: Optional[str] = None,
    from_time: str = "now-6h",
    to_time: str = "now",
    kiosk: str = "tv"
):
    """
    Generate embeddable URL for Grafana dashboard

    Args:
        uid: Dashboard unique identifier
        theme: Dashboard theme ('light' or 'dark')
        refresh: Auto-refresh interval (e.g., '30s', '1m', '5m')
        from_time: Start time for time range (e.g., 'now-6h', 'now-24h')
        to_time: End time for time range (e.g., 'now')
        kiosk: Kiosk mode ('tv' for clean view, 'full' for fullscreen)

    Returns:
        - success: Boolean
        - embed_url: Full embeddable URL
        - external_url: Public URL (using port 3102)
    """
    try:
        # Build query parameters
        params = {
            "theme": theme,
            "kiosk": kiosk,
            "from": from_time,
            "to": to_time
        }

        if refresh:
            params["refresh"] = refresh

        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        # Internal URL (for backend-to-backend)
        internal_url = f"{GRAFANA_URL}/d/{uid}?{query_string}"

        # External URL (for browser access via port 3102)
        external_url = f"http://localhost:3102/d/{uid}?{query_string}"

        logger.info(f"Generated embed URL for dashboard {uid}")

        return {
            "success": True,
            "embed_url": internal_url,
            "external_url": external_url,
            "uid": uid,
            "theme": theme,
            "refresh": refresh,
            "time_range": {
                "from": from_time,
                "to": to_time
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate embed URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_grafana_metrics(
    query: Dict[str, Any],
    api_key: Optional[str] = None
):
    """
    Query Grafana data source for metrics

    Args:
        query: Query configuration with datasource, query, and time range
        api_key: Grafana API key (optional)

    Request body example:
    {
        "datasource": "prometheus",
        "query": "cpu_usage",
        "from": "now-5m",
        "to": "now",
        "interval": "15s"
    }

    Returns:
        - success: Boolean
        - data: Query results
        - metadata: Query metadata
    """
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Extract query parameters
        datasource = query.get("datasource", "prometheus")
        query_str = query.get("query", "")
        from_time = query.get("from", "now-5m")
        to_time = query.get("to", "now")
        interval = query.get("interval", "15s")

        if not query_str:
            raise HTTPException(
                status_code=400,
                detail="Query string is required"
            )

        # Build Grafana query API request
        payload = {
            "queries": [{
                "refId": "A",
                "datasource": {"type": datasource},
                "expr": query_str,
                "interval": interval,
                "format": "time_series"
            }],
            "from": from_time,
            "to": to_time
        }

        async with httpx.AsyncClient(timeout=GRAFANA_TIMEOUT) as client:
            response = await client.post(
                f"{GRAFANA_URL}/api/ds/query",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Query executed successfully: {query_str[:50]}")
                return {
                    "success": True,
                    "data": data.get("results", {}),
                    "metadata": {
                        "datasource": datasource,
                        "query": query_str,
                        "time_range": {
                            "from": from_time,
                            "to": to_time
                        }
                    }
                }
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing API key"
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Query failed: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("Grafana API module initialized")
