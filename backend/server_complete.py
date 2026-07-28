from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import psutil
import docker
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import GPUtil
import aiofiles
from pydantic import BaseModel
from fastapi import UploadFile, File
import httpx
import yaml
from pathlib import Path
import hashlib
import shutil
from collections import defaultdict
import re

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

# Model registry storage
MODEL_REGISTRY_PATH = "/volumes/model_registry.json"
MODELS_DIR = os.environ.get("MODELS_DIR", "/volumes/vllm_models")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Active downloads tracking
active_downloads = {}
download_progress = defaultdict(lambda: {"status": "pending", "progress": 0, "speed": 0, "eta": None})

# Initialize model registry
def load_model_registry():
    if os.path.exists(MODEL_REGISTRY_PATH):
        try:
            with open(MODEL_REGISTRY_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "models": {},
        "active_model": None,
        "global_settings": {
            "default_retention": "keep",
            "default_context_size": 16384
        }
    }

def save_model_registry(registry):
    try:
        with open(MODEL_REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        print(f"Error saving model registry: {e}")

model_registry = load_model_registry()

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
        "healthcheck": "/",
        "description": "Private search engine"
    },
    "qdrant": {
        "container": "unicorn-qdrant",
        "name": "Qdrant",
        "port": 6333,
        "healthcheck": "/health",
        "description": "Vector database for embeddings"
    },
    "tika-ocr": {
        "container": "unicorn-tika-ocr",
        "name": "Tika OCR",
        "port": 9998,
        "healthcheck": "/",
        "description": "Document parsing and OCR"
    },
    "postgres": {
        "container": "unicorn-postgres",
        "name": "PostgreSQL",
        "port": 5432,
        "healthcheck": None,
        "description": "Main database"
    },
    "redis": {
        "container": "unicorn-redis",
        "name": "Redis",
        "port": 6379,
        "healthcheck": None,
        "description": "Cache and message queue"
    },
    "prometheus": {
        "container": "unicorn-prometheus",
        "name": "Prometheus",
        "port": 9090,
        "healthcheck": "/-/healthy",
        "description": "Metrics collection"
    }
}

# WebSocket connections
websocket_connections = set()

# Pydantic models
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

class ModelDownload(BaseModel):
    model_id: str
    quantization: Optional[str] = None

class ModelEstimate(BaseModel):
    model_id: str
    model_size: str
    quantization: str
    context_size: int = 16384

class ActiveModel(BaseModel):
    model_id: str

class ModelConfig(BaseModel):
    retention: Optional[str] = None
    context_size: Optional[int] = None

class GlobalModelSettings(BaseModel):
    default_retention: str = "keep"
    default_context_size: int = 16384

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_progress(model_id: str, progress_data: dict):
    """Broadcast download progress to all connected WebSocket clients"""
    message = json.dumps({
        "type": "download_progress",
        "model_id": model_id,
        "data": progress_data
    })
    
    disconnected = set()
    for websocket in websocket_connections:
        try:
            await websocket.send_text(message)
        except:
            disconnected.add(websocket)
    
    # Clean up disconnected websockets
    for ws in disconnected:
        websocket_connections.discard(ws)

# Hugging Face API functions
async def search_huggingface_models(query: str, limit: int = 20):
    """Search Hugging Face for models"""
    async with httpx.AsyncClient() as client:
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"
        
        # Search for text-generation models that are likely vLLM compatible
        params = {
            "search": query,
            "filter": "text-generation",
            "limit": limit,
            "sort": "downloads"
        }
        
        try:
            response = await client.get(
                "https://huggingface.co/api/models",
                params=params,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                models = response.json()
                
                # Process and enhance model data
                processed_models = []
                for model in models:
                    # Fetch model card to get more details
                    try:
                        card_response = await client.get(
                            f"https://huggingface.co/api/models/{model['id']}",
                            headers=headers,
                            timeout=5.0
                        )
                        if card_response.status_code == 200:
                            model_details = card_response.json()
                            
                            # Determine available quantizations
                            files = model_details.get("siblings", [])
                            quantizations = detect_quantizations(files)
                            
                            # Estimate model size
                            model_size = estimate_model_size_from_files(files)
                            
                            processed_models.append({
                                "id": model["id"],
                                "name": model.get("id", "").split("/")[-1],
                                "description": model.get("pipeline_tag", "Text generation model"),
                                "downloads": model_details.get("downloads", 0),
                                "likes": model_details.get("likes", 0),
                                "size": model_size,
                                "task": "text-generation",
                                "quantizations": quantizations,
                                "vllm_compatible": check_vllm_compatibility(model_details),
                                "trending": model_details.get("downloads", 0) > 100000
                            })
                    except:
                        # Fallback for models where detailed info fails
                        processed_models.append({
                            "id": model["id"],
                            "name": model.get("id", "").split("/")[-1],
                            "description": "Model from Hugging Face",
                            "downloads": model.get("downloads", 0),
                            "likes": model.get("likes", 0),
                            "size": "Unknown",
                            "task": "text-generation",
                            "quantizations": ["Q4_K_M", "Q5_K_M"],
                            "vllm_compatible": True
                        })
                
                return processed_models[:limit]
            
        except Exception as e:
            print(f"Error searching HuggingFace: {e}")
    
    # Return fallback trending models on error
    return get_trending_models()[:limit]

def get_trending_models():
    """Get trending models as fallback"""
    return [
        {
            "id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "name": "Llama 3.1 8B Instruct",
            "description": "Latest Llama model optimized for instruction following",
            "downloads": 2500000,
            "likes": 15000,
            "size": "16GB",
            "task": "text-generation",
            "quantizations": ["Q4_K_M", "Q5_K_M", "Q8_0", "F16"],
            "vllm_compatible": True,
            "trending": True
        },
        {
            "id": "Qwen/Qwen2.5-32B-Instruct-AWQ",
            "name": "Qwen 2.5 32B Instruct AWQ",
            "description": "State-of-the-art model with 32K context length",
            "downloads": 1800000,
            "likes": 12000,
            "size": "18GB",
            "task": "text-generation",
            "quantizations": ["AWQ"],
            "vllm_compatible": True,
            "trending": True
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
            "vllm_compatible": True,
            "trending": True
        }
    ]

def detect_quantizations(files):
    """Detect available quantizations from model files"""
    quantizations = set()
    
    for file in files:
        filename = file.get("rfilename", "")
        
        # Check for common quantization patterns
        if "awq" in filename.lower():
            quantizations.add("AWQ")
        if "gptq" in filename.lower():
            quantizations.add("GPTQ")
        if "q4_k_m" in filename.lower():
            quantizations.add("Q4_K_M")
        if "q5_k_m" in filename.lower():
            quantizations.add("Q5_K_M")
        if "q8_0" in filename.lower():
            quantizations.add("Q8_0")
        if "fp16" in filename.lower() or "f16" in filename.lower():
            quantizations.add("F16")
        if ".gguf" in filename:
            # GGUF files often have multiple quants
            quantizations.update(["Q4_K_M", "Q5_K_M", "Q8_0"])
    
    # Default quantizations if none detected
    if not quantizations:
        quantizations = {"Q4_K_M", "Q5_K_M"}
    
    return sorted(list(quantizations))

def estimate_model_size_from_files(files):
    """Estimate total model size from file listing"""
    total_size = 0
    
    for file in files:
        size = file.get("size", 0)
        total_size += size
    
    # Convert to human readable
    if total_size == 0:
        return "Unknown"
    
    gb = total_size / (1024 ** 3)
    if gb > 1:
        return f"{gb:.1f}GB"
    
    mb = total_size / (1024 ** 2)
    return f"{mb:.0f}MB"

def check_vllm_compatibility(model_details):
    """Check if model is likely vLLM compatible"""
    # Check model architecture
    config = model_details.get("config", {})
    arch = config.get("model_type", "").lower()
    
    # Known vLLM compatible architectures
    vllm_architectures = [
        "llama", "mistral", "qwen", "phi", "gemma", "gpt2", "gptj", 
        "gpt_neox", "opt", "bloom", "falcon", "mpt", "starcoder",
        "baichuan", "aquila", "chatglm", "internlm", "yi"
    ]
    
    for va in vllm_architectures:
        if va in arch:
            return True
    
    # Check tags
    tags = model_details.get("tags", [])
    if "text-generation" in tags:
        return True
    
    # Default to true for text-generation models
    return True

# Memory estimation
def calculate_model_memory(model_size_str: str, quantization: str, context_size: int = 16384):
    """Calculate memory requirements for a model"""
    # Parse model size
    size_gb = 0
    if "GB" in model_size_str.upper():
        size_gb = float(re.findall(r'[\d.]+', model_size_str)[0])
    elif "MB" in model_size_str.upper():
        size_gb = float(re.findall(r'[\d.]+', model_size_str)[0]) / 1024
    elif "B" in model_size_str:
        # Assume it's parameter count in billions
        param_b = float(re.findall(r'[\d.]+', model_size_str)[0])
        # Rough estimate: 2 bytes per parameter for fp16
        size_gb = (param_b * 2)
    
    # Quantization multipliers
    quant_multipliers = {
        'F16': 1.0,        # Full precision
        'FP16': 1.0,
        'Q8_0': 0.5,       # 8-bit quantization  
        'Q5_K_M': 0.375,   # 5-bit quantization
        'Q4_K_M': 0.25,    # 4-bit quantization
        'AWQ': 0.25,       # AWQ 4-bit
        'GPTQ': 0.25,      # GPTQ 4-bit
        'Q3_K_M': 0.1875   # 3-bit quantization
    }
    
    multiplier = quant_multipliers.get(quantization, 0.25)
    model_memory_gb = size_gb * multiplier
    
    # Context memory calculation
    # Rough estimate: 4 bytes per token for KV cache
    context_memory_gb = (context_size * 4 * 2) / (1024 ** 3)  # *2 for K and V
    
    # Add overhead (20% for safety)
    total_memory_gb = (model_memory_gb + context_memory_gb) * 1.2
    
    # Get available GPU memory
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            available_memory_gb = gpus[0].memoryFree / 1024
            total_gpu_memory_gb = gpus[0].memoryTotal / 1024
            usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
        else:
            available_memory_gb = 32  # Default for RTX 5090
            total_gpu_memory_gb = 32
            usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
    except:
        available_memory_gb = 32
        total_gpu_memory_gb = 32
        usage_percentage = (total_memory_gb / total_gpu_memory_gb) * 100
    
    return {
        "model": round(model_memory_gb, 2),
        "context": round(context_memory_gb, 2),
        "total": round(total_memory_gb, 2),
        "available": round(available_memory_gb, 2),
        "percentage": round(usage_percentage, 1),
        "fits": total_memory_gb <= available_memory_gb
    }

# Model download functionality
async def download_model_with_progress(model_id: str, quantization: Optional[str], background_tasks: BackgroundTasks):
    """Download a model using huggingface-cli with progress tracking"""
    download_id = hashlib.md5(f"{model_id}:{quantization}".encode()).hexdigest()
    
    # Initialize progress
    download_progress[download_id] = {
        "status": "initializing",
        "progress": 0,
        "speed": 0,
        "eta": None,
        "model_id": model_id,
        "quantization": quantization
    }
    
    try:
        # Create model directory
        model_path = os.path.join(MODELS_DIR, model_id.replace("/", "_"))
        os.makedirs(model_path, exist_ok=True)
        
        # Build huggingface-cli command
        cmd = ["huggingface-cli", "download", model_id, "--local-dir", model_path]
        
        if HF_TOKEN:
            cmd.extend(["--token", HF_TOKEN])
        
        if quantization:
            # Add pattern to download only specific quantization files
            if quantization == "AWQ":
                cmd.extend(["--include", "*awq*", "*.json", "*.txt"])
            elif quantization == "GPTQ":
                cmd.extend(["--include", "*gptq*", "*.json", "*.txt"])
            elif quantization in ["Q4_K_M", "Q5_K_M", "Q8_0"]:
                cmd.extend(["--include", f"*{quantization.lower()}*", "*.json", "*.txt"])
        
        # Start download process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        download_progress[download_id]["status"] = "downloading"
        active_downloads[download_id] = process
        
        # Parse output for progress
        start_time = time.time()
        last_update = 0
        
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            
            line = line.decode('utf-8').strip()
            
            # Parse progress from huggingface-cli output
            if "Downloading" in line or "%" in line:
                # Extract progress percentage
                match = re.search(r'(\d+)%', line)
                if match:
                    progress = int(match.group(1))
                    current_time = time.time()
                    
                    # Calculate speed
                    if current_time - last_update > 1:  # Update every second
                        elapsed = current_time - start_time
                        speed = progress / elapsed if elapsed > 0 else 0
                        eta = (100 - progress) / speed if speed > 0 else None
                        
                        download_progress[download_id].update({
                            "status": "downloading",
                            "progress": progress,
                            "speed": round(speed, 2),
                            "eta": round(eta) if eta else None
                        })
                        
                        # Broadcast progress
                        await broadcast_progress(model_id, download_progress[download_id])
                        last_update = current_time
        
        # Wait for completion
        await process.wait()
        
        if process.returncode == 0:
            # Success - register the model
            download_progress[download_id]["status"] = "completed"
            download_progress[download_id]["progress"] = 100
            
            # Add to model registry
            model_registry["models"][model_id] = {
                "id": model_id,
                "path": model_path,
                "quantization": quantization,
                "downloaded_at": datetime.now().isoformat(),
                "size": get_directory_size(model_path),
                "active": False
            }
            save_model_registry(model_registry)
            
            await broadcast_progress(model_id, download_progress[download_id])
        else:
            # Failed
            download_progress[download_id]["status"] = "failed"
            download_progress[download_id]["error"] = "Download failed"
            await broadcast_progress(model_id, download_progress[download_id])
    
    except Exception as e:
        download_progress[download_id]["status"] = "failed"
        download_progress[download_id]["error"] = str(e)
        await broadcast_progress(model_id, download_progress[download_id])
    
    finally:
        # Cleanup
        if download_id in active_downloads:
            del active_downloads[download_id]

def get_directory_size(path):
    """Get total size of a directory"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except:
        pass
    
    # Convert to human readable
    gb = total / (1024 ** 3)
    if gb > 1:
        return f"{gb:.1f}GB"
    mb = total / (1024 ** 2)
    return f"{mb:.0f}MB"

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
            "load_average": list(load_avg)
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
                "uptime": "2h 15m" if service_id in ["vllm", "open-webui"] else None
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
                        status = "healthy"
                    else:
                        status = "stopped"
                
                service_data = {
                    "name": service_id,
                    "display_name": service_info["name"],
                    "status": status,
                    "port": service_info["port"],
                    "description": service_info.get("description", "")
                }
                
                services.append(service_data)
                
        except Exception as e:
            print(f"Error listing services: {e}")
    
    return services

@app.post("/api/v1/services/{service_name}/action")
async def service_action(service_name: str, action: ServiceAction):
    """Perform action on a service"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if not docker_client:
        return {"status": "mock", "message": f"Would {action.action} service {service_name}"}
    
    try:
        container_name = SERVICES[service_name]["container"]
        container = docker_client.containers.get(container_name)
        
        if action.action == "start":
            container.start()
        elif action.action == "stop":
            container.stop()
        elif action.action == "restart":
            container.restart()
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        return {"status": "success", "action": action.action, "service": service_name}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model Management Routes

@app.get("/api/v1/models/search")
async def search_models(q: Optional[str] = None):
    """Search for models on Hugging Face"""
    if not q:
        # Return trending models
        trending = await search_huggingface_models("", limit=10)
        return trending
    
    # Search with query
    results = await search_huggingface_models(q, limit=20)
    return results

@app.post("/api/v1/models/estimate-memory")
async def estimate_memory(request: ModelEstimate):
    """Estimate memory requirements for a model"""
    return calculate_model_memory(
        request.model_size,
        request.quantization,
        request.context_size
    )

@app.post("/api/v1/models/download")
async def download_model(request: ModelDownload, background_tasks: BackgroundTasks):
    """Start downloading a model"""
    # Check if already downloading
    for download_id, progress in download_progress.items():
        if progress.get("model_id") == request.model_id and progress.get("status") in ["initializing", "downloading"]:
            return {"status": "already_downloading", "model_id": request.model_id}
    
    # Start download in background
    background_tasks.add_task(
        download_model_with_progress,
        request.model_id,
        request.quantization
    )
    
    return {"status": "started", "model_id": request.model_id}

@app.get("/api/v1/models/download-progress/{model_id:path}")
async def get_download_progress(model_id: str):
    """Get download progress for a model"""
    # Find progress for this model
    for download_id, progress in download_progress.items():
        if progress.get("model_id") == model_id:
            return progress
    
    return {"status": "not_found"}

@app.get("/api/v1/models")
async def get_models():
    """Get list of downloaded models"""
    models = []
    
    for model_id, model_info in model_registry["models"].items():
        models.append({
            "id": model_id,
            "name": model_id.split("/")[-1],
            "type": "Local",
            "size": model_info.get("size", "Unknown"),
            "last_used": model_info.get("last_used", "Never"),
            "active": model_info.get("active", False),
            "quantization": model_info.get("quantization", "Unknown"),
            "path": model_info.get("path", "")
        })
    
    return models

@app.delete("/api/v1/models/{model_id:path}")
async def delete_model(model_id: str):
    """Delete a model"""
    if model_id in model_registry["models"]:
        model_info = model_registry["models"][model_id]
        model_path = model_info.get("path", "")
        
        # Delete files
        if os.path.exists(model_path):
            shutil.rmtree(model_path)
        
        # Remove from registry
        del model_registry["models"][model_id]
        save_model_registry(model_registry)
        
        return {"status": "deleted", "model_id": model_id}
    
    raise HTTPException(status_code=404, detail="Model not found")

@app.post("/api/v1/models/active")
async def set_active_model(request: ActiveModel):
    """Set the active model and restart vLLM"""
    model_id = request.model_id
    
    if model_id not in model_registry["models"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Update registry
    for mid in model_registry["models"]:
        model_registry["models"][mid]["active"] = (mid == model_id)
    
    model_registry["active_model"] = model_id
    save_model_registry(model_registry)
    
    # Update vLLM configuration
    if docker_client:
        try:
            # Get vLLM container
            vllm_container = docker_client.containers.get("unicorn-vllm")
            
            # Update environment variable
            env_vars = vllm_container.attrs['Config']['Env']
            new_env = []
            
            for env in env_vars:
                if not env.startswith("MODEL="):
                    new_env.append(env)
            
            new_env.append(f"MODEL={model_id}")
            
            # Restart container with new model
            vllm_container.stop()
            vllm_container.remove()
            
            # Get original run config
            config = vllm_container.attrs
            
            # Start new container with updated model
            docker_client.containers.run(
                image=config['Config']['Image'],
                name="unicorn-vllm",
                environment=new_env,
                ports={"8000/tcp": 8000},
                volumes=config['Mounts'],
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            return {"status": "activated", "model_id": model_id}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")
    
    return {"status": "activated", "model_id": model_id, "note": "Docker not available, model marked as active"}

@app.put("/api/v1/models/{model_id:path}/config")
async def update_model_config(model_id: str, config: ModelConfig):
    """Update model-specific configuration"""
    if model_id not in model_registry["models"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if config.retention is not None:
        model_registry["models"][model_id]["retention"] = config.retention
    
    if config.context_size is not None:
        model_registry["models"][model_id]["context_size"] = config.context_size
    
    save_model_registry(model_registry)
    
    return {"status": "updated", "model_id": model_id}

@app.get("/api/v1/models/settings")
async def get_model_settings():
    """Get global model settings"""
    return model_registry["global_settings"]

@app.put("/api/v1/models/settings")
async def update_model_settings(settings: GlobalModelSettings):
    """Update global model settings"""
    model_registry["global_settings"].update(settings.dict())
    save_model_registry(model_registry)
    
    return {"status": "updated"}

@app.post("/api/v1/models/upload")
async def upload_model(model: UploadFile = File(...)):
    """Upload a model file"""
    try:
        # Save to models directory
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)
        
        file_path = os.path.join(MODELS_DIR, model.filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await model.read()
            await f.write(content)
        
        # Add to registry
        model_id = f"local/{model.filename}"
        model_registry["models"][model_id] = {
            "id": model_id,
            "path": file_path,
            "uploaded_at": datetime.now().isoformat(),
            "size": get_directory_size(file_path),
            "active": False
        }
        save_model_registry(model_registry)
        
        return {"status": "uploaded", "model_id": model_id, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Network management routes
@app.get("/api/v1/network/status")
async def get_network_status():
    """Get network status and interfaces"""
    # Mock data for now
    return {
        "ethernet": {
            "connected": True,
            "ip": "192.168.1.100",
            "interface": "eth0"
        },
        "wifi": {
            "connected": False,
            "ssid": None,
            "signal": 0
        },
        "bluetooth": {
            "enabled": True,
            "devices": 0
        }
    }

@app.get("/api/v1/network/wifi/scan")
async def scan_wifi():
    """Scan for WiFi networks"""
    # Mock data for development
    return [
        {"ssid": "UnicornNet", "signal": 85, "security": "WPA2"},
        {"ssid": "MagicWiFi", "signal": 70, "security": "WPA3"},
        {"ssid": "Guest Network", "signal": 60, "security": "Open"}
    ]

# Settings routes
@app.get("/api/v1/settings")
async def get_settings():
    """Get system settings"""
    return {
        "idle_timeout_minutes": 5,
        "idle_policy": "swap",
        "idle_model": "microsoft/DialoGPT-small",
        "enable_monitoring": True,
        "enable_backups": True,
        "backup_schedule": "0 2 * * *"
    }

@app.put("/api/v1/settings")
async def update_settings(settings: SystemSettings):
    """Update system settings"""
    # Save settings (mock for now)
    return {"status": "updated"}

# Extension management
EXTENSIONS_DIR = "/home/ucadmin/UC-1-Pro/extensions"

@app.get("/api/v1/extensions")
async def get_extensions():
    """Get list of available extensions"""
    extensions = []
    
    # Check extensions directory
    if os.path.exists(EXTENSIONS_DIR):
        for ext_name in os.listdir(EXTENSIONS_DIR):
            ext_path = os.path.join(EXTENSIONS_DIR, ext_name)
            if os.path.isdir(ext_path) and os.path.exists(os.path.join(ext_path, "docker-compose.yml")):
                # Check if extension is running
                status = "stopped"
                if docker_client:
                    try:
                        # Check for containers with extension name
                        containers = docker_client.containers.list(filters={"label": f"extension={ext_name}"})
                        if containers:
                            status = "running"
                    except:
                        pass
                
                extensions.append({
                    "id": ext_name,
                    "status": status
                })
    
    return extensions

@app.post("/api/v1/extensions/{extension_id}/start")
async def start_extension(extension_id: str):
    """Start an extension"""
    ext_path = os.path.join(EXTENSIONS_DIR, extension_id)
    if not os.path.exists(ext_path):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    try:
        # Run docker-compose up for the extension
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=ext_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"status": "started", "extension": extension_id}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extensions/{extension_id}/stop")
async def stop_extension(extension_id: str):
    """Stop an extension"""
    ext_path = os.path.join(EXTENSIONS_DIR, extension_id)
    if not os.path.exists(ext_path):
        raise HTTPException(status_code=404, detail="Extension not found")
    
    try:
        # Run docker-compose down for the extension
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=ext_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {"status": "stopped", "extension": extension_id}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files at the end
app.mount("/", StaticFiles(directory="dist", html=True), name="static")