"""
GPU Monitoring Utility for Local Inference

Provides GPU stats using nvidia-smi or pynvml.
Caches results to avoid excessive subprocess calls.

Author: Ops-Center Backend Team
Created: 2026-01-24
"""

import asyncio
import logging
import subprocess
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..base_provider import GPUInfo

logger = logging.getLogger(__name__)


# =============================================================================
# Cache Configuration
# =============================================================================

_gpu_cache: Optional[List[GPUInfo]] = None
_gpu_cache_time: Optional[datetime] = None
_gpu_cache_ttl: timedelta = timedelta(seconds=5)

# Lock for thread-safe cache access
_cache_lock = asyncio.Lock()


# =============================================================================
# GPU Monitoring Functions
# =============================================================================

async def get_gpu_info() -> List[GPUInfo]:
    """
    Get GPU information with caching.

    Uses nvidia-smi to query GPU stats. Results are cached for
    5 seconds to avoid excessive subprocess calls.

    Returns:
        List of GPUInfo objects for each detected GPU
    """
    global _gpu_cache, _gpu_cache_time

    async with _cache_lock:
        # Check cache validity
        now = datetime.now()
        if _gpu_cache is not None and _gpu_cache_time is not None:
            if now - _gpu_cache_time < _gpu_cache_ttl:
                logger.debug("Returning cached GPU info")
                return _gpu_cache

        # Fetch fresh GPU info
        try:
            gpu_list = await _fetch_gpu_info_nvidia_smi()
            _gpu_cache = gpu_list
            _gpu_cache_time = now
            return gpu_list
        except Exception as e:
            logger.warning(f"Failed to get GPU info: {e}")
            # Return cached data if available, otherwise empty list
            return _gpu_cache if _gpu_cache is not None else []


async def _fetch_gpu_info_nvidia_smi() -> List[GPUInfo]:
    """
    Fetch GPU info using nvidia-smi command.

    Runs nvidia-smi asynchronously to avoid blocking.

    Returns:
        List of GPUInfo objects
    """
    # nvidia-smi query format
    query_fields = [
        "index",
        "name",
        "memory.used",
        "memory.total",
        "memory.free",
        "utilization.gpu",
        "temperature.gpu",
        "power.draw",
        "power.limit",
        "fan.speed",
        "compute_cap",
        "driver_version",
    ]

    query_format = ",".join(query_fields)

    cmd = [
        "nvidia-smi",
        f"--query-gpu={query_format}",
        "--format=csv,noheader,nounits"
    ]

    try:
        # Run nvidia-smi asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=5.0
        )

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            raise RuntimeError(f"nvidia-smi failed: {error_msg}")

        # Parse output
        output = stdout.decode().strip()
        if not output:
            logger.warning("nvidia-smi returned empty output")
            return []

        gpu_list = []
        for line in output.split("\n"):
            if not line.strip():
                continue

            try:
                gpu_info = _parse_nvidia_smi_line(line)
                if gpu_info:
                    gpu_list.append(gpu_info)
            except Exception as e:
                logger.warning(f"Failed to parse GPU line '{line}': {e}")

        logger.debug(f"Detected {len(gpu_list)} GPUs via nvidia-smi")
        return gpu_list

    except asyncio.TimeoutError:
        raise RuntimeError("nvidia-smi timed out")
    except FileNotFoundError:
        raise RuntimeError("nvidia-smi not found - NVIDIA drivers may not be installed")


def _parse_nvidia_smi_line(line: str) -> Optional[GPUInfo]:
    """
    Parse a single line of nvidia-smi output.

    Args:
        line: CSV line from nvidia-smi

    Returns:
        GPUInfo object or None if parsing fails
    """
    parts = [p.strip() for p in line.split(",")]

    if len(parts) < 6:
        logger.warning(f"Unexpected nvidia-smi output format: {line}")
        return None

    def safe_int(val: str, default: int = 0) -> int:
        """Safely convert string to int"""
        try:
            val = val.strip()
            if val in ("[N/A]", "N/A", "[Not Supported]", ""):
                return default
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def safe_float(val: str, default: float = 0.0) -> float:
        """Safely convert string to float"""
        try:
            val = val.strip()
            if val in ("[N/A]", "N/A", "[Not Supported]", ""):
                return default
            return float(val)
        except (ValueError, TypeError):
            return default

    def safe_str(val: str, default: str = "") -> Optional[str]:
        """Safely get string value"""
        val = val.strip()
        if val in ("[N/A]", "N/A", "[Not Supported]", ""):
            return None
        return val

    # Parse fields
    index = safe_int(parts[0])
    name = parts[1].strip() if len(parts) > 1 else f"GPU {index}"
    memory_used = safe_int(parts[2]) if len(parts) > 2 else 0
    memory_total = safe_int(parts[3]) if len(parts) > 3 else 0
    memory_free = safe_int(parts[4]) if len(parts) > 4 else None
    utilization = safe_float(parts[5]) if len(parts) > 5 else 0.0
    temperature = safe_int(parts[6]) if len(parts) > 6 else None
    power_draw = safe_float(parts[7]) if len(parts) > 7 else None
    power_limit = safe_float(parts[8]) if len(parts) > 8 else None
    fan_speed = safe_int(parts[9]) if len(parts) > 9 else None
    compute_cap = safe_str(parts[10]) if len(parts) > 10 else None
    driver_version = safe_str(parts[11]) if len(parts) > 11 else None

    return GPUInfo(
        index=index,
        name=name,
        memory_used_mb=memory_used,
        memory_total_mb=memory_total,
        memory_free_mb=memory_free,
        utilization_percent=utilization,
        temperature_c=temperature,
        power_draw_w=power_draw,
        power_limit_w=power_limit,
        fan_speed_percent=fan_speed,
        compute_capability=compute_cap,
        driver_version=driver_version,
    )


# =============================================================================
# Alternative: pynvml Implementation
# =============================================================================

async def get_gpu_info_pynvml() -> List[GPUInfo]:
    """
    Get GPU info using pynvml (NVIDIA Management Library).

    This is an alternative implementation that uses the Python
    bindings for NVML. Requires pynvml to be installed.

    Returns:
        List of GPUInfo objects
    """
    try:
        import pynvml
    except ImportError:
        raise RuntimeError("pynvml not installed - run 'pip install pynvml'")

    try:
        pynvml.nvmlInit()

        device_count = pynvml.nvmlDeviceGetCount()
        gpu_list = []

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            # Get basic info
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')

            # Memory info
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used_mb = memory_info.used // (1024 * 1024)
            memory_total_mb = memory_info.total // (1024 * 1024)
            memory_free_mb = memory_info.free // (1024 * 1024)

            # Utilization
            try:
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                util_percent = utilization.gpu
            except pynvml.NVMLError:
                util_percent = 0.0

            # Temperature
            try:
                temperature = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except pynvml.NVMLError:
                temperature = None

            # Power
            try:
                power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
            except pynvml.NVMLError:
                power_draw = None

            try:
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
            except pynvml.NVMLError:
                power_limit = None

            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError:
                fan_speed = None

            # Compute capability
            try:
                major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                compute_cap = f"{major}.{minor}"
            except pynvml.NVMLError:
                compute_cap = None

            # Driver version
            try:
                driver_version = pynvml.nvmlSystemGetDriverVersion()
                if isinstance(driver_version, bytes):
                    driver_version = driver_version.decode('utf-8')
            except pynvml.NVMLError:
                driver_version = None

            # CUDA version
            try:
                cuda_version_raw = pynvml.nvmlSystemGetCudaDriverVersion_v2()
                cuda_major = cuda_version_raw // 1000
                cuda_minor = (cuda_version_raw % 1000) // 10
                cuda_version = f"{cuda_major}.{cuda_minor}"
            except pynvml.NVMLError:
                cuda_version = None

            gpu_info = GPUInfo(
                index=i,
                name=name,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                memory_free_mb=memory_free_mb,
                utilization_percent=float(util_percent),
                temperature_c=temperature,
                power_draw_w=power_draw,
                power_limit_w=power_limit,
                fan_speed_percent=fan_speed,
                compute_capability=compute_cap,
                driver_version=driver_version,
                cuda_version=cuda_version,
            )
            gpu_list.append(gpu_info)

        return gpu_list

    except pynvml.NVMLError as e:
        raise RuntimeError(f"NVML error: {e}")
    finally:
        try:
            pynvml.nvmlShutdown()
        except:
            pass


# =============================================================================
# Utility Functions
# =============================================================================

async def get_gpu_count() -> int:
    """
    Get the number of available GPUs.

    Returns:
        Number of GPUs detected
    """
    gpu_list = await get_gpu_info()
    return len(gpu_list)


async def get_total_gpu_memory_mb() -> int:
    """
    Get total GPU memory across all GPUs.

    Returns:
        Total memory in MB
    """
    gpu_list = await get_gpu_info()
    return sum(gpu.memory_total_mb for gpu in gpu_list)


async def get_available_gpu_memory_mb() -> int:
    """
    Get available GPU memory across all GPUs.

    Returns:
        Available memory in MB
    """
    gpu_list = await get_gpu_info()
    return sum(gpu.memory_free_mb or 0 for gpu in gpu_list)


async def get_gpu_summary() -> Dict[str, Any]:
    """
    Get a summary of GPU status.

    Returns:
        Dictionary with GPU summary information
    """
    gpu_list = await get_gpu_info()

    if not gpu_list:
        return {
            "gpu_count": 0,
            "total_memory_mb": 0,
            "used_memory_mb": 0,
            "free_memory_mb": 0,
            "avg_utilization_percent": 0.0,
            "max_temperature_c": None,
            "total_power_draw_w": None,
            "gpus": [],
        }

    total_memory = sum(gpu.memory_total_mb for gpu in gpu_list)
    used_memory = sum(gpu.memory_used_mb for gpu in gpu_list)
    free_memory = sum(gpu.memory_free_mb or 0 for gpu in gpu_list)
    avg_util = sum(gpu.utilization_percent for gpu in gpu_list) / len(gpu_list)

    temps = [gpu.temperature_c for gpu in gpu_list if gpu.temperature_c is not None]
    max_temp = max(temps) if temps else None

    powers = [gpu.power_draw_w for gpu in gpu_list if gpu.power_draw_w is not None]
    total_power = sum(powers) if powers else None

    return {
        "gpu_count": len(gpu_list),
        "total_memory_mb": total_memory,
        "used_memory_mb": used_memory,
        "free_memory_mb": free_memory,
        "avg_utilization_percent": round(avg_util, 1),
        "max_temperature_c": max_temp,
        "total_power_draw_w": round(total_power, 1) if total_power else None,
        "gpus": [
            {
                "index": gpu.index,
                "name": gpu.name,
                "memory_used_mb": gpu.memory_used_mb,
                "memory_total_mb": gpu.memory_total_mb,
                "utilization_percent": gpu.utilization_percent,
                "temperature_c": gpu.temperature_c,
            }
            for gpu in gpu_list
        ],
    }


def clear_gpu_cache() -> None:
    """Clear the GPU info cache to force a refresh"""
    global _gpu_cache, _gpu_cache_time
    _gpu_cache = None
    _gpu_cache_time = None
    logger.debug("GPU cache cleared")


async def is_nvidia_available() -> bool:
    """
    Check if NVIDIA GPU is available.

    Returns:
        True if nvidia-smi is available and working
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "nvidia-smi", "--version",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(process.wait(), timeout=2.0)
        return process.returncode == 0
    except (FileNotFoundError, asyncio.TimeoutError):
        return False
    except Exception:
        return False
