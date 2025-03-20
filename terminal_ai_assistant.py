import os
import sys
import json
import yaml
import time
import signal
import subprocess
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
from colorama import Fore

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
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=self.config["timeout"])
            end_time = time.time()
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
            return {
                "command": command,
                "error": "Command timed out",
                "exit_code": -1,
                "execution_time": self.config["timeout"],
                "timestamp": datetime.now().isoformat()
            }

    def stream_command_output(self, command: str):
        """Stream command output in real-time"""
        print(f"Streaming output for command: {command}")
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.console.print(output.strip())
                yield output.strip()

        return_code = process.poll()
        if return_code != 0:
            self.console.print(f"[red]Command failed with return code {return_code}[/red]")

    def get_ai_response(self, task: str) -> List[str]:
        """Get AI response for the given task"""
        print(f"Getting AI response for task: {task}")
        prompt = f"""You are a terminal command expert. Given the following task, provide a list of commands to execute in sequence.
        Each command should be a single line and should be executable in a terminal.
        Task: {task}
        Current directory: {self.current_directory}
        Return only the commands, one per line, without any explanations or markdown formatting."""

        response = model.generate_content(prompt)
        return [cmd.strip() for cmd in response.text.split('\n') if cmd.strip()]

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

                        if self.config["stream_output"]:
                            for output in self.stream_command_output(command):
                                pass
                        else:
                            result = self.execute_command(command)
                            self.display_command_result(result)
                            self.command_history.append(result)

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