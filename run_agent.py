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
    parser = argparse.ArgumentParser(description="AI Terminal Assistant")
    parser.add_argument("--execute", type=str, help="Execute a command and exit", default=None)
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    execute_mode = args.execute is not None
    
    # Only print startup message in interactive mode
    if not execute_mode:
        print("Starting Agent Terminal Assistant...")
    
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
            agent = AgentTerminal(auto_run=True, silent_init=True)
            agent.process_user_input(args.execute)
            return 0
        else:
            # Run in interactive mode
            agent = AgentTerminal()
            agent.run()
            return 0
    except Exception as e:
        print(f"Error launching Agent Terminal: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 