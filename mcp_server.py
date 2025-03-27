#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server
Handles system operations and queries for the AI agent
"""
import os
import json
import platform
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import win32api
import win32con
import win32file
import win32security
import win32com.client
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
            "chocolatey": False,
            "winget": False,
            "scoop": False
        }
        
        # Check Chocolatey
        try:
            subprocess.run(["choco", "-v"], capture_output=True, check=True)
            managers["chocolatey"] = True
        except:
            pass
            
        # Check Winget
        try:
            subprocess.run(["winget", "--version"], capture_output=True, check=True)
            managers["winget"] = True
        except:
            pass
            
        # Check Scoop
        try:
            subprocess.run(["scoop", "--version"], capture_output=True, check=True)
            managers["scoop"] = True
        except:
            pass
            
        return managers
    
    def _get_drive_info(self) -> Dict:
        """Get information about system drives"""
        drive_info = {}
        try:
            drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            for drive in drives:
                try:
                    drive_info[drive] = {
                        "type": "fixed" if drive.startswith("C:") else "removable",
                        "free_space": win32api.GetDiskFreeSpace(drive)[0] * win32api.GetDiskFreeSpace(drive)[1] * win32api.GetDiskFreeSpace(drive)[2],
                        "total_space": win32api.GetDiskFreeSpace(drive)[0] * win32api.GetDiskFreeSpace(drive)[1] * win32api.GetDiskFreeSpace(drive)[3]
                    }
                except:
                    drive_info[drive] = {"type": "available"}
        except:
            # Fallback to basic drive detection
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drive_info[drive] = {"type": "available"}
        return drive_info
    
    def _get_common_dirs(self) -> Dict:
        """Get common system directories"""
        return {
            "Program Files": os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files")),
            "Program Files (x86)": os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            "AppData": os.path.join(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))),
            "Local AppData": os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))),
            "Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "Documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "Pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "Videos": os.path.join(os.path.expanduser("~"), "Videos"),
            "Music": os.path.join(os.path.expanduser("~"), "Music")
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
            os.rename(source, destination)
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
        if manager == "chocolatey":
            try:
                # Download and run Chocolatey installation script
                script = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
                subprocess.run(["powershell", "-Command", script], check=True)
                return True
            except Exception as e:
                print(f"Error installing Chocolatey: {str(e)}")
                return False
        return False
    
    def get_package_info(self, package_name: str) -> Dict:
        """Get information about a package"""
        info = {
            "is_installed": False,
            "version": None,
            "location": None,
            "type": None
        }
        
        # Check if package is installed via Chocolatey
        if self.package_managers["chocolatey"]:
            try:
                result = subprocess.run(["choco", "list", package_name, "--local"], capture_output=True, text=True)
                if package_name.lower() in result.stdout.lower():
                    info["is_installed"] = True
                    info["type"] = "chocolatey"
                    # Extract version if available
                    version_match = re.search(rf"{package_name}\s+(\d+\.\d+\.\d+)", result.stdout)
                    if version_match:
                        info["version"] = version_match.group(1)
            except:
                pass
                
        # Check if package is installed via Winget
        if self.package_managers["winget"]:
            try:
                result = subprocess.run(["winget", "list", package_name], capture_output=True, text=True)
                if package_name.lower() in result.stdout.lower():
                    info["is_installed"] = True
                    info["type"] = "winget"
                    # Extract version if available
                    version_match = re.search(rf"{package_name}\s+(\d+\.\d+\.\d+)", result.stdout)
                    if version_match:
                        info["version"] = version_match.group(1)
            except:
                pass
                
        return info

# Create a singleton instance
mcp = MCPServer() 