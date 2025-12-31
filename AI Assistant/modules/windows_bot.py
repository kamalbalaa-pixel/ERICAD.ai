# modules/windows_bot.py
import pyautogui
import time
from pywinauto import Desktop

class WindowsBot:
    def __init__(self):
        print("🤖 WIN BOT: Ready (Universal Mode + Center Snap).")

    def click_smart(self, app_title, user_command):
        try:
            # 1. Focus SolidWorks
            try:
                # Finds the window even if the title is slightly different
                app = Desktop(backend="uia").window(title_re=f".*{app_title}.*")
                if not app.exists():
                    return False, "SolidWorks is not open."
                app.set_focus()
            except:
                return False, "Could not focus SolidWorks."

            time.sleep(0.2)
            
            # 2. Get Screen Size (So we know where the center is)
            screen_width, screen_height = pyautogui.size()

            # 3. SAFE ZONE: Move mouse to top-left (10, 10)
            # This prevents hovering over buttons that might steal focus
            pyautogui.moveTo(10, 10)
            
            # 4. Open Command Search
            pyautogui.press('w')
            time.sleep(0.1) 
            
            # 5. Type the command
            pyautogui.write(user_command, interval=0.05)
            time.sleep(0.5) # Wait for list to populate
            
            # 6. Execute (Press Enter)
            pyautogui.press('enter')
            
            # 7. CENTER SNAP (The Feature You Wanted)
            # Immediately jump mouse to the center of the screen
            pyautogui.moveTo(screen_width / 2, screen_height / 2)
            
            return True, f"Executed '{user_command}'."

        except Exception as e:
            return False, f"Error: {e}"