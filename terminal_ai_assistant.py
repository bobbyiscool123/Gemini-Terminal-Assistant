import os
import sys
import json
import yaml
import time
import signal
import subprocess
import logging
import random
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PTStyle
from dotenv import load_dotenv
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tqdm import tqdm
import colorama
from colorama import Fore, Style
import platform
import select

# Import the advanced AI prompts
try:
    from ai_prompts import STANDARD_PROMPT_TEMPLATE, ERROR_RECOVERY_PROMPT_TEMPLATE
except ImportError:
    # Fallback templates if import fails
    STANDARD_PROMPT_TEMPLATE = """You are a terminal command expert. Given the task: {task}, provide commands for {os_info}.
Return only the commands, one per line, without explanations."""
    
    ERROR_RECOVERY_PROMPT_TEMPLATE = """The command '{failed_command}' failed with error: {error_output}
Provide a different command to accomplish the task: {task} on {os_info}.
Return only the command, without explanations."""

# Import utility modules
from utils.command_aliases import CommandAliases
from utils.command_completion import CommandCompleter
from utils.command_templates import CommandTemplateManager
from utils.file_preview import FilePreview
from utils.filesystem_monitor import FilesystemMonitor
from utils.system_stats import SystemStats
from utils.command_chain import CommandChain
from utils.file_backup import FileBackup
from utils.smart_clipboard import SmartClipboard
from utils.plugin_manager import PluginManager

try:
    from utils.voice_commands import VoiceCommandHandler
except ImportError:
    VoiceCommandHandler = None

print("Starting initialization...")

# Initialize colorama for Windows support
colorama.init()

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print(f"{Fore.RED}Error: GOOGLE_API_KEY not found in environment variables{Style.RESET_ALL}")
    sys.exit(1)

print("Configuring Gemini API with Gemini 2.0 Flash...")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

class TerminalAIAssistant:
    def __init__(self):
        print("Initializing TerminalAIAssistant...")
        with Progress() as progress:
            init_task = progress.add_task("[cyan]Initializing...", total=11)
            
            # Basic setup
            self.console = Console()
            progress.update(init_task, advance=1, description="[cyan]Setting up console...")
            
            # Configure prompt session to ensure input is visible
            from prompt_toolkit.styles import Style as PTStyle
            from prompt_toolkit.history import InMemoryHistory
            self.session = PromptSession(
                history=InMemoryHistory(),
                enable_history_search=True,
                complete_in_thread=True,
                complete_while_typing=True,
                vi_mode=False,  # Set to True for vi key bindings
                wrap_lines=True,
                # Ensure input is echoed to screen
                input_processors=[],
                enable_system_prompt=True,
                mouse_support=True
            )
            progress.update(init_task, advance=1, description="[cyan]Setting up prompt session...")
            
            self.command_history: List[Dict] = []
            self.current_directory = os.getcwd()
            progress.update(init_task, advance=1, description="[cyan]Loading configuration...")
            
            print(f"Current directory: {self.current_directory}")
            self.config = self.load_config()
            
            # Initialize utilities
            progress.update(init_task, advance=1, description="[cyan]Setting up command aliases...")
            self.command_aliases = CommandAliases(config_path="config.yaml")
            
            progress.update(init_task, advance=1, description="[cyan]Setting up command templates...")
            self.command_templates = CommandTemplateManager()
            
            progress.update(init_task, advance=1, description="[cyan]Setting up file preview...")
            self.file_preview = FilePreview(config=self.config)
            
            progress.update(init_task, advance=1, description="[cyan]Setting up system stats...")
            self.system_stats = SystemStats(refresh_interval=5)
            
            progress.update(init_task, advance=1, description="[cyan]Setting up file backup...")
            self.file_backup = FileBackup(config=self.config)
            
            progress.update(init_task, advance=1, description="[cyan]Setting up smart clipboard...")
            self.smart_clipboard = SmartClipboard()
            
            # Initialize plugin manager
            progress.update(init_task, advance=1, description="[cyan]Setting up plugin manager...")
            self.plugin_manager = PluginManager(plugins_dir="plugins", config_file="plugins.yaml")
            self.plugin_manager.set_terminal_assistant(self)
            plugin_results = self.plugin_manager.load_all_plugins()
            plugin_count = sum(1 for result in plugin_results.values() if result)
            if plugin_count > 0:
                self.console.print(f"[green]Loaded {plugin_count} plugins[/green]")
            
            # Initialize voice commands if enabled
            self.voice_handler = None
            if self.config.get("enable_voice_commands", False) and VoiceCommandHandler:
                progress.update(init_task, advance=0.5, description="[cyan]Setting up voice commands...")
                self.voice_handler = VoiceCommandHandler(config=self.config)
            
            # Setup remaining components
            progress.update(init_task, advance=0.5, description="[cyan]Setting up signal handlers...")
            self.observer = None
            self.setup_signal_handlers()
            
        print("Initialization complete!")

        # Load command history after initialization
        self.load_history()
        
        # Start services if enabled in config
        if self.config.get("show_system_stats", False):
            self.system_stats.start_monitoring()
            
        if self.config.get("enable_voice_commands", False) and self.voice_handler and self.voice_handler.is_available():
            self.voice_handler.start_listening(self.handle_voice_command)
            
        # Create backup directory if needed
        if self.config.get("backup_history_files", True):
            os.makedirs("backups", exist_ok=True)
            
        # Create plugins directory if needed
        os.makedirs("plugins", exist_ok=True)

    def load_config(self) -> Dict:
        """Load configuration from config.yaml"""
        print("Loading configuration...")
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        print("No config file found, using defaults")
        return {
            "max_history": 100,
            "auto_save": True,
            "theme": "dark",
            "stream_output": True,
            "confirm_dangerous": True,
            "timeout": 30,
            "max_retries": 3,
            "output_format": "rich",
            "save_history": True,
            "history_file": "command_history.json"
        }

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        print("Setting up signal handlers...")
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signals"""
        print("\nShutting down gracefully...")
        if self.observer:
            self.observer.stop()
        self.save_history()
        sys.exit(0)

    def get_prompt_style(self) -> PTStyle:
        """Get the prompt style based on theme"""
        return PTStyle.from_dict({
            'prompt': 'bold green',
            'input': 'bold white',
        })

    def save_history(self):
        """Save command history to file"""
        if self.config.get("save_history"):
            print("Saving command history...")
            with open(self.config["history_file"], 'w') as f:
                json.dump(self.command_history, f, indent=2)

    def load_history(self):
        """Load command history from file"""
        if self.config.get("save_history") and os.path.exists(self.config["history_file"]):
            print("Loading command history...")
            with open(self.config["history_file"], 'r') as f:
                self.command_history = json.load(f)

    def execute_command(self, command: str) -> Dict:
        """Execute a command and return its result"""
        print(f"Executing command: {command}")
        start_time = time.time()
        
        # Execute special commands
        if command.startswith("ai_ask:"):
            # AI is asking a question
            question = command[7:].strip()
            print(f"{Fore.YELLOW}AI is asking: {question}{Style.RESET_ALL}")
            answer = input(f"{Fore.CYAN}> {Style.RESET_ALL}")
            return {
                "command": command,
                "stdout": f"Question: {question}\nAnswer: {answer}",
                "stderr": "",
                "exit_code": 0,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
        else:
            try:
                # For standard shell commands
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=self.config["timeout"])
                    end_time = time.time()
                    
                    # If command failed, log it more clearly
                    if process.returncode != 0:
                        print(f"{Fore.RED}Command failed with return code {process.returncode}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Command: {command}{Style.RESET_ALL}")
                        if stderr:
                            print(f"{Fore.RED}Error output: {stderr}{Style.RESET_ALL}")
                    
                    return {
                        "command": command,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": process.returncode,
                        "execution_time": end_time - start_time,
                        "timestamp": datetime.now().isoformat()
                    }
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"{Fore.RED}Command timed out after {self.config['timeout']} seconds{Style.RESET_ALL}")
                    return {
                        "command": command,
                        "stdout": "",
                        "stderr": f"Command timed out after {self.config['timeout']} seconds",
                        "exit_code": -1,
                        "execution_time": self.config["timeout"],
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                error_msg = f"Exception while executing command: {str(e)}"
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                return {
                    "command": command,
                    "stdout": "",
                    "stderr": error_msg,
                    "exit_code": 1,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }

    def stream_command_output(self, command: str):
        """Stream command output in real-time"""
        print(f"Streaming output for command: {command}")
        start_time = time.time()
        
        # Special handling for git commands on Windows
        is_windows = platform.system() == "Windows"
        is_git_command = command.strip().startswith("git ")
        
        if is_windows and is_git_command:
            # Add special handling for git commands that may not work well with streaming
            if "git commit" in command and "-m" not in command:
                command = f"{command} -m \"Automatic commit from Terminal AI Assistant\""
                print(f"Modified git commit command to: {command}")
            
            # For Windows, use a different approach for git commands
            try:
                # Run git commands with subprocess.run instead of Popen for better Windows compatibility
                print(f"{Fore.CYAN}Executing git command directly...{Style.RESET_ALL}")
                process = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Process output
                if process.stdout:
                    print(process.stdout)
                    
                # Process errors    
                if process.stderr:
                    print(f"{Fore.RED}Error output:{Style.RESET_ALL}")
                    print(process.stderr)
                
                # Store the result
                self.last_process_result = {
                    "command": command,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Yield a summary of what happened
                if process.returncode == 0:
                    yield f"Command completed successfully"
                else:
                    yield f"Command failed with exit code {process.returncode}"
                
                # Early return for git commands
                return
            except Exception as e:
                error_msg = f"Exception while executing git command: {str(e)}"
                print(f"\n{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
                print(f"{Fore.RED}ERROR EXECUTING GIT COMMAND: {command}{Style.RESET_ALL}")
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
                print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}\n")
                
                # Store error information
                self.last_process_result = {
                    "command": command,
                    "stdout": "",
                    "stderr": error_msg,
                    "exit_code": 1,
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield f"Error: {str(e)}"
                return
        
        # Check for interactive commands that require input
        interactive_commands = {
            "git commit": "-m \"Automatic commit from Terminal AI Assistant\"",
            "git pull": "--no-edit",
            "git merge": "--no-edit"
        }
        
        # Modify command if it's interactive to provide automatic input
        original_command = command
        for interactive_cmd, auto_arg in interactive_commands.items():
            if command.startswith(interactive_cmd) and auto_arg not in command:
                command = f"{command} {auto_arg}"
                print(f"Modified potentially interactive command to: {command}")
                break
                
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Set a timeout for command execution
            max_execution_time = self.config.get("timeout", 30)  # Default 30 seconds
            
            # Collect all stdout lines
            stdout_lines = []
            while True:
                # Check if we've exceeded the timeout
                if time.time() - start_time > max_execution_time:
                    print(f"{Fore.RED}Command execution timed out after {max_execution_time} seconds.{Style.RESET_ALL}")
                    process.kill()
                    stderr_output = f"Command timed out after {max_execution_time} seconds."
                    
                    # Store timeout error in the result
                    self.last_process_result = {
                        "command": original_command,
                        "stdout": "\n".join(stdout_lines),
                        "stderr": stderr_output,
                        "exit_code": -1,  # Use -1 for timeout
                        "execution_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    yield f"Error: Command timed out after {max_execution_time} seconds."
                    return
                
                # Try to read a line with a non-blocking approach that works on Windows
                output = None
                try:
                    # Check if process has finished
                    if process.poll() is not None:
                        # If process has finished and no more output, break the loop
                        if not process.stdout.readable():
                            break
                    
                    # Try to read a line non-blocking
                    output = process.stdout.readline()
                    
                    # Small delay to prevent high CPU usage
                    time.sleep(0.1)
                except Exception as e:
                    # Log the error but continue
                    print(f"{Fore.RED}Error reading process output: {str(e)}{Style.RESET_ALL}")
                    time.sleep(0.1)

                # If we've read an empty line and process is done, break
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    self.console.print(output.strip())
                    stdout_lines.append(output.strip())
                    yield output.strip()
            
            # Check for stderr output
            stderr_output = process.stderr.read()
            if stderr_output:
                self.console.print(f"[red]Error output:[/red]")
                self.console.print(stderr_output)
                
            return_code = process.poll()
            if return_code != 0:
                self.console.print(f"[red]Command failed with return code {return_code}[/red]")
                self.console.print(f"[yellow]Command that failed: {original_command}[/yellow]")
                
                # Add recovery suggestion
                if "command not found" in stderr_output:
                    self.console.print(f"[yellow]Suggestion: The command may not be installed on your system.[/yellow]")
                elif "permission denied" in stderr_output.lower():
                    self.console.print(f"[yellow]Suggestion: You may need elevated permissions to run this command.[/yellow]")
                elif "would be overwritten by merge" in stderr_output.lower():
                    self.console.print(f"[yellow]Suggestion: Try running 'git stash' before this command.[/yellow]")
                elif "editor" in stderr_output.lower() or "terminal" in stderr_output.lower():
                    self.console.print(f"[yellow]Suggestion: This command requires an interactive terminal. Add a message argument to avoid this.[/yellow]")
            
            # Store the full process result for later use
            end_time = time.time()
            self.last_process_result = {
                "command": original_command,
                "stdout": "\n".join(stdout_lines),
                "stderr": stderr_output,
                "exit_code": return_code,
                "execution_time": end_time - start_time,
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            error_msg = f"Exception while executing command: {str(e)}"
            # Make errors more visible with formatting and line separators
            print(f"\n{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.RED}ERROR EXECUTING COMMAND: {original_command}{Style.RESET_ALL}")
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}\n")
            
            # Also log to console for rich formatting support
            self.console.print(f"[red]{error_msg}[/red]")
            
            # Store error information in the result
            self.last_process_result = {
                "command": original_command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 1,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"Error: {str(e)}"

    def get_ai_response(self, task: str, failed_command: str = None, error_output: str = None) -> List[str]:
        """Get AI response for the given task"""
        print(f"Getting AI response for task: {task}")
        
        # Import expanded prompts if available
        try:
            from ai_prompts import STANDARD_PROMPT_TEMPLATE, ERROR_RECOVERY_PROMPT_TEMPLATE
            print(f"{Fore.GREEN}Using enhanced AI prompts for improved command generation{Style.RESET_ALL}")
        except ImportError:
            # Define fallback prompts if import fails
            print(f"{Fore.YELLOW}Enhanced AI prompts not found, using built-in prompts{Style.RESET_ALL}")
            # Use existing prompt templates (code won't change)
            
        # Get detailed OS information
        os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare context for prompts
        context = {
            "task": task,
            "current_directory": self.current_directory,
            "os_info": os_info,
            "platform": sys.platform,
            "platform_machine": platform.machine(),
            "timestamp": timestamp
        }
        
        if failed_command and error_output:
            # If we're regenerating after a failed command, include the error details
            try:
                # Try to use the expanded error recovery prompt
                context["failed_command"] = failed_command
                context["error_output"] = error_output
                prompt = ERROR_RECOVERY_PROMPT_TEMPLATE.format(**context)
            except (NameError, KeyError) as e:
                # Fallback to the built-in error recovery prompt
                prompt = f"""# TERMINAL COMMAND ASSISTANT - ERROR RECOVERY MODE

## PRIMARY ROLE DEFINITION
You are TERMINALEX, the Terminal Command Error Recovery Specialist.
Your mission is to analyze the failed command and provide a corrected alternative.

## COMMAND FAILURE ANALYSIS
Failed Command: `{failed_command}`
Error Message: `{error_output}`
Original User Objective: {task}
Working Directory: {self.current_directory}
Operating System: {os_info}
Platform: {sys.platform}

## CRITICAL REQUIREMENTS
1. NEVER repeat the exact same command that failed
2. Provide ONLY the corrected command(s), one per line
3. Do NOT include explanations, markdown, or code blocks
4. Focus on addressing the ROOT CAUSE of the failure

## WINDOWS COMMAND REFERENCES
- File Operations: use 'copy', 'move', 'del', not 'cp', 'mv', 'rm'
- Process Management: use 'taskkill /F /IM process.exe' instead of 'Stop-Process'
- Git Operations: Always use non-interactive forms, like 'git commit -m "message"'

## OUTPUT FORMAT
Return ONLY the corrected command(s), one per line.
DO NOT include any explanation or formatting.
"""
        else:
            # Standard request for new commands
            try:
                # Try to use the expanded standard prompt
                prompt = STANDARD_PROMPT_TEMPLATE.format(**context)
            except (NameError, KeyError) as e:
                # Fallback to the built-in standard prompt
                prompt = f"""# TERMINAL COMMAND ASSISTANT

## ROLE AND MISSION
You are an expert Terminal Command Assistant for {os_info}.
Your mission is to translate the task into executable commands.

## TASK CONTEXT
Task: {task}
Current Directory: {self.current_directory}
Operating System: {os_info}
Platform: {sys.platform}

## COMMAND GENERATION REQUIREMENTS
1. Generate ONLY executable terminal commands, one per line
2. All commands must be appropriate for {os_info}
3. Do NOT include explanations or formatting
4. For Windows, use CMD.exe compatible commands

## WINDOWS COMMAND GUIDELINES
- File Management: dir, copy, move, del, mkdir, rmdir
- Process Management: taskkill /F /IM program.exe
- Git Operations: Always include '-m' for commit messages

## OUTPUT FORMAT
Return ONLY the executable commands, one per line.
"""

        # Generate AI response using the appropriate prompt
        response = model.generate_content(prompt)
        commands = [cmd.strip() for cmd in response.text.split('\n') if cmd.strip()]
        
        # Add commit message if we're committing
        if task.lower().startswith("commit") and commands and "git commit" in commands[0] and "-m" not in commands[0]:
            commands[0] = f'git commit -m "Automatic commit from Terminal AI Assistant"'
            
        # Make sure we're not repeating the same failed command
        if failed_command and commands and commands[0].strip().lower() == failed_command.strip().lower():
            # If the AI generated the same command again, use hardcoded fallbacks for common tasks
            if "chrome" in task.lower() and ("close" in task.lower() or "kill" in task.lower() or "stop" in task.lower()):
                # For closing Chrome
                return ["wmic process where name='chrome.exe' delete"]
            elif "process" in failed_command.lower() or "taskkill" in failed_command.lower():
                # For killing any process
                if "/im" in failed_command.lower():
                    process_name = failed_command.split("/IM")[1].split()[0].strip().replace('"', '')
                    return [f"wmic process where name='{process_name}' delete"]
                else:
                    return ["wmic process where name='chrome.exe' delete"]
                
        return commands

    def display_command_result(self, result: Dict):
        """Display command execution result in a formatted way"""
        table = Table(title="Command Execution Result")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        for key, value in result.items():
            if key not in ["stdout", "stderr"]:
                table.add_row(key, str(value))

        self.console.print(table)

        if result.get("stdout"):
            self.console.print(Panel(result["stdout"], title="Output", border_style="green"))
        if result.get("stderr"):
            self.console.print(Panel(result["stderr"], title="Error", border_style="red"))

    def run(self):
        """Main run loop"""
        print("Starting main loop...")
        self.console.print(Panel.fit(
            "[bold green]Terminal AI Assistant[/bold green]\n"
            "[yellow]Type 'exit' to quit, 'help' for commands[/yellow]",
            border_style="blue"
        ))

        # Check if echo_input is enabled in config
        echo_input = self.config.get("echo_input", True)
        use_standard_input = self.config.get("use_standard_input", False)
        
        while True:
            try:
                # Use standard input if configured or if prompt_toolkit has issues
                if use_standard_input:
                    print("\nWhat would you like me to do? ", end="", flush=True)
                    task = input()
                else:
                    try:
                        task = self.session.prompt(
                            "\nWhat would you like me to do? ",
                            style=self.get_prompt_style()
                        )
                    except Exception as e:
                        print(f"Error with prompt toolkit: {str(e)}")
                        print("Falling back to standard input...")
                        self.config["use_standard_input"] = True
                        print("\nWhat would you like me to do? ", end="", flush=True)
                        task = input()
                
                # Echo the input if enabled
                if echo_input and not use_standard_input:
                    print(f"You entered: {task}")

                if task.lower() in ['exit', 'quit']:
                    break
                elif task.lower() == 'help':
                    self.show_help()
                    continue
                elif task.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif task.lower() == 'history':
                    self.display_command_history()
                    continue
                elif task.lower() == 'config':
                    self.display_config()
                    continue
                elif task.lower().startswith('cd '):
                    path = task[3:].strip()
                    self.change_directory(path)
                    continue
                elif task.lower() == 'pwd':
                    self.console.print(f"Current directory: {self.current_directory}")
                    continue
                # Handle new commands
                elif task.lower() == 'aliases' or task.lower().startswith('alias '):
                    args = task.split()[1:] if task.lower().startswith('alias ') else []
                    self.handle_alias_command(args)
                    continue
                elif task.lower() == 'templates' or task.lower().startswith('template '):
                    args = task.split()[1:] if task.lower().startswith('template ') else []
                    self.handle_template_command(args)
                    continue
                elif task.lower().startswith('preview '):
                    args = task.split()[1:]
                    self.handle_preview_command(args)
                    continue
                elif task.lower() == 'stats':
                    self.handle_stats_command([])
                    continue
                elif task.lower() == 'backups' or task.lower().startswith('backup '):
                    args = task.split()[1:] if task.lower().startswith('backup ') else []
                    self.handle_backup_command(args)
                    continue
                elif task.lower().startswith('restore '):
                    args = ['restore'] + task.split()[1:]
                    self.handle_backup_command(args)
                    continue
                elif task.lower().startswith('chain '):
                    args = task.split()[1:]
                    self.handle_chain_command(args)
                    continue
                elif task.lower() == 'clipboard' or task.lower().startswith('clipboard '):
                    args = task.split()[1:] if task.lower().startswith('clipboard ') else []
                    self.handle_clipboard_command(args)
                    continue
                elif task.lower().startswith('copy '):
                    args = ['copy'] + [task[5:]]
                    self.handle_clipboard_command(args)
                    continue
                elif task.lower().startswith('transform '):
                    args = ['transform'] + task.split()[1:]
                    self.handle_clipboard_command(args)
                    continue
                elif task.lower().startswith('voice '):
                    setting = task.split()[1].lower() if len(task.split()) > 1 else ""
                    if setting in ['on', 'off']:
                        if self.voice_handler:
                            if setting == 'on':
                                self.voice_handler.start_listening(self.handle_voice_command)
                                self.console.print("[green]Voice commands enabled[/green]")
                            else:
                                self.voice_handler.stop_listening()
                                self.console.print("[yellow]Voice commands disabled[/yellow]")
                        else:
                            self.console.print("[red]Voice command handler not available[/red]")
                    continue
                elif task.lower() == 'plugins' or task.lower().startswith('plugin '):
                    args = task.split()[1:] if task.lower().startswith('plugin ') else []
                    self.handle_plugin_command(args)
                    continue
                
                # Check if this is a plugin command
                if hasattr(self, 'plugin_manager'):
                    cmd_parts = task.split()
                    cmd_name = cmd_parts[0].lower()
                    
                    if cmd_name in self.plugin_manager.plugin_commands:
                        result = self.plugin_manager.execute_plugin_command(cmd_name, cmd_parts[1:])
                        if result:
                            self.command_history.append(result)
                            
                            if result.get("exit_code", 0) == 0:
                                self.console.print(Panel(result.get("stdout", ""), 
                                                      title=f"Plugin Command: {cmd_name}", 
                                                      border_style="green"))
                            else:
                                self.console.print(Panel(result.get("stderr", ""),
                                                      title=f"Plugin Command Error: {cmd_name}",
                                                      border_style="red"))
                                
                            # Save history if configured
                            if self.config["auto_save"]:
                                self.save_history()
                                
                        continue

                # Process command aliases
                if self.command_aliases and hasattr(self.command_aliases, 'expand_alias'):
                    expanded_task = self.command_aliases.expand_alias(task)
                    if expanded_task != task:
                        self.console.print(f"[cyan]Expanded alias:[/cyan] {expanded_task}")
                        task = expanded_task

                with Progress() as progress:
                    task_progress = progress.add_task("[cyan]Processing...", total=None)
                    
                    commands = self.get_ai_response(task)
                    
                    for i, command in enumerate(commands, 1):
                        progress.update(task_progress, description=f"[cyan]Executing command {i}/{len(commands)}")

                        if self.config["confirm_dangerous"] and self.is_dangerous_command(command):
                            if not Prompt.ask("This command might be dangerous. Continue? (y/n)").lower() == 'y':
                                continue

                        # Process command with plugin pre-hooks
                        if hasattr(self, 'plugin_manager'):
                            for plugin in self.plugin_manager.plugins.values():
                                if hasattr(plugin, 'on_command_pre'):
                                    command = plugin.on_command_pre(command)

                        # Execute the command
                        if self.config["stream_output"]:
                            result = None
                            stderr_output = ""
                            
                            # Collect stderr output during streaming
                            for output in self.stream_command_output(command):
                                pass
                                
                            # Get the last process result after streaming
                            if hasattr(self, 'last_process_result') and self.last_process_result:
                                result = self.last_process_result
                        else:
                            result = self.execute_command(command)

                        # Process result with plugin post-hooks
                        if result and hasattr(self, 'plugin_manager'):
                            for plugin in self.plugin_manager.plugins.values():
                                if hasattr(plugin, 'on_command_post'):
                                    result = plugin.on_command_post(command, result)

                        # Save command to history
                        if result:
                            self.command_history.append(result)
                            if len(self.command_history) > self.config["max_history"]:
                                self.command_history.pop(0)
                                
                            # Save history if configured
                            if self.config["auto_save"]:
                                self.save_history()

                        # Check for command failure and try to recover
                        if result and result.get("exit_code", 0) != 0:
                            error_output = result.get("stderr", "")
                            self.console.print(f"[red]Command failed: {command}[/red]")
                            
                            # Try to get a recovery command
                            recovery_commands = self.get_ai_response(task, command, error_output)
                            if recovery_commands:
                                self.console.print(f"[yellow]Attempting recovery with: {recovery_commands[0]}[/yellow]")
                                if Prompt.ask("Try this recovery command? (y/n)").lower() == 'y':
                                    recovery_result = self.execute_command(recovery_commands[0])
                                    self.command_history.append(recovery_result)
                                    
                                    # Save after recovery attempt
                                    if self.config["auto_save"]:
                                        self.save_history()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operation cancelled by user[/yellow]")
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
                continue
                
        # Clean up before exit
        if self.config.get("show_system_stats", False):
            self.system_stats.stop_monitoring()
            
        if self.voice_handler and hasattr(self.voice_handler, 'stop_listening'):
            self.voice_handler.stop_listening()
            
        # Save history one last time
        self.save_history()
        
        self.console.print("[green]Thank you for using Terminal AI Assistant![/green]")

    def display_command_history(self):
        """Display command history"""
        if not self.command_history:
            self.console.print("[yellow]No command history available[/yellow]")
            return
            
        table = Table(title="Command History")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Command", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Time", style="blue")
        
        for i, cmd in enumerate(self.command_history):
            status = "[green]Success[/green]" if cmd.get("exit_code", 1) == 0 else f"[red]Failed ({cmd.get('exit_code')})[/red]"
            execution_time = f"{cmd.get('execution_time', 0):.2f}s"
            table.add_row(str(i+1), cmd.get("command", ""), status, execution_time)
            
        self.console.print(table)
        
    def display_config(self):
        """Display current configuration"""
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in self.config.items():
            table.add_row(key, str(value))
            
        self.console.print(table)

    def handle_alias_command(self, args: List[str]):
        """Handle alias commands"""
        if not self.command_aliases:
            self.console.print("[red]Command aliases not available[/red]")
            return
            
        if not args:
            # List all aliases
            aliases = self.command_aliases.get_all_aliases()
            if not aliases:
                self.console.print("[yellow]No aliases defined[/yellow]")
                return
                
            table = Table(title="Command Aliases")
            table.add_column("Alias", style="cyan")
            table.add_column("Command", style="green")
            
            for alias, command in aliases.items():
                table.add_row(alias, command)
                
            self.console.print(table)
            return
            
        action = args[0].lower()
        
        if action == "add" and len(args) >= 3:
            # Add a new alias
            alias_name = args[1]
            alias_command = " ".join(args[2:])
            
            try:
                self.command_aliases.add_alias(alias_name, alias_command)
                self.console.print(f"[green]Added alias '{alias_name}' for command: {alias_command}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error adding alias: {str(e)}[/red]")
                
        elif action == "remove" and len(args) >= 2:
            # Remove an alias
            alias_name = args[1]
            
            try:
                self.command_aliases.remove_alias(alias_name)
                self.console.print(f"[green]Removed alias '{alias_name}'[/green]")
            except Exception as e:
                self.console.print(f"[red]Error removing alias: {str(e)}[/red]")
                
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]aliases[/cyan] - List all aliases\n  [cyan]alias add [name] [command][/cyan] - Add an alias\n  [cyan]alias remove [name][/cyan] - Remove an alias")

    def handle_template_command(self, args: List[str]):
        """Handle template commands"""
        if not self.command_templates:
            self.console.print("[red]Command templates not available[/red]")
            return
            
        if not args:
            # List all templates
            templates = self.command_templates.get_all_templates()
            if not templates:
                self.console.print("[yellow]No templates defined[/yellow]")
                return
                
            table = Table(title="Command Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Template", style="green")
            table.add_column("Parameters", style="yellow")
            
            for name, template in templates.items():
                params = ", ".join([f"{{{p}}}" for p in self.command_templates.get_template_params(name)])
                table.add_row(name, template, params)
                
            self.console.print(table)
            return
            
        action = args[0].lower()
        
        if action == "add" and len(args) >= 3:
            # Add a new template
            template_name = args[1]
            template_command = " ".join(args[2:])
            
            try:
                self.command_templates.add_template(template_name, template_command)
                self.console.print(f"[green]Added template '{template_name}': {template_command}[/green]")
                
                # Show detected parameters
                params = self.command_templates.get_template_params(template_name)
                if params:
                    self.console.print(f"[cyan]Template parameters: {', '.join([f'{{{p}}}' for p in params])}")
            except Exception as e:
                self.console.print(f"[red]Error adding template: {str(e)}[/red]")
                
        elif action == "remove" and len(args) >= 2:
            # Remove a template
            template_name = args[1]
            
            try:
                self.command_templates.remove_template(template_name)
                self.console.print(f"[green]Removed template '{template_name}'[/green]")
            except Exception as e:
                self.console.print(f"[red]Error removing template: {str(e)}[/red]")
                
        elif action == "run" and len(args) >= 2:
            # Run a template
            template_name = args[1]
            template_params = {}
            
            # Parse parameters (name=value format)
            for param in args[2:]:
                if "=" in param:
                    key, value = param.split("=", 1)
                    template_params[key] = value
            
            try:
                # Execute the template
                command = self.command_templates.render_template(template_name, template_params)
                self.console.print(f"[cyan]Executing: {command}[/cyan]")
                
                result = None
                if self.config["stream_output"]:
                    for output in self.stream_command_output(command):
                        pass
                    result = self.last_process_result if hasattr(self, 'last_process_result') else None
                else:
                    result = self.execute_command(command)
                
                if result:
                    self.command_history.append(result)
                    
                    # Save history if configured
                    if self.config["auto_save"]:
                        self.save_history()
            except Exception as e:
                self.console.print(f"[red]Error running template: {str(e)}[/red]")
                
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]templates[/cyan] - List all templates\n  [cyan]template add [name] [template][/cyan] - Add a template\n  [cyan]template remove [name][/cyan] - Remove a template\n  [cyan]template run [name] [param1=value1...][/cyan] - Run a template")

    def handle_preview_command(self, args: List[str]):
        """Handle file preview commands"""
        if not self.file_preview:
            self.console.print("[red]File preview not available[/red]")
            return
            
        if not args:
            self.console.print("[yellow]Usage: preview [file_path][/yellow]")
            return
            
        file_path = args[0]
        
        # Support basic globbing and wildcards
        if '*' in file_path or '?' in file_path:
            from glob import glob
            matching_files = glob(os.path.join(self.current_directory, file_path))
            
            if not matching_files:
                self.console.print(f"[yellow]No files match the pattern: {file_path}[/yellow]")
                return
                
            if len(matching_files) > 5:
                self.console.print(f"[yellow]Found {len(matching_files)} files. Showing first 5:[/yellow]")
                matching_files = matching_files[:5]
                
            for file in matching_files:
                self.console.print(f"[cyan]Preview of {file}:[/cyan]")
                try:
                    content = self.file_preview.preview_file(file)
                    self.console.print(Panel(content, title=file, border_style="green"))
                except Exception as e:
                    self.console.print(f"[red]Error previewing file: {str(e)}[/red]")
            return
            
        # Handle single file preview
        try:
            # Convert relative path to absolute if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
                
            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return
                
            content = self.file_preview.preview_file(file_path)
            self.console.print(Panel(content, title=file_path, border_style="green"))
        except Exception as e:
            self.console.print(f"[red]Error previewing file: {str(e)}[/red]")

    def handle_stats_command(self, args: List[str]):
        """Handle system stats commands"""
        if not self.system_stats:
            self.console.print("[red]System stats not available[/red]")
            return
            
        # Get current system stats
        try:
            stats = self.system_stats.get_current_stats()
            
            table = Table(title="System Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in stats.items():
                if isinstance(value, float):
                    # Format percentages and numbers
                    if "percent" in key.lower() or "usage" in key.lower():
                        formatted_value = f"{value:.1f}%"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                    
                table.add_row(key, formatted_value)
                
            self.console.print(table)
            
            # Show chart if requested
            if args and args[0].lower() == "chart":
                if hasattr(self.system_stats, "generate_chart"):
                    chart = self.system_stats.generate_chart()
                    self.console.print(chart)
                else:
                    self.console.print("[yellow]Chart generation not available[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error getting system stats: {str(e)}[/red]")

    def handle_backup_command(self, args: List[str]):
        """Handle backup commands"""
        if not self.file_backup:
            self.console.print("[red]File backup not available[/red]")
            return
            
        if not args:
            # List all backups
            try:
                backups = self.file_backup.list_backups()
                
                if not backups:
                    self.console.print("[yellow]No backups available[/yellow]")
                    return
                    
                table = Table(title="File Backups")
                table.add_column("ID", style="cyan")
                table.add_column("File", style="green")
                table.add_column("Date", style="yellow")
                table.add_column("Size", style="blue")
                
                for backup in backups:
                    table.add_row(
                        str(backup.get("id", "")), 
                        backup.get("original_path", ""),
                        backup.get("timestamp", ""),
                        backup.get("size", "")
                    )
                    
                self.console.print(table)
            except Exception as e:
                self.console.print(f"[red]Error listing backups: {str(e)}[/red]")
            return
                
        action = args[0].lower()
        
        if action == "backup" and len(args) >= 2:
            # Create a backup
            file_path = args[1]
            
            # Convert relative path to absolute if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_directory, file_path)
                
            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return
                
            try:
                backup_id = self.file_backup.create_backup(file_path)
                self.console.print(f"[green]Created backup of '{file_path}' with ID: {backup_id}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error creating backup: {str(e)}[/red]")
                
        elif action == "restore" and len(args) >= 2:
            # Restore a backup
            backup_id = args[1]
            
            try:
                restored_path = self.file_backup.restore_backup(backup_id)
                self.console.print(f"[green]Restored backup to: {restored_path}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error restoring backup: {str(e)}[/red]")
                
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]backups[/cyan] - List all backups\n  [cyan]backup [file_path][/cyan] - Create a backup\n  [cyan]restore [backup_id][/cyan] - Restore a backup")

    def handle_chain_command(self, args: List[str]):
        """Handle command chain operations"""
        if not hasattr(self, 'command_chain'):
            # Create a CommandChain instance if not available
            try:
                from utils.command_chain import CommandChain
                self.command_chain = CommandChain()
            except ImportError:
                self.console.print("[red]Command chain functionality not available[/red]")
                return
                
        if not args:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]chain list[/cyan] - List all command chains\n  [cyan]chain add [name] [commands][/cyan] - Add a command chain\n  [cyan]chain run [name][/cyan] - Run a command chain")
            return
            
        action = args[0].lower()
        
        if action == "list":
            # List all chains
            chains = self.command_chain.get_all_chains()
            
            if not chains:
                self.console.print("[yellow]No command chains defined[/yellow]")
                return
                
            table = Table(title="Command Chains")
            table.add_column("Name", style="cyan")
            table.add_column("Commands", style="green")
            
            for name, commands in chains.items():
                table.add_row(name, "; ".join(commands))
                
            self.console.print(table)
            
        elif action == "add" and len(args) >= 3:
            # Add a new chain
            chain_name = args[1]
            # Commands are specified as semicolon-separated list
            chain_commands = " ".join(args[2:]).split(";")
            chain_commands = [cmd.strip() for cmd in chain_commands if cmd.strip()]
            
            if not chain_commands:
                self.console.print("[red]No commands specified[/red]")
                return
                
            try:
                self.command_chain.add_chain(chain_name, chain_commands)
                self.console.print(f"[green]Added command chain '{chain_name}' with {len(chain_commands)} commands[/green]")
            except Exception as e:
                self.console.print(f"[red]Error adding command chain: {str(e)}[/red]")
                
        elif action == "run" and len(args) >= 2:
            # Run a chain
            chain_name = args[1]
            
            try:
                commands = self.command_chain.get_chain(chain_name)
                
                if not commands:
                    self.console.print(f"[red]Command chain '{chain_name}' not found[/red]")
                    return
                    
                self.console.print(f"[cyan]Running command chain '{chain_name}' ({len(commands)} commands)[/cyan]")
                
                for i, command in enumerate(commands, 1):
                    self.console.print(f"[yellow]Command {i}/{len(commands)}: {command}[/yellow]")
                    
                    result = None
                    if self.config["stream_output"]:
                        for output in self.stream_command_output(command):
                            pass
                        result = self.last_process_result if hasattr(self, 'last_process_result') else None
                    else:
                        result = self.execute_command(command)
                    
                    if result:
                        self.command_history.append(result)
                        
                        # Check if command failed and break the chain if needed
                        if result.get("exit_code", 0) != 0:
                            self.console.print(f"[red]Chain execution stopped due to command failure[/red]")
                            
                            # Ask if user wants to continue despite error
                            if Prompt.ask("Continue chain execution despite error? (y/n)").lower() != 'y':
                                break
                                
                # Save history if configured
                if self.config["auto_save"]:
                    self.save_history()
                    
                self.console.print(f"[green]Command chain '{chain_name}' execution completed[/green]")
            except Exception as e:
                self.console.print(f"[red]Error running command chain: {str(e)}[/red]")
                
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]chain list[/cyan] - List all command chains\n  [cyan]chain add [name] [commands][/cyan] - Add a command chain\n  [cyan]chain run [name][/cyan] - Run a command chain")

    def handle_clipboard_command(self, args: List[str]):
        """Handle clipboard operations"""
        if not self.smart_clipboard:
            self.console.print("[red]Smart clipboard not available[/red]")
            return
            
        if not args:
            # Show clipboard content
            try:
                content = self.smart_clipboard.get_clipboard()
                if content:
                    self.console.print(Panel(content, title="Clipboard Content", border_style="green"))
                else:
                    self.console.print("[yellow]Clipboard is empty[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error accessing clipboard: {str(e)}[/red]")
            return
            
        action = args[0].lower()
        
        if action == "copy" and len(args) >= 2:
            text = args[1]
            
            # Check if this is a file path
            if os.path.exists(text):
                try:
                    with open(text, 'r') as f:
                        content = f.read()
                    self.smart_clipboard.set_clipboard(content)
                    self.console.print(f"[green]Copied content of file '{text}' to clipboard[/green]")
                except Exception as e:
                    self.console.print(f"[red]Error copying file content: {str(e)}[/red]")
            else:
                # Treat as text
                try:
                    self.smart_clipboard.set_clipboard(text)
                    self.console.print(f"[green]Copied text to clipboard: {text}[/green]")
                except Exception as e:
                    self.console.print(f"[red]Error copying text: {str(e)}[/red]")
                    
        elif action == "transform" and len(args) >= 2:
            # Transform the clipboard content
            transform_type = args[1].lower()
            
            try:
                content = self.smart_clipboard.get_clipboard()
                
                if not content:
                    self.console.print("[yellow]Clipboard is empty[/yellow]")
                    return
                    
                if transform_type == "uppercase":
                    result = content.upper()
                elif transform_type == "lowercase":
                    result = content.lower()
                elif transform_type == "capitalize":
                    result = content.capitalize()
                elif transform_type == "reverse":
                    result = content[::-1]
                elif transform_type == "trim":
                    result = content.strip()
                elif transform_type == "count":
                    result = f"Character count: {len(content)}\nWord count: {len(content.split())}\nLine count: {len(content.splitlines())}"
                    self.console.print(result)
                    return
                elif transform_type == "json":
                    # Format as JSON
                    import json
                    try:
                        data = json.loads(content)
                        result = json.dumps(data, indent=2)
                    except:
                        self.console.print("[red]Invalid JSON content[/red]")
                        return
                elif transform_type == "base64":
                    # Encode as base64
                    import base64
                    result = base64.b64encode(content.encode()).decode()
                elif transform_type == "base64decode":
                    # Decode from base64
                    import base64
                    try:
                        result = base64.b64decode(content.encode()).decode()
                    except:
                        self.console.print("[red]Invalid base64 content[/red]")
                        return
                else:
                    self.console.print(f"[red]Unknown transformation: {transform_type}[/red]")
                    return
                    
                # Update clipboard with transformed content
                self.smart_clipboard.set_clipboard(result)
                self.console.print(f"[green]Transformed clipboard content using '{transform_type}'[/green]")
                
                # Show preview
                self.console.print(Panel(result[:200] + ("..." if len(result) > 200 else ""), 
                                      title="Transformed Content", border_style="cyan"))
            except Exception as e:
                self.console.print(f"[red]Error transforming clipboard content: {str(e)}[/red]")
                
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]clipboard[/cyan] - Show clipboard content\n  [cyan]copy [text/file][/cyan] - Copy text or file to clipboard\n  [cyan]transform [operation][/cyan] - Transform clipboard content\n\nAvailable transformations: uppercase, lowercase, capitalize, reverse, trim, count, json, base64, base64decode")

    def handle_voice_command(self, command: str):
        """Handle voice commands"""
        if not command:
            return
            
        self.console.print(f"[cyan]Voice command received:[/cyan] {command}")
        
        # Process common voice commands
        if "open" in command.lower() and ("file" in command.lower() or "folder" in command.lower()):
            # Extract the file/folder name
            parts = command.lower().split("open")
            if len(parts) > 1:
                name = parts[1].strip()
                self.console.print(f"[yellow]Opening {name}...[/yellow]")
                cmd = f"start {name}" if platform.system() == "Windows" else f"open {name}"
                self.execute_command(cmd)
                return
                
        # Process other voice commands as regular commands
        self.console.print(f"[yellow]Processing as regular command:[/yellow] {command}")
        
        # Get AI response for the command
        commands = self.get_ai_response(command)
        
        # Execute the commands
        for cmd in commands:
            result = self.execute_command(cmd)
            self.command_history.append(result)
            
        # Save history if configured
        if self.config["auto_save"]:
            self.save_history()

    def is_dangerous_command(self, command: str) -> bool:
        """Check if a command might be dangerous"""
        dangerous_patterns = [
            "rm -rf",
            "rm -r /",
            "rmdir /s",
            "del /f /s /q",
            "format",
            "mkfs",
            "dd",
            "> /dev/sda",
            ":(){:|:&};:",
            "chmod -R 777 /",
            "mv /* /dev/null",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown",
            "halt",
            "poweroff",
            "reboot",
            "wipe",
            "kill -9",
            "crontab -r",
            # Add more patterns as needed
        ]
        
        # Convert to lowercase for case-insensitive matching
        lower_command = command.lower()
        
        for pattern in dangerous_patterns:
            if pattern.lower() in lower_command:
                return True
                
        return False

    def change_directory(self, path: str):
        """Change the current directory"""
        try:
            # Convert relative paths to absolute
            if not os.path.isabs(path):
                new_path = os.path.join(self.current_directory, path)
            else:
                new_path = path
                
            # Resolve path to handle .. and .
            new_path = os.path.normpath(os.path.abspath(new_path))
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                os.chdir(new_path)
                self.current_directory = new_path
                self.console.print(f"[green]Changed directory to: {self.current_directory}[/green]")
            else:
                self.console.print(f"[red]Directory not found: {new_path}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error changing directory: {str(e)}[/red]")

    def show_help(self):
        """Display help information"""
        self.console.print(Panel.fit(
            "[bold green]Terminal AI Assistant Commands[/bold green]\n"
            "[cyan]help[/cyan] - Show this help message\n"
            "[cyan]exit[/cyan] - Exit the application\n"
            "[cyan]clear[/cyan] - Clear the terminal screen\n"
            "[cyan]history[/cyan] - Show command history\n"
            "[cyan]config[/cyan] - Show current configuration\n"
            "[cyan]cd [path][/cyan] - Change directory\n"
            "[cyan]pwd[/cyan] - Show current directory\n"
            "[cyan]aliases[/cyan] - List all command aliases\n"
            "[cyan]alias add [name] [command][/cyan] - Add a command alias\n"
            "[cyan]alias remove [name][/cyan] - Remove a command alias\n"
            "[cyan]templates[/cyan] - List all command templates\n"
            "[cyan]template add [name] [template][/cyan] - Add a command template\n"
            "[cyan]template remove [name][/cyan] - Remove a command template\n"
            "[cyan]template run [name] [params][/cyan] - Run a command template\n"
            "[cyan]preview [file][/cyan] - Preview the content of a file\n"
            "[cyan]stats[/cyan] - Show system statistics\n"
            "[cyan]backups[/cyan] - List all backups\n"
            "[cyan]backup [file][/cyan] - Backup a file\n"
            "[cyan]restore [backup][/cyan] - Restore a backup\n"
            "[cyan]chain add [name] [commands][/cyan] - Add a command chain\n"
            "[cyan]chain run [name][/cyan] - Run a command chain\n"
            "[cyan]chain list[/cyan] - List all command chains\n"
            "[cyan]clipboard[/cyan] - Show clipboard contents\n"
            "[cyan]copy [text/file][/cyan] - Copy text or file to clipboard\n"
            "[cyan]transform [operation][/cyan] - Transform clipboard content\n"
            "[cyan]voice [on/off][/cyan] - Enable/disable voice commands\n"
            "[cyan]plugins[/cyan] - List all plugins\n"
            "[cyan]plugin enable [name][/cyan] - Enable a plugin\n"
            "[cyan]plugin disable [name][/cyan] - Disable a plugin\n"
            "[cyan]plugin help [name][/cyan] - Show help for a plugin\n"
            "[yellow]For any other tasks, simply describe what you want to do[/yellow]",
            border_style="blue", 
            title="Help"
        ))
        
        # Show plugin commands if any
        if hasattr(self, 'plugin_manager') and self.plugin_manager.plugin_commands:
            plugin_commands = Table(title="Plugin Commands")
            plugin_commands.add_column("Command", style="cyan")
            plugin_commands.add_column("Plugin", style="green")
            
            for cmd_name, cmd_func in self.plugin_manager.plugin_commands.items():
                # Find which plugin provides this command
                plugin_name = "Unknown"
                for name, plugin in self.plugin_manager.plugins.items():
                    if cmd_name in plugin.get_commands():
                        plugin_name = name
                        break
                        
                plugin_commands.add_row(cmd_name, plugin_name)
                
            self.console.print(plugin_commands)

    def handle_plugin_command(self, args: List[str]):
        """Handle plugin management commands"""
        if not hasattr(self, 'plugin_manager'):
            self.console.print("[red]Plugin manager not available[/red]")
            return
            
        if not args:
            # List all plugins
            discovered = self.plugin_manager.discover_plugins()
            loaded = self.plugin_manager.plugins.keys()
            disabled = self.plugin_manager.disabled_plugins
            
            if not discovered:
                self.console.print("[yellow]No plugins found[/yellow]")
                return
                
            table = Table(title="Plugins")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Version", style="blue")
            table.add_column("Description", style="yellow")
            
            for plugin_name in sorted(discovered):
                if plugin_name in loaded:
                    plugin = self.plugin_manager.plugins[plugin_name]
                    status = "[green]Enabled[/green]"
                    version = getattr(plugin, 'version', 'unknown')
                    description = getattr(plugin, 'description', 'No description')
                elif plugin_name in disabled:
                    status = "[yellow]Disabled[/yellow]"
                    version = "?"
                    description = "Plugin is disabled"
                else:
                    status = "[red]Unloaded[/red]"
                    version = "?"
                    description = "Plugin could not be loaded"
                    
                table.add_row(plugin_name, status, version, description)
                
            self.console.print(table)
            
            if self.plugin_manager.plugin_commands:
                self.console.print(f"[green]Available plugin commands: {', '.join(sorted(self.plugin_manager.plugin_commands.keys()))}[/green]")
            
            return
            
        action = args[0].lower()
        
        if action == "enable" and len(args) >= 2:
            plugin_name = args[1]
            
            if plugin_name in self.plugin_manager.plugins:
                self.console.print(f"[yellow]Plugin '{plugin_name}' is already enabled[/yellow]")
                return
                
            result = self.plugin_manager.enable_plugin(plugin_name)
            if result:
                self.console.print(f"[green]Enabled plugin '{plugin_name}'[/green]")
            else:
                self.console.print(f"[red]Failed to enable plugin '{plugin_name}'[/red]")
                
        elif action == "disable" and len(args) >= 2:
            plugin_name = args[1]
            
            if plugin_name not in self.plugin_manager.plugins:
                self.console.print(f"[yellow]Plugin '{plugin_name}' is not enabled[/yellow]")
                return
                
            result = self.plugin_manager.disable_plugin(plugin_name)
            if result:
                self.console.print(f"[green]Disabled plugin '{plugin_name}'[/green]")
            else:
                self.console.print(f"[red]Failed to disable plugin '{plugin_name}'[/red]")
                
        elif action == "help" and len(args) >= 2:
            plugin_name = args[1]
            
            if plugin_name not in self.plugin_manager.plugins:
                self.console.print(f"[red]Plugin '{plugin_name}' is not enabled[/red]")
                return
                
            plugin = self.plugin_manager.plugins[plugin_name]
            help_text = plugin.help()
            
            self.console.print(Panel(help_text, title=f"Plugin: {plugin_name}", border_style="green"))
            
        else:
            self.console.print("[yellow]Usage:[/yellow]\n  [cyan]plugins[/cyan] - List all plugins\n  [cyan]plugin enable [name][/cyan] - Enable a plugin\n  [cyan]plugin disable [name][/cyan] - Disable a plugin\n  [cyan]plugin help [name][/cyan] - Show help for a plugin")

if __name__ == "__main__":
    print("Starting Terminal AI Assistant...")
    assistant = TerminalAIAssistant()
    assistant.run() 