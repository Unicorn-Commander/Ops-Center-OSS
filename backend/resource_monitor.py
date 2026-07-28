"""
Real-time Resource Monitoring for Meeting-Ops
Provides system metrics including AMD GPU stats
"""

import psutil
import subprocess
import re
import json
from typing import Dict, Any
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor system resources including AMD iGPU"""
    
    def __init__(self):
        self.has_radeontop = self._check_radeontop()
        self.has_rocm_smi = self._check_rocm_smi()
        self.has_xrt_smi = self._check_xrt_smi()
    
    def _check_radeontop(self) -> bool:
        """Check if radeontop is available"""
        try:
            result = subprocess.run(['which', 'radeontop'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_rocm_smi(self) -> bool:
        """Check if rocm-smi is available"""
        try:
            result = subprocess.run(['which', 'rocm-smi'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_xrt_smi(self) -> bool:
        """Check if xrt-smi is available for NPU monitoring"""
        try:
            result = subprocess.run(['which', 'xrt-smi'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU usage and stats"""
        return {
            "usage_percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency": {
                "current": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "max": psutil.cpu_freq().max if psutil.cpu_freq() else 0
            },
            "per_core_usage": psutil.cpu_percent(interval=0.1, percpu=True),
            "load_average": os.getloadavg()
        }
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory usage stats"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "ram": {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent": mem.percent,
                "cached_gb": round(mem.cached / (1024**3), 2) if hasattr(mem, 'cached') else 0
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent": swap.percent
            }
        }
    
    def get_amd_gpu_metrics(self) -> Dict[str, Any]:
        """Get AMD GPU metrics using radeontop"""
        metrics = {
            "available": False,
            "usage_percent": 0,
            "vram": {
                "total_mb": 0,
                "used_mb": 0,
                "percent": 0
            },
            "gtt": {
                "total_mb": 0,
                "used_mb": 0,
                "percent": 0
            },
            "temperature_c": 0,
            "frequency_mhz": 0,
            "power_w": 0
        }
        
        if self.has_radeontop:
            try:
                # Run radeontop for 1 sample
                result = subprocess.run(
                    ['radeontop', '-d', '-', '-l', '1'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    metrics["available"] = True
                    
                    # Parse GPU usage
                    gpu_match = re.search(r'gpu\s+([\d.]+)%', output)
                    if gpu_match:
                        metrics["usage_percent"] = float(gpu_match.group(1))
                    
                    # Parse VRAM usage
                    vram_match = re.search(r'vram\s+([\d.]+)%\s+([\d.]+)mb', output, re.IGNORECASE)
                    if vram_match:
                        metrics["vram"]["percent"] = float(vram_match.group(1))
                        metrics["vram"]["used_mb"] = float(vram_match.group(2))
                        # Calculate total VRAM from percentage
                        if metrics["vram"]["percent"] > 0:
                            metrics["vram"]["total_mb"] = int(
                                metrics["vram"]["used_mb"] / (metrics["vram"]["percent"] / 100)
                            )
                        else:
                            # Default to 16GB for AMD UMA systems
                            metrics["vram"]["total_mb"] = 16384
                    
                    # Parse GTT usage
                    gtt_match = re.search(r'gtt\s+([\d.]+)%\s+([\d.]+)mb', output, re.IGNORECASE)
                    if gtt_match:
                        metrics["gtt"]["percent"] = float(gtt_match.group(1))
                        metrics["gtt"]["used_mb"] = float(gtt_match.group(2))
                        if metrics["gtt"]["percent"] > 0:
                            metrics["gtt"]["total_mb"] = int(
                                metrics["gtt"]["used_mb"] / (metrics["gtt"]["percent"] / 100)
                            )
                    
                    # Parse clocks
                    sclk_match = re.search(r'sclk\s+[\d.]+%\s+([\d.]+)ghz', output, re.IGNORECASE)
                    if sclk_match:
                        metrics["frequency_mhz"] = int(float(sclk_match.group(1)) * 1000)
                    
            except Exception as e:
                print(f"Error getting AMD GPU metrics: {e}")
        
        # Try to get temperature from hwmon
        try:
            for root, dirs, files in os.walk('/sys/class/hwmon'):
                for file in files:
                    if file == 'name':
                        path = os.path.join(root, file)
                        with open(path, 'r') as f:
                            if 'amdgpu' in f.read():
                                temp_file = os.path.join(root, 'temp1_input')
                                if os.path.exists(temp_file):
                                    with open(temp_file, 'r') as tf:
                                        metrics["temperature_c"] = int(tf.read()) / 1000
                                        break
        except:
            pass
        
        return metrics
    
    def get_npu_metrics(self) -> Dict[str, Any]:
        """Get NPU metrics using xrt-smi"""
        metrics = {
            "available": False,
            "device_name": "Phoenix NPU",
            "generation": "XDNA1",
            "tops": 16,
            "sram": {
                "total_mb": 0,
                "used_mb": 0,
                "percent": 0
            },
            "utilization_percent": 0,
            "temperature_c": 0,
            "power_w": 0,
            "frequency_mhz": 0
        }
        
        if self.has_xrt_smi:
            try:
                # Run xrt-smi examine command for device info
                result = subprocess.run(
                    ['xrt-smi', 'examine', '-r', 'platform'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    metrics["available"] = True
                    
                    # Parse NPU device info
                    if 'Phoenix' in output or 'XDNA' in output:
                        metrics["device_name"] = "AMD Phoenix NPU"
                    
                    # Get memory/SRAM usage
                    mem_result = subprocess.run(
                        ['xrt-smi', 'examine', '-r', 'mem'],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    
                    if mem_result.returncode == 0:
                        mem_output = mem_result.stdout
                        
                        # Parse SRAM usage from memory output
                        # Looking for patterns like "SRAM: 4096 MB total, 512 MB used"
                        sram_total_match = re.search(r'SRAM.*?(\d+)\s*MB\s*total', mem_output, re.IGNORECASE)
                        sram_used_match = re.search(r'SRAM.*?(\d+)\s*MB\s*used', mem_output, re.IGNORECASE)
                        
                        if sram_total_match:
                            metrics["sram"]["total_mb"] = int(sram_total_match.group(1))
                        if sram_used_match:
                            metrics["sram"]["used_mb"] = int(sram_used_match.group(1))
                        
                        # Calculate percentage if we have both values
                        if metrics["sram"]["total_mb"] > 0:
                            metrics["sram"]["percent"] = round(
                                (metrics["sram"]["used_mb"] / metrics["sram"]["total_mb"]) * 100, 1
                            )
                    
                    # Get utilization stats
                    util_result = subprocess.run(
                        ['xrt-smi', 'examine', '-r', 'aie'],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    
                    if util_result.returncode == 0:
                        util_output = util_result.stdout
                        
                        # Parse AIE utilization
                        util_match = re.search(r'Utilization.*?(\d+)%', util_output)
                        if util_match:
                            metrics["utilization_percent"] = int(util_match.group(1))
                        
                        # Parse frequency
                        freq_match = re.search(r'Frequency.*?(\d+)\s*MHz', util_output)
                        if freq_match:
                            metrics["frequency_mhz"] = int(freq_match.group(1))
                        
                        # Parse temperature if available
                        temp_match = re.search(r'Temperature.*?(\d+\.?\d*)\s*C', util_output)
                        if temp_match:
                            metrics["temperature_c"] = float(temp_match.group(1))
                        
                        # Parse power if available
                        power_match = re.search(r'Power.*?(\d+\.?\d*)\s*W', util_output)
                        if power_match:
                            metrics["power_w"] = float(power_match.group(1))
                    
            except subprocess.TimeoutExpired:
                logger.warning("xrt-smi command timed out")
            except Exception as e:
                logger.error(f"Error getting NPU metrics: {e}")
        
        # Alternative: try to read from sysfs if xrt-smi not available
        if not metrics["available"]:
            try:
                # Check for NPU device nodes
                if os.path.exists('/dev/accel/accel0'):
                    metrics["available"] = True
                    metrics["device_name"] = "AMD NPU (detected via device node)"
                    
                    # Try to read SRAM info from sysfs
                    sysfs_paths = [
                        '/sys/class/accel/accel0/device/memory_info',
                        '/sys/devices/platform/aie2/memory_info',
                        '/sys/kernel/debug/amdxdna/memory_info'
                    ]
                    
                    for path in sysfs_paths:
                        if os.path.exists(path):
                            try:
                                with open(path, 'r') as f:
                                    mem_info = f.read()
                                    # Parse memory info
                                    total_match = re.search(r'total:\s*(\d+)', mem_info)
                                    used_match = re.search(r'used:\s*(\d+)', mem_info)
                                    if total_match and used_match:
                                        total_bytes = int(total_match.group(1))
                                        used_bytes = int(used_match.group(1))
                                        metrics["sram"]["total_mb"] = total_bytes // (1024 * 1024)
                                        metrics["sram"]["used_mb"] = used_bytes // (1024 * 1024)
                                        if metrics["sram"]["total_mb"] > 0:
                                            metrics["sram"]["percent"] = round(
                                                (metrics["sram"]["used_mb"] / metrics["sram"]["total_mb"]) * 100, 1
                                            )
                                        break
                            except:
                                pass
            except Exception as e:
                logger.debug(f"NPU sysfs detection failed: {e}")
        
        return metrics
    
    def get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk usage stats"""
        disks = []
        
        # Always include root partition
        try:
            usage = psutil.disk_usage('/')
            disks.append({
                "mount": "/",
                "device": "overlay",
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            })
        except:
            pass
        
        # Add other partitions if different
        for partition in psutil.disk_partitions():
            if partition.mountpoint in ['/home', '/var', '/tmp'] and partition.mountpoint != '/':
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "mount": partition.mountpoint,
                        "device": partition.device,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    })
                except:
                    pass
        
        # Get disk I/O stats
        io_counters = psutil.disk_io_counters()
        if io_counters:
            io_stats = {
                "read_mb_s": 0,  # Would need to track over time
                "write_mb_s": 0,
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count
            }
        else:
            io_stats = {}
        
        return {
            "partitions": disks,
            "io": io_stats
        }
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get network stats"""
        net_io = psutil.net_io_counters()
        
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        }
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """Get top processes by CPU and memory"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 0:
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent']
                    })
            except:
                pass
        
        # Sort by CPU usage and get top 10
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return {
            "top_cpu": processes[:5],
            "total_processes": len(processes),
            "running": len([p for p in processes if p['cpu_percent'] > 0])
        }
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all system metrics"""
        return {
            "timestamp": psutil.boot_time(),
            "uptime_seconds": int(psutil.time.time() - psutil.boot_time()),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "gpu": self.get_amd_gpu_metrics(),
            "npu": self.get_npu_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "processes": self.get_process_metrics()
        }
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        gpu = self.get_amd_gpu_metrics()
        npu = self.get_npu_metrics()
        
        return {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "gpu_percent": gpu["usage_percent"],
            "gpu_memory_percent": gpu["vram"]["percent"],
            "gpu_temperature_c": gpu["temperature_c"],
            "npu_percent": npu["utilization_percent"],
            "npu_sram_percent": npu["sram"]["percent"],
            "npu_available": npu["available"],
            "healthy": cpu < 90 and mem.percent < 90
        }

# Global instance
monitor = ResourceMonitor()