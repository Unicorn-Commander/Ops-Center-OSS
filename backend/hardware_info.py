"""
Hardware Information Module
Detects and returns real system hardware information
"""
import subprocess
import re
import os
import json
from typing import Dict, Any, Optional

class HardwareDetector:
    def __init__(self):
        pass
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        try:
            # Get CPU info from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Extract model name
            model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
            model = model_match.group(1).strip() if model_match else "Unknown CPU"
            
            # Get core and thread count
            physical_cores = len(set(re.findall(r'core id\s*:\s*(\d+)', cpuinfo)))
            logical_cores = len(re.findall(r'processor\s*:', cpuinfo))
            
            # Get CPU frequencies from cpufreq
            try:
                base_freq = self._run_command("cat /sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
                if base_freq:
                    base_freq = f"{int(base_freq.strip()) / 1000000:.1f} GHz"
                else:
                    base_freq = "Unknown"
                    
                max_freq = self._run_command("cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
                if max_freq:
                    max_freq = f"{int(max_freq.strip()) / 1000000:.1f} GHz"
                else:
                    max_freq = "Unknown"
            except:
                base_freq = "Unknown"
                max_freq = "Unknown"
            
            return {
                "model": model,
                "cores": physical_cores if physical_cores > 0 else logical_cores // 2,
                "threads": logical_cores,
                "baseFreq": base_freq,
                "maxFreq": max_freq
            }
        except Exception as e:
            return {
                "model": "Unknown CPU",
                "cores": 0,
                "threads": 0,
                "baseFreq": "Unknown",
                "maxFreq": "Unknown"
            }
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get NVIDIA GPU information using nvidia-smi"""
        try:
            # Run nvidia-smi to get detailed GPU info
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.used,temperature.gpu,power.draw,power.limit",
                "--format=csv,noheader,nounits"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0].strip():
                    parts = [part.strip() for part in lines[0].split(',')]
                    if len(parts) >= 3:
                        vram_total_mb = int(parts[2]) if parts[2].isdigit() else 0
                        vram_gb = vram_total_mb / 1024
                        
                        return {
                            "model": parts[0],
                            "vram": f"{vram_gb:.0f} GB GDDR7" if vram_gb > 16 else f"{vram_gb:.0f} GB",
                            "driver": parts[1],
                            "cuda": self._get_cuda_version()
                        }
            
            # Fallback: try nvidia-ml-py if available
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle).decode()
                driver = pynvml.nvmlSystemGetDriverVersion().decode()
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                vram_gb = memory_info.total / (1024**3)
                
                return {
                    "model": name,
                    "vram": f"{vram_gb:.0f} GB",
                    "driver": driver,
                    "cuda": self._get_cuda_version()
                }
            except:
                pass
                
        except Exception as e:
            print(f"GPU detection error: {e}")
        
        return {
            "model": "No NVIDIA GPU detected",
            "vram": "0 GB",
            "driver": "N/A",
            "cuda": "N/A"
        }
    
    def get_igpu_info(self) -> Dict[str, Any]:
        """Get integrated GPU information (Intel or AMD)"""
        try:
            # Check for any VGA/Display controller
            lspci_output = self._run_command("lspci | grep -E '(VGA|Display|3D controller)'")
            
            if lspci_output:
                # Check for Intel GPU
                if "intel" in lspci_output.lower():
                    # Extract Intel GPU model
                    # Try to match patterns like "AlderLake-S GT1", "UHD Graphics 770", etc.
                    intel_match = re.search(r'Intel Corporation\s+([^(\[]+)', lspci_output, re.IGNORECASE)
                    if intel_match:
                        model_text = intel_match.group(1).strip()
                        # Clean up the model name
                        if "Graphics" in model_text:
                            model = f"Intel {model_text}"
                        else:
                            model = f"Intel {model_text}"
                    else:
                        # Fallback to generic
                        model = "Intel Integrated Graphics"
                    
                    # Try to get driver version
                    try:
                        glxinfo = self._run_command("glxinfo | grep 'OpenGL version'")
                        if glxinfo:
                            mesa_match = re.search(r'Mesa\s+([\d.]+)', glxinfo)
                            driver = f"Mesa {mesa_match.group(1)}" if mesa_match else "Mesa (version unknown)"
                        else:
                            # Try alternative: check for i915 driver
                            modinfo = self._run_command("modinfo i915 | grep version:")
                            if modinfo:
                                driver = f"i915 {modinfo.strip().split(':')[-1].strip()}"
                            else:
                                driver = "i915 (version unknown)"
                    except:
                        driver = "Unknown"
                    
                    return {
                        "model": model,
                        "driver": driver
                    }
                
                # Check for AMD GPU
                elif "amd" in lspci_output.lower() or "radeon" in lspci_output.lower():
                    # Extract AMD GPU model
                    amd_match = re.search(r'AMD.*?:\s*([^(\[]+)', lspci_output, re.IGNORECASE)
                    if amd_match:
                        model = f"AMD {amd_match.group(1).strip()}"
                    else:
                        model = "AMD Integrated Graphics"
                    
                    # Try to get driver version
                    try:
                        glxinfo = self._run_command("glxinfo | grep 'OpenGL version'")
                        if glxinfo:
                            mesa_match = re.search(r'Mesa\s+([\d.]+)', glxinfo)
                            driver = f"Mesa {mesa_match.group(1)}" if mesa_match else "Mesa (version unknown)"
                        else:
                            # Try alternative: check for amdgpu driver
                            modinfo = self._run_command("modinfo amdgpu | grep version:")
                            if modinfo:
                                driver = f"amdgpu {modinfo.strip().split(':')[-1].strip()}"
                            else:
                                driver = "amdgpu (version unknown)"
                    except:
                        driver = "Unknown"
                    
                    return {
                        "model": model,
                        "driver": driver
                    }
        except Exception as e:
            print(f"iGPU detection error: {e}")
        
        return {
            "model": "No iGPU detected",
            "driver": "N/A"
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory configuration information"""
        try:
            # Get total memory from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total_match = re.search(r'MemTotal:\s*(\d+)\s*kB', meminfo)
            total_kb = int(mem_total_match.group(1)) if mem_total_match else 0
            total_gb = total_kb / (1024 * 1024)
            
            # Try to get memory type from dmidecode
            try:
                dmidecode_output = self._run_command("sudo dmidecode -t memory | grep -E '(Type|Speed|Size)'", use_sudo=True)
                if dmidecode_output:
                    # Extract memory type (DDR4, DDR5, etc.)
                    type_match = re.search(r'Type:\s*(DDR\d+)', dmidecode_output)
                    mem_type = type_match.group(1) if type_match else "Unknown"
                    
                    # Extract speed
                    speed_match = re.search(r'Speed:\s*(\d+)\s*MT/s', dmidecode_output)
                    speed = f"-{speed_match.group(1)}" if speed_match else ""
                    
                    # Count memory modules
                    size_matches = re.findall(r'Size:\s*(\d+)\s*GB', dmidecode_output)
                    if size_matches:
                        slot_count = len(size_matches)
                        slot_size = size_matches[0] if size_matches else "0"
                        slots = f"{slot_count} x {slot_size}GB"
                    else:
                        slots = "Unknown configuration"
                else:
                    mem_type = "Unknown"
                    speed = ""
                    slots = "Unknown configuration"
            except:
                mem_type = "DDR4"  # Reasonable default
                speed = ""
                slots = "Unknown configuration"
            
            return {
                "total": f"{total_gb:.0f} GB",
                "type": f"{mem_type}{speed}",
                "slots": slots
            }
        except:
            return {
                "total": "Unknown",
                "type": "Unknown",
                "slots": "Unknown configuration"
            }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage device information"""
        try:
            # Get primary storage device info
            lsblk_output = self._run_command("lsblk -d -o NAME,SIZE,TYPE,MODEL | grep -v loop")
            storage_devices = []
            
            if lsblk_output:
                lines = lsblk_output.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == 'disk':
                        device_name = parts[0]
                        size = parts[1]
                        model = ' '.join(parts[3:]) if len(parts) > 3 else 'Unknown'
                        
                        # Try to determine if it's SSD or HDD
                        try:
                            rotational = self._run_command(f"cat /sys/block/{device_name}/queue/rotational")
                            is_ssd = rotational and rotational.strip() == '0'
                            device_type = "NVMe SSD" if "nvme" in device_name else ("SSD" if is_ssd else "HDD")
                        except:
                            device_type = "Unknown"
                        
                        storage_devices.append(f"{size} {device_type}")
            
            if len(storage_devices) >= 1:
                primary = storage_devices[0]
                secondary = storage_devices[1] if len(storage_devices) > 1 else None
            else:
                primary = "Unknown"
                secondary = None
            
            return {
                "primary": primary,
                "secondary": secondary or "None"
            }
        except:
            return {
                "primary": "Unknown",
                "secondary": "None"
            }
    
    def get_os_info(self) -> Dict[str, Any]:
        """Get operating system information"""
        try:
            # Get OS info from /etc/os-release
            os_info = {}
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_info[key] = value.strip('"')
            except:
                pass
            
            name = os_info.get('PRETTY_NAME', os_info.get('NAME', 'Unknown Linux'))
            
            # Get kernel version
            kernel = self._run_command("uname -r")
            kernel = kernel.strip() if kernel else "Unknown"
            
            # Try to detect desktop environment
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', 
                     os.environ.get('DESKTOP_SESSION', 'Unknown'))
            
            # If still unknown, try other methods
            if desktop == 'Unknown':
                if os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                    desktop = 'GNOME'
                elif os.environ.get('KDE_FULL_SESSION'):
                    desktop = 'KDE'
                elif os.environ.get('XFCE4_SESSION'):
                    desktop = 'XFCE'
                else:
                    # Check for common desktop processes
                    ps_output = self._run_command("ps aux | grep -E '(gnome|kde|xfce|plasma)' | head -1")
                    if ps_output:
                        if 'gnome' in ps_output.lower():
                            desktop = 'GNOME'
                        elif 'kde' in ps_output.lower() or 'plasma' in ps_output.lower():
                            desktop = 'KDE Plasma'
                        elif 'xfce' in ps_output.lower():
                            desktop = 'XFCE'
            
            return {
                "name": name,
                "version": os_info.get('VERSION', ''),
                "kernel": kernel,
                "desktop": desktop if desktop != 'Unknown' else 'Server (No GUI)'
            }
        except:
            return {
                "name": "Unknown Linux",
                "version": "",
                "kernel": "Unknown",
                "desktop": "Unknown"
            }
    
    def _get_cuda_version(self) -> str:
        """Get CUDA version"""
        try:
            # Try nvcc first
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_match = re.search(r'release (\d+\.\d+)', result.stdout)
                if version_match:
                    return version_match.group(1)
            
            # Try nvidia-smi
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_match = re.search(r'CUDA Version: (\d+\.\d+)', result.stdout)
                if version_match:
                    return version_match.group(1)
        except:
            pass
        return "Unknown"
    
    def _run_command(self, command: str, use_sudo: bool = False) -> Optional[str]:
        """Run a shell command safely"""
        try:
            if use_sudo:
                # Only allow specific sudo commands for security
                allowed_sudo_commands = ['dmidecode -t memory']
                if not any(allowed_cmd in command for allowed_cmd in allowed_sudo_commands):
                    return None
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.stdout if result.returncode == 0 else None
        except:
            return None
    
    def get_all_hardware_info(self) -> Dict[str, Any]:
        """Get all hardware information"""
        return {
            "cpu": self.get_cpu_info(),
            "gpu": self.get_gpu_info(),
            "igpu": self.get_igpu_info(),
            "memory": self.get_memory_info(),
            "storage": self.get_storage_info(),
            "os": self.get_os_info()
        }

# Global instance
hardware_detector = HardwareDetector()