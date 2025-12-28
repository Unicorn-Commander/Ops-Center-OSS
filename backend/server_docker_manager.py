"""
Docker container discovery and management for UC-1 Pro Admin Dashboard
Handles both core stack and extension containers
"""

import os
import yaml
import docker
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

class DockerServiceManager:
    def __init__(self):
        self.project_root = Path("/home/ucadmin/UC-1-Pro")
        self.docker_client = None
        self.core_compose_file = self.project_root / "docker-compose.yml"
        self.extensions_dir = self.project_root / "extensions"
        
        try:
            # Try different connection methods
            try:
                self.docker_client = docker.from_env()
            except:
                # Try with explicit socket
                self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            # Try to use docker CLI as fallback
            self.docker_client = None
    
    def discover_all_services(self) -> Dict[str, Any]:
        """Discover all services from core stack and extensions"""
        services = {
            "core": self._discover_core_services(),
            "extensions": self._discover_extension_services()
        }
        return services
    
    def _discover_core_services(self) -> List[Dict[str, Any]]:
        """Discover services from main docker-compose.yml"""
        services = []
        
        try:
            if self.core_compose_file.exists():
                with open(self.core_compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)
                
                if 'services' in compose_data:
                    for service_name, service_config in compose_data['services'].items():
                        container_name = service_config.get('container_name', f'unicorn-{service_name}')
                        
                        # Extract service info
                        service_info = {
                            "name": service_name,
                            "container_name": container_name,
                            "display_name": self._get_display_name(service_name),
                            "category": "core",
                            "source": "docker-compose.yml",
                            "image": service_config.get('image', 'unknown'),
                            "ports": self._extract_ports(service_config.get('ports', [])),
                            "environment": service_config.get('environment', {}),
                            "volumes": service_config.get('volumes', []),
                            "depends_on": service_config.get('depends_on', []),
                            "restart": service_config.get('restart', 'no'),
                            "healthcheck": service_config.get('healthcheck', {}),
                            "gpu_enabled": 'runtime' in service_config and service_config['runtime'] == 'nvidia',
                            "status": self._get_container_status(container_name),
                            "stats": self._get_container_stats(container_name)
                        }
                        
                        services.append(service_info)
        
        except Exception as e:
            logger.error(f"Error discovering core services: {e}")
        
        return services
    
    def _discover_extension_services(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover services from extension docker-compose files"""
        extensions = {}
        
        try:
            if self.extensions_dir.exists():
                for ext_dir in self.extensions_dir.iterdir():
                    if ext_dir.is_dir():
                        compose_file = ext_dir / "docker-compose.yml"
                        
                        if compose_file.exists():
                            extension_name = ext_dir.name
                            services = []
                            
                            with open(compose_file, 'r') as f:
                                compose_data = yaml.safe_load(f)
                            
                            if 'services' in compose_data:
                                for service_name, service_config in compose_data['services'].items():
                                    container_name = service_config.get('container_name', f'{extension_name}-{service_name}')
                                    
                                    service_info = {
                                        "name": service_name,
                                        "container_name": container_name,
                                        "display_name": self._get_display_name(service_name),
                                        "category": "extension",
                                        "extension": extension_name,
                                        "source": f"extensions/{extension_name}/docker-compose.yml",
                                        "image": service_config.get('image', 'unknown'),
                                        "ports": self._extract_ports(service_config.get('ports', [])),
                                        "environment": service_config.get('environment', {}),
                                        "volumes": service_config.get('volumes', []),
                                        "depends_on": service_config.get('depends_on', []),
                                        "restart": service_config.get('restart', 'no'),
                                        "healthcheck": service_config.get('healthcheck', {}),
                                        "gpu_enabled": 'runtime' in service_config and service_config['runtime'] == 'nvidia',
                                        "status": self._get_container_status(container_name),
                                        "stats": self._get_container_stats(container_name)
                                    }
                                    
                                    services.append(service_info)
                            
                            if services:
                                extensions[extension_name] = services
        
        except Exception as e:
            logger.error(f"Error discovering extension services: {e}")
        
        return extensions
    
    def _get_display_name(self, service_name: str) -> str:
        """Generate a user-friendly display name"""
        # Common service name mappings
        display_names = {
            "vllm": "vLLM API",
            "open-webui": "Open WebUI",
            "whisperx": "WhisperX STT",
            "kokoro": "Kokoro TTS",
            "embeddings": "Embeddings API",
            "reranker": "Reranker API",
            "searxng": "SearXNG Search",
            "tika-ocr": "Tika OCR",
            "qdrant": "Qdrant Vector DB",
            "postgresql": "PostgreSQL",
            "redis": "Redis Cache",
            "prometheus": "Prometheus",
            "gpu-exporter": "GPU Exporter",
            "admin-dashboard": "Admin Dashboard",
            "comfyui": "ComfyUI",
            "n8n": "n8n Automation",
            "ollama": "Ollama",
            "portainer": "Portainer",
            "traefik": "Traefik Proxy",
            "grafana": "Grafana"
        }
        
        return display_names.get(service_name, service_name.replace('-', ' ').replace('_', ' ').title())
    
    def _extract_ports(self, ports_config: List) -> List[Dict[str, Any]]:
        """Extract port mappings from docker-compose format"""
        ports = []
        
        for port in ports_config:
            if isinstance(port, str):
                # Format: "8080:80" or "8080:80/tcp"
                parts = port.split(':')
                if len(parts) >= 2:
                    host_port = parts[0]
                    container_port = parts[1].split('/')[0]
                    protocol = parts[1].split('/')[1] if '/' in parts[1] else 'tcp'
                    
                    ports.append({
                        "host": int(host_port) if host_port.isdigit() else host_port,
                        "container": int(container_port) if container_port.isdigit() else container_port,
                        "protocol": protocol
                    })
            elif isinstance(port, dict):
                # Format: {target: 80, published: 8080, protocol: tcp}
                ports.append({
                    "host": port.get('published', port.get('target')),
                    "container": port.get('target'),
                    "protocol": port.get('protocol', 'tcp')
                })
        
        return ports
    
    def _get_container_status(self, container_name: str) -> str:
        """Get the current status of a container"""
        if self.docker_client:
            try:
                container = self.docker_client.containers.get(container_name)
                status = container.status
                
                # Map Docker status to our status
                status_map = {
                    "running": "healthy",
                    "restarting": "starting",
                    "paused": "paused",
                    "exited": "stopped",
                    "dead": "error",
                    "created": "stopped"
                }
                
                return status_map.get(status, "unknown")
            
            except docker.errors.NotFound:
                return "not_created"
            except Exception as e:
                logger.error(f"Error getting status for {container_name}: {e}")
                return "unknown"
        else:
            # Fallback to docker CLI
            try:
                result = subprocess.run(
                    ["docker", "inspect", container_name, "--format", "{{.State.Status}}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    status = result.stdout.strip()
                    status_map = {
                        "running": "healthy",
                        "restarting": "starting",
                        "paused": "paused",
                        "exited": "stopped",
                        "dead": "error",
                        "created": "stopped"
                    }
                    return status_map.get(status, "unknown")
                else:
                    return "not_created"
            except Exception as e:
                logger.error(f"Error getting status via CLI for {container_name}: {e}")
                return "unknown"
    
    def _get_container_stats(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Get resource usage stats for a container"""
        if not self.docker_client:
            return None
        
        try:
            container = self.docker_client.containers.get(container_name)
            if container.status != 'running':
                return None
            
            # Get stats (non-streaming)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0.0:
                cpu_percent = (cpu_delta / system_delta) * 100.0 * stats['cpu_stats']['online_cpus']
            
            # Calculate memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
            
            # Get network stats
            network_rx = 0
            network_tx = 0
            if 'networks' in stats:
                for interface in stats['networks'].values():
                    network_rx += interface.get('rx_bytes', 0)
                    network_tx += interface.get('tx_bytes', 0)
            
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "memory_percent": round(memory_percent, 2),
                "network_rx_mb": round(network_rx / (1024 * 1024), 2),
                "network_tx_mb": round(network_tx / (1024 * 1024), 2)
            }
        
        except Exception as e:
            logger.error(f"Error getting stats for {container_name}: {e}")
            return None
    
    def control_service(self, container_name: str, action: str) -> Dict[str, Any]:
        """Control a service (start, stop, restart)"""
        if self.docker_client:
            try:
                container = self.docker_client.containers.get(container_name)
                
                if action == "start":
                    container.start()
                    return {"success": True, "message": f"Started {container_name}"}
                elif action == "stop":
                    container.stop()
                    return {"success": True, "message": f"Stopped {container_name}"}
                elif action == "restart":
                    container.restart()
                    return {"success": True, "message": f"Restarted {container_name}"}
                else:
                    return {"success": False, "error": f"Unknown action: {action}"}
            
            except docker.errors.NotFound:
                # Container doesn't exist, try to create and start it
                if action == "start":
                    return self._create_and_start_service(container_name)
                else:
                    return {"success": False, "error": f"Container {container_name} not found"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Fallback to docker CLI
            try:
                cmd = ["docker", action, container_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return {"success": True, "message": f"{action.capitalize()}ed {container_name}"}
                else:
                    # Container doesn't exist, try to create and start it
                    if action == "start" and "No such container" in result.stderr:
                        return self._create_and_start_service(container_name)
                    else:
                        return {"success": False, "error": result.stderr}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def _create_and_start_service(self, container_name: str) -> Dict[str, Any]:
        """Create and start a service using docker-compose"""
        try:
            # Find which compose file contains this container
            all_services = self.discover_all_services()
            
            # Check core services
            for service in all_services.get('core', []):
                if service['container_name'] == container_name:
                    # Use docker-compose to start the service
                    compose_cmd = f"cd {self.project_root} && docker-compose up -d {service['name']}"
                    result = os.system(compose_cmd)
                    if result == 0:
                        return {"success": True, "message": f"Created and started {container_name}"}
                    else:
                        return {"success": False, "error": f"Failed to start service with docker-compose"}
            
            # Check extension services
            for ext_name, services in all_services.get('extensions', {}).items():
                for service in services:
                    if service['container_name'] == container_name:
                        # Use docker-compose to start the extension service
                        compose_cmd = f"cd {self.project_root}/extensions/{ext_name} && docker-compose up -d {service['name']}"
                        result = os.system(compose_cmd)
                        if result == 0:
                            return {"success": True, "message": f"Created and started {container_name}"}
                        else:
                            return {"success": False, "error": f"Failed to start extension service with docker-compose"}
            
            return {"success": False, "error": f"Service {container_name} not found in any docker-compose file"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_service_logs(self, container_name: str, lines: int = 100) -> List[str]:
        """Get logs from a container"""
        if not self.docker_client:
            return ["Docker client not available"]
        
        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8').split('\n')
            return [log for log in logs if log.strip()]
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")
            return [f"Error getting logs: {str(e)}"]