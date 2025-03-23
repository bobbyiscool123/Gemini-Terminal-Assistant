import os
import time
import webbrowser
import pyautogui
from terminal_ai_assistant import TaskStructure

# Create a simple test task for JioMart
task = TaskStructure("go to browser and into jio mart and add some snacks to the cart")

# Force create the JioMart fallback phases
task.create_fallback_phases()

print("JioMart fallback phases created:")
for i, phase in enumerate(task.phases):
    print(f"Phase {i+1}: {phase['name']}")
    for j, step in enumerate(phase['steps']):
        print(f"  Step {j+1}: {step['name']}")
        for k, mini_step in enumerate(step['mini_steps']):
            cmd = mini_step.get('command', 'No command')
            print(f"    Mini-step {k+1}: {mini_step['name']} - {cmd}")

# Test executing the first command (opening JioMart)
print("\nTesting browser opening command...")
first_phase = task.phases[0]
first_step = first_phase['steps'][0]
first_mini_step = first_step['mini_steps'][0]
command = first_mini_step.get('command')

if command and command.startswith("ai_browser:"):
    url = command.split("ai_browser:", 1)[1].strip()
    print(f"Opening browser to URL: {url}")
    webbrowser.open(url)
    
    # Wait for browser to load
    time.sleep(5)
    
    # Take a screenshot
    print("Taking screenshot...")
    os.makedirs("screenshots", exist_ok=True)
    screenshot_path = f"screenshots/jiomart_test_{int(time.time())}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

print("\nTest completed successfully!") 