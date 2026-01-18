# modules/windows_bot.py
import pyautogui
import time
import os
import cv2
import numpy as np
from pywinauto import Desktop

class WindowsBot:
    def __init__(self):
        print("🤖 VISION BOT: Ready (Local Template Matching).")
        
        # 1. Setup the path to your screenshot
        # We use absolute paths to fix the "File Not Found" error you had earlier
        current_folder = os.path.dirname(os.path.abspath(__file__))
        self.eye_path = os.path.join(current_folder, "eye_icon.png")
        
        # Debug: Tell you exactly where it is looking
        print(f"   -> Reference Image Path: {self.eye_path}")

    def find_and_click_image(self, target_image_path):
        """
        Takes a screenshot of the screen and finds the target image inside it.
        Returns (x, y) coordinates if found, or None if not found.
        """
        # A. verify target exists
        if not os.path.exists(target_image_path):
            print("   -> ERROR: 'eye_icon.png' is missing from the modules folder!")
            return None

        # B. Take a screenshot of the screen (in memory)
        screenshot = pyautogui.screenshot()
        
        # C. Convert images for OpenCV
        # Convert screenshot to numpy array (RGB) -> BGR (for OpenCV)
        screen_np = np.array(screenshot)
        screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        
        # Load the target image in grayscale
        template = cv2.imread(target_image_path, 0)
        if template is None:
            return None
            
        # D. Match Template
        # This scans the large image (screen) for the small image (eye)
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        
        # Define how picky we are (0.8 = 80% match required)
        threshold = 0.8
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # We found a match! Calculate center point.
            template_h, template_w = template.shape
            top_left = max_loc
            center_x = top_left[0] + template_w // 2
            center_y = top_left[1] + template_h // 2
            return (center_x, center_y)
        
        return None

    def click_smart(self, app_title, user_command):
        try:
            # 1. Focus SolidWorks
            try:
                app = Desktop(backend="uia").window(title_re=f".*{app_title}.*")
                if not app.exists(): return False, "SolidWorks is not open."
                app.set_focus()
            except:
                return False, "Could not focus SolidWorks."

            time.sleep(0.2)
            
            # 2. Reset Mouse (Safe Zone)
            pyautogui.moveTo(10, 10)
            
            # 3. Open Search & Type
            pyautogui.press('w')
            time.sleep(0.01)
            pyautogui.write(user_command, interval=0.01)
            
            # 4. Wait for the list and Eye to appear
            print("   -> Waiting for search results...")
            time.sleep(0.5) 
            
            # 5. VISION SCAN
            print("   -> 📷 Scanning screen for Eye icon...")
            coords = self.find_and_click_image(self.eye_path)
            
            if coords:
                print(f"   -> 🎯 Found Eye at {coords}. Clicking.")
                pyautogui.moveTo(coords[0], coords[1])
                pyautogui.click()
                return True, f"Showing location of '{user_command}'."
            else:
                print("   -> 🤷 Eye not found (Match % was too low). Pressing Enter.")
                pyautogui.press('enter')
                return True, f"Executed '{user_command}' via Enter."

        except Exception as e:
            return False, f"Error: {e}"