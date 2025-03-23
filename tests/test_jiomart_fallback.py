import os
import time
import webbrowser
import platform
import subprocess
import pyautogui
from datetime import datetime
import colorama
from colorama import Fore, Style
from terminal_ai_assistant import TaskStructure

# Initialize colorama
colorama.init()

print(f"{Fore.CYAN}Testing JioMart Fallback Phases{Style.RESET_ALL}")

# Create a task for JioMart
task = TaskStructure("go to browser and into jio mart and add some snacks to the cart")

# Force create the JioMart fallback phases
task.create_fallback_phases()

# Print the phases
print(f"\n{Fore.YELLOW}Generated JioMart Fallback Phases:{Style.RESET_ALL}")
for i, phase in enumerate(task.phases):
    print(f"\n{Fore.CYAN}Phase {i+1}: {phase['name']}{Style.RESET_ALL}")
    for j, step in enumerate(phase['steps']):
        print(f"  Step {j+1}: {step['name']}")
        for k, mini_step in enumerate(step['mini_steps']):
            cmd = mini_step.get('command', 'No command')
            print(f"    Mini-step {k+1}: {mini_step['name']} - {cmd}")

# Execute the commands from the first phase
print(f"\n{Fore.GREEN}Executing commands from the first phase...{Style.RESET_ALL}")

def execute_ai_command(command):
    """Execute a command with AI prefixes"""
    print(f"\n{Fore.YELLOW}Executing: {command}{Style.RESET_ALL}")
    start_time = time.time()
    
    if command.startswith("ai_browser:"):
        url = command.split("ai_browser:", 1)[1].strip()
        print(f"{Fore.CYAN}Opening browser to URL: {url}{Style.RESET_ALL}")
        webbrowser.open(url)
        result = {
            "success": True,
            "message": f"Opened browser to {url}",
            "execution_time": time.time() - start_time
        }
        
    elif command.startswith("ai_screenshot:"):
        screenshot_name = command.split("ai_screenshot:", 1)[1].strip()
        # Ensure screenshots directory exists
        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/{screenshot_name}_{int(time.time())}.png"
        
        try:
            # Take screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            print(f"{Fore.GREEN}Screenshot saved to {screenshot_path}{Style.RESET_ALL}")
            result = {
                "success": True,
                "message": f"Screenshot saved to {screenshot_path}",
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            error_msg = f"Failed to take screenshot: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            result = {
                "success": False,
                "message": error_msg,
                "execution_time": time.time() - start_time
            }
            
    elif command.startswith("ai_ask:"):
        question = command.split("ai_ask:", 1)[1].strip()
        print(f"{Fore.YELLOW}Question for user: {question}{Style.RESET_ALL}")
        answer = input(f"{Fore.CYAN}> {Style.RESET_ALL}")
        result = {
            "success": True,
            "message": f"User response: {answer}",
            "execution_time": time.time() - start_time
        }
        
    else:
        result = {
            "success": False,
            "message": f"Unsupported command: {command}",
            "execution_time": time.time() - start_time
        }
    
    print(f"{Fore.GREEN}Command completed in {result['execution_time']:.2f} seconds{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Result: {result['message']}{Style.RESET_ALL}")
    
    return result

# Execute first phase commands
first_phase = task.phases[0]
print(f"\n{Fore.MAGENTA}Executing Phase 1: {first_phase['name']}{Style.RESET_ALL}")
for step in first_phase['steps']:
    print(f"\n{Fore.YELLOW}Step: {step['name']}{Style.RESET_ALL}")
    for mini_step in step['mini_steps']:
        command = mini_step.get('command')
        if command:
            execute_ai_command(command)
            time.sleep(2)

# Execute second phase commands
second_phase = task.phases[1]
print(f"\n{Fore.MAGENTA}Executing Phase 2: {second_phase['name']}{Style.RESET_ALL}")
for step in second_phase['steps']:
    print(f"\n{Fore.YELLOW}Step: {step['name']}{Style.RESET_ALL}")
    for mini_step in step['mini_steps']:
        command = mini_step.get('command')
        if command:
            execute_ai_command(command)
            time.sleep(2)

print(f"\n{Fore.GREEN}JioMart fallback phases test completed!{Style.RESET_ALL}") 