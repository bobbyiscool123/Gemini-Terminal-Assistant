"""
System Statistics Module
Provides system resource monitoring for CPU, memory, disk, and network
"""
import os
import platform
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import logging

# Setup logging
logger = logging.getLogger(__name__)

class SystemStats:
    """System statistics monitoring utility"""
    
    def __init__(self, refresh_interval: int = 5):
        """Initialize system statistics monitor"""
        self.refresh_interval = refresh_interval  # seconds
        self.monitoring_thread = None
        self.is_monitoring = False
        self.stats = {}
        self.callbacks = []
        self._last_network_io = None
        self._last_disk_io = None
        self._last_io_time = None
        
    def start_monitoring(self) -> bool:
        """Start monitoring system statistics in background"""
        if self.is_monitoring:
            return True
            
        def monitor_loop():
            self.is_monitoring = True
            while self.is_monitoring:
                try:
                    # Update all stats
                    self.stats = self._collect_stats()
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(self.stats)
                        except Exception as e:
                            logger.error(f"Error in system stats callback: {e}")
                            
                    # Sleep until next update
                    time.sleep(self.refresh_interval)
                except Exception as e:
                    logger.error(f"Error collecting system stats: {e}")
                    time.sleep(1)  # Sleep briefly before retry
        
        self.monitoring_thread = threading.Thread(target=monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        return True
        
    def stop_monitoring(self) -> None:
        """Stop monitoring system statistics"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get the most recent system statistics"""
        if not self.stats:
            self.stats = self._collect_stats()
        return self.stats
        
    def get_current_stats(self) -> Dict[str, Any]:
        """Alias for get_stats() - returns the most recent system statistics"""
        return self.get_stats()
        
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a callback function to be notified of stat updates"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """Remove a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
            
    def _collect_stats(self) -> Dict[str, Any]:
        """Collect system statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "system": self._get_system_info(),
        }
        
        # Add CPU stats
        try:
            stats["cpu"] = self._get_cpu_stats()
        except Exception as e:
            logger.error(f"Error collecting CPU stats: {e}")
            stats["cpu"] = {"error": str(e)}
            
        # Add memory stats
        try:
            stats["memory"] = self._get_memory_stats()
        except Exception as e:
            logger.error(f"Error collecting memory stats: {e}")
            stats["memory"] = {"error": str(e)}
            
        # Add disk stats
        try:
            stats["disk"] = self._get_disk_stats()
        except Exception as e:
            logger.error(f"Error collecting disk stats: {e}")
            stats["disk"] = {"error": str(e)}
            
        # Add network stats
        try:
            stats["network"] = self._get_network_stats()
        except Exception as e:
            logger.error(f"Error collecting network stats: {e}")
            stats["network"] = {"error": str(e)}
            
        return stats
        
    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information"""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }
        
    def _get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU statistics"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)
            
            # Get per-CPU utilization
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
            
            result = {
                "percent": cpu_percent,
                "count": {
                    "physical": physical_cores,
                    "logical": cpu_count
                },
                "per_cpu": per_cpu
            }
            
            if cpu_freq:
                result["frequency"] = {
                    "current": cpu_freq.current,
                    "min": cpu_freq.min if hasattr(cpu_freq, 'min') else None,
                    "max": cpu_freq.max if hasattr(cpu_freq, 'max') else None
                }
                
            return result
        except ImportError:
            return {"error": "psutil module not available. Install with: pip install psutil"}
            
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            import psutil
            
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()
            
            return {
                "virtual": {
                    "total": vm.total,
                    "available": vm.available,
                    "used": vm.used,
                    "percent": vm.percent,
                    "free": vm.free
                },
                "swap": {
                    "total": sm.total,
                    "used": sm.used,
                    "free": sm.free,
                    "percent": sm.percent
                }
            }
        except ImportError:
            return {"error": "psutil module not available. Install with: pip install psutil"}
            
    def _get_disk_stats(self) -> Dict[str, Any]:
        """Get disk usage statistics"""
        try:
            import psutil
            
            result = {
                "partitions": [],
                "io": None
            }
            
            # Get disk partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    part_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    }
                    result["partitions"].append(part_info)
                except (PermissionError, FileNotFoundError):
                    # Skip partitions we can't access
                    pass
            
            # Get disk I/O statistics
            current_time = time.time()
            current_disk_io = psutil.disk_io_counters()
            
            if current_disk_io and self._last_disk_io and self._last_io_time:
                time_delta = current_time - self._last_io_time
                
                if time_delta > 0:
                    read_speed = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
                    write_speed = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta
                    
                    result["io"] = {
                        "read_speed": read_speed,
                        "write_speed": write_speed,
                        "read_count": current_disk_io.read_count,
                        "write_count": current_disk_io.write_count,
                        "read_bytes": current_disk_io.read_bytes,
                        "write_bytes": current_disk_io.write_bytes
                    }
                    
            self._last_disk_io = current_disk_io
            self._last_io_time = current_time
            
            return result
        except ImportError:
            return {"error": "psutil module not available. Install with: pip install psutil"}
            
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            import psutil
            
            result = {
                "interfaces": [],
                "speeds": {}
            }
            
            # Get network interface information
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface, addresses in net_if_addrs.items():
                if_stats = net_if_stats.get(interface)
                interface_info = {
                    "name": interface,
                    "addresses": [],
                    "up": if_stats.isup if if_stats else False,
                    "speed": if_stats.speed if if_stats else None,
                    "duplex": str(if_stats.duplex) if if_stats and hasattr(if_stats, 'duplex') else None,
                    "mtu": if_stats.mtu if if_stats else None
                }
                
                for addr in addresses:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address
                    }
                    if hasattr(addr, 'netmask') and addr.netmask:
                        addr_info["netmask"] = addr.netmask
                    if hasattr(addr, 'broadcast') and addr.broadcast:
                        addr_info["broadcast"] = addr.broadcast
                        
                    interface_info["addresses"].append(addr_info)
                    
                result["interfaces"].append(interface_info)
            
            # Get network I/O statistics
            current_time = time.time()
            current_net_io = psutil.net_io_counters(pernic=True)
            
            if current_net_io and self._last_network_io and self._last_io_time:
                time_delta = current_time - self._last_io_time
                
                if time_delta > 0:
                    for interface, counters in current_net_io.items():
                        if interface in self._last_network_io:
                            last_counters = self._last_network_io[interface]
                            
                            bytes_sent = counters.bytes_sent - last_counters.bytes_sent
                            bytes_recv = counters.bytes_recv - last_counters.bytes_recv
                            
                            # Calculate speeds in bytes/second
                            result["speeds"][interface] = {
                                "upload": bytes_sent / time_delta,
                                "download": bytes_recv / time_delta,
                                "packets_sent": counters.packets_sent,
                                "packets_recv": counters.packets_recv,
                                "total_bytes_sent": counters.bytes_sent,
                                "total_bytes_recv": counters.bytes_recv
                            }
                            
            self._last_network_io = current_net_io
            self._last_io_time = current_time
            
            return result
        except ImportError:
            return {"error": "psutil module not available. Install with: pip install psutil"}
        
    def format_stats(self, stats: Dict[str, Any] = None) -> str:
        """Format statistics for human-readable display"""
        if stats is None:
            stats = self.get_stats()
            
        lines = []
        
        # System information
        system = stats.get("system", {})
        lines.append(f"System: {system.get('os', 'Unknown')} {system.get('os_version', '')}")
        lines.append(f"Hostname: {system.get('hostname', 'Unknown')}")
        lines.append(f"Architecture: {system.get('architecture', 'Unknown')}")
        
        # CPU information
        cpu = stats.get("cpu", {})
        if not cpu.get("error"):
            lines.append("\nCPU:")
            lines.append(f"  Usage: {cpu.get('percent', 0)}%")
            
            count = cpu.get("count", {})
            lines.append(f"  Cores: {count.get('physical', 0)} physical, {count.get('logical', 0)} logical")
            
            freq = cpu.get("frequency", {})
            if freq:
                current = freq.get("current")
                if current:
                    lines.append(f"  Frequency: {current:.2f} MHz")
        else:
            lines.append(f"\nCPU: {cpu.get('error')}")
        
        # Memory information
        memory = stats.get("memory", {})
        if not memory.get("error"):
            vm = memory.get("virtual", {})
            if vm:
                lines.append("\nMemory:")
                total_gb = vm.get("total", 0) / (1024 ** 3)
                used_gb = vm.get("used", 0) / (1024 ** 3)
                lines.append(f"  RAM: {used_gb:.2f} GB used / {total_gb:.2f} GB total ({vm.get('percent', 0)}%)")
                
            swap = memory.get("swap", {})
            if swap and swap.get("total", 0) > 0:
                total_gb = swap.get("total", 0) / (1024 ** 3)
                used_gb = swap.get("used", 0) / (1024 ** 3)
                lines.append(f"  Swap: {used_gb:.2f} GB used / {total_gb:.2f} GB total ({swap.get('percent', 0)}%)")
        else:
            lines.append(f"\nMemory: {memory.get('error')}")
        
        # Disk information
        disk = stats.get("disk", {})
        if not disk.get("error"):
            partitions = disk.get("partitions", [])
            if partitions:
                lines.append("\nDisk:")
                for part in partitions:
                    total_gb = part.get("total", 0) / (1024 ** 3)
                    used_gb = part.get("used", 0) / (1024 ** 3)
                    lines.append(f"  {part.get('mountpoint', 'Unknown')}: {used_gb:.2f} GB used / {total_gb:.2f} GB total ({part.get('percent', 0)}%)")
                
            io = disk.get("io")
            if io:
                read_speed_mb = io.get("read_speed", 0) / (1024 ** 2)
                write_speed_mb = io.get("write_speed", 0) / (1024 ** 2)
                lines.append(f"  I/O: {read_speed_mb:.2f} MB/s read, {write_speed_mb:.2f} MB/s write")
        else:
            lines.append(f"\nDisk: {disk.get('error')}")
        
        # Network information
        network = stats.get("network", {})
        if not network.get("error"):
            speeds = network.get("speeds", {})
            if speeds:
                lines.append("\nNetwork:")
                for interface, speed in speeds.items():
                    upload_mb = speed.get("upload", 0) / (1024 ** 2)
                    download_mb = speed.get("download", 0) / (1024 ** 2)
                    lines.append(f"  {interface}: {download_mb:.2f} MB/s down, {upload_mb:.2f} MB/s up")
        else:
            lines.append(f"\nNetwork: {network.get('error')}")
            
        return "\n".join(lines)