"""
AI Model Management Module for UC-1 Pro Admin Dashboard
Handles vLLM and Ollama model management with granular settings
"""

import os
import json
import asyncio
import httpx
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Configuration paths (adjusted for container environment)
MODEL_SETTINGS_PATH = "/volumes/model_settings.json"
VLLM_MODELS_DIR = "/volumes/vllm_models"
OLLAMA_MODELS_DIR = "/volumes/ollama_models"
GEMMA_MODEL_DIRS = {
    "gemma3_27b": "/volumes/gemma3_models",
    "gemma3_12b": "/volumes/gemma3_12b_models",
    "gemma3_4b": "/volumes/gemma3_4b_models",
    "gemma3_1b": "/volumes/gemma3_1b_models"
}

# Pydantic models for API requests/responses
class VLLMSettings(BaseModel):
    gpu_memory_utilization: Optional[float] = None
    max_model_len: Optional[int] = None
    tensor_parallel_size: Optional[int] = None
    quantization: Optional[str] = None
    dtype: Optional[str] = None
    trust_remote_code: Optional[bool] = None
    download_dir: Optional[str] = None
    cpu_offload_gb: Optional[int] = None
    enforce_eager: Optional[bool] = None
    max_num_batched_tokens: Optional[int] = None
    max_num_seqs: Optional[int] = None
    disable_log_stats: Optional[bool] = None
    disable_log_requests: Optional[bool] = None

class OllamaSettings(BaseModel):
    models_path: Optional[str] = None
    gpu_layers: Optional[int] = None
    context_size: Optional[int] = None
    num_thread: Optional[int] = None
    use_mmap: Optional[bool] = None
    use_mlock: Optional[bool] = None
    repeat_penalty: Optional[float] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    seed: Optional[int] = None

class ModelSettingsUpdate(BaseModel):
    model_id: str
    backend: str  # 'vllm' or 'ollama'
    settings: Dict[str, Any]

class ModelDownloadRequest(BaseModel):
    model_id: str
    backend: str  # 'vllm' or 'ollama'
    settings: Optional[Dict[str, Any]] = None

class AIModelManager:
    def __init__(self):
        self.settings = self._load_settings()
        self.download_tasks = {}
        
    def _load_settings(self) -> Dict:
        """Load settings from disk"""
        if os.path.exists(MODEL_SETTINGS_PATH):
            try:
                with open(MODEL_SETTINGS_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        
        return {
            "global": {
                "vllm": {
                    "gpu_memory_utilization": 0.95,
                    "max_model_len": 16384,
                    "tensor_parallel_size": 1,
                    "quantization": "auto",
                    "dtype": "auto",
                    "trust_remote_code": False,
                    "download_dir": VLLM_MODELS_DIR,
                    "cpu_offload_gb": 0,
                    "enforce_eager": False,
                    "max_num_batched_tokens": None,
                    "max_num_seqs": 256,
                    "disable_log_stats": False,
                    "disable_log_requests": False
                },
                "ollama": {
                    "models_path": OLLAMA_MODELS_DIR,
                    "gpu_layers": -1,
                    "context_size": 2048,
                    "num_thread": 0,
                    "use_mmap": True,
                    "use_mlock": False,
                    "repeat_penalty": 1.1,
                    "temperature": 0.8,
                    "top_k": 40,
                    "top_p": 0.9,
                    "seed": -1
                }
            },
            "model_overrides": {}
        }
    
    def _save_settings(self):
        """Save settings to disk"""
        try:
            os.makedirs(os.path.dirname(MODEL_SETTINGS_PATH), exist_ok=True)
            with open(MODEL_SETTINGS_PATH, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get_global_settings(self, backend: str) -> Dict:
        """Get global settings for a backend"""
        return self.settings["global"].get(backend, {})
    
    def update_global_settings(self, backend: str, settings: Dict) -> Dict:
        """Update global settings for a backend"""
        if backend not in ["vllm", "ollama"]:
            raise ValueError(f"Invalid backend: {backend}")
        
        # Update only provided settings
        for key, value in settings.items():
            if value is not None:
                self.settings["global"][backend][key] = value
        
        self._save_settings()
        return self.settings["global"][backend]
    
    def get_model_settings(self, model_id: str, backend: str) -> Dict:
        """Get effective settings for a model (global + overrides)"""
        global_settings = self.settings["global"].get(backend, {})
        overrides = self.settings["model_overrides"].get(f"{backend}:{model_id}", {})
        
        # Merge settings
        effective_settings = global_settings.copy()
        effective_settings.update(overrides)
        
        return {
            "global": global_settings,
            "overrides": overrides,
            "effective": effective_settings
        }
    
    def update_model_settings(self, model_id: str, backend: str, settings: Dict) -> Dict:
        """Update model-specific settings overrides"""
        key = f"{backend}:{model_id}"
        
        # Filter out None values and empty settings
        filtered_settings = {k: v for k, v in settings.items() if v is not None}
        
        if filtered_settings:
            self.settings["model_overrides"][key] = filtered_settings
        else:
            # Remove overrides if all are cleared
            self.settings["model_overrides"].pop(key, None)
        
        self._save_settings()
        return self.get_model_settings(model_id, backend)
    
    async def scan_local_models(self) -> Dict[str, List[Dict]]:
        """Scan for locally installed models"""
        models = {"vllm": [], "ollama": [], "embeddings": [], "reranker": []}
        
        # Scan vLLM models directory
        if os.path.exists(VLLM_MODELS_DIR):
            for model_dir in Path(VLLM_MODELS_DIR).iterdir():
                if model_dir.is_dir() and not model_dir.name.startswith('.'):
                    # Handle both simple directory structure and HuggingFace cache structure
                    if model_dir.name.startswith("models--"):
                        # HuggingFace cache format: models--Qwen--Qwen2.5-32B-Instruct-AWQ
                        model_name = model_dir.name.replace("models--", "").replace("--", "/")
                        display_name = model_name
                    else:
                        # Simple directory structure
                        model_name = model_dir.name
                        display_name = model_name
                    
                    # Check if this is the active model
                    is_active = False
                    try:
                        env_path = "/home/ucadmin/UC-1-Pro/.env"
                        if os.path.exists(env_path):
                            with open(env_path, 'r') as f:
                                for line in f:
                                    if line.startswith('DEFAULT_LLM_MODEL='):
                                        active_model = line.strip().split('=', 1)[1].strip('"')
                                        is_active = (model_name == active_model)
                                        break
                    except Exception:
                        pass
                    
                    model_info = {
                        "id": model_name,
                        "name": display_name,
                        "path": str(model_dir),
                        "size": self._get_dir_size(model_dir),
                        "last_modified": datetime.fromtimestamp(model_dir.stat().st_mtime).isoformat(),
                        "has_overrides": f"vllm:{model_name}" in self.settings.get("model_overrides", {}),
                        "active": is_active
                    }
                    models["vllm"].append(model_info)
        
        # Scan Gemma model directories - Updated Sept 2025 with latest compatibility
        gemma_models = {
            # Working quantized models with vLLM 0.8.0+
            "RedHatAI/gemma-3-12b-it-quantized.w8a8": ("gemma3_12b_int8", "Gemma 3 12B IT (INT8)"),
            "gaunernst/gemma-3-27b-it-int4-awq": ("gemma3_27b", "Gemma 3 27B IT (AWQ)"),
            "gaunernst/gemma-3-12b-it-int4-awq": ("gemma3_12b", "Gemma 3 12B IT (AWQ)"),
            "RedHatAI/gemma-3-4b-it-quantized.w4a16": ("gemma3_4b", "Gemma 3 4B IT (W4A16)"),
            "gaunernst/gemma-3-1b-it-int4-awq": ("gemma3_1b", "Gemma 3 1B IT (AWQ)"),
            # GPTQModel versions (requires main branch vLLM + Transformers ≥ 4.50)
            "MaziyarPanahi/gemma-3-27b-it-GPTQ": ("gemma3_27b_gptq", "Gemma 3 27B IT (GPTQ)"),
            "MaziyarPanahi/gemma-3-12b-it-GPTQ": ("gemma3_12b_gptq", "Gemma 3 12B IT (GPTQ)")
        }
        
        for model_id, (dir_key, display_name) in gemma_models.items():
            model_path = GEMMA_MODEL_DIRS.get(dir_key)
            if model_path and os.path.exists(model_path):
                path_obj = Path(model_path)
                # Check if there are actual model files (not just lock files)
                has_model_files = any(
                    f.suffix in ['.safetensors', '.bin', '.pt', '.pth', '.json'] 
                    for f in path_obj.rglob('*') if f.is_file()
                )
                
                if has_model_files:
                    models["vllm"].append({
                        "id": model_id,
                        "name": display_name,
                        "path": model_path,
                        "size": self._get_dir_size(path_obj),
                        "last_modified": datetime.fromtimestamp(path_obj.stat().st_mtime).isoformat(),
                        "has_overrides": f"vllm:{model_id}" in self.settings.get("model_overrides", {}),
                        "active": False,
                        "gemma_model": True
                    })
        
        # Get Ollama models via API (with timeout)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://unicorn-ollama:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("models", []):
                        model_info = {
                            "id": model["name"],
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "last_modified": model.get("modified_at"),
                            "has_overrides": f"ollama:{model['name']}" in self.settings.get("model_overrides", {})
                        }
                        models["ollama"].append(model_info)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.info(f"Ollama service not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
        
        # Get Embeddings models via service API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://unicorn-embeddings:8082/model/cached")
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("cached_models", []):
                        models["embeddings"].append({
                            "id": model["name"],
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "path": model.get("path", ""),
                            "active": model.get("active", False)
                        })
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.info(f"Embeddings service not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch Embeddings models: {e}")
        
        # Get Reranker models via service API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://unicorn-reranker:8083/model/cached")
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("cached_models", []):
                        models["reranker"].append({
                            "id": model["name"],
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "path": model.get("path", ""),
                            "active": model.get("active", False)
                        })
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.info(f"Reranker service not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch Reranker models: {e}")
        
        return models
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of a directory"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    async def download_vllm_model(self, model_id: str, settings: Optional[Dict] = None) -> str:
        """Download a vLLM model from Hugging Face - unified manager aware"""
        # Try unified manager first if available
        unified_manager_url = "http://unicorn-vllm:8000"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if unified manager is running
                health_response = await client.get(f"{unified_manager_url}/health")
                
                if health_response.status_code == 200:
                    # Use unified manager for download
                    response = await client.post(
                        f"{unified_manager_url}/v1/models/download",
                        json={
                            "model_id": model_id,
                            "quantization": settings.get("quantization") if settings else None,
                            "max_model_len": settings.get("max_model_len", 16384) if settings else 16384
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        task_id = data["task_id"]
                        
                        self.download_tasks[task_id] = {
                            "model_id": model_id,
                            "status": "downloading",
                            "progress": 0,
                            "started_at": datetime.now().isoformat(),
                            "unified_manager": True
                        }
                        
                        # Monitor unified manager download status
                        asyncio.create_task(self._monitor_unified_download(task_id, model_id))
                        return task_id
                        
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.info("Unified manager not available, using traditional download")
        
        # Fallback to traditional download
        task_id = f"vllm:{model_id}:{datetime.now().timestamp()}"
        
        # Get effective settings
        effective_settings = self.get_global_settings("vllm")
        if settings:
            effective_settings.update(settings)
        
        # Create download directory
        model_path = os.path.join(VLLM_MODELS_DIR, model_id.replace("/", "--"))
        os.makedirs(model_path, exist_ok=True)
        
        # Build huggingface-cli command
        cmd = [
            "huggingface-cli", "download",
            model_id,
            "--local-dir", model_path,
            "--local-dir-use-symlinks", "False"
        ]
        
        # Add token if available
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            cmd.extend(["--token", hf_token])
        
        # Start download process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.download_tasks[task_id] = {
            "process": process,
            "model_id": model_id,
            "status": "downloading",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "unified_manager": False
        }
        
        # Monitor download in background
        asyncio.create_task(self._monitor_download(task_id, process))
        
        return task_id
    
    async def _monitor_unified_download(self, task_id: str, model_id: str):
        """Monitor download progress from unified manager"""
        unified_manager_url = "http://unicorn-vllm:8000"
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                while True:
                    response = await client.get(f"{unified_manager_url}/v1/models/downloads")
                    
                    if response.status_code == 200:
                        downloads = response.json()
                        
                        if task_id in downloads:
                            task_data = downloads[task_id]
                            self.download_tasks[task_id]["progress"] = task_data.get("progress", 0)
                            self.download_tasks[task_id]["status"] = task_data.get("status", "downloading")
                            
                            if task_data["status"] in ["completed", "failed"]:
                                break
                    
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Error monitoring unified download: {e}")
            self.download_tasks[task_id]["status"] = "failed"
            self.download_tasks[task_id]["error"] = str(e)
    
    async def download_ollama_model(self, model_name: str) -> str:
        """Download an Ollama model"""
        task_id = f"ollama:{model_name}:{datetime.now().timestamp()}"
        
        # Use Ollama API to pull model
        async with httpx.AsyncClient(timeout=None) as client:
            # Start pull request
            response = await client.post(
                "http://localhost:11434/api/pull",
                json={"name": model_name},
                timeout=None
            )
            
            self.download_tasks[task_id] = {
                "model_id": model_name,
                "status": "downloading",
                "progress": 0,
                "started_at": datetime.now().isoformat()
            }
            
            # Process streaming response
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "completed" in data and "total" in data:
                            progress = (data["completed"] / data["total"]) * 100
                            self.download_tasks[task_id]["progress"] = progress
                        
                        if data.get("status") == "success":
                            self.download_tasks[task_id]["status"] = "completed"
                            self.download_tasks[task_id]["progress"] = 100
                    except json.JSONDecodeError:
                        pass
        
        return task_id
    
    async def _monitor_download(self, task_id: str, process):
        """Monitor vLLM download progress"""
        try:
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.download_tasks[task_id]["status"] = "completed"
                self.download_tasks[task_id]["progress"] = 100
            else:
                self.download_tasks[task_id]["status"] = "failed"
                self.download_tasks[task_id]["error"] = stderr.decode()
        except Exception as e:
            self.download_tasks[task_id]["status"] = "failed"
            self.download_tasks[task_id]["error"] = str(e)
    
    def get_download_status(self, task_id: str) -> Optional[Dict]:
        """Get download task status"""
        return self.download_tasks.get(task_id)
    
    def get_all_downloads(self) -> Dict[str, Dict]:
        """Get all download tasks"""
        return self.download_tasks
    
    async def activate_vllm_model(self, model_id: str) -> Dict:
        """Activate a vLLM model using the unified manager for fast switching"""
        try:
            # Check if unified manager is available
            unified_manager_url = "http://unicorn-vllm:8000"  # Unified vLLM manager on standard port
            
            try:
                # Try to use unified manager first for fast switching
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Switch model via unified manager
                    response = await client.post(
                        f"{unified_manager_url}/v1/models/switch",
                        json={"model_id": model_id}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": "activated",
                            "model_id": model_id,
                            "message": data.get("message", f"Successfully activated {model_id} via unified manager"),
                            "port": data.get("port", 8000),
                            "unified_manager": True
                        }
            except (httpx.ConnectError, httpx.TimeoutException):
                logger.info("Unified manager not available, falling back to traditional method")
            
            # Fallback to traditional method if unified manager not available
            # Check if model exists
            model_found = False
            for model_dir in Path(VLLM_MODELS_DIR).iterdir():
                if model_dir.is_dir():
                    if model_dir.name.startswith("models--"):
                        check_name = model_dir.name.replace("models--", "").replace("--", "/")
                    else:
                        check_name = model_dir.name
                    
                    if check_name == model_id:
                        model_found = True
                        break
            
            if not model_found:
                raise FileNotFoundError(f"Model not found: {model_id}")
            
            # Update .env file with new model
            env_path = "/home/ucadmin/UC-1-Pro/.env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Update DEFAULT_LLM_MODEL
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('DEFAULT_LLM_MODEL='):
                        lines[i] = f'DEFAULT_LLM_MODEL={model_id}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'DEFAULT_LLM_MODEL={model_id}\n')
                
                with open(env_path, 'w') as f:
                    f.writelines(lines)
            
            # Restart vLLM container
            result = subprocess.run(
                ["docker", "restart", "unicorn-vllm"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "status": "activated",
                    "model_id": model_id,
                    "message": f"Successfully activated {model_id}. vLLM service is restarting.",
                    "unified_manager": False
                }
            else:
                raise Exception(f"Failed to restart vLLM: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Failed to activate model {model_id}: {e}")
            return {
                "status": "error",
                "model_id": model_id,
                "message": str(e)
            }
    
    async def delete_model(self, model_id: str, backend: str) -> Dict:
        """Delete a model"""
        if backend == "vllm":
            # Find the model directory
            model_deleted = False
            import shutil
            
            for model_dir in Path(VLLM_MODELS_DIR).iterdir():
                if model_dir.is_dir():
                    if model_dir.name.startswith("models--"):
                        check_name = model_dir.name.replace("models--", "").replace("--", "/")
                    else:
                        check_name = model_dir.name
                    
                    if check_name == model_id:
                        shutil.rmtree(str(model_dir))
                        model_deleted = True
                        break
            
            if model_deleted:
                return {"status": "deleted", "model_id": model_id}
            else:
                raise FileNotFoundError(f"Model not found: {model_id}")
        
        elif backend == "ollama":
            # Use Ollama CLI to delete
            try:
                result = subprocess.run(
                    ["docker", "exec", "unicorn-ollama", "ollama", "rm", model_id],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 or "deleted" in result.stdout.lower():
                    return {"status": "deleted", "model_id": model_id}
                else:
                    raise Exception(f"Failed to delete Ollama model: {result.stderr}")
            except Exception as e:
                logger.error(f"Failed to delete Ollama model {model_id}: {e}")
                raise
        
        else:
            raise ValueError(f"Invalid backend: {backend}")

# Create singleton instance
ai_model_manager = AIModelManager()