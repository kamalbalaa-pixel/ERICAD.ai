import os
import datetime
import mss
import mss.tools
import keyboard
import base64
import win32com.client
import pythoncom
from openai import OpenAI
import time

MODEL_NAME = "gpt-5.1"  # Updated model name


class SolidWorksAssistant:
    def __init__(self):
        self.client = OpenAI()
        self.swApp = None
        self.connect_to_solidworks()

    def connect_to_solidworks(self):
        """Connect to running SolidWorks instance"""
        try:
            pythoncom.CoInitialize()

            # Try to connect
            for attempt in range(3):
                try:
                    self.swApp = win32com.client.Dispatch("SldWorks.Application")
                    if self.swApp:
                        break
                except:
                    print(f"[!] Connection attempt {attempt + 1} failed")
                    time.sleep(1)

            if self.swApp:
                print("[✓] Connected to SolidWorks")
                self.swApp.Visible = True

                # Test the connection
                try:
                    # This might fail if no document is open, which is OK
                    doc_count = self.swApp.GetDocumentCount()
                    print(f"[✓] SolidWorks has {doc_count} document(s) open")
                except:
                    print("[✓] SolidWorks connected (no documents open)")
            else:
                print("[!] Could not connect to SolidWorks. Make sure it's running.")

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            self.swApp = None

class SolidWorksAssistant:
    def __init__(self):
        self.client = OpenAI()
        self.swApp = None
        self.connect_to_solidworks()

    def connect_to_solidworks(self):
        """Connect to running SolidWorks instance"""
        try:
            pythoncom.CoInitialize()
            self.swApp = win32com.client.Dispatch("SldWorks.Application")
            if self.swApp:
                print("[✓] Connected to SolidWorks")
                # Make SW visible if hidden
                self.swApp.Visible = True
            else:
                print("[!] SolidWorks not running. Please start SolidWorks first.")
        except Exception as e:
            print(f"[ERROR] Could not connect to SolidWorks: {e}")

    def get_sw_state(self):
        """Get detailed SolidWorks state information"""
        if not self.swApp:
            return {"mode": "Not connected", "error": "SolidWorks not connected"}

        state = {
            "mode": "Unknown",
            "document_type": None,
            "active_doc_name": None,
            "is_in_edit_mode": False,
            "active_feature": None,
            "selection_count": 0,
            "available_commands": []
        }

        try:
            # Check if SolidWorks has any documents open
            doc_count = 0
            try:
                doc_count = self.swApp.GetDocumentCount()
            except:
                pass

            if doc_count == 0:
                state["mode"] = "No document open"
                state["available_commands"] = ["New Part", "New Assembly", "New Drawing", "Open"]
                return state

            # Try to get active document
            swModel = None
            try:
                swModel = self.swApp.ActiveDoc
            except Exception as e:
                # Try alternative method
                try:
                    # Get first document if ActiveDoc fails
                    swModel = self.swApp.GetFirstDocument()
                except:
                    state["mode"] = "Cannot access document"
                    return state

            if not swModel:
                state["mode"] = "No active document"
                return state

            # Get document info using safe methods
            try:
                doc_type = swModel.GetType()  # Note: GetType() not GetType
                doc_types = {1: "Part", 2: "Assembly", 3: "Drawing"}
                state["document_type"] = doc_types.get(doc_type, "Unknown")
            except:
                state["document_type"] = "Unknown"

            try:
                state["active_doc_name"] = swModel.GetTitle()  # Note: GetTitle() not GetTitle
            except:
                state["active_doc_name"] = "Untitled"

            # Check sketch mode safely
            try:
                swSketchMgr = swModel.SketchManager
                active_sketch = swSketchMgr.ActiveSketch
                if active_sketch:
                    state["mode"] = "Sketch Edit Mode"
                    state["is_in_edit_mode"] = True
                    try:
                        state["active_feature"] = active_sketch.Name
                    except:
                        state["active_feature"] = "Active Sketch"

                    state["available_commands"] = [
                        "Line", "Circle", "Rectangle", "Arc", "Spline",
                        "Smart Dimension", "Relations", "Trim", "Extend",
                        "Exit Sketch"
                    ]
                else:
                    state["mode"] = f"{state['document_type']} Mode"
            except:
                state["mode"] = "Document open"

            # Get selection info safely
            try:
                swSelMgr = swModel.SelectionManager
                sel_count = swSelMgr.GetSelectedObjectCount2(-1)
                state["selection_count"] = sel_count
            except:
                state["selection_count"] = 0

            # Set available commands based on document type
            if state["mode"] != "Sketch Edit Mode":
                if state["document_type"] == "Part":
                    state["available_commands"] = [
                        "Sketch", "Extrude", "Revolve", "Cut-Extrude", "Fillet"
                    ]
                elif state["document_type"] == "Assembly":
                    state["available_commands"] = [
                        "Insert Component", "Mate", "Pattern", "Exploded View"
                    ]

        except Exception as e:
            print(f"[WARNING] Error getting some SW state info: {e}")
            # Return what we have

        return state

    def execute_command(self, command):
        """Execute SolidWorks commands directly"""
        if not self.swApp or not self.swApp.ActiveDoc:
            return False, "No active document"

        try:
            swModel = self.swApp.ActiveDoc

            # Map common commands
            if command.lower() == "new sketch":
                swModel.SketchManager.InsertSketch(True)
                return True, "Started new sketch"

            elif command.lower() == "exit sketch":
                swModel.SketchManager.InsertSketch(False)
                return True, "Exited sketch"

            elif command.lower() == "zoom to fit":
                swModel.ViewZoomtofit2()
                return True, "Zoomed to fit"

            elif command.lower() == "rebuild":
                swModel.ForceRebuild3(True)
                return True, "Model rebuilt"

            # Add more commands as needed

        except Exception as e:
            return False, str(e)

        return False, "Unknown command"

    def capture_screen_with_context(self):
        """Capture screenshot and include SW state data"""
        # Take screenshot
        with mss.mss() as sct:
            screenshot = sct.shot()

        # Get SW state
        sw_state = self.get_sw_state()

        # Convert screenshot to base64
        with open(screenshot, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode('utf-8')

        # Clean up
        os.remove(screenshot)

        return b64_image, sw_state

    def send_to_ai(self, b64_image, sw_state, conversation_history, user_message):
        """Send to AI with both visual and API context"""

        # Build context message
        context_msg = f"""
Current SolidWorks State:
- Mode: {sw_state['mode']}
- Document Type: {sw_state['document_type']}
- Document: {sw_state['active_doc_name']}
- In Edit Mode: {sw_state['is_in_edit_mode']}
- Selection Count: {sw_state['selection_count']}
- Available Commands: {', '.join(sw_state['available_commands'][:5])}...

User Question: {user_message}
"""

        messages = [
            {
                "role": "system",
                "content": """You are ERICAD, a SolidWorks assistant with direct API access.
You can see both the screenshot AND the exact SolidWorks state from the API.
You can execute commands directly if the user wants.

When giving instructions:
1. Use the API state data to be extremely precise
2. Reference the exact mode and available tools
3. If user wants, you can execute commands directly
4. Never guess about UI state - you have the exact data"""
            }
        ]

        # Add conversation history
        for role, content in conversation_history[-6:]:  # Last 3 exchanges
            messages.append({"role": role, "content": content})

        # Add current message with image and context
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": context_msg},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}",
                        "detail": "high"
                    }
                }
            ]
        })

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_completion_tokens=500  # FIXED PARAMETER NAME
        )

        return response.choices[0].message.content

    def interactive_session(self, b64_image, sw_state):
        """Run interactive chat session"""
        conversation_history = []

        print("\n[Session Started]")
        print(f"SolidWorks State: {sw_state['mode']} | Doc: {sw_state['active_doc_name']}")
        print("Type your question (or /done to end, /exec <command> to execute):\n")

        while True:
            user_message = input("You: ").strip()

            if user_message.lower() == "/done":
                break

            if user_message.lower().startswith("/exec "):
                # Execute command directly
                command = user_message[6:]
                success, result = self.execute_command(command)
                print(f"\n[Command Result] {result}\n")
                continue

            if not user_message:
                continue

            try:
                # Get fresh state for each message
                sw_state = self.get_sw_state()
                ai_response = self.send_to_ai(
                    b64_image, sw_state, conversation_history, user_message
                )

                conversation_history.append(("user", user_message))
                conversation_history.append(("assistant", ai_response))

                print(f"\nERICAD:\n{ai_response}\n")
                print("-" * 30)

            except Exception as e:
                print(f"\n[ERROR] {e}\n")


def main():
    print("ERICAD - SolidWorks AI Assistant (API Version)")
    print("Press F8 to capture screen and start assistance")
    print("Press F9 to quit\n")

    assistant = SolidWorksAssistant()

    def handle_f8():
        if not assistant.swApp:
            print("[!] SolidWorks not connected")
            return

        print("\n[Capturing...]")
        b64_image, sw_state = assistant.capture_screen_with_context()
        assistant.interactive_session(b64_image, sw_state)

    keyboard.add_hotkey("F8", handle_f8)
    keyboard.wait("F9")
    print("\n[✓] Quitting ERICAD...")


if __name__ == "__main__":
    main()
