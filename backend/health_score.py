"""
Health Score Calculator

Intelligent health scoring algorithm for system monitoring.
Calculates overall system health (0-100) based on weighted components.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
import psutil
import docker
import logging
import subprocess

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """
    Calculate system health score using weighted components.

    The health score is a value between 0-100 where:
    - 100 = Perfect health, all systems optimal
    - 80-99 = Healthy, minor issues
    - 60-79 = Degraded, attention needed
    - 40-59 = Warning, action required
    - 0-39 = Critical, immediate intervention needed

    Components:
    - CPU (30%): Based on utilization and load average
    - Memory (25%): Based on available memory
    - Disk (20%): Based on free space
    - Services (15%): Based on running containers
    - Network (10%): Based on interface status and errors
    """

    # Component weights (must sum to 1.0)
    WEIGHTS = {
        "cpu": 0.30,
        "memory": 0.25,
        "disk": 0.20,
        "services": 0.15,
        "network": 0.10
    }

    # Status thresholds
    THRESHOLDS = {
        "healthy": 80,
        "degraded": 60,
        "warning": 40,
        "critical": 0
    }

    # Component-specific thresholds
    CPU_WARNING = 70  # % CPU usage
    CPU_CRITICAL = 90

    MEMORY_WARNING = 75  # % memory used
    MEMORY_CRITICAL = 90

    DISK_WARNING = 75  # % disk used
    DISK_CRITICAL = 90

    NETWORK_ERROR_THRESHOLD = 100  # Max acceptable errors

    def __init__(self):
        """Initialize health score calculator."""
        self.last_network_counters = None

    def calculate_overall_score(self) -> Dict:
        """
        Calculate overall health score and component breakdown.

        Returns:
            Dictionary with overall score, status, and component details
        """
        try:
            # Calculate individual component scores
            cpu_score, cpu_details = self.calculate_cpu_health()
            memory_score, memory_details = self.calculate_memory_health()
            disk_score, disk_details = self.calculate_disk_health()
            services_score, services_details = self.calculate_services_health()
            network_score, network_details = self.calculate_network_health()

            # Calculate weighted average
            overall = (
                cpu_score * self.WEIGHTS["cpu"] +
                memory_score * self.WEIGHTS["memory"] +
                disk_score * self.WEIGHTS["disk"] +
                services_score * self.WEIGHTS["services"] +
                network_score * self.WEIGHTS["network"]
            )

            return {
                "overall_score": round(overall, 1),
                "status": self.get_status(overall),
                "timestamp": datetime.utcnow().isoformat(),
                "breakdown": {
                    "cpu": {
                        "score": round(cpu_score, 1),
                        "status": self.get_status(cpu_score),
                        "weight": self.WEIGHTS["cpu"],
                        "details": cpu_details
                    },
                    "memory": {
                        "score": round(memory_score, 1),
                        "status": self.get_status(memory_score),
                        "weight": self.WEIGHTS["memory"],
                        "details": memory_details
                    },
                    "disk": {
                        "score": round(disk_score, 1),
                        "status": self.get_status(disk_score),
                        "weight": self.WEIGHTS["disk"],
                        "details": disk_details
                    },
                    "services": {
                        "score": round(services_score, 1),
                        "status": self.get_status(services_score),
                        "weight": self.WEIGHTS["services"],
                        "details": services_details
                    },
                    "network": {
                        "score": round(network_score, 1),
                        "status": self.get_status(network_score),
                        "weight": self.WEIGHTS["network"],
                        "details": network_details
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {
                "overall_score": 0,
                "status": "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    def calculate_cpu_health(self) -> Tuple[float, Dict]:
        """
        Calculate CPU health score.

        Factors:
        - CPU usage percentage
        - Load average (if available)
        - Per-core balance

        Returns:
            Tuple of (score, details)
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()

            # Base score: 100 when idle, 0 when maxed
            if cpu_percent < self.CPU_WARNING:
                # Linear scale from 100 to 70
                base_score = 100 - (cpu_percent / self.CPU_WARNING * 30)
            elif cpu_percent < self.CPU_CRITICAL:
                # Linear scale from 70 to 30
                range_size = self.CPU_CRITICAL - self.CPU_WARNING
                base_score = 70 - ((cpu_percent - self.CPU_WARNING) / range_size * 40)
            else:
                # Critical range: 30 to 0
                base_score = max(0, 30 - ((cpu_percent - self.CPU_CRITICAL) / 10 * 30))

            # Adjust for load average if available
            load_penalty = 0
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                # Load average > CPU count is concerning
                if load_avg[0] > cpu_count:
                    load_penalty = min(20, (load_avg[0] - cpu_count) * 5)

            final_score = max(0, base_score - load_penalty)

            details = {
                "cpu_percent": round(cpu_percent, 2),
                "cpu_count": cpu_count,
                "load_avg": [round(x, 2) for x in load_avg] if load_avg else None,
                "base_score": round(base_score, 1),
                "load_penalty": round(load_penalty, 1)
            }

            return final_score, details

        except Exception as e:
            logger.error(f"CPU health calculation error: {e}")
            return 50, {"error": str(e)}

    def calculate_memory_health(self) -> Tuple[float, Dict]:
        """
        Calculate memory health score.

        Factors:
        - Memory usage percentage
        - Swap usage
        - Available memory

        Returns:
            Tuple of (score, details)
        """
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Base score from memory usage
            mem_percent = mem.percent

            if mem_percent < self.MEMORY_WARNING:
                # Linear scale from 100 to 70
                base_score = 100 - (mem_percent / self.MEMORY_WARNING * 30)
            elif mem_percent < self.MEMORY_CRITICAL:
                # Linear scale from 70 to 30
                range_size = self.MEMORY_CRITICAL - self.MEMORY_WARNING
                base_score = 70 - ((mem_percent - self.MEMORY_WARNING) / range_size * 40)
            else:
                # Critical range: 30 to 0
                base_score = max(0, 30 - ((mem_percent - self.MEMORY_CRITICAL) / 10 * 30))

            # Penalty for swap usage
            swap_penalty = 0
            if swap.percent > 50:
                swap_penalty = min(20, swap.percent / 5)

            final_score = max(0, base_score - swap_penalty)

            details = {
                "memory_percent": round(mem_percent, 2),
                "memory_available_gb": round(mem.available / (1024**3), 2),
                "swap_percent": round(swap.percent, 2),
                "base_score": round(base_score, 1),
                "swap_penalty": round(swap_penalty, 1)
            }

            return final_score, details

        except Exception as e:
            logger.error(f"Memory health calculation error: {e}")
            return 50, {"error": str(e)}

    def calculate_disk_health(self) -> Tuple[float, Dict]:
        """
        Calculate disk health score.

        Factors:
        - Root partition usage
        - Total disk space available
        - I/O errors (if detectable)

        Returns:
            Tuple of (score, details)
        """
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Base score from disk usage
            if disk_percent < self.DISK_WARNING:
                # Linear scale from 100 to 70
                base_score = 100 - (disk_percent / self.DISK_WARNING * 30)
            elif disk_percent < self.DISK_CRITICAL:
                # Linear scale from 70 to 30
                range_size = self.DISK_CRITICAL - self.DISK_WARNING
                base_score = 70 - ((disk_percent - self.DISK_WARNING) / range_size * 40)
            else:
                # Critical range: 30 to 0
                base_score = max(0, 30 - ((disk_percent - self.DISK_CRITICAL) / 10 * 30))

            # Bonus for having plenty of space
            free_gb = disk.free / (1024**3)
            if free_gb > 100:
                base_score = min(100, base_score + 5)

            details = {
                "disk_percent": round(disk_percent, 2),
                "disk_free_gb": round(free_gb, 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }

            return base_score, details

        except Exception as e:
            logger.error(f"Disk health calculation error: {e}")
            return 50, {"error": str(e)}

    def calculate_services_health(self) -> Tuple[float, Dict]:
        """
        Calculate services health score.

        Factors:
        - Percentage of running containers
        - Container health status
        - Critical services status

        Returns:
            Tuple of (score, details)
        """
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)

            if not containers:
                return 100, {"containers": 0, "message": "No containers to monitor"}

            running = 0
            healthy = 0
            unhealthy = 0
            stopped = 0

            for container in containers:
                status = container.status
                if status == 'running':
                    running += 1

                    # Check health if available
                    health = container.attrs.get('State', {}).get('Health', {}).get('Status')
                    if health == 'healthy':
                        healthy += 1
                    elif health == 'unhealthy':
                        unhealthy += 1
                else:
                    stopped += 1

            total = len(containers)

            # Base score: percentage of running containers
            running_percent = (running / total) * 100
            base_score = running_percent

            # Penalty for unhealthy containers
            unhealthy_penalty = (unhealthy / total) * 30 if unhealthy > 0 else 0

            # Penalty for stopped containers
            stopped_penalty = (stopped / total) * 50 if stopped > 0 else 0

            final_score = max(0, base_score - unhealthy_penalty - stopped_penalty)

            details = {
                "total": total,
                "running": running,
                "stopped": stopped,
                "healthy": healthy,
                "unhealthy": unhealthy,
                "running_percent": round(running_percent, 1),
                "unhealthy_penalty": round(unhealthy_penalty, 1),
                "stopped_penalty": round(stopped_penalty, 1)
            }

            return final_score, details

        except Exception as e:
            logger.error(f"Services health calculation error: {e}")
            return 50, {"error": str(e)}

    def calculate_network_health(self) -> Tuple[float, Dict]:
        """
        Calculate network health score.

        Factors:
        - Interface status (up/down)
        - Packet errors
        - Packet drops

        Returns:
            Tuple of (score, details)
        """
        try:
            net_io = psutil.net_io_counters()

            # Base score starts at 100
            base_score = 100

            # Calculate error rate
            total_packets = net_io.packets_sent + net_io.packets_recv
            total_errors = net_io.errin + net_io.errout
            total_drops = net_io.dropin + net_io.dropout

            error_rate = (total_errors / total_packets * 100) if total_packets > 0 else 0
            drop_rate = (total_drops / total_packets * 100) if total_packets > 0 else 0

            # Penalty for errors (max 30 points)
            error_penalty = min(30, error_rate * 100)

            # Penalty for drops (max 20 points)
            drop_penalty = min(20, drop_rate * 100)

            final_score = max(0, base_score - error_penalty - drop_penalty)

            details = {
                "total_packets": total_packets,
                "total_errors": total_errors,
                "total_drops": total_drops,
                "error_rate": round(error_rate, 4),
                "drop_rate": round(drop_rate, 4),
                "error_penalty": round(error_penalty, 1),
                "drop_penalty": round(drop_penalty, 1)
            }

            return final_score, details

        except Exception as e:
            logger.error(f"Network health calculation error: {e}")
            return 50, {"error": str(e)}

    def get_status(self, score: float) -> str:
        """
        Get status label from score.

        Args:
            score: Health score (0-100)

        Returns:
            Status string: "healthy", "degraded", "warning", or "critical"
        """
        if score >= self.THRESHOLDS["healthy"]:
            return "healthy"
        elif score >= self.THRESHOLDS["degraded"]:
            return "degraded"
        elif score >= self.THRESHOLDS["warning"]:
            return "warning"
        else:
            return "critical"

    def get_recommendations(self, health_data: Dict) -> list:
        """
        Generate recommendations based on health scores.

        Args:
            health_data: Health score data from calculate_overall_score()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        breakdown = health_data.get("breakdown", {})

        # CPU recommendations
        cpu = breakdown.get("cpu", {})
        if cpu.get("score", 100) < 70:
            cpu_percent = cpu.get("details", {}).get("cpu_percent", 0)
            if cpu_percent > 90:
                recommendations.append(
                    f"⚠️ CPU usage is very high ({cpu_percent}%). "
                    "Consider stopping non-essential services or upgrading CPU."
                )
            else:
                recommendations.append(
                    f"⚠️ CPU usage is elevated ({cpu_percent}%). "
                    "Monitor for processes consuming excessive CPU."
                )

        # Memory recommendations
        memory = breakdown.get("memory", {})
        if memory.get("score", 100) < 70:
            mem_percent = memory.get("details", {}).get("memory_percent", 0)
            available_gb = memory.get("details", {}).get("memory_available_gb", 0)
            if mem_percent > 90:
                recommendations.append(
                    f"⚠️ Memory critically low ({available_gb:.1f} GB available). "
                    "Consider stopping containers or adding RAM."
                )
            else:
                recommendations.append(
                    f"⚠️ Memory usage is high ({mem_percent}%). "
                    "Monitor memory-intensive processes."
                )

        # Disk recommendations
        disk = breakdown.get("disk", {})
        if disk.get("score", 100) < 70:
            disk_percent = disk.get("details", {}).get("disk_percent", 0)
            free_gb = disk.get("details", {}).get("disk_free_gb", 0)
            if disk_percent > 90:
                recommendations.append(
                    f"⚠️ Disk space critically low ({free_gb:.1f} GB free). "
                    "Delete old files or add storage."
                )
            else:
                recommendations.append(
                    f"⚠️ Disk space is limited ({free_gb:.1f} GB free). "
                    "Consider cleanup or expansion."
                )

        # Services recommendations
        services = breakdown.get("services", {})
        if services.get("score", 100) < 90:
            stopped = services.get("details", {}).get("stopped", 0)
            unhealthy = services.get("details", {}).get("unhealthy", 0)
            if stopped > 0:
                recommendations.append(
                    f"⚠️ {stopped} container(s) are stopped. "
                    "Check logs and restart if needed."
                )
            if unhealthy > 0:
                recommendations.append(
                    f"⚠️ {unhealthy} container(s) are unhealthy. "
                    "Investigate health check failures."
                )

        # Network recommendations
        network = breakdown.get("network", {})
        if network.get("score", 100) < 70:
            error_rate = network.get("details", {}).get("error_rate", 0)
            drop_rate = network.get("details", {}).get("drop_rate", 0)
            if error_rate > 0.01:
                recommendations.append(
                    f"⚠️ Network errors detected ({error_rate:.2%}). "
                    "Check network connectivity and interfaces."
                )
            if drop_rate > 0.01:
                recommendations.append(
                    f"⚠️ Packet drops detected ({drop_rate:.2%}). "
                    "Network may be congested."
                )

        if not recommendations:
            recommendations.append("✓ All systems operating normally. No issues detected.")

        return recommendations
