"""
Hardware detection for federation node advertisement.
"""


import platform
import shutil
import subprocess
from typing import Any, Dict, List

import psutil


class HardwareDetector:
    def detect(self) -> Dict[str, Any]:
        profile = {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "cpu": {
                "physical_cores": psutil.cpu_count(logical=False) or 0,
                "logical_cores": psutil.cpu_count(logical=True) or 0,
                "usage_percent": psutil.cpu_percent(interval=0.1),
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
            },
            "gpus": self._detect_gpus(),
            "accelerators": [],
        }
        profile["service_types"] = self.advertised_service_types(profile)
        return profile

    def advertised_service_types(self, profile: Dict[str, Any]) -> List[str]:
        services = {"llm", "embeddings", "reranker"}
        gpu_count = len(profile.get("gpus", []))
        total_vram = sum(gpu.get("memory_total_mb", 0) for gpu in profile.get("gpus", []))

        if gpu_count > 0:
            services.update({"image_gen", "tts", "stt"})
        if total_vram >= 12000:
            services.add("music_gen")
        return sorted(services)

    def build_service_inventory(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        services = []
        total_vram = sum(gpu.get("memory_total_mb", 0) for gpu in profile.get("gpus", []))
        for service_type in self.advertised_service_types(profile):
            capabilities = {
                "hardware_accelerated": len(profile.get("gpus", [])) > 0,
                "total_vram_mb": total_vram,
            }
            services.append(
                {
                    "service_type": service_type,
                    "models": [],
                    "endpoint_path": self._default_path(service_type),
                    "status": "running" if len(profile.get("gpus", [])) > 0 or service_type in {"llm", "embeddings", "reranker"} else "degraded",
                    "capabilities": capabilities,
                    "cold_start_seconds": 5 if service_type in {"embeddings", "reranker"} else 20,
                    "avg_latency_ms": 150 if service_type in {"embeddings", "reranker"} else 800,
                    "cost_usd": 0.0,
                }
            )
        return services

    def _detect_gpus(self) -> List[Dict[str, Any]]:
        if not shutil.which("nvidia-smi"):
            return []
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return []

        gpus = []
        for line in result.stdout.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 5:
                continue
            total_mb = int(parts[2])
            free_mb = int(parts[3])
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": parts[1],
                    "memory_total_mb": total_mb,
                    "memory_free_mb": free_mb,
                    "memory_used_mb": total_mb - free_mb,
                    "utilization_percent": int(parts[4]),
                }
            )
        return gpus

    @staticmethod
    def _default_path(service_type: str) -> str:
        mapping = {
            "llm": "/api/v1/llm/chat/completions",
            "tts": "/api/v1/tts/synthesize",
            "stt": "/api/v1/stt/transcribe",
            "embeddings": "/api/v1/embeddings",
            "image_gen": "/api/v1/images/generate",
            "music_gen": "/api/v1/music/generate",
            "reranker": "/api/v1/rerank",
            "agents": "/api/v1/a2a/agents/{id}/invoke",
        }
        return mapping.get(service_type, "/api/v1/inference")
