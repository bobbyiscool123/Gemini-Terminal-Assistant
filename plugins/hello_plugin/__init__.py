"""
Hello Plugin
A simple example plugin for Terminal AI Assistant
"""
from utils.plugin_manager import Plugin
from typing import Dict, List, Callable
import platform
import psutil
import time
import random

class HelloPlugin(Plugin):
    """Hello Plugin provides simple greeting and system info commands"""
    name = "hello_plugin"
    description = "Simple plugin with greeting and system info commands"
    version = "1.0.0"
    
    def __init__(self, terminal_assistant=None):
        super().__init__(terminal_assistant)
        # Store some configuration
        self.greetings = [
            "Hello there!",
            "Hi! How are you?",
            "Greetings, human!",
            "Hello! Nice to see you!",
            "Hi there! Ready to help!"
        ]
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        # Perform any setup needed
        return True
    
    def cleanup(self) -> bool:
        """Clean up any resources used by the plugin"""
        # Nothing to clean up
        return True
    
    def get_commands(self) -> Dict[str, Callable]:
        """Get commands provided by this plugin"""
        return {
            "hello": self.hello_command,
            "systeminfo": self.system_info_command,
            "joke": self.joke_command,
        }
    
    def get_completions(self) -> Dict[str, List[str]]:
        """Get command completions provided by this plugin"""
        return {
            "hello": ["world", "there", "friend"],
            "systeminfo": ["brief", "detailed", "memory", "cpu", "disk"],
            "joke": []
        }
    
    def on_command_pre(self, command: str) -> str:
        """Called before a command is executed"""
        # Example of modifying commands - add 'echo Command intercepted:'
        # before any echo command
        if command.startswith("echo hello") and not "plugin intercepted" in command:
            return command + " (plugin intercepted)"
        return command
    
    def on_command_post(self, command: str, result: Dict) -> Dict:
        """Called after a command is executed"""
        # Add a note to successful commands
        if result.get("exit_code", 1) == 0:
            if not result.get("plugin", False):  # Don't modify plugin commands
                result["stdout"] = result.get("stdout", "") + "\n[Processed by hello_plugin]"
        return result
    
    def hello_command(self, *args) -> str:
        """Say hello with optional name"""
        if args:
            name = " ".join(args)
            return f"Hello, {name}! 👋\nGreetings from the hello_plugin."
        else:
            greeting = random.choice(self.greetings)
            return f"{greeting} 👋\nI'm the hello_plugin, ready to assist you!"
    
    def system_info_command(self, *args) -> str:
        """Show system information"""
        mode = args[0].lower() if args else "brief"
        
        info = [f"System: {platform.system()} {platform.release()} ({platform.version()})"]
        info.append(f"Machine: {platform.machine()}")
        info.append(f"Processor: {platform.processor()}")
        
        if mode == "detailed" or mode == "memory":
            # Memory information
            mem = psutil.virtual_memory()
            info.append(f"\nMemory Usage:")
            info.append(f"  Total: {self._format_bytes(mem.total)}")
            info.append(f"  Available: {self._format_bytes(mem.available)}")
            info.append(f"  Used: {self._format_bytes(mem.used)} ({mem.percent}%)")
            
        if mode == "detailed" or mode == "cpu":
            # CPU information
            info.append(f"\nCPU Usage:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
                info.append(f"  Core {i+1}: {percentage}%")
            info.append(f"  Overall: {psutil.cpu_percent()}%")
            
        if mode == "detailed" or mode == "disk":
            # Disk information
            info.append(f"\nDisk Usage:")
            for part in psutil.disk_partitions(all=False):
                if part.fstype:
                    usage = psutil.disk_usage(part.mountpoint)
                    info.append(f"  {part.device} ({part.mountpoint}):")
                    info.append(f"    Total: {self._format_bytes(usage.total)}")
                    info.append(f"    Used: {self._format_bytes(usage.used)} ({usage.percent}%)")
                    info.append(f"    Free: {self._format_bytes(usage.free)}")
        
        return "\n".join(info)
    
    def joke_command(self, *args) -> str:
        """Tell a programming joke"""
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why do programmers always mix up Christmas and Halloween? Because Oct 31 == Dec 25!",
            "A programmer's wife tells him: 'Go to the store and buy a loaf of bread. If they have eggs, buy a dozen.' The programmer returns with 12 loaves of bread.",
            "Why don't programmers like nature? It has too many bugs and no debugging tool.",
            "Two SQL tables are sitting at a bar. A query walks in and asks 'May I join you?'",
            "Why are keyboards always working so hard? Because they have two shifts!",
            "What's a pirate's favorite programming language? R!",
            "What's the object-oriented way to become wealthy? Inheritance!",
            "Why did the programmer quit his job? Because he didn't get arrays (a raise)!",
            "What did the computer do at lunchtime? Had a byte!"
        ]
        return random.choice(jokes)
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024 or unit == 'TB':
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024 