import os
import time
import webbrowser
import platform
import subprocess
import pyautogui
from datetime import datetime
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

print(f"{Fore.CYAN}Testing AI Command Prefixes{Style.RESET_ALL}")

def execute_ai_command(command):
    """Execute a command with AI prefixes"""
    print(f"\n{Fore.YELLOW}Executing: {command}{Style.RESET_ALL}")
    start_time = time.time()
    
    if command.startswith("ai_browser:"):
        url = command.split("ai_browser:", 1)[1].strip()
        print(f"{Fore.CYAN}Opening browser to URL: {url}{Style.RESET_ALL}")
        webbrowser.open(url)
        result = {
            "command": command,
            "stdout": f"Opened browser to {url}",
            "stderr": "",
            "exit_code": 0,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
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
                "command": command,
                "stdout": f"Screenshot saved to {screenshot_path}",
                "stderr": "",
                "exit_code": 0,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Failed to take screenshot: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            result = {
                "command": command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 1,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
    elif command.startswith("ai_ask:"):
        question = command.split("ai_ask:", 1)[1].strip()
        print(f"{Fore.YELLOW}Question for user: {question}{Style.RESET_ALL}")
        answer = input(f"{Fore.CYAN}> {Style.RESET_ALL}")
        result = {
            "command": command,
            "stdout": f"User response: {answer}",
            "stderr": "",
            "exit_code": 0,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
        }
        
    elif command.startswith("ai_app:"):
        app_name = command.split("ai_app:", 1)[1].strip()
        print(f"{Fore.CYAN}Opening application: {app_name}{Style.RESET_ALL}")
        try:
            if platform.system() == "Windows":
                os.startfile(app_name)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", app_name])
            else:  # Linux
                subprocess.call(["xdg-open", app_name])
            result = {
                "command": command,
                "stdout": f"Opened application: {app_name}",
                "stderr": "",
                "exit_code": 0,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Failed to open application {app_name}: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            result = {
                "command": command,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": 1,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    else:
        # Regular command execution
        result = {
            "command": command,
            "stdout": "Regular command not supported in this test",
            "stderr": "",
            "exit_code": 0,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
        }
    
    # Print result
    print(f"{Fore.GREEN}Command completed in {result['execution_time']:.2f} seconds{Style.RESET_ALL}")
    if result.get("stdout"):
        print(f"{Fore.WHITE}Output: {result['stdout']}{Style.RESET_ALL}")
    if result.get("stderr"):
        print(f"{Fore.RED}Error: {result['stderr']}{Style.RESET_ALL}")
    
    return result

# Test all command types
print("\n1. Testing browser command...")
execute_ai_command("ai_browser:https://www.jiomart.com")
time.sleep(3)

print("\n2. Testing screenshot command...")
execute_ai_command("ai_screenshot:jiomart_test")
time.sleep(1)

print("\n3. Testing ask command...")
execute_ai_command("ai_ask:Do you see any snacks on the JioMart page?")
time.sleep(1)

print("\n4. Testing app command...")
execute_ai_command("ai_app:notepad.exe")
time.sleep(2)

print(f"\n{Fore.GREEN}All tests completed successfully!{Style.RESET_ALL}") 