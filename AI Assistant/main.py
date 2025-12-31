# main.py
from modules.mouth import Mouth
from modules.windows_bot import WindowsBot
from modules.eyes import Eyes
from modules.hands import Hands

def start_app():
    mouth = Mouth()
    win_bot = WindowsBot() # Specialist for SolidWorks
    eyes = Eyes()          # Specialist for reading screen text
    hands = Hands()        # Specialist for clicking pixels

    mouth.speak("System Ready. I can control SolidWorks via Search AND click text on screen.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit": 
            mouth.speak("Goodbye!")
            break

        if user_input.lower().startswith("click"):
            target = user_input[6:].strip()
            
            # --- STRATEGY 1: Try SolidWorks Search First ---
            # This is the "Zero Error" method for CAD commands
            mouth.speak(f"Running command: '{target}'...")
            sw_success, sw_message = win_bot.click_smart("SOLIDWORKS", target)
            
            if sw_success:
                mouth.speak(sw_message)
            
            # --- STRATEGY 2: Visual Fallback ---
            # If SolidWorks didn't work (or wasn't open), look for text on screen
            else:
                mouth.speak("Not a SolidWorks command. Scanning screen for text...")
                coords = eyes.find_text_coordinates(target)
                
                if coords:
                    hands.click_at(coords[0], coords[1])
                    mouth.speak(f"Clicked text '{target}'.")
                else:
                    mouth.speak(f"I could not find '{target}' in SolidWorks or on the screen.")

if __name__ == "__main__":
    start_app()