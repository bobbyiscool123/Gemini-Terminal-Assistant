# AI Terminal Assistant

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

**An intelligent, contextually-aware terminal assistant powered by Gemini AI**

</div>

## ✨ Features

- **🧠 Smart Task Planning** - Analyzes tasks, breaks them down into subtasks, and creates optimized execution plans
- **🔄 Context Awareness** - Maintains conversation context and understands task relationships across interactions
- **⚙️ Automatic Command Generation** - Creates optimal commands for your specific operating system
- **🖥️ Cross-Platform Support** - Works seamlessly on Windows, macOS, and Linux with automatic adaptation
- **🩹 Intelligent Error Recovery** - Automatically recovers from command failures and suggests alternatives
- **📊 Real-time Execution Monitoring** - Streams command output with status updates and progress indicators
- **🔍 Smart Installation Detection** - Finds existing software installations before attempting new installations
- **📁 File Organization** - Can sort and organize files by type and content
- **📦 Package Manager Integration** - Automatically installs Chocolatey (Windows) when needed for installing software
- **🏃 Auto-Run Mode** - Executes tasks automatically without requiring confirmation for each step
- **❓ Intelligent Questioning** - Asks clarifying questions only when necessary for task completion
- **🚀 Portable Usage** - Run from anywhere with the portable batch file setup

## 📋 Requirements

- Python 3.8 or higher
- Google API key for Gemini AI
- Internet connection for AI operations
- Windows operating system (for portable/global setup)

## 🚀 Installation

### Option 1: Quick Setup (Recommended)

Run the `setup_global.bat` file to automatically:
1. Create a virtual environment
2. Install all dependencies
3. Make the assistant accessible from anywhere in your system

```bash
setup_global.bat
```

### Option 2: Manual Setup

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-terminal-assistant.git
cd ai-terminal-assistant
```

#### 2. Run the setup script

```bash
python setup.py
```

#### 3. Configure API access

Create a `.env` file in the project root with your Google API key:

```
GOOGLE_API_KEY=your_api_key_here
```

You can obtain a Gemini API key from [Google AI Studio](https://ai.google.dev/).

#### 4. (Optional) Make globally accessible

To make the assistant accessible from anywhere:

```bash
python launcher.py
```

## 🎮 Usage

### Running the Assistant

#### Option 1: Run from anywhere (after global setup)

Open any terminal or command prompt and type:

```bash
terminal-assistant
```

#### Option 2: Run directly from the project folder

Double-click on `terminal-assistant.bat` or run:

```bash
terminal-assistant.bat
```

### Basic Commands

| Command | Description |
|---------|-------------|
| `help` | Display help information |
| `exit` | Exit the application |
| `clear` | Clear the terminal screen |
| `history` | Show command history |
| `tasks` | Show active and completed tasks |
| `context` | Show current context information |
| `cd [path]` | Change directory |
| `pwd` | Show current directory |
| `auto on/off` | Enable/disable auto-run mode |

### Using the Assistant

Simply describe what you want to do in natural language. The assistant will:

1. Analyze your request and create a structured execution plan
2. Break down the task into logical subtasks
3. Show you the plan and begin execution
4. Execute each subtask with appropriate commands
5. Handle any errors and provide recovery options
6. Complete the task and show you the results

### Example Tasks

```
"Check if ffmpeg is installed on my system"
"Install Python 3.11 with pip"
"Sort my downloads folder by file type"
"Find all JPG files larger than 5MB and compress them"
"Create a backup of my documents folder"
"Monitor CPU and memory usage in real-time"
"Install Node.js and set up a new React project"
"Find duplicate files in my pictures folder"
```

## 🏗️ Architecture

The assistant is built with a modular architecture:

- **agent_terminal.py** - Main agent implementation with task processing logic
- **mcp_server.py** - Model Context Protocol server for system operations
- **agent_utils.py** - Utility functions for platform detection and command validation
- **run_agent.py** - Launcher script with dependency checking
- **setup.py** - Setup script for creating virtual environment and installing dependencies
- **terminal-assistant.bat** - Batch file for running the assistant
- **launcher.py** - Script for making the assistant globally accessible

## ⚙️ Configuration

Customize the assistant by modifying `config.yaml`:

```yaml
# General Settings
max_history: 100  # Maximum number of commands to keep in history
history_file: "command_history.json"  # File to store command history
max_tokens: 8000  # Maximum tokens to use in AI requests

# Agent Behavior
auto_run: true  # Execute commands automatically without confirmation
question_probability: 0.1  # Probability of asking clarifying questions (0.0-1.0)

# System Integration
enable_mcp_server: true  # Enable the Model Context Protocol server
scan_drives_on_startup: false  # Scan system drives during initialization
```

## 🔍 Advanced Features

### File Sorting and Organization

The assistant can sort and organize files by type:

```
"Sort my downloads folder by file type"
```

This will:
1. Analyze files in the specified directory
2. Create folders for different file types (Images, Videos, Documents, etc.)
3. Move files to appropriate folders
4. Clean up empty directories

### Software Installation

When installing software, the assistant will:

1. Check if the program is already installed
2. Install package managers (like Chocolatey) if needed
3. Use appropriate commands for your operating system
4. Verify successful installation

Example:
```
"Install ffmpeg on my system"
```

### Model Context Protocol (MCP)

The MCP server provides system information without sending unnecessary data to the AI model:

- Checks for installed software and package managers
- Gathers system drive information
- Provides folder structure analysis
- Manages file operations locally

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for providing the AI capabilities
- All open-source libraries and tools used in this project