#!/bin/bash
# Terminal Assistant
# A natural language interface for terminal commands using Gemini 2.5 Pro

# Configuration
CONFIG_FILE="$HOME/.config/terminal_assistant/config.yaml"
LOG_FILE="$HOME/.config/terminal_assistant/terminal_assistant.log"
HISTORY_FILE="$HOME/.config/terminal_assistant/command_history.txt"

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
source <(python3 -c '
import yaml
import sys
with open("'"$CONFIG_FILE"'", "r") as f:
    config = yaml.safe_load(f)
for key, value in config.items():
    print(f"export {key.upper()}=\"{value}\"")
')

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
    
    # Use the full agent_terminal.py with rich UI and task breakdown
    python3 -c "
import sys
import os
import asyncio
from agent_terminal import AgentTerminal

# Get query from environment variable
query = os.environ.get('TA_USER_QUERY', '')

# Create agent and run task
agent = AgentTerminal()
agent.auto_run = True  # Run without prompting
asyncio.run(agent.process_user_task(query))
"
}

# Handle command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: terminal-assistant 'your command in natural language'"
    echo "Example: terminal-assistant 'show me the current directory'"
    exit 1
fi

# Run main function with all arguments
main "$@"
