#!/usr/bin/env python3
"""
Script to disable conda automatic initialization in shell config files
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def print_colored(text, color):
    """Print colored text"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m", 
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def run_command(command):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {
            "exit_code": 1,
            "output": "",
            "error": str(e)
        }

def disable_conda():
    """Find and disable conda auto-initialization"""
    print_colored("=" * 50, "cyan")
    print_colored("🚀 Disabling conda automatic initialization", "green")
    print_colored("=" * 50, "cyan")
    print()
    
    start_time = datetime.now()
    errors = []
    
    # Check common shell config files
    shell_files = [
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.bash_profile"),
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/.profile")
    ]
    
    # Execute the search commands
    found_conda_init = False
    for shell_file in shell_files:
        if not os.path.exists(shell_file):
            continue
            
        print_colored(f"🔍 Checking {shell_file}...", "blue")
        with open(shell_file, 'r') as f:
            content = f.read()
            
        if "conda" in content and "initialize" in content:
            found_conda_init = True
            print_colored(f"✅ Found conda initialization in {shell_file}", "green")
            
            # Create a backup
            backup_file = f"{shell_file}.bak"
            shutil.copy2(shell_file, backup_file)
            print_colored(f"✅ Created backup at {backup_file}", "green")
            
            # Modify the file - comment out conda initialization
            modified_content = []
            in_conda_block = False
            for line in content.split('\n'):
                if ">>> conda initialize >>>" in line:
                    in_conda_block = True
                    modified_content.append("# " + line)
                elif "<<< conda initialize <<<" in line:
                    in_conda_block = False
                    modified_content.append("# " + line)
                elif in_conda_block:
                    modified_content.append("# " + line)
                else:
                    modified_content.append(line)
            
            # Add manual initialization instructions
            modified_content.append("\n# To initialize conda manually, use: conda activate")
            modified_content.append("# or source ~/anaconda3/etc/profile.d/conda.sh")
            
            # Write back to file
            with open(shell_file, 'w') as f:
                f.write('\n'.join(modified_content))
                
            print_colored(f"✅ Successfully disabled conda auto-initialization in {shell_file}", "green")
    
    if not found_conda_init:
        print_colored("⚠️ Could not find conda initialization in standard shell config files", "yellow")
        print_colored("🔍 Checking other possible locations...", "blue")
        
        # Check for conda.sh
        conda_sh = os.path.expanduser("~/anaconda3/etc/profile.d/conda.sh")
        if os.path.exists(conda_sh):
            print_colored(f"✅ Found conda.sh at {conda_sh}", "green")
            print_colored("ℹ️ This file is sourced for conda initialization", "blue")
            print_colored("ℹ️ To manually initialize conda, use:", "blue")
            print_colored(f"   source {conda_sh}", "yellow")
        
        # Check for conda in PATH
        result = run_command("which conda")
        if result["exit_code"] == 0:
            conda_path = result["output"].strip()
            print_colored(f"✅ Found conda at {conda_path}", "green")
            print_colored("ℹ️ To use conda without auto-initialization:", "blue")
            print_colored("   1. Create an alias in your shell config:", "yellow")
            print_colored(f"      alias conda='{conda_path}'", "yellow")
            
        errors.append("Could not automatically disable conda initialization")
    
    # Print summary
    duration = (datetime.now() - start_time).total_seconds()
    print()
    print_colored("=" * 50, "cyan")
    print_colored("📊 Task Summary:", "green")
    print_colored("=" * 50, "cyan")
    print_colored(f"Total Duration: {duration:.2f}s", "blue")
    
    if errors:
        print()
        print_colored("❌ Errors:", "red")
        for error in errors:
            print_colored(f"  • {error}", "red")
    else:
        print()
        print_colored("✅ Task completed successfully!", "green")
        print_colored("ℹ️ Please restart your terminal or run 'source ~/.bashrc' to apply changes", "yellow")
    
    print_colored("=" * 50, "cyan")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = disable_conda()
    sys.exit(0 if success else 1) 