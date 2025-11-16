# -*- coding: utf-8 -*-
"""
Improved SolidWorks Tutorial Assistant
Author: Enhanced version with better accuracy and auto-screenshot features
"""

import os
import datetime
import mss
import mss.tools
import keyboard
import base64 
from openai import OpenAI
import json
import re
import tkinter as tk
import win32gui
import win32con
import threading
import time
import win32api
from PIL import Image
import io
from typing import Optional, Tuple, List, Dict

MODEL_NAME = "gpt-4o"  # Using GPT-4o for better visual understanding
overlay_window = None
current_screenshot_data = None  # Store screenshot in memory

ERICAD_SYSTEM_PROMPT = (
"""
You are ERICAD — an expert SolidWorks engineer and on-screen debugging companion. 
Your job is to look at the user's screenshot, understand the exact SolidWorks state, 
and guide them step-by-step with precise, grounded instructions. 
Your tone is concise, confident, fluent, and calm — like a senior CAD mentor.

====================================================
CORE BEHAVIOR
====================================================

1) MULTI-TURN CHAT
You are in an ongoing conversation. 
- The FIRST message you send in a new session may be structured.
- AFTER the first message, your responses must be NATURAL and conversational. 
- Do NOT repeat headings like "Visual summary" or "Diagnosis" in multi-turn chat.
- Adapt based on what the user just did or asked.

2) VISUAL GROUNDING (REQUIRED)
You MUST base your reasoning on what you SEE in the screenshot.  
Never ignore the image. Never assume tools or buttons that are not visible.

At the start of every response, briefly state 1–2 visually obvious things you see 
that matter for the current step.

3) SOLIDWORKS MODE DETECTION
Before giving instructions, determine the user's actual mode:
- editing a sketch
- editing a feature
- part modeling mode
- assembly mode
- drawing mode
- or not editing anything

4) ACTIONABLE GUIDANCE WITH PRECISE HIGHLIGHTS
Your job is to tell the user the SINGLE most likely next step.
- Give a short explanation (1–2 sentences max).
- Then give 2–5 precise steps, each starting with a verb.
- Include ACCURATE highlight coordinates for clickable elements.

5) HIGHLIGHT JSON FORMAT (CRITICAL FOR ACCURACY)
When providing highlights, be VERY PRECISE with coordinates.
Look at the exact pixel location of buttons/elements in the screenshot.
Use normalized coordinates (0.0 to 1.0) where:
- x0, y0 = top-left corner
- x1, y1 = bottom-right corner
- Coordinates are relative to screen dimensions (0,0 is top-left, 1,1 is bottom-right)

IMPORTANT: Make highlight boxes TIGHT around the actual UI element, with just 2-3 pixels padding.
Don't make boxes too large - they should precisely frame the clickable area.

Example format:
```json
{
  "highlights": [
    { 
      "label": "Sketch button", 
      "x0": 0.320,  // Be precise to 3 decimal places
      "y0": 0.205, 
      "x1": 0.385, 
      "y1": 0.245
    }
  ]
}
```

6) NO HALLUCINATIONS
You must NEVER:
- Invent tools, buttons, tabs, or commands not visible.
- Give instructions to click something not in the screenshot.

7) FLUENCY & PERSONA
- Write like a calm, experienced CAD engineer.
- Be brief but highly fluent.
- No filler phrases.
"""    
)

class ScreenshotManager:
    """Manages screenshots in memory without saving to disk."""
    
    def __init__(self):
        self.current_screenshot = None
        self.screenshot_bytes = None
        self.screenshot_base64 = None
        self.screenshot_dimensions = None
        
    def capture_screen(self) -> str:
        """Capture the screen and store in memory, return base64 string."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            # Store dimensions
            self.screenshot_dimensions = screenshot.size
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Store in memory
            self.screenshot_bytes = img_byte_arr
            self.current_screenshot = img
            
            # Convert to base64
            self.screenshot_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            print(f"\n[✓] Screenshot captured (in memory only)")
            return self.screenshot_base64
    
    def save_to_disk(self, path: Optional[str] = None) -> str:
        """Save the current screenshot to disk if needed."""
        if self.screenshot_bytes is None:
            raise ValueError("No screenshot in memory to save")
            
        if path is None:
            desktop = get_desktop_path()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"solidworks_screenshot_{timestamp}.png"
            path = os.path.join(desktop, filename)
            
        with open(path, 'wb') as f:
            f.write(self.screenshot_bytes)
            
        print(f"[✓] Screenshot saved to: {path}")
        return path

class EnhancedOverlayWindow:
    """Enhanced overlay window with better accuracy and click detection."""
    
    def __init__(self, screenshot_manager: ScreenshotManager):
        self.root = None
        self.canvas = None
        self.highlights = []
        self.current_highlights = []
        self.current_index = 0
        self.running = False
        self.click_callback = None
        self.monitoring_clicks = False
        self.screenshot_manager = screenshot_manager
        self.screen_width = 0
        self.screen_height = 0
        self.click_cooldown = False
        self.highlight_rectangles = []  # Store rectangle IDs for better management
        
    def start(self):
        """Start the overlay window in a separate thread."""
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.5)  # Give the window time to initialize
        
    def _run(self):
        """Run the tkinter window."""
        self.root = tk.Tk()
        self.root.title('ERICAD Overlay')
        
        # Get actual screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Make window fullscreen and transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.4)  # Slightly more visible for better accuracy
        self.root.configure(bg='black')
        
        # Make window click-through
        self.root.wm_attributes('-transparentcolor', 'black')
        
        # Create canvas with exact screen dimensions
        self.canvas = tk.Canvas(
            self.root, 
            bg='black', 
            highlightthickness=0,
            width=self.screen_width,
            height=self.screen_height
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for better click detection
        self.root.bind('<Button-1>', self._on_click)
        
        self.running = True
        self.root.after(50, self._update)  # Faster update rate
        self.root.mainloop()
        
    def _update(self):
        """Update the overlay display."""
        if self.running:
            self.root.after(50, self._update)
            
    def _on_click(self, event):
        """Handle mouse click events."""
        if not self.monitoring_clicks or self.click_cooldown:
            return
            
        # Check if click is within any current highlight
        mouse_x, mouse_y = win32api.GetCursorPos()
        
        for i, highlight in enumerate(self.current_highlights):
            x0 = int(highlight['x0'] * self.screen_width)
            y0 = int(highlight['y0'] * self.screen_height)
            x1 = int(highlight['x1'] * self.screen_width)
            y1 = int(highlight['y1'] * self.screen_height)
            
            # Add small tolerance for click detection
            tolerance = 5
            if (x0 - tolerance <= mouse_x <= x1 + tolerance and 
                y0 - tolerance <= mouse_y <= y1 + tolerance):
                
                print(f"\n[✓] Clicked on: {highlight.get('label', 'element')}")
                
                # Set cooldown to prevent multiple triggers
                self.click_cooldown = True
                self.root.after(1000, self._reset_cooldown)
                
                # Clear current highlights
                self.canvas.delete("all")
                
                # Trigger callback if set
                if self.click_callback:
                    self.click_callback(i, highlight)
                
                # Move to next set of highlights or end
                if i == len(self.current_highlights) - 1:
                    self.monitoring_clicks = False
                    self.current_highlights = []
                    print("[✓] All steps completed for this instruction")
                
                break
    
    def _reset_cooldown(self):
        """Reset the click cooldown."""
        self.click_cooldown = False
    
    def show_highlights_sequential(self, highlights, callback=None):
        """Show highlights and wait for clicks, with automatic screenshot on click."""
        if not highlights:
            return
            
        self.current_highlights = highlights
        self.current_index = 0
        self.monitoring_clicks = True
        self.click_callback = callback
        
        # Show all highlights at once for better visibility
        self._show_all_highlights(highlights)
        
    def _show_all_highlights(self, highlights):
        """Show all highlights at once with labels."""
        def draw():
            # Clear previous highlights
            self.canvas.delete("all")
            self.highlight_rectangles = []
            
            # Draw all highlights
            for i, h in enumerate(highlights):
                x0 = int(h['x0'] * self.screen_width)
                y0 = int(h['y0'] * self.screen_height)
                x1 = int(h['x1'] * self.screen_width)
                y1 = int(h['y1'] * self.screen_height)
                
                # Make sure coordinates are valid
                x0, x1 = min(x0, x1), max(x0, x1)
                y0, y1 = min(y0, y1), max(y0, y1)
                
                # Draw rectangle with better visibility
                rect_id = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline='#FF0000',  # Bright red
                    width=3,
                    tags=f"highlight_{i}"
                )
                self.highlight_rectangles.append(rect_id)
                
                # Draw a semi-transparent fill for better visibility
                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill='#FF0000',
                    stipple='gray25',  # Creates a semi-transparent effect
                    outline='',
                    tags=f"highlight_fill_{i}"
                )
                
                # Draw label with better positioning and visibility
                if 'label' in h:
                    # Background for text
                    text_id = self.canvas.create_text(
                        x0 + 5, y0 - 20,
                        text=f"{i+1}. {h['label']}",
                        fill='white',
                        anchor='nw',
                        font=('Arial', 14, 'bold'),
                        tags=f"label_{i}"
                    )
                    
                    # Get text bounds and draw background
                    bbox = self.canvas.bbox(text_id)
                    if bbox:
                        self.canvas.create_rectangle(
                            bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,
                            fill='red',
                            outline='',
                            tags=f"label_bg_{i}"
                        )
                        # Raise text to front
                        self.canvas.tag_raise(text_id)
            
        self.root.after(0, draw)
        
    def show_highlights(self, highlights, duration=5):
        """Show all highlights at once for a duration."""
        if not highlights:
            return
            
        self.current_highlights = highlights
        self._show_all_highlights(highlights)
        
        # Schedule removal
        self.root.after(duration * 1000, lambda: self.canvas.delete("all"))
        
    def clear_highlights(self):
        """Clear all current highlights."""
        if self.canvas:
            self.canvas.delete("all")
        self.current_highlights = []
        self.monitoring_clicks = False
        
    def stop(self):
        """Stop the overlay window."""
        self.running = False
        if self.root:
            self.root.quit()

def get_desktop_path() -> str:
    """Return your Desktop path (normal or OneDrive)."""
    candidates = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        os.path.join(os.path.expanduser("~"), "OneDrive - Personal", "Desktop"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise RuntimeError("Could not find your Desktop folder.")

def extract_highlights(ai_response: str) -> Tuple[str, List[Dict]]:
    """Extract highlight JSON from AI response with better parsing."""
    # Look for JSON block
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, ai_response, re.DOTALL)
    
    if match:
        try:
            json_str = match.group(1)
            highlight_data = json.loads(json_str)
            highlights = highlight_data.get('highlights', [])
            
            # Validate and clean highlight coordinates
            cleaned_highlights = []
            for h in highlights:
                if all(k in h for k in ['x0', 'y0', 'x1', 'y1']):
                    # Ensure coordinates are within bounds
                    h['x0'] = max(0, min(1, float(h['x0'])))
                    h['y0'] = max(0, min(1, float(h['y0'])))
                    h['x1'] = max(0, min(1, float(h['x1'])))
                    h['y1'] = max(0, min(1, float(h['y1'])))
                    cleaned_highlights.append(h)
            
            # Remove JSON block from response
            clean_response = ai_response[:match.start()] + ai_response[match.end():]
            clean_response = clean_response.strip()
            
            return clean_response, cleaned_highlights
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[Warning] Could not parse highlight JSON: {e}")
            return ai_response, []
    
    return ai_response, []

def send_to_ai(
    b64_image: str,
    conversation_history: list,
    user_message: str,
) -> str:
    """Send screenshot + conversation + latest user message to AI."""
    
    # Build conversation context
    history_lines = []
    for role, text in conversation_history[-10:]:  # Keep last 10 exchanges for context
        prefix = "User:" if role == "user" else "ERICAD:"
        history_lines.append(f"{prefix} {text}")

    history_block = ""
    if history_lines:
        history_block = "Recent conversation:\n" + "\n".join(history_lines) + "\n\n"

    full_text = (
        history_block
        + "New user message:\n"
        + user_message
        + "\n\nUse the screenshot to provide precise guidance."
        + "\n\nIMPORTANT: Include accurate highlight JSON with precise coordinates for any UI elements you reference."
        + "\nMake the highlight boxes TIGHT around the actual buttons/elements with minimal padding."
    )

    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ERICAD_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": full_text},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{b64_image}"
                    }}
                ]}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] AI request failed: {e}")
        return "Sorry, I couldn't process the screenshot. Please try again."

def handle_f8():
    """F8 handler: start a chat session with automatic screenshot updates."""
    global overlay_window, current_screenshot_data
    
    # Initialize screenshot manager
    screenshot_manager = ScreenshotManager()
    
    # Capture initial screenshot
    b64_image = screenshot_manager.capture_screen()
    current_screenshot_data = b64_image
    
    # Initialize or reset overlay
    if overlay_window:
        overlay_window.stop()
    overlay_window = EnhancedOverlayWindow(screenshot_manager)
    overlay_window.start()
    
    conversation_history = []
    auto_screenshot = True  # Enable automatic screenshots by default
    
    # Define callback for when highlights are clicked
    def on_highlight_click(index, highlight):
        nonlocal b64_image
        global current_screenshot_data
        if auto_screenshot:
            print(f"[✓] Taking new screenshot after clicking {highlight.get('label', 'element')}...")
            time.sleep(0.5)  # Small delay to let UI update
            b64_image = screenshot_manager.capture_screen()
            current_screenshot_data = b64_image
    
    print(
        "\n" + "="*60
        + "\nERICAD Tutorial Assistant - Enhanced Version"
        + "\n" + "="*60
        + "\n\n📸 Screenshot captured! Chat session started."
        + "\n\nCommands:"
        + "\n  /done, /exit  - End this session"
        + "\n  /auto         - Toggle automatic screenshot on click (currently ON)"
        + "\n  /save         - Save current screenshot to desktop"
        + "\n  /new          - Take a new screenshot manually"
        + "\n  /clear        - Clear all highlights"
        + "\n\nType your question or describe what you want to create:"
        + "\n"
    )

    while True:
        user_message = input("\n💬 You: ").strip()

        if user_message.lower() in ("/done", "/exit"):
            overlay_window.clear_highlights()
            print("\n[✓] Session ended. Press F8 for a new session, or F9 to quit.\n")
            break
            
        if user_message.lower() == "/auto":
            auto_screenshot = not auto_screenshot
            status = "ON" if auto_screenshot else "OFF"
            print(f"[✓] Automatic screenshot on click is now: {status}\n")
            continue
            
        if user_message.lower() == "/save":
            try:
                path = screenshot_manager.save_to_disk()
                print(f"[✓] Screenshot saved to: {path}\n")
            except Exception as e:
                print(f"[ERROR] Could not save screenshot: {e}\n")
            continue
            
        if user_message.lower() == "/new":
            b64_image = screenshot_manager.capture_screen()
            current_screenshot_data = b64_image
            print("[✓] New screenshot captured\n")
            continue
            
        if user_message.lower() == "/clear":
            overlay_window.clear_highlights()
            print("[✓] Highlights cleared\n")
            continue

        if not user_message:
            continue

        try:
            print("\n🤔 ERICAD is analyzing...")
            ai_response = send_to_ai(b64_image, conversation_history, user_message)
        except Exception as e:
            print(f"\n[ERROR] Failed to get AI response: {e}")
            continue

        # Extract highlights from response
        clean_response, highlights = extract_highlights(ai_response)

        # Update conversation history
        conversation_history.append(("user", user_message))
        conversation_history.append(("assistant", clean_response))

        print("\n🤖 ERICAD:\n")
        print("─" * 40)
        print(clean_response)
        print("─" * 40)

        # Show highlights if any
        if highlights:
            print(f"\n[✓] Highlighting {len(highlights)} element(s) on screen")
            print("[!] Click the highlighted areas to proceed")
            if auto_screenshot:
                print("[!] A new screenshot will be taken after each click")
            
            overlay_window.show_highlights_sequential(
                highlights, 
                callback=on_highlight_click if auto_screenshot else None
            )
        else:
            print("\n[Note] No UI elements to highlight in this response")

def main():
    global overlay_window
    
    print("\n" + "="*60)
    print(" ERICAD - Enhanced SolidWorks Tutorial Assistant")
    print("="*60)
    print("\n📌 Features:")
    print("  • Better highlight accuracy with precise coordinate mapping")
    print("  • Automatic screenshot capture when you click highlighted areas")
    print("  • Screenshots kept in memory (not saved unless requested)")
    print("  • Multi-step guidance with sequential highlighting")
    print("\n🎮 Controls:")
    print("  • Press F8 to start a tutorial session")
    print("  • Press F9 to quit the program")
    print("\n" + "="*60 + "\n")

    keyboard.add_hotkey("F8", handle_f8)

    # Wait until F9 is pressed
    keyboard.wait("F9")
    
    # Clean up
    if overlay_window:
        overlay_window.stop()
    
    print("\n[✓] ERICAD shut down successfully.")
    raise SystemExit

if __name__ == "__main__":
    main()
