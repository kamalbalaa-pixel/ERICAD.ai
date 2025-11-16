# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 12:23:58 2025

@author: kamal
"""

# sw_hotkey_screenshot.py

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
import win32con

MODEL_NAME = "gpt-5.1"
overlay_window = None

ERICAD_SYSTEM_PROMPT = ("""
You are ERICAD — an expert SolidWorks engineer and on-screen debugging companion.
You ALWAYS reason from the screenshot FIRST, and only then from the text.
You are helping a user fix SolidWorks problems step-by-step, with short, precise guidance.

====================================================
1) CORE IDENTITY & GOAL
====================================================

- You are a senior SolidWorks power user sitting behind the user.
- Your job: look at the screenshot, understand the exact UI + model state,
  pick the SINGLE best next step, and (optionally) highlight where to click.
- You must be concise, confident, and practical. No fluff, no AI disclaimers.

====================================================
2) ABSOLUTE VISUAL PRIORITY
====================================================

Treat the screenshot as the ONLY ground truth for UI state.

You MUST:
- Look carefully at visible tabs, buttons, icons, dialog boxes, feature tree, and graphics area.
- Infer the mode (sketch, feature edit, part, assembly, drawing) from what is visible.
- Only mention tools, tabs, icons, or dialogs that are actually visible OR that you are telling the user how to open.

You MUST NOT:
- Assume a default SolidWorks layout.
- Mention "Exit Sketch", "Sketch", "Features", or any ribbon button unless you see clear visual evidence OR you give explicit steps to navigate to it.
- Claim that a button is present when the pixels do not show it.

If you are not at least 80% sure about what you see, ask ONE short clarifying question instead of guessing.

====================================================
3) MODE DETECTION (STRICT)
====================================================

Before giving instructions, silently determine the current mode based ONLY on pixels:

- SKETCH EDIT:
  - Sketch entities (lines, arcs, dimensions) visible in the graphics area, AND
  - A sketch is selected / highlighted in the tree, OR
  - A "Sketch" confirmation bar or Exit Sketch–type controls are visible.

- FEATURE EDIT:
  - Feature-specific preview and feature dialog / PropertyManager is visible.

- PART MODE:
  - Single part feature tree, no mates folder, mostly solid body.

- ASSEMBLY MODE:
  - Multiple components / mates folder visible.

- DRAWING:
  - Sheet border, views, annotations, and drawing tree.

If you cannot confidently detect the mode, ask ONE short clarifying question and do NOT fabricate a mode.

====================================================
4) RESPONSE STRUCTURE (SHORT + ACTIONABLE)
====================================================

Your response has two parts:

(1) BRIEF VISUAL ANCHOR (1–2 sentences max)
    - Reference 1–2 key things you SEE that matter to the current step.
    - Example:
      "I see you're in part mode with a sketch visible, but you’re not currently editing that sketch."

(2) NEXT ACTION STEPS
    - Give the SINGLE most likely next step.
    - 2–5 short steps, each starting with a verb:
      - "Click the Sketch tab…"
      - "Right-click the sketch in the tree…"
      - "Press the green checkmark in the PropertyManager…"

Guidelines:
- Prefer one clean path, not multiple branches.
- Explain *why* very briefly only if helpful ("This exits sketch mode so you can apply the feature.").

====================================================
5) HIGHLIGHTING CONTRACT (CRITICAL)
====================================================

You can optionally return a JSON block to tell the overlay where to draw boxes.

Format (MUST MATCH EXACTLY WHEN YOU USE IT):

```json
{
  "highlights": [
    {
      "label": "Exit Sketch",
      "x0": 0.72,
      "y0": 0.10,
      "x1": 0.80,
      "y1": 0.16
    }
  ]
}
Rules:

Only include this JSON block if you genuinely want to highlight UI regions.

"highlights" MUST be a list. If you don’t want any boxes, use "highlights": [].

x0, y0, x1, y1 are normalized coordinates in [0.0, 1.0] relative to the screenshot you see:

(0.0, 0.0) = top-left corner of the screenshot

(1.0, 1.0) = bottom-right corner of the screenshot

NEVER use pixel coordinates. NEVER use values > 1.0 or < 0.0.

Boxes should be as tight as practical around the button or region, not half the toolbar.

If you are not at least 80% sure, set "highlights": [].

IMPORTANT:

The text of your answer should still make sense WITHOUT the JSON.

The JSON block must be syntactically valid and parseable by json.loads.

====================================================
6) MULTI-TURN CHAT BEHAVIOR
You are in a continuing chat about the SAME screenshot until the user captures a new one.

Use conversation history to keep track of what you already told them.

Do NOT repeat the whole diagnostic every message.

Do NOT use headings like "Visual summary:" or "Diagnosis:" after the first reply.

Flow naturally: refer back to what they just did ("Now that you’ve exited the sketch…").

====================================================
7) WHAT NOT TO DO
NEVER:

Invent tools, windows, or modes that are not visually supported.

Say you see buttons that are not clearly visible.

Dump long theory about SolidWorks.

Give 10 possible solutions; pick the best one.

Produce multiple different JSON blocks; if used, there should be ONE "highlights" object.

====================================================
8) PRIORITY
Your priorities, in order:

Be visually faithful to the screenshot.

Pick the single best next action.

Give short, concrete steps.

Use highlight JSON ONLY when you are confident and can localize a UI area.

If forced to choose between being visually correct and being generic-but-maybe-helpful,
ALWAYS choose to be visually correct.
"""
)

class OverlayWindow:
    """Transparent overlay window for drawing highlights on screen."""
    
    def __init__(self):
        self.root = None
        self.canvas = None
        self.highlights = []
        self.current_highlights = []
        self.current_index = 0
        self.running = False
        self.click_detected = False
        self.monitoring_clicks = False
        
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
        
        # Make window fullscreen and transparent
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='black')
        
        # Make window click-through
        self.root.wm_attributes('-transparentcolor', 'black')
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root, 
            bg='black', 
            highlightthickness=0,
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight()
        )
        self.canvas.pack()
        
        self.running = True
        self.root.after(100, self._update)
        self.root.mainloop()
        
    def _update(self):
        """Update the overlay display."""
        if self.running:
            if self.monitoring_clicks:
                self._check_for_click()
            self.root.after(100, self._update)
            
    def _check_for_click(self):
        """Check if mouse was clicked in the highlighted area."""
      if not self.current_highlights or self.current_index >= len(self.current_highlights):
          return
  
      # Left mouse button down
      if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
          x, y = win32api.GetCursorPos()
          screen_width = self.root.winfo_screenwidth()
          screen_height = self.root.winfo_screenheight()
  
          current = self.current_highlights[self.current_index]
          x0 = int(current['x0'] * screen_width)
          y0 = int(current['y0'] * screen_height)
          x1 = int(current['x1'] * screen_width)
          y1 = int(current['y1'] * screen_height)
  
          if x0 <= x <= x1 and y0 <= y <= y1:
              # Click detected in highlighted area
              self.click_detected = True
              self.root.after(500, self._next_highlight)
      
    def show_highlights_sequential(self, highlights):
      """Show highlights one at a time, waiting for clicks."""
      if not highlights or not self.running or not self.canvas:
          return

    # Get screen dimensions
      screen_width = self.root.winfo_screenwidth()
      screen_height = self.root.winfo_screenheight()

    # 🔥 Sanitize once and store
      self.current_highlights = sanitize_highlights(highlights, screen_width, screen_height)
      if not self.current_highlights:
          return

      self.current_index = 0
      self.monitoring_clicks = True

    # Show first highlight
      self._show_single_highlight(0)

        
    def _show_single_highlight(self, index):
      """Show a single highlight by index."""
      if index >= len(self.current_highlights):
        # All highlights shown
          self.monitoring_clicks = False
          if self.canvas:
              self.canvas.delete("all")
          return

      def draw():
          if not self.canvas:
              return

        # Clear previous highlights
          self.canvas.delete("all")

          screen_width = self.root.winfo_screenwidth()
          screen_height = self.root.winfo_screenheight()

        # Current highlight (already sanitized)
          h = self.current_highlights[index]
          x0 = int(h['x0'] * screen_width)
          y0 = int(h['y0'] * screen_height)
          x1 = int(h['x1'] * screen_width)
          y1 = int(h['y1'] * screen_height)

        # Draw rectangle
          self.canvas.create_rectangle(
              x0, y0, x1, y1,
              outline='red',
              width=3,
              tags="highlight"
          )
  
          # Draw label if exists
          if 'label' in h:
              self.canvas.create_text(
                  x0, y0 - 5,
                  text=h['label'],
                  fill='red',
                  anchor='sw',
                  font=('Arial', 12, 'bold'),
                  tags="highlight"
              )
  
          # Add step counter
          self.canvas.create_text(
              x1, y1 + 5,
              text=f"Step {index + 1} of {len(self.current_highlights)}",
              fill='yellow',
              anchor='ne',
              font=('Arial', 10),
              tags="highlight"
          )
  
      self.root.after(0, draw)
          
    def _next_highlight(self):
        """Move to the next highlight."""
        self.current_index += 1
        self._show_single_highlight(self.current_index)
        
    def show_highlights(self, highlights, duration=5):
        """Show all highlights at once for a specified duration (original method)."""
      if not self.running or not self.canvas or not highlights:
          return
  
      def draw():
          self.canvas.delete("all")
  
          screen_width = self.root.winfo_screenwidth()
          screen_height = self.root.winfo_screenheight()
  
          # 🔥 Sanitize list for all-at-once mode
          safe_highlights = sanitize_highlights(highlights, screen_width, screen_height)
  
          for h in safe_highlights:
              x0 = int(h['x0'] * screen_width)
              y0 = int(h['y0'] * screen_height)
              x1 = int(h['x1'] * screen_width)
              y1 = int(h['y1'] * screen_height)
  
              self.canvas.create_rectangle(
                  x0, y0, x1, y1,
                  outline='red',
                  width=3,
                  tags="highlight"
              )
  
              if 'label' in h:
                  self.canvas.create_text(
                      x0, y0 - 5,
                      text=h['label'],
                      fill='red',
                      anchor='sw',
                      font=('Arial', 12, 'bold'),
                      tags="highlight"
                  )
  
          self.root.after(duration * 1000, lambda: self.canvas.delete("highlight"))
  
      self.root.after(0, draw)
          
    def stop(self):
        """Stop the overlay window."""
        self.running = False
        if self.root:
            self.root.quit()




def sanitize_highlights(highlights, screen_width, screen_height):
    """Normalize and clamp highlight coordinates to [0,1], shrink boxes a bit."""
    sanitized = []

    for h in highlights:
        try:
            x0 = float(h.get("x0", 0.0))
            y0 = float(h.get("y0", 0.0))
            x1 = float(h.get("x1", 0.0))
            y1 = float(h.get("y1", 0.0))
        except (TypeError, ValueError):
            continue  # skip bad entries

        # Detect if these look like pixel coordinates
        # (arbitrary heuristic: anything > 2 is probably pixels, not normalized)
        max_val = max(x0, y0, x1, y1)
        if max_val > 2.0:
            # Convert from pixels -> normalized using screen size
            x0 /= screen_width
            x1 /= screen_width
            y0 /= screen_height
            y1 /= screen_height

        # Clamp to [0,1]
        x0 = max(0.0, min(1.0, x0))
        x1 = max(0.0, min(1.0, x1))
        y0 = max(0.0, min(1.0, y0))
        y1 = max(0.0, min(1.0, y1))

        # Ensure x0 <= x1, y0 <= y1
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0

        # Optional: shrink box around its center to avoid huge boxes
        shrink = 0.7  # 70% size of original
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        half_w = (x1 - x0) * shrink / 2.0
        half_h = (y1 - y0) * shrink / 2.0
        x0 = max(0.0, cx - half_w)
        x1 = min(1.0, cx + half_w)
        y0 = max(0.0, cy - half_h)
        y1 = min(1.0, cy + half_h)

        h_fixed = dict(h)
        h_fixed["x0"] = x0
        h_fixed["y0"] = y0
        h_fixed["x1"] = x1
        h_fixed["y1"] = y1

        sanitized.append(h_fixed)

    return sanitized

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

def capture_screen():
    """Capture the screen, save a timestamped PNG, and return its path."""
    desktop = get_desktop_path()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"solidworks_screenshot_{timestamp}.png"
    full_path = os.path.join(desktop, filename)

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=full_path)

    print(f"\n[✓] Screenshot saved: {full_path}")
    return full_path


def image_path_to_b64(image_path: str) -> str:
    """Read image from disk and return base64-encoded string."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Screenshot file not found at: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_highlights(ai_response: str) -> tuple:
    """Extract highlight JSON from AI response and return (clean_response, highlights)."""
    # Look for JSON block
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, ai_response, re.DOTALL)
    
    if match:
        try:
            json_str = match.group(1)
            highlight_data = json.loads(json_str)
            highlights = highlight_data.get('highlights', [])
            
            # Remove JSON block from response
            clean_response = ai_response[:match.start()] + ai_response[match.end():]
            clean_response = clean_response.strip()
            
            return clean_response, highlights
        except json.JSONDecodeError:
            print("[Warning] Could not parse highlight JSON")
            return ai_response, []
    
    return ai_response, []

def send_to_ai(
    b64_image: str,
    conversation_history: list,
    user_message: str,
) -> str:
    """
    Send screenshot + conversation + latest user message to ERICAD and return the reply.

    conversation_history is a list of (role, text) where role is "user" or "assistant".
    """

    # Build a compact text version of the conversation so far
    history_lines = []
    for role, text in conversation_history:
        prefix = "User:" if role == "user" else "ERICAD:"
        history_lines.append(f"{prefix} {text}")

    history_block = ""
    if history_lines:
        history_block = "Conversation so far:\n" + "\n".join(history_lines) + "\n\n"

    full_text = (
      history_block
      + "New user message:\n"
      + user_message
      + "\n\nYou MUST base your answer primarily on the screenshot, "
        "and only then on the text and conversation.\n"
        "If you choose to use highlights, you MUST return normalized "
        "coordinates in [0,1] as described in your instructions.\n"
)
    client = OpenAI()

    response = client.responses.create(
        model=MODEL_NAME,
        instructions=ERICAD_SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": full_text,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{b64_image}",
                    },
                ],
            }
        ],
    )

    return response.output_text


def handle_f8():
    """
    F8 handler: start a chat session tied to a single screenshot.

    You can send multiple messages until you type /done, /exit, or /new.
    """
    global overlay_window
    
    image_path = capture_screen()

    try:
        b64_image = image_path_to_b64(image_path)
    except Exception as e:
        print(f"\n[ERROR] Could not read screenshot: {e}")
        return

    conversation_history = []
    sequential_mode = True  # Default to sequential highlighting

    print(
        "\nERICAD chat session started for this screenshot."
        "\nType your question or description below."
        "\nCommands: /done, /exit, /new to end session"
        "\n         /mode to toggle between sequential and all-at-once highlighting"
        "\n"
    )

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ("/done", "/exit", "/new"):
            print("\n[✓] Ending ERICAD session for this screenshot.")
            print("[Hint] Press F8 to start a new session, or F9 to quit.\n")
            break

        if user_message.lower() == "/mode":
            sequential_mode = not sequential_mode
            mode = "sequential" if sequential_mode else "all at once"
            print(f"[✓] Highlighting mode changed to: {mode}\n")
            continue

        if not user_message:
            # ignore blank lines
            continue

        try:
            ai_response = send_to_ai(b64_image, conversation_history, user_message)
        except Exception as e:
            print("\n[ERROR] Something went wrong talking to ERICAD:")
            print(e)
            break

        # Extract highlights from response
        clean_response, highlights = extract_highlights(ai_response)

        # Update conversation history with clean response
        conversation_history.append(("user", user_message))
        conversation_history.append(("assistant", clean_response))

        print("\nERICAD:\n")
        print(clean_response)
        print("\n-----------------------------\n")

        # Show highlights if any
        if highlights and overlay_window:
            if sequential_mode and len(highlights) > 1:
                print("[Highlighting steps sequentially - click each highlighted button to proceed]")
                overlay_window.show_highlights_sequential(highlights)
            else:
                overlay_window.show_highlights(highlights, duration=5)


def main():
    global overlay_window
    
    print("ERICAD Hotkey Tool Running (Chat Mode)")
    print("Press F8 to capture + start a chat for that screenshot.")
    print("Inside a session, type /done to end it.")
    print("Press F9 to quit the program.\n")
    
    # Initialize overlay window
    overlay_window = OverlayWindow()
    overlay_window.start()

    keyboard.add_hotkey("F8", handle_f8)

    # Wait until F9 is pressed
    keyboard.wait("F9")
    
    # Clean up
    if overlay_window:
        overlay_window.stop()
    
    print("\n[✓] Quitting ERICAD...")
    raise SystemExit

if __name__ == "__main__":
    main()
