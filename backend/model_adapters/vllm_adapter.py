"""
vLLM Server Adapter
Handles communication with vLLM servers using OpenAI-compatible API
"""

from typing import List, Dict, Any, Optional
import aiohttp
import logging
from .base import ServerAdapter, ModelInfo, ServerMetrics

logger = logging.getLogger(__name__)

class VLLMAdapter(ServerAdapter):
    """Adapter for vLLM servers (OpenAI-compatible API)"""

    async def test_connection(self) -> bool:
        """Test connection to vLLM server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/v1/models',
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"vLLM connection test failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List available models on vLLM server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/v1/models',
                    headers=self._get_headers()
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to list vLLM models: {resp.status}")
                        return []

                    data = await resp.json()
                    models = []
                    for model in data.get('data', []):
                        models.append(ModelInfo(
                            id=model.get('id', ''),
                            name=model.get('id', ''),
                            loaded=True,  # vLLM models are loaded if listed
                            metadata=model
                        ))
                    return models
        except Exception as e:
            logger.error(f"Error listing vLLM models: {e}")
            return []

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed information about a specific model"""
        models = await self.list_models()
        for model in models:
            if model.id == model_id:
                return model

        # Model not found, return basic info
        return ModelInfo(
            id=model_id,
            name=model_id,
            loaded=False
        )

    async def load_model(self, model_id: str, **kwargs) -> bool:
        """
        Load a model into vLLM.
        Note: vLLM typically loads models at server startup,
        so this would require server restart or dynamic loading if supported.
        """
        # vLLM doesn't support dynamic model loading in the standard API
        # This would require custom implementation or server restart
        logger.info(f"vLLM model loading requested for {model_id} - requires server configuration")
        return False

    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from vLLM.
        Note: vLLM doesn't support dynamic unloading in standard API.
        """
        logger.info(f"vLLM model unloading requested for {model_id} - not supported")
        return False

    async def get_metrics(self) -> ServerMetrics:
        """Get server metrics from vLLM"""
        metrics = ServerMetrics()

        try:
            # Try to get metrics from /metrics endpoint (Prometheus format)
            async with aiohttp.ClientSession() as session:
                # Try metrics endpoint
                try:
                    async with session.get(
                        f'{self.base_url}/metrics',
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            metrics_text = await resp.text()
                            parsed = self._parse_prometheus_metrics(metrics_text)

                            # Extract relevant metrics
                            if 'vllm:num_requests_running' in parsed:
                                metrics.active_requests = int(parsed['vllm:num_requests_running'])
                            if 'vllm:num_requests_finished' in parsed:
                                metrics.total_requests = int(parsed['vllm:num_requests_finished'])
                            if 'vllm:gpu_cache_usage_perc' in parsed:
                                metrics.gpu_percent = float(parsed['vllm:gpu_cache_usage_perc']) * 100
                except:
                    pass  # Metrics endpoint not available

                # Try to get model info for additional details
                try:
                    async with session.get(
                        f'{self.base_url}/v1/models',
                        headers=self._get_headers(),
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Model is loaded if we get a response
                            if data.get('data'):
                                metrics.metadata = {"loaded_models": len(data.get('data', []))}
                except:
                    pass

        except Exception as e:
            logger.error(f"Error getting vLLM metrics: {e}")

        return metrics

    async def check_health(self) -> Dict[str, Any]:
        """Check health status of vLLM server"""
        health = {
            "status": "unknown",
            "models_loaded": 0,
            "endpoint_responsive": False
        }

        try:
            # Check if models endpoint responds
            models = await self.list_models()
            if models:
                health["status"] = "online"
                health["models_loaded"] = len(models)
                health["endpoint_responsive"] = True
            else:
                # Server responds but no models
                health["status"] = "degraded"
                health["endpoint_responsive"] = True
        except:
            health["status"] = "offline"

        return health