#!/usr/bin/env python3
"""
Agent Terminal Assistant
A terminal-based AI assistant that works as an agent, capable of:
- Context-aware task handling
- Planning and describing actions before execution
- Breaking complex tasks into subtasks
- Maintaining conversation context across interactions
- Auto-run mode with intelligent questioning
"""
import os
import sys
import re
import json
import time
import shlex
import platform
import subprocess
import yaml
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union, Set
from dotenv import load_dotenv

# For colorized output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.table import Table
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    class DummyFore:
        RED = GREEN = YELLOW = CYAN = BLUE = ''
    class DummyStyle:
        RESET_ALL = ''
    Fore = DummyFore()
    Style = DummyStyle()

# Initialize variables that will be set in init_gemini
MODEL = None
SILENT_MODE = False

def init_gemini(silent=False):
    """Initialize Gemini API with option for silent mode"""
    global MODEL, SILENT_MODE
    SILENT_MODE = silent
    
    # Load environment variables
    if not silent:
        print("Loading environment variables...")
    load_dotenv()
    
    # Initialize Gemini API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Configure Gemini API
    if not silent:
        print("Configuring Gemini API...")
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL = genai.GenerativeModel('gemini-2.0-flash')  # Use Flash for faster responses

# Import MCP server
from mcp_server import mcp

# Import agent utilities if available
try:
    from agent_utils import PlatformUtils, CommandValidator, TaskUtils, FileUtils
    HAS_AGENT_UTILS = True
except ImportError:
    HAS_AGENT_UTILS = False

class TaskState:
    """Represents the state of a task in the agent system"""
    def __init__(self, task_id: str, description: str, status: str = "pending"):
        self.task_id = task_id
        self.description = description
        self.status = status  # pending, in_progress, completed, failed
        self.start_time = None
        self.end_time = None
        self.subtasks: List["TaskState"] = []
        self.parent_task: Optional["TaskState"] = None
        self.command_history: List[Dict] = []
        self.output: str = ""
        self.error: str = ""
        
    def start(self):
        """Mark task as started"""
        self.status = "in_progress"
        self.start_time = datetime.now()
        
    def complete(self, output: str = ""):
        """Mark task as completed"""
        self.status = "completed"
        self.end_time = datetime.now()
        self.output = output
        
    def fail(self, error: str = ""):
        """Mark task as failed"""
        self.status = "failed"
        self.end_time = datetime.now()
        self.error = error
        
    def add_subtask(self, description: str) -> "TaskState":
        """Add a subtask to this task"""
        subtask_id = f"{self.task_id}.{len(self.subtasks) + 1}"
        subtask = TaskState(subtask_id, description)
        subtask.parent_task = self
        self.subtasks.append(subtask)
        return subtask
        
    def add_command(self, command_data: Dict):
        """Add command execution to history"""
        self.command_history.append(command_data)
        
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
        
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == "completed"
        
    @property
    def is_failed(self) -> bool:
        """Check if task failed"""
        return self.status == "failed"
        
    @property
    def is_active(self) -> bool:
        """Check if task is currently active"""
        return self.status == "in_progress"
        
    def __str__(self) -> str:
        """String representation of task"""
        status_color = {
            "pending": Fore.YELLOW,
            "in_progress": Fore.CYAN,
            "completed": Fore.GREEN,
            "failed": Fore.RED
        }.get(self.status, Fore.WHITE)
        
        return f"[{status_color}{self.status.upper()}{Style.RESET_ALL}] {self.task_id}: {self.description}"

class AgentContext:
    """Maintains context and conversation history for the agent"""
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.current_task: Optional[TaskState] = None
        self.task_history: List[TaskState] = []
        self.current_directory = os.getcwd()
        self.variables: Dict[str, Any] = {}
        self.session_start_time = datetime.now()
        self.file_access_history: Dict[str, datetime] = {}
        self.command_history: List[Dict] = []
        self.recent_errors: List[Tuple[str, str]] = []  # (command, error_msg)
        
    def add_user_message(self, message: str):
        """Add user message to conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_agent_message(self, message: str):
        """Add agent message to conversation history"""
        self.conversation_history.append({
            "role": "agent",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_system_message(self, message: str):
        """Add system message to conversation history"""
        self.conversation_history.append({
            "role": "system",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def start_task(self, description: str) -> TaskState:
        """Start a new main task"""
        task_id = str(len(self.task_history) + 1)
        task = TaskState(task_id, description)
        task.start()
        self.current_task = task
        self.task_history.append(task)
        return task
        
    def start_subtask(self, description: str) -> Optional[TaskState]:
        """Start a subtask under the current task"""
        if self.current_task:
            subtask = self.current_task.add_subtask(description)
            subtask.start()
            self.current_task = subtask
            return subtask
        return None
        
    def complete_current_task(self, output: str = ""):
        """Complete the current task and return to parent task if it exists"""
        if self.current_task:
            self.current_task.complete(output)
            # If this is a subtask, return to parent task
            if self.current_task.parent_task:
                self.current_task = self.current_task.parent_task
                
    def fail_current_task(self, error: str = ""):
        """Mark current task as failed and return to parent task if it exists"""
        if self.current_task:
            self.current_task.fail(error)
            # If this is a subtask, return to parent task
            if self.current_task.parent_task:
                self.current_task = self.current_task.parent_task
                
    def add_command_to_current_task(self, command_data: Dict):
        """Add command execution to current task history"""
        if self.current_task:
            self.current_task.add_command(command_data)
        self.command_history.append(command_data)
        
    def record_file_access(self, file_path: str):
        """Record file access in history"""
        self.file_access_history[file_path] = datetime.now()
        
    def get_context_summary(self) -> str:
        """Get a summary of the current context for the agent"""
        return f"""
Current Directory: {self.current_directory}
Current Task: {self.current_task.description if self.current_task else 'None'}
Total Tasks: {len(self.task_history)}
Command History: {len(self.command_history)} commands
Recent Files: {', '.join(list(self.file_access_history.keys())[-5:]) if self.file_access_history else 'None'}
Recent Errors: {len(self.recent_errors)}
Session Duration: {str(datetime.now() - self.session_start_time).split('.')[0]}
"""

class AgentTerminal:
    """Terminal-based AI assistant agent"""
    
    def __init__(self, auto_run=False, silent_init=False):
        """Initialize the agent terminal"""
        # Initialize Gemini in silent mode if requested
        init_gemini(silent=silent_init)
        
        self.context = AgentContext()
        self.config = self.load_config()
        self.command_history = []
        self.auto_run = self.config.get("auto_run", False)
        self.silent_init = silent_init
        
        if auto_run:
            self.auto_run = True
        
        # Load command history from previous sessions
        self.load_history()
        
        if not silent_init:
            print("Agent Terminal Assistant initialized")
            if self.auto_run:
                print("Auto-run mode: Enabled")
            else:
                print("Auto-run mode: Disabled (use 'auto on' to enable)")
            print(f"Loaded {len(self.command_history)} command(s) from history.")
            print("Agent Terminal Assistant")
            print("Type 'exit' to quit, 'help' for commands")
            print()
    
    def is_conversational_query(self, text: str) -> bool:
        """Check if the user input is conversational rather than a task"""
        # Common conversational patterns
        conversational_patterns = [
            r'^hi\b', 
            r'^hello\b', 
            r'^hey\b',
            r'how are you',
            r'^what\'?s up',
            r'^good morning',
            r'^good afternoon',
            r'^good evening',
            r'^\?',
            r'^who are you',
            r'^tell me about yourself',
            r'^what can you do'
        ]
        
        # Check if any pattern matches
        text_lower = text.lower()
        if any(re.search(pattern, text_lower) for pattern in conversational_patterns):
            return True
            
        # List of task-related terms that should be processed as commands, not conversations
        task_terms = ['install', 'create', 'delete', 'find', 'run', 'show', 'list', 'make', 'exec', 
                      'search', 'organize', 'copy', 'move', 'check', 'get', 'display', 'monitor', 
                      'analyze', 'download', 'upload', 'convert', 'rename', 'backup']
        
        # Technical/system-specific terms that strongly indicate a command, not conversation
        technical_terms = ['cpu', 'memory', 'ram', 'disk', 'drive', 'file', 'folder', 'directory', 
                           'process', 'system', 'network', 'port', 'usage', 'real-time', 'realtime',
                           'performance', 'monitor', 'resource', 'task manager', 'log', 'service',
                           'registry', 'database', 'hardware', 'software', 'driver', 'update']
        
        # If it contains technical terms, definitely treat as a command
        if any(term in text_lower for term in technical_terms):
            return False
            
        # If it contains task-related terms, it's not conversational
        if any(term in text_lower for term in task_terms):
            return False
            
        # Special case: monitoring commands should never be conversational
        monitoring_patterns = [
            r'(show|display|check|monitor|get).*(cpu|processor|memory|ram|system).*(usage|performance|status|health)',
            r'(cpu|memory|ram|system).*(usage|monitor|status|performance)',
            r'(show|display|monitor).*(resource|usage|performance)',
            r'real.?time.*(monitor|usage|performance|stats)',
            r'how.*(much|many).*(cpu|memory|ram)'
        ]
        
        if any(re.search(pattern, text_lower) for pattern in monitoring_patterns):
            return False
            
        # If it's very short (1-3 words) and doesn't contain task-related terms
        word_count = len(text_lower.split())
        if word_count <= 3:
            return True
            
        return False
        
    def handle_conversation(self, user_input: str):
        """Handle conversational queries directly using the AI model"""
        print(f"{Fore.CYAN}Processing your message...{Style.RESET_ALL}")
        
        prompt = f"""
# CONVERSATIONAL RESPONSE

You are an AI terminal assistant that helps users with computer tasks.
The user has sent a conversational message rather than a task request.
Respond naturally and conversationally to the user's input.

User message: {user_input}

Remember:
- Keep your response friendly and concise
- Ask if they'd like help with a specific terminal task if appropriate
- Don't provide any commands unless specifically requested
"""
        try:
            response = MODEL.generate_content(prompt)
            text = response.text.strip()
            print(f"\n{text}\n")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error generating conversational response: {str(e)}{Style.RESET_ALL}")
            print("Hello! How can I help you with your terminal tasks today?")
            return True
            
    def process_user_input(self, user_input):
        """Process a single user input and execute it"""
        user_input = user_input.strip()
            
        if user_input.lower() == 'exit':
            self.save_history()
            return False
            
        if user_input.lower() == 'help':
            self.show_help()
            return True
            
        if user_input.lower() == 'history':
            self.display_command_history()
            return True
            
        if user_input.lower() == 'tasks':
            self.display_task_status()
            return True
            
        if user_input.lower() == 'context':
            self.display_context()
            return True
            
        if user_input.lower() == 'auto on':
            self.auto_run = True
            print("Auto-run mode enabled")
            return True
            
        if user_input.lower() == 'auto off':
            self.auto_run = False
            print("Auto-run mode disabled")
            return True
            
        if user_input.lower() == 'clear':
            os.system('cls' if platform.system() == 'Windows' else 'clear')
            return True
            
        if user_input.lower().startswith('cd '):
            path = user_input[3:].strip()
            self.change_directory(path)
            return True
            
        if user_input.lower() == 'pwd':
            print(os.getcwd())
            return True
            
        # Enhanced check for monitoring commands before other processing
        # This should happen before the conversational query check
        user_input_lower = user_input.lower()
        is_monitoring = False
        
        # Comprehensive check for various monitoring command formats
        if (('show' in user_input_lower or 'display' in user_input_lower or 'monitor' in user_input_lower) and 
            ('cpu' in user_input_lower or 'processor' in user_input_lower or 'memory' in user_input_lower or 
             'ram' in user_input_lower or 'resource' in user_input_lower or 'system' in user_input_lower) and
            ('usage' in user_input_lower or 'performance' in user_input_lower or 'status' in user_input_lower or 
             'real-time' in user_input_lower or 'realtime' in user_input_lower)):
            is_monitoring = True
            
        # Additional checks for more specific monitoring patterns
        monitoring_patterns = [
            r'(show|display|check|monitor|get).*(cpu|processor|memory|ram|system).*(usage|performance|status|health)',
            r'(cpu|memory|ram|system).*(usage|monitor|status|performance)',
            r'(show|display|monitor).*(resource|usage|performance)',
            r'real.?time.*(monitor|usage|performance|stats)',
            r'how.*(much|many).*(cpu|memory|ram)'
        ]
        
        if not is_monitoring:
            is_monitoring = any(re.search(pattern, user_input_lower) for pattern in monitoring_patterns)
            
        # Handle monitoring commands with direct execution
        if is_monitoring:
            print(f"{Fore.CYAN}Detected system monitoring command. Processing...{Style.RESET_ALL}")
            self.handle_monitoring_command(user_input)
            
            # Add to command history
            self.command_history.append(user_input)
            if not self.silent_init:
                self.save_history()
                
            return True
            
        # Check if this is a conversational query rather than a task
        if self.is_conversational_query(user_input):
            return self.handle_conversation(user_input)
            
        # Add to command history
        self.command_history.append(user_input)
        if not self.silent_init:
            self.save_history()
        
        # Process the task
        self.process_user_task(user_input)
        return True
    
    def is_monitoring_command(self, command: str) -> bool:
        """Check if a command is requesting real-time monitoring"""
        command_lower = command.lower()
        monitoring_terms = ["real-time", "realtime", "monitor", "live", "continuous"]
        resource_terms = ["cpu", "memory", "ram", "processor", "system", "resources", "performance"]
        
        has_monitoring = any(term in command_lower for term in monitoring_terms)
        has_resource = any(term in command_lower for term in resource_terms)
        
        return has_monitoring and has_resource
    
    def handle_monitoring_command(self, command: str) -> None:
        """Handle real-time monitoring commands directly"""
        # Start a task for proper history tracking
        task = self.context.start_task(command)
        task.start()
        
        print(f"{Fore.CYAN}Starting system monitoring...{Style.RESET_ALL}")
        
        # Track if we're showing CPU, memory, or both
        show_cpu = True
        show_memory = True
        
        # Check what resources to monitor based on command
        command_lower = command.lower()
        if 'cpu' in command_lower and 'memory' not in command_lower and 'ram' not in command_lower:
            show_memory = False
        elif ('memory' in command_lower or 'ram' in command_lower) and 'cpu' not in command_lower:
            show_cpu = False
        
        # Different commands based on platform
        if platform.system() == "Windows":
            monitoring_results = []
            
            # Create a better command for monitoring that doesn't use continuous mode
            if show_cpu:
                # Display top CPU-consuming processes
                print(f"{Fore.YELLOW}Top CPU consumers:{Style.RESET_ALL}")
                monitor_cmd = "powershell -Command \"Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize\""
                result = self.execute_command(monitor_cmd)
                if result["exit_code"] == 0:
                    monitoring_results.append("CPU process list: Success")
                else:
                    monitoring_results.append("CPU process list: Failed")
                    
                # Show current CPU usage percentage
                print(f"{Fore.YELLOW}Current CPU usage:{Style.RESET_ALL}")
                cpu_cmd = "powershell -Command \"$CPU = (Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%' -f $CPU)\""
                result = self.execute_command(cpu_cmd)
                if result["exit_code"] == 0:
                    monitoring_results.append("CPU usage percentage: Success")
                else:
                    monitoring_results.append("CPU usage percentage: Failed")
            
            if show_memory:
                # Show memory usage
                print(f"{Fore.YELLOW}Memory usage:{Style.RESET_ALL}")
                memory_cmd = "powershell -Command \"Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalVisibleMemory (MB)';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreePhysicalMemory (MB)';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory (MB)';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage (%)';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize\""
                result = self.execute_command(memory_cmd)
                if result["exit_code"] == 0:
                    monitoring_results.append("Memory usage information: Success")
                else:
                    monitoring_results.append("Memory usage information: Failed")
                
                # Show memory usage by process
                print(f"{Fore.YELLOW}Top memory consumers:{Style.RESET_ALL}")
                mem_process_cmd = "powershell -Command \"Get-Process | Sort-Object -Property WorkingSet -Descending | Select-Object -First 10 Name, @{Name='Memory (MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}}, CPU, ID | Format-Table -AutoSize\""
                result = self.execute_command(mem_process_cmd)
                if result["exit_code"] == 0:
                    monitoring_results.append("Memory process list: Success")
                else:
                    monitoring_results.append("Memory process list: Failed")
            
            # Real-time monitoring hint
            if "real-time" in command_lower or "realtime" in command_lower or "continuous" in command_lower or "live" in command_lower:
                print(f"\n{Fore.GREEN}For continuous real-time monitoring, using Task Manager is recommended.{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Would you like to open Task Manager now? (y/n){Style.RESET_ALL}")
                response = input("> ").strip().lower()
                if response == "y" or response == "yes":
                    print(f"{Fore.CYAN}Opening Task Manager...{Style.RESET_ALL}")
                    subprocess.Popen("taskmgr", shell=True)
                    monitoring_results.append("Opened Task Manager for continuous monitoring")
            else:
                # Provide info about real-time monitoring
                print(f"\n{Fore.GREEN}System monitoring snapshot complete.{Style.RESET_ALL}")
                print(f"{Fore.CYAN}For continuous real-time monitoring, you can use Task Manager.{Style.RESET_ALL}")
            
            # Complete the task
            self.context.complete_current_task("\n".join(monitoring_results))
            
        else:
            # Linux monitoring
            monitoring_results = []
            
            if show_cpu:
                print(f"{Fore.YELLOW}Top CPU consumers:{Style.RESET_ALL}")
                result = self.execute_command("ps aux --sort=-%cpu | head -n 11")
                if result["exit_code"] == 0:
                    monitoring_results.append("CPU process list: Success")
                else:
                    monitoring_results.append("CPU process list: Failed")
                
                print(f"{Fore.YELLOW}System load:{Style.RESET_ALL}")
                result = self.execute_command("uptime")
                if result["exit_code"] == 0:
                    monitoring_results.append("System load: Success")
                else:
                    monitoring_results.append("System load: Failed")
            
            if show_memory:
                print(f"{Fore.YELLOW}Memory usage:{Style.RESET_ALL}")
                result = self.execute_command("free -h")
                if result["exit_code"] == 0:
                    monitoring_results.append("Memory usage: Success")
                else:
                    monitoring_results.append("Memory usage: Failed")
            
            # Real-time monitoring hint
            if "real-time" in command_lower or "realtime" in command_lower or "continuous" in command_lower or "live" in command_lower:
                print(f"\n{Fore.GREEN}For continuous real-time monitoring, you can use the 'top' command in a separate terminal.{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Would you like to run 'top' now? (y/n){Style.RESET_ALL}")
                response = input("> ").strip().lower()
                if response == "y" or response == "yes":
                    print(f"{Fore.CYAN}Running top (press q to exit)...{Style.RESET_ALL}")
                    result = self.execute_command("top")
                    monitoring_results.append("Ran top command")
            else:
                print(f"\n{Fore.GREEN}System monitoring complete. For continuous monitoring, use 'top' in a separate terminal.{Style.RESET_ALL}")
            
            # Complete the task
            self.context.complete_current_task("\n".join(monitoring_results))
    
    def run(self):
        """Run the agent terminal in interactive mode"""
        while True:
            try:
                print()
                user_input = input("What would you like me to do?\n")
                if not self.process_user_input(user_input):
                    break
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting...")
                self.save_history()
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    def load_config(self) -> Dict:
        """Load configuration from config.yaml"""
        try:
            if os.path.exists("config.yaml"):
                with open("config.yaml") as f:
                    return yaml.safe_load(f)
            return {
                "max_history": 100,
                "history_file": "command_history.json",
                "max_tokens": 8000
            }
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return {
                "max_history": 100,
                "history_file": "command_history.json",
                "max_tokens": 8000
            }
            
    def load_history(self):
        """Load command history from file"""
        try:
            if os.path.exists(self.config["history_file"]):
                with open(self.config["history_file"], 'r') as f:
                    self.command_history = json.load(f)
                if not self.silent_init:
                    print(f"Loaded {len(self.command_history)} command(s) from history.")
            else:
                if not self.silent_init:
                    print(f"History file {self.config['history_file']} not found. Creating empty history.")
                self.command_history = []
        except Exception as e:
            if not self.silent_init:
                print(f"Error loading history: {str(e)}")
            self.command_history = []
            
    def save_history(self):
        """Save command history to file"""
        try:
            with open(self.config["history_file"], 'w') as f:
                json.dump(self.command_history, f, indent=2)
            if not self.silent_init:
                print("History saved successfully.")
        except Exception as e:
            if not self.silent_init:
                print(f"Error saving history: {str(e)}")
    
    def get_system_drive_info(self) -> Dict:
        """Get information about system drives and common installation directories"""
        drive_info = {}
        try:
            # Get all drives on Windows
            if platform.system() == "Windows":
                import win32api
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    try:
                        drive_info[drive] = {
                            "type": "fixed" if drive.startswith("C:") else "removable",
                            "free_space": win32api.GetDiskFreeSpace(drive)[0] * win32api.GetDiskFreeSpace(drive)[1] * win32api.GetDiskFreeSpace(drive)[2],
                            "total_space": win32api.GetDiskFreeSpace(drive)[0] * win32api.GetDiskFreeSpace(drive)[1] * win32api.GetDiskFreeSpace(drive)[3]
                        }
                    except Exception:
                        # If we can't get detailed info, just mark it as available
                        drive_info[drive] = {"type": "available"}
        except Exception as e:
            print(f"Warning: Could not get detailed drive information: {str(e)}")
            # Fallback to basic drive detection
            if platform.system() == "Windows":
                import string
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        drive_info[drive] = {"type": "available"}
        
        # Add common installation directories
        common_dirs = {
            "Program Files": os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files")),
            "Program Files (x86)": os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            "AppData": os.path.join(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))),
            "Local AppData": os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))),
            "Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "Documents": os.path.join(os.path.expanduser("~"), "Documents")
        }
        
        drive_info["common_dirs"] = common_dirs
        return drive_info

    def verify_command_execution(self, command: str, result: Dict) -> Tuple[bool, str, Dict]:
        """Verify command execution using Gemini API"""
        prompt = f"""
# COMMAND EXECUTION VERIFICATION

## COMMAND CONTEXT
Command: {command}
Exit Code: {result.get('exit_code', 1)}
Output:
{result.get('stdout', '')}
Errors:
{result.get('stderr', '')}

## INSTRUCTIONS
Analyze the command execution result and determine:
1. Was the command successful?
2. What is the current state of the system?
3. What should be the next action?

Return a JSON object with this structure:
{{
    "success": true/false,
    "system_state": "description of current state",
    "next_action": {{
        "action": "continue/retry/skip/abort",
        "reason": "why this action was chosen",
        "fallback_command": "alternative command if retrying"
    }},
    "diagnostics": {{
        "is_installed": true/false,
        "error_type": "none/not_found/permission/network/etc",
        "suggested_fix": "what needs to be done"
    }}
}}
"""
        try:
            # Default values in case the API call fails
            default_success = result.get('exit_code', 1) == 0
            default_state = "Command executed, but verification unavailable."
            default_action = {"action": "continue" if default_success else "skip", 
                              "reason": "API verification unavailable, decision based on exit code"}
            default_diagnostics = {"is_installed": None, "error_type": None, "suggested_fix": None}
            
            # Try to call the Gemini API with a timeout
            try:
                response = MODEL.generate_content(prompt)
                text = response.text.strip()
                
                # Extract JSON from response
                match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    match = re.search(r'({.*})', text, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                    else:
                        json_str = text
                
                verification = json.loads(json_str)
                return (
                    verification.get("success", False),
                    verification.get("system_state", ""),
                    verification.get("next_action", {}),
                    verification.get("diagnostics", {})
                )
            
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}\nVerification interrupted. Proceeding with basic verification.{Style.RESET_ALL}")
                return default_success, default_state, default_action, default_diagnostics
                
            except Exception as e:
                print(f"{Fore.YELLOW}API verification failed: {str(e)}. Using basic verification.{Style.RESET_ALL}")
                return default_success, default_state, default_action, default_diagnostics
                
        except Exception as e:
            print(f"{Fore.RED}Error verifying command execution: {str(e)}{Style.RESET_ALL}")
            return (
                result.get('exit_code', 1) == 0,  # Consider success based on exit code
                "",
                {"action": "continue", "reason": "Verification failed"},
                {}
            )

    def get_task_planning(self, task: str) -> Dict:
        """Get AI task planning response - breaking the task into subtasks with approaches"""
        # Get system drive information
        drive_info = self.get_system_drive_info()
        
        prompt = f"""
# TASK PLANNING AND ANALYSIS AGENT

## CONTEXT INFORMATION
- User Task: {task}
- Current Directory: {self.context.current_directory}
- OS: {platform.system()} {platform.release()}
- System Drives: {json.dumps(drive_info, indent=2)}
- Previous Commands: {', '.join([cmd.get('command', '') for cmd in self.context.command_history[-5:]])}

## INSTRUCTIONS
Analyze the user's task and create a structured execution plan:

1. Break down the task into logical subtasks
2. For each subtask, explain:
   - What commands/approach you'll use
   - Why this approach is optimal
   - Any potential issues to watch for
   - Required system resources or dependencies

Return a JSON object with this structure:
{{
  "task_summary": "Brief summary of what you understand the task to be",
  "subtasks": [
    {{
      "description": "Subtask description",
      "approach": "How you will accomplish this subtask",
      "commands": ["command1", "command2"],
      "rationale": "Why this approach is best",
      "potential_issues": "What might go wrong",
      "required_resources": ["resource1", "resource2"],
      "fallback_commands": ["fallback1", "fallback2"]
    }}
  ],
  "estimated_steps": 5,
  "system_requirements": {{
    "disk_space": "required space",
    "memory": "required memory",
    "dependencies": ["dep1", "dep2"]
  }}
}}
"""
        
        try:
            response = MODEL.generate_content(prompt)
            # Extract JSON from response
            text = response.text
            
            # Find JSON object in the response
            match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # Try to find JSON without markdown formatting
                match = re.search(r'({.*})', text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    json_str = text
                    
            # Clean and parse JSON
            return json.loads(json_str)
        except Exception as e:
            print(f"Error generating task plan: {str(e)}")
            # Return simple fallback plan
            return {
                "task_summary": task,
                "subtasks": [
                    {
                        "description": "Execute task directly",
                        "approach": "Use direct command execution",
                        "commands": [],
                        "rationale": "Simple direct execution",
                        "potential_issues": "May not be optimal",
                        "required_resources": [],
                        "fallback_commands": []
                    }
                ],
                "estimated_steps": 1,
                "system_requirements": {
                    "disk_space": "unknown",
                    "memory": "unknown",
                    "dependencies": []
                }
            }
    
    def get_command_generation(self, task: str, subtask: str = None) -> List[str]:
        """Get AI generated commands for a specific task or subtask"""
        
        # Prepare context for the prompt
        task_context = task
        if subtask:
            task_context = f"{task} - Subtask: {subtask}"
            
        recent_commands = "\n".join([f"- {cmd.get('command', '')}" for cmd in self.context.command_history[-5:]])
        recent_errors = "\n".join([f"- Command: {cmd}, Error: {err}" for cmd, err in self.context.recent_errors[-3:]])
        
        # Special handling for real-time monitoring
        if ("real-time" in task_context.lower() or "monitor" in task_context.lower()) and \
           ("cpu" in task_context.lower() or "memory" in task_context.lower() or "system" in task_context.lower()):
            
            if platform.system() == "Windows":
                return [
                    # Limited samples instead of continuous for stable execution
                    "powershell -Command \"Get-Counter '\\Processor(_Total)\\% Processor Time', '\\Memory\\% Committed Bytes In Use' -SampleInterval 1 -MaxSamples 10 | Format-Table -AutoSize\"",
                    "powershell -Command \"Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize\""
                ]
            else:
                # Linux commands
                return [
                    "top -n 10 -b",
                    "free -m",
                    "ps aux --sort=-%cpu | head -n 11"
                ]
        
        prompt = f"""
# TERMINAL COMMAND GENERATOR

## CONTEXT
- Task: {task_context}
- Current Directory: {self.context.current_directory}
- OS: {platform.system()} {platform.release()}
- Recent Commands:
{recent_commands}
- Recent Errors:
{recent_errors}

## INSTRUCTIONS
Generate the most efficient terminal commands to accomplish this task.
Return ONLY raw, executable commands with NO explanations or formatting.
Ensure commands are appropriate for the user's operating system.

### WINDOWS GUIDELINES
- Use PowerShell for complex tasks
- Use CMD for simple tasks
- Avoid continuous monitoring commands that run indefinitely
- For PowerShell commands that typically would use -Continuous flag, use -MaxSamples 10 instead
- For complex PowerShell commands, use: powershell -Command "Your-Command-Here"

### RETURN FORMAT
Return ONLY the raw commands, one per line, with NO explanations, backticks, or markdown.
"""
        
        # Generate a safe default command based on the task
        is_windows = platform.system() == "Windows"
        default_commands = []
        
        # Simple command generation based on keywords in the task
        if "file" in task_context.lower() or "list" in task_context.lower():
            default_commands = ["dir"] if is_windows else ["ls -la"]
        elif "process" in task_context.lower():
            default_commands = ["tasklist"] if is_windows else ["ps aux"]
        elif "network" in task_context.lower():
            default_commands = ["ipconfig /all"] if is_windows else ["ifconfig"]
        elif "system" in task_context.lower() or "info" in task_context.lower():
            default_commands = ["systeminfo"] if is_windows else ["uname -a && cat /etc/os-release"]
        elif "cpu" in task_context.lower() or "memory" in task_context.lower() or "monitor" in task_context.lower():
            if is_windows:
                default_commands = [
                    "powershell -Command \"Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize\"",
                    "powershell -Command \"Get-Counter '\\Processor(_Total)\\% Processor Time', '\\Memory\\% Committed Bytes In Use' -SampleInterval 1 -MaxSamples 10 | Format-Table -AutoSize\""
                ]
            else:
                default_commands = ["top -n 10 -b", "free -m"]
        else:
            # Very safe fallback
            default_commands = ["dir"] if is_windows else ["ls"]
        
        try:
            try:
                response = MODEL.generate_content(prompt)
                text = response.text.strip()
                
                # Clean up the response to remove any markdown formatting
                text = re.sub(r'```(?:powershell|sh|bash|cmd|bat|shell)?\n', '', text)
                text = re.sub(r'```', '', text)
                
                # Split into lines and remove empty lines
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                # Additional post-processing to ensure no markdown or explanations
                commands = []
                for line in lines:
                    # Skip lines that look like markdown headings or bullet points
                    if line.startswith('#') or line.startswith('-') or line.startswith('*'):
                        continue
                    # Skip lines that look like explanations
                    if ('Note:' in line or 
                        'This command' in line or 
                        'Use this' in line or 
                        line.startswith('Note') or 
                        line.startswith('For') or 
                        line.startswith('The') or
                        line.startswith('This') or
                        line.startswith('To ') or
                        line.startswith('You can')):
                        continue
                    
                    # Remove any remaining markdown or non-command elements
                    line = re.sub(r'^[>#$] ', '', line)
                    
                    # Add to commands if it looks like an actual command
                    if len(line.split()) >= 1:
                        commands.append(line)
                
                # For real-time monitoring tasks, ensure we don't use continuous monitoring
                if ("real-time" in task_context.lower() or "monitor" in task_context.lower()) and \
                   ("cpu" in task_context.lower() or "memory" in task_context.lower() or "system" in task_context.lower()):
                    commands = [cmd.replace("-Continuous", "-MaxSamples 10") for cmd in commands]
                
                # Final cleanup for PowerShell commands on Windows
                final_commands = []
                
                for cmd in commands:
                    # Fix PowerShell commands
                    if is_windows and ('Get-' in cmd or 'Set-' in cmd or "$_" in cmd or 'Where-Object' in cmd):
                        # If it's a PowerShell command but doesn't have the powershell -Command prefix
                        if not cmd.startswith('powershell -Command') and not cmd.startswith('powershell.exe -Command'):
                            if '"' in cmd:
                                # If there are already quotes, we need to be careful with nesting
                                cmd = f'powershell -Command "{cmd}"'
                            else:
                                # Simple case, just wrap in quotes
                                cmd = f'powershell -Command "{cmd}"'
                    
                    final_commands.append(cmd)
                    
                if final_commands:
                    return final_commands
                else:
                    # Fallback if we couldn't extract commands
                    print(f"{Fore.YELLOW}No valid commands could be extracted from AI response. Using default commands.{Style.RESET_ALL}")
                    return default_commands
                    
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}\nCommand generation interrupted. Using default commands.{Style.RESET_ALL}")
                return default_commands
                
            except Exception as e:
                print(f"{Fore.YELLOW}API command generation failed: {str(e)}. Using default commands.{Style.RESET_ALL}")
                return default_commands
                
        except Exception as e:
            print(f"{Fore.RED}Error generating commands: {str(e)}{Style.RESET_ALL}")
            # Return a safe fallback command
            return default_commands
    
    def execute_command(self, command: str) -> Dict:
        """Execute a command and return its result"""
        # Special handling for common tasks on Windows
        if platform.system() == "Windows":
            # Handle "find large files" command for Windows
            if re.search(r"find.*files.*larger than.*MB", command.lower()):
                size_match = re.search(r"(\d+)\s*MB", command.lower())
                size_mb = "10"  # Default size
                
                if size_match:
                    size_mb = size_match.group(1)
                
                # Execute PowerShell directly
                print(f"{Fore.CYAN}Executing direct PowerShell command for finding large files...{Style.RESET_ALL}")
                command = f'powershell -Command "Get-ChildItem -Path . -Recurse -File | Where-Object {{ $_.Length -gt ({size_mb} * 1MB) }} | Sort-Object Length -Descending | Select-Object @{{Name=\'Size (MB)\';Expression={{[math]::Round($_.Length / 1MB, 2)}}}}, FullName | Format-Table -AutoSize"'
            
            # Special handling for real-time monitoring commands
            if ("Get-Counter" in command or 
                "real-time" in command.lower() or 
                "continuous" in command.lower() or
                "monitor" in command.lower() and "cpu" in command.lower() or
                "monitor" in command.lower() and "memory" in command.lower()):
                
                print(f"{Fore.YELLOW}Executing real-time monitoring command: {command}{Style.RESET_ALL}")
                
                # Convert to a non-continuous command that runs for a limited time
                if "Get-Counter" in command and "-Continuous" in command:
                    # Replace -Continuous with -MaxSamples for a limited run
                    command = command.replace("-Continuous", "-MaxSamples 10")
                
                # For monitoring commands, use direct execution that doesn't rely on streaming
                print(f"{Fore.CYAN}Starting monitoring (will run for a short time)...{Style.RESET_ALL}")
        
        # Original command execution code continues here
        print(f"{Fore.YELLOW}Executing: {command}{Style.RESET_ALL}")
        
        command_data = {
            "command": command,
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "execution_time": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add command to task if we're in a task
        if hasattr(self, 'context') and hasattr(self.context, 'current_task') and self.context.current_task:
            self.context.add_command_to_current_task(command_data)
        
        start_time = time.time()
        
        # For cd commands, use our internal method
        if command.strip().startswith("cd "):
            path = command[3:].strip()
            if path:
                self.change_directory(path)
                return {
                    "command": command,
                    "stdout": f"Changed directory to {self.context.current_directory}",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Just "cd" with no args usually goes to home directory
                self.change_directory("~")
                return {
                    "command": command,
                    "stdout": f"Changed directory to {self.context.current_directory}",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
        
        try:
            # Execute the command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.context.current_directory
            )
            
            # Stream output in real-time
            stdout_lines = []
            stderr_lines = []
            
            # Set a timeout value for each readline operation
            import select
            
            # Read stdout and stderr in real-time with timeout support
            while True:
                try:
                    # Check if the process has already exited
                    if process.poll() is not None:
                        break
                    
                    # Use select to wait for output with a timeout
                    readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                    
                    for stream in readable:
                        if stream == process.stdout:
                            stdout_line = process.stdout.readline()
                            if stdout_line:
                                stdout_line = stdout_line.rstrip()
                                print(stdout_line)
                                stdout_lines.append(stdout_line)
                        elif stream == process.stderr:
                            stderr_line = process.stderr.readline()
                            if stderr_line:
                                stderr_line = stderr_line.rstrip()
                                print(f"{Fore.RED}{stderr_line}{Style.RESET_ALL}")
                                stderr_lines.append(stderr_line)
                    
                except KeyboardInterrupt:
                    print(f"{Fore.YELLOW}\nCommand interrupted by user. Terminating...{Style.RESET_ALL}")
                    try:
                        process.terminate()
                        # Give it a chance to terminate gracefully
                        process.wait(timeout=2)
                    except:
                        # If it doesn't terminate in time, kill it
                        process.kill()
                    
                    return {
                        "command": command,
                        "stdout": '\n'.join(stdout_lines),
                        "stderr": '\n'.join(stderr_lines) + "\nCommand interrupted by user",
                        "exit_code": 130,  # Standard exit code for SIGINT
                        "execution_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    print(f"{Fore.RED}Error reading command output: {str(e)}{Style.RESET_ALL}")
                    break
            
            # Get any remaining output
            try:
                remaining_stdout, remaining_stderr = process.communicate(timeout=5)
                
                if remaining_stdout:
                    print(remaining_stdout.rstrip())
                    stdout_lines.extend(remaining_stdout.rstrip().split('\n'))
                
                if remaining_stderr:
                    print(f"{Fore.RED}{remaining_stderr.rstrip()}{Style.RESET_ALL}")
                    stderr_lines.extend(remaining_stderr.rstrip().split('\n'))
            except subprocess.TimeoutExpired:
                # Process didn't complete within timeout, kill it
                process.kill()
                remaining_stdout, remaining_stderr = process.communicate()
                stderr_lines.append("Command timed out and was terminated")
            
            exit_code = process.returncode
            execution_time = time.time() - start_time
            
            # Store the result
            result = {
                "command": command,
                "stdout": '\n'.join(stdout_lines),
                "stderr": '\n'.join(stderr_lines),
                "exit_code": exit_code,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to context
            self.context.add_command_to_current_task(result)
            
            # If there was an error, add to recent errors
            if exit_code != 0 and stderr_lines:
                self.context.recent_errors.append((command, '\n'.join(stderr_lines)))
            
            # Print a completion message
            if exit_code == 0:
                print(f"\n{Fore.GREEN}Command completed successfully in {execution_time:.2f}s{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}Command failed with exit code {exit_code} in {execution_time:.2f}s{Style.RESET_ALL}")
            
            return result
            
        except KeyboardInterrupt:
            error_msg = "Command execution interrupted by user"
            print(f"{Fore.YELLOW}{error_msg}{Style.RESET_ALL}")
            
            # Store error information
            result = {
                "command": command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 130,  # Standard exit code for SIGINT
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            error_msg = f"Exception while executing command: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            
            # Store error information
            result = {
                "command": command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 1,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            self.context.add_command_to_current_task(result)
            self.context.recent_errors.append((command, error_msg))
            return result
    
    def change_directory(self, path: str):
        """Change the current directory"""
        try:
            # Handle home directory shorthand
            if path == "~":
                path = os.path.expanduser("~")
                
            # Convert relative paths to absolute
            if not os.path.isabs(path):
                new_path = os.path.join(self.context.current_directory, path)
            else:
                new_path = path
                
            # Resolve path to handle .. and .
            new_path = os.path.normpath(os.path.abspath(new_path))
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                os.chdir(new_path)
                self.context.current_directory = new_path
                print(f"{Fore.GREEN}Changed directory to: {self.context.current_directory}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Directory not found: {new_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error changing directory: {str(e)}{Style.RESET_ALL}")
    
    def show_help(self):
        """Display help information"""
        help_text = """
Agent Terminal Assistant Commands:
help - Show this help message
exit - Exit the application
clear - Clear the terminal screen
history - Show command history
cd [path] - Change directory
pwd - Show current directory
tasks - Show active and completed tasks
context - Show current context information
auto [on|off] - Enable or disable auto-run mode

For any other tasks, simply describe what you want to do
"""
        print(help_text)
    
    def display_command_history(self):
        """Display command history"""
        if not self.command_history:
            print(f"{Fore.YELLOW}No command history available{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}Command History:{Style.RESET_ALL}")
        for i, cmd in enumerate(self.command_history, 1):
            status = f"{Fore.GREEN}Success{Style.RESET_ALL}" if cmd.get("exit_code", 1) == 0 else f"{Fore.RED}Failed ({cmd.get('exit_code')}){Style.RESET_ALL}"
            execution_time = f"{cmd.get('execution_time', 0):.2f}s"
            print(f"{i}. {cmd.get('command', '')} - {status} - {execution_time}")
    
    def display_task_status(self):
        """Display all tasks and their status"""
        if not self.context.task_history:
            print(f"{Fore.YELLOW}No tasks have been started yet{Style.RESET_ALL}")
            return
        
        print(f"{Fore.CYAN}Task Status:{Style.RESET_ALL}")
        for task in self.context.task_history:
            print(f"{task}")
            for subtask in task.subtasks:
                print(f"  {subtask}")
    
    def display_context(self):
        """Display current context information"""
        print(f"{Fore.CYAN}Current Context:{Style.RESET_ALL}")
        print(self.context.get_context_summary())
    
    def should_ask_question(self) -> bool:
        """Determine if the agent should ask a question based on probability"""
        return random.random() < self.config.get("question_probability", 0.1)
    
    def ask_question(self, task: str, subtask: str = None) -> Optional[str]:
        """Generate and ask a clarifying question if necessary"""
        if not self.should_ask_question():
            return None
            
        # Context for question generation
        context = f"Task: {task}"
        if subtask:
            context += f"\nSubtask: {subtask}"
            
        context += f"\nDirectory: {self.context.current_directory}"
        context += f"\nPlatform: {platform.system()} {platform.release()}"
            
        # Generate a question
        prompt = f"""
# CLARIFICATION QUESTION GENERATION

Given the following task context, determine if there's any critical information missing 
to complete the task effectively. If there is, generate a single direct question to ask the user.
If no question is needed, respond with "NO_QUESTION_NEEDED".

## CONTEXT
{context}

## INSTRUCTIONS
- Only ask if truly necessary for task completion
- Ask about critical parameters, preferences, or constraints
- Keep questions short and direct
- If the task is clear and has sufficient information, return "NO_QUESTION_NEEDED"

## OUTPUT FORMAT
Return ONLY the question text or "NO_QUESTION_NEEDED", nothing else.
"""
        
        try:
            response = MODEL.generate_content(prompt)
            question = response.text.strip()
            
            # Only ask if an actual question was generated
            if question and "NO_QUESTION_NEEDED" not in question:
                print(f"\n{Fore.YELLOW}I need some clarification: {question}{Style.RESET_ALL}")
                answer = input(f"{Fore.CYAN}> {Style.RESET_ALL}")
                return answer
            
            return None
        except Exception as e:
            print(f"Error generating question: {str(e)}")
            return None
    
    def search_for_installation(self, program_name: str) -> Dict:
        """Search for an existing installation of a program"""
        print(f"{Fore.CYAN}Searching for existing installation of {program_name}...{Style.RESET_ALL}")
        
        # Get system drive info
        drive_info = self.get_system_drive_info()
        common_dirs = drive_info.get("common_dirs", {})
        
        # Common installation patterns
        patterns = [
            program_name.lower(),
            program_name.lower() + ".exe",
            program_name.lower() + ".msi",
            program_name.lower() + ".zip",
            program_name.lower() + "-*",  # For versioned folders
            program_name.lower() + "*"    # Any folder starting with program name
        ]
        
        found_locations = []
        search_results = {
            "is_installed": False,
            "locations": [],
            "executable_path": None,
            "version": None,
            "type": None  # "portable", "installed", "archive"
        }
        
        # Search in common directories
        for dir_name, dir_path in common_dirs.items():
            if not os.path.exists(dir_path):
                continue
            
            print(f"Searching in {dir_name}...")
            
            # Search for exact matches
            for root, dirs, files in os.walk(dir_path):
                # Check directories
                for dir_name in dirs:
                    dir_lower = dir_name.lower()
                    if any(pattern in dir_lower for pattern in patterns):
                        full_path = os.path.join(root, dir_name)
                        found_locations.append({
                            "path": full_path,
                            "type": "directory",
                            "name": dir_name
                        })
            
            # Check files
            for file_name in files:
                file_lower = file_name.lower()
                if any(pattern in file_lower for pattern in patterns):
                    full_path = os.path.join(root, file_name)
                    found_locations.append({
                        "path": full_path,
                        "type": "file",
                        "name": file_name
                    })
        
        # Search in all drives
        for drive in drive_info:
            if drive == "common_dirs":
                continue
            
            print(f"Searching in drive {drive}...")
            try:
                for root, dirs, files in os.walk(drive):
                    # Check directories
                    for dir_name in dirs:
                        dir_lower = dir_name.lower()
                        if any(pattern in dir_lower for pattern in patterns):
                            full_path = os.path.join(root, dir_name)
                            found_locations.append({
                                "path": full_path,
                                "type": "directory",
                                "name": dir_name
                            })
                    
                    # Check files
                    for file_name in files:
                        file_lower = file_name.lower()
                        if any(pattern in file_lower for pattern in patterns):
                            full_path = os.path.join(root, file_name)
                            found_locations.append({
                                "path": full_path,
                                "type": "file",
                                "name": file_name
                            })
            except Exception as e:
                print(f"Warning: Could not search drive {drive}: {str(e)}")
        
        # Analyze results
        if found_locations:
            search_results["is_installed"] = True
            search_results["locations"] = found_locations
            
            # Try to find the executable
            for location in found_locations:
                if location["type"] == "file" and location["name"].lower().endswith(".exe"):
                    search_results["executable_path"] = location["path"]
                    search_results["type"] = "installed"
                    break
                elif location["type"] == "file" and location["name"].lower().endswith(".zip"):
                    search_results["type"] = "archive"
                    break
                elif location["type"] == "directory":
                    # Check if it's a portable installation
                    exe_path = os.path.join(location["path"], f"{program_name.lower()}.exe")
                    if os.path.exists(exe_path):
                        search_results["executable_path"] = exe_path
                        search_results["type"] = "portable"
                        break
        
        # Print results
        if search_results["is_installed"]:
            print(f"{Fore.GREEN}Found existing installation of {program_name}{Style.RESET_ALL}")
            print(f"Type: {search_results['type']}")
            if search_results["executable_path"]:
                print(f"Executable: {search_results['executable_path']}")
            print(f"Total locations found: {len(found_locations)}")
        else:
            print(f"{Fore.YELLOW}No existing installation found{Style.RESET_ALL}")
        
        return search_results

    def process_user_task(self, task: str):
        """Process a user task using the agent approach"""
        # Add task to conversation history
        self.context.add_user_message(task)
        
        # Start a new task
        main_task = self.context.start_task(task)
        
        # Try to ask a clarifying question if needed
        try:
            answer = self.ask_question(task)
            if answer:
                # Add the Q&A to conversation history
                self.context.add_user_message(answer)
                
                # Update task with the additional information
                task = f"{task} (Clarification: {answer})"
        except Exception as e:
            print(f"{Fore.YELLOW}Error while asking clarifying question: {str(e)}{Style.RESET_ALL}")
        
        # Get task planning from AI
        print(f"{Fore.CYAN}Analyzing task and creating execution plan...{Style.RESET_ALL}")
        try:
            task_plan = self.get_task_planning(task)
        except Exception as e:
            print(f"{Fore.RED}Error generating task plan: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Using simple execution plan instead{Style.RESET_ALL}")
            # Create a simple fallback plan
            task_plan = {
                "task_summary": task,
                "subtasks": [
                    {
                        "description": "Execute task directly",
                        "approach": "Direct execution",
                        "commands": [],
                        "rationale": "Simple direct execution",
                        "potential_issues": "May not be optimal",
                        "required_resources": [],
                        "fallback_commands": []
                    }
                ],
                "estimated_steps": 1,
                "system_requirements": {
                    "disk_space": "unknown",
                    "memory": "unknown",
                    "dependencies": []
                }
            }
        
        # Display the plan to the user
        print(f"\n{Fore.GREEN}TASK PLAN: {task_plan['task_summary']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}I'll break this down into {len(task_plan['subtasks'])} subtasks:{Style.RESET_ALL}")
        
        for i, subtask in enumerate(task_plan['subtasks'], 1):
            print(f"{Fore.YELLOW}Subtask {i}: {subtask['description']}{Style.RESET_ALL}")
            if subtask.get('required_resources'):
                print(f"  Required: {', '.join(subtask['required_resources'])}")
        
        # If auto-run is disabled, ask for confirmation
        should_run = True
        if not self.auto_run:
            confirmation = input(f"\n{Fore.CYAN}Does this plan look good? (y/n/modify): {Style.RESET_ALL}")
            
            if confirmation.lower() == 'n':
                print(f"{Fore.YELLOW}Task cancelled{Style.RESET_ALL}")
                self.context.fail_current_task("User cancelled task")
                return
            
            if confirmation.lower() == 'modify':
                modifications = input(f"{Fore.CYAN}What modifications would you like to make?: {Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Adapting plan based on your feedback...{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Understood! Proceeding with modified approach.{Style.RESET_ALL}")
        else:
            # With auto-run enabled, still give a chance to cancel
            print(f"\n{Fore.CYAN}Auto-executing plan in 3 seconds (press Ctrl+C to cancel)...{Style.RESET_ALL}")
            try:
                time.sleep(3)
            except KeyboardInterrupt:
                print(f"{Fore.YELLOW}Task cancelled by user{Style.RESET_ALL}")
                self.context.fail_current_task("User cancelled task")
                return
        
        # Define variables to track task status
        main_task_objective_achieved = False
        main_task_result = ""
        
        # Execute each subtask
        for i, subtask in enumerate(task_plan['subtasks'], 1):
            print(f"\n{Fore.BLUE}{'=' * 40}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}SUBTASK {i}/{len(task_plan['subtasks'])}: {subtask['description']}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}{'=' * 40}{Style.RESET_ALL}\n")
            
            # Start subtask
            current_subtask = self.context.start_subtask(subtask['description'])
            
            # Handle file sorting task
            if "sort" in subtask['description'].lower() and "file" in subtask['description'].lower():
                # Get folder structure from MCP
                folder_structure = mcp.get_folder_structure(mcp.common_dirs["Downloads"])
                analysis = mcp.analyze_files(mcp.common_dirs["Downloads"])
                
                # Create suggested folders
                for folder, count in analysis["suggested_folders"].items():
                    if count > 0:
                        folder_path = os.path.join(mcp.common_dirs["Downloads"], folder)
                        if mcp.create_folder(folder_path):
                            print(f"{Fore.GREEN}Created folder: {folder}{Style.RESET_ALL}")
                
                # Move files to appropriate folders
                for root, _, files in os.walk(mcp.common_dirs["Downloads"]):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        # Determine target folder
                        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                            target_folder = "Images"
                        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                            target_folder = "Videos"
                        elif file_ext in ['.mp3', '.wav', '.flac']:
                            target_folder = "Music"
                        elif file_ext in ['.pdf', '.doc', '.docx', '.txt']:
                            target_folder = "Documents"
                        elif file_ext in ['.zip', '.rar', '.7z']:
                            target_folder = "Archives"
                        else:
                            target_folder = "Others"
                        
                        # Move file if it's not already in the target folder
                        target_path = os.path.join(mcp.common_dirs["Downloads"], target_folder, file)
                        if os.path.dirname(file_path) != os.path.dirname(target_path):
                            if mcp.move_file(file_path, target_path):
                                print(f"{Fore.GREEN}Moved {file} to {target_folder}{Style.RESET_ALL}")
                
                # Delete empty folders
                deleted = mcp.delete_empty_folders(mcp.common_dirs["Downloads"])
                for folder in deleted:
                    print(f"{Fore.YELLOW}Deleted empty folder: {folder}{Style.RESET_ALL}")
                
                self.context.complete_current_task("Files sorted successfully")
                main_task_objective_achieved = True
                main_task_result = "Files sorted successfully"
                break
            
            # Handle installation task
            if "install" in subtask['description'].lower():
                # Extract program name from subtask description
                program_name = subtask['description'].lower().replace("install", "").strip()
                
                # Check if package manager is available
                if not mcp.package_managers["chocolatey"]:
                    print(f"{Fore.YELLOW}Chocolatey not found. Installing Chocolatey first...{Style.RESET_ALL}")
                    if mcp.install_package_manager("chocolatey"):
                        print(f"{Fore.GREEN}Chocolatey installed successfully{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Failed to install Chocolatey{Style.RESET_ALL}")
                        self.context.fail_current_task("Failed to install package manager")
                        continue
                
                # Check if package is already installed
                package_info = mcp.get_package_info(program_name)
                if package_info["is_installed"]:
                    print(f"{Fore.GREEN}Package {program_name} is already installed via {package_info['type']}{Style.RESET_ALL}")
                    if package_info["version"]:
                        print(f"Version: {package_info['version']}")
                    self.context.complete_current_task("Package already installed")
                    main_task_objective_achieved = True
                    main_task_result = f"{program_name} is already installed"
                    break
            
            # Check if task is to verify if something is installed
            is_check_installation = any(word in task.lower() for word in ["check if", "verify if", "see if", "find out if", "is installed"])
            is_program_related = any(word in subtask['description'].lower() for word in ["installed", "accessible", "available"])
            
            # Get commands for the subtask
            if subtask.get('commands') and len(subtask['commands']) > 0:
                commands = subtask['commands']
            else:
                commands = self.get_command_generation(task, subtask['description'])
            
            # Execute commands
            all_success = True
            for j, command in enumerate(commands, 1):
                print(f"{Fore.CYAN}Command {j}/{len(commands)}: {command}{Style.RESET_ALL}")
                
                # If auto-run is disabled, ask confirmation for each command
                if not self.auto_run:
                    cmd_confirm = input(f"{Fore.YELLOW}Execute this command? (y/n/edit): {Style.RESET_ALL}")
                    if cmd_confirm.lower() == 'n':
                        print(f"{Fore.YELLOW}Command skipped{Style.RESET_ALL}")
                        continue
                    elif cmd_confirm.lower() == 'edit':
                        edited_cmd = input(f"{Fore.YELLOW}Enter modified command: {Style.RESET_ALL}")
                        if edited_cmd.strip():
                            command = edited_cmd
                
                result = self.execute_command(command)
                
                # Verify command execution with Gemini
                success, system_state, next_action, diagnostics = self.verify_command_execution(command, result)
                
                # Print system state and diagnostics
                if system_state:
                    print(f"{Fore.CYAN}System State: {system_state}{Style.RESET_ALL}")
                
                if diagnostics:
                    if diagnostics.get("is_installed") is not None:
                        status = "installed" if diagnostics["is_installed"] else "not installed"
                        print(f"{Fore.GREEN}Package Status: {status}{Style.RESET_ALL}")
                        
                        # Check if this completes our main task (for installation checks)
                        if is_check_installation and diagnostics["is_installed"] and is_program_related:
                            main_task_objective_achieved = True
                            main_task_result = f"Program is {status}"
                            
                    if diagnostics.get("error_type"):
                        print(f"{Fore.YELLOW}Error Type: {diagnostics['error_type']}{Style.RESET_ALL}")
                    if diagnostics.get("suggested_fix"):
                        print(f"{Fore.CYAN}Suggested Fix: {diagnostics['suggested_fix']}{Style.RESET_ALL}")
                
                if not success:
                    all_success = False
                    print(f"{Fore.RED}Command verification failed.{Style.RESET_ALL}")
                    
                    # Handle next action based on Gemini's decision
                    action = next_action.get("action", "abort")
                    reason = next_action.get("reason", "Unknown reason")
                    fallback_cmd = next_action.get("fallback_command")
                    
                    print(f"{Fore.YELLOW}Next Action: {action} - {reason}{Style.RESET_ALL}")
                    
                    if action == "retry" and fallback_cmd:
                        print(f"{Fore.CYAN}Trying fallback command: {fallback_cmd}{Style.RESET_ALL}")
                        result = self.execute_command(fallback_cmd)
                        success, system_state, next_action, diagnostics = self.verify_command_execution(fallback_cmd, result)
                        all_success = success
                    elif action == "skip":
                        print(f"{Fore.YELLOW}Skipping to next step.{Style.RESET_ALL}")
                        continue
                    elif action == "abort":
                        print(f"{Fore.RED}Aborting task.{Style.RESET_ALL}")
                        self.context.fail_current_task(f"Failed at subtask {i}: {subtask['description']}")
                        return
                    
                    if not all_success:
                        break
            
            # Complete or fail the subtask
            if all_success:
                self.context.complete_current_task("Completed successfully")
                print(f"{Fore.GREEN}Subtask completed successfully{Style.RESET_ALL}")
                
                # Check if this was a verification task and if the main task is now complete
                if is_check_installation and i < len(task_plan['subtasks']) and all_success:
                    main_task_objective_achieved = True
                    main_task_result = f"Program verification complete - Program is installed"
            else:
                self.context.fail_current_task("Command execution failed")
                print(f"{Fore.RED}Subtask failed{Style.RESET_ALL}")
                
                # Check if we should continue to next subtask
                if i < len(task_plan['subtasks']):
                    # Let Gemini decide if we should continue
                    prompt = f"""
# SUBTASK CONTINUATION DECISION

Current subtask failed but there are more subtasks available.
Should we continue to the next subtask?

Context:
- Failed Subtask: {subtask['description']}
- Next Subtask: {task_plan['subtasks'][i]['description']}
- System State: {system_state}

Return a JSON object with this structure:
{{
    "should_continue": true/false,
    "reason": "why we should or shouldn't continue"
}}
"""
                    try:
                        response = MODEL.generate_content(prompt)
                        text = response.text.strip()
                        
                        # Extract JSON from response
                        match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                        else:
                            match = re.search(r'({.*})', text, re.DOTALL)
                            if match:
                                json_str = match.group(1)
                            else:
                                json_str = text
                        
                        decision = json.loads(json_str)
                        if not decision.get("should_continue", False):
                            print(f"{Fore.RED}Task aborted: {decision.get('reason', 'Unknown reason')}{Style.RESET_ALL}")
                            return
                        else:
                            print(f"{Fore.YELLOW}Continuing to next subtask: {decision.get('reason', '')}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}Error making continuation decision: {str(e)}{Style.RESET_ALL}")
                        return
            
            # Check if main task objective has been achieved after subtask
            if main_task_objective_achieved:
                print(f"\n{Fore.GREEN}Main task objective achieved: {main_task_result}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Remaining subtasks are no longer necessary. Ending task.{Style.RESET_ALL}")
                break
                
            # After each subtask, if this is a verification task, check if we need to continue
            if is_check_installation and i < len(task_plan['subtasks']) and all_success:
                evaluate_prompt = f"""
# TASK CONTINUATION EVALUATION

Evaluate if the main task objective has been achieved and we should stop execution.

Context:
- Main Task: {task}
- Current Subtask: {subtask['description']}
- Subtask Result: {"Success" if all_success else "Failed"}
- System State: {system_state}
- Command Output: {result.get('stdout', '')}

Return a JSON object with this structure:
{{
    "is_complete": true/false,
    "reason": "explanation why the task is complete or needs to continue",
    "result": "summary of findings so far"
}}
"""
                try:
                    response = MODEL.generate_content(evaluate_prompt)
                    text = response.text.strip()
                    
                    # Extract JSON from response
                    match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                    else:
                        match = re.search(r'({.*})', text, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                        else:
                            json_str = text
                    
                    evaluation = json.loads(json_str)
                    if evaluation.get("is_complete", False):
                        main_task_objective_achieved = True
                        main_task_result = evaluation.get("result", "Task complete")
                        print(f"\n{Fore.GREEN}Main task objective achieved: {main_task_result}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Reason: {evaluation.get('reason', '')}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Remaining subtasks are no longer necessary. Ending task.{Style.RESET_ALL}")
                        break
                except Exception as e:
                    print(f"{Fore.YELLOW}Error evaluating task completion: {str(e)}{Style.RESET_ALL}")
        
        # Complete the main task
        if main_task_objective_achieved:
            print(f"\n{Fore.GREEN}Task completed: {task}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Result: {main_task_result}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}Task completed: {task}{Style.RESET_ALL}")
        
        self.context.complete_current_task("All necessary subtasks completed")
        
        # Save command history
        self.save_history()

if __name__ == "__main__":
    agent = AgentTerminal()
    agent.run() 