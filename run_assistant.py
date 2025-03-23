#!/usr/bin/env python3
"""
Terminal AI Assistant Launcher
A menu-based launcher for the Terminal AI Assistant
"""
import os
import sys
import platform
import time
from colorama import init, Fore, Style
import subprocess

# Initialize colorama for cross-platform colored terminal output
init()

def clear_screen():
    """Clear the terminal screen based on the operating system"""
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def load_config():
    """Load configuration settings from config.yaml if available"""
    try:
        import yaml
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.RED}Error loading config: {str(e)}{Style.RESET_ALL}")
    
    # Default configuration
    return {
        "terminal_preferences": {
            "theme": "default",
            "timeout": 30
        }
    }

def display_menu():
    """Display the main menu"""
    clear_screen()
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'Terminal AI Assistant Launcher':^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}Please select an option:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Start Terminal AI Assistant")
    print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Check for Dependencies")
    print(f"{Fore.YELLOW}3.{Style.RESET_ALL} View README")
    print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Exit")
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print(f"{Fore.CYAN}Checking dependencies...{Style.RESET_ALL}")
    
    # List of required packages from requirements.txt
    required_packages = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                package = line.strip().split('==')[0]
                if package and not package.startswith('#'):
                    required_packages.append(package)
    except FileNotFoundError:
        print(f"{Fore.RED}requirements.txt not found!{Style.RESET_ALL}")
        return False
    
    # Check each package
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"{Fore.GREEN}✓ {package} is installed{Style.RESET_ALL}")
        except ImportError:
            missing_packages.append(package)
            print(f"{Fore.RED}✗ {package} is missing{Style.RESET_ALL}")
    
    if missing_packages:
        print(f"\n{Fore.YELLOW}Some dependencies are missing. Install them with:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}pip install -r requirements.txt{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.GREEN}All dependencies are installed!{Style.RESET_ALL}")
    return True

def view_readme():
    """View the README file if it exists"""
    if os.path.exists("README.md"):
        try:
            with open("README.md", "r") as f:
                content = f.read()
            
            # Simple markdown to terminal formatting
            print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'README':^60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
            
            # Very basic markdown parsing
            for line in content.split('\n'):
                if line.startswith('# '):
                    print(f"{Fore.MAGENTA}{line[2:]}{Style.RESET_ALL}")
                elif line.startswith('## '):
                    print(f"{Fore.YELLOW}{line[3:]}{Style.RESET_ALL}")
                elif line.startswith('### '):
                    print(f"{Fore.GREEN}{line[4:]}{Style.RESET_ALL}")
                elif line.startswith('- '):
                    print(f"{Fore.CYAN}•{Style.RESET_ALL} {line[2:]}")
                else:
                    print(line)
            
            print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error reading README: {str(e)}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}README.md not found!{Style.RESET_ALL}")
    
    input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")

def start_assistant():
    """Start the Terminal AI Assistant"""
    print("Starting Terminal AI Assistant...")
    # First make sure terminal_ai_assistant.py exists
    if not os.path.exists("terminal_ai_assistant.py"):
        print(f"{Fore.RED}Error: terminal_ai_assistant.py not found!{Style.RESET_ALL}")
        return
    
    # Ensure the logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Start the assistant with proper terminal detection
    try:
        # Use subprocess instead of os.system for better handling
        subprocess.run([sys.executable, "terminal_ai_assistant.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error running Terminal AI Assistant: {e}{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}Terminal AI Assistant stopped by user.{Style.RESET_ALL}")

def main():
    """Main function to run the launcher"""
    config = load_config()
    
    while True:
        display_menu()
        choice = input(f"\n{Fore.GREEN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            start_assistant()
        elif choice == '2':
            check_dependencies()
            input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Style.RESET_ALL}")
        elif choice == '3':
            view_readme()
        elif choice == '4':
            print(f"\n{Fore.YELLOW}Exiting... Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"\n{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Program interrupted. Exiting...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")
        input("Press Enter to exit...") 