#!/bin/bash
# Simple terminal-assistant launcher script that handles async correctly

# Get current directory
CURRENT_DIR=$(pwd)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if a task was provided
if [ $# -eq 0 ]; then
    echo "Usage: terminal-assistant [task]"
    echo "Example: terminal-assistant 'list files in current directory'"
    exit 1
fi

# Construct the task from arguments
TASK="$*"

# Check for specific tasks that have direct implementations
if [[ "$TASK" == *"conda"* && "$TASK" == *"startup"* ]]; then
    echo "Detected conda startup task. Using specialized script..."
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    python disable_conda.py
    exit $?
fi

# Make sure the .env file is available
if [ -f "$CURRENT_DIR/.env" ]; then
    cp "$CURRENT_DIR/.env" "$SCRIPT_DIR/"
elif [ -f "$SCRIPT_DIR/.env" ]; then
    # Already exists
    :
else
    echo "Warning: No .env file found. API key might be missing."
fi

# Activate environment and run the assistant directly
cd "$SCRIPT_DIR"
source venv/bin/activate
python one_shot.py "$TASK"

# Return to original directory
cd "$CURRENT_DIR"
