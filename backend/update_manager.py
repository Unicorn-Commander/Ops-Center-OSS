"""
GitHub Update Manager
Handles checking for and applying updates from the UC-1 Pro GitHub repository
"""

import os
import json
import subprocess
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiofiles
import httpx
import logging

logger = logging.getLogger(__name__)

class GitHubUpdateManager:
    def __init__(self):
        self.project_root = Path("/home/ucadmin/UC-1-Pro")
        self.update_info_path = self.project_root / "update_info.json"
        self.github_repo = "magicunicorntech/UC-1-Pro"  # Placeholder - update with actual repo
        self.github_api_base = "https://api.github.com"
        self.current_branch = "main"
        self.update_status = {
            "checking": False,
            "updating": False,
            "last_check": None,
            "last_update": None,
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "update_notes": []
        }
    
    async def get_current_version(self) -> str:
        """Get current version from git or version file"""
        try:
            # Try to get version from git
            if (self.project_root / ".git").exists():
                result = await asyncio.create_subprocess_exec(
                    "git", "describe", "--tags", "--exact-match", "HEAD",
                    cwd=self.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    return stdout.decode().strip()
                
                # If no exact tag, get commit hash
                result = await asyncio.create_subprocess_exec(
                    "git", "rev-parse", "--short", "HEAD",
                    cwd=self.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    return f"dev-{stdout.decode().strip()}"
            
            # Fallback to version file
            version_file = self.project_root / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            
            return "unknown"
        
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "unknown"
    
    async def get_latest_release(self) -> Dict[str, Any]:
        """Get latest release information from GitHub"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.github_api_base}/repos/{self.github_repo}/releases/latest",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # If no releases, get latest commit
                    response = await client.get(
                        f"{self.github_api_base}/repos/{self.github_repo}/commits/{self.current_branch}",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        commit_data = response.json()
                        return {
                            "tag_name": f"dev-{commit_data['sha'][:7]}",
                            "name": f"Latest Development ({commit_data['sha'][:7]})",
                            "body": commit_data['commit']['message'],
                            "published_at": commit_data['commit']['committer']['date'],
                            "html_url": commit_data['html_url'],
                            "prerelease": True
                        }
        
        except Exception as e:
            logger.error(f"Error fetching latest release: {e}")
            return {}
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """Check if updates are available"""
        try:
            self.update_status["checking"] = True
            self.update_status["last_check"] = datetime.now().isoformat()
            
            current_version = await self.get_current_version()
            latest_release = await self.get_latest_release()
            
            self.update_status["current_version"] = current_version
            
            if latest_release:
                latest_version = latest_release.get("tag_name", "unknown")
                self.update_status["latest_version"] = latest_version
                self.update_status["update_available"] = latest_version != current_version
                
                # Parse release notes
                body = latest_release.get("body", "")
                self.update_status["update_notes"] = self._parse_release_notes(body)
                
                # Save update info
                await self._save_update_info()
                
                return {
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_available": self.update_status["update_available"],
                    "release_notes": self.update_status["update_notes"],
                    "release_url": latest_release.get("html_url"),
                    "published_at": latest_release.get("published_at"),
                    "prerelease": latest_release.get("prerelease", False)
                }
            else:
                return {
                    "current_version": current_version,
                    "latest_version": "unknown",
                    "update_available": False,
                    "error": "Could not fetch update information"
                }
        
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {
                "current_version": await self.get_current_version(),
                "latest_version": "unknown",
                "update_available": False,
                "error": str(e)
            }
        finally:
            self.update_status["checking"] = False
    
    def _parse_release_notes(self, body: str) -> List[str]:
        """Parse release notes into structured format"""
        if not body:
            return []
        
        lines = body.split('\n')
        notes = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Clean up markdown formatting
                line = line.replace('*', '').replace('-', '').strip()
                if line:
                    notes.append(line)
        
        return notes[:10]  # Limit to 10 items
    
    async def apply_update(self, backup_first: bool = True) -> Dict[str, Any]:
        """Apply the available update"""
        try:
            self.update_status["updating"] = True
            
            # Check if git repo exists
            if not (self.project_root / ".git").exists():
                return {
                    "success": False,
                    "error": "Not a git repository - updates not supported"
                }
            
            # Create backup if requested
            if backup_first:
                await self._create_backup()
            
            # Stash any local changes
            await self._run_git_command(["git", "stash", "push", "-m", "Pre-update stash"])
            
            # Fetch latest changes
            result = await self._run_git_command(["git", "fetch", "origin", self.current_branch])
            if not result["success"]:
                return result
            
            # Get update info
            local_commit = await self._run_git_command(["git", "rev-parse", "HEAD"])
            remote_commit = await self._run_git_command(["git", "rev-parse", f"origin/{self.current_branch}"])
            
            if local_commit["stdout"] == remote_commit["stdout"]:
                return {
                    "success": True,
                    "message": "Already up to date",
                    "no_update_needed": True
                }
            
            # Apply update
            result = await self._run_git_command(["git", "reset", "--hard", f"origin/{self.current_branch}"])
            if not result["success"]:
                return result
            
            # Run any update scripts
            await self._run_update_scripts()
            
            # Update status
            self.update_status["last_update"] = datetime.now().isoformat()
            self.update_status["current_version"] = await self.get_current_version()
            self.update_status["update_available"] = False
            
            await self._save_update_info()
            
            return {
                "success": True,
                "message": "Update applied successfully",
                "new_version": self.update_status["current_version"],
                "restart_required": True
            }
        
        except Exception as e:
            logger.error(f"Error applying update: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self.update_status["updating"] = False
    
    async def _run_git_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Run a git command and return result"""
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return {
                "success": result.returncode == 0,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip(),
                "returncode": result.returncode
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_backup(self):
        """Create a backup before updating"""
        try:
            backup_dir = self.project_root / "backups" / f"pre-update-{int(time.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy important files
            important_files = [
                ".env",
                "docker-compose.yml",
                "volumes",
                "services/ops-center/data"
            ]
            
            for item in important_files:
                src = self.project_root / item
                if src.exists():
                    if src.is_file():
                        await asyncio.create_subprocess_exec(
                            "cp", str(src), str(backup_dir / src.name)
                        )
                    else:
                        await asyncio.create_subprocess_exec(
                            "cp", "-r", str(src), str(backup_dir / src.name)
                        )
            
            logger.info(f"Backup created at {backup_dir}")
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    async def _run_update_scripts(self):
        """Run any update scripts after applying changes"""
        try:
            update_script = self.project_root / "scripts" / "post-update.sh"
            if update_script.exists():
                await asyncio.create_subprocess_exec(
                    "bash", str(update_script),
                    cwd=self.project_root
                )
        
        except Exception as e:
            logger.warning(f"Error running update scripts: {e}")
    
    async def _save_update_info(self):
        """Save update information to disk"""
        try:
            async with aiofiles.open(self.update_info_path, 'w') as f:
                await f.write(json.dumps(self.update_status, indent=2))
        except Exception as e:
            logger.error(f"Error saving update info: {e}")
    
    async def _load_update_info(self):
        """Load update information from disk"""
        try:
            if self.update_info_path.exists():
                async with aiofiles.open(self.update_info_path, 'r') as f:
                    content = await f.read()
                    saved_status = json.loads(content)
                    self.update_status.update(saved_status)
        except Exception as e:
            logger.error(f"Error loading update info: {e}")
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status"""
        return self.update_status.copy()
    
    async def get_changelog(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent changelog entries"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.github_api_base}/repos/{self.github_repo}/commits",
                    params={"per_page": limit, "sha": self.current_branch},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    commits = response.json()
                    changelog = []
                    
                    for commit in commits:
                        changelog.append({
                            "sha": commit["sha"][:7],
                            "message": commit["commit"]["message"].split('\n')[0],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"],
                            "url": commit["html_url"]
                        })
                    
                    return changelog
        
        except Exception as e:
            logger.error(f"Error fetching changelog: {e}")
        
        return []

# Global instance
github_update_manager = GitHubUpdateManager()