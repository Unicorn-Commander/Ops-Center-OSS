"""
Umami Analytics Integration
Manages Umami web analytics configuration, tracking scripts, and privacy settings
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import httpx
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/monitoring/umami", tags=["Monitoring"])

# Umami Configuration
UMAMI_URL = "http://umami.your-domain.com:3000"
UMAMI_TIMEOUT = 30.0

# Pre-defined websites to track
DEFAULT_WEBSITES = [
    {
        "name": "Ops Center",
        "domain": "your-domain.com",
        "enabled": False
    },
    {
        "name": "Brigade",
        "domain": "brigade.your-domain.com",
        "enabled": False
    },
    {
        "name": "Center-Deep",
        "domain": "search.your-domain.com",
        "enabled": False
    }
]

class UmamiConfig(BaseModel):
    url: str
    api_key: Optional[str] = None
    tracking_code: str = "xxxxx-xxxxx-xxxxx-xxxxx"
    privacy_mode: str = "strict"  # strict, balanced, permissive
    respect_dnt: bool = True
    session_tracking: bool = True

class Website(BaseModel):
    name: str
    domain: str
    enabled: bool = False

@router.get("/health")
async def check_umami_health():
    """Check if Umami is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{UMAMI_URL}/api/heartbeat")
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "message": "Umami is running"
                }
            # Try root endpoint if heartbeat doesn't exist
            response = await client.get(f"{UMAMI_URL}/")
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "message": "Umami is accessible"
                }
    except Exception as e:
        logger.error(f"Umami health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/test-connection")
async def test_umami_connection(config: UmamiConfig):
    """Test Umami API connection"""
    try:
        headers = {}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        async with httpx.AsyncClient(timeout=UMAMI_TIMEOUT) as client:
            # Try to access /api/websites endpoint
            response = await client.get(
                f"{config.url}/api/websites",
                headers=headers
            )

            if response.status_code == 200:
                websites = response.json()
                return {
                    "success": True,
                    "message": f"Connected to Umami ({len(websites)} websites tracked)",
                    "details": {"website_count": len(websites)}
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Umami connection failed: Invalid API key",
                    "error": "Authentication required"
                }
            else:
                # Try basic connectivity
                response = await client.get(f"{config.url}/")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Connected to Umami (API key not validated)",
                        "note": "Provide API key for full access"
                    }
                return {
                    "success": False,
                    "message": f"Umami connection failed: {response.status_code}",
                    "error": response.text
                }
    except Exception as e:
        logger.error(f"Umami connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/websites")
async def list_websites(api_key: Optional[str] = None):
    """List configured Umami websites"""
    if not api_key:
        return {
            "success": True,
            "websites": DEFAULT_WEBSITES,
            "note": "Returning default websites (no API key provided)"
        }

    try:
        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=UMAMI_TIMEOUT) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites",
                headers=headers
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "websites": response.json()
                }
            else:
                # Return defaults if API fails
                return {
                    "success": True,
                    "websites": DEFAULT_WEBSITES,
                    "note": f"Returning default websites (API returned {response.status_code})"
                }
    except Exception as e:
        logger.error(f"Failed to list websites: {e}")
        return {
            "success": True,
            "websites": DEFAULT_WEBSITES,
            "note": "Returning default websites (error occurred)"
        }

@router.post("/websites")
async def create_website(website: Website, api_key: str):
    """Create new website in Umami"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "name": website.name,
            "domain": website.domain
        }

        async with httpx.AsyncClient(timeout=UMAMI_TIMEOUT) as client:
            response = await client.post(
                f"{UMAMI_URL}/api/websites",
                json=payload,
                headers=headers
            )

            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": f"Website '{website.name}' created",
                    "data": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create website: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to create website: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-script/{website_id}")
async def generate_tracking_script(website_id: str):
    """Generate Umami tracking script"""
    script = f"""<!-- Umami Analytics -->
<script
  async
  defer
  data-website-id="{website_id}"
  src="{UMAMI_URL}/umami.js"
></script>"""

    return {
        "success": True,
        "script": script,
        "instructions": "Add this script to the <head> section of your HTML"
    }

@router.get("/stats")
async def get_website_stats(website_id: str, api_key: str):
    """Get website analytics stats"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=UMAMI_TIMEOUT) as client:
            response = await client.get(
                f"{UMAMI_URL}/api/websites/{website_id}/stats",
                headers=headers
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "stats": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch stats: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("Umami API module initialized with 3 default websites")
