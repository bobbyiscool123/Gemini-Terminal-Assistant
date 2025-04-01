#!/bin/bash
# terminal-assistant.sh - One-shot command for Gemini Terminal Assistant
# Usage: terminal-assistant <task description>

# Terminal Assistant Launcher
# This script launches the Terminal Assistant in one-shot mode

# Function to display usage
show_usage() {
    echo "Usage: terminal-assistant [task]"
    echo "Example: terminal-assistant 'list files in current directory'"
    exit 1
}

# Function to check Python version
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed"
        exit 1
    fi
    
    # Use Python itself to check version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    major_version=$(python3 -c 'import sys; print(sys.version_info[0])')
    minor_version=$(python3 -c 'import sys; print(sys.version_info[1])')
    
    if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 7 ]); then
        echo "Error: Python 3.7 or higher is required (found $python_version)"
        exit 1
    fi
}

# Function to check Termux environment
check_termux_env() {
    if [ -d "/data/data/com.termux" ]; then
        export TERMUX=true
        # Set Termux-specific paths
        export PATH="/data/data/com.termux/files/usr/bin:$PATH"
        # Check for Termux packages
        if ! command -v python3 &> /dev/null; then
            echo "Installing required Termux packages..."
            pkg update -y
            pkg install -y python
        fi
    else
        export TERMUX=false
    fi
}

# Function to check PRoot-distro environment
check_proot_env() {
    if [ -f "/usr/local/bin/proot-distro" ]; then
        export PROOT=true
        # Get current distribution
        export PROOT_DISTRO=$(proot-distro list | grep "^\*" | cut -d' ' -f2)
    else
        export PROOT=false
    fi
}

# Main script
if [ $# -eq 0 ]; then
    show_usage
fi

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ASSISTANT_DIR="$SCRIPT_DIR"

# Check if assistant directory exists
if [ ! -d "$ASSISTANT_DIR" ]; then
    echo "Error: Assistant directory not found at $ASSISTANT_DIR"
    exit 1
fi

# Check Python version
check_python_version

# Check environment
check_termux_env
check_proot_env

# Check for virtual environment
if [ ! -d "$ASSISTANT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ASSISTANT_DIR/venv"
fi

# Check for .env file
if [ ! -f "$ASSISTANT_DIR/.env" ]; then
    echo "Error: .env file not found. Please create one with your API key."
    exit 1
fi

# Construct the task from arguments
TASK="$*"

# Activate virtual environment and run the assistant
cd "$ASSISTANT_DIR" || exit 1

# Source the virtual environment
if [ "$TERMUX" = true ]; then
    source "$ASSISTANT_DIR/venv/bin/activate"
else
    source "$ASSISTANT_DIR/venv/bin/activate"
fi

# Set environment variables
export PYTHONPATH="$ASSISTANT_DIR:$PYTHONPATH"
export TERMUX_ENV="$TERMUX"
export PROOT_ENV="$PROOT"
export PROOT_DISTRO_NAME="$PROOT_DISTRO"

# Run the assistant
python3 -c "
import os
import sys
from agent_terminal import AgentTerminal

# Set working directory
os.chdir('$ASSISTANT_DIR')

# Initialize and run the assistant
try:
    agent = AgentTerminal()
    agent.run_one_shot('$TASK')
except Exception as e:
    print(f'Error: {str(e)}', file=sys.stderr)
    sys.exit(1)
"
