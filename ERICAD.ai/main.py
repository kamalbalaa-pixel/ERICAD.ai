import sys
import os
from PyQt5.QtWidgets import QApplication
import config
from recorder import FlightRecorder
from ai_client import GeminiClient
from overlay_ui import EricadOverlay

# --- CRITICAL SYSTEM FIXES ---
# 1. Fix OpenMP Conflict (Common in Anaconda)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 2. Fix High DPI Scaling (Prevents drawing offset)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

def main():
    print("Initializing ERICAD v1...")
    
    # 1. Start QT App
    app = QApplication(sys.argv)
    
    # 2. Initialize Backend Systems
    try:
        recorder = FlightRecorder()
        recorder.start()
        
        ai_client = GeminiClient()
        
        # 3. Launch UI
        window = EricadOverlay(recorder, ai_client)
        window.show()
        
        print("ERICAD is running. Press Ctrl+C in console to force quit if needed.")
        
        # This line starts the app loop and waits here until you close the window
        sys.exit(app.exec_())
        
    except Exception as e:
        # This block catches any errors during startup
        print(f"Critical Startup Error: {e}")
        
        # Ensure recorder stops if app crashes
        if 'recorder' in locals():
            recorder.stop()

if __name__ == "__main__":
    main()