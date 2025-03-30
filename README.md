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
- **🚀 Portable Usage** - Run from anywhere with PATH integration

## 📋 Requirements

- Python 3.8 or higher
- Google API key for Gemini AI
- Internet connection for AI operations
- Windows operating system (primary support, Linux/macOS supported with limitations)

## 🚀 Installation

### Option 1: Standard Setup

1. Clone the repository or download and extract the source code
2. Run the setup script:

```bash
python setup.py
```

This will automatically:
- Check and install required dependencies
- Set up the configuration files
- Create a virtual environment (if requested)
- Guide you through API key setup

### Option 2: Global Installation (Windows)

To make the assistant accessible from anywhere in your system:

1. Run the setup script first to ensure all dependencies are installed
2. Run the PATH integration script as administrator:

```bash
add-to-path.bat
```

This will:
- Add the assistant's installation directory to your system PATH
- Allow you to run the assistant from any command prompt or terminal
- Enable direct command execution from anywhere

### Environment Configuration

Create a `.env` file in the project root with your Google API key:

```
GOOGLE_API_KEY=your_api_key_here
```

You can obtain a Gemini API key from [Google AI Studio](https://ai.google.dev/).

## 🎮 Usage

### Running the Assistant

#### Interactive Mode

After setting up the PATH (Option 2 above), you can run from any terminal:

```bash
terminal-assistant
```

Or directly from the installation directory:

```bash
terminal-assistant.bat
```

#### Direct Command Execution

Run a specific task without entering interactive mode:

```bash
terminal-assistant "your task description here"
```

Example:
```bash
terminal-assistant "check if python is installed"
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

### Conversational Interface

The assistant can handle both:

1. **Task-based queries** - Commands to execute specific operations
2. **Conversational queries** - Natural language questions and conversation

The assistant automatically detects the type of input and responds appropriately, using the Gemini AI to generate natural responses for conversational interactions.

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

## 🔄 Recent Changes

### Version 1.0
- Added PATH integration for global access from any terminal
- Implemented direct command execution mode
- Improved error handling and keyboard interrupt management
- Added conversational mode using Gemini AI for natural interactions
- Enhanced the batch file for better drive handling and directory changes
- Added silent mode for non-interactive use
- Fixed issues with command history saving and loading

## 🏗️ Project Structure

- **agent_terminal.py** - Main agent implementation with task processing logic
- **run_agent.py** - Launcher script with dependency checking and argument processing
- **setup.py** - Setup script for installing dependencies
- **terminal-assistant.bat** - Batch file for running the assistant
- **add-to-path.bat** - Script for adding the assistant to the system PATH

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
```

## 🛠️ Troubleshooting

### Common Issues

1. **"The system cannot find the drive specified"**
   - Ensure the batch file has the correct path to your installation directory
   - Try running the terminal-assistant.bat file directly from its location

2. **API Key Issues**
   - Verify your Gemini API key is correctly set in the .env file
   - Check that the API key has not expired or reached its quota limit

3. **Python Not Found**
   - Ensure Python 3.8+ is installed and in your system PATH
   - Try running `python --version` to verify Python is accessible

4. **Keyboard Interrupt Not Working**
   - If Ctrl+C doesn't terminate properly, press it multiple times
   - As a last resort, close the terminal window and restart

### PATH Integration Issues

If the `add-to-path.bat` script fails:
1. Run it as administrator
2. Verify you have write permissions to the registry
3. Try adding the directory manually to your PATH environment variable

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