"""Log Manager Module

This module handles log aggregation, streaming, search, and analysis.
"""

import os
import json
import re
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import aiofiles
from pydantic import BaseModel, Field

class LogEntry(BaseModel):
    """Individual log entry model"""
    timestamp: str
    level: str = "INFO"
    source: str
    message: str
    container: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LogFilter(BaseModel):
    """Log filter parameters"""
    sources: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    search: Optional[str] = None
    container: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 1000

class LogExportRequest(BaseModel):
    """Log export request model"""
    format: str = "json"  # json, csv, txt
    filters: LogFilter
    filename: Optional[str] = None

class LogManager:
    """Manages log collection, streaming, and analysis"""
    
    def __init__(self):
        self.base_dir = Path("/home/ucadmin/UC-1-Pro")
        self.log_dirs = {
            "system": Path("/var/log"),
            "docker": Path("/var/lib/docker/containers"),
            "uc1": self.base_dir / "logs",
            "services": self.base_dir / "services"
        }
        
        # Log level patterns
        self.level_patterns = {
            "ERROR": re.compile(r"ERROR|CRITICAL|FATAL", re.IGNORECASE),
            "WARNING": re.compile(r"WARNING|WARN", re.IGNORECASE),
            "INFO": re.compile(r"INFO", re.IGNORECASE),
            "DEBUG": re.compile(r"DEBUG", re.IGNORECASE)
        }
        
        # Container name mapping
        self.container_map = {}
        self._update_container_map()
    
    def _update_container_map(self):
        """Update container ID to name mapping"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    try:
                        container = json.loads(line)
                        container_id = container.get("ID", "")
                        container_name = container.get("Names", "")
                        if container_id and container_name:
                            self.container_map[container_id] = container_name
                    except:
                        continue
        except:
            pass
    
    def _parse_log_level(self, message: str) -> str:
        """Extract log level from message"""
        for level, pattern in self.level_patterns.items():
            if pattern.search(message):
                return level
        return "INFO"
    
    def _parse_log_line(self, line: str, source: str) -> Optional[LogEntry]:
        """Parse a log line into a LogEntry"""
        try:
            # Try to parse JSON logs (common in Docker)
            if line.strip().startswith('{'):
                try:
                    data = json.loads(line)
                    return LogEntry(
                        timestamp=data.get("time", datetime.now().isoformat()),
                        level=data.get("level", self._parse_log_level(data.get("log", ""))),
                        source=source,
                        message=data.get("log", data.get("msg", str(data))),
                        container=data.get("container", None),
                        metadata=data
                    )
                except:
                    pass
            
            # Parse standard log format
            # Try to extract timestamp
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                message = line[len(timestamp):].strip()
            else:
                timestamp = datetime.now().isoformat()
                message = line.strip()
            
            return LogEntry(
                timestamp=timestamp,
                level=self._parse_log_level(message),
                source=source,
                message=message
            )
            
        except Exception as e:
            print(f"Error parsing log line: {e}")
            return None
    
    async def get_log_sources(self) -> List[Dict[str, Any]]:
        """Get available log sources"""
        sources = []
        
        # System logs
        if self.log_dirs["system"].exists():
            for log_file in self.log_dirs["system"].glob("*.log"):
                sources.append({
                    "id": f"system:{log_file.name}",
                    "name": log_file.name,
                    "type": "system",
                    "path": str(log_file),
                    "size": log_file.stat().st_size if log_file.exists() else 0
                })
        
        # Docker container logs
        self._update_container_map()
        for container_id, container_name in self.container_map.items():
            sources.append({
                "id": f"docker:{container_name}",
                "name": container_name,
                "type": "docker",
                "container_id": container_id
            })
        
        # UC-1 Pro service logs
        if self.log_dirs["services"].exists():
            for service_dir in self.log_dirs["services"].iterdir():
                if service_dir.is_dir():
                    for log_file in service_dir.glob("*.log"):
                        sources.append({
                            "id": f"uc1:{service_dir.name}:{log_file.name}",
                            "name": f"{service_dir.name}/{log_file.name}",
                            "type": "uc1",
                            "path": str(log_file),
                            "size": log_file.stat().st_size if log_file.exists() else 0
                        })
        
        return sources
    
    async def stream_logs(self, source_id: str, filters: Optional[LogFilter] = None) -> AsyncGenerator[str, None]:
        """Stream logs from a specific source"""
        source_type, *source_parts = source_id.split(':')
        
        if source_type == "docker":
            # Stream Docker container logs
            container_name = ':'.join(source_parts)
            cmd = ["docker", "logs", "-f", "--tail", "100", container_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            async for line in process.stdout:
                try:
                    log_line = line.decode('utf-8').strip()
                    if log_line:
                        entry = self._parse_log_line(log_line, source_id)
                        if entry and self._matches_filters(entry, filters):
                            yield json.dumps(entry.dict()) + '\n'
                except:
                    continue
                    
        elif source_type in ["system", "uc1"]:
            # Stream file-based logs
            if source_type == "system":
                log_path = self.log_dirs["system"] / source_parts[0]
            else:
                service_name = source_parts[0]
                log_file = source_parts[1]
                log_path = self.log_dirs["services"] / service_name / log_file
            
            if log_path.exists():
                # Use tail -f for real-time streaming
                cmd = ["tail", "-f", "-n", "100", str(log_path)]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                
                async for line in process.stdout:
                    try:
                        log_line = line.decode('utf-8').strip()
                        if log_line:
                            entry = self._parse_log_line(log_line, source_id)
                            if entry and self._matches_filters(entry, filters):
                                yield json.dumps(entry.dict()) + '\n'
                    except:
                        continue
    
    def _matches_filters(self, entry: LogEntry, filters: Optional[LogFilter]) -> bool:
        """Check if log entry matches filters"""
        if not filters:
            return True
        
        # Check level filter
        if filters.levels and entry.level not in filters.levels:
            return False
        
        # Check search filter
        if filters.search:
            search_lower = filters.search.lower()
            if search_lower not in entry.message.lower():
                return False
        
        # Check time filters
        if filters.start_time or filters.end_time:
            try:
                entry_time = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                if filters.start_time and entry_time < filters.start_time:
                    return False
                if filters.end_time and entry_time > filters.end_time:
                    return False
            except:
                pass
        
        return True
    
    async def search_logs(self, filters: LogFilter) -> List[LogEntry]:
        """Search logs based on filters"""
        results = []
        sources = await self.get_log_sources()
        
        # Filter sources if specified
        if filters.sources:
            sources = [s for s in sources if s["id"] in filters.sources]
        
        for source in sources:
            source_id = source["id"]
            source_type = source["type"]
            
            if source_type == "docker":
                # Search Docker logs
                container_name = source["name"]
                cmd = ["docker", "logs", "--tail", str(filters.limit), container_name]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            entry = self._parse_log_line(line, source_id)
                            if entry and self._matches_filters(entry, filters):
                                results.append(entry)
                                if len(results) >= filters.limit:
                                    return results
                except:
                    continue
                    
            elif source_type in ["system", "uc1"] and "path" in source:
                # Search file-based logs
                log_path = Path(source["path"])
                if log_path.exists():
                    try:
                        # Read last N lines
                        cmd = ["tail", "-n", str(filters.limit * 2), str(log_path)]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            for line in result.stdout.splitlines():
                                entry = self._parse_log_line(line, source_id)
                                if entry and self._matches_filters(entry, filters):
                                    results.append(entry)
                                    if len(results) >= filters.limit:
                                        return results
                    except:
                        continue
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:filters.limit]
    
    async def export_logs(self, request: LogExportRequest) -> Dict[str, Any]:
        """Export logs to file"""
        try:
            # Search logs based on filters
            logs = await self.search_logs(request.filters)
            
            # Generate filename if not provided
            if not request.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                request.filename = f"logs_export_{timestamp}.{request.format}"
            
            export_path = self.base_dir / "exports" / request.filename
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if request.format == "json":
                with open(export_path, 'w') as f:
                    json.dump([log.dict() for log in logs], f, indent=2)
                    
            elif request.format == "csv":
                import csv
                with open(export_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Level", "Source", "Message"])
                    for log in logs:
                        writer.writerow([log.timestamp, log.level, log.source, log.message])
                        
            elif request.format == "txt":
                with open(export_path, 'w') as f:
                    for log in logs:
                        f.write(f"{log.timestamp} [{log.level}] {log.source}: {log.message}\n")
            
            return {
                "success": True,
                "filename": request.filename,
                "path": str(export_path),
                "count": len(logs),
                "size": export_path.stat().st_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics"""
        stats = {
            "total_sources": 0,
            "total_size": 0,
            "levels": {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0},
            "sources_by_type": {"system": 0, "docker": 0, "uc1": 0}
        }
        
        sources = await self.get_log_sources()
        stats["total_sources"] = len(sources)
        
        for source in sources:
            stats["sources_by_type"][source["type"]] += 1
            if "size" in source:
                stats["total_size"] += source["size"]
        
        # Sample recent logs for level statistics
        recent_logs = await self.search_logs(LogFilter(limit=1000))
        for log in recent_logs:
            if log.level in stats["levels"]:
                stats["levels"][log.level] += 1
        
        return stats

# Create singleton instance
log_manager = LogManager()