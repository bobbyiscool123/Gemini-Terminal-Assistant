#!/usr/bin/env python3
"""
Prompt Management for Gemini Terminal Assistant
This module handles all prompt formatting and templates for the Gemini AI model
"""
import os
import yaml
import re
import json
import platform
from typing import Dict, List, Optional, Union, Any

# Import Gemini API
import google.generativeai as genai

# Configure API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
else:
    print("Warning: GOOGLE_API_KEY not found in environment variables")
    MODEL = None

class PromptManager:
    """Manages prompts for the Gemini Terminal Assistant"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the prompt manager"""
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.yaml")
        self.templates = {}
        self.system_prompts = {}
        self.load_templates()
    
    def load_templates(self):
        """Load prompt templates from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f)
                
                # Load prompt templates if available
                self.templates = config.get("prompt_templates", {})
                self.system_prompts = config.get("system_prompts", {})
        except Exception as e:
            print(f"Error loading prompt templates: {str(e)}")
            # Initialize with empty defaults if loading fails
            self.templates = {}
            self.system_prompts = {}
    
    def get_system_prompt(self, prompt_type: str) -> str:
        """Get a system prompt by type"""
        return self.system_prompts.get(prompt_type, "")
    
    def get_template(self, template_name: str) -> str:
        """Get a prompt template by name"""
        return self.templates.get(template_name, "")
    
    def format_command_prompt(self, task: str, context: Optional[Dict] = None) -> str:
        """Format a prompt for command generation"""
        template = self.get_template("command_generation")
        if not template:
            # Default template if none is found
            template = """
            Given the user task: "{task}", 
            Generate a safe and effective command to execute this task in the terminal.
            If multiple commands are needed, list them in sequence.
            Context information: {context}
            """
        
        # Format the template with task and context
        context_str = str(context) if context else "No additional context"
        return template.format(task=task, context=context_str)
    
    def format_task_planning_prompt(self, task: str, system_info: Dict) -> str:
        """Format a prompt for task planning"""
        template = self.get_template("task_planning")
        if not template:
            # Default template if none is found
            template = """
            Given the user task: "{task}",
            Create a plan to accomplish this task.
            Break it down into logical steps.
            System information: {system_info}
            """
        
        return template.format(task=task, system_info=str(system_info))
    
    def format_mcp_prompt(self, task: str, context: Dict) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """Format a complete MCP (Model Context Protocol) prompt for Gemini"""
        # Get the system prompt for general context
        system_prompt = self.get_system_prompt("general")
        
        # Build the full prompt structure for Gemini API
        prompt = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Task: {task}"}]
                }
            ]
        }
        
        # Add system prompt if available
        if system_prompt:
            prompt["contents"].insert(0, {
                "role": "system",
                "parts": [{"text": system_prompt}]
            })
        
        # Add context if provided
        if context:
            # Convert context to a formatted string
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt["contents"].insert(1, {
                "role": "system",
                "parts": [{"text": f"Context:\n{context_str}"}]
            })
        
        return prompt

# Initialize a global instance for easy importing
prompt_manager = PromptManager() 

def generate_command(task: str, config: Optional[Dict] = None) -> str:
    """Generate a terminal command from a natural language request using Gemini API"""
    if not MODEL:
        print("Error: Gemini API not configured. Please set GOOGLE_API_KEY environment variable.")
        return ""
        
    try:
        # Get system context for better command generation
        system_context = {
            "current_directory": os.getcwd(),
            "platform": platform.system(),
            "user": os.getenv("USER") or os.getenv("USERNAME")
        }
        
        # Get appropriate template from config
        template = ""
        command_verification_level = "medium"
        
        if config:
            # If config is provided, get command template and verification level
            if config.get("enable_command_templates", False):
                template = config.get("prompt_templates", {}).get("command_generation", "")
            command_verification_level = config.get("command_verification_level", "medium")
        
        # If no template from config, use default
        if not template:
            template = """
            Task: {task}
            
            Generate a command to accomplish this task in a terminal environment.
            - Operating System: {platform}
            - Current Directory: {directory}
            
            Return ONLY the command with no explanations or markdown formatting.
            Make the command safe and include proper error handling.
            """
            
        # Format the template
        prompt = template.format(
            task=task,
            platform=system_context["platform"],
            directory=system_context["current_directory"]
        )
        
        # Add system prompt based on verification level
        if command_verification_level == "high":
            system_prompt = """
            You are a command generation expert.
            Focus on:
            - System compatibility and security
            - Proper error handling
            - Safe command execution
            - Clear output formatting
            
            IMPORTANT: Return ONLY the raw command with NO explanations, markdown, or formatting.
            """
        else:
            system_prompt = "Generate a terminal command for the given task. Return only the command."
            
        # Generate the command with just a single text prompt
        response = MODEL.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up the response to remove any markdown formatting
        text = re.sub(r'```(?:bash|sh|cmd|powershell)?', '', text)
        text = re.sub(r'`', '', text)
        
        # Remove any explanations or other text that doesn't look like a command
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Found what looks like a command
                return line
                
        # If we got here, we couldn't find a clear command in the response
        return text.strip()
    except Exception as e:
        print(f"Error generating command: {str(e)}")
        return "" 