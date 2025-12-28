"""
Reranking Server Adapter
Handles communication with reranking servers
"""

from typing import List, Dict, Any, Optional
import aiohttp
import logging
from .base import ServerAdapter, ModelInfo, ServerMetrics

logger = logging.getLogger(__name__)

class RerankingAdapter(ServerAdapter):
    """Adapter for reranking servers"""

    async def test_connection(self) -> bool:
        """Test connection to reranking server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/health',
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Reranking server connection test failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List available models on reranking server"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to get model info
                async with session.get(f'{self.base_url}/info') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        model_id = data.get('model_id', data.get('model', 'unknown'))
                        return [ModelInfo(
                            id=model_id,
                            name=model_id,
                            loaded=True,
                            metadata=data
                        )]
        except Exception as e:
            logger.error(f"Error listing reranking models: {e}")

        return []

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed information about the reranking model"""
        models = await self.list_models()
        if models:
            return models[0]
        return ModelInfo(id=model_id, name=model_id, loaded=False)

    async def load_model(self, model_id: str, **kwargs) -> bool:
        """
        Reranking servers typically load one model at startup.
        Dynamic loading not supported.
        """
        logger.info(f"Reranking model loading requested for {model_id} - requires server restart")
        return False

    async def unload_model(self, model_id: str) -> bool:
        """
        Reranking servers don't support dynamic unloading.
        """
        logger.info(f"Reranking model unloading requested for {model_id} - not supported")
        return False

    async def get_metrics(self) -> ServerMetrics:
        """Get server metrics from reranking server"""
        metrics = ServerMetrics()

        try:
            async with aiohttp.ClientSession() as session:
                # Try metrics endpoint if available
                try:
                    async with session.get(
                        f'{self.base_url}/metrics',
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            metrics_text = await resp.text()
                            parsed = self._parse_prometheus_metrics(metrics_text)

                            # Extract relevant metrics
                            if 'rerank_request_count' in parsed:
                                metrics.total_requests = int(parsed['rerank_request_count'])
                            if 'rerank_request_duration_seconds_sum' in parsed and 'rerank_request_count' in parsed:
                                if parsed['rerank_request_count'] > 0:
                                    metrics.avg_response_time = parsed['rerank_request_duration_seconds_sum'] / parsed['rerank_request_count']
                except:
                    pass  # Metrics endpoint not available

                # Get model info for metadata
                try:
                    async with session.get(f'{self.base_url}/info') as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            metrics.metadata = {
                                "model": data.get('model_id', data.get('model')),
                                "max_length": data.get('max_length')
                            }
                except:
                    pass

        except Exception as e:
            logger.error(f"Error getting reranking server metrics: {e}")

        return metrics

    async def check_health(self) -> Dict[str, Any]:
        """Check health status of reranking server"""
        health = {
            "status": "unknown",
            "model_loaded": False,
            "endpoint_responsive": False
        }

        try:
            # Check health endpoint
            if await self.test_connection():
                health["status"] = "online"
                health["endpoint_responsive"] = True

                # Check if model is loaded
                models = await self.list_models()
                if models:
                    health["model_loaded"] = True
                    health["model_id"] = models[0].id
            else:
                health["status"] = "offline"
        except:
            health["status"] = "offline"

        return health