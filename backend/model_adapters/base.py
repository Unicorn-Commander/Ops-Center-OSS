"""
Base Server Adapter for Model Management
Provides abstract interface for different model server types
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
import aiohttp
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    """Model information structure"""
    id: str
    name: str
    size: Optional[int] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    loaded: bool = False
    metadata: Dict[str, Any] = {}

class ServerMetrics(BaseModel):
    """Server resource metrics"""
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_memory_used: Optional[int] = None
    gpu_memory_total: Optional[int] = None
    active_requests: Optional[int] = None
    total_requests: Optional[int] = None
    avg_response_time: Optional[float] = None
    timestamp: datetime = datetime.now()

class ServerAdapter(ABC):
    """Base adapter class for all model servers"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers including auth if configured"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if server is reachable and authenticated"""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """Get list of available models"""
        pass

    @abstractmethod
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed information about a specific model"""
        pass

    @abstractmethod
    async def load_model(self, model_id: str, **kwargs) -> bool:
        """Load a model into memory"""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        pass

    @abstractmethod
    async def get_metrics(self) -> ServerMetrics:
        """Get server resource metrics"""
        pass

    async def pull_model(self, model_name: str, **kwargs) -> AsyncIterator[str]:
        """Pull/download a model (optional, not all servers support this)"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support model pulling")

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model from server storage (optional)"""
        raise NotImplementedError(f"{self.__class__.__name__} does not support model deletion")

    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse Prometheus format metrics"""
        metrics = {}
        lines = metrics_text.split('\n')
        for line in lines:
            if line and not line.startswith('#'):
                parts = line.split(' ')
                if len(parts) == 2:
                    key, value = parts
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
        return metrics