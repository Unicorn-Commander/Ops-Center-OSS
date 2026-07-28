"""
Simple Docker Container Manager
Detects running containers for the UC-1 Pro stack
"""
import docker
import subprocess
import json
from typing import Dict, List, Any, Optional

class SimpleDockerManager:
    def __init__(self):
        try:
            # Try Unix socket first (most common)
            self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            # Test the connection
            self.docker_client.ping()
        except Exception as e:
            print(f"Warning: Docker client initialization failed: {e}")
            # Set to None - we'll handle this gracefully in methods
            self.docker_client = None
    
    def get_all_containers(self) -> List[Dict[str, Any]]:
        """Get all containers with basic info"""
        containers = []
        
        print(f"DEBUG: Docker client available: {self.docker_client is not None}")
        
        try:
            if self.docker_client:
                print("DEBUG: Attempting to use Docker API")
                # Use Docker API
                for container in self.docker_client.containers.list(all=True):
                    containers.append({
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "created": container.attrs['Created'],
                        "ports": self._get_container_ports(container),
                        "stats": self._get_container_stats(container) if container.status == 'running' else None
                    })
                print(f"DEBUG: Found {len(containers)} containers via API")
            else:
                print("DEBUG: Using CLI fallback")
                # Fallback to CLI
                containers = self._get_containers_via_cli()
                
        except Exception as e:
            print(f"Error getting containers via API: {e}")
            print("DEBUG: Using CLI fallback after API failure")
            # Final fallback
            containers = self._get_containers_via_cli()
        
        print(f"DEBUG: Total containers found: {len(containers)}")
        return containers
    
    def get_uc1_services(self) -> List[Dict[str, Any]]:
        """Get containers that are part of UC-1 Pro stack"""
        # Define expected UC-1 Pro services
        expected_services = {
            'vllm': {'patterns': ['unicorn-vllm', 'vllm'], 'display_name': 'vLLM'},
            'open-webui': {'patterns': ['unicorn-open-webui', 'webui', 'open-webui'], 'display_name': 'Open WebUI'},
            'redis': {'patterns': ['unicorn-redis', 'redis'], 'display_name': 'Redis'},
            'postgresql': {'patterns': ['unicorn-postgresql', 'postgres'], 'display_name': 'PostgreSQL'},
            'qdrant': {'patterns': ['unicorn-qdrant', 'qdrant'], 'display_name': 'Qdrant'},
            'whisperx': {'patterns': ['unicorn-whisperx', 'whisper'], 'display_name': 'WhisperX'},
            'kokoro-tts': {'patterns': ['unicorn-kokoro', 'kokoro'], 'display_name': 'Kokoro TTS'},
            'searxng': {'patterns': ['unicorn-searxng', 'searxng'], 'display_name': 'Center-Deep'},
            'embeddings': {'patterns': ['unicorn-embeddings', 'embedding'], 'display_name': 'Embeddings'},
            'reranker': {'patterns': ['unicorn-reranker', 'rerank'], 'display_name': 'Reranker'},
            'tika': {'patterns': ['unicorn-tika', 'tika'], 'display_name': 'Apache Tika'},
            'ops-center': {'patterns': ['unicorn-ops-center', 'ops-center'], 'display_name': 'Operations Center'},
            'gpu-metrics': {'patterns': ['unicorn-gpu-exporter', 'gpu-exporter', 'gpu-metrics'], 'display_name': 'GPU Metrics'}
        }
        
        all_containers = self.get_all_containers()
        uc1_services = []
        
        # Check each expected service
        for service_key, service_config in expected_services.items():
            matching_container = None
            
            # Look for matching container
            for container in all_containers:
                container_name = container['name'].lower()
                for pattern in service_config['patterns']:
                    # Exact match or pattern match
                    if container_name == pattern.lower() or pattern.lower() in container_name:
                        matching_container = container
                        break
                if matching_container:
                    break
            
            if matching_container:
                # Found running container
                service_info = {
                    "name": service_key,
                    "container_name": matching_container['name'],
                    "status": self._normalize_status(matching_container['status']),
                    "image": matching_container['image'],
                    "ports": matching_container['ports'],
                    "stats": matching_container['stats'],
                    "created": matching_container.get('created')
                }
            else:
                # Service not found - mark as stopped
                service_info = {
                    "name": service_key,
                    "container_name": f"unicorn-{service_key}",
                    "status": "stopped",
                    "image": "unknown",
                    "ports": [],
                    "stats": None,
                    "created": None
                }
            
            uc1_services.append(service_info)
        
        return uc1_services
    
    def _normalize_service_name(self, container_name: str) -> str:
        """Normalize container names to service names"""
        name = container_name.lower()
        
        # Map container names to service names
        name_mappings = {
            'unicorn-vllm': 'vllm',
            'unicorn-webui': 'open-webui',
            'unicorn-redis': 'redis',
            'unicorn-postgresql': 'postgresql',
            'unicorn-postgres': 'postgresql',
            'unicorn-qdrant': 'qdrant',
            'unicorn-whisperx': 'whisperx',
            'unicorn-kokoro': 'kokoro-tts',
            'unicorn-searxng': 'searxng',
            'unicorn-embeddings': 'embeddings',
            'unicorn-reranker': 'reranker',
            'unicorn-tika': 'tika',
            'unicorn-gpu-metrics': 'gpu-metrics',
            'unicorn-ops-center': 'ops-center',
            'unicorn-admin': 'ops-center'
        }
        
        # Check exact matches first
        if name in name_mappings:
            return name_mappings[name]
        
        # Check partial matches
        for container_pattern, service_name in name_mappings.items():
            if container_pattern in name:
                return service_name
        
        # Extract service name from container name
        if name.startswith('unicorn-'):
            return name.replace('unicorn-', '')
        
        return name
    
    def _normalize_status(self, docker_status: str) -> str:
        """Normalize Docker statuses to standard format"""
        status = docker_status.lower()
        
        if status == 'running':
            return 'running'
        elif status in ['exited', 'stopped']:
            return 'stopped'
        elif status in ['starting', 'restarting']:
            return 'starting'
        elif status == 'paused':
            return 'paused'
        else:
            return 'unknown'
    
    def _get_container_ports(self, container) -> List[Dict[str, Any]]:
        """Get container port mappings"""
        ports = []
        try:
            if hasattr(container, 'ports') and container.ports:
                for internal_port, external_bindings in container.ports.items():
                    if external_bindings:
                        for binding in external_bindings:
                            ports.append({
                                "internal": internal_port,
                                "external": binding.get('HostPort'),
                                "host": binding.get('HostIp', '0.0.0.0')
                            })
        except:
            pass
        return ports
    
    def _get_container_stats(self, container) -> Optional[Dict[str, Any]]:
        """Get container resource usage stats"""
        try:
            if container.status != 'running':
                return None
                
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = 0
            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                cpu_stats = stats['cpu_stats']
                precpu_stats = stats['precpu_stats']
                
                cpu_usage_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                system_cpu_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                
                if system_cpu_delta > 0 and cpu_usage_delta > 0:
                    cpu_percent = (cpu_usage_delta / system_cpu_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100
            
            # Get memory usage
            memory_usage = 0
            memory_limit = 0
            if 'memory_stats' in stats:
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
            
            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": round((memory_usage / memory_limit * 100), 1) if memory_limit > 0 else 0
            }
        except Exception as e:
            print(f"Error getting stats for {container.name}: {e}")
            return None
    
    def _get_containers_via_cli(self) -> List[Dict[str, Any]]:
        """Fallback method using docker CLI"""
        containers = []
        try:
            print("DEBUG: Executing Docker CLI command...")
            # Get container list with better formatting
            result = subprocess.run([
                'docker', 'ps', '-a', '--format', 
                '{{.Names}}|{{.Status}}|{{.Image}}|{{.CreatedAt}}|{{.Ports}}'
            ], capture_output=True, text=True, timeout=30)
            
            print(f"DEBUG: Docker CLI return code: {result.returncode}")
            print(f"DEBUG: Docker CLI stdout length: {len(result.stdout)}")
            if result.stderr:
                print(f"DEBUG: Docker CLI stderr: {result.stderr}")
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                print(f"DEBUG: Got {len(lines)} lines from Docker CLI")
                
                for line in lines:
                    if line.strip():
                        parts = line.split('|')
                        print(f"DEBUG: Processing line: {parts[0] if parts else 'empty'} - {len(parts)} parts")
                        if len(parts) >= 4:
                            # Normalize status for Docker CLI format
                            raw_status = parts[1].strip()
                            normalized_status = self._normalize_cli_status(raw_status)
                            
                            containers.append({
                                "name": parts[0].strip(),
                                "status": normalized_status,
                                "image": parts[2].strip(),
                                "created": parts[3].strip(),
                                "ports": self._parse_ports_from_cli(parts[4] if len(parts) > 4 else ""),
                                "stats": self._get_container_stats_via_cli(parts[0].strip()) if normalized_status == 'running' else None
                            })
                            
                            print(f"Found container: {parts[0].strip()} - Status: {normalized_status}")
        except Exception as e:
            print(f"CLI fallback failed: {e}")
        
        return containers
        
    def _normalize_cli_status(self, raw_status: str) -> str:
        """Normalize Docker CLI status output"""
        status = raw_status.lower()
        
        if 'up' in status and 'healthy' in status:
            return 'running'
        elif 'up' in status:
            return 'running'
        elif 'restarting' in status:
            return 'starting'
        elif 'exited' in status:
            return 'stopped'
        elif 'paused' in status:
            return 'paused'
        else:
            return 'unknown'
            
    def _get_container_stats_via_cli(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Get container stats via CLI"""
        try:
            result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format', 
                'table {{.Container}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}',
                container_name
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    parts = lines[1].split('|')
                    if len(parts) >= 4:
                        cpu_str = parts[1].strip().replace('%', '')
                        mem_usage = parts[2].strip()
                        
                        # Parse memory usage (format: "used / limit")
                        mem_mb = 0
                        if '/' in mem_usage:
                            used_str = mem_usage.split('/')[0].strip()
                            if 'GiB' in used_str:
                                mem_mb = float(used_str.replace('GiB', '').strip()) * 1024
                            elif 'MiB' in used_str:
                                mem_mb = float(used_str.replace('MiB', '').strip())
                        
                        return {
                            "cpu_percent": float(cpu_str) if cpu_str.replace('.', '').isdigit() else 0,
                            "memory_mb": mem_mb,
                            "memory_percent": float(parts[3].strip().replace('%', '')) if len(parts) > 3 else 0
                        }
        except Exception as e:
            print(f"Error getting CLI stats for {container_name}: {e}")
            
        return None
    
    def _parse_ports_from_cli(self, ports_str: str) -> List[Dict[str, Any]]:
        """Parse port mappings from CLI output"""
        ports = []
        try:
            if ports_str and '>' in ports_str:
                # Format: 0.0.0.0:8080->80/tcp
                for port_mapping in ports_str.split(', '):
                    if '->' in port_mapping:
                        external_part, internal_part = port_mapping.split('->')
                        external_port = external_part.split(':')[-1]
                        internal_port = internal_part.split('/')[0]
                        
                        ports.append({
                            "internal": f"{internal_port}/tcp",
                            "external": external_port,
                            "host": "0.0.0.0"
                        })
        except:
            pass
        return ports
    
    def control_container(self, container_name: str, action: str) -> Dict[str, Any]:
        """Control a container (start/stop/restart)"""
        try:
            if self.docker_client:
                container = self.docker_client.containers.get(container_name)
                
                if action == 'start':
                    container.start()
                elif action == 'stop':
                    container.stop()
                elif action == 'restart':
                    container.restart()
                else:
                    return {"success": False, "error": f"Unknown action: {action}"}
                
                return {"success": True, "action": action, "container": container_name}
            else:
                # Use CLI fallback
                result = subprocess.run(['docker', action, container_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return {"success": True, "action": action, "container": container_name}
                else:
                    return {"success": False, "error": result.stderr}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
simple_docker_manager = SimpleDockerManager()