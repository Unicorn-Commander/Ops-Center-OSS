"""
Universal Hardware Detector for Ops Center
Detects and configures for UC-1-Pro, UC-1, and Meeting-Ops platforms
"""

import subprocess
import os
import re
import json
import platform
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    name: str
    gpu_type: str
    capabilities: List[str]
    recommended_backend: str
    max_models: int
    features: Dict[str, bool]

class UniversalHardwareDetector:
    """Universal hardware detection for all UC platforms"""
    
    # Platform definitions
    PLATFORMS = {
        "UC-1-Pro": {
            "gpu_patterns": ["RTX 4090", "RTX 4080", "A100", "H100", "A6000"],
            "min_vram_gb": 24,
            "features": ["vllm", "high_throughput", "multi_gpu"]
        },
        "Meeting-Ops": {
            "gpu_patterns": ["780M", "680M", "Phoenix", "Rembrandt", "Phoenix3"],
            "cpu_patterns": ["7840", "7940", "8840", "8940", "8945", "6800"],
            "features": ["vulkan", "npu", "real_time", "igpu"]
        },
        "UC-1": {
            "gpu_patterns": ["Arc", "UHD", "RTX 30", "RTX 20", "RX"],
            "features": ["balanced", "ollama", "general_purpose"]
        }
    }
    
    def __init__(self):
        self.platform = None
        self.hardware = {}
        self.detect_all()
    
    def detect_all(self):
        """Detect all hardware and determine platform"""
        self.hardware = {
            "system": self._detect_system(),
            "cpu": self._detect_cpu(),
            "memory": self._detect_memory(),
            "gpus": self._detect_gpus(),
            "npu": self._detect_npu(),
            "storage": self._detect_storage()
        }
        
        # Determine platform based on detected hardware
        self.platform = self._determine_platform()
        
        # Add platform-specific configuration
        self.hardware["platform"] = self._get_platform_config()
        self.hardware["capabilities"] = self._calculate_capabilities()
    
    def _detect_system(self) -> Dict[str, Any]:
        """Detect system information"""
        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "kernel": platform.release(),
            "python_version": platform.python_version()
        }
    
    def _detect_cpu(self) -> Dict[str, Any]:
        """Detect CPU information"""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "model": "Unknown",
            "vendor": "Unknown"
        }
        
        try:
            # Get CPU info from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_info["model"] = line.split(':')[1].strip()
                        
                        # Detect vendor
                        if "Intel" in cpu_info["model"]:
                            cpu_info["vendor"] = "Intel"
                        elif "AMD" in cpu_info["model"]:
                            cpu_info["vendor"] = "AMD"
                        break
            
            # Check for specific CPU features
            cpu_info["features"] = self._detect_cpu_features()
            
        except Exception as e:
            pass
        
        return cpu_info
    
    def _detect_cpu_features(self) -> List[str]:
        """Detect CPU features relevant for AI workloads"""
        features = []
        
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                
                # Check for important instruction sets
                if 'avx512' in cpuinfo:
                    features.append("AVX512")
                elif 'avx2' in cpuinfo:
                    features.append("AVX2")
                elif 'avx' in cpuinfo:
                    features.append("AVX")
                
                if 'sse4' in cpuinfo:
                    features.append("SSE4")
                
                # Check for AI-specific features
                if 'amx' in cpuinfo:
                    features.append("AMX")  # Intel Advanced Matrix Extensions
                if 'vnni' in cpuinfo:
                    features.append("VNNI")  # Vector Neural Network Instructions
        except:
            pass
        
        return features
    
    def _detect_gpus(self) -> Dict[str, Any]:
        """Detect all GPU types"""
        gpus = {
            "nvidia": self._detect_nvidia_gpus(),
            "amd": self._detect_amd_gpus(),
            "intel": self._detect_intel_gpus(),
            "summary": {}
        }
        
        # Calculate summary
        total_gpus = len(gpus["nvidia"]) + len(gpus["amd"]) + len(gpus["intel"])
        gpus["summary"] = {
            "total_count": total_gpus,
            "primary_gpu": self._determine_primary_gpu(gpus),
            "multi_gpu": total_gpus > 1
        }
        
        return gpus
    
    def _detect_nvidia_gpus(self) -> List[Dict[str, Any]]:
        """Detect NVIDIA GPUs"""
        gpus = []
        
        try:
            # Try nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(',')
                        gpus.append({
                            "name": parts[0].strip(),
                            "vram_mb": int(float(parts[1].strip())) if len(parts) > 1 else 0,
                            "compute_capability": parts[2].strip() if len(parts) > 2 else "unknown",
                            "vendor": "NVIDIA"
                        })
        except:
            pass
        
        return gpus
    
    def _detect_amd_gpus(self) -> List[Dict[str, Any]]:
        """Detect AMD GPUs including integrated"""
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
                    if re.search(r'(AMD|ATI).*VGA|VGA.*AMD|Display.*AMD', line, re.IGNORECASE):
                        # Extract model information
                        model = "AMD GPU"
                        is_integrated = False
                        compute_units = 0
                        
                        # Check for specific models
                        if "780M" in line or "Phoenix" in line or "Rembrandt" in line:
                            if "Phoenix" in line or "Phoenix3" in line:
                                model = "AMD Radeon 780M"
                                compute_units = 12
                            else:
                                model = "AMD Radeon 680M" 
                                compute_units = 8
                            is_integrated = True
                        elif re.search(r'RX \d+', line):
                            match = re.search(r'RX \d+', line)
                            model = f"AMD Radeon {match.group()}"
                        
                        gpu_info = {
                            "name": model,
                            "vendor": "AMD",
                            "integrated": is_integrated,
                            "vulkan_support": True,
                            "rocm_compatible": self._check_rocm_support(model),
                            "pci_info": line.strip()
                        }
                        
                        if is_integrated:
                            gpu_info["compute_units"] = compute_units
                            gpu_info["architecture"] = "RDNA3" if "780M" in model else "RDNA2"
                            gpu_info["memory_info"] = self._get_igpu_memory_info()
                            gpu_info["metrics"] = self._get_amd_gpu_metrics()
                        
                        gpus.append(gpu_info)
        except:
            pass
        
        return gpus
    
    def _detect_intel_gpus(self) -> List[Dict[str, Any]]:
        """Detect Intel GPUs including Arc and integrated"""
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
                        model = "Intel GPU"
                        gpu_type = "integrated"
                        
                        if "Arc" in line:
                            model = "Intel Arc Graphics"
                            gpu_type = "discrete"
                        elif "Iris" in line:
                            model = "Intel Iris Graphics"
                        elif "UHD" in line:
                            model = "Intel UHD Graphics"
                        
                        gpus.append({
                            "name": model,
                            "vendor": "Intel",
                            "type": gpu_type,
                            "level_zero_support": True
                        })
        except:
            pass
        
        return gpus
    
    def _detect_npu(self) -> Dict[str, Any]:
        """Detect NPU (Neural Processing Unit)"""
        npu_info = {
            "detected": False,
            "vendor": None,
            "model": None
        }
        
        # Check for AMD NPU via lspci
        try:
            result = subprocess.run(
                ["lspci"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "AMD IPU Device" in line or ("Signal processing controller" in line and "AMD" in line):
                        npu_info["detected"] = True
                        npu_info["vendor"] = "AMD"
                        npu_info["model"] = "Phoenix NPU (XDNA1)"
                        npu_info["tops"] = 16  # 16 TOPS for Phoenix
                        npu_info["architecture"] = "XDNA1"
                        npu_info["pci_info"] = line.strip()
                        break
        except:
            pass
        
        # Get CPU model for fallback checks
        cpu_model = self.hardware.get("cpu", {}).get("model", "")
        
        # Fallback: Check by CPU model (Phoenix/Hawk Point)
        if not npu_info["detected"]:
            if any(x in cpu_model for x in ["7840", "7940", "8840", "8940", "8945"]):
                npu_info["detected"] = True
                npu_info["vendor"] = "AMD"
                npu_info["model"] = "Ryzen AI (XDNA1)"
                npu_info["tops"] = 16  # 16 TOPS for Phoenix
        
        # Check for Intel NPU (Meteor Lake)
        if not npu_info["detected"] and "Core Ultra" in cpu_model:
            npu_info["detected"] = True
            npu_info["vendor"] = "Intel"
            npu_info["model"] = "Intel AI Boost"
            npu_info["tops"] = 11  # Varies by model
        
        # Check for NPU device files
        if os.path.exists("/dev/npu") or os.path.exists("/dev/xdna"):
            npu_info["device_available"] = True
        
        # Get NPU metrics and SRAM usage
        npu_info["metrics"] = self._get_npu_metrics()
        
        return npu_info
    
    def _detect_memory(self) -> Dict[str, Any]:
        """Detect system memory"""
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        }
    
    def _detect_storage(self) -> Dict[str, Any]:
        """Detect storage information"""
        storage = {}
        
        for partition in psutil.disk_partitions():
            if partition.mountpoint == '/':
                usage = psutil.disk_usage(partition.mountpoint)
                storage = {
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent
                }
                break
        
        return storage
    
    def _get_igpu_memory_info(self) -> Dict[str, Any]:
        """Get AMD iGPU memory information (GTT and VRAM)"""
        memory_info = {
            "gtt_total_mb": 0,
            "gtt_used_mb": 0,
            "vram_total_mb": 0,
            "vram_used_mb": 0,
            "shared_system_memory": True
        }
        
        try:
            # Check DRM memory info
            for root, dirs, files in os.walk('/sys/class/drm'):
                for dir_name in dirs:
                    if 'card' in dir_name and 'render' not in dir_name:
                        card_path = os.path.join(root, dir_name)
                        
                        # Check if it's AMD
                        device_path = os.path.join(card_path, 'device')
                        if os.path.exists(device_path):
                            try:
                                with open(os.path.join(device_path, 'vendor'), 'r') as f:
                                    vendor = f.read().strip()
                                    
                                if vendor == "0x1002":  # AMD vendor ID
                                    # Try to get memory info from amdgpu
                                    mem_info_path = os.path.join(card_path, 'device', 'mem_info_gtt_total')
                                    if os.path.exists(mem_info_path):
                                        with open(mem_info_path, 'r') as f:
                                            memory_info["gtt_total_mb"] = int(f.read().strip()) // (1024 * 1024)
                                    
                                    mem_used_path = os.path.join(card_path, 'device', 'mem_info_gtt_used')
                                    if os.path.exists(mem_used_path):
                                        with open(mem_used_path, 'r') as f:
                                            memory_info["gtt_used_mb"] = int(f.read().strip()) // (1024 * 1024)
                                    
                                    # VRAM info (usually small for iGPU)
                                    vram_total_path = os.path.join(card_path, 'device', 'mem_info_vram_total')
                                    if os.path.exists(vram_total_path):
                                        with open(vram_total_path, 'r') as f:
                                            memory_info["vram_total_mb"] = int(f.read().strip()) // (1024 * 1024)
                                    
                                    vram_used_path = os.path.join(card_path, 'device', 'mem_info_vram_used')
                                    if os.path.exists(vram_used_path):
                                        with open(vram_used_path, 'r') as f:
                                            memory_info["vram_used_mb"] = int(f.read().strip()) // (1024 * 1024)
                                    break
                            except:
                                continue
        except:
            pass
        
        # Fallback: Try radeontop for VRAM/GTT info
        try:
            result = subprocess.run(
                ["radeontop", "-d", "-", "-l", "1"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse VRAM usage: "vram 98.76% 16105.27mb"
                vram_match = re.search(r'vram\s+([\d\.]+)%\s+([\d\.]+)mb', output, re.IGNORECASE)
                if vram_match:
                    vram_percent = float(vram_match.group(1))
                    vram_used_mb = float(vram_match.group(2))
                    vram_total_mb = vram_used_mb / (vram_percent / 100) if vram_percent > 0 else 0
                    
                    memory_info["vram_total_mb"] = int(vram_total_mb)
                    memory_info["vram_used_mb"] = int(vram_used_mb)
                    memory_info["vram_percent"] = vram_percent
                
                # Parse GTT usage: "gtt 18.61% 7249.91mb"  
                gtt_match = re.search(r'gtt\s+([\d\.]+)%\s+([\d\.]+)mb', output, re.IGNORECASE)
                if gtt_match:
                    gtt_percent = float(gtt_match.group(1))
                    gtt_used_mb = float(gtt_match.group(2))
                    gtt_total_mb = gtt_used_mb / (gtt_percent / 100) if gtt_percent > 0 else 0
                    
                    memory_info["gtt_total_mb"] = int(gtt_total_mb)
                    memory_info["gtt_used_mb"] = int(gtt_used_mb)
                    memory_info["gtt_percent"] = gtt_percent
        except:
            pass
        
        return memory_info
    
    def _get_amd_gpu_metrics(self) -> Dict[str, Any]:
        """Get AMD GPU performance metrics"""
        metrics = {
            "usage_percent": 0,
            "temperature_c": 0,
            "frequency_mhz": 0,
            "power_usage_w": 0
        }
        
        try:
            # Try to get metrics from sysfs
            for root, dirs, files in os.walk('/sys/class/hwmon'):
                for file in files:
                    if file == 'name':
                        path = os.path.join(root, file)
                        with open(path, 'r') as f:
                            if 'amdgpu' in f.read():
                                # Temperature
                                temp_file = os.path.join(root, 'temp1_input')
                                if os.path.exists(temp_file):
                                    with open(temp_file, 'r') as tf:
                                        metrics["temperature_c"] = int(tf.read()) / 1000
                                
                                # Power usage
                                power_file = os.path.join(root, 'power1_average')
                                if os.path.exists(power_file):
                                    with open(power_file, 'r') as pf:
                                        metrics["power_usage_w"] = int(pf.read()) / 1000000
                                break
            
            # Try radeontop for usage and detailed metrics
            result = subprocess.run(
                ["radeontop", "-d", "-", "-l", "1"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse GPU utilization
                gpu_match = re.search(r'gpu\s+(\d+\.?\d*)%', output)
                if gpu_match:
                    metrics["usage_percent"] = float(gpu_match.group(1))
                
                # Parse memory clocks (mclk and sclk)
                mclk_match = re.search(r'mclk\s+\d+\.\d+%\s+([\d\.]+)ghz', output, re.IGNORECASE)
                if mclk_match:
                    metrics["memory_clock_ghz"] = float(mclk_match.group(1))
                
                sclk_match = re.search(r'sclk\s+\d+\.\d+%\s+([\d\.]+)ghz', output, re.IGNORECASE)  
                if sclk_match:
                    metrics["core_clock_ghz"] = float(sclk_match.group(1))
                    metrics["frequency_mhz"] = int(float(sclk_match.group(1)) * 1000)
        except:
            pass
        
        return metrics
    
    def _get_npu_metrics(self) -> Dict[str, Any]:
        """Get NPU performance metrics and SRAM usage"""
        metrics = {
            "usage_percent": 0,
            "sram_total_mb": 0,
            "sram_used_mb": 0,
            "inference_fps": 0,
            "power_usage_w": 0,
            "temperature_c": 0,
            "available": False
        }
        
        try:
            # Check for XDNA device
            if os.path.exists("/dev/xdna0"):
                metrics["available"] = True
                
                # Try to get NPU metrics from sysfs
                for root, dirs, files in os.walk('/sys/devices'):
                    if 'amdxdna' in root or 'npu' in root.lower():
                        # Look for SRAM information
                        sram_file = os.path.join(root, 'sram_size')
                        if os.path.exists(sram_file):
                            try:
                                with open(sram_file, 'r') as f:
                                    metrics["sram_total_mb"] = int(f.read().strip()) // (1024 * 1024)
                            except:
                                pass
                        
                        # Look for usage information
                        usage_file = os.path.join(root, 'sram_usage')
                        if os.path.exists(usage_file):
                            try:
                                with open(usage_file, 'r') as f:
                                    metrics["sram_used_mb"] = int(f.read().strip()) // (1024 * 1024)
                            except:
                                pass
                        
                        # Look for utilization
                        util_file = os.path.join(root, 'utilization')
                        if os.path.exists(util_file):
                            try:
                                with open(util_file, 'r') as f:
                                    metrics["usage_percent"] = float(f.read().strip())
                            except:
                                pass
                        break
                
                # Fallback: Set typical Phoenix NPU SRAM size if not detected
                if metrics["sram_total_mb"] == 0:
                    metrics["sram_total_mb"] = 50  # Phoenix NPU typically has ~50MB SRAM
        except:
            pass
        
        return metrics
    
    def _check_rocm_support(self, model: str) -> bool:
        """Check if GPU supports ROCm"""
        # List of GPUs known to work with ROCm
        rocm_compatible = [
            "780M", "680M",  # Integrated
            "RX 7900", "RX 7800", "RX 7700", "RX 7600",  # RDNA3
            "RX 6900", "RX 6800", "RX 6700", "RX 6600",  # RDNA2
            "MI250", "MI210", "MI100"  # Instinct
        ]
        
        return any(gpu in model for gpu in rocm_compatible)
    
    def _determine_primary_gpu(self, gpus: Dict) -> Optional[Dict[str, Any]]:
        """Determine the primary GPU to use"""
        # Priority: NVIDIA discrete > AMD discrete > Intel Arc > AMD integrated > Intel integrated
        
        if gpus["nvidia"]:
            return gpus["nvidia"][0]
        
        for gpu in gpus["amd"]:
            if not gpu.get("integrated", False):
                return gpu
        
        for gpu in gpus["intel"]:
            if gpu.get("type") == "discrete":
                return gpu
        
        if gpus["amd"]:
            return gpus["amd"][0]
        
        if gpus["intel"]:
            return gpus["intel"][0]
        
        return None
    
    def _determine_platform(self) -> str:
        """Determine which platform this is"""
        # Check for UC-1-Pro indicators
        nvidia_gpus = self.hardware["gpus"]["nvidia"]
        for gpu in nvidia_gpus:
            for pattern in self.PLATFORMS["UC-1-Pro"]["gpu_patterns"]:
                if pattern in gpu.get("name", ""):
                    if gpu.get("vram_mb", 0) >= self.PLATFORMS["UC-1-Pro"]["min_vram_gb"] * 1024:
                        return "UC-1-Pro"
        
        # Check for Meeting-Ops indicators
        amd_gpus = self.hardware["gpus"]["amd"]
        cpu_model = self.hardware["cpu"]["model"]
        
        for gpu in amd_gpus:
            for pattern in self.PLATFORMS["Meeting-Ops"]["gpu_patterns"]:
                if pattern in gpu.get("name", ""):
                    return "Meeting-Ops"
        
        for pattern in self.PLATFORMS["Meeting-Ops"]["cpu_patterns"]:
            if pattern in cpu_model:
                return "Meeting-Ops"
        
        # Default to UC-1 for everything else
        return "UC-1"
    
    def _get_platform_config(self) -> PlatformConfig:
        """Get platform-specific configuration"""
        configs = {
            "UC-1-Pro": PlatformConfig(
                name="UC-1-Pro",
                gpu_type="high-end-discrete",
                capabilities=["vllm", "high_throughput", "multi_model", "training"],
                recommended_backend="vllm",
                max_models=8,
                features={
                    "vllm": True,
                    "ollama": True,
                    "llamacpp": True,
                    "tensorrt": True
                }
            ),
            "Meeting-Ops": PlatformConfig(
                name="Meeting-Ops",
                gpu_type="amd-igpu",
                capabilities=["real_time", "vulkan", "npu", "edge"],
                recommended_backend="llamacpp",
                max_models=2,
                features={
                    "vllm": False,
                    "ollama": True,
                    "llamacpp": True,
                    "tensorrt": False
                }
            ),
            "UC-1": PlatformConfig(
                name="UC-1",
                gpu_type="mixed",
                capabilities=["balanced", "general_purpose"],
                recommended_backend="ollama",
                max_models=4,
                features={
                    "vllm": False,
                    "ollama": True,
                    "llamacpp": True,
                    "tensorrt": False
                }
            )
        }
        
        return asdict(configs.get(self.platform, configs["UC-1"]))
    
    def _calculate_capabilities(self) -> Dict[str, Any]:
        """Calculate system capabilities based on hardware"""
        primary_gpu = self.hardware["gpus"]["summary"]["primary_gpu"]
        memory_gb = self.hardware["memory"]["total_gb"]
        
        caps = {
            "platform": self.platform,
            "recommended_backends": [],
            "max_model_size_gb": 0,
            "features": []
        }
        
        # Platform-specific recommendations
        if self.platform == "UC-1-Pro":
            caps["recommended_backends"] = ["vllm", "tensorrt-llm", "ollama"]
            caps["max_model_size_gb"] = min(primary_gpu.get("vram_mb", 0) / 1024 * 0.9, 70)
            caps["features"] = ["multi_gpu", "training", "high_batch_size"]
            
        elif self.platform == "Meeting-Ops":
            caps["recommended_backends"] = ["llamacpp", "ollama"]
            caps["max_model_size_gb"] = min((memory_gb - 8) * 0.5, 8)
            caps["features"] = ["vulkan", "real_time", "edge_deployment"]
            
            if self.hardware["npu"]["detected"]:
                caps["features"].append("npu_acceleration")
        
        else:  # UC-1
            caps["recommended_backends"] = ["ollama", "llamacpp"]
            caps["max_model_size_gb"] = min((memory_gb - 4) * 0.5, 13)
            caps["features"] = ["balanced", "flexible"]
        
        return caps
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary for Ops Center"""
        return {
            "platform": self.platform,
            "hardware": self.hardware,
            "configuration": self.hardware["platform"],
            "capabilities": self.hardware["capabilities"]
        }
    
    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration based on platform"""
        config = {
            "compose_file": "docker-compose.yml",
            "environment": {},
            "devices": []
        }
        
        if self.platform == "UC-1-Pro":
            config["compose_file"] = "docker-compose.yml"
            config["environment"] = {
                "ENABLE_VLLM": "true",
                "LLM_BACKEND": "vllm",
                "GPU_MEMORY_FRACTION": "0.95"
            }
            config["devices"] = ["nvidia"]
            
        elif self.platform == "Meeting-Ops":
            config["compose_file"] = "docker-compose.uc-meeting-ops.yml"
            config["environment"] = {
                "ENABLE_VLLM": "false",
                "LLM_BACKEND": "llamacpp",
                "HSA_OVERRIDE_GFX_VERSION": "11.0.0",
                "GPU_BACKEND": "vulkan"
            }
            config["devices"] = ["amd"]
            
        else:  # UC-1
            config["compose_file"] = "docker-compose.uc1.yml"
            config["environment"] = {
                "ENABLE_VLLM": "false",
                "LLM_BACKEND": "ollama"
            }
            config["devices"] = ["auto"]
        
        return config

# Export function for integration
def detect_and_configure():
    """Main entry point for detection and configuration"""
    detector = UniversalHardwareDetector()
    return detector.get_summary(), detector.get_docker_config()