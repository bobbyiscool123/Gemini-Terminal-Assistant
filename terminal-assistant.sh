#!/bin/bash
# Direct terminal-assistant launcher
ASSISTANT_DIR="/root/Desktop/Gemini-Terminal-Assistant"
LOG_FILE="$ASSISTANT_DIR/terminal_assistant.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_message "Error: $1 is not installed"
        return 1
    fi
    return 0
}

# Function to check file permissions
check_file_permissions() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log_message "Error: File not found: $file"
        return 1
    fi
    
    if [ ! -x "$file" ]; then
        log_message "Warning: File not executable: $file"
        if ! chmod +x "$file"; then
            log_message "Error: Failed to make file executable: $file"
            return 1
        fi
        log_message "Made file executable: $file"
    fi
    
    return 0
}

# Check if a task was provided
if [ $# -eq 0 ]; then
    echo "Usage: terminal-assistant [task]"
    echo "Example: terminal-assistant 'list files in current directory'"
    echo "Options:"
    echo "  --debug     Enable debug logging"
    echo "  --help      Show this help message"
    exit 1
fi

# Parse command line options
DEBUG=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG=true
            shift
            ;;
        --help)
            echo "Usage: terminal-assistant [options] [task]"
            echo "Options:"
            echo "  --debug     Enable debug logging"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Save current directory
CURRENT_DIR=$(pwd)

# Check if assistant directory exists
if [ ! -d "$ASSISTANT_DIR" ]; then
    log_message "Error: Assistant directory not found at $ASSISTANT_DIR"
    exit 1
fi

# Go to assistant directory
cd "$ASSISTANT_DIR" || {
    log_message "Error: Failed to change to assistant directory"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "$ASSISTANT_DIR/venv" ]; then
    log_message "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check file permissions for required scripts
required_scripts=("one_shot.py" "disable_conda.py")
for script in "${required_scripts[@]}"; do
    if [ -f "$ASSISTANT_DIR/$script" ]; then
        if ! check_file_permissions "$ASSISTANT_DIR/$script"; then
            log_message "Error: Failed to set permissions for $script"
            exit 1
        fi
    fi
done

# Activate environment
if ! source "$ASSISTANT_DIR/venv/bin/activate"; then
    log_message "Error: Failed to activate virtual environment"
    exit 1
fi

# Check Python version
if ! check_command python3; then
    exit 1
fi

# Check Python version compatibility
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    log_message "Error: Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

# Check required Python packages
REQUIRED_PACKAGES=("google-generativeai" "python-dotenv" "pyyaml" "rich")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! pip show "$package" &> /dev/null; then
        log_message "Error: Required package $package is not installed"
        exit 1
    fi
done

# Run the assistant with the task
log_message "Starting terminal assistant with task: $*"
if [[ "$*" == *"conda"* && "$*" == *"startup"* ]]; then
    # Use specialized conda script
    if [ -f "$ASSISTANT_DIR/disable_conda.py" ]; then
        python3 "$ASSISTANT_DIR/disable_conda.py"
    else
        log_message "Error: disable_conda.py not found"
        exit 1
    fi
else
    # Use standard one-shot mode
    if [ -f "$ASSISTANT_DIR/one_shot.py" ]; then
        python3 "$ASSISTANT_DIR/one_shot.py" "$*"
    else
        log_message "Error: one_shot.py not found"
        exit 1
    fi
fi

# Return to original directory
cd "$CURRENT_DIR" || {
    log_message "Warning: Failed to return to original directory"
}

# Deactivate virtual environment
deactivate

log_message "Terminal assistant completed"
