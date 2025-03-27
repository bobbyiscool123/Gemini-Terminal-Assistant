#!/usr/bin/env python3
"""
Agent Terminal Launcher
Simple script to launch the Agent Terminal Assistant
"""
import os
import sys
import platform

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

def main():
    """Main entry point"""
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