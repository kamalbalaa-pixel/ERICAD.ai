# modules/hands.py
import pyautogui
import time

class Hands:
    def click_at(self, x, y):
        # Save current position
        original_x, original_y = pyautogui.position()
        
        # Move and Click
        pyautogui.moveTo(x, y)
        pyautogui.click()
        
        # Optional: Return mouse to original position? 
        # Uncomment next line if you want that:
        # pyautogui.moveTo(original_x, original_y)clic