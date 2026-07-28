"""
Model Management API for Ops-Center
Exposes ai_model_manager functionality via FastAPI endpoints
Supports vLLM, Ollama, Embeddings, and Reranker model management
"""

import os
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ai_model_manager import ai_model_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["Model Management"])


# ============================================================================
# Pydantic Models for Request/Response Validation
# ============================================================================

class ModelSearchResult(BaseModel):
    """HuggingFace model search result"""
    id: str
    name: str
    description: Optional[str] = None
    downloads: Optional[int] = 0
    likes: Optional[int] = 0
    tags: List[str] = []
    task: Optional[str] = None
    library_name: Optional[str] = None
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    author: Optional[str] = None
    vllm_ready: bool = False
    quantization: Optional[str] = None


class ModelDownloadRequest(BaseModel):
    """Request to download a model"""
    model_id: str = Field(..., description="HuggingFace model ID (e.g., 'Qwen/Qwen2.5-32B-Instruct-AWQ')")
    backend: str = Field("vllm", description="Backend to download for: vllm, ollama, embeddings, reranker")
    settings: Optional[Dict[str, Any]] = Field(None, description="Model-specific settings")


class ModelActivateRequest(BaseModel):
    """Request to activate a model"""
    model_id: str = Field(..., description="Model ID to activate")
    backend: str = Field("vllm", description="Backend: vllm or ollama")


class ModelSettingsUpdate(BaseModel):
    """Request to update model settings"""
    model_id: str
    backend: str
    settings: Dict[str, Any] = Field(..., description="Settings to update")


class ModelListResponse(BaseModel):
    """Response with list of models"""
    vllm: List[Dict[str, Any]] = []
    ollama: List[Dict[str, Any]] = []
    embeddings: List[Dict[str, Any]] = []
    reranker: List[Dict[str, Any]] = []


class ModelDownloadStatus(BaseModel):
    """Download task status"""
    task_id: str
    model_id: str
    status: str = Field(..., description="downloading, completed, failed")
    progress: int = Field(0, ge=0, le=100)
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    unified_manager: bool = False


class ModelDeleteResponse(BaseModel):
    """Response after deleting a model"""
    status: str = "deleted"
    model_id: str
    backend: str
    message: Optional[str] = None


class ModelActivateResponse(BaseModel):
    """Response after activating a model"""
    status: str
    model_id: str
    message: str
    port: Optional[int] = None
    unified_manager: bool = False


# ============================================================================
# Helper Functions
# ============================================================================

async def search_huggingface_models(query: str, limit: int = 20, task_filter: str = None) -> List[Dict]:
    """
    Search HuggingFace for models

    Args:
        query: Search query string
        limit: Max number of results
        task_filter: Optional task filter (text-generation, feature-extraction, etc.)

    Returns:
        List of model dictionaries
    """
    try:
        # Build HuggingFace API URL
        base_url = "https://huggingface.co/api/models"
        params = {
            "search": query,
            "limit": limit,
            "sort": "downloads",
            "direction": -1
        }

        # Add task filter if specified
        if task_filter:
            params["filter"] = task_filter

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url, params=params)

            if response.status_code != 200:
                logger.error(f"HuggingFace API error: {response.status_code}")
                return []

            models = response.json()

            # Transform to our format
            results = []
            for model in models:
                # Determine if model is vLLM-ready based on tags
                tags = model.get("tags", [])
                vllm_ready = any(tag in tags for tag in ["awq", "gptq", "gguf", "exl2"])

                # Determine quantization type
                quantization = None
                if "awq" in tags:
                    quantization = "AWQ (4-bit)"
                elif "gptq" in tags:
                    quantization = "GPTQ (4-bit)"
                elif "gguf" in tags:
                    quantization = "GGUF"
                elif "exl2" in tags:
                    quantization = "EXL2"

                results.append({
                    "id": model["modelId"],
                    "name": model.get("modelId", "").split("/")[-1],
                    "description": model.get("description", ""),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "tags": tags,
                    "task": model.get("pipeline_tag"),
                    "library_name": model.get("library_name"),
                    "created_at": model.get("createdAt"),
                    "last_modified": model.get("lastModified"),
                    "author": model.get("author"),
                    "vllm_ready": vllm_ready,
                    "quantization": quantization
                })

            return results

    except Exception as e:
        logger.error(f"Error searching HuggingFace: {e}")
        return []


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/search", response_model=List[ModelSearchResult])
async def search_models(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    task: Optional[str] = Query(None, description="Filter by task (text-generation, feature-extraction, etc.)")
):
    """
    Search HuggingFace for models

    **Example**:
    ```
    GET /api/v1/models/search?q=llama&limit=10&task=text-generation
    ```

    **Supported Tasks**:
    - text-generation (LLM models)
    - feature-extraction (Embedding models)
    - sentence-similarity (Reranker models)
    - text2text-generation
    - translation
    - summarization
    """
    try:
        results = await search_huggingface_models(q, limit, task)
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/download", response_model=ModelDownloadStatus)
async def download_model(
    request: ModelDownloadRequest,
    background_tasks: BackgroundTasks
):
    """
    Download a model from HuggingFace

    **Backends**:
    - `vllm`: Download for vLLM inference
    - `ollama`: Pull via Ollama API
    - `embeddings`: Download for embedding service
    - `reranker`: Download for reranker service

    **Example**:
    ```json
    {
      "model_id": "Qwen/Qwen2.5-32B-Instruct-AWQ",
      "backend": "vllm",
      "settings": {
        "quantization": "awq",
        "max_model_len": 16384
      }
    }
    ```

    **Returns**: Task ID to track download progress
    """
    try:
        if request.backend == "vllm":
            task_id = await ai_model_manager.download_vllm_model(
                model_id=request.model_id,
                settings=request.settings or {}
            )
        elif request.backend == "ollama":
            task_id = await ai_model_manager.download_ollama_model(
                model_name=request.model_id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported backend: {request.backend}. Use 'vllm' or 'ollama'"
            )

        # Get initial status
        status = ai_model_manager.get_download_status(task_id)
        if not status:
            raise HTTPException(status_code=500, detail="Failed to start download")

        return ModelDownloadStatus(
            task_id=task_id,
            model_id=request.model_id,
            status=status["status"],
            progress=status.get("progress", 0),
            started_at=status["started_at"],
            unified_manager=status.get("unified_manager", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/downloads", response_model=Dict[str, ModelDownloadStatus])
async def get_all_downloads():
    """
    Get status of all download tasks

    **Returns**: Dictionary of task_id -> download status
    """
    try:
        downloads = ai_model_manager.get_all_downloads()

        # Convert to response model
        result = {}
        for task_id, status in downloads.items():
            result[task_id] = ModelDownloadStatus(
                task_id=task_id,
                model_id=status["model_id"],
                status=status["status"],
                progress=status.get("progress", 0),
                started_at=status["started_at"],
                error=status.get("error"),
                unified_manager=status.get("unified_manager", False)
            )

        return result

    except Exception as e:
        logger.error(f"Error fetching downloads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch downloads: {str(e)}")


@router.get("/downloads/{task_id}", response_model=ModelDownloadStatus)
async def get_download_status(task_id: str):
    """
    Get status of a specific download task

    **Example**:
    ```
    GET /api/v1/models/downloads/vllm:Qwen/Qwen2.5-32B-Instruct-AWQ:1729123456.789
    ```
    """
    try:
        status = ai_model_manager.get_download_status(task_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Download task not found: {task_id}")

        return ModelDownloadStatus(
            task_id=task_id,
            model_id=status["model_id"],
            status=status["status"],
            progress=status.get("progress", 0),
            started_at=status["started_at"],
            completed_at=status.get("completed_at"),
            error=status.get("error"),
            unified_manager=status.get("unified_manager", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching download status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")


@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...),
    backend: str = Query("vllm", description="Backend: vllm or ollama"),
    model_name: Optional[str] = Query(None, description="Custom model name")
):
    """
    Upload a custom model file

    **Supported Formats**:
    - GGUF (Ollama/vLLM)
    - SafeTensors (vLLM)
    - BIN (vLLM)
    - PTH (vLLM)

    **Example**:
    ```
    POST /api/v1/models/upload?backend=vllm&model_name=custom-llama
    Content-Type: multipart/form-data

    file: <binary data>
    ```
    """
    try:
        # Validate file extension
        valid_extensions = {".gguf", ".bin", ".safetensors", ".pth", ".pt"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Use one of: {', '.join(valid_extensions)}"
            )

        # Determine save path
        if backend == "vllm":
            from ai_model_manager import VLLM_MODELS_DIR
            model_dir = Path(VLLM_MODELS_DIR) / (model_name or file.filename)
        elif backend == "ollama":
            from ai_model_manager import OLLAMA_MODELS_DIR
            model_dir = Path(OLLAMA_MODELS_DIR) / (model_name or file.filename)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported backend: {backend}")

        # Create directory
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = model_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Format file size
        size = len(content)
        size_formatted = format_file_size(size)

        return {
            "status": "uploaded",
            "model_name": model_name or file.filename,
            "backend": backend,
            "file_path": str(file_path),
            "file_size": size,
            "file_size_formatted": size_formatted,
            "message": f"Successfully uploaded {file.filename} ({size_formatted})"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/{backend}/{model_id:path}", response_model=ModelDeleteResponse)
async def delete_model(backend: str, model_id: str):
    """
    Delete a model

    **Backends**: vllm, ollama, embeddings, reranker

    **Example**:
    ```
    DELETE /api/v1/models/vllm/Qwen/Qwen2.5-32B-Instruct-AWQ
    ```

    **Note**: Use URL encoding for model IDs with slashes
    """
    try:
        if backend not in ["vllm", "ollama", "embeddings", "reranker"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        result = await ai_model_manager.delete_model(model_id, backend)

        return ModelDeleteResponse(
            status=result["status"],
            model_id=model_id,
            backend=backend,
            message=f"Successfully deleted {model_id} from {backend}"
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.post("/{backend}/{model_id:path}/activate", response_model=ModelActivateResponse)
async def activate_model(backend: str, model_id: str):
    """
    Activate a model (set as default/active)

    **vLLM**: Updates .env and restarts vLLM container (or fast-switches via unified manager)
    **Ollama**: Sets model as default in Ollama

    **Example**:
    ```
    POST /api/v1/models/vllm/Qwen/Qwen2.5-32B-Instruct-AWQ/activate
    ```

    **Note**: vLLM activation may take 30-60 seconds for container restart
    """
    try:
        if backend == "vllm":
            result = await ai_model_manager.activate_vllm_model(model_id)
        elif backend == "ollama":
            # Ollama doesn't have an explicit "activate" - just use the model
            result = {
                "status": "activated",
                "model_id": model_id,
                "message": f"Model {model_id} is ready to use. Reference it in your requests.",
                "unified_manager": False
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Activation not supported for backend: {backend}"
            )

        return ModelActivateResponse(
            status=result["status"],
            model_id=model_id,
            message=result["message"],
            port=result.get("port"),
            unified_manager=result.get("unified_manager", False)
        )

    except Exception as e:
        logger.error(f"Activation error: {e}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@router.get("/installed", response_model=Dict[str, List[Dict[str, Any]]])
async def get_installed_models():
    """
    Get all installed models for all backends

    **Example**:
    ```
    GET /api/v1/models/installed
    ```

    **Returns**: Dictionary with backend keys (vllm, ollama, embeddings, reranker)
    containing lists of model objects
    """
    try:
        models = await ai_model_manager.scan_local_models()
        return models
    except Exception as e:
        logger.error(f"Error scanning installed models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan installed models: {str(e)}")


@router.get("/{backend}", response_model=List[Dict[str, Any]])
async def list_models_by_backend(backend: str):
    """
    List all models for a specific backend

    **Backends**: vllm, ollama, embeddings, reranker

    **Example**:
    ```
    GET /api/v1/models/vllm
    ```

    **Returns**: List of model objects with metadata
    """
    try:
        if backend not in ["vllm", "ollama", "embeddings", "reranker"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        all_models = await ai_model_manager.scan_local_models()

        models = all_models.get(backend, [])

        # Add formatted file sizes
        for model in models:
            if "size" in model:
                model["size_formatted"] = format_file_size(model["size"])

        return models

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/", response_model=ModelListResponse)
async def list_all_models():
    """
    List all installed models across all backends

    **Returns**:
    ```json
    {
      "vllm": [...],
      "ollama": [...],
      "embeddings": [...],
      "reranker": [...]
    }
    ```
    """
    try:
        models = await ai_model_manager.scan_local_models()

        # Add formatted file sizes
        for backend_models in models.values():
            for model in backend_models:
                if "size" in model:
                    model["size_formatted"] = format_file_size(model["size"])

        return ModelListResponse(**models)

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/settings/global/{backend}")
async def get_global_settings(backend: str):
    """
    Get global settings for a backend

    **Example**:
    ```
    GET /api/v1/models/settings/global/vllm
    ```
    """
    try:
        if backend not in ["vllm", "ollama"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        settings = ai_model_manager.get_global_settings(backend)
        return {"backend": backend, "settings": settings}

    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


@router.put("/settings/global/{backend}")
async def update_global_settings(backend: str, settings: Dict[str, Any]):
    """
    Update global settings for a backend

    **Example**:
    ```json
    PUT /api/v1/models/settings/global/vllm
    {
      "gpu_memory_utilization": 0.90,
      "max_model_len": 32768,
      "tensor_parallel_size": 2
    }
    ```
    """
    try:
        if backend not in ["vllm", "ollama"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        updated_settings = ai_model_manager.update_global_settings(backend, settings)

        return {
            "backend": backend,
            "settings": updated_settings,
            "message": f"Successfully updated {backend} global settings"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/settings/{backend}/{model_id:path}")
async def get_model_settings(backend: str, model_id: str):
    """
    Get effective settings for a model (global + overrides)

    **Returns**:
    ```json
    {
      "global": {...},      // Global backend settings
      "overrides": {...},   // Model-specific overrides
      "effective": {...}    // Merged effective settings
    }
    ```
    """
    try:
        if backend not in ["vllm", "ollama"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        settings = ai_model_manager.get_model_settings(model_id, backend)

        return {
            "backend": backend,
            "model_id": model_id,
            **settings
        }

    except Exception as e:
        logger.error(f"Error fetching model settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


@router.put("/settings/{backend}/{model_id:path}")
async def update_model_settings(backend: str, model_id: str, settings: Dict[str, Any]):
    """
    Update model-specific settings overrides

    **Example**:
    ```json
    PUT /api/v1/models/settings/vllm/Qwen/Qwen2.5-32B-Instruct-AWQ
    {
      "max_model_len": 8192,
      "gpu_memory_utilization": 0.85
    }
    ```

    **Note**: Pass `null` values to clear overrides
    """
    try:
        if backend not in ["vllm", "ollama"]:
            raise HTTPException(status_code=400, detail=f"Invalid backend: {backend}")

        updated_settings = ai_model_manager.update_model_settings(model_id, backend, settings)

        return {
            "backend": backend,
            "model_id": model_id,
            **updated_settings,
            "message": f"Successfully updated settings for {model_id}"
        }

    except Exception as e:
        logger.error(f"Error updating model settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    **Returns**: Service status and statistics
    """
    try:
        models = await ai_model_manager.scan_local_models()

        total_models = sum(len(m) for m in models.values())
        downloads = ai_model_manager.get_all_downloads()
        active_downloads = sum(1 for d in downloads.values() if d["status"] == "downloading")

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_models": total_models,
                "vllm_models": len(models.get("vllm", [])),
                "ollama_models": len(models.get("ollama", [])),
                "embedding_models": len(models.get("embeddings", [])),
                "reranker_models": len(models.get("reranker", [])),
                "active_downloads": active_downloads,
                "total_downloads": len(downloads)
            }
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# ============================================================================
# Export Router
# ============================================================================

# Router is ready to be included in main FastAPI app:
# app.include_router(router)
