#!/usr/bin/env python3
"""
Quick fix for Docker container detection
"""
import subprocess
import json
from typing import Dict, List, Any

def get_running_services() -> List[Dict[str, Any]]:
    """Get running UC-1 Pro services directly via CLI"""
    services = []
    
    # UC-1 Pro service mappings with type information
    service_map = {
        # Core Services
        'unicorn-vllm': {'name': 'vllm', 'display_name': 'vLLM (Qwen 32B)', 'port': '8000', 'type': 'core', 'category': 'inference'},
        'unicorn-vllm-gemma3': {'name': 'vllm-gemma3', 'display_name': 'vLLM (Gemma 3 27B)', 'port': '8005', 'type': 'core', 'category': 'inference'},
        'unicorn-vllm-gemma3-1b': {'name': 'vllm-gemma3-1b', 'display_name': 'vLLM (Gemma 3 1B)', 'port': '8006', 'type': 'core', 'category': 'inference'},
        'unicorn-vllm-gemma3-4b': {'name': 'vllm-gemma3-4b', 'display_name': 'vLLM (Gemma 3 4B)', 'port': '8007', 'type': 'core', 'category': 'inference'},
        'unicorn-vllm-gemma3-12b': {'name': 'vllm-gemma3-12b', 'display_name': 'vLLM (Gemma 3 12B)', 'port': '8008', 'type': 'core', 'category': 'inference'},
        'unicorn-open-webui': {'name': 'open-webui', 'display_name': 'Open WebUI', 'port': '8080', 'type': 'core', 'category': 'interface'},
        'unicorn-redis': {'name': 'redis', 'display_name': 'Redis', 'port': '6379', 'type': 'core', 'category': 'database'},
        'unicorn-postgresql': {'name': 'postgresql', 'display_name': 'PostgreSQL', 'port': '5432', 'type': 'core', 'category': 'database'},
        'unicorn-qdrant': {'name': 'qdrant', 'display_name': 'Qdrant', 'port': '6333', 'type': 'core', 'category': 'database'},
        'unicorn-whisperx': {'name': 'whisperx', 'display_name': 'WhisperX', 'port': '9000', 'type': 'core', 'category': 'processing'},
        'unicorn-kokoro': {'name': 'kokoro-tts', 'display_name': 'Kokoro TTS', 'port': '8880', 'type': 'core', 'category': 'processing'},
        'unicorn-searxng': {'name': 'searxng', 'display_name': 'Center-Deep', 'port': '8888', 'type': 'core', 'category': 'search'},
        'unicorn-embeddings': {'name': 'embeddings', 'display_name': 'Embeddings', 'port': '8082', 'type': 'core', 'category': 'processing'},
        'unicorn-reranker': {'name': 'reranker', 'display_name': 'Reranker', 'port': '8083', 'type': 'core', 'category': 'processing'},
        'unicorn-tika': {'name': 'tika', 'display_name': 'Apache Tika', 'port': '9998', 'type': 'core', 'category': 'processing'},
        'unicorn-ops-center': {'name': 'ops-center', 'display_name': 'Operations Center', 'port': '8084', 'type': 'core', 'category': 'management'},
        'unicorn-gpu-exporter': {'name': 'gpu-metrics', 'display_name': 'GPU Metrics', 'port': '9835', 'type': 'core', 'category': 'monitoring'},
        
        # Extension Services
        'unicorn-ollama': {'name': 'ollama', 'display_name': 'Ollama', 'port': '11434', 'type': 'extension', 'category': 'inference'},
        'unicorn-ollama-webui': {'name': 'ollama-webui', 'display_name': 'Ollama WebUI', 'port': '11435', 'type': 'extension', 'category': 'interface'},
        
        # Authentication Services (Authentik SSO)
        'authentik-server': {'name': 'authentik-server', 'display_name': 'Authentik SSO', 'port': '9000', 'type': 'extension', 'category': 'authentication'},
        'authentik-worker': {'name': 'authentik-worker', 'display_name': 'Authentik Worker', 'port': '', 'type': 'extension', 'category': 'authentication'},
        'authentik-postgresql': {'name': 'authentik-db', 'display_name': 'Authentik Database', 'port': '5432', 'type': 'extension', 'category': 'authentication'},
        'authentik-redis': {'name': 'authentik-cache', 'display_name': 'Authentik Cache', 'port': '6379', 'type': 'extension', 'category': 'authentication'},
        'authentik-proxy': {'name': 'authentik-proxy', 'display_name': 'Authentik Proxy', 'port': '9876', 'type': 'extension', 'category': 'authentication'},
        
        # Traefik Reverse Proxy
        'traefik': {'name': 'traefik', 'display_name': 'Traefik Proxy', 'port': '80', 'type': 'extension', 'category': 'proxy'},
        'traefik-dashboard': {'name': 'traefik-api', 'display_name': 'Traefik Dashboard', 'port': '8080', 'type': 'extension', 'category': 'proxy'}
    }
    
    try:
        # Get all containers
        result = subprocess.run([
            'docker', 'ps', '-a', '--format', 
            '{{.Names}}|{{.Status}}|{{.Image}}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"Docker command failed: {result.stderr}")
            return []
            
        lines = result.stdout.strip().split('\n')
        running_containers = {}
        
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    status = parts[1].strip()
                    
                    # Normalize status
                    if 'Up' in status:
                        if 'unhealthy' in status:
                            normalized_status = 'unhealthy'
                        elif 'healthy' in status:
                            normalized_status = 'running'
                        else:
                            normalized_status = 'running'
                    elif 'Restarting' in status:
                        normalized_status = 'restarting'
                    elif 'Exited' in status or 'Created' in status:
                        normalized_status = 'stopped'
                    else:
                        normalized_status = 'unknown'
                        
                    running_containers[name] = normalized_status
        
        # Build service list
        for container_name, service_info in service_map.items():
            status = running_containers.get(container_name, 'stopped')
            
            # Get basic stats for running containers (optimized for speed)
            cpu_percent = 0
            memory_mb = 0
            
            # Skip individual docker stats calls to improve performance
            # Individual stats collection was taking 5+ seconds per container
            # TODO: Implement batch stats collection or use Docker API directly
            # if status in ['running', 'unhealthy']:
            #     try:
            #         stats_result = subprocess.run([
            #             'docker', 'stats', '--no-stream', '--format', 
            #             '{{.CPUPerc}}|{{.MemUsage}}', container_name
            #         ], capture_output=True, text=True, timeout=2)
            #         
            #         if stats_result.returncode == 0 and '|' in stats_result.stdout:
            #             stats_parts = stats_result.stdout.strip().split('|')
            #             if len(stats_parts) >= 2:
            #                 cpu_str = stats_parts[0].replace('%', '').strip()
            #                 mem_str = stats_parts[1].split('/')[0].strip()
            #                 
            #                 try:
            #                     cpu_percent = float(cpu_str)
            #                 except:
            #                     cpu_percent = 0
            #                     
            #                 # Parse memory (handle MiB/GiB)
            #                 if 'GiB' in mem_str:
            #                     memory_mb = float(mem_str.replace('GiB', '')) * 1024
            #                 elif 'MiB' in mem_str:
            #                     memory_mb = float(mem_str.replace('MiB', ''))
            #                 else:
            #                     memory_mb = 0
            #     except:
            #         pass
            
            services.append({
                'name': service_info['name'],
                'display_name': service_info['display_name'],
                'status': status,
                'port': int(service_info['port']) if service_info['port'] else None,
                'container_name': container_name,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'type': service_info.get('type', 'core'),
                'category': service_info.get('category', 'general'),
                'gpu_enabled': service_info['name'] in ['vllm', 'whisperx', 'kokoro-tts', 'ollama'],
                'description': f"UC-1 Pro {'extension' if service_info.get('type') == 'extension' else 'core'} service: {service_info['name']}",
                'image': 'unknown',
                'uptime': None
            })
            
    except Exception as e:
        print(f"Error getting services: {e}")
        return []
    
    return services

if __name__ == "__main__":
    services = get_running_services()
    print(f"Found {len(services)} services:")
    for s in services[:5]:
        print(f"  {s['name']}: {s['status']} (CPU: {s['cpu_percent']}%, RAM: {s['memory_mb']:.0f}MB)")