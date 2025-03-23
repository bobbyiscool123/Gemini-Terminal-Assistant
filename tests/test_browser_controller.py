import os
import sys
import time
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.append(str(Path(__file__).parent.parent))

try:
    from terminal_ai_assistant import WebBrowserController
    print("WebBrowserController imported successfully!")
except ImportError as e:
    print(f"Error importing WebBrowserController: {e}")
    sys.exit(1)

def test_browser_navigation():
    """Test basic browser navigation"""
    print("Testing WebBrowserController navigation...")
    
    # Create browser controller
    browser = WebBrowserController(browser_type='chrome')
    
    try:
        # Initialize the browser
        if not browser.initialize():
            print("Browser initialization failed. Trying with default browser instead.")
        
        # Test navigation to JioMart
        print("Navigating to JioMart...")
        browser.navigate("https://www.jiomart.com")
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Take a screenshot
        print("Taking screenshot...")
        screenshot_path = browser.take_screenshot("jiomart_homepage_test.png")
        if screenshot_path:
            print(f"Screenshot saved to: {screenshot_path}")
        
        # Look for search box
        print("Finding search box...")
        search_box = browser.find_element("input#search", timeout=5)
        if search_box:
            print("Search box found!")
            
            # Type "snacks" into search box
            print("Typing 'snacks' into search box...")
            browser.fill_input("input#search", "snacks")
            
            # Wait a moment
            time.sleep(2)
            
            # Take another screenshot
            print("Taking screenshot after typing...")
            browser.take_screenshot("jiomart_search_test.png")
        else:
            print("Search box not found. The site structure might have changed.")
            
        # Test complete
        print("Test completed! Closing browser...")
        time.sleep(3)
    finally:
        # Close the browser
        browser.close()

if __name__ == "__main__":
    test_browser_navigation() 