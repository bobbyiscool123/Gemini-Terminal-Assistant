# Gemini Terminal Assistant Architecture

## Overview

The Gemini Terminal Assistant is a powerful, context-aware AI assistant that runs directly in your terminal. It can help with various tasks by understanding natural language requests, planning actions, and executing commands.

## Core Components

The application consists of the following core components:

1. **Launcher Script** (`terminal-assistant.sh`)
   - Entry point for users
   - Handles environment setup and activation
   - Forwards tasks to the appropriate Python module

2. **Agent Engine** (`agent_terminal.py`)
   - Main AI agent implementation
   - Handles task planning and execution
   - Maintains conversation context
   - Communicates with the Gemini API

3. **Model Context Protocol** (`mcp_server.py`)
   - Provides system information and operations
   - Acts as a bridge between the AI and the operating system
   - Handles file operations and system queries

4. **Prompt Management** (`prompt.py`)
   - Manages all prompts sent to the AI model
   - Standardizes prompt formatting
   - Loads templates from configuration files

5. **One-Shot Execution** (`one_shot.py`)
   - Provides a simplified interface for single tasks
   - Handles async operations and cleanup
   - Used by the launcher script for most tasks

6. **Utilities** (`agent_utils.py`)
   - Helper functions for platform-specific operations
   - Command validation and safety checks
   - File and task utilities

## Project Structure

```
Gemini-Terminal-Assistant/
├── agent_terminal.py         # Main AI agent implementation
├── agent_utils.py            # Utility functions and helpers
├── command_history.json      # History of executed commands
├── command_templates.yaml    # Command templates for various tasks
├── config.yaml               # Application configuration
├── docs/                     # Documentation
│   ├── app_structure.md      # Overview of app architecture
│   ├── modules.md            # Detailed module documentation
│   └── user_guide.md         # End-user documentation
├── mcp_server.py             # Model Context Protocol server
├── one_shot.py               # Single-task execution script
├── prompt.py                 # Prompt management system
├── README.md                 # Project overview and setup
├── requirements.txt          # Python dependencies
├── run_agent.py              # Alternative agent runner
├── setup.py                  # Installation and setup script
├── terminal-assistant.sh     # Main launcher script
├── terminal_assistant.log    # Application logs
├── uninstall.py              # Uninstallation script
└── venv/                     # Virtual environment
```

## Execution Flow

1. User runs `terminal-assistant` with a task
2. The launcher script (`terminal-assistant.sh`) activates the virtual environment
3. The task is passed to `one_shot.py`
4. The agent is initialized from `agent_terminal.py`
5. The agent uses `prompt.py` to format prompts for the Gemini API
6. The agent plans and executes the task, using `mcp_server.py` for system operations
7. Results are displayed to the user in the terminal
8. The virtual environment is deactivated

## Component Interactions

- **agent_terminal.py** ↔ **prompt.py**: The agent uses the prompt manager to format all prompts sent to the Gemini API
- **agent_terminal.py** ↔ **mcp_server.py**: The agent uses the MCP server to access system information and operations
- **agent_terminal.py** ↔ **agent_utils.py**: The agent uses utilities for platform-specific operations
- **one_shot.py** ↔ **agent_terminal.py**: The one-shot executor creates and manages an instance of the agent
- **terminal-assistant.sh** ↔ **one_shot.py**: The launcher invokes the one-shot executor with the user's task 