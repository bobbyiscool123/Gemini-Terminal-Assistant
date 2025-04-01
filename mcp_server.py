#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server
Handles system operations and queries for the AI agent
Optimized for Gemini 2.5 Pro
"""
import os
import json
import platform
import subprocess
import shutil
import sys
import yaml
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from pathlib import Path
from prompt import generate_command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MCPServer:
    """Server to handle system operations and queries"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the MCP server with configuration."""
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.system_info = self._get_system_info()
        self.package_managers = self._check_package_managers()
        self.drive_info = self._get_drive_info()
        self.common_dirs = self._get_common_dirs()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def setup_logging(self):
        """Configure logging based on settings."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        logging.getLogger().setLevel(log_level)

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests and generate responses."""
        try:
            command_type = request.get('type')
            parameters = request.get('parameters', {})
            
            if command_type == 'execute_command':
                return self._execute_command(parameters)
            elif command_type == 'get_system_info':
                return self._get_system_info()
            elif command_type == 'check_package':
                return self._check_package(parameters.get('package_name'))
            else:
                return {'error': f'Unknown command type: {command_type}'}
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {'error': str(e)}

    def _execute_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command using Gemini API."""
        try:
            command = generate_command(parameters.get('command', ''), self.config)
            if not command:
                return {'error': 'Failed to generate command'}
                
            # Execute the command
            result = os.system(command)
            return {
                'success': result == 0,
                'command': command,
                'exit_code': result
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {'error': str(e)}

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information using Gemini API."""
        try:
            command = generate_command("get system information", self.config)
            if not command:
                return {'error': 'Failed to generate system info command'}
                
            result = os.system(command)
            return {
                'success': result == 0,
                'command': command,
                'exit_code': result
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}

    def _check_package(self, package_name: str) -> Dict[str, Any]:
        """Check if a package is installed using Gemini API."""
        try:
            command = generate_command(f"check if package {package_name} is installed", self.config)
            if not command:
                return {'error': 'Failed to generate package check command'}
                
            result = os.system(command)
            return {
                'success': result == 0,
                'command': command,
                'exit_code': result,
                'package_name': package_name
            }
        except Exception as e:
            logger.error(f"Error checking package: {e}")
            return {'error': str(e)}

    def _check_package_managers(self) -> Dict:
        """Check for installed package managers"""
        managers = {
            "apt": False,
            "pip": False,
            "termux": False
        }
        
        # Check for Termux environment
        try:
            if os.path.exists("/data/data/com.termux"):
                managers["termux"] = True
        except:
            pass
            
        # Check apt with multiple possible paths
        apt_paths = ["/usr/bin/apt", "/bin/apt", "/data/data/com.termux/files/usr/bin/apt"]
        for path in apt_paths:
            try:
                if os.path.exists(path):
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    managers["apt"] = True
                    break
            except:
                continue
                
        # Check pip with multiple possible paths
        pip_paths = [
            "/usr/bin/pip",
            "/usr/bin/pip3",
            "/usr/local/bin/pip",
            "/usr/local/bin/pip3",
            "/data/data/com.termux/files/usr/bin/pip",
            "/data/data/com.termux/files/usr/bin/pip3"
        ]
        for path in pip_paths:
            try:
                if os.path.exists(path):
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    managers["pip"] = True
                    break
            except:
                continue
            
        return managers
    
    def _get_drive_info(self) -> Dict:
        """Get information about file systems"""
        drive_info = {}
        try:
            # Get mounted filesystems
            result = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:  # Filesystem, Size, Used, Avail, Use%, Mounted on
                    mount_point = parts[5]
                    drive_info[mount_point] = {
                        "type": "filesystem",
                        "device": parts[0],
                        "total_space": parts[1],
                        "used_space": parts[2],
                        "free_space": parts[3],
                        "use_percent": parts[4]
                    }
        except:
            # Fallback to basic detection
            drive_info["/"] = {"type": "filesystem"}
            
        return drive_info
    
    def _get_common_dirs(self) -> Dict:
        """Get common system directories"""
        home = os.path.expanduser("~")
        return {
            "Home": home,
            "Downloads": os.path.join(home, "Downloads"),
            "Desktop": os.path.join(home, "Desktop"),
            "Documents": os.path.join(home, "Documents"),
            "Pictures": os.path.join(home, "Pictures"),
            "Videos": os.path.join(home, "Videos"),
            "Music": os.path.join(home, "Music"),
            "Applications": "/usr/bin",
            "System": "/etc"
        }
    
    def get_folder_structure(self, path: str, max_depth: int = 3) -> Dict:
        """Get folder structure starting from a path"""
        structure = {
            "path": path,
            "name": os.path.basename(path),
            "type": "directory",
            "size": 0,
            "files": [],
            "folders": []
        }
        
        try:
            for root, dirs, files in os.walk(path, topdown=True):
                current_depth = root[len(path):].count(os.sep)
                if current_depth >= max_depth:
                    continue
                    
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_info = {
                            "name": file,
                            "path": file_path,
                            "type": "file",
                            "size": os.path.getsize(file_path),
                            "extension": os.path.splitext(file)[1].lower(),
                            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        structure["files"].append(file_info)
                    except:
                        continue
                        
                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        dir_info = {
                            "name": dir_name,
                            "path": dir_path,
                            "type": "directory",
                            "size": 0,
                            "files": [],
                            "folders": []
                        }
                        structure["folders"].append(dir_info)
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error scanning folder {path}: {str(e)}")
            
        return structure
    
    def analyze_files(self, path: str) -> Dict:
        """Analyze files in a directory and suggest organization"""
        analysis = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "suggested_folders": {},
            "duplicates": []
        }
        
        try:
            file_structure = self.get_folder_structure(path, max_depth=1)
            analysis["total_files"] = len(file_structure["files"])
            
            # Analyze file types
            for file in file_structure["files"]:
                analysis["total_size"] += file["size"]
                ext = file["extension"]
                if ext not in analysis["file_types"]:
                    analysis["file_types"][ext] = {"count": 0, "size": 0}
                analysis["file_types"][ext]["count"] += 1
                analysis["file_types"][ext]["size"] += file["size"]
            
            # Suggest folders based on file types
            for ext, info in analysis["file_types"].items():
                if ext in [".jpg", ".jpeg", ".png", ".gif"]:
                    analysis["suggested_folders"]["Images"] = analysis["suggested_folders"].get("Images", 0) + info["count"]
                elif ext in [".mp3", ".wav", ".flac"]:
                    analysis["suggested_folders"]["Music"] = analysis["suggested_folders"].get("Music", 0) + info["count"]
                elif ext in [".mp4", ".avi", ".mov"]:
                    analysis["suggested_folders"]["Videos"] = analysis["suggested_folders"].get("Videos", 0) + info["count"]
                elif ext in [".pdf", ".doc", ".docx", ".txt"]:
                    analysis["suggested_folders"]["Documents"] = analysis["suggested_folders"].get("Documents", 0) + info["count"]
                elif ext in [".py", ".js", ".java", ".cpp"]:
                    analysis["suggested_folders"]["Code"] = analysis["suggested_folders"].get("Code", 0) + info["count"]
        except Exception as e:
            print(f"Error analyzing files in {path}: {str(e)}")
        
        return analysis
    
    def create_folder(self, path: str) -> bool:
        """Create a folder at the specified path"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating folder at {path}: {str(e)}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """Move a file from source to destination"""
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            print(f"Error moving file from {source} to {destination}: {str(e)}")
            return False
    
    def delete_empty_folders(self, path: str) -> List[str]:
        """Delete empty folders in the specified path"""
        deleted = []
        
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.listdir(dir_path):  # Check if directory is empty
                        os.rmdir(dir_path)
                        deleted.append(dir_path)
        except Exception as e:
            print(f"Error deleting empty folders in {path}: {str(e)}")
        
        return deleted
    
    def install_package_manager(self, manager: str) -> bool:
        """Install a package manager if it's not already installed"""
        if manager == "pip" and not self.package_managers.get("pip", False):
            try:
                if self.package_managers.get("apt", False):
                    result = subprocess.run(["apt", "install", "-y", "python3-pip"], capture_output=True, text=True, check=True)
                    return "successfully" in result.stdout.lower()
                else:
                    return False
            except:
                return False
        
        return True  # Already installed or unsupported manager
    
    def get_package_info(self, package_name: str) -> Dict:
        """Get information about a package"""
        info = {"name": package_name, "installed": False, "version": None, "location": None}
        
        # Check pip package
        try:
            result = subprocess.run(["pip", "show", package_name], capture_output=True, text=True)
            if result.returncode == 0:
                info["installed"] = True
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        info["version"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Location:"):
                        info["location"] = line.split(":", 1)[1].strip()
        except:
            pass
        
        # Check apt package
        if not info["installed"] and self.package_managers.get("apt", False):
            try:
                result = subprocess.run(["apt", "show", package_name], capture_output=True, text=True)
                if result.returncode == 0 and "installed" in result.stdout.lower():
                    info["installed"] = True
                    for line in result.stdout.split("\n"):
                        if line.startswith("Version:"):
                            info["version"] = line.split(":", 1)[1].strip()
            except:
                pass
        
        return info

def main():
    """Main entry point for the MCP server."""
    try:
        server = MCPServer()
        
        # Read input from stdin
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                request = json.loads(line)
                response = server.process_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON input: {e}")
                print(json.dumps({'error': 'Invalid JSON input'}), flush=True)
                
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 