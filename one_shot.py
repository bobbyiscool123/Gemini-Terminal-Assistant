#!/usr/bin/env python3
"""
One-shot script for Gemini Terminal Assistant
Handles async operations properly
"""
import os
import sys
import asyncio
import signal
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Initialize Rich console
console = Console()

# Global flag for task cancellation
task_cancelled = False

def check_shebang():
    """Check if the script has a valid shebang line"""
    try:
        with open(__file__, 'r') as f:
            first_line = f.readline().strip()
            if not first_line.startswith('#!/usr/bin/env python3'):
                console.print("[yellow]Warning: Script may not have a valid shebang line[/yellow]")
                return False
    except Exception as e:
        console.print(f"[yellow]Warning: Could not check shebang line: {str(e)}[/yellow]")
        return False
    return True

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global task_cancelled
    if not task_cancelled:
        console.print("\n[yellow]⚠️  Task cancellation requested. Cleaning up...[/yellow]")
        task_cancelled = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_environment():
    """Check if all required environment variables and files are present"""
    # Check shebang first
    if not check_shebang():
        console.print("[yellow]Note: Script may not be executable from command line[/yellow]")
    
    # Check required files
    required_files = [".env", "agent_terminal.py"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        console.print(f"[red]Error: Missing required files: {', '.join(missing_files)}[/red]")
        return False
    
    # Check for required environment variables
    load_dotenv()
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        console.print(f"[red]Error: Missing required environment variables: {', '.join(missing_vars)}[/red]")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        console.print(f"[red]Error: Python 3.8 or higher is required. Current version: {sys.version}[/red]")
        return False
    
    return True

# Check if task is provided
if len(sys.argv) < 2:
    console.print("[red]Error: No task provided[/red]")
    console.print("Usage: python one_shot.py <task>")
    console.print("Example: python one_shot.py 'list files in current directory'")
    sys.exit(1)

# Get the task from command line arguments
task = " ".join(sys.argv[1:])

# Check environment before proceeding
if not check_environment():
    sys.exit(1)

# Import the necessary classes
try:
    from agent_terminal import TerminalAgent
except ImportError as e:
    console.print(f"[red]Error: Could not import TerminalAgent: {str(e)}[/red]")
    console.print("Make sure you're in the correct directory and all dependencies are installed.")
    sys.exit(1)

# Run the agent with the task
async def run_one_shot():
    start_time = datetime.now()
    agent = TerminalAgent()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        # Initialize task
        init_task = progress.add_task("[cyan]Initializing Terminal Assistant...", total=None)
        
        try:
            await agent.initialize()
            progress.update(init_task, completed=True)
            
            # Process task
            process_task = progress.add_task(f"[green]Processing task: {task}", total=None)
            
            if task_cancelled:
                progress.update(process_task, description="[yellow]Task cancelled by user")
                return 1
            
            result = await agent.process_task(task, one_shot=True)
            
            if task_cancelled:
                progress.update(process_task, description="[yellow]Task cancelled by user")
                return 1
            
            progress.update(process_task, completed=True)
            
            # Display success message
            duration = datetime.now() - start_time
            console.print(f"\n[green]✅ Task completed successfully in {duration.total_seconds():.2f} seconds![/green]")
            
        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/red]")
            import traceback
            console.print(traceback.format_exc())
            return 1
        
        finally:
            # Clean up
            cleanup_task = progress.add_task("[cyan]Cleaning up...", total=None)
            await agent.cleanup()
            progress.update(cleanup_task, completed=True)
            
            return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(run_one_shot()))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Process interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Fatal error: {str(e)}[/red]")
        sys.exit(1) 