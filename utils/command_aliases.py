"""
Command aliases functionality for Terminal AI Assistant
Provides support for custom command shortcuts and aliases
"""
import os
import yaml
from typing import Dict, Optional

class CommandAliases:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the command aliases handler"""
        self.config_path = config_path
        self.aliases = {}
        self.load_aliases()
    
    def load_aliases(self) -> None:
        """Load aliases from the configuration file"""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                if config and 'custom_command_aliases' in config:
                    self.aliases = config['custom_command_aliases'] or {}
        except Exception as e:
            print(f"Error loading aliases: {str(e)}")
    
    def save_aliases(self) -> bool:
        """Save aliases to the configuration file"""
        if not os.path.exists(self.config_path):
            return False
            
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            config['custom_command_aliases'] = self.aliases
            
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving aliases: {str(e)}")
            return False
    
    def expand_alias(self, command: str) -> str:
        """Expand a command if it contains an alias"""
        if not command:
            return command
            
        # Split the command to check if the first word is an alias
        parts = command.split(maxsplit=1)
        if not parts:
            return command
            
        potential_alias = parts[0]
        if potential_alias in self.aliases:
            # Replace the alias with its expansion
            if len(parts) > 1:
                return f"{self.aliases[potential_alias]} {parts[1]}"
            else:
                return self.aliases[potential_alias]
        
        return command
    
    def add_alias(self, alias: str, command: str) -> bool:
        """Add a new alias"""
        if not alias or not command:
            return False
            
        self.aliases[alias] = command
        return self.save_aliases()
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an existing alias"""
        if alias in self.aliases:
            del self.aliases[alias]
            return self.save_aliases()
        return False
    
    def get_aliases(self) -> Dict[str, str]:
        """Get all defined aliases"""
        return self.aliases
    
    def clear_aliases(self) -> bool:
        """Clear all aliases"""
        self.aliases = {}
        return self.save_aliases() 