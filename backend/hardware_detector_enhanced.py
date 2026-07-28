"""
Enhanced Hardware Detection for Standalone Ops Center
Auto-detects all system hardware and configures services accordingly
"""
import subprocess
import re
import os
import json
import platform
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class GPUConfig:
    """GPU configuration details"""
    index: int
    model: str
    vram_mb: int
    driver: str
    cuda_version: Optional[str] = None
    compute_capability: Optional[str] = None
    pci_bus: Optional[str] = None
    uuid: Optional[str] = None
    
    @property
    def vram_gb(self) -> float:
        return self.vram_mb / 1024

@dataclass
class SystemRequirements:
    """Calculated system requirements for AI services"""
    can_run_llm: bool
    recommended_llm_backend: str  # vllm, ollama, llama.cpp, etc.
    max_model_size_gb: float
    recommended_models: List[str]
    gpu_allocation: Dict[str, Any]
    warnings: List[str]

class EnhancedHardwareDetector:
    """Enhanced hardware detection with AI service recommendations"""
    
    def __init__(self):
        self.hardware = {}
        self.detect_all()
    
    def detect_all(self):
        """Detect all hardware components"""
        self.hardware = {
            "timestamp": self._get_timestamp(),
            "system": self._detect_system(),
            "cpu": self._detect_cpu(),
            "memory": self._detect_memory(),
            "gpus": self._detect_all_gpus(),
            "storage": self._detect_storage(),
            "network": self._detect_network(),
            "docker": self._detect_docker(),
            "virtualization": self._detect_virtualization()
        }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _detect_system(self) -> Dict[str, Any]:
        """Detect system and OS information"""
        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "boot_time": psutil.boot_time()
        }
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """Enhanced CPU detection"""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
            "min_frequency": psutil.cpu_freq().min if psutil.cpu_freq() else 0,
            "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "cpu_usage": psutil.cpu_percent(interval=1),
            "per_cpu_usage": psutil.cpu_percent(interval=1, percpu=True)
        }
        
        # Get detailed CPU info from /proc/cpuinfo
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
            if model_match:
                cpu_info["model"] = model_match.group(1).strip()
            
            # Check for AVX support (important for AI workloads)
            flags_match = re.search(r'flags\s*:\s*(.+)', cpuinfo)
            if flags_match:
                flags = flags_match.group(1)
                cpu_info["features"] = {
                    "avx": "avx" in flags,
                    "avx2": "avx2" in flags,
                    "avx512": "avx512" in flags,
                    "sse4_1": "sse4_1" in flags,
                    "sse4_2": "sse4_2" in flags,
                    "vnni": "vnni" in flags  # Intel DL Boost
                }
        except:
            pass
        
        return cpu_info
    
    def _detect_memory(self) -> Dict[str, Any]:
        """Enhanced memory detection"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": mem.total / (1024**3),
            "available_gb": mem.available / (1024**3),
            "used_gb": mem.used / (1024**3),
            "percent": mem.percent,
            "swap_total_gb": swap.total / (1024**3),
            "swap_used_gb": swap.used / (1024**3),
            "swap_percent": swap.percent,
            "type": self._detect_memory_type()
        }
    
    def _detect_memory_type(self) -> str:
        """Detect memory type (DDR4, DDR5, etc.)"""
        try:
            result = subprocess.run(
                ["sudo", "dmidecode", "-t", "memory"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                type_match = re.search(r'Type:\s*(DDR\d+)', result.stdout)
                if type_match:
                    return type_match.group(1)
        except:
            pass
        return "Unknown"
    
    def _detect_all_gpus(self) -> Dict[str, Any]:
        """Detect all GPUs (NVIDIA, AMD, Intel)"""
        gpus = {
            "nvidia": self._detect_nvidia_gpus(),
            "amd": self._detect_amd_gpus(),
            "intel": self._detect_intel_gpus(),
            "summary": {}
        }
        
        # Create summary
        total_vram = sum(gpu.get("vram_mb", 0) for gpu in gpus["nvidia"])
        gpus["summary"] = {
            "total_gpus": len(gpus["nvidia"]) + len(gpus["amd"]) + len(gpus["intel"]),
            "nvidia_count": len(gpus["nvidia"]),
            "amd_count": len(gpus["amd"]),
            "intel_count": len(gpus["intel"]),
            "total_vram_gb": total_vram / 1024 if total_vram > 0 else 0,
            "cuda_available": len(gpus["nvidia"]) > 0,
            "rocm_available": len(gpus["amd"]) > 0,
            "level_zero_available": len(gpus["intel"]) > 0
        }
        
        return gpus
    
    def _detect_nvidia_gpus(self) -> List[Dict[str, Any]]:
        """Detect NVIDIA GPUs"""
        gpus = []
        try:
            # Use nvidia-ml-py for comprehensive info
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                gpu_info = {
                    "index": i,
                    "name": pynvml.nvmlDeviceGetName(handle).decode(),
                    "uuid": pynvml.nvmlDeviceGetUUID(handle).decode(),
                    "driver_version": pynvml.nvmlSystemGetDriverVersion().decode(),
                    "vram_mb": pynvml.nvmlDeviceGetMemoryInfo(handle).total // (1024*1024),
                    "power_limit_w": pynvml.nvmlDeviceGetPowerManagementLimit(handle) // 1000,
                    "temperature": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
                    "compute_capability": self._get_compute_capability(handle),
                    "pci_info": self._get_pci_info(handle)
                }
                gpus.append(gpu_info)
            
            pynvml.nvmlShutdown()
        except ImportError:
            # Fallback to nvidia-smi
            gpus = self._detect_nvidia_gpus_via_smi()
        except Exception as e:
            print(f"NVIDIA detection error: {e}")
        
        return gpus
    
    def _detect_nvidia_gpus_via_smi(self) -> List[Dict[str, Any]]:
        """Fallback NVIDIA detection via nvidia-smi"""
        gpus = []
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version,uuid",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        gpus.append({
                            "index": int(parts[0]),
                            "name": parts[1],
                            "vram_mb": int(parts[2]),
                            "driver_version": parts[3],
                            "uuid": parts[4]
                        })
        except:
            pass
        return gpus
    
    def _detect_amd_gpus(self) -> List[Dict[str, Any]]:
        """Detect AMD GPUs"""
        gpus = []
        try:
            # Check for AMD GPUs via rocm-smi
            result = subprocess.run(
                ["rocm-smi", "--showid", "--showmeminfo", "vram"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse rocm-smi output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if "GPU" in line:
                        # Extract GPU info
                        parts = line.split()
                        gpu_info = {
                            "index": int(parts[0]) if parts[0].isdigit() else 0,
                            "name": "AMD GPU",
                            "vram_mb": 0  # Would need more parsing
                        }
                        gpus.append(gpu_info)
        except:
            # Fallback to lspci
            try:
                result = subprocess.run(
                    ["lspci", "-nn"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "AMD" in line and ("VGA" in line or "Display" in line):
                            gpus.append({
                                "name": "AMD GPU (via lspci)",
                                "driver": "amdgpu"
                            })
            except:
                pass
        
        return gpus
    
    def _detect_intel_gpus(self) -> List[Dict[str, Any]]:
        """Detect Intel GPUs (integrated and Arc)"""
        gpus = []
        try:
            # Check for Intel GPUs
            result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "Intel" in line and ("VGA" in line or "Display" in line):
                        # Extract model info
                        model = "Intel GPU"
                        if "UHD" in line:
                            model = "Intel UHD Graphics"
                        elif "Iris" in line:
                            model = "Intel Iris Graphics"
                        elif "Arc" in line:
                            model = "Intel Arc Graphics"
                        
                        gpus.append({
                            "name": model,
                            "driver": "i915",
                            "type": "integrated" if "UHD" in model or "Iris" in model else "discrete"
                        })
        except:
            pass
        
        return gpus
    
    def _detect_storage(self) -> Dict[str, Any]:
        """Enhanced storage detection"""
        storage = {
            "disks": [],
            "partitions": [],
            "total_size_gb": 0,
            "used_gb": 0,
            "free_gb": 0
        }
        
        # Get disk info
        for disk in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                partition_info = {
                    "device": disk.device,
                    "mountpoint": disk.mountpoint,
                    "fstype": disk.fstype,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "percent": usage.percent
                }
                storage["partitions"].append(partition_info)
                storage["total_size_gb"] += partition_info["total_gb"]
                storage["used_gb"] += partition_info["used_gb"]
                storage["free_gb"] += partition_info["free_gb"]
            except:
                pass
        
        # Detect NVMe drives
        try:
            nvme_result = subprocess.run(
                ["nvme", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if nvme_result.returncode == 0:
                storage["nvme_drives"] = nvme_result.stdout.count("/dev/nvme")
        except:
            storage["nvme_drives"] = 0
        
        return storage
    
    def _detect_network(self) -> Dict[str, Any]:
        """Detect network interfaces"""
        network = {
            "interfaces": [],
            "has_internet": False
        }
        
        for interface, addrs in psutil.net_if_addrs().items():
            if_info = {
                "name": interface,
                "addresses": []
            }
            for addr in addrs:
                if_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            network["interfaces"].append(if_info)
        
        # Check internet connectivity
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            network["has_internet"] = True
        except:
            network["has_internet"] = False
        
        return network
    
    def _detect_docker(self) -> Dict[str, Any]:
        """Detect Docker installation and configuration"""
        docker_info = {
            "installed": False,
            "version": None,
            "compose_version": None,
            "running": False,
            "socket_accessible": False
        }
        
        try:
            # Check Docker version
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                docker_info["installed"] = True
                version_match = re.search(r'Docker version ([\d.]+)', result.stdout)
                if version_match:
                    docker_info["version"] = version_match.group(1)
            
            # Check Docker Compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_match = re.search(r'version ([\d.]+)', result.stdout)
                if version_match:
                    docker_info["compose_version"] = version_match.group(1)
            
            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            docker_info["running"] = result.returncode == 0
            
            # Check socket access
            docker_info["socket_accessible"] = os.path.exists("/var/run/docker.sock")
            
        except:
            pass
        
        return docker_info
    
    def _detect_virtualization(self) -> Dict[str, Any]:
        """Detect if running in a VM or container"""
        virt_info = {
            "is_virtual": False,
            "hypervisor": None,
            "container": False,
            "container_runtime": None
        }
        
        try:
            # Check for virtualization
            result = subprocess.run(
                ["systemd-detect-virt"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                virt_type = result.stdout.strip()
                if virt_type and virt_type != "none":
                    virt_info["is_virtual"] = True
                    virt_info["hypervisor"] = virt_type
            
            # Check if in container
            if os.path.exists("/.dockerenv"):
                virt_info["container"] = True
                virt_info["container_runtime"] = "docker"
            elif os.path.exists("/run/.containerenv"):
                virt_info["container"] = True
                virt_info["container_runtime"] = "podman"
            
        except:
            pass
        
        return virt_info
    
    def _get_compute_capability(self, handle) -> Optional[str]:
        """Get CUDA compute capability"""
        try:
            import pynvml
            major = pynvml.nvmlDeviceGetCudaComputeCapability(handle)[0]
            minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)[1]
            return f"{major}.{minor}"
        except:
            return None
    
    def _get_pci_info(self, handle) -> Optional[Dict[str, Any]]:
        """Get PCI info for GPU"""
        try:
            import pynvml
            pci = pynvml.nvmlDeviceGetPciInfo(handle)
            return {
                "bus": pci.bus,
                "device": pci.device,
                "domain": pci.domain,
                "bus_id": pci.busId.decode() if hasattr(pci.busId, 'decode') else str(pci.busId)
            }
        except:
            return None
    
    def calculate_ai_requirements(self) -> SystemRequirements:
        """Calculate what AI services can run on this hardware"""
        warnings = []
        
        # Check GPU availability
        nvidia_gpus = self.hardware["gpus"]["nvidia"]
        total_vram_gb = self.hardware["gpus"]["summary"]["total_vram_gb"]
        
        # Check CPU
        cpu_cores = self.hardware["cpu"]["logical_cores"]
        
        # Check RAM
        total_ram_gb = self.hardware["memory"]["total_gb"]
        available_ram_gb = self.hardware["memory"]["available_gb"]
        
        # Determine LLM capability
        can_run_llm = False
        recommended_backend = "none"
        max_model_size_gb = 0
        recommended_models = []
        gpu_allocation = {}
        
        if nvidia_gpus and total_vram_gb >= 4:
            can_run_llm = True
            
            if total_vram_gb >= 24:
                recommended_backend = "vllm"
                max_model_size_gb = total_vram_gb * 0.9  # Leave 10% headroom
                recommended_models = [
                    "Qwen/Qwen2.5-32B-Instruct-AWQ",
                    "meta-llama/Llama-3.1-70B-Instruct-AWQ",
                    "mistralai/Mixtral-8x7B-Instruct-v0.1"
                ]
                gpu_allocation = {
                    "llm": "GPU 0 (100%)",
                    "tts": "CPU",
                    "stt": "CPU"
                }
            elif total_vram_gb >= 12:
                recommended_backend = "vllm"
                max_model_size_gb = total_vram_gb * 0.9
                recommended_models = [
                    "meta-llama/Llama-3.1-8B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3",
                    "Qwen/Qwen2.5-7B-Instruct"
                ]
                gpu_allocation = {
                    "llm": "GPU 0 (100%)",
                    "tts": "CPU",
                    "stt": "CPU"
                }
            elif total_vram_gb >= 6:
                recommended_backend = "ollama"
                max_model_size_gb = total_vram_gb * 0.8
                recommended_models = [
                    "llama3.1:8b",
                    "mistral:7b",
                    "qwen2.5:7b"
                ]
                gpu_allocation = {
                    "llm": "GPU 0 (80%)",
                    "other": "GPU 0 (20%)"
                }
            else:
                recommended_backend = "ollama"
                max_model_size_gb = 4
                recommended_models = [
                    "phi3:mini",
                    "gemma2:2b",
                    "qwen2.5:1.5b"
                ]
                warnings.append(f"Limited VRAM ({total_vram_gb:.1f}GB) - only small models supported")
        
        elif total_ram_gb >= 16:
            # CPU-only inference
            can_run_llm = True
            recommended_backend = "llama.cpp"
            max_model_size_gb = min(available_ram_gb * 0.7, 13)  # Leave headroom
            recommended_models = [
                "llama3.1:8b-q4_K_M",
                "mistral:7b-q4_K_M",
                "phi3:medium"
            ]
            gpu_allocation = {
                "llm": "CPU only",
                "ram_allocation": f"{max_model_size_gb:.1f}GB"
            }
            warnings.append("No NVIDIA GPU detected - CPU inference will be slower")
        
        else:
            warnings.append(f"Insufficient resources: {total_ram_gb:.1f}GB RAM, {total_vram_gb:.1f}GB VRAM")
        
        # Check for Intel GPU (for TTS acceleration)
        intel_gpus = self.hardware["gpus"]["intel"]
        if intel_gpus:
            gpu_allocation["tts_acceleration"] = "Intel GPU (OpenVINO)"
        
        return SystemRequirements(
            can_run_llm=can_run_llm,
            recommended_llm_backend=recommended_backend,
            max_model_size_gb=max_model_size_gb,
            recommended_models=recommended_models,
            gpu_allocation=gpu_allocation,
            warnings=warnings
        )
    
    def generate_config(self) -> Dict[str, Any]:
        """Generate optimal configuration based on detected hardware"""
        requirements = self.calculate_ai_requirements()
        
        config = {
            "auto_detected": True,
            "detection_timestamp": self.hardware["timestamp"],
            "system_profile": {
                "hostname": self.hardware["system"]["hostname"],
                "total_ram_gb": self.hardware["memory"]["total_gb"],
                "total_vram_gb": self.hardware["gpus"]["summary"]["total_vram_gb"],
                "cpu_cores": self.hardware["cpu"]["logical_cores"],
                "has_nvidia_gpu": self.hardware["gpus"]["summary"]["nvidia_count"] > 0,
                "has_intel_gpu": self.hardware["gpus"]["summary"]["intel_count"] > 0,
                "has_amd_gpu": self.hardware["gpus"]["summary"]["amd_count"] > 0
            },
            "recommended_configuration": {
                "llm_backend": requirements.recommended_llm_backend,
                "max_model_size_gb": requirements.max_model_size_gb,
                "recommended_models": requirements.recommended_models,
                "gpu_allocation": requirements.gpu_allocation,
                "enable_gpu_monitoring": requirements.recommended_llm_backend in ["vllm", "ollama"],
                "enable_model_management": requirements.can_run_llm,
                "warnings": requirements.warnings
            },
            "service_endpoints": self._detect_service_endpoints()
        }
        
        return config
    
    def _detect_service_endpoints(self) -> Dict[str, Optional[str]]:
        """Auto-detect running AI service endpoints"""
        endpoints = {
            "vllm": None,
            "ollama": None,
            "redis": None,
            "postgres": None
        }
        
        # Check common ports
        import socket
        
        checks = [
            ("vllm", "localhost", 8000, "http://localhost:8000"),
            ("ollama", "localhost", 11434, "http://localhost:11434"),
            ("redis", "localhost", 6379, "redis://localhost:6379"),
            ("postgres", "localhost", 5432, "postgresql://localhost:5432")
        ]
        
        for service, host, port, url in checks:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                endpoints[service] = url
        
        return endpoints
    
    def export_json(self, filepath: str):
        """Export hardware info to JSON file"""
        data = {
            "hardware": self.hardware,
            "requirements": asdict(self.calculate_ai_requirements()),
            "suggested_config": self.generate_config()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def export_yaml(self, filepath: str):
        """Export configuration to YAML"""
        import yaml
        config = self.generate_config()
        
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)


# Usage example
if __name__ == "__main__":
    detector = EnhancedHardwareDetector()
    
    # Print summary
    print("System Hardware Detection")
    print("=" * 50)
    print(f"CPU: {detector.hardware['cpu']['model']}")
    print(f"RAM: {detector.hardware['memory']['total_gb']:.1f} GB")
    print(f"GPUs: {detector.hardware['gpus']['summary']['total_gpus']}")
    print(f"Total VRAM: {detector.hardware['gpus']['summary']['total_vram_gb']:.1f} GB")
    
    print("\nAI Service Recommendations")
    print("=" * 50)
    requirements = detector.calculate_ai_requirements()
    print(f"Can run LLM: {requirements.can_run_llm}")
    print(f"Recommended backend: {requirements.recommended_backend}")
    print(f"Max model size: {requirements.max_model_size_gb:.1f} GB")
    print(f"Recommended models: {', '.join(requirements.recommended_models[:3])}")
    
    if requirements.warnings:
        print("\nWarnings:")
        for warning in requirements.warnings:
            print(f"  - {warning}")
    
    # Export configurations
    detector.export_json("hardware_info.json")
    detector.export_yaml("auto_config.yaml")
    print("\nConfiguration exported to hardware_info.json and auto_config.yaml")