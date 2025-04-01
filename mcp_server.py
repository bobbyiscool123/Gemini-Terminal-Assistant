#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server
Handles system operations and queries for the AI agent
Modified for Linux/Termux/PRoot-distro environments
"""
import os
import json
import platform
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

class MCPServer:
    """Server to handle system operations and queries"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.package_managers = self._check_package_managers()
        self.drive_info = self._get_drive_info()
        self.common_dirs = self._get_common_dirs()
        
    def _get_system_info(self) -> Dict:
        """Get basic system information"""
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    
    def _check_package_managers(self) -> Dict:
        """Check for installed package managers"""
        managers = {
            "apt": False,
            "pip": False,
            "conda": False,
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
                
        # Check conda with multiple possible paths
        conda_paths = [
            os.path.expanduser("~/anaconda3/bin/conda"),
            os.path.expanduser("~/miniconda3/bin/conda"),
            "/usr/local/bin/conda",
            "/opt/conda/bin/conda"
        ]
        for path in conda_paths:
            try:
                if os.path.exists(path):
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    managers["conda"] = True
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
            for root, _, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        analysis["total_files"] += 1
                        analysis["total_size"] += file_size
                        
                        # Count file types
                        if file_ext:
                            analysis["file_types"][file_ext] = analysis["file_types"].get(file_ext, 0) + 1
                            
                        # Suggest folders based on file types
                        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                            analysis["suggested_folders"]["Images"] = analysis["suggested_folders"].get("Images", 0) + 1
                        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                            analysis["suggested_folders"]["Videos"] = analysis["suggested_folders"].get("Videos", 0) + 1
                        elif file_ext in ['.mp3', '.wav', '.flac']:
                            analysis["suggested_folders"]["Music"] = analysis["suggested_folders"].get("Music", 0) + 1
                        elif file_ext in ['.pdf', '.doc', '.docx', '.txt']:
                            analysis["suggested_folders"]["Documents"] = analysis["suggested_folders"].get("Documents", 0) + 1
                        elif file_ext in ['.zip', '.rar', '.7z']:
                            analysis["suggested_folders"]["Archives"] = analysis["suggested_folders"].get("Archives", 0) + 1
                        else:
                            analysis["suggested_folders"]["Others"] = analysis["suggested_folders"].get("Others", 0) + 1
                            
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error analyzing files in {path}: {str(e)}")
            
        return analysis
    
    def create_folder(self, path: str) -> bool:
        """Create a folder if it doesn't exist"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating folder {path}: {str(e)}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """Move a file to a new location"""
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            print(f"Error moving file {source}: {str(e)}")
            return False
    
    def delete_empty_folders(self, path: str) -> List[str]:
        """Delete empty folders and return list of deleted folders"""
        deleted = []
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.listdir(dir_path):
                        try:
                            os.rmdir(dir_path)
                            deleted.append(dir_path)
                        except:
                            continue
        except Exception as e:
            print(f"Error deleting empty folders in {path}: {str(e)}")
        return deleted
    
    def install_package_manager(self, manager: str) -> bool:
        """Install a package manager if not present"""
        if manager == "pip":
            try:
                subprocess.run(["apt", "install", "-y", "python3-pip"], check=True)
                return True
            except Exception as e:
                print(f"Error installing pip: {str(e)}")
                return False
        elif manager == "conda":
            try:
                # Download and install miniconda
                subprocess.run(["wget", "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh", "-O", "/tmp/miniconda.sh"], check=True)
                subprocess.run(["bash", "/tmp/miniconda.sh", "-b", "-p", "$HOME/miniconda"], check=True)
                return True
            except Exception as e:
                print(f"Error installing conda: {str(e)}")
                return False
        else:
            print(f"Package manager '{manager}' not supported for installation")
            return False
    
    def get_package_info(self, package_name: str) -> Dict:
        """Get information about an installed package"""
        info = {
            "name": package_name,
            "installed": False,
            "version": None,
            "install_location": None,
            "description": None
        }
        
        # Check pip package
        try:
            result = subprocess.run(["pip", "show", package_name], capture_output=True, text=True)
            if result.returncode == 0:
                info["installed"] = True
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        info["version"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Location:"):
                        info["install_location"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Summary:"):
                        info["description"] = line.split(":", 1)[1].strip()
        except:
            pass
        
        # Check apt package
        if not info["installed"]:
            try:
                result = subprocess.run(["apt", "show", package_name], capture_output=True, text=True)
                if result.returncode == 0:
                    info["installed"] = True
                    for line in result.stdout.split("\n"):
                        if line.startswith("Version:"):
                            info["version"] = line.split(":", 1)[1].strip()
                        elif line.startswith("Description:"):
                            info["description"] = line.split(":", 1)[1].strip()
            except:
                pass
                
        return info

# Create global instance
mcp = MCPServer()

if __name__ == "__main__":
    # Example usage
    print(json.dumps(mcp.system_info, indent=2))
    print(json.dumps(mcp.package_managers, indent=2)) 