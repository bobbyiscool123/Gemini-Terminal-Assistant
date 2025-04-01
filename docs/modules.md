# Gemini Terminal Assistant Modules

This document provides detailed information about each module in the Gemini Terminal Assistant.

## agent_terminal.py

The primary module that implements the AI agent functionality.

### Key Components:

- **TaskState**: Represents the state of a task, including status, command history, and subtasks
- **AgentContext**: Maintains conversation history and task context
- **AgentTerminal**: The main agent class that interfaces with the Gemini API
- **TerminalAgent**: A wrapper class for easy agent initialization and cleanup

### Main Functionality:

- Task planning and breakdown
- Command generation and execution
- Conversation context management
- Task status tracking and reporting
- Safety validation for commands

### How It Interfaces:

- Uses `prompt.py` for generating prompts to send to the Gemini API
- Uses `mcp_server.py` for system operations and information
- Calls external commands via subprocess
- Maintains command history in a JSON file

## prompt.py

Manages all prompts sent to the Gemini API.

### Key Components:

- **PromptManager**: Central class for loading and formatting prompts
- Global `prompt_manager` instance for easy importing

### Main Functionality:

- Loading prompt templates from configuration
- Formatting prompts with context information
- Building structured prompts for the Gemini API
- Providing system prompts for different scenarios

### How It Interfaces:

- Used by `agent_terminal.py` to generate all prompts
- Reads from `config.yaml` for template configuration
- Creates properly formatted prompts for Gemini 2.5 Pro

## mcp_server.py

The Model Context Protocol server bridges the AI agent and the operating system.

### Key Components:

- **MCPServer**: Main class that provides system information and operations
- Global `mcp` instance for easy importing

### Main Functionality:

- Gathering system information
- Checking for installed software and package managers
- File and directory operations
- Package installation and information

### How It Interfaces:

- Used by `agent_terminal.py` for system operations
- Executes system commands via subprocess
- Provides system context for the AI agent

## one_shot.py

Provides a simplified interface for single task execution.

### Key Components:

- **run_one_shot**: Main function that initializes and runs the agent
- Signal handling for graceful termination

### Main Functionality:

- Environment checking and validation
- Agent initialization and cleanup
- Task execution with progress reporting
- Error handling and logging

### How It Interfaces:

- Called by `terminal-assistant.sh` for task execution
- Creates an instance of `TerminalAgent` from `agent_terminal.py`
- Uses Rich for terminal output formatting

## agent_utils.py

Provides utility functions for the agent.

### Key Components:

- **PlatformUtils**: Platform-specific operations
- **CommandValidator**: Security validation for commands
- **TaskUtils**: Helper functions for task management
- **FileUtils**: File and directory operation utilities

### Main Functionality:

- Sanitizing and validating commands
- Platform detection and adaptation
- File manipulation and checking
- Task parsing and normalization

### How It Interfaces:

- Used by `agent_terminal.py` for various utility functions
- Provides safety checks for command execution
- Helps with cross-platform compatibility

## terminal-assistant.sh

The main launcher script that users interact with.

### Main Functionality:

- Command-line argument parsing
- Environment setup and validation
- Virtual environment activation
- Task routing to appropriate handlers
- Error handling and logging

### How It Interfaces:

- Invoked directly by users
- Calls `one_shot.py` for most tasks
- Manages the Python virtual environment

## setup.py

Handles the installation and setup of the assistant.

### Main Functionality:

- Python environment validation
- Dependency installation
- Script path configuration
- Terminal integration

### How It Interfaces:

- Run by users during initial setup
- Creates the virtual environment
- Installs the terminal-assistant command 