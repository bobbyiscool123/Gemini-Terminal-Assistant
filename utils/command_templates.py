"""
Command Templates Module
Provides support for templated commands with parameter substitution
"""
import os
import re
import json
import yaml
from typing import Dict, List, Optional, Any

class CommandTemplate:
    """Represents a single command template with parameters"""
    
    def __init__(self, name: str, template: str, description: str = "", params: Dict[str, Any] = None):
        self.name = name
        self.template = template
        self.description = description
        self.params = params or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization"""
        return {
            "name": self.name,
            "template": self.template,
            "description": self.description,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandTemplate':
        """Create template from dictionary"""
        return cls(
            name=data.get("name", ""),
            template=data.get("template", ""),
            description=data.get("description", ""),
            params=data.get("params", {})
        )
    
    def get_param_names(self) -> List[str]:
        """Extract parameter names from template string"""
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, self.template)
        return list(set(matches))
    
    def render(self, params: Dict[str, str] = None) -> str:
        """Render the template with the provided parameters"""
        if not params:
            return self.template
            
        result = self.template
        for key, value in params.items():
            result = result.replace(f"{{{{{key}}}}}", value)
        
        # Check for any remaining unresolved parameters
        unresolved = self.get_param_names()
        if unresolved:
            remaining = [param for param in unresolved if f"{{{{{param}}}}}" in result]
            if remaining:
                raise ValueError(f"Missing required parameters: {', '.join(remaining)}")
                
        return result

class CommandTemplateManager:
    """Manages command templates"""
    
    def __init__(self, template_file: str = "command_templates.yaml"):
        self.template_file = template_file
        self.templates: Dict[str, CommandTemplate] = {}
        self.load_templates()
    
    def load_templates(self) -> None:
        """Load templates from file"""
        if not os.path.exists(self.template_file):
            self._initialize_default_templates()
            return
            
        try:
            with open(self.template_file, 'r') as f:
                data = yaml.safe_load(f)
                if not data:
                    return
                    
                for name, template_data in data.items():
                    self.templates[name] = CommandTemplate.from_dict({
                        "name": name,
                        **template_data
                    })
        except Exception as e:
            print(f"Error loading templates: {str(e)}")
    
    def save_templates(self) -> None:
        """Save templates to file"""
        try:
            data = {}
            for name, template in self.templates.items():
                template_dict = template.to_dict()
                # Remove name as it's already the key
                del template_dict["name"]
                data[name] = template_dict
                
            with open(self.template_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving templates: {str(e)}")
    
    def _initialize_default_templates(self) -> None:
        """Initialize with default templates"""
        defaults = {
            "find_files": CommandTemplate(
                name="find_files",
                template="find {{directory}} -name \"{{pattern}}\" {{options}}",
                description="Find files matching a pattern",
                params={
                    "directory": {"description": "Directory to search in", "default": "."},
                    "pattern": {"description": "File pattern to match", "default": "*.txt"},
                    "options": {"description": "Additional find options", "default": ""}
                }
            ),
            "backup_file": CommandTemplate(
                name="backup_file",
                template="cp {{file}} {{file}}.bak",
                description="Create a backup of a file",
                params={
                    "file": {"description": "File to backup", "default": ""}
                }
            ),
            "extract_archive": CommandTemplate(
                name="extract_archive",
                template="{{command}} {{archive}} {{options}}",
                description="Extract an archive file",
                params={
                    "command": {"description": "Extraction command", "default": "tar -xf",
                               "choices": ["tar -xf", "unzip", "7z x"]},
                    "archive": {"description": "Archive to extract", "default": ""},
                    "options": {"description": "Additional options", "default": ""}
                }
            ),
            "system_info": CommandTemplate(
                name="system_info",
                template="{{command}}",
                description="Get system information",
                params={
                    "command": {"description": "Information command", "default": "systeminfo",
                               "choices": ["systeminfo", "hostname", "whoami", "ipconfig /all"]}
                }
            ),
            "git_clone": CommandTemplate(
                name="git_clone",
                template="git clone {{repository}} {{directory}}",
                description="Clone a git repository",
                params={
                    "repository": {"description": "Repository URL", "default": ""},
                    "directory": {"description": "Target directory", "default": ""}
                }
            )
        }
        
        self.templates = defaults
        self.save_templates()
    
    def get_template(self, name: str) -> Optional[CommandTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
        
    def add_template(self, template: CommandTemplate) -> None:
        """Add a new template"""
        self.templates[template.name] = template
        self.save_templates()
        
    def remove_template(self, name: str) -> bool:
        """Remove a template by name"""
        if name in self.templates:
            del self.templates[name]
            self.save_templates()
            return True
        return False
    
    def get_all_templates(self) -> Dict[str, CommandTemplate]:
        """Get all available templates"""
        return self.templates
    
    def render_template(self, name: str, params: Dict[str, str] = None) -> Optional[str]:
        """Render a template with parameters"""
        template = self.get_template(name)
        if not template:
            return None
            
        try:
            return template.render(params)
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Error rendering template '{name}': {str(e)}")
        
    def get_template_params(self, name: str) -> Optional[Dict[str, Any]]:
        """Get parameters for a template"""
        template = self.get_template(name)
        if not template:
            return None
            
        return template.params 