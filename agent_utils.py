"""
Agent Terminal Utilities
Helper functions and classes for the Agent Terminal Assistant
"""
import os
import re
import sys
import platform
import subprocess
from typing import List, Dict, Optional, Tuple, Set, Any

class PlatformUtils:
    """Utilities for platform-specific operations and detection"""
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return platform.system().lower() == "windows"
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return platform.system().lower() == "linux"
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return platform.system().lower() == "darwin"
    
    @staticmethod
    def get_shell() -> str:
        """Get the current shell"""
        if PlatformUtils.is_windows():
            # Check if PowerShell is available
            try:
                subprocess.run(["powershell", "-Command", "echo 1"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return "powershell"
            except:
                return "cmd"
        else:
            # Unix-like systems
            return os.environ.get("SHELL", "/bin/bash").split("/")[-1]
    
    @staticmethod
    def get_platform_info() -> Dict:
        """Get detailed platform information"""
        info = {
            "os": platform.system().lower(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_termux": False,
            "is_proot": False,
            "termux_version": None,
            "proot_distro": None
        }
        
        # Check for Termux environment
        try:
            if os.path.exists("/data/data/com.termux"):
                info["is_termux"] = True
                # Try to get Termux version
                try:
                    with open("/data/data/com.termux/files/usr/etc/termux/version", "r") as f:
                        info["termux_version"] = f.read().strip()
                except:
                    pass
        except:
            pass
            
        # Check for PRoot-distro
        try:
            if os.path.exists("/usr/local/bin/proot-distro"):
                info["is_proot"] = True
                # Try to get PRoot-distro information
                try:
                    result = subprocess.run(
                        ["proot-distro", "list"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        info["proot_distro"] = result.stdout.strip()
                except:
                    pass
        except:
            pass
            
        return info

class CommandValidator:
    """Validates and adapts commands for different platforms"""
    
    # Common dangerous commands that require confirmation
    DANGEROUS_COMMANDS = {
        "rm -rf": "This command recursively removes files without confirmation",
        "rm -r": "This command recursively removes files",
        "del /s": "This command recursively deletes files",
        "rd /s": "This command recursively removes directories",
        "format": "This command formats storage devices",
        "dd": "This command can overwrite disk data",
        ">": "This will overwrite existing files",
        "shutdown": "This will shut down the system",
        "reboot": "This will reboot the system"
    }
    
    # Commands that don't exist or differ on Windows
    WINDOWS_UNAVAILABLE = {
        "ls": "Use 'dir' instead",
        "grep": "Use 'findstr' or 'Select-String' instead",
        "cat": "Use 'type' or 'Get-Content' instead",
        "cp": "Use 'copy' or 'Copy-Item' instead",
        "mv": "Use 'move' or 'Move-Item' instead",
        "rm": "Use 'del' or 'Remove-Item' instead",
        "touch": "Use 'echo $null >>' or 'New-Item' instead"
    }
    
    # Commands that don't exist or differ on Linux/macOS
    UNIX_UNAVAILABLE = {
        "dir": "Use 'ls' instead",
        "type": "Use 'cat' instead",
        "copy": "Use 'cp' instead",
        "move": "Use 'mv' instead",
        "del": "Use 'rm' instead",
        "findstr": "Use 'grep' instead",
        "ipconfig": "Use 'ifconfig' or 'ip addr' instead"
    }
    
    @staticmethod
    def is_dangerous(command: str) -> Tuple[bool, Optional[str]]:
        """Check if a command is potentially dangerous"""
        for dangerous_cmd, reason in CommandValidator.DANGEROUS_COMMANDS.items():
            if dangerous_cmd in command:
                return True, reason
        return False, None
    
    @staticmethod
    def validate_for_platform(command: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate if a command is compatible with the current platform
        
        Returns:
            (is_valid, reason, suggested_alternative)
        """
        # Check if command is available on this platform
        if PlatformUtils.is_windows():
            # Check for Unix commands that don't work on Windows
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] in CommandValidator.WINDOWS_UNAVAILABLE:
                return False, f"Command '{cmd_parts[0]}' is not available on Windows", CommandValidator.WINDOWS_UNAVAILABLE[cmd_parts[0]]
        else:
            # Check for Windows commands that don't work on Unix
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] in CommandValidator.UNIX_UNAVAILABLE:
                return False, f"Command '{cmd_parts[0]}' is not available on Unix-like systems", CommandValidator.UNIX_UNAVAILABLE[cmd_parts[0]]
        
        return True, None, None
    
    @staticmethod
    def adapt_for_platform(command: str) -> str:
        """Adapt a command for the current platform if possible"""
        if PlatformUtils.is_windows():
            # Convert Unix commands to Windows equivalents
            cmd_parts = command.split()
            if not cmd_parts:
                return command
                
            base_cmd = cmd_parts[0]
            
            # Simple command replacements
            replacements = {
                "ls": "dir",
                "cat": "type",
                "cp": "copy",
                "mv": "move",
                "rm": "del",
                "grep": "findstr"
            }
            
            if base_cmd in replacements:
                cmd_parts[0] = replacements[base_cmd]
                return " ".join(cmd_parts)
            
            # Handle more complex commands
            if base_cmd == "touch":
                if len(cmd_parts) > 1:
                    return f"echo $null >> {cmd_parts[1]}"
                
        else:
            # Convert Windows commands to Unix equivalents
            cmd_parts = command.split()
            if not cmd_parts:
                return command
                
            base_cmd = cmd_parts[0]
            
            # Simple command replacements
            replacements = {
                "dir": "ls",
                "type": "cat",
                "copy": "cp",
                "move": "mv",
                "del": "rm",
                "findstr": "grep",
                "ipconfig": "ifconfig"
            }
            
            if base_cmd in replacements:
                cmd_parts[0] = replacements[base_cmd]
                return " ".join(cmd_parts)
            
        # Return the original command if no adaptation is possible
        return command

class TaskUtils:
    """Utilities for task parsing and categorization"""
    
    # Task categories and keywords
    TASK_CATEGORIES = {
        "file_operations": [
            "find", "list", "search", "copy", "move", "rename", "delete",
            "remove", "create", "make", "touch", "edit", "chmod", "permissions"
        ],
        "system_monitoring": [
            "cpu", "memory", "ram", "disk", "usage", "monitor", "performance",
            "process", "top", "system", "load"
        ],
        "network_operations": [
            "ping", "download", "upload", "network", "ip", "dns", "http",
            "web", "server", "port", "socket", "connection"
        ],
        "archive_operations": [
            "zip", "unzip", "tar", "extract", "compress", "decompress",
            "archive", "package"
        ],
        "text_processing": [
            "grep", "search", "find", "text", "content", "string", "pattern",
            "regular expression", "regex", "match", "replace", "substitute"
        ],
        "package_management": [
            "install", "remove", "update", "upgrade", "package", "library",
            "dependency", "pip", "npm", "apt", "yum", "brew", "chocolatey"
        ]
    }
    
    @staticmethod
    def categorize_task(task: str) -> List[str]:
        """Categorize a task based on keywords"""
        task_lower = task.lower()
        categories = []
        
        for category, keywords in TaskUtils.TASK_CATEGORIES.items():
            for keyword in keywords:
                if keyword in task_lower:
                    categories.append(category)
                    break
        
        return categories
    
    @staticmethod
    def extract_parameters(task: str) -> Dict[str, str]:
        """Extract potential parameters from a task description"""
        params = {}
        
        # Extract file paths (anything that looks like a path)
        path_matches = re.findall(r'[\'"]?([\/\\]?[\w\-\. ]+[\/\\][\w\-\. \/\\]+)[\'"]?', task)
        if path_matches:
            params["paths"] = path_matches
        
        # Extract file extensions
        extension_matches = re.findall(r'\.([a-zA-Z0-9]+)\b', task)
        if extension_matches:
            params["extensions"] = [f".{ext}" for ext in extension_matches]
        
        # Extract sizes with units
        size_matches = re.findall(r'(\d+)\s*(kb|mb|gb|tb|bytes|byte|k|m|g|t)\b', task, re.IGNORECASE)
        if size_matches:
            params["sizes"] = [f"{size}{unit}" for size, unit in size_matches]
        
        # Extract numbers that might be relevant
        number_matches = re.findall(r'\b(\d+)\b', task)
        if number_matches:
            params["numbers"] = number_matches
        
        # Extract quoted strings
        quoted_matches = re.findall(r'[\'"]([^\'"]+)[\'"]', task)
        if quoted_matches:
            params["quoted_strings"] = quoted_matches
        
        return params

class FileUtils:
    """Utilities for file operations"""
    
    @staticmethod
    def get_file_info(path: str) -> Dict[str, Any]:
        """Get information about a file"""
        if not os.path.exists(path):
            return {"exists": False}
        
        stats = os.stat(path)
        return {
            "exists": True,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "size": stats.st_size,
            "size_human": FileUtils.human_readable_size(stats.st_size),
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "accessed": stats.st_atime,
            "permissions": oct(stats.st_mode)[-3:]
        }
    
    @staticmethod
    def human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human-readable size"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f}{size_names[i]}"
    
    @staticmethod
    def is_binary_file(file_path: str) -> bool:
        """Check if a file is binary"""
        try:
            with open(file_path, 'tr') as f:
                chunk = f.read(1024)
                for c in chunk:
                    if 0 <= ord(c) <= 8:
                        return True
            return False
        except UnicodeDecodeError:
            return True
        except Exception:
            return True
    
    @staticmethod
    def find_files(directory: str, pattern: str = "*", recursive: bool = True) -> List[str]:
        """Find files matching a pattern"""
        import fnmatch
        
        matches = []
        if recursive:
            for root, dirnames, filenames in os.walk(directory):
                for filename in fnmatch.filter(filenames, pattern):
                    matches.append(os.path.join(root, filename))
        else:
            for filename in fnmatch.filter(os.listdir(directory), pattern):
                if os.path.isfile(os.path.join(directory, filename)):
                    matches.append(os.path.join(directory, filename))
        
        return matches 