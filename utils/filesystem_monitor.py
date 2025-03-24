"""
Filesystem Monitor Module
Provides file system monitoring to detect changes in directories.
"""
import os
import time
import threading
from typing import Dict, Set, List, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system change events"""
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
    
    def on_any_event(self, event: FileSystemEvent):
        """Called when a file system event occurs"""
        if event.is_directory:
            event_type = "directory"
        else:
            event_type = "file"
            
        # Call the callback with event type and path
        self.callback(event_type, event.src_path)

class FilesystemMonitor:
    """Monitors file system changes in specified directories"""
    def __init__(self):
        self.observer = Observer()
        self.watch_handlers: Dict[str, FileChangeHandler] = {}
        self.monitored_paths: Dict[str, Set[str]] = {}
        self.callbacks: List[Callable[[str, str, str], None]] = []
        self.running = False
    
    def start(self) -> bool:
        """Start the file system monitor"""
        if self.running:
            return True
            
        try:
            self.observer.start()
            self.running = True
            return True
        except Exception:
            return False
    
    def stop(self) -> bool:
        """Stop the file system monitor"""
        if not self.running:
            return True
            
        try:
            self.observer.stop()
            self.observer.join()
            self.running = False
            return True
        except Exception:
            return False
    
    def add_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """Add a callback for file system events"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, str, str], None]) -> bool:
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
    
    def _handle_event(self, event_type: str, path: str) -> None:
        """Handle a file system event"""
        if not path:
            return
            
        # Determine the watch path this event belongs to
        watch_path = None
        for wp in self.monitored_paths.keys():
            if path.startswith(wp):
                watch_path = wp
                break
                
        if not watch_path:
            return
            
        # Get the event action
        if "created" in event_type:
            action = "created"
        elif "deleted" in event_type:
            action = "deleted"
        elif "modified" in event_type:
            action = "modified"
        elif "moved" in event_type:
            action = "moved"
        else:
            action = "unknown"
        
        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(action, event_type, path)
            except Exception:
                pass
    
    def watch_directory(self, path: str, patterns: List[str] = None, recursive: bool = True) -> bool:
        """Watch a directory for changes"""
        if not os.path.isdir(path):
            return False
            
        # Normalize path
        path = os.path.abspath(path)
        
        # Check if already watching
        if path in self.watch_handlers:
            # Update patterns if needed
            if patterns:
                self.monitored_paths[path] = set(patterns)
            return True
        
        # Create handler and schedule watching
        handler = FileChangeHandler(self._handle_event)
        
        try:
            self.observer.schedule(handler, path, recursive=recursive)
            self.watch_handlers[path] = handler
            
            # Store patterns
            if patterns:
                self.monitored_paths[path] = set(patterns)
            else:
                self.monitored_paths[path] = set(["*"])
                
            return True
        except Exception:
            return False
    
    def unwatch_directory(self, path: str) -> bool:
        """Stop watching a directory"""
        if not path or path not in self.watch_handlers:
            return False
            
        # Normalize path
        path = os.path.abspath(path)
        
        # Remove from observer
        try:
            handler = self.watch_handlers[path]
            self.observer.unschedule(handler)
            del self.watch_handlers[path]
            
            # Remove from monitored paths
            if path in self.monitored_paths:
                del self.monitored_paths[path]
                
            return True
        except Exception:
            return False
    
    def get_monitored_directories(self) -> List[Dict[str, any]]:
        """Get a list of monitored directories"""
        result = []
        
        for path, patterns in self.monitored_paths.items():
            result.append({
                "path": path,
                "patterns": list(patterns)
            })
            
        return result
    
    def is_watching(self, path: str) -> bool:
        """Check if a path is being watched"""
        path = os.path.abspath(path)
        return path in self.watch_handlers

class PeriodicDirectoryScanner:
    """Scans directories periodically for changes"""
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.directories: Dict[str, Dict[str, float]] = {}
        self.callbacks: List[Callable[[str, str, str], None]] = []
        self.running = False
        self.thread = None
    
    def start(self) -> bool:
        """Start the scanner"""
        if self.running:
            return True
            
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()
        return True
    
    def stop(self) -> bool:
        """Stop the scanner"""
        if not self.running:
            return True
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        return True
    
    def add_directory(self, path: str) -> bool:
        """Add a directory to scan"""
        if not os.path.isdir(path):
            return False
            
        # Normalize path
        path = os.path.abspath(path)
        
        # Initialize file timestamps
        self.directories[path] = self._get_file_timestamps(path)
        return True
    
    def remove_directory(self, path: str) -> bool:
        """Remove a directory from scanning"""
        path = os.path.abspath(path)
        if path in self.directories:
            del self.directories[path]
            return True
        return False
    
    def add_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """Add a callback for file change events"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, str, str], None]) -> bool:
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
    
    def _get_file_timestamps(self, directory: str) -> Dict[str, float]:
        """Get timestamps for all files in a directory"""
        timestamps = {}
        
        for root, _, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                try:
                    timestamps[path] = os.path.getmtime(path)
                except Exception:
                    pass
                    
        return timestamps
    
    def _scan_loop(self) -> None:
        """Main scanning loop"""
        while self.running:
            for directory, old_timestamps in list(self.directories.items()):
                try:
                    # Get current timestamps
                    new_timestamps = self._get_file_timestamps(directory)
                    
                    # Check for new or modified files
                    for path, timestamp in new_timestamps.items():
                        if path not in old_timestamps:
                            # New file
                            self._notify_callbacks("created", "file", path)
                        elif timestamp > old_timestamps[path]:
                            # Modified file
                            self._notify_callbacks("modified", "file", path)
                    
                    # Check for deleted files
                    for path in old_timestamps:
                        if path not in new_timestamps:
                            # Deleted file
                            self._notify_callbacks("deleted", "file", path)
                    
                    # Update timestamps
                    self.directories[directory] = new_timestamps
                except Exception:
                    pass
            
            # Sleep
            time.sleep(self.interval)
    
    def _notify_callbacks(self, action: str, event_type: str, path: str) -> None:
        """Notify callbacks of a file change"""
        for callback in self.callbacks:
            try:
                callback(action, event_type, path)
            except Exception:
                pass 