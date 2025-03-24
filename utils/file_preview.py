"""
File Preview Module
Provides functionality to preview various file types in the terminal
"""
import os
import mimetypes
import subprocess
from typing import Optional, Dict, List, Tuple
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.console import Console

# Ensure mime types are initialized
mimetypes.init()

class FilePreview:
    """File preview utility for displaying file contents in the terminal"""
    
    # Dictionary mapping mime types to preview functions
    PREVIEW_HANDLERS = {
        "text/": "_preview_text",
        "application/json": "_preview_json",
        "application/xml": "_preview_text",
        "application/yaml": "_preview_text",
        "application/x-yaml": "_preview_text",
        "text/markdown": "_preview_markdown",
        "text/csv": "_preview_csv",
        "image/": "_preview_image",
        "application/pdf": "_preview_pdf",
    }
    
    # Dictionary mapping file extensions to syntax highlighting languages
    SYNTAX_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".bat": "batch",
        ".ps1": "powershell",
        ".sql": "sql",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".java": "java",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".txt": "text",
    }
    
    def __init__(self, config: Dict = None):
        """Initialize the file preview utility"""
        self.config = config or {}
        self.console = Console()
        self.max_file_size = self.config.get("max_file_preview_size_kb", 1024) * 1024  # Convert to bytes
    
    def get_preview(self, file_path: str, max_lines: int = 50) -> Optional[str]:
        """Get a preview of a file based on its type"""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return f"Error: File not found: {file_path}"
            
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return f"Error: File too large for preview ({file_size / 1024 / 1024:.2f} MB)"
            
        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if not mime_type:
            # Fallback to extension-based detection
            if file_ext in self.SYNTAX_LANGUAGES:
                mime_type = "text/plain"
        
        # Find appropriate preview handler
        handler = None
        if mime_type:
            for mime_prefix, handler_name in self.PREVIEW_HANDLERS.items():
                if mime_type.startswith(mime_prefix):
                    handler = getattr(self, handler_name)
                    break
        
        # Default to text preview if no handler found and file seems to be text
        if not handler and self._is_text_file(file_path):
            handler = getattr(self, "_preview_text")
        
        # If no handler, just show file info
        if not handler:
            return self._get_file_info(file_path)
            
        try:
            return handler(file_path, max_lines, mime_type)
        except Exception as e:
            return f"Error previewing file: {str(e)}"
    
    def _is_text_file(self, file_path: str) -> bool:
        """Determine if a file is likely a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read a bit of the file
            return True
        except UnicodeDecodeError:
            return False
    
    def _get_file_info(self, file_path: str) -> str:
        """Get information about a file"""
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return (
            f"File: {os.path.basename(file_path)}\n"
            f"Size: {self._format_size(file_size)}\n"
            f"Type: {mime_type or 'Unknown'}\n"
            f"Path: {os.path.abspath(file_path)}"
        )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    
    def _preview_text(self, file_path: str, max_lines: int = 50, mime_type: str = None) -> str:
        """Preview a text file with syntax highlighting"""
        # Determine language for syntax highlighting
        file_ext = os.path.splitext(file_path)[1].lower()
        language = self.SYNTAX_LANGUAGES.get(file_ext, "text")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = "".join(f.readlines()[:max_lines])
            
        # Check if content was truncated
        truncated = False
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, _ in enumerate(f, 1):
                if i > max_lines:
                    truncated = True
                    break
        
        # Create syntax highlighted preview
        syntax = Syntax(content, language, word_wrap=True)
        
        # Return as string representation
        if truncated:
            return str(syntax) + f"\n\n[Showing first {max_lines} lines of {file_path}]"
        else:
            return str(syntax)
    
    def _preview_json(self, file_path: str, max_lines: int = 50, mime_type: str = None) -> str:
        """Preview a JSON file"""
        import json
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            try:
                content = json.load(f)
                # Pretty-print with indentation
                formatted = json.dumps(content, indent=2)
                
                # Truncate if necessary
                lines = formatted.split('\n')
                if len(lines) > max_lines:
                    lines = lines[:max_lines]
                    truncated = True
                else:
                    truncated = False
                    
                result = '\n'.join(lines)
                
                # Syntax highlight
                syntax = Syntax(result, "json", word_wrap=True)
                
                # Return as string representation
                if truncated:
                    return str(syntax) + f"\n\n[Showing first {max_lines} lines of {file_path}]"
                else:
                    return str(syntax)
            except json.JSONDecodeError:
                # Fallback to text preview if invalid JSON
                return self._preview_text(file_path, max_lines)
    
    def _preview_markdown(self, file_path: str, max_lines: int = 50, mime_type: str = None) -> str:
        """Preview a markdown file"""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = "".join(f.readlines()[:max_lines])
            
        # Check if content was truncated
        truncated = False
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, _ in enumerate(f, 1):
                if i > max_lines:
                    truncated = True
                    break
        
        # Create markdown preview
        md = Markdown(content)
        
        # Return as string representation
        if truncated:
            return str(md) + f"\n\n[Showing first {max_lines} lines of {file_path}]"
        else:
            return str(md)
    
    def _preview_csv(self, file_path: str, max_lines: int = 20, mime_type: str = None) -> str:
        """Preview a CSV file as a table"""
        import csv
        
        table = Table(title=os.path.basename(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                
                # Read header row
                try:
                    headers = next(reader)
                    for header in headers:
                        table.add_column(header)
                except StopIteration:
                    # Empty file
                    return f"Empty CSV file: {file_path}"
                
                # Read data rows (limited to max_lines-1 for the header)
                for i, row in enumerate(reader):
                    if i >= max_lines - 1:
                        break
                    table.add_row(*row)
            
            # Check if content was truncated
            truncated = False
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                for i, _ in enumerate(reader, 1):
                    if i > max_lines:
                        truncated = True
                        break
            
            result = str(table)
            if truncated:
                result += f"\n\n[Showing first {max_lines} lines of {file_path}]"
            
            return result
        except Exception:
            # Fallback to text preview if parsing fails
            return self._preview_text(file_path, max_lines)
            
    def _preview_image(self, file_path: str, max_lines: int = 50, mime_type: str = None) -> str:
        """Show information about an image file"""
        try:
            # Try to get image dimensions if Pillow is available
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode
                format = img.format
                
                return (
                    f"Image: {os.path.basename(file_path)}\n"
                    f"Format: {format}\n"
                    f"Dimensions: {width}x{height}\n"
                    f"Mode: {mode}\n"
                    f"Size: {self._format_size(os.path.getsize(file_path))}\n"
                    f"Path: {os.path.abspath(file_path)}\n\n"
                    f"[Use an external viewer to see this image]"
                )
        except (ImportError, Exception):
            # Fallback to basic file info
            return self._get_file_info(file_path) + "\n\n[Use an external viewer to see this image]"
    
    def _preview_pdf(self, file_path: str, max_lines: int = 50, mime_type: str = None) -> str:
        """Show information about a PDF file"""
        try:
            # Get PDF info if PyPDF2 is available
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            
            info = reader.metadata
            num_pages = len(reader.pages)
            
            # Extract some text from the first page
            first_page_text = reader.pages[0].extract_text()
            if first_page_text:
                first_page_text = '\n'.join(first_page_text.split('\n')[:10])
                if len(first_page_text.split('\n')) >= 10:
                    first_page_text += "\n[...]"
            
            result = (
                f"PDF: {os.path.basename(file_path)}\n"
                f"Pages: {num_pages}\n"
                f"Size: {self._format_size(os.path.getsize(file_path))}\n"
            )
            
            if info:
                if info.title:
                    result += f"Title: {info.title}\n"
                if info.author:
                    result += f"Author: {info.author}\n"
                if info.creator:
                    result += f"Creator: {info.creator}\n"
                    
            if first_page_text:
                result += f"\nFirst page preview:\n{first_page_text}"
                
            return result
        except ImportError:
            # PyPDF2 not available
            return self._get_file_info(file_path) + "\n\n[Install PyPDF2 to see PDF contents]"
        except Exception as e:
            # Error processing PDF
            return f"{self._get_file_info(file_path)}\n\nError reading PDF: {str(e)}" 