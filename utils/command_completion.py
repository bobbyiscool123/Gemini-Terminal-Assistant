"""
Command Completion Module
Provides tab completion functionality for commands and file paths.
"""
import os
import re
import subprocess
from typing import List, Callable, Dict, Set, Optional

class CommandCompleter:
    def __init__(self, current_directory: str = None):
        self.current_directory = current_directory or os.getcwd()
        self.user_defined_completions: Dict[str, List[str]] = {}
        self.command_cache: Set[str] = set()
        self.refresh_command_cache()
    
    def refresh_command_cache(self) -> None:
        """Refresh the cache of available commands"""
        # Windows command discovery
        if os.name == 'nt':
            try:
                # Get commands from PATH
                paths = os.environ.get('PATH', '').split(os.pathsep)
                for path in paths:
                    if os.path.exists(path):
                        for file in os.listdir(path):
                            if file.endswith(('.exe', '.bat', '.cmd')):
                                self.command_cache.add(os.path.splitext(file)[0])
                
                # Add CMD built-ins
                builtin_commands = [
                    'cd', 'dir', 'copy', 'del', 'md', 'mkdir', 'move', 'rd', 'rmdir', 
                    'rename', 'ren', 'replace', 'type', 'more', 'find', 'findstr', 
                    'cls', 'echo', 'set', 'if', 'for', 'goto', 'call', 'start'
                ]
                self.command_cache.update(builtin_commands)
            except Exception:
                pass
        # Unix-like command discovery
        else:
            try:
                # Use which -a to find all commands
                completions = []
                paths = os.environ.get('PATH', '').split(os.pathsep)
                for path in paths:
                    if os.path.exists(path):
                        for file in os.listdir(path):
                            filepath = os.path.join(path, file)
                            if os.access(filepath, os.X_OK) and os.path.isfile(filepath):
                                completions.append(file)
                self.command_cache.update(completions)
            except Exception:
                pass
    
    def set_directory(self, directory: str) -> None:
        """Set the current directory for file completions"""
        self.current_directory = directory
    
    def add_user_completion(self, prefix: str, completions: List[str]) -> None:
        """Add user-defined completions for a specific prefix"""
        self.user_defined_completions[prefix] = completions
    
    def remove_user_completion(self, prefix: str) -> None:
        """Remove user-defined completions for a specific prefix"""
        if prefix in self.user_defined_completions:
            del self.user_defined_completions[prefix]
    
    def get_command_completions(self, prefix: str) -> List[str]:
        """Get command completions for the given prefix"""
        return [cmd for cmd in self.command_cache if cmd.startswith(prefix)]
    
    def get_file_completions(self, prefix: str) -> List[str]:
        """Get file completions for the given prefix"""
        completions = []
        
        # Handle absolute path vs relative path
        if os.path.isabs(prefix):
            directory = os.path.dirname(prefix) if prefix else "/"
            base = os.path.basename(prefix)
        else:
            directory = self.current_directory
            if os.path.dirname(prefix):
                directory = os.path.join(directory, os.path.dirname(prefix))
            base = os.path.basename(prefix)
        
        # Ensure directory exists
        if not os.path.isdir(directory):
            return []
        
        # Get matching files and directories
        try:
            for item in os.listdir(directory):
                if item.startswith(base):
                    full_path = os.path.join(directory, item)
                    if os.path.isdir(full_path):
                        # Add directory separator
                        completions.append(f"{item}{os.path.sep}")
                    else:
                        completions.append(item)
        except Exception:
            pass
            
        return completions
    
    def get_git_completions(self, args: List[str]) -> List[str]:
        """Get git-specific completions"""
        if not args:
            # Git commands
            git_commands = [
                'add', 'branch', 'checkout', 'clone', 'commit', 'diff', 'fetch',
                'init', 'log', 'merge', 'pull', 'push', 'rebase', 'reset',
                'restore', 'status', 'stash', 'tag'
            ]
            return git_commands
        
        command = args[0]
        
        # Command-specific completions
        if command == 'checkout':
            try:
                # Get branches
                proc = subprocess.run(['git', 'branch'], capture_output=True, text=True, shell=True)
                branches = []
                for line in proc.stdout.splitlines():
                    branch = line.strip()
                    if branch.startswith('*'):
                        branch = branch[1:].strip()
                    branches.append(branch)
                return branches
            except Exception:
                return []
        elif command in ['add', 'restore']:
            return self.get_file_completions('')
        
        return []
    
    def complete(self, text: str) -> List[str]:
        """Complete the given text with appropriate suggestions"""
        # Empty input - show available commands
        if not text:
            return list(sorted(self.command_cache))[:10]  # Limit to 10 suggestions
        
        # Check if we're dealing with a git command
        if text.startswith('git '):
            parts = text.split()
            if len(parts) > 1:
                return self.get_git_completions(parts[1:])
            else:
                return self.get_git_completions([])
        
        # Check for user-defined completions
        for prefix, completions in self.user_defined_completions.items():
            if text.startswith(prefix):
                suffix = text[len(prefix):]
                return [f"{prefix}{c}" for c in completions if c.startswith(suffix)]
        
        # If text contains a space, assume it's a command with arguments
        if ' ' in text:
            cmd, partial_arg = text.rsplit(' ', 1)
            
            # Complete file paths
            file_completions = self.get_file_completions(partial_arg)
            return [f"{cmd} {completion}" for completion in file_completions]
        
        # Otherwise, complete command names
        return self.get_command_completions(text)

class TabCompleter:
    def __init__(self, command_completer: CommandCompleter):
        self.command_completer = command_completer
        self.completions: List[str] = []
        self.index = 0
    
    def get_completions(self, text: str) -> List[str]:
        """Get completions for the given text"""
        self.completions = self.command_completer.complete(text)
        self.index = 0
        return self.completions
    
    def get_next_completion(self, text: str) -> Optional[str]:
        """Get next completion in the cycle"""
        if not self.completions:
            self.completions = self.get_completions(text)
            if not self.completions:
                return None
        
        # Cycle through completions
        if self.index >= len(self.completions):
            self.index = 0
        
        completion = self.completions[self.index]
        self.index += 1
        return completion
    
    def reset(self) -> None:
        """Reset completion state"""
        self.completions = []
        self.index = 0 