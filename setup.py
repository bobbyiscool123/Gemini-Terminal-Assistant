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
    if major != 3 or minor < 8:
        print_color("Warning: Recommended Python version is 3.8 or newer", "yellow")
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

def install_python_3_12_8(conda_path):
    """Install Python 3.12.8 using conda"""
    print_color("Installing Python 3.12.8 using conda...", "blue")
    
    conda_bin = os.path.join(conda_path, "bin", "conda") if conda_path else "conda"
    
    # Create a new environment with Python 3.12.8
    env_name = "py3128"
    success, _ = run_command(f"{conda_bin} create -n {env_name} python=3.12.8 -y", shell=True)
    if not success:
        print_color("Failed to create conda environment", "red")
        return False
    
    print_color(f"Python 3.12.8 installed in conda environment '{env_name}'", "green")
    return env_name

def setup_virtualenv(conda_path, env_name):
    """Set up a virtual environment for the project"""
    print_color("Setting up virtual environment...", "blue")
    
    # Activate conda environment
    conda_bin = os.path.join(conda_path, "bin", "conda") if conda_path else "conda"
    
    # Get the Python path from the conda environment
    success, output = run_command(f"{conda_bin} run -n {env_name} which python", shell=True)
    if not success:
        print_color("Failed to find Python in conda environment", "red")
        return False
    
    python_path = output.strip()
    
    # Create a virtual environment
    venv_path = "venv"
    if os.path.exists(venv_path):
        print_color(f"Removing existing virtual environment at {venv_path}...", "yellow")
        shutil.rmtree(venv_path)
    
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
    
    # Install Python 3.12.8
    env_name = install_python_3_12_8(conda_path)
    if not env_name:
        print_color("Failed to install Python 3.12.8. Please install it manually.", "red")
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtualenv(conda_path, env_name):
        print_color("Failed to set up virtual environment. Please set it up manually.", "red")
        sys.exit(1)
    
    print_color("\nSetup completed successfully!", "green")
    print_color("\nTo run Gemini Terminal Assistant:", "cyan")
    print_color("1. Activate the virtual environment:", "cyan")
    print_color("   source venv/bin/activate", "yellow")
    print_color("2. Create a .env file with your Google API key:", "cyan")
    print_color("   echo 'GOOGLE_API_KEY=your_key_here' > .env", "yellow")
    print_color("3. Run the assistant:", "cyan")
    print_color("   python run_agent.py", "yellow")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
