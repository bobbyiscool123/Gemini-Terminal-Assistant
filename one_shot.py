#!/usr/bin/env python3
"""
One-shot script for Gemini Terminal Assistant
Handles async operations properly
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Check if task is provided
if len(sys.argv) < 2:
    print("Usage: python one_shot.py <task>")
    print("Example: python one_shot.py 'list files in current directory'")
    sys.exit(1)

# Get the task from command line arguments
task = " ".join(sys.argv[1:])

# Load environment variables
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("venv/.env"):
    load_dotenv("venv/.env")

# Import the necessary classes
try:
    from agent_terminal import TerminalAgent
except ImportError:
    print("Error: Could not import TerminalAgent. Make sure you're in the correct directory.")
    sys.exit(1)

# Run the agent with the task
async def run_one_shot():
    agent = TerminalAgent()
    await agent.initialize()
    print(f"\n🤖 Terminal Assistant: Working on your task...\n")
    
    try:
        result = await agent.process_task(task, one_shot=True)
        print(f"\n✅ Task completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1
        
    # Clean up
    await agent.cleanup()
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(run_one_shot())) 