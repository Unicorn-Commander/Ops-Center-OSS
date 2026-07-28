"""
Ollama Server Adapter
Handles communication with Ollama servers
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import aiohttp
import json
import logging
from .base import ServerAdapter, ModelInfo, ServerMetrics

logger = logging.getLogger(__name__)

class OllamaAdapter(ServerAdapter):
    """Adapter for Ollama servers"""

    async def test_connection(self) -> bool:
        """Test connection to Ollama server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/api/tags',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List available models on Ollama server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.base_url}/api/tags') as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to list Ollama models: {resp.status}")
                        return []

                    data = await resp.json()
                    models = []

                    # Get list of running models
                    running_models = await self._get_running_models()

                    for model in data.get('models', []):
                        model_name = model.get('name', '')
                        models.append(ModelInfo(
                            id=model_name,
                            name=model_name,
                            size=model.get('size'),
                            quantization=self._extract_quantization(model_name),
                            loaded=model_name in running_models,
                            metadata=model
                        ))
                    return models
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def _get_running_models(self) -> List[str]:
        """Get list of currently running models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.base_url}/api/ps') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m.get('name', '') for m in data.get('models', [])]
        except:
            pass
        return []

    def _extract_quantization(self, model_name: str) -> Optional[str]:
        """Extract quantization info from model name"""
        # Ollama models often have quantization in name like "llama2:7b-q4_0"
        if ':' in model_name:
            parts = model_name.split(':')
            if len(parts) > 1:
                variant = parts[1]
                if 'q4' in variant.lower():
                    return 'q4'
                elif 'q5' in variant.lower():
                    return 'q5'
                elif 'q8' in variant.lower():
                    return 'q8'
        return None

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed information about a specific model"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/api/show',
                    json={"name": model_id}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        running = await self._get_running_models()
                        return ModelInfo(
                            id=model_id,
                            name=model_id,
                            loaded=model_id in running,
                            metadata=data
                        )
        except Exception as e:
            logger.error(f"Error getting Ollama model info: {e}")

        return ModelInfo(id=model_id, name=model_id, loaded=False)

    async def load_model(self, model_id: str, **kwargs) -> bool:
        """Load a model into Ollama memory"""
        try:
            async with aiohttp.ClientSession() as session:
                # Generate a simple prompt to load the model
                async with session.post(
                    f'{self.base_url}/api/generate',
                    json={
                        "model": model_id,
                        "prompt": "test",
                        "stream": False,
                        "options": {"num_predict": 1}
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Error loading Ollama model {model_id}: {e}")
            return False

    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from Ollama memory.
        Note: Ollama doesn't have a direct unload API, models are unloaded based on LRU.
        """
        logger.info(f"Ollama model unloading requested for {model_id} - uses LRU eviction")
        return True  # Ollama handles this automatically

    async def pull_model(self, model_name: str, **kwargs) -> AsyncIterator[str]:
        """Pull a model from Ollama registry with progress updates"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/api/pull',
                    json={'name': model_name, 'stream': True}
                ) as resp:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                status = data.get('status', '')

                                # Format progress message
                                if 'completed' in data and 'total' in data:
                                    percent = (data['completed'] / data['total']) * 100
                                    yield f"{status}: {percent:.1f}%"
                                else:
                                    yield status
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Error pulling Ollama model {model_name}: {e}")
            yield f"Error: {str(e)}"

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f'{self.base_url}/api/delete',
                    json={"name": model_id}
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Error deleting Ollama model {model_id}: {e}")
            return False

    async def get_metrics(self) -> ServerMetrics:
        """Get server metrics from Ollama"""
        metrics = ServerMetrics()

        try:
            # Get running models for basic metrics
            running = await self._get_running_models()
            metrics.active_requests = len(running)
            metrics.metadata = {"running_models": running}

            # Try to get more detailed info if available
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.base_url}/api/ps') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models_info = data.get('models', [])
                        if models_info:
                            # Calculate approximate memory usage
                            total_size = sum(m.get('size', 0) for m in models_info)
                            metrics.gpu_memory_used = total_size

        except Exception as e:
            logger.error(f"Error getting Ollama metrics: {e}")

        return metrics

    async def check_health(self) -> Dict[str, Any]:
        """Check health status of Ollama server"""
        health = {
            "status": "unknown",
            "models_available": 0,
            "models_running": 0,
            "endpoint_responsive": False
        }

        try:
            # Check if server responds
            models = await self.list_models()
            running = await self._get_running_models()

            if models is not None:
                health["status"] = "online"
                health["models_available"] = len(models)
                health["models_running"] = len(running)
                health["endpoint_responsive"] = True
            else:
                health["status"] = "offline"
        except:
            health["status"] = "offline"

        return health