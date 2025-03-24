"""
File Backup Module
Provides functionality to create and manage backups of files and command history
"""
import os
import shutil
import time
import json
import glob
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

class FileBackup:
    """Handles file backup operations"""
    
    def __init__(self, backup_dir: str = "backups", config: Dict = None):
        """Initialize file backup manager"""
        self.config = config or {}
        self.backup_dir = backup_dir
        self.max_backups = self.config.get("max_history_backups", 5)
        self._ensure_backup_dir()
        
    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
                logger.info(f"Created backup directory at {self.backup_dir}")
            except Exception as e:
                logger.error(f"Failed to create backup directory: {e}")
                
    def backup_file(self, file_path: str) -> Optional[str]:
        """Create a backup of a file"""
        if not os.path.exists(file_path):
            logger.error(f"Cannot backup non-existent file: {file_path}")
            return None
            
        try:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file_path)
            backup_name = f"{file_name}.{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups(file_name)
            
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup file {file_path}: {e}")
            return None
            
    def backup_history(self, history_file: str = "command_history.json") -> Optional[str]:
        """Backup command history file"""
        if not os.path.exists(history_file):
            logger.warning(f"Command history file does not exist: {history_file}")
            return None
            
        return self.backup_file(history_file)
        
    def _cleanup_old_backups(self, file_name: str) -> None:
        """Clean up old backups exceeding the maximum count"""
        pattern = os.path.join(self.backup_dir, f"{file_name}.*.bak")
        backups = glob.glob(pattern)
        
        # Sort by modification time (newest first)
        backups.sort(key=os.path.getmtime, reverse=True)
        
        # Remove excess backups
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups:]:
                try:
                    os.remove(old_backup)
                    logger.info(f"Removed old backup: {old_backup}")
                except Exception as e:
                    logger.error(f"Failed to remove old backup {old_backup}: {e}")
                    
    def list_backups(self, file_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups"""
        if file_name:
            pattern = os.path.join(self.backup_dir, f"{file_name}.*.bak")
        else:
            pattern = os.path.join(self.backup_dir, "*.bak")
            
        backups = glob.glob(pattern)
        result = []
        
        for backup_path in backups:
            try:
                backup_name = os.path.basename(backup_path)
                size = os.path.getsize(backup_path)
                mtime = os.path.getmtime(backup_path)
                
                # Parse timestamp from filename
                timestamp = None
                parts = backup_name.split('.')
                if len(parts) >= 3:
                    timestamp_part = parts[-2]
                    try:
                        timestamp = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                    except ValueError:
                        pass
                
                result.append({
                    "name": backup_name,
                    "path": backup_path,
                    "size": size,
                    "modified": datetime.fromtimestamp(mtime).isoformat(),
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "original_file": '.'.join(backup_name.split('.')[:-2])
                })
            except Exception as e:
                logger.error(f"Error processing backup {backup_path}: {e}")
                
        # Sort by modification time (newest first)
        result.sort(key=lambda x: x.get("modified", ""), reverse=True)
        return result
        
    def restore_backup(self, backup_path: str, destination: Optional[str] = None) -> bool:
        """Restore a file from backup"""
        if not os.path.exists(backup_path):
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
            
        try:
            # Determine destination path
            if not destination:
                backup_name = os.path.basename(backup_path)
                original_file = '.'.join(backup_name.split('.')[:-2])
                destination = original_file
                
            # Create a backup of current file before restoring
            if os.path.exists(destination):
                self.backup_file(destination)
                
            # Copy backup to destination
            shutil.copy2(backup_path, destination)
            logger.info(f"Restored {backup_path} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_path}: {e}")
            return False
            
    def delete_backup(self, backup_path: str) -> bool:
        """Delete a backup file"""
        if not os.path.exists(backup_path):
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
            
        try:
            os.remove(backup_path)
            logger.info(f"Deleted backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_path}: {e}")
            return False 