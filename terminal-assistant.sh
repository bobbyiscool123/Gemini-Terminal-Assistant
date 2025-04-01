#!/bin/bash
# Terminal Assistant
# A natural language interface for terminal commands using Gemini 2.5 Pro

# Configuration
CONFIG_FILE="$HOME/.config/terminal_assistant/config.yaml"
LOG_FILE="$HOME/.config/terminal_assistant/terminal_assistant.log"
HISTORY_FILE="$HOME/.config/terminal_assistant/command_history.txt"

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create config directory if it doesn't exist
mkdir -p "$(dirname "$CONFIG_FILE")"

# Default configuration
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << EOF
ai_temperature: 0.7
auto_save: true
enable_autocompletion: true
enable_command_templates: true
auto_correct_typos: true
command_verification_level: "high"
ai_response_style: "concise"
EOF
fi

# Load configuration
# Using a safer approach to avoid executing unexpected text
if [ -f "$CONFIG_FILE" ]; then
    CONFIG_TEMP=$(mktemp)
    python3 - << EOF > "$CONFIG_TEMP"
import yaml
import sys
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
for key, value in config.items():
    if isinstance(value, str):
        print(f"{key.upper()}=\"{value}\"")
    else:
        print(f"{key.upper()}=\"{value}\"")
EOF
    source "$CONFIG_TEMP"
    rm "$CONFIG_TEMP"
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Command history function
add_to_history() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$HISTORY_FILE"
}

# Main function
main() {
    local query="$*"
    
    # Log the query
    log "User query: $query"
    
    # Add to history
    add_to_history "$query"
    
    # Pass the query through an environment variable
    export TA_USER_QUERY="$query"
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    export SCRIPT_DIR="$SCRIPT_DIR"
    
    # Create a Python script file in a temp directory
    TEMP_DIR=$(mktemp -d)
    TEMP_SCRIPT="${TEMP_DIR}/run_assistant.py"
    
    # Write Python code to the temp file
    cat > "$TEMP_SCRIPT" << 'ENDPYTHON'
#!/usr/bin/env python3
import sys
import os
import asyncio

# Add the current directory to path if needed
script_dir = os.environ.get('SCRIPT_DIR', '')
if script_dir and script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now import the module
from agent_terminal import AgentTerminal

# Get query from environment variable
query = os.environ.get('TA_USER_QUERY', '')

# Create agent and run task
agent = AgentTerminal()
agent.auto_run = True  # Run without prompting
asyncio.run(agent.process_user_task(query))
ENDPYTHON
    
    # Make the script executable
    chmod +x "$TEMP_SCRIPT"
    
    # Execute the Python script from the script directory
    # Redirect any potential shell errors to /dev/null to prevent execution
    (cd "$SCRIPT_DIR" && python3 "$TEMP_SCRIPT") 2>/dev/null
    
    # Clean up the temporary directory
    rm -rf "$TEMP_DIR"
}

# Handle command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: terminal-assistant 'your command in natural language'"
    echo "Example: terminal-assistant 'show me the current directory'"
    exit 1
fi

# Run main function with all arguments
main "$@"
