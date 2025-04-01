#!/usr/bin/env python3
"""
Setup script for AI Terminal Assistant
Creates a virtual environment, installs required dependencies,
and makes the assistant globally accessible
"""
import os
import sys
import subprocess
import platform
import venv
from pathlib import Path
import site

# Get script's directory (app base directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_header(message):
    """Print a formatted header message"""
    print("\n" + "="*50)
    print(f" {message}")
    print("="*50 + "\n")

def create_venv():
    """Create a virtual environment for the application"""
    print("Setting up virtual environment...")
    venv_dir = os.path.join(BASE_DIR, "venv")
    
    # Check if venv already exists
    if os.path.exists(venv_dir):
        print(f"Virtual environment found at {venv_dir}")
        return venv_dir
    
    print(f"Creating new virtual environment...")
    venv.create(venv_dir, with_pip=True)
    print("Virtual environment created successfully!")
    
    return venv_dir

def find_pip_path(venv_dir):
    """Find the correct pip executable path within the virtual environment"""
    potential_paths = []
    
    if platform.system() == "Windows":
        potential_paths = [
            os.path.join(venv_dir, "Scripts", "pip.exe"),
            os.path.join(venv_dir, "Scripts", "pip3.exe"),
            os.path.join(venv_dir, "bin", "pip.exe"),
            os.path.join(venv_dir, "bin", "pip3.exe"),
            os.path.join(venv_dir, "Scripts", "python.exe"),  # Fall back to using python -m pip
        ]
    else:
        potential_paths = [
            os.path.join(venv_dir, "bin", "pip"),
            os.path.join(venv_dir, "bin", "pip3"),
            os.path.join(venv_dir, "bin", "python"),  # Fall back to using python -m pip
        ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found pip at: {path}")
            return path
    
    print("Could not find pip in the virtual environment")
    return None

def install_requirements(venv_dir):
    """Install required dependencies in the virtual environment"""
    print("Installing required dependencies...")
    
    # Find pip path
    pip_path = find_pip_path(venv_dir)
    if not pip_path:
        print("Could not find pip in the virtual environment")
        print("Attempting to install with system Python instead")
        return install_with_system_python()
    
    # Check if requirements.txt exists
    requirements_path = os.path.join(BASE_DIR, "requirements.txt")
    if not os.path.exists(requirements_path):
        print("requirements.txt not found!")
        return False
    
    try:
        # If we found python.exe instead of pip.exe, use python -m pip
        if pip_path.endswith("python.exe") or pip_path.endswith("python"):
            subprocess.check_call([pip_path, "-m", "pip", "install", "-r", requirements_path])
        else:
            subprocess.check_call([pip_path, "install", "-r", requirements_path])
        print("Dependencies installed successfully!")
        return True
    except subprocess.SubprocessError:
        print("Could not install dependencies with virtual environment")
        print("Trying alternative installation method...")
        
        try:
            venv_activate = os.path.join(venv_dir, "Scripts", "activate.bat") if platform.system() == "Windows" else os.path.join(venv_dir, "bin", "activate")
            
            if platform.system() == "Windows":
                cmd = f'"{venv_activate}" && pip install -r "{requirements_path}"'
                subprocess.check_call(cmd, shell=True)
            else:
                cmd = f'. "{venv_activate}" && pip install -r "{requirements_path}"'
                subprocess.check_call(cmd, shell=True)
                
            print("Dependencies installed successfully via alternative method!")
            return True
        except subprocess.SubprocessError:
            print("Alternative installation also failed")
            return install_with_system_python()

def install_with_system_python():
    """Install dependencies using the system Python as a fallback"""
    print("Attempting to install dependencies with system Python...")
    requirements_path = os.path.join(BASE_DIR, "requirements.txt")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Dependencies installed successfully with system Python!")
        return True
    except subprocess.SubprocessError:
        print("Failed to install dependencies")
        print("Try running: python -m pip install -r requirements.txt")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        print("Creating .env file template...")
        with open(env_path, 'w') as f:
            f.write("GOOGLE_API_KEY=your_api_key_here\n")
        print("Created .env file. Please edit it with your Gemini API key.")
    else:
        print(".env file already exists")

def add_to_system_path():
    """Add the application directory to the system PATH"""
    if platform.system() != "Windows":
        print("PATH modification is only supported on Windows")
        return False
    
    print("Adding application directory to system PATH...")
    
    try:
        # First try using setx (traditional method)
        cmd = f'setx PATH "%PATH%;{BASE_DIR}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Successfully added to user PATH using setx")
            return True
        else:
            print("Setx command failed, trying PowerShell method instead")
            
            # Fall back to PowerShell method
            ps_cmd = f'powershell -Command "[Environment]::SetEnvironmentVariable(\'Path\', [Environment]::GetEnvironmentVariable(\'Path\', \'User\') + \';{BASE_DIR}\', [EnvironmentVariableTarget]::User)"'
            ps_result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
            
            if ps_result.returncode == 0:
                print("Successfully added to user PATH using PowerShell")
                return True
            else:
                print("Failed to add to PATH using PowerShell")
                print(f"Error: {ps_result.stderr}")
                return False
    except Exception as e:
        print(f"Error modifying PATH: {e}")
        return False

def create_batch_file():
    """Create the terminal-assistant.bat file"""
    print("Creating batch launcher...")
    bat_path = os.path.join(BASE_DIR, "terminal-assistant.bat")
    
    with open(bat_path, 'w') as f:
        f.write('@echo off\n')
        f.write('setlocal enabledelayedexpansion\n\n')
        
        f.write(':: Get the directory where the batch file is located\n')
        f.write('set "SCRIPT_DIR=%~dp0"\n')
        f.write('set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"\n')
        f.write('set "AGENT_SCRIPT=%SCRIPT_DIR%\\run_agent.py"\n\n')
        
        f.write(':: Check if Python is installed\n')
        f.write('python --version >nul 2>&1\n')
        f.write('if errorlevel 1 (\n')
        f.write('    echo Python is not installed or not in PATH.\n')
        f.write('    echo Please install Python 3.8 or higher.\n')
        f.write('    pause\n')
        f.write('    exit /b 1\n')
        f.write(')\n\n')
        
        f.write(':: Check if .env file exists\n')
        f.write('if not exist "%SCRIPT_DIR%\\.env" (\n')
        f.write('    echo Creating .env file template...\n')
        f.write('    echo GOOGLE_API_KEY=your_api_key_here > "%SCRIPT_DIR%\\.env"\n')
        f.write('    echo Please edit the .env file with your Gemini API key.\n')
        f.write('    pause\n')
        f.write('    exit /b 1\n')
        f.write(')\n\n')
        
        f.write(':: Check for requirements\n')
        f.write('if not exist "%SCRIPT_DIR%\\venv" (\n')
        f.write('    echo Setting up environment...\n')
        f.write('    cd /d "%SCRIPT_DIR%"\n')
        f.write('    python -m venv venv\n')
        f.write('    call "%SCRIPT_DIR%\\venv\\Scripts\\activate.bat"\n')
        f.write('    pip install -r requirements.txt\n')
        f.write(') else (\n')
        f.write('    call "%SCRIPT_DIR%\\venv\\Scripts\\activate.bat"\n')
        f.write(')\n\n')
        
        f.write(':: Run the agent with all passed arguments\n')
        f.write('cd /d "%SCRIPT_DIR%"\n\n')
        
        f.write(':: Check if there are any command line arguments\n')
        f.write('if "%~1"=="" (\n')
        f.write('    :: No arguments - run in interactive mode\n')
        f.write('    python "%AGENT_SCRIPT%"\n')
        f.write(') else (\n')
        f.write('    :: Arguments provided - pass them directly\n')
        f.write('    python "%AGENT_SCRIPT%" %*\n')
        f.write(')\n\n')
        
        f.write(':: Deactivate the virtual environment\n')
        f.write('call deactivate\n\n')
        
        f.write('exit /b 0\n')
    
    print(f"Created batch file at {bat_path}")
    return True

def main():
    """Main entry point"""
    print_header("AI Terminal Assistant Setup")
    
    # Create .env file if needed
    create_env_file()
    
    # Create the batch launcher
    create_batch_file()
    
    # Create virtual environment
    venv_dir = create_venv()
    
    # Install requirements
    if not install_requirements(venv_dir):
        print("Setup encountered an issue with dependencies")
        print("You can still try running the assistant with system Python")
    
    # Add the directory to system PATH
    if platform.system() == "Windows":
        path_added = add_to_system_path()
        if path_added:
            print("Directory added to PATH. You can now run 'terminal-assistant' from any command prompt.")
            print("You may need to restart your command prompt for the changes to take effect.")
        else:
            print("Could not add directory to PATH automatically.")
            print(f"To add it manually, run: setx PATH \"%PATH%;{BASE_DIR}\"")
    else:
        # Guidance for Unix-based systems
        print("\nTo make terminal-assistant available from anywhere on Unix-based systems:")
        print(f"1. Add the following line to your ~/.bashrc or ~/.zshrc:")
        print(f"   export PATH=\"$PATH:{BASE_DIR}\"")
        print("2. Run 'source ~/.bashrc' or 'source ~/.zshrc'")
        print("3. Or create a symbolic link:")
        print(f"   sudo ln -s {os.path.join(BASE_DIR, 'terminal-assistant.py')} /usr/local/bin/terminal-assistant")
    
    print_header("Setup Complete")
    print("You can now run the assistant using:")
    print("1. ./terminal-assistant.bat (from this directory)")
    if platform.system() == "Windows":
        print("2. terminal-assistant (from any directory, if PATH was updated successfully)")
    
    print("\nEnsure you've set your API key in the .env file before running the assistant.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 