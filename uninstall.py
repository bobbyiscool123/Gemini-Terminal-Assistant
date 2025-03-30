#!/usr/bin/env python3
"""
Uninstall script for Gemini Terminal Assistant
Removes command-line wrapper, virtual environment, and optionally conda environments
"""
import os
import sys
import shutil
import subprocess
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

def get_user_confirmation(prompt):
    """Get user confirmation (y/n)"""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        print_color("Please enter 'y' or 'n'", "yellow")

def remove_terminal_assistant_command():
    """Remove the terminal-assistant command"""
    print_color("Removing terminal-assistant command...", "blue")
    
    # Check for symlink in /usr/local/bin
    symlink_path = "/usr/local/bin/terminal-assistant"
    if os.path.exists(symlink_path):
        try:
            print_color(f"Removing symlink at {symlink_path}...", "blue")
            success, _ = run_command(f"sudo rm {symlink_path}", shell=True)
            if success:
                print_color("✅ Symlink removed successfully", "green")
            else:
                print_color("❌ Failed to remove symlink. You may need to remove it manually", "red")
        except:
            print_color("❌ Failed to remove symlink. You may need to remove it manually", "red")
    
    # Remove from .bashrc
    home_dir = os.path.expanduser("~")
    bashrc_path = os.path.join(home_dir, ".bashrc")
    
    if os.path.exists(bashrc_path):
        print_color(f"Checking for terminal-assistant alias in {bashrc_path}...", "blue")
        modified = False
        
        with open(bashrc_path, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        skip_next = False
        for line in lines:
            if "# Terminal Assistant command" in line:
                skip_next = True
                modified = True
                continue
            
            if skip_next and "alias terminal-assistant=" in line:
                skip_next = False
                modified = True
                continue
            
            if "alias terminal-assistant=" in line:
                modified = True
                continue
                
            new_lines.append(line)
        
        if modified:
            with open(bashrc_path, "w") as f:
                f.writelines(new_lines)
            print_color("✅ Removed terminal-assistant alias from .bashrc", "green")
            print_color("Please run 'source ~/.bashrc' or restart your terminal to apply changes", "yellow")
        else:
            print_color("No terminal-assistant alias found in .bashrc", "yellow")
    
    # Remove the script file
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal-assistant.sh")
    if os.path.exists(script_path):
        os.remove(script_path)
        print_color(f"✅ Removed terminal-assistant.sh script", "green")

def remove_virtual_environment():
    """Remove the virtual environment"""
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    if os.path.exists(venv_path):
        print_color(f"Removing virtual environment at {venv_path}...", "blue")
        try:
            shutil.rmtree(venv_path)
            print_color("✅ Virtual environment removed successfully", "green")
        except Exception as e:
            print_color(f"❌ Failed to remove virtual environment: {e}", "red")
    else:
        print_color("No virtual environment found", "yellow")

def remove_conda_environment():
    """Remove the conda environment"""
    if not get_user_confirmation("Do you want to remove the conda environment (py3128)?"):
        return
    
    print_color("Removing conda environment py3128...", "blue")
    success, _ = run_command("conda env remove -n py3128 -y", shell=True)
    if success:
        print_color("✅ Conda environment removed successfully", "green")
    else:
        print_color("❌ Failed to remove conda environment", "red")

def main():
    """Main uninstall function"""
    print_color("Gemini Terminal Assistant Uninstaller", "cyan")
    print_color("=" * 50, "cyan")
    
    # Check if we're in the right directory
    if not os.path.exists("agent_terminal.py"):
        print_color("This script must be run from the Gemini Terminal Assistant directory", "red")
        if not get_user_confirmation("Continue anyway?"):
            return 1
    
    # Confirm uninstallation
    if not get_user_confirmation("Are you sure you want to uninstall Gemini Terminal Assistant?"):
        print_color("Uninstallation cancelled", "yellow")
        return 0
    
    # Remove terminal-assistant command
    remove_terminal_assistant_command()
    
    # Remove virtual environment
    if get_user_confirmation("Do you want to remove the virtual environment?"):
        remove_virtual_environment()
    
    # Check if conda is installed
    success, _ = run_command("conda --version")
    if success:
        remove_conda_environment()
    
    print_color("\nUninstallation completed!", "green")
    print_color("Some files may still remain in the project directory.", "yellow")
    print_color("To completely remove everything, delete the project directory:", "yellow")
    print_color(f"  rm -rf {os.path.dirname(os.path.abspath(__file__))}", "yellow")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 