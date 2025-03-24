# Terminal AI Assistant

A smart terminal assistant powered by AI to help with command-line tasks. It uses Google's Gemini AI to generate terminal commands based on natural language descriptions.

## Features

- Natural language to terminal command generation
- Command streaming with real-time output
- Command history tracking and management
- Aliases for frequently used commands
- Command templates with parameter substitution
- File preview functionality
- System statistics monitoring
- Command chaining for complex operations
- Smart clipboard with text transformation
- File backup and restoration
- Voice command support
- Plugin system for extending functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/terminal-ai-assistant.git
cd terminal-ai-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

Run the assistant with:
```bash
python terminal_ai_assistant.py
```

### Basic Commands

- `help` - Show available commands
- `exit` or `quit` - Exit the application
- `clear` - Clear the terminal screen
- `history` - Show command history
- `config` - Display current configuration
- `cd [path]` - Change directory
- `pwd` - Show current directory

### Advanced Features

#### Aliases

- `aliases` - List all command aliases
- `alias add [name] [command]` - Add a command alias
- `alias remove [name]` - Remove a command alias

#### Templates

- `templates` - List all command templates
- `template add [name] [template]` - Add a command template
- `template remove [name]` - Remove a command template
- `template run [name] [params]` - Run a command template

#### File Operations

- `preview [file]` - Preview the content of a file
- `backups` - List all backups
- `backup [file]` - Backup a file
- `restore [backup]` - Restore a backup

#### System Tools

- `stats` - Show system statistics

#### Command Chains

- `chain list` - List all command chains
- `chain add [name] [commands]` - Add a command chain
- `chain run [name]` - Run a command chain

#### Clipboard

- `clipboard` - Show clipboard contents
- `copy [text/file]` - Copy text or file to clipboard
- `transform [operation]` - Transform clipboard content

#### Voice Commands

- `voice [on/off]` - Enable or disable voice commands

#### Plugins

- `plugins` - List all plugins
- `plugin enable [name]` - Enable a plugin
- `plugin disable [name]` - Disable a plugin
- `plugin help [name]` - Show help for a plugin

## Creating Plugins

You can extend the functionality of the Terminal AI Assistant by creating plugins. Plugins are Python packages that implement the `Plugin` interface.

### Basic Plugin Structure

Create a directory in the `plugins` folder with the following structure:

```
plugins/
└── my_plugin/
    ├── __init__.py
    └── [other files]
```

In `__init__.py`, define a class that inherits from `Plugin`:

```python
from utils.plugin_manager import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    description = "My awesome plugin"
    version = "1.0.0"
    
    def __init__(self, terminal_assistant=None):
        super().__init__(terminal_assistant)
    
    def initialize(self) -> bool:
        return True
    
    def get_commands(self):
        return {
            "my_command": self.my_command
        }
    
    def my_command(self, *args):
        return "Hello from my plugin!"
```

## Configuration

Edit `config.yaml` to customize the assistant's behavior:

```yaml
# Terminal AI Assistant Configuration
max_history: 100
auto_save: true
theme: dark
stream_output: true
confirm_dangerous: true
timeout: 30
max_retries: 3
output_format: rich
save_history: true
history_file: command_history.json
enable_voice_commands: false
show_system_stats: false
enable_smart_clipboard: true
enable_command_chaining: true
backup_history_files: true
```

## License

MIT 

## Troubleshooting

### Input Not Visible

If you notice that your typed text doesn't appear in the terminal interface as you type, this may be due to:

1. Input handling settings in the terminal configuration
2. The way the prompt toolkit library handles input in custom terminal applications
3. A configuration setting that suppresses input echo

To fix this issue:

1. Check if `echo_input` is set to `true` in your config.yaml:
   ```yaml
   echo_input: true
   ```

2. If using a custom terminal or console, ensure it's not in "quiet" or "no-echo" mode

3. Some terminal emulators may have compatibility issues with the prompt_toolkit library

The assistant will still process your commands even if the input isn't visible. 