#!/usr/bin/env python3
"""
Setup script for Gemini Terminal Assistant
For Termux/PRoot-Distro/Ubuntu environments
"""
import os
import sys
import subprocess
import platform
import shutil
import re
from pathlib import Path

def print_color(text, color="green"):
    """Print colored text in terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, colors['green'])}{text}{colors['end']}")

def run_command(command, shell=False):
    """Run a command and return its output"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        result = subprocess.run(command, capture_output=True, text=True, shell=shell)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def check_python_version():
    """Check if Python version is suitable"""
    version = platform.python_version()
    print_color(f"Detected Python version: {version}", "blue")
    
    major, minor, patch = map(int, version.split("."))
    if major != 3 or minor < 7:
        print_color("Warning: Recommended Python version is 3.7 or newer", "yellow")
        return False
    
    print_color(f"Python version {version} is suitable", "green")
    return True

def check_conda():
    """Check if conda is installed"""
    success, output = run_command("conda --version")
    if success:
        print_color(f"Conda is installed: {output.strip()}", "green")
        return True
    else:
        print_color("Conda is not installed", "yellow")
        return False

def is_in_virtualenv():
    """Check if running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_conda_env_exists(env_name):
    """Check if a conda environment exists"""
    success, output = run_command("conda env list", shell=True)
    if success:
        return env_name in output
    return False

def check_python_version_in_conda_env(env_name, version):
    """Check Python version in a conda environment"""
    success, output = run_command(f"conda run -n {env_name} python --version", shell=True)
    if success:
        return version in output
    return False

def install_conda():
    """Install Miniforge (conda) if not present"""
    print_color("Installing Miniforge (conda)...", "blue")
    
    # Create a temporary directory for downloading
    tmp_dir = Path("/tmp/miniforge_install")
    tmp_dir.mkdir(exist_ok=True)
    
    # Download the installer
    installer_path = tmp_dir / "Miniforge3-Linux-aarch64.sh"
    download_url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
    
    print_color(f"Downloading Miniforge from {download_url}...", "blue")
    success, _ = run_command(f"wget {download_url} -O {installer_path}", shell=True)
    if not success:
        print_color("Failed to download Miniforge installer", "red")
        return False
    
    # Make it executable
    os.chmod(installer_path, 0o755)
    
    # Run the installer
    home_dir = os.path.expanduser("~")
    install_path = os.path.join(home_dir, ".local", "miniforge3")
    print_color(f"Installing Miniforge to {install_path}...", "blue")
    
    success, _ = run_command(f"bash {installer_path} -b -p {install_path}", shell=True)
    if not success:
        print_color("Failed to install Miniforge", "red")
        return False
    
    # Update PATH in bashrc
    bashrc_path = os.path.join(home_dir, ".bashrc")
    
    # Check if path is already in bashrc
    with open(bashrc_path, "r") as f:
        content = f.read()
    
    conda_path = f'export PATH="{install_path}/bin:$PATH"'
    if conda_path not in content:
        print_color("Adding Miniforge to PATH in .bashrc...", "blue")
        with open(bashrc_path, "a") as f:
            f.write(f"\n# Added by Gemini Terminal Assistant setup\n{conda_path}\n")
    
    # Initialize conda
    print_color("Initializing conda...", "blue")
    success, _ = run_command(f"{install_path}/bin/conda init bash", shell=True)
    if not success:
        print_color("Failed to initialize conda", "red")
        return False
    
    print_color("Conda installation completed!", "green")
    print_color("Please restart your shell or run 'source ~/.bashrc' to use conda", "yellow")
    
    return install_path

def install_python(conda_path):
    """Install Python 3.7+ using conda"""
    env_name = "py3_compatible"
    
    # Check if environment already exists
    if check_conda_env_exists(env_name):
        print_color(f"Conda environment '{env_name}' already exists", "blue")
        
        # Check if it has a compatible Python version
        success, output = run_command(f"conda run -n {env_name} python --version", shell=True)
        if success:
            version_match = re.search(r"Python (\d+\.\d+\.\d+)", output)
            if version_match:
                version = version_match.group(1)
                major, minor, _ = map(int, version.split('.'))
                if major == 3 and minor >= 7:
                    print_color(f"Python {version} is already installed in conda environment '{env_name}'", "green")
                    return env_name
            
        print_color(f"Environment '{env_name}' exists but doesn't have a compatible Python version", "yellow")
        # Ask user if they want to update or recreate
        while True:
            choice = input(f"Update environment '{env_name}' to a compatible Python version? (y/n): ").lower().strip()
            if choice in ["y", "yes"]:
                break
            elif choice in ["n", "no"]:
                print_color(f"Skipping Python installation", "yellow")
                return env_name
            print_color("Please enter 'y' or 'n'", "yellow")
    
    print_color("Installing Python 3.7+ using conda...", "blue")
    
    conda_bin = os.path.join(conda_path, "bin", "conda") if conda_path else "conda"
    
    # Create a new environment with Python 3.7+
    success, _ = run_command(f"{conda_bin} create -n {env_name} python=3.7 -y", shell=True)
    if not success:
        print_color("Failed to create conda environment", "red")
        return False
    
    print_color(f"Python 3.7+ installed in conda environment '{env_name}'", "green")
    return env_name

def setup_virtualenv(conda_path, env_name):
    """Set up a virtual environment for the project"""
    print_color("Setting up virtual environment...", "blue")
    
    # Check if we're already in a virtual environment
    if is_in_virtualenv():
        print_color("Already running in a virtual environment", "yellow")
        
        # Verify Python version in this venv
        version = platform.python_version()
        major, minor, _ = map(int, version.split('.'))
        if major == 3 and minor >= 7:
            print_color(f"Current virtual environment has Python {version}", "green")
            print_color("Using current virtual environment", "green")
            return True
        else:
            print_color(f"Current virtual environment has Python {version}, not 3.7+", "red")
            print_color("Please deactivate the current virtual environment and try again", "red")
            return False
    
    # Check if virtual environment already exists
    venv_path = "venv"
    if os.path.exists(venv_path):
        # Check if the venv has the right Python version
        venv_python = os.path.join(venv_path, "bin", "python")
        success, output = run_command(f"{venv_python} --version", shell=True)
        if success:
            version_match = re.search(r"Python (\d+\.\d+\.\d+)", output)
            if version_match:
                version = version_match.group(1)
                major, minor, _ = map(int, version.split('.'))
                if major == 3 and minor >= 7:
                    print_color(f"Virtual environment already exists with Python {version}", "green")
                    
                    # Ask if user wants to recreate it
                    while True:
                        choice = input("Recreate virtual environment? (y/n): ").lower().strip()
                        if choice in ["y", "yes"]:
                            print_color(f"Removing existing virtual environment at {venv_path}...", "yellow")
                            shutil.rmtree(venv_path)
                            break
                        elif choice in ["n", "no"]:
                            print_color("Using existing virtual environment", "green")
                            return True
                        print_color("Please enter 'y' or 'n'", "yellow")
                else:
                    print_color(f"Existing virtual environment has wrong Python version. Recreating...", "yellow")
                    shutil.rmtree(venv_path)
        else:
            print_color(f"Existing virtual environment has wrong Python version. Recreating...", "yellow")
            shutil.rmtree(venv_path)
    
    # Activate conda environment
    conda_bin = os.path.join(conda_path, "bin", "conda") if conda_path else "conda"
    
    # Get the Python path from the conda environment
    success, output = run_command(f"{conda_bin} run -n {env_name} which python", shell=True)
    if not success:
        print_color("Failed to find Python in conda environment", "red")
        return False
    
    python_path = output.strip()
    
    # Create a virtual environment
    print_color(f"Creating virtual environment at {venv_path} using {python_path}...", "blue")
    success, _ = run_command(f"{python_path} -m venv {venv_path}", shell=True)
    if not success:
        print_color("Failed to create virtual environment", "red")
        return False
    
    # Install requirements
    venv_pip = os.path.join(venv_path, "bin", "pip")
    print_color("Installing dependencies...", "blue")
    success, _ = run_command(f"{venv_pip} install --prefer-binary -r requirements.txt", shell=True)
    if not success:
        print_color("Failed to install dependencies", "red")
        return False
    
    print_color("Virtual environment setup completed!", "green")
    return True

def create_terminal_assistant_script():
    """Create the terminal-assistant.sh script"""
    print_color("Setting up command-line wrapper...", "blue")
    
    # Get the absolute path of the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create terminal-assistant.sh script
    script_path = os.path.join(script_dir, "terminal-assistant.sh")
    
    # Check if the script already exists
    if os.path.exists(script_path):
        print_color(f"Terminal assistant script already exists at {script_path}", "yellow")
        
        # Check if it needs updating (check if the path is correct)
        with open(script_path, "r") as f:
            content = f.read()
        
        if f'ASSISTANT_DIR="{script_dir}"' in content:
            print_color("Terminal assistant script is up to date", "green")
            return script_path
        else:
            print_color("Terminal assistant script needs updating", "yellow")
    else:
        print_color(f"Creating terminal-assistant.sh at {script_path}...", "blue")
    
    script_content = """#!/bin/bash
# terminal-assistant.sh - One-shot command for Gemini Terminal Assistant
# Usage: terminal-assistant <task description>

# Check if a task was provided
if [ $# -eq 0 ]; then
  echo "Usage: terminal-assistant <task description>"
  echo "Example: terminal-assistant \\"install nodejs\\""
  exit 1
fi

# Save the current directory
CURRENT_DIR=$(pwd)

# Path to the Gemini Terminal Assistant installation
# This should be changed to match your actual installation path
ASSISTANT_DIR="{script_dir}"

# Construct the task from all arguments
TASK="$*"

# Check if the assistant directory exists
if [ ! -d "$ASSISTANT_DIR" ]; then
  echo "Error: Terminal Assistant not found at $ASSISTANT_DIR"
  echo "Please update ASSISTANT_DIR in this script to point to your installation"
  exit 1
fi

# Navigate to the assistant directory
cd "$ASSISTANT_DIR"

# Check if virtual environment exists
if [ ! -d "$ASSISTANT_DIR/venv" ]; then
  echo "Error: Virtual environment not found. Please run setup.py first."
  cd "$CURRENT_DIR"
  exit 1
fi

# Check if .env file with API key exists
if [ ! -f "$ASSISTANT_DIR/.env" ]; then
  echo "Error: .env file with GOOGLE_API_KEY not found."
  echo "Please create a .env file with your Google API key."
  cd "$CURRENT_DIR"
  exit 1
fi

# Activate the virtual environment and run the one-shot command
echo "Running task: $TASK"
echo "Working directory: $CURRENT_DIR"
echo "--------------------------------------------"

# Source the virtual environment and run the task in one-shot mode
source "$ASSISTANT_DIR/venv/bin/activate" && \\
CURRENT_WORKING_DIR="$CURRENT_DIR" python -c "
import os
import sys
import asyncio
from dotenv import load_dotenv

# Set working directory for the assistant
os.environ['CURRENT_WORKING_DIR'] = os.environ.get('CURRENT_WORKING_DIR', '.')

# Import assistant modules
try:
    load_dotenv()
    sys.path.append('$ASSISTANT_DIR')
    from agent_terminal import TerminalAgent
except ImportError as e:
    print(f'Error loading Terminal Assistant: {{e}}')
    sys.exit(1)

# Run the assistant with the task
async def run_one_shot():
    agent = TerminalAgent(initial_directory=os.environ.get('CURRENT_WORKING_DIR'))
    await agent.initialize()
    print('\\n🤖 Terminal Assistant: Working on your task...\\n')
    result = await agent.process_task('$TASK', one_shot=True)
    print('\\n✅ Task completed:\\n', result)
    await agent.cleanup()

# Run in one-shot mode
if __name__ == '__main__':
    asyncio.run(run_one_shot())
"

# Return to the original directory
cd "$CURRENT_DIR"
""".format(script_dir=script_dir)
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod(script_path, 0o755)
    print_color("Created executable terminal-assistant.sh script", "green")
    
    return script_path

def install_terminal_assistant_command(script_path):
    """Install the terminal-assistant command"""
    print_color("Installing terminal-assistant command...", "blue")
    
    home_dir = os.path.expanduser("~")
    bashrc_path = os.path.join(home_dir, ".bashrc")
    
    # Check if command is already installed in /usr/local/bin
    symlink_path = "/usr/local/bin/terminal-assistant"
    if os.path.exists(symlink_path):
        link_target = os.path.realpath(symlink_path)
        if link_target == script_path:
            print_color("✅ Terminal-assistant command already installed via symlink", "green")
            return True
        else:
            print_color(f"Symlink exists but points to {link_target} instead of {script_path}", "yellow")
            print_color("Attempting to update symlink...", "blue")
    
    # Try to create symlink in /usr/local/bin first
    print_color("Attempting to create symlink in /usr/local/bin...", "blue")
    try:
        success, _ = run_command(f"sudo ln -sf {script_path} /usr/local/bin/terminal-assistant", shell=True)
        if success:
            print_color("✅ Symlink created successfully in /usr/local/bin", "green")
            return True
    except:
        pass
    
    # Check if alias already exists in .bashrc
    if os.path.exists(bashrc_path):
        with open(bashrc_path, "r") as f:
            content = f.read()
        
        alias_line = f"alias terminal-assistant='{script_path}'"
        
        # Check if the exact alias already exists
        if alias_line in content:
            print_color("✅ Terminal-assistant command already installed via .bashrc alias", "green")
            return True
        # Check if any terminal-assistant alias exists
        elif "alias terminal-assistant=" in content:
            print_color("Terminal-assistant alias exists but needs updating", "yellow")
            
            # Fall back to .bashrc method (update existing alias)
            print_color("Updating terminal-assistant alias in .bashrc...", "blue")
            
            with open(bashrc_path, "r") as f:
                lines = f.readlines()
            
            with open(bashrc_path, "w") as f:
                for line in lines:
                    if "alias terminal-assistant=" in line:
                        f.write(f"{alias_line}\n")
                    else:
                        f.write(line)
            
            print_color("✅ Updated terminal-assistant alias in .bashrc", "green")
            print_color("Please run 'source ~/.bashrc' or restart your terminal to apply changes", "yellow")
            return True
    
    # Add new alias
    print_color("Adding terminal-assistant alias to .bashrc...", "blue")
    with open(bashrc_path, "a") as f:
        f.write(f"\n# Terminal Assistant command\n{alias_line}\n")
    
    print_color("✅ Added terminal-assistant command to .bashrc", "green")
    print_color("Please run 'source ~/.bashrc' or restart your terminal to use the command", "yellow")
    
    return True

def get_user_confirmation(prompt):
    """Get user confirmation (y/n)"""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        print_color("Please enter 'y' or 'n'", "yellow")

def main():
    """Main setup function"""
    print_color("Gemini Terminal Assistant Setup for Termux/PRoot-Distro", "cyan")
    print_color("=" * 60, "cyan")
    
    # Check if running on Linux
    if platform.system() != "Linux":
        print_color("This setup script is intended for Linux systems only.", "red")
        sys.exit(1)
    
    # Check Python version
    check_python_version()
    
    # Check if already in a virtual environment
    if is_in_virtualenv():
        print_color("Running in a virtual environment", "yellow")
        print_color("Your current Python version is: " + platform.python_version(), "blue")
        
        version = platform.python_version()
        major, minor, _ = map(int, version.split('.'))
        if not (major == 3 and minor >= 7):
            print_color("Warning: Current virtual environment does not have Python 3.7+", "red")
            print_color("It is recommended to deactivate this virtual environment first.", "red")
            if not get_user_confirmation("Continue anyway?"):
                print_color("Setup cancelled", "yellow")
                sys.exit(0)
        else:
            print_color("Your virtual environment is using Python 3.7+, which is suitable.", "green")
            
            # Skip conda setup
            conda_path = None
            env_name = None
            
            # Create and install terminal-assistant command
            script_path = create_terminal_assistant_script()
            if script_path:
                install_terminal_assistant_command(script_path)
            
            # Check if requirements are installed
            print_color("Checking if requirements are installed...", "blue")
            success, _ = run_command("pip list")
            if success:
                print_color("✅ Dependencies installed", "green")
            else:
                print_color("Installing dependencies...", "blue")
                success, _ = run_command("pip install --prefer-binary -r requirements.txt", shell=True)
                if success:
                    print_color("✅ Dependencies installed successfully", "green")
                else:
                    print_color("❌ Failed to install dependencies", "red")
            
            print_color("\nSetup completed!", "green")
            print_color("\nTo run Gemini Terminal Assistant:", "cyan")
            print_color("1. Create a .env file with your Google API key:", "cyan")
            print_color("   echo 'GOOGLE_API_KEY=your_key_here' > .env", "yellow")
            print_color("2. Run the assistant:", "cyan")
            print_color("   python run_agent.py", "yellow")
            print_color("\nOr use the command-line wrapper from anywhere:", "cyan")
            print_color("   terminal-assistant \"your task here\"", "yellow")
            
            return 0
    
    # Check for conda
    if check_conda():
        conda_path = None  # Use system conda
    else:
        # Install conda
        print_color("Conda not found. Installing...", "yellow")
        conda_path = install_conda()
        if not conda_path:
            print_color("Failed to install conda. Please install it manually.", "red")
            sys.exit(1)
    
    # Install Python 3.7+
    env_name = install_python(conda_path)
    if not env_name:
        print_color("Failed to install Python 3.7+. Please install it manually.", "red")
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtualenv(conda_path, env_name):
        print_color("Failed to set up virtual environment. Please set it up manually.", "red")
        sys.exit(1)
    
    # Create and install terminal-assistant command
    script_path = create_terminal_assistant_script()
    if script_path:
        install_terminal_assistant_command(script_path)
    
    print_color("\nSetup completed successfully!", "green")
    print_color("\nTo run Gemini Terminal Assistant:", "cyan")
    print_color("1. Activate the virtual environment:", "cyan")
    print_color("   source venv/bin/activate", "yellow")
    print_color("2. Create a .env file with your Google API key:", "cyan")
    print_color("   echo 'GOOGLE_API_KEY=your_key_here' > .env", "yellow")
    print_color("3. Run the assistant:", "cyan")
    print_color("   python run_agent.py", "yellow")
    print_color("\nOr use the command-line wrapper from anywhere:", "cyan")
    print_color("   terminal-assistant \"your task here\"", "yellow")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
