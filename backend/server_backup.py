from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psutil
import docker
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional
import GPUtil
import aiofiles
from pydantic import BaseModel
from fastapi import UploadFile, File

app = FastAPI(title="UC-1 Pro Admin Dashboard API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Warning: Docker client initialization failed: {e}")
    docker_client = None

# Service definitions
SERVICES = {
    "open-webui": {
        "container": "unicorn-open-webui",
        "name": "Chat UI",
        "port": 8080,
        "healthcheck": "/health",
        "description": "Web interface for AI chat interactions"
    },
    "vllm": {
        "container": "unicorn-vllm",
        "name": "vLLM API",
        "port": 8000,
        "healthcheck": "/health",
        "description": "High-performance LLM inference server"
    },
    "whisperx": {
        "container": "unicorn-whisperx",
        "name": "WhisperX",
        "port": 9000,
        "healthcheck": "/health",
        "description": "Advanced speech-to-text with speaker diarization"
    },
    "kokoro": {
        "container": "unicorn-kokoro",
        "name": "Kokoro TTS",
        "port": 8880,
        "healthcheck": "/health",
        "description": "High-quality text-to-speech synthesis"
    },
    "embeddings": {
        "container": "unicorn-embeddings",
        "name": "Embeddings",
        "port": 8082,
        "healthcheck": "/health",
        "description": "Text embedding service for RAG"
    },
    "reranker": {
        "container": "unicorn-reranker",
        "name": "Reranker",
        "port": 8083,
        "healthcheck": "/health",
        "description": "Document reranking for improved search"
    },
    "searxng": {
        "container": "unicorn-searxng",
        "name": "SearXNG",
        "port": 8888,
        "healthcheck": "/"
    },
    "prometheus": {
        "container": "unicorn-prometheus",
        "name": "Prometheus",
        "port": 9090,
        "healthcheck": "/-/healthy"
    }
}

class ServiceAction(BaseModel):
    action: str  # start, stop, restart

class NetworkConfig(BaseModel):
    interface: str
    method: str  # dhcp, static
    address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[List[str]] = None

class SystemSettings(BaseModel):
    idle_timeout_minutes: int = 5
    idle_policy: str = "swap"  # swap, unload, none
    idle_model: str = "microsoft/DialoGPT-small"
    enable_monitoring: bool = True
    enable_backups: bool = True
    backup_schedule: str = "0 2 * * *"

# API Routes

@app.get("/api/v1/system/status")
async def get_system_status():
    """Get current system resource usage"""
    try:
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        # GPU info (if available)
        gpu_info = []
        try:
            # Try using nvidia-ml-py instead of GPUtil
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    
                    gpu_info.append({
                        "name": name,
                        "utilization": utilization.gpu,
                        "memory_used": memory_info.used,
                        "memory_total": memory_info.total,
                        "temperature": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
                        "power_draw": 0,  # Would need specific function
                        "power_limit": 0
                    })
            except:
                # Fallback to GPUtil
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpu_info.append({
                        "name": gpu.name,
                        "utilization": round(gpu.load * 100, 1),
                        "memory_used": int(gpu.memoryUsed * 1024 * 1024),  # Convert to bytes
                        "memory_total": int(gpu.memoryTotal * 1024 * 1024),  # Convert to bytes
                        "temperature": gpu.temperature,
                        "power_draw": getattr(gpu, 'powerDraw', 0),
                        "power_limit": getattr(gpu, 'powerLimit', 0)
                    })
        except Exception as e:
            print(f"GPU info error: {e}")
            # Add mock GPU data for development
            if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
                gpu_info.append({
                    "name": "NVIDIA GeForce RTX 5090 (Mock)",
                    "utilization": 45.5,
                    "memory_used": 8589934592,  # 8GB
                    "memory_total": 34359738368,  # 32GB
                    "temperature": 65,
                    "power_draw": 250,
                    "power_limit": 450
                })
        
        # Get CPU frequency
        cpu_freq = psutil.cpu_freq()
        
        # Get load average
        load_avg = os.getloadavg()
        
        # Get uptime
        boot_time = psutil.boot_time()
        uptime = int(time.time() - boot_time)
        
        # Get top processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 0.1:  # Only show processes using CPU
                    processes.append({
                        "name": proc_info['name'],
                        "cpu_percent": proc_info['cpu_percent'],
                        "memory_mb": proc_info['memory_info'].rss / (1024 * 1024),
                        "status": proc_info['status']
                    })
            except:
                pass
        
        # Sort by CPU usage and take top 10
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
        
        return {
            "cpu": {
                "percent": round(cpu_percent, 1),
                "cores": cpu_count,
                "freq_current": int(cpu_freq.current) if cpu_freq else 0
            },
            "memory": {
                "used": memory.used,
                "total": memory.total,
                "percent": round(memory.percent, 1)
            },
            "disk": {
                "used": disk.used,
                "total": disk.total,
                "percent": round(disk.percent, 1)
            },
            "gpu": gpu_info,
            "uptime": uptime,
            "load_average": list(load_avg),
            "processes": processes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/services")
async def list_services():
    """List all services with their status"""
    services = []
    
    # If no Docker client, return mock data in development mode
    if not docker_client and os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
        # Return mock services for development
        for service_id, service_info in SERVICES.items():
            services.append({
                "name": service_id,
                "display_name": service_info["name"],
                "status": "healthy" if service_id in ["vllm", "open-webui"] else "stopped",
                "port": service_info["port"],
                "description": service_info.get("description", ""),
                "cpu_percent": 12.5 if service_id == "vllm" else 2.1,
                "memory_mb": 8192 if service_id == "vllm" else 512,
                "uptime": "2h 15m" if service_id in ["vllm", "open-webui"] else None,
                "health_check": None
            })
        return services
    
    if docker_client:
        try:
            containers = docker_client.containers.list(all=True)
            container_map = {c.name: c for c in containers}
            
            for service_id, service_info in SERVICES.items():
                container_name = service_info["container"]
                status = "unknown"
                
                if container_name in container_map:
                    container = container_map[container_name]
                    if container.status == "running":
                        # Check health if available
                        if hasattr(container, 'health'):
                            health = container.health
                            if health == "healthy":
                                status = "healthy"
                            elif health == "starting":
                                status = "starting"
                            else:
                                status = "unhealthy"
                        else:
                            status = "healthy"  # Assume healthy if no health check
                    else:
                        status = "stopped"
                
                service_data = {
                    "name": service_id,
                    "display_name": service_info["name"],
                    "status": status,
                    "port": service_info["port"],
                    "description": service_info.get("description", ""),
                    "cpu_percent": 0.0,
                    "memory_mb": 0,
                    "uptime": None,
                    "health_check": None
                }
                
                # Get container stats if running
                if container_name in container_map and container_map[container_name].status == "running":
                    try:
                        container = container_map[container_name]
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                        if system_delta > 0:
                            service_data["cpu_percent"] = (cpu_delta / system_delta) * 100.0
                        
                        # Memory usage
                        service_data["memory_mb"] = stats["memory_stats"]["usage"] / (1024 * 1024)
                        
                        # Uptime
                        started_at = container.attrs['State']['StartedAt']
                        if started_at:
                            from dateutil import parser
                            start_time = parser.isoparse(started_at)
                            uptime_seconds = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                            service_data["uptime"] = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
                    except Exception as e:
                        print(f"Error getting stats for {container_name}: {e}")
                
                services.append(service_data)
        except Exception as e:
            print(f"Error listing services: {e}")
    
    return services

@app.get("/api/v1/services/{service_id}")
async def get_service_details(service_id: str):
    """Get detailed information about a service"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_info = SERVICES[service_id]
    details = {
        "id": service_id,
        "name": service_info["name"],
        "port": service_info["port"],
        "status": "unknown",
        "stats": {}
    }
    
    if docker_client:
        try:
            container = docker_client.containers.get(service_info["container"])
            details["status"] = container.status
            
            # Get container stats
            stats = container.stats(stream=False)
            details["stats"] = {
                "cpu_percent": calculate_cpu_percent(stats),
                "memory_usage": stats["memory_stats"]["usage"] / (1024**2),  # MB
                "network_rx": stats["networks"]["eth0"]["rx_bytes"] / (1024**2),  # MB
                "network_tx": stats["networks"]["eth0"]["tx_bytes"] / (1024**2),  # MB
            }
        except Exception as e:
            print(f"Error getting service details: {e}")
    
    return details

@app.post("/api/v1/services/{service_id}/{action}")
async def service_action(service_id: str, action: str):
    """Start, stop, or restart a service"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    service_info = SERVICES[service_id]
    container_name = service_info["container"]
    
    try:
        # Change to the UC-1-Pro directory where docker-compose.yml is located
        # Try to find the correct path
        uc1_dir = None
        for possible_path in ["/home/ucadmin/UC-1-Pro", "/app/UC-1-Pro", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]:
            if os.path.exists(os.path.join(possible_path, "docker-compose.yml")):
                uc1_dir = possible_path
                break
        
        if not uc1_dir:
            raise HTTPException(status_code=500, detail="Could not find UC-1-Pro directory")
        
        if action == "restart":
            result = subprocess.run(
                ["docker", "compose", "restart", container_name],
                cwd=uc1_dir,
                capture_output=True,
                text=True
            )
        elif action == "stop":
            result = subprocess.run(
                ["docker", "compose", "stop", container_name],
                cwd=uc1_dir,
                capture_output=True,
                text=True
            )
        elif action == "start":
            result = subprocess.run(
                ["docker", "compose", "start", container_name],
                cwd=uc1_dir,
                capture_output=True,
                text=True
            )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to {action} service: {result.stderr}"
            )
        
        return {"status": "success", "message": f"Service {action} completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action failed: {e}")

@app.get("/api/v1/services/{service_id}/logs")
async def get_service_logs(service_id: str, lines: int = 100):
    """Get recent logs from a service"""
    if service_id not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_info = SERVICES[service_id]
    
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), service_info["container"]],
            capture_output=True,
            text=True
        )
        
        return {
            "logs": result.stdout,
            "errors": result.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model Management Endpoints
@app.get("/api/v1/models")
async def get_models():
    """Get list of installed models"""
    models = []
    
    # Check vLLM models directory
    models_dir = os.environ.get("MODELS_DIR", "/volumes/vllm_models")
    # For development, check relative path
    if not os.path.exists(models_dir):
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "volumes", "vllm_models")
    if os.path.exists(models_dir):
        try:
            for model_name in os.listdir(models_dir):
                model_path = os.path.join(models_dir, model_name)
                if os.path.isdir(model_path):
                    # Get model size
                    size = get_directory_size(model_path)
                    models.append({
                        "id": model_name,
                        "name": model_name,
                        "type": "vLLM",
                        "size": f"{size / (1024**3):.2f} GB",
                        "active": model_name == os.environ.get("DEFAULT_LLM_MODEL", "").split("/")[-1],
                        "last_used": None
                    })
        except Exception as e:
            print(f"Error listing models: {e}")
    
    return models

@app.get("/api/v1/models/search")
async def search_models(q: str = ""):
    """Search for models on Hugging Face"""
    # Trending models compatible with vLLM
    trending_models = [
        {
            "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "name": "Llama 3.1 8B Instruct",
            "description": "Latest Llama model optimized for instruction following",
            "downloads": 2500000,
            "likes": 15000,
            "size": "16GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0", "F16"],
            "trending": True,
            "vllm_compatible": True,
        },
        {
            "id": "Qwen/Qwen2.5-32B-Instruct",
            "name": "Qwen 2.5 32B Instruct",
            "description": "State-of-the-art model with 32K context length",
            "downloads": 1800000,
            "likes": 12000,
            "size": "65GB",
            "task": "text-generation",
            "quantizations": ["AWQ", "GPTQ", "Q4_K_M"],
            "trending": True,
            "vllm_compatible": True,
        },
        {
            "id": "mistralai/Mistral-7B-Instruct-v0.2",
            "name": "Mistral 7B Instruct v0.2",
            "description": "Efficient 7B model with sliding window attention",
            "downloads": 3200000,
            "likes": 18000,
            "size": "14GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0"],
            "trending": True,
            "vllm_compatible": True,
        },
        {
            "id": "deepseek-ai/deepseek-coder-33b-instruct",
            "name": "DeepSeek Coder 33B",
            "description": "Code generation specialist model",
            "downloads": 890000,
            "likes": 6700,
            "size": "66GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "AWQ"],
            "trending": True,
            "vllm_compatible": True,
        },
        {
            "id": "microsoft/Phi-3-medium-128k-instruct",
            "name": "Phi-3 Medium 128K",
            "description": "Small but capable model with huge context",
            "downloads": 1200000,
            "likes": 8900,
            "size": "28GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "F16"],
            "trending": True,
            "vllm_compatible": True,
        },
        {
            "id": "NousResearch/Hermes-2-Pro-Llama-3-8B",
            "name": "Hermes 2 Pro Llama 3 8B",
            "description": "Fine-tuned for function calling and structured output",
            "downloads": 670000,
            "likes": 4300,
            "size": "16GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0"],
            "vllm_compatible": True,
        },
        {
            "id": "TheBloke/Llama-2-70B-chat-GPTQ",
            "name": "Llama 2 70B Chat GPTQ",
            "description": "Large Llama 2 model quantized for efficiency",
            "downloads": 1500000,
            "likes": 9800,
            "size": "35GB",
            "task": "text-generation",
            "quantizations": ["GPTQ"],
            "vllm_compatible": True,
        },
        {
            "id": "WizardLM/WizardCoder-Python-34B-V1.0",
            "name": "WizardCoder Python 34B",
            "description": "Specialized for Python code generation",
            "downloads": 450000,
            "likes": 3200,
            "size": "68GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M"],
            "vllm_compatible": True,
        },
        {
            "id": "teknium/OpenHermes-2.5-Mistral-7B",
            "name": "OpenHermes 2.5 Mistral 7B",
            "description": "High quality fine-tune of Mistral",
            "downloads": 890000,
            "likes": 5600,
            "size": "14GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0"],
            "vllm_compatible": True,
        },
        {
            "id": "Nexusflow/StarCoder2-15B",
            "name": "StarCoder2 15B",
            "description": "Advanced code generation model",
            "downloads": 340000,
            "likes": 2100,
            "size": "30GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M"],
            "vllm_compatible": True,
        },
    ]
    
    if not q:
        # Return top 10 trending models
        return trending_models[:10]
    
    # Search through models
    q_lower = q.lower()
    results = []
    
    # Exact matches first
    for model in trending_models:
        if q_lower in model["id"].lower() or q_lower in model["name"].lower():
            results.append(model)
    
    # Then partial matches in description
    for model in trending_models:
        if model not in results and q_lower in model["description"].lower():
            results.append(model)
    
    # Limit to 10 results
    return results[:10]

class ModelDownload(BaseModel):
    model_id: str

@app.post("/api/v1/models/download")
async def download_model(request: ModelDownload):
    """Start downloading a model"""
    # This would trigger actual download
    return {"status": "started", "model_id": request.model_id}

@app.delete("/api/v1/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model"""
    return {"status": "deleted", "model_id": model_id}

class ActiveModel(BaseModel):
    model_id: str

class ModelConfig(BaseModel):
    model_id: str
    context_size: Optional[int] = None
    retention: Optional[str] = None

class GlobalModelSettings(BaseModel):
    default_retention: str = "keep"
    default_context_size: int = 16384

@app.post("/api/v1/models/active")
async def set_active_model(request: ActiveModel):
    """Set the active model"""
    # This would update the vLLM configuration
    return {"status": "activated", "model_id": request.model_id}

@app.post("/api/v1/models/upload")
async def upload_model(model: UploadFile = File(...)):
    """Upload a model file"""
    try:
        # Save to models directory
        models_dir = os.environ.get("MODELS_DIR", "/volumes/vllm_models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
        
        file_path = os.path.join(models_dir, model.filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await model.read()
            await f.write(content)
        
        return {"status": "success", "filename": model.filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/models/{model_id}/config")
async def update_model_config(model_id: str, config: ModelConfig):
    """Update model-specific configuration"""
    # Store model config (in production, this would update a database)
    return {"status": "updated", "model_id": model_id, "config": config.dict()}

@app.get("/api/v1/models/settings")
async def get_global_model_settings():
    """Get global model management settings"""
    # Return current settings (from config file or database)
    return {
        "default_retention": "keep",
        "default_context_size": 16384,
    }

@app.put("/api/v1/models/settings")
async def update_global_model_settings(settings: GlobalModelSettings):
    """Update global model management settings"""
    # Save settings (to config file or database)
    return {"status": "updated", "settings": settings.dict()}

@app.get("/api/v1/network/status")
async def get_network_status():
    """Get current network connection status"""
    status = {
        "ethernet": {
            "connected": False,
            "ip_address": None,
            "speed": None
        },
        "wifi": {
            "connected": False,
            "ssid": None,
            "ip_address": None,
            "signal_strength": None
        },
        "bluetooth": {
            "enabled": False,
            "devices": []
        }
    }
    
    # In development mode, return mock data
    if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
        return {
            "ethernet": {
                "connected": True,
                "ip_address": "192.168.1.100",
                "speed": 1000
            },
            "wifi": {
                "connected": True,
                "ssid": "Home Network 5G",
                "ip_address": "192.168.1.134",
                "signal_strength": -45
            },
            "bluetooth": {
                "enabled": True,
                "devices": []
            }
        }
    
    # Get network interfaces
    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    
    # Check ethernet (typically eth0 or enp*)
    for iface in interfaces:
        if iface.startswith(('eth', 'enp')):
            if iface in stats and stats[iface].isup:
                status["ethernet"]["connected"] = True
                # Get IP address
                for addr in interfaces[iface]:
                    if addr.family == 2:  # AF_INET (IPv4)
                        status["ethernet"]["ip_address"] = addr.address
                # Get speed if available
                if hasattr(stats[iface], 'speed'):
                    status["ethernet"]["speed"] = stats[iface].speed
    
    # Check WiFi (typically wlan0 or wlp*)
    for iface in interfaces:
        if iface.startswith(('wlan', 'wlp')):
            if iface in stats and stats[iface].isup:
                status["wifi"]["connected"] = True
                # Get IP address
                for addr in interfaces[iface]:
                    if addr.family == 2:  # AF_INET (IPv4)
                        status["wifi"]["ip_address"] = addr.address
                
                # Try to get WiFi details
                try:
                    # This would use nmcli or iwconfig on Linux
                    result = subprocess.run(['iwconfig', iface], capture_output=True, text=True)
                    if result.returncode == 0:
                        output = result.stdout
                        # Parse SSID
                        if 'ESSID:' in output:
                            ssid = output.split('ESSID:')[1].split('"')[1]
                            status["wifi"]["ssid"] = ssid
                        # Parse signal strength
                        if 'Signal level=' in output:
                            signal = output.split('Signal level=')[1].split(' ')[0]
                            status["wifi"]["signal_strength"] = int(signal)
                except:
                    pass
    
    return status

@app.get("/api/v1/network/wifi/scan")
async def scan_wifi_networks():
    """Scan for available WiFi networks"""
    networks = []
    
    # In development mode, return mock networks
    if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
        return [
            {"ssid": "Home Network 5G", "signal_strength": -45, "security": True},
            {"ssid": "Home Network", "signal_strength": -52, "security": True},
            {"ssid": "Guest Network", "signal_strength": -65, "security": False},
            {"ssid": "Neighbor's WiFi", "signal_strength": -78, "security": True},
        ]
    
    try:
        # First, trigger a scan
        subprocess.run(['nmcli', 'dev', 'wifi', 'rescan'], capture_output=True)
        
        # Use nmcli to list WiFi networks
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,IN-USE', 'dev', 'wifi'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            seen_ssids = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 3 and parts[0] and parts[0] not in seen_ssids:
                        seen_ssids.add(parts[0])
                        networks.append({
                            "ssid": parts[0],
                            "signal_strength": int(parts[1]) if parts[1] else 0,
                            "security": parts[2] != '' and parts[2] != '--',
                            "connected": len(parts) > 3 and parts[3] == '*'
                        })
            
            # Sort by signal strength
            networks.sort(key=lambda x: x['signal_strength'], reverse=True)
    except Exception as e:
        print(f"WiFi scan error: {e}")
    
    return networks

class WiFiConnect(BaseModel):
    ssid: str
    password: str

@app.post("/api/v1/network/wifi/connect")
async def connect_to_wifi(request: WiFiConnect):
    """Connect to a WiFi network"""
    # In development mode, simulate success
    if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
        return {"status": "connected", "message": f"Connected to {request.ssid} (simulated)"}
    
    try:
        # Use nmcli to connect
        result = subprocess.run(
            ['nmcli', 'dev', 'wifi', 'connect', request.ssid, 'password', request.password],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"status": "connected", "message": f"Connected to {request.ssid}"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to connect: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/network/configure")
async def configure_network(config: NetworkConfig):
    """Configure network settings"""
    # In development mode, simulate success
    if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
        return {"status": "configured", "message": "Network configuration applied (simulated)"}
    
    try:
        # Get the primary network interface
        interfaces = list(psutil.net_if_addrs().keys())
        # Find ethernet interface
        eth_interface = None
        for iface in interfaces:
            if iface.startswith(('eth', 'enp', 'ens')):
                eth_interface = iface
                break
        
        if not eth_interface:
            raise HTTPException(status_code=404, detail="No ethernet interface found")
        
        if config.method == 'dhcp':
            # Set to DHCP
            result = subprocess.run(
                ['nmcli', 'con', 'mod', eth_interface, 'ipv4.method', 'auto'],
                capture_output=True,
                text=True
            )
        else:
            # Set static IP
            if not config.address or not config.gateway:
                raise HTTPException(status_code=400, detail="Static IP requires address and gateway")
            
            # Configure static IP
            cmd = [
                'nmcli', 'con', 'mod', eth_interface,
                'ipv4.method', 'manual',
                'ipv4.addresses', f"{config.address}/{config.netmask or '24'}",
                'ipv4.gateway', config.gateway
            ]
            
            if config.dns:
                cmd.extend(['ipv4.dns', ','.join(config.dns)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Restart the connection
            subprocess.run(['nmcli', 'con', 'up', eth_interface], capture_output=True)
            return {"status": "configured", "message": "Network configuration applied"}
        else:
            raise HTTPException(status_code=500, detail=f"Configuration failed: {result.stderr}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/network/interfaces")
async def list_network_interfaces():
    """List all network interfaces"""
    interfaces = []
    
    for iface, addrs in psutil.net_if_addrs().items():
        iface_info = {
            "name": iface,
            "addresses": []
        }
        
        for addr in addrs:
            if addr.family == 2:  # IPv4
                iface_info["addresses"].append({
                    "type": "ipv4",
                    "address": addr.address,
                    "netmask": addr.netmask
                })
            elif addr.family == 17:  # MAC
                iface_info["mac"] = addr.address
        
        # Get interface stats
        stats = psutil.net_if_stats().get(iface)
        if stats:
            iface_info["is_up"] = stats.isup
            iface_info["speed"] = stats.speed
        
        interfaces.append(iface_info)
    
    return {"interfaces": interfaces}

@app.get("/api/v1/storage/usage")
async def get_storage_usage():
    """Get storage usage information"""
    partitions = []
    
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total / (1024**3),  # GB
                "used": usage.used / (1024**3),    # GB
                "free": usage.free / (1024**3),    # GB
                "percent": usage.percent
            })
        except PermissionError:
            continue
    
    # Model storage breakdown
    model_dirs = {
        "vllm": "/models",
        "whisperx": "/app/models",
        "kokoro": "/app/models",
        "embeddings": "/data",
        "reranker": "/app/models"
    }
    
    model_usage = {}
    for name, path in model_dirs.items():
        if os.path.exists(path):
            size = get_directory_size(path)
            model_usage[name] = size / (1024**3)  # GB
    
    return {
        "partitions": partitions,
        "models": model_usage
    }

@app.get("/api/v1/settings")
async def get_settings():
    """Get current system settings"""
    # Return default settings for now
    # In production, these would be loaded from a config file or database
    return {
        "system": {
            "idle_timeout": 300,
            "auto_swap_enabled": True,
            "max_memory_percent": 95,
            "log_level": "info",
        },
        "notifications": {
            "email_enabled": False,
            "email_address": "",
            "webhook_enabled": False,
            "webhook_url": "",
            "alert_on_errors": True,
            "alert_on_updates": False,
        },
        "security": {
            "auth_enabled": True,
            "session_timeout": 3600,
            "api_keys": [],
        },
        "backup": {
            "auto_backup_enabled": True,
            "backup_schedule": "0 2 * * *",
            "retention_days": 7,
            "backup_location": "/backups",
        },
    }

@app.put("/api/v1/settings")
async def update_settings(settings: dict):
    """Update system settings"""
    # Save to config file (in production)
    # Update relevant services
    return {"status": "success", "settings": settings}

@app.post("/api/v1/settings")
async def update_settings_post(settings: dict):
    """Update system settings (POST alternative)"""
    # Save to config file (in production)
    # Update relevant services
    return {"status": "success", "settings": settings}

# Extension management endpoints
@app.get("/api/v1/extensions")
async def list_extensions():
    """List available extensions and their status"""
    extensions = {
        "monitoring": {"status": "stopped", "port": 3000, "container_name": "monitoring-grafana-1"},
        "comfyui": {"status": "stopped", "port": 8188, "container_name": "comfyui-comfyui-1"},
        "bolt.diy": {"status": "stopped", "port": 3001, "container_name": "boltdiy-bolt-1"},
        "n8n": {"status": "stopped", "port": 5678, "container_name": "n8n-n8n-1"},
        "dev-tools": {"status": "stopped", "port": 8888, "container_name": "dev-tools-jupyterlab-1"},
        "traefik": {"status": "stopped", "port": 8090, "container_name": "traefik-traefik-1"},
        "portainer": {"status": "stopped", "port": 9444, "container_name": "portainer-portainer-1"},
        "ollama": {"status": "stopped", "port": 11434, "container_name": "unicorn-ollama"},
    }
    
    # Check actual Docker container status
    if docker_client:
        try:
            containers = docker_client.containers.list(all=True)
            container_map = {c.name: c.status for c in containers}
            
            for ext_id, ext_info in extensions.items():
                # Check by expected container name pattern
                container_name = ext_info.get("container_name")
                if container_name and container_name in container_map:
                    extensions[ext_id]["status"] = container_map[container_name]
                else:
                    # Fallback: check for any container with extension name
                    for cname, status in container_map.items():
                        if ext_id in cname.lower():
                            extensions[ext_id]["status"] = status
                            break
        except Exception as e:
            print(f"Error checking extension status: {e}")
    else:
        # In development mode, simulate some extensions running
        if os.environ.get('DEVELOPMENT', 'false').lower() == 'true':
            extensions["portainer"]["status"] = "running"
    
    return extensions

@app.post("/api/v1/extensions/{extension_id}/start")
async def start_extension(extension_id: str):
    """Start an extension"""
    try:
        # Find the UC-1-Pro directory
        uc1_dir = None
        for possible_path in ["/home/ucadmin/UC-1-Pro", "/app/UC-1-Pro", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]:
            if os.path.exists(os.path.join(possible_path, "extensions", extension_id)):
                uc1_dir = possible_path
                break
        
        if not uc1_dir:
            raise HTTPException(status_code=404, detail=f"Extension {extension_id} not found")
        
        extension_dir = os.path.join(uc1_dir, "extensions", extension_id)
        
        # Check if docker-compose.yml exists
        if not os.path.exists(os.path.join(extension_dir, "docker-compose.yml")):
            raise HTTPException(status_code=404, detail=f"Extension {extension_id} configuration not found")
        
        # Start the extension using docker-compose
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=extension_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start extension: {result.stderr}"
            )
        
        return {"status": "success", "message": f"Extension {extension_id} started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extensions/{extension_id}/stop")
async def stop_extension(extension_id: str):
    """Stop an extension"""
    try:
        # Find the UC-1-Pro directory
        uc1_dir = None
        for possible_path in ["/home/ucadmin/UC-1-Pro", "/app/UC-1-Pro", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]:
            if os.path.exists(os.path.join(possible_path, "extensions", extension_id)):
                uc1_dir = possible_path
                break
        
        if not uc1_dir:
            raise HTTPException(status_code=404, detail=f"Extension {extension_id} not found")
        
        extension_dir = os.path.join(uc1_dir, "extensions", extension_id)
        
        # Stop the extension using docker-compose
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=extension_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop extension: {result.stderr}"
            )
        
        return {"status": "success", "message": f"Extension {extension_id} stopped"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Send initial data
        try:
            system_status = await get_system_status()
            await websocket.send_json({"type": "system_update", "data": system_status})
            
            services = await list_services() 
            await websocket.send_json({"type": "services_update", "data": services})
            
            models = await get_models()
            await websocket.send_json({"type": "models_update", "data": models})
        except Exception as e:
            print(f"Error sending initial WebSocket data: {e}")
            return
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Send system status every 5 seconds
                system_status = await get_system_status()
                await websocket.send_json({"type": "system_update", "data": system_status})
                
                # Send service status every 10 seconds
                if int(asyncio.get_event_loop().time()) % 10 == 0:
                    services = await list_services()
                    await websocket.send_json({"type": "services_update", "data": services})
                
                await asyncio.sleep(5)
            except WebSocketDisconnect:
                print("WebSocket client disconnected")
                break
            except Exception as e:
                print(f"WebSocket send error: {e}")
                break
    except WebSocketDisconnect:
        print("WebSocket disconnected during setup")
    except Exception as e:
        print(f"WebSocket error: {e}")

# Helper functions
def calculate_cpu_percent(stats):
    """Calculate CPU percentage from Docker stats"""
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                   stats["precpu_stats"]["system_cpu_usage"]
    
    if system_delta > 0:
        cpu_percent = (cpu_delta / system_delta) * 100
        return round(cpu_percent, 2)
    return 0

def get_directory_size(path):
    """Get total size of a directory"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

# Serve the React app index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # Check if it's an API route
    if full_path.startswith("api/") or full_path.startswith("ws"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if the file exists in dist
    file_path = os.path.join("dist", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, serve index.html for client-side routing
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)