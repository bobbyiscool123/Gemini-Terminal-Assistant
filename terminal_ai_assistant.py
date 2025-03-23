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
        self.console = Console()
        self.session = PromptSession()
        self.command_history: List[Dict] = []
        self.current_directory = os.getcwd()
        print(f"Current directory: {self.current_directory}")
        self.config = self.load_config()
        self.observer = None
        self.setup_signal_handlers()
        print("Initialization complete!")

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
                
                # Try to read a line with a small timeout to allow checking execution time
                output = None
                if process.stdout in select.select([process.stdout], [], [], 0.1)[0]:
                    output = process.stdout.readline()
                
                # Check if process has finished
                if process.poll() is not None and output == '':
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
        
        # Get detailed OS information
        os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        
        if failed_command and error_output:
            # If we're regenerating after a failed command, include the error details
            prompt = f"""You are a terminal command expert. The previous command failed. Please provide a DIFFERENT corrected command.

Previous command that failed: {failed_command}
Error message: {error_output}

Task: {task}
Current directory: {self.current_directory}
Operating System: {os_info}
Platform: {sys.platform}

IMPORTANT: The user is on {os_info}. DO NOT generate the same command again.
For Windows, we need to use commands that work in cmd.exe, not PowerShell.

EXAMPLES of good Windows commands:
- Instead of 'Stop-Process', use 'taskkill /F /IM program.exe'
- Instead of 'Get-ChildItem', use 'dir'
- Instead of 'Get-ComputerInfo', use 'systeminfo'

Return only the corrected command(s), one per line, without any explanations or markdown formatting.
DO NOT return the same command that failed."""
        else:
            # Standard request for new commands
            prompt = f"""You are a terminal command expert. Given the following task, provide a list of commands to execute in sequence.
            Each command should be a single line and should be executable in a terminal.
            
            Task: {task}
            Current directory: {self.current_directory}
            Operating System: {os_info}
            Platform: {sys.platform}
            
            IMPORTANT: The user is on {os_info}. Do NOT generate commands for other operating systems.
            For Windows, use standard cmd.exe commands that will work without PowerShell.
            
            EXAMPLES of good Windows commands:
            - To close a program: 'taskkill /F /IM programname.exe'
            - To list files: 'dir'
            - To get system info: 'systeminfo'
            
            GUIDELINES FOR GIT COMMANDS:
            - Always include a message with git commit: 'git commit -m "Your message here"'
            - For git commands that might open an editor, add appropriate flags to prevent it
            - Example: 'git pull --no-edit' instead of just 'git pull'
            
            Return only the commands, one per line, without any explanations or markdown formatting."""

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

        while True:
            try:
                task = self.session.prompt(
                    "\nWhat would you like me to do? ",
                    style=self.get_prompt_style()
                )

                if task.lower() in ['exit', 'quit']:
                    break
                elif task.lower() == 'help':
                    self.show_help()
                    continue

                with Progress() as progress:
                    task_progress = progress.add_task("[cyan]Processing...", total=None)
                    
                    commands = self.get_ai_response(task)
                    
                    for i, command in enumerate(commands, 1):
                        progress.update(task_progress, description=f"[cyan]Executing command {i}/{len(commands)}")

                        if self.config["confirm_dangerous"] and self.is_dangerous_command(command):
                            if not Prompt.ask("This command might be dangerous. Continue? (y/n)").lower() == 'y':
                                continue

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
                            self.display_command_result(result)
                        
                        # Add to history if we have a result
                        if result:
                            self.command_history.append(result)
                            
                            # Check if command failed
                            if result.get("exit_code", 0) != 0:
                                print(f"{Fore.YELLOW}Command failed. Asking AI for an alternative command...{Style.RESET_ALL}")
                                
                                # Get alternative command from AI
                                alternative_commands = self.get_ai_response(
                                    task,
                                    failed_command=command,
                                    error_output=result.get("stderr", "Unknown error")
                                )
                                
                                if alternative_commands:
                                    alt_command = alternative_commands[0]
                                    print(f"{Fore.GREEN}Trying alternative command: {alt_command}{Style.RESET_ALL}")
                                    
                                    # Execute alternative command
                                    if self.config["stream_output"]:
                                        for output in self.stream_command_output(alt_command):
                                            pass
                                    else:
                                        alt_result = self.execute_command(alt_command)
                                        self.display_command_result(alt_result)
                                        self.command_history.append(alt_result)
                                else:
                                    print(f"{Fore.RED}Could not find an alternative command. Please try a different approach.{Style.RESET_ALL}")

                self.save_history()

            except KeyboardInterrupt:
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

    def is_dangerous_command(self, command: str) -> bool:
        """Check if a command might be dangerous"""
        dangerous_patterns = [
            'rm -rf',
            'mkfs',
            'dd',
            'chmod',
            'chown',
            'sudo',
            '> /dev/sda',
            'mkfs.ext4',
            'dd if=',
            'rm -rf /'
        ]
        return any(pattern in command.lower() for pattern in dangerous_patterns)

    def show_help(self):
        """Display help information"""
        help_text = """
        Available Commands:
        - help: Show this help message
        - exit/quit: Exit the program
        - clear: Clear the screen
        - history: Show command history
        - config: Show current configuration
        - cd: Change directory
        - pwd: Show current directory
        """
        self.console.print(Panel(help_text, title="Help", border_style="blue"))

if __name__ == "__main__":
    print("Starting Terminal AI Assistant...")
    assistant = TerminalAIAssistant()
    assistant.run() 