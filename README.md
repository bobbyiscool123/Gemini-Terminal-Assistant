# Terminal AI Assistant

A powerful terminal assistant that uses Google's Gemini 2.0 Flash AI to execute commands based on natural language descriptions. Similar to aider-chat but focused on terminal command execution.

## Features

1. **Natural Language Command Generation**: Describe what you want to do in plain English, and the AI will generate the appropriate commands.
2. **Real-time Command Streaming**: See command output as it happens, just like in a regular terminal.
3. **Command History**: Keep track of all executed commands with their outputs and execution times.
4. **Dangerous Command Protection**: Built-in safety checks for potentially dangerous commands.
5. **Rich Terminal Interface**: Beautiful and informative terminal UI with progress bars and formatted output.
6. **Configuration System**: Customize behavior through a YAML configuration file.
7. **Cross-platform Support**: Works on Windows, macOS, and Linux.
8. **Command Execution Statistics**: Track execution times and success rates.
9. **Interactive Mode**: Natural conversation with the AI about terminal operations.
10. **Graceful Error Handling**: Proper error handling and recovery mechanisms.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/terminal-ai-assistant.git
cd terminal-ai-assistant
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

1. Run the assistant:
```bash
python terminal_ai_assistant.py
```

2. Type your task in natural language. For example:
```
What would you like me to do? Create a new directory called projects and list its contents
```

3. The AI will generate and execute the appropriate commands in sequence.

## Available Commands

- `help`: Show help information
- `exit` or `quit`: Exit the program
- `clear`: Clear the screen
- `history`: Show command history
- `config`: Show current configuration
- `cd`: Change directory
- `pwd`: Show current directory

## Configuration

Edit `config.yaml` to customize the assistant's behavior:

- `max_history`: Maximum number of commands to keep in history
- `auto_save`: Whether to automatically save command history
- `theme`: Terminal theme (dark/light)
- `stream_output`: Whether to stream command output in real-time
- `confirm_dangerous`: Whether to ask for confirmation before executing dangerous commands
- And more...

## Safety Features

- Built-in protection against dangerous commands
- Command confirmation for potentially harmful operations
- Timeout protection for long-running commands
- Error handling and recovery

## Example Tasks

Here are some example tasks you can try:

1. "Show me information about my system"
2. "Find all text files in the current directory and display their contents"
3. "Download a file from https://example.com/sample.txt and save it as sample.txt"
4. "Create a new Python script that prints Hello World"
5. "Show disk usage statistics in a human-readable format"

## Advanced Usage

### Custom Configuration

The Terminal AI Assistant can be customized by editing the `config.yaml` file. This allows you to change various aspects of the assistant's behavior:

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

# AI Settings
ai_model: gemini-2.0-flash
temperature: 0.7
max_tokens: 1000
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 