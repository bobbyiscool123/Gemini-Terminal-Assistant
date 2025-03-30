#!/bin/bash
# terminal-assistant.sh - One-shot command for Gemini Terminal Assistant
# Usage: terminal-assistant <task description>

# Check if a task was provided
if [ $# -eq 0 ]; then
  echo "Usage: terminal-assistant <task description>"
  echo "Example: terminal-assistant \"install nodejs\""
  exit 1
fi

# Save the current directory
CURRENT_DIR=$(pwd)

# Path to the Gemini Terminal Assistant installation
# This should be changed to match your actual installation path
ASSISTANT_DIR="/root/Desktop/Gemini-Terminal-Assistant"

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
source "$ASSISTANT_DIR/venv/bin/activate" && \
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
    print(f'Error loading Terminal Assistant: {e}')
    sys.exit(1)

# Run the assistant with the task
async def run_one_shot():
    agent = TerminalAgent(initial_directory=os.environ.get('CURRENT_WORKING_DIR'))
    await agent.initialize()
    print('\n🤖 Terminal Assistant: Working on your task...\n')
    result = await agent.process_task('$TASK', one_shot=True)
    print('\n✅ Task completed:\n', result)
    await agent.cleanup()

# Run in one-shot mode
if __name__ == '__main__':
    asyncio.run(run_one_shot())
"

# Return to the original directory
cd "$CURRENT_DIR"
