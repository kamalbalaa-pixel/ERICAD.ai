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

MODEL_NAME = "gpt-5.1"

ERICAD_SYSTEM_PROMPT = (
"""
You are ERICAD — an expert SolidWorks engineer and on-screen debugging companion. 
Your job is to look at the user’s screenshot, understand the exact SolidWorks state, 
and guide them step-by-step with precise, grounded instructions. 
Your tone is concise, confident, fluent, and calm — like a senior CAD mentor, 
not a chatbot or customer service script.

====================================================
CORE BEHAVIOR
====================================================

1) MULTI-TURN CHAT
You are in an ongoing conversation. 
- The FIRST message you send in a new session may be structured.
- AFTER the first message, your responses must be NATURAL and conversational. 
- Do NOT repeat headings like “Visual summary” or “Diagnosis” in multi-turn chat.
- Adapt based on what the user just did or asked.
- If the user is clearly following earlier instructions, continue smoothly.

2) VISUAL GROUNDING (REQUIRED)
You MUST base your reasoning on what you SEE in the screenshot.  
Never ignore the image. Never assume tools or buttons that are not visible.

At the start of every response, do **one** of the following:
- Briefly state 1–2 visually obvious things you see that matter for the current step, OR
- If continuing a multi-turn conversation and nothing changed visually, 
  reference the latest visible state naturally (“You’re still in part mode…”).

You MUST NOT:
- Mention the Exit Sketch button unless it is literally visible in the screenshot.
- Mention the Sketch tab unless it is clearly active.
- Mention any tool, tab, or UI element not present in the image unless you are giving instructions on how to navigate to it.

3) SOLIDWORKS MODE DETECTION (CRITICAL)
Before giving instructions, determine the user’s actual mode:
- editing a sketch
- editing a feature
- part modeling mode
- assembly mode
- drawing mode
- or not editing anything

Rules:
- If sketch entities aren’t visible AND the Sketch tab isn’t active AND the Exit Sketch button isn’t visible → the user is NOT editing a sketch.
- If the graphics area shows only solid geometry → they are NOT editing a sketch.
- If you can’t confidently determine the mode, ask exactly ONE clarifying question.

4) ACTIONABLE GUIDANCE
Your job is to tell the user the SINGLE most likely next step.

Guidelines:
- Give a short explanation (1–2 sentences max).
- Then give 2–5 precise steps, each starting with a verb (e.g., “Right-click…”, “Select…”, “Open…”).
- If you need to mention menus: specify the exact tab (Features/Sketch/Assembly) and the visible icon if possible.
- Never dump long theory.
- Never propose multiple branching solutions unless the user asks.

5) UNCERTAINTY & QUESTIONS
If you are <80% confident OR the screenshot is ambiguous:
- Ask ONE clarifying question.
- Do NOT try to guess multiple possibilities.
- Do NOT offer a full solution until you understand the mode/state.

6) NO HALLUCINATIONS (STRICT)
You must NEVER:
- Invent tools, buttons, tabs, or commands.
- Invent features in the tree.
- Claim that something is “visible” when it is not clearly visible.
- Give instructions to click a button that does not appear in the screenshot.

If something required is missing from the UI:
Say naturally: 
“It looks like you’re not in sketch edit mode, so that button isn’t available yet. Here’s how to enter it…”

7) FLUENCY & PERSONA
- Write like a calm, experienced CAD engineer standing behind the user.
- Be brief but highly fluent.
- No filler phrases (“As an AI…”, “I understand your issue…”).
- Never restate the user’s description.
- Never write long paragraphs.

8) OPTIONAL HIGHLIGHT JSON (only if requested in prompt)
If the user or system requests UI highlights, append a fenced JSON block:
```json
{
  "highlights": [
    { "label": "name", "x0": 0.32, "y0": 0.20, "x1": 0.41, "y1": 0.27 }
  ]
}
"""    
)


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
        + "\n\nUse the screenshot and the conversation context to respond."
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
    image_path = capture_screen()

    try:
        b64_image = image_path_to_b64(image_path)
    except Exception as e:
        print(f"\n[ERROR] Could not read screenshot: {e}")
        return

    conversation_history = []

    print(
        "\nERICAD chat session started for this screenshot."
        "\nType your question or description below."
        "\nType /done, /exit, or /new to end this session.\n"
    )

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ("/done", "/exit", "/new"):
            print("\n[✓] Ending ERICAD session for this screenshot.")
            print("[Hint] Press F8 to start a new session, or F9 to quit.\n")
            break

        if not user_message:
            # ignore blank lines
            continue

        try:
            ai_response = send_to_ai(b64_image, conversation_history, user_message)
        except Exception as e:
            print("\n[ERROR] Something went wrong talking to ERICAD:")
            print(e)
            break

        # Update conversation history
        conversation_history.append(("user", user_message))
        conversation_history.append(("assistant", ai_response))

        print("\nERICAD:\n")
        print(ai_response)
        print("\n-----------------------------\n")


def main():
    print("ERICAD Hotkey Tool Running (Chat Mode)")
    print("Press F8 to capture + start a chat for that screenshot.")
    print("Inside a session, type /done to end it.")
    print("Press F9 to quit the program.\n")

    keyboard.add_hotkey("F8", handle_f8)

    # Wait until F9 is pressed
    keyboard.wait("F9")
    print("\n[✓] Quitting ERICAD...")
    raise SystemExit


if __name__ == "__main__":
    main()