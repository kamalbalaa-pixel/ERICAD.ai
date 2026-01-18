import easyocr
import pyautogui
import numpy as np

class Eyes:
    def __init__(self):
        print("👀 EYES: Loading Vision Model... (One moment)")
        # 'en' = English. gpu=False is safer if you don't have CUDA setup.
        self.reader = easyocr.Reader(['en'], gpu=False)

    def find_text_coordinates(self, target_text):
        print(f"👀 EYES: Scanning screen for '{target_text}'...")
        
        # 1. Take Screenshot
        screenshot = pyautogui.screenshot()
        image_np = np.array(screenshot)
        
        # 2. Read Text
        results = self.reader.readtext(image_np)
        
        # 3. Find Match
        for (bbox, text, prob) in results:
            if target_text.lower() in text.lower():
                # bbox = [[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]]
                top_left = bbox[0]
                bottom_right = bbox[2]
                
                # Calculate Center
                center_x = int((top_left[0] + bottom_right[0]) / 2)
                center_y = int((top_left[1] + bottom_right[1]) / 2)
                
                return (center_x, center_y)
        
        return None