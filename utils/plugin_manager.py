"""
Plugin Manager Module
Provides a plugin system to extend the terminal assistant's functionality.
"""
import os
import sys
import importlib
import inspect
import pkgutil
import yaml
from typing import Dict, List, Any, Callable, Optional, Set, Type

class Plugin:
    """Base class for all plugins"""
    name = "base_plugin"
    description = "Base plugin class"
    version = "0.1.0"
    
    def __init__(self, terminal_assistant=None):
        self.terminal_assistant = terminal_assistant
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        return True
    
    def cleanup(self) -> bool:
        """Clean up any resources used by the plugin"""
        return True
    
    def get_commands(self) -> Dict[str, Callable]:
        """Get commands provided by this plugin"""
        return {}
    
    def get_completions(self) -> Dict[str, List[str]]:
        """Get command completions provided by this plugin"""
        return {}
    
    def on_command_pre(self, command: str) -> str:
        """Called before a command is executed"""
        return command
    
    def on_command_post(self, command: str, result: Dict) -> Dict:
        """Called after a command is executed"""
        return result
    
    def help(self) -> str:
        """Get help for this plugin"""
        commands = self.get_commands()
        if not commands:
            return f"{self.name} v{self.version}: {self.description}\nNo commands provided."
        
        help_text = [f"{self.name} v{self.version}: {self.description}", "Commands:"]
        for cmd_name in sorted(commands.keys()):
            cmd_func = commands[cmd_name]
            doc = cmd_func.__doc__ or "No documentation"
            help_text.append(f"  {cmd_name}: {doc}")
        
        return "\n".join(help_text)

class PluginManager:
    """Manages plugins for the terminal assistant"""
    def __init__(self, plugins_dir: str = "plugins", config_file: str = "plugins.yaml"):
        self.plugins_dir = plugins_dir
        self.config_file = config_file
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_commands: Dict[str, Callable] = {}
        self.disabled_plugins: Set[str] = set()
        self.terminal_assistant = None
        
        # Ensure plugins directory exists
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Add plugins directory to path
        plugins_path = os.path.abspath(self.plugins_dir)
        if plugins_path not in sys.path:
            sys.path.insert(0, plugins_path)
    
    def set_terminal_assistant(self, terminal_assistant) -> None:
        """Set the terminal assistant reference"""
        self.terminal_assistant = terminal_assistant
        
        # Update assistant reference in existing plugins
        for plugin in self.plugins.values():
            plugin.terminal_assistant = terminal_assistant
    
    def load_config(self) -> None:
        """Load plugin configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and "disabled_plugins" in config:
                        self.disabled_plugins = set(config["disabled_plugins"])
            except Exception:
                pass
    
    def save_config(self) -> None:
        """Save plugin configuration"""
        config = {
            "disabled_plugins": list(self.disabled_plugins)
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        # Check if plugins directory exists
        if not os.path.isdir(self.plugins_dir):
            return discovered
        
        # Look for plugin modules
        for _, name, ispkg in pkgutil.iter_modules([self.plugins_dir]):
            if ispkg:  # Only consider packages
                discovered.append(name)
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin by name"""
        if plugin_name in self.plugins:
            return True  # Already loaded
        
        if plugin_name in self.disabled_plugins:
            return False  # Disabled
        
        try:
            # Import the plugin module
            module = importlib.import_module(plugin_name)
            
            # Find plugin classes (subclasses of Plugin)
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                print(f"No plugin class found in {plugin_name}")
                return False
            
            # Use the first plugin class found
            plugin_class = plugin_classes[0]
            plugin = plugin_class(self.terminal_assistant)
            
            # Initialize the plugin
            if not plugin.initialize():
                print(f"Failed to initialize {plugin_name}")
                return False
            
            # Register plugin commands
            commands = plugin.get_commands()
            for cmd_name, cmd_func in commands.items():
                self.plugin_commands[cmd_name] = cmd_func
            
            # Store the plugin instance
            self.plugins[plugin_name] = plugin
            
            return True
        
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {str(e)}")
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """Load all available plugins"""
        self.load_config()
        discovered = self.discover_plugins()
        results = {}
        
        for plugin_name in discovered:
            results[plugin_name] = self.load_plugin(plugin_name)
        
        return results
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Clean up plugin resources
        plugin.cleanup()
        
        # Remove plugin commands
        commands = plugin.get_commands()
        for cmd_name in commands:
            if cmd_name in self.plugin_commands:
                del self.plugin_commands[cmd_name]
        
        # Remove plugin
        del self.plugins[plugin_name]
        
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a disabled plugin"""
        if plugin_name in self.disabled_plugins:
            self.disabled_plugins.remove(plugin_name)
            self.save_config()
            return self.load_plugin(plugin_name)
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        # Unload the plugin if it's loaded
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
        
        # Mark as disabled
        self.disabled_plugins.add(plugin_name)
        self.save_config()
        
        return True
    
    def get_plugin_completions(self) -> Dict[str, List[str]]:
        """Get completions from all plugins"""
        completions = {}
        
        for plugin in self.plugins.values():
            plugin_completions = plugin.get_completions()
            completions.update(plugin_completions)
        
        return completions
    
    def execute_plugin_command(self, command: str, args: List[str]) -> Optional[Dict]:
        """Execute a plugin command"""
        if command in self.plugin_commands:
            try:
                result = self.plugin_commands[command](*args)
                return {
                    "command": f"{command} {' '.join(args)}",
                    "stdout": result if isinstance(result, str) else str(result),
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": 0,
                    "plugin": True
                }
            except Exception as e:
                return {
                    "command": f"{command} {' '.join(args)}",
                    "stdout": "",
                    "stderr": f"Error executing plugin command: {str(e)}",
                    "exit_code": 1,
                    "execution_time": 0,
                    "plugin": True
                }
        return None
    
    def pre_process_command(self, command: str) -> str:
        """Pre-process a command through all plugins"""
        for plugin in self.plugins.values():
            command = plugin.on_command_pre(command)
        return command
    
    def post_process_result(self, command: str, result: Dict) -> Dict:
        """Post-process a command result through all plugins"""
        for plugin in self.plugins.values():
            result = plugin.on_command_post(command, result)
        return result
    
    def get_plugin_info(self) -> List[Dict]:
        """Get information about loaded plugins"""
        info = []
        
        for name, plugin in self.plugins.items():
            info.append({
                "name": name,
                "description": plugin.description,
                "version": plugin.version,
                "commands": list(plugin.get_commands().keys())
            })
        
        return info
    
    def get_plugin_help(self, plugin_name: str = None) -> str:
        """Get help for a specific plugin or all plugins"""
        if plugin_name:
            if plugin_name in self.plugins:
                return self.plugins[plugin_name].help()
            return f"Plugin '{plugin_name}' not found"
        
        # Help for all plugins
        if not self.plugins:
            return "No plugins loaded"
        
        help_text = ["Loaded Plugins:"]
        for name, plugin in sorted(self.plugins.items()):
            help_text.append(f"- {name} (v{plugin.version}): {plugin.description}")
        
        return "\n".join(help_text) 