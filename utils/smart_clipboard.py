"""
Smart Clipboard Module
Provides advanced clipboard functionality with history and transformations
"""
import os
import re
import json
import time
import logging
import platform
from typing import List, Dict, Any, Optional, Callable

# Setup logging
logger = logging.getLogger(__name__)

class ClipboardItem:
    """Represents an item in the clipboard history"""
    
    def __init__(self, content: str, source: str = None, 
                 timestamp: float = None, tags: List[str] = None,
                 metadata: Dict[str, Any] = None):
        """Initialize clipboard item"""
        self.content = content
        self.source = source
        self.timestamp = timestamp or time.time()
        self.tags = tags or []
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClipboardItem':
        """Create from dictionary"""
        return cls(
            content=data.get("content", ""),
            source=data.get("source"),
            timestamp=data.get("timestamp", time.time()),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )

class SmartClipboard:
    """Advanced clipboard with history and smart features"""
    
    def __init__(self, max_history: int = 50, history_file: str = "clipboard_history.json"):
        """Initialize smart clipboard"""
        self.max_history = max_history
        self.history_file = history_file
        self.history: List[ClipboardItem] = []
        self.current_index = -1
        self.transformations: Dict[str, Callable[[str], str]] = {}
        
        # Register default transformations
        self._register_default_transformations()
        
        # Load history from file
        self.load_history()
        
    def _register_default_transformations(self) -> None:
        """Register default content transformations"""
        self.transformations = {
            "uppercase": lambda x: x.upper(),
            "lowercase": lambda x: x.lower(),
            "capitalize": lambda x: x.capitalize(),
            "title": lambda x: x.title(),
            "strip": lambda x: x.strip(),
            "remove_whitespace": lambda x: re.sub(r'\s+', '', x),
            "compress_whitespace": lambda x: re.sub(r'\s+', ' ', x).strip(),
            "to_single_line": lambda x: re.sub(r'\s+', ' ', x).strip(),
            "reverse": lambda x: x[::-1],
            "count_chars": lambda x: str(len(x)),
            "count_words": lambda x: str(len(x.split())),
            "count_lines": lambda x: str(len(x.splitlines())),
            "to_snake_case": lambda x: re.sub(r'[\s-]+', '_', x.lower()),
            "to_kebab_case": lambda x: re.sub(r'[\s_]+', '-', x.lower()),
            "to_camel_case": lambda x: re.sub(r'[_\s-]([a-zA-Z])', lambda m: m.group(1).upper(), x.lower()),
            "wrap_quotes": lambda x: f'"{x}"',
            "wrap_single_quotes": lambda x: f"'{x}'",
            "remove_quotes": lambda x: re.sub(r'^[\'"]|[\'"]$', '', x),
            "escape_html": lambda x: x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                      .replace('"', '&quot;').replace("'", '&#39;'),
            "unescape_html": lambda x: x.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                                        .replace('&quot;', '"').replace('&#39;', "'"),
            "path_to_posix": lambda x: x.replace('\\', '/'),
            "path_to_windows": lambda x: x.replace('/', '\\')
        }
        
    def register_transformation(self, name: str, function: Callable[[str], str]) -> None:
        """Register a custom transformation function"""
        self.transformations[name] = function
        
    def get_transformation_names(self) -> List[str]:
        """Get list of available transformations"""
        return sorted(list(self.transformations.keys()))
        
    def transform(self, content: str, transformation: str) -> str:
        """Apply a transformation to content"""
        if transformation in self.transformations:
            try:
                return self.transformations[transformation](content)
            except Exception as e:
                logger.error(f"Error applying transformation '{transformation}': {e}")
                return content
        else:
            logger.warning(f"Unknown transformation: {transformation}")
            return content
        
    def copy_to_system_clipboard(self, content: str) -> bool:
        """Copy content to system clipboard"""
        try:
            # Try using pyperclip if available
            try:
                import pyperclip
                pyperclip.copy(content)
                return True
            except ImportError:
                pass
                
            # Platform-specific fallbacks
            if platform.system() == "Windows":
                # Windows clipboard access via subprocess
                try:
                    import win32clipboard
                    import win32con
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(content, win32con.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                    return True
                except ImportError:
                    # Fallback to PowerShell
                    import subprocess
                    powershell_script = f'Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.Clipboard]::SetText(\'{content.replace("'", "''")}\');'
                    subprocess.run(["powershell", "-Command", powershell_script], shell=True, check=False)
                    return True
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                process = subprocess.Popen(
                    ['pbcopy'],
                    stdin=subprocess.PIPE,
                    close_fds=True
                )
                process.communicate(content.encode('utf-8'))
                return True
            elif platform.system() == "Linux":
                # Try xclip or xsel
                for cmd in [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]:
                    try:
                        import subprocess
                        process = subprocess.Popen(
                            cmd,
                            stdin=subprocess.PIPE,
                            close_fds=True
                        )
                        process.communicate(content.encode('utf-8'))
                        return True
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
                        
            logger.warning("Could not access system clipboard. Install pyperclip for cross-platform clipboard support.")
            return False
        except Exception as e:
            logger.error(f"Error copying to system clipboard: {e}")
            return False
        
    def paste_from_system_clipboard(self) -> Optional[str]:
        """Get content from system clipboard"""
        try:
            # Try using pyperclip if available
            try:
                import pyperclip
                return pyperclip.paste()
            except ImportError:
                pass
                
            # Platform-specific fallbacks
            if platform.system() == "Windows":
                try:
                    import win32clipboard
                    import win32con
                    win32clipboard.OpenClipboard()
                    try:
                        data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        return data
                    finally:
                        win32clipboard.CloseClipboard()
                except ImportError:
                    # Fallback to PowerShell
                    import subprocess
                    powershell_script = 'Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.Clipboard]::GetText();'
                    result = subprocess.run(["powershell", "-Command", powershell_script], 
                                           capture_output=True, text=True, shell=True, check=False)
                    return result.stdout.strip()
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                result = subprocess.run(
                    ['pbpaste'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.stdout
            elif platform.system() == "Linux":
                # Try xclip or xsel
                for cmd in [['xclip', '-selection', 'clipboard', '-o'], ['xsel', '--clipboard', '--output']]:
                    try:
                        import subprocess
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        return result.stdout
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
                        
            logger.warning("Could not access system clipboard. Install pyperclip for cross-platform clipboard support.")
            return None
        except Exception as e:
            logger.error(f"Error pasting from system clipboard: {e}")
            return None
        
    def add_to_history(self, content: str, source: str = None, 
                       tags: List[str] = None, metadata: Dict[str, Any] = None) -> int:
        """Add item to clipboard history"""
        if not content:
            return -1
            
        # Remove duplicates of the same content (keep the most recent)
        self.history = [item for item in self.history if item.content != content]
        
        # Create new item
        item = ClipboardItem(
            content=content,
            source=source,
            tags=tags,
            metadata=metadata
        )
        
        # Add to history
        self.history.insert(0, item)
        self.current_index = 0
        
        # Trim history if exceeds max length
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
            
        # Save history
        self.save_history()
        
        return 0
    
    def copy(self, content: str, source: str = None, 
             tags: List[str] = None, metadata: Dict[str, Any] = None) -> bool:
        """Copy content to clipboard and history"""
        # Copy to system clipboard
        if not self.copy_to_system_clipboard(content):
            return False
            
        # Add to history
        self.add_to_history(content, source, tags, metadata)
        return True
    
    def paste(self) -> Optional[str]:
        """Paste current clipboard content"""
        if self.current_index < 0 or len(self.history) == 0:
            content = self.paste_from_system_clipboard()
            if content:
                self.add_to_history(content, source="system")
            return content
            
        return self.history[self.current_index].content
    
    def get_previous(self) -> Optional[str]:
        """Get previous item from history"""
        if len(self.history) == 0:
            return None
            
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            
        return self.history[self.current_index].content
    
    def get_next(self) -> Optional[str]:
        """Get next item from history"""
        if len(self.history) == 0:
            return None
            
        if self.current_index > 0:
            self.current_index -= 1
            
        return self.history[self.current_index].content
    
    def get_history(self) -> List[ClipboardItem]:
        """Get clipboard history"""
        return self.history
    
    def clear_history(self) -> None:
        """Clear clipboard history"""
        self.history = []
        self.current_index = -1
        self.save_history()
    
    def save_history(self) -> bool:
        """Save history to file"""
        try:
            with open(self.history_file, 'w') as f:
                data = [item.to_dict() for item in self.history]
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving clipboard history: {e}")
            return False
    
    def load_history(self) -> bool:
        """Load history from file"""
        if not os.path.exists(self.history_file):
            return False
            
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.history = [ClipboardItem.from_dict(item) for item in data]
                self.current_index = 0 if self.history else -1
            return True
        except Exception as e:
            logger.error(f"Error loading clipboard history: {e}")
            return False
    
    def search_history(self, query: str) -> List[ClipboardItem]:
        """Search clipboard history"""
        if not query:
            return self.history
            
        return [item for item in self.history 
                if query.lower() in item.content.lower() or 
                any(query.lower() in tag.lower() for tag in item.tags)]
                
    def get_item_by_index(self, index: int) -> Optional[ClipboardItem]:
        """Get history item by index"""
        if 0 <= index < len(self.history):
            return self.history[index]
        return None
    
    def extract_elements(self, pattern: str) -> List[str]:
        """Extract elements from current clipboard using regex pattern"""
        current = self.paste()
        if not current:
            return []
            
        try:
            matches = re.findall(pattern, current)
            return matches if isinstance(matches[0], str) else \
                   [m[0] if isinstance(m, tuple) else m for m in matches]
        except (IndexError, re.error):
            return []
    
    def apply_transformation(self, transformation: str) -> Optional[str]:
        """Apply transformation to current clipboard and update it"""
        current = self.paste()
        if not current:
            return None
            
        transformed = self.transform(current, transformation)
        if transformed != current:
            self.copy(transformed, source=f"transform:{transformation}")
            
        return transformed 