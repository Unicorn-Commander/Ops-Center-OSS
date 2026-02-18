"""
Forgejo API Client for Ops-Center Integration

Provides async HTTP client for Forgejo Git server API.
Supports both user-token and admin-token authentication.

Author: Ops-Center AI
Created: November 8, 2025
"""

import httpx
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ForgejoClient:
    """Async client for Forgejo Git server API"""

    def __init__(
        self,
        base_url: str = "https://git.unicorncommander.ai",
        admin_token: Optional[str] = "4d79a6bef5c793c89b13400115188ea935fc31b5",
        timeout: int = 10
    ):
        """
        Initialize Forgejo client

        Args:
            base_url: Forgejo instance URL
            admin_token: Admin API token for elevated operations
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.admin_token = admin_token
        self.timeout = timeout

    def _get_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        token = user_token or self.admin_token
        return {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Forgejo instance health

        Returns:
            dict: Health status with online/offline and version info
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try to fetch version info (public endpoint)
                response = await client.get(f"{self.base_url}/api/v1/version")

                if response.status_code == 200:
                    version_data = response.json()
                    return {
                        "online": True,
                        "version": version_data.get("version", "unknown"),
                        "status": "healthy"
                    }
                else:
                    return {
                        "online": False,
                        "status": "unreachable",
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            logger.error(f"Forgejo health check failed: {e}")
            return {
                "online": False,
                "status": "error",
                "error": str(e)
            }

    async def get_user_repos(self, user_token: str) -> List[Dict[str, Any]]:
        """
        Get repositories for authenticated user

        Args:
            user_token: User's Forgejo access token

        Returns:
            list: User's repositories
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/user/repos",
                    headers=self._get_headers(user_token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch user repos: {e}")
            return []

    async def get_all_orgs(self) -> List[Dict[str, Any]]:
        """
        Get all organizations (admin only)

        Returns:
            list: All organizations in Forgejo
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/orgs",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch organizations: {e}")
            return []

    async def get_org_repos(self, org_name: str) -> List[Dict[str, Any]]:
        """
        Get repositories for specific organization

        Args:
            org_name: Organization name

        Returns:
            list: Organization's repositories
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/orgs/{org_name}/repos",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch org repos for {org_name}: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get Forgejo instance statistics (admin only)

        Returns:
            dict: Instance statistics
        """
        try:
            # Get organizations
            orgs = await self.get_all_orgs()

            # Count total repos across all orgs
            total_repos = 0
            for org in orgs:
                org_repos = await self.get_org_repos(org["username"])
                total_repos += len(org_repos)

            return {
                "total_organizations": len(orgs),
                "total_repositories": total_repos,
                "instance_url": self.base_url
            }
        except Exception as e:
            logger.error(f"Failed to fetch Forgejo stats: {e}")
            return {
                "error": str(e)
            }
