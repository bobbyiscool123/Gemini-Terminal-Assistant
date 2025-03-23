# Terminal AI Assistant

An advanced terminal assistant powered by Google's Gemini AI that helps you execute terminal commands intelligently.

## Features

- **Task Execution**: AI determines the best commands to execute based on your task
- **Interactive Q&A**: AI can ask questions when needed to complete tasks
- **Advanced Terminal UI**: Rich terminal interface with progress displays
- **Command History**: Track and review all executed commands
- **Smart Error Handling**: Automatic error detection and recovery suggestions
- **Organized Logging**: Dedicated logs directory for tracking operations

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your Google API key in a `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

### Using the Launcher Menu

The easiest way to start the Terminal AI Assistant is by using the launcher menu:

```bash
python run_assistant.py
```

This will display a user-friendly menu where you can:
- Start the Terminal AI Assistant
- Check for Dependencies
- View README
- Exit

### Direct Command Usage

If you prefer to start the assistant directly:

```bash
python terminal_ai_assistant.py
```

### Commands

- `help`: Show help message
- `exit/quit`: Exit the program
- `clear`: Clear the screen
- `history`: Show command history
- `config`: Show current configuration
- `cd [path]`: Change directory
- `pwd`: Show current directory

## Task Execution Process

1. Enter a task description when prompted.
2. The AI will analyze the task and determine the necessary commands.
3. The assistant will execute each command, showing progress in real-time.
4. If errors occur, the AI will suggest ways to fix them.
5. All executed commands are saved in the command history.

## Configuration

Settings can be customized by creating a `config.yaml` file in the root directory with options like:

```yaml
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
```

## Future Enhancements

In future versions, we plan to add:

- Browser automation capabilities
- Screenshot functionality
- Application control
- Enhanced AI task planning

## License

This project is licensed under the MIT License - see the LICENSE file for details. 