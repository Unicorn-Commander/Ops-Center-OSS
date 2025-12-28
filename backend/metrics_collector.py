"""
Metrics Collector

Background service that collects system metrics every 5 seconds and stores
them in Redis for historical data retrieval.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import docker
import redis
import json
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Background service that continuously collects system metrics.

    Features:
    - Collects metrics every 5 seconds
    - Stores in Redis with 24-hour TTL
    - Automatic cleanup of old data
    - Graceful handling of Redis failures
    """

    def __init__(
        self,
        collection_interval: int = 5,
        retention_hours: int = 24,
        redis_host: str = 'unicorn-lago-redis',
        redis_port: int = 6379,
        redis_db: int = 1
    ):
        """
        Initialize metrics collector.

        Args:
            collection_interval: Seconds between collections (default: 5)
            retention_hours: Hours to retain metrics (default: 24)
            redis_host: Redis host (default: 'unicorn-lago-redis')
            redis_port: Redis port (default: 6379)
            redis_db: Redis database number (default: 1)
        """
        self.collection_interval = collection_interval
        self.retention_seconds = retention_hours * 3600
        self.running = False
        self.redis_connected = False

        # In-memory fallback if Redis unavailable
        self.memory_storage: List[Dict] = []
        self.max_memory_items = 1000

        # Initialize Redis connection
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.redis.ping()
            self.redis_connected = True
            logger.info(f"✓ Metrics collector connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠ Redis connection failed: {e}. Using in-memory storage.")
            self.redis = None
            self.redis_connected = False

    async def start(self):
        """
        Start collecting metrics in background.

        This is a long-running task that should be started with asyncio.create_task()
        """
        if self.running:
            logger.warning("Metrics collector already running")
            return

        self.running = True
        logger.info(f"Starting metrics collector (interval: {self.collection_interval}s)")

        collection_count = 0
        error_count = 0

        while self.running:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()

                # Store metrics
                await self.store_metrics(metrics)

                collection_count += 1

                # Log status every 100 collections
                if collection_count % 100 == 0:
                    storage_type = "Redis" if self.redis_connected else "memory"
                    logger.info(
                        f"Metrics collector: {collection_count} collections, "
                        f"{error_count} errors, storage: {storage_type}"
                    )

                # Sleep until next collection
                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                logger.info("Metrics collector cancelled")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)

        self.running = False
        logger.info(f"Metrics collector stopped (total collections: {collection_count})")

    async def stop(self):
        """Stop the metrics collector."""
        self.running = False

    async def collect_metrics(self) -> Dict:
        """
        Collect current system metrics.

        Returns:
            Dictionary with timestamp and all current metrics
        """
        timestamp = datetime.utcnow()

        # Collect all metrics
        cpu_metrics = self._collect_cpu_metrics()
        memory_metrics = self._collect_memory_metrics()
        disk_metrics = self._collect_disk_metrics()
        network_metrics = self._collect_network_metrics()
        gpu_metrics = self._collect_gpu_metrics()
        docker_metrics = await self._collect_docker_metrics()

        return {
            "timestamp": timestamp.isoformat(),
            "timestamp_unix": int(timestamp.timestamp()),
            "cpu": cpu_metrics,
            "memory": memory_metrics,
            "disk": disk_metrics,
            "network": network_metrics,
            "gpu": gpu_metrics,
            "docker": docker_metrics
        }

    def _collect_cpu_metrics(self) -> Dict:
        """Collect CPU metrics."""
        try:
            return {
                "percent": round(psutil.cpu_percent(interval=0.1), 2),
                "per_cpu": [round(p, 2) for p in psutil.cpu_percent(interval=0.1, percpu=True)],
                "load_avg": [round(x, 2) for x in psutil.getloadavg()] if hasattr(psutil, 'getloadavg') else []
            }
        except Exception as e:
            logger.debug(f"CPU metrics error: {e}")
            return {"percent": 0, "per_cpu": [], "load_avg": []}

    def _collect_memory_metrics(self) -> Dict:
        """Collect memory metrics."""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "percent": round(mem.percent, 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "swap_percent": round(swap.percent, 2)
            }
        except Exception as e:
            logger.debug(f"Memory metrics error: {e}")
            return {"percent": 0, "used_gb": 0, "available_gb": 0, "swap_percent": 0}

    def _collect_disk_metrics(self) -> Dict:
        """Collect disk metrics."""
        try:
            root_usage = psutil.disk_usage('/')
            io_counters = psutil.disk_io_counters()

            return {
                "percent": round(root_usage.percent, 2),
                "used_gb": round(root_usage.used / (1024**3), 2),
                "free_gb": round(root_usage.free / (1024**3), 2),
                "read_mb": round(io_counters.read_bytes / (1024**2), 2),
                "write_mb": round(io_counters.write_bytes / (1024**2), 2)
            }
        except Exception as e:
            logger.debug(f"Disk metrics error: {e}")
            return {"percent": 0, "used_gb": 0, "free_gb": 0, "read_mb": 0, "write_mb": 0}

    def _collect_network_metrics(self) -> Dict:
        """Collect network metrics."""
        try:
            net_io = psutil.net_io_counters()

            return {
                "sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors": net_io.errin + net_io.errout,
                "drops": net_io.dropin + net_io.dropout
            }
        except Exception as e:
            logger.debug(f"Network metrics error: {e}")
            return {"sent_mb": 0, "recv_mb": 0, "packets_sent": 0, "packets_recv": 0, "errors": 0, "drops": 0}

    def _collect_gpu_metrics(self) -> Dict:
        """Collect GPU metrics if available."""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return {"available": False}

            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) == 5:
                        gpus.append({
                            "index": int(parts[0]),
                            "utilization": int(parts[1]),
                            "memory_used": int(parts[2]),
                            "memory_total": int(parts[3]),
                            "temperature": int(parts[4])
                        })

            return {
                "available": True,
                "gpus": gpus
            }
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return {"available": False}

    async def _collect_docker_metrics(self) -> Dict:
        """Collect Docker container metrics."""
        try:
            client = docker.from_env()
            containers = client.containers.list()

            running = len([c for c in containers if c.status == 'running'])
            total = len(client.containers.list(all=True))

            return {
                "running": running,
                "total": total,
                "stopped": total - running
            }
        except Exception as e:
            logger.debug(f"Docker metrics error: {e}")
            return {"running": 0, "total": 0, "stopped": 0}

    async def store_metrics(self, metrics: Dict):
        """
        Store metrics in Redis or memory fallback.

        Args:
            metrics: Metrics dictionary to store
        """
        timestamp = metrics.get("timestamp_unix", int(datetime.utcnow().timestamp()))
        key = f"metrics:{timestamp}"

        # Try Redis first
        if self.redis_connected and self.redis:
            try:
                # Store with TTL
                self.redis.setex(
                    key,
                    self.retention_seconds,
                    json.dumps(metrics)
                )
                return
            except Exception as e:
                logger.warning(f"Redis storage failed: {e}. Falling back to memory.")
                self.redis_connected = False

        # Fallback to memory storage
        self.memory_storage.append(metrics)

        # Cleanup old entries
        if len(self.memory_storage) > self.max_memory_items:
            self.memory_storage = self.memory_storage[-self.max_memory_items:]

    async def get_historical_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        max_points: int = 200
    ) -> List[Dict]:
        """
        Retrieve historical metrics from storage.

        Args:
            start_time: Start of time range
            end_time: End of time range
            max_points: Maximum number of data points to return

        Returns:
            List of metrics dictionaries
        """
        # Try Redis first
        if self.redis_connected and self.redis:
            try:
                return await self._get_from_redis(start_time, end_time, max_points)
            except Exception as e:
                logger.warning(f"Redis retrieval failed: {e}. Using memory fallback.")

        # Fallback to memory
        return self._get_from_memory(start_time, end_time, max_points)

    async def _get_from_redis(
        self,
        start_time: datetime,
        end_time: datetime,
        max_points: int
    ) -> List[Dict]:
        """Retrieve metrics from Redis."""
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        metrics = []

        # Scan for keys in range
        for ts in range(start_ts, end_ts, self.collection_interval):
            key = f"metrics:{ts}"
            data = self.redis.get(key)
            if data:
                metrics.append(json.loads(data))

            # Limit results
            if len(metrics) >= max_points:
                break

        return metrics

    def _get_from_memory(
        self,
        start_time: datetime,
        end_time: datetime,
        max_points: int
    ) -> List[Dict]:
        """Retrieve metrics from memory storage."""
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()

        # Filter by time range
        filtered = [
            m for m in self.memory_storage
            if start_ts <= m.get("timestamp_unix", 0) <= end_ts
        ]

        # Limit to max_points
        if len(filtered) > max_points:
            # Sample evenly
            step = len(filtered) // max_points
            filtered = filtered[::step][:max_points]

        return filtered

    async def get_latest_metrics(self) -> Optional[Dict]:
        """
        Get the most recent metrics.

        Returns:
            Latest metrics dictionary or None
        """
        # Try memory first (fastest)
        if self.memory_storage:
            return self.memory_storage[-1]

        # Try Redis
        if self.redis_connected and self.redis:
            try:
                # Get keys from last minute
                now = int(datetime.utcnow().timestamp())
                for offset in range(0, 60, self.collection_interval):
                    key = f"metrics:{now - offset}"
                    data = self.redis.get(key)
                    if data:
                        return json.loads(data)
            except Exception:
                pass

        return None

    def get_storage_stats(self) -> Dict:
        """
        Get statistics about metrics storage.

        Returns:
            Dictionary with storage stats
        """
        stats = {
            "redis_connected": self.redis_connected,
            "memory_items": len(self.memory_storage),
            "running": self.running,
            "collection_interval": self.collection_interval,
            "retention_hours": self.retention_seconds / 3600
        }

        if self.redis_connected and self.redis:
            try:
                # Count keys in Redis
                keys = self.redis.keys("metrics:*")
                stats["redis_items"] = len(keys)
            except Exception:
                stats["redis_items"] = 0

        return stats
