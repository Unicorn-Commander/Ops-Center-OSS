"""
Dynamic System Detection Module for UC-1 Pro
Detects hardware and system configuration across different deployments.
Works on VPS (CPU-only), GPU servers, and hybrid systems.
"""

import os
import re
import json
import subprocess
import platform
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information"""
    vendor: str  # NVIDIA, AMD, Intel
    name: str
    memory_mb: int
    compute_capability: Optional[str] = None
    driver_version: Optional[str] = None
    temperature: Optional[float] = None
    utilization: Optional[float] = None


@dataclass
class NPUInfo:
    """NPU information"""
    vendor: str
    model: str
    tops: int
    available: bool
    driver_loaded: bool = False


@dataclass
class CPUInfo:
    """CPU information"""
    vendor: str
    model: str
    physical_cores: int
    logical_cores: int
    base_frequency_mhz: Optional[float] = None
    features: List[str] = None


@dataclass
class SystemCapabilities:
    """Complete system capabilities"""
    deployment_type: str  # 'cpu', 'gpu', 'npu', 'hybrid'
    home_directory: str
    hostname: str
    platform: str
    architecture: str
    cpu: CPUInfo
    gpus: List[GPUInfo]
    npus: List[NPUInfo]
    memory_gb: float
    storage_gb: float
    has_gpu: bool
    has_npu: bool


class SystemDetector:
    """Detect system hardware and configuration dynamically"""

    def __init__(self):
        self.home_dir = self.get_home_directory()
        logger.info(f"Initialized SystemDetector with home directory: {self.home_dir}")

    @staticmethod
    def get_home_directory() -> str:
        """
        Get current user's home directory dynamically.
        Works across different users (ucadmin, muut, etc.)

        Returns:
            str: Absolute path to home directory
        """
        # Try multiple methods to ensure we get the correct home
        home = os.path.expanduser("~")

        # Verify it exists and is accessible
        if not os.path.exists(home):
            # Fallback to environment variable
            home = os.environ.get('HOME', '/root')

        logger.info(f"Detected home directory: {home}")
        return home

    def detect_gpus(self) -> List[Dict[str, Any]]:
        """
        Detect all GPUs (NVIDIA, AMD, Intel).
        Returns empty list if no GPUs found.

        Returns:
            List[Dict]: List of GPU information dictionaries
        """
        gpus = []

        # Detect NVIDIA GPUs
        nvidia_gpus = self._detect_nvidia_gpus()
        gpus.extend(nvidia_gpus)

        # Detect AMD GPUs
        amd_gpus = self._detect_amd_gpus()
        gpus.extend(amd_gpus)

        # Detect Intel GPUs
        intel_gpus = self._detect_intel_gpus()
        gpus.extend(intel_gpus)

        logger.info(f"Detected {len(gpus)} GPU(s)")
        return gpus

    def _detect_nvidia_gpus(self) -> List[Dict[str, Any]]:
        """Detect NVIDIA GPUs using nvidia-smi"""
        gpus = []

        try:
            # Check if nvidia-smi exists
            result = subprocess.run(
                ["which", "nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                logger.debug("nvidia-smi not found")
                return gpus

            # Query GPU information
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,compute_cap,driver_version,temperature.gpu,utilization.gpu",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2:
                            gpu_info = {
                                "vendor": "NVIDIA",
                                "name": parts[0],
                                "memory_mb": int(float(parts[1])) if len(parts) > 1 else 0,
                                "compute_capability": parts[2] if len(parts) > 2 else None,
                                "driver_version": parts[3] if len(parts) > 3 else None,
                                "temperature": float(parts[4]) if len(parts) > 4 and parts[4] else None,
                                "utilization": float(parts[5]) if len(parts) > 5 and parts[5] else None,
                            }
                            gpus.append(gpu_info)
                            logger.info(f"Found NVIDIA GPU: {gpu_info['name']}")

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"NVIDIA GPU detection failed: {e}")

        return gpus

    def _detect_amd_gpus(self) -> List[Dict[str, Any]]:
        """Detect AMD GPUs using lspci and rocm-smi if available"""
        gpus = []

        try:
            # Use lspci to detect AMD GPUs
            result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if re.search(r'(AMD|ATI).*(VGA|Display)', line, re.IGNORECASE):
                        # Extract GPU name
                        gpu_name = "AMD GPU"

                        # Try to get more specific name
                        if "Radeon" in line:
                            match = re.search(r'Radeon\s+[\w\s]+', line)
                            if match:
                                gpu_name = match.group(0).strip()

                        gpu_info = {
                            "vendor": "AMD",
                            "name": gpu_name,
                            "memory_mb": 0,  # Will try to get from rocm-smi
                            "driver_version": None,
                            "pci_info": line.strip()
                        }

                        # Try to get more info from rocm-smi if available
                        try:
                            rocm_result = subprocess.run(
                                ["rocm-smi", "--showmeminfo", "vram", "--json"],
                                capture_output=True,
                                text=True,
                                timeout=3
                            )
                            if rocm_result.returncode == 0:
                                rocm_data = json.loads(rocm_result.stdout)
                                # Parse VRAM info from rocm-smi output
                                # This is a simplified parse, actual structure may vary
                                gpu_info["rocm_available"] = True
                        except:
                            gpu_info["rocm_available"] = False

                        gpus.append(gpu_info)
                        logger.info(f"Found AMD GPU: {gpu_name}")

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"AMD GPU detection failed: {e}")

        return gpus

    def _detect_intel_gpus(self) -> List[Dict[str, Any]]:
        """Detect Intel GPUs using lspci"""
        gpus = []

        try:
            result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if re.search(r'Intel.*(VGA|Display)', line, re.IGNORECASE):
                        gpu_name = "Intel GPU"

                        # Try to get more specific name
                        if "Arc" in line:
                            gpu_name = "Intel Arc Graphics"
                        elif "Iris" in line:
                            gpu_name = "Intel Iris Graphics"
                        elif "UHD" in line:
                            gpu_name = "Intel UHD Graphics"

                        gpu_info = {
                            "vendor": "Intel",
                            "name": gpu_name,
                            "memory_mb": 0,
                            "type": "discrete" if "Arc" in gpu_name else "integrated",
                            "pci_info": line.strip()
                        }

                        gpus.append(gpu_info)
                        logger.info(f"Found Intel GPU: {gpu_name}")

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Intel GPU detection failed: {e}")

        return gpus

    def detect_npus(self) -> List[Dict[str, Any]]:
        """
        Detect NPUs if present.
        Returns empty list if no NPUs found.

        Returns:
            List[Dict]: List of NPU information dictionaries
        """
        npus = []

        # Check for AMD NPU (Ryzen AI / Phoenix)
        amd_npu = self._detect_amd_npu()
        if amd_npu:
            npus.append(amd_npu)

        # Check for Intel NPU
        intel_npu = self._detect_intel_npu()
        if intel_npu:
            npus.append(intel_npu)

        logger.info(f"Detected {len(npus)} NPU(s)")
        return npus

    def _detect_amd_npu(self) -> Optional[Dict[str, Any]]:
        """Detect AMD NPU (Ryzen AI)"""
        try:
            # Check lspci for NPU
            result = subprocess.run(
                ["lspci"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "AMD IPU Device" in line or ("Signal processing controller" in line and "AMD" in line):
                        npu_info = {
                            "vendor": "AMD",
                            "model": "Ryzen AI (XDNA1)",
                            "tops": 16,
                            "available": os.path.exists("/dev/xdna0"),
                            "driver_loaded": os.path.exists("/dev/xdna0"),
                            "pci_info": line.strip()
                        }
                        logger.info("Found AMD NPU")
                        return npu_info

            # Fallback: Check by CPU model
            cpu_info = self.detect_cpu_info()
            cpu_model = cpu_info.get("model", "")

            if any(x in cpu_model for x in ["7840", "7940", "8840", "8940", "8945"]):
                npu_info = {
                    "vendor": "AMD",
                    "model": "Ryzen AI (XDNA1)",
                    "tops": 16,
                    "available": False,
                    "driver_loaded": False,
                    "detection_method": "cpu_model"
                }
                logger.info("Found AMD NPU via CPU model detection")
                return npu_info

        except Exception as e:
            logger.debug(f"AMD NPU detection failed: {e}")

        return None

    def _detect_intel_npu(self) -> Optional[Dict[str, Any]]:
        """Detect Intel NPU (AI Boost)"""
        try:
            cpu_info = self.detect_cpu_info()
            cpu_model = cpu_info.get("model", "")

            # Intel NPU is in Meteor Lake and later (Core Ultra)
            if "Core Ultra" in cpu_model:
                npu_info = {
                    "vendor": "Intel",
                    "model": "Intel AI Boost",
                    "tops": 11,  # Varies by model
                    "available": False,  # Need proper detection
                    "driver_loaded": False,
                    "detection_method": "cpu_model"
                }
                logger.info("Found Intel NPU")
                return npu_info

        except Exception as e:
            logger.debug(f"Intel NPU detection failed: {e}")

        return None

    def detect_cpu_info(self) -> Dict[str, Any]:
        """
        Get CPU model, cores, threads, and features.

        Returns:
            Dict: CPU information
        """
        cpu_info = {
            "vendor": "Unknown",
            "model": "Unknown CPU",
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "logical_cores": psutil.cpu_count(logical=True) or 1,
            "base_frequency_mhz": None,
            "features": []
        }

        try:
            # Get CPU info from /proc/cpuinfo
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo_content = f.read()

                    # Get model name
                    for line in cpuinfo_content.split('\n'):
                        if 'model name' in line:
                            cpu_info["model"] = line.split(':')[1].strip()

                            # Detect vendor
                            if "Intel" in cpu_info["model"]:
                                cpu_info["vendor"] = "Intel"
                            elif "AMD" in cpu_info["model"]:
                                cpu_info["vendor"] = "AMD"
                            break

                    # Detect CPU features
                    features = []
                    if 'avx512' in cpuinfo_content:
                        features.append("AVX512")
                    elif 'avx2' in cpuinfo_content:
                        features.append("AVX2")
                    elif 'avx' in cpuinfo_content:
                        features.append("AVX")

                    if 'sse4' in cpuinfo_content:
                        features.append("SSE4")
                    if 'amx' in cpuinfo_content:
                        features.append("AMX")
                    if 'vnni' in cpuinfo_content:
                        features.append("VNNI")

                    cpu_info["features"] = features

            # Try to get frequency
            try:
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info["base_frequency_mhz"] = freq.current
            except:
                pass

        except Exception as e:
            logger.warning(f"Error detecting CPU info: {e}")

        logger.info(f"Detected CPU: {cpu_info['model']}")
        return cpu_info

    def get_deployment_type(self) -> str:
        """
        Determine deployment type based on available hardware.

        Returns:
            str: 'cpu', 'gpu', 'npu', or 'hybrid'
        """
        gpus = self.detect_gpus()
        npus = self.detect_npus()

        has_gpu = len(gpus) > 0
        has_npu = len(npus) > 0

        if has_gpu and has_npu:
            return "hybrid"
        elif has_gpu:
            return "gpu"
        elif has_npu:
            return "npu"
        else:
            return "cpu"

    def get_system_capabilities(self) -> Dict[str, Any]:
        """
        Get complete system profile for frontend.

        Returns:
            Dict: Complete system capabilities
        """
        # Detect all components
        cpu_info = self.detect_cpu_info()
        gpus = self.detect_gpus()
        npus = self.detect_npus()

        # Get memory info
        mem = psutil.virtual_memory()
        memory_gb = round(mem.total / (1024**3), 2)

        # Get storage info
        storage_gb = 0
        try:
            for partition in psutil.disk_partitions():
                if partition.mountpoint == '/':
                    usage = psutil.disk_usage(partition.mountpoint)
                    storage_gb = round(usage.total / (1024**3), 2)
                    break
        except:
            pass

        # Determine deployment type
        deployment_type = self.get_deployment_type()

        # Build capabilities object
        capabilities = {
            "deployment_type": deployment_type,
            "home_directory": self.home_dir,
            "hostname": platform.node(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "kernel": platform.release(),
            "cpu": cpu_info,
            "gpus": gpus,
            "npus": npus,
            "memory_gb": memory_gb,
            "memory_available_gb": round(mem.available / (1024**3), 2),
            "storage_gb": storage_gb,
            "has_gpu": len(gpus) > 0,
            "has_npu": len(npus) > 0,
            "timestamp": psutil.boot_time(),
        }

        # Add recommendations
        capabilities["recommendations"] = self._generate_recommendations(capabilities)

        logger.info(f"System capabilities: {deployment_type} deployment with {len(gpus)} GPU(s), {len(npus)} NPU(s)")

        return capabilities

    def _generate_recommendations(self, capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment recommendations based on capabilities"""
        deployment_type = capabilities["deployment_type"]
        memory_gb = capabilities["memory_gb"]

        recommendations = {
            "deployment_type": deployment_type,
            "recommended_backends": [],
            "max_model_size_gb": 0,
            "compose_file": "docker-compose.yml",
            "notes": []
        }

        if deployment_type == "gpu":
            gpus = capabilities["gpus"]
            if gpus and gpus[0]["vendor"] == "NVIDIA":
                vram_gb = gpus[0]["memory_mb"] / 1024
                recommendations["recommended_backends"] = ["vllm", "ollama", "llamacpp"]
                recommendations["max_model_size_gb"] = round(vram_gb * 0.9, 1)
                recommendations["compose_file"] = "docker-compose.yml"
                recommendations["notes"].append("NVIDIA GPU detected - vLLM recommended for best performance")
            else:
                recommendations["recommended_backends"] = ["ollama", "llamacpp"]
                recommendations["max_model_size_gb"] = round(memory_gb * 0.4, 1)
                recommendations["notes"].append("Non-NVIDIA GPU - using Ollama/llama.cpp")

        elif deployment_type == "hybrid":
            recommendations["recommended_backends"] = ["ollama", "llamacpp"]
            recommendations["max_model_size_gb"] = round(memory_gb * 0.4, 1)
            recommendations["compose_file"] = "docker-compose.hybrid.yml"
            recommendations["notes"].append("Hybrid deployment with GPU and NPU support")

        elif deployment_type == "npu":
            recommendations["recommended_backends"] = ["llamacpp", "onnxruntime"]
            recommendations["max_model_size_gb"] = round(memory_gb * 0.3, 1)
            recommendations["compose_file"] = "docker-compose.npu.yml"
            recommendations["notes"].append("NPU-accelerated deployment for edge AI")

        else:  # cpu
            recommendations["recommended_backends"] = ["ollama", "llamacpp"]
            recommendations["max_model_size_gb"] = round(memory_gb * 0.3, 1)
            recommendations["compose_file"] = "docker-compose.cpu.yml"
            recommendations["notes"].append("CPU-only deployment - using remote LLM APIs recommended")

        return recommendations


# Singleton instance
system_detector = SystemDetector()


# Convenience functions
def get_home_directory() -> str:
    """Get current user's home directory"""
    return system_detector.get_home_directory()


def detect_gpus() -> List[Dict[str, Any]]:
    """Detect all GPUs"""
    return system_detector.detect_gpus()


def detect_npus() -> List[Dict[str, Any]]:
    """Detect all NPUs"""
    return system_detector.detect_npus()


def detect_cpu_info() -> Dict[str, Any]:
    """Get CPU information"""
    return system_detector.detect_cpu_info()


def get_deployment_type() -> str:
    """Get deployment type"""
    return system_detector.get_deployment_type()


def get_system_capabilities() -> Dict[str, Any]:
    """Get complete system capabilities"""
    return system_detector.get_system_capabilities()
