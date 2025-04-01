#!/usr/bin/env python3
"""
Agent Terminal Launcher
Simple script to launch the Agent Terminal Assistant
"""
import os
import sys
import platform
import argparse

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import google.generativeai
        import yaml
        import colorama
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if the API key is available"""
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GOOGLE_API_KEY'):
        print("ERROR: GOOGLE_API_KEY not found in environment variables")
        print("Please create a .env file with your API key: GOOGLE_API_KEY=your_key_here")
        return False
    return True

def parse_arguments():
    """Parse command line arguments"""
    # Check for direct arguments (without using argparse)
    # This handles cases where the batch file passes arguments directly
    if len(sys.argv) > 1:
        # If first arg is --execute, use argparse to parse it
        if sys.argv[1].startswith('--execute='):
            parser = argparse.ArgumentParser(description="AI Terminal Assistant")
            parser.add_argument("--execute", type=str, help="Execute a command and exit", default=None)
            # Parse known args only to avoid problems with special characters in commands
            args, _ = parser.parse_known_args()
            return args
        else:
            # Otherwise, treat all args as a command to execute
            command = ' '.join(sys.argv[1:])
            # Create a custom args object
            class Args:
                pass
            args = Args()
            args.execute = command
            return args
    else:
        # No arguments, run in interactive mode
        class Args:
            pass
        args = Args()
        args.execute = None
        return args

def main():
    """Main entry point"""
    args = parse_arguments()
    execute_mode = args.execute is not None
    
    # Only print startup message in interactive mode
    if not execute_mode:
        print("Starting Agent Terminal Assistant...")
    else:
        print(f"Running command: {args.execute}")
    
    # Special handling for help/version only - everything else goes to the AI
    if execute_mode:
        command = args.execute.strip()
        command_lower = command.lower()
        
        # Only handle special commands like version and help
        if command_lower in ["--version", "version", "-v"]:
            print("AI Terminal Assistant v1.0")
            return 0
        elif command_lower in ["--help", "-h"]:
            print("Usage: terminal-assistant [command]")
            print("Run without arguments for interactive mode")
            return 0
    
    # Check if dependencies are installed
    if not check_dependencies():
        return 1
        
    # Check if API key is available
    if not check_api_key():
        return 1
    
    # Launch the agent terminal
    try:
        from agent_terminal import AgentTerminal
        
        if execute_mode:
            # Run in command execution mode
            try:
                # Convert Windows path separators to forward slashes if needed
                # This helps prevent interpretation of backslashes as escape characters
                command = args.execute.replace('\\', '/')
                
                # Create agent with auto_run and silent_init enabled
                agent = AgentTerminal(auto_run=True, silent_init=True)
                
                # Process the user input
                agent.process_user_input(command)
                return 0
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                return 130  # Standard exit code for SIGINT
        else:
            # Run in interactive mode
            try:
                agent = AgentTerminal()
                agent.run()
                return 0
            except KeyboardInterrupt:
                print("\nExiting by user request.")
                return 130
    except Exception as e:
        print(f"Error launching Agent Terminal: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 